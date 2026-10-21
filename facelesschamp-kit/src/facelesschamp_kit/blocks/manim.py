"""Fitted playback of already prepared mathematical media."""

from dataclasses import dataclass

from faceless_champ import PreparedFrameSource, Viewport

from .base import BlockBuild

__all__ = ["ManimCanvas"]

CAPABILITY_METADATA = {
    "ManimCanvas": {
        "family": "manim",
        "tags": ["prepared", "mathematics", "viewport"],
        "preparation": "explicit",
        "preparation_requirements": ["prepared RGBA PNG sequence"],
        "playback_requirements": ["Pillow"],
        "output_formats": ["rgba-png-sequence"],
        "named_targets": ["animation"],
        "use_when": "Compose a prepared mathematical animation inside ordinary Kit layouts and timelines.",
        "documentation": "docs/kit/manim.md",
    }
}


@dataclass(frozen=True)
class ManimCanvas:
    prepared: PreparedFrameSource
    source_start: float = 0

    def compose(self, context, bounds):
        source = self.prepared if isinstance(self.prepared, PreparedFrameSource) else PreparedFrameSource(self.prepared)
        width, height = source.intrinsic_size
        factor = min(bounds.width / width, bounds.height / height)
        view = Viewport(
            source, width=width * factor, height=height * factor, position=bounds.center, source_start=self.source_start
        )
        return BlockBuild(view, {"animation": view})
