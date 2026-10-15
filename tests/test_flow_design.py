"""Public approved-design behavior and graph/card motion stay in core."""

import json
from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from faceless_champ import (
    Bounds,
    Canvas,
    FlowChamp,
    FlowDataError,
    FlowEdge,
    FlowGraph,
    FlowNode,
    FlowPort,
    FlowScript,
    FlowTheme,
    PillowRenderer,
    Scene,
)
from faceless_champ.flow.design import FlowDesign, FlowVisual


def graph():
    return FlowGraph(
        (
            FlowNode("a", position=(200, 250), size=(180, 200), ports=(FlowPort("right"),)),
            FlowNode("b", position=(650, 250), size=(180, 200), ports=(FlowPort("left", "left"),)),
        ),
        (FlowEdge("ab", "a", "b", "right", "left", route="bezier", arrows="none"),),
        layout="manual",
    )


def test_preset_is_explicit_immutable_and_assets_are_portable(tmp_path, monkeypatch):
    design = FlowDesign.named("networking")
    with pytest.raises(FrozenInstanceError):
        design.name = "changed"
    with pytest.raises(TypeError):
        design.palette["blue"] = "red"
    with pytest.raises(ValueError, match="Unknown flow design"):
        FlowDesign.named("missing")
    monkeypatch.chdir(tmp_path)
    assert len(design.asset_paths) == 8
    assert all(path.is_absolute() and path.is_file() for path in design.asset_paths)
    assert design.icon_path("router") == design.icon_path("router_icon.png") == design.icon_path("router.png")
    with pytest.raises(ValueError, match="Unknown networking icon"):
        design.icon_path("../../router")
    assert design.font.endswith("DMSans[opsz,wght].ttf")
    assert design.backdrop(Bounds(100, 60, 900, 510)).bounds == Bounds(100, 60, 900, 510)


def test_cards_keep_approved_dimensions_pivot_shadow_allocation_and_custom_address():
    design = FlowDesign()
    card = design.node_card(
        "Laptop",
        icon="laptop",
        position=(960, 540),
        size=(400, 430),
        detail="192.168.1.20",
        address="docs.test",
    )
    assert isinstance(card, FlowVisual)
    assert card.face_bounds == Bounds(760, 325, 1160, 755)
    assert card.bounds == Bounds(722, 287, 1198, 793)
    assert card.position == card._origin == (960, 540)
    assert set(card.parts) == {"surface", "label", "address", "icon", "detail"}
    assert card.parts["address"].children[1].text == "docs.test"
    assert card.parts["icon"].bounds.top > card.parts["address"].bounds.bottom
    assert card.parts["icon"].bounds.bottom < card.parts["detail"].bounds.top
    assert card.parts["label"].font_size == 32
    assert not hasattr(card, "training_id")
    assert not hasattr(card, "training_face")
    fresh = design.node_card("Laptop", icon="laptop", size=(400, 430))
    assert "address" not in fresh.parts
    assert fresh.parts["surface"] is not card.parts["surface"]
    with pytest.raises(TypeError):
        card.parts["surface"] = fresh.parts["surface"]
    # Scene snapshots deep-copy ordinary component trees, including named parts.
    copied = deepcopy(card)
    assert copied.parts["surface"] is copied.children[0]
    assert copied.parts["surface"] is not card.parts["surface"]
    scene = Scene(Canvas()).add(card).wait(1)
    assert len(scene.entries) > 1
    card.scale = 0.5
    card.move_to(600, 400)
    assert card.face_bounds == Bounds(500, 292.5, 700, 507.5)
    assert card.bounds.center == (600, 400)


@pytest.mark.parametrize("size", [(240, 260), (400, 430), (240, 200)])
@pytest.mark.parametrize("detail", [None, "192.168.1.20"])
@pytest.mark.parametrize("icon", ["laptop", "router", "internet", "cloud", "server", "dns", "lock_tls", "packet"])
def test_address_card_artwork_fits_between_address_and_detail(size, detail, icon):
    card = FlowDesign().node_card(
        "Laptop", icon=icon, address="example.com", detail=detail, size=size, position=(400, 300)
    )
    artwork = card.parts["icon"].bounds
    assert artwork.top > card.parts["address"].bounds.bottom
    assert artwork.bottom < (card.parts["detail"].bounds.top if detail else card.face_bounds.bottom)
    assert artwork.left >= card.face_bounds.left
    assert artwork.right <= card.face_bounds.right


@pytest.mark.parametrize("detail", [None, "192.168.1.20"])
def test_default_address_card_artwork_does_not_paint_over_text(detail):
    card = FlowDesign().node_card("Laptop", icon="laptop", address="example.com", detail=detail, position=(240, 240))
    canvas = Canvas(480, 480)
    with PillowRenderer(2) as renderer:
        full = renderer.frame(Scene(canvas).add(card), 0, (480, 480))
        card.parts["icon"].opacity = 0
        without_artwork = renderer.frame(Scene(canvas).add(card), 0, (480, 480))
    for name in ("label", "address", "detail") if detail else ("label", "address"):
        box = card.parts[name].bounds
        region = (int(box.left), int(box.top), int(box.right), int(box.bottom))
        assert full.crop(region).tobytes() == without_artwork.crop(region).tobytes()
    assert full.tobytes() != without_artwork.tobytes()


def test_popup_compact_card_packet_and_background_share_the_approved_design():
    design = FlowDesign()
    compact = design.node_card("DNS", icon="dns", position=(600, 300), size=(260, 180), detail="resolver")
    assert compact.parts["label"].position == (650, 274)
    assert compact.parts["icon"].position == (527, 303)
    assert compact.bounds == Bounds(432, 172, 768, 428)
    popup = design.popup("tls", "HTTPS :443", position=(900, 300))
    assert popup.face_bounds == Bounds(630, 222, 1170, 378)
    assert popup.bounds == Bounds(592, 184, 1208, 416)
    assert popup.parts["kind"].children[1].color == design.palette["teal"]
    assert popup.parts["value"].text == "HTTPS :443"
    packet = design.packet_marker((80, 90), design.palette["violet"])
    assert packet.face_bounds == Bounds(65, 81, 95, 99)
    assert packet.bounds == Bounds(53, 69, 107, 111)
    assert packet.parts["highlight"].corner_radius == 1.5
    assert design.backdrop().bounds == Bounds(0, 0, 1920, 1080)


def test_proxy_and_card_share_motion_samples_at_boundaries_and_arbitrary_seek_order():
    design = FlowDesign()
    frames = design.move_frames((200, 250), (350, 360), source_scale=1, destination_scale=0.75, duration=2.35)
    script = FlowScript()
    assert design.apply_transform(script, "a", frames, at=0.5, duration=2.35) is script
    probe = FlowChamp(graph(), script, width=900, height=600)
    card = design.node_card("Laptop", icon="laptop", position=(200, 250), size=(180, 200))
    scene = Scene(Canvas())
    with scene.at(0.5):
        scene.play(design.transform_animation(card, frames, offset=(96, 96)), run_time=2.35)
    entry = next(entry for entry in scene.entries if entry.component.__class__ is FlowVisual)
    saved = probe.state_at(1.3)
    for time in (2.85, 0.5, 1.675, 0.73, 1.3):
        state = probe.state_at(time)["elements"]["a"]
        visual = entry.state_at(time)
        assert visual["position"] == pytest.approx(tuple(p + 96 for p in state["position"]))
        assert visual["scale"] == pytest.approx(state["scale"])
    assert saved == probe.state_at(1.3)
    pop = design.pop_frames((300, 400), scale=1.18, duration=1.1)
    assert pop[0] == (0, (300, 422), 1.18 * 0.9)
    assert pop[-1] == (1, (300, 400), 1.18)
    assert max(frame[2] for frame in pop) > 1.18
    assert min(frame[1][1] for frame in pop) < 400
    assert len(pop) == 34


@pytest.mark.parametrize(
    "frames",
    [
        (),
        ((0, (0, 0), 1),),
        ((0, (0, 0), 1), (0.4, (1, 1), 1)),
        ((0, (0, 0), 1), (1, (float("nan"), 1), 1)),
        ((0, (0, 0), 1), (0.8, (1, 1), 1), (0.5, (2, 2), 1), (1, (3, 3), 1)),
    ],
)
def test_invalid_motion_never_partly_mutates_the_script(frames):
    script = FlowScript().reveal("a", at=0, duration=0.5)
    original = script.to_dict()
    with pytest.raises(ValueError):
        FlowDesign().apply_transform(script, "a", frames, at=1, duration=2)
    assert script.to_dict() == original


def test_overlap_validation_is_atomic_and_finite_input_is_required():
    design = FlowDesign()
    script = FlowScript().move("a", (300, 400), at=1, duration=1)
    original = script.to_dict()
    with pytest.raises(ValueError, match="overlapping move"):
        design.apply_transform(script, "a", design.move_frames((200, 250), (350, 360)), at=0.5, duration=2)
    assert script.to_dict() == original
    with pytest.raises(ValueError, match="finite"):
        design.pop_frames((0, 0), duration=float("inf"))
    with pytest.raises(ValueError, match="positive"):
        design.move_frames((0, 0), (100, 100), duration=0)
    with pytest.raises(ValueError, match="finite"):
        design.node_card("Router", icon="router", position=(float("nan"), 0))
    with pytest.raises(ValueError, match="size"):
        design.node_card("Router", icon="router", size=(20, 20))
    with pytest.raises(TypeError, match="address"):
        design.node_card("Laptop", icon="laptop", address=42)
    with pytest.raises(ValueError, match="no space for artwork"):
        design.node_card("Laptop", icon="laptop", address="example.com", detail="192.168.1.20", size=(240, 150))


def test_bound_connection_layers_are_fresh_and_follow_moving_ports():
    design = FlowDesign()
    script = FlowScript().move("a", (330, 400), at=0, duration=2)
    script.highlight("ab", color=design.palette["wire"], at=0, duration=4)
    script.signal("ab", at=2, duration=2)
    first = design.connections(graph(), script, width=900, height=600, source_start=1, position=(1000, 500), scale=0.5)
    second = design.connections(graph(), script, width=900, height=600)
    assert set(first.parts) == {"glow", "diagram"}
    assert first.parts["diagram"] is not second.parts["diagram"]
    assert first.parts["diagram"].source_start == first.parts["glow"].source_start == 1
    assert first.face_bounds == Bounds(775, 350, 1225, 650)
    assert first.bounds == first.face_bounds
    assert first.parts["glow"].opacity == 0.11
    assert first.parts["diagram"].theme.stroke_width == 4.5
    assert first.parts["glow"].theme.stroke_width == 18
    assert first.parts["glow"].state_at(2.5)["signals"] == []
    assert first.parts["diagram"].state_at(2.5)["signals"]
    paths = [first.parts["diagram"].state_at(time)["elements"]["ab"]["path"] for time in (0, 1, 2)]
    assert len({tuple(path) for path in paths}) == 3
    assert paths[-1][0] == (420, 400)


def test_source_offset_in_signal_only_tail_is_valid_for_both_layers():
    script = FlowScript().signal("ab", at=0, duration=4)
    result = FlowDesign().connections(graph(), script, source_start=3)
    assert result.parts["diagram"].source_start == 3
    assert result.parts["glow"].state_at(3)["signals"] == []


def test_native_traffic_focus_fades_and_neutral_gaps_are_atomic_and_idempotent():
    design = FlowDesign()
    script = FlowScript()
    design.signal(script, "ab", at=1, duration=2, direction="reverse")
    assert next(a for a in script.actions if a.kind == "signal").options["marker"] == "capsule"
    assert next(a for a in script.actions if a.kind == "signal").options["color"] == design.palette["teal"]
    design.complete_connections(script, graph().edges, 4)
    complete = script.to_dict()
    design.complete_connections(script, ["ab"], 4)
    assert script.to_dict() == complete
    clip = design.connections(graph(), script, width=900, height=600).parts["diagram"]
    for time in (0, 0.9, 1, 1.1, 2, 2.9, 3, 3.9):
        highlights = [h for h in clip.state_at(time)["highlights"] if "ab" in h["targets"]]
        assert len(highlights) == 1
        if time < 1 or time >= 3:
            assert highlights[0]["color"] == design.palette["wire"]
    assert len(clip.state_at(1)["signals"]) == 1
    assert clip.state_at(2)["highlights"][-1]["color"] == design.palette["teal"]
    original = script.to_dict()
    with pytest.raises(ValueError, match="overlapping"):
        design.signal(script, "ab", at=1.5, duration=1)
    assert script.to_dict() == original
    with pytest.raises(ValueError):
        design.signal(script, "ab", at=5, color="")
    assert script.to_dict() == original
    with pytest.raises(ValueError, match="include"):
        design.complete_connections(script, ["ab"], 1)
    assert script.to_dict() == original


def test_connections_supply_visible_neutral_cables_without_mutating_source_script():
    design = FlowDesign()
    script = FlowScript().signal("ab", at=0, duration=0.1, marker="capsule")
    original = script.to_dict()
    first = design.connections(graph(), script)
    assert script.to_dict() == original
    assert first.parts["diagram"].theme.stroke == design.palette["wire"]
    assert first.parts["diagram"].theme.node_stroke == "#00000000"
    assert first.parts["diagram"].script.to_dict() == original
    assert first.parts["diagram"].theme.highlight_width == 0
    assert design.connections(graph()).parts["diagram"].state_at(0)["highlights"] == []
    short = FlowScript()
    design.signal(short, "ab", at=0, duration=0.05, color="red")
    assert short.duration == pytest.approx(0.05)
    assert all(a.duration > 0 for a in short.actions)


def simple_graph(symbol="rounded_rectangle"):
    return FlowGraph(
        (
            FlowNode("a", symbol=symbol, position=(40, 50), size=(30, 40), ports=(FlowPort("right"),)),
            FlowNode("b", symbol=symbol, position=(160, 50), size=(30, 40), ports=(FlowPort("left", "left"),)),
        ),
        (FlowEdge("ab", "a", "b", "right", "left", route="straight", arrows="none"),),
        layout="manual",
    )


def test_node_stroke_hides_proxy_borders_and_junction_fill_without_hiding_edges():
    theme = FlowTheme(
        background="#00000000",
        surface="#00000000",
        foreground="#00000000",
        stroke="#BBC9E0",
        node_stroke="#00000000",
        stroke_width=4.5,
        highlight_width=0,
    )
    clip = FlowChamp(simple_graph(), theme=theme, width=200, height=100)
    image = clip.frame_image(0)
    assert image.getpixel((100, 50)) == (187, 201, 224, 255)
    assert image.getpixel((40, 30))[3] == 0
    assert image.getpixel((40, 50))[3] == 0
    junction = FlowChamp(simple_graph("junction"), theme=theme, width=200, height=100)
    assert junction.frame_image(0).getpixel((40, 50))[3] == 0
    legacy = FlowChamp(
        simple_graph("junction"),
        theme=FlowTheme(
            background="#00000000",
            surface="#00000000",
            stroke="#BBC9E0",
            stroke_width=4.5,
        ),
        width=200,
        height=100,
    )
    assert legacy.frame_image(0).getpixel((40, 50)) == (187, 201, 224, 255)
    active = FlowChamp(
        simple_graph(),
        FlowScript().highlight("a", at=0, duration=1, color="#2563EB"),
        theme=theme,
        width=200,
        height=100,
    )
    assert active.frame_image(0.5).getpixel((40, 30)) == (37, 99, 235, 255)


@pytest.mark.parametrize("duration", [0, 0.05, 2])
def test_neutral_cables_remain_visible_at_exact_end_and_static_or_short_holds(duration):
    design = FlowDesign()
    script = FlowScript()
    if duration:
        design.signal(script, "ab", at=0, duration=duration)
    original = script.to_dict()
    clip = design.connections(simple_graph(), script, width=200, height=100).parts["diagram"]
    for age in (duration, duration + 0.5, duration + 10):
        image = clip.frame_image(age)
        assert image.getpixel((100, 50)) == (187, 201, 224, 255)
        assert image.getpixel((40, 30))[3] == 0
        assert image.getpixel((40, 50))[3] == 0
    assert clip.duration == duration
    assert script.to_dict() == original


def test_highlight_width_zero_preserves_color_highlight_without_thickening():
    theme = FlowTheme(
        background="#00000000",
        surface="#00000000",
        stroke="#BBC9E0",
        node_stroke="#00000000",
        stroke_width=4.5,
        highlight_width=0,
    )
    script = FlowScript().highlight("ab", at=0, duration=1, color="#2563EB")
    clip = FlowChamp(simple_graph(), script, theme=theme, width=200, height=100)
    active, neutral = clip.frame_image(0.5), clip.frame_image(1)
    assert active.getpixel((100, 50)) == (37, 99, 235, 255)
    assert neutral.getpixel((100, 50)) == (187, 201, 224, 255)
    assert [active.getpixel((100, y))[3] for y in range(100)] == [neutral.getpixel((100, y))[3] for y in range(100)]


def test_independent_node_stroke_and_highlight_width_roundtrip_schema_and_legacy_defaults():
    theme = FlowTheme(stroke="#BBC9E0", node_stroke="#00000000", highlight_width=0)
    clip = FlowChamp(simple_graph(), theme=theme, width=200, height=100)
    document = clip.to_dict()
    assert FlowChamp.from_dict(document).theme == theme
    assert document["theme"]["node_stroke"] == "#00000000"
    assert document["theme"]["highlight_width"] == 0
    from faceless_champ import flow

    properties = json.loads((Path(flow.__file__).parent / "schema.json").read_text())["$defs"]["theme"]["properties"]
    assert properties["highlight_width"] == {"type": "number", "minimum": 0}
    assert properties["node_stroke"]["type"] == ["string", "null"]
    script = FlowScript().highlight("ab", at=0, duration=1, color="#2563EB")
    legacy = FlowChamp(simple_graph(), script, theme=FlowTheme(stroke="#BBC9E0"), width=200, height=100)
    explicit = FlowChamp(
        simple_graph(),
        script,
        theme=FlowTheme(stroke="#BBC9E0", node_stroke="#BBC9E0", highlight_width=2),
        width=200,
        height=100,
    )
    backward_document = legacy.to_dict()
    backward_document["theme"].pop("node_stroke")
    backward_document["theme"].pop("highlight_width")
    backward = FlowChamp.from_dict(backward_document)
    for time in (0, 0.5, 1):
        for factor in (0.25, 1, 2):
            assert legacy.frame_image(time, factor).tobytes() == explicit.frame_image(time, factor).tobytes()
            assert legacy.frame_image(time, factor).tobytes() == backward.frame_image(time, factor).tobytes()


@pytest.mark.parametrize("width", [-1, float("inf"), float("nan"), "2", True])
def test_highlight_width_requires_a_nonnegative_finite_number(width):
    with pytest.raises(FlowDataError, match="theme.highlight_width"):
        FlowTheme(highlight_width=width)


def test_node_stroke_requires_a_color_or_none():
    with pytest.raises(FlowDataError, match="theme.node_stroke"):
        FlowTheme(node_stroke="invalid")


def test_wide_highlights_reserve_bounds_and_avoid_element_layer_clipping():
    script = FlowScript().highlight("ab", at=0, duration=1, color="#2563EB")
    theme = FlowTheme(background="#00000000", surface="#00000000", node_stroke="#00000000", highlight_width=40)
    clip = FlowChamp(simple_graph(), script, theme=theme, width=200, height=100)
    image = clip.frame_image(0.5)
    assert image.getpixel((100, 31))[3] == 255
    assert image.getpixel((100, 69))[3] == 255
    bounds = clip.bounds_for("ab", 0.5)
    assert bounds.top < 30 and bounds.bottom > 70
