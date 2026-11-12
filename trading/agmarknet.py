"""Live Agmarknet feed for Cropora Mandi.

The app reads real APMC prices from the public Agmarknet API
(``api.agmarknet.gov.in/v1``). The ``commodity-price/lastweek`` report is
keyless and returns one week of reported prices per market, so every number
shown on the board comes from an actual mandi report.

Responses are stored in a small SQLite archive (``data/market.db``). That keeps
the app fast, survives API outages, and quietly builds a longer price history
every time it is opened.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from .catalog import (
    MARKETS,
    Commodity,
    Market,
    commodities_for_market,
    get_commodity,
    get_market,
    starter_commodities,
)

BASE_URL = "https://api.agmarknet.gov.in/v1"
HEADERS = {
    "Accept": "application/json",
    "User-Agent": "CroporaMandi/1.0 (paper-trading demo)",
}
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "market.db"
FRESH_MINUTES = 720
RETRY_AFTER_FAILURE_MINUTES = 15


class FeedError(RuntimeError):
    """Raised when Agmarknet cannot be reached."""


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=20)
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS prices (
            commodity TEXT NOT NULL,
            market TEXT NOT NULL,
            variety TEXT NOT NULL,
            date TEXT NOT NULL,
            price REAL NOT NULL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (commodity, market, variety, date)
        );
        CREATE INDEX IF NOT EXISTS prices_market
            ON prices (market, commodity, date);
        CREATE TABLE IF NOT EXISTS sync (
            market TEXT PRIMARY KEY,
            attempted_at TEXT,
            synced_at TEXT,
            latest_date TEXT,
            row_count INTEGER,
            error TEXT
        );
        CREATE TABLE IF NOT EXISTS market_directory (
            commodity TEXT NOT NULL,
            market TEXT NOT NULL,
            market_id INTEGER NOT NULL,
            state_id INTEGER NOT NULL,
            market_name TEXT NOT NULL,
            priority INTEGER NOT NULL,
            PRIMARY KEY (commodity, market, market_id)
        );
        CREATE TABLE IF NOT EXISTS directory (
            commodity TEXT PRIMARY KEY,
            fetched_at TEXT NOT NULL,
            markets INTEGER NOT NULL
        );
        """
    )
    return connection


def _get_json(path: str, params: dict | None = None, *, timeout: int = 20) -> dict:
    url = BASE_URL + path
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(2):
        request = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                time.sleep(2 + attempt * 4)
                continue
            break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(1)
    raise FeedError(f"Agmarknet request failed: {last_error}")


def _parse_week(payload: dict) -> list[tuple[str, str, float]]:
    """Turn one report payload into ``(date, variety, price)`` rows."""
    columns = [str(item.get("key")) for item in payload.get("columns", [])]
    dates = [column for column in columns if column[:2] == "20" and "-" in column]
    rows: list[tuple[str, str, float]] = []
    for record in payload.get("data", []):
        label = str(record.get("variety") or "Unknown")
        variety = label.split(" - ", 1)[1].strip() if " - " in label else label
        for day in dates:
            value = record.get(day)
            if isinstance(value, (int, float)) and float(value) > 0:
                rows.append((day, variety or "Unknown", float(value)))
    return rows


def _ensure_directory(commodity_key: str) -> None:
    """Cache which Agmarknet market ids report ``commodity_key``.

    The same mandi is listed under different market ids for different crops
    (for example Indore F&V vs Indore APMC), so this directory is what makes
    every mandi work for every crop it actually trades.
    """
    commodity = get_commodity(commodity_key)
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT fetched_at FROM directory WHERE commodity = ?", (commodity_key,)
        ).fetchone()
    if row:
        try:
            age = datetime.now() - datetime.fromisoformat(row["fetched_at"])
            if age < timedelta(days=30):
                return
        except ValueError:
            pass

    payload = _get_json(f"/list-comm/{commodity.agmarknet_id}", timeout=30)
    records = payload.get("data", []) or []
    found: list[tuple[str, str, int, int, str, int]] = []
    for market in MARKETS:
        for priority, pattern in enumerate(market.matchers):
            for record in records:
                name = str(record.get("market_name") or "").strip()
                if re.search(pattern, name.lower()):
                    found.append(
                        (
                            commodity_key,
                            market.key,
                            int(record["market_id"]),
                            int(record["state_id"]),
                            name,
                            priority,
                        )
                    )
                    break

    stamp = datetime.now().isoformat(timespec="seconds")
    with closing(_connect()) as connection:
        connection.execute(
            "DELETE FROM market_directory WHERE commodity = ?", (commodity_key,)
        )
        connection.executemany(
            """
            INSERT OR REPLACE INTO market_directory
                (commodity, market, market_id, state_id, market_name, priority)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            found,
        )
        connection.execute(
            """
            INSERT INTO directory (commodity, fetched_at, markets) VALUES (?, ?, ?)
            ON CONFLICT(commodity) DO UPDATE SET
                fetched_at = excluded.fetched_at,
                markets = excluded.markets
            """,
            (commodity_key, stamp, len(found)),
        )
        connection.commit()


def _market_ids(commodity_key: str, market_key: str) -> list[tuple[int, int]]:
    """Market ids to try for a commodity, best match first."""
    try:
        _ensure_directory(commodity_key)
    except FeedError:
        pass
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT market_id, state_id FROM market_directory "
            "WHERE commodity = ? AND market = ? ORDER BY priority, market_id LIMIT 3",
            (commodity_key, market_key),
        ).fetchall()
    if rows:
        return [(int(row["market_id"]), int(row["state_id"])) for row in rows]
    market = get_market(market_key)
    return [(market.market_id, market.state_id)]


def fetch_commodity(commodity: str | Commodity, market: str | Market) -> list[tuple[str, str, float]]:
    """Fetch the last-week report for one commodity at one mandi."""
    commodity = get_commodity(commodity) if isinstance(commodity, str) else commodity
    market = get_market(market) if isinstance(market, str) else market
    for market_id, state_id in _market_ids(commodity.key, market.key):
        payload = _get_json(
            "/prices-and-arrivals/commodity-price/lastweek",
            {
                "commodityId": commodity.agmarknet_id,
                "marketId": market_id,
                "stateId": state_id,
                "includeExcel": "false",
            },
        )
        rows = _parse_week(payload)
        if rows:
            return rows
    return []


def _store(market_key: str, commodity_key: str, rows: list[tuple[str, str, float]]) -> int:
    if not rows:
        return 0
    stamp = datetime.now().isoformat(timespec="seconds")
    with closing(_connect()) as connection:
        connection.executemany(
            """
            INSERT INTO prices (commodity, market, variety, date, price, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(commodity, market, variety, date)
            DO UPDATE SET price = excluded.price, fetched_at = excluded.fetched_at
            """,
            [(commodity_key, market_key, variety, day, price, stamp) for day, variety, price in rows],
        )
        connection.commit()
    return len(rows)


def _record_attempt(market_key: str, *, rows: int, error: str | None) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    with closing(_connect()) as connection:
        latest = connection.execute(
            "SELECT MAX(date) AS latest FROM prices WHERE market = ?", (market_key,)
        ).fetchone()["latest"]
        connection.execute(
            """
            INSERT INTO sync (market, attempted_at, synced_at, latest_date, row_count, error)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(market) DO UPDATE SET
                attempted_at = excluded.attempted_at,
                synced_at = CASE WHEN excluded.row_count > 0
                                 THEN excluded.synced_at ELSE sync.synced_at END,
                latest_date = excluded.latest_date,
                row_count = CASE WHEN excluded.row_count > 0
                                 THEN excluded.row_count ELSE sync.row_count END,
                error = excluded.error
            """,
            (market_key, now, now, latest, rows, error),
        )
        connection.commit()


def refresh_market(
    market_key: str,
    commodity_keys: list[str] | None = None,
    *,
    workers: int = 4,
) -> dict:
    """Fetch and cache fresh prices for one mandi."""
    market = get_market(market_key)
    keys = commodity_keys or commodities_for_market(market_key)
    stored = 0
    errors: list[str] = []

    # Build the per-crop market directory first, one request at a time, so the
    # price fetches below do not stampede Agmarknet with master-data calls.
    for key in keys:
        try:
            _ensure_directory(key)
        except FeedError as exc:
            errors.append(f"{key}: {exc}")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(fetch_commodity, get_commodity(key), market): key for key in keys
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                stored += _store(market_key, key, future.result())
            except Exception as exc:  # noqa: BLE001 - surfaced to the UI
                errors.append(f"{key}: {exc}")

    error = "; ".join(errors[:4]) if errors and not stored else None
    _record_attempt(market_key, rows=stored, error=error)
    return status(market_key)


def refresh_pair(market_key: str, commodity_key: str) -> dict:
    """Fetch one commodity at one mandi (used by the compare page)."""
    try:
        rows = fetch_commodity(commodity_key, get_market(market_key))
        _store(market_key, commodity_key, rows)
        error = None
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
    if error:
        with closing(_connect()) as connection:
            connection.execute(
                "UPDATE sync SET error = ? WHERE market = ?", (error, market_key)
            )
            connection.commit()
    return {"market": market_key, "rows": len(rows) if not error else 0, "error": error}


def status(market_key: str) -> dict:
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT * FROM sync WHERE market = ?", (market_key,)
        ).fetchone()
        totals = connection.execute(
            "SELECT COUNT(*) AS rows, MAX(date) AS latest, COUNT(DISTINCT commodity) AS items "
            "FROM prices WHERE market = ?",
            (market_key,),
        ).fetchone()
    data = dict(row) if row else {}
    coverage = len(commodities_for_market(market_key))
    items = int(totals["items"] or 0)
    return {
        "market": market_key,
        "rows": int(totals["rows"] or 0),
        "items": items,
        "coverage": coverage,
        "partial": items < coverage,
        "latest_date": totals["latest"],
        "attempted_at": data.get("attempted_at"),
        "synced_at": data.get("synced_at"),
        "error": data.get("error"),
    }


def _minutes_since(stamp: str | None) -> float | None:
    if not stamp:
        return None
    try:
        return (datetime.now() - datetime.fromisoformat(stamp)).total_seconds() / 60
    except ValueError:
        return None


def needs_refresh(market_key: str) -> bool:
    info = status(market_key)
    if info["rows"] == 0:
        age = _minutes_since(info["attempted_at"])
        return age is None or age > RETRY_AFTER_FAILURE_MINUTES
    age = _minutes_since(info["attempted_at"])
    return age is None or age > FRESH_MINUTES


def ensure_feed(market_key: str) -> dict:
    """Return cached prices, fetching a starter basket only when needed.

    A full mandi sync is deliberately left to the sidebar Refresh button: the
    public Agmarknet endpoint is slow, so blocking every first page load on all
    commodities would take minutes. See :func:`refresh_market`.
    """
    if needs_refresh(market_key):
        return refresh_market(market_key, starter_commodities(market_key))
    return status(market_key)


def _price_frame(market_key: str) -> pd.DataFrame:
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT commodity, date, variety, price FROM prices WHERE market = ?",
            (market_key,),
        ).fetchall()
    frame = pd.DataFrame([dict(row) for row in rows])
    if not frame.empty:
        frame["date"] = pd.to_datetime(frame["date"])
    return frame


def daily_series(market_key: str, commodity_key: str) -> pd.DataFrame:
    """Median reported price per day, plus variety count and spread."""
    frame = _price_frame(market_key)
    if frame.empty:
        return pd.DataFrame(columns=["date", "price", "low", "high", "varieties"])
    frame = frame[frame["commodity"] == commodity_key]
    if frame.empty:
        return pd.DataFrame(columns=["date", "price", "low", "high", "varieties"])
    grouped = (
        frame.groupby("date")["price"]
        .agg(price="median", low="min", high="max", varieties="count")
        .reset_index()
        .sort_values("date")
    )
    return grouped


def variety_series(market_key: str, commodity_key: str) -> pd.DataFrame:
    frame = _price_frame(market_key)
    if frame.empty:
        return frame
    frame = frame[frame["commodity"] == commodity_key]
    return frame.sort_values(["date", "variety"])


def quote(market_key: str, commodity_key: str) -> dict | None:
    """Latest real quote for a commodity at a mandi, or ``None``."""
    series = daily_series(market_key, commodity_key)
    if series.empty:
        return None
    last = series.iloc[-1]
    previous = series.iloc[-2] if len(series) > 1 else None
    price = float(last["price"])
    prev_price = float(previous["price"]) if previous is not None else price
    change = price - prev_price
    varieties = variety_series(market_key, commodity_key)
    latest_varieties = varieties[varieties["date"] == last["date"]]

    return {
        "commodity": commodity_key,
        "market": market_key,
        "date": last["date"].to_pydatetime().date(),
        "price": price,
        "previous": prev_price,
        "change": change,
        "change_pct": (change / prev_price * 100) if prev_price else 0.0,
        "high": float(last["high"]),
        "low": float(last["low"]),
        "avg": float(series["price"].mean()),
        "high_week": float(series["high"].max()),
        "low_week": float(series["low"].min()),
        "points": int(len(series)),
        "varieties": int(latest_varieties["variety"].nunique()),
        "variety_names": sorted(latest_varieties["variety"].unique().tolist()),
    }


def board(market_key: str) -> pd.DataFrame:
    """One row per commodity traded at a mandi, using the latest report."""
    frame = _price_frame(market_key)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "commodity",
                "local_name",
                "category",
                "price",
                "previous",
                "change_pct",
                "high_week",
                "low_week",
                "avg",
                "varieties",
                "date",
                "spark",
            ]
        )

    grouped = (
        frame.groupby(["commodity", "date"])["price"].median().reset_index().sort_values("date")
    )
    rows = []
    for commodity_key, series in grouped.groupby("commodity"):
        commodity = get_commodity(commodity_key)
        last = series.iloc[-1]
        previous = series.iloc[-2] if len(series) > 1 else last
        change_pct = (
            (last["price"] - previous["price"]) / previous["price"] * 100
            if previous["price"]
            else 0.0
        )
        rows.append(
            {
                "commodity": commodity_key,
                "local_name": commodity.local_name,
                "category": commodity.category,
                "price": float(last["price"]),
                "previous": float(previous["price"]),
                "change_pct": change_pct,
                "high_week": float(series["price"].max()),
                "low_week": float(series["price"].min()),
                "avg": float(series["price"].mean()),
                "varieties": int(
                    frame[(frame["commodity"] == commodity_key) & (frame["date"] == last["date"])][
                        "variety"
                    ].nunique()
                ),
                "date": last["date"],
                "spark": series["price"].tolist(),
            }
        )
    return pd.DataFrame(rows)


def last_synced(market_key: str) -> datetime | None:
    info = status(market_key)
    stamp = info.get("synced_at") or info.get("attempted_at")
    if not stamp:
        return None
    try:
        return datetime.fromisoformat(stamp)
    except ValueError:
        return None


def data_date(market_key: str):
    latest = status(market_key)["latest_date"]
    if not latest:
        return None
    return datetime.fromisoformat(latest).date()


def sync_label(market_key: str) -> str:
    synced = last_synced(market_key)
    if not synced:
        return "not synced yet"
    minutes = int((datetime.now() - synced).total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} min ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} h ago"
    return synced.strftime("%d %b, %H:%M")


def archive_summary() -> dict:
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS rows, COUNT(DISTINCT market) AS markets, "
            "MIN(date) AS first_date, MAX(date) AS last_date FROM prices"
        ).fetchone()
    return dict(row)
