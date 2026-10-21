"""Native fixture: frozen waits must preserve their full frame counts."""

from manim import Circle, Scene, Square, Transform


class GeometryScene(Scene):
    def construct(self):
        shape = Square(side_length=2, fill_opacity=0.5, color="#44BBCC")
        self.add(shape)
        self.wait(0.5)
        self.play(Transform(shape, Circle(radius=1, fill_opacity=0.5, color="#CC8844")), run_time=1)
        self.wait(0.5)


class ParameterScene(Scene):
    def construct(self):
        shape = Square(side_length=self.faceless_parameters["side"], fill_opacity=1, color="#44BBCC")
        self.add(shape)
        self.wait(1)
