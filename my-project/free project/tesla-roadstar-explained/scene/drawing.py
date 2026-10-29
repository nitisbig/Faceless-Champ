"""Resolution-independent scientific composition with core MathText typesetting."""

import itertools
from functools import lru_cache
from math import atan2, cos, sin

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

from faceless_champ import Canvas, Equation, Scene

from . import DISPLAY_FONT, FONT, REPO

C = {
    "white": "#F3F6FF",
    "muted": "#99ABC6",
    "dim": "#172536",
    "cyan": "#78BEFF",
    "blue": "#3886FF",
    "purple": "#548FFF",
    "amber": "#FF526A",
    "green": "#A0D0FF",
    "orange": "#FF304F",
    "red": "#FF2649",
}


@lru_cache(maxsize=512)
def font(size, display=False, greek=False):
    path = REPO / "src/faceless_champ/assets/DejaVuSans.ttf" if greek else (DISPLAY_FONT if display else FONT)
    result = ImageFont.truetype(str(path), max(8, int(size)))
    if greek:
        return result
    axes = result.get_variation_axes()
    values = [500 if axis["name"].lower() == b"weight" else axis["default"] for axis in axes]
    result.set_variation_by_axes(values)
    return result


@lru_cache(maxsize=4)
def backdrop(size):
    """Keep the stage exactly black; only authored objects emit light."""
    return Image.new("RGBA", size, "#000000")


class Painter:
    def __init__(self, size, math_renderer, math_cache, measure_only=False, time=0):
        self.size = size
        self.scale = size[0] / 1920
        self.measure_only = measure_only
        self.time = time
        self.image = Image.new("RGBA", (1, 1), "black") if measure_only else backdrop(size).copy()
        self.draw = ImageDraw.Draw(self.image)
        self.glow = Image.new("RGBA", self.image.size)
        self.glow_draw = ImageDraw.Draw(self.glow)
        self.math_renderer = math_renderer
        self.math_cache = math_cache
        self.boxes = []

    def xy(self, point):
        return tuple(round(v * self.scale) for v in point)

    def text(self, value, xy, size=28, color="white", display=False, width=None, alpha=1, anchor="lt", tag=""):
        if alpha <= 0:
            return
        value = str(value)
        color = C.get(color, color)
        greek = any("\u0370" <= c <= "\u03ff" for c in value)
        f = font(round(size * self.scale), display, greek)
        if width:
            while f.getlength(value) > width * self.scale and size > 22:
                size -= 1
                f = font(round(size * self.scale), display, greek)
        position = self.xy(xy)
        from PIL import ImageColor

        rgba = ImageColor.getrgb(color) + (round(255 * alpha),)
        if not self.measure_only:
            self.draw.text(position, value, font=f, fill=rgba, anchor=anchor)
        box = self.draw.textbbox(position, value, font=f, anchor=anchor)
        self.boxes.append({"tag": tag or value, "bounds": [v / self.scale for v in box], "font_size": size})

    def line(self, points, color="dim", width=1.5, alpha=1, dash=False):
        if self.measure_only:
            return
        from PIL import ImageColor

        rgb = ImageColor.getrgb(C.get(color, color)) + (round(255 * alpha),)
        points = [self.xy(p) for p in points]
        width = max(1, round(width * self.scale))
        if dash:
            for a, b in itertools.pairwise(points):
                a, b = np.asarray(a), np.asarray(b)
                length = np.linalg.norm(b - a)
                for start in np.arange(0, length, 14 * self.scale):
                    end = min(length, start + 7 * self.scale)
                    self.draw.line(
                        [tuple(a + (b - a) * start / max(length, 1)), tuple(a + (b - a) * end / max(length, 1))],
                        fill=rgb,
                        width=width,
                    )
        else:
            self.draw.line(points, fill=rgb, width=width, joint="curve")
        if color not in {"dim", "muted"} and alpha > 0.2:
            self.glow_draw.line(points, fill=rgb[:3] + (round(85 * alpha),), width=max(2, width * 3), joint="curve")

    def circle(self, center, radius, color="cyan", width=2, fill=None):
        if self.measure_only:
            return
        x, y = center
        box = (*self.xy((x - radius, y - radius)), *self.xy((x + radius, y + radius)))
        self.draw.ellipse(
            box, outline=C.get(color, color), width=max(1, round(width * self.scale)), fill=C.get(fill, fill)
        )
        if color not in {"dim", "muted"}:
            self.glow_draw.ellipse(box, outline=C.get(color, color), width=max(2, round(width * 2 * self.scale)))

    def arrow(self, start, end, color="cyan", label=None, width=3, dash=False, label_offset=(12, -15)):
        self.line([start, end], color, width, dash=dash)
        angle = atan2(end[1] - start[1], end[0] - start[0])
        head = 13
        self.line(
            [
                (end[0] - head * cos(angle - 0.46), end[1] - head * sin(angle - 0.46)),
                end,
                (end[0] - head * cos(angle + 0.46), end[1] - head * sin(angle + 0.46)),
            ],
            color,
            width,
        )
        if label:
            self.text(label, (end[0] + label_offset[0], end[1] + label_offset[1]), 27, color, width=280)

    def paste(self, image, rect, alpha=1, fit="contain", glow=False):
        x, y, w, h = rect
        target = self.xy((w, h))
        if self.measure_only:
            if fit == "cover":
                return rect
            factor = min(target[0] / image.width, target[1] / image.height)
            iw, ih = round(image.width * factor) / self.scale, round(image.height * factor) / self.scale
            return (x + (w - iw) / 2, y + (h - ih) / 2, iw, ih)
        image = image if image.mode == "RGBA" else image.convert("RGBA")
        if fit == "cover":
            if image.size != target:
                image = ImageOps.fit(image, target, method=Image.Resampling.LANCZOS)
        else:
            factor = min(target[0] / image.width, target[1] / image.height)
            new_size = (max(1, round(image.width * factor)), max(1, round(image.height * factor)))
            if image.size != new_size:
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            x += (w - image.width / self.scale) / 2
            y += (h - image.height / self.scale) / 2
        if alpha < 1:
            image = image.copy()
            image.putalpha(image.getchannel("A").point(lambda v: round(v * alpha)))
        self.image.alpha_composite(image, self.xy((x, y)))
        if glow:
            pixels = np.asarray(image)
            rgb = pixels[:, :, :3].astype(np.int16)
            mask = ((rgb.max(2) - rgb.min(2) > 60) & (rgb.max(2) > 145)).astype(np.uint8)
            emission = image.copy()
            emission.putalpha(Image.fromarray((mask.astype(np.uint16) * pixels[:, :, 3] // 2).astype(np.uint8)))
            self.glow.alpha_composite(emission, self.xy((x, y)))
        return (x, y, image.width / self.scale, image.height / self.scale)

    def equation(self, expression, xy, size=64, width=800, color="white", alpha=1, tag="equation", anchor="lt"):
        if alpha <= 0:
            return
        key = (expression, size, width, C.get(color, color), round(self.scale, 4))
        if key not in self.math_cache:
            equation = Equation(
                expression,
                fontset="stix",
                font_size=size,
                max_width=width,
                color=C.get(color, color),
                position=(900, 150),
            )
            scene = Scene(Canvas(1800, 300, "#00000000")).add(equation).wait(1)
            sprite = self.math_renderer.frame(scene, 0, self.xy((1800, 300)))
            bbox = sprite.getbbox()
            if not bbox:
                raise ValueError(f"Empty equation: {expression}")
            self.math_cache[key] = sprite.crop(bbox)
        sprite = self.math_cache[key]
        x, y = xy
        if anchor[0] == "m":
            x -= sprite.width / self.scale / 2
        elif anchor[0] == "r":
            x -= sprite.width / self.scale
        if anchor[1] == "m":
            y -= sprite.height / self.scale / 2
        if alpha < 1:
            sprite = sprite.copy()
            sprite.putalpha(sprite.getchannel("A").point(lambda v: round(v * alpha)))
        if not self.measure_only:
            self.image.alpha_composite(sprite, self.xy((x, y)))
            halo = sprite.copy()
            halo.putalpha(halo.getchannel("A").point(lambda v: round(v * (0.09 + 0.025 * sin(self.time * 2)))))
            self.glow.alpha_composite(halo, self.xy((x, y)))
        self.boxes.append(
            {
                "tag": tag,
                "bounds": [x, y, x + sprite.width / self.scale, y + sprite.height / self.scale],
                "font_size": size,
            }
        )
        return self.boxes[-1]["bounds"]

    def finish(self):
        if self.measure_only:
            return self.image.convert("RGB")
        small = (max(1, self.size[0] // 3), max(1, self.size[1] // 3))
        halo = self.glow.resize(small, Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(3.2 * self.scale))
        halo = halo.resize(self.size, Image.Resampling.BILINEAR)
        black = Image.new("RGBA", self.size, "black")
        return ImageChops.add(
            Image.alpha_composite(black, self.image).convert("RGB"), Image.alpha_composite(black, halo).convert("RGB")
        )

    def arc(self, center, radius, start=0, end=6.283185, color="cyan", width=2, alpha=1, squash=1):
        angles = np.linspace(start, end, max(8, round(abs(end - start) * 20)))
        self.line(
            [(center[0] + radius * cos(a), center[1] + radius * sin(a) * squash) for a in angles], color, width, alpha
        )

    def matrix(self, entries, xy, cell=(130, 75), color="cyan", size=42):
        """STIX cells and vector brackets avoid an external TeX installation."""
        x, y = xy
        columns, rows = len(entries[0]), len(entries)
        w, h = cell[0] * columns, cell[1] * rows
        for edge, direction in ((x - 15, 1), (x + w + 2, -1)):
            self.line(
                [
                    (edge + direction * 14, y - 9),
                    (edge, y - 9),
                    (edge, y + h - 10),
                    (edge + direction * 14, y + h - 10),
                ],
                color,
                2.3,
            )
        active = int(self.time * 2.6) % (columns * rows)
        for row, values in enumerate(entries):
            for col, value in enumerate(values):
                self.equation(
                    value,
                    (x + (col + 0.5) * cell[0], y + (row + 0.5) * cell[1] - 10),
                    size=size,
                    width=cell[0] - 18,
                    color=color if row * columns + col == active else "white",
                    tag=f"matrix-{x}-{row}-{col}",
                    anchor="mm",
                )
        return x - 15, y - 9, w + 32, h

    def graph(self, rect, series, xlim, ylim, xlabel, ylabel, cursor=None, shade=None, ticks=4, legend=True):
        """Analytical series and marker share one explicitly defined coordinate map."""
        x, y, w, h = rect
        left, top, right, bottom = x + 65, y + 48, x + w - 24, y + h - 60
        if legend:
            top += 12

        def point(a, b):
            return (
                left + (a - xlim[0]) / (xlim[1] - xlim[0]) * (right - left),
                bottom - (b - ylim[0]) / (ylim[1] - ylim[0]) * (bottom - top),
            )

        if shade and not self.measure_only:
            a, b = shade
            xx1, xx2 = point(a, 0)[0], point(b, 0)[0]
            self.draw.rectangle((*self.xy((xx1, top)), *self.xy((xx2, bottom))), fill="#030A14")
        for v in np.linspace(ylim[0], ylim[1], ticks + 1):
            py = point(xlim[0], v)[1]
            self.line([(left, py), (right, py)], "dim", 1, alpha=0.5)
            self.text(f"{v:.3g}", (left - 15, py), 23, "muted", anchor="rm")
        for v in np.linspace(xlim[0], xlim[1], ticks + 1):
            px = point(v, ylim[0])[0]
            self.line([(px, top), (px, bottom)], "dim", 1, alpha=0.35)
            self.text(f"{v:.3g}", (px, bottom + 12), 23, "muted", anchor="mt")
        self.line([(left, top), (left, bottom), (right, bottom)], "muted", 1.5)
        if ylabel:
            self.equation(ylabel, (left, y), size=31, width=w - 90, color="muted")
        if xlabel:
            self.equation(xlabel, (right - 100, bottom + 36), size=28, width=125, color="muted")
        legendx = left + 190
        for index, (name, xs, ys, color) in enumerate(series):
            points = [point(a, b) for a, b in zip(xs, ys) if xlim[0] - 1e-8 <= a <= xlim[1] + 1e-8]
            self.line(points, color, 2.8, alpha=0.75)
            if points:
                head = (self.time * 0.19 + index * 0.41) % 1
                count = len(points)
                a, b = max(0, int((head - 0.2) * count)), min(count, int(head * count) + 1)
                self.line(points[a:b], color, 4.2)
                self.circle(points[min(count - 1, int(head * count))], 3.5, color, fill="white")
            if legend:
                self.line([(legendx, y + 18), (legendx + 25, y + 18)], color, 3)
                self.equation(name, (legendx + 34, y + 4), size=29, width=170, color=color)
                legendx += 220
            if cursor is not None:
                value = float(np.interp(cursor, xs, ys))
                q = point(float(np.clip(cursor, *xlim)), value)
                self.circle(q, 5, color, 2, fill=color)
                self.circle(q, 10 + 2 * sin(self.time * 4), color, 1)
        if cursor is not None:
            xx = point(cursor, ylim[0])[0]
            self.line([(xx, top), (xx, bottom)], "white", 1, alpha=0.7, dash=True)
        return point

    def meter(self, xy, label, value, unit, color="cyan", width=300):
        x, y = xy
        self.text(label, (x, y), 24, "muted", width=width)
        self.text(f"{value} {unit}".strip(), (x, y + 35), 42, color, display=True, width=width)

    def bracket(self, a, b, label, color="muted"):
        self.line([a, b], color, 1.7)
        for x, y in (a, b):
            self.line([(x - 7, y), (x + 7, y)], color, 1.7)
        self.text(label, ((a[0] + b[0]) / 2 + 15, (a[1] + b[1]) / 2), 26, color, anchor="lm")
