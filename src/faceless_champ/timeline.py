"""Deterministic scenes and compositional timelines."""

from __future__ import annotations

import math
from collections.abc import Callable
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import pairwise
from numbers import Real
from pathlib import Path
from typing import Any, Self

from .animation import Animation, relative_value, smooth
from .audio import AudioClip
from .components import Canvas, Component, finite
from .layout import Group
from .spring import _spring_progress_bounds
from .subtitles import Captions


class Renderable:
    canvas: Canvas

    def __getstate__(self):
        # Execution plans are process-local, rebuildable caches. Do not let
        # mapping proxies break existing composition deepcopy/pickle workflows.
        state = self.__dict__.copy()
        for name in ("_compiled_key", "_compiled_plan", "_evaluated_frame"):
            if name in state:
                state[name] = None
        return state

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
        from ._rendering.evaluate import track_value

        return track_value(self, time)


@dataclass
class Entry:
    component: Component
    start: float
    initial: dict
    tracks: list[Track]
    end: float | None = None
    parent: Entry | None = field(default=None, repr=False, compare=False)
    children: list[Entry] = field(default_factory=list, repr=False, compare=False)

    def ancestors(self):
        parent = self.parent
        while parent is not None:
            yield parent
            parent = parent.parent

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
        self._revision = 0
        self._compiled_key = self._compiled_plan = self._evaluated_frame = None

    def _invalidate(self):
        self._revision += 1
        self._compiled_key = self._compiled_plan = self._evaluated_frame = None

    def _compile(self):
        from ._rendering.plan import compile_scene

        return compile_scene(self)

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
                self._invalidate()
                raise
            finally:
                self._building = False
        return self

    @property
    def duration(self) -> float:
        self.build()
        caption_ends = [
            min(
                [e.start + e.component.track.duration]
                + [ancestor.end for ancestor in (e, *e.ancestors()) if ancestor.end is not None]
            )
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
        self._invalidate()
        try:
            yield self
        finally:
            self._cursor = max(previous, self._cursor)
            self._invalidate()

    def wait_until(self, time: float) -> Self:
        time = finite(time, "time", 0)
        if time < self._cursor - 1e-9:
            raise ValueError("wait_until cannot move backward; use with scene.at(time)")
        self._cursor = max(time, self._cursor)
        self._invalidate()
        return self

    def remove(self, *components: Component) -> Self:
        """End component lifetimes at the cursor without adding an animation."""
        for component in components:
            entry = self._objects.get(component)
            if entry is None or entry.end is not None:
                raise ValueError("remove requires a component currently in the scene")
            if self._cursor < entry.start:
                raise ValueError("Cannot remove a component before its start")
            if any(
                t.start + t.duration > self._cursor + 1e-9
                for descendant in self._descendants(entry)
                for t in descendant.tracks
            ):
                raise ValueError("Cannot remove a component before its animations end")
        for component in components:
            for entry in self._descendants(self._objects[component]):
                entry.end = min(entry.end, self._cursor) if entry.end is not None else self._cursor
        self._invalidate()
        return self

    @staticmethod
    def _descendants(entry):
        yield entry
        for child in entry.children:
            yield from Scene._descendants(child)

    def _prepare_add(self, components):
        """Validate a whole hierarchy before adding any snapshots or ownership."""
        memberships = {}

        def inspect(group, visiting):
            if group in visiting:
                raise ValueError("Group hierarchy cannot contain cycles")
            visiting = visiting | {group}
            for child in group.children:
                if not isinstance(child, Component):
                    raise TypeError("Group members must be Components")
                if child in memberships and memberships[child] is not group:
                    raise ValueError("A component cannot belong to multiple groups")
                memberships[child] = group
                if isinstance(child, Group):
                    inspect(child, visiting)

        for component in components:
            if not isinstance(component, Component):
                raise TypeError("Scene.add requires visual components")
            if isinstance(component, Group) and component not in self._objects:
                inspect(component, set())
        prepared = []
        seen = set()

        def visit(component, parent=None):
            if component in seen:
                return
            seen.add(component)
            if component in self._objects:
                entry = self._objects[component]
                if entry.end is not None:
                    raise ValueError("Removed components cannot be re-added; create a new instance")
                if parent is not None:
                    raise ValueError(
                        "Create groups before adding their members; existing components cannot be reparented"
                    )
                return
            prepared.append((component, parent))
            if isinstance(component, Group):
                for child in component.children:
                    visit(child, component)

        for component in components:
            if component not in memberships:
                visit(component)
        return prepared

    def add(self, *components: Component) -> Self:
        prepared = self._prepare_add(components)
        memo = {}
        snapshots = [(component, parent, deepcopy(component, memo)) for component, parent in prepared]
        for component, parent, snapshot in snapshots:
            parent_entry = self._objects[parent] if parent is not None else None
            entry = Entry(snapshot, self._cursor, component.state(), [], parent=parent_entry)
            self.entries.append(entry)
            self._objects[component] = entry
            if parent_entry is not None:
                parent_entry.children.append(entry)
        if snapshots:
            self._invalidate()
        return self

    def bounds_at(self, component: Component, time: float):
        """Conservative world bounds including animated geometry and ancestors.

        Masks, opacity and lifetimes do not shrink the reserved layout box.
        """
        from ._rendering.evaluate import scene_entries
        from ._rendering.measure import measurement_session

        self.build()
        time = finite(time, "time", 0)
        if component not in self._objects:
            raise ValueError("bounds_at requires a component in the scene")
        index = self.entries.index(self._objects[component])
        return measurement_session().entry_bounds(scene_entries(self, time)[index], time, ancestors=True)

    def ink_bounds_at(self, component: Component, time: float):
        """Conservative effect bounds without opening viewport sessions."""
        from ._rendering.evaluate import evaluate_frame

        self.build()
        time = finite(time, "time", 0)
        if component not in self._objects:
            raise ValueError("ink_bounds_at requires a component in the scene")
        index = self.entries.index(self._objects[component])
        return evaluate_frame(self, time, resource_keys=False).geometry[index].ink

    def play(self, *animations, run_time=None, rate_func=None) -> Self:
        from .scheduling import Schedule, play_schedule

        if any(isinstance(a, Schedule) for a in animations):
            return play_schedule(self, animations, run_time, rate_func)
        return self._play(*animations, run_time=1 if run_time is None else run_time, rate_func=rate_func)

    def _play(
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
            entry = self._objects.get(animation.component)
            state = entry.state_at(self._cursor) if entry is not None else animation.component.state()
            resolved = animation.resolve(state.copy())
            if (
                not isinstance(resolved, Animation)
                or resolved.component is not animation.component
                or not resolved.targets
            ):
                raise TypeError("Animation.resolve must return an Animation for the same component")
            animation = resolved
            if animation.rate_func is not None and not callable(animation.rate_func):
                raise TypeError("Animation rate_func must be callable")
            if set(animation.starts or {}) - set(animation.targets):
                raise ValueError("Animation starts must refer to animated properties")
            if set(animation.keyframes or {}) - set(animation.targets):
                raise ValueError("Keyframes must refer to animated properties")
            if set(animation.relative) - (set(animation.targets) & animation.component.relative_animation_properties):
                raise ValueError("Unsupported relative animation property")
            for properties in (animation.targets, animation.starts or {}):
                for key, value in properties.items():
                    if key not in animation.component.state():
                        raise ValueError(f"Unsupported animation property: {key}")
                    if key in animation.relative and key not in Component.relative_animation_properties:
                        finite(value, key)
                    else:
                        animation.component.validate_animation(key, value)
            tracks = []
            for key in animation.targets:
                identity = (animation.component, key)
                if identity in seen:
                    raise ValueError(f"Overlapping animations for property {key}")
                seen.add(identity)
                if entry is not None:
                    if any(
                        ancestor.end is not None or self._cursor < ancestor.start
                        for ancestor in (entry, *entry.ancestors())
                    ):
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
                        animation.component.validate_animation(key, value)
                        value = relative_value(key, base, value) if relative else value
                        animation.component.validate_animation(key, value)
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
                animation.component.validate_animation(key, initial)
                animation.component.validate_animation(key, target)
                track = Track(
                    key, self._cursor, duration, initial, target, rate_func or animation.rate_func or smooth, frames
                )
                _validate_spring_track(track)
                tracks.append(track)
            prepared.append((animation.component, tracks))
        # Validate the whole play call before changing the scene.
        self.add(*(component for component, _ in prepared))
        for component, tracks in prepared:
            self._objects[component].tracks.extend(tracks)
        self._cursor += duration
        self._invalidate()
        return self

    def wait(self, duration: float = 1.0) -> Self:
        self._cursor += finite(duration, "duration", 0)
        self._invalidate()
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
        self._invalidate()
        return self


def _validate_spring_track(track: Track) -> None:
    """Certify each resolved spring segment before publishing any scene changes.

    Interpolation's rounded subtraction, multiplication, and addition are
    monotone in progress for a fixed finite difference. Evaluating its interval
    endpoints therefore includes arithmetic rounding, without subtracting an
    arbitrary margin from an exactly valid initial scale of 0.001. Underdamped
    progress gets 32 additional outward ulps for kernel evaluation roundoff;
    nonoscillatory formulas stay in [0, 1], and forward progress never goes below
    zero. Reversed springs carry the transformed, already padded interval.
    These are continuous bounds, not frame samples or renderer clamps.
    """
    bounds = _spring_progress_bounds(track.easing)
    if bounds is None:
        return
    end_time = track.start + track.duration
    if not math.isfinite(end_time) or end_time <= track.start:
        raise ValueError("Spring animation interval must have a finite end after its start")
    # Use the representable clock interval so subtraction at its end gives the
    # identical duration, rather than progress one ulp below the terminal return.
    track.duration = end_time - track.start
    key = track.property
    if key not in {"position", "rotation", "scale", "scale_x", "scale_y"}:
        raise ValueError(
            f"Spring does not support animation property '{key}'; use a separate conventional easing track"
        )

    lower, upper = bounds
    points = track.keyframes or ((0, track.initial), (1, track.target))
    for segment, ((_, initial), (_, target)) in enumerate(pairwise(points), start=1):
        coordinates = zip(initial, target) if key == "position" else ((initial, target),)
        for start, end in coordinates:
            if not isinstance(start, Real) or not isinstance(end, Real):
                raise TypeError(f"Spring animation for {key} requires real numeric values")
            # Validate differences as well as endpoints: finite inputs can still
            # overflow in subtraction, multiplication, or overshoot addition.
            try:
                difference = end - start
                bounds = (start + difference * lower, start + difference * upper)
                finite_range = math.isfinite(difference) and all(math.isfinite(value) for value in bounds)
            except OverflowError:
                finite_range = False
            if not finite_range:
                raise ValueError(f"Spring animation for {key} has nonfinite interpolation in segment {segment}")
            if key in {"scale", "scale_x", "scale_y"} and min(bounds) < 0.001:
                raise ValueError(
                    f"Spring cannot certify {key} >= 0.001 throughout segment {segment}; "
                    "reduce overshoot or change scale endpoints"
                )


def _validate_animated_value(key, value):
    """Private compatibility forwarder; components own animation validation."""
    from .components import _validate_animated_value as validate

    return validate(key, value)


class Sequence(Renderable):
    def __init__(
        self, *children: Renderable, crossfade: float = 0.0, canvas: Canvas | None = None, transition=None
    ) -> None:
        if not children:
            raise ValueError("Sequence requires children")
        self.children = list(children)
        self.canvas = canvas or children[0].canvas
        self.crossfade = finite(crossfade, "crossfade", 0)
        from .transitions import transition as validate_transition

        self.transition = validate_transition(transition)
        if transition is not None and not self.crossfade:
            raise ValueError("A transition requires a positive crossfade overlap")

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

    def __init__(self, *children: Renderable, canvas: Canvas | None = None, effects=None) -> None:
        if not children:
            raise ValueError("Layer requires children")
        self.children = list(children)
        self.canvas = canvas or children[0].canvas
        from .effects import effect_stack

        self.effects = effect_stack(effects)

    @property
    def duration(self) -> float:
        return max(child.duration for child in self.children)
