"""List disposable checkout caches; --apply removes only untracked candidates.

User projects, output/evidence, assets, reference material and environments are
outside the cleanup roots. Migration stubs and package metadata are retained.
"""

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (
    "src",
    "tests",
    "scripts",
    "examples",
    "website/scripts",
    "project-map",
    "facelesschamp-kit/src",
    "facelesschamp-kit/tests",
    "facelesschamp-kit/scripts",
    "facelesschamp-agent/src",
    "facelesschamp-agent/tests",
    "facelesschamp-agent/scripts",
)
CACHE_NAMES = {"__pycache__", ".pytest_cache", ".ruff_cache"}


def candidates(root, tracked):
    paths = set()
    for source in SOURCE_ROOTS:
        for parent, directories, _ in os.walk(root / source, followlinks=False):
            for name in directories[:]:
                path = Path(parent) / name
                if name in CACHE_NAMES:
                    paths.add(path)
                    directories.remove(name)
                elif name in {".venv", ".git", "output"} or path.is_symlink():
                    directories.remove(name)
    for package in ("", "facelesschamp-kit", "facelesschamp-agent"):
        for name in (*sorted(CACHE_NAMES), "build"):
            path = root / package / name
            if path.is_dir():
                paths.add(path)
    safe = []
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix()
        linked = any(p.is_symlink() for p in (path, *path.parents) if p != root and p.is_relative_to(root))
        if linked or any(name == relative or name.startswith(relative + "/") for name in tracked):
            continue
        safe.append(path)
    return safe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Remove listed untracked caches/build directories")
    args = parser.parse_args()
    tracked = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"], text=True).split("\0")
    paths = candidates(ROOT, tracked)
    removed_bytes = sum(
        p.stat().st_size for path in paths for p in path.rglob("*") if p.is_file() and not p.is_symlink()
    )
    if args.apply:
        for path in paths:
            shutil.rmtree(path)
    print(
        json.dumps(
            {"applied": args.apply, "directories": [str(p.relative_to(ROOT)) for p in paths], "bytes": removed_bytes},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
