"""Short feedback preview by default; --full opts into the complete film."""

import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
if not os.environ.get("FC_INSTALLED_ONLY"):
    interpreter = ROOT / ".venv/bin/python"
    if interpreter.exists() and Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        os.execv(str(interpreter), [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]])
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "facelesschamp-kit/src")]

from facelesschamp_kit import KitError, Project

from faceless_champ import PillowRenderer, StoryboardSample, render, render_storyboard, save_frame

SAMPLES = (
    4,
    11,
    21,
    25,
    26.5,
    30.5,
    32,
    38,
    45.5,
    54,
    58,
    64,
    79,
    92.5,
    101,
    110,
    117,
    124,
    140,
    146.8,
    155,
    159,
    164,
    170,
    180.5,
)
EXCERPTS = ((3, 6), (20, 23), (47, 50), (94, 97), (114, 117), (142, 145), (177, 180))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Burj Khalifa: default 0–12s, 960×540, 15 FPS")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    modes.add_argument("--scene", metavar="ID")
    modes.add_argument("--frame", type=float, metavar="TIME")
    modes.add_argument("--storyboard", action="store_true")
    modes.add_argument("--list-scenes", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--full", action="store_true")
    parser.add_argument("--quality", choices=("low", "high"), default="low")
    parser.add_argument("--fps", type=int, choices=(15, 30))
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        project = Project(PROJECT)
        compiled = project.build()
        composition, report = compiled.composition, compiled.report
        if args.list_scenes:
            for segment in report["segments"]:
                print(f"{segment['id']:18} {segment['start']:8.3f}–{segment['end']:8.3f}s")
            return
        if args.check:
            with PillowRenderer(1) as renderer:
                renderer.validate(composition)
            result = {
                **report,
                "audio_tracks": len(composition.audio),
                "audio_start": composition.audio[0].start,
                "full_export_verified": False,
                "preview_default": [0, 12],
            }
            print(json.dumps(result, indent=2))
            if args.output:
                if args.output.exists() and not args.overwrite:
                    raise FileExistsError("Check output exists; pass --overwrite")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(result, indent=2) + "\n")
            return
        profile = "final" if args.quality == "high" else "preview"
        settings = project.settings(compiled, profile)
        if args.fps:
            settings = replace(settings, fps=args.fps)
        size = settings.dimensions(composition.canvas)
        output = PROJECT / "output"
        with PillowRenderer(settings.antialias) as renderer:
            if args.storyboard:
                result = render_storyboard(
                    composition,
                    [StoryboardSample(t, f"{t:g}s") for t in SAMPLES],
                    args.output or output / "storyboard",
                    size=(960, 540),
                    renderer=renderer,
                    overwrite=args.overwrite,
                )
            elif args.frame is not None:
                if not 0 <= args.frame < compiled.duration:
                    raise ValueError("Frame time must lie inside the film")
                result = save_frame(
                    composition,
                    args.frame,
                    args.output or output / f"frame-{args.frame:g}s.png",
                    size=size,
                    renderer=renderer,
                    overwrite=args.overwrite,
                )
            else:
                start, end = (0, compiled.duration) if args.full else args.range or (0, 12)
                if args.scene:
                    segment = next((s for s in report["segments"] if s["id"] == args.scene), None)
                    if segment is None:
                        raise ValueError(f"Unknown scene {args.scene!r}; use --list-scenes")
                    start, end = segment["start"], segment["end"]
                if not 0 <= start < end <= compiled.duration:
                    raise ValueError("Range must lie inside the film with START < END")
                target = args.output or output / f"{'full' if args.full else f'{start:g}-{end:g}s'}-{profile}.mp4"
                print(f"Export {start:.3f}–{end:.3f}s | {size[0]}×{size[1]} | {settings.fps:g} FPS", flush=True)

                def progress(done, total):
                    if done == 0 or done == total or done % max(1, round(settings.fps * 2)) == 0:
                        print(f"  {done}/{total} frames", flush=True)

                result = render(
                    composition,
                    target,
                    settings=settings,
                    renderer=renderer,
                    start_time=start,
                    end_time=end,
                    overwrite=args.overwrite,
                    progress=progress,
                )
        print(result)
    except (OSError, ValueError, TypeError, ImportError, RuntimeError, KitError) as exc:
        parser.exit(1, f"burj-khalifa: {exc}\n")


if __name__ == "__main__":
    main()
