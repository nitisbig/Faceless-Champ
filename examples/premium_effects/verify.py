"""Offline media, source-time seek and repeated-export checks for Phase 2A."""

from __future__ import annotations

import argparse
import json
import random
import resource
import subprocess
import tempfile
from hashlib import sha256
from io import BytesIO
from pathlib import Path

from PIL import Image as PI
from PIL import ImageChops, ImageDraw, ImageStat
from render import TIMES, comparison

from faceless_champ import (
    Bounds,
    Canvas,
    CircleMask,
    GradientStop,
    Group,
    LinearGradient,
    PillowRenderer,
    Scene,
    ShadowStyle,
    card_surface,
    gradient_surface,
)
from faceless_champ.typography import load_font


def media(path):
    raw = subprocess.check_output(
        ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True,
    )
    result = json.loads(raw)
    video = next(stream for stream in result["streams"] if stream["codec_type"] == "video")
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], check=True)
    return {
        "path": str(path),
        "width": video["width"],
        "height": video["height"],
        "fps": video["r_frame_rate"],
        "frames": int(video["nb_read_frames"]),
        "seconds": float(result["format"]["duration"]),
        "codec": video["codec_name"],
        "audio_streams": sum(s["codec_type"] == "audio" for s in result["streams"]),
        "bytes": path.stat().st_size,
        "sha256": sha256(path.read_bytes()).hexdigest(),
        "full_decode_passed": True,
    }


def seeks(movie):
    probes = (0, 0.1, 0.37, 0.77, 1, 2, 3.5, 5.9)
    result = {"size": [320, 180], "antialias": 1, "hash_comparisons": 0, "workloads": []}
    with PillowRenderer(1, frame_cache_mb=0) as renderer:
        expected = {t: sha256(renderer.frame(movie, t, (320, 180)).tobytes()).hexdigest() for t in probes}
    for cache in (0, 64):
        with PillowRenderer(1, frame_cache_mb=cache) as renderer:
            for fps in (24, 30, 60):
                frames = list(range(fps * 6))
                order = "forward"
                if fps == 30:
                    frames.reverse()
                    order = "reverse"
                elif fps == 60:
                    random.Random(20261016).shuffle(frames)
                    order = "shuffled"
                for index in frames:
                    renderer.frame(movie, index / fps, (320, 180))
                for t in (*reversed(probes), *probes, *probes):
                    assert sha256(renderer.frame(movie, t, (320, 180)).tobytes()).hexdigest() == expected[t]
                    result["hash_comparisons"] += 1
                result["workloads"].append(
                    {"cache_mb": cache, "fps": fps, "order": order, "frames_sampled": len(frames)}
                )
    result["probe_hashes"] = {str(t): value for t, value in expected.items()}
    return result


def repeated_exports():
    retained = []
    with tempfile.TemporaryDirectory(prefix="fc-premium-exports-") as temporary:
        for _ in range(20):
            paint = LinearGradient((GradientStop(0, "red"), GradientStop(1, "#0000FF00")), angle=125)
            image = gradient_surface(Bounds(0, 0, 64, 36), fill=paint)
            scene = Scene(Canvas(64, 36, "#FFFFFF")).add(image).wait(0.2)
            with PillowRenderer(1) as renderer:
                scene.render(
                    Path(temporary) / "cycle.mp4",
                    width=64,
                    height=36,
                    fps=10,
                    antialias=1,
                    renderer=renderer,
                    preset="ultrafast",
                    overwrite=True,
                )
            assert not renderer._images and not renderer._sprites and not renderer._scene_frames
            retained.append((len(renderer._images), len(renderer._sprites), renderer._frame_cache_bytes))
    return {
        "cycles": 20,
        "frames_per_export": 2,
        "cache_entries_bytes_after_close": retained,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "note": "Whole-process high-water RSS is not a per-export leak oracle; weak-reference lifecycle checks are in tests.",
    }


def decoded_comparisons(movie, path, directory):
    records = []
    with PillowRenderer(1) as renderer:
        for time in TIMES:
            # All six times are exactly on the default 30-FPS grid.
            index = round(time * 30)
            png = subprocess.check_output(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(path),
                    "-vf",
                    f"select=eq(n\\,{index})",
                    "-frames:v",
                    "1",
                    "-f",
                    "image2pipe",
                    "-c:v",
                    "png",
                    "pipe:1",
                ]
            )
            destination = directory / f"decoded-{index:03d}.png"
            destination.write_bytes(png)
            with PI.open(BytesIO(png)) as decoded:
                reference = renderer.frame(movie, index / 30, (960, 540)).convert("RGB")
                difference = ImageChops.difference(reference, decoded.convert("RGB"))
                error = sum(ImageStat.Stat(difference).mean) / 3
                assert error < 4, (time, error)
                records.append(
                    {"time": time, "frame_index": index, "mean_absolute_rgb_error": error, "path": str(destination)}
                )
    return records


def edge_checks(directory):
    """Alpha backgrounds, colored shadow, affine mask, and a shallow 8-bit ramp."""
    checker = PI.new("RGBA", (320, 180), "#FFFFFF")
    draw = ImageDraw.Draw(checker)
    for y in range(0, 180, 12):
        for x in range(0, 320, 12):
            if (x // 12 + y // 12) % 2:
                draw.rectangle((x, y, x + 11, y + 11), fill="#C9CED8")
    sheet = PI.new("RGB", (960, 408), "#DDE2EA")
    labels = (
        "ALPHA / BLACK",
        "ALPHA / WHITE",
        "ALPHA / CHECKER",
        "COLORED SHADOW",
        "AFFINE MASK / AA2",
        "SHALLOW sRGB RAMP",
    )
    fade = LinearGradient((GradientStop(0, "#ED5465"), GradientStop(1, "#0000FF00")))
    for index, label in enumerate(labels):
        shadow = None
        bounds = Bounds(20, 15, 300, 165)
        fill = fade
        if index == 3:
            fill = LinearGradient((GradientStop(0, "white"), GradientStop(1, "white")))
            shadow = ShadowStyle(color="#9441D0B0", blur=7, offset=(0, 5))
            bounds = Bounds(0, 0, 320, 180)
        elif index in (4, 5):
            fill = LinearGradient(
                (GradientStop(0, "#111827"), GradientStop(1, "#3D6595")), angle=125 if index == 4 else 0
            )
        visual = card_surface(bounds, fill=fill, radius=22, shadow=shadow)
        if index == 4:
            visual = Group(visual, mask=CircleMask(68), scale_x=1.05, scale_y=0.8, rotation=9, opacity=0.7)
        scene = Scene(Canvas(320, 180, "#00000000")).add(visual).wait(1)
        background = (
            PI.new("RGBA", (320, 180), "black" if index == 0 else "white") if index in (0, 1, 3) else checker.copy()
        )
        with PillowRenderer(2) as renderer:
            background.alpha_composite(renderer.frame(scene, 0.5, (320, 180)))
        x, y = index % 3 * 320, index // 3 * 204
        sheet.paste(background.convert("RGB"), (x, y))
        ImageDraw.Draw(sheet).text((x + 10, y + 184), label, font=load_font(None, 13), fill="#172333")
        background.close()
    sheet.save(directory / "edge-checks.png")
    sheet.close()
    checker.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/premium_effects/phase2a/verification.json"))
    parser.add_argument("--overwrite", action="store_true", help="regenerate an existing default preview")
    args = parser.parse_args()
    directory = args.output.parent
    directory.mkdir(parents=True, exist_ok=True)
    movie = comparison()
    report = {"seeks": seeks(movie), "fps_exports": []}
    for fps in (24, 30, 60):
        path = movie.render(
            directory / f"fps-{fps}.mp4",
            width=960,
            height=540,
            fps=fps,
            antialias=1,
            end_time=2,
            preset="fast",
            overwrite=True,
        )
        row = media(path)
        assert row["frames"] == 2 * fps and row["audio_streams"] == 0 and row["seconds"] == 2
        report["fps_exports"].append(row)
    preview = directory / "preview.mp4"
    if args.overwrite or not preview.exists():
        movie.render(preview, width=960, height=540, fps=30, antialias=1, preset="fast", crf=18, overwrite=True)
    report["preview"] = media(preview)
    assert report["preview"]["frames"] == 180 and report["preview"]["seconds"] == 6
    report["decoded_comparisons"] = decoded_comparisons(movie, preview, directory)
    report["repeated_exports"] = repeated_exports()
    with PillowRenderer(2) as renderer:
        renderer.frame(comparison(False), 2, (1920, 1080)).save(directory / "comparison-1080-aa2.png")
    with PillowRenderer(1) as renderer:
        renderer.frame(comparison(False), 2, (3840, 2160)).save(directory / "comparison-4k-aa1.png")
    report["smoke_frames"] = ["comparison-1080-aa2.png", "comparison-4k-aa1.png"]
    edge_checks(directory)
    report["edge_checks"] = "edge-checks.png"
    report["visual_inspection"] = "required separately; this script does not assert human inspection"
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "hash_comparisons": report["seeks"]["hash_comparisons"],
                "exports": report["fps_exports"],
                "preview": report["preview"],
                "repeated_exports": 20,
            },
            indent=2,
        )
    )
    print(args.output)


if __name__ == "__main__":
    main()
