"""Standalone base runtime checks, including a separately installed wheel lane.

Set FC_MINIMAL_PYTHON to a fresh venv containing only the candidate wheel and
Pillow. The wheel lane invokes that interpreter with -I from a temporary cwd;
pytest and the source checkout never enter its import path.
"""

import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"


def runtime_probe(directory, fixtures, *, minimal=False):
    """Also executed without pytest inside the isolated wheel interpreter."""
    import array
    import hashlib
    import importlib.abc
    import importlib.metadata
    import math
    import struct
    import wave

    blocked = {
        "manim",
        "cairo",
        "manimpango",
        "av",
        "pyvista",
        "vtk",
        "vtkmodules",
        "numpy",
        "matplotlib",
        "skia",
        "moderngl",
        "glcontext",
        "build123d",
        "OCP",
        "trimesh",
        "scipy",
        "networkx",
        "manifold3d",
        "fast_simplification",
        "chess",
        "pygments",
        "playwright",
        "pydantic",
        "facelesschamp_kit",
        "facelesschamp_agent",
    }

    class Block(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split(".")[0] in blocked:
                raise ImportError("blocked optional dependency: " + fullname)

    sys.meta_path.insert(0, Block())
    import faceless_champ as core

    if minimal:
        installed = {d.metadata["Name"].lower().replace("_", "-") for d in importlib.metadata.distributions()}
        assert installed == {"faceless-champ", "pillow"}, installed
        assert Path(core.__file__).is_relative_to(sys.prefix), core.__file__
    assert set(core.__all__) <= set(dir(core))
    for name in core.__all__:
        getattr(core, name)
    from faceless_champ.integrations.build123d import mesh_from_cad, parts_from_cad
    from faceless_champ.integrations.dependencies import geometry_capabilities
    from faceless_champ.integrations.trimesh import inspect_mesh

    assert geometry_capabilities()["probes"] == {}
    for backend in ("pillow", "skia", "moderngl", "auto"):
        assert not core.renderer_capabilities(backend)["probed"]
    for call, remedy in [
        (lambda: core.ArchCamera(), "faceless-champ[3d]"),
        (lambda: core.ArchMesh(object()), "faceless-champ[3d]"),
        (lambda: core.ArchMesh.from_arrays([(0, 0, 0)]), "faceless-champ[3d]"),
        (lambda: mesh_from_cad(None), "faceless-champ[cad]"),
        (lambda: parts_from_cad(None), "faceless-champ[cad]"),
        (lambda: inspect_mesh(None), "faceless-champ[geometry]"),
        (lambda: core.create_renderer("skia"), "faceless-champ[skia]"),
        (lambda: core.create_renderer("moderngl"), "faceless-champ[gpu]"),
    ]:
        try:
            call()
        except (core.ArchDataError, RuntimeError) as exc:
            assert remedy in str(exc), str(exc)
        else:
            raise AssertionError("explicit optional capability must fail: " + remedy)
    reference = json.loads((fixtures / "m1-v1-reference.json").read_text())
    shape = core.Rectangle(width=60, height=40, stroke=None, position=(80, 60))
    assert list(vars(shape.bounds).values()) == reference["layout"]
    versions = {name: importlib.metadata.version(name) for name in reference["versions"]}
    # Pixels are exact only for the frozen font/Pillow stack. Source suites also
    # test geometry and timing independently across supported Pillow versions.
    compare_pixels = versions == reference["versions"]
    scenes = runpy.run_path(str(fixtures / "minimal_scenes.py"))["scenes"](directory, include_domains=False)
    hashes = {}
    for name, scene in scenes.items():
        with core.PillowRenderer() as renderer:
            renderer.validate(scene)
            for t in (0, 0.35, 1.25, 1.9, 0.35):
                key = f"{name}:{t}"
                frame = renderer.frame(scene, t, (320, 180))
                hashes[key] = hashlib.sha256(frame.tobytes()).hexdigest()
                if compare_pixels:
                    assert hashes[key] == reference["frames"][key], key
    with core.PillowRenderer() as renderer:
        still = core.save_frame(scenes["plain"], 0.35, directory / "still.png", size=(320, 180), renderer=renderer)
    from PIL import Image

    with Image.open(still) as image:
        assert image.size == (320, 180)
        if compare_pixels:
            assert hashlib.sha256(image.convert("RGBA").tobytes()).hexdigest() == reference["frames"]["plain:0.35"]
    tone = directory / "timing.wav"
    with wave.open(str(tone), "wb") as output:
        output.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        output.writeframes(
            b"".join(
                struct.pack(
                    "<h", round(8000 * math.sin(2 * math.pi * 440 * i / 16000)) if 0.4 <= i / 16000 < 1.1 else 0
                )
                for i in range(24000)
            )
        )
    scene = scenes["plain"]
    scene.add_audio(tone, start=0)
    output = core.render(
        scene,
        directory / "range.mp4",
        width=320,
        height=180,
        fps=12,
        start_time=0.25,
        end_time=1.25,
        preset="ultrafast",
    )
    info = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-of", "json", str(output)], text=True
        )
    )
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"], video["r_frame_rate"], video["nb_read_frames"]) == (320, 180, "12/1", "12")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-xerror", "-i", str(output), "-f", "null", "-"], check=True, capture_output=True
    )
    samples = array.array("f")
    samples.frombytes(
        subprocess.check_output(
            ["ffmpeg", "-v", "error", "-i", str(output), "-f", "f32le", "-ac", "1", "-ar", "48000", "pipe:1"]
        )
    )

    def rms(start, end):
        values = samples[int(start * 48000) : int(end * 48000)]
        return math.sqrt(sum(x * x for x in values) / len(values))

    assert rms(0.02, 0.1) < 0.001
    assert rms(0.3, 0.6) > 0.1
    assert rms(0.92, 0.98) < 0.001
    assert not blocked.intersection(sys.modules)
    return {
        "package": core.__file__,
        "fixed_stack_pixels_compared": compare_pixels,
        "frames_checked": len(hashes),
        "export": str(output),
        "video": video,
    }


def run_probe(python, directory, *, minimal):
    code = "import runpy,sys,pathlib,json; m=runpy.run_path(sys.argv[1]); print(json.dumps(m['runtime_probe'](pathlib.Path(sys.argv[2]),pathlib.Path(sys.argv[3]),minimal=sys.argv[4]=='1')))"
    env = {key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "DISPLAY", "WAYLAND_DISPLAY"}}
    result = subprocess.run(
        [
            python,
            "-I",
            "-B",
            "-c",
            code,
            str(Path(__file__).resolve()),
            str(directory),
            str(FIXTURES),
            str(int(minimal)),
        ],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def test_base_runtime_with_optional_imports_blocked(tmp_path):
    result = run_probe(sys.executable, tmp_path, minimal=False)
    assert result["frames_checked"] == 20


def test_clean_base_wheel(tmp_path):
    python = os.environ.get("FC_MINIMAL_PYTHON")
    if not python:
        import pytest

        pytest.skip("Set FC_MINIMAL_PYTHON to a fresh Core+Pillow wheel environment")
    result = run_probe(python, tmp_path, minimal=True)
    assert result["fixed_stack_pixels_compared"]
    help_result = subprocess.run(
        [python, "-I", "-m", "faceless_champ", "--help"], cwd=tmp_path, capture_output=True, text=True, check=False
    )
    assert help_result.returncode == 0, help_result.stderr
    assert "render" in help_result.stdout
