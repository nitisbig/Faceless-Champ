"""CHAPTER 2 · COPYING A CURVE, 02:12.880 – 04:11.520 (cue #371 "Let's" → #691 "2,").

S11  The cosine hill           the bare axes from Chapter 1 settle -> ink cos x draws -> a blue probe drops to x = 0,
                               the camera leans in -> the top of the hill lights, `1` on the y axis -> two shoulder arrows
S12  Attempt 1: a constant     the graph slides left, the derivative ladder floats in at the right (no card) -> f(0) = +1
                               -> the gold flat line hugs out of 0 -> a lens on (0, 1) -> brackets ±0.14 -> the probe walks
                               to 1.5, the violet gap and its size 0.93 -> the whole gap shades violet -> the line pulses flat
S13  Attempt 2: the slope      a tangent rides up to the top, its rise/run triangle collapses flat -> f′(0) = 0 -> the gold
                               line flashes on the ink tangent -> P(x) = 1 + 0·x, and the 0·x fades to a ghost
S14  The bend                  a curvature comb grows along the hill (the flat line has none) -> a gold ghost x² floats in
S15  How much x²?              three stacked plots cos -> −sin -> −cos: f″(0) = −1 (teal) -> x² -> 2x -> 2 by exponent drops
                               -> the target −1 -> −½x² and the check −½ · 2 = −1
S16  The parabola hugs         P(x) = 1 − x²/2 and the hug P₀ -> P₂ -> combs coincide at 0 -> brackets ±0.14 -> ±0.70
S17  The fourth derivative     f‴(0) = 0 struck, f⁗(0) = +1 -> x⁴ -> 4 -> 4·3 -> 4·3·2 -> 4·3·2·1 = 24 on the spoken digits
                               -> x⁴/24 -> P(x) = 1 − x²/2 + x⁴/24 and the hug P₂ -> P₄, brackets ±1.40

Clean frame: no pills, no glass cards, no framed panels. The ladder rows float; formulas are plain Typst, colored by role.
One FunctionSource on the narration clock; beats land 0.15 s before their word cue (cues.beat).
"""

from __future__ import annotations

import math
from itertools import pairwise
from pathlib import Path

import numpy as np
import skia
from components.fx import glow_path
from components.ladder import Ladder
from components.motion import spring
from components.moves import DROP, comb, drop, zoom_about
from components.stage import Axes, TaylorStage
from cues import AUDIO, beat, cue
from theme import THEME, H, W

from faceless_champ.draw import Frame, ease_io, ease_out, hud, lin, pulse, smooth
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc

START = cue(371)  # 132.88 "Let's try it with the cosine curve"
END = cue(691)  # 251.52 "2, 24, …" (Chapter 3)

b = beat

S11, S12, S13, S14, S15, S16, S17 = START, cue(405), cue(457), cue(495), cue(519), cue(595), cue(624)

X = tc("x", "x")
MINUS, PLUS = tc("minus", "-"), tc("plus", "+")


def F(s):
    return tc("fact", s)


# ------------------------------------------------------------------ the stage and its camera

COS = TaylorStage("cos", view=(-4.0, 4.0, -1.6, 1.6), rect=(96.0, 150.0, 1728.0, 780.0))
FULL = (96.0, 150.0, 1728.0, 780.0)
LEFT = (96.0, 150.0, 1180.0, 780.0)  # the ladder takes the right third from S12 on
# (time, rect, x half-width, y half-height, y centre); eased between keys
CAM = [
    (START, (96.0, 200.0, 1728.0, 680.0), 5.859, 1.767, 0.0),  # Chapter 1's last view, bare axes
    (START + 0.9, FULL, 4.0, 1.6, 0.0),
    (b(382), FULL, 4.0, 1.6, 0.0),
    (b(384) + 0.6, FULL, 3.08, 1.23, 0.15),  # "X equals 0": lean in 1.3×
    (b(405), FULL, 3.08, 1.23, 0.15),
    (b(405) + 0.9, LEFT, 2.1, 1.23, 0.15),  # same scale, room for the ladder
    (b(605), LEFT, 2.1, 1.23, 0.15),
    (b(610) + 0.4, LEFT, 2.73, 1.6, 0.0),  # "Look at it on the graph": ease back
]


def stage_ax(t):
    if t <= CAM[0][0]:
        k = CAM[0]
        return Axes(-k[2], k[2], k[4] - k[3], k[4] + k[3], k[1])
    for (t0, r0, x0, y0, c0), (t1, r1, x1, y1, c1) in pairwise(CAM):
        if t <= t1:
            u = ease_io(lin(t, t0, t1))
            break
    else:
        (t0, r0, x0, y0, c0), (t1, r1, x1, y1, c1), u = CAM[-2], CAM[-1], 1.0
    rect = tuple(a + (b_ - a) * u for a, b_ in zip(r0, r1))
    xh, yh, yc = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, c0 + (c1 - c0) * u
    tau = t - START  # two slow, incommensurate drifts: the camera is never quite at rest
    breathe = 1 + 0.012 * math.sin(2 * math.pi * tau / 13.0) + 0.007 * math.sin(2 * math.pi * tau / 5.3)
    return Axes(-xh * breathe, xh * breathe, yc - yh * breathe, yc + yh * breathe, rect)


def stage_alpha(t):
    """The graph steps back to a ghost while a derivation has the floor (S15, S17B)."""
    away = smooth(lin(t, b(519), b(519) + 0.6)) * (1 - smooth(lin(t, b(595), b(595) + 0.6)))
    away = max(away, smooth(lin(t, b(651), b(651) + 0.5)) * (1 - smooth(lin(t, b(677), b(677) + 0.6))))
    return 1 - 0.88 * away


# ------------------------------------------------------------------ the copy: P₀ -> P₂ -> P₄

HUG_DEG = [0, 2, 4]
HUG_T = [b(603), b(690)]
ZONES = [COS.zone(n) for n in HUG_DEG]  # 0.141, 0.702, 1.397
BRACKET_T = [b(621), b(690)]


def copy_c(t):
    c, _, s = COS.chain(t, HUG_DEG, HUG_T)
    return c, s


def bracket_r(t):
    r = ZONES[0]
    for k, t0 in enumerate(BRACKET_T):
        r += (ZONES[k + 1] - ZONES[k]) * spring(t, t0)
    return r


def brackets(fr, ax, r, alpha):
    """Gold hug brackets with a bare readout above the right one (no pill)."""
    if alpha <= 0.003:
        return
    COS.brackets(fr, r, alpha, ax, label=False)
    y = min(max(float(ax.py(0.0)), ax.top), ax.bottom) - 23
    shown = min(ZONES, key=lambda z: abs(z - r))  # read the settled zone, not the spring's overshoot
    hud.tabular(fr, f"±{shown:.2f}", float(ax.px(r)), y - 26, 26, "copy", alpha, glow=0.25)


# ------------------------------------------------------------------ ladder (rows float, no card)

LADDER = Ladder(x=1360.0, y=200.0, rows=5, name="f", w=440.0)
FILLS = [(b(422), 1), (b(481), 0), (b(547), -1), (b(634), 0), (b(643), 1)]
STRUCK = {3: b(637)}
FOCUS = [(0, b(415), b(429)), (1, b(462), b(486)), (2, b(534), b(549)), (3, b(627), b(638)), (4, b(640), b(656))]


def draw_ladder(fr, t):
    a = smooth(lin(t, b(405) + 0.3, b(405) + 1.0))
    if a <= 0.003:
        return
    slide = 60 * (1 - ease_out(lin(t, b(405) + 0.3, b(405) + 1.1)))
    lad = Ladder(x=LADDER.x + slide, y=LADDER.y, rows=5, name="f", w=LADDER.w)
    lad.draw(fr, t, fills=FILLS, struck=STRUCK, alpha=a, card=False)
    fr.line(lad.x + 12, lad.row_y(0) - 32, lad.x + 12, lad.row_y(4) + 32, "line", 1.0, 0.7 * a)
    for k, t0, t1 in FOCUS:  # the row being matched gets a gold mark on the rail
        f = smooth(lin(t, t0, t0 + 0.3)) * (1 - smooth(lin(t, t1, t1 + 0.4)))
        if f > 0.003:
            fr.glow_dot(lad.x + 12, lad.row_y(k), 5.0, "copy", a * f, 1.0)


# ------------------------------------------------------------------ formula, top left

FORMULAS = [  # (appears, expression); each replaces the one before
    (b(428), f"P({X}) = 1"),
    (b(492), f"P({X}) = 1 {PLUS} 0 dot {X}"),
    (b(599), f"P({X}) = 1 {MINUS} {X}^2 / {F('2')}"),
    (b(684), f"P({X}) = 1 {MINUS} {X}^2 / {F('2')} {PLUS} {X}^4 / {F('24')}"),
]
GHOST = (6, 7, 8, 9)  # the "+ 0·x" of P(x) = 1 + 0·x
FX, FY, FS = 128.0, 96.0, 52.0


def draw_formula(fr, t):
    hide = smooth(lin(t, b(519), b(519) + 0.4)) * (1 - smooth(lin(t, b(599) - 0.4, b(599))))
    k = max((i for i, (t0, _) in enumerate(FORMULAS) if t >= t0), default=-1)
    if k < 0 or hide >= 0.997:
        return
    a = (1 - hide) * smooth(lin(t, FORMULAS[0][0], FORMULAS[0][0] + 0.5))
    t0, expr = FORMULAS[k]
    u = lin(t, t0, t0 + 0.6)
    w = typmath.size_of(expr, FS)[0]
    if k in (1, 3) and u < 1:
        prev = FORMULAS[k - 1][1]
        typmath.morph(fr, prev, expr, u, FX + typmath.size_of(prev, FS)[0] / 2, FY, FS, a, b_cx=FX + w / 2)
        return
    alphas = {}
    if k == 1:  # "nothing changes yet": the new term fades to a ghost
        g = 1 - 0.8 * smooth(lin(t, b(493), b(494) + 0.3))
        alphas = {i: g for i in GHOST}
    reveal = lin(t, t0, b(604)) if k == 2 else 1.0
    glow = 0.2 + 0.6 * pulse(t, b(678), 1.6) if k == 2 else 0.2
    typmath.draw(fr, expr, FX, FY, FS, None, a, glow=glow, reveal=reveal, alphas=alphas, align="left")


# ------------------------------------------------------------------ probe, tangent, combs


def probe_x(t):
    x = 1.5 * ease_io(lin(t, b(439), b(444) + 0.3))
    return x * (1 - ease_io(lin(t, b(457), b(461))))


def draw_stage(fr, t):
    ax = stage_ax(t)
    sa = stage_alpha(t)
    COS.static(fr, sa, ax=ax, labels=False)
    reveal = ease_io(lin(t, b(376), b(377) + 0.9))
    COS.original(fr, sa, reveal=reveal, ax=ax)
    c, s = copy_c(t)
    # S12C: the gap shades violet, then rests as a ghost; the hug shrinks it from S16 on
    band = smooth(lin(t, b(449), b(449) + 0.6)) * (1 - 0.55 * smooth(lin(t, b(457), b(461))))
    COS.error_band(fr, c, band * sa, ax=ax)
    born = ease_out(lin(t, b(428), b(428) + 0.8))
    flat = pulse(t, b(455), 0.9)
    p = COS.copy(fr, c, sa * smooth(born), ax=ax, glow=0.6 + 0.5 * s + 0.8 * flat, reveal=born, sym=True)
    if p is not None:
        for t0 in (b(621), b(690)):
            zp = COS.copy_path(c, ax, lo=-bracket_r(t), hi=bracket_r(t))
            fr.light_sweep(glow_path(zp, 24), lin(t, t0 + 0.3, t0 + 1.2), 0.6 * sa)
    brackets(fr, ax, bracket_r(t), sa * smooth(lin(t, b(437), b(437) + 0.3)))
    draw_probe(fr, t, ax, sa)
    draw_shoulders(fr, t, ax)
    draw_tangent(fr, t, ax, sa)
    draw_combs(fr, t, ax, sa)
    draw_lens(fr, t, ax, c)
    return ax


def draw_probe(fr, t, ax, sa):
    pa = sa * smooth(lin(t, b(382), b(382) + 0.4)) * (1 - smooth(lin(t, b(519), b(519) + 0.4)))
    if pa <= 0.003:
        return
    x = probe_x(t)
    COS.probe(fr, x, pa, ax=ax, drop=False)
    base = float(ax.py(0.0))
    top = float(ax.py(math.cos(x)))
    rise = ease_out(lin(t, b(382) + 0.2, b(384)))
    gold = pulse(t, b(415), 1.6)  # "match the height"
    fr.line(
        float(ax.px(x)),
        base,
        float(ax.px(x)),
        base + (top - base) * rise,
        fr.mix("x", "copy", gold),
        1.6 + 1.6 * gold,
        pa * 0.8,
        glow=0.6 * gold,
    )
    da = pa * smooth(lin(t, b(389), b(389) + 0.3))
    fr.glow_dot(float(ax.px(x)), top, 6.5 + 4 * pulse(t, b(389), 0.6), "x", da, 1.0)
    # "height of 1": the 1 on the y axis
    one = pa * smooth(lin(t, b(397), b(397) + 0.3))
    if one > 0.003:
        y1 = float(ax.py(1.0))
        x0 = float(ax.px(0.0))
        fr.line(x0 - 8, y1, x0 + 8, y1, "ink", 2.0, one)
        typmath.number(fr, "1", x0 - 30, y1, 34, "ink", one, glow=0.3 * pulse(t, b(397), 0.8))
    # S12C: the gap at the probe, and its size
    ga = pa * smooth(lin(t, b(441), b(441) + 0.3)) * (1 - smooth(lin(t, b(457), b(457) + 0.4)))
    if ga > 0.003 and x > 0.02:
        px, y_one = float(ax.px(x)), float(ax.py(1.0))
        fr.line(px, y_one, px, top, "error", 3.2, ga, glow=0.6)
        typmath.number(fr, f"{1 - math.cos(x):.2f}", px + 52, (y_one + top) / 2, 34, "error", ga)


def draw_shoulders(fr, t, ax):
    a = smooth(lin(t, b(401), b(401) + 0.3)) * (1 - smooth(lin(t, b(405), b(405) + 0.4)))
    if a <= 0.003:
        return
    grow = ease_out(lin(t, b(401), b(403) + 0.2))
    for s in (1, -1):
        xs = s * np.linspace(0.35, 0.35 + 0.95 * grow, 30)
        px, py = ax.px(xs), ax.py(np.cos(xs)) - 34  # just above the shoulder
        fr.poly(px, py, "ink", 2.2, a, glow=0.3)
        if grow > 0.05:
            hud.arrow_head(
                fr, float(px[-2]), float(py[-2]), float(px[-1]), float(py[-1]), "ink", a, size=14.0, glow=0.3
            )


def draw_tangent(fr, t, ax, sa):
    """S13: a tangent rides to the top of the hill; its rise/run triangle collapses flat."""
    a = sa * smooth(lin(t, b(470), b(470) + 0.3)) * (1 - smooth(lin(t, b(492), b(492) + 0.5)))
    if a <= 0.003:
        return
    x = -0.9 * (1 - ease_io(lin(t, b(470), b(477))))
    y, m = math.cos(x), -math.sin(x)
    flash = pulse(t, b(484), 1.0)
    L = 0.8
    x0, x1 = x - L, x + L
    fr.line(
        *ax.at(x0, y + m * (x0 - x)),
        *ax.at(x1, y + m * (x1 - x)),
        fr.mix("ink", "copy", flash),
        2.2,
        a,
        glow=0.3 + 0.8 * flash,
    )
    run = 0.5
    tri = skia.Path()
    tri.addPoly(
        [skia.Point(*ax.at(x, y)), skia.Point(*ax.at(x + run, y)), skia.Point(*ax.at(x + run, y + m * run))], True
    )
    fr.path_fill(tri, "light", 0.08 * a)
    fr.path_stroke(tri, "light", 1.4, 0.7 * a)
    fr.glow_dot(*ax.at(x, y), 6.0, "light", a, 0.9)


def draw_combs(fr, t, ax, sa):
    xs = np.linspace(-1.6, 1.6, 33)
    # S14: the hill has a bend, the flat line has none
    a = sa * smooth(lin(t, b(501), b(501) + 0.4)) * (1 - smooth(lin(t, b(519), b(519) + 0.4)))
    if a > 0.003:
        grow = ease_out(lin(t, b(501), b(501) + 0.9)) * (1 + 0.35 * pulse(t, b(504), 0.9))
        comb(fr, ax, xs, np.cos(xs), -np.sin(xs), -np.cos(xs), "frame", a, grow=grow)
    # S16: the parabola's comb lands on the cosine's at 0
    a = sa * smooth(lin(t, b(611), b(611) + 0.4)) * (1 - smooth(lin(t, b(621), b(621) + 0.6)))
    if a > 0.003:
        xs = np.linspace(-1.3, 1.3, 27)
        comb(fr, ax, xs, np.cos(xs), -np.sin(xs), -np.cos(xs), "frame", a)
        comb(fr, ax, xs, 1 - xs**2 / 2, -xs, -np.ones_like(xs), "copy", a * ease_out(lin(t, b(611), b(613))))


def draw_lens(fr, t, ax, c):
    """S12B: a lens on (0, 1), the two curves touching ("Right at 0")."""
    a = smooth(lin(t, b(433), b(433) + 0.4)) * (1 - smooth(lin(t, b(439), b(439) + 0.4)))
    if a <= 0.003:
        return
    r = 120 * ease_out(lin(t, b(433), b(433) + 0.45))
    center = (float(ax.px(0.0)) + 270, float(ax.py(0.0)) + 200)

    def inside(sub):
        COS.original(fr, a, ax=sub)
        COS.copy(fr, c, a, ax=sub, glow=0.5)

    COS.loupe(fr, (0.0, 1.0), 6, center, max(r, 1.0), inside, a, ax=ax, label=False)


# ------------------------------------------------------------------ S14 · the ghost x²

GHOST_AX = Axes(-1.25, 1.25, -0.15, 1.6, (880.0, 640.0, 200.0, 140.0))  # below the axis, right of the probe


def draw_ghost_square(fr, t):
    a = smooth(lin(t, b(514), b(514) + 0.5)) * (1 - smooth(lin(t, b(519), b(519) + 0.4)))
    if a <= 0.003:
        return
    lift = 30 * (1 - ease_out(lin(t, b(514), b(514) + 0.7)))
    x, y, w, h = GHOST_AX.rect
    ax = Axes(GHOST_AX.x0, GHOST_AX.x1, GHOST_AX.y0, GHOST_AX.y1, (x, y + lift, w, h))
    xs = np.linspace(-1.2, 1.2, 80)
    fr.poly(ax.px(xs), ax.py(xs**2), "copy", 2.6, 0.6 * a, glow=0.5)
    typmath.draw(fr, f"{X}^2", x + w + 50, y + 50 + lift, 48, None, a)


# ------------------------------------------------------------------ S15 · how much x²?

MINI = [(300.0, 190.0 + 245.0 * k, 820.0, 170.0) for k in range(3)]
MINI_F = [np.cos, lambda x: -np.sin(x), lambda x: -np.cos(x)]
MINI_L = ["f", "f'", "f''"]
MINI_T = [b(525), b(537), b(540)]
D_ROWS = [(760.0, 300.0), (760.0, 500.0), (760.0, 700.0)]
D_EXPR = [f"{X}^2", f"{F('2')} {X}", F("2")]


def draw_s15(fr, t):
    if not b(519) <= t < S16 + 0.6:
        return
    out = 1 - smooth(lin(t, b(595), b(595) + 0.5))
    push = 1 + 0.04 * ease_io(lin(t, b(519), b(549)))
    # 15A · the slope of the slope
    pa = out * (1 - smooth(lin(t, b(549), b(549) + 0.5)))
    if pa > 0.003:
        with zoom_about(fr, 760, 540, push):
            for k, (rect, f, lab, t0) in enumerate(zip(MINI, MINI_F, MINI_L, MINI_T)):
                a = pa * smooth(lin(t, t0, t0 + 0.4))
                if a <= 0.003:
                    continue
                drop_in = 24 * (1 - ease_out(lin(t, t0, t0 + 0.5)))
                ax = Axes(-3.3, 3.3, -1.3, 1.3, (rect[0], rect[1] - drop_in, rect[2], rect[3]))
                fr.line(ax.left, float(ax.py(0)), ax.right, float(ax.py(0)), "axis", 1.6, a)
                fr.line(float(ax.px(0)), ax.top, float(ax.px(0)), ax.bottom, "axis", 1.0, 0.6 * a)
                xs = np.linspace(ax.x0, ax.x1, 220)
                reveal = ease_out(lin(t, t0, t0 + 0.7))
                xs = xs[: max(2, int(len(xs) * reveal))]
                fr.poly(ax.px(xs), ax.py(f(xs)), "original", 2.2, a, glow=0.1)
                lit = k == 2 and t >= b(545)
                lab_glow = 0.8 * pulse(t, b(534), 1.0) if k == 2 else 0.0
                ly = rect[1] + rect[3] / 2 - drop_in
                typmath.draw(fr, lab + f"({X})", rect[0] - 40, ly, 40, None, a, glow=lab_glow, align="right")
                dot = (float(ax.px(0)), float(ax.py(f(np.array([0.0]))[0])))
                fr.glow_dot(*dot, 6.0 + 4 * pulse(t, b(545), 0.8) * lit, "minus" if lit else "ink", a, 0.9)
                if lit:
                    la = a * smooth(lin(t, b(545), b(545) + 0.4))
                    typmath.draw(fr, f"{MINUS} 1", dot[0] + 52, dot[1], 44, None, la, glow=0.4)
                if k < 2:
                    na = pa * smooth(lin(t, MINI_T[k + 1] - 0.1, MINI_T[k + 1] + 0.3))
                    if na > 0.003:
                        hud.arrow(
                            fr,
                            rect[0] + 40,
                            rect[1] + rect[3] + 10,
                            rect[0] + 40,
                            rect[1] + rect[3] + 62,
                            "frame",
                            1.6,
                            na,
                            glow=0.0,
                            head=10.0,
                        )
    with zoom_about(fr, 760, 500, 1 + 0.07 * ease_io(lin(t, b(549), b(595)))):  # slow push through 15B–15C
        _derivation(fr, t, out)


def _derivation(fr, t, out):
    # 15B · x² -> 2x -> 2
    da = out * smooth(lin(t, b(552), b(552) + 0.5)) * (1 - smooth(lin(t, b(588), b(588) + 0.35)))  # "x squared"
    if da > 0.003:
        size = 104
        typmath.draw(fr, D_EXPR[0], *D_ROWS[0], size, None, da)
        ex = typmath.glyph_centers(D_EXPR[0], *D_ROWS[0], size)[1]
        t1 = cue(564) - DROP - 0.1  # lands on "2X"
        d1 = typmath.glyph_centers(D_EXPR[1], *D_ROWS[1], size)
        u1 = drop(fr, t, t1, ex, d1[0], "2", size * 0.62, size, da)
        if u1 >= 1:
            fade = smooth(lin(t, t1 + DROP, t1 + DROP + 0.35))
            typmath.draw(fr, D_EXPR[1], *D_ROWS[1], size, None, da, alphas={1: fade})
        elif u1 > 0:
            typmath.draw(fr, D_EXPR[1], *D_ROWS[1], size, None, da, alphas={0: 0.0, 1: 0.0})
        t2 = cue(569) - DROP - 0.1  # lands on "2"
        top_x = (d1[1][0] + size * 0.22, d1[1][1] - size * 0.35)  # x's invisible exponent 1
        d2 = typmath.glyph_centers(D_EXPR[2], *D_ROWS[2], size)
        u2 = drop(fr, t, t2, top_x, d2[0], "1", size * 0.5, size * 0.8, da)
        if u2 >= 1:
            glow = 0.3 + 1.0 * smooth(lin(t, b(575), b(575) + 0.4))
            typmath.draw(fr, D_EXPR[2], *D_ROWS[2], size, None, da, glow=glow)
        # 15C · the target is −1
        ta = da * smooth(lin(t, b(585), b(585) + 0.4))
        if ta > 0.003:
            tx, ty = D_ROWS[2][0] + 320, D_ROWS[2][1]
            fr.circle(tx, ty, 58 + 6 * pulse(t, b(585), 0.8), "minus", 1.6, 0.6 * ta, glow=0.4)
            typmath.draw(fr, f"{MINUS} 1", tx, ty, 72, None, ta, glow=0.3)
    # 15C · −½x², and the check
    ha = out * smooth(lin(t, b(590), b(590) + 0.4))
    if ha > 0.003:
        half = f"{MINUS} 1/2 {X}^2"
        check = f"{MINUS} 1/2 dot {F('2')} = {MINUS} 1"
        typmath.draw(fr, half, 760, 380, 110, None, ha, reveal=lin(t, b(590), b(594)))
        ca = out * smooth(lin(t, b(594), b(594) + 0.4))
        typmath.draw(fr, check, 760, 620, 72, None, ca)
        w = typmath.size_of(check, 72)[0]
        mark = ease_out(lin(t, b(594) + 0.3, b(594) + 0.7))
        if mark > 0:
            cx, cy = 760 + w / 2 + 60, 620
            path = skia.Path()
            pts = [(cx - 18, cy), (cx - 4, cy + 16), (cx + 24, cy - 20)]
            path.moveTo(*pts[0])
            path.lineTo(*pts[1])
            path.lineTo(*pts[2])
            m = skia.PathMeasure(path, False)
            seg = skia.Path()
            m.getSegment(0, m.getLength() * mark, seg, True)
            fr.path_stroke(seg, "result", 4.0, ca, glow=0.7)


# ------------------------------------------------------------------ S17B · the cascade 4 · 3 · 2 · 1

R_EXPR = [
    f"{X}^4",
    f"{F('4')} {X}^3",
    f"{F('4')} dot {F('3')} {X}^2",
    f"{F('4')} dot {F('3')} dot {F('2')} {X}",
    f"{F('4')} dot {F('3')} dot {F('2')} dot {F('1')}",
]
R_SUM = R_EXPR[4] + f" = {F('24')}"
R_TERM = f"{X}^4 / {F('24')}"
R_SRC = [1, 2, 4, None]  # exponent glyph in the row above (None: x's invisible 1)
R_DST = [0, 2, 4, 6]  # the new magenta factor
R_CHAR = ["4", "3", "2", "1"]
R_LAND = [cue(665), cue(667), cue(669), cue(671)]  # "4", "3", "2", "1"
RX, RY0, RDY, RS = 760.0, 250.0, 135.0, 80.0


def draw_cascade(fr, t):
    if not b(651) <= t < b(678) + 0.6:
        return
    with zoom_about(fr, RX, 520, 1 + 0.06 * ease_io(lin(t, b(651), b(678)))):  # slow push while it runs
        _cascade(fr, t)


def _cascade(fr, t):
    out = 1 - smooth(lin(t, b(677), b(677) + 0.5))
    rows_out = 1 - smooth(lin(t, b(675), b(675) + 0.4))
    a0 = out * smooth(lin(t, b(651), b(651) + 0.4))
    y0 = RY0
    glow0 = 0.8 * pulse(t, b(661), 1.2)  # "differentiated 4 times"
    for k in range(4):  # four steps down, previewed as faint chevrons; each yields to its row
        ca = (
            rows_out
            * smooth(lin(t, b(661) + 0.3 * k, b(661) + 0.3 * k + 0.3))
            * (1 - smooth(lin(t, R_LAND[k] - DROP, R_LAND[k])))
        )
        if ca > 0.003:
            cy = RY0 + RDY * (k + 0.55) + 6 * math.sin(2 * math.pi * (t - b(661)) / 1.4 + k)
            fr.poly([RX - 16, RX, RX + 16], [cy - 8, cy + 8, cy - 8], "frame", 2.0, 0.55 * ca)
    typmath.morph(
        fr, R_EXPR[0], R_TERM, lin(t, b(675), b(675) + 0.6), RX, y0, RS, a0, glow=glow0, b_cy=y0 + 40, b_size=RS * 1.15
    )
    for k in range(4):
        t0 = R_LAND[k] - DROP
        row = R_EXPR[k + 1]
        y = RY0 + RDY * (k + 1)
        src_expr, ys = R_EXPR[k], RY0 + RDY * k
        gs = typmath.glyph_centers(src_expr, RX, ys, RS)
        if R_SRC[k] is None:
            src = (gs[-1][0] + RS * 0.22, gs[-1][1] - RS * 0.35)
        else:
            src = gs[R_SRC[k]]
        dst = typmath.glyph_centers(row, RX, y, RS)[R_DST[k]]
        u = drop(fr, t, t0, src, dst, R_CHAR[k], RS * 0.6, RS, out * rows_out)
        if u <= 0:
            continue
        n = len(typmath.glyphs(row)[0])
        rest = smooth(lin(t, t0 + 0.1, t0 + DROP + 0.2))
        alphas = {i: rest for i in range(n)}
        alphas[R_DST[k]] = 1.0 if u >= 1 else 0.0
        if k == 3 and t >= b(672):  # "24"
            g = smooth(lin(t, b(672) + 0.2, b(672) + 0.5))
            sa = out * rows_out
            typmath.morph(fr, row, R_SUM, lin(t, b(672), b(672) + 0.4), RX, y, RS, sa, glow=0.2 + 0.5 * g)
            continue
        typmath.draw(fr, row, RX, y, RS, None, out * rows_out, alphas=alphas, glow=0.2)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_stage(fr, t)
    draw_ghost_square(fr, t)
    draw_ladder(fr, t)
    draw_formula(fr, t)
    draw_s15(fr, t)
    draw_cascade(fr, t)
    hud.eyebrow(fr, t, "02 · COPYING A CURVE", START + 0.2)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch2:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=END - START, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(END - START)
        if audio:
            scene.add_audio(AUDIO, start=0, trim_start=START)
    return scene


SCENES = {
    "S11": (S11, S12, [134.6, 139.6, 141.6]),
    "S12": (S12, S13, [149.8, 155.6, 160.8]),
    "S13": (S13, S14, [169.0, 172.3, 176.4]),
    "S14": (S14, S15, [180.6, 185.2]),
    "S15": (S15, S16, [192.5, 202.4, 208.0, 213.6]),
    "S16": (S16, S17, [218.4, 221.6, 224.8]),
    "S17": (S17, END, [232.9, 241.2, 243.4, 250.9]),
}
OFFSET = START
DURATION = END - START
STILLS = [s for _, _, st in SCENES.values() for s in st]
