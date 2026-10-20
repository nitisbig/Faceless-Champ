"""Explicit, copy-on-processing Trimesh interoperability for ArchChamp.

Topology-changing operations reject supplied fields unless drop_fields=True.
Rendering continues to use the existing PyVista pipeline.
"""

from .dependencies import _require, _versions
from .model import ArchDataError, ArchMesh, ArchPart, number

__all__ = ["boolean_mesh", "inspect_mesh", "parts_from_trimesh_scene", "repair_mesh", "simplify_mesh", "to_trimesh"]


def to_trimesh(mesh, *, drop_fields=False):
    """Return an independent triangular surface; reject unacknowledged field loss."""
    tm = _require("trimesh", "geometry")
    if isinstance(mesh, tm.Trimesh):
        import numpy as np

        if not drop_fields and (mesh.vertex_attributes or mesh.face_attributes or mesh.visual.kind is not None):
            raise ArchDataError("fields", "processing does not preserve custom arrays/materials; use drop_fields=True")
        if not len(mesh.vertices) or not len(mesh.faces) or not np.isfinite(mesh.vertices).all():
            raise ArchDataError("mesh", "expected a nonempty finite triangle mesh")
        if mesh.faces.min() < 0 or mesh.faces.max() >= len(mesh.vertices):
            raise ArchDataError("faces", "invalid vertex indices")
        return mesh.copy()
    if not isinstance(mesh, ArchMesh):
        raise ArchDataError("mesh", "expected ArchMesh or trimesh.Trimesh")
    data = mesh.dataset
    fields = set(data.point_data) | set(data.cell_data) | set(data.field_data)
    fields -= {"Normals", "vtkOriginalPointIds", "vtkOriginalCellIds", "_PYVISTA_USER_DICT"}
    if fields and not drop_fields:
        raise ArchDataError("fields", "Trimesh conversion drops supplied arrays; use drop_fields=True explicitly")
    data = data.extract_surface(algorithm="dataset_surface").triangulate()
    if not data.n_cells or data.n_lines or data.n_verts:
        raise ArchDataError("mesh", "expected a triangular surface without lines or point cells")
    return tm.Trimesh(data.points.copy(), data.faces.reshape(-1, 4)[:, 1:].copy(), process=False)


def inspect_mesh(mesh):
    """Inspect topology and mass properties; open surfaces have no solid volume."""
    import numpy as np

    value = to_trimesh(mesh, drop_fields=True)
    tm = _require("trimesh", "geometry")
    _require("scipy", "geometry")
    valid = bool(np.isfinite(value.vertices).all())
    watertight = bool(value.is_watertight)
    winding = bool(value.is_winding_consistent)
    return {
        "vertices": len(value.vertices),
        "faces": len(value.faces),
        "finite": valid,
        "degenerate_faces": int((~value.nondegenerate_faces()).sum()),
        "watertight": watertight,
        "winding_consistent": winding,
        "components": len(
            tm.graph.connected_components(value.face_adjacency, nodes=np.arange(len(value.faces)), engine="scipy")
        ),
        "area": float(value.area),
        "volume": float(value.volume) if valid and value.is_volume else None,
        "bounds": value.bounds.tolist(),
    }


def _snapshot(value, source, operation, **settings):
    if not len(value.vertices) or not len(value.faces):
        raise ArchDataError("geometry", "operation produced an empty surface")
    provenance = source.provenance if isinstance(source, ArchMesh) else {}
    engines = ["trimesh", "numpy"]
    engines += (
        ["scipy", "networkx"]
        if operation == "repair"
        else ["scipy", "fast-simplification"]
        if operation == "simplify"
        else ["manifold3d"]
    )
    provenance = {
        **provenance,
        "versions": {
            **provenance.get("versions", {}),
            **{k: v for k, v in _versions(*engines).items() if v},
        },
    }
    provenance["processing"] = [*provenance.get("processing", []), {"operation": operation, **settings}]
    return ArchMesh.from_arrays(value.vertices, value.faces, provenance=provenance)


def repair_mesh(mesh, *, merge_vertices=False, fill_holes=False, drop_fields=False):
    """Remove duplicate/degenerate faces and fix winding; optionally weld/fill small holes.

    Trimesh hole filling handles small boundary loops, not arbitrary damaged solids.
    Use inspect_mesh on the result to assess remaining defects.
    """
    tm = _require("trimesh", "geometry")
    _require("networkx", "geometry")
    value = to_trimesh(mesh, drop_fields=drop_fields)
    value.update_faces(value.unique_faces() & value.nondegenerate_faces())
    value.remove_unreferenced_vertices()
    if merge_vertices:
        value.merge_vertices()
    tm.repair.fix_normals(value, multibody=True)
    if fill_holes:
        tm.repair.fill_holes(value)
    return _snapshot(
        value, mesh, "repair", merge_vertices=merge_vertices, fill_holes=fill_holes, drop_fields=drop_fields
    )


def simplify_mesh(mesh, target_faces, *, drop_fields=False):
    """Explicit quadric decimation; report resulting error against the source separately."""
    if isinstance(target_faces, bool) or not isinstance(target_faces, int) or target_faces < 4:
        raise ArchDataError("target_faces", "expected integer >= 4")
    _require("fast_simplification", "geometry-advanced")
    value = to_trimesh(mesh, drop_fields=drop_fields)
    before = float(value.volume) if value.is_volume else None
    result = (
        value.copy() if target_faces >= len(value.faces) else value.simplify_quadric_decimation(face_count=target_faces)
    )
    after = float(result.volume) if result.is_volume else None
    import numpy as np

    scipy = _require("scipy.spatial", "geometry")
    ids = np.linspace(0, len(value.vertices) - 1, min(1024, len(value.vertices)), dtype=int)
    distances, _ = scipy.cKDTree(result.vertices).query(value.vertices[ids])
    return _snapshot(
        result,
        mesh,
        "simplify",
        target_faces=target_faces,
        drop_fields=drop_fields,
        source_faces=len(value.faces),
        source_volume=before,
        result_volume=after,
        result_faces=len(result.faces),
        sampled_vertex_distance_max=float(distances.max()),
        vertex_distance_samples=len(ids),
    )


def boolean_mesh(meshes, operation="union", *, drop_fields=False):
    """Mesh solid boolean using the explicitly selected Manifold engine."""
    tm = _require("trimesh", "geometry")
    _require("manifold3d", "geometry-advanced")
    if operation not in {"union", "difference", "intersection"}:
        raise ArchDataError("operation", "expected union, difference or intersection")
    meshes = tuple(meshes)
    if len(meshes) < 2:
        raise ArchDataError("meshes", "provide at least two solids")
    units = {m.provenance.get("units") for m in meshes if isinstance(m, ArchMesh)} - {None}
    if len(units) > 1:
        raise ArchDataError("units", "boolean inputs must use the same units")
    values = [to_trimesh(m, drop_fields=drop_fields) for m in meshes]
    if any(not m.is_volume for m in values):
        raise ArchDataError("mesh", "booleans require watertight, consistently wound positive volumes")
    try:
        value = getattr(tm.boolean, operation)(values, engine="manifold", check_volume=True)
    except (ValueError, RuntimeError) as exc:
        raise ArchDataError("geometry.boolean", str(exc)) from exc
    return _snapshot(
        value,
        meshes[0],
        operation,
        inputs=[m.fingerprint if isinstance(m, ArchMesh) else ArchMesh.from_data(m).fingerprint for m in meshes],
        drop_fields=drop_fields,
    )


def parts_from_trimesh_scene(scene, *, scale=1, drop_fields=False):
    """Preserve named instances; bake arbitrary affine transforms on copied arrays."""
    import numpy as np

    tm = _require("trimesh", "geometry")
    if not isinstance(scene, tm.Scene):
        raise ArchDataError("scene", "expected trimesh.Scene")
    scale = number(scale, "scale", 1e-12)
    parts, cache = [], {}
    for node in sorted(scene.graph.nodes_geometry):
        matrix, name = scene.graph[node]
        matrix = np.asarray(matrix, dtype=float)
        if (
            matrix.shape != (4, 4)
            or not np.isfinite(matrix).all()
            or not np.allclose(matrix[3], (0, 0, 0, 1))
            or abs(np.linalg.det(matrix[:3, :3])) < 1e-15
        ):
            raise ArchDataError("transform", "expected finite invertible affine transform")
        source = scene.geometry[name]
        if not isinstance(source, tm.Trimesh):
            raise ArchDataError("scene", "only triangle mesh scene nodes are supported")
        key = name, matrix[:3, :3].tobytes(), scale
        if key not in cache:
            value = to_trimesh(source, drop_fields=drop_fields)
            transform = matrix.copy()
            transform[:3, 3] = 0
            value.apply_transform(transform)
            value.vertices *= scale
            cache[key] = ArchMesh.from_data(
                value,
                provenance={
                    "generator": "trimesh.Scene",
                    "versions": _versions("trimesh"),
                    "scale": scale,
                    "drop_fields": drop_fields,
                },
            )
        part = ArchPart(str(node), cache[key], position=tuple(matrix[:3, 3] * scale))
        parts.append(part)
    if not parts:
        raise ArchDataError("scene", "scene contains no triangle meshes")
    return tuple(parts)
