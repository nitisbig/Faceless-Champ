"""60 seconds of algorithm graphics, using Faceless Champ and native Skia CPU."""

from __future__ import annotations

import argparse
import json
import math
from collections import deque
from pathlib import Path

from PIL import ImageColor

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Animation,
    Arrow,
    Canvas,
    Circle,
    ExportProgress,
    ExportSettings,
    Group,
    Polyline,
    Rectangle,
    Scene,
    Text,
    create_renderer,
    linear,
    render,
    rendering_identity,
    save_frame,
    smooth,
)

ROOT = Path(__file__).resolve().parent
DURATION = 60.0
BG = "#000000"
CYAN, GOLD, MINT, PURPLE = "#64DAFF", "#FFC875", "#74EDBA", "#AF98FF"
WHITE, DIM = "#E9F2FF", "#263D4F"


class AlgorithmScene(Scene):
    def __init__(self):
        super().__init__(Canvas(1920, 1080, BG))
        self.tracks = []
        self.evidence = {}


def track(scene, obj, prop, values, start, end, easing=smooth):
    values = tuple(ImageColor.getcolor(v, "RGBA") for v in values) if prop == "fill" else tuple(values)
    scene.tracks.append(
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


def chapter(scene, objects, start, end):
    group = Group(*objects)
    with scene.at(start):
        scene.add(group)
    track(scene, group, "opacity", (0, 1), start, start + 0.4)
    track(scene, group, "opacity", (1, 0), end - 0.4, end)


def label(value, p, size=28, color=WHITE):
    return Text(str(value), position=p, font=CLEAN_FLOW_FONT, font_size=size, color=color, text_engine="skia")


def line(a, b, color=DIM, width=3):
    return Polyline((a, b), stroke=color, stroke_width=width, line_cap="round")


def arrow(a, b, color=DIM, width=3):
    return Arrow(a, b, stroke=color, stroke_width=width, tip_size=13)


def node(p, value, color=CYAN, radius=39):
    return Group(Circle(radius, position=p, fill="#071018", stroke=color, stroke_width=3), label(value, p, 28, color))


def pulse(scene, objects, p, start, color=GOLD, radius=47, duration=0.6):
    ring = Circle(radius, position=p, fill=None, stroke=color, stroke_width=3, opacity=0)
    objects.append(ring)
    track(scene, ring, "opacity", (0, 1, 0), start, start + duration)
    track(scene, ring, "scale", (0.9, 1.25), start, start + duration)


def sorting(scene):
    values = [8, 3, 10, 5, 1, 7, 4, 9, 2, 6]
    items, bars, objects = list(range(10)), [], [line((240, 825), (1680, 825))]
    for i, value in enumerate(values):
        x, height = 330 + i * 140, value * 48
        bar = Rectangle(width=86, height=height, position=(x, 824 - height / 2), fill=CYAN, stroke=None)
        group = Group(bar, label(value, (x, 870), 28))
        bars.append(group)
        objects.append(group)
    # Selection sort: one scan, one placement, then retain the sorted prefix.
    locations = [bar.position for bar in bars]
    t, swaps = 0.8, []
    for left in range(9):
        minimum = left
        for j in range(left + 1, 10):
            if values[items[j]] < values[items[minimum]]:
                minimum = j
        for j in range(left, 10):
            pulse(scene, objects, (330 + j * 140, 935), t + (j - left) * 0.045, GOLD if j == minimum else CYAN, 9, 0.22)
        a, b = items[left], items[minimum]
        t += 0.5
        if left != minimum:
            for item, old, new, direction in ((a, left, minimum, -1), (b, minimum, left, 1)):
                origin = locations[item]
                dx = (new - old) * 140
                track(
                    scene,
                    bars[item],
                    "position",
                    (origin, (origin[0] + dx / 2, origin[1] + direction * 64), (origin[0] + dx, origin[1])),
                    t,
                    t + 0.6,
                )
                # Scene construction tracks later swaps from the last authored location.
                locations[item] = (origin[0] + dx, origin[1])
            items[left], items[minimum] = b, a
            swaps.append((left, minimum))
        track(scene, bars[b].children[0], "fill", (CYAN, MINT), t + 0.6, t + 0.8)
        t += 0.8
    track(scene, bars[items[-1]].children[0], "fill", (CYAN, MINT), 12.1, 12.4)
    scene.evidence["sorted"] = [values[i] for i in items]
    scene.evidence["swaps"] = swaps
    chapter(scene, objects, 0, 14)


def tree(scene):
    positions = [(960, 240), (600, 440), (1320, 440), (400, 690), (780, 690), (1140, 690), (1520, 690)]
    values = [8, 4, 12, 2, 6, 10, 14]
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 5), (2, 6)]
    objects = []
    for i, j in edges:
        edge = line(positions[i], positions[j])
        objects.append(edge)
        track(scene, edge, "draw", (0, 1), 14.5 + j * 0.38, 15 + j * 0.38)
    for i, (p, value) in enumerate(zip(positions, values)):
        n = node(p, value)
        objects.append(n)
        track(scene, n, "opacity", (0, 1), 14.4 + i * 0.4, 14.8 + i * 0.4)
        track(scene, n, "scale", (0.7, 1), 14.4 + i * 0.4, 14.8 + i * 0.4)
    # An in-order walk emits the binary search tree's sorted values.
    order = [3, 1, 4, 0, 5, 2, 6]
    for step, i in enumerate(order):
        t = 18 + step * 0.72
        pulse(scene, objects, positions[i], t, MINT)
        token = node(positions[i], values[i], MINT, 30)
        token.opacity = 0
        objects.append(token)
        track(scene, token, "opacity", (0, 1), t, t + 0.15)
        track(
            scene,
            token,
            "position",
            (
                token.position,
                (token.position[0] + (480 + step * 160 - positions[i][0]), token.position[1] + 895 - positions[i][1]),
            ),
            t + 0.1,
            t + 0.65,
        )
    scene.evidence["inorder"] = [values[i] for i in order]
    chapter(scene, objects, 14, 25)


def traversal(scene):
    points = [(380, 510), (700, 285), (700, 735), (1080, 285), (1080, 735), (1450, 510)]
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (2, 4), (3, 5), (4, 5)]
    objects = [line(points[a], points[b]) for a, b in edges]
    objects.extend(node(p, chr(65 + i)) for i, p in enumerate(points))
    queue, seen, order, discovery = deque([0]), {0}, [], []
    while queue:
        u = queue.popleft()
        order.append(u)
        for a, b in edges:
            v = b if a == u else a if b == u else None
            if v is not None and v not in seen:
                seen.add(v)
                queue.append(v)
                discovery.append((u, v))
    for i, (a, b) in enumerate(discovery):
        t = 26 + i * 1.25
        active = line(points[a], points[b], MINT, 5)
        active.opacity = 0
        objects.append(active)
        track(scene, active, "opacity", (0, 1), t, t + 0.15)
        track(scene, active, "draw", (0, 1), t, t + 0.7)
        pulse(scene, objects, points[b], t + 0.65, MINT)
    for step, i in enumerate(order):
        t = 25.7 + step * 1.25
        pulse(scene, objects, points[i], t)
        token = node((550 + step * 160, 910), chr(65 + i), MINT, 28)
        token.opacity = 0
        objects.append(token)
        track(scene, token, "opacity", (0, 1), t, t + 0.3)
    scene.evidence["bfs"] = [chr(65 + i) for i in order]
    chapter(scene, objects, 25, 36)


def linked_list(scene):
    xs = [390, 750, 1110, 1470]
    objects = []
    for i, x in enumerate(xs):
        objects.extend(
            (
                Rectangle(width=170, height=105, position=(x, 470), fill="#071018", stroke=CYAN, stroke_width=3),
                label([12, 24, 36, 48][i], (x - 20, 470)),
                line((x + 34, 420), (x + 34, 520)),
                Circle(5, position=(x + 60, 470), fill=CYAN, stroke=None),
            )
        )
        if i < 3:
            edge = arrow((x + 85, 470), (xs[i + 1] - 85, 470), CYAN)
            objects.append(edge)
            if i == 1:
                track(scene, edge, "opacity", (1, 0), 38, 38.5)
    # Insert 30 between 24 and 36; replace the old pointer with two new pointers.
    inserted = Group(
        Rectangle(width=170, height=105, position=(930, 740), fill="#071018", stroke=MINT, stroke_width=3),
        label(30, (910, 740), color=MINT),
        line((964, 690), (964, 790)),
        Circle(5, position=(990, 740), fill=MINT, stroke=None),
    )
    objects.append(inserted)
    track(scene, inserted, "opacity", (0, 1), 36.8, 37.5)
    for a, b, t in (((835, 485), (866, 680), 38.5), ((1010, 700), (1060, 530), 39.5)):
        edge = arrow(a, b, MINT)
        objects.append(edge)
        track(scene, edge, "draw", (0, 1), t, t + 0.8)
    for i, p in enumerate(((390, 470), (750, 470), (930, 740), (1110, 470), (1470, 470))):
        pulse(scene, objects, p, 40.4 + i * 0.33, GOLD, 65, 0.4)
    scene.evidence["linked_list"] = [12, 24, 30, 36, 48]
    chapter(scene, objects, 36, 43)


def stack(scene):
    objects = [Polyline(((700, 270), (700, 870), (1220, 870), (1220, 270)), stroke=DIM, stroke_width=5)]
    for i, value in enumerate((16, 32, 64, 128)):
        target = (960, 795 - i * 132)
        block = Group(
            Rectangle(width=440, height=108, position=(960, 170), fill="#0C2029", stroke=CYAN, stroke_width=3),
            label(value, (960, 170), 34),
        )
        objects.append(block)
        t = 43.5 + i * 0.85
        track(scene, block, "opacity", (0, 1), t, t + 0.15)
        origin = block.position
        final = (origin[0], origin[1] + target[1] - 170)
        track(scene, block, "position", (origin, final), t, t + 0.65)
        if i >= 2:
            t = 47.4 + (3 - i) * 1.1
            track(scene, block, "position", (final, (1480, final[1] - 90)), t, t + 0.8)
            track(scene, block, "opacity", (1, 1, 0), t, t + 1)
    scene.evidence["stack_pop_order"] = [128, 64]
    chapter(scene, objects, 43, 51)


def flow(scene):
    points = [(340, 540), (800, 300), (800, 780), (1300, 300), (1300, 780), (1600, 540)]
    # Two edge-disjoint augmenting paths: min(5,4,6) + min(4,3,5) = 7.
    edges = [(0, 1, 5), (0, 2, 4), (1, 3, 4), (2, 4, 3), (3, 5, 6), (4, 5, 5), (1, 4, 2)]
    objects = []
    routes = [[0, 2, 4], [1, 3, 5]]
    flows = {i: 4 if i in routes[0] else 3 if i in routes[1] else 0 for i in range(7)}
    for i, (a, b, capacity) in enumerate(edges):
        p, q = points[a], points[b]
        dx, dy = q[0] - p[0], q[1] - p[1]
        length = math.hypot(dx, dy)
        aa = (p[0] + dx / length * 49, p[1] + dy / length * 49)
        bb = (q[0] - dx / length * 49, q[1] - dy / length * 49)
        objects.append(arrow(aa, bb, DIM, 4))
        midpoint = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 - 32)
        before = label(f"0/{capacity}", midpoint, 25)
        objects.append(before)
        if flows[i]:
            t = 52 + (0 if i in routes[0] else 3)
            active = arrow(aa, bb, MINT if i in routes[0] else PURPLE, 7)
            objects.append(active)
            track(scene, active, "draw", (0, 1), t, t + 0.8)
            track(scene, before, "opacity", (1, 0), t + 0.8, t + 1)
            after = label(f"{flows[i]}/{capacity}", midpoint, 25, MINT if i in routes[0] else PURPLE)
            objects.append(after)
            track(scene, after, "opacity", (0, 1), t + 0.8, t + 1)
            for cycle in range(3):
                packet = Circle(7, position=aa, fill=GOLD, stroke=None, opacity=0)
                objects.append(packet)
                begin = t + 0.2 + cycle * 0.7
                track(scene, packet, "position", (aa, bb), begin, begin + 0.65, linear)
                track(scene, packet, "opacity", (0, 1, 1, 0), begin, begin + 0.65, linear)
    objects.extend(node(p, value, CYAN, 43) for p, value in zip(points, ("s", "a", "b", "c", "d", "t")))
    total = label("4 + 3 = 7", (960, 965), 34, GOLD)
    objects.append(total)
    track(scene, total, "opacity", (0, 1), 57.5, 58.1)
    scene.evidence["flow"] = {"value": 7, "edges": [(a, b, flows[i], c) for i, (a, b, c) in enumerate(edges)]}
    chapter(scene, objects, 51, 60)


def build_scene():
    scene = AlgorithmScene()
    for build in (sorting, tree, traversal, linked_list, stack, flow):
        build(scene)
    for start, end, animation in scene.tracks:
        with scene.at(start):
            scene.play(animation, run_time=end - start)
    scene.wait_until(DURATION)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float)
    mode.add_argument("--preview", action="store_true", help="Two-second sorting preview")
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
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "skia-algorithms.mp4"
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
                "scene_duration": scene.duration,
                "source_range": source_range,
                "rendering": rendering_identity("skia", scene),
                "algorithms": scene.evidence,
            },
            indent=2,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
