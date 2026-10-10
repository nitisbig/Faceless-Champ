"""Preview-first CLI. All rendering and animation live in the main libraries."""

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / "output/.matplotlib"))
interpreter = ROOT / ".venv/bin/python"
if interpreter.exists() and Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
    os.execv(str(interpreter), [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]])

from main import programming_value_video

from faceless_champ import ExportSettings, PillowRenderer, StoryboardSample, render, render_storyboard, save_frame


def resolution(value):
    sizes = {"540p": (960, 540), "720p": (1280, 720), "1080p": (1920, 1080), "4k": (3840, 2160)}
    try:
        return sizes[value.lower()] if value.lower() in sizes else tuple(int(v) for v in value.lower().split("x"))
    except ValueError:
        raise argparse.ArgumentTypeError("Use 540p, 720p, 1080p, 4k, or WIDTHxHEIGHT") from None


def main():
    parser = argparse.ArgumentParser(description="Programming Value — default: 12-second 540p preview")
    parser.add_argument("--image", choices=("auto", "placeholder", "required"), default="auto")
    parser.add_argument("--version", choices=("v1", "v2"), default="v2")
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--fps", type=float)
    parser.add_argument("--resolution", "-r", type=resolution)
    parser.add_argument("--list-scenes", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--preview", action="store_true", help="Opening 0–12 seconds (the default)")
    modes.add_argument("--full", action="store_true", help="Explicit full-length export")
    modes.add_argument("--scene", help="One chapter; use --list-scenes")
    modes.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    modes.add_argument("--frame", type=float, metavar="SECONDS")
    modes.add_argument("--storyboard", action="store_true")
    modes.add_argument("--check", action="store_true", help="Validate source timing and attention cadence")
    modes.add_argument("--audit-layout", action="store_true", help="Check every final-frame geometry state")
    args = parser.parse_args()
    try:
        compiled = programming_value_video(args.image, args.version)
        video, report = compiled.composition, compiled.report
        if args.list_scenes:
            for chapter in report["segments"]:
                print(f"{chapter['id']:18} {chapter['start']:8.3f}–{chapter['end']:8.3f}s")
            return
        if args.check or args.audit_layout:
            if args.version != "v2":
                raise ValueError("v2 checks require --version v2")
            from scene.audit_v2 import audit_layout, check

            result = audit_layout(compiled, args.fps or 30) if args.audit_layout else check(compiled)
            directory = PROJECT / "output"
            directory.mkdir(exist_ok=True)
            filename = "layout-audit-v2.json" if args.audit_layout else "checks-v2.json"
            (directory / filename).write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps(result, indent=2))
            return
        size = args.resolution or ((1920, 1080) if args.full else (960, 540))
        if len(size) != 2:
            raise ValueError("Resolution must have two dimensions")
        settings = ExportSettings(
            width=size[0],
            height=size[1],
            fps=args.fps if args.fps is not None else (30 if args.full or args.version == "v2" else 15),
            antialias=2 if args.full else 1,
            crf=18 if args.full else 26,
            preset="medium" if args.full else "veryfast",
        )
        settings.dimensions(video.canvas)
        if args.version == "v2":
            from scene.renderer_v2 import FilmRenderer

            renderer = FilmRenderer(settings.antialias)
        else:
            renderer = PillowRenderer(settings.antialias)
        renderer.validate(video)
        directory = PROJECT / "output"
        stem = "programming-value-v2" if args.version == "v2" else "programming-value"
        if args.storyboard:
            samples = (
                [
                    StoryboardSample(e["start"] + (e["end"] - e["start"]) * fraction, f"{i + 1:02}-{e['kind']}")
                    for i, e in enumerate(report["visual_events"])
                    for fraction in (0.22, 0.78)
                ]
                if args.version == "v2"
                else [
                    StoryboardSample(c["start"] + (c["end"] - c["start"]) * fraction, c["id"])
                    for c in report["segments"]
                    for fraction in (0.12, 0.36, 0.62, 0.88)
                ]
            )
            result = render_storyboard(
                video,
                samples,
                args.output or directory / ("storyboard-v2" if args.version == "v2" else "storyboard"),
                renderer=renderer,
                size=(960, 540) if args.version == "v2" else (480, 270),
                overwrite=args.overwrite,
            )
            report["preview_samples"] = [s.time for s in samples]
        elif args.frame is not None:
            result = save_frame(
                video,
                args.frame,
                args.output or directory / f"{stem}-frame-{args.frame:08.3f}.png",
                size=size,
                renderer=renderer,
                overwrite=args.overwrite,
            )
            report["source_time"] = args.frame
        else:
            if args.scene:
                chapter = next((c for c in report["segments"] if c["id"] == args.scene), None)
                if chapter is None:
                    raise ValueError("Unknown scene; use --list-scenes")
                start, end, label = chapter["start"], chapter["end"], args.scene
            elif args.range:
                start, end = args.range
                label = f"{start:g}-{end:g}s"
            else:
                start, end, label = (
                    0,
                    video.duration if args.full else min(12, video.duration),
                    "full" if args.full else "opening-preview",
                )
            if not all(math.isfinite(t) for t in (start, end)) or not 0 <= start < end <= video.duration:
                raise ValueError(f"Range must satisfy 0 <= START < END <= {video.duration:g}")
            print(f"Render {start:.3f}–{end:.3f}s / {size[0]}×{size[1]} / {settings.fps:g} fps", flush=True)
            begun = time.perf_counter()

            def progress(done, total):
                if done == 0 or done == total or done % max(1, round(settings.fps * 2)) == 0:
                    elapsed = time.perf_counter() - begun
                    print(f"  {done}/{total} frames / {elapsed:.1f}s elapsed", flush=True)

            if args.full and args.version == "v2":
                from scene.export_v2 import export_full

                result = export_full(
                    compiled,
                    args.output or directory / f"{stem}-{label}.mp4",
                    settings,
                    renderer,
                    progress=progress,
                    overwrite=args.overwrite,
                )
            else:
                result = render(
                    video,
                    args.output or directory / f"{stem}-{label}.mp4",
                    settings=settings,
                    renderer=renderer,
                    start_time=start,
                    end_time=end,
                    progress=progress,
                    overwrite=args.overwrite,
                )
            report["source_range"] = [start, end]
        report["export_settings"] = {"width": size[0], "height": size[1], "fps": settings.fps}
        report["image_mode"] = args.image
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ("timeline-v2.json" if args.version == "v2" else "timeline.json")).write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print(result, flush=True)
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        parser.exit(1, f"programming-value: {exc}\n")


if __name__ == "__main__":
    main()
