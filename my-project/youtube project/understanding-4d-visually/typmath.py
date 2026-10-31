"""Typst math as skia paths inside fx.Frame: the film's equation engine (no LaTeX needed).

Typst (CLI on PATH, or ``pip install typst``) compiles each expression to SVG once (disk cache,
``faceless_champ.typst_math``); glyphs become skia paths we can colour, glow, reveal and morph per frame.

    tc("x", "x")                                   # '#text(fill: rgb("#FF5A4E"))[$x$]': colour a sub-term by token
    draw(fr, "sqrt(1^2 + 1^2) = sqrt(2)", 960, 540, 72)
    draw(fr, expr, cx, cy, 64, reveal=0.4)         # left-to-right write-on (glyph by glyph)
    morph(fr, "sqrt(4)", "2", u, 960, 540, 72)     # matching glyphs fly, the rest cross-fade

Typst syntax: a/b, sqrt(x), x^2, mat(1, 0; 0, 1), theta, dot, cos, "text", arrow(v), norm(v).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import skia
from fx import ease_io, mix
from theme import TOKENS

from faceless_champ.backends._skia_paint import path_data
from faceless_champ.typst_math import PT_PER_PX, glyph_paths

BASE = 96.0  # glyphs are compiled once at this size and scaled


def tc(token: str, body: str) -> str:
    """Colour a math sub-expression with a theme token (or hex): tc('w', 'w') -> blue w."""
    hexv = TOKENS.get(token, token).lstrip("#")
    return f'#text(fill: rgb("#{hexv}"))[${body}$]'


@dataclass(frozen=True)
class Glyph:
    path: skia.Path  # design px at BASE size, origin at the expression's centre
    color: str  # hex fill, or stroke colour when ``stroke`` > 0
    stroke: float  # 0 = filled glyph; > 0 = stroked rule (radical vinculum, fraction bar) width in px
    key: str  # shape identity for morph matching (translation-free)
    cx: float
    cy: float


@lru_cache(maxsize=512)
def glyphs(expr: str, color: str = TOKENS["ink"]) -> tuple[tuple[Glyph, ...], tuple[float, float, float, float]]:
    """Glyphs left to right, centred on (0, 0), plus the bounds (l, t, r, b) at BASE size."""
    pieces = glyph_paths(expr, BASE, color)
    if not pieces:
        raise ValueError(f"Typst produced no glyphs for {expr!r}")
    boxes = [p.bounds for p, *_ in pieces]
    left, right = min(b.left for b in boxes), max(b.right for b in boxes)
    top, bottom = min(b.top for b in boxes), max(b.bottom for b in boxes)
    ox, oy = (left + right) / 2, (top + bottom) / 2
    out = []
    for data, fill, stroke, width in pieces:
        moved = data.transformed(dx=-ox, dy=-oy)
        path = path_data(skia, moved)
        b = moved.bounds
        filled = fill not in (None, "none")
        shape = data.transformed(dx=-b.left, dy=-b.top).to_svg()
        key = hashlib.sha1(f"{round(b.width, 1)}:{round(b.height, 1)}:{shape[:400]}".encode()).hexdigest()[:16]
        out.append(Glyph(path, fill if filled else stroke, 0.0 if filled else width / PT_PER_PX, key,
                         (b.left + b.right) / 2, (b.top + b.bottom) / 2))
    return tuple(out), (left - ox, top - oy, right - ox, bottom - oy)


def size_of(expr: str, size: float) -> tuple[float, float]:
    _, (lft, t, r, b) = glyphs(expr)
    k = size / BASE
    return (r - lft) * k, (b - t) * k


def _paint_glyph(fr, g: Glyph, m: skia.Matrix, color: str, alpha: float, glow: float):
    p = skia.Path(g.path)
    p.transform(m)
    if g.stroke > 0:
        fr.path_stroke(p, color, g.stroke * m.getScaleX(), alpha, glow=glow, glow_width=6.0)
    else:
        fr.path_fill(p, color, alpha, glow=glow)


def _matrix(cx, cy, size, dx=0.0, dy=0.0):
    k = size / BASE
    m = skia.Matrix()
    m.setScale(k, k)
    m.postTranslate(cx + dx, cy + dy)
    return m


def draw(fr, expr, cx, cy, size=64.0, color=None, alpha=1.0, glow=0.0, reveal=1.0, colors=None, glows=None,
         alphas=None, align="center"):
    """Draw an expression centred on (cx, cy) (``align`` 'left'/'right' anchors that edge at cx).

    color: recolour every glyph (token or hex); colors/glows/alphas: {glyph index: value} overrides.
    reveal: 0..1 writes glyphs on left to right with a short per-glyph fade.
    """
    if alpha <= 0.003:
        return
    gs, (lft, _, r, _) = glyphs(expr)
    k = size / BASE
    shift = 0.0 if align == "center" else (-lft * k if align == "left" else -r * k)
    m = _matrix(cx + shift, cy, size)
    n = len(gs)
    colors, glows, alphas = colors or {}, glows or {}, alphas or {}
    for i, g in enumerate(gs):
        a = alpha * alphas.get(i, 1.0)
        if reveal < 1.0:
            a *= float(np.clip(reveal * (n + 2) - i, 0.0, 1.0))
        if a <= 0.003:
            continue
        c = colors.get(i, TOKENS.get(color, color) if color else g.color)
        _paint_glyph(fr, g, m, c, a, glows.get(i, glow))


def morph(fr, a_expr, b_expr, u, cx, cy, size=64.0, alpha=1.0, glow=0.0, b_cx=None, b_cy=None, b_size=None,
          arc=0.0):
    """Matching-glyph transform: glyphs with the same shape fly from A to B; the rest cross-fade.

    u: 0 -> A, 1 -> B (eased inside). B can sit elsewhere (b_cx, b_cy, b_size). ``arc`` lifts flying glyphs.
    """
    if alpha <= 0.003:
        return
    u = ease_io(float(np.clip(u, 0.0, 1.0)))
    if u <= 0.0:
        draw(fr, a_expr, cx, cy, size, alpha=alpha, glow=glow)
        return
    bx, by, bs = (cx if b_cx is None else b_cx), (cy if b_cy is None else b_cy), (size if b_size is None else b_size)
    if u >= 1.0:
        draw(fr, b_expr, bx, by, bs, alpha=alpha, glow=glow)
        return
    ga, _ = glyphs(a_expr)
    gb, _ = glyphs(b_expr)
    used, pairs = set(), {}
    for j, g in enumerate(gb):
        best = None
        for i, h in enumerate(ga):
            if i not in used and h.key == g.key and (best is None or abs(i - j) < abs(best - j)):
                best = i
        if best is not None:
            used.add(best)
            pairs[j] = best
    ka, kb = size / BASE, bs / BASE
    for i, g in enumerate(ga):  # unmatched A glyphs fade out
        if i not in used:
            _paint_glyph(fr, g, _matrix(cx, cy, size), g.color, alpha * (1 - u) ** 2, glow)
    for j, g in enumerate(gb):
        if j in pairs:
            h = ga[pairs[j]]
            x0, y0 = cx + h.cx * ka, cy + h.cy * ka
            x1, y1 = bx + g.cx * kb, by + g.cy * kb
            s = size + (bs - size) * u
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u - arc * 4 * u * (1 - u)
            m = skia.Matrix()
            m.setScale(s / BASE, s / BASE)
            m.postTranslate(x - g.cx * s / BASE, y - g.cy * s / BASE)
            c = h.color if h.color == g.color else mix(h.color, g.color, u)
            _paint_glyph(fr, g, m, c, alpha, glow)
        else:  # new B glyphs fade in
            _paint_glyph(fr, g, _matrix(bx, by, bs), g.color, alpha * u**2, glow)


# ------------------------------------------------------------------ live numbers (no per-frame compiles)

_STRIP = "0123456789.+−,°"
_NUMERIC = re.compile(r"^[−\-+]?[0-9.,]+°?$")


@lru_cache(maxsize=1)
def _strip():
    """Per-character glyphs of the math digits on one baseline: {char: (path, advance, lead)} at BASE size."""
    pieces = glyph_paths(_STRIP, BASE, TOKENS["ink"])
    if len(pieces) != len(_STRIP):
        raise RuntimeError(f"digit strip produced {len(pieces)} glyphs for {len(_STRIP)} characters")
    baseline = pieces[1][0].bounds.bottom  # the foot of '1'
    out = {}
    for i, (ch, (data, *_)) in enumerate(zip(_STRIP, pieces)):
        b = data.bounds
        width = b.right - b.left
        if ch.isdigit():  # tabular: every digit advances half an em, keep its side bearing
            adv, lead, dx = 0.5 * BASE, b.left - 0.5 * BASE * i, b.left
        else:
            pad = 0.22 * BASE if ch in "+−" else 0.06 * BASE
            adv, lead, dx = width + pad, pad / 2, b.left
        out[ch] = (path_data(skia, data.transformed(dx=-dx, dy=-baseline)), adv, lead)
    return out


def number(fr, s, cx, cy, size=48.0, color="ink", alpha=1.0, glow=0.0, align="center"):
    """A live numeric value ('0.62', '−3', '72.5°') from cached digit glyphs: no Typst compile per frame."""
    if alpha <= 0.003 or not s:
        return 0.0
    strip = _strip()
    chars = [c for c in s.replace("-", "−") if c in strip]
    k = size / BASE
    total = sum(strip[c][1] for c in chars) * k
    x = cx - total / 2 if align == "center" else cx - total if align == "right" else cx
    baseline = cy + 0.335 * size  # digits are ~0.67 em tall: centre them on cy
    hexv = TOKENS.get(color, color)
    for c in chars:
        path, adv, lead = strip[c]
        p = skia.Path(path)
        m = skia.Matrix()
        m.setScale(k, k)
        m.postTranslate(x + lead * k, baseline)
        p.transform(m)
        fr.path_fill(p, hexv, alpha, glow=glow)
        x += adv * k
    return total


def term(fr, tex, cx, cy, size=48.0, color=None, alpha=1.0, glow=0.0):
    """Numbers go through the digit strip (fast, tabular); anything else is compiled by Typst once.

    color None keeps the colours written into the expression with ``tc``.
    """
    if _NUMERIC.match(tex.strip()):
        number(fr, tex.strip(), cx, cy, size, color or "ink", alpha, glow)
    else:
        draw(fr, tex, cx, cy, size, color=color, alpha=alpha, glow=glow)


def glyph_centers(expr, cx, cy, size):
    """Design-px centre of every glyph (to anchor arrows, highlights and connectors to a term)."""
    gs, _ = glyphs(expr)
    k = size / BASE
    return [(cx + g.cx * k, cy + g.cy * k) for g in gs]


__all__ = ["tc", "glyphs", "draw", "morph", "number", "term", "size_of", "glyph_centers"]
