"""45-second, text-free mathematical motion study using native Skia CPU vectors."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from faceless_champ import (
    Animation,
    Arrow,
    Canvas,
    Circle,
    ExportProgress,
    ExportSettings,
    Group,
    Line,
    PathData,
    Polyline,
    Rectangle,
    Scene,
    VectorPath,
    create_renderer,
    linear,
    render,
    rendering_identity,
    save_frame,
)

ROOT = Path(__file__).resolve().parent
DURATION = 45.0
CYAN, VIOLET, GOLD, MINT = "#61DAFB", "#AC95FF", "#FFC875", "#64E4B0"
DIM, AXIS = "#1C2B40", "#425974"
TAU = math.tau


def frames(scene, obj, prop, values, start, end):
    """Source-clock keyframes: repeatable, including out-of-order still sampling."""
    values = tuple(values)
    with scene.at(start):
        scene.play(
            Animation(
                obj,
                {prop: values[-1]},
                starts={prop: values[0]},
                keyframes={prop: tuple((i / (len(values) - 1), v) for i, v in enumerate(values))},
                rate_func=linear,
            ),
            run_time=end - start,
        )


def stroke(points, color=CYAN, width=3, **kwargs):
    return Polyline(points, stroke=color, stroke_width=width, line_cap="round", **kwargs)


def lines(pairs, color=DIM, width=1):
    return VectorPath(
        PathData(tuple(cmd for a, b in pairs for cmd in (("M", *a), ("L", *b)))), stroke=color, stroke_width=width
    )


def appear(scene, obj, start, end, fade=0.5):
    with scene.at(start):
        scene.add(obj)
    frames(scene, obj, "opacity", (0, 1), start, start + fade)
    frames(scene, obj, "opacity", (1, 0), end - fade, end)


def grid():
    pairs = [((x, 140), (x, 940)) for x in range(180, 1741, 60)]
    pairs += [((180, y), (1740, y)) for y in range(180, 901, 60)]
    return lines(pairs, "#152337"), lines([((180, 540), (1740, 540)), ((960, 140), (960, 940))], AXIS)


def f(x):
    return math.sin(x) + 0.25 * math.sin(2 * x)


def df(x):
    return math.cos(x) + 0.5 * math.cos(2 * x)


def xy(x, y):
    return 960 + 225 * x, 540 - 210 * y


def build_scene():
    scene = Scene(Canvas(1920, 1080, "#000000"))
    base = Group(*grid())
    appear(scene, base, 0, 28.5)
    xs = [-math.pi + TAU * i / 480 for i in range(481)]
    # One analytic function stays on screen through its derivative and integral.
    curve = stroke([xy(x, f(x)) for x in xs], CYAN, 5, draw_by="x")
    appear(scene, curve, 0.3, 28.4)
    frames(scene, curve, "draw", (0, 1), 0.3, 3.8)
    tracer = Circle(8, fill="#E5FAFF", stroke=CYAN, stroke_width=3)
    appear(scene, tracer, 3.8, 9.4)
    frames(scene, tracer, "position", [xy(x, f(x)) for x in xs], 3.8, 9.4)
    # Secants close toward a tangent before the exact tangent sweeps the curve.
    x0 = -1.8
    sec = Line(300, stroke=GOLD, stroke_width=4)
    appear(scene, sec, 7.4, 10.2)
    hs = [1.5 - 1.48 * i / 90 for i in range(91)]
    frames(scene, sec, "position", [xy(x0 + h / 2, (f(x0) + f(x0 + h)) / 2) for h in hs], 7.4, 10.2)
    frames(scene, sec, "width", [math.hypot(225 * h, 210 * (f(x0 + h) - f(x0))) + 100 for h in hs], 7.4, 10.2)
    frames(
        scene, sec, "rotation", [math.degrees(math.atan2(-210 * (f(x0 + h) - f(x0)), 225 * h)) for h in hs], 7.4, 10.2
    )
    deriv = stroke([xy(x, df(x)) for x in xs], VIOLET, 3, draw_by="x")
    appear(scene, deriv, 10, 19.4)
    frames(scene, deriv, "draw", (0, 1), 10, 12.2)
    tangent = Line(300, stroke=GOLD, stroke_width=4)
    point = Circle(9, fill=GOLD, stroke=None)
    slope_point = Circle(7, fill=VIOLET, stroke=None)
    guide = Line(650, stroke="#AC95FF40", stroke_width=1, rotation=90)
    tangent_group = Group(tangent, guide, point, slope_point)
    appear(scene, tangent_group, 9.5, 19.5)
    tx = [-1.8 + (math.pi + 1.8) * i / 300 for i in range(301)]
    for obj, values in (
        (tangent, [xy(x, f(x)) for x in tx]),
        (point, [xy(x, f(x)) for x in tx]),
        (slope_point, [xy(x, df(x)) for x in tx]),
        (guide, [(xy(x, 0)[0], 540) for x in tx]),
    ):
        frames(scene, obj, "position", values, 9.5, 19.5)
    frames(scene, tangent, "rotation", [math.degrees(math.atan2(-210 * df(x), 225)) for x in tx], 9.5, 19.5)
    # Signed Riemann strips fill left to right, then refine to a dense integral.
    for count, start, stop in ((32, 19, 23), (128, 23, 28.2)):
        bars = []
        dx = TAU / count
        for i in range(count):
            x = -math.pi + (i + 0.5) * dx
            v = f(x)
            px, py = xy(x, v / 2)
            bar = Rectangle(
                width=225 * dx - (3 if count == 32 else 0.5),
                height=max(1, abs(v) * 210),
                position=(px, py),
                fill="#64E4B055" if v >= 0 else "#AC95FF55",
                stroke=MINT if v >= 0 else VIOLET,
                stroke_width=0.7,
                opacity=0,
            )
            bars.append(bar)
        area = Group(*bars)
        appear(scene, area, start, stop, 0.3)
        for i, bar in enumerate(bars):
            reveal = start + 0.2 + (stop - start - 1) * i / count
            # Scale around the x axis by moving the center along with the height.
            height = bar.height
            center = bar.position
            frames(scene, bar, "height", (1, height), reveal, reveal + 0.45)
            frames(scene, bar, "position", ((center[0], 540), center), reveal, reveal + 0.45)
            frames(scene, bar, "opacity", (0, 1), reveal, reveal + 0.15)
    scan = Line(680, stroke="#FFC87588", stroke_width=2, rotation=90)
    appear(scene, scan, 19.2, 27.8)
    frames(scene, scan, "position", ((253, 540), (1667, 540)), 19.2, 27.8)
    # Fourier synthesis: odd-harmonic epicycles and their synchronized waveform.
    samples = 541
    angles = [TAU * 1.5 * i / (samples - 1) for i in range(samples)]
    sums = [[(440.0, 540.0)] * samples]
    harmonics = (1, 3, 5, 7)
    for n in harmonics:
        r = 165 / n
        prev = sums[-1]
        sums.append([(x + r * math.cos(n * a), y - r * math.sin(n * a)) for (x, y), a in zip(prev, angles)])
    wheel_parts = []
    wheels, arms = [], []
    for i, n in enumerate(harmonics):
        wheels.append(Circle(165 / n, fill=None, stroke="#61DAFB60", stroke_width=2))
        arms.append(Line(165 / n, stroke=GOLD if i == 0 else CYAN, stroke_width=2))
        wheel_parts.extend((wheels[-1], arms[-1]))
    endpoint = Circle(7, fill=GOLD, stroke=None)
    waveform = stroke([(820 + 860 * i / (samples - 1), sums[-1][i][1]) for i in range(samples)], MINT, 4, draw_by="x")
    connector = Line(380, stroke="#FFC87580", stroke_width=1)
    fourier = Group(*wheel_parts, endpoint, waveform, connector, lines([((780, 540), (1720, 540))], AXIS))
    appear(scene, fourier, 28, 37.4)
    begin, finish = 28.0, 36.8
    for i, n in enumerate(harmonics):
        frames(scene, wheels[i], "position", sums[i], begin, finish)
        frames(
            scene,
            arms[i],
            "position",
            [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(sums[i], sums[i + 1])],
            begin,
            finish,
        )
        frames(scene, arms[i], "rotation", [-math.degrees(n * a) for a in angles], begin, finish)
    frames(scene, endpoint, "position", sums[-1], begin, finish)
    frames(scene, waveform, "draw", (0, 1), begin, finish)
    trace_x = [820 + 860 * i / (samples - 1) for i in range(samples)]
    frames(scene, connector, "position", [((x + p[0]) / 2, p[1]) for x, p in zip(trace_x, sums[-1])], begin, finish)
    frames(scene, connector, "width", [x - p[0] for x, p in zip(trace_x, sums[-1])], begin, finish)
    # A planar vortex field. Particle paths solve the same circular field as arrows.
    field_parts = []
    for gx in range(-8, 9):
        for gy in range(-4, 5):
            if gx == gy == 0:
                continue
            px, py = gx * 88, gy * 88
            radius = math.hypot(px, py)
            length = 22 + 22 * min(radius / 650, 1)
            vx, vy = py / radius, -px / radius
            field_parts.append(
                Arrow(
                    (960 + px - vx * length / 2, 540 + py - vy * length / 2),
                    (960 + px + vx * length / 2, 540 + py + vy * length / 2),
                    tip_size=7,
                    stroke="#61DAFB75",
                    stroke_width=1.7,
                )
            )
    for r in (100, 190, 280, 370):
        field_parts.append(Circle(r, position=(960, 540), fill=None, stroke="#25465E70", stroke_width=1))
    particles = []
    for ring, r in enumerate((100, 190, 280, 370)):
        for j in range(8 + ring * 3):
            a = TAU * j / (8 + ring * 3) + ring * 0.21
            particle = Circle(4 if j % 3 else 6, fill=MINT if ring % 2 else GOLD, stroke=None)
            particles.append((particle, r, a))
            field_parts.append(particle)
            # Short curved streaks share the particle's angular velocity.
            tail = stroke(
                [(960 + r * math.cos(a - k * 0.012), 540 - r * math.sin(a - k * 0.012)) for k in range(16)],
                "#64E4B045",
                3,
            )
            field_parts.append(tail)
            # Rotate each whole trail about the vortex center with a symmetric invisible extent.
            trail_group = Group(Circle(r + 2, position=(960, 540), opacity=0), tail)
            field_parts[-1] = trail_group
    field = Group(*field_parts)
    appear(scene, field, 37, 45, 0.6)
    for particle, r, a in particles:
        frames(
            scene,
            particle,
            "position",
            [
                (960 + r * math.cos(a + 1.15 * t), 540 - r * math.sin(a + 1.15 * t))
                for t in [8 * i / 300 for i in range(301)]
            ],
            37,
            45,
        )
    for part in field_parts:
        if isinstance(part, Group):
            frames(scene, part, "rotation", (0, -math.degrees(1.15 * 8)), 37, 45)
    scene.wait_until(DURATION)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"), help="Export a source-clock section")
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="2-second tangent sample using original source time")
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame < DURATION:
        parser.error("frame time must be in [0, 45)")
    if args.range is not None and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 45")
    scene = build_scene()
    assert scene.duration == DURATION
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    out = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png" if args.frame is not None else "preview.mp4" if args.preview else "skia-math.mp4"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    source_range = args.range or (
        [args.frame, args.frame] if args.frame is not None else [13, 15] if args.preview else [0, 45]
    )
    if args.frame is not None:
        with create_renderer("skia", antialias=1) as renderer:
            save_frame(
                scene,
                args.frame,
                out,
                size=settings.dimensions(scene.canvas),
                renderer=renderer,
                overwrite=args.overwrite,
            )
    else:
        with ExportProgress() as progress:
            render(
                scene,
                out,
                settings=settings,
                start_time=source_range[0],
                end_time=source_range[1],
                overwrite=args.overwrite,
                progress=progress,
            )
    out.with_suffix(".json").write_text(
        json.dumps(
            {"scene_duration": DURATION, "source_range": source_range, "rendering": rendering_identity("skia", scene)},
            indent=2,
        )
    )
    print(out)


if __name__ == "__main__":
    main()
