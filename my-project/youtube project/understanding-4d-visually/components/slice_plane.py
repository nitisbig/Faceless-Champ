"""The Blue Slice Plane: translucent fill, bright rim and a scan shimmer moving across it."""

from __future__ import annotations

import numpy as np
import skia
from fx import lerp


def draw_plane(fr, cam, corners, t=0.0, alpha=1.0, color="w", fill=0.06, width=2.6, glow=1.1, shimmer=0.6,
               speed=0.55):
    """``corners``: 4x3 world points in cyclic order. The shimmer is a soft line sweeping corner 0-1 -> 3-2."""
    if alpha <= 0.003:
        return
    corners = np.asarray(corners, float)
    xs, ys, z = cam.project(corners)
    if np.any(z <= 0.08):
        return
    path = skia.Path()
    path.addPoly([skia.Point(float(x), float(y)) for x, y in zip(xs, ys)], True)
    fr.path_fill(path, color, fill * alpha)
    fr.path_stroke(path, color, width, alpha, glow=glow)
    if shimmer > 0:
        u = (t * speed) % 1.0
        a = corners[0] + (corners[3] - corners[0]) * u
        b = corners[1] + (corners[2] - corners[1]) * u
        sx, sy, _ = cam.project(np.array([a, b]))
        env = np.sin(np.pi * u)
        fr.line(sx[0], sy[0], sx[1], sy[1], color, 1.4, alpha * shimmer * env, glow=0.6 * env)
    # Corner ticks: tiny bright brackets that make the plane read as an instrument, not a polygon.
    for k in range(4):
        p, q, r = corners[k], corners[(k + 1) % 4], corners[(k - 1) % 4]
        a = cam.project(np.array([lerp(p, q, 0.06), p, lerp(p, r, 0.06)]))
        fr.poly(a[0], a[1], "ink", 2.0, 0.8 * alpha)


def cut_line(fr, cam, p0, p1, alpha=1.0, color="w"):
    """The bright line where the plane meets a solid."""
    xs, ys, z = cam.project(np.array([p0, p1], float))
    if np.all(z > 0.08):
        fr.line(xs[0], ys[0], xs[1], ys[1], color, 2.8, alpha, glow=1.2)

