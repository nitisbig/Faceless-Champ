"""A 45-second saddle, partial derivatives, tangent plane and gradient study."""

import numpy as np
from manim import (
    DEGREES,
    Cone,
    Create,
    DashedLine,
    Dot3D,
    FadeIn,
    FadeOut,
    Line3D,
    ParametricFunction,
    Surface,
    Text,
    ThreeDAxes,
    ThreeDScene,
    ValueTracker,
    VGroup,
    always_redraw,
    config,
    linear,
)

DURATION = 45.0
CYAN, GOLD, PINK, GREEN = "#55DDEB", "#FFD166", "#F783AC", "#76E6BA"
MUTED = "#637587"


def f(x, y):
    return 0.38 * (x * x - y * y)


def gradient(x, y):
    return np.array([0.76 * x, -0.76 * y])


def tangent_z(x, y, u, v):
    return f(x, y) + np.dot(gradient(x, y), [u, v])


class SaddleSurfaces(ThreeDScene):
    def construct(self):
        config.background_color = "#000000"
        resolution = int(getattr(self, "faceless_parameters", {}).get("surface_resolution", 24))
        self.set_camera_orientation(phi=66 * DEGREES, theta=-54 * DEGREES, zoom=0.83)
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-2.8, 2.8, 1],
            x_length=6,
            y_length=6,
            z_length=5.6,
            axis_config={"color": MUTED, "stroke_width": 1.4, "include_ticks": False},
        )
        surface = Surface(
            lambda u, v: axes.c2p(u, v, f(u, v)),
            u_range=[-2.4, 2.4],
            v_range=[-2.4, 2.4],
            resolution=(resolution, resolution),
            checkerboard_colors=["#124C68", "#19647C"],
            fill_opacity=0.66,
            stroke_color=CYAN,
            stroke_width=0.35,
            stroke_opacity=0.35,
        )
        formula = Text("f(x, y) = 0.38(x² − y²)", font="DejaVu Sans", font_size=25, color=CYAN)
        formula.to_corner(np.array([-1, 1, 0]), buff=0.45)
        self.add_fixed_in_frame_mobjects(formula)
        self.remove(formula)
        axis_labels = VGroup(
            *[
                Text(letter, font_size=21, color=MUTED).move_to(axes.c2p(*point))
                for letter, point in (("x", (3.25, 0, 0)), ("y", (0, 3.25, 0)), ("z", (0, 0, 3.0)))
            ]
        )
        self.add_fixed_orientation_mobjects(*axis_labels)
        self.remove(*axis_labels)
        self.play(Create(axes), FadeIn(surface), FadeIn(formula), FadeIn(axis_labels), run_time=3)
        self.move_camera(theta=-24 * DEGREES, run_time=5)

        x, y = ValueTracker(0.95), ValueTracker(0.7)
        self.add(x, y)

        def point():
            return axes.c2p(x.get_value(), y.get_value(), f(x.get_value(), y.get_value()))

        def arrow(start, end, color):
            # Explicit low-detail meshes avoid Arrow3D's dense default cone on
            # every updater tick while retaining a true volumetric 3D vector.
            direction = (end - start) / np.linalg.norm(end - start)
            shaft = Line3D(start, end - 0.16 * direction, thickness=0.017, color=color, resolution=(2, 8))
            tip = Cone(
                direction=direction,
                height=0.16,
                base_radius=0.06,
                resolution=(2, 8),
                fill_color=color,
                fill_opacity=1,
                stroke_width=0,
            ).shift(end)
            return VGroup(shaft, tip)

        dot = always_redraw(lambda: Dot3D(point(), radius=0.075, color="WHITE", resolution=(8, 8)))
        x_slice = always_redraw(
            lambda: ParametricFunction(
                lambda u: axes.c2p(u, y.get_value(), f(u, y.get_value())),
                t_range=[-2.4, 2.4, 0.06],
                color=GOLD,
                stroke_width=4,
            )
        )
        y_slice = always_redraw(
            lambda: ParametricFunction(
                lambda v: axes.c2p(x.get_value(), v, f(x.get_value(), v)),
                t_range=[-2.4, 2.4, 0.06],
                color=PINK,
                stroke_width=4,
            )
        )

        def partial_vector(axis, color):
            gx, gy = gradient(x.get_value(), y.get_value())
            direction = np.array([1, 0, gx]) if axis == 0 else np.array([0, 1, gy])
            return arrow(point(), point() + 1.15 * direction, color)

        tx = always_redraw(lambda: partial_vector(0, GOLD))
        ty = always_redraw(lambda: partial_vector(1, PINK))

        def caption(text, color, horizontal):
            return Text(text, font="DejaVu Sans", font_size=23, color=color).move_to([horizontal, -3.35, 0])

        fx = caption("∂f/∂x = 0.76x", GOLD, -3.25)
        fy = caption("∂f/∂y = −0.76y", PINK, 3.25)
        self.add_fixed_in_frame_mobjects(fx, fy)
        self.remove(fx, fy)
        self.play(FadeIn(dot), Create(x_slice), FadeIn(tx), FadeIn(fx), run_time=2)
        self.move_camera(theta=-5 * DEGREES, run_time=4)
        self.play(Create(y_slice), FadeIn(ty), FadeIn(fy), run_time=2)
        self.move_camera(theta=20 * DEGREES, phi=60 * DEGREES, run_time=4)

        plane = always_redraw(
            lambda: Surface(
                lambda u, v: axes.c2p(
                    x.get_value() + u, y.get_value() + v, tangent_z(x.get_value(), y.get_value(), u, v)
                ),
                u_range=[-0.8, 0.8],
                v_range=[-0.8, 0.8],
                resolution=(4, 4),
                checkerboard_colors=[GREEN, GREEN],
                fill_opacity=0.32,
                stroke_color=GREEN,
                stroke_width=0.7,
            )
        )

        def normal_arrow():
            gx, gy = gradient(x.get_value(), y.get_value())
            normal = np.array([-gx, -gy, 1.0])
            return arrow(point(), point() + 1.4 * normal / np.linalg.norm(normal), GREEN)

        normal = always_redraw(normal_arrow)
        self.play(FadeIn(plane), FadeIn(normal), surface.animate.set_opacity(0.24), run_time=3)
        self.move_camera(theta=48 * DEGREES, run_time=4)

        # The gradient lives in the domain; place it on a separate xy reference plane.
        floor_z = -2.65
        floor = VGroup(
            *[
                DashedLine(axes.c2p(*a), axes.c2p(*b), color=MUTED, stroke_width=1)
                for a, b in (((-2.5, 0, floor_z), (2.5, 0, floor_z)), ((0, -2.5, floor_z), (0, 2.5, floor_z)))
            ]
        )
        projection = always_redraw(
            lambda: DashedLine(
                point(),
                axes.c2p(x.get_value(), y.get_value(), floor_z),
                color=MUTED,
                stroke_width=1.4,
            )
        )

        def gradient_arrow():
            gx, gy = gradient(x.get_value(), y.get_value())
            return arrow(
                axes.c2p(x.get_value(), y.get_value(), floor_z),
                axes.c2p(x.get_value() + gx, y.get_value() + gy, floor_z),
                CYAN,
            )

        grad = always_redraw(gradient_arrow)
        grad_text = caption("∇f = (0.76x, −0.76y)", CYAN, 0)
        self.add_fixed_in_frame_mobjects(grad_text)
        self.remove(grad_text)
        self.play(
            FadeOut(fx), FadeOut(fy), FadeIn(grad_text), FadeIn(floor), FadeIn(projection), FadeIn(grad), run_time=2
        )
        # Follow one closed ellipse on the surface while keeping all local geometry live.
        angle = ValueTracker(np.arctan2(0.7 / 0.9, 0.95 / 1.2))
        radius_x = 0.95 / np.cos(angle.get_value())
        radius_y = 0.7 / np.sin(angle.get_value())
        x.add_updater(lambda m: m.set_value(radius_x * np.cos(angle.get_value())))
        y.add_updater(lambda m: m.set_value(radius_y * np.sin(angle.get_value())))
        self.begin_ambient_camera_rotation(rate=0.10)
        self.play(angle.animate.increment_value(2 * np.pi), run_time=7, rate_func=linear)
        x.clear_updaters()
        y.clear_updaters()
        self.stop_ambient_camera_rotation()
        self.play(
            FadeOut(x_slice),
            FadeOut(y_slice),
            FadeOut(tx),
            FadeOut(ty),
            FadeOut(grad),
            FadeOut(projection),
            FadeOut(floor),
            FadeOut(grad_text),
            run_time=2,
        )
        for mob in (x_slice, y_slice, tx, ty, grad, projection):
            mob.clear_updaters()
        self.play(x.animate.set_value(0), y.animate.set_value(0), run_time=4)
        stationary = caption("∇f(0, 0) = (0, 0)", CYAN, 0)
        self.add_fixed_in_frame_mobjects(stationary)
        self.move_camera(theta=110 * DEGREES, phi=68 * DEGREES, run_time=3)
