"""Verify a completed export and create inspection frames and chapter clips."""

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
interpreter = PROJECT.parents[1] / ".venv/bin/python"
if interpreter.exists() and Path(sys.prefix).resolve() != interpreter.parent.parent.resolve():
    os.execv(str(interpreter), [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]])
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / "output/.matplotlib"))

import numpy as np
from main import programming_value_video
from PIL import Image, ImageDraw, ImageFont
from scene.audit_v2 import check
from scene.design_v2 import FONT


def run(args):
    p = subprocess.run(args, capture_output=True, check=False)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace")[-3000:])
    return p.stdout


def decode_audio(path):
    data = run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "pipe:1"])
    return np.frombuffer(data, dtype="<f4").astype(np.float64)


def audio_alignment(source, export, start=0):
    reference = decode_audio(source)
    output = decode_audio(export)
    first = round(start * 16000)
    reference = reference[first : first + len(output)]
    n = min(len(reference), len(output))
    reference = reference[:n]
    output = output[:n]
    windows = []
    length = min(8 * 16000, n)
    for at in sorted({min(16000, max(0, n - length)), max(0, n // 2 - length // 2), max(0, n - length - 8000)}):
        x = reference[at : at + length]
        y = output[at : at + length]
        x = x - x.mean()
        y = y - y.mean()
        corr = float(np.dot(x, y) / np.sqrt(np.dot(x, x) * np.dot(y, y)))
        gain = float(np.dot(x, y) / np.dot(x, x))
        fft_n = 1 << (2 * len(x) - 1).bit_length()
        cross = np.fft.irfft(np.fft.rfft(y, fft_n) * np.conj(np.fft.rfft(x, fft_n)), fft_n)
        shifts = np.arange(-800, 801)
        delay = int(shifts[np.argmax(cross[shifts % fft_n])])
        windows.append(
            {
                "source_time": start + at / 16000,
                "zero_lag_correlation": corr,
                "gain_ratio": gain,
                "delay_ms": delay / 16,
            }
        )
    passed = all(
        w["zero_lag_correlation"] > 0.995 and 0.98 <= w["gain_ratio"] <= 1.02 and abs(w["delay_ms"]) <= 5
        for w in windows
    )
    drift = max(w["delay_ms"] for w in windows) - min(w["delay_ms"] for w in windows)
    return {
        "passed": passed,
        "windows": windows,
        "drift_ms": drift,
        "compared_duration": n / 16000,
        "source_decoded_duration": len(decode_audio(source)) / 16000,
    }


def inspect_frames(path, compiled, directory):
    directory.mkdir(parents=True, exist_ok=True)
    samples = [(e["start"] + (e["end"] - e["start"]) * 0.78, e["kind"]) for e in compiled.report["visual_events"]]
    samples.extend([(0, "lead-in"), (493.10, "audio-tail")])
    font = ImageFont.truetype(FONT, 22)
    contacts = []
    for i, (time, kind) in enumerate(samples):
        target = directory / f"{i + 1:02}-{time:08.3f}.png"
        run(["ffmpeg", "-v", "error", "-ss", str(time), "-i", str(path), "-frames:v", "1", "-y", str(target)])
        im = Image.open(target).convert("RGB")
        thumb = im.resize((640, 360), Image.Resampling.LANCZOS)
        if i % 12 == 0:
            contacts.append(Image.new("RGB", (1920, 1568), "#141820"))
        offset = i % 12
        x = (offset % 3) * 640
        y = (offset // 3) * 392
        contacts[-1].paste(thumb, (x, y))
        ImageDraw.Draw(contacts[-1]).text((x + 12, y + 363), f"{time:.3f}s · {kind}", font=font, fill="white")
    for i, contact in enumerate(contacts):
        contact.save(directory / f"contact-{i + 1}.png")
    return [{"time": t, "kind": k} for t, k in samples]


def chapter_clips(path, directory):
    directory.mkdir(exist_ok=True)
    windows = [
        ("code-value", 74, 84),
        ("systems", 136, 148),
        ("optimization", 184, 198),
        ("better-questions", 248, 265),
        ("human-judgment", 354, 368),
        ("useful-systems", 479, 493.1),
    ]
    for name, start, end in windows:
        target = directory / f"{name}.mp4"
        run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-ss",
                str(start),
                "-i",
                str(path),
                "-t",
                str(end - start),
                "-vf",
                "scale=960:540",
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-preset",
                "veryfast",
                "-c:a",
                "aac",
                "-movflags",
                "+faststart",
                "-y",
                str(target),
            ]
        )
        print(target, flush=True)
    return [{"chapter": name, "start": start, "end": end} for name, start, end in windows]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", type=Path, default=PROJECT / "output/programming-value-v2-full.mp4")
    parser.add_argument("--clips", action="store_true")
    parser.add_argument("--audio-only", action="store_true")
    parser.add_argument("--start", type=float, default=0)
    args = parser.parse_args()
    compiled = programming_value_video()
    if args.audio_only:
        result = audio_alignment(PROJECT / "audio.mp3", args.video, args.start)
        print(json.dumps(result, indent=2))
        if not result["passed"]:
            raise RuntimeError("Ranged audio alignment failed")
        return
    result = check(compiled)
    probe = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(args.video)]))
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    audio = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    expected = math.ceil(compiled.duration * 30 - 1e-9)
    if (video["width"], video["height"], video["r_frame_rate"]) != (1920, 1080, "30/1"):
        raise RuntimeError("Full export is not 1920×1080 / 30 fps")
    if int(video["nb_frames"]) != expected:
        raise RuntimeError("Wrong full-export frame count")
    if abs(float(probe["format"]["duration"]) - compiled.duration) > 1 / 30 + 0.002:
        raise RuntimeError("Unexpected duration drift")
    print("Decoding the complete video…", flush=True)
    progress = run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-xerror",
            "-i",
            str(args.video),
            "-map",
            "0:v:0",
            "-progress",
            "pipe:1",
            "-f",
            "null",
            "-",
        ]
    ).decode()
    frames = [int(line.split("=", 1)[1]) for line in progress.splitlines() if line.startswith("frame=")]
    if not frames or frames[-1] != expected:
        raise RuntimeError("Full decode frame count mismatch")
    packets = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "packet=pts",
                "-of",
                "json",
                str(args.video),
            ]
        )
    )["packets"]
    numerator, denominator = map(int, video["time_base"].split("/"))
    pts = np.sort(np.array([int(p["pts"]) for p in packets]) * numerator / denominator)
    if len(pts) != expected:
        raise RuntimeError("Packet count differs from the frame schedule")
    timestamp_error = float(np.max(np.abs(pts - np.arange(expected) / 30)))
    if timestamp_error > 1e-5:
        raise RuntimeError("Joined video timestamps drift from the absolute frame schedule")
    result.update(
        video=str(args.video.resolve()),
        dimensions=[1920, 1080],
        fps=30,
        frames=expected,
        decoded_frames=frames[-1],
        complete_decode=True,
        encoded_duration=float(probe["format"]["duration"]),
        video_codec=video["codec_name"],
        audio_codec=audio["codec_name"],
        maximum_video_timestamp_error=timestamp_error,
        output_sha256=hashlib.sha256(args.video.read_bytes()).hexdigest(),
    )
    result["audio_alignment"] = audio_alignment(PROJECT / "audio.mp3", args.video)
    if not result["audio_alignment"]["passed"]:
        raise RuntimeError("Full audio alignment failed")
    print("Extracting representative encoded frames…", flush=True)
    result["inspection_frames"] = inspect_frames(args.video, compiled, PROJECT / "output/encoded-v2")
    if args.clips:
        result["chapter_clips"] = chapter_clips(args.video, PROJECT / "output/clips-v2")
    layout = json.loads((PROJECT / "output/layout-audit-v2.json").read_text())
    if not layout["passed"]:
        raise RuntimeError("Layout audit did not pass")
    result["layout_audit"] = {"frames_checked": layout["frames_checked"], "issues": layout["issues"]}
    result["passed"] = True
    (PROJECT / "output/verification-v2.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {k: result[k] for k in ("passed", "frames", "decoded_frames", "encoded_duration", "audio_alignment")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
