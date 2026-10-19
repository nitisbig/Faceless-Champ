"""Bounded, process-isolated renderer benchmarks; encoding is measured separately.

Example: python scripts/benchmark_renderers.py --output output/skia/benchmarks.json
Optional --baseline-ref HEAD also measures the prior Pillow implementation.
"""

import argparse
import json
import math
import os
import platform
import resource
import statistics
import subprocess
import sys
import time
import types
from pathlib import Path

from PIL import Image as PI

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Bounds,
    Canvas,
    CircleMask,
    GradientStop,
    Group,
    Image,
    LinearGradient,
    PathData,
    Rectangle,
    Scene,
    ShadowStyle,
    Text,
    VectorPath,
    card_surface,
    create_renderer,
    linear,
    rendering_identity,
)

WORKLOADS = ("plain", "ui", "paths", "type", "effects")


def workload(name, backend):
    scene = Scene(Canvas(1920, 1080, "#F4F5F9"))
    if name == "plain":
        return scene.add(Rectangle(width=1100, height=640, fill="#6575E8", stroke=None, position=(960, 540))).wait(2)
    if name == "paths":
        for i in range(16):
            y = 90 + i * 55
            path = PathData().move_to(80, y).cubic_to(570, y - 50, 1250, y + 50, 1840, y)
            c = VectorPath(path, stroke="#527BEF", stroke_width=3)
            with scene.at(0):
                scene.add(c)
                scene.play(c.animate.move_to(c.position[0] + 20, c.position[1] + 8), run_time=2, rate_func=linear)
        return scene
    if name == "type":
        for i in range(24):
            c = Text(
                "Measured typography / AV office 0123456789",
                font=CLEAN_FLOW_FONT,
                font_size=28,
                text_engine="skia" if backend == "skia" else "pillow",
                color="#25314B",
                position=(520 + (i % 2) * 870, 65 + (i // 2) * 82),
            )
            with scene.at(0):
                scene.add(c)
                scene.play(c.animate.move_to(c.position[0] + 10, c.position[1] + 6), run_time=2, rate_func=linear)
        return scene
    if name == "ui":
        for i in range(48):
            c = Rectangle(
                width=195,
                height=100,
                corner_radius=20,
                fill="#FFFFFF",
                stroke="#CDD3E4",
                stroke_width=1,
                position=(150 + (i % 8) * 230, 100 + (i // 8) * 170),
            )
            with scene.at(0):
                scene.add(c)
                scene.play(c.animate.move_to(c.position[0] + 12, c.position[1] + 8), run_time=2, rate_func=linear)
        return scene
    gradient = LinearGradient((GradientStop(0, "#5860EA"), GradientStop(1, "#8FD8EB")), angle=30)
    for i in range(3):
        box = Bounds(160 + i * 550, 250, 660 + i * 550, 830)
        card = card_surface(
            box,
            fill=gradient,
            radius=36,
            shadow=ShadowStyle(blur=8),
            render_mode="vector" if backend == "skia" else "raster",
        )
        raster = Image.from_source(PI.new("RGBA", (60, 60), "#FFFFFF88"), width=180, height=180, position=box.center)
        group = Group(Group(card, raster, mask=CircleMask(240)), rotation=i * 4)
        with scene.at(0):
            scene.add(group)
            scene.play(
                group.animate.move_to(group.position[0] + 12, group.position[1] + 6), run_time=2, rate_func=linear
            )
    return scene


def baseline_renderer(ref, aa):
    code = subprocess.run(
        ["git", "show", f"{ref}:src/faceless_champ/renderer.py"], check=True, capture_output=True, text=True
    ).stdout
    module = types.ModuleType("faceless_champ._benchmark_baseline")
    module.__package__ = "faceless_champ"
    exec(compile(code, "<baseline renderer>", "exec"), module.__dict__)  # noqa: S102 - explicitly selected local git source
    return module.PillowRenderer(aa)


def trial(name, width, backend, aa, frames, baseline=None):
    start = time.perf_counter()
    scene = workload(name, backend)
    authoring = time.perf_counter() - start
    start = time.perf_counter()
    renderer = baseline_renderer(baseline, aa) if baseline else create_renderer(backend, antialias=aa)
    initialized = time.perf_counter() - start
    try:
        size = width, round(width * 9 / 16)
        renderer.validate(scene)
        start = time.perf_counter()
        renderer.frame(scene, 0, size)
        cold = time.perf_counter() - start
        for t in (0.1, 0.2):
            renderer.frame(scene, t, size)
        samples = []
        stats_before = dict(getattr(renderer, "stats", {}))
        for i in range(frames):
            start = time.perf_counter()
            renderer.frame(scene, 0.4 + i / 30, size)
            samples.append((time.perf_counter() - start) * 1000)
        stats = {k: v - stats_before.get(k, 0) for k, v in getattr(renderer, "stats", {}).items()}
        return {
            "authoring_ms": authoring * 1000,
            "initialization_ms": initialized * 1000,
            "cold_frame_ms": cold * 1000,
            "samples_ms": samples,
            "median_ms": statistics.median(samples),
            "p95_ms": sorted(samples)[math.ceil(0.95 * len(samples)) - 1],
            "fps": 1000 / statistics.mean(samples),
            "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "native_cache_bytes": getattr(getattr(renderer, "images", None), "bytes", 0),
            "frame_cache_bytes": getattr(
                getattr(renderer, "frames", None), "bytes", getattr(renderer, "_frame_cache_bytes", 0)
            ),
            "native_stats": stats,
        }
    finally:
        renderer.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--widths", nargs="+", type=int, default=[1920, 3840])
    parser.add_argument("--workloads", nargs="+", choices=WORKLOADS, default=list(WORKLOADS))
    parser.add_argument("--baseline-ref")
    parser.add_argument("--worker", nargs=5, metavar=("WORKLOAD", "WIDTH", "BACKEND", "AA", "FRAMES"))
    args = parser.parse_args()
    if args.worker:
        name, width, backend, aa, frames = args.worker
        print(json.dumps(trial(name, int(width), backend, int(aa), int(frames), args.baseline_ref)))
        return
    if args.trials < 1 or any(w not in (1920, 3840) for w in args.widths):
        parser.error("Use positive trials and widths 1920/3840")
    cpu = platform.processor()
    if not cpu and Path("/proc/cpuinfo").is_file():
        cpu = next(
            (
                line.split(":", 1)[1].strip()
                for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")
            ),
            platform.machine(),
        )
    report = {
        "schema_version": 1,
        "platform": platform.platform(),
        "cpu": cpu,
        "logical_cpus": os.cpu_count(),
        "python": platform.python_version(),
        "versions": rendering_identity("skia", workload("type", "skia")),
        "results": [],
        "notes": [
            "Fresh process per trial; Linux RSS includes imports/native buffers.",
            "Type/effects use native text/retained surfaces for Skia and legacy equivalents for Pillow.",
            "Frame measurements include pixel conversion; exclude FFmpeg. Preview export is measured separately.",
        ],
    }
    for width in args.widths:
        frames = 24 if width == 1920 else 8
        for name in args.workloads:
            variants = [("pillow", 1, None), ("pillow", 2, None), ("skia", 1, None)]
            if args.baseline_ref and name != "paths":
                variants.append(("pillow", 2, args.baseline_ref))
            for backend, aa, ref in variants:
                trials = []
                for _ in range(args.trials):
                    command = [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--worker",
                        name,
                        str(width),
                        backend,
                        str(aa),
                        str(frames),
                    ]
                    if ref:
                        command.extend(["--baseline-ref", ref])
                    result = subprocess.run(command, capture_output=True, text=True, check=True)
                    trials.append(json.loads(result.stdout))
                med = statistics.median(t["median_ms"] for t in trials)
                report["results"].append(
                    {
                        "workload": name,
                        "width": width,
                        "height": round(width * 9 / 16),
                        "backend": backend,
                        "antialias": aa,
                        "baseline_ref": ref,
                        "frames_per_trial": frames,
                        "median_ms": med,
                        "trials": trials,
                    }
                )
                print(
                    f"{width} {name} {backend} AA={aa} baseline={ref or '-'}: {med:.2f} ms/frame",
                    file=sys.stderr,
                    flush=True,
                )
    output = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
        print(args.output)
    else:
        print(output)


if __name__ == "__main__":
    main()
