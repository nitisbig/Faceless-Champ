"""Animation descriptions; interpolation is independent of rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from .components import Component, Shape, Text, finite


def linear(t: float) -> float:
    return t


def smooth(t: float) -> float:
    return t * t * (3 - 2 * t)


@dataclass
class Animation:
    component: Component
    targets: dict
    starts: dict | None = None


class AnimationBuilder(Animation):
    def __init__(self, component: Component) -> None:
        super().__init__(component, {})

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


def Draw(component: Shape) -> Animation:
    if not isinstance(component, Shape):
        raise TypeError("Draw requires a shape")
    return Animation(component, {"draw": 1.0}, {"draw": 0.0})


def interpolate(a, b, t):
    if isinstance(a, tuple):
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    return a + (b - a) * t
