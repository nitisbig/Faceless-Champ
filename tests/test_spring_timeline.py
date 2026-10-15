"""Public spring track integration, continuous geometry safety and atomic authoring."""

import math
from copy import deepcopy
from dataclasses import astuple
from itertools import pairwise

import pytest

import faceless_champ
from faceless_champ import (
    Animation,
    BarChart,
    Canvas,
    Component,
    EarthMap,
    FadeIn,
    Group,
    Number,
    PillowRenderer,
    PopIn,
    ProgressBar,
    Rectangle,
    RectangleMask,
    SatelliteMap,
    Scene,
    SlideIn,
    Spring,
    Text,
    ZoomIn,
    linear,
    smooth,
)
from faceless_champ.spring import Spring as KernelSpring

BOUNCY = Spring(1, 0.4, 1)
CRITICAL = Spring(1, 2, 1)
OVERDAMPED = Spring(1, 4, 1)


def snapshot(scene):
    """Capture fields and identities; failure must not replace existing entries."""
    return (
        scene.time,
        id(scene.entries),
        id(scene._objects),
        tuple((id(component), id(entry)) for component, entry in scene._objects.items()),
        tuple(
            (
                id(entry),
                entry.start,
                entry.end,
                deepcopy(entry.initial),
                id(entry.parent),
                tuple(id(child) for child in entry.children),
                tuple(
                    (
                        id(track),
                        track.property,
                        track.start,
                        track.duration,
                        track.initial,
                        track.target,
                        track.easing,
                        track.keyframes,
                    )
                    for track in entry.tracks
                ),
            )
            for entry in scene.entries
        ),
        tuple(scene.audio),
    )


def test_root_export_is_the_existing_kernel_class():
    assert Spring is KernelSpring
    assert faceless_champ.__all__.count("Spring") == 1


@pytest.mark.parametrize("spring", [BOUNCY, CRITICAL, OVERDAMPED])
def test_move_rotation_scale_and_exact_boundaries_use_existing_tracks(spring):
    card = Rectangle(position=(20, 40), rotation=-30, scale=0.8, scale_x=1.2, scale_y=0.9)
    scene = Scene().wait(2)
    scene.play(
        card.animate.move_to(120, -10).rotate_to(450).scale_to(1.2).scale_xy_to(1.4, 1.1),
        run_time=0.75,
        rate_func=spring,
    )
    entry = scene._objects[card]
    assert scene.time == scene.duration == 2.75
    assert entry.start == 2
    assert all(track.easing is spring and track.duration == 0.75 for track in entry.tracks)
    for time in (2.075, 2.15, 2.375, 2.7425):
        p = spring((time - 2) / 0.75)
        state = entry.state_at(time)
        assert state["position"] == pytest.approx((20 + 100 * p, 40 - 50 * p))
        assert state["rotation"] == pytest.approx(-30 + 480 * p)
        assert state["scale"] == pytest.approx(0.8 + 0.4 * p)
        assert state["scale_x"] == pytest.approx(1.2 + 0.2 * p)
        assert state["scale_y"] == pytest.approx(0.9 + 0.2 * p)
    assert entry.state_at(-1) == entry.state_at(2)
    assert entry.state_at(2)["position"] == (20, 40)
    final = entry.state_at(2.75)
    assert final["position"] == (120, -10)
    assert final["rotation"] == 450
    assert (final["scale"], final["scale_x"], final["scale_y"]) == (1.2, 1.4, 1.1)
    assert entry.state_at(100) == final
    assert card.position == (20, 40) and card.rotation == -30 and card.scale == 0.8


@pytest.mark.parametrize("duration", [None, 0.000001, 0.25, 12])
def test_duration_default_and_explicit_duration_retain_existing_semantics(duration):
    scene, card = Scene(), Rectangle()
    kwargs = {} if duration is None else {"run_time": duration}
    scene.play(card.animate.move_to(10, 0), rate_func=BOUNCY, **kwargs)
    expected = 1 if duration is None else duration
    assert scene.time == expected
    assert scene._objects[card].state_at(expected * 0.1)["position"] == pytest.approx((10 * BOUNCY(0.1), 0))


@pytest.mark.parametrize("duration", [0, -1, 1e-7, math.inf, math.nan])
def test_invalid_durations_do_not_add_components(duration):
    scene = Scene()
    before = snapshot(scene)
    with pytest.raises(ValueError, match="run_time"):
        scene.play(Rectangle().animate.move_to(10, 0), run_time=duration, rate_func=BOUNCY)
    assert snapshot(scene) == before


@pytest.mark.parametrize("duration", [1, 1e308])
def test_spring_interval_rejects_clock_overflow_or_unrepresentable_end(duration):
    scene = Scene().wait(1e308)
    before = snapshot(scene)
    with pytest.raises(ValueError, match="finite end after its start"):
        scene.play(Rectangle().animate.move_to(10, 0), run_time=duration, rate_func=BOUNCY)
    assert snapshot(scene) == before


@pytest.mark.parametrize("key", ["scale", "scale_x", "scale_y"])
@pytest.mark.parametrize("start,target", [(0.001, 0.001), (0.001, 1), (0.8, 1.2), (1, 0.8)])
def test_safe_growing_shrinking_and_constant_scales(key, start, target):
    card = Rectangle(**{key: start})
    scene = Scene()
    scene.play(Animation(card, {key: target}), rate_func=BOUNCY)
    entry = scene._objects[card]
    assert min(entry.state_at(i / 1000)[key] for i in range(1001)) >= 0.001
    assert entry.state_at(1)[key] == target


@pytest.mark.parametrize("key", ["scale", "scale_x", "scale_y"])
def test_unsafe_scale_shrink_rejects_before_auto_add(key):
    scene, card = Scene(), Rectangle()
    before = snapshot(scene)
    with pytest.raises(ValueError, match=rf"{key} >= 0.001.*segment 1"):
        scene.play(Animation(card, {key: 0.1}), rate_func=BOUNCY)
    assert snapshot(scene) == before


@pytest.mark.parametrize("spring", [CRITICAL, OVERDAMPED])
def test_nonoscillatory_shrink_to_existing_minimum_can_be_certified(spring):
    scene, card = Scene(), Rectangle(scale=1)
    scene.play(card.animate.scale_to(0.001), rate_func=spring)
    assert min(scene._objects[card].state_at(i / 1000)["scale"] for i in range(1001)) >= 0.001


def test_uncertifiable_interpolation_rounding_at_scale_minimum_is_rejected():
    # The current interpolation evaluates this rounded expression below .001.
    assert 2 + (0.001 - 2) * 1 < 0.001
    scene, card = Scene(), Rectangle(scale=2)
    with pytest.raises(ValueError, match="cannot certify scale"):
        scene.play(card.animate.scale_to(0.001), rate_func=CRITICAL)
    assert scene.entries == []


def test_analytic_scale_proof_detects_a_dip_between_thirty_fps_samples():
    peak = 1 + math.exp(-math.pi * 0.2 / math.sqrt(1 - 0.2**2))
    target = 1 - (1 - 0.00099) / peak
    assert target > 0.001
    assert min(1 + (target - 1) * BOUNCY(i / 30) for i in range(31)) > 0.001
    scene, card = Scene(), Rectangle()
    with pytest.raises(ValueError, match="cannot certify scale"):
        scene.play(card.animate.scale_to(target), rate_func=BOUNCY)
    assert not scene.entries


def test_scale_threshold_has_outward_progress_rounding_allowance():
    peak = BOUNCY._progress_bounds[1]
    threshold = 1 - (1 - 0.001) / peak
    for offset, safe in [(0, False), (-1e-10, False), (1e-10, True)]:
        scene, card = Scene(), Rectangle()
        if safe:
            scene.play(card.animate.scale_to(threshold + offset), rate_func=BOUNCY)
        else:
            with pytest.raises(ValueError, match="cannot certify scale"):
                scene.play(card.animate.scale_to(threshold + offset), rate_func=BOUNCY)
            assert scene.entries == []


def unsupported_cases():
    rectangle = lambda: Rectangle(mask=RectangleMask(20, 20))
    cases = [
        (rectangle, key, value)
        for key, value in [
            ("opacity", 0.5),
            ("reveal", 0.5),
            ("draw", 0.5),
            ("fill", (20, 40, 60, 255)),
            ("stroke", (20, 40, 60, 0)),
            ("clip", (0, 0, 0.5, 1)),
            ("width", 100),
            ("height", 60),
            ("stroke_width", 0),
            ("corner_radius", 2),
            ("mask_position", (10, -10)),
            ("mask_width", 30),
            ("mask_height", 30),
        ]
    ]
    cases.extend(
        [
            (lambda: Text("Text"), "color", (20, 40, 60, 255)),
            (ProgressBar, "progress", 0.5),
            (lambda: Number(1), "value", 2),
            (lambda: BarChart(["a"], {"one": [1]}), "data", (2,)),
        ]
    )
    cases.extend((EarthMap, key, value) for key, value in [("longitude", 10), ("latitude", 20), ("zoom", 2)])
    cases.append((SatelliteMap, "map_rotation", 20))
    return cases


@pytest.mark.parametrize("factory,key,value", unsupported_cases())
@pytest.mark.parametrize("spring", [BOUNCY, CRITICAL, OVERDAMPED])
def test_unsupported_properties_reject_all_damping_regimes(factory, key, value, spring):
    scene, card = Scene(), factory()
    before = snapshot(scene)
    with pytest.raises(ValueError, match=rf"Spring does not support animation property '{key}'"):
        scene.play(Animation(card, {key: value}), rate_func=spring)
    assert snapshot(scene) == before


def test_unknown_custom_property_and_noop_bounded_track_are_not_exceptions():
    class Custom(Component):
        def state(self):
            return {**super().state(), "custom": 2, "wipe": 1}

    for key in ("opacity", "wipe", "custom"):
        scene, card = Scene(), Custom()
        with pytest.raises(ValueError, match=rf"property '{key}'"):
            scene.play(Animation(card, {key: card.state()[key]}), rate_func=CRITICAL)
        assert not scene.entries


@pytest.mark.parametrize("factory", [SlideIn, ZoomIn, PopIn])
def test_outer_spring_override_rejects_combined_fade_presets_atomically(factory):
    scene = Scene()
    with pytest.raises(ValueError, match="opacity"):
        scene.play(factory(Rectangle()), rate_func=BOUNCY)
    assert scene.time == 0 and not scene.entries


def test_effective_easing_precedence_and_different_property_concurrency():
    card = Rectangle(position=(20, 40), opacity=0.7)
    scene = Scene()
    scene.play(Animation(card, {"position": (120, 40)}, rate_func=BOUNCY), FadeIn(card), run_time=2)
    entry = scene._objects[card]
    assert entry.tracks[0].easing is BOUNCY
    assert entry.tracks[1].easing is smooth
    assert entry.state_at(0.2)["position"] == pytest.approx((20 + 100 * BOUNCY(0.1), 40))
    assert entry.state_at(0.2)["opacity"] == pytest.approx(0.7 * smooth(0.1))
    assert entry.state_at(2)["opacity"] == 0.7

    override = Scene()
    override.play(Animation(Rectangle(), {"opacity": 0}, rate_func=BOUNCY), rate_func=linear)
    assert override.entries[0].tracks[0].easing is linear
    assert override.entries[0].state_at(0.5)["opacity"] == 0.5
    with pytest.raises(ValueError, match="opacity"):
        Scene().play(Animation(Rectangle(), {"opacity": 0}, rate_func=linear), rate_func=BOUNCY)


def test_falsy_callable_precedence_and_custom_easing_contract_stay_unchanged():
    class Falsy:
        def __bool__(self):
            return False

        def __call__(self, u):
            raise AssertionError("Falsy play easing should retain existing fallback behavior")

    card, scene = Rectangle(), Scene()
    scene.play(Animation(card, {"position": (10, 0)}, rate_func=BOUNCY), rate_func=Falsy())
    assert scene.entries[0].tracks[0].easing is BOUNCY
    custom = lambda u: BOUNCY(u)
    legacy = Scene()
    legacy.play(Rectangle().animate.opacity_to(0), rate_func=custom)
    assert legacy.entries[0].state_at(0.1)["opacity"] == 1 - BOUNCY(0.1)


def test_timeline_resolved_start_and_relative_transforms_are_validated():
    card = Rectangle(position=(10, 20), scale=2, rotation=15)
    scene = Scene().add(card)
    scene.play(card.animate.move_to(30, 40).scale_to(3).rotate_to(25), rate_func=linear)
    scene.play(
        Animation(
            card,
            {"position": (20, -10), "scale": 1.2, "rotation": 30},
            starts={"position": (-10, 5), "scale": 0.8, "rotation": -5},
            relative=("position", "scale", "rotation"),
        ),
        rate_func=BOUNCY,
    )
    entry = scene._objects[card]
    assert entry.state_at(1)["position"] == (20, 45)
    assert entry.state_at(1)["scale"] == pytest.approx(2.4)
    assert entry.state_at(2)["position"] == (50, 30)
    assert entry.state_at(2)["scale"] == pytest.approx(3.6)
    assert entry.state_at(2)["rotation"] == 55
    assert card.position == (10, 20) and card.scale == 2

    before = snapshot(scene)
    with pytest.raises(ValueError, match="cannot certify scale"):
        scene.play(card.animate.scale_to(0.1), rate_func=BOUNCY)
    assert snapshot(scene) == before
    small, small_scene = Rectangle(scale=0.01), Scene()
    with pytest.raises(ValueError, match="cannot certify scale"):
        small_scene.play(Animation(small, {"scale": 0.1}, relative=("scale",)), rate_func=BOUNCY)
    assert not small_scene.entries


def test_explicit_start_determines_the_scale_trajectory():
    scene, card = Scene(), Rectangle(scale=0.1)
    with pytest.raises(ValueError, match="cannot certify scale"):
        scene.play(Animation(card, {"scale": 0.1}, starts={"scale": 1}), rate_func=BOUNCY)
    assert not scene.entries


def test_keyframes_restart_spring_per_segment_and_resolve_relative_values():
    scene, card = Scene(), Rectangle(position=(20, 40), scale=2)
    frames = {"position": ((0, (0, 0)), (0.25, (20, 10)), (1, (-10, 20))), "scale": ((0, 1), (0.25, 1.2), (1, 1))}
    scene.play(
        Animation(card, {"position": (-10, 20), "scale": 1}, keyframes=frames, relative=("position", "scale")),
        rate_func=BOUNCY,
    )
    entry = scene._objects[card]
    assert entry.state_at(0)["position"] == (20, 40)
    assert entry.state_at(0.25)["position"] == (40, 50)
    for time, left, right, a, b in [(0.1, 0, 0.25, (20, 40), (40, 50)), (0.5, 0.25, 1, (40, 50), (10, 60))]:
        p = BOUNCY((time - left) / (right - left))
        assert entry.state_at(time)["position"] == pytest.approx(tuple(x + (y - x) * p for x, y in zip(a, b)))
    assert entry.state_at(1)["position"] == (10, 60)
    assert entry.state_at(1)["scale"] == 2


def test_each_keyframe_segment_is_certified_even_when_whole_track_is_constant():
    scene, card = Scene(), Rectangle()
    frames = ((0, 1), (0.4999, 1), (0.5, 0.1), (1, 1))
    with pytest.raises(ValueError, match="scale.*segment 2"):
        scene.play(Animation(card, {"scale": 1}, keyframes={"scale": frames}), rate_func=BOUNCY)
    assert not scene.entries


@pytest.mark.parametrize(
    "key,start,end",
    [("rotation", -1e308, 1e308), ("position", -1e308, 1e308)]
    + [(key, 1e308, 1.6e308) for key in ("rotation", "position", "scale")],
)
def test_nonfinite_interpolation_rejects_finite_endpoints(key, start, end):
    initial, target = ((start, 0), (end, 0)) if key == "position" else (start, end)
    card, scene = Rectangle(**{key: initial}), Scene()
    before = snapshot(scene)
    with pytest.raises(ValueError, match=rf"{key}.*nonfinite interpolation"):
        scene.play(Animation(card, {key: target}), rate_func=BOUNCY)
    assert snapshot(scene) == before


def test_keyframe_overflow_and_nonreal_raw_values_reject_before_publication():
    scene, card = Scene(), Rectangle(rotation=1e308)
    with pytest.raises(ValueError, match="nonfinite interpolation"):
        scene.play(
            Animation(card, {"rotation": 1e308}, keyframes={"rotation": ((0, 1e308), (0.5, -1e308), (1, 1e308))}),
            rate_func=BOUNCY,
        )
    for key, value in [("rotation", "20"), ("position", ("20", 0))]:
        with pytest.raises(TypeError, match="real numeric values"):
            scene.play(Animation(card, {key: value}), rate_func=BOUNCY)
    assert not scene.entries


def test_integer_conversion_overflow_is_rejected_without_partial_state():
    card, scene = Rectangle(), Scene()
    with pytest.raises(ValueError, match="nonfinite interpolation"):
        scene.play(Animation(card, {"rotation": 10**308}, starts={"rotation": -(10**308)}), rate_func=BOUNCY)
    assert not scene.entries


def test_play_failures_preserve_existing_hierarchy_entries_tracks_and_cursor():
    child = Rectangle()
    group = Group(child)
    scene = Scene().add(group)
    scene.play(child.animate.rotate_to(20), rate_func=linear)
    good_new = Rectangle()
    new_group = Group(good_new)
    for invalid in [
        Animation(child, {"scale": 0.1}),
        Animation(child, {"opacity": 0.5}),
        Animation(child, {"rotation": 1e308}, starts={"rotation": -1e308}),
    ]:
        before = snapshot(scene)
        with pytest.raises(ValueError):
            scene.play(new_group.animate.move_to(10, 10), invalid, rate_func=BOUNCY)
        assert snapshot(scene) == before
        assert new_group not in scene._objects and good_new not in scene._objects
        assert child.scale == 1 and child.rotation == 0

    before = snapshot(scene)
    with pytest.raises(ValueError, match="Overlapping"):
        scene.play(child.animate.rotate_to(30), child.animate.rotate_to(40), rate_func=BOUNCY)
    assert snapshot(scene) == before


def test_absolute_cursor_chronology_lifetimes_and_sampling_still_apply():
    card, scene = Rectangle(), Scene().wait(5)
    with scene.at(0):
        scene.add(card)
    with scene.at(1):
        scene.play(card.animate.move_to(100, 0), rate_func=BOUNCY)
    assert scene.time == 5
    before = snapshot(scene)
    with scene.at(1.5), pytest.raises(ValueError, match="chronological"):
        scene.play(card.animate.move_to(200, 0), rate_func=BOUNCY)
    assert snapshot(scene) == before
    scene.remove(card)
    before = snapshot(scene)
    with pytest.raises(ValueError, match="lifetime"):
        scene.play(card.animate.rotate_to(30), rate_func=BOUNCY)
    assert snapshot(scene) == before


def test_group_axis_transforms_render_and_measure_without_mutating_snapshots():
    card = Rectangle(width=40, height=24, fill="red", stroke=None, position=(100, 80))
    label = Text("A", font_size=16, position=(100, 80))
    inner = Group(card, label)
    outer = Group(inner, rotation=5)
    scene = Scene(Canvas(220, 160)).add(outer)
    source = (card.state(), inner.state(), outer.state())
    scene.play(
        outer.animate.move_to(120, 85).scale_to(1.1).scale_xy_to(1.2, 0.9).rotate_to(15),
        card.animate.scale_to(0.9),
        run_time=2,
        rate_func=BOUNCY,
    )
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    times = (0, 0.2, 0.8, 2, 1.3)
    expected = {
        time: (renderer.frame(scene, time, (220, 160)).tobytes(), scene.bounds_at(card, time)) for time in times
    }
    assert len({image for image, _ in expected.values()}) > 2
    for time in reversed(times):
        assert renderer.frame(scene, time, (220, 160)).tobytes() == expected[time][0]
        assert scene.bounds_at(card, time) == expected[time][1]
        assert all(math.isfinite(value) for value in astuple(expected[time][1]))
    assert (card.state(), inner.state(), outer.state()) == source
    assert tuple(scene._objects[component].initial for component in (card, inner, outer)) == source


def test_unsafe_group_scale_rejects_without_affecting_members_or_existing_entries():
    child = Rectangle()
    group = Group(child)
    scene = Scene().add(group)
    before = snapshot(scene)
    with pytest.raises(ValueError, match="scale_y >= 0.001"):
        scene.play(group.animate.move_to(20, 30).scale_xy_to(1.1, 0.1), rate_func=BOUNCY)
    assert snapshot(scene) == before
    assert child.scale_y == group.scale_y == 1


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Text("Card", position=(100, 80)),
        lambda: BarChart(["a"], {"one": [1]}, position=(100, 80), width=160, height=120),
    ],
)
def test_whole_text_and_chart_transforms_use_the_cpu_renderer(factory):
    card, scene = factory(), Scene(Canvas(220, 160))
    scene.play(card.animate.move_to(120, 90).rotate_to(10), run_time=0.5, rate_func=BOUNCY)
    renderer = PillowRenderer(1)
    renderer.validate(scene)
    start = renderer.frame(scene, 0, (220, 160)).tobytes()
    assert renderer.frame(scene, 0.1, (220, 160)).tobytes() != start
    assert renderer.frame(scene, 0, (220, 160)).tobytes() == start


@pytest.mark.parametrize("easing", [linear, smooth])
def test_non_spring_geometry_and_bounded_properties_keep_existing_behavior(easing):
    card, scene = Rectangle(), Scene()
    scene.play(card.animate.scale_to(0.001).opacity_to(0).width_to(10), rate_func=easing)
    state = scene._objects[card].state_at(0.3)
    p = easing(0.3)
    assert state["scale"] == 1 + (0.001 - 1) * p
    assert state["opacity"] == 1 - p
    assert state["width"] == card.width + (10 - card.width) * p


def test_track_order_holds_and_source_snapshots_are_preserved():
    card, scene = Rectangle(position=(10, 20)), Scene()
    scene.play(card.animate.move_to(30, 40), rate_func=BOUNCY)
    scene.wait(0.5)
    scene.play(card.animate.move_to(50, 60), rate_func=CRITICAL)
    tracks = scene._objects[card].tracks
    assert all(left.start < right.start for left, right in pairwise(tracks))
    assert scene._objects[card].state_at(1.25)["position"] == (30, 40)
    assert scene._objects[card].state_at(1.5)["position"] == (30, 40)
    assert scene._objects[card].state_at(2.5)["position"] == (50, 60)
    assert card.position == (10, 20)
