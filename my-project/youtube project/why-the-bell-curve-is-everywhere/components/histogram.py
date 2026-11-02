"""Blue data bars on a shared floor: exact distributions, spring growth and mass-preserving morphs.

Bars live in *standardized* units: a bar is (z centre, z width, density), with width × density = its
probability. Any distribution therefore sits on the same axes as the standard normal pdf, and the gold
Bell drawn on the same ``Axes`` fits it with no rescaling.

    sup, p = sum_pmf(*die_pmf(), 10)            # exact sum of ten dice (repeated convolution)
    A, B = bars_from(*die_pmf()), bars_from(sup, p)
    draw_bars(fr, ax, morph(A, B, u))           # 1D optimal transport: mass moves, never pops
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import skia

# -------------------------------------------------------------- exact distributions


def die_pmf(faces: int = 6, weights=None):
    """Support 1..faces and probabilities (fair unless ``weights`` given)."""
    sup = np.arange(1, faces + 1, dtype=float)
    p = np.ones(faces) if weights is None else np.asarray(weights, float)
    return sup, p / p.sum()


LOPSIDED = die_pmf(6, [0.1, 0.1, 0.1, 0.1, 0.1, 0.5])  # S10: lands on six half the time


def sum_pmf(sup, p, n: int):
    """Exact distribution of the sum of ``n`` independent copies (integer support with unit steps)."""
    out = np.array([1.0])
    for _ in range(n):
        out = np.convolve(out, p)
    lo = sup[0] * n
    return lo + np.arange(len(out), dtype=float), out


def moments(sup, p):
    m = float(np.dot(sup, p))
    return m, math.sqrt(float(np.dot((sup - m) ** 2, p)))


@dataclass
class Bars:
    z: np.ndarray  # centres (standardized)
    w: np.ndarray  # widths (standardized)
    d: np.ndarray  # densities (heights); w * d = probability
    values: np.ndarray | None = None  # raw support, for labels

    @property
    def mass(self):
        return self.w * self.d


def bars_from(sup, p, mean=None, sd=None, step=1.0) -> Bars:
    """Standardize a pmf on a regular grid (spacing ``step``) into bars."""
    sup, p = np.asarray(sup, float), np.asarray(p, float)
    m, s = moments(sup, p)
    m, s = (m if mean is None else mean), (s if sd is None else sd)
    w = np.full(len(sup), step / s)
    return Bars((sup - m) / s, w, p / w, sup)


def bars_from_samples(x, edges) -> Bars:
    """A sample histogram as density bars, in the units of ``edges`` (standardize the samples first)."""
    c, e = np.histogram(x, bins=edges)
    w = np.diff(e)
    return Bars((e[:-1] + e[1:]) / 2, w, c / max(1, len(x)) / w)


def morph(A: Bars, B: Bars, u: float) -> Bars:
    """B's bars, each starting as the slice of A that holds the same quantiles (1D optimal transport).

    At u = 0 B's bars exactly tile A's silhouette; at u = 1 they are B. Widths interpolate and heights
    follow from mass, so every bar keeps its probability the whole way.
    """
    if u >= 1.0:
        return B
    ca = np.concatenate([[0.0], np.cumsum(A.mass)])
    cb = np.concatenate([[0.0], np.cumsum(B.mass)])
    q = (cb[:-1] + cb[1:]) / 2 / cb[-1] * ca[-1]
    i = np.clip(np.searchsorted(ca, q, side="right") - 1, 0, len(A.z) - 1)
    f = np.where(A.mass[i] > 0, (q - ca[i]) / np.maximum(A.mass[i], 1e-12), 0.5)
    z_src = A.z[i] - A.w[i] / 2 + f * A.w[i]
    d_src = np.maximum(A.d[i], 1e-9)
    w_src = B.mass / d_src
    e = u * u * (3 - 2 * u)
    w = w_src + (B.w - w_src) * e
    z = z_src + (B.z - z_src) * e
    return Bars(z, w, B.mass / np.maximum(w, 1e-9), B.values)


# -------------------------------------------------------------- drawing


@dataclass
class Axes:
    """Standardized units → design px. ``unit`` px per z; ``hscale`` px per unit of density."""

    cx: float = 960.0
    floor: float = 860.0
    unit: float = 150.0
    hscale: float = 1200.0

    def x(self, z):
        return self.cx + np.asarray(z) * self.unit

    def y(self, d):
        return self.floor - np.asarray(d) * self.hscale

    def floor_line(self, fr, z0=-3.6, z1=3.6, alpha=1.0, color="line", width=1.6):
        fr.line(float(self.x(z0)), self.floor, float(self.x(z1)), self.floor, color, width, alpha)


def spring(u):
    """Bar growth: one small (~9 %) overshoot, settled by u = 1."""
    u = np.clip(np.asarray(u, float), 0.0, 1.0)
    return np.where(u >= 1.0, 1.0, 1.0 - np.exp(-6.0 * u) * np.cos(8.0 * u) * (1 - u ** 8))


def stagger(t, t0, n, spread=0.5, dur=0.55):
    """Per-bar grow progress for bars appearing left to right from ``t0``."""
    starts = t0 + spread * np.arange(n) / max(1, n - 1)
    return np.clip((t - starts) / dur, 0.0, 1.0)


def draw_bars(fr, ax: Axes, bars: Bars, alpha=1.0, grow=1.0, color="ball", gap=0.14, glow=0.25, fill=0.85,
              highlight=None, clip=None, radius=2.0):
    """Bars standing on ``ax.floor``. ``grow``: float or per-bar progress (spring applied);
    ``highlight``: {bar index: 0..1} brightens and glows; ``clip`` (z0, z1) fades bars outside the window."""
    if alpha <= 0.003:
        return
    g = spring(np.broadcast_to(np.asarray(grow, float), bars.z.shape))
    hl = highlight or {}
    body = skia.Path()
    for k, (z, w, d) in enumerate(zip(bars.z, bars.w, bars.d)):
        h = float(d * ax.hscale * g[k])
        if h < 0.4:
            continue
        a = 1.0
        if clip is not None:
            a = float(np.clip(1.0 - max(clip[0] - z, z - clip[1], 0.0) / 0.4, 0.0, 1.0))
            if a <= 0.01:
                continue
        x0 = float(ax.x(z - w / 2 * (1 - gap)))
        x1 = float(ax.x(z + w / 2 * (1 - gap)))
        rect = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, ax.floor - h, x1, ax.floor), radius, radius)
        if k in hl or a < 1.0:
            p = skia.Path()
            p.addRRect(rect)
            boost = hl.get(k, 0.0)
            fr.path_fill(p, "ink" if boost > 0.5 else color, alpha * a * min(1.0, fill + 0.3 * boost),
                         glow=glow + 0.6 * boost)
        else:
            body.addRRect(rect)
    fr.path_fill(body, color, alpha * fill, glow=glow)


def bar_tops(ax: Axes, bars: Bars, grow=1.0):
    """Design-px (x, y) of every bar's top centre (labels, the bell trace over a pile)."""
    g = spring(np.broadcast_to(np.asarray(grow, float), bars.z.shape))
    return ax.x(bars.z), ax.y(bars.d * g)


def label_bars(fr, ax: Axes, bars: Bars, texts, alpha=1.0, size=22, color="muted", below=True, grow=1.0):
    """One label per bar: under the floor (values) or above the top (counts)."""
    if alpha <= 0.003:
        return
    xs, ys = bar_tops(ax, bars, grow)
    for x, y, s in zip(xs, ys, texts):
        if s:
            fr.text(str(s), float(x), ax.floor + size * 1.4 if below else float(y) - size * 0.6, "sans", size, 600,
                    color, alpha)

