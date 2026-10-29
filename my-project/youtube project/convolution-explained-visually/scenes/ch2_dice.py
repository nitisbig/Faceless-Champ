"""CHAPTER 2 - DICE (S08-S10), 02:32.400 - 03:23.120.

S08  Counting the ways        3D die tumbles in; six flat bars; the 6x6 outcome board in 3D,
                              anti-diagonals light up per total, then plates fly into towers
                              that form the triangle histogram.
S09  Dice as a slide          flip one row of six bars, slide it across the other; the overlap
                              count drops into a real np.convolve histogram.
S10  Many dice become a bell  3D ridge-line of standardised sums of 1..12 dice (repeated
                              convolution) converging on the Gaussian.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia

from cues import AUDIO, cue
from fx import Frame, back, ease_io, ease_out, env, eyebrow, lerp, lin, mix, pulse, smooth, tokens
from space import Camera, draw_box, draw_boxes, orbit, rot_x, rot_y, text3d
from theme import H, THEME, TOKENS, W

START = cue(410)  # 152.40 "Now let's roll some dice"
END = cue(552)  # 203.12 "Now let's make our shapes smooth"

T = {
    "dice": cue(414), "fair": cue(416), "one_in_six": cue(422), "six_bars": cue(426), "flat": cue(432),
    "roll": cue(434), "add": cue(438), "two": cue(443), "only1": cue(446), "seven": cue(452),
    "six_ways": cue(455), "more": cue(457), "then": cue(461), "falls": cue(464), "single": cue(468),
    "twelve": cue(472), "watch": cue(473), "flip": cue(477), "slide": cue(484), "first": cue(489),
    "only_one": cue(491), "overlaps": cue(494), "grows": cue(497), "seven2": cue(500), "line_up": cue(503),
    "shrinks": cue(507), "flat2": cue(510), "triangle": cue(515), "add3": cue(516), "convolve": cue(521),
    "hill": cue(529), "keep": cue(530), "dice2": cue(532), "bell": cue(539), "central": cue(542),
    "conv": cue(547), "again": cue(551),
}

# ------------------------------------------------------------------ S08A: a real 3D die
FACE_VALUE = {(0, 1, 0): 5, (0, -1, 0): 2, (0, 0, -1): 1, (0, 0, 1): 6, (1, 0, 0): 3, (-1, 0, 0): 4}
FACE_AXES = {0: ((0, 0, 1), (0, 1, 0)), 1: ((1, 0, 0), (0, 0, 1)), 2: ((1, 0, 0), (0, 1, 0))}
PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}
DIE_CAM = Camera((0.0, 3.4, -10.0), (0.0, 0.0, 0.0), focal=1100.0, center=(960.0, 560.0))
CIRCLE = np.stack([np.cos(np.linspace(0, 2 * math.pi, 14)), np.sin(np.linspace(0, 2 * math.pi, 14))], 1)


def draw_die(fr, cam, center, R, pip_color, alpha, half=1.0):
    def pips(normal, pts, path):
        local = np.rint(R.T @ normal).astype(int)
        key = tuple(int(v) for v in local)
        value = FACE_VALUE[key]
        axis = int(np.argmax(np.abs(local)))
        u, v = (np.asarray(a, float) for a in FACE_AXES[axis])
        base = np.asarray(local, float) * half * 1.002
        for du, dv in PIPS[value]:
            ring = base + (du * 0.52 * half + CIRCLE[:, :1] * 0.15 * half) * u + (dv * 0.52 * half + CIRCLE[:, 1:] * 0.15 * half) * v
            world = center + ring @ R.T
            xs, ys, _ = cam.project(world)
            p = skia.Path()
            p.moveTo(float(xs[0]), float(ys[0]))
            for x, y in zip(xs[1:], ys[1:]):
                p.lineTo(float(x), float(y))
            p.close()
            fr.path_fill(p, pip_color, alpha, glow=0.5)

    draw_box(fr, cam, center, (half, half, half), "ink", "ink", alpha, R=R, fill_strength=0.10, stroke_width=1.8,
             glow=0.25, on_face=pips)


def die_pose(t, t0, x_rest, spin=1.0):
    e = ease_out(lin(t, t0, t0 + 0.95))
    y = lerp(4.5, 0.0, back(e, 0.9) if e < 1 else 1.0)
    R = rot_y(lerp(2.8 * spin, -0.55, e)) @ rot_x(lerp(-2.2 * spin, 0.0, e))
    return np.array([x_rest, y, 0.0]), R, smooth(lin(t, t0, t0 + 0.3))


BAR_X0, BAR_W, BAR_BASE, BAR_H = 1040.0, 84.0, 700.0, 300.0


def draw_s08a(fr, t):
    vis = env(t, START, T["add"] + 0.45, 0.3, 0.45)
    if vis <= 0.003:
        return
    two = ease_io(lin(t, T["roll"] - 0.1, T["roll"] + 0.7))
    # die A (cyan pips); slides left to make room for die B
    c, R, a = die_pose(t, T["fair"] - 0.35, lerp(-3.2, -1.5, two))
    draw_die(fr, DIE_CAM, c, R, "signal", a * vis)
    if t > T["roll"] - 0.2:
        c, R, a = die_pose(t, T["roll"] - 0.2, 1.5, spin=-1.0)
        draw_die(fr, DIE_CAM, c, R, "kernel", a * vis)
    # six equal bars (one in six each)
    bars_a = vis * (1 - two)
    for k in range(6):
        g = ease_out(lin(t, T["six_bars"] - 0.1 + 0.07 * k, T["six_bars"] + 0.45 + 0.07 * k))
        x = BAR_X0 + k * (BAR_W + 20)
        h = BAR_H / 6 * 2.4 * g
        if h > 0.5:
            fr.rrect(x, BAR_BASE - h, BAR_W, h, 8, fill="signal", fill_alpha=0.22, stroke="signal", width=2.0,
                     alpha=bars_a, glow=0.4)
        fr.text(str(k + 1), x + BAR_W / 2, BAR_BASE + 40, "display", 30, 600, "muted", bars_a * g)
        la = ease_out(lin(t, T["one_in_six"] - 0.1 + 0.05 * k, T["one_in_six"] + 0.3 + 0.05 * k)) * bars_a
        fr.text("1/6", x + BAR_W / 2, BAR_BASE - BAR_H / 6 * 2.4 - 20, "display", 26, 600, "signal", la)
    fl = ease_io(lin(t, T["flat"] - 0.1, T["flat"] + 0.5))
    if fl > 0:
        y = BAR_BASE - BAR_H / 6 * 2.4 - 62
        x1 = BAR_X0 - 20 + (6 * (BAR_W + 20) + 20) * fl
        fr.line(BAR_X0 - 20, y, x1, y, "output", 2.6, bars_a, glow=0.8)
        fr.text("FLAT", BAR_X0 + 3 * (BAR_W + 20) - 10, y - 22, "sans", 22, 700, "output", bars_a * fl, tracking=0.2)


# ------------------------------------------------------------------ S08B: 6x6 outcome board -> towers
def board_camera(t):
    m = ease_io(lin(t, T["more"] - 0.2, T["then"] + 0.5))
    target = np.array([0.0, lerp(0.0, 2.7, m), lerp(0.6, 0.0, m)])
    return orbit(target, lerp(12.6, 15.0, m), lerp(0.98, 0.13, m), lerp(-0.42, 0.0, m) + 0.06 * math.sin(t * 0.3),
                 focal=1100.0, center=(960.0, 455.0))


@lru_cache(maxsize=1)
def plates():
    out = []
    for i in range(6):
        for j in range(6):
            s = i + j + 2
            rank = i - max(0, s - 2 - 5)
            out.append((i, j, s, rank))
    return out


def plate_highlight(t, i, j, s):
    if s == 2:
        return "output", smooth(lin(t, T["two"] - 0.15, T["two"] + 0.2))
    if s == 7:
        k = i
        return "overlap", smooth(lin(t, T["seven"] + 0.12 * k, T["seven"] + 0.12 * k + 0.25))
    if s == 12:
        return "output", smooth(lin(t, T["single"] - 0.1, T["single"] + 0.3))
    return "line", 0.0


def draw_s08b(fr, t):
    vis = env(t, T["add"] + 0.1, T["watch"] + 0.45, 0.6, 0.55)
    if vis <= 0.003:
        return
    cam = board_camera(t)
    t0 = T["more"] - 0.25
    boxes = []
    labels = []
    for i, j, s, rank in plates():
        appear = ease_out(lin(t, T["add"] + 0.15 + 0.04 * (i + j), T["add"] + 0.15 + 0.04 * (i + j) + 0.5))
        if appear <= 0:
            continue
        m = ease_io(lin(t, t0 + 0.07 * (s - 2), t0 + 0.07 * (s - 2) + 1.3))
        bx, bz = (i - 2.5) * 1.12, (j - 2.5) * 1.12
        tx, ty = (s - 7) * 1.0, 0.46 + rank * 0.94
        hy = lerp(0.07, 0.44, m)
        center = np.array([lerp(bx, tx, m), lerp(0.07 - 0.6 * (1 - appear), ty, m), lerp(bz, 0.0, m)])
        hcol, hl = plate_highlight(t, i, j, s)
        stroke = mix(TOKENS["line"], TOKENS[hcol] if hcol in TOKENS else hcol, hl)
        if m > 0.5 and hcol == "line":
            stroke = mix(TOKENS["line"], TOKENS["output"], smooth(lin(m, 0.5, 1.0)) * 0.85)
        boxes.append({"center": center, "half": (0.46, hy, 0.46), "fill": "output" if m > 0.5 else (hcol if hl > 0.2 else "ink"),
                      "stroke": stroke, "alpha": appear * vis, "fill_strength": 0.10 + 0.25 * max(hl, m),
                      "stroke_width": 1.5 + 1.0 * hl, "glow": 0.5 * hl + 0.25 * m})
        labels.append((str(s), center + np.array([0.0, hy + 0.01, 0.0]), appear * vis * (1 - smooth(lin(m, 0.0, 0.35))),
                       TOKENS[hcol] if hl > 0.3 and hcol in TOKENS else TOKENS["muted"]))
    draw_boxes(fr, cam, boxes)
    for s, p, a, color in labels:
        if a > 0.01:
            text3d(fr, cam, s, p, 0.42, color, a)
    # die faces along the board edges (fade as the board becomes towers)
    edge_a = vis * (1 - smooth(lin(t, t0, t0 + 0.6))) * ease_out(lin(t, T["add"] + 0.3, T["add"] + 0.9))
    for k in range(6):
        text3d(fr, cam, str(k + 1), ((k - 2.5) * 1.12, 0.0, -3.75), 0.5, "signal", edge_a)
        text3d(fr, cam, str(k + 1), (-3.75, 0.0, (k - 2.5) * 1.12), 0.5, "kernel", edge_a)
    text3d(fr, cam, "DIE 1", (0.0, 0.0, -4.6), 0.34, "signal", edge_a, weight=700, family="sans")
    text3d(fr, cam, "DIE 2", (-4.7, 0.0, 0.0), 0.34, "kernel", edge_a, weight=700, family="sans")
    # totals under the towers
    tower_a = vis * smooth(lin(t, T["then"], T["then"] + 0.6))
    for s in range(2, 13):
        text3d(fr, cam, str(s), ((s - 7) * 1.0, -0.45, 0.0), 0.38, "muted" if s not in (2, 7, 12) else "ink", tower_a)
    # caption
    caps = [(T["two"] - 0.1, T["seven"] - 0.25, [("2", "output", 1), ("→", "muted", 1), ("1 way", "ink", 1)]),
            (T["seven"] - 0.1, T["falls"] - 0.3, [("7", "overlap", 1), ("→", "muted", 1), ("6 ways", "ink", 1)]),
            (T["single"] - 0.1, T["watch"] + 0.2, [("12", "output", 1), ("→", "muted", 1), ("1 way", "ink", 1)])]
    for a0, a1, items in caps:
        ca = env(t, a0, a1, 0.3, 0.3) * vis
        if ca > 0:
            tokens(fr, items, 960, 1010, 44, ca)


# ------------------------------------------------------------------ S09: dice as a slide
COLW = 70.0
SIG_X0 = 960.0 - 2.5 * COLW
SIG_BASE, AMB_BASE, OUT_BASE = 330.0, 545.0, 905.0
SIX_H = 120.0
COUNTS = np.convolve(np.ones(6), np.ones(6)).astype(int)  # [1 2 3 4 5 6 5 4 3 2 1]


def slide_p(t):
    """Slide parameter p: amber bars occupy columns [p-6, p-1]; overlap = 6 - |p - 6|."""
    p = lerp(6.0, 0.0, ease_io(lin(t, T["slide"] - 0.1, T["slide"] + 0.6)))
    for a, b, p0, p1 in ((T["only_one"] - 0.45, T["only_one"] + 0.15, 0, 1), (T["grows"] - 0.9, T["seven2"] - 0.05, 1, 6),
                         (T["shrinks"] - 0.5, T["shrinks"] + 1.2, 6, 11), (T["triangle"] - 1.6, T["triangle"] - 1.0, 11, 12.5)):
        if t >= a:
            p = lerp(p0, p1, ease_io(lin(t, a, b)) if p1 - p0 <= 1.5 else lin(t, a, b))
    return p


def draw_s09(fr, t):
    vis = env(t, T["watch"] + 0.1, T["add3"] + 0.25, 0.5, 0.6)
    if vis <= 0.003:
        return
    rows_a = vis * (1 - smooth(lin(t, T["triangle"] - 0.9, T["triangle"] - 0.2)))
    fr.text("DIE 1", 300, SIG_BASE - 40, "sans", 22, 700, "signal", rows_a, align="right", tracking=0.16)
    fr.text("DIE 2", 300, AMB_BASE - 40, "sans", 22, 700, "kernel", rows_a, align="right", tracking=0.16)
    fr.text("SUM", 300, OUT_BASE - 20, "sans", 22, 700, "output", vis, align="right", tracking=0.16)
    # signal row
    for c in range(6):
        x = SIG_X0 + c * COLW
        fr.rrect(x - COLW * 0.4, SIG_BASE - SIX_H, COLW * 0.8, SIX_H, 6, fill="signal", fill_alpha=0.2, stroke="signal",
                 width=2.0, alpha=rows_a, glow=0.3)
        fr.text(str(c + 1), x, SIG_BASE + 34, "display", 24, 600, "signal", rows_a * 0.85)
    # amber row: flip (mirror about its centre), then slide by p
    flip = ease_io(lin(t, T["flip"] - 0.1, T["flip"] + 0.7))
    p = slide_p(t)
    cos_f = math.cos(math.pi * flip)
    for k in range(6):
        base_col = 2.5 + (k - 2.5) * cos_f  # before flip: k; after flip: 5-k
        col = base_col + (p - 6)
        x = SIG_X0 + col * COLW
        w = COLW * 0.8 * max(0.08, abs(cos_f)) if 0 < flip < 1 else COLW * 0.8
        fr.rrect(x - w / 2, AMB_BASE - SIX_H, w, SIX_H, 6, fill="kernel", fill_alpha=0.2, stroke="kernel", width=2.0,
                 alpha=rows_a, glow=0.3)
        fr.text(str(k + 1), x, AMB_BASE + 34, "display", 24, 600, "kernel", rows_a * 0.85 * (abs(cos_f) if 0 < flip < 1 else 1))
        # overlap beam
        d = abs(col - round(col))
        sc = round(col)
        if 0 <= sc <= 5 and d < 0.3 and t > T["slide"] + 0.6:
            a = (1 - d / 0.3) * rows_a
            fr.line(SIG_X0 + sc * COLW, SIG_BASE + 50, x, AMB_BASE - SIX_H - 8, "overlap", 3.0, a, glow=0.8)
    fr.text("FLIP", 960, AMB_BASE + 84, "sans", 22, 700, "kernel", env(t, T["flip"] - 0.1, T["flip"] + 1.4, 0.2, 0.4) * rows_a,
            tracking=0.2)
    # live overlap count
    if T["slide"] + 0.6 < t < T["triangle"] - 0.3:
        n = max(0, 6 - abs(round(p) - 6)) if 0.5 < p < 12 else 0
        fr.text("OVERLAP", 1690, AMB_BASE - 80, "sans", 22, 700, "muted", rows_a, tracking=0.2)
        fr.text(str(n), 1690, AMB_BASE - 4, "display", 72, 600, "overlap", rows_a, glow=0.4)
    # output histogram: one bar per slide position, height = overlap count
    for n in range(1, 12):
        if t < T["only_one"] - 0.5 or (p < n - 0.02 and t < T["triangle"]):
            continue
        g = ease_out(clamp01((p - (n - 0.02)) / 0.3)) if t < T["triangle"] - 1.0 else 1.0
        x = 960 + (n - 6) * COLW
        h = COUNTS[n - 1] * 34.0 * g
        hl = n == 6 and t > T["seven2"] - 0.1
        fr.rrect(x - COLW * 0.4, OUT_BASE - h, COLW * 0.8, h, 6, fill="output", fill_alpha=0.75, alpha=vis)
        if hl:
            fr.rrect(x - COLW * 0.4 - 4, OUT_BASE - h - 4, COLW * 0.8 + 8, h + 8, 8, stroke="overlap", width=2.4,
                     alpha=vis * smooth(lin(t, T["seven2"] - 0.1, T["seven2"] + 0.3)), glow=0.8)
        fr.text(str(n + 1), x, OUT_BASE + 34, "display", 22, 600, "muted", vis * g)
    sa = env(t, T["seven2"] - 0.1, T["shrinks"] + 0.8, 0.3, 0.4) * vis
    fr.text("6 / 36", 960, OUT_BASE - 6 * 34 - 26, "display", 34, 600, "overlap", sa)
    # triangle trace
    tr = ease_io(lin(t, T["triangle"] - 0.25, T["triangle"] + 0.55))
    if tr > 0:
        xs = [960 + (n - 6) * COLW for n in range(1, 12)]
        ys = [OUT_BASE - c * 34.0 for c in COUNTS]
        xs = [xs[0] - COLW / 2] + xs + [xs[-1] + COLW / 2]
        ys = [OUT_BASE] + ys + [OUT_BASE]
        m = max(2, int(len(xs) * tr))
        fr.poly(xs[:m], [y - 14 for y in ys[:m]], "output", 3.2, vis, glow=1.0)
        fr.text("TRIANGLE", 960, OUT_BASE - 6 * 34 - 70, "sans", 24, 700, "output", vis * tr, tracking=0.22)


def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


# ------------------------------------------------------------------ S10: many dice become a bell (3D ridge-line)
LAYERS = [1, 2, 3, 4, 6, 8, 12]
SCALE_X, SCALE_Y, LAYER_DZ = 1.35, 5.2, 1.25


@lru_cache(maxsize=1)
def distributions():
    out = []
    pmf = np.array([1.0])
    die = np.ones(6) / 6
    n = 0
    for target in LAYERS:
        while n < target:
            pmf = np.convolve(pmf, die)  # repeated convolution = sum of one more die
            n += 1
        s = np.arange(n, 6 * n + 1)
        mu, sd = 3.5 * n, math.sqrt(n * 35 / 12)
        zx = (s - mu) / sd
        dens = pmf * sd
        if n <= 2:  # step outline so 1 and 2 dice read as bars / triangle
            xs, ys = [zx[0] - 0.5 / sd], [0.0]
            for z, d in zip(zx, dens):
                xs += [z - 0.5 / sd, z + 0.5 / sd]
                ys += [d, d]
            xs.append(zx[-1] + 0.5 / sd)
            ys.append(0.0)
        else:
            xs = [zx[0] - 0.5 / sd] + list(zx) + [zx[-1] + 0.5 / sd]
            ys = [0.0] + list(dens) + [0.0]
        out.append((n, np.array(xs), np.array(ys)))
    return out


def layer_times():
    return [T["add3"] - 0.1, T["add3"] - 0.1, T["convolve"] + 0.3, T["keep"], T["keep"] + 0.45, T["dice2"] + 0.35,
            T["dice2"] + 1.0]


def ridge_camera(t):
    e0 = ease_io(lin(t, T["add3"] - 0.1, T["convolve"] + 0.6))
    e1 = ease_io(lin(t, T["hill"], END))
    return orbit((0.0, 1.3, 3.6), lerp(12.5, 14.5, e1), lerp(0.02, 0.42, e0), lerp(0.0, -0.45, e1),
                 focal=1100.0, center=(960.0, 600.0))


def draw_s10(fr, t):
    vis = env(t, T["add3"] + 0.05, END, 0.6, 0.5)
    if vis <= 0.003:
        return
    cam = ridge_camera(t)
    times = layer_times()
    dists = distributions()
    order = sorted(range(len(dists)), key=lambda k: -k)  # far (newest) first
    for k in order:
        n, xs, ys = dists[k]
        g = ease_out(lin(t, times[k], times[k] + 0.7))
        if g <= 0:
            continue
        z = k * LAYER_DZ
        pts = np.stack([xs * SCALE_X, ys * SCALE_Y * g, np.full(len(xs), z)], 1)
        sx, sy, _ = cam.project(pts)
        color = mix(TOKENS["signal"], TOKENS["output"], k / (len(dists) - 1))
        p = skia.Path()
        p.moveTo(float(sx[0]), float(sy[0]))
        for x, y in zip(sx[1:], sy[1:]):
            p.lineTo(float(x), float(y))
        p.close()
        fr.path_fill(p, mix(TOKENS["bg"], color, 0.10), vis * g)
        fr.poly(sx, sy, color, 2.4, vis * g, glow=0.6)
        bx, by, _ = cam.project(np.array([[-4.6 * 1.0, 0.0, z], [4.6, 0.0, z]]))
        fr.line(bx[0], by[0], bx[1], by[1], "grid", 1.0, vis * g)
        text3d(fr, cam, f"{n} {'die' if n == 1 else 'dice'}", (-5.4, 0.15, z), 0.32, color, vis * g, weight=700,
               family="sans")
    # the Gaussian overlay on the newest layer
    ba = ease_io(lin(t, T["bell"] - 0.2, T["bell"] + 0.8))
    if ba > 0:
        z = (len(dists) - 1) * LAYER_DZ
        x = np.linspace(-3.4, 3.4, 120)
        y = np.exp(-x**2 / 2) / math.sqrt(2 * math.pi)
        m = max(2, int(len(x) * ba))
        pts = np.stack([x[:m] * SCALE_X, y[:m] * SCALE_Y + 0.02, np.full(m, z)], 1)
        sx, sy, _ = cam.project(pts)
        fr.poly(sx, sy, "#ffffff", 2.0, vis * 0.9, glow=1.2)
    ca = ease_out(lin(t, T["central"] - 0.3, T["central"] + 0.3)) * vis
    fr.text("Central limit theorem", 960, 180, "display", 60, 600, "ink", ca)
    ra = ease_out(lin(t, T["conv"] - 0.25, T["conv"] + 0.3)) * vis
    if ra > 0:
        tokens(fr, [("=", "muted", 1), ("convolution,", "overlap", 1), ("repeated", "ink", 1)], 960, 250, 40, ra)


# ------------------------------------------------------------------ assembly

def draw(t, size):
    t = t + START
    fr = Frame(size)
    draw_s08a(fr, t)
    draw_s08b(fr, t)
    draw_s09(fr, t)
    draw_s10(fr, t)
    eyebrow(fr, t, "02 · DICE", START + 0.15)
    return fr.finish()


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch2:{Path(__file__).stat().st_mtime_ns}"
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
STILLS = [153.0, 155.6, 158.0, 159.8, 161.2, 163.4, 166.6, 168.4, 169.6, 171.8, 174.0, 175.4, 178.0, 180.0,
          182.5, 184.0, 186.5, 189.2, 190.3, 192.5, 195.6, 197.8, 199.0, 201.5]
