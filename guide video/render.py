#!/usr/bin/env python3
"""Preview by default; explicit quality without a range exports the complete guide."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parent
interpreter = ROOT / ".venv/bin/python"
if interpreter.exists() and Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
    os.execv(str(interpreter), [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]])
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "facelesschamp-kit/src")]
from scene.spec import PROJECT, chapters, prepare
from scene.story import build_video

from faceless_champ import ExportSettings, PillowRenderer, StoryboardSample, render, render_storyboard, save_frame

SIZES = {"low": (1280, 720), "high": (1920, 1080), "4k": (3840, 2160)}
SAMPLES = (
    3.5,
    9,
    15,
    25,
    39,
    50.8,
    59,
    70,
    83,
    95,
    110,
    118,
    128,
    136,
    146,
    155,
    164,
    173,
    182,
    190,
    201,
    207,
    210,
    214,
    222,
    228,
    234,
    238,
    245,
    252,
    255,
    259,
    262.8,
    270,
    278,
    283.5,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality", choices=SIZES, default=None)
    parser.add_argument("--fps", type=int, choices=(10, 30), default=None)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--frame", type=float, metavar="SECONDS")
    modes.add_argument("--storyboard", action="store_true")
    modes.add_argument("--list-scenes", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.prepare:
            print(json.dumps(prepare(), indent=2))
            return
        if args.list_scenes:
            for chapter in chapters():
                print(f"{chapter['id']:16} {chapter['start']:8.3f}–{chapter['end']:8.3f}s")
            return
        video, report = build_video()
        if args.check:
            from scene.audit import check

            result = check(video, report)
            directory = PROJECT / "output"
            directory.mkdir(exist_ok=True)
            (directory / "preflight.json").write_text(json.dumps(result, indent=2))
            print(json.dumps(result, indent=2))
            return
        quality = args.quality or "low"
        fps = args.fps or (10 if quality == "low" else 30)
        size = SIZES[quality]
        aa = 1 if quality == "low" else 2
        renderer = PillowRenderer(aa, frame_cache_mb=48, code_cache_mb=24)
        directory = PROJECT / "output"
        if args.frame is not None:
            result = save_frame(
                video,
                args.frame,
                args.output or directory / f"frame-{args.frame:g}s.png",
                renderer=renderer,
                size=size,
                overwrite=args.overwrite,
            )
        elif args.storyboard:
            result = render_storyboard(
                video,
                [StoryboardSample(t, f"{t:g}s") for t in SAMPLES],
                args.output or directory / "storyboard",
                renderer=renderer,
                size=(960, 540),
                columns=3,
                overwrite=args.overwrite,
            )
        else:
            start, end = args.range or ((0, video.duration) if args.quality else (0, 12))
            if not 0 <= start < end <= video.duration:
                raise ValueError(f"Range must satisfy 0 <= START < END <= {video.duration:g}")
            label = "full" if start == 0 and end == video.duration else f"{start:g}-{end:g}s"
            destination = args.output or directory / f"guide-{label}-{quality}-{fps}fps.mp4"
            settings = ExportSettings(
                width=size[0],
                height=size[1],
                fps=fps,
                antialias=aa,
                crf=23 if quality == "low" else 18,
                preset="veryfast" if quality == "low" else "medium",
            )
            print(f"Export {start:.3f}–{end:.3f}s | {size[0]}×{size[1]} | {fps} FPS", flush=True)
            began = time.monotonic()

            def progress(done, total):
                if done == 0 or done == total or done % (fps * 2) == 0:
                    print(f"  {done}/{total} frames | {time.monotonic() - began:.1f}s", flush=True)

            result = render(
                video,
                destination,
                settings=settings,
                renderer=renderer,
                start_time=start,
                end_time=end,
                overwrite=args.overwrite,
                progress=progress,
            )
        print(result)
    except (OSError, ValueError, TypeError, ImportError, RuntimeError) as exc:
        message = str(exc)
        if any(code in message for code in ("PLAYGROUND_UNPREPARED", "PLAYGROUND_STALE", "PLAYGROUND_ASSET")):
            message += "; run python3 render.py --prepare"
        parser.exit(1, f"guide-video: {message}\n")


if __name__ == "__main__":
    main()
