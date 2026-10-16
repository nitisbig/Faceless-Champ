"""JSON-capable CLI over the public production services."""

import argparse
import json
import shutil
import sys
from dataclasses import asdict
from importlib.resources import as_file, files
from pathlib import Path

from facelesschamp_kit.cli import doctor
from facelesschamp_kit.diagnostics import KitError
from facelesschamp_kit.recipes import recipe_specs
from pydantic import ValidationError

from .context import read_project_context
from .errors import AgentError
from .models import SCHEMAS
from .planning import plan_project
from .project import AgentProject, init_project
from .registry import CapabilityRegistry


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise AgentError("ARGUMENT", message, suggested_fix="Use fc-agent --help or COMMAND --help")


def export_skill(destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise AgentError("DESTINATION", "Skill destination already exists")
    with as_file(files("facelesschamp_agent").joinpath("resources/skill")) as source:
        shutil.copytree(source, destination)
    return {"path": str(destination), "entrypoint": str(destination / "SKILL.md")}


def main(argv=None):
    parser = Parser(prog="fc-agent")
    parser.add_argument("--project", default=".")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    commands = {}
    for name in (
        "init",
        "doctor",
        "status",
        "capabilities",
        "describe",
        "recipes",
        "schema",
        "validate",
        "prepare",
        "frame",
        "storyboard",
        "preview",
        "review",
        "render",
        "verify",
        "skill",
        "context",
        "plan",
        "audit-layout",
        "entrypoint",
    ):
        command = sub.add_parser(name)
        command.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
        command.add_argument("--project", default=argparse.SUPPRESS)
        commands[name] = command
    commands["init"].add_argument("destination")
    commands["capabilities"].add_argument("query", nargs="?", default="")
    commands["capabilities"].add_argument("--limit", type=int)
    commands["capabilities"].add_argument("--compact", action="store_true")
    commands["capabilities"].add_argument("--recommend", action="store_true")
    commands["capabilities"].add_argument("--kind")
    commands["context"].add_argument("paths", nargs="*")
    commands["context"].add_argument("--max-chars", type=int, default=24000)
    commands["audit-layout"].add_argument("--full", action="store_true", help="Include every geometry sample time")
    commands["plan"].add_argument("--prompt", required=True)
    commands["plan"].add_argument("--instructions", action="append", default=[])
    commands["plan"].add_argument("--instructions-file", type=Path)
    commands["plan"].add_argument("--design", type=Path)
    commands["plan"].add_argument("--format", choices=("landscape", "shorts"))
    commands["plan"].add_argument("--duration", type=float)
    commands["plan"].add_argument("--beat-seconds", type=float, default=7.0)
    commands["plan"].add_argument("--candidates", type=int, default=4)
    commands["plan"].add_argument("--input", action="append", dest="inputs")
    commands["plan"].add_argument("--max-chars", type=int, default=24000)
    commands["describe"].add_argument("name")
    commands["schema"].add_argument("name", choices=sorted(SCHEMAS), nargs="?", default="VideoPlan")
    commands["frame"].add_argument("--time", type=float, required=True)
    commands["review"].add_argument("file", type=Path)
    commands["skill"].add_argument("--output", type=Path, required=True)
    for name in ("frame", "storyboard", "preview", "render", "verify"):
        commands[name].add_argument("-o", "--output", type=Path)
    commands["preview"].add_argument("--start", type=float)
    commands["preview"].add_argument("--end", type=float)
    commands["preview"].add_argument("--scene")
    for name in ("preview", "render"):
        commands[name].add_argument("--fps", type=float)
        commands[name].add_argument("--quality", choices=("low", "high", "4k"))
    try:
        args = parser.parse_args(argv)
        command = args.command
        if command == "init":
            result = {"path": str(init_project(args.destination))}
        elif command == "doctor":
            from . import __version__

            result = doctor(args.project)
            result["agent"] = __version__
            result["registry"] = CapabilityRegistry().check()
        elif command == "capabilities":
            registry = CapabilityRegistry()
            if args.recommend:
                result = registry.recommend(
                    args.query, limit=args.limit if args.limit is not None else 5, kind=args.kind
                )
            else:
                result = registry.search(args.query, limit=args.limit, compact=args.compact, kind=args.kind)
        elif command == "context":
            result = read_project_context(args.project, paths=args.paths or None, max_chars=args.max_chars)
        elif command == "plan":
            instructions = list(args.instructions)
            if args.instructions_file:
                instructions.append(args.instructions_file.read_text(encoding="utf-8"))
            result = plan_project(
                args.project,
                prompt=args.prompt,
                instructions=instructions,
                design=json.loads(args.design.read_text(encoding="utf-8")) if args.design else None,
                format=args.format,
                duration=args.duration,
                target_beat_seconds=args.beat_seconds,
                candidate_limit=args.candidates,
                paths=args.inputs,
                max_chars=args.max_chars,
            )
        elif command == "describe":
            result = CapabilityRegistry().describe(args.name)
        elif command == "recipes":
            result = [asdict(spec) for spec in recipe_specs()]
        elif command == "schema":
            result = SCHEMAS[args.name].model_json_schema()
        elif command == "skill":
            result = export_skill(args.output)
        else:
            project = AgentProject(args.project)
            if command == "frame":
                result = project.frame(args.time, args.output)
            elif command == "preview":
                result = project.preview(
                    args.output, start=args.start, end=args.end, scene=args.scene, fps=args.fps, quality=args.quality
                )
            elif command == "review":
                result = project.review(json.loads(args.file.read_text()))
            elif command == "render":
                result = project.render(args.output, fps=args.fps, quality=args.quality)
            elif command in {"storyboard", "verify"}:
                result = getattr(project, command)(args.output)
            elif command == "audit-layout":
                result = project.audit_layout(detailed=args.full)
            else:
                result = getattr(project, command)()
            if hasattr(result, "model_dump"):
                result = result.model_dump(mode="json")
        ok = not isinstance(result, dict) or (result.get("ok", True) and result.get("status") != "failed")
        if isinstance(result, dict) and "verification" in result:
            ok = result["verification"]["status"] == "passed"
        print(json.dumps({"ok": ok, "result": result}, indent=2, default=str))
        return 0 if ok else 1
    except (AgentError, KitError, ValidationError, ValueError, TypeError, OSError, RuntimeError) as exc:
        if isinstance(exc, AgentError):
            error = exc.as_dict()
        elif isinstance(exc, KitError):
            error = {**exc.as_dict(), "suggested_fix": "Correct the scoped kit error, then repeat this operation"}
        elif isinstance(exc, ValidationError):
            error = {
                "code": "PLAN_SCHEMA",
                "message": str(exc),
                "locations": [list(e["loc"]) for e in exc.errors()],
                "suggested_fix": "Inspect fc-agent schema for this record and correct the reported fields",
            }
        else:
            error = {"code": "RUNTIME", "message": str(exc), "suggested_fix": "Inspect the input path and diagnostic"}
        print(json.dumps({"ok": False, "error": error}, default=str), file=sys.stderr)
        return 1
