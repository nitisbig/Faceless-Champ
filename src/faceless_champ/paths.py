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

    # ----- constructors -------------------------------------------------------
    @classmethod
    def from_svg(cls, d):
        """Parse an SVG path ``d`` string (M L H V C S Q T A Z, absolute or relative)."""
        return cls(_parse_svg_path(d))

    @classmethod
    def rect(cls, x, y, width, height, radius=0):
        """Rectangle with top-left (x, y); optional rounded corners."""
        r = min(finite(radius, "radius", 0), width / 2, height / 2)
        if not r:
            return cls((("M", x, y), ("L", x + width, y), ("L", x + width, y + height), ("L", x, y + height), ("Z",)))
        k = r * 0.5522847498
        right, bottom = x + width, y + height
        return cls(
            (
                ("M", x + r, y),
                ("L", right - r, y),
                ("C", right - r + k, y, right, y + r - k, right, y + r),
                ("L", right, bottom - r),
                ("C", right, bottom - r + k, right - r + k, bottom, right - r, bottom),
                ("L", x + r, bottom),
                ("C", x + r - k, bottom, x, bottom - r + k, x, bottom - r),
                ("L", x, y + r),
                ("C", x, y + r - k, x + r - k, y, x + r, y),
                ("Z",),
            )
        )

    @classmethod
    def ellipse(cls, cx, cy, rx, ry=None):
        """Ellipse (or circle when ``ry`` is omitted) from four cubic arcs, starting at the top."""
        ry = rx if ry is None else ry
        kx, ky = rx * 0.5522847498, ry * 0.5522847498
        return cls(
            (
                ("M", cx, cy - ry),
                ("C", cx + kx, cy - ry, cx + rx, cy - ky, cx + rx, cy),
                ("C", cx + rx, cy + ky, cx + kx, cy + ry, cx, cy + ry),
                ("C", cx - kx, cy + ry, cx - rx, cy + ky, cx - rx, cy),
                ("C", cx - rx, cy - ky, cx - kx, cy - ry, cx, cy - ry),
                ("Z",),
            )
        )

    @classmethod
    def polygon(cls, points, closed=True):
        points = list(points)
        if len(points) < 2:
            raise ValueError("polygon needs at least two points")
        commands = [("M", *points[0]), *(("L", *p) for p in points[1:])]
        return cls((*commands, ("Z",)) if closed else tuple(commands))

    @classmethod
    def star(cls, cx, cy, outer, inner, points=5, rotation=-90):
        """Star with ``points`` tips; ``rotation`` in degrees (-90 puts a tip on top)."""
        count = int(points)
        if count < 2:
            raise ValueError("star needs at least two points")
        vertices = []
        for i in range(count * 2):
            radius = outer if i % 2 == 0 else inner
            angle = math.radians(rotation + i * 180 / count)
            vertices.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        return cls.polygon(vertices)

    @classmethod
    def from_text(cls, text, *, font=None, font_size=96, weight=None, x=0, y=0, tracking=0):
        """Glyph outlines of single-line ``text`` (baseline at y). Needs skia-python.

        Combine with VectorPath + Draw/Trace to "write" a word stroke by stroke, or
        use it as a PathMask to show footage through letters.
        """
        from .backends._native import load_skia
        from .typography import resolve_font

        s = load_skia()
        path, _ = resolve_font(font, text, weight)
        from .typography import DEFAULT_FONT

        typeface = s.Typeface.MakeFromFile(str(path or DEFAULT_FONT))
        if typeface is None:
            raise ValueError(f"Cannot load font {path}")
        skfont = s.Font(typeface, finite(font_size, "font_size", 1))
        glyphs = skfont.textToGlyphs(text)
        positions = skfont.getXPos(glyphs)
        track = finite(tracking, "tracking") * font_size
        combined = s.Path()
        for index, (glyph, gx) in enumerate(zip(glyphs, positions)):
            outline = skfont.getPath(glyph)
            if outline is not None and outline.countVerbs():
                combined.addPath(outline, x + gx + index * track, y)
        if not combined.countVerbs():
            raise ValueError("text has no visible glyph outlines")
        return _from_skia(s, combined)

    # ----- boolean operations (Skia PathOps) ----------------------------------
    def _op(self, other, op):
        from .backends._native import load_skia

        s = load_skia()
        if not isinstance(other, PathData):
            other = PathData(other)
        result = s.Op(_to_skia(s, self), _to_skia(s, other), getattr(s.PathOp, op))
        if result is None:
            raise ValueError("Path boolean operation failed")
        return _from_skia(s, result)

    def union(self, other):
        return self._op(other, "kUnion_PathOp")

    def intersection(self, other):
        return self._op(other, "kIntersect_PathOp")

    def difference(self, other):
        """This shape minus ``other``."""
        return self._op(other, "kDifference_PathOp")

    def xor(self, other):
        return self._op(other, "kXOR_PathOp")

    __or__, __and__, __sub__, __xor__ = union, intersection, difference, xor

    def to_svg(self):
        """Serialize as an SVG path ``d`` string."""
        return " ".join(c[0] + ("" if len(c) == 1 else " " + " ".join(f"{v:g}" for v in c[1:])) for c in self.commands)

    def affine(self, a, b, c, d, e, f):
        """Apply the affine map (x, y) -> (a x + c y + e, b x + d y + f) (SVG matrix order)."""

        def mapped(values):
            out = []
            for x, y in zip(values[0::2], values[1::2]):
                out += [a * x + c * y + e, b * x + d * y + f]
            return out

        return PathData(tuple((cmd[0], *mapped(cmd[1:])) for cmd in self.commands))

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


# ----- native conversion and SVG parsing helpers --------------------------------


def _to_skia(s, data):
    from .backends._skia_paint import path_data

    return path_data(s, data)


def _from_skia(s, path):
    """Convert a skia.Path to PathData; conics become quadratics."""
    verbs = s.Path.Verb
    commands = []
    iterator = s.Path.Iter(path, False)
    while True:
        verb, points = iterator.next()
        if verb == verbs.kDone_Verb:
            break
        if verb == verbs.kMove_Verb:
            commands.append(("M", points[0].x(), points[0].y()))
        elif verb == verbs.kLine_Verb:
            commands.append(("L", points[1].x(), points[1].y()))
        elif verb == verbs.kQuad_Verb:
            commands.append(("Q", points[1].x(), points[1].y(), points[2].x(), points[2].y()))
        elif verb == verbs.kCubic_Verb:
            commands.append(
                ("C", points[1].x(), points[1].y(), points[2].x(), points[2].y(), points[3].x(), points[3].y())
            )
        elif verb == verbs.kConic_Verb:
            quads = s.Path.ConvertConicToQuads(points[0], points[1], points[2], iterator.conicWeight(), 2)
            for i in range(1, len(quads) - 1, 2):
                commands.append(("Q", quads[i].x(), quads[i].y(), quads[i + 1].x(), quads[i + 1].y()))
        elif verb == verbs.kClose_Verb and commands and commands[-1][0] != "Z":
            commands.append(("Z",))
    if not commands:
        raise ValueError("Path operation produced empty geometry")
    return PathData(tuple(commands))


_SVG_TOKEN = None


def _svg_tokens(d):
    import re

    global _SVG_TOKEN
    if _SVG_TOKEN is None:
        _SVG_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
    return _SVG_TOKEN.findall(d)


def _arc_to_cubics(x1, y1, rx, ry, phi, large, sweep, x2, y2):
    """SVG elliptical arc (endpoint form) as cubic Bézier commands."""
    if (x1, y1) == (x2, y2):
        return []
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0:
        return [("L", x2, y2)]
    cos_p, sin_p = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cos_p * dx + sin_p * dy, -sin_p * dx + cos_p * dy
    scale = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if scale > 1:
        rx, ry = rx * math.sqrt(scale), ry * math.sqrt(scale)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    coef = math.sqrt(max(0, num / den)) if den else 0
    if large == sweep:
        coef = -coef
    cxp, cyp = coef * rx * y1p / ry, -coef * ry * x1p / rx
    cx = cos_p * cxp - sin_p * cyp + (x1 + x2) / 2
    cy = sin_p * cxp + cos_p * cyp + (y1 + y2) / 2

    def angle(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a

    theta = angle(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    delta = angle((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and delta > 0:
        delta -= math.tau
    elif sweep and delta < 0:
        delta += math.tau
    segments = max(1, math.ceil(abs(delta) / (math.pi / 2)))
    step = delta / segments
    k = 4 / 3 * math.tan(step / 4)

    def point(t):
        x, y = rx * math.cos(t), ry * math.sin(t)
        return cos_p * x - sin_p * y + cx, sin_p * x + cos_p * y + cy

    def derivative(t):
        x, y = -rx * math.sin(t), ry * math.cos(t)
        return cos_p * x - sin_p * y, sin_p * x + cos_p * y

    out = []
    for i in range(segments):
        t1, t2 = theta + i * step, theta + (i + 1) * step
        p1, p2 = point(t1), point(t2)
        d1, d2 = derivative(t1), derivative(t2)
        out.append(
            (
                "C",
                p1[0] + k * d1[0],
                p1[1] + k * d1[1],
                p2[0] - k * d2[0],
                p2[1] - k * d2[1],
                *(p2 if i < segments - 1 else (x2, y2)),
            )
        )
    return out


def _parse_svg_path(d):
    if not isinstance(d, str):
        raise TypeError("SVG path data must be a string")
    tokens = _svg_tokens(d)
    counts = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}
    out, i, cmd = [], 0, None
    x = y = sx = sy = 0.0
    last_control, last_cmd = None, None
    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
        elif cmd is None:
            raise ValueError("SVG path must start with a command")
        upper, rel = cmd.upper(), cmd.islower()
        n = counts[upper]
        if upper == "Z":
            out.append(("Z",))
            x, y = sx, sy
            last_control, last_cmd = None, "Z"
            continue
        args = tokens[i : i + n]
        if len(args) < n or any(a.isalpha() for a in args):
            raise ValueError(f"SVG path command {cmd} has too few numbers")
        v = [float(a) for a in args]
        i += n
        ox, oy = (x, y) if rel else (0.0, 0.0)
        if upper == "M":
            x, y = v[0] + ox, v[1] + oy
            sx, sy = x, y
            out.append(("M", x, y))
            cmd = "l" if rel else "L"  # implicit lineto after moveto
            last_control = None
        elif upper == "L":
            x, y = v[0] + ox, v[1] + oy
            out.append(("L", x, y))
            last_control = None
        elif upper == "H":
            x = v[0] + (x if rel else 0)
            out.append(("L", x, y))
            last_control = None
        elif upper == "V":
            y = v[0] + (y if rel else 0)
            out.append(("L", x, y))
            last_control = None
        elif upper in {"C", "S"}:
            if upper == "C":
                c1 = (v[0] + ox, v[1] + oy)
                c2, end = (v[2] + ox, v[3] + oy), (v[4] + ox, v[5] + oy)
            else:
                c1 = (2 * x - last_control[0], 2 * y - last_control[1]) if last_cmd in {"C", "S"} else (x, y)
                c2, end = (v[0] + ox, v[1] + oy), (v[2] + ox, v[3] + oy)
            out.append(("C", *c1, *c2, *end))
            last_control, (x, y) = c2, end
        elif upper in {"Q", "T"}:
            if upper == "Q":
                c, end = (v[0] + ox, v[1] + oy), (v[2] + ox, v[3] + oy)
            else:
                c = (2 * x - last_control[0], 2 * y - last_control[1]) if last_cmd in {"Q", "T"} else (x, y)
                end = (v[0] + ox, v[1] + oy)
            out.append(("Q", *c, *end))
            last_control, (x, y) = c, end
        elif upper == "A":
            end = (v[5] + ox, v[6] + oy)
            out.extend(_arc_to_cubics(x, y, v[0], v[1], v[2], bool(v[3]), bool(v[4]), *end))
            x, y = end
            last_control = None
        last_cmd = upper
    if not out:
        raise ValueError("SVG path is empty")
    return tuple(out)
