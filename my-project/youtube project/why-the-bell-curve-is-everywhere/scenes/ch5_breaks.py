"""CHAPTER 5 - WHERE THE BELL BREAKS (S19-S21), 05:36.780 (#986 "But") - 06:27.180 (#1127 "Let's").

S19  Adding vs multiplying  "almost impossible" cracks on "warning" (a red breath at the edges) -> a height ruler: 175 cm,
                            the tallest recorded 272 cm, a ghost at twice the average, 78 cm short -> the 175 cm column
                            stacks from + blocks -> two lanes: height adds a block a step, wealth multiplies by 1.5 a step
                            and shoots past the top of the frame.
S20  The long tail          10,000 multiplicative walks pour into a histogram, the fitted gold bell cracks, the right side
                            crawls into a red tail, the camera pans along it past isolated extremes -> heights spread like
                            wealth: one person grows and the camera cranes up past clouds, the atmosphere and the space
                            station (> 1,000 km) -> four long-tail cards: cities, earthquakes, market crashes, viral videos.
S21  Added or multiplied?   the bell's 5σ tail beside the wealth tail on the same σ axis: 0 vs 43 samples beyond 5σ, the top
                            1% share -> one bell, "?", a gold + over a mini bell, a red × over a mini long tail.

All wealth numbers come from one seeded simulation (a multiplicative random walk with a small floor, median scaled to 1).
"""

from __future__ import annotations

import contextlib
import math
from pathlib import Path

import numpy as np
import skia
import typmath
from components import crowd, hud
from components.bell import Bell
from components.histogram import Axes, Bars, draw_bars, stagger
from cues import AUDIO, beat, cue
from fx import Frame, chroma_kick, col, ease_in, ease_io, ease_out, env, lin, smooth, text_path
from scipy.special import ndtr
from scipy.stats import gaussian_kde
from theme import THEME, H, W
from typmath import tc

from scenes import ch4_ruler as ch4

START = cue(986)  # 336.78 "But that last sentence is also a warning."
END = cue(1127)  # 387.18 "Let's ..."

b = beat


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


@contextlib.contextmanager
def view(fr, m):
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
def clipped(fr, path):
    fr.c.save()
    fr.g.save()
    fr.c.clipPath(path, skia.ClipOp.kIntersect, True)
    fr.g.clipPath(path, skia.ClipOp.kIntersect, True)
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


def clamp01(x):
    return max(0.0, min(1.0, x))


def poly_path(xs, ys, close=False):
    p = skia.Path()
    p.moveTo(float(xs[0]), float(ys[0]))
    for x, y in zip(xs[1:], ys[1:]):
        p.lineTo(float(x), float(y))
    if close:
        p.close()
    return p


def red_breath(fr, a):
    """A faint red vignette that breathes once at the frame edges."""
    if a <= 0.003:
        return
    shader = skia.GradientShader.MakeRadial(
        skia.Point(W / 2, H / 2), W * 0.7, [col("tail", 0.0), col("tail", 0.0), col("tail", 0.32 * a)], [0.0, 0.6, 1.0]
    )
    fr.c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=shader))


# ------------------------------------------------------------------ the wealth simulation (one seed for the chapter)

N_SIM = 10_000


def simulate(n=N_SIM, steps=120, vol=0.30, drift=-0.02, floor=0.05, seed=57):
    """Each fortune is multiplied by a random return every step; a small floor keeps it positive."""
    rng = np.random.default_rng(seed)
    w = np.ones(n)
    for _ in range(steps):
        w = w * np.exp(rng.normal(-(vol**2) / 2 + drift, vol, n)) + floor
    return w / np.median(w)


WEALTH = simulate()
W_MEAN, W_SD = float(WEALTH.mean()), float(WEALTH.std())
W_Z = (WEALTH - W_MEAN) / W_SD
TOP1 = float(np.sort(WEALTH)[-N_SIM // 100 :].sum() / WEALTH.sum())  # share held by the top 1 %
BEYOND5_W = int((W_Z > 5).sum())
ZMAX_W = float(W_Z.max())
NORMAL = np.random.default_rng(58).normal(0.0, 1.0, N_SIM)
BEYOND5_N = int((NORMAL > 5).sum())
P5 = float(ndtr(-5.0))  # one-sided tail of the bell beyond 5σ
Q25, Q75 = np.quantile(WEALTH, [0.25, 0.75])
FIT_MU, FIT_SIGMA = 1.0, float((Q75 - Q25) / 1.349)  # the bell that fits the middle of the pile
_KDE = gaussian_kde(np.log(WEALTH), bw_method=0.08)


def wealth_pdf(w):
    """Smooth density of the simulated wealth (a KDE in log space, mapped back)."""
    w = np.maximum(np.asarray(w, float), 1e-3)
    return _KDE(np.log(w)) / w


# ------------------------------------------------------------------ timing

WARN_T = b(993)  # "warning"
TALL_T = b(995)  # "tallest person ever recorded"
TWICE_T = b(1000)  # "not even twice"
CALM_T = b(1006)  # "Heights stay calm"
ADD_T = b(1012)  # "built by adding"
WEALTH_T = b(1018)  # "wealth"
MULT_T = b(1022)  # "multiplying"
RET_T = b(1024)  # "A fortune earns returns"
MULT2_T = b(1035)  # "multiply instead of add"
BREAK_T = b(1041)  # "breaks"
LONG_T = b(1045)  # "long tail stretching far to the right"
IF_T = b(1052)  # "If human height were spread out like wealth"
GROW_T = b(1061)  # "the tallest person would stand"
CRANE_T = b(1065)  # "thousands of kilometers high"
ORBIT_T = b(1072)  # "orbit of the space station"
SAME_T = b(1077)  # "The same long tails appear"
CARD_T = (b(1086), b(1087), b(1088), b(1092))  # cities, earthquakes, stock market crashes, viral videos
WORLDS_T = b(1094)  # "In these worlds"
NOT_T = b(1101)  # "not almost impossible"
MOST_T = b(1109)  # "matters most"
TRUST_T = b(1114)  # "trust a bell"
ASK_T = b(1118)  # "one question"
ARE_T = b(1120)  # "Are the pieces"
PLUS_T = b(1124)  # "added"
TIMES_T = b(1126)  # "multiplied?"

# ------------------------------------------------------------------ S19A: "almost impossible" cracks

LABEL_Y = 440.0


def draw_ch4_tail(fr, t):
    a = 1 - smooth(lin(t, WARN_T + 0.2, WARN_T + 0.8))
    if a <= 0.003:
        return
    t1 = ch4.END - 1e-3
    with faded(fr, a):
        ax, _ = ch4.bell_at(t1)
        ch4.draw_bell(fr, t1)
        ch4.draw_ruler(fr, t1, ax)


def crack_line(xc, y0, y1, n=9, seed=4):
    rng = np.random.default_rng(seed)
    ys = np.linspace(y0, y1, n)
    xs = xc + np.cumsum(rng.uniform(-1, 1, n)) * 7.0
    return xs, ys


def draw_warning_label(fr, t):
    a = smooth(lin(t, START, START + 0.35)) * (1 - smooth(lin(t, WARN_T + 0.45, WARN_T + 0.95)))
    if a <= 0.003:
        return
    path = text_path("almost impossible", 960, LABEL_Y, "display", 56, 600)
    u = ease_out(lin(t, WARN_T, WARN_T + 0.9))
    if u <= 0:
        fr.path_fill(path, "ink", a * 0.85)
        return
    xs, ys = crack_line(985, LABEL_Y - 60, LABEL_Y + 20)
    left = poly_path(np.r_[0, xs, 0], np.r_[ys[0], ys, ys[-1]], close=True)
    right = poly_path(np.r_[W, xs, W], np.r_[ys[0], ys, ys[-1]], close=True)
    for piece, dx, dy, rot in ((left, -10, 26, -3.0), (right, 16, 60, 5.0)):
        m = skia.Matrix()
        m.setRotate(rot * u, 985, LABEL_Y)
        m.postTranslate(dx * u, dy * u * u)
        with view(fr, m), clipped(fr, piece):
            fr.path_fill(path, "ink", a * 0.85)
    fr.poly(xs, ys, "tail", 2.0, a * clamp01(3 * u) * (1 - u), glow=1.2)


# ------------------------------------------------------------------ S19B: heights are built by adding

FLOOR19 = 900.0
PX_CM = 2.0
RULER_X = 300.0
AVG_X, TALL_X, GHOST_X = 600.0, 860.0, 1120.0
AVG_CM, TALL_CM = 175.0, 272.0  # 272 cm: the tallest height ever recorded
BLOCK_CM = AVG_CM / 14


def y_cm(c):
    return FLOOR19 - c * PX_CM


def heights_alpha(t):
    return env(t, TALL_T - 0.05, WEALTH_T + 0.4, 0.4, 0.45)


def draw_heights(fr, t):
    a = heights_alpha(t)
    if a <= 0.003:
        return
    # the ruler
    fr.line(RULER_X, FLOOR19, RULER_X, y_cm(380), "muted", 1.8, a * 0.8)
    fr.line(RULER_X - 20, FLOOR19, GHOST_X + 140, FLOOR19, "line", 1.6, a)
    for c in range(0, 381, 25):
        major = c % 100 == 0
        fr.line(RULER_X - (14 if major else 7), y_cm(c), RULER_X, y_cm(c), "muted", 1.4, a * (0.9 if major else 0.5))
        if major and c:
            typmath.number(fr, str(c), RULER_X - 52, y_cm(c), 24, "muted", a)
    fr.text("cm", RULER_X - 52, y_cm(380) - 4, "sans", 20, 600, "muted", a)
    calm = smooth(lin(t, ADD_T - 0.3, ADD_T + 0.2))
    # average and tallest
    crowd.person(fr, AVG_X, FLOOR19, AVG_CM * PX_CM, a, fill=0.08, width=2.0)
    fr.text("175 cm", AVG_X, y_cm(AVG_CM) - 26, "display", 30, 600, "bell", a, glow=0.3)
    ta = a * smooth(lin(t, TALL_T + 0.2, TALL_T + 0.7)) * (1 - 0.6 * calm)
    if ta > 0.003:
        rise = ease_out(lin(t, TALL_T + 0.2, TALL_T + 1.0))
        crowd.person(fr, TALL_X, FLOOR19, TALL_CM * PX_CM * (0.9 + 0.1 * rise), ta, fill=0.08, width=2.0)
        fr.dashed([RULER_X, GHOST_X + 150], [y_cm(TALL_CM)] * 2, "muted", 1.4, ta * 0.6, on=8, off=7)
        fr.text("tallest recorded · 272 cm", TALL_X, y_cm(TALL_CM) - 26, "sans", 26, 600, "ink", ta)
    # twice the average: a ghost that nobody reaches
    ga = a * smooth(lin(t, TWICE_T, TWICE_T + 0.5)) * (1 - 0.6 * calm)
    if ga > 0.003:
        crowd.person(fr, GHOST_X, FLOOR19, 2 * AVG_CM * PX_CM, ga * 0.4, width=1.6)
        fr.dashed([RULER_X, GHOST_X + 150], [y_cm(2 * AVG_CM)] * 2, "muted", 1.4, ga * 0.7, on=8, off=7)
        fr.text("twice average · 350 cm", GHOST_X, y_cm(2 * AVG_CM) - 22, "sans", 24, 600, "muted", ga)
        short = 2 * AVG_CM - TALL_CM
        gx = GHOST_X + 140
        u = ease_out(lin(t, TWICE_T + 0.4, TWICE_T + 1.0))
        if u > 0:
            hud.arrow(
                fr,
                gx,
                y_cm(TALL_CM) - 4,
                gx,
                y_cm(TALL_CM) - 4 - (short * PX_CM - 8) * u,
                "muted",
                2.0,
                ga,
                glow=0.0,
                head=12.0,
            )
            fr.text(
                f"{short:.0f} cm short",
                gx + 16,
                y_cm(TALL_CM + short / 2) + 8,
                "sans",
                22,
                600,
                "muted",
                ga * u,
                align="left",
            )
    # the 175 cm column, stacked from + blocks
    draw_plus_column(fr, AVG_X + 110, AVG_CM / BLOCK_CM, t, ADD_T, 0.8, a)


def plus_block(fr, x, y, w, h, alpha, color="bell"):
    fr.rrect(x - w / 2, y - h, w, h, 4, fill=color, stroke=color, width=1.4, alpha=alpha, fill_alpha=0.16)
    s = min(w, h) * 0.22
    cy = y - h / 2
    fr.line(x - s, cy, x + s, cy, color, 2.0, alpha)
    fr.line(x, cy - s, x, cy + s, color, 2.0, alpha)


def draw_plus_column(fr, x, n_blocks, t, t0, dur, alpha, floor=FLOOR19, w=56.0, blk=BLOCK_CM * PX_CM):
    """``n_blocks`` gold + blocks dropping in bottom-up from ``t0`` over ``dur`` s."""
    n = round(n_blocks)
    for k in range(n):
        u = clamp01((t - t0 - dur * k / max(1, n)) / 0.18)
        if u <= 0:
            break
        y = floor - k * blk - 14 * (1 - ease_out(u))
        plus_block(fr, x, y - 1, w, blk - 2, alpha * smooth(u))


# ------------------------------------------------------------------ S19C: two lanes, + and ×

LANE_H, LANE_W = 700.0, 1220.0
LANE_BLK = 26.0
FACTOR = 1.5
STEPS = np.array([0.0, 0.62, 1.12, 1.58, 1.98, 2.34, 2.66, 2.94, 3.2, 3.43, 3.64]) + RET_T + 0.05


def lanes_alpha(t):
    return env(t, WEALTH_T + 0.1, MULT2_T + 0.4, 0.45, 0.4)


def draw_lanes(fr, t):
    a = lanes_alpha(t)
    if a <= 0.003:
        return
    fr.line(LANE_H - 200, FLOOR19, LANE_W + 200, FLOOR19, "line", 1.6, a)
    k = int(np.searchsorted(STEPS, t, side="right"))  # completed steps
    # height lane: + one block per step
    for j in range(1 + k):
        t0 = WEALTH_T + 0.3 if j == 0 else STEPS[j - 1]
        u = clamp01((t - t0) / 0.2)
        y = FLOOR19 - j * LANE_BLK - 12 * (1 - ease_out(u))
        plus_block(fr, LANE_H, y - 1, 70, LANE_BLK - 2, a * smooth(u))
    # wealth lane: × 1.5 per step, every segment longer than the last
    flip = smooth(lin(t, MULT_T, MULT_T + 0.3))
    u0 = clamp01((t - WEALTH_T - 0.3) / 0.2)
    if flip < 1:
        plus_block(fr, LANE_W, FLOOR19 - 1 - 12 * (1 - ease_out(u0)), 70, LANE_BLK - 2, a * smooth(u0) * (1 - flip))
    top = FLOOR19 - LANE_BLK
    if flip > 0:
        fr.rrect(
            LANE_W - 35,
            top,
            70,
            LANE_BLK - 2,
            4,
            fill="tail",
            stroke="tail",
            width=1.4,
            alpha=a * flip,
            fill_alpha=0.22,
        )
    h = LANE_BLK
    for j in range(len(STEPS)):
        if t < STEPS[j]:
            break
        u = ease_out(clamp01((t - STEPS[j]) / 0.28))
        seg = h * (FACTOR - 1) * u
        y1 = FLOOR19 - h
        if y1 > -40:
            fr.rrect(
                LANE_W - 35,
                y1 - seg,
                70,
                max(1.0, seg - 2),
                4,
                fill="tail",
                stroke="tail",
                width=1.4,
                alpha=a,
                fill_alpha=0.22 + 0.25 * math.exp(-(t - STEPS[j]) / 0.3),
                glow=0.3,
            )
            if seg > 34:
                fr.text("×1.5", LANE_W + 50, y1 - seg / 2 + 8, "sans", 20, 600, "muted", a * u, align="left")
        h *= FACTOR if u >= 1 else 1 + (FACTOR - 1) * u
    # lane labels and their operators
    for x, name in ((LANE_H, "height"), (LANE_W, "wealth")):
        fr.text(name, x, FLOOR19 + 46, "display", 32, 600, "ink", a)
    badge(fr, LANE_H, FLOOR19 + 104, "+", "bell", a)
    badge(fr, LANE_W, FLOOR19 + 104, "+", "bell", a * (1 - flip))
    badge(fr, LANE_W, FLOOR19 + 104, "×", "tail", a * flip, pop=math.exp(-max(0.0, t - MULT_T) / 0.25) * (flip > 0))


def badge(fr, x, y, sym, color, alpha, r=30.0, pop=0.0, glow=0.4):
    if alpha <= 0.003:
        return
    rr = r * (1 + 0.25 * pop)
    hud.glass_card(fr, x - rr, y - rr, 2 * rr, 2 * rr, alpha, r=int(rr), glow=glow + pop, glow_color=color)
    fr.circle(x, y, rr, color, 2.0, alpha, glow=0.4)
    fr.text(sym, x, y + rr * 0.42, "display", rr * 1.25, 600, color, alpha)


# ------------------------------------------------------------------ S20A: the pour, the crack, the tail

AX20 = Axes(cx=260.0, floor=760.0, unit=110.0, hscale=560.0)
EDGES20 = np.arange(0.0, 8.0001, 0.25)
_c, _ = np.histogram(WEALTH, EDGES20)
BARS20 = Bars((EDGES20[:-1] + EDGES20[1:]) / 2, np.diff(EDGES20), _c / N_SIM / np.diff(EDGES20))
FAR = WEALTH[WEALTH > 8.0]
FAR_XY = crowd.dot_layout(FAR, AX20.x, 1.0, 4.0, AX20.floor, origin=8.0, cols=3)
BELL20 = Bell(AX20, FIT_MU - 3.3 * FIT_SIGMA, FIT_MU + 3.3 * FIT_SIGMA)
CRACK_AT = FIT_MU + 0.8 * FIT_SIGMA
PAN = 1650.0


def crawl(t):
    """How far right (wealth units) the red has spread."""
    return lerp(2.4, 8.0, ease_in(lin(t, BREAK_T + 0.2, LONG_T))) + lerp(
        0.0, 16.0, ease_io(lin(t, LONG_T, LONG_T + 2.2))
    )


def draw_pour(fr, t):
    a = env(t, MULT2_T - 0.2, IF_T + 0.5, 0.35, 0.5)
    if a <= 0.003:
        return
    pan = PAN * ease_io(lin(t, LONG_T, LONG_T + 2.2))
    with view(fr, translate(-pan, 0.0)):
        AX20.floor_line(fr, -0.3, 26.0, a)
        grow = stagger(t, MULT2_T, len(BARS20.z), spread=0.9, dur=0.5)
        c = crawl(t)
        red = (BARS20.z >= 2.4) & (BARS20.z < c)
        blue = ~red
        draw_bars(fr, AX20, Bars(BARS20.z[blue], BARS20.w[blue], BARS20.d[blue]), a, grow[blue])
        if red.any():
            draw_bars(fr, AX20, Bars(BARS20.z[red], BARS20.w[red], BARS20.d[red]), a, grow[red], color="tail", glow=0.4)
        for z in range(0, 25, 2):
            x = float(AX20.x(z))
            fr.line(x, AX20.floor + 4, x, AX20.floor + 12, "muted", 1.4, a * 0.7)
            typmath.number(fr, str(z), x, AX20.floor + 34, 22, "muted", a * 0.7)
        # the isolated extremes
        far = FAR <= c
        if far.any():
            crowd.draw_dots(fr, FAR_XY[far], 4.0, "tail", a, glow=0.5)
        # the red tail over the data
        if c > 2.4:
            ws = np.linspace(2.4, c, 300)
            fr.poly(AX20.x(ws), AX20.y(wealth_pdf(ws)), "tail", 3.2, a, glow=0.9)
            fr.glow_dot(float(AX20.x(c)), float(AX20.y(wealth_pdf([c])[0])), 4.0, "tail", a, strength=1.2)
        # the bell that fit the middle, then broke
        if t < BREAK_T:
            BELL20.snap(fr, t, MULT2_T + 0.9, mu=FIT_MU, sigma=FIT_SIGMA, alpha=a, width=3.2)
        else:
            u = lin(t, BREAK_T, BREAK_T + 0.45)
            BELL20.crack(
                fr, u, at=CRACK_AT, mu=FIT_MU, sigma=FIT_SIGMA, alpha=a * (1 - 0.5 * smooth(u)), width=3.2, gap=12
            )
    fr.text(
        "wealth",
        float(AX20.x(8.0)) + 40,
        AX20.floor + 80,
        "sans",
        24,
        600,
        "muted",
        a * (1 - smooth(lin(t, LONG_T, LONG_T + 0.5))),
        align="right",
    )
    fr.chroma(chroma_kick(t, BREAK_T, 7.0))
    red_breath(fr, pulse_once(t, BREAK_T, 0.9))
    if t > LONG_T + 0.6:  # where the walk ends up
        ra = a * smooth(lin(t, LONG_T + 0.6, LONG_T + 1.0))
        hud.readout(fr, 1500, 230, "richest", f"{WEALTH.max():,.0f}× median", "tail", ra, 30)


def pulse_once(t, at, dur):
    u = lin(t, at, at + dur)
    return math.sin(math.pi * u) if 0 < u < 1 else 0.0


# ------------------------------------------------------------------ S20B: heights spread like wealth

ROW_N = 11
ROW_MID = ROW_N // 2
ROW_PX_CM = 1.2
_q = np.quantile(WEALTH, np.linspace(0.1, 0.72, ROW_N - 1))
ROW_CM = np.insert(np.random.default_rng(59).permutation(170.0 * _q), ROW_MID, 170.0)
ROW_X = 960.0 + (np.arange(ROW_N) - ROW_MID) * 132.0
HEAD_Y = 260.0
GIANT_PX = FLOOR19 - HEAD_Y  # the giant's height when the crane starts
CRANE_END = SAME_T + 0.3
L_KEYS = np.array(
    [
        [CRANE_T, -2.25],
        [CRANE_T + 0.8, 0.0],
        [CRANE_T + 2.0, 1.55],
        [ORBIT_T + 0.3, 2.62],
        [ORBIT_T + 1.3, 3.1],
        [CRANE_END, 3.3],
    ]
)
K_DEC = 300.0  # screen px per decade of altitude


def log_alt(t):
    """log10 of the giant's height in km."""
    return float(np.interp(t, L_KEYS[:, 0], L_KEYS[:, 1]))


def y_alt(t, log_km):
    return HEAD_Y + (log_alt(t) - log_km) * K_DEC


def crowd_alpha(t):
    return env(t, IF_T - 0.1, SAME_T + 0.5, 0.45, 0.5)


def ground_drop(t):
    return 1500.0 * ease_in(lin(t, CRANE_T, CRANE_T + 1.1))


def draw_giant(fr, x, head_top, floor, s, alpha):
    """A silhouette of body scale ``s`` (px) from ``head_top`` down to the hip, its legs stretched to ``floor``."""
    hip = head_top + 0.52 * s
    body = crowd.person_path(x, hip + 0.48 * s, s)
    cut = skia.Path()
    cut.addRect(skia.Rect.MakeLTRB(x - s, hip - 2 * s, x + s, hip + 1))
    with clipped(fr, cut):
        fr.path_fill(body, "ink", alpha * 0.08)
        fr.path_stroke(body, "ink", 2.0, alpha, glow=0.3)
    for side in (-1, 1):
        xo, xi = x + side * 0.085 * s, x + side * 0.0
        leg = poly_path(
            [xo, x + side * 0.07 * s, x + side * 0.02 * s, xi], [hip, floor, floor, hip + 0.06 * s], close=False
        )
        fr.path_stroke(leg, "ink", 2.0, alpha, glow=0.3)
        fill = poly_path(
            [xo, x + side * 0.07 * s, x + side * 0.02 * s, xi, xi],
            [hip, floor, floor, hip + 0.06 * s, hip],
            close=True,
        )
        fr.path_fill(fill, "ink", alpha * 0.08)


def draw_crane(fr, t):
    a = crowd_alpha(t)
    if a <= 0.003:
        return
    drop = ground_drop(t)
    floor = FLOOR19 + drop
    rise = ease_out(lin(t, IF_T, IF_T + 0.7))
    hud.pill(fr, 960, 150, "height, spread like wealth", "muted", a * env(t, IF_T, CRANE_T + 0.3, 0.4, 0.4), 24)
    # the sky: clouds, the thin blue line, the station's orbit, stars
    sky = smooth(lin(t, CRANE_T, CRANE_T + 0.4))
    if sky > 0.003:
        draw_sky(fr, t, a * sky)
    # the row (median 170 cm)
    fr.line(0, floor, W, floor, "line", 1.6, a)
    my = floor - 170.0 * ROW_PX_CM
    fr.dashed([ROW_X[0] - 80, ROW_X[-1] + 80], [my, my], "muted", 1.4, a * 0.6 * (1 - sky), on=8, off=7)
    fr.text("median 170 cm", ROW_X[-1] + 80, my - 12, "sans", 22, 600, "muted", a * (1 - sky), align="right")
    for k in range(ROW_N):
        if k == ROW_MID:
            continue
        h = ROW_CM[k] * ROW_PX_CM * (0.92 + 0.08 * rise)
        crowd.person(fr, ROW_X[k], floor + 30 * (1 - rise), h, a * rise, fill=0.06, width=1.8)
    # the giant: grows, then the camera rides up with his head
    g = ease_in(lin(t, GROW_T, CRANE_T))
    s = lerp(170.0 * ROW_PX_CM, GIANT_PX, g)
    feet = FLOOR19 + 30 * (1 - rise)
    draw_giant(fr, ROW_X[ROW_MID], feet - s, feet + drop, s, a * rise)
    # the altitude readout
    ra = a * smooth(lin(t, GROW_T, GROW_T + 0.4))
    if ra > 0.003:
        if t < CRANE_T:
            km = 10**-2.25 * (s / GIANT_PX)
        else:
            km = 10 ** log_alt(t)
        if km < 1:
            value = f"{km * 1000:,.0f} m"
        elif km < 1000:
            value = f"{km:,.0f} km"
        else:
            value = "> 1,000 km"
        hud.readout(fr, 1560, 230, "height", value, "tail" if km >= 1000 else "ink", ra, 34)


SKY_RNG = np.random.default_rng(60)
STARS = np.c_[SKY_RNG.uniform(0, W, 160), SKY_RNG.uniform(2.1, 5.0, 160)]  # x, log10 km
CLOUDS = [(260.0, -0.1, 1.0), (720.0, 0.25, 1.3), (1250.0, 0.05, 1.1), (1680.0, 0.4, 0.9), (480.0, 0.55, 0.8)]


def draw_sky(fr, t, a):
    # clouds (1-3 km)
    with fr.blurred(14.0):
        for x, lk, sc in CLOUDS:
            y = y_alt(t, lk)
            if -200 < y < H + 200:
                for dx, dy, r in ((-60, 10, 60), (0, -10, 80), (70, 8, 64), (130, 18, 44)):
                    fr.circle(x + dx * sc, y + dy * sc, r * sc, "ink", alpha=a * 0.10, fill=True)
    # the atmosphere thins out: a blue haze up to the thin blue line at 100 km
    y_top, y_bot = y_alt(t, 2.0), y_alt(t, 0.6)
    if y_top < H and y_bot > 0:
        shader = skia.GradientShader.MakeLinear(
            [skia.Point(0, y_top), skia.Point(0, y_bot)],
            [col("ball", 0.03 * a), col("ball", 0.10 * a), col("ball", 0.0)],
            [0.0, 0.45, 1.0],
        )
        fr.c.drawRect(skia.Rect.MakeLTRB(0, max(0.0, y_top), W, min(float(H), y_bot)), skia.Paint(Shader=shader))
    if -20 < y_top < H + 20:
        fr.line(0, y_top, W, y_top, "ball", 2.0, a * 0.9, glow=1.0)
        fr.text("edge of space · 100 km", 120, y_top - 14, "sans", 22, 600, "ball", a, align="left")
    # the space station's orbit
    y_iss = y_alt(t, math.log10(400.0))
    if -20 < y_iss < H + 20:
        fr.dashed([0, W], [y_iss, y_iss], "muted", 1.8, a, on=12, off=9)
        fr.text("space station · 400 km", 120, y_iss - 14, "sans", 22, 600, "ink", a, align="left")
    # stars above the atmosphere
    ys = HEAD_Y + (log_alt(t) - STARS[:, 1]) * K_DEC
    vis = (ys > -10) & (ys < H + 10)
    if vis.any():
        crowd.draw_dots(fr, np.c_[STARS[vis, 0], ys[vis]], 1.4, "ink", a * 0.5)


# ------------------------------------------------------------------ S20C: the same long tails elsewhere

CARD_W, CARD_H = 360.0, 280.0
CARD_X = (300.0, 740.0, 1180.0, 1620.0)
CARD_Y = 520.0
CARD_NAMES = ("cities", "earthquakes", "market crashes", "viral videos")
CARD_ALPHA = (1.15, 1.5, 1.3, 1.05)  # Pareto exponents (illustrative)


def card_bars(k):
    rng = np.random.default_rng(70 + k)
    x = np.arange(16)
    d = (1 + x) ** -CARD_ALPHA[k] * np.exp(rng.normal(0, 0.12, 16))
    d[-1] = d[-1] * 1.8  # one isolated extreme
    d[-4:-1] *= 0.25
    return d / d.max()


CARD_BARS = [card_bars(k) for k in range(4)]


def draw_cards(fr, t):
    out = 1 - smooth(lin(t, WORLDS_T, WORLDS_T + 0.45))
    for k in range(4):
        u = ease_out(lin(t, SAME_T + 0.12 * k, SAME_T + 0.7 + 0.12 * k))
        a = smooth(u) * out
        if a <= 0.003:
            continue
        lit = smooth(lin(t, CARD_T[k], CARD_T[k] + 0.3))
        cx = lerp(960.0, CARD_X[k], u)
        cy = CARD_Y + 120 * (1 - u)
        m = skia.Matrix()
        m.setRotate((k - 1.5) * 8.0 * (1 - u), cx, cy)
        with view(fr, m):
            x0, y0 = cx - CARD_W / 2, cy - CARD_H / 2
            hud.glass_card(fr, x0, y0, CARD_W, CARD_H, a * (0.5 + 0.5 * lit), r=20, glow=0.5 * lit, glow_color="tail")
            floor = y0 + CARD_H - 36
            fr.line(x0 + 24, floor, x0 + CARD_W - 24, floor, "line", 1.4, a)
            bw = (CARD_W - 48) / 16
            grow = np.clip((t - CARD_T[k] - 0.04 * np.arange(16)) / 0.45, 0, 1)
            for j, d in enumerate(CARD_BARS[k]):
                h = d * (CARD_H - 90) * (0.08 + 0.92 * ease_out(grow[j]))
                if h < 0.5:
                    continue
                fr.rrect(
                    x0 + 24 + j * bw + 2,
                    floor - h,
                    bw - 4,
                    h,
                    2,
                    fill="tail",
                    alpha=a * (0.35 + 0.65 * lit),
                    fill_alpha=0.85,
                    glow=0.3 * lit,
                )
            fr.text(CARD_NAMES[k], cx, y0 + CARD_H + 48, "display", 32, 600, "ink", a * (0.4 + 0.6 * lit))


# ------------------------------------------------------------------ S21A: the same 5σ, two worlds

AXL = Axes(cx=230.0, floor=620.0, unit=78.0, hscale=560.0)
AXRW = Axes(cx=1130.0, floor=620.0, unit=78.0, hscale=560.0)
BELL21 = Bell(AXL, -1.2, 8.0, n=360)
DOT_R21 = 3.4
N_DOTS = NORMAL[(NORMAL > 3) & (NORMAL < 8)]
W_DOTS = W_Z[(W_Z > 3) & (W_Z < 8)]
N_XY = crowd.dot_layout(N_DOTS, AXL.x, 0.25, DOT_R21, AXL.floor, origin=3.0)
W_XY = crowd.dot_layout(W_DOTS, AXRW.x, 0.25, DOT_R21, AXRW.floor, origin=3.0)
BEYOND8_W = int((W_Z >= 8).sum())


def split_alpha(t):
    return env(t, WORLDS_T + 0.1, TRUST_T + 0.4, 0.45, 0.4)


def wealth_z_pdf(z):
    """Density of the simulated wealth on its own σ axis."""
    return wealth_pdf(W_MEAN + np.asarray(z) * W_SD) * W_SD


def draw_split(fr, t):
    a = split_alpha(t)
    if a <= 0.003:
        return
    u = ease_out(lin(t, WORLDS_T + 0.1, WORLDS_T + 0.9))
    hud.pill(fr, AXL.x(3.4), 170, "added", "bell", a, 26)
    hud.pill(fr, AXRW.x(3.4), 170, "multiplied", "tail", a, 26)
    for ax in (AXL, AXRW):
        ax.floor_line(fr, -1.2, 8.2, a)
        for z in range(9):
            x = float(ax.x(z))
            fr.line(x, ax.floor + 4, x, ax.floor + 12, "muted", 1.4, a * 0.7)
            if z:
                typmath.draw(fr, f"{z} {tc('sigma', 'sigma')}", x, ax.floor + 36, 22, color="muted", alpha=a * 0.8)
    # left: the bell and its 10,000 seeded samples beyond 3σ
    BELL21.draw(fr, reveal=u, alpha=a, width=3.2, glow=0.7, fill=0.08)
    crowd.draw_dots(fr, N_XY, DOT_R21, "ball", a * u)
    # right: the wealth curve (a spike, then the long tail) and its samples beyond 3σ
    z0 = (0.05 - W_MEAN) / W_SD  # the floor of the walk
    zs = np.linspace(z0, z0 + (8.2 - z0) * u, 500)
    clip = skia.Path()
    clip.addRect(skia.Rect.MakeLTRB(AXRW.x(-1.3), 190, AXRW.x(8.3), AXRW.floor + 2))
    with clipped(fr, clip):
        fr.poly(AXRW.x(zs), AXRW.y(wealth_z_pdf(zs)), "tail", 3.2, a, glow=0.8)
    crowd.draw_dots(fr, W_XY, DOT_R21, "ball", a * u)
    # the 5σ line in both worlds
    na = a * smooth(lin(t, NOT_T - 0.3, NOT_T + 0.2))
    if na > 0.003:
        x = float(AXL.x(5))
        fr.line(x, AXL.floor, x, AXL.floor - 220, "bell", 1.0, na * 0.6)
        hud.readout(fr, x, AXL.floor - 250, "", f"1 in {round(1 / P5, -5):,.0f}", "bell", na, 26)
        typmath.draw(fr, '"beyond" 5 sigma', float(AXL.x(5)), AXL.floor + 82, 24, color="muted", alpha=na)
        hud.readout(fr, float(AXL.x(5)), AXL.floor + 128, "", f"{BEYOND5_N} of {N_SIM:,}", "ink", na, 26)
        x = float(AXRW.x(5))
        fr.line(x, AXRW.floor, x, AXRW.floor - 220, "tail", 3.0, na, glow=0.8)
        fr.glow_dot(x, AXRW.floor - 220, 6.0, "tail", na, strength=1.2)
        hud.readout(fr, x, AXRW.floor - 250, "", f"1 in {N_SIM / BEYOND5_W:,.0f}", "tail", na, 26)
        typmath.draw(fr, '"beyond" 5 sigma', float(AXRW.x(5)), AXRW.floor + 82, 24, color="muted", alpha=na)
        hud.readout(fr, float(AXRW.x(5)), AXRW.floor + 128, "", f"{BEYOND5_W} of {N_SIM:,}", "ink", na, 26)
    # what lies past the frame: the richest, far out
    ea = a * smooth(lin(t, MOST_T, MOST_T + 0.4))
    if ea > 0.003:
        x0 = float(AXRW.x(8.25))
        glow = 0.6 + 0.8 * math.exp(-max(0.0, t - MOST_T) / 0.5)
        hud.arrow(fr, x0 - 40, AXRW.floor - 30, x0 + 20, AXRW.floor - 30, "tail", 2.4, ea, glow=glow, head=14)
        typmath.draw(
            fr,
            f'"max" {ZMAX_W:.0f} {tc("tail", "sigma")}',
            x0 - 10,
            AXRW.floor - 62,
            24,
            color="tail",
            alpha=ea,
            glow=glow * 0.6,
        )
        draw_share(fr, t, ea)


def draw_share(fr, t, a):
    """The top 1 %'s share of all the simulated wealth."""
    x0, x1, y = float(AXRW.x(-1.0)), float(AXRW.x(8.0)), AXRW.floor + 220
    u = ease_out(lin(t, MOST_T + 0.1, MOST_T + 0.8))
    fr.rrect(x0, y - 14, x1 - x0, 28, 14, fill="muted", alpha=a, fill_alpha=0.18)
    xs = x1 - (x1 - x0) * TOP1 * u
    fr.rrect(xs, y - 14, x1 - xs, 28, 14, fill="tail", alpha=a, fill_alpha=0.9, glow=0.6)
    fr.text(f"top 1% hold {100 * TOP1:.0f}%", x1, y + 52, "sans", 26, 600, "tail", a * u, align="right")
    fr.text("all wealth", x0, y + 52, "sans", 22, 600, "muted", a, align="left")


# ------------------------------------------------------------------ S21B: one question

AXQ = Axes(cx=960.0, floor=560.0, unit=150.0, hscale=700.0)
BELLQ = Bell(AXQ, -3.4, 3.4)
TOG_Y = 700.0
TOG_X = (700.0, 1220.0)
AX_MINI_B = Axes(cx=700.0, floor=960.0, unit=55.0, hscale=330.0)
MINI_B = Bell(AX_MINI_B, -2.8, 2.8)
AX_MINI_T = Axes(cx=1070.0, floor=960.0, unit=34.0, hscale=230.0)


def draw_question(fr, t):
    a = smooth(lin(t, TRUST_T, TRUST_T + 0.4)) * (1 - smooth(lin(t, END - 0.35, END)))
    if a <= 0.003:
        return
    AXQ.floor_line(fr, -3.6, 3.6, a)
    BELLQ.snap(fr, t, TRUST_T + 0.1, alpha=a, width=3.4, fill=0.10)
    qa = a * smooth(lin(t, ASK_T, ASK_T + 0.3))
    if qa > 0.003:
        pop = math.exp(-max(0.0, t - ASK_T) / 0.3)
        hud.pill(fr, 960, 200, "?", "ink", qa, 34 * (1 + 0.2 * pop))
    ta = a * smooth(lin(t, ARE_T, ARE_T + 0.4))
    if ta <= 0.003:
        return
    lp = smooth(lin(t, PLUS_T, PLUS_T + 0.25))
    lt = smooth(lin(t, TIMES_T, TIMES_T + 0.25))
    badge(
        fr,
        TOG_X[0],
        TOG_Y,
        "+",
        "bell",
        ta * (0.4 + 0.6 * lp),
        r=44,
        glow=0.6 * lp,
        pop=math.exp(-max(0.0, t - PLUS_T) / 0.25) * lp,
    )
    badge(
        fr,
        TOG_X[1],
        TOG_Y,
        "×",
        "tail",
        ta * (0.4 + 0.6 * lt),
        r=44,
        glow=0.6 * lt,
        pop=math.exp(-max(0.0, t - TIMES_T) / 0.25) * lt,
    )
    if lp > 0:
        AX_MINI_B.floor_line(fr, -3.0, 3.0, ta * lp)
        MINI_B.snap(fr, t, PLUS_T + 0.05, alpha=ta, width=2.6, trace=0.4, fill=0.12)
    if lt > 0:
        AX_MINI_T.floor_line(fr, -0.3, 12.0, ta * lt)
        u = ease_out(lin(t, TIMES_T + 0.05, TIMES_T + 0.6))
        ws = np.linspace(0.02, 0.02 + 11.5 * u, 260)
        fr.poly(AX_MINI_T.x(ws), AX_MINI_T.y(wealth_pdf(ws)), "tail", 2.6, ta * lt, glow=0.8)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_ch4_tail(fr, t)
    draw_warning_label(fr, t)
    red_breath(fr, pulse_once(t, WARN_T, 1.2))
    if t < WEALTH_T + 0.5:
        draw_heights(fr, t)
    if WEALTH_T < t < MULT2_T + 0.5:
        draw_lanes(fr, t)
    if MULT2_T - 0.3 < t < IF_T + 0.6:
        draw_pour(fr, t)
    if IF_T - 0.2 < t < SAME_T + 0.6:
        draw_crane(fr, t)
    if SAME_T < t < WORLDS_T + 0.5:
        draw_cards(fr, t)
    if WORLDS_T < t < TRUST_T + 0.5:
        draw_split(fr, t)
    if t > TRUST_T:
        draw_question(fr, t)
    hud.eyebrow(fr, t, "05 · WHERE IT BREAKS", 337.0)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch5:{Path(__file__).stat().st_mtime_ns}"
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
    337.2,
    338.8,
    339.4,
    340.6,
    342.2,
    344.0,
    346.4,
    348.0,
    349.6,
    351.2,
    352.6,
    353.8,
    355.6,
    357.0,
    357.6,
    358.6,
    360.4,
    361.8,
    363.2,
    364.4,
    365.4,
    366.4,
    367.6,
    368.6,
    369.6,
    371.4,
    372.4,
    374.6,
    376.0,
    378.0,
    380.6,
    382.6,
    383.6,
    385.0,
    385.9,
    386.6,
    387.1,
]
