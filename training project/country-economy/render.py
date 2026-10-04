"""Full exports and previews of the Country Economy narration.

From this folder: python3 render.py --image placeholder
All reusable rendering behavior lives in faceless_champ in the main checkout.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from main import PROJECT, country_economy_video, timeline
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from scene.design import CANVAS

from faceless_champ import ExportSettings, PillowRenderer

PREVIEW_SIZE = (960, 540)
RESOLUTIONS = {
    "540p": PREVIEW_SIZE,
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "4k": (3840, 2160),
}


def resolution(value):
    tag = value.lower()
    if tag in RESOLUTIONS:
        return RESOLUTIONS[tag]
    match = re.fullmatch(r"(\d+)[x×](\d+)", tag)
    if match:
        size = tuple(int(part) for part in match.groups())
        try:
            ExportSettings(width=size[0], height=size[1]).dimensions(CANVAS)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(str(exc)) from exc
        return size
    raise argparse.ArgumentTypeError("Use 540p, 720p, 1080p, 4k, or WIDTHxHEIGHT (for example 1920x1080)")


def positive_fps(value):
    try:
        fps = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("FPS must be a positive finite number") from exc
    if not math.isfinite(fps) or fps < 0.001:
        raise argparse.ArgumentTypeError("FPS must be a finite number >= 0.001")
    return fps


def storyboard(video, plan, directory, renderer, overwrite=False, size=PREVIEW_SIZE):
    times = plan["storyboard_times"]
    paths = [directory / f"{i + 1:02d}-{time:07.3f}s.png" for i, time in enumerate(times)]
    output = directory / "storyboard.png"
    if not overwrite:
        existing = next((path for path in [*paths, output] if path.exists()), None)
        if existing:
            raise FileExistsError(f"Output already exists: {existing}; pass --overwrite")
    directory.mkdir(parents=True, exist_ok=True)
    sheet = PILImage.new("RGB", (1440, 304 * math.ceil(len(times) / 3)), "#F4F3EE")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(PROJECT.parents[1] / "src/faceless_champ/assets/DejaVuSans.ttf"), 15)
    for i, (time, path) in enumerate(zip(times, paths)):
        frame = renderer.frame(video, time, size).convert("RGB")
        frame.save(path)
        x, y = (i % 3) * 480, (i // 3) * 304
        sheet.paste(frame.resize((480, 270), PILImage.Resampling.LANCZOS), (x, y))
        chapter = next(c for c in plan["chapters"] if c["start"] <= time < c["end"])
        draw.text((x + 12, y + 278), f"{time:.2f}s  /  {chapter['id']}", font=font, fill="#292724")
    sheet.save(output)
    return output


def main():
    parser = argparse.ArgumentParser(description="Render the full Country Economy narration (default: 1080p / 30 fps).")
    parser.add_argument(
        "--image",
        choices=("auto", "placeholder", "required"),
        default="auto",
        help="auto loads image/1.png…6.png when present; placeholder always shows named boxes",
    )
    parser.add_argument("--fps", type=positive_fps, help="Frames per second, including fractional rates (default: 30)")
    parser.add_argument(
        "-r",
        "--resolution",
        type=resolution,
        metavar="TAG|WIDTHxHEIGHT",
        help="540p, 720p, 1080p, 4k, or custom 16:9 dimensions (default: 1080p)",
    )
    parser.add_argument("-o", "--output", type=Path, help="MP4, PNG, or storyboard directory according to mode")
    parser.add_argument("--overwrite", action="store_true", help="Replace the selected generated output")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--preview", action="store_true", help="Render the opening at 960×540 / 15 fps")
    modes.add_argument("--scene", metavar="ID", help="Preview a complete chapter; use --list-scenes for IDs")
    modes.add_argument("--range", nargs=2, type=float, metavar=("START", "END"), help="Source-audio seconds")
    modes.add_argument("--frame", type=float, metavar="SECONDS", help="Save a single source-time PNG")
    modes.add_argument(
        "--storyboard", "--frames", action="store_true", help="Chapter/key-moment PNGs and contact sheet"
    )
    modes.add_argument(
        "--all-preview", action="store_true", help="Explicitly render the entire narration at low quality"
    )
    modes.add_argument("--list-scenes", action="store_true", help="List exact cue-derived chapter boundaries")
    args = parser.parse_args()
    try:
        video = country_economy_video(args.image)
        plan = timeline(video)
        if args.list_scenes:
            for chapter in plan["chapters"]:
                print(f"{chapter['id']:15} {chapter['start']:7.3f}–{chapter['end']:7.3f}s  {chapter['title']}")
            return
        preview = args.preview or args.all_preview
        size = args.resolution or (PREVIEW_SIZE if preview else RESOLUTIONS["1080p"])
        fps = args.fps if args.fps is not None else (15 if preview else 30)
        settings = ExportSettings(
            width=size[0],
            height=size[1],
            fps=fps,
            antialias=1 if preview else 2,
            crf=26 if preview else 18,
            preset="veryfast" if preview else "medium",
        )
        settings.dimensions(video.canvas)
        renderer = PillowRenderer(settings.antialias)
        renderer.validate(video)
        directory = PROJECT / "output"
        directory.mkdir(parents=True, exist_ok=True)
        if args.storyboard:
            result = storyboard(video, plan, args.output or directory / "frames", renderer, args.overwrite, size)
        elif args.frame is not None:
            if not math.isfinite(args.frame) or not 0 <= args.frame < video.duration:
                raise ValueError(f"--frame must satisfy 0 <= seconds < {video.duration:g}")
            result = args.output or directory / "frames" / f"frame-{args.frame:07.3f}s.png"
            if result.suffix.lower() != ".png":
                raise ValueError("A single frame output must have a .png extension")
            if result.exists() and not args.overwrite:
                raise FileExistsError(f"Output already exists: {result}; pass --overwrite")
            result.parent.mkdir(parents=True, exist_ok=True)
            renderer.frame(video, args.frame, size).convert("RGB").save(result)
        else:
            if args.scene:
                chapter = next((c for c in plan["chapters"] if c["id"] == args.scene), None)
                if chapter is None:
                    raise ValueError("Unknown scene; choose " + ", ".join(c["id"] for c in plan["chapters"]))
                start, end, name = chapter["start"], chapter["end"], chapter["id"]
            elif args.range:
                start, end = args.range
                name = f"{start:g}-{end:g}s"
            elif args.preview:
                start, end, name = 0, plan["chapters"][0]["end"], "opening"
            else:
                start, end, name = 0, video.duration, "full"
            print(
                f"Render {start:.3f}–{end:.3f}s / {size[0]}×{size[1]} / {fps:g} fps / images: {args.image}", flush=True
            )

            def progress(completed, total):
                if completed == 0 or completed == total or completed % max(1, round(fps * 2)) == 0:
                    print(f"  {completed}/{total} frames", flush=True)

            result = video.render(
                args.output or directory / f"country-economy-{name}{'-preview' if preview else ''}.mp4",
                settings=settings,
                renderer=renderer,
                start_time=start,
                end_time=end,
                progress=progress,
                overwrite=args.overwrite,
            )
            plan["last_render_range"] = [start, end]
            plan["last_export_settings"] = {"width": size[0], "height": size[1], "fps": fps}
        (directory / "timeline.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print(result, flush=True)
    except (ValueError, TypeError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        parser.exit(1, f"country-economy: {exc}\n")


if __name__ == "__main__":
    main()
