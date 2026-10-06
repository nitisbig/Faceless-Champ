"""Structured authoring over the independent faceless-champ video engine."""

from .blocks import Block, BlockBuild
from .compiler import CompiledVideo
from .context import BuildContext
from .diagnostics import KitError
from .project import Project
from .video import Segment, Video

__version__ = "0.1.0rc1"
__all__ = ["Block", "BlockBuild", "BuildContext", "CompiledVideo", "KitError", "Project", "Segment", "Video"]
