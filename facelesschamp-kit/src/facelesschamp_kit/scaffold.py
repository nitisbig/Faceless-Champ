import json
import os
import shutil
import tempfile
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
    if template not in {"silent", "explainer-short", "narrated-short"}:
        raise KitError("TEMPLATE", "Choose silent, explainer-short, or narrated-short")
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
        (staging / "facelesschamp.toml").write_text(CONFIG)
        narrated = template == "narrated-short"
        (staging / "videos/main.py").write_text(NARRATED if narrated else SILENT)
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
            'requires-python = ">=3.12"\ndependencies = ["facelesschamp-kit==0.1.0rc1"]\n'
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
        (staging / "README.md").write_text(
            "# Your video\n\n"
            + instructions
            + "Run `fc-kit validate main`, `fc-kit preview main -o output/preview.mp4`, and "
            "`fc-kit render main -o output/main.mp4`. Preview defaults to the first ten seconds.\n\n"
            "Change format to `landscape` or theme to `light` in facelesschamp.toml. "
            "Enable captions explicitly with `captions = true`.\n"
        )
        # Reserve the destination before moving content; never merge with an existing project.
        os.mkdir(destination)
        for item in staging.iterdir():
            shutil.move(str(item), destination / item.name)
    finally:
        shutil.rmtree(staging)
    return destination
