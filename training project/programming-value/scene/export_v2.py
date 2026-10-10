"""Frame-aligned full export checkpoints, with one final continuous audio mux."""

import hashlib
import json
import math
import subprocess
from copy import copy
from dataclasses import asdict
from pathlib import Path

from faceless_champ import render


def fingerprint(project, settings):
    digest = hashlib.sha256(json.dumps(asdict(settings), sort_keys=True).encode())
    files = [
        project / "audio.mp3",
        project / "cue-per-word.srt",
        project / "main.py",
        *(project / "assets/fonts").glob("*.ttf"),
    ]
    files.extend(project / "scene" / name for name in ("story_v2.py", "design_v2.py", "design.py", "renderer_v2.py"))
    root = project.parents[1]
    for directory in (root / "src/faceless_champ", root / "facelesschamp-kit/src/facelesschamp_kit"):
        files.extend(directory.rglob("*.py"))
    for path in sorted(files):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def valid_chunk(path, frames, settings):
    if not path.exists():
        return False
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if p.returncode:
        return False
    try:
        streams = json.loads(p.stdout)["streams"]
        video = next(s for s in streams if s["codec_type"] == "video")
        numerator, denominator = map(int, video["r_frame_rate"].split("/"))
        return (
            int(video["nb_frames"]) == frames
            and video["width"] == settings.width
            and video["height"] == settings.height
            and abs(numerator / denominator - settings.fps) < 1e-7
            and len(streams) == 1
        )
    except (ValueError, KeyError, StopIteration):
        return False


def export_full(compiled, output, settings, renderer, progress=None, overwrite=False):
    output = Path(output).resolve()
    if output.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {output}; pass --overwrite")
    project = compiled.context.root
    identity = fingerprint(project, settings)
    directory = project / "output/v2-chunks" / identity[:16]
    directory.mkdir(parents=True, exist_ok=True)
    silent = copy(compiled.composition)
    silent.audio = []
    total = math.ceil(compiled.duration * settings.fps - 1e-9)
    step = round(settings.fps * 10)
    chunks = []
    for first in range(0, total, step):
        stop = min(first + step, total)
        target = directory / f"{first:08}-{stop:08}.mp4"
        if valid_chunk(target, stop - first, settings):
            print(f"Reuse verified chunk {first}–{stop}", flush=True)
            if progress:
                progress(stop, total)
        else:
            print(f"Render chunk {first}–{stop} / {total}", flush=True)
            render(
                silent,
                target,
                settings=settings,
                renderer=renderer,
                start_time=first / settings.fps,
                end_time=min(stop / settings.fps, compiled.duration),
                progress=(lambda done, count, offset=first: progress(offset + done, total)) if progress else None,
                overwrite=target.exists(),
            )
            if not valid_chunk(target, stop - first, settings):
                raise RuntimeError(f"Chunk verification failed: {target}")
        chunks.append(target)
        checkpoint = {
            "fingerprint": identity,
            "settings": asdict(settings),
            "frames_done": stop,
            "frames_total": total,
            "chunks": [p.name for p in chunks],
        }
        temporary = directory / "checkpoint.tmp.json"
        temporary.write_text(json.dumps(checkpoint, indent=2) + "\n")
        temporary.replace(directory / "checkpoint.json")
    listing = directory / "concat.txt"
    listing.write_text("".join(f"file '{p.name}'\n" for p in chunks))
    output.parent.mkdir(parents=True, exist_ok=True)
    assembled = output.with_name(output.stem + ".assembling.mp4")
    duration = total / settings.fps
    command = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(listing),
        "-i",
        str(project / "audio.mp3"),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-af",
        f"aresample=48000,aformat=channel_layouts=stereo,apad,atrim=end={duration},asetpts=PTS-STARTPTS",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-t",
        str(duration),
        "-movflags",
        "+faststart",
        str(assembled),
    ]
    p = subprocess.run(command, capture_output=True, text=True, check=False)
    if p.returncode:
        raise RuntimeError("Final mux failed: " + p.stderr[-2000:])
    p = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_frames",
            "-of",
            "default=nw=1:nk=1",
            str(assembled),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if p.returncode or int(p.stdout.strip()) != total:
        raise RuntimeError("Final mux frame count does not match checkpoints")
    assembled.replace(output)
    compiled.report["checkpoint_export"] = {"fingerprint": identity, "chunks": len(chunks), "frames": total}
    return output
