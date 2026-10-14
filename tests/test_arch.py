"""Geometry contracts, random-access compositing and owned-session lifecycle."""

from copy import deepcopy

import numpy as np
import pytest
import pyvista as pv

from faceless_champ import (
    ArchCamera,
    ArchChamp,
    ArchDataError,
    ArchDimension,
    ArchLabel,
    ArchMesh,
    ArchPart,
    ArchScript,
    ArchStyle,
    Canvas,
    Grid,
    Group,
    Layer,
    PillowRenderer,
    RectangleMask,
    Scene,
    Sequence,
    render_storyboard,
    save_frame,
)
from faceless_champ.arch import validate_design
from faceless_champ.arch.rendering import ArchSession


def cube(script=None, **kwargs):
    return ArchChamp(
        [ArchPart("body", ArchMesh.from_data(pv.Cube()))], script, width=160, height=120, position=(80, 60), **kwargs
    )


def scene(clip):
    node = Scene(Canvas(160, 120, "#000000"))
    node.add(clip)
    node.wait(max(2, clip.duration))
    return node


def test_geometry_isolation_fingerprints_and_scene_snapshots():
    source = pv.Cube()
    source.point_data["temperature"] = np.arange(source.n_points, dtype=float)
    mesh = ArchMesh.from_data(source)
    same = ArchMesh.from_data(source)
    assert mesh.fingerprint == same.fingerprint
    source.points[:] *= 5
    source["temperature"][:] = 100
    inspected = mesh.dataset
    inspected.points[:] = 0
    assert mesh.dataset.bounds == same.dataset.bounds
    assert deepcopy(mesh) is mesh
    with pytest.raises(AttributeError):
        mesh.fingerprint = "altered"
    assert mesh.fingerprint != ArchMesh.from_data(source).fingerprint
    clip = ArchChamp(mesh, width=160, height=120, position=(80, 60))
    first = scene(clip)
    clip.frame_image(0)
    second = scene(clip)
    with PillowRenderer(1) as r:
        assert np.array_equal(r.frame(first, 0, (160, 120)), r.frame(second, 0, (160, 120)))


@pytest.mark.parametrize("suffix", [".stl", ".obj", ".ply", ".vtp", ".vtu"])
def test_local_file_imports(tmp_path, suffix):
    mesh = pv.Cube().triangulate()
    if suffix == ".vtu":
        mesh = mesh.cast_to_unstructured_grid()
    path = tmp_path / ("model" + suffix)
    mesh.save(path)
    asset = ArchMesh.from_file(path)
    assert asset.dataset.n_points > 0
    assert asset.source == str(path.resolve())


def test_named_multiblock_file(tmp_path):
    data = pv.MultiBlock({"shell": pv.Cube(), "core": pv.Sphere(radius=0.25)})
    data.save(tmp_path / "assembly.vtm")
    clip = ArchChamp.from_file(tmp_path / "assembly.vtm")
    assert [p.id for p in clip.parts] == ["shell", "core"]


def test_array_validation_and_fields():
    points = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
    mesh = ArchMesh.from_arrays(points, [[0, 1, 2]], point_data={"value": [1, 2, 3]})
    assert mesh.dataset.n_cells == 1
    for bad in ([[0, 1, 5]], [[0, 1, -1]], [3, 0, 1], [[0.0, 1.0, 2.0]]):
        with pytest.raises(ArchDataError):
            ArchMesh.from_arrays(points, bad)
    with pytest.raises(ArchDataError):
        ArchMesh.from_arrays([[float("nan"), 0, 0]])
    with pytest.raises(ArchDataError):
        ArchMesh.from_arrays(points, point_data={"bad": [1]})
    with pytest.raises(ArchDataError):
        cube(style=ArchStyle(concept="heatmap"))
    with pytest.raises(ArchDataError):
        cube(style=ArchStyle(scalars="missing"))


def test_script_validation_serialization_and_random_access():
    script = ArchScript().move("body", (1, 0, 0), at=0, duration=1).rotate("body", (0, 0, 90), at=0, duration=1)
    script.opacity("body", 0.5, at=0, duration=1).explode("body", 2, at=1, duration=1).orbit(30, at=0, duration=2).wait(
        1
    )
    assert ArchScript.from_dict(script.to_dict()).to_dict() == script.to_dict()
    clip = cube(script)
    expected = clip.state_at(1.5)
    clip.state_at(0.1)
    assert clip.state_at(1.5) == expected
    assert expected["parts"]["body"]["position"] == (0.5, 0, 1)
    assert clip.state_at(10)["parts"]["body"]["position"] == (0, 0, 2)
    assert clip.frame_key(2.2) == clip.frame_key(2.9)
    hidden = cube(ArchScript().show("body", at=1))
    assert not hidden.state_at(0)["parts"]["body"]["visible"]
    assert hidden.state_at(1)["parts"]["body"]["visible"]
    assert not cube(ArchScript().hide("body", at=0)).state_at(0)["parts"]["body"]["visible"]
    with pytest.raises(ArchDataError):
        script.move("body", (2, 0, 0), at=0.5)
    with pytest.raises(ArchDataError):
        cube(ArchScript().move("unknown", (0, 0, 0)))
    with pytest.raises(ArchDataError):
        ArchScript().opacity("body", 2)
    with pytest.raises(ArchDataError):
        ArchCamera(position=(0, 0, 0))
    with pytest.raises(ArchDataError):
        cube(source_start=1)


@pytest.mark.parametrize(
    "concept",
    ["clay", "solid", "wireframe", "topology", "transparent", "xray", "blueprint", "points", "isometric", "voxel"],
)
def test_design_concepts_render_visible_pixels(concept):
    clip = cube(style=ArchStyle(concept=concept, voxel_spacing=0.3))
    with ArchSession(clip, 1) as session:
        pixels = np.asarray(session.frame(0))
        assert pixels.shape == (120, 160, 4)
        assert np.count_nonzero(pixels[..., 3]) > 20
        assert pixels[..., 3].min() == 0
        if concept in {"transparent", "xray"}:
            assert pixels[..., 3].max() < 255


def test_scalar_vector_fields_and_streamlines():
    grid = pv.ImageData(dimensions=(5, 5, 5), spacing=(0.2, 0.2, 0.2))
    grid["temperature"] = grid.points[:, 0]
    grid["flow"] = np.tile([1.0, 0.0, 0.0], (grid.n_points, 1))
    for mode in ("glyphs", "streamlines"):
        clip = ArchChamp(
            ArchMesh.from_data(grid),
            style=ArchStyle(concept="heatmap", scalars="temperature", vectors="flow", field_mode=mode, clim=(0, 1)),
            width=160,
            height=120,
        )
        with ArchSession(clip) as session:
            assert np.asarray(session.frame(0))[..., 3].max() > 0
            assert len(session.actors["model"]) == 2
    highlighted = ArchChamp(
        ArchMesh.from_data(grid),
        ArchScript().highlight("model"),
        style=ArchStyle(concept="heatmap", scalars="temperature"),
        width=160,
        height=120,
    )
    with ArchSession(highlighted) as session:
        session.frame(0.5)
        assert session.actors["model"][0].prop.show_edges


def test_sections_cap_constraints_and_backward_sampling():
    script = ArchScript().section("body", (0, 0, 0), cap=True, duration=1).wait(1)
    clip = cube(script)
    with ArchSession(clip) as session:
        end = np.asarray(session.frame(1)).copy()
        session.frame(0.2)
        assert np.array_equal(end, session.frame(1))
    with pytest.raises(ArchDataError):
        ArchChamp([ArchPart("body", ArchMesh.from_data(pv.Plane()))], script)
    data = pv.Cube()
    data["temperature"] = np.arange(data.n_points)
    with pytest.raises(ArchDataError):
        ArchChamp([ArchPart("body", ArchMesh.from_data(data))], script, style=ArchStyle(scalars="temperature"))


def test_annotations_measurement_projection_and_diagnostics():
    clip = cube(
        labels=[ArchLabel("body", (0, 0, 0), "body"), ArchLabel("body", (0, 0, 0), "body")],
        dimensions=[ArchDimension((-0.5, 0, 0), (0.5, 0, 0), "body")],
        units="m",
    )
    values = list(clip._annotations(0))
    assert values[-1][1] == "1.00 m"
    clip.scale = 3
    assert list(clip._annotations(0))[-1][1] == "1.00 m"
    assert any(d["code"] == "ARCH_ANNOTATION_OVERLAP" for d in clip.diagnostics_at(0))
    camera = clip.state_at(0)["camera"]
    behind = tuple(camera.position[i] * 2 - camera.focal_point[i] for i in range(3))
    assert clip.project_at(0, [behind])[0] is None


def test_nested_composition_mask_cache_and_source_offset():
    script = ArchScript().orbit(90, duration=2)
    original = cube(script)
    offset = cube(script, source_start=1)
    first, second = scene(original), scene(offset)
    with PillowRenderer(1) as r:
        assert np.array_equal(r.frame(first, 1.5, (160, 120)), r.frame(second, 0.5, (160, 120)))
        expected = r.frame(first, 0.4, (160, 120))
        r.frame(first, 1.8, (160, 120))
        assert np.array_equal(expected, r.frame(first, 0.4, (160, 120)))
        for node in (Sequence(first, second), Layer(first, second), Grid(first, second, columns=2)):
            assert r.frame(node, 0.5, (320, 240)).size == (320, 240)
    original.mask = RectangleMask(160, 120)
    group = Group(original)
    grouped = Scene(Canvas(160, 120, "#000000"))
    grouped.add(group)
    grouped.wait(2)
    with PillowRenderer(1, arch_session_limit=1) as r:
        r.frame(grouped, 0.5, (160, 120))
        old = next(iter(r._arch_sessions.values()))
        r.frame(second, 0.5, (160, 120))
        assert old.plotter is None
    assert not r._arch_sessions


def test_helper_cleanup_and_caller_ownership(tmp_path, monkeypatch):
    closed = []
    original = PillowRenderer.close

    def close(renderer):
        closed.append(renderer)
        original(renderer)

    monkeypatch.setattr(PillowRenderer, "close", close)
    node = scene(cube())
    save_frame(node, 0, tmp_path / "frame.png", size=(160, 120))
    assert closed[-1]._arch_sessions == {}
    count = len(closed)
    r = PillowRenderer(1)
    render_storyboard(node, [0, 1], tmp_path / "board", size=(160, 120), renderer=r)
    assert len(closed) == count and r._arch_sessions
    r.close()
    with pytest.raises(ValueError):
        save_frame(node, 3, tmp_path / "bad.png")
    assert len(closed) == count + 2


def test_structured_contract_no_gl_and_shared_validation(monkeypatch):
    data = {
        "parts": [{"id": "body", "mesh": {"primitive": "cube"}}],
        "script": {"actions": [{"kind": "orbit", "degrees": 20, "at": 0, "duration": 1}]},
    }
    monkeypatch.setattr(pv, "Plotter", lambda *a, **k: pytest.fail("validation opened GL"))
    assert validate_design(data) == data
    assert ArchChamp.from_dict(data).duration == 1
    with pytest.raises(ArchDataError):
        validate_design({"parts": [{"id": "body", "mesh": {"file": "x.stl"}}]}, registered_only=True)
    with pytest.raises(ArchDataError):
        ArchScript.from_dict({"actions": [{"kind": "orbit", "degrees": 20, "unexpected": True}]})


def test_field_sections_restore_all_actors_and_failure_closes(tmp_path, monkeypatch):
    mesh = pv.ImageData(dimensions=(5, 5, 5), spacing=(0.2, 0.2, 0.2))
    mesh["flow"] = np.tile([1.0, 0.0, 0.0], (mesh.n_points, 1))
    clip = ArchChamp(
        ArchMesh.from_data(mesh),
        ArchScript().section("model", (0.4, 0, 0), at=0.2, duration=0.8),
        style=ArchStyle(vectors="flow"),
        width=160,
        height=120,
        position=(80, 60),
    )
    with ArchSession(clip) as session:
        original = session.field_meshes["model"].n_points
        session.frame(1)
        assert session.actors["model"][1].mapper.dataset.n_points < original
        session.frame(0)
        assert session.actors["model"][1].mapper.dataset.n_points == original
    closed = []
    real_close = ArchSession.close

    def close(session):
        closed.append(session)
        real_close(session)

    def fail(session, age):
        raise RuntimeError("injected frame failure")

    monkeypatch.setattr(ArchSession, "close", close)
    monkeypatch.setattr(ArchSession, "frame", fail)
    with pytest.raises(RuntimeError, match="injected"):
        save_frame(scene(clip), 0, tmp_path / "failed.png", size=(160, 120))
    assert closed and all(s.plotter is None for s in closed)


def test_reused_session_updates_framebuffer_and_matches_fresh_frames():
    script = ArchScript().explode("body", 1.5, at=0, duration=1).orbit(45, at=0, duration=1)
    clip = cube(script)
    with ArchSession(clip) as reused:
        initial = np.asarray(reused.frame(0)).copy()
        changed = np.asarray(reused.frame(1)).copy()
        assert not np.array_equal(initial, changed)
        for time in (0.4, 1, 0, 0.75):
            actual = reused.frame(time)
            with ArchSession(clip) as fresh:
                assert np.array_equal(actual, fresh.frame(time))
