"""The dart target of Chapter 3: seeded 2D Gaussian throws, their two independent errors, marginals and rings.

Horizontal errors are ``left`` (teal) and vertical errors are ``right`` (orange): the two independent
directions. Iso-density rings are ``pi`` (pink): the hidden circle.

    tg = Target(cx=760, cy=540, unit=110)            # unit = px per standard deviation
    tg.draw_board(fr, alpha)
    tg.draw_darts(fr, t, t0=3.0, rate=40)            # throws land one by one with a small impact ring
    tg.draw_errors(fr, i, uh, uv)                    # the hero dart's teal and orange error segments
    tg.draw_marginals(fr, n_landed, strip=(a, b))    # histograms along the bottom and the side
    tg.draw_rings(fr, alpha)                         # pink iso-density contours
"""

from __future__ import annotations

import math

import numpy as np
import skia

SEED_DARTS = 11


def draw_dots(fr, xy, r, color, alpha=1.0, glow=0.0):
    """Many round dots in one draw call (thousands per frame)."""
    if alpha <= 0.003 or len(xy) == 0:
        return
    pts = [skia.Point(float(x), float(y)) for x, y in xy]
    paint = fr._stroke(color, 2 * r, alpha)
    fr.c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint)
    if glow > 0:
        fr.glow_used = True
        fr.g.drawPoints(skia.Canvas.kPoints_PointMode, pts, fr._stroke(color, 4.4 * r, alpha * glow))


class Target:
    def __init__(self, cx=760.0, cy=540.0, unit=110.0, n=300, seed=SEED_DARTS, rings=(1, 2, 3)):
        self.cx, self.cy, self.unit, self.rings = cx, cy, unit, rings
        self.z = np.random.default_rng(seed).normal(0.0, 1.0, (n, 2))
        self.n = n
        self.xy = np.c_[cx + self.z[:, 0] * unit, cy - self.z[:, 1] * unit]

    def landed(self, t, t0, rate):
        return int(np.clip(np.floor((t - t0) * rate), 0, self.n))

    def draw_board(self, fr, alpha=1.0, reveal=1.0):
        if alpha <= 0.003:
            return
        for k, r in enumerate((*self.rings, 3.6)):
            a = alpha * min(1.0, max(0.0, reveal * (len(self.rings) + 1) - k))
            fr.circle(self.cx, self.cy, r * self.unit, "line", 1.4, a)
        fr.circle(self.cx, self.cy, 0.16 * self.unit, "line", 1.6, alpha * reveal)
        fr.circle(self.cx, self.cy, 3.0, "ink", alpha=alpha * reveal * 0.8, fill=True)

    def draw_darts(self, fr, t, t0, rate, alpha=1.0, r=3.6, mask=None, dim=1.0):
        """Darts land in order at ``rate`` per second; each landing flashes a small expanding ring."""
        if alpha <= 0.003:
            return
        n = self.landed(t, t0, rate)
        idx = np.arange(n)
        if mask is not None:
            on = idx[mask[:n]]
            off = idx[~mask[:n]]
            draw_dots(fr, self.xy[off], r, "ball", alpha * 0.85 * dim)
            draw_dots(fr, self.xy[on], r, "ball", alpha, glow=0.5)
        else:
            draw_dots(fr, self.xy[:n], r, "ball", alpha * 0.9, glow=0.3)
        for i in range(max(0, n - 12), min(self.n, n + 1)):
            age = t - (t0 + i / rate)
            if 0 <= age < 0.3:
                u = age / 0.3
                fr.circle(self.xy[i, 0], self.xy[i, 1], r + 14 * u, "ink", 1.2, alpha * (1 - u) * 0.8)

    def draw_errors(self, fr, i, uh=1.0, uv=1.0, alpha=1.0, width=3.2):
        """Dart ``i``'s horizontal (teal) and vertical (orange) miss, drawn from the bullseye's axes."""
        if alpha <= 0.003:
            return
        x, y = self.xy[i]
        if uh > 0:
            fr.line(self.cx, y, self.cx + (x - self.cx) * uh, y, "left", width, alpha, glow=0.6)
            fr.dashed([self.cx, self.cx], [self.cy, y], "muted", 1.2, alpha * 0.5 * uh)
        if uv > 0:
            fr.line(x, self.cy, x, self.cy + (y - self.cy) * uv, "right", width, alpha, glow=0.6)
            fr.dashed([self.cx, x], [self.cy, self.cy], "muted", 1.2, alpha * 0.5 * uv)
        fr.glow_dot(x, y, 6.0, "ball", alpha, strength=1.3)

    def marginal_counts(self, n, axis, edges, mask=None):
        z = self.z[:n, axis]
        if mask is not None:
            z = z[mask[:n]]
        c, _ = np.histogram(z, bins=edges)
        return c / max(1, len(z)) / np.diff(edges)

    def draw_marginals(self, fr, n, alpha=1.0, edges=None, strip_mask=None, gap=40.0, hscale=170.0,
                       horiz=True, vert=True):
        """Density histograms of the landed darts: x errors under the target, y errors at its right."""
        if alpha <= 0.003 or n < 2:
            return
        edges = np.linspace(-3.2, 3.2, 25) if edges is None else edges
        base_y = self.cy + 3.6 * self.unit + gap + 0.42 * hscale  # floor of the x marginal; bars grow up
        base_x = self.cx + 3.6 * self.unit + gap
        if horiz:
            d = self.marginal_counts(n, 0, edges)
            body = skia.Path()
            for k in range(len(d)):
                x0 = self.cx + edges[k] * self.unit + 1
                x1 = self.cx + edges[k + 1] * self.unit - 1
                body.addRect(skia.Rect.MakeLTRB(x0, base_y - d[k] * hscale, x1, base_y))
            fr.path_fill(body, "left", alpha * 0.85, glow=0.2)
        if vert:
            d = self.marginal_counts(n, 1, edges, strip_mask)
            body = skia.Path()
            for k in range(len(d)):
                y0 = self.cy - edges[k + 1] * self.unit + 1
                y1 = self.cy - edges[k] * self.unit - 1
                body.addRect(skia.Rect.MakeLTRB(base_x, y0, base_x + d[k] * hscale, y1))
            fr.path_fill(body, "right", alpha * 0.85, glow=0.2)

    def strip(self, z0, z1):
        """Darts whose horizontal error lies in [z0, z1] (the independence demo in S13C)."""
        return (self.z[:, 0] >= z0) & (self.z[:, 0] <= z1)

    def draw_rings(self, fr, alpha=1.0, radii=(0.5, 1.0, 1.5, 2.0, 2.5), u=1.0, width=2.0):
        """Pink iso-density contours (circles: the density depends only on distance), lit from the centre out."""
        if alpha <= 0.003:
            return
        for k, r in enumerate(radii):
            a = alpha * min(1.0, max(0.0, u * (len(radii) + 1) - k)) * math.exp(-0.25 * r * r) ** 0.5
            fr.circle(self.cx, self.cy, r * self.unit, "pi", width, a, glow=0.6 * a)
