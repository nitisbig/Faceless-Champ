"""Immutable local-coordinate alpha masks."""

from dataclasses import dataclass

from .components import finite


@dataclass(frozen=True)
class Mask:
    width: float
    height: float
    position: tuple = (0, 0)
    kind: str = "rectangle"
    points: tuple = ()

    def __post_init__(self):
        for key in ("width", "height"):
            object.__setattr__(self, key, finite(getattr(self, key), key, 0))
        position = tuple(finite(v, "mask position") for v in self.position)
        if len(position) != 2:
            raise ValueError("mask position needs two coordinates")
        object.__setattr__(self, "position", position)
        if self.kind not in {"rectangle", "ellipse", "polygon"}:
            raise ValueError("Unsupported mask kind")
        points = tuple(tuple(finite(v, "mask point") for v in p) for p in self.points)
        if self.kind == "polygon" and (len(points) < 3 or any(len(p) != 2 for p in points)):
            raise ValueError("Polygon mask needs three normalized (x, y) points")
        object.__setattr__(self, "points", points)


class RectangleMask(Mask):
    pass


class CircleMask(Mask):
    def __init__(self, radius, *, position=(0, 0)):
        radius = finite(radius, "radius", 0)
        super().__init__(radius * 2, radius * 2, position, "ellipse")


class ShapeMask(Mask):
    """A polygon in normalized [0,1] box coordinates."""

    def __init__(self, points, *, width, height, position=(0, 0)):
        super().__init__(width, height, position, "polygon", tuple(points))
        if any(not 0 <= v <= 1 for p in self.points for v in p):
            raise ValueError("ShapeMask coordinates must be within [0,1]")


def Wipe(component, *, direction="right"):
    from .animation import Animation, linear

    starts = {"right": (0, 0, 0, 1), "left": (1, 0, 1, 1), "down": (0, 0, 1, 0), "up": (0, 1, 1, 1)}
    if direction not in starts:
        raise ValueError("direction must be right, left, down, or up")
    return Animation(component, {"clip": (0, 0, 1, 1)}, {"clip": starts[direction]}, rate_func=linear)
