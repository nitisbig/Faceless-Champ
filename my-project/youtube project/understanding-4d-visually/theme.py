"""Design tokens for "Understanding 4D Visually".

One color per direction, never reused for anything else:
x = red, y = orange, z = yellow, and blue for "the extra direction" (time first, then w).
"""

from dataclasses import replace

from faceless_champ import Theme
from faceless_champ.colors import ColorScheme

TOKENS = {
    "bg": "#000000",
    "x": "#FF5A4E",
    "y": "#FF9F3D",
    "z": "#FFD17E",
    "w": "#5FB6FF",
    "ink": "#F5F7FA",
    "muted": "#7C8597",
    "grid": "#1C2433",
    "line": "#2A3140",
    "light": "#FFE9C7",
}

SCHEME = ColorScheme(
    name="tesseract-noir",
    background=TOKENS["bg"],
    surface="#05070A",
    text=TOKENS["ink"],
    muted=TOKENS["muted"],
    axis="#3A4252",
    border=TOKENS["line"],
    grid=TOKENS["grid"],
    primary=TOKENS["w"],
    secondary=TOKENS["y"],
    tertiary=TOKENS["z"],
    highlight=TOKENS["x"],
)

THEME = replace(Theme.named("midnight"), name="tesseract-noir", colors=SCHEME)

W, H = 1920, 1080
