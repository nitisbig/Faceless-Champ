import pytest
from faceless_champ import Bounds, Canvas, Circle, PillowRenderer

from facelesschamp_kit import BuildContext, KitError, Video
from facelesschamp_kit.recipes import apply_recipe, recipe_specs, validate_recipe
from facelesschamp_kit.themes import LIGHT, MIDNIGHT


@pytest.mark.parametrize("spec", [s for s in recipe_specs() if s.id not in {"code-result", "arch-design"}], ids=lambda s: s.id)
@pytest.mark.parametrize("size", [(1920, 1080), (1080, 1920)])
@pytest.mark.parametrize("theme", [MIDNIGHT, LIGHT])
def test_recipe_frames_at_entrance_action_exit(tmp_path, spec, size, theme):
    ctx = BuildContext(tmp_path, Canvas(*size, theme.background), theme)
    video = Video(ctx)
    handles = apply_recipe(video.segment("demo", duration=4), spec.id, spec.example)
    assert set(handles) == set(spec.targets)
    compiled = video.compile()
    renderer = PillowRenderer(1)
    for time in (0, 0.7, 2.2, 3.95):
        image = renderer.frame(compiled.composition, time, (320, 180) if size[0] > size[1] else (180, 320))
        assert image.size == ((320, 180) if size[0] > size[1] else (180, 320))
        assert compiled.layout_at(time)["placements"]


def test_layout_measures_animated_handles_and_lifetimes(tmp_path):
    video = Video(BuildContext(tmp_path))
    segment = video.segment("demo", duration=3)
    handle = segment.add_core(
        lambda ctx, box: Circle(20, stroke=None, stroke_width=0, position=(100, 100)), id="dot", at=0.5, duration=1.5
    )
    segment.play(handle, lambda c: c.animate.move_to(200, 100), at=0.5, duration=1)
    compiled = video.compile()
    assert compiled.layout_at(0)["placements"] == []
    initial = compiled.layout_at(0.5)["placements"][0]["bounds"]["left"]
    moved = compiled.layout_at(1.5)["placements"][0]["bounds"]["left"]
    assert moved - initial == 100
    assert initial <= 80  # Core reserves a conservative antialias fringe.
    assert compiled.layout_at(2)["placements"] == []
    with pytest.raises(KitError, match="SAMPLE_TIME"):
        compiled.layout_at(3)


@pytest.mark.parametrize(
    "recipe,content",
    [
        ("missing", {}),
        ("process-flow", {"steps": ["one"]}),
        ("part-whole", {"parts": {"a": 0, "b": 0}}),
        ("annotated-trend", {"points": [[1, 2], [0, 3]], "label": "L", "annotation": "A"}),
        ("overview-detail", {"steps": ["a", "b"], "focus": True, "detail": "D"}),
        ("hierarchy", {"nodes": [{"id": "a", "label": "A", "parent": "b"}, {"id": "b", "label": "B", "parent": "a"}]}),
    ],
)
def test_invalid_recipe_content(recipe, content):
    with pytest.raises(KitError):
        validate_recipe(recipe, content)


def test_recipe_content_snapshot_events_and_long_text(tmp_path):
    video = Video(BuildContext(tmp_path))
    content = {
        "value": 10,
        "label": "A useful metric",
        "context": "A longer explanation that wraps into its allocated region.",
    }
    handles = apply_recipe(
        video.segment("metric", duration=3),
        "metric-context",
        content,
        events=[{"target": "value", "action": "value", "value": 20, "at": 1, "duration": 1}],
    )
    content["label"] = "changed"
    compiled = video.compile()
    assert "value" in compiled.layout_at(2)["placements"][0]["children"]
    assert handles["value"].child == "value"
    with pytest.raises(KitError):
        apply_recipe(
            video.segment("bad", duration=3),
            "before-after",
            {"before": "A", "after": "B"},
            events=[{"target": "missing", "at": 0}],
        )


def test_impossible_recipe_text_is_an_error(tmp_path):
    video = Video(BuildContext(tmp_path))
    apply_recipe(
        video.segment("demo", duration=3),
        "before-after",
        {"before": "x" * 10000, "after": "B"},
        bounds=Bounds(64, 64, 500, 400),
    )
    with pytest.raises(KitError, match="TEXT_FIT"):
        video.compile()
