import pytest

from faceless_champ import (
    Animation,
    BounceIn,
    Canvas,
    FadeIn,
    PillowRenderer,
    PopIn,
    PopOut,
    Pulse,
    Scene,
    Shake,
    SlideIn,
    SlideOut,
    SpinIn,
    Square,
    Wiggle,
    ZoomIn,
    ZoomOut,
    ease_in,
    ease_out,
    linear,
    smooth,
)


@pytest.mark.parametrize("factory", [SlideIn, ZoomIn, PopIn, BounceIn, SpinIn])
def test_entrances_restore_nondefault_transforms_and_bound_opacity(factory):
    scene = Scene(Canvas(240, 180))
    square = Square(30, position=(120, 90), scale=1.6, rotation=15, opacity=0.65, fill="red", stroke=None)
    scene.play(factory(square), run_time=1)
    entry = scene.entries[0]
    assert entry.state_at(0)["opacity"] == 0
    for time in (0.01, 0.2, 0.55, 0.64, 0.78, 0.99):
        state = entry.state_at(time)
        assert 0 <= state["opacity"] <= 0.65
        assert state["scale"] > 0
    final = entry.state_at(1)
    assert final["position"] == (120, 90)
    assert final["scale"] == 1.6
    assert final["rotation"] == 15
    assert final["opacity"] == 0.65
    assert entry.state_at(2) == final
    renderer = PillowRenderer(1)
    initial = renderer.frame(scene, 0, (240, 180)).convert("RGB")
    middle = renderer.frame(scene, 0.4, (240, 180)).tobytes()
    renderer.frame(scene, 1, (240, 180))
    assert initial.getbbox() is None
    assert renderer.frame(scene, 0.4, (240, 180)).tobytes() == middle


def test_pop_overshoots_and_settles_without_opacity_overshoot():
    scene, square = Scene(), Square(scale=2)
    scene.play(PopIn(square, from_scale=0.4, overshoot=1.2))
    entry = scene.entries[0]
    assert entry.state_at(0)["scale"] == 0.8
    assert entry.state_at(0.64)["scale"] == pytest.approx(2.4)
    assert 0 < entry.state_at(0.64)["opacity"] < 1
    assert entry.state_at(1)["scale"] == 2
    scene.play(PopOut(square, to_scale=0.3, overshoot=1.1))
    assert entry.state_at(1.28)["scale"] == pytest.approx(2.2)
    assert entry.state_at(2)["scale"] == 0.6
    assert entry.state_at(2)["opacity"] == 0


@pytest.mark.parametrize(
    "direction, start",
    [
        ("up", (100, 120)),
        ("down", (100, 40)),
        ("left", (140, 80)),
        ("right", (60, 80)),
    ],
)
def test_slide_direction_means_direction_of_travel(direction, start):
    scene, square = Scene(), Square(position=(100, 80))
    scene.play(SlideIn(square, direction=direction, distance=40))
    assert scene.entries[0].state_at(0)["position"] == start
    assert scene.entries[0].state_at(1)["position"] == (100, 80)


@pytest.mark.parametrize("factory", [ZoomOut, PopOut, SlideOut])
def test_exits_resolve_from_timeline_state_after_prior_transforms(factory):
    scene, square = Scene(), Square(position=(20, 20), scale=1.2)
    scene.play(square.animate.move_to(200, 100).scale_to(2).rotate_to(25), run_time=1)
    scene.play(factory(square), run_time=1)
    entry = scene.entries[0]
    assert entry.state_at(1)["position"] == (200, 100)
    assert entry.state_at(1)["scale"] == 2
    assert entry.state_at(2)["rotation"] == 25
    assert entry.state_at(2)["opacity"] == 0
    if factory is SlideOut:
        assert entry.state_at(2)["position"] == (200, 180)
    elif factory is ZoomOut:
        assert entry.state_at(2)["scale"] == 1.2
    else:
        assert entry.state_at(2)["scale"] == 0.9


@pytest.mark.parametrize(
    "factory, key, peak",
    [
        (Pulse, "scale", 2.24),
        (Shake, "position", (214, 100)),
        (Wiggle, "rotation", 33),
    ],
)
def test_emphasis_repeatedly_returns_to_current_timeline_state(factory, key, peak):
    scene, square = Scene(), Square(position=(10, 10))
    scene.play(square.animate.move_to(200, 100).scale_to(2).rotate_to(25))
    baseline = scene.entries[0].state_at(1)
    kwargs = {"cycles": 2}
    scene.play(factory(square, **kwargs), run_time=1)
    assert scene.entries[0].state_at(1.25 if factory is Pulse else 1.125)[key] == pytest.approx(peak)
    assert scene.entries[0].state_at(2) == baseline
    scene.play(factory(square, **kwargs), run_time=1)
    assert scene.entries[0].state_at(3) == baseline


def test_bounce_and_spin_intermediate_states():
    scene, square = Scene(), Square(position=(100, 100), rotation=12, scale=2)
    scene.play(BounceIn(square, distance=100))
    assert scene.entries[0].state_at(0)["position"] == (100, 200)
    assert scene.entries[0].state_at(0.55)["position"] == (100, 82)
    assert scene.entries[0].state_at(0.78)["position"] == (100, 107)
    scene.play(SpinIn(square, angle=-40, from_scale=0.5))
    assert scene.entries[0].state_at(1)["rotation"] == -28
    assert scene.entries[0].state_at(1)["scale"] == 1
    assert scene.entries[0].state_at(2)["rotation"] == 12
    assert scene.entries[0].state_at(2)["scale"] == 2


def test_explicit_play_easing_overrides_preset_easing():
    square = Square(position=(100, 100))
    default, overridden = Scene(), Scene()
    default.play(SlideIn(square))
    overridden.play(SlideIn(square), rate_func=linear)
    assert default.entries[0].state_at(0.5)["position"] == (100, 110)
    assert overridden.entries[0].state_at(0.5)["position"] == (100, 140)
    assert [f(0) for f in (linear, smooth, ease_in, ease_out)] == [0, 0, 0, 0]
    assert [f(1) for f in (linear, smooth, ease_in, ease_out)] == [1, 1, 1, 1]


@pytest.mark.parametrize(
    "points",
    [
        ((0, 1),),
        ((0.1, 1), (1, 2)),
        ((0, 1), (0.8, 2)),
        ((0, 1), (0.5, 1), (0.5, 2), (1, 2)),
        ((0, 1), (1, 3)),
        ((0, 1), (float("nan"), 1), (1, 2)),
        ((0, 1), (0.5, -1), (1, 2)),
        ((0, 1), (0.5,), (1, 2)),
    ],
)
def test_invalid_keyframes_reject_entire_play_call(points):
    scene, good, bad = Scene(), Square(), Square()
    with pytest.raises(ValueError):
        scene.play(FadeIn(good), Animation(bad, {"scale": 2}, keyframes={"scale": points}))
    assert scene.time == 0
    assert not scene.entries


def test_keyframe_property_start_and_relative_validation():
    square = Square()
    invalid = [
        Animation(square, {"scale": 2}, keyframes={"rotation": ((0, 0), (1, 90))}),
        Animation(square, {"scale": 2}, starts={"scale": 0.5}, keyframes={"scale": ((0, 1), (1, 2))}),
        Animation(square, {"scale": 2}, relative=("position",)),
        Animation(square, {"opacity": 0}, relative=("opacity",)),
        Animation(square, {"scale": 2}, rate_func="bad"),
    ]
    for animation in invalid:
        scene = Scene()
        with pytest.raises((ValueError, TypeError)):
            scene.play(animation)
        assert not scene.entries


@pytest.mark.parametrize(
    "factory, kwargs",
    [
        (SlideIn, {"direction": "diagonal"}),
        (SlideOut, {"distance": -1}),
        (ZoomIn, {"from_scale": 0}),
        (ZoomOut, {"to_scale": float("nan")}),
        (PopIn, {"overshoot": 0.5}),
        (PopOut, {"to_scale": 0}),
        (BounceIn, {"distance": -10}),
        (SpinIn, {"angle": float("inf")}),
        (Pulse, {"cycles": 0}),
        (Shake, {"cycles": True}),
        (Shake, {"direction": "diagonal"}),
        (Wiggle, {"angle": -1}),
    ],
)
def test_invalid_preset_parameters_fail_early(factory, kwargs):
    with pytest.raises(ValueError):
        factory(Square(), **kwargs)


def test_absolute_keyframes_conflicts_and_before_start_sampling():
    scene, square = Scene(), Square(scale=1.5)
    with scene.at(2):
        scene.play(Pulse(square, cycles=2), run_time=2)
    with scene.at(3), pytest.raises(ValueError, match="chronological"):
        scene.play(ZoomOut(square))
    assert scene.entries[0].state_at(1)["scale"] == 1.5
    assert scene.entries[0].state_at(2.5)["scale"] == pytest.approx(1.68)
    assert scene.entries[0].state_at(4)["scale"] == 1.5
    assert scene.duration == 4
