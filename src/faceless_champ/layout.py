"""Measured initial layouts and transformable component hierarchies."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Self

from .components import Component, finite


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

    # -- construction -------------------------------------------------------

    @classmethod
    def from_center(cls, center, width: float, height: float) -> Bounds:
        x, y = center
        width, height = finite(width, "width", 0), finite(height, "height", 0)
        return cls(x - width / 2, y - height / 2, x + width / 2, y + height / 2)

    @classmethod
    def from_size(cls, left: float, top: float, width: float, height: float) -> Bounds:
        return cls(left, top, left + finite(width, "width", 0), top + finite(height, "height", 0))

    # -- points -------------------------------------------------------------

    def point(self, anchor: str = "center") -> tuple[float, float]:
        """A named point: center, top, bottom, left, right, top_left, top_right,
        bottom_left or bottom_right."""
        xs = {"left": self.left, "center": (self.left + self.right) / 2, "right": self.right}
        ys = {"top": self.top, "center": (self.top + self.bottom) / 2, "bottom": self.bottom}
        if anchor == "center":
            return xs["center"], ys["center"]
        if anchor in ys:
            return xs["center"], ys[anchor]
        if anchor in xs:
            return xs[anchor], ys["center"]
        parts = anchor.split("_")
        if len(parts) == 2 and parts[0] in ys and parts[1] in xs:
            return xs[parts[1]], ys[parts[0]]
        raise ValueError(f"Unknown anchor {anchor!r}")

    # -- derived boxes -----------------------------------------------------

    def inset(
        self,
        amount: float = 0,
        *,
        x: float | None = None,
        y: float | None = None,
        left: float | None = None,
        top: float | None = None,
        right: float | None = None,
        bottom: float | None = None,
    ) -> Bounds:
        """Shrink by padding (negative values grow). Specific edges override x/y/amount."""
        x = amount if x is None else x
        y = amount if y is None else y
        left, right = (x if left is None else left), (x if right is None else right)
        top, bottom = (y if top is None else top), (y if bottom is None else bottom)
        result_left, result_right = self.left + left, self.right - right
        result_top, result_bottom = self.top + top, self.bottom - bottom
        if result_right < result_left or result_bottom < result_top:
            raise ValueError("inset is larger than the bounds")
        return Bounds(result_left, result_top, result_right, result_bottom)

    def columns(self, spec=2, *, gap: float = 0) -> tuple[Bounds, ...]:
        """Side-by-side boxes. ``spec`` is a count or relative weights: columns((2, 1), gap=32)."""
        return tuple(
            Bounds(self.left + a, self.top, self.left + b, self.bottom) for a, b in _segments(self.width, spec, gap)
        )

    def rows(self, spec=2, *, gap: float = 0) -> tuple[Bounds, ...]:
        """Stacked boxes. ``spec`` is a count or relative weights: rows((1, 3), gap=24)."""
        return tuple(
            Bounds(self.left, self.top + a, self.right, self.top + b) for a, b in _segments(self.height, spec, gap)
        )

    def grid(self, rows: int, cols: int, *, gap: float = 0, gap_x: float | None = None, gap_y: float | None = None):
        """Row-major cells of an evenly divided grid."""
        return tuple(
            cell
            for row in self.rows(rows, gap=gap if gap_y is None else gap_y)
            for cell in row.columns(cols, gap=gap if gap_x is None else gap_x)
        )

    def fit(self, width: float, height: float, *, align: str = "center") -> Bounds:
        """A width x height box placed inside at ``align`` (shrunk to fit, aspect kept)."""
        width, height = finite(width, "width", 0.000001), finite(height, "height", 0.000001)
        scale = min(1.0, self.width / width, self.height / height)
        width, height = width * scale, height * scale
        x, y = self.point(align)
        left = x - width / 2 if align in {"center", "top", "bottom"} else (x if "left" in align else x - width)
        top = y - height / 2 if align in {"center", "left", "right"} else (y if "top" in align else y - height)
        return Bounds(left, top, left + width, top + height)

    def aspect(self, ratio: float, *, align: str = "center") -> Bounds:
        """The largest box with width/height ``ratio`` inside these bounds."""
        ratio = finite(ratio, "ratio", 0.000001)
        return self.fit(ratio * max(self.height, self.width / ratio), max(self.height, self.width / ratio), align=align)

    def union(self, other: Bounds) -> Bounds:
        return Bounds(
            min(self.left, other.left),
            min(self.top, other.top),
            max(self.right, other.right),
            max(self.bottom, other.bottom),
        )

    def contains(self, other, *, tolerance: float = 0.5) -> bool:
        """Whether another Bounds (or an (x, y) point) lies inside."""
        if isinstance(other, Bounds):
            return (
                other.left >= self.left - tolerance
                and other.top >= self.top - tolerance
                and other.right <= self.right + tolerance
                and other.bottom <= self.bottom + tolerance
            )
        x, y = other
        return (
            self.left - tolerance <= x <= self.right + tolerance
            and self.top - tolerance <= y <= self.bottom + tolerance
        )


def _segments(extent, spec, gap):
    gap = finite(gap, "gap", 0)
    if isinstance(spec, int) and not isinstance(spec, bool):
        if spec < 1:
            raise ValueError("count must be at least 1")
        weights = (1.0,) * spec
    else:
        weights = tuple(finite(w, "weight", 0.000001) for w in spec)
        if not weights:
            raise ValueError("weights must not be empty")
    usable = extent - gap * (len(weights) - 1)
    if usable <= 0:
        raise ValueError("gaps exceed the available space")
    total, offset, result = sum(weights), 0.0, []
    for weight in weights:
        size = usable * weight / total
        result.append((offset, offset + size))
        offset += size + gap
    return result


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


def _size(component, measurement):
    return measurement.size(component, logical=True)


def _points(component, measurement):
    return tuple(measurement.points(component))


def _enclose(points) -> Bounds:
    return Bounds(
        min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)
    )


def bounds(component: Component) -> Bounds:
    if not isinstance(component, Component):
        raise TypeError("bounds requires a Component")
    from ._rendering.measure import measurement_session

    return measurement_session().bounds(component)


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

    def validate_animation(self, property, value):
        if not property.startswith("effect.") and property not in {
            "position",
            "scale",
            "rotation",
            "opacity",
            "scale_x",
            "scale_y",
            "mask_position",
            "mask_width",
            "mask_height",
            "wipe",
            "clip",
        }:
            raise ValueError("Groups support transforms, opacity, masks, and wipe animations")
        super().validate_animation(property, value)

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
