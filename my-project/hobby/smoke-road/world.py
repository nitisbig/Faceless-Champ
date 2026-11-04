"""Procedural night road built only from particles, smoke and baked light.

Units are metres. The road follows ``center(s)``, where ``s`` is distance along +z. Lighting is
baked into point colours: a dim moonlit ambient, only two lit street lamps near the start (the
others along the way are dark), and a strongly lit valley far down the road with its own row of
lamps, so the near world sits mostly in shadow and the distance glows.

Every near point also carries a reveal time ``ton`` (the world condenses out of the dark from
near to far) and a random offset ``jit`` that it drifts in from.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

CACHE = Path(__file__).with_name(".world_cache.npz")
VERSION = 4

ROAD_HALF = 3.6
FAR_LIGHT_S = 172.0
REVEAL_SPEED = 16.0  # metres of world condensed per second


def X(s):
    return 6.0 * np.sin(np.asarray(s, float) / 40.0)


def Y(s):
    s = np.asarray(s, float)
    return 0.8 * np.sin(s / 28.0) - 0.012 * np.clip(s, 0, None)


def center(s):
    s = np.asarray(s, float)
    return np.stack([X(s), Y(s), s], axis=-1)


def lateral(s):
    """Unit vector across the road at s (x-ish, follows the curve)."""
    s = np.asarray(s, float)
    dx = (X(s + 0.5) - X(s - 0.5)) / 1.0
    n = np.stack([np.ones_like(dx), np.zeros_like(dx), -dx], axis=-1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def road_point(s, u, v):
    """World point at distance s, lateral offset u, height v above the road surface."""
    s, u, v = np.broadcast_arrays(*(np.asarray(a, float) for a in (s, u, v)))
    return center(s) + lateral(s) * u[..., None] + np.stack([0 * u, v, 0 * u], axis=-1)


# lamps: (s, side, lit). Only two near lamps are on; far lamps are all on.
NEAR_LAMPS = [(11.0, -1, True), (29.0, 1, False), (47.0, -1, True), (68.0, 1, False), (90.0, -1, False)]
FAR_LAMPS = [(108.0 + 13.0 * i, (-1) ** i, True) for i in range(11)]
LAMPS = NEAR_LAMPS + FAR_LAMPS


def lamp_geometry(s, side):
    base = road_point(s, side * (ROAD_HALF + 1.2), 0.0)
    head = road_point(s, side * (ROAD_HALF - 0.6), 7.2)
    return base, head


def lamp_lights():
    """(position, intensity, radius) of every lit lamp."""
    out = []
    for s, side, lit in LAMPS:
        if lit:
            _, head = lamp_geometry(s, side)
            far = s > 100
            out.append((head - [0, 0.25, 0], 0.75 if far else 1.0, 3.8 if far else 4.2))
    return out


FAR_LIGHT = center(FAR_LIGHT_S) + [0, 9.0, 0]


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


# ---------------------------------------------------------------- lighting


def lighting(p, C, lamp_gain=1.0):
    """Baked irradiance (N, 3): moon ambient + lamp pools (downward cones) + far valley light."""
    out = np.repeat(C["moon"][None] * 0.07, len(p), 0)
    lamp = np.zeros(len(p), np.float32)
    for pos, k, r in lamp_lights():
        d = p - pos
        dist = np.linalg.norm(d, axis=1) + 1e-6
        down = np.clip(-d[:, 1] / dist, -1, 1)
        cone = np.clip((down - 0.15) / 0.55, 0, 1) ** 1.5 + 0.12 * np.exp(-dist / 1.2)
        lamp += k * cone / (1 + (dist / r) ** 2.2)
    far = 1.0 / (1 + (np.linalg.norm(p - FAR_LIGHT, axis=1) / 34.0) ** 2.0)
    return out + C["lamp"][None] * (lamp * lamp_gain)[:, None] + C["far"][None] * (far * 1.6)[:, None]


# ---------------------------------------------------------------- build


def _reveal(rng, p):
    """Reveal time (near first) and a drift-in offset for each point."""
    ton = 0.3 + np.clip(p[:, 2] + 4.0, 0, None) / REVEAL_SPEED + 0.9 * rng.random(len(p))
    jit = rng.normal(0, 1, (len(p), 3)).astype(np.float32)
    jit /= np.linalg.norm(jit, axis=1, keepdims=True)
    jit = jit * (0.6 + 0.8 * rng.random((len(p), 1))) + [0, 0.7, 0]
    return ton.astype(np.float32), jit


def _density(rng, cand, scale, thresh, gamma, seed):
    d = fbm(cand * scale, 4, seed)
    prob = np.clip((d - thresh) / (1 - thresh), 0, 1) ** gamma
    sel = rng.random(len(cand)) < prob
    return cand[sel], prob[sel]


def _tree(rng, base, h, crown, n_trunk, n_crown, seed):
    """Trunk cylinder, a few branches and a clumpy crown."""
    lean = rng.normal(0, 0.12, 2)
    v = rng.random(n_trunk) ** 0.8 * h
    a = rng.uniform(0, 2 * np.pi, n_trunk)
    r = (0.32 - 0.16 * v / h) * (1 + 0.15 * rng.random(n_trunk))
    trunk = np.stack([np.cos(a) * r + lean[0] * v, v, np.sin(a) * r + lean[1] * v], 1)
    pts = [trunk]
    for _ in range(rng.integers(3, 6)):
        start = rng.uniform(0.55, 0.9) * h
        d = rng.normal(0, 1, 3)
        d[1] = abs(d[1]) + 0.8
        d /= np.linalg.norm(d)
        t = rng.random(140)[:, None] * rng.uniform(1.5, 2.8)
        b = np.array([lean[0] * start, start, lean[1] * start]) + t * d + rng.normal(0, 0.04, (140, 3))
        pts.append(b)
    top = np.array([lean[0] * h, h + crown[1] * 0.55, lean[1] * h])
    cand = rng.normal(0, 1, (n_crown * 4, 3)) * np.array(crown) * 0.62 + top
    cpts, _ = _density(rng, cand, 0.9, 0.42, 1.0, seed)
    pts.append(cpts[:n_crown])
    kinds = np.concatenate([np.zeros(sum(len(q) for q in pts[:-1])), np.ones(len(pts[-1]))])
    return np.concatenate(pts) + base, kinds


def build(rgb):
    rng = np.random.default_rng(5)
    C = {k: np.array(rgb(k), np.float32) for k in (
        "asphalt", "marking", "grass", "bark", "leaf", "metal", "mist", "lamp", "far", "moon", "star", "window",
    )}
    L = {}

    def add(name, p, albedo, reveal=True, **kw):
        col = albedo * lighting(p, C)
        layer = dict(p=p.astype(np.float32), c=col.astype(np.float32), **kw)
        if reveal:
            layer["ton"], layer["jit"] = _reveal(rng, p)
        L[name] = layer

    # road surface: denser near the camera's stretch
    parts = []
    for s0, s1, per_m2 in ((-6, 85, 260), (85, 240, 70)):
        n = int((s1 - s0) * 2 * ROAD_HALF * per_m2)
        s = rng.uniform(s0, s1, n)
        u = rng.uniform(-ROAD_HALF, ROAD_HALF, n)
        parts.append((s, u))
    s = np.concatenate([q[0] for q in parts])
    u = np.concatenate([q[1] for q in parts])
    crown = 0.06 * (1 - (u / ROAD_HALF) ** 2)
    p = road_point(s, u, crown)
    patch = fbm(p * [0.6, 0, 0.6], 3, 2)
    tracks = np.exp(-(((np.abs(u) - 1.8) / 0.45) ** 2))  # polished wheel tracks catch light
    alb = C["asphalt"][None] * (0.45 + 0.6 * patch[:, None] + 0.5 * tracks[:, None])
    add("road", p, alb, fog=70.0, sharp=1.0)

    # lane markings: dashed centre, solid edges
    s = rng.uniform(-6, 240, 260_000)
    which = rng.integers(0, 3, len(s))
    u = np.where(which == 0, 0.0, np.where(which == 1, -ROAD_HALF + 0.25, ROAD_HALF - 0.25)) + rng.uniform(-0.06, 0.06, len(s))
    keep = (which > 0) | (np.mod(s, 12.0) < 3.0)
    keep &= rng.random(len(s)) < np.where(s < 85, 1.0, 0.35)
    s, u = s[keep], u[keep]
    p = road_point(s, u, 0.075)
    add("markings", p, np.repeat(C["marking"][None] * 1.6, len(p), 0), fog=70.0)

    # grass verges with tufts
    n = 420_000
    s = rng.uniform(-6, 130, n)
    side = np.where(rng.random(n) < 0.5, -1, 1)
    u = side * (ROAD_HALF + 0.3 + rng.gamma(1.4, 2.8, n))
    v = rng.random(n) ** 2.2 * 0.45
    p = road_point(s, u, v + 0.15 * (fbm(np.stack([s * 0.2, u * 0.2, s * 0]).T, 2, 6) - 0.5))
    clump = fbm(p * 0.7, 3, 7)
    keep = rng.random(n) < clump**1.5 * 1.8
    p, v = p[keep], v[keep]
    alb = C["grass"][None] * (0.5 + 1.6 * (v / 0.45))[:, None]
    add("verge", p, alb, fog=60.0, occ=0.02)

    # trees: two rows on each side near, sparse silhouettes far
    tp, tc = [], []
    k = 0
    for s0, s1, umin, umax, step, scale in ((-6, 124, 6.5, 12.0, 6.5, 1.0), (-6, 130, 13.0, 24.0, 7.5, 1.1), (120, 230, 9.0, 34.0, 6.0, 1.2)):
        s_ = s0
        while s_ < s1:
            for side in (-1, 1):
                if rng.random() < 0.18:
                    continue
                ss = s_ + rng.uniform(-2.5, 2.5)
                if any(abs(ss - ls) < 3.0 and side == lsd for ls, lsd, _ in NEAR_LAMPS) and umin < 7:
                    continue
                base = road_point(ss, side * rng.uniform(umin, umax), -0.05)
                h = rng.uniform(3.2, 5.8) * scale
                crown = np.array([rng.uniform(2.6, 3.6), rng.uniform(2.4, 3.4), rng.uniform(2.6, 3.6)]) * scale
                pts, kinds = _tree(rng, base, h, crown, 450, 6500 if s0 < 100 else 3200, 100 + k)
                tp.append(pts)
                tc.append(kinds)
                k += 1
            s_ += step * rng.uniform(0.8, 1.2)
    tp = np.concatenate(tp)
    kinds = np.concatenate(tc)[:, None]
    shade = 0.6 + 0.7 * fbm(tp * 1.3, 2, 9)[:, None]
    alb = (C["bark"][None] * 0.6 * (1 - kinds) + C["leaf"][None] * 2.6 * kinds) * shade
    add("trees", tp, alb, fog=75.0, occ=0.07)

    # street lamps: poles, arms, heads (lit and dark)
    pp = []
    for s, side, lit in LAMPS:
        base, head = lamp_geometry(s, side)
        v = rng.random(1400) * 7.4
        a = rng.uniform(0, 2 * np.pi, 1400)
        pole = base + np.stack([np.cos(a) * 0.09, v, np.sin(a) * 0.09], 1)
        t = rng.random(500)[:, None]
        arm = base + [0, 7.3, 0] + t * (head - base - [0, 7.3, 0]) + rng.normal(0, 0.025, (500, 3))
        hd = head + rng.normal(0, 1, (300, 3)) * [0.28, 0.06, 0.12]
        pp += [pole, arm, hd]
    pp = np.concatenate(pp)
    add("lamps", pp, np.repeat(C["metal"][None] * 0.9, len(pp), 0), fog=90.0, occ=0.06)

    # power line: poles on the left and sagging wires
    pp, wp = [], []
    poles = [road_point(s, -11.5, -0.05) for s in np.arange(-8, 236, 31.0)]
    for i, base in enumerate(poles):
        v = rng.random(1600) * 9.5
        a = rng.uniform(0, 2 * np.pi, 1600)
        pp.append(base + np.stack([np.cos(a) * 0.15, v, np.sin(a) * 0.15], 1))
        t = rng.uniform(-1.3, 1.3, 400)[:, None]
        pp.append(base + [0, 9.0, 0] + t * [1, 0, 0] + rng.normal(0, 0.04, (400, 3)))
        if i + 1 < len(poles):
            nxt = poles[i + 1]
            for off in (-1.2, 0.0, 1.2):
                f = rng.random(900)[:, None]
                a0 = base + [off, 9.0, 0]
                b0 = nxt + [off, 9.0, 0]
                w = a0 + f * (b0 - a0) - [0, 1, 0] * (1.0 * 4 * f * (1 - f))
                wp.append(w)
    pp = np.concatenate(pp)
    add("power", pp, np.repeat(C["bark"][None] * 0.8, len(pp), 0), fog=90.0, occ=0.06)
    wp = np.concatenate(wp)
    add("wires", wp, np.repeat(C["metal"][None] * 1.4, len(wp), 0), fog=110.0, occ=0.03)

    # guardrail on the right through the middle stretch
    gp = []
    for s in np.arange(16, 78, 2.0):
        gp.append(road_point(np.full(80, s), np.full(80, ROAD_HALF + 0.7), rng.random(80) * 0.75) + rng.normal(0, 0.03, (80, 3)))
    s = rng.uniform(16, 78, 14000)
    gp.append(road_point(s, np.full(len(s), ROAD_HALF + 0.62), np.where(rng.random(len(s)) < 0.5, 0.55, 0.7) + rng.normal(0, 0.02, len(s))))
    gp = np.concatenate(gp)
    add("rail", gp, np.repeat(C["metal"][None] * 1.5, len(gp), 0), fog=80.0, occ=0.03)

    # ground mist, thick near the ground, lit in pools by the two lamps
    n = 1_400_000
    s = rng.uniform(-6, 135, n)
    u = rng.uniform(-16, 16, n)
    v = rng.exponential(0.75, n)
    p = road_point(s, u, v)
    mp, dens = _density(rng, p, [0.16, 0.5, 0.16], 0.45, 1.3, 31)
    alb = C["mist"][None] * (0.4 + dens[:, None])
    add("mist", mp, alb, fog=60.0, smoke=1.0, sharp=0.12)

    # volumetric lamp cones
    cp = []
    for pos, k, r in lamp_lights():
        if pos[2] > 100:
            continue
        n = 16000
        hgt = rng.random(n) ** 0.9 * 7.0
        rad = np.sqrt(rng.random(n)) * hgt * np.tan(np.radians(34))
        a = rng.uniform(0, 2 * np.pi, n)
        cp.append(pos + np.stack([np.cos(a) * rad, -hgt, np.sin(a) * rad], 1))
    cp = np.concatenate(cp)
    add("cones", cp, np.repeat(C["mist"][None] * 0.55, len(cp), 0), fog=70.0, smoke=1.0, sharp=0.05)

    # far valley: bright haze, far lamp heads, scattered windows (always visible, behind occluders)
    n = 1_000_000
    s = rng.uniform(112, 260, n)
    u = rng.uniform(-60, 60, n)
    v = rng.exponential(4.0, n) - 1.0
    p = road_point(s, u, v)
    hp, dens = _density(rng, p, [0.05, 0.15, 0.05], 0.4, 1.2, 51)
    alb = C["mist"][None] * (0.5 + dens[:, None])
    add("far_haze", hp, alb * 0.9, reveal=False, back=True, fog=400.0, smoke=1.0, sharp=0.25)

    lp = []
    for s, side, lit in FAR_LAMPS:
        _, head = lamp_geometry(s, side)
        lp.append(head + rng.normal(0, 0.12, (60, 3)))
    wn = []
    for _ in range(140):
        s = rng.uniform(150, 255)
        base = road_point(s, rng.choice([-1, 1]) * rng.uniform(12, 55), rng.uniform(0.6, 9))
        wn.append(base + rng.random((24, 3)) * [0.9, 0.6, 0.05])
    lp = np.concatenate(lp)
    wn = np.concatenate(wn)
    L["far_lights"] = dict(p=np.concatenate([lp, wn]).astype(np.float32),
                           c=np.concatenate([np.repeat(C["lamp"][None] * 3.0, len(lp), 0),
                                             np.repeat(C["window"][None] * 1.6, len(wn), 0)]).astype(np.float32),
                           back=True, fog=600.0, smoke=0.4)

    # stars over everything, faint
    d = rng.normal(size=(5000, 3))
    d[:, 1] = np.abs(d[:, 1]) + 0.15
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    mag = np.clip(rng.pareto(2.5, 5000) + 0.2, 0, 4)
    L["stars"] = dict(p=(d * 600 + [0, 0, 80]).astype(np.float32), c=(C["star"][None] * mag[:, None] * 0.25).astype(np.float32),
                      back=True, far=True)

    # floating motes (pollen and dust) along the flight, gently drifting
    n = 6000
    s = rng.uniform(-6, 75, n)
    p = road_point(s, rng.uniform(-9, 9, n), 0.2 + rng.random(n) ** 1.5 * 6)
    alb = C["mist"][None] * (0.6 + 2.0 * rng.random(n)[:, None] ** 3)
    add("motes", p, alb * 1.5, fog=40.0, size=(0.008 + 0.016 * rng.random(n) ** 4).astype(np.float32),
        phase=rng.uniform(0, 2 * np.pi, (n, 3)).astype(np.float32))
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
