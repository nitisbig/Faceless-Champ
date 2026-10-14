"""Audit the full timeline; optionally generate only the seven bounded excerpts."""

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[1]
if not os.environ.get("FC_INSTALLED_ONLY"):
    interpreter = ROOT / ".venv/bin/python"
    if interpreter.exists() and Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        os.execv(str(interpreter), [str(interpreter), str(Path(__file__).resolve()), *sys.argv[1:]])
    sys.path[:0] = [str(ROOT / "src"), str(ROOT / "facelesschamp-kit/src")]
sys.path.insert(0, str(PROJECT))

from facelesschamp_kit import Project
from render import EXCERPTS
from scene.audit import audit, source_hashes, verify_media

from faceless_champ import PillowRenderer, render


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-excerpts", action="store_true")
    parser.add_argument("--media", action="store_true")
    args = parser.parse_args()
    print("Build and audit full source timeline (no full export)", flush=True)
    project = Project(PROJECT)
    compiled = project.build()
    report = audit(compiled)
    print(f"Audit: {report['samples']} viewport states; {len(report['findings'])} findings", flush=True)
    report["source_sha256"] = source_hashes(PROJECT)
    if report["findings"]:
        print(json.dumps(report, indent=2))
        raise SystemExit("Timeline audit failed")
    if args.render_excerpts:
        settings = project.settings(compiled, "preview")
        with PillowRenderer(settings.antialias) as renderer:
            for start, end in EXCERPTS:
                print(f"Excerpt {start:g}–{end:g}s", flush=True)
                render(
                    compiled.composition,
                    PROJECT / "output" / f"{start:g}-{end:g}s-preview.mp4",
                    settings=settings,
                    renderer=renderer,
                    start_time=start,
                    end_time=end,
                    overwrite=True,
                )
    if args.media or args.render_excerpts:
        report.update(verify_media(PROJECT, EXCERPTS))
    report["editorial_review"] = "See verification.md for inspected artifacts and limits"
    target = PROJECT / "verification.json"
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "source_sha256"}, indent=2))


if __name__ == "__main__":
    main()
