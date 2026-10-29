"""One minute of neural geometry, rendered with native Python and Skia."""

from __future__ import annotations

import argparse
import json
import math
import random
from itertools import pairwise
from pathlib import Path

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Animation,
    Canvas,
    Circle,
    ExportProgress,
    ExportSettings,
    GradientStop,
    Group,
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
DURATION = 60.0
BG, CYAN, VIOLET, CORAL, WHITE = "#080D19", "#66E7DA", "#AB9AFF", "#FF9B87", "#E5ECF8"
DIM = "#34435D"


class NeuralScene(Scene):
    """Collect tracks until all components belong to their chapter groups."""

    def __init__(self):
        super().__init__(Canvas(1920, 1080, BG))
        self.pending_tracks = []


def text(value, position, size=24, color=WHITE):
    return Text(value, position=position, font=CLEAN_FLOW_FONT, font_size=size, color=color, text_engine="skia")


def line(a, b, color=DIM, width=2):
    return Polyline((a, b), stroke=color, stroke_width=width)


def track(scene, obj, prop, values, start, end, easing=smooth):
    values = tuple(values)
    scene.pending_tracks.append(
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


def show(scene, objects, start, end):
    group = Group(*objects)
    with scene.at(start):
        scene.add(group)
    track(scene, group, "opacity", (0, 1), start, start + 0.65)
    track(scene, group, "opacity", (1, 0), end - 0.55, end)
    return group


def dot(position, radius=6, color=CYAN):
    return Circle(radius, position=position, fill=color, stroke=None)


def packet(scene, objects, a, b, start, end, color=CYAN):
    # Three spatially separated particles make a directional comet without blur.
    for i, radius in enumerate((7, 4, 2)):
        p = dot(a, radius, color)
        p.opacity = 0
        objects.append(p)
        delay = i * 0.055
        track(scene, p, "position", (a, b), start + delay, end + delay, linear)
        track(scene, p, "opacity", (0, 1, 1, 0), start + delay, end + delay, linear)


def arrow(a, b, color=CORAL, width=3):
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    wing = [(b[0] - 16 * math.cos(angle + s * 0.45), b[1] - 16 * math.sin(angle + s * 0.45)) for s in (-1, 1)]
    return Group(line(a, b, color, width), Polyline((wing[0], b, wing[1]), stroke=color, stroke_width=width))


def network(scene, start, end, backward=False, finale=False):
    objects = []
    counts = (4, 6, 6, 3)
    positions = [
        [(330 + layer * 420, 540 + (i - (n - 1) / 2) * 103) for i in range(n)] for layer, n in enumerate(counts)
    ]
    color = CORAL if backward else CYAN
    rng = random.Random(19)
    weights = [[[rng.uniform(-1, 1) for _ in left] for _ in right] for left, right in pairwise(positions)]
    activations = [[0.25, 0.85, 0.65, 0.4]]
    for matrix in weights:
        activations.append([1 / (1 + math.exp(-sum(w * x for w, x in zip(row, activations[-1])))) for row in matrix])
    # Edges stay quiet; only selected signal paths receive bright moving packets.
    for layer, (left, right) in enumerate(pairwise(positions)):
        for i, a in enumerate(left):
            for j, b in enumerate(right):
                w = weights[layer][j][i]
                objects.append(line(a, b, "#8579C538" if w < 0 else "#66E7DA30", 0.7 + abs(w) * 1.5))
    cycles = (start + 1.1, start + 4.8, start + 8.5) if not finale else (start + 0.9, start + 4.5)
    for cycle in cycles:
        for step in range(3):
            layer = 2 - step if backward else step
            left, right = positions[layer : layer + 2]
            for i, a in enumerate(left):
                j = (i * 2 + step) % len(right)
                b = right[j]
                if backward:
                    a, b = b, a
                packet(scene, objects, a, b, cycle + step * 0.95, cycle + step * 0.95 + 0.85, color)
                if backward:
                    head = arrow((b[0] + (a[0] - b[0]) * 0.45, b[1] + (a[1] - b[1]) * 0.45), b)
                    head.opacity = 0
                    objects.append(head)
                    track(scene, head, "opacity", (0, 0.9, 0), cycle + step * 0.95, cycle + step * 0.95 + 1.2)
    for layer, points in enumerate(positions):
        for i, p in enumerate(points):
            value = activations[layer][i]
            objects.append(Circle(28, position=p, fill=BG, stroke=DIM, stroke_width=2))
            core = dot(p, 10 + value * 10, color if backward else (CYAN if layer != 2 else VIOLET))
            objects.append(core)
            for cycle in cycles:
                hit = cycle + ((3 - layer) if backward else layer) * 0.95
                track(scene, core, "scale", (1, 1.35, 1), hit, hit + 0.9)
                track(scene, core, "opacity", (0.3, 1, 0.65), hit, hit + 0.9)
                ring = Circle(29, position=p, fill=None, stroke=color, stroke_width=2, opacity=0)
                objects.append(ring)
                track(scene, ring, "scale", (1, 1.85), hit, hit + 0.9)
                track(scene, ring, "opacity", (0, 0.7, 0), hit, hit + 0.9)
    objects.extend(
        (text("x", (330, 900), 28, CYAN), text("h", (960, 900), 28, VIOLET), text("y", (1590, 900), 28, CYAN))
    )
    if backward:
        objects.extend((text("-dL/dw", (960, 190), 32, CORAL), line((625, 830), (1280, 830), DIM, 1)))
        loss = Number(
            0.82,
            position=(1460, 865),
            font=CLEAN_FLOW_FONT,
            font_size=29,
            text_engine="skia",
            color=CORAL,
            format_spec=".2f",
            width=110,
        )
        objects.extend((text("L", (1365, 865), 27, CORAL), loss))
        track(scene, loss, "value", (0.82, 0.59, 0.37, 0.18), start + 1, end - 1)
    show(scene, objects, start, end)


def embeddings(scene, start=13, end=26):
    rng = random.Random(42)
    objects = [
        arrow((370, 835), (1550, 835), DIM, 2),
        arrow((370, 835), (370, 210), DIM, 2),
        text("z1", (1580, 835), 22),
        text("z2", (370, 175), 22),
    ]
    centers = ((680, 380), (1250, 420), (930, 700))
    colors = (CYAN, VIOLET, CORAL)
    names = (("cat", "dog"), ("car", "train"), ("apple", "pear"))
    for cluster, (cx, cy) in enumerate(centers):
        for i in range(22):
            a, r = rng.uniform(0, math.tau), rng.uniform(20, 125)
            target = (cx + math.cos(a) * r, cy + math.sin(a) * r * 0.65)
            initial = (rng.uniform(510, 1450), rng.uniform(280, 770))
            p = dot(initial, 5 if i > 1 else 9, colors[cluster])
            objects.append(p)
            track(scene, p, "position", (initial, target), start + 0.8 + i * 0.025, start + 5 + i * 0.025)
            if i < 2:
                # Fixed anchor dots make the semantic nearest-neighbor relation legible.
                anchor = (cx - 42 + i * 84, cy)
                track(scene, p, "position", (target, anchor), start + 6, start + 7)
                label = text(names[cluster][i], (anchor[0], anchor[1] - 33), 23, colors[cluster])
                label.opacity = 0
                objects.append(label)
                track(scene, label, "opacity", (0, 1), start + 6.5, start + 7.5)
        ring = Circle(
            152, position=(cx, cy), scale_y=0.72, fill=None, stroke=colors[cluster], stroke_width=1, opacity=0
        )
        objects.append(ring)
        track(scene, ring, "opacity", (0, 0.35), start + 5.5, start + 7)
    connector = line((638, 380), (722, 380), CYAN, 3)
    connector.opacity = 0
    objects.append(connector)
    track(scene, connector, "opacity", (0, 1), start + 7.5, start + 8.5)
    show(scene, objects, start, end)


def attention(scene, start=25.5, end=39):
    objects = []
    tokens = ("The", "cat", "sat", "on", "the", "mat")
    xs = [385 + i * 230 for i in range(6)]
    # Lower triangular, row-normalized causal attention, with a strong cat -> sat relation.
    rows = []
    for row in range(6):
        scores = [math.exp(2.3 if (col == 1 and row >= 2) else 1.1 if col == row else 0.1) for col in range(row + 1)]
        rows.append([score / sum(scores) for score in scores])
    for i, (token, x) in enumerate(zip(tokens, xs)):
        objects.extend(
            (
                Rectangle(width=156, height=62, position=(x, 228), fill="#131E32", stroke=DIM, stroke_width=1),
                text(token, (x, 228), 27),
            )
        )
        objects.append(text(token, (668 + i * 82, 435), 20, "#8899B4"))
        objects.append(text(token, (575, 505 + i * 62), 20, "#8899B4"))
    for row in range(6):
        for col in range(6):
            weight = rows[row][col] if col <= row else 0
            cell = Rectangle(
                width=72,
                height=52,
                position=(668 + col * 82, 505 + row * 62),
                fill=CYAN if col <= row else "#172033",
                stroke=None,
                opacity=0.06 if col > row else 0.12 + weight * 0.88,
            )
            objects.append(cell)
    objects.extend((text("Q", (503, 659), 28, VIOLET), text("K", (873, 390), 28, CYAN)))
    for step in range(6):
        t = start + 1.1 + step * 1.65
        active = Rectangle(
            width=510, height=60, position=(873, 505 + step * 62), fill=None, stroke=VIOLET, stroke_width=2, opacity=0
        )
        objects.append(active)
        track(scene, active, "opacity", (0, 1, 1, 0), t, t + 1.6)
        for col in range(step + 1):
            a, b = (xs[step], 267), (xs[col], 267)
            height = 45 + (step - col) * 23
            path = PathData().move_to(*a).cubic_to(a[0], a[1] + height, b[0], b[1] + height, *b)
            arc = VectorPath(path, stroke=CYAN, stroke_width=1.5 + rows[step][col] * 7, opacity=0)
            objects.append(arc)
            track(scene, arc, "opacity", (0, 0.25 + rows[step][col] * 0.75, 0), t, t + 1.6)
            particle = dot(a, 5, VIOLET)
            particle.opacity = 0
            objects.append(particle)
            samples = []
            for j in range(25):
                u = j / 24
                samples.append(
                    (
                        (1 - u) ** 3 * a[0] + 3 * (1 - u) ** 2 * u * a[0] + 3 * (1 - u) * u * u * b[0] + u**3 * b[0],
                        a[1] + 3 * (1 - u) * u * height,
                    )
                )
            track(scene, particle, "position", samples, t, t + 1.45, linear)
            track(scene, particle, "opacity", (0, 1, 1, 0), t, t + 1.45)
    show(scene, objects, start, end)


def build_scene():
    scene = NeuralScene()
    scene.add(
        Circle(
            740,
            position=(960, 520),
            fill=RadialGradient((GradientStop(0, "#19294675"), GradientStop(1, "#080D1900"))),
            stroke=None,
        )
    )
    network(scene, 0, 13.5)
    embeddings(scene)
    attention(scene)
    network(scene, 38.5, 51.5, backward=True)
    network(scene, 51, 60, finale=True)
    for start, end, animation in scene.pending_tracks:
        with scene.at(start):
            scene.play(animation, run_time=end - start)
    scene.wait_until(DURATION)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="Source seconds 3–5")
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
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "skia-neural-network.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    source_range = args.range or ([3, 5] if args.preview else [0, DURATION])
    if args.frame is not None:
        source_range = [args.frame, args.frame]
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
                overwrite=args.overwrite,
                progress=progress,
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
