"""2D rigid-body physics (pymunk), simulated once ahead of time and sampled by time.

    from faceless_champ.draw import physics

    world = physics.World(gravity=1800, bounds=(0, -200, 1920, 1280))
    world.walls((560, 80, 800, 960))                         # floor and sides of a box
    world.peg(960, 300, 6)                                   # a static circle
    for i in range(150):
        world.ball(960 + (i % 3) - 1, 40, 8, at=i * 0.08, tag="bead")
    sim = world.bake(16.0)                                   # cached on disk after the first run

    def draw(t, size):
        fr = Frame(size)
        for body in sim.at(t):                               # live bodies, interpolated
            fr.circle(body.x, body.y, body.radius, "primary", fill=True)
        return fr.finish()

    for hit in sim.impacts(min_speed=250):                   # land a click on each strong hit
        scene.add_sfx("tick.wav", hit.time, volume=min(1, hit.speed / 1500))

Coordinates are design pixels with y down, so positive gravity falls. Frame functions render out of
order and in parallel chunks, so a live simulation would differ between workers. Instead ``bake``
steps at a fixed rate (240 Hz by default), stores every body's pose, and caches the result
(``FC_CACHE_DIR`` or ``~/.cache/faceless_champ/physics``) keyed by the world's contents. Bake at
import or build time, before rendering starts. Needs ``faceless-champ[motion]``.
"""

from __future__ import annotations

import hashlib
import math
import os
from dataclasses import dataclass
from pathlib import Path

from ..components import finite

__all__ = ["Body", "Impact", "Simulation", "Static", "World", "cache_root"]

_FORMAT = 1  # bump when the baked data layout changes


def cache_root() -> Path:
    return Path(os.environ.get("FC_CACHE_DIR") or Path.home() / ".cache" / "faceless_champ") / "physics"


def _pymunk():
    try:
        import pymunk
    except ImportError as exc:
        raise RuntimeError("Physics needs faceless-champ[motion] (pymunk)") from exc
    return pymunk


@dataclass(frozen=True, slots=True)
class Body:
    """A dynamic body's pose at one time. ``angle`` is in radians, clockwise on screen."""

    index: int
    kind: str  # "ball" or "box"
    x: float
    y: float
    angle: float
    radius: float
    width: float
    height: float
    tag: str


@dataclass(frozen=True, slots=True)
class Static:
    """A fixed shape for drawing: kind "segment" (a, b, radius), "peg" (a=center, radius) or "box"."""

    kind: str
    a: tuple[float, float]
    b: tuple[float, float]
    radius: float
    width: float
    height: float
    angle: float
    tag: str


@dataclass(frozen=True, slots=True)
class Impact:
    time: float
    x: float
    y: float
    speed: float  # closing speed along the contact normal, px/s
    tags: tuple[str, str]


class World:
    """Describe bodies, then ``bake``. Elasticity 0-1 (bounce), friction 0 and up."""

    def __init__(
        self,
        gravity: float | tuple[float, float] = 1800.0,
        *,
        rate: int = 240,
        damping: float = 1.0,
        iterations: int = 20,
        bounds: tuple[float, float, float, float] | None = None,
    ):
        gx, gy = (0.0, gravity) if isinstance(gravity, (int, float)) else gravity
        self.gravity = (finite(gx, "gravity x"), finite(gy, "gravity y"))
        self.rate = int(finite(rate, "rate", 30))
        self.damping = finite(damping, "damping", 0)
        self.iterations = int(finite(iterations, "iterations", 1))
        self.bounds = (
            None if bounds is None else tuple(float(v) for v in bounds)
        )  # x, y, w, h; leaving it removes a body
        self.dynamic: list[tuple] = []
        self.statics: list[tuple] = []

    def ball(self, x, y, radius, *, at=0.0, velocity=(0.0, 0.0), mass=1.0, elasticity=0.4, friction=0.6, tag="ball"):
        finite(radius, "radius", 0.01)
        finite(at, "at", 0)
        finite(mass, "mass", 1e-6)
        self.dynamic.append(("ball", x, y, radius, radius * 2, radius * 2, 0.0, at, *velocity, 0.0, mass,
                             elasticity, friction, tag))  # fmt: skip
        return len(self.dynamic) - 1

    def box(
        self, x, y, width, height, *, angle=0.0, at=0.0, velocity=(0.0, 0.0), spin=0.0, mass=1.0,
        elasticity=0.3, friction=0.7, static=False, tag="box",
    ):  # fmt: skip
        """A rectangle centered on (x, y); ``angle`` and ``spin`` in radians and radians per second."""
        finite(width, "width", 0.01)
        finite(height, "height", 0.01)
        if static:
            self.statics.append(("box", (x, y), (x, y), 0.0, width, height, angle, elasticity, friction, tag))
            return None
        finite(at, "at", 0)
        finite(mass, "mass", 1e-6)
        self.dynamic.append(("box", x, y, 0.0, width, height, angle, at, *velocity, spin, mass, elasticity, friction,
                             tag))  # fmt: skip
        return len(self.dynamic) - 1

    def segment(self, a, b, radius=2.0, *, elasticity=0.4, friction=0.6, tag="segment"):
        self.statics.append(("segment", tuple(a), tuple(b), radius, 0.0, 0.0, 0.0, elasticity, friction, tag))

    def peg(self, x, y, radius, *, elasticity=0.4, friction=0.4, tag="peg"):
        self.statics.append(("peg", (x, y), (x, y), radius, 0.0, 0.0, 0.0, elasticity, friction, tag))

    def walls(self, area, *, top=False, radius=4.0, **options):
        """Floor and side walls (and a lid with ``top=True``) around ``area`` (x, y, width, height)."""
        x, y, w, h = area
        corners = [(x, y), (x, y + h), (x + w, y + h), (x + w, y)]
        for a, b in zip(corners, corners[1:] + (corners[:1] if top else [])):
            self.segment(a, b, radius, **options)

    def _key(self, duration: float) -> str:
        pymunk = _pymunk()
        spec = (_FORMAT, pymunk.version, self.gravity, self.rate, self.damping, self.iterations, self.bounds,
                self.dynamic, self.statics, duration)  # fmt: skip
        return hashlib.sha256(repr(spec).encode()).hexdigest()[:20]

    def bake(self, duration: float, *, cache: bool = True) -> Simulation:
        """Simulate ``duration`` seconds (or load the cached result) and return a Simulation."""
        duration = finite(duration, "duration", 0.001)
        path = cache_root() / f"{self._key(duration)}.npz" if cache else None
        if path is not None and path.is_file():
            return Simulation._load(path, self)
        data = self._simulate(duration)
        if path is not None:
            import numpy as np

            path.parent.mkdir(parents=True, exist_ok=True)
            partial = path.with_name(f".{path.stem}.partial.npz")
            np.savez(partial, **data)
            partial.replace(path)
        return Simulation(self, **data)

    def _simulate(self, duration: float) -> dict:
        import numpy as np

        pymunk = _pymunk()
        space = pymunk.Space()
        space.gravity = self.gravity
        space.damping = self.damping
        space.iterations = self.iterations
        tags = {}

        for kind, a, b, radius, width, height, angle, elasticity, friction, tag in self.statics:
            body = space.static_body
            if kind == "segment":
                shape = pymunk.Segment(body, a, b, radius)
            elif kind == "peg":
                shape = pymunk.Circle(body, radius, a)
            else:
                corners = [(sx * width / 2, sy * height / 2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                transform = pymunk.Transform.translation(*a).rotated(angle)
                shape = pymunk.Poly(body, corners, transform)
            shape.elasticity, shape.friction = elasticity, friction
            tags[shape] = tag
            space.add(shape)

        steps = math.ceil(duration * self.rate - 1e-9)
        count = len(self.dynamic)
        poses = np.zeros((steps + 1, count, 3), np.float32)
        born = np.array([min(steps, math.ceil(spec[7] * self.rate - 1e-9)) for spec in self.dynamic], np.int32)
        died = np.full(count, steps + 1, np.int32)
        bodies: list = [None] * count
        order = sorted(range(count), key=lambda i: (born[i], i))
        impacts: list[tuple] = []
        clock = {"step": 0}

        def begin(arbiter, _space, _data):
            a, b = arbiter.shapes
            normal = arbiter.contact_point_set.normal
            closing = abs((a.body.velocity - b.body.velocity).dot(normal))
            points = arbiter.contact_point_set.points
            x, y = points[0].point_a if points else a.body.position
            impacts.append((clock["step"] / self.rate, x, y, closing, tags.get(a, ""), tags.get(b, "")))

        space.on_collision(begin=begin)
        cursor = 0
        x0, y0, w, h = self.bounds or (0, 0, 0, 0)
        for step in range(steps + 1):
            clock["step"] = step
            while cursor < count and born[order[cursor]] <= step:
                i = order[cursor]
                kind, x, y, radius, width, height, angle, _, vx, vy, spin, mass, elasticity, friction, tag = (
                    self.dynamic[i]
                )
                if kind == "ball":
                    body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
                    shape = pymunk.Circle(body, radius)
                else:
                    body = pymunk.Body(mass, pymunk.moment_for_box(mass, (width, height)))
                    shape = pymunk.Poly.create_box(body, (width, height))
                body.position, body.angle = (x, y), angle
                body.velocity, body.angular_velocity = (vx, vy), spin
                shape.elasticity, shape.friction = elasticity, friction
                tags[shape] = tag
                space.add(body, shape)
                bodies[i] = (body, shape)
                cursor += 1
            for i in range(count):
                if bodies[i] is None:
                    continue
                body = bodies[i][0]
                px, py = body.position
                poses[step, i] = (px, py, body.angle)
                if self.bounds and not (x0 <= px <= x0 + w and y0 <= py <= y0 + h):
                    space.remove(body, bodies[i][1])
                    bodies[i] = None
                    died[i] = step
            if step < steps:
                space.step(1 / self.rate)
        impact_times = np.array([v[0] for v in impacts], np.float64)
        impact_xyv = np.array([v[1:4] for v in impacts], np.float32).reshape(-1, 3)
        impact_tags = np.array([f"{v[4]}\n{v[5]}" for v in impacts], dtype=str)
        return {
            "poses": poses,
            "born": born,
            "died": died,
            "impact_times": impact_times,
            "impact_xyv": impact_xyv,
            "impact_tags": impact_tags,
            "duration": np.array(duration),
        }


class Simulation:
    """Baked poses. ``at(t)`` returns live bodies; ``impacts()`` lists collisions for sound design."""

    def __init__(self, world: World, *, poses, born, died, impact_times, impact_xyv, impact_tags, duration):
        self.world = world
        self.rate = world.rate
        self.duration = float(duration)
        self.poses, self.born, self.died = poses, born, died
        self._impact_times, self._impact_xyv, self._impact_tags = impact_times, impact_xyv, impact_tags
        self.statics = tuple(
            Static(kind, tuple(a), tuple(b), radius, width, height, angle, tag)
            for kind, a, b, radius, width, height, angle, _, _, tag in world.statics
        )

    @classmethod
    def _load(cls, path: Path, world: World) -> Simulation:
        import numpy as np

        with np.load(path) as data:
            return cls(world, **{name: data[name] for name in data.files})

    def _sample(self, t: float):
        position = min(max(t, 0.0), self.duration) * self.rate
        step = min(int(position), len(self.poses) - 1)
        nxt = min(step + 1, len(self.poses) - 1)
        alive = (self.born <= step) & (self.died > step)
        frac = position - step
        # Bodies born or removed between the two samples hold their last known pose.
        blend = (self.died > nxt) & (self.born <= step)
        pose = self.poses[step].astype("float64")
        pose[blend] += (self.poses[nxt][blend] - self.poses[step][blend]) * frac
        return alive, pose

    def positions(self, t: float, tag: str | None = None):
        """(x, y, angle) rows for live bodies at ``t`` (optionally one tag), as a numpy array."""
        alive, pose = self._sample(t)
        if tag is not None:
            alive &= [spec[-1] == tag for spec in self.world.dynamic]
        return pose[alive]

    def at(self, t: float, tag: str | None = None) -> list[Body]:
        alive, pose = self._sample(t)
        bodies = []
        for i in alive.nonzero()[0]:
            kind, _, _, radius, width, height, *_rest, body_tag = self.world.dynamic[i]
            if tag is None or body_tag == tag:
                x, y, angle = pose[i]
                bodies.append(Body(int(i), kind, float(x), float(y), float(angle), radius, width, height, body_tag))
        return bodies

    def impacts(self, min_speed: float = 200.0, *, tag: str | None = None, spacing: float = 0.04) -> list[Impact]:
        """Collisions closing faster than ``min_speed`` px/s, at least ``spacing`` seconds apart (for SFX)."""
        found, last = [], -math.inf
        for when, (x, y, speed), tags in zip(self._impact_times, self._impact_xyv, self._impact_tags):
            pair = tuple(str(tags).split("\n"))
            if speed < min_speed or (tag is not None and tag not in pair) or when - last < spacing:
                continue
            found.append(Impact(float(when), float(x), float(y), float(speed), pair))
            last = when
        return found

    def settle_time(self, speed: float = 5.0) -> float:
        """The last time any live body moved faster than ``speed`` px/s (0 when nothing ever moves)."""
        import numpy as np

        steps = np.arange(len(self.poses) - 1)[:, None]
        alive = (self.born <= steps) & (self.died > steps + 1)
        moved = np.hypot(*np.moveaxis(np.diff(self.poses[:, :, :2], axis=0), -1, 0)) * self.rate
        indices = (np.where(alive, moved, 0) > speed).any(axis=1).nonzero()[0]
        return float(indices[-1] + 1) / self.rate if len(indices) else 0.0

    def __len__(self) -> int:
        return len(self.world.dynamic)

    def __repr__(self) -> str:
        return f"Simulation({len(self)} bodies, {len(self.statics)} statics, {self.duration:g}s at {self.rate} Hz)"
