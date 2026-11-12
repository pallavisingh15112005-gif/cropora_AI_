"""Cropora Mandi — compare one commodity across mandis."""

from __future__ import annotations

import streamlit as st

from trading import catalog, prices, ui
from trading.charts import market_compare_chart

market = st.session_state.market

with st.spinner("Syncing the latest Agmarknet reports…"):
    prices.ensure_feed(market)

st.title("Compare mandis")
st.caption(
    "The same crop rarely sells for the same price everywhere. Compare the latest "
    "reported rate across APMCs before you trade."
)

board = prices.snapshot(market)
options = board["commodity"].tolist() if not board.empty else [item.key for item in catalog.COMMODITIES]

controls = st.columns([0.45, 0.55], vertical_alignment="bottom")
with controls[0]:
    commodity_key = st.selectbox(
        "Commodity",
        options=options,
        format_func=catalog.commodity_label,
        key="compare_commodity",
    )
with controls[1]:
    selected = st.multiselect(
        "Mandis",
        options=[item.key for item in catalog.MARKETS],
        default=[market, "vashi", "bengaluru", "kolar"][:4],
        format_func=catalog.market_label,
        key="compare_markets",
    )

selected = list(dict.fromkeys([market, *selected]))

fetch = st.button("Fetch latest from these mandis", icon=":material/sync:", type="primary")

frame = prices.compare_markets(commodity_key, selected)

# First visit (or a new selection) fills gaps automatically so the comparison
# is useful without making the user press the button.
signature = f"{commodity_key}|{','.join(sorted(selected))}"
needs_data = len(frame) < len(selected)
if fetch or (len(frame) < 2 and needs_data and st.session_state.get("compare_auto") != signature):
    st.session_state["compare_auto"] = signature
    with st.spinner("Pulling the latest report from each mandi… this can take a minute."):
        frame = prices.compare_markets(commodity_key, selected, refresh=True)

commodity = catalog.get_commodity(commodity_key)
ui.section(
    f"{commodity.name} across mandis",
    "Median price of the reported varieties, ₹ per quintal.",
)

if frame.empty:
    ui.note(
        "<strong>No cached prices.</strong> Press <em>Fetch latest</em> to pull this "
        "commodity from the selected mandis."
    )
    st.stop()

missing = [key for key in selected if key not in set(frame["market"])]
if missing:
    ui.note(
        "No report in the current cache for: "
        + ", ".join(catalog.get_market(key).name for key in missing)
        + ". Agmarknet may not publish this crop for that mandi — try another crop or mandi."
    )

if len(frame) < 2:
    ui.stat_cards(
        [
            ("Mandi with data", f"{len(frame)}", "only one report available"),
            ("Rate", f"₹{frame.iloc[0]['price']:,.0f}", f"{frame.iloc[0]['market_name']}, {frame.iloc[0]['state']}"),
            ("Reported", frame.iloc[0]["date"].strftime("%d %b %Y"), "latest Agmarknet report"),
            ("Tip", "Add mandis", "pick more APMCs above to compare"),
        ]
    )
else:
    best = frame.iloc[0]
    worst = frame.iloc[-1]
    spread = best["price"] - worst["price"]
    spread_pct = (spread / worst["price"] * 100) if worst["price"] else 0.0

    ui.stat_cards(
        [
            ("Highest", f"₹{best['price']:,.0f}", f"{best['market_name']}, {best['state']}"),
            ("Lowest", f"₹{worst['price']:,.0f}", f"{worst['market_name']}, {worst['state']}"),
            ("Spread", f"₹{spread:,.0f}", f"{spread_pct:+.1f}% between mandis"),
            ("Mandis", f"{len(frame)}", "with a live report"),
        ]
    )

    st.altair_chart(market_compare_chart(frame), width="stretch")

table = frame.copy()
table["change_pct"] = table["change_pct"].map(lambda value: f"{value:+.2f}%")
table = table.rename(
    columns={
        "market_name": "Mandi",
        "state": "State",
        "price": "Price",
        "change_pct": "Day change",
        "date": "Reported",
        "varieties": "Varieties",
    }
)[["Mandi", "State", "Price", "Day change", "Varieties", "Reported"]]

st.dataframe(
    table,
    hide_index=True,
    column_config={
        "Price": st.column_config.NumberColumn(format="₹%d"),
        "Varieties": st.column_config.NumberColumn(format="%d"),
        "Reported": st.column_config.DateColumn(format="DD MMM YYYY"),
    },
)

st.caption(
    "Spread is informational only. Freight, mandi charges, grading and local demand "
    "decide whether a real arbitrage exists."
)
