from faceless_champ import Canvas, Scene, Text, Rectangle, Group, PopIn

scene = Scene(Canvas(1920, 1080, "#0b101b"))
card = Rectangle(width=900, height=360, corner_radius=28,
                 fill="#172238", stroke="#48e0cb", stroke_width=3,
                 position=(960, 540))
title = Text("Build with Python", font_size=72,
             color="#edf2fc", position=(960, 490))
label = Text("Text. Shapes. A timeline.", font_size=32,
             color="#8996ad", position=(960, 590))
scene.play(PopIn(Group(card, title, label)), run_time=0.6)
scene.wait(1.4)
