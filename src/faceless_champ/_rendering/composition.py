"""Shared pixel composition driven by canonical source-time placements."""

from PIL import Image


def composition_frame(renderer, node, time, size):
    """Legacy pixel operations driven by the shared source-clock composition plan."""
    from ..timeline import Sequence
    from .evaluate import composition_plan

    parts, progress = composition_plan(node, time, size)
    background = Image.new("RGBA", size, node.canvas.bg)
    if isinstance(node, Sequence):
        if not parts:
            return background
        first = fit_frame(renderer, parts[0].node, parts[0].time, size, parts[0].background)
        if progress is not None:
            second = fit_frame(renderer, parts[1].node, parts[1].time, size, parts[1].background)
            return Image.blend(first, second, progress)
        return first
    for p in parts:
        x, y, w, h = p.viewport
        background.alpha_composite(fit_frame(renderer, p.node, p.time, (w, h), p.background), (x, y))
    return background


def fit_frame(renderer, node, time, size, bg):
    from .evaluate import fit

    fitted, position = fit(node.canvas, size)
    result = Image.new("RGBA", size, bg)
    result.alpha_composite(renderer.frame(node, time, fitted), position)
    return result
