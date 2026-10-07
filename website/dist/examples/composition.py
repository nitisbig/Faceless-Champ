from faceless_champ import Canvas, Scene, Text, FadeIn, Sequence, Grid

canvas = Canvas(1920, 1080, "#0b101b")
def panel(word):
    scene = Scene(canvas)
    scene.play(FadeIn(Text(word, font_size=120,
                            position=(960, 540))), run_time=0.5)
    scene.wait(1.5)
    return scene

video = Sequence(
    panel("One idea"),
    Grid(panel("A"), panel("B"), rows=1, columns=2,
         gap=24, canvas=canvas),
    panel("One video"),
    crossfade=0.3,
)
