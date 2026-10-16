"""Check by default. Every media export requires an explicit mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO / "facelesschamp-kit/src"), str(ROOT)]

from scene import DURATION, build_scene, check_scene

from faceless_champ import ExportProgress, ExportSettings, render, save_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument(
        "--full",
        "--render",
        dest="render",
        action="store_true",
        help="Render all authored content (14.96-second opening)",
    )
    mode.add_argument("--frame", type=float, metavar="TIME")
    mode.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fps", type=float, default=60)
    parser.add_argument("--quality", choices=("low", "high", "4k"), default="high")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    settings = ExportSettings(
        quality={"low": "ql", "high": "qh", "4k": "qk"}[args.quality],
        fps=args.fps,
        width=args.width,
        height=args.height,
        antialias=2,
    )
    try:
        from faceless_champ import Canvas

        width, height = settings.dimensions(Canvas(1920, 1080))
    except ValueError as exc:
        parser.error(str(exc))
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
        save_frame(scene, args.frame, output, size=(width, height), overwrite=args.overwrite)
    else:
        output = args.output or ROOT / "output" / "opening.mp4"
        start, end = args.range or (0, DURATION)
        with ExportProgress() as progress:
            render(
                scene,
                output,
                settings=settings,
                start_time=start,
                end_time=end,
                overwrite=args.overwrite,
                progress=progress,
            )
    print(output)


if __name__ == "__main__":
    main()
