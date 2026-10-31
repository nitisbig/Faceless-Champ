"""Render tool for "Understanding 4D Visually".

    python render.py --chapter 0 --stills              # 720p PNG stills at the chapter's key times
    python render.py --chapter 0 --frame 12.4 30.0     # specific narration seconds
    python render.py --chapter 0 --preview             # 720p MP4 with narration, veryfast encode
    python render.py --chapter 0 --preview --start 20 --end 36
    python render.py --chapter 0 --final               # 1080p, crf 16, motion blur on
    python render.py --chapter full --final --quality 4k
    python render.py --chapter test --stills           # Stage A component sheet

Times are narration source-clock seconds. Full-quality renders sit behind --final so previews never
overwrite finals by accident. --final turns motion blur on (FC_MOTION_BLUR, 5 subframes) unless
--blur is given; previews and stills render without it.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

CHAPTERS = {
    "0": "scenes.ch0_intro",
    "1": "scenes.ch1_dimension",
    "2": "scenes.ch2_build",
    "3": "scenes.ch3_slices",
    "4": "scenes.ch4_shadows",
    "5": "scenes.ch5_rotation",
    "6": "scenes.ch6_matters",
    "7": "scenes.ch7_recap",
    "full": "scenes.full",
    "test": "scenes.stage_a_test",
    "s01": "scenes.s01_cinematic",
}
OUT = ROOT / "output"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chapter", default="0", choices=list(CHAPTERS))
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stills", action="store_true")
    mode.add_argument("--frame", type=float, nargs="+")
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--final", action="store_true")
    ap.add_argument("--start", type=float, default=None)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--quality", default="1080p", choices=["1080p", "4k"], help="--final resolution")
    ap.add_argument("--blur", type=int, default=None, help="motion-blur subframes (default: 5 for --final, else off)")
    ap.add_argument("--backend", default="skia", choices=["skia", "pillow", "moderngl", "auto"])
    args = ap.parse_args()

    blur = args.blur if args.blur is not None else (5 if args.final else 1)
    os.environ["FC_MOTION_BLUR"] = str(blur)

    from faceless_champ import ExportSettings, render, save_frame

    mod = importlib.import_module(CHAPTERS[args.chapter])
    scene = mod.build(audio=not (args.stills or args.frame))
    tag = f"ch{args.chapter}" if args.chapter.isdigit() else args.chapter
    off = getattr(mod, "OFFSET", 0.0)  # chapter scenes start at narration time OFFSET

    if args.stills or args.frame:
        times = mod.STILLS if args.stills else args.frame
        folder = OUT / "frames" / tag
        folder.mkdir(parents=True, exist_ok=True)
        for t in times:
            t0 = time.time()
            path = folder / f"{tag}_{t:07.3f}.png"
            save_frame(scene, t - off, path, size=(1280, 720), backend=args.backend, overwrite=True)
            print(f"{path.name}  {time.time() - t0:.2f}s", flush=True)
        return

    start = (args.start - off) if args.start is not None else 0.0
    end = (args.end - off) if args.end is not None else mod.DURATION
    ranged = args.start is not None or args.end is not None
    if args.final:
        settings = ExportSettings(quality=args.quality, fps=args.fps, antialias=1, backend=args.backend, preset="slow",
                                  crf=16)
        out = OUT / f"{tag}_{args.quality}.mp4"
        if ranged:
            out = OUT / "sections" / f"{tag}_{args.quality}_{start + off:g}-{end + off:g}.mp4"
    else:
        settings = ExportSettings(quality="720p", fps=args.fps, antialias=1, backend=args.backend, preset="veryfast",
                                  crf=20)
        suffix = f"_{start + off:g}-{end + off:g}" if ranged else ""
        out = OUT / "previews" / f"{tag}_720p{suffix}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    last = [0.0]

    def progress(done, total):
        if time.time() - last[0] > 15 or done == total:
            last[0] = time.time()
            print(f"  {done}/{total} frames  {time.time() - t0:.0f}s", flush=True)

    render(scene, out, settings=settings, overwrite=True, start_time=start, end_time=end, progress=progress)
    print(f"wrote {out}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
