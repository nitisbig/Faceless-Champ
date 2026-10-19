"""Optional CPU Skia compositor, with native vectors and existing raster leaves."""

import math
import time as clock
from contextlib import contextmanager

from PIL import Image as PILImage

from .._portable import guard_size
from .._render_state import ByteCache, composition_frame, entry_geometry, ink_box, transformed_box
from ..components import Image, Shape, Text, finite
from ..layout import Bounds, Group
from ..subtitles import Captions
from ..surfaces import Surface, _shadow_padding
from ..timeline import Scene
from ._native import image_from_pillow, image_to_pillow, load_skia
from ._raster_adapter import PillowRasterAdapter
from ._skia_paint import color, draw_shape, draw_surface, path_data
from ._skia_text import TextSession


class SkiaRenderer:
    """Deterministic CPU renderer. Internally premultiplied sRGB, externally RGBA.

    antialias retains the Pillow supersampling meaning; use 1 for native edge AA.
    Frame/native caches are byte bounded; local working surfaces have a separate
    allocation budget. Each instance owns its fonts, caches and raster sessions.
    """

    def __init__(self, antialias=1, *, frame_cache_mb=64, native_cache_mb=64, working_mb=256, arch_session_limit=4):
        if antialias not in (1, 2, 3, 4):
            raise ValueError("antialias must be 1, 2, 3, or 4")
        self.skia = load_skia()
        self._closed = False
        self.antialias = antialias
        self.frames = ByteCache(round(finite(frame_cache_mb, "frame_cache_mb", 0) * 1024**2))
        self.images = ByteCache(round(finite(native_cache_mb, "native_cache_mb", 0) * 1024**2))
        self.working_limit = round(finite(working_mb, "working_mb", 1) * 1024**2)
        self.working_bytes = 0
        self.raster = PillowRasterAdapter(native_cache_mb, arch_session_limit)
        self.text = TextSession()
        self.raster.text_session = self.text
        self.stats = {
            "native_leaves": 0,
            "raster_leaves": 0,
            "frame_cache_hits": 0,
            "conversion_seconds": 0.0,
            "raster_seconds": 0.0,
        }

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        self._closed = True
        self.frames.clear()
        self.images.clear()
        self.text.close()
        self.raster.close()

    def validate(self, node):
        if self._closed:
            raise RuntimeError("SkiaRenderer is closed")
        self.raster.renderer.validate(node, backend="skia")

    @contextmanager
    def _surface(self, size):
        guard_size(size)
        cost = size[0] * size[1] * 4
        if self.working_bytes + cost > self.working_limit:
            raise ValueError("Skia local surfaces exceed working_mb; reduce dimensions, AA, scale or effect bounds")
        s = self.skia
        info = s.ImageInfo.Make(
            *size, s.ColorType.kRGBA_8888_ColorType, s.AlphaType.kPremul_AlphaType, s.ColorSpace.MakeSRGB()
        )
        surface = s.Surface.MakeRaster(info)
        if surface is None:
            raise RuntimeError("Skia could not allocate raster surface")
        self.working_bytes += cost
        try:
            yield surface
        finally:
            self.working_bytes -= cost

    def _matrix(self, world):
        a, b, c, d, x, y = world
        return self.skia.Matrix.MakeAll(a, c, x, b, d, y, 0, 0, 1)

    def _age_key(self, c, age):
        if hasattr(c, "frame_key"):
            return c.frame_key(age)
        if isinstance(c, Captions):
            return self.raster.renderer._caption_state(c, age)
        if isinstance(c, Image):
            frames, durations = self.raster.renderer._image(c)
            if len(frames) > 1:
                clock = age % sum(durations)
                for i, duration in enumerate(durations):
                    if clock < duration:
                        return i
                    clock -= duration
        return None

    def frame(self, node, time, size):
        if self._closed:
            raise RuntimeError("SkiaRenderer is closed")
        if not math.isfinite(time):
            raise ValueError("Frame time must be finite")
        if len(size) != 2:
            raise ValueError("Frame size needs width and height")
        guard_size(size)
        from ..effects import needs_compositor

        if needs_compositor(node):
            # The shared CPU reference uses existing Skia typography/path tiles.
            self.raster.renderer.antialias = self.antialias
            return self.raster.renderer.frame(node, time, size)
        if not isinstance(node, Scene):
            return composition_frame(self, node, time, size)
        node.build()
        signature = (
            node.canvas,
            size,
            tuple(
                (
                    e.component,
                    e.start,
                    e.end,
                    e.start <= time and (e.end is None or time < e.end),
                    tuple(e.state_at(time).items()),
                    self._age_key(e.component, max(0, time - e.start)),
                )
                for e in node.entries
            ),
        )
        cached = self.frames.get(node)
        if cached is not None and cached[0] == signature:
            self.stats["frame_cache_hits"] += 1
            return cached[1].copy()
        big = size[0] * self.antialias, size[1] * self.antialias
        factor = min(big[0] / node.canvas.width, big[1] / node.canvas.height)
        self._raster_factor = factor
        with self._surface(big) as surface:
            canvas = surface.getCanvas()
            canvas.clear(color(self.skia, node.canvas.bg))
            limit = Bounds(0, 0, *big)
            for entry in sorted((e for e in node.entries if e.parent is None), key=lambda e: e.component.z_index):
                self._visit(canvas, entry, time, (factor, 0, 0, factor, 0, 0), 1, limit)
            started = clock.perf_counter()
            result = image_to_pillow(surface.makeImageSnapshot(), self.skia)
            self.stats["conversion_seconds"] += clock.perf_counter() - started
        if self.antialias > 1:
            result = result.resize(size, PILImage.Resampling.LANCZOS)
        cost = size[0] * size[1] * 4
        if cost <= self.frames.limit:
            self.frames.put(node, (signature, result.copy()), cost)
        return result

    def _ink_box(self, entry, time, parent):
        return ink_box(entry, time, parent, self.raster)

    @staticmethod
    def _clip_box(c, state, box):
        l, t, r, b = state["clip"]
        left, top, right, bottom = (
            box.left + l * box.width,
            box.top + t * box.height,
            box.left + r * box.width,
            box.top + b * box.height,
        )
        if c.mask is not None:
            origin = c._origin if isinstance(c, Group) else (0, 0)
            x, y = state["mask_position"][0] + origin[0], state["mask_position"][1] + origin[1]
            w, h = state["mask_width"], state["mask_height"]
            left, top, right, bottom = (
                max(left, x - w / 2),
                max(top, y - h / 2),
                min(right, x + w / 2),
                min(bottom, y + h / 2),
            )
        return Bounds(left, top, right, bottom) if left < right and top < bottom else None

    def _mask_path(self, c, state, box):
        s = self.skia
        b = s.PathBuilder()
        mask = c.mask
        center = c._origin if isinstance(c, Group) else (0, 0)
        if mask is not None:
            w, h = state["mask_width"], state["mask_height"]
            x, y = state["mask_position"][0] + center[0], state["mask_position"][1] + center[1]
            if w == 0 or h == 0:
                return b.detach()
            rect = s.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h)
            if mask.kind == "ellipse":
                b.addOval(rect)
            elif mask.kind == "path":
                return path_data(s, mask.path.transformed(w, h, x - w / 2, y - h / 2))
            elif mask.kind == "polygon":
                pts = [(x + (px - 0.5) * w, y + (py - 0.5) * h) for px, py in mask.points]
                b.moveTo(*pts[0])
                for p in pts[1:]:
                    b.lineTo(*p)
                b.close()
            else:
                b.addRect(rect)
        return b.detach()

    def _apply_mask(self, surface, c, state, box, world, offset=(0, 0)):
        s = self.skia
        size = surface.width(), surface.height()
        with self._surface(size) as mask:
            canvas = mask.getCanvas()
            canvas.translate(-offset[0], -offset[1])
            canvas.concat(self._matrix(world))
            if c.mask is not None:
                canvas.clipPath(self._mask_path(c, state, box), doAntiAlias=True)
            l, t, r, b = state["clip"]
            rect = s.Rect.MakeLTRB(
                box.left + l * box.width, box.top + t * box.height, box.left + r * box.width, box.top + b * box.height
            )
            canvas.drawRect(rect, s.Paint(AntiAlias=True, Color=s.ColorWHITE))
            surface.getCanvas().drawImage(
                mask.makeImageSnapshot(), 0, 0, s.SamplingOptions(), s.Paint(BlendMode=s.BlendMode.kDstIn)
            )

    def _visit(self, canvas, entry, time, parent, inherited, limit):
        c, state = entry.component, entry.state_at(time)
        if time < entry.start or (entry.end is not None and time >= entry.end) or state["opacity"] <= 0:
            return
        world, box = entry_geometry(entry, time, parent, self.raster)
        opacity = inherited * state["opacity"]
        if isinstance(c, Group):
            if c.drop_shadow is not None:
                raise ValueError("Group shadows are unsupported; use a surface or leaf")
            if c.mask is None and state["clip"] == (0, 0, 1, 1):
                for child in sorted(entry.children, key=lambda e: e.component.z_index):
                    self._visit(canvas, child, time, world, opacity, limit)
                return
            ink = self._ink_box(entry, time, parent)
            clipped = self._clip_box(c, state, box)
            if clipped is None:
                return
            clip = transformed_box(clipped, world)
            if ink.right <= clip.left or ink.left >= clip.right or ink.bottom <= clip.top or ink.top >= clip.bottom:
                return
            ink = Bounds(
                max(ink.left, clip.left),
                max(ink.top, clip.top),
                min(ink.right, clip.right),
                min(ink.bottom, clip.bottom),
            )
            left, top = (
                max(math.floor(ink.left) - 1, math.floor(limit.left)),
                max(math.floor(ink.top) - 1, math.floor(limit.top)),
            )
            right, bottom = (
                min(math.ceil(ink.right) + 1, math.ceil(limit.right)),
                min(math.ceil(ink.bottom) + 1, math.ceil(limit.bottom)),
            )
            if right <= left or bottom <= top:
                return
            roi = Bounds(left, top, right, bottom)
            with self._surface((right - left, bottom - top)) as layer:
                target = layer.getCanvas()
                target.translate(-left, -top)
                for child in sorted(entry.children, key=lambda e: e.component.z_index):
                    self._visit(target, child, time, world, opacity, roi)
                self._apply_mask(layer, c, state, box, world, (left, top))
                canvas.drawImage(layer.makeImageSnapshot(), left, top)
            return
        if c.drop_shadow or c.mask or state["clip"] != (0, 0, 1, 1) or (isinstance(c, Surface) and c.surface_shadow):
            ink = self._ink_box(entry, time, parent)
            if ink.right < limit.left or ink.left > limit.right or ink.bottom < limit.top or ink.top > limit.bottom:
                return
            self._isolated_leaf(canvas, c, state, box, world, max(0, time - entry.start), opacity)
            return
        canvas.save()
        canvas.concat(self._matrix(world))
        self._draw_leaf(canvas, c, state, box, max(0, time - entry.start), self._density(world), opacity)
        canvas.restore()

    @staticmethod
    def _density(world):
        a, b, c, d, _, _ = world
        # Largest singular value includes shear from nested nonuniform transforms.
        trace = a * a + b * b + c * c + d * d
        det = (a * d - b * c) ** 2
        return max(0.001, math.sqrt((trace + math.sqrt(max(0, trace * trace - 4 * det))) / 2))

    def _draw_leaf(self, canvas, c, state, box, age, density, opacity):
        s = self.skia
        if isinstance(c, Shape):
            self.stats["native_leaves"] += 1
            draw_shape(s, canvas, c, state, opacity)
        elif isinstance(c, Surface):
            self.stats["native_leaves"] += 1
            draw_surface(s, canvas, c, opacity)
        elif isinstance(c, Text) and c.text_engine == "skia":
            self.stats["native_leaves"] += 1
            from ..motion import rgba

            r, g, b, a = rgba(state["color"])
            canvas.save()
            canvas.translate(box.left, box.top)
            self.text.paint(canvas, c, {**state, "color": (r, g, b, round(a * opacity))})
            canvas.restore()
        else:
            self.stats["raster_leaves"] += 1
            # Specialist viewports own prepared caches/live Arch sessions. Keep
            # their resolution tied to output, as in Pillow, rather than creating
            # a new native/VTK session on every animated ancestor scale sample.
            factor = self._raster_factor if hasattr(c, "frame_key") else density
            key = (
                c,
                tuple(
                    (k, v)
                    for k, v in state.items()
                    if k not in {"position", "rotation", "scale", "scale_x", "scale_y", "opacity"}
                ),
                self._age_key(c, age),
                factor,
            )
            image = self.images.get(key)
            if image is None:
                started = clock.perf_counter()
                guard_size((max(1, math.ceil(box.width * factor)), max(1, math.ceil(box.height * factor))))
                sprite = self.raster.sprite(c, state, factor, age)
                image = image_from_pillow(sprite, s)
                self.stats["raster_seconds"] += clock.perf_counter() - started
                self.images.put(key, image, image.width() * image.height() * 4)
            p = s.Paint()
            p.setAlphaf(opacity)
            canvas.drawImageRect(
                image,
                s.Rect.MakeLTRB(box.left, box.top, box.right, box.bottom),
                s.SamplingOptions(s.CubicResampler.Mitchell()),
                p,
            )

    def _isolated_leaf(self, canvas, c, state, box, world, age, opacity):
        s = self.skia
        density = self._density(world)
        clipped = self._clip_box(c, state, box)
        if clipped is None:
            return
        pad = _shadow_padding(c.drop_shadow) + 1 / density
        local = Bounds(clipped.left - pad, clipped.top - pad, clipped.right + pad, clipped.bottom + pad)
        size = max(1, math.ceil(local.width * density)), max(1, math.ceil(local.height * density))
        # Keep the same local origin/scale after ceil allocation; extra edge is transparent.
        target = Bounds(local.left, local.top, local.left + size[0] / density, local.top + size[1] / density)
        key = (
            "isolated",
            c,
            tuple(
                (k, v)
                for k, v in state.items()
                if k not in {"position", "rotation", "scale", "scale_x", "scale_y", "opacity"}
            ),
            self._age_key(c, age),
            density,
        )
        image = self.images.get(key)
        if image is None:
            with self._surface(size) as layer:
                local_world = (density, 0, 0, density, -local.left * density, -local.top * density)
                inner = layer.getCanvas()
                inner.concat(self._matrix(local_world))
                self._draw_leaf(inner, c, state, box, age, density, 1)
                inner.resetMatrix()
                if c.mask or state["clip"] != (0, 0, 1, 1):
                    self._apply_mask(layer, c, state, box, local_world)
                image = layer.makeImageSnapshot()
                if c.drop_shadow:
                    shadow = c.drop_shadow
                    with self._surface(size) as cast:
                        p = s.Paint(
                            ImageFilter=s.ImageFilters.DropShadow(
                                shadow.offset[0] * density,
                                shadow.offset[1] * density,
                                shadow.blur * density,
                                shadow.blur * density,
                                color(s, shadow.color),
                            )
                        )
                        cast.getCanvas().drawImage(image, 0, 0, s.SamplingOptions(), p)
                        image = cast.makeImageSnapshot()
                self.images.put(key, image, size[0] * size[1] * 4)
        canvas.save()
        canvas.concat(self._matrix(world))
        p = s.Paint()
        p.setAlphaf(opacity)
        canvas.drawImageRect(
            image,
            s.Rect.MakeLTRB(target.left, target.top, target.right, target.bottom),
            s.SamplingOptions(s.CubicResampler.Mitchell()),
            p,
        )
        canvas.restore()
