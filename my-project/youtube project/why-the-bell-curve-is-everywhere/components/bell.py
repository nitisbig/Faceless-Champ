"""The gold law: the real normal pdf on a histogram ``Axes``, with its signature motions (scene-plan.md §1.4).

    bell = Bell(ax)
    bell.draw(fr, mu=0, sigma=1, reveal=u)          # trace left to right
    bell.snap(fr, t, t0)                            # trace 0.6 s, glow pulse, light sweep: "the law appears"
    bell.band(fr, k=1)                              # the ±kσ band fill (violet)
    bell.crack(fr, u); bell.tail(fr, u)             # the break and the red heavy tail (Chapter 5)

``mu`` and ``sigma`` are in the axes' standardized units, so a fitted histogram and its bell share a frame.
"""

from __future__ import annotations

import math

import numpy as np
import skia
from faceless_champ.draw import ease_io, ease_out, lin, smooth

from components.histogram import Axes, Bars

SQRT2PI = math.sqrt(2 * math.pi)


def pdf(z, mu=0.0, sigma=1.0):
    z = np.asarray(z, float)
    return np.exp(-0.5 * ((z - mu) / sigma) ** 2) / (sigma * SQRT2PI)


def band_share(k: float) -> float:
    """P(|Z| < k), e.g. 0.6827 for k = 1 (erf, never typed)."""
    return math.erf(k / math.sqrt(2))


def fit(bars: Bars):
    """Moment-matched (mu, sigma) of a bar set, in its own standardized units."""
    m = bars.mass / bars.mass.sum()
    mu = float(np.dot(bars.z, m))
    var = float(np.dot((bars.z - mu) ** 2, m) + np.dot(bars.w ** 2 / 12, m))
    return mu, math.sqrt(var)


class Bell:
    def __init__(self, ax: Axes, z0=-3.6, z1=3.6, n=280):
        self.ax, self.z0, self.z1, self.n = ax, z0, z1, n

    def points(self, mu=0.0, sigma=1.0, scale=1.0, z0=None, z1=None, n=None):
        z = np.linspace(self.z0 if z0 is None else z0, self.z1 if z1 is None else z1, n or self.n)
        return self.ax.x(z), self.ax.y(pdf(z, mu, sigma) * scale)

    def path(self, mu=0.0, sigma=1.0, scale=1.0, reveal=1.0, z0=None, z1=None):
        a = self.z0 if z0 is None else z0
        b = self.z1 if z1 is None else z1
        b = a + (b - a) * max(0.0, min(1.0, reveal))
        xs, ys = self.points(mu, sigma, scale, a, b, max(8, int(self.n * (b - a) / (self.z1 - self.z0))))
        p = skia.Path()
        p.moveTo(float(xs[0]), float(ys[0]))
        for x, y in zip(xs[1:], ys[1:]):
            p.lineTo(float(x), float(y))
        return p

    def area_path(self, mu=0.0, sigma=1.0, scale=1.0, a=None, b=None):
        """Closed region under the curve between z = a and z = b."""
        a = self.z0 if a is None else a
        b = self.z1 if b is None else b
        p = self.path(mu, sigma, scale, 1.0, a, b)
        p.lineTo(float(self.ax.x(b)), self.ax.floor)
        p.lineTo(float(self.ax.x(a)), self.ax.floor)
        p.close()
        return p

    def draw(self, fr, mu=0.0, sigma=1.0, scale=1.0, reveal=1.0, alpha=1.0, width=3.0, glow=0.7, color="bell",
             fill=0.0):
        if alpha <= 0.003 or reveal <= 0:
            return
        if fill > 0:
            fr.path_fill(self.area_path(mu, sigma, scale), color, alpha * fill)
        p = self.path(mu, sigma, scale, reveal)
        fr.path_stroke(p, color, width, alpha, glow=glow)
        if reveal < 1.0:  # a hot pen tip while tracing
            xs, ys = self.points(mu, sigma, scale, self.z0, self.z0 + (self.z1 - self.z0) * reveal, 2)
            fr.glow_dot(float(xs[-1]), float(ys[-1]), width * 1.3, "light", alpha, strength=1.3)

    def outline(self, mu=0.0, sigma=1.0, scale=1.0, width=3.0):
        """The stroked curve as a fillable shape (clip region for the light sweep)."""
        out = skia.Path()
        skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=width * 2.2, StrokeCap=skia.Paint.kRound_Cap).getFillPath(
            self.path(mu, sigma, scale), out)
        return out

    def snap(self, fr, t, t0, mu=0.0, sigma=1.0, scale=1.0, alpha=1.0, width=3.0, trace=0.6, fill=0.0):
        """The film's signature: trace left to right in ``trace`` s, a glow pulse, then a light sweep."""
        if t < t0 or alpha <= 0.003:
            return
        u = ease_io(lin(t, t0, t0 + trace))
        pulse = math.exp(-max(0.0, t - t0 - trace) / 0.35) if t > t0 + trace else 0.0
        self.draw(fr, mu, sigma, scale, u, alpha, width, 0.7 + 0.9 * pulse, fill=fill * smooth(u))
        if u >= 1.0:
            fr.light_sweep(self.outline(mu, sigma, scale, width), lin(t, t0 + trace, t0 + trace + 0.7), strength=0.95)

    def band(self, fr, k=1.0, mu=0.0, sigma=1.0, scale=1.0, alpha=1.0, fill=0.30, color="sigma", edges=True, u=1.0):
        """±kσ band under the curve; ``u`` grows it outward from the centre."""
        if alpha <= 0.003 or u <= 0:
            return
        h = k * sigma * ease_out(u)
        fr.path_fill(self.area_path(mu, sigma, scale, mu - h, mu + h), color, alpha * fill)
        if edges:
            for z in (mu - h, mu + h):
                x = float(self.ax.x(z))
                y = float(self.ax.y(pdf(z, mu, sigma) * scale))
                fr.line(x, self.ax.floor, x, y, color, 2.0, alpha * 0.9, glow=0.4)

    def mean_line(self, fr, mu=0.0, sigma=1.0, scale=1.0, alpha=1.0, color="bell", u=1.0):
        if alpha <= 0.003 or u <= 0:
            return
        x = float(self.ax.x(mu))
        top = float(self.ax.y(pdf(mu, mu, sigma) * scale))
        fr.line(x, self.ax.floor, x, self.ax.floor + (top - self.ax.floor) * ease_out(u), color, 2.0, alpha, glow=0.5)

    # -- the break (S03D, S20A, S22) ----------------------------------------------------
    def crack(self, fr, u, at=0.9, mu=0.0, sigma=1.0, scale=1.0, alpha=1.0, width=3.0, gap=10.0):
        """Split the curve at z = ``at``: the right piece drops and drifts, with a jagged red edge."""
        if alpha <= 0.003:
            return
        e = ease_out(u)
        left = self.path(mu, sigma, scale, 1.0, self.z0, at)
        right = self.path(mu, sigma, scale, 1.0, at, self.z1)
        right.offset(gap * e, 0.6 * gap * e)
        fr.path_stroke(left, "bell", width, alpha, glow=0.6)
        fr.path_stroke(right, "bell", width, alpha * (1 - 0.6 * e), glow=0.6 * (1 - e))
        if 0.0 < u:
            x = float(self.ax.x(at))
            y = float(self.ax.y(pdf(at, mu, sigma) * scale))
            rng = np.random.default_rng(3)
            jag = np.cumsum(rng.uniform(-1, 1, 7)) * 3.0
            ys = y - 26 + np.linspace(0, 52, 7)
            fr.poly(x + gap * 0.5 * e + jag, ys, "tail", 1.6, alpha * min(1.0, 3 * u) * (1 - 0.5 * e), glow=1.0)

    def tail(self, fr, u, at=0.9, mu=0.0, sigma=1.0, scale=1.0, alpha=1.0, width=3.0, reach=9.0, power=1.6):
        """A red heavy tail growing right from z = ``at``: density ~ c / (1 + z - at)^power, matched at the join.
        ``reach`` is in z units and may run past the frame edge."""
        if alpha <= 0.003 or u <= 0:
            return
        y0 = float(pdf(at, mu, sigma) * scale)
        z = np.linspace(at, at + reach * ease_out(u), 220)
        d = y0 / (1 + (z - at)) ** power
        xs, ys = self.ax.x(z), self.ax.y(d)
        p = skia.Path()
        p.moveTo(float(xs[0]), float(ys[0]))
        for x, y in zip(xs[1:], ys[1:]):
            p.lineTo(float(x), float(y))
        fr.path_stroke(p, "tail", width, alpha, glow=0.9)
        fr.glow_dot(float(xs[-1]), float(ys[-1]), width * 1.3, "tail", alpha, strength=1.2)
