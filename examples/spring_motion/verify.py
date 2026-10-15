"""Verify identical spring states/pixels after 24/30/60-fps timeline seeks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

from faceless_champ import (
    Animation,
    Canvas,
    Group,
    PillowRenderer,
    Rectangle,
    Repeat,
    Scene,
    Spring,
    Stagger,
    Succession,
    Text,
    smooth,
)


def release_scene(spring):
    scene = Scene(Canvas(320, 180, "#101722"))
    card = Group(
        Rectangle(width=54, height=36, position=(75, 65), fill="#58dfc1", stroke=None),
        Text("A", position=(75, 65), font_size=17, color="#101722"),
        scale=0.8,
    )
    marker = Rectangle(width=24, height=18, position=(75, 140), fill="#82a8ff", stroke=None)
    scene.add(card, marker)
    with scene.at(0.125):
        scene.play(
            Stagger(
                Repeat(
                    Animation(card, {"position": (225, 65), "scale": 1.1, "rotation": 7}, rate_func=spring),
                    cycles=2,
                    ping_pong=True,
                    duration=0.375,
                ),
                Succession(
                    Animation(marker, {"position": (240, 140)}, rate_func=spring),
                    Animation(marker, {"position": (90, 140)}, rate_func=spring),
                    duration=0.25,
                ),
                lag=0.125,
                delay=0.125,
            ),
            run_time=1.25,
        )
    with scene.at(0.125):
        scene.play(card.animate.opacity_to(0.8), run_time=0.5, rate_func=smooth)
    scene.wait_until(1.75)
    return scene, (card, marker)


def verify_frame_rates(spring, *, frame_cache_mb=64):
    # Multiples of 1/6 lie on all three frame grids. Extra probes include track
    # boundaries and early overshoot times that need not lie on an export grid.
    shared_times = tuple(float(Fraction(i, 6)) for i in range(11))
    probes = tuple(sorted({*shared_times, 0.125, 0.25, 0.3, 0.625, 0.875, 1.375}))
    reference, _ = release_scene(spring)
    expected = {}
    with PillowRenderer(1, frame_cache_mb=0) as renderer:
        for time in probes:
            states = [entry.state_at(time) for entry in reference.entries]
            pixels = renderer.frame(reference, time, (320, 180)).tobytes()
            expected[time] = (states, hashlib.sha256(pixels).hexdigest())
    results = []
    for fps in (24, 30, 60):
        scene, sources = release_scene(spring)
        original = deepcopy(([source.state() for source in sources], [entry.initial for entry in scene.entries]))
        frames = list(range(math.ceil(scene.duration * fps)))
        order = "forward"
        if fps == 30:
            frames.reverse()
            order = "reverse"
        elif fps == 60:
            random.Random(6401).shuffle(frames)
            order = "shuffled"
        with PillowRenderer(1, frame_cache_mb=frame_cache_mb) as renderer:
            for index in frames:
                renderer.frame(scene, index / fps, (320, 180))
            # Seek again after the entire, differently ordered FPS workload.
            for time in reversed(probes):
                states = [entry.state_at(time) for entry in scene.entries]
                pixels = renderer.frame(scene, time, (320, 180)).tobytes()
                digest = hashlib.sha256(pixels).hexdigest()
                if states != expected[time][0] or digest != expected[time][1]:
                    raise AssertionError(f"FPS-dependent state/frame at {time}s after {fps}-fps {order} seeks")
        if original != ([source.state() for source in sources], [entry.initial for entry in scene.entries]):
            raise AssertionError("Sampling mutated an authoring object or scene snapshot")
        results.append({"fps": fps, "frames_sampled": len(frames), "order": order, "matching_probes": len(probes)})
    return {
        "spring": {"stiffness": spring.stiffness, "damping": spring.damping, "mass": spring.mass},
        "frame_cache_mb": frame_cache_mb,
        "method": "direct shared timeline sampling, not encoded FPS exports",
        "shared_grid_times": shared_times,
        "probe_times": probes,
        "reference_frame_sha256": {str(time): digest for time, (_, digest) in expected.items()},
        "states_and_pixels_equal": True,
        "sources_unchanged": True,
        "runs": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    results = {
        "cases": [
            verify_frame_rates(Spring(100, damping, 1), frame_cache_mb=cache)
            for damping in (10, 20, 25)
            for cache in (0, 64)
        ]
    }
    payload = json.dumps(results, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
