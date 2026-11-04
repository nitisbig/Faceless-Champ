"""Motions shared from Chapter 2 on: the exponent drop, a slow push-in and the curvature comb.

drop(fr, t, t0, src, dst, "4", 48, 80)          # a magenta 4 falls from src to dst (scene-plan.md §1.4.2)
with zoom_about(fr, 760, 500, 1.04):             # push in on a derivation
    ...
comb(fr, ax, xs, f(xs), f1(xs), f2(xs), "frame", 1.0)
"""

from __future__ import annotations

import math

from faceless_champ.draw import back, ease_out, lin, pulse
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc

DROP = 0.45  # seconds per exponent drop


def drop(fr, t, t0, src, dst, char, s0, s1, alpha=1.0, dur=DROP):
    """The exponent drop: a glyph falls on a gravity arc to the front, lands with a back-ease and a magenta spark.
    Returns 0..1 progress."""
    u = lin(t, t0, t0 + dur)
    if u <= 0 or alpha <= 0.003:
        return u

    def at(v):
        return src[0] + (dst[0] - src[0]) * ease_out(v), src[1] + (dst[1] - src[1]) * v * v

    if u < 1:
        for k in range(1, 6):  # trail
            v = u - 0.06 * k
            if v > 0:
                fr.glow_dot(*at(v), 4.0 - 0.5 * k, "fact", alpha * 0.5 * (1 - k / 6), 0.9)
        x, y = at(u)
        size = (s0 + (s1 - s0) * u) * back(min(1.0, u * 1.15), 1.2)
        typmath.draw(fr, tc("fact", char), x, y, size, None, alpha, glow=0.6)
    sp = pulse(t, t0 + dur, 0.4)  # the × spark that multiplies it in
    if sp > 0:
        fr.glow_dot(*dst, 6 + 12 * sp, "fact", 0.45 * sp * alpha, 1.0)
    return u


class zoom_about:
    """Scale both canvases about a point (a slow push-in)."""

    def __init__(self, fr, cx, cy, k):
        self.fr, self.cx, self.cy, self.k = fr, cx, cy, k

    def __enter__(self):
        for c in (self.fr.c, self.fr.g):
            c.save()
            c.translate(self.cx, self.cy)
            c.scale(self.k, self.k)
            c.translate(-self.cx, -self.cy)

    def __exit__(self, *exc):
        self.fr.c.restore()
        self.fr.g.restore()


def curvature(f1, f2):
    return f2 / (1 + f1 * f1) ** 1.5


def comb(fr, ax, xs, y, d1, d2, color, alpha, scale=95.0, grow=1.0):
    """CAD curvature comb: hairline normals with length ∝ curvature, joined by an envelope."""
    if alpha <= 0.003:
        return
    tips = []
    for x, yv, s1, s2 in zip(xs, y, d1, d2):
        k = curvature(s1, s2)
        px, py = float(ax.px(x)), float(ax.py(yv))
        tx, ty = ax.sx, -s1 * ax.sy
        n = math.hypot(tx, ty)
        nx, ny = ty / n, -tx / n  # points up the screen
        side = 1.0 if k < 0 else -1.0  # outward: above a hill, below a bowl
        L = scale * abs(k) * grow
        ex, ey = px + side * nx * L, py + side * ny * L
        fr.line(px, py, ex, ey, color, 1.0, 0.7 * alpha)
        tips.append((ex, ey))
    xs_, ys_ = zip(*tips)
    fr.poly(xs_, ys_, color, 1.4, alpha, glow=0.2)
