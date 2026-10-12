from faceless_champ import Canvas, CodeReveal, CodingChamp, Scene

class CodeDemo(Scene):
    def __init__(self):
        super().__init__(Canvas(1280, 720, "#000000"))

    def construct(self):
        panel = CodingChamp(
            "def square(x):\n    return x * x\n\nprint(square(7))",
            language="python", filename="square.py", theme="midnight",
            width=1080, height=520, font_size=40, position=(640, 360),
            reveal_mode="block", block_ends=(2, 4), highlighted_lines=(2,),
        )
        self.play(CodeReveal(panel, end=.5), run_time=1)
        self.wait(.5)
        self.play(CodeReveal(panel, start=.5), run_time=1)
        self.wait(1)
