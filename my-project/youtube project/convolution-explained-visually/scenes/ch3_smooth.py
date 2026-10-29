"""CHAPTER 3 - SMOOTH SHAPES (S11-S13), 03:23.120 - 04:27.440.

S11  From bars to curves: the formula   bars subdivide into a smooth curve, the sum sign morphs
                                        into an integral that flies into the definition, which
                                        writes on word by word (STIX math as vector paths).
S12  Reading it in pieces               each piece of the formula drives the plot below it:
                                        flip g, slide to t, multiply by f, area of overlap,
                                        then a live sweep traces (f*g)(t).  All numeric.
S13  Box * box = triangle               two unit boxes, linear slide, real overlap trace,
                                        then "smooths, spreads and blends" micro-beats.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia

from cues import AUDIO, cue
from fx import (
    Frame, conv_symbol, ease_io, ease_out, env, eyebrow, lerp, lin, mix, pulse, smooth, tokens,
)
from mathtype import Formula, Token, glyphs, symbol
from theme import H, THEME, TOKENS, W

START = cue(552)  # 203.12
END = cue(730)  # 267.44 "Now let's step into two dimensions"

T = {
    "smooth_w": cue(557), "continuous": cue(562), "curves": cue(563), "sum": cue(565), "integral": cue(568),
    "here": cue(569), "f1": cue(573), "star": cue(574), "g1": cue(575), "of_t": cue(576), "equals": cue(578),
    "int": cue(580), "minus_inf": cue(582), "inf": cue(585), "f2": cue(587), "tau1": cue(589), "times": cue(590),
    "g2": cue(591), "t2": cue(593), "minus": cue(594), "tau2": cue(595), "dtau": cue(596),
    "looks": cue(599), "but": cue(601), "pieces": cue(605), "g_minus": cue(606), "flipped": cue(613),
    "g_t": cue(615), "slid": cue(624), "position": cue(627), "we": cue(629), "multiply": cue(630),
    "point": cue(634), "and_int": cue(637), "integral2": cue(639), "area": cue(643), "overlap": cue(646),
    "so": cue(647), "convolution": cue(649), "flip": cue(656), "slide": cue(659), "measure": cue(664),
    "overlap2": cue(666), "lets": cue(667), "classic": cue(670), "boxes": cue(673), "height": cue(676),
    "one_h": cue(677), "width": cue(679), "one_w": cue(680), "apart": cue(682), "zero": cue(690),
    "slide3": cue(691), "grows": cue(699), "line_up": cue(706), "peaks": cue(710), "one_p": cue(712),
    "shrinks": cue(715), "zero2": cue(718), "boxes2": cue(720), "triangle": cue(724), "smooths": cue(726),
    "spreads": cue(727), "blends": cue(729),
}

INK, SIG, KER, OVL, OUT = (TOKENS[k] for k in ("ink", "signal", "kernel", "overlap", "output"))

FORMULA = Formula([
    Token("l1", "(", INK, 0.0), Token("f1", "f", SIG, 0.04), Token("st", r"\ast", OVL, 0.04),
    Token("g1", "g", KER, 0.0), Token("l2", ")(t)", INK, 0.25), Token("eq", "=", INK, 0.25),
    Token("int", r"\int_{-\infty}^{\infty}", INK, 0.12), Token("f2", "f", SIG, 0.0), Token("ft", r"(\tau)", INK, 0.14),
    Token("g2", "g", KER, 0.03), Token("p1", "(", INK, 0.0), Token("tm", "t-", INK, 0.03),
    Token("tau", r"\tau", INK, 0.0), Token("p2", ")", INK, 0.16), Token("d", r"d\tau", INK, 0.0),
], size=96)
LHS = ("l1", "f1", "st", "g1", "l2")
WRITE = {
    "l1": "f1", "f1": "f1", "st": "star", "g1": "g1", "l2": "of_t", "eq": "equals", "int": "int",
    "f2": "f2", "ft": "tau1", "g2": "g2", "p1": "t2", "tm": "minus", "tau": "tau2", "p2": "tau2", "d": "dtau",
}


def formula_place(t):
    m = ease_io(lin(t, T["but"], T["pieces"] + 0.2))
    return lerp(540.0, 205.0, m), lerp(1.0, 0.72, m)


# ------------------------------------------------------------------ S11
def bell(x):
    return np.exp(-x**2 / 2)


def draw_s11(fr, t):
    vis = env(t, START, T["but"] + 0.4, 0.5, 0.5)
    # bars subdividing into a smooth filled curve
    bars_a = env(t, START + 0.05, T["here"] + 0.5, 0.5, 0.6)
    if bars_a > 0:
        levels = [13, 25, 49, 101, 241]
        k = 0
        for i, tt in enumerate((T["continuous"] - 0.3, T["continuous"] + 0.25, T["curves"] + 0.1, T["curves"] + 0.45)):
            if t >= tt:
                k = i + 1
        n = levels[k]
        x0, x1, base, hgt = 300.0, 1260.0, 760.0, 380.0
        xs = np.linspace(-3.2, 3.2, n)
        w = (x1 - x0) / n
        for j, xv in enumerate(xs):
            h = bell(xv) * hgt
            bx = x0 + j * w
            gap = max(0.0, w * 0.18) if n < 100 else 0.0
            fr.rrect(bx + gap / 2, base - h, w - gap, h, min(4.0, w * 0.2), fill="output",
                     fill_alpha=0.55 if n < 100 else 0.32, alpha=bars_a)
        if n >= 101:
            px = np.linspace(x0, x1, 200)
            py = base - bell(np.linspace(-3.2, 3.2, 200)) * hgt
            fr.poly(px, py, "output", 3.0, bars_a, glow=0.8)
        fr.line(x0 - 20, base, x1 + 20, base, "line", 1.4, bars_a)
    # sum sign morphs into the integral sign, then flies into the formula
    morph = ease_io(lin(t, T["integral"] - 0.35, T["integral"] + 0.25))
    fly = ease_io(lin(t, T["here"] + 0.3, T["here"] + 1.3))
    sa = ease_out(lin(t, T["sum"] - 0.3, T["sum"] + 0.2))
    if sa > 0 and fly < 1:
        cx, cy = 1530.0, 520.0
        ib = FORMULA.bounds("int", 960, 540)
        tx, ty = ib[0] + 26, 540 - 30
        x, y = lerp(cx, tx, fly), lerp(cy, ty, fly)
        size = lerp(260.0, 96.0, fly)
        symbol(fr, r"\sum", x, y, size, "output", sa * (1 - morph), glow=0.4, scale=1.0)
        symbol(fr, r"\int", x, y, size * 1.15, "ink", sa * morph, glow=0.4 * (1 - fly))
        fr.text("SUM" if morph < 0.5 else "INTEGRAL", 1530, 760, "sans", 24, 700, "output" if morph < 0.5 else "ink",
                sa * (1 - fly) * abs(1 - 2 * morph), tracking=0.22)


def draw_formula(fr, t):
    vis = env(t, T["here"] + 0.2, T["lets"] - 0.1, 0.3, 0.5)
    if vis <= 0.003:
        return
    base, scale = formula_place(t)
    alpha, glow, dy, color = {}, {}, {}, {}
    for tok in FORMULA.tokens:
        t0 = T[WRITE[tok.key]] - 0.12
        if tok.key == "int":
            t0 = T["here"] + 1.25
        a = ease_out(lin(t, t0, t0 + 0.35))
        alpha[tok.key] = a * vis
        dy[tok.key] = 16 * (1 - a) * scale
    # highlight windows in S12: (keys, start, end, colour)
    windows = [
        (("g2", "p1", "tm", "tau", "p2"), T["g_minus"] - 0.2, T["g_t"] - 0.2, None),
        (("tm",), T["g_t"] - 0.2, T["we"] - 0.2, OUT),
        (("f2", "ft", "g2", "p1", "tm", "tau", "p2"), T["we"] - 0.1, T["and_int"] - 0.1, None),
        (("int", "d"), T["and_int"] - 0.1, T["so"] - 0.1, None),
        (LHS, T["so"], T["flip"] - 0.2, OUT),
    ]
    active = None
    for keys, a0, a1, col in windows:
        if a0 <= t < a1:
            active = (keys, a0, a1, col)
    if active:
        keys, a0, a1, col = active
        h = env(t, a0, a1, 0.25, 0.25)
        for tok in FORMULA.tokens:
            if tok.key in keys:
                glow[tok.key] = 0.9 * h
                if col:
                    color[tok.key] = mix(tok.color, col, h)
            else:
                alpha[tok.key] *= 1 - 0.55 * h
    # intimidating: a quick scale pulse
    scale *= 1 + 0.035 * pulse(t, T["looks"], 0.9)
    # integral: bare sign until the limits are spoken
    lim = ease_out(lin(t, T["minus_inf"] - 0.2, T["minus_inf"] + 0.3))
    a_int = alpha.get("int", 0)
    alpha["int"] = a_int * lim
    FORMULA.draw(fr, 960, base, scale, alpha=alpha, color=color, glow=glow, dy=dy)
    if a_int * (1 - lim) > 0.003:
        b = FORMULA.bounds("int", 960, base, scale)
        path, (x0, x1, top, bottom) = glyphs(r"\int", FORMULA.size)
        m = skia.Matrix()
        m.setScale(scale, scale)
        m.postTranslate(b[0] - x0 * scale, base)
        p = skia.Path(path)
        p.transform(m)
        fr.path_fill(p, INK, a_int * (1 - lim))
    # LHS underline when it is named "the convolution at time t"
    u = env(t, T["convolution"] - 0.2, T["lets"] - 0.2, 0.4, 0.4) * vis
    if u > 0:
        l = FORMULA.bounds("l1", 960, base, scale)[0]
        r = FORMULA.bounds("l2", 960, base, scale)[2]
        fr.line(l, base + 26 * scale, lerp(l, r, ease_io(min(1, u * 1.5))), base + 26 * scale, "output", 3.0, u, glow=0.8)


# ------------------------------------------------------------------ S12: the plot under the formula
TAU = np.linspace(-5.0, 5.0, 801)
X0, XS, BASE, YS = 960.0, 190.0, 870.0, 330.0


def f_fn(x):
    return 0.9 * np.exp(-(x**2) / 0.8)


def g_fn(x):
    x = np.asarray(x, float)
    return np.where(x >= 0, 0.85 * (x / 0.7) * np.exp(1 - x / 0.7), 0.0)


@lru_cache(maxsize=1)
def conv_curve():
    ts = np.linspace(-3.0, 4.0, 281)
    vals = np.array([np.trapezoid(f_fn(TAU) * g_fn(tt - TAU), TAU) for tt in ts])
    return ts, vals


def sx(tau):
    return X0 + np.asarray(tau) * XS


def sy(v):
    return BASE - np.asarray(v) * YS


def plot_t(t):
    """Current shift t and flip factor k (1 = original g, -1 = flipped)."""
    k = math.cos(math.pi * ease_io(lin(t, T["flipped"] - 0.25, T["flipped"] + 0.6)))
    tt = lerp(0.0, 1.3, ease_io(lin(t, T["slid"] - 0.4, T["position"] + 0.3)))
    tt = lerp(tt, -3.0, ease_io(lin(t, T["flip"] - 0.7, T["flip"] - 0.1)))
    tt = lerp(tt, 4.0, lin(t, T["flip"], T["overlap2"] + 0.5))
    return tt, k


def draw_s12(fr, t):
    vis = env(t, T["but"] + 0.1, T["lets"] - 0.05, 0.6, 0.45)
    if vis <= 0.003:
        return
    tt, k = plot_t(t)
    # axis
    fr.line(sx(-4.3), BASE, sx(4.3), BASE, "line", 1.5, vis)
    symbol(fr, r"\tau", sx(4.45), BASE + 6, 40, TOKENS["muted"], vis)
    # f
    vis_tau = np.abs(TAU) <= 4.3
    fr.poly(sx(TAU[vis_tau]), sy(f_fn(TAU[vis_tau])), "signal", 2.8, vis, glow=0.5)
    symbol(fr, r"f(\tau)", sx(-1.55), sy(0.62), 44, SIG, vis)
    # g: original -> flipped (x = t + k*tau') -> slid
    gx = tt + k * TAU
    gv = g_fn(TAU)
    mask = (gv > 1e-4) & (np.abs(gx) <= 4.3)
    fr.poly(sx(gx[mask]), sy(gv[mask]), "kernel", 2.8, vis, glow=0.5)
    flipped = k < 0
    label = r"g(\tau)" if not flipped else (r"g(-\tau)" if t < T["g_t"] - 0.1 else r"g(t-\tau)")
    peak_x = tt + k * 0.7
    symbol(fr, label, sx(peak_x) + (90 if not flipped else -100), sy(0.98), 44, KER, vis)
    fr.text("FLIP", 960, 1010, "sans", 24, 700, "kernel", env(t, T["flipped"] - 0.3, T["g_t"], 0.25, 0.35) * vis,
            tracking=0.22)
    # t marker
    ta = env(t, T["g_t"] + 0.2, T["lets"] - 0.1, 0.4, 0.4) * vis
    if ta > 0:
        x = sx(tt)
        for y0 in range(int(sy(1.15)), int(BASE), 18):
            fr.line(x, y0, x, y0 + 9, "output", 2.0, ta)
        symbol(fr, "t", x, sy(1.15) - 26, 46, OUT, ta, glow=0.4)
    fr.text("SLIDE TO t", 960, 1010, "sans", 24, 700, "kernel", env(t, T["slid"] - 0.3, T["we"] - 0.1, 0.25, 0.35) * vis,
            tracking=0.22)
    # product and its area
    pa = ease_out(lin(t, T["multiply"] - 0.2, T["multiply"] + 0.5)) * vis
    if pa > 0:
        prod = f_fn(TAU) * g_fn(tt - TAU) if flipped else f_fn(TAU) * gv
        area = float(np.trapezoid(prod, TAU))
        sel = prod > 1e-4
        if sel.sum() > 2:
            px, py = sx(TAU[sel]), sy(prod[sel])
            fill_a = lerp(0.18, 0.5, ease_out(lin(t, T["area"] - 0.4, T["area"] + 0.3)))
            p = skia.Path()
            p.moveTo(float(px[0]), BASE)
            for x, y in zip(px, py):
                p.lineTo(float(x), float(y))
            p.lineTo(float(px[-1]), BASE)
            p.close()
            fr.path_fill(p, "overlap", fill_a * pa, glow=0.35 * fill_a)
            fr.poly(px, py, "overlap", 2.6, pa, glow=0.7)
        fr.text("MULTIPLY", 960, 1010, "sans", 24, 700, "overlap", env(t, T["multiply"] - 0.2, T["and_int"], 0.25, 0.35) * vis,
                tracking=0.22)
        aa = ease_out(lin(t, T["integral2"] - 0.2, T["integral2"] + 0.4)) * vis
        if aa > 0:
            tokens(fr, [("area", "muted", 1), ("=", "muted", 1), (f"{area:.2f}", "output", 1)], 430, sy(1.05), 42, aa)
    # live output trace (f*g)(t) during the summary sweep
    sa = ease_out(lin(t, T["flip"] - 0.1, T["flip"] + 0.3)) * vis
    if sa > 0:
        ts, vals = conv_curve()
        sel = ts <= tt
        if sel.sum() > 1:
            fr.poly(sx(ts[sel]), sy(vals[sel] * 1.15), "output", 3.2, sa, glow=0.9)
            fr.glow_dot(sx(ts[sel][-1]), sy(vals[sel][-1] * 1.15), 7, "output", alpha=sa, strength=1.2)
        symbol(fr, r"(f\ast g)(t)", sx(-2.9), sy(0.42), 40, OUT, sa * smooth(lin(t, T["slide"], T["slide"] + 0.5)))
    # recipe words lighting on the summary sentence
    ra = env(t, T["flip"] - 0.3, T["lets"] - 0.1, 0.3, 0.4) * vis
    if ra > 0:
        lit = [smooth(lin(t, T[k] - 0.15, T[k] + 0.2)) for k in ("flip", "slide", "measure")]
        items = [("FLIP", mix(TOKENS["muted"], KER, lit[0]), 1), ("·", "muted", 1),
                 ("SLIDE", mix(TOKENS["muted"], KER, lit[1]), 1), ("·", "muted", 1),
                 ("MEASURE THE OVERLAP", mix(TOKENS["muted"], OVL, lit[2]), 1)]
        tokens(fr, items, 960, 1010, 28, ra, family="sans", weight=700)


# ------------------------------------------------------------------ S13: box * box = triangle
UNIT = 220.0
BOX_BOTTOM = 590.0
PLOT_BASE, PLOT_H = 930.0, 230.0
CYAN_X = 960.0
SPEED = (960.0 - 521.0) / 5.7  # px per second; aligned exactly on "peaks at one"


def amber_x(t):
    t_aligned = T["peaks"] + 0.05
    t0 = t_aligned - 5.7
    return 521.0 + SPEED * max(0.0, t - t0) if t > t0 else 521.0


def overlap_frac(x):
    return max(0.0, 1.0 - abs(x - CYAN_X) / UNIT)


@lru_cache(maxsize=1)
def smoothed_triangle():
    xs = np.linspace(521.0, 1400.0, 400)
    tri = np.array([overlap_frac(x) for x in xs])
    k = np.exp(-np.linspace(-3, 3, 61) ** 2 / 2)
    k /= k.sum()
    pad = np.pad(tri, 30, mode="edge")
    return xs, tri, np.convolve(pad, k, mode="same")[30:-30]


def draw_s13(fr, t):
    vis = env(t, T["lets"] - 0.1, END, 0.5, 0.45)
    if vis <= 0.003:
        return
    xa = amber_x(t)
    # boxes
    ca = ease_out(lin(t, T["boxes"] - 0.2, T["boxes"] + 0.3)) * vis
    fr.rrect(CYAN_X - UNIT / 2, BOX_BOTTOM - UNIT, UNIT, UNIT, 6, fill="signal", fill_alpha=0.12, stroke="signal",
             width=2.6, alpha=ca, glow=0.5)
    aa = ease_out(lin(t, T["boxes"] - 0.05, T["boxes"] + 0.45)) * vis * (1 - smooth(lin(t, T["triangle"] - 0.2, T["triangle"] + 0.4)))
    fr.rrect(xa - UNIT / 2, BOX_BOTTOM - UNIT, UNIT, UNIT, 6, fill="kernel", fill_alpha=0.12, stroke="kernel",
             width=2.6, alpha=aa, glow=0.5)
    fr.line(300, BOX_BOTTOM, 1620, BOX_BOTTOM, "line", 1.4, ca)
    ov = overlap_frac(xa)
    if ov > 0:
        lo = max(xa, CYAN_X) - UNIT / 2
        fr.rrect(lo, BOX_BOTTOM - UNIT, ov * UNIT, UNIT, 2, fill="overlap", fill_alpha=0.38, alpha=aa)
    # dimensions: height 1, width 1
    ha = env(t, T["height"] - 0.2, T["slide3"], 0.3, 0.4) * vis
    if ha > 0:
        x = CYAN_X + UNIT / 2 + 34
        fr.line(x, BOX_BOTTOM - UNIT, x, BOX_BOTTOM, "muted", 1.6, ha)
        for y in (BOX_BOTTOM - UNIT, BOX_BOTTOM):
            fr.line(x - 10, y, x + 10, y, "muted", 1.6, ha)
        symbol(fr, "1", x + 30, BOX_BOTTOM - UNIT / 2, 44, INK, ha)
    wa = env(t, T["width"] - 0.2, T["slide3"], 0.3, 0.4) * vis
    if wa > 0:
        y = BOX_BOTTOM + 30
        fr.line(CYAN_X - UNIT / 2, y, CYAN_X + UNIT / 2, y, "muted", 1.6, wa)
        for x in (CYAN_X - UNIT / 2, CYAN_X + UNIT / 2):
            fr.line(x, y - 10, x, y + 10, "muted", 1.6, wa)
        symbol(fr, "1", CYAN_X, y + 34, 44, INK, wa)
    # output plot
    pa = ease_out(lin(t, T["apart"] + 0.3, T["apart"] + 0.9)) * vis
    if pa > 0:
        fr.line(380, PLOT_BASE, 1540, PLOT_BASE, "line", 1.4, pa)
        fr.text("OVERLAP", 380, PLOT_BASE - PLOT_H - 30, "sans", 22, 700, "output", pa, align="left", tracking=0.2)
        xs, tri, smo = smoothed_triangle()
        reach = xa if t < T["triangle"] else 1400.0
        sel = xs <= reach
        sm = ease_io(lin(t, T["smooths"] - 0.15, T["smooths"] + 0.45))
        sp = ease_io(lin(t, T["spreads"] - 0.15, T["spreads"] + 0.45))
        bl = pulse(t, T["blends"] - 0.1, 0.9)
        vals = lerp(tri, smo, sm)
        xx = CYAN_X + (xs - CYAN_X) * (1 + 0.16 * sp)
        if sel.sum() > 1:
            color = mix(OUT, "#ffffff", 0.35 * bl)
            fr.poly(xx[sel], PLOT_BASE - vals[sel] * PLOT_H, color, 3.2, pa, glow=0.9 + 0.8 * bl)
            if t < T["triangle"]:
                fr.glow_dot(xx[sel][-1], PLOT_BASE - vals[sel][-1] * PLOT_H, 7, "output", alpha=pa, strength=1.2)
        za = env(t, T["zero"] - 0.2, T["slide3"] + 0.6, 0.3, 0.4) * pa
        symbol(fr, "0", 521.0, PLOT_BASE + 40, 40, INK, za)
        oa = env(t, T["one_p"] - 0.25, T["triangle"] + 0.3, 0.3, 0.4) * pa
        if oa > 0:
            for x0 in range(400, 940, 22):
                fr.line(x0, PLOT_BASE - PLOT_H, x0 + 11, PLOT_BASE - PLOT_H, "muted", 1.4, oa)
            symbol(fr, "1", 360, PLOT_BASE - PLOT_H, 40, INK, oa)
        for key, word in (("smooths", "SMOOTHS"), ("spreads", "SPREADS"), ("blends", "BLENDS")):
            k = ("smooths", "spreads", "blends").index(key)
            wa2 = ease_out(lin(t, T[key] - 0.15, T[key] + 0.2)) * vis
            fr.text(word, 760 + k * 200, 1010, "sans", 26, 700, "output", wa2, tracking=0.22)
    # box * box = triangle
    ea = ease_out(lin(t, T["triangle"] - 0.3, T["triangle"] + 0.3)) * vis
    if ea > 0:
        y = 250.0
        fr.rrect(760 - 34, y - 34, 68, 68, 4, fill="signal", fill_alpha=0.15, stroke="signal", width=2.4, alpha=ea)
        conv_symbol(fr, 850, y, 24, ea)
        fr.rrect(940 - 34, y - 34, 68, 68, 4, fill="kernel", fill_alpha=0.15, stroke="kernel", width=2.4, alpha=ea)
        symbol(fr, "=", 1030, y, 70, INK, ea)
        p = skia.Path()
        p.moveTo(1090, y + 34)
        p.lineTo(1160, y - 34)
        p.lineTo(1230, y + 34)
        p.close()
        fr.path_fill(p, "output", 0.15 * ea)
        fr.path_stroke(p, "output", 2.6, ea, glow=0.8)


# ------------------------------------------------------------------ assembly

def draw(t, size):
    t = t + START
    fr = Frame(size)
    draw_s11(fr, t)
    draw_formula(fr, t)
    draw_s12(fr, t)
    draw_s13(fr, t)
    eyebrow(fr, t, "03 · SMOOTH SHAPES", START + 0.15)
    return fr.finish()


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
STILLS = [205.0, 207.3, 208.6, 209.8, 210.8, 212.5, 216.6, 219.3, 221.9, 224.0, 225.0, 228.6, 232.2, 235.6,
          238.4, 241.0, 243.2, 247.0, 248.9, 251.0, 255.0, 258.8, 260.8, 263.8, 265.5, 266.9]
