"""Command-line authoring entry point."""

import argparse
import runpy
import sys
from pathlib import Path

from .export import render
from .timeline import Renderable


def _check(args) -> int:
    import json
    from dataclasses import asdict

    from .delivery import delivery_report

    try:
        report = delivery_report(args.file, loudness=args.loudness, true_peak=args.true_peak)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"faceless-champ: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(asdict(report) | {"path": str(report.path), "ok": report.ok}, indent=2))
    else:
        print(report)
    return 0 if report.ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="faceless-champ")
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("render", help="Render a Scene class, composition, or factory in a Python file")
    command.add_argument("file", type=Path)
    command.add_argument("name")
    command.add_argument("-o", "--output", type=Path, required=True)
    command.add_argument("-q", "--quality", default="qh")
    command.add_argument("--width", type=int)
    command.add_argument("--height", type=int)
    command.add_argument("--fps", type=float, default=30)
    command.add_argument("--crf", type=int, default=18)
    command.add_argument("--preset", default="medium")
    command.add_argument("--antialias", type=int, default=2)
    command.add_argument("--backend", choices=("pillow", "skia", "moderngl", "auto"), default="pillow")
    command.add_argument("--codec", choices=("h264", "hevc10", "prores"), default="h264")
    command.add_argument("--lut", type=Path, help="apply a .cube color grade")
    command.add_argument("--loudness", type=float, help="normalize audio to this integrated LUFS (YouTube: -14)")
    command.add_argument("--workers", type=int, default=1, help="render chunks in N processes (pillow/skia)")
    command.add_argument("--chunk-frames", type=int, default=300)
    command.add_argument("--chunk-dir", type=Path, help="keep chunks here so an interrupted render resumes")
    command.add_argument("--overwrite", action="store_true")
    sub.add_parser("plugins", help="List discovered plugins, their status and capabilities")
    check = sub.add_parser(
        "check", help="Pre-upload checks: loudness, true peak, color tags, black/frozen/silent spans"
    )
    check.add_argument("file", type=Path)
    check.add_argument("--loudness", type=float, default=-14.0, help="integrated LUFS target (default -14)")
    check.add_argument("--true-peak", type=float, default=-1.0, help="dBTP ceiling (default -1)")
    check.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.command == "check":
        return _check(args)
    if args.command == "plugins":
        import json

        from . import plugins

        print(json.dumps({"plugins": plugins.plugin_report(), "capabilities": plugins.capabilities()}, indent=2))
        return 0
    try:
        path = args.file.resolve()
        sys.path.insert(0, str(path.parent))
        try:
            namespace = runpy.run_path(str(path))
        finally:
            sys.path.pop(0)
        if args.name not in namespace:
            raise ValueError(f"No scene or factory named {args.name!r} in {path}")
        node = namespace[args.name]
        if callable(node):
            node = node()
        if not isinstance(node, Renderable):
            raise TypeError(f"{args.name} must be a Scene, composition, or factory returning one")
        options = vars(args).copy()
        for key in ("command", "file", "name", "output"):
            options.pop(key)
        chunk_dir = options.pop("chunk_dir")
        print(render(node, args.output, chunk_dir=chunk_dir, **options))
        return 0
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        print(f"faceless-champ: {exc}", file=sys.stderr)
        return 1
