from faceless_champ import Scene, Text, Circle, Typewriter, FadeIn

class Hello(Scene):
    def construct(self):
        title = Text("Hello, world!", font_size=100,
                     position=(960, 400), color="#edf2fc")
        dot = Circle(60, fill="#48e0cb", stroke=None,
                     position=(400, 700))
        self.play(Typewriter(title), FadeIn(dot), run_time=1.5)
        self.play(dot.animate.move_to(1520, 700), run_time=1)
        self.wait(0.5)
