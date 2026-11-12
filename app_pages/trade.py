"""Place paper orders against the latest mandi price."""

from __future__ import annotations

import streamlit as st

from trading import catalog, portfolio, prices, ui

market = st.session_state.market

with st.spinner("Syncing the latest Agmarknet reports…"):
    prices.ensure_feed(market)

board = prices.snapshot(market)

st.title("Trade")
st.caption(
    f"{catalog.market_label(market)} · orders fill at the latest reported rate · "
    "paper money only"
)

if board.empty:
    ui.note(
        "<strong>No live prices for this mandi yet.</strong> Refresh from the sidebar "
        "or switch to another APMC."
    )
    st.stop()

flash = st.session_state.pop("trade_flash", None)
if flash:
    st.success(flash, icon=":material/check_circle:")

options = board["commodity"].tolist()
commodity_key = st.selectbox(
    "Commodity",
    options=options,
    format_func=catalog.commodity_label,
    key="trade_commodity",
)

item = prices.latest(commodity_key, market)
account = portfolio.get_account()
position = portfolio.get_position(commodity_key, market)

if item is None:
    ui.note("This mandi has no report for the selected commodity. Pick another crop.")
    st.stop()

st.markdown(f"#### {catalog.get_commodity(commodity_key).name} · latest report {item['date'].strftime('%d %b %Y')}")

metric_top = st.columns(2)
metric_top[0].metric(
    "Today's rate", f"₹{item['price']:,.0f}", f"{item['change_pct']:+.2f}%"
)
metric_top[1].metric("7-day range", f"₹{item['low_week']:,.0f}–₹{item['high_week']:,.0f}")
metric_bottom = st.columns(2)
metric_bottom[0].metric("Varieties quoted", f"{item['varieties']}")
metric_bottom[1].metric("Latest report", item["date"].strftime("%d %b %Y"))

st.space("medium")

order_column, position_column = st.columns([0.55, 0.45])

with order_column:
    with st.container(border=True):
        st.subheader("Place an order")
        side = st.segmented_control(
            "Side", options=["Buy", "Sell"], default="Buy", key="order_side"
        )
        side = side or "Buy"

        held = float(position["qty"]) if position else 0.0
        average_cost = float(position["avg_cost"]) if position else 0.0

        qty = st.number_input(
            "Quantity (quintal)",
            min_value=1,
            max_value=100_000,
            value=1,
            step=1,
            format="%d",
            key=f"qty_{commodity_key}_{side}",
        )

        estimated = float(qty) * item["price"]
        st.markdown(f"Estimated value: **{prices.inr(estimated)}**")

        if side == "Buy":
            affordable = int(account["cash"] // item["price"])
            st.caption(f"Cash {prices.inr(account['cash'])} · max {affordable:,} q")
        else:
            st.caption(f"You hold {held:g} quintal at this mandi.")

        if st.button(
            f"{side} {qty:g} quintal",
            type="primary",
            width="stretch",
            icon=":material/swap_horiz:",
        ):
            success, message = portfolio.execute_trade(
                commodity_key, market, side.lower(), float(qty), float(item["price"])
            )
            if success:
                st.session_state["trade_flash"] = message
                st.rerun()
            else:
                st.error(message, icon=":material/error:")

with position_column:
    with st.container(border=True):
        st.markdown("**Your position**")
        if position:
            current_value = held * item["price"]
            unrealized = (item["price"] - average_cost) * held
            unrealized_pct = (
                (item["price"] - average_cost) / average_cost * 100 if average_cost else 0.0
            )
            st.metric("Open quantity", f"{held:g} quintal")
            st.metric("Average cost", f"₹{average_cost:,.0f}")
            st.metric("Current value", prices.inr(current_value))
            st.metric(
                "Unrealised P&L",
                prices.inr(unrealized),
                f"{unrealized_pct:+.2f}%",
            )
        else:
            st.caption("No open position in this commodity at this mandi.")
            st.caption("Buy to start a position, then sell whenever you like.")

ui.section("Same crop, other mandis", "Cached reports from the other APMCs.")
comparison = prices.compare_markets(commodity_key, [item_key for item_key in catalog.MARKET_BY_KEY])
if comparison.empty:
    st.caption("No cached prices for this commodity elsewhere yet.")
else:
    comparison["spread_to_best"] = comparison["price"] - comparison["price"].max()
    table = comparison.rename(
        columns={
            "market_name": "Mandi",
            "state": "State",
            "price": "Price",
            "change_pct": "Day %",
            "spread_to_best": "vs best",
            "date": "Reported",
        }
    )[["Mandi", "State", "Price", "Day %", "vs best", "Reported"]]
    st.dataframe(
        table,
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(format="₹%d"),
            "Day %": st.column_config.NumberColumn(format="%+.2f%%"),
            "vs best": st.column_config.NumberColumn(format="₹%d"),
            "Reported": st.column_config.DateColumn(format="DD MMM YYYY"),
        },
    )

ui.section("Recent trades here")
trades = portfolio.get_trades(limit=100)
if not trades.empty:
    trades = trades[
        (trades["commodity"] == commodity_key) & (trades["market"] == market)
    ].head(5)

if trades.empty:
    st.caption("No trades in this commodity yet.")
else:
    recent = trades[["ts", "side", "qty", "price", "amount"]].rename(
        columns={
            "ts": "Time",
            "side": "Side",
            "qty": "Quantity",
            "price": "Price",
            "amount": "Value",
        }
    )
    recent["Side"] = recent["Side"].str.title()
    st.dataframe(
        recent,
        hide_index=True,
        column_config={
            "Price": st.column_config.NumberColumn(format="₹%d"),
            "Value": st.column_config.NumberColumn(format="₹%d"),
            "Quantity": st.column_config.NumberColumn(format="%g q"),
        },
    )
