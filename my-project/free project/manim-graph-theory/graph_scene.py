"""Directed BFS, recursive DFS, and Dijkstra on one deterministic network."""

import itertools
from collections import deque
from fractions import Fraction
from math import inf

import numpy as np
from manim import (
    Arrow,
    Circle,
    Create,
    Dot,
    FadeIn,
    MoveAlongPath,
    Scene,
    Text,
    Transform,
    VGroup,
    Wait,
    config,
    linear,
)

DURATION = 45.0
CYAN, GOLD, GREEN = "#55DDEB", "#FFD166", "#76E5AA"
MUTED, WHITE = "#526272", "#EAF2FA"
POSITIONS = {
    "S": (-5.5, 0.3),
    "A": (-3, 2),
    "B": (-3, -1.4),
    "C": (0, 2),
    "D": (0, -1.4),
    "E": (3, 2),
    "F": (3, -1.4),
    "T": (5.5, 0.3),
}
EDGES = (
    ("S", "A", 4),
    ("S", "B", 1),
    ("A", "C", 2),
    ("A", "D", 2),
    ("B", "A", 2),
    ("B", "D", 5),
    ("C", "E", 4),
    ("D", "C", 1),
    ("D", "F", 2),
    ("E", "T", 4),
    ("F", "E", 1),
    ("F", "T", 3),
)


def adjacency():
    return {u: [(v, w) for a, v, w in EDGES if a == u] for u in POSITIONS}


def traversal_steps(depth_first=False):
    """Snapshots show pending FIFO nodes or the actual recursive call stack."""
    graph = adjacency()
    steps = []
    if depth_first:
        seen = set()

        def visit(u, parent, stack):
            seen.add(u)
            steps.append((u, parent, tuple(stack + [u])))
            for v, _ in graph[u]:
                if v not in seen:
                    visit(v, u, stack + [u])

        visit("S", None, [])
    else:
        pending, seen = deque([("S", None)]), {"S"}
        while pending:
            u, parent = pending.popleft()
            for v, _ in graph[u]:
                if v not in seen:
                    seen.add(v)
                    pending.append((v, u))
            steps.append((u, parent, tuple(v for v, _ in pending)))
    return steps


def dijkstra_steps():
    graph = adjacency()
    distances = dict.fromkeys(POSITIONS, inf)
    distances["S"] = 0
    parents, settled, steps = {}, set(), []
    while len(settled) < len(POSITIONS):
        u = min((v for v in POSITIONS if v not in settled), key=lambda v: (distances[v], v))
        if distances[u] == inf:
            break
        settled.add(u)
        changes = []
        for v, weight in graph[u]:
            candidate = distances[u] + weight
            improved = v not in settled and candidate < distances[v]
            changes.append((v, weight, candidate, improved))
            if improved:
                distances[v], parents[v] = candidate, u
        steps.append((u, changes, distances.copy(), settled.copy()))
    route = ["T"]
    while route[-1] != "S":
        route.append(parents[route[-1]])
    return steps, list(reversed(route))


def label(value, x, y, color=WHITE, size=25):
    return Text(str(value), font="DejaVu Sans", font_size=size, color=color).move_to([x, y, 0])


def distance_label(u, value, color):
    x, y = POSITIONS[u]
    return label(value, x, y + (0.57 if y > 1 else -0.57), color, 22).set_z_index(5)


class GraphAlgorithms(Scene):
    def beat(self, *animations, seconds=1, **kwargs):
        elapsed = getattr(self, "_cue_time", Fraction(0))
        target = elapsed + Fraction(str(seconds))
        fps = Fraction(str(config.frame_rate))
        count = round(target * fps) - round(elapsed * fps)
        if count < 1:
            raise ValueError("Frame rate too low for a scene beat")
        self._cue_time = target
        self.play(*animations, run_time=np.nextafter(float(count / fps), 0), **kwargs)

    def construct(self):
        config.background_color = "#000000"
        points = {u: np.array([x, y, 0.0]) for u, (x, y) in POSITIONS.items()}
        arrows, weights, nodes, names = {}, VGroup(), {}, VGroup()
        for u, v, weight in EDGES:
            arrow = Arrow(
                points[u],
                points[v],
                buff=0.34,
                color=MUTED,
                stroke_width=2.4,
                max_tip_length_to_length_ratio=0.065,
            ).set_z_index(0)
            arrows[u, v] = arrow
            delta = points[v] - points[u]
            normal = np.array([-delta[1], delta[0], 0]) / np.linalg.norm(delta)
            # Weights sit in black cutouts so diagonal lines never cross glyphs.
            center = (points[u] + points[v]) / 2 + normal * 0.2
            weights.add(
                label(weight, *center[:2], size=23)
                .add_background_rectangle(color="#000000", opacity=1, buff=0.06)
                .set_z_index(2)
            )
        for u, point in points.items():
            nodes[u] = (
                Circle(
                    radius=0.31,
                    color=CYAN,
                    stroke_width=2.5,
                    fill_color="#000000",
                    fill_opacity=1,
                )
                .move_to(point)
                .set_z_index(3)
            )
            names.add(label(u, *point[:2], size=25).set_z_index(4))
        self.beat(Create(VGroup(*arrows.values())), seconds=1.5)
        self.beat(FadeIn(VGroup(*nodes.values())), FadeIn(names), FadeIn(weights), seconds=1.5)

        panel = VGroup()
        self.add(panel)

        def reset():
            return [
                *[edge.animate.set_color(MUTED).set_stroke(width=2.4) for edge in arrows.values()],
                *[node.animate.set_stroke(CYAN, width=2.5).set_fill("#000000", opacity=1) for node in nodes.values()],
            ]

        def frontier(mode, values, color):
            result = VGroup(label(mode, -5.1, -3.0, color, 23))
            for i, u in enumerate(values):
                x = -3.45 + i * 0.8
                result.add(Circle(radius=0.25, color=color, stroke_width=1.5).move_to([x, -3, 0]))
                result.add(label(u, x, -3, color, 21))
            if not values:
                result.add(label("∅", -3.45, -3, MUTED, 23))
            return result

        for depth_first, color in ((False, CYAN), (True, GOLD)):
            for index, (u, parent, pending) in enumerate(traversal_steps(depth_first)):
                animations = [
                    Transform(panel, frontier("DFS · stack" if depth_first else "BFS · queue", pending, color))
                ]
                if index == 0:
                    animations.extend(reset())
                if parent:
                    animations.append(arrows[parent, u].animate.set_color(color).set_stroke(width=4))
                # Skip a duplicate animation on the source during the reset beat.
                if index == 0:
                    animations = animations[:1] + [a for a in animations[1:] if a.mobject is not nodes[u]]
                animations.append(nodes[u].animate.set_stroke(color, width=4).set_fill(color, opacity=0.25))
                self.beat(*animations, seconds=1)

        distances = {u: distance_label(u, "0" if u == "S" else "∞", CYAN) for u in POSITIONS}
        self.beat(
            *reset(),
            Transform(panel, frontier("Dijkstra", ["S"], GREEN)),
            FadeIn(VGroup(*distances.values())),
            seconds=1,
        )
        # 20–40s: each settled node gets a selection beat, edge probes, then updates.
        steps, route = dijkstra_steps()
        for u, changes, values, settled in steps:
            self.beat(nodes[u].animate.set_stroke(GOLD, width=4).set_fill(GOLD, opacity=0.28), seconds=0.5)
            packets, probes = VGroup(), []
            for v, _weight, _candidate, improved in changes:
                dot = Dot(radius=0.065, color=GREEN if improved else MUTED).set_z_index(6)
                dot.move_to(arrows[u, v].get_start())
                packets.add(dot)
                probes.append(MoveAlongPath(dot, arrows[u, v], rate_func=linear))
            self.add(packets)
            self.beat(*(probes or [Wait(frozen_frame=False)]), seconds=1)
            self.remove(packets)
            pending = sorted(
                (v for v in POSITIONS if v not in settled and values[v] < inf), key=lambda v: (values[v], v)
            )
            updates = [
                Transform(panel, frontier("Dijkstra", pending, GREEN)),
                nodes[u].animate.set_stroke(GREEN, width=3).set_fill(GREEN, opacity=0.22),
            ]
            for v, _weight, _candidate, improved in changes:
                if improved:
                    updates.append(Transform(distances[v], distance_label(v, values[v], GREEN)))
                    updates.append(arrows[u, v].animate.set_color(GREEN).set_stroke(width=3))
            self.beat(*updates, seconds=1)

        path_edges = set(itertools.pairwise(route))
        summary = label("S → B → A → D → F → T     Σw = 10", 0, -3, GREEN, 27)
        self.beat(
            Transform(panel, VGroup(summary)),
            *[
                arrow.animate.set_color(GREEN if edge in path_edges else MUTED).set_stroke(
                    width=5 if edge in path_edges else 1.5, opacity=1 if edge in path_edges else 0.35
                )
                for edge, arrow in arrows.items()
            ],
            *[
                nodes[u]
                .animate.set_stroke(GREEN if u in route else MUTED, width=3)
                .set_fill(GREEN if u in route else "#000000", opacity=0.22 if u in route else 1)
                for u in POSITIONS
            ],
            seconds=1,
        )
        packet = Dot(radius=0.09, color=GOLD).set_z_index(6)
        self.add(packet)
        for edge in itertools.pairwise(route):
            packet.move_to(arrows[edge].get_start())
            self.beat(MoveAlongPath(packet, arrows[edge], rate_func=linear), seconds=0.5)
        self.remove(packet)
        self.beat(Wait(frozen_frame=False), seconds=1.5)
        assert self._cue_time == Fraction(45)
