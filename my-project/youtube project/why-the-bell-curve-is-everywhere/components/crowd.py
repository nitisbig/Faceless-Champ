"""People as data: silhouettes that stand in a row and collapse into a dot histogram of their heights.

    heights = sample_heights(10_000)                     # seeded N(175, 7) cm, illustrative
    person(fr, x, floor, height_px, alpha)               # one ink silhouette, feet at (x, floor)
    xy = dot_layout(heights, x_of, bin_cm=1.0, r=2.2)    # stacked dot histogram positions
    draw_dots(fr, xy[:n], 2.2, "ball")
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import skia

from components.darts import draw_dots  # noqa: F401  (re-exported for scenes)

SEED_HEIGHTS = 21
MEAN_CM, SD_CM = 175.0, 7.0


def sample_heights(n=10_000, seed=SEED_HEIGHTS, mean=MEAN_CM, sd=SD_CM):
    return np.random.default_rng(seed).normal(mean, sd, n)


@lru_cache(maxsize=1)
def _unit_person() -> skia.Path:
    """A simple standing figure 1.0 tall, feet centred at (0, 0), drawn upward (negative y)."""
    p = skia.Path()
    p.addCircle(0.0, -0.905, 0.075)  # head
    body = skia.Path()
    body.moveTo(-0.13, -0.80)  # shoulders
    body.quadTo(0.0, -0.835, 0.13, -0.80)
    body.quadTo(0.155, -0.79, 0.15, -0.70)
    body.lineTo(0.135, -0.46)  # arm to hand
    body.lineTo(0.105, -0.46)
    body.lineTo(0.10, -0.66)
    body.lineTo(0.085, -0.48)  # hip
    body.lineTo(0.07, 0.0)  # right leg
    body.lineTo(0.02, 0.0)
    body.lineTo(0.0, -0.42)  # crotch
    body.lineTo(-0.02, 0.0)
    body.lineTo(-0.07, 0.0)  # left leg
    body.lineTo(-0.085, -0.48)
    body.lineTo(-0.10, -0.66)
    body.lineTo(-0.105, -0.46)
    body.lineTo(-0.135, -0.46)
    body.lineTo(-0.15, -0.70)
    body.quadTo(-0.155, -0.79, -0.13, -0.80)
    body.close()
    p.addPath(body)
    return p


def person_path(x, floor, height_px):
    p = skia.Path(_unit_person())
    m = skia.Matrix()
    m.setScale(height_px, height_px)
    m.postTranslate(x, floor)
    p.transform(m)
    return p


def person(fr, x, floor, height_px, alpha=1.0, color="ink", fill=0.0, width=1.8, glow=0.0):
    """One silhouette: an outline (``fill`` adds a translucent body)."""
    if alpha <= 0.003:
        return
    p = person_path(x, floor, height_px)
    if fill > 0:
        fr.path_fill(p, color, alpha * fill)
    fr.path_stroke(p, color, width, alpha, glow=glow)


def dot_layout(values, x_of, bin_w=1.0, r=2.2, floor=860.0, origin=None, cols=None):
    """Dot-histogram positions for ``values``: binned by ``bin_w`` (value units), stacked upward in order.

    ``x_of`` maps a value to design px. Each bin holds ``cols`` dots per layer (default: as many as fit).
    """
    values = np.asarray(values, float)
    lo = values.min() if origin is None else origin
    k = np.floor((values - lo) / bin_w).astype(np.int64)
    centres = lo + (k + 0.5) * bin_w
    bin_px = abs(float(x_of(lo + bin_w) - x_of(lo)))
    d = 2 * r
    m = cols or max(1, int(bin_px // d))
    order = np.argsort(k, kind="stable")
    slot = np.zeros(len(values), np.int64)
    seen: dict[int, int] = {}
    for i in order:
        j = seen.get(k[i], 0)
        slot[i] = j
        seen[k[i]] = j + 1
    layer, c = np.divmod(slot, m)
    x = x_of(centres) - (m - 1) / 2 * d + c * d
    y = floor - r - layer * d
    return np.c_[x, y]

