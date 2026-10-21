"""Synchronize selected offline references and shared release metadata.

Run with the repository environment. --check reports drift without writing.
The inclusion map deliberately excludes historical audits and release reports.
"""

import argparse
import importlib
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = Path("facelesschamp-agent/src/facelesschamp_agent/resources")
CORE_DOCS = (
    "api",
    "archchamp",
    "architecture",
    "cad-geometry",
    "charts",
    "chesschamp",
    "clean-flow",
    "coding-playgrounds",
    "coding",
    "flowchamp",
    "guide",
    "html-to-video",
    "maps",
    "moderngl",
    "motion-graphics",
    "narration",
    "os-ui",
    "premium-effects",
    "raster-sources",
    "skia",
)
KIT_DOCS = (
    "api",
    "archchamp",
    "architecture",
    "catalog",
    "chesschamp",
    "clean-flow",
    "coding-playgrounds",
    "flowchamp",
    "html-to-video",
    "os-ui",
    "skia",
    "whiteboard",
)
AGENT_DOCS = ("archchamp", "coding-template", "scene-selection")
INCLUSION = {
    Path("llms.txt"): RESOURCES / "core-guide.txt",
    Path("facelesschamp-kit/llms.txt"): RESOURCES / "kit-guide.txt",
    Path("facelesschamp-agent/llms.txt"): RESOURCES / "agent-guide.txt",
    **{Path(f"docs/{name}.md"): RESOURCES / f"docs/core/{name}.md" for name in CORE_DOCS},
    **{Path(f"facelesschamp-kit/docs/{name}.md"): RESOURCES / f"docs/kit/{name}.md" for name in KIT_DOCS},
    **{Path(f"facelesschamp-agent/docs/{name}.md"): RESOURCES / f"docs/agent/{name}.md" for name in AGENT_DOCS},
    Path("docs/v2/m4-migration.md"): RESOURCES / "docs/v2/m4-migration.md",
    Path("docs/v2/m5-migration.md"): RESOURCES / "docs/v2/m5-migration.md",
    Path("docs/v2/m5-implementation.md"): RESOURCES / "docs/v2/m5-implementation.md",
    Path("docs/v2/repository-layout.md"): RESOURCES / "docs/v2/repository-layout.md",
    Path("docs/legacy/v1/chesschamp.md"): RESOURCES / "docs/legacy/v1/chesschamp.md",
    Path("docs/legacy/v1/kit-chesschamp.md"): RESOURCES / "docs/legacy/v1/kit-chesschamp.md",
}


def snapshot(source, target):
    """Keep links between included references navigable in installed resources."""

    def rewrite(match):
        href = match[2]
        parts = urlsplit(href)
        if parts.scheme or not parts.path:
            return match[0]
        path = (ROOT / source).parent.joinpath(unquote(parts.path)).resolve()
        if not path.is_file():
            raise ValueError(f"Broken canonical reference: {source}: {href}")
        relative = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        if relative in INCLUSION:
            href = os.path.relpath(INCLUSION[relative], target.parent)
            if parts.fragment:
                href += "#" + parts.fragment
        return match[1] + href + ")"

    return re.sub(r"(\[[^\]]*\]\()([^\s)]+)\)", rewrite, (ROOT / source).read_text())


def reference_metadata():
    """One version/capability source for offline docs, website and recipe atlas."""
    # Import only base public facades, never resolve native APIs or allocate engines.
    paths = [ROOT / "src", ROOT / "facelesschamp-kit/src", ROOT / "facelesschamp-agent/src"]
    previous = sys.path[:]
    sys.path[:0] = [str(path) for path in paths]
    try:
        from facelesschamp_kit import public_capabilities

        result = public_capabilities()
        packages = result["packages"]
        for module, manifest in (
            ("faceless_champ", "pyproject.toml"),
            ("facelesschamp_kit", "facelesschamp-kit/pyproject.toml"),
            ("facelesschamp_agent", "facelesschamp-agent/pyproject.toml"),
        ):
            project = tomllib.loads((ROOT / manifest).read_text())["project"]
            package = importlib.import_module(module)
            assert project["version"] == package.__version__, f"Version drift: {module}"
            packages[module] = {
                "distribution": project["name"],
                "version": project["version"],
                "exports": sorted(package.__all__),
                "extras": sorted(project["optional-dependencies"]),
                "requires_python": project["requires-python"],
                "dependencies": project["dependencies"],
            }
        result["optional_policy"] = "Install explicitly; discovery does not probe hardware or execute preparation."
        return result
    finally:
        sys.path[:] = previous


def generated_files():
    from facelesschamp_agent.models import BenchmarkResult, QualityReport, VideoPlan

    outputs = {target: snapshot(source, target) for source, target in INCLUSION.items()}
    for name, model in (
        ("video-plan", VideoPlan),
        ("quality-report", QualityReport),
        ("benchmark-result", BenchmarkResult),
    ):
        outputs[RESOURCES / f"{name}.schema.json"] = json.dumps(model.model_json_schema(), indent=2) + "\n"
    data = json.dumps(reference_metadata(), indent=2, sort_keys=True) + "\n"
    for path in (
        RESOURCES / "public-capabilities.json",
        Path("docs/v2/public-capabilities.json"),
        Path("website/dist/capabilities.json"),
    ):
        outputs[path] = data
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    drift = []
    outputs = generated_files()
    for target, content in outputs.items():
        path = ROOT / target
        if not path.is_file() or path.read_text() != content:
            drift.append(str(target))
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
    print(json.dumps({"checked": len(outputs), "drift" if args.check else "updated": drift}, indent=2))
    return int(args.check and bool(drift))


if __name__ == "__main__":
    raise SystemExit(main())
