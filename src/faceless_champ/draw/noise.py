"""Smooth, repeatable randomness for organic motion (OpenSimplex noise).

    from faceless_champ.draw import noise

    dx, dy, deg = noise.shake(t, 6.0)                   # handheld camera drift, about ±6 px
    pts = noise.wobble(pts, t, 2.5, fps=12)             # hand-drawn line boil
    xy = noise.drift(120, t, (0, 0, 1920, 1080))        # floating dust or particles
    grid = noise.field(t)                               # (27, 48) values for a moving background

Every function is a pure function of ``t`` and ``seed``, so frames can render in any order and in
parallel chunks. Values are roughly in [-1, 1]. Needs ``faceless-champ[motion]``. Each noise
sample is pure Python, so keep point counts in the hundreds and fields coarse; installing
``numba`` speeds opensimplex up many times.
"""

from __future__ import annotations

import math
from functools import lru_cache

__all__ = ["drift", "field", "shake", "value", "wobble"]


@lru_cache(maxsize=32)
def _gen(seed: int):
    try:
        from opensimplex import OpenSimplex
    except ImportError as exc:
        raise RuntimeError("Noise needs faceless-champ[motion] (opensimplex)") from exc
    return OpenSimplex(int(seed))


def _hold(t: float, fps: float | None) -> float:
    return t if not fps else math.floor(t * fps + 1e-9) / fps


def value(t: float, freq: float = 1.0, *, seed: int = 0, octaves: int = 1, lane: float = 0.0) -> float:
    """Noise at time ``t``; ``freq`` is roughly wiggles per second. Different ``lane`` values are independent."""
    gen = _gen(seed)
    total = norm = 0.0
    amp = 1.0
    for octave in range(max(1, int(octaves))):
        total += amp * float(gen.noise2(t * freq * 2**octave, lane + 31.7 * octave))
        norm += amp
        amp *= 0.5
    return total / norm


def shake(
    t: float, amount: float = 6.0, freq: float = 0.8, *, rotation: float = 0.3, seed: int = 0
) -> tuple[float, float, float]:
    """Handheld camera offset: (dx, dy) in pixels and a roll in degrees. Scale ``amount`` by an envelope for hits."""
    return (
        amount * value(t, freq, seed=seed, octaves=2, lane=0.0),
        amount * value(t, freq, seed=seed, octaves=2, lane=11.0),
        rotation * value(t, freq * 0.7, seed=seed, octaves=2, lane=23.0),
    )


def wobble(points, t: float, amount: float = 2.0, *, scale: float = 0.01, speed: float = 1.5, fps=None, seed=0):
    """Displace (x, y) points by up to about ``amount`` px with noise that varies along the line and in time.

    ``scale`` is noise features per pixel; ``fps=12`` holds each pose for a frame of a 12 fps "boil".
    Returns a list of (x, y) tuples.
    """
    gen = _gen(seed)
    z = _hold(t, fps) * speed
    return [
        (
            x + amount * float(gen.noise3(x * scale, y * scale, z)),
            y + amount * float(gen.noise3(x * scale + 41.3, y * scale - 17.9, z)),
        )
        for x, y in points
    ]


def drift(count: int, t: float, area, *, speed: float = 18.0, wander: float = 40.0, freq=0.15, seed: int = 0):
    """Positions of ``count`` particles drifting through ``area`` (x, y, width, height) at time ``t``.

    Each particle travels in its own direction at up to ``speed`` px/s, wanders up to about ``wander`` px
    off that line, and wraps around the area's edges. Returns a numpy array of shape (count, 2).
    """
    import numpy as np

    left, top, width, height = area
    rng = np.random.default_rng(seed)
    start = rng.uniform((0, 0), (width, height), size=(count, 2))
    angle = rng.uniform(0, 2 * np.pi, count)
    velocity = rng.uniform(0.4, 1.0, count)[:, None] * speed * np.stack([np.cos(angle), np.sin(angle)], axis=1)
    gen = _gen(seed)
    lanes = np.arange(count) * 7.31
    offset = np.stack(
        [gen.noise2array(np.array([t * freq]), lanes)[:, 0], gen.noise2array(np.array([t * freq + 97.0]), lanes)[:, 0]],
        axis=1,
    )
    position = (start + velocity * t + wander * offset) % (width, height)
    return position + (left, top)


def field(t: float, shape=(48, 27), *, scale: float = 3.0, speed: float = 0.12, seed: int = 0):
    """A (rows, columns) float32 grid of noise evolving with ``t``; ``scale`` features span the width.

    Draw it scaled up (``image_from_array`` plus a smooth filter) for fog, heat or aurora backgrounds.
    """
    import numpy as np

    columns, rows = shape
    xs = np.linspace(0, scale, columns, endpoint=False)
    ys = np.linspace(0, scale * rows / columns, rows, endpoint=False)
    grid = _gen(seed).noise3array(xs, ys, np.array([t * speed]))[0]
    return grid.astype(np.float32)
