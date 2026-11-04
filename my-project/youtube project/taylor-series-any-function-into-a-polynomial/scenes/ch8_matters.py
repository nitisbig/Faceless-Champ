"""CHAPTER 8 · WHY IT MATTERS, 11:33.000 – 12:28.080 (cue #1839 "Once" → #2004 "So").

S44  Everywhere           three open fields, no frames: √(1 + x) and its gold tangent 1 + x/2 (linearize) -> a unit arrow
                          turning on a pink ring, cos and sin from degree-7 polynomials, its tip trailing a wave (rotate)
                          -> the third field grows to full frame: a PyVista loss landscape, a blue point, the gold
                          second-order bowl snaps on, the point drops to its bottom (a Newton step), a new bowl, a second step
S45  Einstein's series    E = -> m c² -> m c² / √(1 − v²/c²) -> a muted ghost ½ m v² far right -> the root unrolls into
                          m c² (1 + ½ v²/c² + ⅜ v⁴/c⁴ + ⋯) -> E ≈ m c² + ½ m v² + ⋯, the second term gold, the ghost lands on it
S46  Newton was not wrong m c² glints (rest energy), ½ m v² (kinetic energy) -> kinetic energy against v/c: the exact curve
                          and Newton's parabola hug at low speed (0.76 % apart at 0.1 c) and part near c -> + ⅜ m v⁴/c² + ⋯
                          fades in muted, a light sweep

Clean frame: no cards, pills or panels. The loss landscape is an illustration (seeded bumps, no values shown); the
Newton steps, the bowl (finite-difference Hessian) and the 0.76 % are computed.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
from components import taylor as T
from components.fx import layer_alpha
from components.stage import Axes
from cues import AUDIO, beat, cue
from theme import PV_CACHE, THEME, TOKENS, H, W

from faceless_champ.draw import Frame, back, ease_io, ease_out, hud, lin, pulse, smooth
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc
from faceless_champ.draw.space import orbit
from scenes import ch7_breaks as ch7

START = cue(1839)  # 693.00 "Once you know this trick"
END = cue(2004)  # 748.08 "So let's look back" (Chapter 9)

b = beat

S44, S45, S46 = START, cue(1897), cue(1968)

X = tc("x", "x")
V = tc("x", "v")


def term_box(expr, hexcol, cx, cy, size):
    """Design-px bounds (l, t, r, b) of the glyphs drawn in ``hexcol`` and their indices."""
    gs, _ = typmath.glyphs(expr)
    k = size / typmath.BASE
    idx = [i for i, g in enumerate(gs) if g.color.lower() == hexcol.lower()]
    boxes = [gs[i].path.computeTightBounds() for i in idx]
    l, t = min(r.left() for r in boxes), min(r.top() for r in boxes)
    r_, b_ = max(r.right() for r in boxes), max(r.bottom() for r in boxes)
    return (cx + l * k, cy + t * k, cx + r_ * k, cy + b_ * k), idx


def outline(expr, cx, cy, size):
    """The glyph outlines of a formula as one path, for light sweeps that touch only the ink."""
    gs, _ = typmath.glyphs(expr)
    k = size / typmath.BASE
    m = skia.Matrix.Translate(cx, cy)
    m.preScale(k, k)
    p = skia.Path()
    for g in gs:
        p.addPath(g.path, m)
    return p


# ------------------------------------------------------------------ S44 · three fields

FIELD_X = [340.0, 960.0, 1580.0]
FIELD_T = [b(1849), b(1862), b(1873)]
CAPTIONS = ["linearize", "rotate", "optimize"]
AX1 = Axes(-1.0, 3.0, -0.25, 2.25, (120.0, 300.0, 440.0, 330.0))


def field_alpha(t, i):
    a = smooth(lin(t, FIELD_T[i] - 0.2, FIELD_T[i] + 0.4))
    if i < 2:
        a *= 1 - smooth(lin(t, b(1873) + 0.3, b(1873) + 1.0))
    return a


def draw_sparks(fr, t):
    """ "you start seeing it everywhere": three gold sparks mark where the fields will open."""
    a = smooth(lin(t, b(1846), b(1846) + 0.5)) * (1 - smooth(lin(t, b(1849), b(1849) + 0.6)))
    for i, x in enumerate(FIELD_X):
        u = ease_out(lin(t, b(1846) + 0.18 * i, b(1846) + 0.18 * i + 0.5))
        if u > 0:
            fr.glow_dot(x, 470, 4 + 6 * pulse(t, b(1848) + 0.12 * i, 0.6), "copy", a * u, 1.2)


def draw_field1(fr, t):
    a = field_alpha(t, 0)
    if a <= 0.003:
        return
    ax = AX1
    fr.line(ax.left, ax.py(0), ax.right, ax.py(0), "axis", 1.6, a)
    fr.line(ax.px(0), ax.top + 20, ax.px(0), ax.bottom, "axis", 1.2, 0.6 * a)
    rv = ease_io(lin(t, FIELD_T[0], FIELD_T[0] + 1.0))
    xs = np.linspace(-1.0, -1.0 + 4.0 * rv, 240)
    fr.poly(ax.px(xs), ax.py(np.sqrt(1 + xs)), "original", 2.5, a)
    g = ease_out(lin(t, b(1852), b(1852) + 0.8))  # "first few terms": the tangent grows out of x = 0
    if g > 0:
        xs = np.linspace(-0.9 * g, 2.3 * g, 80)
        fr.poly(ax.px(xs), ax.py(1 + xs / 2), "copy", 4.0, a, glow=0.5 + 0.6 * pulse(t, b(1857), 0.8))
        fr.glow_dot(*ax.at(0, 1), 6, "copy", a, 1.0)
    f0 = f"sqrt(1 + {X})"
    f1 = f"sqrt(1 + {X}) approx {tc('copy', '1 + x/2')}"
    m = ease_io(lin(t, b(1857), b(1857) + 0.7))
    typmath.morph(fr, f0, f1, m, FIELD_X[0], 720, 46, a * smooth(lin(t, FIELD_T[0] + 0.3, FIELD_T[0] + 0.8)))


def sin7(th):
    """sin and cos the way a game engine might: fold the angle into [−π/2, π/2], then degree-7 polynomials."""
    th = (th + math.pi) % (2 * math.pi) - math.pi
    s_th = math.pi - th if th > math.pi / 2 else (-math.pi - th if th < -math.pi / 2 else th)
    c_th = th - math.pi / 2  # cos θ = −sin(θ − π/2)
    c_th = (c_th + math.pi) % (2 * math.pi) - math.pi
    c_th = math.pi - c_th if c_th > math.pi / 2 else (-math.pi - c_th if c_th < -math.pi / 2 else c_th)
    s = float(T.evaluate(SIN7, np.array([s_th]))[0])
    c = -float(T.evaluate(SIN7, np.array([c_th]))[0])
    return c, s


SIN7 = T.coeffs("sin", 7)
RING_C, RING_R = (830.0, 470.0), 112.0
OMEGA = 2.6  # rad/s


def angle(t):
    return OMEGA * max(0.0, t - FIELD_T[1])


def draw_field2(fr, t):
    a = field_alpha(t, 1)
    if a <= 0.003:
        return
    cx, cy = RING_C
    ru = ease_out(lin(t, FIELD_T[1], FIELD_T[1] + 0.6))
    fr.circle(cx, cy, RING_R * ru, "circle", 2.4, a, glow=0.4)
    fr.line(cx - RING_R - 20, cy, cx + RING_R + 20, cy, "axis", 1.2, 0.6 * a)
    c, s = sin7(angle(t))
    tx, ty = cx + RING_R * ru * c, cy - RING_R * ru * s
    fr.line(cx, cy, tx, ty, "x", 3.0, a, glow=0.3)
    fr.glow_dot(tx, ty, 7, "x", a, 1.0)
    w = smooth(lin(t, b(1869), b(1869) + 0.5))  # "waves": the tip's height trails off to the right as a wave
    if w > 0.003:
        x0 = cx + RING_R + 50
        taus = np.linspace(0.0, 1.6, 120)
        ys = [cy - RING_R * sin7(angle(t - tau))[1] for tau in taus]
        xs = x0 + taus * 170
        keep = t - taus >= FIELD_T[1]
        fr.poly(xs[keep], np.asarray(ys)[keep], "copy", 3.0, a * w, glow=0.4)
        fr.line(tx, ty, x0, ys[0], "copy", 1.0, 0.35 * a * w)
    series = f"sin {X} approx {X} - {X}^3/3! + {X}^5/5! - {X}^7/7!"
    typmath.draw(fr, series, FIELD_X[1], 720, 34, None, a * smooth(lin(t, b(1865), b(1865) + 0.5)), glow=0.1)


# --- field 3: the loss landscape (PyVista)

SC = 1.7  # height scale of the illustration
P0 = np.array([1.2, -1.8])


def newton(p):
    from pv3d import surfaces as S

    _, g, Hm = S.hessian(tuple(p))
    return p - np.linalg.solve(Hm, g)


P1 = newton(P0)
P2 = newton(P1)
BOWL_T = (b(1884), b(1894) + 0.1)  # the first bowl snaps on; the second forms at the new point
STEP_T = [(b(1892), b(1892) + 0.8), (b(1895) - 0.1, b(1895) + 0.5)]


def quad(p, q):
    from pv3d import surfaces as S

    f0, g, Hm = S.hessian(tuple(p))
    d = np.asarray(q) - p
    return f0 + g @ d + 0.5 * d @ Hm @ d


def point(t):
    """The parameter point (x, y) and its height: on the surface, or riding the bowl while it steps."""
    from pv3d import surfaces as S

    for (t0, t1), p, q in ((STEP_T[0], P0, P1), (STEP_T[1], P1, P2)):
        if t0 <= t < t1:
            u = ease_io(lin(t, t0, t1))
            r = p + (q - p) * u
            return r, quad(p, r) + 0.08
    p = P0 if t < STEP_T[0][1] else (P1 if t < STEP_T[1][1] else P2)
    return p, float(S.loss(*p))


def loss_cam(t):
    u = ease_io(lin(t, FIELD_T[2] + 0.4, FIELD_T[2] + 1.8))
    dist = 30.0 + (7.4 - 30.0) * u
    center = (FIELD_X[2] + (960.0 - FIELD_X[2]) * u, 470.0 + 80.0 * u)
    azim = -0.62 + 0.035 * (t - FIELD_T[2])
    return orbit((0.55, 0.45, -0.9), dist, 0.6, azim, focal=1150.0, center=center)


@lru_cache(maxsize=2)
def _loss_mesh():
    from pv3d import surfaces as S

    return S.loss_surface(scale=SC)


@lru_cache(maxsize=8)
def _bowl(i, r):
    from pv3d import surfaces as S

    return S.hessian_bowl(tuple((P0, P1)[i]), radius=r, scale=SC, lift=0.05)


def draw_field3(fr, t):
    a = field_alpha(t, 2) * (1 - smooth(lin(t, S45 - 0.2, S45 + 0.5)))
    if a <= 0.003:
        return
    from faceless_champ.draw import mesh3d as pv3

    cam = loss_cam(t)
    size = pv3.frame_size(fr)
    rgba = pv3.render([(_loss_mesh(), pv3.gloss("#3A4C70"))], cam, size, cache="ch8_loss", root=PV_CACHE)
    pv3.composite(fr, rgba, a)
    for i, t0 in enumerate(BOWL_T):
        ba = smooth(lin(t, t0, t0 + 0.3)) * (1 - smooth(lin(t, BOWL_T[1], BOWL_T[1] + 0.4)) if i == 0 else 1.0)
        if ba <= 0.003:
            continue
        r = round(0.25 + 0.95 * back(min(1.0, lin(t, t0, t0 + 0.45)), 1.4), 2)
        style = pv3.glass("copy", opacity=0.6, smooth_shading=True)
        rgba = pv3.render([(_bowl(i, r), style)], cam, size, cache="ch8_bowl", root=PV_CACHE)
        pv3.composite(fr, rgba, a * ba)
    # the trail of steps and the point
    p, h = point(t)
    trail = [P0] + [q for (t0, _), q in zip(STEP_T, (P1, P2)) if t >= t0]
    if len(trail) > 1:
        from pv3d import surfaces as S

        pts = [(q[0], float(S.loss(*q)) * SC + 0.04, q[1]) for q in trail[:-1]] + [(p[0], h * SC + 0.04, p[1])]
        xs, ys, _ = cam.project(np.asarray(pts))
        fr.dashed(xs, ys, "copy", 2.0, 0.8 * a, glow=0.4, on=8, off=6)
    xs, ys, _ = cam.project(np.array([[p[0], h * SC + 0.04, p[1]]]))
    fr.glow_dot(float(xs[0]), float(ys[0]), 9, "x", a, 1.2)


def draw_captions(fr, t):
    for i, (x, s) in enumerate(zip(FIELD_X, CAPTIONS)):
        ca = field_alpha(t, i) * smooth(lin(t, FIELD_T[i] + 0.5, FIELD_T[i] + 1.0))
        if i == 2:
            ca *= 1 - smooth(lin(t, FIELD_T[2] + 0.3, FIELD_T[2] + 0.8))
        fr.text(s.upper(), x, 800, "sans", 20, 700, "muted", ca, tracking=0.24)


# ------------------------------------------------------------------ S45–S46 · Einstein

HEX = TOKENS
REST = tc("light", "m c^2")
KIN = tc("copy", f"1/2 m {V}^2")
NEXT = tc("muted", f"3/8 (m {V}^4)/c^2")
E0 = "E ="
E1 = "E = m c^2"
E2 = f"E = (m c^2) / sqrt(1 - {V}^2 / c^2)"
E3 = f"E = m c^2 (1 + 1/2 {V}^2/c^2 + 3/8 {V}^4/c^4 + dots.c)"
E4 = f"E approx {REST} + 1/2 m {V}^2 + dots.c"
E4G = f"E approx {REST} + {KIN} + dots.c"
E5 = f"E approx {REST} + {KIN} + {NEXT} + dots.c"
GHOST = f"1/2 m {V}^2"
CHAIN = [(E0, b(1910)), (E1, b(1917)), (E2, b(1924)), (E3, b(1945)), (E4, b(1960))]
FY, FS = 470.0, 92.0  # S45 formula
UP_T = b(1988)  # "Newton's formula": the formula rises to make room for the plot
UY, US = 200.0, 70.0
GHOST_AT = (1560.0, 800.0, 64.0)
LAND_T = (b(1965), cue(1967) + 0.1)


def formula_pos(t):
    u = ease_io(lin(t, UP_T, UP_T + 0.8))
    return FY + (UY - FY) * u, FS + (US - FS) * u


def draw_formula(fr, t):
    a = smooth(lin(t, CHAIN[0][1] - 0.1, CHAIN[0][1] + 0.4)) * (1 - smooth(lin(t, END - 0.6, END)))
    if a <= 0.003:
        return
    cy, size = formula_pos(t)
    if t >= b(1997):  # "first useful term of a deeper series"
        u = ease_io(lin(t, b(1997), b(1997) + 0.9))
        typmath.morph(fr, E4G, E5, u, 960, cy, size, a, glow=0.15)
        fr.light_sweep(outline(E5, 960, cy, size), lin(t, b(2001), b(2001) + 1.1), 0.6 * a)
        return
    k = sum(t >= t0 for _, t0 in CHAIN)
    if k <= 1:
        typmath.draw(fr, CHAIN[0][0], 960, cy, size, None, a)
        return
    t0 = CHAIN[k - 1][1]
    dur = 1.2 if k in (3, 4) else 0.7
    u = ease_io(lin(t, t0, t0 + dur))
    if k < len(CHAIN) or u < 1:
        typmath.morph(fr, CHAIN[k - 2][0], CHAIN[k - 1][0], u, 960, cy, size, a, glow=0.1)
        return
    # E ≈ m c² + ½ m v² + ⋯ : the kinetic term turns gold as the ghost lands on it
    g = smooth(lin(t, b(1964), b(1964) + 0.4))
    land = pulse(t, LAND_T[1], 0.9)
    _, idx = term_box(E4G, HEX["copy"], 960, cy, size)
    typmath.draw(
        fr,
        E4,
        960,
        cy,
        size,
        None,
        a,
        glow=0.1,
        colors=dict.fromkeys(idx, "copy") if g > 0.5 else None,
        glows=dict.fromkeys(idx, 0.3 + 0.9 * land) if g > 0.5 else None,
    )
    if t >= b(1973):
        draw_labels(fr, t, cy, size, a)


def draw_mover(fr, t):
    """ "one of the most famous examples": a blue object glides across, trailing light, until E = sets."""
    a = smooth(lin(t, S45 + 0.2, S45 + 0.8)) * (1 - smooth(lin(t, b(1910) - 0.3, b(1910) + 0.4)))
    if a <= 0.003:
        return
    u = lin(t, S45, b(1910) + 0.4)
    x = 300 + 1320 * ease_io(u)
    trail = np.linspace(0.0, 1.0, 40)
    xs = x - trail * 380 * (0.3 + 0.7 * math.sin(math.pi * u))
    fr.poly(xs, np.full_like(xs, FY + 150), "x", 2.0, 0.35 * a, glow=0.5)
    fr.glow_dot(x, FY + 150, 8, "x", a, 1.2)


def draw_ghost(fr, t):
    a = smooth(lin(t, b(1936), b(1936) + 0.6))
    if a <= 0.003 or t > LAND_T[1] + 0.05:
        return
    gx, gy, gs = GHOST_AT
    u = ease_io(lin(t, *LAND_T))
    cy, size = formula_pos(t)
    (l, tp, r, bt), _ = term_box(E4G, HEX["copy"], 960, cy, size)
    tx, ty = (l + r) / 2, (tp + bt) / 2
    x = gx + (tx - gx) * u
    y = gy + (ty - gy) * u - 160 * math.sin(math.pi * u)
    s = gs + (size - gs) * u
    col = "muted" if u < 0.5 else "copy"
    typmath.draw(fr, GHOST, x, y, s, col, a * (0.55 + 0.45 * u), glow=0.5 * u)


def draw_labels(fr, t, cy, size, a):
    (l, tp, r, bt), _ = term_box(E4G, HEX["light"], 960, cy, size)
    ra = a * smooth(lin(t, b(1973), b(1973) + 0.5))
    fr.glint((l + r) / 2 + 30, (tp + bt) / 2 - 10, 90, ra * pulse(t, b(1974), 1.2))
    fr.text("REST ENERGY", (l + r) / 2, bt + 54, "sans", 20, 700, "muted", ra, tracking=0.24)
    (l, tp, r, bt), _ = term_box(E4G, HEX["copy"], 960, cy, size)
    ka = a * smooth(lin(t, b(1983), b(1983) + 0.5))
    fr.text("KINETIC ENERGY", (l + r) / 2, bt + 54, "sans", 20, 700, "copy", ka, tracking=0.24)


# --- the plot: kinetic energy against v/c

AXP = Axes(0.0, 1.0, 0.0, 2.2, (440.0, 430.0, 1040.0, 470.0))
BETA = np.linspace(0.0, 0.995, 600)
EXACT = 1 / np.sqrt(1 - BETA**2) - 1
NEWTON = BETA**2 / 2
GAP_01 = ((1 / math.sqrt(1 - 0.01) - 1) / 0.005 - 1) * 100  # 0.76 %


def draw_plot(fr, t):
    a = smooth(lin(t, UP_T + 0.3, UP_T + 0.8)) * (1 - smooth(lin(t, END - 0.6, END)))
    if a <= 0.003:
        return
    ax = AXP
    fr.line(ax.left, ax.bottom, ax.right + 30, ax.bottom, "axis", 2.0, a)
    fr.line(ax.left, ax.bottom, ax.left, ax.top, "axis", 1.4, 0.6 * a)
    fr.dashed([ax.px(1.0)] * 2, [ax.bottom, ax.top], "muted", 1.4, 0.6 * a)
    typmath.draw(fr, "c", ax.px(1.0), ax.bottom + 34, 34, "muted", a)
    typmath.draw(fr, f"{V}", ax.right + 60, ax.bottom, 36, None, a)
    typmath.draw(fr, "0", ax.left, ax.bottom + 34, 28, "muted", a)
    rv = ease_io(lin(t, UP_T + 0.5, UP_T + 2.0))
    n = max(2, int(len(BETA) * rv))
    keep = EXACT[:n] <= ax.y1
    gap = smooth(lin(t, b(1993), b(1993) + 0.8))  # the gap opens near c
    if gap > 0.003:
        m = (BETA[:n] > 0.35) & keep
        if m.sum() > 2:
            p = skia.Path()
            xs, y1, y0 = ax.px(BETA[:n][m]), ax.py(EXACT[:n][m]), ax.py(NEWTON[:n][m])
            p.moveTo(xs[0], y0[0])
            for x, y in zip(xs, y0):
                p.lineTo(x, y)
            for x, y in zip(xs[::-1], y1[::-1]):
                p.lineTo(x, y)
            p.close()
            fr.path_fill(p, "error", 0.22 * a * gap)
    fr.poly(ax.px(BETA[:n][keep]), ax.py(EXACT[:n][keep]), "original", 2.6, a)
    fr.poly(ax.px(BETA[:n]), ax.py(NEWTON[:n]), "copy", 4.0, a, glow=0.5)
    # the probe at 0.1 c: they agree to within 0.76 %
    pa = a * smooth(lin(t, b(1990), b(1990) + 0.4))
    if pa > 0.003:
        x, y = ax.at(0.1, 0.0)
        fr.glow_dot(x, y, 7, "x", pa, 1.0)
        fr.dashed([x, x], [y, ax.py(0.6)], "x", 1.4, 0.6 * pa)
        fr.text(f"{GAP_01:.2f} % apart at 0.1 c", x + 14, ax.py(0.6) - 20, "sans", 26, 500, "ink", pa, align="left")


# ------------------------------------------------------------------ assembly


def draw_handoff(fr, t):
    a = 1 - smooth(lin(t, START, START + 0.9))
    if a > 0.003:
        with layer_alpha(fr, a):
            ch7.draw_tilt(fr, t)


def draw_one(t, size):
    fr = Frame(size)
    draw_handoff(fr, t)
    if t < S45 + 0.6:
        draw_sparks(fr, t)
        draw_field3(fr, t)
        draw_field1(fr, t)
        draw_field2(fr, t)
        draw_captions(fr, t)
    if t >= S45 - 0.2:
        draw_mover(fr, t)
        draw_formula(fr, t)
        draw_ghost(fr, t)
        draw_plot(fr, t)
    hud.eyebrow(fr, t, "08 · WHY IT MATTERS", START + 0.2)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch8:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=END - START, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(END - START)
        if audio:
            scene.add_audio(AUDIO, start=0, trim_start=START)
    return scene


SCENES = {
    "S44": (S44, S45, [695.9, 698.9, 702.6, 706.0, 709.4, 711.8]),
    "S45": (S45, S46, [718.9, 721.5, 723.9, 726.0, 729.4, 732.4, 734.4]),
    "S46": (S46, END, [737.4, 740.6, 743.4, 745.0, 747.2]),
}
OFFSET = START
DURATION = END - START
STILLS = [s for _, _, st in SCENES.values() for s in st]
