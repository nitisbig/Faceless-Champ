"""Immutable, per-build semantic style tokens."""

from dataclasses import dataclass, replace
from types import MappingProxyType

from faceless_champ import CLEAN_FLOW_FONT, ShadowStyle
from PIL import ImageColor

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
    font_weight: float | None = None
    heading_weight: float | None = None
    shadow: ShadowStyle | None = None
    background_pattern: str | None = None
    grid_color: str = "#B7B3AE55"
    grid_spacing: float = 28
    grid_radius: float = 1
    default_enter: str | None = None
    default_exit: str | None = None
    motion_distance: float = 24
    motion_stagger: float = 0.06
    text_engine: str = "pillow"
    surface_mode: str = "raster"
    code_theme: str = "midnight"

    def __post_init__(self):
        if self.text_engine not in {"pillow", "skia"} or self.surface_mode not in {"raster", "vector"}:
            raise KitError("THEME", "text_engine must be pillow/skia and surface_mode raster/vector")
        for name in ("heading_size", "body_size", "minimum_font_size", "motion_duration"):
            number(getattr(self, name), name, positive=True)
        for name in ("spacing", "radius"):
            number(getattr(self, name), name)
        number(self.grid_spacing, "grid_spacing", minimum=1)
        number(self.grid_radius, "grid_radius", positive=True)
        for name in ("motion_distance", "motion_stagger"):
            number(getattr(self, name), name)
        for name in ("font_weight", "heading_weight"):
            if getattr(self, name) is not None:
                number(getattr(self, name), name, positive=True)
        if self.shadow is not None and not isinstance(self.shadow, ShadowStyle):
            raise KitError("THEME", "shadow must be a ShadowStyle")
        if self.background_pattern not in {None, "dots"}:
            raise KitError("THEME", "background_pattern must be dots or None")
        if self.default_enter not in {None, "flow", "fade", "pop", "stagger"}:
            raise KitError("THEME", "Unknown default entrance")
        if self.default_exit not in {None, "flow", "fade"}:
            raise KitError("THEME", "Unknown default outro")
        try:
            for name in ("background", "surface", "foreground", "muted", "accent", "grid_color"):
                ImageColor.getcolor(getattr(self, name), "RGBA")
        except (TypeError, ValueError) as exc:
            raise KitError("THEME", "Invalid theme color") from exc
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
WHITEBOARD = replace(
    LIGHT,
    name="whiteboard",
    background="#FFFFFF",
    surface="#FFFFFF",
    foreground="#1E293B",
    muted="#64748B",
    accent="#2563EB",
    radius=0,
)
CLEAN_FLOW = replace(
    LIGHT,
    name="clean-flow",
    background="#E8E6E2",
    surface="#FFFFFF",
    foreground="#111111",
    muted="#737373",
    accent="#FF5A20",
    font=CLEAN_FLOW_FONT,
    font_weight=400,
    heading_weight=700,
    radius=44,
    shadow=ShadowStyle(),
    background_pattern="dots",
    default_enter="flow",
    default_exit="flow",
    code_theme="clean-flow",
)
THEMES = MappingProxyType({"midnight": MIDNIGHT, "light": LIGHT, "whiteboard": WHITEBOARD, "clean-flow": CLEAN_FLOW})
