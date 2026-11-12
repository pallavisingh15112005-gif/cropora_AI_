"""Chat with the mandi rate assistant."""

from __future__ import annotations

import streamlit as st

from trading import assistant, catalog, prices, ui

market = st.session_state.market

with st.spinner("Syncing the latest Agmarknet reports…"):
    prices.ensure_feed(market)

data_day = prices.data_date(market)
summary = prices.market_summary(market)

st.title("Ask rates")
st.caption(
    f"{catalog.market_label(market)} · latest report "
    f"{data_day.strftime('%d %b %Y') if data_day else 'not available'} · "
    f"{summary['items']} commodities"
)
st.caption(
    "Ask in English or Hinglish. Mention a commodity and, if you like, a mandi — "
    "for example “apple rate in Mumbai”."
)

if summary["error"]:
    ui.note(
        "<strong>Some Agmarknet calls failed.</strong> Answers use the last cached "
        "reports. Press refresh in the sidebar to retry."
    )

st.session_state.setdefault("rate_chat", [])

if st.session_state.rate_chat:
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Clear chat", icon=":material/delete_sweep:"):
            st.session_state.rate_chat = []
            st.rerun()

for message in st.session_state.rate_chat:
    avatar = ":material/agriculture:" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

suggestions = [
    "Tomato ka rate kya hai?",
    "Wheat price in Ludhiana",
    "Top gainers today",
    "Sabse sasta kaun hai?",
]

choice = None
if not st.session_state.rate_chat:
    choice = st.pills("Try asking", options=suggestions, label_visibility="collapsed")

prompt = st.chat_input(
    "Ask about a rate, e.g. onion ka bhav kya hai?",
    submit_mode="disable",
)

if choice and not prompt:
    prompt = choice

if prompt:
    st.session_state.rate_chat.append({"role": "user", "content": prompt})
    st.session_state.rate_chat.append(
        {"role": "assistant", "content": assistant.answer(prompt, market)}
    )
    st.rerun()

st.caption(
    "Answers are built from live Agmarknet reports for the selected mandi, and are "
    "not investment advice."
)
