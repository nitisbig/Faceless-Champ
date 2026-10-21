"""Offline feature requirements; no renderer allocation or optional engine imports."""

from ..components import Text
from ..paths import VectorPath
from ..timeline import Scene


def requirements(node):
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
    else:
        for child in node.children:
            result.update(requirements(child))
    if getattr(node, "effects", None) is not None or getattr(node, "transition", None) is not None:
        result.add("effects")
    return frozenset(result)


def unsupported(backend, features):
    return features & {"native_text", "compound_paths", "path_masks"} if backend == "pillow" else frozenset()


def preflight(node, backend):
    missing = unsupported(backend, requirements(node))
    if missing:
        labels = {"native_text": "Native typography", "compound_paths": "Compound paths", "path_masks": "PathMask"}
        raise ValueError(f"{', '.join(labels[name] for name in sorted(missing))} requires backend='skia' or 'moderngl'")
