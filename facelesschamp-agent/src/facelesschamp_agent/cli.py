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

from .errors import AgentError
from .models import SCHEMAS
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
    ):
        command = sub.add_parser(name)
        command.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
        command.add_argument("--project", default=argparse.SUPPRESS)
        commands[name] = command
    commands["init"].add_argument("destination")
    commands["capabilities"].add_argument("query", nargs="?", default="")
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
    try:
        args = parser.parse_args(argv)
        command = args.command
        if command == "init":
            result = {"path": str(init_project(args.destination))}
        elif command == "doctor":
            result = doctor(args.project)
            result["agent"] = "0.1.0rc1"
            result["registry"] = CapabilityRegistry().check()
        elif command == "capabilities":
            result = CapabilityRegistry().search(args.query)
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
                result = project.preview(args.output, start=args.start, end=args.end, scene=args.scene)
            elif command == "review":
                result = project.review(json.loads(args.file.read_text()))
            elif command in {"storyboard", "render", "verify"}:
                result = getattr(project, command)(args.output)
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
