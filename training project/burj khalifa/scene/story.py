"""Cue-authored engineering film, composed entirely through public core/kit APIs."""

import math
import re
from dataclasses import replace
from pathlib import Path

import numpy as np
import pyvista as pv
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import ArchCanvas

from faceless_champ import (
    ArchCamera,
    ArchChamp,
    ArchDimension,
    ArchLabel,
    ArchScript,
    Arrow,
    Canvas,
    Group,
    Polyline,
    SubtitleTrack,
    Text,
)

from .model import (
    AMBER,
    BLUE,
    CYAN,
    MUTED,
    NAVY,
    ORANGE,
    WHITE,
    arrow,
    batch,
    curve,
    floor_plan,
    foundation,
    geometry,
    hexagon,
    part,
    prism,
    rotate_xy,
    tower,
)

PROJECT = Path(__file__).resolve().parents[1]
TRACK = SubtitleTrack.from_srt(PROJECT / "cue-per-word.srt", overlap_tolerance=0.001)
VIEWPORT = (1728, 888)
MOTION_END = TRACK.cues[-1].end
DURATION = 182.2


def normalized(text):
    return re.sub(r"[^a-z0-9 ]", "", text.lower())


def T(phrase):
    """Resolve a phrase to its original first word cue; never rescale source time."""
    tokens = normalized(phrase).split()
    words = [normalized(c.text) for c in TRACK.cues]
    for i in range(len(words) - len(tokens) + 1):
        if words[i : i + len(tokens)] == tokens:
            return TRACK.cues[i].start
    raise ValueError(f"Missing narration phrase: {phrase!r}")


CHAPTERS = (
    ("introduction", 0, 13.960),
    ("geometry", 13.960, 32.820),
    ("structure", 32.820, 70.080),
    ("aerodynamics", 70.080, 106.800),
    ("foundation", 106.800, 128.840),
    ("construction", 128.840, 166.920),
    ("final", 166.920, DURATION),
)


def camera(focus=(0, 0, 410), azimuth=-55, elevation=9, distance=1800, zoom=1):
    az, el = math.radians(azimuth), math.radians(elevation)
    offset = (math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))
    return ArchCamera(position=tuple(focus[i] + distance * offset[i] for i in range(3)), focal_point=focus, zoom=zoom)


def label(text, point, part_id=None, offset=(120, -45), color=WHITE):
    return ArchLabel(text, point, part_id, offset=offset, color=color, font_size=28)


def view(parts, script=None, *, span=1020, cam=None, labels=(), dimensions=()):
    """Specify framing as a vertical world span; use public viewport inspection."""
    script = script or ArchScript()
    cam = cam or camera()
    probe = ArchChamp(parts, script, camera=cam, width=VIEWPORT[0], height=VIEWPORT[1])
    fit = 2 * probe.parallel_scale / span
    data = script.to_dict()
    for action in data["actions"]:
        if action["kind"] == "camera_to":
            action["camera"]["zoom"] *= fit
    return ArchCanvas(
        parts,
        ArchScript.from_dict(data),
        camera=replace(cam, zoom=cam.zoom * fit),
        labels=tuple(labels),
        dimensions=tuple(dimensions),
        units="m",
        viewport=VIEWPORT,
    )


def shot(s, id, start, end, parts, script=None, **options):
    return s.add(view(parts, script, **options), id=id, at=start - s.start, duration=end - start)


def note(s, text, start=None, end=None, x=960, y=938, color=MUTED):
    start = s.start if start is None else start
    end = s.end if end is None else end

    def factory(ctx, bounds):
        return Text(text, font=ctx.theme.font, font_size=24, color=color, position=(x, y), align="center")

    return s.add_core(factory, id=f"note-{len(s.placements)}", at=start - s.start, duration=end - start, z_index=5)


def overlay(s, factory, start, end, id):
    return s.add_core(factory, id=id, at=start - s.start, duration=end - start, z_index=4)


def intro(s):
    cut = T("828m")
    shot(s, "opening", 0, cut, tower(), ArchScript().orbit(-4, at=0, duration=cut, easing="smooth"))
    parts = tower()
    parts += [part("wind", arrow((-160, 0, 420), (-35, 0, 420), 1.7), ORANGE)]
    angles = np.linspace(0, 1.7 * math.pi, 48)
    points = [(40 * math.cos(a), 40 * math.sin(a), 650) for a in angles]
    parts += [part("torsion", batch([curve(points, 0.8), arrow(points[-3], points[-1], 0.8)]), ORANGE)]
    script = (
        ArchScript()
        .orbit(-10, at=0, duration=3, easing="smooth")
        .show("wind", at=T("powerful winds") - cut, duration=0.1)
        .move("wind", (18, 0, 0), at=T("powerful winds") - cut, duration=1.5, easing="smooth")
        .show("torsion", at=T("twist") - cut, duration=0.1)
        .rotate("torsion", (0, 0, 65), at=T("twist") - cut, duration=1.5, easing="smooth")
        .opacity(["wind", "torsion"], 0, at=T("intelligent") - cut, duration=0.7, easing="smooth")
    )
    shot(
        s,
        "height-and-wind",
        cut,
        s.end,
        parts,
        script,
        cam=camera(azimuth=-59),
        dimensions=[ArchDimension((-74, 0, 0), (-74, 0, 828), offset=(-105, 0), precision=0, font_size=30)],
    )
    note(s, "Wind and forces · schematic", T("powerful winds"))


def geometry_scene(s):
    plan = floor_plan()
    top = ArchCamera(position=(0, -1, 260), focal_point=(0, 0, 0), up=(0, 1, 0))
    script = ArchScript().camera_to(top, at=0, duration=1.9, easing="smooth")
    for key, at in zip("abc", (T("a y shape"), T("three wings"), T("three wings") + 0.35)):
        script.show(f"plan-{key}", at=at - s.start, duration=0.1)
        script.opacity(f"plan-{key}", 1, at=at - s.start, duration=0.8, easing="smooth")
    script.highlight("plan-core", AMBER, at=T("central hexagonal core") - s.start, duration=1, easing="smooth")
    end = T("inspired by")
    shot(s, "plan-reveal", s.start, end, plan, script, span=165, cam=camera((0, 0, 0), elevation=60, distance=260))
    labels = [
        label("Hexagonal core", (0, 0, 5), "plan-core", (155, 10), AMBER),
        label("Three wings", (0, 48, 2), "plan-a", (-165, -65)),
    ]
    shot(s, "flower-and-light", end, s.end, plan, span=165, cam=top, labels=labels)

    def flower(ctx, bounds):
        paths = []
        for a in np.linspace(0, 2 * math.pi, 6, endpoint=False):
            points = []
            for t in np.linspace(0, 2 * math.pi, 48):
                r, w = 52 * (1 - math.cos(t)) / 2, 11 * math.sin(t)
                points.append((310 + r * math.cos(a) - w * math.sin(a), 420 + r * math.sin(a) + w * math.cos(a)))
            paths.append(Polyline(points, stroke=CYAN, stroke_width=2, fill=None, closed=True))
        paths.append(Text("Hymenocallis", font=ctx.theme.font, font_size=26, color=WHITE, position=(310, 510)))
        return Group(*paths)

    overlay(s, flower, end, T("this geometry"), "flower")

    def rays(ctx, bounds, incoming=False):
        arrows = []
        for angle in (90, 210, 330):
            a = math.radians(angle)
            dx, dy = math.cos(a), -math.sin(a)
            r0, r1 = (345, 260) if incoming else (260, 345)
            arrows.append(
                Arrow(
                    (960 + dx * r0, 540 + dy * r0),
                    (960 + dx * r1, 540 + dy * r1),
                    stroke=CYAN if incoming else AMBER,
                    stroke_width=3,
                    tip_size=12,
                )
            )
        return Group(*arrows)

    light, views = T("maximizing natural light"), T("panoramic views")
    overlay(s, lambda ctx, bounds: rays(ctx, bounds, incoming=True), light, views, "daylight")
    overlay(s, rays, views, s.end, "outward-views")
    note(s, "Natural light", light, views)
    note(s, "Panoramic views", views, s.end)


def structure_scene(s):
    a, b, c = T("at the center"), T("engineers call"), T("when wind")
    parts = tower(structure=True)
    shell = [
        replace(p, id="glass-" + p.id, style=replace(p.style, opacity=0.55))
        for p in tower("solid", facade=True)
        if p.id.startswith("wing")
    ]
    fade = ArchScript().opacity(
        [p.id for p in shell], 0, at=T("removing the glass") - s.start, duration=2.2, easing="smooth"
    )
    fade.camera_to(camera((0, 0, 315), elevation=14, zoom=1.12), at=0, duration=3, easing="smooth")
    shot(s, "expose-skeleton", s.start, a, parts + shell, fade)

    # A short storey assembly makes the real wall/column geometry readable.
    local = floor_plan()
    for key in "abc":
        i = "abc".index(key)
        angle = i * 120 + 90
        wallmesh = batch(
            [
                prism(rotate_xy([(7, y - 0.7), (51, y - 0.7), (51, y + 0.7), (7, y + 0.7)], angle), 2, 18)
                for y in (-4.2, 4.2)
            ]
        )
        local.append(part(f"wall-{key}", wallmesh, CYAN, explode=(*rotate_xy([(18, 0)], angle)[0], 0)))
        cols = [
            prism(
                rotate_xy([(x - 0.8, y - 0.8), (x + 0.8, y - 0.8), (x + 0.8, y + 0.8), (x - 0.8, y + 0.8)], angle),
                2,
                18,
            )
            for x in (20, 36, 49)
            for y in (-9, 9)
        ]
        local.append(part(f"column-{key}", batch(cols), MUTED, explode=(*rotate_xy([(18, 0)], angle)[0], 0)))
    local[0] = part("plan-core", prism(hexagon(12.8), 0, 21), AMBER)
    targets = [p.id for p in local if p.id != "plan-core"]
    script = (
        ArchScript()
        .explode(targets, 0.65, at=1, duration=1.7, easing="smooth")
        .explode(targets, 0, at=T("each wing supports") - a, duration=2, easing="smooth")
    )
    shot(
        s,
        "storey-assembly",
        a,
        b,
        local,
        script,
        span=190,
        cam=camera((0, 0, 5), elevation=48, distance=260),
        labels=[
            label("Concrete core", (0, 0, 21), "plan-core", (-230, -100), AMBER),
            label("Structural walls", (-4.2, 31, 15), "wall-a", (210, 55)),
            label("Perimeter columns", (-9, 49, 15), "column-a", (200, -50)),
        ],
    )
    shot(
        s,
        "buttressed-core",
        b,
        c,
        local,
        ArchScript().highlight(["wall-a", "wall-b", "wall-c"], AMBER, at=0, duration=1.4, easing="smooth"),
        span=180,
        cam=camera((0, 0, 5), elevation=48, distance=260),
        labels=[label("Buttressed core", (0, 0, 21), "plan-core", (210, -80), AMBER)],
    )
    twist = T("meanwhile")
    wind = part("lateral", arrow((-95, 0, 16), (-30, 0, 16), 1), ORANGE)
    shot(
        s,
        "lateral-resistance",
        c,
        twist,
        local + [wind],
        ArchScript()
        .move("lateral", (14, 0, 0), at=0, duration=1.7, easing="smooth")
        .highlight(["wall-b", "wall-c"], AMBER, at=1.7, duration=1.2, easing="smooth"),
        span=205,
        cam=camera((0, 0, 5), elevation=65, distance=260),
        labels=[label("Horizontal wind load", (-65, 0, 16), "lateral", (-170, -100))],
    )
    points = [(26 * math.cos(t), 26 * math.sin(t), 27) for t in np.linspace(0, 1.7 * math.pi, 50)]
    torsion = part("torsion", batch([curve(points, 0.5), arrow(points[-3], points[-1], 0.5)]), ORANGE)
    shot(
        s,
        "torsion-resistance",
        twist,
        s.end,
        local + [torsion],
        ArchScript().rotate("torsion", (0, 0, 90), at=0, duration=2, easing="smooth"),
        span=180,
        cam=camera((0, 0, 5), elevation=56, distance=260),
        labels=[label("Torsion resistance", (0, 0, 21), "plan-core", (220, -90), AMBER)],
    )
    note(s, "Forces · schematic", c)


def vortex_parts(heights, coherent=True):
    """Authored vortex paths; neither a fluid solution nor measured velocities."""
    result = []
    for i, z in enumerate(heights):
        rings = []
        for j in range(4):
            phase = j * math.pi if coherent else j * math.pi + i * 1.1
            center_x = 85 + j * 50
            center_y = (13 if j % 2 else -13) + (0 if coherent else 9 * math.sin(i * 1.6 + j))
            points = [
                (center_x + 19 * math.cos(t + phase), center_y + 18 * math.sin(t + phase), z)
                for t in np.linspace(0, 1.65 * math.pi, 32)
            ]
            rings.append(curve(points, 0.95))
        result.append(part(f"vortices-{i}", batch(rings), ORANGE))
    return result


def aero_scene(s):
    start = T("as air flows")
    shot(s, "wind-challenge", s.start, start, tower(), ArchScript().orbit(12, at=0, duration=3.5, easing="smooth"))
    cut = T("the burj khalifa solves")
    simple = part("prism", pv.Cube(center=(0, 0, 225), x_length=38, y_length=38, z_length=450), BLUE)
    vortices = vortex_parts((100, 225, 350))
    inflow = part("inflow", batch([arrow((-145, 0, z), (-40, 0, z), 1.1) for z in (100, 225, 350)]), CYAN)
    script = ArchScript()
    for i in range(3):
        script.move(f"vortices-{i}", (18, 0, 0), at=1, duration=min(4, cut - start - 1), easing="smooth")
    shot(
        s,
        "coherent-vortices",
        start,
        cut,
        [simple, inflow, *vortices],
        script,
        span=650,
        cam=camera((55, 0, 230), azimuth=-75, elevation=32),
        labels=[
            label("Constant cross-section", (0, 0, 450), "prism", (-170, -55)),
            label("Organized vortices", (170, 0, 225), offset=(185, 55), color=ORANGE),
        ],
    )
    end = T("this disrupts")
    script = ArchScript().camera_to(
        camera((0, 0, 440), elevation=15, zoom=1.35), at=T("notice how") - cut, duration=3, easing="smooth"
    )
    for i, key in enumerate("abc"):
        script.highlight(f"wing-{key}", AMBER, at=T("these setbacks") - cut + i * 0.7, duration=0.6, easing="smooth")
    shot(
        s,
        "spiraling-setbacks",
        cut,
        end,
        tower(),
        script,
        labels=[label("Spiraling setbacks", (-14, -12, 480), offset=(230, -40), color=AMBER)],
    )
    parts = tower() + vortex_parts((150, 330, 520), coherent=False)
    script = ArchScript()
    for i in range(3):
        script.move(f"vortices-{i}", (9 + i * 4, (i - 1) * 5, 0), at=i * 0.3, duration=3.6, easing="smooth")
    shot(
        s,
        "disrupted-rhythm",
        end,
        s.end,
        parts,
        script,
        span=1040,
        cam=camera((50, 0, 410), azimuth=-75, elevation=22),
        labels=[
            label("Changing cross-section", (0, 0, 510), offset=(-255, -30)),
            label("Disrupted rhythm", (170, 0, 330), offset=(185, 25), color=ORANGE),
        ],
    )
    note(s, "Wind flow · schematic, not CFD", start, x=450)


def foundation_scene(s):
    raft_time, pile_time = T("our reinforced"), T("beneath it")
    # Start at the base and track below grade. Soil section reveals actual piles.
    parts = foundation()
    script = (
        ArchScript()
        .camera_to(camera((0, 0, -22), azimuth=-55, elevation=18, distance=260), at=0, duration=2.5, easing="smooth")
        .section("soil", (0, 0, -20), (0, -1, 0), at=0.4, duration=2.5, cap=True, contour=True, easing="smooth")
    )
    shot(
        s,
        "below-grade",
        s.start,
        raft_time,
        parts,
        script,
        span=190,
        cam=camera((0, 0, 35), azimuth=-55, elevation=18, distance=260),
    )
    # Remove soil from the explanatory detail; thickness remains true in metres.
    cutaway = [p for p in parts if p.id != "soil"]
    loads = part("loads", batch([arrow((x, 8, 23), (x, 8, -4), 0.6) for x in (-27, 0, 27)]), ORANGE)
    shot(
        s,
        "raft-loads",
        raft_time,
        pile_time,
        [*cutaway, loads],
        ArchScript().move("loads", (0, 0, -3), at=0, duration=1.5, easing="smooth"),
        span=150,
        cam=camera((0, 0, -15), azimuth=-55, elevation=14, distance=260),
        labels=[label("Reinforced concrete raft", (-35, 0, -5), "raft", (-230, -65), AMBER)],
        dimensions=[ArchDimension((65, 0, -8.7), (65, 0, -5), offset=(90, -20), precision=1, font_size=28)],
    )
    shot(
        s,
        "pile-field",
        pile_time,
        s.end,
        [*cutaway, loads],
        ArchScript().highlight("piles", AMBER, at=T("192") - pile_time, duration=1.2, easing="smooth"),
        span=155,
        cam=camera((0, 0, -20), azimuth=-55, elevation=24, distance=260),
        labels=[
            label("192 reinforced concrete piles", (38, -20, -30), "piles", (170, 80), AMBER),
            label("Loads into the ground", (-20, 0, -48), offset=(-200, 55)),
        ],
    )
    note(s, "Foundation arrangement and forces · schematic")


def construction_scene(s):
    facade_time, heat_time, spire_time = T("finally"), T("specialized coatings"), T("above the reinforced")
    g = geometry()
    parts = tower(structure=True) + [
        part("pump-pipe", g["pump-pipe"], MUTED),
        part("pump-packet", g["pump-packet"], ORANGE),
    ]
    pump_start = T("engineers developed")
    script = (
        ArchScript()
        .show(["pump-pipe", "pump-packet"], at=T("how do you deliver") - s.start, duration=0.1)
        .move("pump-packet", (0, 0, 606), at=pump_start - s.start, duration=T("600") - pump_start, easing="smooth")
    )
    shot(
        s,
        "concrete-pumping",
        s.start,
        facade_time,
        parts,
        script,
        labels=[label("High-performance concrete", (-17, -20, 240), offset=(-270, 0), color=ORANGE)],
        dimensions=[ArchDimension((-70, -20, 0), (-70, -20, 606), offset=(-110, 0), precision=0, font_size=28)],
    )
    note(s, "Concrete pumping · schematic", T("how do you deliver"), facade_time)

    parts = tower("solid", facade=True)
    targets = [p.id for p in parts if p.id.startswith("wing") or p.id.startswith("bands")]
    # A slight separated start uses the same facade meshes, then reassembles them.
    parts = [
        replace(p, position=(*rotate_xy([(9, 0)], "abc".index(p.id[-1]) * 120 + 90)[0], 0)) if p.id in targets else p
        for p in parts
    ]
    script = ArchScript()
    for i, key in enumerate("abc"):
        script.move([f"wing-{key}", f"bands-{key}"], (0, 0, 0), at=i * 0.6, duration=1.6, easing="smooth")
    shot(
        s,
        "facade-assembly",
        facade_time,
        heat_time,
        parts,
        script,
        labels=[label("Nearly 26,000 glass panels", (0, 0, 380), offset=(260, -5))],
    )
    note(s, "Representative façade modules", facade_time, heat_time)

    glass = part("glass", pv.Cube(x_length=2.2, y_length=0.15, z_length=3.3), CYAN, opacity=0.42)
    coating = part(
        "coating", pv.Cube(center=(0, -0.10, 0), x_length=2.2, y_length=0.025, z_length=3.3), AMBER, opacity=0.5
    )
    sunlight = part(
        "sunlight", batch([arrow((-2.7, -2.5, z), (-0.5, -0.15, z), 0.025) for z in (-0.8, 0, 0.8)]), ORANGE
    )
    reflected = part("reflected", batch([arrow((-0.5, -0.2, z), (1.1, -2.1, z), 0.025) for z in (-0.8, 0, 0.8)]), AMBER)
    transmitted = part("transmitted", arrow((-0.5, 0.2, 0), (0.1, 1.0, 0), 0.02), ORANGE, opacity=0.4)
    shot(
        s,
        "solar-coating",
        heat_time,
        spire_time,
        [glass, coating, sunlight, reflected, transmitted],
        ArchScript().opacity("reflected", 0.95, at=0.2, duration=1, easing="smooth"),
        span=6.2,
        cam=camera((0, -0.5, 0), azimuth=-65, elevation=12, distance=15),
        labels=[
            label("Coated glass", (0.7, -0.1, 1.1), "glass", (175, -50), CYAN),
            label("Reduced heat gain", (0.1, 1, 0), offset=(170, 110), color=AMBER),
        ],
    )
    note(s, "Solar heat paths · schematic", heat_time, spire_time)
    shot(
        s,
        "steel-spire",
        spire_time,
        s.end,
        tower("solid", facade=True),
        ArchScript().highlight(["crown", "spire"], AMBER, at=0.2, duration=1.4, easing="smooth"),
        span=335,
        cam=camera((0, 0, 705), elevation=9),
        labels=[label("Structural steel spire", (0, 0, 775), "spire", (230, 0), AMBER)],
    )


def final_scene(s):
    script = ArchScript().orbit(-22, at=0, duration=MOTION_END - s.start, easing="smooth")
    wire = shot(s, "wireframe", s.start, s.end, tower(), script)
    block = view(tower("solid", facade=True), script)

    def initially_hidden(ctx, bounds):
        built = block.compose(ctx, bounds)
        built.root.opacity = 0
        return built

    solid = s.add_core(initially_hidden, id="complete")
    # Both layers share identical metre framing and cameras, despite different mesh batches.
    at = T("architecture mathematics") - s.start
    s.play(solid["model"], lambda c: c.animate.opacity_to(1), at=at, duration=3.2)
    s.play(wire["model"], lambda c: c.animate.opacity_to(0), at=at, duration=3.2)


AUTHORS = (intro, geometry_scene, structure_scene, aero_scene, foundation_scene, construction_scene, final_scene)


def build(ctx):
    from .audio import prepare_audio

    prepare_audio(ctx.root)
    ctx.canvas = Canvas(1920, 1080, NAVY)
    inter = Path.home() / ".local/share/fonts/inter/InterVariable.ttf"
    ctx.theme = replace(
        ctx.theme,
        name="burj-engineering",
        background=NAVY,
        surface=NAVY,
        font=str(inter) if inter.exists() else ctx.theme.font,
        foreground=WHITE,
        muted=MUTED,
        accent=CYAN,
        body_size=28,
        minimum_font_size=24,
    )
    ctx.captions = False
    video = Video(ctx)
    narration = video.narration(
        audio="output/narration.wav", subtitles="cue-per-word.srt", captions=False, overlap_tolerance=0.001
    )
    if abs(narration.duration - DURATION) > 1 / 48000:
        raise ValueError("Derived narration must retain its 182.200-second source clock")
    for (name, start, end), author in zip(CHAPTERS, AUTHORS):
        author(video.segment(name, start=start, duration=end - start))
    return video
