"""Pillow frame renderer with asset caches and bounded frame memory."""

from __future__ import annotations

import math
from itertools import pairwise
from pathlib import Path
from typing import Protocol

from PIL import Image as PILImage
from PIL import ImageColor, ImageDraw, ImageFont, ImageOps

from .components import Circle, Image, Line, Shape, Text, Triangle
from .timeline import Grid, Renderable, Scene, Sequence


class Renderer(Protocol):
    def validate(self, node: Renderable) -> None: ...
    def frame(self, node: Renderable, time: float, size: tuple[int, int]) -> PILImage.Image: ...


class PillowRenderer:
    def __init__(self, antialias: int = 2):
        if antialias not in (1, 2, 3, 4):
            raise ValueError("antialias must be 1, 2, 3, or 4")
        self.antialias = antialias
        self._images = {}
        self._fonts = {}
        self._sprites = {}

    def _font(self, component: Text, size: int):
        path = component.font or str(Path(__file__).parent / "assets" / "DejaVuSans.ttf")
        key = (path, size)
        if key not in self._fonts:
            try:
                self._fonts[key] = ImageFont.truetype(path, size)
            except OSError as exc:
                raise ValueError(f"Cannot load font: {path}") from exc
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
        if not isinstance(node, (Scene, Sequence, Grid)):
            raise TypeError("Expected Scene, Sequence, or Grid")
        ImageColor.getcolor(node.canvas.bg, "RGBA")
        _ = node.duration
        if isinstance(node, Scene):
            for entry in node.entries:
                c = entry.component
                if isinstance(c, Text):
                    self._font(c, round(c.font_size))
                    ImageColor.getcolor(c.color, "RGBA")
                elif isinstance(c, Image):
                    self._image(c.path)
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
            cw = (node.canvas.width - node.gap * (node.columns - 1)) / node.columns
            ch = (node.canvas.height - node.gap * (node.rows - 1)) / node.rows
            for i, child in enumerate(node.children):
                col, row = i % node.columns, i // node.columns
                x, y = round(col * (cw + node.gap) * sx), round(row * (ch + node.gap) * sy)
                right, bottom = round((col * (cw + node.gap) + cw) * sx), round((row * (ch + node.gap) + ch) * sy)
                cell = self._fit(
                    child, min(time, child.duration), (max(1, right - x), max(1, bottom - y)), node.canvas.bg
                )
                background.alpha_composite(cell, (x, y))
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
        aa = self.antialias
        big = (size[0] * aa, size[1] * aa)
        result = PILImage.new("RGBA", big, scene.canvas.bg)
        factor = min(big[0] / scene.canvas.width, big[1] / scene.canvas.height)
        for entry in sorted(scene.entries, key=lambda e: e.component.z_index):
            if time < entry.start:
                continue
            state = entry.state_at(time)
            if state["opacity"] <= 0:
                continue
            c = entry.component
            sprite = self._sprite(c, state, factor, max(0, time - entry.start))
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
        return result

    def _sprite(self, c, state, factor, age):
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
        if isinstance(c, Text):
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
            if c.fit == "cover":
                sprite = ImageOps.fit(source, size, method=PILImage.Resampling.LANCZOS)
            else:
                fit = ImageOps.contain(source, size, method=PILImage.Resampling.LANCZOS)
                sprite = PILImage.new("RGBA", size)
                sprite.alpha_composite(fit, ((size[0] - fit.width) // 2, (size[1] - fit.height) // 2))
        else:
            width = max(1, round(c.stroke_width * factor))
            w, h = max(1, round(c.width * factor)), max(1, round(c.height * factor))
            sprite = PILImage.new("RGBA", (w + width * 2, h + width * 2))
            draw = ImageDraw.Draw(sprite)
            x, y = width, width
            if isinstance(c, Circle):
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
            if c.fill and not isinstance(c, Line) and progress >= 1:
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
        if static:
            self._sprites[key] = sprite
        return sprite
