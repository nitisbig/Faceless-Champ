"""Compare complete installed M1/M2 builds in fresh sequential processes.

Run after correctness suites, with no competing render/test jobs. Both interpreters
must resolve their own installed SDK wheel and the same dependency versions.
Render samples use the frozen workload script supplied by --render-workload.
"""

import argparse
import gc
import hashlib
import json
import platform
import resource
import runpy
import statistics
import subprocess
import time
import tracemalloc
from pathlib import Path


def structural(kind, count):
    import faceless_champ as core

    # M1's first Group.bounds implicitly imports the renderer and Scene. M2's
    # measurement does not. Warm both complete paths before tracing snapshots,
    # otherwise M2 alone pays its lazy Scene/plan imports inside this region.
    started = time.perf_counter()
    warm = core.Scene().add(core.Group(core.Rectangle(width=10, height=10)))
    if hasattr(warm, "_compile"):
        warm._compile()
    first_use_ms = (time.perf_counter() - started) * 1000
    del warm
    started = time.perf_counter()
    if kind == "chain":
        root = core.Rectangle(width=10, height=10)
        for _ in range(count - 1):
            root = core.Group(root)
    elif kind == "wide":
        root = core.Group(*(core.Rectangle(width=10, height=10) for _ in range(count)))
    else:
        raise ValueError(kind)
    authoring_ms = (time.perf_counter() - started) * 1000
    gc.collect()
    tracemalloc.start()
    started = time.perf_counter()
    scene = core.Scene().add(root).wait(1)
    snapshot_ms = (time.perf_counter() - started) * 1000
    snapshot_bytes, snapshot_peak = tracemalloc.get_traced_memory()
    started = time.perf_counter()
    compiled = scene._compile() if hasattr(scene, "_compile") else None
    compile_ms = (time.perf_counter() - started) * 1000 if compiled is not None else None
    retained_bytes, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    retained = set()

    def visit(c):
        if id(c) in retained:
            return
        retained.add(id(c))
        if isinstance(c, core.Group):
            for child in c.children:
                visit(child)

    for entry in scene.entries:
        visit(entry.component)
    return {
        "package": core.__file__,
        "kind": kind,
        "count": count,
        "authored_nodes": len(scene.entries),
        "retained_snapshots": len(retained),
        "first_use_ms": first_use_ms,
        "authoring_ms": authoring_ms,
        "snapshot_ms": snapshot_ms,
        "compile_ms": compile_ms,
        "snapshot_traced_bytes": snapshot_bytes,
        "snapshot_peak_traced_bytes": snapshot_peak,
        "compiled_traced_bytes": retained_bytes,
        "compiled_peak_traced_bytes": peak,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def render(workload, name, aa, frames):
    import faceless_champ as core

    module = runpy.run_path(workload)
    return {
        "package": core.__file__,
        "workload": name,
        "aa": aa,
        **module["trial"](name, 1920, "pillow", aa, frames, certify=True),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-python", type=Path)
    parser.add_argument("--candidate-python", type=Path)
    parser.add_argument("--render-workload", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--worker", nargs="+")
    args = parser.parse_args()
    if args.worker:
        if args.worker[0] == "structural":
            result = structural(args.worker[1], int(args.worker[2]))
        else:
            result = render(args.worker[1], args.worker[2], int(args.worker[3]), int(args.worker[4]))
        print(json.dumps(result))
        return
    if not all((args.baseline_python, args.candidate_python, args.output, args.render_workload)):
        parser.error("Provide both interpreters, --render-workload and --output")
    result = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "render_workload_sha256": hashlib.sha256(args.render_workload.read_bytes()).hexdigest(),
        "frames_per_trial": args.frames,
        "warmup_frames_including_cold": 10,
        "structural_warmup": "one two-node group scene, including candidate compilation, before timed construction/tracing",
        "trials": [],
        "summary": [],
    }
    script = str(Path(__file__).resolve())
    cases = [["structural", "chain", str(n)] for n in (5, 9, 17, 33)]
    cases += [["structural", "wide", str(n)] for n in (100, 1000)]
    cases += [
        ["render", str(args.render_workload.resolve()), name, str(aa), str(args.frames)]
        for name in ("plain", "ui")
        for aa in (1, 2)
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for case in cases:
        pair = {}
        for label, python in (("baseline", args.baseline_python), ("candidate", args.candidate_python)):
            samples = []
            for trial in range(args.trials):
                completed = subprocess.run(
                    [str(python.absolute()), "-I", "-B", script, "--worker", *case],
                    cwd="/tmp",
                    capture_output=True,
                    text=True,
                    check=True,
                )
                sample = json.loads(completed.stdout)
                samples.append(sample)
                result["trials"].append({"label": label, "trial": trial, "case": case, "result": sample})
                args.output.write_text(json.dumps(result, indent=2) + "\n")
            pair[label] = samples
        if case[0] == "render":
            summary = {"case": case, "baseline": {}, "candidate": {}}
            for label, samples in pair.items():
                for metric in ("median_ms", "p95_ms", "process_peak_rss_kib", "authoring_ms", "cold_frame_ms"):
                    summary[label][metric] = statistics.median(s[metric] for s in samples)
            summary["gate"] = all(
                summary["candidate"][m] <= 1.1 * summary["baseline"][m] for m in ("median_ms", "p95_ms")
            )
        else:
            summary = {
                "case": case,
                **{
                    label: {
                        metric: statistics.median(s[metric] for s in samples)
                        for metric in ("retained_snapshots", "snapshot_ms", "compiled_traced_bytes", "peak_rss_kib")
                    }
                    for label, samples in pair.items()
                },
            }
        result["summary"].append(summary)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
