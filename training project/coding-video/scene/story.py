"""Tutorial composition only; all editor rendering lives in faceless_champ."""

# These chapter helpers are called immediately; no closures escape the loop.
# ruff: noqa: B023
from __future__ import annotations

import ast
import textwrap
from pathlib import Path

from faceless_champ import (
    Arrow,
    Canvas,
    CodeReveal,
    CodeTheme,
    CodingChamp,
    CueScene,
    FadeIn,
    Group,
    Layer,
    Number,
    Polyline,
    ProgressBar,
    Rectangle,
    Scene,
    Sequence,
    SubtitleTrack,
    Text,
    linear,
)
from faceless_champ.coding import MONO_FONT

PROJECT = Path(__file__).resolve().parents[1]
CHAPTERS = (
    ("players", 1, 52),
    ("blueprint", 52, 88),
    ("constructor", 88, 140),
    ("attributes", 140, 190),
    ("methods", 190, 254),
    ("encapsulation", 254, 279),
    ("instances", 279, 335),
    ("actions", 335, 374),
    ("recap", 374, None),
)


def source_parts():
    source = (PROJECT / "class.py").read_text()
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Player")
    result = {"class": ast.get_source_segment(source, cls)}
    for method in cls.body:
        if isinstance(method, ast.FunctionDef):
            # Source spans begin at `def`; dedent complete physical lines instead.
            result[method.name] = textwrap.dedent("\n".join(source.splitlines()[method.lineno - 1 : method.end_lineno]))
    result["calls"] = [ast.get_source_segment(source, n) for n in tree.body if n is not cls]
    return result


def build_video(theme="midnight"):
    colors = CodeTheme.named(theme)
    canvas = Canvas(1920, 1080, "#080E1B" if theme != "paper" else "#E9EFF6")
    track = SubtitleTrack.from_srt(PROJECT / "cue-per-word.srt")
    narration = Scene(Canvas(1920, 1080, "#00000000"))
    narration.add_audio(PROJECT / "audio.mp3", start=0)
    duration = narration.duration
    parts = source_parts()
    events, scenes = [], []
    accent, green = colors.accent, ("#A6DA95" if theme != "paper" else "#287537")
    text_color = colors.foreground

    def label(text, x, y, size=32, color=None):
        return Text(text, font=MONO_FONT, font_size=size, color=color or text_color, position=(x, y))

    def box(x, y, w, h, color=None):
        return Rectangle(
            width=w,
            height=h,
            corner_radius=18,
            fill=colors.background,
            stroke=color or colors.chrome,
            stroke_width=2,
            position=(x, y),
        )

    def card(name, x=1580, y=330, health=100):
        num = Number(
            health, suffix=" HP", font=MONO_FONT, font_size=44, color=text_color, width=260, position=(x, y + 5)
        )
        bar = ProgressBar(
            width=380,
            height=18,
            progress=health / 100,
            color=accent if name == "Alex" else green,
            track_color=colors.chrome,
            position=(x, y + 76),
        )
        group = Group(box(x, y, 480, 230), label(name, x, y - 65, 34), num, bar)
        return group, num, bar

    def editor(
        code,
        *,
        mode="typewriter",
        highlights=(),
        blocks=None,
        x=660,
        y=520,
        w=1200,
        h=840,
        size=36,
        filename="class.py",
        language="python",
    ):
        return CodingChamp(
            code,
            language=language,
            theme=colors,
            width=w,
            height=h,
            font_size=size,
            filename=filename,
            highlighted_lines=highlights,
            reveal_mode=mode,
            block_ends=blocks,
            position=(x, y),
        )

    for name, first, following in CHAPTERS:
        start = 0 if first == 1 else track.cue(first).start
        end = track.cue(following).start if following else duration
        scene = CueScene(track, canvas, start_time=start, end_time=end)
        removals = []

        def at(cue):
            return track.cue(cue).start

        def put(component, cue=None, *, until=None, seconds=0.35, reveal=False, p0=0, p1=1):
            when = start if cue is None else at(cue)
            stop = end if until is None else at(until)
            if not when < stop or when + seconds > stop + 1e-9:
                raise ValueError(f"Invalid authored window: {name} / cue {cue}")
            with scene.at(when - start):
                scene.play(CodeReveal(component, p0, p1) if reveal else FadeIn(component), run_time=seconds)
            if until is not None:
                removals.append((stop - start, component))
            events.append(
                {
                    "chapter": name,
                    "cue": cue or first,
                    "start": when,
                    "end": stop,
                    "motion_end": when + seconds,
                    "kind": type(component).__name__,
                }
            )
            return component

        def reveal_more(component, cue, stop_cue, p0, p1, seconds=0.65):
            when, stop = at(cue), at(stop_cue)
            motion_end = min(stop, when + seconds)
            with scene.at(when - start):
                scene.play(CodeReveal(component, p0, p1), run_time=motion_end - when)
            events.append(
                {
                    "chapter": name,
                    "cue": cue,
                    "start": when,
                    "end": stop,
                    "motion_end": motion_end,
                    "kind": "CodeReveal",
                }
            )

        def connect(cue, y, text="self", until=None):
            put(Arrow((1260, y), (1330, y), stroke=accent, stroke_width=5), cue, until=until)
            if text:
                put(label(text, 1295, y - 30, 22, accent), cue, until=until)

        if name == "players":
            a, _, _ = card("Alex", 680, 430)
            b, _, _ = card("Sam", 1240, 430)
            put(a, until=26)
            put(b, 9, until=26)
            put(
                editor(
                    'name = "Alex"\nhealth = 100\n\ntake_damage(30)\nheal(15)', x=960, y=530, w=1420, h=740, size=42
                ),
                26,
                until=48,
                reveal=True,
                seconds=1.2,
            )
            for i in range(3):
                put(label(f"player_{i + 3}.health = 100", 960, 710 + i * 62, 30, colors.muted), 31 + i, until=48)
            put(
                editor(
                    "class Player:\n    name\n    health\n\n    take_damage(...)\n    heal(...)",
                    x=960,
                    y=530,
                    w=1420,
                    h=740,
                    size=42,
                ),
                48,
                reveal=True,
                seconds=1.1,
            )
        elif name == "blueprint":
            blueprint = Group(
                box(500, 480, 520, 500, accent),
                Rectangle(width=310, height=270, fill=None, stroke=accent, stroke_width=3, position=(500, 490)),
                Rectangle(width=90, height=130, fill=None, stroke=accent, stroke_width=3, position=(470, 555)),
                label("blueprint", 500, 320, 32, accent),
            )
            put(blueprint, until=82)
            for i, cue in enumerate((67, 78)):
                x = 1180 + i * 450
                house = Group(
                    Polyline([(x - 140, 440), (x, 310), (x + 140, 440)], stroke=accent, stroke_width=6),
                    Rectangle(
                        width=240, height=230, fill=colors.background, stroke=accent, stroke_width=3, position=(x, 570)
                    ),
                    Rectangle(width=60, height=115, fill=colors.chrome, stroke=None, position=(x, 627)),
                )
                put(house, cue, until=82)
            put(Arrow((790, 500), (1000, 500), stroke=accent, stroke_width=5), 75, until=82)
            put(editor("class Player:\n    ...", x=620, y=500, w=1040, h=400, size=52), 82)
            put(card("Alex", y=350)[0], 82)
            put(card("Sam", y=670)[0], 82)
        elif name == "constructor":
            code = "class Player:\n    " + parts["__init__"].splitlines()[0]
            panel = editor(code, size=42)
            cut = len("class Player:") / len(code)
            put(panel, 88, reveal=True, seconds=0.01, p1=0)
            keyword = len("class") / len(code)
            reveal_more(panel, 99, 100, 0, keyword, seconds=0.5)
            reveal_more(panel, 100, 104, keyword, cut, seconds=1.4)
            reveal_more(panel, 104, 114, cut, 1, seconds=3.0)
            put(label("__init__", 1580, 355, 44, accent), 112)
            put(editor('Player("Alex")', x=1580, y=560, w=480, h=160, size=28), 124, reveal=True, seconds=0.6)
            put(label("→  Alex", 1580, 750, 38), 130)
        elif name == "attributes":
            code = "class Player:\n" + textwrap.indent(parts["__init__"], "    ")
            panel = editor(code, size=39, highlights=(3, 4), mode="word")
            put(panel, reveal=True, seconds=2.5)
            put(card("Alex")[0], 146)
            put(card("Sam", y=660)[0], 170)
            connect(159, 330)
            connect(178, 660)
            put(label("self.name     self.health", 660, 830, 32, accent), 158)
        elif name == "methods":
            put(editor(parts["class"], size=32), until=198)
            for key, cue, until in [("take_damage", 198, 232), ("heal", 232, 242), ("show_status", 242, None)]:
                code = "class Player:\n\n" + textwrap.indent(parts[key], "    ")
                panel = editor(code, mode="block", blocks=(3, 4), highlights=(4,), size=34)
                put(panel, cue, until=until, reveal=True, seconds=0.5, p1=0.5)
                action_cue = {"take_damage": 218, "heal": 239, "show_status": 249}[key]
                reveal_more(panel, action_cue, {"take_damage": 232, "heal": 242, "show_status": 254}[key], 0.5, 1)
                put(
                    label(
                        {"take_damage": "health − amount", "heal": "health + amount", "show_status": "Alex: 85 HP"}[
                            key
                        ],
                        1580,
                        530,
                        30,
                        accent,
                    ),
                    action_cue,
                    until=until,
                )
        elif name == "encapsulation":
            put(editor(parts["class"], size=32, highlights=(3, 4, 7, 10, 13)), reveal=True, seconds=1.0)
            put(label("name · health", 1580, 370, 30, accent), 261)
            put(label("take_damage()", 1580, 520, 30), 264)
            put(label("heal()", 1580, 620, 30), 266)
            put(label("show_status()", 1580, 720, 30), 270)
        elif name == "instances":
            put(editor(parts["class"], size=32), until=284)
            code = "\n\n".join(parts["calls"][:2])
            panel = editor(code, mode="word", size=40)
            half = 0.5
            put(panel, 284, reveal=True, seconds=5.5, p1=half)
            put(card("Alex")[0], 296)
            reveal_more(panel, 318, 324, half, 1, seconds=2.0)
            put(card("Sam", y=660)[0], 323)
            connect(324, 330, "")
            connect(330, 660, "")
        elif name == "actions":
            a, an, ab = card("Alex")
            b, bn, bb = card("Sam", y=620)
            put(a)
            put(b)
            calls = parts["calls"]
            ordered = [calls[2], calls[4], calls[3], *calls[5:]]
            panel = editor("\n\n".join(ordered), mode="block", blocks=(2, 4, 6, 8, 9), size=34)
            put(panel, reveal=True, seconds=0.6, p1=0.2)
            for cue, stop, p0, p1 in [(345, 350, 0.2, 0.4), (355, 359, 0.4, 0.6), (364, 369, 0.6, 1)]:
                reveal_more(panel, cue, stop, p0, p1)
            for cue, stop_cue, number, bar, health in [
                (342, 344, an, ab, 70),
                (353, 354, an, ab, 85),
                (360, 363, bn, bb, 90),
            ]:
                with scene.at_cue(cue):
                    scene.play(
                        number.animate.value_to(health),
                        bar.animate.progress_to(health / 100),
                        run_time=at(stop_cue) - at(cue),
                        rate_func=linear,
                    )
            put(
                editor(
                    "Alex: 85 HP\nSam: 90 HP", language="text", filename="output", x=1580, y=870, w=480, h=200, size=28
                ),
                371,
                reveal=True,
                seconds=0.6,
            )
        else:
            code = parts["class"]
            phases = [
                (374, 392, (1,)),
                (392, 402, (2,)),
                (402, 407, (3, 4)),
                (407, 412, (6, 9, 12)),
                (412, 419, (3, 4, 7, 10, 13)),
                (419, None, ()),
            ]
            for cue, until, highlights in phases:
                put(editor(code, size=32, highlights=highlights), cue, until=until, seconds=0.2)
            put(card("Alex", health=85)[0])
            put(card("Sam", y=660, health=90)[0])
            connect(412, 330)
            connect(417, 660)
        for local_end, component in removals:
            with scene.at(local_end):
                scene.remove(component)
        scene.finish()
        scenes.append(scene)
    composition = Layer(Sequence(*scenes), narration, canvas=canvas)
    report = {
        "cue_count": len(track.cues),
        "cue_end": track.duration,
        "duration": duration,
        "chapters": [
            {"id": name, "start": s.start_time, "end": s.end_time} for (name, _, _), s in zip(CHAPTERS, scenes)
        ],
        "events": events,
        "full_export_verified": False,
        "theme": theme,
        "final_health": {"Alex": 85, "Sam": 90},
    }
    return composition, report
