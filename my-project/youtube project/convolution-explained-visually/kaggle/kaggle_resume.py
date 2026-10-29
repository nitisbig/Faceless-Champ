"""Resume an interrupted Kaggle render (or just download what is finished).

    python kaggle/kaggle_resume.py status      # show the latest run's status
    python kaggle/kaggle_resume.py download    # download Output (chapters / final / chunks) to kaggle/output
    python kaggle/kaggle_resume.py resume      # download, publish finished chunks as a dataset, re-run the kernel

A resumed run adopts every verified chunk from the progress dataset and renders only
what is missing. Requires the Kaggle CLI (already configured for this machine).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
USER = "nitesh1230"
KERNEL = f"{USER}/convolution-explained-4k-render"
PROGRESS = f"{USER}/convolution-explained-4k-progress"
OUT = HERE / "output"


def kaggle(*args, check=True):
    print("$ kaggle", " ".join(args), flush=True)
    return subprocess.run(["kaggle", *args], check=check, text=True)


def status():
    kaggle("kernels", "status", KERNEL, check=False)


def download():
    OUT.mkdir(exist_ok=True)
    kaggle("kernels", "output", KERNEL, "-p", str(OUT), "-o")
    st = OUT / "status.json"
    if st.exists():
        print(json.dumps({k: v for k, v in json.loads(st.read_text()).items() if k != "missing"}, indent=2))
    for folder in ("final", "chapters"):
        for f in sorted((OUT / folder).glob("*.mp4")):
            print("ready:", f)


def resume():
    download()
    chunks = sorted((OUT / "chunks").glob("c*_f*-*.mp4"))
    chunks = [c for c in chunks if not c.name.endswith(".part.mp4")]
    if not chunks:
        sys.exit("no finished chunks found in the output; just push the kernel again")
    stage = HERE / "progress_dataset"
    shutil.rmtree(stage, ignore_errors=True)
    (stage / "chunks").mkdir(parents=True)
    for c in chunks:
        shutil.copy2(c, stage / "chunks" / c.name)
    (stage / "dataset-metadata.json").write_text(json.dumps({
        "title": "Convolution Explained 4K Progress", "id": PROGRESS, "licenses": [{"name": "other"}],
        "isPrivate": True}, indent=2))
    exists = subprocess.run(["kaggle", "datasets", "status", PROGRESS], capture_output=True, text=True).returncode == 0
    if exists:
        kaggle("datasets", "version", "-p", str(stage), "-m", f"{len(chunks)} finished chunks", "-r", "zip")
    else:
        kaggle("datasets", "create", "-p", str(stage), "-r", "zip")
    meta_path = HERE / "kernel" / "kernel-metadata.json"
    meta = json.loads(meta_path.read_text())
    if PROGRESS not in meta["dataset_sources"]:
        meta["dataset_sources"].append(PROGRESS)
        meta_path.write_text(json.dumps(meta, indent=2))
    print(f"published {len(chunks)} chunks; waiting for the dataset, then pushing the kernel")
    kaggle("datasets", "status", PROGRESS, check=False)
    kaggle("kernels", "push", "-p", str(HERE / "kernel"))


if __name__ == "__main__":
    {"status": status, "download": download, "resume": resume}[sys.argv[1] if len(sys.argv) > 1 else "status"]()
