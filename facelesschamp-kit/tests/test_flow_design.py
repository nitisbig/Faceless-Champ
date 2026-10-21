"""Public layout and timeline contracts for the promoted networking design."""

import pytest
from faceless_champ import Bounds, Canvas, Group
from facelesschamp_kit.diagrams import FlowChamp, FlowEdge, FlowGraph, FlowNode, FlowScript, FlowTheme
from facelesschamp_kit.diagrams import FlowDesign

from facelesschamp_kit import Video, blocks
from facelesschamp_kit.blocks import FlowBackdrop, FlowCanvas, FlowCard, FlowPopup
from facelesschamp_kit.context import BuildContext
from facelesschamp_kit.diagnostics import KitError


def members(root):
    yield root
    if isinstance(root, Group):
        for child in root.children:
            yield from members(child)


def assert_fits(root, bounds):
    box = root.bounds
    assert box.left >= bounds.left - 1e-6
    assert box.top >= bounds.top - 1e-6
    assert box.right <= bounds.right + 1e-6
    assert box.bottom <= bounds.bottom + 1e-6


def graph():
    return FlowGraph(
        (FlowNode("laptop", position=(180, 200)), FlowNode("router", position=(620, 200))),
        (FlowEdge("wifi", "laptop", "router", route="bezier"),),
        layout="manual",
    )


def test_flow_design_blocks_are_publicly_discoverable():
    assert {"FlowBackdrop", "FlowCard", "FlowPopup", "FlowCanvas"} <= set(blocks.__all__)


@pytest.mark.parametrize("canvas", [Canvas(1920, 1080), Canvas(1080, 1920)])
@pytest.mark.parametrize(
    "block",
    [FlowCard("Router", "router"), FlowPopup("TCP", "SYN"), FlowBackdrop()],
)
def test_design_blocks_have_fresh_named_parts_and_fit_allocations(tmp_path, canvas, block):
    ctx = BuildContext(tmp_path, canvas=canvas)
    bounds = Bounds(100, 200, 320, 340)
    first = block.compose(ctx, bounds)
    second = block.compose(ctx, bounds)
    assert not set(members(first.root)) & set(members(second.root))
    assert set(first.children.values()) <= set(members(first.root))
    assert first.children
    assert_fits(first.root, bounds)
    assert first.root.bounds.center == pytest.approx(bounds.center)
    if isinstance(block, FlowBackdrop):
        assert first.children == {"background": first.root}
    else:
        assert first.children == first.root.parts
        assert first.root.scale_x == first.root.scale_y == 1
        assert first.root.scale < 1
        assert set(first.children) == (
            {"surface", "icon", "label"} if isinstance(block, FlowCard) else {"surface", "icon", "kind", "value"}
        )


def test_card_keeps_native_size_in_large_slot_and_optional_content(tmp_path):
    ctx = BuildContext(tmp_path)
    bounds = Bounds(100, 100, 1500, 1000)
    plain = FlowCard("Laptop", "laptop").compose(ctx, bounds)
    detailed = FlowCard(
        "Laptop", "laptop", detail="192.168.1.20", address="example.com", design=FlowDesign.named("networking")
    ).compose(ctx, bounds)
    assert plain.root.scale == detailed.root.scale == 1
    assert "detail" not in plain.children
    assert "address" not in plain.children
    assert "detail" in detailed.children
    assert "address" in detailed.children
    assert set(detailed.children) == {"surface", "icon", "label", "detail", "address"}
    assert detailed.children["detail"].text == "192.168.1.20"
    assert any(getattr(item, "text", None) == "example.com" for item in members(detailed.children["address"]))
    assert plain.root.bounds.center == detailed.root.bounds.center == bounds.center


@pytest.mark.parametrize("detail", [None, "192.168.1.20"])
def test_default_address_card_keeps_artwork_clear_of_text(tmp_path, detail):
    ctx = BuildContext(tmp_path)
    built = FlowCard("Laptop", "laptop", address="example.com", detail=detail).compose(ctx, ctx.bounds)
    artwork = built.children["icon"].bounds
    assert artwork.top > built.children["address"].bounds.bottom
    assert artwork.bottom < (built.children["detail"].bounds.top if detail else built.root.face_bounds.bottom)
    assert_fits(built.root, ctx.bounds)


def test_named_visual_parts_can_receive_kit_animation(tmp_path):
    video = Video(BuildContext(tmp_path))
    segment = video.segment("device", duration=2)
    handle = segment.add(FlowCard("Laptop", "laptop", detail="192.168.1.20"))
    segment.play(handle["detail"], lambda component: component.animate.opacity_to(0.5), at=1, duration=1)
    compiled = video.compile()
    assert compiled.duration == 2
    assert "detail" in compiled.report["segments"][0]["placements"][0]["children"]


@pytest.mark.parametrize("canvas", [Canvas(1920, 1080), Canvas(1080, 1920)])
def test_canvas_design_fits_and_preserves_source_offset(tmp_path, canvas):
    ctx = BuildContext(tmp_path, canvas=canvas)
    script = FlowScript().move("router", (700, 240), at=1, duration=2)
    block = FlowCanvas(graph(), script, viewport=(800, 400), source_start=1, design="networking")
    first = block.compose(ctx, ctx.bounds)
    second = block.compose(ctx, ctx.bounds)
    assert set(first.children) == {"diagram", "glow"}
    assert first.children == first.root.parts
    assert not set(members(first.root)) & set(members(second.root))
    assert_fits(first.root, ctx.bounds)
    assert first.root.bounds.center == pytest.approx(ctx.bounds.center)
    clips = [item for item in members(first.root) if isinstance(item, FlowChamp)]
    assert len(clips) == 2
    for clip in clips:
        assert clip.source_start == 1
        assert clip.duration == 3
        assert clip.state_at(2)["elements"]["router"]["position"] == pytest.approx((660, 220))


def test_canvas_legacy_positional_contract_is_unchanged(tmp_path):
    ctx = BuildContext(tmp_path)
    theme = FlowTheme(accent="#C15F3C")
    script = FlowScript().reveal("laptop", duration=2)
    built = FlowCanvas(graph(), script, theme, (800, 400), 1).compose(ctx, ctx.bounds)
    assert isinstance(built.root, FlowChamp)
    assert built.children == {"diagram": built.root}
    assert built.root.theme == theme
    assert built.root.source_start == 1


def test_designed_canvas_rejects_conflicting_explicit_theme(tmp_path):
    ctx = BuildContext(tmp_path)
    with pytest.raises(ValueError, match="either theme or design"):
        FlowCanvas(graph(), theme=FlowTheme(), design="networking").compose(ctx, ctx.bounds)


def test_signal_tail_keeps_both_layers_seekable(tmp_path):
    ctx = BuildContext(tmp_path)
    script = FlowScript().signal("wifi", at=1, duration=3, marker="capsule")
    built = FlowCanvas(graph(), script, viewport=(800, 400), source_start=3, design="networking").compose(
        ctx, ctx.bounds
    )
    assert built.children["diagram"].duration == script.duration
    assert built.children["diagram"].source_start == 3
    assert built.children["glow"].source_start <= built.children["glow"].duration
    assert all(action.kind != "signal" for action in built.children["glow"].script.actions)
    assert any(action.kind == "signal" for action in built.children["diagram"].script.actions)
    video = Video(ctx)
    video.segment("tail", duration=1).add(
        FlowCanvas(graph(), script, viewport=(800, 400), source_start=3, design="networking")
    )
    assert video.compile().duration == 1


def test_designed_canvas_script_lifetime_and_diagnostics_scope(tmp_path):
    overlap = FlowGraph((FlowNode("a", position=(150, 200)), FlowNode("b", position=(550, 200))), layout="manual")
    script = FlowScript().move("b", (150, 200), at=1, duration=2)
    video = Video(BuildContext(tmp_path))
    video.segment("route", start=10, duration=4).add(
        FlowCanvas(overlap, script, viewport=(800, 400), source_start=1, design="networking"),
        at=1,
        duration=2,
    )
    report = video.compile().report
    timed = [item for item in report["diagnostics"] if item["code"] == "FLOW_OVERLAP" and "script_time" in item]
    assert timed
    assert all(item["segment"] == "route" and item["placement"] == "route/block-1" for item in timed)
    assert all(item["source_time"] == 10 + item["script_time"] for item in timed)
    assert all(11 <= item["source_time"] <= 13 for item in timed)

    short = Video(BuildContext(tmp_path))
    short.segment("route", duration=1).add(
        FlowCanvas(overlap, script, viewport=(800, 400), source_start=1, design="networking")
    )
    with pytest.raises(KitError, match="MOTION_WINDOW"):
        short.compile()


@pytest.mark.parametrize("duration", [0, 0.1])
def test_short_and_static_designed_canvas_do_not_extend_placement_lifetime(tmp_path, duration):
    script = FlowScript()
    if duration:
        script.signal("wifi", at=0, duration=duration, marker="capsule")
    video = Video(BuildContext(tmp_path))
    video.segment("short", duration=0.25).add(FlowCanvas(graph(), script, viewport=(800, 400), design="networking"))
    compiled = video.compile()
    assert compiled.duration == 0.25
    clips = [entry.component for entry in compiled.composition.entries if isinstance(entry.component, FlowChamp)]
    assert len(clips) == 2
    assert all(clip.duration <= duration for clip in clips)
