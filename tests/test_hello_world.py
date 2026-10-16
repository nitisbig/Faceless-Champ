"""The premium opening can be checked without rendering scene frames."""

import importlib.util
import subprocess
import sys
from pathlib import Path

from faceless_champ import PillowRenderer

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/programming/hello_world"


def test_opening_checks_preserve_inputs_and_never_render_frames(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Structural checks must not render scene frames")

    monkeypatch.setattr(PillowRenderer, "frame", forbidden)
    spec = importlib.util.spec_from_file_location("premium_hello_world", EXAMPLE / "scene.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.check_scene()
    assert report["duration"] == 14.96 and report["audio_tracks"] == 1
    assert report["layout_samples"] == 898 and report["minimum_face_clearance_px"] >= 32
    assert not report["media_rendered"] and not report["full_export_verified"]


def test_runner_rejects_invalid_review_ranges_without_creating_outputs(tmp_path):
    output = tmp_path / "unexpected.mp4"
    result = subprocess.run(
        [sys.executable, str(EXAMPLE / "render.py"), "--range", "14", "16", "--output", str(output)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0 and "--range must satisfy" in result.stderr
    assert not output.exists()
