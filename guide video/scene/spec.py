"""Unchanged source cues, complete editor revisions, and preparation identities."""

import ast
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from facelesschamp_kit import BuildContext
from facelesschamp_kit.themes import Theme

from faceless_champ import Canvas, CodeCheckpoint, PlaygroundScript, SubtitleTrack

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parent
DURATION = 286.1
ACCENT = "#48E0CB"
INK = "#F3F4F7"
MUTED = "#9CA3AF"
SURFACE = "#111318"
LINE = "#353A43"
CHAPTERS = (
    ("opening", 1),
    ("model", 65),
    ("setup", 133),
    ("author", 210),
    ("coordinates", 312),
    ("circle", 359),
    ("timeline", 389),
    ("export", 524),
    ("edits", 581),
    ("narration", 627),
    ("kit", 690),
    ("recap", 760),
)


def track():
    return SubtitleTrack.from_srt(PROJECT / "cue-per-word.srt", overlap_tolerance=0.001)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def context(preparing=False):
    return BuildContext(
        PROJECT,
        canvas=Canvas(1920, 1080, "#000000"),
        theme=Theme(
            background="#000000",
            surface=SURFACE,
            foreground=INK,
            muted=MUTED,
            accent=ACCENT,
            body_size=38,
            minimum_font_size=28,
            spacing=24,
            radius=16,
        ),
        safe_margin=72,
        captions=False,
        preparing=preparing,
    )


def examples():
    base = (PROJECT / "examples/hello.py").read_text()
    return {
        "baseline": base,
        "text": base.replace("Hello, Faceless Champ", "Hello, Python"),
        "color": base.replace("Hello, Faceless Champ", "Hello, Python").replace(ACCENT, "#F5A97F"),
        "duration": base.replace("Hello, Faceless Champ", "Hello, Python")
        .replace(ACCENT, "#F5A97F")
        .replace("run_time=2,", "run_time=3,"),
    }


def lesson_scripts():
    cues = track()
    base = examples()["baseline"]
    adapter = (PROJECT / "scene/checkpoint.py").read_text()
    lines = base.splitlines(keepends=True)
    tree = ast.parse(base)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    init, construct = cls.body
    title, dot, together, wait, move, *_ = construct.body

    # Every published revision is a runnable module. Temporary editor text never executes.
    def revision(stop, add=""):
        return "".join(lines[:stop]) + add

    revisions = [
        ("imports", 212, 231, revision(tree.body[0].end_lineno) + "\nclass Hello(Scene):\n    pass\n", 1),
        ("class", 233, 248, revision(cls.lineno) + "    pass\n", 1),
        ("canvas", 249, 265, revision(init.end_lineno), 6),
        ("construct", 282, 289, revision(construct.lineno) + "        pass\n", 6),
        ("text", 292, 309, revision(title.end_lineno), 10),
        ("circle", 359, 379, revision(dot.end_lineno), 17),
        ("together", 395, 411, revision(together.end_lineno), 22),
        ("wait", 435, 448, revision(wait.end_lineno), 22),
        ("move", 453, 479, revision(move.end_lineno), 26),
        ("finish", 509, 520, base, 28),
    ]
    start = cues.cue(210).start
    checkpoints = []
    for name, first, last, source, scroll in revisions:
        at, end = cues.cue(first).start - start, cues.cue(last).start - start
        checkpoints.append(
            CodeCheckpoint(
                name,
                {"hello.py": source, "checkpoint.py": adapter},
                "hello.py",
                "checkpoint.py",
                at,
                end,
                end,
                first_line=scroll,
            )
        )
    author = PlaygroundScript(checkpoints, duration=cues.cue(524).start - start, mode="concept")
    edit_start = cues.cue(581).start
    edit_points = [
        ("baseline", edit_start, edit_start),
        ("text", cues.cue(585).start, cues.cue(589).start),
        ("color", cues.cue(590).start, cues.cue(595).start),
        ("duration", cues.cue(596).start, cues.cue(600).start),
    ]
    edits = PlaygroundScript(
        [
            CodeCheckpoint(
                name,
                {"hello.py": examples()[name], "checkpoint.py": adapter},
                "hello.py",
                "checkpoint.py",
                a - edit_start,
                b - edit_start,
                b - edit_start,
                first_line=10 if name in {"baseline", "text"} else 17 if name == "color" else 26,
            )
            for name, a, b in edit_points
        ],
        duration=cues.cue(627).start - edit_start,
        mode="concept",
    )
    return {"author": author, "edits": edits}


def prepare():
    cache = PROJECT / ".fc-kit"
    cache.mkdir(exist_ok=True)
    # Decode once; pad only the tail. Never alter the supplied MP3 or subtitle files.
    fd, temporary = tempfile.mkstemp(suffix=".wav", dir=cache)
    os.close(fd)
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-i",
                str(PROJECT / "audio.mp3"),
                "-af",
                f"apad,atrim=duration={DURATION}",
                "-ar",
                "48000",
                "-ac",
                "1",
                "-c:a",
                "pcm_s16le",
                temporary,
            ],
            check=True,
        )
        os.replace(temporary, cache / "narration.wav")
    finally:
        Path(temporary).unlink(missing_ok=True)
    from facelesschamp_kit.scaffold import init_project

    if not (cache / "starter").exists():
        init_project(cache / "starter", template="silent")
    for name, source in examples().items():
        if name != "baseline":
            (PROJECT / "examples" / f"hello_{name}.py").write_text(source)
    ctx = context(preparing=True)
    for script in lesson_scripts().values():
        ctx.playground(script)
    info = {
        "audio": digest(PROJECT / "audio.mp3"),
        "cues": digest(PROJECT / "cue-per-word.srt"),
        "derived_audio": digest(cache / "narration.wav"),
        "duration": DURATION,
        "full_export_verified": False,
    }
    (cache / "preparation.json").write_text(json.dumps(info, indent=2))
    return info


def require_audio():
    cache = PROJECT / ".fc-kit"
    try:
        record = json.loads((cache / "preparation.json").read_text())
        for key, path in (
            ("audio", PROJECT / "audio.mp3"),
            ("cues", PROJECT / "cue-per-word.srt"),
            ("derived_audio", cache / "narration.wav"),
        ):
            if record[key] != digest(path):
                raise ValueError("Preparation is stale or corrupt")
    except (OSError, ValueError, KeyError) as exc:
        raise ValueError("Run python3 render.py --prepare before building the guide") from exc
    return cache / "narration.wav"


def chapters():
    cues = track()
    return [
        {
            "id": name,
            "first": first,
            "start": 0 if i == 0 else cues.cue(first).start,
            "end": cues.cue(CHAPTERS[i + 1][1]).start if i + 1 < len(CHAPTERS) else DURATION,
        }
        for i, (name, first) in enumerate(CHAPTERS)
    ]
