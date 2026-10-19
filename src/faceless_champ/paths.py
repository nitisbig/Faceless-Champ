"""Immutable Bézier geometry shared by native and portable raster backends."""

import math
from dataclasses import dataclass
from itertools import pairwise

from .components import Shape, finite


@dataclass(frozen=True)
class PathData:
    """Absolute commands: (M,x,y), (L,x,y), (Q,cx,cy,x,y), (C,...,x,y), (Z,).

    Fluent methods return a new description; no native handles or mutable builders
    enter scene snapshots. Coordinates are in authored design pixels.
    """

    commands: tuple = ()

    def __post_init__(self):
        from itertools import islice

        commands = tuple(islice(iter(self.commands), 10001))
        if len(commands) > 10000:
            raise ValueError("PathData supports at most 10000 commands")
        result, active = [], False
        for command in commands:
            command = tuple(command)
            if not command or command[0] not in {"M", "L", "Q", "C", "Z"}:
                raise ValueError("Path commands must be M, L, Q, C, or Z")
            op = command[0]
            if len(command) != {"M": 3, "L": 3, "Q": 5, "C": 7, "Z": 1}[op]:
                raise ValueError(f"Invalid {op} path command")
            if op != "M" and not active:
                raise ValueError("A path contour must start with M")
            values = tuple(finite(v, "path coordinate") for v in command[1:])
            if any(abs(v) > 1e9 for v in values):
                raise ValueError("Path coordinates must be within +/-1e9")
            result.append((op, *values))
            active = op != "Z"
        object.__setattr__(self, "commands", tuple(result))

    def move_to(self, x, y):
        return PathData((*self.commands, ("M", x, y)))

    def line_to(self, x, y):
        return PathData((*self.commands, ("L", x, y)))

    def quad_to(self, cx, cy, x, y):
        return PathData((*self.commands, ("Q", cx, cy, x, y)))

    def cubic_to(self, cx1, cy1, cx2, cy2, x, y):
        return PathData((*self.commands, ("C", cx1, cy1, cx2, cy2, x, y)))

    def close(self):
        return PathData((*self.commands, ("Z",)))

    def transformed(self, sx=1, sy=1, dx=0, dy=0):
        return PathData(
            tuple(
                (c[0], *(v * (sx if i % 2 == 0 else sy) + (dx if i % 2 == 0 else dy) for i, v in enumerate(c[1:])))
                for c in self.commands
            )
        )

    @property
    def bounds(self):
        """Tight curve bounds, including analytic quadratic/cubic extrema."""
        from .layout import Bounds

        points, current, start = [], (0, 0), (0, 0)
        for c in self.commands:
            op = c[0]
            if op == "M":
                current = start = c[1:]
                points.append(current)
            elif op == "Z":
                current = start
            else:
                controls = (current, *tuple(zip(c[1::2], c[2::2])))
                points.extend((current, controls[-1]))
                if op in {"Q", "C"}:
                    for axis in (0, 1):
                        v = [p[axis] for p in controls]
                        if op == "Q":
                            d = v[0] - 2 * v[1] + v[2]
                            roots = [(v[0] - v[1]) / d] if d else []
                        else:
                            a = -v[0] + 3 * v[1] - 3 * v[2] + v[3]
                            b = 2 * (v[0] - 2 * v[1] + v[2])
                            d = v[1] - v[0]
                            disc = b * b - 4 * a * d
                            roots = (
                                ([-d / b] if b else [])
                                if abs(a) < 1e-15
                                else (
                                    [(-b - math.sqrt(disc)) / (2 * a), (-b + math.sqrt(disc)) / (2 * a)]
                                    if disc >= 0
                                    else []
                                )
                            )
                        for t in roots:
                            if 0 < t < 1:
                                work = list(controls)
                                while len(work) > 1:
                                    work = [tuple(a + (b - a) * t for a, b in zip(p, q)) for p, q in pairwise(work)]
                                points.append(work[0])
                current = controls[-1]
        if not points:
            raise ValueError("PathData needs geometry")
        return Bounds(
            min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)
        )

    def flatten(self, tolerance=0.25):
        """Adaptive portable contours; tolerance is measured in these coordinates."""
        tolerance = finite(tolerance, "path tolerance", 1e-6)
        contours, contour, current, count = [], [], (0, 0), 0

        def append(p):
            nonlocal count
            count += 1
            if count > 65536:
                raise ValueError("Path flattening exceeds 65536 points")
            contour.append(p)

        def curve(points, depth=0):
            a, b = points[0], points[-1]
            distance = math.dist(a, b)
            error = max(
                (
                    abs((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) / distance
                    if distance
                    else math.dist(a, p)
                )
                for p in points[1:-1]
            )
            # Collinear reversals also need subdivision to retain arc length.
            excess = sum(math.dist(p, q) for p, q in pairwise(points)) - distance
            if depth >= 20 or max(error, excess) <= tolerance:
                append(b)
                return
            levels = [points]
            while len(levels[-1]) > 1:
                levels.append([tuple((x + y) / 2 for x, y in zip(p, q)) for p, q in zip(levels[-1], levels[-1][1:])])
            curve([level[0] for level in levels], depth + 1)
            curve([level[-1] for level in reversed(levels)], depth + 1)

        for c in self.commands:
            if c[0] == "M":
                if contour:
                    contours.append(tuple(contour))
                contour = []
                current = c[1:]
                append(current)
            elif c[0] == "Z":
                append(contour[0])
                current = contour[0]
            elif c[0] == "L":
                current = c[1:]
                append(current)
            else:
                controls = [current, *zip(c[1::2], c[2::2])]
                curve(controls)
                current = controls[-1]
        if contour:
            contours.append(tuple(contour))
        return tuple(contours)


class VectorPath(Shape):
    """A native Bézier Shape. Pillow supports one winding-rule contour.

    Geometry is normalized into its tight box, like Polyline. Explicit position
    replaces the default authored bounding-box center. Fill appears at Draw=1.
    """

    def __init__(self, path, *, fill_rule="winding", line_cap="butt", **kwargs):
        if not isinstance(path, PathData):
            path = PathData(path)
        if fill_rule not in {"winding", "even_odd"}:
            raise ValueError("fill_rule must be winding or even_odd")
        if line_cap not in {"butt", "round", "square"}:
            raise ValueError("line_cap must be butt, round, or square")
        if sum(c[0] in {"L", "Q", "C"} for c in path.commands) == 0:
            raise ValueError("VectorPath needs a drawable segment")
        box = path.bounds
        kwargs.setdefault("position", box.center)
        super().__init__(width=max(1, box.width), height=max(1, box.height), **kwargs)
        self.path = path.transformed(dx=-box.left, dy=-box.top)
        self.fill_rule, self.line_cap = fill_rule, line_cap

    @property
    def portable(self):
        return self.fill_rule == "winding" and sum(c[0] == "M" for c in self.path.commands) == 1
