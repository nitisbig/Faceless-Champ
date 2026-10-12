from faceless_champ import Canvas, FlowChamp, FlowTheme, Scene
from faceless_champ.flow.examples import recipe

class FlowDemo(Scene):
    def __init__(self):
        super().__init__(Canvas(1200, 675, "#000000"))

    def construct(self):
        graph, script = recipe("system")
        diagram = FlowChamp(graph, script, width=1200, height=675,
                            position=(600, 337.5),
                            theme=FlowTheme(background="#000000", stroke="#8996AD"))
        self.add(diagram)
        self.wait(6)
