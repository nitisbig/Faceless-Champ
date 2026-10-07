"""Immutable drawing recipes composed with public core shape APIs."""

import math
from dataclasses import dataclass

from faceless_champ import Arrow, Circle, Group, Polyline, Rectangle
from PIL import ImageColor

from ..diagnostics import KitError, number
from .base import BlockBuild


def _tuple(value, name):
    try:
        if isinstance(value, (str, bytes)):
            raise TypeError
        return tuple(value)
    except TypeError:
        raise KitError("WHITEBOARD_GEOMETRY", f"{name} must be a sequence") from None


def _point(value, name):
    value = _tuple(value, name)
    if len(value) != 2:
        raise KitError("WHITEBOARD_GEOMETRY", f"{name} requires two coordinates")
    return tuple(number(v, name) for v in value)


@dataclass(frozen=True, kw_only=True)
class _Stroke:
    color: str | None = None
    stroke_width: float = 5

    def __post_init__(self):
        object.__setattr__(self, "stroke_width", number(self.stroke_width, "stroke_width", positive=True))
        if self.color is not None:
            try:
                if not isinstance(self.color, str):
                    raise TypeError
                ImageColor.getcolor(self.color, "RGBA")
            except (ValueError, TypeError):
                raise KitError("WHITEBOARD_GEOMETRY", "color must be a valid color string") from None

    def _style(self, context):
        return {"stroke": self.color or context.theme.foreground, "stroke_width": self.stroke_width, "fill": None}


@dataclass(frozen=True)
class WhiteboardPath(_Stroke):
    points: tuple
    closed: bool = False

    def __post_init__(self):
        super().__post_init__()
        points = tuple(_point(p, "path point") for p in _tuple(self.points, "points"))
        object.__setattr__(self, "points", points)
        if not isinstance(self.closed, bool) or len(set(points)) < (3 if self.closed else 2):
            raise KitError("WHITEBOARD_GEOMETRY", "Paths need two distinct points, or three for a closed path")

    def _extent(self):
        xs, ys = zip(*self.points)
        return min(xs), min(ys), max(xs), max(ys)

    def _build(self, context):
        return Polyline(self.points, closed=self.closed, line_cap="round", **self._style(context))


@dataclass(frozen=True)
class WhiteboardLine(_Stroke):
    start: tuple
    end: tuple

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, "start", _point(self.start, "start"))
        object.__setattr__(self, "end", _point(self.end, "end"))
        if math.dist(self.start, self.end) < 1:
            raise KitError("WHITEBOARD_GEOMETRY", "Line endpoints must be at least one source unit apart")

    def _extent(self):
        return (*map(min, zip(self.start, self.end)), *map(max, zip(self.start, self.end)))

    def _build(self, context):
        return Polyline((self.start, self.end), line_cap="round", **self._style(context))


@dataclass(frozen=True)
class WhiteboardArrow(WhiteboardLine):
    tip_size: float = 18

    def __post_init__(self):
        super().__post_init__()
        tip = number(self.tip_size, "tip_size", minimum=1)
        if tip > math.dist(self.start, self.end):
            raise KitError("WHITEBOARD_GEOMETRY", "Arrow tip_size must fit its length")
        object.__setattr__(self, "tip_size", tip)

    def _build(self, context):
        return Arrow(self.start, self.end, tip_size=self.tip_size, **self._style(context))


@dataclass(frozen=True)
class WhiteboardRectangle(_Stroke):
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self):
        super().__post_init__()
        for name in ("x", "y", "width", "height"):
            object.__setattr__(
                self, name, number(getattr(self, name), name, minimum=1 if name in {"width", "height"} else 0)
            )

    def _extent(self):
        return self.x, self.y, self.x + self.width, self.y + self.height

    def _build(self, context):
        return Rectangle(
            width=self.width,
            height=self.height,
            position=(self.x + self.width / 2, self.y + self.height / 2),
            **self._style(context),
        )


@dataclass(frozen=True)
class WhiteboardCircle(_Stroke):
    center: tuple
    radius: float

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, "center", _point(self.center, "center"))
        object.__setattr__(self, "radius", number(self.radius, "radius", minimum=0.5))

    def _extent(self):
        x, y = self.center
        return x - self.radius, y - self.radius, x + self.radius, y + self.radius

    def _build(self, context):
        return Circle(self.radius, position=self.center, **self._style(context))


_DRAWINGS = (WhiteboardPath, WhiteboardLine, WhiteboardArrow, WhiteboardRectangle, WhiteboardCircle)


@dataclass(frozen=True)
class WhiteboardDrawing:
    """Ordered strokes in a fixed source viewbox; named children are stroke-0, stroke-1, ..."""

    drawings: tuple
    viewbox: tuple = (1000, 1000)

    def __post_init__(self):
        drawings = _tuple(self.drawings, "drawings")
        viewbox = _point(self.viewbox, "viewbox")
        if not drawings or min(viewbox) <= 0:
            raise KitError("WHITEBOARD_GEOMETRY", "Supply drawings and positive viewbox dimensions")
        for index, item in enumerate(drawings):
            if not isinstance(item, _DRAWINGS):
                raise KitError("WHITEBOARD_GEOMETRY", "Expected a whiteboard drawing specification", drawing=index)
            left, top, right, bottom = item._extent()
            if left < 0 or top < 0 or right > viewbox[0] or bottom > viewbox[1]:
                raise KitError("WHITEBOARD_GEOMETRY", "Geometry must lie inside its source viewbox", drawing=index)
        object.__setattr__(self, "drawings", drawings)
        object.__setattr__(self, "viewbox", viewbox)

    def compose(self, context, bounds):
        children = {}
        for index, item in enumerate(self.drawings):
            try:
                children[f"stroke-{index}"] = item._build(context)
            except (ValueError, TypeError) as exc:
                raise KitError("WHITEBOARD_GEOMETRY", str(exc), drawing=index) from exc
        root = Group(*children.values())
        measured = root.bounds
        # Include the entire viewbox, plus actual renderer padding (including rotated arrowheads).
        left, top = min(0, measured.left), min(0, measured.top)
        right, bottom = max(self.viewbox[0], measured.right), max(self.viewbox[1], measured.bottom)
        scale = min(bounds.width / (right - left), bounds.height / (bottom - top))
        if scale < 0.001:
            raise KitError("LAYOUT", "Whiteboard drawing area is too small for its viewbox")
        x, y = root.position
        root.scale = scale
        root.move_to(
            bounds.center[0] + (x - (left + right) / 2) * scale,
            bounds.center[1] + (y - (top + bottom) / 2) * scale,
        )
        return BlockBuild(root, children)
