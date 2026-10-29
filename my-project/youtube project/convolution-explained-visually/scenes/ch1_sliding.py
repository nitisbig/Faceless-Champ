"""CHAPTER 1 - SLIDING BY HAND (S04-S07), 00:53.080 - 02:32.400.

S04  Smoothing a jumpy week       moving average with a real 3-day kernel
S05  The smallest example         [1 2 3] * [1 1] on the Slide Rig, every step on its word
S06  Long multiplication          Manim column multiplication (transparent) + lime tiles + arcs
S07  Why flip? Listening back     echo timeline: kernel weights reach into the past

Skia graphics in one FunctionSource; S06 digits come from a prepared Manim clip
played through a Viewport on top. All times are narration source-clock seconds.
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia

from cues import AUDIO, cue, word
from fx import (
    Frame, back, clamp, ease_in, ease_io, ease_out, env, eyebrow, lerp, lin, mix, pulse, smooth, tile, tokens,
)
from theme import H, THEME, TOKENS, W

ROOT = Path(__file__).resolve().parents[1]
START = cue(145)  # 53.08 "Let's"
END = cue(410)  # 152.40 "Now let's roll some dice"

T = {
    "hand": cue(153), "week": cue(156), "jump": cue(160),
    "v0": cue(162), "v1": cue(163), "v2": cue(164), "v3": cue(165),
    "take": cue(170), "three": cue(171), "multiply": cue(176), "third": cue(179), "add": cue(182),
    "then": cue(185), "slide": cue(186), "repeat": cue(191), "that": cue(192), "window": cue(194),
    "w1": cue(197), "w2": cue(199), "w3": cue(201), "kernel": cue(206),
    "sliding": cue(208), "signal": cue(213), "multiplying": cue(214), "adding": cue(216),
    "convolution": cue(223), "lets": cue(225),
    # S05
    "here_signal": cue(232), "s1": cue(237), "s2": cue(238), "s3": cue(239),
    "here_kernel": cue(244), "k1": cue(248), "k2": cue(249),
    "flip": cue(252), "slide_in": cue(258), "first": cue(269), "only": cue(273),
    "p0a": cue(277), "p0g": cue(281),
    "slide2": cue(282), "two_pairs": cue(285), "p1a": cue(288), "p1b": cue(291), "p1g": cue(296),
    "slide3": cue(297), "p2a": cue(299), "p2b": cue(302), "p2g": cue(307),
    "last": cue(309), "only3": cue(313), "p3g": cue(318),
    "so": cue(319), "a0": cue(323), "a1": cue(324), "a2": cue(325), "a3": cue(326),
    # S06
    "now": cue(327), "surprise": cue(330), "mult": cue(331), "by": cue(333), "eleven": cue(334),
    "get": cue(337), "d0": cue(338), "d1": cue(339), "d2": cue(340), "d3": cue(341),
    "same": cue(343), "long": cue(345), "is_conv": cue(348), "sliding_digits": cue(349), "but": cue(356),
    # S07
    "why": cue(357), "echo": cue(364), "instant": cue(372), "quieter": cue(378), "fainter": cue(386),
    "output": cue(392), "backwards": cue(394), "flip2": cue(399), "line_up": cue(403), "past": cue(409),
}

# ------------------------------------------------------------------ S04: smoothing a jumpy week
TEMPS = np.array([20, 24, 18, 26, 21, 25, 19], float)
SMOOTH = np.convolve(TEMPS, np.ones(3) / 3, mode="valid")  # centred on days 1..5
DAYS = "MTWTFSS"
PX0, PSTEP = 420.0, 180.0
VAL_T = [T["v0"], T["v1"], T["v2"], T["v3"], T["v3"] + 0.35, T["v3"] + 0.5, T["v3"] + 0.65]


def day_x(i):
    return PX0 + i * PSTEP


def temp_y(v):
    return lerp(700.0, 380.0, (v - 16.0) / 12.0)


def window_pos(t):
    """Index of the window's first day (fractional while sliding)."""
    steps = [T["slide"], T["repeat"] - 0.55, T["repeat"] + 0.05, T["repeat"] + 0.45]
    pos = 0.0
    for k, s in enumerate(steps):
        dur = 0.6 if k == 0 else 0.35
        pos += back(lin(t, s, s + dur), 1.2) if t >= s else 0.0
    return pos


def smooth_done(t):
    """How many smoothed outputs exist (window has visited them)."""
    first = T["add"] + 0.35
    if t < first:
        return 0
    steps = [T["slide"] + 0.6, T["repeat"] - 0.2, T["repeat"] + 0.4, T["repeat"] + 0.8]
    return 1 + sum(1 for s in steps if t >= s)


def draw_s04(fr, t):
    vis = env(t, START, T["lets"] + 0.05, 0.5, 0.45)
    if vis <= 0.003:
        return
    dim_plot = 1 - 0.55 * smooth(lin(t, T["that"], T["that"] + 0.6)) + 0.55 * smooth(
        lin(t, T["sliding"] - 0.2, T["sliding"] + 0.4))
    # axes + day labels
    axis_a = ease_out(lin(t, T["hand"], T["hand"] + 0.7)) * vis
    fr.line(PX0 - 80, 740, PX0 + 6 * PSTEP + 80, 740, "line", 1.4, axis_a)
    for i, d in enumerate(DAYS):
        fr.text(d, day_x(i), 790, "sans", 24, 600, "muted", axis_a * 0.9)
        fr.line(day_x(i), 734, day_x(i), 746, "line", 1.4, axis_a)
    fr.text("TEMPERATURE", PX0 - 80, 270, "sans", 20, 700, "signal", axis_a * 0.8 * dim_plot, align="left",
            tracking=0.18)
    # raw points + jumpy line
    shown = [i for i in range(7) if t >= VAL_T[i] - 0.1]
    if shown:
        xs = [day_x(i) for i in shown]
        ys = [temp_y(TEMPS[i]) for i in shown]
        last = shown[-1]
        u = ease_out(lin(t, VAL_T[last] - 0.1, VAL_T[last] + 0.25))
        if len(xs) > 1:
            xs[-1] = lerp(xs[-2], xs[-1], u)
            ys[-1] = lerp(ys[-2], ys[-1], u)
        fr.poly(xs, ys, "signal", 2.6, vis * dim_plot, glow=0.55)
        for i in shown:
            a = ease_out(lin(t, VAL_T[i] - 0.1, VAL_T[i] + 0.3)) * vis * dim_plot
            fr.glow_dot(day_x(i), temp_y(TEMPS[i]), 7, "signal", alpha=a, strength=0.9)
            big = i < 4
            fr.text(f"{int(TEMPS[i])}", day_x(i), temp_y(TEMPS[i]) - 26, "display", 34 if big else 26, 600,
                    "ink" if big else "muted", a * (1.0 if big else 0.8))
    # kernel window (3 days)
    wa = ease_out(lin(t, T["take"], T["take"] + 0.5)) * vis
    wpos = window_pos(t)
    if wa > 0:
        x0 = day_x(wpos) - 70
        fr.rrect(x0, 300, 2 * PSTEP + 140, 470, 26, fill="kernel", fill_alpha=0.05 * wa, stroke="kernel",
                 width=2.2, alpha=wa * (1 - 0.6 * smooth(lin(t, T["that"], T["that"] + 0.5))), glow=0.4)
    # one-third chips under the three days in the window (first pass only), then they rise into the kernel row
    chip_a = ease_out(lin(t, T["three"] + 0.2, T["three"] + 0.6)) * vis
    rise = ease_io(lin(t, T["window"] - 0.4, T["window"] + 0.5))
    for j in range(3):
        if chip_a <= 0:
            break
        cx0, cy0 = day_x(wpos + j), 852.0
        cx1, cy1 = 960 + (j - 1) * 150.0, 210.0
        cx, cy = lerp(cx0, cx1, rise), lerp(cy0, cy1, rise)
        size = lerp(66, 110, rise)
        lit = pulse(t, (T["w1"], T["w2"], T["w3"])[j] - 0.1, 0.6)
        tile(fr, cx, cy, size, "1/3", "kernel", chip_a, lit=lit, font_scale=0.36)
    # multiply sparks + working line on the first pass
    if T["multiply"] - 0.2 < t < T["slide"] + 0.3:
        for j in range(3):
            p = pulse(t, T["multiply"] + 0.08 * j, 0.7)
            if p > 0:
                fr.circle(day_x(j), temp_y(TEMPS[j]), 12 + 26 * p, "overlap", 2.0, p * vis, glow=0.8)
        wa2 = env(t, T["multiply"] - 0.1, T["slide"] + 0.2, 0.35, 0.3) * vis
        add = ease_out(lin(t, T["add"] - 0.1, T["add"] + 0.35))
        items = [("1/3·20", "ink", 1 - add), ("+", "muted", 1 - add), ("1/3·24", "ink", 1 - add),
                 ("+", "muted", 1 - add), ("1/3·18", "ink", 1 - add), ("=", "muted", 1.0),
                 (f"{SMOOTH[0]:.1f}", "output", add)]
        tokens(fr, items, 960, 960, 38, wa2)
    # smoothed (output) line, built as the window visits each day
    done = smooth_done(t)
    if done:
        xs = [day_x(i + 1) for i in range(done)]
        ys = [temp_y(v) for v in SMOOTH[:done]]
        boost = 1 + 0.7 * pulse(t, T["convolution"] - 0.15, 1.0)
        if len(xs) > 1:
            fr.poly(xs, ys, "output", 3.0, vis, glow=0.6 * boost)
        for x, y in zip(xs, ys):
            fr.glow_dot(x, y, 6.5, "output", alpha=vis, strength=0.8 * boost)
    # labels for the definition (S04D)
    la = env(t, T["sliding"] - 0.1, T["lets"], 0.4, 0.4) * vis
    if la > 0:
        fr.text("SIGNAL", day_x(6) + 40, temp_y(TEMPS[6]) + 30, "sans", 22, 700, "signal", la, align="left",
                tracking=0.16)
        fr.text("KERNEL", 960, 132, "sans", 22, 700, "kernel", la, tracking=0.16)
        if done >= 5:
            fr.text("OUTPUT", day_x(6) + 40, temp_y(SMOOTH[4]) - 22, "sans", 22, 700, "output", la, align="left",
                    tracking=0.16)
    ka = env(t, T["kernel"] - 0.15, T["sliding"] - 0.1, 0.3, 0.3) * vis
    fr.text("kernel", 960, 330, "display", 44, 600, "kernel", ka, glow=0.4)
    ca = ease_out(lin(t, T["convolution"] - 0.15, T["convolution"] + 0.4)) * env(t, START, T["lets"] + 0.05, 0.1, 0.45)
    if ca > 0:
        tokens(fr, [("signal", "signal", 1), ("⊛", "overlap", 1), ("kernel", "kernel", 1), ("=", "muted", 1),
                    ("output", "output", 1)], 960, 960, 40, ca)


# ------------------------------------------------------------------ S05: the smallest example (Slide Rig)
COL = 150.0
TILE = 128.0
SIG_Y, KER_Y, OUT_Y = 400.0, 575.0, 750.0
SIGNAL = [1, 2, 3]
KERNEL = [1, 1]
OUTPUT = list(np.convolve(SIGNAL, KERNEL))  # [1, 3, 5, 3]
STEP_T = [T["first"] - 0.15, T["slide2"], T["slide3"], T["last"]]
OUT_T = [T["p0g"] + 0.1, T["p1g"] + 0.15, T["p2g"] + 0.15, T["p3g"]]


def col_x(c):
    return 960 + (c - 1) * COL


def kernel_center(t):
    """x of the kernel pair's centre; it parks at the centre, slides off left, then steps right."""
    park = col_x(0.5)
    off_left = col_x(-1.5)
    x = lerp(park, off_left, ease_io(lin(t, T["slide_in"] - 0.1, T["slide_in"] + 0.8)))
    for j, s in enumerate(STEP_T):
        target = col_x(j - 0.5)
        prev = col_x(j - 1.5)
        u = lin(t, s, s + 0.55)
        if u > 0:
            x = lerp(prev, target, back(u, 1.15))
    return x


def kernel_pos(t):
    """Current integer step (or -1 before the first position)."""
    pos = -1
    for j, s in enumerate(STEP_T):
        if t >= s + 0.45:
            pos = j
    return pos


def draw_s05(fr, t):
    to_right = ease_io(lin(t, T["now"] - 0.05, T["surprise"] + 0.2))
    vis = env(t, T["lets"] - 0.05, T["now"] + 0.9, 0.45, 0.6)
    if vis <= 0.003:
        draw_output_tiles(fr, t, to_right)
        return
    rows_a = vis * (1 - to_right)
    final = smooth(lin(t, T["so"], T["so"] + 0.4))
    pos = kernel_pos(t)
    # row labels
    for label, y, color in (("SIGNAL", SIG_Y, "signal"), ("KERNEL", KER_Y, "kernel"), ("OUTPUT", OUT_Y, "output")):
        t0 = {"signal": T["here_signal"], "kernel": T["here_kernel"], "output": T["p0g"] - 0.3}[color]
        a = ease_out(lin(t, t0 - 0.2, t0 + 0.3)) * (rows_a if color != "output" else vis * (1 - to_right))
        fr.text(label, 380, y + 8, "sans", 22, 700, color, a, align="right", tracking=0.16)
    # signal tiles
    for i, v in enumerate(SIGNAL):
        a = ease_out(lin(t, (T["s1"], T["s2"], T["s3"])[i] - 0.15, (T["s1"], T["s2"], T["s3"])[i] + 0.25))
        lit = 0.0
        if pos >= 0:
            lit = 1.0 if i in (pos - 1, pos) else 0.0
        dim = 1.0 if pos < 0 or lit or t > T["so"] else 0.4
        dim = lerp(dim, 0.45, final)
        sc = back(a, 2.0) if a < 1 else 1.0
        tile(fr, col_x(i), SIG_Y, TILE * max(sc, 0.01), str(v), "signal", a * rows_a * dim, lit=lit * 0.6)
    # kernel tiles (with a/b order markers so the flip is visible)
    ka = [ease_out(lin(t, T["k1"] - 0.15, T["k1"] + 0.25)), ease_out(lin(t, T["k2"] - 0.15, T["k2"] + 0.25))]
    flip = ease_io(lin(t, T["flip"] - 0.05, T["flip"] + 0.75))
    theta = math.pi * flip
    kc = kernel_center(t)
    for j in range(2):
        side = -1 if j == 0 else 1
        off = side * COL / 2 * math.cos(theta)
        sx = math.cos(theta)
        depth = 1 + 0.08 * math.sin(theta) * (-side)
        a = ka[j] * rows_a * lerp(1.0, 0.45, final)
        tile(fr, kc + off, KER_Y, TILE * depth, str(KERNEL[j]), "kernel", a, scale_x=sx,
             lit=0.5 if pos >= 0 and t > STEP_T[min(pos, 3)] + 0.4 else 0.0)
        mark = "a" if j == 0 else "b"
        fr.text(mark, kc + off, KER_Y + TILE / 2 + 30, "sans", 20, 600, "muted", a * 0.9)
    fr.text("FLIP", kc, KER_Y - TILE / 2 - 18, "sans", 20, 700, "kernel",
            env(t, T["flip"] - 0.1, T["flip"] + 1.4, 0.2, 0.4) * rows_a, tracking=0.2)
    # overlap beams, products, sums, output tiles
    steps = [
        (T["only"], [(0, 0)], [(T["p0a"], "1×1")], T["p0g"]),
        (T["two_pairs"], [(0, 1), (1, 0)], [(T["p1a"], "1×1"), (T["p1b"], "2×1")], T["p1g"]),
        (T["p2a"] - 0.5, [(1, 1), (2, 0)], [(T["p2a"], "2×1"), (T["p2b"], "3×1")], T["p2g"]),
        (T["only3"], [(2, 1)], [(T["only3"] + 0.3, "3×1")], T["p3g"]),
    ]
    for j, (beam_t, pairs, prods, sum_t) in enumerate(steps):
        if pos != j or t > (STEP_T[j + 1] if j < 3 else T["so"]):
            continue
        for si, ki in pairs:
            x = col_x(si)
            p = ease_out(lin(t, beam_t - 0.1, beam_t + 0.3))
            fr.line(x, SIG_Y + TILE / 2 + 4, x, KER_Y - TILE / 2 - 4, "overlap", 3.0, p * rows_a, glow=0.9)
            fr.glow_dot(x, (SIG_Y + KER_Y) / 2, 6, "overlap", alpha=p * rows_a, strength=1.0)
        # working line under the rig
        items = []
        for k, (pt_, txt) in enumerate(prods):
            a = ease_out(lin(t, pt_ - 0.1, pt_ + 0.25))
            if k:
                items.append(("+", "muted", a))
            items.append((txt, "ink", a))
        g = ease_out(lin(t, sum_t - 0.15, sum_t + 0.2))
        items += [("=", "muted", g), (str(OUTPUT[j]), "output", g)]
        tokens(fr, items, 960, 920, 44, rows_a)
    draw_output_tiles(fr, t, to_right)


def draw_output_tiles(fr, t, to_right):
    vis = env(t, T["lets"] - 0.05, T["but"] + 0.1, 0.45, 0.6)
    if vis <= 0.003:
        return
    tiles_x = [1246.0 + 116.0 * j for j in range(4)]
    for j in range(4):
        a = ease_out(lin(t, OUT_T[j] - 0.15, OUT_T[j] + 0.3))
        if a <= 0:
            continue
        x0, y0, s0 = col_x(j - 0.5), OUT_Y - 30 * (1 - back(a, 1.6)), TILE
        x = lerp(x0, tiles_x[j], to_right)
        y = lerp(y0, float(ROWS["result"]), to_right)
        size = lerp(s0, 100.0, to_right)
        lit = pulse(t, (T["a0"], T["a1"], T["a2"], T["a3"])[j] - 0.1, 0.6) + 0.8 * pulse(t, T["a3"] + 0.5, 0.9)
        lit += pulse(t, (T["d0"], T["d1"], T["d2"], T["d3"])[j] - 0.05, 0.6) + pulse(t, T["same"], 0.8)
        tile(fr, x, y, size, str(OUTPUT[j]), "output", a * vis * s06_fade(t), lit=min(1.0, lit))


def s06_fade(t):
    return 1 - smooth(lin(t, T["but"] - 0.6, T["but"] + 0.05))


# ------------------------------------------------------------------ S06: skia part (arcs + caption)
MANIM_T0 = cue(327) - 0.2  # clip starts just before "Now here's the surprise"
X_RIGHT, CW = 860.0, 80.0
ROWS = {"top": 330, "mult": 402, "line1": 440, "p1": 492, "p2": 556, "line2": 596, "result": 656, "sums": 728}


def result_digit_x(i):
    """x of the i-th (left-to-right) digit of 1353 in the Manim layout."""
    col = 3 - i
    return X_RIGHT - col * CW - CW / 2


def draw_s06(fr, t):
    vis = env(t, T["now"], T["but"] + 0.05, 0.3, 0.6)
    if vis <= 0.003:
        return
    tiles_x = [1246.0 + 116.0 * j for j in range(4)]
    for i in range(4):
        t0 = (T["d0"], T["d1"], T["d2"], T["d3"])[i]
        u = ease_io(lin(t, t0 - 0.1, t0 + 0.45))
        if u <= 0:
            continue
        x0, x1, y = result_digit_x(i), tiles_x[i], ROWS["result"] + 40.0
        mid = (x0 + x1) / 2
        p = skia.Path()
        n = 40
        for k in range(n + 1):
            s = k / n * u
            x = lerp(x0, x1, s)
            yy = y + 150 * 4 * s * (1 - s) * (1 - 0.15 * i)
            (p.moveTo if k == 0 else p.lineTo)(x, yy)
        arc_fade = 1 - smooth(lin(t, T["long"] - 0.3, T["long"] + 0.3))
        fr.path_stroke(p, "overlap", 2.2, vis * arc_fade * (0.55 + 0.45 * pulse(t, T["same"], 0.8)), glow=0.6)
    ca = ease_out(lin(t, T["is_conv"] - 0.25, T["is_conv"] + 0.3)) * vis
    if ca > 0:
        tokens(fr, [("long multiplication", "ink", 1), ("=", "muted", 1), ("convolution", "overlap", 1)],
               960, 930, 40, ca)
    fr.text("SAME DIGITS", 1420, ROWS["result"] - 90, "sans", 22, 700, "output", env(t, T["same"] - 0.1, T["long"] + 0.2, 0.3, 0.4) * vis,
            tracking=0.2)


# ------------------------------------------------------------------ S07: why flip? listening backwards
AX_L, AX_R, AX_Y, NOW_X, STEP = 240.0, 1680.0, 600.0, 1320.0, 230.0
EVENTS = [0.85, 1.0, 0.62, 0.92, 0.7]  # cyan sound events at NOW, NOW-1, NOW-2 ...
WEIGHTS = [1.0, 0.6, 0.3]


def draw_s07(fr, t):
    vis = env(t, T["but"] - 0.1, END, 0.4, 0.5)
    if vis <= 0.003:
        return
    # question title
    qa = env(t, T["but"] - 0.05, T["output"] - 0.3, 0.35, 0.5) * vis
    fr.text("Why flip the kernel?", 960, 220, "display", 64, 600, "ink", qa)
    # axis + NOW playhead
    ax = ease_io(lin(t, T["echo"] - 0.6, T["echo"] + 0.4))
    fr.line(lerp(NOW_X, AX_L, ax), AX_Y, NOW_X + 260, AX_Y, "line", 1.6, vis * min(1, ax * 2))
    fr.text("← PAST", AX_L + 10, AX_Y + 120, "sans", 22, 700, "muted", ax * vis, align="left", tracking=0.2)
    na = ease_out(lin(t, T["echo"] - 0.3, T["echo"] + 0.2)) * vis
    fr.line(NOW_X, AX_Y - 260, NOW_X, AX_Y, "ink", 2.0, na * 0.9, glow=0.4)
    fr.text("NOW", NOW_X, AX_Y - 280, "sans", 24, 700, "ink", na, tracking=0.2)
    for k in range(3):  # echo rings around NOW
        age = t - (T["echo"] + 0.2 + 0.5 * k)
        if 0 < age < 2.2:
            fr.circle(NOW_X, AX_Y, 18 + 90 * age, "signal", 1.6, (1 - age / 2.2) * 0.6 * vis, glow=0.5)
    # cyan sound events (stems above the axis)
    for k, h in enumerate(EVENTS):
        x = NOW_X - k * STEP
        a = ease_out(lin(t, T["echo"] + 0.1 + 0.08 * k, T["echo"] + 0.5 + 0.08 * k)) * vis
        if a <= 0 or x < AX_L:
            continue
        lit = 0.0
        if k < 3:
            lit = smooth(lin(t, (T["instant"], T["quieter"], T["fainter"])[k] - 0.2,
                             (T["instant"], T["quieter"], T["fainter"])[k] + 0.2))
        top = AX_Y - 200 * h
        fr.line(x, AX_Y, x, top, "signal", 3.0, a * (0.4 + 0.6 * lit), glow=0.5 * lit)
        fr.glow_dot(x, top, 7, "signal", alpha=a * (0.45 + 0.55 * lit), strength=0.8 * lit)
    # kernel weights reach back from NOW (amber bars below the axis)
    for k, w in enumerate(WEIGHTS):
        t0 = (T["instant"], T["quieter"], T["fainter"])[k]
        a = ease_out(lin(t, t0 - 0.2, t0 + 0.35)) * vis
        if a <= 0:
            continue
        x = NOW_X - k * STEP
        bot = AX_Y + 170 * w * a
        fr.rrect(x - 20, AX_Y + 6, 40, bot - AX_Y, 6, fill="kernel", fill_alpha=0.85 * a, alpha=1.0)
        fr.text(f"{w:.1f}", x, bot + 36, "display", 28, 600, "kernel", a)
        if k:
            fr.line(x + 20, AX_Y + 18, NOW_X - 20 - (k - 1) * STEP, AX_Y + 18, "kernel", 1.2, a * 0.35)
    # output gathered at NOW
    oa = ease_out(lin(t, T["output"] - 0.2, T["output"] + 0.3)) * vis
    if oa > 0:
        val = sum(w * EVENTS[k] for k, w in enumerate(WEIGHTS))
        fr.glow_dot(NOW_X + 90, AX_Y - 120 * val, 8, "output", alpha=oa, strength=1.2)
        fr.line(NOW_X + 90, AX_Y, NOW_X + 90, AX_Y - 120 * val, "output", 3.0, oa, glow=0.6)
        fr.text("OUTPUT", NOW_X + 90, AX_Y - 120 * val - 26, "sans", 20, 700, "output", oa, tracking=0.16)
    # magenta sweep: reading backwards in time
    su = ease_io(lin(t, T["backwards"] - 0.2, T["backwards"] + 0.9))
    if 0 < su < 1 or (su >= 1 and t < T["flip2"]):
        x = lerp(NOW_X, NOW_X - 2 * STEP - 60, su)
        fade = 1 - smooth(lin(t, T["backwards"] + 0.9, T["flip2"]))
        fr.line(NOW_X, AX_Y + 250, x, AX_Y + 250, "overlap", 3.0, vis * fade, glow=0.8)
        fr.line(x, AX_Y + 250, x + 16, AX_Y + 240, "overlap", 3.0, vis * fade)
        fr.line(x, AX_Y + 250, x + 16, AX_Y + 260, "overlap", 3.0, vis * fade)
    # kernel as written [1.0 0.6 0.3] flips into time order [0.3 0.6 1.0] above the bars
    wa = ease_out(lin(t, T["output"] + 0.3, T["output"] + 0.8)) * vis
    if wa > 0:
        flip = ease_io(lin(t, T["flip2"] - 0.15, T["flip2"] + 0.6))
        theta = math.pi * flip
        cx = lerp(960.0, NOW_X - STEP, ease_io(lin(t, T["flip2"] + 0.5, T["line_up"] + 0.2)))
        gap = lerp(140.0, STEP, ease_io(lin(t, T["flip2"] + 0.5, T["line_up"] + 0.2)))
        for k, w in enumerate(WEIGHTS):
            off = (k - 1) * gap * math.cos(theta)
            tile(fr, cx + off, 230, 104, f"{w:.1f}", "kernel", wa, scale_x=math.cos(theta), font_scale=0.34,
                 lit=pulse(t, T["line_up"], 0.9))
        lab = "KERNEL AS WRITTEN" if flip < 0.5 else "FLIPPED: LINED UP WITH TIME"
        fr.text(lab, cx, 140, "sans", 22, 700, "kernel", wa, tracking=0.2)
        la = ease_out(lin(t, T["line_up"], T["line_up"] + 0.5)) * vis
        for k in range(3):
            x = NOW_X - k * STEP
            for y0 in range(300, int(AX_Y - 210), 22):
                fr.line(x, y0, x, y0 + 10, "kernel", 1.4, la * 0.6)


# ------------------------------------------------------------------ assembly

def draw(t, size):
    t = t + START  # FunctionSource time -> narration clock
    fr = Frame(size)
    draw_s04(fr, t)
    draw_s05(fr, t)
    draw_s06(fr, t)
    draw_s07(fr, t)
    eyebrow(fr, t, "01 · SLIDING BY HAND", START + 0.1)
    return fr.finish()


def manim_clip():
    """S06 Manim clip. On render machines without Manim, play a bundled prepared clip instead:
    FC_MANIM_PREPARED=<folder with manifest.json>.  FC_MANIM_4K=1 prepares at 3840x2160."""
    import os

    bundled = os.environ.get("FC_MANIM_PREPARED")
    if bundled:
        from faceless_champ.prepared import PreparedFrameSource

        return PreparedFrameSource(bundled)
    from faceless_champ.integrations.manim import ManimRenderOptions, ManimSceneSpec, prepare_manim

    rel = {k: round(v - MANIM_T0, 3) for k, v in {
        "top": T["mult"] - 0.25, "mult": T["by"], "line1": T["eleven"] + 0.3, "result": T["get"] - 0.1,
        "d0": T["d0"], "d1": T["d1"], "d2": T["d2"], "d3": T["d3"], "same": T["same"],
        "columns": T["long"], "slide": T["sliding_digits"] - 0.1, "out": T["but"] - 0.55, "end": T["but"] + 0.1,
    }.items()}
    spec = ManimSceneSpec(
        str(ROOT / "manim" / "long_mult.py"), "LongMult", inputs=("fonts/SpaceGrotesk.ttf",),
        parameters={
            "times": rel,
            "colors": {k: TOKENS[k] for k in ("signal", "kernel", "output", "overlap", "line")},
            "x_right": X_RIGHT, "cw": CW, "size": 40, "rows": ROWS,
        },
    )
    four_k = os.environ.get("FC_MANIM_4K") == "1"
    options = ManimRenderOptions(width=3840 if four_k else 1920, height=2160 if four_k else 1080, fps=30, background=None)
    return prepare_manim(spec, cache_dir=ROOT / "output" / "cache" / "manim", options=options, python=sys.executable)


def build(audio: bool = True, local: bool = True):
    """Chapter scene. ``local=True``: scene time 0 = narration START (for chapter previews)."""
    from faceless_champ import FunctionSource, Scene, Viewport

    key = f"ch1:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=END - START, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        frames = manim_clip()
        with scene.at(MANIM_T0 - START):
            scene.add(Viewport(frames, width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(END - START)
        if audio:
            scene.add_audio(AUDIO, start=0, trim_start=START)
    return scene


OFFSET = START
DURATION = END - START
STILLS = [s for s in (55.5, 61.2, 65.9, 69.6, 73.0, 77.5, 80.8, 87.0, 91.0, 92.2, 95.0, 100.5, 106.9,
                              111.6, 115.8, 119.3, 125.2, 128.0, 132.8, 134.4, 138.0, 143.5, 146.8, 148.2,
                              150.2, 151.6)]
