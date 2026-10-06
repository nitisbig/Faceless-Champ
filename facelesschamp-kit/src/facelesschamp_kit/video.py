"""Authoring definitions. Core components are constructed only during compilation."""

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from weakref import WeakSet

from faceless_champ import SubtitleTrack
from faceless_champ.audio import AudioClip

from .diagnostics import KitError, number


@dataclass(frozen=True)
class Handle:
    placement: str
    child: str | None = None

    def __getitem__(self, name):
        if self.child is not None:
            raise KitError("HANDLE", "Use a named child from the placement handle")
        return Handle(self.placement, name)


@dataclass(frozen=True)
class Window:
    start: float
    end: float
    cues: tuple = ()


@dataclass
class Placement:
    handle: Handle
    block: object
    bounds: object
    enter: str | None
    enter_duration: float
    z_index: float
    core: bool = False


@dataclass
class Segment:
    name: str
    start: float
    duration: float
    cues: tuple = ()
    placements: list = field(default_factory=list)
    motions: list = field(default_factory=list)

    @property
    def end(self):
        return self.start + self.duration

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def add(self, block, *, id=None, bounds=None, anchor="center", enter=None, enter_duration=None, z_index=0):
        if anchor != "center":
            raise KitError("LAYOUT", "Use anchor='center' or explicit bounds for placement")
        if enter not in {None, "fade", "pop", "stagger"}:
            raise KitError("MOTION", "Entry must be fade, pop, or stagger")
        name = id or f"block-{len(self.placements) + 1}"
        if not isinstance(name, str) or not name or "/" in name:
            raise KitError("PLACEMENT_ID", "Placement IDs must be nonempty and cannot contain '/'")
        handle = Handle(f"{self.name}/{name}")
        if any(p.handle == handle for p in self.placements):
            raise KitError("PLACEMENT_ID", "Duplicate placement ID", placement=handle.placement)
        duration = number(enter_duration, "enter_duration", positive=True) if enter_duration is not None else None
        self.placements.append(
            Placement(
                handle, deepcopy(block), bounds, enter, duration, number(z_index, "z_index", minimum=-float("inf"))
            )
        )
        return handle

    def add_core(self, factory, **kwargs):
        if not callable(factory):
            raise KitError("BLOCK_CONTRACT", "add_core requires a factory returning fresh core components")
        handle = self.add(factory, **kwargs)
        self.placements[-1].core = True
        return handle

    def play(self, target, animation, *, at=0, duration=1):
        if not isinstance(target, Handle) or not any(p.handle.placement == target.placement for p in self.placements):
            raise KitError("HANDLE", "Animation target must belong to this segment")
        if not callable(animation):
            raise KitError("MOTION", "Pass a callback: lambda component: component.animate.scale_to(1.2)")
        at = number(at, "at")
        duration = number(duration, "duration", positive=True)
        if at + duration > self.duration + 1e-9:
            raise KitError("MOTION_WINDOW", "Animation exceeds its segment", segment=self.name)
        self.motions.append((target, animation, at, duration))
        return self


class Narration:
    def __init__(self, audio, subtitles, markers, overlap_tolerance=0):
        self.audio = Path(audio)
        self.subtitles = Path(subtitles)
        self.duration = AudioClip(self.audio).duration
        self.track = SubtitleTrack.from_srt(subtitles, overlap_tolerance=overlap_tolerance)
        self.markers = dict(markers)
        if self.track.duration > self.duration + 0.001:
            raise KitError("CUE_AUDIO", "Subtitles extend beyond audio duration")
        for name, index in self.markers.items():
            if not isinstance(index, int) or isinstance(index, bool) or index < 1:
                raise KitError("CUE_INDEX", "Markers require original positive SRT cue indices", marker=name)
            try:
                self.track.cue(index)
            except KeyError:
                raise KitError("CUE_INDEX", "SRT cue index does not exist", marker=name, cue=index) from None

    def between(self, first, next=None):
        try:
            start = self.track.cue(self.markers[first]).start
            end = self.track.cue(self.markers[next]).start if next else self.duration
        except KeyError as exc:
            raise KitError("CUE_MARKER", f"Unknown marker {exc}") from None
        if end <= start:
            raise KitError("CUE_WINDOW", "End marker must follow start marker")
        return Window(start, end, (self.markers[first],) + ((self.markers[next],) if next else ()))


class Video:
    def __init__(self, context):
        self.context = context
        self.segments = []
        self.voice = None
        self._constructed = WeakSet()

    def segment(self, name, *, start=None, duration=None, window=None):
        if not isinstance(name, str) or not name or "/" in name or any(s.name == name for s in self.segments):
            raise KitError("SEGMENT_ID", "Segment IDs must be unique, nonempty, and contain no '/'")
        if window is not None:
            if start is not None or duration is not None:
                raise KitError("SEGMENT_WINDOW", "Use window or start/duration, not both")
            start, duration = window.start, window.end - window.start
        else:
            start = max((s.end for s in self.segments), default=0) if start is None else start
        segment = Segment(
            name, number(start, "start"), number(duration, "duration", positive=True), window.cues if window else ()
        )
        self.segments.append(segment)
        return segment

    def narration(self, *, audio, subtitles, markers, captions=None, overlap_tolerance=0):
        if self.voice is not None:
            raise KitError("NARRATION", "A video supports one master narration track")
        self.voice = Narration(self.context.root / audio, self.context.root / subtitles, markers, overlap_tolerance)
        if captions is not None:
            self.context.captions = bool(captions)
        return self.voice

    def compile(self):
        from .compiler import compile_video

        return compile_video(self)
