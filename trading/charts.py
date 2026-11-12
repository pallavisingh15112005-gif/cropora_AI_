"""Cropora Mandi — Altair chart builders for the live feed."""

from __future__ import annotations

import altair as alt
import pandas as pd

GREEN = "#166534"
LIME = "#84CC16"
AMBER = "#D97706"
RED = "#DC2626"
BLUE = "#0284C7"
SLATE = "#94A3B8"
SAND = "#A3B18A"

AXIS = alt.Axis(labelColor="#64748B", titleColor="#475569", gridColor="#E2E8F0")


def price_chart(data: pd.DataFrame, *, height: int = 320):
    """Real reported price line with an intra-day high/low band."""
    base = alt.Chart(data)
    band = base.mark_area(opacity=0.14, color=GREEN).encode(
        x=alt.X("date:T", title=None, axis=AXIS),
        y=alt.Y("low:Q", title="₹ per quintal", scale=alt.Scale(zero=False), axis=AXIS),
        y2="high:Q",
    )
    line = base.mark_line(color=GREEN, strokeWidth=2.4, point=alt.OverlayMarkDef(color=GREEN, size=45)).encode(
        x="date:T",
        y="price:Q",
        tooltip=[
            alt.Tooltip("date:T", title="Reported", format="%d %b %Y"),
            alt.Tooltip("price:Q", title="Modal price", format=","),
            alt.Tooltip("low:Q", title="Low", format=","),
            alt.Tooltip("high:Q", title="High", format=","),
            alt.Tooltip("varieties:Q", title="Varieties", format="d"),
        ],
    )
    return (band + line).properties(height=height)


def variety_chart(data: pd.DataFrame, *, height: int = 320):
    """One line per reported variety, useful when a mandi quotes several grades."""
    return (
        alt.Chart(data)
        .mark_line(strokeWidth=1.8, point=alt.OverlayMarkDef(size=30))
        .encode(
            x=alt.X("date:T", title=None, axis=AXIS),
            y=alt.Y("price:Q", title="₹ per quintal", scale=alt.Scale(zero=False), axis=AXIS),
            color=alt.Color("variety:N", title=None, scale=alt.Scale(scheme="greens")),
            tooltip=[
                alt.Tooltip("date:T", title="Reported", format="%d %b %Y"),
                alt.Tooltip("variety:N", title="Variety"),
                alt.Tooltip("price:Q", title="Price", format=","),
            ],
        )
        .properties(height=height)
    )


def sparkline(values: list[float], *, width: int = 150, height: int = 42, up: bool = True):
    """Tiny trend chart used inside commodity cards."""
    frame = pd.DataFrame({"i": range(len(values)), "v": values})
    color = GREEN if up else RED
    return (
        alt.Chart(frame)
        .mark_area(
            line={"color": color, "strokeWidth": 2},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color=color, offset=0),
                    alt.GradientStop(color="#ffffff", offset=1),
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0,
            ),
            opacity=0.22,
        )
        .encode(
            x=alt.X("i:Q", axis=None),
            y=alt.Y("v:Q", axis=None, scale=alt.Scale(zero=False)),
        )
        .properties(width=width, height=height)
        .configure_view(stroke=None)
    )


def market_compare_chart(data: pd.DataFrame, *, height: int = 300):
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("market_name:N", title=None, sort="-y", axis=alt.Axis(labelAngle=-35, labelColor="#64748B")),
            y=alt.Y("price:Q", title="₹ per quintal", axis=AXIS),
            color=alt.Color("price:Q", legend=None, scale=alt.Scale(scheme="greens")),
            tooltip=[
                alt.Tooltip("market_name:N", title="Mandi"),
                alt.Tooltip("state:N", title="State"),
                alt.Tooltip("price:Q", title="Price", format=","),
                alt.Tooltip("change_pct:Q", title="Day %", format="+.2f"),
                alt.Tooltip("date:T", title="Reported", format="%d %b %Y"),
            ],
        )
        .properties(height=height)
    )


def equity_chart(curve: pd.DataFrame, *, height: int = 300):
    low = float(curve["equity"].min())
    high = float(curve["equity"].max())
    pad = max((high - low) * 0.2, abs(high) * 0.004, 1.0)
    # The area must stop at the bottom of the visible domain, not at zero: the
    # axis starts near the account value, so a zero baseline would draw a fill
    # thousands of pixels tall.
    data = curve.assign(floor=low - pad)
    return (
        alt.Chart(data)
        .mark_area(
            line={"color": GREEN, "strokeWidth": 2},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color=GREEN, offset=0),
                    alt.GradientStop(color="#ffffff", offset=1),
                ],
                x1=1,
                x2=1,
                y1=1,
                y2=0,
            ),
            opacity=0.22,
        )
        .encode(
            x=alt.X("ts:T", title=None, axis=alt.Axis(format="%d %b %H:%M", labelColor="#64748B")),
            y=alt.Y(
                "equity:Q",
                title=None,
                scale=alt.Scale(domain=[low - pad, high + pad], zero=False),
                axis=alt.Axis(
                    labelColor="#64748B",
                    gridColor="#E2E8F0",
                    format="~s",
                    tickCount=4,
                ),
            ),
            y2="floor:Q",
            tooltip=[
                alt.Tooltip("ts:T", title="Time", format="%d %b %Y %H:%M"),
                alt.Tooltip("equity:Q", title="Equity", format=","),
            ],
        )
        .properties(height=height)
    )
