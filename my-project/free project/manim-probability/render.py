"""45-second probability simulations: native Manim + FacelessChamp export."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from faceless_champ import Canvas, ExportProgress, Scene, Viewport, create_renderer, render
from faceless_champ.integrations.manim import ManimRenderOptions, ManimSceneSpec, prepare_manim

ROOT = Path(__file__).resolve().parent
DURATION = 45.0


def build_scene(source, width, height):
    if source.duration != DURATION:
        raise ValueError(f"Expected 45 seconds; producer returned {source.duration}")
    return (
        Scene(Canvas(width, height, "#000000"))
        .add(Viewport(source, width=width, height=height, position=(width / 2, height / 2)))
        .wait(DURATION)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manim-python", default=os.environ.get("FC_MANIM_PYTHON", sys.executable))
    parser.add_argument("--preview", action="store_true", help="Full 45-second 640×360/15 preview")
    parser.add_argument("--frames", action="store_true", help="Prepare at 640×360/4 fps and composite key frames only")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            parser.error(f"Missing {tool}; install native prerequisites")
    width, height, fps = (640, 360, 15) if args.preview or args.frames else (1920, 1080, 30)
    if args.frames:
        fps = 4
    output = args.output or ROOT / "output" / ("preview.mp4" if args.preview else "probability.mp4")
    if not args.frames and output.exists() and not args.overwrite:
        parser.error("Output exists; pass --overwrite")
    source = prepare_manim(
        ManimSceneSpec(ROOT / "probability_scene.py", "ProbabilitySimulations"),
        cache_dir=ROOT / "output" / "manim-cache",
        python=args.manim_python,
        options=ManimRenderOptions(width=width, height=height, fps=fps, background="#000000"),
    )
    scene = build_scene(source, width, height)
    if args.frames:
        directory = ROOT / "output" / "frames"
        directory.mkdir(parents=True, exist_ok=True)
        with create_renderer("pillow", antialias=1) as renderer:
            for timestamp in (4, 15, 23, 30, 36, 44):
                image = renderer.frame(scene, timestamp, (width, height))
                assert image.getpixel((0, 0))[:3] == (0, 0, 0)
                image.save(directory / f"{timestamp:02d}.png")
        print(f"45-second timeline: {source.frame_count} prepared frames; key frames: {directory}")
    else:
        with ExportProgress() as progress:
            render(
                scene,
                output,
                width=width,
                height=height,
                fps=fps,
                antialias=1,
                overwrite=args.overwrite,
                progress=progress,
            )
        print(output)


if __name__ == "__main__":
    main()
