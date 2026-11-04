"""Procedural point-cloud cosmos for the cosmic drift.

Everything is points: smoke is clumpy fbm-sampled dust, planes are dense point sheets, light is
baked into point colours from a few static light sources. The camera flies along ``center(s)``,
a path where ``s`` is roughly distance travelled along +z.

Sections along s:
    A  -12..27   nebula corridor, particle floor, portal light at the end
    B   27..68   open dust plain with standing light-planes and a floating light sheet
    C   68..130  spiral wormhole
    D  130..     open space, a spiral galaxy ahead
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

CACHE = Path(__file__).with_name(".world_cache.npz")
VERSION = 8

PORTAL = np.array([0.0, 0.0, 27.0])
WORM_A, WORM_B = 68.0, 130.0
GALAXY = np.array([-14.0, -30.0, 250.0])
GALAXY_N = np.array([0.18, 0.86, -0.48])


# ---------------------------------------------------------------- path


def _ss(a, b, s):
    u = np.clip((s - a) / (b - a), 0.0, 1.0)
    return u * u * (3 - 2 * u)


def _bump(a, b, s):
    u = np.clip((s - a) / (b - a), 0.0, 1.0)
    return np.sin(np.pi * u) ** 2


def center(s):
    """Path centre at distance ``s``; works on scalars and arrays."""
    s = np.asarray(s, float)
    x = 7 * _ss(28, 58, s) - 7 * _ss(100, 138, s) + 4.5 * np.sin(2 * np.pi * (s - WORM_A) / 62) * _bump(WORM_A, WORM_B, s)
    y = -1.4 * _ss(27, 40, s) + 1.4 * _ss(56, 70, s) + 2.2 * np.sin(np.pi * (s - WORM_A) / 31) * _bump(WORM_A, WORM_B, s)
    y = y + 5 * _ss(128, 165, s)
    return np.stack([x, y, s], axis=-1)


def worm_radius(s):
    """Tube radius: flared funnels at the mouth and the exit, 3.2 inside."""
    return 3.2 + 9.0 * (1 - _ss(WORM_A - 6, WORM_A + 3, s)) + 9.0 * _ss(WORM_B - 3, WORM_B + 5, s)


# ---------------------------------------------------------------- noise


def _hash(ix, iy, iz, seed):
    h = (ix * 374761393 + iy * 668265263 + iz * 1274126177 + seed * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float32) / float(0xFFFFFF)


def vnoise(p, seed=0):
    """3D value noise in [0, 1] for an (N, 3) array."""
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


def fbm(p, octaves=5, seed=0):
    total = np.zeros(len(p), np.float32)
    amp, norm, freq = 1.0, 0.0, 1.0
    for o in range(octaves):
        total += amp * vnoise(p * freq, seed + 17 * o)
        norm += amp
        amp *= 0.5
        freq *= 2.03
    return total / norm


def _density_sample(rng, cand, scale, thresh, gamma, seed, keep):
    d = fbm(cand * scale, 5, seed)
    prob = np.clip((d - thresh) / (1 - thresh), 0, 1) ** gamma
    sel = rng.random(len(cand)) < prob
    pts, dens = cand[sel], prob[sel]
    if len(pts) > keep:
        idx = rng.choice(len(pts), keep, replace=False)
        pts, dens = pts[idx], dens[idx]
    return pts, dens


def _light(p, pos, radius, power=2.0):
    d = np.linalg.norm(p - pos, axis=1) / radius
    return 1.0 / (1.0 + d**power)


# ---------------------------------------------------------------- layers


def build(rgb):
    """Generate every layer. ``rgb(token)`` resolves palette tokens to floats."""
    rng = np.random.default_rng(11)
    C = {k: np.array(rgb(k), np.float32) for k in (
        "smoke", "smoke_lit", "dust", "star", "core", "arm", "lane", "rim", "portal", "plane",
    )}
    layers = {}

    # A: nebula corridor walls -------------------------------------------------
    n = 1_400_000
    s = rng.uniform(-14, 30, n)
    ang = rng.uniform(-np.pi * 0.62, np.pi * 1.62, n)  # arch: open at the floor
    r = 2.6 + rng.gamma(1.6, 1.9, n)
    c = center(s)
    cand = np.stack([c[:, 0] + r * np.cos(ang), c[:, 1] + r * np.sin(ang), s], 1)
    cand = cand[cand[:, 1] > c[:, 1] - 1.9]
    wall, dens = _density_sample(rng, cand, 0.42, 0.40, 1.2, 3, 260_000)
    lit = _light(wall, PORTAL + [0, 0.6, 1.5], 5.5, 2.2)
    depth = np.clip(np.linalg.norm(wall[:, :2] - center(wall[:, 2])[:, :2], axis=1) - 2.6, 0, 8) / 8
    col = C["smoke"][None] * (0.55 + 0.6 * dens[:, None]) * (1 - 0.6 * depth[:, None])
    col = col + C["smoke_lit"][None] * (lit[:, None] * 2.6)
    layers["walls"] = dict(p=wall, c=col * 0.55, smoke=0.55, fog=55.0)

    # A: particle floor ----------------------------------------------------------
    gx, gz = np.meshgrid(np.arange(-4.4, 4.4, 0.06), np.arange(-14, 29, 0.075))
    fp = np.stack([gx.ravel(), np.zeros(gx.size), gz.ravel()], 1)
    fp[:, :2] += rng.normal(0, 0.012, (len(fp), 2))
    fp[:, 0] *= 1 + 0.25 * (fbm(fp * [0.2, 0, 0.2], 2, 9) - 0.5)
    fp[:, 1] = center(fp[:, 2])[:, 1] - 1.9 + 0.05 * (fbm(fp * 1.5, 3, 4) - 0.5)
    fp[:, 0] += center(fp[:, 2])[:, 0]
    keep = rng.random(len(fp)) < np.clip(1.15 - np.abs(fp[:, 0]) / 4.6, 0, 1)
    fp = fp[keep]
    lit = _light(fp, PORTAL + [0, -1.0, 0.5], 6.0, 2.0)
    col = C["dust"][None] * (0.05 + 1.7 * lit[:, None])
    layers["floor"] = dict(p=fp, c=col * 0.5, fog=60.0)
    # sparse bright floor grains that streak like the floor lines in the references
    gi = rng.choice(len(fp), 7000, replace=False)
    layers["floor_streak"] = dict(p=fp[gi] + [0, 0.01, 0], c=C["dust"][None] * (0.35 + 1.2 * lit[gi, None]), fog=60.0, streak=1.0)

    # A: portal gate (ring of light) and its halo dust ---------------------------
    th = rng.uniform(0, 2 * np.pi, 26000)
    rr = 2.5 + rng.normal(0, 0.05, len(th)) + 0.4 * rng.random(len(th)) ** 6
    ring = np.stack([rr * np.cos(th), rr * np.sin(th) * 1.15 + 0.3, rng.normal(0, 0.04, len(th))], 1) + PORTAL
    layers["portal_ring"] = dict(p=ring, c=np.repeat(C["portal"][None] * 0.9, len(ring), 0), smoke=0.35, fog=80.0)

    # B: dust plain ---------------------------------------------------------------
    n = 900_000
    cand = np.stack([rng.uniform(-30, 42, n), np.zeros(n), rng.uniform(22, 84, n)], 1)
    base = center(cand[:, 2])
    dune = fbm(cand * [0.09, 0, 0.09], 4, 21)
    cand[:, 1] = base[:, 1] - 4.6 + 2.2 * (dune - 0.5) + 0.25 * np.sin(cand[:, 0] * 0.9 + cand[:, 2] * 0.35)
    plain, dens = _density_sample(rng, cand * [1, 1, 1], 0.25, 0.32, 0.9, 5, 240_000)
    sky = np.clip(0.4 + 1.8 * (center(plain[:, 2])[:, 1] - plain[:, 1] - 3.9), 0, 2.2)
    glow = _light(plain, center(np.array([WORM_A]))[0] + [0, 2, 4], 14.0, 2.0)
    col = C["dust"][None] * (0.12 + 0.22 * sky[:, None] * dens[:, None] + 1.4 * glow[:, None])
    layers["plain"] = dict(p=plain, c=col * 0.65, smoke=0.25, fog=70.0)

    # B: low smoke drifting over the plain
    n = 600_000
    cand = np.stack([rng.uniform(-30, 42, n), rng.uniform(-6.5, -1.0, n), rng.uniform(22, 84, n)], 1)
    cand[:, 1] += center(cand[:, 2])[:, 1]
    haze, dens = _density_sample(rng, cand, 0.18, 0.45, 1.4, 7, 110_000)
    col = C["smoke"][None] * (0.5 + dens[:, None]) + C["smoke_lit"][None] * _light(haze, center(np.array([WORM_A]))[0], 12, 2)[:, None]
    layers["haze"] = dict(p=haze, c=col * 0.35, smoke=1.0, fog=70.0, sharp=0.35)

    # B: standing light-planes and a floating light sheet ---------------------------
    sheets_p, sheets_c, edges_p, edges_c = [], [], [], []
    specs = [  # (x offset, s, width, height, yaw)
        (-7.5, 34, 3.0, 13, 0.35), (8.0, 39, 2.2, 17, -0.5), (-12, 47, 4.5, 9, 0.9),
        (5.0, 52, 1.4, 22, 0.15), (15, 57, 5.0, 12, -0.8), (-4.5, 61, 2.0, 15, -0.2),
        (11, 66, 2.6, 19, 0.6), (-16, 63, 3.2, 24, 0.4),
    ]
    for i, (dx, s0, w, h, yaw) in enumerate(specs):
        base = center(np.array([s0]))[0] + [dx, -4.6, 0]
        u = rng.uniform(-0.5, 0.5, 9000)
        v = rng.random(9000) ** 1.4
        ax = np.array([np.cos(yaw), 0, np.sin(yaw)])
        pts = base + u[:, None] * w * ax + v[:, None] * [0, h, 0]
        fade = (1 - v) ** 1.5 * (1 - (2 * np.abs(u)) ** 4)
        sheets_p.append(pts)
        sheets_c.append(C["plane"][None] * (0.25 + 0.75 * fade[:, None]))
        k = 2400
        t = rng.random(k)
        side = rng.integers(0, 3, k)
        e = np.where(side[:, None] == 0, base - 0.5 * w * ax + t[:, None] * [0, h, 0],
                     np.where(side[:, None] == 1, base + 0.5 * w * ax + t[:, None] * [0, h, 0],
                              base + (t[:, None] - 0.5) * w * ax))
        edges_p.append(e + rng.normal(0, 0.01, (k, 3)))
        edges_c.append(C["rim"][None] * (1.0 - 0.8 * t[:, None] * (side[:, None] < 2)))
    sheet = np.concatenate(sheets_p)
    layers["sheets"] = dict(p=sheet, c=np.concatenate(sheets_c) * 0.5, smoke=0.7, fog=80.0, sharp=0.18)
    layers["sheet_edges"] = dict(p=np.concatenate(edges_p), c=np.concatenate(edges_c) * 0.55, fog=80.0)

    # floating horizontal light sheet overhead
    n = 70000
    sp = np.stack([rng.uniform(-14, 20, n), np.zeros(n), rng.uniform(30, 70, n)], 1)
    sp[:, 1] = center(sp[:, 2])[:, 1] + 7.5 + 0.6 * np.sin(sp[:, 0] * 0.3 + sp[:, 2] * 0.2)
    m = fbm(sp * [0.12, 0, 0.12], 3, 31)
    sp = sp[rng.random(n) < m**2 * 1.6]
    layers["sky_sheet"] = dict(p=sp, c=np.repeat(C["plane"][None] * 0.22, len(sp), 0), smoke=0.8, fog=60.0, sharp=0.4)

    # C: wormhole filaments (stored as s, theta, radius; positioned per frame) -------
    nf, per = 84, 1900
    s = rng.uniform(WORM_A - 6, WORM_B + 4, nf * per)
    fil = np.repeat(np.arange(nf), per)
    th = 2 * np.pi * fil / nf + 0.16 * (s - WORM_A) + rng.normal(0, 0.012, len(s))
    rad = worm_radius(s) * (1 + rng.normal(0, 0.035, len(s)))
    br = 0.45 + 0.55 * np.sin(fil * 2.3) ** 2
    mouth = _ss(WORM_A - 6, WORM_A + 2, s) * (1 - _ss(WORM_B - 2, WORM_B + 4, s))
    exitlight = np.exp(-((WORM_B - s) / 18) ** 2)
    col = C["rim"][None] * (br * mouth)[:, None] * 0.8 + C["portal"][None] * exitlight[:, None] * 0.6
    layers["worm"] = dict(s=s, cxy=center(s)[:, :2], th=th, r=rad, c=col * 0.55, fog=45.0, spin=0.55)
    # wormhole wall haze
    n = 120_000
    s = rng.uniform(WORM_A - 6, WORM_B + 4, n)
    th = rng.uniform(0, 2 * np.pi, n)
    rad = worm_radius(s) * (1.0 + 0.6 * rng.gamma(1.5, 0.35, n))
    tc = np.stack([np.cos(th) * 3, np.sin(th) * 3, s * 0.35], 1)
    dens = fbm(tc, 4, 41)
    col = C["smoke"][None] * (dens[:, None] * 1.4) * (_ss(WORM_A - 6, WORM_A, s) * (1 - _ss(WORM_B - 1, WORM_B + 4, s)))[:, None]
    layers["worm_haze"] = dict(s=s, cxy=center(s)[:, :2], th=th, r=rad, c=col * 0.6, smoke=1.0, fog=45.0, spin=0.3, sharp=0.5)

    # D: spiral galaxy (stored in its own polar frame) --------------------------------
    n = 260_000
    arms = 3
    rad = rng.gamma(1.4, 13.0, n)
    rad = rad[rad < 75]
    n = len(rad)
    arm = rng.integers(0, arms, n)
    phi = arm * 2 * np.pi / arms + np.log1p(rad / 6.0) * 2.4 + rng.normal(0, 0.28 + 0.6 / (1 + rad / 4), n)
    hgt = rng.normal(0, 0.6 + 2.5 * np.exp(-rad / 6), n)
    core = np.exp(-rad / 7.0)
    inarm = np.exp(-(rng.normal(0, 1, n) ** 2) * 0.5)
    col = (C["core"][None] * core[:, None] * 1.6 + C["arm"][None] * (1 - core)[:, None] * (0.45 + 0.4 * inarm[:, None]))
    lane = rng.random(n) < 0.18 * (1 - core)
    col[lane] = C["lane"] * 0.35
    layers["galaxy"] = dict(gr=rad, gphi=phi, gh=hgt, c=col * 0.7, smoke=0.6, sharp=1.0)

    # background stars -----------------------------------------------------------
    n = 9000
    d = rng.normal(size=(n, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    mag = rng.pareto(2.2, n) + 0.3
    sp = d * 900 + [0, 0, 90]
    tint = np.where(rng.random(n)[:, None] < 0.2, C["arm"][None], C["star"][None])
    layers["stars"] = dict(p=sp, c=tint * np.clip(mag, 0, 6)[:, None] * 0.55, far=True)

    # near dust motes along the whole path (speed streaks and square sprites) --------
    n = 30000
    s = rng.uniform(-12, 170, n)
    ang = rng.uniform(0, 2 * np.pi, n)
    r = 0.7 + 13 * rng.random(n) ** 1.3
    c = center(s)
    mp = np.stack([c[:, 0] + r * np.cos(ang), c[:, 1] + r * np.sin(ang) * 0.8, s], 1)
    size = 0.012 + 0.03 * rng.random(n) ** 6
    br = 0.35 + 1.4 * rng.random(n) ** 3
    layers["motes"] = dict(p=mp, c=C["dust"][None] * br[:, None], size=size, fog=50.0, streak=1.0)

    return layers


def load(rgb):
    """Layers as dict-of-dicts of float32 arrays, cached next to this file."""
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
