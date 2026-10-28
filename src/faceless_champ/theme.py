"""One design-token system: colors, type, spacing, radius, shadow and motion.

Activate a theme and components pick their defaults from it::

    theme = Theme.named("neon")
    with theme.use():
        scene = Scene(theme.canvas())
        title = Text("Orbital mechanics", role="title")      # theme font, size, color
        tag = theme.text("CHAPTER 2", role="label", color="primary")
        scene.reveal(tag, title, stagger=0.12)

Presets: midnight, paper, ocean, clean-flow, neon, documentary, whiteboard.
Without an active theme every component keeps its legacy defaults.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, fields, replace
from types import MappingProxyType

from .colors import COLOR_SCHEMES, ColorScheme
from .components import finite
from .surfaces import ShadowStyle
from .typography import TYPE_PAIRINGS, TypeScale

ROLE_COLORS = MappingProxyType(
    {
        "display": "text",
        "title": "text",
        "heading": "text",
        "body": "text",
        "label": "primary",
        "caption": "muted",
    }
)


@dataclass(frozen=True)
class MotionStyle:
    """Default entrance motion used by Scene.reveal and kit placements."""

    duration: float = 0.6
    enter: str = "rise"
    distance: float = 24
    ease: str = "emphasized"
    stagger: float = 0.08

    def __post_init__(self):
        finite(self.duration, "motion duration", 0.000001)
        finite(self.distance, "motion distance", 0)
        finite(self.stagger, "motion stagger", 0)
        from .easing import easing

        easing(self.ease)
        if self.enter not in {"rise", "fade", "pop", "zoom", "drop", "left", "right", "none"}:
            raise ValueError("MotionStyle.enter must be rise, fade, pop, zoom, drop, left, right or none")


@dataclass(frozen=True)
class Theme:
    """Design tokens for a whole video. Sizes are design pixels at 1080p."""

    name: str = "midnight"
    colors: ColorScheme = field(default_factory=ColorScheme)
    type_scale: TypeScale = field(default_factory=TypeScale)
    spacing: tuple[float, ...] = (4, 8, 16, 24, 32, 48, 64, 96, 128)
    radius: float = 24
    shadow: ShadowStyle | None = None
    margin: float = 64
    motion: MotionStyle = field(default_factory=MotionStyle)

    def __post_init__(self):
        if not isinstance(self.colors, ColorScheme):
            raise TypeError("Theme.colors must be a ColorScheme")
        if not isinstance(self.type_scale, TypeScale):
            raise TypeError("Theme.type_scale must be a TypeScale")
        if not isinstance(self.motion, MotionStyle):
            raise TypeError("Theme.motion must be a MotionStyle")
        if self.shadow is not None and not isinstance(self.shadow, ShadowStyle):
            raise TypeError("Theme.shadow must be a ShadowStyle or None")
        steps = tuple(finite(v, "spacing", 0) for v in self.spacing)
        if not steps or list(steps) != sorted(steps):
            raise ValueError("Theme.spacing must be a nonempty increasing scale")
        object.__setattr__(self, "spacing", steps)
        finite(self.radius, "radius", 0)
        finite(self.margin, "margin", 0)

    # -- lookup -------------------------------------------------------------

    @classmethod
    def named(cls, name: str) -> Theme:
        try:
            return THEMES[name]
        except KeyError:
            raise ValueError(f"Unknown theme {name!r}; choose {', '.join(THEMES)}") from None

    def color(self, role_or_color: str) -> str:
        """A color role ("text", "muted", "primary"...) or a literal color string."""
        names = {f.name for f in fields(ColorScheme)} - {"name"}
        return self.colors.color(role_or_color) if role_or_color in names else role_or_color

    def readable(self, color: str, *, on: str | None = None, large: bool = False) -> str:
        """``color`` if it meets WCAG contrast on ``on`` (default: background), else the text color.

        Large text (>= 40 px) needs 3:1, smaller text 4.5:1. Accents that are
        too weak on the background therefore degrade to plain text.
        """
        from .colors import contrast_ratio, readable_color

        background = self.color(on) if on is not None else self.colors.background
        needed = 3.0 if large else 4.5
        color = self.color(color)
        if contrast_ratio(color, background) >= needed:
            return color
        if contrast_ratio(self.colors.text, background) >= needed:
            return self.colors.text
        return readable_color(background)

    def role_color(self, role: str | None) -> str:
        """The readable color for a text role on the background (label=primary, caption=muted)."""
        role = role or "body"
        return self.readable(
            self.colors.color(ROLE_COLORS.get(role, "text")), large=role in {"display", "title", "heading"}
        )

    def space(self, step: int) -> float:
        """Spacing scale value: space(0)=4 ... space(6)=64."""
        if not isinstance(step, int) or not 0 <= step < len(self.spacing):
            raise ValueError(f"space step must be an integer 0..{len(self.spacing) - 1}")
        return self.spacing[step]

    # -- activation ---------------------------------------------------------

    @contextmanager
    def use(self):
        """Make this the active theme for components created inside the block."""
        token = _ACTIVE.set(self)
        try:
            yield self
        finally:
            _ACTIVE.reset(token)

    # -- factories ----------------------------------------------------------

    def canvas(self, width: int = 1920, height: int = 1080):
        from .components import Canvas

        return Canvas(width, height, self.colors.background)

    def for_canvas(self, canvas) -> Theme:
        """Scale type, spacing, radius and margin to the canvas short side."""
        factor = min(canvas.width, canvas.height) / 1080
        return replace(
            self,
            type_scale=self.type_scale.scaled(factor),
            spacing=tuple(v * factor for v in self.spacing),
            radius=self.radius * factor,
            margin=self.margin * factor,
            motion=replace(self.motion, distance=self.motion.distance * factor),
        )

    def text(self, text: str, role: str = "body", *, color: str | None = None, **kwargs):
        """Text styled by role; ``color`` may be a role name such as "muted"."""
        from .components import Text

        color = self.role_color(role) if color is None else self.color(color)
        return Text(text, role=role, type_scale=self.type_scale, color=color, **kwargs)

    def fit(self, text: str, bounds, role: str = "body", *, color: str | None = None, **kwargs):
        """fit_text styled by role with the theme's type scale and colors."""
        from .typography import fit_text

        color = self.role_color(role) if color is None else self.color(color)
        return fit_text(text, bounds, role=role, type_scale=self.type_scale, color=color, **kwargs)

    def card(self, bounds, *, fill: str | None = None, radius: float | None = None, **kwargs):
        """A surface card using the theme's surface color, radius and shadow."""
        from .surfaces import card_surface

        return card_surface(
            bounds,
            fill=self.color(fill) if fill else self.colors.surface,
            radius=self.radius if radius is None else radius,
            shadow=kwargs.pop("shadow", self.shadow),
            **kwargs,
        )


DEFAULT_THEME = Theme()
_ACTIVE: ContextVar[Theme | None] = ContextVar("faceless_champ_theme", default=None)


def active_theme() -> Theme | None:
    """The theme activated with ``Theme.use()``, or None."""
    return _ACTIVE.get()


def current_theme() -> Theme:
    """The active theme, falling back to the default midnight theme."""
    return _ACTIVE.get() or DEFAULT_THEME


def set_theme(theme: Theme | None) -> None:
    """Activate a theme globally for the current context (None clears it)."""
    if theme is not None and not isinstance(theme, Theme):
        raise TypeError("set_theme needs a Theme or None")
    _ACTIVE.set(theme)


_dark_shadow = ShadowStyle("#00000059", 36, (0, 20))
_light_shadow = ShadowStyle("#1A202C1F", 28, (0, 14))

THEMES = MappingProxyType(
    {
        "midnight": Theme(
            "midnight", COLOR_SCHEMES["midnight"], TYPE_PAIRINGS["modern"], radius=28, shadow=_dark_shadow
        ),
        "paper": Theme("paper", COLOR_SCHEMES["paper"], TYPE_PAIRINGS["editorial"], radius=20, shadow=_light_shadow),
        "ocean": Theme("ocean", COLOR_SCHEMES["ocean"], TYPE_PAIRINGS["modern"], radius=28, shadow=_dark_shadow),
        "clean-flow": Theme(
            "clean-flow",
            COLOR_SCHEMES["clean-flow"],
            TYPE_PAIRINGS["modern"],
            radius=44,
            shadow=ShadowStyle(),
            motion=MotionStyle(ease="standard"),
        ),
        "neon": Theme(
            "neon",
            COLOR_SCHEMES["neon"],
            TYPE_PAIRINGS["tech"],
            radius=18,
            shadow=ShadowStyle("#000000AA", 40, (0, 18)),
            motion=MotionStyle(duration=0.5, ease="snappy", distance=32),
        ),
        "documentary": Theme(
            "documentary",
            COLOR_SCHEMES["documentary"],
            TYPE_PAIRINGS["editorial"],
            radius=12,
            shadow=_dark_shadow,
            motion=MotionStyle(duration=0.9, enter="fade", ease="gentle", stagger=0.15),
        ),
        "whiteboard": Theme(
            "whiteboard",
            COLOR_SCHEMES["whiteboard"],
            TYPE_PAIRINGS["modern"],
            radius=16,
            shadow=None,
            motion=MotionStyle(enter="pop", ease="overshoot"),
        ),
    }
)
