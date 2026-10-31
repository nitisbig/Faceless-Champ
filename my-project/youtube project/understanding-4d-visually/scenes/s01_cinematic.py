"""S01 - COLD OPEN: A CHEETAH IN FOUR DIMENSIONS, 00:00.000 - 00:25.000.

Act 1  0.0-4.5   Footage           smooth 30 fps cheetah, 2.39:1 bars, slow push-in.
Act 2  4.5-7.5   A frame is 2D     playback stutters to 5 fps; the frame comes loose and
                                   becomes a sheet in space; its x / y edges trace on.
Act 3  7.5-13.6  Stack into time   every other frame unfolds behind it into a block of time;
                                   a blue slicing plane sweeps through and the video plays.
Act 4 12.6-15.0  Reveal the plane  floor grid grows out of the dark; x, y, t axes draw on.
Act 5 15.0-19.0  Shadow 3D -> 2D   sheets dissolve, the block becomes a cube (t becomes z),
                                   a light from above casts its 2D shadow on the floor.
Act 6 19.0-25.0  4D -> 3D          the cube extrudes along w into a tesseract - the 3D shadow
                                   of a 4D object - with the cheetah playing on its w-slices.

One continuous camera spline, no cuts. The only text is the axis letters.
Everything is drawn with skia inside one Faceless Champ FunctionSource.
"""

from __future__ import annotations

import itertools
import math
from functools import lru_cache
from pathlib import Path

import media
import numpy as np
import skia
from fx import Frame, col, ease_io, ease_out, env, lerp, lin, mix, quad_matrix, smooth
from space import orbit, rot_x, rot_y, text3d
from theme import THEME, TOKENS, H, W

DURATION = 25.0
T = {
    "loose": 4.5,  # footage hands over to the 3D sheet
    "freeze": 7.5,  # current frame holds; the stack unfolds
    "sweep": (10.0, 13.6),  # slicing plane plays the clip
    "grid": (12.6, 15.0),
    "cube": (15.6, 17.0),  # block -> cube morph
    "light": (15.8, 16.9),
    "w": (19.4, 21.4),  # extrusion along w
    "spin": 21.2,  # ZW rotation starts
    "slices": 21.6,
}

# ------------------------------------------------------------------ world (units; y up, z away from camera)
SHEET_W, SHEET_H = 3.2, 1.8
BLOCK_L = 4.4
FLOOR = -1.5
FOCAL = 1500.0
HOLD_FRAME = 38  # the frame on screen when the stack unfolds
SHEETS = tuple(range(1, media.FRAME_COUNT + 1, 2))
AXIS_O = np.array([-1.6, FLOOR, -BLOCK_L / 2])  # the block's front-left corner
AXIS_O_CUBE = np.array([-3.4, FLOOR, -1.4])  # moved clear of the cube so no axis cuts through it
LIGHT = np.array([0.9, 6.5, 0.6])
D4 = 5.0
CUBE = 1.25

V4 = np.array(list(itertools.product((-1, 1), repeat=4)), float)
EDGES = [
    (i, j, int(np.flatnonzero(V4[i] != V4[j])[0]))
    for i, j in itertools.combinations(range(16), 2)
    if np.count_nonzero(V4[i] != V4[j]) == 1
]


def z_of(frame: float) -> float:
    return -BLOCK_L / 2 + BLOCK_L * (frame - 1) / (media.FRAME_COUNT - 1)


# ------------------------------------------------------------------ camera: one Hermite spline, no cuts

_D0 = FOCAL * SHEET_W / (W * 1.06)  # matches the end of the 2D push-in exactly
_KEYS = [  # time, target xyz, dist, elev, azim
    (4.5, (0, 0, z_of(HOLD_FRAME)), _D0, 0.0, 0.0),
    (6.2, (0, 0, z_of(HOLD_FRAME)), 3.9, 0.10, -0.32),
    (8.0, (0, 0, z_of(HOLD_FRAME) * 0.5), 6.0, 0.20, -0.62),
    (10.5, (0, 0, 0.2), 9.0, 0.26, -0.86),
    (13.0, (0, -0.35, 0.2), 10.2, 0.36, -0.95),
    (15.5, (0, -0.25, 0), 10.4, 0.44, -0.70),
    (19.0, (0, 0.05, 0), 9.8, 0.38, -0.35),
    (22.5, (0, 0.15, 0), 9.2, 0.28, -0.06),
    (25.0, (0, 0.2, 0), 9.6, 0.24, 0.08),
]
_KT = np.array([k[0] for k in _KEYS])
_KV = np.array([[*k[1], k[2], k[3], k[4]] for k in _KEYS], float)


def _spline(t: float) -> np.ndarray:
    if t <= _KT[0]:
        return _KV[0]
    if t >= _KT[-1]:
        return _KV[-1]
    i = int(np.searchsorted(_KT, t)) - 1
    t0, t1 = _KT[i], _KT[i + 1]

    def tangent(k):
        if k == 0 or k == len(_KT) - 1:
            return np.zeros(_KV.shape[1])
        return (_KV[k + 1] - _KV[k - 1]) / (_KT[k + 1] - _KT[k - 1])

    h = t1 - t0
    u = (t - t0) / h
    h00, h10, h01, h11 = 2 * u**3 - 3 * u**2 + 1, u**3 - 2 * u**2 + u, -2 * u**3 + 3 * u**2, u**3 - u**2
    return h00 * _KV[i] + h10 * h * tangent(i) + h01 * _KV[i + 1] + h11 * h * tangent(i + 1)


def camera(t: float):
    v = _spline(t)
    return orbit(v[:3], v[3], v[4], v[5], focal=FOCAL)


def project(cam, pts):
    """Nx3 world points -> (xs, ys, depth, all-in-front)."""
    xs, ys, z = cam.project(pts)
    return xs, ys, z, bool(np.all(z > 0.08))


# ------------------------------------------------------------------ the 4D model (box -> cube -> tesseract)


def theta_zw(t: float) -> float:
    if t <= T["spin"]:
        return 0.0
    return 0.5 * (t - T["spin"]) * smooth(lin(t, T["spin"], T["spin"] + 1.4))


def model(t: float):
    """Half extents (4), 3D rotation, centre."""
    u = ease_io(lin(t, *T["cube"]))
    half3 = lerp(np.array([SHEET_W / 2, SHEET_H / 2, BLOCK_L / 2]), np.full(3, CUBE), u)
    hw = CUBE * ease_io(lin(t, *T["w"]))
    turn = ease_io(lin(t, 16.2, 18.8))
    settle = ease_io(lin(t, 19.6, 22.6))
    yaw = 0.95 * turn - 0.80 * settle + 0.025 * max(0.0, t - 16.2)
    pitch = 0.32 * turn - 0.22 * settle
    R = rot_y(yaw) @ rot_x(pitch)
    centre = np.array([0.0, 0.55 * u, 0.0])
    return np.array([*half3, hw]), R, centre


def to_world(p4: np.ndarray, t: float, R, centre) -> np.ndarray:
    a = theta_zw(t)
    c, s = math.cos(a), math.sin(a)
    z = p4[:, 2] * c - p4[:, 3] * s
    w = p4[:, 2] * s + p4[:, 3] * c
    f = D4 / (D4 - w)
    p3 = np.stack([p4[:, 0] * f, p4[:, 1] * f, z * f], 1)
    return p3 @ R.T + centre


def edge_color(axis: int, t: float) -> str:
    if axis == 2:
        return mix(TOKENS["w"], TOKENS["z"], lin(t, 15.4, 16.4))
    return TOKENS["xyzw"[axis]]


# ------------------------------------------------------------------ act 1: footage


def draw_footage(fr, t):
    if t >= T["loose"]:
        return
    image = media.opener(int(t * media.OPENER_FPS) + 1)
    fr.image_fill(image, 1.0 + 0.06 * t / T["loose"], smooth(lin(t, 0.0, 1.2)))


# ------------------------------------------------------------------ acts 2-3: sheets and the block of time


def sheet_corners(z: float, scale: float = 1.0) -> np.ndarray:
    hw, hh = SHEET_W / 2 * scale, SHEET_H / 2 * scale
    return np.array([[-hw, hh, z], [hw, hh, z], [hw, -hh, z], [-hw, -hh, z]])


def active_frame(t: float) -> float:
    if t < T["freeze"]:
        return media.frame_at(t)  # clip time = scene time: the clip keeps playing, at 5 fps
    a, b = T["sweep"]
    return HOLD_FRAME + (media.FRAME_COUNT - HOLD_FRAME) * lin(t, a, b)


def sheets_alpha(t: float) -> float:
    return 1 - smooth(lin(t, 15.3, 16.5))


def draw_sheets(fr, cam, t):
    if t < T["loose"] or sheets_alpha(t) <= 0:
        return
    fade = sheets_alpha(t)
    hold_z = z_of(HOLD_FRAME)
    items = []  # (depth, kind, payload)
    for j in SHEETS:
        appear = T["freeze"] + 0.1 + 0.045 * abs(j - HOLD_FRAME) / 2
        a = smooth(lin(t, appear, appear + 0.45)) * fade
        if a <= 0:
            continue
        z = lerp(hold_z, z_of(j), ease_out(lin(t, appear, appear + 0.7)))
        corners = sheet_corners(z)
        xs, ys, depth, ok = project(cam, corners)
        if ok:
            items.append((float(depth.mean()), "volume", (j, list(zip(xs, ys)), a)))

    f = active_frame(t)
    z_active = hold_z if t < T["sweep"][0] else z_of(f)
    active_a = (1 - smooth(lin(t, T["sweep"][1], T["sweep"][1] + 0.8))) * fade
    if active_a > 0:
        xs, ys, depth, ok = project(cam, sheet_corners(z_active))
        if ok:
            items.append((float(depth.mean()), "active", (round(f), list(zip(xs, ys)), active_a)))
    for depth, kind, (index, quad, a) in sorted(items, key=lambda it: -it[0]):
        if kind == "volume":
            # Additive, faint: dark grass vanishes, the bright cheetah accumulates into a trail through time.
            fr.image_quad(media.thumb(index), quad, 0.075 * a, blend=skia.BlendMode.kPlus)
            xs, ys = zip(*quad)
            fr.poly(xs, ys, "w", 1.0, 0.07 * a, close=True)
        else:
            fr.image_quad(media.frame(index), quad, a)
            draw_active_border(fr, quad, t, a)
    draw_slice_plane(fr, cam, t, z_active, fade)


def draw_active_border(fr, quad, t, a):
    (tlx, tly), (trx, try_), (brx, bry), (blx, bly) = quad
    # The 5 fps stutter: a soft tick on every new frame.
    since = (t * media.FRAME_FPS) % 1 / media.FRAME_FPS if t < T["freeze"] else 1.0
    tick = math.exp(-since * 18) * smooth(lin(t, T["loose"], T["loose"] + 0.3))
    x_draw = ease_io(lin(t, 5.0, 5.9))
    y_draw = ease_io(lin(t, 5.4, 6.3))
    rest = smooth(lin(t, 5.8, 6.6))
    if x_draw > 0:
        fr.line(blx, bly, lerp(blx, brx, x_draw), lerp(bly, bry, x_draw), "x", 3.2, a, glow=0.9)
    if y_draw > 0:
        fr.line(blx, bly, lerp(blx, tlx, y_draw), lerp(bly, tly, y_draw), "y", 3.2, a, glow=0.9)
    fr.poly([tlx, trx, brx], [tly, try_, bry], "ink", 1.4, a * (0.35 * rest + 0.5 * tick), glow=0.4 * tick)


def draw_slice_plane(fr, cam, t, z, fade):
    a, b = T["sweep"]
    alpha = env(t, a - 0.5, b + 0.6, 0.5, 0.6) * fade
    if alpha <= 0:
        return
    xs, ys, _, ok = project(cam, sheet_corners(z, 1.07))
    if not ok:
        return
    path = skia.Path()
    path.addPoly([skia.Point(float(x), float(y)) for x, y in zip(xs, ys)], True)
    fr.path_fill(path, "w", 0.06 * alpha)
    fr.path_stroke(path, "w", 2.6, alpha, glow=1.1)


# ------------------------------------------------------------------ act 4: the floor plane and axes


@lru_cache(maxsize=1)
def grid_segments():
    """Floor grid as short segments (start, end, distance from centre)."""
    segs = []
    ticks = np.arange(-7.0, 7.01, 0.5)
    for a in ticks:
        for b0 in ticks[:-1]:
            b1 = b0 + 0.5
            for p, q in (((a, b0), (a, b1)), ((b0, a), (b1, a))):
                mid = math.hypot((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                segs.append(((p[0], FLOOR, p[1]), (q[0], FLOOR, q[1]), mid))
    starts = np.array([s[0] for s in segs])
    ends = np.array([s[1] for s in segs])
    dist = np.array([s[2] for s in segs])
    major = np.array([abs(s[0][0]) % 2 < 1e-6 and s[0][0] == s[1][0] or abs(s[0][2]) % 2 < 1e-6 and s[0][2] == s[1][2] for s in segs])
    return starts, ends, dist, major


def draw_grid(fr, cam, t):
    a, b = T["grid"]
    if t < a:
        return
    radius = 9.0 * ease_out(lin(t, a, b + 0.6))
    starts, ends, dist, major = grid_segments()
    x0, y0, z0 = cam.project(starts)
    x1, y1, z1 = cam.project(ends)
    visible = (z0 > 0.2) & (z1 > 0.2) & (dist < radius + 1.0)
    edge = np.clip((radius - dist) / 1.2, 0, 1)
    fog = np.clip(1.15 - dist / 7.5, 0, 1)
    for k in np.flatnonzero(visible):
        alpha = edge[k] * fog[k] * (0.7 if major[k] else 0.38)
        if alpha > 0.01:
            fr.line(x0[k], y0[k], x1[k], y1[k], "#3A4A63", 1.3 if major[k] else 1.0, alpha)


def _arrow_head(fr, x0, y0, x1, y1, color, alpha, size=16):
    ang = math.atan2(y1 - y0, x1 - x0)
    pts = [(x1, y1)] + [(x1 - size * math.cos(ang + s * 0.42), y1 - size * math.sin(ang + s * 0.42)) for s in (1, -1)]
    path = skia.Path()
    path.addPoly([skia.Point(float(x), float(y)) for x, y in pts], True)
    fr.path_fill(path, color, alpha, glow=0.5)


def axis_origin(t: float) -> np.ndarray:
    return lerp(AXIS_O, AXIS_O_CUBE, ease_io(lin(t, *T["cube"])))


def draw_axes(fr, cam, t):
    origin = axis_origin(t)
    m = ease_io(lin(t, *T["cube"]))
    axes = (
        ("x", np.array([lerp(4.7, 6.6, m), 0, 0]), TOKENS["x"], 13.1),
        ("y", np.array([0, lerp(3.4, 4.0, m), 0]), TOKENS["y"], 13.5),
        ("t", np.array([0, 0, lerp(5.6, 4.6, m)]), edge_color(2, t), 13.9),
    )
    for name, vec, color, start in axes:
        u = ease_io(lin(t, start, start + 0.9))
        if u <= 0:
            continue
        tip = origin + vec * u
        xs, ys, _, ok = project(cam, np.array([origin, tip]))
        if not ok:
            continue
        fr.line(xs[0], ys[0], xs[1], ys[1], color, 2.4, 0.95, glow=0.6)
        _arrow_head(fr, xs[0], ys[0], xs[1], ys[1], color, 0.95)
        label_at = origin + vec * (u + 0.07)
        la = smooth(lin(t, start + 0.6, start + 1.1))
        if name == "t":
            swap = smooth(lin(t, 15.4, 16.4))
            text3d(fr, cam, "t", label_at, 0.42, color, la * (1 - swap), 500, "italic")
            text3d(fr, cam, "z", label_at, 0.42, color, la * swap, 500, "italic")
        else:
            text3d(fr, cam, name, label_at, 0.42, color, la, 500, "italic")
    # The fourth direction has nowhere left to point: a dashed blue arrow off at an "impossible" angle.
    u = ease_io(lin(t, 19.4, 20.4))
    if u > 0:
        direction = np.array([0.48, 0.78, -0.42])
        tip = origin + direction / np.linalg.norm(direction) * 3.0 * u
        xs, ys, _, ok = project(cam, np.array([origin, tip]))
        if ok:
            n = 14
            for k in range(n):
                if k % 2:
                    continue
                f0, f1 = k / n, (k + 1) / n
                fr.line(lerp(xs[0], xs[1], f0), lerp(ys[0], ys[1], f0), lerp(xs[0], xs[1], f1),
                        lerp(ys[0], ys[1], f1), "w", 2.6, 0.95, glow=0.8)
            _arrow_head(fr, xs[0], ys[0], xs[1], ys[1], TOKENS["w"], 0.95)
            label_at = origin + direction / np.linalg.norm(direction) * 3.0 * (u + 0.09)
            text3d(fr, cam, "w", label_at, 0.46, TOKENS["w"], smooth(lin(t, 20.0, 20.6)), 500, "italic")


# ------------------------------------------------------------------ act 5: light pool and shadows


def draw_light_pool(fr, cam, t):
    """A soft pool of light on the floor: a radial gradient mapped onto the floor plane by homography."""
    a = smooth(lin(t, *T["light"]))
    if a <= 0:
        return
    cx, cz, r = 0.15, 0.1, 4.6
    corners = np.array([[cx - r, FLOOR, cz + r], [cx + r, FLOOR, cz + r], [cx + r, FLOOR, cz - r], [cx - r, FLOOR, cz - r]])
    xs, ys, _, ok = project(cam, corners)
    if not ok:
        return
    shader = skia.GradientShader.MakeRadial(
        skia.Point(r, r), r, [col("light", 0.42 * a), col("light", 0.15 * a), col("light", 0.0)], [0.0, 0.45, 1.0]
    )
    fr.c.save()
    fr.c.concat(quad_matrix(2 * r, 2 * r, list(zip(xs, ys))))
    fr.c.drawRect(skia.Rect.MakeWH(2 * r, 2 * r), skia.Paint(AntiAlias=True, Shader=shader))
    fr.c.restore()


def _shadow(points3: np.ndarray) -> np.ndarray:
    k = (FLOOR - LIGHT[1]) / (points3[:, 1] - LIGHT[1])
    return LIGHT + (points3 - LIGHT) * k[:, None]


def _hull(points2: np.ndarray) -> np.ndarray:
    pts = sorted(map(tuple, points2))
    if len(pts) < 3:
        return np.array(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.array(lower[:-1] + upper[:-1])


def draw_shadow(fr, cam, t, world):
    a = smooth(lin(t, T["light"][0] + 0.3, T["light"][1] + 0.3))
    if a <= 0:
        return
    shadow = _shadow(world)
    hull = _hull(shadow[:, [0, 2]])
    ring = np.stack([hull[:, 0], np.full(len(hull), FLOOR), hull[:, 1]], 1)
    xs, ys, _, ok = project(cam, ring)
    if ok:
        path = skia.Path()
        path.addPoly([skia.Point(float(x), float(y)) for x, y in zip(xs, ys)], True)
        fr.path_fill(path, "bg", 0.62 * a)
    sx, sy, _, ok = project(cam, shadow)
    if ok:
        hw = model(t)[0][3]
        for i, j, axis in EDGES:
            if axis == 3 and hw < 1e-3:
                continue
            fr.line(sx[i], sy[i], sx[j], sy[j], "ink", 1.1, 0.22 * a)


# ------------------------------------------------------------------ acts 5-6: box edges, tesseract, w-slices


def edges_alpha(t: float) -> float:
    return 0.30 * smooth(lin(t, 8.6, 10.0)) + 0.70 * smooth(lin(t, 15.2, 16.6))


def draw_edges(fr, cam, t, world):
    alpha = edges_alpha(t)
    if alpha <= 0.003:
        return
    hw = model(t)[0][3]
    xs, ys, depth, ok = project(cam, world)
    if not ok:
        return
    near = (depth.max() - depth) / max(1e-6, depth.max() - depth.min())
    lit = smooth(lin(t, 15.2, 16.6))
    for i, j, axis in sorted(EDGES, key=lambda e: -(depth[e[0]] + depth[e[1]])):
        if axis == 3:
            if hw < 1e-3:
                continue
            a = alpha * min(1.0, hw / CUBE * 3)
        else:
            a = alpha
        k = (near[i] + near[j]) / 2
        fr.line(xs[i], ys[i], xs[j], ys[j], edge_color(axis, t), 1.6 + 1.6 * k, a * (0.55 + 0.45 * k),
                glow=0.75 * lit)
    for i in np.argsort(-depth):
        if lit > 0:
            fr.glow_dot(xs[i], ys[i], 3.0 + 2.5 * near[i], "ink", lit * (0.5 + 0.5 * near[i]), 0.6)


def draw_w_slices(fr, cam, t, R, centre, half):
    start = T["slices"]
    show = smooth(lin(t, start, start + 0.8))
    if show <= 0:
        return
    n = 7
    tick = int((t - start) * 8)
    hw = half[3]
    quads = []
    for k in range(n):
        born = start + 0.16 * k
        a = smooth(lin(t, born, born + 0.4)) * show
        if a <= 0:
            continue
        w = (-1 + 2 * k / (n - 1)) * hw
        corners4 = np.array([[-CUBE, CUBE * 9 / 16, 0, w], [CUBE, CUBE * 9 / 16, 0, w],
                             [CUBE, -CUBE * 9 / 16, 0, w], [-CUBE, -CUBE * 9 / 16, 0, w]])
        xs, ys, depth, ok = project(cam, to_world(corners4, t, R, centre))
        if not ok:
            continue
        age = n - 1 - k
        index = (HOLD_FRAME + tick - 3 * age - 1) % media.FRAME_COUNT + 1
        quads.append((age == 0, float(depth.mean()), list(zip(xs, ys)), index, a * (1.0 if age == 0 else 0.5 - 0.06 * age)))
    for newest, _, quad, index, a in sorted(quads, key=lambda q: (q[0], -q[1])):
        fr.image_quad(media.frame(index) if newest else media.thumb(index), quad, a)
        xs, ys = zip(*quad)
        fr.poly(xs, ys, "w", 2.4 if newest else 1.2, a * (1.0 if newest else 0.6), glow=0.7 if newest else 0.0,
                close=True)


# ------------------------------------------------------------------ frame function


def draw(t, size):
    fr = Frame(size)
    draw_footage(fr, t)
    if t >= T["loose"]:
        cam = camera(t)
        half, R, centre = model(t)
        world = to_world(V4 * half, t, R, centre)
        draw_grid(fr, cam, t)
        draw_light_pool(fr, cam, t)
        draw_shadow(fr, cam, t, world)
        draw_axes(fr, cam, t)
        draw_sheets(fr, cam, t)
        draw_edges(fr, cam, t, world)
        draw_w_slices(fr, cam, t, R, centre, half)
    fr.letterbox(1 - ease_io(lin(t, 4.7, 5.8)))
    fr.vignette(0.5)
    fr.grain(t, 0.045)
    return fr.finish()


def build(audio: bool = False):
    from faceless_champ import FunctionSource, Scene

    key = f"s01:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=DURATION, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(DURATION)
    return scene


STILLS = [1.0, 3.5, 4.8, 5.8, 7.0, 8.4, 9.6, 11.0, 12.8, 13.8, 15.2, 16.4, 17.8, 19.8, 21.0, 22.4, 23.6, 24.8]
