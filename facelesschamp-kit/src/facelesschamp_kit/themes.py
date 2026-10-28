"""Immutable, per-build semantic style tokens."""

from dataclasses import dataclass, replace
from functools import lru_cache
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
    text_budgets: bool = True
    heading_font: str | None = None

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

    # -- core bridge ---------------------------------------------------------

    def core(self):
        """The equivalent faceless_champ Theme (colors, type roles, radius, motion).

        Kit activates it while blocks compose, so core primitives and role
        text inside blocks match the kit theme.
        """
        return _to_core(self)

    @classmethod
    def from_core(cls, core, **overrides):
        """A kit Theme from a faceless_champ Theme or preset name ("neon", ...)."""
        from faceless_champ.colors import relative_luminance
        from faceless_champ.theme import Theme as CoreTheme

        core = CoreTheme.named(core) if isinstance(core, str) else core
        title, body = core.type_scale.title, core.type_scale.body
        enter = {"rise": "flow", "fade": "fade", "pop": "pop", "zoom": "pop"}.get(core.motion.enter, "flow")
        values = {
            "name": core.name,
            "background": core.colors.background,
            "surface": core.colors.surface,
            "foreground": core.colors.text,
            "muted": core.colors.muted,
            "accent": core.colors.primary,
            "font": body.font,
            "heading_font": title.font if title.font != body.font else None,
            "heading_size": title.font_size,
            "body_size": body.font_size,
            "minimum_font_size": min(28, body.font_size),
            "font_weight": body.font_weight,
            "heading_weight": title.font_weight,
            "radius": core.radius,
            "shadow": core.shadow,
            "default_enter": enter,
            "default_exit": "fade" if enter == "fade" else "flow",
            "motion_duration": core.motion.duration,
            "motion_distance": core.motion.distance,
            "motion_stagger": core.motion.stagger,
            "grid_color": core.colors.grid,
            "code_theme": "paper" if relative_luminance(core.colors.background) > 0.5 else "midnight",
        }
        values.update(overrides)
        return cls(**values)


@lru_cache(maxsize=32)
def _to_core(theme):
    from faceless_champ import COLOR_SCHEMES, ColorScheme
    from faceless_champ.theme import THEMES as CORE_THEMES
    from faceless_champ.theme import MotionStyle
    from faceless_champ.theme import Theme as CoreTheme
    from faceless_champ.typography import TYPE_SCALE

    base = CORE_THEMES.get(theme.name, CORE_THEMES["midnight"])
    scheme = COLOR_SCHEMES.get(theme.name, base.colors)
    colors = ColorScheme(
        name=theme.name,
        background=theme.background,
        surface=theme.surface,
        text=theme.foreground,
        muted=theme.muted,
        axis=scheme.axis,
        border=scheme.border,
        grid=theme.grid_color,
        primary=theme.accent,
        secondary=scheme.secondary,
        tertiary=scheme.tertiary,
        highlight=scheme.highlight,
    )
    roles = {}
    for role in ("display", "title", "heading", "body", "label", "caption"):
        style = TYPE_SCALE.style(role)
        heading = role in {"display", "title", "heading"}
        font = (theme.heading_font or theme.font) if heading else theme.font
        weight = theme.heading_weight if heading else theme.font_weight
        if weight is None and font is None:
            weight = style.font_weight
        size = style.font_size
        if role == "title":
            size = theme.heading_size
        elif role == "body":
            size = theme.body_size
        roles[role] = replace(style, font=font, font_weight=weight, font_size=size)
    enter = {"flow": "rise", "fade": "fade", "pop": "pop", "stagger": "rise"}.get(theme.default_enter, "rise")
    return CoreTheme(
        name=theme.name,
        colors=colors,
        type_scale=replace(TYPE_SCALE, **roles),
        radius=theme.radius,
        shadow=theme.shadow,
        motion=MotionStyle(
            duration=theme.motion_duration,
            enter=enter,
            distance=theme.motion_distance,
            stagger=theme.motion_stagger,
            ease=base.motion.ease,
        ),
    )


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
NEON = Theme.from_core("neon")
DOCUMENTARY = Theme.from_core("documentary")
PAPER = Theme.from_core("paper")
THEMES = MappingProxyType(
    {
        "midnight": MIDNIGHT,
        "light": LIGHT,
        "whiteboard": WHITEBOARD,
        "clean-flow": CLEAN_FLOW,
        "neon": NEON,
        "documentary": DOCUMENTARY,
        "paper": PAPER,
    }
)


def resolve_theme(name):
    """A kit theme by name: built-in kit themes, then core/plugin themes via Theme.from_core."""
    if name in THEMES:
        return THEMES[name]
    from faceless_champ.theme import Theme as CoreTheme

    try:
        return Theme.from_core(CoreTheme.named(name))
    except ValueError as exc:
        raise KitError("THEME", str(exc).replace("choose ", f"choose {', '.join(THEMES)}, ")) from None
