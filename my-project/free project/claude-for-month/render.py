"""A silent 60-second cinematic motion graphic: one month, from idea to launch."""

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
    GradientStop,
    Group,
    PathData,
    Polyline,
    RadialGradient,
    Rectangle,
    Scene,
    ShadowStyle,
    Text,
    VectorPath,
    create_renderer,
    ease_out,
    linear,
    render,
    rendering_identity,
    save_frame,
    smooth,
)

ROOT = Path(__file__).resolve().parent
DURATION = 60.0
CANVAS = (1920.0, 1080.0)
HERO = (1268.0, 508.0)
BG = "#F2EDE4"
INK = "#1B1A1E"
MUTED = "#756F65"
CARD = "#FFFCF5"

ACTS = (
    ("EXPLORE", "#6558D6", "#1F8B86"),
    ("BUILD", "#147F75", "#8C8A1C"),
    ("SHIP", "#C9583B", "#9A791C"),
)


def polar(radius: float, degrees: float, center: tuple[float, float] = (0.0, 0.0)) -> tuple[float, float]:
    angle = math.radians(degrees)
    return center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle)


def mix(a: str, b: str, amount: float) -> str:
    a, b = a.lstrip("#"), b.lstrip("#")
    channels = []
    for index in (0, 2, 4):
        left, right = int(a[index : index + 2], 16), int(b[index : index + 2], 16)
        channels.append(round(left + (right - left) * amount))
    return "#" + "".join(f"{value:02X}" for value in channels)


def line(points, color: str = INK, width: float = 2.0, cap: str = "round") -> Polyline:
    return Polyline(tuple(points), stroke=color, stroke_width=width, line_cap=cap)


def dot(x: float, y: float, radius: float, color: str, glow: str | None = None) -> Circle:
    shadow = ShadowStyle(glow + "4D", 18, (0, 0)) if glow else None
    return Circle(radius, position=(x, y), fill=color, stroke=None, shadow=shadow)


def arc_path(
    radius: float,
    start: float,
    end: float,
    color: str,
    width: float = 2.0,
    center: tuple[float, float] = (0.0, 0.0),
) -> VectorPath:
    count = max(1, math.ceil(abs(end - start) / 60))
    path = PathData().move_to(*polar(radius, start, center))
    for index in range(count):
        a = math.radians(start + (end - start) * index / count)
        b = math.radians(start + (end - start) * (index + 1) / count)
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


def field(pairs, color: str, width: float = 1.0) -> VectorPath:
    commands = tuple(command for a, b in pairs for command in (("M", *a), ("L", *b)))
    return VectorPath(PathData(commands), stroke=color, stroke_width=width)


def right_text(text: str, x: float, y: float, *, size: float, color: str, weight: float = 500) -> Text:
    label = Text(
        text,
        font=CLEAN_FLOW_FONT,
        font_size=size,
        font_weight=weight,
        color=color,
        text_engine="skia",
        anchor="top_left",
    )
    label.move_to(x - label.bounds.width, y)
    return label


def track(scene: Scene, obj, prop: str, values, start: float, end: float, easing=smooth) -> None:
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


# ---------------------------------------------------------------------------
# Generative project sigils. Every day gets a different visual family so the
# film communicates range without labels: foundations, interfaces, systems,
# data, 3D, sound, motion and launch.
# ---------------------------------------------------------------------------


def m_orbit(day: int, p1: str, p2: str):
    parts, draws = [], []
    parts.append(Circle(174, fill=None, stroke=p1 + "2C", stroke_width=1.2))
    for radius, start, end, color, width in (
        (100, -80, 120, p1, 2.6),
        (142, 40, 250, p2, 2.0),
        (184, 140, 380, p1 + "B0", 1.3),
    ):
        arc = arc_path(radius, start, end, color, width)
        parts.append(arc)
        draws.append(arc)
    for index, (radius, degrees, color) in enumerate(((100, 120, p2), (142, 250, INK), (184, 380, p1))):
        x, y = polar(radius, degrees)
        parts.append(dot(x, y, 6 if index == 0 else 4, color, glow=color if index < 2 else None))
    parts.append(dot(0, 0, 12, p1, glow=p1))
    for degrees in (0, 90, 180, 270):
        parts.append(line((polar(210, degrees), polar(226, degrees)), INK + "30", 1.2))
    return parts, draws


def m_compass(day: int, p1: str, p2: str):
    parts, draws = [], []
    parts.extend(
        (
            Circle(188, fill=None, stroke=p1 + "70", stroke_width=1.4),
            Circle(148, fill=None, stroke=p2 + "45", stroke_width=1),
        )
    )
    for index in range(24):
        degrees = index * 15
        inner, outer = ((168, 187) if index % 3 else (162, 194))
        parts.append(line((polar(inner, degrees), polar(outer, degrees)), INK + "40" if index % 3 else p2 + "AA", 1.2))
    for degrees in (0, 90, 180, 270):
        parts.append(line((polar(152, degrees), polar(206, degrees)), INK + "12", 1))
    parts.append(
        Polyline(
            ((0, -152), (34, -8), (0, 30), (-34, -8)),
            closed=True,
            fill=p2 + "D8",
            stroke=p2,
            stroke_width=1,
        )
    )
    parts.append(
        Polyline(
            ((0, 30), (18, 62), (0, 94), (-18, 62)),
            closed=True,
            fill=p1 + "55",
            stroke=p1 + "AA",
            stroke_width=1,
        )
    )
    parts.append(dot(0, 0, 10, INK, glow=p1))
    sweep = arc_path(168, -152, -12, p2, 2.2)
    parts.append(sweep)
    draws.append(sweep)
    return parts, draws


def m_grid(day: int, p1: str, p2: str):
    parts, draws = [], []
    count, step, size = 4, 62, 44
    for row in range(count):
        for column in range(count):
            index = row * count + column
            x = (column - (count - 1) / 2) * step
            y = (row - (count - 1) / 2) * step
            if (index * 3 + day * 5) % 11 < 4:
                fill, stroke, opacity = p1, None, 0.9
            elif (index + day) % 5 == 0:
                fill, stroke, opacity = p2 + "33", p2 + "99", 1.0
            else:
                fill, stroke, opacity = None, INK + "1C", 1.0
            parts.append(
                Rectangle(
                    width=size,
                    height=size,
                    corner_radius=10,
                    position=(x, y),
                    fill=fill,
                    stroke=stroke,
                    stroke_width=1.2,
                    opacity=opacity,
                )
            )
    frame = Rectangle(width=278, height=278, corner_radius=30, fill=None, stroke=p2 + "55", stroke_width=1.5)
    parts.append(frame)
    draws.append(frame)
    return parts, draws


def m_arcs(day: int, p1: str, p2: str):
    parts, draws = [], []
    for radius, start, end, color, width in (
        (78, -140, 40, p1, 2.8),
        (128, 50, 230, p2, 2.0),
        (178, 150, 400, p1 + "88", 1.4),
    ):
        arc = arc_path(radius, start, end, color, width)
        parts.append(arc)
        draws.append(arc)
        x, y = polar(radius, end)
        parts.append(dot(x, y, 4, color, glow=color if width > 2 else None))
        parts.append(line((polar(radius, end), polar(radius + 12, end)), INK + "44", 1.2))
    parts.append(dot(0, 0, 9, p1, glow=p1))
    for degrees in (0, 90, 180, 270):
        parts.append(line((polar(192, degrees), polar(212, degrees)), INK + "24", 1.2))
    return parts, draws


def m_code(day: int, p1: str, p2: str):
    parts, draws = [], []
    left = Polyline(((-152, -88), (-92, 0), (-152, 88)), stroke=p1, stroke_width=11)
    right = Polyline(((152, -88), (92, 0), (152, 88)), stroke=p2, stroke_width=11)
    parts.extend((left, right))
    draws.extend((left, right))
    for index, (width, color) in enumerate(
        ((118, p2 + "EE"), (176, INK + "30"), (96, INK + "20"), (148, p1 + "AA"))
    ):
        parts.append(
            Rectangle(
                width=width,
                height=11,
                corner_radius=5.5,
                position=(-18, -54 + index * 36),
                fill=color,
                stroke=None,
                opacity=0.95,
            )
        )
    parts.append(Rectangle(width=9, height=38, corner_radius=3, position=(96, 54), fill=p2, stroke=None))
    parts.append(dot(0, -112, 4, p1 + "AA"))
    return parts, draws


def m_wave(day: int, p1: str, p2: str):
    parts, draws = [], []
    phase = (day % 5) * 0.6
    for index, (amplitude, y_offset, color, width) in enumerate(
        ((26, -62, p1, 3.0), (44, 10, p2, 2.2), (58, 78, INK + "22", 1.2))
    ):
        points = [
            (x, y_offset + amplitude * math.sin(x / 56 + phase + index * 0.9)) for x in range(-228, 229, 7)
        ]
        wave = Polyline(points, stroke=color, stroke_width=width, line_cap="round")
        parts.append(wave)
        draws.append(wave)
        if index == 0:
            parts.append(dot(points[-1][0], points[-1][1], 5, p2, glow=p2))
    x = -180 + (day * 47) % 360
    parts.append(line(((x, -112), (x, 112)), p2 + "44", 1.2))
    return parts, draws


def m_bars(day: int, p1: str, p2: str, steps: bool = False):
    parts, draws = [], []
    count, first_x, step, base = 9, -196, 49, 104
    heights = []
    for index in range(count):
        height = 40 + index * 18 if steps else 54 + 120 * (0.5 + 0.5 * math.sin(index * 0.85 + day * 0.7))
        heights.append(height)
        color = p1 if index % 3 == 0 else p2 if index % 2 == 0 else INK + "22"
        parts.append(
            Rectangle(
                width=22,
                height=height,
                corner_radius=11,
                position=(first_x + index * step, base - height / 2),
                fill=color,
                stroke=None,
                opacity=0.92,
            )
        )
    parts.append(line(((-214, base), (214, base)), INK + "30", 1.2))
    tops = [(first_x + index * step, base - height - 14) for index, height in enumerate(heights)]
    trend = Polyline(tops, stroke=p2, stroke_width=2.6, line_cap="round")
    parts.append(trend)
    draws.append(trend)
    parts.append(dot(tops[-1][0], tops[-1][1], 6, p2, glow=p2))
    return parts, draws


def m_network(day: int, p1: str, p2: str):
    parts, draws = [], []
    outer = Circle(158, fill=None, stroke=p2 + "28", stroke_width=1.2)
    parts.append(outer)
    draws.append(outer)
    nodes = []
    for index in range(6):
        degrees = index * 60 + day * 7
        radius = 128 + 22 * math.sin(index * 1.7 + day)
        x, y = polar(radius, degrees)
        nodes.append((x, y))
        parts.append(line(((0, 0), (x, y)), p2 + "30" if index % 2 else INK + "18", 1.2))
    for index, (x, y) in enumerate(nodes):
        color = p1 if index % 3 == 0 else p2
        parts.append(dot(x, y, 9 if index % 2 else 7, color, glow=color if index % 3 == 0 else None))
    for index in range(0, 6, 2):
        x0, y0 = nodes[index]
        x1, y1 = nodes[(index + 1) % 6]
        parts.append(line(((x0, y0), (x1, y1)), p1 + "24", 1))
    parts.append(dot(0, 0, 21, p1, glow=p1))
    parts.append(Circle(35, fill=None, stroke=p1 + "44", stroke_width=1.2))
    return parts, draws


def cube_faces(cx: float, cy: float, scale: float, p1: str, p2: str):
    top = (
        (cx, cy - 105 * scale),
        (cx + 95 * scale, cy - 52 * scale),
        (cx, cy),
        (cx - 95 * scale, cy - 52 * scale),
    )
    left = (
        (cx - 95 * scale, cy - 52 * scale),
        (cx, cy),
        (cx, cy + 110 * scale),
        (cx - 95 * scale, cy + 58 * scale),
    )
    right = (
        (cx + 95 * scale, cy - 52 * scale),
        (cx, cy),
        (cx, cy + 110 * scale),
        (cx + 95 * scale, cy + 58 * scale),
    )
    return (
        Polyline(top, closed=True, fill=p1 + "C0", stroke=p1, stroke_width=1.5),
        Polyline(left, closed=True, fill=p2 + "36", stroke=p2 + "AA", stroke_width=1.2),
        Polyline(right, closed=True, fill=p1 + "22", stroke=p1 + "66", stroke_width=1.2),
    )


def m_cube(day: int, p1: str, p2: str, ribbon: bool = False, stack: bool = False):
    parts, draws = [], []
    if stack:
        for cx, cy, scale, color_a, color_b in (
            (0, 55, 0.66, p1, p2),
            (102, -110, 0.34, p2, p1),
        ):
            faces = cube_faces(cx, cy, scale, color_a, color_b)
            parts.extend(faces)
        draws.append(parts[0])
        parts.append(dot(-40, 205, 6, p2, glow=p2))
    else:
        scale = 0.86 if ribbon else 0.92
        faces = cube_faces(0, 0, scale, p1, p2)
        parts.extend(faces)
        draws.append(faces[0])
        if ribbon:
            parts.extend(
                (
                    line(((-95 * scale, -52 * scale), (95 * scale, -52 * scale)), INK + "66", 1.6),
                    line(((0, -105 * scale), (0, 0)), p2 + "AA", 1.6),
                    dot(112, -128, 5, p2, glow=p2),
                )
            )
            small = cube_faces(128, -112, 0.28, p2, p1)
            parts.extend(small)
    return parts, draws


def m_window(day: int, p1: str, p2: str):
    parts, draws = [], []
    parts.append(
        Rectangle(
            width=398,
            height=276,
            corner_radius=24,
            fill=CARD,
            stroke=p1 + "88",
            stroke_width=1.4,
            shadow=ShadowStyle("#1B1A1E1F", 30, (0, 18)),
        )
    )
    parts.append(line(((-199, -84), (199, -84)), p2 + "30", 1))
    for index in range(3):
        parts.append(Circle(5, position=(-170 + index * 20, -113), fill=(p1, p2, INK)[index], stroke=None, opacity=0.8))
    parts.append(Rectangle(width=52, height=6, corner_radius=3, position=(152, -113), fill=p2 + "44", stroke=None))
    parts.append(line(((-132, -84), (-132, 132)), INK + "18", 1))
    for index in range(3):
        parts.append(
            Rectangle(
                width=9,
                height=9,
                corner_radius=3,
                position=(-171, -46 + index * 28),
                fill=p1 if index == 0 else INK + "22",
                stroke=None,
            )
        )
    parts.append(Rectangle(width=126, height=52, corner_radius=10, position=(5, -28), fill=p1 + "99", stroke=None))
    parts.append(Rectangle(width=126, height=8, corner_radius=4, position=(5, 16), fill=INK + "22", stroke=None))
    parts.append(Rectangle(width=96, height=8, corner_radius=4, position=(-10, 34), fill=INK + "14", stroke=None))
    points = [(-70, 118), (-44, 96), (-16, 108), (12, 72), (40, 86), (72, 50), (100, 64), (132, 38)]
    chart = Polyline(points, stroke=p2, stroke_width=2.6, line_cap="round")
    parts.append(chart)
    draws.append(chart)
    parts.append(dot(points[-1][0], points[-1][1], 5, p2, glow=p2))
    return parts, draws


def m_terminal(day: int, p1: str, p2: str):
    parts, draws = [], []
    outer = Rectangle(
        width=398,
        height=266,
        corner_radius=22,
        fill=CARD,
        stroke=p2 + "88",
        stroke_width=1.4,
        shadow=ShadowStyle("#1B1A1E1F", 30, (0, 18)),
    )
    parts.append(outer)
    draws.append(outer)
    parts.append(line(((-198, -82), (198, -82)), p1 + "30", 1))
    for index in range(3):
        parts.append(Circle(5, position=(-170 + index * 20, -111), fill=(p2, INK, p1)[index], stroke=None, opacity=0.75))
    for index, (width, color) in enumerate(
        ((92, p2), (150, INK + "30"), (112, INK + "20"), (176, p1 + "88"), (74, INK + "20"))
    ):
        y = -52 + index * 32
        parts.append(dot(-164, y, 3, p2 if index == 0 else INK + "44"))
        parts.append(Rectangle(width=width, height=9, corner_radius=4.5, position=(-28, y), fill=color, stroke=None))
    parts.append(Rectangle(width=8, height=30, corner_radius=2, position=(92, 114), fill=p2, stroke=None))
    parts.append(Rectangle(width=330, height=4, corner_radius=2, position=(0, 116), fill=INK + "1A", stroke=None))
    parts.append(Rectangle(width=198, height=4, corner_radius=2, position=(-66, 116), fill=p2, stroke=None))
    return parts, draws


def m_dashboard(day: int, p1: str, p2: str):
    parts, draws = [], []
    parts.append(
        Rectangle(
            width=408,
            height=286,
            corner_radius=24,
            fill=CARD,
            stroke=p2 + "88",
            stroke_width=1.4,
            shadow=ShadowStyle("#1B1A1E1F", 30, (0, 18)),
        )
    )
    parts.append(line(((-204, -95), (204, -95)), p1 + "30", 1))
    for index in range(3):
        parts.append(Circle(5, position=(-174 + index * 20, -120), fill=(p2, p1, INK)[index], stroke=None, opacity=0.75))
    for x, y in ((-96, -30), (96, -30), (-96, 88), (96, 88)):
        parts.append(
            Rectangle(
                width=166,
                height=96,
                corner_radius=14,
                position=(x, y),
                fill=INK + "05",
                stroke=INK + "16",
                stroke_width=1,
            )
        )
    ring_center = (-96, -30)
    parts.append(Circle(30, position=ring_center, fill=None, stroke=p1 + "55", stroke_width=4))
    ring = arc_path(30, -90, 150, p1, 4, center=ring_center)
    parts.append(ring)
    draws.append(ring)
    parts.append(dot(ring_center[0], ring_center[1], 5, INK, glow=p1))
    for index in range(5):
        height = (18, 30, 24, 44, 36)[index]
        parts.append(
            Rectangle(
                width=12,
                height=height,
                corner_radius=6,
                position=(56 + index * 20, 8 - height / 2),
                fill=p1 if index % 2 else p2,
                stroke=None,
                opacity=0.85,
            )
        )
    points = [(-154, 112), (-132, 92), (-112, 102), (-92, 78), (-70, 86), (-48, 62), (-30, 72)]
    spark = Polyline(points, stroke=p2, stroke_width=2.4, line_cap="round")
    parts.append(spark)
    draws.append(spark)
    nodes = ((58, 68), (92, 58), (126, 78), (88, 110))
    for index, (x, y) in enumerate(nodes):
        parts.append(dot(x, y, 6, p1 if index % 2 else p2, glow=p1 if index == 0 else None))
    for a, b in (((58, 68), (92, 58)), ((92, 58), (126, 78)), ((92, 58), (88, 110)), ((58, 68), (88, 110))):
        parts.append(line((a, b), p2 + "33", 1))
    return parts, draws


def m_globe(day: int, p1: str, p2: str):
    parts, draws = [], []
    parts.append(
        Circle(
            168,
            fill=RadialGradient((GradientStop(0, p1 + "26"), GradientStop(1, p1 + "05"))),
            stroke=p1 + "AA",
            stroke_width=1.5,
        )
    )
    parts.append(Ellipse(width=430, height=120, fill=None, stroke=p2 + "33", stroke_width=1.2, rotation=-18))
    meridian = Ellipse(width=168, height=336, fill=None, stroke=p2 + "66", stroke_width=1.2)
    parts.append(meridian)
    draws.append(meridian)
    parts.append(Ellipse(width=300, height=78, fill=None, stroke=INK + "28", stroke_width=1))
    parts.append(Ellipse(width=222, height=56, fill=None, stroke=INK + "18", stroke_width=1, position=(0, -34)))
    for index, (x, y) in enumerate(((-62, -40), (26, 12), (72, -72), (-20, 82))):
        parts.append(dot(x + (day % 7) * 2, y, 5 if index == 0 else 3.5, p2, glow=p2 if index == 0 else None))
    return parts, draws


def m_signal(day: int, p1: str, p2: str):
    parts, draws = [], []
    origin = (0.0, 118.0)
    parts.append(dot(origin[0], origin[1], 14, p1, glow=p1))
    for index, radius in enumerate((64, 110, 156, 202)):
        color = p2 if index % 2 else p1
        arc = arc_path(radius, 220, 320, color + ("CC" if index < 2 else "66"), 2.8 if index == 0 else 1.8, center=origin)
        parts.append(arc)
        if index == 0:
            draws.append(arc)
        parts.append(dot(origin[0], origin[1] - radius, 3.5, color, glow=color if index == 0 else None))
    parts.append(line(((origin[0] - 42, origin[1] + 30), (origin[0] + 42, origin[1] + 30)), INK + "24", 1.2))
    return parts, draws


def m_arrow(day: int, p1: str, p2: str):
    parts, draws = [], []
    main = Polyline(((-112, 54), (0, -126), (112, 54)), stroke=p2, stroke_width=16, line_cap="round")
    parts.append(main)
    draws.append(main)
    parts.append(Polyline(((-74, 146), (0, 34), (74, 146)), stroke=p1 + "77", stroke_width=10, line_cap="round"))
    parts.append(line(((0, -150), (0, -214)), p1 + "66", 2))
    for y in (-160, -180, -200):
        parts.append(dot(0, y, 3.5, p1 + "AA"))
    parts.append(Circle(24, fill=None, stroke=p2 + "88", stroke_width=1.6, position=(0, -150)))
    parts.append(dot(0, -150, 5, p2, glow=p2))
    return parts, draws


def m_spiral(day: int, p1: str, p2: str):
    parts, draws = [], []
    points = []
    for index in range(200):
        t = index / 199
        points.append(polar(16 + 190 * t, -90 + t * 900))
    spiral = Polyline(points, stroke=p1, stroke_width=2.8, line_cap="round")
    parts.append(spiral)
    draws.append(spiral)
    second = []
    for index in range(200):
        t = index / 199
        second.append(polar(24 + 165 * t, 90 - t * 720))
    trail = Polyline(second, stroke=p2 + "AA", stroke_width=1.6, line_cap="round")
    parts.append(trail)
    draws.append(trail)
    parts.append(dot(0, 0, 8, p1, glow=p1))
    parts.append(dot(points[-1][0], points[-1][1], 6, p2, glow=p2))
    return parts, draws


def m_infinity(day: int, p1: str, p2: str):
    parts, draws = [], []
    points = [(190 * math.sin(t), 95 * math.sin(2 * t)) for t in (index / 239 * math.tau for index in range(240))]
    curve = Polyline(points, stroke=p1, stroke_width=3.2, line_cap="round")
    parts.append(curve)
    draws.append(curve)
    echo = [(190 * math.sin(t) * 0.86, 95 * math.sin(2 * t) * 0.86 + 10) for t in (index / 239 * math.tau for index in range(240))]
    parts.append(Polyline(echo, stroke=p2 + "66", stroke_width=1.4, line_cap="round"))
    parts.append(dot(0, 0, 7, INK, glow=p1))
    parts.append(dot(190, 0, 5, p2, glow=p2))
    parts.append(dot(-190, 0, 5, p2, glow=p2))
    return parts, draws


def m_shield(day: int, p1: str, p2: str):
    parts, draws = [], []
    points = ((0, -196), (162, -104), (154, 42), (0, 196), (-154, 42), (-162, -104))
    shield = Polyline(points, closed=True, fill=p1 + "18", stroke=p1, stroke_width=2.2)
    parts.append(shield)
    draws.append(shield)
    parts.append(Polyline(((-66, 0), (-12, 58), (84, -64)), stroke=p2, stroke_width=8, line_cap="round"))
    for index in range(3):
        parts.append(dot(112, -60 + index * 34, 3, p2 + "AA"))
    return parts, draws


def m_burst(day: int, p1: str, p2: str, rays: int):
    parts, draws = [], []
    for index in range(rays):
        degrees = 360 * index / rays + day * 3.7
        start = 64 + 18 * math.sin(index * 2.3 + day)
        end = 176 + 42 * math.sin(index * 1.7 + day * 0.6)
        color = p1 if index % 3 == 0 else p2 if index % 2 == 0 else INK + "66"
        parts.append(line((polar(start, degrees), polar(end, degrees)), color, 2.4 if index % 3 == 0 else 1.2))
        if index % 4 == 0:
            x, y = polar(end + 8, degrees)
            parts.append(dot(x, y, 3, color))
    parts.append(Circle(58, fill=None, stroke=p2 + "66", stroke_width=1.4))
    parts.append(Circle(136, fill=None, stroke=p1 + "24", stroke_width=1))
    parts.append(dot(0, 0, 14, p1, glow=p1))
    ring = Circle(196, fill=None, stroke=p1 + "22", stroke_width=1)
    parts.append(ring)
    draws.append(ring)
    return parts, draws


def build_motif(day: int, p1: str, p2: str):
    if day in (1, 10):
        return m_orbit(day, p1, p2)
    if day == 2:
        return m_compass(day, p1, p2)
    if day in (3, 18):
        return m_grid(day, p1, p2)
    if day in (4, 20):
        return m_arcs(day, p1, p2)
    if day == 5:
        return m_code(day, p1, p2)
    if day in (6, 17):
        return m_wave(day, p1, p2)
    if day == 7:
        return m_bars(day, p1, p2)
    if day in (8, 13):
        return m_network(day, p1, p2)
    if day == 9:
        return m_cube(day, p1, p2)
    if day in (11, 15):
        return m_window(day, p1, p2)
    if day == 12:
        return m_terminal(day, p1, p2)
    if day == 14:
        return m_dashboard(day, p1, p2)
    if day == 16:
        return m_cube(day, p1, p2)
    if day == 19:
        return m_spiral(day, p1, p2)
    if day == 21:
        return m_cube(day, p1, p2, ribbon=True)
    if day == 22:
        return m_shield(day, p1, p2)
    if day == 23:
        return m_globe(day, p1, p2)
    if day == 24:
        return m_signal(day, p1, p2)
    if day == 25:
        return m_arrow(day, p1, p2)
    if day == 26:
        return m_bars(day, p1, p2, steps=True)
    if day == 27:
        return m_cube(day, p1, p2, stack=True)
    if day == 28:
        return m_infinity(day, p1, p2)
    if day == 29:
        return m_burst(day, p1, p2, 18)
    return m_burst(day, p1, p2, 30)


def day_palette(day: int):
    if day <= 10:
        base, secondary = ACTS[0][1], ACTS[0][2]
    elif day <= 20:
        base, secondary = ACTS[1][1], ACTS[1][2]
    else:
        base, secondary = ACTS[2][1], ACTS[2][2]
    first = mix(base, INK, 0.055 * ((day - 1) % 5) / 4)
    second = mix(secondary, INK, 0.045 * ((day * 3) % 4) / 3)
    return first, second, base


# ---------------------------------------------------------------------------
# Scene assembly
# ---------------------------------------------------------------------------


def mini_card(day: int, kind: int, p1: str, p2: str, width: float, height: float, position, rotation: float):
    """A tiny geometric dashboard tile used as a satellite in each day poster."""
    parts = [
        Rectangle(
            width=width,
            height=height,
            corner_radius=18,
            fill=CARD,
            stroke=INK + "18",
            stroke_width=1,
            shadow=ShadowStyle("#1B1A1E1C", 24, (0, 14)),
        ),
        Circle(4, position=(-width / 2 + 18, -height / 2 + 17), fill=p1, stroke=None),
        line(
            ((-width / 2 + 31, -height / 2 + 17), (width / 2 - 16, -height / 2 + 17)),
            INK + "12",
            1,
        ),
    ]
    local = int((day * 7 + kind * 11) % 4)
    if local == 0:
        center = (-width / 2 + 44, height / 2 - 34)
        parts.append(Circle(22, position=center, fill=None, stroke=p1 + "2E", stroke_width=3))
        parts.append(arc_path(22, -90, 154, p1, 3, center=center))
        parts.append(dot(center[0], center[1], 4, p2, glow=p2))
        for index, bar_height in enumerate((15, 27, 20, 34)):
            parts.append(
                Rectangle(
                    width=7,
                    height=bar_height,
                    corner_radius=3.5,
                    position=(-6 + index * 18, 10 - bar_height / 2 + 4),
                    fill=p1 if index % 2 else p2 + "88",
                    stroke=None,
                )
            )
    elif local == 1:
        points = [
            (-width / 2 + 34 + index * ((width - 68) / 7), height / 2 - 32 - (index * 5 + 7 * math.sin(day + index)) % 30)
            for index in range(8)
        ]
        spark = Polyline(points, stroke=p1, stroke_width=2.2, line_cap="round")
        parts.append(spark)
        parts.append(dot(points[-1][0], points[-1][1], 4, p2, glow=p2))
        parts.append(line(((-width / 2 + 20, height / 2 - 24), (width / 2 - 20, height / 2 - 24)), INK + "10", 1))
    elif local == 2:
        base = height / 2 - 24
        for index, bar_height in enumerate((16, 28, 21, 38, 30, 44)):
            parts.append(
                Rectangle(
                    width=8,
                    height=bar_height,
                    corner_radius=4,
                    position=(-width / 2 + 36 + index * 20, base - bar_height / 2),
                    fill=p1 if index % 3 == 0 else p2 if index % 2 else p1 + "66",
                    stroke=None,
                )
            )
        parts.append(line(((-width / 2 + 18, base), (width / 2 - 18, base)), INK + "16", 1))
    else:
        nodes = (
            (-width / 2 + 34, 14),
            (-width / 2 + 78, -16),
            (width / 2 - 70, 12),
            (width / 2 - 28, -10),
        )
        for a, b in ((0, 1), (1, 2), (2, 3), (0, 2)):
            parts.append(line((nodes[a], nodes[b]), p1 + "44", 1))
        for index, node in enumerate(nodes):
            parts.append(dot(node[0], node[1], 5 if index % 2 else 3.5, p1 if index % 2 else p2))
    return Group(*parts, position=position, rotation=rotation, scale=0.94, opacity=0)


def connector_path(start, end, bend: float, color: str):
    c1 = (start[0] + (end[0] - start[0]) * 0.32, start[1] + bend)
    c2 = (start[0] + (end[0] - start[0]) * 0.68, end[1] + bend * 0.35)
    path = PathData().move_to(*start).cubic_to(*c1, *c2, *end)
    return VectorPath(path, stroke=color, stroke_width=1.4), c1, c2


def cubic_at(start, c1, c2, end, t: float):
    q = 1 - t
    return (
        q**3 * start[0] + 3 * q * q * t * c1[0] + 3 * q * t * t * c2[0] + t**3 * end[0],
        q**3 * start[1] + 3 * q * q * t * c1[1] + 3 * q * t * t * c2[1] + t**3 * end[1],
    )


def bloom_cloud(center, radius: float, color: str, secondary: str | None = None, core: bool = False):
    """Layered gradients that read as an optical bloom rather than a flat circle."""
    secondary = secondary or color
    layers = [
        Circle(
            radius * 2.35,
            position=center,
            fill=RadialGradient(
                (GradientStop(0, color + "0B"), GradientStop(0.52, color + "06"), GradientStop(1, color + "00"))
            ),
            stroke=None,
        ),
        Circle(
            radius * 1.18,
            position=center,
            fill=RadialGradient(
                (
                    GradientStop(0, secondary + "50"),
                    GradientStop(0.42, color + "22"),
                    GradientStop(1, color + "00"),
                )
            ),
            stroke=None,
        ),
        Circle(
            radius * 0.52,
            position=center,
            fill=RadialGradient((GradientStop(0, color + "A0"), GradientStop(0.55, color + "24"), GradientStop(1, color + "00"))),
            stroke=None,
        ),
    ]
    if core:
        layers.append(Circle(radius * 0.12, position=center, fill=color + "D0", stroke=None))
    return tuple(layers)


def sun_rays(center, inner: float, outer: float, color: str, count: int = 24, seed: int = 0, width: float = 1.1):
    rays = []
    for index in range(count):
        degrees = index * 360 / count + seed * 5.7
        length = inner + (outer - inner) * (0.32 + 0.68 * ((index * 37 + seed * 19) % 100) / 99)
        rays.append(
            line(
                (polar(inner, degrees, center), polar(length, degrees, center)),
                color if index % 3 else color + "88",
                width if index % 4 == 0 else width * 0.7,
            )
        )
    return tuple(rays)


def hero_stage(day: int, center, scale: float, p1: str, p2: str):
    """A signet, bloom, orbit rings and drafting ticks in one scalable group."""
    parts, draws = build_motif(day, p1, p2)
    motif = Group(*parts, position=center, scale=scale, rotation=-4)
    ring_radius = 210 * scale
    accent_arc = arc_path(ring_radius * 1.34, -148, 26, p1 + "70", 2.4, center=center)
    accent_arc_two = arc_path(ring_radius * 1.34, 54, 168, p2 + "50", 1.3, center=center)
    ornaments = [
        *bloom_cloud(center, ring_radius * 0.9, p1, p2),
        Circle(ring_radius, fill=None, stroke=p1 + "30", stroke_width=1.3, position=center),
        Circle(ring_radius * 1.18, fill=None, stroke=p2 + "20", stroke_width=1, position=center),
        Rectangle(
            width=ring_radius * 1.65,
            height=ring_radius * 1.65,
            corner_radius=ring_radius * 0.36,
            fill=None,
            stroke=p1 + "14",
            stroke_width=1,
            position=center,
            rotation=12,
        ),
        accent_arc,
        accent_arc_two,
    ]
    for index in range(24):
        degrees = index * 15
        ornaments.append(
            line(
                (polar(ring_radius + 8, degrees, center), polar(ring_radius + 18, degrees, center)),
                p1 + "55" if index % 3 == 0 else INK + "16",
                1.1,
            )
        )
    stage = Group(*ornaments, motif)
    return stage, (accent_arc, accent_arc_two, *draws), motif


def small_stage(day: int, center, scale: float, p1: str, p2: str):
    parts, draws = build_motif(day, p1, p2)
    ring_radius = 205 * scale
    return (
        Group(
            Circle(ring_radius, fill=None, stroke=p1 + "2A", stroke_width=1, position=center),
            *parts,
            position=center,
            scale=scale,
            rotation=3,
        ),
        draws,
    )


def make_satellites(day: int, center, ring_radius: float, p1: str, p2: str, specs):
    cards, connectors, packets = [], [], []
    for index, (angle, distance, width, height, rotation) in enumerate(specs):
        cx, cy = polar(distance, angle, center)
        card = mini_card(day, index, p1, p2, width, height, (cx, cy), rotation - 4)
        sx, sy = polar(ring_radius + 24, angle, center)
        bend = 76 if cy < center[1] else -76
        path, c1, c2 = connector_path((sx, sy), (cx, cy), bend, p1 + "55")
        packet = dot(sx, sy, 4.2, p2, glow=p2)
        packet.opacity = 0
        cards.append(card)
        connectors.append(path)
        packets.append((packet, (sx, sy), c1, c2, (cx, cy), index))
    return cards, connectors, packets


def animate_satellites(scene: Scene, satellites, start: float) -> None:
    cards, connectors, packets = satellites
    for index, card in enumerate(cards):
        card_start = start + 0.12 + index * 0.09
        end = card_start + 0.58
        x, y = card.position
        track(scene, card, "opacity", (0, 1), card_start, card_start + 0.22, ease_out)
        track(scene, card, "position", ((x, y + 16), (x, y)), card_start, end, ease_out)
        track(scene, card, "scale", (0.9, 1), card_start, end, ease_out)
    for index, path in enumerate(connectors):
        track(scene, path, "draw", (0, 1), start + 0.1 + index * 0.06, start + 0.72 + index * 0.06, ease_out)
    for packet, begin, c1, c2, finish, index in packets:
        packet_start = start + 0.24 + index * 0.08
        track(
            scene,
            packet,
            "position",
            tuple(cubic_at(begin, c1, c2, finish, step / 24) for step in range(25)),
            packet_start,
            packet_start + 0.72,
            linear,
        )
        track(scene, packet, "opacity", (0, 1, 1, 0), packet_start, packet_start + 0.76)


def add_section(scene: Scene, components, start: float, end: float, fade_in: float = 0.6, fade_out: float = 0.6):
    section = Group(*components, opacity=0 if fade_in else 1)
    with scene.at(0):
        scene.add(section)
    if fade_in:
        track(scene, section, "opacity", (0, 1), start, start + fade_in, ease_out)
    if end < DURATION:
        track(scene, section, "opacity", (1, 0), end - fade_out, end, ease_out)
    return section


def animate_title(scene: Scene, title: Text, start: float, drift: float = 20) -> None:
    x, y = title.position
    track(scene, title, "position", ((x, y + drift), (x, y)), start, start + 0.95, ease_out)
    track(scene, title, "reveal", (0, 1), start, start + 1.05, linear)


def act_header(index: int, name: str, days: str, color: str):
    label = Text(
        f"0{index} / {name}",
        font=CLEAN_FLOW_FONT,
        font_size=12,
        font_weight=700,
        color=color,
        text_engine="skia",
        position=(96, 158),
        anchor="top_left",
    )
    span = Text(
        f"DAYS {days}",
        font=CLEAN_FLOW_FONT,
        font_size=10,
        font_weight=600,
        color=MUTED,
        text_engine="skia",
        position=(96, 181),
        anchor="top_left",
    )
    return label, span


def cinematic_beat(
    scene: Scene,
    *,
    start: float,
    end: float,
    act_index: int,
    act_name: str,
    days: str,
    p1: str,
    p2: str,
    motif_day: int,
    center,
    scale: float,
    title_text: str,
    title_size: float = 76,
    secondary_day: int | None = None,
    secondary_center=(1010, 800),
    secondary_scale: float = 0.52,
    cards_spec=None,
    sweep: bool = False,
    rays: bool = False,
) -> None:
    wash = Circle(
        1120,
        position=(1440, 520),
        fill=RadialGradient(
            (
                GradientStop(0, mix(p1, BG, 0.84) + "C0"),
                GradientStop(0.55, mix(p2, BG, 0.92) + "66"),
                GradientStop(1, BG + "00"),
            )
        ),
        stroke=None,
    )
    lower_wash = Circle(
        700,
        position=(660, 940),
        fill=RadialGradient((GradientStop(0, mix(p2, BG, 0.94) + "99"), GradientStop(1, BG + "00"))),
        stroke=None,
    )
    ghost = Text(
        f"0{act_index}",
        font=CLEAN_FLOW_FONT,
        font_size=560,
        font_weight=600,
        color=p1 + "09",
        text_engine="skia",
        position=(1530, 620),
        anchor="top_left",
    )
    arcs = [
        arc_path(600, 142, 316, p1 + "30", 1.7, center=(1824, 108)),
        arc_path(760, 26, 172, p2 + "1C", 1.0, center=(1824, 108)),
        arc_path(780, 202, 330, p1 + "16", 1.1, center=(530, 1008)),
    ]
    particles = []
    for index in range(20):
        angle = index * 137.508 + act_index * 23 + motif_day * 7
        distance = 320 + (index * 79) % 300
        px, py = polar(distance, angle, center)
        if 40 < px < 1880 and 130 < py < 950:
            particles.append(
                Circle(
                    1.1 + (index % 3) * 0.6,
                    position=(px, py),
                    fill=p1 if index % 4 else p2,
                    stroke=None,
                    opacity=0.16 + (index % 4) * 0.045,
                )
            )

    stage, draws, motif = hero_stage(motif_day, center, scale, p1, p2)
    secondary = None
    secondary_draws = []
    if secondary_day is not None:
        secondary, secondary_draws = small_stage(secondary_day, secondary_center, secondary_scale, p1, p2)

    specs = cards_spec or (
        (208, 500, 204, 104, -4),
        (336, 500, 212, 102, 4),
        (118, 505, 190, 92, -3),
    )
    satellites = make_satellites(motif_day, center, 210 * scale, p1, p2, specs)

    header, span = act_header(act_index, act_name, days, p1)
    title = Text(
        title_text,
        font=CLEAN_FLOW_FONT,
        font_size=title_size,
        font_weight=300,
        color=INK,
        text_engine="skia",
        position=(96, 228),
        anchor="top_left",
        spacing=0,
    )
    rule = Rectangle(
        width=68,
        height=3,
        corner_radius=1.5,
        position=(130, 492),
        fill=p1,
        stroke=None,
        scale_x=0.001,
    )

    children = [
        wash,
        lower_wash,
        ghost,
        *arcs,
        *particles,
        *satellites[1],
        *satellites[0],
        secondary,
        stage,
        *(packet for packet, *_ in satellites[2]),
        header,
        span,
        title,
        rule,
    ]
    if rays:
        ray_group = Group(*sun_rays(center, 210 * scale + 40, 650, p1, 22, motif_day, 1.2))
        children.insert(3, ray_group)
    if sweep:
        sweep_group = Group(
            Rectangle(width=28, height=1600, fill=CARD + "1F", stroke=None),
            Rectangle(width=66, height=1600, fill=CARD + "12", stroke=None),
            Rectangle(width=132, height=1600, fill=CARD + "09", stroke=None),
            position=(720, 540),
            rotation=17,
            opacity=0,
        )
        children.append(sweep_group)

    children = [child for child in children if child is not None]
    add_section(scene, children, start, end, fade_in=0.55, fade_out=0.55)
    animate_title(scene, title, start)
    track(scene, stage, "scale", (1, 1.045), start, end, linear)
    track(scene, motif, "rotation", (-4, 2.5), start, end, linear)
    track(scene, rule, "scale_x", (0.001, 1), start + 0.4, start + 1.05, ease_out)
    animate_satellites(scene, satellites, start)
    for index, path in enumerate(arcs):
        track(scene, path, "draw", (0, 1), start + index * 0.05, start + 0.8 + index * 0.05, ease_out)
    for index, path in enumerate(draws[:5]):
        track(scene, path, "draw", (0, 1), start + index * 0.04, start + 0.75 + index * 0.04, ease_out)
    if secondary is not None:
        track(scene, secondary, "rotation", (3, -2), start, end, linear)
        for index, path in enumerate(secondary_draws[:2]):
            track(scene, path, "draw", (0, 1), start + index * 0.05, start + 0.8 + index * 0.05, ease_out)
    if rays:
        track(scene, ray_group, "rotation", (0, -7), start, end, linear)
        track(scene, ray_group, "scale", (0.82, 1.12), start, end, ease_out)
    if sweep:
        track(scene, sweep_group, "opacity", (0, 0.95, 0.95, 0), start + 0.5, start + 3.0)
        track(scene, sweep_group, "position", ((620, 540), (1290, 540)), start + 0.5, start + 2.8, linear)


def shot_cold_open(scene: Scene) -> None:
    center = (960, 540)
    p1, p2 = ACTS[0][1], ACTS[0][2]
    bloom = Group(*bloom_cloud(center, 285, p1, p2, core=True), scale=0.08, opacity=0)
    rays = Group(*sun_rays(center, 82, 540, p1, 30, 4, 1.1), scale=0.08, opacity=0)
    rings = []
    titles = [
        Text(
            "STARTS\nSMALL.",
            font=CLEAN_FLOW_FONT,
            font_size=104,
            font_weight=300,
            color=INK,
            text_engine="skia",
            position=center,
            align="center",
            spacing=0,
            opacity=0,
        ),
        Text(
            "ONE IDEA. THIRTY DAYS.",
            font=CLEAN_FLOW_FONT,
            font_size=17,
            font_weight=600,
            color=MUTED,
            text_engine="skia",
            position=(960, 690),
            align="center",
            opacity=0,
        ),
    ]
    for _ in range(3):
        rings.append(Circle(76, fill=None, stroke=p1 + "AA", stroke_width=1.3, position=center, opacity=0))
    section = add_section(scene, [bloom, rays, *rings, *titles], 0, 8.2, fade_in=0, fade_out=1.0)
    track(scene, bloom, "opacity", (0, 0.95), 0.1, 0.9, ease_out)
    track(scene, bloom, "scale", (0.08, 1.28), 0.1, 2.7, ease_out)
    track(scene, rays, "opacity", (0, 0.55), 0.5, 1.6, ease_out)
    track(scene, rays, "scale", (0.08, 1.3), 0.4, 3.0, ease_out)
    track(scene, rays, "rotation", (0, 12), 0, 8.0, linear)
    for ring, offset in zip(rings, (0.9, 2.3, 3.7)):
        track(scene, ring, "scale", (0.35, 5.6), offset, offset + 1.5, ease_out)
        track(scene, ring, "opacity", (0.55, 0), offset, offset + 1.5)
    track(scene, titles[0], "opacity", (0, 1), 0.7, 1.5, ease_out)
    track(scene, titles[0], "reveal", (0, 1), 0.95, 2.3, linear)
    track(scene, titles[0], "position", ((960, 560), center), 0.7, 2.0, ease_out)
    track(scene, titles[1], "opacity", (0, 1), 2.9, 3.7, ease_out)
    for title in titles:
        track(scene, title, "opacity", (1, 0), 5.4, 6.4, ease_out)
    track(scene, bloom, "scale", (1.28, 3.4), 5.4, 7.9, ease_out)
    track(scene, bloom, "opacity", (0.95, 0), 6.4, 7.9, ease_out)
    track(scene, section, "scale", (1, 1.02), 0, 8.0, linear)


def shot_explore(scene: Scene) -> None:
    p1, p2 = ACTS[0][1], ACTS[0][2]
    cinematic_beat(
        scene,
        start=8.0,
        end=13.05,
        act_index=1,
        act_name="EXPLORE",
        days="01—10",
        p1=p1,
        p2=p2,
        motif_day=1,
        center=(1400, 520),
        scale=1.85,
        title_text="FOLLOW\nTHE SIGNAL.",
        secondary_day=2,
        secondary_center=(1005, 792),
        secondary_scale=0.46,
        cards_spec=((208, 500, 204, 104, -4), (336, 470, 210, 102, 4), (118, 500, 190, 92, -3)),
    )
    cinematic_beat(
        scene,
        start=12.8,
        end=17.85,
        act_index=1,
        act_name="EXPLORE",
        days="01—10",
        p1=p1,
        p2=p2,
        motif_day=3,
        center=(1370, 500),
        scale=1.72,
        title_text="MAP\nTHE UNKNOWN.",
        secondary_day=5,
        secondary_center=(1000, 795),
        secondary_scale=0.48,
        cards_spec=((202, 495, 204, 104, -4), (344, 470, 208, 100, 4), (112, 500, 188, 90, -3)),
    )
    cinematic_beat(
        scene,
        start=17.6,
        end=22.2,
        act_index=1,
        act_name="EXPLORE",
        days="01—10",
        p1=p1,
        p2=p2,
        motif_day=8,
        center=(1375, 505),
        scale=1.9,
        title_text="MAKE\nCONNECTIONS.",
        title_size=70,
        secondary_day=6,
        secondary_center=(1008, 800),
        secondary_scale=0.46,
        cards_spec=((205, 500, 200, 102, -4), (334, 470, 210, 100, 4), (116, 500, 188, 90, -3)),
    )


def shot_build(scene: Scene) -> None:
    p1, p2 = ACTS[1][1], ACTS[1][2]
    cinematic_beat(
        scene,
        start=22.0,
        end=27.05,
        act_index=2,
        act_name="BUILD",
        days="11—20",
        p1=p1,
        p2=p2,
        motif_day=11,
        center=(1380, 505),
        scale=1.6,
        title_text="STRUCTURE\nTHE IDEA.",
        secondary_day=12,
        secondary_center=(1010, 795),
        secondary_scale=0.45,
        cards_spec=((205, 500, 204, 104, -4), (336, 470, 212, 104, 4), (118, 500, 190, 92, -3)),
        sweep=True,
    )
    cinematic_beat(
        scene,
        start=26.8,
        end=31.85,
        act_index=2,
        act_name="BUILD",
        days="11—20",
        p1=p1,
        p2=p2,
        motif_day=14,
        center=(1380, 505),
        scale=1.6,
        title_text="MAKE IT\nTANGIBLE.",
        secondary_day=16,
        secondary_center=(1008, 800),
        secondary_scale=0.5,
        cards_spec=((200, 500, 204, 104, -4), (340, 470, 208, 100, 4), (112, 505, 188, 90, -3)),
    )
    cinematic_beat(
        scene,
        start=31.6,
        end=36.2,
        act_index=2,
        act_name="BUILD",
        days="11—20",
        p1=p1,
        p2=p2,
        motif_day=13,
        center=(1375, 505),
        scale=1.85,
        title_text="TUNE\nTHE SYSTEM.",
        secondary_day=7,
        secondary_center=(1008, 800),
        secondary_scale=0.45,
        cards_spec=((205, 500, 204, 104, -4), (334, 470, 210, 100, 4), (116, 500, 188, 90, -3)),
    )


def shot_ship(scene: Scene) -> None:
    p1, p2 = ACTS[2][1], ACTS[2][2]
    cinematic_beat(
        scene,
        start=36.0,
        end=41.05,
        act_index=3,
        act_name="SHIP",
        days="21—30",
        p1=p1,
        p2=p2,
        motif_day=22,
        center=(1375, 505),
        scale=1.9,
        title_text="MAKE IT\nMATTER.",
        secondary_day=23,
        secondary_center=(1008, 800),
        secondary_scale=0.46,
        cards_spec=((205, 500, 204, 104, -4), (336, 470, 210, 100, 4), (116, 500, 190, 90, -3)),
        rays=True,
    )
    cinematic_beat(
        scene,
        start=40.8,
        end=45.85,
        act_index=3,
        act_name="SHIP",
        days="21—30",
        p1=p1,
        p2=p2,
        motif_day=24,
        center=(1335, 575),
        scale=1.95,
        title_text="SEND IT\nFORWARD.",
        secondary_day=25,
        secondary_center=(1030, 795),
        secondary_scale=0.52,
        cards_spec=((210, 500, 204, 104, -4), (338, 470, 210, 100, 4), (116, 500, 188, 90, -3)),
        rays=True,
    )
    cinematic_beat(
        scene,
        start=45.6,
        end=50.2,
        act_index=3,
        act_name="SHIP",
        days="21—30",
        p1=p1,
        p2=p2,
        motif_day=30,
        center=(1360, 495),
        scale=1.76,
        title_text="LAUNCH\nTHE MONTH.",
        title_size=72,
        secondary_day=28,
        secondary_center=(1008, 800),
        secondary_scale=0.5,
        cards_spec=((205, 500, 204, 104, -4), (336, 470, 210, 100, 4), (116, 500, 190, 90, -3)),
        rays=True,
    )


def day_tile(day: int, center, width: float = 180, height: float = 104):
    p1, p2, _ = day_palette(day)
    parts, _ = build_motif(day, p1, p2)
    icon = Group(*parts, position=(0, 9), scale=0.155, rotation=-2)
    number = Text(
        f"{day:02d}",
        font=CLEAN_FLOW_FONT,
        font_size=10,
        font_weight=700,
        color=MUTED,
        text_engine="skia",
        position=(-width / 2 + 14, -height / 2 + 10),
        anchor="top_left",
    )
    body = Rectangle(
        width=width,
        height=height,
        corner_radius=16,
        fill=CARD,
        stroke=INK + "18",
        stroke_width=1,
        shadow=ShadowStyle("#1B1A1E14", 18, (0, 10)),
    )
    edge = Rectangle(width=34, height=2, corner_radius=1, position=(width / 2 - 31, -height / 2 + 15), fill=p1, stroke=None)
    return Group(body, edge, icon, number, position=center, opacity=0, scale=0.86)


def shot_month(scene: Scene) -> None:
    p1, p2 = ACTS[2][1], ACTS[2][2]
    wash = Circle(
        1080,
        position=(960, 560),
        fill=RadialGradient(
            (
                GradientStop(0, mix(p1, BG, 0.9) + "B0"),
                GradientStop(0.58, mix(ACTS[1][2], BG, 0.94) + "66"),
                GradientStop(1, BG + "00"),
            )
        ),
        stroke=None,
    )
    bloom = Group(*bloom_cloud((960, 590), 330, p1, p2), scale=0.7, opacity=0.4)
    label = Text(
        "THIRTY DAYS. THIRTY BUILDS.",
        font=CLEAN_FLOW_FONT,
        font_size=46,
        font_weight=300,
        color=INK,
        text_engine="skia",
        position=(960, 142),
        align="center",
    )
    rule = Rectangle(width=860, height=1, fill=INK + "18", stroke=None, position=(960, 264), scale_x=0.001)
    tile_w, tile_h, gap_x, gap_y = 180, 104, 18, 18
    start_x = (1920 - (6 * tile_w + 5 * gap_x)) / 2 + tile_w / 2
    start_y = 332 + tile_h / 2
    tiles = []
    for index in range(30):
        row, column = divmod(index, 6)
        tile = day_tile(index + 1, (start_x + column * (tile_w + gap_x), start_y + row * (tile_h + gap_y)))
        tiles.append(tile)
    section = add_section(scene, [wash, bloom, label, rule, *tiles], 50.0, 56.8, fade_in=0.65, fade_out=0.6)
    track(scene, label, "reveal", (0, 1), 50.0, 51.1, linear)
    track(scene, label, "opacity", (0, 1), 50.0, 50.6, ease_out)
    track(scene, bloom, "scale", (0.7, 1.18), 50.0, 54.0, ease_out)
    track(scene, rule, "scale_x", (0.001, 1), 50.5, 51.5, ease_out)
    for index, tile in enumerate(tiles):
        tile_start = 50.8 + index * 0.035
        track(scene, tile, "opacity", (0, 1), tile_start, tile_start + 0.3, ease_out)
        track(scene, tile, "scale", (0.86, 1), tile_start, tile_start + 0.38, ease_out)
    track(scene, section, "scale", (1.0, 1.012), 50.0, 56.8, linear)


def shot_finale(scene: Scene) -> None:
    p1, p2 = ACTS[2][1], ACTS[2][2]
    bloom = Group(*bloom_cloud((960, 470), 330, p1, p2), scale=0.25, opacity=0)
    title = Text(
        "CLAUDE",
        font=CLEAN_FLOW_FONT,
        font_size=164,
        font_weight=600,
        color=INK,
        text_engine="skia",
        position=(960, 395),
        align="center",
        opacity=0,
    )
    subtitle = Text(
        "FOR A MONTH",
        font=CLEAN_FLOW_FONT,
        font_size=36,
        font_weight=400,
        color=MUTED,
        text_engine="skia",
        position=(960, 535),
        align="center",
        opacity=0,
    )
    tagline = Text(
        "ONE IDEA. THIRTY DAYS. SHIPPED.",
        font=CLEAN_FLOW_FONT,
        font_size=12,
        font_weight=700,
        color=INK,
        text_engine="skia",
        position=(960, 670),
        align="center",
        opacity=0,
    )
    rule = Rectangle(width=160, height=2, fill=p1, stroke=None, position=(960, 610), scale_x=0.001)
    add_section(scene, [bloom, title, subtitle, rule, tagline], 56.8, DURATION, fade_in=0.55, fade_out=0)
    track(scene, bloom, "opacity", (0, 0.92), 56.9, 57.8, ease_out)
    track(scene, bloom, "scale", (0.25, 1.14), 56.9, 59.1, ease_out)
    track(scene, title, "opacity", (0, 1), 57.1, 57.8, ease_out)
    track(scene, title, "reveal", (0, 1), 57.2, 58.2, linear)
    track(scene, subtitle, "opacity", (0, 1), 57.8, 58.5, ease_out)
    track(scene, rule, "scale_x", (0.001, 1), 58.0, 58.8, ease_out)
    track(scene, tagline, "opacity", (0, 1), 58.3, 59.0, ease_out)


def _legacy_build_scene() -> Scene:
    scene = Scene(Canvas(int(CANVAS[0]), int(CANVAS[1]), BG))

    def add_at_zero(*components):
        with scene.at(0):
            scene.add(*components)

    # Full-bleed paper, with two soft stains and a fine drafting field.
    glows = (
        Circle(
            760,
            position=(250, 870),
            fill=RadialGradient((GradientStop(0, "#D4C1A84A"), GradientStop(1, BG + "00"))),
            stroke=None,
        ),
        Circle(
            610,
            position=(560, 150),
            fill=RadialGradient((GradientStop(0, "#BFC8D13D"), GradientStop(1, BG + "00"))),
            stroke=None,
        ),
    )
    add_at_zero(*glows)
    track(scene, glows[0], "position", ((250, 870), (315, 805), (250, 870)), 0, DURATION)
    track(scene, glows[1], "position", ((560, 150), (505, 210), (560, 150)), 0, DURATION)

    dots = [((x, y), (x, y + 1)) for x in range(72, 1880, 42) for y in range(140, 946, 42)]
    add_at_zero(field(dots, INK + "09", 1.2))

    specks = []
    for index in range(46):
        x = 70 + (index * 271) % 1780
        y = 148 + (index * 167) % 790
        specks.append(Circle(1.0 + (index % 3) * 0.35, position=(x, y), fill=INK, stroke=None, opacity=0.08 + (index % 4) * 0.015))
    add_at_zero(*specks)

    # One second, one day: a full-width editorial poster, a giant date, and a
    # constellation of compact metric cards around the daily sigil.
    for day in range(1, 31):
        start, end = day - 1.0, float(day)
        p1, p2, _ = day_palette(day)
        parts, draws = build_motif(day, p1, p2)
        intro = day == 1

        field_rect = Rectangle(
            width=1290,
            height=1420,
            corner_radius=146,
            position=(1300, 540),
            fill=mix(p2, BG, 0.925),
            stroke=None,
        )
        accent_block = Rectangle(
            width=390,
            height=1500,
            corner_radius=195,
            position=(1718, 540),
            fill=p1 + "0A",
            stroke=None,
            rotation=15,
        )
        wash = Circle(
            560,
            position=(HERO[0] + 6, HERO[1]),
            fill=RadialGradient(
                (GradientStop(0, mix(p1, BG, 0.88) + "C8"), GradientStop(1, mix(p1, BG, 0.94) + "00"))
            ),
            stroke=None,
        )

        backdrop_arcs = []
        for radius, begin, finish, color, width, center in (
            (520, 148, 342, p1 + "30", 1.8, (1792, 116)),
            (690, 40, 190, p2 + "22", 1.1, (1812, 116)),
            (720, 205, 326, p1 + "14", 1.1, (602, 972)),
        ):
            backdrop_arcs.append(arc_path(radius, begin, finish, color, width, center=center))

        hero_ornaments = [
            Circle(382, fill=mix(p1, BG, 0.90), stroke=p1 + "24", stroke_width=1.2),
            Circle(338, fill=None, stroke=INK + "10", stroke_width=1),
            Rectangle(
                width=424,
                height=424,
                corner_radius=94,
                fill=None,
                stroke=p1 + "1A",
                stroke_width=1,
                rotation=12,
            ),
        ]
        for index in range(24):
            degrees = index * 15
            hero_ornaments.append(
                line(
                    (polar(360, degrees), polar(374, degrees)),
                    p1 + "55" if index % 3 == 0 else INK + "16",
                    1.2,
                )
            )
        hero_arc = arc_path(448, -145, 22, p1 + "AA", 2.4)
        hero_arc_two = arc_path(448, 58, 176, p2 + "70", 1.4)
        orbit_dot = dot(*polar(448, -145), 4.5, p2, glow=p2)
        hero_ornaments.extend((hero_arc, hero_arc_two, orbit_dot))

        motif = Group(*parts, position=(0, 0), scale=1.36, rotation=-4)
        hero = Group(*hero_ornaments, motif, position=HERO, scale=0.96)

        day_number = Text(
            f"{day:02d}",
            font=CLEAN_FLOW_FONT,
            font_size=316,
            font_weight=300,
            color=INK,
            text_engine="skia",
            position=(92, 202),
            anchor="top_left",
        )
        act_name = Text(
            ACTS[0][0] if day <= 10 else ACTS[1][0] if day <= 20 else ACTS[2][0],
            font=CLEAN_FLOW_FONT,
            font_size=20,
            font_weight=600,
            color=p1,
            text_engine="skia",
            position=(98, 566),
            anchor="top_left",
        )
        act_rule = Rectangle(width=96, height=3, corner_radius=1.5, position=(146, 606), fill=p1, stroke=None)
        ripple = Circle(64, fill=None, stroke=p2 + "AA", stroke_width=1.5, position=HERO, opacity=0.8)

        cards, connectors, packets = [], [], []
        card_specs = (
            (-462, -252, 214, 108, -5),
            (452, -230, 208, 112, 4),
            (420, 258, 244, 104, -3),
            (-438, 260, 188, 96, 5),
        )
        for index, (dx, dy, width, height, angle) in enumerate(card_specs):
            cx, cy = HERO[0] + dx, HERO[1] + dy
            card = mini_card(day, index, p1, p2, width, height, (cx, cy + 16), angle - 4)
            distance = max(1.0, math.hypot(dx, dy))
            sx, sy = HERO[0] + dx / distance * 346, HERO[1] + dy / distance * 346
            bend = 74 if dy < 0 else -74
            path, c1, c2 = connector_path((sx, sy), (cx, cy), bend, p1 + "50")
            packet = dot(sx, sy, 4.2, p2, glow=p2)
            packet.opacity = 0
            cards.append(card)
            connectors.append(path)
            packets.append((packet, (sx, sy), c1, c2, (cx, cy), index, angle, cx, cy))

        layer = Group(
            field_rect,
            accent_block,
            wash,
            *backdrop_arcs,
            *connectors,
            ripple,
            hero,
            day_number,
            act_name,
            act_rule,
            *cards,
            *(packet for packet, *_ in packets),
            opacity=0,
        )
        add_at_zero(layer)

        for index, card in enumerate(cards):
            dx, dy, _, _, angle = card_specs[index]
            cx, cy = HERO[0] + dx, HERO[1] + dy
            card_start = start + 0.04 + index * 0.045
            track(scene, card, "opacity", (0, 1), card_start, card_start + 0.16, ease_out)
            track(scene, card, "position", ((cx, cy + 16), (cx, cy)), card_start, card_start + 0.3, ease_out)
            track(scene, card, "rotation", (angle - 4, angle), card_start, card_start + 0.3, ease_out)
        for index, path in enumerate(connectors):
            track(scene, path, "draw", (0, 1), start + 0.02 + index * 0.035, start + 0.36 + index * 0.035, ease_out)
        for packet, begin, c1, c2, finish, index, _, _, _ in packets:
            packet_start = start + 0.05 + index * 0.035
            track(
                scene,
                packet,
                "position",
                tuple(cubic_at(begin, c1, c2, finish, step / 22) for step in range(23)),
                packet_start + 0.01,
                packet_start + 0.59,
                linear,
            )
            track(scene, packet, "opacity", (0, 1, 1, 0), packet_start, packet_start + 0.63)

        track(scene, layer, "opacity", (0, 1) if intro else (0.86, 1), start, start + (0.46 if intro else 0.09), ease_out)
        track(scene, ripple, "scale", (0.45, 2.7), start, start + 0.6)
        track(scene, ripple, "opacity", (0.7, 0), start, start + 0.6)
        track(scene, hero, "scale", (0.96, 1.025), start, start + (0.62 if intro else 0.46), ease_out)
        track(scene, motif, "rotation", (-5, 3.5), start, end, linear)
        track(
            scene,
            orbit_dot,
            "position",
            tuple(polar(448, -145 + index * 9) for index in range(19)),
            start,
            start + 0.8,
            linear,
        )
        for index, path in enumerate(backdrop_arcs):
            track(scene, path, "draw", (0, 1), start + index * 0.04, start + 0.44 + index * 0.04, ease_out)
        track(scene, hero_arc, "draw", (0, 1), start + 0.02, start + 0.42, ease_out)
        track(scene, hero_arc_two, "draw", (0, 1), start + 0.08, start + 0.54, ease_out)
        for index, path in enumerate(draws[:4]):
            track(scene, path, "draw", (0, 1), start + 0.03 + index * 0.03, start + 0.58 + index * 0.03, ease_out)
        track(
            scene,
            day_number,
            "position",
            ((92, 214), (92, 202)),
            start,
            start + (0.34 if intro else 0.2),
            ease_out,
        )
        track(scene, act_rule, "scale_x", (0.01, 1), start + 0.04, start + 0.36, ease_out)

        if day < 30:
            track(scene, layer, "opacity", (1, 0), end - 0.001, end)

    # Persistent editorial frame.
    brand_mark = Rectangle(width=17, height=17, corner_radius=5, fill=INK, stroke=None, position=(85, 74), opacity=0)
    brand_slash = line(((80, 82), (90, 66)), CARD, 1.8)
    brand_slash.opacity = 0
    wordmark = Text(
        "CLAUDE FOR A MONTH",
        font=CLEAN_FLOW_FONT,
        font_size=20,
        font_weight=600,
        color=INK,
        text_engine="skia",
        position=(112, 58),
        anchor="top_left",
        opacity=0,
    )
    tagline = right_text("30 DAYS / 30 BUILDS", 1810, 84, size=10, color=MUTED, weight=600)
    tagline.opacity = 0
    day_word = Text(
        "DAY",
        font=CLEAN_FLOW_FONT,
        font_size=12,
        font_weight=700,
        color=MUTED,
        text_engine="skia",
        position=(98, 166),
        anchor="top_left",
        opacity=0,
    )
    header_rule = Rectangle(width=1728, height=1, fill=INK + "1B", stroke=None, position=(960, 118), opacity=0)
    spine = Rectangle(width=1, height=808, fill=INK + "14", stroke=None, position=(650, 536), opacity=0)

    phase_labels = []
    for index, (name, color, _) in enumerate(ACTS):
        label = right_text(name, (1572, 1688, 1810)[index], 54, size=12, color=color, weight=700)
        label.opacity = 1 if index == 0 else 0.3
        phase_labels.append(label)
    add_at_zero(
        brand_mark,
        brand_slash,
        wordmark,
        tagline,
        day_word,
        header_rule,
        spine,
        *phase_labels,
    )
    track(scene, brand_mark, "opacity", (0, 1), 0.2, 0.8, ease_out)
    track(scene, brand_slash, "opacity", (0, 0.9), 0.35, 0.85, ease_out)
    track(scene, wordmark, "opacity", (0, 1), 0.22, 0.9, ease_out)
    track(scene, tagline, "opacity", (0, 0.7), 0.5, 1.15, ease_out)
    track(scene, day_word, "opacity", (0, 1), 0.3, 0.95, ease_out)
    track(scene, header_rule, "scale_x", (0.001, 1), 0.4, 1.25, ease_out)
    track(scene, header_rule, "opacity", (0, 0.8), 0.4, 1.25)
    track(scene, spine, "opacity", (0, 1), 0.55, 1.3, ease_out)
    for index, label in enumerate(phase_labels):
        if index:
            track(scene, label, "opacity", (0.3, 1), index * 10, index * 10 + 0.001)
        if index < 2:
            track(scene, label, "opacity", (1, 0.3), (index + 1) * 10 - 0.001, (index + 1) * 10)

    # Registration marks keep the full-frame composition feeling designed.
    marks = []
    for x, y, sx, sy in ((56, 44, 1, 1), (1864, 44, -1, 1), (56, 1038, 1, -1), (1864, 1038, -1, -1)):
        marks.append(line(((x, y), (x + 22 * sx, y)), INK + "30", 1))
        marks.append(line(((x, y), (x, y + 22 * sy)), INK + "30", 1))
    add_at_zero(*marks)

    # A full-width thirty-day ruler doubles as the timeline and act key.
    ruler_y, ruler_x0, ruler_x1 = 976.0, 96.0, 1824.0
    xs = [ruler_x0 + (ruler_x1 - ruler_x0) * index / 29 for index in range(30)]
    ruler_parts = [
        Rectangle(width=ruler_x1 - ruler_x0, height=1, fill=INK + "20", stroke=None, position=(960, ruler_y))
    ]
    for index, x in enumerate(xs):
        day = index + 1
        color = ACTS[0][1] if day <= 10 else ACTS[1][1] if day <= 20 else ACTS[2][1]
        tick_height = 19 if day % 5 == 0 else 10
        ruler_parts.append(
            Rectangle(
                width=1.6,
                height=tick_height,
                corner_radius=0.8,
                position=(x, ruler_y - tick_height / 2),
                fill=color + "74",
                stroke=None,
            )
        )
    for day in (1, 10, 20, 30):
        ruler_parts.append(
            Text(
                f"{day:02d}",
                font=CLEAN_FLOW_FONT,
                font_size=10,
                font_weight=600,
                color=MUTED,
                text_engine="skia",
                position=(xs[day - 1], 1003),
            )
        )

    progress_lines = []
    for index in range(3):
        first, last = index * 10, min(29, index * 10 + 9)
        progress = line(((xs[first], ruler_y), (xs[last], ruler_y)), ACTS[index][1] + "B8", 2.4)
        progress.opacity = 0
        progress_lines.append(progress)
        ruler_parts.append(progress)

    marker = Group(
        line(((0, -15), (0, 15)), INK + "88", 1.4),
        Circle(8, fill=CARD, stroke=INK + "88", stroke_width=1.2),
        Circle(3.2, fill=INK, stroke=None),
        position=(xs[0], ruler_y),
    )
    ruler = Group(*ruler_parts, marker, opacity=0)
    add_at_zero(ruler)
    track(scene, ruler, "opacity", (0, 1), 0.55, 1.2, ease_out)
    track(scene, marker, "position", tuple((x, ruler_y) for x in xs), 0, 29, linear)
    for index, progress in enumerate(progress_lines):
        track(scene, progress, "opacity", (0, 1), index * 10, index * 10 + 0.02)
        track(scene, progress, "draw", (0, 1), index * 10, (index + 1) * 10, linear)

    closing = Group(
        Text(
            "30 DAYS. 30 BUILDS.",
            font=CLEAN_FLOW_FONT,
            font_size=15,
            font_weight=600,
            color=INK,
            text_engine="skia",
            position=(112, 824),
            anchor="top_left",
        ),
        Rectangle(width=72, height=2, corner_radius=1, position=(148, 854), fill=ACTS[2][1], stroke=None),
        opacity=0,
    )
    add_at_zero(closing)
    track(scene, closing, "opacity", (0, 1), 28.4, 29.15, ease_out)

    for offset in (29.0, 29.36):
        ring = Circle(82, fill=None, stroke=ACTS[2][1] + "99", stroke_width=1.6, position=HERO, opacity=0)
        add_at_zero(ring)
        track(scene, ring, "scale", (0.45, 4.6), offset, offset + 0.62, ease_out)
        track(scene, ring, "opacity", (0.65, 0), offset, offset + 0.62)

    scene.wait_until(DURATION)
    return scene


def build_scene() -> Scene:
    scene = Scene(Canvas(int(CANVAS[0]), int(CANVAS[1]), BG))

    def add_at_zero(*components):
        with scene.at(0):
            scene.add(*components)

    glows = (
        Circle(
            780,
            position=(200, 900),
            fill=RadialGradient((GradientStop(0, "#D3BFA64A"), GradientStop(1, BG + "00"))),
            stroke=None,
        ),
        Circle(
            680,
            position=(520, 120),
            fill=RadialGradient((GradientStop(0, "#B8C5CE44"), GradientStop(1, BG + "00"))),
            stroke=None,
        ),
        Circle(
            900,
            position=(1700, 800),
            fill=RadialGradient((GradientStop(0, "#D7C2A335"), GradientStop(1, BG + "00"))),
            stroke=None,
        ),
    )
    add_at_zero(*glows)
    track(scene, glows[0], "position", ((200, 900), (290, 820), (200, 900)), 0, DURATION)
    track(scene, glows[1], "position", ((520, 120), (450, 205), (520, 120)), 0, DURATION)
    track(scene, glows[2], "position", ((1700, 800), (1620, 865), (1700, 800)), 0, DURATION)

    dots = [((x, y), (x, y + 1)) for x in range(72, 1880, 42) for y in range(112, 952, 42)]
    add_at_zero(field(dots, INK + "08", 1.2))

    specks = []
    for index in range(92):
        x = 48 + (index * 271) % 1824
        y = 58 + (index * 167) % 968
        specks.append(
            Circle(
                0.7 + (index % 4) * 0.35,
                position=(x, y),
                fill=INK,
                stroke=None,
                opacity=0.07 + (index % 5) * 0.012,
            )
        )
    add_at_zero(*specks)

    light_leak = Circle(
        720,
        position=(-70, -80),
        fill=RadialGradient((GradientStop(0, "#D88B5826"), GradientStop(0.55, "#D88B580B"), GradientStop(1, "#D88B5800"))),
        stroke=None,
    )
    add_at_zero(light_leak)
    track(scene, light_leak, "position", ((-70, -80), (30, -10), (-70, -80)), 0, DURATION)

    shot_cold_open(scene)
    shot_explore(scene)
    shot_build(scene)
    shot_ship(scene)
    shot_month(scene)
    shot_finale(scene)

    # Solar flashes turn the chapter cuts into part of the motion language.
    for index, (moment, color, secondary) in enumerate(
        (
            (7.85, ACTS[0][1], ACTS[0][2]),
            (21.85, ACTS[1][1], ACTS[1][2]),
            (35.85, ACTS[2][1], ACTS[2][2]),
            (49.85, ACTS[2][1], ACTS[1][2]),
            (56.72, ACTS[2][1], ACTS[2][2]),
        )
    ):
        veil = Rectangle(width=1920, height=1080, fill=CARD, stroke=None, position=(960, 540), opacity=0)
        bloom = Group(*bloom_cloud((960, 540), 300, color, secondary), scale=0.4, opacity=0)
        rays = Group(*sun_rays((960, 540), 180, 560, color, 18, index * 13 + 5, 1.2), scale=0.4, opacity=0)
        ring_a = Circle(150, fill=None, stroke=color + "AA", stroke_width=1.6, position=(960, 540), opacity=0)
        ring_b = Circle(260, fill=None, stroke=secondary + "80", stroke_width=1.1, position=(960, 540), opacity=0)
        add_at_zero(veil, bloom, rays, ring_a, ring_b)
        track(scene, veil, "opacity", (0, 0.78, 0.78, 0), moment - 0.2, moment + 0.8)
        track(scene, bloom, "opacity", (0, 0.95, 0.95, 0), moment - 0.28, moment + 0.88)
        track(scene, bloom, "scale", (0.4, 2.1), moment - 0.28, moment + 0.9, ease_out)
        track(scene, rays, "opacity", (0, 0.7, 0.7, 0), moment - 0.24, moment + 0.85)
        track(scene, rays, "scale", (0.4, 1.7), moment - 0.24, moment + 0.9, ease_out)
        track(scene, rays, "rotation", (0, 19), moment - 0.24, moment + 0.9, linear)
        track(scene, ring_a, "scale", (0.3, 3.6), moment - 0.1, moment + 0.65, ease_out)
        track(scene, ring_a, "opacity", (0, 0.8, 0), moment - 0.1, moment + 0.7)
        track(scene, ring_b, "scale", (0.3, 2.8), moment + 0.02, moment + 0.78, ease_out)
        track(scene, ring_b, "opacity", (0, 0.55, 0), moment + 0.02, moment + 0.8)

    vignette = Circle(
        1480,
        position=(960, 540),
        fill=RadialGradient(
            (
                GradientStop(0, BG + "00"),
                GradientStop(0.62, BG + "00"),
                GradientStop(0.86, INK + "0A"),
                GradientStop(1, INK + "1C"),
            )
        ),
        stroke=None,
    )
    add_at_zero(vignette)

    grain = []
    for index in range(110):
        x = 18 + (index * 223) % 1884
        y = 18 + (index * 149) % 1044
        grain.append(Circle(0.55 + (index % 3) * 0.25, position=(x, y), fill=INK, stroke=None, opacity=0.05))
    add_at_zero(*grain)

    brand_mark = Rectangle(width=15, height=15, corner_radius=4.5, fill=INK, stroke=None, position=(85, 64), opacity=0)
    brand_slash = line(((80, 71), (90, 57)), CARD, 1.6)
    brand_slash.opacity = 0
    wordmark = Text(
        "CLAUDE FOR A MONTH",
        font=CLEAN_FLOW_FONT,
        font_size=17,
        font_weight=600,
        color=INK,
        text_engine="skia",
        position=(110, 49),
        anchor="top_left",
        opacity=0,
    )
    tagline = right_text("30 DAYS / 30 BUILDS", 1810, 63, size=10, color=MUTED, weight=600)
    tagline.opacity = 0
    header_rule = Rectangle(width=1728, height=1, fill=INK + "16", stroke=None, position=(960, 100), opacity=0)
    add_at_zero(brand_mark, brand_slash, wordmark, tagline, header_rule)
    track(scene, brand_mark, "opacity", (0, 1), 0.2, 0.9, ease_out)
    track(scene, brand_slash, "opacity", (0, 0.9), 0.35, 1.0, ease_out)
    track(scene, wordmark, "opacity", (0, 1), 0.3, 1.0, ease_out)
    track(scene, tagline, "opacity", (0, 0.75), 0.55, 1.25, ease_out)
    track(scene, header_rule, "scale_x", (0.001, 1), 0.45, 1.4, ease_out)
    track(scene, header_rule, "opacity", (0, 0.85), 0.45, 1.4)
    for item, opacity in ((brand_mark, 1), (brand_slash, 0.9), (wordmark, 1), (tagline, 0.75), (header_rule, 0.85)):
        track(scene, item, "opacity", (opacity, 0), 56.8, 57.25, ease_out)

    marks = []
    for x, y, sx, sy in ((56, 42, 1, 1), (1864, 42, -1, 1), (56, 1038, 1, -1), (1864, 1038, -1, -1)):
        marks.append(line(((x, y), (x + 22 * sx, y)), INK + "30", 1))
        marks.append(line(((x, y), (x, y + 22 * sy)), INK + "30", 1))
    add_at_zero(*marks)

    scene.wait_until(DURATION)
    return scene


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="Two seconds from the build act (source 24–26 s)")
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"))
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame < DURATION:
        parser.error(f"frame must be in [0, {DURATION:g})")
    if args.range and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error(f"range must satisfy 0 <= START < END <= {DURATION:g}")
    if args.fps <= 0:
        parser.error("fps must be positive")

    scene = build_scene()
    assert scene.duration == DURATION
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    interval = args.range or ([24, 26] if args.preview else [0, DURATION])
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "claude-for-month.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.frame is not None:
        interval = [args.frame, args.frame]
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
                start_time=interval[0],
                end_time=interval[1],
                overwrite=args.overwrite,
                progress=progress,
            )
    output.with_suffix(".json").write_text(
        json.dumps(
            {
                "scene_duration": DURATION,
                "source_range": interval,
                "rendering": rendering_identity("skia", scene),
                "full_export_verified": False,
            },
            indent=2,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
