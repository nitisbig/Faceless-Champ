"""Native Manim producer; FacelessChamp owns playback and final export."""

from itertools import pairwise

from manim import MathTex, Scene, TransformMatchingTex, Write, config, smooth

DURATION = 45.0
# Each expression is an equality of entire convergent Taylor series.
EXPRESSIONS = (
    r"e^z = 1 + z + \frac{z^2}{2!} + \frac{z^3}{3!} + \frac{z^4}{4!} + \cdots",
    r"e^{i\theta} = 1 + i\theta + \frac{(i\theta)^2}{2!} + \frac{(i\theta)^3}{3!} + \frac{(i\theta)^4}{4!} + \cdots",
    r"e^{i\theta} = 1 + i\theta - \frac{\theta^2}{2!} - i\frac{\theta^3}{3!} + \frac{\theta^4}{4!} + \cdots",
    r"e^{i\theta} = \left(1-\frac{\theta^2}{2!}+\frac{\theta^4}{4!}-\cdots\right) + i\left(\theta-\frac{\theta^3}{3!}+\frac{\theta^5}{5!}-\cdots\right)",
    r"e^{i\theta} = \underbrace{\left(1-\frac{\theta^2}{2!}+\frac{\theta^4}{4!}-\cdots\right)}_{\cos\theta} + i\underbrace{\left(\theta-\frac{\theta^3}{3!}+\frac{\theta^5}{5!}-\cdots\right)}_{\sin\theta}",
    r"e^{i\theta} = \cos\theta + i\sin\theta",
    r"e^{i\pi} = \cos\pi + i\sin\pi",
    r"e^{i\pi} = -1 + i\cdot 0",
    r"e^{i\pi} = -1",
    r"e^{i\pi} + 1 = 0",
)
HOLDS = (2, 3, 3, 3, 3, 2, 2, 2, 1, 4)
WRITE_TIME = 2
TRANSFORM_TIME = 2


class EulerIdentity(Scene):
    def construct(self):
        assert WRITE_TIME + (len(EXPRESSIONS) - 1) * TRANSFORM_TIME + sum(HOLDS) == DURATION
        formulas = []
        for index, expression in enumerate(EXPRESSIONS):
            formula = MathTex(
                expression,
                font_size=80 if index == len(EXPRESSIONS) - 1 else 56,
                substrings_to_isolate=[r"e^{i\theta}", r"e^{i\pi}", "e^z", "=", "+", r"\cos", r"\sin"],
            )
            formula.set_color_by_tex(r"\cos", "#68DBE8")
            formula.set_color_by_tex(r"\sin", "#FFC878")
            # Per-equation fit keeps the final identity large and long series legible.
            if formula.width > config.frame_width - 1.8:
                formula.scale_to_fit_width(config.frame_width - 1.8)
            formula.move_to([0, 0, 0])
            formulas.append(formula)
        self.play(Write(formulas[0]), run_time=WRITE_TIME)
        self.wait(HOLDS[0])
        for index, (previous, following) in enumerate(pairwise(formulas), start=1):
            self.play(
                TransformMatchingTex(previous, following),
                run_time=TRANSFORM_TIME,
                rate_func=smooth,
            )
            self.wait(HOLDS[index])
