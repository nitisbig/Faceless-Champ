"""Reusable full-screen editor and fluid terminal window design.

Windows compose existing components. They neither execute source code nor own a
lesson timeline; callers schedule the returned animations with explicit times.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from PIL import ImageColor

from .animation import Animation
from .coding import CodeTheme
from .components import Circle, Component, Rectangle, Text, finite
from .layout import Bounds, Group
from .surfaces import ShadowStyle, card_surface
from .typography import CLEAN_FLOW_FONT

# Reserve the controls, the 144-unit title offset, and title/right-edge space.
_MIN_CHROME_WIDTH = 192


def _positive(value, name):
    value = finite(value, name)
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _theme(value):
    value = CodeTheme.named(value) if isinstance(value, str) else value
    if not isinstance(value, CodeTheme):
        raise TypeError("theme must be a named theme or CodeTheme")
    return value


class CodeWindow(Group):
    """Dark macOS-style chrome around fixed-size, pre-positioned components.

    ``bounds`` describes the window face; ordinary ``Group.bounds`` also includes
    the symmetric shadow allocation. Faces need at least ``192 * unit`` width;
    titles shrink uniformly to fit the header. Content must lie inside the face.
    Construct the complete window before adding it or its children to a scene.
    """

    def __init__(self, bounds, *, title="", theme="clean-flow", fullscreen=False, unit=1, children=()):
        if not isinstance(bounds, Bounds):
            raise TypeError("CodeWindow bounds must be Bounds")
        unit = _positive(unit, "unit")
        if bounds.width < 1 or bounds.height < 1:
            raise ValueError("CodeWindow bounds need at least one design pixel per side")
        theme = _theme(theme)
        fullscreen = bool(fullscreen)
        header_height = (80 if fullscreen else 64) * unit
        if bounds.height <= header_height:
            raise ValueError("CodeWindow height must leave content space below its header")
        if bounds.width < _MIN_CHROME_WIDTH * unit - 1e-9:
            raise ValueError("CodeWindow width must be at least 192 * unit to fit its chrome")
        children = tuple(children)
        for child in children:
            if not isinstance(child, Component):
                raise TypeError("CodeWindow children must be Components")
            box = child.bounds
            # Fixed viewports have integer raster dimensions, so tolerate only
            # the half-pixel rounding of their authored fractional geometry.
            if (
                box.left < bounds.left - 0.5
                or box.top < bounds.top - 0.5
                or box.right > bounds.right + 0.5
                or box.bottom > bounds.bottom + 0.5
            ):
                raise ValueError("CodeWindow content must fit inside its face bounds")

        self.bounds_box = bounds
        self.theme = theme
        self.unit = unit
        self.fullscreen = fullscreen
        shadow_style = ShadowStyle(color="#00000028", blur=16 * unit, offset=(0, 10 * unit))
        shadow_pad = math.ceil(3 * shadow_style.blur + max(abs(value) for value in shadow_style.offset))
        allocation = Bounds(
            bounds.left - shadow_pad,
            bounds.top - shadow_pad,
            bounds.right + shadow_pad,
            bounds.bottom + shadow_pad,
        )
        self.shadow = card_surface(allocation, fill="#00000000", radius=26 * unit, shadow=shadow_style)
        self.shadow.anchor = "top_left"
        self.shadow.position = (allocation.left, allocation.top)
        radius = 0 if fullscreen else 22 * unit
        self.face = Rectangle(
            width=bounds.width,
            height=bounds.height,
            corner_radius=radius,
            fill=theme.background,
            stroke=None,
            stroke_width=0,
            position=(bounds.left, bounds.top),
            anchor="top_left",
        )
        self.header = Rectangle(
            width=bounds.width,
            height=header_height,
            corner_radius=radius,
            fill=theme.chrome,
            stroke=None,
            position=(bounds.left, bounds.top),
            anchor="top_left",
        )
        header_bottom = Rectangle(
            width=bounds.width,
            height=header_height / 2,
            fill=theme.chrome,
            stroke=None,
            position=(bounds.left, bounds.top + header_height / 2),
            anchor="top_left",
        )
        divider = Rectangle(
            width=bounds.width,
            height=max(1, unit),
            fill="#FFFFFF18",
            stroke=None,
            position=(bounds.left, bounds.top + header_height),
            anchor="top_left",
        )
        controls = tuple(
            Circle(
                radius=(9 if fullscreen else 7.5) * unit,
                fill=color,
                stroke=None,
                position=(bounds.left + (36 + index * 28) * unit, bounds.top + header_height / 2),
            )
            for index, color in enumerate(("#FF6058", "#FEBC2E", "#28C840"))
        )
        title_top = (22 if fullscreen else 16) * unit
        self.heading = Text(
            str(title),
            font=CLEAN_FLOW_FONT,
            font_weight=500,
            font_size=(30 if fullscreen else 26) * unit,
            color=theme.muted,
            position=(bounds.left + 144 * unit, bounds.top + title_top),
            anchor="top_left",
        )
        # Measure the complete raster allocation, including multiline height and
        # text padding, before fixing the group's origin or accepting the title.
        title_box = self.heading.bounds
        title_scale = min(
            1,
            (bounds.right - 24 * unit - title_box.left) / title_box.width,
            (header_height - 2 * title_top) / title_box.height,
        )
        if title_scale < 0.001:
            raise ValueError("CodeWindow title cannot fit its header; shorten it or allocate more width")
        self.heading.scale = title_scale
        super().__init__(
            self.shadow, self.face, self.header, header_bottom, divider, *controls, self.heading, *children
        )
        # Raster rounding and title/content extents must never move the pivot.
        self._origin = bounds.center
        self.position = bounds.center


@dataclass(frozen=True)
class CodeWorkspaceDesign:
    """The approved clean-flow workspace geometry and motion defaults.

    Geometry is in design pixels. Text, chrome, margins and terminal motion use
    ``unit``; the complete editor always shrinks uniformly by ``editor_scale``.
    """

    bounds: Bounds = field(default_factory=lambda: Bounds(0, 0, 1920, 1080))
    theme: str | CodeTheme = "clean-flow"
    background: str = "#E8E6E2"
    editor_scale: float = 0.64
    code_size: float = 54
    terminal_size: float = 32
    shrink_duration: float = 0.8
    restore_duration: float = 0.9
    terminal_entrance_duration: float = 0.6
    terminal_exit_duration: float = 0.45

    def __post_init__(self):
        if not isinstance(self.bounds, Bounds):
            raise TypeError("workspace bounds must be Bounds")
        if self.bounds.width < 1 or self.bounds.height < 1:
            raise ValueError("workspace bounds need at least one design pixel per side")
        object.__setattr__(self, "theme", _theme(self.theme))
        ImageColor.getcolor(self.background, "RGBA")
        for name in (
            "editor_scale",
            "code_size",
            "terminal_size",
            "shrink_duration",
            "restore_duration",
            "terminal_entrance_duration",
            "terminal_exit_duration",
        ):
            object.__setattr__(self, name, _positive(getattr(self, name), name))
        if self.editor_scale >= 1:
            raise ValueError("editor_scale must be less than 1 to leave room for the terminal")
        terminal_width = self.bounds.width * (1 - self.editor_scale) - 128 * self.unit
        if terminal_width < _MIN_CHROME_WIDTH * self.unit - 1e-9:
            raise ValueError("editor_scale leaves too little terminal width for window chrome (need 192 * unit)")
        if self.bounds.width <= 96 * self.unit or self.bounds.height <= 200 * self.unit:
            raise ValueError("workspace bounds leave no positive code content area")
        if self.bounds.height * self.editor_scale <= 64 * self.unit:
            raise ValueError("editor_scale leaves no terminal content space below its header")

    @classmethod
    def named(cls, name, **kwargs):
        """Load the saved workspace design, with explicit optional overrides."""
        if name != "clean-flow":
            raise ValueError("Unknown code workspace design; use clean-flow")
        return cls(**kwargs)

    @property
    def unit(self):
        return min(self.bounds.width / 1920, self.bounds.height / 1080)

    @property
    def editor_full(self):
        return self.bounds

    @property
    def editor_split(self):
        width = self.bounds.width * self.editor_scale
        height = self.bounds.height * self.editor_scale
        left = self.bounds.left + 48 * self.unit
        top = self.bounds.center[1] - height / 2
        return Bounds(left, top, left + width, top + height)

    @property
    def terminal_bounds(self):
        editor = self.editor_split
        return Bounds(editor.right + 32 * self.unit, editor.top, self.bounds.right - 48 * self.unit, editor.bottom)

    @property
    def code_bounds(self):
        return Bounds(
            self.bounds.left + 48 * self.unit,
            self.bounds.top + 144 * self.unit,
            self.bounds.right - 48 * self.unit,
            self.bounds.bottom - 56 * self.unit,
        )

    @staticmethod
    def fluid(progress):
        """Monotonic settling with zero velocity at both endpoints."""
        return 1 - (1 - progress) ** 4 * (1 + 4 * progress)

    def window(self, box, title, *, children=(), fullscreen=False):
        return CodeWindow(box, title=title, theme=self.theme, fullscreen=fullscreen, unit=self.unit, children=children)

    def editor_motion(self, window, *, running):
        """Uniformly resize and position the complete editor window."""
        self._require_window(window)
        return Animation(
            window,
            {
                "scale": self.editor_scale if running else 1,
                "position": self.editor_split.center if running else self.editor_full.center,
            },
            rate_func=self.fluid,
        )

    def editor_corners(self, window, *, running):
        self._require_window(window)
        return tuple(
            Animation(shape, {"corner_radius": 32 * self.unit if running else 0}, rate_func=self.fluid)
            for shape in (window.face, window.header)
        )

    def terminal_in(self, window):
        self._require_window(window)
        center = window.bounds_box.center
        return Animation(
            window,
            {"scale": 1, "position": center, "opacity": 1},
            {"scale": 0.94, "position": (center[0], center[1] + 28 * self.unit), "opacity": 0},
            rate_func=self.fluid,
        )

    def terminal_out(self, window):
        self._require_window(window)
        center = window.bounds_box.center
        return Animation(
            window,
            {"scale": 0.96, "position": (center[0], center[1] + 18 * self.unit), "opacity": 0},
            rate_func=self.fluid,
        )

    @staticmethod
    def _require_window(window):
        if not isinstance(window, CodeWindow):
            raise TypeError("workspace motion requires a CodeWindow")
