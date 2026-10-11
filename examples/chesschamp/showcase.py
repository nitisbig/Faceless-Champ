"""Run from any directory: python showcase.py [-o output/chesschamp.mp4]."""
import argparse
from pathlib import Path

from faceless_champ import Canvas, ChessChamp, ChessScript, Scene, render


def build(data):
    script = ChessScript.from_json(data)
    scene = Scene(Canvas(1600, 900, "#171E1A"))
    scene.add(ChessChamp(script, position=(800, 450)))
    scene.wait(script.duration)
    return scene


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).with_name("data.json"))
    parser.add_argument("-o", "--output", type=Path, default=Path("output/chesschamp.mp4"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    render(build(args.data), args.output, width=1280, height=720, fps=30, overwrite=args.overwrite)
