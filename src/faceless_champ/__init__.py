"""Faceless Champ: programmatic animated videos for developers and agents."""

from .animation import Animation, Draw, FadeIn, FadeOut, Typewriter, linear, smooth
from .cli import main as main
from .components import Canvas, Circle, Component, Image, Line, Rectangle, Square, Text, Triangle
from .export import ExportSettings, render
from .renderer import PillowRenderer, Renderer
from .timeline import Grid, Scene, Sequence

__all__ = [
    "Animation",
    "Canvas",
    "Circle",
    "Component",
    "Draw",
    "ExportSettings",
    "FadeIn",
    "FadeOut",
    "Grid",
    "Image",
    "Line",
    "PillowRenderer",
    "Rectangle",
    "Renderer",
    "Scene",
    "Sequence",
    "Square",
    "Text",
    "Triangle",
    "Typewriter",
    "linear",
    "render",
    "smooth",
]
__version__ = "0.1.0"
