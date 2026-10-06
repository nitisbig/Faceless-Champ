"""Preview-first rendering of the stock-analysis example from any cwd."""

import argparse
import json
import math
from pathlib import Path

from main import PROJECT, stock_analysis_video, timeline
from scene.design import CANVAS, CONFIG

from faceless_champ import ExportSettings, PillowRenderer, StoryboardSample, render_storyboard, save_frame


def fps_value(value):
    value = float(value)
    if not math.isfinite(value) or value < 0.001:
        raise argparse.ArgumentTypeError("FPS must be finite and at least 0.001")
    return value


def main():
    parser = argparse.ArgumentParser(description="Stock analysis: default is a short 540×810 / 12 fps opening preview.")
    parser.add_argument("--image", choices=("auto", "placeholder", "required"), default="auto")
    parser.add_argument("--fps", type=fps_value, default=CONFIG["preview"]["fps"])
    parser.add_argument("--resolution", choices=("preview", "design"), default="preview")
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--list-scenes", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--preview", action="store_true", help="Opening preview (also the default)")
    modes.add_argument("--scene", metavar="ID", help="Preview one chapter")
    modes.add_argument("--range", nargs=2, type=float, metavar=("START", "END"), help="Original audio seconds")
    modes.add_argument("--frame", type=float, metavar="SECONDS", help="Save a PNG at original source time")
    modes.add_argument("--storyboard", action="store_true", help="Save key frames and a contact sheet")
    modes.add_argument("--full", action="store_true", help="Explicit opt-in to the entire video")
    args = parser.parse_args()
    try:
        video = stock_analysis_video(args.image)
        plan = timeline(video)
        if args.list_scenes:
            for chapter in plan["chapters"]:
                print(f"{chapter['id']:14} {chapter['start']:7.3f}–{chapter['end']:7.3f}s / {chapter['title']}")
            return
        size = (
            (CONFIG["preview"]["width"], CONFIG["preview"]["height"])
            if args.resolution == "preview"
            else (CANVAS.width, CANVAS.height)
        )
        renderer = PillowRenderer(2 if args.full and args.resolution == "design" else 1)
        directory = PROJECT / "output"
        if args.storyboard:
            samples = [
                StoryboardSample(t, next(c["id"] for c in plan["chapters"] if c["start"] <= t < c["end"]))
                for t in plan["storyboard_times"]
            ]
            result = render_storyboard(
                video,
                samples,
                args.output or directory / "storyboard",
                size=(360, 540),
                renderer=renderer,
                overwrite=args.overwrite,
            )
        elif args.frame is not None:
            result = save_frame(
                video,
                args.frame,
                args.output or directory / f"frame-{args.frame:07.3f}s.png",
                size=size,
                renderer=renderer,
                overwrite=args.overwrite,
            )
        else:
            if args.scene:
                chapter = next((c for c in plan["chapters"] if c["id"] == args.scene), None)
                if chapter is None:
                    raise ValueError("Unknown scene; use --list-scenes")
                start, end, name = chapter["start"], chapter["end"], chapter["id"]
            elif args.range:
                start, end = args.range
                name = f"{start:g}-{end:g}s"
            elif args.full:
                start, end, name = 0, video.duration, "full"
            else:
                start, end, name = 0, plan["chapters"][0]["end"], "opening"
            settings = ExportSettings(
                width=size[0],
                height=size[1],
                fps=args.fps,
                antialias=renderer.antialias,
                crf=18 if args.full else 27,
                preset="medium" if args.full else "veryfast",
            )
            print(f"Render {start:.3f}–{end:.3f}s / {size[0]}×{size[1]} / {args.fps:g} fps / {args.image}", flush=True)

            def progress(done, total):
                if done == 0 or done == total or done % max(1, round(args.fps * 2)) == 0:
                    print(f"  {done}/{total} frames", flush=True)

            suffix = "" if args.full else "-preview"
            result = video.render(
                args.output or directory / f"stock-analysis-{name}{suffix}.mp4",
                settings=settings,
                renderer=renderer,
                start_time=start,
                end_time=end,
                overwrite=args.overwrite,
                progress=progress,
            )
            plan["last_render_range"] = [start, end]
            plan["last_export_settings"] = {"width": size[0], "height": size[1], "fps": args.fps}
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "timeline.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        print(result)
    except (ValueError, TypeError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        parser.exit(1, f"stock-analysis: {exc}\n")


if __name__ == "__main__":
    main()
