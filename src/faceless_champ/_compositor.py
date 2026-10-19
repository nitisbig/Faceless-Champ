"""Renderer-neutral local isolation; GPU nodes never cross the image boundary."""

import math

from PIL import Image, ImageChops, ImageDraw

from ._composition_plan import composition_plan, fit
from ._portable import guard_size
from ._render_state import component_ink_box, entry_geometry, ink_box, transformed_box
from .layout import Bounds, Group
from .motion import IDENTITY
from .surfaces import _shadow_padding
from .timeline import Scene, Sequence


def density(world):
    a, b, c, d, _, _ = world
    trace, det = a * a + b * b + c * c + d * d, (a * d - b * c) ** 2
    return max(0.001, math.sqrt((trace + math.sqrt(max(0, trace * trace - 4 * det))) / 2))


def mask_image(c, state, box, roi, q, size):
    # Coverage is sampled above output density even when renderer AA is one.
    output_size = size
    size = size[0] * 2, size[1] * 2
    guard_size(size)
    q *= 2
    mask = Image.new("L", size, 255)
    if c.mask is not None:
        mask.paste(0, (0, 0, *size))
        mx, my = state["mask_position"]
        if isinstance(c, Group):
            mx, my = mx + c._origin[0], my + c._origin[1]
        w, h = state["mask_width"], state["mask_height"]
        xy = (
            (mx - w / 2 - roi.left) * q,
            (my - h / 2 - roi.top) * q,
            (mx + w / 2 - roi.left) * q,
            (my + h / 2 - roi.top) * q,
        )
        if w > 0 and h > 0:
            draw = ImageDraw.Draw(mask)
            if c.mask.kind == "ellipse":
                draw.ellipse(xy, fill=255)
            elif c.mask.kind == "polygon":
                draw.polygon(
                    [
                        ((mx + (x - 0.5) * w - roi.left) * q, (my + (y - 0.5) * h - roi.top) * q)
                        for x, y in c.mask.points
                    ],
                    fill=255,
                )
            elif c.mask.kind == "path":
                from .backends._native import image_to_pillow, load_skia
                from .backends._skia_paint import path_data

                s = load_skia()
                surface = s.Surface(*size)
                path = c.mask.path.transformed(w * q, h * q, xy[0], xy[1])
                surface.getCanvas().drawPath(path_data(s, path), s.Paint(Color=s.ColorWHITE, AntiAlias=True))
                with image_to_pillow(surface.makeImageSnapshot(), s) as native:
                    mask.paste(native.getchannel("A"))
            else:
                draw.rectangle(xy, fill=255)
    if state["clip"] != (0, 0, 1, 1):
        l, t, r, b = state["clip"]
        clip = Image.new("L", size)
        if l < r and t < b:
            ImageDraw.Draw(clip).rectangle(
                (
                    (box.left + l * box.width - roi.left) * q,
                    (box.top + t * box.height - roi.top) * q,
                    (box.left + r * box.width - roi.left) * q,
                    (box.top + b * box.height - roi.top) * q,
                ),
                fill=255,
            )
        mask = ImageChops.multiply(mask, clip)
    out = Image.new("RGBA", size, "white")
    out.putalpha(mask)
    return out.resize(output_size, Image.Resampling.LANCZOS)


class Compositor:
    def __init__(self, device, raster, antialias=1):
        self.device, self.raster, self.antialias = device, raster, antialias

    def frame(self, node, time, size):
        if not math.isfinite(time):
            raise ValueError("Frame time must be finite")
        guard_size(size)
        big = size[0] * self.antialias, size[1] * self.antialias
        with self.device.surface(big) as target:
            self.node(target, node, time)
            return self.device.finish(target, size)

    def fitted(self, target, node, time, bg):
        self.device.clear(target, bg)
        fitted, (x, y) = fit(node.canvas, target.size)
        with self.device.surface(fitted) as inner:
            self.node(inner, node, time)
            self.device.blit(target, inner, Bounds(x, y, x + fitted[0], y + fitted[1]))

    def node(self, target, node, time):
        d = self.device
        d.clear(target, node.canvas.bg)
        if isinstance(node, Scene):
            node.build()
            q = min(target.size[0] / node.canvas.width, target.size[1] / node.canvas.height)
            self.raster_factor = q
            for entry in sorted((e for e in node.entries if e.parent is None), key=lambda e: e.component.z_index):
                self.visit(target, entry, time, (q, 0, 0, q, 0, 0), 1)
            return
        parts, progress = composition_plan(node, time, target.size)
        if progress is not None:
            with d.surface(target.size) as first, d.surface(target.size) as second:
                self.fitted(first, parts[0].node, parts[0].time, parts[0].background)
                self.fitted(second, parts[1].node, parts[1].time, parts[1].background)
                d.mix(target, first, second, progress, node.transition)
        else:
            for p in parts:
                x, y, w, h = p.viewport
                with d.surface((w, h)) as child:
                    self.fitted(child, p.node, p.time, p.background)
                    if isinstance(node, Sequence):
                        d.clear(target)
                    d.blit(target, child, Bounds(x, y, x + w, y + h))
        if getattr(node, "effects", None) is not None:
            q = min(target.size[0] / node.canvas.width, target.size[1] / node.canvas.height)
            d.content(target, node.effects, q, time)
            d.halos(target, node.effects, q)

    def leaf(self, target, c, state, box, world, opacity, age):
        d = self.device
        if d.component(target, c, state, box, world, opacity, age):
            return
        q = self.raster_factor if hasattr(c, "frame_key") else density(world)
        key = (
            c,
            tuple(
                (k, v)
                for k, v in state.items()
                if k not in {"position", "rotation", "scale", "scale_x", "scale_y", "opacity"}
            ),
            q,
            self.raster.renderer_age_key(c, age),
        )
        texture = getattr(d, "cached", lambda key: None)(key)
        if texture is None:
            guard_size((max(1, math.ceil(box.width * q)), max(1, math.ceil(box.height * q))))
            sprite = self.raster.sprite(c, state, q, age)
            texture = d.upload(sprite, key)
        try:
            d.blit(target, texture, box, world, opacity)
        finally:
            if hasattr(d, "release_upload"):
                d.release_upload(texture)

    def visit(self, target, entry, time, parent, inherited):
        c, state = entry.component, entry.state_at(time)
        if time < entry.start or (entry.end is not None and time >= entry.end) or state["opacity"] <= 0:
            return
        world, box = entry_geometry(entry, time, parent, self.raster)
        opacity, q = inherited * state["opacity"], density(world)
        effects = c.effects.evaluated(state) if c.effects is not None else None
        isolate = (
            effects is not None or c.mask is not None or state["clip"] != (0, 0, 1, 1) or c.drop_shadow is not None
        )
        if not isolate:
            if isinstance(c, Group):
                for child in sorted(entry.children, key=lambda e: e.component.z_index):
                    self.visit(target, child, time, world, opacity)
            else:
                self.leaf(target, c, state, box, world, opacity, max(0, time - entry.start))
            return
        if isinstance(c, Group):
            if c.drop_shadow:
                raise ValueError("Group shadows are unsupported; use a surface or leaf")
            children = [e for e in entry.children if e.start <= time and (e.end is None or time < e.end)]
            if not children:
                return
            boxes = [ink_box(child, time, IDENTITY, self.raster) for child in children]
            ink = Bounds(
                min(b.left for b in boxes),
                min(b.top for b in boxes),
                max(b.right for b in boxes),
                max(b.bottom for b in boxes),
            )
        else:
            ink = component_ink_box(c, box)
        pad = (effects.padding if effects else 0) + _shadow_padding(c.drop_shadow) + 2 / q
        roi = Bounds(ink.left - pad, ink.top - pad, ink.right + pad, ink.bottom + pad)
        projected = transformed_box(roi, world)
        if (
            projected.right < 0
            or projected.bottom < 0
            or projected.left > target.size[0]
            or projected.top > target.size[1]
        ):
            return
        size = max(1, math.ceil(roi.width * q)), max(1, math.ceil(roi.height * q))
        local = (q, 0, 0, q, -roi.left * q, -roi.top * q)
        d = self.device
        with d.surface(size) as layer:
            if isinstance(c, Group):
                for child in sorted(children, key=lambda e: e.component.z_index):
                    self.visit(layer, child, time, local, opacity)
            else:
                self.leaf(layer, c, state, box, local, 1, max(0, time - entry.start))
            d.content(
                layer,
                effects,
                q,
                max(0, time - entry.start),
                ((box.left - roi.left) * q, (box.top - roi.top) * q, box.width * q, box.height * q),
            )
            if c.mask is not None or state["clip"] != (0, 0, 1, 1):
                with mask_image(c, state, box, roi, q, size) as mask:
                    d.mask(layer, mask)
            # Both halos and the old shadow derive from the masked content, independently.
            if c.drop_shadow and effects and (effects.glow or effects.bloom):
                with d.surface(size) as content:
                    d.blit(content, layer, Bounds(0, 0, *size))
                    d.shadow(layer, c.drop_shadow, q, include_content=False)
                    d.halos(content, effects, q)
                    d.blit(layer, content, Bounds(0, 0, *size))
            else:
                d.halos(layer, effects, q)
                d.shadow(layer, c.drop_shadow, q)
            actual = Bounds(roi.left, roi.top, roi.left + size[0] / q, roi.top + size[1] / q)
            d.blit(target, layer, actual, world, 1 if isinstance(c, Group) else opacity)
