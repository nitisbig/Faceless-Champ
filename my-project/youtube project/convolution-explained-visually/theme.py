"""Design tokens for "Convolution Explained Visually".

Semantic colors never change meaning across the video:
signal = cyan, kernel = amber, overlap/multiply = magenta, output = lime.
"""

from dataclasses import replace

from faceless_champ import Theme
from faceless_champ.colors import ColorScheme

TOKENS = {
    "bg": "#000000",
    "signal": "#22D3EE",
    "kernel": "#FFB020",
    "overlap": "#FF3D9A",
    "output": "#C6FF4A",
    "ink": "#F5F7FA",
    "muted": "#7C8597",
    "grid": "#1A1F2B",
    "line": "#2A3140",
    "card": "#05070A",
    "alert": "#FF4D4D",
    "stone": "#8FA3C7",
}

SCHEME = ColorScheme(
    name="conv-noir",
    background=TOKENS["bg"],
    surface=TOKENS["card"],
    text=TOKENS["ink"],
    muted=TOKENS["muted"],
    axis="#3A4252",
    border=TOKENS["line"],
    grid=TOKENS["grid"],
    primary=TOKENS["signal"],
    secondary=TOKENS["kernel"],
    tertiary=TOKENS["output"],
    highlight=TOKENS["overlap"],
)

THEME = replace(Theme.named("midnight"), name="conv-noir", colors=SCHEME)

W, H = 1920, 1080
