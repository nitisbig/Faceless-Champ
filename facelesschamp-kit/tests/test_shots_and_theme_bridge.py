import json

import pytest
from faceless_champ import Bounds, Canvas, Text
from faceless_champ.theme import THEMES as CORE_THEMES

from facelesschamp_kit import KitError, shot, shot_video
from facelesschamp_kit.blocks import Comparison, Heading, MetricCard, TextPanel
from facelesschamp_kit.cli import main
from facelesschamp_kit.context import BuildContext
from facelesschamp_kit.layouts import Stack
from facelesschamp_kit.shots import SHOTS, shot_fields
from facelesschamp_kit.themes import THEMES, Theme

CONTENT = {
    "title": {"eyebrow": "Chapter 2", "title": "How networks learn", "subtitle": "Gradients flow backward."},
    "stat": {"value": 98, "suffix": "%", "label": "of requests hit the cache", "context": "Over 30 days."},
    "quote": {"text": "Simplicity is prerequisite for reliability.", "attribution": "Edsger Dijkstra"},
    "steps": {"title": "Training loop", "steps": ["Forward pass", "Measure loss", "Update weights"]},
    "compare": {
        "left_title": "Before",
        "left": "Every request hits disk.",
        "right_title": "After",
        "right": "Hot keys stay in memory.",
    },
    "end": {"title": "Now build your own", "action": "Read the guide"},
}


@pytest.mark.parametrize("name", list(SHOTS))
@pytest.mark.parametrize("theme", ["midnight", "paper", "neon"])
def test_every_shot_renders_and_passes_design_audit(name, theme, tmp_path):
    from faceless_champ import design_audit

    video = shot_video(name, CONTENT[name], theme=theme, duration=3, root=tmp_path)
    assert video.frame(2.5, size=(480, 270)).size == (480, 270)
    report = design_audit(video.composition, samples=3)
    assert report.ok, str(report)


def test_shots_reject_long_copy_and_unknown_fields(tmp_path):
    with pytest.raises(KitError, match="TEXT_BUDGET"):
        shot_video("title", {"title": "A title that is far too long for display use"}, root=tmp_path)
    with pytest.raises(KitError, match="2 to 5"):
        shot("steps", {"steps": ["only one"]})
    with pytest.raises(KitError, match="Unknown fields"):
        shot("stat", {"value": 1, "label": "x", "color": "red"})
    with pytest.raises(KitError, match="Unknown shot"):
        shot("banner", {})
    assert shot_fields("quote") == ["text", "attribution?"]


def test_portrait_shot_and_cli(tmp_path, capsys, monkeypatch):
    video = shot_video("stat", CONTENT["stat"], size=(1080, 1920), root=tmp_path)
    assert video.composition.canvas.height == 1920
    monkeypatch.chdir(tmp_path)
    assert main(["shot", "end", json.dumps(CONTENT["end"]), "--theme", "neon", "--frame", "2"]) == 0
    result = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert result["ok"] and (tmp_path / result["frames"][0]).is_file()
    assert main(["shot", "--list"]) == 0
    assert "stat" in json.loads(capsys.readouterr().out)


def test_kit_theme_bridges_to_core_and_back(tmp_path):
    neon = THEMES["neon"]
    assert neon.accent == CORE_THEMES["neon"].colors.primary and neon.heading_font == "display"
    core = THEMES["clean-flow"].core()
    assert core.colors.primary == THEMES["clean-flow"].accent and core.type_scale.title.font_size == 76
    custom = Theme.from_core("documentary", accent="#FF0000")
    assert custom.accent == "#FF0000" and custom.default_enter == "fade"
    ctx = BuildContext(tmp_path, Canvas(1920, 1080, neon.background), neon)
    heading = Heading("Orbital mechanics").compose(ctx, Bounds(100, 100, 1800, 400)).root
    assert "SpaceGrotesk" in heading.font
    # Core primitives inside a kit placement pick up the kit theme.
    from facelesschamp_kit import Video

    seen = {}

    def factory(ctx, bounds):
        seen["color"] = Text("x", role="label").color
        return Text("Core", role="heading", position=bounds.center)

    video = Video(ctx)
    video.segment("one", duration=1).add_core(factory)
    video.compile()
    assert seen["color"] == neon.accent


def test_blocks_scale_with_canvas_and_stack_weights(tmp_path):
    small = BuildContext(tmp_path, Canvas(1920, 1080))
    large = BuildContext(tmp_path, Canvas(3840, 2160))
    a = MetricCard(42, "projects").compose(small, Bounds(0, 0, 1920, 1080)).root.bounds
    b = MetricCard(42, "projects").compose(large, Bounds(0, 0, 3840, 2160)).root.bounds
    assert b.height == pytest.approx(2 * a.height, rel=0.02)
    built = Stack(TextPanel("Short"), TextPanel("Body"), gap=20, weights=(1, 2)).compose(small, Bounds(0, 0, 1000, 920))
    first, second = built.children["0"].bounds, built.children["1"].bounds
    assert second.height > first.height
    with pytest.raises(KitError, match="one value per block"):
        Stack(TextPanel("a"), weights=(1, 2))
    comparison = Comparison("Old way.", "New way.", left_title="Then", right_title="Now").compose(
        small, Bounds(0, 0, 1800, 700)
    )
    assert {"Then", "Now"} <= {t.text for t in _texts(comparison.root)}


def _texts(component):
    if isinstance(component, Text):
        yield component
    for child in getattr(component, "children", ()):
        yield from _texts(child)
