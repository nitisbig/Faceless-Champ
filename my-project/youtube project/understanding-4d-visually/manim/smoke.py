"""Stage A Manim smoke test: a matching-token morph sqrt(1+1+1+1) -> sqrt(4) -> 2 in STIX, transparent overlay.

There is no LaTeX on this machine, so equations use ``Text`` with the bundled STIX fonts (no MathTex).
Parameters (self.faceless_parameters): colors {token: hex}.
"""

from pathlib import Path

from manim import UP, FadeIn, Indicate, Scene, Text, TransformMatchingShapes, VGroup, register_font

FONTS = Path(__file__).resolve().parent / "fonts"


def term(s, color, size=72, slant="NORMAL"):
    return Text(s, font="STIXGeneral", font_size=size, color=color, slant=slant)


class Smoke(Scene):
    def construct(self):
        with register_font(str(FONTS / "STIXGeneral.ttf")), register_font(str(FONTS / "STIXGeneralItalic.ttf")):
            self.body(self.faceless_parameters["colors"])

    def body(self, C):
        ones = [term("1²", C[k]) for k in ("x", "y", "z", "w")]
        plus = [term("+", C["muted"]) for _ in range(3)]
        inner = VGroup(ones[0], plus[0], ones[1], plus[1], ones[2], plus[2], ones[3]).arrange(buff=0.18)
        root = VGroup(term("√(", C["ink"]), inner, term(")", C["ink"])).arrange(buff=0.08)
        self.play(FadeIn(root, shift=UP * 0.2), run_time=0.6)
        self.wait(0.4)
        four = VGroup(term("√", C["ink"]), term("4", C["ink"])).arrange(buff=0.06)
        self.play(TransformMatchingShapes(root, four), run_time=0.8)
        self.wait(0.3)
        two = term("2", C["ink"], size=120)
        self.play(TransformMatchingShapes(four, two), run_time=0.6)
        self.play(Indicate(two, color="#FFFFFF", scale_factor=1.15), run_time=0.5)
        self.wait(0.3)
