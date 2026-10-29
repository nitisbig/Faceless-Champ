"""A sixty-second, graphics-only native Skia study of silk, liquid and light."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from faceless_champ import (
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
    VectorPath,
    create_renderer,
    render,
    rendering_identity,
    save_frame,
)

ROOT = Path(__file__).resolve().parent
DURATION = 60.0
TAU = math.tau


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def window(t, start, end, fade=4):
    return smooth((t - start) / fade) * smooth((end - t) / fade)


def color_mix(a, b, amount):
    a, b = a.lstrip("#"), b.lstrip("#")
    return "#" + "".join(
        f"{round(int(a[i : i + 2], 16) * (1 - amount) + int(b[i : i + 2], 16) * amount):02X}" for i in (0, 2, 4)
    )


def palette(t):
    # Moving stops are authored anew at source time; no unsupported paint tracks.
    amount = (1 - math.cos(t * TAU / DURATION)) / 2
    return [
        color_mix(a, b, amount)
        for a, b in zip(
            ("#4937DB", "#BE69EF", "#63E7F0", "#F0B4EE"),
            ("#7224BB", "#F87F93", "#FFD2A0", "#FFE5C5"),
        )
    ]


def gradient(colors, angle):
    return LinearGradient(tuple(GradientStop(i / (len(colors) - 1), c) for i, c in enumerate(colors)), angle=angle)


def bezier_loop(points):
    """Closed Catmull-Rom contour expressed as genuine cubic Bézier segments."""
    path = PathData().move_to(*points[0])
    for i in range(len(points)):
        p0, p1, p2, p3 = [points[j % len(points)] for j in (i - 1, i, i + 1, i + 2)]
        c1 = tuple(p1[k] + (p2[k] - p0[k]) / 6 for k in (0, 1))
        c2 = tuple(p2[k] - (p3[k] - p1[k]) / 6 for k in (0, 1))
        path = path.cubic_to(*c1, *c2, *p2)
    return path.close()


def halo(scene, x, y, radius, color, opacity):
    scene.add(
        Circle(
            radius,
            position=(x, y),
            fill=RadialGradient(
                (
                    GradientStop(0, color + "72"),
                    GradientStop(0.35, color + "32"),
                    GradientStop(1, color + "00"),
                )
            ),
            stroke=None,
            opacity=opacity,
        )
    )


def ribbon_path(t, index, orbit=False, thin=False):
    """Two continuously deforming edges, smoothly joined into one silk surface."""
    top, bottom = [], []
    phase = t * 0.24 + index * 0.85
    for j in range(21):
        u = j / 20
        if orbit:
            angle = u * TAU * 0.89 + phase * 0.42 + index * 0.17
            rx = 510 + 65 * math.sin(phase + u * TAU)
            ry = 235 + 50 * math.sin(phase * 0.7 + u * TAU * 2)
            x = 960 + rx * math.cos(angle)
            y = 540 + ry * math.sin(angle) + 45 * math.sin(phase)
            nx, ny = math.cos(angle), math.sin(angle)
            width = (25 + 19 * (1 + math.sin(u * TAU + phase))) * math.sin(math.pi * u) ** 0.65
        else:
            x = -200 + u * 2320
            y = 540 + (index - 1) * 140 + 150 * math.sin(u * TAU * 0.85 + phase)
            y += 62 * math.sin(u * TAU * 1.7 - phase * 0.6)
            slope = (
                150 * TAU * 0.85 * math.cos(u * TAU * 0.85 + phase)
                + 62 * TAU * 1.7 * math.cos(u * TAU * 1.7 - phase * 0.6)
            ) / 2320
            nx, ny = -slope / math.hypot(slope, 1), 1 / math.hypot(slope, 1)
            width = 28 + 34 * (0.5 + 0.5 * math.sin(u * TAU - phase + index))
        if thin:
            width *= 0.025
        top.append((x + nx * width, y + ny * width))
        bottom.append((x - nx * width, y - ny * width))
    return bezier_loop(top + bottom[::-1])


class AbstractGradients(Scene):
    """Source-time procedural authoring; sampled leaves use the public vector APIs."""

    def construct(self):
        self.wait_until(DURATION)

    def sample(self, t):
        if not math.isfinite(t) or not 0 <= t <= DURATION:
            raise ValueError("source time must be in [0, 60]")
        scene = Scene(Canvas(1920, 1080, "#000000"))
        colors = palette(t)
        envelope = window(t, 0, 60, 2.5)
        # Quiet peripheral light leaves generous, truly black negative space.
        for i in range(3):
            halo(
                scene,
                420 + i * 530 + 100 * math.sin(t * 0.14 + i),
                570 + 210 * math.sin(t * 0.17 + i * 2),
                460 + 70 * math.sin(t * 0.11 + i),
                colors[i],
                0.24 * envelope,
            )

        silk = window(t, -4, 26, 5) * envelope
        if silk > 0:
            for i in range(3):
                path = ribbon_path(t, i)
                scene.add(
                    VectorPath(
                        path,
                        fill=gradient(
                            (colors[0], colors[(i + 1) % 3], colors[3], colors[0]), 25 + 18 * math.sin(t * 0.12 + i)
                        ),
                        stroke=None,
                        opacity=silk * (0.8 if i == 0 else 0.95),
                        shadow=ShadowStyle(colors[i] + "45", 23, (0, 0)),
                    )
                )
                # A narrow luminous seam follows the same flowing centerline.
                scene.add(
                    VectorPath(
                        ribbon_path(t, i, thin=True),
                        fill=gradient((colors[0] + "00", colors[3] + "A0", colors[2] + "00"), 5),
                        stroke=None,
                        opacity=silk * 0.7,
                    )
                )

        liquid = window(t, 17, 45, 6) * envelope
        if liquid > 0:
            for i in range(3):
                phase = t * 0.28 + i * TAU / 3
                cx, cy = 960 + 320 * math.cos(phase * 0.7), 540 + 145 * math.sin(phase)
                points = []
                for j in range(12):
                    a = j * TAU / 12
                    radius = 210 + 38 * math.sin(3 * a + phase) + 22 * math.sin(2 * a - phase * 1.4)
                    points.append((cx + radius * math.cos(a), cy + radius * math.sin(a) * 0.92))
                fill = RadialGradient(
                    (
                        GradientStop(0, colors[3]),
                        GradientStop(0.3, colors[(i + 1) % 3]),
                        GradientStop(0.72, colors[0]),
                        GradientStop(1, "#10091D"),
                    ),
                    center=(0.3 + 0.09 * math.sin(phase), 0.25),
                    radius=0.8,
                )
                scene.add(
                    VectorPath(
                        bezier_loop(points),
                        fill=fill,
                        stroke=None,
                        opacity=liquid * 0.92,
                        shadow=ShadowStyle(colors[i] + "65", 36, (0, 0)),
                    )
                )

        orbit = window(t, 36, 64, 6) * envelope
        if orbit > 0:
            for i in range(4):
                scene.add(
                    VectorPath(
                        ribbon_path(t, i, orbit=True),
                        fill=gradient((colors[0], colors[i % 3], colors[3], colors[0]), 90 + i * 37 + t * 2),
                        stroke=None,
                        opacity=orbit * 0.82,
                        shadow=ShadowStyle(colors[i % 3] + "38", 20, (0, 0)),
                    )
                )
        scene.wait_until(DURATION)
        return scene


def build_scene():
    return AbstractGradients(Canvas(1920, 1080, "#000000"))


class GradientRenderer:
    """Project-local source-time adapter around Faceless Champ's native renderer.

    Core v1 has no path/gradient-stop animation tracks. Each sample builds fresh
    immutable vector descriptions, then delegates all painting to SkiaRenderer.
    No raster assets, frame history, core patches or direct Skia drawing needed.
    """

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
    mode.add_argument("--preview", action="store_true", help="Two seconds of liquid morphs at source time 28–30")
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
        else "skia-gradients.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    source_range = args.range or ([28, 30] if args.preview else [0, DURATION])
    with GradientRenderer() as renderer:
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
                "rendering": rendering_identity("skia", scene.sample(8)),
                "procedural_authoring": "source-time immutable native vector samples",
                "stats": stats,
            },
            indent=2,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
