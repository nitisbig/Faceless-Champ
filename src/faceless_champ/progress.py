"""Terminal feedback for the export engine's frame progress callback."""

from __future__ import annotations

import math
import sys
import time
from typing import TextIO


def _duration(seconds: float) -> str:
    seconds = math.ceil(max(0, seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


class ExportProgress:
    """A throttled stderr progress bar with elapsed time and estimated time left.

    Use ``with ExportProgress() as progress: render(..., progress=progress)``.
    ETA is based on observed frame throughput. The last frame enters Finalizing;
    success is shown only after the export returns without an exception. Redirected
    output uses occasional newline records instead of terminal control characters.
    """

    def __init__(self, *, stream: TextIO | None = None, interval: float = 0.5):
        if not math.isfinite(interval) or interval < 0:
            raise ValueError("Progress interval must be finite and nonnegative")
        self.stream = sys.stderr if stream is None else stream
        self.interactive = bool(getattr(self.stream, "isatty", lambda: False)())
        self.interval = interval if self.interactive else max(5.0, interval)
        self.started = None
        self.updated = None
        self.completed = 0
        self.total = 0
        self.line_width = 0

    def __enter__(self):
        return self

    def __call__(self, completed: int, total: int) -> None:
        if not 0 <= completed <= total or total <= 0:
            raise ValueError("Progress requires 0 <= completed <= total and total > 0")
        now = time.monotonic()
        if self.started is None or completed == 0:
            self.started = now
            self.updated = None
        self.completed, self.total = completed, total
        if self.updated is None or completed == total or now - self.updated >= self.interval:
            self._write("Finalizing" if completed == total else "Exporting", now)
            self.updated = now

    def _write(self, label: str, now: float, *, final: bool = False) -> None:
        elapsed = max(0, now - self.started)
        ratio = self.completed / self.total
        filled = int(24 * ratio)
        bar = "#" * filled + "-" * (24 - filled)
        eta = "--:--"
        if label == "Exported":
            eta = "00:00"
        elif label == "Exporting" and self.completed and elapsed > 0:
            eta = _duration(elapsed / self.completed * (self.total - self.completed))
        line = (
            f"{label} [{bar}] {ratio:6.1%} {self.completed}/{self.total} frames"
            f" | elapsed {_duration(elapsed)} | ETA {eta}"
        )
        if self.interactive:
            self.stream.write("\r" + line.ljust(self.line_width) + ("\n" if final else ""))
            self.line_width = len(line)
        else:
            self.stream.write(line + "\n")
        self.stream.flush()

    def __exit__(self, exc_type, exc, traceback):
        if self.started is not None:
            complete = exc_type is None and self.completed == self.total
            self._write("Exported" if complete else "Export stopped", time.monotonic(), final=True)
        return False
