"""Native styled packets follow the live routed geometry without sampled overlays."""

import json
import math
from itertools import pairwise
from pathlib import Path

import pytest

from faceless_champ import FlowChamp, FlowEdge, FlowGraph, FlowNode, FlowPort, FlowScript, FlowTheme


def network():
    ports = (FlowPort("center", "center"), FlowPort("left", "left"), FlowPort("right", "right"))
    return FlowGraph(
        (
            FlowNode("a", position=(150, 220), size=(90, 80), ports=ports),
            FlowNode("b", position=(380, 160), size=(90, 80), ports=ports),
            FlowNode("c", position=(650, 260), size=(90, 80), ports=ports),
        ),
        (
            FlowEdge("ab", "a", "b", "right", "center", route="bezier", arrows="none"),
            FlowEdge("bc", "b", "c", "center", "left", route="bezier", arrows="none"),
        ),
        layout="manual",
    )


def distance_to_path(point, path):
    result = math.inf
    for a, b in pairwise(path):
        dx, dy = b[0] - a[0], b[1] - a[1]
        square = dx * dx + dy * dy
        p = min(1, max(0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / square)) if square else 0
        result = min(result, math.dist(point, (a[0] + p * dx, a[1] + p * dy)))
    return result


@pytest.mark.parametrize("direction", ["forward", "reverse"])
def test_native_capsule_tracks_moving_rotated_scaled_nodes_and_random_seeks(direction):
    script = FlowScript().signal(["ab", "bc"], at=0, duration=4, marker="capsule", direction=direction)
    script.move("b", (430, 290), at=0, duration=4).rotate("b", 25, at=0, duration=4)
    script.scale("b", 1.25, at=0, duration=4)
    clip = FlowChamp(network(), script, width=800, height=480)
    for time in (3.9, 0, 2, 0.25, 3.25, 1):
        snapshot = clip.state_at(time)
        assert len(snapshot["signals"]) == 1
        packet = snapshot["signals"][0]
        assert packet["marker"] == "capsule"
        assert distance_to_path(packet["position"], snapshot["elements"][packet["edge"]]["path"]) < 1e-7
        assert snapshot["elements"]["ab"]["path"][-1] == snapshot["elements"]["bc"]["path"][0]
    assert clip.state_at(4)["signals"] == []
    assert clip.state_at(0) == FlowChamp(network(), script, width=800, height=480).state_at(0)


def test_capsule_serialization_schema_and_source_offset():
    script = FlowScript().signal(["ab", "bc"], at=0.5, duration=3, marker="capsule", repeat=2)
    clip = FlowChamp(network(), script, width=800, height=480, source_start=1)
    restored = FlowChamp.from_dict(json.loads(json.dumps(clip.to_dict())))
    assert restored.to_dict() == clip.to_dict()
    assert restored.frame_image(0, 0.5).tobytes() == clip.frame_image(0, 0.5).tobytes()
    schema = json.loads((Path(__file__).parents[1] / "src/faceless_champ/flow/schema.json").read_text())
    assert '"capsule"' in json.dumps(schema)


def test_capsule_sprite_opacity_isolated_from_cache_and_reserves_shadow_bounds():
    from faceless_champ.flow.drawing import capsule_sprite

    opaque = capsule_sprite("#2563EB", 1).copy()
    assert opaque.size == (54, 42)
    assert opaque.getpixel((27, 24))[3] > 200
    assert opaque.getpixel((0, 0))[3] == 0
    assert capsule_sprite("#2563EB00", 1).getbbox() is None
    script = FlowScript().signal("ab", at=0, duration=2, marker="capsule")
    theme = FlowTheme(background="#00000000", surface="#00000000", stroke="#00000000")
    clip = FlowChamp(network(), script, width=800, height=480, theme=theme)
    clip.frame_image(0.5)
    assert capsule_sprite("#2563EB", 1).tobytes() == opaque.tobytes()
    legacy = FlowChamp(network(), FlowScript().signal("ab", marker="packet"), width=800, height=480)
    assert clip.bounds_for("ab").width > legacy.bounds_for("ab").width


@pytest.mark.parametrize("factor", [0.001, 0.01, 0.02, 1 / 36, 0.03, 0.05, 0.1])
def test_capsule_markers_render_at_small_output_scales(factor):
    script = FlowScript().signal("ab", at=0, duration=2, marker="capsule")
    theme = FlowTheme(background="#00000000", surface="#00000000", stroke="#00000000")
    clip = FlowChamp(network(), script, width=800, height=480, theme=theme)
    image = clip.frame_image(0.5, factor=factor)
    assert image.size == (max(1, round(800 * factor)), max(1, round(480 * factor)))
    assert image.getbbox() is not None
    assert clip.frame_image(0.5, factor=factor).tobytes() == image.tobytes()


@pytest.mark.parametrize("marker", ["dot", "packet", "capsule"])
def test_reverse_activation_is_visible_at_exact_start(marker):
    script = FlowScript().signal(["ab", "bc"], at=1, duration=2, marker=marker, direction="reverse")
    clip = FlowChamp(network(), script, width=800, height=480)
    snapshot = clip.state_at(1)
    assert len(snapshot["signals"]) == 1
    assert snapshot["signals"][0]["position"] == snapshot["elements"]["bc"]["path"][-1]
