"""Deprecated Core-local geometry aliases; engineering authoring moved to Kit."""

from ..integrations.build123d import TessellationOptions, mesh_from_cad, parts_from_cad, read_step
from ..integrations.dependencies import geometry_capabilities
from ..integrations.pyvista import ArchCamera, ArchDataError, ArchMesh, ArchPart, ArchStyle
from ..integrations.trimesh import (
    boolean_mesh,
    inspect_mesh,
    parts_from_trimesh_scene,
    repair_mesh,
    simplify_mesh,
    to_trimesh,
)

__all__ = [
    "ArchCamera",
    "ArchDataError",
    "ArchMesh",
    "ArchPart",
    "ArchStyle",
    "TessellationOptions",
    "boolean_mesh",
    "geometry_capabilities",
    "inspect_mesh",
    "mesh_from_cad",
    "parts_from_cad",
    "parts_from_trimesh_scene",
    "read_step",
    "repair_mesh",
    "simplify_mesh",
    "to_trimesh",
]


def __getattr__(name):
    from importlib import import_module

    aliases = {
        "cad": "build123d",
        "mesh": "trimesh",
        "dependencies": "dependencies",
        "model": "pyvista.model",
        "camera": "pyvista.camera",
        "rendering": "pyvista.rendering",
    }
    if name in aliases:
        return import_module("faceless_champ.integrations." + aliases[name])
    raise AttributeError(
        f"{name} moved from faceless_champ.arch to facelesschamp_kit.engineering; see docs/v2/m4-migration.md"
    )
