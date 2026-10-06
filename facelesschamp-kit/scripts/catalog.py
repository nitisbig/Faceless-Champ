"""Generate reproducible thumbnails and short motion previews for all six blocks."""

import argparse
import json
from pathlib import Path

from faceless_champ import Canvas, render, save_frame

from facelesschamp_kit import BuildContext, Video
from facelesschamp_kit.blocks import Comparison, Heading, ImageCard, MetricCard, StepList, TextPanel
from facelesschamp_kit.themes import LIGHT, MIDNIGHT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    blocks = [
        Heading("One clear idea", variant="accent"),
        TextPanel("Reusable content with measured typography.", "Context"),
        MetricCard(42, "Reusable components"),
        ImageCard("your-artwork", "Explicit media placeholders", mode="placeholder"),
        Comparison("Repeated setup", "Shared building blocks"),
        StepList(("Compose", "Preview", "Export")),
    ]
    catalog = []
    for block in blocks:
        name = type(block).__name__
        print(name, flush=True)
        for theme in (MIDNIGHT, LIGHT):
            for size in ((1080, 1920), (1920, 1080)):
                ctx = BuildContext(args.output, Canvas(*size, theme.background), theme)
                video = Video(ctx)
                video.segment("demo", duration=2).add(block, enter="stagger" if name == "StepList" else "pop")
                compiled = video.compile()
                tag = f"{name}-{theme.name}-{'portrait' if size[0] < size[1] else 'landscape'}"
                output_size = (270, 480) if size[0] < size[1] else (480, 270)
                save_frame(compiled.composition, 1, args.output / f"{tag}.png", size=output_size, overwrite=True)
                if theme is MIDNIGHT and size[0] < size[1]:
                    render(
                        compiled.composition,
                        args.output / f"{name}.mp4",
                        width=270,
                        height=480,
                        fps=15,
                        antialias=1,
                        preset="veryfast",
                        overwrite=True,
                    )
                catalog.append({"block": name, "theme": theme.name, "size": size, "thumbnail": f"{tag}.png"})
    (args.output / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")


if __name__ == "__main__":
    main()
