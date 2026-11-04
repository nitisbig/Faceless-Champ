"""Design tokens for "The Math Trick That Turns Any Function Into a Polynomial" (scheme ``aion-taylor``).

Aion YouTube Design System, mapped to the local roles of scene-plan.md §1.2:

    original  ink    the true function, always thin white
    copy      gold   the Taylor polynomial, thick with a glow
    x         blue   the input, probes, x-axis values
    error     violet the gap between copy and original (also i)
    fact      magenta factorials and dropped exponents
    result    lime   a digit or value that matches the truth
    plus/minus orange/teal  alternating signs
    circle    pink   the circle of convergence
    alert     red    Ch7 only, once

At most five hues in one frame. Red appears only when the series breaks.
"""

from dataclasses import replace
from pathlib import Path

from faceless_champ import Theme
from faceless_champ.colors import ColorScheme
from faceless_champ.draw import Palette, set_default_palette

TOKENS = {
    "bg": "#000000",
    "stage_raised": "#05070A",
    "slate": "#16181C",
    "ink": "#F5F7FA",
    "original": "#F5F7FA",
    "copy": "#FFD17E",
    "x": "#5FB6FF",
    "error": "#B58CFF",
    "fact": "#FF3D9A",
    "result": "#A6E35A",
    "plus": "#FF9F3D",
    "minus": "#36D6B0",
    "circle": "#FF6FA8",
    "alert": "#FF5A4E",
    "cyan": "#22D3EE",
    "plane_major": "#1E96D2",
    "plane_minor": "#0F2B3A",
    "grid": "#1A2130",
    "line": "#2A3140",
    "axis": "#3A4252",
    "frame": "#9AA0AA",
    "muted": "#7C8597",
    "light": "#FFE9C7",
}

SCHEME = ColorScheme(
    name="aion-taylor",
    background=TOKENS["bg"],
    surface=TOKENS["stage_raised"],
    text=TOKENS["ink"],
    muted=TOKENS["muted"],
    axis=TOKENS["axis"],
    border=TOKENS["line"],
    grid=TOKENS["grid"],
    primary=TOKENS["x"],
    secondary=TOKENS["copy"],
    tertiary=TOKENS["error"],
    highlight=TOKENS["alert"],
)

THEME = replace(Theme.named("midnight"), name="aion-taylor", colors=SCHEME)

# Every faceless_champ.draw helper resolves these tokens: Frame(size), col("copy"), tc("x", "x"), hud.*.
PALETTE = Palette.from_theme(THEME, **TOKENS, glass="#0E131C", glass_deep="#04060A")
set_default_palette(PALETTE)

W, H = 1920, 1080

# Aion strokes, sizes and spacing (scene-plan.md §1.2), in 1080p pixels.
STROKE = {"hairline": 1.0, "rim": 1.2, "pill": 1.6, "frame": 2.0, "axis": 2.4, "arrow": 2.6, "curve": 4.0}
ALPHA = {"grid": 0.08, "ghost": 0.25, "nonfocal": 0.4, "glow": 0.6}
SIZE = {
    "hero": 120,
    "headline": 72,
    "heading": 48,
    "title_card": 112,
    "chapter": 80,
    "label": 28,
    "readout": 30,
    "caption": 24,
    "eyebrow": 22,
    "tick": 20,
    "math_display": 96,
    "math_inline": 48,
}
SAFE = 96  # safe margin
INSET = 120  # panel inset

# Frame.text family aliases: DM Sans for labels and readouts, Space Grotesk for statements and numbers.
# Title cards use Cormorant Garamond (bundled; chosen in Stage A over Typst New Computer Modern, scene-plan.md §1.3).
SANS, DISPLAY, SERIF, SERIF_ITALIC = "sans", "display", "serif", "italic"
TITLE_WEIGHT = 600

ROOT = Path(__file__).resolve().parent
PV_CACHE = ROOT / "output" / "cache" / "pyvista"
DOMAIN_CACHE = ROOT / "output" / "cache" / "domain"
