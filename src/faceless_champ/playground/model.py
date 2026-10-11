"""Validated, serializable authoring contracts for CodingChamp playgrounds."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from types import MappingProxyType

from ..components import finite


class PlaygroundError(ValueError):
    def __init__(self, code, message, **scope):
        super().__init__(message)
        self.code, self.scope = code, scope

    def as_dict(self):
        return {"code": self.code, "message": str(self), **self.scope}


def fail(message, **scope):
    raise PlaygroundError("PLAYGROUND_SPEC", message, **scope)


def json_copy(value):
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (ValueError, TypeError) as exc:
        fail(f"Expected finite JSON data: {exc}")


def relative_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        fail("Source paths must be nonempty relative POSIX paths")
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in {"", ".", ".."} for x in value.split("/")) or ":" in value:
        fail(f"Source path must stay inside the project: {value!r}")
    return value


@dataclass(frozen=True)
class CodeCheckpoint:
    id: str
    files: dict[str, str]
    active_file: str
    entrypoint: str
    edit_start: float
    edit_end: float
    publish: float
    runtime: str = "python"
    first_line: int = 1
    inputs: dict = field(default_factory=dict)
    expected_failure: bool = False
    ready: tuple[str, ...] = ()
    web_script: object = None

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.strip():
            fail("Checkpoint id must be nonempty")
        if self.runtime not in {"python", "web"}:
            fail("runtime must be python or web", checkpoint=self.id)
        if not isinstance(self.files, dict) or not self.files:
            fail("files must contain the complete source revision", checkpoint=self.id)
        sources = {}
        for path, source in self.files.items():
            relative_path(path)
            if not isinstance(source, str):
                fail("Source contents must be strings", checkpoint=self.id, file=path)
            sources[path] = source
        for path in sources:
            if any(str(parent) in sources for parent in PurePosixPath(path).parents):
                fail("Source file is also a directory", checkpoint=self.id, file=path)
        if self.active_file not in sources or self.entrypoint not in sources:
            fail("active_file and entrypoint must exist in files", checkpoint=self.id)
        if self.runtime == "web" and not self.entrypoint.endswith((".html", ".htm")):
            fail("Web entrypoint must be HTML", checkpoint=self.id)
        for name in ("edit_start", "edit_end", "publish"):
            object.__setattr__(self, name, finite(getattr(self, name), name, 0))
        if not self.edit_start <= self.edit_end <= self.publish:
            fail("Require edit_start <= edit_end <= publish", checkpoint=self.id)
        if type(self.first_line) is not int or self.first_line < 1:
            fail("first_line must be a positive integer", checkpoint=self.id)
        if type(self.expected_failure) is not bool:
            fail("expected_failure must be boolean")
        if not isinstance(self.inputs, dict):
            fail("inputs must be a JSON object")
        if any(not isinstance(s, str) or not s.strip() for s in self.ready):
            fail("ready selectors must be nonempty strings")
        from ..web import WebScript

        if self.web_script is not None and not isinstance(self.web_script, WebScript):
            fail("web_script must be WebScript")
        object.__setattr__(self, "files", MappingProxyType(sources))
        object.__setattr__(self, "inputs", json_copy(self.inputs))
        object.__setattr__(self, "ready", tuple(self.ready))

    def __deepcopy__(self, memo):
        from copy import deepcopy

        return type(self)(
            **{
                name: deepcopy(dict(value) if name == "files" else value, memo)
                for name in self.__dataclass_fields__
                for value in (getattr(self, name),)
            }
        )

    def record(self):
        return {
            name: (dict(value) if name == "files" else value.record() if name == "web_script" and value else value)
            for name in self.__dataclass_fields__
            for value in (getattr(self, name),)
        }


def valid_canvas_value(kind, value):
    if kind in {"car", "object"}:
        return isinstance(value, dict)
    if kind == "collection":
        return isinstance(value, (dict, list))
    if kind in {"vector", "matrix"}:
        rows = [value] if kind == "vector" else value
        return (
            isinstance(rows, list)
            and bool(rows)
            and all(isinstance(r, list) and r for r in rows)
            and len({len(r) for r in rows}) == 1
            and all(type(v) in {int, float} for r in rows for v in r)
        )
    return True


@dataclass(frozen=True)
class CanvasItem:
    id: str
    kind: str = "object"
    label: str = ""
    value: object = None
    color: str = "#63D9B3"

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.strip():
            fail("Canvas item id must be nonempty")
        if self.kind not in {"car", "object", "flow", "variable", "collection", "vector", "matrix"}:
            fail(f"Unknown canvas kind {self.kind!r}")
        if not isinstance(self.label, str):
            fail("Canvas label must be text")
        from PIL import ImageColor

        ImageColor.getcolor(self.color, "RGBA")
        json_copy(self.value)
        if self.value is not None and not valid_canvas_value(self.kind, self.value):
            fail(f"Invalid static value for {self.kind}")


@dataclass(frozen=True)
class ValueBinding:
    key: str
    target: str
    property: str = "value"


@dataclass(frozen=True)
class EventBinding:
    checkpoint: str
    event: str
    target: str
    at: float
    duration: float = 0.6
    to: str | None = None
    cell: tuple[int, int] | None = None

    def __post_init__(self):
        if self.cell is not None:
            if len(self.cell) != 2 or any(type(n) is not int or n < 0 for n in self.cell):
                fail("cell must be a nonnegative (row, column) pair")
            object.__setattr__(self, "cell", tuple(self.cell))
        object.__setattr__(self, "at", finite(self.at, "event at", 0))
        object.__setattr__(self, "duration", finite(self.duration, "event duration", 0.001))


class PlaygroundScript:
    """All times use one authored clock, independent of execution wall time."""

    def __init__(self, checkpoints, *, duration, mode="concept", items=(), bindings=(), events=(), viewport=(720, 640)):
        self.checkpoints = tuple(checkpoints)
        self.duration = finite(duration, "duration", 0.001)
        self.mode = mode
        self.items, self.bindings, self.events = tuple(items), tuple(bindings), tuple(events)
        self.viewport = tuple(viewport)
        if mode not in {"web", "concept", "backend"}:
            fail("mode must be web, concept, or backend")
        if len(self.viewport) != 2 or any(type(v) is not int or v < 1 for v in self.viewport):
            fail("viewport must contain two positive integers")
        if not self.checkpoints or any(not isinstance(c, CodeCheckpoint) for c in self.checkpoints):
            fail("Supply at least one CodeCheckpoint")
        ids = [c.id for c in self.checkpoints]
        if len(set(ids)) != len(ids):
            fail("Checkpoint ids must be unique")
        previous = -1
        for c in self.checkpoints:
            if c.publish >= self.duration or c.edit_start < max(0, previous) or c.publish <= previous:
                fail("Checkpoints must be ordered, nonoverlapping, and publish before duration", checkpoint=c.id)
            if (mode == "web") != (c.runtime == "web"):
                fail("Web canvases require web checkpoints; other canvases require Python", checkpoint=c.id)
            previous = c.publish
        if any(not isinstance(i, CanvasItem) for i in self.items):
            fail("items must contain CanvasItem records")
        targets = {i.id for i in self.items}
        if len(targets) != len(self.items):
            fail("Canvas item ids must be unique")
        used = set()
        for b in self.bindings:
            if (
                not isinstance(b, ValueBinding)
                or b.target not in targets
                or b.property not in {"value", "label", "color"}
            ):
                fail("Invalid value binding target/property")
            if not isinstance(b.key, str) or not b.key or (b.target, b.property) in used:
                fail("Binding keys must be nonempty; target properties must be unique")
            used.add((b.target, b.property))
        for e in self.events:
            if not isinstance(e, EventBinding) or e.checkpoint not in ids or e.target not in targets:
                fail("Invalid event binding")
            if not isinstance(e.event, str) or not e.event or (e.to is not None and e.to not in targets):
                fail("Invalid event name or destination")
            if e.cell is not None and next(i.kind for i in self.items if i.id == e.target) not in {"vector", "matrix"}:
                fail("Cell emphasis requires a vector or matrix target")
            index = ids.index(e.checkpoint)
            end = self.checkpoints[index + 1].publish if index + 1 < len(ids) else self.duration
            if e.at < self.checkpoints[index].publish or e.at + e.duration > end:
                fail("Event must fit inside its checkpoint output window")
        # Freeze nested caller-owned data by retaining a canonical serialized record.
        self._record = json_copy(self._make_record())

    def _make_record(self):
        from dataclasses import asdict

        return {
            "checkpoints": [c.record() for c in self.checkpoints],
            "duration": self.duration,
            "mode": self.mode,
            "items": [asdict(i) for i in self.items],
            "bindings": [asdict(b) for b in self.bindings],
            "events": [asdict(e) for e in self.events],
            "viewport": self.viewport,
        }

    def __deepcopy__(self, memo):
        return self.from_record(self.record())

    def record(self):
        return json_copy(self._record)

    @classmethod
    def from_record(cls, data):
        from ..web.model import WebAction, WebScript

        checkpoints = []
        for raw in data["checkpoints"]:
            raw = dict(raw)
            if raw.get("web_script"):
                rec = raw["web_script"]
                script = WebScript(rec["duration"])
                for a in rec["actions"]:
                    action = WebAction(**a)
                    script._add(action.kind, action.selector, action.at, action.duration, action.value)
                script.track(*rec["selectors"])
                raw["web_script"] = script
            checkpoints.append(CodeCheckpoint(**raw))
        return cls(
            checkpoints,
            duration=data["duration"],
            mode=data["mode"],
            viewport=data["viewport"],
            items=[CanvasItem(**i) for i in data["items"]],
            bindings=[ValueBinding(**b) for b in data["bindings"]],
            events=[EventBinding(**e) for e in data["events"]],
        )
