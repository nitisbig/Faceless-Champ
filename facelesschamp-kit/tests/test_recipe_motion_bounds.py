from dataclasses import replace

import pytest
from faceless_champ import Canvas

from facelesschamp_kit import BuildContext, Video
from facelesschamp_kit.recipes import apply_recipe
from facelesschamp_kit.themes import CLEAN_FLOW


def assert_inside(box, outer):
    assert box["left"] >= outer.left - 1
    assert box["top"] >= outer.top - 1
    assert box["right"] <= outer.right + 1
    assert box["bottom"] <= outer.bottom + 1


@pytest.mark.parametrize("size", [(1920, 1080), (1080, 1920)])
@pytest.mark.parametrize(
    "recipe,content",
    [
        ("process-flow", {"steps": ["Collect", "Transform", "Deliver"]}),
        ("before-after", {"before": "Ad hoc choices", "after": "Purposeful visual relationships"}),
    ],
)
def test_default_clean_flow_recipe_reserves_motion_inside_safe_bounds(tmp_path, size, recipe, content):
    context = BuildContext(tmp_path, Canvas(*size), CLEAN_FLOW)
    video = Video(context)
    apply_recipe(video.segment("demo", duration=4), recipe, content)
    compiled = video.compile()
    for time in [i / 30 for i in range(120)]:
        for placement in compiled.layout_at(time)["placements"]:
            assert_inside(placement["bounds"], context.bounds)
            for bounds in placement["children"].values():
                assert_inside(bounds, context.bounds)


def test_explicit_recipe_bounds_remain_exact_while_default_bounds_reserve_travel(tmp_path):
    context = BuildContext(tmp_path, Canvas(1920, 1080), CLEAN_FLOW)
    video = Video(context)
    apply_recipe(
        video.segment("authored", duration=4),
        "process-flow",
        {"steps": ["A", "B"]},
        bounds=context.bounds,
    )
    compiled = video.compile()
    initial = compiled.layout_at(0)["placements"][0]["bounds"]
    assert initial["top"] == context.bounds.top
    final = compiled.layout_at(3.999)["placements"][0]["bounds"]
    assert final["top"] < context.bounds.top - context.theme.motion_distance + 1


def test_non_flow_theme_does_not_lose_default_recipe_space(tmp_path):
    context = BuildContext(tmp_path, Canvas(1920, 1080), replace(CLEAN_FLOW, default_exit="fade"))
    video = Video(context)
    apply_recipe(video.segment("demo", duration=4), "process-flow", {"steps": ["A", "B"]})
    initial = video.compile().layout_at(0)["placements"][0]["bounds"]
    assert initial["top"] == context.bounds.top
    assert initial["bottom"] == context.bounds.bottom
