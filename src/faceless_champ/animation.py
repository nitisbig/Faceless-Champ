"""Animation descriptions; interpolation is independent of rendering."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

from .components import Component, Equation, Number, Shape, Text, finite


def linear(t: float) -> float:
    return t


def smooth(t: float) -> float:
    return t * t * (3 - 2 * t)


def ease_in(t: float) -> float:
    return t * t * t


def ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


@dataclass
class Animation:
    component: Component
    targets: dict
    starts: dict | None = None
    keyframes: dict[str, tuple[tuple[float, object], ...]] | None = None
    relative: tuple[str, ...] = ()
    rate_func: Callable[[float], float] | None = None


class AnimationBuilder(Animation):
    def __init__(self, component: Component) -> None:
        super().__init__(component, {})

    def _to(self, key, value):
        from .timeline import _validate_animated_value

        if key not in self.component.state():
            raise ValueError(f"Unsupported animation property: {key}")
        _validate_animated_value(key, value)
        self.targets[key] = value if isinstance(value, tuple) else finite(value, key)
        return self

    def fill_to(self, color) -> Self:
        from .motion import rgba

        return self._to("fill", rgba(color))

    def stroke_to(self, color) -> Self:
        from .motion import rgba

        return self._to("stroke", rgba(color))

    def color_to(self, color) -> Self:
        from .motion import rgba

        return self._to("color", rgba(color))

    def width_to(self, value) -> Self:
        return self._to("width", value)

    def height_to(self, value) -> Self:
        return self._to("height", value)

    def stroke_width_to(self, value) -> Self:
        return self._to("stroke_width", value)

    def corner_radius_to(self, value) -> Self:
        return self._to("corner_radius", value)

    def scale_xy_to(self, x, y) -> Self:
        return self._to("scale_x", x)._to("scale_y", y)

    def progress_to(self, value) -> Self:
        return self._to("progress", value)

    def mask_to(self, *, position=None, width=None, height=None) -> Self:
        for key, value in (("mask_position", position), ("mask_width", width), ("mask_height", height)):
            if value is not None:
                self._to(key, tuple(value) if key == "mask_position" else value)
        return self

    def data_to(self, data) -> Self:
        from .charts import Chart

        if not isinstance(self.component, Chart):
            raise TypeError("data_to requires a Chart")
        self.targets["data"] = self.component.transition_data(data)
        return self

    def value_to(self, value: float) -> Self:
        if not isinstance(self.component, Number):
            raise TypeError("value_to requires a Number")
        from .indicators import Countdown

        self.targets["value"] = finite(value, "value", 0 if isinstance(self.component, Countdown) else None)
        return self

    def move_to(self, x: float, y: float) -> Self:
        self.targets["position"] = (finite(x, "x"), finite(y, "y"))
        return self

    def scale_to(self, value: float) -> Self:
        self.targets["scale"] = finite(value, "scale", 0.001)
        return self

    def rotate_to(self, degrees: float) -> Self:
        self.targets["rotation"] = finite(degrees, "rotation")
        return self

    def opacity_to(self, value: float) -> Self:
        value = finite(value, "opacity", 0)
        if value > 1:
            raise ValueError("opacity must be <= 1")
        self.targets["opacity"] = value
        return self


def FadeIn(component: Component) -> Animation:
    return Animation(component, {"opacity": component.opacity}, {"opacity": 0.0})


def FadeOut(component: Component) -> Animation:
    return Animation(component, {"opacity": 0.0})


def Typewriter(component: Text) -> Animation:
    if not isinstance(component, Text):
        raise TypeError("Typewriter requires Text")
    return Animation(component, {"reveal": 1.0}, {"reveal": 0.0})


def Write(component: Equation) -> Animation:
    """Reveal a fully typeset equation from left to right without reflow."""
    if not isinstance(component, Equation):
        raise TypeError("Write requires Equation")
    return Animation(component, {"reveal": 1.0}, {"reveal": 0.0}, rate_func=linear)


def Draw(component: Shape) -> Animation:
    if not isinstance(component, Shape):
        raise TypeError("Draw requires a shape")
    return Animation(component, {"draw": 1.0}, {"draw": 0.0})


def _component(component: Component) -> Component:
    if not isinstance(component, Component):
        raise TypeError("Animation requires a Component")
    return component


def _direction(direction: str, distance: float) -> tuple[float, float]:
    directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    if direction not in directions:
        raise ValueError("direction must be up, down, left, or right")
    distance = finite(distance, "distance", 0)
    return tuple(value * distance for value in directions[direction])


def SlideIn(component: Component, *, direction: str = "up", distance: float = 80) -> Animation:
    """Move in the named direction from an offset, while fading into place."""
    component = _component(component)
    delta = _direction(direction, distance)
    return Animation(
        component,
        {"position": (0, 0), "opacity": component.opacity},
        {"position": tuple(-value for value in delta), "opacity": 0},
        relative=("position",),
        rate_func=ease_out,
    )


def SlideOut(component: Component, *, direction: str = "down", distance: float = 80) -> Animation:
    component = _component(component)
    return Animation(
        component,
        {"position": _direction(direction, distance), "opacity": 0},
        relative=("position",),
        rate_func=ease_in,
    )


def ZoomIn(component: Component, *, from_scale: float = 0.6) -> Animation:
    """Fade in while scaling from a ratio of the current timeline scale."""
    component = _component(component)
    return Animation(
        component,
        {"scale": 1, "opacity": component.opacity},
        {"scale": finite(from_scale, "from_scale", 0.001), "opacity": 0},
        relative=("scale",),
        rate_func=ease_out,
    )


def ZoomOut(component: Component, *, to_scale: float = 0.6) -> Animation:
    component = _component(component)
    return Animation(
        component, {"scale": finite(to_scale, "to_scale", 0.001), "opacity": 0}, relative=("scale",), rate_func=ease_in
    )


def PopIn(component: Component, *, from_scale: float = 0.45, overshoot: float = 1.14) -> Animation:
    """Grow past the resting size, then settle; opacity remains bounded."""
    component = _component(component)
    start = finite(from_scale, "from_scale", 0.001)
    peak = finite(overshoot, "overshoot", 1)
    return Animation(
        component,
        {"scale": 1, "opacity": component.opacity},
        {"scale": start, "opacity": 0},
        keyframes={"scale": ((0, start), (0.64, peak), (1, 1))},
        relative=("scale",),
        rate_func=smooth,
    )


def PopOut(component: Component, *, to_scale: float = 0.45, overshoot: float = 1.08) -> Animation:
    component = _component(component)
    end = finite(to_scale, "to_scale", 0.001)
    peak = finite(overshoot, "overshoot", 1)
    return Animation(
        component,
        {"scale": end, "opacity": 0},
        keyframes={"scale": ((0, 1), (0.28, peak), (1, end))},
        relative=("scale",),
        rate_func=smooth,
    )


def BounceIn(component: Component, *, distance: float = 80) -> Animation:
    """Rise from below, overshoot slightly, and settle at the resting position."""
    component = _component(component)
    distance = finite(distance, "distance", 0)
    points = ((0, (0, distance)), (0.55, (0, -distance * 0.18)), (0.78, (0, distance * 0.07)), (1, (0, 0)))
    return Animation(
        component,
        {"position": (0, 0), "opacity": component.opacity},
        {"position": (0, distance), "opacity": 0},
        keyframes={"position": points},
        relative=("position",),
        rate_func=smooth,
    )


def SpinIn(component: Component, *, angle: float = -35, from_scale: float = 0.7) -> Animation:
    component = _component(component)
    return Animation(
        component,
        {"rotation": 0, "scale": 1, "opacity": component.opacity},
        {"rotation": finite(angle, "angle"), "scale": finite(from_scale, "from_scale", 0.001), "opacity": 0},
        relative=("rotation", "scale"),
        rate_func=ease_out,
    )


def _cycles(cycles: int) -> int:
    if not isinstance(cycles, int) or isinstance(cycles, bool) or cycles < 1:
        raise ValueError("cycles must be a positive integer")
    return cycles


def Pulse(component: Component, *, factor: float = 1.12, cycles: int = 1) -> Animation:
    """Scale up and back around the current timeline size without drift."""
    component = _component(component)
    factor = finite(factor, "factor", 0.001)
    cycles = _cycles(cycles)
    points = [(0, 1)]
    for cycle in range(cycles):
        points.extend([((cycle + 0.5) / cycles, factor), ((cycle + 1) / cycles, 1)])
    return Animation(component, {"scale": 1}, keyframes={"scale": tuple(points)}, relative=("scale",), rate_func=smooth)


def Shake(component: Component, *, distance: float = 14, direction: str = "horizontal", cycles: int = 2) -> Animation:
    """Shake around the current position, returning exactly to it."""
    component = _component(component)
    if direction not in {"horizontal", "vertical"}:
        raise ValueError("direction must be horizontal or vertical")
    distance = finite(distance, "distance", 0)
    cycles = _cycles(cycles)
    points = []
    for step in range(cycles * 4 + 1):
        offset = (0, distance, 0, -distance)[step % 4]
        value = (offset, 0) if direction == "horizontal" else (0, offset)
        points.append((step / (cycles * 4), value))
    return Animation(
        component, {"position": (0, 0)}, keyframes={"position": tuple(points)}, relative=("position",), rate_func=smooth
    )


def Wiggle(component: Component, *, angle: float = 8, cycles: int = 2) -> Animation:
    """Rock around the current rotation, returning exactly to it."""
    component = _component(component)
    angle = finite(angle, "angle", 0)
    cycles = _cycles(cycles)
    points = tuple((step / (cycles * 4), (0, angle, 0, -angle)[step % 4]) for step in range(cycles * 4 + 1))
    return Animation(
        component, {"rotation": 0}, keyframes={"rotation": points}, relative=("rotation",), rate_func=smooth
    )


def relative_value(property: str, base, value):
    """Scale uses factors; numeric and position properties use additive offsets."""
    if property == "scale":
        return base * value
    if isinstance(base, tuple):
        return tuple(a + b for a, b in zip(base, value))
    return base + value


def interpolate(a, b, t):
    if isinstance(a, tuple):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    return a + (b - a) * t


def ChartReveal(component) -> Animation:
    """Reveal chart marks while retaining axes and labels."""
    from .charts import Chart

    if not isinstance(component, Chart):
        raise TypeError("ChartReveal requires a Chart")
    return Animation(component, {"reveal": 1.0}, {"reveal": 0.0}, rate_func=linear)
