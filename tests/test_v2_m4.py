"""M4 ownership and explicit import-migration contracts."""

import ast
import importlib
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_core_imports_and_rendering_do_not_require_kit_or_native_engines():
    code = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'facelesschamp_kit', 'facelesschamp_agent', 'numpy', 'pyvista', 'vtk', 'vtkmodules', 'skia', 'moderngl', 'playwright', 'pygments'}:
            raise AssertionError('unexpected import: ' + fullname)
sys.meta_path.insert(0, Block())
import faceless_champ as core
for name in core.__all__:
    getattr(core, name)
scene = core.Scene(core.Canvas(80, 60)).add(core.Rectangle(width=20, height=20, fill='red', position=(40, 30))).wait(1)
with core.PillowRenderer(1) as renderer:
    renderer.validate(scene)
    assert renderer.frame(scene, 0, (80, 60)).getpixel((40, 30)) == (255, 0, 0, 255)
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr


def test_generic_rendering_and_compilation_have_no_domain_dispatch():
    forbidden = {
        "ArchChamp",
        "Chart",
        "Map",
        "CodingChamp",
        "FlowChamp",
        "OSClip",
        "HtmlClip",
        "PlaygroundView",
        "ChessChamp",
    }
    for path in [
        ROOT / "src/faceless_champ/_rendering/raster.py",
        ROOT / "src/faceless_champ/backends/_raster_adapter.py",
        ROOT / "src/faceless_champ/_rendering/plan.py",
    ]:
        names = {node.id for node in ast.walk(ast.parse(path.read_text())) if isinstance(node, ast.Name)}
        assert not names & forbidden, (path, names & forbidden)


@pytest.mark.parametrize(
    "old,new",
    [
        ("charts", "charts"),
        ("maps", "maps"),
        ("coding", "coding"),
        ("flow", "diagrams"),
        ("os_ui", "desktop"),
        ("playground", "playground"),
        ("web", "web"),
    ],
)
def test_old_domain_modules_fail_with_actionable_migration(old, new):
    with pytest.raises(ImportError, match="facelesschamp_kit." + new):
        importlib.import_module("faceless_champ." + old)


def test_chess_is_retired_without_rewriting_user_data():
    import faceless_champ as core

    assert not hasattr(core, "ChessChamp")
    with pytest.raises(ImportError, match="22f3beaccb5a56990bd0974666b7c639a0667a68"):
        importlib.import_module("faceless_champ.chess")
    assert not (ROOT / "src/faceless_champ/assets/chess").exists()
    assert not (ROOT / "assets/chess").exists()
    for manifest in [ROOT / "pyproject.toml", ROOT / "facelesschamp-kit/pyproject.toml"]:
        assert "chess" not in tomllib.loads(manifest.read_text())["project"]["optional-dependencies"]
    assert (ROOT / "docs/legacy/v1/chesschamp.md").is_file()


@pytest.mark.parametrize("isolate", [False, True])
def test_scientific_source_honors_fractional_viewport_size(monkeypatch, isolate):
    from types import SimpleNamespace

    from PIL import Image

    pytest.importorskip("numpy")
    from faceless_champ.integrations.pyvista import _worker, rendering
    from faceless_champ.integrations.pyvista.source import PyVistaSource

    closed = []

    class Session:
        def __init__(self, *args):
            pass

        def frame(self, age):
            return Image.new("RGBA", (50, 166), "red")

        def sprite(self, *args):
            return self.frame(0)

        def close(self):
            closed.append(True)

    monkeypatch.setattr(rendering, "ArchSession", Session)
    monkeypatch.setattr(_worker, "ArchWorker", Session)
    source = PyVistaSource(SimpleNamespace(width=100.3, height=333.3), isolate=isolate)
    session = source.open((50, 167))
    try:
        assert session.frame(0).size == (50, 167)
    finally:
        session.close()
    assert closed == [True]
