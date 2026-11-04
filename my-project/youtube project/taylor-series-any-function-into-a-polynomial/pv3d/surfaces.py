"""True-3D surfaces for PyVista (``draw.mesh3d``), in view coordinates (x right, y up, z depth).

    pole_surface(1.0)          # |1/(1+z²)| over the complex plane, domain-colored, poles cut off at ``cap``
    loss_surface()             # an illustrative, seeded loss landscape (S44C)
    hessian_bowl(p)            # its second-order Taylor bowl at p (the "simple bowl")

Re z runs along x, Im z along depth; heights are |f| × ``height_scale``. Rendered with ``mesh3d.render(..., cache=)``
so each camera position renders once.
"""

from __future__ import annotations

import numpy as np
import pyvista as pv
from components.plane import FUNCS, wheel_rgb

EXTENT = (-2.5, 2.5, -2.0, 2.0)


def _grid(X, H, Z, rgb=None):
    g = pv.StructuredGrid(X, H, Z)
    if rgb is not None:  # structured points run with the first index fastest
        g.point_data["rgb"] = np.ascontiguousarray(rgb.transpose(1, 0, 2).reshape(-1, 3))
    return g.extract_surface(algorithm="dataset_surface").triangulate()


def pole_surface(height_scale=1.0, cap=3.2, n=(181, 145), extent=EXTENT, fn="hill"):
    """|f(z)| as a height field, colored by arg(f) on the Aion wheel (banded by log2|f|). Points beyond ``cap`` are clipped."""
    re = np.linspace(extent[0], extent[1], n[0])
    im = np.linspace(extent[2], extent[3], n[1])
    R, I = np.meshgrid(re, im, indexing="ij")
    with np.errstate(all="ignore"):
        F = FUNCS[fn](R + 1j * I)
    mag = np.nan_to_num(np.abs(F), nan=cap, posinf=cap)
    lm = np.log2(np.maximum(mag, 1e-9))
    rgb = wheel_rgb((np.angle(F) / (2 * np.pi)) % 1.0) * (0.62 + 0.38 * (lm - np.floor(lm)))[..., None]
    H = np.minimum(mag, cap) * height_scale
    rgb = (np.clip(np.nan_to_num(rgb, nan=1.0), 0, 1) * 255).astype(np.uint8)
    return _grid(R, H, I, rgb)


def surface_style(**kw):
    return {
        "scalars": "rgb",
        "rgb": True,
        "smooth_shading": True,
        "specular": 0.45,
        "specular_power": 40,
        "ambient": 0.25,
        "diffuse": 0.8,
        **kw,
    }


# ----------------------------------------------------------------------------- loss landscape (illustration)

_RNG = np.random.default_rng(44)
_BUMPS = [
    (_RNG.uniform(-2.2, 2.2), _RNG.uniform(-2.2, 2.2), _RNG.uniform(0.4, 0.9), _RNG.uniform(0.5, 1.1)) for _ in range(6)
]


def loss(x, y):
    """Illustrative loss: a broad bowl with seeded bumps (no claim attached to its values)."""
    z = 0.09 * (x * x + 0.7 * y * y)
    for bx, by, amp, s in _BUMPS:
        z = z + amp * np.exp(-((x - bx) ** 2 + (y - by) ** 2) / (2 * s * s)) * 0.6
    return z


def loss_surface(n=161, half=3.0, scale=1.0):
    xs = np.linspace(-half, half, n)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    return _grid(X, loss(X, Y) * scale, Y)


def hessian(p, h=1e-3):
    """Value, gradient and Hessian of ``loss`` at p (central differences)."""
    x, y = p
    f = lambda a, b: float(loss(a, b))
    f0 = f(x, y)
    gx = (f(x + h, y) - f(x - h, y)) / (2 * h)
    gy = (f(x, y + h) - f(x, y - h)) / (2 * h)
    fxx = (f(x + h, y) - 2 * f0 + f(x - h, y)) / h**2
    fyy = (f(x, y + h) - 2 * f0 + f(x, y - h)) / h**2
    fxy = (f(x + h, y + h) - f(x + h, y - h) - f(x - h, y + h) + f(x - h, y - h)) / (4 * h * h)
    return f0, np.array([gx, gy]), np.array([[fxx, fxy], [fxy, fyy]])


def hessian_bowl(p, radius=1.1, n=(24, 97), scale=1.0, lift=0.08):
    """The second-order Taylor patch of ``loss`` around p: the simple bowl that replaces the landscape (a disc)."""
    f0, g, Hm = hessian(p)
    r = np.linspace(0.0, radius, n[0])
    th = np.linspace(0.0, 2 * np.pi, n[1])
    Rr, Th = np.meshgrid(r, th, indexing="ij")
    U, V = Rr * np.cos(Th), Rr * np.sin(Th)
    Q = f0 + g[0] * U + g[1] * V + 0.5 * (Hm[0, 0] * U * U + 2 * Hm[0, 1] * U * V + Hm[1, 1] * V * V)
    return _grid(p[0] + U, (Q + lift) * scale, p[1] + V)
