"""Render showcase videos and write reproducible verification artifacts."""

import array
import json
import math
import subprocess
from pathlib import Path

from showcase import AnimatedTitle, media_sequence, six_panel_canvas

from faceless_champ import Canvas, Scene, Text, render
from faceless_champ.audio import probe

OUTPUT = Path(__file__).resolve().parents[1] / "output"


def verify(path, node, dimensions, fps=30):
    info = probe(path)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == dimensions
    assert video["codec_name"] == "h264"
    assert video["pix_fmt"] == "yuv420p"
    numerator, denominator = map(int, video["avg_frame_rate"].split("/"))
    assert numerator / denominator == fps
    assert abs(float(info["format"]["duration"]) - node.duration) <= 1 / fps + 0.001
    # Decode every frame to catch damaged exports, not just plausible metadata.
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], check=True)
    return {
        "path": str(path),
        "duration": float(info["format"]["duration"]),
        "dimensions": dimensions,
        "fps": fps,
        "bytes": path.stat().st_size,
        "streams": [{k: s[k] for k in ("codec_type", "codec_name")} for s in info["streams"]],
    }


def main():
    OUTPUT.mkdir(exist_ok=True)
    records = []
    examples = [
        ("animated_title", AnimatedTitle, [0.5, 2.8, 4.1]),
        ("media_sequence", media_sequence, [1.5, 3.2, 4.6]),
        ("six_panel_canvas", six_panel_canvas, [0.4, 1.7, 3.2]),
    ]
    for name, factory, times in examples:
        node = factory()
        print(f"Rendering {name}: {node.duration:.2f}s at 720p / 30fps", flush=True)
        path = render(node, OUTPUT / f"{name}.mp4", quality="ql", overwrite=True)
        record = verify(path, node, (1280, 720))
        for time in times:
            preview = OUTPUT / f"{name}_{time:.1f}s.png"
            subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-ss",
                    str(time),
                    "-i",
                    str(path),
                    "-frames:v",
                    "1",
                    "-update",
                    "1",
                    str(preview),
                ],
                check=True,
            )
        if name == "media_sequence":
            audio = subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", "48000", "pipe:1"],
                capture_output=True,
                check=True,
            )
            samples = array.array("f")
            samples.frombytes(audio.stdout)
            rms = lambda a, b, samples=samples: math.sqrt(
                sum(x * x for x in samples[int(a * 48000) : int(b * 48000)]) / (int(b * 48000) - int(a * 48000))
            )
            record["audio_rms"] = {"before": rms(0, 0.2), "during": rms(1, 2), "after": rms(4.5, 5)}
            assert record["audio_rms"]["before"] < 0.001
            assert record["audio_rms"]["during"] > 0.01
            assert record["audio_rms"]["after"] < 0.001
        records.append(record)
        print(f"Verified {path.name}", flush=True)
    for quality, dimensions in [("qh", (1920, 1080)), ("qk", (3840, 2160))]:
        print(f"Rendering {quality} resolution smoke check", flush=True)
        node = Scene(Canvas(bg="#101b30"))
        node.add(Text("Faceless Champ / resolution check", font_size=72, position=(960, 540))).wait(0.1)
        path = render(node, OUTPUT / f"resolution_{quality}.mp4", quality=quality, preset="ultrafast", overwrite=True)
        records.append(verify(path, node, dimensions))
    (OUTPUT / "verification.json").write_text(json.dumps(records, indent=2) + "\n")
    print(f"All exports verified. Report: {OUTPUT / 'verification.json'}", flush=True)


if __name__ == "__main__":
    main()
