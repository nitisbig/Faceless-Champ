"""Camera-led local approximation, with essential mathematical labels only."""

import numpy as np
from manim import (
    Axes,
    Circle,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    MovingCameraScene,
    ReplacementTransform,
    Text,
    Transform,
    ValueTracker,
    VGroup,
    always_redraw,
    config,
    linear,
)

DURATION = 45.0
CYAN, GOLD, PINK, MUTED = "#55DDEB", "#FFD166", "#F783AC", "#34414D"


def f(x):
    return np.sin(1.5 * x) + 0.22 * np.sin(4 * x) + 0.08 * x * x


def df(x):
    return 1.5 * np.cos(1.5 * x) + 0.88 * np.cos(4 * x) + 0.16 * x


def ddf(x):
    return -2.25 * np.sin(1.5 * x) - 3.52 * np.sin(4 * x) + 0.16


def text(value, point, color=GOLD, size=27):
    return Text(value, font="DejaVu Sans", font_size=size, color=color).move_to(point)


class MathematicalCamera(MovingCameraScene):
    def construct(self):
        config.background_color = "#000000"
        frame = self.camera.frame
        frame.save_state()
        axes = Axes(
            x_range=[-4.5, 4.5, 1],
            y_range=[-2, 3.5, 1],
            x_length=12,
            y_length=5.2,
            tips=False,
            axis_config={"color": MUTED, "stroke_width": 1.2, "include_ticks": False},
        ).move_to([0, -0.25, 0])
        curve = axes.plot(f, x_range=[-4.4, 4.4, 0.025], color=CYAN, stroke_width=3)
        formula = text("f(x) = sin(1.5x) + 0.22 sin(4x) + 0.08x²", [0, 3.25, 0], CYAN, 25)
        self.play(Create(axes), Create(curve), FadeIn(formula), run_time=3)

        a, h = ValueTracker(-0.4), ValueTracker(0.65)
        point = lambda: axes.c2p(a.get_value(), f(a.get_value()))
        dot = always_redraw(lambda: Dot(point(), radius=0.045, color=GOLD))
        ring = Circle(radius=0.24, color=GOLD, stroke_width=1.5).move_to(point())
        callout = VGroup(
            Line(point() + [0.18, 0.18, 0], point() + [0.7, 0.75, 0], color=GOLD, stroke_width=1.4),
            text("f(a)", point() + [0.92, 0.87, 0], size=22),
        )
        self.play(FadeIn(dot), Create(ring), FadeIn(callout), run_time=2)
        self.wait(1)  # 6: establish the small region before entering it.
        self.play(
            frame.animate.set(width=4.8).move_to(point() + [0.35, -0.12, 0]),
            FadeOut(formula),
            FadeOut(ring),
            FadeOut(callout),
            run_time=4,
        )

        def chord():
            x, dx = a.get_value(), h.get_value()
            slope = (f(x + dx) - f(x)) / dx
            return Line(
                axes.c2p(x - 0.8, f(x) - 0.8 * slope),
                axes.c2p(x + 0.85, f(x) + 0.85 * slope),
                color=PINK,
                stroke_width=2,
            )

        secant = always_redraw(chord)
        other = always_redraw(
            lambda: Dot(
                axes.c2p(a.get_value() + h.get_value(), f(a.get_value() + h.get_value())), color=PINK, radius=0.025
            )
        )
        triangle = always_redraw(
            lambda: VGroup(
                DashedLine(
                    point(),
                    axes.c2p(a.get_value() + h.get_value(), f(a.get_value())),
                    color=GOLD,
                    stroke_width=1,
                    dash_length=0.04,
                ),
                DashedLine(
                    axes.c2p(a.get_value() + h.get_value(), f(a.get_value())),
                    other.get_center(),
                    color=PINK,
                    stroke_width=1,
                    dash_length=0.04,
                ),
            )
        )
        delta = text("Δx → 0", point() + [0.8, -0.75, 0], PINK, 13)
        self.play(Create(secant), FadeIn(other), FadeIn(triangle), FadeIn(delta), run_time=1)
        self.play(h.animate.set_value(0.015), run_time=3)  # 14
        tangent = always_redraw(
            lambda: Line(
                axes.c2p(a.get_value() - 0.8, f(a.get_value()) - 0.8 * df(a.get_value())),
                axes.c2p(a.get_value() + 0.8, f(a.get_value()) + 0.8 * df(a.get_value())),
                color=GOLD,
                stroke_width=2,
            )
        )
        self.play(FadeOut(secant), FadeOut(other), FadeOut(triangle), FadeOut(delta), FadeIn(tangent), run_time=1)
        for mob in (secant, other, triangle):
            mob.clear_updaters(recursive=True)
        # The camera follows the same moving mathematical point as the tangent.
        frame.add_updater(lambda mob: mob.move_to(point() + [0.3, -0.15, 0]))
        self.play(a.animate.set_value(0.8), run_time=3, rate_func=linear)  # 18
        frame.clear_updaters()
        local = VGroup(axes, curve, dot, tangent)
        equation = text("f(x) ≈ f(a) + f′(a)(x − a)", [0, 0, 0], GOLD, 34)
        self.play(frame.animate.restore(), FadeOut(local), FadeIn(equation), run_time=3)  # 21
        dot.clear_updaters()
        tangent.clear_updaters()
        quadratic = VGroup(
            text("f(x) ≈ f(a) + f′(a)(x − a)", [0, 0.4, 0], GOLD, 32),
            text("+ ½ f″(a)(x − a)²", [0, -0.55, 0], PINK, 32),
        )
        self.play(ReplacementTransform(equation, quadratic), run_time=3)
        self.wait(1)  # 25: isolate the equation before returning to geometry.

        anchor = 0.8
        p = axes.c2p(anchor, f(anchor))

        def approximation(order, extent):
            def value(x):
                dx = x - anchor
                return f(anchor) + df(anchor) * dx + (0.5 * ddf(anchor) * dx * dx if order == 2 else 0)

            return axes.plot(
                value,
                x_range=[anchor - extent, anchor + extent, 0.01],
                color=PINK if order == 2 else GOLD,
                stroke_width=3,
            )

        point_label = text("a", axes.c2p(anchor, 0) + [0, -0.25, 0], GOLD, 20)
        anchor_dot = Dot(p, color=GOLD, radius=0.045)
        guide = DashedLine(axes.c2p(anchor, 0), p, color=MUTED, stroke_width=1)
        line = approximation(1, 0.7)
        self.play(
            quadratic.animate.scale(0.72).move_to([0, 2.85, 0]),
            FadeIn(axes),
            Create(curve),
            FadeIn(anchor_dot),
            FadeIn(point_label),
            Create(guide),
            Create(line),
            run_time=3,
        )  # 28
        parabola = approximation(2, 0.7)
        self.play(Transform(line, parabola), run_time=4)  # 32
        self.play(frame.animate.set(width=5.2).move_to(p + [0.15, -0.25, 0]), FadeOut(quadratic), run_time=4)  # 36
        # Pull back from local agreement to reveal where approximation diverges.
        self.play(
            frame.animate.set(width=9).move_to(p + [0.1, -0.55, 0]), Transform(line, approximation(2, 1.35)), run_time=4
        )  # 40
        final = (
            VGroup(
                text("f(x) ≈ f(a) + f′(a)(x − a)", [0, 0, 0], size=19),
                text("+ ½ f″(a)(x − a)²", [0, 0, 0], PINK, size=19),
            )
            .arrange(buff=0.12)
            .move_to(p + [0.1, 1.45, 0])
        )
        self.play(FadeIn(final), run_time=3)
        self.wait(2)  # 45
