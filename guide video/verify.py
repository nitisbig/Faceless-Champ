#!/usr/bin/env python3
"""Reproduce low-only excerpt QA. Never exports the complete guide."""

import argparse
import contextlib
import io
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parent
interpreter = ROOT / ".venv/bin/python"
if interpreter.exists() and Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
    os.execv(str(interpreter), [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]])
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "facelesschamp-kit/src")]
from scene.audit import check
from scene.story import build_video

from faceless_champ import ExportSettings, PillowRenderer, render

EXCERPTS = (
    (0, 12, 10),
    (114, 121, 10),
    (144, 150, 10),
    (161, 167, 10),
    (204, 211, 10),
    (224, 230, 10),
    (252, 260, 10),
    (144, 150, 30),
    (161, 167, 30),
)


def contracts(video, report):
    import render as wrapper

    cases = [([], 0, 12, "low", 10)] + [
        (["--quality", q, "--fps", str(f)], 0, video.duration, q, f) for q in ("low", "high", "4k") for f in (10, 30)
    ]
    cases += [(["--quality", "low", "--fps", "30", "--range", "161", "167"], 161, 167, "low", 30)]
    for args, start, end, quality, fps in cases:
        with (
            patch.object(wrapper, "build_video", return_value=(video, report)),
            patch.object(wrapper, "render", return_value="contract only") as export,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            wrapper.main(args)
            kwargs = export.call_args.kwargs
            assert kwargs["start_time"] == start and kwargs["end_time"] == end
            assert kwargs["settings"].dimensions(video.canvas) == wrapper.SIZES[quality]
            assert kwargs["settings"].fps == fps
            assert kwargs["settings"].antialias == (1 if quality == "low" else 2)
    # Seeking backward and repeated frames must agree with uncached playback.
    cached = PillowRenderer(1)
    uncached = PillowRenderer(1, frame_cache_mb=0, code_cache_mb=0, caption_cache_mb=0)
    for t in (3.5, 146, 214, 114.62, 164, 3.5, 146):
        assert cached.frame(video, t, (480, 270)).tobytes() == uncached.frame(video, t, (480, 270)).tobytes(), t
    return {"cli_cases": len(cases), "random_access_frames": 7, "playback_execution_calls": 0}


def audio_samples(path, start, duration):
    import numpy as np

    result = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-ar",
            "12000",
            "-ac",
            "1",
            "-f",
            "f32le",
            "pipe:1",
        ],
        capture_output=True,
        check=True,
    )
    return np.frombuffer(result.stdout, dtype="<f4").astype("float64")


def inspect_media(path, start, end, fps):
    import numpy as np

    probe = json.loads(
        subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    )
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == (1280, 720)
    a, b = map(int, video["avg_frame_rate"].split("/"))
    assert a / b == fps
    expected = math.ceil((end - start) * fps - 1e-8)
    assert int(video["nb_frames"]) == expected
    assert math.isclose(float(video["duration"]), expected / fps, abs_tol=0.001)
    assert len([s for s in probe["streams"] if s["codec_type"] == "audio"]) == 1
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], check=True)
    source = audio_samples(PROJECT / "audio.mp3", start, end - start)
    actual = audio_samples(path, 0, end - start)
    n = min(len(source), len(actual))
    source = source[:n]
    actual = actual[:n]
    correlation = float(np.corrcoef(source, actual)[0, 1])
    assert correlation > 0.99, (path, correlation)
    # Search the bounded timing neighborhood using FFT cross correlation.
    size = 1 << (2 * n - 1).bit_length()
    cross = np.fft.irfft(np.fft.rfft(actual, size) * np.conj(np.fft.rfft(source, size)), size)
    lags = np.arange(-1200, 1201)
    lag = int(lags[np.argmax(cross[lags % size])])
    assert abs(lag) <= 24, (path, lag)  # two milliseconds at the comparison sample rate
    frames = []
    for i, t in enumerate((min(1, (end - start) / 3), (end - start) * 0.65)):
        frame = path.with_name(path.stem + f"-frame-{i + 1}.png")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(path), "-frames:v", "1", str(frame)], check=True
        )
        frames.append(str(frame.relative_to(PROJECT)))
    return {
        "path": str(path.relative_to(PROJECT)),
        "source_range": [start, end],
        "fps": fps,
        "size": [1280, 720],
        "frames": expected,
        "decode_passed": True,
        "audio_correlation": correlation,
        "audio_lag_ms": lag / 12,
        "inspection_frames": frames,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect-only", action="store_true", help="Verify existing excerpts without rendering again")
    args = parser.parse_args()
    # Ordinary builds, validations, and frames must never execute checkpoints.
    with (
        patch("faceless_champ.prepare_playground", side_effect=AssertionError("Playback executed a checkpoint")),
        patch("faceless_champ.playground.prepare._python", side_effect=AssertionError("Playback executed Python")),
    ):
        video, report = build_video()
        preflight = check(video, report)
        tests = contracts(video, report)
        renderer = PillowRenderer(1)
        results = []
        directory = PROJECT / "output/qa"
        directory.mkdir(parents=True, exist_ok=True)
        for start, end, fps in EXCERPTS:
            assert end - start <= 12 and end < video.duration
            path = directory / f"guide-{start:g}-{end:g}s-low-{fps}fps.mp4"
            if not args.inspect_only:
                print(f"Preview {start:g}–{end:g}s at {fps} FPS", flush=True)
                settings = ExportSettings(width=1280, height=720, fps=fps, antialias=1, crf=23, preset="veryfast")
                render(
                    video,
                    path,
                    settings=settings,
                    renderer=renderer,
                    start_time=start,
                    end_time=end,
                    overwrite=True,
                    progress=lambda done, total: (
                        print(f"  {done}/{total}", flush=True) if done % 50 == 0 or done == total else None
                    ),
                )
            result = inspect_media(path, start, end, fps)
            print(f"  decode passed; audio correlation {result['audio_correlation']:.5f}", flush=True)
            results.append(result)
    verification = {
        "date": "2026-10-12",
        "preflight": preflight,
        "contracts": tests,
        "excerpts": results,
        "visuals_inspected": False,
        "full_export_verified": False,
        "high_and_4k": "CLI and dimensions checked; no high/4K media exported",
    }
    (PROJECT / "verification.json").write_text(json.dumps(verification, indent=2))
    print(PROJECT / "verification.json")


if __name__ == "__main__":
    main()
