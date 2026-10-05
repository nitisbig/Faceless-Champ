"""Measured initial layouts and transformable component hierarchies."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Self

from .components import Component, Image, finite


@dataclass(frozen=True)
class Bounds:
    """Axis-aligned rectangle in design pixels, including raster padding."""

    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self):
        for name in ("left", "top", "right", "bottom"):
            object.__setattr__(self, name, finite(getattr(self, name), name))
        if self.right < self.left or self.bottom < self.top:
            raise ValueError("Bounds edges must be ordered")

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def center(self) -> tuple[float, float]:
        return ((self.left + self.right) / 2, (self.top + self.bottom) / 2)


def transform_point(point, origin, state):
    """Apply local X/Y scaling and clockwise rotation around the parent origin."""
    angle = math.radians(state["rotation"])
    x, y = (
        (value - pivot) * state["scale"] * state.get(axis, 1)
        for value, pivot, axis in zip(point, origin, ("scale_x", "scale_y"))
    )
    return (
        state["position"][0] + x * math.cos(angle) - y * math.sin(angle),
        state["position"][1] + x * math.sin(angle) + y * math.cos(angle),
    )


def _size(component, renderer):
    # Fixed viewports need neither their assets nor optional map dependencies to lay out.
    from .charts import Chart
    from .maps import Map
    from .subtitles import Captions

    if isinstance(component, (Image, Chart, Map)):
        return max(1, round(component.width)), max(1, round(component.height))
    if isinstance(component, Captions):
        sizes = [renderer._caption_sprite(component, 1, phrase[0].start).size for phrase in component.phrases]
        return max(w for w, _ in sizes), max(h for _, h in sizes)
    return renderer._sprite(component, component.state(), 1, 0).size


def _points(component, renderer):
    if isinstance(component, Group):
        return [
            transform_point(point, component._origin, component.state())
            for child in component.children
            for point in _points(child, renderer)
        ]
    w, h = _size(component, renderer)
    state = component.state()
    center = component.position
    if component.anchor == "top_left":
        center = (
            center[0] + w * component.scale * component.scale_x / 2,
            center[1] + h * component.scale * component.scale_y / 2,
        )
    state = {**state, "position": center}
    return [
        transform_point(point, (0, 0), state)
        for point in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))
    ]


def _enclose(points) -> Bounds:
    return Bounds(
        min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)
    )


def bounds(component: Component) -> Bounds:
    if not isinstance(component, Component):
        raise TypeError("bounds requires a Component")
    from .renderer import PillowRenderer

    return _enclose(_points(component, PillowRenderer(1, frame_cache_mb=0, caption_cache_mb=0)))


def _target(other) -> Bounds:
    if isinstance(other, Bounds):
        return other
    if isinstance(other, Component):
        return other.bounds
    raise TypeError("Layout target must be a Component or Bounds")


def _beside(current, target, direction, gap, align):
    gap = finite(gap, "gap", 0)
    if direction not in {"left", "right", "up", "down"}:
        raise ValueError("direction must be left, right, up, or down")
    horizontal = direction in {"left", "right"}
    choices = {"center", "top", "bottom"} if horizontal else {"center", "left", "right"}
    if align not in choices:
        raise ValueError(f"align must be one of {sorted(choices)} for {direction}")
    if horizontal:
        dx = target.right + gap - current.left if direction == "right" else target.left - gap - current.right
        dy = (
            target.center[1] - current.center[1]
            if align == "center"
            else getattr(target, align) - getattr(current, align)
        )
    else:
        dy = target.bottom + gap - current.top if direction == "down" else target.top - gap - current.bottom
        dx = (
            target.center[0] - current.center[0]
            if align == "center"
            else getattr(target, align) - getattr(current, align)
        )
    return dx, dy


def next_to(component, other, *, direction="right", gap=20, align="center"):
    component.shift(*_beside(component.bounds, _target(other), direction, gap, align))


def align_to(component, other, *, edge="left"):
    if edge not in {"left", "right", "top", "bottom", "center_x", "center_y", "center"}:
        raise ValueError("edge must be left, right, top, bottom, center_x, center_y, or center")
    current, target = component.bounds, _target(other)
    dx = dy = 0
    if edge in {"left", "right"}:
        dx = getattr(target, edge) - getattr(current, edge)
    elif edge in {"top", "bottom"}:
        dy = getattr(target, edge) - getattr(current, edge)
    else:
        if edge in {"center", "center_x"}:
            dx = target.center[0] - current.center[0]
        if edge in {"center", "center_y"}:
            dy = target.center[1] - current.center[1]
    component.shift(dx, dy)


class Group(Component):
    """Group members in their existing coordinates around a fixed layout pivot.

    Create groups before adding their members to a scene. Membership is immutable;
    use Scene.remove() for visibility. Child animations remain independently usable.
    """

    def __init__(self, *children: Component, **kwargs: Any) -> None:
        if not children:
            raise ValueError("Group requires at least one component")
        seen = set()

        def check(child):
            if not isinstance(child, Component):
                raise TypeError("Group members must be Components")
            if child in seen:
                raise ValueError("A component may appear only once in a group hierarchy")
            seen.add(child)
            if isinstance(child, Group):
                for descendant in child.children:
                    check(descendant)

        for child in children:
            check(child)
        self._children = tuple(children)
        box = _enclose([point for child in children for point in _corners(child.bounds)])
        anchor = kwargs.get("anchor", "center")
        self._origin = (box.left, box.top) if anchor == "top_left" else box.center
        kwargs.setdefault("position", self._origin)
        super().__init__(**kwargs)

    @property
    def children(self) -> tuple[Component, ...]:
        return self._children

    def arrange(self, *, direction: str = "right", gap: float = 20, align: str = "center") -> Self:
        """Arrange members with measured gaps, preserving this group's fixed pivot.

        Direction and gap are measured in the group's untransformed coordinate space.
        Parent scaling/rotation subsequently applies to the complete arranged layout.
        """
        boxes = [child.bounds for child in self.children]
        # Validate even a single-member arrangement, and prepare before mutating anything.
        _beside(boxes[0], boxes[0], direction, gap, align)
        placed = [boxes[0]]
        offsets = [(0, 0)]
        for box in boxes[1:]:
            dx, dy = _beside(box, placed[-1], direction, gap, align)
            offsets.append((dx, dy))
            placed.append(Bounds(box.left + dx, box.top + dy, box.right + dx, box.bottom + dy))
        union = _enclose([point for box in placed for point in _corners(box)])
        pivot = (union.left, union.top) if self.anchor == "top_left" else union.center
        shift = (self._origin[0] - pivot[0], self._origin[1] - pivot[1])
        for child, (dx, dy) in zip(self.children, offsets):
            child.shift(dx + shift[0], dy + shift[1])
        return self


def _corners(box):
    return ((box.left, box.top), (box.right, box.top), (box.right, box.bottom), (box.left, box.bottom))
