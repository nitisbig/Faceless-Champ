"""Graphics-only linear algebra, prepared by native Manim for FacelessChamp."""

import numpy as np
from manim import (
    Arrow,
    Dot,
    FadeIn,
    Line,
    Polygon,
    Scene,
    Text,
    UpdateFromAlphaFunc,
    VGroup,
    config,
    smooth,
)

DURATION = 45.0
CYAN, PINK, GOLD = "#55DDEB", "#F783AC", "#FFD166"
ORIGIN = np.array([1.65, -0.35, 0.0])
SCALE = 1.15
IDENTITY = np.eye(2)
STRETCH = np.diag([1.6, 0.65])
SHEAR = np.array([[1.0, 0.8], [0.0, 1.0]])


def rotation(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s], [s, c]])


def point(matrix, xy):
    return ORIGIN + SCALE * np.append(matrix @ np.asarray(xy), 0)


def world_for(matrix):
    def p(x, y):
        return point(matrix, (x, y))

    grid = VGroup(
        *[Line(p(x, -1.8), p(x, 1.8), color="#263846", stroke_width=1.2) for x in np.arange(-2, 2.01, 0.5)],
        *[Line(p(-2, y), p(2, y), color="#263846", stroke_width=1.2) for y in np.arange(-1.5, 1.51, 0.5)],
        Line(p(-2.3, 0), p(2.3, 0), color="#597182", stroke_width=2),
        Line(p(0, -2), p(0, 2), color="#597182", stroke_width=2),
    )
    square = Polygon(p(0, 0), p(1, 0), p(1, 1), p(0, 1), color=GOLD, stroke_width=2, fill_color=GOLD, fill_opacity=0.12)
    guides = VGroup(
        Line(p(1, 0), p(1, 1), color=PINK, stroke_width=2, stroke_opacity=0.6),
        Line(p(0, 1), p(1, 1), color=CYAN, stroke_width=2, stroke_opacity=0.6),
    )
    arrows = VGroup(
        *[
            Arrow(ORIGIN, p(*xy), buff=0, color=color, stroke_width=4, max_tip_length_to_length_ratio=0.15)
            for xy, color in (((1, 0), CYAN), ((0, 1), PINK), ((1, 1), GOLD))
        ]
    )
    return VGroup(grid, square, guides, arrows, Dot(p(1, 1), radius=0.065, color=GOLD))


def matrix_panel(matrix, symbol):
    """No TeX dependency; column colors match the two transformed basis vectors."""
    center = np.array([-4.65, 1.0, 0])
    entries = VGroup()
    for row in range(2):
        for col, color in enumerate((CYAN, PINK)):
            value = matrix[row, col]
            if abs(value) < 0.005:
                value = 0.0
            entries.add(
                Text(f"{value:.2f}", font="DejaVu Sans", font_size=29, color=color).move_to(
                    center + [col * 1.05 - 0.525, 0.36 - row * 0.72, 0]
                )
            )
    brackets = VGroup()
    for side in (-1, 1):
        x = center[0] + side * 1.13
        brackets.add(
            Line([x - side * 0.16, 1.76, 0], [x, 1.76, 0]),
            Line([x, 1.76, 0], [x, 0.24, 0]),
            Line([x, 0.24, 0], [x - side * 0.16, 0.24, 0]),
        )
    name = Text(symbol, font="DejaVu Sans", font_size=28, color="#DCE6EF")
    name.move_to([-4.65, 2.35, 0])
    return VGroup(name, brackets, entries)


class MatrixTransformations(Scene):
    def construct(self):
        config.background_color = "#000000"
        world = world_for(IDENTITY)
        panel = matrix_panel(IDENTITY, "I")
        equation = (
            VGroup(
                Text("v", font_size=30, color=GOLD),
                Text("=", font_size=30),
                Text("e₁", font_size=30, color=CYAN),
                Text("+", font_size=30),
                Text("e₂", font_size=30, color=PINK),
            )
            .arrange(buff=0.12)
            .move_to([-4.65, -1.0, 0])
        )
        self.play(FadeIn(world), FadeIn(panel), FadeIn(equation), run_time=2)
        self.wait(1)

        def morph(path, symbol, seconds):
            def update_world(mobject, alpha):
                mobject.become(world_for(path(alpha)))

            def update_panel(mobject, alpha):
                mobject.become(matrix_panel(path(alpha), symbol))

            self.play(
                UpdateFromAlphaFunc(world, update_world),
                UpdateFromAlphaFunc(panel, update_panel),
                run_time=seconds,
                rate_func=smooth,
            )

        turn = np.pi / 3
        r = rotation(turn)
        morph(lambda a: rotation(turn * a), "R", 6)
        self.wait(3)
        morph(lambda a: rotation(turn * (1 - a)), "R", 2)
        morph(lambda a: IDENTITY + a * (STRETCH - IDENTITY), "S", 6)
        self.wait(3)
        morph(lambda a: STRETCH + a * (IDENTITY - STRETCH), "S", 2)
        morph(lambda a: IDENTITY + a * (SHEAR - IDENTITY), "H", 6)
        self.wait(3)
        morph(lambda a: SHEAR + a * (IDENTITY - SHEAR), "H", 2)
        # Rightmost matrix acts first: v -> Rv -> SRv -> HSRv.
        morph(lambda a: rotation(turn * a), "R", 2)
        morph(lambda a: (IDENTITY + a * (STRETCH - IDENTITY)) @ r, "SR", 2)
        morph(lambda a: (IDENTITY + a * (SHEAR - IDENTITY)) @ STRETCH @ r, "HSR", 2)
        self.wait(3)
