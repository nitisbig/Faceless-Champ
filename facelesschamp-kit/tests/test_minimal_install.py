"""3D installation is optional for base projects and explicit for Arch starters."""

import json
import subprocess
import sys
import tomllib

from facelesschamp_kit.scaffold import init_project


def test_arch_starter_declares_3d_extra(tmp_path):
    root = init_project(tmp_path / "arch", "archchamp")
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    assert project["dependencies"] == ["facelesschamp-kit[3d]==2.0.0rc1"]
    assert "facelesschamp-kit[3d]" in (root / "README.md").read_text()
    silent = init_project(tmp_path / "silent", "silent")
    assert "[3d]" not in (silent / "pyproject.toml").read_text()


def test_doctor_treats_missing_3d_as_optional(tmp_path, monkeypatch):
    from facelesschamp_kit import cli

    original = cli.package_version
    monkeypatch.setattr(cli, "package_version", lambda name: "source" if name in {"pyvista", "vtk"} else original(name))
    result = cli.doctor(tmp_path)
    assert not result["optional"]["pyvista"]
    assert not result["optional"]["vtk"]
    assert "pyvista" not in result["checks"]
    assert "vtk" not in result["checks"]
    assert result["ok"] == all(result["checks"].values())
    assert "facelesschamp-kit[3d]" in result["guidance"]["3d"]


def test_doctor_and_agent_discovery_open_no_native_engines(tmp_path):
    code = """
import importlib.abc, json, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'manim','cairo','manimpango','av','pyvista','vtk','vtkmodules','numpy','matplotlib','skia','moderngl','glcontext','build123d','OCP','trimesh','scipy','chess','pygments','playwright'}:
            raise AssertionError('unexpected native import: '+fullname)
sys.meta_path.insert(0,Block())
from facelesschamp_kit.cli import doctor
result=doctor(sys.argv[1])
assert not result['gpu']['probed']
print(json.dumps(result))
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code, str(tmp_path)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert not json.loads(result.stdout)["gpu"]["probed"]
