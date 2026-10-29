"""Package the project for the Kaggle render and write the kernel/dataset metadata.

    python kaggle/build_bundle.py --manim-dir <prepared 4K manim folder>

Creates
    kaggle/dataset/convolution-input.bin   (zip; .bin so Kaggle does not auto-extract it)
    kaggle/dataset/dataset-metadata.json
    kaggle/kernel/kaggle_render.py + kernel-metadata.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
LIB = PROJECT.parents[2]
REL = "repo/my-project/youtube project/convolution-explained-visually"
USER = "nitesh1230"
DATASET = "convolution-explained-4k-input"
KERNEL = "convolution-explained-4k-render"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def files():
    skip = ("__pycache__", ".pyc")
    for p in sorted((LIB / "src" / "faceless_champ").rglob("*")):
        if p.is_file() and not any(s in str(p) for s in skip):
            yield p, "repo/" + str(p.relative_to(LIB))
    for p in sorted((LIB / "assets" / "fonts").glob("*")):
        yield p, "repo/" + str(p.relative_to(LIB))
    for name in ("theme.py", "cues.py", "fx.py", "mathtype.py", "space.py", "render.py", "audio.mp3",
                 "cue-per-word.srt", "normal-subtitle.srt"):
        yield PROJECT / name, f"{REL}/{name}"
    for sub in ("scenes", "sources"):
        for p in sorted((PROJECT / sub).glob("*.py")):
            yield p, f"{REL}/{sub}/{p.name}"
    yield PROJECT / "manim" / "long_mult.py", f"{REL}/manim/long_mult.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manim-dir", required=True, help="prepared 4K Manim asset folder (contains manifest.json)")
    args = ap.parse_args()
    manim = Path(args.manim_dir)
    assert (manim / "manifest.json").exists(), "not a prepared Manim folder"

    out = PROJECT / "kaggle"
    ds, kn = out / "dataset", out / "kernel"
    for d in (ds, kn):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    sources = {}
    job_id = time.strftime("%Y%m%d-%H%M%S")
    with zipfile.ZipFile(ds / "convolution-input.bin", "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path, arc in files():
            z.write(path, arc)
            sources[arc] = sha(path)
        for p in sorted(manim.rglob("*")):
            if p.is_file():
                arc = f"{REL}/prepared/manim_4k/{p.relative_to(manim)}"
                z.write(p, arc, compress_type=zipfile.ZIP_STORED)
        z.writestr("job.json", json.dumps({"job_id": job_id, "sources": sources}, indent=1))
    (ds / "dataset-metadata.json").write_text(json.dumps({
        "title": "Convolution Explained 4K Input", "id": f"{USER}/{DATASET}",
        "licenses": [{"name": "other"}], "isPrivate": True}, indent=2))
    shutil.copy2(out / "kaggle_render.py", kn / "kaggle_render.py")
    (kn / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{USER}/{KERNEL}", "title": KERNEL, "code_file": "kaggle_render.py", "language": "python",
        "kernel_type": "script", "is_private": True, "enable_gpu": False, "enable_tpu": False,
        "enable_internet": True, "dataset_sources": [f"{USER}/{DATASET}"], "kernel_sources": [],
        "competition_sources": [], "model_sources": []}, indent=2))
    size = (ds / "convolution-input.bin").stat().st_size / 1e6
    print(f"bundle {size:.1f} MB, {len(sources)} source files, job {job_id}")


if __name__ == "__main__":
    main()
