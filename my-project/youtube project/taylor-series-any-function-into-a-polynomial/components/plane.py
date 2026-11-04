"""Complex plane (Aion ComplexPlane) and domain coloring (scene-plan.md §1.6.7).

    pl = ComplexPlane(center=(960, 540), unit=220, extent=(-2.5, 2.5, -2, 2))
    pl.draw(fr, alpha)                                   # minor/major grid, real axis, violet i-axis ticks
    pl.disk(fr, 1.0, u)                                  # the pink circle of convergence
    pl.pole(fr, 1j, strength)                            # red glow (Chapter 7 only)
    img = domain_image("hill", pl.extent, (1100, 880))   # hue = arg on the Aion wheel, bands = log|f|

Domain images are computed once per (function, view, size) and cached as .npy under output/cache/domain.
"""

from __future__ import annotations

import hashlib

import numpy as np
import skia
from theme import DOMAIN_CACHE, PALETTE

from faceless_champ.draw import LINEAR, image_from_array
from faceless_champ.draw import mathtype as typmath

# Aion hue wheel, red → magenta, one turn of arg.
WHEEL = ["#FF5A4E", "#FF9F3D", "#FFD17E", "#A6E35A", "#36D6B0", "#22D3EE", "#5FB6FF", "#B58CFF", "#FF3D9A"]

FUNCS = {
    "hill": lambda z: 1 / (1 + z * z),
    "exp": np.exp,
    "id": lambda z: z,
}


def wheel_rgb(u):
    """Aion hue wheel colors (0..1 floats) for positions ``u`` (any shape, wraps)."""
    cols = np.array([PALETTE.rgb(c)[:3] for c in WHEEL + WHEEL[:1]], float)
    pos = (np.nan_to_num(np.asarray(u, float)) % 1.0) * (len(cols) - 1)
    i = np.floor(pos).astype(int)
    w = (pos - i)[..., None]
    return cols[i] * (1 - w) + cols[np.minimum(i + 1, len(cols) - 1)] * w


def domain_image(fn="hill", extent=(-2.5, 2.5, -2.0, 2.0), size=(1100, 880), bands=True, cache=True):
    """RGBA uint8 (H × W × 4) domain coloring of ``fn`` over ``extent`` = (re0, re1, im0, im1)."""
    w, h = int(size[0]), int(size[1])
    key = hashlib.sha1(repr((fn, tuple(round(v, 6) for v in extent), w, h, bands, WHEEL)).encode()).hexdigest()[:16]
    path = DOMAIN_CACHE / f"{fn}-{key}.npy"
    if cache and path.exists():
        return np.load(path)
    re = np.linspace(extent[0], extent[1], w)
    im = np.linspace(extent[3], extent[2], h)
    Z = re[None, :] + 1j * im[:, None]
    with np.errstate(all="ignore"):
        F = FUNCS[fn](Z)
    arg = (np.angle(F) / (2 * np.pi)) % 1.0
    rgb = wheel_rgb(arg)
    mag = np.abs(F)
    if bands:
        lm = np.log2(np.where(np.isfinite(mag) & (mag > 0), mag, 1e-9))
        frac = lm - np.floor(lm)
        rgb = rgb * (0.62 + 0.38 * frac)[..., None]
    rgb = np.clip(np.nan_to_num(rgb, nan=1.0), 0, 1)
    out = np.dstack([(rgb * 255).astype(np.uint8), np.full((h, w), 255, np.uint8)])
    if cache:
        DOMAIN_CACHE.mkdir(parents=True, exist_ok=True)
        np.save(path, out)
    return out


class ComplexPlane:
    def __init__(self, center=(960.0, 540.0), unit=220.0, extent=(-2.5, 2.5, -2.0, 2.0)):
        self.cx, self.cy = center
        self.unit = unit
        self.extent = extent
        self._img = {}

    def at(self, z: complex):
        return self.cx + z.real * self.unit, self.cy - z.imag * self.unit

    @property
    def rect(self):
        r0, r1, i0, i1 = self.extent
        return (self.cx + r0 * self.unit, self.cy - i1 * self.unit, (r1 - r0) * self.unit, (i1 - i0) * self.unit)

    def draw(self, fr, alpha=1.0, labels=True, minor=0.5):
        if alpha <= 0.003:
            return
        r0, r1, i0, i1 = self.extent
        x, y, w, h = self.rect
        for step, tok, wd, a in ((minor, "plane_minor", 1.0, 0.9), (1.0, "plane_major", 1.2, 0.55)):
            for v in np.arange(np.ceil(r0 / step) * step, r1 + 1e-9, step):
                px = self.cx + v * self.unit
                fr.line(px, y, px, y + h, tok, wd, alpha * a)
            for v in np.arange(np.ceil(i0 / step) * step, i1 + 1e-9, step):
                py = self.cy - v * self.unit
                fr.line(x, py, x + w, py, tok, wd, alpha * a)
        fr.line(x, self.cy, x + w, self.cy, "axis", 2.4, alpha)
        fr.line(self.cx, y, self.cx, y + h, "error", 2.0, alpha * 0.8)
        if not labels:
            return
        for v in range(int(np.ceil(r0)), int(np.floor(r1)) + 1):
            if v:
                fr.text(
                    f"{v}".replace("-", "−"), self.cx + v * self.unit, self.cy + 32, "sans", 20, 600, "muted", alpha
                )
        for v in range(int(np.ceil(i0)), int(np.floor(i1)) + 1):
            if v:
                s = {1: "i", -1: "−i"}.get(v, f"{v}i".replace("-", "−"))
                typmath.draw(fr, s, self.cx - 22, self.cy - v * self.unit, 30, "error", alpha, align="right")

    def domain(self, fr, fn="hill", alpha=1.0, size=None):
        """Domain coloring filling the plane's rect (computed once per output size)."""
        if alpha <= 0.003:
            return
        x, y, w, h = self.rect
        size = size or (round(w * fr.k), round(h * fr.k))
        key = (fn, size)
        if key not in self._img:
            self._img[key] = image_from_array(domain_image(fn, self.extent, size))
        fr.c.drawImageRect(self._img[key], skia.Rect.MakeXYWH(x, y, w, h), LINEAR, skia.Paint(Alphaf=alpha))

    def disk(self, fr, radius, u=1.0, alpha=1.0, fill=0.10):
        """Circle of convergence drawn on (sweep ``u``), pink, with a faint fill."""
        if alpha <= 0.003 or u <= 0:
            return
        r = radius * self.unit
        p = skia.Path()
        p.addArc(skia.Rect.MakeXYWH(self.cx - r, self.cy - r, 2 * r, 2 * r), 0, -360 * min(1.0, u))
        if u >= 1:
            fp = skia.Path()
            fp.addCircle(self.cx, self.cy, r)
            fr.path_fill(fp, "circle", alpha * fill)
        fr.path_stroke(p, "circle", 3.0, alpha, glow=0.6)

    def pole(self, fr, z: complex, strength=1.0, alpha=1.0, r=9.0, color="alert"):
        if alpha <= 0.003:
            return
        x, y = self.at(z)
        fr.glow_dot(x, y, r * (1 + 0.3 * strength), color, alpha, 0.35 + 0.45 * strength)
        fr.circle(x, y, r * 2.4 * (0.6 + 0.4 * strength), color, 1.6, alpha * 0.6)
