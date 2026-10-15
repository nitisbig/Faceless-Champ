"""Check Networking Explained v2; rendering requires an explicit mode."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from dataclasses import replace
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
INTERPRETER = ROOT / ".venv/bin/python"
if INTERPRETER.is_file() and Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
    os.execv(str(INTERPRETER), [str(INTERPRETER), str(Path(__file__).resolve()), *sys.argv[1:]])

# Resolve the scene and public APIs from this checkout, from any working directory.
sys.path[:0] = [str(PROJECT), str(ROOT / "src"), str(ROOT / "facelesschamp-kit/src")]

from facelesschamp_kit import KitError, Project
from scene import CHAPTERS, STORYBOARD_TIMES, TITLE, TOTAL_DURATION

from faceless_champ import PillowRenderer, StoryboardSample, render, render_storyboard, save_frame


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Check timing, silence, actions and layout (the default)")
    modes.add_argument("--frame", type=float, metavar="SECONDS", help="Save one PNG at source time")
    modes.add_argument("--range", nargs=2, type=float, metavar=("START", "END"), help="Render a source-time excerpt")
    modes.add_argument("--storyboard", action="store_true", help="Save story-beat PNGs and a contact sheet")
    modes.add_argument("--list-scenes", action="store_true", help="List the story chapters within the continuous scene")
    modes.add_argument("--full", action="store_true", help="Render the complete silent 120-second scene")
    parser.add_argument("--quality", choices=("low", "high"), default="high")
    parser.add_argument("--fps", type=int, choices=(15, 30, 60), help="Defaults to 60; low quality defaults to 30")
    parser.add_argument(
        "--output", "-o", type=Path, help="PNG, MP4, storyboard directory, or optional check-report JSON"
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.frame is not None and not (math.isfinite(args.frame) and 0 <= args.frame < TOTAL_DURATION):
            raise ValueError(f"--frame must satisfy 0 <= SECONDS < {TOTAL_DURATION:g}")
        if args.range is not None:
            start, end = args.range
            if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= TOTAL_DURATION):
                raise ValueError(f"--range must satisfy 0 <= START < END <= {TOTAL_DURATION:g}")
        if args.list_scenes:
            print(TITLE)
            for identifier, start, end in CHAPTERS:
                print(f"{identifier:20} {start:7.3f}–{end:7.3f}s")
            return 0

        project = Project(PROJECT)
        compiled = project.build("main", strict_assets=True)
        composition = compiled.composition
        if not math.isclose(compiled.duration, TOTAL_DURATION, rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"Expected a {TOTAL_DURATION:g}-second scene, got {compiled.duration:g}")
        if composition.audio:
            raise ValueError("This training scene must contain no audio")

        if args.check or not (args.full or args.range is not None or args.frame is not None or args.storyboard):
            from checks import check

            payload = json.dumps(check(compiled) | {"full_export_verified": False}, indent=2)
            if args.output is not None:
                if args.output.exists() and not args.overwrite:
                    raise FileExistsError(f"Output already exists: {args.output}; pass --overwrite")
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(payload + "\n", encoding="utf-8")
            print(payload)
            return 0

        settings = project.settings(compiled, "preview" if args.quality == "low" else "final")
        if args.fps is not None:
            settings = replace(settings, fps=args.fps)
        size = settings.dimensions(composition.canvas)
        output_dir = PROJECT / "output"
        with PillowRenderer(settings.antialias, frame_cache_mb=48, code_cache_mb=24) as renderer:
            if args.frame is not None:
                result = save_frame(
                    composition,
                    args.frame,
                    args.output or output_dir / f"networking-explained-v2-{args.frame:g}s-{args.quality}.png",
                    renderer=renderer,
                    size=size,
                    overwrite=args.overwrite,
                )
            elif args.storyboard:
                result = render_storyboard(
                    composition,
                    [StoryboardSample(t, chapter_at(t)) for t in STORYBOARD_TIMES],
                    args.output or output_dir / f"networking-explained-v2-storyboard-{args.quality}",
                    renderer=renderer,
                    size=size,
                    columns=3,
                    overwrite=args.overwrite,
                )
            else:
                start, end = args.range or (0.0, TOTAL_DURATION)
                label = "full" if args.full else f"{start:g}-{end:g}s"
                destination = args.output or output_dir / (
                    f"networking-explained-v2-{label}-{args.quality}-{settings.fps:g}fps.mp4"
                )
                print(
                    f"Silent export {start:g}–{end:g}s | {size[0]}×{size[1]} | {settings.fps:g} FPS",
                    flush=True,
                )
                began = time.monotonic()

                def progress(done: int, total: int) -> None:
                    if done == 0 or done == total or done % max(1, round(settings.fps * 2)) == 0:
                        print(f"  {done}/{total} frames | {time.monotonic() - began:.1f}s", flush=True)

                result = render(
                    composition,
                    destination,
                    settings=settings,
                    renderer=renderer,
                    start_time=start,
                    end_time=end,
                    overwrite=args.overwrite,
                    progress=progress,
                )
        print(result)
        return 0
    except (OSError, ValueError, TypeError, ImportError, RuntimeError, AssertionError, KitError) as exc:
        parser.exit(1, f"networking-explained: {exc}\n")


def chapter_at(time: float) -> str:
    """Return a storyboard label without splitting the continuous kit segment."""
    return next((identifier for identifier, start, end in CHAPTERS if start <= time < end), "")


if __name__ == "__main__":
    raise SystemExit(main())
