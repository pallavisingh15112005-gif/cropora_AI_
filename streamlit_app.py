"""Cropora Mandi — live mandi prices and agricultural paper trading."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Cropora Mandi — live APMC prices",
    page_icon=":material/agriculture:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from trading import catalog, portfolio, prices, ui  # noqa: E402

ui.inject_css()
st.logo("assets/logo.svg", icon_image="assets/logo_mark.svg", size="large")
st.session_state.setdefault("market", "azadpur")


@st.dialog("Reset paper account")
def reset_dialog() -> None:
    st.write(
        "This clears every open position, trade and equity snapshot, then restores "
        "the starting cash. Live prices stay cached."
    )
    starting = st.number_input(
        "Starting cash (₹)",
        min_value=10_000,
        max_value=1_00_00_000,
        value=500_000,
        step=50_000,
        format="%d",
    )
    if st.button("Reset account", type="primary", icon=":material/restart_alt:"):
        portfolio.reset_account(float(starting))
        st.rerun()


with st.sidebar:
    st.space("small")
    market_keys = [market.key for market in catalog.MARKETS]
    st.selectbox(
        "Mandi",
        options=market_keys,
        format_func=catalog.market_label,
        key="market",
    )

    market = st.session_state.market
    account = portfolio.get_account()

    with st.container(border=True):
        st.metric("Cash available", prices.inr(account["cash"]))
        st.caption(
            f"Paper account · started with {prices.inr(account['starting_cash'])}"
        )

    status = prices.feed_status(market)
    data_day = prices.data_date(market)
    online = status["rows"] > 0
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:.5rem;font-size:.78rem;margin:.2rem 0 .35rem">
          <span style="width:8px;height:8px;border-radius:50%;background:{'#84CC16' if online else '#FBBF24'}"></span>
          <span style="color:{'#D9F99D' if online else '#FDE68A'};font-weight:600">
            {'Agmarknet feed ready' if online else 'Waiting for first sync'}
          </span>
        </div>
        <div style="font-size:.74rem;color:#9CAEA0;line-height:1.55">
          Latest report: <b style="color:#E7E5E4">{data_day.strftime('%d %b %Y') if data_day else '—'}</b><br/>
          Synced: {ui._e(prices.sync_label(market))} · {status['items']} of {status['coverage']} commodities
        </div>
        """,
        unsafe_allow_html=True,
    )
    if status.get("partial"):
        st.caption("First sync loads popular crops. **Refresh** pulls the whole mandi.")

    if st.button("Refresh live data", icon=":material/sync:", width="stretch"):
        with st.spinner("Pulling the latest APMC reports…"):
            result = prices.refresh(market)
        if result["rows"]:
            st.toast("Live prices updated", icon=":material/check_circle:")
        else:
            st.toast("Agmarknet did not return data. Try again shortly.", icon=":material/error:")
        st.rerun()

    if st.button("Reset account", icon=":material/restart_alt:", width="stretch"):
        reset_dialog()

    st.space("small")
    st.caption(
        "Prices are real Agmarknet APMC reports. Trading is simulated and no real "
        "money is involved — not investment advice."
    )

pages = [
    st.Page("app_pages/home.py", title="Overview", icon=":material/space_dashboard:", default=True),
    st.Page("app_pages/markets.py", title="Price board", icon=":material/storefront:"),
    st.Page("app_pages/compare.py", title="Compare mandis", icon=":material/compare_arrows:"),
    st.Page("app_pages/assistant.py", title="Ask rates", icon=":material/forum:"),
    st.Page("app_pages/trade.py", title="Trade", icon=":material/swap_horiz:"),
    st.Page("app_pages/portfolio.py", title="Portfolio", icon=":material/account_balance_wallet:"),
]

page = st.navigation(pages)
page.run()
