from dataclasses import replace

import pytest
from faceless_champ import (
    Bounds,
    Canvas,
    ChessScript,
    Circle,
    CodeCheckpoint,
    Group,
    Image,
    PlaygroundScript,
    Text,
    prepare_playground,
)

from facelesschamp_kit import CLEAN_FLOW, BuildContext, KitError, Video
from facelesschamp_kit.blocks import ChessBoard, CodeEditor, CodingPlayground, Heading, OSWalkthrough, TextPanel
from facelesschamp_kit.cli import CATALOG
from facelesschamp_kit.themes import LIGHT, MIDNIGHT, THEMES, WHITEBOARD


def context(tmp_path, theme=CLEAN_FLOW):
    return BuildContext(tmp_path, Canvas(1920, 1080, theme.background), theme)


def nested(ctx, bounds):
    x, y = bounds.center
    return Group(
        Circle(20, fill="red", position=(x - 100, y), opacity=0.35),
        Group(Circle(20, fill="blue", position=(x, y)), Circle(20, fill="green", position=(x + 100, y))),
    )


def leaves(scene):
    return [e for e in scene.entries if isinstance(e.component, Circle)]


def test_registered_theme_and_variable_heading(tmp_path):
    assert THEMES["clean-flow"] is CLEAN_FLOW
    assert "clean-flow" in CATALOG["themes"]
    heading = Heading("Clean flow").compose(context(tmp_path), Bounds(100, 100, 1500, 300)).root
    assert isinstance(heading, Text)
    assert heading.font_weight == 700
    panel = TextPanel("Readable body", "Title").compose(context(tmp_path), Bounds(100, 300, 1500, 900))
    assert isinstance(panel.children["background"], Image)
    assert panel.children["text"].font_weight == 400
    assert panel.children["title"].font_weight == 700
    assert panel.children["background"].bounds.left >= 100
    assert panel.children["text"].bounds.left >= 160


@pytest.mark.parametrize("theme", [MIDNIGHT, LIGHT, WHITEBOARD])
def test_existing_themes_stay_static_by_default(tmp_path, theme):
    video = Video(context(tmp_path, theme))
    video.segment("one", duration=1).add_core(nested)
    scene = video.compile().composition
    assert all(not e.tracks for e in scene.entries)
    assert not any(isinstance(e.component, Image) for e in scene.entries)


def test_nested_motion_hides_then_restores_authored_layout(tmp_path):
    video = Video(context(tmp_path))
    video.segment("one", start=2, duration=3).add_core(nested)
    compiled = video.compile()
    entries = leaves(compiled.composition)
    assert len(entries) == 3
    assert entries[1].state_at(2)["opacity"] == 0
    assert entries[2].state_at(2.04)["opacity"] == 0
    for entry, x, opacity in zip(entries, (860, 960, 1060), (0.35, 1, 1), strict=True):
        assert entry.state_at(2.6)["position"] == pytest.approx((x, 540))
        assert entry.state_at(2.6)["opacity"] == pytest.approx(opacity)
        assert entry.state_at(5)["opacity"] == pytest.approx(0)
    assert compiled.report["segments"][0]["placements"][0]["exit"] == "flow"


def test_outro_uses_position_after_custom_move(tmp_path):
    video = Video(context(tmp_path))
    segment = video.segment("one", duration=3)
    handle = segment.add(Heading("Moving"))
    segment.play(handle, lambda c: c.animate.move_to(1100, 600), at=1, duration=0.5)
    scene = video.compile().composition
    entry = next(e for e in scene.entries if isinstance(e.component, Text))
    assert entry.state_at(2.4)["position"] == pytest.approx((1100, 600))
    assert entry.state_at(3)["position"] == pytest.approx((1100, 576))


def test_none_disables_motion_and_overrides_preserve_conflict_checks(tmp_path):
    video = Video(context(tmp_path))
    video.segment("off", duration=0.2).add_core(nested, enter=None, exit=None)
    assert all(not e.tracks for e in leaves(video.compile().composition))
    video = Video(context(tmp_path))
    segment = video.segment("conflict", duration=2)
    handle = segment.add(Heading("Overlapping"))
    segment.play(handle, lambda c: c.animate.opacity_to(0.5), at=0.2, duration=1)
    with pytest.raises(KitError, match="TIMELINE"):
        video.compile()


def test_automatic_windows_cannot_overlap_or_exceed_lifetime(tmp_path):
    video = Video(context(tmp_path))
    video.segment("short", duration=1).add(Heading("Too short"))
    with pytest.raises(KitError, match="MOTION_WINDOW"):
        video.compile()
    video = Video(context(tmp_path))
    video.segment("delayed", duration=3).add(Heading("Too late"), at=2, duration=0.9)
    with pytest.raises(KitError, match="MOTION_WINDOW"):
        video.compile()
    with pytest.raises(KitError, match="MOTION"):
        Video(context(tmp_path)).segment("bad", duration=3).add(Heading("Bad"), exit="pop")


def test_large_stagger_completes_inside_side_window(tmp_path):
    def many(ctx, bounds):
        return Group(*(Circle(2, position=(bounds.center[0] + i * 3, bounds.center[1])) for i in range(40)))

    video = Video(context(tmp_path))
    video.segment("many", duration=2).add_core(many)
    scene = video.compile().composition
    assert all(e.state_at(0.6)["opacity"] == 1 for e in leaves(scene))
    assert all(e.state_at(2)["opacity"] == 0 for e in leaves(scene))


def test_profiles_and_explicit_styles(tmp_path):
    ctx = context(tmp_path)
    box = Bounds(100, 100, 1700, 1000)
    ui = OSWalkthrough().compose(ctx, box).root
    assert ui.preset.accent == CLEAN_FLOW.accent
    assert ui.preset.wallpaper == CLEAN_FLOW.background
    script = PlaygroundScript(
        [CodeCheckpoint("one", {"main.py": "print(1)"}, "main.py", "main.py", 0, 0, 0)], duration=1
    )
    code = CodeEditor(script).compose(ctx, box).root
    assert code.theme.accent == CLEAN_FLOW.accent
    override = CodeEditor(script, theme="paper").compose(ctx, box).root
    assert override.theme.background != code.theme.background
    chess = ChessBoard(
        ChessScript({"schema_version": 1, "duration": 3, "moves": [{"at": 1, "duration": 0.5, "uci": "e2e4"}]})
    ).compose(ctx, box).root
    assert chess.theme.accent == CLEAN_FLOW.accent
    prepared = prepare_playground(script, cache_dir=tmp_path / "prepared")
    panels = CodingPlayground(prepared).compose(ctx, box).children
    assert panels["canvas"].theme.accent == CLEAN_FLOW.accent
    assert panels["output"].theme.background == panels["editor"].theme.background
    override = CodingPlayground(prepared, theme="paper").compose(ctx, box).children
    assert override["canvas"].theme.background == override["editor"].theme.background


def test_background_can_be_disabled_without_changing_theme(tmp_path):
    ctx = context(tmp_path, replace(CLEAN_FLOW, background_pattern=None))
    video = Video(ctx)
    video.segment("one", duration=2).add(Heading("Plain canvas"))
    scene = video.compile().composition
    assert len(scene.entries) == 1


def test_grid_spacing_rejected_before_compilation():
    with pytest.raises(KitError, match="grid_spacing"):
        replace(CLEAN_FLOW, grid_spacing=0.5)
