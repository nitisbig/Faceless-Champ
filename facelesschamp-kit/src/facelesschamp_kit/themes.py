"""Immutable, per-build semantic style tokens."""

from dataclasses import dataclass, replace
from types import MappingProxyType

from .diagnostics import KitError, number


@dataclass(frozen=True)
class Theme:
    name: str = "midnight"
    background: str = "#0B1020"
    surface: str = "#172139"
    foreground: str = "#F3F6FF"
    muted: str = "#A8B5D0"
    accent: str = "#6CE5C1"
    font: str | None = None
    heading_size: float = 76
    body_size: float = 44
    minimum_font_size: float = 24
    spacing: float = 28
    radius: float = 28
    motion_duration: float = 0.6

    def __post_init__(self):
        for name in ("heading_size", "body_size", "minimum_font_size", "motion_duration"):
            number(getattr(self, name), name, positive=True)
        for name in ("spacing", "radius"):
            number(getattr(self, name), name)
        if self.minimum_font_size > min(self.heading_size, self.body_size):
            raise KitError("THEME", "Minimum font size exceeds the heading or body size")


MIDNIGHT = Theme()
LIGHT = replace(
    MIDNIGHT,
    name="light",
    background="#F5F1E8",
    surface="#E7E0D2",
    foreground="#1E2928",
    muted="#52625E",
    accent="#097B67",
)
THEMES = MappingProxyType({"midnight": MIDNIGHT, "light": LIGHT})
