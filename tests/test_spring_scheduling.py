"""Spring composition through existing finite schedules and publication trials."""

import math
import pickle
from copy import copy, deepcopy
from dataclasses import FrozenInstanceError

import pytest

from faceless_champ import (
    Animation,
    Canvas,
    FadeIn,
    Group,
    PillowRenderer,
    Rectangle,
    Repeat,
    Scene,
    Spring,
    Stagger,
    Succession,
    ease_in,
    linear,
    smooth,
)
from faceless_champ.scheduling import _reverse_easing
from faceless_champ.spring import _ReversedSpring, _spring_progress_bounds

SPRINGS = [Spring(1, 0.4, 1), Spring(1, 2, 1), Spring(1, 4, 1)]


def snapshot(scene):
    return (
        scene.time,
        id(scene.entries),
        id(scene._objects),
        tuple((id(c), id(e)) for c, e in scene._objects.items()),
        tuple(
            (
                id(e),
                e.start,
                e.end,
                deepcopy(e.initial),
                id(e.parent),
                tuple(id(child) for child in e.children),
                tuple(
                    (id(t), t.property, t.start, t.duration, t.initial, t.target, t.easing, t.keyframes)
                    for t in e.tracks
                ),
            )
            for e in scene.entries
        ),
        tuple(scene.audio),
    )


@pytest.mark.parametrize("spring", SPRINGS)
def test_reversed_adapter_retains_bounds_immutability_and_canonical_double_reversal(spring):
    reversed_spring = _reverse_easing(spring)
    assert isinstance(reversed_spring, _ReversedSpring)
    assert reversed_spring.spring is spring
    lower, upper = _spring_progress_bounds(spring)
    assert _spring_progress_bounds(reversed_spring) == (1 - upper, 1 - lower)
    if spring._damping_ratio < 1:
        assert reversed_spring._progress_bounds[0] < 0
    for u in (-2, 0, math.nextafter(0, 1), 0.01, 0.1, 0.5, 0.99, math.nextafter(1, 0), 1, 2):
        assert reversed_spring(u) == 1 - spring(1 - u)
    with pytest.raises(FrozenInstanceError):
        reversed_spring.spring = SPRINGS[0]
    for clone in (copy(reversed_spring), deepcopy(reversed_spring), pickle.loads(pickle.dumps(reversed_spring))):
        assert clone == reversed_spring
        assert _spring_progress_bounds(clone) == reversed_spring._progress_bounds
        assert _reverse_easing(clone) == spring
    for _ in range(20):
        assert _reverse_easing(reversed_spring) is spring
        assert _spring_progress_bounds(_reverse_easing(reversed_spring)) == (lower, upper)


@pytest.mark.parametrize(
    "value,error", [(True, TypeError), ("0.5", TypeError), (math.nan, ValueError), (math.inf, ValueError)]
)
def test_reversed_adapter_validates_progress(value, error):
    with pytest.raises(error, match="progress"):
        _reverse_easing(SPRINGS[0])(value)


def test_generic_callable_reversal_keeps_existing_semantics():
    reversed_ease = _reverse_easing(ease_in)
    assert _spring_progress_bounds(reversed_ease) is None
    assert _spring_progress_bounds(lambda u: SPRINGS[0](u)) is None
    for u in (0, 0.1, 0.4, 1):
        assert reversed_ease(u) == 1 - ease_in(1 - u)


@pytest.mark.parametrize("spring", SPRINGS)
@pytest.mark.parametrize("cycles", [1, 2, 3, 4])
@pytest.mark.parametrize("ping_pong", [False, True])
def test_repeat_transforms_boundaries_and_final_holds(spring, cycles, ping_pong):
    card = Rectangle(position=(10, -20), rotation=-10, scale=0.4)
    scene = Scene().add(card).wait(0.125)
    scene.play(
        Repeat(
            card.animate.move_to(110, 80).rotate_to(70).scale_to(1),
            cycles=cycles,
            ping_pong=ping_pong,
            duration=0.5,
            delay=0.25,
        ),
        rate_func=spring,
    )
    entry = scene._objects[card]
    assert scene.time == 0.375 + cycles * 0.5
    assert len(entry.tracks) == cycles * 3
    for cycle in range(cycles):
        start = 0.375 + cycle * 0.5
        reverse = ping_pong and cycle % 2
        position_track = entry.tracks[cycle * 3]
        assert isinstance(position_track.easing, _ReversedSpring if reverse else Spring)
        assert position_track.start == start and position_track.duration == 0.5
        for u in (0, 0.05, 0.2, 0.75, 0.999):
            p = spring(1 - u) if reverse else spring(u)
            state = entry.state_at(start + u * 0.5)
            assert state["position"] == pytest.approx((10 + 100 * p, -20 + 100 * p), abs=1e-12)
            assert state["rotation"] == pytest.approx(-10 + 80 * p, abs=1e-12)
            assert state["scale"] == pytest.approx(0.4 + 0.6 * p, abs=1e-12)
        if cycle:
            before = entry.state_at(math.nextafter(start, -math.inf))
            at = entry.state_at(start)
            if ping_pong:
                assert before["position"] == pytest.approx(at["position"], abs=1e-7)
            else:
                assert before["position"] == pytest.approx((110, 80), abs=1e-7)
                assert at["position"] == (10, -20)
    final = entry.state_at(scene.time)
    assert final["position"] == ((10, -20) if ping_pong and cycles % 2 == 0 else (110, 80))
    assert entry.state_at(scene.time + 5) == final
    assert card.position == (10, -20) and card.scale == 0.4


@pytest.mark.parametrize("spring", SPRINGS)
@pytest.mark.parametrize("key", ["scale", "scale_x", "scale_y"])
def test_reversed_scale_uses_transformed_bounds_instead_of_a_fresh_forward_spring(spring, key):
    card, scene = Rectangle(**{key: 0.1}), Scene()
    scene.play(Repeat(Animation(card, {key: 1}, rate_func=spring), cycles=2, ping_pong=True))
    entry = scene._objects[card]
    assert isinstance(entry.tracks[1].easing, _ReversedSpring)
    assert min(entry.state_at(i / 1000)[key] for i in range(2001)) >= 0.001
    assert entry.state_at(2)[key] == 0.1
    for t in (0.01, 0.1, 0.4, 0.9):
        assert entry.state_at(t)[key] == pytest.approx(entry.state_at(2 - t)[key], abs=3e-15)


@pytest.mark.parametrize("spring", SPRINGS)
def test_reversal_rounding_failure_in_a_later_traversal_discards_the_whole_schedule(spring):
    child = Rectangle(scale=0.001)
    group = Group(child)
    scene = Scene().add(group)
    before = snapshot(scene)
    # Forward growth is safe; the return arithmetic rounds slightly below .001.
    assert 2 + (0.001 - 2) * 1 < 0.001
    with pytest.raises(ValueError, match="cannot certify scale"):
        scene.play(Repeat(child.animate.scale_to(2), cycles=2, ping_pong=True), rate_func=spring)
    assert snapshot(scene) == before
    assert child.scale == 0.001 and not scene._objects[child].tracks


@pytest.mark.parametrize("factor", [0.5, 1, 2])
@pytest.mark.parametrize("override", [False, True])
def test_nested_stagger_succession_scales_delays_gaps_durations_and_leaf_easing(factor, override):
    spring = SPRINGS[0]
    a, b = Rectangle(), Rectangle()
    scene = Scene().add(a, b).wait(0.5)
    leaf_easing = None if override else spring
    schedule = Stagger(
        Succession(
            Animation(a, {"position": (10, 0)}, rate_func=leaf_easing),
            Animation(a, {"position": (20, 0)}, rate_func=leaf_easing),
            duration=0.5,
            delay=0.25,
        ),
        Animation(b, {"position": (100, 0)}, rate_func=leaf_easing),
        lag=0.125,
        duration=0.75,
        delay=0.125,
    )
    assert schedule.run_time == 1.375
    kwargs = {} if factor == 1 else {"run_time": 1.375 * factor}
    scene.play(schedule, rate_func=spring if override else None, **kwargs)
    assert scene.time == 0.5 + 1.375 * factor
    first, second = scene._objects[a].tracks
    other = scene._objects[b].tracks[0]
    assert (first.start, first.duration) == (0.5 + 0.375 * factor, 0.5 * factor)
    assert (second.start, second.duration) == (0.5 + 0.875 * factor, 0.5 * factor)
    assert (other.start, other.duration) == (0.5 + 0.25 * factor, 0.75 * factor)
    assert all(t.easing == spring for t in (first, second, other))
    assert first.value_at(first.start + 0.1 * first.duration) == pytest.approx((10 * spring(0.1), 0))
    assert scene._objects[a].state_at(scene.time)["position"] == (20, 0)
    assert scene._objects[b].state_at(scene.time)["position"] == (100, 0)


@pytest.mark.parametrize("spring", SPRINGS)
def test_keyframes_reverse_order_and_easing_per_segment(spring):
    card, scene = Rectangle(rotation=10, scale=0.5), Scene()
    animation = Animation(
        card,
        {"rotation": 70, "scale": 1},
        keyframes={"rotation": ((0, 10), (0.25, 25), (1, 70)), "scale": ((0, 0.5), (0.25, 0.7), (1, 1))},
        rate_func=spring,
    )
    scene.play(Repeat(animation, cycles=2, ping_pong=True))
    entry = scene._objects[card]
    reverse_rotation = entry.tracks[2]
    assert reverse_rotation.keyframes == ((0, 70), (0.75, 25), (1, 10))
    for t in (0, 0.02, 0.1, 0.25, 0.3, 0.7, 0.95, 1):
        forward, backward = entry.state_at(t), entry.state_at(2 - t)
        assert forward["rotation"] == pytest.approx(backward["rotation"], abs=1e-12)
        assert forward["scale"] == pytest.approx(backward["scale"], abs=1e-14)


def test_nested_repeat_canonicalizes_double_reversals_without_bound_inflation():
    spring = SPRINGS[0]
    card, scene = Rectangle(), Scene()
    inner = Repeat(
        Animation(card, {"position": (10, 0)}, rate_func=spring), cycles=2, ping_pong=True, duration=0.25, delay=0.125
    )
    scene.play(Repeat(inner, cycles=2, ping_pong=True, delay=0.125))
    tracks = scene._objects[card].tracks
    assert scene.time == 1.375
    assert [t.start for t in tracks] == [0.25, 0.5, 0.75, 1]
    assert [isinstance(t.easing, _ReversedSpring) for t in tracks] == [False, True, False, True]
    assert tracks[2].easing is tracks[0].easing
    assert _spring_progress_bounds(tracks[3].easing) == _spring_progress_bounds(tracks[1].easing)
    assert scene._objects[card].state_at(scene.time)["position"] == (0, 0)
    for local in (0.02, 0.1, 0.2, 0.4, 0.6):
        assert scene._objects[card].state_at(0.125 + local)["position"] == pytest.approx(
            scene._objects[card].state_at(1.375 - local)["position"], abs=1e-12
        )


def test_nested_delays_become_holds_in_the_mirrored_traversal():
    card, scene = Rectangle(), Scene()
    child = Succession(
        Animation(card, {"position": (10, 0)}, rate_func=SPRINGS[0]),
        Succession(Animation(card, {"position": (20, 0)}, rate_func=SPRINGS[0]), duration=0.25, delay=0.5),
        duration=0.5,
        delay=0.25,
    )
    assert child.run_time == 1.5
    scene.add(card).play(Repeat(child, cycles=2, ping_pong=True))
    entry = scene._objects[card]
    assert entry.state_at(0.1)["position"] == (0, 0)
    assert entry.state_at(1)["position"] == (10, 0)
    assert entry.state_at(2)["position"] == (10, 0)
    assert entry.state_at(2.9)["position"] == (0, 0)
    for t in (0.1, 0.3, 0.6, 0.8, 1, 1.4):
        assert entry.state_at(t)["position"] == pytest.approx(entry.state_at(3 - t)["position"], abs=1e-12)


@pytest.mark.parametrize("ping_pong,final", [(False, (20, 0)), (True, (10, 0))])
def test_repeat_captures_resolved_relative_values_without_accumulating(ping_pong, final):
    card, scene = Rectangle(position=(10, 0), scale=0.5), Scene()
    animation = Animation(
        card, {"position": (10, 0), "scale": 1.1}, relative=("position", "scale"), rate_func=SPRINGS[0]
    )
    scene.play(Repeat(animation, cycles=4, ping_pong=ping_pong, duration=0.25))
    assert scene._objects[card].state_at(1)["position"] == final
    assert scene._objects[card].state_at(1)["scale"] == (0.5 if ping_pong else 0.55)
    assert card.position == (10, 0) and card.scale == 0.5


@pytest.mark.parametrize("mode", ["at", "stagger", "arguments"])
def test_spring_transform_and_conventional_fade_can_overlap(mode):
    card = Rectangle(width=30, height=20, position=(60, 60), fill="red", stroke=None)
    scene = Scene(Canvas(180, 120, "#00000000")).add(card)
    motion = Repeat(
        Animation(card, {"position": (120, 60)}, rate_func=SPRINGS[0]), cycles=2, ping_pong=True, duration=0.5
    )
    if mode == "stagger":
        scene.play(Stagger(motion, FadeIn(card), lag=0, duration=0.5))
    elif mode == "arguments":
        scene.play(motion, FadeIn(card))
    else:
        with scene.at(0):
            scene.play(motion)
        with scene.at(0):
            scene.play(FadeIn(card), run_time=0.5)
    entry = scene._objects[card]
    assert scene.time == 1
    assert entry.state_at(0.125)["opacity"] == smooth(0.125 if mode == "arguments" else 0.25)
    assert entry.state_at(0.125)["position"] == pytest.approx((60 + 60 * SPRINGS[0](0.25), 60))
    assert entry.state_at(1)["position"] == (60, 60)
    assert entry.state_at(1)["opacity"] == 1
    renderer = PillowRenderer(1)
    assert renderer.frame(scene, 0, (180, 120)).getbbox() is None
    middle = renderer.frame(scene, 0.125, (180, 120)).tobytes()
    assert renderer.frame(scene, 0.5, (180, 120)).getbbox() is not None
    assert renderer.frame(scene, 0.125, (180, 120)).tobytes() == middle
    assert card.opacity == 1 and card.position == (60, 60)


@pytest.mark.parametrize("failure", ["property", "scale", "collision", "keyframes"])
def test_late_nested_failures_preserve_existing_scene_and_new_hierarchy_ownership(failure):
    existing = Rectangle()
    old_group = Group(existing)
    scene = Scene().add(old_group)
    scene.play(existing.animate.rotate_to(10), rate_func=linear)
    new_child = Rectangle()
    new_group = Group(new_child)
    if failure == "property":
        schedule = Succession(new_group.animate.move_to(20, 20), existing.animate.opacity_to(0.5))
    elif failure == "scale":
        schedule = Succession(new_group.animate.move_to(20, 20), existing.animate.scale_to(0.1))
    elif failure == "collision":
        schedule = Stagger(
            new_group.animate.move_to(20, 20),
            existing.animate.move_to(10, 0),
            existing.animate.move_to(20, 0),
            lag=0.25,
        )
    else:
        tiny = math.nextafter(0, 1)
        animation = Animation(existing, {"rotation": 20}, keyframes={"rotation": ((0, 10), (tiny, 15), (1, 20))})
        schedule = Succession(new_group.animate.move_to(20, 20), Repeat(animation, cycles=2, ping_pong=True))
    before = snapshot(scene)
    with pytest.raises(ValueError):
        scene.play(schedule, rate_func=SPRINGS[0])
    assert snapshot(scene) == before
    assert new_group not in scene._objects and new_child not in scene._objects
    assert new_child.position == (0, 0) and existing.rotation == 0


def test_group_lifetimes_and_existing_entry_identity_survive_scheduling():
    child = Rectangle(width=30, height=20, position=(60, 60), fill="red", stroke=None)
    group = Group(child)
    scene = Scene(Canvas(120, 120, "#00000000")).add(group)
    entry, parent = scene._objects[child], scene._objects[group]
    scene.play(
        Repeat(child.animate.rotate_to(20), cycles=2, ping_pong=True, duration=0.5, delay=0.25), rate_func=SPRINGS[0]
    )
    assert scene._objects[child] is entry and scene._objects[group] is parent
    assert entry.parent is parent and parent.children == [entry]
    before = snapshot(scene)
    with scene.at(1), pytest.raises(ValueError, match="animations end"):
        scene.remove(group)
    assert snapshot(scene) == before
    scene.remove(group)
    renderer = PillowRenderer(1)
    assert renderer.frame(scene, 1.2, (120, 120)).getbbox() is not None
    assert renderer.frame(scene, 1.25, (120, 120)).getbbox() is None
    new = Rectangle()
    before = snapshot(scene)
    with pytest.raises(ValueError, match="lifetime"):
        scene.play(Succession(new.animate.move_to(10, 0), child.animate.move_to(20, 0)), rate_func=SPRINGS[0])
    assert snapshot(scene) == before
    assert new not in scene._objects


def test_absolute_schedule_conflicts_are_atomic_and_keep_the_furthest_cursor():
    card, other = Rectangle(), Rectangle()
    scene = Scene().add(card).wait(5)
    with scene.at(1):
        scene.play(Repeat(card.animate.move_to(10, 0), cycles=2, ping_pong=True, duration=0.5), rate_func=SPRINGS[0])
    assert scene.time == 5
    before = snapshot(scene)
    with scene.at(1.25), pytest.raises(ValueError, match="chronological"):
        scene.play(Stagger(other.animate.move_to(10, 0), card.animate.move_to(20, 0), lag=0.25), rate_func=SPRINGS[0])
    assert snapshot(scene) == before
    assert other not in scene._objects


def test_top_level_spring_override_does_not_silently_apply_to_fades():
    card, scene = Rectangle(), Scene()
    before = snapshot(scene)
    with pytest.raises(ValueError, match="opacity"):
        scene.play(
            Stagger(Repeat(card.animate.move_to(10, 0), cycles=2, ping_pong=True), FadeIn(card), lag=0),
            rate_func=SPRINGS[0],
        )
    assert snapshot(scene) == before


@pytest.mark.parametrize("factor", [0.5, 2, 3])
def test_repeat_retiming_scales_every_traversal_and_mirrored_delay(factor):
    def make(scale):
        card, scene = Rectangle(scale=0.6), Scene()
        scene.add(card).wait(0.5)
        animation = Animation(card, {"position": (10, 0), "scale": 1}, rate_func=SPRINGS[0])
        schedule = Repeat(Succession(animation, duration=0.5, delay=0.25), cycles=3, ping_pong=True, delay=0.25)
        assert schedule.run_time == 2.5
        scene.play(schedule, run_time=2.5 * scale)
        return card, scene

    original_card, original = make(1)
    retimed_card, retimed = make(factor)
    assert retimed.time == 0.5 + 2.5 * factor
    first, second = original._objects[original_card], retimed._objects[retimed_card]
    assert [isinstance(t.easing, _ReversedSpring) for t in first.tracks] == [
        isinstance(t.easing, _ReversedSpring) for t in second.tracks
    ]
    for i in range(81):
        local = i / 32
        a = first.state_at(0.5 + local)
        b = second.state_at(0.5 + factor * local)
        assert a["position"] == pytest.approx(b["position"], abs=2e-13)
        assert a["scale"] == pytest.approx(b["scale"], abs=2e-14)


def test_reversed_clock_overflow_in_a_later_traversal_is_atomic():
    card, scene = Rectangle(), Scene().wait(1e308)
    before = snapshot(scene)
    with pytest.raises(ValueError, match="finite end after its start"):
        scene.play(Repeat(card.animate.move_to(10, 0), cycles=2, ping_pong=True, duration=5e307), rate_func=SPRINGS[0])
    assert snapshot(scene) == before
    assert card not in scene._objects


def test_existing_reversed_tracks_survive_a_subsequent_successful_trial():
    card, scene = Rectangle(position=(30, 40)), Scene()
    scene.add(card).play(
        Repeat(card.animate.move_to(60, 40), cycles=2, ping_pong=True, duration=0.5), rate_func=SPRINGS[0]
    )
    entry = scene._objects[card]
    times = (0.05, 0.2, 0.6, 0.9)
    expected = {time: entry.state_at(time) for time in times}
    scene.play(Repeat(card.animate.rotate_to(30), cycles=2, ping_pong=True, duration=0.25), rate_func=SPRINGS[1])
    assert scene._objects[card] is entry
    assert isinstance(entry.tracks[1].easing, _ReversedSpring)
    assert all(entry.state_at(time) == expected[time] for time in times)
    assert _reverse_easing(entry.tracks[1].easing) == SPRINGS[0]
    assert entry.state_at(scene.time)["rotation"] == 0


@pytest.mark.parametrize("cycles", [2, 3, 7])
@pytest.mark.parametrize("duration", [0.1, 0.3, 0.4, 0.7])
@pytest.mark.parametrize("run_time", [0.6, 0.75, 1.3])
def test_decimal_retiming_reaches_exact_scene_endpoint(cycles, duration, run_time):
    card, scene = Rectangle(), Scene()
    scene.play(
        Repeat(card.animate.move_to(10, 0), cycles=cycles, duration=duration, delay=0.13, ping_pong=True),
        run_time=run_time,
        rate_func=SPRINGS[1],
    )
    entry = scene._objects[card]
    expected = (0, 0) if cycles % 2 == 0 else (10, 0)
    assert entry.state_at(scene.time)["position"] == expected
    assert entry.state_at(scene.time + 1)["position"] == expected


@pytest.mark.parametrize("easing", [linear, lambda u: SPRINGS[1](u)])
def test_terminal_alignment_keeps_generic_callable_duration_arithmetic_unchanged(easing):
    card, scene = Rectangle(), Scene()
    schedule = Repeat(Animation(card, {"position": (10, 0)}, rate_func=easing), cycles=3, duration=0.3, delay=0.13)
    scene.play(schedule, run_time=0.6)
    expected_duration = 0.3 * (0.6 / schedule.run_time)
    assert all(track.duration == expected_duration for track in scene._objects[card].tracks)


def test_endpoint_alignment_preserves_an_intentional_terminal_hold():
    card, scene = Rectangle(), Scene()
    scene.add(card).wait(1e9)
    child = Succession(Animation(card, {"position": (10, 0)}, rate_func=SPRINGS[0]), duration=0.5, delay=1e-6)
    scene.play(Repeat(child, cycles=2, ping_pong=True))
    last = scene._objects[card].tracks[-1]
    assert last.duration == 0.5
    assert 0 < scene.time - (last.start + last.duration) < 16 * math.ulp(scene.time)
    assert scene._objects[card].state_at(scene.time)["position"] == (0, 0)


@pytest.mark.parametrize("spring", SPRINGS)
@pytest.mark.parametrize("start,duration", [(0.3, 0.4), (0.4, 0.1)])
def test_direct_spring_intervals_also_reach_their_exact_absolute_endpoint(spring, start, duration):
    card, scene = Rectangle(), Scene().wait(start)
    scene.play(card.animate.move_to(10, 0), run_time=duration, rate_func=spring)
    assert scene.time == start + duration
    assert scene._objects[card].state_at(scene.time)["position"] == (10, 0)
