"""Check the silent Python-functions scene; rendering requires an explicit mode."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
INTERPRETER = ROOT / ".venv/bin/python"
if INTERPRETER.is_file() and Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
    os.execv(str(INTERPRETER), [str(INTERPRETER), str(Path(__file__).resolve()), *sys.argv[1:]])

# Resolve this scene and the public APIs from this checkout, from any working directory.
sys.path[:0] = [str(PROJECT), str(ROOT / "src"), str(ROOT / "facelesschamp-kit/src")]

from scene import TOTAL_DURATION, build_video

from faceless_champ import ExportSettings, PillowRenderer, render, save_frame

SIZES = {"low": (960, 540), "high": (1920, 1080), "4k": (3840, 2160)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Check timing, silence, code and layout (the default)")
    modes.add_argument("--frame", type=float, metavar="SECONDS", help="Save a PNG at source time")
    modes.add_argument("--range", nargs=2, type=float, metavar=("START", "END"), help="Render a source-time excerpt")
    modes.add_argument("--full", action="store_true", help="Render the complete silent 120-second scene")
    parser.add_argument("--quality", choices=SIZES, default="high")
    parser.add_argument("--fps", type=int, choices=(15, 30, 60), default=30)
    parser.add_argument("--output", "-o", type=Path, help="Output PNG, MP4, or optional check-report JSON")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.frame is not None and not (math.isfinite(args.frame) and 0 <= args.frame < TOTAL_DURATION):
            raise ValueError("--frame must satisfy 0 <= SECONDS < 120")
        if args.range is not None:
            start, end = args.range
            if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= TOTAL_DURATION):
                raise ValueError("--range must satisfy 0 <= START < END <= 120")

        video, report = build_video()
        if not math.isclose(video.duration, 120.0, rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"Expected a 120-second scene, got {video.duration:g}")
        if video.audio:
            raise ValueError("This training scene must contain no audio")

        if args.check or not (args.full or args.range is not None or args.frame is not None):
            from checks import check

            payload = json.dumps(check(video, report), indent=2)
            if args.output is not None:
                if args.output.exists() and not args.overwrite:
                    raise FileExistsError(f"Output already exists: {args.output}; pass --overwrite")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(payload + "\n", encoding="utf-8")
            print(payload)
            return 0

        size = SIZES[args.quality]
        antialias = 1 if args.quality == "low" else 2
        output_dir = PROJECT / "output"
        with PillowRenderer(antialias, frame_cache_mb=48, code_cache_mb=24) as renderer:
            if args.frame is not None:
                result = save_frame(
                    video,
                    args.frame,
                    args.output or output_dir / f"python-functions-{args.frame:g}s-{args.quality}.png",
                    renderer=renderer,
                    size=size,
                    overwrite=args.overwrite,
                )
            else:
                start, end = args.range or (0.0, TOTAL_DURATION)
                label = "full" if args.full else f"{start:g}-{end:g}s"
                destination = args.output or output_dir / f"python-functions-{label}-{args.quality}-{args.fps}fps.mp4"
                settings = ExportSettings(
                    width=size[0],
                    height=size[1],
                    fps=args.fps,
                    antialias=antialias,
                    crf=23 if args.quality == "low" else 18,
                    preset="veryfast" if args.quality == "low" else "medium",
                )
                print(f"Silent export {start:g}–{end:g}s | {size[0]}×{size[1]} | {args.fps} FPS", flush=True)
                began = time.monotonic()

                def progress(done: int, total: int) -> None:
                    if done == 0 or done == total or done % (args.fps * 2) == 0:
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
        return 0
    except (OSError, ValueError, TypeError, ImportError, RuntimeError, AssertionError) as exc:
        parser.exit(1, f"python-functions: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
