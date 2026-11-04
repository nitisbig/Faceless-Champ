"""TaylorStage: the hero graph. Ink original, gold copy, violet error, hug brackets, probe, loupe.

    st = TaylorStage("cos", view=(-4, 4, -1.6, 1.6))
    st.static(fr)                                  # dot floor, axes, ticks (cached per output size)
    st.original(fr)                                # the true function, 2.5 px ink
    st.copy(fr, coeffs("cos", 4))                  # the polynomial, 4 px gold with glow
    st.hug(fr, t, 2, 4, t0)                        # the signature motion: P2 → P4 (scene-plan.md §1.4.1)
    st.loupe(fr, (1.4, cos(1.4)), 12, (1500, 300), 150, lambda ax: ...)

Math coordinates go through ``st.ax``; everything else is design px (1920 × 1080).
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from dataclasses import dataclass

import numpy as np
import skia

from components import taylor as T
from components.motion import HUG, settle, spring
from faceless_champ.draw import LINEAR, hud, lin, offscreen
from faceless_champ.draw import mathtype as typmath

CURVE, ORIGINAL = 4.0, 2.5


@dataclass(frozen=True)
class Axes:
    """Linear map from a math view (x0, x1, y0, y1) onto a design-px rect (left, top, width, height)."""

    x0: float
    x1: float
    y0: float
    y1: float
    rect: tuple = (96.0, 140.0, 1728.0, 800.0)

    @property
    def left(self):
        return self.rect[0]

    @property
    def top(self):
        return self.rect[1]

    @property
    def right(self):
        return self.rect[0] + self.rect[2]

    @property
    def bottom(self):
        return self.rect[1] + self.rect[3]

    @property
    def sx(self):
        return self.rect[2] / (self.x1 - self.x0)

    @property
    def sy(self):
        return self.rect[3] / (self.y1 - self.y0)

    def px(self, x):
        return self.left + (np.asarray(x, float) - self.x0) * self.sx

    def py(self, y):
        return self.bottom - (np.asarray(y, float) - self.y0) * self.sy

    def at(self, x, y):
        return float(self.px(x)), float(self.py(y))

    def mx(self, px):
        return self.x0 + (px - self.left) / self.sx

    def lerp(self, other: Axes, u: float) -> Axes:
        """In-between view (camera push), rect included."""
        mix = lambda a, b: a + (b - a) * u
        return Axes(
            mix(self.x0, other.x0),
            mix(self.x1, other.x1),
            mix(self.y0, other.y0),
            mix(self.y1, other.y1),
            tuple(mix(a, b) for a, b in zip(self.rect, other.rect)),
        )

    def around(self, cx: float, cy: float, mag: float, center, radius) -> Axes:
        """A loupe view: math point (cx, cy) at design ``center``, ``mag`` × this axes' scale."""
        hx, hy = radius / (self.sx * mag), radius / (self.sy * mag)
        return Axes(
            cx - hx, cx + hx, cy - hy, cy + hy, (center[0] - radius, center[1] - radius, 2 * radius, 2 * radius)
        )


@contextmanager
def clip(fr, rect=None, path=None):
    """Clip both the crisp and the glow canvas."""
    for c in (fr.c, fr.g):
        c.save()
        if path is not None:
            c.clipPath(path, doAntiAlias=True)
        else:
            c.clipRect(skia.Rect.MakeXYWH(*rect), doAntiAlias=True)
    try:
        yield
    finally:
        fr.c.restore()
        fr.g.restore()


def curve_path(ax: Axes, xs, ys, pad: float = 60.0) -> skia.Path:
    """Polyline in design px; y is clamped just outside the rect so steep tails leave the frame cleanly."""
    X, Y = ax.px(xs), np.clip(ax.py(ys), ax.top - pad, ax.bottom + pad)
    p = skia.Path()
    p.moveTo(float(X[0]), float(Y[0]))
    for x, y in zip(X[1:], Y[1:]):
        p.lineTo(float(x), float(y))
    return p


def nice_ticks(lo: float, hi: float, step: float):
    k0, k1 = math.ceil(lo / step - 1e-9), math.floor(hi / step + 1e-9)
    return [k * step for k in range(k0, k1 + 1)]


PI_LABELS = {-2: "−2π", -1: "−π", 1: "π", 2: "2π", -3: "−3π", 3: "3π", -4: "−4π", 4: "4π"}


class TaylorStage:
    def __init__(
        self,
        f="cos",
        view=(-4.0, 4.0, -1.6, 1.6),
        rect=(96.0, 150.0, 1728.0, 780.0),
        a: float = 0.0,
        xstep: float = 1.0,
        ystep: float = 1.0,
        pi_ticks: bool = False,
        samples: int = 900,
    ):
        self.f, self.a = f, a
        self.ax = Axes(*view, rect=tuple(float(v) for v in rect))
        self.xstep, self.ystep, self.pi_ticks = xstep, ystep, pi_ticks
        self.samples = samples
        self._static = {}

    # ------------------------------------------------------------------ static layer

    def static(self, fr, alpha=1.0, focal=False, ax: Axes | None = None, labels=True):
        """Dot floor, axes and tick labels. Cached per (output scale, view) as one image."""
        if alpha <= 0.003:
            return
        ax = ax or self.ax
        if ax is not self.ax:  # animated view: draw live
            self._draw_static(fr, ax, focal, labels, alpha)
            return
        key = (round(fr.k, 4), focal, labels)
        if key not in self._static:
            surf, pen = offscreen(1920, 1080, fr.k, palette=fr.palette)
            self._draw_static(pen, ax, focal, labels, 1.0)
            self._static[key] = surf.makeImageSnapshot()
        fr.c.drawImageRect(self._static[key], skia.Rect.MakeWH(1920, 1080), LINEAR, skia.Paint(Alphaf=alpha))

    def _draw_static(self, pen, ax: Axes, focal, labels, alpha):
        # dot floor: grid token, pitch space-4 (32 px), opacity-grid
        xs = np.arange(ax.left + 16, ax.right, 32.0)
        ys = np.arange(ax.top + 16, ax.bottom, 32.0)
        dots = skia.Path()
        for y in ys:
            for x in xs:
                dots.addCircle(float(x), float(y), 1.4)
        pen.path_fill(dots, "frame", 0.08 * alpha)
        axis = "ink" if focal else "axis"
        x0, y0 = ax.at(0.0, 0.0)
        y0 = min(max(y0, ax.top), ax.bottom)
        x0 = min(max(x0, ax.left), ax.right)
        pen.line(ax.left, y0, ax.right, y0, axis, 2.4, alpha)
        pen.line(x0, ax.top, x0, ax.bottom, axis, 2.4, 0.7 * alpha)
        if not labels:
            return
        step = math.pi / 2 if self.pi_ticks else self.xstep
        for v in nice_ticks(ax.x0, ax.x1, step):
            if abs(v) < 1e-9:
                continue
            px = float(ax.px(v))
            pen.line(px, y0 - 7, px, y0 + 7, axis, 2.0, alpha)
            if self.pi_ticks:
                k = round(v / (math.pi / 2))
                if k % 2:
                    continue
                s = PI_LABELS.get(k // 2, "")
            else:
                s = f"{v:g}".replace("-", "−")
            pen.text(s, px, y0 + 34, "sans", 20, 600, "muted", alpha)
        for v in nice_ticks(ax.y0, ax.y1, self.ystep):
            if abs(v) < 1e-9:
                continue
            py = float(ax.py(v))
            pen.line(x0 - 7, py, x0 + 7, py, axis, 2.0, alpha)
            pen.text(f"{v:g}".replace("-", "−"), x0 - 16, py + 7, "sans", 20, 600, "muted", alpha, align="right")

    # ------------------------------------------------------------------ curves

    def xs(self, ax=None, lo=None, hi=None):
        ax = ax or self.ax
        return np.linspace(ax.x0 if lo is None else lo, ax.x1 if hi is None else hi, self.samples)

    def original(
        self, fr, alpha=1.0, reveal=1.0, ax=None, width=ORIGINAL, color="original", glow=0.0, lo=None, hi=None
    ):
        """The true function, revealed left to right (or from ``lo`` to ``hi``)."""
        if alpha <= 0.003 or reveal <= 0:
            return
        ax = ax or self.ax
        lo = ax.x0 if lo is None else lo
        hi = ax.x1 if hi is None else hi
        hi = lo + (hi - lo) * min(1.0, reveal)
        xs = self.xs(ax, lo, hi)
        with clip(fr, ax.rect):
            fr.path_stroke(curve_path(ax, xs, T.fn(self.f)(xs)), color, width, alpha, glow=glow)

    def copy_path(self, c, ax=None, lo=None, hi=None):
        ax = ax or self.ax
        xs = self.xs(ax, lo, hi)
        return curve_path(ax, xs, T.evaluate(c, xs, self.a))

    def copy(self, fr, c, alpha=1.0, ax=None, width=CURVE, glow=0.6, color="copy", reveal=1.0, sym=False):
        """The polynomial. ``reveal`` grows it out of x = a (symmetric if ``sym``) or from the left edge."""
        if alpha <= 0.003 or reveal <= 0:
            return None
        ax = ax or self.ax
        if reveal >= 1:
            lo, hi = ax.x0, ax.x1
        elif sym:
            r = max(self.a - ax.x0, ax.x1 - self.a) * reveal
            lo, hi = max(ax.x0, self.a - r), min(ax.x1, self.a + r)
        else:
            lo, hi = ax.x0, ax.x0 + (ax.x1 - ax.x0) * reveal
        p = self.copy_path(c, ax, lo, hi)
        with clip(fr, ax.rect):
            fr.path_stroke(p, color, width, alpha, glow=glow)
        return p

    def error_band(self, fr, c, alpha=1.0, ax=None, color="error", fill=0.25, lo=None, hi=None):
        """Violet region between the original and the copy."""
        if alpha <= 0.003:
            return
        ax = ax or self.ax
        xs = self.xs(ax, lo, hi)
        top = curve_path(ax, xs, T.fn(self.f)(xs), pad=400)
        ys = np.clip(T.evaluate(c, xs, self.a), ax.y0 - 50, ax.y1 + 50)
        X, Y = ax.px(xs[::-1]), np.clip(ax.py(ys[::-1]), ax.top - 400, ax.bottom + 400)
        for x, y in zip(X, Y):
            top.lineTo(float(x), float(y))
        top.close()
        with clip(fr, ax.rect):
            fr.path_fill(top, color, alpha * fill)

    # ------------------------------------------------------------------ hug zone

    def zone(self, n, tol=0.01, side="both"):
        return T.hug_zone(self.f, n, tol, side, self.a)

    def brackets(self, fr, r, alpha=1.0, ax=None, label=None, side="both", lift=0.0, height=46.0):
        """Gold brackets on the x-axis at a ± r, with a ``±r`` pill above the right one."""
        if alpha <= 0.003:
            return
        ax = ax or self.ax
        y = min(max(float(ax.py(0.0)), ax.top), ax.bottom) - lift
        ends = [(1, self.a + r)] + ([(-1, self.a - r)] if side == "both" else [])
        for s, xv in ends:
            x = float(ax.px(xv))
            p = skia.Path()
            p.moveTo(x - 12 * s, y - height / 2)
            p.lineTo(x, y - height / 2)
            p.lineTo(x, y + height / 2)
            p.lineTo(x - 12 * s, y + height / 2)
            fr.path_stroke(p, "copy", 2.6, alpha, glow=0.5)
        if label is False:  # brackets only, no readout
            return
        if label is None:
            label = ("±" if side == "both" else "") + f"{r:.2f}"
        x = float(ax.px(self.a + r))
        fw = len(label) * 13.5 + 30
        fr.rrect(x - fw / 2, y - height / 2 - 50, fw, 40, 20, fill="bg", alpha=0.85 * alpha)  # reads over the curve
        hud.pill(fr, x, y - height / 2 - 30, label, "copy", alpha, size=22, fill=0.10, glow=0.25)

    def chain(self, t, degrees, times):
        """A run of hugs P(d0) → P(d1) → … starting at ``times`` (overlap allowed, still continuous).

        Returns (coefficients, hug-zone radius, settle pulse) at time t.
        """
        cs = [T.coeffs(self.f, d, self.a) for d in degrees]
        rs = [self.zone(d) for d in degrees]
        m = max(len(c) for c in cs)
        cs = [np.pad(c, (0, m - len(c))) for c in cs]
        c, r, s = cs[0].copy(), rs[0], 0.0
        for k, t0 in enumerate(times):
            u = spring(t, t0)
            c += (cs[k + 1] - cs[k]) * u
            r += (rs[k + 1] - rs[k]) * u
            s = max(s, settle(t, t0))
        return c, r, s

    def hug(self, fr, t, n_from, n_to, t0, alpha=1.0, ax=None, band=True, brackets=True, glow=0.6, sweep=True):
        """The signature motion (scene-plan.md §1.4.1): P_from springs into P_to; returns the spring value."""
        ax = ax or self.ax
        u = spring(t, t0)
        c = T.blend(T.coeffs(self.f, n_from, self.a), T.coeffs(self.f, n_to, self.a), u)
        s = settle(t, t0)
        r0, r1 = self.zone(n_from), self.zone(n_to)
        r = r0 + (r1 - r0) * u
        if band:
            self.error_band(fr, c, alpha, ax)
        p = self.copy(fr, c, alpha, ax, glow=glow + 0.5 * s)
        if sweep and p is not None:
            lo, hi = self.a - r1, self.a + r1
            zp = self.copy_path(c, ax, max(ax.x0, lo), min(ax.x1, hi))
            sweep_u = lin(t, t0 + 0.4 * HUG, t0 + 0.4 * HUG + 0.9)
            stroke = skia.Path()
            skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=26).getFillPath(zp, stroke)
            fr.light_sweep(stroke, sweep_u, strength=0.55 * alpha)
        if brackets:
            self.brackets(fr, r, alpha, ax, label=f"±{r1 if u >= 1 else r:.2f}")
        return u

    # ------------------------------------------------------------------ probe and loupe

    def probe(self, fr, x, alpha=1.0, ax=None, label=None, y=None, color="x", drop=True):
        """Blue input marker (Aion ParameterSlider handle) on the x-axis, with a dashed drop to the curve."""
        if alpha <= 0.003:
            return
        ax = ax or self.ax
        px = float(ax.px(x))
        base = min(max(float(ax.py(0.0)), ax.top), ax.bottom)
        if drop and y is not None:
            fr.dashed([px, px], [base, float(ax.py(y))], color, 1.6, 0.7 * alpha, on=8, off=7)
            fr.glow_dot(px, float(ax.py(y)), 6.0, color, alpha, 0.8)
        d = skia.Path()
        d.addPoly(
            [
                skia.Point(px, base - 11),
                skia.Point(px + 11, base),
                skia.Point(px, base + 11),
                skia.Point(px - 11, base),
            ],
            True,
        )
        fr.path_fill(d, color, alpha, glow=0.6)
        if label:
            typmath.draw(fr, label, px, base + 44, 30, color, alpha)

    def loupe(self, fr, src, mag, center, radius, draw, alpha=1.0, ax=None, label=None, link=True):
        """A circular magnifier: math point ``src`` drawn ``mag`` × at design ``center`` by ``draw(sub_axes)``."""
        if alpha <= 0.003:
            return None
        ax = ax or self.ax
        sx, sy = ax.at(*src)
        sub = ax.around(src[0], src[1], mag, center, radius)
        ring = skia.Path()
        ring.addCircle(center[0], center[1], radius)
        small = radius / mag
        if link:
            d = math.hypot(center[0] - sx, center[1] - sy)
            if d > radius + small:
                ux, uy = (center[0] - sx) / d, (center[1] - sy) / d
                fr.line(
                    sx + ux * small,
                    sy + uy * small,
                    center[0] - ux * radius,
                    center[1] - uy * radius,
                    "frame",
                    1.0,
                    0.6 * alpha,
                )
            fr.circle(sx, sy, max(small, 6.0), "frame", 1.2, 0.8 * alpha)
        fr.path_fill(ring, "stage_raised", 0.96 * alpha)
        with clip(fr, path=ring):
            draw(sub)
        fr.path_stroke(ring, "frame", 2.0, alpha)
        if label is False:  # the lens alone, no magnification pill
            return sub
        tag = label or f"×{mag:g}"
        hud.pill(fr, center[0], center[1] + radius + 26, tag, "frame", alpha, size=20, fill=0.08, glow=0.0)
        return sub


def with_view(st: TaylorStage, ax: Axes) -> TaylorStage:
    """Shallow copy of a stage on a different view (for camera pushes kept separately)."""
    s = TaylorStage.__new__(TaylorStage)
    s.__dict__.update(st.__dict__)
    s.ax = ax
    s._static = {}
    return s
