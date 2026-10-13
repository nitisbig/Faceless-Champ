"""Render reproducible recipe evidence and complete examples; review is external."""

import argparse
import json
from pathlib import Path

from faceless_champ import Canvas, StoryboardSample, render, render_storyboard
from facelesschamp_kit import BuildContext, Video
from facelesschamp_kit.recipes import apply_recipe, recipe_specs
from facelesschamp_kit.themes import MIDNIGHT
from PIL import Image, ImageDraw, ImageFont

from facelesschamp_agent.examples import create_example, prepare_example
from facelesschamp_agent.media import verify_media


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--recipes-only", action="store_true")
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    prepared = prepare_example(root / "prepared")
    report = {"recipes": [], "examples": [], "visual_review": "pending", "editorial_review": "pending"}
    posters = []
    for spec in recipe_specs():
        directory = root / "recipes" / spec.id
        directory.mkdir(parents=True, exist_ok=True)
        content = dict(spec.example)
        if spec.id == "code-result":
            content["prepared"] = str(prepared.directory)
        video = Video(BuildContext(root, Canvas(1920, 1080, MIDNIGHT.background)))
        apply_recipe(video.segment(spec.id, duration=4), spec.id, content)
        compiled = video.compile()
        media = directory / "preview.mp4"
        render(compiled.composition, media, width=960, height=540, fps=15, antialias=1, preset="veryfast")
        result = verify_media(
            media,
            width=960,
            height=540,
            fps=15,
            duration=4,
            require_audio=False,
            frame_directory=directory / "decoded",
            samples=[0.5, 2.2, 3.9],
        )
        sheet = render_storyboard(
            compiled.composition, [StoryboardSample(t, spec.id) for t in (0.5, 2.2, 3.9)], directory / "storyboard"
        )
        poster = Path(result["frames"][1]["path"])
        posters.append((spec.id, poster))
        row = {
            "recipe": spec.id,
            "content": content,
            "preview": str(media),
            "storyboard": str(sheet),
            "thumbnail": str(poster),
            "verification": result,
        }
        report["recipes"].append(row)
        (root / "verification.json").write_text(json.dumps(report, indent=2))
        print(spec.id, result["status"], flush=True)
    gallery = Image.new("RGB", (960, 5 * 310), "#18202b")
    draw = ImageDraw.Draw(gallery)
    font = ImageFont.truetype("DejaVuSans.ttf", 20)
    for i, (name, poster) in enumerate(posters):
        x, y = (i % 2) * 480, (i // 2) * 310
        with Image.open(poster) as frame:
            gallery.paste(frame.resize((480, 270)), (x, y))
        draw.text((x + 12, y + 279), name, font=font, fill="white")
    gallery.save(root / "recipe-gallery.png")
    if not args.recipes_only:
        for kind in ("narrated-system", "chart-explanation", "code-result"):
            project = create_example(root / "examples" / kind, kind)
            # Native 1080p/30 export, with one raster sample per pixel for a
            # bounded release fixture. Production scaffold retains its default AA.
            config = project.root / "facelesschamp.toml"
            config.write_text(config.read_text().replace("antialias = 2", "antialias = 1"))
            project.validate()
            storyboard = project.storyboard()
            preview = project.preview(start=0, end=min(3, project.plan.brief.duration))
            project.verify(preview["artifacts"][0]["path"])
            exported = project.render()
            report["examples"].append(
                {
                    "name": kind,
                    "project": str(project.root),
                    "storyboard": storyboard,
                    "render": exported,
                    "status": project.status().model_dump(mode="json"),
                }
            )
            (root / "verification.json").write_text(json.dumps(report, indent=2))
            print(kind, exported["verification"]["status"], flush=True)
    (root / "verification.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
