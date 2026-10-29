"""Finish a cloud render locally: render any missing chunks here, then assemble chapters + final.

    python kaggle/finish_local.py          # uses kaggle/output (downloaded Kaggle Output)
"""

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
os.environ.setdefault("CONV_WORK", str(HERE / "output"))
os.environ.setdefault("CONV_INPUT", str(HERE / "no-input"))
sys.path[:0] = [str(HERE), str(PROJECT), str(PROJECT.parents[2] / "src")]
os.chdir(PROJECT)

import kaggle_render as k  # noqa: E402
from scenes import full  # noqa: E402


def main():
    boundaries = [0.0]
    for m in full.chapters():
        boundaries.append(getattr(m, "OFFSET", 0.0) + m.DURATION)
    frames, chunks = k.plan(boundaries)
    missing = [c for c in chunks if c not in k.done_set(chunks)]
    k.log(f"{len(chunks)} chunks, {len(missing)} missing: {[k.chunk_name(*c) for c in missing]}")
    if missing:
        k._worker_init(str(PROJECT))
        for c in missing:
            k.log("rendering", k.chunk_name(*c))
            print(k._render_chunk(*c, time.time() + 1e9), flush=True)
    complete = len(k.done_set(chunks)) == len(chunks)
    info = k.assemble(chunks, frames, PROJECT, complete=complete)
    k.status(chunks, frames, "complete" if complete else "incomplete", [], [])
    k.log("final", info)


if __name__ == "__main__":
    main()
