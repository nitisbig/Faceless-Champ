"""A silent, text-free, sixty-second native Skia UI motion study."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import ImageColor

from faceless_champ import (
    Animation,
    Canvas,
    Circle,
    ExportProgress,
    ExportSettings,
    GradientStop,
    Group,
    LinearGradient,
    PathData,
    Polyline,
    RadialGradient,
    Rectangle,
    Scene,
    ShadowStyle,
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
BG, VIOLET, CYAN, CORAL, WHITE = "#080C18", "#A59BFF", "#70E3DB", "#F9AD99", "#E6EBFF"


def gradient(a, b, angle=110):
    return LinearGradient((GradientStop(0, a), GradientStop(1, b)), angle=angle)


def rect(x, y, w, h, fill, radius=16, stroke=None, **kwargs):
    return Rectangle(
        width=w,
        height=h,
        position=(x, y),
        fill=fill,
        stroke=stroke,
        stroke_width=1,
        corner_radius=min(radius, w / 2, h / 2),
        **kwargs,
    )


def glass(x, y, w, h, tint="#272B486E", radius=30):
    return Group(
        rect(
            x, y, w, h, gradient(tint, "#151D307D"), radius, "#DCE5FF26", shadow=ShadowStyle("#00000060", 22, (0, 18))
        ),
        rect(x, y - h / 2 + 1, w - radius * 2, 1, "#E4ECFF3B", 0),
    )


def line(points, color=WHITE, width=3):
    return Polyline(tuple(points), stroke=color, stroke_width=width)


def track(scene, obj, prop, values, start, end, easing=smooth):
    values = tuple(values)
    if prop in {"fill", "stroke", "color"}:
        values = tuple(ImageColor.getcolor(value, "RGBA") if isinstance(value, str) else value for value in values)
    # Register whole hierarchies first; Scene snapshots cannot reparent children.
    scene.ui_tracks.append(
        (
            start,
            end,
            Animation(
                obj,
                {prop: values[-1]},
                starts={prop: values[0]},
                keyframes={prop: tuple((i / (len(values) - 1), v) for i, v in enumerate(values))},
                rate_func=easing,
            ),
        )
    )


def reveal(scene, obj, start, end, drift=48):
    with scene.at(start):
        scene.add(obj)
    x, y = obj.position
    track(scene, obj, "opacity", (0, 1), start, start + 0.9)
    if drift:
        track(scene, obj, "position", ((x, y + drift), (x, y)), start, start + 1.1)
    track(scene, obj, "opacity", (1, 0), end - 0.65, end)
    if drift:
        track(scene, obj, "position", ((x, y), (x, y - drift)), end - 0.65, end)


def arc(x, y, r, fraction=1, color=CYAN, width=12):
    points = [
        (
            x + r * math.cos(-math.pi / 2 + i / 100 * math.tau * fraction),
            y + r * math.sin(-math.pi / 2 + i / 100 * math.tau * fraction),
        )
        for i in range(101)
    ]
    return line(points, color, width)


def icon(x, y, kind="grid", color=VIOLET, size=20):
    if kind == "grid":
        return Group(
            *(
                rect(x + dx * size * 0.58, y + dy * size * 0.58, size * 0.65, size * 0.65, color, 4)
                for dx in (-1, 1)
                for dy in (-1, 1)
            )
        )
    if kind == "chip":
        bits = [rect(x, y, size * 1.35, size * 1.35, None, 6, color), rect(x, y, size * 0.55, size * 0.55, color, 3)]
        for d in (-1, 1):
            for p in (-0.35, 0.35):
                bits.extend(
                    (
                        line(((x + d * size * 0.7, y + p * size), (x + d * size, y + p * size)), color, 2),
                        line(((x + p * size, y + d * size * 0.7), (x + p * size, y + d * size)), color, 2),
                    )
                )
        return Group(*bits)
    if kind == "play":
        return line(
            (
                (x - size * 0.3, y - size * 0.5),
                (x + size * 0.5, y),
                (x - size * 0.3, y + size * 0.5),
                (x - size * 0.3, y - size * 0.5),
            ),
            color,
            3,
        )
    return line(((x - size * 0.5, y), (x - size * 0.1, y + size * 0.4), (x + size * 0.6, y - size * 0.4)), color, 4)


def dashboard(scene, start, end, compact=False):
    """Persistent app shell, independently animated native chart and widgets."""
    parts = [glass(960, 540, 1560, 820, "#30314B8A", 36)]
    # Window chrome and icon-only navigation.
    for i, color in enumerate((CORAL, "#EDD99A", CYAN)):
        parts.append(Circle(5, position=(221 + 20 * i, 166), fill=color, stroke=None))
    parts.extend((rect(960, 166, 250, 7, "#E9ECFF18", 3), line(((280, 210), (280, 907)), "#DCE5FF12", 1)))
    for i, kind in enumerate(("grid", "chip", "play", "check")):
        y = 269 + i * 100
        if i == 0:
            parts.append(rect(231, y, 62, 62, "#A59BFF25", 18))
        parts.append(icon(231, y, kind, VIOLET if i == 0 else "#8B96AE", 16))
    parts.extend(
        (
            Circle(17, position=(231, 868), fill=gradient(VIOLET, CYAN), stroke=None),
            rect(487, 258, 302, 38, "#B4A5FF18", 19),
            icon(364, 258, "chip", VIOLET, 12),
            rect(491, 258, 190, 5, "#C9C6F84A", 2),
        )
    )
    # Three compact graphical summary cards.
    for j, color in enumerate((VIOLET, CYAN, CORAL)):
        x = 552 + j * 448
        parts.append(glass(x, 370, 418, 136))
        parts.append(icon(x - 162, 350, ("grid", "chip", "check")[j], color, 14))
        for k, w in enumerate((68, 36, 52)):
            parts.append(rect(x - 115 + k * 54, 393, w * 0.65, 12, color + ("BF" if k == 0 else "55"), 5))
        spark = line([(x + 32 + n * 12, 394 - 10 * math.sin(n * 0.7 + j) - n * 4) for n in range(10)], color, 3)
        parts.append(spark)
        track(scene, spark, "draw", (0, 1), start + 1.1 + j * 0.18, start + 3)
    # Large native Bézier chart. No axis labels or decorative pseudo-text.
    parts.append(glass(797, 680, 906, 418))
    for y in (555, 630, 705, 780, 842):
        parts.append(line(((385, y), (1207, y)), "#C3D2F010", 1))
    for x in (385, 590, 796, 1001, 1207):
        parts.append(line(((x, 535), (x, 842)), "#C3D2F009", 1))
    path = (
        PathData()
        .move_to(385, 794)
        .cubic_to(470, 796, 473, 660, 566, 703)
        .cubic_to(656, 747, 683, 596, 774, 638)
        .cubic_to(865, 679, 901, 556, 985, 584)
        .cubic_to(1070, 611, 1126, 548, 1207, 539)
    )
    fill = VectorPath(
        path.line_to(1207, 842).line_to(385, 842).close(), fill=gradient("#A59BFF01", "#A59BFF45", 270), stroke=None
    )
    curve = VectorPath(path, stroke=VIOLET, stroke_width=4)
    secondary = line([(385 + n * 13.7, 790 - n * 2.2 + 18 * math.sin(n * 0.19)) for n in range(61)], "#70E3DB88", 2)
    parts.extend((fill, secondary, curve))
    track(scene, fill, "opacity", (0, 1), start + 1.4, start + 3.8)
    track(scene, curve, "draw", (0, 1), start + 1.2, start + 4)
    track(scene, secondary, "draw", (0, 1), start + 1.6, start + 4.3)

    # Hover marker slides on the actual cubic chart, using exact cubic samples.
    def bezier(t):
        q = 1 - t
        return (
            q**3 * 774 + 3 * q * q * t * 865 + 3 * q * t * t * 901 + t**3 * 985,
            q**3 * 638 + 3 * q * q * t * 679 + 3 * q * t * t * 556 + t**3 * 584,
        )

    marker = Group(
        Circle(17, fill="#A59BFF24", stroke=None, position=bezier(0)),
        Circle(6, fill=WHITE, stroke=VIOLET, stroke_width=3, position=bezier(0)),
    )
    parts.append(marker)
    samples = [bezier(0.5 - 0.5 * math.cos(i / 48 * math.tau * 2)) for i in range(49)]
    track(scene, marker, "position", samples, start + 4, end - 1, linear)
    # Ring card and small live histogram.
    parts.append(glass(1482, 680, 418, 418))
    parts.append(arc(1482, 610, 77, color="#D6DDFC10", width=13))
    ring = arc(1482, 610, 77, 0.78, VIOLET, 13)
    parts.extend((ring, icon(1482, 610, "check", CYAN, 28)))
    track(scene, ring, "draw", (0, 0.78, 1, 0.9, 1), start + 1.2, end - 1)
    for i in range(16):
        h = 24 + 63 * (0.5 + 0.5 * math.sin(i * 0.7))
        bar = rect(1334 + i * 20, 850 - h / 2, 9, h, CYAN if i % 4 else VIOLET, 4)
        # Animate height and center together to hold the histogram baseline.
        heights = [h * a for a in (0.3, 1, 0.55, 0.85, 0.4, 1)]
        track(scene, bar, "height", heights, start + 1.3, end - 1)
        track(scene, bar, "position", [(1334 + i * 20, 850 - v / 2) for v in heights], start + 1.3, end - 1)
        parts.append(bar)
    app = Group(*parts)
    reveal(scene, app, start, end, 42)
    if compact:
        track(scene, app, "scale", (0.94, 1), start, start + 1.5)


def controls(scene, start=19.4, end=38.5):
    # Three staggered floating panels; every control communicates through geometry.
    left = [glass(535, 540, 510, 640), icon(535, 315, "chip", VIOLET, 34)]
    for i, color in enumerate((VIOLET, CYAN, CORAL)):
        y = 470 + 104 * i
        left.extend((rect(535, y, 358, 6, "#DBE4FF15", 3), Circle(5, position=(358, y), fill=color, stroke=None)))
        knob = Group(
            Circle(21, position=(440, y), fill="#121B32", stroke=color, stroke_width=2),
            Circle(8, position=(440, y), fill=color, stroke=None),
        )
        active = rect(400, y, 84, 6, color, 3)
        left.extend((active, knob))
        positions = [440, 650 - i * 55, 510 + i * 40, 600 - i * 28]
        track(scene, knob, "position", [(v, y) for v in positions], start + 2 + i * 0.25, end - 2)
        track(scene, active, "width", [v - 358 for v in positions], start + 2 + i * 0.25, end - 2)
        track(scene, active, "position", [((v + 358) / 2, y) for v in positions], start + 2 + i * 0.25, end - 2)
    left.extend(
        (
            rect(535, 771, 358, 1, "#DBE4FF12", 0),
            Circle(6, position=(370, 805), fill=CYAN, stroke=None),
            Circle(6, position=(401, 805), fill=VIOLET, stroke=None),
            Circle(6, position=(432, 805), fill=CORAL, stroke=None),
        )
    )
    reveal(scene, Group(*left), start, end)

    middle = [glass(1028, 408, 416, 376), arc(1028, 400, 103, color="#D6DDFC12", width=15)]
    progress = arc(1028, 400, 103, 0.96, CYAN, 15)
    middle.extend((progress, icon(1028, 400, "check", WHITE, 34)))
    track(scene, progress, "draw", (0, 0.25, 0.65, 0.96, 1), start + 1, start + 13)
    for i in range(5):
        dot = Circle(4, position=(980 + i * 24, 554), fill=CYAN, stroke=None)
        middle.append(dot)
        track(scene, dot, "opacity", [0.2 + 0.8 * ((j + i) % 5 == 0) for j in range(26)], start + 1, end - 1, linear)
    reveal(scene, Group(*middle), start + 0.2, end)
    # A pressable icon button with a geometric cursor and expanding click ring.
    button = Group(
        rect(
            1028,
            733,
            416,
            254,
            gradient("#9182EF", "#5652A2"),
            30,
            "#D7CCFF80",
            shadow=ShadowStyle("#6051CF40", 24, (0, 15)),
        ),
        icon(1028, 733, "play", WHITE, 38),
    )
    reveal(scene, button, start + 0.4, end)
    track(scene, button, "scale", (1, 1, 0.95, 1, 1, 0.95, 1), start + 5, start + 13)
    for t in (start + 7.5, start + 12.2):
        ripple = Circle(30, position=(1080, 762), fill=None, stroke="#EAE5FF99", stroke_width=2)
        with scene.at(t):
            scene.add(ripple)
        track(scene, ripple, "scale", (0.5, 3), t, t + 0.9)
        track(scene, ripple, "opacity", (0.8, 0), t, t + 0.9)
    cursor = line(((1092, 784), (1090, 746), (1119, 769), (1103, 771), (1098, 786)), WHITE, 3)
    reveal(scene, cursor, start + 3, end - 1, 0)
    track(scene, cursor, "position", ((1190, 850), cursor.position, cursor.position), start + 3, start + 7)

    right = [glass(1493, 540, 456, 640)]
    for i, color in enumerate((CYAN, VIOLET, CORAL)):
        y = 345 + i * 190
        right.append(icon(1354, y, ("chip", "grid", "check")[i], color, 20))
        pill = rect(1578, y, 114, 60, "#48526A", 30)
        knob = Circle(23, position=(1551, y), fill=WHITE, stroke=None)
        right.extend((pill, knob))
        states = (1551, 1605, 1605, 1551, 1605)
        track(scene, knob, "position", [(v, y) for v in states], start + 2 + i, end - 2)
        track(scene, pill, "fill", ("#48526A", color, color, "#48526A", color), start + 2 + i, end - 2)
        for k in range(8):
            seg = rect(1354 + k * 36, y + 72, 24, 5, color, 2)
            right.append(seg)
            track(scene, seg, "opacity", (0.15, 1, 0.45, 1), start + 1 + k * 0.13, end - 1)
    reveal(scene, Group(*right), start + 0.3, end)


def network(scene, start=37.8, end=52.8):
    nodes = ((450, 360), (450, 720), (960, 540), (1470, 360), (1470, 720))
    parts = []
    for i, (a, b) in enumerate(((0, 2), (1, 2), (2, 3), (2, 4))):
        x0, y0 = nodes[a]
        x1, y1 = nodes[b]
        path = PathData().move_to(x0 + 102, y0).cubic_to(x0 + 260, y0, x1 - 260, y1, x1 - 102, y1)
        wire = VectorPath(path, stroke="#9DA8DD46", stroke_width=3)
        parts.append(wire)
        track(scene, wire, "draw", (0, 1), start + 0.3 + i * 0.15, start + 2)
        for j in range(3):
            packet = Circle(
                5,
                position=(x0 + 102, y0),
                fill=CYAN if i % 2 else VIOLET,
                stroke=None,
                shadow=ShadowStyle("#8DADFF99", 9, (0, 0)),
            )
            parts.append(packet)
            clock, finish = start + 2, end - 1
            period, phase = (finish - clock) / 4, j / 3
            while clock < finish - 1e-8:
                duration = min(period * (1 - phase), finish - clock)
                samples = []
                for k in range(31):
                    t = phase + k / 30 * duration / period
                    q = 1 - t
                    samples.append(
                        (
                            q**3 * (x0 + 102)
                            + 3 * q * q * t * (x0 + 260)
                            + 3 * q * t * t * (x1 - 260)
                            + t**3 * (x1 - 102),
                            q**3 * y0 + 3 * q * q * t * y0 + 3 * q * t * t * y1 + t**3 * y1,
                        )
                    )
                track(scene, packet, "position", samples, clock, clock + duration, linear)
                clock, phase = clock + duration, 0
    for i, (x, y) in enumerate(nodes):
        color = (VIOLET, CYAN, WHITE, CORAL, VIOLET)[i]
        node = Group(
            glass(x, y, 204 if i != 2 else 250, 190 if i != 2 else 250),
            icon(x, y, "chip" if i == 2 else "grid", color, 39 if i == 2 else 26),
        )
        parts.append(node)
        track(scene, node, "scale", (1, 1.04, 1, 1.04, 1), start + 2 + i * 0.15, end - 1)
        if i != 2:
            parts.append(rect(x, y + 62, 72, 4, color + "66", 2))
    # Native expanding concentric fields around the processor.
    for i in range(3):
        halo = Circle(150 + i * 28, position=(960, 540), fill=None, stroke="#A59BFF20", stroke_width=1)
        parts.insert(0, halo)
        track(scene, halo, "scale", (1, 1.12, 1), start + 1 + i * 0.2, end - 1)
    reveal(scene, Group(*parts), start, end, 32)


def build_scene():
    scene = Scene(Canvas(1920, 1080, BG))
    scene.ui_tracks = []
    # Large soft vector gradients create light behind the translucent panels.
    for x, y, r, color, dx in (
        (420, 260, 680, "#7464DF4D", 170),
        (1530, 760, 680, "#31B5BC30", -150),
        (1250, 230, 480, "#B96E9D1F", -100),
    ):
        glow = Circle(
            r, position=(x, y), fill=RadialGradient((GradientStop(0, color), GradientStop(1, BG + "00"))), stroke=None
        )
        with scene.at(0):
            scene.add(glow)
        track(scene, glow, "position", ((x, y), (x + dx, y + 100), (x, y)), 0, DURATION)
    # Very quiet dot field, with ample empty space at the canvas edges.
    dots = tuple(
        cmd for x in range(160, 1800, 40) for y in range(140, 980, 40) for cmd in (("M", x, y), ("L", x + 0.6, y))
    )
    with scene.at(0):
        scene.add(VectorPath(PathData(dots), stroke="#C9D6FF12", stroke_width=1.5))
    dashboard(scene, 0.1, 20.2)
    controls(scene)
    network(scene)
    dashboard(scene, 52, 60, compact=True)
    for start, end, animation in sorted(scene.ui_tracks, key=lambda item: item[0]):
        with scene.at(start):
            scene.play(animation, run_time=end - start)
    del scene.ui_tracks
    scene.wait_until(DURATION)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="Two-second dashboard sample")
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
    interval = args.range or ([7, 9] if args.preview else [0, DURATION])
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "skia-premium-ui.mp4"
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
