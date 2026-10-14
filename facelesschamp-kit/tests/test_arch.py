import json

import pytest
import pyvista as pv
from faceless_champ import ArchMesh, ArchPart, ArchScript, Canvas

from facelesschamp_kit import BuildContext, KitError, Project, Video
from facelesschamp_kit.blocks import ArchCanvas
from facelesschamp_kit.cli import doctor
from facelesschamp_kit.dependencies import check_dependencies, dependencies
from facelesschamp_kit.recipes import apply_recipe, recipe_specs, validate_recipe
from facelesschamp_kit.scaffold import init_project


@pytest.mark.parametrize("size", [(1920, 1080), (1080, 1920)])
def test_fresh_viewports_lifetimes_and_source_offsets(tmp_path, size):
    ctx = BuildContext(tmp_path, Canvas(*size))
    block = ArchCanvas(
        [ArchPart("body", ArchMesh.from_data(pv.Cube()))], ArchScript().orbit(90, duration=3), source_start=1
    )
    a, b = block.compose(ctx, ctx.bounds), block.compose(ctx, ctx.bounds)
    assert a.root is not b.root and a.children == {"model": a.root}
    video = Video(ctx)
    video.segment("model", duration=2).add(block)
    compiled = video.compile()
    assert not [d for d in compiled.report["diagnostics"] if d["code"] == "BOUNDS"]
    short = Video(ctx)
    short.segment("model", duration=1).add(block)
    with pytest.raises(KitError, match="MOTION_WINDOW"):
        short.compile()


def test_recipe_validation_no_gl_and_model_handles(tmp_path, monkeypatch):
    spec = next(s for s in recipe_specs() if s.id == "arch-design")
    monkeypatch.setattr(pv, "Plotter", lambda *a, **k: pytest.fail("opened GL"))
    content = validate_recipe(spec.id, spec.example)
    video = Video(BuildContext(tmp_path))
    assert set(apply_recipe(video.segment("model", duration=2), spec.id, content)) == {"model"}
    assert video.compile().duration == 2
    with pytest.raises(KitError, match="ARCH_DATA"):
        validate_recipe(spec.id, {"design": {"parts": [{"id": "body", "mesh": {"file": "x.stl"}}]}})


def test_mesh_assets_and_geometry_fingerprints(tmp_path):
    root = init_project(tmp_path / "project", "archchamp")
    data = pv.Cube()
    data.save(root / "assets/model.vtp")
    (root / "assets/manifest.json").write_text(json.dumps({"body": {"type": "mesh", "path": "assets/model.vtp"}}))
    (root / "videos/main.py").write_text("""from facelesschamp_kit import Video
from facelesschamp_kit.blocks import ArchCanvas
def build(ctx):
    v=Video(ctx)
    v.segment("model",duration=2).add(ArchCanvas({"parts":[{"id":"body","mesh":{"asset":"body"}}]}))
    return v
""")
    project = Project(root)
    first = project.build().report
    assert first["assets"][0]["type"] == "mesh"
    data.points[:] *= 2
    data.save(root / "assets/model.vtp")
    second = project.build().report
    assert first["arch_designs"] != second["arch_designs"]
    assert first["assets"][0]["checksum"] != second["assets"][0]["checksum"]


def test_standard_project_dependencies_and_doctor(tmp_path, monkeypatch):
    from importlib.metadata import PackageNotFoundError

    import facelesschamp_kit.dependencies as module

    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies=["demo>=2", "absent; python_version < \'1\'"]\n')

    def installed(name):
        if name == "demo":
            return "2.5"
        raise PackageNotFoundError(name)

    monkeypatch.setattr(module, "version", installed)
    assert [r["status"] for r in check_dependencies(tmp_path)] == ["passed", "inactive"]
    monkeypatch.setattr(module, "version", lambda name: "1")
    assert dependencies(tmp_path)[0]["status"] == "incompatible"
    assert not doctor(tmp_path)["ok"]
    with pytest.raises(KitError, match="uv sync"):
        check_dependencies(tmp_path)
    (tmp_path / "pyproject.toml").unlink()
    assert dependencies(tmp_path) == []


def test_dependency_failure_precedes_factory_execution(tmp_path):
    root = init_project(tmp_path / "project", "archchamp")
    (root / "pyproject.toml").write_text('[project]\ndependencies=["fc-deliberately-missing-package>=999"]\n')
    (root / "videos/main.py").write_text('raise AssertionError("must not import factory")')
    with pytest.raises(KitError, match="PROJECT_DEPENDENCY"):
        Project(root).build()


def test_silent_arch_scaffold_and_external_versions(tmp_path):
    root = init_project(tmp_path / "project", "archchamp")
    project = Project(root)
    compiled = project.build()
    assert compiled.composition.canvas.width == 1920
    assert compiled.report["arch_designs"]
    assert compiled.report["versions"]["pyvista"] != "source"
    assert project.dependencies()[0]["status"] == "passed"
    assert not list((root / "assets/audio").iterdir())


def test_scoped_render_failure(tmp_path, monkeypatch):
    from faceless_champ import ArchDataError

    import facelesschamp_kit.project as module

    root = init_project(tmp_path / "project", "archchamp")

    def fail(*args, **kwargs):
        raise ArchDataError("render", "injected backend failure")

    monkeypatch.setattr(module, "save_frame", fail)
    with pytest.raises(KitError, match="ARCH_RENDER"):
        Project(root).frame("main", 0, root / "failed.png")
