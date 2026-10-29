"""45 seconds of native Skia HUD graphics; run with the checkout's .venv Python."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Animation,
    Canvas,
    Circle,
    Ellipse,
    ExportProgress,
    ExportSettings,
    FadeIn,
    FadeOut,
    GradientStop,
    Group,
    Line,
    Number,
    PathData,
    Polyline,
    RadialGradient,
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
DURATION = 45.0
CYAN, DIM, AMBER, WHITE = "#55E9F4", "#235664", "#FFB45C", "#DBFCFF"


def polar(r, a, center=(0, 0)):
    a = math.radians(a)
    return center[0] + r * math.cos(a), center[1] + r * math.sin(a)


def label(value, x, y, size=16, color=DIM):
    return Text(
        value, position=(x, y), anchor="top_left", font=CLEAN_FLOW_FONT, font_size=size, color=color, text_engine="skia"
    )


def number(value, x, y, size=32, color=CYAN, spec="06.1f", width=180):
    return Number(
        value,
        position=(x, y),
        anchor="top_left",
        font=CLEAN_FLOW_FONT,
        font_size=size,
        color=color,
        text_engine="skia",
        format_spec=spec,
        width=width,
    )


def segment(a, b, color=DIM, width=1):
    return Polyline((a, b), stroke=color, stroke_width=width)


def arc(radius, start, end, color=CYAN, width=2, center=(0, 0)):
    """Exact cubic arc segments, staying in the native vector path pipeline."""
    count = max(1, math.ceil(abs(end - start) / 60))
    path = PathData().move_to(*polar(radius, start, center))
    for i in range(count):
        a = math.radians(start + (end - start) * i / count)
        b = math.radians(start + (end - start) * (i + 1) / count)
        k = 4 / 3 * math.tan((b - a) / 4)
        x, y = center
        path = path.cubic_to(
            x + radius * (math.cos(a) - k * math.sin(a)),
            y + radius * (math.sin(a) + k * math.cos(a)),
            x + radius * (math.cos(b) + k * math.sin(b)),
            y + radius * (math.sin(b) - k * math.cos(b)),
            *polar(radius, math.degrees(b), center),
        )
    return VectorPath(path, stroke=color, stroke_width=width)


def line_field(pairs, color=DIM, width=1):
    """Batch static instrument strokes into one retained native path."""
    commands = tuple(command for a, b in pairs for command in (("M", *a), ("L", *b)))
    return VectorPath(PathData(commands), stroke=color, stroke_width=width)


def rotor(radius, children, center):
    # Symmetric bounds hold the rotation pivot at the dial's center.
    return Group(Circle(radius + 5, opacity=0), *children, position=center)


def keyframes(scene, component, prop, values, start=0, end=DURATION, easing=linear):
    frames = tuple((i / (len(values) - 1), value) for i, value in enumerate(values))
    with scene.at(start):
        scene.play(
            Animation(component, {prop: values[-1]}, keyframes={prop: frames}, rate_func=easing), run_time=end - start
        )


def build_scene():
    scene = Scene(Canvas(1920, 1080, "#030C13"))

    def add(*components):
        with scene.at(0):
            scene.add(*components)

    backdrop = Circle(
        640,
        position=(960, 510),
        stroke=None,
        fill=RadialGradient((GradientStop(0, "#123D4D80"), GradientStop(1, "#030C1300"))),
    )
    add(backdrop)
    # Quiet Cartesian field and fine screen texture, authored as vectors.
    add(
        line_field(
            [((x, 130), (x, 974)) for x in range(60, 1880, 40)] + [((60, y), (1860, y)) for y in range(134, 975, 40)],
            "#16344338",
        )
    )
    add(line_field([((60, y), (1860, y)) for y in range(130, 975, 8)], "#72CFE904"))
    add(
        label("O R B I T A L", 62, 42, 31, WHITE),
        label("SENSOR ARRAY  /  07", 65, 86, 14, CYAN),
        label("AUTONOMOUS SURVEILLANCE", 1455, 55, 17, CYAN),
        label("UPLINK  08 : 42 : 16   /   SECTOR 04", 1455, 85, 14),
        segment((60, 117), (1860, 117)),
        segment((60, 990), (1860, 990)),
        label("FC / NATIVE VECTOR SYSTEM", 62, 1013, 13),
        label("38.8977 N   /   077.0365 W", 1510, 1013, 14, CYAN),
    )
    clock = number(0, 911, 1010, 19, CYAN, "05.1f", 100)
    keyframes(scene, clock, "value", [0, 45])
    for x, sign in ((60, 1), (1860, -1)):
        for y, dy in ((137, 1), (969, -1)):
            add(Polyline(((x, y + dy * 24), (x, y), (x + sign * 24, y)), stroke=CYAN, stroke_width=2))

    # Centerpiece: nested, opposing circular mechanics around a true radar sweep.
    center = (960, 510)
    core = []
    for r in (82, 160, 238, 275, 306):
        core.append(Circle(r, position=center, fill=None, stroke=DIM, stroke_width=1))
    core.append(line_field([(polar(35, a, center), polar(273, a, center)) for a in range(0, 360, 30)], "#367B8938"))
    for step, color, width in ((0, CYAN, 2), (1, DIM, 2), (2, DIM, 1)):
        angles = [a for a in range(0, 360, 3) if (0 if a % 30 == 0 else 1 if a % 15 == 0 else 2) == step]
        core.append(
            line_field(
                [(polar(313 if a % 15 else 308, a, center), polar(322, a, center)) for a in angles], color, width
            )
        )
    for a in range(0, 360, 30):
        x, y = polar(342, a - 90, center)
        core.append(label(f"{a:03}", x - 13, y - 9, 13, CYAN))
    for x in (-1, 1):
        core.extend(
            (
                segment((960 + x * 368, 510), (960 + x * 405, 510), CYAN, 2),
                segment((960, 510 + x * 365), (960, 510 + x * 383), CYAN, 2),
            )
        )
    base = Group(*core)
    add(base)
    rings = rotor(297, [arc(294, a, a + 67, CYAN, 5) for a in range(0, 360, 90)], center)
    inner = rotor(253, [arc(252, a, a + 33, AMBER, 2) for a in range(0, 360, 60)], center)
    add(rings, inner)
    keyframes(scene, rings, "rotation", [0, 270])
    keyframes(scene, inner, "rotation", [0, -540])
    wedges = []
    for i in range(28):
        a = -i * 1.5
        wedges.append(
            Polyline(
                ((0, 0), polar(272, a), polar(272, a - 1.55)),
                closed=True,
                stroke=None,
                fill=f"#55E9F4{int(34 * (1 - i / 28)):02X}",
            )
        )
    wedges.append(segment((0, 0), (273, 0), CYAN, 2))
    sweep = rotor(275, wedges, center)
    add(sweep)
    keyframes(scene, sweep, "rotation", [-90, 990])
    # Orbital wireframe gives the radar a dimensional instrument core.
    globe = Group(
        Circle(70, fill="#071F2A", stroke=CYAN, stroke_width=1),
        Ellipse(width=52, height=140, stroke=DIM),
        Ellipse(width=112, height=140, stroke=DIM),
        Ellipse(width=140, height=44, stroke=DIM),
        Ellipse(width=140, height=100, stroke=DIM),
        position=center,
    )
    add(
        globe,
        segment((942, 510), (978, 510), WHITE),
        segment((960, 492), (960, 528), WHITE),
        Circle(3, position=center, fill=WHITE, stroke=None),
    )
    keyframes(scene, globe, "rotation", [0, 45, 0, -45, 0])

    # Contacts move continuously along authored paths; no random per-frame state.
    contact_paths = []
    for i in range(8):
        angle = i * 47 + 17
        points = [
            polar(125 + (i % 3) * 39 + 13 * math.sin(j + i), angle + 12 * math.sin(j * 0.8), center) for j in range(10)
        ]
        x, y = points[0]
        contact = Group(
            Circle(4, fill=AMBER, stroke=None, position=(x, y)),
            Circle(12, fill=None, stroke=AMBER, stroke_width=1, position=(x, y)),
            segment((x - 20, y), (x - 14, y), AMBER),
            label(f"{i + 1:02}", x + 16, y - 16, 12, AMBER),
        )
        add(contact)
        dx, dy = contact.position[0] - x, contact.position[1] - y
        keyframes(scene, contact, "position", [(p[0] + dx, p[1] + dy) for p in points], easing=smooth)
        contact_paths.append(points)

    # Tracking bracket follows the first contact, then settles into a lock.
    brackets = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            brackets.append(
                Polyline(((sx * 42, sy * 26), (sx * 42, sy * 42), (sx * 26, sy * 42)), stroke=AMBER, stroke_width=3)
            )
    target = Group(*brackets, position=contact_paths[0][0], opacity=0)
    add(target)
    with scene.at(8):
        scene.play(target.animate.opacity_to(1), run_time=0.6)
    keyframes(scene, target, "position", contact_paths[0], easing=smooth)
    keyframes(scene, target, "scale", [1.6, 1.25, 0.85, 0.85, 1.1], start=8, end=44, easing=smooth)

    # Left: instrument cluster, arcs, segmented power and waveform.
    add(label("01 / PROPULSION", 86, 156, 16, CYAN))
    gauges = ((205, 305, 91, 87, "THRUST"), (407, 305, 69, 64, "CORE"))
    for x, y, r, value, title in gauges:
        add(arc(r, 135, 405, DIM, 7, (x, y)), label(title, x - 30, y + 30, 12, CYAN))
        g = arc(r, 135, 405, CYAN, 7, (x, y))
        add(g)
        readings = [value, value + 8, value - 13, value + 4, value, value + 5]
        keyframes(scene, g, "draw", [v / 100 for v in readings], easing=smooth)
        n = number(value, x - 41, y - 31, 40, WHITE, "02.0f", 100)
        add(n)
        keyframes(scene, n, "value", readings, easing=smooth)
        for a in range(135, 406, 15):
            add(segment(polar(r + 14, a, (x, y)), polar(r + 19, a, (x, y)), DIM))
    add(segment((86, 440), (498, 440)), label("ENERGY DISTRIBUTION", 86, 464, 14, CYAN))
    for row in range(3):
        add(label(("AUX", "SYS", "PWR")[row], 86, 505 + row * 35, 12))
        for col in range(22):
            cell = Rectangle(
                width=10,
                height=13,
                fill=CYAN if col < 14 + row * 2 else DIM,
                stroke=None,
                position=(160 + col * 15, 514 + row * 35),
            )
            add(cell)
            if col > 10:
                keyframes(scene, cell, "opacity", [0.2 + 0.8 * ((j + col + row) % 4 != 0) for j in range(16)])
    add(label("SIGNAL / FREQUENCY", 86, 657, 14, CYAN))
    for y in (706, 756, 806):
        add(segment((86, y), (498, y), "#23566480"))
    for i in range(3):
        points = [
            (88 + j * 4, 755 + (25 + i * 12) * math.sin(j * 0.19 + i) * math.sin(j * 0.071 + i * 0.8))
            for j in range(103)
        ]
        wave = Polyline(points, stroke=CYAN if i == 0 else "#55E9F43A", stroke_width=2 if i == 0 else 1)
        add(wave)
        keyframes(scene, wave, "scale_y", [1, 0.3, 1.3, 0.6, 1, 0.4, 1.1, 0.5, 1], easing=smooth)
    wave_scanner = Line(122, position=(88, 755), rotation=90, stroke=AMBER, stroke_width=2)
    add(wave_scanner)
    keyframes(scene, wave_scanner, "position", [(88 if j % 2 == 0 else 496, 755) for j in range(12)])

    # Right: independent radar, target geometry and live coordinates.
    add(label("02 / TARGET SOLUTION", 1424, 156, 16, CYAN))
    for r in (35, 70, 106):
        add(Circle(r, position=(1640, 298), fill=None, stroke=DIM, stroke_width=1))
    add(segment((1522, 298), (1758, 298)), segment((1640, 180), (1640, 416)))
    for a in range(0, 360, 45):
        add(segment(polar(109, a, (1640, 298)), polar(116, a, (1640, 298)), CYAN, 2))
    satellite = rotor(
        106,
        [
            segment((0, 0), (74, -63), AMBER, 2),
            Circle(7, position=(74, -63), fill=AMBER, stroke=None),
            arc(106, -70, -25, CYAN, 4),
        ],
        (1640, 298),
    )
    add(satellite)
    keyframes(scene, satellite, "rotation", [0, -720])
    add(segment((1424, 440), (1834, 440)))
    for i, (title, value, end) in enumerate(
        (("AZIMUTH", 247.8, 312.6), ("ELEVATION", 38.2, 42.7), ("RANGE / KM", 1284.5, 974.2))
    ):
        y = 472 + i * 79
        add(label(title, 1424, y, 13, CYAN))
        n = number(value, 1615, y - 9, 32, WHITE, "06.1f", 210)
        add(n)
        keyframes(scene, n, "value", [value, end, end - 12, end + 5, end], easing=smooth)
        add(segment((1424, y + 50), (1834, y + 50), "#23566470"))
    # Angular spacecraft silhouette and a vertical scan curtain.
    craft = Polyline(
        (
            (1630, 728),
            (1654, 765),
            (1748, 804),
            (1671, 799),
            (1655, 836),
            (1630, 814),
            (1605, 836),
            (1589, 799),
            (1512, 804),
            (1606, 765),
        ),
        closed=True,
        fill="#153D4D70",
        stroke=CYAN,
        stroke_width=2,
    )
    add(
        craft,
        segment((1630, 731), (1630, 816), DIM),
        segment((1589, 799), (1654, 765)),
        segment((1671, 799), (1606, 765)),
    )
    scan = Rectangle(width=260, height=4, fill=AMBER, stroke=None, position=(1630, 734))
    add(scan)
    keyframes(scene, scan, "position", [(1630, 734 if i % 2 == 0 else 836) for i in range(19)])

    # Lower strip: graphical spectrum and changing mission state.
    add(segment((86, 870), (1834, 870)), label("SPECTRAL DENSITY", 86, 894, 12, CYAN))
    for i in range(65):
        h = 9 + 34 * abs(math.sin(i * 0.37) * math.cos(i * 0.11))
        bar = Rectangle(
            width=5,
            height=h,
            fill=CYAN if i % 9 else AMBER,
            stroke=None,
            anchor="top_left",
            position=(88 + i * 6.2, 958 - h),
        )
        add(bar)
        keyframes(scene, bar, "height", [h, 8 + h * 0.4, h * 0.8, h * 1.1, 9, h], easing=smooth)
    add(label("CONTACTS", 1430, 895, 12), label("08", 1430, 915, 35, WHITE), label("CONFIDENCE", 1640, 895, 12))
    confidence = number(72, 1640, 915, 35, AMBER, "02.0f", 100)
    add(confidence, label("%", 1710, 930, 16, AMBER))
    keyframes(scene, confidence, "value", [72, 86, 94, 99, 99, 81])
    phases = (
        (0, 8, "ACQUIRING", CYAN),
        (8, 20, "TRACKING", CYAN),
        (20, 34, "TARGET LOCKED", AMBER),
        (34, 45, "RESCANNING", CYAN),
    )
    for start, end, title, color in phases:
        status = Group(
            Circle(4, position=(756, 913), fill=color, stroke=None),
            label(title, 776, 900, 19, color),
            label("SECTOR 04  /  ARRAY ACTIVE", 776, 932, 12),
        )
        with scene.at(start):
            scene.play(FadeIn(status), run_time=0.5)
        with scene.at(end - 0.4):
            scene.play(FadeOut(status), run_time=0.4)
    # Activation is quick; retain the instrument composition throughout the film.
    with scene.at(0):
        scene.play(FadeIn(base), run_time=1.2)
    scene.wait_until(DURATION)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="3-second sample of active tracking")
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame < DURATION:
        parser.error("frame time must be in [0, 45)")
    scene = build_scene()
    assert scene.duration == DURATION
    out = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png" if args.frame is not None else "preview.mp4" if args.preview else "skia-hud.mp4"
    )
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    out.parent.mkdir(parents=True, exist_ok=True)
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
                start_time=10 if args.preview else 0,
                end_time=13 if args.preview else DURATION,
                progress=progress,
                overwrite=args.overwrite,
            )
    out.with_suffix(".json").write_text(
        json.dumps(
            {
                "scene_duration": scene.duration,
                "range": [args.frame, args.frame] if args.frame is not None else [10, 13] if args.preview else [0, 45],
                "rendering": rendering_identity("skia", scene),
            },
            indent=2,
        )
    )
    print(out)


if __name__ == "__main__":
    main()
