"""Render the 45-second spring motion lesson; default: complete 960×540 preview."""

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
sys.path[:0] = [str(PROJECT), str(ROOT / "src")]

from scene import STORYBOARD, TOTAL_DURATION, build_shots, check

from faceless_champ import ExportSettings, PillowRenderer, Sequence, render, render_storyboard, save_frame

SIZES = {"preview": (960, 540), "high": (1920, 1080), "4k": (3840, 2160)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--check", action="store_true", help="Check timing, silence, spring properties and sampled bounds"
    )
    modes.add_argument("--storyboard", action="store_true", help="Save twelve annotated stills and a contact sheet")
    modes.add_argument("--frame", type=float, metavar="SECONDS")
    modes.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    parser.add_argument("--quality", choices=SIZES, default="preview")
    parser.add_argument("--fps", type=int, choices=(24, 30, 60), default=30)
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.frame is not None and not (math.isfinite(args.frame) and 0 <= args.frame < TOTAL_DURATION):
            raise ValueError("--frame must satisfy 0 <= SECONDS < 45")
        if args.range is not None:
            start, end = args.range
            if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= TOTAL_DURATION):
                raise ValueError("--range must satisfy 0 <= START < END <= 45")
        shots = build_shots()
        output_dir = PROJECT / "output"
        if args.check:
            payload = json.dumps(check(shots), indent=2)
            if args.output:
                if args.output.exists() and not args.overwrite:
                    raise FileExistsError(f"Output already exists: {args.output}; pass --overwrite")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(payload + "\n", encoding="utf-8")
            print(payload)
            return 0
        movie = Sequence(*(shot.scene for shot in shots))
        size = SIZES[args.quality]
        with PillowRenderer(1 if args.quality == "preview" else 2) as renderer:
            if args.storyboard:
                result = render_storyboard(
                    movie,
                    STORYBOARD,
                    args.output or output_dir / "storyboard",
                    renderer=renderer,
                    overwrite=args.overwrite,
                )
            elif args.frame is not None:
                result = save_frame(
                    movie,
                    args.frame,
                    args.output or output_dir / f"frame-{args.frame:g}s-{args.quality}.png",
                    renderer=renderer,
                    size=size,
                    overwrite=args.overwrite,
                )
            else:
                start, end = args.range or (0, TOTAL_DURATION)
                name = (
                    "preview"
                    if args.range is None and args.quality == "preview"
                    else (f"spring-motion-{start:g}-{end:g}s-{args.quality}")
                )
                began = time.monotonic()
                print(f"Silent {end - start:g}s export / {size[0]}×{size[1]} / {args.fps} fps", flush=True)

                def progress(done, total):
                    if done == total or done % (args.fps * 2) == 0:
                        print(f"  {done}/{total} frames / {time.monotonic() - began:.1f}s", flush=True)

                result = render(
                    movie,
                    args.output or output_dir / f"{name}.mp4",
                    renderer=renderer,
                    settings=ExportSettings(
                        width=size[0],
                        height=size[1],
                        fps=args.fps,
                        antialias=1 if args.quality == "preview" else 2,
                        crf=20 if args.quality == "preview" else 18,
                        preset="fast" if args.quality == "preview" else "medium",
                    ),
                    start_time=start,
                    end_time=end,
                    overwrite=args.overwrite,
                    progress=progress,
                )
        print(result)
        return 0
    except (OSError, ValueError, TypeError, RuntimeError, AssertionError) as exc:
        parser.exit(1, f"spring-motion: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
