"""Deterministic Fourier synthesis, epicycles and filtering; no TeX required."""

import numpy as np
from manim import Circle, Dot, Line, Scene, Text, ValueTracker, VGroup, VMobject, config, linear

DURATION = 45.0
FREQUENCIES = np.array([1, 2, 3, 5, 7])
AMPLITUDES = np.array([1.0, 0.42, 0.30, 0.20, 0.13])
PHASES = np.array([0.0, 0.7, -0.45, 1.0, -0.6])
COLORS = ("#55DDEB", "#FFD166", "#F783AC", "#A699FF", "#70E1B5")
MUTED = "#536471"
SCALE = 1.2
PERIOD = 6.0
ORIGIN = np.array([-4.0, 0.9, 0.0])
WAVE_X = 0.0
WAVE_WIDTH = 6.15
HISTORY = 12.0


def smooth(start, end, time):
    u = np.clip((np.asarray(time) - start) / (end - start), 0, 1)
    return u * u * (3 - 2 * u)


def gains(time):
    """Same absolute-time envelope for vectors, signal history and spectrum."""
    time = np.asarray(time)
    entry = np.stack(
        [np.ones_like(time), smooth(9, 12, time), smooth(12, 15, time), smooth(16, 19, time), smooth(19, 22, time)],
        axis=-1,
    )
    high_pass = 1 - smooth(30, 34, time) + smooth(38, 42, time)
    entry[..., 2:] *= high_pass[..., None]
    return entry


def components(time):
    angle = 2 * np.pi * np.asarray(time)[..., None] * FREQUENCIES / PERIOD + PHASES
    return SCALE * AMPLITUDES * gains(time) * np.exp(1j * angle)


def signal(time):
    return components(time).sum(axis=-1).imag


def label(content, position, color=MUTED, size=22):
    return Text(content, font="DejaVu Sans", font_size=size, color=color).move_to(position)


def path(points, color, width=3, opacity=1):
    return VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity).set_points_as_corners(points)


class FourierSignal(Scene):
    def construct(self):
        config.background_color = "#000000"
        clock = ValueTracker(0)
        axes = VGroup(
            Line([-6.55, 0.9, 0], [-1.45, 0.9, 0], color=MUTED, stroke_width=1),
            Line([-4, -1.65, 0], [-4, 3.45, 0], color=MUTED, stroke_width=1),
            Line([WAVE_X, 0.9, 0], [6.35, 0.9, 0], color=MUTED, stroke_width=1),
            Line([WAVE_X, -1.55, 0], [WAVE_X, 3.35, 0], color=MUTED, stroke_width=1),
            Line([-5.9, -3.25, 0], [6.05, -3.25, 0], color=MUTED, stroke_width=1.5),
            Line([-5.9, -3.25, 0], [-5.9, -1.95, 0], color=MUTED, stroke_width=1.5),
            label("Re", [-1.35, 0.63, 0], size=18),
            label("Im", [-4.3, 3.44, 0], size=18),
            label("t", [6.4, 0.65, 0]),
            label("f", [6.25, -3.25, 0]),
            label("|X(f)|", [-5.85, -1.75, 0], size=20),
        )
        # A one-sided amplitude spectrum: each spike is the sinusoid amplitude.
        bins = -5.15 + (FREQUENCIES - 1) * 1.62
        for x, frequency, color in zip(bins, FREQUENCIES, COLORS):
            axes.add(label(str(frequency), [x, -3.58, 0], color, 19))
        self.add(axes)
        dynamic = VGroup()

        def update(mob):
            time = clock.get_value()
            weights = gains(time)
            vectors = components(time)
            items = VGroup()
            center = ORIGIN.copy()
            for value, amplitude, weight, color in zip(vectors, AMPLITUDES, weights, COLORS):
                radius = SCALE * amplitude * weight
                if radius < 0.002:
                    continue
                endpoint = center + [value.real, value.imag, 0]
                items.add(Circle(radius=radius, color=color, stroke_width=1.25, stroke_opacity=0.36).move_to(center))
                items.add(Line(center, endpoint, color=color, stroke_width=3))
                # A small arrowhead preserves the vector direction at every scale.
                direction = (endpoint - center) / radius
                perpendicular = np.array([-direction[1], direction[0], 0])
                tip_size = min(0.10, radius * 0.3)
                for side in (-1, 1):
                    items.add(
                        Line(
                            endpoint,
                            endpoint - tip_size * direction + side * tip_size * 0.45 * perpendicular,
                            color=color,
                            stroke_width=2,
                        )
                    )
                center = endpoint
            items.add(Dot(center, color="WHITE", radius=0.055))
            # Current sample is at the left; twelve seconds of actual history flow right.
            ages = np.linspace(0, min(time, HISTORY), max(2, int(min(time, HISTORY) * 42) + 1))
            points = np.column_stack(
                (WAVE_X + ages / HISTORY * WAVE_WIDTH, 0.9 + signal(time - ages), np.zeros_like(ages))
            )
            if time > 0:
                items.add(path(points, COLORS[0], 3.5))
            sample = np.array([WAVE_X, center[1], 0])
            items.add(Line(center, sample, color="WHITE", stroke_width=1.2, stroke_opacity=0.45))
            items.add(Dot(sample, color="WHITE", radius=0.055))
            # Faint complete signal provides a visual comparison during filtering.
            ages_reference = np.linspace(0, HISTORY, 400)
            angles = 2 * np.pi * (time - ages_reference[:, None]) * FREQUENCIES / PERIOD + PHASES
            reference = SCALE * (AMPLITUDES * np.sin(angles)).sum(axis=-1)
            items.add(
                path(
                    np.column_stack(
                        (WAVE_X + ages_reference / HISTORY * WAVE_WIDTH, 0.9 + reference, np.zeros_like(reference))
                    ),
                    "#81929F",
                    1,
                    0.25,
                )
            )
            for x, amplitude, weight, color in zip(bins, AMPLITUDES, weights, COLORS):
                bottom = [x, -3.25, 0]
                top = [x, -3.25 + amplitude * weight * 1.10, 0]
                if weight > 0.002:
                    items.add(Line(bottom, top, color=color, stroke_width=5), Dot(top, color=color, radius=0.045))
            mob.become(items)
            mob.fade(1 - float(smooth(0, 1.5, time)))

        dynamic.add_updater(update)
        self.add(dynamic)
        self.play(clock.animate.set_value(DURATION), run_time=DURATION, rate_func=linear)
        dynamic.clear_updaters()
