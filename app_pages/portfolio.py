"""Paper portfolio marked to live mandi prices."""

from __future__ import annotations

import streamlit as st

from trading import catalog, portfolio, prices, ui
from trading.charts import equity_chart

market = st.session_state.market

with st.spinner("Syncing the latest Agmarknet reports…"):
    prices.ensure_feed(market)

st.title("Portfolio")
st.caption("Holdings are marked to the latest cached Agmarknet report for each mandi.")

account = portfolio.get_account()
positions = portfolio.get_positions()

rows = []
holdings_value = 0.0
cost_value = 0.0
for position in positions:
    commodity_key = position["commodity"]
    item = prices.latest(commodity_key, position["market"])
    qty = float(position["qty"])
    cost = float(position["avg_cost"])
    cost_value += qty * cost
    if item is None:
        rows.append(
            {
                "Commodity": catalog.get_commodity(commodity_key).name,
                "Mandi": catalog.get_market(position["market"]).name,
                "Quantity": qty,
                "Average cost": cost,
                "Live price": None,
                "Value": None,
                "P&L": None,
                "Reported": None,
            }
        )
        continue
    value = qty * item["price"]
    holdings_value += value
    rows.append(
        {
            "Commodity": catalog.get_commodity(commodity_key).name,
            "Mandi": catalog.get_market(position["market"]).name,
            "Quantity": qty,
            "Average cost": cost,
            "Live price": item["price"],
            "Value": value,
            "P&L": value - qty * cost,
            "Reported": item["date"].strftime("%d %b %Y"),
        }
    )

equity = account["cash"] + holdings_value
pnl = equity - account["starting_cash"]
pnl_pct = pnl / account["starting_cash"] * 100 if account["starting_cash"] else 0.0
portfolio.record_equity(equity)

ui.stat_cards(
    [
        ("Total equity", prices.inr(equity), "cash + holdings"),
        ("Cash", prices.inr(account["cash"]), f"of {prices.inr(account['starting_cash'])} start"),
        ("Holdings", prices.inr(holdings_value), f"{len(positions)} open position(s)"),
        ("Total P&L", f"{pnl:+,.0f}", f"{pnl_pct:+.2f}% since start"),
    ]
)

curve = portfolio.equity_history().drop_duplicates(subset=["ts"], keep="last")
if len(curve) >= 2 and curve["ts"].nunique() >= 2:
    ui.section("Equity curve", "Snapshots recorded as your paper account changes.")
    st.altair_chart(equity_chart(curve), width="stretch")
else:
    ui.note(
        "The equity chart appears after a couple of snapshots. Buy or sell something, "
        "or come back later — the app records equity automatically."
    )

ui.section("Open positions")
if not rows:
    st.caption("No open positions yet. Head to Trade to buy your first lot.")
else:
    st.dataframe(
        rows,
        hide_index=True,
        column_config={
            "Average cost": st.column_config.NumberColumn(format="₹%d"),
            "Live price": st.column_config.NumberColumn(format="₹%d"),
            "Value": st.column_config.NumberColumn(format="₹%d"),
            "P&L": st.column_config.NumberColumn(format="₹%d"),
            "Quantity": st.column_config.NumberColumn(format="%g q"),
        },
    )
    st.caption(
        "Live price is the latest reported median for that commodity at the mandi "
        "where you hold it."
    )

ui.section("Trade history")
trades = portfolio.get_trades()
if trades.empty:
    st.caption("No trades yet.")
else:
    history = trades.copy()
    history["commodity"] = history["commodity"].map(lambda key: catalog.get_commodity(key).name)
    history["market"] = history["market"].map(lambda key: catalog.get_market(key).name)
    history["Side"] = history["side"].str.title()
    history = history[
        ["ts", "Side", "commodity", "market", "qty", "price", "amount"]
    ].rename(
        columns={
            "ts": "Time",
            "commodity": "Commodity",
            "market": "Mandi",
            "qty": "Quantity",
            "price": "Price",
            "amount": "Value",
        }
    )
    st.dataframe(
        history,
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(format="₹%d"),
            "Value": st.column_config.NumberColumn(format="₹%d"),
            "Quantity": st.column_config.NumberColumn(format="%g q"),
        },
    )
    st.download_button(
        "Download trade history (CSV)",
        data=history.to_csv(index=False).encode("utf-8"),
        file_name="cropora_trades.csv",
        mime="text/csv",
        icon=":material/download:",
    )
