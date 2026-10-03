"""Deterministic scenes and compositional timelines."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from .animation import Animation, interpolate, smooth
from .audio import AudioClip
from .components import Canvas, Component, finite
from .subtitles import Captions


class Renderable:
    canvas: Canvas

    @property
    def duration(self) -> float:
        raise NotImplementedError

    def render(self, output: str | Path, **kwargs: Any) -> Path:
        from .export import render

        return render(self, output, **kwargs)


@dataclass
class Track:
    property: str
    start: float
    duration: float
    initial: object
    target: object
    easing: Callable[[float], float]


@dataclass
class Entry:
    component: Component
    start: float
    initial: dict
    tracks: list[Track]
    end: float | None = None

    def state_at(self, time: float) -> dict:
        state = self.initial.copy()
        for track in self.tracks:
            if time >= track.start:
                progress = min(1.0, (time - track.start) / track.duration)
                state[track.property] = interpolate(track.initial, track.target, track.easing(progress))
        return state


class Scene(Renderable):
    def __init__(self, canvas: Canvas | None = None) -> None:
        self.canvas = canvas or Canvas()
        self.entries: list[Entry] = []
        self.audio: list[AudioClip] = []
        self._cursor = 0.0
        self._built = False
        self._building = False
        self._objects: dict[Component, Entry] = {}

    def construct(self) -> None:
        """Override to author a scene."""

    def build(self) -> Self:
        if not self._built and not self._building:
            self._building = True
            try:
                self.construct()
                self._built = True
            except Exception:
                self.entries.clear()
                self.audio.clear()
                self._objects.clear()
                self._cursor = 0.0
                raise
            finally:
                self._building = False
        return self

    @property
    def duration(self) -> float:
        self.build()
        caption_ends = [
            min(e.start + e.component.track.duration, e.end if e.end is not None else float("inf"))
            for e in self.entries
            if isinstance(e.component, Captions)
        ]
        return max([self._cursor] + [a.start + a.duration for a in self.audio] + caption_ends)

    @property
    def time(self) -> float:
        """The current visual authoring cursor, in seconds."""
        return self._cursor

    @contextmanager
    def at(self, time: float):
        """Author a block at an absolute time, then keep the furthest cursor.

        Independent objects can be scheduled out of order. Animations of the
        same object's property must still be authored in chronological order.
        """
        time = finite(time, "time", 0)
        previous = self._cursor
        self._cursor = time
        try:
            yield self
        finally:
            self._cursor = max(previous, self._cursor)

    def wait_until(self, time: float) -> Self:
        time = finite(time, "time", 0)
        if time < self._cursor - 1e-9:
            raise ValueError("wait_until cannot move backward; use with scene.at(time)")
        self._cursor = max(time, self._cursor)
        return self

    def remove(self, *components: Component) -> Self:
        """End component lifetimes at the cursor without adding an animation."""
        for component in components:
            entry = self._objects.get(component)
            if entry is None or entry.end is not None:
                raise ValueError("remove requires a component currently in the scene")
            if self._cursor < entry.start:
                raise ValueError("Cannot remove a component before its start")
            if any(t.start + t.duration > self._cursor + 1e-9 for t in entry.tracks):
                raise ValueError("Cannot remove a component before its animations end")
        for component in components:
            self._objects[component].end = self._cursor
        return self

    def add(self, *components: Component) -> Self:
        for component in components:
            if not isinstance(component, Component):
                raise TypeError("Scene.add requires visual components")
            if component in self._objects:
                entry = self._objects[component]
                if entry.end is not None:
                    raise ValueError("Removed components cannot be re-added; create a new instance")
                continue
            entry = Entry(deepcopy(component), self._cursor, component.state(), [])
            self.entries.append(entry)
            self._objects[component] = entry
        return self

    def play(self, *animations: Animation, run_time: float = 1.0, rate_func: Callable[[float], float] = smooth) -> Self:
        duration = finite(run_time, "run_time", 0.000001)
        if not animations:
            raise ValueError("play requires at least one animation")
        if not callable(rate_func):
            raise TypeError("rate_func must be callable")
        seen = set()
        for animation in animations:
            if not isinstance(animation, Animation) or not animation.targets:
                raise TypeError("play requires nonempty animations")
            if not isinstance(animation.component, Component):
                raise TypeError("Animation requires a Component")
            for properties in (animation.targets, animation.starts or {}):
                for key, value in properties.items():
                    if key not in animation.component.state():
                        raise ValueError(f"Unsupported animation property: {key}")
                    if key == "position":
                        if not isinstance(value, tuple) or len(value) != 2:
                            raise ValueError("Animated position must be an (x, y) tuple")
                        for coordinate in value:
                            finite(coordinate, "position")
                    else:
                        finite(value, key, 0.001 if key == "scale" else (None if key == "rotation" else 0))
                        if key in {"opacity", "reveal", "draw"} and value > 1:
                            raise ValueError(f"{key} must be <= 1")
            for key in animation.targets:
                identity = (animation.component, key)
                if identity in seen:
                    raise ValueError(f"Overlapping animations for property {key}")
                seen.add(identity)
                entry = self._objects.get(animation.component)
                if entry is not None:
                    if entry.end is not None or self._cursor < entry.start:
                        raise ValueError("Animation is outside the component's lifetime")
                    if any(t.property == key and t.start + t.duration > self._cursor + 1e-9 for t in entry.tracks):
                        raise ValueError(
                            f"Animations for {key} must be authored in chronological order without overlaps"
                        )
        for animation in animations:
            self.add(animation.component)
            entry = self._objects[animation.component]
            state = entry.state_at(self._cursor)
            for key, target in animation.targets.items():
                initial = (animation.starts or {}).get(key, state[key])
                entry.tracks.append(Track(key, self._cursor, duration, initial, target, rate_func))
        self._cursor += duration
        return self

    def wait(self, duration: float = 1.0) -> Self:
        self._cursor += finite(duration, "duration", 0)
        return self

    def add_audio(
        self,
        path: str | Path,
        *,
        start: float | None = None,
        trim_start: float = 0,
        trim_end: float | None = None,
        volume: float = 1,
        fade_in: float = 0,
        fade_out: float = 0,
    ) -> Self:
        self.audio.append(
            AudioClip(path, self._cursor if start is None else start, trim_start, trim_end, volume, fade_in, fade_out)
        )
        return self


class Sequence(Renderable):
    def __init__(self, *children: Renderable, crossfade: float = 0.0, canvas: Canvas | None = None) -> None:
        if not children:
            raise ValueError("Sequence requires children")
        self.children = list(children)
        self.canvas = canvas or children[0].canvas
        self.crossfade = finite(crossfade, "crossfade", 0)

    @property
    def starts(self) -> list[float]:
        durations = [c.duration for c in self.children]
        if any(d <= 0 for d in durations):
            raise ValueError("Sequence children must have positive durations")
        if len(durations) > 1 and self.crossfade:
            for i, duration in enumerate(durations):
                required = self.crossfade * (2 if 0 < i < len(durations) - 1 else 1)
                if required > duration:
                    raise ValueError("Crossfades must fit child durations without triple overlaps")
        starts = [0.0]
        for duration in durations[:-1]:
            starts.append(starts[-1] + duration - self.crossfade)
        return starts

    @property
    def duration(self) -> float:
        return self.starts[-1] + self.children[-1].duration


class Grid(Renderable):
    def __init__(
        self, *children: Renderable, rows: int = 2, columns: int = 3, canvas: Canvas | None = None, gap: float = 0
    ) -> None:
        if any(not isinstance(x, int) or isinstance(x, bool) or x <= 0 for x in (rows, columns)):
            raise ValueError("rows and columns must be positive integers")
        if not children or len(children) > rows * columns:
            raise ValueError("Grid needs between 1 and rows * columns children")
        self.children = list(children)
        self.rows, self.columns = rows, columns
        self.canvas = canvas or Canvas()
        self.gap = finite(gap, "gap", 0)
        if self.gap * (columns - 1) >= self.canvas.width or self.gap * (rows - 1) >= self.canvas.height:
            raise ValueError("Grid gaps leave no room for cells")

    @property
    def duration(self) -> float:
        return max(c.duration for c in self.children)
