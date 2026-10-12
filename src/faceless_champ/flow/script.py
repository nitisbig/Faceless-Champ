"""Named actions with explicit local timing and immutable argument snapshots."""

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from .model import FlowDataError, choice, color, number, object_fields, point, text

OPTIONS = {
    "reveal": {"stagger"},
    "hide": set(),
    "move": {"position"},
    "scale": {"value"},
    "rotate": {"value"},
    "signal": {"direction", "repeat", "marker", "color"},
    "highlight": {"dim", "color", "mode"},
    "draw": {"tool", "stagger"},
}


@dataclass(frozen=True)
class FlowAction:
    kind: str
    targets: tuple[str, ...]
    at: float
    duration: float
    args: tuple

    @property
    def options(self):
        return dict(self.args)

    @property
    def end(self):
        return self.at + self.duration + self.options.get("stagger", 0) * (len(self.targets) - 1)


class FlowScript:
    def __init__(self):
        self._actions = []

    @property
    def actions(self):
        return tuple(self._actions)

    @property
    def duration(self):
        return max((a.end for a in self._actions), default=0)

    def _add(self, kind, targets, *, at=None, duration=1, **args):
        choice(kind, OPTIONS, "action.kind")
        if isinstance(targets, str):
            targets = (targets,)
        elif isinstance(targets, (tuple, list)):
            targets = tuple(targets)
        else:
            raise FlowDataError("action.targets", "expected an ID or array of IDs")
        if not targets:
            raise FlowDataError("action.targets", "at least one target required")
        for id in targets:
            text(id, "action.targets")
        if len(targets) != len(set(targets)):
            raise FlowDataError("action.targets", "duplicate targets")
        object_fields(
            args,
            OPTIONS[kind],
            f"action.{kind}",
            ("position",) if kind == "move" else ("value",) if kind in {"scale", "rotate"} else (),
        )
        at = self.duration if at is None else number(at, "action.at", 0)
        duration = number(duration, "action.duration", 0.000001)
        if "position" in args:
            args["position"] = point(args["position"], "action.position")
        if "value" in args:
            number(args["value"], "action.value", 0.001 if kind == "scale" else None)
        if "stagger" in args:
            number(args["stagger"], "action.stagger", 0)
        if "color" in args:
            color(args["color"], "action.color")
        if "dim" in args:
            number(args["dim"], "action.dim", 0)
            if args["dim"] > 1:
                raise FlowDataError("action.dim", "must be <= 1")
        for key, values in (
            ("direction", ("forward", "reverse")),
            ("marker", ("dot", "packet")),
            ("mode", ("outline", "tint")),
            ("tool", ("none", "pen", "pencil")),
        ):
            if key in args:
                choice(args[key], values, f"action.{key}")
        if "repeat" in args and (
            isinstance(args["repeat"], bool) or not isinstance(args["repeat"], int) or args["repeat"] < 1
        ):
            raise FlowDataError("action.repeat", "must be a positive integer")
        action = FlowAction(kind, targets, at, duration, tuple(sorted(args.items())))
        properties = {"reveal": "visibility", "hide": "visibility", "draw": "visibility"}
        prop = properties.get(kind, kind)
        for old in self._actions:
            if properties.get(old.kind, old.kind) != prop:
                continue
            for id in set(targets) & set(old.targets):
                start = at + targets.index(id) * args.get("stagger", 0)
                previous = old.at + old.targets.index(id) * old.options.get("stagger", 0)
                if max(start, previous) < min(start + duration, previous + old.duration) - 1e-9:
                    raise FlowDataError(id, f"overlapping {prop} actions")
        self._actions.append(action)
        return self

    def reveal(self, targets, **kwargs):
        return self._add("reveal", targets, **kwargs)

    def hide(self, targets, **kwargs):
        return self._add("hide", targets, **kwargs)

    def move(self, targets, position, **kwargs):
        return self._add("move", targets, position=position, **kwargs)

    def scale(self, targets, value, **kwargs):
        return self._add("scale", targets, value=value, **kwargs)

    def rotate(self, targets, value, **kwargs):
        return self._add("rotate", targets, value=value, **kwargs)

    def signal(self, targets, **kwargs):
        return self._add("signal", targets, **kwargs)

    def highlight(self, targets, **kwargs):
        return self._add("highlight", targets, **kwargs)

    def draw(self, targets, **kwargs):
        return self._add("draw", targets, **kwargs)

    def to_dict(self):
        return {
            "actions": [
                {"kind": a.kind, "targets": list(a.targets), "at": a.at, "duration": a.duration, **a.options}
                for a in self.actions
            ]
        }

    @classmethod
    def from_dict(cls, data):
        object_fields(data, ("actions",), "script")
        if not isinstance(data.get("actions", []), (tuple, list)):
            raise FlowDataError("script.actions", "expected an array")
        result = cls()
        for i, raw in enumerate(data.get("actions", ())):
            if not isinstance(raw, dict):
                raise FlowDataError(f"script.actions[{i}]", "expected an object")
            action = deepcopy(raw)
            choice(action.get("kind"), OPTIONS, f"script.actions[{i}].kind")
            object_fields(
                action,
                {"kind", "targets", "at", "duration"} | OPTIONS.get(action.get("kind"), set()),
                f"script.actions[{i}]",
                ("kind", "targets"),
            )
            try:
                result._add(action.pop("kind"), action.pop("targets"), **action)
            except (ValueError, TypeError) as exc:
                raise FlowDataError(f"script.actions[{i}]", str(exc)) from exc
        return result

    @classmethod
    def from_json(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text()))
