"""Opt-in native tests; the selected interpreter need not contain FacelessChamp."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from faceless_champ import Canvas, Scene, Viewport, create_renderer, render
from faceless_champ.integrations.manim import ManimRenderOptions, ManimSceneSpec, prepare_manim

pytestmark = [
    pytest.mark.manim,
    pytest.mark.skipif(not os.environ.get("FC_MANIM_PYTHON"), reason="Set FC_MANIM_PYTHON"),
]
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("background", [None, "#172235"])
def test_native_frozen_holds_alpha_clock_and_encoded_export(tmp_path, background):
    spec = ManimSceneSpec(ROOT / "tests/fixtures/manim/basic_scene.py", "GeometryScene")
    source = prepare_manim(
        spec,
        cache_dir=tmp_path / "cache",
        python=os.environ["FC_MANIM_PYTHON"],
        options=ManimRenderOptions(width=320, height=180, fps=12, background=background),
    )
    assert source.frame_count == 24 and source.duration == 2
    if background is None:
        repeated = prepare_manim(
            spec,
            cache_dir=tmp_path / "cache",
            python=os.environ["FC_MANIM_PYTHON"],
            options=ManimRenderOptions(width=320, height=180, fps=12),
            refresh=True,
        )
        assert repeated.fingerprint == source.fingerprint
    session = source.open((320, 180))
    first, final = session.frame(0.1), session.frame(1.9)
    assert first.tobytes() != final.tobytes()
    assert first.getpixel((0, 0))[3] == (0 if background is None else 255)
    if background is None:
        assert any(0 < alpha < 255 for alpha in first.getchannel("A").tobytes())
    assert session.frame(0.1).tobytes() == first.tobytes()
    session.close()
    scene = Scene(Canvas(320, 180, "white")).add(Viewport(source, position=(160, 90))).wait(2)
    with create_renderer("pillow", antialias=1) as renderer:
        image = renderer.frame(scene, 0.1, (320, 180))
        assert image.getpixel((0, 0))[:3] == ((255, 255, 255) if background is None else (23, 34, 53))
    output = render(scene, tmp_path / "example.mp4", width=320, height=180, fps=12, antialias=1, preset="ultrafast")
    info = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-of", "json", str(output)]
        )
    )
    assert info["streams"][0]["nb_read_frames"] == "24"
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(output), "-f", "null", "-"], check=True)
    # Replay in a fresh process with producer engines and subprocess creation blocked.
    code = """
import importlib.abc, subprocess, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'manim','numpy','cairo','manimpango','av','facelesschamp_kit'}:
            raise AssertionError(fullname)
sys.meta_path.insert(0,Block())
subprocess.Popen=lambda *a,**k: (_ for _ in ()).throw(AssertionError('subprocess'))
from faceless_champ import PreparedFrameSource
s=PreparedFrameSource(sys.argv[1]); p=s.open((160,90)); assert p.frame(1).size==(160,90); p.close()
"""
    subprocess.run([sys.executable, "-B", "-c", code, str(source.directory)], check=True)


def test_native_parameters_and_equation_preset(tmp_path):
    from facelesschamp_kit import EquationTransform

    python = os.environ["FC_MANIM_PYTHON"]
    options = ManimRenderOptions(width=640, height=360, fps=15)
    custom = ManimSceneSpec(ROOT / "tests/fixtures/manim/basic_scene.py", "ParameterScene", parameters={"side": 2})
    assert prepare_manim(custom, cache_dir=tmp_path / "custom", python=python, options=options).frame_count == 15
    if not os.environ.get("FC_MANIM_TEX"):
        pytest.skip("Set FC_MANIM_TEX=1 after installing LaTeX/dvisvgm in the worker PATH")
    spec = EquationTransform((r"{{x}}^2+2{{x}}+1", r"({{x}}+1)^2"), transform_time=2, hold_time=1.5).scene_spec()
    source = prepare_manim(spec, cache_dir=tmp_path / "equation", python=python, options=options)
    assert source.frame_count == 90 and source.duration == 6
    session = source.open((640, 360))
    assert session.frame(2).tobytes() != session.frame(5.8).tobytes()
    assert session.frame(6).tobytes() == session.frame(5.99).tobytes()
    reference = json.loads((ROOT / "tests/fixtures/manim/equation-reference.json").read_text())
    for timestamp in reference["samples"]:
        actual = session.frame(timestamp)
        with Image.open(ROOT / f"tests/fixtures/manim/equation-{timestamp}.png") as expected:
            # Tolerate rasterizer/TeX antialiasing differences while catching
            # missing glyphs, changed expressions, color, placement and timing.
            assert actual.size == expected.size
            assert all(abs(a - b) <= 2 for a, b in zip(actual.getbbox(), expected.getbbox(), strict=True))
            difference = ImageChops.difference(actual.convert("RGBa"), expected.convert("RGBa"))
            error = sum((index % 256) * count for index, count in enumerate(difference.histogram()))
            energy = sum(value * count for value, count in enumerate(expected.getchannel("A").histogram()))
            assert error / (4 * energy) < 0.2, f"Visual regression at {timestamp}s"
    session.close()
