"""Data-only Manim requests; importing these types never loads Manim."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import ImageColor

from faceless_champ.components import finite
from faceless_champ.prepared import _digest, _file_digest

__all__ = ["ManimError", "ManimRenderOptions", "ManimSceneSpec"]

CAPABILITY_METADATA = {
    "ManimSceneSpec": {
        "family": "manim",
        "tags": ["manim", "calculus", "linear algebra", "mathematical graphs", "geometry"],
        "preparation": "explicit",
        "preparation_requirements": ["manim>=0.22,<0.23", "Cairo", "FFmpeg/ffprobe"],
        "playback_requirements": ["Pillow"],
        "output_formats": ["rgba-png-sequence"],
        "use_when": "Animate mathematical constructions or symbolic relationships in an authored Manim scene.",
        "avoid": "Prefer Equation/Write or existing Kit charts for simple typesetting and data plots.",
        "documentation": "docs/core/manim.md",
    }
}


class ManimError(RuntimeError):
    def __init__(self, code, message, **details):
        self.code, self.details = code, details
        super().__init__(message)


@dataclass(frozen=True, init=False)
class ManimSceneSpec:
    """Trusted scene file plus explicit local inputs and JSON parameters.

    Additional inputs are file paths relative to source_root. Only those files
    and the entrypoint are copied to the worker. Use faceless_parameters from
    setup/construct; no caller-provided Python expression is evaluated.
    """

    source: Path
    scene_name: str
    source_root: Path
    inputs: tuple[str, ...]
    _parameters: str

    def __init__(self, source, scene_name, *, source_root=None, inputs=(), parameters=None):
        source = Path(source).resolve()
        root = Path(source_root).resolve() if source_root is not None else source.parent
        if not isinstance(scene_name, str) or not scene_name.isidentifier():
            raise ValueError("scene_name must be a Python class identifier")
        if source.suffix != ".py" or not source.is_relative_to(root):
            raise ValueError("Scene source must be a Python file within source_root")
        if isinstance(inputs, (str, bytes)):
            raise TypeError("inputs must be a sequence of relative file paths")
        names = {str(source.relative_to(root))}
        for value in inputs:
            relative = Path(value)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Inputs must be contained relative paths")
            path = (root / relative).resolve()
            if not path.is_relative_to(root):
                raise ValueError("Input escapes source_root")
            names.add(str(relative))
        if not isinstance(parameters if parameters is not None else {}, dict):
            raise TypeError("parameters must be a JSON object")
        serialized = json.dumps(parameters or {}, sort_keys=True, allow_nan=False)
        for name, value in {
            "source": source,
            "scene_name": scene_name,
            "source_root": root,
            "inputs": tuple(sorted(names)),
            "_parameters": serialized,
        }.items():
            object.__setattr__(self, name, value)

    @property
    def parameters(self):
        return json.loads(self._parameters)

    def record(self):
        if any(not (self.source_root / name).resolve().is_relative_to(self.source_root) for name in self.inputs):
            raise ValueError("Input escapes source_root")
        return {
            "source": str(self.source.relative_to(self.source_root)),
            "scene_name": self.scene_name,
            "inputs": {name: _file_digest(self.source_root / name) for name in self.inputs},
            "parameters": self.parameters,
        }


@dataclass(frozen=True)
class ManimRenderOptions:
    quality: str = "low_quality"
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    background: str | None = None
    seed: int = 0

    def __post_init__(self):
        if self.quality not in {"low_quality", "medium_quality", "high_quality", "fourk_quality"}:
            raise ValueError("Use a documented low/medium/high/fourk_quality Manim preset")
        if (self.width is None) != (self.height is None):
            raise ValueError("Specify both width and height")
        if self.width is not None and any(type(v) is not int or v < 1 for v in (self.width, self.height)):
            raise ValueError("Dimensions must be positive integers")
        if self.fps is not None and (type(self.fps) not in (int, float) or finite(self.fps, "fps", 0) == 0):
            raise ValueError("fps must be positive")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("seed must be an integer in 0..2**32-1")
        if self.background is not None and ImageColor.getcolor(self.background, "RGBA")[3] != 255:
            raise ValueError("Use background=None for transparency, or an opaque background color")


def request_record(spec, options, python):
    import sys
    from dataclasses import asdict

    if not isinstance(spec, ManimSceneSpec) or not isinstance(options, ManimRenderOptions):
        raise TypeError("Expected ManimSceneSpec and ManimRenderOptions")
    record = {
        "spec": spec.record(),
        "options": asdict(options),
        # Resolving the executable symlink would discard a virtual environment.
        "python": str(Path(python or sys.executable).absolute()),
    }
    return _digest(record), record
