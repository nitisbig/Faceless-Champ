from faceless_champ import Canvas, Circle, Scene, Text, FadeIn

scene = Scene(Canvas(1080, 1920, "#0b101b"))
scene.add(Text("Made with Python", font_size=72,
               position=(540, 760), color="#edf2fc"))
scene.play(FadeIn(Circle(90, fill="#48e0cb", stroke=None,
                         position=(540, 1100))), run_time=1)
scene.wait(1)
