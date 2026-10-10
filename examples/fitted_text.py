"""Measured typography using only the public core package."""

from faceless_champ import Bounds, Canvas, FadeIn, Scene, fit_text


class FittedTypography(Scene):
    def construct(self):
        self.canvas = Canvas(1920, 1080, "#FFFFFF")
        label = fit_text(
            "Understand the system.\nChoose a useful problem.",
            Bounds(240, 280, 1680, 800),
            font_size=100,
            min_font_size=40,
            color="#292724",
        )
        self.play(FadeIn(label), run_time=0.5)
        self.wait(1.5)
