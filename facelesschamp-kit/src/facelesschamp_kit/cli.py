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
from .themes import THEMES

CATALOG = {
    "blocks": [
        "EffectBlock",
        "ProceduralBackdrop",
        "ParticleBackdrop",
        "ArchCanvas",
        "CodeEditor",
        "CodingPlayground",
        "WebWalkthrough",
        "WebElement",
        "ManimCanvas",
        "Heading",
        "TextPanel",
        "MetricCard",
        "ImageCard",
        "Comparison",
        "StepList",
        "FlowDiagram",
        "FlowCanvas",
        "WhiteboardDrawing",
        "OSWalkthrough",
        "FinderWindow",
        "SettingsWindow",
        "TitleCard",
        "BigStat",
        "QuoteCard",
        "StepsCard",
        "CompareCard",
        "EndCard",
    ],
    "themes": list(THEMES),
    "templates": [
        "silent",
        "explainer-short",
        "narrated-short",
        "whiteboard-basic",
        "archchamp",
        "flowchamp",
        "os-ui",
        "coding-web",
        "coding-concept",
        "coding-backend",
    ],
}


def doctor(root=".", *, gpu=False):
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
    root = root.parent if root.is_file() else root
    for directory in (root / "output", root / ".fc-kit"):
        parent = directory
        while not parent.exists():
            parent = parent.parent
        checks[str(directory)] = os.access(parent, os.W_OK)
    optional = {
        name: package_version(distribution) != "source"
        for name, distribution in (
            ("pyvista", "pyvista"),
            ("vtk", "vtk"),
            ("maps", "numpy"),
            ("equations", "matplotlib"),
            ("coding", "Pygments"),
            ("web", "playwright"),
        )
    }
    from .dependencies import dependencies

    dependency_rows = dependencies(root)
    checks["project_dependencies"] = all(r["status"] not in {"missing", "incompatible"} for r in dependency_rows)
    result = {
        "dependencies": dependency_rows,
        "ok": all(checks.values()),
        "checks": checks,
        "optional": optional,
        "guidance": {"3d": "Install facelesschamp-kit[3d] (or facelesschamp-agent[3d]) for ArchChamp/PyVista."},
        "versions": {name: package_version(name) for name in ("faceless-champ", "facelesschamp-kit", "pyvista", "vtk")},
    }
    from faceless_champ import renderer_capabilities

    result["gpu"] = renderer_capabilities("moderngl", probe=gpu)
    return result


def shot_main(argv):
    """fc-kit shot TEMPLATE CONTENT [--theme T] [--duration S] [--portrait] [runner flags].

    CONTENT is a JSON file or an inline JSON object. Runner flags are those of
    faceless_champ.run: --frame T, --preview [S], --storyboard [N], --audit, --output.
    """
    from faceless_champ import run

    from .shots import SHOTS, shot_fields, shot_video

    parser = argparse.ArgumentParser(prog="fc-kit shot", description=shot_main.__doc__)
    parser.add_argument("template", nargs="?", choices=list(SHOTS))
    parser.add_argument("content", nargs="?", help="JSON file or inline JSON object")
    parser.add_argument("--list", action="store_true", help="print templates and their fields")
    parser.add_argument("--theme", default="midnight", choices=list(THEMES))
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--portrait", action="store_true", help="1080x1920 instead of 1920x1080")
    args, rest = parser.parse_known_args(argv)
    if args.list or not args.template:
        print(json.dumps({name: shot_fields(name) for name in SHOTS}, indent=2))
        return 0
    if not args.content:
        print(f"fc-kit shot: {args.template} needs content with fields {shot_fields(args.template)}", file=sys.stderr)
        return 2
    try:
        text = args.content
        content = json.loads(Path(text).read_text() if not text.lstrip().startswith("{") else text)
        size = (1080, 1920) if args.portrait else (1920, 1080)
        video = shot_video(args.template, content, theme=args.theme, duration=args.duration, size=size)
    except (KitError, ValueError, OSError) as exc:
        error = exc.as_dict() if isinstance(exc, KitError) else {"code": "SHOT", "message": str(exc)}
        print(json.dumps({"ok": False, "error": error}))
        return 1
    return run(video.composition, argv=rest or ["--frame", str(args.duration * 0.6)], name=f"shot-{args.template}")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "shot":
        return shot_main(argv[1:])
    parser = argparse.ArgumentParser(prog="fc-kit")
    parser.add_argument("--project", default=".", help="Project directory or facelesschamp.toml")
    parser.add_argument("--json", action="store_true", help="Machine-readable results and errors")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("destination")
    init.add_argument("--template", default="silent")
    sub.add_parser("doctor").add_argument("--gpu", action="store_true", help="Explicitly probe headless OpenGL")
    listing = sub.add_parser("list")
    listing.add_argument("kind", choices=["videos", *CATALOG])
    for name in ("prepare", "validate", "inspect", "frame", "storyboard", "preview", "render"):
        command = sub.add_parser(name)
        command.add_argument("video", nargs="?", default="main")
        command.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
        if name == "prepare":
            command.add_argument("--refresh", action="store_true")
        elif name in {"validate", "inspect"}:
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
            result = doctor(args.project, gpu=args.gpu)
        elif args.command == "list" and args.kind != "videos":
            result = CATALOG[args.kind]
        else:
            project = Project(args.project)
            if args.command == "list":
                result = list(project.config["videos"])
            elif args.command == "prepare":
                result = project.prepare(args.video, refresh=args.refresh)
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
