"""Exercise whiteboard CLI/media from an installed package, without source imports."""

import argparse
import array
import json
import math
import subprocess
import sys
import wave
from io import BytesIO
from pathlib import Path

from faceless_champ import PillowRenderer
from PIL import Image, ImageChops, ImageDraw, ImageStat
from verify_media import pcm, verify

from facelesschamp_kit import Project


def cli(root, *arguments):
    subprocess.run(
        [sys.executable, "-m", "facelesschamp_kit", "--project", str(root), *map(str, arguments)], check=True
    )


def decoded_frame(path, time):
    data = subprocess.run(
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
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "-",
        ],
        capture_output=True,
        check=True,
    ).stdout
    return Image.open(BytesIO(data)).convert("RGB")


def inspect_frames(project, path, times, output, source_start=0):
    compiled = project.build()
    sheet = Image.new("RGB", (960, math.ceil(len(times) / 2) * 294), "#E2E8F0")
    errors = []
    renderer = PillowRenderer(1)
    for index, time in enumerate(times):
        decoded = decoded_frame(path, time)
        source = renderer.frame(compiled.composition, source_start + time, decoded.size).convert("RGB")
        error = sum(ImageStat.Stat(ImageChops.difference(decoded, source)).mean) / 3
        assert error < 4, (time, error)
        errors.append(error)
        x, y = (index % 2) * 480, (index // 2) * 294
        sheet.paste(decoded.resize((480, 270)), (x, y))
        ImageDraw.Draw(sheet).text((x + 8, y + 276), f"Source {source_start + time:.2f}s", fill="black")
    sheet.save(output)
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True, help="Fresh verification directory")
    parser.add_argument("--resume", action="store_true", help="Reuse existing outputs but repeat media verification")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=args.resume)

    def artifact(project_root, command, destination, *options):
        if not (args.resume and destination.exists()):
            cli(project_root, command, "main", *options, "-o", destination)

    root = output / "silent"
    if not (args.resume and root.exists()):
        cli(output, "init", root, "--template", "whiteboard-basic")
    cli(root, "validate", "main")
    artifact(root, "frame", output / "frame.png", "--time", 4)
    artifact(root, "storyboard", output / "storyboard")
    artifact(root, "preview", output / "preview.mp4")
    artifact(root, "render", output / "final.mp4")
    results = [
        verify(output / "preview.mp4", 10, False, 15, (960, 540)),
        verify(output / "final.mp4", 10, False, 30, (1920, 1080)),
    ]
    results[-1]["decoded_frame_mae"] = inspect_frames(
        Project(root),
        output / "final.mp4",
        (0, 0.5, 1.5, 3.5, 4.5, 5, 6.5, 9.5),
        output / "decoded-frames.png",
    )

    narrated = output / "narrated"
    if not (args.resume and narrated.exists()):
        cli(output, "init", narrated, "--template", "whiteboard-basic")
    samples = array.array(
        "h", (int(7000 * math.sin(2 * math.pi * (180 * i / 22050 + 30 * (i / 22050) ** 2))) for i in range(4 * 22050))
    )
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(narrated / "assets/audio/test.wav"), "wb") as stream:
        stream.setparams((1, 2, 22050, 0, "NONE", "not compressed"))
        stream.writeframes(samples.tobytes())
    (narrated / "assets/words.srt").write_text(
        "7\n00:00:00,250 --> 00:00:00,750\nFirst\n\n"
        "19\n00:00:01,250 --> 00:00:02,000\nSecond\n\n"
        "55\n00:00:02,500 --> 00:00:03,500\nTail\n"
    )
    (narrated / "assets/manifest.json").write_text(
        json.dumps(
            {
                "voice": {"type": "audio", "path": "assets/audio/test.wav", "source": "Synthetic test tone"},
                "words": {"type": "subtitle", "path": "assets/words.srt"},
            }
        )
    )
    (narrated / "videos/main.py").write_text("""from facelesschamp_kit.blocks import WhiteboardCircle, WhiteboardDrawing
from facelesschamp_kit.templates import WhiteboardScene, whiteboard_basic

def build(ctx):
    drawing = WhiteboardDrawing((WhiteboardCircle((250, 500), 100), WhiteboardCircle((750, 500), 100)))
    return whiteboard_basic(ctx, audio="voice", subtitles="words", markers={"first": 7, "next": 19}, scenes=[
        WhiteboardScene("first", drawing, label="SYNTHETIC AUDIO TEST", cues=("first", "next")),
        WhiteboardScene("tail", drawing, label="SYNTHETIC AUDIO TEST", start=1.25, duration=1),
    ])
""")
    artifact(narrated, "preview", output / "narrated-excerpt.mp4", "--start", 1.25, "--end", 3.75)
    result = verify(output / "narrated-excerpt.mp4", 2.5, True, 15, (960, 540))
    expected = pcm(narrated / "assets/audio/test.wav", 1.25, 3.75)
    actual = pcm(output / "narrated-excerpt.mp4")
    length = min(len(expected), len(actual))
    a, b = expected[1102 : length - 1102], actual[1102 : length - 1102]
    correlation = sum(x * y for x, y in zip(a, b)) / math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
    assert correlation > 0.97, correlation
    result["audio_correlation"] = correlation
    result["decoded_frame_mae"] = inspect_frames(
        Project(narrated),
        output / "narrated-excerpt.mp4",
        (0, 0.8, 2.2),
        output / "narrated-frames.png",
        source_start=1.25,
    )
    results.append(result)
    (output / "verification.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
