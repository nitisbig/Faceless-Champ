"""Render with: faceless-champ render examples/flags.py FlagsShowcase -o output/flags.mp4 -q ql."""

from faceless_champ import Canvas, FadeIn, Flag, PopIn, Scene, Text


class FlagsShowcase(Scene):
    def __init__(self):
        super().__init__(Canvas(960, 540, "#111827"))

    def construct(self):
        flags = []
        for index, code in enumerate(("np", "us", "gb-eng", "jp", "ch", "br")):
            x = 240 + (index % 3) * 240
            y = 155 + (index // 3) * 230
            flag = Flag(code, width=170, height=140, position=(x, y))
            label = Text(code.upper(), font_size=24, color="#D1D5DB", position=(x, y + 95))
            self.play(PopIn(flag), FadeIn(label), run_time=0.2)
            flags.append(flag)
        self.play(*(flag.animate.scale_to(1.08) for flag in flags), run_time=0.4)
        self.wait(0.6)
