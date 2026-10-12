"""Validated, serializable diagram recipes. Coordinates are viewport design pixels."""

import json
import math
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from PIL import ImageColor

SYMBOLS = (
    "rectangle",
    "rounded_rectangle",
    "circle",
    "diamond",
    "document",
    "service",
    "database",
    "queue",
    "server",
    "client",
    "router",
    "resistor",
    "capacitor",
    "battery",
    "ground",
    "switch",
    "diode",
    "led",
    "and",
    "or",
    "not",
    "image",
    "junction",
)


class FlowDataError(ValueError):
    def __init__(self, path, message):
        self.path = path
        super().__init__(f"{path}: {message}")


def number(value, path, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise FlowDataError(path, "expected a finite number")
    if minimum is not None and value < minimum:
        raise FlowDataError(path, f"must be >= {minimum}")
    return float(value)


def point(value, path):
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise FlowDataError(path, "expected two coordinates")
    return tuple(number(x, path) for x in value)


def text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise FlowDataError(path, "expected nonempty text")
    return value


def choice(value, values, path):
    if not isinstance(value, str) or value not in values:
        raise FlowDataError(path, f"expected one of {', '.join(values)}")


def color(value, path):
    try:
        if not isinstance(value, str):
            raise TypeError
        ImageColor.getcolor(value, "RGBA")
    except (ValueError, TypeError):
        raise FlowDataError(path, "expected a color string") from None


def object_fields(data, allowed, path, required=()):
    if not isinstance(data, dict):
        raise FlowDataError(path, "expected an object")
    for key in data:
        if key not in allowed:
            raise FlowDataError(f"{path}.{key}", "unknown field")
    for key in required:
        if key not in data:
            raise FlowDataError(f"{path}.{key}", "required field")


def construct(cls, data, path, required=()):
    object_fields(data, {f.name for f in fields(cls)}, path, required)
    try:
        return cls(**data)
    except (ValueError, TypeError) as exc:
        raise FlowDataError(path, str(exc)) from exc


@dataclass(frozen=True)
class FlowPort:
    id: str
    side: str = "right"
    offset: float = 0.5

    def __post_init__(self):
        text(self.id, "port.id")
        choice(self.side, ("left", "right", "top", "bottom", "center"), self.id)
        number(self.offset, self.id, 0)
        if self.offset > 1:
            raise FlowDataError(self.id, "port offset must be <= 1")


@dataclass(frozen=True)
class FlowNode:
    id: str
    label: str = ""
    symbol: str = "rounded_rectangle"
    position: tuple | None = None
    size: tuple = (160, 90)
    ports: tuple = ()
    image: str | None = None
    rotation: float = 0
    scale: float = 1

    def __post_init__(self):
        text(self.id, "node.id")
        if not isinstance(self.label, str):
            raise FlowDataError(self.id, "label must be text")
        choice(self.symbol, SYMBOLS, self.id)
        if self.position is not None:
            object.__setattr__(self, "position", point(self.position, self.id))
        object.__setattr__(self, "size", point(self.size, self.id))
        if min(self.size) <= 0:
            raise FlowDataError(self.id, "size must be positive")
        ports = tuple(self.ports)
        if any(not isinstance(p, FlowPort) for p in ports) or len({p.id for p in ports}) != len(ports):
            raise FlowDataError(self.id, "ports must have unique IDs and be FlowPort objects")
        object.__setattr__(self, "ports", ports)
        number(self.rotation, self.id)
        number(self.scale, self.id, 0.001)
        if self.symbol == "image" and self.image is None:
            raise FlowDataError(self.id, "image symbol requires a local image path")
        if self.image is not None:
            if not isinstance(self.image, (str, Path)):
                raise FlowDataError(self.id, "image must be a local path")
            text(str(self.image), self.id)
            object.__setattr__(self, "image", str(self.image))


@dataclass(frozen=True)
class FlowEdge:
    id: str
    source: str
    target: str
    source_port: str | None = None
    target_port: str | None = None
    label: str = ""
    route: str = "orthogonal"
    waypoints: tuple = ()
    dashed: bool = False
    arrows: str = "end"

    def __post_init__(self):
        for name in ("id", "source", "target"):
            text(getattr(self, name), f"edge.{name}")
        for name in ("source_port", "target_port"):
            if getattr(self, name) is not None:
                text(getattr(self, name), f"{self.id}.{name}")
        if not isinstance(self.label, str) or not isinstance(self.dashed, bool):
            raise FlowDataError(self.id, "label must be text and dashed must be boolean")
        choice(self.route, ("straight", "orthogonal", "bezier"), self.id)
        choice(self.arrows, ("none", "start", "end", "both"), self.id)
        object.__setattr__(self, "waypoints", tuple(point(p, self.id) for p in self.waypoints))
        if self.route == "bezier" and len(self.waypoints) not in (0, 2):
            raise FlowDataError(self.id, "Bezier routes need zero or two control points")


@dataclass(frozen=True)
class FlowTheme:
    foreground: str = "#EDF3FF"
    surface: str = "#172337"
    accent: str = "#55BDEB"
    background: str = "#0B1220"
    font: str | None = None
    font_size: float = 20
    minimum_font_size: float = 12
    stroke_width: float = 2.5
    sketch: bool = False
    seed: int = 0
    stroke: str | None = None

    def __post_init__(self):
        for name in ("foreground", "surface", "accent", "background"):
            color(getattr(self, name), f"theme.{name}")
        if self.stroke is not None:
            color(self.stroke, "theme.stroke")
        for name in ("font_size", "minimum_font_size", "stroke_width"):
            number(getattr(self, name), f"theme.{name}", 0.1)
        if self.font is not None:
            text(self.font, "theme.font")
        if self.minimum_font_size > self.font_size:
            raise FlowDataError("theme.minimum_font_size", "exceeds font_size")
        if not isinstance(self.sketch, bool) or isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise FlowDataError("theme", "sketch must be boolean and seed must be integer")


@dataclass(frozen=True)
class FlowGraph:
    nodes: tuple
    edges: tuple = ()
    layout: str = "layered"
    direction: str = "horizontal"

    def __post_init__(self):
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "edges", tuple(self.edges))
        if not self.nodes or any(not isinstance(n, FlowNode) for n in self.nodes):
            raise FlowDataError("nodes", "supply at least one FlowNode")
        if any(not isinstance(e, FlowEdge) for e in self.edges):
            raise FlowDataError("edges", "expected FlowEdge objects")
        ids = [x.id for x in (*self.nodes, *self.edges)]
        if len(ids) != len(set(ids)):
            raise FlowDataError("graph", "node and edge IDs must be unique")
        choice(self.layout, ("manual", "layered", "grid", "radial"), "layout")
        choice(self.direction, ("horizontal", "vertical"), "direction")
        nodes = {n.id: n for n in self.nodes}
        for edge in self.edges:
            for end in ("source", "target"):
                node = nodes.get(getattr(edge, end))
                if node is None:
                    raise FlowDataError(edge.id, f"unknown {end} node")
                port = getattr(edge, end + "_port")
                if port is not None and port not in {p.id for p in node.ports}:
                    raise FlowDataError(edge.id, f"unknown {end} port {port!r}")

    def to_dict(self):
        return json.loads(json.dumps(asdict(self)))

    @classmethod
    def from_dict(cls, data, *, base_path=None):
        object_fields(data, ("nodes", "edges", "layout", "direction"), "graph", ("nodes",))
        for key in ("nodes", "edges"):
            if not isinstance(data.get(key, []), (list, tuple)):
                raise FlowDataError(f"graph.{key}", "expected an array")
        nodes = []
        for i, raw in enumerate(data["nodes"]):
            path = f"graph.nodes[{i}]"
            object_fields(raw, {f.name for f in fields(FlowNode)}, path, ("id",))
            node = dict(raw)
            if not isinstance(node.get("ports", []), (list, tuple)):
                raise FlowDataError(f"{path}.ports", "expected an array")
            node["ports"] = tuple(
                construct(FlowPort, p, f"{path}.ports[{j}]", ("id",)) for j, p in enumerate(node.get("ports", ()))
            )
            if node.get("image") is not None and base_path is not None:
                node["image"] = str((Path(base_path) / node["image"]).resolve())
            nodes.append(construct(FlowNode, node, path, ("id",)))
        edges = tuple(
            construct(FlowEdge, e, f"graph.edges[{i}]", ("id", "source", "target"))
            for i, e in enumerate(data.get("edges", ()))
        )
        return cls(tuple(nodes), edges, data.get("layout", "layered"), data.get("direction", "horizontal"))

    @classmethod
    def from_json(cls, path):
        path = Path(path)
        return cls.from_dict(json.loads(path.read_text()), base_path=path.parent)
