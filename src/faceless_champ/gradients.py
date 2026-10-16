"""Immutable surface paints and pure, encoded-sRGB premultiplied color math."""

import math
from bisect import bisect_right
from dataclasses import dataclass, field
from itertools import islice, pairwise

from PIL import ImageColor


def _number(value, name, minimum=None, maximum=None):
    try:
        if isinstance(value, bool):
            raise TypeError("boolean is not a gradient number")
        value = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(f"{name} must be in [{minimum}, {maximum}]")
    return value


@dataclass(frozen=True)
class GradientStop:
    """A stop in [0, 1]. Transparent colors normalize to transparent black."""

    offset: float
    color: str
    _rgba: tuple[int, int, int, int] = field(init=False, repr=False, compare=False)
    _premultiplied: tuple[float, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "offset", _number(self.offset, "stop offset", 0, 1))
        if not isinstance(self.color, str):
            raise TypeError("Gradient stop color must be a color string")
        try:
            rgba = ImageColor.getcolor(self.color, "RGBA")
        except ValueError as exc:
            raise ValueError(f"Invalid gradient color: {self.color!r}") from exc
        if rgba[3] == 0:
            rgba = (0, 0, 0, 0)
        object.__setattr__(self, "color", "#" + "".join(f"{c:02X}" for c in rgba))
        object.__setattr__(self, "_rgba", rgba)
        object.__setattr__(self, "_premultiplied", (*[c * rgba[3] / 255 for c in rgba[:3]], float(rgba[3])))


def _stops(value):
    try:
        stops = tuple(islice(iter(value), 65))
    except TypeError as exc:
        raise TypeError("Gradient stops must be an iterable of GradientStop") from exc
    if not 2 <= len(stops) <= 64:
        raise ValueError("Gradient needs 2 to 64 stops")
    if any(not isinstance(stop, GradientStop) for stop in stops):
        raise TypeError("Gradient stops must be GradientStop objects")
    if any(a.offset >= b.offset for a, b in pairwise(stops)):
        raise ValueError("Gradient stop offsets must be strictly increasing")
    return stops


@dataclass(frozen=True)
class LinearGradient:
    """Linear paint; 0 degrees runs right, 90 down, clockwise in design space."""

    stops: tuple[GradientStop, ...]
    angle: float = 0
    _offsets: tuple[float, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        stops = _stops(self.stops)
        object.__setattr__(self, "stops", stops)
        object.__setattr__(self, "_offsets", tuple(stop.offset for stop in stops))
        object.__setattr__(self, "angle", _number(self.angle, "gradient angle") % 360)


@dataclass(frozen=True)
class RadialGradient:
    """Circular paint; center is normalized, radius is a fraction of min(width, height)."""

    stops: tuple[GradientStop, ...]
    center: tuple[float, float] = (0.5, 0.5)
    radius: float = 0.5
    _offsets: tuple[float, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        stops = _stops(self.stops)
        object.__setattr__(self, "stops", stops)
        object.__setattr__(self, "_offsets", tuple(stop.offset for stop in stops))
        try:
            center = tuple(islice(iter(self.center), 3))
        except TypeError as exc:
            raise ValueError("Gradient center needs two coordinates") from exc
        if len(center) != 2:
            raise ValueError("Gradient center needs two coordinates")
        object.__setattr__(self, "center", tuple(_number(v, "gradient center", 0, 1) for v in center))
        object.__setattr__(self, "radius", _number(self.radius, "gradient radius", 1e-6, 16))


def _sample(gradient, offset):
    """Scalar reference. Keep float alpha through division, then quantize once."""
    stops = gradient.stops
    index = bisect_right(gradient._offsets, offset)
    if index == 0:
        return stops[0]._rgba
    left = stops[index - 1]
    if index == len(stops) or offset == left.offset:
        return left._rgba
    right = stops[index]
    u = (offset - left.offset) / (right.offset - left.offset)
    channels = tuple(a + (b - a) * u for a, b in zip(left._premultiplied, right._premultiplied))
    alpha = math.floor(channels[3] + 0.5)
    if alpha == 0:
        return (0, 0, 0, 0)
    return (*[min(255, max(0, math.floor(c * 255 / channels[3] + 0.5))) for c in channels[:3]], alpha)


def _linear_coefficients(gradient, width, height):
    cardinal = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}
    if gradient.angle in cardinal:
        dx, dy = cardinal[gradient.angle]
    else:
        radians = math.radians(gradient.angle)
        dx, dy = math.cos(radians), math.sin(radians)
    x, y = dx * width, dy * height
    span = abs(x) + abs(y)
    return (x / span, y / span, -(min(0, x) + min(0, y)) / span) if span else (0, 0, 0)


def _parameter(gradient, x, y, width, height):
    """Sample normalized face coordinates, using physical design-space aspect ratio."""
    if isinstance(gradient, LinearGradient):
        a, b, c = _linear_coefficients(gradient, width, height)
        value = a * x + b * y + c
    else:
        cx, cy = gradient.center
        value = math.hypot((x - cx) * width, (y - cy) * height) / (gradient.radius * min(width, height))
    return min(1, max(0, value))
