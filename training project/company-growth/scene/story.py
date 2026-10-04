"""An airy, serif-led 45-second company-growth story composed from the library."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from faceless_champ import (
    Arrow,
    Axis,
    Canvas,
    ChartReveal,
    ChartStyle,
    Circle,
    ColorScheme,
    Draw,
    Ellipse,
    FadeIn,
    Line,
    LineChart,
    Number,
    Polyline,
    RankedBarChart,
    Scene,
    Sequence,
    Text,
    linear,
)

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
SERIF = ROOT / "assets" / "fonts" / "CormorantGaramond[wght].ttf"
ITALIC = ROOT / "assets" / "fonts" / "CormorantGaramond-Italic[wght].ttf"
SANS = ROOT / "assets" / "fonts" / "DMSans[opsz,wght].ttf"
SERIF = SERIF if SERIF.is_file() else None
ITALIC = ITALIC if ITALIC.is_file() else SERIF
SANS = SANS if SANS.is_file() else None
SCHEME = replace(
    ColorScheme.named("paper"),
    name="company-ivory",
    background="#FAF7F2",
    surface="#FAF7F2",
    text="#282622",
    muted="#777168",
    axis="#CFC7BC",
    border="#DED6CC",
    grid="#EDE6DD",
    primary="#DF6F38",
    tertiary="#5C755B",
)
CANVAS = Canvas(1920, 1080, SCHEME.background)
CROSSFADE = 0.35
COMPANY_COLORS = {
    "NVIDIA": SCHEME.primary,
    "Microsoft": SCHEME.tertiary,
    "Apple": "#302D28",
    "Alphabet": "#777168",
    "Amazon": "#514B43",
    "Meta": "#6C6257",
    "SpaceX": "#3F3B35",
    "Broadcom": "#857467",
    "Tesla": "#62594E",
    "Micron": "#77816D",
}
CHAPTERS = [
    {"start": 0, "end": 4, "title": "A different scale", "preview": 2.6},
    {"start": 4, "end": 30, "title": "The companies, moving", "preview": 17.9},
    {"start": 30, "end": 39, "title": "Growth has many shapes", "preview": 37.4},
    {"start": 39, "end": 45, "title": "Where they stand", "preview": 43.5},
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


def chart_style(data, *, font_size=30):
    return ChartStyle(
        scheme=SCHEME,
        colors=tuple(COMPANY_COLORS[c["name"]] for c in data["companies"]),
        font=SERIF,
        font_weight=400 if SERIF else None,
        font_size=font_size,
        title_font=SERIF,
        title_font_weight=400 if SERIF else None,
        title_size=38,
        grid=False,
        legend=False,
        line_width=2.4,
    )


def text(value, x, y, size=32, *, color=None, italic=False, small=False, weight=400, **kwargs):
    font = SANS if small else (ITALIC if italic else SERIF)
    return Text(
        value,
        font=font,
        font_weight=weight if font else None,
        font_size=size,
        color=color or SCHEME.text,
        position=(x, y),
        align="center",
        spacing=8,
        **kwargs,
    )


def number(value, x, y, size, *, width=450, italic=False, color=None, **kwargs):
    font = ITALIC if italic else SERIF
    return Number(
        value,
        font=font,
        font_weight=400 if font else None,
        font_size=size,
        width=width,
        align="center",
        color=color or SCHEME.text,
        position=(x, y),
        **kwargs,
    )


def appear(scene, *components, at=0, duration=0.6):
    with scene.at(at):
        scene.play(*(FadeIn(c) for c in components), run_time=duration)


def header(scene, chapter, title, subtitle):
    appear(scene, text(title, 960, 105, 76), at=0, duration=0.6)
    appear(scene, text(subtitle, 960, 173, 25, color=SCHEME.muted), at=0.15, duration=0.5)
    with scene.at(0):
        scene.add(text(f"{chapter:02d} / 04", 1790, 50, 18, color=SCHEME.muted, small=True))


def footer(scene, detail):
    with scene.at(0):
        scene.add(text(detail, 960, 1007, 19, color=SCHEME.muted, small=True))
        scene.add(text("CompaniesMarketCap · StockAnalysis", 960, 1044, 16, color=SCHEME.muted, small=True))


def intro(data):
    scene = Scene(CANVAS)
    header(scene, 1, "A different scale.", "Ten U.S. public companies · 2010 to October 2026")
    baseline = sum(v for v in values_at(data, 2010).values() if v is not None)
    total = sum(values_at(data, 2026).values())
    coins = [
        Ellipse(width=106, height=25, stroke=SCHEME.text, stroke_width=2.3, position=(390, 332 + i * 20))
        for i in range(3)
    ]
    curve = Polyline(
        [(1435, 380), (1460, 374), (1485, 364), (1510, 351), (1535, 335), (1560, 315), (1585, 289)],
        stroke=SCHEME.primary,
        stroke_width=3,
        line_cap="round",
    )
    with scene.at(0.25):
        scene.play(*(Draw(c) for c in coins), Draw(curve), run_time=0.8)
    appear(
        scene,
        number(baseline / 1000, 390, 484, 104, format_spec=".2f", prefix="$", suffix="T"),
        text("the listed value in 2010", 390, 562, 32),
        at=0.45,
    )
    appear(
        scene,
        number(total / 1000, 1530, 484, 104, format_spec=".1f", prefix="$", suffix="T"),
        text("the listed value today", 1530, 562, 32),
        at=0.55,
    )
    appear(scene, text("growth", 960, 504, 112, color=SCHEME.primary, italic=True), at=0.3)
    arrows = [
        Arrow((810, 484), (618, 416), stroke=SCHEME.muted, stroke_width=2, tip_size=17),
        Arrow((1110, 484), (1310, 416), stroke=SCHEME.muted, stroke_width=2, tip_size=17),
        Arrow((960, 606), (960, 726), stroke=SCHEME.muted, stroke_width=2, tip_size=17),
    ]
    with scene.at(0.75):
        scene.play(*(Draw(a) for a in arrows), run_time=0.7)
    for i in range(10):
        dot = Circle(radius=8, fill=SCHEME.text, stroke=None, position=(825 + i * 30, 797))
        appear(scene, dot, at=0.9 + i * 0.045, duration=0.3)
    appear(scene, text("ten companies", 960, 866, 43), at=1.25)
    footer(scene, "The latest top ten, followed back in time · missing public observations are left unvalued")
    scene.wait_until(4 + CROSSFADE)
    return scene


def race(data):
    scene = Scene(CANVAS)
    header(scene, 2, "The companies, moving.", "Market capitalization · a fixed group of ten · nominal U.S. dollars")
    chart = RankedBarChart(
        values_at(data, 2010),
        width=1230,
        height=690,
        label_width=200,
        value_width=194,
        missing_label="No public data",
        value_formatter=money,
        bar_height=7,
        corner_radius=0,
        show_markers=False,
        x_axis=Axis(formatter=money),
        style=chart_style(data),
        position=(90, 254),
        anchor="top_left",
    )
    with scene.at(0.15):
        scene.play(ChartReveal(chart), run_time=0.7)
    year = number(2010, 1580, 348, 170, italic=True, width=476, format_spec=".0f")
    total = number(
        sum(v for v in values_at(data, 2010).values() if v is not None) / 1000,
        1580,
        648,
        102,
        width=476,
        format_spec=".2f",
        prefix="$",
        suffix="T",
    )
    with scene.at(0):
        scene.add(year, total)
        scene.add(text("public value shown", 1580, 560, 30, color=SCHEME.muted))
        scene.add(Line(length=320, stroke=SCHEME.border, stroke_width=1.5, position=(1580, 473)))
        scene.add(text("2010", 1420, 503, 21, color=SCHEME.muted), text("2026", 1740, 503, 21, color=SCHEME.muted))
    marker = Circle(radius=4, fill=SCHEME.primary, stroke=None, position=(1420, 473))
    with scene.at(0):
        scene.add(marker)
    notes = [
        (0, "A smaller beginning.", "Apple leads this group."),
        (3.575, "Another name joins.", "Facebook's public history begins."),
        (9.475, "Technology scales.", "The same names move in value."),
        (15.375, "Into the trillions.", "Several companies cross $1T."),
        (18.325, "A year of retreat.", "2022 brings broad declines."),
        (19.8, "A broad recovery.", "Values recover from their lows."),
        (22.75, "A new leader.", "NVIDIA rises to the top."),
        (24.225, "The latest view.", "SpaceX enters the public data."),
    ]
    for i, (start, title, body) in enumerate(notes):
        end = notes[i + 1][0] if i + 1 < len(notes) else 26 + CROSSFADE
        title_c = text(title, 1580, 802, 43)
        body_c = text(body, 1580, 866, 28, color=SCHEME.muted)
        appear(scene, title_c, body_c, at=start, duration=0.3)
        with scene.at(end):
            scene.remove(title_c, body_c)
    for target_year in range(2011, 2027):
        start = 1 + (target_year - 2011) * 1.475
        target, previous = values_at(data, target_year), values_at(data, target_year - 1)
        continuing = sum(v for name, v in target.items() if v is not None and previous[name] is not None) / 1000
        final = sum(v for v in target.values() if v is not None) / 1000
        with scene.at(start):
            scene.play(
                chart.animate.data_to(target),
                total.animate.value_to(continuing),
                marker.animate.move_to(1420 + (target_year - 2010) / 16 * 320, 473),
                run_time=1.1,
                rate_func=linear,
            )
        with scene.at(start + 1.1):
            scene.play(
                year.animate.value_to(target_year), total.animate.value_to(final), run_time=0.04, rate_func=linear
            )
    year_label = text("year-end observation", 1580, 421, 26, color=SCHEME.muted, italic=True)
    with scene.at(0):
        scene.add(year_label)
    with scene.at(24.225):
        scene.remove(year_label)
        scene.add(text("October snapshot", 1580, 421, 26, color=SCHEME.muted, italic=True))
    footer(scene, "Ranks within the latest cohort · transitions interpolate annual observations · bar scale adjusts")
    scene.wait_until(26 + CROSSFADE)
    return scene


def perspective(data):
    scene = Scene(CANVAS)
    header(scene, 3, "Growth has many shapes.", "Value in dollars, and value relative to a 2010 beginning")
    selected = [data["companies"][i] for i in (0, 1, 2, 3)]
    series = {
        c["name"]: [(2010 + i, c["market_cap_billions"][str(2010 + i)] / 1000) for i in range(17)] for c in selected
    }
    style = replace(chart_style(data), colors=tuple(COMPANY_COLORS[c["name"]] for c in selected))
    lines = LineChart(
        series,
        width=1270,
        height=630,
        end_labels=True,
        x_axis=Axis(limits=(2010, 2026), ticks=(2010, 2018, 2026), formatter=lambda v: f"{v:.0f}"),
        y_axis=Axis(limits=(0, 6), ticks=(0, 3, 6), formatter=lambda v: f"${v:.0f}T"),
        style=style,
        position=(86, 268),
        anchor="top_left",
    )
    with scene.at(0.2):
        scene.play(ChartReveal(lines), run_time=2.1)
    appear(scene, text("four largest today", 725, 236, 29, color=SCHEME.muted, italic=True), at=0.4)
    appear(scene, text("from their 2010 baseline", 1590, 260, 29, color=SCHEME.muted, italic=True), at=0.4)
    eligible = [c for c in data["companies"] if "2010" in c["market_cap_billions"]]
    eligible.sort(key=lambda c: c["market_cap_billions"]["2026"] / c["market_cap_billions"]["2010"], reverse=True)
    for i, c in enumerate(eligible[:3]):
        y = 380 + i * 206
        multiple = number(
            1, 1590, y, 96, italic=True, suffix="×", width=460, color=SCHEME.primary if i == 0 else SCHEME.text
        )
        with scene.at(0.5 + i * 0.25):
            scene.play(
                multiple.animate.value_to(c["market_cap_billions"]["2026"] / c["market_cap_billions"]["2010"]),
                run_time=1.8,
            )
        appear(scene, text(c["name"], 1590, y + 76, 37), at=0.55 + i * 0.25)
    appear(
        scene, text("eight comparable histories;\nthe three largest multiples", 1590, 925, 25, color=SCHEME.muted), at=1
    )
    footer(scene, "2026 = October snapshot; earlier points = year-end · market-cap growth is not total return")
    scene.wait_until(9 + CROSSFADE)
    return scene


def latest(data):
    scene = Scene(CANVAS)
    header(scene, 4, "Where they stand.", "October 2026 · the latest ten U.S. public companies")
    chart = RankedBarChart(
        values_at(data, 2026),
        width=1230,
        height=690,
        label_width=200,
        value_width=194,
        value_formatter=money,
        bar_height=7,
        corner_radius=0,
        show_markers=False,
        x_axis=Axis(limits=(0, 6000), ticks=(0, 3000, 6000), formatter=money),
        style=chart_style(data),
        position=(90, 254),
        anchor="top_left",
    )
    with scene.at(0.15):
        scene.play(ChartReveal(chart), run_time=0.9)
    final = values_at(data, 2026)
    total = sum(final.values())
    appear(scene, text("together", 1580, 307, 39, italic=True), at=0.3)
    appear(
        scene,
        number(total / 1000, 1580, 423, 126, width=530, prefix="$", suffix="T", format_spec=".1f"),
        text("in public market value", 1580, 517, 29, color=SCHEME.muted),
        at=0.45,
    )
    arrow = Arrow((1580, 577), (1580, 650), stroke=SCHEME.muted, stroke_width=2, tip_size=15)
    with scene.at(0.75):
        scene.play(Draw(arrow), run_time=0.6)
    share = sum(list(final.values())[:4]) / total * 100
    appear(
        scene,
        number(share, 1580, 732, 100, italic=True, suffix="%", format_spec=".0f", color=SCHEME.primary),
        text("held by four companies", 1580, 815, 32),
        at=0.9,
    )
    for i in range(10):
        dot = Circle(
            radius=6, fill=SCHEME.primary if i < 4 else SCHEME.border, stroke=None, position=(1472 + i * 24, 874)
        )
        appear(scene, dot, at=1.1 + i * 0.035, duration=0.35)
    appear(scene, text("the four largest, within this group", 1580, 929, 24, color=SCHEME.muted), at=1.25)
    footer(scene, "Fixed latest top-ten cohort · market capitalization in nominal USD · observed 04 October 2026")
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
        "design": "Ivory, serif typography, thin line art",
        "reference": "layout.png",
        "chapters": CHAPTERS,
        "metric": "Market capitalization",
        "snapshot": "October 2026",
        "data": "data/market-cap.json",
        "ranking_scope": "Fixed latest top-ten US public company cohort",
        "storyboard_times": [2.6, 5.0, 8.2, 14.1, 20.0, 25.5, 29.3, 33.6, 37.4, 40.5, 43.5, 44.9],
    }
