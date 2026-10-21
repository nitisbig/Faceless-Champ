"""Composable mathematical scene specifications without native imports."""

from dataclasses import dataclass
from pathlib import Path

from faceless_champ.components import finite
from faceless_champ.integrations.manim import ManimSceneSpec
from PIL import ImageColor

__all__ = ["EquationTransform"]

CAPABILITY_METADATA = {
    "EquationTransform": {
        "family": "manim",
        "category": "mathematics",
        "tags": ["equation", "symbolic", "transformation", "matching", "latex", "manim"],
        "preparation": "explicit",
        "preparation_requirements": ["manim>=0.22,<0.23", "LaTeX", "dvisvgm", "Cairo", "FFmpeg/ffprobe"],
        "playback_requirements": ["Pillow"],
        "output_formats": ["rgba-png-sequence"],
        "use_when": "Preserve matching TeX symbols while transforming between author-supplied equations.",
        "avoid": "Use Core Equation/Write for static typesetting or simple reveals. Does not solve or prove algebra.",
        "documentation": "docs/kit/manim.md",
    }
}


@dataclass(frozen=True)
class EquationTransform:
    """Prepare MathTex/TransformMatchingTex via context.manim(scene_spec()).

    Expressions may use Manim's {{token}} isolation. All expressions share a
    fixed camera fit. Durations resolve to absolute source-frame boundaries.
    """

    expressions: tuple[str, ...]
    write_time: float = 1
    transform_time: float = 1
    hold_time: float = 1
    color: str = "#FFFFFF"
    font_size: float = 64

    def __post_init__(self):
        if isinstance(self.expressions, str):
            raise TypeError("expressions must be a sequence of TeX expressions")
        expressions = tuple(self.expressions)
        if len(expressions) < 2 or any(not isinstance(e, str) or not e.strip() for e in expressions):
            raise ValueError("Supply at least two nonempty TeX expressions")
        object.__setattr__(self, "expressions", expressions)
        for name in ("write_time", "transform_time", "font_size"):
            if finite(getattr(self, name), name, 0) == 0:
                raise ValueError(f"{name} must be positive")
        finite(self.hold_time, "hold_time", 0)
        ImageColor.getrgb(self.color)

    def scene_spec(self):
        from dataclasses import asdict

        return ManimSceneSpec(
            Path(__file__).with_name("_equation_scene.py"), "EquationTransformScene", parameters=asdict(self)
        )
