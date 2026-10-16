"""A deterministic, silent 45-second tour of the public Spring API."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

from faceless_champ import (
    Animation,
    Arrow,
    Canvas,
    Circle,
    Component,
    Draw,
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
    smooth,
)

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / "assets/fonts/DMSans[opsz,wght].ttf"
MONO = ROOT / "src/faceless_champ/assets/DejaVuSansMono.ttf"
WIDTH, HEIGHT = 1280, 720
TOTAL_DURATION = 45.0
BG, INK, MUTED, LINE = "#F6F4EE", "#202620", "#697068", "#D9DDD3"
PAPER, ORANGE, GREEN, BLUE = "#FFFFFF", "#ED673A", "#4C795D", "#5E7F9A"
SPRING = Spring(stiffness=100, damping=12, mass=1)
CHAPTERS = (
    ("Meet the spring", 0, 5),
    ("Compare damping", 5, 14),
    ("Position", 14, 21),
    ("Scale and rotation", 21, 29),
    ("Stagger", 29, 38),
    ("Put it together", 38, 45),
)


def label(value, x, y, size=22, color=INK, *, weight=500, align="left", mono=False):
    return Text(
        value,
        font=MONO if mono else FONT,
        font_size=size,
        font_weight=None if mono else weight,
        color=color,
        position=(x, y),
        anchor="center" if align == "center" else "top_left",
        align=align,
        spacing=10,
    )


def box(x, y, width, height, *, fill=PAPER, stroke=None, radius=20, **kwargs):
    return Rectangle(
        width=width,
        height=height,
        corner_radius=radius,
        fill=fill,
        stroke=stroke,
        stroke_width=1 if stroke else 0,
        position=(x, y),
        **kwargs,
    )


def line(start, end, color=LINE, width=2):
    return Polyline((start, end), stroke=color, stroke_width=width, line_cap="round")


@dataclass
class Shot:
    scene: Scene
    duration: float
    visuals: list[Component] = field(default_factory=list)

    def add(self, *visuals, at=0):
        for i, visual in enumerate(visuals, start=len(self.visuals)):
            visual.training_id = f"visual-{i}"
        with self.scene.at(at):
            self.scene.add(*visuals)
        self.visuals.extend(visuals)

    def play(self, at, duration, *animations, easing=SPRING):
        with self.scene.at(at):
            self.scene.play(*animations, run_time=duration, rate_func=easing)

    def finish(self):
        self.scene.wait_until(self.duration)
        return self


def page(index, title, subtitle):
    name, start, end = CHAPTERS[index]
    shot = Shot(Scene(Canvas(WIDTH, HEIGHT, BG)), end - start)
    shot.add(
        label("FACELESS CHAMP  /  MOTION STUDIES", 64, 35, 14, MUTED, weight=650),
        label(f"0{index + 1}  /  {name.upper()}", 850, 35, 14, MUTED, weight=650),
        label(title, 64, 86, 55, weight=700),
        label(subtitle, 67, 163, 22, MUTED),
        line((64, 675), (1216, 675)),
        label("SPRING MOTION", 64, 689, 12, MUTED, weight=650),
        label(f"{start:02d}–{end:02d}s  /  45s", 1090, 689, 12, MUTED, mono=True),
    )
    for i in range(6):
        shot.add(box(505 + i * 55, 697, 39, 4, fill=ORANGE if i == index else LINE, radius=2))
    return shot


def code(shot, lines):
    shot.add(box(640, 608, 1152, 102, fill=INK, radius=16))
    for i, value in enumerate(lines):
        shot.add(label(value, 88, 575 + i * 27, 18, "#E4EADC", mono=True))


def curve(shot, x, y, width, height, *, duration=2.6, at=0.6):
    """Plot the exact easing used by the animated examples, including its peak."""
    shot.add(
        line((x, y), (x + width, y)),
        line((x, y - height), (x + width, y - height)),
        label("TARGET", x + width - 61, y - height - 25, 12, MUTED, mono=True),
        label("TIME →", x + width - 61, y + 15, 12, MUTED, mono=True),
    )
    path = Polyline(
        tuple((x + width * i / 320, y - height * SPRING(i / 320)) for i in range(321)),
        stroke=ORANGE,
        stroke_width=4,
        line_cap="round",
        draw_by="x",
    )
    shot.add(path, at=at)
    shot.play(at, duration, Draw(path), easing=linear)


def introduction():
    shot = page(0, "Give motion a little life.", "Move past the target. Return. Settle into place.")
    shot.add(
        label("Move.\nOvershoot.\nSettle.", 80, 250, 51, weight=650),
        box(881, 378, 654, 322, stroke=LINE),
        label("THE SPRING RESPONSE", 585, 239, 14, MUTED, weight=650),
    )
    curve(shot, 594, 430, 566, 116)
    shot.add(
        line((610, 507), (1040, 507)),
        Circle(radius=21, fill=None, stroke=LINE, stroke_width=2, position=(1040, 507)),
    )
    ball = Circle(radius=13, fill=ORANGE, stroke=None, position=(610, 507))
    shot.add(ball)
    shot.play(0.6, 2.6, ball.animate.move_to(1040, 507))
    code(shot, ["from faceless_champ import Spring", "spring = Spring(stiffness=100, damping=12, mass=1)"])
    return shot.finish()


def comparison():
    shot = page(1, "Change the damping.", "Same travel. Same duration. Less damping means more overshoot.")
    profiles = (
        ("Light damping", 6, ORANGE, "37% overshoot"),
        ("Balanced damping", 12, BLUE, "9% overshoot"),
        ("Critical damping", 20, GREEN, "No overshoot"),
    )
    shot.add(label("START", 458, 210, 12, MUTED, mono=True), label("TARGET", 855, 210, 12, MUTED, mono=True))
    for i, (name, damping, color, note) in enumerate(profiles):
        y = 283 + i * 102
        shot.add(
            box(640, y, 1152, 88, radius=16),
            label(name, 88, y - 25, 23, weight=650),
            label(note, 89, y + 9, 15, MUTED),
            line((480, y), (1060, y)),
            Circle(radius=24, fill=None, stroke=LINE, stroke_width=2, position=(880, y)),
            label(f"c = {damping}", 1095, y - 9, 17, color, mono=True),
        )
        ball = Circle(radius=17, fill=color, stroke=None, position=(480, y))
        shot.add(ball)
        easing = Spring(stiffness=100, damping=damping, mass=1)
        for at, duration, target in ((0.8, 2.2, 880), (3.6, 1.7, 480), (6.0, 2.2, 880)):
            shot.play(at, duration, ball.animate.move_to(target, y), easing=easing)
    code(
        shot,
        [
            "Spring(stiffness=100, damping=6, mass=1)   # try damping=12 or 20",
            "# k=100, m=1 throughout; run_time sets the duration.",
        ],
    )
    return shot.finish()


def notification(x, y):
    return Group(
        box(x, y, 380, 128, stroke=LINE),
        box(x - 143, y, 48, 48, fill=ORANGE, radius=13),
        Polyline(((x - 155, y), (x - 147, y + 8), (x - 131, y - 9)), stroke=PAPER, stroke_width=4),
        label("Your render is ready", x - 102, y - 24, 23, weight=650),
        label("spring-motion.mp4", x - 101, y + 14, 17, MUTED),
        position=(x, y),
    )


def position():
    shot = page(2, "Land the whole card.", "Position animates the parent. Every child travels with it.")
    shot.add(
        box(900, 340, 388, 136, fill=None, stroke=LINE),
        label("FROM", 290, 281, 13, MUTED, mono=True),
        label("TARGET", 871, 231, 13, MUTED, mono=True),
        Arrow((460, 421), (680, 354), stroke=LINE, stroke_width=2, tip_size=12),
        label("One group. One position track.", 640, 500, 21, MUTED, align="center"),
    )
    card = notification(320, 425)
    shot.add(card)
    for at, target in ((0.65, (900, 340)), (3.0, (320, 425)), (4.7, (900, 340))):
        shot.play(at, 1.6, card.animate.move_to(*target))
    code(shot, ["scene.play(card.animate.move_to(900, 340),", "           run_time=1.6, rate_func=spring)"])
    return shot.finish()


def transforms():
    shot = page(3, "Pop in. Straighten up.", "Scale a button. Rotate a card. Keep every child attached.")
    shot.add(
        box(344, 374, 560, 304, stroke=LINE),
        box(936, 374, 560, 304, stroke=LINE),
        label("SCALE", 92, 246, 14, MUTED, weight=650),
        label("ROTATION", 684, 246, 14, MUTED, weight=650),
        label("0.65 → 1.00", 344, 489, 18, MUTED, mono=True, align="center"),
        label("−22° → 0°", 936, 489, 18, MUTED, mono=True, align="center"),
    )
    button = Group(
        box(344, 371, 230, 92, fill=ORANGE, radius=46),
        label("RUN", 344, 371, 30, PAPER, weight=700, align="center"),
        position=(344, 371),
        scale=0.65,
    )
    card = Group(
        box(936, 371, 150, 150, fill=GREEN, radius=24),
        label("OK", 936, 371, 48, PAPER, weight=700, align="center"),
        position=(936, 371),
        rotation=-22,
    )
    shot.add(button, card)
    for at, scale, rotation in ((0.8, 1, 0), (3.0, 0.65, -22), (5.2, 1, 0)):
        shot.play(at, 1.8, button.animate.scale_to(scale), card.animate.rotate_to(rotation))
    code(
        shot,
        [
            "scene.play(button.animate.scale_to(1), card.animate.rotate_to(0),",
            "           run_time=1.8, rate_func=spring)",
        ],
    )
    return shot.finish()


def step_card(x, number, title, description, color, *, tilt):
    return Group(
        box(x, 370, 338, 258, stroke=LINE),
        Circle(radius=28, fill=color, stroke=None, position=(x - 107, 300)),
        label(number, x - 107, 300, 19, PAPER, mono=True, align="center"),
        label(title, x - 132, 355, 34, weight=650),
        label(description, x - 131, 412, 20, MUTED),
        line((x - 132, 467), (x + 132, 467), color=color, width=4),
        position=(x, 423),
        scale=0.9,
        rotation=tilt,
        opacity=0,
    )


def stagger():
    shot = page(4, "Build rhythm with a stagger.", "The same motion, started 0.22 seconds apart.")
    cards = [
        step_card(x, number, title, description, color, tilt=tilt)
        for x, number, title, description, color, tilt in (
            (268, "01", "Design", "Set the target.", ORANGE, -4),
            (640, "02", "Animate", "Share one spring.", BLUE, 0),
            (1012, "03", "Settle", "Hold the final state.", GREEN, 4),
        )
    ]
    shot.add(*cards)
    for start in (0.7, 6.0):
        moves = [
            Animation(card, {"position": (x, 370), "scale": 1, "rotation": 0}, rate_func=SPRING)
            for x, card in zip((268, 640, 1012), cards)
        ]
        with shot.scene.at(start):
            shot.scene.play(Stagger(*moves, lag=0.22, duration=1.8))
        for i, card in enumerate(cards):
            shot.play(start + i * 0.22, 0.28, card.animate.opacity_to(1), easing=smooth)
        if start == 0.7:
            for i, (x, card) in enumerate(zip((268, 640, 1012), cards)):
                shot.play(4.15 + i * 0.16, 1.0, card.animate.move_to(x, 423).scale_to(0.9))
                shot.play(5.0 + i * 0.16, 0.25, card.animate.opacity_to(0), easing=smooth)
    code(
        shot,
        ["scene.play(Stagger(*moves, lag=0.22, duration=1.8))", "# Each move is an Animation(..., rate_func=spring)."],
    )
    return shot.finish()


def finale():
    shot = page(
        5, "One spring. Many possibilities.", "Choose the character with damping. Choose the pace with run_time."
    )
    for x, title in ((268, "POSITION"), (640, "SCALE"), (1012, "ROTATION")):
        shot.add(
            box(x, 376, 338, 294, stroke=LINE),
            label(title, x, 478, 15, MUTED, weight=650, align="center"),
        )
    shot.add(
        line((183, 365), (353, 365)),
        Circle(radius=26, fill=None, stroke=LINE, stroke_width=2, position=(353, 365)),
    )
    ball = Circle(radius=20, fill=ORANGE, stroke=None, position=(183, 365))
    tile = box(640, 365, 126, 126, fill=BLUE, scale=0.65)
    square = box(1012, 365, 126, 126, fill=GREEN, rotation=-22)
    shot.add(ball, tile, square)
    for at, target, scale, angle in ((0.6, 353, 1, 0), (2.6, 183, 0.65, -22), (4.6, 353, 1, 0)):
        shot.play(
            at, 1.6, ball.animate.move_to(target, 365), tile.animate.scale_to(scale), square.animate.rotate_to(angle)
        )
    code(
        shot,
        ["spring = Spring(stiffness=100, damping=12, mass=1)", "# Same timestamp → same state, at any frame rate."],
    )
    return shot.finish()


def build_shots():
    return introduction(), comparison(), position(), transforms(), stagger(), finale()


def build_video():
    return Sequence(*(shot.scene for shot in build_shots()))


STORYBOARD = tuple(
    StoryboardSample(time, title)
    for time, title in (
        (0.9, "meet the spring"),
        (3.6, "spring response"),
        (5.96, "damping / overshoot"),
        (8.4, "damping / at rest"),
        (14.8, "position / in flight"),
        (16.5, "position / landed"),
        (22.0, "scale and rotation"),
        (24.3, "transform replay"),
        (29.98, "staggered arrivals"),
        (32.2, "stagger / settled"),
        (38.8, "all three transforms"),
        (44.9666666667, "last encoded frame"),
    )
)


def check(shots=None):
    """Audit timing, all visible bounds and the actual spring property tracks."""
    shots = shots or build_shots()
    video = Sequence(*(shot.scene for shot in shots))
    assert math.isclose(video.duration, TOTAL_DURATION, abs_tol=1e-9)
    minimum = float("inf")
    checked = spring_tracks = 0
    peak_samples = {}
    for shot, (_, start, end) in zip(shots, CHAPTERS):
        assert shot.scene.duration == end - start
        assert not shot.scene.audio
        entries = {
            entry.component.training_id: entry
            for entry in shot.scene.entries
            if hasattr(entry.component, "training_id")
        }
        for entry in shot.scene.entries:
            for track in entry.tracks:
                assert 0 <= track.start < track.start + track.duration <= shot.duration
                if isinstance(track.easing, Spring):
                    spring_tracks += 1
                    assert track.property in {"position", "scale", "rotation"}
        for visual in shot.visuals:
            # Each root reserves all its children. Sample only its own geometry
            # changes; unrelated tracks cannot alter this root's bounds.
            entry = entries[visual.training_id]
            samples = {entry.start, shot.duration}
            for track in entry.tracks:
                samples.update((track.start, track.start + track.duration))
                if track.property in {"position", "scale", "rotation"}:
                    samples.update(track.start + track.duration * i / 32 for i in range(33))
                if isinstance(track.easing, Spring):
                    if track.easing not in peak_samples:
                        # Locate the early peak on a dense numerical grid, then
                        # inspect its neighborhood as well as regular samples.
                        peak = max(range(4097), key=lambda i: track.easing(i / 4096))
                        peak_samples[track.easing] = tuple(
                            i / 4096 for i in range(max(0, peak - 4), min(4096, peak + 4) + 1)
                        )
                    samples.update(track.start + track.duration * u for u in peak_samples[track.easing])
            cache = {}
            for time in sorted(samples):
                state = entry.state_at(time)
                if time < entry.start or state["opacity"] < 1e-6:
                    continue
                key = (state["position"], state["scale"], state["rotation"])
                if key not in cache:
                    cache[key] = shot.scene.bounds_at(visual, time)
                bounds = cache[key]
                clearance = min(bounds.left, bounds.top, WIDTH - bounds.right, HEIGHT - bounds.bottom)
                if clearance < 5:
                    raise AssertionError(f"{start + time:.4f}s: {type(visual).__name__} exceeds margin: {bounds}")
                minimum = min(minimum, clearance)
                checked += 1
    return {
        "duration_seconds": video.duration,
        "audio_tracks": 0,
        "canvas": [WIDTH, HEIGHT],
        "chapters": [{"title": name, "start": start, "end": end} for name, start, end in CHAPTERS],
        "spring_tracks": spring_tracks,
        "bounds_checked": checked,
        "minimum_canvas_clearance_px": round(minimum, 3),
        "verification": "structural and sampled layout; media verification is separate",
    }
