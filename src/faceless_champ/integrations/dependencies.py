"""Optional geometry engines: metadata inspection is separate from native probes."""

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version

from faceless_champ.integrations.pyvista.model import ArchDataError

__all__ = ["geometry_capabilities"]


def _require(module, extra):
    try:
        return import_module(module)
    except (ImportError, OSError) as exc:
        raise ArchDataError("dependency", f"Install faceless-champ[{extra}]; cannot load {module}: {exc}") from exc


def _versions(*names):
    result = {}
    for name in names:
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            result[name] = None
    return result


def geometry_capabilities(*, cad=False, geometry=False):
    """Report optional versions without imports; explicit probes create no GL window."""
    versions = _versions(
        "pyvista",
        "vtk",
        "numpy",
        "build123d",
        "cadquery-ocp-novtk",
        "cadquery-ocp",
        "trimesh",
        "scipy",
        "networkx",
        "manifold3d",
        "fast-simplification",
    )
    result = {"versions": versions, "probes": {}, "ok": True}
    for name, requested in (("cad", cad), ("geometry", geometry)):
        if not requested:
            continue
        try:
            if name == "cad":
                from faceless_champ.integrations.build123d import _engine, mesh_from_cad

                engine = _engine()
                mesh = mesh_from_cad(engine.Box(1, 2, 3))
                count = mesh.dataset.n_cells
            else:
                from faceless_champ.integrations.trimesh import inspect_mesh

                engine = _require("trimesh", "geometry")
                count = inspect_mesh(engine.creation.box())["faces"]
            result["probes"][name] = {"ok": True, "faces": count}
        except (ArchDataError, RuntimeError, ValueError) as exc:
            result["probes"][name] = {"ok": False, "error": str(exc)}
            result["ok"] = False
    return result
