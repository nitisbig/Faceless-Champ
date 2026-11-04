"""Render tool for "The Math Trick That Turns Any Function Into a Polynomial".

    python render.py --scene S12 --stills              # one scene's still times (720p PNG)
    python render.py --scene S12 --preview             # one scene's range as a 720p MP4 with narration
    python render.py --chapter 2 --stills              # every still of a chapter
    python render.py --chapter 2 --frame 150.2 160.0   # specific narration seconds
    python render.py --chapter 2 --preview --start 150 --end 170
    python render.py --chapter 7 --pv-cache 1080       # pre-render PyVista frames for a 1080p final (one process)
    python render.py --chapter full --final            # 1080p, crf 16, motion blur on
    python render.py --chapter full --final --quality 4k
    python render.py --chapter test --stills           # Stage A component sheet

Times are narration source-clock seconds. Full-quality renders sit behind --final so previews never
overwrite finals by accident. --final turns motion blur on (FC_MOTION_BLUR, 5 subframes) unless --blur is
given; previews and stills render without it. Every video render normalizes the narration to -14 LUFS
(YouTube), and finals print a delivery report. Finals keep their chunks in output/chunks/, keyed by the
project's source files, so an interrupted final resumes and any code edit starts fresh chunks.

--scene SNN finds the chapter whose ``SCENES`` lists SNN and limits the range (and stills) to that scene.
--pv-cache HEIGHT walks every frame of the range at that output height through ``mod.pv_warm(t, size)``
(or the whole frame if the chapter has none), so PyVista renders land in output/cache/pyvista before a
parallel render reads them.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

CHAPTERS = {
    "0": "scenes.ch0_open",
    "1": "scenes.ch1_polynomials",
    "2": "scenes.ch2_copy",
    "3": "scenes.ch3_factorials",
    "4": "scenes.ch4_recipe",
    "5": "scenes.ch5_e",
    "6": "scenes.ch6_sine",
    "7": "scenes.ch7_breaks",
    "8": "scenes.ch8_matters",
    "9": "scenes.ch9_recap",
    "full": "scenes.full",
    "test": "scenes.stage_a_test",
}
OUT = ROOT / "output"
SIZES = {720: (1280, 720), 1080: (1920, 1080), 2160: (3840, 2160)}


def source_fingerprint() -> str:
    """Changes whenever any project .py file changes, so resumed finals never reuse stale chunks."""
    h = hashlib.sha1()
    for path in sorted(ROOT.rglob("*.py")):
        if "output" not in path.parts:
            h.update(f"{path.relative_to(ROOT)}:{path.stat().st_mtime_ns}:{path.stat().st_size}".encode())
    return h.hexdigest()[:10]


def find_scene(sid: str):
    """(chapter key, (t0, t1, stills)) for a scene id like S12."""
    sid = sid.upper()
    for key, name in CHAPTERS.items():
        if not key.isdigit() or not (ROOT / (name.replace(".", "/") + ".py")).exists():
            continue
        mod = importlib.import_module(name)
        if sid in getattr(mod, "SCENES", {}):
            return key, mod.SCENES[sid]
    raise SystemExit(f"{sid} is not in any built chapter's SCENES")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chapter", default=None, choices=list(CHAPTERS))
    ap.add_argument("--scene", default=None, help="scene id (S01–S51): its chapter, range and stills")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stills", action="store_true")
    mode.add_argument("--frame", type=float, nargs="+")
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--final", action="store_true")
    mode.add_argument("--pv-cache", type=int, choices=sorted(SIZES), help="warm the PyVista cache at this height")
    ap.add_argument("--start", type=float, default=None)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--quality", default="1080p", choices=["1080p", "4k"], help="--final resolution")
    ap.add_argument("--blur", type=int, default=None, help="motion-blur subframes (default: 5 for --final, else off)")
    ap.add_argument("--backend", default="skia", choices=["skia", "pillow", "moderngl", "auto"])
    ap.add_argument("--codec", default="h264", choices=["h264", "hevc10", "prores"], help="--final codec")
    ap.add_argument("--lut", type=Path, default=None, help="--final .cube colour grade")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 1, help="parallel render processes")
    args = ap.parse_args()

    scene_range = None
    if args.scene:
        args.chapter, scene_range = find_scene(args.scene)
    if args.chapter is None:
        ap.error("give --chapter or --scene")

    blur = args.blur if args.blur is not None else (5 if args.final else 1)
    os.environ["FC_MOTION_BLUR"] = str(blur)

    from faceless_champ import ExportSettings, delivery_report, render, save_frame

    mod = importlib.import_module(CHAPTERS[args.chapter])
    tag = args.scene.upper() if args.scene else (f"ch{args.chapter}" if args.chapter.isdigit() else args.chapter)
    off = getattr(mod, "OFFSET", 0.0)  # chapter scenes start at narration time OFFSET
    if scene_range is not None:
        args.start = scene_range[0] if args.start is None else args.start
        args.end = scene_range[1] if args.end is None else args.end

    if args.stills or args.frame:
        scene = mod.build(audio=False)
        times = (scene_range[2] if scene_range else mod.STILLS) if args.stills else args.frame
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

    if args.pv_cache:
        size = SIZES[args.pv_cache]
        warm = getattr(mod, "pv_warm", None) or mod.draw
        n = round((end - start) * args.fps)
        t0 = time.time()
        for i in range(n):
            warm(start + i / args.fps, size)
            if i % 60 == 0:
                print(f"  {i}/{n} frames  {time.time() - t0:.0f}s", flush=True)
        print(f"PyVista cache warm for {n} frames at {size[0]}x{size[1]}  ({time.time() - t0:.0f}s)")
        return

    scene = mod.build(audio=True)
    if args.final:
        settings = ExportSettings(
            quality=args.quality,
            fps=args.fps,
            antialias=1,
            backend=args.backend,
            preset="slow",
            crf=16,
            codec=args.codec,
            lut=args.lut,
            loudness=-14,
            workers=args.workers,
        )
        out = OUT / f"{tag}_{args.quality}{settings.suffix}"
        if ranged:
            out = OUT / "sections" / f"{tag}_{args.quality}_{start + off:g}-{end + off:g}{settings.suffix}"
    else:
        settings = ExportSettings(
            quality="720p",
            fps=args.fps,
            antialias=1,
            backend=args.backend,
            preset="veryfast",
            crf=20,
            loudness=-14,
            workers=args.workers,
        )
        suffix = f"_{start + off:g}-{end + off:g}" if ranged and not args.scene else ""
        out = OUT / "previews" / f"{tag}_720p{suffix}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    last = [0.0]

    def progress(done, total):
        if time.time() - last[0] > 15 or done == total:
            last[0] = time.time()
            print(f"  {done}/{total} frames  {time.time() - t0:.0f}s", flush=True)

    chunks = OUT / "chunks" / f"{out.stem}-{source_fingerprint()}" if args.final else None
    render(
        scene,
        out,
        settings=settings,
        overwrite=True,
        start_time=start,
        end_time=end,
        progress=progress,
        chunk_dir=chunks,
    )
    if chunks is not None:
        shutil.rmtree(chunks)  # the final is published; its chunks are only resume material
    print(f"wrote {out}  ({time.time() - t0:.0f}s)")
    if args.final:
        print(delivery_report(out))


if __name__ == "__main__":
    main()
