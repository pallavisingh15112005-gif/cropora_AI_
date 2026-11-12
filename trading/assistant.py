"""Cropora Mandi — rule-based rate assistant for the live feed.

Answers are built directly from the latest Agmarknet reports, so every rate
carries the mandi name and the date it was reported. No API key is needed.
"""

from __future__ import annotations

import re

from . import catalog, prices

HELP = """Ask me for a mandi rate. Examples:

- **Tomato ka rate kya hai?**
- **Wheat price in Ludhiana**
- **Compare onion and potato**
- **Top gainers today**
- **Sabse sasta kaun hai?**
- **Which fruits are available?**

You can name any mandi — for example *"apple rate in Mumbai"* — and I will use
its latest Agmarknet report."""

_EXTRA_ALIASES = {
    "tamatar": "tomato",
    "pyaz": "onion",
    "kanda": "onion",
    "aloo": "potato",
    "gobhi": "cauliflower",
    "phool gobhi": "cauliflower",
    "patta gobhi": "cabbage",
    "mirch": "green_chilli",
    "hari mirch": "green_chilli",
    "chilli": "green_chilli",
    "chili": "green_chilli",
    "lehsun": "garlic",
    "adrak": "ginger",
    "seb": "apple",
    "kela": "banana",
    "aam": "mango",
    "anar": "pomegranate",
    "angoor": "grapes",
    "gehun": "wheat",
    "dhan": "paddy",
    "paddy": "paddy",
    "rice": "rice",
    "chawal": "rice",
    "basmati": "basmati",
    "makka": "maize",
    "corn": "maize",
    "soya": "soybean",
    "soyabean": "soybean",
    "chana": "gram",
    "sarson": "mustard",
    "kapas": "cotton",
}

_MARKET_ALIASES = {
    "delhi": "azadpur",
    "azadpur": "azadpur",
    "mumbai": "vashi",
    "vashi": "vashi",
    "navi mumbai": "vashi",
    "bangalore": "bengaluru",
    "bengaluru": "bengaluru",
    "binny mill": "bengaluru",
    "kolar": "kolar",
    "indore": "indore",
    "madhya pradesh": "indore",
    "ludhiana": "ludhiana",
    "punjab": "ludhiana",
    "lasalgaon": "lasalgaon",
    "nashik": "lasalgaon",
    "nasik": "lasalgaon",
    "hyderabad": "bowenpally",
    "bowenpally": "bowenpally",
    "telangana": "bowenpally",
}


def _aliases() -> dict[str, str]:
    aliases = dict(_EXTRA_ALIASES)
    for commodity in catalog.COMMODITIES:
        aliases[commodity.key] = commodity.key
        aliases[commodity.name.lower()] = commodity.key
        aliases[commodity.local_name.lower()] = commodity.key
    return aliases


ALIASES = _aliases()


def _find(aliases: dict[str, str], text: str) -> list[str]:
    padded = f" {text.lower()} "
    hits: list[tuple[int, str]] = []
    for alias in sorted(aliases, key=len, reverse=True):
        pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?:s|es)?(?![a-z0-9])"
        match = re.search(pattern, padded)
        if match:
            hits.append((match.start(), aliases[alias]))
    hits.sort(key=lambda item: item[0])
    found: list[str] = []
    for _, value in hits:
        if value not in found:
            found.append(value)
    return found


def detect_commodities(question: str) -> list[str]:
    return _find(ALIASES, question)


def detect_market(question: str) -> str | None:
    markets = _find(_MARKET_ALIASES, question)
    return markets[0] if markets else None


def _has(question: str, *words: str) -> bool:
    return any(word in question for word in words)


def _date_label(market: str) -> str:
    day = prices.data_date(market)
    return day.strftime("%d %b %Y") if day else "the latest report"


def _price_block(commodity_key: str, market: str) -> str:
    item = prices.latest(commodity_key, market)
    commodity = catalog.get_commodity(commodity_key)
    if item is None:
        return (
            f"**{commodity.name} ({commodity.local_name})** — no trade reported at "
            f"{catalog.market_label(market)} in the last week."
        )
    arrow = "▲" if item["change_pct"] > 0.05 else "▼" if item["change_pct"] < -0.05 else "•"
    varieties = ", ".join(item["variety_names"][:4]) or "—"
    return (
        f"**{commodity.name} ({commodity.local_name}) — ₹{item['price']:,.0f} per quintal**  \n"
        f"{arrow} {item['change_pct']:+.2f}% vs previous report · reported {item['date'].strftime('%d %b %Y')}  \n"
        f"7-day range ₹{item['low_week']:,.0f}–₹{item['high_week']:,.0f} · "
        f"{item['varieties']} {'variety' if item['varieties'] == 1 else 'varieties'} ({varieties})"
    )


def _extremes(market: str, *, cheapest: bool) -> str:
    frame = prices.snapshot(market)
    if frame.empty:
        return f"No prices are cached for {catalog.market_label(market)} yet. Open the Price board and sync."
    frame = frame.sort_values("price", ascending=cheapest).head(5)
    title = "Cheapest" if cheapest else "Costliest"
    lines = [
        f"{index}. **{row.local_name} ({catalog.get_commodity(row.commodity).name})** "
        f"— ₹{row.price:,.0f}"
        for index, row in enumerate(frame.itertuples(), start=1)
    ]
    return (
        f"**{title} at {catalog.market_label(market)}** ({_date_label(market)})\n\n"
        + "\n".join(lines)
    )


def _movers(market: str, *, gainers: bool) -> str:
    frame = prices.snapshot(market)
    if frame.empty:
        return f"No prices are cached for {catalog.market_label(market)} yet."
    frame = frame.sort_values("change_pct", ascending=not gainers).head(3)
    title = "Top gainers" if gainers else "Top losers"
    lines = [
        f"- **{row.local_name} ({catalog.get_commodity(row.commodity).name})** — "
        f"₹{row.price:,.0f} ({row.change_pct:+.2f}%)"
        for row in frame.itertuples()
    ]
    return f"**{title} at {catalog.market_label(market)}** ({_date_label(market)})\n\n" + "\n".join(lines)


def _catalog_list(market: str) -> str:
    frame = prices.snapshot(market)
    if frame.empty:
        return "No commodities are cached for this mandi yet."
    lines = []
    for category in catalog.CATEGORIES:
        items = frame[frame["category"] == category]
        if items.empty:
            continue
        names = ", ".join(
            f"{row.local_name} ({catalog.get_commodity(row.commodity).name})"
            for row in items.itertuples()
        )
        lines.append(f"**{category}:** {names}")
    return (
        f"**Traded at {catalog.market_label(market)}** ({_date_label(market)})\n\n"
        + "\n\n".join(lines)
    )


def answer(question: str, default_market: str) -> str:
    """Build a reply for a free-text question about live mandi rates."""
    text = question.strip().lower()
    if not text:
        return HELP

    market = detect_market(text) or default_market
    commodities = detect_commodities(text)

    if _has(text, "help", "madad", "kaise use", "example", "kya puch", "what can you"):
        return HELP

    if len(commodities) >= 2:
        blocks = [_price_block(key, market) for key in commodities[:3]]
        header = f"**Comparison at {catalog.market_label(market)}** ({_date_label(market)})\n\n"
        quotes = [prices.latest(key, market) for key in commodities[:2]]
        if all(quotes):
            diff = quotes[0]["price"] - quotes[1]["price"]
            if not diff:
                delta = "Both are at the same price."
            else:
                higher = catalog.get_commodity(
                    commodities[0] if diff > 0 else commodities[1]
                ).name
                delta = f"{higher} is ₹{abs(diff):,.0f} per quintal higher."
            return header + "\n\n".join(blocks) + f"\n\n**Difference:** {delta}"
        return header + "\n\n".join(blocks)

    if _has(text, "sasta", "sasti", "sabse kam", "cheap", "lowest", "minimum"):
        return _extremes(market, cheapest=True)

    if _has(text, "mahanga", "mehnga", "sabse zyada", "costliest", "expensive", "highest", "maximum"):
        return _extremes(market, cheapest=False)

    if _has(text, "gainer", "gain", "badh", "badh raha", "tezi", "rising", "increase"):
        return _movers(market, gainers=True)

    if _has(text, "loser", "gir", "girawat", "falling", "decrease", "down"):
        return _movers(market, gainers=False)

    if _has(text, "list", "kaun kaun", "kya kya", "available", "commodities", "sab batao"):
        return _catalog_list(market)

    if commodities:
        blocks = [_price_block(key, market) for key in commodities[:3]]
        return (
            f"**Rates at {catalog.market_label(market)}** ({_date_label(market)})\n\n"
            + "\n\n".join(blocks)
        )

    if _has(text, "rate", "bhav", "price", "kitna", "kya chal", "today", "aaj"):
        frame = prices.snapshot(market)
        if frame.empty:
            return f"No prices are cached for {catalog.market_label(market)} yet."
        popular = ["tomato", "onion", "potato", "wheat", "paddy", "apple"]
        available = [key for key in popular if key in set(frame["commodity"])]
        blocks = [
            f"- **{catalog.get_commodity(key).local_name.title()} "
            f"({catalog.get_commodity(key).name})** — ₹{prices.latest(key, market)['price']:,.0f}"
            for key in available[:6]
        ]
        return (
            f"**Today at {catalog.market_label(market)}** ({_date_label(market)})\n\n"
            + "\n".join(blocks)
            + "\n\nName a commodity for its full rate, or ask for gainers and losers."
        )

    return HELP
