"""Bundled country flag images, looked up by country code without network I/O."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from .components import Image

_ASSETS = Path(__file__).parent / "assets" / "flags"


@lru_cache(maxsize=1)
def supported_flags() -> tuple[str, ...]:
    """Return the available lowercase flag codes, sorted alphabetically."""
    return tuple(sorted(path.stem for path in _ASSETS.glob("*.png") if path.is_file()))


def flag_path(country_code: str) -> Path:
    """Return a bundled PNG path for a case-insensitive code such as NP or gb-eng."""
    if not isinstance(country_code, str):
        raise TypeError("country_code must be a string")
    code = country_code.strip().casefold()
    if code not in supported_flags():
        raise ValueError(f"Unknown flag code {country_code!r}; use supported_flags() for available codes")
    return _ASSETS / f"{code}.png"


class Flag(Image):
    """Country flag in its original colors, fitted into a 120 x 80 box by default.

    Accepts bundled country codes such as ``np``, ``US``, and ``gb-eng``. All Image
    fitting options, component transforms, and ordinary animations apply.
    """

    def __init__(self, country_code: str, *, width: float = 120, height: float = 80, **kwargs: Any) -> None:
        path = flag_path(country_code)
        super().__init__(path, width=width, height=height, **kwargs)
        self.country_code = path.stem
