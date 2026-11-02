"""CHAPTER 4 - THE RULER: 68, 95, 99.7 (S17-S18), 04:55.220 (#883 "Those") - 05:36.780 (#986 "But").

S17  Heights in sigma  the formula and dials hand over -> a violet σ ruler slides in under the bell -> 8,000 heights pour
                       in as dots -> μ = 175 cm, σ = 7 cm -> the ruler relabels in cm -> markers step out to ±1σ (168, 182),
                       the band fills: 68% -> ±2σ: 95% -> ±3σ: 99.7% -> the classic nested diagram holds.
S18  Five sigma        the view pulls out to ±5σ -> a loupe opens on the 5σ tail (log scale): < 1 in 1,000,000 ->
                       a detector plot: data over a smooth background with a bump, the significance meter climbs to
                       5σ, "discovery" lights gold -> the bell returns, its tails thin to hairlines and fade to one dot.
"""

from __future__ import annotations

import contextlib
import itertools
import math
from pathlib import Path

import numpy as np
import skia
import typmath
from components import crowd, hud
from components.bell import Bell, band_share, pdf
from components.dials import dial_pair
from components.histogram import Axes
from cues import AUDIO, beat, cue
from fx import Frame, ease_io, ease_out, env, font, lin, pulse, smooth
from scipy.special import ndtr
from theme import THEME, H, W
from typmath import tc

from scenes import ch3_formula as ch3

START = cue(883)  # 295.22 "Those two dials give us a powerful ruler."
END = cue(986)  # 336.78 "But ..."

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


# ------------------------------------------------------------------ timing

DIALS_T = b(884)  # "two dials"
RULER_T = b(889)  # "powerful ruler"
MEN_T = b(892)  # "adult men"
AVG_T = b(898)  # "average height"
CM175_T = b(902)  # "175 centimeters"
SD_T = b(906)  # "standard deviation"
SEVEN_T = b(910)  # "about seven"
STEP_T = b(911)  # "Step one sigma away on each side"
L168_T, R182_T = b(919), b(921)
BAND_T = b(923)  # "That band"
P68_T = b(927)  # "68%"
TWO_T = b(931)  # "Step out two sigma"
P95_T = b(939)
THREE_T = b(940)  # "Three sigma"
P997_T = b(945)
FIVE_T = b(946)  # "Beyond five sigma"
LOUPE_T = b(948)
MILLION_T = b(951)  # "fewer than one in a million"
WHY_T = b(957)  # "This is why"
PHYS_T = b(960)  # "physicists"
METER_T = b(964)  # "five sigma result"
DISC_T = b(971)  # "discovery"
UNDER_T = b(972)  # "Under a bell curve"
EXTREME_T = b(976)  # "extreme events"
IMPOSSIBLE_T = b(984)  # "almost impossible"

# ------------------------------------------------------------------ geometry

N_MEN = 3900
HEIGHTS = crowd.sample_heights(N_MEN, seed=73)
Z_MEN = (HEIGHTS - crowd.MEAN_CM) / crowd.SD_CM
DOT_R = 3.0
UNIT = 200.0
PX_CM = UNIT / crowd.SD_CM
COLS = int(PX_CM // (2 * DOT_R))
FLOOR = 680.0
AXR = Axes(cx=960.0, floor=FLOOR, unit=UNIT, hscale=N_MEN * 2 * DOT_R / (crowd.SD_CM * COLS))
DOTS = crowd.dot_layout(
    HEIGHTS, lambda v: 960.0 + (np.asarray(v) - crowd.MEAN_CM) * PX_CM, 1.0, DOT_R, FLOOR, origin=crowd.MEAN_CM - 0.5
)
ZOOM = 0.46
AXZ = Axes(cx=960.0, floor=FLOOR, unit=UNIT * ZOOM, hscale=AXR.hscale * ZOOM)
GROUPS = [
    np.abs(Z_MEN) < 1,
    (np.abs(Z_MEN) >= 1) & (np.abs(Z_MEN) < 2),
    (np.abs(Z_MEN) >= 2) & (np.abs(Z_MEN) < 3),
    np.abs(Z_MEN) >= 3,
]
RELEASE = MEN_T + 1.8 * np.arange(N_MEN) / N_MEN
RULER_Y = FLOOR + 32.0
SHARES = {k: band_share(k) for k in (1, 2, 3)}  # 0.6827, 0.9545, 0.9973 from erf
SPOKEN = {1: "68%", 2: "95%", 3: "99.7%"}
P_TIMES = {1: P68_T, 2: P95_T, 3: P997_T}
TAIL5 = 2 * float(ndtr(-5.0))  # P(|Z| > 5) = 5.7e-7


def axes_at(t):
    u0 = ease_io(lin(t, RULER_T, RULER_T + 1.0))
    ax = lerp_axes(ch3.AX16, AXR, u0)
    return lerp_axes(ax, AXZ, zoom_u(t))


def zoom_u(t):
    return ease_io(lin(t, FIVE_T, FIVE_T + 1.1))


def bell_at(t):
    ax = axes_at(t)
    zr = lerp(3.6, 5.8, zoom_u(t))
    return ax, Bell(ax, -zr, zr, n=360)


def scene_alpha(t):
    """The bell-and-ruler stage: away for the detector plot (18B), back for 18C."""
    return 1 - env(t, WHY_T + 0.2, UNDER_T + 0.3, 0.4, 0.5)


# ------------------------------------------------------------------ S17: handover from chapter 3


def draw_handover(fr, t):
    a = 1 - smooth(lin(t, RULER_T - 0.2, RULER_T + 0.35))
    if a <= 0.003:
        return
    with faded(fr, a):
        ch3.draw_formula16(fr, t)
    glow = pulse(t, DIALS_T, 0.9)
    dial_pair(
        fr,
        *ch3.DIAL_C,
        0.0,
        1.0,
        a,
        gap=ch3.DIAL_GAP,
        mu_range=2.0,
        sigma_range=(0.5, 2.0),
        active_mu=glow,
        active_sigma=glow,
    )


# ------------------------------------------------------------------ S17: the ruler


def sigma_label(k):
    if k == 0:
        return tc("bell", "mu")
    return f"{'+' if k > 0 else '-'}{abs(k)} {tc('sigma', 'sigma')}"


def lit_label(k, t):
    """A ruler label lights as its marker arrives (168 and 182 on their words)."""
    if abs(k) == 1:
        at = L168_T if k < 0 else R182_T
    elif abs(k) == 2:
        at = TWO_T + 1.0
    elif abs(k) == 3:
        at = THREE_T + 0.6
    else:
        return 0.0
    return smooth(lin(t, at, at + 0.3)) * (1 - smooth(lin(t, FIVE_T - 0.3, FIVE_T)))


def draw_ruler(fr, t, ax):
    a = scene_alpha(t) * smooth(lin(t, RULER_T, RULER_T + 0.4))
    if a <= 0.003:
        return
    zr = lerp(3.0, 5.0, zoom_u(t))
    slide = 260 * (1 - ease_out(lin(t, RULER_T, RULER_T + 0.8)))
    x0, x1 = float(ax.x(-zr - 0.25)) - slide, float(ax.x(zr + 0.25)) - slide
    dim = 1 - 0.55 * smooth(lin(t, UNDER_T, UNDER_T + 0.6))
    fr.line(x0, RULER_Y, x1, RULER_Y, "sigma", 2.2, a * 0.8 * dim, glow=0.3)
    cm = smooth(lin(t, SEVEN_T + 0.2, SEVEN_T + 0.7)) * (1 - smooth(lin(t, FIVE_T, FIVE_T + 0.4)))
    kmax = round(zr)
    for k in range(-5, 6):
        ka = a * dim * clamp01((zr + 0.3 - abs(k)) / 0.3)
        if ka <= 0.003:
            continue
        x = float(ax.x(k)) - slide
        fr.line(x, RULER_Y - 10, x, RULER_Y + 10, "sigma", 2.0, ka)
        for j in range(1, 5):  # minor ticks
            if k < kmax:
                xm = x + j * (float(ax.x(k + 1)) - float(ax.x(k))) / 5
                fr.line(xm, RULER_Y - 4, xm, RULER_Y + 4, "sigma", 1.2, ka * 0.5)
        lit = lit_label(k, t)
        size = 28 + 6 * lit
        y = RULER_Y + 44
        if cm < 1:
            typmath.draw(
                fr,
                sigma_label(k),
                x,
                y - 8 * cm,
                size,
                color="ink" if k else None,
                alpha=ka * (1 - cm) * (0.75 + 0.25 * lit),
                glow=0.6 * lit,
            )
        if cm > 0 and abs(k) <= 3:
            cmv = f"{crowd.MEAN_CM + crowd.SD_CM * k:.0f}"
            col = "bell" if k == 0 else "ink"
            typmath.number(fr, cmv, x, y + 8 * (1 - cm), size, col, ka * cm * (0.7 + 0.3 * lit), glow=0.7 * lit)


def clamp01(x):
    return max(0.0, min(1.0, x))


def draw_dots_s17(fr, t, ax):
    a = scene_alpha(t) * (1 - smooth(lin(t, FIVE_T, FIVE_T + 0.5)))
    if a <= 0.003 or t < MEN_T:
        return
    s = ax.unit / UNIT
    xy = DOTS.copy()
    if t < RELEASE[-1] + 0.5:  # the pour: each dot drops into its stack
        u = np.clip((t - RELEASE) / 0.35, 0.0, 1.0)
        xy[:, 1] -= 240 * (1 - u) ** 2
        live = u > 0
    else:
        live = np.ones(N_MEN, bool)
    xy[:, 0] = ax.cx + (xy[:, 0] - 960.0) * s
    xy[:, 1] = ax.floor - (FLOOR - xy[:, 1]) * s
    r = DOT_R * s
    d = smooth(lin(t, P68_T, P68_T + 0.4))
    level = (
        smooth(lin(t, P68_T, P68_T + 0.4)) + smooth(lin(t, P95_T, P95_T + 0.4)) + smooth(lin(t, P997_T, P997_T + 0.4))
    )
    for j, g in enumerate(GROUPS):
        lit = clamp01(level - j)
        ga = 0.85 * (1 - d) + d * (0.25 + 0.75 * lit)
        crowd.draw_dots(fr, xy[g & live], r, "ball", a * ga, glow=0.06 * d * lit)


def marker_k(t):
    m = ease_io(lin(t, STEP_T + 0.6, STEP_T + 2.0))
    m += ease_io(lin(t, TWO_T + 0.3, TWO_T + 1.1))
    m += ease_io(lin(t, THREE_T, THREE_T + 0.7))
    return m


def draw_bands(fr, t, bell):
    a = scene_alpha(t) * (1 - smooth(lin(t, FIVE_T, FIVE_T + 0.5)))
    m = marker_k(t)
    if a <= 0.003 or m <= 0.002:
        return
    f1 = smooth(lin(t, BAND_T, BAND_T + 0.5))
    if m > 2:
        bell.band(fr, m, alpha=a, fill=0.07, edges=False)
    if m > 1:
        bell.band(fr, min(m, 2.0), alpha=a, fill=0.09, edges=False)
    bell.band(fr, min(m, 1.0), alpha=a * f1, fill=0.16, edges=False)
    ax = bell.ax
    for k in (1.0, 2.0):  # settled edges stay as faint guides
        if m > k + 0.05:
            for z in (-k, k):
                fr.line(float(ax.x(z)), ax.floor, float(ax.x(z)), float(ax.y(pdf(z))), "sigma", 1.6, a * 0.5)
    for z in (-m, m):  # the moving markers
        x, y = float(ax.x(z)), float(ax.y(pdf(z)))
        fr.line(x, ax.floor, x, y, "sigma", 2.6, a, glow=0.6)
        fr.circle(x, y, 5.0, "sigma", alpha=a, fill=True)
        tri = skia.Path()
        tri.addPoly(
            [skia.Point(x, RULER_Y - 12), skia.Point(x - 8, RULER_Y - 26), skia.Point(x + 8, RULER_Y - 26)], True
        )
        fr.path_fill(tri, "sigma", a, glow=0.5)


def draw_mean(fr, t, bell):
    a = scene_alpha(t) * (1 - smooth(lin(t, FIVE_T, FIVE_T + 0.5)))
    if a <= 0.003:
        return
    bell.mean_line(fr, alpha=a, u=1.0)
    la = a * env(t, CM175_T, BAND_T + 0.2, 0.35, 0.3)
    if la > 0.003:
        top = float(bell.ax.y(pdf(0.0)))
        fr.text("175 cm", float(bell.ax.x(0)) - 20, top - 16, "display", 34, 600, "bell", la, align="right", glow=0.3)
    # σ = 7 cm: the typical step from μ
    sa = a * env(t, SD_T, STEP_T + 0.5, 0.3, 0.3)
    if sa > 0.003:
        u = ease_out(lin(t, SD_T, SD_T + 0.6))
        ax = bell.ax
        y = float(ax.y(pdf(0.0))) - 44  # above the pile, clear of the dots
        x0, x1 = float(ax.x(0)), float(ax.x(u))
        fr.dashed([x1, x1], [y + 12, ax.floor], "sigma", 1.6, sa * 0.6 * u, on=7, off=6)  # down to +1σ
        fr.line(x0, y, x1, y, "bg", 9.0, sa * 0.8)
        hud.arrow(fr, x0, y, x1, y, "sigma", 3.0, sa, glow=0.8, head=15.0)
        e = smooth(lin(t, SEVEN_T, SEVEN_T + 0.3))
        typmath.draw(fr, tc("sigma", "sigma"), (x0 + x1) / 2, y - 34, 36, alpha=sa * u * (1 - e))
        typmath.draw(fr, f'{tc("sigma", "sigma")} = "7 cm"', (x0 + x1) / 2, y - 34, 36, alpha=sa * e)


def draw_men_pill(fr, t):
    hud.pill(fr, 960, 150, "adult men's heights", "ball", env(t, MEN_T, BAND_T, 0.4, 0.4), 26)


def draw_shares(fr, t):
    """The big readout for the current band, its erf value, and the nested brackets under the ruler."""
    a = scene_alpha(t) * (1 - smooth(lin(t, FIVE_T, FIVE_T + 0.4)))
    if a <= 0.003:
        return
    for k in (1, 2, 3):
        t0 = P_TIMES[k]
        nxt = P_TIMES.get(k + 1, FIVE_T)
        ra = a * env(t, t0, nxt + 0.15, 0.3, 0.3 if k < 3 else 0.01)
        if ra > 0.003:
            rise = 14 * (1 - ease_out(lin(t, t0, t0 + 0.45)))
            fr.text(SPOKEN[k], 960, 250 + rise, "display", 92, 600, "ink", ra, glow=0.5)
            hud.tabular(fr, f"{100 * SHARES[k]:.2f}%", 960, 298 + rise, 26, "muted", ra)
        ba = a * smooth(lin(t, t0, t0 + 0.4))
        if ba <= 0.003:
            continue
        ax = axes_at(t)
        y = RULER_Y + 108 + 46 * (k - 1)
        u = ease_out(lin(t, t0, t0 + 0.5))
        x0, x1 = float(ax.x(-k * u)), float(ax.x(k * u))
        fr.line(x0, y, x1, y, "sigma", 1.8, ba * (1.0 - 0.2 * k))
        for x in (x0, x1):
            fr.line(x, y - 9, x, y + 1, "sigma", 1.8, ba * (1.0 - 0.2 * k))
        label = SPOKEN[k]
        w = font("sans", 22, 600).measureText(label) + 26
        fr.rrect(960 - w / 2, y - 17, w, 34, 17, fill="bg", fill_alpha=ba)
        hud.pill(fr, 960, y, label, "sigma", ba, 20)


# ------------------------------------------------------------------ S18A: five sigma and the loupe

LOUPE = (1450.0, 330.0, 195.0)


def draw_loupe(fr, t, ax):
    a = scene_alpha(t) * env(t, LOUPE_T, WHY_T + 0.6, 0.3, 0.4)
    if a <= 0.003:
        return
    cx, cy, R0 = LOUPE
    R = R0 * (0.3 + 0.7 * back_out(lin(t, LOUPE_T, LOUPE_T + 0.55)))
    px, py = float(ax.x(5.0)), ax.floor
    fr.circle(px, py, 11.0, "sigma", 2.0, a, glow=0.6)
    ang = math.atan2(py - cy, px - cx)
    fr.dashed(
        [px - 11 * math.cos(ang), cx + R * math.cos(ang)],
        [py - 11 * math.sin(ang), cy + R * math.sin(ang)],
        "muted",
        1.6,
        a * 0.8,
        on=7,
        off=6,
    )
    hud.glass_card(fr, cx - R, cy - R, 2 * R, 2 * R, a, r=int(R))
    disc = skia.Path()
    disc.addCircle(cx, cy, R - 2)
    with clipped(fr, disc):

        def lx(z):
            return cx - 0.78 * R0 + (np.asarray(z) - 3.0) / 3.2 * 1.56 * R0

        def ly(lg):
            return cy - 0.62 * R0 + (-2.0 - np.asarray(lg)) / 7.5 * 1.3 * R0

        for e in (-3, -5, -7, -9):  # decades
            y = float(ly(e))
            fr.line(cx - R0, y, cx + R0, y, "grid", 1.0, a)
            typmath.draw(fr, f"10^({e})", cx - 0.6 * R0, y - 13, 21, color="muted", alpha=a * 0.9)
        x5 = float(lx(5.0))
        fr.dashed([x5, x5], [cy - R0, cy + R0], "sigma", 1.6, a * 0.8, on=6, off=5)
        z = np.linspace(3.0, 6.2, 90)
        u = ease_out(lin(t, LOUPE_T + 0.25, LOUPE_T + 1.0))
        k = max(2, int(len(z) * u))
        lg = np.log10(pdf(z))
        fr.poly(lx(z[:k]), ly(lg[:k]), "bell", 2.6, a, glow=0.7)
        beyond = z >= 5.0
        if u >= 0.99:
            fr.poly(
                lx(z[beyond]), ly(lg[beyond]), "sigma", 3.6, a * smooth(lin(t, MILLION_T, MILLION_T + 0.3)), glow=0.9
            )
        typmath.draw(fr, f"5 {tc('sigma', 'sigma')}", x5 + 26, cy + 0.66 * R0, 28, color="ink", alpha=a)
    fr.circle(cx, cy, R, "sigma", 1.6, a * 0.7, glow=0.3)
    fr.text("log scale", cx, cy + R + 32, "sans", 20, 600, "muted", a, tracking=0.08)


def back_out(u):
    u = clamp01(u)
    s = 1.7
    v = u - 1
    return 1 + (s + 1) * v**3 + s * v**2


def draw_million(fr, t):
    a = scene_alpha(t) * env(t, MILLION_T, WHY_T + 0.6, 0.35, 0.4)
    if a <= 0.003:
        return
    rise = 12 * (1 - ease_out(lin(t, MILLION_T, MILLION_T + 0.45)))
    fr.text("< 1 in 1,000,000", 900, 250 + rise, "display", 64, 600, "ink", a, glow=0.4)
    mant, ex = f"{TAIL5:.1e}".split("e")
    typmath.draw(fr, f"P(|z| > 5) = {mant} times 10^({int(ex)})", 900, 312 + rise, 28, color="muted", alpha=a)


# ------------------------------------------------------------------ S18B: the detector plot

PLOT = (330.0, 760.0, 1000.0, 420.0)  # left, floor, width, height
NB = 44
XB = (np.arange(NB) + 0.5) / NB
BUMP_X, BUMP_W = 0.56, 0.022


def background(x):
    return 820 * np.exp(-2.3 * np.asarray(x)) + 60


def signal(x):
    return 150 * np.exp(-0.5 * ((np.asarray(x) - BUMP_X) / BUMP_W) ** 2)


COUNTS = np.random.default_rng(46).poisson(background(XB) + signal(XB)).astype(float)
YMAX = 960.0
IN_BUMP = np.abs(XB - BUMP_X) < 2.2 * BUMP_W


def plot_xy(x, n):
    left, floor, w, h = PLOT
    return left + np.asarray(x) * w, floor - np.asarray(n) / YMAX * h


def draw_plot(fr, t):
    a = env(t, PHYS_T - 0.1, UNDER_T + 0.5, 0.35, 0.5)
    if a <= 0.003:
        return
    left, floor, w, h = PLOT
    fr.line(left, floor, left + w, floor, "line", 1.6, a)
    fr.line(left, floor, left, floor - h - 20, "line", 1.6, a)
    fr.text("mass", left + w, floor + 40, "sans", 22, 600, "muted", a, align="right")
    fr.text("events", left - 18, floor - h - 30, "sans", 22, 600, "muted", a, align="left")
    hud.pill(fr, left + w / 2, 175, "particle collisions", "muted", a * 0.9, 22)
    # the smooth background
    bu = ease_io(lin(t, PHYS_T + 0.5, PHYS_T + 1.3))
    if bu > 0:
        xs = np.linspace(0.0, bu, 160)
        bx, by = plot_xy(xs, background(xs))
        fr.dashed(bx, by, "muted", 2.0, a * 0.9, on=10, off=8)
    disc = smooth(lin(t, DISC_T, DISC_T + 0.4))
    # data: points with error bars, dropping in left to right
    gx, gy = plot_xy(XB, COUNTS)
    err = np.sqrt(COUNTS) / YMAX * h
    for i in range(NB):
        u = clamp01((t - PHYS_T - 0.9 * i / NB) / 0.35)
        if u <= 0:
            continue
        y = gy[i] - 40 * (1 - ease_out(u))
        hot = disc if IN_BUMP[i] else 0.0
        color = "bell" if hot > 0.5 else "ball"
        pa = a * smooth(u)
        fr.line(gx[i], y - err[i], gx[i], y + err[i], color, 1.6, pa * 0.7)
        fr.circle(gx[i], y, 4.6, color, alpha=pa, fill=True, glow=0.3 + 0.9 * hot)
    # the fitted bump lights gold on "discovery"
    if disc > 0:
        xs = np.linspace(BUMP_X - 0.12, BUMP_X + 0.12, 120)
        sx, sy = plot_xy(xs, background(xs) + signal(xs))
        fr.poly(sx, sy, "bell", 3.0, a * disc, glow=1.0)
        bx, by = plot_xy(BUMP_X, background(BUMP_X) + signal(BUMP_X))
        hud.pill(fr, float(bx), float(by) - 70, "discovery", "bell", a * disc, 24)
    draw_meter(fr, t, a)


METER = (1600.0, 760.0, 420.0)  # x, floor (0σ), height up to 5σ


def draw_meter(fr, t, a):
    ma = a * smooth(lin(t, METER_T - 0.4, METER_T))
    if ma <= 0.003:
        return
    x, floor, h = METER
    disc = smooth(lin(t, DISC_T, DISC_T + 0.4))
    v = 5.0 * ease_io(lin(t, METER_T, METER_T + 2.4))
    hud.glass_card(fr, x - 22, floor - h - 22, 44, h + 44, ma, r=22)
    top = floor - v / 5 * h
    fill = "bell" if disc > 0.5 else "sigma"
    fr.rrect(x - 9, top, 18, floor - top, 9, fill=fill, fill_alpha=ma * 0.85, glow=0.5 + 0.8 * disc)
    for k in range(1, 6):
        y = floor - k / 5 * h
        passed = smooth(clamp01((v - k + 0.15) / 0.15))
        col = "bell" if (k == 5 and disc > 0.5) else "ink"
        fr.line(x + 26, y, x + 38, y, "muted", 1.6, ma)
        typmath.draw(
            fr,
            f"{k} {tc('sigma', 'sigma')}",
            x + 74,
            y,
            26,
            color=col if passed > 0.5 else "muted",
            alpha=ma * (0.5 + 0.5 * passed),
            glow=0.8 * disc if k == 5 else 0.0,
        )


# ------------------------------------------------------------------ S18C: tails to hairlines


def draw_bell(fr, t):
    """The gold bell through the whole chapter; in 18C its tails thin to hairlines and the 5σ tail fades to a dot."""
    a = scene_alpha(t)
    if a <= 0.003:
        return
    ax, bell = bell_at(t)
    fill = 0.10 * (1 - smooth(lin(t, MEN_T, MEN_T + 0.8))) + 0.06 * smooth(lin(t, UNDER_T, UNDER_T + 0.6))
    ax.floor_line(fr, bell.z0 - 0.2, bell.z1 + 0.2, a)
    if fill > 0.003:
        fr.path_fill(bell.area_path(), "bell", a * fill)
    thin = ease_io(lin(t, EXTREME_T, EXTREME_T + 1.6))
    gone = smooth(lin(t, IMPOSSIBLE_T, IMPOSSIBLE_T + 0.9))
    if thin <= 0:
        bell.draw(fr, alpha=a, width=3.6, glow=0.8)
        return
    core = 2.0
    p = bell.path(z0=-core, z1=core)
    fr.path_stroke(p, "bell", 3.6, a, glow=0.8)
    zs = np.linspace(core, bell.z1, 70)
    for side in (-1, 1):
        for z0, z1 in itertools.pairwise(zs):
            zm = (z0 + z1) / 2
            wid = lerp(3.6, max(0.5, 3.6 * math.exp(-0.5 * (zm * zm - core * core))), thin)
            sa = a * (1 - 0.6 * thin * clamp01((zm - core) / 2.0)) * (1 - gone * clamp01((zm - 4.6) / 0.4))
            if sa <= 0.003:
                continue
            xs = ax.x(np.array([side * z0, side * z1]))
            ys = ax.y(pdf(np.array([side * z0, side * z1])))
            fr.line(float(xs[0]), float(ys[0]), float(xs[1]), float(ys[1]), "bell", wid, sa, glow=0.3 * (1 - thin))
    if gone > 0:  # all that is left out past 5σ
        fr.glow_dot(float(ax.x(5.0)), ax.floor - 3, 3.0, "muted", a * gone * 0.8, strength=0.6)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    ax, bell = bell_at(t)
    if t < RULER_T + 0.4:
        draw_handover(fr, t)
    if t < WHY_T + 1.0 or t > UNDER_T:
        draw_dots_s17(fr, t, ax)
        draw_bands(fr, t, bell)
        draw_bell(fr, t)
        draw_mean(fr, t, bell)
        draw_ruler(fr, t, ax)
        draw_shares(fr, t)
        draw_loupe(fr, t, ax)
        draw_million(fr, t)
    draw_men_pill(fr, t)
    draw_plot(fr, t)
    hud.eyebrow(fr, t, "04 · THE RULER", 295.4)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch4:{Path(__file__).stat().st_mtime_ns}"
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
    295.3,
    296.2,
    297.0,
    298.6,
    299.6,
    301.0,
    302.6,
    304.0,
    304.8,
    306.4,
    308.0,
    309.6,
    311.2,
    313.6,
    315.2,
    316.6,
    318.4,
    320.0,
    321.2,
    322.9,
    323.8,
    325.6,
    327.8,
    329.0,
    330.7,
    332.0,
    334.0,
    336.0,
    336.7,
]
