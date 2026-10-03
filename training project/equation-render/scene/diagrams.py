"""Diagrams whose colored quantities match the symbols in their equations."""

import math
from dataclasses import dataclass, field
from itertools import pairwise

from faceless_champ import Animation, Arrow, Circle, Polyline, Rectangle, with_alpha

from .style import DEFAULT_SCHEME, equation, text


@dataclass
class Diagram:
    guides: list = field(default_factory=list)
    paths: list = field(default_factory=list)
    marks: list = field(default_factory=list)
    motions: list = field(default_factory=list)


def make_diagram(spec, *, tall=False, scheme=DEFAULT_SCHEME):
    d = Diagram()
    ox, oy, w, h = (74, 450, 730, 185) if tall else (602, 125, 224, 115)
    color = spec.accent(scheme)

    def p(u, v):
        return (ox + u * w, oy + v * h)

    def path(points, *, stroke=color, width=3.5, **kwargs):
        return Polyline([p(u, v) for u, v in points], stroke=stroke, stroke_width=width, line_cap="round", **kwargs)

    def label(words, u, v, *, color=None):
        return text(words, p(u, v), size=23 if tall else 18, color=color or scheme.muted, body=True)

    def dot(u, v, radius=5.5, *, color=None):
        return Circle(radius, position=p(u, v), fill=color or spec.accent(scheme), stroke=None)

    def axes():
        d.guides.extend(
            (
                path([(0, 0.94), (1, 0.94)], stroke=scheme.axis, width=1.6),
                path([(0, 0.94), (0, 0.04)], stroke=scheme.axis, width=1.6),
            )
        )

    if spec.diagram == "triangle":
        d.paths.extend(
            (
                path([(0.14, 0.95), (0.78, 0.95)], stroke=scheme.primary),
                path([(0.14, 0.95), (0.14, 0.02)], stroke=scheme.secondary),
                path([(0.14, 0.02), (0.78, 0.95)], stroke=scheme.tertiary),
            )
        )
        d.guides.append(path([(0.14, 0.76), (0.24, 0.76), (0.24, 0.95)], stroke=scheme.axis, width=1.5))
        d.marks.extend(
            (
                label("a = 4", 0.46, 1.12, color=scheme.primary),
                label("b = 3", -0.02, 0.45, color=scheme.secondary),
                label("c = 5", 0.55, 0.40, color=scheme.tertiary),
            )
        )
    elif spec.diagram == "quadratic":
        d.guides.append(path([(0, 0.75), (1, 0.75)], stroke=scheme.axis, width=1.6))
        points = [(i / 60, 0.75 - (1 + 3 * i / 60 - 2) * (1 + 3 * i / 60 - 3) * 0.22) for i in range(61)]
        d.paths.append(path(points, stroke=scheme.primary))
        d.marks.extend(
            (
                dot(1 / 3, 0.75),
                dot(2 / 3, 0.75),
                label("2", 1 / 3, 1.06, color=scheme.highlight),
                label("3", 2 / 3, 1.06, color=scheme.highlight),
            )
        )
    elif spec.diagram == "slope":
        axes()
        d.guides.extend(
            (
                path([(0.12, 0.85), (0.87, 0.85)], stroke=scheme.primary, width=2),
                path([(0.87, 0.85), (0.87, 0.1)], stroke=scheme.secondary, width=2),
            )
        )
        d.paths.append(path([(0.12, 0.85), (0.87, 0.1)], stroke=scheme.tertiary))
        d.marks.extend(
            (
                dot(0.12, 0.85, color=scheme.tertiary),
                dot(0.87, 0.1, color=scheme.tertiary),
                label("run: 2", 0.50, 1.10, color=scheme.primary),
                label("rise: 4", 0.72, 0.56, color=scheme.secondary),
            )
        )
    elif spec.diagram == "growth":
        axes()
        points = [(i / 60, 0.88 - 0.76 * (1.05 ** (20 * i / 60) - 1) / (1.05**20 - 1)) for i in range(61)]
        d.paths.append(path(points))
        moving = dot(*points[0])
        d.marks.extend((moving, label("time →", 0.54, 1.10, color=scheme.highlight)))
        d.motions.append(
            Animation(
                moving,
                {"position": p(*points[-1])},
                keyframes={"position": tuple((i / 60, p(*xy)) for i, xy in enumerate(points))},
            )
        )
    elif spec.diagram == "derivative":
        axes()
        d.paths.append(path([(i / 60, 0.88 - 0.80 * (i / 60) ** 2) for i in range(61)], stroke=scheme.primary))
        d.paths.append(path([(0.23, 0.9472), (0.98, 0.2272)], stroke=scheme.secondary, width=2.8))
        d.marks.extend((dot(0.60, 0.592, color=scheme.tertiary), label("tangent", 0.46, 1.10, color=scheme.secondary)))
    elif spec.diagram == "integral":
        axes()
        d.guides.append(
            path(
                [(0.14, 0.84), (0.90, 0.20), (0.90, 0.94), (0.14, 0.94)],
                closed=True,
                fill=with_alpha(scheme.highlight, 0.18),
                stroke=None,
            )
        )
        d.paths.append(path([(0.14, 0.84), (0.90, 0.20)], stroke=scheme.primary))
        d.marks.extend(
            (
                label("a", 0.14, 1.10, color=scheme.secondary),
                label("b", 0.90, 1.10, color=scheme.tertiary),
                label("area", 0.63, 0.72, color=scheme.highlight),
            )
        )
    elif spec.diagram == "force":
        block = Rectangle(
            width=50, height=43, fill=scheme.secondary, stroke=None, corner_radius=7, position=p(0.20, 0.63)
        )
        mass = label("m", 0.20, 1.10, color=scheme.secondary)
        d.marks.extend((block, mass, label("F →", 0.73, 0.27, color=scheme.primary)))
        d.paths.append(Arrow(p(0.37, 0.63), p(0.94, 0.63), stroke=scheme.primary, stroke_width=3.5, tip_size=10))
        d.guides.append(path([(0, 0.88), (1, 0.88)], stroke=scheme.axis, width=1.6))
        d.motions.extend((block.animate.move_to(*p(0.48, 0.63)), mass.animate.move_to(*p(0.48, 1.10))))
    elif spec.diagram == "bayes":
        nodes = ((0.08, 0.62), (0.5, 0.20), (0.92, 0.62))
        d.paths.extend(
            Arrow(p(*a), p(*b), stroke=scheme.axis, stroke_width=2.3, tip_size=7) for a, b in pairwise(nodes)
        )
        d.marks.extend(dot(*node, radius=8, color=scheme.series(i)) for i, node in enumerate(nodes))
        d.marks.extend(
            (
                label("prior A", 0.08, 0.97, color=scheme.primary),
                label("given B", 0.5, -0.06, color=scheme.secondary),
                label("updated", 0.91, 0.97, color=scheme.tertiary),
            )
        )
    elif spec.diagram == "normal":

        def curve(x):
            return ((x + 3.2) / 6.4, 0.90 - 0.79 * math.exp(-x * x / 2))

        axes()
        shaded = [curve(-1 + i / 30) for i in range(61)]
        d.guides.append(
            path(
                [(shaded[0][0], 0.90), *shaded, (shaded[-1][0], 0.90)],
                closed=True,
                fill=with_alpha(scheme.tertiary, 0.18),
                stroke=None,
            )
        )
        for x in (-1, 0, 1):
            u, v = curve(x)
            for j in range(8):
                y = v + (0.90 - v) * j / 8
                d.guides.append(
                    path(
                        [(u, y), (u, min(0.90, y + 0.045))],
                        stroke=scheme.secondary if x == 0 else scheme.tertiary,
                        width=1.8,
                    )
                )
        d.paths.append(path([curve(-3.2 + i * 6.4 / 140) for i in range(141)], stroke=scheme.primary, width=4.2))
        d.marks.extend(
            (
                equation(r"\mu-\sigma", p(2.2 / 6.4, 1.10), size=27, scheme=scheme, color_map=spec.color_map(scheme)),
                equation(r"\mu", p(0.5, 1.10), size=27, scheme=scheme, color_map=spec.color_map(scheme)),
                equation(r"\mu+\sigma", p(4.2 / 6.4, 1.10), size=27, scheme=scheme, color_map=spec.color_map(scheme)),
                dot(0.5, 0.11, radius=7, color=scheme.secondary),
            )
        )
    elif spec.diagram == "fourier":
        d.guides.extend(
            (
                path([(0, 0.55), (0.40, 0.55)], stroke=scheme.axis, width=1.6),
                path([(0.62, 0.92), (1, 0.92)], stroke=scheme.axis, width=1.6),
            )
        )
        d.paths.append(
            path(
                [
                    (
                        i / 140 * 0.40,
                        0.55 - 0.24 * math.sin(math.tau * 3 * i / 140) - 0.08 * math.sin(math.tau * 7 * i / 140),
                    )
                    for i in range(141)
                ],
                width=3.5,
            )
        )
        d.paths.append(Arrow(p(0.45, 0.53), p(0.56, 0.53), stroke=scheme.muted, stroke_width=2, tip_size=9))
        for u, height in ((0.71, 0.61), (0.85, 0.22)):
            d.paths.append(path([(u, 0.92), (u, 0.92 - height)], stroke=scheme.secondary, width=12))
        d.marks.extend(
            (label("TIME", 0.20, 1.12, color=scheme.primary), label("FREQUENCY", 0.81, 1.12, color=scheme.secondary))
        )
    return d
