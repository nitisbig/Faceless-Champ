"""CHAPTER 1 · WHY POLYNOMIALS, 01:20.840 – 02:12.880 (cue #218 "Start" → #371 "Let's").

S07  What a computer finds easy   the blue dot left by the title push becomes x -> x × x fuses into x² -> 3x² −
                                  2x + 5 builds term by term -> products glow magenta, signs orange/teal -> the
                                  formula lifts, a parabola appears and a blue probe sweeps it in 0.8 s
S08  Friendly functions           the graph opens up -> a tangent glides (p′ = 6x − 2) -> the area fills blue
                                  (x³ − x² + 5x) -> the camera pulls very wide, a light sweep runs the curve
S09  Circles, growth and areas    three open fields, no frames: a pink circle spins out a sine wave; eˣ with its
                                  tangent triangle (run 1, rise = height); the area under 1/t -> one light sweep
                                  -> the Chip rises, the circle is thrown at it and bounces off
S10  The impostor plan            ink sin x draws -> a gold P₃ materializes above and glides down onto it -> light
                                  sweep -> the violet error band blooms where the disguise fails

Clean frame: no pills, cards, panels or slider boxes. Formulas are Typst, colored by role; the rest is geometry.
One FunctionSource on the narration clock; beats land 0.15 s before their word cue (cues.beat).
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import skia
from components import taylor as T
from components.chip import Chip
from components.fx import glow_path
from components.stage import Axes, TaylorStage, clip, curve_path
from cues import AUDIO, beat, cue
from theme import THEME, H, W

from faceless_champ.draw import Frame, back, ease_io, ease_out, hud, lin, pulse, smooth
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc

START = cue(218)  # 80.84 "Start with what a computer finds easy."
END = cue(371)  # 132.88 "Let's start with the simplest smooth curve"

b = beat

S07, S08, S09, S10 = START, cue(273), cue(302), cue(338)  # 80.84, 100.00, 109.40, 121.68

X = tc("x", "x")
MINUS, PLUS = tc("minus", "-"), tc("plus", "+")
FORMULAS = [  # (when it lands, expression): each morphs out of the one before
    (b(227), X),  # "number X"
    (b(229), f"{X} {tc('fact', 'times')} {X}"),  # "multiply it by itself"
    (b(232), f"{X}^2"),  # "itself": the pair fuses
    (b(236), f"3 {X}^2"),  # "constant"
    (b(239), f"3 {X}^2 {MINUS} 2 {X}"),  # "a few"
    (b(242), f"3 {X}^2 {MINUS} 2 {X} {PLUS} 5"),  # "together"
]
POLY = FORMULAS[-1][1]
TERMS = [(b(243), (0, 1, 2)), (b(245), (3, 4, 5)), (b(247), (6, 7))]  # glyphs of 3x² · −2x · +5
PRODUCTS = {0: "ink", 1: "x", 2: "ink", 4: "ink", 5: "x"}  # the implied multiplications
SIGNS = (3, 6)
MORPH = 0.5


def p(x):
    return 3 * x * x - 2 * x + 5


def dp(x):
    return 6 * x - 2


# ------------------------------------------------------------------ the graph of p (S07C → S08)

GRAPH_SMALL = Axes(-2.4, 2.4, -2.0, 24.0, (430.0, 300.0, 1060.0, 690.0))
GRAPH = Axes(-2.5, 2.5, -2.0, 24.0, (160.0, 150.0, 1600.0, 820.0))
GRAPH_WIDE = Axes(-9.0, 9.0, -30.0, 300.0, (96.0, 96.0, 1728.0, 888.0))
PROBE = TaylorStage("cos")  # only its probe marker is used
DERIV = f"p'({X}) = 6 {X} {MINUS} 2"
AREA = f"integral_0^{X} p = {X}^3 {MINUS} {X}^2 {PLUS} 5 {X}"


def graph_ax(t):
    ax = GRAPH_SMALL.lerp(GRAPH, ease_io(lin(t, b(273), b(281))))
    return ax.lerp(GRAPH_WIDE, ease_io(lin(t, b(295), b(299) + 0.4)))


def axes_lines(fr, ax, alpha, color="axis"):
    if alpha <= 0.003:
        return
    with clip(fr, ax.rect):
        y0, x0 = float(ax.py(0.0)), float(ax.px(0.0))
        fr.line(ax.left, y0, ax.right, y0, color, 2.0, alpha)
        fr.line(x0, ax.top, x0, ax.bottom, color, 2.0, alpha)


def parabola_path(ax):
    xs = np.linspace(ax.x0, ax.x1, 400)
    return curve_path(ax, xs, p(xs))


def probe_x(t):
    if t < b(272):
        return 0.5 + (-2.0 - 0.5) * ease_io(lin(t, b(266), b(271)))
    return -2.0 + 4.0 * ease_io(lin(t, b(272), b(272) + 0.8))  # "instantly": the whole sweep in 0.8 s


def draw_graph(fr, t):
    a = smooth(lin(t, b(265), b(265) + 0.6)) * (1 - smooth(lin(t, b(302) - 0.1, b(302) + 0.4)))
    if a <= 0.003:
        return
    ax = graph_ax(t)
    axes_lines(fr, ax, a * 0.9)
    # area under p from 0 to x (S08, "areas under them")
    xa = 1.7 * ease_io(lin(t, b(287), b(293)))
    area_a = a * smooth(lin(t, b(287), b(287) + 0.3)) * (1 - smooth(lin(t, b(295), b(295) + 0.5)))
    if area_a > 0.003 and xa > 1e-3:
        xs = np.linspace(0.0, xa, 120)
        region = skia.Path()
        region.moveTo(float(ax.px(0.0)), float(ax.py(0.0)))
        for x, y in zip(ax.px(xs), ax.py(p(xs))):
            region.lineTo(float(x), float(y))
        region.lineTo(float(ax.px(xa)), float(ax.py(0.0)))
        region.close()
        fr.path_fill(region, "x", area_a * 0.24)
        fr.line(float(ax.px(xa)), float(ax.py(0.0)), float(ax.px(xa)), float(ax.py(p(xa))), "x", 2.0, area_a, glow=0.5)
    path = parabola_path(ax)
    with clip(fr, ax.rect):
        fr.path_stroke(path, "original", 2.5, a, glow=0.15)
    fr.light_sweep(glow_path(path, 14), lin(t, b(300), b(300) + 1.1), 0.7, width=0.12)
    # S07C: the probe rides the curve; the readout is the value itself, no label, no box
    pa = a * smooth(lin(t, b(265) + 0.3, b(265) + 0.8)) * (1 - smooth(lin(t, b(273), b(273) + 0.4)))
    if pa > 0.003:
        x = probe_x(t)
        PROBE.probe(fr, x, pa, ax=ax, y=p(x))
        hud.tabular(fr, f"{p(x):.2f}", float(ax.px(x)) + 26, float(ax.py(p(x))) - 26, 36, "ink", pa, align="left")
    # S08: the tangent glides along the curve ("slopes")
    ta = a * smooth(lin(t, b(281), b(281) + 0.3)) * (1 - smooth(lin(t, b(287), b(287) + 0.4)))
    if ta > 0.003:
        x = -1.6 + 3.0 * ease_io(lin(t, b(281), b(281) + 1.6))
        cx, cy = float(ax.px(x)), float(ax.py(p(x)))
        dx, dy = ax.sx, -dp(x) * ax.sy
        n = math.hypot(dx, dy)
        ux, uy = 210 * dx / n, 210 * dy / n
        fr.line(cx - ux, cy - uy, cx + ux, cy + uy, "light", 2.2, ta, glow=0.4)
        fr.glow_dot(cx, cy, 6.0, "light", ta, 0.9)
    # S08: p′ sets, then becomes the area formula
    fa = smooth(lin(t, b(281) + 0.2, b(281) + 0.6)) * (1 - smooth(lin(t, b(295), b(295) + 0.4)))
    if fa > 0.003:
        typmath.morph(fr, DERIV, AREA, lin(t, b(287), b(287) + 0.6), 960, 250, 60, fa)


# ------------------------------------------------------------------ S07: building a polynomial


def formula_place(t):
    """(y, size): centre stage while it builds, then up out of the graph's way ("any X")."""
    u = ease_io(lin(t, b(265), b(265) + 0.7))
    return 540 - 340 * u, 132 - 48 * u


def draw_s07(fr, t):
    if t >= S08 + 0.5:
        return
    out = 1 - smooth(lin(t, b(273), b(273) + 0.4))
    # the blue dot the title push left behind drifts to centre and becomes x
    born = lin(t, FORMULAS[0][0], FORMULAS[0][0] + 0.45)
    if born < 1:
        u = ease_io(lin(t, START, FORMULAS[0][0]))
        r = 9.0 * (1 + 0.12 * math.sin(2 * math.pi * (t - START) / 1.3)) * (1 - born)
        fr.glow_dot(960, 650 - 110 * u, r, "x", 1 - born, 1.0)
    y, size = formula_place(t)
    k = max(i for i, (t0, _) in enumerate(FORMULAS) if t >= t0) if t >= FORMULAS[0][0] else -1
    if k < 0:
        return
    t0, expr = FORMULAS[k]
    u = lin(t, t0, t0 + MORPH)
    if k == 0:
        s = back(ease_out(born)) if born < 1 else 1.0
        typmath.draw(fr, expr, 960, y, size * max(0.05, 0.4 + 0.6 * s), None, smooth(born) * out, glow=0.3)
    elif u < 1:
        typmath.morph(fr, FORMULAS[k - 1][1], expr, u, 960, y, size, out, glow=0.2)
    else:
        colors, glows = {}, {}
        if expr == POLY:
            for t1, idx in TERMS:  # 3x², −2x, +5 set one by one
                for i in idx:
                    glows[i] = 1.1 * pulse(t, t1, 0.8)
            m = pulse(t, b(259), 1.3)  # "multiplying": the hidden products glow magenta
            for i, tok in PRODUCTS.items():
                if m > 0:
                    colors[i] = fr.mix(tok, "fact", m)
                    glows[i] = max(glows.get(i, 0), 0.9 * m)
            for i in SIGNS:  # "adding"
                glows[i] = max(glows.get(i, 0), 1.2 * pulse(t, b(261), 1.0))
        typmath.draw(fr, expr, 960, y, size, None, out, glow=0.2, colors=colors, glows=glows)
    # × sparks: the meeting, then the fusion
    for ts, idx in ((b(231), 1), (b(232), None)):
        sp = pulse(t, ts, 0.45)
        if sp > 0:
            if idx is None:
                gx, gy = 960, y
            else:
                gx, gy = typmath.glyph_centers(FORMULAS[1][1], 960, y, size)[idx]
            fr.glow_dot(gx, gy, 6 + 18 * sp, "fact", 0.8 * sp, 1.0)
    # "polynomial": a gold line draws under it (gold means polynomial for the rest of the film)
    if t >= b(252):
        w, h = typmath.size_of(POLY, size)
        ul = ease_out(lin(t, b(252), b(252) + 0.6))
        line = skia.Path()
        line.moveTo(960 - w / 2, y + h * 0.62)
        line.lineTo(960 - w / 2 + w * ul, y + h * 0.62)
        fr.path_stroke(line, "copy", 3.0, 0.85 * out, glow=0.6)
        fr.light_sweep(glow_path(line, 12), lin(t, b(252) + 0.3, b(252) + 1.0), 0.8)


# ------------------------------------------------------------------ S09: circles, growth and areas

CIRCLE = (250.0, 470.0, 95.0)
WAVE_X0, WAVE_X1 = 380.0, 650.0
SPIN = 2.6  # seconds per turn
EXP_AX = Axes(-2.2, 1.7, -0.4, 5.6, (740.0, 300.0, 440.0, 340.0))
LOG_AX = Axes(0.0, 4.4, -0.3, 2.9, (1300.0, 300.0, 440.0, 340.0))
CHIP = Chip(cx=960.0, cy=900.0, size=300.0)
LAND = (960.0, 690.0, 60.0)  # where the thrown circle meets the chip


def theta(t):
    return 2 * math.pi * (t - b(302)) / SPIN


def circle_point(t, cx, cy, r):
    th = theta(t)
    return cx + r * math.cos(th), cy - r * math.sin(th)


def sine_field(fr, t, a, circle_a):
    cx, cy, r = CIRCLE
    draw_on = ease_out(lin(t, b(302), b(302) + 0.7))
    arc = skia.Path()
    arc.addArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), 0, -359.9 * draw_on)
    fr.path_stroke(arc, "circle", 2.4, a * circle_a, glow=0.3 + 0.9 * pulse(t, b(311), 0.9))
    px, py = circle_point(t, cx, cy, r)
    fr.line(cx, cy, px, py, "circle", 1.2, 0.5 * a * circle_a)
    fr.glow_dot(px, py, 6.0, "circle", a * draw_on, 0.9)
    # its height, carried right, traces the sine wave ("circle")
    grow = ease_io(lin(t, b(302) + 0.6, b(311) + 0.4))
    if grow > 0:
        k = (WAVE_X1 - WAVE_X0) / (2 * math.pi)
        s = np.linspace(0.0, (WAVE_X1 - WAVE_X0) * grow, 160)
        ys = cy - r * np.sin(theta(t) - s / k)
        wave = skia.Path()
        wave.moveTo(WAVE_X0, float(ys[0]))
        for x, y in zip(WAVE_X0 + s[1:], ys[1:]):
            wave.lineTo(float(x), float(y))
        fr.dashed([px, WAVE_X0], [py, py], "circle", 1.2, 0.5 * a * grow, on=6, off=6)
        fr.path_stroke(wave, "original", 2.5, a * grow, glow=0.15)
        return wave
    return None


def exp_field(fr, t, a):
    ax = EXP_AX
    reveal = ease_out(lin(t, b(313), b(313) + 0.8))
    if reveal <= 0:
        return None
    fr.line(ax.left, float(ax.py(0)), ax.right, float(ax.py(0)), "axis", 2.0, a * reveal)
    xs = np.linspace(ax.x0, ax.x0 + (ax.x1 - ax.x0) * reveal, 200)
    curve = curve_path(ax, xs, np.exp(xs))
    with clip(fr, ax.rect):
        fr.path_stroke(curve, "original", 2.5, a, glow=0.15)
    ta = a * smooth(lin(t, b(313) + 0.6, b(313) + 1.1))
    if ta > 0.003:
        xp = 0.25 + 0.85 * math.sin(2 * math.pi * (t - b(313) - 0.6) / 5.0)
        hp = math.exp(xp)
        base, foot, top = ax.at(xp - 1, 0), ax.at(xp, 0), ax.at(xp, hp)
        tri = skia.Path()
        tri.addPoly([skia.Point(*base), skia.Point(*foot), skia.Point(*top)], True)
        fr.path_fill(tri, "light", 0.06 * ta)
        g = pulse(t, b(318), 1.4)  # "growth": rise over a run of 1 is the height itself
        with clip(fr, ax.rect):
            tip = ax.at(xp + 0.55, hp * 1.55)
            fr.line(*base, *tip, "light", 1.8, 0.8 * ta, glow=0.3)
        fr.line(*base, *foot, "x", 2.4 + 1.2 * g, ta, glow=0.3 + 0.6 * g)
        fr.line(*foot, *top, "light", 2.4 + 1.2 * g, ta, glow=0.3 + 0.8 * g)
        fr.glow_dot(*top, 6.0, "light", ta, 0.9)
        one = ta * smooth(lin(t, b(318) - 0.2, b(318) + 0.3))
        typmath.number(fr, "1", (base[0] + foot[0]) / 2, base[1] + 30, 30, "x", one)
    return curve


def log_field(fr, t, a):
    ax = LOG_AX
    reveal = ease_out(lin(t, b(320), b(320) + 0.8))
    if reveal <= 0:
        return None
    fr.line(ax.left, float(ax.py(0)), ax.right, float(ax.py(0)), "axis", 2.0, a * reveal)
    lo = 0.33
    xs = np.linspace(lo, lo + (ax.x1 - lo) * reveal, 200)
    curve = curve_path(ax, xs, 1 / xs)
    xa = 1.0 + 2.2 * ease_io(lin(t, b(321), b(326)))
    if xa > 1.0 + 1e-3:
        us = np.linspace(1.0, xa, 80)
        region = skia.Path()
        region.moveTo(*ax.at(1.0, 0.0))
        for x, y in zip(ax.px(us), ax.py(1 / us)):
            region.lineTo(float(x), float(y))
        region.lineTo(*ax.at(xa, 0.0))
        region.close()
        fr.path_fill(region, "x", 0.24 * a)
        fr.line(*ax.at(1.0, 0.0), *ax.at(1.0, 1.0), "x", 1.4, 0.6 * a)
        fr.line(*ax.at(xa, 0.0), *ax.at(xa, 1 / xa), "x", 2.0, a, glow=0.5)
        la = a * smooth(lin(t, b(323), b(323) + 0.5))
        typmath.draw(fr, f"ln {X}", *ax.at((1 + xa) / 2, 0.22), 40, None, la)
    with clip(fr, ax.rect):
        fr.path_stroke(curve, "original", 2.5, a, glow=0.15)
    return curve


def throw(t):
    """The pink circle: (cx, cy, r, alpha) as it is lifted out, thrown at the chip and bounced off."""
    u = lin(t, b(332), b(335))
    if u <= 0:
        return None
    cx0, cy0, r0 = CIRCLE
    cx1, cy1, r1 = LAND
    if u < 1:
        e = ease_io(u)
        return cx0 + (cx1 - cx0) * e, cy0 + (cy1 - cy0) * e - 220 * math.sin(math.pi * e), r0 + (r1 - r0) * e, 1.0
    v = lin(t, b(335), b(335) + 0.9)
    lift = 90 * back(ease_out(v), 1.2)
    return cx1 + 150 * ease_out(v), cy1 - lift, r1, 1 - smooth(lin(t, b(335) + 0.2, b(335) + 0.8))


def draw_s09(fr, t):
    if not b(302) - 0.1 <= t < S10 + 0.6:
        return
    out = 1 - smooth(lin(t, b(338), b(338) + 0.5))
    dim = 1 - 0.6 * smooth(lin(t, b(329), b(329) + 0.5))
    opens = (b(302), b(313), b(320))
    alphas = [smooth(lin(t, t0, t0 + 0.5)) * out * dim for t0 in opens]
    flying = throw(t)
    paths = []
    paths.append(sine_field(fr, t, alphas[0], 0.0 if flying else 1.0))
    paths.append(exp_field(fr, t, alphas[1]))
    paths.append(log_field(fr, t, alphas[2]))
    # "Beautiful ideas": one sweep crosses all three
    sweep = skia.Path()
    for q in paths:
        if q is not None:
            sweep.addPath(glow_path(q, 14))
    fr.light_sweep(sweep, lin(t, b(327), b(327) + 1.2), 0.7 * out, width=0.1)
    # "you cannot type a circle into a chip"
    rise = ease_out(lin(t, b(329), b(332) - 0.1))
    if rise > 0:
        chip = Chip(
            cx=CHIP.cx, cy=CHIP.cy + 420 * (1 - rise) + 420 * smooth(lin(t, b(338), b(338) + 0.6)), size=CHIP.size
        )
        chip.draw(fr, t, alpha=out, pulses=0.7)
        hit = pulse(t, b(335), 0.5)
        if hit > 0:
            fr.glow_dot(LAND[0], LAND[1] + LAND[2], 10 + 30 * hit, "circle", 0.7 * hit, 1.0)
    if flying:
        cx, cy, r, fa = flying
        fr.circle(cx, cy, r, "circle", 2.6, fa * out, glow=0.6)


# ------------------------------------------------------------------ S10: the impostor plan

SIN = TaylorStage("sin", view=(-6.3, 6.3, -1.9, 1.9), rect=(96.0, 200.0, 1728.0, 680.0))
P3 = T.coeffs("sin", 3)
F_LABEL = f"f({X})"


def sin_ax(t):
    z = 1 - 0.07 * ease_io(lin(t, b(338), END))  # a slow push keeps the long beats alive
    return Axes(-6.3 * z, 6.3 * z, -1.9 * z, 1.9 * z, SIN.ax.rect)


def draw_s10(fr, t):
    if t < b(338):
        return
    ax = sin_ax(t)
    SIN.static(fr, smooth(lin(t, b(338) + 0.2, b(338) + 0.8)), ax=ax, labels=False)
    gone = 1 - smooth(lin(t, END - 0.6, END))  # hand the bare axes to Chapter 2
    reveal = ease_io(lin(t, b(342), b(348) + 0.3))
    SIN.original(fr, gone, reveal=reveal, ax=ax)
    la = smooth(lin(t, b(347), b(347) + 0.5))
    lx, ly = ax.at(-math.pi * 1.5, 1.0)
    typmath.draw(fr, F_LABEL, lx, ly - 54, 48, None, la * gone)
    # the impostor: materializes above, then settles onto the original
    appear = ease_out(lin(t, b(350), b(350) + 0.8)) * gone
    if appear <= 0:
        return
    c = P3.copy()
    c[0] += 0.9 * (1 - ease_io(lin(t, b(354), b(357) + 0.3)))
    band = smooth(lin(t, b(369), b(369) + 0.7)) * gone
    SIN.error_band(fr, c, band, ax=ax)
    glow = 0.6 + 0.6 * pulse(t, b(357) + 0.3, 0.7)
    SIN.copy(fr, c, appear, ax=ax, glow=glow, reveal=appear, sym=True)
    zone = SIN.copy_path(c, ax, lo=-1.3, hi=1.3)
    fr.light_sweep(glow_path(zone, 14), lin(t, b(359), b(359) + 1.0), 0.8 * gone, width=0.12)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_graph(fr, t)
    draw_s07(fr, t)
    draw_s09(fr, t)
    draw_s10(fr, t)
    hud.eyebrow(fr, t, "01 · WHY POLYNOMIALS", START + 0.2)
    fr.zoom_blur(0.06 * math.sin(math.pi * ease_io(lin(t, b(295), b(299) + 0.4))))
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch1:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=END - START, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(END - START)
        if audio:
            scene.add_audio(AUDIO, start=0, trim_start=START)
    return scene


SCENES = {
    "S07": (S07, S08, [85.0, 91.6, 99.4]),
    "S08": (S08, S09, [103.3, 105.0, 108.8]),
    "S09": (S09, S10, [111.9, 116.5, 120.6]),
    "S10": (S10, END, [124.9, 128.4, 132.3]),
}
OFFSET = START
DURATION = END - START
STILLS = [s for _, _, st in SCENES.values() for s in st]
