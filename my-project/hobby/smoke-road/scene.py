"""Smoke road: a slow, lucid 20 s flight down a night road built from particles, smoke and light.

The world (see world.py) is about a million points. Each frame projects them through a floating
camera and splats them with numpy into two groups. The *near* group (road, trees, lamps, mist)
also writes an occlusion density at quarter resolution. The *back* group (the far lit valley,
its lamps and the stars) is dimmed by that density, so trees, poles and wires stand as dark
silhouettes against the lit distance. Smoke layers are blurred into volume, then bloom, god rays,
a filmic tonemap, and Frame's vignette and grain.

    python scene.py --frame 4 10 16 --quality medium
    python render.py                     # full 20 s, 1280x720, 30 fps, 2 workers
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d

import world
from faceless_champ import Theme, run
from faceless_champ.draw import Frame, Palette, draw_scene, image_from_array, noise
from world import FAR_LIGHT, LAMPS, center, lamp_geometry, lateral

THEME = Theme.named("midnight")
PALETTE = Palette.from_theme(
    THEME,
    bg="#020304",
    asphalt="#5d6266",
    marking="#ece8dc",
    grass="#56664f",
    bark="#4b4741",
    leaf="#435d48",
    metal="#8d949b",
    mist="#a3b0ad",
    lamp="#ffcf96",
    far="#dfe8f2",
    moon="#5f7290",
    star="#eef3ff",
    window="#ffd9a0",
)
DESIGN = (1920, 1080)
DURATION = 20.0
LAYERS = world.load(PALETTE.rgb)
BG = np.array(PALETTE.rgb("bg"), np.float32)

GAIN = {  # per-layer brightness, tuned on stills without rebuilding the world
    "road": 1.0, "markings": 1.0, "verge": 1.0, "trees": 1.0, "lamps": 0.45, "power": 1.0, "wires": 1.0,
    "rail": 1.0, "mist": 0.45, "cones": 1.0, "far_haze": 1.0, "far_lights": 1.0, "stars": 1.0, "motes": 1.0,
}
for _name, _L in LAYERS.items():
    _L["c"] = (_L["c"] * GAIN.get(_name, 1.0)).astype(np.float32)
REVEAL_END = max(float(L["ton"].max()) for L in LAYERS.values() if "ton" in L) + 1.6

# ---------------------------------------------------------------- camera

_TT = np.linspace(-1, DURATION + 1, 2201)
_V = np.interp(_TT, [0, 3.0, 8.0, 14.0, 20.0], [0.7, 2.5, 3.3, 3.0, 2.1])
_V = gaussian_filter1d(_V, 0.6 / (_TT[1] - _TT[0]), mode="nearest")
_S = np.concatenate([[0], np.cumsum((_V[1:] + _V[:-1]) / 2 * np.diff(_TT))])
_S -= np.interp(0.0, _TT, _S)


def dist(t):
    return float(np.interp(t, _TT, _S))


def speed(t):
    return float(np.interp(t, _TT, _V))


def _ss(a, b, x):
    u = min(max((x - a) / (b - a), 0.0), 1.0)
    return u * u * (3 - 2 * u)


def _bump(a, b, x):
    u = min(max((x - a) / (b - a), 0.0), 1.0)
    return float(np.sin(np.pi * u) ** 2)


_GLANCE = lamp_geometry(47.0, -1)[1] - [0, 3.5, 0]  # the second lit lamp, looked at in passing


def camera(t):
    """(position, right, up, forward, focal-in-widths) at time t: a slow, floating, dreamlike glide."""
    s, v = dist(t), speed(t)
    sway = 0.9 * np.sin(0.31 * t + 0.4) * _ss(2, 8, t)
    height = 0.35 + 1.5 * _ss(0.3, 6.5, t) + 0.25 * np.sin(0.5 * t) + 3.6 * _ss(12.5, 19.8, t)
    pos = center(s) + lateral(s) * sway + [0, height, 0]
    pos = pos + 0.1 * np.array([noise.value(t, 0.12, seed=3), noise.value(t, 0.12, seed=4), 0])

    ahead = 16 + 14 * _ss(11, 19, t)
    target = center(s + ahead) + [0, 1.4 - 0.25 * _ss(12, 19, t), 0]
    w = 0.32 * _bump(7.5, 13.5, t)
    target = target * (1 - w) + _GLANCE * w
    fwd = target - pos
    fwd /= np.linalg.norm(fwd)

    ds = 2.0
    ax = (world.X(s + ds) - 2 * world.X(s) + world.X(s - ds)) / ds**2
    roll = float(np.clip(-1.4 * ax * v * v, -0.08, 0.08)) + 0.035 * np.sin(0.27 * t) + 0.015 * noise.value(t, 0.2, seed=7)

    up0 = np.array([0.0, 1.0, 0.0])
    right = np.cross(up0, fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    cr, sr = np.cos(roll), np.sin(roll)
    right, up = right * cr + up * sr, up * cr - right * sr
    focal = 0.86 + 0.1 * _ss(11, 20, t)
    return pos, right, up, fwd, focal


# ---------------------------------------------------------------- layers per frame


def reveal(L, t):
    """(alpha, displacement) for a layer that condenses out of the dark, or (None, None)."""
    if "ton" not in L or t > REVEAL_END:
        return None, None
    a = np.clip((t - L["ton"]) / 1.5, 0, 1)
    a = a * a * (3 - 2 * a)
    return a, L["jit"] * ((1 - a) ** 2)[:, None]


def positions(L, t):
    p = L["p"]
    _, disp = reveal(L, t)
    if disp is not None:
        p = p + disp
    if "phase" in L:  # motes drift
        ph = L["phase"]
        p = p + 0.25 * np.sin(0.4 * t + ph) + [0, 0.05 * t, 0]
    return p


_ZRANGE = {}
for _name, _L in LAYERS.items():
    _ZRANGE[_name] = (float(_L["p"][:, 2].min()) - 40, float(_L["p"][:, 2].max()) + 5)


class Buffers:
    """Splat targets: sharp (full res) and smoke (quarter res) per group, plus occlusion density."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.lw, self.lh = max(2, w // 4), max(2, h // 4)
        self.lists = {key: ([], []) for key in ("near_sharp", "near_smoke", "back_sharp", "back_smoke", "occ")}

    def dot(self, key, x, y, col):
        xi, yi = x.astype(np.int64), y.astype(np.int64)
        ok = (x >= 0) & (y >= 0) & (xi < self.w) & (yi < self.h)
        self.lists[key][0].append(yi[ok] * self.w + xi[ok])
        self.lists[key][1].append(col[ok])

    def low(self, key, x, y, col):
        lx = (x * self.lw / self.w).astype(np.int64)
        ly = (y * self.lh / self.h).astype(np.int64)
        ok = (x >= 0) & (y >= 0) & (lx < self.lw) & (ly < self.lh)
        self.lists[key][0].append(ly[ok] * self.lw + lx[ok])
        self.lists[key][1].append(col[ok])

    def squares(self, key, x, y, side, col):
        for k in range(2, 9):
            m = side == k
            if not m.any():
                continue
            x0 = np.round(x[m] - k / 2).astype(np.int64)
            y0 = np.round(y[m] - k / 2).astype(np.int64)
            ok = (x0 >= 0) & (y0 >= 0) & (x0 + k <= self.w) & (y0 + k <= self.h)
            off = (np.arange(k)[:, None] * self.w + np.arange(k)[None, :]).ravel()
            self.lists[key][0].append(((y0[ok] * self.w + x0[ok])[:, None] + off[None, :]).ravel())
            self.lists[key][1].append(np.repeat(col[m][ok], k * k, axis=0))

    def image(self, key):
        full = key.endswith("sharp")
        n = self.w * self.h if full else self.lw * self.lh
        idx, wts = self.lists[key]
        chans = 1 if key == "occ" else 3
        out = np.zeros((n, chans), np.float32)
        if idx:
            idx = np.concatenate(idx)
            wts = np.concatenate(wts).reshape(len(idx), -1)
            for c in range(chans):
                out[:, c] = np.bincount(idx, wts[:, c], minlength=n)
        return out.reshape((self.h, self.w, chans) if full else (self.lh, self.lw, chans))


def project(p, cam, w, h):
    pos, right, up, fwd, focal = cam
    d = p - pos
    z = d @ fwd
    f = focal * w
    with np.errstate(divide="ignore", invalid="ignore"):
        x = w / 2 + f * (d @ right) / z
        y = h / 2 - f * (d @ up) / z
    return x, y, z, f


def splat_layers(buf, t, cam, kres):
    w, h = buf.w, buf.h
    cz = cam[0][2]
    for name, L in LAYERS.items():
        z0, z1 = _ZRANGE[name]
        if not L.get("far") and (cz < z0 or cz > z1):
            continue
        alpha, _ = reveal(L, t)
        p = positions(L, t)
        x, y, z, f = project(p, cam, w, h)
        vis = (z > 0.12) & (x > -2) & (x < w + 2) & (y > -2) & (y < h + 2)
        if alpha is not None:
            vis &= alpha > 0.002
        if not vis.any():
            continue
        idx = np.nonzero(vis)[0]
        x, y, z = x[idx], y[idx], z[idx]
        fade = np.clip((z - 0.12) / 1.2, 0, 1) ** 2
        if "fog" in L:
            fade = fade * np.exp(-z / float(L["fog"]))
        if alpha is not None:
            fade = fade * alpha[idx]
        col = L["c"][idx] * (fade * kres)[:, None]

        group = "back" if L.get("back") else "near"
        smoke = float(L.get("smoke", 0.0))
        if smoke:
            buf.low(group + "_smoke", x, y, col * smoke)
        sharp = float(L.get("sharp", 1.0 if not smoke else 0.5))
        occ = float(L.get("occ", 0.0))
        if occ:
            a = (fade if alpha is None else alpha[idx]) * occ * kres
            buf.low("occ", x, y, a[:, None])
        if "size" in L:
            side = np.clip(np.round(L["size"][idx] * f / z), 0, 8).astype(np.int64)
            big = side >= 2
            buf.squares(group + "_sharp", x[big], y[big], side[big], col[big] * 0.8)
            x, y, col = x[~big], y[~big], col[~big]
        if sharp > 0:
            buf.dot(group + "_sharp", x, y, col * sharp)


# ---------------------------------------------------------------- image ops

_UP = {}
_GRID = {}


def upsample(img, h, w):
    lh, lw = img.shape[:2]
    key = (lh, lw, h, w)
    if key not in _UP:
        def axis(n_out, n_in):
            c = np.clip((np.arange(n_out) + 0.5) * n_in / n_out - 0.5, 0, n_in - 1)
            i0 = np.floor(c).astype(np.int64)
            return i0, np.minimum(i0 + 1, n_in - 1), (c - i0).astype(np.float32)
        _UP[key] = (axis(h, lh), axis(w, lw))
    (r0, r1, rw), (c0, c1, cw) = _UP[key]
    rows = img[r0] * (1 - rw)[:, None, None] + img[r1] * rw[:, None, None]
    return rows[:, c0] * (1 - cw)[None, :, None] + rows[:, c1] * cw[None, :, None]


def downsample(img, lh, lw):
    h, w = img.shape[:2]
    fy, fx = h // lh, w // lw
    return img[: lh * fy, : lw * fx].reshape(lh, fy, lw, fx, -1).mean(axis=(1, 3))


def grid(lh, lw):
    if (lh, lw) not in _GRID:
        _GRID[(lh, lw)] = np.mgrid[0:lh, 0:lw].astype(np.float32)
    return _GRID[(lh, lw)]


def god_rays(img, cx, cy, strength, steps=14, reach=0.6):
    lh, lw = img.shape[:2]
    yy, xx = grid(lh, lw)
    out = np.zeros_like(img)
    norm = 0.0
    for k in range(steps):
        sc = 1 - reach * k / steps
        sx = np.clip(np.round(cx + (xx - cx) * sc), 0, lw - 1).astype(np.int64)
        sy = np.clip(np.round(cy + (yy - cy) * sc), 0, lh - 1).astype(np.int64)
        wk = 0.94**k
        out += img[sy, sx] * wk
        norm += wk
    return out * (strength / norm)


def blob(lh, lw, cx, cy, radius, col):
    yy, xx = grid(lh, lw)
    g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * radius**2))
    return g[..., None] * col[None, None, :]


LAMP_COL = np.array(PALETTE.rgb("lamp"), np.float32)
FAR_COL = np.array(PALETTE.rgb("far"), np.float32)


def light_sources(t, cam, w, h):
    """Screen-space glows: (x, y, z, colour, power, occludable)."""
    out = []
    for s, side, lit in LAMPS:
        if not lit:
            continue
        _, head = lamp_geometry(s, side)
        on = 1.0 if s > 100 else _ss(0.3 + (s + 4) / world.REVEAL_SPEED, 1.8 + (s + 4) / world.REVEAL_SPEED, t)
        out.append((head - [0, 0.15, 0], LAMP_COL, (0.6 if s > 100 else 1.0) * on, s > 100))
    out.append((FAR_LIGHT, FAR_COL, 1.0, True))
    res = []
    for p, c, k, back in out:
        x, y, z, _ = project(np.asarray(p, float)[None], cam, w, h)
        if z[0] > 0.5 and -0.3 * w < x[0] < 1.3 * w and -0.3 * h < y[0] < 1.3 * h:
            res.append((float(x[0]), float(y[0]), float(z[0]), c, k, back))
    return res


# ---------------------------------------------------------------- frame


def render_frame(t, w, h):
    cam = camera(t)
    kres = (1280.0 / w) ** 2
    buf = Buffers(w, h)
    splat_layers(buf, t, cam, kres)
    lh, lw = buf.lh, buf.lw
    q = lw / 320.0

    occ = gaussian_filter(buf.image("occ"), (0.8 * q, 0.8 * q, 0))
    trans_low = np.exp(-occ * 1.6)
    trans = upsample(trans_low, h, w)
    sharp = buf.image("near_sharp") + buf.image("back_sharp") * trans

    near_smoke, back_smoke = buf.image("near_smoke"), buf.image("back_smoke")
    soft = gaussian_filter(near_smoke, (1.3 * q, 1.3 * q, 0)) + 0.6 * gaussian_filter(near_smoke, (5 * q, 5 * q, 0))
    back_soft = (gaussian_filter(back_smoke, (1.5 * q, 1.5 * q, 0)) + 0.6 * gaussian_filter(back_smoke, (6 * q, 6 * q, 0))) * trans_low
    soft += back_soft

    low = downsample(sharp, lh, lw)
    bloom = gaussian_filter(low, (2.0 * q, 2.0 * q, 0)) * 0.8 + gaussian_filter(low, (10 * q, 10 * q, 0)) * 0.6

    lights = np.zeros_like(low)
    back_lights = np.zeros_like(low)
    far_xy = None
    for x, y, z, col, k, back in light_sources(t, cam, w, h):
        lx, ly = x * lw / w, y * lh / h
        if col is FAR_COL:
            g = blob(lh, lw, lx, ly, 9 * q, col) * 0.5 + blob(lh, lw, lx, ly, 34 * q, col) * 0.18
            far_xy = (lx, ly)
        else:
            r = np.clip(4.0 / z, 0.35, 6) * q
            g = blob(lh, lw, lx, ly, r, col) * (k * 1.4) + blob(lh, lw, lx, ly, r * 5, col) * (k * 0.08)
        if back:
            iy, ix = int(np.clip(ly, 0, lh - 1)), int(np.clip(lx, 0, lw - 1))
            g = g * float(trans_low[iy, ix, 0])
            back_lights += g
        lights += g
    rays = 0
    if far_xy is not None:
        # rays only from the lit distance, so near lamps never smear into fans
        rays = gaussian_filter(god_rays(back_soft * 0.6 + back_lights, far_xy[0], far_xy[1], 0.45), (1.5 * q, 1.5 * q, 0))

    img = sharp + upsample(soft * 1.0 + bloom * 0.7 + lights + rays, h, w)

    expo = float(1.1 * _ss(0.0, 2.2, t) * (1 - _ss(DURATION - 1.4, DURATION, t)))
    img = 1 - np.exp(-img * expo)
    img = BG + (1 - BG) * np.clip(img, 0, 1)
    img *= 255.0
    img += np.random.default_rng(int(t * 1000)).random((h, w, 1), np.float32)
    rgba = np.empty((h, w, 4), np.uint8)
    rgba[..., :3] = np.clip(img, 0, 255)
    rgba[..., 3] = 255
    return rgba


def draw(t, size):
    w, h = int(size[0]), int(size[1])
    rgba = render_frame(t, w, h)
    fr = Frame(size, palette=PALETTE, design=DESIGN)
    fr.c.save()
    fr.c.resetMatrix()
    fr.c.drawImage(image_from_array(rgba), 0, 0)
    fr.c.restore()
    fr.chroma(0.5)
    fr.vignette(0.6)
    fr.grain(t, 0.06)
    return fr.finish()


def build():
    key = max(Path(__file__).stat().st_mtime, Path(world.__file__).stat().st_mtime)
    with THEME.use():
        return draw_scene(draw, DURATION, theme=THEME, design=DESIGN, key=str(key))


if __name__ == "__main__":
    run(build)
