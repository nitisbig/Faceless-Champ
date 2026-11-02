"""faceless_champ.draw.noise (OpenSimplex) and draw.physics (baked pymunk worlds)."""

import math
import multiprocessing
from itertools import pairwise

import pytest

pytest.importorskip("opensimplex")
pytest.importorskip("pymunk")
np = pytest.importorskip("numpy")

from PIL import Image, ImageDraw

from faceless_champ import Canvas, FunctionSource, Scene, render
from faceless_champ.draw import noise, physics


@pytest.fixture(autouse=True)
def _cache(tmp_path, monkeypatch):
    monkeypatch.setenv("FC_CACHE_DIR", str(tmp_path / "cache"))


# ---------------------------------------------------------------- noise


def test_value_is_smooth_bounded_and_seeded():
    samples = [noise.value(i / 100, 1.0) for i in range(1000)]
    assert all(-1 <= v <= 1 for v in samples) and max(samples) - min(samples) > 0.8
    assert max(abs(a - b) for a, b in pairwise(samples)) < 0.1  # continuous at 100 samples/s
    assert noise.value(3.3) == noise.value(3.3)
    assert noise.value(3.3, seed=1) != noise.value(3.3, seed=2)
    assert noise.value(3.3, lane=0) != noise.value(3.3, lane=5)
    assert -1 <= noise.value(2.0, octaves=4) <= 1


def test_shake_scales_with_amount():
    small = [noise.shake(i / 30, 2.0) for i in range(300)]
    large = [noise.shake(i / 30, 10.0) for i in range(300)]
    assert max(abs(dx) for dx, _, _ in small) <= 2.0
    assert max(abs(dx) for dx, _, _ in large) > 3.0
    assert all(isinstance(v, float) for v in small[5])
    assert noise.shake(1.0, 0.0)[:2] == (0.0, 0.0)


def test_wobble_boils_on_held_frames():
    line = [(x, 540.0) for x in range(100, 900, 40)]
    a = noise.wobble(line, 1.00, 3.0, fps=12)
    assert a == noise.wobble(line, 1.05, 3.0, fps=12)  # same 1/12 s pose
    assert a != noise.wobble(line, 1.10, 3.0, fps=12)
    assert max(math.dist(p, q) for p, q in zip(line, a)) <= 3.0 * math.sqrt(2)
    assert noise.wobble(line, 1.0, 3.0) != noise.wobble(line, 1.01, 3.0)


def test_drift_stays_in_area_and_moves_continuously():
    area = (100, 50, 800, 400)
    a = noise.drift(60, 2.0, area, seed=4)
    b = noise.drift(60, 2.0 + 1 / 30, area, seed=4)
    assert a.shape == (60, 2) and np.array_equal(a, noise.drift(60, 2.0, area, seed=4))
    assert (a[:, 0] >= 100).all() and (a[:, 0] < 900).all() and (a[:, 1] >= 50).all() and (a[:, 1] < 450).all()
    step = np.hypot(*(b - a).T)
    assert np.median(step) < 5 and np.median(step) > 0.05  # wraps can jump; most particles glide
    assert not np.array_equal(a, noise.drift(60, 2.0, area, seed=5))


def test_field_shape_and_motion():
    grid = noise.field(1.0, (32, 18))
    assert grid.shape == (18, 32) and grid.dtype == np.float32
    assert -1 <= grid.min() < grid.max() <= 1
    assert not np.array_equal(grid, noise.field(2.0, (32, 18)))


# ---------------------------------------------------------------- physics


def test_free_fall_matches_gravity():
    world = physics.World(gravity=1000)
    world.ball(100, 0, 5)
    sim = world.bake(1.0)
    body = sim.at(1.0)[0]
    assert body.kind == "ball" and body.radius == 5
    assert body.y == pytest.approx(500, rel=0.01) and body.x == pytest.approx(100)
    assert sim.at(0.5)[0].y == pytest.approx(125, rel=0.02)
    # Between stored samples the pose is interpolated, so motion stays smooth at any frame rate.
    ys = [sim.at(0.5 + i / 2000)[0].y for i in range(10)]
    assert all(b > a for a, b in pairwise(ys))


def test_bodies_spawn_late_and_leave_through_bounds():
    world = physics.World(gravity=1000, bounds=(0, -100, 500, 400))
    first = world.ball(50, 0, 5, tag="early")
    second = world.ball(150, 0, 5, at=0.5, tag="late")
    sim = world.bake(1.5)
    assert [b.index for b in sim.at(0.2)] == [first]
    assert {b.index for b in sim.at(0.6)} == {first, second}
    assert [b.tag for b in sim.at(0.6, "late")] == ["late"]
    assert sim.at(1.0, "early") == []  # fell out of the bounds at y = 300
    assert sim.positions(0.6).shape == (2, 3) and sim.positions(0.6, "late").shape == (1, 3)
    assert len(sim) == 2 and "2 bodies" in repr(sim)


def test_boxes_spin_and_rest_on_static_shapes():
    world = physics.World(gravity=0)
    world.box(0, 0, 40, 20, spin=math.pi)
    sim = world.bake(1.0)
    assert sim.at(1.0)[0].angle == pytest.approx(math.pi, rel=0.01)
    world = physics.World(gravity=2000)
    world.box(200, 400, 400, 20, static=True)
    world.walls((0, 0, 400, 300))
    world.ball(100, 100, 10, elasticity=0)
    sim = world.bake(3.0)
    assert sim.at(3.0)[0].y == pytest.approx(300 - 10 - 4, abs=1.5)  # resting on the 4 px floor segment
    assert [s.kind for s in sim.statics] == ["box", "segment", "segment", "segment"]
    assert sim.settle_time() < 2.0


def test_impacts_report_time_place_and_speed():
    world = physics.World(gravity=1000)
    world.segment((0, 500), (400, 500), 0.5, elasticity=0.5, tag="floor")
    world.ball(200, 0, 10, elasticity=0.5, tag="ball")
    sim = world.bake(3.0)
    hits = sim.impacts(100)
    fall = math.sqrt(2 * 489.5 / 1000)
    assert hits[0].time == pytest.approx(fall, abs=0.01)
    assert hits[0].speed == pytest.approx(1000 * fall, rel=0.03)
    assert hits[0].x == pytest.approx(200, abs=1) and set(hits[0].tags) == {"ball", "floor"}
    assert len(hits) >= 2 and hits[1].speed < hits[0].speed  # each bounce is softer
    assert sim.impacts(hits[0].speed + 1) == []
    assert sim.impacts(100, tag="nothing") == []
    assert len(sim.impacts(100, spacing=10.0)) == 1


def test_bake_is_deterministic_and_cached(tmp_path, monkeypatch):
    def world():
        w = physics.World(gravity=1500)
        w.walls((0, 0, 300, 300))
        for i in range(30):
            w.ball(150 + (i % 3), 20, 6, at=i * 0.05)
        return w

    first = world().bake(2.0)
    assert np.array_equal(first.poses, world().bake(2.0, cache=False).poses)
    assert len(list((tmp_path / "cache" / "physics").glob("*.npz"))) == 1

    def boom(*_):
        raise AssertionError("re-simulated instead of loading the cache")

    monkeypatch.setattr(physics.World, "_simulate", boom)
    cached = world().bake(2.0)
    assert np.array_equal(cached.poses, first.poses) and len(cached.impacts(0)) == len(first.impacts(0))
    changed = world()
    changed.ball(10, 10, 3)
    with pytest.raises(AssertionError, match="re-simulated"):
        changed.bake(2.0)


@pytest.mark.skipif("fork" not in multiprocessing.get_all_start_methods(), reason="needs fork")
@pytest.mark.filterwarnings("ignore:This process .* is multi-threaded, use of fork:DeprecationWarning")
def test_baked_world_renders_identically_in_parallel(tmp_path):
    world = physics.World(gravity=400)
    world.walls((0, 0, 160, 90))
    for i in range(8):
        world.ball(20 + i * 15, 10, 4, at=i * 0.1, velocity=(30 * (i % 2 * 2 - 1), 0))
    sim = world.bake(2.0)

    def frame(t, size):
        image = Image.new("RGB", size, "black")
        pen = ImageDraw.Draw(image)
        for body in sim.at(t):
            pen.ellipse((body.x - 4, body.y - 4, body.x + 4, body.y + 4), fill="white")
        return image

    def scene():
        sc = Scene(Canvas(160, 90, "#000000"))
        sc.add(FunctionSource(frame, size=(160, 90), duration=2.0).viewport(width=160, height=90, position=(80, 45)))
        return sc.wait_until(2.0)

    options = {"width": 160, "height": 90, "fps": 10, "antialias": 1, "crf": 0, "preset": "ultrafast"}
    serial = render(scene(), tmp_path / "serial.mp4", **options)
    parallel = render(scene(), tmp_path / "parallel.mp4", workers=2, chunk_frames=5, **options)
    assert serial.read_bytes() != b"" and _frames(serial) == _frames(parallel)


def _frames(path):
    import subprocess

    return subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
        capture_output=True,
        check=True,
    ).stdout


@pytest.mark.parametrize(
    ("build", "match"),
    [
        (lambda w: w.ball(0, 0, 0), "radius"),
        (lambda w: w.ball(0, 0, 5, at=-1), "at"),
        (lambda w: w.box(0, 0, 0, 5), "width"),
        (lambda w: w.bake(0), "duration"),
    ],
)
def test_physics_validation(build, match):
    with pytest.raises(ValueError, match=match):
        build(physics.World())
