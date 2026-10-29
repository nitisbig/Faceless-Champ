"""Regression coverage for narrated engineering behavior, not drawing internals."""

import itertools
import math

import numpy as np
import pytest
from scene import END
from scene import physics as p
from scene.equations import BEATS
from scene.model import components, make_view
from scene.story import RoadsterRenderer, build_master, model_state
from scene.timing import CHAPTERS, SHOTS, TRACK, shot_at


def test_exact_cues_cover_the_contiguous_source_clock():
    assert len(TRACK.cues) == 1975
    assert SHOTS[0].start == 0
    assert SHOTS[-1].end == 738.3
    assert sum(s.end_cue - s.cue + 1 for s in SHOTS) == 1975
    for a, b in itertools.pairwise(SHOTS):
        assert a.end == b.start == TRACK.cue(b.cue).start
        assert shot_at(b.start).id == b.id
    assert CHAPTERS[4] == (268.88, 353.4)


def test_intentional_millisecond_overlaps_are_preserved():
    overlaps = [(a.index, b.index, a.end - b.start) for a, b in zip(TRACK.cues, TRACK.cues[1:]) if a.end > b.start]
    assert [(a, b) for a, b, _ in overlaps] == [(436, 437), (670, 671), (824, 825), (1037, 1038), (1240, 1241)]
    assert all(abs(d - 0.001) < 1e-9 for _, _, d in overlaps)


def test_equation_reveals_are_within_their_narrated_chapters():
    for chapter, beats in BEATS.items():
        lo, hi = CHAPTERS[chapter - 1]
        assert all(lo <= beat.time < hi for beat in beats)
        assert [b.cue for b in beats] == sorted(b.cue for b in beats)


def test_single_master_audio_with_unshifted_decoder_tail():
    master = build_master()
    assert master.duration == END
    assert len(master.audio) == 1 and master.audio[0].start == 0
    assert master.audio[0].trim_start == 0
    assert master.audio[0].trim_end == pytest.approx(738.2726666666666)


def test_friction_capacity_does_not_become_an_extra_applied_force():
    state = p.incline(math.pi / 2, suction=p.SUCTION)
    assert state["normal"] == pytest.approx(33354)
    assert state["capacity"] == pytest.approx(33354)
    assert state["friction"] == pytest.approx(16677)
    assert p.incline(math.pi / 2)["sliding"]
    assert not p.incline(math.pi / 4)["sliding"]


def test_inside_loop_balance_in_world_coordinates():
    for a in np.linspace(0, math.pi, 101):
        s = p.loop(a)
        net = (s["normal"] - p.SUCTION) * s["inward"] + np.array((0, 0, -p.WEIGHT)) + s["friction"] * s["tangent"]
        np.testing.assert_allclose(net, p.MASS * 12 * s["inward"], atol=1e-8)
    assert p.loop(math.pi)["normal"] == pytest.approx(37077)
    assert p.loop(math.pi, speed=0)["normal"] == pytest.approx(16677)


def test_half_roll_position_rate_and_torque_reversal():
    assert p.roll(0)["theta"] == 0 and p.roll(0)["omega"] == 0
    assert p.roll(0.8)["theta"] == pytest.approx(math.pi / 2)
    assert p.roll(0.7999)["torque"] > 0 and p.roll(0.8)["torque"] < 0
    assert p.roll(1.6)["theta"] == pytest.approx(math.pi)
    assert p.roll(1.6)["omega"] == 0
    assert p.TORQUE / p.SEPARATION == pytest.approx(2617.993877991494)
    eps = 1e-5
    for t in (0.2, 0.5, 1.0, 1.4):
        derivative = (p.roll(t + eps)["theta"] - p.roll(t - eps)["theta"]) / (2 * eps)
        assert derivative == pytest.approx(p.roll(t)["omega"], rel=1e-8)


def test_hover_thrust_does_not_stop_a_falling_vehicle():
    a, b = p.hover_demo(0.1), p.hover_demo(0.5)
    assert a["thrust"] == b["thrust"] == p.WEIGHT
    assert a["velocity"] == b["velocity"] == -14
    assert b["height"] < a["height"]
    c = p.hover_demo(0.9)
    assert c["velocity"] > b["velocity"] and c["velocity"] < 0
    assert c["thrust"] == 2 * p.WEIGHT
    assert model_state(9, 617.24)[0] == "hover"


def test_landing_is_a_calculated_endpoint_and_contact_clamps_height():
    switch = math.sqrt(20 / p.G)
    a = p.landing(switch)
    assert a["height"] == pytest.approx(10)
    assert a["velocity"] == pytest.approx(-math.sqrt(2 * p.G * 10))
    b = p.landing(2 * switch)
    assert b["contact"] and not b["impact"]
    assert b["height"] == 0 and b["velocity"] == 0
    assert p.landing(100)["height"] == 0
    assert p.landing(100, assisted=False)["velocity"] == 0
    assert p.landing(100, assisted=False)["impact_velocity"] == pytest.approx(-math.sqrt(2 * p.G * 20))


def test_release_has_no_ghost_contact_or_suction_and_preserves_velocity():
    left = p.replay(p.RELEASE_TIME - 1e-7)
    right = p.replay(p.RELEASE_TIME)
    np.testing.assert_allclose(left.position, right.position, atol=2e-6)
    np.testing.assert_allclose(left.velocity, right.velocity, atol=2e-6)
    assert right.normal == right.suction == 0
    assert right.velocity[0] == -12
    assert p.replay(p.REPLAY_TIME).velocity[0] == -12  # touchdown still has horizontal momentum


def test_cutaway_meshes_are_closed_and_wheels_contact_the_plane():
    data = components()
    for name in ("body", "canopy", "chassis", "tanks", "tires", "skirts", "nozzles"):
        assert data[name].is_manifold, name
    assert data["tires"].bounds[4] == pytest.approx(-p.CG_HEIGHT, abs=1e-6)
    assert len(data["rotors"]) == 4
    view = make_view("nozzle")
    assert view.duration == 4


def test_arch_tracks_can_seek_backwards_and_share_the_roll_state():
    view = make_view("roll")
    state = view.component.state_at(0.4)
    view.component.state_at(1.5)
    again = view.component.state_at(0.4)
    assert state == again
    assert state["parts"]["body"]["rotation"][0] == pytest.approx(p.roll(0.4)["theta"] * 180 / math.pi, abs=0.02)


def test_hold_cache_matches_a_fresh_arbitrary_time_sample():
    master = build_master()
    with RoadsterRenderer(geometry=False) as cached:
        cached.frame(master, 85.4, (960, 540))
        image = cached.frame(master, 85.41, (960, 540))
    with RoadsterRenderer(geometry=False) as fresh:
        expected = fresh.frame(master, 85.41, (960, 540))
    assert image.tobytes() == expected.tobytes()


def test_motion_and_equation_fades_are_not_frozen_by_the_hold_cache():
    with RoadsterRenderer(geometry=False) as renderer:
        master = build_master()
        before = renderer.frame(master, 84.6, (960, 540))
        after = renderer.frame(master, 84.9, (960, 540))
        assert before.tobytes() != after.tobytes()


def test_native_layout_audit_matches_rendered_glyph_bounds():
    with RoadsterRenderer(geometry=False) as renderer:
        renderer.frame(build_master(), 666, (3840, 2160))
        expected = renderer.last_layout
        measured = renderer.layout_at(666)
        assert measured == expected
        assert not renderer.measuring
        from scene.qa import layout_findings

        assert not layout_findings(measured)


def test_curvature_camera_keeps_force_labels_clear_of_the_math_column():
    from scene.qa import layout_findings

    with RoadsterRenderer(geometry=False) as renderer:
        for time in (285.52, 285.553333333333, 286, 286.12, 286.5, 287.5, 292.5):
            assert not layout_findings(renderer.layout_at(time)), time
