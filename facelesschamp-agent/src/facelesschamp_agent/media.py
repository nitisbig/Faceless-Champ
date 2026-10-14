"""Encoded-media checks and unchanged-master narration alignment."""

import array
import math
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from faceless_champ.audio import probe

from .errors import AgentError


def run_tool(command, *, timeout=300):
    try:
        result = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AgentError(
            "MEDIA_TOOL", str(exc), suggested_fix="Check FFmpeg/ffprobe and rerun", tool=command[0]
        ) from exc
    if result.returncode:
        raise AgentError(
            "MEDIA_DECODE",
            result.stderr.decode(errors="replace")[-3000:],
            suggested_fix="Inspect or regenerate the encoded media",
            tool=command[0],
        )
    return result.stdout


def pcm(path, start, duration, *, rate=2000):
    data = run_tool(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            str(max(0, start)),
            "-i",
            str(path),
            "-t",
            str(duration),
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(rate),
            "-f",
            "s16le",
            "-",
        ]
    )
    samples = array.array("h")
    samples.frombytes(data)
    if sys.byteorder != "little":
        samples.byteswap()
    return samples


def _correlation(reference, actual):
    n = len(reference)
    if n < 100 or len(actual) < n:
        return None
    a, b = reference[:n], actual[:n]
    ma, mb = sum(a) / n, sum(b) / n
    va = sum((v - ma) ** 2 for v in a)
    vb = sum((v - mb) ** 2 for v in b)
    if min(va, vb) / n < 25:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


def alignment(reference, output, *, source_start, duration):
    """Correlate multiple windows; silence cannot establish alignment."""
    rate, margin = 2000, 0.25
    if duration < 0.8:
        return {"status": "unverified", "reason": "Clip too short for alignment windows"}
    width = min(2.0, duration - 0.5)
    positions = sorted({0.25, max(0.25, (duration - width) / 2), max(0.25, duration - width - 0.25)})
    rows = []
    for start in positions:
        ref = pcm(reference, source_start + start, width)
        if _correlation(ref, ref) is None:
            continue
        actual = pcm(output, start - margin, width + 2 * margin)
        center = round(margin * rate)
        direct = _correlation(ref, actual[center : center + len(ref)])
        if direct is None:
            rows.append(
                {
                    "output_time": start,
                    "correlation": 0.0,
                    "offset_seconds": None,
                    "reason": "Output narration is silent or truncated where reference audio is present",
                }
            )
            continue
        best = (direct, 0)
        if direct < 0.97:
            for lag in range(-center, center + 1, 4):
                corr = _correlation(ref, actual[center + lag : center + lag + len(ref)])
                if corr is not None and corr > best[0]:
                    best = (corr, lag)
            coarse = best[1]
            for lag in range(max(-center, coarse - 3), min(center, coarse + 3) + 1):
                corr = _correlation(ref, actual[center + lag : center + lag + len(ref)])
                if corr is not None and corr > best[0]:
                    best = (corr, lag)
        rows.append({"output_time": start, "correlation": round(best[0], 5), "offset_seconds": best[1] / rate})
    if not rows:
        return {"status": "unverified", "reason": "No non-silent reference windows"}
    passed = all(row["correlation"] >= 0.8 and abs(row["offset_seconds"]) <= 0.04 for row in rows)
    return {
        "status": "passed" if passed else "failed",
        "windows": rows,
        "tolerance_seconds": 0.04,
        "method": "mono 2kHz waveform correlation",
    }


def verify_media(
    path,
    *,
    width,
    height,
    fps,
    duration,
    require_audio,
    frame_directory,
    reference=None,
    source_start=0,
    samples=None,
    alignment_reason=None,
):
    path = Path(path)
    metadata = probe(path)
    videos = [s for s in metadata["streams"] if s["codec_type"] == "video"]
    audio = [s for s in metadata["streams"] if s["codec_type"] == "audio"]
    if len(videos) != 1:
        raise AgentError("MEDIA_STREAM", "Expected one video stream")
    stream = videos[0]
    actual_fps = float(Fraction(stream.get("avg_frame_rate", "0")))
    actual_duration = float(stream.get("duration", metadata["format"]["duration"]))
    checks = {
        "dimensions": (stream["width"], stream["height"]) == (width, height),
        "fps": abs(actual_fps - fps) < 0.001,
        "duration": abs(actual_duration - duration) <= 1 / fps + 0.015,
        "audio": bool(audio) if require_audio else True,
    }
    run_tool(
        ["ffmpeg", "-v", "error", "-xerror", "-i", str(path), "-map", "0:v", "-map", "0:a?", "-f", "null", "-"],
        timeout=3600,
    )
    checks["full_decode"] = True
    frame_directory = Path(frame_directory)
    frame_directory.mkdir(parents=True, exist_ok=False)
    requested = samples or [0, duration / 2, max(0, duration - 1 / fps)]
    frames = []
    for i, time in enumerate(sorted(set(requested))):
        time = max(0, min(time, actual_duration - 1 / max(actual_fps, 1) - 0.001))
        output = frame_directory / f"{i:03d}-{time:.3f}.png"
        run_tool(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                str(time),
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-vf",
                "scale=480:-1",
                str(output),
            ]
        )
        if not output.is_file():
            raise AgentError("MEDIA_FRAME", "Could not extract representative frame", source_time=time)
        frames.append({"path": str(output.resolve()), "output_time": time, "source_time": source_start + time})
    if reference and audio:
        audio_check = alignment(reference, path, source_start=source_start, duration=duration)
    else:
        audio_check = {
            "status": "unverified" if require_audio else "not_applicable",
            "reason": alignment_reason or "No unchanged master narration reference",
        }
    return {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "metadata": metadata,
        "frames": frames,
        "narration_alignment": audio_check,
    }
