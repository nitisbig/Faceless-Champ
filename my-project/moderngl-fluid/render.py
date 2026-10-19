"""Fifteen seconds of advected smoke, velocity tracers and vortex pressure contours."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from faceless_champ import (
    Canvas,
    Circle,
    EffectStack,
    ExportProgress,
    ExportSettings,
    GPUOptions,
    OuterGlow,
    ParticleField,
    PathData,
    Scene,
    VectorPath,
    create_renderer,
    render,
    rendering_identity,
)

ROOT = Path(__file__).resolve().parent
DURATION = 15.0
DT = 1 / 60
COUNT = 1800
COLORS = ("#126A9B", "#168FB6", "#26B9D0", "#4CE4E6", "#ACEFE8", "#FFD298")


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def cores(t):
    return (
        (1030 + 90 * math.sin(t * 0.43), 385 + 35 * math.sin(t * 0.7), 1),
        (1160 + 100 * math.sin(t * 0.35 + 1), 695 + 40 * math.cos(t * 0.6), -1),
    )


def velocity(p, t):
    """An artistic incompressible field: uniform drift, regularized vortices, curl waves.

    This is deterministic tracer advection, not a Navier–Stokes pressure solve.
    """
    x, y = p[..., 0], p[..., 1]
    vx = np.full_like(x, 155.0)
    vy = np.zeros_like(y)
    strength = 0.18 + 0.82 * smooth((t - 1) / 4)
    for cx, cy, sign in cores(t):
        dx, dy = x - cx, y - cy
        omega = sign * 150000 * strength / (dx * dx + dy * dy + 95**2)
        vx -= omega * dy
        vy += omega * dx
    # Curl of a scalar wave potential; turbulence grows toward the final beat.
    a = 10 + 48 * smooth((t - 5) / 6)
    for kx, ky, phase in ((0.009, 0.012, 0.7), (0.019, -0.016, -1.1), (0.033, 0.024, 1.7)):
        wave = np.cos(kx * x + ky * y + phase * t)
        vx += a * ky / 0.02 * wave
        vy -= a * kx / 0.02 * wave
    return np.stack((vx, vy), axis=-1)


def bake():
    """Fixed-step midpoint integration makes seeking independent of export FPS."""
    rng = np.random.default_rng(20261019)
    p = np.column_stack((rng.uniform(80, 1840, COUNT), rng.normal(540, 105, COUNT)))
    history = np.empty((round(DURATION / DT) + 1, COUNT, 2), dtype=np.float32)
    history[0] = p
    inlet_y = rng.normal(540, 95, COUNT)
    for i in range(1, len(history)):
        t = (i - 1) * DT
        mid = p + velocity(p, t) * (DT / 2)
        p += velocity(mid, t + DT / 2) * DT
        reset = (p[:, 0] > 1890) | (p[:, 0] < 30) | (p[:, 1] < 75) | (p[:, 1] > 1005)
        p[reset, 0] = 55
        p[reset, 1] = inlet_y[reset]
        history[i] = p
    return history


def path(scene, commands, color, width, opacity):
    if commands and opacity > 0.0001:
        scene.add(
            VectorPath(
                PathData(tuple(commands)),
                fill=None,
                stroke=color,
                stroke_width=width,
                line_cap="round",
                opacity=float(opacity),
            )
        )


def polyline(points):
    return [("M" if i == 0 else "L", float(x), float(y)) for i, (x, y) in enumerate(points)]


class FluidScene(Scene):
    def __init__(self):
        super().__init__(Canvas(1920, 1080, "#000000"))
        self.history = bake()

    def construct(self):
        self.wait_until(DURATION)

    def sample(self, t):
        if not math.isfinite(t) or not 0 <= t <= DURATION:
            raise ValueError("source time must be in [0, 15]")
        scene = Scene(self.canvas)
        envelope = float(smooth(t / 0.8) * smooth((DURATION - t) / 1.2))
        # Small GPU-instanced motes give the black negative space a sense of depth.
        scene.add(
            ParticleField(
                width=1700,
                height=840,
                position=(960, 540),
                seed=71,
                count=700,
                radius=0.85,
                velocity=(28, -3),
                lifetime=7,
                color="#387A95",
                opacity=0.20 * envelope,
            )
        )
        index = min(int(t / DT), len(self.history) - 2)
        fraction = t / DT - index
        current = self.history[index] * (1 - fraction) + self.history[index + 1] * fraction
        # Pressure proxies: sparse deformed isobars around the two rotating cores.
        pressure_alpha = envelope * float(smooth((t - 2.5) / 2))
        for cx, cy, sign in cores(t):
            color = "#257CBE" if sign == 1 else "#E69C69"
            for ring in range(6):
                r = 43 + ring * 28
                points = []
                for a in np.linspace(0, math.tau, 129):
                    rr = r * (1 + 0.055 * math.sin(3 * a + t * sign))
                    points.append((cx + rr * math.cos(a), cy + 0.87 * rr * math.sin(a)))
                path(scene, polyline(points), color, 0.85, pressure_alpha * (0.25 - ring * 0.026))
            scene.add(
                Circle(
                    3,
                    fill=color,
                    stroke=None,
                    position=(cx, cy),
                    opacity=pressure_alpha,
                    effects=EffectStack(glow=OuterGlow(color, 14, 0.65)),
                )
            )
        # Shared velocity arrows remain quiet behind the advected material.
        grid = np.array([(x, y) for y in range(210, 920, 100) for x in range(200, 1800, 115)], dtype=float)
        vectors = velocity(grid, t)
        commands = []
        for p, v in zip(grid, vectors):
            speed = np.linalg.norm(v)
            direction = v / max(speed, 1)
            length = min(32, 9 + speed * 0.065)
            tip = p + direction * length / 2
            tail = p - direction * length / 2
            side = np.array((-direction[1], direction[0]))
            commands.extend(polyline((tail, tip, tip - direction * 5 + side * 3)))
            commands.extend(polyline((tip, tip - direction * 5 - side * 3)))
        path(scene, commands, "#5B9DA9", 1.1, envelope * (0.27 - 0.17 * float(smooth(t / 7))))
        # Long exposure filaments. Reset discontinuities never create screen-spanning lines.
        trails = self.history[np.maximum(0, index - np.arange(32, -1, -2))].copy()
        trails[-1] = current
        speeds = np.linalg.norm(velocity(current, t), axis=1)
        buckets = np.clip((speeds / 430 * len(COLORS)).astype(int), 0, len(COLORS) - 1)
        edge = np.minimum.reduce((current[:, 0] - 40, 1890 - current[:, 0], current[:, 1] - 70, 1010 - current[:, 1]))
        for bucket, color in enumerate(COLORS):
            for band in range(3):
                commands = []
                for particle in np.flatnonzero((buckets == bucket) & (edge > 24)):
                    points = trails[band * 5 : band * 5 + 7, particle]
                    if np.max(np.linalg.norm(np.diff(points, axis=0), axis=1)) < 100:
                        commands.extend(polyline(points))
                # A soft broad stroke creates smoke volume, with a fine luminous thread.
                path(scene, commands, color, 11 - band * 2, envelope * (0.019 + band * 0.012))
                path(scene, commands, color, 0.65 + band * 0.15, envelope * (0.12 + band * 0.16))
        scene.wait_until(DURATION)
        return scene


def build_scene():
    return FluidScene()


class FluidRenderer:
    """Project-local source-time adapter; Faceless Champ owns composition and GL."""

    def __init__(self):
        self.native = create_renderer("moderngl", antialias=1, gpu=GPUOptions(frame_cache_mb=0))
        self.identity = self.native.identity

    def validate(self, scene):
        self.native.validate(scene.sample(7.5))

    def frame(self, scene, time, size):
        return self.native.frame(scene.sample(time), time, size)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.native.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="One-second turbulence sample at 9–10s")
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"))
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and (not math.isfinite(args.frame) or not 0 <= args.frame <= DURATION):
        parser.error("frame must be in [0, 15]")
    if args.range and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 15")
    if args.fps <= 0:
        parser.error("fps must be positive")
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "moderngl-fluid.mp4"
    )
    if output.exists() and not args.overwrite:
        parser.error("output exists; pass --overwrite")
    if output.suffix.lower() != (".png" if args.frame is not None else ".mp4"):
        parser.error("output must use .png for a frame or .mp4 for video")
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = build_scene()
    settings = ExportSettings(backend="moderngl", antialias=1, quality=args.quality, fps=args.fps)
    source_range = args.range or ([9, 10] if args.preview else [0, DURATION])
    with FluidRenderer() as renderer:
        print(json.dumps(renderer.identity), flush=True)
        if args.frame is not None:
            source_range = [args.frame, args.frame]
            renderer.frame(scene, args.frame, settings.dimensions(scene.canvas)).convert("RGB").save(output)
        else:
            with ExportProgress() as progress:
                render(
                    scene,
                    output,
                    settings=settings,
                    renderer=renderer,
                    start_time=source_range[0],
                    end_time=source_range[1],
                    overwrite=args.overwrite,
                    progress=progress,
                )
        evidence = {
            "scene_duration": scene.duration,
            "source_range": source_range,
            "rendering": rendering_identity("moderngl", renderer=renderer),
            "stats": dict(renderer.native.stats),
            "full_export_verified": False,
        }
    output.with_suffix(".json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
