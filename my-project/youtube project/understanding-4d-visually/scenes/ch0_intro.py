"""CHAPTER 0 - COLD OPEN (S01-S03), 00:00.000 - 00:49.560 (cue #142 "So").

S01  Time is a direction      cheetah footage (speed ramp on "slow it down") -> 5 fps stepping -> the frame
                              comes loose; x / y edges trace on "flat" -> frames stack into a block of time,
                              t axis on "time" -> the blue slice plane plays the clip -> "solid block".
S02  The shadow of a cube     block -> cube, a light opens, its real point-light shadow on the floor ->
                              "3D -> 2D" -> the world dims and a dashed w arrow asks the question ->
                              extrude along w on "fourth dimension" -> ZW spin, cheetah on 7 w-slices.
S03  The promise              coordinates bloom on "understand it" -> vector + matrix plaques ->
                              four teasers: count corners / measure diagonal / slice / rotate ->
                              title lockup, light sweep, zoom-blur exit.

Ported from scenes/s01_cinematic.py (the 25 s silent prototype): same geometry and camera spline,
every beat re-timed to word cues. One continuous camera, no cuts. All in one FunctionSource.
"""

from __future__ import annotations

import itertools
import math
from functools import lru_cache
from pathlib import Path

import media
import numpy as np
import skia
from components import hud
from components import tesseract as T4
from components.cards import card_space
from components.matrix_plaque import draw_matrix, zw_rotation_cells
from components.slice_plane import draw_plane
from components.vector_slot import Slot, draw_vector
from cues import AUDIO, cue
from fx import (
    Frame,
    card_quad,
    chroma_kick,
    col,
    ease_io,
    ease_out,
    env,
    lerp,
    lin,
    mix,
    motion_blur,
    pulse,
    quad_matrix,
    smooth,
    text_path,
)
from space import Spline, orbit, rot_x, rot_y, text3d
from theme import THEME, TOKENS, H, W

START = 0.0
END = cue(142)  # 49.56 "So first, what actually is a dimension?"

C = {
    i: cue(i)
    for i in (
        9,
        14,
        16,
        21,
        23,
        25,
        31,
        34,
        37,
        39,
        44,
        50,
        51,
        55,
        61,
        66,
        75,
        76,
        80,
        86,
        89,
        93,
        106,
        108,
        111,
        114,
        118,
        122,
        124,
        125,
        127,
        128,
        131,
        138,
        141,
    )
}

T = {
    "slow": C[9],  # 2.99 "slow it down": speed ramp
    "strange": C[14],  # 4.24 a blue scanline crosses the footage
    "loose": C[16],  # 6.04 "Every video": 5 fps stepping, the frame comes loose
    "flat": C[23],  # 8.09 x / y edges trace
    "freeze": C[25],  # 9.36 "Stack": the stack unfolds
    "time": C[31],  # 11.36 t axis
    "direction": C[34],  # 12.24 arrowhead flare
    "point": C[37],  # 13.29 glint down the axis
    "playing": C[39],  # 14.08 slice plane enters
    "sweep": (C[44] - 0.6, C[51] - 0.2),  # "sliding" ... "block": the plane plays the clip
    "solid": C[50],  # 17.50 "solid block": sheets fuse
    "cube": (C[55] - 0.4, C[55] + 1.0),  # "cube" 19.22: block -> cube
    "light": (C[55] + 0.1, C[55] + 1.2),
    "flat_shadow": C[61],  # 21.36
    "understand": C[66],  # 23.08 shadow outline traces
    "pill": (C[75] - 0.1, cue(82) + 0.2),  # "two-dimensional shadow" -> until "An"
    "question": C[80],  # 28.53 "three-dimensional one?"
    "w": (C[86] - 0.15, C[86] + 1.25),  # "fourth" 31.41: extrude along w
    "spin": C[89] - 0.1,  # 32.98 "this is what its shadow looks like"
    "slices": C[89] + 0.3,
    "slices_out": C[111],  # 38.92 coordinates replace the footage slices
    "coords": C[111],
    "vector": C[114],  # 40.53
    "matrix": C[118],  # 41.72
    "count": C[122],  # 42.90
    "measure": C[125],  # 43.70
    "slice": C[128],  # 45.28
    "rotate": C[131],  # 46.19
    "title": C[138],  # 47.94 "impossible"
    "world": C[141],  # 49.10
}

# ------------------------------------------------------------------ world (units; y up, z away from camera)
SHEET_W, SHEET_H = 3.2, 1.8
BLOCK_L = 4.4
FLOOR = -1.5
FOCAL = 1500.0
SHEETS = tuple(range(1, media.FRAME_COUNT + 1, 2))
AXIS_O = np.array([-1.6, FLOOR, -BLOCK_L / 2])  # the block's front-left corner
AXIS_O_CUBE = np.array([-3.4, FLOOR, -1.4])  # moved clear of the cube so no axis cuts through it
LIGHT = np.array([0.9, 6.5, 0.6])
D4 = 5.0
CUBE = 1.25
RAMP = 0.35  # footage speed after "slow it down"

V4 = np.array(list(itertools.product((-1, 1), repeat=4)), float)  # same vertex order as components.tesseract
EDGES = T4.EDGES


def clip_time(t: float) -> float:
    """Footage clock: real time, then RAMP after 'slow it down', then real time again while it steps at 5 fps."""
    if t <= T["slow"]:
        return t
    ramp_end = T["slow"] + (T["loose"] - T["slow"]) * RAMP
    if t <= T["loose"]:
        return T["slow"] + (t - T["slow"]) * RAMP
    return ramp_end + (t - T["loose"])


HOLD_FRAME = media.frame_at(clip_time(T["freeze"]))  # the frame on screen when the stack unfolds


def z_of(frame: float) -> float:
    return -BLOCK_L / 2 + BLOCK_L * (frame - 1) / (media.FRAME_COUNT - 1)


# ------------------------------------------------------------------ camera: one Hermite spline, no cuts

_D0 = FOCAL * SHEET_W / (W * 1.06)  # matches the end of the 2D push-in exactly
_HZ = z_of(HOLD_FRAME)
CAMERA = Spline(
    [  # time, target xyz, dist, elev, azim
        (T["loose"], (0, 0, _HZ), _D0, 0.0, 0.0),
        (T["loose"] + 1.9, (0, 0, _HZ), 3.9, 0.10, -0.32),
        (T["freeze"] + 0.9, (0, 0, _HZ * 0.5), 6.0, 0.20, -0.62),
        (T["time"] + 1.2, (0, 0, 0.2), 9.0, 0.26, -0.86),
        (T["playing"] + 1.5, (0, -0.35, 0.2), 10.2, 0.36, -0.95),
        (T["solid"] + 0.8, (0, -0.25, 0), 10.4, 0.44, -0.70),
        (T["flat_shadow"], (0, -0.1, 0), 10.0, 0.42, -0.45),
        (T["understand"] + 2.0, (0, -0.2, 0), 10.6, 0.46, -0.25),
        (T["question"], (0, 0.0, 0), 11.2, 0.40, -0.15),
        (T["w"][0], (0, 0.05, 0), 9.8, 0.36, -0.30),
        (T["slices"] + 2.0, (0, 0.2, 0), 9.4, 0.26, 0.0),
        (T["vector"], (0, 0.45, 0), 11.0, 0.22, 0.22),
        (T["rotate"], (0, 0.45, 0), 10.6, 0.20, 0.50),
        (T["title"] + 0.6, (0, 0.45, 0), 12.5, 0.16, 0.62),
        (END, (0, 0.45, 0), 12.0, 0.15, 0.66),
    ]
)


def camera(t: float):
    v = CAMERA(t)
    return orbit(v[:3], v[3], v[4], v[5], focal=FOCAL)


def project(cam, pts):
    """Nx3 world points -> (xs, ys, depth, all-in-front)."""
    xs, ys, z = cam.project(pts)
    return xs, ys, z, bool(np.all(z > 0.08))


# ------------------------------------------------------------------ the 4D model (box -> cube -> tesseract)


def theta_zw(t: float) -> float:
    if t <= T["spin"]:
        return 0.0
    base = 0.5 * (t - T["spin"]) * smooth(lin(t, T["spin"], T["spin"] + 1.4))
    return base + math.pi * ease_io(lin(t, T["rotate"] - 0.1, T["rotate"] + 1.15))  # the "rotate it" teaser


def model(t: float):
    """Half extents (4), 3D rotation, centre."""
    u = ease_io(lin(t, *T["cube"]))
    half3 = lerp(np.array([SHEET_W / 2, SHEET_H / 2, BLOCK_L / 2]), np.full(3, CUBE), u)
    hw = CUBE * ease_io(lin(t, *T["w"]))
    turn = ease_io(lin(t, T["cube"][1] - 0.4, T["understand"] + 1.6))
    settle = ease_io(lin(t, T["w"][0] - 0.6, T["spin"] + 1.4))
    t0 = T["cube"][1] - 0.4
    yaw = 0.95 * turn - 0.80 * settle + 0.025 * max(0.0, t - t0)
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


def world_at(t: float) -> np.ndarray:
    half, R, centre = model(t)
    return to_world(V4 * half, t, R, centre)


def edge_color(axis: int, t: float) -> str:
    if axis == 2:  # the time direction becomes z when the block becomes a cube
        return mix(TOKENS["w"], TOKENS["z"], lin(t, T["cube"][0] - 0.1, T["cube"][0] + 0.8))
    return TOKENS["xyzw"[axis]]


# ------------------------------------------------------------------ S01A: footage


def card_u(t: float) -> float:
    """0: the footage floats as a lit 3D card; 1: it fills the frame for the hand-off to the stack."""
    return ease_io(lin(t, T["loose"] - 1.35, T["loose"] - 0.05))


def footage_quad(t: float):
    u = card_u(t)
    k = t / T["loose"]
    angle = lerp(-0.16 + 0.07 * k, 0.0, u)  # a slow yaw: the card turns toward us
    scale = lerp(0.60 + 0.03 * k, 1.06, u)
    return card_quad(960.0, lerp(470.0, 540.0, u), W, H, angle, scale), u


def _quad_path(quad):
    p = skia.Path()
    p.addPoly([skia.Point(*q) for q in quad], True)
    return p


def draw_backdrop(fr, t, quad, a):
    """Lifted stage for the card: a cool radial ground, ambient light spilled from the footage, a feathered shadow."""
    if a <= 0.003:
        return
    shader = skia.GradientShader.MakeRadial(
        skia.Point(960, 600), 1150, [col("#273244", a), col("#0D121B", a), col("#000000", a)], [0.0, 0.5, 1.0]
    )
    fr.c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=shader))
    # ambient light: the footage itself, hugely blurred, glowing around the card
    c = clip_time(t)
    hud.dot_grid(
        fr,
        orbit((0.0, 0.0, 0.0), 10.0, 0.16, 0.0, focal=FOCAL, center=(960.0, 470.0)),
        -2.0,
        extent=9.0,
        spacing=0.55,
        alpha=0.16 * a,
    )
    amb = skia.Paint(Alphaf=0.6 * a, ImageFilter=skia.ImageFilters.Blur(90, 90), BlendMode=skia.BlendMode.kPlus)
    fr.c.saveLayer(None, amb)
    fr.image_quad(media.opener(int(c * media.OPENER_FPS) + 1), quad, 1.0)
    fr.c.restore()
    # feathered shadow: a wide soft drop plus a tighter contact shadow
    bottom = max(q[1] for q in quad)
    for dy, sigma, alpha, grow in ((60, 60, 0.9, 1.04), (18, 16, 0.65, 1.0)):
        sq = [(960 + (x - 960) * grow, y + dy) for x, y in quad]
        paint = skia.Paint(
            AntiAlias=True,
            Color4f=col("#000000", alpha * a),
            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma),
        )
        fr.c.drawPath(_quad_path(sq), paint)
    # a faint floor sheen under the card
    sheen = skia.GradientShader.MakeRadial(
        skia.Point(960, bottom + 70), 700, [col("light", 0.05 * a), col("light", 0.0)]
    )
    fr.c.save()
    fr.c.scale(1.0, 0.18)
    fr.c.drawCircle(960, (bottom + 70) / 0.18, 700, skia.Paint(AntiAlias=True, Shader=sheen))
    fr.c.restore()


def draw_reflection(fr, t, quad, img, a):
    """The card mirrored in a dark glossy floor, fading out within ~170 px."""
    if a <= 0.003:
        return
    tl, tr, br, bl = (np.array(q) for q in quad)
    rq = [tuple(bl), tuple(br), tuple(br + (br - tr)), tuple(bl + (bl - tl))]
    y0 = max(bl[1], br[1])
    fr.c.saveLayer(None, None)
    fr.image_quad(img, rq, 0.24 * a)
    fade = skia.GradientShader.MakeLinear(
        [skia.Point(0, y0), skia.Point(0, y0 + 170)], [col("#ffffff", 1.0), col("#ffffff", 0.0)]
    )
    fr.c.drawRect(skia.Rect.MakeLTRB(0, y0 - 4, W, H), skia.Paint(Shader=fade, BlendMode=skia.BlendMode.kDstIn))
    fr.c.restore()


def draw_footage(fr, t):
    if t >= T["loose"]:
        return
    f = clip_time(t) * media.OPENER_FPS
    i, frac = int(f) + 1, f - int(f)
    a = smooth(lin(t, 0.0, 1.2))
    quad, u = footage_quad(t)
    stage = a * (1 - u)
    img = media.opener(i)
    draw_backdrop(fr, t, quad, stage)
    draw_reflection(fr, t, quad, img, stage)
    inner = lerp(1.0 + 0.03 * t / T["loose"], 1.0, u)
    with card_space(fr, quad, W, H):
        r = lerp(30.0, 0.0, u)
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeWH(W, H), r, r)
        fr.c.save()
        fr.c.clipRRect(rr, doAntiAlias=True)
        fr.image_fill(img, inner, a)
        if t > T["slow"] and frac > 0.02:  # frame-blend the slow motion so it glides instead of judders
            fr.image_fill(media.opener(i + 1), inner, a * frac)
        uu = lin(t, T["strange"] - 0.05, T["strange"] + 0.85)  # the first hint of w: a thin blue scanline
        if 0 < uu < 1:
            y = H * ease_io(uu)
            fr.line(0, y, W, y, "w", 2.2, 0.8 * math.sin(math.pi * uu), glow=1.0)
        fr.c.restore()
        edge = skia.Path()
        edge.addRRect(rr)
        fr.path_stroke(edge, "ink", 2.0, 0.22 * stage)
        fr.light_sweep(edge, lin(t, 0.6, 2.2), strength=0.22 * stage, width=0.10)


# ------------------------------------------------------------------ S01B-D: sheets and the block of time


def sheet_corners(z: float, scale: float = 1.0) -> np.ndarray:
    hw, hh = SHEET_W / 2 * scale, SHEET_H / 2 * scale
    return np.array([[-hw, hh, z], [hw, hh, z], [hw, -hh, z], [-hw, -hh, z]])


def active_frame(t: float) -> float:
    if t < T["freeze"]:
        return media.frame_at(clip_time(t))  # the clip keeps playing, stepped at 5 fps
    a, b = T["sweep"]
    return HOLD_FRAME + (media.FRAME_COUNT - HOLD_FRAME) * lin(t, a, b)


def sheets_alpha(t: float) -> float:
    return 1 - smooth(lin(t, T["cube"][0] - 0.7, T["cube"][0] + 0.5))


def draw_sheets(fr, cam, t):
    if t < T["loose"] or sheets_alpha(t) <= 0:
        return
    fade = sheets_alpha(t)
    fuse = smooth(lin(t, T["solid"] - 0.1, T["solid"] + 0.6))  # "solid block": the stack fuses into glass
    hold_z = z_of(HOLD_FRAME)
    items = []  # (depth, kind, payload)
    for j in SHEETS:
        appear = T["freeze"] + 0.1 + 0.045 * abs(j - HOLD_FRAME) / 2
        a = smooth(lin(t, appear, appear + 0.45)) * fade * (1 - 0.55 * fuse)
        if a <= 0:
            continue
        z = lerp(hold_z, z_of(j), ease_out(lin(t, appear, appear + 0.7)))
        xs, ys, depth, ok = project(cam, sheet_corners(z))
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
    a, b = T["sweep"]
    plane_a = env(t, T["playing"], b + 0.6, 0.5, 0.6) * fade
    if plane_a > 0:
        draw_plane(fr, cam, sheet_corners(z_active, 1.07), t, plane_a, shimmer=0.0)


def draw_active_border(fr, quad, t, a):
    (tlx, tly), (trx, try_), (brx, bry), (blx, bly) = quad
    # The 5 fps stutter: a soft tick on every new frame.
    since = (clip_time(t) * media.FRAME_FPS) % 1 / media.FRAME_FPS if t < T["freeze"] else 1.0
    tick = math.exp(-since * 18) * smooth(lin(t, T["loose"], T["loose"] + 0.3))
    x_draw = ease_io(lin(t, T["flat"] - 0.2, T["flat"] + 0.5))
    y_draw = ease_io(lin(t, T["flat"] + 0.1, T["flat"] + 0.8))
    rest = smooth(lin(t, T["flat"] + 0.6, T["flat"] + 1.3))
    if x_draw > 0:
        fr.line(blx, bly, lerp(blx, brx, x_draw), lerp(bly, bry, x_draw), "x", 3.2, a, glow=0.9)
    if y_draw > 0:
        fr.line(blx, bly, lerp(blx, tlx, y_draw), lerp(bly, tly, y_draw), "y", 3.2, a, glow=0.9)
    fr.poly([tlx, trx, brx], [tly, try_, bry], "ink", 1.4, a * (0.35 * rest + 0.5 * tick), glow=0.4 * tick)


# ------------------------------------------------------------------ the floor and axes


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
    major = np.array(
        [
            (abs(s[0][0]) % 2 < 1e-6 and s[0][0] == s[1][0]) or (abs(s[0][2]) % 2 < 1e-6 and s[0][2] == s[1][2])
            for s in segs
        ]
    )
    return starts, ends, dist, major


def draw_grid(fr, cam, t):
    a = T["time"] + 1.0
    if t < a:
        return
    radius = 9.0 * ease_out(lin(t, a, a + 3.0))
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


def axis_origin(t: float) -> np.ndarray:
    return lerp(AXIS_O, AXIS_O_CUBE, ease_io(lin(t, *T["cube"])))


def axes_alpha(t):
    """The axes step aside once the coordinates take over (S03)."""
    return 1 - smooth(lin(t, T["coords"] - 0.3, T["coords"] + 0.5))


def draw_axes(fr, cam, t):
    fade = axes_alpha(t)
    if fade <= 0.003:
        return
    origin = axis_origin(t)
    m = ease_io(lin(t, *T["cube"]))
    axes = (
        ("x", np.array([lerp(4.7, 6.6, m), 0, 0]), TOKENS["x"], T["time"] - 0.75),
        ("y", np.array([0, lerp(3.4, 4.0, m), 0]), TOKENS["y"], T["time"] - 0.45),
        ("t", np.array([0, 0, lerp(5.6, 4.6, m)]), edge_color(2, t), T["time"] - 0.1),
    )
    for name, vec, color, start in axes:
        u = ease_io(lin(t, start, start + 0.9))
        if u <= 0:
            continue
        tip = origin + vec * u
        xs, ys, _, ok = project(cam, np.array([origin, tip]))
        if not ok:
            continue
        flare = pulse(t, T["direction"] - 0.05, 0.6) if name == "t" else 0.0
        fr.line(xs[0], ys[0], xs[1], ys[1], color, 2.4 + 1.2 * flare, 0.95 * fade, glow=0.6 + 0.8 * flare)
        hud.arrow_head(fr, xs[0], ys[0], xs[1], ys[1], color, 0.95 * fade, 16 + 10 * flare)
        if name == "t" and flare > 0:
            fr.glow_dot(xs[1], ys[1], 5 + 6 * flare, color, flare, 1.4)
        if name == "t":  # "point to": a glint runs down the time axis
            g = lin(t, T["point"] - 0.1, T["point"] + 0.7)
            if 0 < g < 1:
                fr.glow_dot(lerp(xs[0], xs[1], g), lerp(ys[0], ys[1], g), 4.0, "#ffffff", math.sin(math.pi * g), 1.6)
        label_at = origin + vec * (u + 0.07)
        la = smooth(lin(t, start + 0.6, start + 1.1)) * fade
        if name == "t":
            swap = smooth(lin(t, T["cube"][0] - 0.1, T["cube"][0] + 0.8))
            text3d(fr, cam, "t", label_at, 0.42, color, la * (1 - swap), 500, "italic")
            text3d(fr, cam, "z", label_at, 0.42, color, la * swap, 500, "italic")
        else:
            text3d(fr, cam, name, label_at, 0.42, color, la, 500, "italic")


def draw_w_arrow(fr, cam, t):
    """The fourth direction has nowhere left to point: a dashed blue arrow off at an 'impossible' angle."""
    u = ease_io(lin(t, T["question"] - 0.15, T["question"] + 0.85))
    fade = axes_alpha(t)
    if u <= 0 or fade <= 0.003:
        return
    origin = axis_origin(t)
    direction = np.array([0.48, 0.78, -0.42])
    direction /= np.linalg.norm(direction)
    tip = origin + direction * 3.0 * u
    xs, ys, _, ok = project(cam, np.array([origin, tip]))
    if not ok:
        return
    shimmer = 0.85 + 0.15 * math.sin(t * 23.0)
    hud.arrow(fr, xs[0], ys[0], xs[1], ys[1], "w", 2.8, 0.95 * shimmer * fade, glow=0.9, dashed=True)
    label_at = origin + direction * 3.0 * (u + 0.09)
    text3d(
        fr,
        cam,
        "w",
        label_at,
        0.5,
        TOKENS["w"],
        smooth(lin(t, T["question"] + 0.4, T["question"] + 1.0)) * fade,
        500,
        "italic",
        glow=0.4,
    )


# ------------------------------------------------------------------ S02: light pool, glint and shadows


def light_alpha(t):
    return smooth(lin(t, *T["light"])) * (1 - 0.6 * smooth(lin(t, T["title"] - 0.2, T["title"] + 0.8)))


def draw_light_pool(fr, cam, t):
    """A soft pool of light on the floor: a radial gradient mapped onto the floor plane by homography."""
    a = light_alpha(t)
    if a <= 0:
        return
    cx, cz, r = 0.15, 0.1, 4.6
    corners = np.array(
        [[cx - r, FLOOR, cz + r], [cx + r, FLOOR, cz + r], [cx + r, FLOOR, cz - r], [cx - r, FLOOR, cz - r]]
    )
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


def draw_light_source(fr, cam, t):
    """Volumetric cone from the light to the floor pool, and a lens glint at the source."""
    a = light_alpha(t)
    if a <= 0:
        return
    pts = np.array([LIGHT, [-2.4, FLOOR, 0.1], [2.7, FLOOR, 0.1]])
    xs, ys, _, ok = project(cam, pts)
    if not ok:
        return
    fr.light_cone((xs[0], ys[0]), (xs[1], ys[1]), (xs[2], ys[2]), alpha=0.16 * a)
    if -80 < xs[0] < W + 80 and -80 < ys[0] < H + 80:
        fr.glint(float(xs[0]), float(ys[0]), 56.0, a * (0.85 + 0.15 * math.sin(t * 3.1)))


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
    a = smooth(lin(t, T["light"][0] + 0.3, T["light"][1] + 0.3)) * (
        1 - 0.5 * smooth(lin(t, T["title"], T["title"] + 0.8))
    )
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
        # "flat shadow": the silhouette breathes once; "understand it": its outline traces in ink.
        breathe = pulse(t, T["flat_shadow"] - 0.1, 0.9)
        trace = env(t, T["understand"] - 0.1, T["question"] - 0.4, 0.5, 0.6)
        if breathe + trace > 0.01:
            fr.path_stroke(path, "ink", 1.6 + 1.2 * breathe, a * max(0.55 * breathe, 0.75 * trace), glow=0.5)
    sx, sy, _, ok = project(cam, shadow)
    if ok:
        hw = model(t)[0][3]
        for i, j, axis in EDGES:
            if axis == 3 and hw < 1e-3:
                continue
            fr.line(sx[i], sy[i], sx[j], sy[j], "ink", 1.1, 0.22 * a)


def draw_pill(fr, cam, t):
    a = env(t, *T["pill"], 0.4, 0.5)
    if a <= 0:
        return
    xs, ys, _, ok = project(cam, np.array([[3.3, FLOOR, -1.6]]))
    if ok:
        hud.pill(fr, float(xs[0]), float(ys[0]), "3D → 2D", "ink", a, size=26)


# ------------------------------------------------------------------ S02C: edges, tesseract, w-slices


def edges_alpha(t: float) -> float:
    return 0.30 * smooth(lin(t, T["freeze"] + 1.2, T["freeze"] + 2.6)) + 0.70 * smooth(
        lin(t, T["solid"] - 0.2, T["solid"] + 0.9)
    )


def draw_edges(fr, cam, t, world, alpha=1.0):
    alpha *= edges_alpha(t)
    if alpha <= 0.003:
        return
    hw = model(t)[0][3]
    xs, ys, depth, ok = project(cam, world)
    if not ok:
        return
    near = (depth.max() - depth) / max(1e-6, depth.max() - depth.min())
    lit = smooth(lin(t, T["solid"] - 0.2, T["solid"] + 0.9))
    for i, j, axis in sorted(EDGES, key=lambda e: -(depth[e[0]] + depth[e[1]])):
        if axis == 3:
            if hw < 1e-3:
                continue
            a = alpha * min(1.0, hw / CUBE * 3)
        else:
            a = alpha
        k = (near[i] + near[j]) / 2
        fr.line(xs[i], ys[i], xs[j], ys[j], edge_color(axis, t), 1.6 + 1.6 * k, a * (0.55 + 0.45 * k), glow=0.75 * lit)
    pops = vertex_pops(t)
    for i in np.argsort(-depth):
        if lit > 0:
            p = pops[i]
            fr.glow_dot(
                xs[i],
                ys[i],
                3.0 + 2.5 * near[i] + 6.0 * p,
                "ink" if p < 0.01 else "#ffffff",
                alpha * lit * (0.5 + 0.5 * near[i]) + p,
                0.6 + 1.2 * p,
            )


def draw_w_slices(fr, cam, t, R, centre, half):
    start = T["slices"]
    show = smooth(lin(t, start, start + 0.8)) * (1 - smooth(lin(t, T["slices_out"] - 0.4, T["slices_out"] + 0.4)))
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
        corners4 = np.array(
            [
                [-CUBE, CUBE * 9 / 16, 0, w],
                [CUBE, CUBE * 9 / 16, 0, w],
                [CUBE, -CUBE * 9 / 16, 0, w],
                [-CUBE, -CUBE * 9 / 16, 0, w],
            ]
        )
        xs, ys, depth, ok = project(cam, to_world(corners4, t, R, centre))
        if not ok:
            continue
        age = n - 1 - k
        index = (HOLD_FRAME + tick - 3 * age - 1) % media.FRAME_COUNT + 1
        quads.append(
            (age == 0, float(depth.mean()), list(zip(xs, ys)), index, a * (1.0 if age == 0 else 0.5 - 0.06 * age))
        )
    for newest, _, quad, index, a in sorted(quads, key=lambda q: (q[0], -q[1])):
        fr.image_quad(media.frame(index) if newest else media.thumb(index), quad, a)
        xs, ys = zip(*quad)
        fr.poly(
            xs, ys, "w", 2.4 if newest else 1.2, a * (1.0 if newest else 0.6), glow=0.7 if newest else 0.0, close=True
        )


# ------------------------------------------------------------------ S03: the promise


def vertex_pops(t: float) -> np.ndarray:
    """'count its corners': the 16 vertices pop in sequence (0 -> 1 -> 0 bump per vertex)."""
    out = np.zeros(16)
    t0 = T["count"] - 0.15
    if t0 - 0.1 < t < t0 + 1.4:
        for i in range(16):
            out[i] = pulse(t, t0 + 0.055 * i, 0.32)
    return out


def corners_counted(t: float) -> int:
    t0 = T["count"] - 0.15
    return int(np.clip((t - t0) / 0.055 + 1, 0, 16))


def draw_coords(fr, cam, t, world):
    """'You will understand it': every vertex shows its 4-digit coordinate, digits coloured by axis."""
    a = env(t, T["coords"] - 0.1, T["count"] - 0.3, 0.6, 0.5)
    if a <= 0:
        return
    xs, ys, depth = cam.project(world)
    near = (depth.max() - depth) / max(1e-6, depth.max() - depth.min())
    for i in range(16):
        bits = T4.label(i)
        size = 22 + 10 * near[i]
        bloom = smooth(lin(t, T["coords"] + 0.03 * i, T["coords"] + 0.03 * i + 0.4))
        x0 = xs[i] + 10
        for k, ch in enumerate(bits):
            fr.text(
                ch,
                x0 + k * size * 0.62,
                ys[i] - 10,
                "sans",
                size,
                600,
                "xyzw"[k],
                a * bloom * (0.45 + 0.55 * near[i]),
                align="left",
            )


def draw_tools(fr, t):
    """'Using vectors and a little linear algebra': small, defocused plaques either side of the tesseract."""
    out = 1 - smooth(lin(t, T["title"] - 0.5, T["title"] + 0.2))
    va = smooth(lin(t, T["vector"] - 0.1, T["vector"] + 0.5)) * out
    ma = smooth(lin(t, T["matrix"] - 0.1, T["matrix"] + 0.5)) * out
    slide_v = (1 - ease_out(lin(t, T["vector"] - 0.1, T["vector"] + 0.6))) * -80
    slide_m = (1 - ease_out(lin(t, T["matrix"] - 0.1, T["matrix"] + 0.6))) * 80
    if va > 0.003:
        with fr.blurred(1.6):
            slots = [Slot(k, k, underline=1) for k in "xyzw"]
            hud.glass_card(fr, 150 + slide_v, 360, 160, 360, va * 0.85)
            draw_vector(fr, 230 + slide_v, 540, slots, 44, alpha=va * 0.9)
    if ma > 0.003:
        with fr.blurred(1.6):
            colors = {(0, 0): "x", (1, 1): "y", (2, 2): "z", (2, 3): "z", (3, 2): "w", (3, 3): "w"}
            dimz = {(r, k): 0.35 for r in range(4) for k in range(4) if (r, k) not in colors}
            draw_matrix(
                fr,
                1620 + slide_m,
                540,
                zw_rotation_cells(),
                colors,
                cell_w=72,
                cell_h=52,
                size=24,
                alpha=ma * 0.9,
                entry_alpha=dimz,
                pad=22,
                blocks=[((2, 2, 3, 3), TOKENS["z"], TOKENS["w"], ma)],
            )


def draw_teasers(fr, cam, t, world):
    # 1. count its corners
    a = env(t, T["count"] - 0.2, T["measure"] - 0.05, 0.25, 0.3)
    if a > 0:
        hud.readout(fr, 960, 110, "corners", f"{corners_counted(t):>2}", "ink", a, size=34)
    # 2. measure its diagonal: from (-,-,-,-) to (+,+,+,+)
    a = env(t, T["measure"] - 0.15, T["slice"] - 0.2, 0.2, 0.35)
    if a > 0:
        u = ease_out(lin(t, T["measure"] - 0.15, T["measure"] + 0.45))
        p0, p1 = world[0], world[15]
        q = lerp(p0, p1, u)
        xs, ys, _ = cam.project(np.array([p0, q]))
        fr.line(xs[0], ys[0], xs[1], ys[1], "#ffffff", 3.0, a, glow=1.4)
        fr.glow_dot(xs[1], ys[1], 5.0, "#ffffff", a, 1.5)
        la = a * smooth(lin(t, T["measure"] + 0.3, T["measure"] + 0.6))
        diag = np.linalg.norm(T4.V[15] - T4.V[0])  # unit tesseract: sqrt(1 + 1 + 1 + 1)
        hud.readout(fr, 960, 110, "diagonal", f"{diag:.0f}", "ink", la, size=34)
        fr.chroma(chroma_kick(t, T["measure"] + 0.35, 4.0))
    # 3. slice it: the blue plane cuts the tesseract and a glass octahedron flashes
    a = env(t, T["slice"] - 0.2, T["rotate"] - 0.05, 0.2, 0.3)
    if a > 0:
        half, R, centre = model(t)
        u = ease_io(lin(t, T["slice"] - 0.2, T["slice"] + 0.5))
        y = centre[1] + lerp(1.9, 0.0, u)
        s = 1.9
        plane = np.array([[-s, y, -s], [s, y, -s], [s, y, s], [-s, y, s]])
        draw_plane(fr, cam, plane, t, a, fill=0.08, shimmer=0.0)
        oa = a * smooth(lin(t, T["slice"] + 0.1, T["slice"] + 0.35))
        if oa > 0:
            pts, loops = T4.corner_slice(2.0)
            Rs = rot_y(0.9 * t) @ rot_x(0.35)
            octa = pts @ Rs.T * 1.25 + centre
            T4.draw_solid(
                fr,
                cam,
                octa,
                loops,
                "w",
                oa,
                fill=0.22,
                width=2.6,
                glow=1.1,
                sweep=lin(t, T["slice"] + 0.15, T["slice"] + 0.7),
            )
    # 4. rotate it: hard ZW spin with trails (motion blur weight is set in draw())
    a = env(t, T["rotate"] - 0.1, T["title"] - 0.2, 0.2, 0.4)
    if a > 0:
        T4.draw_trails(fr, cam, world_at, t, span=0.35, steps=12, alpha=0.45 * a, width=1.6, color="w")


def draw_title(fr, t):
    a = smooth(lin(t, T["title"] - 0.05, T["title"] + 0.55))
    if a <= 0:
        return
    rise = (1 - ease_out(lin(t, T["title"] - 0.05, T["title"] + 0.7))) * 26
    title, size, y = "UNDERSTANDING 4D", 104, 548 + rise
    fr.text(title, 960, y, "display", size, 600, "ink", a, tracking=0.06, glow=0.25)
    sweep = lin(t, T["world"] - 0.15, T["world"] + 0.75)
    fr.light_sweep(text_path(title, 960, y, "display", size, 600, tracking=0.06), sweep, strength=0.9)
    u = ease_io(lin(t, T["title"] + 0.2, T["title"] + 0.9))
    half = 340 * u
    fr.line(960 - half, y + 34, 960 + half, y + 34, "w", 2.6, a, glow=0.9)
    sa = smooth(lin(t, T["title"] + 0.5, T["title"] + 1.0))
    fr.text("visually", 960, y + 118, "italic", 64, 500, "w", sa, glow=0.35)
    fr.chroma(chroma_kick(t, T["title"], 5.0))


# ------------------------------------------------------------------ frame function


def draw_one(t, size):
    fr = Frame(size)
    draw_footage(fr, t)
    if t >= T["loose"]:
        cam = camera(t)
        half, R, centre = model(t)
        world = to_world(V4 * half, t, R, centre)
        dof = 4.5 * smooth(lin(t, T["title"] - 0.1, T["title"] + 0.7))
        with fr.blurred(dof):
            draw_grid(fr, cam, t)
            draw_light_pool(fr, cam, t)
            draw_shadow(fr, cam, t, world)
            draw_axes(fr, cam, t)
            draw_sheets(fr, cam, t)
            draw_edges(fr, cam, t, world)
            draw_w_slices(fr, cam, t, R, centre, half)
            draw_teasers(fr, cam, t, world)
            draw_light_source(fr, cam, t)
            draw_coords(fr, cam, t, world)
        fr.dim(
            0.72 * env(t, T["question"] - 0.25, T["w"][0] + 0.3, 0.45, 0.5)
            + 0.55 * smooth(lin(t, T["title"] - 0.1, T["title"] + 0.6))
        )
        draw_w_arrow(fr, cam, t)
        draw_pill(fr, cam, t)
        draw_tools(fr, t)
        draw_title(fr, t)
        fr.chroma(chroma_kick(t, T["w"][0] + 0.15, 6.0))
    if t < T["loose"]:
        fr.letterbox(card_u(t))  # the floating card has no bars; they close in as it fills the frame
    else:
        fr.letterbox(1 - ease_io(lin(t, T["loose"] + 0.2, T["loose"] + 1.3)))
    exit_u = lin(t, END - 0.55, END)
    if exit_u > 0:
        fr.zoom_blur(0.35 * ease_io(exit_u))
        fr.dim(ease_io(exit_u))
    fr.vignette(0.5)
    fr.grain(t, 0.045)
    return fr.finish()


def blur_weight(t: float) -> float:
    """Motion blur only where things move fast: the extrusion and the 'rotate it' spin."""
    return max(
        env(t, T["w"][0] - 0.1, T["w"][1] + 0.2, 0.2, 0.3), env(t, T["rotate"] - 0.2, T["rotate"] + 1.3, 0.2, 0.3)
    )


def draw(t, size):
    t = t + START
    return motion_blur(draw_one, t, size, weight=blur_weight(t))


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch0:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=END - START, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(END - START)
        if audio:
            scene.add_audio(AUDIO, start=0, trim_start=START)
    return scene


OFFSET = START
DURATION = END - START
STILLS = [
    1.0,
    3.5,
    4.4,
    7.0,
    8.4,
    10.5,
    12.5,
    13.4,
    14.8,
    16.5,
    17.9,
    19.8,
    21.5,
    24.0,
    26.8,
    29.2,
    31.8,
    33.8,
    36.5,
    39.4,
    41.9,
    43.1,
    44.1,
    45.6,
    46.6,
    48.6,
    49.3,
]
