"""Geometry, authoring and random-access playback contracts for FlowChamp."""

import json
import math
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

from faceless_champ import (
    Canvas,
    FlowChamp,
    FlowDataError,
    FlowEdge,
    FlowGraph,
    FlowNode,
    FlowPort,
    FlowScript,
    FlowTheme,
    Group,
    PillowRenderer,
    Scene,
)
from faceless_champ.flow.geometry import layers, length, sample
from faceless_champ.flow.model import SYMBOLS


def graph(**kwargs):
    return FlowGraph(
        (
            FlowNode("a", "Input", position=(150, 150), ports=(FlowPort("out"),)),
            FlowNode("b", "Output", position=(450, 150), ports=(FlowPort("in", "left"),)),
        ),
        (FlowEdge("e", "a", "b", "out", "in", **kwargs),),
        layout="manual",
    )


def clip(script=None, **kwargs):
    return FlowChamp(graph(), script, width=600, height=400, **kwargs)


def test_round_trip_and_relative_assets(tmp_path):
    Image.new("RGB", (20, 20), "red").save(tmp_path / "image.png")
    g = FlowGraph((FlowNode("a", "Photo", "image", image="image.png"),))
    s = FlowScript().draw("a", tool="pen").move("a", (200, 180)).highlight("a", dim=0.2)
    data = {"schema_version": 1, "graph": g.to_dict(), "script": s.to_dict()}
    path = tmp_path / "flow.json"
    path.write_text(json.dumps(data))
    a = FlowChamp.from_json(path)
    b = FlowChamp.from_dict(a.to_dict())
    assert a.to_dict() == b.to_dict()
    assert a.frame_image(2.5, 0.2).tobytes() == b.frame_image(2.5, 0.2).tobytes()
    assert a.graph.nodes[0].image == str(tmp_path / "image.png")
    assert FlowScript.from_dict(s.to_dict()).actions == s.actions
    assert FlowGraph.from_dict(g.to_dict()) == g


@pytest.mark.parametrize(
    "mutate,match",
    [
        (lambda d: d.update(extra=True), "unknown field"),
        (lambda d: d.update(schema_version=True), "schema_version"),
        (lambda d: d["graph"]["nodes"].append(d["graph"]["nodes"][0]), "unique"),
        (lambda d: d["graph"]["nodes"][0].update(symbol="unknown"), "graph.nodes"),
        (lambda d: d["graph"]["edges"][0].update(source="missing"), "unknown source"),
        (lambda d: d["graph"]["edges"][0].update(target_port="missing"), "unknown target port"),
        (lambda d: d["graph"]["nodes"][0].update(size=[0, 30]), "positive"),
        (lambda d: d.update(width=float("nan")), "finite"),
    ],
)
def test_validation(mutate, match):
    data = clip().to_dict()
    mutate(data)
    with pytest.raises(FlowDataError, match=match):
        FlowChamp.from_dict(data)


def test_action_validation_and_snapshot():
    with pytest.raises(FlowDataError, match="overlapping"):
        FlowScript().draw("a", at=0, duration=2).hide("a", at=1)
    with pytest.raises(FlowDataError, match="positive integer"):
        FlowScript().signal("e", repeat=0)
    with pytest.raises(FlowDataError, match="requires a node"):
        clip(FlowScript().move("e", (10, 20)))
    with pytest.raises(FlowDataError, match="unknown action"):
        clip(FlowScript().highlight("missing"))
    s = FlowScript().move("a", (200, 200), duration=2).rotate("a", 90, at=0, duration=2)
    c = clip(s)
    s.move("a", (0, 0))
    assert c.state_at(5)["elements"]["a"]["position"] == (200, 200)
    assert c.duration == 2


@pytest.mark.parametrize("layout", ["layered", "grid", "radial", "manual"])
def test_layout_determinism_and_pinned_positions(layout):
    g = replace(graph(), layout=layout)
    assert FlowChamp(g)._positions == FlowChamp(g)._positions == {"a": (150, 150), "b": (450, 150)}
    if layout != "manual":
        g = replace(g, nodes=tuple(replace(n, position=None) for n in g.nodes))
        assert FlowChamp(g)._positions == FlowChamp(g)._positions
    else:
        with pytest.raises(FlowDataError, match="requires every"):
            FlowChamp(FlowGraph((FlowNode("a"),), layout="manual"))


def test_scc_and_disconnected_layout():
    g = FlowGraph(
        tuple(FlowNode(x) for x in "abcd"),
        (FlowEdge("ab", "a", "b"), FlowEdge("ba", "b", "a"), FlowEdge("bc", "b", "c")),
    )
    assert layers(g) == [["a", "b", "d"], ["c"]]
    c = FlowChamp(g)
    assert c._positions["a"][0] == c._positions["b"][0]
    assert c._positions["c"][0] > c._positions["a"][0]


def test_ports_follow_combined_transforms():
    s = FlowScript().move("a", (250, 200), duration=2).rotate("a", 90, at=0, duration=2)
    s.scale("a", 2, at=0, duration=2)
    c = clip(s)
    state = c.state_at(2)["elements"]
    assert state["e"]["path"][0] == pytest.approx((250, 360))
    assert state["e"]["path"][-1] == pytest.approx((370, 150))
    assert c.bounds_for("a", 2).height > c.bounds_for("a", 0).height


@pytest.mark.parametrize("route", ["straight", "orthogonal", "bezier"])
def test_routes_signal_and_pencil_share_geometry(route):
    c = FlowChamp(
        graph(route=route, dashed=True, arrows="both"),
        FlowScript().draw("e", duration=2).signal("e", at=0, duration=2),
        width=600,
        height=400,
    )
    state = c.state_at(1)
    expected = sample(state["elements"]["e"]["path"], 0.5)
    assert state["tools"][0]["position"] == pytest.approx(expected)
    assert state["signals"][0]["position"] == pytest.approx(expected)
    assert length(state["elements"]["e"]["path"]) > 0
    assert c.frame_image(0.5).tobytes() != c.frame_image(1.5).tobytes()


def test_reveal_stagger_and_highlight_lifetime():
    c = clip(FlowScript().reveal(["a", "b"], at=1, duration=1, stagger=0.5).highlight("a", at=3, duration=1, dim=0.2))
    assert c.state_at(0)["elements"]["a"]["opacity"] == 0
    assert c.state_at(1.5)["elements"]["a"]["opacity"] == 0.5
    assert c.state_at(1.5)["elements"]["b"]["opacity"] == 0
    assert c.state_at(3.5)["highlights"][0]["dim"] == 0.2
    assert not c.state_at(4)["highlights"]
    assert c.frame_image(2.9).tobytes() == c.frame_image(4).tobytes()


def test_connected_signal_reverse_repeat_and_discontinuity():
    g = FlowGraph(tuple(FlowNode(x) for x in "abc"), (FlowEdge("ab", "a", "b"), FlowEdge("bc", "b", "c")))
    c = FlowChamp(g, FlowScript().signal(["ab", "bc"], duration=4, direction="reverse", repeat=2))
    assert c.state_at(0)["signals"][0]["edge"] == "bc"
    assert c.state_at(0.25)["signals"] == c.state_at(2.25)["signals"]
    assert not c.state_at(4)["signals"]
    with pytest.raises(FlowDataError, match="connected"):
        FlowChamp(g, FlowScript().signal(["bc", "ab"]))


def test_random_access_cache_source_start_and_scene_transforms():
    s = FlowScript().move("a", (210, 210), duration=2).signal("e", at=0, duration=2)
    c = clip(s, theme=FlowTheme(sketch=True), source_start=0.25, position=(300, 200))
    scene = Scene(Canvas(600, 400))
    group = Group(c)
    scene.add(group)
    scene.play(group.animate.rotate_to(12), run_time=2)
    scene.wait(1)
    cached, plain = PillowRenderer(1), PillowRenderer(1, frame_cache_mb=0)
    expected = {t: plain.frame(scene, t, (300, 200)).tobytes() for t in (0, 0.5, 1, 1.5, 2.5)}
    for t in (1.5, 0, 2.5, 0.5, 1, 1.5):
        assert cached.frame(scene, t, (300, 200)).tobytes() == expected[t]
    assert len(set(expected.values())) == len(expected)
    assert c.frame_image(0).tobytes() == clip(s, theme=FlowTheme(sketch=True)).frame_image(0.25).tobytes()
    assert scene.bounds_at(group, 1).width > 0


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_all_symbols_render(symbol, tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (20, 20), "orange").save(path)
    c = FlowChamp(
        FlowGraph((FlowNode("n", symbol, symbol, size=(200, 100), image=str(path) if symbol == "image" else None),)),
        FlowScript().draw("n", duration=1),
        width=400,
        height=300,
    )
    a, b = c.frame_image(0.3), c.frame_image(1)
    assert a.tobytes() != b.tobytes()
    assert c.bounds_for("n").width >= 200
    assert all(math.isfinite(x) for p in c.paths_for("n", c.state_at(0)["elements"]) for point in p for x in point)


def test_self_loop_and_overlap_diagnostics():
    g = FlowGraph(
        (FlowNode("a", position=(200, 200)), FlowNode("b", position=(210, 200))), (FlowEdge("loop", "a", "a"),)
    )
    c = FlowChamp(g)
    assert any(d["code"] == "FLOW_OVERLAP" for d in c.diagnostics)
    assert length(c.state_at(0)["elements"]["loop"]["path"]) > 0


def test_named_orthogonal_port_leads_and_shape_boundaries():
    g = graph()
    c = FlowChamp(g, FlowScript().rotate("a", 90), width=600, height=400)
    path = c.state_at(1)["elements"]["e"]["path"]
    assert path[1][0] == pytest.approx(path[0][0])
    assert path[1][1] > path[0][1]
    assert path[-2][0] < path[-1][0]
    n = FlowNode("a", symbol="circle", position=(200, 200), size=(100, 100), ports=(FlowPort("corner", "right", 0),))
    g = FlowGraph((n, FlowNode("b", position=(400, 200))), (FlowEdge("e", "a", "b", source_port="corner"),))
    start = FlowChamp(g).state_at(0)["elements"]["e"]["path"][0]
    assert math.dist(start, (200, 200)) == pytest.approx(50)


@pytest.mark.parametrize("field,value", [("nodes", None), ("edges", 4)])
def test_invalid_json_collection_has_path(field, value):
    data = clip().to_dict()
    data["graph"][field] = value
    with pytest.raises(FlowDataError, match=f"graph.{field}"):
        FlowChamp.from_dict(data)


def test_unstarted_symbol_strokes_are_not_drawn():
    # Capacitor's second wire and plates must not appear before the first wire completes.
    c = FlowChamp(
        FlowGraph((FlowNode("c", symbol="capacitor"),)), FlowScript().draw("c", tool="none"), width=400, height=300
    )
    image = c.frame_image(0.05)
    assert image.getpixel((280, 150)) == (11, 18, 32, 255)


def test_exterior_labels_mask_connections():
    g = FlowGraph(
        (FlowNode("client", "Client", "client"), FlowNode("server", "Server", "server")),
        (FlowEdge("wire", "client", "server"),),
        direction="vertical",
    )
    c = FlowChamp(g, width=400, height=600)
    with_wire = c.frame_image(0)
    without_wire = FlowChamp(replace(g, edges=()), width=400, height=600).frame_image(0)
    # Removing edges changes layered positions, so preserve explicit positions for comparison.
    positions = c.state_at(0)["elements"]
    plain = replace(g, edges=(), nodes=tuple(replace(n, position=positions[n.id]["position"]) for n in g.nodes))
    without_wire = FlowChamp(plain, width=400, height=600).frame_image(0)
    x, y = positions["client"]["position"]
    label_y = y + 45 + 20 * 0.9 + 6
    region = (int(x - 8), int(label_y - 3), int(x + 8), int(label_y + 3))
    assert with_wire.crop(region).tobytes() == without_wire.crop(region).tobytes()


def test_neutral_stroke_round_trip_and_legacy_default():
    legacy = clip(theme=FlowTheme(accent="#C15F3C"))
    explicit = clip(theme=FlowTheme(accent="#C15F3C", stroke="#C15F3C"))
    assert legacy.frame_image(0).tobytes() == explicit.frame_image(0).tobytes()
    neutral = clip(FlowScript().highlight("a", at=1), theme=FlowTheme(accent="#C15F3C", stroke="#B1ADA1"))
    assert neutral.frame_image(0).getpixel((70, 150))[:3] == (177, 173, 161)
    assert neutral.frame_image(1.5).getpixel((70, 150))[:3] == (193, 95, 60)
    assert FlowChamp.from_dict(neutral.to_dict()).to_dict() == neutral.to_dict()
    with pytest.raises(FlowDataError, match="theme.stroke"):
        FlowTheme(stroke="invalid")


def test_static_frame_keys_and_transient_boundaries():
    s = FlowScript().reveal("a", at=2, duration=1).highlight("b", at=4, duration=1)
    s.signal("e", at=6, duration=1)
    c = clip(s)
    assert c.frame_key(0.5) == c.frame_key(1.5) == 0
    assert c.frame_key(2.25) != c.frame_key(2.5)
    assert c.frame_key(3.1) == c.frame_key(3.9) == 3
    assert c.frame_key(4.1) == c.frame_key(4.9) == 4
    assert c.frame_key(5) == 5
    assert c.frame_image(4.9).tobytes() != c.frame_image(5).tobytes()
    assert c.frame_key(6.25) != c.frame_key(6.5)
    assert not c.state_at(7)["signals"]
    shifted = clip(s, source_start=3.5)
    assert shifted.frame_image(0.6).tobytes() == c.frame_image(4.1).tobytes()
    scene = Scene(Canvas(600, 400))
    held = clip(s, position=(300, 200))
    scene.add(held).wait(8)
    cached, plain = PillowRenderer(1), PillowRenderer(1, frame_cache_mb=0)
    for t in (4.5, 5, 1.3, 6.4, 4.9, 3.5):
        assert cached.frame(scene, t, (300, 200)).tobytes() == plain.frame(scene, t, (300, 200)).tobytes()


def test_label_cache_budget_and_random_access_parity():
    s = FlowScript().scale("a", 2, duration=1).rotate("a", 40, at=0)
    cached, plain = clip(s, label_cache_mb=0.02), clip(s, label_cache_mb=0)
    for i in (0, 19, 4, 27, 3, 19):
        t = i / 30
        for factor in (0.5, 1, 1.4):
            assert cached.frame_image(t, factor).tobytes() == plain.frame_image(t, factor).tobytes()
            assert cached._label_cache_bytes <= cached._label_cache_limit
    assert not plain._label_cache


def test_visible_diagnostics_moves_labels_and_hidden_targets():
    g = FlowGraph(
        (FlowNode("a", position=(150, 150)), FlowNode("b", position=(450, 150)), FlowNode("c", position=(300, 260))),
        (FlowEdge("e", "a", "b", label="Request"),),
        layout="manual",
    )
    s = FlowScript().move("c", (300, 150), duration=1).hide("c", at=1, duration=1)
    c = FlowChamp(g, s, width=600, height=400)
    assert not c.diagnostics_at(0)
    assert any(d["code"] == "FLOW_LABEL_OVERLAP" and d["elements"] == ["c", "e"] for d in c.diagnostics_at(1))
    assert not c.diagnostics_at(2)
    offscreen = clip(FlowScript().move("a", (20, 150), duration=1).hide("a", at=1))
    assert any(d["code"] == "FLOW_BOUNDS" and d["element"] == "a" for d in offscreen.diagnostics_at(1))
    assert not offscreen.diagnostics_at(2)
    dimmed = clip(FlowScript().move("a", (20, 150), duration=1).highlight("b", at=1, dim=0))
    assert not dimmed.diagnostics_at(1.5)


def test_large_exterior_labels_wrap_and_fit():
    c = FlowChamp(
        FlowGraph((FlowNode("db", "Object storage", "database", size=(210, 130)),)),
        theme=FlowTheme(font_size=38, minimum_font_size=28),
        width=400,
        height=300,
    )
    assert "\n" in c._labels["db"][0]
    assert c.bounds_for("db").bottom > 230
    assert c.frame_image(0).getbbox()


def test_tiny_node_scale_does_not_clip_fixed_pixel_label_padding():
    from faceless_champ.flow.drawing import label_image, rgba

    c = FlowChamp(
        FlowGraph((FlowNode("db", "Object store", "database", position=(150, 150), size=(210, 90)),)),
        FlowScript().scale("db", 0.001),
        width=300,
        height=300,
    )
    expected = label_image(c, "db", 0.001, rgba(c.theme.foreground))
    backing = Image.new("RGBA", (expected.width + 8, expected.height + 4), c.theme.background)
    backing.alpha_composite(expected, (4, 2))
    # The text's minimum raster font is 1px, and backing padding remains fixed pixels.
    left, top = round(150 - backing.width / 2), round(150.069 - backing.height / 2)
    actual = c.frame_image(1).crop((left, top, left + backing.width, top + backing.height))
    assert actual.tobytes() == backing.tobytes()
    assert c.bounds_for("db", 1).width >= backing.width


def test_edge_label_defaults_preserve_positional_constructor_and_legacy_pixels(monkeypatch):
    from faceless_champ.flow import drawing

    edge = FlowEdge("e", "a", "b", "out", "in", "Request", "orthogonal", (), False, "end")
    assert edge.label_position == 0.5 and edge.label_offset == (0, 0)
    c = FlowChamp(replace(graph(), edges=(edge,)), width=600, height=400)
    actual = c.frame_image(0, 0.75).tobytes()
    current = drawing.raster_label

    def legacy_label(clip, id, state, factor):
        sprite, position = current(clip, id, state, factor)
        if id in clip._edges:
            position = tuple(v * factor for v in sample(state["path"], 0.5))
        return sprite, position

    monkeypatch.setattr(drawing, "raster_label", legacy_label)
    assert c.frame_image(0, 0.75).tobytes() == actual


@pytest.mark.parametrize("route", ["straight", "orthogonal", "bezier"])
def test_edge_label_follows_routed_distance_moving_endpoints_and_scaled_offset(route):
    from faceless_champ.flow.drawing import raster_label

    c = FlowChamp(
        graph(route=route, label="Request", label_position=0.25, label_offset=(12, -35)),
        FlowScript().move("b", (470, 250), duration=2),
        width=600,
        height=400,
    )
    centers = []
    for time in (2, 0, 1, 2):
        state = c.state_at(time)["elements"]["e"]
        anchor = sample(state["path"], 0.25)
        _, center = raster_label(c, "e", state, 1.5)
        assert center == pytest.approx(((anchor[0] + 12) * 1.5, (anchor[1] - 35) * 1.5))
        centers.append(center)
        assert c.frame_image(time, 1.5).getbbox()
    assert centers[0] == centers[-1] and centers[0] != centers[1]


@pytest.mark.parametrize("position", [0, 1])
def test_edge_label_endpoints_and_json_roundtrip(position):
    c = FlowChamp(graph(label="Read", label_position=position, label_offset=[5, -30]), width=600, height=400)
    restored = FlowChamp.from_dict(json.loads(json.dumps(c.to_dict())))
    assert restored.graph.edges[0].label_offset == (5, -30)
    assert restored.to_dict() == c.to_dict()
    assert restored.frame_image(0).tobytes() == c.frame_image(0).tobytes()


@pytest.mark.parametrize("value", [-0.1, 1.1, True, float("nan"), float("inf"), "0.5"])
def test_invalid_edge_label_position_has_field_path(value):
    with pytest.raises(FlowDataError, match="e.label_position"):
        FlowEdge("e", "a", "b", label_position=value)


@pytest.mark.parametrize("value", [None, (1,), (1, 2, 3), (0, True), (float("nan"), 0), "0,0"])
def test_invalid_edge_label_offset_has_field_path(value):
    with pytest.raises(FlowDataError, match="e.label_offset"):
        FlowEdge("e", "a", "b", label_offset=value)


def test_edge_label_offset_changes_raster_bounds_and_collision_diagnostics():
    # The normal midpoint label is clear; offsetting it onto node b must report a collision.
    clear = FlowChamp(graph(label="Request", label_offset=(0, -40)), width=600, height=400)
    collision = FlowChamp(graph(label="Request", label_offset=(150, 0)), width=600, height=400)
    assert not any(d["code"] == "FLOW_LABEL_OVERLAP" for d in clear.diagnostics_at(0))
    assert any(d.get("elements") == ["b", "e"] for d in collision.diagnostics_at(0))
    outside = FlowChamp(graph(label="Request", label_offset=(0, -200)), width=600, height=400)
    assert outside.bounds_for("e").top < 0
    assert any(d.get("element") == "e" and d["code"] == "FLOW_BOUNDS" for d in outside.diagnostics_at(0))
    assert clear.frame_image(0).tobytes() != collision.frame_image(0).tobytes()


def test_edge_label_schema_accepts_new_fields_and_legacy_documents():
    schema = json.loads((Path(__file__).parents[1] / "src/faceless_champ/flow/schema.json").read_text())
    edge = schema["$defs"]["edge"]["properties"]
    assert edge["label_position"] == {"type": "number", "minimum": 0, "maximum": 1, "default": 0.5}
    assert edge["label_offset"]["$ref"] == "#/$defs/point"
    point = schema["$defs"]["point"]
    assert point["minItems"] == point["maxItems"] == 2
    assert point["prefixItems"] == [{"type": "number"}, {"type": "number"}]
    assert not {"label_position", "label_offset"} & set(schema["$defs"]["edge"]["required"])
    old = clip().to_dict()
    for item in old["graph"]["edges"]:
        item.pop("label_position")
        item.pop("label_offset")
    assert FlowChamp.from_dict(old).graph.edges[0].label_position == 0.5
