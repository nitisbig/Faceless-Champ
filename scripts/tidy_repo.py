"""Archive historical docs and clear disposable caches so agents read only current material.

Dry run by default: prints a JSON plan. ``--apply`` performs it.

* Historical docs (audits, plans, decisions, milestone logs, codex plans) move to
  ``docs/archive/`` with ``git mv`` when tracked, keeping history. Markdown links
  and repo paths that point at moved files are rewritten in the referencing
  .md/.txt files. A file referenced from code or data (.py, .json, .toml...) is
  kept in place and listed, so sync scripts and tests never break. After
  applying, scripts/sync_reference_docs.py runs to refresh bundled copies.
* ``--caches`` also removes untracked __pycache__/.pytest_cache/.ruff_cache/build
  directories (same rules as scripts/clean_dev_caches.py).

User work (my-project/, output/, assets/, examples/) is never touched.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path("docs/archive")

# Historical material: decision records, audits, milestone logs and one-off plans.
CANDIDATES = (
    "docs/audits",
    "docs/plans",
    "docs/decisions",
    "docs/PREMIUM_EFFECTS_COMPOSITING_CODEX_PLAN.md",
    "docs/SPRING_MOTION_ENGINE_CODEX_PLAN.md",
    "docs/facelesschamp-kit-plan.md",
    "docs/spring-motion-pr.md",
    "docs/v2/api-design.md",
    "docs/v2/architecture-audit.md",
    "docs/v2/architecture-proposal.md",
    "docs/v2/backend-integration.md",
    "docs/v2/dependency-analysis.md",
    "docs/v2/feature-decisions.md",
    "docs/v2/migration-plan.md",
    "docs/v2/performance-baseline.md",
    "docs/v2/m1-implementation.md",
    "docs/v2/m2-implementation.md",
    "docs/v2/m3-implementation.md",
    "docs/v2/m4-implementation.md",
    "docs/v2/m1-evidence",
    "docs/v2/m2-evidence",
)
TEXT_SUFFIXES = {".md", ".txt", ".py", ".toml", ".json", ".yml", ".yaml", ".cfg", ".ini", ".js", ".html"}
SKIP_DIRS = {".git", ".venv", "node_modules", "output", "my-project", "__pycache__", ".ruff_cache", ".pytest_cache"}
PROSE_SUFFIXES = {".md", ".txt"}
# Files that name candidates on purpose (this script, the agent skip list) are not references.
IGNORED_REFERENCES = {"scripts/tidy_repo.py", "AGENTS.md"}
# Generated copies are refreshed by scripts/sync_reference_docs.py instead of being rewritten.
GENERATED = ("facelesschamp-agent/src/facelesschamp_agent/resources/",)


def _git(*args):
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None


def _tracked():
    result = _git("ls-files", "-z")
    return set(result.stdout.split("\0")) if result is not None and result.returncode == 0 else set()


def _files(path):
    path = ROOT / path
    if path.is_file():
        return [path]
    return [p for p in path.rglob("*") if p.is_file()] if path.is_dir() else []


def _text_files(excluded):
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        posix = relative.as_posix()
        if any(part in SKIP_DIRS for part in relative.parts) or relative.parts[:2] == ARCHIVE.parts:
            continue
        if posix in IGNORED_REFERENCES or posix.startswith(GENERATED):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES and path not in excluded:
            yield path


def plan():
    """Return (moves, skipped) without changing anything.

    Each move lists the prose files whose links will be rewritten.
    """
    candidates = {item: _files(item) for item in CANDIDATES if _files(item)}
    members = {p for files in candidates.values() for p in files}
    patterns = {}
    for item, files in candidates.items():
        needles = {item}
        for file in files:
            needles.add(file.relative_to(ROOT).as_posix())
            needles.add(file.name)  # relative links such as (v2/m4-implementation.md)
        if (ROOT / item).is_dir():
            needles.add(Path(item).name + "/")  # e.g. (decisions/skia-backend.md)
        patterns[item] = [re.compile(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])") for n in sorted(needles)]
    references = {item: set() for item in candidates}
    for path in _text_files(members):
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for item, compiled in patterns.items():
            if any(p.search(text) for p in compiled):
                references[item].add(path.relative_to(ROOT).as_posix())
    moves, skipped = [], []
    for item in candidates:
        code = sorted(r for r in references[item] if Path(r).suffix.lower() not in PROSE_SUFFIXES)
        if code:
            skipped.append({"path": item, "referenced_by": code[:10]})
        else:
            moves.append(
                {
                    "from": item,
                    "to": (ARCHIVE / Path(item).relative_to("docs")).as_posix(),
                    "rewrite": sorted(references[item]),
                }
            )
    return moves, skipped


_LINK = re.compile(r"(\]\()([^)\s#]+)(#[^)\s]*)?(\))")


def _rewrite(path, mapping):
    """Point links and literal repo paths in one prose file at moved locations."""
    text = path.read_text()
    original = text

    def link(match):
        target = match.group(2)
        if "://" in target:
            return match.group(0)
        resolved = (path.parent / target).resolve()
        try:
            relative = resolved.relative_to(ROOT).as_posix()
        except ValueError:
            return match.group(0)
        for old, new in mapping.items():
            if relative == old or relative.startswith(old + "/"):
                moved = ROOT / (new + relative[len(old) :])
                href = Path(os.path.relpath(moved, path.parent)).as_posix()
                return match.group(1) + href + (match.group(3) or "") + match.group(4)
        return match.group(0)

    text = _LINK.sub(link, text)
    for old, new in mapping.items():
        text = re.sub(r"(?<![\w/-])" + re.escape(old) + r"(?=[/\s)\]`.,;:]|$)", new, text)
    if text != original:
        path.write_text(text)
        return True
    return False


ARCHIVE_README = """# Archived history

Audits, decision records, plans and milestone logs kept for reference. They describe
how the library got here, not how to use it today. Agents and contributors should
read AGENTS.md, CHEATSHEET.md, llms.txt and docs/api.md instead.
"""


def apply(moves):
    tracked = _tracked()
    done = []
    for move in moves:
        source, target = ROOT / move["from"], ROOT / move["to"]
        target.parent.mkdir(parents=True, exist_ok=True)
        is_tracked = any(name == move["from"] or name.startswith(move["from"] + "/") for name in tracked)
        result = _git("mv", move["from"], move["to"]) if is_tracked else None
        if result is None or result.returncode != 0:
            shutil.move(str(source), str(target))
        done.append({**move, "git": bool(result and result.returncode == 0)})
    readme = ROOT / ARCHIVE / "README.md"
    if done and not readme.exists():
        readme.write_text(ARCHIVE_README)
    mapping = {move["from"]: move["to"] for move in moves}
    rewritten = sorted({name for move in moves for name in move["rewrite"] if _rewrite(ROOT / name, mapping)})
    return done, rewritten


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="perform the plan (default: dry run)")
    parser.add_argument("--caches", action="store_true", help="also remove untracked cache/build directories")
    args = parser.parse_args(argv)
    moves, skipped = plan()
    report = {"applied": args.apply, "archive": moves, "kept_referenced": skipped}
    if args.caches:
        import importlib.util

        spec = importlib.util.spec_from_file_location("clean_dev_caches", ROOT / "scripts" / "clean_dev_caches.py")
        caches = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(caches)
        paths = caches.candidates(ROOT, _tracked())
        report["caches"] = [str(p.relative_to(ROOT)) for p in paths]
        if args.apply:
            for path in paths:
                shutil.rmtree(path)
    if args.apply:
        report["archive"], report["rewritten"] = apply(moves)
        sync = ROOT / "scripts" / "sync_reference_docs.py"
        if moves and sync.is_file():
            result = subprocess.run([sys.executable, str(sync)], capture_output=True, text=True, check=False)
            report["sync_reference_docs"] = "ok" if result.returncode == 0 else result.stderr.strip()[-500:]
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
