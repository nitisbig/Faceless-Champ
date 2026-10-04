"""A 45-second editorial data story. Rendering and chart behavior live in the library."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from faceless_champ import (
    Axis,
    Canvas,
    ChartReveal,
    ChartStyle,
    Circle,
    ColorScheme,
    FadeIn,
    Line,
    LineChart,
    Number,
    PieChart,
    RankedBarChart,
    Rectangle,
    Scene,
    Sequence,
    SlideIn,
    Text,
    linear,
)

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
FONT = ROOT / "assets" / "fonts" / "DMSans[opsz,wght].ttf"
FONT = FONT if FONT.is_file() else None
SCHEME = replace(
    ColorScheme.named("paper"),
    name="company-light",
    background="#F5F4EF",
    text="#172A38",
    muted="#566772",
    surface="#FFFFFF",
    grid="#E8ECEE",
    border="#DCE3E5",
    primary="#296553",
)
CANVAS = Canvas(1920, 1080, SCHEME.background)
CROSSFADE = 0.35
CHAPTERS = [
    {"start": 0, "end": 4, "title": "Ten giants. Sixteen years.", "preview": 2.6},
    {"start": 4, "end": 30, "title": "The ranking race", "preview": 17.9},
    {"start": 30, "end": 39, "title": "Growth in perspective", "preview": 37.4},
    {"start": 39, "end": 45, "title": "The latest top ten", "preview": 43.5},
]


def load_data():
    data = json.loads((PROJECT / "data" / "market-cap.json").read_text(encoding="utf-8"))
    if len(data["companies"]) != 10:
        raise ValueError("The company-growth story requires ten companies")
    return data


def values_at(data, year):
    return {c["name"]: c["market_cap_billions"].get(str(year)) for c in data["companies"]}


def money(value):
    return f"${value / 1000:.2f}T" if value >= 1000 else f"${value:.1f}B"


def chart_style(data, *, font_size=24, legend=False):
    return ChartStyle(
        scheme=SCHEME,
        colors=tuple(c["color"] for c in data["companies"]),
        font_size=font_size,
        title_size=28,
        legend=legend,
    )


def text(value, x, y, size=28, *, color=None, weight=500, **kwargs):
    return Text(
        value,
        font=FONT,
        font_weight=weight if FONT else None,
        font_size=size,
        color=color or SCHEME.text,
        position=(x, y),
        anchor="top_left",
        **kwargs,
    )


def panel(x, y, width, height, *, fill=None):
    return Rectangle(
        width=width,
        height=height,
        corner_radius=22,
        fill=fill or SCHEME.surface,
        stroke=SCHEME.border,
        stroke_width=1,
        position=(x, y),
        anchor="top_left",
    )


def header(scene, chapter, title, subtitle):
    scene.add(text("FACELESS CHAMP  /  DATA STORIES", 72, 43, 22, color=SCHEME.primary, weight=700))
    scene.add(text(f"{chapter:02d}  /  COMPANY GROWTH", 1440, 43, 22, color=SCHEME.muted))
    scene.add(text(title, 72, 103, 62, weight=700))
    scene.add(text(subtitle, 76, 184, 26, color=SCHEME.muted))


def footer(scene, chapter, *, detail="Nominal USD • market capitalization • fixed latest top-ten cohort"):
    scene.add(Line(length=1776, stroke=SCHEME.border, stroke_width=1, position=(960, 977)))
    scene.add(text(detail, 76, 1000, 21, color=SCHEME.muted))
    scene.add(text("Sources: CompaniesMarketCap / StockAnalysis", 1240, 1000, 20, color=SCHEME.muted))
    for i in range(4):
        scene.add(
            Rectangle(
                width=64,
                height=4,
                fill=SCHEME.primary if i == chapter - 1 else SCHEME.border,
                stroke=None,
                position=(76 + i * 74, 1048),
                anchor="top_left",
            )
        )


def intro(data):
    scene = Scene(CANVAS)
    scene.add(text("FACELESS CHAMP  /  DATA STORIES", 76, 52, 22, color=SCHEME.primary, weight=700))
    scene.add(text("US PUBLIC COMPANIES", 76, 246, 25, color=SCHEME.primary, weight=700))
    headline = text("Ten giants.\nSixteen years.", 70, 300, 116, weight=700, spacing=4)
    scene.play(SlideIn(headline, direction="up", distance=26), run_time=0.65)
    with scene.at(0.25):
        scene.play(FadeIn(text("How today's largest companies grew in value.", 78, 605, 31)), run_time=0.6)
    scene.add(text("2010", 78, 724, 66, weight=600))
    scene.add(Line(length=180, stroke=SCHEME.primary, stroke_width=3, position=(350, 763)))
    scene.add(text("OCT 2026", 480, 737, 43, weight=600))
    scene.add(text("A market-cap story • 45 seconds", 78, 838, 26, color=SCHEME.muted))
    scene.add(panel(1036, 205, 804, 685))
    latest = values_at(data, 2026)
    donut = PieChart(
        latest.keys(),
        latest.values(),
        hole=0.77,
        width=740,
        height=545,
        style=chart_style(data),
        position=(1440, 505),
    )
    with scene.at(0.35):
        scene.play(ChartReveal(donut), run_time=1.1)
    scene.add(text("LATEST TOP-TEN VALUE", 1251, 423, 23, color=SCHEME.muted, weight=600))
    total = Number(
        sum(latest.values()) / 1000,
        format_spec=".1f",
        prefix="$",
        suffix="T",
        font=FONT,
        font_weight=700 if FONT else None,
        font_size=92,
        color=SCHEME.text,
        width=420,
        align="center",
        anchor="top_left",
        position=(1230, 477),
    )
    scene.add(total)
    scene.add(text("October 2026 snapshot", 1268, 596, 26, color=SCHEME.muted))
    scene.add(text("10 companies, shown in consistent colors", 1160, 814, 25, color=SCHEME.muted))
    footer(scene, 1)
    scene.wait_until(4 + CROSSFADE)
    return scene


def race(data):
    scene = Scene(CANVAS)
    header(scene, 2, "How the ranking changed", "Today's ten largest US public companies, traced back to 2010")
    scene.add(panel(72, 246, 1280, 688))
    scene.add(panel(1384, 246, 456, 688))
    chart = RankedBarChart(
        values_at(data, 2010),
        width=1256,
        height=657,
        label_width=180,
        value_width=190,
        missing_label="No public data",
        value_formatter=money,
        x_axis=Axis(formatter=money),
        style=chart_style(data, font_size=23),
        position=(84, 261),
        anchor="top_left",
    )
    scene.play(ChartReveal(chart), run_time=0.45)
    scene.add(text("OBSERVATION", 1414, 283, 22, color=SCHEME.muted, weight=600))
    year = Number(
        2010,
        format_spec=".0f",
        font=FONT,
        font_weight=700 if FONT else None,
        font_size=108,
        color=SCHEME.text,
        width=388,
        align="left",
        position=(1408, 330),
        anchor="top_left",
    )
    scene.add(year)
    scene.add(text("PUBLIC VALUE SHOWN", 1414, 524, 22, color=SCHEME.muted, weight=600))
    total = Number(
        sum(v for v in values_at(data, 2010).values() if v is not None) / 1000,
        format_spec=".2f",
        prefix="$",
        suffix="T",
        font=FONT,
        font_size=70,
        font_weight=600 if FONT else None,
        color=SCHEME.primary,
        width=394,
        anchor="top_left",
        position=(1412, 574),
    )
    scene.add(total)
    scene.add(Line(length=372, stroke=SCHEME.border, stroke_width=2, position=(1612, 470)))
    marker = Circle(radius=6, fill=SCHEME.primary, stroke=None, position=(1426, 470))
    scene.add(marker)
    notes = [
        (0, "A smaller starting line", "Apple leads this group.\nSome public histories\nbegin after 2010."),
        (3.575, "A new public entrant", "Facebook's public series\nbegins in 2012. It later\nbecomes Meta."),
        (9.475, "The scale expands", "The same company colors\nfollow every move\nthrough the ranking."),
        (15.375, "The trillion-dollar era", "Several companies cross\nfrom billions into\ntrillions of dollars."),
        (18.325, "Growth can reverse", "The 2022 observations\nshow a broad decline\nacross these companies."),
        (19.8, "A broad rebound", "Several values recover\nfrom their 2022 lows\nin the following years."),
        (22.75, "A changing leader", "NVIDIA climbs to the top\nof this group as chip\nvaluations expand."),
        (24.225, "The latest snapshot", "SpaceX appears in the\n2026 source. Earlier years\nhave no public data."),
    ]
    for i, (start, title, body) in enumerate(notes):
        end = notes[i + 1][0] if i + 1 < len(notes) else 26 + CROSSFADE
        title_c, body_c = (
            text(title, 1414, 714, 26, weight=700),
            text(body, 1414, 762, 24, color=SCHEME.muted, spacing=8),
        )
        with scene.at(start):
            scene.add(title_c, body_c)
        with scene.at(end):
            scene.remove(title_c, body_c)
    for target_year in range(2011, 2027):
        start = 1.0 + (target_year - 2011) * 1.475
        target = values_at(data, target_year)
        previous = values_at(data, target_year - 1)
        continuing_total = sum(v for name, v in target.items() if v is not None and previous[name] is not None) / 1000
        final_total = sum(v for v in target.values() if v is not None) / 1000
        # Do not imply a monthly observation: all interpolation is labeled below.
        with scene.at(start):
            scene.play(
                chart.animate.data_to(target),
                total.animate.value_to(continuing_total),
                marker.animate.move_to(1426 + (target_year - 2010) / 16 * 372, 470),
                run_time=1.1,
                rate_func=linear,
            )
        # Keep the displayed date on the preceding snapshot until the transition ends.
        with scene.at(start + 1.1):
            scene.play(
                year.animate.value_to(target_year), total.animate.value_to(final_total), run_time=0.04, rate_func=linear
            )
    with scene.at(0):
        year_label = text("YEAR-END • 2010–2025", 1414, 446, 19, color=SCHEME.muted)
        scene.add(year_label)
    with scene.at(24.225):
        scene.remove(year_label)
        scene.add(text("LATEST • OCTOBER 2026", 1414, 446, 19, color=SCHEME.muted))
    with scene.at(0):
        footer(
            scene,
            2,
            detail="Ranks within this fixed cohort • transitions interpolate annual observations • scale adjusts",
        )
    scene.wait_until(26 + CROSSFADE)
    return scene


def perspective(data):
    scene = Scene(CANVAS)
    header(
        scene,
        3,
        "Size and growth tell different stories",
        "Market value in dollars, and multiples of the 2010 baseline",
    )
    scene.add(panel(72, 246, 1180, 688), panel(1284, 246, 556, 688))
    selected = [data["companies"][i] for i in (0, 1, 2, 3)]
    series = {
        c["name"]: [(2010 + i, c["market_cap_billions"][str(2010 + i)] / 1000) for i in range(17)] for c in selected
    }
    lines = LineChart(
        series,
        width=1132,
        height=613,
        title="Four largest today • nominal USD trillions",
        x_axis=Axis(limits=(2010, 2026), ticks=(2010, 2014, 2018, 2022, 2026), formatter=lambda v: f"{v:.0f}"),
        y_axis=Axis(limits=(0, 6), ticks=(0, 1, 2, 3, 4, 5, 6), formatter=lambda v: f"${v:.0f}T"),
        style=ChartStyle(scheme=SCHEME, colors=tuple(c["color"] for c in selected), font_size=23, title_size=25),
        position=(96, 269),
        anchor="top_left",
    )
    scene.play(ChartReveal(lines), run_time=2.1)
    scene.add(text("2026 endpoint = October snapshot; other points = year-end", 148, 882, 22, color=SCHEME.muted))
    scene.add(text("GROWTH MULTIPLES", 1314, 284, 22, color=SCHEME.muted, weight=700))
    eligible = [c for c in data["companies"] if "2010" in c["market_cap_billions"]]
    eligible.sort(key=lambda c: c["market_cap_billions"]["2026"] / c["market_cap_billions"]["2010"], reverse=True)
    for i, c in enumerate(eligible[:3]):
        y = 354 + i * 164
        scene.add(text(c["name"], 1320, y, 29, weight=600))
        multiple = Number(
            0,
            format_spec=".0f",
            suffix="×",
            font=FONT,
            font_weight=700 if FONT else None,
            font_size=73,
            width=410,
            color=c["color"],
            position=(1316, y + 46),
            anchor="top_left",
        )
        with scene.at(0.5 + i * 0.25):
            scene.play(
                multiple.animate.value_to(c["market_cap_billions"]["2026"] / c["market_cap_billions"]["2010"]),
                run_time=1.6,
            )
    scene.add(text("Latest market cap / 2010 market cap", 1320, 859, 23, color=SCHEME.muted))
    scene.add(text("Eight comparable histories; top three shown", 1320, 895, 21, color=SCHEME.muted))
    footer(
        scene, 3, detail="Growth multiples use only companies with 2010 data • market-cap growth is not total return"
    )
    scene.wait_until(9 + CROSSFADE)
    return scene


def latest(data):
    scene = Scene(CANVAS)
    header(scene, 4, "The latest top ten", "United States • public companies • October 2026 snapshot")
    scene.add(panel(72, 246, 1198, 688), panel(1302, 246, 538, 688))
    chart = RankedBarChart(
        values_at(data, 2026),
        width=1168,
        height=647,
        label_width=180,
        value_width=136,
        value_formatter=money,
        x_axis=Axis(limits=(0, 6000), ticks=(0, 2000, 4000, 6000), formatter=money),
        style=chart_style(data, font_size=24),
        position=(88, 267),
        anchor="top_left",
    )
    scene.play(ChartReveal(chart), run_time=0.8)
    final = values_at(data, 2026)
    total = sum(final.values())
    scene.add(text("COMBINED MARKET CAP", 1334, 287, 24, color=SCHEME.muted, weight=700))
    scene.add(
        Number(
            total / 1000,
            format_spec=".1f",
            prefix="$",
            suffix="T",
            font=FONT,
            font_weight=700 if FONT else None,
            font_size=89,
            width=457,
            color=SCHEME.primary,
            anchor="top_left",
            position=(1328, 342),
        )
    )
    share = sum(list(final.values())[:4]) / total * 100
    scene.add(text("FOUR LARGEST / TOP TEN", 1334, 502, 23, color=SCHEME.muted, weight=700))
    scene.add(
        Number(
            share,
            format_spec=".0f",
            suffix="%",
            font=FONT,
            font_weight=700 if FONT else None,
            font_size=82,
            width=436,
            color=SCHEME.text,
            anchor="top_left",
            position=(1330, 551),
        )
    )
    scene.add(Rectangle(width=442, height=15, fill=SCHEME.grid, stroke=None, position=(1338, 663), anchor="top_left"))
    scene.add(
        Rectangle(
            width=442 * share / 100,
            height=15,
            fill=SCHEME.primary,
            stroke=None,
            position=(1338, 663),
            anchor="top_left",
        )
    )
    scene.add(text("Same names.\nA very different scale.", 1332, 730, 37, weight=700, spacing=8))
    scene.add(text("Data observed 04 Oct 2026", 1336, 879, 23, color=SCHEME.muted))
    footer(
        scene,
        4,
        detail="Fixed cohort selected at the latest snapshot • full data and methodology included with this project",
    )
    scene.wait_until(6)
    return scene


def company_growth_video():
    data = load_data()
    return Sequence(intro(data), race(data), perspective(data), latest(data), crossfade=CROSSFADE, canvas=CANVAS)


def timeline(video):
    return {
        "duration": video.duration,
        "canvas": [video.canvas.width, video.canvas.height],
        "background": SCHEME.background,
        "color_scheme": "light",
        "chapters": CHAPTERS,
        "metric": "Market capitalization",
        "snapshot": "October 2026",
        "data": "data/market-cap.json",
        "ranking_scope": "Fixed latest top-ten US public company cohort",
        "storyboard_times": [2.6, 5.0, 8.2, 14.1, 20.0, 25.5, 29.3, 33.6, 37.4, 40.5, 43.5, 44.9],
    }
