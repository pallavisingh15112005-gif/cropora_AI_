"""Cropora Mandi — full price board with a trend detail view."""

from __future__ import annotations

import streamlit as st

from trading import catalog, prices, ui
from trading.charts import price_chart, variety_chart

market = st.session_state.market

with st.spinner("Syncing the latest Agmarknet reports…"):
    prices.ensure_feed(market)

board = prices.snapshot(market)
data_day = prices.data_date(market)

st.title("Mandi price board")
st.caption(
    f"{catalog.market_label(market)} · ₹ per quintal · latest Agmarknet report "
    f"{data_day.strftime('%d %b %Y') if data_day else 'not available'}"
)
st.badge("Live government data", icon=":material/verified:", color="green")

if board.empty:
    ui.note(
        "<strong>Nothing cached for this mandi yet.</strong> Use the refresh button in "
        "the sidebar, or try another APMC."
    )
    st.stop()

st.space("small")

category = st.pills(
    "Category",
    options=["All", "Vegetables", "Fruits", "Cereals", "Pulses & oilseeds", "Cash crops"],
    default="All",
    key="board_category",
)
query = st.text_input(
    "Search",
    placeholder="Search tomato, wheat, apple…",
    label_visibility="collapsed",
    key="board_search",
)

filtered = board.copy()
if category and category != "All":
    filtered = filtered[filtered["category"] == category]
if query:
    needle = query.strip().lower()
    filtered = filtered[
        filtered["commodity"].str.lower().str.contains(needle)
        | filtered["local_name"].str.lower().str.contains(needle)
        | filtered["category"].str.lower().str.contains(needle)
    ]

ui.section(
    "Live cards",
    f"{len(filtered)} of {len(board)} commodities · pick one below for the full trend.",
)
ui.commodity_grid(prices.card_rows(filtered))

ui.section("Full board", "Sorted by the latest reported price.")
table = filtered.copy()
table["name"] = table["commodity"].map(lambda key: catalog.get_commodity(key).name)
table = table[
    ["name", "local_name", "category", "price", "change_pct", "low_week", "high_week", "varieties", "date"]
].rename(
    columns={
        "name": "Commodity",
        "local_name": "Local name",
        "category": "Category",
        "price": "Price",
        "change_pct": "Day %",
        "low_week": "7d low",
        "high_week": "7d high",
        "varieties": "Varieties",
        "date": "Reported",
    }
)
st.dataframe(
    table,
    hide_index=True,
    height=min(480, 38 * len(table) + 42),
    column_config={
        "Price": st.column_config.NumberColumn(format="₹%d"),
        "Day %": st.column_config.NumberColumn(format="%+.2f%%"),
        "7d low": st.column_config.NumberColumn(format="₹%d"),
        "7d high": st.column_config.NumberColumn(format="₹%d"),
        "Varieties": st.column_config.NumberColumn(format="%d"),
        "Reported": st.column_config.DateColumn(format="DD MMM YYYY"),
    },
)

if table.empty:
    st.caption("No commodity matches this filter.")
    st.stop()

ui.section("Price trend", "Real reported prices, not an estimate.")
controls = st.container(horizontal=True, vertical_alignment="bottom")
with controls:
    commodity_key = st.selectbox(
        "Commodity",
        options=board["commodity"].tolist(),
        format_func=catalog.commodity_label,
        key="trend_commodity",
    )

item = prices.latest(commodity_key, market)
series = prices.history(commodity_key, market)
commodity = catalog.get_commodity(commodity_key)

st.markdown(f"#### {commodity.name} · {commodity.local_name}")

metric_top = st.columns(3)
metric_top[0].metric(
    "Latest rate", f"₹{item['price']:,.0f}", f"{item['change_pct']:+.2f}%"
)
metric_top[1].metric("7-day low", f"₹{item['low_week']:,.0f}")
metric_top[2].metric("7-day high", f"₹{item['high_week']:,.0f}")

metric_bottom = st.columns(3)
metric_bottom[0].metric("Reported", item["date"].strftime("%d %b"))
metric_bottom[1].metric("Varieties", f"{item['varieties']}")
metric_bottom[2].metric(
    "Day spread", f"₹{item['low']:,.0f}–₹{item['high']:,.0f}"
)

st.altair_chart(price_chart(series), width="stretch")
st.caption(
    "Median of every variety reported that day · shaded band shows the lowest and "
    "highest variety price."
)

varieties = prices.variety_history(commodity_key, market)
if len(varieties) > 1:
    with st.expander("Variety-wise rates", icon=":material/category:"):
        st.altair_chart(variety_chart(varieties), width="stretch")
        detail = varieties.copy()
        detail["date"] = detail["date"].dt.strftime("%d %b %Y")
        st.dataframe(
            detail.rename(
                columns={
                    "date": "Reported",
                    "variety": "Variety",
                    "price": "Price",
                }
            ),
            hide_index=True,
            column_config={"Price": st.column_config.NumberColumn(format="₹%d")},
        )
