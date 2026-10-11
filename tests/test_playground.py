"""Behavioral contracts for execution, source fidelity, and random-access playback."""

import json
import os
from copy import deepcopy

import pytest

from faceless_champ import (
    Canvas,
    CanvasItem,
    CodeCheckpoint,
    CodeEditor,
    EditTimeline,
    EventBinding,
    Group,
    PillowRenderer,
    PlaygroundCanvas,
    PlaygroundError,
    PlaygroundOutput,
    PlaygroundScript,
    PreparedPlayground,
    RectangleMask,
    Scene,
    ValueBinding,
    prepare_playground,
)


def checkpoint(source="print(42)", **kwargs):
    values = {
        "id": "one",
        "files": {"main.py": source},
        "active_file": "main.py",
        "entrypoint": "main.py",
        "edit_start": 0,
        "edit_end": 1,
        "publish": 1,
    }
    values.update(kwargs)
    return CodeCheckpoint(**values)


def script(source="print(42)", **kwargs):
    return PlaygroundScript([checkpoint(source)], duration=3, **kwargs)


def prepare(tmp_path, source="print(42)", **kwargs):
    return prepare_playground(script(source), cache_dir=tmp_path, **kwargs)


@pytest.mark.parametrize("path", ["../out.py", "/out.py", "a/../../out.py", "a\\b.py", "a//b", "./a.py", "C:/x"])
def test_sources_cannot_escape_project(path):
    with pytest.raises(PlaygroundError):
        checkpoint(files={path: ""}, active_file=path, entrypoint=path)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"publish": 0.5},
        {"edit_start": 2},
        {"first_line": 0},
        {"runtime": "node"},
        {"active_file": "missing"},
        {"inputs": {"x": float("nan")}},
    ],
)
def test_checkpoint_validation(kwargs):
    with pytest.raises(ValueError):
        checkpoint(**kwargs)


def test_order_and_snapshot_contract():
    with pytest.raises(PlaygroundError):
        PlaygroundScript([checkpoint(), checkpoint(id="two", edit_start=0.5, publish=2)], duration=3)
    files = {"main.py": "a\t= 1\r\n"}
    s = PlaygroundScript([checkpoint(files=files)], duration=3)
    files["main.py"] = "changed"
    assert s.record()["checkpoints"][0]["files"]["main.py"] == "a\t= 1\r\n"
    assert deepcopy(s).record() == s.record()


@pytest.mark.parametrize(
    "before,after",
    [
        ("abc def", "ax def!"),
        ("a\n\tb\n", "x\n\ty\nz\n"),
        ("hello", ""),
        ("", "hello"),
        ("abc", "abc"),
        ("a\r\nb", "a\r\nc"),
    ],
)
def test_edits_are_seekable_and_exact(before, after):
    s = PlaygroundScript(
        [checkpoint(before, edit_end=0, publish=0), checkpoint(after, id="two", edit_start=1, edit_end=2, publish=2)],
        duration=3,
    )
    timeline = EditTimeline(s)
    assert timeline.state_at(0.9)["source"] == before
    assert timeline.state_at(1)["source"] == before
    middle = timeline.state_at(1.5)
    assert timeline.state_at(2)["source"] == after
    assert timeline.state_at(1.5) == middle
    assert timeline.state_at(2.9)["source"] == after


def test_file_switch_and_explicit_scroll():
    first = checkpoint(files={"main.py": "a=1\nb=2\nc=3", "other.py": "\tx=1"})
    second = checkpoint(
        id="two",
        files={"main.py": "a=1\nb=4\nc=3", "other.py": "\tx=2"},
        edit_start=1.5,
        edit_end=2,
        publish=2,
        active_file="other.py",
    )
    timeline = EditTimeline(PlaygroundScript([first, second], duration=3))
    assert timeline.state_at(1.5)["source"] == "\tx=1"
    assert timeline.state_at(2)["file"] == "other.py"
    editor = CodeEditor(
        PlaygroundScript([checkpoint("a=1\nb=2\nc=3", first_line=2)], duration=3), width=500, height=230
    )
    state = editor.timeline.state_at(1)
    assert editor._panel(state).first_line == 2
    assert editor._panel(state).code == "b=2\nc=3"


def test_python_real_values_inputs_and_independent_checkpoints(tmp_path):
    source = 'from faceless_champ.playground.runtime import emit, event, inputs\nx=inputs()["n"]\nemit("v", x*2)\nevent("done")\nprint(x)'
    s = PlaygroundScript(
        [
            checkpoint(source, inputs={"n": 3}),
            checkpoint(source, id="two", edit_start=1.5, edit_end=2, publish=2, inputs={"n": 7}),
        ],
        duration=3,
        items=[CanvasItem("v", "variable")],
        bindings=[ValueBinding("v", "v")],
        events=[EventBinding("one", "done", "v", 1.1, 0.5)],
    )
    prepared = prepare_playground(s, cache_dir=tmp_path)
    assert [r["values"]["v"] for r in prepared.results] == [6, 14]
    canvas = PlaygroundCanvas(prepared, width=400, height=220)
    assert canvas.state_at(0.99) is None
    assert canvas.state_at(1)["items"]["v"]["value"] == 6
    assert canvas.state_at(1.999)["items"]["v"]["value"] == 6
    assert canvas.state_at(2)["items"]["v"]["value"] == 14


def test_actual_class_instances_are_independent(tmp_path):
    source = """from faceless_champ.playground.runtime import emit
class Car:
    speed = 0
a, b = Car(), Car()
a.speed += 40
emit("a", {"speed": a.speed})
emit("b", {"speed": b.speed})
"""
    s = script(
        source,
        items=[CanvasItem("a", "car"), CanvasItem("b", "car")],
        bindings=[ValueBinding("a", "a"), ValueBinding("b", "b")],
    )
    p = prepare_playground(s, cache_dir=tmp_path)
    assert p.results[0]["values"] == {"a": {"speed": 40}, "b": {"speed": 0}}


@pytest.mark.parametrize(
    "source,code",
    [
        ('raise RuntimeError("boom")', "PLAYGROUND_EXECUTION"),
        ("while True: pass", "PLAYGROUND_TIMEOUT"),
        ('print("x" * 100000)', "PLAYGROUND_OUTPUT_LIMIT"),
        ('import os\nopen(os.environ["FACELESS_PLAYGROUND_EMIT"],"w").write("not json")', "PLAYGROUND_EMISSION"),
    ],
)
def test_execution_failures_are_scoped_and_not_published(tmp_path, source, code):
    with pytest.raises(PlaygroundError) as error:
        prepare(tmp_path, source, timeout=0.8, output_limit=10000)
    assert error.value.code == code
    assert error.value.scope["checkpoint"] == "one"
    assert not list(tmp_path.glob("*/manifest.json"))


def test_expected_failure_is_explicit(tmp_path):
    s = PlaygroundScript([checkpoint('raise ValueError("lesson")', expected_failure=True)], duration=3)
    p = prepare_playground(s, cache_dir=tmp_path)
    assert p.results[0]["exit_code"] != 0 and "lesson" in p.results[0]["stderr"]
    s = PlaygroundScript([checkpoint(expected_failure=True)], duration=3)
    with pytest.raises(PlaygroundError, match="Expected failure"):
        prepare_playground(s, cache_dir=tmp_path)


@pytest.mark.parametrize(
    "value,kind", [("42", "matrix"), ("[[1],[2,3]]", "matrix"), ("[True]", "vector"), ("1", "car")]
)
def test_binding_types_fail_before_render(tmp_path, value, kind):
    source = f'from faceless_champ.playground.runtime import emit\nemit("x", {value})'
    with pytest.raises(PlaygroundError) as error:
        prepare_playground(
            script(source, items=[CanvasItem("x", kind)], bindings=[ValueBinding("x", "x")]), cache_dir=tmp_path
        )
    assert error.value.code == "PLAYGROUND_BINDING"


def test_missing_binding_and_event_order(tmp_path):
    with pytest.raises(PlaygroundError, match="Missing emitted"):
        prepare_playground(script(items=[CanvasItem("x")], bindings=[ValueBinding("x", "x")]), cache_dir=tmp_path)
    source = 'from faceless_champ.playground.runtime import event\nevent("b")\nevent("a")'
    s = script(
        source,
        items=[CanvasItem("x", "flow")],
        events=[EventBinding("one", "a", "x", 1, 0.3), EventBinding("one", "b", "x", 1.5, 0.3)],
    )
    with pytest.raises(PlaygroundError, match="event order"):
        prepare_playground(s, cache_dir=tmp_path)
    with pytest.raises(PlaygroundError, match="target/property"):
        script(items=[CanvasItem("x")], bindings=[ValueBinding("x", "x", "bogus")])


def test_cache_hit_refresh_corruption_and_no_implicit_execution(tmp_path, monkeypatch):
    p = prepare(tmp_path)
    again = prepare(tmp_path)
    assert again.directory == p.directory
    refreshed = prepare(tmp_path, refresh=True)
    assert refreshed.directory != p.directory
    assert p.results == refreshed.results
    assert prepare(tmp_path).directory == refreshed.directory
    changed = prepare(tmp_path, "print(43)")
    assert changed.fingerprint != p.fingerprint
    import subprocess

    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("Implicit execution"))
    loaded = PreparedPlayground(p.directory)
    PlaygroundOutput(loaded, width=400, height=120).frame_image(1)
    manifest = p.directory / "manifest.json"
    record = json.loads(manifest.read_text())
    record["results"][0]["stdout"] = "tampered"
    manifest.write_text(json.dumps(record))
    with pytest.raises(PlaygroundError, match="Corrupt results"):
        PreparedPlayground(p.directory)


def test_render_seeking_snapshot_masks_and_cache_parity(tmp_path):
    s = script()
    prepared = prepare_playground(s, cache_dir=tmp_path)
    editor = CodeEditor(
        s, width=430, height=240, font_size=20, position=(240, 140), mask=RectangleMask(width=430, height=240)
    )
    output = PlaygroundOutput(prepared, width=350, height=90, position=(250, 330))
    group = Group(editor, output, rotation=2, scale=0.9)
    scene = Scene(Canvas(500, 400)).add(group).wait(3)
    cached, uncached = PillowRenderer(1), PillowRenderer(1, code_cache_mb=0, frame_cache_mb=0)
    cached.validate(scene)
    before = cached.frame(scene, 0.5, (500, 400)).tobytes()
    editor.timeline.script.checkpoints = ()  # Authored component mutation must not affect scene snapshot.
    for time in (2, 0, 1, 0.5, 2.9):
        assert cached.frame(scene, time, (500, 400)).tobytes() == uncached.frame(scene, time, (500, 400)).tobytes()
    assert cached.frame(scene, 0.5, (500, 400)).tobytes() == before
    assert cached._code_cache_bytes == 0


@pytest.mark.skipif(os.environ.get("FC_WEB_BROWSER_TESTS") != "1", reason="opt-in Chromium integration")
def test_web_revisions_real_pixels_console_and_expected_error(tmp_path):
    def web(text, **kwargs):
        return checkpoint(
            files={"index.html": text}, active_file="index.html", entrypoint="index.html", runtime="web", **kwargs
        )

    first = web(
        '<body style="background:red"><script>setTimeout(()=>console.log("later"),500)</script>', edit_end=0, publish=0
    )
    second = web('<body style="background:blue">', id="two", edit_start=0.5, edit_end=1, publish=1)
    p = prepare_playground(
        PlaygroundScript([first, second], duration=2, mode="web", viewport=(100, 100)),
        cache_dir=tmp_path,
        fps=4,
        timeout=20,
    )
    view = PlaygroundCanvas(p, width=100, height=100)
    assert view.frame_image(0.4).getpixel((50, 50))[:3] == (255, 0, 0)
    assert view.frame_image(1).getpixel((50, 50))[:3] == (0, 0, 255)
    from faceless_champ.web import WebCapture

    capture = WebCapture(p.directory / p.results[0]["capture"])
    assert capture.metadata(0)["console_count"] == 0
    assert capture.metadata(0.75)["console_count"] == 1
    error = web('<script>throw Error("teaching")</script>', expected_failure=True)
    p = prepare_playground(
        PlaygroundScript([error], duration=2, mode="web", viewport=(100, 100)), cache_dir=tmp_path, fps=2, timeout=20
    )
    assert "teaching" in p.results[0]["stderr"]


def test_tensor_cell_emphasis_and_invalid_cells(tmp_path):
    source = 'from faceless_champ.playground.runtime import emit, event\nemit("m", [[1,2],[3,4]])\nevent("cell")'
    s = script(
        source,
        items=[CanvasItem("m", "matrix")],
        bindings=[ValueBinding("m", "m")],
        events=[EventBinding("one", "cell", "m", 1.2, 0.5, cell=(1, 0))],
    )
    p = prepare_playground(s, cache_dir=tmp_path)
    view = PlaygroundCanvas(p, width=400, height=300)
    assert view.frame_image(1.3).tobytes() != view.frame_image(1).tobytes()
    s = script(
        source,
        items=[CanvasItem("m", "matrix")],
        bindings=[ValueBinding("m", "m")],
        events=[EventBinding("one", "cell", "m", 1.2, 0.5, cell=(9, 0))],
    )
    with pytest.raises(PlaygroundError, match="outside tensor"):
        prepare_playground(s, cache_dir=tmp_path)
    with pytest.raises(PlaygroundError, match="static value"):
        CanvasItem("m", "matrix", value=42)


def test_prepared_snapshot_is_immutable(tmp_path):
    p = prepare(tmp_path)
    with pytest.raises(AttributeError, match="immutable"):
        p.directory = tmp_path
    p.script.checkpoints = ()
    p.results[0]["stdout"] = "wrong"
    assert len(p.script.checkpoints) == 1
    assert p.results[0]["stdout"] == "42\n"
    assert deepcopy(checkpoint()).files["main.py"] == "print(42)"


def test_interrupted_preparation_cleans_worker_and_staging(tmp_path, monkeypatch):
    import importlib
    import time

    module = importlib.import_module("faceless_champ.playground.prepare")
    marker = tmp_path / "pid.txt"
    source = f'import os\nopen({str(marker)!r},"w").write(str(os.getpid()))\nwhile True: pass'
    original_sleep = time.sleep

    def interrupt(_):
        original_sleep(0.2)
        raise KeyboardInterrupt

    monkeypatch.setattr(module.time, "sleep", interrupt)
    with pytest.raises(KeyboardInterrupt):
        prepare(tmp_path / "cache", source)
    assert not list((tmp_path / "cache").iterdir())
    if marker.exists() and os.name == "posix":
        with pytest.raises(ProcessLookupError):
            os.kill(int(marker.read_text()), 0)


def test_many_revisions_do_not_retain_intermediate_sprites():
    checkpoints = [
        checkpoint(f"value = {i}", id=str(i), edit_start=i, edit_end=i + 0.5, publish=i + 0.5) for i in range(40)
    ]
    s = PlaygroundScript(checkpoints, duration=41)
    editor = CodeEditor(s, width=400, height=220, position=(200, 110))
    scene = Scene(Canvas(400, 220)).add(editor).wait(41)
    renderer = PillowRenderer(1, code_cache_mb=1, frame_cache_mb=1)
    for i in range(40):
        renderer.frame(scene, i + 0.25, (400, 220))
    assert renderer._code_cache_bytes == 0
    assert len(renderer._scene_frames) <= 1
