"""A silent CodingChamp design study. Building/seeking never executes the examples.

The approved window styling and motion come from the reusable core design.
Lesson content, typing stages and output remain authored in this training project.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from faceless_champ import (
    Animation,
    Canvas,
    CodeReveal,
    CodeWorkspaceDesign,
    CodingChamp,
    FadeIn,
    FadeOut,
    Rectangle,
    Scene,
    linear,
)

TOTAL_DURATION = 120.0
TITLE = "function in python"
CANVAS_SIZE = (1920, 1080)
DESIGN = CodeWorkspaceDesign.named("clean-flow")
CODE_SIZE = DESIGN.code_size
TERMINAL_SIZE = DESIGN.terminal_size
EDITOR_SCALE = DESIGN.editor_scale
SHRINK_DURATION = DESIGN.shrink_duration
RESTORE_DURATION = DESIGN.restore_duration
TERMINAL_ENTRANCE = DESIGN.terminal_entrance_duration
TERMINAL_EXIT = DESIGN.terminal_exit_duration
COMMAND = "$ python functions.py"
PALETTE = {
    "background": DESIGN.background,
    "ink": "#111111",
    "muted": "#737373",
    "orange": "#FF5A20",
    "purple": "#BCA7E6",
    "blue": "#81B6D9",
    "green": "#A3C9A6",
    "white": "#FFFFFF",
}
CODE_THEME = DESIGN.theme
OUTPUT_THEME = replace(CODE_THEME, foreground="#B1D7AD")
EDITOR_FULL = DESIGN.editor_full
EDITOR_SPLIT = DESIGN.editor_split
TERMINAL_BOX = DESIGN.terminal_bounds
CODE_BOX = DESIGN.code_bounds

BASIC_CODE = 'def greet():\n    print("Hello, Python!")\n\ngreet()'
PARAMETER_CODE = 'def greet(name):\n    print(f"Hello, {name}!")\n\ngreet("Maya")\ngreet("Leo")'
RETURN_CODE = "def add(a, b):\n    return a + b\n\nresult = add(3, 4)\nprint(result)"
REUSE_CODE = RETURN_CODE + "\nprint(add(10, 5))"


@dataclass(frozen=True)
class Example:
    id: str
    code: str
    stdout: str
    publish: float
    close: float

    @property
    def terminal_start(self):
        return self.publish - 2.0


EXAMPLES = (
    Example("define-call", BASIC_CODE, "Hello, Python!\n", 24, 29),
    Example("parameters", PARAMETER_CODE, "Hello, Maya!\nHello, Leo!\n", 55, 59),
    Example("return", RETURN_CODE, "7\n", 85, 89),
    Example("reuse", REUSE_CODE, "7\n15\n", 103, 109),
)
CHAPTERS = (
    ("intro", 0, 6, "A reusable block of code"),
    ("define-call", 6, 32, "01 / Define & call"),
    ("parameters", 32, 62, "02 / Parameters & arguments"),
    ("return", 62, 92, "03 / Return a value"),
    ("reuse", 92, 114, "04 / Reuse the function"),
    ("recap", 114, 120, "Define. Call. Return. Reuse."),
)
# Each stage reveals the next physical lines, with deliberate reading pauses.
TYPING = (
    ("basic", 1.2, 4.8, "def greet():\n"),
    ("basic", 6.0, 11.4, 'def greet():\n    print("Hello, Python!")\n'),
    ("basic", 18.5, 21.0, BASIC_CODE),
    ("parameters", 33.0, 36.8, "def greet(name):\n"),
    ("parameters", 37.5, 43.0, 'def greet(name):\n    print(f"Hello, {name}!")\n'),
    ("parameters", 46.0, 48.7, PARAMETER_CODE.rsplit("\n", 1)[0]),
    ("parameters", 49.5, 52.1, PARAMETER_CODE),
    ("return", 63.0, 66.2, "def add(a, b):\n"),
    ("return", 67.0, 71.2, "def add(a, b):\n    return a + b\n"),
    ("return", 74.0, 77.5, RETURN_CODE.rsplit("\n", 1)[0]),
    ("return", 79.0, 81.8, RETURN_CODE),
    ("return", 92.5, 98.5, REUSE_CODE),
)
# panel, visible physical line, start, end, accent
HIGHLIGHTS = (
    ("basic", 1, 4.9, 5.8, "purple"),
    ("basic", 2, 11.6, 18.0, "orange"),
    ("basic", 4, 21.0, 22.0, "blue"),
    ("parameters", 1, 36.9, 37.3, "purple"),
    ("parameters", 2, 43.1, 45.5, "green"),
    ("parameters", 4, 48.8, 49.3, "blue"),
    ("parameters", 5, 52.1, 53.0, "blue"),
    ("return", 2, 71.3, 73.5, "orange"),
    ("return", 4, 77.6, 78.8, "blue"),
    ("return", 5, 81.9, 83.0, "blue"),
    ("return", 6, 98.6, 100.4, "green"),
)


fluid = DESIGN.fluid


def build_video():
    """Return the 120-second Scene and a JSON-serializable authoring report."""
    scene = Scene(Canvas(*CANVAS_SIZE, PALETTE["background"]))
    # References support geometry/state checks through Scene.bounds_at().
    scene.training_objects = {}
    events = []

    def register(name, component, *, check_bounds=True):
        component.training_id = name
        component.training_check_bounds = check_bounds
        scene.training_objects[name] = component
        return component

    def play(at, duration, *animations):
        with scene.at(at):
            scene.play(*animations, run_time=duration)

    def lifetime(component, start, end, *, entrance=0.12, exit=0.12):
        play(start, entrance, component.animate.opacity_to(1))
        play(end - exit, exit, FadeOut(component))
        with scene.at(end):
            scene.remove(component)

    def window(name, box, title, *, children=(), fullscreen=False):
        root = DESIGN.window(box, title, children=children, fullscreen=fullscreen)
        register(f"{name}.shadow", root.shadow, check_bounds=False)
        register(f"{name}.face", root.face)
        register(f"{name}.heading", root.heading)
        register(name, root, check_bounds=False)
        return root

    panels = {}
    for name, source in (("basic", BASIC_CODE), ("parameters", PARAMETER_CODE), ("return", REUSE_CODE)):
        panels[name] = register(
            f"code.{name}",
            CodingChamp(
                source,
                language="python",
                theme=CODE_THEME,
                chrome=False,
                width=CODE_BOX.width,
                height=CODE_BOX.height,
                font_size=CODE_SIZE,
                padding=8,
                position=(CODE_BOX.left, CODE_BOX.top),
                anchor="top_left",
                opacity=0,
            ),
        )
    highlights = []
    for index, (name, line, start, end, color) in enumerate(HIGHLIGHTS):
        panel = panels[name]
        highlight = register(
            f"highlight.{index}",
            Rectangle(
                width=CODE_BOX.width - 12,
                height=panel.line_height,
                corner_radius=7,
                fill=PALETTE[color] + "10",
                stroke=PALETTE[color] + "55",
                stroke_width=1,
                position=(CODE_BOX.left + 6, CODE_BOX.top + panel.code_y + (line - 1) * panel.line_height),
                anchor="top_left",
                opacity=0,
            ),
        )
        highlights.append(highlight)

    editor = window(
        "editor",
        EDITOR_FULL,
        "functions.py",
        children=(*panels.values(), *highlights),
        fullscreen=True,
    )
    # Adding the group before scheduling child animations preserves ownership.
    scene.add(editor)
    play(0, 0.001, *(CodeReveal(panel, 0, 0) for panel in panels.values()))
    play(0, 0.2, panels["basic"].animate.opacity_to(1))
    for old, new, at in (("basic", "parameters", 32.0), ("parameters", "return", 62.0)):
        play(at, 0.3, FadeOut(panels[old]))
        play(at + 0.3, 0.2, panels[new].animate.opacity_to(1))

    previous = {name: 0 for name in panels}
    for name, start, end, prefix in TYPING:
        panel = panels[name]
        if not panel.code.startswith(prefix):
            raise ValueError(f"Typing stage must be a prefix of {name}")
        first, last = previous[name], len(prefix)
        play(start, end - start, CodeReveal(panel, first / len(panel.code), last / len(panel.code)))
        events.append(
            {
                "kind": "typing",
                "panel": name,
                "start": start,
                "end": end,
                "first_character": first,
                "last_character": last,
            }
        )
        previous[name] = last

    def resize(at, *, shrink):
        scale = EDITOR_SCALE if shrink else 1.0
        position = EDITOR_SPLIT.center if shrink else EDITOR_FULL.center
        duration = SHRINK_DURATION if shrink else RESTORE_DURATION
        play(
            at,
            duration,
            DESIGN.editor_motion(editor, running=shrink),
            *DESIGN.editor_corners(editor, running=shrink),
        )
        events.append(
            {"kind": "resize", "start": at, "end": at + duration, "scale": scale, "position": list(position)},
        )

    for example in EXAMPLES:
        box = TERMINAL_BOX
        command = register(
            f"terminal.{example.id}.command",
            CodingChamp(
                COMMAND,
                language="text",
                theme=CODE_THEME,
                chrome=False,
                line_numbers=False,
                width=box.width - 56,
                height=66,
                font_size=TERMINAL_SIZE,
                padding=0,
                position=(box.left + 28, box.top + 96),
                anchor="top_left",
                opacity=0,
            ),
        )
        output = register(
            f"terminal.{example.id}.output",
            CodingChamp(
                example.stdout.rstrip("\n"),
                language="text",
                theme=OUTPUT_THEME,
                chrome=False,
                line_numbers=False,
                width=box.width - 56,
                height=400,
                font_size=TERMINAL_SIZE,
                padding=0,
                position=(box.left + 28, box.top + 176),
                anchor="top_left",
                opacity=0,
            ),
        )
        terminal = window(f"terminal.{example.id}", box, "Terminal", children=(command, output))
        resize(example.terminal_start - SHRINK_DURATION, shrink=True)
        play(example.terminal_start, TERMINAL_ENTRANCE, DESIGN.terminal_in(terminal))
        play(
            example.terminal_start + TERMINAL_ENTRANCE,
            2.0 - TERMINAL_ENTRANCE,
            Animation(command, {"opacity": 1, "reveal": 1}, {"opacity": 1, "reveal": 0}, rate_func=linear),
        )
        play(example.publish, 0.15, output.animate.opacity_to(1))
        play(example.close, TERMINAL_EXIT, DESIGN.terminal_out(terminal))
        with scene.at(example.close + TERMINAL_EXIT):
            scene.remove(terminal)
        resize(example.close + TERMINAL_EXIT, shrink=False)
        events.append(
            {
                "kind": "run",
                "id": example.id,
                "start": example.terminal_start,
                "publish": example.publish,
                "close": example.close,
                "end": example.close + TERMINAL_EXIT,
            }
        )

    for highlight, (_, _, start, end, _) in zip(highlights, HIGHLIGHTS):
        lifetime(highlight, start, end)

    # Close on the editor itself, with no title or recap overlay.
    veil = Rectangle(
        width=1920,
        height=1080,
        fill=CODE_THEME.background,
        stroke=None,
        position=(0, 0),
        anchor="top_left",
        z_index=100,
    )
    play(119.4, 0.6, FadeIn(veil))
    scene.wait_until(TOTAL_DURATION)
    report = {
        "title": TITLE,
        "duration": TOTAL_DURATION,
        "canvas": list(CANVAS_SIZE),
        "audio_tracks": 0,
        "external_text": False,
        "editor_run_scale": EDITOR_SCALE,
        "full_export_verified": False,
        "chapters": [{"id": name, "start": start, "end": end} for name, start, end, _ in CHAPTERS],
        "examples": [{"id": e.id, "code": e.code, "stdout": e.stdout, "publish": e.publish} for e in EXAMPLES],
        "events": sorted(events, key=lambda event: event["start"]),
    }
    return scene, report
