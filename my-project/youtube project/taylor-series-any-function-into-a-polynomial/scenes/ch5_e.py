"""CHAPTER 5 · e FROM FRACTIONS, 05:59.560 – 07:24.240 (cue #987 "Let's" → #1177 "Now,").

S24  Its own slope       the recipe, then eˣ sets and draws -> a probe rides it: the height bar and the tangent's rise over
                         a run of 1 are the same length, height and slope tick together -> f′ and f″ slide onto the curve,
                         five ghost derivatives fan out in depth and collapse into one line
S25  All ones            the probe snaps to 0, e⁰ = 1 -> the ladder fills 1 1 1 1 1 -> the 1s fly into the recipe, which
                         comes out clean: 1 + x + x²/2! + x³/3! + x⁴/4! + ⋯, each term lighting as the hug runs P₀ … P₄
S26  Out comes e         every x turns into a blue 1 -> 1 + 1 + 1/2! + ⋯ = e -> a gold fraction bar grows along a number line,
                         the running sum locking in lime, a lens following the tip (×10, ×100) -> e = 2.71828…, the gap 0.0016
S27  Factorials win      n = 5 -> n = 10, the lens dives to ×10⁷ while seven decimals lock -> a bar race on a log axis, 2ⁿ
                         against n!, 10! = 3,628,800 -> the bars flip to 1/n! and the running sum lands flat on e

Clean frame: no cards or pills. Every number is computed (``T.e_sums``, ``math.factorial``, ``np.exp``), never typed.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import skia
from components import taylor as T
from components.digits import lock
from components.fx import glow_path, layer_alpha
from components.ladder import float_rows, label
from components.moves import zoom_about
from components.stage import Axes, TaylorStage, clip
from cues import AUDIO, beat, cue
from theme import THEME, H, W

from faceless_champ.draw import Frame, back, ease_io, ease_out, hud, lin, pulse, smooth
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc
from scenes import ch4_recipe as ch4

START = cue(987)  # 359.56 "Let's put the recipe to work"
END = cue(1177)  # 444.24 "Now, let's return to"

b = beat

S24, S25, S26, S27 = START, cue(1033), cue(1089), cue(1130)

X = tc("x", "x")
E = tc("result", "e")
ONE = tc("x", "1")


def F(s):
    return tc("fact", s)


LIME = "#a6e35a"
SUMS = T.e_sums(10)
TRUE_E = math.e

# ------------------------------------------------------------------ S24 · eˣ, its own slope

FULL = Axes(-3.2, 3.2, -0.7, 5.6, (96.0, 220.0, 1728.0, 760.0))  # the rect Chapter 4 left on screen
AX25 = Axes(-2.8, 2.2, -0.6, 4.4, (96.0, 250.0, 1180.0, 700.0))
EXP = TaylorStage("exp", view=(-3.2, 3.2, -0.7, 5.6), rect=FULL.rect)
FX, FY, TS = 150.0, 150.0, 78.0
TITLE = [f"{E}^{X}", f"({E}^{X})' = {E}^{X}", f"({E}^{X})'' = {E}^{X}", f"({E}^{X})^((n)) = {E}^{X}"]
TITLE_T = [b(1023), b(1028), b(1031)]  # "itself", "second … itself", "Every derivative"


def title_cx(expr):
    return FX + typmath.size_of(expr, TS)[0] / 2


def stage_ax(t):
    return FULL.lerp(AX25, ease_io(lin(t, b(1033), b(1034) + 0.6)))


def draw_title(fr, t):
    """The recipe in Σ form, then eˣ big at centre, which settles top-left and grows into (eˣ)⁽ⁿ⁾ = eˣ."""
    ra = smooth(lin(t, b(988), b(988) + 0.5)) * (1 - smooth(lin(t, b(999), b(1000))))
    typmath.draw(fr, ch4.SUM, 960, 470, 84, None, ra, glow=0.2)
    if t < b(1000):
        return
    out = 1 - smooth(lin(t, b(1033), b(1033) + 0.5))
    a = smooth(lin(t, b(1000), b(1000) + 0.35)) * out
    if a <= 0.003:
        return
    u = ease_io(lin(t, b(1003) + 0.3, b(1004) + 0.5))
    if t < TITLE_T[0]:
        pop = back(min(1.0, lin(t, b(1000), b(1000) + 0.45)), 1.4)
        size = (170 + (TS - 170) * u) * (0.7 + 0.3 * pop)
        cx, cy = 960 + (title_cx(TITLE[0]) - 960) * u, 470 + (FY - 470) * u
        typmath.draw(fr, TITLE[0], cx, cy, size, None, a, glow=0.3)
        return
    k = max(i for i, t0 in enumerate(TITLE_T) if t >= t0)
    m = lin(t, TITLE_T[k], TITLE_T[k] + 0.6)
    A, B = TITLE[k], TITLE[k + 1]
    typmath.morph(
        fr, A, B, m, title_cx(A), FY, TS, a, glow=0.3 + 0.5 * pulse(t, TITLE_T[k] + 0.6, 0.6), b_cx=title_cx(B)
    )


def deriv_copy(fr, ax, dy, alpha, width=2.4, glow=0.4):
    xs = np.linspace(ax.x0, ax.x1, 300)
    px, py = ax.px(xs), ax.py(np.exp(xs)) + dy
    with clip(fr, ax.rect):
        fr.poly(px, py, "cyan", width, alpha, glow)


def draw_exp(fr, t):
    a = smooth(lin(t, START + 0.3, START + 1.0)) * (1 - smooth(lin(t, b(1097), b(1098) + 0.4)))
    if a <= 0.003:
        return
    ax = stage_ax(t)
    push = 1 + 0.035 * ease_io(lin(t, b(1004), b(1011))) * (1 - ease_io(lin(t, b(1011), b(1012) + 0.4)))
    with zoom_about(fr, 960, 600, push):
        EXP.static(fr, a, ax=ax, labels=False)
        reveal = ease_io(lin(t, b(1000) + 0.2, b(1004)))
        glow = 0.15 + 0.6 * pulse(t, b(1008), 1.0) + 0.6 * pulse(t, b(1032) + 0.3, 0.8)
        EXP.original(fr, a, reveal=reveal, ax=ax, glow=glow)
        draw_probe24(fr, t, ax, a)
        draw_derivs(fr, t, ax, a)
    if t >= S25:
        draw_s25_stage(fr, t, ax, a)


def draw_probe24(fr, t, ax, a):
    """A probe rides eˣ: the height bar at x and the tangent's rise over a run of 1 are the same length."""
    pa = a * smooth(lin(t, b(1011) - 0.2, b(1011) + 0.3)) * (1 - smooth(lin(t, b(1019), b(1019) + 0.5)))
    if pa <= 0.003:
        return
    x0 = -2.2 + 3.0 * ease_io(lin(t, b(1011), b(1018) + 0.3))
    h = math.exp(x0)
    slope = (math.exp(x0 + 1e-5) - math.exp(x0 - 1e-5)) / 2e-5  # measured, not assumed
    with clip(fr, ax.rect):
        xs = np.array([x0 - 1.4, x0 + 1.6])
        fr.line(
            *ax.at(xs[0], h + slope * (xs[0] - x0)), *ax.at(xs[1], h + slope * (xs[1] - x0)), "frame", 1.6, 0.8 * pa
        )
        fr.line(*ax.at(x0, 0), *ax.at(x0, h), "x", 3.0, pa, glow=0.4)  # height
        fr.dashed([float(ax.px(x0)), float(ax.px(x0 + 1))], [float(ax.py(h))] * 2, "frame", 1.4, 0.7 * pa, on=7, off=6)
        fr.line(*ax.at(x0 + 1, h), *ax.at(x0 + 1, h + slope), "x", 3.0, pa, glow=0.4)  # rise over a run of 1
    typmath.draw(fr, "1", float(ax.px(x0 + 0.5)), float(ax.py(h)) + 26, 28, "muted", pa)
    fr.glow_dot(*ax.at(x0, h), 7.0, "x", pa, 1.0)
    EXP.probe(fr, x0, pa, ax=ax, drop=False)
    for k, (name, v) in enumerate((("height", h), ("slope", slope))):
        y = 300 + 72 * k
        fr.text(name, 150, y, "sans", 30, 500, "muted", pa, align="left")
        hud.tabular(fr, f"{v:.3f}", 430, y, 46, "x", pa, align="right", glow=0.2)


def draw_derivs(fr, t, ax, a):
    """f′ drops onto eˣ from above, f″ rises from below; then five ghosts fan out in depth and collapse."""
    for t0, dy0 in ((b(1021), -170.0), (b(1025), 170.0)):
        u = ease_io(lin(t, t0, t0 + 0.8))
        ca = a * smooth(lin(t, t0 - 0.2, t0 + 0.2)) * (1 - smooth(lin(t, t0 + 0.8, t0 + 1.3)))
        if ca > 0.003:
            deriv_copy(fr, ax, dy0 * (1 - u), ca, glow=0.4 + 0.6 * pulse(t, t0 + 0.8, 0.5))
            name = "f'" if dy0 < 0 else "f''"
            typmath.draw(
                fr,
                tc("cyan", name),
                float(ax.px(1.15)) + 46,
                float(ax.py(math.exp(1.15))) + dy0 * (1 - u),
                40,
                None,
                ca,
            )
    spread = ease_out(lin(t, b(1029), b(1029) + 0.5)) * (1 - ease_io(lin(t, b(1031) + 0.1, b(1032) + 0.3)))
    if spread > 0.003:
        for k in range(5, 0, -1):
            for c in (fr.c, fr.g):
                c.save()
                c.translate(30 * k * spread, -24 * k * spread)
            with zoom_about(fr, 960, 600, 1 - 0.03 * k * spread):
                deriv_copy(fr, ax, 0.0, a * spread * 0.55 * (1 - 0.13 * k), width=2.0, glow=0.2)
            for c in (fr.c, fr.g):
                c.restore()


# ------------------------------------------------------------------ S25 · all ones, then the clean series

LAD_X, LAD_Y, LAD_W, LAD_S, LAD_H = 1330.0, 300.0, 460.0, 42.0, 80.0
ROW_T = [b(1043) + 0.1 * k for k in range(5)]
FILL_T = [b(1050) + 0.1 * k for k in range(5)]
FORM5 = ch4.FORM5
FILLED_P = [
    tc("result", "1"),
    f"+ {tc('result', '1')} {X}",
    f"+ {tc('result', '1')}/{F('2!')} {X}^2",
    f"+ {tc('result', '1')}/{F('3!')} {X}^3",
    f"+ {tc('result', '1')}/{F('4!')} {X}^4",
    "+ dots.c",
]
CLEAN_P = ["1", f"+ {X}", f"+ {X}^2/{F('2!')}", f"+ {X}^3/{F('3!')}", f"+ {X}^4/{F('4!')}", "+ dots.c"]
ONES_P = ["1", f"+ {ONE}", f"+ {ONE}^2/{F('2!')}", f"+ {ONE}^3/{F('3!')}", f"+ {ONE}^4/{F('4!')}", "+ dots.c"]
FRACS_P = ["1", "+ 1", f"+ 1/{F('2!')}", f"+ 1/{F('3!')}", f"+ 1/{F('4!')}", "+ dots.c"]
PLUS = {p: p.replace("+ ", f"{tc('plus', '+')} ", 1) for p in FILLED_P + CLEAN_P + ONES_P + FRACS_P}
FILLED, CLEAN, ONES, FRACS = (" ".join(PLUS[p] for p in ps) for ps in (FILLED_P, CLEAN_P, ONES_P, FRACS_P))
FRACS_E = f"{FRACS} = {E}"
TERM_T = [b(1063), b(1064), b(1066), b(1072), b(1078), b(1086)]  # "1", "plus X", "X squared …", …, "and so on"
HUG_T = TERM_T[1:5]
SX, SY, SS = 960.0, 150.0, 54.0
ONE_SLOTS = [i for i, g in enumerate(typmath.glyphs(FILLED)[0]) if g.color.lower() == LIME]
EXP_Z = [T.hug_zone("exp", n, side="right") for n in range(1, 5)]


def ranges(parts):
    out, i = [], 0
    for p in parts:
        n = len(typmath.glyphs(PLUS[p])[0])
        out.append(range(i, i + n))
        i += n
    return out


R_CLEAN, R_FRACS = ranges(CLEAN_P), ranges(FRACS_P)


def value_center(k):
    return LAD_X + LAD_W - 56 - 12, LAD_Y + LAD_H * (k + 0.5)


def zone_lr(fn, c, a=0.0, tol=0.01, reach=4.0):
    steps = np.arange(1, int(reach / 0.004) + 1) * 0.004
    out = []
    for s in (-1, 1):
        xs = a + s * steps
        bad = np.nonzero(np.abs(fn(xs) - T.evaluate(c, xs, a)) >= tol)[0]
        out.append(steps[bad[0] - 1] if len(bad) and bad[0] else (0.0 if len(bad) else reach))
    return a - out[0], a + out[1]


def draw_s25_stage(fr, t, ax, a):
    # the probe snaps to 0; e⁰ = 1
    snap = back(min(1.0, lin(t, b(1034), b(1034) + 0.45)), 1.3)
    x0 = 0.8 * (1 - snap)
    to1 = ease_io(lin(t, b(1091), b(1091) + 0.6))  # S26: "set X equal to 1"
    x0 += to1
    pa = a * smooth(lin(t, b(1034) - 0.1, b(1034) + 0.2))
    EXP.probe(fr, x0, pa, ax=ax, drop=False)
    dot = smooth(lin(t, b(1036), b(1036) + 0.3))
    if dot > 0:
        y = math.exp(x0)
        fr.dashed([float(ax.px(x0))] * 2, [float(ax.py(0)), float(ax.py(y))], "x", 1.6, 0.7 * pa * dot, on=8, off=7)
        fr.glow_dot(*ax.at(x0, y), 8.0 + 8 * pulse(t, b(1041), 0.6), "result", pa * dot, 1.0)
        la = pa * dot * (1 - smooth(lin(t, b(1063), b(1063) + 0.4)))
        typmath.draw(
            fr, f"{E}^{tc('x', '0')} = {tc('result', '1')}", float(ax.px(0)) - 130, float(ax.py(1)) - 70, 46, None, la
        )
        ea = pa * to1 * (1 - smooth(lin(t, b(1097), b(1097) + 0.4)))
        typmath.draw(fr, f"{E}^{ONE} = {E}", float(ax.px(1)) + 110, float(ax.py(math.exp(1))) - 10, 46, None, ea)
    # the hug, P₀ → P₄, in step with the spoken terms
    if t < TERM_T[0]:
        return
    c, _, s = EXP.chain(t, [0, 1, 2, 3, 4], HUG_T)
    grow = ease_out(lin(t, TERM_T[0], TERM_T[0] + 0.6))
    EXP.error_band(fr, c, 0.6 * a * grow, ax=ax)
    EXP.copy(fr, c, a, ax=ax, glow=0.6 + 0.5 * s, reveal=grow, sym=True)
    for k, t0 in enumerate(HUG_T):
        u = lin(t, t0 + 0.3, t0 + 1.1)
        if 0 < u < 1:
            lo, hi = -T.hug_zone("exp", k + 1, side="left"), EXP_Z[k]
            fr.light_sweep(glow_path(EXP.copy_path(c, ax, lo, hi), 24), u, 0.55 * a)
    if t >= HUG_T[0]:
        lo, hi = zone_lr(np.exp, c)
        ba = a * smooth(lin(t, HUG_T[0], HUG_T[0] + 0.3)) * (1 - smooth(lin(t, b(1090), b(1090) + 0.4)))
        ch4.bracket(fr, ax, hi, 1, ba)
        ch4.bracket(fr, ax, lo, -1, ba)
        shown = min(EXP_Z, key=lambda z: abs(z - hi))
        hud.tabular(fr, f"{shown:.2f}", float(ax.px(hi)), float(ax.py(0)) - 49, 26, "copy", ba, glow=0.25)


def draw_ladder25(fr, t):
    a = 1 - smooth(lin(t, b(1056), b(1056) + 0.5))
    if t < ROW_T[0] - 0.1 or a <= 0.003:
        return
    rows = []
    for k in range(5):
        ra = smooth(lin(t, ROW_T[k], ROW_T[k] + 0.3))
        fill = smooth(lin(t, FILL_T[k], FILL_T[k] + 0.2))
        gone = lin(t, FLY_T[k], FLY_T[k] + 0.01) > 0  # the 1 has left for the recipe
        val = tc("result", "1") if fill > 0 and not gone else None
        rows.append((label(k), val, ra, fill))
    float_rows(fr, LAD_X, LAD_Y, rows, a, w=LAD_W, size=LAD_S, row_h=LAD_H)


FLY_T = [b(1053) + 0.14 * k for k in range(5)]
FLY = 0.6


def draw_series(fr, t):
    """FORM5 -> the 1s fly in (FILLED) -> CLEAN, terms lit one by one -> ONES -> FRACS -> FRACS = e."""
    if t < b(1051):
        return
    a = smooth(lin(t, b(1051), b(1051) + 0.4)) * (1 - smooth(lin(t, b(1149), b(1149) + 0.3)))
    fill = lin(t, FLY_T[0], FLY_T[-1] + FLY)
    clean = lin(t, b(1061), b(1062) + 0.3)
    if fill < 1:
        typmath.morph(fr, FORM5, FILLED, fill, SX, SY, SS * 0.92 + SS * 0.08 * fill, a, glow=0.15)
        cs = typmath.glyph_centers(FILLED, SX, SY, SS)
        for k, t0 in enumerate(FLY_T):
            u = lin(t, t0, t0 + FLY)
            if 0 < u < 1:
                (sx, sy), (dx, dy) = value_center(k), cs[ONE_SLOTS[k]]
                e = ease_io(u)
                x, y = sx + (dx - sx) * e, sy + (dy - sy) * e - 90 * math.sin(math.pi * e)
                typmath.draw(
                    fr, tc("result", "1"), x, y, LAD_S + (SS - LAD_S) * e, None, a * (1 - smooth(fill)), glow=0.6
                )
        return
    if t < b(1090):
        if clean < 1:
            typmath.morph(fr, FILLED, CLEAN, clean, SX, SY, SS, a, glow=0.15)
            return
        alphas, glows = {}, {}
        dim = 0.7 * smooth(lin(t, b(1062) + 0.3, b(1062) + 0.6))
        for k, (rng, t0) in enumerate(zip(R_CLEAN, TERM_T)):
            lit = smooth(lin(t, t0, t0 + 0.3))
            for i in rng:
                alphas[i] = 1 - dim * (1 - lit)
                glows[i] = 0.8 * pulse(t, t0 + 0.3, 0.9)
        typmath.draw(fr, CLEAN, SX, SY, SS, None, a, alphas=alphas, glows=glows)
        return
    # S26A: every x becomes a blue 1, the powers of 1 fall away, and the sum is named e
    m1 = lin(t, b(1090), b(1091) + 0.5)
    m2 = lin(t, b(1095), b(1097) + 0.2)
    m3 = lin(t, b(1100) - 0.1, b(1100) + 0.5)
    if m2 <= 0:
        typmath.morph(fr, CLEAN, ONES, m1, SX, SY, SS, a, glow=0.2 + 0.4 * pulse(t, b(1094), 0.8))
    elif m3 <= 0:
        typmath.morph(fr, ONES, FRACS, m2, SX, SY, SS, a, glow=0.2)
    elif m3 < 1:
        typmath.morph(fr, FRACS, FRACS_E, m3, SX, SY, SS, a, glow=0.2)
    else:  # the term being added to the bar glows
        glows = {}
        for k, rng in enumerate(R_FRACS):
            g = max(pulse(t, LAND_T[j] + 0.2, 0.9) for j in range(len(LAND_T)) if min(j, 5) == k)
            for i in rng:
                glows[i] = 0.9 * g
        typmath.draw(fr, FRACS_E, SX, SY, SS, None, a, glows=glows)


# ------------------------------------------------------------------ S26 · the fraction bar

NL = Axes(0.0, 3.0, -1.0, 1.0, (200.0, 540.0, 1520.0, 200.0))  # y = 0 at 640
LAND_T = [b(1102), b(1104), b(1108), b(1111), b(1116), b(1121)] + [b(1139) + 0.13 * k for k in range(5)]
READ_T = [b(1102), b(1106), b(1109), b(1112), b(1117), b(1122)] + LAND_T[6:]
DECIMALS = [0, 0, 1, 3, 3, 4]  # as spoken: 1, 2, 2.5, 2.667, 2.708, 2.7167
FRACS_LAB = [tc("copy", "1")] * 2 + [tc("copy", f"1/{math.factorial(k)}") for k in range(2, 11)]
GROW = 0.35
LENS_C, LENS_R = (1120.0, 410.0), 165.0
LENS = TaylorStage("exp")  # only for its loupe
E_TRUE = f"{E} = {tc('result', '2.71828')} dots"


def reading(k):
    if k < 6:
        return f"{SUMS[k]:.{DECIMALS[k]}f}"
    return f"{math.floor(SUMS[k] * 1e7) / 1e7:.7f}"  # truncated: every shown digit is earned


def tip(t):
    """Sum so far, with the newest segment still growing; and how many segments have started."""
    s, n = 0.0, 0
    for k, t0 in enumerate(LAND_T):
        u = ease_out(lin(t, t0, t0 + GROW))
        if u <= 0:
            break
        s += u / math.factorial(k)
        n = k + 1
    return s, n


def mag(t):
    return 10 ** (1 + smooth(lin(t, b(1118), b(1118) + 0.7)) + 5 * ease_io(lin(t, b(1139), b(1143) + 0.4)))


def draw_bar(fr, ax, t, a, inside=False):
    y0 = float(ax.py(0))
    fr.line(ax.left - 400, y0, ax.right + 400, y0, "axis", 1.6, a)
    if inside:  # ticks at the lens's own scale
        hw = (ax.x1 - ax.x0) / 2
        step = 10 ** math.floor(math.log10(hw))
        k0 = math.floor(ax.x0 / step)
        for k in range(k0, k0 + int(2 * hw / step) + 2):
            fr.line(float(ax.px(k * step)), y0 + 10, float(ax.px(k * step)), y0 + 24, "axis", 1.2, a)
    else:
        for k in range(4):
            fr.line(float(ax.px(k)), y0 + 12, float(ax.px(k)), y0 + 30, "axis", 1.6, a)
            typmath.draw(fr, str(k), float(ax.px(k)), y0 + 62, 30, "muted", a)
    # the lime ghost tick at e, breathing
    ea = a * smooth(lin(t, b(1100), b(1100) + 0.4)) * (0.55 + 0.25 * math.sin(2.4 * t))
    xe = float(ax.px(TRUE_E))
    fr.line(xe, y0 - 36, xe, y0 + 36, "result", 2.0, ea, glow=0.4)
    if not inside:
        typmath.draw(fr, E, xe + 22, y0 - 58, 40, None, ea / 0.8)
    s, n = tip(t)
    lo = 0.0
    for k in range(n):
        hi = lo + ease_out(lin(t, LAND_T[k], LAND_T[k] + GROW)) / math.factorial(k)
        x0, x1 = float(ax.px(lo)), float(ax.px(hi))
        if x1 > ax.left - 400 and x0 < ax.right + 400:
            x0, x1 = max(x0, ax.left - 400), min(x1, ax.right + 400)
            fr.rrect(x0, y0 - 7, x1 - x0, 14, 2, fill="copy", alpha=a * (1.0 if k % 2 == 0 else 0.7), glow=0.25)
            fr.line(x0, y0 - 9, x0, y0 + 9, "bg", 2.0, a)
        lo = hi
    if inside and t >= b(1129) - 0.1:  # the gap that is left after six terms
        ga = a * smooth(lin(t, b(1129), b(1129) + 0.4)) * (1 - smooth(lin(t, LAND_T[6], LAND_T[6] + 0.3)))
        x0, x1 = float(ax.px(SUMS[5])), float(ax.px(TRUE_E))
        fr.rrect(x0, y0 - 7, x1 - x0, 14, 2, fill="error", alpha=0.7 * ga, glow=0.4)
        hud.tabular(fr, f"{TRUE_E - SUMS[5]:.4f}", (x0 + x1) / 2, y0 - 34, 26, "error", ga, glow=0.3)
    return s, n


def draw_numberline(fr, t):
    a = smooth(lin(t, b(1098) + 0.2, b(1099) + 0.4)) * (1 - smooth(lin(t, b(1149), b(1149) + 0.3)))
    if a <= 0.003:
        return
    s, n = draw_bar(fr, NL, t, a)
    y0 = float(NL.py(0))
    # fraction labels over the visible segments; the newest one rides in the lens once they get thin
    lo = 0.0
    for k in range(min(n, 4)):
        hi = lo + 1 / math.factorial(k)
        fa = a * smooth(lin(t, LAND_T[k], LAND_T[k] + 0.3)) * (1.0 if k == n - 1 else 0.4)
        typmath.draw(fr, FRACS_LAB[k], float(NL.px((lo + hi) / 2)), y0 - 50, 36, None, fa)
        lo = hi
    # the lens follows the tip
    open_ = ease_out(lin(t, b(1113), b(1113) + 0.45))
    if open_ > 0.01:
        r = LENS_R * open_ + 3 * math.sin(1.7 * t)
        center = (LENS_C[0] + 6 * math.sin(0.5 * t), LENS_C[1])
        m = mag(t)
        LENS.loupe(fr, (s, 0.0), m, center, r, lambda sub: draw_bar(fr, sub, t, a, inside=True), a, ax=NL, label=False)
        if n >= 5:
            k = n - 1
            fa = a * open_ * smooth(lin(t, LAND_T[k], LAND_T[k] + 0.2))
            typmath.draw(fr, FRACS_LAB[k], center[0], center[1] - r * 0.55, 34, None, fa)
        hud.tabular(
            fr,
            f"×{10 ** round(math.log10(m)):,}",
            center[0] - r - 24,
            center[1] + 8,
            24,
            "muted",
            a * open_,
            align="right",
        )
    # the running sum, locking in lime
    k = max((i for i, t0 in enumerate(READ_T) if t >= t0), default=-1)
    if k >= 0:
        s_txt = reading(k)
        force = None
        if t >= LAND_T[6]:  # S27A: the seven decimals lock one by one on "seven decimal places are correct"
            step = lin(t, b(1143), b(1148))
            force = 4 + math.ceil(5 * step) if step > 0 else 4
        g = lin(t, READ_T[k], READ_T[k] + 0.3)
        if force is not None and 0 < lin(t, b(1143), b(1148)) < 1:
            g = (5 * lin(t, b(1143), b(1148))) % 1
        pop = 1 + 0.06 * pulse(t, READ_T[k], 0.3)
        lock(fr, s_txt, "2.718281828", 960, 870, 80 * pop, a, glint=g, force=force)
    ta = a * smooth(lin(t, b(1123) + 0.1, b(1123) + 0.5))
    if ta > 0.003:
        typmath.draw(fr, E_TRUE, 960, 960, 46, None, ta, glow=0.2 + 0.5 * pulse(t, b(1129), 0.8))
        if t >= b(1129):
            w, _ = typmath.size_of(E_TRUE, 46)
            box = skia.Path()
            box.addRect(skia.Rect.MakeXYWH(960 - w / 2, 930, w, 60))
            fr.light_sweep(box, lin(t, b(1129) + 0.4, b(1129) + 1.4), 0.7 * ta)
    # S27A counter
    ca = a * smooth(lin(t, b(1132), b(1132) + 0.3))
    if ca > 0.003:
        nn = 5 + max(0, sum(t >= t0 for t0 in LAND_T[6:]))
        typmath.draw(
            fr,
            f"{tc('x', 'n')} = {nn}",
            1440,
            860,
            50,
            None,
            ca,
            align="left",
            glow=0.4 * pulse(t, LAND_T[nn], 0.3) if nn > 5 else 0.0,
        )
        if nn == 5:  # "after just six terms"
            fr.text(
                "6 terms",
                1442,
                920,
                "sans",
                28,
                500,
                "muted",
                ca * (1 - smooth(lin(t, LAND_T[6] - 0.3, LAND_T[6]))),
                align="left",
            )


# ------------------------------------------------------------------ S27B/C · the race, then 1/n!

NS = np.arange(1, 11)
BASE, TOP = 900.0, 170.0
SLOT = [430.0 + 124.0 * (n - 1) for n in NS]
BAR_W = 34.0
LIN_PX = 620.0  # 1/n! bars: a height of 1 is 620 px


def decades(t):
    return 4.2 + 2.8 * ease_io(lin(t, b(1157), b(1158) + 0.9))


def draw_race(fr, t):
    a = smooth(lin(t, b(1149) + 0.15, b(1149) + 0.5))
    if a <= 0.003:
        return
    flip = ease_io(lin(t, b(1166), b(1167) + 0.6))
    settle = smooth(lin(t, b(1173), b(1173) + 0.5))
    dpx = (BASE - TOP) / decades(t)
    ga = a * (1 - flip)
    for d in range(8):  # decade grid
        y = BASE - d * dpx
        if y < TOP - 4:
            break
        fr.line(290, y, 1640, y, "grid" if d else "axis", 1.0 if d else 1.6, ga if d else a)
        if d:
            typmath.draw(fr, f"10^{d}", 320, y, 24, "muted", ga, align="right")
    for i, n in enumerate(NS):
        x = SLOT[i]
        typmath.draw(fr, str(n), x, BASE + 34, 26, "muted", a)
        # 2ⁿ in muted ink
        u2 = ease_out(lin(t, b(1152) + 0.06 * i, b(1152) + 0.06 * i + 0.8))
        h2 = max(2.0, math.log10(2**n) * dpx * u2)
        if u2 > 0:
            fr.rrect(x - BAR_W - 4, BASE - h2, BAR_W, h2, 3, fill="muted", alpha=0.55 * ga)
        # n! in magenta: rockets, then flips to 1/n!
        uf = back(min(1.0, lin(t, b(1154) + 0.08 * i, b(1154) + 0.08 * i + 0.7)), 1.2)
        hlog = max(2.0, math.log10(math.factorial(n)) * dpx * uf)
        hlin = max(1.0, LIN_PX / math.factorial(n))
        hf = hlog + (hlin - hlog) * flip
        if uf > 0 or flip > 0:
            fr.rrect(
                x + 4, BASE - hf, BAR_W, hf, 3, fill="fact", alpha=a * (1 - 0.65 * settle), glow=0.3 * (1 - settle)
            )
    # direct labels instead of a legend
    la = a * smooth(lin(t, b(1154) + 0.6, b(1154) + 1.0))
    x10 = SLOT[-1]
    h2 = math.log10(2**10) * dpx
    typmath.draw(fr, "2^n", x10 - BAR_W / 2 - 4, BASE - h2 - 34, 30, "muted", la * (1 - flip))
    yf = BASE - math.log10(math.factorial(10)) * dpx
    if flip <= 0:
        typmath.draw(fr, F("n!"), x10 + 4 + BAR_W / 2, yf - 34, 34, None, la)
    else:
        typmath.morph(
            fr,
            F("n!"),
            f"1/{F('n!')}",
            flip,
            x10 + 4 + BAR_W / 2,
            yf - 34,
            34,
            la * (1 - flip),
            b_cx=SLOT[0] + 90,
            b_cy=BASE - LIN_PX - 10,
        )
        typmath.draw(fr, f"1/{F('n!')}", SLOT[0] + 90, BASE - LIN_PX - 10, 34, None, la * flip * (1 - 0.6 * settle))
    # "10 factorial is already more than 3.5 million"
    ca = a * smooth(lin(t, b(1163), b(1163) + 0.25)) * (1 - flip)
    if ca > 0.003:
        v = math.factorial(10) * ease_out(lin(t, b(1163), cue(1164) + 0.2))
        hud.tabular(
            fr, f"10! = {round(v):,}", x10 - 40, max(TOP + 20, yf - 92), 44, "fact", ca, align="right", glow=0.3
        )
        fr.glint(x10 - 50, yf - 104, 70, ca * pulse(t, cue(1164) + 0.2, 0.5))
    # the running sum lands flat on e by n = 5
    if settle > 0:
        ye = BASE - (TRUE_E - 1) / (TRUE_E - 1) * 560
        fr.dashed([360.0, 1640.0], [ye, ye], "result", 1.6, 0.6 * a * settle, on=10, off=8)
        typmath.draw(fr, E, 1672, ye, 40, None, a * settle)
        xs = [SLOT[0] - 124] + SLOT
        ys = [BASE - (SUMS[n] - 1) / (TRUE_E - 1) * 560 for n in range(11)]
        r = ease_io(lin(t, b(1173), b(1175) + 0.4))
        m = r * 10
        k = int(m)
        px = xs[: k + 1] + ([xs[k] + (xs[k + 1] - xs[k]) * (m - k)] if k < 10 else [])
        py = ys[: k + 1] + ([ys[k] + (ys[k + 1] - ys[k]) * (m - k)] if k < 10 else [])
        fr.poly(px, py, "result", 3.0, a, glow=0.6)
        for x, y in zip(xs[: k + 1], ys[: k + 1]):
            fr.glow_dot(x, y, 5.0, "result", a, 0.7)
        path = skia.Path()
        path.moveTo(xs[0], ys[0])
        for x, y in zip(xs[1:], ys[1:]):
            path.lineTo(x, y)
        fr.light_sweep(glow_path(path, 18), lin(t, b(1176), b(1176) + 0.9), 0.7 * a)


# ------------------------------------------------------------------ assembly


def draw_handoff(fr, t):
    a = 1 - smooth(lin(t, START, START + 0.7))
    if a > 0.003:
        with layer_alpha(fr, a):
            ch4.draw_stage(fr, t)
            ch4.draw_s22_text(fr, t)


def draw_one(t, size):
    fr = Frame(size)
    draw_handoff(fr, t)
    draw_exp(fr, t)
    draw_title(fr, t)
    if S25 <= t < b(1057):
        draw_ladder25(fr, t)
    draw_series(fr, t)
    draw_numberline(fr, t)
    if t >= b(1149):
        draw_race(fr, t)
    hud.eyebrow(fr, t, "05 · e FROM FRACTIONS", START + 0.2)
    fr.zoom_blur(0.2 * (1 - ease_out(lin(t, b(1149), b(1149) + 0.45))) * (t >= b(1149)))
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


SCENES = {
    "S24": (S24, S25, [363.9, 369.4, 376.2]),
    "S25": (S25, S26, [382.6, 390.9, 396.4]),
    "S26": (S26, S27, [400.6, 404.9, 409.9, 418.4, 422.3]),
    "S27": (S27, END, [425.8, 430.8, 435.5, 439.0, 443.4]),
}
OFFSET = START
DURATION = END - START
STILLS = [s for _, _, st in SCENES.values() for s in st]
