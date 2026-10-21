"""A geometric area proof; native Manim producer for FacelessChamp."""

import numpy as np
from manim import (
    Arc,
    Create,
    FadeIn,
    FadeOut,
    LaggedStart,
    Line,
    Polygon,
    Rotate,
    Scene,
    Text,
    Transform,
    VGroup,
    config,
)

DURATION = 45.0
A, B, UNIT = 3.0, 2.0, 0.75
CYAN, PINK, GOLD = "#55DDEB", "#F783AC", "#FFD166"
TRI_COLORS = ("#466B91", "#5B659B", "#457E87", "#80638D")
LEFT = np.array([-5.025, -1.425, 0.0])
RIGHT = np.array([1.275, -1.425, 0.0])


def label(value, position, color="#E8EEF5", size=28):
    return Text(value, font="DejaVu Sans", font_size=size, color=color).move_to(position)


def patch(points, color, opacity=0.22):
    return Polygon(*points, color=color, stroke_width=2.3, fill_color=color, fill_opacity=opacity)


def p(origin, x, y):
    return origin + UNIT * np.array([x, y, 0.0])


def triangle(origin, corner, angle, color):
    shape = patch([np.zeros(3), [A * UNIT, 0, 0], [0, B * UNIT, 0]], color, 0.65)
    return shape.rotate(angle, about_point=np.zeros(3)).shift(p(origin, *corner))


def border(origin):
    return patch([p(origin, 0, 0), p(origin, 5, 0), p(origin, 5, 5), p(origin, 0, 5)], "#A5B4C4", 0)


class PythagoreanProof(Scene):
    def construct(self):
        config.background_color = "#000000"
        # 0–12: construct the triangle, measure its angles, and erect squares.
        o = np.array([-1.4, -0.4, 0.0])
        x, y = o + [2.1, 0, 0], o + [0, 1.4, 0]
        tri = patch([o, x, y], "#CCD9E7", 0.08)
        sides = VGroup(
            label("a", o + [1.05, -0.24, 0], CYAN),
            label("b", o + [-0.25, 0.7, 0], PINK),
            label("c", (x + y) / 2 + [0.17, 0.22, 0], GOLD),
        )
        right_angle = VGroup(Line(o + [0.22, 0, 0], o + [0.22, 0.22, 0]), Line(o + [0.22, 0.22, 0], o + [0, 0.22, 0]))
        theta = np.arctan2(B, A)
        angle = Arc(radius=0.42, start_angle=np.pi - theta, angle=theta, arc_center=x, color=GOLD)
        measurements = VGroup(
            label("90°", o + [0.55, 0.32, 0], size=20), label("θ = 33.7°", x + [1.15, 0.05, 0], GOLD, 23)
        )
        self.play(Create(tri), run_time=2)
        self.play(FadeIn(sides), Create(right_angle), Create(angle), run_time=2)
        self.play(FadeIn(measurements), run_time=1)
        self.wait(1)
        square_a = patch([o, x, x + [0, -2.1, 0], o + [0, -2.1, 0]], CYAN)
        square_b = patch([o, y, y + [-1.4, 0, 0], o + [-1.4, 0, 0]], PINK)
        outward = np.array([1.4, 2.1, 0])
        square_c = patch([x, y, y + outward, x + outward], GOLD)
        squares = VGroup(square_a, square_b, square_c)
        areas = VGroup(
            label("a²", square_a.get_center(), CYAN, 32),
            label("b²", square_b.get_center(), PINK, 32),
            label("c²", square_c.get_center(), GOLD, 32),
        )
        self.play(
            LaggedStart(*[Create(s) for s in squares], lag_ratio=0.3),
            FadeOut(measurements),
            FadeOut(angle),
            FadeOut(sides),
            run_time=3,
        )
        self.play(FadeIn(areas), run_time=1)
        self.wait(1)
        self.play(FadeOut(VGroup(tri, right_angle, squares, areas)), run_time=1)

        # 12–19: four congruent triangles enclose a square of side c.
        left_border = border(LEFT)
        corners = ((0, 0), (5, 0), (5, 5), (0, 5))
        triangles = VGroup(
            *[
                triangle(LEFT, corner, i * np.pi / 2, color)
                for i, (corner, color) in enumerate(zip(corners, TRI_COLORS))
            ]
        )
        c_square = patch([p(LEFT, A, 0), p(LEFT, 5, A), p(LEFT, B, 5), p(LEFT, 0, B)], GOLD)
        c_label = label("c²", c_square.get_center(), GOLD, 36)
        edge_labels = VGroup(
            label("a", p(LEFT, A / 2, -0.35), CYAN, 24), label("b", p(LEFT, A + B / 2, -0.35), PINK, 24)
        )
        self.play(Create(left_border), run_time=1)
        self.play(LaggedStart(*[FadeIn(t) for t in triangles], lag_ratio=0.25), run_time=3)
        self.play(Create(c_square), FadeIn(c_label), FadeIn(edge_labels), run_time=2)
        self.wait(1)

        # 19–22: duplicate the entire area, preserving the first arrangement.
        right_border = border(RIGHT)
        moving = triangles.copy()
        self.add(moving)
        self.play(moving.animate.shift(RIGHT - LEFT), Create(right_border), run_time=3)

        # 22–30: each piece rotates rigidly, then translates to its new place.
        # Correspondence preserves the same colored triangle throughout the proof.
        targets = ((0, 0), (A, B), (5, B), (A, 5))
        rotations = (0, np.pi / 2, -np.pi / 2, 0)
        # Manim rounds each play up to a whole frame. At 30 fps, 0.75s
        # and 1.25s each contain half a frame, adding one frame per piece.
        # Allocate whole frames within each two-second movement instead.
        fps = float(config.frame_rate)
        turn_frames = round(0.75 * fps)
        move_frames = round(2 * fps) - turn_frames
        for i, (target, turn) in enumerate(zip(targets, rotations)):
            pivot = p(RIGHT, *corners[i])
            self.play(Rotate(moving[i], turn, about_point=pivot), run_time=turn_frames / fps)
            self.play(moving[i].animate.shift(p(RIGHT, *target) - pivot), run_time=move_frames / fps)

        # 30–35: the two remaining regions are exactly a² and b².
        a_square = patch([p(RIGHT, 0, B), p(RIGHT, A, B), p(RIGHT, A, 5), p(RIGHT, 0, 5)], CYAN)
        b_square = patch([p(RIGHT, A, 0), p(RIGHT, 5, 0), p(RIGHT, 5, B), p(RIGHT, A, B)], PINK)
        a_label = label("a²", a_square.get_center(), CYAN, 36)
        b_label = label("b²", b_square.get_center(), PINK, 32)
        self.play(Create(a_square), FadeIn(a_label), run_time=2)
        self.play(Create(b_square), FadeIn(b_label), run_time=2)
        self.play(FadeIn(label("=", [0, 0.45, 0], size=42)), run_time=1)

        # 35–41: matching triangle areas cancel; only uncovered areas remain.
        self.play(triangles.animate.set_opacity(0.22), moving.animate.set_opacity(0.22), run_time=2)
        equation = (
            VGroup(
                label("a²", [0, 0, 0], CYAN, 42),
                label("+", [0, 0, 0], size=38),
                label("b²", [0, 0, 0], PINK, 42),
                label("=", [0, 0, 0], size=38),
                label("c²", [0, 0, 0], GOLD, 42),
            )
            .arrange(buff=0.22)
            .move_to([0, -2.8, 0])
        )
        for source, target in ((a_label, equation[0]), (b_label, equation[2]), (c_label, equation[4])):
            ghost = source.copy()
            self.add(ghost)
            self.play(Transform(ghost, target), run_time=1)
        self.play(FadeIn(equation[1]), FadeIn(equation[3]), run_time=1)
        self.wait(4)
