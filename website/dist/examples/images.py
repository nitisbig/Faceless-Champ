from pathlib import Path
from faceless_champ import Canvas, Scene, ImageSlot, FadeIn

ASSETS = Path(__file__).resolve().parent / "assets"
scene = Scene(Canvas(1920, 1080, "#0b101b"))
image = ImageSlot(ASSETS / "photo.png", width=1000, height=620,
                  position=(960, 540), fit="cover", mode="auto")
scene.play(FadeIn(image), run_time=0.5)
scene.wait(1.5)
