import argparse
from faceless_champ import (
    Canvas, CanvasItem, CodeCheckpoint, CodeEditor, PlaygroundCanvas,
    PlaygroundOutput, PlaygroundScript, PreparedPlayground, Scene,
    ValueBinding, prepare_playground,
)

SOURCE = "from faceless_champ.playground import (\n    runtime as pg,\n)\nx = VALUE\nanswer = x * x\npg.emit('answer', answer)\nprint(answer)\n"

def script():
    return PlaygroundScript([
        CodeCheckpoint("first", {"square.py": SOURCE.replace("VALUE", "6")},
                       "square.py", "square.py", 0, 1, 1),
        CodeCheckpoint("second", {"square.py": SOURCE.replace("VALUE", "7")},
                       "square.py", "square.py", 2.5, 4, 4),
    ], duration=6, mode="backend",
       items=[CanvasItem("answer", "variable", "Answer")],
       bindings=[ValueBinding("answer", "answer")])

def build_scene(asset):
    scene = Scene(Canvas(1280, 720, "#000000"))
    scene.add(CodeEditor(asset.script, width=780, height=600,
                         font_size=22, position=(420, 360)))
    scene.add(PlaygroundCanvas(asset, width=400, height=380, position=(1050, 250)))
    scene.add(PlaygroundOutput(asset, width=400, height=180, position=(1050, 570)))
    scene.wait(asset.script.duration)
    return scene

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true",
                        help="Execute trusted checkpoints explicitly")
    parser.add_argument("--cache", default=".playground-cache")
    parser.add_argument("--asset", help="Prepared directory for browser-free replay")
    parser.add_argument("--output", default="output/playground.mp4")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        asset = prepare_playground(script(), cache_dir=args.cache)
        print("Prepared:", asset.directory)
    elif args.asset:
        asset = PreparedPlayground(args.asset)
    else:
        parser.error("Use --prepare or --asset PATH")
    build_scene(asset).render(args.output, width=640, height=360, fps=15,
                             antialias=1, overwrite=args.overwrite)

if __name__ == "__main__":
    main()
