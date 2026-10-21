"""Optional build123d/OCCT bridge with explicit units and absolute tessellation.

All native CAD state stays in preparation. Only immutable ArchMesh snapshots enter
scenes and the isolated VTK renderer. No Trimesh dependency is needed here.
"""

import hashlib
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from faceless_champ.integrations.dependencies import _require, _versions
from faceless_champ.integrations.pyvista.model import ArchDataError, ArchMesh, ArchPart, number

__all__ = ["TessellationOptions", "mesh_from_cad", "parts_from_cad", "read_step"]

_UNITS = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "ft": 304.8}


def _unit_scale(source, target):
    if not isinstance(source, str) or not isinstance(target, str) or source not in _UNITS or target not in _UNITS:
        raise ArchDataError("units", "use mm, cm, m, in or ft explicitly")
    return _UNITS[source] / _UNITS[target]


def _engine():
    if not (3, 12) <= sys.version_info[:2] < (3, 15):
        raise ArchDataError("dependency", "this CAD integration supports Python 3.12 through 3.14")
    versions = _versions("cadquery-ocp", "cadquery-ocp-novtk")
    if all(versions.values()):
        raise ArchDataError("dependency", "conflicting OCP providers: use cadquery-ocp-novtk without cadquery-ocp")
    return _require("build123d", "cad")


def _detached(shape):
    # Copy only native geometry. deepcopy(leaf) also traverses its anytree parent,
    # siblings and arbitrary Python attributes, turning an assembly into O(n²)
    # native copies and retaining unrelated authoring objects.
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy

    return shape.cast(BRepBuilderAPI_Copy(shape.wrapped).Shape())


@dataclass(frozen=True)
class TessellationOptions:
    """Absolute linear/weld deflections are in source units; angular deflection is radians.

    The triangle budget bounds extracted output, not allocations internal to OCCT.
    """

    linear_deflection: float = 0.05
    angular_deflection: float = 0.1
    weld_tolerance: float = 1e-7
    max_triangles: int = 1_000_000

    def __post_init__(self):
        number(self.linear_deflection, "linear_deflection", 1e-9)
        angle = number(self.angular_deflection, "angular_deflection", 1e-9)
        if angle > math.pi:
            raise ArchDataError("angular_deflection", "must be <= pi radians")
        weld = number(self.weld_tolerance, "weld_tolerance", 0)
        if weld > self.linear_deflection * 0.01:
            raise ArchDataError("weld_tolerance", "must be <= one percent of linear_deflection")
        if isinstance(self.max_triangles, bool) or not isinstance(self.max_triangles, int) or self.max_triangles < 1:
            raise ArchDataError("max_triangles", "expected positive integer")


def mesh_from_cad(shape, *, options=None, source_units="mm", target_units="mm", provenance=None):
    """Tessellate a detached native Shape using serial absolute OCCT meshing."""
    bd = _engine()
    import numpy as np

    if not isinstance(shape, bd.Shape) or shape.wrapped is None:
        raise ArchDataError("cad.shape", "expected a nonempty build123d Shape")
    options = TessellationOptions() if options is None else options
    if not isinstance(options, TessellationOptions):
        raise ArchDataError("tessellation", "expected TessellationOptions")
    factor = _unit_scale(source_units, target_units)
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRepTools import BRepTools
    from OCP.TopAbs import TopAbs_Orientation
    from OCP.TopLoc import TopLoc_Location

    try:
        copied = _detached(shape)
        if not copied.is_valid:
            raise ArchDataError("cad.shape", "CAD shape is invalid")
        BRepTools.Clean_s(copied.wrapped)
        mesher = BRepMesh_IncrementalMesh(
            copied.wrapped, options.linear_deflection, False, options.angular_deflection, False
        )
        if not mesher.IsDone():
            raise ArchDataError("cad.tessellation", "OCCT meshing failed")
        points, faces = [], []
        for face in copied.faces():
            location = TopLoc_Location()
            triangles = BRep_Tool.Triangulation_s(face.wrapped, location)
            if triangles is None:
                raise ArchDataError("cad.tessellation", "face has no triangulation")
            if len(faces) + triangles.NbTriangles() > options.max_triangles:
                raise ArchDataError("cad.budget", "triangle budget exceeded; increase deflection or explicit budget")
            offset = len(points)
            for i in range(1, triangles.NbNodes() + 1):
                p = triangles.Node(i).Transformed(location.Transformation())
                points.append((p.X(), p.Y(), p.Z()))
            reverse = face.wrapped.Orientation() == TopAbs_Orientation.TopAbs_REVERSED
            for triangle in triangles.Triangles():
                a, b, c = (triangle.Value(i) - 1 + offset for i in (1, 2, 3))
                faces.append((a, c, b) if reverse else (a, b, c))
        if not faces:
            raise ArchDataError("cad.shape", "expected geometry with faces")
        # Merge face seams on a detached VTK dataset, preserving sharp face normals
        # for the renderer to compute without compromising topological closure.
        mesh = ArchMesh.from_arrays(points, faces).dataset
        mesh = mesh.clean(tolerance=options.weld_tolerance, absolute=True)
        mesh.points = np.asarray(mesh.points, dtype=float) * factor
        record = {
            **getattr(shape, "_faceless_provenance", {}),
            **(provenance or {}),
            "generator": "build123d",
            "source_units": source_units,
            "units": target_units,
            "tessellation": asdict(options),
            "versions": _versions("build123d", "cadquery-ocp-novtk", "numpy", "pyvista", "vtk"),
        }
        return ArchMesh(mesh, provenance=record)
    except ArchDataError:
        raise
    except (ValueError, RuntimeError, TypeError) as exc:
        raise ArchDataError("cad.tessellation", str(exc)) from exc


def parts_from_cad(shape, *, options=None, source_units="mm", target_units="mm", provenance=None):
    """Flatten a native assembly, preserving local geometry and accumulated locations.

    Repeated native solids share a mesh snapshot within this conversion. Duplicate
    and missing labels receive deterministic sibling suffixes.
    """
    bd = _engine()
    import numpy as np

    if not isinstance(shape, bd.Shape) or shape.wrapped is None:
        raise ArchDataError("cad.shape", "expected a nonempty build123d Shape")
    factor = _unit_scale(source_units, target_units)
    provenance = {**getattr(shape, "_faceless_provenance", {}), **(provenance or {})}
    parts, cache = [], []
    budget = options or TessellationOptions()
    if not isinstance(budget, TessellationOptions):
        raise ArchDataError("tessellation", "expected TessellationOptions")
    triangle_count = 0

    def visit(node, prefix, parent):
        nonlocal triangle_count
        matrix = (
            parent @ np.asarray(bd.Matrix(node.location.wrapped.Transformation()).transposed_list()).reshape(4, 4).T
        )
        children = tuple(node.children)
        if children:
            used = set()
            for i, child in enumerate(children):
                base = child.label.strip().replace("/", "_") or f"part-{i}"
                name, suffix = base, 2
                while name in used or name == "camera":
                    name = f"{base}-{suffix}"
                    suffix += 1
                used.add(name)
                visit(child, f"{prefix}/{name}" if prefix else name, matrix)
            return
        mesh = next(
            (
                mesh
                for native, mesh in cache
                if native.IsPartner(node.wrapped) and native.Orientation() == node.wrapped.Orientation()
            ),
            None,
        )
        if mesh is None:
            from dataclasses import replace

            remaining = budget.max_triangles - triangle_count
            if remaining < 1:
                raise ArchDataError("cad.budget", "assembly triangle budget exceeded")
            local = _detached(node)
            local.location = bd.Location()
            mesh = mesh_from_cad(
                local,
                options=replace(budget, max_triangles=remaining),
                source_units=source_units,
                target_units=target_units,
                provenance=provenance,
            )
            cache.append((node.wrapped, mesh))
        triangle_count += mesh._dataset.n_cells
        if triangle_count > budget.max_triangles:
            raise ArchDataError("cad.budget", "assembly triangle budget exceeded")
        # build123d exposes intrinsic XYZ angles; ArchChamp uses Rz @ Ry @ Rx.
        # Extract that convention directly from the accumulated rigid matrix.
        from faceless_champ.integrations.geometry import _euler_xyz

        parts.append(
            ArchPart(
                prefix or (node.label if node.label and node.label != "camera" else "model"),
                mesh,
                position=tuple(matrix[:3, 3] * factor),
                rotation=_euler_xyz(matrix[:3, :3]),
            )
        )

    visit(shape, "", np.eye(4))
    if not parts:
        raise ArchDataError("cad.shape", "assembly has no renderable leaves")
    return tuple(parts)


def read_step(path):
    """Read a local STEP assembly in build123d's millimetre coordinate convention."""
    bd = _engine()
    path = Path(path)
    if not path.is_file() or path.suffix.lower() not in {".step", ".stp"}:
        raise ArchDataError("cad.file", "provide an existing .step or .stp file")
    try:
        shape = bd.import_step(path)
        shape._faceless_provenance = _file_provenance(path)
        return shape
    except (ValueError, RuntimeError, OSError) as exc:
        raise ArchDataError("cad.file", str(exc)) from exc


def _file_provenance(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return {"source_checksum": h.hexdigest()}
