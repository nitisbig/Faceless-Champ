"""Sixty seconds of native Skia infographics on pure black. Synthetic data."""

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
    ExportProgress,
    ExportSettings,
    Group,
    Number,
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
MINT, PURPLE, AMBER, WHITE, DIM = "#6DF2C1", "#AF98FF", "#FFCC70", "#F5F5F2", "#242727"


def text(value, x, y, size=25, color=WHITE):
    return Text(value, position=(x, y), font=CLEAN_FLOW_FONT, font_size=size, color=color, text_engine="skia")


def number(value, x, y, size=100, color=WHITE, suffix="", prefix="", spec=",.0f", width=600):
    return Number(
        value,
        position=(x, y),
        font=CLEAN_FLOW_FONT,
        font_size=size,
        color=color,
        text_engine="skia",
        width=width,
        align="center",
        suffix=suffix,
        prefix=prefix,
        format_spec=spec,
    )


def line(points, color=DIM, width=2):
    return Polyline(tuple(points), stroke=color, stroke_width=width)


def arc(x, y, radius, start=-90, sweep=360, color=MINT, width=20):
    def point(a):
        return x + radius * math.cos(a), y + radius * math.sin(a)

    a = math.radians(start)
    path = PathData().move_to(*point(a))
    count = max(1, math.ceil(abs(sweep) / 45))
    for i in range(count):
        a = math.radians(start + sweep * i / count)
        b = math.radians(start + sweep * (i + 1) / count)
        k = 4 / 3 * math.tan((b - a) / 4)
        path = path.cubic_to(
            x + radius * (math.cos(a) - k * math.sin(a)),
            y + radius * (math.sin(a) + k * math.cos(a)),
            x + radius * (math.cos(b) + k * math.sin(b)),
            y + radius * (math.sin(b) - k * math.cos(b)),
            *point(b),
        )
    return VectorPath(path, stroke=color, stroke_width=width)


def track(scene, obj, prop, values, start, end, easing=smooth):
    values = tuple(values)
    frames = tuple((i / (len(values) - 1), v) for i, v in enumerate(values))
    key = (obj, prop)
    if key not in scene.first_tracks:
        scene.first_tracks.add(key)
        # Explicit starts apply only once a track begins. Hold that state from
        # the chapter entrance so delayed marks cannot flash at their defaults.
        if start > scene.chapter_start:
            delay, duration = start - scene.chapter_start, end - start
            frames = ((0, values[0]),) + tuple(
                ((delay + duration * t) / (end - scene.chapter_start), v) for t, v in frames
            )
            start = scene.chapter_start
    scene.tracks.append(
        (
            start,
            end,
            Animation(
                obj,
                {prop: values[-1]},
                starts={prop: values[0]},
                keyframes={prop: frames},
                rate_func=easing,
            ),
        )
    )


def stage(scene, parts, start, end):
    group = Group(*parts)
    with scene.at(start):
        scene.add(group)
    track(scene, group, "opacity", (0, 1), start, start + 0.65)
    track(scene, group, "opacity", (1, 0), end - 0.65, end)


def counters(scene):
    n = number(0, 700, 480, 160, width=900)
    parts = [n, text("units", 700, 616, 27, MINT)]
    track(scene, n, "value", (0, 12480), 0.8, 8.5)
    # A 120-cell accumulation field, with the same normalized clock as the counter.
    for i in range(120):
        x, y = 1270 + i % 10 * 34, 354 + i // 10 * 34
        parts.append(Circle(9, position=(x, y), fill=DIM, stroke=None))
        dot = Circle(9, position=(x, y), fill=MINT, stroke=None)
        parts.append(dot)
        # Invert smoothstep to align the dot threshold to the counter's easing.
        fraction = (i + 1) / 120
        lo, hi = 0.0, 1.0
        for _ in range(24):
            mid = (lo + hi) / 2
            if smooth(mid) < fraction:
                lo = mid
            else:
                hi = mid
        t = 0.8 + 7.7 * (lo + hi) / 2
        track(scene, dot, "opacity", (0, 1), t - 0.07, t)
    parts.append(line(((260, 755), (1650, 755))))
    fill = Rectangle(width=1390, height=5, anchor="top_left", position=(260, 753), fill=MINT, stroke=None)
    parts.append(fill)
    track(scene, fill, "width", (0.01, 1390), 0.8, 8.5)
    stage(scene, parts, 0, 12)


def radial(scene):
    parts = []
    for i, (value, color, key) in enumerate(((72, MINT, "A"), (54, PURPLE, "B"), (89, AMBER, "C"))):
        x, y = 450 + i * 510, 505
        parts.append(arc(x, y, 177, color=DIM, width=22))
        ring = arc(x, y, 177, color=color, width=22)
        n = number(0, x, y, 88, suffix="%", width=360)
        parts.extend((ring, n, text(key, x, 785, 32, color)))
        track(scene, ring, "draw", (0, value / 100), 12.9 + i * 0.3, 19.5 + i * 0.3)
        track(scene, n, "value", (0, value), 12.9 + i * 0.3, 19.5 + i * 0.3)
    stage(scene, parts, 12, 24)


def comparison(scene):
    parts = [line(((400, 785), (1520, 785))), text("A", 650, 850, 32, PURPLE), text("B", 1270, 850, 32, MINT)]
    for i, (value, color) in enumerate(((40, PURPLE), (68, MINT))):
        x = 650 + i * 620
        h = value * 6
        bar = Rectangle(width=240, height=h, position=(x, 785 - h / 2), fill=color, stroke=None, corner_radius=12)
        n = number(0, x, 745, 72, width=350)
        parts.extend((bar, n))
        track(scene, bar, "height", (0.01, h), 25 + i * 0.4, 30.2 + i * 0.4)
        track(scene, bar, "position", ((x, 785), (x, 785 - h / 2)), 25 + i * 0.4, 30.2 + i * 0.4)
        track(scene, n, "value", (0, value), 25 + i * 0.4, 30.2 + i * 0.4)
        track(scene, n, "position", ((x, 745), (x, 735 - h)), 25 + i * 0.4, 30.2 + i * 0.4)
    bracket = line(((650, 300), (650, 245), (1270, 245), (1270, 300)), AMBER, 3)
    uplift = number(0, 960, 180, 54, AMBER, suffix="%", prefix="+", width=400)
    parts.extend((bracket, uplift))
    track(scene, bracket, "draw", (0, 1), 31, 32.5)
    track(scene, uplift, "opacity", (0, 1), 31, 31.5)
    track(scene, uplift, "value", (0, 70), 31, 33)
    stage(scene, parts, 24, 36)


def percentage(scene):
    parts = []
    for i in range(100):
        x, y = 305 + i % 10 * 48, 320 + i // 10 * 48
        parts.append(Circle(13, position=(x, y), fill=DIM, stroke=None))
        if i < 76:
            dot = Circle(13, position=(x, y), fill=AMBER, stroke=None)
            parts.append(dot)
            t = 37 + (i + 1) / 76 * 6
            track(scene, dot, "opacity", (0, 1), t - 0.06, t, linear)
    parts.append(arc(1280, 535, 220, start=135, sweep=270, color=DIM, width=18))
    ring = arc(1280, 535, 220, start=135, sweep=270, color=AMBER, width=18)
    n = number(0, 1280, 535, 116, suffix="%", width=500)
    parts.extend((ring, n, text("of 100", 1280, 790, 27, AMBER)))
    track(scene, ring, "draw", (0, 0.76), 37, 43, linear)
    track(scene, n, "value", (0, 76), 37, 43, linear)
    stage(scene, parts, 36, 48)


def statistics(scene):
    # Six comparable annual observations; the endpoint and reading follow the line.
    values = (100, 112, 108, 139, 157, 184)
    points = tuple((320 + i * 256, 780 - (v - 100) * 4.6) for i, v in enumerate(values))
    parts = []
    for v in (100, 140, 180):
        y = 780 - (v - 100) * 4.6
        parts.extend((line(((320, y), (1600, y))), text(str(v), 235, y, 22, "#737B78")))
    for i, year in enumerate(range(2020, 2026)):
        parts.append(text(str(year), 320 + i * 256, 850, 23, "#737B78"))
    # Independent segments preserve the exact data clock without arc-length distortion.
    for i in range(5):
        segment = line(points[i : i + 2], MINT, 5)
        parts.append(segment)
        track(scene, segment, "draw", (0, 1), 49 + i * 1.3, 50.3 + i * 1.3, linear)
    marker = Circle(8, position=points[0], fill=WHITE, stroke=MINT, stroke_width=4)
    n = number(100, 550, 230, 104, width=420)
    gain = number(0, 1420, 230, 68, MINT, suffix="%", prefix="+", width=400)
    parts.extend((marker, n, gain))
    track(scene, marker, "position", points, 49, 55.5, linear)
    track(scene, n, "value", values, 49, 55.5, linear)
    track(scene, gain, "value", tuple(v - 100 for v in values), 49, 55.5, linear)
    stage(scene, parts, 48, 60)


def build_scene():
    scene = Scene(Canvas(1920, 1080, "#000000"))
    scene.tracks = []
    scene.first_tracks = set()
    for i, chapter in enumerate((counters, radial, comparison, percentage, statistics)):
        scene.chapter_start = i * 12
        chapter(scene)
    for start, end, animation in sorted(scene.tracks, key=lambda item: item[0]):
        with scene.at(start):
            scene.play(animation, run_time=end - start)
    del scene.tracks
    del scene.first_tracks
    del scene.chapter_start
    scene.wait_until(DURATION)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float)
    mode.add_argument("--preview", action="store_true", help="Two-second comparison excerpt")
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"))
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame < DURATION:
        parser.error("frame must be in [0, 60)")
    if args.range and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 60")
    if args.fps <= 0:
        parser.error("fps must be positive")
    scene = build_scene()
    assert scene.duration == DURATION
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    interval = args.range or ([28, 30] if args.preview else [0, DURATION])
    name = (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "skia-infographics.mp4"
    )
    output = args.output or ROOT / "output" / name
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
                "synthetic_data": True,
                "rendering": rendering_identity("skia", scene),
                "full_export_verified": False,
            },
            indent=2,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
