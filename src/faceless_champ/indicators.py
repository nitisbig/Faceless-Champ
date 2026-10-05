"""Lightweight progress components with explicit, deterministic progress."""

import math
from itertools import pairwise

from PIL import Image, ImageDraw

from .components import Component, Number, finite
from .motion import rgba


class ProgressBar(Component):
    def __init__(
        self,
        *,
        progress=0,
        width=240,
        height=20,
        color="#48e0cb",
        track_color="#26354a",
        stroke_width=10,
        label=False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.progress = finite(progress, "progress", 0)
        if self.progress > 1:
            raise ValueError("progress must be <= 1")
        self.width, self.height = finite(width, "width", 1), finite(height, "height", 1)
        self.stroke_width = finite(stroke_width, "stroke_width", 1)
        self.color, self.track_color = rgba(color), rgba(track_color)
        self.label = bool(label)

    def state(self):
        return {**super().state(), "progress": self.progress}


class ProgressRing(ProgressBar):
    def __init__(self, *, width=120, height=120, **kwargs):
        super().__init__(width=width, height=height, **kwargs)


class Gauge(ProgressRing):
    """A semicircular gauge, empty at 0 and full at 1."""


class LoadingDots(ProgressBar):
    """Three dots; animate progress 0 to 1 and Repeat for a seamless cycle."""

    def __init__(self, *, width=100, height=24, **kwargs):
        super().__init__(width=width, height=height, **kwargs)


class Checkmark(ProgressBar):
    def __init__(self, *, width=80, height=80, **kwargs):
        super().__init__(width=width, height=height, **kwargs)


class Countdown(Number):
    """Nonnegative numeric countdown; animate value_to(0) with explicit timing."""

    def __init__(self, seconds, **kwargs):
        kwargs.setdefault("formatter", lambda value: str(math.ceil(max(0, value))))
        super().__init__(finite(seconds, "seconds", 0), **kwargs)


def draw_indicator(c, state, factor, renderer):
    w, h = max(1, round(c.width * factor)), max(1, round(c.height * factor))
    sprite = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(sprite)
    p = state["progress"]
    stroke = min(w, h, max(1, round(c.stroke_width * factor)))
    color, track = c.color, c.track_color
    if isinstance(c, LoadingDots):
        radius = min(h / 2, w / 8)
        for i in range(3):
            x, y = w * (i + 1) / 4, h / 2
            alpha = 0.25 + 0.75 * (0.5 + 0.5 * math.cos(math.tau * (p - i / 3)))
            fill = (*color[:3], round(color[3] * alpha))
            d.ellipse((x - radius, y - radius, x + radius - 1, y + radius - 1), fill=fill)
    elif isinstance(c, Checkmark):
        points = [(w * 0.12, h * 0.5), (w * 0.4, h * 0.78), (w * 0.88, h * 0.2)]
        lengths = [math.dist(a, b) for a, b in pairwise(points)]
        remaining = sum(lengths) * p
        for a, b, length in zip(points, points[1:], lengths):
            ratio = min(1, remaining / length)
            if ratio > 0:
                d.line((a, (a[0] + (b[0] - a[0]) * ratio, a[1] + (b[1] - a[1]) * ratio)), fill=color, width=stroke)
            remaining = max(0, remaining - length)
    elif isinstance(c, ProgressRing):
        box = (0, 0, w - 1, h - 1)
        start, sweep = (180, 180) if isinstance(c, Gauge) else (-90, 360)
        d.arc(box, start, start + sweep, fill=track, width=stroke)
        if p > 0:
            d.arc(box, start, start + sweep * p, fill=color, width=stroke)
    else:
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h / 2, fill=track)
        if p > 0:
            foreground = Image.new("RGBA", (w, h))
            ImageDraw.Draw(foreground).rounded_rectangle((0, 0, w - 1, h - 1), radius=h / 2, fill=color)
            sprite.alpha_composite(foreground.crop((0, 0, max(1, round(w * p)), h)))
    if c.label:
        number = Number(p * 100, suffix="%", font_size=min(22, c.height / 4), color=color)
        label = renderer._sprite(number, number.state(), factor, 0)
        sprite.alpha_composite(label, ((w - label.width) // 2, (h - label.height) // 2))
    return sprite
