"""Cropora Mandi — live overview dashboard."""

from __future__ import annotations

import streamlit as st

from trading import catalog, portfolio, prices, ui

market = st.session_state.market
market_name = catalog.market_label(market)

with st.spinner("Syncing the latest Agmarknet reports…"):
    prices.ensure_feed(market)

board = prices.snapshot(market)
summary = prices.market_summary(market)
data_day = summary["data_date"]

ui.hero(
    "Live APMC feed · Agmarknet",
    "Mandi rates that move with the market",
    "Real wholesale prices from government APMC reports, with a paper-trading "
    "desk to practise buying and selling agricultural commodities.",
    [
        (market_name, ""),
        (f"Report {data_day.strftime('%d %b %Y')}" if data_day else "No report yet", "amber"),
        (f"{summary['items']} of {summary['coverage']} commodities", ""),
        (f"Synced {prices.sync_label(market)}", ""),
    ],
)

if board.empty:
    ui.note(
        "<strong>No prices cached yet.</strong> Agmarknet may be slow or the mandi "
        "did not report this week. Press sync to try again."
    )
    if st.button("Sync this mandi", type="primary", icon=":material/sync:"):
        with st.spinner("Fetching…"):
            prices.refresh(market)
        st.rerun()
    st.stop()

# Ticker: the everyday basket first, then whatever else the mandi reports.
popular = ["tomato", "onion", "potato", "apple", "banana", "wheat", "paddy"]
by_key = {row["key"]: row for row in prices.card_rows(board)}
ticker_rows = [by_key[key] for key in popular if key in by_key][:6]
for row in prices.card_rows(board):
    if len(ticker_rows) >= 6:
        break
    if row["key"] not in {item["key"] for item in ticker_rows}:
        ticker_rows.append(row)
ticker_items = [
    {
        "name": row["name"],
        "price": row["price"],
        "change_pct": row["change_pct"],
    }
    for row in ticker_rows
]
ui.ticker(ticker_items)

change = summary["avg_change"]
direction = "gaining" if change > 0.05 else "cooling" if change < -0.05 else "steady"
ui.stat_cards(
    [
        ("Commodities", f"{summary['items']:,}", f"traded at {catalog.get_market(market).name}"),
        ("Average move", f"{change:+.2f}%", f"market is {direction}"),
        ("Gainers / losers", f"{summary['gainers']} / {summary['losers']}", "versus previous report"),
        ("Report date", data_day.strftime("%d %b") if data_day else "—", "latest APMC report"),
    ]
)

ui.section("Today's movers", "Biggest changes against the previous reported price.")
left, right = st.columns(2)
with left:
    st.markdown("**Gainers today**")
    gainers = prices.commodity_movers(market, limit=3, gainers=True)
    if gainers.empty:
        st.caption("No gainers in the latest report.")
    else:
        ui.commodity_grid(prices.card_rows(gainers))
with right:
    st.markdown("**Losers today**")
    losers = prices.commodity_movers(market, limit=3, gainers=False)
    if losers.empty:
        st.caption("No losers in the latest report.")
    else:
        ui.commodity_grid(prices.card_rows(losers))

ui.section(
    "Commodity watch",
    "Every commodity this mandi reported in the last week.",
)
ui.commodity_grid(prices.card_rows(board))

ui.section("Quick actions", "Jump straight into the desk.")
action_cols = st.columns(3)
actions = [
    ("Price board", "app_pages/markets.py", ":material/storefront:", "Search every commodity and open a full trend view."),
    ("Compare mandis", "app_pages/compare.py", ":material/compare_arrows:", "See which APMC is paying the most for a crop."),
    ("Trade", "app_pages/trade.py", ":material/swap_horiz:", "Buy or sell at the live rate with paper money."),
]
for column, (title, target, icon, text) in zip(action_cols, actions):
    with column, st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(text)
        st.page_link(target, label=title, icon=icon)

trades = portfolio.get_trades(limit=3)
if not trades.empty:
    ui.section("Recent paper trades")
    recent = trades[["ts", "side", "commodity", "market", "qty", "price"]].copy()
    recent["commodity"] = recent["commodity"].map(lambda key: catalog.get_commodity(key).name)
    recent["market"] = recent["market"].map(lambda key: catalog.get_market(key).name)
    st.dataframe(
        recent.rename(
            columns={
                "ts": "Time",
                "side": "Side",
                "commodity": "Commodity",
                "market": "Mandi",
                "qty": "Quantity",
                "price": "Price",
            }
        ),
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(format="₹%d"),
            "Quantity": st.column_config.NumberColumn(format="%g q"),
        },
    )
