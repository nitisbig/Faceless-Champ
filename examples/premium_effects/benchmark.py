"""CPU-only construction/native-RSS and interleaved legacy/gradient replay benchmarks."""

from __future__ import annotations

import argparse
import json
import platform
import resource
import statistics
import subprocess
import sys
import types
from hashlib import sha256
from pathlib import Path
from time import perf_counter

import PIL

from faceless_champ import (
    Bounds,
    Canvas,
    GradientStop,
    Group,
    LinearGradient,
    PillowRenderer,
    RadialGradient,
    Scene,
    ShadowStyle,
    Spring,
    Text,
    card_surface,
    gradient_surface,
)

BASE = "e1312dd409da072e38f308095491418836e9699d"
MODES = ("legacy-solid", "current-solid", "linear", "radial")


def legacy_surfaces():
    """Load only the pinned historical factory into a separate QA module namespace."""
    source = subprocess.check_output(["git", "show", f"{BASE}:src/faceless_champ/surfaces.py"], text=True)
    module = types.ModuleType("faceless_champ._premium_legacy_surfaces")
    sys.modules[module.__name__] = module
    exec(compile(source, "<pinned legacy surfaces>", "exec"), module.__dict__)  # noqa: S102 -- fixed local Git revision
    return module


def gradient(kind):
    stops = (GradientStop(0, "#17213B"), GradientStop(0.55, "#3647A0"), GradientStop(1, "#62DDDB"))
    return RadialGradient(stops, radius=0.8) if kind == "radial" else LinearGradient(stops, angle=125)


def build_scene(mode, legacy=None):
    scene = Scene(Canvas(960, 540, "#111827"))
    factory = legacy.card_surface if mode == "legacy-solid" else card_surface
    shadow_type = legacy.ShadowStyle if mode == "legacy-solid" else ShadowStyle
    fill = "#253852" if mode.endswith("solid") else gradient(mode)
    for i in range(6):
        x, y = 160 + i % 3 * 320, 155 + i // 3 * 240
        face = factory(
            Bounds(x - 140, y - 95, x + 140, y + 95), fill=fill, radius=18, shadow=shadow_type(blur=6, offset=(0, 4))
        )
        label = Text(f"CARD {i + 1}", position=(x, y), font_size=21, color="#ECF3FF")
        group = Group(face, label)
        with scene.at(0):
            scene.add(group)
            scene.play(group.animate.move_to(x + 10, y - 12), run_time=2, rate_func=Spring(100, 10, 1))
    scene.wait_until(2.25)
    return scene


def replay_worker(width, frames, trials):
    legacy = legacy_surfaces()
    size = (width, width * 9 // 16)
    renderers = {mode: PillowRenderer(1) for mode in MODES}
    scenes = {mode: build_scene(mode, legacy) for mode in MODES}
    times = tuple(0.05 + i / (frames - 1) * 1.7 for i in range(frames))
    values = {mode: [] for mode in MODES}
    try:
        for mode in MODES:
            for t in (0.2, 0.3, 0.4):
                renderers[mode].frame(scenes[mode], t, size)
        # The historical and current string branch must match, including shadow pixels.
        assert (
            renderers[MODES[0]].frame(scenes[MODES[0]], 0.77, size).tobytes()
            == renderers[MODES[1]].frame(scenes[MODES[1]], 0.77, size).tobytes()
        )
        order = []
        for trial in range(trials):
            modes = MODES[trial % 4 :] + MODES[: trial % 4]
            order.append(modes)
            for mode in modes:
                start = perf_counter()
                for t in times:
                    renderers[mode].frame(scenes[mode], t, size)
                values[mode].append((perf_counter() - start) * 1000 / frames)
        result = {
            "size": size,
            "antialias": 1,
            "trials": trials,
            "frames_per_trial": frames,
            "trial_order": order,
            "modes": {
                mode: {"trials_ms_per_frame": v, "median_ms_per_frame": statistics.median(v)}
                for mode, v in values.items()
            },
            "legacy_raw_pixels_equal": True,
        }
        print(json.dumps(result))
    finally:
        for renderer in renderers.values():
            renderer.close()


def construction_worker(kind):
    before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    fill = gradient("radial" if kind.startswith("radial") else "linear")
    if kind == "cardinal-1080":
        fill = LinearGradient(fill.stops, angle=0)
    size = (1920, 1080) if kind.endswith("1080") else (480, 320)
    start = perf_counter()
    if kind.endswith("1080") and kind != "rounded-1080":
        image = gradient_surface(Bounds(0, 0, *size), fill=fill)
    else:
        image = card_surface(
            Bounds(0, 0, *size), fill=fill, shadow=ShadowStyle(color="#B24DA880", blur=12, offset=(0, 8))
        )
    seconds = perf_counter() - start
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(
        json.dumps(
            {
                "kind": kind,
                "design_size": size,
                "raster_scale": 2,
                "construction_seconds": seconds,
                "process_peak_rss_kib": peak,
                "peak_rss_before_kib": before,
                "peak_delta_kib": peak - before,
                "encoded_source_bytes": len(image.source_bytes),
                "source_sha256": sha256(image.source_bytes).hexdigest(),
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/premium_effects/phase2a/benchmark.json"))
    parser.add_argument("--frames", type=int, default=18)
    parser.add_argument("--trials", type=int, default=7)
    parser.add_argument("--replay-worker", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--construction-worker", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.frames < 2 or args.trials < 2:
        parser.error("frames and trials must be >=2")
    if args.replay_worker:
        replay_worker(args.replay_worker, args.frames, args.trials)
        return
    if args.construction_worker:
        construction_worker(args.construction_worker)
        return
    report = {
        "baseline_revision": BASE,
        "python": platform.python_version(),
        "pillow": PIL.__version__,
        "method": "Fresh processes per construction/size. Interleaved replay trials at AA1; no tests or FFmpeg during timing.",
        "construction": [],
        "replay": [],
    }
    for kind in ("linear-card", "radial-card", "cardinal-1080", "linear-1080", "radial-1080", "rounded-1080"):
        row = json.loads(subprocess.check_output([sys.executable, __file__, "--construction-worker", kind], text=True))
        report["construction"].append(row)
        print(json.dumps(row), flush=True)
    for width in (960, 1920):
        row = json.loads(
            subprocess.check_output(
                [
                    sys.executable,
                    __file__,
                    "--replay-worker",
                    str(width),
                    "--frames",
                    str(args.frames),
                    "--trials",
                    str(args.trials),
                ],
                text=True,
            )
        )
        report["replay"].append(row)
        print(json.dumps(row), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
