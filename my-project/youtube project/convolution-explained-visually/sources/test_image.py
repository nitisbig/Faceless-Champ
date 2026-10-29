"""Procedural night-skyline test image (no external photo needed).

All blur / edge results in the video are real convolutions of this array.
"""

from functools import lru_cache

import numpy as np
from scipy import ndimage


@lru_cache(maxsize=4)
def skyline(h: int = 300, w: int = 340, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:h, 0:w].astype(float)
    horizon = int(h * 0.80)
    img = 0.05 + 0.20 * (y / horizon) ** 2.2  # dark zenith, glow near the horizon
    # moon with a soft halo
    cx, cy, r = w * 0.70, h * 0.25, h * 0.10
    d = np.hypot(x - cx, y - cy)
    img = img + 0.22 * np.exp(-np.clip(d - r, 0, None) / 16.0)
    img = np.where(d < r, 0.97, img)
    # stars
    for _ in range(40):
        sx, sy = rng.integers(0, w), rng.integers(0, int(h * 0.5))
        if np.hypot(sx - cx, sy - cy) > r * 1.6:
            img[sy, sx] = max(img[sy, sx], rng.uniform(0.5, 0.9))
    # skyline silhouettes with lit windows
    xpos = 0
    while xpos < w:
        bw = int(rng.integers(20, 46))
        bh = int(rng.integers(int(h * 0.16), int(h * 0.50)))
        top = horizon - bh
        img[top:horizon, xpos : xpos + bw - 3] = 0.035
        if rng.random() < 0.3:  # antenna
            ax = xpos + bw // 2
            img[top - 14 : top, ax : ax + 2] = 0.035
        for wy in range(top + 7, horizon - 6, 10):
            for wx in range(xpos + 5, xpos + bw - 9, 8):
                if rng.random() < 0.42:
                    img[wy : wy + 4, wx : wx + 3] = rng.uniform(0.6, 0.95)
        xpos += bw
    # water: flipped, rippled, darker reflection
    depth = h - horizon
    src = img[horizon - 1 : horizon - 1 - depth : -1, :]
    rows = np.arange(depth)[:, None]
    shift = (2.5 * np.sin(rows * 0.9 + x[:depth] * 0.05)).astype(int)
    cols = np.clip(x[:depth].astype(int) + shift, 0, w - 1)
    refl = src[np.arange(depth)[:, None], cols] * 0.42
    img[horizon:, :] = refl + 0.02
    return np.clip(img, 0, 1)


def gaussian_kernel(size: int = 9, sigma: float = 2.4) -> np.ndarray:
    ax = np.arange(size) - size // 2
    g = np.exp(-(ax**2) / (2 * sigma**2))
    k = np.outer(g, g)
    return k / k.sum()


@lru_cache(maxsize=4)
def blurred(h: int = 300, w: int = 340) -> np.ndarray:
    return ndimage.convolve(skyline(h, w), gaussian_kernel(), mode="nearest")


@lru_cache(maxsize=4)
def edges(h: int = 300, w: int = 340) -> np.ndarray:
    """Magnitude of horizontal + vertical [-1 0 +1] kernel responses, normalised."""
    img = skyline(h, w)
    kx = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], float)
    gx = ndimage.convolve(img, kx, mode="nearest")
    gy = ndimage.convolve(img, kx.T, mode="nearest")
    mag = np.hypot(gx, gy)
    return np.clip(mag / np.percentile(mag, 99.3), 0, 1)


def tint(values: np.ndarray, color, highlight: float = 0.35) -> np.ndarray:
    """Grayscale 0..1 -> opaque RGBA uint8 tinted toward ``color`` (r,g,b 0..1)."""
    v = values[..., None]
    rgb = v * np.array(color)[None, None, :] + highlight * v**3
    out = np.empty(values.shape + (4,), np.uint8)
    out[..., :3] = np.clip(rgb * 255, 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return out
