"""Deterministic scenes and compositional timelines."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any, Self

from .animation import Animation, interpolate, relative_value, smooth
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
    keyframes: tuple[tuple[float, object], ...] | None = None

    def value_at(self, time: float):
        progress = (time - self.start) / self.duration
        if progress <= 0:
            return self.initial
        if progress >= 1:
            return self.target
        if self.keyframes:
            for (left, initial), (right, target) in pairwise(self.keyframes):
                if progress <= right:
                    local = (progress - left) / (right - left)
                    return interpolate(initial, target, self.easing(local))
        return interpolate(self.initial, self.target, self.easing(progress))


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
                state[track.property] = track.value_at(time)
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

    def play(
        self, *animations: Animation, run_time: float = 1.0, rate_func: Callable[[float], float] | None = None
    ) -> Self:
        duration = finite(run_time, "run_time", 0.000001)
        if not animations:
            raise ValueError("play requires at least one animation")
        if rate_func is not None and not callable(rate_func):
            raise TypeError("rate_func must be callable")
        seen = set()
        prepared = []
        for animation in animations:
            if not isinstance(animation, Animation) or not animation.targets:
                raise TypeError("play requires nonempty animations")
            if not isinstance(animation.component, Component):
                raise TypeError("Animation requires a Component")
            if animation.rate_func is not None and not callable(animation.rate_func):
                raise TypeError("Animation rate_func must be callable")
            if set(animation.starts or {}) - set(animation.targets):
                raise ValueError("Animation starts must refer to animated properties")
            if set(animation.keyframes or {}) - set(animation.targets):
                raise ValueError("Keyframes must refer to animated properties")
            if set(animation.relative) - (set(animation.targets) & {"position", "scale", "rotation"}):
                raise ValueError("Relative properties must be animated position, scale, or rotation")
            for properties in (animation.targets, animation.starts or {}):
                for key, value in properties.items():
                    if key not in animation.component.state():
                        raise ValueError(f"Unsupported animation property: {key}")
                    _validate_animated_value(key, value)
                    if key == "data":
                        animation.component.validate_data(value)
            entry = self._objects.get(animation.component)
            state = entry.state_at(self._cursor) if entry is not None else animation.component.state()
            tracks = []
            for key in animation.targets:
                identity = (animation.component, key)
                if identity in seen:
                    raise ValueError(f"Overlapping animations for property {key}")
                seen.add(identity)
                if entry is not None:
                    if entry.end is not None or self._cursor < entry.start:
                        raise ValueError("Animation is outside the component's lifetime")
                    if any(t.property == key and t.start + t.duration > self._cursor + 1e-9 for t in entry.tracks):
                        raise ValueError(
                            f"Animations for {key} must be authored in chronological order without overlaps"
                        )
                base = state[key]
                initial = (animation.starts or {}).get(key, base)
                target = animation.targets[key]
                relative = key in animation.relative
                if relative:
                    initial = (
                        relative_value(key, base, animation.starts[key]) if key in (animation.starts or {}) else base
                    )
                    target = relative_value(key, base, target)
                frames = None
                if key in (animation.keyframes or {}):
                    points = animation.keyframes[key]
                    if len(points) < 2:
                        raise ValueError("Keyframes need at least two points")
                    frames = []
                    previous = -1.0
                    for point in points:
                        if not isinstance(point, (tuple, list)) or len(point) != 2:
                            raise ValueError("Keyframes need (progress, value) pairs")
                        progress, value = point
                        progress = finite(progress, "keyframe progress", 0)
                        if progress > 1 or progress <= previous:
                            raise ValueError("Keyframe progress must increase strictly within [0, 1]")
                        _validate_animated_value(key, value)
                        if key == "data":
                            animation.component.validate_data(value)
                        value = relative_value(key, base, value) if relative else value
                        _validate_animated_value(key, value)
                        frames.append((progress, value))
                        previous = progress
                    if frames[0][0] != 0 or frames[-1][0] != 1:
                        raise ValueError("Keyframes must include progress 0 and 1")
                    if frames[-1][1] != target:
                        raise ValueError("Last keyframe must match the animation target")
                    if key in (animation.starts or {}) and frames[0][1] != initial:
                        raise ValueError("First keyframe must match the explicit animation start")
                    initial = frames[0][1]
                    frames = tuple(frames)
                _validate_animated_value(key, initial)
                _validate_animated_value(key, target)
                tracks.append(
                    Track(
                        key, self._cursor, duration, initial, target, rate_func or animation.rate_func or smooth, frames
                    )
                )
            prepared.append((animation.component, tracks))
        # Validate the whole play call before changing the scene.
        for component, tracks in prepared:
            self.add(component)
            self._objects[component].tracks.extend(tracks)
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


def _validate_animated_value(key: str, value) -> None:
    if key == "data":
        if not isinstance(value, tuple) or not value:
            raise ValueError("Animated data must be a nonempty numeric tuple")
        for item in value:
            finite(item, "data")
    elif key == "position":
        if not isinstance(value, tuple) or len(value) != 2:
            raise ValueError("Animated position must be an (x, y) tuple")
        for coordinate in value:
            finite(coordinate, "position")
    else:
        finite(value, key, 0.001 if key == "scale" else (None if key == "rotation" else 0))
        if key in {"opacity", "reveal", "draw"} and value > 1:
            raise ValueError(f"{key} must be <= 1")


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
        self,
        *children: Renderable,
        rows: int = 2,
        columns: int = 3,
        canvas: Canvas | None = None,
        gap: float = 0,
        padding: float | tuple[float, float, float, float] = 0,
        start_times: list[float] | tuple[float, ...] | None = None,
    ) -> None:
        if any(not isinstance(x, int) or isinstance(x, bool) or x <= 0 for x in (rows, columns)):
            raise ValueError("rows and columns must be positive integers")
        if not children or len(children) > rows * columns:
            raise ValueError("Grid needs between 1 and rows * columns children")
        self.children = list(children)
        self.rows, self.columns = rows, columns
        self.canvas = canvas or Canvas()
        self.gap = finite(gap, "gap", 0)
        if isinstance(padding, (int, float)):
            padding = (padding,) * 4
        if len(padding) != 4:
            raise ValueError("padding must be a number or (top, right, bottom, left)")
        self.padding = tuple(finite(v, "padding", 0) for v in padding)
        top, right, bottom, left = self.padding
        if (
            left + right + self.gap * (columns - 1) >= self.canvas.width
            or top + bottom + self.gap * (rows - 1) >= self.canvas.height
        ):
            raise ValueError("Grid gaps and padding leave no room for cells")
        if start_times is not None and len(start_times) != len(children):
            raise ValueError("start_times needs one offset per child")
        self.start_times = tuple(finite(t, "start time", 0) for t in (start_times or [0] * len(children)))

    @property
    def duration(self) -> float:
        return max(start + child.duration for start, child in zip(self.start_times, self.children))


class Layer(Renderable):
    """Composite children in order on one canvas, mixing their audio.

    Use transparent child canvases (``bg="#00000000"``) for overlays. Shorter
    children hold their final frame, as they do in a Grid.
    """

    def __init__(self, *children: Renderable, canvas: Canvas | None = None) -> None:
        if not children:
            raise ValueError("Layer requires children")
        self.children = list(children)
        self.canvas = canvas or children[0].canvas

    @property
    def duration(self) -> float:
        return max(child.duration for child in self.children)
