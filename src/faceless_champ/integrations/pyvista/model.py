"""Validated, immutable geometry and presentation inputs for ArchChamp."""

import hashlib
import json
import math
from dataclasses import dataclass, fields
from pathlib import Path

from PIL import ImageColor


class ArchDataError(ValueError):
    def __init__(self, field, message):
        self.field = field
        super().__init__(f"{field}: {message}")


def number(value, name, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ArchDataError(name, "expected a finite number")
    if minimum is not None and value < minimum:
        raise ArchDataError(name, f"must be >= {minimum}")
    return float(value)


def vector(value, name):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ArchDataError(name, "expected three coordinates")
    return tuple(number(v, name) for v in value)


def text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ArchDataError(name, "expected nonempty text")
    return value


def color(value):
    try:
        ImageColor.getcolor(value, "RGBA")
    except (ValueError, TypeError) as exc:
        raise ArchDataError("color", "expected a Pillow color string") from exc
    return value


def construct(cls, value):
    if not isinstance(value, dict) or set(value) - {f.name for f in fields(cls)}:
        raise ArchDataError(cls.__name__, "unknown fields or expected an object")
    try:
        return cls(**value)
    except TypeError as exc:
        raise ArchDataError(cls.__name__, str(exc)) from exc


def pyvista():
    try:
        import pyvista as pv
    except (ImportError, OSError) as exc:
        raise ArchDataError(
            "dependency",
            f"Install faceless-champ[3d] (or facelesschamp-kit[3d]/facelesschamp-agent[3d]); cannot load PyVista: {exc}",
        ) from exc
    return pv


class ArchMesh:
    """Sealed geometry snapshot. ``dataset`` returns an independent inspection copy."""

    def __setattr__(self, name, value):
        if getattr(self, "_sealed", False):
            raise AttributeError("ArchMesh is immutable; create a new snapshot")
        object.__setattr__(self, name, value)

    def __init__(self, dataset, *, source=None, provenance=None):
        pv = pyvista()
        import numpy as np

        if not isinstance(dataset, pv.DataSet) or dataset.n_points == 0:
            raise ArchDataError("mesh", "expected a nonempty dataset; split MultiBlock into named parts")
        if not np.isfinite(dataset.points).all():
            raise ArchDataError("mesh.points", "coordinates must be finite")
        self._dataset = dataset.copy(deep=True)
        self.source = str(source) if source else None
        try:
            self._provenance_json = json.dumps(
                {} if provenance is None else provenance, sort_keys=True, allow_nan=False
            )
            if not isinstance(json.loads(self._provenance_json), dict):
                raise TypeError("expected an object")
        except (ValueError, TypeError) as exc:
            raise ArchDataError("provenance", "expected finite JSON metadata") from exc
        h = hashlib.sha256(type(dataset).__name__.encode())
        arrays = [("points", self._dataset.points)]
        for name in ("cells", "celltypes", "faces", "lines", "verts", "strips", "dimensions", "spacing", "origin"):
            value = getattr(self._dataset, name, None)
            if value is not None:
                arrays.append((name, value))
        for group in ("point_data", "cell_data", "field_data"):
            for name in sorted(getattr(self._dataset, group)):
                arrays.append((f"{group}:{name}", getattr(self._dataset, group)[name]))
        for name, value in arrays:
            a = np.asarray(value)
            if a.dtype.kind in "fci" and not np.isfinite(a).all():
                raise ArchDataError(name, "values must be finite")
            h.update(name.encode())
            h.update(str((a.dtype.str, a.shape)).encode())
            h.update(a.tobytes() if a.dtype.kind != "O" else repr(a.tolist()).encode())
        self.fingerprint = h.hexdigest()
        self._sealed = True

    @classmethod
    def from_data(cls, data, *, provenance=None):
        """Wrap PyVista, VTK, XYZ NumPy, trimesh or meshio geometry, then copy it."""
        try:
            return cls(pyvista().wrap(data), provenance=provenance)
        except ArchDataError:
            raise
        except (TypeError, ValueError, ImportError) as exc:
            raise ArchDataError("mesh", str(exc)) from exc

    from_pyvista = from_data

    @classmethod
    def from_file(cls, path):
        path = Path(path)
        if not path.is_file():
            raise ArchDataError("mesh.file", f"file not found: {path}")
        try:
            return cls(pyvista().read(path), source=path.resolve())
        except ArchDataError:
            raise
        except (OSError, ValueError, TypeError) as exc:
            raise ArchDataError("mesh.file", str(exc)) from exc

    @classmethod
    def from_arrays(cls, points, faces=None, *, point_data=None, cell_data=None, provenance=None):
        pv = pyvista()
        import numpy as np

        points = np.asarray(points, dtype=float)
        if points.ndim != 2 or points.shape[1] != 3 or not len(points) or not np.isfinite(points).all():
            raise ArchDataError("points", "expected nonempty finite N x 3 coordinates")
        flat = None
        if faces is not None:
            rows = np.asarray(faces)
            if rows.dtype.kind not in "iu" or rows.ndim not in (1, 2):
                raise ArchDataError("faces", "expected integer polygons or VTK connectivity")
            if rows.ndim == 2:
                rows = np.column_stack((np.full(len(rows), rows.shape[1]), rows))
            flat = rows.ravel()
            cursor = 0
            while cursor < len(flat):
                count = int(flat[cursor])
                ids = flat[cursor + 1 : cursor + 1 + count]
                if count < 3 or len(ids) != count or (ids < 0).any() or (ids >= len(points)).any():
                    raise ArchDataError("faces", "invalid polygon connectivity")
                cursor += count + 1
        mesh = pv.PolyData(points, faces=flat) if flat is not None else pv.PolyData(points)
        for group, arrays, size in (
            (mesh.point_data, point_data, mesh.n_points),
            (mesh.cell_data, cell_data, mesh.n_cells),
        ):
            for name, values in (arrays or {}).items():
                a = np.asarray(values)
                if a.ndim == 0 or len(a) != size:
                    raise ArchDataError(name, "field length differs from point/cell count")
                group[name] = a.copy()
        return cls(mesh, provenance=provenance)

    @property
    def provenance(self):
        """Independent JSON metadata; never contains mutable native CAD objects."""
        return json.loads(self._provenance_json)

    @property
    def dataset(self):
        return self._dataset.copy(deep=True)

    def __deepcopy__(self, memo):
        return self  # Private snapshot is never mutated by authoring or filters.


CONCEPTS = (
    "clay",
    "solid",
    "wireframe",
    "topology",
    "transparent",
    "xray",
    "blueprint",
    "points",
    "isometric",
    "heatmap",
    "voxel",
)


@dataclass(frozen=True)
class ArchStyle:
    concept: str = "clay"
    color: str = "#d7e2ee"
    edge_color: str = "#63d3ff"
    opacity: float = 1
    line_width: float = 1.5
    point_size: float = 5
    scalars: str | None = None
    vectors: str | None = None
    field_mode: str = "glyphs"
    clim: tuple | None = None
    cmap: str = "viridis"
    association: str = "point"
    voxel_spacing: float = 0.15
    smooth_shading: bool = True

    def __post_init__(self):
        if self.concept not in CONCEPTS:
            raise ArchDataError("concept", f"expected one of {CONCEPTS}")
        color(self.color)
        color(self.edge_color)
        if not 0 <= number(self.opacity, "opacity") <= 1:
            raise ArchDataError("opacity", "must be between 0 and 1")
        for name in ("line_width", "point_size", "voxel_spacing"):
            number(getattr(self, name), name, 0.000001)
        if self.field_mode not in {"glyphs", "streamlines"} or self.association not in {"point", "cell"}:
            raise ArchDataError("field", "invalid mode or association")
        if not isinstance(self.smooth_shading, bool):
            raise ArchDataError("smooth_shading", "expected boolean")
        for name in ("scalars", "vectors"):
            if getattr(self, name) is not None:
                text(getattr(self, name), name)
        text(self.cmap, "cmap")
        if self.clim is not None:
            if len(self.clim) != 2 or number(self.clim[0], "clim") >= number(self.clim[1], "clim"):
                raise ArchDataError("clim", "expected increasing range")
            object.__setattr__(self, "clim", tuple(self.clim))


@dataclass(frozen=True)
class ArchPart:
    id: str
    mesh: ArchMesh
    position: tuple = (0, 0, 0)
    rotation: tuple = (0, 0, 0)
    scale: float = 1
    style: ArchStyle | None = None
    explode_vector: tuple = (0, 0, 1)

    def __post_init__(self):
        text(self.id, "part.id")
        if self.id == "camera" or not isinstance(self.mesh, ArchMesh):
            raise ArchDataError("part", "reserved ID or expected ArchMesh")
        for key in ("position", "rotation", "explode_vector"):
            object.__setattr__(self, key, vector(getattr(self, key), key))
        number(self.scale, "scale", 0.000001)
        if self.style is not None and not isinstance(self.style, ArchStyle):
            raise ArchDataError("style", "expected ArchStyle")
