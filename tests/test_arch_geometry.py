"""Optional CAD/mesh preparation contracts and exact mechanical source clocks."""

import math
import os
import pickle
import subprocess
import sys
from copy import copy, deepcopy

import numpy as np
import pytest
import pyvista as pv

from faceless_champ.arch import (
    ArchChamp,
    ArchDataError,
    ArchMesh,
    ArchPart,
    ArchScript,
    TessellationOptions,
    boolean_mesh,
    inspect_mesh,
    mesh_from_cad,
    parts_from_cad,
    parts_from_trimesh_scene,
    read_step,
    repair_mesh,
    simplify_mesh,
    slider_crank_pose,
    to_trimesh,
    validate_design,
)
from faceless_champ.arch.camera import part_matrix, world


def test_optional_imports_stay_lazy():
    code = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'build123d','OCP','trimesh','scipy','manifold3d','fast_simplification'}:
            raise AssertionError('optional import: '+fullname)
sys.meta_path.insert(0, Block())
import faceless_champ
from faceless_champ.arch import validate_design, geometry_capabilities
validate_design({'cad':{'preset':'slider_crank'},'units':'mm'})
geometry_capabilities()
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=os.environ, check=False)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "source",
    [
        {"preset": "unknown"},
        {"preset": "piston", "params": {"pin_diameter": 30}},
        {"preset": "spur_gear", "params": {"teeth": 3}},
        {"preset": "slider_crank", "params": {"rod_length": 2}},
        {"asset": "part", "preset": "piston"},
        {"file": "hidden.step"},
        {"preset": "piston", "tessellation": {"surprise": 1}},
    ],
)
def test_structural_cad_errors_without_native_imports(source):
    with pytest.raises(ArchDataError):
        validate_design({"cad": source})


def test_tessellation_validation():
    for kwargs in (
        {"linear_deflection": 0},
        {"max_triangles": True},
        {"angular_deflection": float("nan")},
        {"weld_tolerance": 1},
    ):
        with pytest.raises(ArchDataError):
            TessellationOptions(**kwargs)
    with pytest.raises(ArchDataError):
        validate_design({"cad": {"preset": "piston"}, "parts": []})


def test_cad_probe_rejects_conflicting_providers_before_import(monkeypatch):
    from faceless_champ.arch import cad, dependencies

    monkeypatch.setattr(cad, "_versions", lambda *names: dict.fromkeys(names, "installed"))

    def unexpected_import(*args):
        pytest.fail("native import must follow provider validation")

    monkeypatch.setattr(cad, "_require", unexpected_import)
    result = dependencies.geometry_capabilities(cad=True)
    assert not result["ok"]
    assert "conflicting OCP providers" in result["probes"]["cad"]["error"]


def test_absolute_tessellation_accuracy_order_units_and_immutability():
    bd = pytest.importorskip("build123d")
    shape = bd.Cylinder(10, 25)
    original = tuple(shape.bounding_box().size)
    coarse = mesh_from_cad(shape, options=TessellationOptions(0.5, 0.5))
    fine = mesh_from_cad(shape, options=TessellationOptions(0.01, 0.05))
    assert mesh_from_cad(shape, options=TessellationOptions(0.5, 0.5)).fingerprint == coarse.fingerprint
    assert fine.dataset.n_cells > coarse.dataset.n_cells
    assert fine.dataset.is_manifold
    assert fine.dataset.volume == pytest.approx(np.pi * 100 * 25, rel=0.001)
    data = fine.dataset
    triangles = data.points[data.faces.reshape(-1, 4)[:, 1:]]
    sides = triangles[np.ptp(triangles[:, :, 2], axis=1) > 1e-6]
    midpoints = (sides + np.roll(sides, 1, axis=1)) / 2
    assert (10 - np.linalg.norm(midpoints[:, :, :2], axis=2)).max() <= 0.011
    meter = mesh_from_cad(shape, source_units="mm", target_units="m")
    assert meter.dataset.length == pytest.approx(mesh_from_cad(shape).dataset.length * 0.001)
    assert tuple(shape.bounding_box().size) == original
    assert deepcopy(fine) is fine
    metadata = fine.provenance
    metadata["units"] = "changed"
    assert fine.provenance["units"] == "mm"
    assert pickle.loads(pickle.dumps(fine)).fingerprint == fine.fingerprint
    with pytest.raises(ArchDataError, match="budget"):
        mesh_from_cad(shape, options=TessellationOptions(max_triangles=2))


def test_nested_cad_placements_and_shared_native_instances():
    bd = pytest.importorskip("build123d")
    solid = bd.Box(2, 3, 4)
    a, b = copy(solid), copy(solid)
    a.label = b.label = "part"
    a.location = bd.Location((3, 0, 0), (10, 20, 30))
    b.location = bd.Location((6, 0, 0))
    parent = bd.Compound(children=[a, b], label="root")
    parent.location = bd.Location((1, 2, 3), (0, 0, 90))
    parts = parts_from_cad(parent)
    assert [p.id for p in parts] == ["part", "part-2"]
    assert parts[0].mesh is parts[1].mesh
    for native, part in zip((a, b), parts):
        actual = part_matrix({"position": part.position, "rotation": part.rotation, "scale": 1})
        expected = (
            np.asarray(bd.Matrix(native.global_location.wrapped.Transformation()).transposed_list()).reshape(4, 4).T
        )
        assert np.allclose(actual, expected)


def test_native_identity_cache_keeps_unrelated_parts_distinct():
    pytest.importorskip("build123d")
    from faceless_champ.arch.cad_models import inline_engine

    found = {p.id: p for p in parts_from_cad(inline_engine(cylinders=2))}
    assert found["cylinder-1/rod"].mesh.dataset.n_cells == found["cylinder-2/rod"].mesh.dataset.n_cells == 12
    assert found["cylinder-1/rod"].mesh.fingerprint != found["cylinder-1/crank"].mesh.fingerprint


def test_cad_copy_does_not_traverse_authoring_attributes_or_parent_tree():
    bd = pytest.importorskip("build123d")

    class AuthoringOnly:
        def __deepcopy__(self, memo):
            pytest.fail("conversion copied unrelated authoring state")

    shape = bd.Box(1, 2, 3)
    shape.unrelated = AuthoringOnly()
    parent = bd.Compound(children=[shape])
    parent.unrelated = AuthoringOnly()
    assert parts_from_cad(parent)[0].mesh.dataset.volume == pytest.approx(6)
    assert mesh_from_cad(shape).dataset.volume == pytest.approx(6)


def test_step_inch_units_normalize_to_mm(tmp_path):
    bd = pytest.importorskip("build123d")
    path = tmp_path / "inch.step"
    # export_step's unit describes the authored coordinates (one inch here).
    bd.export_step(bd.Box(1, 2, 3), path, unit=bd.Unit.IN)
    parts = parts_from_cad(read_step(path), target_units="in")
    assert parts[0].mesh.dataset.bounds == pytest.approx((-0.5, 0.5, -1, 1, -1.5, 1.5), abs=1e-6)


def test_cad_provenance_and_serializable_snapshots():
    pytest.importorskip("build123d")
    first = ArchChamp.from_dict({"cad": {"preset": "piston"}, "units": "mm"})
    second = ArchChamp.from_dict({"cad": {"preset": "piston", "params": {"diameter": 16}}})
    assert first.fingerprint != second.fingerprint
    assert first.geometry_record()["provenance"]["piston"]["preset"] == "piston"
    assert pickle.loads(pickle.dumps(first)).fingerprint == first.fingerprint
    with pytest.raises(ArchDataError, match="units"):
        ArchChamp(first.parts, units="m")
    with pytest.raises(ArchDataError, match="unknown part"):
        ArchChamp.from_dict(
            {"cad": {"preset": "piston"}, "labels": [{"text": "bad", "point": [0, 0, 0], "part": "missing"}]}
        )


def test_cad_preset_snapshots_repeat_in_fresh_interpreters():
    pytest.importorskip("build123d")
    code = """
import json
from faceless_champ.arch import parts_from_cad
from faceless_champ.arch.cad_models import gear_pair
shape = gear_pair(teeth=(24, 35))
assert abs(shape.children[1].orientation.Z) < 1e-9
parts = parts_from_cad(shape)
print(json.dumps([(p.id, p.mesh.fingerprint, p.position, p.rotation) for p in parts]))
"""
    results = [
        subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True, timeout=120).stdout
        for _ in range(2)
    ]
    assert results[0] == results[1]


@pytest.mark.parametrize("name", ["spur_gear", "gear_pair", "piston", "slider_crank", "inline_engine", "portal_frame"])
def test_cad_presets_are_valid_and_dimensioned(name):
    pytest.importorskip("build123d")
    from faceless_champ.arch.cad_models import CAD_PRESETS, validate_preset

    params = {"cylinders": 1} if name == "inline_engine" else {"bays": 1} if name == "portal_frame" else {}
    shape = CAD_PRESETS[name](**validate_preset(name, params))
    assert shape.is_valid and shape.volume > 0
    if name == "gear_pair":
        assert shape.children[1].location.position.X == pytest.approx(72)


def test_mesh_roundtrip_quality_fields_and_explicit_repair():
    tm = pytest.importorskip("trimesh")
    pytest.importorskip("scipy")
    source = tm.creation.icosphere(subdivisions=2)
    snapshot = ArchMesh.from_data(source)
    restored = to_trimesh(snapshot)
    restored.vertices[:] *= 2
    assert snapshot.dataset.volume == pytest.approx(source.volume)
    report = inspect_mesh(snapshot)
    assert report["watertight"] and report["winding_consistent"] and report["components"] == 1
    field = ArchMesh.from_arrays(
        source.vertices, source.faces, point_data={"temperature": np.ones(len(source.vertices))}
    )
    with pytest.raises(ArchDataError, match="fields"):
        repair_mesh(field)
    repaired = repair_mesh(field, drop_fields=True)
    assert "temperature" not in repaired.dataset.point_data
    assert "manifold3d" not in repaired.provenance["versions"]
    tagged = snapshot.dataset
    tagged.field_data["batch"] = np.array([42])
    with pytest.raises(ArchDataError, match="fields"):
        to_trimesh(ArchMesh.from_data(tagged))
    opened = tm.creation.box()
    opened.update_faces(np.arange(len(opened.faces)) != 0)
    assert inspect_mesh(opened)["volume"] is None
    assert inspect_mesh(repair_mesh(opened, fill_holes=True))["watertight"]


def test_scene_affine_transforms_reflections_and_shared_instances():
    tm = pytest.importorskip("trimesh")
    scene = tm.Scene()
    source = tm.creation.box()
    scene.add_geometry(source, geom_name="shared", node_name="first")
    scene.graph.update(frame_to="second", matrix=tm.transformations.translation_matrix([3, 0, 0]), geometry="shared")
    scene.graph.update(frame_to="third", matrix=np.diag([-2.0, 1.0, 1.0, 1.0]), geometry="shared")
    parts = parts_from_trimesh_scene(scene)
    assert parts[0].mesh is parts[1].mesh
    assert parts[1].position == (3, 0, 0)
    assert inspect_mesh(parts[2].mesh)["volume"] == pytest.approx(2)
    assert np.allclose(source.extents, [1, 1, 1])
    scene.geometry["shared"].vertex_attributes["temperature"] = np.ones(len(source.vertices))
    with pytest.raises(ArchDataError, match="fields"):
        parts_from_trimesh_scene(scene)
    assert parts_from_trimesh_scene(scene, drop_fields=True)[0].mesh.provenance["drop_fields"]


def test_mesh_booleans_decimation_and_provenance():
    tm = pytest.importorskip("trimesh")
    pytest.importorskip("manifold3d")
    pytest.importorskip("fast_simplification")
    a = tm.creation.box()
    b = tm.creation.box(transform=tm.transformations.translation_matrix([0.5, 0, 0]))
    assert inspect_mesh(boolean_mesh([a, b]))["volume"] == pytest.approx(1.5)
    source = tm.creation.icosphere(subdivisions=3)
    simplified = simplify_mesh(source, 300)
    assert simplified.dataset.n_cells <= 300
    assert simplified.provenance["processing"][-1]["source_faces"] == len(source.faces)
    assert abs(inspect_mesh(simplified)["volume"] / source.volume - 1) < 0.05


def test_slider_crank_closure_and_random_access():
    r, length = 10, 35
    for angle in range(0, 721, 3):
        pose = slider_crank_pose(angle, r, length)
        assert math.dist(pose["crank_pin"], pose["piston_pin"]) == pytest.approx(length)
    mesh = ArchMesh.from_data(pv.Cube())
    parts = [
        ArchPart("crank", mesh),
        ArchPart("rod", mesh, position=(r, 0, 0)),
        ArchPart("piston", mesh, position=(r + length, 0, 0)),
    ]
    script = ArchScript().slider_crank(["crank", "rod", "piston"], duration=4)
    clip = ArchChamp(parts, script)
    restored = ArchChamp(parts, ArchScript.from_dict(script.to_dict()))
    for time in (4, 1, 3, 0, 2, 1):
        assert clip.state_at(time) == restored.state_at(time)
        states = clip.state_at(time)["parts"]
        assert np.allclose(world((r, 0, 0), "crank", states), world((0, 0, 0), "rod", states))
        assert np.allclose(world((length, 0, 0), "rod", states), world((0, 0, 0), "piston", states))


def test_spin_pivot_ratio_conflicts_and_continuous_framing():
    mesh = ArchMesh.from_data(pv.Cube())
    script = ArchScript().spin("a", 90, pivot=(2, 0, 0), duration=2).move("a", (10, 0, 0), at=0, duration=2)
    clip = ArchChamp([ArchPart("a", mesh)], script)
    assert np.allclose(part_matrix(clip.state_at(2)["parts"]["a"]) @ [2, 0, 0, 1], [12, 0, 0, 1])
    with pytest.raises(ArchDataError, match="conflicting"):
        script.spin("a", 30, at=1)
    gears = ArchScript().gear_pair("a", "b", teeth=(24, 48), degrees=180, duration=2)
    clip = ArchChamp([ArchPart("a", mesh), ArchPart("b", mesh)], gears)
    assert np.allclose(part_matrix(clip.state_at(1)["parts"]["b"])[:2, :2], [[2**-0.5, 2**-0.5], [-(2**-0.5), 2**-0.5]])
    before = gears.to_dict()
    with pytest.raises(ArchDataError):
        gears.gear_pair("a", "a", at=2)
    assert gears.to_dict() == before
    mesh = ArchMesh.from_data(pv.Cube(center=(20, 0, 0)))
    clip = ArchChamp([ArchPart("p", mesh)], ArchScript().spin("p", 360))
    center, radius = clip._framing()
    for t in np.linspace(0, 1, 101):
        assert (
            math.dist(world((20, 0, 0), "p", clip.state_at(float(t))["parts"]), center) + mesh.dataset.length / 2
            <= radius + 1e-9
        )


@pytest.mark.parametrize("backend", ["pillow", "skia", "moderngl"])
def test_cad_cutaways_and_prepared_blueprints_keep_native_overlays(backend, monkeypatch):
    bd = pytest.importorskip("build123d")
    if backend != "pillow":
        pytest.importorskip("skia" if backend == "skia" else "moderngl")
    from faceless_champ import Canvas, Scene, Text, create_renderer
    from faceless_champ.arch import ArchCamera, ArchDimension, blueprint_from_cad, cad

    shape = bd.Box(30, 20, 10) - bd.Cylinder(3, 30)
    mesh = mesh_from_cad(shape)
    view = ArchChamp(
        mesh, ArchScript().section("model", (0, 0, 0), cap=True), width=210, height=180, position=(105, 90)
    )
    blueprint = blueprint_from_cad(
        shape,
        width=320,
        height=180,
        margin=30,
        camera=ArchCamera(position=(50, -70, 60)),
        dimensions=[ArchDimension((-15, 0, 0), (15, 0, 0))],
    )
    first = Scene(Canvas(320, 180, "black")).add(view, Text("CAD", font_size=22, position=(275, 90))).wait(1)
    second = Scene(Canvas(320, 180, "black")).add(blueprint).wait(1)
    monkeypatch.setattr(cad, "_engine", lambda: pytest.fail("CAD regenerated during rendering"))
    with create_renderer(backend, antialias=1) as renderer:
        frame = np.asarray(renderer.frame(first, 0.8, (320, 180)))
        assert frame[:, :210, :3].any() and frame[:, 235:, :3].any()
        renderer.frame(first, 0.1, (320, 180))
        assert np.array_equal(frame, renderer.frame(first, 0.8, (320, 180)))
        drawing = np.asarray(renderer.frame(second, 0, (320, 180)))
        assert np.count_nonzero(drawing[:, :, :3]) > 100
    assert blueprint.geometry_provenance["generator"] == "build123d.HLR"


def test_render_sessions_share_base_mesh_but_keep_part_sections_independent():
    from faceless_champ.arch.rendering import ArchSession

    mesh = ArchMesh.from_data(pv.Sphere())
    view = ArchChamp(
        [ArchPart("a", mesh), ArchPart("b", mesh)], ArchScript().section("a", (0, 0, 0), cap=True), width=160, height=90
    )
    with ArchSession(view) as session:
        assert session.meshes["a"] is session.meshes["b"]
        session.frame(1)
        assert session.actors["b"][0].mapper.dataset.n_cells == mesh.dataset.n_cells
        assert session.actors["a"][0].mapper.dataset.n_cells != mesh.dataset.n_cells


def test_different_supplied_fields_do_not_share_prepared_dataset_state():
    from faceless_champ.arch import ArchStyle
    from faceless_champ.arch.rendering import ArchSession

    data = pv.Sphere()
    data["a"] = data.points[:, 0]
    data["b"] = data.points[:, 2]
    mesh = ArchMesh.from_data(data)
    view = ArchChamp(
        [ArchPart("a", mesh, style=ArchStyle(scalars="a")), ArchPart("b", mesh, style=ArchStyle(scalars="b"))],
        width=160,
        height=90,
    )
    with ArchSession(view) as session:
        assert session.meshes["a"] is not session.meshes["b"]
        session.frame(0)
