"""A 60-second native Skia / PyVista engineering drawing study."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/faceless-skia-blueprint-mpl")

import numpy as np
import pyvista as pv

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Animation,
    ArchCamera,
    ArchChamp,
    ArchMesh,
    ArchPart,
    ArchScript,
    ArchStyle,
    Canvas,
    Circle,
    ExportProgress,
    ExportSettings,
    Group,
    Line,
    PathData,
    Polyline,
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
CYAN, WHITE, AMBER = "#75D9ED", "#E4F4F6", "#F4BD78"
DIM, GRID = "#31565F", "#0C1C22"


def text(value, x, y, size=24, color=WHITE):
    return Text(value, position=(x, y), font=CLEAN_FLOW_FONT, font_size=size, color=color, text_engine="skia")


def line(a, b, color=CYAN, width=1.5):
    return Polyline((a, b), stroke=color, stroke_width=width)


def field(pairs, color=DIM, width=1):
    return VectorPath(
        PathData(tuple(cmd for a, b in pairs for cmd in (("M", *a), ("L", *b)))),
        stroke=color,
        stroke_width=width,
    )


def frames(scene, obj, prop, values, start, end, easing=linear):
    values = tuple(values)
    with scene.at(start):
        scene.play(
            Animation(
                obj,
                {prop: values[-1]},
                starts={prop: values[0]},
                keyframes={prop: tuple((i / (len(values) - 1), value) for i, value in enumerate(values))},
                rate_func=easing,
            ),
            run_time=end - start,
        )


def show(scene, obj, start, end=60, fade=0.65):
    with scene.at(start):
        scene.add(obj)
    frames(scene, obj, "opacity", (0, 1), start, start + fade, smooth)
    if end < DURATION:
        frames(scene, obj, "opacity", (1, 0), end - fade, end, smooth)


def draw(scene, obj, start, end):
    frames(scene, obj, "draw", (0, 1), start, end)


def dashed(a, b, color=DIM, dash=15, gap=9):
    length = math.dist(a, b)
    dx, dy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    return field(
        [
            ((a[0] + p * dx, a[1] + p * dy), (a[0] + min(p + dash, length) * dx, a[1] + min(p + dash, length) * dy))
            for p in np.arange(0, length, dash + gap)
        ],
        color,
    )


def tip(point, angle, color=CYAN, size=10):
    # Open CAD arrowhead, pointing along the given screen-space angle.
    x, y = point
    dx, dy = math.cos(angle), math.sin(angle)
    shape = Polyline(
        (
            (x - size * dx + size * 0.32 * dy, y - size * dy - size * 0.32 * dx),
            (x, y),
            (x - size * dx - size * 0.32 * dy, y - size * dy + size * 0.32 * dx),
        ),
        stroke=color,
        stroke_width=1.5,
    )
    return Group(Circle(size * 1.1, position=point, opacity=0), shape)


def dimension(a, b, offset, value, color=CYAN):
    p = (a[0] + offset[0], a[1] + offset[1])
    q = (b[0] + offset[0], b[1] + offset[1])
    angle = math.atan2(q[1] - p[1], q[0] - p[0])
    vertical = abs(q[1] - p[1]) > abs(q[0] - p[0])
    label = text(
        value, (p[0] + q[0]) / 2 + (36 if vertical else 0), (p[1] + q[1]) / 2 - (0 if vertical else 23), 24, color
    )
    return Group(
        line(a, (p[0] + offset[0] * 0.08, p[1] + offset[1] * 0.08), DIM),
        line(b, (q[0] + offset[0] * 0.08, q[1] + offset[1] * 0.08), DIM),
        line(p, q, color, 1),
        tip(p, angle + math.pi, color),
        tip(q, angle, color),
        label,
    )


def leader(point, elbow, end, value, color=WHITE):
    return Group(
        Circle(3, position=point, fill=color, stroke=None),
        Polyline((point, elbow, end), stroke=color, stroke_width=1),
        text(value, end[0], end[1] - 21, 23, color),
    )


def ring_hatch(center, outer, inner, pitch=15, color=DIM):
    """Exact intersections of 45-degree hatch lines with an annulus."""
    pairs = []
    root = math.sqrt(2)
    for offset in np.arange(-outer + pitch / 2, outer, pitch):
        span = math.sqrt(max(0, outer * outer - offset * offset))
        intervals = [(-span, span)]
        if abs(offset) < inner:
            hole = math.sqrt(inner * inner - offset * offset)
            intervals = [(-span, -hole), (hole, span)]
        for lo, hi in intervals:
            pairs.append(tuple((center[0] + (s + offset) / root, center[1] + (s - offset) / root) for s in (lo, hi)))
    return field(pairs, color, 1)


def annulus(x0, x1, outer, inner, resolution=72):
    """Closed manifold lathed tube: real bore, caps and consistent winding."""
    profile = ((x0, inner), (x0, outer), (x1, outer), (x1, inner))
    points = [
        (x, r * math.cos(a), r * math.sin(a))
        for x, r in profile
        for a in np.linspace(0, math.tau, resolution, endpoint=False)
    ]
    faces = []
    for j in range(4):
        for k in range(resolution):
            faces.extend(
                (
                    4,
                    j * resolution + k,
                    j * resolution + (k + 1) % resolution,
                    ((j + 1) % 4) * resolution + (k + 1) % resolution,
                    ((j + 1) % 4) * resolution + k,
                )
            )
    return pv.PolyData(points, faces).triangulate().compute_normals(auto_orient_normals=True)


def assembly():
    shell = ArchStyle(concept="solid", color="#247087", smooth_shading=False)
    flange = ArchStyle(concept="solid", color="#7EBDC9", smooth_shading=False)
    brass = ArchStyle(concept="solid", color=AMBER, smooth_shading=False)
    parts = [
        ArchPart("body", ArchMesh.from_data(annulus(-48, 48, 26, 12)), style=shell, explode_vector=(0, 0, 0)),
        ArchPart("left", ArchMesh.from_data(annulus(-60, -48, 40, 12)), style=flange, explode_vector=(-27, 0, 0)),
        ArchPart("right", ArchMesh.from_data(annulus(48, 60, 40, 12)), style=flange, explode_vector=(27, 0, 0)),
        ArchPart(
            "shaft",
            ArchMesh.from_data(
                pv.Cylinder(direction=(1, 0, 0), radius=9, height=176, resolution=64).triangulate().clean()
            ),
            style=brass,
            explode_vector=(0, 0, 0),
        ),
    ]
    for i in range(6):
        a = math.tau * i / 6
        y, z = 32 * math.cos(a), 32 * math.sin(a)
        # Tie rods are embedded in the flange disks, with visible hexagonal heads.
        rod = pv.Cylinder(center=(0, y, z), direction=(1, 0, 0), radius=3, height=132, resolution=20)
        for x in (-65, 65):
            rod = rod.merge(pv.Cylinder(center=(x, y, z), direction=(1, 0, 0), radius=5, height=5, resolution=6))
        parts.append(
            ArchPart(
                f"rod-{i}", ArchMesh.from_data(rod.triangulate()), style=brass, explode_vector=(0, y * 0.22, z * 0.22)
            )
        )
    return parts


def elevations(scene):
    s, cx, cy = 5, 650, 470
    xy = lambda x, z: (cx + x * s, cy - z * s)
    outline = [
        (-60, -40),
        (-48, -40),
        (-48, -26),
        (48, -26),
        (48, -40),
        (60, -40),
        (60, 40),
        (48, 40),
        (48, 26),
        (-48, 26),
        (-48, 40),
        (-60, 40),
    ]
    profile = Polyline([xy(x, z) for x, z in outline], closed=True, stroke=CYAN, stroke_width=2.5)
    geometry = Group(
        profile,
        field([(xy(x, -40), xy(x, 40)) for x in (-48, 48)], CYAN),
        field([(xy(-88, z), xy(88, z)) for z in (-9, 9)], AMBER, 2),
        field([(xy(x, -9), xy(x, 9)) for x in (-88, 88)], AMBER, 2),
        dashed(xy(-60, -12), xy(60, -12)),
        dashed(xy(-60, 12), xy(60, 12)),
        dashed((160, cy), (1140, cy), DIM, 28, 8),
        dashed((cx, 215), (cx, 730), DIM, 28, 8),
    )
    show(scene, geometry, 0.5, 18.3)
    draw(scene, profile, 0.5, 3.2)
    for i, item in enumerate(
        (
            dimension(xy(-60, 40), xy(60, 40), (0, -100), "120 mm"),
            dimension(xy(-48, -26), xy(48, -26), (0, 162), "96"),
            dimension(xy(-60, -40), xy(-48, -40), (0, 86), "12"),
            leader(xy(10, 9), (930, 355), (1060, 355), "Ø18", AMBER),
        )
    ):
        show(scene, item, 3 + i * 0.6, 18.3)

    center = (1450, 470)
    end_parts = [
        Circle(r, position=center, fill=None, stroke=color, stroke_width=width)
        for r, color, width in ((200, CYAN, 2.5), (130, DIM, 1), (60, CYAN, 2), (45, AMBER, 2))
    ]
    end_parts += [dashed((1190, 470), (1710, 470)), dashed((1450, 210), (1450, 730))]
    for i in range(6):
        a = math.tau * i / 6
        p = (center[0] + 160 * math.cos(a), center[1] - 160 * math.sin(a))
        end_parts += [Circle(15, position=p, fill=None, stroke=AMBER, stroke_width=1.7)]
    view = Group(*end_parts)
    show(scene, view, 2.5, 18.3)
    show(scene, dimension((1650, 270), (1650, 670), (75, 0), "Ø80"), 6, 18.3)
    show(scene, leader((1490, 425), (1600, 185), (1700, 185), "Ø24 H7"), 7, 18.3)
    # Section arrows identify the axial station shown in the final section view.
    section = Group(
        dashed((380, 220), (380, 710), AMBER, 36, 12),
        tip((380, 220), 0, AMBER, 15),
        tip((380, 710), 0, AMBER, 15),
        text("A", 347, 210, 25, AMBER),
        text("A", 347, 710, 25, AMBER),
    )
    show(scene, section, 9, 18.3)

    # A continuous native cubic routing schematic with construction tangents.
    curve_path = PathData().move_to(340, 930).line_to(575, 930).cubic_to(655, 930, 655, 810, 735, 810)
    curve_path = curve_path.line_to(1160, 810).cubic_to(1240, 810, 1240, 930, 1320, 930).line_to(1580, 930)
    route = VectorPath(curve_path, stroke=CYAN, stroke_width=3)
    show(scene, route, 10.5, 18.3)
    draw(scene, route, 10.5, 14.5)
    show(
        scene,
        Group(
            field(
                [
                    ((575, 930), (655, 930)),
                    ((655, 930), (655, 810)),
                    ((655, 810), (735, 810)),
                    ((1160, 810), (1240, 810)),
                    ((1240, 810), (1240, 930)),
                    ((1240, 930), (1320, 930)),
                ],
                DIM,
            ),
            *[
                Circle(4, position=p, fill="#000000", stroke=DIM, stroke_width=1)
                for p in ((655, 930), (655, 810), (1240, 810), (1240, 930))
            ],
            leader((684, 853), (805, 922), (910, 922), "R16", CYAN),
        ),
        14.3,
        18.3,
    )


def projected_measure(scene, viewport, start, end):
    """Native Skia dimension tracks public ArchChamp projection during orbit."""
    times = np.linspace(0, end - start, 121)
    positions = [viewport.project_at(float(t), ((-48, 0, -26), (48, 0, -26)), part="body") for t in times]
    origin = (viewport.position[0] - viewport.width / 2, viewport.position[1] - viewport.height / 2)
    a = [(p[0][0] + origin[0], p[0][1] + origin[1]) for p in positions]
    b = [(p[1][0] + origin[0], p[1][1] + origin[1]) for p in positions]
    p, q = [(x, y + 150) for x, y in a], [(x, y + 150) for x, y in b]
    mid = [((x[0] + y[0]) / 2, (x[1] + y[1]) / 2) for x, y in zip(p, q)]
    angles = [math.degrees(math.atan2(y[1] - x[1], y[0] - x[0])) for x, y in zip(p, q)]
    main = Line(100, stroke=CYAN, stroke_width=1)
    ext1, ext2 = Line(160, rotation=90, stroke=DIM), Line(160, rotation=90, stroke=DIM)
    cap1, cap2 = tip((0, 0), math.pi), tip((0, 0), 0)
    label = text("96 mm", 0, 0, 25, CYAN)
    for obj in (main, ext1, ext2, cap1, cap2, label):
        show(scene, obj, start, end)
    for obj, samples in (
        (main, mid),
        (ext1, [(x, y + 75) for x, y in a]),
        (ext2, [(x, y + 75) for x, y in b]),
        (cap1, p),
        (cap2, q),
        (label, [(x, y + 29) for x, y in mid]),
    ):
        # Polyline normalizes its local bounds; preserve the tip coordinate offset.
        delta = obj.position if obj in (cap1, cap2) else (0, 0)
        frames(scene, obj, "position", [(x + delta[0], y + delta[1]) for x, y in samples], start, end)
    frames(scene, main, "width", [math.dist(x, y) for x, y in zip(p, q)], start, end)
    for obj in (main, cap1, cap2):
        frames(scene, obj, "rotation", angles, start, end)

    # A second projected anchor attaches the Ø18 leader to the moving shaft.
    anchors = [viewport.project_at(float(t), ((88, 0, 0),), part="shaft")[0] for t in times]
    anchors = [(x + origin[0], y + origin[1]) for x, y in anchors]
    elbow = (1560, 812)
    pointer = Line(100, stroke=AMBER, stroke_width=1)
    dot = Circle(3, fill=AMBER, stroke=None)
    for obj in (pointer, dot):
        show(scene, obj, start, end)
    frames(scene, dot, "position", anchors, start, end)
    frames(scene, pointer, "position", [((x + elbow[0]) / 2, (y + elbow[1]) / 2) for x, y in anchors], start, end)
    frames(scene, pointer, "width", [math.dist(p, elbow) for p in anchors], start, end)
    frames(
        scene,
        pointer,
        "rotation",
        [math.degrees(math.atan2(elbow[1] - y, elbow[0] - x)) for x, y in anchors],
        start,
        end,
    )
    show(scene, Group(text("Ø18", 1595, 840, 25, AMBER), line(elbow, (1645, 812), AMBER)), start, end)


def section_drawing(scene):
    center = (1430, 510)
    ring = Group(
        ring_hatch(center, 240, 72, 15, "#387381"),
        Circle(240, position=center, fill=None, stroke=CYAN, stroke_width=2.5),
        Circle(72, position=center, fill="#000000", stroke=CYAN, stroke_width=2),
        Circle(54, position=center, fill="#281F12", stroke=AMBER, stroke_width=2),
        ring_hatch(center, 54, 0, 12, "#9D7644"),
        dashed((1140, 510), (1720, 510)),
        dashed((1430, 220), (1430, 800)),
    )
    show(scene, ring, 43, 60, 1)
    for i in range(6):
        a = math.tau * i / 6
        p = (center[0] + 192 * math.cos(a), center[1] - 192 * math.sin(a))
        bolt = Group(
            Circle(18, position=p, fill="#1F1A10", stroke=AMBER, stroke_width=1.8), ring_hatch(p, 18, 0, 9, "#886540")
        )
        show(scene, bolt, 44 + i * 0.2)
    show(scene, text("A–A", 1430, 880, 30, CYAN), 44)
    show(scene, dimension((1670, 270), (1670, 750), (90, 0), "Ø80"), 46)
    show(scene, leader((1475, 453), (1570, 170), (1690, 170), "Ø24 H7"), 47)
    show(scene, leader((1622, 510), (1690, 820), (1780, 820), "6 × Ø6", AMBER), 48)
    # Thin scan traverses the section; hatch and measurements remain in place.
    scan = Line(570, position=(1145, 510), rotation=90, stroke="#F4BD7866", stroke_width=1)
    show(scene, scan, 49, 56)
    frames(scene, scan, "position", ((1145, 510), (1715, 510)), 49, 56)


def build_scene():
    scene = Scene(Canvas(1920, 1080, "#000000"))
    grid = field(
        [((x, 110), (x, 970)) for x in range(100, 1841, 40)] + [((100, y), (1840, y)) for y in range(110, 971, 40)],
        GRID,
    )
    show(scene, grid, 0, 60, 1)
    show(
        scene,
        field(
            [((x, 110), (x, 970)) for x in range(100, 1841, 200)]
            + [((100, y), (1840, y)) for y in range(110, 971, 200)],
            "#152C34",
        ),
        0,
        60,
        1,
    )
    elevations(scene)
    parts = assembly()
    ids = [p.id for p in parts]
    exploded = ArchScript().explode(ids, 1, at=3, duration=4, easing="smooth")
    exploded.orbit(18, at=0, duration=14, easing="smooth")
    exploded.explode(ids, 0, at=14, duration=4, easing="smooth").wait(4)
    camera = ArchCamera(position=(120, -360, 170), zoom=1.65)
    view = ArchChamp(parts, exploded, width=1520, height=830, position=(960, 480), camera=camera, units="mm")
    show(scene, view, 17.6, 40.5, 1)
    projected_measure(scene, view, 17.6, 39.6)
    show(scene, dashed((230, 480), (1690, 480), "#31565F88", 22, 10), 22, 38.8)

    cut = ArchScript()
    cut.section(
        ["body", "left", "right", "shaft"],
        (0, 0, 0),
        normal=(0, -1, 0),
        cap=True,
        contour=True,
        at=1,
        duration=4,
        easing="smooth",
    )
    cut.hide(["rod-2", "rod-3", "rod-4"], at=1, duration=0.01)
    cut.orbit(-10, at=6, duration=8, easing="smooth").wait(6)
    cutaway = ArchChamp(
        parts,
        cut,
        width=1030,
        height=780,
        position=(600, 505),
        camera=ArchCamera(position=(210, -310, 205), zoom=1.38),
        units="mm",
    )
    show(scene, cutaway, 39.8, 60, 0.9)
    section_drawing(scene)
    # A finished drawing holds for the final four seconds.
    scene.wait_until(DURATION)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"))
    mode.add_argument("--preview", action="store_true", help="Two-second exploded assembly excerpt")
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame < DURATION:
        parser.error("frame must be in [0, 60)")
    if args.range is not None and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 60")
    if args.fps <= 0:
        parser.error("fps must be positive")
    scene = build_scene()
    assert scene.duration == DURATION
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    source_range = args.range or (
        [args.frame, args.frame] if args.frame is not None else [24, 26] if args.preview else [0, 60]
    )
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "skia-blueprint.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.frame is not None:
        with create_renderer("skia", antialias=1) as renderer:
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
                progress=progress,
                overwrite=args.overwrite,
            )
    output.with_suffix(".json").write_text(
        json.dumps(
            {
                "scene_duration": DURATION,
                "source_range": source_range,
                "rendering": rendering_identity("skia", scene),
            },
            indent=2,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
