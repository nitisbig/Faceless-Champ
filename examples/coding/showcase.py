"""Render with: faceless-champ render examples/coding/showcase.py CodeDemo -q ql."""

from faceless_champ import Canvas, CodeReveal, CodingChamp, Scene


class CodeDemo(Scene):
    def __init__(self):
        super().__init__(Canvas(1920, 1080, "#080E1B"))

    def construct(self):
        code = CodingChamp(
            "class Player:\n    def __init__(self, name):\n        self.name = name\n        self.health = 100",
            language="python",
            theme="midnight",
            filename="player.py",
            width=1500,
            height=720,
            font_size=48,
            position=(960, 540),
            reveal_mode="block",
            block_ends=(1, 2, 4),
            highlighted_lines=(3, 4),
        )
        self.play(CodeReveal(code, end=1 / 3), run_time=0.5)
        self.wait(0.5)
        self.play(CodeReveal(code, start=1 / 3, end=2 / 3), run_time=0.5)
        self.wait(0.5)
        self.play(CodeReveal(code, start=2 / 3), run_time=0.5)
        self.wait(1)
