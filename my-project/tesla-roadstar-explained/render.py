"""V1 Roadster renderer with crisp typography and vector plots. Run --help for export controls."""

import argparse
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/faceless-roadster-matplotlib")

QUALITIES = {
    "low": (960, 540, 23, "fast"),
    "high": (1920, 1080, 17, "medium"),
    "4k": (3840, 2160, 17, "medium"),
}


def format_duration(seconds):
    hours, remainder = divmod(max(0, round(seconds)), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true")
    action.add_argument("--frame", type=float, metavar="SOURCE_SECONDS")
    action.add_argument("--storyboard", action="store_true")
    action.add_argument("--preview", action="store_true")
    action.add_argument("--range", type=float, nargs=2, metavar=("START", "END"))
    action.add_argument("--full", action="store_true")
    action.add_argument("--test-seconds", type=float, metavar="SECONDS", help="test 1–30 seconds on Colab at 4K/30 FPS")
    action.add_argument("--verify", action="store_true")
    action.add_argument("--audit-layout", action="store_true")
    parser.add_argument("--chapter", type=int, choices=range(1, 11))
    quality = parser.add_mutually_exclusive_group()
    quality.add_argument(
        "--quality",
        choices=("low", "high", "4k", "1080p"),
        default=None,
        help="low: 540p, high: 1080p, 4k: 2160p; 1080p is an alias for high",
    )
    quality.add_argument("--quality4k", dest="quality", action="store_const", const="4k")
    parser.add_argument("--fps", type=int, choices=(10, 15, 30), default=30)
    parser.add_argument("--colab", action="store_true", help="export on a saved Colab T4 at 4K/30 FPS")
    parser.add_argument("--resume", action="store_true", help="recover the saved Colab job")
    parser.add_argument("--restart-runtime", action="store_true", help="replace a confirmed lost Colab VM")
    parser.add_argument("--refresh-inputs", action="store_true", help="repair updated renderer inputs when resuming")
    parser.add_argument(
        "--detach", action="store_true", help="leave the local checkpoint controller running in background"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.resume and not args.colab:
        parser.error("--resume requires --colab")
    if (args.restart_runtime or args.refresh_inputs) and not (args.colab and args.resume):
        parser.error("--restart-runtime and --refresh-inputs require --colab --resume")
    if args.detach and not args.colab:
        parser.error("--detach requires --colab")
    if args.test_seconds is not None and (
        not args.colab or not math.isfinite(args.test_seconds) or not 1 <= args.test_seconds <= 30
    ):
        parser.error("--test-seconds requires --colab and a duration between 1 and 30 seconds")
    if args.colab and not args.check:
        if any(
            (
                args.frame is not None,
                args.storyboard,
                args.preview,
                args.range,
                args.verify,
                args.audit_layout,
                args.chapter,
            )
        ):
            parser.error("--colab exports the full render.py film; use local commands for excerpts and stills")
        if args.fps != 30 or args.quality not in (None, "4k"):
            parser.error("Colab requires the fixed 4K/30 FPS profile")
        args.full = args.test_seconds is None
    if not any(
        (
            args.check,
            args.frame is not None,
            args.storyboard,
            args.preview,
            args.range,
            args.full,
            args.verify,
            args.audit_layout,
            args.test_seconds is not None,
        )
    ):
        parser.error("choose an action such as --full, --preview, --check or --colab")
    args.quality = "high" if args.quality == "1080p" else (args.quality or "4k")
    return args


def main(argv=None, managed=False):
    args = parse_args(argv)
    if args.colab and not args.check:
        from colab_render import start

        options = {"resume": args.resume, "output": args.output, "overwrite": args.overwrite}
        if args.test_seconds is not None:
            options["test_seconds"] = args.test_seconds
        if args.refresh_inputs:
            options["refresh_inputs"] = True
        if args.restart_runtime:
            options["restart_runtime"] = True
        if managed:
            from colab_service import run

            return run(options, detach=args.detach)
        return start(**options)

    from scene import END, OUTPUT
    from scene.qa import audit_layout, check_project, source_integrity, storyboard, verify_media, write_json
    from scene.story import RoadsterRenderer, build_master
    from scene.timing import PREVIEWS

    from faceless_champ import render

    source_integrity()
    if args.preview and args.output and args.chapter is None:
        raise ValueError("--output requires --chapter when rendering a preview")
    if args.audit_layout:
        result = audit_layout()
        print(
            json.dumps({"samples": result["samples"], "passed": result["passed"], "findings": len(result["findings"])})
        )
        return
    if args.verify:
        result = verify_media()
        print(json.dumps(result, indent=2))
        return
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with RoadsterRenderer() as renderer:
        master = build_master()
        if args.check:
            print(json.dumps(check_project(renderer), indent=2))
            return
        if args.storyboard:
            print(json.dumps(storyboard(renderer, master), indent=2))
            return
        if args.frame is not None:
            if not 0 <= args.frame <= END:
                raise ValueError("Frame time must lie inside the source timeline")
            quality = args.quality
            size = QUALITIES[quality][:2]
            output = args.output or OUTPUT / "frames" / f"{args.frame:09.3f}.png"
            if output.exists() and not args.overwrite:
                raise FileExistsError(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            renderer.frame(master, args.frame, size).save(output)
            print(output)
            return
        quality = args.quality
        width, height, crf, preset = QUALITIES[quality]
        if args.preview:
            jobs = [(chapter, *PREVIEWS[chapter - 1]) for chapter in ([args.chapter] if args.chapter else range(1, 11))]
        elif args.range:
            jobs = [(args.chapter or 0, *args.range)]
        else:
            jobs = [(0, 0, END)]
        metadata = OUTPUT / "previews.json"
        existing = json.loads(metadata.read_text()) if metadata.exists() else []
        for chapter, start, end in jobs:
            output = args.output or (
                OUTPUT / f"full-{quality}-{args.fps}fps.mp4"
                if args.full
                else OUTPUT
                / "previews"
                / (
                    f"chapter-{chapter:02d}-{quality}-{args.fps}fps.mp4"
                    if args.preview
                    else f"range-{start:.2f}-{end:.2f}-{quality}-{args.fps}fps.mp4"
                )
            )

            export_started = time.monotonic()

            def progress(frame, total, chapter=chapter, start=start, end=end, export_started=export_started):
                if frame == 0 or frame == total or frame % (args.fps * 2) == 0:
                    elapsed = time.monotonic() - export_started
                    remaining = format_duration(elapsed * (total - frame) / frame) if frame else "estimating…"
                    percent = 100 * frame / total if total else 0
                    print(
                        f"Chapter {chapter:02d}: {frame}/{total} frames ({percent:.1f}%) "
                        f"({start:.3f}–{end:.3f}s) | elapsed {format_duration(elapsed)} | ETA {remaining}",
                        flush=True,
                    )

            render(
                master,
                output,
                renderer=renderer,
                start_time=start,
                end_time=end,
                width=width,
                height=height,
                fps=args.fps,
                antialias=1,
                crf=crf,
                preset=preset,
                overwrite=args.overwrite,
                progress=progress,
            )
            if args.preview:
                item = {
                    "chapter": chapter,
                    "file": str(output.resolve().relative_to(OUTPUT.resolve())),
                    "start": start,
                    "end": end,
                    "width": width,
                    "height": height,
                    "fps": args.fps,
                    "quality": quality,
                }
                existing = [x for x in existing if x["chapter"] != chapter] + [item]
                write_json(metadata, sorted(existing, key=lambda x: x["chapter"]))
            print(output, flush=True)


def command_line(argv=None):
    try:
        result = main(argv, managed=True)
        return result if type(result) is int else 0
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"Render failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(command_line())
