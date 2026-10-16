"""Check by default. Every media export requires an explicit mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path[:0] = [str(REPO / "src"), str(ROOT)]

from scene import DURATION, build_scene, check_scene

from faceless_champ import render, save_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--render", action="store_true", help="Render the complete 14.96-second opening")
    mode.add_argument("--frame", type=float, metavar="TIME")
    mode.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fps", type=int, choices=(24, 30, 60), default=60)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if (
        args.width < 2
        or args.height < 2
        or args.width % 2
        or args.height % 2
        or abs(args.width / args.height - 16 / 9) > 0.002
    ):
        parser.error("Use positive, even 16:9 dimensions")
    if args.frame is not None and not 0 <= args.frame < DURATION:
        parser.error(f"--frame must be in [0, {DURATION})")
    if args.range and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error(f"--range must satisfy 0 <= START < END <= {DURATION}")
    report = check_scene()
    if not args.render and args.frame is None and args.range is None:
        print(json.dumps(report, indent=2))
        return
    scene = build_scene()
    if args.frame is not None:
        output = args.output or ROOT / "output" / f"frame-{args.frame:06.3f}.png"
        save_frame(scene, args.frame, output, size=(args.width, args.height), overwrite=args.overwrite)
    else:
        output = args.output or ROOT / "output" / "opening.mp4"
        start, end = args.range or (0, DURATION)
        render(
            scene,
            output,
            width=args.width,
            height=args.height,
            fps=args.fps,
            start_time=start,
            end_time=end,
            antialias=2,
            crf=18,
            overwrite=args.overwrite,
        )
    print(output)


if __name__ == "__main__":
    main()
