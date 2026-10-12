"""Self-contained deterministic graph playback and document serialization."""

import json
from bisect import bisect_right
from collections import OrderedDict
from copy import deepcopy
from dataclasses import asdict
from itertools import pairwise
from pathlib import Path

from PIL import Image

from ..components import Component
from ..layout import Bounds
from .geometry import edge_path, layout_graph, length, sample, transform
from .model import FlowDataError, FlowGraph, FlowTheme, construct, number, object_fields
from .script import FlowScript
from .symbols import symbol_paths


class FlowChamp(Component):
    def __init__(
        self, graph, script=None, *, width=1600, height=900, theme=None, source_start=0, label_cache_mb=8, **kwargs
    ):
        super().__init__(**kwargs)
        if not isinstance(graph, FlowGraph) or (script is not None and not isinstance(script, FlowScript)):
            raise FlowDataError("flow", "expected FlowGraph and FlowScript")
        self.graph = deepcopy(graph)
        self.script = deepcopy(script or FlowScript())
        self.theme = deepcopy(theme or FlowTheme())
        if not isinstance(self.theme, FlowTheme):
            raise FlowDataError("theme", "expected FlowTheme")
        self.width = number(width, "width", 1)
        self.height = number(height, "height", 1)
        self.duration = self.script.duration
        self.source_start = number(source_start, "source_start", 0)
        if self.source_start > self.duration:
            raise FlowDataError("source_start", "exceeds script duration")
        self._nodes = {n.id: n for n in self.graph.nodes}
        self._edges = {e.id: e for e in self.graph.edges}
        self._positions = layout_graph(self.graph, self.width, self.height)
        self._actions = tuple(sorted(self.script.actions, key=lambda a: a.at))
        self._label_cache_limit = int(number(label_cache_mb, "label_cache_mb", 0) * 1024 * 1024)
        self._label_cache = OrderedDict()
        self._label_cache_bytes = 0
        self._intervals = tuple(
            (a.at + i * a.options.get("stagger", 0), a.at + i * a.options.get("stagger", 0) + a.duration, a.kind)
            for a in self._actions
            for i in range(len(a.targets))
        )
        self._boundaries = tuple(sorted({0.0, *(t for start, end, _ in self._intervals for t in (start, end))}))
        for action in self._actions:
            for id in action.targets:
                if id not in self._nodes and id not in self._edges:
                    raise FlowDataError(id, "unknown action target")
                if action.kind in {"move", "scale", "rotate"} and id not in self._nodes:
                    raise FlowDataError(id, f"{action.kind} requires a node")
                if action.kind == "signal" and id not in self._edges:
                    raise FlowDataError(id, "signal requires edges")
            if action.kind == "signal":
                edges = [self._edges[id] for id in action.targets]
                if any(a.target != b.source for a, b in pairwise(edges)):
                    raise FlowDataError("signal", "edge sequence must be connected in source-to-target order")
        self._images = {}
        for n in graph.nodes:
            if n.image:
                try:
                    with Image.open(n.image) as source:
                        self._images[n.id] = source.convert("RGBA").copy()
                except (OSError, ValueError) as exc:
                    raise FlowDataError(n.id, f"cannot load image: {n.image}") from exc
        # Labels are measured once, never reflowed between animation frames.
        from .drawing import prepare_labels

        self._labels = prepare_labels(self)
        self.diagnostics = tuple(self._diagnostics())

    def _diagnostics(self):
        boxes = {id: self.bounds_for(id, 0) for id in self._nodes}
        ids = list(boxes)
        for i, id in enumerate(ids):
            a = boxes[id]
            if a.left < 0 or a.top < 0 or a.right > self.width or a.bottom > self.height:
                yield {"code": "FLOW_BOUNDS", "element": id}
            for other in ids[i + 1 :]:
                b = boxes[other]
                if min(a.right, b.right) > max(a.left, b.left) and min(a.bottom, b.bottom) > max(a.top, b.top):
                    yield {"code": "FLOW_OVERLAP", "elements": [id, other]}

    def frame_key(self, age):
        time = min(self.duration, self.source_start + max(0, number(age, "age")))
        if any(start <= time < end and kind != "highlight" for start, end, kind in self._intervals):
            return time
        return self._boundaries[bisect_right(self._boundaries, time) - 1]

    def diagnostics_at(self, time):
        """Visible geometry warnings at original script time; does not change playback."""
        time = number(time, "time", 0)
        snapshot = self.state_at(time)
        states = snapshot["elements"]
        visible = {
            id
            for id, s in states.items()
            if s["opacity"] > 0
            and s["draw"] > 0
            and all(h["dim"] > 0 or id in h["targets"] for h in snapshot["highlights"])
        }
        nodes = {id: self._bounds_for(id, states, labels=False) for id in self._nodes if id in visible}
        labels = {id: self._label_bounds(id, states) for id in self._labels if id in visible}
        result = []

        def overlaps(a, b):
            return min(a.right, b.right) > max(a.left, b.left) and min(a.bottom, b.bottom) > max(a.top, b.top)

        for id in sorted(visible):
            b = self._bounds_for(id, states)
            if b.left < 0 or b.top < 0 or b.right > self.width or b.bottom > self.height:
                result.append({"code": "FLOW_BOUNDS", "element": id, "time": time})
        for i, (id, a) in enumerate(nodes.items()):
            for other, b in list(nodes.items())[i + 1 :]:
                if overlaps(a, b):
                    result.append({"code": "FLOW_OVERLAP", "elements": [id, other], "time": time})
        collisions = set()
        for id, a in labels.items():
            for other, b in (*nodes.items(), *labels.items()):
                if id != other and overlaps(a, b):
                    collisions.add(tuple(sorted((id, other))))
        result.extend(
            {"code": "FLOW_LABEL_OVERLAP", "elements": list(pair), "time": time} for pair in sorted(collisions)
        )
        return tuple(result)

    def _label_bounds(self, target, states):
        from .drawing import raster_label

        sprite, position = raster_label(self, target, states[target], 1)
        left, top = round(position[0] - sprite.width / 2), round(position[1] - sprite.height / 2)
        return Bounds(left, top, left + sprite.width, top + sprite.height)

    def _evaluate(self, time):
        states = {
            n.id: {
                "position": self._positions[n.id],
                "scale": n.scale,
                "rotation": n.rotation,
                "opacity": 1.0,
                "draw": 1.0,
            }
            for n in self.graph.nodes
        }
        states.update({e.id: {"opacity": 1.0, "draw": 1.0} for e in self.graph.edges})
        for a in self._actions:
            if a.kind in {"draw", "reveal"}:
                for id in a.targets:
                    states[id]["opacity"] = 0.0
        for a in self._actions:
            for i, id in enumerate(a.targets):
                start = a.at + i * a.options.get("stagger", 0)
                if time < start:
                    continue
                p = min(1.0, (time - start) / a.duration)
                s = states[id]
                if a.kind in {"move", "scale", "rotate"}:
                    key = {"move": "position", "scale": "scale", "rotate": "rotation"}[a.kind]
                    target = a.options["position" if a.kind == "move" else "value"]
                    old = s[key]
                    s[key] = (
                        tuple(x + (y - x) * p for x, y in zip(old, target))
                        if key == "position"
                        else old + (target - old) * p
                    )
                elif a.kind == "reveal":
                    s["opacity"] = p
                    s["draw"] = 1.0
                elif a.kind == "hide":
                    s["opacity"] *= 1 - p
                elif a.kind == "draw":
                    s["opacity"], s["draw"] = 1.0, p
        for e in self.graph.edges:
            states[e.id]["path"] = edge_path(e, self._nodes, states)
            states[e.id]["opacity"] *= min(states[e.source]["opacity"], states[e.target]["opacity"])
        return states

    def paths_for(self, id, states):
        if id in self._edges:
            return [states[id]["path"]]
        n, s = self._nodes[id], states[id]
        return [[transform((x * n.size[0], y * n.size[1]), s) for x, y in path] for path in symbol_paths(n.symbol)]

    def state_at(self, time):
        """Snapshot at original script time, independent of source_start and frame order."""
        time = number(time, "time", 0)
        states = self._evaluate(time)
        signals, highlights, tools = [], [], []
        for a in self._actions:
            if a.kind == "draw":
                for i, id in enumerate(a.targets):
                    start = a.at + i * a.options.get("stagger", 0)
                    if start <= time < start + a.duration and a.options.get("tool", "pencil") != "none":
                        paths = self.paths_for(id, states)
                        progress = (time - start) / a.duration
                        spans = [length(p) for p in paths]
                        remaining = sum(spans) * progress
                        for path, span in zip(paths, spans):
                            if remaining <= span or path is paths[-1]:
                                tools.append(
                                    {
                                        "target": id,
                                        "position": sample(path, remaining / span if span else 0),
                                        "tool": a.options.get("tool", "pencil"),
                                    }
                                )
                                break
                            remaining -= span
                continue
            if not a.at <= time < a.at + a.duration:
                continue
            if a.kind == "highlight":
                highlights.append(
                    {
                        "targets": a.targets,
                        "dim": a.options.get("dim", 1),
                        "color": a.options.get("color", self.theme.accent),
                        "mode": a.options.get("mode", "outline"),
                    }
                )
            elif a.kind == "signal":
                progress = ((time - a.at) / a.duration * a.options.get("repeat", 1)) % 1
                if a.options.get("direction", "forward") == "reverse":
                    progress = 1 - progress
                paths = [states[id]["path"] for id in a.targets]
                spans = [length(p) for p in paths]
                remaining = progress * sum(spans)
                for id, path, span in zip(a.targets, paths, spans):
                    if remaining <= span or id == a.targets[-1]:
                        local = remaining / span if span else 0
                        if states[id]["opacity"] > 0 and local <= states[id]["draw"]:
                            signals.append(
                                {
                                    "edge": id,
                                    "position": sample(path, local),
                                    "opacity": states[id]["opacity"],
                                    "marker": a.options.get("marker", "dot"),
                                    "color": a.options.get("color", self.theme.accent),
                                }
                            )
                        break
                    remaining -= span
        return {"elements": states, "signals": signals, "highlights": highlights, "tools": tools}

    def bounds_for(self, target, time=0):
        if target not in self._nodes and target not in self._edges:
            raise FlowDataError(target, "unknown target")
        states = self._evaluate(number(time, "time", 0))
        return self._bounds_for(target, states)

    def _bounds_for(self, target, states, *, labels=True):
        points = [p for path in self.paths_for(target, states) for p in path]
        # Reserve node rectangle too, including labels and custom images.
        if target in self._nodes:
            n = self._nodes[target]
            points += [
                transform((x * n.size[0] / 2, y * n.size[1] / 2), states[target])
                for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))
            ]
        if labels and target in self._labels:
            b = self._label_bounds(target, states)
            points += [(b.left, b.top), (b.right, b.bottom)]
        xs, ys = zip(*points)
        pad = self.theme.stroke_width / 2 + (12 if target in self._edges else 0)
        return Bounds(min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)

    def frame_image(self, age, factor=1):
        from .drawing import draw_frame

        return draw_frame(self, self.state_at(self.frame_key(age)), factor)

    def to_dict(self):
        return {
            "schema_version": 1,
            "width": self.width,
            "height": self.height,
            "source_start": self.source_start,
            "graph": self.graph.to_dict(),
            "script": self.script.to_dict(),
            "theme": asdict(self.theme),
        }

    @classmethod
    def from_dict(cls, data, *, base_path=None, **kwargs):
        object_fields(
            data,
            ("schema_version", "width", "height", "source_start", "graph", "script", "theme"),
            "$",
            ("schema_version", "graph"),
        )
        if type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise FlowDataError("schema_version", "expected 1")
        object_fields(data.get("theme", {}), asdict(FlowTheme()), "theme")
        theme_data = dict(data.get("theme", {}))
        if theme_data.get("font") is not None and base_path is not None:
            theme_data["font"] = str((Path(base_path) / theme_data["font"]).resolve())
        return cls(
            FlowGraph.from_dict(data["graph"], base_path=base_path),
            FlowScript.from_dict(data.get("script", {})),
            theme=construct(FlowTheme, theme_data, "theme"),
            width=data.get("width", 1600),
            height=data.get("height", 900),
            source_start=data.get("source_start", 0),
            **kwargs,
        )

    @classmethod
    def from_json(cls, path, **kwargs):
        path = Path(path)
        try:
            data = json.loads(path.read_text())
        except (ValueError, OSError) as exc:
            raise FlowDataError(str(path), str(exc)) from exc
        return cls.from_dict(data, base_path=path.parent, **kwargs)
