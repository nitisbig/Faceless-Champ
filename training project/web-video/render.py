"""Prepare HTML, inspect frames, or export the tour. No work runs on import."""

import argparse
from pathlib import Path

from main import ROOT, STORYBOARD_TIMES, browser_script, build_video

from faceless_champ import StoryboardSample, render, render_storyboard, save_frame
from faceless_champ.web import capture_html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["prepare", "frame", "storyboard", "preview", "render"], default="render")
    parser.add_argument("--fps", type=float, default=30)
    parser.add_argument("--resolution", choices=["540p", "720p", "1080p", "4k"], default="1080p")
    parser.add_argument("--time", type=float, default=7)
    parser.add_argument("--start", type=float, default=4)
    parser.add_argument("--end", type=float, default=9)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    size = {"540p": (960, 540), "720p": (1280, 720), "1080p": (1920, 1080), "4k": (3840, 2160)}[args.resolution]
    suffix = "" if args.mode == "storyboard" else (".png" if args.mode == "frame" else ".mp4")
    output = args.output or ROOT / "output" / (args.mode + suffix)
    if args.mode != "prepare" and output.exists() and not args.overwrite:
        parser.error(f"{output} exists; pass --overwrite")
    page, script = browser_script()
    options = {}
    if args.mode == "frame":
        options["sample_times"] = [args.time]
    elif args.mode == "storyboard":
        options["sample_times"] = STORYBOARD_TIMES
    elif args.mode == "preview":
        options.update({"start_time": args.start, "end_time": args.end})
    capture = capture_html(page, script, fps=args.fps, cache_dir=ROOT / ".web-cache", **options)
    print(f"Prepared: {capture.directory}", flush=True)
    if args.mode == "prepare":
        return
    video = build_video(capture)
    if args.mode == "frame":
        save_frame(video, args.time, output, size=size, overwrite=args.overwrite)
    elif args.mode == "storyboard":
        render_storyboard(
            video, [StoryboardSample(t) for t in STORYBOARD_TIMES], output, size=(480, 270), overwrite=args.overwrite
        )
    else:
        ranges = {"start_time": args.start, "end_time": args.end} if args.mode == "preview" else {}
        render(
            video, output, width=size[0], height=size[1], fps=args.fps, antialias=1, overwrite=args.overwrite, **ranges
        )
    print(output.resolve())


if __name__ == "__main__":
    main()
