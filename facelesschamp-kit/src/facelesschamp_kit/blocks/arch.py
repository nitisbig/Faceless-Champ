"""Themed, fitted technical design viewports."""

from copy import deepcopy
from dataclasses import dataclass

from faceless_champ.arch import ArchChamp, ArchStyle

from .base import BlockBuild


@dataclass(frozen=True)
class ArchCanvas:
    parts: object
    script: object = None
    style: ArchStyle | None = None
    camera: object = None
    labels: tuple = ()
    dimensions: tuple = ()
    units: str = "model units"
    viewport: tuple = (1600, 900)
    source_start: float = 0

    def compose(self, context, bounds):
        width, height = self.viewport
        options = {
            "width": width,
            "height": height,
            "source_start": self.source_start,
            "font": context.theme.font,
            "position": bounds.center,
            "scale": min(bounds.width / width, bounds.height / height),
        }
        default_style = self.style or ArchStyle(color=context.theme.foreground, edge_color=context.theme.accent)
        if isinstance(self.parts, dict):
            data = deepcopy(self.parts)
            if "style" not in data:
                from dataclasses import asdict

                data["style"] = asdict(default_style)
            clip = ArchChamp.from_dict(data, mesh_resolver=context.assets.mesh, **options)
        else:
            # Standalone objects remain easy to mix with ordinary blocks.
            clip = ArchChamp(
                self.parts,
                self.script,
                style=default_style,
                camera=self.camera,
                labels=self.labels,
                dimensions=self.dimensions,
                units=self.units,
                **options,
            )
        return BlockBuild(clip, {"model": clip})
