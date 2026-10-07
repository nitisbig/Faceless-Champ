from faceless_champ import Canvas, Rectangle, Scene, Text

scene = Scene(Canvas(1920, 1080, "#0b101b"))
card = Rectangle(width=400, height=220, fill="#48e0cb",
                 stroke="#edf2fc", stroke_width=2, position=(960, 540))
scene.add(card)
scene.play(
    card.animate.fill_to("#708fff").width_to(650).height_to(340)
        .corner_radius_to(48).stroke_width_to(6).rotate_to(8),
    run_time=2,
)
scene.wait(0.5)
