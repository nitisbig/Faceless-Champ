"""The Vector Slot: a column vector whose slots are colored by axis.

Slots can fill per cue, grow a new slot (x y z -> w -> ... n) and stream thousands of
entries into depth (S12, S27). Entries are Typst math (``typmath.term``): numbers use the cached digit strip.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import typmath
from fx import ease_out, lerp


@dataclass
class Slot:
    tex: str  # Typst math, e.g. "3", "x", "sqrt(14)"
    color: str = "ink"
    alpha: float = 1.0
    glow: float = 0.0
    underline: float = 0.0  # 0..1 axis-colored underline under the entry


def bracket(fr, x, top, bottom, side, color="ink", alpha=1.0, width=2.4, lip=14.0, draw=1.0):
    """A square bracket; ``side`` -1 = left '[', +1 = right ']'. ``draw`` traces it on (0..1)."""
    if alpha <= 0.003 or draw <= 0:
        return
    lx = x - side * lip
    pts = [(lx, top), (x, top), (x, bottom), (lx, bottom)]
    seg = np.array([lip, bottom - top, lip])
    n = draw * seg.sum()
    xs, ys = [pts[0][0]], [pts[0][1]]
    for (a, b), L in zip(zip(pts, pts[1:]), seg):
        if n <= 0:
            break
        u = min(1.0, n / L)
        xs.append(lerp(a[0], b[0], u))
        ys.append(lerp(a[1], b[1], u))
        n -= L
    fr.poly(xs, ys, color, width, alpha, glow=0.25)


def draw_vector(fr, cx, cy, slots, size=48.0, pitch=1.3, alpha=1.0, width=None, bracket_color="ink", grow=None,
                brackets=1.0):
    """Column vector centred at (cx, cy). Returns the y centre of each slot.

    grow: optional (index, u) — slot ``index`` opens with ease u (0..1), pushing the brackets apart.
    """
    if alpha <= 0.003:
        return []
    n = len(slots)
    step = size * pitch
    opens = [1.0] * n
    if grow is not None:
        opens[grow[0]] = ease_out(max(0.0, min(1.0, grow[1])))
    height = step * sum(opens)
    y = cy - height / 2
    centers = []
    for s, o in zip(slots, opens):
        yc = y + step * o / 2
        centers.append(yc)
        if s.alpha * o > 0.003:
            typmath.term(fr, s.tex, cx, yc, size, s.color, alpha * s.alpha * o, glow=s.glow)
            if s.underline > 0:
                uw = size * 0.55 * s.underline
                uy = yc + size * 0.6
                fr.line(cx - uw, uy, cx + uw, uy, s.color, 2.0, alpha * s.alpha * o, glow=0.4)
        y += step * o
    w = width or size * 1.5
    pad = size * 0.22
    bracket(fr, cx - w / 2, cy - height / 2 - pad, cy + height / 2 + pad, -1, bracket_color, alpha, draw=brackets)
    bracket(fr, cx + w / 2, cy - height / 2 - pad, cy + height / 2 + pad, 1, bracket_color, alpha, draw=brackets)
    return centers


def draw_stream(fr, cx, base_y, count, reveal=1.0, alpha=1.0, size=30.0, seed=7, colors=("ink",), depth=0.82):
    """A tall vector of ``count`` tiny entries receding upward into perspective (a data waterfall).

    Only the visible rows are drawn; each row shrinks by ``depth`` per step, so thousands of entries read
    as a column vanishing toward a vanishing point.
    """
    if alpha <= 0.003 or count <= 0:
        return
    rng = np.random.default_rng(seed)
    vals = rng.normal(0, 1, 64)
    shown = max(1, int(count * reveal))
    y, s = base_y, size
    k = 0
    while k < shown and s > 2.0:
        color = colors[k % len(colors)]
        fade = alpha * min(1.0, s / size * 1.4)
        typmath.number(fr, f"{vals[k % 64]:+.2f}", cx, y, s, color, fade)
        y -= s * 1.25
        s *= depth
        k += 1
