from faceless_champ import Bounds, Canvas, Group, Rectangle

from facelesschamp_kit import BuildContext, Video
from facelesschamp_kit.blocks import BlockBuild


def test_layout_exposes_actual_named_ancestry_without_inferring_containment(tmp_path):
    context = BuildContext(tmp_path, Canvas(400, 300), safe_margin=10)
    video = Video(context)

    def custom(ctx, bounds):
        nested = Rectangle(width=40, height=20, position=(100, 100))
        container = Group(nested)
        # A sibling can geometrically contain nested without being its parent.
        sibling = Rectangle(width=100, height=80, position=(100, 100))
        return BlockBuild(Group(container, sibling), {"container": container, "nested": nested, "sibling": sibling})

    video.segment("example", start=0, duration=1).add_core(custom, id="panel", bounds=Bounds(20, 20, 380, 280))
    compiled = video.compile()
    result = compiled.layout_at(0.5)["placements"][0]
    assert result["child_ancestors"] == {"container": [], "nested": ["container"], "sibling": []}
    assert set(result["children"]) == {"container", "nested", "sibling"}
    assert set(result["bounds"]) == {"left", "top", "right", "bottom"}
    result["child_ancestors"]["nested"].append("sibling")
    assert compiled.layout_at(0.5)["placements"][0]["child_ancestors"]["nested"] == ["container"]
