"""Check, preview, frame and export Great Thinkers.

Examples:
    python render.py --check
    python render.py --frames
    python render.py --preview
    python render.py --render
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from faceless_champ import ExportProgress, ExportSettings, render, save_frame

from scene import DURATION, FPS, build_scene, check_scene

ROOT = Path(__file__).resolve().parent
FRAME_TIMES = {
    "01-intro": 1.4,
    "02-confucius": 9.4,
    "03-socrates": 16.8,
    "04-leonardo": 24.2,
    "05-newton": 31.2,
    "06-darwin": 38.6,
    "07-curie": 45.6,
    "08-einstein": 52.2,
    "09-outro": 58.2,
}


def settings_for(quality: str, fps: float) -> ExportSettings:
    return ExportSettings(
        quality=quality,
        fps=fps,
        antialias=1,
        backend="skia",
        crf=18,
        preset="medium",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--frames", action="store_true")
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--render", action="store_true")
    mode.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    parser.add_argument("--fps", type=float, default=float(FPS))
    parser.add_argument("--quality", choices=("ql", "qh", "qk"), default="qh")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    report = check_scene()
    if args.check or not any((args.frames, args.preview, args.render, args.range)):
        print(json.dumps(report, indent=2))
        return

    output_dir = ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    settings = settings_for(args.quality, args.fps)
    scene = build_scene()

    if args.frames:
        frame_dir = output_dir / "frames"
        frame_dir.mkdir(parents=True, exist_ok=True)
        for name, at in FRAME_TIMES.items():
            path = frame_dir / f"{name}.png"
            save_frame(scene, at, path, size=(1920, 1080), backend="skia", overwrite=True)
            print(path)
        return

    if args.preview:
        start, end = 0.0, 15.0
        filename = "preview-0-15.mp4"
    elif args.range:
        start, end = args.range
        filename = f"excerpt-{start:05.1f}-{end:05.1f}.mp4"
    else:
        start, end = 0.0, DURATION
        filename = "great-thinkers-60s.mp4"

    if not 0 <= start < end <= DURATION:
        parser.error(f"range must satisfy 0 <= START < END <= {DURATION}")
    output = args.output or output_dir / filename
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
