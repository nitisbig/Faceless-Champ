"""Design tokens for "Why the Bell Curve Is Everywhere" (scheme ``bell-noir``).

Blue data, gold law: balls, dots and bars are always ``ball``; every bell curve is ``bell``.
Red (``tail``) appears only once the bell fails. See scene-plan.md §1.2.
"""

from dataclasses import replace

from faceless_champ import Theme
from faceless_champ.colors import ColorScheme

TOKENS = {
    "bg": "#000000",
    "ball": "#5FB6FF",
    "bell": "#FFD17E",
    "sigma": "#B58CFF",
    "left": "#36D6B0",
    "right": "#FFA24C",
    "e": "#A6E35A",
    "pi": "#FF6FA8",
    "tail": "#FF4D4D",
    "ink": "#F5F7FA",
    "muted": "#7C8597",
    "grid": "#1A2130",
    "line": "#2A3140",
    "light": "#FFE9C7",
}

SCHEME = ColorScheme(
    name="bell-noir",
    background=TOKENS["bg"],
    surface="#05070A",
    text=TOKENS["ink"],
    muted=TOKENS["muted"],
    axis="#3A4252",
    border=TOKENS["line"],
    grid=TOKENS["grid"],
    primary=TOKENS["ball"],
    secondary=TOKENS["bell"],
    tertiary=TOKENS["sigma"],
    highlight=TOKENS["tail"],
)

THEME = replace(Theme.named("midnight"), name="bell-noir", colors=SCHEME)

W, H = 1920, 1080
