"""CHAPTER 3 · WHY FACTORIALS, 04:11.520 – 04:45.920 (cue #691 "2," → #778 "Now,").

S18  Two, twenty-four    the denominators 2 and 24 lift out of P₄ and enlarge in magenta, breathing through the pause ->
                         they step into a staircase -> 2 = 2 × 1 (hand-timed #696–700), 24 = 4 × 3 × 2 × 1 factor by factor
                         -> both collapse to 2! and 4!, the ! glints -> 4, 3, 2, 1 light down a staircase -> the muted
                         row 1! … 5! = 1 2 6 24 120 underneath
S19  The exponent drops  x⁵ alone -> d/dx slides in -> the 5 falls slowly to the front: 5x⁴ -> the fast cascade
                         20x³, 60x², 120x, 120 while every dropped exponent falls into the row 5 × 4 × 3 × 2 × 1 ->
                         5! = 120 -> x⁵/5! runs to 120/120, both struck, 1 -> x⁴/24 lights f⁗(0) = +1 and nothing else

Clean frame: formulas on black, no pills or cards. One FunctionSource on the narration clock (cues.beat).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from components.fx import layer_alpha
from components.ladder import float_rows, label, value_token
from components.moves import drop, zoom_about
from cues import AUDIO, beat, cue
from theme import THEME, H, W

from faceless_champ.draw import Frame, ease_io, ease_out, hud, lin, pulse, smooth
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc
from scenes import ch2_copy as ch2

START = cue(691)  # 251.52 "2, 24."
END = cue(778)  # 285.92 "Now, we can write the whole trick"

b = beat

S18, S19 = START, cue(724)
X = tc("x", "x")
TIMES = tc("fact", "times")


def F(s):
    return tc("fact", s)


# ------------------------------------------------------------------ S18A · the denominators lift out of P₄

P4 = ch2.FORMULAS[3][1]
_P4W = typmath.size_of(P4, ch2.FS)[0]
_P4C = typmath.glyph_centers(P4, ch2.FX + _P4W / 2, ch2.FY, ch2.FS)
_MAG = [i for i, g in enumerate(typmath.glyphs(P4)[0]) if g.color.lower() == "#ff3d9a"]  # 2, then 2 4
DEN_SRC = [_P4C[_MAG[0]], tuple(np.mean([_P4C[i] for i in _MAG[1:3]], axis=0))]
DEN = [F("2"), F("24")]
DEN_T = [b(691), b(692)]
DEN_MID = [(700.0, 470.0), (1220.0, 470.0)]

ROW_X, ROW_Y, ROW_S = 300.0, (360.0, 600.0), 110.0
E1 = f"{F('2')} = 2 {TIMES} 1"
E2 = f"{F('24')} = 4 {TIMES} 3 {TIMES} 2 {TIMES} 1"
G1 = f"{F('2')} = {F('2!')}"
G2 = f"{F('24')} = {F('4!')}"
E1_T = {1: b(697), 2: b(698), 3: b(699), 4: b(700)}  # glyph -> when it sets ("Two is two times one")
E2_T = {2: b(702), 3: b(703), 4: b(704), 5: b(705), 6: b(706), 7: b(707), 8: b(708), 9: b(709)}


def row_cx(expr):
    return ROW_X + typmath.size_of(expr, ROW_S)[0] / 2


def lhs_center(expr, y, n):
    """Centre of the first ``n`` glyphs (the magenta left-hand side) when the row is left-aligned."""
    cs = typmath.glyph_centers(expr, row_cx(expr), y, ROW_S)[:n]
    return tuple(np.mean(cs, axis=0))


LHS_DST = [lhs_center(E1, ROW_Y[0], 1), lhs_center(E2, ROW_Y[1], 2)]


def draw_handoff(fr, t):
    """Chapter 2's last frame, fading as the denominators leave it."""
    a = 1 - smooth(lin(t, START, START + 0.8))
    if a <= 0.003:
        return
    with layer_alpha(fr, a):
        ch2.draw_stage(fr, t)
        ch2.draw_ladder(fr, t)
    alphas = {i: 0.0 for i in _MAG}
    typmath.draw(fr, P4, ch2.FX, ch2.FY, ch2.FS, None, a, alphas=alphas, align="left")


def draw_s18(fr, t):
    if t >= S19 + 0.6:
        return
    out = 1 - smooth(lin(t, b(724), b(724) + 0.5))
    stair = ease_io(lin(t, b(693), b(695) + 0.5))  # "Notice the pattern": step into rows
    for k in range(2):
        u = ease_out(lin(t, DEN_T[k], DEN_T[k] + 0.7))
        if u <= 0:
            continue
        src, mid, dst = DEN_SRC[k], DEN_MID[k], LHS_DST[k]
        x = src[0] + (mid[0] - src[0]) * u + (dst[0] - mid[0]) * stair
        y = src[1] + (mid[1] - src[1]) * u - 120 * np.sin(np.pi * u) * (1 - stair) + (dst[1] - mid[1]) * stair
        size = ch2.FS * 0.7 + (150 - ch2.FS * 0.7) * u + (ROW_S - 150) * stair
        breathe = 0.35 + 0.25 * np.sin(2 * np.pi * (t - DEN_T[k]) / 1.6) * (1 - stair)
        if stair < 1:
            typmath.draw(fr, DEN[k], x, y, size, None, out, glow=breathe)
    if stair < 1:
        return
    # 18B · the products build on their words; 18C · they collapse into factorials
    for expr, g, y, sched, t_c in ((E1, G1, ROW_Y[0], E1_T, b(712)), (E2, G2, ROW_Y[1], E2_T, b(712) + 0.25)):
        u = lin(t, t_c, t_c + 0.6)
        if u <= 0:
            alphas = {i: smooth(lin(t, t0, t0 + 0.25)) for i, t0 in sched.items()}
            glows = {i: 0.9 * pulse(t, t0, 0.6) for i, t0 in sched.items()}
            typmath.draw(fr, expr, ROW_X, y, ROW_S, None, out, glow=0.25, alphas=alphas, glows=glows, align="left")
        else:
            gw = typmath.size_of(g, ROW_S)[0]
            glow = 0.25 + 0.9 * pulse(t, b(722), 1.2) * (g == G2)  # "below it": 4! = 24
            typmath.morph(fr, expr, g, u, row_cx(expr), y, ROW_S, out, glow=glow, b_cx=ROW_X + gw / 2)
            if u >= 1:
                bang = typmath.glyph_centers(g, ROW_X + gw / 2, y, ROW_S)[-1]
                fr.glint(*bang, 70.0, out * pulse(t, t_c + 0.5, 0.6), color="fact")
    draw_staircase(fr, t, out)
    draw_factorial_row(fr, t, out)


STEPS = [(1080.0 + 160.0 * k, 330.0 + 80.0 * k) for k in range(4)]
STEP_T = [b(716), b(717) + 0.25, b(719), b(721)]  # "4 multiplied by every whole number below it"


def draw_staircase(fr, t, out):
    a = out * smooth(lin(t, b(713), b(713) + 0.5))
    if a <= 0.003:
        return
    for k, ((x, y), t0) in enumerate(zip(STEPS, STEP_T)):
        lit = smooth(lin(t, t0, t0 + 0.3))
        fr.line(x - 70, y + 62, x + 90, y + 62, "frame", 1.2, a * (0.4 + 0.4 * lit))
        if k < 3:
            fr.line(x + 90, y + 62, x + 90, y + 142, "frame", 1.2, a * (0.4 + 0.4 * lit))
        typmath.draw(
            fr,
            str(4 - k),
            x,
            y,
            92,
            "fact" if lit > 0.5 else "muted",
            a * (0.45 + 0.55 * lit),
            glow=0.8 * pulse(t, t0, 0.6),
        )
        if k < 3:
            ta = a * smooth(lin(t, STEP_T[k + 1] - 0.2, STEP_T[k + 1]))
            typmath.draw(fr, TIMES, x + 80, y + 40, 44, None, ta)


def draw_factorial_row(fr, t, out):
    a = out * 0.4 * smooth(lin(t, b(713) + 0.6, b(713) + 1.2))
    if a <= 0.003:
        return
    for n, v in zip(range(1, 6), (1, 2, 6, 24, 120)):
        x = 560 + 200 * (n - 1)
        typmath.draw(fr, f"{n}!", x, 860, 44, "muted", a)
        typmath.number(fr, str(v), x, 930, 40, "muted", a)


# ------------------------------------------------------------------ S19 · the exponent drops

MX, MY, MS = 960.0, 470.0, 160.0
M = [f"{X}^5", f"{F('5')} {X}^4", f"{F('20')} {X}^3", f"{F('60')} {X}^2", f"{F('120')} {X}", F("120")]
EXP_IDX = [1, 2, 3, 3, None]  # exponent glyph of M[k] (None: x's invisible 1)
SLOW_T = cue(746) - 0.8  # the first drop takes 0.8 s and lands on "front"
FAST = [cue(749) + 0.0, cue(749) + 0.38, cue(749) + 0.76, cue(749) + 1.14]  # "Take enough derivatives"
FAST_DUR = 0.38
BR = f"{F('5')} {TIMES} {F('4')} {TIMES} {F('3')} {TIMES} {F('2')} {TIMES} {F('1')}"
BR_X, BR_Y, BR_S = 960.0, 800.0, 90.0
BR_DIGIT = [0, 2, 4, 6, 8]
FIVE_T = cue(749) - 0.4
BR_SUM = f"{F('5!')} = 120"
CANCEL = f"{F('120')} / {F('120')}"
QUOT = f"{X}^5 / {F('5!')}"


def main_state(t):
    """(index into M, morph u from the previous state) for the main row."""
    if t < SLOW_T + 0.8:
        return 0, 1.0
    k = 1
    for i, t0 in enumerate(FAST):
        if t >= t0 + FAST_DUR:
            k = i + 2
    t_last = SLOW_T + 0.8 if k == 1 else FAST[k - 2] + FAST_DUR
    return k, lin(t, t_last, t_last + 0.22)


def exp_center(k):
    cs = typmath.glyph_centers(M[k], MX, MY, MS)
    if EXP_IDX[k] is None:
        return cs[-1][0] + MS * 0.22, cs[-1][1] - MS * 0.35
    return cs[EXP_IDX[k]]


def draw_s19(fr, t):
    if t < S19:
        return
    a = smooth(lin(t, S19 + 0.1, S19 + 0.6))
    end = 1 - smooth(lin(t, b(768), b(768) + 0.4))
    push = 1 + 0.05 * ease_io(lin(t, S19, b(768)))
    with zoom_about(fr, MX, 600, push):
        draw_main(fr, t, a * end)
        draw_bottom_row(fr, t, a * end)
    draw_delivers(fr, t)


def draw_main(fr, t, a):
    if a <= 0.003:
        return
    # d/dx slides in on "derivative of a power", leaves once it has done its work
    da = a * smooth(lin(t, b(737), b(737) + 0.4)) * (1 - smooth(lin(t, b(748), b(748) + 0.4)))
    if da > 0.003:
        slide = 60 * (1 - ease_out(lin(t, b(737), b(737) + 0.5)))
        typmath.draw(fr, f"(d)/(d {X})", MX - 260 - slide, MY, 96, None, da)
    q = lin(t, b(761), b(761) + 0.5)  # 19C: the same cascade on x⁵/5!
    if q > 0:
        draw_quotient(fr, t, a, q)
        return
    if t < SLOW_T:
        typmath.draw(fr, M[0], MX, MY, MS, None, a, glow=0.2)
        return
    u = drop(fr, t, SLOW_T, exp_center(0), typmath.glyph_centers(M[1], MX, MY, MS)[0], "5", MS * 0.6, MS, a, dur=0.8)
    if u < 1:
        typmath.draw(fr, M[1], MX, MY, MS, None, a, alphas={0: 0.0, 2: u}, glow=0.2)
        return
    sp = pulse(t, b(748), 0.6)  # "multiplies"
    if sp > 0:
        fr.glow_dot(*typmath.glyph_centers(M[1], MX, MY, MS)[0], 10 + 26 * sp, "fact", 0.5 * sp * a, 1.0)
    k, mu = main_state(t)
    glow = 0.25 + 0.8 * smooth(lin(t, b(755), b(755) + 0.5)) * (k == 5)
    if mu < 1 and k > 1:
        typmath.morph(fr, M[k - 1], M[k], mu, MX, MY, MS, a, glow=glow)
    else:
        typmath.draw(fr, M[k], MX, MY, MS, None, a, glow=glow)


def draw_quotient(fr, t, a, q):
    if q < 1:
        typmath.morph(fr, M[5], QUOT, q, MX, MY, MS, a)
        return
    r = lin(t, b(761) + 0.75, b(761) + 1.25)
    gone = lin(t, b(767), b(767) + 0.5)
    if gone > 0:
        typmath.morph(fr, CANCEL, "1", gone, MX, MY, MS, a, glow=0.3 + 0.6 * gone)
    else:
        typmath.morph(fr, QUOT, CANCEL, r, MX, MY, MS, a)
    s = ease_out(lin(t, b(765), b(765) + 0.35)) * (1 - smooth(gone))  # "cancels": both 120s strike out
    if s > 0:
        w, h = typmath.size_of(CANCEL, MS)
        for dy in (-h * 0.27, h * 0.27):
            x0, y0 = MX - w * 0.42, MY + dy + 22
            fr.line(x0, y0, x0 + w * 0.84 * s, y0 - 44 * s, "ink", 3.0, a * 0.9, glow=0.3)


def draw_bottom_row(fr, t, a):
    if a <= 0.003 or t < FIVE_T:
        return
    q = 1 - smooth(lin(t, b(761), b(761) + 0.4))
    a *= q
    cs = typmath.glyph_centers(BR, BR_X, BR_Y, BR_S)
    landed = {}
    src5 = typmath.glyph_centers(M[1], MX, MY, MS)[0]
    landed[0] = drop(fr, t, FIVE_T, src5, cs[0], "5", MS * 0.7, BR_S, a, dur=FAST_DUR)
    for i, t0 in enumerate(FAST):
        landed[i + 1] = drop(
            fr, t, t0, exp_center(i + 1), cs[BR_DIGIT[i + 1]], str(4 - i), MS * 0.5, BR_S, a, dur=FAST_DUR
        )
    c = lin(t, b(755), b(755) + 0.7)  # "multiplied all of those exponents together"
    if c > 0:
        typmath.morph(fr, BR, BR_SUM, c, BR_X, BR_Y, BR_S, a, glow=0.3 + 0.6 * smooth(c))
        return
    alphas = {}
    for i, u in landed.items():
        alphas[BR_DIGIT[i]] = 1.0 if u >= 1 else 0.0
        if i:
            alphas[BR_DIGIT[i] - 1] = smooth(min(1.0, u * 2))
    typmath.draw(fr, BR, BR_X, BR_Y, BR_S, None, a, alphas=alphas, glow=0.2)


# ------------------------------------------------------------------ S19C · each term delivers exactly its amount

LAD_X, LAD_Y = 1300.0, 300.0
COS_D = [1, 0, -1, 0, 1]
TERM = f"{X}^4 / {F('24')}"


def cos_rows(t, lit):
    rows = []
    for k, v in enumerate(COS_D):
        s, tok = value_token(v)
        ra = 1.0 if k == 4 else 1 - 0.7 * lit
        rows.append((label(k), tc(tok, s), ra, lit if k == 4 else 0.0))
    return rows


def draw_delivers(fr, t):
    a = smooth(lin(t, b(768) + 0.2, b(768) + 0.7))
    if a <= 0.003:
        return
    lit = smooth(lin(t, b(771), b(771) + 0.6))
    float_rows(fr, LAD_X, LAD_Y, cos_rows(t, lit), a)
    tx, ty = 700.0, 300.0 + 64 * 4.5
    typmath.draw(fr, TERM, tx, ty, 96, None, a, glow=0.2 + 0.6 * lit)
    w = typmath.size_of(TERM, 96)[0]
    x0, x1 = tx + w / 2 + 30, LAD_X - 6
    u = ease_out(lin(t, b(771), b(771) + 0.7))
    if u > 0:
        fr.line(x0, ty, x0 + (x1 - x0) * u, ty, "copy", 2.0, a * 0.9, glow=0.6)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_handoff(fr, t)
    draw_s18(fr, t)
    draw_s19(fr, t)
    hud.eyebrow(fr, t, "03 · WHY FACTORIALS", START + 0.2)
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


SCENES = {
    "S18": (S18, S19, [253.4, 260.95, 266.5]),
    "S19": (S19, END, [273.6, 278.8, 281.9, 284.6]),
}
OFFSET = START
DURATION = END - START
STILLS = [s for _, _, st in SCENES.values() for s in st]
