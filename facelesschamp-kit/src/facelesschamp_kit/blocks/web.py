"""Walkthrough presentation blocks over prepared core HTML assets."""

from dataclasses import dataclass

from faceless_champ import Bounds, Group, Rectangle, fit_text
from faceless_champ.web import HtmlClip, WebCallout, WebCapture, WebFocus, WebHighlight

from .base import BlockBuild


@dataclass(frozen=True)
class WebWalkthrough:
    capture: WebCapture
    browser_chrome: bool = True
    title: str = "Local app demo"
    cursor: bool = True
    source_start: float = 0
    highlights: tuple[WebHighlight, ...] = ()
    focuses: tuple[WebFocus, ...] = ()
    callouts: tuple[WebCallout, ...] = ()

    def compose(self, context, bounds: Bounds):
        vw, vh = self.capture.viewport
        chrome = 42 if self.browser_chrome else 0
        ratio = min(bounds.width / vw, bounds.height / (vh + chrome))
        width, height = vw * ratio, vh * ratio
        left, top = bounds.center[0] - width / 2, bounds.center[1] - (height + chrome * ratio) / 2
        clip = HtmlClip(
            self.capture,
            width=width,
            height=height,
            source_start=self.source_start,
            cursor=self.cursor,
            highlights=self.highlights,
            focuses=self.focuses,
            callouts=self.callouts,
            position=(left, top + chrome * ratio),
            anchor="top_left",
        )
        children = {"page": clip}
        if self.browser_chrome:
            children["chrome"] = Rectangle(
                width=max(1, width - 2),
                height=max(1, chrome * ratio - 2),
                fill=context.theme.surface,
                stroke=None,
                stroke_width=0,
                position=(left, top),
                anchor="top_left",
            )
            children["title"] = fit_text(
                self.title,
                Bounds(left + 12 * ratio, top + 4 * ratio, left + width - 12 * ratio, top + (chrome - 4) * ratio),
                font_size=max(1, round(16 * ratio)),
                min_font_size=1,
                color=context.theme.foreground,
                align="left",
                spacing=0,
            )
        root = Group(*children.values())
        return BlockBuild(root, children)


@dataclass(frozen=True)
class WebElement:
    capture: WebCapture
    selector: str
    source_start: float = 0

    def compose(self, context, bounds: Bounds):
        clip = HtmlClip(
            self.capture,
            selector=self.selector,
            source_start=self.source_start,
            width=bounds.width,
            height=bounds.height,
            position=bounds.center,
        )
        return BlockBuild(clip, {"element": clip})
