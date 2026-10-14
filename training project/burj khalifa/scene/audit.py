"""Whole-timeline CPU diagnostics and bounded media QA, never a full film render."""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from faceless_champ import ArchChamp

from .model import MODEL_FACTS
from .story import CHAPTERS, DURATION, MOTION_END, TRACK


def audit(compiled):
    findings, samples, annotations = [], 0, 0
    for entry in compiled.composition.entries:
        clip = entry.component
        if not isinstance(clip, ArchChamp):
            continue
        end = min(entry.end if entry.end is not None else DURATION, DURATION)
        times = set(np.arange(entry.start, end, 0.1))
        times.add(max(entry.start, end - 1e-6))
        for action in clip.script.actions:
            for age in (
                action.at,
                action.at + action.duration * 0.25,
                action.at + action.duration * 0.5,
                action.at + action.duration * 0.75,
                action.at + action.duration,
            ):
                if entry.start <= entry.start + age - clip.source_start < end:
                    times.add(entry.start + age - clip.source_start)
            if entry.start + action.at + action.duration - clip.source_start > MOTION_END + 1e-6:
                findings.append({"code": "MOTION_AFTER_NARRATION", "time": entry.start + action.at + action.duration})
        for t in sorted(times):
            local = clip.source_start + t - entry.start
            # state_at also validates every sampled camera frame without opening GL.
            clip.state_at(local)
            findings.extend({**item, "source_time": float(t)} for item in clip.diagnostics_at(local))
            annotations += len(clip.labels) + len(clip.dimensions)
            samples += 1
    for t in np.arange(0, DURATION, 0.1):
        rows = compiled.layout_at(float(t))["placements"]
        for row in rows:
            box = row["bounds"]
            if (
                box["left"] < 96 - 1e-6
                or box["right"] > 1824 + 1e-6
                or box["top"] < 96 - 1e-6
                or box["bottom"] > 984 + 1e-6
            ):
                findings.append({"code": "SAFE_MARGIN", "placement": row["id"], "time": float(t)})
    return {
        "samples": samples,
        "annotation_observations": annotations,
        "findings": findings,
        "cue_count": len(TRACK.cues),
        "last_cue_end": MOTION_END,
        "duration": DURATION,
        "chapters": [{"id": id, "start": start, "end": end} for id, start, end in CHAPTERS],
        "model": MODEL_FACTS,
        "audio_tracks": len(compiled.composition.audio),
        "audio_start": compiled.composition.audio[0].start,
        "full_export_verified": False,
    }


def command(args):
    return subprocess.check_output(args, stderr=subprocess.PIPE)


def audio(path):
    return np.frombuffer(
        command(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "pipe:1"]),
        dtype="<f4",
    )


def verify_media(project, ranges):
    project = Path(project)
    source = audio(project / "audio.mp3")
    results = []
    for start, end in ranges:
        path = project / "output" / f"{start:g}-{end:g}s-preview.mp4"
        info = json.loads(
            command(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-of", "json", str(path)])
        )
        stream = next(s for s in info["streams"] if s["codec_type"] == "video")
        assert (stream["width"], stream["height"]) == (960, 540)
        assert stream["avg_frame_rate"] == "15/1"
        assert int(stream["nb_read_frames"]) == round((end - start) * 15)
        command(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
        decoded = audio(path)
        expected = source[round(start * 48000) : round(end * 48000)]
        count = min(len(decoded), len(expected))
        assert count >= len(expected) - 1
        correlation = float(np.corrcoef(expected[:count], decoded[:count])[0, 1])
        assert correlation > 0.99, (path, correlation)
        # Compare a central window at every integer-sample lag within ±10 ms.
        n = min(48000, count - 960)
        ref = expected[480 : 480 + n].astype(float)
        candidates = []
        for lag in range(-480, 481):
            test = decoded[480 + lag : 480 + lag + n].astype(float)
            # Least squared error avoids a sample-size-dependent correlation bias.
            candidates.append(float(np.mean((ref - test) ** 2)))
        lag = int(np.argmin(candidates)) - 480
        assert abs(lag) <= 1, (path, lag)
        frame = path.with_suffix(".png")
        command(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ss", "1.4", "-frames:v", "1", str(frame)])
        results.append(
            {
                "path": str(path.relative_to(project)),
                "source_range": [start, end],
                "dimensions": [960, 540],
                "fps": 15,
                "frames": int(stream["nb_read_frames"]),
                "complete_decode": True,
                "audio_correlation": correlation,
                "best_lag_samples": lag,
                "frame": str(frame.relative_to(project)),
            }
        )
    return {"excerpts": results, "full_export_verified": False}


def source_hashes(project):
    project = Path(project)
    names = ("audio.mp3", "cue-per-word.srt", "normal-subtitle.srt", "voicover.md", "design-guidelines.md")
    return {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in names}
