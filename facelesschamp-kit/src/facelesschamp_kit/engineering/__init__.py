"""Engineering authoring over optional Core geometry and native rendering."""

from faceless_champ.integrations.build123d import TessellationOptions, mesh_from_cad, parts_from_cad, read_step
from faceless_champ.integrations.dependencies import geometry_capabilities
from faceless_champ.integrations.pyvista import ArchCamera, ArchDataError, ArchMesh, ArchPart, ArchStyle
from faceless_champ.integrations.trimesh import (
    boolean_mesh,
    inspect_mesh,
    parts_from_trimesh_scene,
    repair_mesh,
    simplify_mesh,
    to_trimesh,
)

from .annotations import ArchDimension, ArchLabel
from .blueprint import blueprint_from_cad
from .clip import ArchChamp, validate_design
from .mechanisms import slider_crank_pose
from .script import ArchScript

__all__ = [
    "ArchCamera",
    "ArchChamp",
    "ArchDataError",
    "ArchDimension",
    "ArchLabel",
    "ArchMesh",
    "ArchPart",
    "ArchScript",
    "ArchStyle",
    "TessellationOptions",
    "blueprint_from_cad",
    "boolean_mesh",
    "geometry_capabilities",
    "inspect_mesh",
    "mesh_from_cad",
    "parts_from_cad",
    "parts_from_trimesh_scene",
    "read_step",
    "repair_mesh",
    "simplify_mesh",
    "slider_crank_pose",
    "to_trimesh",
    "validate_design",
]
