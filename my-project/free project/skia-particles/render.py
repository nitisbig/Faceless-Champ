"""One minute of luminous generative geometry, rendered with native Python/Skia."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from faceless_champ import (
    Canvas,
    ExportProgress,
    ExportSettings,
    PathData,
    Scene,
    VectorPath,
    create_renderer,
    render,
    rendering_identity,
    save_frame,
)

ROOT = Path(__file__).resolve().parent
DURATION = 60.0
TAU = math.tau
COLORS = ("#47E8ED", "#6C88FF", "#B16DFF", "#FF83B5", "#FFC887")


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def window(t, start, end, fade=2.5):
    return smooth((t - start) / fade) * smooth((end - t) / fade)


def stroke(scene, points, color, opacity, width=1.5):
    """Three native strokes supply a luminous core and broad, quiet light spill."""
    path = PathData(tuple(("M" if i == 0 else "L", *p) for i, p in enumerate(points)))
    for factor, alpha in ((7, 0.035), (3, 0.10), (1, 0.8)):
        scene.add(
            VectorPath(
                path, fill=None, stroke=color, stroke_width=width * factor, line_cap="round", opacity=opacity * alpha
            )
        )


def dots(scene, points, color, opacity):
    """Batch circular cubic contours; each batch remains a native vector leaf."""
    if not points:
        return
    for scale, alpha in ((3.8, 0.035), (1.9, 0.13), (1, 0.95)):
        commands = []
        for x, y, radius in points:
            r = radius * scale
            k = r * 0.5522847498
            commands.extend(
                (
                    ("M", x + r, y),
                    ("C", x + r, y + k, x + k, y + r, x, y + r),
                    ("C", x - k, y + r, x - r, y + k, x - r, y),
                    ("C", x - r, y - k, x - k, y - r, x, y - r),
                    ("C", x + k, y - r, x + r, y - k, x + r, y),
                    ("Z",),
                )
            )
        scene.add(VectorPath(PathData(tuple(commands)), fill=color, stroke=None, opacity=opacity * alpha))


def orbit(t, i):
    a = t * 0.58 + i * TAU / 12
    r = 285 + 75 * math.sin(t * 0.27 + i * 1.9)
    return (960 + 1.8 * r * math.cos(a), 540 + r * math.sin(a) + 60 * math.sin(2 * a))


def trails(scene, t, opacity):
    for i in range(12):
        color = COLORS[i % 3]
        # Increasing brightness toward the head makes the direction legible.
        for band in range(4):
            ages = [2.8 * (1 - (band + j / 24) / 4) for j in range(25)]
            stroke(scene, [orbit(t - age, i) for age in ages], color, opacity * (0.12 + band * 0.22), 1.4 + band * 0.35)
        x, y = orbit(t, i)
        dots(scene, [(x, y, 3.1)], "#D8FFFF", opacity)


def spirals(scene, t, opacity):
    for arm in range(5):
        points = []
        sparks = []
        for j in range(321):
            u = j / 320
            a = u * TAU * 2.2 + arm * TAU / 5 + t * 0.20
            r = 14 + 403 * u
            r *= 1 + 0.035 * math.sin(a * 4 - t * 0.5)
            x, y = 960 + 1.35 * r * math.cos(a), 540 + r * math.sin(a)
            points.append((x, y))
            if j % 8 == 0:
                sparks.append((x, y, 1.5 + 1.2 * u))
        stroke(scene, points, COLORS[arm], opacity * 0.7, 1.3)
        dots(scene, sparks, COLORS[arm], opacity)


def lissajous(scene, t, opacity):
    for layer in range(5):
        phase = t * 0.15 + layer * 0.16
        points = []
        for j in range(721):
            a = j / 720 * TAU
            x = 960 + (590 - layer * 22) * math.sin(3 * a + phase)
            y = 540 + (350 - layer * 13) * math.sin(2 * a)
            points.append((x, y))
        stroke(scene, points, COLORS[layer], opacity * 0.65, 1.35)
        a = t * 0.64 + layer * TAU / 5
        dots(
            scene,
            [(960 + (590 - layer * 22) * math.sin(3 * a + phase), 540 + (350 - layer * 13) * math.sin(2 * a), 3.5)],
            "#FFF2F8",
            opacity,
        )


def field_point(u, v, t):
    x = 960 + u * 760
    y = 540 + v * 330
    wave = math.sin(u * 4.2 + v * 2 - t * 0.7)
    x += 33 * math.cos(v * 5 + t * 0.4)
    y += 66 * wave + 30 * math.sin(u * 7 - v * 4 + t * 0.45)
    return x, y, wave


def field(scene, t, opacity):
    buckets = [[] for _ in range(5)]
    for row in range(22):
        for col in range(47):
            u, v = col / 46 * 2 - 1, row / 21 * 2 - 1
            x, y, wave = field_point(u, v, t)
            edge = math.sin(math.pi * col / 46) * math.sin(math.pi * row / 21)
            if edge > 0.06:
                buckets[min(4, col * 5 // 47)].append((x, y, (1.35 + (wave + 1) * 0.8) * edge**0.35))
    for color, points in zip(COLORS, buckets):
        dots(scene, points, color, opacity)
    for row in (5, 10, 15):
        points = [field_point(j / 120 * 2 - 1, row / 21 * 2 - 1, t)[:2] for j in range(121)]
        stroke(scene, points, "#6C88FF", opacity * 0.18, 0.8)


def bloom(scene, t, opacity):
    buckets = [[] for _ in range(5)]
    angle = math.pi * (3 - math.sqrt(5))
    breathing = 1 + 0.045 * math.sin(t * 0.9)
    for i in range(720):
        u = (i + 0.5) / 720
        a = i * angle + t * 0.085
        r = 425 * math.sqrt(u) * breathing
        # Slow torsion lets the golden-angle pattern breathe without randomness.
        a += 0.10 * math.sin(r / 85 - t * 0.45)
        x, y = 960 + r * math.cos(a), 540 + r * math.sin(a)
        radius = 1.15 + 1.45 * math.sin(math.pi * u) + 0.55 * (1 + math.sin(i * 0.1 - t))
        buckets[min(4, int(u * 5))].append((x, y, radius))
    for color, points in zip(COLORS, buckets):
        dots(scene, points, color, opacity)


class ParticleArt(Scene):
    def construct(self):
        self.wait_until(DURATION)

    def sample(self, t):
        if not math.isfinite(t) or not 0 <= t <= DURATION:
            raise ValueError("source time must be in [0, 60]")
        scene = Scene(Canvas(1920, 1080, "#000000"))
        envelope = window(t, 0, 60, 2)
        for artist, start, end in (
            (trails, -3, 15),
            (spirals, 11, 28),
            (lissajous, 24, 40),
            (field, 36, 52),
            (bloom, 48, 63),
        ):
            opacity = envelope * window(t, start, end, 3)
            if opacity > 0:
                artist(scene, t, opacity)
        scene.wait_until(DURATION)
        return scene


def build_scene():
    return ParticleArt(Canvas(1920, 1080, "#000000"))


class ParticleRenderer:
    """Source-time geometry adapter delegating all painting to Faceless Champ."""

    def __init__(self):
        self.native = create_renderer("skia", antialias=1, frame_cache_mb=0)

    def validate(self, node):
        self.native.validate(node.sample(30))

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
    mode.add_argument("--preview", action="store_true", help="Two seconds of particle trails, source time 6–8")
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
        else "skia-particles.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    source_range = args.range or ([6, 8] if args.preview else [0, DURATION])
    with ParticleRenderer() as renderer:
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
                "rendering": rendering_identity("skia", scene.sample(30)),
                "stats": stats,
                "full_export_verified": False,
            },
            indent=2,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
