"""Cropora Mandi — shared look and feel.

Small helpers that inject the design system and render the custom HTML blocks
(hero, ticker, commodity cards) used across the pages.
"""

from __future__ import annotations

import html
from datetime import date, datetime

import streamlit as st

GREEN = "#14532D"
GREEN_SOFT = "#166534"
LIME = "#84CC16"
CREAM = "#FAF8F3"
INK = "#1C1917"
MUTED = "#78716C"
LINE = "#E7E2D8"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: "Plus Jakarta Sans", "Inter", -apple-system, "Segoe UI", sans-serif;
}}
.stApp {{ background: {CREAM}; color: {INK}; }}
.block-container {{ padding-top: 2.1rem; padding-bottom: 3rem; max-width: 1200px; }}
h1, h2, h3, h4 {{ letter-spacing: -0.02em; color: {INK}; }}
h1 {{ font-weight: 800; }}
h2 {{ font-weight: 700; }}
p, li, .stCaption, [data-testid="stCaptionContainer"] {{ color: #57534E; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: #10241A;
    border-right: 1px solid rgba(255,255,255,0.06);
}}
[data-testid="stSidebar"] * {{ color: #E7E5E4; }}
[data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] small {{ color: #A8B5A8 !important; }}
[data-testid="stSidebar"] [data-testid="stMetricValue"] {{ color: #F5F5F4; font-size: 1.55rem; }}
[data-testid="stSidebar"] [data-testid="stMetricLabel"] {{ color: #9CAEA0; }}
[data-testid="stSidebar"] [data-testid="stMetric"] {{
    background: rgba(255,255,255,0.05);
    border-color: rgba(255,255,255,0.10);
    box-shadow: none;
}}
[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {{
    background: rgba(255,255,255,0.04);
    border-color: rgba(255,255,255,0.10);
    box-shadow: none;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
    background: rgba(255,255,255,0.06);
    border-color: rgba(255,255,255,0.14);
    color: #F5F5F4;
}}
[data-testid="stSidebar"] [data-baseweb="select"] * {{ color: #F5F5F4; }}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {{ border-radius: 10px; }}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {{ background: rgba(132,204,22,0.12); }}
[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: rgba(132,204,22,0.16);
    border-left: 3px solid {LIME};
}}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.08); }}

/* Buttons */
.stButton > button, .stFormSubmitButton > button {{
    border-radius: 11px;
    font-weight: 600;
    border: 1px solid {LINE};
    transition: all .15s ease;
}}
.stButton > button[kind="primary"] {{
    background: {GREEN};
    border-color: {GREEN};
    box-shadow: 0 6px 16px rgba(20,83,45,.18);
    color: #FFFFFF;
}}
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {{ color: #FFFFFF !important; }}
.stButton > button[kind="primary"]:hover {{
    background: {GREEN_SOFT};
    border-color: {GREEN_SOFT};
    transform: translateY(-1px);
}}
[data-testid="stSidebar"] .stButton > button {{
    background: rgba(255,255,255,0.07);
    border-color: rgba(255,255,255,0.14);
    color: #F5F5F4;
}}
[data-testid="stSidebar"] .stButton > button:hover {{ border-color: {LIME}; }}

/* Metric cards */
[data-testid="stMetric"] {{
    background: #FFFFFF;
    border: 1px solid {LINE};
    border-radius: 16px;
    padding: .85rem .95rem;
    box-shadow: 0 1px 2px rgba(28,25,23,.04);
}}
[data-testid="stMetricLabel"] {{ color: {MUTED}; font-weight: 500; }}
[data-testid="stMetricValue"] {{ font-weight: 700; letter-spacing: -0.02em; font-size: 1.4rem; }}
[data-testid="stMetricValue"] p, [data-testid="stMetricValue"] div {{ font-size: inherit; }}
[data-testid="stMetricDelta"] {{ font-size: .8rem; }}

/* Inputs and containers */
[data-baseweb="input"], [data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {{
    border-radius: 11px !important;
}}
[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 18px;
    border-color: {LINE};
    background: #FFFFFF;
    box-shadow: 0 1px 2px rgba(28,25,23,.04);
}}
[data-testid="stDataFrame"] {{
    border-radius: 14px;
    border: 1px solid {LINE};
    overflow: hidden;
}}
[data-testid="stChatMessage"] {{
    background: #FFFFFF;
    border: 1px solid {LINE};
    border-radius: 16px;
    padding: .35rem .6rem;
}}

/* Tabs / pills */
[data-testid="stPills"] button {{ border-radius: 999px; }}
[data-testid="stExpander"] details {{ border-radius: 14px; border-color: {LINE}; }}

/* Custom blocks */
.cr-hero {{
    position: relative;
    overflow: hidden;
    border-radius: 24px;
    padding: 2.1rem 2.2rem 1.9rem;
    background:
        radial-gradient(1100px 420px at 85% -10%, rgba(132,204,22,.28), transparent 60%),
        linear-gradient(135deg, #0B2216 0%, #14532D 55%, #1B6B3A 100%);
    color: #F7FEE8;
    box-shadow: 0 18px 40px rgba(20,83,45,.22);
    margin-bottom: 1.6rem;
}}
.cr-hero:after {{
    content: "";
    position: absolute;
    inset: 0;
    background-image: radial-gradient(rgba(255,255,255,.10) 1px, transparent 1px);
    background-size: 22px 22px;
    opacity: .35;
    pointer-events: none;
}}
.cr-hero h1 {{
    color: #FFFFFF;
    font-size: 2.15rem;
    line-height: 1.08;
    margin: 0 0 .5rem 0;
    font-weight: 800;
}}
.cr-hero p {{ color: #C7E0C9; margin: 0; max-width: 60ch; font-size: .98rem; }}
.cr-hero .cr-eyebrow {{
    display: inline-flex; align-items: center; gap: .45rem;
    font-size: .74rem; letter-spacing: .14em; text-transform: uppercase;
    font-weight: 700; color: #BEF264; margin-bottom: .85rem;
}}
.cr-hero .cr-meta {{ display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.35rem; }}
.cr-chip {{
    display: inline-flex; align-items: center; gap: .4rem;
    padding: .38rem .8rem;
    border-radius: 999px;
    background: rgba(255,255,255,.12);
    border: 1px solid rgba(255,255,255,.18);
    font-size: .8rem; font-weight: 600; color: #F7FEE8;
}}
.cr-dot {{ width: 8px; height: 8px; border-radius: 50%; background: {LIME}; box-shadow: 0 0 0 4px rgba(132,204,22,.18); }}
.cr-dot.amber {{ background: #FBBF24; box-shadow: 0 0 0 4px rgba(251,191,36,.18); }}
.cr-dot.red {{ background: #F87171; box-shadow: 0 0 0 4px rgba(248,113,113,.18); }}

.cr-ticker {{
    display: flex; flex-wrap: wrap; gap: .45rem; padding: .15rem 0 .7rem;
}}
.cr-tick {{
    display: inline-flex; align-items: center; gap: .45rem;
    background: #FFFFFF;
    border: 1px solid {LINE};
    border-radius: 999px;
    padding: .34rem .72rem;
}}
.cr-tick .t-name {{ font-size: .74rem; color: {MUTED}; font-weight: 600; letter-spacing: .02em; }}
.cr-tick .t-price {{ font-size: .82rem; font-weight: 700; }}
.cr-tick .t-chg {{ font-size: .72rem; font-weight: 600; }}
.up {{ color: {GREEN_SOFT}; }}
.down {{ color: #B91C1C; }}
.flat {{ color: {MUTED}; }}

.cr-section {{ margin: 2.1rem 0 .9rem; }}
.cr-section h3 {{ margin: 0; font-size: 1.16rem; font-weight: 700; }}
.cr-section p {{ margin: .18rem 0 0; color: {MUTED}; font-size: .86rem; }}

.cr-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(195px, 1fr));
    gap: .8rem;
}}
.cr-card {{
    background: #FFFFFF;
    border: 1px solid {LINE};
    border-radius: 18px;
    padding: 1rem 1.05rem .9rem;
    box-shadow: 0 1px 2px rgba(28,25,23,.04);
    transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
}}
.cr-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 14px 28px rgba(28,25,23,.08);
    border-color: #D5CFC2;
}}
.cr-card .c-top {{ display: flex; justify-content: space-between; align-items: flex-start; gap: .4rem; }}
.cr-card .c-name {{
    font-weight: 700; font-size: .95rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.cr-card .c-local {{
    color: {MUTED}; font-size: .71rem; font-weight: 500;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 130px;
}}
.cr-card .c-tag {{
    font-size: .58rem; letter-spacing: .05em; text-transform: uppercase;
    background: #F1F5EE; color: {GREEN_SOFT}; border-radius: 999px;
    padding: .14rem .42rem; font-weight: 700; white-space: nowrap; flex: 0 0 auto;
}}
.cr-card .c-price {{ font-size: 1.3rem; font-weight: 800; margin-top: .6rem; letter-spacing: -.02em; }}
.cr-card .c-unit {{ font-size: .72rem; color: {MUTED}; font-weight: 500; }}
.cr-card .c-change {{ font-size: .8rem; font-weight: 700; margin-top: .1rem; }}
.cr-card .c-spark {{ margin-top: .55rem; height: 42px; }}
.cr-card .c-foot {{ display: flex; justify-content: space-between; font-size: .68rem; color: {MUTED}; margin-top: .35rem; }}

.cr-stat {{
    background: #FFFFFF; border: 1px solid {LINE}; border-radius: 16px;
    padding: .95rem 1.05rem;
}}
.cr-stat .s-label {{ font-size: .72rem; text-transform: uppercase; letter-spacing: .09em; color: {MUTED}; font-weight: 700; }}
.cr-stat .s-value {{ font-size: 1.5rem; font-weight: 800; letter-spacing: -.02em; margin-top: .2rem; }}
.cr-stat .s-note {{ font-size: .75rem; color: {MUTED}; margin-top: .1rem; }}

.cr-note {{
    background: #FFFDF5; border: 1px solid #F2E7C9; border-left: 3px solid #D97706;
    border-radius: 12px; padding: .7rem .9rem; font-size: .82rem; color: #78350F;
}}
.cr-note strong {{ color: #92400E; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def _e(value: object) -> str:
    return html.escape(str(value))


def spark_svg(values: list[float], *, up: bool = True, width: int = 210, height: int = 42) -> str:
    if not values:
        return ""
    values = [float(value) for value in values]
    low, high = min(values), max(values)
    span = (high - low) or 1.0
    flat = high == low
    step = width / max(len(values) - 1, 1)
    points = [
        (
            index * step,
            height / 2 if flat else height - 4 - ((value - low) / span) * (height - 8),
        )
        for index, value in enumerate(values)
    ]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = f"0,{height} " + line + f" {width},{height}"
    color = GREEN_SOFT if up else "#B91C1C"
    fill = "#166534" if up else "#B91C1C"
    if flat:
        return (
            f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
            f'preserveAspectRatio="none" aria-hidden="true">'
            f'<line x1="0" y1="{height / 2:.1f}" x2="{width}" y2="{height / 2:.1f}" '
            f'stroke="{MUTED}" stroke-width="1.6" stroke-dasharray="4 4" opacity="0.55"></line>'
            "</svg>"
        )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
        f'preserveAspectRatio="none" aria-hidden="true">'
        f'<polygon points="{area}" fill="{fill}" opacity="0.10"></polygon>'
        f'<polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"></polyline>'
        "</svg>"
    )


def change_class(value: float) -> str:
    if value > 0.05:
        return "up"
    if value < -0.05:
        return "down"
    return "flat"


def hero(
    eyebrow: str,
    title: str,
    subtitle: str,
    chips: list[tuple[str, str]] | None = None,
) -> None:
    chip_html = "".join(
        f'<span class="cr-chip"><span class="cr-dot {tone}"></span>{_e(text)}</span>'
        for text, tone in (chips or [])
    )
    st.markdown(
        f"""
        <div class="cr-hero">
            <div class="cr-eyebrow"><span class="cr-dot"></span>{_e(eyebrow)}</div>
            <h1>{_e(title)}</h1>
            <p>{_e(subtitle)}</p>
            <div class="cr-meta">{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def ticker(items: list[dict]) -> None:
    """A compact strip of live quotes: name, price and day change."""
    if not items:
        return
    cards = []
    for item in items:
        change = float(item.get("change_pct", 0.0))
        arrow = "▲" if change > 0.05 else "▼" if change < -0.05 else "•"
        cards.append(
            f'<div class="cr-tick">'
            f'<div class="t-name">{_e(item["name"])}</div>'
            f'<div class="t-price">₹{float(item["price"]):,.0f}</div>'
            f'<div class="t-chg {change_class(change)}">{arrow} {change:+.2f}%</div>'
            f"</div>"
        )
    st.markdown(f'<div class="cr-ticker">{"".join(cards)}</div>', unsafe_allow_html=True)


def section(title: str, subtitle: str = "") -> None:
    note = f"<p>{_e(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f'<div class="cr-section"><h3>{_e(title)}</h3>{note}</div>',
        unsafe_allow_html=True,
    )


def commodity_grid(rows: list[dict]) -> None:
    """Cards with price, day change, weekly sparkline and variety count."""
    if not rows:
        st.info("No commodity reported by this mandi yet.", icon=":material/info:")
        return
    cards = []
    for row in rows:
        change = float(row["change_pct"])
        up = change >= 0
        spark = spark_svg(row.get("spark", []), up=up)
        arrow = "▲" if change > 0.05 else "▼" if change < -0.05 else "•"
        cards.append(
            f'<div class="cr-card">'
            f'<div class="c-top"><div><div class="c-name">{_e(row["name"])}</div>'
            f'<div class="c-local">{_e(row["local_name"])} · {_e(row["category"])}</div></div>'
            f'<span class="c-tag">{_e(row.get("tag", "live"))}</span></div>'
            f'<div class="c-price">₹{float(row["price"]):,.0f} <span class="c-unit">/ quintal</span></div>'
            f'<div class="c-change {change_class(change)}">{arrow} {change:+.2f}% today</div>'
            f'<div class="c-spark">{spark}</div>'
            f'<div class="c-foot"><span>7d ₹{float(row["low_week"]):,.0f}–₹{float(row["high_week"]):,.0f}</span>'
            f'<span>{int(row["varieties"])} {"variety" if int(row["varieties"]) == 1 else "varieties"}</span></div>'
            f"</div>"
        )
    st.markdown(f'<div class="cr-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def stat_cards(items: list[tuple[str, str, str]]) -> None:
    cards = "".join(
        f'<div class="cr-stat"><div class="s-label">{_e(label)}</div>'
        f'<div class="s-value">{_e(value)}</div><div class="s-note">{_e(note)}</div></div>'
        for label, value, note in items
    )
    st.markdown(
        f'<div class="cr-grid" style="margin-bottom:.4rem">{cards}</div>',
        unsafe_allow_html=True,
    )


def note(text: str) -> None:
    st.markdown(f'<div class="cr-note">{text}</div>', unsafe_allow_html=True)


def live_chip(ok: bool, label: str) -> str:
    return label
