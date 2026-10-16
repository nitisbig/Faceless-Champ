"""Complete, source-clock Python lesson in the approved coding tutorial design.

The supplied word cues are the clock. Code and shell output are authored visuals;
building, checking and rendering this scene never execute the displayed programs.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

from facelesschamp_kit import CodingTutorialStyle, CodingTutorialTemplate
from PIL import ImageFont

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Animation,
    Circle,
    CodeReveal,
    CodingChamp,
    FlowScript,
    Rectangle,
    Scene,
    SubtitleTrack,
    Text,
    linear,
    smooth,
)

ROOT = Path(__file__).resolve().parent
STATUS = "full-length-authored"
OPENING_DURATION = 14.96
# ffprobe duration of the hash-checked supplied MP3. The last SRT cue ends
# 104 ms later, so retain that final visual hold without trimming the audio.
AUDIO_DURATION = 131.016
CUES = SubtitleTrack.from_srt(ROOT / "cue-per-word.srt", overlap_tolerance=0.001)
DURATION = CUES.duration
CANVAS_SIZE = (1920, 1080)
STYLE_PATH = ROOT / "templates/coding-tutorial/style.json"
SOURCE = 'print("Hello World")'
OUTPUT = "Hello World"
CHANGED_SOURCE = 'print("I\'m learning Python")'
MATH_SOURCE = "print(5 + 3)"
RECAP_SOURCE = f"{SOURCE}\n{CHANGED_SOURCE}\n{MATH_SOURCE}"
VARIABLE_SOURCE = 'message = "Hello World"\nprint(message)'
TIMES = {
    "intro_exit": 3.78,
    "editor_in": 4.10,
    "typing": 7.76,
    "split": 9.79,
    "terminal_in": 10.60,
    "signal": 11.20,
    "output": 12.99,
    "hold": 13.76,
}
CHAPTERS = (
    (0.0, "Opening / goal"),
    (14.96, "Open the editor and create hello.py"),
    (28.65, "Write the first program"),
    (39.65, "Function, parentheses and string"),
    (64.16, "Save and run the file"),
    (83.11, "Change the message and run again"),
    (91.92, "Numbers and calculations"),
    (113.84, "Instructions, execution and recap"),
    (124.96, "Next lesson: variables"),
)
INPUT_SHA256 = {
    "audio.mp3": "cd5764b59b939230a4112116f793013e476029d1511c873bf452ebdff9533002",
    "cue-per-word.srt": "6ed87164415c77d24bc3ccd47d76d7c51cd8e208973a741803b802fbb0741842",
    "normal-subtitle.srt": "a9bc26e35d22306ef56ea1e64eac3e7d6e8561f85ea84885b65e33b4d3f73e94",
}


def _fade(scene, component, at, duration, opacity):
    with scene.at(at):
        scene.play(component.animate.opacity_to(opacity), run_time=duration, rate_func=smooth)


def _opening(template):
    """Keep the approved opening design and timing, with explicit reveal holds."""
    workspace = template.workspace
    scene = Scene(template.canvas())
    emblem = template.emblem()
    finder = template.finder("hello.py", SOURCE, folder="Python")
    editor, code, caret = template.editor(SOURCE, filename="hello.py")
    terminal, output = template.terminal(OUTPUT)
    terminal_box = workspace.terminal_bounds
    flow = template.flow()

    scene.add(emblem, finder)
    with scene.at(0):
        scene.play(emblem.animate.move_to(370, 540).scale_to(1), run_time=0.85, rate_func=template.icon_spring)
    _fade(scene, emblem, 0, 0.45, 1)
    with scene.at(0.30):
        scene.play(finder.animate.move_to(1240, 540).scale_to(0.80), run_time=0.90, rate_func=template.window_spring)
    _fade(scene, finder, 0.30, 0.50, 1)
    for item in (emblem, finder):
        _fade(scene, item, TIMES["intro_exit"], 0.28, 0)
    with scene.at(TIMES["editor_in"]):
        scene.add(editor)
        scene.play(
            editor.animate.move_to(*workspace.editor_full.center).scale_to(1),
            run_time=0.80,
            rate_func=template.window_spring,
        )
    _fade(scene, editor, TIMES["editor_in"], 0.50, 1)
    with scene.at(TIMES["editor_in"]):
        scene.play(CodeReveal(code, end=0), run_time=0.000001)
    for at, opacity in ((5.10, 0), (5.60, 1), (6.10, 0), (6.60, 1), (7.26, 0)):
        _fade(scene, caret, at, 0.10, opacity)
    with scene.at(TIMES["typing"]):
        scene.play(CodeReveal(code), run_time=TIMES["split"] - TIMES["typing"])
    with scene.at(TIMES["split"]):
        scene.play(
            editor.animate.move_to(*workspace.editor_split.center).scale_to(workspace.editor_scale),
            run_time=workspace.shrink_duration,
            rate_func=template.window_spring,
        )
    with scene.at(TIMES["terminal_in"]):
        scene.add(terminal)
        scene.play(
            terminal.animate.move_to(*terminal_box.center).scale_to(1),
            run_time=workspace.terminal_entrance_duration,
            rate_func=template.window_spring,
        )
    _fade(scene, terminal, TIMES["terminal_in"], 0.40, 1)
    with scene.at(TIMES["terminal_in"]):
        scene.play(CodeReveal(output, end=0), run_time=0.000001)
    with scene.at(TIMES["signal"]):
        scene.add(flow)
    _fade(scene, flow, TIMES["signal"], 0.30, 1)
    with scene.at(TIMES["output"]):
        scene.play(CodeReveal(output), run_time=TIMES["hold"] - TIMES["output"], rate_func=linear)
    scene.wait_until(OPENING_DURATION)
    return scene, {
        "emblem": emblem,
        "finder": finder,
        "editor": editor,
        "terminal": terminal,
        "code": code,
        "output": output,
        "caret": caret,
        "flow": flow,
    }


def _code(template, source, *, terminal=False, row=0, opacity=0):
    design, unit = template.workspace, template.workspace.unit
    box = design.terminal_bounds if terminal else design.code_bounds
    panel = CodingChamp(
        source,
        language="text" if terminal else "python",
        theme=design.theme,
        chrome=False,
        line_numbers=not terminal,
        font_size=(design.terminal_size if terminal else design.code_size) * unit,
        padding=0 if terminal else 8 * unit,
        width=box.width - 48 * unit if terminal else box.width,
        height=180 * unit if terminal else box.height,
        position=(box.left + 24 * unit, box.top + 112 * unit) if terminal else (box.left, box.top),
        anchor="top_left",
        opacity=opacity,
    )
    if terminal:
        panel.shift(0, row * panel.line_height)
    return panel


def _underline(template, panel, start, end, *, row=0):
    """Measure the same font as CodingChamp so focus follows the actual glyphs."""
    font = ImageFont.truetype(panel.font, round(panel.font_size))
    line = panel.code.splitlines()[row]
    return Rectangle(
        width=max(2, font.getlength(line[start:end])),
        height=3 * template.workspace.unit,
        fill=template.style.accent,
        stroke=None,
        position=(
            panel.position[0] + panel.code_x + font.getlength(line[:start]),
            panel.position[1] + panel.code_y + row * panel.line_height + font.getmetrics()[0] + 5,
        ),
        anchor="top_left",
        opacity=0,
    )


def _reveal(scene, panel, at, end, *, start=0, finish=1):
    with scene.at(at):
        scene.play(CodeReveal(panel, start=start, end=finish), run_time=end - at, rate_func=linear)


def _focus(scene, markers, at, end):
    for marker in markers:
        _fade(scene, marker, at, 0.18, 1)
        _fade(scene, marker, end - 0.18, 0.18, 0)


def _editor_motion(scene, template, editor, at, *, running):
    workspace = template.workspace
    target = workspace.editor_split if running else workspace.editor_full
    with scene.at(at):
        scene.play(
            editor.animate.move_to(*target.center).scale_to(workspace.editor_scale if running else 1),
            run_time=workspace.shrink_duration if running else workspace.restore_duration,
            rate_func=template.window_spring,
        )


def _compose():
    template = CodingTutorialTemplate(CodingTutorialStyle.load(STYLE_PATH))
    workspace, unit = template.workspace, template.workspace.unit
    scene, items = _opening(template)
    roots = [items[name] for name in ("emblem", "finder", "editor", "terminal", "flow")]
    for name in ("editor", "terminal", "flow"):
        _fade(scene, items[name], OPENING_DURATION, 0.35, 0)
    with scene.at(15.31):
        scene.remove(*(items[name] for name in ("editor", "terminal", "flow")))

    # One complete hierarchy carries every code state and focus mark through
    # each full-size / split transition. No independently moving window pieces.
    hello = _code(template, SOURCE, opacity=1)
    changed = _code(template, CHANGED_SOURCE)
    arithmetic = _code(template, MATH_SOURCE)
    recap = _code(template, RECAP_SOURCE)
    variables = _code(template, VARIABLE_SOURCE)
    caret = Rectangle(
        width=3,
        height=46 * unit,
        fill=template.style.accent,
        stroke=None,
        position=(hello.position[0] + hello.code_x, hello.position[1] + hello.code_y + 4),
        anchor="top_left",
    )
    focus = {
        "function": (_underline(template, hello, 0, 5),),
        "parentheses": (_underline(template, hello, 5, 6), _underline(template, hello, 19, 20)),
        "string": (_underline(template, hello, 7, 18),),
        "quotes": (_underline(template, hello, 6, 7), _underline(template, hello, 18, 19)),
        "literal": (_underline(template, hello, 6, 19),),
        "changed_function": (_underline(template, changed, 0, 5),),
        "replace_line": (_underline(template, changed, 0, len(CHANGED_SOURCE)),),
        "left_number": (_underline(template, arithmetic, 6, 7),),
        "operator": (_underline(template, arithmetic, 8, 9),),
        "right_number": (_underline(template, arithmetic, 10, 11),),
        "expression": (_underline(template, arithmetic, 6, 11),),
        "instruction": (_underline(template, arithmetic, 0, len(MATH_SOURCE)),),
        "variable": (_underline(template, variables, 0, 7),),
    }
    untitled = Text(
        "Untitled-1",
        font=CLEAN_FLOW_FONT,
        font_weight=500,
        font_size=26 * unit,
        color=template.style.muted,
        position=(workspace.editor_full.left + 144 * unit, workspace.editor_full.top + 16 * unit),
        anchor="top_left",
    )
    untitled.scale = min(1, 32 * unit / untitled.bounds.height)
    # Include the alternate filename and save indicator before scene ownership.
    saved = Circle(
        4 * unit,
        fill=template.style.accent,
        stroke=None,
        position=(320, workspace.editor_full.top + 32 * unit),
        opacity=0,
    )
    editor = workspace.window(
        workspace.editor_full,
        "hello.py",
        children=(
            hello,
            changed,
            arithmetic,
            recap,
            variables,
            caret,
            untitled,
            saved,
            *(m for group in focus.values() for m in group),
        ),
    )
    editor.position, editor.scale, editor.opacity = (960, 562), 0.96, 0
    editor.heading.opacity = 0
    saved.position = (editor.heading.bounds.right + 18 * unit, editor.bounds_box.top + 32 * unit)

    python = _code(template, "$ python hello.py", terminal=True, opacity=1)
    python3 = _code(template, "$ python3 hello.py", terminal=True)
    hello_result = _code(template, OUTPUT, terminal=True, row=2)
    changed_result = _code(template, "I'm learning Python", terminal=True, row=2)
    math_result = _code(template, "8", terminal=True, row=2)
    recap_result = _code(template, "Hello World\nI'm learning Python\n8", terminal=True, row=2)
    result_mark = _underline(template, math_result, 0, 1)
    terminal = workspace.window(
        workspace.terminal_bounds,
        "Terminal",
        children=(python, python3, hello_result, changed_result, math_result, recap_result, result_mark),
    )
    terminal.position = (workspace.terminal_bounds.center[0], workspace.terminal_bounds.center[1] + 20)
    terminal.scale, terminal.opacity = 0.96, 0
    roots.extend((editor, terminal))

    # Open an empty editor, create the named file, and type with the spoken code.
    with scene.at(CUES.cue(48).start):
        scene.add(editor)
        scene.play(
            editor.animate.move_to(*workspace.editor_full.center).scale_to(1),
            run_time=0.8,
            rate_func=template.window_spring,
        )
    _fade(scene, editor, CUES.cue(48).start, 0.5, 1)
    # Component.state() defaults reveal to 1. Schedule an explicit initial hold;
    # assigning a Python attribute named `reveal` does not seed scene state.
    with scene.at(CUES.cue(48).start):
        scene.play(
            *(
                CodeReveal(panel, start=value, end=value)
                for panel, value in (
                    (hello, 0),
                    (changed, 6 / len(CHANGED_SOURCE)),
                    (arithmetic, 0),
                    (recap, 0),
                    (variables, 0),
                )
            ),
            run_time=0.000001,
        )
    _fade(scene, untitled, CUES.cue(71).start, 0.2, 0)
    _fade(scene, editor.heading, CUES.cue(71).start, 0.3, 1)
    _fade(scene, saved, CUES.cue(71).start, 0.3, 1)
    for at in (17.0, 18.2, 19.4, 20.6, 21.8, 23.0, 24.2, 25.4, 26.6, 27.8, 29.0, 30.2):
        _fade(scene, caret, at, 0.08, 0)
        _fade(scene, caret, at + 0.6, 0.08, 1)
    _fade(scene, caret, CUES.cue(94).start, 0.1, 0)
    for first, last, start, finish in ((94, 94, 0, 7), (95, 95, 7, 13), (96, 96, 13, len(SOURCE))):
        _reveal(
            scene,
            hello,
            CUES.cue(first).start,
            CUES.cue(last).end,
            start=start / len(SOURCE),
            finish=finish / len(SOURCE),
        )

    # Syntax teaching uses in-editor underlines, without explanatory overlays.
    _focus(scene, focus["function"], CUES.cue(118).start, CUES.cue(132).end)
    _focus(scene, focus["parentheses"], CUES.cue(136).start, CUES.cue(145).end)
    _focus(scene, focus["string"], CUES.cue(148).end, CUES.cue(152).end)
    _focus(scene, focus["quotes"], CUES.cue(153).start, CUES.cue(167).end)
    _focus(scene, focus["literal"], CUES.cue(168).start, CUES.cue(184).end)

    def terminal_in(at):
        with scene.at(at):
            scene.play(
                Animation(
                    terminal,
                    {"position": workspace.terminal_bounds.center, "scale": 1},
                    {
                        "position": (workspace.terminal_bounds.center[0], workspace.terminal_bounds.center[1] + 20),
                        "scale": 0.96,
                    },
                ),
                run_time=workspace.terminal_entrance_duration,
                rate_func=template.window_spring,
            )
        _fade(scene, terminal, at, 0.4, 1)

    def close_terminal(at):
        _fade(scene, terminal, at, workspace.terminal_exit_duration, 0)
        _editor_motion(scene, template, editor, at + workspace.terminal_exit_duration, running=False)

    def execution(at, output_at):
        flow = template.flow(
            FlowScript()
            .reveal(("source", "result", "execution"), at=0, duration=0.25)
            .signal("execution", at=0.32, duration=output_at - at - 0.32, marker="capsule", color=template.style.accent)
        )
        with scene.at(at):
            scene.add(flow)
        _fade(scene, flow, at, 0.2, 1)
        _fade(scene, flow, output_at + 0.8, 0.3, 0)
        roots.append(flow)

    _fade(scene, saved, CUES.cue(190).start, 0.3, 0)
    _editor_motion(scene, template, editor, CUES.cue(193).start, running=True)
    with scene.at(68.2):
        scene.add(terminal)
        scene.play(
            *(
                CodeReveal(panel, end=0)
                for panel in (python, python3, hello_result, changed_result, math_result, recap_result)
            ),
            run_time=0.000001,
        )
    terminal_in(68.2)
    _reveal(scene, python, CUES.cue(198).start, CUES.cue(198).end)
    _fade(scene, python, CUES.cue(206).start, 0.15, 0)
    _fade(scene, python3, CUES.cue(206).start, 0.15, 1)
    _reveal(scene, python3, CUES.cue(206).start, CUES.cue(206).end)
    execution(CUES.cue(208).start, CUES.cue(214).start)
    _fade(scene, hello_result, CUES.cue(214).start, 0.1, 1)
    _reveal(scene, hello_result, CUES.cue(214).start, CUES.cue(215).end)

    # Replace the string, keep the function, and show the new result on rerun.
    close_terminal(CUES.cue(228).start)
    _focus(scene, focus["literal"], CUES.cue(232).start, CUES.cue(235).end)
    _fade(scene, hello, CUES.cue(236).start, 0.12, 0)
    _fade(scene, changed, CUES.cue(236).start, 0.12, 1)
    _reveal(scene, changed, CUES.cue(237).start, CUES.cue(239).end, start=6 / len(CHANGED_SOURCE))
    _editor_motion(scene, template, editor, CUES.cue(240).start, running=True)
    _fade(scene, hello_result, CUES.cue(240).start, 0.12, 0)
    terminal_in(88.9)
    _reveal(scene, python3, 88.9, CUES.cue(243).end)
    execution(CUES.cue(240).start + workspace.shrink_duration, CUES.cue(247).start)
    _fade(scene, changed_result, CUES.cue(247).start, 0.1, 1)
    _reveal(scene, changed_result, CUES.cue(247).start, CUES.cue(248).end)

    # A numerical expression is evaluated; it is deliberately shown unquoted.
    close_terminal(CUES.cue(250).start)
    _focus(scene, focus["changed_function"], CUES.cue(255).start, CUES.cue(261).end)
    _focus(scene, focus["replace_line"], CUES.cue(273).start, CUES.cue(275).end)
    _fade(scene, changed, CUES.cue(276).start, 0.12, 0)
    _fade(scene, arithmetic, CUES.cue(276).start, 0.12, 1)
    _reveal(scene, arithmetic, CUES.cue(276).start, CUES.cue(276).end)
    _editor_motion(scene, template, editor, CUES.cue(277).start, running=True)
    _fade(scene, changed_result, CUES.cue(277).start, 0.12, 0)
    terminal_in(103.9)
    _reveal(scene, python3, 103.9, CUES.cue(279).end)
    execution(CUES.cue(277).start + workspace.shrink_duration, CUES.cue(282).start)
    _fade(scene, math_result, CUES.cue(282).start, 0.1, 1)
    _reveal(scene, math_result, CUES.cue(282).start, CUES.cue(282).end)
    _focus(scene, focus["expression"], CUES.cue(283).start, CUES.cue(291).end)
    _focus(scene, focus["left_number"], CUES.cue(294).start, CUES.cue(295).end)
    _focus(scene, focus["operator"], CUES.cue(297).start, CUES.cue(297).end)
    _focus(scene, focus["right_number"], CUES.cue(298).start, CUES.cue(298).end)
    _focus(scene, (result_mark,), CUES.cue(298).end, CUES.cue(304).end)

    # Repeat the instruction → execution → result visual during the recap.
    _focus(scene, focus["instruction"], CUES.cue(313).start, CUES.cue(314).end)
    execution(CUES.cue(314).start, CUES.cue(318).start)
    _focus(scene, (result_mark,), CUES.cue(318).start, CUES.cue(320).end)
    _fade(scene, arithmetic, CUES.cue(321).start, 0.2, 0)
    _fade(scene, recap, CUES.cue(321).start, 0.2, 1)
    _reveal(scene, recap, CUES.cue(321).start, CUES.cue(322).end)
    _fade(scene, math_result, CUES.cue(323).start, 0.15, 0)
    _fade(scene, recap_result, CUES.cue(323).start, 0.15, 1)
    _reveal(scene, recap_result, CUES.cue(323).start, CUES.cue(325).end)

    # The final cue previews the subject of the next tutorial, without running it.
    close_terminal(CUES.cue(330).start)
    _fade(scene, recap, CUES.cue(333).end, 0.2, 0)
    _fade(scene, variables, CUES.cue(334).start, 0.2, 1)
    first_line = len(VARIABLE_SOURCE.splitlines()[0]) / len(VARIABLE_SOURCE)
    _reveal(scene, variables, CUES.cue(334).start, CUES.cue(336).end, finish=first_line)
    _focus(scene, focus["variable"], CUES.cue(337).start, CUES.cue(342).end)
    _reveal(scene, variables, CUES.cue(338).start, CUES.cue(342).end, start=first_line)

    scene.add_audio(ROOT / "audio.mp3", start=0)
    scene.wait_until(DURATION)
    items.update(
        lesson_editor=editor,
        lesson_terminal=terminal,
        hello=hello,
        changed=changed,
        arithmetic=arithmetic,
        recap=recap,
        variables=variables,
        python=python,
        python3=python3,
        hello_result=hello_result,
        changed_result=changed_result,
        math_result=math_result,
        recap_result=recap_result,
        roots=roots,
    )
    return scene, items


def build_scene():
    """Return the entire 131.12-second lesson without rendering or executing code."""
    return _compose()[0]


def check_scene():
    """Audit authored state and measured geometry without rendering scene frames."""
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in INPUT_SHA256}
    if hashes != INPUT_SHA256:
        raise ValueError("The supplied narration or subtitle inputs changed")
    scene, items = _compose()
    assert math.isclose(scene.duration, DURATION, abs_tol=1e-9)
    assert len(scene.audio) == 1 and scene.audio[0].start == 0 and scene.audio[0].trim_start == 0
    assert math.isclose(scene.audio[0].duration, AUDIO_DURATION, abs_tol=1e-6)
    assert scene.audio[0].fade_in == scene.audio[0].fade_out == 0
    assert len(CUES.cues) == 345 and CUES.cue(49).end > CUES.cue(50).start
    allowed_text = {"hello.py", "Untitled-1", "Terminal", ""}
    assert all(entry.component.text in allowed_text for entry in scene.entries if isinstance(entry.component, Text))
    assert items["code"].code == SOURCE and items["output"].code == OUTPUT
    assert all(not node.label for node in items["flow"].graph.nodes)
    assert not any(isinstance(entry.component, Text) and entry.parent is None for entry in scene.entries)

    def visible(component, time):
        entry = scene._objects[component]
        return (
            entry.start <= time
            and (entry.end is None or time < entry.end)
            and all(ancestor.state_at(time)["opacity"] > 0.001 for ancestor in (entry, *entry.ancestors()))
        )

    def overlaps(a, b):
        return min(a.right, b.right) - max(a.left, b.left) > 1 and min(a.bottom, b.bottom) - max(a.top, b.top) > 1

    roots = items["roots"]
    boxes = {}
    minimum_clearance, samples = math.inf, math.ceil(DURATION * 60)
    blank_run = longest_blank_run = 0
    for index in range(samples):
        time = index / 60
        active = []
        for root in roots:
            if not visible(root, time):
                continue
            # Window faces define collision regions; shadows are intentional decoration.
            target = getattr(root, "face", root)
            state = scene._objects[root].state_at(time)
            assert state["scale_x"] == state["scale_y"] == 1
            key = (root, state["position"], state["scale"])
            if key not in boxes:
                boxes[key] = scene.bounds_at(target, time)
            box = boxes[key]
            clearance = min(box.left, box.top, CANVAS_SIZE[0] - box.right, CANVAS_SIZE[1] - box.bottom)
            assert clearance >= 32, (time, clearance)
            minimum_clearance = min(minimum_clearance, clearance)
            active.append(box)
        assert not any(overlaps(a, b) for i, a in enumerate(active) for b in active[i + 1 :]), time
        blank_run = 0 if active else blank_run + 1
        longest_blank_run = max(longest_blank_run, blank_run)
    assert longest_blank_run / 60 < 0.25
    for root in roots:
        if hasattr(root, "diagnostics_at"):
            for local_time in (0, 0.5, 1.8, 3):
                assert not root.diagnostics_at(local_time)

    def reveal_is(name, time, value):
        assert math.isclose(scene._objects[items[name]].state_at(time)["reveal"], value, abs_tol=1e-8), (name, time)

    for name, before, complete in (
        ("code", TIMES["typing"], TIMES["split"]),
        ("output", TIMES["output"], TIMES["hold"]),
        ("hello", CUES.cue(94).start, CUES.cue(96).end),
        ("python", CUES.cue(198).start, CUES.cue(198).end),
        ("hello_result", CUES.cue(214).start, CUES.cue(215).end),
        ("changed_result", CUES.cue(247).start, CUES.cue(248).end),
        ("arithmetic", CUES.cue(276).start, CUES.cue(276).end),
        ("math_result", CUES.cue(282).start, CUES.cue(282).end),
        ("recap_result", CUES.cue(323).start, CUES.cue(325).end),
        ("variables", CUES.cue(334).start, CUES.cue(342).end),
    ):
        reveal_is(name, before, 0)
        reveal_is(name, complete, 1)
    for at in (16, 20, 26, 31.75):
        reveal_is("hello", at, 0)
    reveal_is("code", 6, 0)
    reveal_is("output", 12, 0)
    reveal_is("python", 68.9, 0)
    reveal_is("changed", 86.5, 6 / len(CHANGED_SOURCE))
    reveal_is("changed", CUES.cue(237).start, 6 / len(CHANGED_SOURCE))
    reveal_is("changed", CUES.cue(239).end, 1)
    reveal_is("recap", CUES.cue(329).end, 1)
    assert visible(items["variables"], DURATION - 0.001)
    # Every example is valid Python, without executing any of it.
    for source in (SOURCE, CHANGED_SOURCE, MATH_SOURCE, RECAP_SOURCE, VARIABLE_SOURCE):
        compile(source, "hello.py", "exec")
    for name, at in (("hello_result", 83.1), ("changed_result", 91.9), ("math_result", 119.5)):
        assert visible(items[name], at)
    return {
        "status": STATUS,
        "structural_checks": "passed",
        "duration": DURATION,
        "canvas": list(CANVAS_SIZE),
        "audio_tracks": 1,
        "audio_start": 0,
        "audio_trimmed": False,
        "source_audio_duration": scene.audio[0].duration,
        "source_cues": len(CUES.cues),
        "chapters": [{"start": at, "title": title} for at, title in CHAPTERS],
        "input_sha256": hashes,
        "layout_samples": samples,
        "minimum_face_clearance_px": round(minimum_clearance, 3),
        "longest_blank_transition_seconds": round(longest_blank_run / 60, 3),
        "external_text": False,
        "media_rendered": False,
        "full_export_verified": False,
    }
