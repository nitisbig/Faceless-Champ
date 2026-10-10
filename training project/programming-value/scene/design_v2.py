"""Portable typography and semantic colors for the cinematic version."""

from pathlib import Path

from facelesschamp_kit.themes import Theme

from faceless_champ import Bounds, Canvas

FONTS = Path(__file__).resolve().parents[1] / "assets/fonts"
FONT = str(FONTS / "InterVariable.ttf")
MONO = str(FONTS / "DejaVuSansMono.ttf")
WHITE, MUTED = "#F4F7FB", "#AAB4C3"
AI, SYSTEM, HUMAN, ERROR = "#56B4E9", "#009E73", "#E69F00", "#CC79A7"
SURFACE, LINE = "#10151D", "#445366"
CANVAS = Canvas(1920, 1080, "#000000")
SAFE = Bounds(96, 96, 1824, 984)
THEME = Theme(
    name="cinematic-v2",
    background="#000000",
    surface=SURFACE,
    foreground=WHITE,
    muted=MUTED,
    accent=AI,
    font=FONT,
    heading_size=76,
    body_size=40,
    minimum_font_size=32,
    spacing=32,
    radius=20,
    motion_duration=0.45,
)
PALETTE = {"ai": AI, "system": SYSTEM, "human": HUMAN, "error": ERROR, "foreground": WHITE, "supporting": MUTED}
