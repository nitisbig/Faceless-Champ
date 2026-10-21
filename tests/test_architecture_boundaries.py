"""M1 import ownership, lazy facade and metadata-only discovery contracts."""

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_core_has_no_upward_imports():
    failures = []
    for path in (ROOT / "src/faceless_champ").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, (ast.Name, ast.Attribute))
                and (node.func.id if isinstance(node.func, ast.Name) else node.func.attr)
                in {"import_module", "__import__"}
            ):
                names = [
                    arg.value for arg in node.args[:1] if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                ]
            if any(name.split(".")[0] in {"facelesschamp_kit", "facelesschamp_agent"} for name in names):
                failures.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not failures, failures


def test_lazy_facade_preserves_frozen_public_names_and_identity():
    reference = json.loads((ROOT / "tests/fixtures/m1-v1-reference.json").read_text())
    code = """
import importlib, json, sys
import faceless_champ as core
assert not any(name.startswith('faceless_champ.') for name in sys.modules)
expected = json.loads(sys.argv[1])
expected = {name: target for name, target in expected.items() if name not in core._MOVED and name not in core._RETIRED}
for name in ('ArchCamera', 'ArchMesh', 'ArchPart', 'ArchStyle', 'ArchDataError'):
    module, attribute = core._EXPORTS[name]
    expected[name] = {'module': 'faceless_champ.' + module, 'attribute': attribute}
assert [name for name in core.__all__ if name in expected] == list(expected)
assert len(core.__all__) == len(set(core.__all__))
assert set(expected) <= set(dir(core))
assert 'main' in dir(core)
assert not any(name.startswith('faceless_champ.') for name in sys.modules)
try: core.no_such_public_name
except AttributeError: pass
else: raise AssertionError('unknown name must raise AttributeError')
for name, target in expected.items():
    value = getattr(core, name)
    assert value is getattr(importlib.import_module(target['module']), target['attribute']), name
    assert getattr(core, name) is value
assert callable(core.main)
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code, json.dumps(reference["exports"])],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_discovery_and_all_exports_never_import_optional_engines():
    code = """
import importlib.abc, sys
blocked = {'manim','cairo','manimpango','av','pyvista','vtk','vtkmodules','numpy','matplotlib','skia','moderngl','glcontext',
           'build123d','OCP','trimesh','scipy','networkx','manifold3d','fast_simplification',
           'chess','pygments','playwright'}
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in blocked: raise AssertionError('native import: '+fullname)
sys.meta_path.insert(0,Block())
import faceless_champ as core
for name in core.__all__: getattr(core,name)
from faceless_champ.arch import geometry_capabilities
for backend in ('pillow','skia','moderngl','auto'):
    assert not core.renderer_capabilities(backend)['probed']
assert geometry_capabilities()['probes'] == {}
assert not blocked.intersection(sys.modules)
"""
    result = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_three_wheels_forward_optional_3d_conversion_dependencies():
    import tomllib

    core = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert core["dependencies"] == ["Pillow>=10.4,<13"]
    extras = ("3d", "cad", "geometry", "geometry-advanced")
    for extra in extras:
        assert "pyvista>=0.49.1,<0.50" in core["optional-dependencies"][extra]
    for directory, downstream in (
        ("facelesschamp-kit", "faceless-champ"),
        ("facelesschamp-agent", "facelesschamp-kit"),
    ):
        project = tomllib.loads((ROOT / directory / "pyproject.toml").read_text())["project"]
        assert not any("[" in dependency for dependency in project["dependencies"])
        for extra in extras:
            assert project["optional-dependencies"][extra][0].startswith(f"{downstream}[{extra}]>=")


def test_optional_native_frames_match_frozen_v1_wheel():
    import hashlib
    import os
    import runpy
    from importlib.metadata import version

    import pytest

    baseline_python = os.environ.get("FC_NATIVE_REFERENCE_PYTHON")
    if os.environ.get("FC_NATIVE_REFERENCE_PIXELS") != "1" and not baseline_python:
        pytest.skip("Select the certified V1 stack or an isolated complete M1 reference wheel interpreter")
    for module in ("pyvista", "numpy", "skia"):
        pytest.importorskip(module)
    from faceless_champ import create_renderer

    reference = json.loads((ROOT / "tests/fixtures/m1-v1-reference.json").read_text())
    versions = {name: version(name) for name in reference["native_versions"]}
    if versions != reference["native_versions"]:
        pytest.skip("Pixel hashes require the frozen native dependency stack")
    expected = reference["native_frames"]
    if baseline_python:
        # Scientific pixels also depend on the host's native rendering libraries.
        # Preserve the original goldens; on another host compare a complete M1
        # wheel with the same fixture/dependencies in a fresh interpreter.
        probe = """
import hashlib, json, runpy, sys
from pathlib import Path
from importlib.metadata import version
import faceless_champ as core
assert Path(core.__file__).is_relative_to(sys.prefix), core.__file__
assert not hasattr(core, 'Viewport'), 'reference must be the complete frozen M1 wheel'
frames = {}
for name, (backend, scene) in runpy.run_path(sys.argv[1])['native_scenes']().items():
    with core.create_renderer(backend) as renderer:
        renderer.validate(scene)
        for t in (0, .35, 1.25, .35):
            frames[f'{name}:{t}'] = hashlib.sha256(renderer.frame(scene, t, (320, 180)).tobytes()).hexdigest()
print(json.dumps({'frames': frames, 'versions': {name: version(name) for name in json.loads(sys.argv[2])}}))
"""
        completed = subprocess.run(
            [
                baseline_python,
                "-I",
                "-B",
                "-c",
                probe,
                str(ROOT / "tests/fixtures/v1/minimal_scenes.py"),
                json.dumps(list(versions)),
            ],
            cwd="/tmp",
            capture_output=True,
            text=True,
            check=True,
        )
        baseline = json.loads(completed.stdout)
        assert baseline["versions"] == versions
        expected = baseline["frames"]
        # Font/path samples still match the original fixed-stack goldens.
        assert {k: v for k, v in expected.items() if k.startswith("native:")} == {
            k: v for k, v in reference["native_frames"].items() if k.startswith("native:")
        }
    factory = runpy.run_path(str(ROOT / "tests/fixtures/minimal_scenes.py"))["native_scenes"]
    for name, (backend, scene) in factory().items():
        with create_renderer(backend) as renderer:
            renderer.validate(scene)
            for t in (0, 0.35, 1.25, 0.35):
                image = renderer.frame(scene, t, (320, 180))
                assert hashlib.sha256(image.tobytes()).hexdigest() == expected[f"{name}:{t}"]
