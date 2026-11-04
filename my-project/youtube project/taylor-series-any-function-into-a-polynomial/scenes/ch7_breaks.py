"""CHAPTER 7 · WHERE THE TRICK BREAKS, 09:28.280 – 11:33.000 (cue #1495 "So" → #1839 "Once").

S35  So far, so good       three lanes, eˣ, sin and cos, each with its gold copy -> a probe runs out to 8 in each, and the
                           copies climb until their hug zones pass it -> the lanes ghost away, 0.4 s of black
S36  The innocent hill     f(x) = 1/(1 + x²) draws; the peak, a probe down both sides, a lens on three points (no breaks,
                           no corners, no jumps) -> 1 − x² + x⁴ − x⁶ + ⋯ while the copy hugs P₀ … P₆
S37  Inside: it settles    x = 0.5: the running sums zigzag onto the dashed height 0.8, which carries across from the hill
S38  At the edge           x = 1: 1, 0, 1, 0 on the words, never 0.5, faster and faster as a ghost trail
S39  Beyond: it explodes   x = 1.2: the swings leave the panel -> P₂ … P₂₀ on the hill, gold inside |x| < 1, alert red outside
                           -> two red walls at ±1, perfectly still
S40  Off the graph         a lens at x = 1: nothing strange -> the graph tilts back 62°, the x axis becomes the real axis of
                           the complex plane, i on the imaginary axis

S41  The hidden explosion the probe walks up the imaginary axis to i; 1/(1 + x²) -> 1/(1 + (−1)) -> 1/0 -> the PyVista surface
                         |f(z)| rises (back-ease) and the towers at ±i shoot off-frame, shake and chroma kick on 652.74 ->
                         |i| = 1 on both sides
S42  The circle of trust  the camera orbits overhead, the towers sink, cross to the flat domain image -> a pink disk grows
                         (P₂₀'s colors inside, f's outside), hits ±i, overshoots 0.15 and springs back -> R = 1 -> tilt back
                         to the side view: the circle drops onto the red walls, [−1, 1] lights, the copy lives inside it
S43  Radius of convergence the name and R = 1 -> a soft disk of knowledge around 0, the rest dims -> a 25° peek at the towers

The tilt uses a pinhole camera matched pixel for pixel to the flat hill stage (270 px per unit), so the cut is invisible;
the PyVista renders share that camera (mesh3d.match_camera) and are cached per frame under output/cache/pyvista/ch7_poles.
"""

from __future__ import annotations

import math
from functools import lru_cache
from itertools import pairwise
from pathlib import Path

import numpy as np
import skia
from components import taylor as T
from components.digits import lock
from components.fx import layer_alpha
from components.moves import comb
from components.plane import FUNCS, ComplexPlane
from components.stage import Axes, TaylorStage, clip
from cues import AUDIO, beat, cue
from theme import DISPLAY, PV_CACHE, THEME, H, W

from faceless_champ.draw import Frame, back, chroma_kick, ease_io, ease_out, hud, lin, noise, pulse, smooth, text_path
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc
from faceless_champ.draw.space import orbit
from scenes import ch4_recipe as ch4
from scenes import ch5_e as ch5
from scenes import ch6_sine as ch6

START = cue(1495)  # 568.28 "So far, the series has worked"
END = cue(1839)  # 693.00 "Once you know" (Chapter 8)

b = beat

S35, S36, S37, S38, S39, S40 = START, cue(1540), cue(1602), cue(1617), cue(1640), cue(1668)
S41, S42, S43 = cue(1691), cue(1737), cue(1799)

X = tc("x", "x")
PLUS, MINUS = tc("plus", "+"), tc("minus", "−")

# ------------------------------------------------------------------ S35 · three lanes

LANES = [
    ("exp", f"{tc('result', 'e')}^{X}", (-9.5, 3.5, -0.5, 3.4), [2, 6, 10, 14, 18, 22, 24], -8.0),
    ("sin", f"sin {X}", (-9.5, 9.5, -1.6, 1.6), [1, 5, 9, 13, 17, 21, 23], 8.0),
    ("cos", f"cos {X}", (-9.5, 9.5, -1.6, 1.6), [0, 4, 8, 12, 16, 20, 22], 8.0),
]
LANE_Y = [300.0, 540.0, 780.0]
LANE_T = [b(1505), b(1510), b(1513)]  # "E to the X", "sine", "cosine"
LANE_ST = [
    TaylorStage(f, view=v, rect=(300.0, y - 85, 1440.0, 170.0), samples=700)
    for (f, _, v, _, _), y in zip(LANES, LANE_Y)
]
FN = {"exp": np.exp, "sin": np.sin, "cos": np.cos}


def lane_hugs(k):
    t0 = b(1529) + 0.15 * k
    return [t0 + 0.22 * j for j in range(len(LANES[k][3]) - 1)]


def draw_lanes(fr, t):
    if t >= b(1540):
        return
    away = ease_io(lin(t, b(1534), b(1537) + 0.3))
    ghost = 1 - 0.85 * smooth(lin(t, b(1534), b(1534) + 0.4))
    for k, ((fname, name, _, degs, probe), st) in enumerate(zip(LANES, LANE_ST)):
        a = smooth(lin(t, LANE_T[k], LANE_T[k] + 0.4)) * ghost * (1 - smooth(lin(t, b(1537), b(1539))))
        if a <= 0.003:
            continue
        slide = 60 * (1 - ease_out(lin(t, LANE_T[k], LANE_T[k] + 0.5))) - 900 * away * (1 + 0.2 * k)
        ax = st.ax
        ax = Axes(ax.x0, ax.x1, ax.y0, ax.y1, (ax.rect[0] + slide, *ax.rect[1:]))
        fr.line(ax.left, float(ax.py(0)), ax.right, float(ax.py(0)), "axis", 1.4, a)
        fr.line(float(ax.px(0)), ax.top, float(ax.px(0)), ax.bottom, "axis", 1.0, 0.5 * a)
        st.original(fr, a, ax=ax)
        c, _, s = st.chain(t, degs, lane_hugs(k))
        st.error_band(fr, c, 0.3 * a, ax=ax)
        st.copy(fr, c, a, ax=ax, glow=0.5 + 0.5 * s, width=3.0)
        lo, hi = ch5.zone_lr(FN[fname], c, reach=10.0)
        ch4.bracket(fr, ax, max(hi, ax.x0), 1, 0.8 * a, height=30)
        ch4.bracket(fr, ax, max(lo, ax.x0), -1, 0.8 * a, height=30)
        typmath.draw(fr, name, ax.left - 40, ax.rect[1] + ax.rect[3] / 2, 46, None, a, align="right")
        # "travel as far from 0 as you like": the probe runs out to 8 (or −8 for eˣ)
        run = ease_io(lin(t, b(1516) + 0.1 * k, b(1523)))
        if run > 0:
            xp = probe * run
            caught = (lo <= xp <= hi) and t > b(1529)
            st.probe(fr, xp, a, ax=ax, drop=False, color="result" if caught else "x")
            if caught:
                fr.glow_dot(*ax.at(xp, 0), 14 * pulse(t, b(1531) + 0.15 * k, 0.6), "result", a, 1.0)


# ------------------------------------------------------------------ S36 · the innocent hill

R = (96.0, 200.0, 1728.0, 760.0)
FULL = Axes(-3.2, 3.2, -0.9, -0.9 + 760 / 270, R)  # 270 px per unit both ways: the camera in S40 matches it
LEFT = Axes(-3.2, 3.2, -0.9, -0.9 + 760 / 270, (96.0, 200.0, 900.0, 760.0))
HILL = TaylorStage("hill", view=(FULL.x0, FULL.x1, FULL.y0, FULL.y1), rect=R, samples=900)
HUG36 = ([0, 2, 4, 6], [b(1586), b(1589), b(1594)])
DEG39 = list(range(2, 22, 2))
HUG39 = [b(1656) + 0.15 * k for k in range(len(DEG39) - 1)]
f = T.fn("hill")
FORMULA = f"f({X}) = 1 / (1 + {X}^2)"
SER_P = ["1", f"{MINUS} {X}^2", f"{PLUS} {X}^4", f"{MINUS} {X}^6", f"{PLUS} dots.c"]
SER_T = [b(1585), b(1586), b(1589), b(1594), b(1599)]
SER = " ".join(SER_P)
LENS_X = [-1.5, 0.7, 1.8]
LENS_T = [b(1565), b(1567), b(1569)]
LENS_W = ["no breaks", "no corners", "no jumps"]


def hill_ax(t):
    u = ease_io(lin(t, b(1603), b(1603) + 0.8)) * (1 - ease_io(lin(t, b(1656), b(1656) + 0.8)))
    return FULL.lerp(LEFT, u)


def ranges(parts):
    out, i = [], 0
    for p in parts:
        n = len(typmath.glyphs(p)[0])
        out.append(range(i, i + n))
        i += n
    return out


R_SER = ranges(SER_P)


def hill_derivs(xs):
    d1 = -2 * xs / (1 + xs**2) ** 2
    d2 = (6 * xs**2 - 2) / (1 + xs**2) ** 3
    return d1, d2


def draw_hill(fr, t):
    if t < S36:
        return
    a = smooth(lin(t, b(1544), b(1544) + 0.5)) * (1 - smooth(lin(t, b(1683), b(1683) + 0.3)))
    if a <= 0.003:
        return
    ax = hill_ax(t)
    HILL.static(fr, a, ax=ax, labels=False)
    reveal = ease_io(lin(t, b(1544) + 0.2, b(1550) + 0.6))
    HILL.original(fr, a, reveal=reveal, ax=ax, glow=0.15 + 0.5 * pulse(t, b(1573) + 0.5, 1.2))
    draw_hill_marks(fr, t, ax, a)
    draw_hill_copy(fr, t, ax, a)


def draw_hill_marks(fr, t, ax, a):
    # the peak, then a probe down both sides
    pk = a * smooth(lin(t, b(1556), b(1556) + 0.3)) * (1 - smooth(lin(t, b(1565), b(1565) + 0.4)))
    if pk > 0.003:
        fr.glow_dot(*ax.at(0, 1), 9 + 6 * pulse(t, b(1556), 0.6), "x", pk, 1.0)
        run = ease_io(lin(t, b(1559), b(1564) + 0.3))
        for s in (-1, 1):
            xv = 2.2 * s * run
            fr.glow_dot(*ax.at(xv, float(f(xv))), 7.0, "x", pk * smooth(lin(t, b(1559), b(1559) + 0.3)), 0.8)
    # "No breaks, no corners, no jumps": one lens per phrase, each with a calm curvature comb
    for k, (xv, t0, word) in enumerate(zip(LENS_X, LENS_T, LENS_W)):
        t1 = LENS_T[k + 1] if k < 2 else b(1572)
        la = a * smooth(lin(t, t0, t0 + 0.3)) * (1 - smooth(lin(t, t1 - 0.1, t1 + 0.2)))
        if la <= 0.003:
            continue
        r = 110 * ease_out(lin(t, t0, t0 + 0.35))
        center = (float(ax.px(xv)), float(ax.py(f(xv))) - 230)

        def inside(sub, xv=xv, la=la):
            HILL.original(fr, la, ax=sub, width=3.0)
            xs = np.linspace(sub.x0, sub.x1, 21)
            d1, d2 = hill_derivs(xs)
            comb(fr, sub, xs, f(xs), d1, d2, "frame", la, scale=40.0)

        HILL.loupe(fr, (xv, float(f(xv))), 4, center, max(r, 1.0), inside, la, ax=ax, label=False)
        fr.text(word, center[0], center[1] + r + 40, "sans", 28, 500, "muted", la)
    # the formula, then the series
    fa = smooth(lin(t, b(1544), b(1544) + 0.4)) * (1 - smooth(lin(t, b(1603), b(1603) + 0.4)))
    fa = max(fa, smooth(lin(t, b(1656), b(1656) + 0.4)) * (1 - smooth(lin(t, b(1683), b(1683) + 0.4))))
    typmath.draw(fr, FORMULA, 960, 120, 60, None, fa, glow=0.2)
    sa = fa * smooth(lin(t, b(1579), b(1579) + 0.3))
    if sa > 0.003:
        alphas, glows = {}, {}
        for rng, t0 in zip(R_SER, SER_T):
            u = smooth(lin(t, t0, t0 + 0.3))
            for i in rng:
                alphas[i] = u
                glows[i] = 0.7 * pulse(t, t0 + 0.3, 0.7)
        typmath.draw(fr, SER, 960, 240, 50, None, sa, alphas=alphas, glows=glows)


def draw_hill_copy(fr, t, ax, a):
    if t < SER_T[0]:
        return
    a36 = 1 - smooth(lin(t, b(1603), b(1603) + 0.4))
    if t < b(1656):
        if a36 <= 0.003:
            return
        c, _, s = HILL.chain(t, *HUG36)
        grow = ease_out(lin(t, SER_T[0], SER_T[0] + 0.6))
        HILL.error_band(fr, c, 0.5 * a * a36, ax=ax)
        HILL.copy(fr, c, a * a36, ax=ax, glow=0.6 + 0.5 * s, reveal=grow, sym=True)
        return
    # S39: P₂ … P₂₀, gold inside |x| < 1, red outside, fading as the graph tilts away
    ca = a * smooth(lin(t, b(1656), b(1656) + 0.3)) * (1 - smooth(lin(t, b(1681), b(1683))))
    c, _, s = HILL.chain(t, DEG39, HUG39)
    x1 = float(ax.px(1.0))
    x0 = float(ax.px(-1.0))
    with clip(fr, (x0, ax.top, x1 - x0, ax.rect[3])):
        HILL.copy(fr, c, ca, ax=ax, glow=0.6 + 0.5 * s)
    for rect in ((ax.left, ax.top, x0 - ax.left, ax.rect[3]), (x1, ax.top, ax.right - x1, ax.rect[3])):
        with clip(fr, rect):
            HILL.copy(fr, c, ca, ax=ax, glow=0.5, color="alert")
    # "perfectly calm": two red hairline walls at ±1
    wa = a * smooth(lin(t, b(1666), b(1666) + 0.3)) * (1 - smooth(lin(t, b(1683), b(1683) + 0.4)))
    if wa > 0.003:
        p = pulse(t, b(1668), 0.6)
        for xv in (x0, x1):
            fr.line(xv, ax.top, xv, ax.bottom, "alert", 1.4 + 1.6 * p, wa, glow=0.3 + 0.6 * p)


# ------------------------------------------------------------------ S37–S39 · the zigzag of running sums

ZX0, ZX1 = 1100.0, 1780.0
PROBE = [(b(1603), 0.5), (b(1619), 1.0), (b(1641), 1.2)]
Z37 = [b(1607) + 0.42 * k for k in range(10)]
Z38 = [b(1622), b(1623), b(1625), b(1627)]
FAST = []
_tt, _dt = b(1635), 0.34
while _tt < S39 - 0.2:
    FAST.append(_tt)
    _tt += _dt
    _dt = max(0.06, _dt * 0.82)
Z38 = Z38 + FAST
Z39 = [b(1647) + 0.38 * k for k in range(9)]
PHASES = [(0.5, Z37, S37, S38, "0.8000"), (1.0, Z38, S38, S39, "0.5000"), (1.2, Z39, S39, b(1656), "0.4098")]


def probe_x(t):
    x = 0.0
    prev = 0.0
    for t0, xv in PROBE:
        x = prev + (xv - prev) * ease_io(lin(t, t0, t0 + 0.6))
        if t < t0 + 0.6:
            return x
        prev = xv
    return prev


def sums(xv, n):
    return np.cumsum([(-(xv**2)) ** k for k in range(n)])


def step_x(i, n_fast):
    """x of step i; S38's fast steps crowd closer and closer."""
    if i < 4 or not n_fast:
        return ZX0 + 60 + 62 * i
    return ZX0 + 60 + 62 * 3 + sum(62 * 0.86 ** (j + 1) for j in range(i - 3))


def draw_zigzag(fr, t):
    if not S37 <= t < b(1656) + 0.5:
        return
    ax = hill_ax(t)
    pa = smooth(lin(t, b(1603) + 0.3, b(1603) + 0.8)) * (1 - smooth(lin(t, b(1656), b(1656) + 0.4)))
    if pa <= 0.003:
        return
    xp = probe_x(t)
    HILL.probe(fr, xp, pa, ax=ax, y=float(f(xp)), drop=True)
    for xv, times, t0, t1, target in PHASES:
        za = pa * smooth(lin(t, t0, t0 + 0.4)) * (1 - smooth(lin(t, t1 - 0.2, t1 + 0.2)))
        if za <= 0.003:
            continue
        yt = float(ax.py(f(xv)))
        # the height f(x) carried across as the target line
        fr.dashed([float(ax.px(xv)), ZX1], [yt, yt], "original", 1.4, 0.7 * za, on=9, off=7)
        typmath.draw(fr, f"f({tc('x', f'{xv:g}')}) = {f(xv):.4g}", ZX1, yt - 30, 30, "muted", za, align="right")
        S = sums(xv, len(times))
        n = sum(t >= tk for tk in times)
        n_fast = len(FAST) if xv == 1.0 else 0
        with clip(fr, (ZX0, 200.0, ZX1 - ZX0 + 40, 670.0)):
            prev = 0.0
            for i in range(n):
                g = ease_out(lin(t, times[i], times[i] + 0.25))
                x = step_x(i, n_fast)
                v0, v1 = prev, prev + (S[i] - prev) * g
                old = 1.0
                if n_fast and i >= 4:
                    old = 0.35 + 0.65 * (i >= n - 3)
                tok = "plus" if S[i] >= prev else "minus"
                fr.line(x, float(ax.py(v0)), x, float(ax.py(v1)), tok, 4.0, za * old, glow=0.4)
                if i + 1 < n:
                    fr.line(
                        x, float(ax.py(S[i])), step_x(i + 1, n_fast), float(ax.py(S[i])), "copy", 1.6, 0.7 * za * old
                    )
                prev = S[i]
            if n:
                fr.glow_dot(step_x(n - 1, n_fast), float(ax.py(prev)), 6.0, "copy", za, 0.8)
        # the readout: locks for x = 0.5, flickers and never locks for x = 1, flails for x = 1.2
        if n:
            cur = S[n - 1]
            if xv == 1.0 and b(1631) <= t < b(1632) + 0.5:
                cur = 1.0 if int((t - b(1631)) / 0.15) % 2 == 0 else 0.0
            s_txt = f"{cur:.4f}" if abs(cur) < 10 else f"{cur:.1f}"
            force = None if xv == 0.5 else 0
            g = lin(t, b(1612), b(1612) + 0.3) if xv == 0.5 else 0.0
            lock(fr, s_txt, target, (ZX0 + ZX1) / 2 + 20, 930, 60, za, glint=g, force=force)
        if xv == 0.5:  # "Exactly right": a glint where the zigzag meets the line
            fr.glint(step_x(9, 0), yt, 70, za * pulse(t, b(1615), 0.6))


# ------------------------------------------------------------------ S40 · off the graph: the camera tilts

PX_PER = 270.0
FOCAL = 1100.0
Y_C = (960 - 580) / PX_PER - 0.9  # world height at the screen centre (960, 580) of the flat stage
TILT = (b(1683), b(1686) + 0.6)


def tilt_cam(t):
    u = ease_io(lin(t, *TILT))
    elev = math.radians(62) * u
    target = (0.0, Y_C * (1 - u), 1.0 * u)
    dist = FOCAL / PX_PER * (1 + 0.45 * u)
    return orbit(target, dist, elev, 0.0, focal=FOCAL, center=(960.0, 580.0))


def poly3(fr, cam, pts, color, width, alpha, glow=0.0):
    px, py, _ = cam.project(np.asarray(pts))
    fr.poly(px, py, color, width, alpha, glow)


def draw_tilt(fr, t):
    if t < b(1668):
        return
    # the lens at x = 1: nothing strange
    la = smooth(lin(t, b(1672), b(1672) + 0.3)) * (1 - smooth(lin(t, b(1678), b(1678) + 0.4)))
    if la > 0.003:
        ax = FULL
        r = 130 * ease_out(lin(t, b(1672), b(1672) + 0.4)) * (1 - ease_io(lin(t, b(1678), b(1678) + 0.4))) + 1

        def inside(sub):
            HILL.original(fr, la, ax=sub, width=3.0)
            xs = np.linspace(sub.x0, sub.x1, 21)
            d1, d2 = hill_derivs(xs)
            comb(fr, sub, xs, f(xs), d1, d2, "frame", la, scale=40.0)

        HILL.loupe(fr, (1.0, 0.5), 5, (float(ax.px(1.0)) + 260, 330.0), r, inside, la, ax=ax, label=False)
    if t >= TILT[0]:
        draw_world(fr, t)


# ------------------------------------------------------------------ S41–S43 · the camera keeps going: the hidden towers

UNIT = 300.0  # the top-down complex plane, px per unit
PL = ComplexPlane(center=(960.0, 540.0), unit=UNIT, extent=(-3.2, 3.2, -1.8, 1.8))
FUNCS["hill_p20"] = lambda z: sum((-(z * z)) ** k for k in range(11))  # P₂₀ of the hill, in z
SIDE = ((0.0, Y_C, 0.0), FOCAL / PX_PER, 0.0, 0.0, (960.0, 580.0))
TILTED = ((0.0, 0.0, 1.0), FOCAL / PX_PER * 1.45, math.radians(62), 0.0, (960.0, 580.0))
VIEW41 = ((0.0, 0.35, 0.0), 5.6, 0.58, 0.36, (960.0, 640.0))
VIEW41B = ((0.0, 0.35, 0.0), 5.3, 0.52, 0.56, (960.0, 640.0))
TOP = ((0.0, 0.0, 0.0), FOCAL / UNIT, 1.55, 0.0, (960.0, 540.0))
PEEK = ((0.0, Y_C, 0.0), FOCAL / PX_PER * 1.7, math.radians(25), 0.45, (960.0, 600.0))
TOP_T = b(1737) + 1.6  # the camera is straight overhead: cross to the flat domain image
BACK_T = (b(1783), b(1785) + 0.6)  # "the ordinary number line": tilt back to the side view
CAM3 = [
    (TILT[1], TILTED),
    (b(1697) + 0.6, VIEW41),
    (b(1737), VIEW41B),
    (TOP_T, TOP),
    (BACK_T[0], TOP),
    (BACK_T[1], SIDE),
    (b(1833), SIDE),
    (b(1835) + 0.3, PEEK),
    (b(1838) + 0.2, SIDE),
]
CAP = 8.0
KICK = b(1723)  # 652.74, the surprise beat


def _mix_key(k0, k1, u):
    (t0, d0, e0, a0, c0), (t1, d1, e1, a1, c1) = k0, k1
    m = lambda p, q: p + (q - p) * u
    return (
        tuple(m(x, y) for x, y in zip(t0, t1)),
        m(d0, d1),
        m(e0, e1),
        m(a0, a1),
        tuple(m(x, y) for x, y in zip(c0, c1)),
    )


def cam3(t):
    if t <= TILT[1]:
        return tilt_cam(t)
    key = CAM3[-1][1]
    for (t0, k0), (t1, k1) in pairwise(CAM3):
        if t < t1:
            key = _mix_key(k0, k1, ease_io(lin(t, t0, t1)))
            break
    target, dist, elev, azim, center = key
    return orbit(target, dist, elev, azim, focal=FOCAL, center=center)


def height_scale(t):
    if t >= b(1833):
        return 0.35
    rise = back(min(1.0, lin(t, KICK - 0.9, KICK)), 1.3)
    return rise * (1.0 - 0.85 * ease_io(lin(t, b(1729) - 0.3, b(1729) + 0.7)))  # sink for "a distance of one"


@lru_cache(maxsize=4)
def _pole(hs):
    from pv3d import surfaces as S

    return S.pole_surface(hs, cap=CAP, extent=(-3.4, 3.4, -2.4, 2.4))


def surface(fr, cam, hs, alpha):
    if alpha <= 0.003:
        return
    from pv3d import surfaces as S

    from faceless_champ.draw import mesh3d as pv3

    rgba = pv3.render(
        [(_pole(round(hs, 3)), S.surface_style())], cam, pv3.frame_size(fr), cache="ch7_poles", root=PV_CACHE
    )
    pv3.composite(fr, rgba, alpha)


def disk_r(t):
    r = ease_io(lin(t, b(1753), b(1757)))
    return r + 0.15 * math.sin(math.pi * lin(t, b(1757), b(1757) + 0.5))


def draw_grid3(fr, cam, a, zr=2.4):
    for xv in np.arange(-3.0, 3.01, 0.5):
        major = abs(xv - round(xv)) < 1e-6
        tok, wd, k = ("plane_major", 1.2, 0.7) if major else ("plane_minor", 1.0, 0.5)
        poly3(fr, cam, [(xv, 0, -zr), (xv, 0, zr)], tok, wd, a * k)
    for zv in np.arange(-2.0, 2.01, 0.5):
        if abs(zv) <= zr:
            major = abs(zv - round(zv)) < 1e-6
            tok, wd, k = ("plane_major", 1.2, 0.7) if major else ("plane_minor", 1.0, 0.5)
            poly3(fr, cam, [(-3.4, 0, zv), (3.4, 0, zv)], tok, wd, a * k * (1 - smooth(lin(abs(zv), zr - 0.3, zr))))
    poly3(fr, cam, [(0, 0, -zr), (0, 0, zr)], "error", 2.0, a, glow=0.4)
    for zv, lab in ((1.0, "i"), (-1.0, f"{MINUS} i")):
        ta = a * smooth(lin(zr, abs(zv), abs(zv) + 0.3))
        px, py = proj(cam, (0.0, 0.0, zv))
        fr.line(px - 12, py, px + 12, py, "error", 2.4, ta, glow=0.5)
        typmath.draw(fr, tc("error", lab), px + 34, py - 18, 40 if zv > 0 else 30, None, ta * (1 if zv > 0 else 0.6))


def proj(cam, p):
    px, py, _ = cam.project([p])
    return float(px[0]), float(py[0])


FORMS = [
    f"f({X}) = 1 / (1 + {X}^2)",
    f"f({tc('error', 'i')}) = 1 / (1 + {tc('error', 'i')}^2)",
    f"f({tc('error', 'i')}) = 1 / (1 + ({MINUS} 1))",
    f"f({tc('error', 'i')}) = 1 / {tc('alert', '0')}",
]
FORM_T = [b(1699), b(1708), b(1715)]


def draw_world(fr, t):
    cam = cam3(t)
    a = smooth(lin(t, TILT[0], TILT[0] + 0.3))
    flat2d = smooth(lin(t, TOP_T - 0.15, TOP_T + 0.3)) * (1 - smooth(lin(t, BACK_T[0], BACK_T[0] + 0.5)))
    # the surface: rises on "explodes", sinks on "Here is the rule", peeks once in S43
    sa = smooth(lin(t, b(1721), b(1721) + 0.4)) * (1 - smooth(lin(t, TOP_T - 0.1, TOP_T + 0.2)))
    sa *= 1 - 0.4 * ease_io(lin(t, b(1737), TOP_T))  # meet the dimmer flat domain image
    peek = smooth(lin(t, b(1833), b(1833) + 0.4)) * (1 - smooth(lin(t, b(1838), b(1838) + 0.3)))
    hs = height_scale(t)
    surface(fr, cam, hs, max(sa, 0.6 * peek))
    if peek > 0.003:
        for zv in (1.0, -1.0):
            px, py = proj(cam, (0.0, min(CAP * hs, 3.2), zv))
            fr.glow_dot(px, py, 10.0, "alert", peek, 1.2)
    # the flat complex plane seen from above: f outside the circle, P₂₀ inside
    if flat2d > 0.003:
        draw_plane2d(fr, t, flat2d)
    # the 3D grid: S40 and S41 before the surface, and again during the tilt back
    ga = a * (1 - smooth(lin(t, b(1721), b(1722)))) if t < TOP_T else 0.0
    if t >= BACK_T[0]:
        ga = smooth(lin(t, BACK_T[0], BACK_T[0] + 0.4)) * (1 - smooth(lin(t, BACK_T[1] - 0.2, BACK_T[1] + 0.3)))
    if ga > 0.003:
        grid = ease_out(lin(t, b(1689) - 0.3, b(1690) + 0.6))
        draw_grid3(fr, cam, ga, 2.4 * grid)
    # the real axis and the hill as a slice along it
    ha = a * (1 - smooth(lin(t, b(1721), b(1721) + 0.4))) if t < TOP_T else smooth(lin(t, BACK_T[0] + 0.3, BACK_T[1]))
    poly3(fr, cam, [(-3.4, 0, 0), (3.4, 0, 0)], "axis", 2.0, max(ha, 0.6 * sa))
    xs = np.linspace(-3.2, 3.2, 300)
    poly3(fr, cam, np.column_stack([xs, f(xs), np.zeros_like(xs)]), "original", 2.5, ha, glow=0.15)
    if t < b(1721):
        px, py = proj(cam, (3.25, 0.0, 0.0))
        ra = a * smooth(lin(t, b(1686), b(1686) + 0.4)) * (1 - smooth(lin(t, b(1694), b(1694) + 0.4)))
        fr.text("real", px + 10, py + 34, "sans", 24, 500, "muted", ra, align="left")
    draw_walk(fr, t, cam)
    draw_side(fr, t, cam)


def draw_walk(fr, t, cam):
    """S41: the probe walks up the imaginary axis to i; the denominator becomes 0; |i| = 1."""
    if not b(1694) - 0.2 <= t < TOP_T:
        return
    wa = smooth(lin(t, b(1694) - 0.2, b(1694) + 0.2)) * (1 - smooth(lin(t, b(1737), b(1737) + 0.5)))
    z = ease_io(lin(t, b(1694), b(1701)))
    poly3(fr, cam, [(0, 0.01, 0), (0, 0.01, z)], "error", 3.0, wa * (1 - smooth(lin(t, b(1721), b(1722)))), glow=0.6)
    px, py = proj(cam, (0.0, 0.0, z))
    pa = wa * (1 - smooth(lin(t, b(1721), b(1721) + 0.3)))
    fr.glow_dot(px, py, 10 + 8 * pulse(t, b(1701), 0.6), "x", pa, 1.0)
    ia = pa * smooth(lin(t, b(1703), b(1703) + 0.3))
    typmath.draw(fr, f"{tc('error', 'i')}^2 = {MINUS} 1", px + 60, py - 70, 44, None, ia, align="left", glow=0.3)
    # the formula, step by step to a zero on the bottom
    fa = smooth(lin(t, b(1694), b(1694) + 0.4)) * (1 - smooth(lin(t, KICK + 1.2, KICK + 1.7)))
    k = sum(t >= t0 for t0 in FORM_T)
    fx = 960 - 480 * ease_io(lin(t, KICK - 0.9, KICK - 0.1))  # step aside for the towers
    if k == 0:
        typmath.draw(fr, FORMS[0], fx, 140, 60, None, fa, glow=0.2)
    else:
        m = lin(t, FORM_T[k - 1], FORM_T[k - 1] + 0.6)
        typmath.morph(fr, FORMS[k - 1], FORMS[k], m, fx, 140, 60, fa, glow=0.2 + 0.6 * pulse(t, KICK, 0.8) * (k == 3))
    # "a distance of exactly one from zero"
    for zt, t0 in ((1.0, b(1731)), (-1.0, b(1734))):
        u = ease_out(lin(t, t0, t0 + 0.6))
        if u > 0:
            da = wa
            poly3(fr, cam, [(0, 0.03, 0), (0, 0.03, zt * u)], "x", 3.0, da, glow=0.5)
            for zz in (0.0, zt * u):
                x0, y0 = proj(cam, (-0.12, 0.03, zz))
                x1, y1 = proj(cam, (0.12, 0.03, zz))
                fr.line(x0, y0, x1, y1, "x", 2.4, da)
            if zt > 0:
                lx, ly = proj(cam, (0.0, 0.03, 0.5))
                typmath.draw(
                    fr, f"abs({tc('error', 'i')}) = 1", lx + 36, ly + 8, 52, None, da * u, align="left", glow=0.4
                )


def draw_plane2d(fr, t, a):
    PL.domain(fr, "hill", 0.6 * a)
    r = disk_r(t)
    if r > 0.002:
        circle = skia.Path()
        circle.addCircle(PL.cx, PL.cy, r * UNIT)
        with clip(fr, path=circle):
            PL.domain(fr, "hill_p20", 0.75 * a)
    PL.draw(fr, 0.35 * a, labels=True)
    da = a * smooth(lin(t, b(1745), b(1745) + 0.3))
    if da > 0.003:
        fr.glow_dot(PL.cx, PL.cy, 6.0, "circle", da, 1.0)
        PL.disk(fr, max(r, 0.001), 1.0, da)
    flash = pulse(t, b(1757) + 0.1, 0.6) + pulse(t, b(1766), 0.8)
    for z in (1j, -1j):
        PL.pole(fr, z, 1.0 + 1.5 * flash, a)
    ra = a * smooth(lin(t, b(1778), b(1778) + 0.4))
    if ra > 0.003:
        x, y = PL.at(complex(math.cos(-0.6), math.sin(-0.6)))
        typmath.draw(fr, tc("circle", "R = 1"), x + 30, y + 30, 54, None, ra, align="left", glow=0.4)


def draw_side(fr, t, cam):
    """S42C–S43: back in the side view: the circle drops onto the red walls, [−1, 1] lights, the copy lives inside."""
    if t < BACK_T[0]:
        return
    u = ease_io(lin(t, *BACK_T))
    ca = smooth(lin(t, BACK_T[0], BACK_T[0] + 0.3)) * (1 - smooth(lin(t, BACK_T[1], BACK_T[1] + 0.3)))
    if ca > 0.003:
        th = np.linspace(0, 2 * np.pi, 120)
        poly3(fr, cam, np.column_stack([np.cos(th), np.full_like(th, 0.002), np.sin(th)]), "circle", 3.0, ca, glow=0.6)
    wa = smooth(lin(t, BACK_T[1] - 0.3, BACK_T[1] + 0.2))
    if wa <= 0.003:
        return
    for xv in (-1.0, 1.0):
        poly3(fr, cam, [(xv, FULL.y0, 0), (xv, FULL.y1 - 0.45, 0)], "alert", 1.4, wa, glow=0.3)
        drop = back(min(1.0, lin(t, BACK_T[1], BACK_T[1] + 0.5)), 1.4)
        yc = 0.8 * (1 - drop)
        poly3(fr, cam, [(xv, yc - 0.12, 0), (xv, yc + 0.12, 0)], "circle", 4.0, wa, glow=0.7)
    del u
    ia = smooth(lin(t, b(1794), b(1794) + 0.5))
    if ia > 0.003:
        poly3(
            fr,
            cam,
            [(-1.0, 0.0, 0), (-1.0 + 2.0 * ease_out(lin(t, b(1794), b(1796))), 0.0, 0)],
            "circle",
            6.0,
            ia,
            glow=0.8,
        )
        xs = np.linspace(-1.0, 1.0, 200)
        c = T.coeffs("hill", 20)
        poly3(fr, cam, np.column_stack([xs, T.evaluate(c, xs), np.zeros_like(xs)]), "copy", 4.0, ia, glow=0.6)
    # S43: the name, then the disk of knowledge
    na = smooth(lin(t, b(1804), b(1804) + 0.4)) * (1 - smooth(lin(t, b(1826), b(1826) + 0.5)))
    if na > 0.003:
        fr.text("radius of convergence", 960, 150, DISPLAY, 58, 600, "ink", na)
        fr.light_sweep(
            text_path("radius of convergence", 960, 150, DISPLAY, 58, 600), lin(t, b(1806), b(1806) + 0.9), 0.8 * na
        )
        typmath.draw(fr, tc("circle", "R = 1"), 960, 228, 50, None, na, glow=0.4)
    ka = smooth(lin(t, b(1816), b(1816) + 0.6)) * (1 - smooth(lin(t, b(1833), b(1833) + 0.3)))
    if ka > 0.003:
        cx, cy = proj(cam, (0.0, 0.0, 0.0))
        r = PX_PER * (1 + 0.06 * math.sin(2 * math.pi * (t - b(1826)) / 1.4) * (t >= b(1826)))
        knowledge(fr, cx, cy, r, ka)


def knowledge(fr, cx, cy, r, a):
    """A soft pink disk around 0; everything outside it dims to the non-focal level."""
    dim = skia.GradientShader.MakeRadial(
        skia.Point(cx, cy),
        r * 1.25,
        [
            skia.Color4f(0, 0, 0, 0).toColor(),
            skia.Color4f(0, 0, 0, 0).toColor(),
            skia.Color4f(0, 0, 0, 0.6 * a).toColor(),
        ],
        [0.0, 0.78, 1.0],
    )
    for c in (fr.c, fr.g):
        c.drawPaint(skia.Paint(Shader=dim))
    glow = skia.Path()
    glow.addCircle(cx, cy, r)
    fr.path_fill(glow, "circle", 0.09 * a)
    fr.path_stroke(glow, "circle", 2.0, 0.7 * a, glow=0.6)


# ------------------------------------------------------------------ assembly


def draw_handoff(fr, t):
    a = 1 - smooth(lin(t, START, START + 0.7))
    if a > 0.003:
        with layer_alpha(fr, a):
            ch6.draw_pendulums(fr, t)


def draw_one(t, size):
    fr = Frame(size)
    draw_handoff(fr, t)
    draw_lanes(fr, t)
    draw_hill(fr, t)
    draw_zigzag(fr, t)
    k = math.exp(-max(0.0, t - KICK) / 0.25) * (t >= KICK - 0.02)
    if k > 0.01:
        dx, dy, roll = noise.shake(t, 14.0 * k, 9.0, rotation=0.6 * k, seed=5)
        for c in (fr.c, fr.g):
            c.save()
            c.translate(960 + dx, 540 + dy)
            c.rotate(roll)
            c.translate(-960, -540)
        draw_tilt(fr, t)
        for c in (fr.c, fr.g):
            c.restore()
    else:
        draw_tilt(fr, t)
    fr.chroma(chroma_kick(t, KICK, 9.0, 0.35))
    hud.eyebrow(fr, t, "07 · WHERE IT BREAKS", START + 0.2)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch7:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=END - START, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(END - START)
        if audio:
            scene.add_audio(AUDIO, start=0, trim_start=START)
    return scene


SCENES = {
    "S35": (S35, S36, [573.9, 578.9, 581.6]),
    "S36": (S36, S37, [584.9, 592.5, 602.3]),
    "S37": (S37, S38, [606.2, 609.4]),
    "S38": (S38, S39, [614.3, 618.0, 620.4]),
    "S39": (S39, S40, [624.8, 628.2, 631.4]),
    "S40": (S40, S41, [634.6, 638.4, 640.6]),
    "S41": (S41, S42, [645.2, 650.9, 653.4, 657.6]),
    "S42": (S42, S43, [662.4, 666.2, 670.0, 675.4, 678.9]),
    "S43": (S43, END, [681.8, 686.4, 691.9]),
}
OFFSET = START
DURATION = END - START
STILLS = [s for _, _, st in SCENES.values() for s in st]
