"""Process-isolated geometry benchmarks against the identical prepared mesh scene.

Example: python scripts/benchmark_geometry.py --case engine --backend pillow
Each trial compares fresh native-preparation and mesh-only replay interpreters.
The trusted local pickle is temporary benchmark IPC, never an asset format.
"""

import argparse
import json
import pickle
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CASES = ("bracket", "gears", "instances", "mesh", "engine", "blueprint")


def workload(case, width):
    from faceless_champ import Canvas, Scene
    from faceless_champ.arch import ArchChamp, ArchScript, blueprint_from_cad, mesh_from_cad, parts_from_cad

    height = round(width * 9 / 16)
    stats = {}
    script = ArchScript().orbit(30, duration=3)
    if case == "mesh":
        import trimesh

        from faceless_champ.arch import inspect_mesh, simplify_mesh

        # Trimesh doubles longitude subdivisions internally: this is 996k faces.
        source = trimesh.creation.uv_sphere(count=(500, 500))
        stats["source_faces"] = len(source.faces)
        start = time.perf_counter()
        stats["inspection"] = inspect_mesh(source)
        stats["inspection_seconds"] = time.perf_counter() - start
        start = time.perf_counter()
        parts = simplify_mesh(source, 250_000, drop_fields=True)
        stats["processing_seconds"] = time.perf_counter() - start
        stats["result_volume"] = inspect_mesh(parts)["volume"]
    else:
        from copy import copy

        import build123d as bd

        from faceless_champ.arch.cad_models import gear_pair, inline_engine

        if case == "bracket":
            shape = bd.fillet(bd.Box(50, 30, 15).edges().filter_by(bd.Axis.Z), 2)
            shape -= bd.Cylinder(4, 30)
            parts = mesh_from_cad(shape)
        elif case == "gears":
            parts = parts_from_cad(gear_pair())
            script = ArchScript().gear_pair("driver", "driven", degrees=360, duration=3)
        elif case == "instances":
            solid = bd.Box(2, 3, 4) - bd.Cylinder(0.4, 10)
            children = []
            for i in range(100):
                child = copy(solid)
                child.label, child.location = f"part-{i}", bd.Location((i % 10 * 4, i // 10 * 5, 0))
                children.append(child)
            parts = parts_from_cad(bd.Compound(children=children))
            stats["unique_meshes"] = len({id(p.mesh) for p in parts})
        elif case == "engine":
            parts = parts_from_cad(inline_engine())
            script = ArchScript()
            for i in range(4):
                script.slider_crank(
                    [f"cylinder-{i + 1}/{p}" for p in ("crank", "rod", "piston")], phase=180 * (i % 2), at=0, duration=3
                )
            script.section("block", (45, 0, 36), at=0, duration=3, cap=True)
        else:
            group = blueprint_from_cad(bd.Box(50, 30, 15) - bd.Cylinder(4, 30), width=width, height=height)
            return Scene(Canvas(width, height, "#080f1c")).add(group).wait(3), stats
    view = ArchChamp(parts, script, units="mm", width=width, height=height, position=(width / 2, height / 2))
    stats["parts"] = len(view.parts)
    stats["triangles"] = sum(p.mesh._dataset.n_cells for p in view.parts)
    return Scene(Canvas(width, height, "#080f1c")).add(view).wait(3), stats


def trial(args):
    from faceless_champ import create_renderer, rendering_identity

    start = time.perf_counter()
    if args.replay:
        with args.scene.open("rb") as stream:
            scene = pickle.load(stream)
        stats = {}
    else:
        scene, stats = workload(args.case, args.width)
        with args.scene.open("wb") as stream:
            pickle.dump(scene, stream, protocol=5)
    prepared = time.perf_counter() - start
    size = (args.width, round(args.width * 9 / 16))
    with create_renderer(args.backend, antialias=args.antialias) as renderer:
        start = time.perf_counter()
        renderer.frame(scene, 0, size)
        cold = time.perf_counter() - start
        renderer.frame(scene, 0.01, size)
        samples = []
        for i in range(args.frames):
            start = time.perf_counter()
            renderer.frame(scene, 0.03 + (i + 1) * 2.9 / (args.frames + 1), size)
            samples.append(time.perf_counter() - start)
        identity = rendering_identity(args.backend, renderer=renderer)
    samples.sort()
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss + resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    return {
        "preparation_seconds": prepared,
        "cold_frame_seconds": cold,
        "median_frame_seconds": statistics.median(samples),
        "p95_frame_seconds": samples[min(len(samples) - 1, int(len(samples) * 0.95))],
        "aggregate_peak_rss_mib_upper_bound": peak / 1024,
        "snapshot_bytes": args.scene.stat().st_size,
        "identity": identity,
        **stats,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, default="bracket")
    parser.add_argument("--backend", choices=["pillow", "skia", "moderngl"], default="pillow")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--antialias", type=int, default=1)
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--replay", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--scene", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if min(args.frames, args.trials, args.width) < 1:
        parser.error("frames, trials and width must be positive")
    if args.worker:
        print(json.dumps(trial(args)))
        return
    rows = []
    with tempfile.TemporaryDirectory(prefix="fc-geometry-benchmark-") as directory:
        for trial_index in range(args.trials):
            command = [
                sys.executable,
                __file__,
                "--worker",
                "--case",
                args.case,
                "--backend",
                args.backend,
                "--width",
                str(args.width),
                "--antialias",
                str(args.antialias),
                "--frames",
                str(args.frames),
                "--scene",
                str(Path(directory) / "scene.pickle"),
            ]
            values = []
            for replay in (False, True):
                print(
                    f"{args.case}: trial {trial_index + 1}/{args.trials}, {'mesh replay' if replay else 'preparation'}",
                    file=sys.stderr,
                    flush=True,
                )
                run = subprocess.run(
                    command + (["--replay"] if replay else []), capture_output=True, text=True, check=True, timeout=600
                )
                values.append(json.loads(run.stdout))
            rows.append({"prepared": values[0], "mesh_only": values[1]})
    ratio = statistics.median(row["prepared"]["median_frame_seconds"] for row in rows) / statistics.median(
        row["mesh_only"]["median_frame_seconds"] for row in rows
    )
    memory = max(
        row["prepared"]["aggregate_peak_rss_mib_upper_bound"] - row["mesh_only"]["aggregate_peak_rss_mib_upper_bound"]
        for row in rows
    )
    result = {
        "case": args.case,
        "backend": args.backend,
        "width": args.width,
        "antialias": args.antialias,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "trials": rows,
        "warm_frame_ratio": ratio,
        "incremental_peak_mib": memory,
        "targets": {"warm_within_10_percent": ratio <= 1.1, "incremental_below_1536_mib": memory <= 1536},
    }
    encoded = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n")
    print(encoded)


if __name__ == "__main__":
    main()
