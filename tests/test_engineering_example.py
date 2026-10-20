"""Exercise export dimensions without requiring optional CAD construction."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

from faceless_champ import Canvas, Scene


@pytest.mark.parametrize("width", [160, 1920, 3840])
def test_engineering_cli_passes_paired_dimensions(tmp_path, monkeypatch, width):
    source = Path(__file__).resolve().parents[1] / "examples/engineering.py"
    spec = importlib.util.spec_from_file_location("engineering_example", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "build_scene", lambda: Scene(Canvas(1920, 1080)).wait(1))
    calls = []

    def capture(node, output, **options):
        from faceless_champ import ExportSettings

        settings = ExportSettings(width=options["width"], height=options["height"])
        calls.append(settings.dimensions(node.canvas))

    monkeypatch.setattr(module, "render", capture)
    module.main(["--width", str(width), "--output", str(tmp_path / "sample.mp4")])
    assert calls == [(width, width * 9 // 16)]


def test_engineering_cli_short_encode(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "examples/engineering.py"
    spec = importlib.util.spec_from_file_location("engineering_encode", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "build_scene", lambda: Scene(Canvas(1920, 1080, "red")).wait(1))
    output = tmp_path / "sample.mp4"
    module.main(["--width", "160", "--fps", "2", "--seconds", ".5", "--output", str(output)])
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"], check=True)
