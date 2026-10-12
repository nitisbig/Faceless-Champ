"""Repeatable FlowChamp raster benchmark; run with the selected installed/source package."""

import argparse
import json
import resource
import time
import tracemalloc

from faceless_champ import FlowChamp, FlowEdge, FlowGraph, FlowNode, FlowScript
from faceless_champ.flow.examples import recipe


def benchmark(frames=45, factor=0.8):
    results = {}
    for family in ("system", "dense"):
        if family == "system":
            graph, script = recipe("system")
        else:
            graph = FlowGraph(
                tuple(
                    FlowNode(f"n{i}", f"Service {i}", position=(140 + i % 4 * 280, 120 + i // 4 * 200), size=(200, 100))
                    for i in range(12)
                ),
                tuple(FlowEdge(f"e{i}", f"n{i}", f"n{i + 1}", route="straight") for i in range(11)),
                layout="manual",
            )
            script = FlowScript().signal("e0", at=0, duration=10)
        clip = FlowChamp(graph, script, width=1200, height=675)
        for t in (2, 2.1):
            clip.frame_image(t, factor)
        tracemalloc.start()
        started = time.perf_counter()
        for i in range(frames):
            clip.frame_image(2 + i / 30, factor)
        elapsed = time.perf_counter() - started
        retained, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        results[family] = {
            "frames": frames,
            "seconds": elapsed,
            "python_peak_bytes": peak,
            "retained_python_bytes": retained,
        }
    # Linux reports KiB. Unlike tracemalloc, RSS includes native Pillow allocations.
    results["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    results["note"] = "Linux RSS is whole-process high-water memory; tracemalloc excludes native Pillow buffers."
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=45)
    parser.add_argument("--factor", type=float, default=0.8)
    args = parser.parse_args()
    if args.frames <= 0 or not 0 < args.factor <= 4:
        parser.error("frames must be positive and factor must be in (0,4]")
    print(json.dumps(benchmark(args.frames, args.factor), indent=2))


if __name__ == "__main__":
    main()
