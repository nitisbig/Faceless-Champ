"""Procedural moonlit mountain lake built from particles, smoke and light.

Metres, y up, the water surface is y = 0 and the camera flies along +z. Each point carries a
base colour (albedo times ambient and the warm lights, baked) and a separate moon factor, so the
shader can raise the moonlight over time as the moon clears the cloud.

Layers are plain dicts of arrays plus render settings for gpu.PointRenderer:
    p (N,3) position, base (N,3) colour, moon (N,) moonlight factor, size (N,) world sprite size
    kind: 0 static, 1 water glitter, 2 drifting mist, 3 rising smoke, 4 fireflies, 5 stars
    fog, sharp, smoke, occ (world size of the depth-prepass splat, 0 = not an occluder), reflect
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

CACHE = Path(__file__).with_name(".world_cache.npz")
VERSION = 4

MOON_DIR = np.array([0.03, 0.25, 1.0]) / np.linalg.norm([0.03, 0.25, 1.0])
MOON_POS = MOON_DIR * 1500.0
FAR_SHORE = 300.0
LANTERNS = np.array([[-8.7, 2.45, 8.2], [-8.7, 2.45, 10.8]])
CABIN = np.array([0.0, 0.0, 176.0])  # x set from the shore below


def shore_left(z):
    z = np.asarray(z, float)
    return -(33 + 6 * np.sin(z / 37) + 4 * np.sin(z / 13 + 1))


def shore_right(z):
    z = np.asarray(z, float)
    return 34 + 8 * np.sin(z / 45 + 2) + 3 * np.sin(z / 11)


def far_shore(x):
    return FAR_SHORE + 10 * np.sin(np.asarray(x, float) / 40)


CABIN[0] = float(shore_right(CABIN[2])) + 7.0
WINDOW = CABIN + [-3.05, 1.6, 0.0]


# ---------------------------------------------------------------- noise


def _hash(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 1274126177 + seed * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float32) / float(0xFFFFFF)


def vnoise(p, seed=0):
    i = np.floor(p).astype(np.int64)
    f = (p - i).astype(np.float32)
    u = f * f * (3 - 2 * f)
    out = np.zeros(len(p), np.float32)
    for dx in (0, 1):
        wx = u[:, 0] if dx else 1 - u[:, 0]
        for dy in (0, 1):
            wy = u[:, 1] if dy else 1 - u[:, 1]
            for dz in (0, 1):
                wz = u[:, 2] if dz else 1 - u[:, 2]
                out += wx * wy * wz * _hash(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, seed)
    return out


def fbm(p, octaves=4, seed=0):
    total = np.zeros(len(p), np.float32)
    amp, norm, freq = 1.0, 0.0, 1.0
    for o in range(octaves):
        total += amp * vnoise(p * freq, seed + 17 * o)
        norm += amp
        amp *= 0.5
        freq *= 2.03
    return total / norm


def _density(rng, cand, scale, thresh, gamma, seed):
    """Keep candidates with probability shaped by fbm density (chunked to bound memory)."""
    d = np.concatenate([fbm(c * scale, 4, seed) for c in np.array_split(cand, max(1, len(cand) // 400_000))])
    prob = np.clip((d - thresh) / (1 - thresh), 0, 1) ** gamma
    sel = rng.random(len(cand)) < prob
    return cand[sel], prob[sel]


# ---------------------------------------------------------------- warm lights (baked)


def warm(p, C):
    """Lantern and cabin-window light: (N, 3)."""
    k = np.zeros(len(p), np.float32)
    for lp in LANTERNS:
        k += 1.1 / (1 + (np.linalg.norm(p - lp, axis=1) / 2.6) ** 2.2)
    win = 1.4 / (1 + (np.linalg.norm(p - (WINDOW + [-2.5, 0, 0]), axis=1) / 4.0) ** 2.2)
    return C["lamp"][None] * k[:, None] + C["window"][None] * win[:, None]


# ---------------------------------------------------------------- shapes


def _pine(rng, base, height, radius, n):
    """Tiered conifer: thin trunk plus droopy foliage tiers. Returns points and moon factor."""
    nt = max(40, n // 12)
    v = rng.random(nt) * height * 0.35
    a = rng.uniform(0, 2 * np.pi, nt)
    trunk = np.stack([np.cos(a) * 0.18, v, np.sin(a) * 0.18], 1)
    hh = 0.12 + 0.88 * rng.random(n) ** 0.75
    tiers = rng.integers(5, 9)
    saw = 0.62 + 0.38 * np.mod(hh * tiers, 1.0)
    rmax = radius * (1 - hh) ** 1.05 * saw
    r = rmax * rng.random(n) ** 0.35
    a = rng.uniform(0, 2 * np.pi, n)
    fol = np.stack([np.cos(a) * r, hh * height - 0.3 * r, np.sin(a) * r], 1)
    out = np.concatenate([trunk, fol]) + base
    nrm = np.stack([np.cos(a), np.full(n, 0.35), np.sin(a)], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    lit = np.clip(nrm @ MOON_DIR, 0, 1) ** 1.5 * (r / np.maximum(rmax, 1e-3)) ** 2
    moon = np.concatenate([np.zeros(nt), lit])
    kind = np.concatenate([np.zeros(nt), np.ones(n)])
    return out, moon, kind


def _box_surface(rng, center, size, n):
    """Points on the surface of an axis-aligned box."""
    sx, sy, sz = size
    areas = np.array([sy * sz, sy * sz, sx * sz, sx * sz, sx * sy, sx * sy])
    face = rng.choice(6, n, p=areas / areas.sum())
    u = rng.random((n, 3)) - 0.5
    pts = u * size
    axis = face // 2
    sign = np.where(face % 2 == 0, -0.5, 0.5)
    pts[np.arange(n), axis] = sign * np.array(size)[axis]
    return pts + center


# ---------------------------------------------------------------- build


def build(rgb):
    rng = np.random.default_rng(21)
    C = {k: np.array(rgb(k), np.float32) for k in (
        "pine", "bark", "rock", "snow", "water", "mist", "wood", "lamp", "window", "moon", "star", "firefly", "sky",
    )}
    L = {}

    def layer(name, p, base, moon=None, size=None, **kw):
        n = len(p)
        L[name] = dict(
            p=np.asarray(p, np.float32),
            base=np.asarray(base, np.float32),
            moon=np.zeros(n, np.float32) if moon is None else np.asarray(moon, np.float32),
            size=np.zeros(n, np.float32) if size is None else np.asarray(size, np.float32),
            **kw,
        )

    amb = 0.035

    # pine forests: dense rows along both shores, sparser deep inland, a wall on the far shore
    pts, moon, kinds = [], [], []
    for side in (-1, 1):
        z = -40.0
        while z < FAR_SHORE:
            z += rng.uniform(2.2, 4.2)
            edge = float(shore_left(z) if side < 0 else shore_right(z))
            for depth in rng.gamma(1.3, 9.0, 3):
                x = edge + side * (1.5 + depth)
                if side > 0 and abs(z - CABIN[2]) < 7 and x < CABIN[0] + 5:
                    continue
                height = rng.uniform(9, 19) * (1.0 + 0.3 * (depth > 15))
                near = z < 140 and depth < 14
                q, m, k = _pine(rng, np.array([x, rng.uniform(-0.3, 0.6), z]), height, height * 0.24, 1700 if near else 650)
                pts.append(q), moon.append(m), kinds.append(k)
    for x in np.arange(-200, 200, 3.4):
        for _ in range(2):
            z = float(far_shore(x)) + rng.gamma(1.4, 8.0)
            height = rng.uniform(10, 22)
            q, m, k = _pine(rng, np.array([x + rng.uniform(-1.5, 1.5), rng.uniform(0, 2), z]), height, height * 0.24, 420)
            pts.append(q), moon.append(m), kinds.append(k)
    pts, moon, kinds = np.concatenate(pts), np.concatenate(moon), np.concatenate(kinds)
    shade = 0.6 + 0.8 * fbm(pts * 0.8, 2, 3)
    alb = (C["pine"][None] * kinds[:, None] + C["bark"][None] * (1 - kinds[:, None])) * shade[:, None]
    base = alb * amb * 2.0 + alb * warm(pts, C) * 0.8
    layer("pines", pts, base, moon=moon * 1.4 * shade, fog=420.0, sharp=1.0, smoke=0.25, occ=0.55, reflect=True)

    # shoreline stones and reeds
    n = 160_000
    z = rng.uniform(-40, FAR_SHORE, n)
    side = np.where(rng.random(n) < 0.5, -1, 1)
    edge = np.where(side < 0, shore_left(z), shore_right(z))
    x = edge + side * rng.normal(0.3, 1.2, n)
    y = np.abs(rng.normal(0, 0.25, n)) * (rng.random(n) < 0.7) + (rng.random(n) < 0.3) * rng.random(n) * 1.1
    p = np.stack([x, y, z], 1)
    alb = C["rock"][None] * (0.5 + fbm(p * 1.5, 2, 5)[:, None])
    layer("shore", p, alb * amb + alb * warm(p, C), moon=0.35 * rng.random(n) ** 2, fog=300.0, sharp=1.0, reflect=True)

    # mountains: ridged heightfield behind the far shore
    n = 520_000
    x = rng.uniform(-900, 900, n)
    z = rng.uniform(FAR_SHORE + 40, 1100, n)
    xz = np.stack([x * 0.004, z * 0.004, np.zeros(n)], 1)
    ridge = 1 - np.abs(2 * fbm(xz, 5, 41) - 1)
    rise = np.clip((z - FAR_SHORE - 40) / 260, 0, 1) ** 0.7
    peak = np.exp(-((x + 120) / 260) ** 2) * 1.0 + np.exp(-((x - 260) / 200) ** 2) * 0.7 + 0.35
    hgt = 115 * ridge**2.2 * rise * peak

    def height(xx, zz):
        q = np.stack([xx * 0.004, zz * 0.004, np.zeros_like(xx)], 1)
        rr = 1 - np.abs(2 * fbm(q, 5, 41) - 1)
        ri = np.clip((zz - FAR_SHORE - 40) / 260, 0, 1) ** 0.7
        pk = np.exp(-((xx + 120) / 260) ** 2) + np.exp(-((xx - 260) / 200) ** 2) * 0.7 + 0.35
        return 115 * rr**2.2 * ri * pk

    e = 3.0
    nx = -(height(x + e, z) - height(x - e, z)) / (2 * e)
    nz = -(height(x, z + e) - height(x, z - e)) / (2 * e)
    nrm = np.stack([nx, np.ones(n), nz], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    lit = np.clip(nrm @ MOON_DIR * -1 + 0.25, 0, 1)  # moon is ahead: faces turned toward the camera get rim light
    p = np.stack([x, hgt - 2, z], 1)
    snow = np.clip((hgt - 55) / 30, 0, 1)
    alb = C["rock"][None] * (1 - snow[:, None]) + C["snow"][None] * snow[:, None] * 1.6
    layer("mountains", p, alb * amb * 3.0, moon=lit * (0.4 + 0.9 * snow) * 2.0, fog=2600.0, sharp=1.0, smoke=0.3, occ=3.5, reflect=True)

    # lake surface (glitter computed in the shader); denser near the flight
    parts = []
    for z0, z1, count in ((-30, 120, 650_000), (120, FAR_SHORE + 5, 250_000)):
        z = rng.uniform(z0, z1, count)
        x = rng.uniform(shore_left(z), shore_right(z))
        parts.append(np.stack([x, np.zeros(count), z], 1))
    p = np.concatenate(parts)
    p = p[p[:, 2] < far_shore(p[:, 0])]
    base = C["water"][None] * amb * 0.6 + C["water"][None] * warm(p, C) * 0.25
    layer("water", p, base, kind=1, fog=500.0, sharp=1.0)

    # mist banks over the water, thick at the start so the flight emerges from it
    n = 2_400_000
    z = rng.uniform(-30, FAR_SHORE + 20, n)
    x = rng.uniform(shore_left(z) - 25, shore_right(z) + 25)
    y = rng.exponential(2.2, n) - 0.2
    p = np.stack([x, y, z], 1)
    mp, dens = _density(rng, p, [0.04, 0.22, 0.04], 0.36, 1.2, 61)
    start = np.exp(-(((mp[:, 2] - 6) / 14) ** 2)) * np.exp(-mp[:, 1] / 2.5)
    keep = rng.random(len(mp)) < 0.55 + start
    mp, dens, start = mp[keep], dens[keep], start[keep]
    alb = C["mist"][None] * (0.4 + dens[:, None] + 0.8 * start[:, None])
    layer("mist", mp, alb * 0.02 + alb * warm(mp, C) * 0.35, moon=0.18 * (0.4 + dens), kind=2, fog=380.0,
          sharp=0.06, smoke=1.0)

    # pier with posts, lanterns and a rowboat
    pp = []
    for x0 in np.arange(-38, -8.4, 0.28):  # planks
        m = 220
        pp.append(np.stack([x0 + rng.random(m) * 0.24, 1.0 + rng.normal(0, 0.01, m), 8.0 + rng.random(m) * 3.0], 1))
    for x0 in np.arange(-37.5, -8, 2.5):
        for z0 in (8.1, 10.9):
            m = 260
            a = rng.uniform(0, 2 * np.pi, m)
            pp.append(np.stack([x0 + np.cos(a) * 0.12, rng.uniform(-1.5, 1.05, m), z0 + np.sin(a) * 0.12], 1))
    for lp in LANTERNS:  # lantern posts
        m = 300
        a = rng.uniform(0, 2 * np.pi, m)
        pp.append(np.stack([lp[0] + np.cos(a) * 0.05, rng.uniform(1.0, lp[1] - 0.15, m), lp[2] + np.sin(a) * 0.05], 1))
        pp.append(_box_surface(rng, lp + [0, 0.05, 0], (0.26, 0.36, 0.26), 400))
    u = rng.uniform(-1, 1, 9000)  # rowboat hull tied off the pier end
    v = rng.uniform(0, np.pi, 9000)
    half = 0.75 * np.sqrt(np.clip(1 - u**4, 0, 1))
    hull = np.stack([-6.4 + half * np.cos(v), 0.35 - 0.45 * np.sin(v) * np.sqrt(np.clip(1 - u**2, 0, 1)), 12.6 + 2.2 * u], 1)
    pp.append(hull)
    pp = np.concatenate(pp)
    alb = np.repeat(C["wood"][None], len(pp), 0)
    layer("pier", pp, alb * amb + alb * warm(pp, C) * 1.3, moon=np.full(len(pp), 0.12), fog=300.0, sharp=1.0, occ=0.18, reflect=True)

    # lantern flames: small bright cores (also give the light blobs their colour)
    fl = np.concatenate([lp + rng.normal(0, 1, (900, 3)) * [0.07, 0.1, 0.07] for lp in LANTERNS])
    layer("flames", fl, np.repeat(C["lamp"][None] * 1.2, len(fl), 0), fog=400.0, sharp=1.0, reflect=True)

    # cabin on the right shore with a warm window and chimney smoke
    walls = _box_surface(rng, CABIN + [0, 1.9, 0], (6.0, 3.8, 5.0), 14000)
    t = rng.random(9000)
    s = rng.uniform(-1, 1, 9000)
    roof = CABIN + np.stack([s * 3.3, 3.8 + 2.2 * (1 - np.abs(rng.uniform(-1, 1, 9000))), (t - 0.5) * 5.6], 1)
    roof[:, 1] = CABIN[1] + 3.8 + 2.2 * (1 - np.abs(s))
    cab = np.concatenate([walls, roof])
    alb = np.repeat(C["wood"][None] * 0.8, len(cab), 0)
    layer("cabin", cab, alb * amb + alb * warm(cab, C), moon=np.full(len(cab), 0.15), fog=420.0, sharp=1.0, occ=0.4, reflect=True)
    win = WINDOW + rng.random((2500, 3)) * [0.05, 1.1, 1.4] - [0, 0.55, 0.7]
    layer("window", win, np.repeat(C["window"][None] * 1.8, len(win), 0), fog=600.0, sharp=1.0, reflect=True)
    smoke = CABIN + [1.8, 6.2, 1.0] + rng.normal(0, 0.15, (7000, 3))
    layer("chimney", smoke, np.repeat(C["mist"][None] * 0.05, len(smoke), 0), moon=np.full(len(smoke), 0.4), kind=3,
          fog=500.0, sharp=0.1, smoke=1.0)

    # fireflies near the pier and the left shore
    n = 450
    z = rng.uniform(-10, 70, n)
    p = np.stack([shore_left(z) + rng.uniform(-2, 9, n), rng.uniform(0.4, 3.5, n), z], 1)
    layer("fireflies", p, np.repeat(C["firefly"][None] * 2.5, n, 0), size=np.full(n, 0.035), kind=4, fog=120.0, sharp=1.0, reflect=True)

    # sky: stars, the moon disc, and thin cloud bands across it
    d = rng.normal(size=(9000, 3))
    d[:, 1] = np.abs(d[:, 1]) + 0.05
    d[:, 2] = np.abs(d[:, 2]) * 0.6 + 0.2
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    mag = np.clip(rng.pareto(2.4, len(d)) + 0.15, 0, 5) * (1 - 0.8 * np.clip(d @ MOON_DIR, 0, 1) ** 8)
    layer("stars", d * 2000, C["star"][None] * mag[:, None] * 0.3, kind=5, fog=1e9, sharp=1.0, reflect=True)

    e1 = np.cross(MOON_DIR, [0, 1, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(e1, MOON_DIR)
    r = 42 * np.sqrt(rng.random(20000))
    a = rng.uniform(0, 2 * np.pi, 20000)
    disc = MOON_POS + np.outer(r * np.cos(a), e1) + np.outer(r * np.sin(a), e2)
    mare = 0.75 + 0.25 * fbm(disc * 0.05, 3, 71)
    layer("moon", disc, np.zeros((len(disc), 3)), moon=1.6 * mare, fog=1e9, sharp=1.0, reflect=True)

    n = 900_000
    u = rng.uniform(-700, 500, n)
    w = rng.normal(0, 70, n)
    cl = MOON_POS * 0.85 + np.outer(u, e1) + np.outer(w + 0.12 * u, e2) + np.outer(rng.normal(0, 30, n), MOON_DIR)
    cp, dens = _density(rng, cl, [0.012, 0.03, 0.012], 0.55, 1.3, 81)
    layer("clouds", cp, C["sky"][None] * 0.01 * (0.4 + dens[:, None]), moon=0.12 * (0.3 + dens), kind=2, fog=1e9,
          sharp=0.05, smoke=1.0)
    return L


def load(rgb):
    if CACHE.exists():
        data = np.load(CACHE)
        if int(data["__version"]) == VERSION:
            layers = {}
            for key in data.files:
                if key == "__version":
                    continue
                name, field = key.split("/")
                v = data[key]
                layers.setdefault(name, {})[field] = v.item() if v.ndim == 0 else v
            return layers
    layers = build(rgb)
    flat = {"__version": np.array(VERSION)}
    for name, layer in layers.items():
        for field, v in layer.items():
            arr = np.asarray(v)
            flat[f"{name}/{field}"] = arr.astype(np.float32) if arr.dtype.kind == "f" and arr.ndim else arr
    np.savez(CACHE, **flat)
    return load(rgb)
