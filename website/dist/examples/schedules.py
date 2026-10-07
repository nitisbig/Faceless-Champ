from faceless_champ import Canvas, Circle, Scene, Stagger, Succession, Repeat, PopIn

scene = Scene(Canvas(1920, 1080, "#0b101b"))
dots = [Circle(50, fill="#48e0cb", stroke=None,
               position=(660 + i * 200, 540)) for i in range(4)]
scene.play(Stagger(*(PopIn(dot) for dot in dots), lag=0.2, duration=0.5))
scene.play(Stagger(*(
    Succession(dot.animate.scale_to(1.5), dot.animate.scale_to(1), duration=0.4)
    for dot in dots
), lag=0.15))
scene.play(Repeat(dots[0].animate.opacity_to(0.3),
                  cycles=2, ping_pong=True, duration=0.4))
scene.wait(0.5)
