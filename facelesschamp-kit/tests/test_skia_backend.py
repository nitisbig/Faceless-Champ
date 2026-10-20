import json
from dataclasses import replace

import pytest
from faceless_champ import Bounds, ShadowStyle, Surface, Text

from facelesschamp_kit import BuildContext, Project
from facelesschamp_kit.blocks import MetricCard, TextPanel
from facelesschamp_kit.scaffold import init_project


def test_theme_native_blocks_use_public_core_descriptions(tmp_path):
    pytest.importorskip("skia")
    context = BuildContext(tmp_path)
    context.theme = replace(context.theme, text_engine="skia", surface_mode="vector", shadow=ShadowStyle(blur=3))
    block = TextPanel("Measured text").compose(context, Bounds(0, 0, 600, 400))
    components = block.root.children
    assert any(isinstance(c, Surface) for c in components)
    assert all(c.text_engine == "skia" for c in components if isinstance(c, Text))


@pytest.mark.parametrize("engine", ["pillow", "skia"])
def test_metric_value_and_label_honor_theme_text_engine(tmp_path, engine):
    if engine == "skia":
        pytest.importorskip("skia")
    context = BuildContext(tmp_path)
    context.theme = replace(context.theme, text_engine=engine)
    block = MetricCard(42, "Answer").compose(context, Bounds(0, 0, 900, 600))
    assert block.children["value"].text_engine == engine
    assert block.children["label"].text_engine == engine


def test_project_backend_applies_to_validation_frame_storyboard_export(tmp_path):
    pytest.importorskip("skia")
    root = init_project(tmp_path / "native")
    config = root / "facelesschamp.toml"
    config.write_text(
        config.read_text()
        .replace('format = "shorts"', 'format = "landscape"')
        .replace("[profiles.preview]", '[profiles.preview]\nbackend="skia"\nwidth=320\nheight=180')
        .replace("[profiles.final]", '[profiles.final]\nbackend="skia"\nwidth=320\nheight=180')
        .replace("fps = 15", "fps = 5")
        .replace("antialias = 2", "antialias = 1")
    )
    project = Project(root)
    report = project.validate()
    assert report["render_backends"]["preview"]["backend"] == "skia"
    project.frame("main", 1, root / "frame.png")
    project.storyboard("main", root / "sheet")
    project.export("main", root / "short.mp4", preview=True, start=0, end=0.2)
    reports = [json.loads(path.read_text()) for path in (root / ".fc-kit/reports").glob("*.json")]
    assert {r["operation"] for r in reports} == {"frame", "storyboard", "preview"}
    assert all(r["rendering"]["backend"] == "skia" for r in reports)
