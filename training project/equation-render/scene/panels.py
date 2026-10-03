"""Each equation is an independent six-second Scene, held by its parent Grid."""

from faceless_champ import (
    Canvas,
    Draw,
    FadeIn,
    FadeOut,
    Icon,
    Line,
    PopIn,
    Pulse,
    Rectangle,
    Scene,
    SlideIn,
    Write,
    linear,
)

from .diagrams import make_diagram
from .style import ASSETS, DEFAULT_SCHEME, SFX, TRANSPARENT, equation, text

PANEL_DURATION = 6.2


class EquationPanel(Scene):
    def __init__(self, spec, *, tall=False, sound=True, scheme=DEFAULT_SCHEME):
        super().__init__(Canvas(879, 776 if tall else 377, TRANSPARENT))
        self.spec, self.tall, self.sound = spec, tall, sound
        self.scheme = scheme

    def construct(self):
        spec, tall = self.spec, self.tall
        scheme = self.scheme
        height, color = self.canvas.height, spec.accent(scheme)
        card = Rectangle(
            width=869,
            height=height - 10,
            corner_radius=20,
            fill=scheme.surface,
            stroke=scheme.border,
            stroke_width=1.5,
            position=(439.5, height / 2),
        )
        active = Rectangle(
            width=869, height=height - 10, corner_radius=20, stroke=color, stroke_width=2, position=(439.5, height / 2)
        )
        self.play(FadeIn(card), FadeIn(active), run_time=0.35)
        icon = Icon(ASSETS / "icons" / f"{spec.icon}.png", size=31, color=color, position=(54, 46))
        title = text(spec.title, (82, 30), size=30, anchor="top_left", scheme=scheme)
        number = text(f"{spec.number:02d}", (811, 45), size=29, color=color)
        category = text(spec.category, (40, 84), size=16, color=scheme.muted, anchor="top_left")
        with self.at(0.14):
            self.play(PopIn(icon), SlideIn(title, distance=14), FadeIn(number), FadeIn(category), run_time=0.45)
        main = equation(
            spec.expression,
            (439.5, 216) if tall else (289, 169),
            size=62 if tall else 63,
            width=770 if tall else 487,
            scheme=scheme,
            color_map=spec.color_map(scheme),
        )
        with self.at(0.65):
            self.play(Write(main), run_time=1.0)
        description = text(
            spec.description,
            (40, 314 if tall else 254),
            size=26 if tall else 21,
            color=scheme.muted,
            anchor="top_left",
            body=True,
            spacing=12,
        )
        with self.at(1.1):
            self.play(SlideIn(description, distance=10), run_time=0.45)
        diagram = make_diagram(spec, tall=tall, scheme=scheme)
        if diagram.guides:
            with self.at(1.45):
                self.play(*(FadeIn(c) for c in diagram.guides), run_time=0.35)
        if diagram.paths:
            with self.at(1.60):
                self.play(*(Draw(c) for c in diagram.paths), run_time=1.15, rate_func=linear)
        if diagram.marks:
            with self.at(2.25):
                self.play(*(PopIn(c) if not hasattr(c, "text") else FadeIn(c) for c in diagram.marks), run_time=0.45)
        if diagram.motions:
            with self.at(2.8):
                self.play(*diagram.motions, run_time=1.45, rate_func=linear)
        example_label = text(
            "IN PRACTICE" if not tall else "THE IDEA IN ONE LINE",
            (40, 683 if tall else 298),
            size=15 if not tall else 16,
            color=scheme.muted,
            anchor="top_left",
        )
        sample = equation(
            spec.example,
            (40, 714 if tall else 319),
            size=28 if not tall else 32,
            color=color,
            color_map={"3": scheme.secondary, "4": scheme.primary, "5": scheme.tertiary}
            if spec.number == 1
            else spec.color_map(scheme),
            width=793,
            anchor="top_left",
        )
        with self.at(2.9):
            self.play(FadeIn(example_label), Write(sample), run_time=0.65)
        with self.at(3.75):
            self.play(Pulse(main, factor=1.025), run_time=0.65)
        progress = Line(807, stroke=color, stroke_width=2, position=(36, height - 24), anchor="top_left")
        # A left-anchored line grows through the equation's active reading window.
        with self.at(0.35):
            self.play(Draw(progress), run_time=4.85, rate_func=linear)
        with self.at(5.20):
            self.play(FadeOut(active), progress.animate.opacity_to(0.24), run_time=0.45)
        if self.sound:
            self.add_audio(SFX / "tick.wav", start=0.14, volume=0.5)
            self.add_audio(SFX / "resolve.wav", start=2.9, volume=0.5)
        self.wait_until(PANEL_DURATION)
