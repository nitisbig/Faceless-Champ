"""Visual property snapshots and affine math, without optional dependencies."""

import math

from PIL import ImageColor


def rgba(value):
    if value is None:
        return (0, 0, 0, 0)
    if isinstance(value, str):
        return ImageColor.getcolor(value, "RGBA")
    value = tuple(value)
    if len(value) != 4 or any(not math.isfinite(v) or not 0 <= v <= 255 for v in value):
        raise ValueError("Colors require four channels in [0,255]")
    return value


def visual_state(c):
    from .components import Shape, Text

    state = {"clip": (0, 0, 1, 1)}
    if isinstance(c, Shape):
        state.update(
            fill=paint_state(c.fill), stroke=rgba(c.stroke), width=c.width, height=c.height, stroke_width=c.stroke_width
        )
        if hasattr(c, "corner_radius"):
            state["corner_radius"] = c.corner_radius
        state.update(
            trim_start=getattr(c, "trim_start", 0),
            trim_offset=getattr(c, "trim_offset", 0),
            dash_offset=getattr(c, "dash_offset", 0),
        )
    if isinstance(c, Text):
        state["color"] = rgba(c.color)
    if c.mask is not None:
        state.update(mask_position=c.mask.position, mask_width=c.mask.width, mask_height=c.mask.height)
    return state


def paint_state(value):
    from .gradients import LinearGradient, RadialGradient

    return value if isinstance(value, (LinearGradient, RadialGradient)) else rgba(value)


def style_value(key, value):
    """Restore evaluated style without interpreting immutable paints as tuples."""
    return tuple(round(v) for v in value) if key in {"fill", "stroke", "color"} and isinstance(value, tuple) else value


IDENTITY = (1, 0, 0, 1, 0, 0)


def multiply(a, b):
    aa, ab, ac, ad, ax, ay = a
    ba, bb, bc, bd, bx, by = b
    return (
        aa * ba + ac * bb,
        ab * ba + ad * bb,
        aa * bc + ac * bd,
        ab * bc + ad * bd,
        aa * bx + ac * by + ax,
        ab * bx + ad * by + ay,
    )


def point(m, x, y):
    a, b, c, d, tx, ty = m
    return a * x + c * y + tx, b * x + d * y + ty


def matrix(state, origin=(0, 0)):
    angle = math.radians(state["rotation"])
    sx, sy = state["scale"] * state["scale_x"], state["scale"] * state["scale_y"]
    a, b, c, d = math.cos(angle) * sx, math.sin(angle) * sx, -math.sin(angle) * sy, math.cos(angle) * sy
    x, y = state["position"]
    ox, oy = origin
    return a, b, c, d, x - a * ox - c * oy, y - b * ox - d * oy


def inverse(m):
    a, b, c, d, x, y = m
    det = a * d - b * c
    return d / det, -c / det, (c * y - d * x) / det, -b / det, a / det, (b * x - a * y) / det


def tilted(c, state):
    """True when a component has an active 2.5D tilt."""
    return getattr(c, "perspective", None) is not None and bool(state.get("tilt_x", 0) or state.get("tilt_y", 0))


def perspective_matrix(tilt_x, tilt_y, distance, cx, cy):
    """Row-major 3x3 projective matrix: rotate the z=0 plane about (cx, cy) by
    tilt_x (around x) then tilt_y (around y) and project it from ``distance``."""
    a, b = math.radians(tilt_x), math.radians(tilt_y)
    ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
    # R = Ry(b) @ Rx(a); x' = (r00 x + r01 y) / w, y' = (r10 x + r11 y) / w, w = 1 + (r20 x + r21 y) / d
    m = ((cb, sb * sa, 0.0), (0.0, ca, 0.0), (-sb / distance, cb * sa / distance, 1.0))
    t = ((1, 0, cx), (0, 1, cy), (0, 0, 1))
    u = ((1, 0, -cx), (0, 1, -cy), (0, 0, 1))
    return _mat3(_mat3(t, m), u)


def _mat3(p, q):
    return tuple(tuple(sum(p[i][k] * q[k][j] for k in range(3)) for j in range(3)) for i in range(3))


def inverse3(m):
    (a, b, c), (d, e, f), (g, h, i) = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    return (
        ((e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det),
        ((f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det),
        ((d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det),
    )
