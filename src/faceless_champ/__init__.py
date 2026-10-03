"""Faceless Champ: programmatic animated videos for developers and agents."""

from .animation import Animation, Draw, FadeIn, FadeOut, Typewriter, linear, smooth
from .cli import main as main
from .components import Arrow, Canvas, Circle, Component, Icon, Image, Line, Rectangle, Square, Text, Triangle
from .export import ExportSettings, render
from .renderer import PillowRenderer, Renderer
from .subtitles import Captions, SubtitleCue, SubtitleTrack
from .timeline import Grid, Scene, Sequence

__all__ = [
    "Animation",
    "Arrow",
    "Canvas",
    "Captions",
    "Circle",
    "Component",
    "Draw",
    "ExportSettings",
    "FadeIn",
    "FadeOut",
    "Grid",
    "Icon",
    "Image",
    "Line",
    "PillowRenderer",
    "Rectangle",
    "Renderer",
    "Scene",
    "Sequence",
    "Square",
    "SubtitleCue",
    "SubtitleTrack",
    "Text",
    "Triangle",
    "Typewriter",
    "linear",
    "render",
    "smooth",
]
__version__ = "0.1.0"
