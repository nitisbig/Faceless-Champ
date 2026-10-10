"""Export the complete tutorial, or an explicit source-clock preview range."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
interpreter = ROOT / ".venv/bin/python"
if interpreter.exists() and Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
    os.execv(str(interpreter), [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]])
# Prefer this checkout so the wrapper also works from another working directory.
sys.path.insert(0, str(ROOT / "src"))

from scene.story import build_video

from faceless_champ import ExportSettings, PillowRenderer, StoryboardSample, render, render_storyboard, save_frame

SIZES = {"low": (1280, 720), "high": (1920, 1080), "4k": (3840, 2160)}
SAMPLES = (
    5,
    12,
    17.8,
    26.5,
    29.2,
    35.2,
    40,
    48.8,
    61,
    74,
    79.5,
    83.5,
    89.5,
    102,
    109,
    114.5,
    118,
    121.6,
    124.5,
    128,
    135,
    139.5,
    149,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description="CodingChamp: default is the FULL tutorial at 1080p / 30 FPS")
    parser.add_argument("--quality", choices=SIZES, default="high")
    parser.add_argument("--fps", type=int, choices=(20, 30, 60), default=30)
    parser.add_argument("--theme", choices=("midnight", "ocean", "paper"), default="midnight")
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    modes.add_argument("--frame", type=float, metavar="SECONDS")
    modes.add_argument("--storyboard", action="store_true")
    modes.add_argument("--list-scenes", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        video, report = build_video(args.theme)
        if args.list_scenes:
            for chapter in report["chapters"]:
                print(f"{chapter['id']:16} {chapter['start']:8.3f}–{chapter['end']:8.3f}s")
            return
        if args.check:
            from scene.audit import check

            print(json.dumps(check(video, report), indent=2))
            return
        width, height = SIZES[args.quality]
        settings = ExportSettings(
            width=width,
            height=height,
            fps=args.fps,
            antialias=1,
            crf=23 if args.quality == "low" else 18,
            preset="veryfast" if args.quality == "low" else "medium",
        )
        renderer = PillowRenderer(1)
        directory = PROJECT / "output"
        prefix = f"coding-video-{args.theme}"
        if args.storyboard:
            result = render_storyboard(
                video,
                [StoryboardSample(t, f"{t:g}s") for t in SAMPLES],
                args.output or directory / f"storyboard-{args.theme}",
                renderer=renderer,
                size=(640, 360),
                overwrite=args.overwrite,
            )
        elif args.frame is not None:
            result = save_frame(
                video,
                args.frame,
                args.output or directory / f"{prefix}-{args.frame:g}s.png",
                renderer=renderer,
                size=(width, height),
                overwrite=args.overwrite,
            )
        else:
            start, end = args.range or (0, video.duration)
            label = f"{start:g}-{end:g}s" if args.range else "full"
            output = args.output or directory / f"{prefix}-{label}-{args.quality}-{args.fps}fps.mp4"
            print(f"Export {start:.3f}–{end:.3f}s | {width}×{height} | {args.fps} FPS", flush=True)
            began = time.monotonic()

            def progress(done, total):
                if done == 0 or done == total or done % (args.fps * 2) == 0:
                    print(f"  {done}/{total} frames | {time.monotonic() - began:.1f}s", flush=True)

            result = render(
                video,
                output,
                settings=settings,
                renderer=renderer,
                start_time=start,
                end_time=end,
                overwrite=args.overwrite,
                progress=progress,
            )
        print(result)
    except (OSError, ValueError, TypeError, ImportError, RuntimeError) as exc:
        parser.exit(1, f"coding-video: {exc}\n")


if __name__ == "__main__":
    main()
