"""Sixty-second native Skia editor: type, run, diagnose, edit, and run again."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from pygments import lex
from pygments.lexers import PythonLexer

from faceless_champ import (
    Bounds,
    Canvas,
    CodeTheme,
    CodeWindow,
    ExportProgress,
    ExportSettings,
    Rectangle,
    Scene,
    Text,
    create_renderer,
    render,
    rendering_identity,
    save_frame,
)
from faceless_champ.coding import MONO_FONT

ROOT = Path(__file__).resolve().parent
DURATION = 60.0
THEME = CodeTheme.named("clean-flow")
CYAN, GREEN, RED = "#78DCE8", "#A6E3A1", "#FF8397"
SOURCE = """def average(values):
    if not values:
        return 0.0
    total = sum(values)
    return total


samples = [6, 8, 10]
result = average(samples)
print(f"Average: {result:.1f}")
assert result == 8.0"""
FIX = " / len(values)"
CORRECTED = SOURCE.replace("return total", "return total" + FIX)
FONT_SIZE, LINE_HEIGHT = 39, 64
# DejaVu Sans Mono's fixed advance, in its 2048-unit em square.
ADVANCE = FONT_SIZE * 1233 / 2048


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def text(value, x, y, size=FONT_SIZE, color=THEME.foreground):
    return Text(
        value, font=str(MONO_FONT), font_size=size, color=color, position=(x, y), anchor="top_left", text_engine="skia"
    )


def rect(x, y, w, h, color, opacity=1):
    return Rectangle(width=w, height=h, position=(x, y), anchor="top_left", fill=color, stroke=None, opacity=opacity)


def syntax_runs(source):
    """Tokenize the complete revision so partial keywords keep stable colors."""
    runs, row, col, offset = [], 0, 0, 0
    for kind, value in lex(source, PythonLexer(stripnl=False, ensurenl=False)):
        name = str(kind).removeprefix("Token.")
        color = THEME.foreground
        while name:
            if name in THEME.syntax:
                color = THEME.syntax[name]
                break
            name = name.rpartition(".")[0]
        for piece in value.splitlines(keepends=True):
            content = piece.rstrip("\n")
            if content.strip():
                runs.append((offset, row, col, content, color))
            offset += len(piece)
            if piece.endswith("\n"):
                row, col = row + 1, 0
            else:
                col += len(piece)
    return runs


RUNS = syntax_runs(SOURCE)


def editor(t):
    typed = min(len(SOURCE), max(0, int((t - 2) / 22 * len(SOURCE))))
    fixing = t >= 41
    extra = min(len(FIX), max(0, int((t - 42) / 3 * len(FIX))))
    insertion = SOURCE.index("return total") + len("return total")
    if fixing:
        visible = SOURCE[:insertion] + FIX[:extra] + SOURCE[insertion:]
        caret_offset = insertion + extra
        # Complete fixed token colors can be reused against the visible revision.
        runs = syntax_runs(visible)
        limit = len(visible)
    else:
        visible, caret_offset, runs, limit = SOURCE, typed, RUNS, typed
    x, y = 206, 217
    caret_prefix = visible[:caret_offset]
    row = caret_prefix.count("\n")
    col = len(caret_prefix.rsplit("\n", 1)[-1])
    active_row = row if t < 25 or 41 <= t < 46 else (10 if 36 <= t < 41 else 4 if t >= 46 else 8)
    children = [
        rect(173, y + active_row * LINE_HEIGHT - 3, 1600, 55, "#24303A", 0.8),
        rect(173, y + active_row * LINE_HEIGHT - 3, 3, 55, CYAN),
    ]
    for line in range(11):
        children.append(text(f"{line + 1:2}", 117, y + line * LINE_HEIGHT, 25, "#68717E"))
    for offset, token_row, token_col, value, color in runs:
        shown = value[: max(0, limit - offset)]
        if shown.strip():
            children.append(text(shown, x + token_col * ADVANCE, y + token_row * LINE_HEIGHT, color=color))
    # Cursor blinks while resting and stays solid while typing.
    moving = 2 <= t < 24 or 42 <= t < 45
    if moving or int(t * 2) % 2 == 0:
        children.append(rect(x + col * ADVANCE, y + row * LINE_HEIGHT + 3, 3, 44, CYAN))
    window = CodeWindow(
        Bounds(80, 90, 1840, 990), title="average.py", children=children, surface_mode="vector", text_engine="skia"
    )
    split = smooth((t - 29) / 2)
    window.scale = 1 - 0.32 * split
    window.position = (960 - 285 * split, 540)
    return window


COMMAND = "$ python average.py"
FIRST_OUTPUT = (
    (34.0, "Average: 24.0", THEME.foreground),
    (35.0, "Traceback (most recent call last):", "#A6A7AD"),
    (35.6, '  File "average.py", line 11', "#A6A7AD"),
    (36.2, "    assert result == 8.0", "#FFC887"),
    (36.8, "AssertionError", RED),
)
SECOND_OUTPUT = ((49.8, "Average: 8.0", GREEN),)


def terminal(t):
    enter = smooth((t - 30) / 1.4)
    if enter == 0:
        return None
    children = []
    x, y, step = 1324, 261, 39
    command_len = max(0, min(len(COMMAND), int((t - 31.5) / 1.6 * len(COMMAND))))
    if command_len:
        children.append(text(COMMAND[:command_len], x, y, 24, CYAN))
    lines = []
    for when, value, color in FIRST_OUTPUT:
        if t >= when:
            lines.append((value, color))
    for i, (value, color) in enumerate(lines):
        children.append(text(value, x, y + (i + 1) * step, 23, color))
    y2 = y + 7 * step
    if t >= 47:
        command_len = min(len(COMMAND), max(0, int((t - 47) / 1.6 * len(COMMAND))))
        if command_len:
            children.append(text(COMMAND[:command_len], x, y2, 24, CYAN))
        for when, value, color in SECOND_OUTPUT:
            if t >= when:
                children.append(text(value, x, y2 + step, 24, color))
        if t >= 51:
            children.append(text("$", x, y2 + 3 * step, 24, CYAN))
            if int(t * 2) % 2 == 0:
                children.append(rect(x + 30, y2 + 3 * step + 4, 13, 25, CYAN))
    elif 38 <= t < 47:
        children.append(text("$", x, y2, 24, CYAN))
        if int(t * 2) % 2 == 0:
            children.append(rect(x + 30, y2 + 4, 13, 25, CYAN))
    window = CodeWindow(
        Bounds(1294, 207, 1840, 873),
        title="Terminal",
        children=children,
        surface_mode="vector",
        text_engine="skia",
        unit=0.85,
    )
    window.position = (1567 + 650 * (1 - enter), 540)
    window.opacity = enter
    return window


class EditorScene(Scene):
    def construct(self):
        self.wait_until(DURATION)

    def sample(self, t):
        if not math.isfinite(t) or not 0 <= t <= DURATION:
            raise ValueError("source time must be in [0, 60]")
        scene = Scene(Canvas(1920, 1080, "#000000"))
        envelope = smooth(t / 1.2) * smooth((60 - t) / 2)
        if envelope:
            code = editor(t)
            code.opacity = envelope
            scene.add(code)
            shell = terminal(t)
            if shell is not None:
                shell.opacity *= envelope
                scene.add(shell)
        scene.wait_until(DURATION)
        return scene


def build_scene():
    return EditorScene(Canvas(1920, 1080, "#000000"))


class EditorRenderer:
    def __init__(self):
        self.native = create_renderer("skia", antialias=1, frame_cache_mb=0)

    def validate(self, node):
        self.native.validate(node.sample(53))

    def frame(self, node, time, size):
        return self.native.frame(node.sample(time), 0, size)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.native.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true", help="Editor and terminal transition, source time 30–32")
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"))
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame <= DURATION:
        parser.error("frame must be in [0, 60]")
    if args.range and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 60")
    if args.fps <= 0:
        parser.error("fps must be positive")
    scene = build_scene()
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "skia-code-terminal.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    source_range = args.range or ([30, 32] if args.preview else [0, DURATION])
    with EditorRenderer() as renderer:
        if args.frame is not None:
            source_range = [args.frame, args.frame]
            save_frame(
                scene,
                args.frame,
                output,
                size=settings.dimensions(scene.canvas),
                renderer=renderer,
                overwrite=args.overwrite,
            )
        else:
            with ExportProgress() as progress:
                render(
                    scene,
                    output,
                    settings=settings,
                    start_time=source_range[0],
                    end_time=source_range[1],
                    renderer=renderer,
                    overwrite=args.overwrite,
                    progress=progress,
                )
        stats = dict(renderer.native.stats)
    output.with_suffix(".json").write_text(
        json.dumps(
            {
                "scene_duration": scene.duration,
                "source_range": source_range,
                "rendering": rendering_identity("skia", scene.sample(30)),
                "stats": stats,
                "full_export_verified": False,
            },
            indent=2,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
