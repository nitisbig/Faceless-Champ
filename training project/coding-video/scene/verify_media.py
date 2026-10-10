"""Verify only the five explicitly selected excerpts; never launch a video render."""

import json
import math
import subprocess
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT / "output"
EXCERPTS = (
    (33, 41, "low", 20, (1280, 720)),
    (72, 80, "low", 30, (1280, 720)),
    (110.64, 124.84, "low", 30, (1280, 720)),
    (38, 39, "high", 60, (1920, 1080)),
    (124, 124.25, "4k", 30, (3840, 2160)),
)


def command(args):
    return subprocess.run(args, capture_output=True, check=True).stdout


def audio(path):
    return np.frombuffer(
        command(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "pipe:1"]),
        dtype="<f4",
    )


def main():
    source = audio(PROJECT / "audio.mp3")
    results = []
    for start, end, quality, fps, size in EXCERPTS:
        path = OUTPUT / f"coding-video-midnight-{start:g}-{end:g}s-{quality}-{fps}fps.mp4"
        info = json.loads(
            command(
                ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(path)]
            )
        )
        video = next(s for s in info["streams"] if s["codec_type"] == "video")
        assert (video["width"], video["height"]) == size
        numerator, denominator = map(int, video["avg_frame_rate"].split("/"))
        assert numerator / denominator == fps
        frames = math.ceil((end - start) * fps - 1e-9)
        assert int(video["nb_read_frames"]) == frames
        assert abs(float(video["duration"]) - frames / fps) < 1 / fps
        command(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
        decoded = audio(path)
        expected = source[round(start * 48000) : round(end * 48000)]
        count = min(len(decoded), len(expected))
        assert count >= (end - start) * 48000 - 2
        correlation = float(np.corrcoef(expected[:count], decoded[:count])[0, 1])
        assert correlation > 0.99, (path.name, correlation)
        image = OUTPUT / f"{path.stem}-frame.png"
        offset = min((end - start) * 0.8, end - start - 1 / fps)
        command(["ffmpeg", "-v", "error", "-i", str(path), "-ss", str(offset), "-frames:v", "1", "-y", str(image)])
        results.append(
            {
                "path": path.name,
                "source_range": [start, end],
                "size": size,
                "fps": fps,
                "frames": frames,
                "complete_decode": True,
                "audio_correlation": correlation,
                "inspected_frame": image.name,
            }
        )
    report = {"excerpts": results, "total_frames": sum(r["frames"] for r in results), "full_export_verified": False}
    (OUTPUT / "media-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
