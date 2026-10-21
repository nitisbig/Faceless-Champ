"""Structured authoring over the independent faceless-champ video engine."""

from .blocks import Block, BlockBuild
from .blocks.effects import EffectBlock, ParticleBackdrop, ProceduralBackdrop
from .capabilities import public_capabilities
from .compiler import CompiledVideo
from .context import BuildContext
from .diagnostics import KitError
from .project import Project
from .recipes import RecipeEvent, RecipeSpec, apply_recipe, recipe_specs, validate_recipe
from .rendering import ExportProgress, media_probe, validate_rendering
from .subtitles import read_subtitle_cues
from .themes import CLEAN_FLOW, Theme
from .tutorials import CodingTutorialStyle, CodingTutorialTemplate
from .video import Segment, Video

__version__ = "2.0.0rc1"
__all__ = ["Block", "BlockBuild", "BuildContext", "CompiledVideo", "KitError", "Project", "Segment", "Video"]
__all__ += ["RecipeEvent", "RecipeSpec", "apply_recipe", "recipe_specs", "validate_recipe"]
__all__ += ["CLEAN_FLOW", "Theme"]
__all__ += ["CodingTutorialStyle", "CodingTutorialTemplate"]
__all__ += ["EffectBlock", "ParticleBackdrop", "ProceduralBackdrop"]

__all__ += ["read_subtitle_cues"]
__all__ += ["ExportProgress", "media_probe", "public_capabilities", "validate_rendering"]


# Domain APIs retain their names under the owning authoring package.
_DOMAIN_EXPORTS = {
    "Axis": ("charts", "Axis"),
    "BarChart": ("charts", "BarChart"),
    "Chart": ("charts", "Chart"),
    "ChartReveal": ("charts", "ChartReveal"),
    "ChartStyle": ("charts", "ChartStyle"),
    "EarthMap": ("maps", "EarthMap"),
    "Flag": ("maps.flags", "Flag"),
    "Heatmap": ("charts", "Heatmap"),
    "Histogram": ("charts", "Histogram"),
    "LineChart": ("charts", "LineChart"),
    "NetworkGraph": ("charts", "NetworkGraph"),
    "OutlineMap": ("maps", "OutlineMap"),
    "PieChart": ("charts", "PieChart"),
    "RankedBarChart": ("charts", "RankedBarChart"),
    "SankeyChart": ("charts", "SankeyChart"),
    "SatelliteMap": ("maps", "SatelliteMap"),
    "ScatterPlot": ("charts", "ScatterPlot"),
    "VectorField": ("charts", "VectorField"),
    "flag_path": ("maps.flags", "flag_path"),
    "supported_countries": ("maps", "supported_countries"),
    "supported_flags": ("maps.flags", "supported_flags"),
    "CodeReveal": ("coding", "CodeReveal"),
    "CodeTheme": ("coding", "CodeTheme"),
    "CodingChamp": ("coding", "CodingChamp"),
    "CodeWindow": ("coding.workspace", "CodeWindow"),
    "CodeWorkspaceDesign": ("coding.workspace", "CodeWorkspaceDesign"),
    "CanvasItem": ("playground", "CanvasItem"),
    "CodeCheckpoint": ("playground", "CodeCheckpoint"),
    "CodeEditor": ("playground", "CodeEditor"),
    "EditTimeline": ("playground", "EditTimeline"),
    "EventBinding": ("playground", "EventBinding"),
    "PlaygroundCanvas": ("playground", "PlaygroundCanvas"),
    "PlaygroundError": ("playground", "PlaygroundError"),
    "PlaygroundOutput": ("playground", "PlaygroundOutput"),
    "PlaygroundScript": ("playground", "PlaygroundScript"),
    "PreparedPlayground": ("playground", "PreparedPlayground"),
    "ValueBinding": ("playground", "ValueBinding"),
    "prepare_playground": ("playground", "prepare_playground"),
    "FlowChamp": ("diagrams", "FlowChamp"),
    "FlowDataError": ("diagrams", "FlowDataError"),
    "FlowDesign": ("diagrams", "FlowDesign"),
    "FlowEdge": ("diagrams", "FlowEdge"),
    "FlowGraph": ("diagrams", "FlowGraph"),
    "FlowNode": ("diagrams", "FlowNode"),
    "FlowPort": ("diagrams", "FlowPort"),
    "FlowScript": ("diagrams", "FlowScript"),
    "FlowTheme": ("diagrams", "FlowTheme"),
    "FlowVisual": ("diagrams", "FlowVisual"),
    "ArchChamp": ("engineering.clip", "ArchChamp"),
    "ArchDimension": ("engineering.annotations", "ArchDimension"),
    "ArchLabel": ("engineering.annotations", "ArchLabel"),
    "ArchScript": ("engineering.script", "ArchScript"),
    "EquationTransform": ("mathematics", "EquationTransform"),
}
__all__ += list(_DOMAIN_EXPORTS)


def __getattr__(name):
    from importlib import import_module

    if name not in _DOMAIN_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attribute = _DOMAIN_EXPORTS[name]
    value = getattr(import_module("." + module, __name__), attribute)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
