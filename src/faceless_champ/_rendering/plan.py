"""Private, owned scene snapshots and immutable execution records.

Visual objects are the single snapshots captured by Scene.add, never authoring
objects. Backends treat them as read-only; mutable native sessions live elsewhere.
Group edges and track indexes are compiled once instead of copying subtrees.
"""

from bisect import bisect_right
from dataclasses import dataclass
from types import MappingProxyType


def freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class TrackSpec:
    property: str
    start: float
    duration: float
    initial: object
    target: object
    easing: object
    keyframes: tuple | None

    def value_at(self, time):
        from .evaluate import track_value

        return track_value(self, time)


@dataclass(frozen=True, eq=False)
class NodeSpec:
    id: int
    component: object
    start: float
    end: float | None
    initial: object
    tracks: tuple
    track_index: tuple
    parent_id: int | None
    child_ids: tuple
    resource_id: int | None

    def state_at(self, time):
        state = dict(self.initial)
        for name, starts, tracks in self.track_index:
            offset = bisect_right(starts, time) - 1
            if offset >= 0:
                state[name] = tracks[offset].value_at(time)
        return state


@dataclass(frozen=True, eq=False)
class ResourceSpec:
    id: int
    descriptor: object


@dataclass(frozen=True, eq=False)
class SceneSpec:
    canvas: object
    duration: float
    nodes: tuple
    roots: tuple
    resources: tuple
    audio: tuple
    terminal_introduction: bool


@dataclass(frozen=True, eq=False)
class CompositionSpec:
    kind: str
    canvas: object
    duration: float
    children: tuple
    starts: tuple
    crossfade: float = 0
    rows: int = 1
    columns: int = 1
    padding: tuple = (0, 0, 0, 0)
    gap: float = 0
    effects: object = None
    transition: object = None


@dataclass(frozen=True)
class Placement:
    node: object
    time: float
    viewport: tuple
    background: str


def compile_scene(scene):
    scene.build()
    key = scene._revision, scene.canvas
    if scene._compiled_key == key:
        return scene._compiled_plan
    ids = {id(entry): index for index, entry in enumerate(scene.entries)}
    resources, nodes = [], []
    from ..sources import Viewport, source_from_component

    for index, entry in enumerate(scene.entries):
        component = entry.component
        source = component.source if isinstance(component, Viewport) else None
        if source is None and callable(getattr(component, "frame_key", None)):
            source = source_from_component(component)
        resource_id = None
        if source is not None:
            resource_id = len(resources)
            resources.append(ResourceSpec(resource_id, source))
        tracks = tuple(
            TrackSpec(
                t.property, t.start, t.duration, freeze(t.initial), freeze(t.target), t.easing, freeze(t.keyframes)
            )
            for t in entry.tracks
        )
        grouped = {}
        for track in tracks:
            grouped.setdefault(track.property, []).append(track)
        nodes.append(
            NodeSpec(
                index,
                component,
                entry.start,
                entry.end,
                freeze(entry.initial),
                tracks,
                tuple((name, tuple(t.start for t in values), tuple(values)) for name, values in grouped.items()),
                ids[id(entry.parent)] if entry.parent is not None else None,
                tuple(ids[id(child)] for child in sorted(entry.children, key=lambda e: e.component.z_index)),
                resource_id,
            )
        )
    roots = tuple(n.id for n in sorted((n for n in nodes if n.parent_id is None), key=lambda n: n.component.z_index))
    duration = scene.duration
    result = SceneSpec(
        scene.canvas,
        duration,
        tuple(nodes),
        roots,
        tuple(resources),
        tuple(scene.audio),
        any(n.start == duration for n in nodes),
    )
    scene._compiled_key, scene._compiled_plan = key, result
    scene._evaluated_frame = None
    return result


def compile_renderable(node):
    from ..timeline import Grid, Layer, Scene, Sequence

    if isinstance(node, Scene):
        return compile_scene(node)
    if not isinstance(node, (Sequence, Grid, Layer)):
        raise TypeError(f"Unsupported renderable: {type(node).__name__}")
    children = tuple(compile_renderable(child) for child in node.children)
    settings = (
        node.canvas,
        getattr(node, "crossfade", 0),
        getattr(node, "rows", 1),
        getattr(node, "columns", 1),
        getattr(node, "padding", (0, 0, 0, 0)),
        getattr(node, "gap", 0),
        getattr(node, "start_times", ()),
        getattr(node, "effects", None),
        getattr(node, "transition", None),
    )
    key = tuple(id(child) for child in children), settings
    if getattr(node, "_compiled_key", None) == key:
        return node._compiled_plan
    kind = "sequence" if isinstance(node, Sequence) else "grid" if isinstance(node, Grid) else "layer"
    starts = (
        tuple(node.starts) if isinstance(node, Sequence) else tuple(node.start_times) if isinstance(node, Grid) else ()
    )
    result = CompositionSpec(
        kind, node.canvas, node.duration, children, starts, *settings[1:6], effects=settings[7], transition=settings[8]
    )
    node._compiled_key, node._compiled_plan = key, result
    return result
