"""A continuous calculus demonstration; native Manim, no LaTeX dependency."""

from manim import (
    Axes,
    Create,
    DashedLine,
    DecimalNumber,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    Scene,
    Text,
    Transform,
    ValueTracker,
    VGroup,
    always_redraw,
    config,
    linear,
)

DURATION = 45.0
CYAN, GOLD, PINK = "#55DDEB", "#FFD166", "#F783AC"
MUTED = "#536471"


def f(x):
    return 2.5 - 0.35 * x * x


def derivative(x):
    return -0.7 * x


def midpoint_sum(n):
    dx = 4 / n
    return sum(f(-2 + (i + 0.5) * dx) * dx for i in range(n))


def label(content, position, color="WHITE", size=27):
    return Text(content, font="DejaVu Sans", font_size=size, color=color).move_to(position)


class Calculus(Scene):
    def construct(self):
        config.background_color = "#000000"
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[0, 3.3, 1],
            x_length=8,
            y_length=4.7,
            tips=False,
            axis_config={"color": MUTED, "stroke_width": 2, "include_ticks": False},
        ).move_to([-2.0, -0.25, 0])
        curve = axes.plot(f, x_range=[-2.6, 2.6], color=CYAN, stroke_width=4)
        formula = label("f(x) = 2.5 − 0.35x²", [-2, 3.05, 0], CYAN, 30)
        axis_labels = VGroup(
            label("x", axes.c2p(3, 0) + [0.2, -0.12, 0], size=21),
            label("0", axes.c2p(0, 0) + [-0.18, -0.22, 0], size=19),
        )
        self.play(Create(axes), Create(curve), FadeIn(formula), FadeIn(axis_labels), run_time=2)

        x, h = ValueTracker(-1.6), ValueTracker(1.4)

        def slope():
            return (f(x.get_value() + h.get_value()) - f(x.get_value())) / h.get_value()

        def slope_line(m):
            a = x.get_value()
            # Fixed data-space span keeps the moving line inside the graph area.
            return Line(
                axes.c2p(a - 0.62, f(a) - m * 0.62), axes.c2p(a + 0.62, f(a) + m * 0.62), color=GOLD, stroke_width=4
            )

        secant = always_redraw(
            lambda: Line(
                axes.c2p(x.get_value(), f(x.get_value())),
                axes.c2p(x.get_value() + h.get_value(), f(x.get_value() + h.get_value())),
                color=PINK,
                stroke_width=4,
            )
        )
        a_dot = always_redraw(lambda: Dot(axes.c2p(x.get_value(), f(x.get_value())), color=GOLD, radius=0.065))
        b_dot = always_redraw(
            lambda: Dot(
                axes.c2p(x.get_value() + h.get_value(), f(x.get_value() + h.get_value())), color=PINK, radius=0.065
            )
        )
        triangle = always_redraw(
            lambda: VGroup(
                DashedLine(
                    axes.c2p(x.get_value(), f(x.get_value())),
                    axes.c2p(x.get_value() + h.get_value(), f(x.get_value())),
                    color=MUTED,
                ),
                DashedLine(
                    axes.c2p(x.get_value() + h.get_value(), f(x.get_value())),
                    axes.c2p(x.get_value() + h.get_value(), f(x.get_value() + h.get_value())),
                    color=PINK,
                ),
            )
        )

        def readout(prefix, value, y, color):
            number = DecimalNumber(value(), num_decimal_places=2, font_size=30, color=color, mob_class=Text)
            number.move_to([5.25, y, 0])
            number.add_updater(lambda mob: mob.set_value(value()).move_to([5.25, y, 0]))
            return VGroup(label(prefix, [3.7, y, 0], color, 25), number)

        h_value = readout("Δx =", h.get_value, 2.1, PINK)
        slope_value = readout("Δy/Δx =", slope, 1.35, GOLD)
        self.play(
            FadeIn(secant),
            FadeIn(triangle),
            FadeIn(a_dot),
            FadeIn(b_dot),
            FadeIn(h_value),
            FadeIn(slope_value),
            run_time=2,
        )
        self.play(h.animate.set_value(0.7), run_time=4)
        self.play(h.animate.set_value(0.025), run_time=4)
        # 12s: replace the limiting secant with the exact analytic tangent.
        tangent = always_redraw(lambda: slope_line(derivative(x.get_value())))
        slope_value.clear_updaters(recursive=True)
        exact_value = readout("f′(x) =", lambda: derivative(x.get_value()), 1.35, GOLD)
        x_value = readout("x =", x.get_value, 2.1, CYAN)
        d_axes = Axes(
            x_range=[-2.5, 2.5, 1],
            y_range=[-2, 2, 1],
            x_length=3.4,
            y_length=2.1,
            tips=False,
            axis_config={"color": MUTED, "stroke_width": 1.5, "include_ticks": False},
        ).move_to([4.4, -0.65, 0])
        d_curve = d_axes.plot(derivative, x_range=[-2.5, 2.5], color=GOLD, stroke_width=2.5)
        d_dot = always_redraw(
            lambda: Dot(d_axes.c2p(x.get_value(), derivative(x.get_value())), color=GOLD, radius=0.065)
        )
        d_formula = label("f′(x) = −0.7x", [4.4, -2.3, 0], GOLD, 24)
        self.play(
            FadeOut(secant),
            FadeOut(triangle),
            FadeOut(b_dot),
            FadeOut(h_value),
            FadeOut(slope_value),
            FadeIn(tangent),
            FadeIn(exact_value),
            FadeIn(x_value),
            FadeIn(d_axes),
            Create(d_curve),
            FadeIn(d_dot),
            FadeIn(d_formula),
            run_time=1,
        )
        self.play(x.animate.set_value(2.1), run_time=7, rate_func=linear)
        self.play(x.animate.set_value(0), run_time=2)
        maximum = label("f′(0) = 0", [-2, 2.25, 0], GOLD, 25)
        self.play(FadeIn(maximum), run_time=1)
        # 23s: leave the same curve in place and switch to accumulated area.
        dynamic = VGroup(tangent, a_dot, exact_value, x_value, d_axes, d_curve, d_dot, d_formula, maximum)
        self.play(FadeOut(dynamic), run_time=2)
        dynamic.clear_updaters(recursive=True)

        bounds = VGroup(
            *[
                VGroup(
                    DashedLine(axes.c2p(v, 0), axes.c2p(v, f(v)), color=MUTED),
                    label(str(v), axes.c2p(v, 0) + [0, -0.28, 0], size=22),
                )
                for v in (-2, 2)
            ]
        )

        def rectangles(n):
            return axes.get_riemann_rectangles(
                curve,
                x_range=[-2, 2],
                dx=4 / n,
                input_sample_type="center",
                color=[CYAN, GOLD],
                fill_opacity=0.38,
                stroke_width=0.6,
                stroke_color="#000000",
                width_scale_factor=1.0,
            ).set_z_index(-1)

        def sum_panel(n):
            return VGroup(
                label(f"n = {n}", [4.35, 2.1, 0], CYAN),
                label(f"Δx = {4 / n:.4f}", [4.35, 1.25, 0], size=25),
                label("Σ f(xᵢ) Δx", [4.35, 0.1, 0], GOLD, 29),
                label(f"= {midpoint_sum(n):.5f}", [4.35, -0.75, 0], GOLD, 29),
            )

        rects, panel = rectangles(8), sum_panel(8)
        self.play(FadeIn(bounds), FadeIn(rects), FadeIn(panel), run_time=2)
        self.wait(2)
        for n in (16, 32, 64, 128):
            self.play(Transform(rects, rectangles(n)), Transform(panel, sum_panel(n)), run_time=2)
        # 37s: the sum becomes the exact definite integral.
        area = axes.get_area(curve, x_range=[-2, 2], color=[CYAN, GOLD], opacity=0.38).set_z_index(-1)
        integral = VGroup(
            label("∫²₋₂ f(x) dx", [4.35, 1.6, 0], GOLD, 32),
            label("= [2.5x − 0.35x³/3]²₋₂", [4.35, 0.35, 0], size=21),
            label("= 122/15", [4.35, -0.7, 0], GOLD, 30),
            label("≈ 8.13333", [4.35, -1.65, 0], GOLD, 28),
        )
        self.play(Transform(rects, area), Transform(panel, integral), run_time=3)
        self.wait(5)
