"""CHAPTER 0 - COLD OPEN: THE CATHEDRAL (S01-S03), 00:00.000 - 00:53.080.

S01  One clap, many echoes     3D nave (projected wireframe) + image-source wavefronts,
                               then a song streaming in and its echoes peeling off in depth.
S02  It's everywhere           the blend symbol becomes CONVOLUTION, then four 2.5D
                               flip-in panels with real blur / edges / dice / 123 x 11.
S03  The recipe and promise    FLIP SLIDE MULTIPLY ADD pills, a box sliding over a box
                               drawing a real overlap trace, and the Fourier teaser.

All graphics are drawn with skia inside one Faceless Champ FunctionSource; the
teaser equation is a Faceless Champ Equation. Every visual beat is keyed to a
word cue from cue-per-word.srt.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia

from cues import AUDIO, cue, word
from fx import (
    Frame, back, card_quad, clamp, ease_in, ease_io, ease_out, env, image_from_array, lerp, lin, mix,
    offscreen, pulse, smooth, hex_rgb,
)
from sources.test_image import blurred, edges, skyline, tint
from theme import H, THEME, TOKENS, W

# ------------------------------------------------------------------ timing
END = word("let's", 52)  # 53.08 - first word of chapter 1

T = {
    "clap": cue(1), "rings": cue(13), "echoes": cue(15), "fades": cue(18),
    "play": cue(20), "every": cue(27), "echo": cue(32), "pile": cue(37), "other": cue(42),
    "what": cue(43), "blend": cue(50), "song": cue(53), "room": cue(56),
    "that": cue(57), "name": cue(61), "conv": cue(62), "everywhere": cue(65),
    "blurs": cue(67), "neural": cue(75), "edges": cue(78), "roll": cue(86), "dice": cue(88),
    "long": cue(94), "school": cue(99), "one": cue(100), "recipe": cue(102),
    "flip": cue(103), "slide": cue(104), "multiply": cue(105), "add": cue(107),
    "build": cue(114), "other2": cue(125), "fourier": cue(134),
    "sliding": word("sliding", 48), "single": word("single", 48),
    "multiplication": word("multiplication", 48), "end": END,
}

# ------------------------------------------------------------------ S01: nave geometry (world units)
BAYS = [6.0 + 4.0 * k for k in range(10)]
XC, SPRING, ARC_A = 3.2, 4.5, 1.6
ARC_R = XC + ARC_A
APEX = SPRING + math.sqrt(ARC_R**2 - ARC_A**2)
CLAP = np.array([0.0, 1.6, 12.0])
FOCAL, CX, CY = 1000.0, 960.0, 600.0


def _arch(z, inset=0.0, n=26):
    r = ARC_R - inset
    th = np.linspace(math.pi, math.acos(-ARC_A / r), n)
    left = np.stack([ARC_A + r * np.cos(th), SPRING + r * np.sin(th), np.full(n, z)], 1)
    right = left[::-1].copy()
    right[:, 0] *= -1
    return np.vstack([left, right[1:]])


def _bezier(p0, p1, p2, n=22):
    u = np.linspace(0, 1, n)[:, None]
    return (1 - u) ** 2 * p0 + 2 * (1 - u) * u * p1 + u**2 * p2


def _seg(a, b):
    return np.array([a, b], float)


@lru_cache(maxsize=1)
def nave_lines():
    """(points Nx3, base alpha, width) for every line of the nave."""
    lines = []
    for i, z in enumerate(BAYS):
        lines.append((_arch(z), 0.95, 1.7))
        lines.append((_arch(z, 0.38), 0.45, 1.1))
        for x in (-XC, XC):
            lines.append((_seg((x, 0, z), (x, SPRING, z)), 0.85, 1.6))
        for x in (-XC + 0.38, XC - 0.38):
            lines.append((_seg((x, 0, z), (x, SPRING, z)), 0.4, 1.0))
        lines.append((_seg((-XC, 0, z), (XC, 0, z)), 0.28, 1.0))
        if i < len(BAYS) - 1:
            z2 = BAYS[i + 1]
            ctrl = np.array([0.0, APEX + 1.3, (z + z2) / 2])
            lines.append((_bezier(np.array([-XC, SPRING, z]), ctrl, np.array([XC, SPRING, z2])), 0.42, 1.0))
            lines.append((_bezier(np.array([XC, SPRING, z]), ctrl, np.array([-XC, SPRING, z2])), 0.42, 1.0))
    z0, z1 = BAYS[0], BAYS[-1]
    for x in (-XC, XC):
        for y, a in ((0.0, 0.5), (SPRING, 0.6), (SPRING + 2.9, 0.35)):
            lines.append((_seg((x, y, z0), (x, y, z1)), a, 1.2))
    lines.append((_seg((0, APEX, z0), (0, APEX, z1)), 0.5, 1.2))
    lines.append((_seg((0, 0, z0), (0, 0, z1)), 0.16, 1.0))
    # rose window on the far wall
    zr, cy, ang = z1 + 1.0, SPRING + 2.0, np.linspace(0, 2 * math.pi, 49)
    for r, a in ((1.9, 0.8), (1.55, 0.4), (0.7, 0.7)):
        lines.append((np.stack([r * np.cos(ang), cy + r * np.sin(ang), np.full(49, zr)], 1), a, 1.3))
    for k in range(12):
        th = k * math.pi / 6
        lines.append((_seg((0.7 * math.cos(th), cy + 0.7 * math.sin(th), zr),
                           (1.9 * math.cos(th), cy + 1.9 * math.sin(th), zr)), 0.55, 1.0))
    return lines


def camera(t):
    """Slow dolly down the aisle, with a short kick (shake + focal punch) on the clap."""
    u = ease_io(lin(t, 0.0, 20.0))
    age = t - T["clap"]
    kick = math.exp(-max(age, 0.0) / 0.16) if age > 0 else 0.0
    shake = 0.06 * kick * math.sin(age * 95.0) if age > 0 else 0.0
    focal = FOCAL * (1.0 + 0.06 * math.exp(-max(age, 0.0) / 0.45)) if age > 0 else FOCAL * 1.06
    return (shake, 1.75 + 0.5 * shake, -4.6 + 2.4 * u, 0.11 - 0.015 * u, focal)


def project(points, cam):
    x0, y0, z0, p = cam[:4]
    f = cam[4] if len(cam) > 4 else FOCAL
    dx, dy, dz = points[:, 0] - x0, points[:, 1] - y0, points[:, 2] - z0
    cp, sp = math.cos(p), math.sin(p)
    zc = np.maximum(dy * sp + dz * cp, 1e-3)
    yc = dy * cp - dz * sp
    return CX + f * dx / zc, CY - f * yc / zc, zc


def nave_opacity(t):
    return lerp(1.0, 0.24, smooth(lin(t, T["play"] - 0.2, T["play"] + 1.6))) * (1 - smooth(lin(t, T["that"], T["that"] + 0.8)))


# ------------------------------------------------------------------ S01 opening: the sound reveals the cathedral
SPEED = 6.0  # wavefront speed in world units / s: the reveal sweeps the whole nave in ~5 s
FRONT_W = 0.55  # thickness of the bright wavefront shell
ECHO_DELAY = 1.4  # reflections arrive later so the cyan reveal owns the first beats ("rings", "echoes")
# image sources (mirror positions of the clap across walls / floor / vault): (position, gain, visible-after radius)
MIRRORS = [
    (np.array([2 * XC, 1.6, 12.0]), 0.62, XC), (np.array([-2 * XC, 1.6, 12.0]), 0.62, XC),
    (np.array([0.0, -1.6, 12.0]), 0.42, 1.6), (np.array([0.0, 2 * APEX - 1.6, 12.0]), 0.45, APEX - 1.6),
    (np.array([4 * XC, 1.6, 12.0]), 0.3, 3 * XC), (np.array([-4 * XC, 1.6, 12.0]), 0.3, 3 * XC),
]


def highlight_fade(t):
    return 1 - smooth(lin(t, T["fades"] - 0.9, T["play"] + 1.0))


@lru_cache(maxsize=1)
def nave_segments():
    """Every nave line resampled into short segments, with distances to the clap and its mirrors."""
    p0, p1, base, width = [], [], [], []
    for pts, b, w in nave_lines():
        for a, c in zip(pts[:-1], pts[1:]):
            n = max(1, int(math.ceil(float(np.linalg.norm(c - a)) / 0.45)))
            for k in range(n):
                p0.append(a + (c - a) * k / n)
                p1.append(a + (c - a) * (k + 1) / n)
                base.append(b)
                width.append(w)
    p0, p1 = np.array(p0), np.array(p1)
    mid = (p0 + p1) / 2
    d0 = np.linalg.norm(mid - CLAP, axis=1)
    dm = np.stack([np.linalg.norm(mid - m, axis=1) for m, _, _ in MIRRORS], 1)
    return p0, p1, np.array(base), np.array(width), d0, dm


def _bins(fr, x0, y0, x1, y1, alpha, width, color, levels=7, glow=0.0, width_scale=1.0):
    """Stroke segments grouped by quantised alpha and two width classes (few draw calls per frame)."""
    q = np.minimum((alpha * levels).astype(int), levels)
    wide = width > 1.15
    for lv in range(1, levels + 1):
        for wclass in (False, True):
            idx = np.nonzero((q == lv) & (wide == wclass))[0]
            if not len(idx):
                continue
            p = skia.Path()
            for i in idx:
                p.moveTo(float(x0[i]), float(y0[i]))
                p.lineTo(float(x1[i]), float(y1[i]))
            w = float(np.mean(width[idx])) * width_scale
            fr.path_stroke(p, color, w, lv / levels, glow=glow)


def draw_nave(fr, t):
    op = nave_opacity(t)
    if op <= 0.003:
        return
    cam = camera(t)
    p0, p1, base, width, d0, dm = nave_segments()
    x0, y0, z0 = project(p0, cam)
    x1, y1, z1 = project(p1, cam)
    depth = (z0 + z1) / 2
    depthf = np.clip(1.3 - depth / 42.0, 0.14, 1.0)
    w = width * np.clip(10.0 / depth, 0.55, 1.6)
    age = t - T["clap"]
    r = SPEED * age if age > 0 else -10.0
    rv = np.clip((r - d0) / 2.2, 0.0, 1.0)
    reveal = rv * rv * (3 - 2 * rv)
    hf = highlight_fade(t)
    front = np.exp(-(((r - d0) / FRONT_W) ** 2))
    after = np.where(r > d0, np.exp(-(r - d0) / (SPEED * 0.9)), 0.0)
    cyan = (front + 0.4 * after) * hf
    amber = np.zeros_like(d0)
    ra = SPEED * (age - ECHO_DELAY)
    for k, (_, g, rmin) in enumerate(MIRRORS):
        if ra > rmin:
            amber += g * np.exp(-(((ra - dm[:, k]) / FRONT_W) ** 2))
    amber *= hf
    # stone revealed behind the wave, then the travelling light on top
    _bins(fr, x0, y0, x1, y1, np.clip(base * op * depthf * reveal * 0.9, 0, 1), w, "stone", glow=0.15)
    _bins(fr, x0, y0, x1, y1, np.clip(1.25 * cyan * op * (0.45 + 0.55 * depthf), 0, 1), w, mix(TOKENS["signal"], "#ffffff", 0.3),
          glow=1.1, width_scale=1.6)
    _bins(fr, x0, y0, x1, y1, np.clip(amber * op * (0.35 + 0.65 * depthf), 0, 1), w, "kernel", glow=0.9, width_scale=1.3)


@lru_cache(maxsize=1)
def motes():
    rng = np.random.default_rng(21)
    n = 320
    pos = np.stack([rng.uniform(-2.9, 2.9, n), rng.uniform(0.3, 8.6, n), rng.uniform(6.0, 42.0, n)], 1)
    return pos, rng.uniform(0, 2 * math.pi, n), rng.uniform(0.6, 1.4, n)


def draw_motes(fr, t):
    op = nave_opacity(t) * (1 - smooth(lin(t, T["play"] - 0.4, T["play"] + 1.0)))
    if op <= 0.003:
        return
    pos, phase, size = motes()
    p = pos.copy()
    p[:, 0] += 0.12 * np.sin(t * 0.35 + phase)
    p[:, 1] += 0.10 * np.sin(t * 0.5 + 1.7 * phase)
    age = t - T["clap"]
    r = SPEED * age if age > 0 else -10.0
    d = np.linalg.norm(p - CLAP, axis=1)
    rv = np.clip((r - d) / 2.0, 0, 1)
    lit = 0.3 * rv + 0.95 * np.exp(-(((r - d) / 0.7) ** 2)) * highlight_fade(t)
    sx, sy, zc = project(p, camera(t))
    radius = np.clip(size * 34.0 / zc, 0.8, 3.6)
    q = np.minimum((lit * 6).astype(int), 6)
    for lv in range(1, 7):
        idx = np.nonzero(q == lv)[0]
        if not len(idx):
            continue
        a = lv / 6 * op
        for big in (False, True):
            sel = idx[(radius[idx] > 1.6) == big]
            if not len(sel):
                continue
            pts = [skia.Point(float(sx[i]), float(sy[i])) for i in sel]
            col = mix(TOKENS["stone"], "#ffffff", lv / 6)
            paint = skia.Paint(AntiAlias=True, StrokeCap=skia.Paint.kRound_Cap, StrokeWidth=3.0 if big else 1.8,
                               Color4f=_c4(col, a))
            fr.c.drawPoints(skia.Canvas.kPoints_PointMode, pts, paint)
            if lv >= 4:
                fr.glow_used = True
                gpaint = skia.Paint(AntiAlias=True, StrokeCap=skia.Paint.kRound_Cap, StrokeWidth=9.0, Color4f=_c4(col, a * 0.8))
                fr.g.drawPoints(skia.Canvas.kPoints_PointMode, pts, gpaint)


def _c4(color, a):
    from fx import col

    return col(color, a)


def draw_shafts(fr, t):
    """Soft clerestory light shafts, revealed once the sound has passed."""
    op = nave_opacity(t)
    a = smooth(lin(t, 1.6, 3.4)) * op * (1 - smooth(lin(t, T["play"] - 0.5, T["play"] + 1.2)))
    if a <= 0.003:
        return
    cam = camera(t)
    for k, z in enumerate((14.0, 26.0, 38.0)):
        top = np.array([[-XC, 7.2, z - 1.1], [-XC, 7.2, z + 1.1]])
        bot = np.array([[2.6, 0.0, z + 3.0], [-0.4, 0.0, z + 0.2]])
        sx, sy, _ = project(np.vstack([top, bot]), cam)
        quad = [skia.Point(float(x), float(y)) for x, y in zip(sx, sy)]
        path = skia.Path()
        path.addPoly(quad, True)
        flicker = 0.85 + 0.15 * math.sin(t * 0.9 + k * 2.1)
        fr.path_fill(path, "#cfdcff", 0.07 * a * flicker / (1 + 0.25 * k), glow=1.6)


def _ring_runs(fr, xs, ys, mask, color, width, alpha, glow):
    run_x, run_y = [], []
    for x, y, m in zip(xs, ys, mask):
        if m:
            run_x.append(x)
            run_y.append(y)
        elif len(run_x) > 1:
            fr.poly(run_x, run_y, color, width, alpha, glow=glow)
            run_x, run_y = [], []
        else:
            run_x, run_y = [], []
    if len(run_x) > 1:
        fr.poly(run_x, run_y, color, width, alpha, glow=glow)


ANG = np.linspace(0, 2 * math.pi, 160)


def draw_rings(fr, t):
    age = t - T["clap"]
    if age < 0:
        return
    cam = camera(t)
    gate = 1 - smooth(lin(t, T["fades"] - 0.6, T["play"] + 1.6))
    sx, sy, zc = project(CLAP[None, :], cam)
    f = cam[4]
    # the impact: exposure bloom, anamorphic streak, white-hot core
    if age < 0.9:
        e = math.exp(-age / 0.12)
        shader = skia.GradientShader.MakeRadial(skia.Point(float(sx[0]), float(sy[0])), 1100.0,
                                                [_c4("#ffffff", 0.55 * e), _c4(TOKENS["signal"], 0.16 * e), _c4("#000000", 0.0)],
                                                [0.0, 0.25, 1.0])
        fr.c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=shader, BlendMode=skia.BlendMode.kPlus))
        L = 1150.0 * (1 - math.exp(-age / 0.05))
        sa = math.exp(-age / 0.32)
        streak = skia.GradientShader.MakeLinear(
            [skia.Point(float(sx[0]) - L, 0), skia.Point(float(sx[0]) + L, 0)],
            [_c4(TOKENS["signal"], 0.0), _c4(TOKENS["signal"], 0.7 * sa), _c4("#ffffff", sa), _c4(TOKENS["signal"], 0.7 * sa),
             _c4(TOKENS["signal"], 0.0)],
            [0.0, 0.35, 0.5, 0.65, 1.0])
        for thick, k in ((2.4, 1.0), (7.0, 0.35)):
            fr.c.drawLine(float(sx[0]) - L, float(sy[0]), float(sx[0]) + L, float(sy[0]),
                          skia.Paint(AntiAlias=True, Shader=streak, StrokeWidth=thick, Color4f=_c4("#ffffff", k)))
        fr.glow_dot(sx[0], sy[0], 5.0 + 4.0 * (1 - e), "ink", alpha=min(1.0, 0.4 + e), strength=2.2)
    # spherical shock front around the clap, with a slight prismatic edge
    r = SPEED * age
    if age < 2.4:
        a = math.exp(-age / 0.7) * gate
        rs = f * r / float(zc[0])
        fr.circle(sx[0], sy[0], rs, "signal", 3.0, a, glow=1.2)
        fr.circle(sx[0], sy[0], rs + 5, "overlap", 1.4, a * 0.45, glow=0.4)
        fr.circle(sx[0], sy[0], rs * 0.86, "signal", 1.2, a * 0.4)
    # ripples across the floor: direct (cyan) and reflected from the side walls (amber)
    if gate > 0.003:
        z_lo, z_hi = BAYS[0] - 1.0, BAYS[-1]
        for (cx, gain, rmin, color) in ((0.0, 1.0, 0.0, "signal"), (2 * XC, 0.62, XC, "kernel"), (-2 * XC, 0.62, XC, "kernel"),
                                        (4 * XC, 0.3, 3 * XC, "kernel"), (-4 * XC, 0.3, 3 * XC, "kernel")):
            for off, ta in ((0.0, 1.0), (0.5, 0.5), (1.0, 0.25)):
                rr = (r if color == "signal" else SPEED * (age - ECHO_DELAY)) - off
                if rr <= rmin:
                    continue
                pts = np.stack([cx + rr * np.cos(ANG), np.full(len(ANG), 0.01), 12.0 + rr * np.sin(ANG)], 1)
                mask = (np.abs(pts[:, 0]) <= XC) & (pts[:, 2] >= z_lo) & (pts[:, 2] <= z_hi)
                if not mask.any():
                    continue
                px, py, _ = project(pts, cam)
                appear = smooth(min(1.0, (rr - rmin) / 0.8))
                a = gain * ta * math.exp(-rr / 16.0) * gate * appear
                _ring_runs(fr, px, py, mask, color, 2.0 if off == 0 else 1.3, a, 0.7)


# ------------------------------------------------------------------ the room's impulse response, recorded live
LISTENER = np.array([0.0, 1.6, 8.5])
IR_X0, IR_X1, IR_Y, IR_H, IR_T = 660.0, 1260.0, 1004.0, 64.0, 6.5


@lru_cache(maxsize=1)
def impulse_spikes():
    spikes = [(float(np.linalg.norm(CLAP - LISTENER)) / SPEED, 1.0, "signal")]
    for m, g, _ in MIRRORS:
        d = float(np.linalg.norm(m - LISTENER))
        spikes.append((d / SPEED + ECHO_DELAY, min(0.9, g * 4.5 / d), "kernel"))
    rng = np.random.default_rng(8)
    for _ in range(46):  # late diffuse reverberation
        a = rng.uniform(2.2, 6.3)
        spikes.append((a, 0.42 * math.exp(-(a - 2.2) / 1.7) * rng.uniform(0.3, 1.0), "kernel"))
    return sorted(spikes)


def draw_impulse(fr, t):
    vis = env(t, 0.5, T["play"] + 0.5, 0.5, 0.6)
    if vis <= 0.003:
        return
    age = t - T["clap"]
    fr.text("ROOM IMPULSE RESPONSE", IR_X0, IR_Y - IR_H - 22, "sans", 17, 700, "muted", vis * 0.9, align="left", tracking=0.24)
    fr.line(IR_X0, IR_Y, IR_X1, IR_Y, "line", 1.2, vis)
    for at, h, color in impulse_spikes():
        if age < at or at > IR_T:
            continue
        x = IR_X0 + (IR_X1 - IR_X0) * at / IR_T
        pop = back(min(1.0, (age - at) / 0.18), 2.0)
        fr.line(x, IR_Y, x, IR_Y - IR_H * h * pop, color, 1.8 if color == "signal" else 1.4, vis, glow=0.6)
    if 0 < age < IR_T:
        x = IR_X0 + (IR_X1 - IR_X0) * age / IR_T
        fr.line(x, IR_Y + 6, x, IR_Y - IR_H - 4, "#ffffff", 1.0, vis * 0.35)


# ------------------------------------------------------------------ S01C: song + echoes
N = 600
WAVE_X0, WAVE_X1, BASE_Y = 210.0, 1710.0, 800.0
VANISH = (960.0, 330.0)
ECHO_D, ECHO_G = 38, [0.6**k for k in range(1, 5)]


@lru_cache(maxsize=1)
def song():
    n = np.arange(N, dtype=float)
    x = np.zeros(N)
    for n0, period, amp in ((4, 13, 0.9), (78, 10, 0.75), (152, 16, 0.95), (218, 11, 0.7),
                            (292, 9, 0.85), (372, 14, 0.9), (444, 12, 0.72), (518, 10, 0.82)):
        k = n - n0
        on = k >= 0
        x += np.where(on, amp * np.exp(-k / 30.0) * (1 - np.exp(-k / 3.0)) * np.sin(2 * math.pi * k / period), 0)
    y = x.copy()
    for k, g in enumerate(ECHO_G, 1):
        y[ECHO_D * k :] += g * x[: N - ECHO_D * k]
    scale = 118.0 / np.abs(y).max()
    return x * scale, y * scale


XS = np.linspace(WAVE_X0, WAVE_X1, N)
NIDX = np.arange(N, dtype=float)


def wave_pts(vals, depth=0.0, upto=1.0):
    m = max(2, int(upto * N))
    s = 1.0 / (1.0 + 0.17 * depth)
    px = VANISH[0] + (XS[:m] - VANISH[0]) * s
    py = VANISH[1] + (BASE_Y - vals[:m] - VANISH[1]) * s
    return px, py


def draw_song(fr, t):
    vis = env(t, T["play"] - 0.1, T["that"] + 0.7, 0.3, 0.7)
    if vis <= 0.003:
        return
    x, y = song()
    upto = ease_io(lin(t, T["play"], T["play"] + 1.9))
    pile = ease_io(lin(t, T["pile"] - 0.1, T["other"]))
    merge = ease_io(lin(t, T["other"] + 0.1, T["what"] + 0.8))
    # baseline
    fr.line(WAVE_X0, BASE_Y, WAVE_X1, BASE_Y, "grid", 1.0, 0.9 * vis)
    # echo copies peel off backwards in depth, delayed and quieter
    for k, g in enumerate(ECHO_G, 1):
        start = T["every"] + 0.42 * (k - 1)
        ak = ease_out(lin(t, start, start + 0.9))
        if ak <= 0:
            continue
        shift = ECHO_D * k * ak
        vals = g * np.interp(NIDX - shift, NIDX, x, left=0.0)
        depth = k * ak * (1 - pile)
        alpha = (0.4 + 0.55 * g**0.5) * ak * (1 - 0.8 * merge) * vis
        px, py = wave_pts(vals, depth)
        fr.poly(px, py, "kernel", 1.8, alpha, glow=0.45)
    # the song itself
    px, py = wave_pts(x, 0.0, upto)
    fr.poly(px, py, "signal", 2.4, vis * (1 - 0.72 * merge), glow=0.7)
    if 0 < upto < 1:
        fr.glow_dot(px[-1], py[-1], 4.5, "signal", alpha=vis, strength=1.4)
    # what reaches your ears: the real sum
    if merge > 0:
        px, py = wave_pts(y, 0.0)
        fr.poly(px, py, "output", 2.6, merge * vis, glow=0.5)
    # labels
    fr.text("SONG", WAVE_X0, BASE_Y - 178, "sans", 20, 700, "signal", vis * env(t, T["play"], T["other"] + 0.6),
            align="left", tracking=0.18)
    fr.text("+ ECHOES", WAVE_X0 + 96, BASE_Y - 178, "sans", 20, 700, "kernel",
            vis * env(t, T["every"] + 0.2, T["other"] + 0.6), align="left", tracking=0.18)
    fr.text("WHAT YOU HEAR", WAVE_X0, BASE_Y - 178, "sans", 20, 700, "output",
            vis * env(t, T["what"] + 0.2, T["that"] + 0.7), align="left", tracking=0.18)


# ------------------------------------------------------------------ pictogram + blend symbol
PICTO_Y = 232.0
G1, STAR0, G2, EQX, G3 = 560.0, 762.0, 960.0, 1158.0, 1360.0


def mini_wave(fr, vals, cx, cy, w, h, color, alpha, width=2.0, glow=0.5):
    idx = np.linspace(0, len(vals) - 1, 160).astype(int)
    v = vals[idx]
    px = np.linspace(cx - w / 2, cx + w / 2, len(v))
    py = cy - v / np.abs(vals).max() * h / 2
    fr.poly(px, py, color, width, alpha, glow)


def draw_star(fr, x, y, s, alpha, rot=0.0, glow=0.8):
    if alpha <= 0.003:
        return
    fr.circle(x, y, 22 * s, "overlap", width=2.6 * s, alpha=alpha, glow=glow)
    for k in range(3):
        a = rot + k * math.pi / 3 + math.pi / 2
        dx, dy = 11 * s * math.cos(a), 11 * s * math.sin(a)
        fr.line(x - dx, y - dy, x + dx, y + dy, "overlap", 2.6 * s, alpha, glow=glow)


def star_state(t):
    """Position, scale, rotation and opacity of the blend symbol across S01D-S02A."""
    a = ease_out(lin(t, T["what"] + 1.45, T["what"] + 1.95))
    x, y, s, rot = STAR0, PICTO_Y - 22 * (1 - a), 1.0, 0.0
    m1 = ease_io(lin(t, T["that"] + 0.15, T["name"] - 0.1))
    x, y, s, rot = lerp(x, 960, m1), lerp(y, 500, m1), lerp(s, 3.4, m1), lerp(0, math.pi / 3, m1)
    m2 = ease_io(lin(t, T["conv"] - 0.45, T["conv"] + 0.2))
    y, s = lerp(y, 318, m2), lerp(s, 1.55, m2)
    out = 1 - smooth(lin(t, T["everywhere"] - 0.25, T["everywhere"] + 0.35))
    s *= 1 + 0.32 * pulse(t, T["blend"] - 0.08, 0.6)
    return x, y, s, rot, a * out


def draw_pictogram(fr, t):
    x, y_sum = song()
    fade = 1 - smooth(lin(t, T["that"] - 0.05, T["that"] + 0.5))
    items = ((G1, 250, T["what"] + 1.2), (G2, 200, T["what"] + 1.7), (G3, 250, T["what"] + 2.0))
    for i, (cx, w, t0) in enumerate(items):
        a = ease_out(lin(t, t0, t0 + 0.5)) * fade
        if a <= 0.003:
            continue
        cy = PICTO_Y - 18 * (1 - a)
        color = ("signal", "kernel", "output")[i]
        hl = pulse(t, (T["song"], T["room"], T["blend"] + 0.3)[i] - 0.1, 0.9)
        fr.rrect(cx - w / 2, cy - 55, w, 110, 18, fill="card", stroke=mix(TOKENS["line"], TOKENS[color], 0.25 + 0.75 * hl),
                 width=1.5 + hl, alpha=a, glow=0.8 * hl)
        if i == 0:
            mini_wave(fr, x, cx, cy, w - 40, 70, "signal", a)
        elif i == 2:
            mini_wave(fr, y_sum, cx, cy, w - 40, 70, "output", a, width=2.4, glow=0.7)
        else:
            for k, g in enumerate([1.0] + ECHO_G):
                sx = cx - 64 + k * 32
                fr.line(sx, cy + 30, sx, cy + 30 - 58 * g, "kernel", 2.4, a, glow=0.5)
                fr.circle(sx, cy + 30 - 58 * g, 4.2, "kernel", alpha=a, fill=True)
    ea = ease_out(lin(t, T["what"] + 1.85, T["what"] + 2.3)) * fade
    if ea > 0:
        fr.line(EQX - 16, PICTO_Y - 7, EQX + 16, PICTO_Y - 7, "ink", 2.4, ea * 0.8)
        fr.line(EQX - 16, PICTO_Y + 7, EQX + 16, PICTO_Y + 7, "ink", 2.4, ea * 0.8)
    fr.text("song", G1, PICTO_Y + 92, "sans", 20, 600, "signal", ease_out(lin(t, T["song"] - 0.2, T["song"] + 0.3)) * fade,
            tracking=0.12)
    fr.text("room", G2, PICTO_Y + 92, "sans", 20, 600, "kernel", ease_out(lin(t, T["room"] - 0.2, T["room"] + 0.3)) * fade,
            tracking=0.12)
    sx, sy, s, rot, sa = star_state(t)
    draw_star(fr, sx, sy, s, sa, rot, glow=0.6 + 0.8 * pulse(t, T["blend"] - 0.08, 0.6))


# ------------------------------------------------------------------ S02A: CONVOLUTION title
TITLE = "CONVOLUTION"


def title_state(t):
    m = ease_io(lin(t, T["everywhere"] - 0.15, T["everywhere"] + 0.6))
    size = lerp(150.0, 56.0, m)
    base = lerp(640.0, 128.0, m)
    alpha = 1 - smooth(lin(t, T["school"] + 0.2, T["one"] + 0.1))
    return size, base, alpha


def draw_title(fr, t):
    t0 = T["conv"] - 0.18
    if t < t0:
        return
    size, base, alpha = title_state(t)
    if alpha <= 0.003:
        return
    from fx import font

    f = font("display", size, 700)
    tracking = 0.04 * size
    widths = [f.measureText(ch) for ch in TITLE]
    total = sum(widths) + tracking * (len(TITLE) - 1)
    # chromatic kick on landing
    kick = 1 - lin(t, t0 + 0.05, t0 + 0.45)
    x = 960 - total / 2
    for i, ch in enumerate(TITLE):
        ai = ease_out(lin(t, t0 + 0.035 * i, t0 + 0.035 * i + 0.4))
        dy = 28 * (1 - ai)
        if kick > 0 and ai > 0:
            fr.text(ch, x - 7 * kick, base + dy, "display", size, 700, "#FF2D55", 0.5 * kick * ai * alpha, align="left")
            fr.text(ch, x + 7 * kick, base + dy, "display", size, 700, "#2D9CFF", 0.5 * kick * ai * alpha, align="left")
        fr.text(ch, x, base + dy, "display", size, 700, "ink", ai * alpha, align="left", glow=0.18)
        x += widths[i] + tracking
    u = ease_io(lin(t, T["conv"] + 0.25, T["conv"] + 0.95))
    if u > 0:
        half = total * 0.51 * u
        uy = base + 0.26 * size
        fr.line(960 - half, uy, 960 + half, uy, "overlap", 1.0 + 3.2 * size / 150, alpha, glow=0.9)


# ------------------------------------------------------------------ S02B: montage panels
PANEL_W, PANEL_H, PANEL_Y = 380.0, 560.0, 610.0
PANEL_X = [336.0 + i * 416.0 for i in range(4)]
PILL_X = [462.0, 794.0, 1126.0, 1458.0]
PILL_Y, PILL_W, PILL_H = 520.0, 300.0, 96.0


def panel_times():
    return [T["blurs"] - 0.25, T["neural"] - 0.3, T["roll"] - 0.25, T["long"] - 0.3]


@lru_cache(maxsize=1)
def panel_images():
    signal, output = hex_rgb("signal"), hex_rgb("output")
    sharp = image_from_array(tint(skyline(), signal))
    blur = image_from_array(tint(blurred(), signal))
    edge = image_from_array(tint(edges(), output, highlight=0.2))
    dim = image_from_array(tint(skyline() * 0.35, signal, highlight=0.0))
    return sharp, blur, edge, dim


IMG_RECT = (20.0, 78.0, 340.0, 300.0)


def _clip_image(p, image, frac_lo, frac_hi):
    x, y, w, h = IMG_RECT
    if frac_hi <= frac_lo:
        return
    iw, ih = image.width(), image.height()
    src = skia.Rect.MakeLTRB(iw * frac_lo, 0, iw * frac_hi, ih)
    dst = skia.Rect.MakeLTRB(x + w * frac_lo, y, x + w * frac_hi, y + h)
    p.c.drawImageRect(image, src, dst, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(AntiAlias=True))


def _kernel_glyph(p, x, y, weights, label):
    cell = 26
    for r in range(3):
        for c in range(3):
            w = weights[r][c]
            a = 0.18 + 0.6 * abs(w) / max(abs(v) for row in weights for v in row)
            p.rrect(x + c * (cell + 3), y + r * (cell + 3), cell, cell, 5, fill="kernel", fill_alpha=a * 0.55,
                    stroke="kernel", width=1.0, alpha=0.9)
            sym = "" if w == 0 else ("+" if w > 0 and len(set(v for row in weights for v in row)) > 1 else
                                     ("−" if w < 0 else ""))
            if sym:
                p.text(sym, x + c * (cell + 3) + cell / 2, y + r * (cell + 3) + 19, "sans", 18, 700, "ink", 0.95)
    p.text(label, x + 3 * (cell + 3) + 18, y + 50, "sans", 20, 500, "muted", 1.0, align="left")


def _pips(p, cx, cy, s, value, color):
    p.rrect(cx - s / 2, cy - s / 2, s, s, s * 0.2, fill="card", stroke=color, width=2.0)
    q = s * 0.26
    spots = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)],
             4: [(-1, -1), (1, -1), (-1, 1), (1, 1)], 5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
             6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}[value]
    for dx, dy in spots:
        p.circle(cx + dx * q, cy + dy * q, s * 0.07, color, fill=True)


def render_panel(i, u, k):
    surf, p = offscreen(PANEL_W, PANEL_H, k)
    p.rrect(0.75, 0.75, PANEL_W - 1.5, PANEL_H - 1.5, 22, fill="card", stroke="line", width=1.5)
    names = ("BLUR", "EDGES", "DICE", "MULTIPLICATION")
    p.text(f"0{i + 1}", 24, 50, "display", 20, 600, "muted", 1.0, align="left")
    p.text(names[i], 24, 528, "sans", 22, 700, "ink", 1.0, align="left", tracking=0.16)
    sharp, blur, edge, dim = panel_images()
    x, y, w, h = IMG_RECT
    if i in (0, 1):
        sweep = ease_io(lin(u, 0.35, 1.75))
        if i == 0:
            _clip_image(p, blur, 0.0, sweep)
            _clip_image(p, sharp, sweep, 1.0)
            _kernel_glyph(p, 24, 404, [[1, 1, 1]] * 3, "average")
        else:
            _clip_image(p, edge, 0.0, sweep)
            _clip_image(p, dim, sweep, 1.0)
            _kernel_glyph(p, 24, 404, [[-1, 0, 1]] * 3, "edge kernel")
        if 0 < sweep < 1:
            sx = x + w * sweep
            p.line(sx, y, sx, y + h, "kernel", 1.5, 0.55)
            cy = y + h * 0.55
            for j in range(4):
                p.line(sx - 18 + 12 * j, cy - 18, sx - 18 + 12 * j, cy + 18, "kernel", 1.4, 0.95)
                p.line(sx - 18, cy - 18 + 12 * j, sx + 18, cy - 18 + 12 * j, "kernel", 1.4, 0.95)
    elif i == 2:
        for j, (cx, val, color) in enumerate(((120.0, 3, "signal"), (260.0, 4, "kernel"))):
            a = ease_out(lin(u, 0.05 + 0.12 * j, 0.45 + 0.12 * j))
            p.c.save()
            p.c.translate(cx, 136)
            p.c.rotate(28 * (1 - a) * (1 if j else -1))
            p.c.translate(-cx, -136)
            _pips(p, cx, 136 - 30 * (1 - back(a)), 78, val, color)
            p.c.restore()
        p.text("+", 190, 150, "display", 40, 500, "muted", ease_out(lin(u, 0.3, 0.6)))
        counts = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
        bw, gap, x0, base = 24.0, 5.6, 30.0, 392.0
        for j, c in enumerate(counts):
            g = ease_out(lin(u, 0.55 + 0.07 * j, 1.05 + 0.07 * j))
            hgt = 30.0 * c * g
            bx = x0 + j * (bw + gap)
            if hgt > 0.5:
                p.rrect(bx, base - hgt, bw, hgt, 4, fill="output", fill_alpha=0.82)
            if j == 5 and u > 1.55:
                p.rrect(bx - 3, base - hgt - 3, bw + 6, hgt + 6, 6, stroke="overlap", width=2.2,
                        alpha=ease_out(lin(u, 1.55, 1.9)))
        p.line(x0 - 6, base, x0 + 11 * (bw + gap) - gap + 6, base, "line", 1.2)
        for j, lab in ((0, "2"), (5, "7"), (10, "12")):
            p.text(lab, x0 + j * (bw + gap) + bw / 2, base + 26, "display", 18, 500, "muted", 1.0)
    else:
        cw, right = 36.0, 300.0
        from fx import font  # noqa: F401  (fonts cached)

        def digits(s, yb, color, a, start_col=0):
            for j, ch in enumerate(reversed(s)):
                col_x = right - (j + start_col) * cw - cw / 2
                p.text(ch, col_x, yb, "display", 52, 600, color, a)

        rows = [("123", 150, "signal", 0.0, 0), ("11", 218, "kernel", 0.25, 0), ("123", 300, "signal", 0.8, 0),
                ("123", 364, "signal", 1.0, 1)]
        for s, yb, color, t0, sc in rows:
            a = ease_out(lin(u, t0, t0 + 0.3))
            digits(s, yb + 10 * (1 - a), color, a * (0.62 if yb > 250 else 1.0), sc)
        p.text("×", right - 3 * cw - cw / 2, 218, "display", 46, 500, "kernel", ease_out(lin(u, 0.25, 0.55)))
        for ly, t0 in ((240, 0.5), (386, 1.2)):
            a = ease_out(lin(u, t0, t0 + 0.35))
            p.line(right - 4 * cw * a, ly, right, ly, "line", 2.0)
        for j, ch in enumerate("1353"):
            t0 = 1.35 + 0.16 * j
            a = ease_out(lin(u, t0, t0 + 0.25))
            flash = pulse(u, t0, 0.5)
            col_x = right - (3 - j) * cw - cw / 2
            p.text(ch, col_x, 456 - 8 * (1 - a), "display", 56, 700, mix(TOKENS["output"], "#ffffff", flash * 0.6), a)
    return surf.makeImageSnapshot()


def draw_montage(fr, t):
    times = panel_times()
    if t < times[0] - 0.05 or t > T["one"] + 0.3:
        return
    collapse = ease_in(lin(t, T["school"] + 0.15, T["one"] + 0.15))
    truck = -26.0 * lin(t, times[0], T["school"])
    for i, t0 in enumerate(times):
        if t < t0:
            continue
        e = lin(t, t0, t0 + 0.75)
        angle = 1.25 * (1 - ease_out(e)) + 0.11 * (1.5 - i) * (1 - collapse)
        alpha = smooth(lin(t, t0, t0 + 0.35))
        nxt = times[i + 1] if i + 1 < len(times) else None
        if nxt is not None:
            alpha *= 1 - 0.55 * smooth(lin(t, nxt, nxt + 0.5))
        alpha = max(alpha, smooth(lin(t, T["school"] - 0.5, T["school"])) * min(1.0, alpha + 1))  # all relight
        scale = lerp(0.9, 1.0, ease_out(e)) * (1 - collapse)
        cx = lerp(PANEL_X[i] + truck, PILL_X[i], ease_io(collapse))
        cy = lerp(PANEL_Y, PILL_Y, ease_io(collapse))
        if scale < 0.05:
            fr.circle(cx, cy, 7, "line", alpha=1.0, fill=True)
            continue
        img = render_panel(i, t - t0, fr.k * scale)
        quad = card_quad(cx, cy, PANEL_W, PANEL_H, angle, scale)
        fr.image_quad(img, quad, alpha)


# ------------------------------------------------------------------ S03: recipe pills
PILL_NAMES = ("FLIP", "SLIDE", "MULTIPLY", "ADD")
PILL_COLORS = ("kernel", "kernel", "overlap", "output")


def pill_layout(t):
    m = ease_io(lin(t, T["build"] - 1.6, T["build"] - 0.8))
    return lerp(PILL_Y, 196.0, m), lerp(1.0, 0.78, m)


def _icon(fr, i, x, y, color, a, act):
    if i == 0:  # flip: a triangle mirrored through a dashed axis
        sxs = math.cos(math.pi * act)
        for j in range(4):
            fr.line(x, y - 16 + j * 9, x, y - 11 + j * 9, color, 1.6, a * 0.8)
        p = skia.Path()
        p.moveTo(x + 4 * sxs, y - 12)
        p.lineTo(x + 4 * sxs, y + 12)
        p.lineTo(x + 20 * sxs, y)
        p.close()
        fr.path_fill(p, color, a)
        q = skia.Path()
        q.moveTo(x - 4, y - 12)
        q.lineTo(x - 4, y + 12)
        q.lineTo(x - 20, y)
        q.close()
        fr.path_stroke(q, color, 1.6, a * 0.7)
    elif i == 1:  # slide: a square nudging along a track
        dx = 12 * math.sin(math.pi * act)
        fr.rrect(x - 20 + dx, y - 10, 20, 20, 4, fill=color, alpha=a)
        fr.line(x - 22, y + 16, x + 22, y + 16, color, 1.6, a * 0.7)
        fr.line(x + 12, y + 11, x + 22, y + 16, color, 1.6, a * 0.7)
        fr.line(x + 12, y + 21, x + 22, y + 16, color, 1.6, a * 0.7)
    elif i == 2:  # multiply: x rotating a quarter turn
        rot = math.pi / 4 + math.pi / 2 * ease_io(act)
        for k in range(2):
            ang = rot + k * math.pi / 2
            dx, dy = 13 * math.cos(ang), 13 * math.sin(ang)
            fr.line(x - dx, y - dy, x + dx, y + dy, color, 3.0, a)
    else:  # add: sigma
        s = 1 + 0.3 * math.sin(math.pi * act)
        pts = [(9, -12), (-9, -12), (2, 0), (-9, 12), (9, 12)]
        fr.poly([x + px * s for px, _ in pts], [y + py * s for _, py in pts], color, 2.6, a)


def draw_pills(fr, t):
    grow = ease_out(lin(t, T["one"] - 0.1, T["one"] + 0.55))
    if grow <= 0:
        return
    end_fade = 1 - smooth(lin(t, END - 0.5, END - 0.02))
    y, s = pill_layout(t)
    fr.text("ONE SIMPLE RECIPE", 960, y - 92 * s, "sans", 22, 700, "muted",
            env(t, T["one"] + 0.1, T["build"] - 1.2) * 0.9, tracking=0.24)
    lights = (T["flip"], T["slide"], T["multiply"], T["add"])
    for i in range(4):
        L = smooth(lin(t, lights[i] - 0.12, lights[i] + 0.25))
        act = lin(t, lights[i], lights[i] + 0.55)
        color = PILL_COLORS[i]
        cx = 960 + (PILL_X[i] - 960) * s
        w, h = lerp(14, PILL_W, grow) * s, lerp(14, PILL_H, grow) * s
        fr.rrect(cx - w / 2, y - h / 2, w, h, h / 2, fill=color, fill_alpha=0.1 * L, alpha=end_fade,
                 stroke=mix(TOKENS["line"], TOKENS[color], L), width=1.6, glow=0.9 * pulse(t, lights[i] - 0.1, 0.7))
        if grow < 0.6:
            continue
        a = smooth(lin(grow, 0.6, 1.0)) * end_fade
        ink = mix(TOKENS["muted"], TOKENS["ink"], L)
        icol = mix(TOKENS["muted"], TOKENS[color], L)
        left = cx - w / 2
        fr.c.save()
        fr.c.translate(left + 52 * s, y)
        fr.c.scale(s, s)
        _icon(fr, i, 0, 0, icol, a * (0.55 + 0.45 * L), act)
        fr.c.restore()
        fr.text(PILL_NAMES[i], left + 94 * s, y + 11 * s, "sans", 30 * s, 700, ink, a * (0.5 + 0.5 * L),
                align="left", tracking=0.1)


# ------------------------------------------------------------------ S03B/C: sliding boxes rig
RIG_ANCHOR = (960.0, 640.0)
TRACK_Y = 640.0
BOX_W, BOX_H = 240.0, 200.0
TRACK_L, TRACK_R, PLOT_Y = 280.0, 1640.0, 880.0
TRACE_H = 170.0


def rig_xform(t):
    cm = ease_io(lin(t, T["other2"] + 0.4, T["fourier"] - 0.3))
    s = lerp(1.0, 0.5, cm)
    ax, ay = lerp(960.0, 500.0, cm), lerp(640.0, 560.0, cm)

    def f(x, y):
        return ax + (x - RIG_ANCHOR[0]) * s, ay + (y - RIG_ANCHOR[1]) * s

    return f, s


def amber_x(t):
    p1 = ease_io(lin(t, T["build"] - 0.3, T["other2"] + 0.2))
    x = lerp(250.0, 1670.0, p1)
    p2 = ease_io(lin(t, T["sliding"] - 1.1, T["single"] - 0.2))
    return lerp(x, 250.0, p2) if p2 > 0 else x


def overlap(xa):
    lo, hi = max(xa - BOX_W / 2, 960 - BOX_W / 2), min(xa + BOX_W / 2, 960 + BOX_W / 2)
    return max(0.0, hi - lo), lo, hi


def draw_rig(fr, t):
    vis = env(t, T["build"] - 1.0, END - 0.02, 0.6, 0.45)
    if vis <= 0.003:
        return
    f, s = rig_xform(t)
    xa = amber_x(t)
    hl = 1 + 0.6 * pulse(t, T["sliding"] - 0.2, 1.2)
    # track and plot axis
    fr.line(*f(TRACK_L, TRACK_Y), *f(TRACK_R, TRACK_Y), "line", 1.4 * s, vis)
    fr.line(*f(TRACK_L, PLOT_Y), *f(TRACK_R, PLOT_Y), "grid", 1.2 * s, vis)
    # cyan box (fixed)
    x0, y0 = f(960 - BOX_W / 2, TRACK_Y - BOX_H)
    fr.rrect(x0, y0, BOX_W * s, BOX_H * s, 8 * s, fill="signal", fill_alpha=0.12, stroke="signal",
             width=2.4 * s, alpha=vis, glow=0.5)
    # amber box (sliding)
    x0, y0 = f(xa - BOX_W / 2, TRACK_Y - BOX_H)
    fr.rrect(x0, y0, BOX_W * s, BOX_H * s, 8 * s, fill="kernel", fill_alpha=0.10, stroke="kernel",
             width=2.4 * s, alpha=vis, glow=0.5)
    ov, lo, hi = overlap(xa)
    if ov > 0:
        x0, y0 = f(lo, TRACK_Y - BOX_H)
        fr.rrect(x0, y0, ov * s, BOX_H * s, 4 * s, fill="overlap", fill_alpha=min(1.0, 0.32 * hl), alpha=vis)
        fr.glow_used = True
        fr.g.drawPath(_rect_path(x0, y0, ov * s, BOX_H * s), fr._fill("overlap", min(1.0, 0.3 * vis * hl)))
    # trace: real overlap width as the box slides
    reached = max(xa, 250.0) if t < T["other2"] + 0.25 else 1670.0
    xs = np.linspace(250.0, reached, 220)
    ys = [PLOT_Y - TRACE_H * overlap(v)[0] / BOX_W for v in xs]
    pts = [f(xv, yv) for xv, yv in zip(xs, ys)]
    fr.poly([p[0] for p in pts], [p[1] for p in pts], "output", 3.0 * s, vis, glow=0.9)
    dx, dy = f(xa, PLOT_Y - TRACE_H * ov / BOX_W)
    fr.glow_dot(dx, dy, 5.5 * s, "output", alpha=vis, strength=1.2)


def _rect_path(x, y, w, h):
    p = skia.Path()
    p.addRect(skia.Rect.MakeXYWH(x, y, w, h))
    return p


# ------------------------------------------------------------------ S03C: equation highlights
EQ_POS, EQ_SIZE = (1375.0, 560.0), 72.0


@lru_cache(maxsize=1)
def make_equation():
    from faceless_champ import Equation

    return Equation(
        r"\mathcal{F}\{f \ast g\} = \mathcal{F}\{f\} \cdot \mathcal{F}\{g\}",
        font_size=EQ_SIZE,
        color=TOKENS["ink"],
        color_map={"f": TOKENS["signal"], "g": TOKENS["kernel"], r"\ast": TOKENS["overlap"]},
        position=EQ_POS,
    )


def draw_equation_marks(fr, t):
    b = make_equation().bounds
    width = b.right - b.left
    fade = 1 - smooth(lin(t, END - 0.5, END - 0.02))
    segs = ((0.0, 0.365, "overlap", T["sliding"] - 0.15, "SLIDING"),
            (0.495, 1.0, "output", T["multiplication"] - 0.35, "ONE MULTIPLICATION"))
    for lo, hi, color, t0, label in segs:
        u = ease_io(lin(t, t0, t0 + 0.6))
        if u <= 0:
            continue
        x0, x1 = b.left + width * lo, b.left + width * hi
        mid = (x0 + x1) / 2
        half = (x1 - x0) / 2 * u
        y = b.bottom + 26
        fr.line(mid - half, y, mid + half, y, color, 3.0, fade, glow=0.9)
        fr.text(label, mid, y + 44, "sans", 20, 700, color, ease_out(lin(t, t0 + 0.2, t0 + 0.6)) * fade, tracking=0.16)


# ------------------------------------------------------------------ frame function

def draw(t, size):
    fr = Frame(size)
    draw_shafts(fr, t)
    draw_nave(fr, t)
    draw_motes(fr, t)
    draw_rings(fr, t)
    draw_impulse(fr, t)
    draw_song(fr, t)
    draw_pictogram(fr, t)
    draw_title(fr, t)
    draw_montage(fr, t)
    draw_pills(fr, t)
    draw_rig(fr, t)
    draw_equation_marks(fr, t)
    return fr.finish()


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch0:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=END, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.reveal(make_equation(), at=T["fourier"] - 0.25, until=END - 0.02, style="rise", duration=0.7,
                     exit_duration=0.45)
        scene.wait_until(END)
        if audio:
            scene.add_audio(AUDIO, start=0)
    return scene


DURATION = END
STILLS = [0.6, 2.5, 5.6, 9.2, 12.4, 14.2, 16.4, 18.4, 20.5, 22.3, 25.4, 28.0, 31.2, 33.9, 35.5,
          38.4, 40.2, 43.5, 48.6, 50.4, 52.3]
