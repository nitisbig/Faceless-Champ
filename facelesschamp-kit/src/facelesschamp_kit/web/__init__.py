"""Optional HTML-to-video. Playwright is imported only by capture_html()."""

from facelesschamp_kit.web.capture import capture_html
from facelesschamp_kit.web.clip import HtmlClip, WebCallout, WebFocus, WebHighlight
from facelesschamp_kit.web.model import HtmlPage, WebAction, WebCapture, WebError, WebScript

__all__ = [
    "HtmlClip",
    "HtmlPage",
    "WebAction",
    "WebCallout",
    "WebCapture",
    "WebError",
    "WebFocus",
    "WebHighlight",
    "WebScript",
    "capture_html",
]
