import json
from copy import deepcopy
from dataclasses import asdict, replace

import pytest
import pyvista as pv
from faceless_champ.integrations.pyvista.camera import ArchCamera
from faceless_champ.integrations.pyvista.model import ArchDataError, ArchMesh, ArchPart, ArchStyle
from facelesschamp_kit.engineering.annotations import ArchDimension, ArchLabel
from facelesschamp_kit.engineering.script import ArchScript
from faceless_champ import Canvas

from facelesschamp_kit import BuildContext, KitError, Project, Video
from facelesschamp_kit.blocks import ArchCanvas
from facelesschamp_kit.cli import doctor
from facelesschamp_kit.dependencies import check_dependencies, dependencies
from facelesschamp_kit.recipes import apply_recipe, recipe_specs, validate_recipe
from facelesschamp_kit.scaffold import init_project


def design_with_settings():
    return {
        "parts": [{"id": "body", "mesh": {"primitive": "cube"}}],
        "script": ArchScript().orbit(20, duration=1).to_dict(),
        "camera": asdict(ArchCamera(position=(3, -3, 2))),
        "style": asdict(ArchStyle(color="#123456")),
        "labels": [asdict(ArchLabel("Original", (0, 0, 0), part="body"))],
        "dimensions": [asdict(ArchDimension((0, 0, 0), (0.5, 0, 0), part="body"))],
        "units": "cm",
    }


@pytest.mark.parametrize("include_settings", [False, True])
def test_structured_design_applies_explicit_canvas_settings(tmp_path, include_settings):
    data = design_with_settings()
    if not include_settings:
        data = {"parts": data["parts"]}
    original = deepcopy(data)
    ctx = BuildContext(tmp_path)
    script = ArchScript().orbit(90, duration=3)
    camera = ArchCamera(position=(8, -4, 3))
    labels = (ArchLabel("Body", (0, 0, 0), part="body"),)
    dimensions = (ArchDimension((-0.5, 0, 0), (0.5, 0, 0), part="body"),)
    block = ArchCanvas(data, script, camera=camera, labels=labels, dimensions=dimensions, units="m", source_start=1)
    first, second = (block.compose(ctx, ctx.bounds).root for _ in range(2))
    assert first is not second
    assert first.script.to_dict() == script.to_dict()
    assert first.state_at(3)["camera"].position != first.state_at(0)["camera"].position
    assert first.camera == camera
    assert first.labels == labels and first.dimensions == dimensions
    assert first.units == "m" and first.source_start == 1
    assert list(first._annotations(0))[-1][1] == "1.00 m"
    assert first.fingerprint == second.fingerprint
    assert data == original
    # Each compose owns its script and annotation snapshots.
    script.wait(1)
    assert first.duration == second.duration == 3


@pytest.mark.parametrize("copy_block", [lambda b: b, deepcopy, replace])
def test_structured_design_preserves_settings_when_canvas_options_are_omitted(tmp_path, copy_block):
    data = design_with_settings()
    original = deepcopy(data)
    ctx = BuildContext(tmp_path)
    block = copy_block(ArchCanvas(data, style=ArchStyle(color="#abcdef")))
    clip = block.compose(ctx, ctx.bounds).root
    assert clip.script.to_dict() == data["script"]
    assert clip.camera == ArchCamera(**data["camera"])
    assert clip.labels == tuple(ArchLabel(**v) for v in data["labels"])
    assert clip.dimensions == tuple(ArchDimension(**v) for v in data["dimensions"])
    assert clip.units == "cm"
    assert clip.style == ArchStyle(**data["style"])
    assert data == original


def test_structured_design_accepts_explicit_empty_annotations_and_default_units(tmp_path):
    ctx = BuildContext(tmp_path)
    clip = (
        ArchCanvas(design_with_settings(), ArchScript(), labels=(), dimensions=[], units="model units")
        .compose(ctx, ctx.bounds)
        .root
    )
    assert clip.duration == 0 and not clip.script.actions
    assert clip.labels == clip.dimensions == ()
    assert clip.units == "model units"


def test_canvas_defaults_remain_compatible_for_parts_and_structured_designs(tmp_path):
    ctx = BuildContext(tmp_path)
    for parts in ([ArchPart("body", ArchMesh.from_data(pv.Cube()))], {"parts": design_with_settings()["parts"]}):
        block = ArchCanvas(parts)
        assert block.labels == block.dimensions == ()
        assert block.units == "model units"
        clip = block.compose(ctx, ctx.bounds).root
        assert clip.duration == 0 and clip.labels == clip.dimensions == ()
        assert clip.units == "model units"
        assert clip.style.color == ctx.theme.foreground and clip.style.edge_color == ctx.theme.accent


def test_structured_design_validates_supplied_annotations(tmp_path):
    ctx = BuildContext(tmp_path)
    block = ArchCanvas({"parts": design_with_settings()["parts"]}, labels=(ArchLabel("Missing", (0, 0, 0), "absent"),))
    with pytest.raises(ArchDataError, match="unknown anchor part"):
        block.compose(ctx, ctx.bounds)


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
    from faceless_champ.integrations.pyvista.model import ArchDataError

    import facelesschamp_kit.project as module

    root = init_project(tmp_path / "project", "archchamp")

    def fail(*args, **kwargs):
        raise ArchDataError("render", "injected backend failure")

    monkeypatch.setattr(module, "save_frame", fail)
    with pytest.raises(KitError, match="ARCH_RENDER"):
        Project(root).frame("main", 0, root / "failed.png")
