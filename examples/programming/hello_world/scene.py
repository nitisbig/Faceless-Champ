"""Approved coding design reference; lesson playback never executes displayed code."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

from facelesschamp_kit import CodingTutorialStyle, CodingTutorialTemplate

from faceless_champ import (
    CodeReveal,
    Scene,
    Text,
    linear,
    smooth,
)

ROOT = Path(__file__).resolve().parent
STATUS = "design-approved"
DURATION = 14.96
CANVAS_SIZE = (1920, 1080)
STYLE_PATH = ROOT / "templates/coding-tutorial/style.json"
SOURCE = 'print("Hello World")'
OUTPUT = "Hello World"
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


def _fade(scene, component, at, duration, opacity):
    with scene.at(at):
        scene.play(component.animate.opacity_to(opacity), run_time=duration, rate_func=smooth)


def _compose():
    template = CodingTutorialTemplate(CodingTutorialStyle.load(STYLE_PATH))
    workspace = template.workspace
    scene = Scene(template.canvas())
    emblem = template.emblem()
    finder = template.finder("hello.py", SOURCE, folder="Python")
    editor, code, caret = template.editor(SOURCE, filename="hello.py")
    terminal, output = template.terminal(OUTPUT)
    terminal_box = workspace.terminal_bounds
    flow = template.flow()

    scene.add(emblem, finder)
    with scene.at(0):
        scene.play(emblem.animate.move_to(370, 540).scale_to(1), run_time=0.85, rate_func=template.icon_spring)
    _fade(scene, emblem, 0, 0.45, 1)
    with scene.at(0.30):
        scene.play(finder.animate.move_to(1240, 540).scale_to(0.80), run_time=0.90, rate_func=template.window_spring)
    _fade(scene, finder, 0.30, 0.50, 1)
    for item in (emblem, finder):
        _fade(scene, item, TIMES["intro_exit"], 0.28, 0)
    with scene.at(TIMES["editor_in"]):
        scene.add(editor)
        scene.play(
            editor.animate.move_to(*workspace.editor_full.center).scale_to(1),
            run_time=0.80,
            rate_func=template.window_spring,
        )
    _fade(scene, editor, TIMES["editor_in"], 0.50, 1)
    for at, opacity in ((5.10, 0), (5.60, 1), (6.10, 0), (6.60, 1), (7.26, 0)):
        _fade(scene, caret, at, 0.10, opacity)
    with scene.at(TIMES["typing"]):
        scene.play(CodeReveal(code), run_time=TIMES["split"] - TIMES["typing"])
    with scene.at(TIMES["split"]):
        scene.play(
            editor.animate.move_to(*workspace.editor_split.center).scale_to(workspace.editor_scale),
            run_time=workspace.shrink_duration,
            rate_func=template.window_spring,
        )
    with scene.at(TIMES["terminal_in"]):
        scene.add(terminal)
        scene.play(
            terminal.animate.move_to(*terminal_box.center).scale_to(1),
            run_time=workspace.terminal_entrance_duration,
            rate_func=template.window_spring,
        )
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
