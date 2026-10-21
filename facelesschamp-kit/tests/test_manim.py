"""Preparation declarations and layout reuse without an installed math engine."""

import subprocess

import pytest
from faceless_champ import Canvas, Scene, create_renderer
from faceless_champ.integrations.manim import ManimRenderOptions, ManimSceneSpec
from faceless_champ.integrations.manim.model import request_record
from faceless_champ.integrations.manim.prepare import _atomic_json
from faceless_champ.prepared import _write_manifest
from PIL import Image

from facelesschamp_kit import BuildContext, EquationTransform, KitError
from facelesschamp_kit.blocks import ManimCanvas


def test_context_prepares_explicitly_tracks_content_and_replays_without_processes(tmp_path, monkeypatch):
    import faceless_champ.integrations.manim as integration

    path = tmp_path / "scene.py"
    path.write_text("# fixture scene\n")
    spec = ManimSceneSpec(path, "Lesson")
    ctx = BuildContext(tmp_path)
    with pytest.raises(KitError) as error:
        ctx.manim(spec)
    assert error.value.code == "MANIM_UNPREPARED"
    calls = []

    def prepare(spec, *, cache_dir, options, python, **limits):
        calls.append(limits)
        key, record = request_record(spec, options, python)
        directory = cache_dir / "assets" / "fixture"
        (directory / "frames").mkdir(parents=True)
        for index, color in enumerate(("red", "blue")):
            Image.new("RGBA", (20, 10), color).save(directory / "frames" / f"{index:08d}.png")
        source = _write_manifest(directory, size=(20, 10), fps="2", provenance={"request": record})
        _atomic_json(cache_dir / "requests" / (key + ".json"), {"request": record, "asset": "assets/fixture"})
        return source

    monkeypatch.setattr(integration, "prepare_manim", prepare)
    ctx.preparing = True
    source = ctx.manim(spec)
    assert len(calls) == 1 and ctx.prepared_assets[-1]["fingerprint"] == source.fingerprint
    ctx.preparing = False
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: pytest.fail("Normal build started a subprocess"))
    assert ctx.manim(spec).fingerprint == source.fingerprint
    path.write_text("# changed scene\n")
    with pytest.raises(KitError) as error:
        ctx.manim(spec)
    assert error.value.code == "MANIM_UNPREPARED"


@pytest.mark.parametrize("size", [(1920, 1080), (1080, 1920)])
def test_manim_canvas_fits_both_formats_and_uses_source_clock(tmp_path, size):
    (tmp_path / "frames").mkdir()
    for index, color in enumerate(("red", "blue")):
        Image.new("RGBA", (20, 10), color).save(tmp_path / "frames" / f"{index:08d}.png")
    source = _write_manifest(tmp_path, size=(20, 10), fps="2", provenance={})
    ctx = BuildContext(tmp_path, Canvas(*size))
    built = ManimCanvas(source, source_start=0.5).compose(ctx, ctx.bounds)
    assert set(built.children) == {"animation"}
    assert built.bounds.left >= ctx.bounds.left and built.bounds.right <= ctx.bounds.right
    scene = Scene(ctx.canvas).add(built.root).wait(2)
    with create_renderer("pillow", antialias=1) as renderer:
        assert renderer.frame(scene, 0, (320, round(320 * size[1] / size[0]))).getpixel(
            (160, round(160 * size[1] / size[0]))
        )[:3] == (0, 0, 255)


def test_equation_preset_is_data_only_and_defaults_are_detached():
    preset = EquationTransform(["{{a}}+{{b}}", "{{b}}+{{a}}"], transform_time=2, hold_time=1.5)
    spec = preset.scene_spec()
    assert spec.source.is_file()
    assert spec.parameters["expressions"] == ["{{a}}+{{b}}", "{{b}}+{{a}}"]
    assert ManimRenderOptions().background is None
    assert 1 + 2 + 2 * 1.5 == 6
    for expressions in (("x",), ("", "x"), "x+y"):
        with pytest.raises((ValueError, TypeError)):
            EquationTransform(expressions)
