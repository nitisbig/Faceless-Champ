"""Seeded probability simulations, authored in native Manim without TeX."""

import math
from functools import lru_cache

import numpy as np
from manim import Circle, Dot, Line, Rectangle, Scene, Text, ValueTracker, VGroup, VMobject, config, linear

DURATION = 45.0
CYAN, GOLD, MINT, MUTED = "#55DDEB", "#FFD166", "#70E1B5", "#52616E"
SEED = 241021


@lru_cache(maxsize=512)
def text_template(value, color, size):
    return Text(value, font="DejaVu Sans", font_size=size, color=color)


def label(value, x, y, color=MUTED, size=22):
    return text_template(value, color, size).copy().move_to([x, y, 0])


def path(x, y, color=CYAN, width=3, opacity=1):
    return VMobject(stroke_color=color, stroke_width=width, stroke_opacity=opacity).set_points_as_corners(
        np.column_stack((x, y, np.zeros_like(x)))
    )


def smooth(value):
    u = np.clip(value, 0, 1)
    return float(u * u * (3 - 2 * u))


def wilson(successes, count):
    """Two-sided 95% Wilson score interval for the Bernoulli parameter."""
    z = 1.959963984540054
    p = successes / count
    denominator = 1 + z * z / count
    center = (p + z * z / (2 * count)) / denominator
    half = z * math.sqrt(p * (1 - p) / count + z * z / (4 * count**2)) / denominator
    return center - half, center + half


class ProbabilitySimulations(Scene):
    def construct(self):
        config.background_color = "#000000"
        rng = np.random.default_rng(SEED)
        samples = rng.uniform(size=(1200, 24))
        means = (samples.mean(axis=1) - 0.5) * math.sqrt(12 * 24)
        points = rng.uniform(-1, 1, (640, 2))
        inside = np.sum(points**2, axis=1) <= 1
        cloud = [
            Dot([-2.9 + point[0] * 2.65, point[1] * 2.65, 0], radius=0.027, color=CYAN if hit else MUTED)
            for point, hit in zip(points, inside)
        ]
        tosses = rng.random(240) < 0.65
        clock = ValueTracker(0)
        graphics = VGroup()

        def gaussian(time):
            count = min(1200, max(80, int(1200 * smooth((time - 0.8) / 14.0))))
            items = VGroup()
            baseline, scale = -1.75, 6.5
            edges = np.linspace(-4, 4, 41)
            density = np.histogram(means[:count], bins=edges)[0] / (count * 0.2)
            items.add(Line([-5.7, baseline, 0], [5.7, baseline, 0], color=MUTED, stroke_width=1))
            for left, height in zip(edges[:-1], density):
                # Fixed density units: the histogram converges without arbitrary rescaling.
                height = float(height * scale)
                if height > 0:
                    items.add(
                        Rectangle(
                            width=0.252, height=height, stroke_width=0, fill_color=CYAN, fill_opacity=0.65
                        ).move_to([(left + 0.1) * 1.35, baseline + height / 2, 0])
                    )
            z = np.linspace(-4, 4, 241)
            items.add(path(z * 1.35, baseline + scale * np.exp(-(z**2) / 2) / math.sqrt(2 * math.pi), GOLD))
            for tick in (-3, 0, 3):
                items.add(label(str(tick), tick * 1.35, -2.05, size=18))
            items.add(label("z", 5.85, -1.75), label(f"N = {count}", 4.8, 3.15, CYAN))
            # A fresh row of 24 uniform draws links to its standardized sample mean.
            batch = samples[count - 1]
            items.add(Line([-5.4, 2.7, 0], [5.4, 2.7, 0], color=MUTED, stroke_width=1))
            for value in batch:
                items.add(Dot([-5.4 + 10.8 * value, 2.7, 0], color=CYAN, radius=0.035))
            items.add(label("n = 24", -5.0, 3.15, size=20))
            x = means[count - 1] * 1.35
            items.add(Dot([x, baseline - 0.04, 0], color="WHITE", radius=0.07))
            items.add(Line([x, baseline - 0.18, 0], [x, -2.65, 0], color=CYAN, stroke_width=1.3))
            items.add(label("z = (x̄ − μ) / (σ / √n)", 0, -3.1, GOLD, 25))
            return items

        def monte_carlo(time):
            count = min(640, max(1, int(640 * smooth(time / 10.3))))
            items = VGroup()
            center, radius = np.array([-2.9, 0, 0]), 2.65
            items.add(Rectangle(width=5.3, height=5.3, color=MUTED, stroke_width=1).move_to(center))
            items.add(Circle(radius=radius, color=GOLD, stroke_width=2).move_to(center))
            for dot in cloud[:count]:
                items.add(dot.set_opacity(1))
            estimate = 4 * inside[:count].mean()
            items.add(label("π ≈ 4 ×", 3.25, 2.4, GOLD, 30))
            items.add(label(f"{int(inside[:count].sum())} / {count}", 3.25, 1.65, CYAN, 28))
            items.add(label(f"{estimate:.4f}", 3.25, 0.65, "WHITE", 42))
            # Running estimate converges toward the faint true-pi reference.
            ns = np.arange(1, count + 1)
            estimates = 4 * np.cumsum(inside[:count]) / ns
            xs = 0.7 + ns / 640 * 5.3
            ys = -2.5 + (estimates - 2.4) * 1.25
            items.add(Line([0.7, -2.5, 0], [6, -2.5, 0], color=MUTED, stroke_width=1))
            items.add(Line([0.7, -1.573, 0], [6, -1.573, 0], color=GOLD, stroke_width=1, stroke_opacity=0.5))
            if count > 1:
                items.add(path(xs, ys, CYAN, 2))
            items.add(label("N", 6.2, -2.5), label("π", 0.4, -1.573, GOLD))
            return items

        def bayesian(time):
            count = min(240, max(0, int(240 * smooth((time - 1.0) / 12.7))))
            successes = int(tosses[:count].sum())
            failures = count - successes
            p = np.linspace(0.001, 0.999, 401)
            # Uniform Beta(1,1) prior and exact conjugate Beta(s+1,f+1) posterior.
            log_density = (
                successes * np.log(p)
                + failures * np.log1p(-p)
                + math.lgamma(count + 2)
                - math.lgamma(successes + 1)
                - math.lgamma(failures + 1)
            )
            density = np.exp(log_density)
            baseline = -0.9
            items = VGroup(Line([-5.5, baseline, 0], [5.5, baseline, 0], color=MUTED, stroke_width=1))
            # All posteriors share one vertical scale; a concentration becomes taller.
            items.add(path(p * 11 - 5.5, baseline + density * 0.22, CYAN, 3.5))
            items.add(Line([-5.5, baseline + 0.22, 0], [5.5, baseline + 0.22, 0], color=MUTED, stroke_width=1))
            true_x = -5.5 + 11 * 0.65
            items.add(Line([true_x, -3.05, 0], [true_x, 2.95, 0], color=GOLD, stroke_width=1, stroke_opacity=0.45))
            items.add(label("p = 0.65", true_x, 3.3, GOLD, 20))
            items.add(label(f"{successes} / {count}", -4.35, 3.3, CYAN, 25))
            # Recent binary observations: cyan successes, dim failures.
            for index, success in enumerate(tosses[max(0, count - 36) : count]):
                items.add(Dot([-5.25 + index * 0.30, 2.7, 0], radius=0.055, color=CYAN if success else MUTED))
            for tick in (0, 0.5, 1):
                items.add(label(f"{tick:g}", tick * 11 - 5.5, -1.2, size=18))
            items.add(label("p", 5.85, -0.9, size=22))
            if count:
                lo, hi = wilson(successes, count)
                left, right = lo * 11 - 5.5, hi * 11 - 5.5
                y = -2.35
                items.add(Line([left, y, 0], [right, y, 0], color=MINT, stroke_width=5))
                for x in (left, right):
                    items.add(Line([x, y - 0.12, 0], [x, y + 0.12, 0], color=MINT, stroke_width=2))
                items.add(Dot([-5.5 + 11 * successes / count, y, 0], radius=0.065, color="WHITE"))
                items.add(label("95% CI", -4.5, -3.1, MINT, 21))
                items.add(label(f"[{lo:.3f}, {hi:.3f}]", 0, -3.1, MINT, 22))
            return items

        def update(mob):
            time = clock.get_value()
            if time < 17:
                items = gaussian(time)
                opacity = smooth(time / 0.65) * (1 - smooth((time - 16.3) / 0.7))
            elif time < 29:
                items = monte_carlo(time - 17)
                opacity = smooth((time - 17) / 0.65) * (1 - smooth((time - 28.3) / 0.7))
            else:
                items = bayesian(time - 29)
                opacity = smooth((time - 29) / 0.65)
            # Replace the group directly; become() aligns growing dot families.
            mob.remove(*mob.submobjects)
            mob.add(*items.submobjects)
            mob.fade(1 - opacity)

        graphics.add_updater(update)
        self.add(graphics)
        self.play(clock.animate.set_value(DURATION), run_time=DURATION, rate_func=linear)
        graphics.clear_updaters()
