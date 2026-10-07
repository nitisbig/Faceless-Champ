from faceless_champ import Canvas, Scene, Text, FadeIn, FadeOut

scene = Scene(Canvas(1920, 1080, "#0b101b"))
first = Text("First, the question.", font_size=72, position=(960, 460))
second = Text("Then, the evidence.", font_size=56, position=(960, 600))
scene.play(FadeIn(first), run_time=0.5)
with scene.at(1.5):
    scene.play(FadeIn(second), run_time=0.5)
scene.wait_until(3)
scene.play(FadeOut(first), FadeOut(second), run_time=0.5)
scene.wait(0.5)
