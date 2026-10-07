from faceless_champ import Canvas, Circle, Group, Text, Scene, FadeIn

scene = Scene(Canvas(1920, 1080, "#0b101b"))
cards = []
for word in ("Compose", "Animate", "Export"):
    dot = Circle(50, fill="#48e0cb", stroke=None)
    label = Text(word, font_size=36).next_to(dot, direction="down", gap=24)
    cards.append(Group(dot, label))
diagram = Group(*cards).arrange(direction="right", gap=120).move_to(960, 540)
scene.play(FadeIn(diagram), run_time=0.7)
scene.play(diagram.animate.scale_to(1.15), run_time=0.8)
scene.wait(0.5)
