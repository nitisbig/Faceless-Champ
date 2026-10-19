"""Sixty seconds of native Skia black-hole graphics on a black canvas."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from faceless_champ import (
    Arrow,
    Canvas,
    Circle,
    ExportProgress,
    ExportSettings,
    GradientStop,
    LinearGradient,
    PathData,
    RadialGradient,
    Scene,
    ShadowStyle,
    Text,
    VectorPath,
    create_renderer,
    render,
    rendering_identity,
    save_frame,
)

ROOT = Path(__file__).resolve().parent
DURATION = 60.0
TAU = math.tau
CYAN, GOLD = "#7CDCEB", "#FFBA70"


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def window(t, start, end, fade=2):
    return smooth((t - start) / fade) * smooth((end - t) / fade)


def curve(points, closed=False):
    """Interpolating cubic spline, including smooth joins around closed contours."""
    commands = [("M", *points[0])]
    for i in range(len(points) if closed else len(points) - 1):
        p0 = points[(i - 1) % len(points)] if closed or i else points[0]
        p1, p2 = points[i], points[(i + 1) % len(points)]
        p3 = points[(i + 2) % len(points)] if closed or i + 2 < len(points) else points[-1]
        a = [p1[k] + (p2[k] - p0[k]) / 6 for k in (0, 1)]
        b = [p2[k] - (p3[k] - p1[k]) / 6 for k in (0, 1)]
        commands.append(("C", *a, *b, *p2))
    if closed:
        commands.append(("Z",))
    return PathData(tuple(commands))


def line(scene, points, color, width=1, opacity=1, glow=0):
    scene.add(
        VectorPath(
            curve(points),
            stroke=color,
            stroke_width=width,
            opacity=opacity,
            shadow=ShadowStyle(color + "70", glow, (0, 0)) if glow else None,
        )
    )


def text(scene, value, xy, opacity, color=CYAN, size=25):
    scene.add(Text(value, position=xy, font_size=size, text_engine="skia", color=color, opacity=opacity))


_rng = random.Random(72)
STARS = [(_rng.uniform(55, 1865), _rng.uniform(50, 1030), _rng.uniform(0.65, 1.7), _rng.random()) for _ in range(115)]


class BlackHole(Scene):
    def construct(self):
        self.wait_until(DURATION)

    def sample(self, t):
        if not math.isfinite(t) or not 0 <= t <= DURATION:
            raise ValueError("source time must be in [0, 60]")
        scene = Scene(Canvas(1920, 1080, "#000000"))
        fade = window(t, 0, 60, 2)
        scale = 0.92 + 0.08 * smooth(t / 55)
        cx, cy = 960, 490

        def project(x, y):
            return cx + x * scale, cy + y * scale

        for x, y, r, phase in STARS:
            scene.add(
                Circle(
                    r,
                    position=(x, y),
                    fill="#CDDEF1",
                    stroke=None,
                    opacity=fade * (0.18 + 0.19 * (1 + math.sin(t * 0.35 + phase * TAU)) / 2),
                )
            )

        # A diagrammatic embedding grid, projected in perspective behind the disk.
        grid = window(t, 14, 39, 4) * fade
        if grid:

            def mesh(x, z):
                r = math.hypot(x, z)
                depression = 210 / (1 + (r / 210) ** 1.65)
                return project(x, 160 + z * 0.31 + depression)

            for z in range(-650, 1000, 90):
                line(scene, [mesh(x, z) for x in range(-860, 861, 35)], "#366574", 1.2, grid * 0.66)
            for x in range(-810, 811, 90):
                line(scene, [mesh(x, z) for z in range(-650, 1001, 35)], "#366574", 1.2, grid * 0.66)

        # Radial transparent paint creates a diffuse halo with black negative space.
        scene.add(
            Circle(
                550 * scale,
                position=project(0, 0),
                stroke=None,
                opacity=fade * 0.60,
                fill=RadialGradient(
                    (
                        GradientStop(0, "#FFB77800"),
                        GradientStop(0.23, "#E8894035"),
                        GradientStop(0.52, "#8D421015"),
                        GradientStop(1, "#00000000"),
                    )
                ),
            )
        )
        # Lensed far-side disk: a bright arch lifted over the silhouette.
        for i in range(17):
            r = 146 + i * 5
            points = [project(r * math.cos(a), -r * 1.08 * math.sin(a)) for a in [j * math.pi / 64 for j in range(65)]]
            line(scene, points, "#FFA854", 2.5, fade * (0.16 + 0.60 * math.exp(-i / 5)), 9 if i in (0, 4) else 0)

        # Thin annular ribbons: genuine native gradients, with animated spiral texture.
        for i in range(30):
            r = 178 + i * 10.8
            points = []
            for j in range(97):
                a = j * TAU / 96
                wobble = 2.8 * math.sin(3 * a - t * 0.65 + i * 0.35)
                points.append(project((r + wobble) * math.cos(a), (r + wobble) * 0.245 * math.sin(a)))
            inner = [(cx + (x - cx) * (1 - 9.4 / r), cy + (y - cy) * (1 - 9.4 / r)) for x, y in points]
            path = curve(points + inner[::-1], closed=True)
            strength = (1 - i / 38) * fade
            scene.add(
                VectorPath(
                    path,
                    fill=LinearGradient(
                        (
                            GradientStop(0, "#98451D"),
                            GradientStop(0.36, "#FFAA56"),
                            GradientStop(0.68, "#FFF0B9"),
                            GradientStop(1, "#DF7132"),
                        ),
                        angle=8 + 4 * math.sin(t * 0.12),
                    ),
                    stroke=None,
                    opacity=strength * 0.90,
                )
            )
        # Orbiting hot knots follow the disk and are occluded by the central silhouette.
        for i in range(26):
            r = 210 + (i * 67 % 265)
            a = i * 2.39996 + t * (0.23 + (480 - r) / 700)
            x, y = project(r * math.cos(a), r * 0.245 * math.sin(a))
            scene.add(
                Circle(
                    1.4 + i % 3 * 0.45,
                    position=(x, y),
                    fill="#FFF2C9",
                    stroke=None,
                    opacity=fade * 0.78,
                    shadow=ShadowStyle("#FFB768A0", 8, (0, 0)),
                )
            )
        scene.add(Circle(117 * scale, position=project(0, 0), fill="#000000", stroke=None, opacity=fade))
        scene.add(
            Circle(
                119 * scale,
                position=project(0, 0),
                fill=None,
                stroke="#FFD69C",
                stroke_width=2.1,
                opacity=fade * 0.9,
                shadow=ShadowStyle("#FF9B55B0", 13, (0, 0)),
            )
        )

        # Illustrative trajectories, not a numerical relativistic ray tracer.
        rays = window(t, 32, 54, 3) * fade
        if rays:
            paths = [
                [(-830, -245), (-480, -239), (-195, -198), (65, -213), (345, -310), (800, -405)],
                [
                    (-830, -145),
                    (-490, -140),
                    (-240, -123),
                    (-142, -160),
                    (-47, -223),
                    (122, -253),
                    (270, -220),
                    (480, -96),
                    (790, 130),
                ],
                [(-830, 230), (-530, 212), (-290, 156), (-160, 71), (-119, 28)],
            ]
            for i, path in enumerate(paths):
                points = [project(*p) for p in path]
                line(scene, points, CYAN if i < 2 else GOLD, 2.3, rays * 0.9, 8)
                # Smoothly moving wave packets along the same cubic curve's control samples.
                # Use a dense spline evaluation for exact agreement with the drawn trajectory.
                for j in range(3):
                    u = ((t - 32) * 0.11 + j / 3 + i * 0.19) % 1
                    k = min(int(u * (len(points) - 1)), len(points) - 2)
                    f = u * (len(points) - 1) - k
                    p0, p1 = points[max(0, k - 1)], points[k]
                    p2, p3 = points[k + 1], points[min(len(points) - 1, k + 2)]
                    pos = tuple(
                        0.5
                        * (
                            (2 * p1[q])
                            + (-p0[q] + p2[q]) * f
                            + (2 * p0[q] - 5 * p1[q] + 4 * p2[q] - p3[q]) * f * f
                            + (-p0[q] + 3 * p1[q] - 3 * p2[q] + p3[q]) * f * f * f
                        )
                        for q in (0, 1)
                    )
                    scene.add(
                        Circle(
                            4,
                            position=pos,
                            fill="#E7FFFF" if i < 2 else GOLD,
                            stroke=None,
                            opacity=rays,
                            shadow=ShadowStyle("#83EFFF90", 10, (0, 0)),
                        )
                    )
            text(scene, "α ≈ 4GM / (bc²)", (1480, 180), rays, size=30)
            text(scene, "b ≫ rₛ", (1480, 225), rays * 0.65, size=22)
            scene.add(
                Arrow(
                    (1530, 290),
                    project(500, -100),
                    stroke=CYAN,
                    stroke_width=1.3,
                    tip_size=9,
                    opacity=rays * 0.75,
                )
            )

        annotation = window(t, 5, 17, 2) * fade + window(t, 52, 59, 2) * fade
        if annotation:
            line(scene, [project(94, -73), (1270, 260), (1390, 260)], "#78949B", 1.2, annotation)
            text(scene, "rₛ = 2GM / c²", (1500, 260), annotation, size=30)
            text(scene, "event horizon", (1495, 301), annotation * 0.65, size=22)
        if grid:
            scene.add(Arrow((1490, 855), (1330, 786), stroke=CYAN, stroke_width=1.3, tip_size=9, opacity=grid * 0.7))
            text(scene, "spacetime curvature", (1530, 897), grid * 0.75, size=24)
        scene.wait_until(DURATION)
        return scene


def build_scene():
    return BlackHole(Canvas(1920, 1080, "#000000"))


class BlackHoleRenderer:
    """Public renderer adapter: source-time vector descriptions painted by Skia."""

    def __init__(self):
        self.native = create_renderer("skia", antialias=1, frame_cache_mb=0)

    def validate(self, node):
        self.native.validate(node.sample(0))

    def frame(self, node, time, size):
        return self.native.frame(node.sample(time), 0, size)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.native.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="Two-second excerpt, source time 40–42")
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"))
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame <= DURATION:
        parser.error("frame must be in [0, 60]")
    if args.range and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 60")
    if args.fps <= 0:
        parser.error("fps must be positive")
    scene = build_scene()
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "skia-black-hole.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    source_range = args.range or ([40, 42] if args.preview else [0, DURATION])
    with BlackHoleRenderer() as renderer:
        if args.frame is not None:
            source_range = [args.frame, args.frame]
            save_frame(
                scene,
                args.frame,
                output,
                size=settings.dimensions(scene.canvas),
                renderer=renderer,
                overwrite=args.overwrite,
            )
        else:
            with ExportProgress() as progress:
                render(
                    scene,
                    output,
                    settings=settings,
                    start_time=source_range[0],
                    end_time=source_range[1],
                    renderer=renderer,
                    overwrite=args.overwrite,
                    progress=progress,
                )
        stats = dict(renderer.native.stats)
    output.with_suffix(".json").write_text(
        json.dumps(
            {
                "scene_duration": scene.duration,
                "source_range": source_range,
                "rendering": rendering_identity("skia", scene.sample(24)),
                "stats": stats,
                "full_export_verified": False,
            },
            indent=2,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
