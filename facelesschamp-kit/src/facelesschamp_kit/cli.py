"""Thin argparse interface to the public project services."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .diagnostics import KitError
from .project import Project, package_version
from .scaffold import init_project

CATALOG = {
    "blocks": [
        "Heading",
        "TextPanel",
        "MetricCard",
        "ImageCard",
        "Comparison",
        "StepList",
        "FlowDiagram",
        "WhiteboardDrawing",
    ],
    "themes": ["midnight", "light", "whiteboard"],
    "templates": ["silent", "explainer-short", "narrated-short", "whiteboard-basic"],
}


def doctor(root="."):
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    encoder = False
    if ffmpeg:
        result = subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True, text=True, check=False)
        encoder = result.returncode == 0 and "libx264" in result.stdout
    checks = {
        "python_312": sys.version_info >= (3, 12),
        "ffmpeg": bool(ffmpeg),
        "ffprobe": bool(ffprobe),
        "libx264": encoder,
    }
    root = Path(root).resolve()
    for directory in (root / "output", root / ".fc-kit"):
        parent = directory
        while not parent.exists():
            parent = parent.parent
        checks[str(directory)] = os.access(parent, os.W_OK)
    import importlib.util

    optional = {
        name: importlib.util.find_spec(module) is not None
        for name, module in (("maps", "numpy"), ("equations", "matplotlib"))
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "optional": optional,
        "versions": {name: package_version(name) for name in ("faceless-champ", "facelesschamp-kit")},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(prog="fc-kit")
    parser.add_argument("--project", default=".", help="Project directory or facelesschamp.toml")
    parser.add_argument("--json", action="store_true", help="Machine-readable results and errors")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("destination")
    init.add_argument("--template", default="silent")
    sub.add_parser("doctor")
    listing = sub.add_parser("list")
    listing.add_argument("kind", choices=["videos", *CATALOG])
    for name in ("validate", "inspect", "frame", "storyboard", "preview", "render"):
        command = sub.add_parser(name)
        command.add_argument("video", nargs="?", default="main")
        command.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
        if name in {"validate", "inspect"}:
            command.add_argument("--strict-assets", action="store_true")
        else:
            command.add_argument("-o", "--output", type=Path, required=True)
            command.add_argument("--overwrite", action="store_true")
        if name == "frame":
            command.add_argument("--time", type=float, required=True)
        if name in {"preview", "render"}:
            command.add_argument("--profile")
            command.add_argument("--allow-placeholders", action="store_true")
        if name == "preview":
            command.add_argument("--segment")
            command.add_argument("--start", type=float)
            command.add_argument("--end", type=float)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = str(init_project(args.destination, args.template))
        elif args.command == "doctor":
            result = doctor(args.project)
        elif args.command == "list" and args.kind != "videos":
            result = CATALOG[args.kind]
        else:
            project = Project(args.project)
            if args.command == "list":
                result = list(project.config["videos"])
            elif args.command in {"validate", "inspect"}:
                result = project.validate(args.video, strict_assets=args.strict_assets)
            elif args.command == "frame":
                result = str(project.frame(args.video, args.time, args.output, overwrite=args.overwrite))
            elif args.command == "storyboard":
                result = str(project.storyboard(args.video, args.output, overwrite=args.overwrite))
            else:
                result = str(
                    project.export(
                        args.video,
                        args.output,
                        preview=args.command == "preview",
                        profile=args.profile,
                        segment=getattr(args, "segment", None),
                        start=getattr(args, "start", None),
                        end=getattr(args, "end", None),
                        overwrite=args.overwrite,
                        allow_placeholders=args.allow_placeholders,
                    )
                )
        print(json.dumps(result, indent=2) if args.json or isinstance(result, (dict, list)) else result)
        return 0 if not isinstance(result, dict) or result.get("ok", True) else 1
    except (KitError, ValueError, TypeError, OSError, RuntimeError) as exc:
        error = exc.as_dict() if isinstance(exc, KitError) else {"code": "RUNTIME", "message": str(exc)}
        print(json.dumps({"error": error}) if args.json else f"fc-kit: {error}", file=sys.stderr)
        return 1
