from faceless_champ import (
    Canvas, Scene, ProgressRing, ProgressBar, LoadingDots,
    Countdown, Repeat, linear,
)

scene = Scene(Canvas(1920, 1080, "#0b101b"))
ring = ProgressRing(width=240, height=240, label=True, position=(650, 480))
timer = Countdown(4, font_size=120, position=(1250, 480))
bar = ProgressBar(width=700, height=30, position=(960, 730))
dots = LoadingDots(width=160, height=40, position=(960, 850))
scene.add(ring, timer, bar, dots)
with scene.at(0):
    scene.play(ring.animate.progress_to(1), timer.animate.value_to(0),
               bar.animate.progress_to(1), run_time=4, rate_func=linear)
with scene.at(0):
    scene.play(Repeat(dots.animate.progress_to(1), cycles=4, duration=1),
               rate_func=linear)
scene.wait_until(4.5)
