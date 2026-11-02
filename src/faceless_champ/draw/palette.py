"""Color tokens for frame functions, built from a Theme.

A Palette maps token names to hex colors. ``Palette.from_theme(theme)`` exposes every
ColorScheme role (``background``, ``text``, ``primary`` ...), the short aliases ``bg``, ``ink``
and ``line``, and a few drawing tokens; keyword arguments add or override tokens::

    PALETTE = Palette.from_theme(THEME, ball="#5FB6FF", bell="#FFD17E")
    set_default_palette(PALETTE)          # used by Frame(size) and the module-level helpers

Anything that takes a color accepts a token name or a ``#rrggbb`` / ``#rrggbbaa`` hex.
"""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache

ALIASES = {"bg": "background", "ink": "text", "line": "border"}


@lru_cache(maxsize=1024)
def _rgb(value: str) -> tuple[float, float, float]:
    digits = value.lstrip("#")
    if len(digits) not in (6, 8):
        raise ValueError(f"{value!r} is not a #rrggbb color")
    return tuple(int(digits[i : i + 2], 16) / 255 for i in (0, 2, 4))


class Palette:
    """Immutable token -> hex mapping. Hashable, so it can key caches."""

    __slots__ = ("_key", "_tokens")

    def __init__(self, tokens: dict[str, str]):
        clean = {}
        for name, value in tokens.items():
            if not isinstance(value, str) or not value.startswith("#"):
                raise ValueError(f"token {name!r} needs a #rrggbb hex, got {value!r}")
            _rgb(value)
            clean[name] = value
        self._tokens = clean
        self._key = tuple(sorted(clean.items()))

    @classmethod
    def from_theme(cls, theme=None, **tokens: str) -> Palette:
        """Tokens from ``theme`` (default: the active theme), then ``tokens`` on top.

        Drawing tokens and their defaults: ``light`` (glints and sweeps, = text), ``glass`` and
        ``glass_deep`` (glass card gradient, = surface and background), ``floor`` (3D dot floor, = axis).
        """
        if theme is None:
            from ..theme import current_theme

            theme = current_theme()
        scheme = theme.colors
        base = {f.name: getattr(scheme, f.name) for f in fields(scheme) if f.name != "name"}
        for alias, role in ALIASES.items():
            base[alias] = base[role]
        base.update(light=scheme.text, glass=scheme.surface, glass_deep=scheme.background, floor=scheme.axis)
        base.update(tokens)
        return cls(base)

    def with_tokens(self, **tokens: str) -> Palette:
        return Palette({**self._tokens, **tokens})

    @property
    def tokens(self) -> dict[str, str]:
        return dict(self._tokens)

    def __contains__(self, name) -> bool:
        return name in self._tokens

    def __eq__(self, other) -> bool:
        return isinstance(other, Palette) and other._key == self._key

    def __hash__(self) -> int:
        return hash(self._key)

    def __repr__(self) -> str:
        return f"Palette({len(self._tokens)} tokens)"

    def hex(self, value: str) -> str:
        """Resolve a token name or pass a hex through."""
        if value.startswith("#"):
            return value
        try:
            return self._tokens[value]
        except KeyError:
            raise KeyError(f"unknown color token {value!r}; known: {', '.join(sorted(self._tokens))}") from None

    def rgb(self, value: str) -> tuple[float, float, float]:
        return _rgb(self.hex(value))

    def mix(self, a: str, b: str, u: float) -> str:
        """Hex color ``u`` of the way from ``a`` to ``b`` (clamped)."""
        ra, rb = self.rgb(a), self.rgb(b)
        u = max(0.0, min(1.0, u))
        return "#" + "".join(f"{round((x + (y - x) * u) * 255):02x}" for x, y in zip(ra, rb))


_DEFAULT: Palette | None = None


def set_default_palette(palette: Palette | None) -> None:
    """Process-wide palette for ``Frame(size)`` and ``col``/``mix``; None returns to the active theme.

    Set it where the project's tokens are defined (its theme module), so render workers that
    import the scene get it too.
    """
    global _DEFAULT
    if palette is not None and not isinstance(palette, Palette):
        raise TypeError("set_default_palette needs a Palette or None")
    _DEFAULT = palette


def default_palette() -> Palette:
    return _DEFAULT if _DEFAULT is not None else Palette.from_theme()
