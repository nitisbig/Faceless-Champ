"""Importable project entrypoint; render.py is v1, render_v2.py is v2."""

from scene.story import RoadsterRenderer, build_master
from scene.v2 import RoadsterV2Renderer

__all__ = ["RoadsterRenderer", "RoadsterV2Renderer", "build_master"]
