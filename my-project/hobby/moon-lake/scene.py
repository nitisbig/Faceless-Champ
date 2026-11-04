"""Moon lake: a slow 20 s glide across a moonlit mountain lake built from particles, smoke and light.

Rendered on the GPU (gpu.PointRenderer, moderngl): about 3M points with real depth occlusion,
reflections in the water, shader-animated glitter, mist, fireflies and chimney smoke.

The flight leaves a lantern-lit pier through a mist bank, skims the water toward the moon as it
clears the cloud, glances at a lit cabin on the far right shore, then rises to show the whole
lake with the moon's path on the water.

    python scene.py --frame 3 9 15 --quality medium
    python render.py                     # full 20 s, 1280x720, 30 fps, GPU, one process
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d

import world
from faceless_champ import Theme, run
from faceless_champ.draw import Frame, Palette, draw_scene, image_from_array, noise
from world import LANTERNS, MOON_DIR, MOON_POS, WINDOW

THEME = Theme.named("midnight")
PALETTE = Palette.from_theme(
    THEME,
    bg="#020306",
    pine="#3a5446",
    bark="#3d3832",
    rock="#5d6570",
    snow="#dfe7f2",
    water="#5d7a8c",
    mist="#a9b9c4",
    wood="#8a6e55",
    lamp="#ffc27a",
    window="#ffcf8f",
    moon="#dbe6ff",
    star="#eef3ff",
    firefly="#d9ff9a",
    sky="#6f86a8",
)
DESIGN = (1920, 1080)
DURATION = 20.0
LAYERS = world.load(PALETTE.rgb)
GAIN = {  # per-layer brightness, tuned on stills without rebuilding the world
    "pines": 0.8, "shore": 1.0, "mountains": 0.65, "water": 1.0, "mist": 0.3, "pier": 1.0, "flames": 1.0,
    "cabin": 1.0, "window": 1.0, "chimney": 1.0, "fireflies": 1.0, "stars": 1.0, "moon": 1.0, "clouds": 0.5,
}
for _name, _L in LAYERS.items():
    _L["gain"] = GAIN.get(_name, 1.0)
LAYERS["mist"]["fog"] = 110.0  # distant mist would pile up into a white band at grazing angles

C = {k: np.array(PALETTE.rgb(k), np.float32) for k in ("bg", "lamp", "window", "moon")}

# ---------------------------------------------------------------- camera

_TT = np.linspace(-1, DURATION + 1, 2201)
_V = np.interp(_TT, [0, 3.0, 8.0, 14.0, 20.0], [0.8, 2.2, 3.2, 3.6, 2.6])
_V = gaussian_filter1d(_V, 0.6 / (_TT[1] - _TT[0]), mode="nearest")
_S = np.concatenate([[0], np.cumsum((_V[1:] + _V[:-1]) / 2 * np.diff(_TT))])
_S -= np.interp(0.0, _TT, _S)


def dist(t):
    return float(np.interp(t, _TT, _S))


def _ss(a, b, x):
    u = min(max((x - a) / (b - a), 0.0), 1.0)
    return u * u * (3 - 2 * u)


def _bump(a, b, x):
    u = min(max((x - a) / (b - a), 0.0), 1.0)
    return float(np.sin(np.pi * u) ** 2)


def _yaw_dir(yaw, pitch):
    return np.array([np.sin(yaw) * np.cos(pitch), np.sin(pitch), np.cos(yaw) * np.cos(pitch)])


MOON_YAW = float(np.arctan2(MOON_DIR[0], MOON_DIR[2]))


def camera(t):
    """((pos, right, up, fwd), focal-in-widths): leave the pier, skim the water, rise."""
    s = dist(t)
    x = -4.0 + 4.5 * _ss(1.0, 12.0, t) - 1.5 * _ss(14.0, 20.0, t)
    y = 1.6 - 0.75 * _ss(3.0, 8.0, t) + 0.12 * np.sin(0.6 * t) + 8.0 * _ss(12.5, 19.8, t) ** 1.2
    pos = np.array([x, y, -2.0 + s])
    pos += 0.08 * np.array([noise.value(t, 0.12, seed=3), noise.value(t, 0.12, seed=4), 0])

    to_lamp = (LANTERNS.mean(axis=0) - pos)
    lamp_yaw = float(np.arctan2(to_lamp[0], to_lamp[2]))
    to_cabin = WINDOW - pos
    cabin_yaw = float(np.arctan2(to_cabin[0], to_cabin[2]))
    yaw = lamp_yaw * (1 - _ss(1.5, 7.5, t)) + MOON_YAW * _ss(1.5, 7.5, t)
    yaw += (cabin_yaw - MOON_YAW) * 0.55 * _bump(9.5, 15.5, t)
    pitch = np.radians(4.0 - 10.0 * _ss(12.5, 19.5, t))
    fwd = _yaw_dir(yaw, pitch)

    roll = 0.03 * np.sin(0.27 * t) + 0.012 * noise.value(t, 0.2, seed=7)
    up0 = np.array([0.0, 1.0, 0.0])
    right = np.cross(up0, fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)
    cr, sr = np.cos(roll), np.sin(roll)
    right, up = right * cr + up * sr, up * cr - right * sr
    focal = 0.84 + 0.08 * _ss(12, 20, t)
    return (pos, right, up, fwd), focal


# ---------------------------------------------------------------- render

_RENDERERS = {}


def renderer(w, h):
    if (w, h) not in _RENDERERS:
        from gpu import PointRenderer

        _RENDERERS[(w, h)] = PointRenderer(LAYERS, w, h)
    return _RENDERERS[(w, h)]


def moon_strength(t):
    """The moon clears the cloud between 2 and 7 s."""
    return 0.25 + 0.75 * _ss(2.0, 7.0, t)


def render_frame(t, w, h):
    cam, focal = camera(t)
    m = moon_strength(t)
    uni = dict(moon_k=m, moon_col=C["moon"], moon_dir=MOON_DIR, lamp0=LANTERNS[0], lamp1=LANTERNS[1], lamp_col=C["lamp"])
    flicker = [0.9 + 0.1 * noise.value(t, 3.0, seed=11 + i) for i in range(2)]
    lights = [
        (MOON_POS, C["moon"], 40.0, 0.9 * m),
        (LANTERNS[0], C["lamp"], 0.16, 1.4 * flicker[0]),
        (LANTERNS[1], C["lamp"], 0.16, 1.4 * flicker[1]),
        (WINDOW + [-0.1, 0, 0], C["window"], 0.6, 0.8),
    ]
    expo = 0.95 * _ss(0.0, 2.5, t) * (1 - _ss(DURATION - 1.3, DURATION, t))
    return renderer(w, h).frame(
        cam, focal, t, uni, lights, (MOON_POS, C["moon"] * m, 0.05, 0.35),
        k_soft=1.0, k_bloom=0.5, k_rays=1.0, exposure=expo, flash=0.0, bg=C["bg"],
    )


def draw(t, size):
    w, h = int(size[0]), int(size[1])
    rgb = render_frame(t, w, h)
    rgba = np.empty((h, w, 4), np.uint8)
    rgba[..., :3] = rgb
    rgba[..., 3] = 255
    fr = Frame(size, palette=PALETTE, design=DESIGN)
    fr.c.save()
    fr.c.resetMatrix()
    fr.c.drawImage(image_from_array(rgba), 0, 0)
    fr.c.restore()
    fr.chroma(0.5)
    fr.vignette(0.55)
    fr.grain(t, 0.05)
    return fr.finish()


def build():
    key = max(Path(__file__).stat().st_mtime, Path(world.__file__).stat().st_mtime)
    with THEME.use():
        return draw_scene(draw, DURATION, theme=THEME, design=DESIGN, key=str(key))


if __name__ == "__main__":
    run(build)
