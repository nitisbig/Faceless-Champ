"""A connected, silent 60-second tour using public Kit/core components.

Only ``build(ctx)`` with ``ctx.preparing`` runs Python checkpoints or a browser.
Normal builds seek immutable prepared results. Major scenes overlap by .6s.
"""

import json
import os
import tempfile
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path

from facelesschamp_kit import Video
from facelesschamp_kit.blocks import (
    ArchCanvas,
    BlockBuild,
    ChessBoard,
    CodingPlayground,
    FlowCanvas,
    OSWalkthrough,
    WebWalkthrough,
    WhiteboardDrawing,
    WhiteboardPath,
)

from faceless_champ import (
    Arrow,
    Axis,
    BarChart,
    Bounds,
    CanvasItem,
    ChartReveal,
    ChartStyle,
    Checkmark,
    ChessScript,
    ChessTheme,
    CodeCheckpoint,
    ColorScheme,
    Draw,
    EarthMap,
    Equation,
    EventBinding,
    FlowEdge,
    FlowGraph,
    FlowNode,
    FlowScript,
    FlowTheme,
    Gauge,
    Group,
    Image,
    ImageSlot,
    LineChart,
    Number,
    OutlineMap,
    PieChart,
    PlaygroundScript,
    Polyline,
    ProgressBar,
    ProgressRing,
    Rectangle,
    RectangleMask,
    SatelliteMap,
    ShadowStyle,
    ValueBinding,
    Wipe,
    Write,
    card_content_bounds,
    card_surface,
    fit_text,
)
from faceless_champ.os_ui import File, Folder, MacOSPreset, OSScript, VirtualFileSystem
from faceless_champ.web import (
    HtmlPage,
    WebCapture,
    WebError,
    WebFocus,
    WebHighlight,
    WebScript,
    capture_html,
)

PROJECT = Path(__file__).resolve().parents[1]
ORANGE = "#FF5A20"
INK = "#111111"
MUTED = "#737373"
PEACH = "#FFF0E8"
DARK = "#14161A"
SHADOW = ShadowStyle()
TOTAL_DURATION = 60.0
OVERLAP = 0.6
NOMINAL_SCENES = (
    ("plan", 0, 6, "From files to a finished dashboard."),
    ("os", 6, 14, "Organize the workspace."),
    ("code", 14, 24, "Turn data into a useful result."),
    ("html", 24, 33, "Build an interface people can use."),
    ("insights", 33, 43, "Make the numbers easy to see."),
    ("arch", 43, 52, "Explore the structure underneath."),
    ("finish", 52, 60, "Every detail has a place."),
)
FEATURES = (
    "assets",
    "text",
    "shapes",
    "groups",
    "masks",
    "motion",
    "oschamp",
    "codingchamp",
    "prepared-python",
    "console",
    "html-capture",
    "html-focus",
    "line-chart",
    "bar-chart",
    "donut-chart",
    "maps",
    "flags",
    "metrics",
    "indicators",
    "archchamp",
    "chesschamp",
    "equations",
    "whiteboard",
    "flowchamp",
)
STORYBOARD_TIMES = (3, 6, 9.4, 13.8, 19, 24, 28.7, 33, 37.5, 40.5, 43, 47.5, 50.5, 52, 55.5, 58.2)


def scene_windows():
    return [
        {
            "id": name,
            "nominal_start": start,
            "nominal_end": end,
            "start": max(0, start - OVERLAP / 2),
            "end": min(TOTAL_DURATION, end + OVERLAP / 2),
            "label": label,
        }
        for name, start, end, label in NOMINAL_SCENES
    ]


def label(ctx, value, box, *, size=34, color=INK, weight=400, align="left"):
    return fit_text(
        value,
        box,
        font=ctx.theme.font,
        font_weight=weight,
        font_size=size,
        min_font_size=min(24, size),
        color=color,
        align=align,
        spacing=4,
    )


def put(segment, factory, id, box, *, at=0, duration=None, z_index=0):
    return segment.add_core(factory, id=id, bounds=box, at=at, duration=duration, z_index=z_index)


def text(segment, value, box, id, *, size=34, color=INK, weight=400, at=0, duration=None, align="left"):
    return put(
        segment,
        lambda ctx, b: label(ctx, value, b, size=size, color=color, weight=weight, align=align),
        id,
        box,
        at=at,
        duration=duration,
        z_index=10,
    )


def surface(segment, box, id, *, fill="#FFFFFF", radius=44):
    return put(segment, lambda ctx, b: card_surface(b, fill=fill, radius=radius, shadow=SHADOW), id, box)


@dataclass(frozen=True)
class Framed:
    """Compose a real public block inside an allocated rounded surface."""

    block: object
    fill: str = "#FFFFFF"
    padding: float = 20

    def compose(self, ctx, bounds):
        interior = card_content_bounds(bounds, shadow=SHADOW, padding=self.padding)
        built = self.block.compose(ctx, interior)
        root = Group(card_surface(bounds, fill=self.fill, radius=44, shadow=SHADOW), built.root)
        return BlockBuild(root, built.children)


def icon_group(kind, x, y, size=116):
    """Original geometric icons, assembled from ordinary animated shapes."""
    options = {"fill": None, "stroke": INK, "stroke_width": 7}
    if kind == "files":
        return Group(
            Rectangle(width=size * 0.72, height=size * 0.9, corner_radius=12, position=(x, y), **options),
            Polyline([(x - 23, y - 12), (x + 23, y - 12)], stroke=INK, stroke_width=7),
            Polyline([(x - 23, y + 13), (x + 10, y + 13)], stroke=ORANGE, stroke_width=7),
            mask=RectangleMask(size * 1.4, size * 1.4),
        )
    if kind == "code":
        return Group(
            Polyline([(x - 18, y - 31), (x - 48, y), (x - 18, y + 31)], stroke=INK, stroke_width=7),
            Polyline([(x + 18, y - 31), (x + 48, y), (x + 18, y + 31)], stroke=INK, stroke_width=7),
            Polyline([(x + 9, y - 43), (x - 9, y + 43)], stroke=ORANGE, stroke_width=7),
            mask=RectangleMask(size * 1.4, size * 1.4),
        )
    return Group(
        Rectangle(width=size, height=size * 0.82, corner_radius=14, position=(x, y), **options),
        Polyline([(x - 35, y + 19), (x - 10, y - 2), (x + 9, y + 7), (x + 38, y - 27)], stroke=ORANGE, stroke_width=7),
        mask=RectangleMask(size * 1.4, size * 1.4),
    )


def build_plan(segment, ctx, prepared, capture):
    cards = (Bounds(84, 275, 659, 925), Bounds(672, 275, 1247, 925), Bounds(1260, 275, 1835, 925))
    for index, (box, kind, name, detail) in enumerate(
        zip(
            cards,
            ("files", "code", "dashboard"),
            ("Assets", "Build", "Dashboard"),
            ("Images · fonts · geometry", "Code · motion · meaning", "One clear view"),
        )
    ):
        surface(segment, box, f"tile-{index}")
        inside = card_content_bounds(box, shadow=SHADOW, padding=28)
        icon = put(
            segment,
            lambda c, b, k=kind: icon_group(k, *b.center),
            f"icon-{index}",
            Bounds(inside.left, inside.top + 50, inside.right, inside.top + 210),
            z_index=4,
        )
        segment.play(icon, lambda c: Wipe(c), at=0, duration=0.9 + index * 0.12)
        text(
            segment,
            name,
            Bounds(inside.left, inside.top + 260, inside.right, inside.top + 322),
            f"tile-label-{index}",
            size=48,
            weight=700,
            align="center",
        )
        text(
            segment,
            detail,
            Bounds(inside.left, inside.top + 340, inside.right, inside.top + 410),
            f"tile-detail-{index}",
            size=26,
            color=MUTED,
            align="center",
        )
        if index == 0:
            put(
                segment,
                lambda c, b: ImageSlot(
                    c.assets.image("brand-mark"), width=64, height=64, position=b.center, mode="required"
                ),
                "named-image",
                Bounds(inside.left + 36, inside.bottom - 70, inside.left + 100, inside.bottom - 6),
                at=0.7,
                z_index=5,
            )
            put(
                segment,
                lambda c, b: Image(c.assets.image("knight"), width=52, height=64, position=b.center),
                "packaged-image",
                Bounds(inside.right - 100, inside.bottom - 70, inside.right - 36, inside.bottom - 6),
                at=0.9,
                z_index=5,
            )
        if index == 2:
            handle = put(
                segment,
                lambda c, b: ProgressBar(
                    width=b.width, height=16, color=ORANGE, track_color="#F0EDE8", position=b.center
                ),
                "launch-progress",
                Bounds(inside.left + 25, inside.bottom - 54, inside.right - 25, inside.bottom - 24),
                at=0.5,
                z_index=5,
            )
            segment.play(handle, lambda c: c.animate.progress_to(1), at=1.1, duration=3.5)
    text(segment, "Files", Bounds(570, 912, 770, 960), "flow-word-1", size=25, color=MUTED, align="center")
    text(segment, "Build", Bounds(860, 912, 1060, 960), "flow-word-2", size=25, color=MUTED, align="center")
    text(segment, "Publish", Bounds(1150, 912, 1350, 960), "flow-word-3", size=25, color=MUTED, align="center")
    for index, (start, end) in enumerate(((775, 855), (1065, 1145))):
        connector = put(
            segment,
            lambda c, b, a=start, z=end: Arrow((a, 936), (z, 936), stroke=ORANGE, stroke_width=3, tip_size=11),
            f"plan-connector-{index}",
            Bounds(start - 20, 916, end + 20, 956),
            at=0.7 + index * 0.2,
            z_index=6,
        )
        segment.play(connector, lambda c: Draw(c), at=0.7 + index * 0.2, duration=0.9)


def os_story():
    filesystem = VirtualFileSystem(
        Folder(
            "home",
            "Workspace",
            (
                Folder(
                    "project",
                    "Dashboard project",
                    (
                        File("data", "sessions.csv", "day,sessions\nMon,18\nTue,24\nWed,31\nThu,48"),
                        File("notes", "Notes.txt", "A small project.\nA clear dashboard.\nBuilt with Faceless Champ."),
                        File("mark", "Brand mark.png", "Original artwork in the asset registry."),
                        Folder("assets", "Assets"),
                    ),
                ),
                Folder("exports", "Exports"),
            ),
        )
    )
    script = (
        OSScript()
        .open_folder("project", at=0.75, duration=0.8)
        .select("data", at=1.7, duration=0.5)
        .rename("data", "weekly-sessions.csv", at=2.3, duration=0.9)
        .preview("notes", at=3.4, duration=0.7)
        .window("preview", "close", at=4.5, duration=0.5)
        .drag("mark", "assets", at=5.2, duration=1)
        .set_view("list", at=6.5, duration=0.6)
        .open_settings("appearance", at=7.2, duration=0.7)
    )
    return filesystem, script


def build_os(segment, ctx, prepared, capture):
    filesystem, script = os_story()
    block = OSWalkthrough(
        filesystem,
        script,
        preset=MacOSPreset(
            appearance="dark",
            wallpaper=DARK,
            accent=ORANGE,
            font=ctx.theme.font,
            clock="Project workspace",
            cursor_size=1.15,
        ),
        viewport=(1440, 760),
    )
    segment.add(Framed(block, fill=DARK, padding=10), id="os-workspace", bounds=Bounds(96, 205, 1824, 956))
    text(
        segment,
        "A real authored filesystem. Repeatable actions.",
        Bounds(420, 936, 1500, 982),
        "os-detail",
        size=27,
        color=MUTED,
        align="center",
    )


SOURCE = """import faceless_champ.playground.runtime as pg

sessions = [18, 24, 31, LAST]
total = sum(sessions)
pg.emit("sessions", sessions)
pg.emit("total", total)
pg.event("updated")
print("Sessions:", total)
"""


def code_script():
    return PlaygroundScript(
        [
            CodeCheckpoint(
                "draft", {"dashboard.py": SOURCE.replace("LAST", "36")}, "dashboard.py", "dashboard.py", 0.4, 1.8, 2
            ),
            CodeCheckpoint(
                "update", {"dashboard.py": SOURCE.replace("LAST", "48")}, "dashboard.py", "dashboard.py", 4.4, 5.8, 6
            ),
        ],
        duration=9.6,
        mode="backend",
        items=[
            CanvasItem("input", "flow", "Data", color=ORANGE),
            CanvasItem("compute", "flow", "Compute", color=ORANGE),
            CanvasItem("sessions", "collection", "Sessions", color=ORANGE),
            CanvasItem("total", "variable", "Total", color=ORANGE),
        ],
        bindings=[ValueBinding("sessions", "sessions"), ValueBinding("total", "total")],
        events=[
            EventBinding("draft", "updated", "input", 2.2, 1, "compute"),
            EventBinding("update", "updated", "compute", 6.2, 1, "total"),
        ],
    )


def build_code(segment, ctx, prepared, capture):
    segment.add(
        Framed(
            CodingPlayground(prepared, code_ratio=0.53, font_size=24, theme="clean-flow", output=True),
            fill=DARK,
            padding=16,
        ),
        id="coding-playground",
        bounds=Bounds(96, 210, 1824, 960),
    )
    text(
        segment,
        "Edit → run a checkpoint → replay the result",
        Bounds(400, 940, 1520, 990),
        "code-detail",
        size=27,
        color=MUTED,
        align="center",
    )


def browser_script():
    page = HtmlPage(
        PROJECT / "assets/dashboard/index.html",
        viewport=(1440, 760),
        asset_root=PROJECT / "assets/dashboard",
        ready=("#metric", "#publish", "#nepal"),
    )
    script = (
        WebScript(9.3)
        .track("#metric", ".trend", "#publish", "#nepal")
        .move("#nepal", at=0.8, duration=0.6)
        .click("#nepal", at=1.5)
        .move("#all", at=3.6, duration=0.5)
        .click("#all", at=4.2)
        .move("#publish", at=5.5, duration=0.6)
        .click("#publish", at=6.2)
    )
    return page, script


def web_fingerprint():
    page, script = browser_script()
    files = {}
    for p in sorted(page.asset_root.iterdir()):
        if p.is_file():
            files[p.name] = sha256(p.read_bytes()).hexdigest()
    return sha256(
        json.dumps(
            {"files": files, "script": script.record(), "fps": 30, "viewport": page.viewport}, sort_keys=True
        ).encode()
    ).hexdigest()


def prepared_web(ctx):
    reference = ctx.root / ".fc-kit/web/reference.json"
    key = web_fingerprint()
    if ctx.preparing:
        page, script = browser_script()
        print("Preparing local HTML capture (installed Chromium)…", flush=True)

        def capture_progress(done, total):
            if done == total or done % 30 == 0:
                print(f"  HTML {done}/{total} frames", flush=True)

        capture = capture_html(
            page,
            script,
            fps=30,
            cache_dir=ctx.root / ".fc-kit/web/captures",
            timeout=30,
            progress=capture_progress,
        )
        reference.parent.mkdir(parents=True, exist_ok=True)
        record = {"fingerprint": key, "directory": str(capture.directory.relative_to(reference.parent))}
        descriptor, temporary = tempfile.mkstemp(prefix=".reference-", dir=reference.parent)
        try:
            with os.fdopen(descriptor, "w") as stream:
                json.dump(record, stream)
            os.replace(temporary, reference)
        finally:
            Path(temporary).unlink(missing_ok=True)
    else:
        if not reference.is_file():
            raise WebError("WEB_UNPREPARED: run python3 render.py --prepare")
        record = json.loads(reference.read_text())
        if record["fingerprint"] != key:
            raise WebError("WEB_STALE: source changed; run python3 render.py --prepare")
        directory = (reference.parent / record["directory"]).resolve()
        if not directory.is_relative_to(reference.parent.resolve()):
            raise WebError("Prepared HTML reference escapes the project cache")
        capture = WebCapture(directory)
    if len(capture.frames) != capture.count:
        raise WebError("WEB_INCOMPLETE: prepare the complete nine-second HTML clip")
    ctx.prepared_assets.append(
        {
            "kind": "html-capture",
            "status": "prepared",
            "fingerprint": key,
            "path": str(capture.directory),
            "fps": capture.fps,
        }
    )
    return capture


def build_html(segment, ctx, prepared, capture):
    walkthrough = WebWalkthrough(
        capture,
        title="dashboard.local / project",
        cursor=True,
        highlights=(WebHighlight("#nepal", 0.9, 3.2, ORANGE), WebHighlight("#publish", 5.7, 7.6, ORANGE)),
        focuses=(WebFocus("#metric", 2, 3.6, zoom=1.35, transition=0.5),),
    )
    segment.add(Framed(walkthrough, padding=10), id="prepared-web", bounds=Bounds(94, 205, 1826, 960))
    text(
        segment,
        "Local HTML + CSS + JavaScript. Captured once.",
        Bounds(420, 940, 1500, 990),
        "html-detail",
        size=27,
        color=MUTED,
        align="center",
    )


def chart_style(ctx):
    return ChartStyle(
        scheme=replace(ColorScheme.named("clean-flow"), surface="#00000000"),
        font=ctx.theme.font,
        title_font=ctx.theme.font,
        title_font_weight=700,
        font_size=22,
        title_size=29,
        line_width=4,
        legend=False,
    )


def chart_factory(kind, sessions):
    def factory(ctx, box):
        inside = card_content_bounds(box, shadow=SHADOW, padding=18)
        options = {"width": inside.width, "height": inside.height, "position": inside.center, "style": chart_style(ctx)}
        if kind == "line":
            chart = LineChart(
                {"Sessions": list(enumerate(sessions))},
                title="Weekly sessions",
                x_axis=Axis(limits=(0, 3), ticks=(0, 1, 2, 3)),
                y_axis=Axis(limits=(0, 60), ticks=(0, 20, 40, 60)),
                **options,
            )
        elif kind == "bar":
            chart = BarChart(
                ["M", "T", "W", "T" + "h"],
                {"Sessions": sessions},
                title="Daily activity",
                y_axis=Axis(limits=(0, 60), ticks=(0, 20, 40, 60)),
                **options,
            )
        else:
            chart = PieChart(["Mon", "Tue", "Wed", "Thu"], sessions, hole=0.7, title="Mix", **options)
        return BlockBuild(Group(card_surface(box, radius=44, shadow=SHADOW), chart), {"chart": chart})

    return factory


def build_insights(segment, ctx, prepared, capture):
    # This is the exact emitted checkpoint data, loaded from the prepared asset.
    # Rendering never reruns dashboard.py and the chart does not invent values.
    draft, updated = (result["values"] for result in prepared.results)
    published_at = prepared.script.checkpoints[1].publish
    boxes = (Bounds(80, 225, 1015, 657), Bounds(985, 225, 1515, 657), Bounds(1480, 225, 1840, 657))
    for kind, box in zip(("line", "bar", "donut"), boxes):
        handle = put(segment, chart_factory(kind, draft["sessions"]), f"{kind}-chart", box, z_index=2)
        segment.play(handle["chart"], lambda c: ChartReveal(c), at=0, duration=1.3)
        if kind == "line":
            segment.play(
                handle["chart"],
                lambda c: c.animate.data_to({"Sessions": list(enumerate(updated["sessions"]))}),
                at=published_at,
                duration=1.5,
            )
        elif kind == "bar":
            segment.play(
                handle["chart"],
                lambda c: c.animate.data_to({"Sessions": updated["sessions"]}),
                at=published_at,
                duration=1.5,
            )
        else:
            segment.play(
                handle["chart"], lambda c: c.animate.data_to(updated["sessions"]), at=published_at, duration=1.5
            )
    map_box = Bounds(80, 600, 1125, 971)
    surface(segment, map_box, "map-surface")
    inside = card_content_bounds(map_box, shadow=SHADOW, padding=18)
    map_handle = put(
        segment,
        lambda c, b: OutlineMap(
            width=b.width, height=b.height, fill="#C8C4BC", border_color="#FFFFFF", border_width=1.5, position=b.center
        ),
        "outline-map",
        Bounds(inside.left, inside.top, inside.right - 285, inside.bottom),
        z_index=3,
    )
    segment.play(map_handle, lambda c: c.animate.zoom_to("Nepal"), at=2.8, duration=2.4)
    globe = put(
        segment,
        lambda c, b: EarthMap(width=140, height=140, longitude=60, latitude=20, position=b.center),
        "earth-map",
        Bounds(inside.right - 250, inside.top + 6, inside.right - 110, inside.top + 146),
        z_index=3,
    )
    segment.play(globe, lambda c: c.animate.rotate(longitude=140), at=1, duration=5)
    put(
        segment,
        lambda c, b: SatelliteMap(width=160, height=88, longitude=84, latitude=28, zoom=9, position=b.center),
        "satellite-map",
        Bounds(inside.right - 260, inside.bottom - 95, inside.right - 100, inside.bottom - 7),
        z_index=3,
    )
    put(
        segment,
        lambda c, b: Image(c.assets.image("nepal-flag"), width=54, height=60, position=b.center),
        "named-flag",
        Bounds(inside.right - 72, inside.top + 4, inside.right - 18, inside.top + 64),
        z_index=3,
    )
    text(
        segment,
        "Nepal",
        Bounds(inside.right - 85, inside.top + 78, inside.right, inside.top + 123),
        "map-region",
        size=27,
        weight=700,
        align="center",
    )
    metric_box = Bounds(1070, 610, 1840, 970)
    surface(segment, metric_box, "metric-surface")
    inside = card_content_bounds(metric_box, shadow=SHADOW, padding=18)
    number_handle = put(
        segment,
        lambda c, b: Number(
            draft["total"], font=c.theme.font, font_weight=700, font_size=76, color=INK, position=b.center
        ),
        "session-number",
        Bounds(inside.left, inside.top, inside.left + 230, inside.top + 94),
        z_index=3,
    )
    segment.play(number_handle, lambda c: c.animate.value_to(updated["total"]), at=published_at, duration=1.5)
    text(
        segment,
        "sessions",
        Bounds(inside.left, inside.top + 98, inside.left + 230, inside.top + 145),
        "metric-label",
        size=26,
        color=MUTED,
        align="center",
    )
    for id, kind, x, width in (("ring", ProgressRing, inside.left + 322, 92), ("gauge", Gauge, inside.left + 470, 104)):
        h = put(
            segment,
            lambda c, b, k=kind, w=width: k(
                width=w, height=w, color=ORANGE, track_color="#EAE7E2", stroke_width=11, position=b.center
            ),
            id,
            Bounds(x - 56, inside.top + 18, x + 56, inside.top + 132),
            z_index=3,
        )
        segment.play(h, lambda c: c.animate.progress_to(0.82), at=1.2, duration=4.2)
    text(
        segment,
        "Python result · dashboard.py",
        Bounds(inside.left, inside.bottom - 40, inside.right, inside.bottom),
        "illustrative-label",
        size=24,
        color=MUTED,
        align="center",
    )


def arch_design():
    """An original project module, including dimensional annotations and section."""
    return {
        "units": "m",
        "style": {"concept": "clay", "color": "#E1DDD5", "edge_color": ORANGE},
        "camera": {"position": [7, -7, 5], "focal_point": [0, 0, 0.25], "zoom": 1.05},
        "parts": [
            {
                "id": "base",
                "mesh": {"primitive": "cube", "params": {"x_length": 3, "y_length": 1.8, "z_length": 0.22}},
                "position": [0, 0, -0.64],
                "style": {"color": "#BCB8B1", "edge_color": "#737373"},
            },
            {
                "id": "shell",
                "mesh": {"primitive": "cube", "params": {"x_length": 2.8, "y_length": 1.6, "z_length": 1.1}},
                "style": {"concept": "transparent", "color": "#A7B0B2", "edge_color": "#A7B0B2"},
            },
            {
                "id": "shaft",
                "mesh": {
                    "primitive": "cylinder",
                    "params": {"direction": [1, 0, 0], "radius": 0.25, "height": 2.2, "resolution": 24},
                },
                "style": {"color": ORANGE, "edge_color": ORANGE},
            },
            {
                "id": "cover",
                "mesh": {"primitive": "cube", "params": {"x_length": 2.8, "y_length": 1.6, "z_length": 0.12}},
                "position": [0, 0, 0.64],
                "explode_vector": [0, 0, 1],
                "style": {"color": "#E8E6E2", "edge_color": "#737373"},
            },
        ],
        "script": {
            "duration": 8.5,
            "actions": [
                {"kind": "orbit", "degrees": -20, "at": 0.7, "duration": 1.3, "easing": "smooth"},
                {"kind": "explode", "targets": ["cover"], "factor": 0.7, "at": 2, "duration": 1.5, "easing": "smooth"},
                {"kind": "highlight", "targets": ["shaft"], "color": ORANGE, "at": 3.5, "duration": 0.7},
                {
                    "kind": "section",
                    "targets": ["shell"],
                    "origin": [0, 0, 0],
                    "normal": [1, 0, 0],
                    "at": 4.2,
                    "duration": 1.8,
                },
                {"kind": "orbit", "degrees": -15, "at": 4.4, "duration": 1.5, "easing": "smooth"},
                {"kind": "explode", "targets": ["cover"], "factor": 0, "at": 6.4, "duration": 1.5, "easing": "smooth"},
            ],
        },
        "labels": [
            {
                "text": "Cover",
                "point": [0, 0, 0],
                "part": "cover",
                "offset": [180, -90],
                "font_size": 32,
                "color": ORANGE,
            },
            {
                "text": "Core",
                "point": [0, 0, 0],
                "part": "shaft",
                "offset": [-180, 40],
                "font_size": 32,
                "color": ORANGE,
            },
        ],
        "dimensions": [
            {
                "start": [-1.5, -0.9, -0.1],
                "end": [1.5, -0.9, -0.1],
                "part": "base",
                "offset": [0, 80],
                "font_size": 30,
                "color": ORANGE,
            }
        ],
    }


def build_arch(segment, ctx, prepared, capture):
    segment.add(
        Framed(ArchCanvas(arch_design(), viewport=(1600, 760)), padding=10),
        id="arch-assembly",
        bounds=Bounds(96, 205, 1824, 966),
    )
    text(
        segment,
        "Assembly · dimensions · sections · camera motion",
        Bounds(400, 940, 1520, 990),
        "arch-detail",
        size=27,
        color=MUTED,
        align="center",
    )


def chess_script():
    return ChessScript(
        {
            "schema_version": 1,
            "duration": 7.7,
            "players": {"white": "White", "black": "Black"},
            "moves": [
                {"uci": "e2e4", "at": 0.9, "duration": 0.8},
                {"uci": "e7e5", "at": 2.1, "duration": 0.8},
                {"uci": "g1f3", "at": 3.3, "duration": 0.8},
            ],
            "annotations": [{"type": "arrow", "from": "f3", "to": "e5", "at": 4.2, "duration": 2.8, "color": ORANGE}],
        }
    )


def finish_flow():
    graph = FlowGraph(
        (
            FlowNode("files", "Assets", symbol="document", size=(155, 100)),
            FlowNode("build", "Build", symbol="server", size=(155, 100)),
            FlowNode("dashboard", "Dashboard", symbol="service", size=(175, 100)),
        ),
        (FlowEdge("input", "files", "build"), FlowEdge("output", "build", "dashboard")),
    )
    script = (
        FlowScript()
        .reveal(["files", "build", "dashboard"], at=0.8, duration=0.7, stagger=0.12)
        .draw(["input", "output"], at=1.8, duration=0.7, stagger=0.1)
        .signal(["input", "output"], at=3, duration=1.5, marker="packet", color=ORANGE)
        .highlight("dashboard", at=5, duration=0.7, color=ORANGE, mode="tint")
    )
    return graph, script


def build_finish(segment, ctx, prepared, capture):
    chess = ChessBoard(
        chess_script(),
        theme=ChessTheme(
            light="#F5F2EC",
            dark="#BDB7AE",
            background="#FFFFFF",
            panel="#FFFFFF",
            foreground=INK,
            muted=MUTED,
            accent=ORANGE,
            check=ORANGE,
            white_piece="#FFFFFF",
            black_piece=INK,
        ),
    )
    segment.add(Framed(chess, padding=10), id="chess-board", bounds=Bounds(78, 220, 920, 922))
    equation_box = Bounds(860, 215, 1840, 590)
    surface(segment, equation_box, "equation-surface")
    inside = card_content_bounds(equation_box, shadow=SHADOW, padding=20)
    equation = put(
        segment,
        lambda c, b: Equation(r"y = \sum_{i=1}^{n} x_i", font_size=62, color=INK, position=b.center),
        "equation",
        Bounds(inside.left, inside.top, inside.right, inside.top + 145),
        z_index=4,
    )
    segment.play(equation, lambda c: Write(c), at=0, duration=1.4)
    text(
        segment,
        "Clear inputs. Clear outcome.",
        Bounds(inside.left, inside.top + 150, inside.right, inside.bottom),
        "equation-label",
        size=31,
        color=MUTED,
        align="center",
    )
    underline = segment.add(
        WhiteboardDrawing(
            (WhiteboardPath(((15, 30), (180, 24), (320, 28), (505, 18)), color=ORANGE, stroke_width=6),),
            viewbox=(520, 55),
        ),
        id="whiteboard-mark",
        bounds=Bounds(1110, 485, 1595, 530),
        at=1.6,
        z_index=5,
    )
    segment.play(underline["stroke-0"], lambda c: Draw(c), at=1.6, duration=0.8)
    graph, script = finish_flow()
    flow = FlowCanvas(
        graph,
        script,
        viewport=(1250, 370),
        theme=FlowTheme(
            foreground=INK,
            surface="#FFFFFF",
            accent=ORANGE,
            background="#00000000",
            font=ctx.theme.font,
            font_size=36,
            minimum_font_size=26,
            stroke_width=3,
            stroke=MUTED,
        ),
    )
    segment.add(Framed(flow, padding=12), id="request-flow", bounds=Bounds(868, 542, 1840, 899))
    complete = put(
        segment,
        lambda c, b: Checkmark(width=64, height=64, color=ORANGE, stroke_width=7, position=b.center),
        "completion-check",
        Bounds(888, 894, 968, 974),
        at=4.6,
        z_index=5,
    )
    segment.play(complete, lambda c: c.animate.progress_to(1), at=5.3, duration=0.7)
    text(segment, "Ready to create.", Bounds(994, 899, 1650, 961), "completion-label", size=44, weight=700, at=4.6)


BUILDERS = (build_plan, build_os, build_code, build_html, build_insights, build_arch, build_finish)


def build(ctx):
    # Required fonts/assets are resolved by the named registry; no downloads occur.
    ctx.assets.font("ui-font")
    prepared = ctx.playground(code_script(), timeout=15, fps=30)
    capture = prepared_web(ctx)
    video = Video(ctx)
    for index, (window, compose) in enumerate(zip(scene_windows(), BUILDERS)):
        with video.segment(window["id"], start=window["start"], duration=window["end"] - window["start"]) as segment:
            text(segment, window["label"], Bounds(100, 64, 1820, 181), "heading", size=76, weight=700)
            compose(segment, ctx, prepared, capture)
            # Incoming scenes cover outgoing decorations while their content overlaps.
            # Headings and footnotes hand off at the nominal boundary for readability.
            for placement in segment.placements:
                placement.z_index += index * 100
                name = placement.handle.placement.rsplit("/", 1)[-1]
                if name == "heading" or name.endswith("-detail"):
                    placement.at = window["nominal_start"] - window["start"]
                    placement.duration = window["nominal_end"] - window["nominal_start"]
                    placement.enter_duration = OVERLAP / 2
                    placement.exit_duration = OVERLAP / 2
    with video.segment("progress", start=0, duration=TOTAL_DURATION) as segment:
        text(segment, "clean-flow", Bounds(110, 996, 380, 1038), "theme-name", size=24, weight=700, color=MUTED)
        for index, (_, start, end, _) in enumerate(NOMINAL_SCENES):
            x = 698 + index * 125
            h = put(
                segment,
                lambda c, b: ProgressBar(width=102, height=10, color=ORANGE, track_color="#CFCAC3", position=b.center),
                f"progress-{index}",
                Bounds(x, 1010, x + 102, 1020),
                z_index=20,
            )
            segment.play(h, lambda c: c.animate.progress_to(1), at=start + 0.65, duration=max(0.5, end - start - 1.25))
        text(segment, "01:00", Bounds(1610, 996, 1790, 1038), "duration-label", size=24, color=MUTED, align="right")
    return video
