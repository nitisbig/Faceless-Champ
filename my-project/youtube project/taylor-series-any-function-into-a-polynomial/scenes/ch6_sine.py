"""CHAPTER 6 · WRAPPING THE SINE WAVE, 07:24.240 – 09:28.280 (cue #1177 "Now" → #1495 "So").

S28  Back to the calculator   the Chip slides back, its display frosted over 0.4794 -> sin(0.5) lifts out -> the Chip
                              leaves and the ink sine draws
S29  The derivative loop      a pink ring, a pointer visiting sin x, cos x, −sin x, −cos x -> their values at 0 -> two fast
                              turns fill the ladder 0 1 0 −1 0 1 0 −1 -> the even rows drop out, the signs take turns
S30  The sine series          sin x = x − x³/6 + x⁵/120 − x⁷/5040 + ⋯ on its words (3!, 5!, 7! under the denominators)
                              -> the formula becomes a top strip and the stage dollies wide
S31  The vine climbs          P₁ hugs ±0.39 and shoots away -> P₃ follows the hump (0.925 against 1) -> P₅ catches the
                              valley (−1.0045 against −1) -> degree 7 … 17, the camera pulls out, the tips wobble like a vine
S32  The calculation          graph left, rows right: x = 0.5, x³/6 = 0.125 ÷ 6 ≈ 0.0208, 0.4792, + x⁵/120 ≈ 0.00026,
                              0.479427 -> a lens ×100 then ×10,000 shows a 1.5 × 10⁻⁶ sliver -> sin 0.5 = 0.4794255…
S33  The secret revealed      × 4, + 2 from the Horner program -> the total flies into the Chip, whose display unfrosts ->
                              the core runs the polynomial -> a circle ghost fades; the gold copy is left alone
S34  Small angles             the copy relaxes to y = x, the stage zooms in: sin x ≈ x -> two pendulums from 10°, exact
                              and small-angle, swing in lockstep -> θ(t) = θ₀ cos(√(g/L) t)

Clean frame: no cards or pills (the plan's calculation card is floating rows on the bare stage).
"""

from __future__ import annotations

import math
from itertools import pairwise
from pathlib import Path

import numpy as np
import skia
from components import taylor as T
from components.chip import Chip
from components.digits import lock
from components.fx import glow_path, layer_alpha
from components.ladder import float_rows, label, value_token
from components.motion import spring
from components.pendulum import Pendulums, bob, trail
from components.stage import Axes, TaylorStage, clip
from cues import AUDIO, beat, cue
from theme import THEME, H, W

from faceless_champ.draw import Frame, back, ease_io, ease_out, hud, lin, noise, pulse, smooth
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc
from scenes import ch4_recipe as ch4
from scenes import ch5_e as ch5

START = cue(1177)  # 444.24 "Now let's return to the question"
END = cue(1495)  # 568.28 "So far, so good"

b = beat

S28, S29, S30, S31, S32, S33, S34 = START, cue(1203), cue(1249), cue(1282), cue(1350), cue(1393), cue(1454)

X = tc("x", "x")
PLUS, MINUS = tc("plus", "+"), tc("minus", "−")


def F(s):
    return tc("fact", s)


R = (96.0, 200.0, 1728.0, 760.0)
STAGE = TaylorStage("sin", view=(-8.0, 8.0, -1.7, 1.7), rect=R, samples=1600)
SIN0 = math.sin(0.5)

# ------------------------------------------------------------------ camera keys for the sine stage

W7 = Axes(-7.0, 7.0, -1.6, 1.6, R)
TIGHT = Axes(-4.0, 4.0, -1.7, 1.7, R)
W8 = Axes(-8.0, 8.0, -1.7, 1.7, R)
HUMP = Axes(math.pi / 2 - 3.0, math.pi / 2 + 3.0, -1.0, 1.64, R)
VALLEY = Axes(-math.pi / 2 - 3.0, -math.pi / 2 + 3.0, -1.64, 1.0, R)
W12 = Axes(-12.5, 12.5, -1.9, 1.9, R)
CALC = Axes(-0.4, 1.4, -0.25, 1.05, (96.0, 200.0, 980.0, 720.0))
SMALL = Axes(-0.3, 0.3, -0.3, 0.3, R)
CAM = [
    (S28, W7),
    (b(1276), TIGHT),
    (b(1281) + 0.4, W8),
    (b(1316), W8),
    (b(1316) + 1.1, HUMP),
    (b(1328), HUMP),
    (b(1328) + 1.1, VALLEY),
    (b(1331), VALLEY),
    (b(1344), W12),
    (b(1352), W12),
    (b(1352) + 1.2, CALC),
    (b(1446), CALC),
    (b(1446), W7),
    (b(1462), W7),
    (b(1462) + 1.0, SMALL),
]


def cam(t):
    for (t0, a0), (t1, a1) in pairwise(CAM):
        if t < t1:
            return a0 if t1 <= t0 else a0.lerp(a1, ease_io(lin(t, t0, t1)))
    return CAM[-1][1]


# ------------------------------------------------------------------ S28 · back to the calculator

CHIP = Chip(cx=960.0, cy=560.0, size=400.0)
DX, DY, DW, DH = CHIP.display_rect()


def chip_x(t):
    enter = ease_out(lin(t, START + 0.3, b(1186)))
    leave = ease_io(lin(t, b(1196), b(1197) + 0.5))
    back_in = ease_out(lin(t, b(1408), b(1411) + 0.3))
    if t < b(1300):
        return 2300 + (960 - 2300) * enter + (-500 - 960) * leave
    return 2300 + (960 - 2300) * back_in


def draw_chip(fr, t):
    if b(1197) + 0.6 < t < b(1408) or t > b(1447) + 1.0:
        return
    x = chip_x(t)
    out = 1 - smooth(lin(t, b(1446), b(1447) + 0.8))
    a = out * (smooth(lin(t, START + 0.3, START + 0.9)) if t < b(1300) else smooth(lin(t, b(1408), b(1409))))
    if a <= 0.003:
        return
    CHIP.cx = x
    dx = x - 960
    heart = smooth(lin(t, b(1430), b(1430) + 0.5))
    active, rings = {}, []
    k = math.floor((t - (b(1430) + 0.4)) / 0.1)
    if 0 <= k < len(PROG):  # the same op flicker as S02, from the real Horner program
        active[PROG[k]["op"]] = 1.0
        rings.append((PROG[k]["op"], lin(t, b(1430) + 0.4 + 0.1 * k, b(1430) + 0.85 + 0.1 * k)))
    CHIP.draw(fr, t, a, display=None, active=active, pad_fill=1.0 - 0.7 * heart, core_alpha=1.0 - 0.4 * heart)
    for op, u in rings:
        CHIP.pulse_ring(fr, op, u, a)
    # the display: frosted over 0.4794 until the calculation is done, then crisp
    clear = smooth(lin(t, b(1411) + 0.6, b(1412) + 0.4))
    txt_x, txt_y, size = DX + dx + DW - CHIP.size * 0.04, DY + DH * 0.7, DH * 0.56
    with fr.blurred(8.0 * (1 - clear)):
        hud.tabular(
            fr,
            "0.4794",
            txt_x,
            txt_y,
            size,
            "result" if clear > 0.5 else "ink",
            a * (0.45 + 0.55 * clear),
            align="right",
            glow=0.3,
        )
    if clear > 0:
        box = skia.Path()
        box.addRect(skia.Rect.MakeXYWH(DX + dx, DY, DW, DH))
        fr.light_sweep(box, lin(t, b(1412) + 0.2, b(1413) + 0.3), 0.8 * a)
    # "clever refinements": two honest captions flicker inside the die
    ca = a * smooth(lin(t, b(1419), b(1419) + 0.3)) * (1 - smooth(lin(t, b(1429), b(1430))))
    for j, cap in enumerate(("range reduction", "tuned coefficients")):
        fl = 0.55 + 0.45 * (noise.value(t, 7.0, seed=11 + j) > -0.4)
        x0, y0 = CHIP.at(0.5, 0.86 + 0.07 * j)
        fr.text(
            cap,
            x0,
            y0,
            "sans",
            20,
            500,
            "muted",
            ca * fl * smooth(lin(t, b(1419) + 0.25 * j, b(1419) + 0.25 * j + 0.3)),
        )
    # "at the heart of it": the gold polynomial inside the core
    if heart > 0:
        cx, cy, w = CHIP.core()
        core = Axes(-3.2, 3.2, -1.4, 1.4, (cx + 6, cy + w * 0.2, w - 12, w * 0.6))
        STAGE.copy(fr, C17, a * heart, ax=core, width=2.6, glow=0.9)
    CHIP.cx = 960.0


def draw_title28(fr, t):
    """sin(0.5) lifts out of the display and becomes the chapter's question."""
    if not b(1193) <= t < b(1211) + 0.6:
        return
    u = ease_io(lin(t, b(1193), b(1194) + 0.5))
    a = smooth(lin(t, b(1193), b(1193) + 0.3)) * (1 - smooth(lin(t, b(1210), b(1211) + 0.4)))
    x0, y0 = DX + DW / 2 + (chip_x(t) - 960), DY + DH / 2
    x, y = x0 + (960 - x0) * u, y0 + (140 - y0) * u - 60 * math.sin(math.pi * u)
    size = 34 + (72 - 34) * u
    m = lin(t, b(1200), b(1200) + 0.6)  # "apply the recipe to sine at 0"
    typmath.morph(fr, f"sin({tc('x', '0.5')})", f"sin {X}", m, x, y, size, a, glow=0.3 + 0.4 * pulse(t, b(1195), 0.6))


# ------------------------------------------------------------------ S29 · the derivative loop

WC, WR = (600.0, 560.0), 220.0
NODES = [f"sin {X}", f"cos {X}", f"{MINUS} sin {X}", f"{MINUS} cos {X}"]
NODE_F = [np.sin, np.cos, lambda x: -np.sin(x), lambda x: -np.cos(x)]
NODE_V = [0, 1, 0, -1]
NODE_T = [b(1212), b(1214), b(1216), b(1219), b(1222)]  # pointer arrivals, the last one closes the loop
VAL_T = [b(1230), b(1231), b(1232), b(1233)]
SPIN = (b(1235), b(1237) + 0.5)
LAD = (1160.0, 150.0, 500.0, 40.0, 88.0)  # x, y, w, size, row height
FILL_T = [SPIN[0] + (k + 0.6) / 8 * (SPIN[1] - SPIN[0]) for k in range(8)]
TERMS = ["1"] + [f"{X}" if k == 1 else f"{X}^{k}" for k in range(1, 8)]


def node_xy(k, r=WR):
    ang = -math.pi / 2 + math.pi / 2 * k
    return WC[0] + r * math.cos(ang), WC[1] + r * math.sin(ang)


def pointer_angle(t):
    ang = 0.0
    for k in range(4):
        ang += math.pi / 2 * ease_io(lin(t, NODE_T[k + 1] - 0.5, NODE_T[k + 1]))
    return -math.pi / 2 + ang + 4 * math.pi * ease_io(lin(t, *SPIN))


def draw_wheel(fr, t):
    a = smooth(lin(t, b(1211) - 0.2, b(1211) + 0.3)) * (1 - smooth(lin(t, b(1249) - 0.2, b(1249) + 0.4)))
    if a <= 0.003:
        return
    draw = ease_out(lin(t, b(1211), b(1211) + 0.7))
    ring = skia.Path()
    ring.addArc(skia.Rect.MakeXYWH(WC[0] - WR, WC[1] - WR, 2 * WR, 2 * WR), -90, 359.9 * draw)
    fr.path_stroke(ring, "circle", 2.4, a, glow=0.4)
    full = skia.Path()
    full.addCircle(*WC, WR)
    fr.light_sweep(glow_path(full, 14), lin(t, NODE_T[4] - 0.2, NODE_T[4] + 0.9), 0.7 * a)
    for k in range(4):
        na = a * smooth(lin(t, NODE_T[k] - 0.15, NODE_T[k] + 0.25))
        if na <= 0.003:
            continue
        x, y = node_xy(k)
        hit = pulse(t, NODE_T[k], 0.6) + (pulse(t, NODE_T[4], 0.6) if k == 0 else 0.0)
        fr.glow_dot(x, y, 7 + 5 * hit, "circle", na, 0.8)
        lx, ly = node_xy(k, WR + 78)
        align = "center" if k in (0, 2) else ("left" if k == 1 else "right")
        typmath.draw(
            fr, NODES[k], lx + (-40 if k == 1 else 40 if k == 3 else 0), ly, 44, None, na, glow=0.4 * hit, align=align
        )
        # a mini-curve of each node's function
        mx = lx + (60 if k == 1 else -150 if k == 3 else -45)
        my = ly + (44 if k in (1, 3) else (-56 if k == 0 else 50))
        xs = np.linspace(-math.pi, math.pi, 40)
        fr.poly(mx + (xs + math.pi) / (2 * math.pi) * 90, my - 14 * NODE_F[k](xs), "original", 1.4, 0.5 * na)
        # its value at 0, toward the centre
        va = na * smooth(lin(t, VAL_T[k], VAL_T[k] + 0.25))
        if va > 0.003:
            vx, vy = node_xy(k, WR * 0.58)
            s, tok = value_token(NODE_V[k])
            typmath.draw(fr, tc(tok, s.lstrip("+")), vx, vy, 46, None, va, glow=0.5 * pulse(t, VAL_T[k] + 0.25, 0.5))
    ang = pointer_angle(t)
    pa = a * smooth(lin(t, NODE_T[0] - 0.4, NODE_T[0]))
    px, py = WC[0] + WR * math.cos(ang), WC[1] + WR * math.sin(ang)
    for j in range(1, 6):  # a short comet tail
        ta = ang - 0.06 * j * (1 + 4 * (SPIN[0] <= t <= SPIN[1]))
        fr.glow_dot(
            WC[0] + WR * math.cos(ta), WC[1] + WR * math.sin(ta), 6 - 0.8 * j, "circle", pa * 0.5 * (1 - j / 6), 0.8
        )
    fr.glow_dot(px, py, 10.0, "circle", pa, 1.0)


def draw_ladder29(fr, t):
    a = smooth(lin(t, SPIN[0] - 0.3, SPIN[0])) * (1 - smooth(lin(t, b(1249) - 0.2, b(1249) + 0.4)))
    if a <= 0.003:
        return
    x, y, w, size, rh = LAD
    vanish = smooth(lin(t, b(1241), b(1243) + 0.2))
    rows = []
    for k in range(8):
        fill = smooth(lin(t, FILL_T[k], FILL_T[k] + 0.15))
        s, tok = value_token(NODE_V[k % 4])
        flash = pulse(t, b(1246) + 0.3 * (k // 2), 0.5) if k % 2 else 0.0
        val = tc(tok, s) if fill > 0 else None
        ra = (1 - 0.75 * vanish) if k % 2 == 0 else 1.0
        rows.append((label(k), val, ra * smooth(lin(t, FILL_T[k] - 0.2, FILL_T[k])), flash))
        # each row's power, waiting in its slot; the even ones slide out
        ta = a * fill * (1 - (vanish if k % 2 == 0 else 0.0))
        slide = 80 * vanish if k % 2 == 0 else 0.0
        if ta > 0.003:
            typmath.draw(
                fr, TERMS[k], x + w + 40 + slide, y + rh * (k + 0.5), 36, None, ta * 0.8, align="left", glow=0.6 * flash
            )
    float_rows(fr, x, y, rows, a, w=w, size=size, row_h=rh)


# ------------------------------------------------------------------ S30 · the sine series

SIN_P = [
    f"sin {X} =",
    f"{X}",
    f"{MINUS} {X}^3 / {F('6')}",
    f"{PLUS} {X}^5 / {F('120')}",
    f"{MINUS} {X}^7 / {F('5040')}",
    f"{PLUS} dots.c",
]
SIN_E = " ".join(SIN_P)
PIECE_T = [b(1249), b(1253), b(1254), b(1259), b(1266), b(1273)]
DEN_T = [None, None, b(1258), b(1265), b(1272), None]
HELP = [None, None, "3!", "5!", "7!", None]


def ranges(parts):
    out, i = [], 0
    for p in parts:
        n = len(typmath.glyphs(p)[0])
        out.append(range(i, i + n))
        i += n
    return out


R_SIN = ranges(SIN_P)
MAG_I = {k: [i for i in R_SIN[k] if typmath.glyphs(SIN_E)[0][i].color.lower() == "#ff3d9a"] for k in range(6)}
STRIP_GLOW = [(1, b(1285)), (2, b(1306)), (3, b(1320)), (5, b(1331)), (1, b(1458))]


def strip_state(t):
    """(cx, cy, size, alpha) of the series: built at centre in S30, a top strip from "watch it on the graph"."""
    u = ease_io(lin(t, b(1276), b(1277) + 0.6))
    a = smooth(lin(t, PIECE_T[0], PIECE_T[0] + 0.3)) * (1 - smooth(lin(t, b(1408), b(1409))))
    a = max(a, smooth(lin(t, b(1455), b(1455) + 0.5)) * (1 - smooth(lin(t, b(1472), b(1472) + 0.4))))
    return 960.0, 480 + (120 - 480) * u, 78 + (44 - 78) * u, a


def draw_series(fr, t):
    if t < PIECE_T[0]:
        return
    cx, cy, size, a = strip_state(t)
    if a <= 0.003:
        return
    alphas, glows = {}, {}
    for k, (rng, t0) in enumerate(zip(R_SIN, PIECE_T)):
        u = smooth(lin(t, t0, t0 + 0.35))
        for i in rng:
            alphas[i] = u
        if DEN_T[k] is not None:
            for i in MAG_I[k]:
                glows[i] = 0.9 * pulse(t, DEN_T[k], 0.8)
    for k, t0 in STRIP_GLOW:
        g = pulse(t, t0 + 0.3, 1.2)
        for i in R_SIN[k]:
            glows[i] = max(glows.get(i, 0.0), 0.9 * g)
    typmath.draw(fr, SIN_E, cx, cy, size, None, a, alphas=alphas, glows=glows)
    # muted 3!, 5!, 7! under the denominators while the series is being built
    ha = a * (1 - smooth(lin(t, b(1276), b(1276) + 0.4)))
    if ha > 0.003:
        cs = typmath.glyph_centers(SIN_E, cx, cy, size)
        for k, h in enumerate(HELP):
            if h:
                mx = np.mean([cs[i][0] for i in MAG_I[k]])
                my = max(cs[i][1] for i in MAG_I[k])
                fa = ha * smooth(lin(t, DEN_T[k] + 0.2, DEN_T[k] + 0.6))
                typmath.draw(fr, f"= {h}", mx, my + size * 0.75, size * 0.45, "muted", fa)


# ------------------------------------------------------------------ S31 · the vine climbs

CLIMB_T = [b(1331) + 0.2 + 0.6 * k for k in range(6)]
DEGS = [1, 3, 5, 7, 9, 11, 13, 15, 17]
HUG31 = [b(1306), b(1320)] + CLIMB_T
ZONES = [T.hug_zone("sin", n) for n in DEGS]
C17 = T.coeffs("sin", 17)
P3_HUMP = float(T.evaluate(T.coeffs("sin", 3), np.array([math.pi / 2]))[0])
P5_VALLEY = float(T.evaluate(T.coeffs("sin", 5), np.array([-math.pi / 2]))[0])


def wobble_tip(fr, ax, c, side, t, a):
    """The copy's leading tip, where it leaves the wave: a hand-drawn boil and a glint."""
    xs = np.linspace(0.0, ax.x1, 900) * side
    gap = np.abs(np.sin(xs) - T.evaluate(c, xs))
    i0 = int(np.argmax(gap > 0.03))
    if i0 == 0:
        return
    seg = xs[i0 : i0 + 120]
    ys = T.evaluate(c, seg)
    keep = np.abs(ys) < ax.y1 + 0.3
    pts = list(zip(ax.px(seg[keep]), ax.py(ys[keep])))
    if len(pts) < 3:
        return
    pts = noise.wobble(pts, t, 4.0, scale=0.02, fps=12, seed=3 + (side > 0))
    with clip(fr, ax.rect):
        fr.poly([p[0] for p in pts], [p[1] for p in pts], "copy", 4.0, a, 0.7)
    fr.glint(*pts[0], 50, a * (0.6 + 0.4 * math.sin(6 * t)))


def draw_climb(fr, t, ax, a):
    if t < b(1285):
        return
    ca = a * (1 - smooth(lin(t, b(1352), b(1352) + 0.5)))
    if ca <= 0.003:
        return
    c, _, s = STAGE.chain(t, DEGS, HUG31)
    band = smooth(lin(t, b(1303), b(1304) + 0.4))
    STAGE.error_band(fr, c, 0.7 * band * ca, ax=ax)
    grow = ease_out(lin(t, b(1285), b(1286) + 0.6))
    p = STAGE.copy(fr, c, ca, ax=ax, glow=0.6 + 0.5 * s, reveal=grow, sym=True)
    # brackets: they appear on "hugs", then jump outward with every hug (settled values only in the readout)
    rr = ZONES[0] + sum(spring(t, t0) * (ZONES[k + 1] - ZONES[k]) for k, t0 in enumerate(HUG31))
    ba = ca * smooth(lin(t, b(1295), b(1295) + 0.3))
    if ba > 0.003:
        snap = back(min(1.0, lin(t, b(1295), b(1295) + 0.4)), 1.6)
        ch4.bracket(fr, ax, rr * snap, 1, ba)
        ch4.bracket(fr, ax, -rr * snap, -1, ba)
        shown = min(ZONES, key=lambda z: abs(z - rr))
        x = min(float(ax.px(rr)) + 34, ax.right - 50)
        hud.tabular(fr, f"±{shown:.2f}", x, float(ax.py(0)) - 49, 26, "copy", ba, glow=0.25)
    # the hump and the valley: gold against ink
    for t0, t1, xv, pv, tv in (
        (b(1316) + 0.6, b(1328), math.pi / 2, P3_HUMP, 1.0),
        (b(1328) + 0.6, b(1331), -math.pi / 2, P5_VALLEY, -1.0),
    ):
        ha = ca * smooth(lin(t, t0, t0 + 0.4)) * (1 - smooth(lin(t, t1, t1 + 0.4)))
        if ha > 0.003:
            gx, gy = ax.at(xv, pv)
            ix, iy = ax.at(xv, tv)
            fr.glow_dot(ix, iy, 7.0, "original", ha, 0.8)
            fr.glow_dot(gx, gy, 8.0, "copy", ha, 1.0)
            up = -1 if tv > 0 else 1
            hud.tabular(fr, f"{tv:g}", ix + 18, iy + up * 34, 30, "ink", ha, align="left")
            hud.tabular(
                fr,
                f"{pv:.4g}" if abs(pv) > 1 else f"{pv:.3f}",
                gx + 18,
                gy - up * 34,
                30,
                "copy",
                ha,
                align="left",
                glow=0.3,
            )
    # degree 7 … 17
    da = ca * smooth(lin(t, CLIMB_T[0] - 0.3, CLIMB_T[0])) * (1 - smooth(lin(t, b(1350), b(1351))))
    if da > 0.003:
        n = DEGS[2 + sum(t >= t0 for t0 in CLIMB_T)]
        fr.text("degree", 1560, 136, "sans", 26, 500, "muted", da, align="right")
        hud.tabular(
            fr,
            str(n),
            1580,
            140,
            52,
            "copy",
            da,
            align="left",
            glow=0.3 + 0.5 * max(pulse(t, t0, 0.4) for t0 in CLIMB_T),
        )
    # "like a vine climbing a fence"
    va = ca * smooth(lin(t, b(1345), b(1345) + 0.4))
    if va > 0.003:
        for side in (-1, 1):
            wobble_tip(fr, ax, c, side, t, va)
    if p is not None:
        with clip(fr, ax.rect):
            fr.light_sweep(glow_path(p, 26), lin(t, b(1345), b(1348) + 0.6), 0.6 * ca)
            for t0 in HUG31:
                u = lin(t, t0 + 0.25, t0 + 0.9)
                if 0 < u < 1:
                    fr.light_sweep(glow_path(p, 22), u, 0.4 * ca)


def draw_sine_stage(fr, t):
    a = smooth(lin(t, b(1196) + 0.2, b(1197) + 0.4)) * (1 - smooth(lin(t, b(1210), b(1211) + 0.3)))
    a = max(a, smooth(lin(t, b(1276), b(1277) + 0.4)) * (1 - smooth(lin(t, b(1408), b(1409) + 0.2))))
    if a <= 0.003:
        return
    ax = cam(t)
    STAGE.static(fr, a, ax=ax, labels=False)
    reveal = ease_io(lin(t, b(1196) + 0.3, b(1202) + 0.4)) if t < b(1250) else 1.0
    STAGE.original(fr, a, reveal=reveal, ax=ax, glow=0.1)
    draw_climb(fr, t, ax, a)
    if t >= b(1352):
        draw_calc_graph(fr, t, ax, a)


# ------------------------------------------------------------------ S32 · the calculation

RX = 1200.0
CALC_DEG = ([1, 3, 5], [b(1371), b(1378)])
ROW1 = f"{X} = 0.5"
ROW2 = f"{MINUS} {X}^3 / {F('6')} = 0.125 div 6"
ROW2B = f"approx {0.5**3 / 6:.4f}"
ROW3 = f"{PLUS} {X}^5 / {F('120')} approx {0.5**5 / 120:.5f}"
P3_HALF = 0.5 - 0.5**3 / 6
P5_HALF = float(T.evaluate(T.coeffs("sin", 5), np.array([0.5]))[0])
TARGET = f"{SIN0:.10f}"
GAP = P5_HALF - SIN0
GAP_LABEL = f"{GAP / 10 ** math.floor(math.log10(GAP)):.1f} times 10^({math.floor(math.log10(GAP))})"
LENS_C, LENS_R = (330.0, 380.0), 140.0
PROG = T.ops(T.coeffs("sin", 5), 0.5)
TALLY = {op: sum(s["op"] == op for s in PROG) for op in ("×", "+")}


def lens_mag(t):
    return 10 ** (2 + 2 * ease_io(lin(t, b(1387) + 0.5, b(1387) + 1.4)))


def draw_calc_graph(fr, t, ax, a):
    ga = a * smooth(lin(t, b(1352) + 0.3, b(1352) + 0.9))
    if ga <= 0.003:
        return
    c, _, s = STAGE.chain(t, *CALC_DEG)
    STAGE.error_band(fr, c, 0.5 * ga, ax=ax)
    STAGE.copy(fr, c, ga, ax=ax, glow=0.6 + 0.5 * s)
    x = 0.5 * ease_io(lin(t, b(1353), b(1355) + 0.2))
    STAGE.probe(fr, x, ga * smooth(lin(t, b(1353) - 0.2, b(1353) + 0.2)), ax=ax, drop=False)
    ma = ga * smooth(lin(t, b(1357), b(1357) + 0.3))
    if ma > 0.003:
        y = float(T.evaluate(c, np.array([0.5]))[0])
        fr.dashed([float(ax.px(0.5))] * 2, [float(ax.py(0)), float(ax.py(y))], "x", 1.4, 0.6 * ma, on=7, off=6)
        fr.glow_dot(*ax.at(0.5, y), 8.0, "copy", ma, 1.0)
    ia = ga * smooth(lin(t, b(1388), b(1388) + 0.4))
    if ia > 0.003:
        fr.glow_dot(*ax.at(0.5, SIN0), 6.0, "original", ia, 0.7)
    # the lens on the tiny step: ×100, then ×10,000 in the pause
    open_ = ease_out(lin(t, b(1378) + 0.3, b(1378) + 0.75))
    if open_ > 0.01:
        m = lens_mag(t)
        r = LENS_R * open_ + 2 * math.sin(1.5 * t)

        def inside(sub):
            STAGE.error_band(fr, c, 0.8 * ga, ax=sub)
            STAGE.original(fr, ga, ax=sub)
            STAGE.copy(fr, c, ga, ax=sub, glow=0.4)
            sl = ga * smooth(lin(t, b(1387) + 1.2, b(1387) + 1.6))
            if sl > 0.003:
                typmath.draw(fr, tc("error", GAP_LABEL), LENS_C[0], LENS_C[1] - r * 0.55, 28, None, sl)

        LENS_STAGE.loupe(fr, (0.5, SIN0), m, LENS_C, r, inside, ga, ax=ax, label=False)
        hud.tabular(fr, f"×{10 ** round(math.log10(m)):,}", LENS_C[0], LENS_C[1] + r + 32, 24, "muted", ga * open_)


LENS_STAGE = TaylorStage("sin")


def draw_rows(fr, t):
    a = smooth(lin(t, b(1352), b(1352) + 0.5)) * (1 - smooth(lin(t, b(1409), b(1410))))
    if a <= 0.003:
        return
    fr.dashed([1130.0, 1130.0], [220.0, 220 + 700 * ease_out(lin(t, b(1352), b(1353)))], "line", 1.2, a, on=10, off=9)
    rows = [(ROW1, b(1357), 280.0), (ROW2, b(1365), 390.0), (ROW3, b(1378), 520.0)]
    for k, (expr, t0, y) in enumerate(rows):
        ra = a * smooth(lin(t, t0, t0 + 0.35))
        g = 0.8 * pulse(t, b(1393) + 0.15 * k, 0.6)
        slide = 40 * (1 - ease_out(lin(t, t0, t0 + 0.5)))
        typmath.draw(fr, expr, RX + slide, y, 46, None, ra, align="left", glow=g)
    ra = a * smooth(lin(t, b(1369), b(1369) + 0.35))
    typmath.draw(fr, ROW2B, RX + 120, 452, 40, "muted", ra, align="left")
    # the running total and, under it, the true value
    fr.line(RX, 590, RX + 520, 590, "line", 1.2, a * smooth(lin(t, b(1371), b(1371) + 0.4)))
    if t >= b(1376):
        late = t >= b(1387)
        s = f"{P5_HALF:.6f}" if late else f"{P3_HALF:.4f}"
        t0 = b(1387) if late else b(1376)
        force = None
        if t >= b(1388):  # compare column by column: the decimals light in pairs
            j = sum(t >= b(1392) + 0.3 * i for i in range(3))
            force = (2, 4, 6, 7)[j]
        g = 0.0
        if force is not None and t >= b(1392):
            g = lin(t, b(1392) + 0.3 * (j - 1), b(1392) + 0.3 * (j - 1) + 0.3)
        else:
            g = lin(t, t0, t0 + 0.3)
        glow = 1 + 0.08 * pulse(t, b(1405), 0.8)
        lock(fr, s, TARGET, RX, 660, 66 * glow, a * smooth(lin(t, t0, t0 + 0.2)), align="left", glint=g, force=force)
    ta = a * smooth(lin(t, b(1388), b(1388) + 0.4))
    if ta > 0.003:
        slide = 30 * (1 - ease_out(lin(t, b(1388), b(1388) + 0.5)))
        lock(fr, f"{SIN0:.7f}", TARGET, RX, 760 + slide, 66, ta, align="left", base="ink", locked="ink")
        fr.text("…", RX + 66 * 0.6 * 9.2, 760 + slide, "display", 66, 600, "ink", ta, align="left")
        typmath.draw(fr, "sin 0.5", RX - 30, 742 + slide, 34, "muted", ta, align="right")
    # S33A: the tally, from the Horner program the chip runs
    ya = a * smooth(lin(t, b(1397), b(1397) + 0.3))
    if ya > 0.003:
        k = max(0, min(len(PROG), math.floor((t - b(1397)) / 0.12) + 1))
        for j, (op, tok) in enumerate((("×", "fact"), ("+", "plus"))):
            n = sum(s["op"] == op for s in PROG[:k])
            typmath.draw(
                fr,
                f"{tc(tok, 'times' if op == '×' else '+')} {n}",
                RX + 40 + 200 * j,
                870,
                52,
                None,
                ya,
                glow=0.4 * (n == TALLY[op]),
            )


def draw_flight(fr, t):
    """33B: the total flies into the Chip's display."""
    u = lin(t, b(1409), b(1411) + 0.6)
    if not 0 < u < 1:
        return
    e = ease_io(u)
    x0, y0 = RX + 140, 640.0
    x1, y1 = DX + DW / 2, DY + DH * 0.7 - DH * 0.2
    x, y = x0 + (x1 - x0) * e, y0 + (y1 - y0) * e - 80 * math.sin(math.pi * e)
    hud.tabular(fr, "0.4794", x, y, 66 + (DH * 0.56 - 66) * e, "result", 1 - smooth(lin(u, 0.75, 1.0)), glow=0.5)


# ------------------------------------------------------------------ S33C / S34 · the gold copy alone, then small angles


def draw_alone(fr, t):
    """The circle the machine never knew, then the gold copy left glowing alone, which S34 relaxes to y = x."""
    ca = smooth(lin(t, b(1435), b(1435) + 0.3)) * (1 - smooth(lin(t, b(1443) + 0.3, b(1443) + 0.9)))
    if ca > 0.003:
        ring = skia.Path()
        ring.addArc(
            skia.Rect.MakeXYWH(1460 - 110, 560 - 110, 220, 220), -90, 359.9 * ease_out(lin(t, b(1435), b(1436) + 0.4))
        )
        fr.path_stroke(ring, "circle", 2.0, 0.55 * ca, glow=0.3)
    if t < b(1446):
        return
    u = ease_io(lin(t, b(1446), b(1448) + 0.4))
    core = Axes(
        -3.2,
        3.2,
        -1.4,
        1.4,
        (CHIP.core()[0] + 6, CHIP.core()[1] + CHIP.core()[2] * 0.2, CHIP.core()[2] - 12, CHIP.core()[2] * 0.6),
    )
    ax = core.lerp(W7, u) if t < b(1462) else cam(t)
    out = 1 - smooth(lin(t, b(1472), b(1472) + 0.5))
    a = out
    ia = smooth(lin(t, b(1454), b(1455) + 0.4)) * out
    if ia > 0.003:
        STAGE.static(fr, ia, ax=ax, labels=False)
        STAGE.original(fr, ia, ax=ax)
    rel = spring(t, b(1458))
    c = T.blend(C17, np.pad(T.coeffs("sin", 1), (0, len(C17) - 2)), rel)
    STAGE.copy(fr, c, a, ax=ax, glow=0.9 - 0.3 * u)
    sa = smooth(lin(t, b(1469), b(1469) + 0.4)) * out
    if sa > 0.003:
        typmath.draw(fr, f"sin {X} approx {X}", 220, 300, 84, None, sa, align="left", glow=0.3)


PEND = Pendulums(theta0=math.radians(10))
PIVOTS = ((560.0, 260.0), (1360.0, 260.0))
ROD = 400.0
REL = b(1472) + 0.7


def draw_pendulums(fr, t):
    a = smooth(lin(t, b(1472) + 0.2, b(1472) + 0.7))
    if a <= 0.003:
        return
    tt = max(0.0, t - REL)
    for j, pv in enumerate(PIVOTS):
        th = PEND.angles(tt)[j]
        hist = [PEND.angles(max(0.0, tt - 0.03 * i))[j] for i in range(24, -1, -1)]
        trail(fr, pv, ROD, hist, "circle", 0.8 * a * smooth(lin(t, REL, REL + 0.3)), 2.0)
        x, y = bob(pv, ROD, th)
        fr.line(pv[0] - 60, pv[1], pv[0] + 60, pv[1], "line", 1.2, a)
        fr.line(pv[0], pv[1], x, y, "original", 2.0, a)
        fr.circle(pv[0], pv[1], 5, "frame", alpha=a, fill=True)
        fr.glow_dot(x, y, 18.0, "x", a, 0.6)
    la = a * smooth(lin(t, b(1472) + 0.8, b(1472) + 1.2))
    typmath.draw(fr, f"theta'' = {MINUS} g / L sin theta", PIVOTS[0][0], 830, 42, None, 0.8 * la)
    fr.text("exact", PIVOTS[0][0], 210, "sans", 26, 500, "muted", la)
    fr.text("small angle", PIVOTS[1][0], 210, "sans", 26, 500, "muted", la)
    sa = a * smooth(lin(t, b(1492), b(1492) + 0.4))
    typmath.draw(
        fr,
        f"theta({tc('x', 't')}) = theta_0 cos(sqrt(g / L) {tc('x', 't')})",
        PIVOTS[1][0],
        830,
        42,
        None,
        sa,
        glow=0.3 + 0.5 * pulse(t, b(1494), 0.8),
    )


# ------------------------------------------------------------------ assembly


def draw_handoff(fr, t):
    a = 1 - smooth(lin(t, START, START + 0.7))
    if a > 0.003:
        with layer_alpha(fr, a):
            ch5.draw_race(fr, t)


def draw_one(t, size):
    fr = Frame(size)
    draw_handoff(fr, t)
    draw_sine_stage(fr, t)
    draw_wheel(fr, t)
    draw_ladder29(fr, t)
    draw_series(fr, t)
    if S32 <= t < S33 + 15:
        draw_rows(fr, t)
    draw_alone(fr, t)
    draw_chip(fr, t)
    draw_title28(fr, t)
    draw_flight(fr, t)
    if t >= b(1472):
        draw_pendulums(fr, t)
    hud.eyebrow(fr, t, "06 · WRAPPING THE SINE", START + 0.2)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch6:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=END - START, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(END - START)
        if audio:
            scene.add_audio(AUDIO, start=0, trim_start=START)
    return scene


SCENES = {
    "S28": (S28, S29, [446.6, 449.9, 452.9]),
    "S29": (S29, S30, [458.2, 465.3, 470.6]),
    "S30": (S30, S31, [476.8, 481.0, 483.8]),
    "S31": (S31, S32, [488.6, 493.9, 498.6, 502.4, 505.4]),
    "S32": (S32, S33, [508.4, 516.2, 520.6, 529.9, 534.5]),
    "S33": (S33, S34, [538.4, 544.2, 549.8, 555.2]),
    "S34": (S34, END, [559.0, 564.8, 567.9]),
}
OFFSET = START
DURATION = END - START
STILLS = [s for _, _, st in SCENES.values() for s in st]
