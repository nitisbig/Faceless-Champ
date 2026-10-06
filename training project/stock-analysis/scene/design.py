"""This project's palette and placements; drawing comes from Faceless Champ."""

import json
from pathlib import Path

from faceless_champ import Canvas, ColorScheme, Group, ImageSlot, Line, Number, Rectangle, Text

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
CONFIG = json.loads((PROJECT / "project.json").read_text(encoding="utf-8"))
WHITE, RUST, STONE, CREAM, INK = (CONFIG["palette"][key] for key in ("background", "accent", "muted", "surface", "ink"))
CANVAS = Canvas(**CONFIG["canvas"], bg=WHITE)
SERIF = ROOT / "assets/fonts/CormorantGaramond[wght].ttf"
SANS = ROOT / "assets/fonts/DMSans[opsz,wght].ttf"
SYMBOLS = ROOT / "assets/icons/MaterialSymbolsOutlined[FILL,GRAD,opsz,wght].ttf"
SCHEME = ColorScheme(
    name="stock-analysis",
    background=WHITE,
    surface=CREAM,
    text=INK,
    muted=STONE,
    axis=STONE,
    border=STONE,
    grid=CREAM,
    primary=RUST,
    secondary=STONE,
    tertiary=INK,
    highlight=RUST,
)


def text(value, x, y, size=38, *, serif=False, color=INK, weight=400, align="center"):
    return Text(
        value,
        font=SERIF if serif else SANS,
        font_size=size,
        font_weight=weight,
        color=color,
        align=align,
        position=(x, y),
    )


def artwork(number, x, y, width, height, mode):
    return ImageSlot(
        PROJECT / "image" / f"{number}.png",
        mode=mode,
        position=(x, y),
        width=width,
        height=height,
        fit="cover",
        placeholder_fill=CREAM,
        placeholder_stroke=STONE,
        placeholder_color=INK,
        placeholder_font=SANS,
        placeholder_font_size=38,
    )


def panel(x, y, width, height, *, accent=False, dark=False):
    return Group(
        Rectangle(width=width, height=height, corner_radius=26, position=(x, y + 7), fill="#2927240C", stroke=None),
        Rectangle(
            width=width,
            height=height,
            corner_radius=24,
            position=(x, y),
            fill=INK if dark else CREAM,
            stroke=RUST if accent else "#E5E2D9",
            stroke_width=2,
        ),
    )


def icon(glyph, x, y, size=90, *, color=RUST):
    if glyph == "\ue322":
        side = size * 0.55
        shapes = [
            Rectangle(
                width=side,
                height=side,
                corner_radius=size * 0.06,
                position=(x, y),
                stroke=color,
                stroke_width=max(2, size * 0.04),
                fill=None,
            ),
            Rectangle(
                width=side * 0.55,
                height=side * 0.55,
                position=(x, y),
                stroke=color,
                stroke_width=max(1.5, size * 0.025),
                fill=None,
            ),
        ]
        for offset in (-0.16, 0, 0.16):
            for sign in (-1, 1):
                shapes.extend(
                    [
                        Line(
                            size * 0.16,
                            position=(x + sign * size * 0.355, y + offset * size),
                            stroke=color,
                            stroke_width=max(2, size * 0.035),
                        ),
                        Line(
                            size * 0.16,
                            rotation=90,
                            position=(x + offset * size, y + sign * size * 0.355),
                            stroke=color,
                            stroke_width=max(2, size * 0.035),
                        ),
                    ]
                )
        return Group(*shapes)
    return Text(glyph, font=SYMBOLS, font_size=size, color=color, position=(x, y))


def number(value, x, y, size=80, *, prefix="", suffix="", decimals=1, color=RUST, width=420):
    return Number(
        value,
        font=SANS,
        font_size=size,
        font_weight=650,
        color=color,
        position=(x, y),
        align="center",
        width=width,
        prefix=prefix,
        suffix=suffix,
        format_spec=f",.{decimals}f",
    )


def pill(value, x, y, width=280, *, dark=False):
    return Group(
        Rectangle(
            width=width, height=58, corner_radius=29, position=(x, y), fill=INK if dark else "#EBE6DB", stroke=None
        ),
        text(value, x, y, 24, color=WHITE if dark else INK, weight=600),
    )
