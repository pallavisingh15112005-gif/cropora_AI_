"""Cropora Mandi — paper trading account stored in SQLite."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "mandi.db"
STARTING_CASH = 500_000.0


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    _ensure_schema(connection)
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            cash REAL NOT NULL,
            starting_cash REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS positions (
            commodity TEXT NOT NULL,
            market TEXT NOT NULL,
            qty REAL NOT NULL,
            avg_cost REAL NOT NULL,
            PRIMARY KEY (commodity, market)
        );
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            commodity TEXT NOT NULL,
            market TEXT NOT NULL,
            side TEXT NOT NULL,
            qty REAL NOT NULL,
            price REAL NOT NULL,
            amount REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS equity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            equity REAL NOT NULL
        );
        """
    )
    row = connection.execute("SELECT id FROM account WHERE id = 1").fetchone()
    if row is None:
        connection.execute(
            "INSERT INTO account (id, cash, starting_cash) VALUES (1, ?, ?)",
            (STARTING_CASH, STARTING_CASH),
        )
        connection.execute(
            "INSERT INTO equity (ts, equity) VALUES (?, ?)",
            (datetime.now().isoformat(timespec="seconds"), STARTING_CASH),
        )
        connection.commit()


def get_account() -> dict:
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT cash, starting_cash FROM account WHERE id = 1"
        ).fetchone()
    return {"cash": float(row["cash"]), "starting_cash": float(row["starting_cash"])}


def reset_account(starting_cash: float = STARTING_CASH) -> None:
    with closing(_connect()) as connection:
        connection.execute("DELETE FROM positions")
        connection.execute("DELETE FROM trades")
        connection.execute("DELETE FROM equity")
        connection.execute(
            "UPDATE account SET cash = ?, starting_cash = ? WHERE id = 1",
            (starting_cash, starting_cash),
        )
        connection.execute(
            "INSERT INTO equity (ts, equity) VALUES (?, ?)",
            (datetime.now().isoformat(timespec="seconds"), starting_cash),
        )
        connection.commit()


def get_positions() -> list[dict]:
    with closing(_connect()) as connection:
        rows = connection.execute(
            "SELECT commodity, market, qty, avg_cost FROM positions ORDER BY commodity"
        ).fetchall()
    return [dict(row) for row in rows]


def get_position(commodity: str, market: str) -> dict | None:
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT commodity, market, qty, avg_cost FROM positions WHERE commodity = ? AND market = ?",
            (commodity, market),
        ).fetchone()
    return dict(row) if row else None


def get_trades(limit: int | None = None) -> pd.DataFrame:
    query = "SELECT ts, commodity, market, side, qty, price, amount FROM trades ORDER BY id DESC"
    params: tuple = ()
    if limit:
        query += " LIMIT ?"
        params = (int(limit),)
    with closing(_connect()) as connection:
        rows = connection.execute(query, params).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def execute_trade(commodity: str, market: str, side: str, qty: float, price: float) -> tuple[bool, str]:
    """Execute a market order at ``price``. Returns (success, message)."""
    if qty <= 0:
        return False, "Quantity must be greater than zero."
    if price <= 0:
        return False, "Invalid price."

    side = side.lower()
    amount = qty * price

    with closing(_connect()) as connection:
        account = connection.execute("SELECT cash FROM account WHERE id = 1").fetchone()
        cash = float(account["cash"])

        position = connection.execute(
            "SELECT qty, avg_cost FROM positions WHERE commodity = ? AND market = ?",
            (commodity, market),
        ).fetchone()

        timestamp = datetime.now().isoformat(timespec="seconds")

        if side == "buy":
            if amount > cash + 1e-6:
                return False, f"Not enough cash. Required ₹{amount:,.0f}, available ₹{cash:,.0f}."
            old_qty = float(position["qty"]) if position else 0.0
            old_cost = float(position["avg_cost"]) if position else 0.0
            new_qty = old_qty + qty
            new_avg = (old_qty * old_cost + amount) / new_qty if new_qty else 0.0
            connection.execute(
                """
                INSERT INTO positions (commodity, market, qty, avg_cost)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(commodity, market) DO UPDATE SET qty = ?, avg_cost = ?
                """,
                (commodity, market, new_qty, new_avg, new_qty, new_avg),
            )
            connection.execute("UPDATE account SET cash = ? WHERE id = 1", (cash - amount,))
            message = f"Bought {qty:g} quintal at ₹{price:,.0f}."
        elif side == "sell":
            held = float(position["qty"]) if position else 0.0
            if qty > held + 1e-6:
                return False, f"You hold only {held:g} quintal of this commodity at this mandi."
            remaining = held - qty
            if remaining <= 1e-6:
                connection.execute(
                    "DELETE FROM positions WHERE commodity = ? AND market = ?",
                    (commodity, market),
                )
            else:
                connection.execute(
                    "UPDATE positions SET qty = ? WHERE commodity = ? AND market = ?",
                    (remaining, commodity, market),
                )
            connection.execute("UPDATE account SET cash = ? WHERE id = 1", (cash + amount,))
            message = f"Sold {qty:g} quintal at ₹{price:,.0f}."
        else:
            return False, "Unknown order side."

        connection.execute(
            """
            INSERT INTO trades (ts, commodity, market, side, qty, price, amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (timestamp, commodity, market, side, qty, price, amount),
        )
        connection.commit()

    return True, message


def record_equity(equity: float) -> None:
    """Snapshot total equity when it changed, or at most once per hour."""
    now = datetime.now()
    with closing(_connect()) as connection:
        row = connection.execute(
            "SELECT ts, equity FROM equity ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is not None:
            try:
                last = datetime.fromisoformat(row["ts"])
                unchanged = abs(float(row["equity"]) - equity) < 1.0
                if unchanged and now - last < timedelta(hours=1):
                    return
            except ValueError:
                pass
        connection.execute(
            "INSERT INTO equity (ts, equity) VALUES (?, ?)",
            (now.isoformat(timespec="seconds"), float(equity)),
        )
        connection.commit()


def equity_history() -> pd.DataFrame:
    with closing(_connect()) as connection:
        rows = connection.execute("SELECT ts, equity FROM equity ORDER BY id").fetchall()
    frame = pd.DataFrame([dict(row) for row in rows])
    if not frame.empty:
        frame["ts"] = pd.to_datetime(frame["ts"])
    return frame
