"""Term Stack: each Taylor term on its own floating hairline panel in depth, sliding together into their sum.

    stack = TermStack(terms_of("cos", 6), view=(-3, 3, -2, 2))
    stack.draw(fr, orbit((0, 0, 0), 14, 0.25, -0.6), merge=u)     # u = 1: one panel showing the sum

2.5D: skia geometry through ``draw.space.Camera`` (scene-plan.md §1.6.5). World units: panel width ``span``.
"""

from __future__ import annotations

import numpy as np
import skia

from components import taylor as T
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw import smooth


def terms_of(f, n: int, a: float = 0.0, skip_zero: bool = True):
    """One single-term coefficient array per nonzero power up to n."""
    c = T.coeffs(f, n, a)
    out = []
    for k, v in enumerate(c):
        if skip_zero and v == 0:
            continue
        e = np.zeros(k + 1)
        e[k] = v
        out.append(e)
    return out


class TermStack:
    def __init__(self, terms, view=(-3.0, 3.0, -2.0, 2.0), span=8.0, gap=3.4, labels=None, samples=240, height=None):
        self.terms = [np.asarray(c, float) for c in terms]
        self.x0, self.x1, self.y0, self.y1 = view
        self.span, self.gap, self.labels, self.samples = span, gap, labels, samples
        self.sx = span / (self.x1 - self.x0)
        self.sy = self.sx if height is None else height / (self.y1 - self.y0)
        self.hw, self.hh = span / 2, (self.y1 - self.y0) * self.sy / 2

    def z(self, i: int, merge: float) -> float:
        n = len(self.terms)
        return (i - (n - 1) / 2) * self.gap * (1 - smooth(merge))

    def world(self, xs, ys, z):
        X = (xs - (self.x0 + self.x1) / 2) * self.sx
        Y = (ys - (self.y0 + self.y1) / 2) * self.sy
        return np.column_stack([X, Y, np.full_like(X, z)])

    def _curve(self, fr, cam, c, z, color, alpha, width, glow):
        xs = np.linspace(self.x0, self.x1, self.samples)
        ys = T.evaluate(c, xs)
        inside = (ys >= self.y0) & (ys <= self.y1)
        P = self.world(xs, np.clip(ys, self.y0, self.y1), z)
        px, py, _ = cam.project(P)
        # draw runs that stay inside the panel
        start = None
        for i, ok in enumerate(np.r_[inside, False]):
            if ok and start is None:
                start = i
            elif not ok and start is not None:
                if i - start > 1:
                    fr.poly(px[start:i], py[start:i], color, width, alpha, glow)
                start = None

    def draw(
        self, fr, cam, merge=0.0, alpha=1.0, panel_alpha=1.0, focus=None, show_sum=None, label_size=34, appear=None
    ):
        """Panels far to near. ``focus``: index drawn at full strength, the others at 0.4 (opacity-nonfocal)."""
        if alpha <= 0.003:
            return
        n = len(self.terms)
        order = sorted(range(n), key=lambda i: -cam.depth((0.0, 0.0, self.z(i, merge))))
        merged = smooth(np.clip((merge - 0.55) / 0.45, 0, 1)) if show_sum is None else show_sum
        for i in order:
            z = self.z(i, merge)
            corners = np.array(
                [[-self.hw, -self.hh, z], [self.hw, -self.hh, z], [self.hw, self.hh, z], [-self.hw, self.hh, z]]
            )
            cx, cy, _ = cam.project(corners)
            ap = 1.0 if appear is None else appear[i]
            if ap <= 0.003:
                continue
            fa = alpha * ap * (1.0 if focus is None or focus == i else 0.4) * (1 - 0.85 * merged if i else 1.0)
            pa = panel_alpha * fa
            # panel: dark glass fill (hides the panels behind it), hairline rim, axis line
            body = skia.Path()
            body.addPoly([skia.Point(float(x), float(y)) for x, y in zip(cx, cy)], True)
            fr.path_fill(body, "stage_raised", pa * 0.82)
            fr.poly(list(cx) + [cx[0]], list(cy) + [cy[0]], "frame", 1.0, pa * 0.8)
            ax_pts = self.world(np.array([self.x0, self.x1]), np.array([0.0, 0.0]), z)
            ax, ay, _ = cam.project(ax_pts)
            fr.line(ax[0], ay[0], ax[1], ay[1], "axis", 1.6, pa)
            self._curve(fr, cam, self.terms[i], z, "copy", fa * (1 - merged), 3.0, 0.5)
            if self.labels and i < len(self.labels):
                lx, ly, _ = cam.project(np.array([[-self.hw + 0.2, self.hh + 0.35, z]]))
                typmath.draw(
                    fr, self.labels[i], float(lx[0]), float(ly[0]), label_size, None, fa * (1 - merged), align="left"
                )
        if merged > 0:
            m = max(len(c) for c in self.terms)
            total = sum(np.pad(c, (0, m - len(c))) for c in self.terms)
            self._curve(fr, cam, total, self.z(0, merge), "copy", alpha * merged, 4.0, 0.6)
