"""A word-cue-driven math story in the visual language of layout.png.

Edit BEATS to change the story. All cue numbers refer to cue-per-word.srt;
the timing comes from that file, rather than accumulated animation durations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from faceless_champ import (
    Arrow,
    BounceIn,
    Canvas,
    Captions,
    Circle,
    Draw,
    FadeIn,
    FadeOut,
    Icon,
    PopIn,
    PopOut,
    Pulse,
    Scene,
    Shake,
    SlideIn,
    SlideOut,
    SpinIn,
    SubtitleTrack,
    Text,
    Typewriter,
    Wiggle,
    ZoomIn,
    ZoomOut,
    linear,
)

PROJECT = Path(__file__).resolve().parents[1]
ASSETS = PROJECT.parents[1] / "assets"
FONT = ASSETS / "fonts" / "CormorantGaramond[wght].ttf"
ITALIC = ASSETS / "fonts" / "CormorantGaramond-Italic[wght].ttf"

PAPER = "#faf7f2"
INK = "#282622"
MUTED = "#716b64"
ORANGE = "#e86d35"
GREEN = "#4d6e50"
PALE_GREEN = "#d2ddca"
CENTER = (960, 510)
ENTRANCES = ("pop", "slide", "zoom", "bounce", "spin", "typewriter", "fade")
EXITS = ("fade", "slide", "zoom", "pop")
EMPHASES = ("pulse", "wiggle", "scale", "shake", "move", "rotate", "opacity")
EXIT_DURATION = 0.22
SLOTS = {
    "upper_left": (395, 350),
    "upper_right": (1525, 350),
    "lower_left": (420, 740),
    "lower_right": (1500, 740),
    "bottom": (960, 805),
}


@dataclass(frozen=True)
class Node:
    cue: int
    slot: str
    label: str
    icon: str | None = None
    symbol: str | None = None
    color: str = INK


@dataclass(frozen=True)
class Beat:
    cue: int
    title: str
    core: str
    subtitle: str
    nodes: tuple[Node, ...]
    color: str = ORANGE
    core_icon: bool = False
    subtitle_cue: int | None = None


BEATS = (
    Beat(
        1,
        "a fixed belief",
        "math?",
        "a student’s story",
        (
            Node(4, "upper_left", "a student", icon="person"),
            Node(6, "upper_right", "a fixed belief", icon="psychology"),
            Node(9, "bottom", "“I’m terrible at math.”", icon="help", color=ORANGE),
        ),
    ),
    Beat(
        12,
        "the old habit",
        "x² + 3x = ?",
        "a difficult problem",
        (
            Node(17, "upper_left", "a difficult problem", icon="calculate"),
            Node(21, "upper_right", "stare at it", icon="visibility"),
            Node(25, "bottom", "only 30 seconds", icon="timer", color=ORANGE),
        ),
    ),
    Beat(
        27,
        "the shortcut",
        "menu_book",
        "look at the solution",
        (
            Node(32, "upper_left", "the answer", icon="calculate"),
            Node(39, "upper_right", "recognize the steps", icon="visibility"),
            Node(44, "bottom", "“Oh, that makes sense.”", icon="lightbulb", color=ORANGE),
        ),
        core_icon=True,
    ),
    Beat(
        46,
        "the next day",
        "?",
        "the same problem",
        (
            Node(48, "upper_left", "the next day", icon="event_repeat"),
            Node(51, "upper_right", "still can’t solve it", icon="close", color=ORANGE),
            Node(54, "bottom", "recognizing ≠ solving", icon="calculate"),
        ),
    ),
    Beat(
        56,
        "a teacher’s advice",
        "one rule",
        "a different way to learn",
        (
            Node(60, "upper_left", "his teacher", icon="school"),
            Node(65, "upper_right", "one simple rule", icon="edit", color=ORANGE),
            Node(66, "bottom", "pause before the answer", icon="hourglass_empty"),
        ),
    ),
    Beat(
        68,
        "the ten-minute rule",
        "10",
        "minutes",
        (
            Node(69, "upper_left", "before looking", icon="visibility"),
            Node(73, "upper_right", "stay with the problem", icon="calculate", color=ORANGE),
            Node(78, "lower_left", "give it ten minutes", icon="timer"),
            Node(85, "lower_right", "try it yourself", icon="edit", color=GREEN),
        ),
    ),
    Beat(
        86,
        "the messy middle",
        "try",
        "even when it feels useless",
        (
            Node(92, "upper_left", "this feels useless", icon="hourglass_empty"),
            Node(95, "upper_right", "make mistakes", icon="close", color=ORANGE),
            Node(98, "lower_left", "try different ideas", icon="lightbulb"),
            Node(103, "lower_right", "take a wrong path", icon="route"),
        ),
    ),
    Beat(
        104,
        "something starts to change",
        "psychology",
        "the mind starts connecting",
        (
            Node(106, "upper_left", "something changes", icon="trending_up", color=GREEN),
            Node(111, "upper_right", "pay closer attention", icon="visibility"),
            Node(113, "bottom", "notice patterns", symbol="pattern", color=GREEN),
        ),
        color=GREEN,
        core_icon=True,
    ),
    Beat(
        114,
        "from impossible to familiar",
        "familiar",
        "one connection at a time",
        (
            Node(118, "upper_left", "ask better questions", icon="help", color=GREEN),
            Node(120, "upper_right", "meet the problem again", icon="calculate"),
            Node(124, "lower_left", "once impossible", symbol="?", color=MUTED),
            Node(127, "lower_right", "now familiar", icon="check", color=GREEN),
        ),
        color=GREEN,
    ),
    Beat(
        128,
        "what he understood",
        "≠",
        "seeing isn’t solving",
        (
            Node(132, "upper_left", "getting better at math", icon="trending_up", color=GREEN),
            Node(138, "upper_right", "seeing more solutions", icon="menu_book"),
            Node(140, "bottom", "recognition alone isn’t enough", icon="visibility", color=ORANGE),
        ),
    ),
    Beat(
        141,
        "think before you look",
        "think",
        "before you see the solution",
        (
            Node(143, "upper_left", "spend more time", icon="schedule"),
            Node(148, "upper_right", "think it through", icon="psychology", color=GREEN),
            Node(152, "bottom", "then look at the answer", icon="menu_book"),
        ),
    ),
    Beat(
        153,
        "the lesson",
        "struggle",
        "is the learning.",
        (
            Node(155, "upper_left", "mathematics", icon="calculate"),
            Node(159, "upper_right", "stay with it", icon="timer", color=ORANGE),
            Node(164, "lower_left", "make connections", symbol="pattern", color=GREEN),
            Node(170, "lower_right", "keep growing", symbol="tree", color=GREEN),
        ),
        subtitle_cue=168,
    ),
)


class GoodMath(Scene):
    def __init__(self, *, captions: bool = True) -> None:
        super().__init__(Canvas(1920, 1080, PAPER))
        self.show_captions = captions
        self.transcript = SubtitleTrack.from_srt(PROJECT / "cue-per-word.srt")
        self.beat_times: list[dict] = []
        self.animation_events: list[dict] = []

    def text(self, words, position, *, size=44, color=INK, italic=False):
        return Text(
            words,
            font=ITALIC if italic else FONT,
            font_size=size,
            color=color,
            position=position,
            align="center",
            spacing=8,
        )

    def icon(self, name, position, *, size=112, color=INK):
        return Icon(ASSETS / "icons" / f"{name}.png", size=size, color=color, position=position)

    def log_motion(self, components, time, duration, phase, effects):
        self.animation_events.append(
            {
                "time": round(time, 6),
                "duration": round(duration, 6),
                "phase": phase,
                "effects": sorted(set(effects)),
                "components": [c.text if isinstance(c, Text) else type(c).__name__ for c in components],
            }
        )

    def reveal(self, components, time, *, duration=0.24, draw=False, style="fade", direction="up"):
        animations, names = [], []
        factories = {"fade": FadeIn, "pop": PopIn, "zoom": ZoomIn, "bounce": BounceIn, "spin": SpinIn}
        for component in components:
            if draw:
                animations.append(Draw(component))
                names.append("Draw")
            elif style == "typewriter" and isinstance(component, Text):
                animations.extend((FadeIn(component), Typewriter(component)))
                names.extend(("FadeIn", "Typewriter"))
            elif style == "slide":
                animations.append(SlideIn(component, direction=direction, distance=72))
                names.append("SlideIn")
            else:
                factory = factories.get(style, ZoomIn if style == "typewriter" else None)
                if factory is None:
                    raise ValueError(f"Unknown entrance: {style}")
                animations.append(
                    factory(component, angle=-10 if isinstance(component, Text) else -35)
                    if factory is SpinIn
                    else factory(component)
                )
                names.append(factory.__name__)
        with self.at(time):
            self.play(*animations, run_time=duration, rate_func=linear if draw else None)
        self.log_motion(components, time, duration, "entrance", names)

    def emphasize(self, components, time, *, style="pulse", duration=0.6):
        factories = {"pulse": Pulse, "shake": Shake, "wiggle": Wiggle}
        with self.at(time):
            if style in factories:
                factory = factories[style]
                self.play(*(factory(c) for c in components), run_time=duration)
                names = [factory.__name__]
            else:

                def target(component, outward):
                    if style == "scale":
                        return component.animate.scale_to(component.scale * (1.09 if outward else 1))
                    if style == "move":
                        x, y = component.position
                        return component.animate.move_to(x, y - 16 if outward else y)
                    if style == "rotate":
                        return component.animate.rotate_to(component.rotation + (7 if outward else 0))
                    if style == "opacity":
                        return component.animate.opacity_to(component.opacity * (0.55 if outward else 1))
                    raise ValueError(f"Unknown emphasis: {style}")

                self.play(*(target(c, True) for c in components), run_time=duration / 2)
                self.play(*(target(c, False) for c in components), run_time=duration / 2)
                names = [
                    {"scale": "scale_to", "move": "move_to", "rotate": "rotate_to", "opacity": "opacity_to"}[style]
                ]
        self.log_motion(components, time, duration, "emphasis", names)

    def disappear(self, components, time, *, style="fade", direction="down"):
        factories = {"fade": FadeOut, "zoom": ZoomOut, "pop": PopOut}
        animations = (
            [SlideOut(c, direction=direction, distance=50) for c in components]
            if style == "slide"
            else [factories[style](c) for c in components]
        )
        with self.at(time):
            self.play(*animations, run_time=EXIT_DURATION)
            self.remove(*components)
        self.log_motion(
            components, time, EXIT_DURATION, "exit", ["SlideOut" if style == "slide" else factories[style].__name__]
        )

    def node_components(self, node, core_margin):
        x, y = SLOTS[node.slot]
        components = []
        if node.icon:
            components.append(self.icon(node.icon, (x, y), color=node.color))
        elif node.symbol == "pattern":
            # The reference's dot cluster becomes a small pattern diagram.
            for row, count in enumerate((1, 2, 3)):
                for col in range(count):
                    components.append(
                        Circle(9, fill=node.color, stroke=None, position=(x - 32 + col * 32, y - 32 + row * 32))
                    )
        elif node.symbol == "tree":
            components.extend(
                (
                    Circle(40, fill=PALE_GREEN, stroke=GREEN, stroke_width=3, position=(x, y - 10)),
                    Arrow((x, y + 75), (x, y + 15), tip_size=1, stroke=INK, stroke_width=4),
                )
            )
        else:
            components.append(self.text(node.symbol or "?", (x, y), size=100, color=node.color, italic=True))
        components.append(self.text(node.label, (x, y + 84), size=42, color=node.color))
        # Short spokes with whitespace at both ends reproduce the reference.
        direction = -1 if "left" in node.slot else 1
        if node.slot.startswith("upper"):
            start = (960 + direction * core_margin, 480)
            end = (960 + direction * (core_margin + 110), 435)
        elif node.slot.startswith("lower"):
            start = (960 + direction * 160, 660)
            end = (960 + direction * 270, 710)
        else:
            start, end = (960, 665), (960, 725)
        arrow = Arrow(start, end, tip_size=20, stroke=MUTED, stroke_width=3)
        return components, arrow

    def ornaments(self):
        circle = Circle(31, stroke=ORANGE, stroke_width=4, position=(277, 86))
        self.reveal([circle], 0, duration=0.5, draw=True)
        self.reveal(
            [
                self.text("π", (342, 84), size=40, italic=True),
                self.text("a problem worth staying with", (299, 150), size=28, color=MUTED),
                self.text("good at math", (960, 85), size=36, color=INK, italic=True),
                self.text("a mind still growing", (1615, 145), size=28, color=MUTED),
            ],
            0,
            duration=0.65,
            style="typewriter",
        )
        # A minimal rising line in the same position as the reference's e curve.
        self.reveal(
            [Arrow((1558, 104), (1641, 65), tip_size=1, stroke=ORANGE, stroke_width=4)], 0, duration=0.55, draw=True
        )
        self.reveal([self.text("e", (1675, 84), size=42, italic=True)], 0, duration=0.55, style="spin")

    def construct(self):
        for path in (
            FONT,
            ITALIC,
            *(ASSETS / "icons" / f"{beat.core}.png" for beat in BEATS if beat.core_icon),
            *(ASSETS / "icons" / f"{node.icon}.png" for beat in BEATS for node in beat.nodes if node.icon),
        ):
            if not path.is_file():
                raise FileNotFoundError(f"Missing asset {path}. Run good-math/download_assets.py once.")
        self.add_audio(PROJECT / "audio.mp3", start=0)
        self.ornaments()
        if self.show_captions:
            with self.at(0):
                self.add(
                    Captions(
                        self.transcript,
                        font=FONT,
                        font_size=43,
                        width=1520,
                        position=(960, 1008),
                        color=INK,
                        highlight_color=ORANGE,
                        future_color="#99918a",
                        max_words=7,
                        max_duration=3,
                        z_index=20,
                    )
                )

        final_end = self.transcript.duration + 0.9
        for number, beat in enumerate(BEATS, 1):
            start = self.transcript.cue(beat.cue).start
            end = self.transcript.cue(BEATS[number].cue).start if number < len(BEATS) else final_end
            objects = []
            entrance = ENTRANCES[(number - 1) % len(ENTRANCES)]
            exit_style = EXITS[(number - 1) % len(EXITS)]
            emphasis = EMPHASES[(number - 1) % len(EMPHASES)]
            title = self.text(f"{number:02d} / {beat.title}", (960, 175), size=27, color=MUTED)
            core = (
                self.icon(beat.core, CENTER, size=154, color=beat.color)
                if beat.core_icon
                else self.text(
                    beat.core, CENTER, size=96 if len(beat.core) > 10 else 140, color=beat.color, italic=True
                )
            )
            subtitle = self.text(beat.subtitle, (960, 609), size=46, color=INK)
            objects.extend([title, core, subtitle])
            self.reveal([title], start, duration=0.4, style="slide")
            self.reveal([core], start, duration=0.48, style=entrance)
            subtitle_start = self.transcript.cue(beat.subtitle_cue).start if beat.subtitle_cue else start
            self.reveal([subtitle], subtitle_start, duration=0.4, style=entrance)
            emphasis_time = max(start + 0.6, self.transcript.cue(beat.nodes[0].cue).start)
            self.emphasize([core], emphasis_time, style=emphasis, duration=0.6)
            latest = subtitle_start
            node_motions = []
            for node_number, node in enumerate(beat.nodes):
                time = self.transcript.cue(node.cue).start
                style = ENTRANCES[(number + node_number - 1) % len(ENTRANCES)]
                direction = "right" if "left" in node.slot else ("left" if "right" in node.slot else "up")
                # Short late cues still leave room for their entrance and exit.
                available = end - EXIT_DURATION - time
                duration = min(0.48, available * 0.72)
                if duration <= 0:
                    raise ValueError(f"Cue {node.cue} leaves no time for its entrance")
                core_margin = 270 if not beat.core_icon and len(beat.core) > 6 else 180
                components, arrow = self.node_components(node, core_margin)
                objects.extend([*components, arrow])
                self.reveal(components, time, duration=duration, style=style, direction=direction)
                self.reveal([arrow], time, duration=min(0.32, duration), draw=True)
                attention = (
                    "shake"
                    if node.icon in {"close", "route"}
                    else "wiggle"
                    if node.icon in {"help", "lightbulb"}
                    else "pulse"
                )
                attention_start = time + duration + 0.1
                attention_duration = min(0.6, end - EXIT_DURATION - attention_start - 0.05)
                if attention_duration >= 0.35:
                    self.emphasize(components, attention_start, style=attention, duration=attention_duration)
                else:
                    attention = None
                node_motions.append({"entrance": style, "duration": duration, "emphasis": attention})
                latest = max(latest, time)
            if number < len(BEATS):
                # End exactly on the next cue, without cumulative timeline drift.
                self.disappear(objects, end - EXIT_DURATION, style=exit_style)
            self.beat_times.append(
                {
                    "number": number,
                    "title": beat.title,
                    "cue": beat.cue,
                    "start": start,
                    "end": end,
                    "entrance": entrance,
                    "emphasis": emphasis,
                    "exit": exit_style if number < len(BEATS) else None,
                    "preview": min(end - EXIT_DURATION - 0.05, latest + 0.65),
                    "nodes": [
                        {
                            "cue": n.cue,
                            "start": self.transcript.cue(n.cue).start,
                            "label": n.label,
                            "slot": n.slot,
                            **motion,
                        }
                        for n, motion in zip(beat.nodes, node_motions)
                    ],
                }
            )
        self.wait_until(final_end)
