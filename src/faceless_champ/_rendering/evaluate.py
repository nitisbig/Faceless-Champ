"""Shared arbitrary-time, composition, geometry and isolation evaluation."""

import math
from copy import copy
from dataclasses import dataclass, field
from itertools import pairwise
from math import nextafter
from types import MappingProxyType

from ..layout import Bounds, Group
from ..motion import matrix, multiply, point, style_value
from .plan import CompositionSpec, Placement


def track_value(track, time):
    from ..animation import interpolate

    progress = (time - track.start) / track.duration
    if progress <= 0:
        return track.initial
    if progress >= 1:
        return track.target
    if track.keyframes:
        for (left, initial), (right, target) in pairwise(track.keyframes):
            if progress <= right:
                return interpolate(initial, target, track.easing((progress - left) / (right - left)))
    return interpolate(track.initial, track.target, track.easing(progress))


@dataclass(frozen=True, eq=False)
class EvaluatedEntry:
    node: object
    state: object
    time: float
    parent: object = field(default=None, repr=False)
    children: tuple = field(default=(), repr=False)
    visible: bool = False
    age: float = 0
    effects: object = None
    isolate: bool = False

    @property
    def component(self):
        return self.node.component

    @property
    def start(self):
        return self.node.start

    @property
    def end(self):
        return self.node.end

    @property
    def initial(self):
        return self.node.initial

    def state_at(self, time):
        return self.state if time == self.time else self.node.state_at(time)

    def ancestors(self):
        parent = self.parent
        while parent is not None:
            yield parent
            parent = parent.parent


@dataclass(frozen=True)
class Geometry:
    node_id: int
    world: tuple
    logical: object
    ink: object
    visible: bool
    opacity: float
    age: float
    source_time: float
    resource_key: object
    isolate: bool


@dataclass(frozen=True)
class FramePlan:
    scene: object
    time: float
    entries: tuple
    roots: tuple
    geometry: tuple = ()
    affine: bool = False


def evaluate_frame(scene, time, *, measurement=None, geometry=True, resource_keys=True):
    """Evaluate every indexed track once; optionally produce logical/ink geometry."""
    from ..components import finite
    from .plan import SceneSpec, compile_scene

    time = finite(time, "frame time")
    owner = None if isinstance(scene, SceneSpec) else scene
    spec = scene if owner is None else compile_scene(scene)
    cached = getattr(owner, "_evaluated_frame", None)
    if cached is not None and cached.scene is spec and cached.time == time:
        frame = cached
    else:
        entries = []
        for node in spec.nodes:
            parent = entries[node.parent_id] if node.parent_id is not None else None
            state = MappingProxyType(node.state_at(time))
            c = node.component
            visible = node.start <= time and (node.end is None or time < node.end) and state["opacity"] > 0
            visible = visible and (parent is None or parent.visible)
            effects = c.effects.evaluated(state) if c.effects is not None else None
            entries.append(
                EvaluatedEntry(
                    node,
                    state,
                    time,
                    parent,
                    visible=visible,
                    age=max(0, time - node.start),
                    effects=effects,
                    isolate=effects is not None
                    or c.mask is not None
                    or c.drop_shadow is not None
                    or state["clip"] != (0, 0, 1, 1),
                )
            )
        for entry in entries:
            object.__setattr__(entry, "children", tuple(entries[i] for i in entry.node.child_ids))
        affine = any(
            e.component.mask is not None
            or e.component.drop_shadow is not None
            or e.state["clip"] != (0, 0, 1, 1)
            or e.state["scale_x"] != 1
            or e.state["scale_y"] != 1
            for e in entries
        )
        frame = FramePlan(spec, time, tuple(entries), tuple(entries[i] for i in spec.roots), affine=affine)
        if owner is not None:
            owner._evaluated_frame = frame
    if not geometry:
        return frame
    from ..motion import IDENTITY
    from .measure import measurement_session

    measure = measurement or measurement_session()
    worlds, boxes, logical, inks, records = {}, {}, {}, {}, {}
    for entry in frame.entries:
        parent = worlds[entry.parent.node.id] if entry.parent is not None else IDENTITY
        if isinstance(entry.component, Group):
            worlds[entry.node.id] = multiply(parent, matrix(entry.state, entry.component._origin))
        else:
            worlds[entry.node.id], boxes[entry.node.id] = entry_geometry(entry, time, parent, measure)
            # Logical layout reserves captions' full phrase box rather than the
            # current gap sprite; otherwise use the same leaf transform contract.
            logical[entry.node.id] = measure.entry_bounds(entry, time, ancestors=True)
    for entry in reversed(frame.entries):
        c, state, index = entry.component, entry.state, entry.node.id
        if isinstance(c, Group):
            logical[index] = union(tuple(logical[child.node.id] for child in entry.children))
            box = union(tuple(inks[child.node.id] for child in entry.children))
            pad = c.effects.evaluated(state).padding * density(worlds[index]) if c.effects is not None else 0
            inks[index] = Bounds(box.left - pad, box.top - pad, box.right + pad, box.bottom + pad)
        else:
            from ..surfaces import _shadow_padding

            box = component_ink_box(c, boxes[index])
            pad = _shadow_padding(c.drop_shadow) + (c.effects.evaluated(state).padding if c.effects else 0)
            inks[index] = transformed_box(
                Bounds(box.left - pad, box.top - pad, box.right + pad, box.bottom + pad), worlds[index]
            )
    for entry in frame.entries:
        c, state, index = entry.component, entry.state, entry.node.id
        parent = records.get(entry.parent.node.id) if entry.parent is not None else None
        visible, age = entry.visible, entry.age
        source_time = c.source_time(age) if callable(getattr(c, "source_time", None)) else age
        key = measure.age_key(c, age) if resource_keys else None
        records[index] = Geometry(
            index,
            worlds[index],
            logical[index],
            inks[index],
            visible,
            state["opacity"] * (parent.opacity if parent else 1),
            age,
            source_time,
            key,
            entry.isolate,
        )
    return FramePlan(spec, time, frame.entries, frame.roots, tuple(records.values()), frame.affine)


def render_signature(node, time, measurement=None):
    """One visibility/source-age/effect identity policy for every backend."""
    from ..timeline import Scene
    from .measure import measurement_session

    measure = measurement or measurement_session()
    if isinstance(node, Scene):
        frame = evaluate_frame(node, time, geometry=False)
        return (
            frame.scene.canvas,
            tuple(
                (
                    e.node.id,
                    e.node.parent_id,
                    e.component,
                    e.start,
                    e.end,
                    e.visible,
                    tuple(e.state.items()),
                    measure.age_key(e.component, e.age) if e.visible else None,
                    e.age
                    if e.visible and e.effects is not None and (e.effects.distortion or e.effects.light_sweep)
                    else None,
                )
                for e in frame.entries
            ),
        )
    parts, progress = composition_plan(node, time, (node.canvas.width, node.canvas.height))
    effects = getattr(node, "effects", None)
    return (
        node.canvas,
        progress,
        getattr(node, "transition", None),
        effects,
        time if effects and (effects.distortion or effects.light_sweep) else None,
        tuple((p.viewport, p.background, render_signature(p.node, p.time, measure)) for p in parts),
    )


def sprite_key(c, state, factor, age, measurement):
    return (
        c,
        tuple(
            (k, v)
            for k, v in state.items()
            if k not in {"position", "rotation", "scale", "scale_x", "scale_y", "opacity"}
        ),
        factor,
        measurement.age_key(c, age),
    )


def scene_entries(scene, time):
    return evaluate_frame(scene, time, geometry=False).entries


def union(boxes):
    return Bounds(
        min(b.left for b in boxes), min(b.top for b in boxes), max(b.right for b in boxes), max(b.bottom for b in boxes)
    )


def density(world):
    a, b, c, d, _, _ = world
    trace, det = a * a + b * b + c * c + d * d, (a * d - b * c) ** 2
    return max(0.001, math.sqrt((trace + math.sqrt(max(0, trace * trace - 4 * det))) / 2))


def fit(canvas, size):
    ratio = min(size[0] / canvas.width, size[1] / canvas.height)
    fitted = max(1, round(canvas.width * ratio)), max(1, round(canvas.height * ratio))
    return fitted, ((size[0] - fitted[0]) // 2, (size[1] - fitted[1]) // 2)


def _held_time(time, node):
    from .plan import SceneSpec, compile_renderable

    node = node if isinstance(node, (SceneSpec, CompositionSpec)) else compile_renderable(node)
    duration = node.duration
    if time < duration:
        return time
    if duration <= 0:
        return 0
    # Composite nodes resolve their own terminal children, so preserve their
    # exact boundary until reaching a scene. Explicit terminal introductions
    # retain the existing final-state contract (e.g. wait(1).add(component)).
    if not isinstance(node, SceneSpec) or node.terminal_introduction:
        return duration
    # Lifetimes are end-exclusive. Hold the visual left limit, not the state
    # after terminal removals/caption expiry; leave audio on its own clock.
    return nextafter(duration, -float("inf"))


def composition_plan(node, time, size):
    from .plan import compile_renderable

    authored = None if isinstance(node, CompositionSpec) else node
    node = node if authored is None else compile_renderable(node)
    children = node.children if authored is None else authored.children
    full = (0, 0, *size)
    if node.kind == "sequence":
        starts = node.starts
        active = [i for i, (s, c) in enumerate(zip(starts, node.children)) if s <= time < s + c.duration]
        holding = not active and time >= node.duration
        if holding:
            active = [len(node.children) - 1]
        parts = tuple(
            Placement(
                children[i],
                _held_time(time - starts[i], node.children[i]) if holding else time - starts[i],
                full,
                node.canvas.bg,
            )
            for i in active
        )
        progress = min(1, (time - starts[active[1]]) / node.crossfade) if len(active) == 2 else None
        return parts, progress
    if node.kind == "grid":
        sx, sy = size[0] / node.canvas.width, size[1] / node.canvas.height
        top, right_pad, bottom_pad, left = node.padding
        cw = (node.canvas.width - left - right_pad - node.gap * (node.columns - 1)) / node.columns
        ch = (node.canvas.height - top - bottom_pad - node.gap * (node.rows - 1)) / node.rows
        parts = []
        for i, (start, child) in enumerate(zip(node.starts, node.children)):
            if time < start:
                continue
            col, row = i % node.columns, i // node.columns
            x, y = round((left + col * (cw + node.gap)) * sx), round((top + row * (ch + node.gap)) * sy)
            r, b = round((left + col * (cw + node.gap) + cw) * sx), round((top + row * (ch + node.gap) + ch) * sy)
            parts.append(
                Placement(
                    children[i],
                    _held_time(time - start, child),
                    (x, y, max(1, r - x), max(1, b - y)),
                    node.canvas.bg,
                )
            )
        return tuple(parts), None
    if node.kind == "layer":
        return tuple(
            Placement(c, _held_time(time, spec), full, "#00000000") for c, spec in zip(children, node.children)
        ), None
    raise TypeError(f"Unsupported renderable: {type(node).__name__}")


def evaluated(entry, time):
    view = copy(entry.component)
    for key, value in entry.state_at(time).items():
        if hasattr(view, key):
            setattr(view, key, style_value(key, value))
    if isinstance(view, Group):
        view._children = tuple(evaluated(child, time) for child in entry.children)
    return view


def component_size(c, state, raster, age):
    from .measure import measurement_session

    measure = getattr(raster, "measurement", None) or measurement_session()
    return measure.size(c, state, age=age)


def entry_geometry(entry, time, parent, raster):
    c, state = entry.component, entry.state_at(time)
    if isinstance(c, Group):
        from .measure import measurement_session

        measure = getattr(raster, "measurement", None) or measurement_session()
        boxes = [measure.entry_bounds(child, time) for child in entry.children]
        box = Bounds(
            min(b.left for b in boxes),
            min(b.top for b in boxes),
            max(b.right for b in boxes),
            max(b.bottom for b in boxes),
        )
        return multiply(parent, matrix(state, c._origin)), box
    w, h = component_size(c, state, raster, max(0, time - entry.start))
    local = dict(state)
    if c.anchor == "top_left":
        local["position"] = (
            state["position"][0] + w * state["scale"] * state["scale_x"] / 2,
            state["position"][1] + h * state["scale"] * state["scale_y"] / 2,
        )
    return multiply(parent, matrix(local)), Bounds(-w / 2, -h / 2, w / 2, h / 2)


def transformed_box(box, world):
    points = [
        point(world, x, y)
        for x, y in ((box.left, box.top), (box.right, box.top), (box.right, box.bottom), (box.left, box.bottom))
    ]
    return Bounds(
        min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)
    )


def component_ink_box(c, box):
    from ..procedural import ParticleField

    if isinstance(c, ParticleField):
        # Centers wrap inside the field, but the shader's quads include a
        # one-design-pixel fringe for antialiasing beyond each particle radius.
        pad = c.radius + 1
        return Bounds(-c.width / 2 - pad, -c.height / 2 - pad, c.width / 2 + pad, c.height / 2 + pad)
    return box


def ink_box(entry, time, parent, raster):
    from ..surfaces import _shadow_padding

    c = entry.component
    world, box = entry_geometry(entry, time, parent, raster)
    if isinstance(c, Group):
        boxes = [ink_box(child, time, world, raster) for child in entry.children]
        result = Bounds(
            min(b.left for b in boxes),
            min(b.top for b in boxes),
            max(b.right for b in boxes),
            max(b.bottom for b in boxes),
        )
        if c.effects is not None:
            pad = c.effects.evaluated(entry.state_at(time)).padding * density(world)
            result = Bounds(result.left - pad, result.top - pad, result.right + pad, result.bottom + pad)
        return result
    effects = c.effects.evaluated(entry.state_at(time)) if c.effects is not None else None
    box = component_ink_box(c, box)
    pad = _shadow_padding(c.drop_shadow) + (effects.padding if effects else 0)
    return transformed_box(Bounds(box.left - pad, box.top - pad, box.right + pad, box.bottom + pad), world)
