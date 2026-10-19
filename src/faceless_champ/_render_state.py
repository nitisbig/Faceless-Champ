"""Shared composition timing and geometry; no optional rendering dependencies."""

import math
from collections import OrderedDict
from copy import copy

from PIL import Image

from .components import Arrow, Shape, Text
from .layout import Bounds, Group
from .motion import matrix, multiply, point, style_value


def evaluated(entry, time):
    view = copy(entry.component)
    for key, value in entry.state_at(time).items():
        if hasattr(view, key):
            setattr(view, key, style_value(key, value))
    if isinstance(view, Group):
        view._children = tuple(evaluated(child, time) for child in entry.children)
    return view


def component_size(c, state, raster, age):
    from .surfaces import Surface

    if isinstance(c, Surface):
        return c.width, c.height
    if isinstance(c, Shape):
        sw = max(1, round(state["stroke_width"]))
        if isinstance(c, Arrow):
            pad = math.ceil(c.tip_size + sw)
            return math.ceil(state["width"]) + 2 * pad + 1, 2 * pad + 1
        return max(1, round(state["width"])) + 2 * sw, max(1, round(state["height"])) + 2 * sw
    if isinstance(c, Text) and c.text_engine == "skia":
        return raster.native_text_size(c, state)
    if not isinstance(c, Text) and hasattr(c, "width") and hasattr(c, "height"):
        return max(1, round(c.width)), max(1, round(c.height))
    return raster.sprite(c, state, 1, age).size


def entry_geometry(entry, time, parent, raster):
    c, state = entry.component, entry.state_at(time)
    if isinstance(c, Group):
        boxes = [evaluated(child, time).bounds for child in entry.children]
        box = Bounds(
            min(b.left for b in boxes),
            min(b.top for b in boxes),
            max(b.right for b in boxes),
            max(b.bottom for b in boxes),
        )
        return multiply(parent, matrix(state, c._origin)), box
    w, h = component_size(c, state, raster, max(0, time - entry.start))
    local = dict(state)
    if c.anchor == "top_left":
        local["position"] = (
            state["position"][0] + w * state["scale"] * state["scale_x"] / 2,
            state["position"][1] + h * state["scale"] * state["scale_y"] / 2,
        )
    return multiply(parent, matrix(local)), Bounds(-w / 2, -h / 2, w / 2, h / 2)


def transformed_box(box, world):
    points = [
        point(world, x, y)
        for x, y in ((box.left, box.top), (box.right, box.top), (box.right, box.bottom), (box.left, box.bottom))
    ]
    return Bounds(
        min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)
    )


def ink_box(entry, time, parent, raster):
    from .surfaces import _shadow_padding

    c = entry.component
    world, box = entry_geometry(entry, time, parent, raster)
    if isinstance(c, Group):
        boxes = [ink_box(child, time, world, raster) for child in entry.children]
        return Bounds(
            min(b.left for b in boxes),
            min(b.top for b in boxes),
            max(b.right for b in boxes),
            max(b.bottom for b in boxes),
        )
    pad = _shadow_padding(c.drop_shadow)
    return transformed_box(Bounds(box.left - pad, box.top - pad, box.right + pad, box.bottom + pad), world)


def composition_frame(renderer, node, time, size):
    """Preserve existing fitting, straight-RGBA crossfade and source-clock rules."""
    from .timeline import Grid, Layer, Sequence

    background = Image.new("RGBA", size, node.canvas.bg)
    if isinstance(node, Sequence):
        starts = node.starts
        active = [i for i, (s, c) in enumerate(zip(starts, node.children)) if s <= time < s + c.duration]
        if not active and time >= node.duration:
            active = [len(node.children) - 1]
        if not active:
            return background
        i = active[0]
        first = fit_frame(renderer, node.children[i], time - starts[i], size, node.canvas.bg)
        if len(active) == 2:
            j = active[1]
            second = fit_frame(renderer, node.children[j], time - starts[j], size, node.canvas.bg)
            return Image.blend(first, second, min(1, (time - starts[j]) / node.crossfade))
        return first
    if isinstance(node, Grid):
        sx, sy = size[0] / node.canvas.width, size[1] / node.canvas.height
        top, right_pad, bottom_pad, left = node.padding
        cw = (node.canvas.width - left - right_pad - node.gap * (node.columns - 1)) / node.columns
        ch = (node.canvas.height - top - bottom_pad - node.gap * (node.rows - 1)) / node.rows
        for i, (start, child) in enumerate(zip(node.start_times, node.children)):
            if time < start:
                continue
            col, row = i % node.columns, i // node.columns
            x, y = round((left + col * (cw + node.gap)) * sx), round((top + row * (ch + node.gap)) * sy)
            right, bottom = (
                round((left + col * (cw + node.gap) + cw) * sx),
                round((top + row * (ch + node.gap) + ch) * sy),
            )
            cell = fit_frame(
                renderer,
                child,
                min(time - start, child.duration),
                (max(1, right - x), max(1, bottom - y)),
                node.canvas.bg,
            )
            background.alpha_composite(cell, (x, y))
        return background
    if isinstance(node, Layer):
        for child in node.children:
            background.alpha_composite(fit_frame(renderer, child, min(time, child.duration), size, "#00000000"))
        return background
    raise TypeError(f"Unsupported renderable: {type(node).__name__}")


def fit_frame(renderer, node, time, size, bg):
    ratio = min(size[0] / node.canvas.width, size[1] / node.canvas.height)
    fitted = (max(1, round(node.canvas.width * ratio)), max(1, round(node.canvas.height * ratio)))
    result = Image.new("RGBA", size, bg)
    result.alpha_composite(renderer.frame(node, time, fitted), ((size[0] - fitted[0]) // 2, (size[1] - fitted[1]) // 2))
    return result


class ByteCache:
    """Renderer-owned LRU; oversized values are returned but never retained."""

    def __init__(self, limit):
        self.limit = limit
        self.bytes = 0
        self.items = OrderedDict()

    def get(self, key):
        item = self.items.get(key)
        if item is not None:
            self.items.move_to_end(key)
            return item[0]

    def put(self, key, value, cost):
        old = self.items.pop(key, None)
        if old:
            self.bytes -= old[1]
        if cost <= self.limit:
            while self.bytes + cost > self.limit:
                _, (_, removed) = self.items.popitem(last=False)
                self.bytes -= removed
            self.items[key] = (value, cost)
            self.bytes += cost
        return value

    def clear(self):
        self.items.clear()
        self.bytes = 0
