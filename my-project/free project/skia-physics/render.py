"""One minute of physics diagrams, authored with public Faceless Champ / Skia APIs."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from faceless_champ import (
    CLEAN_FLOW_FONT,
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
    Text,
    VectorPath,
    create_renderer,
    linear,
    render,
    rendering_identity,
    save_frame,
    smooth,
)

ROOT = Path(__file__).resolve().parent
DURATION = 60.0
CYAN, GOLD, MINT, VIOLET = "#68DDF0", "#FFC778", "#80E7BC", "#B19AFF"
WHITE, DIM, GHOST = "#E9F4F7", "#344A57", "#16252E"


def track(scene, obj, prop, values, start, end, easing=linear):
    values = tuple(values)
    with scene.at(start):
        scene.play(
            Animation(
                obj,
                {prop: values[-1]},
                starts={prop: values[0]},
                keyframes={prop: tuple((i / (len(values) - 1), v) for i, v in enumerate(values))},
                rate_func=easing,
            ),
            run_time=end - start,
        )


def show(scene, obj, start, end, fade=0.55):
    with scene.at(start):
        scene.add(obj)
    track(scene, obj, "opacity", (0, 1), start, start + fade, smooth)
    track(scene, obj, "opacity", (1, 0), end - fade, end, smooth)


def ink(points, color=DIM, width=2, **kwargs):
    return Polyline(points, stroke=color, stroke_width=width, line_cap="round", **kwargs)


def label(value, position, color=WHITE):
    return Text(value, position=position, font=CLEAN_FLOW_FONT, font_size=28, color=color, text_engine="skia")


def segments(pairs, color=DIM, width=1.5):
    return VectorPath(
        PathData(tuple(cmd for a, b in pairs for cmd in (("M", *a), ("L", *b)))),
        stroke=color,
        stroke_width=width,
    )


def dashed(a, b, color=DIM):
    length = math.dist(a, b)
    n = max(1, math.ceil(length / 24))
    return segments(
        [
            (
                tuple(x + (y - x) * i / n for x, y in zip(a, b)),
                tuple(x + (y - x) * min((i + 0.55) / n, 1) for x, y in zip(a, b)),
            )
            for i in range(n)
        ],
        color,
    )


def vector(a, b, color=CYAN, width=4):
    return Arrow(a, b, stroke=color, stroke_width=width, tip_size=14)


def moving_vector(scene, origins, deltas, color, start, end, lifetime):
    arrow = vector((0, 0), (40, 0), color)
    show(scene, arrow, *lifetime)
    track(scene, arrow, "position", [(x + dx / 2, y + dy / 2) for (x, y), (dx, dy) in zip(origins, deltas)], start, end)
    track(scene, arrow, "width", [max(2, math.hypot(dx, dy)) for dx, dy in deltas], start, end)
    # Angles are unwrapped so the arrow never flips through a full turn at +/-180.
    angles = []
    for dx, dy in deltas:
        angle = math.degrees(math.atan2(dy, dx))
        if angles:
            angle += 360 * round((angles[-1] - angle) / 360)
        angles.append(angle)
    track(scene, arrow, "rotation", angles, start, end)
    return arrow


def free_body(scene):
    angle = math.radians(22)
    c, s = math.cos(angle), math.sin(angle)
    center = (930, 550)
    contact = (center[0] + 57 * s, center[1] + 57 * c)
    a = (contact[0] - 600 * c, contact[1] + 600 * s)
    b = (contact[0] + 600 * c, contact[1] - 600 * s)
    ground = ink((a, b), WHITE, 3)
    hatches = segments(
        [((a[0] + i * c, a[1] - i * s), (a[0] + i * c - 18, a[1] - i * s + 32)) for i in range(0, 1201, 38)]
    )
    block = Rectangle(
        width=160,
        height=114,
        position=center,
        rotation=-22,
        fill="#12252E",
        stroke=CYAN,
        stroke_width=3,
        corner_radius=6,
    )
    base = Group(ground, hatches, block, Circle(6, position=center, fill=WHITE, stroke=None))
    show(scene, base, 0, 14.4)
    track(scene, ground, "draw", (0, 1), 0.2, 1.8)
    # A static block: N = mg cos(theta), f = mg sin(theta). All three sum to zero.
    normal = (-240 * c * s, -240 * c * c)
    friction = (240 * s * c, -240 * s * s)
    forces = (
        ((0, 240), GOLD, "mg", (980, 807), 2.0),
        (normal, MINT, "N", (803, 310), 3.5),
        (friction, VIOLET, "f", (1068, 497), 5.0),
    )
    for (dx, dy), color, symbol, pos, start in forces:
        arrow = vector(center, (center[0] + dx, center[1] + dy), color)
        show(scene, Group(arrow, label(symbol, pos, color)), start, 14.3)
        track(scene, arrow, "draw", (0, 1), start, start + 0.8)
    # Weight resolved into an into-plane and a down-slope component.
    p = (center[0] - friction[0], center[1] - friction[1])
    q = (center[0], center[1] + 240)
    construction = Group(dashed(center, p, GOLD), dashed(p, q, GOLD))
    show(scene, construction, 7, 14.3)
    # A separate tip-to-tail force triangle makes equilibrium visible.
    o = (1470, 620)
    n = (o[0] + normal[0], o[1] + normal[1])
    f = (n[0] + friction[0], n[1] + friction[1])
    for i, (start, stop, color) in enumerate(((o, n, MINT), (n, f, VIOLET), (f, o, GOLD))):
        edge = vector(start, stop, color, 3)
        show(scene, edge, 8.5 + i * 0.65, 14.3)
        track(scene, edge, "draw", (0, 1), 8.5 + i * 0.65, 9.1 + i * 0.65)


def projectile(scene):
    begin, finish = 15.4, 27.8
    qs = [i / 372 for i in range(373)]
    points = [(300 + 1320 * q, 820 - 1760 * q * (1 - q)) for q in qs]
    floor = ink(((240, 820), (1680, 820)), DIM, 2)
    path = ink(points, CYAN, 3, draw_by="x")
    reference = ink(points, GHOST, 2)
    ticks = segments([((300 + 110 * i, 820), (300 + 110 * i, 833)) for i in range(13)])
    show(scene, Group(floor, ticks, reference, path), 14, 29.3)
    track(scene, path, "draw", (0, 1), begin, finish)
    for i in range(1, 12):
        q = i / 12
        ghost = Circle(5, position=(300 + 1320 * q, 820 - 1760 * q * (1 - q)), fill=DIM, stroke=None)
        show(scene, ghost, begin + (finish - begin) * q, 29.2, 0.2)
    ball = Circle(13, fill=WHITE, stroke=CYAN, stroke_width=3)
    velocity = [(110, 0.3 * (-1760 + 3520 * q) / 3.6) for q in qs]
    moving_vector(scene, points, velocity, MINT, begin, finish, (15, 29.2))
    moving_vector(scene, points, [(0, 120)] * len(qs), GOLD, begin, finish, (15, 29.2))
    # Velocity components form a moving right triangle with the resultant.
    moving_vector(scene, points, [(110, 0)] * len(qs), CYAN, begin, finish, (15, 29.2))
    vertical = Line(100, rotation=90, stroke=VIOLET, stroke_width=2)
    vlabel, glabel = label("v", (0, 0), MINT), label("g", (0, 0), GOLD)
    show(scene, Group(vertical, ball, vlabel, glabel), 15, 29.2)
    track(
        scene, vertical, "position", [(x + 110, y + dy / 2) for (x, y), (_, dy) in zip(points, velocity)], begin, finish
    )
    track(scene, vertical, "width", [max(1, abs(dy)) for _, dy in velocity], begin, finish)
    track(scene, ball, "position", points, begin, finish)
    track(
        scene,
        vlabel,
        "position",
        [(x + dx + 20, y + dy - 18) for (x, y), (dx, dy) in zip(points, velocity)],
        begin,
        finish,
    )
    track(scene, glabel, "position", [(x + 24, y + 120) for x, y in points], begin, finish)


def oscillator(scene):
    begin, finish = 30.3, 43.0
    ts = [i / 480 for i in range(481)]
    omega = 6 * math.pi
    displacements = [230 * math.cos(omega * t) for t in ts]
    positions = [(1000 + x, 480) for x in displacements]
    wall = Group(
        ink(((400, 340), (400, 570)), WHITE, 4),
        segments([((400, y), (370, y + 25)) for y in range(345, 560, 25)]),
        ink(((400, 538), (1530, 538)), DIM, 2),
        dashed((1000, 280), (1000, 680)),
    )
    # Stretching the coil's horizontal bounds preserves its fixed vertical amplitude.
    coil_points = [(400, 480), (435, 480)]
    for i in range(25):
        coil_points.append((450 + i * 18, 480 + (30 if i % 2 else -30)))
    coil_points += [(900, 480), (935, 480)]
    coil = ink(coil_points, CYAN, 3)
    mass = Rectangle(width=130, height=110, fill="#12252E", stroke=CYAN, stroke_width=3, corner_radius=8)
    show(scene, Group(wall, coil, mass), 29, 44.3)
    lengths = [x - 65 - 400 for x, _ in positions]
    track(scene, coil, "width", lengths, begin, finish)
    track(scene, coil, "position", [(400 + length / 2, 480) for length in lengths], begin, finish)
    track(scene, mass, "position", positions, begin, finish)
    # Separate fixed-direction arrows crossfade at zero: no 180-degree interpolation artifact.
    for values, y, color, symbol in (
        ([-0.72 * x for x in displacements], 320, GOLD, "F"),
        ([-160 * math.sin(omega * t) for t in ts], 640, MINT, "v"),
    ):
        show(scene, label(symbol, (1480, y), color), 30, 44.2)
        for direction in (-1, 1):
            arrow = vector((0, 0), (direction * 100, 0), color)
            show(scene, Group(arrow), 30, 44.2)
            active = [max(0, direction * value) for value in values]
            track(scene, arrow, "width", [max(16, v) for v in active], begin, finish)
            track(
                scene,
                arrow,
                "position",
                [(p[0] + direction * max(16, v) / 2, y) for p, v in zip(positions, active)],
                begin,
                finish,
            )
            track(scene, arrow, "opacity", [min(1, v / 18) for v in active], begin, finish)
    # Displacement trace shares the oscillator's exact phase and source clock.
    plot_points = [(400 + 1120 * t, 850 - 0.36 * x) for t, x in zip(ts, displacements)]
    curve = ink(plot_points, CYAN, 3, draw_by="x")
    dot = Circle(6, fill=WHITE, stroke=None)
    show(scene, Group(ink(((400, 850), (1550, 850)), DIM, 1), curve, dot, label("x", (355, 850), CYAN)), 30, 44.2)
    track(scene, dot, "position", plot_points, begin, finish)
    track(scene, curve, "draw", (0, 1), begin, finish)


def circular_motion(scene):
    begin, finish = 45.3, 59.0
    angles = [math.tau * 1.5 * i / 480 for i in range(481)]
    center, radius = (960, 540), 280
    points = [(960 + radius * math.cos(a), 540 - radius * math.sin(a)) for a in angles]
    circle = Circle(radius, position=center, fill=None, stroke=DIM, stroke_width=2)
    axes = segments([((570, 540), (1350, 540)), ((960, 180), (960, 900))], GHOST)
    show(scene, Group(circle, axes), 44, 60)
    radius_line = Line(radius, stroke=CYAN, stroke_width=3)
    show(scene, radius_line, 44.7, 60)
    track(scene, radius_line, "position", [((x + 960) / 2, (y + 540) / 2) for x, y in points], begin, finish)
    track(scene, radius_line, "rotation", [-math.degrees(a) for a in angles], begin, finish)
    ball = Circle(12, fill=WHITE, stroke=CYAN, stroke_width=3)
    show(scene, ball, 44.7, 60)
    track(scene, ball, "position", points, begin, finish)
    moving_vector(
        scene, points, [(-165 * math.sin(a), -165 * math.cos(a)) for a in angles], MINT, begin, finish, (44.7, 60)
    )
    moving_vector(
        scene, points, [(-135 * math.cos(a), 135 * math.sin(a)) for a in angles], GOLD, begin, finish, (44.7, 60)
    )
    origin = Circle(5, position=center, fill=WHITE, stroke=None)
    show(scene, origin, 44.7, 60)
    # Orthogonal projection of the rotating radius constructs a live right triangle.
    h = Line(100, stroke="#68DDF080", stroke_width=2)
    v = Line(100, rotation=90, stroke="#B19AFF90", stroke_width=2)
    foot = Circle(5, fill=VIOLET, stroke=None)
    show(scene, Group(h, v, foot), 45, 60)
    track(scene, h, "width", [max(1, abs(x - 960)) for x, _ in points], begin, finish)
    track(scene, h, "position", [((x + 960) / 2, 540) for x, _ in points], begin, finish)
    track(scene, v, "width", [max(1, abs(y - 540)) for _, y in points], begin, finish)
    track(scene, v, "position", [(x, (y + 540) / 2) for x, y in points], begin, finish)
    track(scene, foot, "position", [(x, 540) for x, _ in points], begin, finish)
    # The tiny square turns with the radius and proves v is perpendicular to r.
    right_angle = ink(((0, 0), (-22, 0), (-22, -22), (0, -22)), WHITE, 1.5)
    show(scene, right_angle, 45, 60)
    # Bounds center is offset from the particle, so rotate that offset as well.
    track(
        scene,
        right_angle,
        "position",
        [
            (x - 11 * math.cos(a) - 11 * math.sin(a), y + 11 * math.sin(a) - 11 * math.cos(a))
            for (x, y), a in zip(points, angles)
        ],
        begin,
        finish,
    )
    track(scene, right_angle, "rotation", [-math.degrees(a) for a in angles], begin, finish)
    vl, al = label("v", (0, 0), MINT), label("a", (0, 0), GOLD)
    show(scene, Group(vl, al), 45, 60)
    track(
        scene,
        vl,
        "position",
        [(x - 195 * math.sin(a), y - 195 * math.cos(a)) for (x, y), a in zip(points, angles)],
        begin,
        finish,
    )
    track(
        scene,
        al,
        "position",
        [(x - 165 * math.cos(a), y + 165 * math.sin(a)) for (x, y), a in zip(points, angles)],
        begin,
        finish,
    )


def build_scene():
    scene = Scene(Canvas(1920, 1080, "#000000"))
    free_body(scene)
    projectile(scene)
    oscillator(scene)
    circular_motion(scene)
    scene.wait_until(DURATION)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="Export source seconds 34–36")
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"))
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame < DURATION:
        parser.error("frame time must satisfy 0 <= SECONDS < 60")
    if args.range is not None and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 60")
    if args.fps <= 0:
        parser.error("fps must be positive")
    scene = build_scene()
    assert scene.duration == DURATION
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    out = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png" if args.frame is not None else "preview.mp4" if args.preview else "skia-physics.mp4"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    source_range = args.range or ([34, 36] if args.preview else [0, DURATION])
    if args.frame is not None:
        source_range = [args.frame, args.frame]
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
