"""Great Thinkers — a 60-second, light-premium history timeline.

Rendering plan
--------------
2D   Skia: native vector paths, crisp editorial typography, gradients, masks.
2.5D Skia layers with parallax ellipses, layered depth, CPU glow/bloom and dust.
3D   ArchChamp (PyVista) transparent viewports composited inside dark specimen
     cards by the Skia renderer.

Only the name, year and one idea line appear per chapter. The persistent
timeline supplies continuity instead of extra labels.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
import pyvista as pv
from faceless_champ import (
    Animation,
    Bloom,
    Bounds,
    Canvas,
    Circle,
    Draw,
    EffectStack,
    Ellipse,
    GradientStop,
    Group,
    LinearGradient,
    OuterGlow,
    Polyline,
    Pulse,
    RadialGradient,
    Rectangle,
    Scene,
    ShadowStyle,
    Text,
    card_surface,
    gradient_surface,
    linear,
    smooth,
)
from faceless_champ.integrations.pyvista.camera import ArchCamera
from faceless_champ.integrations.pyvista.model import ArchMesh, ArchPart, ArchStyle
from facelesschamp_kit.engineering.clip import ArchChamp
from facelesschamp_kit.engineering.script import ArchScript

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SERIF = REPO / "assets/fonts/CormorantGaramond[wght].ttf"
SANS = REPO / "assets/fonts/SpaceGrotesk[wght].ttf"

W, H = 1920, 1080
DURATION = 60.0
FPS = 30

BG = "#F3EFE6"
INK = "#1C1A17"
INK_SOFT = "#4E483E"
MUTED = "#8B806C"
HAIR = "#D8CEBC"
GOLD = "#B4833C"
GOLD_LIGHT = "#D9B87A"
DARK = "#12151A"

XS = (240.0, 480.0, 720.0, 960.0, 1200.0, 1440.0, 1680.0)
TIMELINE_Y = 950.0

INTRO = (0.0, 6.5)
CHAPTERS = (
    ("confucius", 6.5, 13.5),
    ("socrates", 13.5, 20.5),
    ("leonardo", 20.5, 27.5),
    ("newton", 27.5, 35.0),
    ("darwin", 35.0, 42.0),
    ("curie", 42.0, 49.0),
    ("einstein", 49.0, 56.5),
)
OUTRO = (56.5, 60.0)

PEOPLE = (
    ("551 BCE", "Confucius", "Harmony is the order beneath things."),
    ("399 BCE", "Socrates", "The examined life is the only one."),
    ("1452", "Leonardo da Vinci", "Art and science speak one language."),
    ("1687", "Isaac Newton", "Nature obeys a hidden order."),
    ("1859", "Charles Darwin", "Life branches, adapts, endures."),
    ("1911", "Marie Curie", "Nothing is to be feared, only understood."),
    ("1915", "Albert Einstein", "Time bends around matter."),
)

# Dark specimen cards. Bounds are the visible face; the surface allocates
# transparent shadow clearance around them.
CARD_FACE = (1020.0, 240.0, 1780.0, 840.0)
CARD_CENTER = ((CARD_FACE[0] + CARD_FACE[2]) / 2, (CARD_FACE[1] + CARD_FACE[3]) / 2)
CARD_RADIUS = 36.0
CARD_SHADOW = ShadowStyle("#3B302040", blur=16, offset=(0, 12))
CARD_CLEARANCE = math.ceil(3 * CARD_SHADOW.blur + max(abs(v) for v in CARD_SHADOW.offset))


def label(value, *, size, weight, color, position, font=SANS, anchor="top_left"):
    return Text(
        value,
        font=font,
        font_weight=weight,
        font_size=size,
        color=color,
        position=position,
        anchor=anchor,
        text_engine="skia",
    )


def seed_draw(scene, shapes, at):
    with scene.at(at):
        scene.play(*(Animation(shape, {"draw": 0.0}, {"draw": 0.0}) for shape in shapes), run_time=0.000001)


def open_group(scene, group, start, *, fade_in=0.55):
    group.opacity = 0
    with scene.at(start):
        scene.add(group)
        scene.play(group.animate.opacity_to(1), run_time=fade_in, rate_func=smooth)


def close_group(scene, group, end, *, fade_out=0.45):
    with scene.at(end - fade_out):
        scene.play(group.animate.opacity_to(0), run_time=fade_out * 0.9, rate_func=smooth)
    with scene.at(end):
        scene.remove(group)


def background(scene):
    warm = gradient_surface(
        Bounds(0, 0, W, H),
        fill=RadialGradient(
            (
                GradientStop(0, "#E6D0A03A"),
                GradientStop(0.55, "#E6D0A010"),
                GradientStop(1, "#E6D0A000"),
            ),
            center=(0.82, 0.12),
            radius=0.92,
        ),
        opacity=1,
        z_index=-3,
    )
    scene.add(warm)


def timeline(scene):
    line = Polyline(((180, TIMELINE_Y), (1740, TIMELINE_Y)), stroke=HAIR, stroke_width=1.5, line_cap="round")
    with scene.at(0.4):
        scene.add(line)
        scene.play(Animation(line, {"draw": 0.0}, {"draw": 0.0}), run_time=0.000001)
    with scene.at(0.5):
        scene.play(Draw(line), run_time=1.8, rate_func=smooth)

    ticks = Group(*(Rectangle(width=1, height=8, fill=HAIR, position=(x, TIMELINE_Y)) for x in XS))
    ticks.opacity = 0
    with scene.at(0):
        scene.add(ticks)
    with scene.at(1.8):
        scene.play(ticks.animate.opacity_to(0.75), run_time=0.6, rate_func=smooth)

    markers = []
    for x in XS:
        marker = Group(
            Circle(11, fill="#B4833C22", stroke=None, position=(x, TIMELINE_Y)),
            Circle(4, fill=GOLD, stroke=None, position=(x, TIMELINE_Y)),
        )
        marker.opacity = 0
        with scene.at(0):
            scene.add(marker)
        markers.append(marker)

    cursor = Group(
        Circle(18, fill="#B4833C22", stroke=None, position=(XS[0], TIMELINE_Y)),
        Circle(7, fill=GOLD, stroke=None, position=(XS[0], TIMELINE_Y)),
    )
    cursor.opacity = 0
    with scene.at(0):
        scene.add(cursor)
    return markers, cursor


def intro(scene):
    eyebrow = label(
        "A 2,500-YEAR TIMELINE OF IDEAS",
        size=24,
        weight=500,
        color=MUTED,
        position=(960, 362),
        anchor="center",
    )
    title = label("Great Thinkers", size=158, weight=600, color=INK, position=(960, 500), font=SERIF, anchor="center")
    rule = Rectangle(width=140, height=2, fill=GOLD, stroke=None, position=(960, 610))
    rule.opacity = 0
    group = Group(eyebrow, title, rule)
    group.opacity = 0
    with scene.at(0):
        scene.add(group)
        scene.play(group.animate.opacity_to(1), run_time=0.7, rate_func=smooth)
    with scene.at(0.15):
        scene.play(
            eyebrow.animate.move_to(960, 330),
            title.animate.move_to(960, 470),
            rule.animate.move_to(960, 600),
            rule.animate.opacity_to(1),
            run_time=1.15,
            rate_func=smooth,
        )
    with scene.at(5.9):
        scene.play(group.animate.opacity_to(0), run_time=0.45, rate_func=smooth)
    with scene.at(6.5):
        scene.remove(group)
    return group


def text_block(year, name, idea):
    year_t = label(year, size=24, weight=500, color=GOLD, position=(180, 350))
    rule = Rectangle(width=48, height=2, fill=GOLD, stroke=None, position=(204, 388))
    name_t = label(name, size=108, weight=600, color=INK, position=(180, 416), font=SERIF)
    idea_t = label(idea, size=30, weight=400, color=INK_SOFT, position=(180, 582))
    return year_t, rule, name_t, idea_t


def slide_text(scene, parts, start):
    year_t, rule, name_t, idea_t = parts
    with scene.at(start + 0.12):
        scene.play(
            year_t.animate.move_to(180, 330),
            rule.animate.move_to(204, 372),
            name_t.animate.move_to(180, 392),
            idea_t.animate.move_to(180, 558),
            run_time=0.95,
            rate_func=smooth,
        )


def confuse_visual(start):
    cx, cy = 1360.0, 515.0
    specs = (
        (560, 210, "#B4833C4D"),
        (430, 160, "#B4833C80"),
        (300, 112, "#1C1A1799"),
        (180, 66, GOLD),
    )
    rings = [
        Ellipse(width=w, height=h, fill=None, stroke=color, stroke_width=1.7, position=(cx, cy))
        for w, h, color in specs
    ]
    for ring in rings:
        ring.scale = 0.72
    core = Group(Circle(21, fill=GOLD, stroke=None, position=(cx, cy)))
    visual = Group(*rings, core)
    visual.rotation = -14
    return visual, rings, core, (cx, cy)


def socrates_visual(start):
    cx, cy = 1360.0, 515.0
    turns, count = 3.0, 240

    def spiral(offset=(0, 0), radius=238, inner=22):
        points = []
        for i in range(count):
            t = i / (count - 1)
            angle = turns * math.tau * t
            r = inner + (radius - inner) * t
            points.append((cx + r * math.cos(angle) + offset[0], cy + r * math.sin(angle) + offset[1]))
        return points

    guide = Circle(252, fill=None, stroke=HAIR, stroke_width=1.2, position=(cx, cy), opacity=0.7)
    guide.scale = 0.92
    shade = Polyline(spiral((7, 9)), stroke="#C9BDA8", stroke_width=4.2, line_cap="round", opacity=0.55)
    spiral_line = Polyline(spiral(), stroke=INK, stroke_width=2.4, line_cap="round")
    dot = Circle(9, fill=GOLD, stroke=None, position=(cx, cy))
    dot.scale = 0.3
    visual = Group(guide, shade, spiral_line, dot)
    return visual, (shade, spiral_line), dot, guide


def leonardo_visual(start):
    cx, cy = 1360.0, 518.0
    circle = Circle(205, fill=None, stroke=INK, stroke_width=2.0, position=(cx, cy), shadow=ShadowStyle("#00000010", 8, (0, 6)))
    square = Rectangle(
        width=352,
        height=352,
        fill=None,
        stroke=GOLD,
        stroke_width=2.0,
        position=(cx, cy),
        rotation=8,
        shadow=ShadowStyle("#00000010", 8, (0, 6)),
    )

    spokes = []
    for i in range(12):
        angle = i * math.tau / 12
        x1, y1 = cx + 58 * math.cos(angle), cy + 58 * math.sin(angle)
        x2, y2 = cx + 205 * math.cos(angle), cy + 205 * math.sin(angle)
        spokes.append(Polyline(((x1, y1), (x2, y2)), stroke="#C9BDA8", stroke_width=1.2, line_cap="round"))
    spokes_group = Group(*spokes)
    spokes_group.opacity = 0

    points = []
    for i in range(230):
        t = i / 229
        angle = 0.35 + t * 2.15 * math.tau
        r = 14 * math.exp(0.193 * (angle - 0.35))
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    golden = Polyline(points, stroke=GOLD, stroke_width=1.8, line_cap="round", opacity=0.9)
    core = Circle(6, fill=GOLD, stroke=None, position=(cx, cy))
    visual = Group(circle, square, spokes_group, golden, core)
    return visual, (golden,), square, circle, spokes_group


def dark_card(bounds=CARD_FACE, radius=CARD_RADIUS, shadow=CARD_SHADOW):
    clearance = math.ceil(3 * shadow.blur + max(abs(v) for v in shadow.offset))
    left, top, right, bottom = bounds
    allocation = Bounds(left - clearance, top - clearance, right + clearance, bottom + clearance)
    card = card_surface(
        allocation,
        fill=LinearGradient((GradientStop(0, "#20252D"), GradientStop(1, "#0B0E12")), angle=140),
        radius=radius,
        shadow=shadow,
        render_mode="vector",
    )
    hairline = Rectangle(
        width=right - left,
        height=bottom - top,
        corner_radius=radius,
        fill=None,
        stroke="#C08A3E42",
        stroke_width=1,
        position=((left + right) / 2, (top + bottom) / 2),
    )
    return card, hairline


def newton_visual():
    card, hairline = dark_card()
    glow = gradient_surface(
        Bounds(CARD_FACE[0] + 40, CARD_FACE[1] + 20, CARD_FACE[2] - 40, CARD_FACE[3] - 20),
        fill=RadialGradient(
            (GradientStop(0, "#C08A3E40"), GradientStop(0.38, "#C08A3E14"), GradientStop(0.62, "#C08A3E00")),
            center=(0.5, 0.52),
            radius=0.45,
        ),
    )
    planet = ArchPart(
        "planet",
        ArchMesh.from_data(pv.Sphere(radius=0.98, theta_resolution=56, phi_resolution=56)),
        style=ArchStyle(concept="solid", color="#DCCCA9", edge_color="#C08A3E", smooth_shading=True),
    )
    ring_a = ArchPart(
        "orbit_a",
        ArchMesh.from_data(pv.ParametricTorus(ringradius=1.85, crosssectionradius=0.017)),
        rotation=(74, 0, 18),
        style=ArchStyle(concept="solid", color="#C08A3E", edge_color="#C08A3E"),
    )
    ring_b = ArchPart(
        "orbit_b",
        ArchMesh.from_data(pv.ParametricTorus(ringradius=1.55, crosssectionradius=0.010)),
        rotation=(50, 36, 66),
        style=ArchStyle(concept="solid", color="#C08A3E", edge_color="#C08A3E"),
    )
    script = ArchScript().orbit(52, duration=7.5, easing="smooth")
    view = ArchChamp(
        [planet, ring_a, ring_b],
        script,
        camera=ArchCamera(position=(180, -320, 210), focal_point=(0, 0, 0)),
        width=CARD_FACE[2] - CARD_FACE[0],
        height=CARD_FACE[3] - CARD_FACE[1],
        position=CARD_CENTER,
    )
    visual = Group(card, glow, view, hairline)
    return visual, view


def darwin_visual(start):
    cx, cy = 1360.0, 810.0
    ground = Ellipse(width=440, height=46, fill="#D8CEBC", stroke=None, position=(cx, 812), opacity=0.32)
    branches = []
    leaves = []

    def grow(x, y, angle, length, depth):
        x2 = x + math.cos(angle) * length
        y2 = y + math.sin(angle) * length
        if depth >= 4:
            color, width = INK, 5.0
        elif depth >= 2:
            color, width = "#6A6153", 3.0
        elif depth == 1:
            color, width = "#8B806C", 1.8
        else:
            color, width = GOLD, 1.3
        branches.append(
            (depth, Polyline(((x, y), (x2, y2)), stroke=color, stroke_width=width, line_cap="round"))
        )
        if depth == 0:
            leaves.append((x2, y2))
            return
        grow(x2, y2, angle - 0.43, length * 0.72, depth - 1)
        grow(x2, y2, angle + 0.43, length * 0.72, depth - 1)

    grow(cx, cy, -math.pi / 2, 148, 5)
    branch_parts = [branch for _, branch in branches]
    leaf_parts = [Circle(5.0, fill=GOLD, stroke=None, position=(x, y), scale=0.2) for x, y in leaves]
    visual = Group(ground, *branch_parts, *leaf_parts)
    return visual, branch_parts, leaf_parts, branches


def curie_visual(start):
    cx, cy = 1360.0, 515.0
    rings = [
        Ellipse(width=430, height=150, fill=None, stroke="#B4833C99", stroke_width=1.5, position=(cx, cy), rotation=0),
        Ellipse(width=430, height=150, fill=None, stroke="#B4833C77", stroke_width=1.4, position=(cx, cy), rotation=60),
        Ellipse(width=430, height=150, fill=None, stroke="#B4833C77", stroke_width=1.4, position=(cx, cy), rotation=120),
        Ellipse(width=500, height=176, fill=None, stroke="#D9B87A55", stroke_width=1.1, position=(cx, cy), rotation=30),
    ]
    electrons = []
    for rotation in (0, 60, 120):
        angle = math.radians(rotation)
        ex, ey = cx + 215 * math.cos(angle), cy + 215 * math.sin(angle)
        electrons.append(Circle(6, fill=GOLD_LIGHT, stroke=None, position=(ex, ey)))
    nucleus = Circle(
        30,
        fill=GOLD,
        stroke=None,
        position=(cx, cy),
        effects=EffectStack(glow=OuterGlow("#C08A3E", 38, 0.6), bloom=Bloom(16, 0.4, 0.7)),
    )
    halo = Circle(250, fill=None, stroke=HAIR, stroke_width=1.2, position=(cx, cy), opacity=0.65)
    atom = Group(*rings, *electrons, nucleus)
    atom.rotation = 0

    rng = random.Random(1911)
    dust = []
    for _ in range(22):
        angle, radius = rng.uniform(0, math.tau), rng.uniform(195, 330)
        size = rng.uniform(1.2, 3.0)
        opacity = rng.uniform(0.12, 0.34)
        dust.append(
            Circle(
                size,
                fill=GOLD if rng.random() < 0.65 else INK,
                stroke=None,
                position=(cx + radius * math.cos(angle), cy + radius * math.sin(angle)),
                opacity=opacity,
            )
        )
    visual = Group(halo, atom, *dust)
    return visual, atom, nucleus


def einstein_visual():
    card, hairline = dark_card()
    glow = gradient_surface(
        Bounds(CARD_FACE[0] + 170, CARD_FACE[1] + 120, CARD_FACE[2] - 170, CARD_FACE[3] - 120),
        fill=RadialGradient(
            (GradientStop(0, "#E0B56655"), GradientStop(0.35, "#C08A3E18"), GradientStop(0.6, "#C08A3E00")),
            center=(0.5, 0.55),
            radius=0.55,
        ),
    )
    plane = pv.Plane(i_size=6.2, j_size=6.2, i_resolution=48, j_resolution=48)
    points = np.asarray(plane.points).copy()
    radius2 = points[:, 0] ** 2 + points[:, 1] ** 2
    points[:, 2] = -1.15 * np.exp(-radius2 / 1.5)
    plane.points = points
    grid = ArchPart(
        "spacetime",
        ArchMesh.from_data(plane),
        style=ArchStyle(concept="wireframe", color="#C08A3E", edge_color="#C08A3E", line_width=1.3),
    )
    mass = ArchPart(
        "mass",
        ArchMesh.from_data(pv.Sphere(radius=0.28, theta_resolution=36, phi_resolution=36)),
        position=(0, 0, -0.92),
        style=ArchStyle(concept="solid", color="#F0E3C8", edge_color="#F0E3C8", smooth_shading=True),
    )
    initial = ArchCamera(position=(4.3, -5.9, 3.7), focal_point=(0, 0, -0.4))
    final = ArchCamera(position=(3.3, -5.0, 4.2), focal_point=(0, 0, -0.4))
    script = ArchScript().camera_to(final, duration=7.5, easing="smooth")
    view = ArchChamp(
        [grid, mass],
        script,
        camera=initial,
        width=CARD_FACE[2] - CARD_FACE[0],
        height=CARD_FACE[3] - CARD_FACE[1],
        position=CARD_CENTER,
    )
    core = Circle(6, fill="#F5E3B8", stroke=None, position=(CARD_CENTER[0], CARD_CENTER[1] + 4))
    visual = Group(card, glow, view, core, hairline)
    return visual, view


def outro(scene):
    title = label("Great Thinkers", size=132, weight=600, color=INK, position=(960, 400), font=SERIF, anchor="center")
    rule = Rectangle(width=90, height=2, fill=GOLD, stroke=None, position=(960, 490))
    rule.opacity = 0
    subtitle = label(
        "Ideas outlive their thinkers.", size=28, weight=400, color=MUTED, position=(960, 545), anchor="center"
    )
    labels = [
        label(year, size=17, weight=500, color=MUTED, position=(x, 992), anchor="center")
        for x, (year, _, _) in zip(XS, PEOPLE)
    ]
    for item in labels:
        item.opacity = 0
    group = Group(title, rule, subtitle, *labels)
    group.opacity = 0
    with scene.at(OUTRO[0]):
        scene.add(group)
        scene.play(group.animate.opacity_to(1), run_time=0.8, rate_func=smooth)
    with scene.at(OUTRO[0] + 0.1):
        scene.play(
            title.animate.move_to(960, 380),
            rule.animate.move_to(960, 465),
            rule.animate.opacity_to(1),
            subtitle.animate.move_to(960, 520),
            run_time=1.0,
            rate_func=smooth,
        )
    for i, item in enumerate(labels):
        with scene.at(OUTRO[0] + 0.55 + i * 0.07):
            scene.play(item.animate.opacity_to(1), run_time=0.3, rate_func=smooth)
    return group, labels


def _compose():
    scene = Scene(Canvas(W, H, BG))
    background(scene)
    markers, cursor = timeline(scene)
    intro_group = intro(scene)

    chapter_groups = {}
    chapter_parts = {}

    # Confucius — 2.5D perspective rings.
    start, end = CHAPTERS[0][1], CHAPTERS[0][2]
    parts = text_block(*PEOPLE[0])
    visual, rings, core, _ = confuse_visual(start)
    group = Group(*parts, visual)
    open_group(scene, group, start)
    slide_text(scene, parts, start)
    for i, ring in enumerate(rings):
        with scene.at(start + 0.25 + i * 0.1):
            scene.play(ring.animate.scale_to(1), run_time=1.25, rate_func=smooth)
    with scene.at(start + 0.3):
        scene.play(visual.animate.rotate_to(-6), run_time=6.0, rate_func=smooth)
    close_group(scene, group, end)
    chapter_groups["confucius"] = group
    chapter_parts["confucius"] = {"text": parts, "visual": visual}

    # Socrates — an inward spiral (2D vector, layered shadow).
    start, end = CHAPTERS[1][1], CHAPTERS[1][2]
    parts = text_block(*PEOPLE[1])
    visual, spirals, dot, guide = socrates_visual(start)
    group = Group(*parts, visual)
    open_group(scene, group, start)
    slide_text(scene, parts, start)
    seed_draw(scene, spirals, start)
    with scene.at(start + 0.18):
        scene.play(guide.animate.scale_to(1), run_time=1.1, rate_func=smooth)
    with scene.at(start + 0.35):
        scene.play(Draw(spirals[1]), run_time=3.8, rate_func=linear)
    with scene.at(start + 0.5):
        scene.play(Draw(spirals[0]), run_time=3.6, rate_func=linear)
    with scene.at(start + 0.35):
        scene.play(dot.animate.scale_to(1), run_time=0.6, rate_func=smooth)
    close_group(scene, group, end)
    chapter_groups["socrates"] = group
    chapter_parts["socrates"] = {"text": parts, "visual": visual}

    # Leonardo — circle, square, proportion, golden spiral.
    start, end = CHAPTERS[2][1], CHAPTERS[2][2]
    parts = text_block(*PEOPLE[2])
    visual, (golden,), square, circle, spokes = leonardo_visual(start)
    group = Group(*parts, visual)
    open_group(scene, group, start)
    slide_text(scene, parts, start)
    seed_draw(scene, (golden,), start)
    with scene.at(start + 0.3):
        scene.play(Draw(golden), run_time=3.6, rate_func=smooth)
    with scene.at(start + 0.3):
        scene.play(square.animate.rotate_to(-2), run_time=6.2, rate_func=smooth)
    with scene.at(start + 0.55):
        scene.play(spokes.animate.opacity_to(0.65), run_time=0.8, rate_func=smooth)
    close_group(scene, group, end)
    chapter_groups["leonardo"] = group
    chapter_parts["leonardo"] = {"text": parts, "visual": visual}

    # Newton — 3D planet and orbital rings.
    start, end = CHAPTERS[3][1], CHAPTERS[3][2]
    parts = text_block(*PEOPLE[3])
    visual, view = newton_visual()
    group = Group(*parts, visual)
    open_group(scene, group, start)
    slide_text(scene, parts, start)
    close_group(scene, group, end)
    chapter_groups["newton"] = group
    chapter_parts["newton"] = {"text": parts, "visual": visual, "view": view}

    # Darwin — recursive tree growth.
    start, end = CHAPTERS[4][1], CHAPTERS[4][2]
    parts = text_block(*PEOPLE[4])
    visual, branches, leaves, branch_data = darwin_visual(start)
    group = Group(*parts, visual)
    open_group(scene, group, start)
    slide_text(scene, parts, start)
    seed_draw(scene, branches, start)
    for depth, branch in branch_data:
        with scene.at(start + 0.35 + (5 - depth) * 0.5):
            scene.play(Draw(branch), run_time=0.55, rate_func=smooth)
    for i, leaf in enumerate(leaves):
        with scene.at(start + 3.0 + i * 0.012):
            scene.play(leaf.animate.scale_to(1), run_time=0.35, rate_func=smooth)
    close_group(scene, group, end)
    chapter_groups["darwin"] = group
    chapter_parts["darwin"] = {"text": parts, "visual": visual}

    # Curie — 2.5D atom with luminous nucleus and dust.
    start, end = CHAPTERS[5][1], CHAPTERS[5][2]
    parts = text_block(*PEOPLE[5])
    visual, atom, nucleus = curie_visual(start)
    group = Group(*parts, visual)
    open_group(scene, group, start)
    slide_text(scene, parts, start)
    with scene.at(start + 0.3):
        scene.play(atom.animate.rotate_to(9), run_time=6.2, rate_func=smooth)
    with scene.at(start + 1.2):
        scene.play(Pulse(nucleus, factor=1.07), run_time=2.4, rate_func=smooth)
    close_group(scene, group, end)
    chapter_groups["curie"] = group
    chapter_parts["curie"] = {"text": parts, "visual": visual}

    # Einstein — 3D warped spacetime grid.
    start, end = CHAPTERS[6][1], CHAPTERS[6][2]
    parts = text_block(*PEOPLE[6])
    visual, view = einstein_visual()
    group = Group(*parts, visual)
    open_group(scene, group, start)
    slide_text(scene, parts, start)
    close_group(scene, group, end)
    chapter_groups["einstein"] = group
    chapter_parts["einstein"] = {"text": parts, "visual": visual, "view": view}

    outro_group, outro_labels = outro(scene)

    # Timeline cursor and markers follow the seven chapters.
    for i, (_, start, _) in enumerate(CHAPTERS):
        x = XS[i]
        if i == 0:
            with scene.at(start + 0.05):
                scene.play(
                    cursor.animate.opacity_to(1),
                    markers[i].animate.opacity_to(1),
                    run_time=0.35,
                    rate_func=smooth,
                )
        else:
            with scene.at(start + 0.02):
                scene.play(
                    cursor.animate.move_to(x, TIMELINE_Y),
                    cursor.animate.opacity_to(1),
                    run_time=0.65,
                    rate_func=smooth,
                )
            with scene.at(start + 0.38):
                scene.play(markers[i].animate.opacity_to(1), run_time=0.32, rate_func=smooth)

    scene.wait_until(DURATION)
    return scene, {
        "intro": intro_group,
        "chapters": chapter_groups,
        "chapter_parts": chapter_parts,
        "outro": outro_group,
        "outro_labels": outro_labels,
        "markers": markers,
        "cursor": cursor,
    }


def build_scene():
    return _compose()[0]


def check_scene():
    scene, items = _compose()
    assert math.isclose(scene.duration, DURATION, abs_tol=1e-9), scene.duration
    assert len(CHAPTERS) == len(PEOPLE) == len(XS) == len(items["markers"])
    for year, name, idea in PEOPLE:
        assert year and name and idea
    texts = []
    for group in items["chapters"].values():
        for child in group.children:
            if isinstance(child, Text):
                texts.append(child)
            elif isinstance(child, Group):
                texts.extend(entry for entry in child.children if isinstance(entry, Text))
    for text in texts:
        assert text.bounds.left >= 0 and text.bounds.right <= W, (text.text, text.bounds)
    for key in ("newton", "einstein"):
        view = items["chapter_parts"][key]["view"]
        assert view.width == CARD_FACE[2] - CARD_FACE[0]
        assert view.height == CARD_FACE[3] - CARD_FACE[1]
    return {
        "status": "authored",
        "duration": DURATION,
        "canvas": [W, H],
        "fps": FPS,
        "backend": "skia",
        "chapters": [
            {"id": key, "start": start, "end": end, "year": PEOPLE[i][0], "name": PEOPLE[i][1]}
            for i, (key, start, end) in enumerate(CHAPTERS)
        ],
        "scene_modes": {
            "confucius": "2.5D layered rings",
            "socrates": "2D vector spiral",
            "leonardo": "2D vector proportion",
            "newton": "3D ArchChamp",
            "darwin": "2D vector tree",
            "curie": "2.5D glow + dust",
            "einstein": "3D ArchChamp",
        },
        "text_items": len(texts),
        "media_rendered": False,
        "full_export_verified": False,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(check_scene(), indent=2))
