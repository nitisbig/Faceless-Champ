"""SRT cues and deterministic word-highlight captions on the scene clock."""

from __future__ import annotations

import re
from bisect import bisect_right
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .components import Component, finite


def _timestamp(value: str) -> float:
    match = re.fullmatch(r"(\d{2,}):([0-5]\d):([0-5]\d)[,.](\d{3})", value)
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {value!r}")
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


@dataclass(frozen=True)
class SubtitleCue:
    index: int
    start: float
    end: float
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or isinstance(self.index, bool) or self.index < 1:
            raise ValueError("Cue index must be a positive integer")
        object.__setattr__(self, "start", finite(self.start, "cue start", 0))
        object.__setattr__(self, "end", finite(self.end, "cue end", 0))
        if self.end <= self.start:
            raise ValueError(f"Cue {self.index} must end after it starts")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError(f"Cue {self.index} must have text")


class SubtitleTrack:
    """An ordered, nonoverlapping collection of cues. Times are never retimed."""

    def __init__(self, cues: Iterable[SubtitleCue]) -> None:
        self.cues = tuple(cues)
        if not self.cues:
            raise ValueError("Subtitle track needs at least one cue")
        if any(not isinstance(cue, SubtitleCue) for cue in self.cues):
            raise TypeError("SubtitleTrack requires SubtitleCue objects")
        self._by_index = {cue.index: cue for cue in self.cues}
        if len(self._by_index) != len(self.cues):
            raise ValueError("Subtitle cue indices must be unique")
        for previous, cue in zip(self.cues, self.cues[1:]):
            if cue.start < previous.end:
                raise ValueError(f"Cues {previous.index} and {cue.index} overlap or are out of order")
        self._starts = tuple(cue.start for cue in self.cues)

    @classmethod
    def from_srt(cls, path: str | Path) -> SubtitleTrack:
        return cls.parse_srt(Path(path).read_text(encoding="utf-8-sig"))

    @classmethod
    def parse_srt(cls, text: str) -> SubtitleTrack:
        text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").strip()
        cues = []
        for block_number, block in enumerate(re.split(r"\n(?:[ \t]*\n)+", text), 1):
            lines = block.splitlines()
            try:
                index = int(lines[0])
                start, end = re.split(r"\s*-->\s*", lines[1])
                cues.append(
                    SubtitleCue(index, _timestamp(start.strip()), _timestamp(end.strip()), "\n".join(lines[2:]))
                )
            except (ValueError, IndexError) as exc:
                raise ValueError(f"Invalid SRT block {block_number}: {exc}") from exc
        return cls(cues)

    @property
    def duration(self) -> float:
        return self.cues[-1].end

    def cue(self, index: int) -> SubtitleCue:
        """Look up the original SRT cue number (one-based, not a list offset)."""
        return self._by_index[index]

    def active_at(self, time: float) -> SubtitleCue | None:
        """Use half-open intervals: start <= time < end; gaps return None."""
        time = finite(time, "subtitle time")
        offset = bisect_right(self._starts, time) - 1
        if offset >= 0 and time < self.cues[offset].end:
            return self.cues[offset]
        return None

    def phrases(self, max_words: int = 7, max_duration: float = 3) -> tuple[tuple[SubtitleCue, ...], ...]:
        if not isinstance(max_words, int) or isinstance(max_words, bool) or max_words < 1:
            raise ValueError("max_words must be a positive integer")
        max_duration = finite(max_duration, "max_duration", 0.001)
        phrases, current = [], []
        words = 0
        for cue in self.cues:
            count = len(cue.text.split())
            if current and (words + count > max_words or cue.end - current[0].start > max_duration):
                phrases.append(tuple(current))
                current, words = [], 0
            current.append(cue)
            words += count
            if cue.text.rstrip("\"'”’").endswith((".", "!", "?", ",", ";", ":")):
                phrases.append(tuple(current))
                current, words = [], 0
        if current:
            phrases.append(tuple(current))
        return tuple(phrases)


class Captions(Component):
    """Display short phrases and highlight the cue spoken at the current time.

    Cue times are relative to when this component is added to the scene. A
    word-per-cue SRT gives word highlighting; sentence cues highlight sentences.
    """

    def __init__(
        self,
        track: SubtitleTrack,
        *,
        font: str | Path | None = None,
        font_size: float = 42,
        width: float = 1440,
        color: str = "#292724",
        highlight_color: str = "#e56c35",
        future_color: str = "#99938b",
        max_words: int = 7,
        max_duration: float = 3,
        spacing: float = 8,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if not isinstance(track, SubtitleTrack):
            raise TypeError("Captions requires a SubtitleTrack")
        self.track = track
        self.font = str(font) if font else None
        self.font_size = finite(font_size, "font_size", 1)
        self.width = finite(width, "width", 1)
        self.spacing = finite(spacing, "spacing", 0)
        self.color, self.highlight_color, self.future_color = color, highlight_color, future_color
        self.phrases = track.phrases(max_words, max_duration)
        self._phrase_starts = tuple(phrase[0].start for phrase in self.phrases)

    def phrase_at(self, time: float) -> tuple[SubtitleCue, ...]:
        time = finite(time, "caption time")
        offset = bisect_right(self._phrase_starts, time) - 1
        if offset >= 0 and time < self.phrases[offset][-1].end:
            return self.phrases[offset]
        return ()
