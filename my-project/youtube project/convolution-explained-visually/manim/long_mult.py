"""S06 - long multiplication is convolution (Manim, transparent overlay).

Parameters (self.faceless_parameters):
  times   relative seconds for each beat
  colors  token colors
  x_right, cw, size, rows  layout in 1920x1080 design pixels (top-left origin)
"""

from pathlib import Path

import numpy as np
from manim import (
    DOWN, LEFT, RIGHT, UP, Create, FadeIn, FadeOut, Indicate, LaggedStart, Line, RoundedRectangle,
    Scene, Text, VGroup, register_font,
)

FONT = Path(__file__).resolve().parent / "fonts" / "SpaceGrotesk.ttf"
PX = 1 / 135.0  # design pixels -> manim units (frame width 14.222 at 1920 px)


def pt(x, y):
    return np.array([(x - 960) * PX, (540 - y) * PX, 0.0])


class LongMult(Scene):
    def construct(self):
        with register_font(str(FONT)):
            self.body(self.faceless_parameters)

    def body(self, P):
        T, C = P["times"], P["colors"]
        xr, cw, size, rows = P["x_right"], P["cw"], P["size"], P["rows"]
        self.cur = 0.0

        def go(t):
            if t > self.cur + 1e-3:
                self.wait(t - self.cur)
                self.cur = t

        def play(*anims, run_time):
            self.play(*anims, run_time=run_time)
            self.cur += run_time

        def digit(ch, col, y, color, s=size, weight="MEDIUM"):
            return Text(ch, font="Space Grotesk", font_size=s, color=color, weight=weight).move_to(
                pt(xr - col * cw - cw / 2, y)
            )

        def number(text, y, color, shift_cols=0, **kw):
            return VGroup(*[digit(ch, i + shift_cols, y, color, **kw) for i, ch in enumerate(reversed(text))])

        top = number("123", rows["top"], C["signal"])
        times_sign = digit("×", 3, rows["mult"], C["kernel"], s=size * 0.8)
        mult = number("11", rows["mult"], C["kernel"])
        line1 = Line(pt(xr - 4 * cw, rows["line1"]), pt(xr + 8, rows["line1"]), color=C["line"], stroke_width=3)
        row1 = number("123", rows["p1"], C["signal"])
        row2 = number("123", rows["p2"], C["signal"], shift_cols=1)
        row1.set_opacity(0.72)
        row2.set_opacity(0.72)
        line2 = Line(pt(xr - 4 * cw, rows["line2"]), pt(xr + 8, rows["line2"]), color=C["line"], stroke_width=3)
        result = number("1353", rows["result"], C["output"], s=size * 1.08, weight="BOLD")
        res_lr = list(reversed(result))  # left-to-right digits

        go(T["top"])
        play(LaggedStart(*[FadeIn(d, shift=UP * 0.18) for d in reversed(top)], lag_ratio=0.3), run_time=0.7)
        go(T["mult"])
        play(FadeIn(times_sign, shift=UP * 0.1), LaggedStart(*[FadeIn(d, shift=UP * 0.18) for d in reversed(mult)],
                                                              lag_ratio=0.3), run_time=0.5)
        go(T["line1"])
        play(Create(line1), run_time=0.3)
        play(LaggedStart(*[FadeIn(d, shift=DOWN * 0.12) for d in reversed(row1)], lag_ratio=0.2), run_time=0.35)
        play(LaggedStart(*[FadeIn(d, shift=DOWN * 0.12) for d in reversed(row2)], lag_ratio=0.2), run_time=0.35)
        play(Create(line2), run_time=0.25)
        go(T["result"])
        play(LaggedStart(*[FadeIn(d, scale=1.3) for d in res_lr], lag_ratio=0.25), run_time=0.7)
        for i in range(4):
            go(T[f"d{i}"])
            play(Indicate(res_lr[i], color="#FFFFFF", scale_factor=1.28), run_time=0.5)
        go(T["same"])
        play(*[Indicate(d, color="#FFFFFF", scale_factor=1.12) for d in res_lr], run_time=0.7)

        # column sums: each result digit is the sum of one column = one slide position
        go(T["columns"])
        boxes, labels = [], []
        sums = ["3", "3+2", "2+1", "1"]  # columns right-to-left
        for col in range(4):
            x = xr - col * cw - cw / 2
            box = RoundedRectangle(corner_radius=0.08, width=cw * PX * 0.86,
                                   height=(rows["p2"] - rows["p1"] + 60) * PX,
                                   color=C["kernel"], stroke_width=2.5).move_to(pt(x, (rows["p1"] + rows["p2"]) / 2))
            label = Text(sums[col], font="Space Grotesk", font_size=size * 0.5, color=C["kernel"]).move_to(
                pt(x, rows["sums"])
            )
            boxes.append(box)
            labels.append(label)
        play(LaggedStart(*[Create(b) for b in reversed(boxes)], lag_ratio=0.2),
             LaggedStart(*[FadeIn(lb, shift=UP * 0.1) for lb in reversed(labels)], lag_ratio=0.2), run_time=0.9)

        # sliding one list of digits across another
        go(T["slide"])
        play(row2.animate.shift(RIGHT * cw * PX * 2).set_opacity(1.0), run_time=0.45)
        play(row2.animate.shift(LEFT * cw * PX * 2), run_time=1.25)
        play(row2.animate.set_opacity(0.72), run_time=0.2)

        go(T["out"])
        everything = VGroup(top, times_sign, mult, line1, row1, row2, line2, result, *boxes, *labels)
        play(FadeOut(everything), run_time=0.45)
        go(T["end"])
