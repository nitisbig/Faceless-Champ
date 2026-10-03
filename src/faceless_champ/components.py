"""Reusable visual components in design pixels."""

from __future__ import annotations

import math
from dataclasses import dataclass
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
    pass


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
