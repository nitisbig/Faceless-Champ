"""Envelope and easing helpers for frame functions, plus word-cue timing on a narration clock.

Every helper is a pure function of time, so ``fn(t, size)`` stays deterministic::

    a = smooth(lin(t, 2.0, 2.6))             # fade in over 0.6 s
    a = env(t, 2.0, 9.0, 0.4, 0.6)           # in at 2.0, out by 9.0
    clock = CueClock("cue-per-word.srt")
    lift = clock.beat(560)                   # 0.15 s before word cue #560
"""

from __future__ import annotations

import math
import re
from pathlib import Path


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else min(x, hi)


def lin(t, t0, t1):
    """0 before t0, 1 after t1, linear between (a step at t1 when the span is empty)."""
    return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)


def smooth(u):
    return u * u * (3 - 2 * u)


def ease_out(u):
    return 1 - (1 - u) ** 3


def ease_in(u):
    return u**3


def ease_io(u):
    return 4 * u**3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def back(u, s=1.6):
    """Ease out with a small overshoot past 1."""
    v = u - 1
    return 1 + (s + 1) * v**3 + s * v**2


def env(t, a, b, fin=0.4, fout=0.4):
    """Visibility envelope: fade in from a, fade out to zero at b."""
    if t < a or t > b:
        return 0.0
    return smooth(lin(t, a, a + fin)) * (1 - smooth(lin(t, b - fout, b)))


def lerp(a, b, u):
    return a + (b - a) * u


def pulse(t, at, width=0.5):
    """0 -> 1 -> 0 bump centred just after ``at``."""
    u = lin(t, at, at + width)
    return math.sin(math.pi * u) if 0 < u < 1 else 0.0


def chroma_kick(t, at, amount=6.0, width=0.18):
    """Chromatic split in design px for a kick landing at ``at`` (fast attack, short decay)."""
    if t < at - 0.03 or t > at + width:
        return 0.0
    return amount * math.exp(-max(0.0, t - at) / (width / 3))


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


class CueClock:
    """Word-cue times from a one-cue-per-word SRT on the narration source clock.

    ASR text can be wrong (digits for spoken numbers, misheard words): anchor those beats with
    ``cue(n)`` rather than ``word()``.
    """

    def __init__(self, srt: str | Path, *, lead: float = 0.15, overlap_tolerance: float = 0.001):
        self.srt = Path(srt)
        self.lead = lead
        self.overlap_tolerance = overlap_tolerance
        self._track = None

    @property
    def track(self):
        if self._track is None:
            from ..subtitles import SubtitleTrack

            self._track = SubtitleTrack.from_srt(self.srt, overlap_tolerance=self.overlap_tolerance)
        return self._track

    def cue(self, index: int) -> float:
        """Start time (s) of a one-based word cue."""
        return self.track.cue(index).start

    def beat(self, index: int, lead: float | None = None) -> float:
        """When a visual beat lands: ``lead`` seconds (default ``self.lead``) before its word cue."""
        return max(0.0, self.cue(index) - (self.lead if lead is None else lead))

    def word(self, text: str, after: float = 0.0) -> float:
        """Start time of the first cue matching ``text`` at or after ``after`` seconds."""
        target = _norm(text)
        for c in self.track.cues:
            if c.start >= after - 1e-6 and _norm(c.text) == target:
                return c.start
        raise KeyError(f"word {text!r} not found after {after}")
