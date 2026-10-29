"""V2 motion typography and scientific graphics, rendered without external TeX."""

from math import cos, pi, sin

import numpy as np
from PIL import ImageDraw

from . import physics as p
from .drawing import Painter
from .timing import shot_at


class V2Painter(Painter):
    def polygon(self, points, color):
        if not self.measure_only:
            self.draw.polygon([self.xy(q) for q in points], fill=color)

    def layer(self):
        layer = type(self)(self.size, self.math_renderer, self.math_cache, self.measure_only, self.time)
        if not self.measure_only:
            layer.image.paste((0, 0, 0, 0), (0, 0, *layer.size))
            layer.draw = ImageDraw.Draw(layer.image)
        return layer

    def composite(self, layer, alpha=1, offset=(0, 0)):
        if alpha <= 0:
            return
        if not self.measure_only:
            for destination, source in ((self.image, layer.image), (self.glow, layer.glow)):
                source = source.copy()
                source.putalpha(source.getchannel("A").point(lambda v: round(v * alpha)))
                destination.alpha_composite(source, self.xy(offset))
        for item in layer.boxes:
            x0, y0, x1, y1 = item["bounds"]
            self.boxes.append(dict(item, bounds=[x0 + offset[0], y0 + offset[1], x1 + offset[0], y1 + offset[1]]))

    def formula(self, expression, center=(960, 934), size=92, width=1660, alpha=1, tag="formula"):
        """Optically centered relation with measured STIX terms on one math axis."""
        # Split only complete top-level equals relations. Other relations retain
        # MathText's own spacing and typography, including nested fractions.
        if "=" not in expression or r"\Rightarrow" in expression:
            return self.equation(expression, center, size=size, width=width, anchor="mm", alpha=alpha, tag=tag)
        lhs, rhs = expression.split("=", 1)
        tokens = (lhs, "=", rhs)
        colors = ("cyan", "muted", "white")
        measuring = self.measure_only
        measured = []
        try:
            self.measure_only = True
            for token in tokens:
                box = self.equation(token, (0, 0), size=size, width=width)
                measured.append(box[2])
                self.boxes.pop()
        finally:
            self.measure_only = measuring
        gap = 22
        factor = min(1, width / (sum(measured) + gap * 2))
        x = center[0] - (sum(measured) + gap * 2) * factor / 2
        for token, color, length in zip(tokens, colors, measured):
            self.equation(
                token,
                (x, center[1]),
                size=size * factor,
                width=width,
                color=color,
                anchor="lm",
                alpha=alpha,
                tag=tag,
            )
            x += (length + gap) * factor

    def graph(self, rect, series, xlim, ylim, xlabel="", ylabel="", cursor=None, shade=None, ticks=4, legend=True):
        x, y, w, h = rect
        compact = h < 300
        left, right = x + 72, x + w - 24
        top, bottom = y + (40 if compact else 78), y + h - (45 if compact else 65)

        def point(a, b):
            return (
                left + (a - xlim[0]) / (xlim[1] - xlim[0]) * (right - left),
                bottom - (b - ylim[0]) / (ylim[1] - ylim[0]) * (bottom - top),
            )

        if shade:
            self.polygon(
                [
                    (point(shade[0], 0)[0], top),
                    (point(shade[1], 0)[0], top),
                    (point(shade[1], 0)[0], bottom),
                    (point(shade[0], 0)[0], bottom),
                ],
                "#040B17",
            )
        for value in np.linspace(*ylim, ticks + 1):
            py = point(xlim[0], value)[1]
            self.line([(left, py), (right, py)], "dim", 1, alpha=0.55)
            self.equation(f"{value:.3g}", (left - 18, py), size=24, width=65, color="muted", anchor="rm")
        for value in np.linspace(*xlim, ticks + 1):
            px = point(value, ylim[0])[0]
            self.line([(px, bottom), (px, bottom + 5)], "muted", 1)
            self.equation(f"{value:.3g}", (px, bottom + 22), size=23, width=75, color="muted", anchor="mm")
        self.line([(left, top), (left, bottom), (right, bottom)], "blue", 1.6, alpha=0.75)
        self.equation(ylabel, (left, y), size=30 if compact else 34, width=310, color="white") if ylabel else None
        if xlabel:
            self.equation(xlabel, (right, bottom + 46), size=26, width=180, color="muted", anchor="rm")
        elapsed = self.time - shot_at(self.time).start
        reveal = p.smooth(p.progress(elapsed, 0.15, 1.05))
        for index, (name, xs, ys, color) in enumerate(series):
            pairs = [(a, b) for a, b in zip(xs, ys) if xlim[0] <= a <= xlim[1]]
            points = [point(a, b) for a, b in pairs]
            if len(points) < 2:
                continue
            self.line(points, color, 1.5, alpha=0.18)
            visible = points[: max(2, round(len(points) * reveal))]
            self.line(visible, color, 3.5, alpha=0.95)
            # A short light packet follows the relation; the larger ring is the
            # actual physical cursor. The curve's data never oscillates.
            phase = (self.time * 0.13 + index * 0.37) % 1
            head = min(len(visible) - 1, int(phase * len(visible)))
            self.line(visible[max(0, head - 8) : head + 1], "white", 1.7, alpha=0.7)
            if legend:
                lx = left + 245 + index * 205
                self.line([(lx, y + 21), (lx + 23, y + 21)], color, 3)
                self.equation(name, (lx + 34, y + 21), size=28, width=165, color=color, anchor="lm")
            if cursor is not None:
                value = float(np.interp(cursor, xs, ys))
                q = point(float(np.clip(cursor, *xlim)), value)
                self.circle(q, 6, color, 2, fill="white")
                self.arc(q, 13, self.time * 1.6, self.time * 1.6 + pi * 1.45, color, 1.5)
        if cursor is not None:
            px = point(float(np.clip(cursor, *xlim)), ylim[0])[0]
            self.line([(px, top), (px, bottom)], "white", 1, alpha=0.4, dash=True)
        return point

    def matrix(self, entries, xy, cell=(130, 75), color="cyan", size=42):
        x, y = xy
        rows, columns = len(entries), len(entries[0])
        w, h = columns * cell[0], rows * cell[1]
        for edge, direction in ((x - 12, 1), (x + w + 12, -1)):
            self.line([(edge + 18 * direction, y), (edge, y), (edge, y + h), (edge + 18 * direction, y + h)], color, 3)
        for row, values in enumerate(entries):
            for col, value in enumerate(values):
                cx, cy = x + (col + 0.5) * cell[0], y + (row + 0.5) * cell[1]
                if row == col:
                    self.polygon(
                        [
                            (cx - cell[0] * 0.44, cy - cell[1] * 0.39),
                            (cx + cell[0] * 0.44, cy - cell[1] * 0.39),
                            (cx + cell[0] * 0.44, cy + cell[1] * 0.39),
                            (cx - cell[0] * 0.44, cy + cell[1] * 0.39),
                        ],
                        "#07172D",
                    )
                    self.line([(cx - 24, cy + cell[1] * 0.39), (cx + 24, cy + cell[1] * 0.39)], "red", 2)
                self.equation(
                    value,
                    (cx, cy),
                    size=size,
                    width=cell[0] - 24,
                    color="white" if row == col else "muted",
                    anchor="mm",
                )
        # A single rim light moves around the bracket; numerical entries stay fixed.
        phase = (self.time * 0.24) % 1
        cy = y + phase * h
        self.line([(x - 12, max(y, cy - 30)), (x - 12, cy)], "white", 2)

    def fan(self, center, radius):
        x, y = center
        self.circle(center, radius, "blue", 2.8)
        self.circle(center, radius * 0.83, "dim", 1.5)
        for i in range(9):
            a = self.time * 4 + i * 2 * pi / 9
            points = [
                (x + r * cos(a + offset), y + r * sin(a + offset))
                for r, offset in (
                    (radius * 0.18, 0),
                    (radius * 0.75, 0.13),
                    (radius * 0.78, 0.32),
                    (radius * 0.24, 0.23),
                )
            ]
            self.polygon(points, "#153A65")
            self.line(points[:3], "cyan", 2)
        self.circle(center, radius * 0.16, "cyan", 2, fill="#061020")
        self.arc(center, radius + 10, -self.time, -self.time + pi * 0.6, "red", 3)
