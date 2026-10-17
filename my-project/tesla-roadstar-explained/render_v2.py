"""Render the independent Roadster v2 film or a short source-clock excerpt."""

import argparse
import json
from pathlib import Path

from render import QUALITIES
from scene import END, OUTPUT
from scene.qa import source_integrity
from scene.story import build_master
from scene.timing import PREVIEWS
from scene.v2 import RoadsterV2Renderer

from faceless_champ import render


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--frame", type=float, metavar="SOURCE_SECONDS")
    action.add_argument("--range", nargs=2, type=float, metavar=("START", "END"))
    action.add_argument("--preview", type=int, choices=range(1, 11), metavar="CHAPTER")
    action.add_argument("--full", action="store_true")
    parser.add_argument("--quality", choices=QUALITIES, default=None)
    parser.add_argument("--fps", type=int, choices=(10, 15, 30), default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    quality = args.quality or ("4k" if args.full else "low")
    width, height, crf, preset = QUALITIES[quality]
    if args.frame is not None:
        if not 0 <= args.frame <= END:
            parser.error(f"--frame must be between 0 and {END}")
        output = args.output or OUTPUT / "v2" / "frames" / f"{args.frame:09.3f}-{quality}.png"
        start, end = args.frame, args.frame
    else:
        start, end = args.range or (PREVIEWS[args.preview - 1] if args.preview else (0, END))
        if not 0 <= start < end <= END:
            parser.error(f"Range must satisfy 0 <= START < END <= {END}")
        name = "full" if args.full else f"range-{start:.2f}-{end:.2f}"
        output = args.output or OUTPUT / "v2" / f"{name}-{quality}-{args.fps}fps.mp4"
    if output.exists() and not args.overwrite:
        parser.error(f"Output exists; use --overwrite: {output}")
    source_integrity()
    output.parent.mkdir(parents=True, exist_ok=True)
    with RoadsterV2Renderer() as renderer:
        master = build_master()
        if args.frame is not None:
            renderer.frame(master, args.frame, (width, height)).save(output)
        else:

            def progress(frame, total):
                if frame == 0 or frame == total or frame % (args.fps * 2) == 0:
                    print(f"V2: {frame}/{total} frames ({start:.2f}–{end:.2f}s)", flush=True)

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
    output.with_suffix(output.suffix + ".json").write_text(
        json.dumps(
            {
                "version": "v2",
                "source_start": start,
                "source_end": end,
                "quality": quality,
                "size": [width, height],
                "fps": args.fps if args.frame is None else None,
                "full_export_verified": False,
                "note": "Render metadata only; visual inspection is recorded separately in review.json.",
            },
            indent=2,
        )
        + "\n"
    )
    print(output)


if __name__ == "__main__":
    main()
