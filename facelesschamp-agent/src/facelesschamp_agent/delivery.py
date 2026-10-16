"""A portable renderer that defaults to a short, verified preview."""

from pathlib import Path

from .errors import AgentError

_RENDER_SOURCE = '''"""Render a short preview, or explicitly request the complete video with --full."""

import argparse
import json
import uuid
from pathlib import Path

from facelesschamp_agent import AgentError, AgentProject
from facelesschamp_kit.diagnostics import KitError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="Render the complete final profile")
    parser.add_argument("--start", type=float, default=0, help="Preview source start in seconds")
    parser.add_argument("--duration", type=float, default=10, help="Preview length, at most 10 seconds")
    parser.add_argument("--output", type=Path, help="Output path; relative paths are relative to this project")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent
    try:
        project = AgentProject(root)
        validation = project.validate()
        layout = project.audit_layout()
        if layout["status"] != "passed":
            print(json.dumps({"status": "failed", "stage": "layout", "layout": layout}, indent=2))
            return 1
        operation = "final" if args.full else "preview"
        output = args.output or Path(f"output/agent/{operation}-{uuid.uuid4().hex[:12]}.mp4")
        if not output.is_absolute():
            output = root / output
        if args.full:
            result = project.render(output)
            verification = result["verification"]
        else:
            import math

            if not math.isfinite(args.start) or not math.isfinite(args.duration):
                raise AgentError("RANGE", "Preview start and duration must be finite")
            if not 0 < args.duration <= 10 or not 0 <= args.start < project.plan.brief.duration:
                raise AgentError("RANGE", "Preview requires a valid start and 0 < duration <= 10")
            end = min(project.plan.brief.duration, args.start + args.duration)
            result = project.preview(output, start=args.start, end=end)
            verification = project.verify(output)
        passed = verification.get("status") == "passed"
        print(json.dumps({
            "status": "passed" if passed else "failed",
            "delivery": "full" if args.full else "preview",
            "output": str(output.resolve()),
            "validation": validation,
            "layout": layout,
            "render": result,
            "verification": verification,
            "full_export_verified": bool(args.full and passed),
        }, indent=2, default=str))
        return 0 if passed else 1
    except KitError as exc:
        print(json.dumps({"status": "failed", "error": exc.as_dict()}, indent=2))
        return 1
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "failed", "error": {"code": "INPUT", "message": str(exc)}}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_render_entrypoint(root, *, overwrite=False):
    """Write ``render.py`` without replacing existing user code by default.

    The script anchors both the project and relative outputs at its own path,
    validates and audits layout before export, and decodes/verifies its preview.
    It never prepares executable checkpoints implicitly.
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise AgentError("PROJECT_MISSING", "The project directory must exist", path=str(root))
    target = root / "render.py"
    if target.is_symlink():
        raise AgentError("RENDER_EXISTS", "Refusing to replace a symbolic-link renderer", path=str(target))
    if target.exists() and not overwrite:
        if target.is_file() and target.read_text() == _RENDER_SOURCE:
            return target
        raise AgentError(
            "RENDER_EXISTS",
            "An existing render.py contains user code",
            path=str(target),
            suggested_fix="Review the existing renderer; pass overwrite=True only when replacement is intended",
        )
    with target.open("w" if overwrite else "x") as stream:
        stream.write(_RENDER_SOURCE)
    return target
