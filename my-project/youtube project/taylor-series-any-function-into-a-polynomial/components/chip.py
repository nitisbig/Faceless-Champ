"""The Chip: a square die with pin rows, light-carrying traces, four operation pads and a display window.

    chip = Chip(cx=960, cy=560, size=420)
    chip.draw(fr, t, display="0.4794", active={"×": 1.0})    # pad glow 0..1 per operation

Geometry, not an icon (scene-plan.md §1.6.4). The trace layout is seeded (rng 7) at import.
"""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
import skia

from components.stage import clip
from faceless_champ.draw import hud

PADS = (("+", "plus"), ("−", "minus"), ("×", "fact"), ("÷", "ink"))
RNG = np.random.default_rng(7)
_TRACES = []  # unit-square polylines from the die edge to the core, shared by every Chip
for side in range(4):
    for i in range(7):
        s = (i + 1) / 8
        depth = 0.18 + 0.12 * RNG.random()
        bend = (RNG.random() - 0.5) * 0.18
        a = (s, 0.0)
        b = (s, depth)
        c = (min(0.72, max(0.28, s + bend)), depth + 0.06)
        pts = [a, b, c]
        rot = {
            0: lambda p: p,
            1: lambda p: (1 - p[1], p[0]),
            2: lambda p: (1 - p[0], 1 - p[1]),
            3: lambda p: (p[1], 1 - p[0]),
        }[side]
        _TRACES.append([rot(p) for p in pts])
_PHASE = RNG.random(len(_TRACES))


class Chip:
    def __init__(self, cx=960.0, cy=540.0, size=420.0):
        self.cx, self.cy, self.size = cx, cy, size

    @property
    def x0(self):
        return self.cx - self.size / 2

    @property
    def y0(self):
        return self.cy - self.size / 2

    def at(self, u, v):
        return self.x0 + u * self.size, self.y0 + v * self.size

    def pad_width(self):
        return (self.core()[2] - self.size * 0.02) / 2

    def pad_center(self, op: str):
        i = [p for p, _ in PADS].index(op)
        cu = self.core()
        pw = self.pad_width()
        gap = self.size * 0.02
        return cu[0] + (i % 2) * (pw + gap) + pw / 2, cu[1] + (i // 2) * (pw + gap) + pw / 2

    def core(self):
        s = self.size
        w = s * 0.34
        return self.cx - w / 2, self.cy - w / 2 + s * 0.06, w

    def core_center(self):
        x, y, w = self.core()
        return x + w / 2, y + w / 2

    def display_rect(self):
        """(x, y, w, h) of the display window in design px."""
        s = self.size
        dw, dh = s * 0.62, s * 0.16
        return self.cx - dw / 2, self.y0 + s * 0.1, dw, dh

    def draw(self, fr, t, alpha=1.0, display=None, active=None, pulses=1.0, display_color="ink", **kw):
        self.pins(fr, alpha)
        self.body(fr, t, alpha, active=active, pulses=pulses, display=display, display_color=display_color, **kw)

    def pins(self, fr, alpha=1.0, n=12):
        if alpha <= 0.003:
            return
        s = self.size
        for side in range(4):
            for i in range(n):
                u = (i + 0.5) / n
                if side in (0, 2):
                    x, y = self.at(u, -0.035 if side == 0 else 1.035)
                    fr.rrect(x - s * 0.012, y - s * 0.03, s * 0.024, s * 0.06, 2, fill="frame", alpha=alpha * 0.55)
                else:
                    x, y = self.at(-0.035 if side == 3 else 1.035, u)
                    fr.rrect(x - s * 0.03, y - s * 0.012, s * 0.06, s * 0.024, 2, fill="frame", alpha=alpha * 0.55)

    def body(
        self,
        fr,
        t,
        alpha=1.0,
        active=None,
        pulses=1.0,
        display=None,
        display_color="ink",
        dim=0.0,
        core_alpha=1.0,
        core_rise=1.0,
        pad_reveal=1.0,
        pad_fill=1.0,
        window=1.0,
    ):
        """Die, traces, core and display window. ``dim`` drops everything but the core toward opacity-ghost;
        ``core_rise`` 0..1 lifts the 2×2 core out of the dark; ``pad_reveal`` 0..1 draws the pad outlines on."""
        if alpha <= 0.003:
            return
        s = self.size
        active = active or {}
        rest = alpha * (1 - 0.75 * dim)
        fr.rrect(self.x0, self.y0, s, s, 6, fill="stage_raised", stroke="line", width=1.2, alpha=alpha, fill_alpha=1.0)
        fr.rrect(
            self.x0 + s * 0.03, self.y0 + s * 0.03, s * 0.94, s * 0.94, 4, stroke="line", width=1.0, alpha=0.6 * rest
        )
        body = skia.Path()
        body.addRect(skia.Rect.MakeXYWH(self.x0, self.y0, s, s))
        with clip(fr, path=body):
            for k, tr in enumerate(_TRACES):
                pts = [self.at(*p) for p in tr]
                xs, ys = zip(*pts)
                fr.poly(xs, ys, "line", 1.2, rest * 0.8)
                if pulses > 0:
                    u = (t * 0.45 + _PHASE[k]) % 1.0
                    x, y = _along(pts, u)
                    fr.glow_dot(x, y, 2.2, "light", rest * pulses * 0.8 * math.sin(math.pi * u), 0.9)
        ca = alpha * core_alpha * core_rise
        if ca > 0.003:
            pw = self.pad_width() * (0.86 + 0.14 * core_rise)
            for op, token in PADS:
                px, py = self.pad_center(op)
                a = active.get(op, 0.0)
                outline = skia.Path()
                outline.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(px - pw / 2, py - pw / 2, pw, pw), 6, 6))
                fr.path_fill(outline, token, ca * pad_fill * pad_reveal * (0.10 + 0.5 * a), glow=0.0)
                fr.path_stroke(_trim(outline, pad_reveal), token, 1.6, ca, glow=0.3 * pad_fill + 0.9 * a)
                fr.text(op, px, py + pw * 0.17, "display", pw * 0.48, 600, token if a < 0.5 else "bg", ca * pad_reveal)
        dx, dy, dw, dh = self.display_rect()
        fr.rrect(dx, dy, dw, dh, 4, fill="bg", stroke="line", width=1.2, alpha=alpha * window)
        if display:
            hud.tabular(
                fr,
                display.replace("-", "−"),
                dx + dw - s * 0.04,
                dy + dh * 0.7,
                dh * 0.56,
                display_color,
                alpha,
                align="right",
                glow=0.3,
            )

    def pulse_ring(self, fr, op, u, alpha=1.0):
        """An expanding ring around a pad as it fires (``u`` 0..1)."""
        if not 0 < u < 1 or alpha <= 0.003:
            return
        token = dict(PADS)[op]
        px, py = self.pad_center(op)
        pw = self.pad_width()
        g = pw * (0.5 + 0.55 * u)
        p = skia.Path()
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(px - g, py - g, 2 * g, 2 * g), 10, 10))
        fr.path_stroke(p, token, 2.0, alpha * (1 - u) ** 1.5, glow=0.5)


def _trim(path, u):
    """The first ``u`` (0..1) of a path's length."""
    if u >= 1:
        return path
    out = skia.Path()
    if u <= 0:
        return out
    m = skia.PathMeasure(path, False)
    m.getSegment(0, m.getLength() * u, out, True)
    return out


def _along(pts, u):
    seg = [math.dist(a, b) for a, b in pairwise(pts)]
    d = u * sum(seg)
    for (a, b), L in zip(pairwise(pts), seg):
        if d <= L:
            w = d / L if L else 0
            return a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w
        d -= L
    return pts[-1]
