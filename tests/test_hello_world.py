"""The premium opening can be checked without rendering scene frames."""

import importlib.util
import math
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from faceless_champ import Canvas, PillowRenderer

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/programming/hello_world"


@pytest.mark.parametrize(
    ("quality", "dimensions"), [("low", (1280, 720)), ("high", (1920, 1080)), ("4k", (3840, 2160))]
)
@pytest.mark.parametrize("mode", ["--full", "--render"])
def test_example_renderer_applies_fps_and_quality_without_rendering(
    tmp_path, monkeypatch, capsys, quality, dimensions, mode
):
    import faceless_champ

    captured = []
    monkeypatch.setitem(
        sys.modules,
        "scene",
        SimpleNamespace(
            DURATION=14.96,
            check_scene=dict,
            build_scene=lambda: SimpleNamespace(canvas=Canvas(1920, 1080)),
        ),
    )

    def fake_render(scene, output, **kwargs):
        captured.append((scene, kwargs))
        kwargs["progress"](0, 2)
        kwargs["progress"](1, 2)
        kwargs["progress"](2, 2)

    monkeypatch.setattr(faceless_champ, "render", fake_render)
    output = tmp_path / "opening.mp4"
    monkeypatch.setattr(
        sys,
        "argv",
        [str(EXAMPLE / "render.py"), mode, "--quality", quality, "--fps", "48", "--output", str(output)],
    )
    runpy.run_path(str(EXAMPLE / "render.py"))["main"]()
    scene, options = captured[0]
    assert options["settings"].dimensions(scene.canvas) == dimensions
    assert options["settings"].fps == 48 and options["end_time"] == 14.96
    assert options["start_time"] == 0
    feedback = capsys.readouterr()
    assert "Exported" in feedback.err and "ETA" in feedback.err
    assert feedback.out.strip() == str(output)
    assert not output.exists()


def test_opening_checks_preserve_inputs_and_never_render_frames(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Structural checks must not render scene frames")

    monkeypatch.setattr(PillowRenderer, "frame", forbidden)
    spec = importlib.util.spec_from_file_location("premium_hello_world", EXAMPLE / "scene.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.check_scene()
    assert report["duration"] == module.DURATION and report["audio_tracks"] == 1
    assert report["layout_samples"] == math.ceil(module.DURATION * 60)
    assert report["minimum_face_clearance_px"] >= 32
    assert not report["media_rendered"] and not report["full_export_verified"]


def test_runner_rejects_invalid_review_ranges_without_creating_outputs(tmp_path):
    output = tmp_path / "unexpected.mp4"
    result = subprocess.run(
        [sys.executable, str(EXAMPLE / "render.py"), "--range", "-1", "0", "--output", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0 and "--range must satisfy" in result.stderr
    assert not output.exists()
