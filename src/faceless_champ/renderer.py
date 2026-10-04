"""Pillow frame renderer with asset caches and bounded frame memory."""

from __future__ import annotations

import math
from collections import OrderedDict
from itertools import pairwise
from pathlib import Path
from typing import Protocol

from PIL import Image as PILImage
from PIL import ImageColor, ImageDraw, ImageOps

from .charts import Chart
from .charts.drawing import draw_chart
from .components import (
    Arrow,
    Circle,
    Ellipse,
    Equation,
    Icon,
    Image,
    Line,
    Number,
    Polyline,
    Rectangle,
    Shape,
    Text,
    Triangle,
    finite,
)
from .subtitles import Captions
from .timeline import Grid, Layer, Renderable, Scene, Sequence
from .typography import DEFAULT_FONT, load_font


class Renderer(Protocol):
    def validate(self, node: Renderable) -> None: ...
    def frame(self, node: Renderable, time: float, size: tuple[int, int]) -> PILImage.Image: ...


class PillowRenderer:
    def __init__(self, antialias: int = 2, *, frame_cache_mb: float = 64):
        if antialias not in (1, 2, 3, 4):
            raise ValueError("antialias must be 1, 2, 3, or 4")
        self.antialias = antialias
        self._images = {}
        self._fonts = {}
        self._sprites = {}
        self._equations = {}
        self._math_parser = None
        self._math_vector_parser = None
        self._scene_frames = OrderedDict()
        self._frame_cache_limit = round(finite(frame_cache_mb, "frame_cache_mb", 0) * 1024 * 1024)
        self._frame_cache_bytes = 0

    def _font(self, component: Text | Captions, size: int):
        path = component.font or DEFAULT_FONT
        weight = getattr(component, "font_weight", None)
        key = (path, size, weight)
        if key not in self._fonts:
            self._fonts[key] = load_font(path, size, weight)
        return self._fonts[key]

    def _image(self, path: Path):
        key = path.resolve()
        if key not in self._images:
            if not path.is_file():
                raise FileNotFoundError(f"Image file not found: {path}")
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
                raise ValueError("Images must be PNG, JPEG, WebP, or GIF")
            frames, durations = [], []
            with PILImage.open(path) as source:
                count = getattr(source, "n_frames", 1) if source.format == "GIF" else 1
                for index in range(count):
                    source.seek(index)
                    frames.append(ImageOps.exif_transpose(source).convert("RGBA"))
                    durations.append(max(0.01, source.info.get("duration", 100) / 1000))
            self._images[key] = (frames, durations)
        return self._images[key]

    def validate(self, node: Renderable) -> None:
        if not isinstance(node, (Scene, Sequence, Grid, Layer)):
            raise TypeError("Expected Scene, Sequence, Grid, or Layer")
        ImageColor.getcolor(node.canvas.bg, "RGBA")
        _ = node.duration
        if isinstance(node, Scene):
            for entry in node.entries:
                c = entry.component
                if isinstance(c, Chart):
                    draw_chart(c, entry.initial, 1)
                elif isinstance(c, Equation):
                    ImageColor.getcolor(c.color, "RGBA")
                    self._equation(c, 1)
                elif isinstance(c, (Text, Captions)):
                    self._font(c, round(c.font_size))
                    ImageColor.getcolor(c.color, "RGBA")
                    if isinstance(c, Captions):
                        ImageColor.getcolor(c.highlight_color, "RGBA")
                        ImageColor.getcolor(c.future_color, "RGBA")
                        for phrase in c.phrases:
                            self._caption_sprite(c, 1, phrase[0].start)
                elif isinstance(c, Image):
                    self._image(c.path)
                    if isinstance(c, Icon):
                        ImageColor.getcolor(c.color, "RGBA")
                elif isinstance(c, Shape):
                    for color in (c.fill, c.stroke):
                        if color is not None:
                            ImageColor.getcolor(color, "RGBA")
                else:
                    raise TypeError(f"Unsupported component: {type(c).__name__}")
        else:
            for child in node.children:
                self.validate(child)

    def frame(self, node: Renderable, time: float, size: tuple[int, int]) -> PILImage.Image:
        if isinstance(node, Scene):
            node.build()
            return self._scene(node, time, size)
        background = PILImage.new("RGBA", size, node.canvas.bg)
        if isinstance(node, Sequence):
            starts = node.starts
            active = [i for i, (s, c) in enumerate(zip(starts, node.children)) if s <= time < s + c.duration]
            if not active and time >= node.duration:
                active = [len(node.children) - 1]
            if not active:
                return background
            i = active[0]
            first = self._fit(node.children[i], time - starts[i], size, node.canvas.bg)
            if len(active) == 2:
                j = active[1]
                second = self._fit(node.children[j], time - starts[j], size, node.canvas.bg)
                return PILImage.blend(first, second, min(1, (time - starts[j]) / node.crossfade))
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
                right = round((left + col * (cw + node.gap) + cw) * sx)
                bottom = round((top + row * (ch + node.gap) + ch) * sy)
                cell = self._fit(
                    child, min(time - start, child.duration), (max(1, right - x), max(1, bottom - y)), node.canvas.bg
                )
                background.alpha_composite(cell, (x, y))
            return background
        if isinstance(node, Layer):
            for child in node.children:
                background.alpha_composite(self._fit(child, min(time, child.duration), size, "#00000000"))
            return background
        raise TypeError(f"Unsupported renderable: {type(node).__name__}")

    def _fit(self, node, time, size, bg):
        ratio = min(size[0] / node.canvas.width, size[1] / node.canvas.height)
        fitted = (max(1, round(node.canvas.width * ratio)), max(1, round(node.canvas.height * ratio)))
        frame = self.frame(node, time, fitted)
        result = PILImage.new("RGBA", size, bg)
        result.alpha_composite(frame, ((size[0] - fitted[0]) // 2, (size[1] - fitted[1]) // 2))
        return result

    def _scene(self, scene, time, size):
        visible = []
        for entry in sorted(scene.entries, key=lambda e: e.component.z_index):
            if time < entry.start or (entry.end is not None and time >= entry.end):
                continue
            state = entry.state_at(time)
            if state["opacity"] > 0:
                visible.append((entry.component, state, max(0, time - entry.start)))
        signature = (
            scene.canvas,
            size,
            tuple(
                (
                    c,
                    tuple(state.items()),
                    age
                    if isinstance(c, Captions) or (isinstance(c, Image) and c.path.suffix.lower() == ".gif")
                    else None,
                )
                for c, state, age in visible
            ),
        )
        cached = self._scene_frames.get(scene)
        if cached is not None and cached[0] == signature:
            self._scene_frames.move_to_end(scene)
            return cached[1].copy()
        aa = self.antialias
        big = (size[0] * aa, size[1] * aa)
        result = PILImage.new("RGBA", big, scene.canvas.bg)
        factor = min(big[0] / scene.canvas.width, big[1] / scene.canvas.height)
        for c, state, age in visible:
            sprite = self._sprite(c, state, factor, age)
            w, h = sprite.size
            scale = state["scale"]
            if scale != 1:
                sprite = sprite.resize(
                    (max(1, round(w * scale)), max(1, round(h * scale))), PILImage.Resampling.LANCZOS
                )
            w, h = sprite.size
            x, y = (v * factor for v in state["position"])
            # Rotate around the sprite center. Top-left anchors refer to its unrotated box.
            if c.anchor == "top_left":
                x += w / 2
                y += h / 2
            if state["rotation"]:
                sprite = sprite.rotate(-state["rotation"], resample=PILImage.Resampling.BICUBIC, expand=True)
            if state["opacity"] < 1:
                sprite = sprite.copy()
                sprite.putalpha(sprite.getchannel("A").point(lambda a, opacity=state["opacity"]: round(a * opacity)))
            result.alpha_composite(sprite, (round(x - sprite.width / 2), round(y - sprite.height / 2)))
        if aa > 1:
            result = result.resize(size, PILImage.Resampling.LANCZOS)
        # One frame per scene within an LRU byte budget. Copies protect caller edits.
        previous = self._scene_frames.pop(scene, None)
        if previous is not None:
            self._frame_cache_bytes -= previous[1].width * previous[1].height * 4
        cost = result.width * result.height * 4
        if cost <= self._frame_cache_limit:
            while self._frame_cache_bytes + cost > self._frame_cache_limit:
                _, (_, old) = self._scene_frames.popitem(last=False)
                self._frame_cache_bytes -= old.width * old.height * 4
            self._scene_frames[scene] = (signature, result.copy())
            self._frame_cache_bytes += cost
        return result

    def _sprite(self, c, state, factor, age):
        if isinstance(c, Chart):
            # The bounded scene-frame cache handles holds; never retain per-frame chart sprites.
            return draw_chart(c, state, factor)
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
        static = state["reveal"] == 1 and state["draw"] == 1
        frame_index = 0
        if isinstance(c, Image):
            frames, durations = self._image(c.path)
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
            if isinstance(c, Icon):
                source = PILImage.new("RGBA", source.size, c.color)
                tint_alpha = ImageColor.getcolor(c.color, "RGBA")[3]
                source.putalpha(frames[frame_index].getchannel("A").point(lambda a: round(a * tint_alpha / 255)))
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
                radius = c.corner_radius * factor
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
                lengths = [math.dist(a, b) for a, b in pairwise(points)]
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

    def _equation(self, c: Equation, factor: float):
        key = (c.expression, c.font_size, c.fontset, c.color, c.max_width, tuple(sorted(c.color_map.items())), factor)
        if key in self._equations:
            return self._equations[key]
        try:
            import numpy as np
            from matplotlib import rc_context
            from matplotlib.font_manager import FontProperties
            from matplotlib.mathtext import MathTextParser
        except ImportError as exc:
            raise RuntimeError(
                "Equation requires the equations extra: install 'faceless-champ[equations]' "
                "or run 'uv sync --extra equations' in this checkout"
            ) from exc
        if self._math_parser is None:
            self._math_parser = MathTextParser("agg")
        with rc_context({"mathtext.default": "it"}):
            try:
                prop = FontProperties(size=max(1, c.font_size * factor), math_fontfamily=c.fontset)
                if c.color_map:
                    sprite = self._colored_equation(c, prop)
                else:
                    parsed = self._math_parser.parse(f"${c.expression}$", dpi=72, prop=prop)
            except ValueError as exc:
                raise ValueError(f"Invalid Equation {c.expression!r}: {exc}") from exc
        if not c.color_map:
            mask = PILImage.fromarray(np.asarray(parsed.image).copy())
            color = ImageColor.getcolor(c.color, "RGBA")
            sprite = PILImage.new("RGBA", mask.size, color)
            if color[3] != 255:
                mask = mask.point(lambda alpha: round(alpha * color[3] / 255))
            sprite.putalpha(mask)
        box = sprite.getbbox()
        if box:
            sprite = sprite.crop(box)
        if c.max_width is not None and sprite.width > c.max_width * factor:
            ratio = c.max_width * factor / sprite.width
            sprite = sprite.resize(
                (max(1, round(sprite.width * ratio)), max(1, round(sprite.height * ratio))), PILImage.Resampling.LANCZOS
            )
        self._equations[key] = sprite
        return sprite

    def _colored_equation(self, c, prop):
        """Color positioned math glyphs after typesetting the complete expression."""
        import numpy as np
        from matplotlib import ft2font
        from matplotlib.backends.backend_agg import RendererAgg
        from matplotlib.mathtext import MathTextParser
        from matplotlib.path import Path as MathPath
        from matplotlib.transforms import Affine2D, Bbox

        if self._math_vector_parser is None:
            self._math_vector_parser = MathTextParser("path")
        parser = self._math_vector_parser
        base = tuple(v / 255 for v in ImageColor.getcolor(c.color, "RGBA"))
        colors = {}
        for symbol, color in c.color_map.items():
            parsed_symbol = parser.parse(f"${symbol}$", dpi=72, prop=prop)
            if len(parsed_symbol.glyphs) != 1 or parsed_symbol.rects:
                raise ValueError(f"color_map key {symbol!r} must represent one math glyph")
            code = parsed_symbol.glyphs[0][2]
            rgba = tuple(v / 255 for v in ImageColor.getcolor(color, "RGBA"))
            if code in colors and colors[code] != rgba:
                raise ValueError(f"color_map contains conflicting aliases for {symbol!r}")
            colors[code] = rgba
        parsed = parser.parse(f"${c.expression}$", dpi=72, prop=prop)
        paths = []
        flags = ft2font.LoadFlags.NO_HINTING if hasattr(ft2font, "LoadFlags") else ft2font.LOAD_NO_HINTING
        for glyph in parsed.glyphs:
            font, size, code = glyph[:3]
            x, y = glyph[-2:]
            font.set_size(size, 72)
            # Matplotlib 3.11 includes the glyph index; 3.9/3.10 return five fields.
            if len(glyph) == 6:
                font.load_glyph(glyph[3], flags=flags)
            else:
                font.load_char(code, flags=flags)
            vertices, codes = font.get_path()
            if len(vertices):
                path = MathPath(vertices, codes).transformed(Affine2D().translate(x, y))
                paths.append((path, colors.get(code, base)))
        for x, y, width, height in parsed.rects:
            path = MathPath.unit_rectangle().transformed(Affine2D().scale(width, height).translate(x, y))
            paths.append((path, base))
        if not paths:
            return PILImage.new("RGBA", (1, 1))
        bounds = Bbox.union([path.get_extents() for path, _ in paths])
        left, bottom = math.floor(bounds.x0), math.floor(bounds.y0)
        renderer = RendererAgg(math.ceil(bounds.x1 - left) + 4, math.ceil(bounds.y1 - bottom) + 4, 72)
        gc = renderer.new_gc()
        gc.set_linewidth(0)
        gc.set_antialiased(True)
        transform = Affine2D().translate(2 - left, 2 - bottom)
        for path, rgba in paths:
            renderer.draw_path(gc, path, transform, rgbFace=rgba)
        gc.restore()
        return PILImage.fromarray(np.asarray(renderer.buffer_rgba()).copy())

    def _caption_sprite(self, c: Captions, factor: float, age: float):
        phrase = c.phrase_at(age)
        if not phrase:
            return PILImage.new("RGBA", (1, 1))
        active = c.track.active_at(age)
        finished = sum(cue.end <= age for cue in phrase)
        key = (c, factor, phrase[0].index, active.index if active else None, finished)
        if key in self._sprites:
            return self._sprites[key]
        font = self._font(c, max(1, round(c.font_size * factor)))
        width = max(1, round(c.width * factor))
        space = font.getlength(" ")
        lines, line, used = [], [], 0.0
        for cue in phrase:
            for word in cue.text.split():
                length = font.getlength(word)
                if length + 4 > width:
                    raise ValueError(f"Caption word {word!r} exceeds width; increase width or reduce font_size")
                if line and used + space + length + 4 > width:
                    lines.append((line, used))
                    line, used = [], 0.0
                if line:
                    used += space
                line.append((word, cue, length))
                used += length
        if line:
            lines.append((line, used))
        ascent, descent = font.getmetrics()
        step = ascent + descent + round(c.spacing * factor)
        sprite = PILImage.new("RGBA", (width, step * len(lines) + 4))
        draw = ImageDraw.Draw(sprite)
        for row, (words, length) in enumerate(lines):
            x = (width - length) / 2
            for word, cue, word_length in words:
                color = c.highlight_color if active == cue else (c.color if age >= cue.end else c.future_color)
                draw.text((x, 2 + ascent + row * step), word, font=font, fill=color, anchor="ls")
                x += word_length + space
        self._sprites[key] = sprite
        return sprite
