"""A real 3–4–3–1 network: forward pass, chain rule, and gradient descent."""

from fractions import Fraction
from itertools import pairwise

import numpy as np
from manim import (
    Axes,
    Circle,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    MoveAlongPath,
    Scene,
    Text,
    Transform,
    ValueTracker,
    VGroup,
    Wait,
    always_redraw,
    config,
    linear,
)

DURATION = 45.0
CYAN, PINK, GOLD = "#55DDEB", "#F783AC", "#FFD166"
MUTED = "#455767"
X = np.array([0.8, -0.4, 0.6])
TARGET = 0.8
RATE = 0.12


def initial_parameters():
    rng = np.random.default_rng(8)
    weights = [rng.normal(0, 0.55, (b, a)) for a, b in zip((3, 4, 3), (4, 3, 1))]
    return weights, [np.zeros(n) for n in (4, 3, 1)]


def evaluate(weights, biases):
    activations = [X.copy()]
    for i, (weight, bias) in enumerate(zip(weights, biases)):
        z = weight @ activations[-1] + bias
        activations.append(np.tanh(z) if i < 2 else z)
    error = activations[-1][0] - TARGET
    delta = np.array([error])
    gradients, deltas = [None] * 3, [None] * 3
    for i in reversed(range(3)):
        deltas[i] = delta.copy()
        gradients[i] = np.outer(delta, activations[i])
        if i:
            delta = (weights[i].T @ delta) * (1 - activations[i] ** 2)
    return activations, 0.5 * error**2, gradients, deltas


def training_states(steps=20):
    weights, biases = initial_parameters()
    states = []
    for step in range(steps + 1):
        activations, loss, gradients, deltas = evaluate(weights, biases)
        states.append((step, [w.copy() for w in weights], activations, loss))
        weights = [w - RATE * g for w, g in zip(weights, gradients)]
        biases = [b - RATE * d for b, d in zip(biases, deltas)]
    return states


def text(value, x, y, color="WHITE", size=25):
    return Text(value, font="DejaVu Sans", font_size=size, color=color).move_to([x, y, 0])


def matrix(values, x, y, color=CYAN):
    values = np.atleast_2d(values)
    rows, cols = values.shape
    cells = VGroup(
        *[
            text(f"{values[r, c]:+.2f}", x + (c - (cols - 1) / 2) * 0.95, y + ((rows - 1) / 2 - r) * 0.43, color, 20)
            for r in range(rows)
            for c in range(cols)
        ]
    )
    half_w, half_h = cols * 0.95 / 2 + 0.1, rows * 0.43 / 2 + 0.08
    brackets = VGroup()
    for sign in (-1, 1):
        side = x + sign * half_w
        brackets.add(Line([side, y - half_h, 0], [side, y + half_h, 0], color=MUTED))
        for yy in (y - half_h, y + half_h):
            brackets.add(Line([side, yy, 0], [side - sign * 0.13, yy, 0], color=MUTED))
    return VGroup(cells, brackets)


class NeuralBackpropagation(Scene):
    def play_for(self, *animations, run_time=1, **kwargs):
        """Round cumulative cue boundaries, rather than each individual beat."""
        elapsed = getattr(self, "_cue_time", Fraction(0))
        target = elapsed + Fraction(str(run_time))
        fps = Fraction(str(config.frame_rate))
        frames = round(target * fps) - round(elapsed * fps)
        if frames < 1:
            raise ValueError("Scene frame rate is too low for this beat")
        self._cue_time = target
        # Manim samples with np.arange; stay just below the exclusive end to
        # prevent floating-point division from adding a spurious final frame.
        duration = np.nextafter(float(frames / fps), 0.0)
        self.play(*animations, run_time=duration, **kwargs)

    def hold_for(self, seconds):
        # Use the same frame sampling as animations, including static holds.
        self.play_for(Wait(frozen_frame=False), run_time=seconds)

    def construct(self):
        config.background_color = "#000000"
        weights, biases = initial_parameters()
        activations, loss, gradients, _deltas = evaluate(weights, biases)
        layers = VGroup(
            *[
                VGroup(
                    *[
                        Circle(radius=0.21, color=CYAN, stroke_width=2.3, fill_color="#000000", fill_opacity=1).move_to(
                            [x, 1.35 + (n - 1) * 0.42 - j * 0.84, 0]
                        )
                        for j in range(n)
                    ]
                )
                for x, n in zip((-4.8, -1.6, 1.6, 4.8), (3, 4, 3, 1))
            ]
        )
        edges = VGroup()
        for i, weight in enumerate(weights):
            group = VGroup()
            for row in range(weight.shape[0]):
                for col in range(weight.shape[1]):
                    a, b = layers[i][col].get_center(), layers[i + 1][row].get_center()
                    unit = (b - a) / np.linalg.norm(b - a)
                    group.add(
                        Line(
                            a + unit * 0.23,
                            b - unit * 0.23,
                            color=CYAN if weight[row, col] >= 0 else PINK,
                            stroke_width=1 + 2 * abs(weight[row, col]),
                            stroke_opacity=0.55,
                        )
                    )
            edges.add(group)
        names = VGroup(
            *[text(name, x, 3.15, CYAN, 24) for name, x in zip(("x", "a₁", "a₂", "ŷ"), (-4.8, -1.6, 1.6, 4.8))]
        )
        self.play_for(Create(edges), FadeIn(layers), FadeIn(names), run_time=3)

        def light(layer, values):
            return [
                node.animate.set_fill(CYAN if value >= 0 else PINK, opacity=0.15 + 0.75 * min(abs(value), 1))
                for node, value in zip(layer, values)
            ]

        def pulses(index, backwards=False):
            packets = VGroup()
            animations = []
            for k, edge in enumerate(edges[index]):
                magnitude = abs(gradients[index].flat[k]) if backwards else 0.2
                dot = Dot(radius=0.035 + min(magnitude, 0.5) * 0.06, color=GOLD if backwards else CYAN)
                path = Line(edge.get_end(), edge.get_start()) if backwards else edge
                dot.move_to(path.get_start())
                packets.add(dot)
                animations.append(MoveAlongPath(dot, path, rate_func=linear))
            self.add(packets)
            self.play_for(*animations, run_time=1.25 if backwards else 1)
            self.remove(packets)

        self.play_for(*light(layers[0], activations[0]), run_time=0.5)
        for i in range(3):
            pulses(i)
            self.play_for(*light(layers[i + 1], activations[i + 1]), run_time=0.5)
        # 8s: explicit first-layer matrix product, with zero initial bias.
        product = VGroup(
            matrix(weights[0], -3.9, -2.0),
            text("×", -1.8, -2),
            matrix(X[:, None], -0.65, -2),
            text("=", 0.5, -2),
            matrix((weights[0] @ X)[:, None], 1.7, -2, GOLD),
            text("z₁ = W₁x + b₁", 4.3, -1.6, size=25),
            text("b₁ = 0", 4.3, -2.4, MUTED, 23),
        )
        self.play_for(FadeIn(product), run_time=2)
        for row in range(4):
            self.play_for(
                product[0][0][row * 3 : (row + 1) * 3].animate.set_color(GOLD),
                layers[1][row].animate.set_stroke(GOLD, width=4),
                run_time=0.5,
            )
            self.play_for(
                product[0][0][row * 3 : (row + 1) * 3].animate.set_color(CYAN),
                layers[1][row].animate.set_stroke(CYAN, width=2.3),
                run_time=0.75,
            )
        self.hold_for(2)
        # 17s: tanh and its local derivative, used below in the chain rule.
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-1.2, 1.2, 1],
            x_length=5,
            y_length=2.1,
            tips=False,
            axis_config={"color": MUTED, "include_ticks": False},
        )
        axes.move_to([-2.8, -2.05, 0])
        curve = axes.plot(np.tanh, x_range=[-3, 3], color=CYAN)
        z = ValueTracker(-2.6)
        marker = always_redraw(lambda: Dot(axes.c2p(z.get_value(), np.tanh(z.get_value())), color=GOLD, radius=0.075))
        activation = VGroup(
            axes, curve, text("a = tanh(z)", 3.05, -1.5, CYAN, 30), text("da/dz = 1 − a²", 3.05, -2.4, GOLD, 27)
        )
        self.play_for(FadeOut(product), FadeIn(activation), FadeIn(marker), run_time=1)
        self.play_for(z.animate.set_value(2.6), run_time=4, rate_func=linear)
        self.hold_for(1)
        # 23s: loss seed, then gradients move in the reverse layer order.
        rule = VGroup(
            text("L = ½(ŷ − y)²", -3.6, -1.65, GOLD, 29),
            text("y = 0.80", -3.6, -2.5, size=24),
            text("δₗ = (Wₗ₊₁ᵀδₗ₊₁) ⊙ (1 − aₗ²)", 2.4, -1.65, GOLD, 27),
            text("∂L/∂Wₗ = δₗ aₗ₋₁ᵀ", 2.4, -2.5, CYAN, 27),
        )
        self.play_for(FadeOut(activation), FadeOut(marker), FadeIn(rule), run_time=1)
        marker.clear_updaters()
        for i in reversed(range(3)):
            pulses(i, backwards=True)
            self.play_for(*[node.animate.set_stroke(GOLD, width=3.5) for node in layers[i]], run_time=0.75)
        update = text("W ← W − η ∂L/∂W     b ← b − ηδ     η = 0.12", 0, -3.3, GOLD, 25)
        self.play_for(FadeIn(update), run_time=2)
        # 32s: all weights and biases train on the displayed example.
        states = training_states()
        loss_axes = Axes(
            x_range=[0, 20, 5],
            y_range=[0, loss * 1.15, loss / 2],
            x_length=5.5,
            y_length=2,
            tips=False,
            axis_config={"color": MUTED, "include_ticks": False},
        ).move_to([-3, -2, 0])

        def stats(state):
            step, w, a, value = state
            return VGroup(
                text(f"k = {step:02d}     L = {value:.5f}", 3.25, -1.3, GOLD, 25),
                text(f"ŷ = {a[-1][0]:.3f}     y = 0.800", 3.25, -2.05, CYAN, 25),
                text(f"w₁₁ = {w[0][0, 0]:+.3f}", 3.25, -2.8, size=25),
            )

        panel = stats(states[0])
        axis_labels = VGroup(text("L", -6.05, -1.0, GOLD, 22), text("k", -0.05, -3.0, size=22))
        self.play_for(FadeOut(rule), FadeIn(loss_axes), FadeIn(panel), FadeIn(axis_labels), run_time=1)
        trail = VGroup()
        self.add(trail)
        for previous, state in pairwise(states):
            segment = Line(
                loss_axes.c2p(previous[0], previous[3]), loss_axes.c2p(state[0], state[3]), color=GOLD, stroke_width=3
            )
            animations = [Create(segment), Transform(panel, stats(state))]
            for i, weight in enumerate(state[1]):
                for k, value in enumerate(weight.flat):
                    animations.append(
                        edges[i][k].animate.set_stroke(
                            CYAN if value >= 0 else PINK, width=1 + 2 * abs(value), opacity=0.65
                        )
                    )
            for layer, values in zip(layers, state[2]):
                animations.extend(light(layer, values))
            self.play_for(*animations, run_time=0.5, rate_func=linear)
            trail.add(segment)
        self.hold_for(2)
