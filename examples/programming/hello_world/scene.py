"""Draft premium opening. Importing this module never renders or executes code."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Bounds,
    Canvas,
    Circle,
    CodeReveal,
    CodeWorkspaceDesign,
    CodingChamp,
    FlowChamp,
    FlowEdge,
    FlowGraph,
    FlowNode,
    FlowScript,
    FlowTheme,
    Group,
    Polyline,
    Rectangle,
    Scene,
    Spring,
    Text,
    linear,
    smooth,
)
from faceless_champ.os_ui import File, Folder, MacOSPreset, OSClip, OSScript, VirtualFileSystem

ROOT = Path(__file__).resolve().parent
STATUS = "draft"
DURATION = 14.96
CANVAS_SIZE = (1920, 1080)
BACKGROUND = "#E8E6E2"
ACCENT = "#FF5A20"
PYTHON_BLUE = "#3776AB"
PYTHON_YELLOW = "#FFD343"
SOURCE = 'print("Hello World")'
OUTPUT = "Hello World"
WORKSPACE = CodeWorkspaceDesign.named("clean-flow", bounds=Bounds(96, 108, 1824, 972))
WINDOW_SPRING = Spring(stiffness=180, damping=27, mass=1)
ICON_SPRING = Spring(stiffness=180, damping=23, mass=1)
TIMES = {
    "intro_exit": 3.78,
    "editor_in": 4.10,
    "typing": 7.76,
    "split": 9.79,
    "terminal_in": 10.60,
    "signal": 11.20,
    "output": 12.99,
    "hold": 13.76,
}
INPUT_SHA256 = {
    "audio.mp3": "cd5764b59b939230a4112116f793013e476029d1511c873bf452ebdff9533002",
    "cue-per-word.srt": "6ed87164415c77d24bc3ccd47d76d7c51cd8e208973a741803b802fbb0741842",
    "normal-subtitle.srt": "a9bc26e35d22306ef56ea1e64eac3e7d6e8561f85ea84885b65e33b4d3f73e94",
}


def _rounded_outline(corners, radius=15):
    """Round a local, orthogonal silhouette using quadratic corner segments."""
    result = []
    for i, corner in enumerate(corners):
        previous, following = corners[i - 1], corners[(i + 1) % len(corners)]
        distances = (math.dist(corner, previous), math.dist(corner, following))
        inset = min(radius, *(distance / 2 for distance in distances))
        start = tuple(c + (p - c) * inset / distances[0] for c, p in zip(corner, previous))
        end = tuple(c + (p - c) * inset / distances[1] for c, p in zip(corner, following))
        for step in range(9):
            t = step / 8
            result.append(
                tuple((1 - t) ** 2 * a + 2 * (1 - t) * t * c + t**2 * b for a, c, b in zip(start, corner, end))
            )
    return tuple(result)


def _python_emblem():
    # Two interlocking silhouettes, authored as vectors rather than text glyphs.
    upper = (
        (-8, -142),
        (-100, -142),
        (-100, -52),
        (-20, -52),
        (-20, -30),
        (-152, -30),
        (-152, 84),
        (-108, 84),
        (-108, 10),
        (16, 10),
        (40, -14),
        (40, -142),
    )
    blue = _rounded_outline(upper)
    yellow = tuple((-x, -y) for x, y in blue)
    return Group(
        Polyline(blue, closed=True, fill=PYTHON_BLUE, stroke=BACKGROUND, stroke_width=10),
        Polyline(yellow, closed=True, fill=PYTHON_YELLOW, stroke=BACKGROUND, stroke_width=10),
        Circle(7, fill="white", stroke=None, position=(-70, -108)),
        Circle(7, fill="white", stroke=None, position=(70, 108)),
        position=(370, 568),
        scale=0.90,
        opacity=0,
    )


def _fade(scene, component, at, duration, opacity):
    with scene.at(at):
        scene.play(component.animate.opacity_to(opacity), run_time=duration, rate_func=smooth)


def _compose():
    scene = Scene(Canvas(*CANVAS_SIZE, BACKGROUND))
    emblem = _python_emblem()
    finder = OSClip(
        VirtualFileSystem(Folder("root", "Python", (File("hello", "hello.py", SOURCE),))),
        OSScript().select("hello", at=1.10, duration=0.7, cursor=False),
        mode="finder",
        width=1280,
        height=800,
        cursor=False,
        preset=MacOSPreset(wallpaper=BACKGROUND, accent=ACCENT, font=str(CLEAN_FLOW_FONT), font_size=28),
        position=(1240, 560),
        scale=0.77,
        opacity=0,
    )

    box, unit = WORKSPACE.code_bounds, WORKSPACE.unit
    code = CodingChamp(
        SOURCE,
        language="python",
        theme=WORKSPACE.theme,
        chrome=False,
        font_size=WORKSPACE.code_size * unit,
        padding=8 * unit,
        width=box.width,
        height=box.height,
        position=(box.left, box.top),
        anchor="top_left",
    )
    code.reveal = 0
    caret = Rectangle(
        width=3,
        height=46 * unit,
        fill=ACCENT,
        stroke=None,
        position=(box.left + code.code_x, box.top + code.code_y + 4),
        anchor="top_left",
    )
    editor = WORKSPACE.window(WORKSPACE.editor_full, "hello.py", children=(code, caret))
    editor.position = (960, 562)
    editor.scale, editor.opacity = 0.96, 0

    terminal_box = WORKSPACE.terminal_bounds
    output = CodingChamp(
        OUTPUT,
        language="text",
        theme=WORKSPACE.theme,
        chrome=False,
        line_numbers=False,
        font_size=WORKSPACE.terminal_size * unit,
        padding=0,
        width=terminal_box.width - 48 * unit,
        height=100 * unit,
        position=(terminal_box.left + 24 * unit, terminal_box.top + 112 * unit),
        anchor="top_left",
    )
    output.reveal = 0
    terminal = WORKSPACE.window(terminal_box, "Terminal", children=(output,))
    terminal.position = (terminal_box.center[0], terminal_box.center[1] + 20)
    terminal.scale, terminal.opacity = 0.96, 0

    graph = FlowGraph(
        (
            FlowNode("source", symbol="junction", position=(380, 40), size=(12, 12)),
            FlowNode("result", symbol="junction", position=(1340, 40), size=(12, 12)),
        ),
        (FlowEdge("execution", "source", "result", route="straight"),),
        layout="manual",
    )
    flow = FlowChamp(
        graph,
        FlowScript()
        .reveal(("source", "result", "execution"), at=0, duration=0.30)
        .signal("execution", at=0.32, duration=1.47, marker="capsule", color=ACCENT),
        width=1728,
        height=80,
        position=(960, 934),
        opacity=0,
        theme=FlowTheme(
            background="#00000000", surface=ACCENT, foreground=ACCENT, accent=ACCENT, stroke="#BDB8B1", stroke_width=2
        ),
    )

    scene.add(emblem, finder)
    with scene.at(0):
        scene.play(emblem.animate.move_to(370, 540).scale_to(1), run_time=0.85, rate_func=ICON_SPRING)
    _fade(scene, emblem, 0, 0.45, 1)
    with scene.at(0.30):
        scene.play(finder.animate.move_to(1240, 540).scale_to(0.80), run_time=0.90, rate_func=WINDOW_SPRING)
    _fade(scene, finder, 0.30, 0.50, 1)
    for item in (emblem, finder):
        _fade(scene, item, TIMES["intro_exit"], 0.28, 0)
    with scene.at(TIMES["editor_in"]):
        scene.add(editor)
        scene.play(
            editor.animate.move_to(*WORKSPACE.editor_full.center).scale_to(1), run_time=0.80, rate_func=WINDOW_SPRING
        )
    _fade(scene, editor, TIMES["editor_in"], 0.50, 1)
    for at, opacity in ((5.10, 0), (5.60, 1), (6.10, 0), (6.60, 1), (7.26, 0)):
        _fade(scene, caret, at, 0.10, opacity)
    with scene.at(TIMES["typing"]):
        scene.play(CodeReveal(code), run_time=TIMES["split"] - TIMES["typing"])
    with scene.at(TIMES["split"]):
        scene.play(
            editor.animate.move_to(*WORKSPACE.editor_split.center).scale_to(WORKSPACE.editor_scale),
            run_time=WORKSPACE.shrink_duration,
            rate_func=WINDOW_SPRING,
        )
    with scene.at(TIMES["terminal_in"]):
        scene.add(terminal)
        scene.play(terminal.animate.move_to(*terminal_box.center).scale_to(1), run_time=0.60, rate_func=WINDOW_SPRING)
    _fade(scene, terminal, TIMES["terminal_in"], 0.40, 1)
    with scene.at(TIMES["signal"]):
        scene.add(flow)
    _fade(scene, flow, TIMES["signal"], 0.30, 1)
    with scene.at(TIMES["output"]):
        scene.play(CodeReveal(output), run_time=TIMES["hold"] - TIMES["output"], rate_func=linear)
    scene.add_audio(ROOT / "audio.mp3", start=0, trim_end=DURATION)
    scene.wait_until(DURATION)
    return scene, {
        "emblem": emblem,
        "finder": finder,
        "editor": editor,
        "terminal": terminal,
        "code": code,
        "output": output,
        "caret": caret,
        "flow": flow,
    }


def build_scene():
    """Return the opening only, with source-clock narration and no rendering."""
    return _compose()[0]


def check_scene():
    """Audit authored state and measured geometry without rendering scene frames."""
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in INPUT_SHA256}
    if hashes != INPUT_SHA256:
        raise ValueError("The supplied narration or subtitle inputs changed")
    scene, items = _compose()
    assert math.isclose(scene.duration, DURATION, abs_tol=1e-9)
    assert len(scene.audio) == 1 and scene.audio[0].start == 0 and scene.audio[0].trim_end == DURATION
    allowed_text = {"hello.py", "Terminal", ""}
    assert all(entry.component.text in allowed_text for entry in scene.entries if isinstance(entry.component, Text))
    assert items["code"].code == SOURCE and items["output"].code == OUTPUT
    assert all(not node.label for node in items["flow"].graph.nodes)
    assert not any(isinstance(entry.component, Text) and entry.parent is None for entry in scene.entries)

    def visible(component, time):
        entry = scene._objects[component]
        return entry.start <= time and all(
            ancestor.state_at(time)["opacity"] > 0.001 for ancestor in (entry, *entry.ancestors())
        )

    def overlaps(a, b):
        return min(a.right, b.right) - max(a.left, b.left) > 1 and min(a.bottom, b.bottom) - max(a.top, b.top) > 1

    roots = (items["emblem"], items["finder"], items["editor"], items["terminal"], items["flow"])
    minimum_clearance, samples = math.inf, math.ceil(DURATION * 60)
    for index in range(samples):
        time = index / 60
        active = []
        for root in roots:
            if not visible(root, time):
                continue
            # Window faces define collision regions; shadows are intentional decoration.
            target = root.face if root in (items["editor"], items["terminal"]) else root
            box = scene.bounds_at(target, time)
            clearance = min(box.left, box.top, CANVAS_SIZE[0] - box.right, CANVAS_SIZE[1] - box.bottom)
            assert clearance >= 32, (time, clearance)
            minimum_clearance = min(minimum_clearance, clearance)
            active.append(box)
        assert not any(overlaps(a, b) for i, a in enumerate(active) for b in active[i + 1 :]), time
        state = scene._objects[items["editor"]].state_at(time)
        assert state["scale_x"] == state["scale_y"] == 1
        if time >= TIMES["signal"]:
            assert not items["flow"].diagnostics_at(time - TIMES["signal"])
    assert scene._objects[items["code"]].state_at(TIMES["typing"])["reveal"] == 0
    assert scene._objects[items["code"]].state_at(TIMES["split"])["reveal"] == 1
    assert scene._objects[items["output"]].state_at(TIMES["output"])["reveal"] == 0
    assert scene._objects[items["output"]].state_at(TIMES["hold"])["reveal"] == 1
    return {
        "status": STATUS,
        "structural_checks": "passed",
        "duration": DURATION,
        "canvas": list(CANVAS_SIZE),
        "audio_tracks": 1,
        "audio_start": 0,
        "input_sha256": hashes,
        "layout_samples": samples,
        "minimum_face_clearance_px": round(minimum_clearance, 3),
        "external_text": False,
        "media_rendered": False,
        "full_export_verified": False,
    }
