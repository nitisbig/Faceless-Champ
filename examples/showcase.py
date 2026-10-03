"""Self-contained examples. Asset generation only runs when a factory needs it."""

import math
import struct
import wave
from pathlib import Path

from PIL import Image as PILImage
from PIL import ImageDraw

from faceless_champ import (
    Canvas,
    Circle,
    Draw,
    FadeIn,
    FadeOut,
    Grid,
    Image,
    Line,
    Rectangle,
    Scene,
    Sequence,
    Text,
    Triangle,
    Typewriter,
)

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "output" / "assets"
NAVY = "#101b30"
TEAL = "#48e0cb"


def make_assets():
    ASSETS.mkdir(parents=True, exist_ok=True)
    card = PILImage.new("RGBA", (640, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((12, 12, 628, 408), radius=40, fill="#233d60", outline=TEAL, width=5)
    d.ellipse((190, 70, 450, 330), fill=TEAL)
    d.polygon([(270, 140), (270, 270), (380, 205)], fill=NAVY)
    card.save(ASSETS / "card.png")
    frames = []
    for i in range(12):
        frame = PILImage.new("RGB", (240, 160), NAVY)
        d = ImageDraw.Draw(frame)
        for j in range(8):
            x, y = 120 + 52 * math.cos(j * math.tau / 8), 80 + 52 * math.sin(j * math.tau / 8)
            d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=TEAL if j == i % 8 else "#314966")
        frames.append(frame)
    frames[0].save(ASSETS / "spinner.gif", save_all=True, append_images=frames[1:], duration=100, loop=0)
    with wave.open(str(ASSETS / "tone.wav"), "wb") as out:
        out.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        out.writeframes(
            b"".join(struct.pack("<h", round(6000 * math.sin(math.tau * 220 * i / 48000))) for i in range(48000 * 6))
        )
    return ASSETS


class AnimatedTitle(Scene):
    def __init__(self):
        super().__init__(Canvas(bg=NAVY))

    def construct(self):
        self.add(Text("FACELESS CHAMP / 01", font_size=28, color=TEAL, position=(180, 150), anchor="top_left"))
        title = Text("Ideas into motion.", font_size=112, position=(960, 420))
        subtitle = Text(
            "Python components. One timeline. Your video.", font_size=40, color="#adbed6", position=(960, 560)
        )
        circle = Circle(70, fill=TEAL, stroke=None, position=(420, 780))
        line = Line(850, stroke=TEAL, stroke_width=5, position=(960, 655))
        self.play(Typewriter(title), Draw(line), run_time=1.6)
        self.play(FadeIn(subtitle), FadeIn(circle), run_time=0.5)
        self.play(circle.animate.move_to(1500, 780).scale_to(1.3), run_time=1.2)
        self.wait(0.5)
        self.play(FadeOut(title), FadeOut(subtitle), FadeOut(circle), FadeOut(line), run_time=0.6)


class MediaCard(Scene):
    def __init__(self, assets):
        super().__init__(Canvas(bg=NAVY))
        self.assets = assets

    def construct(self):
        self.add_audio(
            self.assets / "tone.wav", start=0.3, trim_start=0.5, trim_end=3.5, volume=0.35, fade_in=0.3, fade_out=0.4
        )
        self.add(Text("BRING YOUR ASSETS", font_size=32, color=TEAL, position=(960, 165)))
        picture = Image(self.assets / "card.png", width=780, height=520, position=(780, 560))
        spinner = Image(self.assets / "spinner.gif", width=360, height=240, position=(1440, 550))
        self.play(FadeIn(picture), FadeIn(spinner), run_time=0.7)
        self.play(picture.animate.rotate_to(-5).scale_to(1.05), run_time=0.8)
        self.add(Text("Images + GIF + sound", font_size=52, position=(960, 925)))
        self.wait(2)


class Closing(Scene):
    def construct(self):
        self.add(Rectangle(width=1700, height=860, fill="#163e46", stroke=None, position=(960, 540)))
        self.play(Typewriter(Text("Made with Python.", font_size=100, position=(960, 470))), run_time=1)
        self.play(
            FadeIn(Text("Ready to render your next idea?", font_size=44, color=TEAL, position=(960, 630))), run_time=0.5
        )
        self.wait(1)


def media_sequence():
    assets = make_assets()
    return Sequence(MediaCard(assets), Closing(Canvas(bg=NAVY)), crossfade=0.6)


class Panel(Scene):
    def __init__(self, index, assets):
        super().__init__(Canvas(640, 540, bg=["#15243c", "#19333e", "#29263d"][index % 3]))
        self.index, self.assets = index, assets

    def construct(self):
        labels = ["TYPE", "IMAGE", "DRAW", "MOVE", "ROTATE", "LOOP"]
        self.add(
            Text(
                f"0{self.index + 1} / {labels[self.index]}",
                font_size=26,
                color=TEAL,
                position=(35, 30),
                anchor="top_left",
            )
        )
        if self.index == 0:
            self.play(Typewriter(Text("Hello, world.", font_size=50, position=(320, 285))), run_time=1.5)
        elif self.index == 1:
            self.play(FadeIn(Image(self.assets / "card.png", width=310, height=210, position=(320, 300))), run_time=1)
        elif self.index == 2:
            self.play(
                Draw(Triangle(width=190, height=170, stroke=TEAL, stroke_width=7, position=(320, 300))), run_time=2
            )
        elif self.index == 3:
            dot = Circle(35, fill=TEAL, stroke=None, position=(100, 305))
            self.add(dot)
            self.play(dot.animate.move_to(540, 305), run_time=2.5)
        elif self.index == 4:
            square = Rectangle(width=120, height=120, fill="#d9a2ff", stroke=None, position=(320, 300))
            self.add(square)
            self.play(square.animate.rotate_to(180), run_time=2.5)
        else:
            self.add(Image(self.assets / "spinner.gif", width=320, height=215, position=(320, 300)))
        self.wait(1)


def six_panel_canvas():
    assets = make_assets()
    return Grid(*(Panel(i, assets) for i in range(6)), rows=2, columns=3, gap=18, canvas=Canvas(bg="#080f1c"))
