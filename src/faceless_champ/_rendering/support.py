"""Offline feature requirements; no renderer allocation or optional engine imports."""

from ..components import Text
from ..paths import VectorPath
from ..timeline import Scene

# Features the ModernGL shaders do not implement; they are composited with Skia on the CPU.
_CPU_SKIA_ONLY = frozenset({"blend_modes", "skia_effects"})


def requirements(node):
    from ..blending import blends

    result = set()
    if isinstance(node, Scene):
        node.build()
        for entry in node.entries:
            c = entry.component
            if isinstance(c, Text) and c.text_engine == "skia":
                result.add("native_text")
            if isinstance(c, VectorPath) and not c.portable:
                result.add("compound_paths")
            if c.mask is not None and c.mask.kind == "path":
                result.add("path_masks")
            if c.effects is not None or getattr(c, "_procedural", False):
                result.add("effects")
            if c.effects is not None and c.effects.uses_skia:
                result.add("skia_effects")
            if blends(c):
                result.add("blend_modes")
            if getattr(c, "round_corners", 0) or getattr(c, "jitter", None):
                result.add("path_effects")
            if getattr(c, "perspective", None) is not None:
                result.add("perspective")
    else:
        for child in node.children:
            result.update(requirements(child))
    if getattr(node, "effects", None) is not None or getattr(node, "transition", None) is not None:
        result.add("effects")
        if getattr(node, "effects", None) is not None and node.effects.uses_skia:
            result.add("skia_effects")
    return frozenset(result)


def unsupported(backend, features):
    if backend == "pillow":
        return features & {"native_text", "compound_paths", "path_masks", "path_effects"}
    if backend == "moderngl":
        return features & (_CPU_SKIA_ONLY | {"perspective"})
    return frozenset()


_LABELS = {
    "native_text": "Native typography",
    "compound_paths": "Compound paths",
    "path_masks": "PathMask",
    "blend_modes": "Blend modes",
    "skia_effects": "DisplacementMap/ShaderEffect",
    "path_effects": "round_corners/jitter",
    "perspective": "Perspective tilt",
}


def preflight(node, backend):
    missing = unsupported(backend, requirements(node))
    if missing:
        names = ", ".join(_LABELS[name] for name in sorted(missing))
        if backend == "moderngl":
            raise ValueError(f"{names} require backend='skia' or 'pillow' (CPU Skia compositing)")
        raise ValueError(f"{names} requires backend='skia' or 'moderngl'")
