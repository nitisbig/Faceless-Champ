"""Math typesetting as vector paths (no LaTeX needed).

Each token is typeset by Matplotlib's MathText engine (STIX fonts) into glyph
outlines, converted to skia.Path and laid out on a shared baseline. Tokens can
be coloured, highlighted, revealed and moved independently, in sync with the
rest of a skia frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import skia
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path as MPath
from matplotlib.textpath import TextPath

PROP = FontProperties(family="STIXGeneral", math_fontfamily="stix")


@lru_cache(maxsize=256)
def glyphs(tex: str, size: float):
    """skia.Path of ``$tex$`` at ``size`` px, baseline at y=0 (y down), plus (x0, x1, top, bottom)."""
    tp = TextPath((0, 0), f"${tex}$", size=size, prop=PROP)
    path = skia.Path()
    for verts, code in tp.iter_segments(curves=True, simplify=False):
        if code == MPath.MOVETO:
            path.moveTo(verts[0], -verts[1])
        elif code == MPath.LINETO:
            path.lineTo(verts[0], -verts[1])
        elif code == MPath.CURVE3:
            path.quadTo(verts[0], -verts[1], verts[2], -verts[3])
        elif code == MPath.CURVE4:
            path.cubicTo(verts[0], -verts[1], verts[2], -verts[3], verts[4], -verts[5])
        elif code == MPath.CLOSEPOLY:
            path.close()
    ext = tp.get_extents()
    return path, (ext.x0, ext.x1, -ext.y1, -ext.y0)


@dataclass
class Token:
    key: str
    tex: str
    color: str
    gap: float = 0.06  # space after, in ems


class Formula:
    """A row of tokens on one baseline. ``place(cx, baseline, scale)`` gives token positions."""

    def __init__(self, tokens, size=96.0):
        self.tokens = tokens
        self.size = size
        self.offsets = {}
        x = 0.0
        for tok in tokens:
            _, (x0, x1, top, bottom) = glyphs(tok.tex, size)
            self.offsets[tok.key] = (x - x0, x0, x1, top, bottom)
            x += (x1 - x0) + tok.gap * size
        self.width = x - tokens[-1].gap * size

    def bounds(self, key, cx, baseline, scale=1.0):
        off, x0, x1, top, bottom = self.offsets[key]
        left = cx - self.width * scale / 2 + (off + x0) * scale
        return left, baseline + top * scale, left + (x1 - x0) * scale, baseline + bottom * scale

    def draw(self, fr, cx, baseline, scale=1.0, alpha=None, color=None, glow=None, dy=None):
        """alpha/color/glow/dy: dicts key -> value (missing = defaults)."""
        alpha, color, glow, dy = alpha or {}, color or {}, glow or {}, dy or {}
        for tok in self.tokens:
            a = alpha.get(tok.key, 1.0)
            if a <= 0.003:
                continue
            path, _ = glyphs(tok.tex, self.size)
            off = self.offsets[tok.key][0]
            m = skia.Matrix()
            m.setScale(scale, scale)
            m.postTranslate(cx - self.width * scale / 2 + off * scale, baseline + dy.get(tok.key, 0.0))
            p = skia.Path(path)
            p.transform(m)
            fr.path_fill(p, color.get(tok.key, tok.color), a, glow=glow.get(tok.key, 0.0))


def symbol(fr, tex, cx, cy, size, color, alpha=1.0, glow=0.0, scale=1.0):
    """Single expression centred on (cx, cy)."""
    if alpha <= 0.003:
        return
    path, (x0, x1, top, bottom) = glyphs(tex, size)
    m = skia.Matrix()
    m.setScale(scale, scale)
    m.postTranslate(cx - (x0 + x1) / 2 * scale, cy - (top + bottom) / 2 * scale)
    p = skia.Path(path)
    p.transform(m)
    fr.path_fill(p, color, alpha, glow=glow)
