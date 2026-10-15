"""Ten-second, CPU-only spring showcase. Run with --frames for a storyboard first."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from faceless_champ import (
    Animation,
    Canvas,
    Circle,
    Component,
    Group,
    Polyline,
    Rectangle,
    Scene,
    Sequence,
    Spring,
    Stagger,
    StoryboardSample,
    Text,
    linear,
    render_storyboard,
    smooth,
)

BG, PANEL, WHITE, MUTED = "#101722", "#1d2a3c", "#f0f4fa", "#9baac0"
TEAL, BLUE, AMBER, GUIDE = "#58dfc1", "#82a8ff", "#ffc278", "#36465f"
WIDTH, HEIGHT = 960, 540

# Example configurations, not a preset registry. All use stiffness=100, mass=1.
GENTLE = Spring(stiffness=100, damping=20, mass=1)  # critical
SNAPPY = Spring(stiffness=100, damping=25, mass=1)  # overdamped
BOUNCY = Spring(stiffness=100, damping=10, mass=1)  # underdamped


@dataclass
class Shot:
    """Keep authoring objects available for the example's sampled layout audit."""

    scene: Scene
    visuals: list[Component] = field(default_factory=list)

    def add(self, *visuals):
        with self.scene.at(0):
            self.scene.add(*visuals)
        self.visuals.extend(visuals)

    def text(self, value, x, y, size=18, color=MUTED):
        visual = Text(value, position=(x, y), font_size=size, color=color, align="center")
        self.add(visual)
        return visual


def page(number, title, subtitle):
    shot = Shot(Scene(Canvas(WIDTH, HEIGHT, BG)))
    shot.text(f"FACELESS CHAMP  /  SPRING MOTION  /  {number}", 480, 40, 14, TEAL)
    shot.text(title, 480, 91, 32, WHITE)
    shot.text(subtitle, 480, 132, 17)
    return shot


def card(word, x, y, color=TEAL, width=112, height=50, **transform):
    return Group(
        Rectangle(
            width=width,
            height=height,
            corner_radius=12,
            fill=color,
            stroke=None,
            stroke_width=0,
            position=(x, y),
        ),
        Text(word, position=(x, y), font_size=18, color=BG, align="center"),
        **transform,
    )


def comparison():
    shot = page("01", "Same distance. Different character.", "160 px of travel  /  2.6 seconds per track")
    profiles = (
        ("Linear", linear, "constant speed", MUTED),
        ("Smooth", smooth, "ease in / out", WHITE),
        ("Gentle spring", GENTLE, "critical  /  c = 20", TEAL),
        ("Snappy spring", SNAPPY, "over  /  c = 25", BLUE),
        ("Bouncy spring", BOUNCY, "under  /  c = 10", AMBER),
    )
    for i, (name, easing, caption, color) in enumerate(profiles):
        x = 112 + i * 184
        shot.add(
            Polyline(((x, 235), (x, 395)), stroke=GUIDE, stroke_width=2),
            Polyline(((x - 65, 235), (x + 65, 235)), stroke=GUIDE, stroke_width=2),
            Circle(radius=3, fill=GUIDE, stroke=None, position=(x, 395)),
        )
        tile = card("160 px", x, 395, color)
        shot.add(tile)
        shot.text(name, x, 452, 18, color)
        shot.text(caption, x, 481, 14)
        with shot.scene.at(0.45):
            shot.scene.play(tile.animate.move_to(x, 235), run_time=2.6, rate_func=easing)
    shot.text("Spring configurations: k = 100, m = 1. Labels describe this example only.", 480, 508, 13)
    shot.scene.wait_until(4)
    return shot


def transforms():
    shot = page("02", "Text, cards, and complete groups.", "Position, scale, and rotation share the existing timeline")
    words = Text("Words\narrive.", position=(120, 278), font_size=38, color=TEAL, align="center", opacity=0)
    tile = card("READY", 480, 334, BLUE, width=164, height=106, scale=0.72, rotation=-6)
    tiles = Group(
        *(card(str(i + 1), 714 + i * 66, 280, AMBER, width=52, height=78) for i in range(3)),
        position=(780, 340),
        scale=0.8,
        rotation=-8,
    )
    shot.add(words, tile, tiles)
    for x, name, caption in (
        (180, "TEXT SLIDE", "spring motion + smooth fade"),
        (480, "CARD TRANSFORM", "translate / scale / rotate"),
        (780, "GROUP OF CARDS", "one parent, three children"),
    ):
        shot.text(name, x, 426, 16, WHITE)
        shot.text(caption, x, 460, 15)
    with shot.scene.at(0.25):
        shot.scene.play(Animation(words, {"position": (180, 278)}, rate_func=GENTLE), run_time=1.8)
    with shot.scene.at(0.25):
        shot.scene.play(words.animate.opacity_to(1), run_time=0.3, rate_func=smooth)
    with shot.scene.at(0.4):
        shot.scene.play(tile.animate.move_to(480, 278).scale_to(1).rotate_to(0), run_time=1.8, rate_func=SNAPPY)
    with shot.scene.at(0.6):
        shot.scene.play(tiles.animate.move_to(780, 280).scale_to(1).rotate_to(0), run_time=1.8, rate_func=BOUNCY)
    shot.scene.wait_until(3)
    return shot


def network():
    shot = page("03", "One network. Four arrivals.", "Staggered node groups settle into a shared layout")
    targets = ((280, 235), (680, 235), (280, 365), (680, 365))
    edges = [Polyline(((480, 300), target), stroke=GUIDE, stroke_width=3, opacity=0) for target in targets]
    shot.add(*edges)
    hub = Group(
        Circle(radius=35, fill=PANEL, stroke=TEAL, stroke_width=2, position=(480, 300)),
        Text("API", position=(480, 300), font_size=20, color=WHITE),
    )
    shot.add(hub)
    motions = []
    for i, ((x, y), label) in enumerate(zip(targets, ("UI", "DB", "JOB", "LOG"))):
        node = Group(
            Circle(radius=28, fill=PANEL, stroke=BLUE, stroke_width=2, position=(x, y)),
            Text(label, position=(x, y), font_size=17, color=WHITE, align="center"),
            position=(x + (-75 if i % 2 == 0 else 75), y + 45),
            scale=0.78,
        )
        shot.add(node)
        motions.append(Animation(node, {"position": (x, y), "scale": 1}, rate_func=BOUNCY))
    with shot.scene.at(0):
        shot.scene.play(Stagger(*motions, lag=0.13, duration=1.6, delay=0.25))
    with shot.scene.at(0.8):
        shot.scene.play(*(edge.animate.opacity_to(1) for edge in edges), run_time=0.6, rate_func=smooth)
    shot.text("Independent tracks. One shared timeline.", 480, 480, 18)
    shot.scene.wait_until(3)
    return shot


def build_shots():
    return comparison(), transforms(), network()


def showcase():
    return Sequence(*(shot.scene for shot in build_shots()))


STORYBOARD = tuple(
    StoryboardSample(time, label)
    for time, label in (
        (0, "comparison / start"),
        (0.64, "comparison / bounce"),
        (1.75, "comparison / mid travel"),
        (3.97, "comparison / terminal hold"),
        (4.3, "text / entrance"),
        (4.72, "group / overshoot"),
        (6.97, "transforms / terminal hold"),
        (7.25, "network / first node"),
        (7.65, "network / stagger"),
        (8.4, "network / connections"),
        (9.0, "network / settled"),
        (299 / 30, "last encoded frame / hold"),
    )
)


def audit_layout(shots, samples=301, margin=20):
    """Sample conservative bounds; this is a visual audit, not a continuous proof."""
    minimum = float("inf")
    count = 0
    for shot in shots:
        for i in range(samples):
            time = shot.scene.duration * i / (samples - 1)
            for visual in shot.visuals:
                box = shot.scene.bounds_at(visual, time)
                clearance = min(box.left, box.top, WIDTH - box.right, HEIGHT - box.bottom)
                if clearance < margin:
                    raise ValueError(
                        f"Unsafe layout at {time:g}s: {type(visual).__name__} has {clearance:g}px clearance"
                    )
                minimum = min(minimum, clearance)
                count += 1
    return {"bounds_checked": count, "samples_per_shot": samples, "minimum_canvas_clearance_px": minimum}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/spring_motion/preview.mp4"))
    parser.add_argument("--quality", choices=("preview", "high"), default="preview")
    parser.add_argument("--frames", action="store_true", help="save a storyboard before encoding")
    parser.add_argument("--storyboard-only", action="store_true", help="save a storyboard without encoding")
    parser.add_argument("--check", action="store_true", help="audit sampled bounds without encoding")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    shots = build_shots()
    if args.check:
        print(json.dumps(audit_layout(shots), indent=2))
        return
    movie = Sequence(*(shot.scene for shot in shots))
    if args.frames or args.storyboard_only:
        path = render_storyboard(movie, STORYBOARD, args.output.parent / "storyboard", overwrite=args.overwrite)
        print(f"Storyboard: {path}")
    if not args.storyboard_only:
        high = args.quality == "high"
        path = movie.render(
            args.output,
            width=1920 if high else 960,
            height=1080 if high else 540,
            fps=30,
            antialias=2 if high else 1,
            crf=18 if high else 20,
            preset="medium" if high else "fast",
            overwrite=args.overwrite,
        )
        print(f"Video: {path}")


if __name__ == "__main__":
    main()
