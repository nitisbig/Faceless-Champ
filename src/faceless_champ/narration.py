"""Narration chapters authored against unchanged source subtitle timestamps."""

from __future__ import annotations

from typing import Self

from .components import Canvas, finite
from .subtitles import SubtitleTrack
from .timeline import Scene


class CueScene(Scene):
    """A local scene clock mapped to a segment of a source SubtitleTrack.

    This schedules visuals only. Put continuous narration on a parent Layer to
    avoid restarting or duplicating audio when assembling chapters in a Sequence.
    An explicit end_time may extend beyond the last cue to preserve an audio tail.
    """

    def __init__(
        self,
        track: SubtitleTrack,
        canvas: Canvas | None = None,
        *,
        start_time: float = 0,
        end_time: float | None = None,
    ) -> None:
        if not isinstance(track, SubtitleTrack):
            raise TypeError("CueScene requires a SubtitleTrack")
        self.track = track
        self.start_time = finite(start_time, "start_time", 0)
        self.end_time = finite(track.duration if end_time is None else end_time, "end_time", 0)
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        super().__init__(canvas)

    @property
    def segment_duration(self) -> float:
        return self.end_time - self.start_time

    def cue_time(self, index: int, *, edge: str = "start", offset: float = 0) -> float:
        """Return local seconds for an original cue edge plus a signed offset.

        The cue start must belong to this chapter's half-open source interval.
        The resulting event may fall on the end boundary (e.g. for removal).
        """
        if not isinstance(index, int) or isinstance(index, bool) or index < 1:
            raise ValueError("Cue index must be a positive integer")
        if edge not in {"start", "end"}:
            raise ValueError("edge must be start or end")
        cue = self.track.cue(index)
        if not self.start_time <= cue.start < self.end_time:
            raise ValueError(f"Cue {index} is outside the scene's source interval")
        source_time = getattr(cue, edge) + finite(offset, "offset")
        if not self.start_time <= source_time <= self.end_time:
            raise ValueError(f"Cue {index} event is outside the scene's source interval")
        return source_time - self.start_time

    def at_cue(self, index: int, *, edge: str = "start", offset: float = 0):
        """Author an absolute-time block using an original SRT cue number."""
        return self.at(self.cue_time(index, edge=edge, offset=offset))

    def finish(self) -> Self:
        """Hold to the exact chapter boundary; reject overflowing animation/audio.

        Call after authoring, before assembling a cut-only Sequence. No durations
        are silently shortened, and cues are never edited or retimed.
        """
        if self.duration > self.segment_duration + 1e-9:
            raise ValueError("Scene content extends beyond the source interval")
        self.wait_until(self.segment_duration)
        return self
