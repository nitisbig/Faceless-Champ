"""Render the 45-second company-growth example from any working directory.

uv run python 'training project/company-growth/render.py' --preview
uv run python 'training project/company-growth/render.py' --frames
uv run python 'training project/company-growth/render.py' --overwrite
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from scene import company_growth_video, timeline

from faceless_champ import ExportSettings, PillowRenderer


def storyboard(video, plan, directory, renderer):
    directory.mkdir(parents=True, exist_ok=True)
    times = plan["storyboard_times"]
    cell_width, cell_height = 640, 394
    sheet = PILImage.new("RGB", (cell_width * 3, cell_height * math.ceil(len(times) / 3)), plan["background"])
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=19)
    for i, time in enumerate(times):
        frame = renderer.frame(video, time, (1280, 720)).convert("RGB")
        frame.save(directory / f"{i + 1:02d}-{time:05.2f}s.png")
        x, y = (i % 3) * cell_width, (i // 3) * cell_height
        sheet.paste(frame.resize((640, 360), PILImage.Resampling.LANCZOS), (x, y))
        chapter = next(c for c in plan["chapters"] if c["start"] <= time < c["end"])
        draw.text((x + 14, y + 367), f"{time:04.1f}s / {chapter['title']}", fill="#172A38", font=font)
    output = directory / "storyboard.png"
    sheet.save(output)
    return output


def main():
    parser = argparse.ArgumentParser(description="Render a 45-second light-mode US company growth story.")
    parser.add_argument("--preview", action="store_true", help="720p at 24 fps; default is 1080p at 30 fps")
    parser.add_argument("-q", "--quality", choices=("ql", "qh", "qk", "720p", "1080p", "4k"))
    parser.add_argument("--fps", type=float, help="Override the frame rate")
    parser.add_argument(
        "--antialias", type=int, choices=(1, 2, 3, 4), help="Override edge smoothing (preview: 1; default: 2)"
    )
    parser.add_argument("-o", "--output", type=Path, help="MP4 or PNG path, or storyboard directory, according to mode")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing video or frame")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--frames", "--storyboard", action="store_true", help="Save twelve frames and a contact sheet")
    modes.add_argument("--frame", type=float, metavar="SECONDS", help="Save a single frame between 0 and 45 seconds")
    args = parser.parse_args()
    try:
        video = company_growth_video()
        settings = ExportSettings(
            quality=args.quality or ("ql" if args.preview else "qh"),
            fps=args.fps if args.fps is not None else (24 if args.preview else 30),
            antialias=args.antialias if args.antialias is not None else (1 if args.preview else 2),
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
        if args.frames:
            print(storyboard(video, plan, args.output or directory / "frames", renderer))
            return
        if args.frame is not None:
            if not math.isfinite(args.frame) or not 0 <= args.frame < video.duration:
                parser.error("--frame must be finite and between 0 and 45 seconds (exclusive)")
            output = args.output or directory / "frames" / f"frame-{args.frame:06.2f}s.png"
            if output.suffix.lower() != ".png":
                raise ValueError("A single frame requires a .png output path")
            if output.exists() and not args.overwrite:
                raise FileExistsError(f"Frame already exists: {output}; pass --overwrite")
            output.parent.mkdir(parents=True, exist_ok=True)
            renderer.frame(video, args.frame, size).convert("RGB").save(output)
            print(output)
            return
        output = args.output or directory / f"company-growth{'-preview' if args.preview else ''}.mp4"
        print(f"Rendering {video.duration:.2f}s / {size[0]}×{size[1]} / {settings.fps:g} fps / light mode…", flush=True)
        interval = max(1, round(settings.fps * 2))

        def report_progress(completed, total):
            if completed == 0 or completed == total or completed % interval == 0:
                print(f"  Frames {completed}/{total} ({completed / total:.0%})", flush=True)

        print(
            video.render(
                output, settings=settings, renderer=renderer, overwrite=args.overwrite, progress=report_progress
            ),
            flush=True,
        )
    except (ValueError, TypeError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        parser.exit(1, f"company-growth: {exc}\n")


if __name__ == "__main__":
    main()
