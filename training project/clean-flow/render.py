#!/usr/bin/env python3
"""Inspect or render the silent clean-flow tour. Default: a 0–6s low preview."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
interpreter = ROOT / ".venv/bin/python"
if interpreter.is_file() and Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
    os.execv(str(interpreter), [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]])
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "facelesschamp-kit/src"), str(PROJECT)]
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".fc-kit/matplotlib"))

from facelesschamp_kit import Project
from videos.main import STORYBOARD_TIMES, TOTAL_DURATION, scene_windows

from faceless_champ import ExportSettings, PillowRenderer, StoryboardSample, render, render_storyboard, save_frame

SIZES = {"low": (960, 540), "high": (1920, 1080), "4k": (3840, 2160)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quality", choices=SIZES)
    parser.add_argument("--fps", type=int, choices=(15, 30, 60))
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--prepare", action="store_true", help="Execute checkpoints and capture the local HTML")
    modes.add_argument("--check", action="store_true", help="Replay assets and check timing/features/layout/silence")
    modes.add_argument("--frame", type=float, metavar="SECONDS")
    modes.add_argument("--storyboard", action="store_true")
    modes.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    modes.add_argument("--full", action="store_true", help="Explicitly render the complete silent 60-second tour")
    modes.add_argument("--list-scenes", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.list_scenes:
            for row in scene_windows():
                print(
                    f"{row['id']:12} {row['nominal_start']:2g}–{row['nominal_end']:2g}s "
                    f"(flow window {row['start']:g}–{row['end']:g}s)"
                )
            return 0
        project = Project(PROJECT)
        if args.prepare:
            report = project.prepare("main")
            print(json.dumps({"prepared_assets": report["prepared_assets"], "duration": report["duration"]}, indent=2))
            return 0
        compiled = project.build("main", strict_assets=True)
        output_dir = PROJECT / "output"
        if args.check:
            from checks import check

            report = check(compiled)
            output_dir.mkdir(exist_ok=True)
            destination = args.output or output_dir / "preflight.json"
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(report, indent=2))
            print(json.dumps(report, indent=2))
            return 0
        quality = args.quality or ("high" if args.full else "low")
        fps = args.fps or (15 if quality == "low" else 30)
        size = SIZES[quality]
        aa = 1 if quality == "low" else 2
        renderer = PillowRenderer(aa, frame_cache_mb=48, code_cache_mb=24)
        if args.frame is not None:
            if not 0 <= args.frame < TOTAL_DURATION:
                raise ValueError("--frame must be between 0 (inclusive) and 60 (exclusive)")
            result = save_frame(
                compiled.composition,
                args.frame,
                args.output or output_dir / f"frame-{args.frame:g}s-{quality}.png",
                renderer=renderer,
                size=size,
                overwrite=args.overwrite,
            )
        elif args.storyboard:
            result = render_storyboard(
                compiled.composition,
                [StoryboardSample(t, f"{t:g}s") for t in STORYBOARD_TIMES],
                args.output or output_dir / "storyboard",
                renderer=renderer,
                size=(960, 540),
                columns=4,
                overwrite=args.overwrite,
            )
        else:
            start, end = args.range or ((0, TOTAL_DURATION) if args.full else (0, 6))
            if not 0 <= start < end <= TOTAL_DURATION:
                raise ValueError("Range must satisfy 0 <= START < END <= 60")
            label = "full" if args.full else f"{start:g}-{end:g}s"
            destination = args.output or output_dir / f"clean-flow-{label}-{quality}-{fps}fps.mp4"
            settings = ExportSettings(
                width=size[0],
                height=size[1],
                fps=fps,
                antialias=aa,
                crf=23 if quality == "low" else 18,
                preset="veryfast" if quality == "low" else "medium",
            )
            print(f"Silent export {start:g}–{end:g}s | {size[0]}×{size[1]} | {fps} FPS", flush=True)
            began = time.monotonic()

            def progress(done, total):
                if done == 0 or done == total or done % (fps * 2) == 0:
                    elapsed = time.monotonic() - began
                    print(f"  {done}/{total} frames ({done / total:.1%}) | {elapsed:.1f}s", flush=True)

            result = render(
                compiled.composition,
                destination,
                settings=settings,
                renderer=renderer,
                start_time=start,
                end_time=end,
                overwrite=args.overwrite,
                progress=progress,
            )
        print(result)
        return 0
    except (OSError, ValueError, TypeError, ImportError, RuntimeError, AssertionError) as exc:
        parser.exit(1, f"clean-flow: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
