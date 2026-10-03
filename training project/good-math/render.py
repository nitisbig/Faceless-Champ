"""Render GoodMath from this checkout, independent of your working directory.

uv run python 'training project/good-math/render.py' --preview
uv run python 'training project/good-math/render.py'
uv run python 'training project/good-math/render.py' --frames
uv run python 'training project/good-math/render.py' --frame 24.7
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
# Use the library being improved in this repository, including before installation.
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from scene import GoodMath

from faceless_champ import ExportSettings, PillowRenderer


def storyboard(scene, directory, renderer):
    directory.mkdir(parents=True, exist_ok=True)
    sheet = PILImage.new("RGB", (1920, 4 * 398), "#faf7f2")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(ROOT / "src/faceless_champ/assets/DejaVuSans.ttf"), 15)
    for i, beat in enumerate(scene.beat_times):
        time = beat["preview"]
        frame = renderer.frame(scene, time, (1280, 720)).convert("RGB")
        frame.save(directory / f"{i + 1:02d}-{time:05.2f}s.png")
        x, y = (i % 3) * 640, (i // 3) * 398
        sheet.paste(frame.resize((640, 360), PILImage.Resampling.LANCZOS), (x, y))
        draw.text((x + 18, y + 369), f"{i + 1:02d} · {time:.2f}s · {beat['title']}", font=font, fill="#716b64")
    sheet.save(directory / "storyboard.png")
    return directory / "storyboard.png"


def main():
    parser = argparse.ArgumentParser(description="Render the good-math training project with Faceless Champ.")
    parser.add_argument("--preview", action="store_true", help="Quick 720p / 24 fps render")
    parser.add_argument("-q", "--quality", choices=("ql", "qh", "qk", "720p", "1080p", "4k"))
    parser.add_argument("--fps", type=float, help="Override frame rate (default: 30; preview: 24)")
    parser.add_argument("--antialias", type=int, choices=(1, 2, 3, 4))
    parser.add_argument("-o", "--output", type=Path, help="MP4 output path; defaults to this project's output folder")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output")
    parser.add_argument("--no-captions", action="store_true", help="Hide the word-highlight caption line")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--frames", action="store_true", help="Save all 12 storyboard frames instead of a video")
    modes.add_argument("--frame", type=float, metavar="SECONDS", help="Save a PNG at an exact audio time")
    args = parser.parse_args()
    try:
        scene = GoodMath(captions=not args.no_captions).build()
        quality = args.quality or ("ql" if args.preview else "qh")
        settings = ExportSettings(
            quality=quality,
            fps=args.fps if args.fps is not None else (24 if args.preview else 30),
            antialias=args.antialias or (1 if args.preview else 2),
            preset="veryfast" if args.preview else "medium",
            crf=20 if args.preview else 18,
        )
        size = settings.dimensions(scene.canvas)
        renderer = PillowRenderer(settings.antialias)
        renderer.validate(scene)
        directory = PROJECT / "output"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "timeline.json").write_text(json.dumps(scene.beat_times, indent=2) + "\n")
        (directory / "animations.json").write_text(
            json.dumps(sorted(scene.animation_events, key=lambda e: e["time"]), indent=2) + "\n"
        )
        if args.frames:
            print(storyboard(scene, directory / "frames", renderer))
            return
        if args.frame is not None:
            if not 0 <= args.frame < scene.duration:
                parser.error(f"--frame must be between 0 and {scene.duration:.3f} seconds")
            path = directory / f"frame-{args.frame:06.2f}s.png"
            renderer.frame(scene, args.frame, size).convert("RGB").save(path)
            print(path)
            return
        output = args.output or directory / ("good-math-preview.mp4" if args.preview else "good-math.mp4")
        print(
            f"Rendering {len(scene.beat_times)} beats, {scene.duration:.2f}s, "
            f"{size[0]}×{size[1]} at {settings.fps:g} fps…",
            flush=True,
        )
        path = scene.render(output, settings=settings, renderer=renderer, overwrite=args.overwrite)
        print(f"Rendered: {path}", flush=True)
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        parser.exit(1, f"good-math: {exc}\n")


if __name__ == "__main__":
    main()
