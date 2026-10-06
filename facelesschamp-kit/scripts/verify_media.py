"""Full short-video QA from installed packages, including a late source-clock excerpt."""

import argparse
import array
import json
import math
import subprocess
from io import BytesIO
from pathlib import Path

from faceless_champ import PillowRenderer
from faceless_champ.audio import probe
from PIL import Image, ImageChops, ImageStat

from facelesschamp_kit import Project
from facelesschamp_kit.scaffold import init_project


def pcm(path, start=None, end=None):
    command = ["ffmpeg", "-v", "error", "-i", str(path)]
    if start is not None:
        command += ["-ss", str(start), "-t", str(end - start)]
    command += ["-vn", "-ac", "1", "-ar", "22050", "-f", "s16le", "-"]
    data = subprocess.run(command, capture_output=True, check=True).stdout
    samples = array.array("h")
    samples.frombytes(data)
    return samples


def verify(path, duration, audio, fps, size):
    info = probe(path)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (video["width"], video["height"]) == size
    a, b = map(int, video["avg_frame_rate"].split("/"))
    assert abs(a / b - fps) < 0.001
    assert abs(float(info["format"]["duration"]) - duration) < 0.12
    assert any(s["codec_type"] == "audio" for s in info["streams"]) == audio
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], check=True)
    return {"path": str(path), "duration": duration, "size": size, "fps": fps, "audio": audio, "decoded": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", choices=("preview", "final"), default="preview")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for name, template, duration, has_audio in (
        ("silent", "silent", 10, False),
        ("narrated", "narrated-short", 30, True),
    ):
        root = args.output / name
        if not root.exists():
            init_project(root, template)
        project = Project(root)
        compiled = project.build()
        settings = project.settings(compiled, args.profile)
        output = root / "output" / f"{name}.mp4"
        print(f"Rendering {name}: {duration}s, {args.profile}", flush=True)
        project.export("main", output, profile=args.profile, overwrite=True)
        results.append(
            verify(output, duration, has_audio, settings.fps, settings.dimensions(compiled.composition.canvas))
        )
        project.storyboard("main", root / "output/storyboard", overwrite=True)
        if has_audio:
            excerpt = root / "output/late.mp4"
            project.export("main", excerpt, preview=True, start=22, end=27, overwrite=True)
            preview_settings = project.settings(compiled, "preview")
            results.append(
                verify(excerpt, 5, True, preview_settings.fps, preview_settings.dimensions(compiled.composition.canvas))
            )
            source = compiled.context.assets.audio("voiceover")
            expected, actual = pcm(source, 22, 27), pcm(excerpt)
            length = min(len(expected), len(actual))
            # Skip the first/last 50ms, where codec priming and padding may differ.
            a, b = expected[1102 : length - 1102], actual[1102 : length - 1102]
            correlation = sum(x * y for x, y in zip(a, b)) / math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
            assert correlation > 0.97, correlation
            renderer = PillowRenderer(1)
            for time in (22, 24, 26):
                frame = renderer.frame(compiled.composition, time, (270, 480))
                rebuilt = project.build()
                reference = PillowRenderer(1).frame(rebuilt.composition, time, (270, 480))
                assert ImageChops.difference(frame.convert("RGB"), reference.convert("RGB")).getbbox() is None
            errors = []
            for offset in (0, 2, 4):
                decoded = subprocess.run(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-ss",
                        str(offset),
                        "-i",
                        str(excerpt),
                        "-frames:v",
                        "1",
                        "-f",
                        "image2pipe",
                        "-vcodec",
                        "png",
                        "-",
                    ],
                    capture_output=True,
                    check=True,
                ).stdout
                actual_frame = Image.open(BytesIO(decoded)).convert("RGB")
                source_frame = renderer.frame(compiled.composition, 22 + offset, actual_frame.size).convert("RGB")
                error = sum(ImageStat.Stat(ImageChops.difference(actual_frame, source_frame)).mean) / 3
                assert error < 4, error
                errors.append(error)
            results[-1]["excerpt_source_pixel_mae"] = errors
            results[-1]["audio_correlation"] = correlation
            results[-1]["source_frame_rebuilds_identical"] = True
    (args.output / "verification.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2), flush=True)


if __name__ == "__main__":
    main()
