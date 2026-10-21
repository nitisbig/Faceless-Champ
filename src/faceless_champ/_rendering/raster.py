"""Owned primitive and prepared-source raster painting, independent of renderers."""

from __future__ import annotations

import math
from collections import OrderedDict
from contextlib import ExitStack
from copy import copy
from io import BytesIO
from itertools import pairwise

from PIL import Image as PILImage
from PIL import ImageColor, ImageDraw, ImageOps

from ..components import (
    Arrow,
    Circle,
    Ellipse,
    Equation,
    Icon,
    Image,
    ImageSlot,
    Line,
    Number,
    Polyline,
    Rectangle,
    Shape,
    Text,
    Triangle,
    finite,
)
from ..layout import Group
from ..motion import style_value
from ..subtitles import Captions
from ..timeline import Grid, Layer, Renderable, Scene, Sequence
from ..typography import load_font


class RasterPainter:
    def __init__(
        self,
        *,
        source_cache_mb: float = 64,
        raster_cache_mb: float = 64,
        caption_cache_mb: float = 32,
        code_cache_mb: float = 32,
        arch_session_limit: int = 4,
    ):
        self._code_sprites = OrderedDict()
        self._code_cache_limit = round(finite(code_cache_mb, "code_cache_mb", 0) * 1024 * 1024)
        self._code_cache_bytes = 0
        self._images = {}
        from .._rendering.measure import Measurement

        self._measurement = Measurement(
            caption_cache_limit=round(finite(caption_cache_mb, "caption_cache_mb", 0) * 1024**2)
        )
        self._fonts = self._measurement._fonts
        self._sprites = {}
        self._equations = self._measurement._equations
        source_cache_bytes = round(finite(source_cache_mb, "source_cache_mb", 0) * 1024**2)
        self._raster_cache_limit = round(finite(raster_cache_mb, "raster_cache_mb", 0) * 1024**2)
        self._caption_sprites = OrderedDict()
        self._caption_layouts = self._measurement._caption_layouts
        self._caption_cache_limit = round(finite(caption_cache_mb, "caption_cache_mb", 0) * 1024 * 1024)
        self._caption_cache_bytes = 0
        if isinstance(arch_session_limit, bool) or not isinstance(arch_session_limit, int) or arch_session_limit < 1:
            raise ValueError("arch_session_limit must be a positive integer")
        self._arch_session_limit = arch_session_limit
        self._component_sources = OrderedDict()
        self.isolate_sources = False
        from .._rendering.resources import SourceSessions

        self._sources = SourceSessions(cache_bytes=source_cache_bytes, session_limit=arch_session_limit)

    def close(self):
        with ExitStack() as cleanup:
            for cache in (
                self._images,
                self._fonts,
                self._sprites,
                self._equations,
                self._caption_sprites,
                self._caption_layouts,
                self._code_sprites,
            ):
                cleanup.callback(cache.clear)
            self._caption_cache_bytes = self._code_cache_bytes = 0
            cleanup.callback(self._measurement.close)
            self._component_sources.clear()
            cleanup.callback(self._sources.close)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    @property
    def measurement(self):
        return self._measurement

    def sprite(self, component, state, factor, age):
        result = self._sprite(component, state, factor, age)
        self.trim(self._raster_cache_limit)
        return result

    def primitive(self, component, state, factor, age=0):
        return self._base_sprite(component, state, factor, age)

    def age_key(self, component, age):
        return self._measurement.age_key(component, age)

    def trim(self, limit):
        def cost(value):
            images = value[0] if isinstance(value, tuple) else (value,)
            return sum(im.width * im.height * 4 for im in images)

        caches = self._sprites, self._equations, self._images
        total = sum(cost(value) for cache in caches for value in cache.values())
        for cache in caches:
            while total > limit and cache:
                total -= cost(cache.pop(next(iter(cache))))

    def _font(self, component, size):
        return self._measurement._font(component, size)

    def _image(self, component: Image):
        path = component.path
        if (
            isinstance(component, ImageSlot)
            and path is not None
            and (component.mode == "placeholder" or (component.mode == "auto" and not path.exists()))
        ):
            key = ("placeholder", component)
            if key not in self._images:
                size = (max(1, round(component.width)), max(1, round(component.height)))
                sprite = PILImage.new("RGBA", size, component.placeholder_fill)
                draw = ImageDraw.Draw(sprite)
                draw.rectangle((0, 0, size[0] - 1, size[1] - 1), outline=component.placeholder_stroke, width=2)
                font = load_font(component.placeholder_font, round(component.placeholder_font_size))
                box = draw.multiline_textbbox((0, 0), component.label, font=font, align="center")
                ratio = min(1, (size[0] - 16) / max(1, box[2] - box[0]), (size[1] - 16) / max(1, box[3] - box[1]))
                if ratio < 1:
                    font = load_font(component.placeholder_font, max(1, round(component.placeholder_font_size * ratio)))
                draw.multiline_text(
                    (size[0] / 2, size[1] / 2),
                    component.label,
                    font=font,
                    fill=component.placeholder_color,
                    anchor="mm",
                    align="center",
                )
                self._images[key] = ([sprite], [0.1])
            return self._images[key]
        key = path.resolve() if path is not None else component.source_bytes
        if key not in self._images:
            if path is not None and not path.is_file():
                raise FileNotFoundError(f"Image file not found: {path}")
            if path is not None and path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                raise ValueError("Images must be PNG, JPEG, WebP, or GIF")
            frames, durations = [], []
            try:
                with PILImage.open(path if path is not None else BytesIO(component.source_bytes)) as source:
                    if source.format not in {"PNG", "JPEG", "WEBP", "GIF"}:
                        raise ValueError("Images must be PNG, JPEG, WebP, or GIF")
                    count = getattr(source, "n_frames", 1) if source.format == "GIF" else 1
                    for index in range(count):
                        source.seek(index)
                        frames.append(ImageOps.exif_transpose(source).convert("RGBA"))
                        durations.append(max(0.01, source.info.get("duration", 100) / 1000))
            except OSError as exc:
                if isinstance(component, ImageSlot):
                    raise ValueError(f"Cannot decode image: {path or 'in-memory source'}") from exc  # noqa: TRY004
                raise
            self._images[key] = (frames, durations)
        return self._images[key]

    def validate(self, node: Renderable, *, backend="pillow") -> None:
        from ..gradients import LinearGradient, RadialGradient
        from ..paths import VectorPath
        from ..sources import Viewport
        from ..surfaces import Surface

        if not isinstance(node, (Scene, Sequence, Grid, Layer)):
            raise TypeError("Expected Scene, Sequence, Grid, or Layer")
        if backend != "structural":
            from .support import preflight

            preflight(node, backend)
        if backend != "structural" and (
            getattr(node, "effects", None) is not None or getattr(node, "transition", None) is not None
        ):
            from .._effects_cpu import numpy

            numpy()
        ImageColor.getcolor(node.canvas.bg, "RGBA")
        _ = node.duration
        if isinstance(node, Scene):
            for entry in node.entries:
                c = entry.component
                from ..indicators import ProgressBar

                if c.effects is not None and backend != "structural":
                    from .._effects_cpu import numpy

                    numpy()
                if c.mask is not None and c.mask.kind == "path" and backend == "pillow":
                    raise ValueError("PathMask requires backend='skia'")
                if backend not in {"structural", "pillow"} and (
                    (c.mask is not None and c.mask.kind == "path") or (isinstance(c, VectorPath) and not c.portable)
                ):
                    from ..backends._native import load_skia

                    load_skia()
                if isinstance(c, Group) and c.drop_shadow is not None:
                    raise ValueError("Group shadows are not supported; attach a shadow to a surface or leaf")
                if getattr(c, "_procedural", False):
                    if backend != "structural":
                        from .._effects_cpu import numpy

                        numpy()
                    continue
                if c.validate_render(backend, self):
                    continue
                if isinstance(c, ProgressBar):
                    continue
                if isinstance(c, (Group, Surface, Viewport)):
                    continue
                elif isinstance(c, Equation):
                    ImageColor.getcolor(c.color, "RGBA")
                    self._equation(c, 1)
                elif isinstance(c, (Text, Captions)):
                    if isinstance(c, Text) and c.text_engine == "skia":
                        if backend == "pillow":
                            raise ValueError("Native typography requires backend='skia'")
                        if backend == "skia":
                            from ..backends._skia_text import text_size

                            text_size(c, entry.initial)
                    else:
                        self._font(c, round(c.font_size))
                    ImageColor.getcolor(c.color, "RGBA")
                    if isinstance(c, Captions):
                        ImageColor.getcolor(c.highlight_color, "RGBA")
                        ImageColor.getcolor(c.future_color, "RGBA")
                        for phrase in c.phrases:
                            self._caption_sprite(c, 1, phrase[0].start)
                elif isinstance(c, Image):
                    self._image(c)
                    self.trim(self._raster_cache_limit)
                    if c.tint is not None:
                        ImageColor.getcolor(c.tint, "RGBA")
                    if isinstance(c, Icon):
                        ImageColor.getcolor(c.color, "RGBA")
                elif isinstance(c, Shape):
                    if isinstance(c, VectorPath) and not c.portable and backend == "pillow":
                        raise ValueError("Compound paths and even_odd fill require backend='skia'")
                    for color in (c.fill, c.stroke):
                        if color is not None and not isinstance(color, (LinearGradient, RadialGradient)):
                            ImageColor.getcolor(color, "RGBA")
                else:
                    raise TypeError(f"Unsupported component: {type(c).__name__}")
        else:
            for child in node.children:
                self.validate(child, backend=backend)

    def _sprite(self, c, state, factor, age):
        from ..gradients import LinearGradient, RadialGradient
        from ..paths import VectorPath
        from ..surfaces import Surface

        if isinstance(c, Text) and c.text_engine == "skia":
            raise ValueError("Native typography requires backend='skia'")
        if isinstance(c, (Surface, VectorPath)) or (
            isinstance(c, Shape) and isinstance(state["fill"], (LinearGradient, RadialGradient))
        ):
            from .._portable import shape_sprite, surface_sprite

            static = state["draw"] == 1 and all(
                state.get(k) == v
                for k, v in c.state().items()
                if k in {"fill", "stroke", "width", "height", "stroke_width", "corner_radius"}
            )
            key = (c, factor, "retained")
            if static and key in self._sprites:
                return self._sprites[key]
            sprite = surface_sprite(c, factor) if isinstance(c, Surface) else shape_sprite(c, state, factor)
            if static:
                self._sprites[key] = sprite
            return sprite
        return self._base_sprite(c, state, factor, age)

    def _base_sprite(self, c, state, factor, age):
        from ..sources import Viewport

        if isinstance(c, Viewport):
            size = max(1, round(c.width * factor)), max(1, round(c.height * factor))
            return self._sources.frame(c.source, size, c.source_time(age))

        from ..components import Component
        from ..indicators import ProgressBar, draw_indicator

        if type(c).raster_source is not Component.raster_source:
            source = self._component_sources.pop(c, None)
            if source is None:
                source = c.raster_source(isolate=self.isolate_sources)
            self._component_sources[c] = source
            while len(self._component_sources) > self._arch_session_limit:
                self._component_sources.popitem(last=False)
            size = max(1, round(c.width * factor)), max(1, round(c.height * factor))
            return self._sources.frame(source, size, age)
        custom = c.render_raster(state, factor, age, self)
        if custom is not NotImplemented:
            return custom
        if callable(getattr(c, "frame_image", None)):
            return c.frame_image(age, factor)
        if isinstance(c, ProgressBar):
            return draw_indicator(c, state, factor, self)
        # A temporary style view avoids mutating snapshots and retaining intermediate sprites.
        dynamic = any(
            key in state and state[key] != value
            for key, value in c.state().items()
            if key in {"fill", "stroke", "color", "width", "height", "stroke_width", "corner_radius"}
        )
        if dynamic:
            original = c
            c = copy(c)
            for key in ("fill", "stroke", "color", "width", "height", "stroke_width", "corner_radius"):
                if key in state:
                    value = state[key]
                    setattr(c, key, style_value(key, value))
            if isinstance(c, Polyline):
                c.points = tuple((x * c.width / original.width, y * c.height / original.height) for x, y in c.points)
        else:
            dynamic = False

        if isinstance(c, Captions):
            return self._caption_sprite(c, factor, age)
        if isinstance(c, Number):
            font = self._font(c, max(1, round(c.font_size * factor)))
            text = c.format(state["value"])
            d = ImageDraw.Draw(PILImage.new("RGBA", (1, 1)))
            box = d.textbbox((0, 0), text or " ", font=font)
            text_width = math.ceil(box[2] - box[0])
            width = text_width if c.width is None else round(c.width * factor)
            if width < text_width:
                raise ValueError("Number text exceeds its fixed width")
            sprite = PILImage.new("RGBA", (max(1, width) + 4, max(1, math.ceil(box[3] - box[1])) + 4))
            x = 0 if c.align == "left" else (width - text_width if c.align == "right" else (width - text_width) / 2)
            visible = text[: math.floor(len(text) * state["reveal"] + 1e-9)]
            ImageDraw.Draw(sprite).text((x + 2 - box[0], 2 - box[1]), visible, font=font, fill=c.color)
            return sprite
        # Dynamic reveal/draw frames are deliberately not retained in the cache.
        static = not dynamic and state["reveal"] == 1 and state["draw"] == 1
        frame_index = 0
        if isinstance(c, Image):
            frames, durations = self._image(c)
            clock = age % sum(durations)
            for frame_index, duration in enumerate(durations):
                if clock < duration:
                    break
                clock -= duration
        key = (c, factor, frame_index)
        if static and key in self._sprites:
            return self._sprites[key]
        if isinstance(c, Equation):
            sprite = self._equation(c, factor)
            if state["reveal"] < 1:
                visible = max(0, min(sprite.width, math.floor(sprite.width * state["reveal"])))
                revealed = PILImage.new("RGBA", sprite.size)
                if visible:
                    revealed.paste(sprite.crop((0, 0, visible, sprite.height)), (0, 0))
                sprite = revealed
        elif isinstance(c, Text):
            font = self._font(c, max(1, round(c.font_size * factor)))
            spacing = round(c.spacing * factor)
            draw = ImageDraw.Draw(PILImage.new("RGBA", (1, 1)))
            box = draw.multiline_textbbox((0, 0), c.text or " ", font=font, spacing=spacing, align=c.align)
            sprite = PILImage.new(
                "RGBA", (max(1, math.ceil(box[2] - box[0]) + 4), max(1, math.ceil(box[3] - box[1]) + 4))
            )
            text = c.text[: math.floor(len(c.text) * state["reveal"] + 1e-9)]
            ImageDraw.Draw(sprite).multiline_text(
                (2 - box[0], 2 - box[1]), text, font=font, fill=c.color, spacing=spacing, align=c.align
            )
        elif isinstance(c, Image):
            size = (max(1, round(c.width * factor)), max(1, round(c.height * factor)))
            source = frames[frame_index]
            if c.trim:
                # Use a union across frames to prevent animated assets from wobbling.
                boxes = [frame.getchannel("A").getbbox() for frame in frames]
                boxes = [box for box in boxes if box is not None]
                if boxes:
                    box = (
                        min(b[0] for b in boxes),
                        min(b[1] for b in boxes),
                        max(b[2] for b in boxes),
                        max(b[3] for b in boxes),
                    )
                    source = source.crop(box)
            tint = c.color if isinstance(c, Icon) else c.tint
            if tint is not None:
                alpha = source.getchannel("A")
                source = PILImage.new("RGBA", source.size, tint)
                tint_alpha = ImageColor.getcolor(tint, "RGBA")[3]
                source.putalpha(alpha.point(lambda a: round(a * tint_alpha / 255)))
            if c.fit == "cover":
                sprite = ImageOps.fit(source, size, method=PILImage.Resampling.LANCZOS)
            else:
                fit = ImageOps.contain(source, size, method=PILImage.Resampling.LANCZOS)
                sprite = PILImage.new("RGBA", size)
                sprite.alpha_composite(fit, ((size[0] - fit.width) // 2, (size[1] - fit.height) // 2))
        elif isinstance(c, Arrow):
            width = max(1, round(c.stroke_width * factor))
            length, tip = c.width * factor, c.tip_size * factor
            pad = math.ceil(tip + width)
            sprite = PILImage.new("RGBA", (math.ceil(length) + pad * 2 + 1, pad * 2 + 1))
            progress = max(0, min(1, state["draw"]))
            if c.stroke and c.stroke_width > 0 and progress > 0:
                draw = ImageDraw.Draw(sprite)
                end = pad + length * progress
                draw.line([(pad, pad), (end, pad)], fill=c.stroke, width=width)
                visible_tip = tip * min(1, max(0, (progress - 0.85) / 0.15))
                if visible_tip:
                    draw.polygon(
                        [
                            (end, pad),
                            (end - visible_tip, pad - visible_tip / 2),
                            (end - visible_tip, pad + visible_tip / 2),
                        ],
                        fill=c.stroke,
                    )
        else:
            width = max(1, round(c.stroke_width * factor))
            w, h = max(1, round(c.width * factor)), max(1, round(c.height * factor))
            sprite = PILImage.new("RGBA", (w + width * 2, h + width * 2))
            draw = ImageDraw.Draw(sprite)
            x, y = width, width
            if isinstance(c, Polyline):
                points = [(x + px * factor, y + py * factor) for px, py in c.points]
                if c.closed:
                    points.append(points[0])
            elif isinstance(c, Rectangle) and c.corner_radius:
                radius = min(c.corner_radius, c.width / 2, c.height / 2) * factor
                points = []
                for cx, cy, start in (
                    (x + w - radius, y + radius, -90),
                    (x + w - radius, y + h - radius, 0),
                    (x + radius, y + h - radius, 90),
                    (x + radius, y + radius, 180),
                ):
                    for step in range(13):
                        angle = math.radians(start + step * 90 / 12)
                        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
                points.append(points[0])
            elif isinstance(c, (Circle, Ellipse)):
                points = [
                    (
                        x + w / 2 + w / 2 * math.cos(a * math.tau / 180 - math.pi / 2),
                        y + h / 2 + h / 2 * math.sin(a * math.tau / 180 - math.pi / 2),
                    )
                    for a in range(181)
                ]
            elif isinstance(c, Triangle):
                points = [(x + w / 2, y), (x + w, y + h), (x, y + h), (x + w / 2, y)]
            elif isinstance(c, Line):
                points = [(x, y), (x + w, y)]
            else:
                points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
            progress = max(0, min(1, state["draw"]))
            can_fill = not isinstance(c, Line) and (not isinstance(c, Polyline) or c.closed)
            if c.fill and can_fill and progress >= 1:
                draw.polygon(points, fill=c.fill)
            if c.stroke and c.stroke_width > 0 and progress > 0:
                lengths = [
                    b[0] - a[0] if isinstance(c, Polyline) and c.draw_by == "x" else math.dist(a, b)
                    for a, b in pairwise(points)
                ]
                remaining = sum(lengths) * progress
                visible = [points[0]]
                for a, b, length in zip(points, points[1:], lengths):
                    if remaining >= length:
                        visible.append(b)
                        remaining -= length
                    else:
                        ratio = remaining / length if length else 0
                        visible.append((a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio))
                        break
                draw.line(visible, fill=c.stroke, width=width, joint="curve")
                if isinstance(c, Polyline) and c.line_cap == "round" and not c.closed:
                    radius = width / 2
                    for px, py in (visible[0], visible[-1]):
                        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=c.stroke)
        if static:
            self._sprites[key] = sprite
        return sprite

    def _equation(self, c, factor):
        return self._measurement._equation(c, factor)

    def _colored_equation(self, c, prop):
        return self._measurement._colored_equation(c, prop)

    @staticmethod
    def _caption_state(c: Captions, age: float):
        phrase = c.phrase_at(age)
        if not phrase:
            return None
        active = c.track.active_at(age)
        finished = sum(cue.end <= age for cue in phrase)
        return (phrase[0].index, active.index if active else None, finished)

    def _caption_layout(self, c, factor, phrase):
        return self._measurement._caption_layout(c, factor, phrase)

    def _caption_sprite(self, c: Captions, factor: float, age: float):
        state = self._caption_state(c, age)
        if state is None:
            return PILImage.new("RGBA", (1, 1))
        key = (c, factor, state)
        if key in self._caption_sprites:
            self._caption_sprites.move_to_end(key)
            return self._caption_sprites[key]
        phrase = c.phrase_at(age)
        active = c.track.active_at(age)
        font, width, lines, ascent, step = self._caption_layout(c, factor, phrase)
        space = font.getlength(" ")
        sprite = PILImage.new("RGBA", (width, step * len(lines) + 4))
        draw = ImageDraw.Draw(sprite)
        for row, (words, length) in enumerate(lines):
            x = (width - length) / 2
            for word, cue, word_length in words:
                color = c.highlight_color if active == cue else (c.color if age >= cue.end else c.future_color)
                draw.text((x, 2 + ascent + row * step), word, font=font, fill=color, anchor="ls")
                x += word_length + space
        cost = sprite.width * sprite.height * 4
        if cost <= self._caption_cache_limit:
            while self._caption_cache_bytes + cost > self._caption_cache_limit:
                _, old = self._caption_sprites.popitem(last=False)
                self._caption_cache_bytes -= old.width * old.height * 4
            self._caption_sprites[key] = sprite
            self._caption_cache_bytes += cost
        return sprite
