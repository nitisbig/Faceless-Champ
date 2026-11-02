"""CHAPTER 0 - COLD OPEN (S01-S03), 00:00.000 - 00:56.720 (cue #168 "Let's").

S01  The board          frame 0 already pouring -> hero ball hops left (#14) and right (#16) -> camera eases in,
                        ghost futures fan out on "cannot predict" -> it lands -> x6 pour -> the pile ->
                        the bell traces over it -> "A bell." snap, sweep, chroma kick.
S02  Bell after bell    board shrinks to a panel -> silhouettes walk in and collapse into 10,000 height dots ->
                        star / sensor / exam panels fill their own histograms -> five panels in an arc light
                        bell by bell -> all five curves fly to the centre and land as one -> peg, person, star.
S03  The questions      icons feed one bell, "?" -> the formula types in, its pi lifts out and gets a circle ->
                        a scan finds no circle -> four teaser chips (coin, circle, ruler, break) -> the main bell
                        cracks and a red tail whips off frame -> title lockup -> zoom-blur exit.

One FunctionSource on the narration clock; beats land 0.15 s before their word cue (cues.beat).
"""

from __future__ import annotations

import contextlib
import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
import typmath
from components import crowd, hud
from components.bell import Bell
from components.darts import Target, draw_dots
from components.galton import Board, warp
from components.histogram import Axes, bars_from_samples, draw_bars
from cues import AUDIO, beat, cue
from fx import Frame, chroma_kick, ease_io, ease_out, env, lin, motion_blur, smooth, text_path
from scipy.special import ndtri
from theme import THEME, TOKENS, H, W
from typmath import tc

START = 0.0
END = cue(168)  # 56.72 "Let's go back to the board of pegs."

b = beat  # b(n): when the visual for word cue n lands

# ------------------------------------------------------------------ view helpers


@contextlib.contextmanager
def view(fr, m):
    """Draw inside a scale+translate transform (crisp and glow canvases together)."""
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


def fit_matrix(src, dst):
    """Uniformly fit rect ``src`` (x, y, w, h) into the centre of rect ``dst``."""
    sx, sy, sw, sh = src
    dx, dy, dw, dh = dst
    k = min(dw / sw, dh / sh)
    m = skia.Matrix()
    m.setTranslate(-(sx + sw / 2), -(sy + sh / 2))
    m.postScale(k, k)
    m.postTranslate(dx + dw / 2, dy + dh / 2)
    return m


def zoom_matrix(z, fx_, fy_, cx=W / 2, cy=H / 2):
    m = skia.Matrix()
    m.setTranslate(-fx_, -fy_)
    m.postScale(z, z)
    m.postTranslate(cx, cy)
    return m


def lerp_rect(a, b_, u):
    return tuple(p + (q - p) * u for p, q in zip(a, b_))


def map_pts(m, xs, ys):
    return np.asarray(xs) * m.getScaleX() + m.getTranslateX(), np.asarray(ys) * m.getScaleY() + m.getTranslateY()


# ------------------------------------------------------------------ S01: the board

REL = np.where(np.arange(1000) < 40, -0.15 + np.arange(1000) * 0.26, 10.4 + (np.arange(1000) - 40) / 42.0)
POUR = Board(rows=12, n=1000, release=REL)
POUR_WARP = [(0.0, 1.0), (b(29), 6.0)]  # "And yet": the pour speeds up x6
SD12 = math.sqrt(12) / 2
PILE_AX = Axes(cx=POUR.cx, floor=POUR.floor, unit=POUR.dx * SD12,
               hscale=POUR.n * 2 * POUR.ball_r * 0.87 / (POUR.per_layer * SD12) * 1.05)
PILE_BELL = Bell(PILE_AX, -3.8, 3.8)
BOARD_HOME = (540.0, 40.0, 840.0, 990.0)

HOP = 0.42
HERO_BITS = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1]  # left on row 1 ("left", #14), right on row 2 ("right", #16)
HERO_REL = b(14) - 2 * HOP
HERO = Board(rows=12, n=1, bits=[HERO_BITS], release=[HERO_REL], hop=HOP, fall=0.3)
HERO_LAND = HERO_REL + HERO.t_exit + HERO.fall


def hero_focus(t):
    """A smooth point that follows the hero ball down the board (for the camera)."""
    r = float(np.clip((t - HERO_REL) / HOP - 1.0, 0.0, HERO.rows))
    k = float(np.interp(r, np.arange(HERO.rows + 1), HERO.k[0]))
    x = HERO.cx + (k - r / 2) * HERO.dx
    y = HERO.top + r * HERO.dy
    if t > HERO_REL + HERO.t_exit:
        rx, ry = HERO.rest[0]
        u = smooth(lin(t, HERO_REL + HERO.t_exit, HERO_LAND))
        x, y = x + (rx - x) * u, y + (ry - y) * u
    return x, y


def s01_zoom(t):
    return smooth(lin(t, 6.78, 7.7)) * (1 - smooth(lin(t, 10.15, 11.0)))


def draw_board_content(fr, t, alpha=1.0, curve_alpha=1.0, live=True):
    """The board, its pour and its bell, in design coordinates (BOARD_HOME is its footprint)."""
    s = warp(t, POUR_WARP) if live else 1e3
    rows = 12 * ease_out(lin(t, 0.0, 0.6)) + 1.0 if live else 12
    flash = HERO.hit_flash(0, t) if live else None
    POUR.draw_frame(fr, alpha, rows_shown=rows, flash=flash)
    POUR.draw_balls(fr, s, alpha)
    if live:
        ha = alpha * (1 - smooth(lin(t, 10.4, 11.2)))
        HERO.draw_hero(fr, 0, t, ha, trail=0.5, size=1.8)
        # L / R ticks on the two narrated hops
        for row, label, color, at in ((1, "L", "left", b(14)), (2, "R", "right", b(16))):
            x, y = POUR.peg(row, int(HERO.k[0, row]))
            dx = -30 if label == "L" else 30
            fr.text(label, x + dx * 1.2, y - 16, "sans", 30, 700, color, alpha * env(t, at, at + 1.5, 0.15, 0.4), glow=0.5)
        if HERO_LAND <= t < HERO_LAND + 0.5:  # soft landing click
            u = (t - HERO_LAND) / 0.5
            rx, ry = HERO.rest[0]
            fr.circle(rx, ry, 6 + 22 * u, "ink", 1.4, alpha * (1 - u))
        # the ghost futures on "cannot predict", collapsing on "single ball"
        fan = env(t, b(21), b(25) + 0.2, 0.5, 0.45)
        if fan > 0:
            HERO.draw_fan(fr, 8, int(HERO.k[0, 8]), alpha * fan, color="ball", width=1.4)
    if curve_alpha > 0:
        draw_pile_bell(fr, t, alpha * curve_alpha, live)


def draw_pile_bell(fr, t, a, live):
    if not live:
        PILE_BELL.draw(fr, alpha=a)
        return
    reveal = ease_io(lin(t, b(42), b(44) + 0.6))
    if reveal <= 0:
        return
    pulse = math.exp(-(t - b(46)) / 0.4) if t >= b(46) else 0.0
    PILE_BELL.draw(fr, reveal=reveal, alpha=a, glow=0.7 + 1.1 * pulse)
    fr.light_sweep(PILE_BELL.outline(), lin(t, b(46), b(46) + 0.8), strength=0.95)


def draw_s01(fr, t):
    z = 1 + 0.55 * s01_zoom(t)
    u = s01_zoom(t)
    hx, hy = hero_focus(t)
    m = zoom_matrix(z, W / 2 + (hx - W / 2) * u * 0.85, H / 2 + (hy - H / 2) * u * 0.85)
    with view(fr, m):
        draw_board_content(fr, t)
    hud.pill(fr, 1460, 140, "×6", "muted", env(t, b(29) + 0.2, 13.6, 0.4, 0.5), 22)
    fr.chroma(chroma_kick(t, b(46), 7.0))


# ------------------------------------------------------------------ S02: bell after bell

HEIGHTS = crowd.sample_heights()
PX_CM, DOT_R = 14.0, 1.2
COLS = int(PX_CM // (2 * DOT_R))
HFLOOR, HCX = 900.0, 1240.0
CM_AX = Axes(cx=HCX, floor=HFLOOR, unit=PX_CM * crowd.SD_CM,
             hscale=len(HEIGHTS) * 2 * DOT_R / (crowd.SD_CM * COLS) * 1.04)
CM_BELL = Bell(CM_AX, -3.4, 3.4)
DOTS = crowd.dot_layout(HEIGHTS, lambda v: HCX + (np.asarray(v) - crowd.MEAN_CM) * PX_CM, 1.0, DOT_R, HFLOOR)
WALKERS = 11
HEIGHTS_HOME = (900.0, 430.0, 680.0, 500.0)

BOX = (0.0, 0.0, 430.0, 320.0)  # canonical panel box for star / sensor / exam
AX_BOX = Axes(cx=270.0, floor=285.0, unit=42.0, hscale=330.0)
BOX_BELL = Bell(AX_BOX, -3.3, 3.3)
EDGES = np.linspace(-3.2, 3.2, 17)

L1 = [(60, 150, 380, 300), (60, 530, 380, 300), (495, 330, 430, 320), (960, 330, 430, 320), (1425, 330, 430, 320)]
ARC_Y = (36, 10, 0, 10, 36)
L2 = [(40 + i * 372, 380 + ARC_Y[i], 352, 264) for i in range(5)]
LABELS = ("pegs", "heights", "star position", "sensor noise", "exam scores")
LIT = (b(81), b(81), b(83), b(83), b(85))  # "bell after bell after bell"
FLY0 = b(85) + 0.2

CENTER_AX = Axes(cx=960.0, floor=600.0, unit=150.0, hscale=700.0)
CENTER = Bell(CENTER_AX)


@lru_cache(maxsize=8)
def stratified(seed, n=360):
    """Normal samples that fill a smooth histogram once all have arrived (random order)."""
    rng = np.random.default_rng(seed)
    return ndtri((rng.permutation(n) + 0.5) / n), rng.normal(0, 1, n)


# Each box panel: (seed, sampling window start, end). Its bell snaps at the window end.
BOXES = {2: (31, b(64), b(67) + 0.2), 3: (32, b(69), b(73) + 0.15), 4: (33, b(75), b(79) + 0.1)}


def panel_rect(i, t):
    """Where panel i sits at time t (S02 layout choreography)."""
    u2 = ease_io(lin(t, 28.35, 29.0))
    if i == 0:
        r = lerp_rect(BOARD_HOME, L1[0], ease_io(lin(t, 17.2, 18.0)))
    elif i == 1:
        r = lerp_rect(HEIGHTS_HOME, L1[1], ease_io(lin(t, 21.2, 21.9)))
    else:
        start = BOXES[i][1] - 0.45
        r = L1[i]
        r = (r[0] + 70 * (1 - ease_out(lin(t, start, start + 0.5))), *r[1:])
    return lerp_rect(r, L2[i], u2)


def panel_home(i):
    return BOARD_HOME if i == 0 else HEIGHTS_HOME if i == 1 else BOX


def panel_alpha(i, t):
    if i == 0:
        a = 1.0
    elif i == 1:
        a = smooth(lin(t, b(48) - 0.1, b(48) + 0.3))
    else:
        a = smooth(lin(t, BOXES[i][1] - 0.45, BOXES[i][1]))
    dim = 1 - 0.8 * smooth(lin(t, b(86), b(86) + 0.6))
    return a * dim * (1 - smooth(lin(t, 33.6, 34.6)))


def card_alpha(i, t):
    if i == 0:
        return smooth(lin(t, 17.5, 18.0))
    if i == 1:
        return smooth(lin(t, 21.3, 21.9))
    return 1.0


def ready_at(i):
    """When panel i's bell has finished snapping and settles to its resting brightness."""
    return 17.2 if i == 0 else b(54) + 1.5 if i == 1 else BOXES[i][2] + 1.5


def curve_state(i, t):
    """(alpha, glow pulse) of a panel's bell: full after its snap, resting at 0.55, lit again on its "bell"."""
    rest = 0.55 + 0.45 * (1 - smooth(lin(t, ready_at(i), ready_at(i) + 0.6)))
    pulse = math.exp(-(t - LIT[i]) / 0.45) if t >= LIT[i] else 0.0
    return (rest + (1 - rest) * smooth(lin(t, LIT[i], LIT[i] + 0.2))), pulse


def fly_u(i, t):
    return ease_io(lin(t, FLY0 + 0.07 * i, FLY0 + 0.8 + 0.07 * i))


def draw_heights_content(fr, t, alpha, curve_a=1.0, glow=0.7, show_curve=True):
    if alpha <= 0.003:
        return
    # silhouettes walk in, then collapse into their own dots
    cu = ease_io(lin(t, b(52), b(52) + 0.7))
    for k in range(WALKERS):
        walk = ease_out(lin(t, b(48) + 0.05 * k, b(48) + 1.0 + 0.05 * k))
        x0 = 760 + k * 96 + 900 * (1 - walk)
        bob = 5 * abs(math.sin(9 * t + k)) * (1 - walk)
        hp = HEIGHTS[k] * 1.6
        fx_, fy_ = DOTS[k]
        x = x0 + (fx_ - x0) * cu
        y = HFLOOR - bob + (fy_ - HFLOOR) * cu
        crowd.person(fr, x, y, hp * (1 - cu) + 2 * cu, alpha * (1 - cu), fill=0.06)
    n = int(WALKERS + (len(HEIGHTS) - WALKERS) * smooth(lin(t, b(52) + 0.3, b(52) + 1.4)))
    if cu >= 1.0:
        draw_dots(fr, DOTS[:n], DOT_R, "ball", alpha)
    elif t > b(52) + 0.3:
        draw_dots(fr, DOTS[WALKERS:n], DOT_R, "ball", alpha)
    hud.tabular(fr, f"{max(n, WALKERS) if cu > 0 else 0:,}", HCX, 500, 40, "ink",
                alpha * smooth(lin(t, b(52), b(52) + 0.3)))
    if show_curve:
        if t < b(54) + 1.5:
            CM_BELL.snap(fr, t, b(54), alpha=alpha * curve_a)
        else:
            CM_BELL.draw(fr, alpha=alpha * curve_a, glow=glow)


def draw_box_content(fr, i, t, alpha, curve_a=1.0, glow=0.7, show_curve=True):
    seed, t0, t1 = BOXES[i]
    z, z2 = stratified(seed)
    n = int(len(z) * smooth(lin(t, t0, t1)))
    cur = max(0, n - 1)
    AX_BOX.floor_line(fr, -3.4, 3.4, alpha)
    if n > 1:
        draw_bars(fr, AX_BOX, bars_from_samples(z[:n], EDGES), alpha, gap=0.16, glow=0.2)
    live = t0 <= t <= t1 + 0.3
    if i == 2:  # a star and the jittering crosshair of each measurement
        sx, sy = 72.0, 150.0
        star = star_path(sx, sy, 15, 6.5, 4)
        fr.path_fill(star, "ink", alpha, glow=0.8)
        if live:
            cx_, cy_ = sx + 9 * z[cur], sy - 9 * z2[cur]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                fr.line(cx_ + 7 * dx, cy_ + 7 * dy, cx_ + 22 * dx, cy_ + 22 * dy, "ball", 2.0, alpha, glow=0.5)
    elif i == 3:  # a patch of flickering sensor pixels
        rng = np.random.default_rng(int(t * 20) % 997)
        vals = np.clip(0.42 + 0.14 * rng.normal(0, 1, (8, 8)), 0, 1) if live else np.full((8, 8), 0.42)
        for r in range(8):
            for c in range(8):
                g = int(40 + 150 * vals[r, c])
                fr.rrect(22 + c * 12, 100 + r * 12, 11, 11, 1.5, fill=f"#{g:02x}{g:02x}{g:02x}", alpha=alpha)
    else:  # an exam card with the current score
        fr.rrect(26, 96, 98, 126, 8, fill="#0E131C", stroke="line", alpha=alpha)
        for k in range(4):
            fr.line(40, 120 + 14 * k, 110 - 12 * (k % 2), 120 + 14 * k, "muted", 1.4, alpha * 0.5)
        score = int(np.clip(round(68 + 12 * z[cur]), 0, 100)) if n else 0
        fr.text(str(score), 75, 205, "sans", 30, 700, "ink", alpha * (1.0 if n else 0.0))
    if show_curve and t >= t1:
        if t < t1 + 1.5:
            BOX_BELL.snap(fr, t, t1, alpha=alpha * curve_a)
        else:
            BOX_BELL.draw(fr, alpha=alpha * curve_a, glow=glow)


def star_path(x, y, r_out, r_in, points=5, rot=-math.pi / 2):
    p = skia.Path()
    for k in range(points * 2):
        r = r_out if k % 2 == 0 else r_in
        a = rot + k * math.pi / points
        (p.moveTo if k == 0 else p.lineTo)(x + r * math.cos(a), y + r * math.sin(a))
    p.close()
    return p


def panel_curve_points(i, n=200):
    """A panel's bell in its own home coordinates (to transform and fly)."""
    if i == 0:
        return PILE_BELL.points(n=n)
    if i == 1:
        return CM_BELL.points(n=n)
    return BOX_BELL.points(n=n)


def draw_panels(fr, t):
    if t < 17.2 or t > 34.6:
        return
    blur = 5.0 * smooth(lin(t, b(86), b(86) + 0.6))
    flying = []
    with fr.blurred(blur):
        for i in range(5):
            a = panel_alpha(i, t)
            if a <= 0.003 or (i == 1 and t < b(48) - 0.1):
                continue
            rect = panel_rect(i, t)
            ca = card_alpha(i, t) * a
            if ca > 0.003:
                hud.glass_card(fr, *rect, ca, r=16)
                fr.text(LABELS[i], rect[0] + 18, rect[1] + 30, "sans", 17, 600, "muted", ca, align="left")
            m = fit_matrix(panel_home(i), rect)
            calpha, pulse = curve_state(i, t) if t >= ready_at(i) else (1.0, 0.0)
            fu = fly_u(i, t)
            with view(fr, m):
                if i == 0:
                    draw_board_content(fr, t, a, curve_alpha=calpha * (fu <= 0), live=False)
                elif i == 1:
                    draw_heights_content(fr, t, a, calpha, 0.7 + pulse, show_curve=fu <= 0)
                else:
                    draw_box_content(fr, i, t, a, calpha, 0.7 + pulse, show_curve=fu <= 0)
            if fu > 0:
                flying.append((i, m, fu))
    draw_flight(fr, t, flying)


def draw_flight(fr, t, flying):
    """Five curves lift out of their panels and land on one centre bell (02C)."""
    if not flying:
        return
    tx, ty = CENTER.points(n=200)
    for i, m, u in flying:
        if u >= 1.0:
            continue
        xs, ys = map_pts(m, *panel_curve_points(i))
        lift = 60 * math.sin(math.pi * u)
        x = xs + (tx - xs) * u
        y = ys + (ty - ys) * u - lift
        fr.poly(x, y, "bell", 2.6 + 0.6 * u, 1.0, glow=0.9)


def center_alpha(t):
    landed = smooth(lin(t, FLY0 + 0.75, FLY0 + 1.2))
    dimmed = 1 - 0.65 * smooth(lin(t, b(86) + 0.4, b(86) + 1.0))
    bright = smooth(lin(t, 35.8, 36.3))
    return landed * (dimmed + (1 - dimmed) * bright)


def draw_icons(fr, t):
    a_all = 1 - smooth(lin(t, 36.4, 37.1))
    if t < b(86) or a_all <= 0:
        return
    for k, (cue_i, x) in enumerate(((86, 560.0), (87, 960.0), (89, 1360.0))):
        u = ease_out(lin(t, b(cue_i), b(cue_i) + 0.5))
        a = a_all * smooth(u)
        if a <= 0.003:
            continue
        if k == 0:  # three rows of pegs and a ball
            for r in range(3):
                for j in range(r + 1):
                    fr.circle(x + (j - r / 2) * 26, 860 + r * 24, 4.0 * u, "line", alpha=a, fill=True)
                    fr.circle(x + (j - r / 2) * 26, 860 + r * 24, 4.0 * u, "muted", 1.0, a)
            fr.glow_dot(x + 6, 834, 6 * u, "ball", a)
        elif k == 1:
            crowd.person(fr, x, 940, 130 * (0.6 + 0.4 * u), a, fill=0.06)
        else:
            fr.path_stroke(star_path(x, 880, 46 * u, 19 * u), "ink", 2.0, a, glow=0.4)
    for x, at in ((760.0, b(91)), (1160.0, b(93))):
        u = ease_out(lin(t, at, at + 0.5))
        fr.line(x, 820, x, 820 + 130 * u, "line", 1.6, a_all * smooth(u))


# ------------------------------------------------------------------ S03: the questions and the promise

FORMULA = f"f(x) = 1/(sigma sqrt(2 {tc('pi', 'pi')})) e^(-(x - mu)^2 / (2 sigma^2))"
F_XY, F_SIZE = (960.0, 730.0), 50.0
PI_IDX = next(i for i, g in enumerate(typmath.glyphs(FORMULA)[0]) if g.color.lower() == TOKENS["pi"].lower())
PI_FROM = typmath.glyph_centers(FORMULA, *F_XY, F_SIZE)[PI_IDX]
PI_AT, PI_CORNER = (1500.0, 360.0), (1790.0, 112.0)

CHIP_W, CHIP_H, CHIP_Y = 300.0, 190.0, 830.0
CHIP_X = (180.0, 600.0, 1020.0, 1440.0)
CHIP_T = (b(129), b(134), b(140), b(150))  # coin flip, hidden circle, simple ruler, bell breaks
CHIP_TARGET = Target(cx=150.0, cy=96.0, unit=24.0, n=140, seed=12)
CHIP_AX = Axes(cx=150.0, floor=160.0, unit=36.0, hscale=280.0)
CHIP_BELL = Bell(CHIP_AX, -3.4, 3.4)
CRACK_AT = 0.9


ICON_X = (560.0, 960.0, 1360.0)
MINI_AX = [Axes(cx=x, floor=800.0, unit=40.0, hscale=170.0) for x in ICON_X]


def draw_feeds(fr, t):
    """03A: a small gold bell rises over each icon, then all three fly into the centre bell."""
    if t < b(95) or t > 36.6:
        return
    tx, ty = CENTER.points(n=160)
    for i, ax in enumerate(MINI_AX):
        rise = ease_out(lin(t, b(95) + 0.1 * i, b(95) + 0.6 + 0.1 * i))
        u = ease_io(lin(t, b(95) + 0.55 + 0.1 * i, b(95) + 1.35 + 0.1 * i))
        if rise <= 0 or u >= 1:
            continue
        xs, ys = Bell(ax, -3.2, 3.2).points(scale=rise, n=160)
        lift = 50 * math.sin(math.pi * u)
        fr.poly(xs + (tx - xs) * u, ys + (ty - ys) * u - lift, "bell", 2.4, rise, glow=0.8)


def draw_question(fr, t):
    a = smooth(lin(t, b(102), b(102) + 0.3)) * (1 - smooth(lin(t, 38.0, 38.5)))
    if a > 0.003:
        s = 1 + 0.25 * math.exp(-max(0.0, t - b(102)) / 0.2)
        fr.text("?", 960, 300, "display", 64 * s, 500, "muted", a)


def draw_formula(fr, t):
    a = 0.6 * smooth(lin(t, b(107), b(107) + 0.3)) * (1 - smooth(lin(t, 42.9, 43.4)))
    if t < b(107) or t > 53.0:
        return
    lifted = t >= b(109)
    if a > 0.003:
        typmath.draw(fr, FORMULA, *F_XY, F_SIZE, color="ink", alpha=a, reveal=lin(t, b(107), b(107) + 0.9),
                     alphas={PI_IDX: 0.0} if lifted else None)
    if not lifted:
        return
    # the pi lifts out, enlarges, gets its circle, loses it, and is left with a question
    u = ease_io(lin(t, b(109), b(109) + 0.75))
    c = ease_io(lin(t, 42.9, 43.5))
    x = PI_FROM[0] + (PI_AT[0] - PI_FROM[0]) * u
    y = PI_FROM[1] + (PI_AT[1] - PI_FROM[1]) * u - 50 * math.sin(math.pi * u)
    size = F_SIZE * 0.72 + (170 - F_SIZE * 0.72) * u
    x, y = x + (PI_CORNER[0] - x) * c, y + (PI_CORNER[1] - y) * c
    size = size + (54 - size) * c
    pa = (1 - 0.45 * c) * (1 - smooth(lin(t, 52.4, 52.9)))
    typmath.draw(fr, "pi", x, y, size, color="pi", alpha=pa, glow=0.8 * (1 - c) + 0.3)
    ring = ease_io(lin(t, b(113), b(113) + 0.8)) * (1 - smooth(lin(t, b(117), b(117) + 0.6)))
    if ring > 0.003 and c <= 0:
        p = skia.Path()
        p.addArc(skia.Rect.MakeLTRB(x - 125, y - 125, x + 125, y + 125), -90, 359.9 * min(1.0, ring * 1.0))
        fr.path_stroke(p, "pi", 3.0, min(1.0, ring * 3), glow=0.8)
    qa = smooth(lin(t, b(121), b(121) + 0.3)) * pa
    if qa > 0.003:
        fr.text("?", x + size * 0.62, y - size * 0.18, "display", size * 0.5, 500, "pi", qa, glow=0.4)


def draw_scan(fr, t):
    """03B: a scan line crosses the bell looking for a circle, and finds none."""
    u = ease_io(lin(t, b(117), b(121)))
    if not 0 < u < 1:
        return
    x = 400 + 1120 * u
    a = math.sin(math.pi * u)
    fr.line(x, 230, x, 620, "ink", 1.6, 0.45 * a, glow=0.6)
    fr.light_sweep(CENTER.outline(), u, strength=0.5 * a, width=0.05, angle=0.0)


def draw_chips(fr, t):
    fade = 1 - smooth(lin(t, 52.6, 53.3))
    for k, (x, t0) in enumerate(zip(CHIP_X, CHIP_T)):
        a = smooth(lin(t, t0 - 0.35, t0)) * fade
        if a <= 0.003:
            continue
        nxt = CHIP_T[k + 1] if k < 3 else 1e9
        dim = 1 - 0.5 * smooth(lin(t, nxt - 0.3, nxt))
        y = CHIP_Y + 24 * (1 - ease_out(lin(t, t0 - 0.35, t0 + 0.1)))
        hud.glass_card(fr, x, y, CHIP_W, CHIP_H, a, r=16, glow=0.4 * (dim > 0.9) * a, glow_color="bell")
        m = skia.Matrix()
        m.setTranslate(x, y)
        with view(fr, m):
            CHIP_DRAW[k](fr, t, t0, a * dim)


def chip_coin(fr, t, t0, a):
    land = t0 + 0.9
    if t < land:
        ph = 16 * max(0.0, t - t0 + 0.35)
        w = 20 * abs(math.cos(ph))
        color = "left" if math.cos(ph) > 0 else "right"
        y = 66 - 26 * math.sin(math.pi * min(1.0, max(0.0, (t - t0 + 0.35) / 1.25)))
        fr.path_fill(_ellipse(150, y, w, 20), color, a * 0.85, glow=0.4)
        fr.path_stroke(_ellipse(150, y, w * 0.72, 14.4), "bg", 1.4, a * 0.5)
    fr.circle(150, 112, 5, "line", alpha=a, fill=True)
    u = ease_out(lin(t, land, land + 0.5))
    if u > 0:
        fr.line(150, 112, 150 - 40 * u, 112 + 50 * u, "left", 3, a, glow=0.6)
        fr.line(150, 112, 150 + 40 * u, 112 + 50 * u, "right", 3, a, glow=0.6)


def _ellipse(x, y, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(x - max(rx, 1.5), y - ry, x + max(rx, 1.5), y + ry))
    return p


def chip_circle(fr, t, t0, a):
    CHIP_TARGET.draw_darts(fr, t, t0 - 0.2, 180, a, r=2.4)
    CHIP_TARGET.draw_rings(fr, a * smooth(lin(t, t0 + 0.7, t0 + 1.2)), radii=(1.2,), width=2.4)


def chip_ruler(fr, t, t0, a):
    CHIP_AX.floor_line(fr, -3.4, 3.4, a)
    for k in (3, 2, 1):
        CHIP_BELL.band(fr, k, alpha=a, fill=0.18, edges=False, u=lin(t, t0 + 0.1 * (3 - k), t0 + 0.6 + 0.1 * (3 - k)))
    for k in range(-3, 4):
        x = float(CHIP_AX.x(k))
        fr.line(x, CHIP_AX.floor + 4, x, CHIP_AX.floor + (12 if k else 16), "sigma", 1.6, a)
    CHIP_BELL.draw(fr, alpha=a, width=2.4)


def chip_break(fr, t, t0, a):
    CHIP_AX.floor_line(fr, -3.4, 3.4, a)
    if t < t0:
        CHIP_BELL.draw(fr, alpha=a, width=2.4)
    else:
        CHIP_BELL.crack(fr, lin(t, t0, t0 + 0.4), at=CRACK_AT, alpha=a, width=2.4, gap=7)


CHIP_DRAW = (chip_coin, chip_circle, chip_ruler, chip_break)


def draw_center(fr, t):
    """The one bell that S02 lands and S03 interrogates, cracks and breaks."""
    a = center_alpha(t)
    if a <= 0.003:
        return
    pull = ease_io(lin(t, b(162), b(162) + 1.3))
    m = zoom_matrix(1 - 0.14 * pull, 960, 470, 960, 470 - 40 * pull)
    with view(fr, m):
        CENTER_AX.floor_line(fr, -3.6, 3.6, a * 0.8)
        if t < CHIP_T[3]:
            CENTER.draw(fr, alpha=a)
        else:
            CENTER.crack(fr, lin(t, CHIP_T[3], CHIP_T[3] + 0.45), at=CRACK_AT, alpha=a)
            CENTER.tail(fr, lin(t, b(156), b(156) + 1.0), at=CRACK_AT, alpha=a, reach=14.0)
    fr.chroma(chroma_kick(t, CHIP_T[3], 6.0))
    fr.chroma(chroma_kick(t, b(156), 4.0))


def draw_title(fr, t):
    a = smooth(lin(t, b(162), b(162) + 0.7))
    if a <= 0.003:
        return
    rise = 20 * (1 - ease_out(lin(t, b(162), b(162) + 0.9)))
    title = "THE BELL CURVE"
    fr.text(title, 960, 860 + rise, "display", 92, 600, "ink", a, tracking=0.06)
    fr.text("why it's everywhere", 960, 922 + rise, "sans", 34, 500, "bell", a * smooth(lin(t, b(164), b(164) + 0.6)))
    fr.light_sweep(text_path(title, 960, 860 + rise, "display", 92, 600, tracking=0.06), lin(t, b(167), b(167) + 0.8),
                   strength=0.95)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    if t < 17.2:
        draw_s01(fr, t)
    draw_panels(fr, t)
    draw_center(fr, t)
    draw_icons(fr, t)
    draw_feeds(fr, t)
    draw_question(fr, t)
    draw_scan(fr, t)
    draw_formula(fr, t)
    draw_chips(fr, t)
    draw_title(fr, t)
    out = smooth(lin(t, END - 0.45, END))
    if out > 0:
        fr.zoom_blur(0.3 * out)
        fr.dim(out)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def blur_weight(t):
    return 1.0 if t < 17.2 else 0.0


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
STILLS = [2.0, 4.8, 8.0, 13.6, 16.4, 19.5, 24.0, 30.9, 33.5, 36.3, 40.0, 46.2, 51.5, 55.5]
