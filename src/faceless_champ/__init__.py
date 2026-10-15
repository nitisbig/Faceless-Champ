"""Faceless Champ: programmatic animated videos for developers and agents."""

from .animation import (
    Animation,
    BounceIn,
    ChartReveal,
    Draw,
    FadeIn,
    FadeOut,
    PopIn,
    PopOut,
    Pulse,
    Shake,
    SlideIn,
    SlideOut,
    SpinIn,
    Typewriter,
    Wiggle,
    Write,
    ZoomIn,
    ZoomOut,
    ease_in,
    ease_out,
    linear,
    smooth,
)
from .charts import (
    Axis,
    BarChart,
    Chart,
    ChartStyle,
    Heatmap,
    Histogram,
    LineChart,
    NetworkGraph,
    PieChart,
    RankedBarChart,
    SankeyChart,
    ScatterPlot,
    VectorField,
)
from .cli import main as main
from .colors import COLOR_SCHEMES, ColorScheme, with_alpha
from .components import (
    Arrow,
    Canvas,
    Circle,
    Component,
    Ellipse,
    Equation,
    Icon,
    Image,
    ImageSlot,
    Line,
    Number,
    Polyline,
    Rectangle,
    Square,
    Text,
    Triangle,
)
from .export import ExportSettings, render
from .flags import Flag, flag_path, supported_flags
from .layout import Bounds, Group
from .maps import EarthMap, OutlineMap, SatelliteMap, supported_countries
from .narration import CueScene
from .preview import StoryboardSample, render_storyboard, save_frame
from .renderer import PillowRenderer, Renderer
from .subtitles import Captions, SubtitleCue, SubtitleTrack
from .surfaces import ShadowStyle, card_content_bounds, card_surface, dot_grid
from .timeline import Grid, Layer, Scene, Sequence
from .typography import CLEAN_FLOW_FONT, fit_text

__all__ = [
    "CLEAN_FLOW_FONT",
    "COLOR_SCHEMES",
    "Animation",
    "Arrow",
    "Axis",
    "BarChart",
    "BounceIn",
    "Bounds",
    "Canvas",
    "Captions",
    "Chart",
    "ChartReveal",
    "ChartStyle",
    "Circle",
    "ColorScheme",
    "Component",
    "CueScene",
    "Draw",
    "EarthMap",
    "Ellipse",
    "Equation",
    "ExportSettings",
    "FadeIn",
    "FadeOut",
    "Flag",
    "Grid",
    "Group",
    "Heatmap",
    "Histogram",
    "Icon",
    "Image",
    "ImageSlot",
    "Layer",
    "Line",
    "LineChart",
    "NetworkGraph",
    "Number",
    "OutlineMap",
    "PieChart",
    "PillowRenderer",
    "Polyline",
    "PopIn",
    "PopOut",
    "Pulse",
    "RankedBarChart",
    "Rectangle",
    "Renderer",
    "SankeyChart",
    "SatelliteMap",
    "ScatterPlot",
    "Scene",
    "Sequence",
    "ShadowStyle",
    "Shake",
    "SlideIn",
    "SlideOut",
    "SpinIn",
    "Square",
    "StoryboardSample",
    "SubtitleCue",
    "SubtitleTrack",
    "Text",
    "Triangle",
    "Typewriter",
    "VectorField",
    "Wiggle",
    "Write",
    "ZoomIn",
    "ZoomOut",
    "card_content_bounds",
    "card_surface",
    "dot_grid",
    "ease_in",
    "ease_out",
    "fit_text",
    "flag_path",
    "linear",
    "render",
    "render_storyboard",
    "save_frame",
    "smooth",
    "supported_countries",
    "supported_flags",
    "with_alpha",
]
__version__ = "0.1.5"

from .indicators import Checkmark, Countdown, Gauge, LoadingDots, ProgressBar, ProgressRing
from .masks import CircleMask, RectangleMask, ShapeMask, Wipe
from .scheduling import Repeat, Stagger, Succession

__all__ += [
    "Checkmark",
    "CircleMask",
    "Countdown",
    "Gauge",
    "LoadingDots",
    "ProgressBar",
    "ProgressRing",
    "RectangleMask",
    "Repeat",
    "ShapeMask",
    "Stagger",
    "Succession",
    "Wipe",
]

from .coding import CodeReveal, CodeTheme, CodingChamp

__all__ += ["CodeReveal", "CodeTheme", "CodingChamp"]

from .coding_workspace import CodeWindow, CodeWorkspaceDesign

__all__ += ["CodeWindow", "CodeWorkspaceDesign"]

from .chess import ChessAssets, ChessChamp, ChessScript, ChessTheme

__all__ += ["ChessAssets", "ChessChamp", "ChessScript", "ChessTheme"]

from .playground import (
    CanvasItem,
    CodeCheckpoint,
    CodeEditor,
    EditTimeline,
    EventBinding,
    PlaygroundCanvas,
    PlaygroundError,
    PlaygroundOutput,
    PlaygroundScript,
    PreparedPlayground,
    ValueBinding,
    prepare_playground,
)

__all__ += [
    "CanvasItem",
    "CodeCheckpoint",
    "CodeEditor",
    "EditTimeline",
    "EventBinding",
    "PlaygroundCanvas",
    "PlaygroundError",
    "PlaygroundOutput",
    "PlaygroundScript",
    "PreparedPlayground",
    "ValueBinding",
    "prepare_playground",
]

from .flow import FlowChamp, FlowDataError, FlowEdge, FlowGraph, FlowNode, FlowPort, FlowScript, FlowTheme

__all__ += ["FlowChamp", "FlowDataError", "FlowEdge", "FlowGraph", "FlowNode", "FlowPort", "FlowScript", "FlowTheme"]

from .arch import (
    ArchCamera,
    ArchChamp,
    ArchDataError,
    ArchDimension,
    ArchLabel,
    ArchMesh,
    ArchPart,
    ArchScript,
    ArchStyle,
)

__all__ += [
    "ArchCamera",
    "ArchChamp",
    "ArchDataError",
    "ArchDimension",
    "ArchLabel",
    "ArchMesh",
    "ArchPart",
    "ArchScript",
    "ArchStyle",
]
