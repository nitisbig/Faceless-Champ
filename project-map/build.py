"""Refresh the offline project atlas from this checkout. Standard library only."""

from __future__ import annotations

import ast
import base64
import importlib.util
import json
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def exports(path):
    names = []
    for node in ast.parse((ROOT / path).read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            names = ast.literal_eval(node.value)
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) and node.target.id == "__all__":
            names += ast.literal_eval(node.value)
    return names


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def snapshot():
    packages = []
    for directory, source, label in (
        ("", "src/faceless_champ", "Core engine"),
        ("facelesschamp-kit", "facelesschamp-kit/src/facelesschamp_kit", "Authoring framework"),
        ("facelesschamp-agent", "facelesschamp-agent/src/facelesschamp_agent", "Agent workflow"),
    ):
        manifest = tomllib.loads((ROOT / directory / "pyproject.toml").read_text())["project"]
        test_root = ROOT / directory / "tests"
        # Bundled copies of docs/examples are resources, not implementation modules.
        modules = [
            p for p in (ROOT / source).rglob("*.py") if "resources" not in p.parts and "sample_assets" not in p.parts
        ]
        packages.append(
            {
                "name": manifest["name"],
                "version": manifest["version"],
                "label": label,
                "source": source,
                "modules": len(modules),
                "tests": len(list(test_root.glob("test*.py"))),
                "exports": exports(source + "/__init__.py"),
                "dependencies": manifest.get("dependencies", []),
                "extras": manifest.get("optional-dependencies", {}),
            }
        )
    recipe_tree = ast.parse((ROOT / "facelesschamp-kit/src/facelesschamp_kit/recipes.py").read_text())
    recipes = []
    for node in ast.walk(recipe_tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "RecipeSpec":
            recipes.append({"id": ast.literal_eval(node.args[0]), "purpose": ast.literal_eval(node.args[1])})
    scaffold = ast.parse((ROOT / "facelesschamp-kit/src/facelesschamp_kit/scaffold.py").read_text())
    templates = []
    for node in ast.walk(scaffold):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and node.left.id == "template":
            for value in node.comparators:
                if isinstance(value, ast.Set) and any(
                    isinstance(v, ast.Constant) and v.value == "silent" for v in value.elts
                ):
                    templates = sorted(ast.literal_eval(value))
    # Load the standalone analytical kernel; do not import the renderer or execute scenes.
    spec = importlib.util.spec_from_file_location("atlas_spring", ROOT / "src/faceless_champ/spring.py")
    spring_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = spring_module
    spec.loader.exec_module(spring_module)
    curves = {}
    for label, damping in (("gentle", 25), ("critical", 20), ("bouncy", 10)):
        curve = spring_module.Spring(stiffness=100, damping=damping, mass=1)
        curves[label] = [round(curve(i / 1000), 9) for i in range(1001)]
    projects = []
    for directory in sorted((ROOT / "examples/programming").iterdir()):
        readme = directory / "README.md"
        if directory.is_dir() and readme.exists():
            projects.append(
                {
                    "id": directory.name,
                    "readme": str(readme.relative_to(ROOT)),
                    "renderer": str((directory / "render.py").relative_to(ROOT))
                    if (directory / "render.py").exists()
                    else None,
                }
            )
    history = []
    for line in git("log", "--reverse", "--date=short", "--format=%h%x09%ad%x09%s").splitlines():
        sha, day, subject = line.split("\t", 2)
        history.append({"sha": sha, "date": day, "subject": subject})
    return {
        "date": datetime.now(ZoneInfo("Asia/Kathmandu")).date().isoformat(),
        "head": git("rev-parse", "--short", "HEAD"),
        "branch": git("branch", "--show-current"),
        "packages": packages,
        "recipes": recipes,
        "templates": templates,
        "projects": projects,
        "history": history,
        "curves": curves,
        "web_exports": exports("src/faceless_champ/web/__init__.py"),
        "os_exports": exports("src/faceless_champ/os_ui/__init__.py"),
    }


def build():
    data = snapshot()
    page = (HERE / "src/page.html").read_text()
    font = base64.b64encode((ROOT / "assets/fonts/DMSans[opsz,wght].ttf").read_bytes()).decode()
    styles = (HERE / "src/style.css").read_text().replace("ATLAS_FONT_BASE64", font)
    page = page.replace("/* ATLAS_STYLES */", styles)
    page = page.replace(
        "/* ATLAS_DATA */", "const SNAPSHOT = " + json.dumps(data, ensure_ascii=False).replace("</", "<\\/") + ";"
    )
    page = page.replace("/* ATLAS_CATALOG */", (HERE / "src/catalog.js").read_text())
    page = page.replace("/* ATLAS_APP */", (HERE / "src/app.js").read_text())
    (HERE / "index.html").write_text(page)
    print(f"Built {HERE / 'index.html'} ({len(page.encode()):,} bytes)")
    print(
        f"Source {data['head']}: {len(data['projects'])} premium references, {len(data['recipes'])} recipes, {len(data['templates'])} starters"
    )


if __name__ == "__main__":
    build()
