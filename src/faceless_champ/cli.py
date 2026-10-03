"""Command-line authoring entry point."""

import argparse
import runpy
import sys
from pathlib import Path

from .export import render
from .timeline import Renderable


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
    command.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
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
        print(render(node, args.output, **options))
        return 0
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        print(f"faceless-champ: {exc}", file=sys.stderr)
        return 1
