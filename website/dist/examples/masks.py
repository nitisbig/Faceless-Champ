from faceless_champ import Canvas, CircleMask, Group, Rectangle, Scene, Text, Wipe

scene = Scene(Canvas(1920, 1080, "#0b101b"))
card = Rectangle(width=700, height=400, fill="#708fff", stroke=None,
                 position=(960, 540))
stripe = Rectangle(width=760, height=100, fill="#48e0cb", stroke=None,
                   rotation=-20, position=(960, 540))
word = Text("REVEAL", font_size=64, color="#0b101b", position=(960, 540))
visual = Group(card, stripe, word, mask=CircleMask(230))
scene.add(visual)
scene.play(Wipe(visual, direction="right"), run_time=1)
scene.play(visual.animate.mask_to(width=620, height=380), run_time=1)
scene.wait(0.5)
