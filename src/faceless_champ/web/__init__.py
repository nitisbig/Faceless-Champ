"""Optional HTML-to-video. Playwright is imported only by capture_html()."""

from .capture import capture_html
from .clip import HtmlClip, WebCallout, WebFocus, WebHighlight
from .model import HtmlPage, WebAction, WebCapture, WebError, WebScript

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
