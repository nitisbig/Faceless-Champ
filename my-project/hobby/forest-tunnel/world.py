"""Forest tunnel point cloud, stored in path coordinates.

Every point is (s, u, v): s = distance along the path, u = lateral offset (right positive),
v = height. The shader turns these into world positions through the path tables below, which
lets it light the scene relative to the path and curl the whole world into a tube.

The look follows a LiDAR-style scan: a pale gravel path in scan rows, gnarled trunks with roots,
a dense arching canopy and side thickets, and loose white motes.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

CACHE = Path(__file__).with_name(".world_cache.npz")
VERSION = 1

S_MIN, S_MAX = -20.0, 220.0
PATH_HALF = 1.6
TURN_A, TURN_B, TURN = 58.0, 118.0, 0.95  # the path bends right between these s values (radians)


# ---------------------------------------------------------------- path


def _tables(n=4096):
    s = np.linspace(S_MIN, S_MAX, n)
    u = np.clip((s - TURN_A) / (TURN_B - TURN_A), 0, 1)
    heading = TURN * u * u * (3 - 2 * u)
    ds = s[1] - s[0]
    x = np.concatenate([[0], np.cumsum(np.sin(heading[:-1]) * ds)])
    z = np.concatenate([[0], np.cumsum(np.cos(heading[:-1]) * ds)]) + S_MIN
    y = 0.35 * np.sin(s / 23.0)
    center = np.stack([x, y, z], 1)
    lateral = np.stack([np.cos(heading), np.zeros(n), -np.sin(heading)], 1)
    tangent = np.stack([np.sin(heading), np.zeros(n), np.cos(heading)], 1)
    return s, center.astype(np.float32), lateral.astype(np.float32), tangent.astype(np.float32)


PATH_S, PATH_C, PATH_L, PATH_T = _tables()


def frame_at(s):
    """(center, lateral, tangent) of the path at scalar s."""
    i = np.interp(s, PATH_S, np.arange(len(PATH_S)))
    i0 = int(np.clip(np.floor(i), 0, len(PATH_S) - 2))
    f = i - i0
    return tuple(a[i0] * (1 - f) + a[i0 + 1] * f for a in (PATH_C, PATH_L, PATH_T))


def to_world(suv):
    s, u, v = suv
    c, lat, _ = frame_at(s)
    return c + lat * u + np.array([0, v, 0])


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
    d = np.concatenate([fbm(c * scale, 4, seed) for c in np.array_split(cand, max(1, len(cand) // 400_000))])
    prob = np.clip((d - thresh) / (1 - thresh), 0, 1) ** gamma
    sel = rng.random(len(cand)) < prob
    return cand[sel], prob[sel]


# ---------------------------------------------------------------- shapes (path coordinates)


def _curve(rng, start, direction, length, n, wobble, r0, r1):
    """A gnarled tube along a wandering direction: points on its surface."""
    t = rng.random(n)
    steps = 24
    d = np.array(direction, float)
    d /= np.linalg.norm(d)
    pts = [np.array(start, float)]
    for _ in range(steps):
        d = d + rng.normal(0, wobble, 3)
        d /= np.linalg.norm(d)
        pts.append(pts[-1] + d * length / steps)
    pts = np.array(pts)
    idx = t * steps
    i0 = np.minimum(idx.astype(int), steps - 1)
    f = (idx - i0)[:, None]
    axis = pts[i0] * (1 - f) + pts[i0 + 1] * f
    r = (r0 + (r1 - r0) * t) * (1 + 0.18 * np.sin(rng.uniform(0, 2 * np.pi, n) * 3))
    off = rng.normal(0, 1, (n, 3))
    off /= np.linalg.norm(off, axis=1, keepdims=True)
    return axis + off * r[:, None]


def _tree(rng, s0, u0):
    """Gnarled trunk leaning over the path, with roots and arching branches."""
    side = np.sign(u0)
    height = rng.uniform(3.5, 6.5)
    parts = [_curve(rng, (s0, u0, -0.1), (rng.normal(0, 0.15), -side * rng.uniform(0.15, 0.45), 1.0), height, 1700, 0.1,
                    rng.uniform(0.22, 0.38), 0.12)]
    for _ in range(rng.integers(3, 6)):  # roots
        a = rng.uniform(0, 2 * np.pi)
        parts.append(_curve(rng, (s0, u0, 0.15), (np.cos(a), np.sin(a), -0.25), rng.uniform(0.8, 2.2), 200, 0.18, 0.12, 0.03))
    top = parts[0][np.argsort(parts[0][:, 2])[-50:]].mean(axis=0)
    for _ in range(rng.integers(3, 7)):  # branches arch over the path or spread out
        inward = rng.random() < 0.6
        d = (rng.normal(0, 0.5), (-side if inward else side) * rng.uniform(0.4, 1.0), rng.uniform(0.3, 0.9))
        start = top - [0, 0, rng.uniform(0, height * 0.35)]
        parts.append(_curve(rng, start, d, rng.uniform(2.0, 4.5), 420, 0.2, 0.1, 0.03))
    return np.concatenate(parts)


# ---------------------------------------------------------------- build


def build(rgb):
    rng = np.random.default_rng(3)
    C = {k: np.array(rgb(k), np.float32) for k in ("gravel", "litter", "bark", "leaf", "leaf_dark", "mote")}
    L = {}

    def layer(name, suv, alb, size=None, **kw):
        n = len(suv)
        L[name] = dict(suv=np.asarray(suv, np.float32), alb=np.asarray(alb, np.float32),
                       size=np.zeros(n, np.float32) if size is None else np.asarray(size, np.float32), **kw)

    # gravel path in scan rows (rows across the path give the striated scan texture)
    rows = np.arange(-12, 200, 0.07)
    per_row = np.where(rows < 140, 75, 38)
    s = np.repeat(rows, per_row) + rng.normal(0, 0.012, per_row.sum())
    u = rng.uniform(-PATH_HALF - 0.3, PATH_HALF + 0.3, len(s))
    keep = rng.random(len(s)) < np.clip((PATH_HALF + 0.3 - np.abs(u)) / 0.5, 0, 1)
    s, u = s[keep], u[keep]
    tex = fbm(np.stack([s * 0.8, u * 0.8, np.zeros_like(s)], 1), 3, 2)
    v = 0.04 * (tex - 0.5) + 0.03 * (1 - (u / PATH_HALF) ** 2)
    suv = np.stack([s, u, v], 1)
    layer("path", suv, C["gravel"][None] * (0.55 + 0.7 * tex[:, None]), occ=0.0)
    gi = rng.choice(len(suv), 14000, replace=False)
    layer("path_streak", suv[gi] + [0, 0, 0.01], C["gravel"][None] * np.ones((len(gi), 1)) * 1.3, streak=True)

    # ground litter and roots-floor either side
    n = 900_000
    s = rng.uniform(-12, 200, n)
    side = np.where(rng.random(n) < 0.5, -1, 1)
    u = side * (PATH_HALF + 0.1 + rng.gamma(1.3, 1.6, n))
    cand = np.stack([s, u, np.zeros(n)], 1)
    gp, dens = _density(rng, cand, [0.6, 0.6, 0], 0.3, 0.8, 5)
    gp[:, 2] = 0.12 * fbm(gp * 1.3, 2, 6) + 0.25 * rng.random(len(gp)) ** 6
    layer("ground", gp, C["litter"][None] * (0.4 + dens[:, None]), occ=0.08)

    # trees lining both sides
    tp = []
    for side in (-1, 1):
        s = -12.0
        while s < 200:
            s += rng.uniform(1.8, 3.4)
            tp.append(_tree(rng, s, side * rng.uniform(2.1, 3.6)))
            if rng.random() < 0.5:  # second row behind
                tp.append(_tree(rng, s + rng.uniform(-1, 1), side * rng.uniform(4.5, 7.5)))
    tp = np.concatenate(tp)
    shade = 0.5 + 0.8 * fbm(tp * 2.0, 2, 8)
    layer("trees", tp, C["bark"][None] * shade[:, None], occ=0.1)

    # canopy arch and side thickets
    n = 2_600_000
    s = rng.uniform(-12, 205, n)
    phi = rng.uniform(-1.75, 1.75, n)
    r = 3.9 + 0.9 * rng.random(n) + rng.gamma(1.5, 0.8, n)
    arch = np.stack([s, r * np.sin(phi), 1.4 + r * np.cos(phi) * 0.9], 1)
    arch = arch[arch[:, 2] > 0.3]
    ap, dens = _density(rng, arch, [0.45, 0.6, 0.6], 0.42, 1.1, 11)
    n = 1_200_000
    s = rng.uniform(-12, 205, n)
    side = np.where(rng.random(n) < 0.5, -1, 1)
    bush = np.stack([s, side * (2.6 + rng.gamma(1.5, 1.6, n)), rng.random(n) ** 1.3 * 3.2], 1)
    bp, bdens = _density(rng, bush, [0.6, 0.6, 0.8], 0.45, 1.1, 13)
    cp = np.concatenate([ap, bp])
    cd = np.concatenate([dens, bdens])
    mixk = fbm(cp * 0.35, 2, 17)[:, None]
    alb = C["leaf"][None] * mixk + C["leaf_dark"][None] * (1 - mixk)
    layer("canopy", cp, alb * (0.45 + 0.8 * cd[:, None]), occ=0.12, smoke=0.12)

    # loose white motes (square sprites with streaks)
    n = 26000
    s = rng.uniform(-12, 200, n)
    u = rng.uniform(-4.5, 4.5, n)
    v = rng.uniform(0.15, 6.0, n)
    size = 0.012 + 0.03 * rng.random(n) ** 4
    layer("motes", np.stack([s, u, v], 1), C["mote"][None] * (0.6 + 1.6 * rng.random((n, 1)) ** 3), size=size,
          kind=1, streak=True, unlit=True)
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
