"""Cosmic drift: a 20 s exploratory flight through a cosmos built from smoke, light, planes and particles.

Every frame projects a few hundred thousand world points through a moving pinhole camera and
splats them into float buffers with numpy: a sharp buffer (bilinear point splats, speed streaks,
square near-motes) and a quarter-resolution smoke buffer that is blurred into volume. Bloom and
god rays are built at quarter resolution, then a filmic tonemap, and Frame adds the vignette and
grain.

    python scene.py --frame 3 9 12 17     # stills (720p is --quality medium)
    python render.py                      # full 20 s, 720x1280, 30 fps, 2 workers
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d

import world
from faceless_champ import Theme, run
from faceless_champ.draw import Frame, Palette, draw_scene, image_from_array, noise
from world import GALAXY, GALAXY_N, PORTAL, WORM_A, WORM_B, center

THEME = Theme.named("midnight")
PALETTE = Palette.from_theme(
    THEME,
    bg="#020304",
    smoke="#3f5f49",
    smoke_lit="#b8d9b2",
    dust="#e6ece4",
    star="#f3f6ff",
    core="#ffe2b8",
    arm="#a9c8dc",
    lane="#4d6f5d",
    rim="#d8ecf2",
    portal="#eafff0",
    plane="#c9e4dc",
)
DESIGN = (1080, 1920)
DURATION = 20.0
SHUTTER = 0.07  # streak length in seconds of camera travel
LAYERS = world.load(PALETTE.rgb)
GAIN = {  # per-layer brightness, tuned on stills without rebuilding the world
    "walls": 0.9, "floor": 0.5, "floor_streak": 0.7, "portal_ring": 0.12, "plain": 0.3, "haze": 0.2,
    "sheets": 0.2, "sheet_edges": 0.6, "sky_sheet": 0.3, "worm": 0.5, "worm_haze": 0.12,
    "galaxy": 0.09, "stars": 1.0, "motes": 0.8,
}
for _name, _L in LAYERS.items():
    _L["c"] = (_L["c"] * GAIN.get(_name, 1.0)).astype(np.float32)
for _name in ("plain", "haze"):  # keep the plain out of the corridor
    _keep = LAYERS[_name]["p"][:, 2] > 31.0
    LAYERS[_name] = {k: (v[_keep] if isinstance(v, np.ndarray) and v.ndim and len(v) == len(_keep) else v)
                     for k, v in LAYERS[_name].items()}
LAYERS["worm"]["streak"] = 0.1  # a tenth of the tube points draw hyperspace lines
for _name in ("sheet_edges", "portal_ring"):
    LAYERS[_name]["fine"] = True  # thin lines: bilinear splats
BG = np.array(PALETTE.rgb("bg"), np.float32)

# ---------------------------------------------------------------- camera

_TT = np.linspace(-1, DURATION + 1, 4401)
_V = np.interp(_TT, [0, 1.0, 4.5, 8.8, 10.2, 13.6, 15.4, 20], [1.2, 5.0, 6.0, 7.2, 17.0, 17.0, 4.2, 1.3])
_V = gaussian_filter1d(_V, 0.5 / (_TT[1] - _TT[0]), mode="nearest")
_S = np.concatenate([[0], np.cumsum((_V[1:] + _V[:-1]) / 2 * np.diff(_TT))])
_S -= np.interp(0.0, _TT, _S)


def dist(t):
    return float(np.interp(t, _TT, _S))


def speed(t):
    return float(np.interp(t, _TT, _V))


def _ss(a, b, x):
    u = min(max((x - a) / (b - a), 0.0), 1.0)
    return u * u * (3 - 2 * u)


def camera(t):
    """(position, right, up, forward, focal-in-widths) at time t."""
    s, v = dist(t), speed(t)
    pos = center(s).copy()
    in_worm = _ss(WORM_A - 4, WORM_A + 6, s) * (1 - _ss(WORM_B - 6, WORM_B + 2, s))
    pos += [0.9 * np.sin(0.8 * t) * in_worm, 0.7 * np.cos(0.6 * t) * in_worm - 0.25 * in_worm, 0]
    pos += 0.12 * np.array([noise.value(t, 0.15, seed=3), noise.value(t, 0.15, seed=4), 0])
    pos[1] += 1.4 * _ss(30, 46, s) * (1 - _ss(54, 66, s))  # glide a little higher over the plain

    look = center(s + 5.0 + 0.45 * v) - pos
    look /= np.linalg.norm(look)
    to_gal = GALAXY + [0, 6, 0] - pos
    to_gal /= np.linalg.norm(to_gal)
    w_gal = _ss(122, 150, s)
    fwd = look * (1 - w_gal) + to_gal * w_gal
    fwd /= np.linalg.norm(fwd)

    ds = 2.0
    ax = (center(s + ds)[0] - 2 * center(s)[0] + center(s - ds)[0]) / ds**2
    roll = np.clip(-0.9 * ax * v, -0.45, 0.45)
    roll += 1.1 * np.sin(np.pi * _ss(WORM_A - 2, WORM_B + 12, s))  # corkscrew through the wormhole
    roll += -0.32 * w_gal + 0.03 * noise.value(t, 0.2, seed=7)

    up0 = np.array([0.0, 1.0, 0.0])
    right = np.cross(up0, fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    cr, sr = np.cos(roll), np.sin(roll)
    right, up = right * cr + up * sr, up * cr - right * sr
    focal = 1.18 - 0.3 * _ss(7, 17, v)  # widen the lens with speed
    return pos, right, up, fwd, focal


# ---------------------------------------------------------------- layer positions


def _galaxy_basis():
    n = GALAXY_N / np.linalg.norm(GALAXY_N)
    e1 = np.cross(n, [0, 0, 1.0])
    e1 /= np.linalg.norm(e1)
    return e1, np.cross(n, e1), n


_GB = np.stack(_galaxy_basis())


def positions(L, t):
    if "p" in L:
        return L["p"]
    if "gr" in L:
        r = L["gr"]
        phi = L["gphi"] + 0.9 * t / (1 + r / 10)  # differential rotation
        local = np.stack([r * np.cos(phi), r * np.sin(phi), L["gh"]], 1)
        return GALAXY + local @ _GB
    th = L["th"] + L["spin"] * t
    c = L["cxy"]
    return np.stack([c[:, 0] + L["r"] * np.cos(th), c[:, 1] + L["r"] * np.sin(th), L["s"]], 1)


_ZRANGE = {}
for _name, _L in LAYERS.items():
    _p = positions(_L, 0.0)
    _ZRANGE[_name] = (float(_p[:, 2].min()) - 80, float(_p[:, 2].max()) + 15)


# ---------------------------------------------------------------- splatting


class Buffers:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.lw, self.lh = max(2, w // 4), max(2, h // 4)
        self.sharp_i, self.sharp_w = [], []
        self.smoke_i, self.smoke_w = [], []

    def point(self, x, y, col):
        """Bilinear splat into the sharp buffer."""
        x0 = np.floor(x).astype(np.int64)
        y0 = np.floor(y).astype(np.int64)
        ok = (x0 >= 0) & (y0 >= 0) & (x0 < self.w - 1) & (y0 < self.h - 1)
        x0, y0, fx, fy, col = x0[ok], y0[ok], (x - x0)[ok], (y - y0)[ok], col[ok]
        base = y0 * self.w + x0
        for dx, dy, wt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            self.sharp_i.append(base + dy * self.w + dx)
            self.sharp_w.append(col * wt[:, None])

    def dot(self, x, y, col):
        """Nearest-pixel splat into the sharp buffer (dense clouds)."""
        xi = x.astype(np.int64)
        yi = y.astype(np.int64)
        ok = (x >= 0) & (y >= 0) & (xi < self.w) & (yi < self.h)
        self.sharp_i.append(yi[ok] * self.w + xi[ok])
        self.sharp_w.append(col[ok])

    def squares(self, x, y, side, col):
        """Solid k x k squares (near motes), grouped by size."""
        for k in range(2, 11):
            m = side == k
            if not m.any():
                continue
            x0 = np.round(x[m] - k / 2).astype(np.int64)
            y0 = np.round(y[m] - k / 2).astype(np.int64)
            ok = (x0 >= 0) & (y0 >= 0) & (x0 + k <= self.w) & (y0 + k <= self.h)
            if not ok.any():
                continue
            off = (np.arange(k)[:, None] * self.w + np.arange(k)[None, :]).ravel()
            idx = ((y0[ok] * self.w + x0[ok])[:, None] + off[None, :]).ravel()
            self.sharp_i.append(idx)
            self.sharp_w.append(np.repeat(col[m][ok], k * k, axis=0))

    def smoke(self, x, y, col):
        lx = (x * self.lw / self.w).astype(np.int64)
        ly = (y * self.lh / self.h).astype(np.int64)
        ok = (lx >= 0) & (ly >= 0) & (lx < self.lw) & (ly < self.lh)
        self.smoke_i.append(ly[ok] * self.lw + lx[ok])
        self.smoke_w.append(col[ok])

    @staticmethod
    def _accumulate(idx, wts, n):
        if not idx:
            return np.zeros((n, 3), np.float32)
        idx = np.concatenate(idx)
        wts = np.concatenate(wts)
        out = np.empty((n, 3), np.float32)
        for c in range(3):
            out[:, c] = np.bincount(idx, wts[:, c], minlength=n)
        return out

    def sharp_image(self):
        return self._accumulate(self.sharp_i, self.sharp_w, self.w * self.h).reshape(self.h, self.w, 3)

    def smoke_image(self):
        return self._accumulate(self.smoke_i, self.smoke_w, self.lw * self.lh).reshape(self.lh, self.lw, 3)


def project(p, cam, w, h):
    pos, right, up, fwd, focal = cam
    d = p - pos
    z = d @ fwd
    f = focal * w
    with np.errstate(divide="ignore", invalid="ignore"):
        x = w / 2 + f * (d @ right) / z
        y = h / 2 - f * (d @ up) / z
    return x, y, z, f


def _streaks(buf, x, y, xp, yp, col, budget=350_000):
    """Line samples from the previous screen position to the current one."""
    length = np.hypot(x - xp, y - yp)
    n = np.clip(np.ceil(length / 0.9), 2, 240).astype(np.int64)
    if n.sum() > budget:  # very fast frames: coarser sampling instead of a stall
        n = np.maximum(2, (n * (budget / n.sum())).astype(np.int64))
    total = int(n.sum())
    if total == 0:
        return
    owner = np.repeat(np.arange(len(n)), n)
    starts = np.cumsum(n) - n
    u = (np.arange(total) - starts[owner]) / (n[owner] - 1)
    sx = xp[owner] + (x - xp)[owner] * u
    sy = yp[owner] + (y - yp)[owner] * u
    fade = (0.12 + 0.88 * u**1.6)[:, None]
    gain = np.clip(2.2 / np.sqrt(n[owner]), 0.35, 1.0)[:, None]
    buf.point(sx, sy, col[owner] * fade * gain)


def splat_layers(buf, t, cam, prev, kres):
    w, h = buf.w, buf.h
    cz = cam[0][2]
    for name, L in LAYERS.items():
        z0, z1 = _ZRANGE[name]
        if not L.get("far") and (cz < z0 or cz > z1):
            continue
        p = positions(L, t)
        x, y, z, f = project(p, cam, w, h)
        margin = 0.15 * w
        vis = (z > 0.15) & (x > -margin) & (x < w + margin) & (y > -margin) & (y < h + margin)
        if not vis.any():
            continue
        idx = np.nonzero(vis)[0]
        x, y, z = x[idx], y[idx], z[idx]
        fade = np.clip((z - 0.15) / 1.6, 0, 1) ** 2
        if "fog" in L:
            fade = fade * np.exp(-z / float(L["fog"]))
        if name == "galaxy":  # hidden by the wormhole walls until the exit
            fade = fade * _ss(WORM_B - 6, WORM_B + 8, dist(t))
        col = L["c"][idx] * (fade * kres)[:, None]

        smoke = float(L.get("smoke", 0.0))
        if smoke:
            buf.smoke(x, y, col * smoke)
        sharp = float(L.get("sharp", 1.0 if not smoke else 0.6))

        if "size" in L:
            side = np.clip(np.round(L["size"][idx] * f / z), 0, 10).astype(np.int64)
            big = side >= 2
            buf.squares(x[big], y[big], side[big], col[big] * 0.9)
        else:
            big = np.zeros(len(idx), bool)

        if L.get("streak"):
            pp = p[idx] if "p" in L else positions(L, t - SHUTTER)[idx]
            xp, yp, zp, _ = project(pp, prev, w, h)
            moving = (zp > 0.15) & (np.hypot(x - xp, y - yp) > 1.6)
            frac = float(L["streak"])
            if frac < 1:
                moving &= (idx % int(round(1 / frac))) == 0
            moving &= np.hypot(x - xp, y - yp) < 1.2 * w
            _streaks(buf, x[moving], y[moving], xp[moving], yp[moving], col[moving] * sharp)
            still = ~moving & ~big
        else:
            still = ~big
        if L.get("fine"):
            buf.point(x[still], y[still], col[still] * sharp)
        else:
            buf.dot(x[still], y[still], col[still] * sharp)


# ---------------------------------------------------------------- image ops

_UP = {}


def upsample(img, h, w):
    """Bilinear resize of an (lh, lw, 3) image to (h, w, 3)."""
    lh, lw = img.shape[:2]
    key = (lh, lw, h, w)
    if key not in _UP:
        def axis(n_out, n_in):
            c = np.clip((np.arange(n_out) + 0.5) * n_in / n_out - 0.5, 0, n_in - 1)
            i0 = np.floor(c).astype(np.int64)
            i1 = np.minimum(i0 + 1, n_in - 1)
            return i0, i1, (c - i0).astype(np.float32)
        _UP[key] = (axis(h, lh), axis(w, lw))
    (r0, r1, rw), (c0, c1, cw) = _UP[key]
    rows = img[r0] * (1 - rw)[:, None, None] + img[r1] * rw[:, None, None]
    return rows[:, c0] * (1 - cw)[None, :, None] + rows[:, c1] * cw[None, :, None]


def downsample(img, lh, lw):
    h, w = img.shape[:2]
    fy, fx = h // lh, w // lw
    return img[: lh * fy, : lw * fx].reshape(lh, fy, lw, fx, 3).mean(axis=(1, 3))


def god_rays(img, cx, cy, strength, steps=14, reach=0.55):
    """Radial blur of ``img`` toward (cx, cy) in its own pixel coordinates."""
    lh, lw = img.shape[:2]
    yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
    out = np.zeros_like(img)
    norm = 0.0
    for k in range(steps):
        sc = 1 - reach * k / steps
        sx = np.clip(np.round(cx + (xx - cx) * sc), 0, lw - 1).astype(np.int64)
        sy = np.clip(np.round(cy + (yy - cy) * sc), 0, lh - 1).astype(np.int64)
        wk = 0.93**k
        out += img[sy, sx] * wk
        norm += wk
    return out * (strength / norm)


def blob(lh, lw, cx, cy, radius, col):
    yy, xx = np.mgrid[0:lh, 0:lw].astype(np.float32)
    g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * radius**2))
    return g[..., None] * col[None, None, :]


def light_sources(t, cam, w, h):
    """Screen-space lights: (x, y, z, colour, power)."""
    s = dist(t)
    out = []
    portal = 1 - _ss(26.0, 28.5, s)
    if portal > 0:
        out.append((PORTAL + [0, 0.2, 0.6], np.array(PALETTE.rgb("portal")), 2.6 * portal))
    exitw = _ss(WORM_A + 10, WORM_B - 4, s) * (1 - _ss(WORM_B - 1, WORM_B + 3, s))
    if exitw > 0:
        out.append((center(WORM_B + 6.0), np.array(PALETTE.rgb("portal")), 3.0 * exitw))
    gal = _ss(WORM_B - 4, WORM_B + 10, s)
    if gal > 0:
        out.append((GALAXY, np.array(PALETTE.rgb("core")), 1.1 * gal))
    res = []
    for p, c, k in out:
        x, y, z, _ = project(np.asarray(p, float)[None], cam, w, h)
        if z[0] > 0.5:
            res.append((float(x[0]), float(y[0]), float(z[0]), c.astype(np.float32), k))
    return res


# ---------------------------------------------------------------- frame


def render_frame(t, w, h):
    cam = camera(t)
    prev = camera(t - SHUTTER)
    kres = (720.0 / w) ** 2 * 1.0
    buf = Buffers(w, h)
    splat_layers(buf, t, cam, prev, kres)
    sharp = buf.sharp_image()
    smoke = buf.smoke_image()
    lh, lw = buf.lh, buf.lw
    q = lw / 180.0  # low-res pixel scale relative to 720p

    low = downsample(sharp, lh, lw)
    soft = gaussian_filter(smoke, (1.4 * q, 1.4 * q, 0)) * 1.0 + gaussian_filter(smoke, (5 * q, 5 * q, 0)) * 0.6
    bloom = gaussian_filter(low, (2.0 * q, 2.0 * q, 0)) * 0.9 + gaussian_filter(low, (9 * q, 9 * q, 0)) * 0.7

    lights = np.zeros_like(low)
    s = dist(t)
    for x, y, z, col, k in light_sources(t, cam, w, h):
        lx, ly = x * lw / w, y * lh / h
        r = np.clip(55.0 / z, 1.5, 40) * q
        lights += blob(lh, lw, lx, ly, r, col) * (k * 0.35) + blob(lh, lw, lx, ly, r * 4, col) * (k * 0.05)
    rays = np.zeros_like(low)
    src = light_sources(t, cam, w, h)
    if src:
        x, y, _, _, k = max(src, key=lambda e: e[4])
        rays = god_rays(soft * 0.5 + low * 1.0 + lights, x * lw / w, y * lh / h, 0.35 * min(k, 1.5))

    total = soft * 1.0 + bloom * 0.8 + lights + rays
    img = sharp + upsample(total, h, w)

    # exposure: fade in, flashes at the portal and the wormhole exit, fade out
    flash = 1.0 * np.exp(-(((s - 27.2) / 1.6) ** 2)) + 1.2 * np.exp(-(((s - WORM_B - 1) / 3.5) ** 2))
    flash = float(flash)
    expo = float(1.0 * _ss(0.0, 1.4, t) * (1 - _ss(DURATION - 1.2, DURATION, t)) * (1 + flash))
    img = 1 - np.exp(-img * expo)
    img = img + flash * 0.05 * _ss(0, 1, t)
    img = BG + (1 - BG) * np.clip(img, 0, 1)
    img *= 255.0
    img += np.random.default_rng(int(t * 1000)).random((h, w, 1), np.float32)
    rgba = np.empty((h, w, 4), np.uint8)
    rgba[..., :3] = np.clip(img, 0, 255)
    rgba[..., 3] = 255
    return rgba, speed(t), flash


def draw(t, size):
    w, h = int(size[0]), int(size[1])
    rgba, v, flash = render_frame(t, w, h)
    fr = Frame(size, palette=PALETTE, design=DESIGN)
    fr.c.save()
    fr.c.resetMatrix()
    fr.c.drawImage(image_from_array(rgba), 0, 0)
    fr.c.restore()
    fr.zoom_blur(0.075 * _ss(8, 17, v) + 0.05 * min(flash, 1.0), samples=8)
    fr.chroma(1.6 * _ss(10, 17, v) + 2.0 * min(flash, 1.0))
    fr.vignette(0.55)
    fr.grain(t, 0.06)
    return fr.finish()


def build():
    key = max(Path(__file__).stat().st_mtime, Path(world.__file__).stat().st_mtime)
    with THEME.use():
        return draw_scene(draw, DURATION, theme=THEME, design=DESIGN, key=str(key))


if __name__ == "__main__":
    run(build)
