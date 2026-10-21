"""Optional preparation-only Manim Community integration."""

from .model import ManimError, ManimRenderOptions, ManimSceneSpec
from .prepare import load_manim, manim_capabilities, prepare_manim

__all__ = ["ManimError", "ManimRenderOptions", "ManimSceneSpec", "load_manim", "manim_capabilities", "prepare_manim"]
