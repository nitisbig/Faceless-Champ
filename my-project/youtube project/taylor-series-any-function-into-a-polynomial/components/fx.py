"""Small finishing helpers shared by the chapters.

fr.light_sweep(glow_path(curve, 12), u)       # sweep a stroked curve, not its fill
with feather(fr, (160, 430, 1600, 440)):       # open field: edges fade into the dark, no frame
    ...
"""

from __future__ import annotations

import skia


def glow_path(path, width=10.0):
    """The outline of ``path`` stroked at ``width`` px, as a fillable path (light sweeps, hit areas)."""
    out = skia.Path()
    skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=width).getFillPath(path, out)
    return out


class feather:
    """Fade whatever is drawn inside to nothing at the left and right ``edge`` fraction of ``rect``."""

    def __init__(self, fr, rect, edge=0.22):
        self.fr, self.rect, self.edge = fr, rect, edge

    def __enter__(self):
        for c in (self.fr.c, self.fr.g):
            c.saveLayer(None, None)

    def __exit__(self, *exc):
        x, _, w, _ = self.rect
        e = self.edge
        shader = skia.GradientShader.MakeLinear(
            [skia.Point(x, 0), skia.Point(x + w, 0)],
            [skia.ColorTRANSPARENT, skia.ColorBLACK, skia.ColorBLACK, skia.ColorTRANSPARENT],
            [0.0, e, 1 - e, 1.0],
        )
        paint = skia.Paint(Shader=shader, BlendMode=skia.BlendMode.kDstIn)
        for c in (self.fr.c, self.fr.g):
            c.drawPaint(paint)
            c.restore()


class layer_alpha:
    """Draw a group at one opacity on both canvases (a whole scene fading as one, no per-element seams)."""

    def __init__(self, fr, alpha):
        self.fr, self.alpha = fr, max(0.0, min(1.0, alpha))

    def __enter__(self):
        for c in (self.fr.c, self.fr.g):
            c.saveLayerAlpha(None, int(255 * self.alpha))

    def __exit__(self, *exc):
        self.fr.c.restore()
        self.fr.g.restore()
