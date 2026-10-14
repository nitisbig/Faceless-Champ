"""Inspect standard project requirements without installing or importing them."""

import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement

from .diagnostics import KitError


def dependencies(root):
    path = Path(root) / "pyproject.toml"
    if not path.is_file():
        return []
    try:
        declared = tomllib.loads(path.read_text()).get("project", {}).get("dependencies", [])
    except (tomllib.TOMLDecodeError, OSError) as exc:
        raise KitError("PROJECT_DEPENDENCY", f"Cannot read project requirements: {exc}") from exc
    if not isinstance(declared, list) or any(not isinstance(r, str) for r in declared):
        raise KitError("PROJECT_DEPENDENCY", "project.dependencies must be a list of PEP 508 requirements")
    result = []
    for raw in declared:
        try:
            requirement = Requirement(raw)
        except InvalidRequirement as exc:
            raise KitError("PROJECT_DEPENDENCY", f"Invalid requirement: {raw}") from exc
        active = requirement.marker is None or requirement.marker.evaluate({"extra": ""})
        try:
            installed = version(requirement.name)
        except PackageNotFoundError:
            installed = None
        status = (
            "inactive"
            if not active
            else "missing"
            if installed is None
            else (
                "passed"
                if not requirement.specifier or requirement.specifier.contains(installed, prereleases=True)
                else "incompatible"
            )
        )
        result.append(
            {
                "requirement": raw,
                "name": requirement.name,
                "installed_version": installed,
                "status": status,
                "extras": sorted(requirement.extras),
                "direct_url": requirement.url,
            }
        )
    return result


def check_dependencies(root):
    rows = dependencies(root)
    failures = [r for r in rows if r["status"] in {"missing", "incompatible"}]
    if failures:
        raise KitError(
            "PROJECT_DEPENDENCY",
            "Missing or incompatible project dependencies; run uv sync in the project environment",
            dependencies=failures,
        )
    return rows
