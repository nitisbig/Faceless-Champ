"""Repeatable CPU spring benchmark; timing and memory passes are separate."""

from __future__ import annotations

import argparse
import json
import platform
import resource
import statistics
import subprocess
import sys
import time
import tracemalloc
from contextlib import ExitStack
from pathlib import Path

from faceless_champ import Canvas, PillowRenderer, Rectangle, Scene, Spring, smooth

SPRING = Spring(100, 10, 1)
MODES = ("static", "smooth", "spring", "spring_lookup")
SIZE = (960, 540)


class SampledSpring:
    """Benchmark control: identical sampled curve, with physics computed up front."""

    def __init__(self, frames):
        self.values = {
            (3 * i / count) / 3: SPRING((3 * i / count) / 3) for count in (15, 30, frames) for i in range(count)
        }

    def __call__(self, progress):
        return self.values[progress]


def build_scene(mode, frames=90):
    scene = Scene(Canvas(*SIZE, "#101722"))
    cards = [
        Rectangle(
            width=64,
            height=40,
            position=(110 + 300 * (i % 3), 90 + 110 * (i // 3)),
            fill="#58dfc1",
            stroke=None,
            stroke_width=0,
        )
        for i in range(12)
    ]
    scene.add(*cards)
    if mode != "static":
        scene.play(
            *(card.animate.move_to(card.position[0] + 80, card.position[1] + 8) for card in cards),
            run_time=3,
            rate_func=SampledSpring(frames) if mode == "spring_lookup" else SPRING if mode == "spring" else smooth,
        )
    else:
        scene.wait(3)
    return scene


def render_frames(scene, renderer, mode, frames):
    for i in range(frames):
        renderer.frame(scene, 0.5 if mode == "static" else 3 * i / frames, SIZE)


def summarize(seconds, operations):
    per_operation = [value / operations for value in seconds]
    return {
        "trials_seconds": seconds,
        "operations_per_trial": operations,
        "median_us_per_operation": 1e6 * statistics.median(per_operation),
        "min_us_per_operation": 1e6 * min(per_operation),
        "max_us_per_operation": 1e6 * max(per_operation),
        "stdev_us_per_operation": 1e6 * statistics.stdev(per_operation),
    }


def timed_trials(action, count, repeats):
    for _ in range(10):
        action()
    values = []
    for _ in range(repeats):
        started = time.perf_counter()
        for _ in range(count):
            action()
        values.append(time.perf_counter() - started)
    return summarize(values, count)


def memory_pass(mode, frames):
    scene = build_scene(mode, frames)
    with PillowRenderer(1) as renderer:
        render_frames(scene, renderer, mode, 15)
        tracemalloc.start()
        render_frames(scene, renderer, mode, frames)
        retained, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return {
        "python_retained_bytes": retained,
        "python_peak_bytes": peak,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def benchmark(frames=90, repeats=7):
    # No tracemalloc during timings: its per-allocation cost distorts comparisons.
    constructors = {
        label: timed_trials(lambda c=damping: Spring(100, c, 1), 1000, repeats)
        for label, damping in (("under", 10), ("critical", 20), ("over", 25))
    }
    authoring = {mode: timed_trials(lambda m=mode: build_scene(m), 100, repeats) for mode in ("smooth", "spring")}
    inputs = tuple(i / 50000 for i in range(50000))
    evaluation = {}
    for label, easing in (("smooth", smooth), ("spring", SPRING)):
        sum(map(easing, inputs))
        times = []
        for _ in range(repeats):
            started = time.perf_counter()
            sum(map(easing, inputs))
            times.append(time.perf_counter() - started)
        evaluation[label] = summarize(times, len(inputs))

    timings = {mode: [] for mode in MODES}
    orders = []
    with ExitStack() as stack:
        scenes = {mode: build_scene(mode, frames) for mode in MODES}
        for i in range(frames):
            timestamp = 3 * i / frames
            live = [entry.state_at(timestamp) for entry in scenes["spring"].entries]
            cached = [entry.state_at(timestamp) for entry in scenes["spring_lookup"].entries]
            if live != cached:
                raise AssertionError("The precomputed spring control changed the sampled trajectory")
        renderers = {mode: stack.enter_context(PillowRenderer(1)) for mode in MODES}
        for mode in MODES:
            render_frames(scenes[mode], renderers[mode], mode, 30)
        for trial in range(repeats):
            order = MODES[trial % len(MODES) :] + MODES[: trial % len(MODES)]
            orders.append(order)
            for mode in order:
                started = time.perf_counter()
                render_frames(scenes[mode], renderers[mode], mode, frames)
                timings[mode].append(time.perf_counter() - started)
    rendering = {mode: summarize(values, frames) for mode, values in timings.items()}
    # Fresh subprocesses isolate whole-process native/Pillow high-water memory.
    memory = {}
    for mode in MODES:
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--memory-worker", mode, "--frames", str(frames)],
            capture_output=True,
            text=True,
            check=True,
        )
        memory[mode] = json.loads(completed.stdout)
    baseline = rendering["smooth"]["median_us_per_operation"]
    delta = rendering["spring"]["median_us_per_operation"] - baseline
    lookup_delta = (
        rendering["spring"]["median_us_per_operation"] - rendering["spring_lookup"]["median_us_per_operation"]
    )
    return {
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "workload": {
            "size": SIZE,
            "antialias": 1,
            "components": 12,
            "property": "position",
            "frames_per_trial": frames,
            "trials": repeats,
            "warmup_frames_per_mode": 30,
            "trial_order": orders,
            "static_time_seconds": 0.5,
            "moving_source_span_seconds": 3,
            "spring": {"stiffness": 100, "damping": 10, "mass": 1},
        },
        "construction": constructors,
        "authoring": authoring,
        "evaluation": evaluation,
        "rendering": rendering,
        "isolated_memory": memory,
        "spring_minus_smooth_us_per_frame": delta,
        "spring_overhead_vs_smooth_percent": 100 * delta / baseline,
        "spring_minus_identical_lookup_us_per_frame": lookup_delta,
        "lookup_control_states_equal": True,
        "paired_spring_minus_lookup_us_per_frame": [
            1e6 * (live - cached) / frames for live, cached in zip(timings["spring"], timings["spring_lookup"])
        ],
        "notes": [
            "Local CPU result; timings are warmed, interleaved, and exclude FFmpeg encoding.",
            "Rendering uses identical sprites, dimensions, track counts, and translation distances; curve paths differ.",
            "RSS is Linux whole-process high-water KiB, including imports/warmup; it is not incremental spring memory.",
            "Tracemalloc memory passes exclude native Pillow buffers and are separate from performance timings.",
            "Static rendering deliberately exercises repeated-frame cache reuse; moving modes evaluate changing tracks.",
            "spring_lookup uses exactly the live spring's sampled coordinates with precomputed easing values.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=90)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--memory-worker", choices=MODES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.frames < 1 or args.repeats < 2:
        parser.error("frames must be positive and repeats must be at least two")
    if args.memory_worker:
        result = memory_pass(args.memory_worker, args.frames)
    else:
        result = benchmark(args.frames, args.repeats)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
