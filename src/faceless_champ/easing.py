"""Easing curves. Every easing maps progress t in [0, 1] to eased progress.

Pass a function or a preset name anywhere a ``rate_func`` is accepted::

    scene.play(card.animate.move_to(960, 400), rate_func="emphasized")

Presets: ``linear``, ``smooth``, ``standard``, ``emphasized``, ``decelerate``,
``accelerate``, ``snappy``, ``gentle``, ``overshoot``, ``anticipate``. Curves are
module-level objects so scenes stay picklable and deep-copyable.
"""

from __future__ import annotations

import math
from types import MappingProxyType

from .components import finite


def linear(t: float) -> float:
    return t


def smooth(t: float) -> float:
    return t * t * (3 - 2 * t)


def ease_in(t: float) -> float:
    return t * t * t


def ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_quart(t: float) -> float:
    return 1 - (1 - t) ** 4


def ease_out_quint(t: float) -> float:
    return 1 - (1 - t) ** 5


def ease_in_expo(t: float) -> float:
    return 0.0 if t <= 0 else 2 ** (10 * t - 10)


def ease_out_expo(t: float) -> float:
    return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)


def ease_in_out_expo(t: float) -> float:
    if t <= 0 or t >= 1:
        return float(min(max(t, 0), 1))
    return 2 ** (20 * t - 10) / 2 if t < 0.5 else (2 - 2 ** (-20 * t + 10)) / 2


def ease_out_circ(t: float) -> float:
    return math.sqrt(max(0.0, 1 - (t - 1) ** 2))


class BackOut:
    """Ease out with an overshoot past the target before settling (1.70158 = classic)."""

    def __init__(self, overshoot: float = 1.70158):
        self.overshoot = finite(overshoot, "overshoot", 0)

    def __call__(self, t: float) -> float:
        c1 = self.overshoot
        c3 = c1 + 1
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

    def __repr__(self):
        return f"BackOut({self.overshoot:g})"


class BackIn:
    """Pull back slightly before moving (anticipation)."""

    def __init__(self, overshoot: float = 1.70158):
        self.overshoot = finite(overshoot, "overshoot", 0)

    def __call__(self, t: float) -> float:
        c1 = self.overshoot
        return (c1 + 1) * t**3 - c1 * t**2

    def __repr__(self):
        return f"BackIn({self.overshoot:g})"


class CubicBezier:
    """CSS-style ``cubic-bezier(x1, y1, x2, y2)`` easing (x values within [0, 1])."""

    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1, self.y1, self.x2, self.y2 = (finite(v, "bezier control") for v in (x1, y1, x2, y2))
        if not (0 <= self.x1 <= 1 and 0 <= self.x2 <= 1):
            raise ValueError("cubic_bezier x control points must be within [0, 1]")

    @staticmethod
    def _curve(t, a, b):
        return 3 * a * (1 - t) ** 2 * t + 3 * b * (1 - t) * t * t + t**3

    def __call__(self, x: float) -> float:
        if x <= 0 or x >= 1:
            return float(min(max(x, 0), 1))
        lo, hi, t = 0.0, 1.0, x
        for _ in range(32):  # bisection: monotonic in x for valid control points
            value = self._curve(t, self.x1, self.x2)
            if abs(value - x) < 1e-7:
                break
            if value < x:
                lo = t
            else:
                hi = t
            t = (lo + hi) / 2
        return self._curve(t, self.y1, self.y2)

    def __repr__(self):
        return f"CubicBezier({self.x1:g}, {self.y1:g}, {self.x2:g}, {self.y2:g})"

    def __eq__(self, other):
        return isinstance(other, CubicBezier) and (self.x1, self.y1, self.x2, self.y2) == (
            other.x1,
            other.y1,
            other.x2,
            other.y2,
        )

    def __hash__(self):
        return hash((CubicBezier, self.x1, self.y1, self.x2, self.y2))


def cubic_bezier(x1: float, y1: float, x2: float, y2: float) -> CubicBezier:
    return CubicBezier(x1, y1, x2, y2)


EASINGS = MappingProxyType(
    {
        "linear": linear,
        "smooth": smooth,
        "ease_in": ease_in,
        "ease_out": ease_out,
        "ease_in_out": ease_in_out,
        # Material-style curves: calm, confident UI motion.
        "standard": CubicBezier(0.2, 0.0, 0.0, 1.0),
        "emphasized": CubicBezier(0.05, 0.7, 0.1, 1.0),
        "decelerate": ease_out_quint,
        "accelerate": CubicBezier(0.3, 0.0, 1.0, 1.0),
        "snappy": ease_out_expo,
        "gentle": ease_in_out,
        "overshoot": BackOut(1.4),
        "anticipate": BackIn(1.4),
    }
)


def easing(value):
    """Resolve a preset name or callable to an easing function."""
    if value is None or callable(value):
        return value
    if isinstance(value, str):
        if value in EASINGS:
            return EASINGS[value]
        from . import plugins

        found = plugins.easing(value)
        if found is not None:
            return found
        choices = [*EASINGS, *plugins.names("easings")]
        raise ValueError(f"Unknown easing {value!r}; choose {', '.join(choices)} or pass a function")
    raise TypeError("rate_func must be a callable or an easing preset name")
