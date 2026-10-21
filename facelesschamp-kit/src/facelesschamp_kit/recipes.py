"""Editable explanatory compositions. No agent or model service is required.

``apply_recipe`` returns semantic handles. Explicit events supplement the recipe's
entrances; the normal kit compiler remains authoritative for track conflicts.
"""

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from faceless_champ import Bounds, ColorScheme, FadeIn, Pulse

from facelesschamp_kit.charts import ChartReveal, ChartStyle, LineChart, PieChart
from facelesschamp_kit.diagrams import FlowEdge, FlowGraph, FlowNode, FlowScript

from .blocks import BlockBuild, CodingPlayground, FlowCanvas, MetricCard, TextPanel
from .diagnostics import KitError, fields, number


@dataclass(frozen=True)
class RecipeSpec:
    id: str
    purpose: str
    fields: tuple[str, ...]
    targets: tuple[str, ...]
    example: dict
    avoid: str


_SPECS = (
    RecipeSpec(
        "arch-design",
        "Demonstrate named geometry, assemblies, sections and technical dimensions",
        ("design",),
        ("model",),
        {"design": {"parts": [{"id": "body", "mesh": {"primitive": "cube"}}]}},
        "Use supplied models and fields; mark illustrative scientific values.",
    ),
    RecipeSpec(
        "process-flow",
        "Explain ordered steps through progressive disclosure",
        ("steps",),
        ("diagram",),
        {"steps": ["Collect", "Transform", "Deliver"]},
        "Use request-journey when movement is the point.",
    ),
    RecipeSpec(
        "request-journey",
        "Follow a request through connected services",
        ("steps",),
        ("diagram",),
        {"steps": ["Client", "Cache", "Database"]},
        "Do not imply measured latency without real data.",
    ),
    RecipeSpec(
        "before-after",
        "Contrast a specific change",
        ("before", "after"),
        ("before", "after"),
        {"before": "Every request repeats the work", "after": "Repeated requests reuse the result"},
        "Avoid unrelated comparisons or dense paragraphs.",
    ),
    RecipeSpec(
        "cause-effect",
        "Explain cause, mechanism, and consequence",
        ("cause", "mechanism", "effect"),
        ("diagram",),
        {"cause": "More requests", "mechanism": "Shared cache", "effect": "Less repeated work"},
        "Do not present correlation alone as causation.",
    ),
    RecipeSpec(
        "metric-context",
        "Give a number meaning through context",
        ("value", "label", "context"),
        ("metric", "value", "context"),
        {
            "value": 80,
            "label": "Requests served from cache",
            "context": "Illustrative: 80 out of 100 requests avoid repeated database work",
        },
        "Always state units and source or mark illustrative values.",
    ),
    RecipeSpec(
        "annotated-trend",
        "Explain a change in a time series",
        ("points", "label", "annotation"),
        ("chart", "annotation"),
        {
            "points": [[0, 2], [1, 3], [2, 6], [3, 7]],
            "label": "Illustrative throughput",
            "annotation": "Capacity increases after the change",
        },
        "Use ordered x values and explain units.",
    ),
    RecipeSpec(
        "part-whole",
        "Explain how parts contribute to one total",
        ("parts",),
        ("chart",),
        {"parts": {"Compute": 55, "Storage": 30, "Network": 15}},
        "Use nonnegative comparable values; keep the number of categories small.",
    ),
    RecipeSpec(
        "hierarchy",
        "Reveal an explicit parent-child hierarchy by level",
        ("nodes",),
        ("diagram",),
        {
            "nodes": [
                {"id": "root", "label": "System", "parent": None},
                {"id": "a", "label": "Application", "parent": "root"},
                {"id": "b", "label": "Storage", "parent": "root"},
                {"id": "c", "label": "Cache", "parent": "b"},
            ]
        },
        "Use explicit parents; cyclic graphs need a custom FlowCanvas.",
    ),
    RecipeSpec(
        "code-result",
        "Connect a prepared code checkpoint to its visual result",
        ("prepared",),
        ("editor", "canvas", "output"),
        {"prepared": ".playground-cache/prepared-example"},
        "Prepare complete checkpoints explicitly. Intermediate edits never execute.",
    ),
    RecipeSpec(
        "overview-detail",
        "Establish context, emphasize one part, return to the overview",
        ("steps", "focus", "detail"),
        ("diagram", "detail"),
        {
            "steps": ["Input", "Cache", "Output"],
            "focus": 1,
            "detail": "The cache retains results for repeated requests",
        },
        "Keep the same object identity and spatial context during focus.",
    ),
)
RECIPES = {spec.id: spec for spec in _SPECS}


def recipe_specs():
    """Return independent catalog records so callers cannot alter the registry."""
    return deepcopy(tuple(RECIPES.values()))


def _text(value, key):
    if not isinstance(value, str) or not value.strip():
        raise KitError("RECIPE_CONTENT", "Expected nonempty text", property=key)


def validate_recipe(recipe_id, content):
    """Validate content without composing, opening prepared assets, or executing code."""
    if recipe_id not in RECIPES:
        raise KitError("RECIPE_ID", "Unknown recipe; list recipes first", recipe=recipe_id)
    spec = RECIPES[recipe_id]
    fields(content, set(spec.fields), "recipe content")
    missing = set(spec.fields) - content.keys()
    if missing:
        raise KitError("RECIPE_CONTENT", "Missing content fields", recipe=recipe_id, fields=sorted(missing))
    if recipe_id == "arch-design":
        from faceless_champ.integrations.pyvista.model import ArchDataError

        from facelesschamp_kit.engineering.clip import validate_design

        try:
            validate_design(content["design"], registered_only=True)
        except ArchDataError as exc:
            raise KitError("ARCH_DATA", str(exc), path=exc.field) from exc
        return deepcopy(content)
    for key in set(spec.fields) - {"steps", "points", "parts", "nodes", "focus", "value", "prepared"}:
        _text(content[key], key)
    if "steps" in content:
        steps = content["steps"]
        if not isinstance(steps, (list, tuple)) or not 2 <= len(steps) <= 6:
            raise KitError("RECIPE_CONTENT", "Use 2–6 steps; split a denser explanation into scenes")
        for step in steps:
            _text(step, "steps")
    if "focus" in content:
        focus = content["focus"]
        if isinstance(focus, bool) or not isinstance(focus, int) or not 0 <= focus < len(content["steps"]):
            raise KitError("RECIPE_CONTENT", "focus must index an existing step")
    if "value" in content:
        number(content["value"], "value", minimum=-float("inf"))
    if "points" in content:
        points = content["points"]
        if not isinstance(points, (list, tuple)) or len(points) < 2:
            raise KitError("RECIPE_CONTENT", "A trend needs at least two points")
        previous = -float("inf")
        for point in points:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                raise KitError("RECIPE_CONTENT", "Each point must contain x and y")
            x, _ = [number(v, "point", minimum=-float("inf")) for v in point]
            if x <= previous:
                raise KitError("RECIPE_CONTENT", "Trend x values must increase")
            previous = x
    if "parts" in content:
        parts = content["parts"]
        if not isinstance(parts, dict) or not 2 <= len(parts) <= 6:
            raise KitError("RECIPE_CONTENT", "Use 2–6 named parts")
        for name, value in parts.items():
            _text(name, "parts")
            number(value, "part")
        if sum(parts.values()) <= 0:
            raise KitError("RECIPE_CONTENT", "Parts must have a positive total")
    if "nodes" in content:
        nodes = content["nodes"]
        if not isinstance(nodes, (list, tuple)) or not 2 <= len(nodes) <= 12:
            raise KitError("RECIPE_CONTENT", "Use 2–12 hierarchy nodes")
        parents = {}
        for node in nodes:
            fields(node, {"id", "label", "parent"}, "hierarchy node")
            for key in ("id", "label"):
                _text(node.get(key), key)
            if node["id"] in parents:
                raise KitError("RECIPE_CONTENT", "Duplicate hierarchy ID")
            parent = node.get("parent")
            if parent is not None:
                _text(parent, "parent")
            parents[node["id"]] = parent
        if sum(p is None for p in parents.values()) != 1:
            raise KitError("RECIPE_CONTENT", "Hierarchy needs one root")
        for node in parents:
            seen = set()
            current = node
            while current is not None:
                if current in seen or current not in parents:
                    raise KitError("RECIPE_CONTENT", "Hierarchy contains a cycle or unknown parent")
                seen.add(current)
                current = parents[current]
    if "prepared" in content and not isinstance(content["prepared"], (str, Path)):
        raise KitError("RECIPE_CONTENT", "prepared must be a prepared asset directory path")
    return deepcopy(content)


@dataclass(frozen=True)
class RecipeEvent:
    target: str
    at: float
    duration: float = 0.5
    action: str = "emphasize"
    value: float | None = None

    def __post_init__(self):
        _text(self.target, "target")
        number(self.at, "at")
        number(self.duration, "duration", positive=True)
        if self.action not in {"emphasize", "reveal", "value"}:
            raise KitError("RECIPE_EVENT", "Use emphasize, reveal, or value")
        if self.action == "value":
            number(self.value, "value", minimum=-float("inf"))


def _region(box, start, end):
    return Bounds(box.left, box.top + box.height * start, box.right, box.top + box.height * end)


@dataclass(frozen=True)
class _Region:
    block: object
    start: float
    end: float

    def compose(self, ctx, bounds):
        return self.block.compose(ctx, _region(bounds, self.start, self.end))


@dataclass(frozen=True)
class _RecipeMotionBounds:
    block: object
    enter: str | None

    def compose(self, ctx, bounds):
        # Flow motion translates content rather than changing its allocation.
        # Reserve its travel inside the default safe area before subdividing a
        # recipe. Explicit authored bounds remain the caller's responsibility.
        entrance = ctx.theme.default_enter if self.enter == "theme" else self.enter
        top = ctx.theme.motion_distance if ctx.theme.default_exit == "flow" else 0
        bottom = ctx.theme.motion_distance if entrance == "flow" else 0
        if bounds.height <= top + bottom:
            raise KitError("LAYOUT", "Recipe area is too short for the theme's flow motion")
        box = Bounds(bounds.left, bounds.top + top, bounds.right, bounds.bottom - bottom)
        return self.block.compose(ctx, box)


@dataclass(frozen=True)
class _ComparisonHalf:
    text: str
    title: str
    second: bool

    def compose(self, ctx, box):
        gap = ctx.theme.spacing
        if box.width >= box.height:
            middle = (box.left + box.right) / 2
            cell = (
                Bounds(middle + gap / 2, box.top, box.right, box.bottom)
                if self.second
                else Bounds(box.left, box.top, middle - gap / 2, box.bottom)
            )
        else:
            middle = (box.top + box.bottom) / 2
            cell = (
                Bounds(box.left, middle + gap / 2, box.right, box.bottom)
                if self.second
                else Bounds(box.left, box.top, box.right, middle - gap / 2)
            )
        return TextPanel(self.text, self.title).compose(ctx, cell)


@dataclass(frozen=True)
class _Diagram:
    recipe: str
    content: dict
    duration: float

    def compose(self, ctx, box):
        duration = self.duration
        node_size = (min(380, box.width * 0.65), 170)
        if self.recipe == "hierarchy":
            raw = self.content["nodes"]
            nodes = tuple(FlowNode(n["id"], n["label"], size=node_size) for n in raw)
            used_ids = {node.id for node in nodes}
            edges = []
            for i, node in enumerate(raw):
                if node.get("parent") is None:
                    continue
                edge_id = f"edge-{i}"
                while edge_id in used_ids:
                    edge_id += "-edge"
                used_ids.add(edge_id)
                edges.append(FlowEdge(edge_id, node["parent"], node["id"]))
            edges = tuple(edges)
            parents = {n["id"]: n.get("parent") for n in raw}

            def depth(name):
                result = 0
                while parents[name] is not None:
                    result += 1
                    name = parents[name]
                return result

            order = sorted(parents, key=depth)
        else:
            labels = self.content.get("steps") or [self.content[k] for k in ("cause", "mechanism", "effect")]
            if box.width >= box.height:
                node_size = (min(380, box.width * 0.72 / len(labels)), 170)
            nodes = tuple(FlowNode(f"n{i}", label, size=node_size) for i, label in enumerate(labels))
            edges = tuple(FlowEdge(f"edge-{i}", nodes[i].id, nodes[i + 1].id) for i in range(len(nodes) - 1))
            order = [n.id for n in nodes]
        graph = FlowGraph(nodes, edges, direction="horizontal" if box.width >= box.height else "vertical")
        script = FlowScript()
        step = duration * 0.30 / len(nodes)
        if self.recipe == "hierarchy":
            levels = max(depth(name) for name in order) + 1
            for name in order:
                script.draw(name, at=depth(name) * duration * 0.35 / levels, duration=duration * 0.07)
            for edge in edges:
                script.draw(edge.id, at=depth(edge.target) * duration * 0.35 / levels, duration=duration * 0.07)
        else:
            script.draw(order, at=0, duration=duration * 0.07, stagger=step)
            for i, edge in enumerate(edges):
                script.draw(edge.id, at=(i + 1) * step, duration=duration * 0.07)
        if self.recipe == "request-journey":
            for i, edge in enumerate(edges):
                script.signal(
                    edge.id,
                    at=duration * 0.4 + i * duration * 0.4 / len(edges),
                    duration=duration * 0.35 / len(edges),
                    marker="packet",
                )
        elif self.recipe == "overview-detail":
            focus = nodes[self.content["focus"]].id
            script.highlight(focus, at=duration * 0.35, duration=duration * 0.38, dim=0.25)
        else:
            script.highlight(order[-1], at=duration * 0.62, duration=duration * 0.2)
        return FlowCanvas(graph, script, viewport=(box.width, box.height)).compose(ctx, box)


@dataclass(frozen=True)
class _Chart:
    content: dict
    pie: bool = False

    def compose(self, ctx, box):
        from faceless_champ import with_alpha

        scheme = ColorScheme(
            background=ctx.theme.background,
            surface=ctx.theme.surface,
            text=ctx.theme.foreground,
            primary=ctx.theme.accent,
            muted=ctx.theme.muted,
            axis=ctx.theme.muted,
            grid=with_alpha(ctx.theme.muted, 0.25),
        )
        style = ChartStyle(
            scheme=scheme,
            font_size=max(ctx.theme.minimum_font_size, ctx.theme.body_size * 0.8),
            title_size=ctx.theme.body_size,
            font=ctx.theme.font,
            legend=True,
        )
        kwargs = {"width": box.width, "height": box.height, "style": style, "position": box.center}
        chart = (
            PieChart(
                tuple(
                    f"{name} {value / sum(self.content['parts'].values()):.0%}"
                    for name, value in self.content["parts"].items()
                ),
                tuple(self.content["parts"].values()),
                hole=0.55,
                **kwargs,
            )
            if self.pie
            else LineChart({self.content["label"]: self.content["points"]}, **kwargs)
        )
        return BlockBuild(chart, {"chart": chart})


@dataclass(frozen=True)
class _Prepared:
    path: str
    duration: float

    def compose(self, ctx, box):
        from facelesschamp_kit.playground import PreparedPlayground

        prepared = PreparedPlayground(ctx.root / self.path)
        if prepared.script.duration > self.duration + 1e-9:
            raise KitError("MOTION_WINDOW", "Prepared code script exceeds the recipe segment")
        side = box.width >= box.height
        editor_width = (box.width - ctx.theme.spacing) / 2 if side else box.width
        longest = max(
            (
                len(line)
                for cp in prepared.script.checkpoints
                for source in cp.files.values()
                for line in source.splitlines()
            ),
            default=0,
        )
        font_size = max(ctx.theme.minimum_font_size, min(36, (editor_width - 180) / max(1, longest * 0.65)))
        return CodingPlayground(
            prepared,
            layout="side" if side else "stacked",
            font_size=font_size,
            theme="paper" if ctx.theme.name in {"light", "whiteboard"} else ctx.theme.code_theme,
        ).compose(ctx, box)


def apply_recipe(segment, recipe_id, content, *, bounds=None, events=(), id=None):
    """Add an explanatory composition and return semantic ``Handle`` targets.

    Events use segment-local seconds. Use distinct ``id`` values when applying
    the same recipe more than once in one segment. Content is copied immediately.
    Default content areas reserve space for theme flow motion. Explicit bounds
    are used as supplied, including any required animation clearance.
    """
    content = validate_recipe(recipe_id, content)
    events = tuple(e if isinstance(e, RecipeEvent) else RecipeEvent(**e) for e in events)
    spec = RECIPES[recipe_id]
    for event in events:
        if event.target not in spec.targets or event.at + event.duration > segment.duration:
            raise KitError("RECIPE_EVENT", "Event target or time is outside this recipe", target=event.target)
        if event.action == "value" and event.target != "value":
            raise KitError("RECIPE_EVENT", "Value events require the value target")
    prefix = id or recipe_id
    duration = segment.duration
    handles = {}

    def add(name, block, *, at=0, life=None, enter="fade"):
        if bounds is None:
            block = _RecipeMotionBounds(block, enter)
        handle = segment.add(
            block,
            id=f"{prefix}-{name}",
            bounds=bounds,
            at=at,
            duration=life,
            enter=enter,
            enter_duration=min(0.5, (life or duration - at) / 3),
        )
        handles[name] = handle
        return handle

    if recipe_id == "arch-design":
        from .blocks import ArchCanvas

        add("model", ArchCanvas(content["design"]), enter=None)
    elif recipe_id in {"process-flow", "request-journey", "cause-effect", "hierarchy"}:
        add("diagram", _Diagram(recipe_id, content, duration), enter=None)
    elif recipe_id == "overview-detail":
        add("diagram", _Region(_Diagram(recipe_id, content, duration), 0, 0.68), enter=None)
        add("detail", _Region(TextPanel(content["detail"]), 0.72, 1), at=duration * 0.35, life=duration * 0.4)
    elif recipe_id == "before-after":
        add("before", _ComparisonHalf(content["before"], "Before", False))
        add("after", _ComparisonHalf(content["after"], "After", True), at=duration * 0.3)
    elif recipe_id == "metric-context":
        metric = add("metric", _Region(MetricCard(content["value"], content["label"]), 0, 0.58))
        handles["value"] = metric["value"]
        add("context", _Region(TextPanel(content["context"]), 0.63, 1), at=duration * 0.3)
    elif recipe_id in {"annotated-trend", "part-whole"}:
        block = _Chart(content, recipe_id == "part-whole")
        chart = add("chart", _Region(block, 0, 0.7) if recipe_id == "annotated-trend" else block)
        segment.play(chart["chart"], lambda c: ChartReveal(c), at=0, duration=duration * 0.5)
        if recipe_id == "annotated-trend":
            add("annotation", _Region(TextPanel(content["annotation"]), 0.74, 1), at=duration * 0.5)
    else:
        handle = add("playground", _Prepared(str(content["prepared"]), duration))
        handles = {name: handle[name] for name in spec.targets}
    for event in events:
        if event.action == "emphasize":
            factory = lambda c: Pulse(c, factor=1.04)
        elif event.action == "reveal":
            factory = lambda c: FadeIn(c)
        else:
            factory = lambda c, value=event.value: c.animate.value_to(value)
        segment.play(handles[event.target], factory, at=event.at, duration=event.duration)
    return handles


__all__ = ["RecipeEvent", "RecipeSpec", "apply_recipe", "recipe_specs", "validate_recipe"]
