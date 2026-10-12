from faceless_champ import (
    Canvas, Scene, Text, Circle,
    Typewriter, FadeIn, FadeOut,
)


class Hello(Scene):
    def __init__(self):
        canvas = Canvas(1920, 1080, "#000000")
        super().__init__(canvas)

    def construct(self):
        title = Text(
            "Hello, Python",
            font_size=100,
            color="white",
            position=(960, 400),
        )
        dot = Circle(
            60,
            fill="#F5A97F",
            stroke=None,
            position=(400, 700),
        )
        self.play(
            Typewriter(title), FadeIn(dot),
            run_time=1.5,
        )
        self.wait(0.5)
        self.play(
            dot.animate.move_to(1520, 700),
            run_time=3,
        )
        self.wait(0.5)
        self.play(
            FadeOut(title), FadeOut(dot),
            run_time=0.8,
        )
        self.wait(0.5)
