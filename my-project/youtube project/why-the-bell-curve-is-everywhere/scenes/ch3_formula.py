"""CHAPTER 3 - WHERE e AND π COME FROM (S13-S16), 03:10.500 (#560 "So") - 04:55.220 (#883 "Those").

S13  The dart target   push into the bell's shoulder -> it fades -> a target, darts land and scatter -> two rule cards ->
                       rule 1: a hero dart's teal and orange errors, marginals, a strip sweep that leaves the orange
                       marginal unchanged ("independent") -> rule 2: a ring through the dart, it slides, density fixed.
S14  e^(-x^2)          the cards merge -> the teal marginal lifts out -> e^(-x^2) builds and its curve traces the bars ->
                       real f(x)f(y) contours: triangle (diamonds), 1/(1+x^2) (stars), Gaussian (circles) -> e^x mirrors
                       into decay -> the parabola: -2 and +2 both give 4 -> double the distance: 0.368 vs 0.018 (÷ 20).
S15  The hidden circle darts with pink rings -> the area under the curve fills (area = 1) -> the curve spins into a 3D
                       surface that splits into pink shells -> the view rises to top-down: the shells are the rings ->
                       the integral morphs to sqrt(pi) -> the pink π from the cold open lands in the bullseye.
S16  The formula       built term by term on its words -> shrinks to the top -> μ and σ fly into two dials -> the bell
                       slides, widens, narrows -> ±σ, μ to μ + σ -> 1/(σ√(2π)) glows while area = 1.000 holds.
"""

from __future__ import annotations

import contextlib
import math
from functools import cache
from pathlib import Path

import numpy as np
import skia
import typmath
from components import hud
from components.bell import Bell, pdf
from components.darts import Target
from components.dials import dial_pair
from components.histogram import Axes, Bars, bars_from_samples, draw_bars, morph
from cues import AUDIO, beat, cue
from fx import Frame, chroma_kick, clamp, ease_in, ease_io, ease_out, env, lin, smooth
from scipy.special import ndtr
from space import orbit
from theme import THEME, H, W
from typmath import tc

START = cue(560)  # 190.50 "So what is the exact shape of this curve?"
END = cue(883)  # 295.22 "Those two dials ..."

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


def zoom_at(z, fx_, fy_):
    m = skia.Matrix()
    m.setScale(z, z, fx_, fy_)
    return m


def lerp(a, b_, u):
    return a + (b_ - a) * u


def lerp_axes(a: Axes, c: Axes, u):
    return Axes(lerp(a.cx, c.cx, u), lerp(a.floor, c.floor, u), lerp(a.unit, c.unit, u), lerp(a.hscale, c.hscale, u))


def poly_path(xs, ys, close=False):
    p = skia.Path()
    p.moveTo(float(xs[0]), float(ys[0]))
    for x, y in zip(xs[1:], ys[1:]):
        p.lineTo(float(x), float(y))
    if close:
        p.close()
    return p


# ------------------------------------------------------------------ S13A: the bell's shoulder

PREV_AX = Axes(cx=960.0, floor=700.0, unit=165.0, hscale=1000.0)  # chapter 2's last bell (S12C)
PREV = Bell(PREV_AX, -3.2, 3.2, n=320)
SHAPE_T = b(564)  # "exact shape"
SURPRISE_T = b(574)  # "surprising place": the bell fades


def draw_prev_bell(fr, t):
    a = 1 - smooth(lin(t, SURPRISE_T, SURPRISE_T + 0.7))
    if a <= 0.003:
        return
    sx, sy = float(PREV_AX.x(1.0)), float(PREV_AX.y(pdf(1.0)))
    z = 1 + 0.9 * ease_io(lin(t, SHAPE_T, SHAPE_T + 1.6)) + 0.25 * ease_in(lin(t, SURPRISE_T, SURPRISE_T + 0.7))
    with view(fr, zoom_at(z, sx, sy)):
        fr.path_fill(PREV.area_path(), "bell", a * 0.10)
        PREV.draw(fr, alpha=a, width=4.0, glow=0.8)
    qa = a * env(t, SHAPE_T + 0.6, SURPRISE_T + 0.4, 0.4, 0.3)
    fr.text("?", sx + 90, sy - 70, "display", 96, 600, "ink", qa)


# ------------------------------------------------------------------ S13: the dart target and its two rules

TG = Target(cx=680.0, cy=520.0, unit=85.0)
TG_EDGES = np.linspace(-3.2, 3.2, 25)
BOARD_T = b(577)  # "throwing darts at a target"
SCATTER_T = b(585)  # "not perfect"
TWO_T = b(590)  # "two things"
FIRST_T = b(592)  # "First"
LR_T = b(595)  # "left or right"
NOTHING_T = b(599)  # "nothing to do with"
UD_T = b(605)  # "up or down"
SECOND_T = b(608)  # "Second"
DIST_T = b(611)  # "distance from the center matters"
DIR_T = b(616)  # "Not the direction"
MERGE_T = b(623)  # "force a single answer"
LIFT_T = b(630)  # "missing by a distance x"
HERO = int(np.argmin(np.hypot(TG.z[:, 0] - 1.15, TG.z[:, 1] - 0.85)))
STRIPS = ((-1.9, -1.1), (-0.8, 0.0), (0.0, 0.8), (1.1, 1.9))
STRIP_T = NOTHING_T + 0.1
STRIP_D = 0.62
CARD_X, CARD_W, CARD_H = 1240.0, 560.0, 150.0
CARD_Y = (300.0, 500.0)
BASE_Y = TG.cy + 3.6 * TG.unit + 30 + 0.42 * 170  # floor of the teal marginal under the target
TEAL_AX = Axes(cx=TG.cx, floor=BASE_Y, unit=TG.unit, hscale=170.0)


def darts_n(t):
    """Darts landed: a few slow throws, then the scatter (about 300)."""
    if t < BOARD_T + 0.5:
        return 0
    if t < SCATTER_T:
        return int((t - BOARD_T - 0.5) * 3.5) + 1
    return min(TG.n, int(6 + 170 * (t - SCATTER_T)))


def target_alpha(t):
    return smooth(lin(t, BOARD_T, BOARD_T + 0.6)) * (1 - smooth(lin(t, LIFT_T - 0.6, LIFT_T + 0.2)))


def strip_now(t):
    for k, (z0, z1) in enumerate(STRIPS):
        t0 = STRIP_T + k * STRIP_D
        if t0 <= t < t0 + STRIP_D:
            return z0, z1, env(t, t0, t0 + STRIP_D, 0.12, 0.12)
    return None


def draw_target(fr, t):
    a = target_alpha(t)
    if a <= 0.003:
        return
    TG.draw_board(fr, a, reveal=ease_out(lin(t, BOARD_T, BOARD_T + 0.8)))
    n = darts_n(t)
    rate = 60.0
    tv = BOARD_T + n / rate  # virtual clock so the impact rings follow our landing curve
    st = strip_now(t)
    mask = None
    hero_on = smooth(lin(t, FIRST_T, FIRST_T + 0.4))
    if st is not None:
        z0, z1, sa = st
        mask = TG.strip(z0, z1)
        x0, x1 = float(TG.cx + z0 * TG.unit), float(TG.cx + z1 * TG.unit)
        fr.rrect(x0, TG.cy - 3.6 * TG.unit, x1 - x0, 7.2 * TG.unit, 6, fill="left", fill_alpha=0.07 * sa, alpha=a)
    TG.draw_darts(fr, tv, BOARD_T, rate, a * (1 - 0.35 * hero_on * (mask is None)), mask=mask, dim=0.22)
    if n > 0 and t < SCATTER_T + 2.0:
        last = min(n, TG.n) - 1
        age = (t - BOARD_T) % 0.3
        fr.circle(*TG.xy[last], 4 + 14 * age / 0.3, "ink", 1.2, a * (1 - age / 0.3) * 0.6)
    # marginals: teal along the bottom (all darts), orange up the side (the strip's darts while it sweeps)
    ta = a * smooth(lin(t, LR_T + 0.3, LR_T + 0.9))
    if ta > 0.003 and n > 2:
        bars = bars_from_samples(TG.z[:n, 0], TG_EDGES)
        draw_bars(fr, TEAL_AX, bars, ta, color="left", gap=0.12, glow=0.2)
    oa = a * smooth(lin(t, NOTHING_T, NOTHING_T + 0.5))
    if oa > 0.003:
        TG.draw_marginals(fr, n, oa, edges=np.linspace(-3.2, 3.2, 17), strip_mask=mask, gap=30.0, horiz=False)
    # the hero dart: its two independent errors, then its ring
    ha = a * hero_on
    if ha > 0.003:
        uh = ease_out(lin(t, LR_T, LR_T + 0.5))
        uv = ease_out(lin(t, UD_T, UD_T + 0.5))
        err_a = ha * (1 - smooth(lin(t, SECOND_T, SECOND_T + 0.5)))
        if err_a > 0.003:
            TG.draw_errors(fr, HERO, uh, uv, err_a)
        draw_ring_rule(fr, t, ha)
        if err_a > 0.003 and t < DIR_T:
            x, y = TG.xy[HERO]
            fr.glow_dot(x, y, 7.0, "ball", ha, strength=1.4)


def draw_ring_rule(fr, t, a):
    """Rule 2: the ring through the hero dart, its radius, the dart sliding round, a density that does not move."""
    ra = a * smooth(lin(t, DIST_T, DIST_T + 0.5))
    if ra <= 0.003:
        return
    zx, zy = TG.z[HERO]
    r = math.hypot(zx, zy)
    th0 = math.atan2(zy, zx)
    u = ease_io(lin(t, DIR_T, DIR_T + 1.3))
    th = th0 + 3.4 * u
    R = r * TG.unit
    fr.circle(TG.cx, TG.cy, R * ease_out(lin(t, DIST_T, DIST_T + 0.6)), "ink", 2.0, ra * 0.9, glow=0.4)
    x, y = TG.cx + R * math.cos(th), TG.cy - R * math.sin(th)
    fr.line(TG.cx, TG.cy, x, y, "ink", 2.0, ra, glow=0.3)
    mx, my = (TG.cx + x) / 2, (TG.cy + y) / 2
    fr.text("r", mx + 14 * math.sin(th), my + 14 * math.cos(th) + 8, "sans", 30, 600, "ink", ra)
    fr.glow_dot(x, y, 7.0, "ball", ra, strength=1.4)
    dens = math.exp(-r * r / 2) / (2 * math.pi)
    hud.readout(fr, x + 100 * math.cos(th) + 30, y - 100 * math.sin(th) - 10, "density", f"{dens:.3f}", "ball",
                ra * smooth(lin(t, DIR_T - 0.3, DIR_T + 0.1)), size=26)


def card_rect(i, t):
    """Rule card i: home on the right, merging into one plaque on "force a single answer"."""
    u = ease_io(lin(t, MERGE_T, MERGE_T + 0.8))
    y = lerp(CARD_Y[i], (CARD_Y[0] + CARD_Y[1]) / 2, u)
    return CARD_X, y, CARD_W, CARD_H


def draw_cards(fr, t):
    a = smooth(lin(t, TWO_T, TWO_T + 0.5)) * (1 - smooth(lin(t, LIFT_T - 0.3, LIFT_T + 0.3)))
    if a <= 0.003:
        return
    merged = ease_io(lin(t, MERGE_T, MERGE_T + 0.8))
    lit = (env(t, FIRST_T, SECOND_T + 0.2, 0.3, 0.4), smooth(lin(t, SECOND_T, SECOND_T + 0.4)))
    labels = ("independent", "round")
    label_t = (UD_T + 0.5, DIR_T + 0.5)
    for i in range(2):
        x, y, w, h = card_rect(i, t)
        ca = a * (1 - merged) if i == 1 else a
        glow = 0.6 * lit[i] * (1 - merged)
        hud.glass_card(fr, x, y, w, h, ca, r=22, glow=glow, glow_color="ball")
        if merged < 0.5:
            na = ca * (0.45 + 0.55 * lit[i]) * (1 - 2 * merged)
            fr.text(str(i + 1), x + 60, y + h / 2 + 30, "display", 84, 600, "ink" if lit[i] > 0.5 else "muted", na)
            la = ca * smooth(lin(t, label_t[i], label_t[i] + 0.4)) * (1 - 2 * merged)
            fr.text(labels[i], x + 140, y + h / 2 + 14, "sans", 40, 600, "ink", la, align="left")
    ma = a * smooth(lin(t, MERGE_T + 0.5, MERGE_T + 0.9))
    if ma > 0.003:
        x, y, w, h = card_rect(0, t)
        hud.glass_card(fr, x, y, w, h, ma, r=22, glow=0.6 * env(t, MERGE_T + 0.5, LIFT_T, 0.3, 0.5), glow_color="bell")
        fr.text("independent  +  round", x + w / 2, y + h / 2 + 14, "sans", 38, 600, "ink", ma)


# ------------------------------------------------------------------ S14A: one answer, e^(-x^2)

AXE = Axes(cx=620.0, floor=780.0, unit=130.0, hscale=620.0)
BELLE = Bell(AXE, -3.4, 3.4)
EXACT = Bars((TG_EDGES[:-1] + TG_EDGES[1:]) / 2, np.diff(TG_EDGES),
             (ndtr(TG_EDGES[1:]) - ndtr(TG_EDGES[:-1])) / np.diff(TG_EDGES))
EXPR = f"{tc('e', 'e')}^(-x^2)"  # glyphs: 0 e, 1 minus, 2 x, 3 the 2
EXPR_AT, EXPR_SIZE = (620.0, 250.0), 120.0
GLYPH_T = (b(639), b(644), b(645), b(646))  # e, minus, x, squared
NOOTHER_T = b(647)  # "No other shape"
ROUND_T = b(660)  # "perfectly round"
E_T = b(666)  # "number e"
GROW_T = b(675)  # "natural growth"
REVERSE_T = b(678)  # "running in reverse"
DECAY_T = b(682)  # "natural decay"
WHYSQ_T = b(684)  # "Why x squared?"
LEFTM_T = b(690)  # "a mistake to the left"
RIGHTM_T = b(701)  # "to the right"
FAST_T = b(710)  # "fall off fast"
DOUBLE_T = b(713)  # "Double the distance"
HALVE_T = b(719)  # "does not just halve"
COLLAPSE_T = b(724)  # "It collapses."
CLEAR14 = cue(725) - 0.1  # "And now, the circle."


def s14_alpha(t):
    return smooth(lin(t, LIFT_T - 0.4, LIFT_T + 0.2)) * (1 - smooth(lin(t, CLEAR14, CLEAR14 + 0.5)))


def draw_lifted(fr, t):
    """The teal marginal lifts out of the target, becomes the exact distribution, and the curve traces over it."""
    a = s14_alpha(t)
    if a <= 0.003:
        return
    u = ease_io(lin(t, LIFT_T - 0.4, LIFT_T + 0.8))
    ax = lerp_axes(TEAL_AX, AXE, u)
    bars = morph(bars_from_samples(TG.z[:, 0], TG_EDGES), EXACT, smooth(lin(t, LIFT_T + 0.4, LIFT_T + 1.4)))
    dim = 1 - 0.45 * smooth(lin(t, GROW_T - 0.4, GROW_T + 0.2))
    ax.floor_line(fr, -3.4, 3.4, a * u)
    draw_bars(fr, ax, bars, a * dim * 0.9, color="left", gap=0.1, glow=0.15)
    # the x axis
    la = a * smooth(lin(t, LIFT_T + 0.6, LIFT_T + 1.1))
    for k in (-2, -1, 0, 1, 2):
        x = float(AXE.x(k * math.sqrt(2)))  # e^(-x^2) is the bell with x = z / sqrt(2)
        fr.line(x, AXE.floor, x, AXE.floor + 8, "muted", 1.4, la)
        fr.text(str(k).replace("-", "−"), x, AXE.floor + 34, "sans", 22, 500, "muted", la)
    fr.text("x", float(AXE.x(3.5)), AXE.floor + 8, "sans", 30, 600, "ink", la)
    # the curve traces as the formula is spoken
    trace = ease_io(lin(t, GLYPH_T[0], GLYPH_T[3] + 0.5))
    if trace > 0:
        BELLE.draw(fr, reveal=trace, alpha=a, width=3.6, glow=0.8)
    if trace >= 1:
        fr.light_sweep(BELLE.outline(width=3.6), lin(t, GLYPH_T[3] + 0.5, GLYPH_T[3] + 1.2), strength=0.9)


def draw_expr(fr, t):
    a = smooth(lin(t, GLYPH_T[0] - 0.1, GLYPH_T[0] + 0.2)) * (1 - smooth(lin(t, CLEAR14, CLEAR14 + 0.5)))
    if a <= 0.003:
        return
    alphas = {i: smooth(lin(t, t0, t0 + 0.25)) for i, t0 in enumerate(GLYPH_T)}
    eg = env(t, E_T, DECAY_T + 0.8, 0.3, 0.5)
    sq = math.exp(-((t - WHYSQ_T - 0.25) / 0.2) ** 2) + math.exp(-((t - WHYSQ_T - 0.75) / 0.2) ** 2)
    glows = {0: 1.4 * eg, 2: 1.2 * sq, 3: 1.2 * sq}
    pop = {0: 1.0}
    size = EXPR_SIZE * (1 + 0.06 * pop[0] * eg)
    typmath.draw(fr, EXPR, *EXPR_AT, size, alpha=a, alphas=alphas, glows=glows)


# --- contours of f(x) f(y) for three candidate curves (computed, not drawn by hand)

CANDIDATES = (
    ("triangle", lambda v: np.maximum(0.0, 1 - np.abs(v) / 2.5), "muted"),
    ("1 / (1 + x²)", lambda v: 1 / (1 + v * v), "muted"),
    ("e^(−x²)", lambda v: np.exp(-v * v), "pi"),
)
LEVELS = (0.8, 0.6, 0.4, 0.22, 0.1)


@cache
def contours(i):
    """Iso-lines of f(x) f(y) by radial bisection (each candidate falls off monotonically from the centre)."""
    f = CANDIDATES[i][1]
    th = np.linspace(0, 2 * np.pi, 240, endpoint=False)
    c, s = np.cos(th), np.sin(th)
    out = []
    for level in LEVELS:
        lo, hi = np.zeros_like(th), np.full_like(th, 6.0)
        for _ in range(42):
            mid = (lo + hi) / 2
            inside = f(mid * c) * f(mid * s) > level
            lo, hi = np.where(inside, mid, lo), np.where(inside, hi, mid)
        r = (lo + hi) / 2
        out.append((r * c, r * s))
    rmax = max(float(np.max(np.hypot(x, y))) for x, y in out)
    return out, rmax


def inset_rect(i, t):
    """Insets sit in a row; the round one grows and takes over on "perfectly round"."""
    x, y, s = 1120.0 + i * 250.0, 420.0, 230.0
    if i == 2:
        u = ease_io(lin(t, ROUND_T, ROUND_T + 0.8))
        x, y, s = lerp(x, 1230.0, u), lerp(y, 330.0, u), lerp(s, 470.0, u)
    return x, y, s


def draw_insets(fr, t):
    out = 1 - smooth(lin(t, E_T, E_T + 0.6))
    for i, (label, _, color) in enumerate(CANDIDATES):
        t0 = NOOTHER_T + 0.25 * i if i < 2 else NOOTHER_T + 1.6
        a = smooth(lin(t, t0, t0 + 0.45)) * out
        if i < 2:
            a *= 1 - smooth(lin(t, ROUND_T, ROUND_T + 0.6))
        if a <= 0.003:
            continue
        x, y, s = inset_rect(i, t)
        hud.glass_card(fr, x, y, s, s, a, r=18)
        lines, rmax = contours(i)
        k = s * 0.42 / rmax
        cx, cy = x + s / 2, y + s / 2
        draw = ease_out(lin(t, t0, t0 + 0.9))
        for j, (xs, ys) in enumerate(lines):
            la = a * clamp(draw * len(lines) - j)
            if la > 0.003:
                fr.path_stroke(poly_path(cx + xs * k, cy - ys * k, True), color, 1.8 if i < 2 else 2.4, la,
                               glow=0.6 if i == 2 else 0.0)
        fr.text(label, cx, y + s + 34, "sans", 24, 600, "muted" if i < 2 else "pi", a)
        if i < 2:  # struck out: these break one of the two rules
            u = ease_out(lin(t, t0 + 0.8, t0 + 1.1))
            if u > 0:
                fr.line(x + 14, y + s - 14, x + 14 + (s - 28) * u, y + s - 14 - (s - 28) * u, "muted", 2.6, a, glow=0.2)


# --- e^x into e^(-x), the parabola, the collapse (a plot panel on the right)

PANEL = (1120.0, 260.0, 700.0, 560.0)
PX0, PY0, PXS = 1470.0, 740.0, 95.0  # plot origin (x = 0 on the baseline) and px per x unit


def panel_alpha(t):
    return smooth(lin(t, GROW_T - 0.3, GROW_T + 0.2)) * (1 - smooth(lin(t, CLEAR14, CLEAR14 + 0.5)))


def plot_xy(x, y, ys):
    return PX0 + np.asarray(x) * PXS, PY0 - np.asarray(y) * ys


def draw_panel(fr, t):
    a = panel_alpha(t)
    if a <= 0.003:
        return
    x, y, w, h = PANEL
    hud.glass_card(fr, x, y, w, h, a, r=22)
    fr.line(x + 40, PY0, x + w - 40, PY0, "line", 1.6, a)
    fr.line(PX0, PY0 + 10, PX0, y + 40, "line", 1.2, a * 0.6)
    # 14B: e^x, mirrored into e^(-x), falling away in lime
    ga = a * (1 - smooth(lin(t, WHYSQ_T, WHYSQ_T + 0.4)))
    if ga > 0.003:
        xs = np.linspace(-2.9, 2.0, 160)
        flip = ease_io(lin(t, REVERSE_T, REVERSE_T + 0.7))
        u = ease_io(lin(t, GROW_T, GROW_T + 0.8))
        n = max(2, int(len(xs) * u))
        sign = 1 - 2 * flip
        px, py = plot_xy(sign * xs[:n], np.exp(xs[:n]), 50.0)
        decay = smooth(lin(t, DECAY_T, DECAY_T + 0.4))
        fr.poly(px, py, "e", 3.2, ga, glow=0.5 + 0.8 * decay)
        lab = "e^x" if flip < 0.5 else "e^(-x)"
        typmath.draw(fr, lab, PX0 + 200 * sign, y + 90, 48, color="e", alpha=ga * abs(1 - 2 * flip))
        fr.text("natural growth" if flip < 0.5 else "natural decay", x + w / 2, y + h - 22, "sans", 24, 600, "muted",
                ga * abs(1 - 2 * flip) * smooth(lin(t, GROW_T + 0.4, GROW_T + 0.8)))
    # 14C: the parabola: left and right mistakes count the same
    pa = a * smooth(lin(t, LEFTM_T - 0.3, LEFTM_T + 0.2)) * (1 - smooth(lin(t, FAST_T, FAST_T + 0.4)))
    if pa > 0.003:
        ys = 40.0
        xs = np.linspace(-3.0, 3.0, 160)
        n = max(2, int(len(xs) * ease_io(lin(t, LEFTM_T - 0.2, LEFTM_T + 0.6))))
        px, py = plot_xy(xs[:n], xs[:n] ** 2, ys)
        fr.poly(px, py, "ink", 3.0, pa, glow=0.4)
        typmath.draw(fr, "x^2", PX0 + 230, y + 100, 52, alpha=pa)
        for xv, color, t0 in ((-2.0, "left", LEFTM_T + 0.5), (2.0, "right", RIGHTM_T)):
            u = ease_out(lin(t, t0, t0 + 0.6))
            if u <= 0:
                continue
            bx, by = plot_xy(xv, 0.0, ys)
            tx, ty = plot_xy(xv, 4.0 * u, ys)
            fr.dashed([bx, bx], [by, ty], color, 2.0, pa)
            fr.glow_dot(float(bx), float(by), 7.0, color, pa, strength=1.3)
            fr.text(f"{int(xv):+d}".replace("-", "−"), float(bx), float(by) + 36, "sans", 26, 700, color, pa)
            if u >= 1:
                fr.dashed([float(tx), PX0], [float(ty), float(ty)], color, 1.6, pa * 0.8)
                fr.glow_dot(float(tx), float(ty), 6.0, color, pa, strength=1.2)
        meet = pa * smooth(lin(t, RIGHTM_T + 0.6, RIGHTM_T + 0.9))
        _, y4 = plot_xy(0.0, 4.0, ys)
        fr.text("4", PX0 - 26, float(y4) + 10, "sans", 32, 700, "ink", meet, glow=0.5)
    # back to e^(-x^2), then the two bars at x = 1 and x = 2
    ea = a * smooth(lin(t, FAST_T, FAST_T + 0.4))
    if ea > 0.003:
        ys = 400.0
        xs = np.linspace(-3.0, 3.0, 200)
        px, py = plot_xy(xs, np.exp(-xs * xs), ys)
        fr.poly(px, py, "bell", 3.0, ea, glow=0.6)
        typmath.draw(fr, EXPR, PX0 + 230, y + 90, 50, alpha=ea)
        e1, e4 = math.exp(-1), math.exp(-4)
        bw = 46.0
        drop = ease_in(lin(t, COLLAPSE_T, COLLAPSE_T + 0.32))
        squash = math.exp(-max(0.0, t - COLLAPSE_T - 0.32) / 0.12) * (t >= COLLAPSE_T + 0.32)
        for xv, val, t0 in ((1.0, e1, DOUBLE_T), (2.0, e1 + (e4 - e1) * drop, DOUBLE_T + 0.3)):
            u = float(smooth(lin(t, t0, t0 + 0.45)))
            if u <= 0:
                continue
            bx, _ = plot_xy(xv, 0.0, ys)
            hgt = val * ys * u
            wid = bw * (1 + 0.5 * squash) if xv == 2.0 else bw
            fr.rrect(float(bx) - wid / 2, PY0 - hgt, wid, hgt, 4, fill="ball", fill_alpha=0.85, alpha=ea, glow=0.3)
            label = f"{val:.3f}" if xv == 1.0 or drop < 1 else f"{e4:.3f}"
            hud.tabular(fr, label, float(bx), PY0 - max(hgt, 6) - 14, 24, "ink", ea * u)
            fr.text(f"x = {int(xv)}", float(bx), PY0 + 34, "sans", 22, 600, "muted", ea * u)
        ha = ea * env(t, HALVE_T, CLEAR14, 0.3, 0.4)
        if ha > 0.003:
            bx, _ = plot_xy(2.0, 0.0, ys)
            hh = e1 / 2 * ys
            xs_ = [float(bx) - bw / 2, float(bx) - bw / 2, float(bx) + bw / 2, float(bx) + bw / 2]
            fr.dashed(xs_, [PY0, PY0 - hh, PY0 - hh, PY0], "ink", 1.8, ha * 0.8, on=6, off=5)
            fr.text("half?", float(bx) + bw / 2 + 12, PY0 - hh + 8, "sans", 22, 600, "muted", ha, align="left")
        ca = ea * smooth(lin(t, COLLAPSE_T + 0.35, COLLAPSE_T + 0.7))
        hud.pill(fr, PX0 + 190, PY0 - 230, "÷ 20", "ball", ca, 30)


# ------------------------------------------------------------------ S15: the hidden circle

TG2 = Target(cx=960.0, cy=540.0, unit=85.0)
CIRCLE_T = b(727)  # "the circle"
RINGS_T = b(731)  # "spread out in rings"
BULL_T = b(737)  # "bullseye"
AREA_T = b(743)  # "total area under the curve"
ONE_T = b(753)  # "add up to one"
TRAVEL_T = b(758)  # "quietly travels around those rings"
INT_T = b(765)  # "area under e to the minus x squared"
SQRT_T = b(777)  # "exactly the square root of pi"
HIDE_T = b(784)  # "The circle was hiding"
ALONG_T = b(793)  # "all along"
CLEAR15 = cue(795) - 0.15  # "Put everything together"
AX15 = Axes(cx=960.0, floor=700.0, unit=150.0, hscale=800.0)
AX15C = Axes(cx=560.0, floor=620.0, unit=110.0, hscale=600.0)
SPIN = (TRAVEL_T, TRAVEL_T + 1.4)
SHELLS = (TRAVEL_T + 1.3, TRAVEL_T + 2.6)
TOP = (INT_T - 0.1, INT_T + 1.2)
H3, R3 = 2.55, 1.2  # surface height and world units per sigma: matches AX15 at elevation 0
INTEGRAL = f"integral {tc('e', 'e')}^(-x^2) dif x"
INTEGRAL_EQ = f"integral {tc('e', 'e')}^(-x^2) dif x = sqrt({tc('pi', 'pi')})"
PI_CORNER = (1790.0, 112.0)  # where the cold open's π waited (S03)


def h3(r):
    return H3 * np.exp(-((np.asarray(r) / R3) ** 2) / 2)


def cam15(t):
    e1 = ease_io(lin(t, SPIN[0], SPIN[1] + 0.4))
    e2 = ease_io(lin(t, *TOP))
    elev = lerp(lerp(0.0, 0.5, e1), 1.42, e2)
    azim = 0.35 * e1 * (1 - e2) + 0.1 * (t - SPIN[0]) * (t > SPIN[0]) * (1 - e2)
    dist = lerp(10.0, 15.0, e2)
    center = (lerp(960.0, 1400.0, e2), lerp(600.0, 500.0, e2))
    return orbit((0.0, 0.0, 0.0), dist, elev, azim, focal=1250.0, center=center)


def bullseye(t):
    cam = cam15(t)
    xs, ys, _ = cam.project(np.array([[0.0, H3 * 0.5, 0.0]]))
    return float(xs[0]), float(ys[0])


def draw_darts15(fr, t):
    a = smooth(lin(t, CIRCLE_T, CIRCLE_T + 0.5)) * (1 - smooth(lin(t, AREA_T - 0.2, AREA_T + 0.4)))
    if a <= 0.003:
        return
    TG2.draw_board(fr, a * 0.6)
    TG2.draw_darts(fr, 1e6, 0.0, 60.0, a)
    TG2.draw_rings(fr, a, u=ease_out(lin(t, RINGS_T, RINGS_T + 1.0)))
    g = env(t, BULL_T, AREA_T, 0.15, 0.5)
    if g > 0.003:
        fr.glow_dot(TG2.cx, TG2.cy, 10.0, "light", g * a, strength=1.6)


def draw_area_curve(fr, t):
    """15B: the 1D curve and its gold area, then (15C) the same curve at the left with the integral under it."""
    a = smooth(lin(t, AREA_T - 0.1, AREA_T + 0.4)) * (1 - smooth(lin(t, CLEAR15, CLEAR15 + 0.5)))
    if a <= 0.003:
        return
    away = smooth(lin(t, SPIN[0], SPIN[0] + 0.5))  # hands over to the 3D surface
    back_ = smooth(lin(t, TOP[0], TOP[1]))  # returns at the left for 15C
    ax = AX15C if back_ > 0 else AX15
    ca = a * ((1 - away) if back_ <= 0 else back_)
    if ca <= 0.003:
        return
    bell = Bell(ax, -3.4, 3.4)
    fill = ease_io(lin(t, AREA_T, AREA_T + 1.3)) if back_ <= 0 else 1.0
    ax.floor_line(fr, -3.6, 3.6, ca)
    fr.path_fill(bell.area_path(a=-3.4, b=-3.4 + 6.8 * fill), "bell", ca * 0.22)
    bell.draw(fr, alpha=ca, width=3.4, glow=0.8)
    oa = ca * env(t, ONE_T, SPIN[0] + 0.4, 0.3, 0.3)
    hud.readout(fr, ax.cx, float(ax.y(0.18)), "area", "1", "bell", oa, size=34)


def draw_surface(fr, t):
    a = smooth(lin(t, SPIN[0] - 0.1, SPIN[0] + 0.3)) * (1 - smooth(lin(t, CLEAR15, CLEAR15 + 0.5)))
    if a <= 0.003:
        return
    cam = cam15(t)
    rs = np.linspace(0.0, 3.0 * R3, 60)
    hs = h3(rs)
    # ground rings, faint, for the target underneath
    th = np.linspace(0, 2 * np.pi, 120)
    for rr in (1.0, 2.0, 3.0):
        xs, ys, _ = cam.project(np.c_[rr * R3 * np.cos(th), np.zeros_like(th), rr * R3 * np.sin(th)])
        fr.poly(xs, ys, "line", 1.4, a * 0.7, close=True)
    # the profile sweeps round the axis, leaving gold meridians behind
    spin = ease_io(lin(t, *SPIN))
    top = smooth(lin(t, *TOP))
    psi_max = math.pi * spin
    n_mer = 18
    for k in range(n_mer + 1):
        psi = math.pi * k / n_mer
        if psi > psi_max + 1e-6:
            break
        prof = np.r_[-rs[::-1], rs[1:]]
        ph = np.r_[hs[::-1], hs[1:]]
        xs, ys, _ = cam.project(np.c_[prof * math.cos(psi), ph, prof * math.sin(psi)])
        ma = a * (0.32 + 0.3 * (k == 0)) * (1 - 0.7 * top)
        fr.poly(xs, ys, "bell", 1.6 if k else 2.8, ma, glow=0.3)
    prof = np.r_[-rs[::-1], rs[1:]]
    ph = np.r_[hs[::-1], hs[1:]]
    xs, ys, _ = cam.project(np.c_[prof * math.cos(psi_max), ph, prof * math.sin(psi_max)])
    fr.poly(xs, ys, "bell", 3.2, a * (1 - 0.6 * top), glow=0.8)
    # pink shells light from the centre outward: the r dr rings of the integral
    u = lin(t, *SHELLS)
    radii = np.linspace(0.25, 2.75, 11)
    for j, r in enumerate(radii):
        la = a * clamp(u * (len(radii) + 2) - j)
        if la <= 0.003:
            continue
        hy = float(h3(r * R3))
        xs, ys, _ = cam.project(np.c_[r * R3 * np.cos(th), np.full_like(th, hy), r * R3 * np.sin(th)])
        w = math.exp(-0.25 * r * r) ** 0.5
        fr.poly(xs, ys, "pi", 2.2, la * (0.35 + 0.65 * w), glow=0.6 * w, close=True)


def draw_integral(fr, t):
    a = smooth(lin(t, INT_T, INT_T + 0.3)) * (1 - smooth(lin(t, NORMAL_T + 0.6, FX_T - 0.1)))
    if a <= 0.003:
        return
    glide = ease_io(lin(t, CLEAR15, CLEAR15 + 0.9))  # "Put everything together": the result takes centre stage
    cx, cy, size = lerp(600.0, 960.0, glide), lerp(790.0, 520.0, glide), lerp(70.0, 84.0, glide)
    if t < SQRT_T:
        typmath.draw(fr, INTEGRAL, cx, cy, size, alpha=a, reveal=lin(t, INT_T, INT_T + 1.4))
        return
    typmath.morph(fr, INTEGRAL, INTEGRAL_EQ, lin(t, SQRT_T, SQRT_T + 0.8), cx, cy, size, alpha=a)
    if t >= SQRT_T + 0.8:  # sqrt(pi) lands: a pink flash and its value
        kick = math.exp(-(t - SQRT_T - 0.8) / 0.4)
        px, py = typmath.glyph_centers(INTEGRAL_EQ, cx, cy, size)[10]
        fr.glow_dot(px, py, 16.0, "pi", a * 0.6 * kick, strength=1.2)
        typmath.draw(fr, "approx 1.7725", cx + 110, cy + 90, 40, color="muted",
                     alpha=a * smooth(lin(t, SQRT_T + 0.9, SQRT_T + 1.3)) * (1 - glide))


def draw_pi(fr, t):
    """The pink π from the cold open flies back and settles in the bullseye."""
    a = smooth(lin(t, HIDE_T - 0.1, HIDE_T + 0.15)) * (1 - smooth(lin(t, CLEAR15, CLEAR15 + 0.5)))
    if a <= 0.003:
        return
    u = ease_io(lin(t, HIDE_T, HIDE_T + 0.95))
    bx, by = bullseye(t)
    x = lerp(PI_CORNER[0], bx, u)
    y = lerp(PI_CORNER[1], by, u) - 90 * math.sin(math.pi * u)
    size = lerp(54.0, 92.0, u)
    land = math.exp(-max(0.0, t - HIDE_T - 0.95) / 0.35) * (u >= 1)
    if u >= 1:
        fr.circle(bx, by, 40 + 50 * (1 - land), "pi", 2.0, a * land * 0.8)
    typmath.draw(fr, tc("pi", "pi"), x, y, size, alpha=a, glow=0.5 + 1.2 * land)


def draw_sweep15(fr, t):
    u = lin(t, ALONG_T, ALONG_T + 0.9)
    if u <= 0 or u >= 1 or t > CLEAR15:
        return
    cam = cam15(t)
    th = np.linspace(0, 2 * np.pi, 120)
    path = skia.Path()
    for r in np.linspace(0.25, 2.75, 11):
        hy = float(h3(r * R3))
        xs, ys, _ = cam.project(np.c_[r * R3 * np.cos(th), np.full_like(th, hy), r * R3 * np.sin(th)])
        ring = skia.Path()
        skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=6.0).getFillPath(poly_path(xs, ys, True), ring)
        path.addPath(ring)
    fr.light_sweep(path, u, strength=0.9)


# ------------------------------------------------------------------ S16: the full formula and its two dials

FORMULA = (f"f(x) = 1/({tc('sigma', 'sigma')} sqrt(2 {tc('pi', 'pi')})) "
           f"{tc('e', 'e')}^(-(x - {tc('bell', 'mu')})^2 / (2 {tc('sigma', 'sigma')}^2))")
# glyph groups (see typmath.glyphs(FORMULA)): f ( x ) = | 1 σ √ ‾ 2 π — | e | − ( x − μ ) 2 — | 2 σ 2
G_FX = (0, 1, 2, 3, 4)
G_COEF = {5: b(808), 11: b(810), 6: b(810), 7: b(813), 8: b(813), 9: b(816), 10: b(817)}
G_E = 12
G_NUM = {13: b(824), 14: b(825), 15: b(825), 16: b(826), 17: b(827), 18: b(828), 19: b(828), 23: b(828)}
G_DEN = {20: b(830), 21: b(831), 22: b(832)}
SQRT_PI = (7, 8, 9, 10)
CORE = (12, 13, 15, 19)
MU_IDX, SIGMA_IDX = 17, 6
NORMAL_T = b(802)  # "normal distribution"
FX_T = b(804)
E16_T = b(819)
CORE_T = b(832) + 0.45
SHRINK_T = b(833)  # "looks frightening"
DIALS_T = b(840)  # "two dials"
MU_T = b(842)  # "Mu slides the bell"
LEFT_T, RIGHT_T = b(846), b(848)
AVG_T = b(852)  # "average"
SIGMA_T = b(853)  # "Sigma stretches the bell wider"
NARROW_T = b(859)  # "squeezes it narrower"
SD_T = b(865)  # "standard deviation"
TYPICAL_T = b(868)  # "typical distance from the average"
AREA16_T = b(873)  # "keeps the total area equal to one"
F_BIG, F_SMALL = ((960.0, 430.0), 88.0), ((960.0, 175.0), 56.0)
AX16 = Axes(cx=960.0, floor=720.0, unit=150.0, hscale=650.0)
BELL16 = Bell(AX16, -3.6, 3.6)
DIAL_C, DIAL_GAP = (960.0, 880.0), 340.0


def glyph_alpha(i, t):
    if i in G_FX:
        return smooth(lin(t, FX_T, FX_T + 0.3))
    for group in (G_COEF, G_NUM, G_DEN):
        if i in group:
            return smooth(lin(t, group[i], group[i] + 0.3))
    if i == G_E:
        return smooth(lin(t, E16_T, E16_T + 0.3))
    return 1.0


def formula_place(t):
    u = ease_io(lin(t, SHRINK_T, SHRINK_T + 0.8))
    (x0, y0), s0 = F_BIG
    (x1, y1), s1 = F_SMALL
    return lerp(x0, x1, u), lerp(y0, y1, u), lerp(s0, s1, u)


def mu_sigma(t):
    """The two dials, driven by the narration."""
    mu = 0.0
    mu += -1.2 * ease_io(lin(t, LEFT_T - 0.3, LEFT_T + 0.3))
    mu += 2.4 * ease_io(lin(t, RIGHT_T - 0.1, RIGHT_T + 0.5))
    mu += -1.2 * ease_io(lin(t, RIGHT_T + 0.7, RIGHT_T + 1.4))
    sigma = 1.0
    sigma += 0.6 * ease_io(lin(t, SIGMA_T + 0.2, SIGMA_T + 1.2))
    sigma += -1.0 * ease_io(lin(t, NARROW_T, NARROW_T + 0.8))
    sigma += 0.4 * ease_io(lin(t, NARROW_T + 1.1, NARROW_T + 1.8))
    w = lin(t, AREA16_T + 0.5, AREA16_T + 2.6)
    sigma *= 1 + 0.35 * math.sin(2 * math.pi * w) * (1 - w) * (w > 0)
    return mu, sigma


def draw_formula16(fr, t):
    pa = env(t, NORMAL_T, SHRINK_T + 0.4, 0.4, 0.4)
    hud.pill(fr, 960, 200, "normal distribution", "bell", pa, 30)
    a = smooth(lin(t, FX_T - 0.2, FX_T + 0.2))
    if t < FX_T - 0.2 or a <= 0.003:
        return
    gs, _ = typmath.glyphs(FORMULA)
    alphas = {i: glyph_alpha(i, t) for i in range(len(gs))}
    flown = smooth(lin(t, DIALS_T, DIALS_T + 0.25))
    alphas[MU_IDX] *= 1 - 0.6 * flown
    alphas[SIGMA_IDX] *= 1 - 0.6 * flown
    glows = {}
    circle = env(t, b(817) + 0.15, b(817) + 1.2, 0.2, 0.5)
    for i in SQRT_PI:
        glows[i] = 1.2 * circle
    core = env(t, CORE_T, SHRINK_T + 0.3, 0.2, 0.4)
    coef = env(t, AREA16_T, END, 0.4, 0.3)
    for i in G_COEF:
        glows[i] = max(glows.get(i, 0.0), 1.2 * coef)
    x, y, size = formula_place(t)
    typmath.draw(fr, FORMULA, x, y, size, alpha=a, alphas=alphas, glows=glows)
    if core > 0.003:  # the darts' answer, outlined in lime
        cs = typmath.glyph_centers(FORMULA, x, y, size)
        xs = [cs[i][0] for i in CORE]
        ys = [cs[i][1] for i in CORE]
        pad = size * 0.35
        fr.rrect(min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad, 14,
                 stroke="e", width=2.4, alpha=a * core, glow=0.8)


def knob_symbol_xy(i):
    return DIAL_C[0] + (-1 if i == 0 else 1) * DIAL_GAP / 2, DIAL_C[1] + 46 + 46


def draw_dials16(fr, t):
    """μ and σ fly out of the formula into the dials; the dials drive a live bell."""
    if t < DIALS_T:
        return
    u = ease_io(lin(t, DIALS_T, DIALS_T + 0.75))
    x, y, size = formula_place(t)
    cs = typmath.glyph_centers(FORMULA, x, y, size)
    if u < 1:
        for k, (idx, expr) in enumerate(((MU_IDX, tc("bell", "mu")), (SIGMA_IDX, tc("sigma", "sigma")))):
            sx, sy = cs[idx]
            tx, ty = knob_symbol_xy(k)
            px, py = lerp(sx, tx, u), lerp(sy, ty, u) - 80 * math.sin(math.pi * u)
            typmath.draw(fr, expr, px, py, lerp(size * 0.75, 40.0, u), alpha=1.0, glow=0.6)
    a = smooth(lin(t, DIALS_T + 0.55, DIALS_T + 0.85))
    if a <= 0.003:
        return
    mu, sigma = mu_sigma(t)
    am = env(t, MU_T, AVG_T + 0.6, 0.3, 0.4)
    asg = env(t, SIGMA_T, END, 0.3, 0.2)
    dial_pair(fr, *DIAL_C, mu, sigma, a, gap=DIAL_GAP, mu_range=2.0, sigma_range=(0.5, 2.0), active_mu=am,
              active_sigma=asg)
    # the live bell
    AX16.floor_line(fr, -3.8, 3.8, a)
    BELL16.draw(fr, mu, sigma, alpha=a, width=3.6, glow=0.8, fill=0.10)
    # μ = average
    ca = a * smooth(lin(t, AVG_T, AVG_T + 0.4))
    if ca > 0.003:
        BELL16.mean_line(fr, mu, sigma, alpha=ca, u=ease_out(lin(t, AVG_T, AVG_T + 0.5)))
        top = float(AX16.y(pdf(mu, mu, sigma)))
        typmath.draw(fr, f'{tc("bell", "mu")} = "average"', float(AX16.x(mu)) + 150, top - 30, 36,
                     alpha=ca * (1 - smooth(lin(t, SIGMA_T + 0.3, SIGMA_T + 0.8))))
    # ±σ and the typical distance
    sa = a * env(t, SD_T, END, 0.4, 0.2)
    if sa > 0.003:
        BELL16.band(fr, 1.0, mu, sigma, alpha=sa, fill=0.22, u=ease_out(lin(t, SD_T, SD_T + 0.6)))
        typmath.draw(fr, f'"±" {tc("sigma", "sigma")}', float(AX16.x(mu)), AX16.floor + 40, 36,
                     alpha=sa * (1 - smooth(lin(t, TYPICAL_T, TYPICAL_T + 0.4))))
    ta = a * env(t, TYPICAL_T, END, 0.3, 0.2)
    if ta > 0.003:
        u2 = ease_out(lin(t, TYPICAL_T, TYPICAL_T + 0.7))
        y = float(AX16.y(pdf(mu + sigma, mu, sigma))) - 40
        x0 = float(AX16.x(mu))
        x1 = x0 + sigma * AX16.unit * u2
        fr.line(x0, y, x1, y, "bg", 9.0, ta * 0.8)
        hud.arrow(fr, x0, y, x1, y, "sigma", 3.2, ta, glow=0.8, head=15.0)
        typmath.draw(fr, tc("sigma", "sigma"), (x0 + x1) / 2, y - 30, 36, alpha=ta * u2)
    # the total area never changes
    ra = a * env(t, AREA16_T, END, 0.4, 0.2)
    if ra > 0.003:
        hud.readout(fr, 1560, 600, "area", "1.000", "bell", ra, size=34)  # exact for every μ and σ


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_prev_bell(fr, t)
    if t < CLEAR14 + 0.6:
        draw_target(fr, t)
        draw_cards(fr, t)
        draw_lifted(fr, t)
        draw_expr(fr, t)
        draw_insets(fr, t)
        draw_panel(fr, t)
    if CLEAR14 - 0.1 <= t < CLEAR15 + 0.6:
        draw_darts15(fr, t)
        draw_area_curve(fr, t)
        draw_surface(fr, t)
        draw_pi(fr, t)
        draw_sweep15(fr, t)
        fr.chroma(chroma_kick(t, SQRT_T + 0.8, 6.0))
    if CLEAR14 - 0.1 <= t < FX_T:
        draw_integral(fr, t)
    if t >= CLEAR15:
        draw_formula16(fr, t)
        draw_dials16(fr, t)
    hud.eyebrow(fr, t, "03 · WHERE e AND π COME FROM", 190.7)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch3:{Path(__file__).stat().st_mtime_ns}"
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
STILLS = [191.0, 193.0, 197.0, 199.8, 201.5, 203.6, 205.0, 206.9, 209.9, 211.0, 213.8, 216.4, 219.6, 222.0, 225.0,
          227.0, 229.4, 230.8, 232.4, 235.5, 237.6, 240.0, 241.5, 242.6, 243.8, 245.8, 247.6, 249.0, 251.2, 253.4,
          254.6, 255.5, 256.6, 257.9, 259.0, 260.6, 262.6, 263.5, 265.0, 266.6, 269.0, 271.0, 273.2, 275.0, 277.8,
          279.5, 281.3, 282.7, 283.2, 284.6, 286.0, 287.4, 289.0, 290.6, 293.0, 295.0]
