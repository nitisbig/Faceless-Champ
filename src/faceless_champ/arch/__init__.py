"""Technical 3D visualization and deterministic demonstrations with PyVista."""

from .blueprint import blueprint_from_cad
from .cad import TessellationOptions, mesh_from_cad, parts_from_cad, read_step
from .camera import ArchCamera
from .clip import ArchChamp, validate_design
from .dependencies import geometry_capabilities
from .mechanical import slider_crank_pose
from .mesh import boolean_mesh, inspect_mesh, parts_from_trimesh_scene, repair_mesh, simplify_mesh, to_trimesh
from .model import ArchDataError, ArchDimension, ArchLabel, ArchMesh, ArchPart, ArchStyle
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
