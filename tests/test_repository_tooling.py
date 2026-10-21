"""Focused atlas drift/current ownership and cleanup safety regressions."""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    not (ROOT / "project-map/build.py").is_file(),
    reason="Repository tooling checks require the complete checkout, rather than a standalone Core sdist",
)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_atlas_uses_shared_v2_metadata_without_sdk_dependencies():
    module = load("atlas_build", "project-map/build.py")
    data = module.snapshot()
    metadata = json.loads((ROOT / "docs/v2/public-capabilities.json").read_text())
    assert data["capabilities"] == metadata
    for package in data["packages"]:
        public = metadata["packages"][Path(package["source"]).name]
        assert package["exports"] == public["exports"]
        assert package["version"] == public["version"]
        assert package["dependencies"] == public["dependencies"]
    assert "HtmlClip" in data["web_exports"] and "OSClip" in data["os_exports"]
    assert "chesschamp" not in data["templates"]
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", str(ROOT / "project-map/build.py"), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_atlas_check_rejects_drift_without_writing(tmp_path, monkeypatch):
    module = load("atlas_drift", "project-map/build.py")
    shutil.copytree(ROOT / "project-map/src", tmp_path / "src")
    monkeypatch.setattr(module, "HERE", tmp_path)
    assert module.build() == 0
    assert module.build(check=True) == 0
    page = tmp_path / "index.html"
    changed = page.read_text() + "\n<!-- stale -->"
    page.write_text(changed)
    assert module.build(check=True) == 1
    assert page.read_text() == changed


def test_current_catalog_paths_and_timeline_targets_exist():
    node = shutil.which("node")
    if not node:
        pytest.skip("JavaScript source validation requires Node")
    script = "const fs=require('fs'),vm=require('vm'); process.stdout.write(vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8')+'\\nJSON.stringify({features:FEATURES,milestones:MILESTONES})'));"
    data = json.loads(
        subprocess.check_output([node, "-e", script, str(ROOT / "project-map/src/catalog.js")], text=True)
    )
    ids = {f["id"] for f in data["features"]}
    assert "chess" not in ids and "backends" in ids
    assert len(ids) == len(data["features"])
    for feature in data["features"]:
        assert (ROOT / feature["source"]).is_file(), feature
        assert (ROOT / feature["docs"]).is_file(), feature
        if feature["id"] in {"charts", "maps", "coding", "playground", "web", "os", "flow"}:
            assert feature["layer"] == "kit"
            assert feature["source"].startswith("facelesschamp-kit/")
    assert all(set(m["ids"]) <= ids for m in data["milestones"])
    # Execute the real view builders as pure string functions, without a DOM.
    # This catches removed-feature references and stale paths in rendered views.
    snapshot = load("atlas_views", "project-map/build.py").snapshot()
    render = """
const fs=require('fs'),vm=require('vm');
const source=fs.readFileSync(process.argv[1],'utf8') + '\\n' +
  fs.readFileSync(process.argv[2],'utf8').split('const VIEWS=')[0];
const views=vm.runInNewContext(source + '\\nJSON.stringify({overview:overview(),architecture:architecture(),features:features(),motion:motion(),projects:projects(),timeline:timeline(),repository:repository()})',
  {SNAPSHOT:JSON.parse(fs.readFileSync(0,'utf8'))});
process.stdout.write(views);
"""
    result = subprocess.run(
        [node, "-e", render, str(ROOT / "project-map/src/catalog.js"), str(ROOT / "project-map/src/app.js")],
        input=json.dumps(snapshot),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    views = json.loads(result.stdout)
    assert len(views) == 7
    assert all("<h1>" in html and "undefined" not in html for html in views.values())


def test_cache_cleanup_excludes_user_work_tracked_content_and_symlinks(tmp_path):
    module = load("cache_cleanup", "scripts/clean_dev_caches.py")
    for name in (
        "src/pkg/__pycache__/module.pyc",
        "facelesschamp-kit/build/generated.py",
        "src/tracked/__pycache__/keep.pyc",
        "my-project/__pycache__/keep.pyc",
        "output/__pycache__/keep.pyc",
        ".venv/__pycache__/keep.pyc",
        "assets/__pycache__/keep.pyc",
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("preserve or regenerate")
    (tmp_path / "tests").symlink_to(tmp_path / "my-project", target_is_directory=True)
    paths = module.candidates(tmp_path, ["src/tracked/__pycache__/keep.pyc"])
    assert {p.relative_to(tmp_path).as_posix() for p in paths} == {"src/pkg/__pycache__", "facelesschamp-kit/build"}
