"""Self-contained motion graphics showcase: python examples/motion_graphics/render.py."""

import argparse
from pathlib import Path

from faceless_champ import (
    Canvas,
    Checkmark,
    Circle,
    CircleMask,
    Countdown,
    Gauge,
    Group,
    LoadingDots,
    PillowRenderer,
    ProgressBar,
    ProgressRing,
    Rectangle,
    RectangleMask,
    Repeat,
    Scene,
    Sequence,
    ShapeMask,
    Stagger,
    Succession,
    Text,
    Wipe,
    linear,
)

BG, WHITE, MUTED, TEAL, BLUE = "#0b101b", "#edf2fc", "#8996ad", "#48e0cb", "#708fff"


def text(scene, value, x, y, size=20, color=MUTED):
    c = Text(value, position=(x, y), font_size=size, color=color)
    with scene.at(0):
        scene.add(c)
    return c


def page(number, title):
    s = Scene(Canvas(960, 540, BG))
    text(s, f"FACELESS CHAMP   /   MOTION {number}", 480, 42, 15, TEAL)
    text(s, title, 480, 92, 34, WHITE)
    return s


def properties():
    s = page("01", "Properties that move together")
    card = Rectangle(width=140, height=90, fill=TEAL, stroke=WHITE, stroke_width=2, position=(270, 265))
    label = text(s, "COLOR / GEOMETRY", 270, 390, 17)
    inner = Group(
        Rectangle(width=100, height=65, fill=BLUE, stroke=None, rotation=25, position=(690, 265)),
        Rectangle(width=100, height=65, fill=None, stroke=WHITE, rotation=-25, position=(690, 265)),
    )
    nested = Group(inner, rotation=15)
    s.add(card, nested)
    text(s, "NESTED X / Y SCALE", 690, 390, 17)
    with s.at(0):
        s.play(
            Repeat(
                card.animate.fill_to("#708fff88")
                .stroke_to(TEAL)
                .width_to(220)
                .height_to(150)
                .stroke_width_to(8)
                .corner_radius_to(40),
                cycles=2,
                ping_pong=True,
                duration=2.5,
            )
        )
    with s.at(0):
        s.play(Repeat(nested.animate.scale_xy_to(1.6, 0.65).rotate_to(-25), cycles=2, ping_pong=True, duration=2.5))
    with s.at(0):
        s.play(label.animate.color_to(TEAL), run_time=2)
    dots = [Circle(radius=6, fill=TEAL, stroke=None, position=(420 + i * 40, 470)) for i in range(4)]
    with s.at(0):
        s.add(*dots)
        s.play(
            Stagger(*(Succession(d.animate.scale_to(1.8), d.animate.scale_to(1), duration=0.6) for d in dots), lag=0.25)
        )
    s.wait_until(6)
    return s


def masks():
    s = page("02", "One mask. The complete composition.")
    specs = [
        RectangleMask(170, 150),
        CircleMask(85),
        ShapeMask(((0.5, 0), (1, 0.5), (0.5, 1), (0, 0.5)), width=180, height=180),
    ]
    for i, mask in enumerate(specs):
        x = 210 + i * 270
        bg = Rectangle(width=220, height=200, fill=BLUE, stroke=None, position=(x, 275))
        stripe = Rectangle(width=230, height=65, fill=TEAL, stroke=None, rotation=-25, position=(x, 275))
        word = Text("LOCAL", font_size=20, color=BG, position=(x, 275))
        g = Group(bg, stripe, word, mask=mask)
        with s.at(0):
            s.add(g)
        text(s, ("RECTANGLE", "CIRCLE", "POLYGON")[i], x, 412, 17)
        with s.at(0):
            s.play(Wipe(g, direction=("right", "up", "down")[i]), run_time=1.5)
        with s.at(1.5):
            s.play(
                Repeat(
                    g.animate.mask_to(position=(10, -5), width=110, height=130), cycles=2, ping_pong=True, duration=1.5
                )
            )
    text(s, "Group clipping  /  local coordinates  /  animated dimensions", 480, 480, 18)
    s.wait_until(6)
    return s


def indicators():
    s = page("03", "Progress with a purpose")
    bar = ProgressBar(width=190, height=18, position=(190, 237))
    ring = ProgressRing(width=100, height=100, position=(480, 232), label=True)
    gauge = Gauge(width=120, height=120, position=(770, 258), label=True)
    dots = LoadingDots(position=(190, 400))
    check = Checkmark(width=70, height=70, position=(480, 400), color=TEAL, stroke_width=7)
    countdown = Countdown(5, font_size=60, position=(770, 400), color=WHITE)
    s.add(bar, ring, gauge, dots, check, countdown)
    for name, x, y in (
        ("PROGRESS BAR", 190, 303),
        ("PROGRESS RING", 480, 303),
        ("GAUGE", 770, 303),
        ("LOADING DOTS", 190, 470),
        ("CHECKMARK", 480, 470),
        ("COUNTDOWN", 770, 470),
    ):
        text(s, name, x, y, 16)
    with s.at(0):
        s.play(
            bar.animate.progress_to(1),
            ring.animate.progress_to(1),
            gauge.animate.progress_to(1),
            countdown.animate.value_to(0),
            run_time=5,
            rate_func=linear,
        )
    with s.at(0):
        s.play(Repeat(dots.animate.progress_to(1), cycles=3, duration=2), rate_func=linear)
    with s.at(3.5):
        s.play(check.animate.progress_to(1), run_time=1)
    s.wait_until(6)
    return s


def showcase():
    return Sequence(properties(), masks(), indicators())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("output/motion_graphics/showcase.mp4"))
    parser.add_argument("--frames", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    movie = showcase()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.frames:
        renderer = PillowRenderer(2)
        for t in (1, 2.5, 6.8, 9, 13, 17.5):
            renderer.frame(movie, t, (960, 540)).save(args.output.parent / f"frame-{t:g}.png")
    else:
        movie.render(args.output, width=960, height=540, fps=24, antialias=2, overwrite=args.overwrite)
