"""Reusable visual components in design pixels."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from .animation import AnimationBuilder


def finite(value: float, name: str, minimum: float | None = None) -> float:
    value = float(value)
    if not math.isfinite(value) or (minimum is not None and value < minimum):
        raise ValueError(f"{name} must be finite" + (f" and >= {minimum}" if minimum is not None else ""))
    return value


@dataclass(frozen=True)
class Canvas:
    width: int = 1920
    height: int = 1080
    bg: str = "black"

    def __post_init__(self) -> None:
        for name in ("width", "height"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"Canvas {name} must be a positive integer")

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height


class Component:
    def __init__(
        self,
        *,
        position: tuple[float, float] = (0, 0),
        anchor: str = "center",
        scale: float = 1.0,
        rotation: float = 0.0,
        opacity: float = 1.0,
        z_index: float = 0,
    ) -> None:
        if anchor not in {"center", "top_left"}:
            raise ValueError("anchor must be center or top_left")
        self.anchor = anchor
        self.position = tuple(finite(v, "position") for v in position)
        if len(self.position) != 2:
            raise ValueError("position needs x and y")
        self.scale = finite(scale, "scale", 0.001)
        self.rotation = finite(rotation, "rotation")
        self.opacity = finite(opacity, "opacity", 0)
        if self.opacity > 1:
            raise ValueError("opacity must be <= 1")
        self.z_index = finite(z_index, "z_index")

    def move_to(self, x: float, y: float) -> Self:
        self.position = (finite(x, "x"), finite(y, "y"))
        return self

    @property
    def animate(self) -> AnimationBuilder:
        from .animation import AnimationBuilder

        return AnimationBuilder(self)

    def state(self) -> dict:
        return {
            "position": self.position,
            "scale": self.scale,
            "rotation": self.rotation,
            "opacity": self.opacity,
            "reveal": 1.0,
            "draw": 1.0,
        }


class Text(Component):
    def __init__(
        self,
        text: str,
        *,
        font: str | Path | None = None,
        font_size: float = 64,
        color: str = "white",
        align: str = "left",
        spacing: float = 8,
        font_weight: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if align not in {"left", "center", "right"}:
            raise ValueError("align must be left, center, or right")
        self.text, self.font = text, str(font) if font else None
        self.font_size = finite(font_size, "font_size", 1)
        self.color, self.align = color, align
        self.spacing = finite(spacing, "spacing", 0)
        self.font_weight = None if font_weight is None else finite(font_weight, "font_weight", 1)


class Equation(Component):
    """TeX-style math typeset with the optional Matplotlib MathText engine.

    Pass an expression without dollar delimiters. ``max_width`` scales long
    expressions down to fit a design-pixel width, retaining their aspect ratio.
    """

    def __init__(
        self,
        expression: str,
        *,
        font_size: float = 64,
        color: str = "white",
        fontset: str = "stix",
        max_width: float | None = None,
        color_map: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if not isinstance(expression, str):
            raise TypeError("expression must be a string")
        if not expression.strip() or "$" in expression or "\n" in expression:
            raise ValueError("Equation needs a nonempty, single-line expression without dollar delimiters")
        if fontset not in {"stix", "stixsans", "cm", "dejavusans", "dejavuserif"}:
            raise ValueError("Unsupported MathText fontset")
        self.expression, self.fontset, self.color = expression, fontset, color
        self.font_size = finite(font_size, "font_size", 1)
        self.max_width = None if max_width is None else finite(max_width, "max_width", 1)
        if color_map is not None and not isinstance(color_map, Mapping):
            raise TypeError("color_map must map individual symbols to colors")
        self.color_map = dict(color_map or {})
        for symbol, symbol_color in self.color_map.items():
            if (
                not isinstance(symbol, str)
                or not symbol.strip()
                or symbol in {"$", "\\"}
                or not (len(symbol) == 1 or re.fullmatch(r"\\[A-Za-z]+", symbol))
            ):
                raise ValueError("color_map keys must be a single character or TeX symbol command such as \\mu")
            if not isinstance(symbol_color, str):
                raise TypeError("color_map values must be color strings")


class Image(Component):
    def __init__(
        self, path: str | Path, *, width: float = 400, height: float = 300, fit: str = "contain", **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        if fit not in {"contain", "cover"}:
            raise ValueError("fit must be contain or cover")
        self.path = Path(path)
        self.width, self.height = finite(width, "width", 1), finite(height, "height", 1)
        self.fit = fit


class Icon(Image):
    """Tint a transparent raster icon with a color, preserving its alpha mask."""

    def __init__(self, path: str | Path, *, size: float = 120, color: str = "white", **kwargs: Any) -> None:
        super().__init__(path, width=size, height=size, **kwargs)
        self.color = color


class Shape(Component):
    def __init__(
        self,
        *,
        width: float = 200,
        height: float = 200,
        fill: str | None = None,
        stroke: str | None = "white",
        stroke_width: float = 4,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.width, self.height = finite(width, "width", 1), finite(height, "height", 1)
        self.fill, self.stroke = fill, stroke
        self.stroke_width = finite(stroke_width, "stroke_width", 0)


class Rectangle(Shape):
    def __init__(self, *, corner_radius: float = 0, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.corner_radius = finite(corner_radius, "corner_radius", 0)
        if self.corner_radius > min(self.width, self.height) / 2:
            raise ValueError("corner_radius must fit the rectangle")


class Square(Rectangle):
    def __init__(self, side: float = 200, **kwargs: Any) -> None:
        super().__init__(width=side, height=side, **kwargs)


class Circle(Shape):
    def __init__(self, radius: float = 100, **kwargs: Any) -> None:
        super().__init__(width=radius * 2, height=radius * 2, **kwargs)


class Triangle(Shape):
    pass


class Line(Shape):
    """Horizontal line centered in its local bounding box."""

    def __init__(self, length: float = 200, **kwargs: Any) -> None:
        super().__init__(width=length, height=1, **kwargs)


class Polyline(Shape):
    """A drawable path through canvas points, optionally closed and filled.

    Its default position is the points' bounding-box center. Explicit position
    replaces that center; transforms work like those of every other shape.
    """

    def __init__(self, points, *, closed: bool = False, line_cap: str = "butt", **kwargs: Any) -> None:
        points = tuple(tuple(finite(v, "point") for v in p) for p in points)
        if len(points) < (3 if closed else 2) or any(len(p) != 2 for p in points):
            raise ValueError("Polyline needs at least two (x, y) points; closed paths need three")
        if not any(a != b for a, b in pairwise(points)):
            raise ValueError("Polyline needs distinct points")
        left, top = min(p[0] for p in points), min(p[1] for p in points)
        right, bottom = max(p[0] for p in points), max(p[1] for p in points)
        kwargs.setdefault("position", ((left + right) / 2, (top + bottom) / 2))
        super().__init__(width=max(1, right - left), height=max(1, bottom - top), **kwargs)
        self.points = tuple((x - left, y - top) for x, y in points)
        self.closed = closed
        if line_cap not in {"butt", "round"}:
            raise ValueError("line_cap must be butt or round")
        self.line_cap = line_cap


class Arrow(Line):
    """An arrow between two design-pixel points; supports Draw and transforms."""

    def __init__(
        self, start: tuple[float, float], end: tuple[float, float], *, tip_size: float = 18, **kwargs: Any
    ) -> None:
        if len(start) != 2 or len(end) != 2:
            raise ValueError("Arrow endpoints need x and y")
        start = tuple(finite(v, "arrow start") for v in start)
        end = tuple(finite(v, "arrow end") for v in end)
        length = math.dist(start, end)
        if length < 1:
            raise ValueError("Arrow endpoints must be at least one pixel apart")
        kwargs.setdefault("position", tuple((a + b) / 2 for a, b in zip(start, end)))
        kwargs.setdefault("rotation", math.degrees(math.atan2(end[1] - start[1], end[0] - start[0])))
        super().__init__(length, **kwargs)
        self.tip_size = finite(tip_size, "tip_size", 1)
        if self.tip_size > length:
            raise ValueError("Arrow tip_size must fit its length")
