"""Render five diagram families in landscape or portrait, with JSON companions."""

import argparse
import json
from pathlib import Path

from faceless_champ import Canvas, FlowChamp, FlowScript, FlowTheme, Scene, Sequence
from faceless_champ.flow.examples import recipe


def showcase(portrait=False, clean=False):
    width, height = (600, 1000) if portrait else (1200, 675)
    scenes, documents = [], []
    theme = (
        FlowTheme(background="#000000", surface="#000000", foreground="#F4F3EE", stroke="#B1ADA1", accent="#C15F3C")
        if clean
        else None
    )
    for family in ("workflow", "system", "network", "idea-map", "circuit"):
        graph, script = recipe(family, portrait=portrait)
        center = FlowChamp(graph, width=width, height=height).state_at(0)["elements"]["n1"]["position"]
        destination = (center[0] + 45, center[1]) if portrait else (center[0], center[1] + 45)
        script.move("n1", destination, at=2.8, duration=1)
        script.scale("n1", 0.9, at=2.8, duration=1)
        script.rotate("n1", 8, at=2.8, duration=1)
        script.move("n1", center, at=4.8, duration=1)
        script.scale("n1", 1, at=4.8, duration=1)
        script.rotate("n1", 0, at=4.8, duration=1)
        if clean:
            document = script.to_dict()
            for action in document["actions"]:
                if action["kind"] == "draw":
                    action["tool"] = "none"
            script = FlowScript.from_dict(document)
        component = FlowChamp(graph, script, theme=theme, width=width, height=height, position=(width / 2, height / 2))
        if component.diagnostics:
            raise RuntimeError(component.diagnostics)
        scene = Scene(Canvas(width, height, component.theme.background))
        scene.add(component).wait(6)
        scenes.append(scene)
        documents.append((family, component.to_dict()))
    return Sequence(*scenes), documents


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portrait", action="store_true")
    parser.add_argument("--clean", action="store_true", help="Black/neutral/terracotta palette without drawing tools")
    parser.add_argument("--output", type=Path, default=Path("output/flowchamp"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    video, documents = showcase(args.portrait, args.clean)
    name = "portrait" if args.portrait else "landscape"
    args.output.mkdir(parents=True, exist_ok=True)
    for family, document in documents:
        (args.output / f"{name}-{family}.json").write_text(json.dumps(document, indent=2) + "\n")
    path = video.render(
        args.output / f"{name}.mp4",
        width=600 if args.portrait else 960,
        height=1000 if args.portrait else 540,
        fps=12,
        antialias=2,
        preset="veryfast",
        overwrite=args.overwrite,
    )
    print(path)


if __name__ == "__main__":
    main()
