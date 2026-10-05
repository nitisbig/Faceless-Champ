"""Nested diagrams, measured layout, and simultaneous group/member animation.

faceless-champ render examples/groups.py GroupedDiagram -o output/groups.mp4 -q ql
"""

from itertools import pairwise

from faceless_champ import Arrow, Canvas, Circle, FadeIn, FadeOut, Group, Scene, Text, Typewriter


class GroupedDiagram(Scene):
    def __init__(self):
        super().__init__(Canvas(1280, 720, "#101b30"))

    def construct(self):
        title = Text("One diagram. One transform.", font_size=44, position=(640, 100))
        self.play(Typewriter(title), run_time=0.8)
        nodes = []
        for name, color in [("INPUT", "#48e0cb"), ("MODEL", "#f6c85f"), ("OUTPUT", "#a99bff")]:
            dot = Circle(38, fill=color, stroke=None)
            label = Text(name, font_size=25, color=color).next_to(dot, direction="down", gap=18)
            nodes.append(Group(dot, label))
        row = Group(*nodes).arrange(gap=145)
        arrows = [
            Arrow(
                (left.bounds.right + 18, left.children[0].bounds.center[1]),
                (right.bounds.left - 18, right.children[0].bounds.center[1]),
                stroke="#adbed6",
                stroke_width=3,
            )
            for left, right in pairwise(nodes)
        ]
        diagram = Group(row, *arrows).move_to(640, 350)
        note = Text("Measured spacing · Nested groups · Independent members", font_size=24, color="#adbed6")
        note.next_to(diagram, direction="down", gap=65)
        self.play(FadeIn(diagram), FadeIn(note), run_time=0.6)
        self.play(
            diagram.animate.move_to(640, 340).scale_to(0.85).rotate_to(-8),
            nodes[1].children[0].animate.scale_to(1.2),
            run_time=1.4,
        )
        self.play(diagram.animate.rotate_to(8), run_time=1)
        self.play(diagram.animate.rotate_to(0).scale_to(1), run_time=1)
        self.wait(0.6)
        self.play(FadeOut(diagram), FadeOut(note), FadeOut(title), run_time=0.6)
