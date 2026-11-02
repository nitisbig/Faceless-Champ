"""CHAPTER 2 - ADDING DICE: THE CENTRAL LIMIT THEOREM (S08-S12), 01:56.620 (#343 "But") - 03:10.500 (#560 "So").

S08  One die, two dice   the L/R coin spins, wobbles on "messier" and folds into a die -> one die: six level bars, a
                         ghost bell that does not fit -> two dice roll, 3 + 4 = 7 -> the 6 x 6 grid of sums, the
                         sevens light (6 pairs), the corner (1 pair) -> the cells slide down and stack into 2..12.
S09  Three, ten dice     the stack morphs to the exact sum of 3 dice, then 10 dice -> the bell snaps on.
S10  The lopsided die    a die whose six face glows -> 0.1 x 5 and 0.5 -> n = 2, 3, 5, 10, 30, re-standardized ->
                         the skew melts -> the same bell, and the fair-dice bell drops exactly onto it.
S11  The theorem         title -> eight different small distributions with + signs -> they pour into one bell ->
                         they keep changing, the bell does not -> they wash out -> mu and sigma dials survive.
S12  Addition is bell    the five S02 panels flash past -> one height, genes, food, sleep, health -> up and down
                         nudges stack into a random walk -> a crowd does it fast and pours a histogram -> + -> bell.

Every histogram is an exact distribution (numpy.convolve); morphs move mass, they never pop.
The dice are real 3D boxes projected with space.Camera and drawn in skia (crisp, fast, deterministic).
"""

from __future__ import annotations

import contextlib
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
from components import crowd
from faceless_champ.draw import hud
from components.bell import Bell, pdf
from components.dials import dial_pair
from components.histogram import LOPSIDED, Axes, bars_from, die_pmf, draw_bars, label_bars, morph, stagger, sum_pmf
from cues import AUDIO, beat, cue
from faceless_champ.draw import Frame, back, clamp, ease_in, ease_io, ease_out, env, lin, mix, smooth, text_path
from pv3d.solids import FACES, PIPS, rotation
from scipy.spatial.transform import Rotation
from faceless_champ.draw.space import Camera, draw_box
from theme import THEME, H, W

from scenes import ch1_paths as ch1

START = cue(343)  # 116.62 "But a peg is a perfectly fair coin."
END = cue(560)  # 190.50 "So ..."

b = beat


@contextlib.contextmanager
def view(fr, m):
    if m is None:
        yield
        return
    fr.c.save()
    fr.g.save()
    fr.c.concat(m)
    fr.g.concat(m)
    try:
        yield
    finally:
        fr.c.restore()
        fr.g.restore()


@contextlib.contextmanager
def faded(fr, a):
    """Group opacity for everything drawn inside (crisp and glow canvases)."""
    fr.c.saveLayer(None, skia.Paint(Alphaf=a))
    fr.g.saveLayer(None, skia.Paint(Alphaf=a))
    try:
        yield
    finally:
        fr.c.restore()
        fr.g.restore()


def translate(dx, dy):
    m = skia.Matrix()
    m.setTranslate(dx, dy)
    return m


def lerp(a, b_, u):
    return a + (b_ - a) * u


def lerp_axes(a: Axes, c: Axes, u):
    return Axes(lerp(a.cx, c.cx, u), lerp(a.floor, c.floor, u), lerp(a.unit, c.unit, u), lerp(a.hscale, c.hscale, u))


# ------------------------------------------------------------------ the 3D die

TILT = rotation(-0.42, 0.55, 0.0)  # shows the top and the right side as well as the front face
BASE = {1: (0, 0, 0), 6: (0, math.pi, 0), 2: (0, math.pi / 2, 0), 5: (0, -math.pi / 2, 0), 3: (-math.pi / 2, 0, 0),
        4: (math.pi / 2, 0, 0)}
DIE_HALF = 1.1  # world units; 100 px per unit at depth 0


def shown(value):
    """Die orientation (tilted) with ``value`` on the front face."""
    return TILT @ rotation(*BASE[value])


def euler(R):
    z, y, x = Rotation.from_matrix(R).as_euler("ZYX")
    return np.array([x, y, z])


def tumble(R0, R1, e, turns=(2, 1, 1)):
    """Spin from orientation R0 to R1 (Euler path plus whole turns, so it lands exactly)."""
    a0, a1 = euler(R0), euler(R1) + 2 * math.pi * np.asarray(turns, float)
    a = a0 + (a1 - a0) * e
    return rotation(*a)


def face_value(R, normal):
    local = R.T @ normal
    return max(FACES, key=lambda v: float(np.dot(local, FACES[v][0])))


def draw_die(fr, sx, sy, s, R, alpha=1.0, glow=0.35, hot=None, hot_a=0.0):
    """A glass die centred on screen point (sx, sy), ``s`` x the base size. ``hot`` face glows (S10's six)."""
    if alpha <= 0.003 or s <= 0.01:
        return
    half = DIE_HALF * s
    center = np.zeros(3)
    cam = Camera(eye=(0.0, 0.0, -10.0), target=(0.0, 0.0, 0.0), focal=1000.0, center=(sx, sy))  # head-on anywhere

    def on_face(normal, pts, path):
        v = face_value(R, normal)
        n, u, w = (np.asarray(a, float) for a in FACES[v])
        if hot == v and hot_a > 0:
            fr.path_fill(path, "ball", alpha * 0.25 * hot_a)
            fr.path_stroke(path, "ball", 3.0, alpha * hot_a, glow=1.2 * hot_a)
        for a_, b_ in PIPS[v]:
            p = R @ ((n * 1.002 + (u * a_ + w * b_) * 0.62) * half) + center
            facing = float(np.dot(normal, cam.eye - p) / np.linalg.norm(cam.eye - p))
            if facing <= 0.05:
                continue
            xs, ys, z = cam.project(p)
            r = cam.focal * 0.11 * half / float(z[0]) * math.sqrt(facing)
            fr.circle(float(xs[0]), float(ys[0]), r, "ink", alpha=alpha * min(1.0, facing * 2.5), fill=True)

    draw_box(fr, cam, center, (half, half, half), "ball", "ball", alpha, R, fill_strength=0.30, stroke_width=2.2,
             glow=glow, on_face=on_face)


def hop(t, t0, t1, p0, p1, height=150.0, bounces=2.5):
    """Screen position of a die rolling from p0 to p1: decaying bounces."""
    u = lin(t, t0, t1)
    x = lerp(p0[0], p1[0], ease_out(u))
    y = lerp(p0[1], p1[1], u) - height * abs(math.sin(bounces * math.pi * u)) * (1 - u) ** 1.5
    return x, y


def ellipse(x, y, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(x - rx, y - ry, x + rx, y + ry))
    return p


def tail_fade(fr, t):
    """Chapter 1's last frame (bars, bell, pointer, pill) clears as the coin arrives."""
    a = 1 - smooth(lin(t, START, START + 0.4))
    if a <= 0.003:
        return
    t1 = ch1.END - 1e-3
    with faded(fr, a):
        with view(fr, translate(0.0, ch1.SHIFT_Y)):
            ch1.draw_ten(fr, t1, 0.0)
            ch1.BAX.floor_line(fr, -3.6, 3.6, 1.0, "line", 2.0)
            ch1.draw_pointer(fr, t1)
        ch1.draw_pill(fr, t1)


# ------------------------------------------------------------------ S08A: coin -> die

COIN = (960.0, 470.0, 110.0)
COIN_SPIN = (b(348), b(350) + 0.3)  # "perfectly fair coin"
MESSY_T = b(356)  # "messier": wobble, then fold into a die
FOLD = (MESSY_T + 0.35, MESSY_T + 0.75)
ROLL1 = (b(357), b(359) + 0.2)  # "Roll one die."
DIE1_HOME = (430.0, 500.0)
FRONT_HALF = 1000 * DIE_HALF / (10 - DIE_HALF)  # px half-size of the front face at depth 0


def draw_coin(fr, t):
    a = env(t, START + 0.4, FOLD[1] + 0.05, 0.4, 0.08)
    if a <= 0.003:
        return
    cx, cy, R = COIN
    spin = lin(t, *COIN_SPIN)
    ph = 6 * math.pi * ease_io(spin)
    rise = 50 * math.sin(math.pi * spin)
    wob = env(t, MESSY_T - 0.05, FOLD[0] + 0.1, 0.1, 0.1)
    rot = 0.16 * wob * math.sin(28 * (t - MESSY_T))
    fold = smooth(lin(t, *FOLD))
    c = math.cos(ph)
    color = mix("left" if c > 0 else "right", "ball", fold)
    y = cy - rise
    if fold <= 0:
        rx = max(2.5, R * abs(c))
        m = skia.Matrix()
        m.setRotate(math.degrees(rot), cx, y)
        fr.c.save()
        fr.c.concat(m)
        fr.path_fill(ellipse(cx, y + 6, rx, R), "line", a * 0.8)
        fr.path_fill(ellipse(cx, y, rx, R), color, a * 0.2)
        fr.path_stroke(ellipse(cx, y, rx, R), color, 3.4, a, glow=0.6)
        fr.path_stroke(ellipse(cx, y, rx * 0.78, R * 0.78), color, 1.4, a * 0.5)
        fr.text("L" if c > 0 else "R", cx, y + 30, "sans", 84, 700, color, a * smooth(clamp((abs(c) - 0.72) / 0.2)))
        fr.c.restore()
        return
    # the coin's rim folds into the die's front face: a circle becomes a rounded square
    half = lerp(R, FRONT_HALF, fold)
    rr = lerp(R, 18.0, fold)
    rect = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(cx - half, y - half, cx + half, y + half), rr, rr)
    p = skia.Path()
    p.addRRect(rect)
    fr.path_fill(p, "ball", a * 0.18)
    fr.path_stroke(p, "ball", 3.0, a, glow=0.7)


def die1_state(t):
    """(x, y, scale, R) of the first die through S08."""
    if t < ROLL1[0]:
        return COIN[0], COIN[1], 1.0, np.eye(3)
    if t < ROLL2[0]:
        e = ease_out(lin(t, *ROLL1))
        x, y = hop(t, *ROLL1, COIN[:2], DIE1_HOME, height=180)
        return x, y, 1.0 - 0.15 * e, tumble(np.eye(3), shown(4), e)
    e = ease_out(lin(t, *ROLL2))
    x, y = hop(t, *ROLL2, DIE1_HOME, DIE_A, height=110)
    return x, y, lerp(0.85, 0.55, e), tumble(shown(4), shown(3), e, (1, 2, 0))


def draw_dice(fr, t):
    a = smooth(lin(t, FOLD[1] - 0.05, FOLD[1] + 0.05)) * (1 - smooth(lin(t, CLEAR8, CLEAR8 + 0.5)))
    if a <= 0.003:
        return
    x, y, s, R = die1_state(t)
    draw_die(fr, x, y, s, R, a)
    if t >= ROLL2[0]:
        e = ease_out(lin(t, *ROLL2))
        x2, y2 = hop(t, *ROLL2, (900.0, 120.0), DIE_B, height=110)
        draw_die(fr, x2, y2, 0.55, tumble(shown(2), shown(4), e, (2, 1, 1)), a * smooth(lin(t, ROLL2[0], ROLL2[0] + 0.2)))
        sa = a * smooth(lin(t, b(383), b(383) + 0.35))
        fr.text("+", (DIE_A[0] + DIE_B[0]) / 2, DIE_A[1] + 18, "sans", 56, 500, "muted", sa)
        fr.text("= 7", DIE_B[0] + 150, DIE_A[1] + 20, "sans", 60, 700, "ball", sa, glow=0.5)
    if ROLL1[0] <= t < ROLL1[0] + 0.5:  # the fold hands over with a glint
        u = (t - ROLL1[0]) / 0.5
        fr.glint(COIN[0], COIN[1], 60.0, 1 - u)


# ------------------------------------------------------------------ S08B: one die is flat

AX8 = Axes(cx=1240.0, floor=820.0, unit=120.0, hscale=900.0)
ONE = bars_from(*die_pmf())
TWO = bars_from(*sum_pmf(*die_pmf(), 2))
ONE_T = b(363)  # "one to six"
FLAT_T = b(373)  # "flat"
NOBELL_T = b(374)  # "no bell at all"
BELL8 = Bell(AX8, -3.3, 3.3)


def draw_one_die_bars(fr, t):
    a = 1 - smooth(lin(t, ROLL2[0], ROLL2[0] + 0.5))
    if t < ONE_T or a <= 0.003:
        return
    grow = stagger(t, ONE_T, 6, spread=0.45, dur=0.55)
    AX8.floor_line(fr, -2.1, 2.1, a * smooth(lin(t, ONE_T - 0.3, ONE_T)))
    draw_bars(fr, AX8, ONE, a, grow, gap=0.14)
    label_bars(fr, AX8, ONE, [str(v) for v in range(1, 7)], a * smooth(lin(t, ONE_T, ONE_T + 0.5)), size=26)
    # "flat": a level line across the tops
    u = ease_out(lin(t, FLAT_T, FLAT_T + 0.5))
    if u > 0:
        y = float(AX8.y(ONE.d[0]))
        x0, x1 = float(AX8.x(-1.9)), float(AX8.x(1.9))
        fr.line(x0 - 20, y - 12, x0 - 20 + (x1 - x0 + 40) * u, y - 12, "ink", 2.0, a * 0.85, glow=0.4)
    # "no bell at all": a ghost bell tries to fit, shivers, and gives up
    ga = a * env(t, NOBELL_T, NOBELL_T + 1.2, 0.15, 0.45) * 0.55
    if ga > 0.003:
        shake = 6 * math.sin(40 * (t - NOBELL_T)) * env(t, NOBELL_T + 0.45, NOBELL_T + 0.9, 0.05, 0.2)
        with view(fr, translate(shake, 0.0)):
            BELL8.draw(fr, reveal=ease_io(lin(t, NOBELL_T, NOBELL_T + 0.5)), alpha=ga, glow=0.3)


# ------------------------------------------------------------------ S08C: two dice, the grid, the triangle

ROLL2 = (b(380), b(384) + 0.1)  # "two dice and add them"
DIE_A, DIE_B = (300.0, 260.0), (555.0, 260.0)
GRID_T = b(385)  # "Suddenly"
SEVEN_T = b(386)  # "seven is the favorite"
SIX_T = b(391)  # "six different pairs"
ONE_PAIR_T = b(397)  # "only one pair makes two"
SLIDE_T = b(402)  # "The flat shape has become ..."
TRI_T = b(408)  # "triangle"
CLEAR8 = b(409)  # "Add three dice": the dice and the grid leave
CELL, GX, GY = 62.0, 230.0, 400.0
SD2 = math.sqrt(35 / 6)
BLOCK_H = SD2 / 36 * AX8.hscale
BLOCK_W = AX8.unit / SD2 * (1 - 0.14)


def cell_xy(i, j):
    return GX + CELL * (j + 0.5), GY + CELL * (i + 0.5)


def cell_slide(i, j, t):
    s = i + j + 2
    m = i if s <= 7 else i - (s - 7)  # rank of the cell within its sum
    t0 = SLIDE_T + 0.07 * (s - 2) + 0.035 * m
    return s, m, ease_io(lin(t, t0, t0 + 0.65))


def draw_grid(fr, t):
    a = smooth(lin(t, GRID_T, GRID_T + 0.6)) * (1 - smooth(lin(t, CLEAR8, CLEAR8 + 0.4)))
    if a <= 0.003:
        return
    sev = env(t, SEVEN_T, ONE_PAIR_T + 0.2, 0.3, 0.35)
    pulse = math.exp(-((t - SIX_T - 0.2) / 0.25) ** 2) + math.exp(-((t - SIX_T - 0.75) / 0.25) ** 2)
    corner = env(t, ONE_PAIR_T, SLIDE_T + 0.3, 0.3, 0.3)
    head = a * (1 - smooth(lin(t, SLIDE_T, SLIDE_T + 0.4)))
    for k in range(6):
        fr.text(str(k + 1), GX + CELL * (k + 0.5), GY - 14, "sans", 22, 600, "muted", head)
        fr.text(str(k + 1), GX - 20, GY + CELL * (k + 0.5) + 8, "sans", 22, 600, "muted", head)
    for i in range(6):
        for j in range(6):
            s, m, u = cell_slide(i, j, t)
            ca = a * smooth(lin(t, GRID_T + 0.05 * i, GRID_T + 0.05 * i + 0.4))
            if ca <= 0.003:
                continue
            hot = sev * (0.7 + 0.3 * min(1.0, pulse)) if s == 7 else 0.0
            if s == 2:
                hot = max(hot, corner)
            if s != 7 and s != 2:
                dim = 1 - 0.55 * max(sev, corner)
            else:
                dim = 1.0 if (s == 7 and sev > 0) or (s == 2 and corner > 0) else 1 - 0.55 * max(sev, corner)
            cx, cy = cell_xy(i, j)
            w0, h0 = CELL - 6, CELL - 6
            bx = float(AX8.x((s - 7) / SD2))
            by = AX8.floor - BLOCK_H * (m + 0.5)
            x, y = lerp(cx, bx, u), lerp(cy, by, u)
            w, h = lerp(w0, BLOCK_W, u), lerp(h0, BLOCK_H - 2, u)
            fill_a = lerp(0.10 + 0.25 * hot, 0.85, u)
            ad = lerp(ca * dim, ca, u)
            fr.rrect(x - w / 2, y - h / 2, w, h, lerp(8, 2, u), fill="ball", fill_alpha=fill_a, alpha=ad)
            fr.rrect(x - w / 2, y - h / 2, w, h, lerp(8, 2, u), stroke="ball", width=1.6, alpha=ad * (1 - u),
                     glow=0.8 * hot)
            na = ca * dim * (1 - smooth(min(1.0, u * 3)))
            fr.text(str(s), x, y + 9, "sans", 26 * (1 + 0.15 * hot), 700 if hot > 0.3 else 600,
                    mix("ink", "ball", hot) if hot > 0 else "ink", na, glow=0.6 * hot)
    pa = env(t, SIX_T, ONE_PAIR_T, 0.3, 0.25) * a
    hud.pill(fr, GX + 3 * CELL, GY + 6 * CELL + 50, "6 pairs make 7", "ball", pa, 24)
    pb = env(t, ONE_PAIR_T, SLIDE_T + 0.3, 0.3, 0.3) * a
    hud.pill(fr, GX + 3 * CELL, GY + 6 * CELL + 50, "1 pair makes 2", "ball", pb, 24)


def draw_two_labels(fr, t):
    a = smooth(lin(t, SLIDE_T + 0.6, SLIDE_T + 1.2)) * (1 - smooth(lin(t, CLEAR8, CLEAR8 + 0.4)))
    if a <= 0.003:
        return
    AX8.floor_line(fr, -2.6, 2.6, a)
    label_bars(fr, AX8, TWO, [str(v) for v in range(2, 13)], a, size=22)


def draw_triangle(fr, t):
    """An ink outline traced over the stacked bars on "triangle", and a tiny muted * between two flat pmfs."""
    a = smooth(lin(t, TRI_T, TRI_T + 0.2)) * (1 - smooth(lin(t, CLEAR8 - 0.25, CLEAR8 + 0.05)))
    if a <= 0.003:
        return
    xs = [float(AX8.x(-6 / SD2))] + [float(AX8.x((s - 7) / SD2)) for s in range(2, 13)] + [float(AX8.x(6 / SD2))]
    ys = [AX8.floor] + [AX8.floor - BLOCK_H * min(s - 1, 13 - s) - 10 for s in range(2, 13)] + [AX8.floor]
    u = ease_io(lin(t, TRI_T, TRI_T + 0.6))
    n = 1 + u * (len(xs) - 1)
    k = int(n)
    px, py = xs[: k + 1], ys[: k + 1]
    if k < len(xs) - 1:
        f = n - k
        px = px + [lerp(xs[k], xs[k + 1], f)]
        py = py + [lerp(ys[k], ys[k + 1], f)]
    fr.poly(px, py, "ink", 2.4, a, glow=0.5)
    # flat * flat = triangle, small and muted
    ma = a * smooth(lin(t, TRI_T + 0.3, TRI_T + 0.8)) * 0.8
    if ma > 0.003:
        cx, cy = AX8.cx, 250.0
        for ox in (-110, 30):
            for k2 in range(6):
                fr.rrect(cx + ox + k2 * 13, cy - 28, 10, 28, 1.5, fill="muted", alpha=ma)
        fr.text("∗", cx - 4, cy - 2, "sans", 34, 500, "muted", ma)
        fr.text("=", cx + 125, cy - 4, "sans", 30, 500, "muted", ma)
        tri = [cx + 150 + 6 * q for q in range(11)]
        for q, x in enumerate(tri):
            h = 6 * min(q + 1, 11 - q)
            fr.rrect(x, cy - h, 5, h, 1, fill="muted", alpha=ma)


# ------------------------------------------------------------------ S09: three dice, ten dice

AX9 = Axes(cx=960.0, floor=840.0, unit=150.0, hscale=1100.0)
THREE = bars_from(*sum_pmf(*die_pmf(), 3))
TEN = bars_from(*sum_pmf(*die_pmf(), 10))
MOVE9 = (CLEAR8 - 0.1, CLEAR8 + 0.6)
M3 = (b(410), b(411) + 0.4)  # "three dice"
M10 = (b(420), b(421) + 0.45)  # "ten dice"
SNAP9 = b(426)  # "nearly perfect bell"
CLEAR9 = b(432)  # "surprising part": the bell clears
BELL9 = Bell(AX9, -3.4, 3.4)


def fair_bars(t):
    if t < M3[0]:
        return TWO
    if t < M10[0]:
        return morph(TWO, THREE, ease_io(lin(t, *M3)))
    return morph(THREE, TEN, ease_io(lin(t, *M10)))


def draw_s09(fr, t):
    if t < MOVE9[0]:
        return
    a = 1 - smooth(lin(t, CLEAR9, CLEAR9 + 0.6))
    if a <= 0.003:
        return
    ax = lerp_axes(AX8, AX9, ease_io(lin(t, *MOVE9)))
    bars = fair_bars(t)
    ax.floor_line(fr, -3.5, 3.5, a * smooth(lin(t, *MOVE9)))
    draw_bars(fr, ax, bars, a, gap=0.12 if len(bars.z) < 30 else 0.08)
    # the outline through the bar tops: a triangle softening into a curve
    oa = a * env(t, M3[0], M10[0] + 0.3, 0.3, 0.4)
    if oa > 0.003:
        xs = ax.x(bars.z)
        ys = ax.y(bars.d) - 10
        x0 = float(ax.x(bars.z[0] - bars.w[0]))
        x1 = float(ax.x(bars.z[-1] + bars.w[-1]))
        fr.poly([x0, *xs, x1], [ax.floor, *ys, ax.floor], "ink", 2.4, oa, glow=0.5)
    n = 2 if t < M3[0] else 3 if t < M10[0] + 0.2 else 10
    dice_row(fr, n, a * smooth(lin(t, M3[0] - 0.2, M3[0] + 0.2)), t)
    if t < CLEAR9 + 0.6:
        BELL9.snap(fr, t, SNAP9, alpha=a, width=3.2)


def dice_row(fr, n, alpha, t, hot=False):
    """A counter: n small die glyphs (wrapping at 15) and the readout 'dice n'."""
    if alpha <= 0.003:
        return
    per = 15
    rows = (n + per - 1) // per
    for k in range(n):
        r, c = divmod(k, per)
        m = min(per, n - r * per)
        x = 960 + (c - (m - 1) / 2) * 34
        y = 150 + r * 34
        fr.rrect(x - 13, y - 13, 26, 26, 6, fill="ball", fill_alpha=0.16, stroke="ball", width=1.6, alpha=alpha)
        if hot:
            fr.circle(x - 6, y - 6, 2.2, "ink", alpha=alpha, fill=True)
            fr.circle(x + 6, y + 6, 2.2, "ink", alpha=alpha, fill=True)
        else:
            fr.circle(x, y, 2.6, "ink", alpha=alpha, fill=True)
    hud.readout(fr, 960, 150 + rows * 34 + 30, "dice", str(n), "ball", alpha, size=30)


# ------------------------------------------------------------------ S10: the lopsided die

LOP_DIE_T = b(437)  # "lopsided die"
HALF_T = b(443)  # "six half the time"
NS = (1, 2, 3, 5, 10, 30)
LOP = [bars_from(*sum_pmf(*LOPSIDED, n)) for n in NS]
HSCALE = (650.0, 760.0, 860.0, 960.0, 1040.0, 1100.0)
STEP_T = (None, b(447), b(447) + 0.5, b(447) + 1.0, b(447) + 1.55, b(447) + 2.15)  # "Add enough of them together"
STEP_D = 0.45
MELT_T = b(455)
SAME_T = b(461)  # "same bell"
CLEAR10 = b(466)  # "This is called the central limit theorem": the bell leaves as the title lands


def lop_state(t):
    k = max([0] + [i for i in range(1, len(NS)) if t >= STEP_T[i]])
    if k == 0:
        return LOP[0], HSCALE[0], 1
    u = ease_io(lin(t, STEP_T[k], STEP_T[k] + STEP_D))
    return morph(LOP[k - 1], LOP[k], u), lerp(HSCALE[k - 1], HSCALE[k], u), NS[k]


def draw_s10(fr, t):
    if t < LOP_DIE_T - 0.2:
        return
    a = 1 - smooth(lin(t, CLEAR10, CLEAR10 + 0.6))
    if a <= 0.003:
        return
    # the die, its six face glowing and bulging
    da = a * smooth(lin(t, LOP_DIE_T, LOP_DIE_T + 0.4)) * (1 - smooth(lin(t, STEP_T[1], STEP_T[1] + 0.5)))
    if da > 0.003:
        s = 0.85 * back(lin(t, LOP_DIE_T, LOP_DIE_T + 0.5))
        bulge = 0.5 + 0.5 * math.sin(5.0 * (t - LOP_DIE_T))
        R = shown(6) @ rotation(0.0, 0.12 * math.sin(1.3 * (t - LOP_DIE_T)), 0.0)
        draw_die(fr, 290.0, 470.0, s * (1 + 0.03 * bulge), R, da, hot=6, hot_a=0.6 + 0.4 * bulge)
    if t < HALF_T:
        return
    bars, hs, n = lop_state(t)
    ax = Axes(AX9.cx, AX9.floor, AX9.unit, hs)
    ax.floor_line(fr, -3.5, 3.5, a * smooth(lin(t, HALF_T - 0.3, HALF_T)))
    grow = stagger(t, HALF_T, 6, spread=0.3, dur=0.6) if n == 1 else 1.0
    draw_bars(fr, ax, bars, a, grow, gap=0.12 if len(bars.z) < 30 else 0.06)
    if n == 1 and t < STEP_T[1] + 0.3:
        la = a * smooth(lin(t, HALF_T + 0.4, HALF_T + 0.8)) * (1 - smooth(lin(t, STEP_T[1], STEP_T[1] + 0.3)))
        label_bars(fr, ax, bars, ["0.1"] * 5 + ["0.5"], la, size=24, color="ink", below=False, grow=grow)
        label_bars(fr, ax, bars, [str(v) for v in range(1, 7)], la, size=24)
    ra = smooth(lin(t, STEP_T[1] - 0.1, STEP_T[1] + 0.3)) * (1 - smooth(lin(t, SAME_T, SAME_T + 0.35)))
    dice_row(fr, n, a * ra, t, hot=True)
    if t >= SAME_T:
        BELL9.snap(fr, t, SAME_T, alpha=a, width=3.2)
        # the fair-dice bell drops in from above and lands exactly on top
        e = ease_in(lin(t, SAME_T + 0.35, SAME_T + 0.85))
        ga = a * env(t, SAME_T + 0.25, SAME_T + 1.6, 0.2, 0.5)
        if ga > 0.003:
            with view(fr, translate(0.0, -160 * (1 - e))):
                BELL9.draw(fr, alpha=ga * 0.8, width=2.0, glow=0.2, color="ink")
                fr.text("fair dice", AX9.cx, float(AX9.y(pdf(0.0))) - 24, "sans", 24, 600, "muted", ga)
            if e >= 1.0:
                fr.light_sweep(BELL9.outline(), lin(t, SAME_T + 0.85, SAME_T + 1.55), strength=0.9)


# ------------------------------------------------------------------ S11: the central limit theorem

TITLE_T = b(467)  # "central limit theorem"
TITLE = "THE CENTRAL LIMIT THEOREM"
MINI_T = b(472)  # "add up many small, independent random effects"
INDEP_T = b(476)
FUNNEL_T = b(480)  # "the total follows a bell curve"
SNAP11 = b(483)
CHANGE_T = b(485)  # "Almost no matter what each single effect looks like"
WASH_T = b(497)  # "washed out"
DIALS_T = b(499)  # "Only two things survive"
CENTER_T = b(503)
SPREAD_T = b(508)
CLEAR11 = cue(513) - 0.05  # "And this explains the list"
ROW_Y = 400.0
SUM_PT = (960.0, 470.0)
AX11 = Axes(cx=960.0, floor=760.0, unit=120.0, hscale=560.0)
BELL11 = Bell(AX11, -3.4, 3.4)


def _shapes():
    x = np.linspace(0.0, 1.0, 12)
    s = [
        np.ones(12),  # flat
        np.r_[np.full(11, 0.22), 1.0],  # lopsided
        np.r_[1.0, np.zeros(10), 1.0],  # coin
        1 - np.abs(2 * x - 1),  # triangle
        (2 * x - 1) ** 2 + 0.08,  # U-shape
        np.exp(-(((x - 0.5) / 0.07) ** 2)),  # spike
        np.exp(-4 * x),  # exponential-like
        np.exp(-(((x - 0.22) / 0.1) ** 2)) + np.exp(-(((x - 0.78) / 0.1) ** 2)),  # two bumps
    ]
    return [np.maximum(v, 0.03) / max(v.max(), 1e-9) for v in s]


SHAPES = _shapes()


def mini_x(i, t):
    pitch = 175.0 + 30.0 * smooth(lin(t, INDEP_T, INDEP_T + 0.5))
    return 960.0 + (i - 3.5) * pitch


def mini_heights(i, t):
    if t < CHANGE_T:
        return SHAPES[i]
    c = (t - CHANGE_T) / 0.85 + i * 0.37
    k = int(c)
    f = smooth(clamp((c - k) / 0.45))
    return lerp(SHAPES[(i + k) % 8], SHAPES[(i + k + 1) % 8], f)


def draw_minis(fr, t):
    a = env(t, MINI_T, WASH_T + 0.9, 0.3, 0.6)
    if a <= 0.003:
        return
    blur = 8.0 * smooth(lin(t, WASH_T, WASH_T + 0.8))
    with fr.blurred(blur) if blur > 0.05 else contextlib.nullcontext():
        for i in range(8):
            ia = a * smooth(lin(t, MINI_T + 0.08 * i, MINI_T + 0.08 * i + 0.35))
            if ia <= 0.003:
                continue
            cx = mini_x(i, t)
            hs = mini_heights(i, t)
            body = skia.Path()
            for k, h in enumerate(hs):
                x0 = cx - 60 + k * 10
                body.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, ROW_Y - h * 64, x0 + 8, ROW_Y), 1.5, 1.5))
            fr.path_fill(body, "ball", ia * 0.85, glow=0.2)
            fr.line(cx - 64, ROW_Y + 2, cx + 64, ROW_Y + 2, "line", 1.4, ia)
            if i < 7:
                fr.text("+", (cx + mini_x(i + 1, t)) / 2, ROW_Y - 18, "sans", 34, 500, "muted", ia)
    # the funnel: each effect sends a few glowing drops into one sum
    for i in range(8):
        for j in range(5):
            t0 = FUNNEL_T + 0.05 * i + 0.09 * j
            u = lin(t, t0, t0 + 0.55)
            if 0 < u < 1:
                cx = mini_x(i, t)
                e = ease_in(u)
                x = (1 - e) ** 2 * cx + 2 * (1 - e) * e * cx + e * e * SUM_PT[0]
                y = (1 - e) ** 2 * (ROW_Y - 30) + 2 * (1 - e) * e * (SUM_PT[1] + 10) + e * e * SUM_PT[1]
                fr.glow_dot(x, y, 4.0, "ball", (1 - u * 0.5), strength=1.1)


def draw_title(fr, t):
    a = smooth(lin(t, TITLE_T, TITLE_T + 0.6)) * (1 - smooth(lin(t, CLEAR11, CLEAR11 + 0.5)))
    if a <= 0.003:
        return
    rise = 18 * (1 - ease_out(lin(t, TITLE_T, TITLE_T + 0.8)))
    fr.text(TITLE, 960, 190 + rise, "display", 66, 600, "ink", a, tracking=0.05)
    u = ease_out(lin(t, TITLE_T + 0.4, TITLE_T + 1.0))
    if u > 0:
        fr.line(960 - 330 * u, 222 + rise, 960 + 330 * u, 222 + rise, "bell", 3.0, a, glow=0.7)
    fr.light_sweep(text_path(TITLE, 960, 190 + rise, "display", 66, 600, tracking=0.05),
                   lin(t, TITLE_T + 0.7, TITLE_T + 1.5), strength=0.9)


def draw_sum(fr, t):
    a = 1 - smooth(lin(t, CLEAR11, CLEAR11 + 0.5))
    if t < FUNNEL_T or a <= 0.003:
        return
    pa = a * env(t, FUNNEL_T + 0.1, CHANGE_T + 0.4, 0.3, 0.4)
    if pa > 0.003:
        fr.circle(*SUM_PT, 20.0, "ball", 2.0, pa, glow=0.6)
        fr.text("+", SUM_PT[0], SUM_PT[1] + 11, "sans", 32, 600, "ball", pa)
    grow = stagger(t, FUNNEL_T + 0.45, len(TEN.z), spread=0.7, dur=0.6)
    AX11.floor_line(fr, -3.5, 3.5, a * smooth(lin(t, FUNNEL_T + 0.3, FUNNEL_T + 0.6)))
    draw_bars(fr, AX11, TEN, a, grow, gap=0.08, glow=0.2)
    BELL11.snap(fr, t, SNAP11, alpha=a, width=3.2)
    # the two survivors: the centre and the spread
    ca = a * env(t, CENTER_T, CLEAR11 + 0.5, 0.3, 0.1)
    if ca > 0.003:
        BELL11.mean_line(fr, alpha=ca, u=ease_out(lin(t, CENTER_T, CENTER_T + 0.5)))
        kick = math.exp(-max(0.0, t - CENTER_T - 0.3) / 0.5)
        fr.glow_dot(float(AX11.x(0.0)), float(AX11.y(pdf(0.0))), 6.0, "bell", ca, strength=1.0 + kick)
    sa = a * env(t, SPREAD_T, CLEAR11 + 0.5, 0.3, 0.1)
    if sa > 0.003:
        u = ease_out(lin(t, SPREAD_T, SPREAD_T + 0.7))
        y = float(AX11.y(pdf(1.0)))
        xc = float(AX11.x(0.0))
        reach = AX11.unit * u
        fr.line(xc - reach, y, xc + reach, y, "bg", 9.0, sa * 0.8)
        for sgn in (-1, 1):
            hud.arrow(fr, xc, y, xc + sgn * reach, y, "sigma", 3.4, sa, glow=0.8, head=16.0)
        fr.line(xc - AX11.unit, y - 12, xc - AX11.unit, y + 12, "sigma", 2.0, sa * u)
        fr.line(xc + AX11.unit, y - 12, xc + AX11.unit, y + 12, "sigma", 2.0, sa * u)


def draw_dials(fr, t):
    a = smooth(lin(t, DIALS_T, DIALS_T + 0.6)) * (1 - smooth(lin(t, CLEAR11, CLEAR11 + 0.5)))
    if a <= 0.003:
        return
    am = env(t, CENTER_T, SPREAD_T, 0.3, 0.4)
    asg = env(t, SPREAD_T, CLEAR11 + 0.5, 0.3, 0.3)
    dial_pair(fr, 960, 880, 0.0, 1.0, a, gap=300, active_mu=am, active_sigma=asg, readouts=False)


# ------------------------------------------------------------------ S12: addition is the bell

LIST_T = b(516)  # "the list from the start"
HEIGHT_T = b(521)  # "Your height"
GENES_T = b(525)  # "thousands of genes"
ICON_T = (b(531), b(532), b(534))  # "food, sleep, and health"
NUDGE_T = b(537)  # "nudging you a little up or a little down"
STACK_T = b(546)  # "Many small pushes, added together"
PLUS_T = b(552)  # "The bell is simply what addition looks like"
MORPH_T = b(555)
SWEEP_T = b(557)
LABELS = ("pegs", "heights", "star position", "sensor noise", "exam scores")
FIG_X, FIG_FLOOR, FIG_H = 560.0, 900.0, 460.0
N_NUDGE = 44
STEPS = np.random.default_rng(52).choice([-1.0, 1.0], N_NUDGE)
NUDGE_AT = NUDGE_T + np.arange(N_NUDGE) * (STACK_T - NUDGE_T - 0.15) / N_NUDGE
WALK_X0, WALK_DX, WALK_DY = 790.0, 8.0, 9.0
CROWD_X = np.linspace(1240.0, 1800.0, 11)
CROWD_FLOOR, CROWD_H = 560.0, 190.0
CROWD_WALK = np.cumsum(np.random.default_rng(53).choice([-1.0, 1.0], (11, 40)), axis=1)
POUR_N = 900
POUR_CM = crowd.sample_heights(POUR_N, seed=54)
POUR_PX_CM = 13.0
POUR_FLOOR = 990.0
CLEAR12 = PLUS_T - 0.25


@lru_cache(maxsize=1)
def pour_dots():
    return crowd.dot_layout(POUR_CM, lambda v: 1520 + (np.asarray(v) - crowd.MEAN_CM) * POUR_PX_CM, 1.0, 3.0,
                            POUR_FLOOR)


def draw_strip(fr, t):
    """The five panels from the cold open flash past at the top."""
    u = lin(t, LIST_T - 0.1, LIST_T + 2.0)
    if u <= 0 or u >= 1:
        return
    shift = lerp(W + 40, -5 * 330 - 60, ease_io(u))
    for i, label in enumerate(LABELS):
        x = shift + i * 330
        if x > W or x + 300 < 0:
            continue
        hud.glass_card(fr, x, 60, 300, 130, 1.0, r=16)
        fr.text(label, x + 16, 88, "sans", 17, 600, "muted", 1.0, align="left")
        ax = Axes(cx=x + 150, floor=176, unit=34, hscale=180)
        Bell(ax, -3.2, 3.2).draw(fr, alpha=1.0, width=2.4, glow=0.5)


def walk_offset(t):
    """The height marker's position: the sum of the nudges so far (smoothed per step), in steps."""
    done = smooth(np.clip((t - NUDGE_AT) / 0.18, 0.0, 1.0))
    return float(np.dot(done, STEPS))


def draw_person(fr, t):
    a = smooth(lin(t, HEIGHT_T, HEIGHT_T + 0.5)) * (1 - smooth(lin(t, CLEAR12, CLEAR12 + 0.4)))
    if a <= 0.003:
        return
    w = walk_offset(t)
    h = FIG_H + 3.0 * w
    crowd.person(fr, FIG_X, FIG_FLOOR, h, a, fill=0.06, width=2.0)
    top = FIG_FLOOR - h * 0.98
    jit = env(t, NUDGE_T, STACK_T + 0.2, 0.2, 0.3)
    fr.line(FIG_X - 60, top, FIG_X + 150, top, "ball", 2.4, a, glow=0.5 + 0.5 * jit)
    hud.arrow_head(fr, FIG_X + 175, top, FIG_X + 150, top, "ball", a, 14.0)
    cm = crowd.MEAN_CM + 0.5 * w
    hud.tabular(fr, f"{cm:.1f} cm", FIG_X + 240, top + 10, 28, "ink", a * smooth(lin(t, HEIGHT_T + 0.3, HEIGHT_T + 0.8)))


@lru_cache(maxsize=1)
def gene_ticks():
    rng = np.random.default_rng(55)
    n = 320
    ang = rng.uniform(0, 2 * np.pi, n)
    rad = np.sqrt(rng.uniform(0.25, 1.0, n))
    xs = FIG_X + 250 * rad * np.cos(ang)
    ys = 650 + 300 * rad * np.sin(ang)
    th = rng.uniform(0, np.pi, n)
    return xs, ys, th, rng.uniform(0, 1, n), rng.uniform(0, 2 * np.pi, n)


def draw_genes(fr, t):
    a = smooth(lin(t, GENES_T, GENES_T + 0.4)) * (1 - smooth(lin(t, STACK_T, STACK_T + 0.6)))
    if a <= 0.003:
        return
    xs, ys, th, delay, _ = gene_ticks()
    path = skia.Path()
    for x, y, q, d in zip(xs, ys, th, delay):
        if t < GENES_T + 0.9 * d:
            continue
        dx, dy = 5 * math.cos(q), 5 * math.sin(q)
        path.moveTo(float(x - dx), float(y - dy))
        path.lineTo(float(x + dx), float(y + dy))
    fr.path_stroke(path, "ball", 1.4, a * 0.45)


def icon(fr, kind, x, y, a):
    hud.glass_card(fr, x - 38, y - 38, 76, 76, a, r=38)
    if kind == "bowl":
        p = skia.Path()
        p.moveTo(x - 22, y - 4)
        p.quadTo(x - 20, y + 20, x, y + 20)
        p.quadTo(x + 20, y + 20, x + 22, y - 4)
        p.close()
        fr.path_stroke(p, "ink", 2.2, a)
        for k in (-8, 0, 8):
            fr.line(x + k, y - 10, x + k + 2, y - 20, "muted", 1.6, a)
    elif kind == "moon":
        outer = skia.Path()
        outer.addCircle(x, y, 20)
        inner = skia.Path()
        inner.addCircle(x + 10, y - 7, 17)
        moon = skia.Op(outer, inner, skia.PathOp.kDifference_PathOp)
        fr.path_fill(moon, "ink", a * 0.9)
    else:
        p = skia.Path()
        p.moveTo(x, y + 18)
        p.cubicTo(x - 30, y - 2, x - 14, y - 26, x, y - 10)
        p.cubicTo(x + 14, y - 26, x + 30, y - 2, x, y + 18)
        p.close()
        fr.path_stroke(p, "ink", 2.2, a)


def draw_icons(fr, t):
    a_out = 1 - smooth(lin(t, STACK_T, STACK_T + 0.5))
    for kind, t0, y in zip(("bowl", "moon", "heart"), ICON_T, (420.0, 560.0, 700.0)):
        a = smooth(lin(t, t0, t0 + 0.35)) * a_out
        if a > 0.003:
            s = back(lin(t, t0, t0 + 0.45))
            with view(fr, scale_at(s, 210.0, y)):
                icon(fr, kind, 210.0, y, a)


def scale_at(s, x, y):
    m = skia.Matrix()
    m.setScale(s, s, x, y)
    return m


def draw_nudges(fr, t):
    """Short-lived up (orange) and down (teal) arrows around the marker, then all of them stacked tip to tail."""
    top0 = FIG_FLOOR - FIG_H * 0.98
    a_all = 1 - smooth(lin(t, CLEAR12, CLEAR12 + 0.4))
    rng = np.random.default_rng(56)
    offs = rng.uniform(-70, 70, (N_NUDGE, 2))
    for k, (t0, s) in enumerate(zip(NUDGE_AT, STEPS)):
        a = env(t, t0, t0 + 0.55, 0.08, 0.3) * a_all * (1 - smooth(lin(t, STACK_T, STACK_T + 0.3)))
        if a > 0.003:
            x = FIG_X + 30 + offs[k, 0]
            y = top0 + offs[k, 1]
            color = "right" if s > 0 else "left"
            hud.arrow(fr, x, y + 14 * s, x, y - 14 * s, color, 2.4, a, glow=0.5, head=9.0)
    # tip to tail: a random walk drawn step by step from the marker
    if t < STACK_T:
        return
    ys = top0 - WALK_DY * np.r_[0.0, np.cumsum(STEPS)]
    for k, s in enumerate(STEPS):
        t0 = STACK_T + 0.035 * k
        u = ease_out(lin(t, t0, t0 + 0.15))
        if u <= 0:
            break
        x = WALK_X0 + WALK_DX * k
        color = "right" if s > 0 else "left"
        y1 = lerp(ys[k], ys[k + 1], u)
        fr.line(x, ys[k], x + WALK_DX * u, y1, color, 2.6, a_all, glow=0.5)
    fr.dashed([FIG_X + 150, WALK_X0], [top0, top0], "muted", 1.2, a_all * 0.6, on=5, off=6)
    end = STACK_T + 0.035 * N_NUDGE + 0.15
    la = a_all * smooth(lin(t, end, end + 0.3))
    if la > 0.003:
        xe = WALK_X0 + WALK_DX * N_NUDGE
        fr.glow_dot(xe, ys[-1], 6.0, "ball", la, strength=1.3)
        fr.dashed([xe, FIG_X + 150], [ys[-1], FIG_FLOOR - (FIG_H + 3.0 * STEPS.sum()) * 0.98], "ball", 1.4, la * 0.7,
                  on=5, off=6)


def draw_crowd(fr, t):
    """A crowd does the same at high speed, and their heights pour into a histogram."""
    a = smooth(lin(t, STACK_T + 0.1, STACK_T + 0.5)) * (1 - smooth(lin(t, CLEAR12, CLEAR12 + 0.4)))
    if a <= 0.003:
        return
    u = lin(t, STACK_T + 0.2, STACK_T + 1.3)
    k = min(CROWD_WALK.shape[1] - 1, int(u * (CROWD_WALK.shape[1] - 1)))
    for i, x in enumerate(CROWD_X):
        h = CROWD_H * (1 + 0.012 * CROWD_WALK[i, k])
        crowd.person(fr, x, CROWD_FLOOR, h, a, fill=0.05, width=1.6)
    pa = a * smooth(lin(t, STACK_T + 1.0, STACK_T + 1.3))
    if pa > 0.003:
        n = int(POUR_N * ease_out(lin(t, STACK_T + 1.0, PLUS_T - 0.1)))
        crowd.draw_dots(fr, pour_dots()[:n], 3.0, "ball", pa)
        fr.line(1520 - 3.4 * crowd.SD_CM * POUR_PX_CM, POUR_FLOOR + 4, 1520 + 3.4 * crowd.SD_CM * POUR_PX_CM,
                POUR_FLOOR + 4, "line", 1.6, pa)


PLUS_C, PLUS_ARM, PLUS_THICK = (960.0, 520.0), 170.0, 30.0
AX12 = Axes(cx=960.0, floor=700.0, unit=165.0, hscale=1000.0)
BELL12 = Bell(AX12, -3.2, 3.2, n=320)


def resample(xs, ys, n=480):
    """Closed polygon -> n points evenly spaced by arc length."""
    xs, ys = np.r_[xs, xs[0]], np.r_[ys, ys[0]]
    seg = np.hypot(np.diff(xs), np.diff(ys))
    s = np.r_[0.0, np.cumsum(seg)]
    q = np.linspace(0.0, s[-1], n, endpoint=False)
    return np.interp(q, s, xs), np.interp(q, s, ys)


@lru_cache(maxsize=1)
def outlines():
    x, y = PLUS_C
    A, T = PLUS_ARM, PLUS_THICK
    px = [x - A, x - A, x - T, x - T, x + T, x + T, x + A, x + A, x + T, x + T, x - T, x - T]
    py = [y + T, y - T, y - T, y - A, y - A, y - T, y - T, y + T, y + T, y + A, y + A, y + T]
    bx, by = BELL12.points()
    return resample(np.array(px), np.array(py)), resample(np.asarray(bx), np.asarray(by))


def draw_plus_bell(fr, t):
    a = smooth(lin(t, PLUS_T, PLUS_T + 0.4))
    if a <= 0.003:
        return
    (px, py), (bx, by) = outlines()
    u = ease_io(lin(t, MORPH_T, MORPH_T + 0.8))
    s = back(lin(t, PLUS_T, PLUS_T + 0.55))
    xs = lerp(PLUS_C[0] + (px - PLUS_C[0]) * s, bx, u)
    ys = lerp(PLUS_C[1] + (py - PLUS_C[1]) * s, by, u)
    path = skia.Path()
    path.moveTo(float(xs[0]), float(ys[0]))
    for x, y in zip(xs[1:], ys[1:]):
        path.lineTo(float(x), float(y))
    path.close()
    fr.path_fill(path, "bell", a * lerp(0.22, 0.10, u))
    fr.path_stroke(path, "bell", 4.0, a, glow=0.8 + 0.6 * math.exp(-max(0.0, t - MORPH_T - 0.8) / 0.4) * (u >= 1))
    if u >= 1:
        fr.light_sweep(BELL12.outline(width=4.0), lin(t, SWEEP_T + 0.15, SWEEP_T + 0.95), strength=0.95)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    tail_fade(fr, t)
    draw_coin(fr, t)
    draw_one_die_bars(fr, t)
    draw_grid(fr, t)
    draw_two_labels(fr, t)
    draw_triangle(fr, t)
    draw_dice(fr, t)
    draw_s09(fr, t)
    draw_s10(fr, t)
    draw_title(fr, t)
    draw_minis(fr, t)
    draw_sum(fr, t)
    draw_dials(fr, t)
    draw_strip(fr, t)
    draw_genes(fr, t)
    draw_icons(fr, t)
    draw_person(fr, t)
    draw_nudges(fr, t)
    draw_crowd(fr, t)
    draw_plus_bell(fr, t)
    hud.eyebrow(fr, t, "02 · ADDING DICE", 116.8)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


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
STILLS = [117.0, 118.2, 120.8, 121.6, 123.0, 125.0, 126.6, 127.3, 129.4, 131.5, 132.8, 135.0, 136.6, 137.9, 139.6,
          142.6, 144.7, 146.8, 148.4, 150.0, 152.2, 154.0, 155.8, 156.4, 158.4, 160.8, 163.5, 166.0, 169.0, 171.8,
          174.2, 176.0, 178.8, 181.0, 183.6, 185.8, 186.7, 188.0, 188.9, 189.6, 190.4]
