"""Themed, fitted technical design viewports."""

from copy import deepcopy
from dataclasses import asdict, dataclass

from faceless_champ.integrations.pyvista.model import ArchStyle

from facelesschamp_kit.engineering.clip import ArchChamp

from .base import BlockBuild


class _DefaultAnnotations(tuple):
    """Keep the empty-tuple default while distinguishing explicit empty overrides."""


class _DefaultUnits(str):
    """Keep the string default while distinguishing an explicit units override."""


@dataclass(frozen=True)
class ArchCanvas:
    """Explicit settings override structured designs; omitted settings use the design.

    A design's style retains its existing precedence over the block's default style.
    """

    parts: object
    script: object = None
    style: ArchStyle | None = None
    camera: object = None
    labels: tuple = _DefaultAnnotations()
    dimensions: tuple = _DefaultAnnotations()
    units: str = _DefaultUnits("model units")
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
        if self.style is None and context.theme.name == "clean-flow":
            default_style = ArchStyle(color="#D8D5CF", edge_color=context.theme.muted)
        if isinstance(self.parts, dict):
            data = deepcopy(self.parts)
            if self.script is not None:
                data["script"] = self.script.to_dict()
            if self.camera is not None:
                data["camera"] = asdict(self.camera)
            for name in ("labels", "dimensions"):
                annotations = getattr(self, name)
                if not isinstance(annotations, _DefaultAnnotations):
                    data[name] = [asdict(item) for item in annotations]
            if not isinstance(self.units, _DefaultUnits):
                data["units"] = self.units
            if "style" not in data:
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
