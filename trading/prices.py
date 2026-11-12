"""Cropora Mandi — live price helpers used by the pages.

All values come from :mod:`trading.agmarknet`, which reads the public Agmarknet
APMC report feed. Nothing here invents a price.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from . import agmarknet
from .agmarknet import FeedError  # re-exported for the UI
from .catalog import COMMODITIES, get_commodity, get_market

__all__ = [
    "FeedError",
    "archive_summary",
    "board",
    "commodity_movers",
    "compare_markets",
    "data_date",
    "ensure_feed",
    "feed_status",
    "history",
    "inr",
    "latest",
    "market_summary",
    "quote",
    "refresh",
    "sign",
    "snapshot",
    "sync_label",
]


def ensure_feed(market_key: str) -> dict:
    return agmarknet.ensure_feed(market_key)


def refresh(market_key: str) -> dict:
    return agmarknet.refresh_market(market_key)


def feed_status(market_key: str) -> dict:
    return agmarknet.status(market_key)


def sync_label(market_key: str) -> str:
    return agmarknet.sync_label(market_key)


def data_date(market_key: str) -> date | None:
    return agmarknet.data_date(market_key)


def archive_summary() -> dict:
    return agmarknet.archive_summary()


def latest(commodity_key: str, market_key: str) -> dict | None:
    """Latest real quote, or ``None`` when the mandi did not report it."""
    return agmarknet.quote(market_key, commodity_key)


def quote(commodity_key: str, market_key: str) -> dict | None:
    return latest(commodity_key, market_key)


def snapshot(market_key: str) -> pd.DataFrame:
    return agmarknet.board(market_key)


def board(market_key: str) -> pd.DataFrame:
    return agmarknet.board(market_key)


def history(commodity_key: str, market_key: str) -> pd.DataFrame:
    """Daily median price series for one commodity at one mandi."""
    return agmarknet.daily_series(market_key, commodity_key)


def variety_history(commodity_key: str, market_key: str) -> pd.DataFrame:
    return agmarknet.variety_series(market_key, commodity_key)


def commodity_movers(market_key: str, *, limit: int = 4, gainers: bool = True) -> pd.DataFrame:
    frame = snapshot(market_key)
    if frame.empty:
        return frame
    if gainers:
        frame = frame[frame["change_pct"] > 0.05].sort_values("change_pct", ascending=False)
    else:
        frame = frame[frame["change_pct"] < -0.05].sort_values("change_pct")
    return frame.head(limit)


def market_summary(market_key: str) -> dict:
    frame = snapshot(market_key)
    status = feed_status(market_key)
    summary = {
        "items": int(len(frame)),
        "coverage": int(status.get("coverage", len(frame))),
        "partial": bool(status.get("partial", False)),
        "data_date": data_date(market_key),
        "synced_at": agmarknet.last_synced(market_key),
        "gainers": 0,
        "losers": 0,
        "flat": 0,
        "avg_change": 0.0,
        "rows": status["rows"],
        "error": status["error"],
    }
    if frame.empty:
        return summary
    summary["gainers"] = int((frame["change_pct"] > 0.05).sum())
    summary["losers"] = int((frame["change_pct"] < -0.05).sum())
    summary["flat"] = int(len(frame) - summary["gainers"] - summary["losers"])
    summary["avg_change"] = float(frame["change_pct"].mean())
    return summary


def compare_markets(commodity_key: str, market_keys: list[str], *, refresh: bool = False) -> pd.DataFrame:
    """Latest price for one commodity across several mandis."""
    if refresh:
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda key: agmarknet.refresh_pair(key, commodity_key), market_keys))

    rows = []
    for market_key in market_keys:
        item = latest(commodity_key, market_key)
        if item is None:
            continue
        rows.append(
            {
                "market": market_key,
                "market_name": get_market(market_key).name,
                "state": get_market(market_key).state,
                "price": item["price"],
                "change_pct": item["change_pct"],
                "date": item["date"],
                "varieties": item["varieties"],
            }
        )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values("price", ascending=False).reset_index(drop=True)
    return frame


def card_rows(frame: pd.DataFrame, *, limit: int | None = None, sort: str = "price") -> list[dict]:
    """Turn board rows into the dicts expected by :func:`trading.ui.commodity_grid`."""
    if frame.empty:
        return []
    data = frame.sort_values(sort, ascending=False)
    if limit:
        data = data.head(limit)
    rows = []
    for record in data.itertuples():
        commodity = get_commodity(record.commodity)
        rows.append(
            {
                "key": record.commodity,
                "name": commodity.name,
                "local_name": commodity.local_name,
                "category": commodity.category,
                "price": float(record.price),
                "change_pct": float(record.change_pct),
                "low_week": float(record.low_week),
                "high_week": float(record.high_week),
                "varieties": int(record.varieties),
                "spark": list(record.spark),
                "tag": commodity.category.split()[0],
            }
        )
    return rows


def market_coverage(market_key: str) -> list[str]:
    """Commodity keys for which this mandi reported at least one price."""
    frame = snapshot(market_key)
    if frame.empty:
        return []
    return frame["commodity"].tolist()


def odd_lot(price: float, qty: float = 1.0) -> float:
    return price * qty


def sign(value: float) -> str:
    return "▲" if value >= 0 else "▼"


def inr(value: float) -> str:
    """Format a number in Indian rupees with lakh/crore grouping."""
    value = float(value)
    negative = value < 0
    value = abs(value)
    if value >= 1_00_00_000:
        text = f"{value / 1_00_00_000:.2f} Cr"
    elif value >= 1_00_000:
        text = f"{value / 1_00_000:.2f} lakh"
    elif value >= 1_000:
        text = f"{value:,.0f}"
    else:
        text = f"{value:,.0f}" if value.is_integer() else f"{value:,.2f}"
    return f"{'-' if negative else ''}₹{text}"


def all_commodities() -> list:
    return list(COMMODITIES)
