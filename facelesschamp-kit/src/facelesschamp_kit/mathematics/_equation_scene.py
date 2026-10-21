"""Executed only by the isolated Manim worker, never imported by Kit."""

from itertools import pairwise

from manim import MathTex, Scene, TransformMatchingTex, Write, config


class EquationTransformScene(Scene):
    def construct(self):
        params = self.faceless_parameters
        formulas = [MathTex(e, color=params["color"], font_size=params["font_size"]) for e in params["expressions"]]
        ratio = min(
            1,
            (config.frame_width - 0.8) / max(m.width for m in formulas),
            (config.frame_height - 0.8) / max(m.height for m in formulas),
        )
        for formula in formulas:
            formula.scale(ratio).move_to([0, 0, 0])
        elapsed, frame = 0.0, 0

        def duration(seconds):
            nonlocal elapsed, frame
            elapsed += seconds
            target = round(elapsed * config.frame_rate)
            count, frame = target - frame, target
            if seconds > 0 and count < 1:
                raise ValueError("Equation phase is shorter than one source frame")
            return count / config.frame_rate

        self.play(Write(formulas[0]), run_time=duration(params["write_time"]))
        for previous, following in pairwise(formulas):
            if params["hold_time"]:
                self.wait(duration(params["hold_time"]))
            self.play(TransformMatchingTex(previous, following), run_time=duration(params["transform_time"]))
        if params["hold_time"]:
            self.wait(duration(params["hold_time"]))
