"""This project's palette and placements; drawing comes from Faceless Champ."""

import json
from pathlib import Path

from faceless_champ import Canvas, ColorScheme, ImageSlot, Rectangle, Text

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


def text(value, x, y, size=38, *, serif=False, color=INK, weight=400):
    return Text(
        value,
        font=SERIF if serif else SANS,
        font_size=size,
        font_weight=weight,
        color=color,
        align="center",
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


def panel(x, y, width, height, *, accent=False):
    return Rectangle(
        width=width,
        height=height,
        corner_radius=18,
        position=(x, y),
        fill=CREAM,
        stroke=RUST if accent else None,
        stroke_width=2,
    )


def icon(glyph, x, y, size=90):
    return Text(glyph, font=SYMBOLS, font_size=size, color=RUST, position=(x, y))
