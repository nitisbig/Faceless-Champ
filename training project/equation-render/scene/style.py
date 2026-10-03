"""Shared local fonts, palette, and component helpers."""

from pathlib import Path

from faceless_champ import ColorScheme, Equation, Text

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "assets"
FONT = ASSETS / "fonts" / "SpaceGrotesk[wght].ttf"
BODY = ASSETS / "fonts" / "DMSans[opsz,wght].ttf"
SFX = ASSETS / "sfx" / "equation-render"
DEFAULT_SCHEME = ColorScheme.named("midnight")
TRANSPARENT = "#00000000"


def text(words, position, *, size=28, color=None, anchor="center", body=False, scheme=DEFAULT_SCHEME, **kwargs):
    kwargs.setdefault("font_weight", 450 if body else 500)
    return Text(
        words,
        font=BODY if body else FONT,
        font_size=size,
        color=color or scheme.text,
        position=position,
        anchor=anchor,
        **kwargs,
    )


def equation(expression, position, *, size=64, color=None, width=None, scheme=DEFAULT_SCHEME, **kwargs):
    return Equation(
        expression, font_size=size, color=color or scheme.text, max_width=width, position=position, **kwargs
    )
