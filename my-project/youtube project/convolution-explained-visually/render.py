"""Render tool for "Convolution Explained Visually".

    python render.py --chapter 0 --stills            # check stills (720p PNG) at the chapter's key times
    python render.py --chapter 0 --frame 12.4 30.0   # specific source-clock seconds
    python render.py --chapter 0 --preview           # 720p MP4 with narration, veryfast encode
    python render.py --chapter 0 --preview --start 20 --end 36

Times are narration source-clock seconds. Full-quality renders are deliberately
behind --final so previews never overwrite finals by accident.
"""

from __future__ import annotations

import argparse
import importlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from faceless_champ import ExportSettings, render, save_frame  # noqa: E402

CHAPTERS = {0: "scenes.ch0_intro", 1: "scenes.ch1_sliding", 2: "scenes.ch2_dice", 3: "scenes.ch3_smooth", 4: "scenes.ch4_images", 5: "scenes.ch5_fourier", 6: "scenes.ch6_recap", 9: "scenes.full"}
OUT = ROOT / "output"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chapter", type=int, default=0, choices=sorted(CHAPTERS))
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stills", action="store_true")
    mode.add_argument("--frame", type=float, nargs="+")
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--final", action="store_true")
    ap.add_argument("--start", type=float, default=None)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--backend", default="skia", choices=["skia", "pillow", "moderngl", "auto"])
    args = ap.parse_args()

    mod = importlib.import_module(CHAPTERS[args.chapter])
    scene = mod.build(audio=not (args.stills or args.frame))
    tag = f"ch{args.chapter}"

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
    if args.final:
        settings = ExportSettings(quality="1080p", fps=args.fps, antialias=1, backend=args.backend, preset="slow", crf=16)
        out = OUT / f"{tag}_1080p.mp4"
    else:
        settings = ExportSettings(quality="720p", fps=args.fps, antialias=1, backend=args.backend, preset="veryfast", crf=20)
        suffix = "" if (args.start is None and args.end is None) else f"_{start + off:g}-{end + off:g}"
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
