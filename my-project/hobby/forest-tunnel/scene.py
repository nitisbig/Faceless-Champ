"""Forest tunnel: a 30 s point-cloud flight through a tree tunnel that curls into a vortex (16:9).

Beats:
    0-8 s    glide down the tunnel toward the lit path ahead, speed streaks along the floor
    8-14 s   slow down and turn to watch the gnarled trunks slide past
    14-21 s  pick up speed as the path bends right, the floor streaking under the lens
    21-30 s  the world ahead rolls up into a tube and the camera dives into it

Rendered on the GPU (gpu.TunnelRenderer).

    python scene.py --frame 4 11 18 25 --quality medium
    python render.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d

import world
from faceless_champ import Theme, run
from faceless_champ.draw import Frame, Palette, draw_scene, image_from_array, noise
from world import PATH_C, PATH_L, PATH_S, frame_at, to_world

THEME = Theme.named("midnight")
PALETTE = Palette.from_theme(
    THEME,
    bg="#000000",
    gravel="#e9ece6",
    litter="#8e9188",
    bark="#9a9a92",
    leaf="#9fbf8c",
    leaf_dark="#5d6f57",
    mote="#ffffff",
    light="#f2f7ee",
)
DESIGN = (1920, 1080)
DURATION = 30.0
SHUTTER = 0.22  # streak length in seconds of travel
LAYERS = world.load(PALETTE.rgb)
GAIN = {"path": 1.0, "path_streak": 0.9, "ground": 1.2, "trees": 1.8, "canopy": 3.4, "motes": 1.0}
for _name, _L in LAYERS.items():
    _L["gain"] = GAIN.get(_name, 1.0)
# the references show a few dozen streaks, not thousands: keep sparse subsets
_rng = np.random.default_rng(9)
for _name, _keep in (("path_streak", 1800), ("motes", 7000)):
    _idx = np.sort(_rng.choice(len(LAYERS[_name]["suv"]), _keep, replace=False))
    for _k in ("suv", "alb", "size"):
        LAYERS[_name][_k] = LAYERS[_name][_k][_idx]

BG = np.array(PALETTE.rgb("bg"), np.float32)
LIGHT = np.array(PALETTE.rgb("light"), np.float32)

# ---------------------------------------------------------------- camera

_TT = np.linspace(-1, DURATION + 1, 3201)
_V = np.interp(_TT, [0, 4, 8, 10.5, 13.5, 16, 20, 24, 30], [1.2, 2.6, 2.2, 1.2, 1.5, 5.0, 6.0, 7.0, 8.0])
_V = gaussian_filter1d(_V, 0.6 / (_TT[1] - _TT[0]), mode="nearest")
_S = np.concatenate([[0], np.cumsum((_V[1:] + _V[:-1]) / 2 * np.diff(_TT))])
_S -= np.interp(0.0, _TT, _S)


def dist(t):
    return float(np.interp(t, _TT, _S))


def _ss(a, b, x):
    u = min(max((x - a) / (b - a), 0.0), 1.0)
    return u * u * (3 - 2 * u)


def _bump(a, b, c, d, x):
    return _ss(a, b, x) * (1 - _ss(c, d, x))


def curl(t):
    """(amount, start s) of the world curl at time t."""
    amt = _ss(21.0, 26.5, t)
    return amt, dist(t) + 9.0 - 7.5 * _ss(25.5, 29.5, t)


def camera(t):
    """Dict of camera uniforms at time t (position, basis, focal)."""
    s = dist(t)
    u = 0.6 * _bump(8, 11, 13, 15.5, t) + 0.3 * np.sin(0.21 * t)
    h = 1.45 + 0.1 * np.sin(0.4 * t) - 0.25 * _bump(14, 17, 25, 28, t)
    pos = to_world((s, u, h)) + 0.04 * np.array([noise.value(t, 0.3, seed=1), noise.value(t, 0.3, seed=2), 0])
    _, lat, tan = frame_at(s)
    yaw = np.radians(32 * _bump(8.0, 11.0, 13.2, 15.8, t) + 12 * _bump(21, 24.5, 27, 29.5, t)) + 0.03 * noise.value(t, 0.15, seed=3)
    pitch = np.radians(-2 - 7 * _bump(14, 17, 22, 26, t) + 2 * _ss(26, 29, t))
    flat = np.cos(yaw) * tan + np.sin(yaw) * lat
    fwd = flat * np.cos(pitch) + np.array([0, np.sin(pitch), 0])
    fwd /= np.linalg.norm(fwd)
    roll = 0.025 * noise.value(t, 0.2, seed=4) + np.radians(8) * _bump(22, 26, 28, 30, t)
    right = np.cross([0.0, 1.0, 0.0], fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    cr, sr = np.cos(roll), np.sin(roll)
    right, up = right * cr + up * sr, up * cr - right * sr
    return pos, right, up, fwd, 0.78 - 0.08 * _ss(16, 26, t)


# ---------------------------------------------------------------- render

_RENDERERS = {}


def renderer(w, h):
    if (w, h) not in _RENDERERS:
        from gpu import TunnelRenderer

        _RENDERERS[(w, h)] = TunnelRenderer(LAYERS, PATH_S, PATH_C, PATH_L, w, h)
    return _RENDERERS[(w, h)]


def render_frame(t, w, h):
    pos, right, up, fwd, focal = camera(t)
    ppos, pright, pup, pfwd, pfocal = camera(t - SHUTTER)
    amt, s0 = curl(t)
    pamt, ps0 = curl(t - SHUTTER)
    s = dist(t)
    gaze = _bump(7.5, 10.5, 13.5, 16.0, t)
    uni = dict(
        cam_pos=pos, cam_right=right, cam_up=up, cam_fwd=fwd, focal=focal,
        pcam_pos=ppos, pcam_right=pright, pcam_up=pup, pcam_fwd=pfwd, pfocal=pfocal,
        curl_amt=amt, curl_s0=s0, pcurl_amt=pamt, pcurl_s0=ps0, curl_axis=(2.4, 3.0), curl_len=26.0,
        t=t, t_prev=t - SHUTTER,
        # the light runs ahead of the camera; while we watch the trunks it swings in beside them
        light_suv=(s + 17.0 - 9.0 * gaze, 2.2 * gaze, 2.0), light_r=8.0, light_k=2.4, ambient=0.06, light_col=LIGHT,
    )
    expo = 1.5 * _ss(0.0, 2.0, t) * (1 - _ss(DURATION - 1.5, DURATION, t))
    return renderer(w, h).frame(uni, k_soft=1.0, k_bloom=0.35, exposure=expo, bg=BG, seed=float(t * 37.0 % 100.0))


def draw(t, size):
    w, h = int(size[0]), int(size[1])
    rgba = np.empty((h, w, 4), np.uint8)
    rgba[..., :3] = render_frame(t, w, h)
    rgba[..., 3] = 255
    fr = Frame(size, palette=PALETTE, design=DESIGN)
    fr.c.save()
    fr.c.resetMatrix()
    fr.c.drawImage(image_from_array(rgba), 0, 0)
    fr.c.restore()
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def build():
    key = max(Path(__file__).stat().st_mtime, Path(world.__file__).stat().st_mtime)
    with THEME.use():
        return draw_scene(draw, DURATION, theme=THEME, design=DESIGN, key=str(key))


if __name__ == "__main__":
    run(build)
