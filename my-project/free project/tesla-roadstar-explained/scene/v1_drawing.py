"""Crisp v1 typography and analytical plots; all coordinates retain source data."""

from functools import lru_cache
from math import ceil, floor

import numpy as np
from matplotlib.backends.backend_agg import RendererAgg
from matplotlib.path import Path
from matplotlib.transforms import IdentityTransform
from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFont

from faceless_champ import Canvas, Equation, Scene

from . import DISPLAY_FONT, FONT, REPO
from . import physics as p
from .drawing import Painter
from .timing import shot_at

PALETTE = {
    "white": "#F5F8FF",
    "muted": "#A6B5CA",
    "dim": "#233147",
    "cyan": "#67DFFF",
    "blue": "#70A7FF",
    "purple": "#A5ACFF",
    "amber": "#FF7385",
    "green": "#6DE3D1",
    "orange": "#FFAE70",
    "red": "#FF516B",
}


@lru_cache(maxsize=256)
def label_font(size, display=False, greek=False):
    path = REPO / "src/faceless_champ/assets/DejaVuSans.ttf" if greek else (DISPLAY_FONT if display else FONT)
    face = ImageFont.truetype(str(path), max(8, size))
    if not greek:
        face.set_variation_by_axes(
            [
                (650 if display else 550) if axis["name"].lower() == b"weight" else axis["default"]
                for axis in face.get_variation_axes()
            ]
        )
    return face


class V1Painter(Painter):
    def _sprite(self, sprite, position, alpha=1, reveal=1):
        if self.measure_only or alpha <= 0 or reveal <= 0:
            return
        if alpha < 1 or reveal < 1:
            sprite = sprite.copy()
            mask = sprite.getchannel("A")
            if reveal < 1:
                # A soft leading edge reveals the whole typeset expression without
                # reflow, per-letter jitter, or changing the final glyph weight.
                feather = max(1, 36 * self.scale)
                edge = (sprite.width + feather) * reveal
                ramp = np.clip((edge - np.arange(sprite.width)) / feather, 0, 1)
                wipe = Image.fromarray(np.uint8(np.broadcast_to(ramp * 255, (sprite.height, sprite.width))))
                mask = ImageChops.multiply(mask, wipe)
            if alpha < 1:
                mask = mask.point(lambda value: round(value * alpha))
            sprite.putalpha(mask)
        self.image.alpha_composite(sprite, self.xy(position))

    def text(self, value, xy, size=28, color="white", display=False, width=None, alpha=1, anchor="lt", tag=""):
        if alpha <= 0:
            return
        value = str(value)
        greek = any("\u0370" <= char <= "\u03ff" for char in value)
        sample = max(1, 2 / self.scale)
        density = self.scale * sample
        face = label_font(round(size * density), display, greek)
        while width and face.getlength(value) > width * density and size > 22:
            size -= 1
            face = label_font(round(size * density), display, greek)
        bounds = face.getbbox(value, anchor=anchor)
        x, y = xy[0] + bounds[0] / density, xy[1] + bounds[1] / density
        w, h = bounds[2] - bounds[0], bounds[3] - bounds[1]
        self.boxes.append({"tag": tag or value, "bounds": [x, y, x + w / density, y + h / density], "font_size": size})
        if self.measure_only or not w or not h:
            return
        sprite = Image.new("RGBA", (w + 4, h + 4))
        ImageDraw.Draw(sprite).text(
            (2 - bounds[0], 2 - bounds[1]), value, font=face, fill=PALETTE.get(color, color), anchor=anchor
        )
        sprite = sprite.resize(
            (max(1, round(sprite.width / sample)), max(1, round(sprite.height / sample))), Image.Resampling.LANCZOS
        )
        self._sprite(sprite, (x - 2 / density, y - 2 / density), alpha)

    def equation(
        self, expression, xy, size=64, width=800, color="white", alpha=1, tag="equation", anchor="lt", reveal=1
    ):
        if alpha <= 0:
            return
        color = PALETTE.get(color, color)
        density = max(2, self.scale)
        key = ("v1-sharp", expression, size, width, color, self.scale)
        if key not in self.math_cache:
            equation = Equation(
                expression, fontset="stix", font_size=size, max_width=width, color=color, position=(900, 150)
            )
            scene = Scene(Canvas(1800, 300, "#00000000")).add(equation).wait(1)
            sprite = self.math_renderer.frame(scene, 0, (round(1800 * density), round(300 * density)))
            bbox = sprite.getbbox()
            if not bbox:
                raise ValueError(f"Empty equation: {expression}")
            sprite = sprite.crop(bbox)
            target = tuple(max(1, round(v * self.scale / density)) for v in sprite.size)
            if sprite.size != target:
                sprite = sprite.resize(target, Image.Resampling.LANCZOS)
            self.math_cache[key] = sprite
        sprite = self.math_cache[key]
        w, h = sprite.width / self.scale, sprite.height / self.scale
        x, y = xy
        x -= w / 2 if anchor[0] == "m" else w if anchor[0] == "r" else 0
        y -= h / 2 if anchor[1] == "m" else 0
        self._sprite(sprite, (x, y), alpha, reveal)
        bounds = [x, y, x + w, y + h]
        self.boxes.append({"tag": tag, "bounds": bounds, "font_size": size})
        return bounds

    def line(self, points, color="dim", width=1.5, alpha=1, dash=False):
        if self.measure_only or alpha <= 0 or len(points) < 2:
            return
        # AGG strokes floating-point paths with true antialiased joins. Pillow's
        # integer segment rasterizer produced uneven weight even with dense data.
        # No fitted splines can overshoot analytical corners or physical steps.
        points = np.asarray(points, dtype=float) * self.scale
        stroke = width * self.scale
        pad = ceil(stroke / 2) + 3
        x0, y0 = (floor(v) - pad for v in points.min(axis=0))
        x1, y1 = (ceil(v) + pad for v in points.max(axis=0))
        x0, y0 = max(-pad, x0), max(-pad, y0)
        x1, y1 = min(self.size[0] + pad, x1), min(self.size[1] + pad, y1)
        if x1 <= x0 or y1 <= y0:
            return
        renderer = RendererAgg(x1 - x0, y1 - y0, 72)
        points -= (x0, y0)
        points[:, 1] = y1 - y0 - points[:, 1]
        gc = renderer.new_gc()
        rgb = tuple(value / 255 for value in ImageColor.getrgb(PALETTE.get(color, color)))
        gc.set_foreground((*rgb, alpha))
        gc.set_linewidth(stroke)
        gc.set_antialiased(True)
        gc.set_capstyle("round")
        gc.set_joinstyle("round")
        if dash:
            gc.set_dashes(0, [5 * self.scale, 7 * self.scale])
        renderer.draw_path(gc, Path(points), IdentityTransform())
        gc.restore()
        tile = Image.fromarray(np.asarray(renderer.buffer_rgba()))
        self.image.alpha_composite(tile, (x0, y0))

    def circle(self, center, radius, color="cyan", width=2, fill=None):
        if self.measure_only:
            return
        # A tiny supersampled sprite also keeps the physical cursor crisp.
        density = max(2, self.scale * 2)
        pad = 2 / density
        extent = radius + width / 2 + pad
        side = ceil(2 * extent * density)
        sprite = Image.new("RGBA", (side, side))
        inset = (width / 2 + pad) * density
        ImageDraw.Draw(sprite).ellipse(
            (inset, inset, side - inset, side - inset),
            outline=PALETTE.get(color, color),
            width=max(1, round(width * density)),
            fill=PALETTE.get(fill, fill),
        )
        side = max(1, round(side * self.scale / density))
        sprite = sprite.resize((side, side), Image.Resampling.LANCZOS)
        self._sprite(sprite, (center[0] - extent, center[1] - extent))

    def graph(self, rect, series, xlim, ylim, xlabel, ylabel, cursor=None, shade=None, ticks=4, legend=True):
        x, y, w, h = rect
        compact = h < 300
        left, right = x + 72, x + w - 24
        top, bottom = y + (42 if compact else 66), y + h - (48 if compact else 62)

        def point(a, b):
            return (
                left + (a - xlim[0]) / (xlim[1] - xlim[0]) * (right - left),
                bottom - (b - ylim[0]) / (ylim[1] - ylim[0]) * (bottom - top),
            )

        if shade and not self.measure_only:
            self.draw.rectangle(
                (*self.xy((point(shade[0], 0)[0], top)), *self.xy((point(shade[1], 0)[0], bottom))), fill="#06121C"
            )
        for value in np.linspace(*ylim, ticks + 1):
            py = point(xlim[0], value)[1]
            self.line([(left, py), (right, py)], "dim", 1, alpha=0.65)
            self.text(f"{value:.3g}", (left - 16, py), 23, "muted", anchor="rm")
        for value in np.linspace(*xlim, ticks + 1):
            px = point(value, ylim[0])[0]
            self.line([(px, bottom), (px, bottom + 5)], "muted", 1)
            self.text(f"{value:.3g}", (px, bottom + 12), 22, "muted", anchor="mt")
        self.line([(left, top), (left, bottom), (right, bottom)], "muted", 1.2, alpha=0.8)
        if ylabel:
            self.equation(ylabel, (left, y), size=30, width=220, color="white")
        if xlabel:
            self.equation(xlabel, (right, bottom + 38), size=25, width=160, color="muted", anchor="rt")
        chapter = shot_at(self.time).chapter
        entry = {
            3: 108.28,
            5: 275.82,
            6: 404.56,
            7: 444.16,
            9: 629.88 if self.time >= 629.88 else 605.84 if self.time >= 605.84 else 589.12,
        }.get(chapter, 0)
        reveal = p.smooth(p.progress(self.time, entry, entry + 0.85))
        frontier = xlim[0] + (xlim[1] - xlim[0]) * reveal
        if cursor is not None:
            cursor = float(np.clip(cursor, *xlim))
            px = point(cursor, ylim[0])[0]
            self.line([(px, top), (px, bottom)], "muted", 1, alpha=0.55, dash=True)
        for index, (name, xs, ys, color) in enumerate(series):
            pairs = [(a, b) for a, b in zip(xs, ys) if xlim[0] <= a <= min(frontier, xlim[1])]
            if pairs and pairs[-1][0] < frontier <= xs[-1]:
                pairs.append((frontier, float(np.interp(frontier, xs, ys))))
            self.line([point(a, b) for a, b in pairs], color, 3.2)
            if legend:
                lx = left + 235 + index * 205
                self.line([(lx, y + 17), (lx + 25, y + 17)], color, 3.2)
                self.equation(name, (lx + 36, y + 17), size=28, width=160, color=color, anchor="lm")
            if cursor is not None and cursor <= frontier:
                q = point(cursor, float(np.interp(cursor, xs, ys)))
                self.circle(q, 6, color, 2, fill="#000000")
                self.circle(q, 2, "white", 1, fill="white")
        return point
