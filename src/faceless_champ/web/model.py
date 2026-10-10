"""Serializable authoring records and disk-backed browser captures."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..components import finite


class WebError(ValueError):
    """A browser preparation or prepared asset error."""


@dataclass(frozen=True)
class HtmlPage:
    path: str | Path
    viewport: tuple[int, int] = (1440, 900)
    asset_root: str | Path | None = None
    storage: dict[str, str] = field(default_factory=dict)
    ready: tuple[str, ...] = ()

    def __post_init__(self):
        path = Path(self.path).resolve()
        root = Path(self.asset_root).resolve() if self.asset_root else path.parent
        if not path.is_file() or path.suffix.lower() not in {".html", ".htm"}:
            raise WebError(f"Local HTML file not found: {path}")
        if not path.is_relative_to(root):
            raise WebError("HTML must be inside asset_root")
        if len(self.viewport) != 2 or any(type(v) is not int or v <= 0 for v in self.viewport):
            raise WebError("viewport must contain two positive integers")
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in self.storage.items()):
            raise WebError("storage keys and values must be strings")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "asset_root", root)
        object.__setattr__(self, "storage", dict(self.storage))
        object.__setattr__(self, "ready", tuple(self.ready))


@dataclass(frozen=True)
class WebAction:
    kind: str
    selector: str
    at: float
    duration: float = 0
    value: object = None


class WebScript:
    """Times are relative to capture zero. Methods return self for chaining."""

    def __init__(self, duration: float):
        self.duration = finite(duration, "duration", 0.001)
        self.actions: list[WebAction] = []
        self.selectors: list[str] = []

    def track(self, *selectors):
        for selector in selectors:
            if not isinstance(selector, str) or not selector.strip():
                raise WebError("Selectors must be nonempty strings")
            if selector not in self.selectors:
                self.selectors.append(selector)
        return self

    def _add(self, kind, selector, at, duration=0, value=None):
        at = finite(at, "at", 0)
        duration = finite(duration, "duration", 0)
        if at >= self.duration or at + duration > self.duration:
            raise WebError("Action exceeds script duration")
        for action in self.actions:
            if (
                at == action.at
                or max(at, action.at) < min(at + duration, action.at + action.duration)
                or at < action.at < at + duration
                or action.at < at < action.at + action.duration
            ):
                raise WebError(f"Overlapping input actions at {at:g}s and {action.at:g}s")
        self.track(selector)
        self.actions.append(WebAction(kind, selector, at, duration, value))
        return self

    def move(self, selector, *, at, duration=0.4):
        return self._add("move", selector, at, duration)

    def click(self, selector, *, at):
        return self._add("click", selector, at)

    def type(self, selector, text, *, at, duration=1):
        if not isinstance(text, str) or not text:
            raise WebError("type requires nonempty text")
        return self._add("type", selector, at, duration, text)

    def press(self, selector, key, *, at):
        if not isinstance(key, str) or not key:
            raise WebError("press requires a key")
        return self._add("press", selector, at, value=key)

    def select(self, selector, value, *, at):
        if not isinstance(value, str):
            raise WebError("select requires a string value")
        return self._add("select", selector, at, value=value)

    def scroll(self, selector, *, at, y, x=0, duration=0.7):
        return self._add("scroll", selector, at, duration, [finite(x, "scroll x"), finite(y, "scroll y")])

    def assert_ready(self, selector, *, at):
        return self._add("ready", selector, at)

    def record(self):
        return {
            "duration": self.duration,
            "actions": [asdict(a) for a in sorted(self.actions, key=lambda a: a.at)],
            "selectors": self.selectors,
        }


class WebCapture:
    """Immutable prepared asset; no browser is needed to open or display it."""

    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        try:
            self.manifest = json.loads((self.directory / "manifest.json").read_text())
            if self.manifest["schema"] != 1:
                raise ValueError("Unsupported capture schema")
            self.fps = finite(self.manifest["fps"], "fps", 0.001)
            self.duration = finite(self.manifest["duration"], "duration", 0.001)
            self.viewport = tuple(self.manifest["viewport"])
            if len(self.viewport) != 2 or any(type(v) is not int or v <= 0 for v in self.viewport):
                raise ValueError("Invalid capture viewport")
            self.frames = self.manifest["frames"]
            self.count = math.ceil(self.duration * self.fps - 1e-9)
            if any(str(int(i)) != i or not 0 <= int(i) < self.count for i in self.frames):
                raise ValueError("Invalid capture frame indices")
            if not self.frames or any(not (self.directory / f"{int(i):08d}.png").is_file() for i in self.frames):
                raise ValueError("Missing frame files")
            from PIL import Image

            for index in self.frames:
                with Image.open(self.directory / f"{int(index):08d}.png") as image:
                    if image.format != "PNG" or image.size != self.viewport:
                        raise ValueError("Invalid capture frame format or dimensions")
                    image.verify()
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise WebError(f"Incomplete capture at {self.directory}; run capture_html again: {exc}") from exc

    def index(self, time):
        return min(self.count - 1, math.floor(finite(time, "time", 0) * self.fps + 1e-9))

    def metadata(self, time):
        index = self.index(time)
        if str(index) not in self.frames:
            raise WebError(f"Frame at {index / self.fps:g}s was not prepared; run capture_html with this range")
        return self.frames[str(index)]

    def image(self, time):
        from PIL import Image

        self.metadata(time)
        with Image.open(self.directory / f"{self.index(time):08d}.png") as image:
            return image.convert("RGBA")
