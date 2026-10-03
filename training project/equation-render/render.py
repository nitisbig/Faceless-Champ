"""Run from any directory. Assets are local; every video is exactly 60 seconds.

uv run --extra equations python 'training project/equation-render/render.py' --preview
uv run --extra equations python 'training project/equation-render/render.py'
uv run --extra equations python 'training project/equation-render/render.py' --frames
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / "output" / ".matplotlib"))

from download_assets import FONT, required_assets
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from scene import equation_video, timeline

from faceless_champ import COLOR_SCHEMES, ExportSettings, PillowRenderer


def storyboard(video, plan, directory, renderer):
    directory.mkdir(parents=True, exist_ok=True)
    sheet = PILImage.new("RGB", (1920, 4 * 406), plan["background"])
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(FONT), 18)
    for i, beat in enumerate(plan["equations"]):
        time = beat["preview"]
        frame = renderer.frame(video, time, (1280, 720)).convert("RGB")
        frame.save(directory / f"{beat['number']:02d}-{time:05.2f}s.png")
        x, y = (i % 3) * 640, (i // 3) * 406
        sheet.paste(frame.resize((640, 360), PILImage.Resampling.LANCZOS), (x, y))
        draw.text(
            (x + 16, y + 371), f"{beat['number']:02d} / {beat['title']} / {time:.2f}s", font=font, fill=beat["color"]
        )
    for i, time in enumerate((23.6, 47.6, 59.6), 1):
        renderer.frame(video, time, (1920, 1080)).convert("RGB").save(directory / f"canvas-{i}-complete.png")
    path = directory / "storyboard.png"
    sheet.save(path)
    return path


def main():
    parser = argparse.ArgumentParser(description="Render ten equations across three animated canvases in one minute.")
    parser.add_argument("--preview", action="store_true", help="Quick 720p / 24 fps video")
    parser.add_argument("-q", "--quality", choices=("ql", "qh", "qk", "720p", "1080p", "4k"))
    parser.add_argument("--fps", type=float, help="Override frame rate (default: 30; preview: 24)")
    parser.add_argument("--antialias", type=int, choices=(1, 2, 3, 4))
    parser.add_argument("--silent", action="store_true", help="Disable the quiet sound effects")
    parser.add_argument(
        "--color-scheme",
        choices=tuple(COLOR_SCHEMES),
        default="midnight",
        help="Formula, graph, and canvas palette (default: midnight)",
    )
    parser.add_argument("-o", "--output", type=Path, help="MP4 destination (default: this project's output folder)")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing MP4")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--frames", action="store_true", help="Save a storyboard and the three completed canvases")
    modes.add_argument("--frame", type=float, metavar="SECONDS", help="Save one PNG at a specified time")
    args = parser.parse_args()
    try:
        missing = [str(path.relative_to(ROOT)) for path in required_assets() if not path.is_file()]
        if missing:
            raise FileNotFoundError(
                "Missing assets: "
                + ", ".join(missing)
                + ". Run training project/equation-render/download_assets.py once."
            )
        video = equation_video(sound=not args.silent, scheme=args.color_scheme)
        settings = ExportSettings(
            quality=args.quality or ("ql" if args.preview else "qh"),
            fps=args.fps if args.fps is not None else (24 if args.preview else 30),
            antialias=args.antialias or 2,
            preset="veryfast" if args.preview else "medium",
            crf=18 if args.preview else 16,
        )
        size = settings.dimensions(video.canvas)
        renderer = PillowRenderer(settings.antialias)
        renderer.validate(video)
        plan = timeline(video)
        directory = PROJECT / "output"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "timeline.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        (directory / f"timeline-{args.color_scheme}.json").write_text(
            json.dumps(plan, indent=2) + "\n", encoding="utf-8"
        )
        frame_directory = directory / "frames" / args.color_scheme
        if args.frames:
            print(storyboard(video, plan, frame_directory, renderer))
            return
        if args.frame is not None:
            if not 0 <= args.frame < video.duration:
                parser.error("--frame must be between 0 and 60 seconds (exclusive)")
            frame_directory.mkdir(parents=True, exist_ok=True)
            output = frame_directory / f"frame-{args.frame:06.2f}s.png"
            renderer.frame(video, args.frame, size).convert("RGB").save(output)
            print(output)
            return
        suffix = "" if args.color_scheme == "midnight" else f"-{args.color_scheme}"
        output = args.output or directory / f"equations{suffix}{'-preview' if args.preview else ''}.mp4"
        print(
            f"Rendering 10 equations / 3 canvases / {video.duration:.2f}s / {size[0]}×{size[1]} / {settings.fps:g} fps…",
            flush=True,
        )
        print(video.render(output, settings=settings, renderer=renderer, overwrite=args.overwrite), flush=True)
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        parser.exit(1, f"equation-render: {exc}\n")


if __name__ == "__main__":
    main()
