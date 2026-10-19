import json

import pytest
from faceless_champ import Bounds, EffectStack, GPUOptions, OuterGlow, ParticleField, ProceduralBackground

from facelesschamp_kit import BuildContext, EffectBlock, ParticleBackdrop, ProceduralBackdrop, Project
from facelesschamp_kit.blocks import TextPanel
from facelesschamp_kit.scaffold import init_project


def test_gpu_blocks_are_core_descriptions_and_keep_named_children(tmp_path):
    ctx = BuildContext(tmp_path)
    box = Bounds(0, 0, 600, 400)
    built = EffectBlock(TextPanel("GPU composition"), EffectStack(glow=OuterGlow(radius=3))).compose(ctx, box)
    assert built.root.effects.glow.radius == 3
    assert "text" in built.children
    assert isinstance(ProceduralBackdrop().compose(ctx, box).root, ProceduralBackground)
    assert isinstance(ParticleBackdrop(count=40).compose(ctx, box).root, ParticleField)


def test_gpu_profile_nested_options_and_actual_export_provenance(tmp_path):
    pytest.importorskip("moderngl")
    from faceless_champ import renderer_capabilities

    if not renderer_capabilities(probe=True).get("available"):
        pytest.skip("No EGL context")
    root = init_project(tmp_path / "gpu")
    config = root / "facelesschamp.toml"
    text = config.read_text().replace('format = "shorts"', 'format = "landscape"')
    text = text.replace("[profiles.preview]", '[profiles.preview]\nbackend="moderngl"\nwidth=160\nheight=90')
    text += "\n[profiles.preview.gpu]\nworking_mb=64\ntexture_cache_mb=4\n"
    config.write_text(text)
    project = Project(root)
    compiled = project.build()
    assert project.settings(compiled, "preview").gpu == GPUOptions(working_mb=64, texture_cache_mb=4)
    project.frame("main", 1, root / "frame.png")
    project.export("main", root / "preview.mp4", preview=True, start=0, end=0.15)
    records = [json.loads(p.read_text()) for p in (root / ".fc-kit/reports").glob("*.json")]
    assert {r["operation"] for r in records} == {"frame", "preview"}
    assert all(r["rendering"]["backend"] == "moderngl" and r["rendering"]["resolved"] for r in records)
    assert all("shader_hash" in r["rendering"] for r in records)
