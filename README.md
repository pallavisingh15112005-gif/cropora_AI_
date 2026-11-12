# Cropora Mandi

Live mandi prices from government APMC reports, plus a paper-trading desk for
Indian agricultural commodities — vegetables, fruits, cereals, pulses, and cash
crops. Track real rates, compare mandis, ask a rate chatbot, and place simulated
buy and sell orders.

Built with Streamlit. Prices come from the public, keyless
[Agmarknet](https://agmarknet.gov.in/) API (`api.agmarknet.gov.in/v1`), so the
numbers are actual APMC reports — not a random walk.

> **Paper trading.** Prices are real, but every order is simulated. No real
> money, brokerage, or settlement is involved, and nothing here is investment
> advice.

## Features

- **Overview** — a live dashboard: market hero, ticker, commodity cards with
  seven-day sparklines, gainers/losers, and quick actions.
- **Price board** — every commodity the selected mandi reported in the last
  week, with today's rate, day change, weekly range, variety count, search and
  category filters, a sortable table, and a full price-trend chart.
- **Compare mandis** — the same crop across APMCs, with the highest/lowest
  price, spread, bar chart, and a mandi-wise table.
- **Ask rates** — a rule-based chatbot for questions like *"tomato ka rate kya
  hai?"*, *"wheat price in Ludhiana"*, *"sabse sasta kaun hai?"* or *"compare
  onion and potato"*. Works in English and Hinglish, no API key needed.
- **Trade** — today's real rate, instant paper fills, cash and position checks,
  unrealised P&L, and the same crop at other mandis.
- **Portfolio** — equity, cash, holdings marked to live prices, total P&L,
  equity curve, trade history, and CSV export.

## Run locally

```bash
git clone https://github.com/pallavisingh15112005-gif/cropora_AI_.git
cd cropora_AI_

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app opens at http://localhost:8501. The first load for a mandi fetches a
starter basket of popular crops from Agmarknet and can take a minute; after
that the cache is used. Use **Refresh live data** in the sidebar to pull the
mandi's full commodity list.

## Project structure

```
streamlit_app.py        App entry, sidebar, navigation, refresh and reset
app_pages/
  home.py               Live overview dashboard
  markets.py            Price board, filters and price-trend detail
  compare.py            Cross-mandi price comparison
  assistant.py          Chatbot for mandi rate questions
  trade.py              Order ticket and position summary
  portfolio.py          Holdings, equity curve, trade history
trading/
  agmarknet.py          Agmarknet client, market directory, SQLite price archive
  prices.py             Page-facing API, formatting helpers
  catalog.py            Commodity and mandi definitions with Agmarknet ids
  assistant.py          Rule-based English/Hinglish rate chatbot
  charts.py             Altair chart builders
  portfolio.py          SQLite paper-trading account
  ui.py                 Design system and custom HTML blocks
data/market.db          Local price archive (gitignored)
data/mandi.db           Local paper account (gitignored)
```

## Data

Every quote comes from the Agmarknet report
`/prices-and-arrivals/commodity-price/lastweek`, which returns one week of daily
prices per market/commodity. Agmarknet lists the same mandi under different
market ids for different crops, so the app keeps a small directory
(`list-comm/<commodity>`) that maps each mandi to the ids that actually report
each commodity.

Responses are cached in `data/market.db` and treated as fresh for 12 hours. The
archive grows every time the app runs, so charts gain history over time. Use
**Refresh live data** in the sidebar to pull the newest reports on demand.

Agmarknet is rate-limited and occasionally slow; if a call fails the app keeps
serving the last cached report and shows a note. Only one keyless report
endpoint is used — no captcha, no API key, no secrets.

## Paper account

- Starting cash: ₹5,00,000 (configurable on reset).
- Orders fill immediately at the latest reported median price for that
  commodity and mandi.
- Positions are tracked per commodity **and** mandi, and marked to live prices.
- The account is stored in `data/mandi.db` and can be reset from the sidebar.

## Deploy

Push the repository to GitHub, then create a Streamlit Community Cloud app with
`streamlit_app.py` as the entry point. No secrets are required. The free tier
has an ephemeral filesystem, so the SQLite cache resets when the app restarts —
the first load then refetches from Agmarknet.

## Disclaimer

Educational demo only. Prices are real Agmarknet reports but may be delayed or
incomplete; fills are simulated, with no brokerage or settlement. Do not use it
to make real trading decisions.
