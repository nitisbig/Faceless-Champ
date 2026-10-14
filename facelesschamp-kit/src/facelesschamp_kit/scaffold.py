import json
import os
import shutil
import tempfile
from importlib.resources import files
from pathlib import Path

from .diagnostics import KitError

CONFIG = """schema_version = 1

[project]
name = "first-video"
seed = 0
safe_margin = 64
caption_space = 220

[videos.main]
factory = "videos.main:build"
format = "shorts"
theme = "midnight"
captions = false

[profiles.preview]
fps = 15
antialias = 1
preset = "veryfast"

[profiles.final]
fps = 30
antialias = 2
preset = "medium"
"""
SILENT = """from facelesschamp_kit import Video
from facelesschamp_kit.blocks import Comparison, MetricCard, StepList


def build(ctx):
    video = Video(ctx)
    with video.segment("hook", duration=3) as segment:
        segment.add(MetricCard(42, "Reusable components"), enter="pop")
    with video.segment("comparison", duration=4) as segment:
        segment.add(Comparison("Repeated setup", "Shared building blocks"), enter="fade")
    with video.segment("finish", duration=3) as segment:
        segment.add(StepList(("Compose", "Preview", "Export")), enter="stagger")
    return video
"""
NARRATED = """from facelesschamp_kit import Video
from facelesschamp_kit.blocks import Comparison, Heading, StepList


def build(ctx):
    video = Video(ctx)
    if ctx.assets.entries.get("voiceover", {}).get("source") == "Synthetic demonstration speech":
        from faceless_champ import Bounds
        video.segment("sample-label", start=0, duration=30).add(
            Heading("SYNTHETIC DEMO AUDIO", variant="muted"),
            bounds=Bounds(64, 8, ctx.canvas.width-64, 58), z_index=10001,
        )
    voice = video.narration(
        audio=ctx.assets.audio("voiceover"),
        subtitles=ctx.assets.subtitle("word_cues"),
        markers={"hook": 1, "comparison": 2, "finish": 3},
    )
    with video.segment("hook", window=voice.between("hook", "comparison")) as segment:
        segment.add(Heading("Build once. Reuse everywhere."), enter="fade")
    with video.segment("comparison", window=voice.between("comparison", "finish")) as segment:
        segment.add(Comparison("Repeated setup", "Shared building blocks"), enter="fade")
    with video.segment("finish", window=voice.between("finish")) as segment:
        segment.add(StepList(("Compose", "Preview", "Export")), enter="stagger")
    return video
"""


def init_project(destination, template="silent"):
    if template not in {
        "silent",
        "explainer-short",
        "narrated-short",
        "whiteboard-basic",
        "flowchamp",
        "archchamp",
        "os-ui",
        "chesschamp",
        "coding-web",
        "coding-concept",
        "coding-backend",
    }:
        raise KitError(
            "TEMPLATE",
            "Choose flowchamp, silent, explainer-short, narrated-short, whiteboard-basic, os-ui, chesschamp, coding-web, coding-concept, or coding-backend",
        )
    destination = Path(destination).resolve()
    if destination.exists():
        raise KitError("DESTINATION", "Destination already exists; choose a new directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".fc-kit-init-", dir=destination.parent))
    try:
        for directory in ("videos", "components", "assets/images", "assets/fonts", "assets/audio", "data"):
            (staging / directory).mkdir(parents=True)
        (staging / "videos/__init__.py").write_text("")
        (staging / "components/__init__.py").write_text("")
        whiteboard = template == "whiteboard-basic"
        os_ui = template == "os-ui"
        chess = template == "chesschamp"
        coding = template.startswith("coding-")
        config = (
            CONFIG.replace('format = "shorts"', 'format = "landscape"').replace(
                'theme = "midnight"', 'theme = "whiteboard"'
            )
            if whiteboard or os_ui or chess or coding or template in {"flowchamp", "archchamp"}
            else CONFIG
        )
        if os_ui or chess or coding or template in {"flowchamp", "archchamp"}:
            config = config.replace('theme = "whiteboard"', 'theme = "midnight"')
        (staging / "facelesschamp.toml").write_text(config)
        narrated = template == "narrated-short"
        source = (
            files("facelesschamp_kit")
            .joinpath("sample_assets/os_ui.py" if os_ui else "sample_assets/whiteboard.py")
            .read_text()
            if whiteboard or os_ui
            else (NARRATED if narrated else SILENT)
        )
        if chess:
            source = (
                "from facelesschamp_kit.templates import chesschamp\n\ndef build(ctx):\n    return chesschamp(ctx)\n"
            )
            (staging / "data.json").write_text(
                files("facelesschamp_kit").joinpath("sample_assets/chesschamp.json").read_text()
            )
        if coding:
            source = (
                files("facelesschamp_kit").joinpath("sample_assets/" + template.replace("-", "_") + ".py").read_text()
            )
        if template in {"flowchamp", "archchamp"}:
            source = files("facelesschamp_kit").joinpath("sample_assets/" + template + ".py").read_text()
        (staging / "videos/main.py").write_text(source)
        manifest = (
            {
                "voiceover": {
                    "type": "audio",
                    "package": "facelesschamp_kit",
                    "resource": "sample_assets/voiceover.wav",
                    "source": "Synthetic demonstration speech",
                },
                "word_cues": {
                    "type": "subtitle",
                    "package": "facelesschamp_kit",
                    "resource": "sample_assets/word-cues.srt",
                    "source": "Demonstration sentence cues",
                },
            }
            if narrated
            else {}
        )
        (staging / "assets/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        (staging / "pyproject.toml").write_text(
            '[project]\nname = "my-video"\nversion = "0.1.0"\n'
            'requires-python = ">=3.12"\ndependencies = ["facelesschamp-kit==0.1.0rc7"]\n'
        )
        if chess:
            project_file = staging / "pyproject.toml"
            project_file.write_text(
                project_file.read_text().replace("facelesschamp-kit==", "facelesschamp-kit[chess]==")
            )
        if coding:
            project_file = staging / "pyproject.toml"
            project_file.write_text(
                project_file.read_text().replace("facelesschamp-kit==", "facelesschamp-kit[playground]==")
            )
        (staging / ".gitignore").write_text("output/\n.fc-kit/\n.venv/\n__pycache__/\n")
        instructions = (
            (
                "This starter uses bundled synthetic demonstration speech and sentence-level SRT cues. "
                "Replace the package resource entries in assets/manifest.json with paths to your audio and SRT. Update the marker indices "
                "in videos/main.py to match your original SRT cues. Speech generation is not part of the runtime.\n\n"
            )
            if narrated
            else ""
        )
        if chess:
            instructions = (
                "Install `facelesschamp-kit[chess]`. Edit the required root data.json to author legal UCI moves, "
                "absolute timing, player names, and text/arrow/highlight annotations. "
                "Optional narration.audio names an audio asset in assets/manifest.json; subtitles are not required. "
                "The chess rules dependency is GPL-3.0-or-later. See the ChessChamp guide for its data contract.\n\n"
            )
        if whiteboard:
            instructions = (
                "Edit the two WhiteboardScene recipes in videos/main.py. Drawings use source coordinates in each "
                "viewbox and fit both landscape and shorts formats without stretching. Each board draws, holds, "
                "and clears before the next scene. All geometry is local; no media downloads are required.\n\n"
                "For narration, register audio/subtitle assets in assets/manifest.json, pass their IDs and a "
                "marker mapping to whiteboard_basic, and replace scene durations with cues=(start_marker, end_marker). "
                "Use None for the last end marker to hold through the audio end. Captions are optional.\n\n"
            )
        if coding:
            instructions = (
                "Edit the complete source revisions and explicit bindings in videos/main.py. "
                "Install facelesschamp-kit[playground]; for web also install Chromium explicitly. "
                "Run `fc-kit prepare main` before validate, preview, or render. "
                "Preparation executes trusted local source; it is not a security sandbox. "
                "Use `fc-kit prepare main --refresh` to execute again.\n\n"
            )
        (staging / "README.md").write_text(
            "# Your video\n\n"
            + instructions
            + "Run `fc-kit validate main`, `fc-kit preview main -o output/preview.mp4`, and "
            "`fc-kit render main -o output/main.mp4`. Preview defaults to the first ten seconds.\n\n"
            "Choose format `shorts` or `landscape`, and theme `midnight`, `light`, or `whiteboard` in facelesschamp.toml. "
            "Enable captions explicitly with `captions = true`.\n"
        )
        # Reserve the destination before moving content; never merge with an existing project.
        os.mkdir(destination)
        for item in staging.iterdir():
            shutil.move(str(item), destination / item.name)
    finally:
        shutil.rmtree(staging)
    return destination
