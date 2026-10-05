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
            fill=rgba(c.fill), stroke=rgba(c.stroke), width=c.width, height=c.height, stroke_width=c.stroke_width
        )
        if hasattr(c, "corner_radius"):
            state["corner_radius"] = c.corner_radius
    if isinstance(c, Text):
        state["color"] = rgba(c.color)
    if c.mask is not None:
        state.update(mask_position=c.mask.position, mask_width=c.mask.width, mask_height=c.mask.height)
    return state


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
