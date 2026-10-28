"""Session-owned logical/ink/text measurement. No renderer or viewport sessions."""

from __future__ import annotations

import math
from collections import OrderedDict
from threading import local

from PIL import Image as PILImage
from PIL import ImageColor, ImageDraw

from ..components import Arrow, Equation, Number, Shape, Text
from ..subtitles import Captions
from ..typography import DEFAULT_FONT, load_font, pillow_line_spacing, tracked_layout


class Measurement:
    def __init__(self, *, caption_cache_limit=32 * 1024**2):
        self._fonts = {}
        self._equations = {}
        self._math_parser = self._math_vector_parser = None
        self._caption_layouts = OrderedDict()
        self._caption_cache_limit = caption_cache_limit
        self._image_durations = OrderedDict()

    @property
    def measurement(self):
        return self

    def size(self, c, state=None, *, age=0, logical=False):
        from ..surfaces import Surface

        state = c.state() if state is None else state
        if isinstance(c, Surface) or (logical and getattr(c, "_procedural", False)):
            return c.width, c.height
        if isinstance(c, Shape):
            sw = max(1, round(state["stroke_width"]))
            if isinstance(c, Arrow):
                pad = math.ceil(c.tip_size + sw)
                return math.ceil(state["width"]) + 2 * pad + 1, 2 * pad + 1
            return max(1, round(state["width"])) + 2 * sw, max(1, round(state["height"])) + 2 * sw
        if isinstance(c, Text) and c.text_engine == "skia":
            from ..backends._skia_text import text_size

            return text_size(c, state)
        if isinstance(c, Captions):
            phrases = (c.phrase_at(age),) if not logical else tuple(c.phrase_at(p[0].start) for p in c.phrases)
            sizes = []
            for phrase in phrases:
                if not phrase:
                    sizes.append((1, 1))
                else:
                    _, width, lines, _, step = self._caption_layout(c, 1, phrase)
                    sizes.append((width, step * len(lines) + 4))
            return max(w for w, _ in sizes), max(h for _, h in sizes)
        if isinstance(c, Equation):
            return self._equation(c, 1).size
        if isinstance(c, Number):
            font = self._font(c, max(1, round(c.font_size)))
            draw = ImageDraw.Draw(PILImage.new("L", (1, 1)))
            value = c.format(state["value"]) or " "
            if c.tracking:
                box = tracked_layout(draw, font, value, spacing=0, align="left", track=c.tracking * c.font_size)[0]
            else:
                box = draw.textbbox((0, 0), value, font=font)
            width = math.ceil(box[2] - box[0])
            if c.width is not None:
                if round(c.width) < width:
                    raise ValueError("Number text exceeds its fixed width")
                width = round(c.width)
            return max(1, width) + 4, max(1, math.ceil(box[3] - box[1])) + 4
        if isinstance(c, Text):
            size = max(1, round(c.font_size))
            font = self._font(c, size)
            spacing = pillow_line_spacing(font, size, c.line_height, c.spacing)
            draw = ImageDraw.Draw(PILImage.new("L", (1, 1)))
            if c.tracking:
                box = tracked_layout(
                    draw, font, c.text or " ", spacing=spacing, align=c.align, track=c.tracking * size
                )[0]
            else:
                box = draw.multiline_textbbox((0, 0), c.text or " ", font=font, spacing=spacing, align=c.align)
            return max(1, math.ceil(box[2] - box[0]) + 4), max(1, math.ceil(box[3] - box[1]) + 4)
        if hasattr(c, "width") and hasattr(c, "height"):
            return max(1, round(c.width)), max(1, round(c.height))
        raise TypeError(f"No measurement for {type(c).__name__}")

    def points(self, c, *, entry=None, time=0):
        from ..layout import Group, transform_point

        state = entry.state_at(time) if entry is not None else c.state()
        if isinstance(c, Group):
            children = (
                ((e.component, e) for e in entry.children)
                if entry is not None
                else ((child, None) for child in c.children)
            )
            for child, child_entry in children:
                for p in self.points(child, entry=child_entry, time=time):
                    yield transform_point(p, c._origin, state)
            return
        w, h = self.size(c, state, age=max(0, time - entry.start) if entry is not None else 0, logical=True)
        if c.anchor == "top_left":
            state = {
                **state,
                "position": (
                    state["position"][0] + w * state["scale"] * state["scale_x"] / 2,
                    state["position"][1] + h * state["scale"] * state["scale_y"] / 2,
                ),
            }
        for p in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
            yield transform_point(p, (0, 0), state)

    def bounds(self, c):
        from ..layout import _enclose

        return _enclose(tuple(self.points(c)))

    def entry_bounds(self, entry, time, *, ancestors=False):
        from ..layout import _enclose, transform_point

        points = self.points(entry.component, entry=entry, time=time)
        if ancestors:
            points = tuple(points)
            for parent in entry.ancestors():
                points = tuple(transform_point(p, parent.component._origin, parent.state_at(time)) for p in points)
        return _enclose(tuple(points))

    def age_key(self, c, age):
        from ..components import Image, ImageSlot

        if callable(getattr(c, "frame_key", None)):
            return c.frame_key(age)
        if isinstance(c, Captions):
            phrase, active = c.phrase_at(age), c.track.active_at(age)
            return (
                (phrase[0].index, active.index if active else None, sum(cue.end <= age for cue in phrase))
                if phrase
                else None
            )
        if (
            isinstance(c, ImageSlot)
            and c.path is not None
            and (c.mode == "placeholder" or (c.mode == "auto" and not c.path.exists()))
        ):
            return None
        if isinstance(c, Image):
            key = c.path if c.path is not None else c.source_bytes
            durations = self._image_durations.get(key)
            if durations is None:
                from io import BytesIO

                with PILImage.open(c.path if c.path is not None else BytesIO(c.source_bytes)) as source:
                    durations = []
                    for index in range(getattr(source, "n_frames", 1) if source.format == "GIF" else 1):
                        source.seek(index)
                        durations.append(max(0.01, source.info.get("duration", 100) / 1000))
                durations = tuple(durations)
                if len(self._image_durations) >= 128:
                    self._image_durations.popitem(last=False)
                self._image_durations[key] = durations
            if len(durations) > 1:
                clock = age % sum(durations)
                for index, duration in enumerate(durations):
                    if clock < duration:
                        return index
                    clock -= duration
        return None

    def close(self):
        self._fonts.clear()
        self._equations.clear()
        self._caption_layouts.clear()
        self._image_durations.clear()
        self._math_parser = self._math_vector_parser = None

    def _font(self, component: Text | Captions, size: int):
        path = component.font or DEFAULT_FONT
        weight = getattr(component, "font_weight", None)
        # Optical size follows the design size, so supersampled and 4K rasters
        # use the same cut as 1080p measurement.
        opsz = getattr(component, "font_size", size)
        key = (path, size, weight, opsz)
        if key not in self._fonts:
            if len(self._fonts) >= 128:
                self._fonts.pop(next(iter(self._fonts)))
            self._fonts[key] = load_font(path, size, weight, opsz=opsz)
        return self._fonts[key]

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
        cost = sprite.width * sprite.height * 4
        total = sum(im.width * im.height * 4 for im in self._equations.values())
        if cost <= 32 * 1024**2:
            while self._equations and total + cost > 32 * 1024**2:
                old = self._equations.pop(next(iter(self._equations)))
                total -= old.width * old.height * 4
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

    def _caption_layout(self, c: Captions, factor: float, phrase):
        # Authoring can resize/reflow captions between measurements. A reusable
        # service must key metric inputs, rather than a mutable component id.
        key = (c.font, c.font_size, getattr(c, "font_weight", None), c.width, c.spacing, factor, phrase)
        if key in self._caption_layouts:
            self._caption_layouts.move_to_end(key)
            return self._caption_layouts[key]
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
        layout = (font, width, lines, ascent, step)
        if self._caption_cache_limit:
            if len(self._caption_layouts) >= 128:
                self._caption_layouts.popitem(last=False)
            self._caption_layouts[key] = layout
        return layout


_sessions = local()


def measurement_session():
    """Thread-owned CPU metrics; contains no rendering/native viewport sessions."""
    if not hasattr(_sessions, "measurement"):
        _sessions.measurement = Measurement()
    return _sessions.measurement
