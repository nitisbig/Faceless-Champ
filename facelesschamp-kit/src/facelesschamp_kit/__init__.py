"""Structured authoring over the independent faceless-champ video engine."""

from .blocks import Block, BlockBuild
from .compiler import CompiledVideo
from .context import BuildContext
from .diagnostics import KitError
from .project import Project
from .recipes import RecipeEvent, RecipeSpec, apply_recipe, recipe_specs, validate_recipe
from .themes import CLEAN_FLOW, Theme
from .tutorials import CodingTutorialStyle, CodingTutorialTemplate
from .video import Segment, Video

__version__ = "0.1.0rc7"
__all__ = ["Block", "BlockBuild", "BuildContext", "CompiledVideo", "KitError", "Project", "Segment", "Video"]
__all__ += ["RecipeEvent", "RecipeSpec", "apply_recipe", "recipe_specs", "validate_recipe"]
__all__ += ["CLEAN_FLOW", "Theme"]
__all__ += ["CodingTutorialStyle", "CodingTutorialTemplate"]
