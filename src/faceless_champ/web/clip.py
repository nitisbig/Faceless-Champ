"""Browser-free playback of prepared HTML frames and geometry."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageOps

from ..components import Component, finite
from ..typography import DEFAULT_FONT, load_font
from .model import WebCapture, WebError


@dataclass(frozen=True)
class WebFocus:
    selector: str
    start: float
    end: float
    zoom: float = 1.6
    transition: float = 0.4

    def __post_init__(self):
        _window(self)
        finite(self.zoom, "zoom", 1)
        finite(self.transition, "transition", 0)


@dataclass(frozen=True)
class WebHighlight:
    selector: str
    start: float
    end: float
    color: str = "#45d6ba"

    def __post_init__(self):
        _window(self)


@dataclass(frozen=True)
class WebCallout:
    text: str
    start: float
    end: float

    def __post_init__(self):
        _window(self)
        if not self.text.strip():
            raise WebError("Callout text must not be empty")


def _window(record):
    if finite(record.end, "end", 0) <= finite(record.start, "start", 0):
        raise WebError("Annotation end must be after start")


class HtmlClip(Component):
    """A fixed-size HTML viewport in an ordinary core scene.

    Annotation times and source_start use the original capture clock. Selector
    crops preserve visible page pixels (including backgrounds and occluders).
    """

    def __init__(
        self,
        capture,
        *,
        width,
        height,
        selector=None,
        source_start=0,
        cursor=False,
        highlights=(),
        focuses=(),
        callouts=(),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.capture = capture if isinstance(capture, WebCapture) else WebCapture(capture)
        self.width = finite(width, "width", 1)
        self.height = finite(height, "height", 1)
        self.selector = selector
        self.source_start = finite(source_start, "source_start", 0)
        if self.source_start >= self.capture.duration:
            raise WebError("source_start must be before capture end")
        self.cursor = bool(cursor)
        self.highlights = tuple(highlights)
        self.focuses = tuple(focuses)
        self.callouts = tuple(callouts)
        for records, expected in (
            (self.highlights, WebHighlight),
            (self.focuses, WebFocus),
            (self.callouts, WebCallout),
        ):
            if any(not isinstance(r, expected) for r in records):
                raise WebError(f"Expected {expected.__name__} records")
        for a, b in zip(sorted(self.focuses, key=lambda f: f.start), sorted(self.focuses, key=lambda f: f.start)[1:]):
            if a.end > b.start:
                raise WebError("Focus windows cannot overlap")

    def frame_key(self, age):
        return self.capture.index(self.source_start + age)

    def frame_image(self, age, factor=1):
        time = self.frame_key(age) / self.capture.fps
        source = self.capture.image(time)
        metadata = self.capture.metadata(time)
        geometry = metadata["geometry"]
        draw = ImageDraw.Draw(source)
        if self.cursor:
            for click in metadata["clicks"]:
                progress = (time - click["at"]) / 0.6
                if not 0 <= progress <= 1:
                    continue
                x, y = click["position"]
                radius = 8 + 24 * progress
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="#35bca5", width=3)
            x, y = metadata["cursor"]
            draw.polygon(
                [(x, y), (x + 5, y + 25), (x + 11, y + 17), (x + 22, y + 16)], fill="white", outline="#161c28", width=2
            )
        for highlight in self.highlights:
            if highlight.start <= time < highlight.end:
                box = geometry.get(highlight.selector)
                if box:
                    draw.rounded_rectangle(tuple(box), radius=8, outline=highlight.color, width=4)
        box = (0, 0, source.width, source.height)
        if self.selector:
            box = geometry.get(self.selector)
            if not box:
                raise WebError(
                    f"Selector {self.selector!r} has no prepared visible bounds at {time:g}s; track it first"
                )
        else:
            for focus in self.focuses:
                if focus.start <= time < focus.end:
                    target = geometry.get(focus.selector)
                    if not target:
                        raise WebError(f"Focus selector {focus.selector!r} not visible at {time:g}s")
                    blend = (
                        min(1, (time - focus.start) / focus.transition, (focus.end - time) / focus.transition)
                        if focus.transition
                        else 1
                    )
                    blend = blend * blend * (3 - 2 * blend)
                    zoom = 1 + (focus.zoom - 1) * blend
                    w, h = source.width / zoom, source.height / zoom
                    cx = source.width / 2 + ((target[0] + target[2]) / 2 - source.width / 2) * blend
                    cy = source.height / 2 + ((target[1] + target[3]) / 2 - source.height / 2) * blend
                    x = max(0, min(source.width - w, cx - w / 2))
                    y = max(0, min(source.height - h, cy - h / 2))
                    box = (x, y, x + w, y + h)
        source = source.crop(tuple(round(v) for v in box))
        size = (max(1, round(self.width * factor)), max(1, round(self.height * factor)))
        fitted = ImageOps.contain(source, size, Image.Resampling.LANCZOS)
        result = Image.new("RGBA", size)
        result.alpha_composite(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
        for callout in self.callouts:
            if callout.start <= time < callout.end:
                font_size = max(10, round(min(size) * 0.035))
                font = load_font(DEFAULT_FONT, font_size)
                painter = ImageDraw.Draw(result)
                while font_size > 8 and painter.textbbox((0, 0), callout.text, font=font)[2] > size[0] * 0.9:
                    font_size -= 1
                    font = load_font(DEFAULT_FONT, font_size)
                bounds = painter.textbbox((0, 0), callout.text, font=font)
                w, h = bounds[2] - bounds[0], bounds[3] - bounds[1]
                pad = max(4, round(font_size * 0.65))
                x, y = (size[0] - w) // 2, size[1] - h - 3 * pad
                painter.rounded_rectangle((x - pad, y - pad, x + w + pad, y + h + pad), radius=pad, fill="#172235")
                painter.text((x - bounds[0], y - bounds[1]), callout.text, font=font, fill="white")
        return result
