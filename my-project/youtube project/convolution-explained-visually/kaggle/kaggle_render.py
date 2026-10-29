"""Kaggle cloud renderer for "Convolution Explained Visually" (4K, 30 fps).

Recovery design
  * The full timeline is split into fixed 300-frame chunks on an exact frame grid.
  * Each chunk renders to "<name>.part.mp4" and is renamed only after it verifies, so a
    half-written file can never look finished.
  * status.json is rewritten after every chunk (done / missing / timing / ETA).
  * A time guard stops starting new chunks before Kaggle's 12-hour limit, so the run
    always ends normally and Kaggle saves /kaggle/working as the version Output.
  * Finished chunks found in any attached input (a resume dataset) are reused, so a
    resumed run only renders what is missing.
  * Chapters are assembled (with their narration) as soon as all their chunks exist;
    the final video is assembled when everything is done.

Outputs (/kaggle/working)
  status.json                         progress, always current
  chunks/cN_fNNNNNN-NNNNNN.mp4        finished video-only chunks (resume material)
  chapters/chN_<name>_4k.mp4          finished chapters with audio
  final/convolution_explained_4k.mp4  the full video with narration (when 100% done)
  logs/                               per-chunk error logs
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

WORK = Path(os.environ.get("CONV_WORK", "/kaggle/working"))
INPUT = Path(os.environ.get("CONV_INPUT", "/kaggle/input"))
CHECKOUT = Path(os.environ.get("CONV_CHECKOUT", "/tmp/conv-source"))
QUALITY = os.environ.get("CONV_QUALITY", "4k")
FPS = 30
CHUNK_FRAMES = int(os.environ.get("CONV_CHUNK_FRAMES", "300"))
BUDGET_S = float(os.environ.get("CONV_BUDGET_S", str(11.25 * 3600)))
WORKERS = int(os.environ.get("CONV_WORKERS", str(max(1, (os.cpu_count() or 4)))))
LIMIT_CHUNKS = int(os.environ.get("CONV_LIMIT_CHUNKS", "0"))  # >0 only for smoke tests
STARTED = time.time()
PROJECT_REL = "repo/my-project/youtube project/convolution-explained-visually"
CHAPTER_NAMES = ["intro", "sliding", "dice", "smooth", "images", "fourier", "recap"]
EXPECTED_SIZE = {"4k": (3840, 2160), "1080p": (1920, 1080), "720p": (1280, 720)}

for sub in ("chunks", "chapters", "final", "logs"):
    (WORK / sub).mkdir(parents=True, exist_ok=True)


def log(*args):
    print(time.strftime("%H:%M:%S"), *args, flush=True)


def write_json(name, value):
    path = WORK / name
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n")
    tmp.replace(path)


def run(args, **kw):
    log("RUN", " ".join(map(str, args)))
    subprocess.run(list(map(str, args)), check=True, **kw)


# ------------------------------------------------------------------ stage 1: environment (system python)
def setup_environment():
    write_json("status.json", {"stage": "setup", "started": STARTED})
    run([sys.executable, "-m", "pip", "install", "--quiet", "uv"])
    run(["uv", "venv", "/tmp/conv-env", "--python", "3.12"])
    py = "/tmp/conv-env/bin/python"
    run(["uv", "pip", "install", "--python", py, "Pillow==12.3.0", "skia-python==144.0.post2", "numpy==2.5.3",
         "scipy==1.18.1", "matplotlib==3.11.2"])
    env = {**os.environ, "CONV_STAGE": "render", "PYTHONUNBUFFERED": "1", "OMP_NUM_THREADS": "1",
           "OPENBLAS_NUM_THREADS": "1", "MPLBACKEND": "Agg", "CONV_STARTED": str(STARTED)}
    run([py, Path(__file__).resolve()], env=env)


# ------------------------------------------------------------------ stage 2: render
def extract_bundle():
    if (CHECKOUT / "job.json").exists():
        return json.loads((CHECKOUT / "job.json").read_text())
    archives = list(INPUT.rglob("convolution-input.bin"))
    if len(archives) != 1:
        raise RuntimeError(f"expected exactly one convolution-input.bin under {INPUT}, found {len(archives)}")
    with zipfile.ZipFile(archives[0]) as bundle:
        for item in bundle.infolist():
            target = (CHECKOUT / item.filename).resolve()
            if not target.is_relative_to(CHECKOUT.resolve()):
                raise ValueError(f"unsafe archive member {item.filename}")
        bundle.extractall(CHECKOUT)
    return json.loads((CHECKOUT / "job.json").read_text())


def prepare_imports():
    project = CHECKOUT / PROJECT_REL
    os.environ["FC_MANIM_PREPARED"] = str(project / "prepared" / "manim_4k")
    sys.path[:0] = [str(project), str(CHECKOUT / "repo" / "src")]
    os.chdir(project)
    return project


def plan(boundaries):
    """Chunks per chapter on the global 30 fps frame grid: (chapter, f0, f1)."""
    # the last boundary is floored so the final frame never starts past the end of the timeline
    frames = [round(t * FPS) for t in boundaries[:-1]] + [int(boundaries[-1] * FPS + 1e-9)]
    chunks = []
    for ch in range(len(frames) - 1):
        f = frames[ch]
        while f < frames[ch + 1]:
            g = min(f + CHUNK_FRAMES, frames[ch + 1])
            chunks.append((ch, f, g))
            f = g
    return frames, chunks


def chunk_name(ch, f0, f1):
    return f"c{ch}_f{f0:06d}-{f1:06d}.mp4"


def probe_frames(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                          "stream=nb_read_packets,width,height", "-of", "json", str(path)],
                         capture_output=True, text=True)
    if out.returncode:
        return None
    try:
        st = json.loads(out.stdout)["streams"][0]
        return int(st["nb_read_packets"]), int(st["width"]), int(st["height"])
    except (KeyError, IndexError, ValueError):
        return None


def chunk_ok(path, f0, f1):
    info = probe_frames(path)
    return bool(info) and info[0] == f1 - f0 and (info[1], info[2]) == EXPECTED_SIZE[QUALITY]


def adopt_previous_chunks(chunks):
    """Copy verified chunks from attached inputs (resume datasets / previous outputs)."""
    wanted = {chunk_name(*c): c for c in chunks}
    adopted = 0
    if INPUT.exists():
        for path in INPUT.rglob("c*_f*-*.mp4"):
            if path.name in wanted and not (WORK / "chunks" / path.name).exists():
                ch, f0, f1 = wanted[path.name]
                if chunk_ok(path, f0, f1):
                    shutil.copy2(path, WORK / "chunks" / path.name)
                    adopted += 1
    log(f"adopted {adopted} finished chunks from attached inputs")


_SCENE = None


def _worker_init(project):
    global _SCENE
    project = Path(project)
    sys.path[:0] = [str(project), str(project.parents[2] / "src")]
    os.chdir(project)
    from scenes import full

    _SCENE = full.build(audio=False)


def _render_chunk(ch, f0, f1, deadline):
    if time.time() > deadline:
        return ch, f0, f1, "skipped (time budget)", 0.0
    from faceless_champ import ExportSettings, render

    final = WORK / "chunks" / chunk_name(ch, f0, f1)
    part = final.with_name(final.stem + ".part.mp4")
    t0 = time.time()
    settings = ExportSettings(quality=QUALITY, fps=FPS, antialias=1, backend="skia", preset="medium", crf=16)
    render(_SCENE, part, settings=settings, overwrite=True, start_time=f0 / FPS, end_time=min(f1 / FPS, _SCENE.duration))
    if not chunk_ok(part, f0, f1):
        info = probe_frames(part)
        part.unlink(missing_ok=True)
        raise RuntimeError(f"chunk {final.name} failed verification: {info}")
    part.replace(final)
    return ch, f0, f1, "done", time.time() - t0


def done_set(chunks):
    return {c for c in chunks if (WORK / "chunks" / chunk_name(*c)).exists()}


def status(chunks, frames, stage, timings, errors):
    done = done_set(chunks)
    per = (sum(timings) / len(timings)) if timings else None
    remaining = len(chunks) - len(done)
    write_json("status.json", {
        "stage": stage, "quality": QUALITY, "fps": FPS, "workers": WORKERS,
        "chunks_total": len(chunks), "chunks_done": len(done), "percent": round(100 * len(done) / len(chunks), 1),
        "elapsed_min": round((time.time() - STARTED) / 60, 1),
        "avg_chunk_min_per_worker": round(per / 60, 2) if per else None,
        "eta_min": round(per * remaining / WORKERS / 60, 1) if per else None,
        "chapters_done": [CHAPTER_NAMES[ch] for ch in range(len(frames) - 1)
                          if any(c[0] == ch for c in chunks) and all(c in done for c in chunks if c[0] == ch)],
        "missing": [chunk_name(*c) for c in chunks if c not in done][:400],
        "errors": errors[-20:],
    })


def concat(paths, out, audio=None, a_start=0.0, a_dur=None):
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in paths))
    tmp = out.with_name(out.stem + ".part.mp4")
    args = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst]
    if audio:
        args += ["-ss", f"{a_start:.6f}"]
        if a_dur:
            args += ["-t", f"{a_dur:.6f}"]
        args += ["-i", audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                 "-ar", "48000"]
    else:
        args += ["-c", "copy"]
    args += ["-movflags", "+faststart", tmp]
    run(args)
    tmp.replace(out)
    lst.unlink(missing_ok=True)


def assemble(chunks, frames, project, complete):
    audio = project / "audio.mp3"
    done = done_set(chunks)
    for ch in range(len(frames) - 1):
        mine = [c for c in chunks if c[0] == ch]
        out = WORK / "chapters" / f"ch{ch}_{CHAPTER_NAMES[ch]}_{QUALITY}.mp4"
        if out.exists() or not mine or not all(c in done for c in mine) or mine[-1][2] != frames[ch + 1]:
            continue
        concat([WORK / "chunks" / chunk_name(*c) for c in mine], out, audio, frames[ch] / FPS,
               (frames[ch + 1] - frames[ch]) / FPS)
        log("chapter ready", out.name)
    if complete:
        out = WORK / "final" / f"convolution_explained_{QUALITY}.mp4"
        concat([WORK / "chunks" / chunk_name(*c) for c in chunks], out, audio, 0.0, None)
        info = probe_frames(out)
        log("FINAL", out.name, info)
        return info
    return None


def render_stage():
    job = extract_bundle()
    project = prepare_imports()
    from scenes import full

    boundaries = [0.0]
    for m in full.chapters():
        boundaries.append(getattr(m, "OFFSET", 0.0) + m.DURATION)
    frames, chunks = plan(boundaries)
    if LIMIT_CHUNKS:
        chunks = chunks[:LIMIT_CHUNKS]
    log(f"{len(chunks)} chunks, {frames[-1]} frames total, {WORKERS} workers, quality={QUALITY}, job={job.get('job_id')}")
    adopt_previous_chunks(chunks)
    timings, errors = [], []
    status(chunks, frames, "rendering", timings, errors)
    todo = [c for c in chunks if c not in done_set(chunks)]
    deadline = float(os.environ.get("CONV_STARTED", STARTED)) + BUDGET_S
    if todo:
        with ProcessPoolExecutor(max_workers=WORKERS, initializer=_worker_init, initargs=(str(project),)) as pool:
            futures = {pool.submit(_render_chunk, *c, deadline): c for c in todo}  # chapter order
            for fut in as_completed(futures):
                c = futures[fut]
                try:
                    _, _, _, state, secs = fut.result()
                    if state == "done":
                        timings.append(secs)
                        log(f"chunk {chunk_name(*c)} done in {secs / 60:.1f} min")
                    else:
                        log(f"chunk {chunk_name(*c)} {state}")
                except Exception as exc:  # keep going; the chunk stays missing and can be resumed
                    errors.append(f"{chunk_name(*c)}: {exc!r}")
                    log("ERROR", chunk_name(*c), repr(exc))
                    (WORK / "logs" / (chunk_name(*c) + ".log")).write_text(traceback.format_exc())
                status(chunks, frames, "rendering", timings, errors)
                try:
                    assemble(chunks, frames, project, complete=False)
                except Exception as exc:
                    errors.append(f"assemble: {exc!r}")
    complete = len(done_set(chunks)) == len(chunks)
    info = assemble(chunks, frames, project, complete=complete and not LIMIT_CHUNKS)
    status(chunks, frames, "complete" if complete and not LIMIT_CHUNKS else "stopped: resume to finish", timings, errors)
    log("finished", "COMPLETE" if complete else "PARTIAL", info)


if __name__ == "__main__":
    if os.environ.get("CONV_STAGE") == "render":
        render_stage()
    else:
        setup_environment()
