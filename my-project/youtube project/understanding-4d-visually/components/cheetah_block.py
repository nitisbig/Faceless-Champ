"""The Cheetah Block: footage frames stacked along time into a translucent 3D block.

Factored out of scenes/s01_cinematic.py. World coordinates are view coordinates (x right,
y up, z = time into depth). Used in S01, S07, S15B, S19A, S26B and S29.
"""

from __future__ import annotations

import math
from functools import lru_cache

import media
import numpy as np
import skia
from fx import ease_out, lerp, lin, smooth

from components import hud
from components.slice_plane import draw_plane

SHEET_W, SHEET_H = 3.2, 1.8
BLOCK_L = 4.4
SHEETS = tuple(range(1, media.FRAME_COUNT + 1, 2))  # every second 5 fps frame forms the block


class CheetahBlock:
    def __init__(self, center=(0.0, 0.0, 0.0), scale=1.0):
        self.center = np.asarray(center, float)
        self.k = scale

    def z_of(self, frame: float) -> float:
        return (-BLOCK_L / 2 + BLOCK_L * (frame - 1) / (media.FRAME_COUNT - 1)) * self.k

    def sheet(self, z: float, scale: float = 1.0) -> np.ndarray:
        """4x3 world corners (TL, TR, BR, BL) of a sheet at depth ``z`` (block-local, scaled)."""
        hw, hh = SHEET_W / 2 * scale * self.k, SHEET_H / 2 * scale * self.k
        return self.center + np.array([[-hw, hh, z], [hw, hh, z], [hw, -hh, z], [-hw, -hh, z]])

    def pixel(self, frame: float, px: float, py: float) -> np.ndarray:
        """World point of image pixel (px, py) (1920x1080 prepared frame) on that frame's sheet."""
        tl, tr, _, bl = self.sheet(self.z_of(frame))
        return tl + (tr - tl) * (px / 1920) + (bl - tl) * (py / 1080)

    def box(self, scale=1.0) -> np.ndarray:
        """8 corners of the whole block."""
        hw, hh, hl = SHEET_W / 2 * self.k * scale, SHEET_H / 2 * self.k * scale, BLOCK_L / 2 * self.k * scale
        return self.center + np.array([[x, y, z] for x in (-hw, hw) for y in (-hh, hh) for z in (-hl, hl)])

    def draw(
        self,
        fr,
        cam,
        t,
        unfold=1.0,
        hold=38,
        active=None,
        active_alpha=1.0,
        volume=1.0,
        slice_alpha=0.0,
        outline=0.0,
        fade=1.0,
        border=None,
    ):
        """unfold: 0 = only the held frame, 1 = full block. active: frame index shown sharp (float ok)."""
        if fade <= 0.003:
            return
        hold_z = self.z_of(hold)
        maxd = max(abs(j - hold) for j in SHEETS)
        items = []
        if volume > 0:
            for j in SHEETS:
                delay = 0.65 * abs(j - hold) / maxd
                p = lin(unfold, delay, delay + 0.35)
                a = smooth(p) * volume * fade
                if a <= 0.003:
                    continue
                z = lerp(hold_z, self.z_of(j), ease_out(p))
                quad = self.sheet(z)
                xs, ys, depth = cam.project(quad)
                if np.all(depth > 0.08):
                    items.append((float(depth.mean()), "volume", j, list(zip(xs, ys)), a))
        z_active = hold_z if active is None else self.z_of(active)
        if active_alpha * fade > 0.003:
            xs, ys, depth = cam.project(self.sheet(z_active))
            if np.all(depth > 0.08):
                index = hold if active is None else round(active)
                items.append((float(depth.mean()), "active", index, list(zip(xs, ys)), active_alpha * fade))
        for _, kind, index, quad, a in sorted(items, key=lambda it: -it[0]):
            if kind == "volume":
                # Additive and faint: dark grass vanishes, the bright cheetah accumulates into a trail through time.
                fr.image_quad(media.thumb(index), quad, 0.075 * a, blend=skia.BlendMode.kPlus)
                xs, ys = zip(*quad)
                fr.poly(xs, ys, "w", 1.0, 0.07 * a, close=True)
            else:
                fr.image_quad(media.frame(index), quad, a)
                xs, ys = zip(*quad)
                fr.poly(xs, ys, "ink", 1.4, a * (0.5 if border is None else border), close=True)
        if slice_alpha > 0:
            draw_plane(fr, cam, self.sheet(z_active, 1.07), t, slice_alpha * fade)
        if outline > 0:
            self.draw_outline(fr, cam, outline * fade)

    def draw_outline(self, fr, cam, alpha, color="ink", width=1.6, glow=0.5):
        b = self.box()
        xs, ys, z = cam.project(b)
        if np.any(z <= 0.08):
            return
        for i in range(8):
            for j in range(i + 1, 8):
                if bin(i ^ j).count("1") == 1:
                    fr.line(xs[i], ys[i], xs[j], ys[j], color, width, alpha, glow=glow)

    def draw_axes(self, fr, cam, ux=1.0, uy=1.0, ut=1.0, t_name="t", t_color="w", t_flare=0.0, alpha=1.0):
        """x (red) along the bottom edge, y (orange) up the side, time (blue) into depth, from the front corner.

        t_flare (0..1) widens and brightens the time axis and lights its tip ("time becomes a direction").
        """
        if alpha <= 0.003:
            return
        b = self.box()
        origin = b[0] + np.array([-0.15, -0.15, -0.15]) * self.k
        size = np.array([SHEET_W + 0.9, SHEET_H + 0.8, BLOCK_L + 1.0]) * self.k
        hud.axis3d(fr, cam, origin, [size[0], 0, 0], "x", "x", ux * alpha)
        hud.axis3d(fr, cam, origin, [0, size[1], 0], "y", "y", uy * alpha)
        hud.axis3d(fr, cam, origin, [0, 0, size[2]], t_name, t_color, ut * alpha)
        if t_flare > 0.003 and ut > 0:
            xs, ys, z = cam.project(np.array([origin, origin + np.array([0, 0, size[2]]) * ut]))
            if np.all(z > 0.05):
                fr.line(xs[0], ys[0], xs[1], ys[1], t_color, 2.4 + 2.4 * t_flare, t_flare * alpha, glow=1.4)
                fr.glow_dot(xs[1], ys[1], 5 + 7 * t_flare, t_color, t_flare * alpha, 1.5)


def playback_frame(t: float, t0: float, t1: float, f0: float = 1.0, f1: float = media.FRAME_COUNT) -> float:
    """Frame index swept linearly from f0 to f1 over [t0, t1] (the slice *is* playback)."""
    return lerp(f0, f1, lin(t, t0, t1))


def stutter_tick(t: float) -> float:
    """1 -> 0 decay after each new 5 fps frame: the soft 'tick' of stepped playback."""
    since = (t * media.FRAME_FPS) % 1 / media.FRAME_FPS
    return math.exp(-since * 18)


@lru_cache(maxsize=1)
def _track():
    """Centroid of the cheetah's coat in every 5 fps frame (1920x1080 px), smoothed over 5 frames."""
    from PIL import Image

    pts = []
    for i in range(1, media.FRAME_COUNT + 1):
        a = np.asarray(Image.open(media.PREPARED / "thumb" / f"{i:03d}.jpg").convert("RGB")).astype(np.int16)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        ys, xs = np.nonzero((r > 120) & (r > g + 15) & (r > b + 45))  # tan coat: not grass, not shadow
        sx, sy = 1920 / a.shape[1], 1080 / a.shape[0]
        pts.append((xs.mean() * sx, ys.mean() * sy))
    pts = np.array(pts)
    kernel = np.ones(5) / 5
    padded = np.pad(pts, ((2, 2), (0, 0)), mode="edge")
    return np.stack([np.convolve(padded[:, k], kernel, mode="valid") for k in range(2)], 1)


def track(frame: float) -> tuple[float, float]:
    """Where the cheetah is in frame ``frame`` (float ok): the anchor of its world-line."""
    pts = _track()
    f = min(max(frame, 1.0), media.FRAME_COUNT) - 1
    i = min(int(f), media.FRAME_COUNT - 2)
    u = f - i
    p = pts[i] * (1 - u) + pts[i + 1] * u
    return float(p[0]), float(p[1])
