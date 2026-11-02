"""CHAPTER 6 - RECAP AND OUTRO (S22-S24), 06:27.180 (#1127 "Let's") - 07:41.576 (end screen).

S22  Everything we built  six glass cards in an arc, each a live miniature of a chapter: the camera trucks from card
                          to card (the active one sharp, the others dim and blurred). counting (the path light, the
                          middle bins, the two lonely edges) -> adding (three dice, independent, add up, the bell; a
                          lopsided die and the bell stays) -> two dials (μ slides, σ stretches) -> e and π (the darts'
                          teal/orange axes, then the pink rings) -> the ruler (68, 95, 99.7) -> where it breaks (+ vs ×,
                          the crack and the red tail).
S23  Not a coincidence    the cards collapse to a point -> the opening board pours again, the bins fill, the gold curve
                          traces over the pile and snaps, a gold + flickers inside it.
S24  Next                 the formula returns, its lime e lifts out and grows, then slides into the left end-screen slot,
                          which traces with a light sweep -> THE BELL CURVE lockup, the second slot and the subscribe
                          circle -> a 20 s end screen over a faint endless pour.
"""

from __future__ import annotations

import contextlib
import math
from pathlib import Path

import numpy as np
import skia
import typmath
from components import hud
from components.bell import Bell, band_share, pdf
from components.darts import Target
from components.dials import dial_pair
from components.galton import Board, binom_row
from components.histogram import LOPSIDED, Axes, bars_from, die_pmf, draw_bars, morph, sum_pmf
from cues import AUDIO, TOTAL, beat, cue
from fx import Frame, card_quad, chroma_kick, ease_in, ease_io, ease_out, env, lin, quad_matrix, smooth, text_path
from theme import THEME, H, W
from typmath import tc

from scenes import ch0_intro as ch0
from scenes import ch3_formula as ch3

START = cue(1127)  # 387.18 "Let's bring it all together."
END = TOTAL  # 461.576: narration ends at 441.58, then the 20 s end screen

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


def lerp(a, b_, u):
    return a + (b_ - a) * u


def clamp01(x):
    return max(0.0, min(1.0, x))


def pop(t, at, tau=0.35):
    return math.exp(-(t - at) / tau) if t >= at else 0.0


def badge(fr, x, y, sym, color, alpha, r=44.0, kick=0.0, glow=0.4):
    if alpha <= 0.003:
        return
    rr = r * (1 + 0.25 * kick)
    hud.glass_card(fr, x - rr, y - rr, 2 * rr, 2 * rr, alpha, r=int(rr), glow=glow + kick, glow_color=color)
    fr.circle(x, y, rr, color, 2.4, alpha, glow=0.4)
    fr.text(sym, x, y + rr * 0.42, "display", rr * 1.25, 600, color, alpha)


def page_title(fr, k, name, alpha=1.0):
    fr.text(str(k), 120, 150, "display", 72, 600, "bell", alpha, align="left")
    fr.text(name, 190, 150, "display", 72, 600, "ink", alpha, align="left")


# ------------------------------------------------------------------ timing

TOPIC = (b(1132), b(1151), b(1177), b(1190), b(1207), b(1222))  # the six cards
COLLAPSE_T = b(1239)  # "next time you see a bell curve"
COINC_T = b(1251)  # "not a coincidence"
SHAPE_T = b(1257)  # "shape randomness takes"
ADDUP_T = b(1261)  # "many little things add up"
AND_T = b(1266)  # "And if you want to see"
E_T = b(1273)  # "number e"
WATCH_T = b(1278)  # "watch the video"
WHY_T = b(1282)  # "why e is everywhere"
THANKS_T = b(1287)  # "Thanks for watching"
SPEECH_END = 441.58


def topic_end(i):
    return TOPIC[i + 1] if i + 1 < len(TOPIC) else COLLAPSE_T


# ------------------------------------------------------------------ card 1: counting

B1 = Board(rows=10, cx=960.0, top=260.0, dx=74.0, dy=48.0, peg_r=5.0, ball_r=6.0, n=1, floor=930.0)
C10 = binom_row(10)
MIDDLE_T = b(1146)
EDGES_T = b(1150)


def page_counting(fr, t):
    page_title(fr, 1, "counting")
    B1.draw_frame(fr, 1.0, funnel=False)
    B1.draw_path_light(fr, 1.0 - 0.5 * smooth(lin(t, EDGES_T, EDGES_T + 0.3)), gamma=1.6)
    mid = smooth(lin(t, MIDDLE_T, MIDDLE_T + 0.3))
    edge = smooth(lin(t, EDGES_T, EDGES_T + 0.3))
    for k in range(11):
        x = float(B1.bin_x(k))
        h = C10[k] / C10.max() * 150
        hot = mid if 4 <= k <= 6 else edge if k in (0, 10) else 0.0
        fr.rrect(
            x - 26,
            B1.floor - max(h, 3),
            52,
            max(h, 3),
            3,
            fill="ink" if hot > 0.5 else "ball",
            alpha=1.0,
            fill_alpha=0.75 + 0.25 * hot,
            glow=0.2 + 0.8 * hot,
        )
        typmath.number(
            fr, str(C10[k]), x, B1.floor + 44, 30, "ink" if hot > 0.5 else "muted", 0.6 + 0.4 * hot, glow=0.5 * hot
        )
    if edge > 0:
        B1.draw_path(fr, [0] * 10, edge, alpha=edge, width=4.0)
        B1.draw_path(fr, [1] * 10, edge, alpha=edge, width=4.0)


# ------------------------------------------------------------------ card 2: adding

AXA = Axes(cx=960.0, floor=900.0, unit=150.0, hscale=760.0)
BELLA = Bell(AXA, -3.4, 3.4)
FAIR = [bars_from(*die_pmf())] + [bars_from(*sum_pmf(*die_pmf(), n)) for n in (2, 3, 10)]
LOP30 = bars_from(*sum_pmf(*LOPSIDED, 30))
INDEP_T = b(1161)
ADD_T = b(1163)
BELL_T = b(1169)
STRANGE_T = b(1170)


def page_adding(fr, t):
    page_title(fr, 2, "adding")
    # three small dice, pulled apart on "independent", swapped for lopsided ones on "no matter how strange"
    sep = lerp(200.0, 330.0, ease_io(lin(t, INDEP_T, INDEP_T + 0.6)))
    lop = smooth(lin(t, STRANGE_T, STRANGE_T + 0.4))
    fair_p = die_pmf()[1]
    for j in range(3):
        x0 = 960 + (j - 1) * sep
        for f in range(6):
            p = lerp(fair_p[f], LOPSIDED[1][f], lop)
            h = p * 6 * 54
            fr.rrect(x0 - 63 + f * 21, 380 - h, 17, h, 2, fill="ball", alpha=1.0, fill_alpha=0.85)
        fr.line(x0 - 70, 381, x0 + 70, 381, "line", 1.4, 1.0)
        if j < 2:
            fr.text("+", x0 + sep / 2, 360, "display", 48, 600, "muted", 1.0)
    # the sum: one die -> 2 -> 3 -> 10 -> the bell; then thirty lopsided dice, same bell
    u = 3 * lin(t, ADD_T, BELL_T - 0.1)
    k = min(2, int(u))
    bars = morph(FAIR[k], FAIR[k + 1], ease_io(clamp01(u - k)))
    if t > STRANGE_T:
        bars = morph(FAIR[3], LOP30, ease_io(lin(t, STRANGE_T + 0.1, STRANGE_T + 1.2)))
    AXA.floor_line(fr, -3.6, 3.6, 1.0)
    draw_bars(fr, AXA, bars, 1.0)
    BELLA.snap(fr, t, BELL_T, alpha=1.0, width=4.0)


# ------------------------------------------------------------------ card 3: two dials

AX3 = Axes(cx=960.0, floor=640.0, unit=150.0, hscale=650.0)
BELL3 = Bell(AX3, -3.6, 3.6)
MU3_T = b(1185)
SIG3_T = b(1189)


def dials_state(t):
    mu = 0.9 * (ease_io(lin(t, MU3_T, MU3_T + 0.5)) - ease_io(lin(t, MU3_T + 0.7, MU3_T + 1.2)))
    sigma = 1 + 0.5 * (ease_io(lin(t, SIG3_T, SIG3_T + 0.5)) - ease_io(lin(t, SIG3_T + 0.9, SIG3_T + 1.4)))
    return mu, sigma


def page_dials(fr, t):
    page_title(fr, 3, "two dials")
    mu, sigma = dials_state(t)
    glows = {ch3.MU_IDX: 1.2 * env(t, MU3_T, MU3_T + 1.4, 0.2, 0.4)}
    glows[ch3.SIGMA_IDX] = 1.2 * env(t, SIG3_T, SIG3_T + 1.6, 0.2, 0.4)
    glows[21] = glows[ch3.SIGMA_IDX]
    typmath.draw(fr, ch3.FORMULA, 1180, 150, 56, glows=glows)
    AX3.floor_line(fr, -3.8, 3.8, 1.0)
    BELL3.draw(fr, mu, sigma, alpha=1.0, width=4.0, glow=0.8, fill=0.10)
    BELL3.mean_line(fr, mu, sigma, alpha=0.8)
    dial_pair(
        fr,
        960,
        840,
        mu,
        sigma,
        1.0,
        gap=360,
        active_mu=env(t, MU3_T, MU3_T + 1.4, 0.2, 0.4),
        active_sigma=env(t, SIG3_T, SIG3_T + 1.6, 0.2, 0.4),
    )


# ------------------------------------------------------------------ card 4: e and π

TG4 = Target(cx=960.0, cy=650.0, unit=70.0, n=300)
HERO4 = int(np.argmin(np.hypot(TG4.z[:, 0] - 1.6, TG4.z[:, 1] - 1.1)))
E4_T = b(1192)
INDEP4_T = b(1195)
PI4_T = b(1197)
CIRC4_T = b(1202)
PI_GLYPH = 10


def page_epi(fr, t):
    page_title(fr, 4, "e and π")
    glows = {ch3.G_E: 1.4 * env(t, E4_T, PI4_T + 0.2, 0.2, 0.4), PI_GLYPH: 1.4 * env(t, PI4_T, CIRC4_T + 1.5, 0.2, 0.5)}
    typmath.draw(fr, ch3.FORMULA, 1180, 150, 56, glows=glows)
    TG4.draw_board(fr, 1.0)
    TG4.draw_darts(fr, 1e3, 0.0, 1e3, alpha=0.9)
    ax = smooth(lin(t, INDEP4_T, INDEP4_T + 0.4)) * (1 - 0.6 * smooth(lin(t, CIRC4_T, CIRC4_T + 0.4)))
    if ax > 0.003:
        r = 3.6 * TG4.unit
        fr.line(TG4.cx - r, TG4.cy, TG4.cx + r, TG4.cy, "left", 2.4, ax, glow=0.5)
        fr.line(TG4.cx, TG4.cy - r, TG4.cx, TG4.cy + r, "right", 2.4, ax, glow=0.5)
        u = ease_out(lin(t, INDEP4_T + 0.1, INDEP4_T + 0.6))
        TG4.draw_errors(fr, HERO4, u, u, ax)
    TG4.draw_rings(fr, smooth(lin(t, CIRC4_T, CIRC4_T + 0.3)), u=lin(t, CIRC4_T, CIRC4_T + 0.9), width=3.0)


# ------------------------------------------------------------------ card 5: the ruler

AX5 = Axes(cx=960.0, floor=800.0, unit=190.0, hscale=900.0)
BELL5 = Bell(AX5, -3.6, 3.6)
P_T = (b(1207), b(1208), b(1210))  # 68, 95, 99.7
STEP5_T = (b(1217), b(1218), b(1220))  # one, two, three sigma
SPOKEN = ("68%", "95%", "99.7%")


def page_ruler(fr, t):
    page_title(fr, 5, "the ruler")
    AX5.floor_line(fr, -3.8, 3.8, 1.0)
    for k in (3, 2, 1):
        u = ease_out(lin(t, P_T[k - 1], P_T[k - 1] + 0.5))
        BELL5.band(fr, k, alpha=1.0, fill=(0.10, 0.12, 0.26)[k - 1], u=u, edges=False)
    BELL5.draw(fr, alpha=1.0, width=4.0, glow=0.8)
    for k in (1, 2, 3):
        a = env(t, P_T[k - 1], P_T[k] if k < 3 else 1e9, 0.25, 0.25)
        if a > 0.003:
            fr.text(SPOKEN[k - 1], 1520, 330, "display", 96, 600, "ink", a, glow=0.4)
            hud.tabular(fr, f"{100 * band_share(k):.2f}%", 1520, 380, 30, "muted", a)
        s = smooth(lin(t, STEP5_T[k - 1], STEP5_T[k - 1] + 0.3))
        if s > 0.003:
            for z in (-k, k):
                x = float(AX5.x(z))
                fr.line(x, AX5.floor, x, float(AX5.y(pdf(z))), "sigma", 3.0, s, glow=0.7)
            typmath.draw(fr, f"{k} {tc('sigma', 'sigma')}", float(AX5.x(k)), AX5.floor + 50, 40, color="ink", alpha=s)


# ------------------------------------------------------------------ card 6: where it breaks

AX6 = Axes(cx=760.0, floor=820.0, unit=160.0, hscale=900.0)
BELL6 = Bell(AX6, -3.4, 3.4)
MULT6_T = b(1225)
BREAK6_T = b(1231)
EXTREME6_T = b(1234)


def page_breaks(fr, t):
    page_title(fr, 6, "where it breaks")
    m = smooth(lin(t, MULT6_T, MULT6_T + 0.3))
    badge(fr, 1260, 330, "+", "bell", 1.0 - 0.6 * m)
    badge(fr, 1460, 330, "×", "tail", 0.4 + 0.6 * m, kick=pop(t, MULT6_T, 0.3), glow=0.6 * m)
    AX6.floor_line(fr, -3.6, 7.0, 1.0)
    if t < BREAK6_T:
        BELL6.draw(fr, alpha=1.0, width=4.0, glow=0.8, fill=0.10)
    else:
        BELL6.crack(fr, lin(t, BREAK6_T, BREAK6_T + 0.45), at=0.9, alpha=1.0, width=4.0, gap=12)
        BELL6.tail(fr, lin(t, EXTREME6_T, EXTREME6_T + 1.0), at=0.9, alpha=1.0, width=4.0, reach=14.0)


PAGES = (page_counting, page_adding, page_dials, page_epi, page_ruler, page_breaks)

# ------------------------------------------------------------------ the arc of cards (S22)

CARD_W, CARD_H = 1120.0, 630.0
SPACING = 990.0
OVER = (START + 0.2, TOPIC[0] - 0.1)  # the wide shot of all six cards eases into card 1


def camera(t):
    """Focused card index (float) and how far the wide shot has eased into the arc (0 = all six, 1 = focused)."""
    c = sum(ease_io(lin(t, TOPIC[k] - 0.45, TOPIC[k] + 0.3)) for k in range(1, 6))
    f = ease_io(lin(t, *OVER))
    return lerp(2.5, c, f), f


def card_time(i, t):
    return min(max(t, TOPIC[i] - 0.2), topic_end(i) - 0.05)


def draw_cards(fr, t):
    if t > COLLAPSE_T + 0.7:
        return
    c, f = camera(t)
    collapse = ease_in(lin(t, COLLAPSE_T, COLLAPSE_T + 0.6))
    appear = smooth(lin(t, START, START + 0.5))
    order = sorted(range(6), key=lambda i: -abs(i - c))
    m = skia.Matrix()
    m.setScale(1 - collapse, 1 - collapse, 960, 560)
    with view(fr, m):
        for i in order:
            d = i - c
            ad = min(abs(d), 1.0)
            if f > 0.5 and abs(d) > 1.7:
                continue
            x = 960 + d * lerp(310.0, SPACING, f)
            y = 560 + 46 * d * d * f
            scale = lerp(0.26, 1 - 0.3 * ad, f)
            angle = -0.32 * max(-1.5, min(1.5, d)) * f
            alpha = appear * lerp(0.85, 1 - 0.7 * ad, f) * (1 - collapse)
            blur = 7.0 * ad * f
            draw_card(fr, i, card_time(i, t), x, y, scale, angle, alpha, blur)
    if collapse > 0:  # the point they collapse into
        fr.glow_dot(960, 560, 6 + 10 * collapse, "bell", math.sin(math.pi * collapse), strength=1.5)
    if f < 1 or t > COLLAPSE_T:
        return
    k = round(c)
    if k == 5:
        fr.chroma(chroma_kick(t, BREAK6_T, 6.0))


def draw_card(fr, i, t, cx, cy, scale, angle, alpha, blur):
    if alpha <= 0.003:
        return
    quad = card_quad(cx, cy, CARD_W, CARD_H, angle, scale)
    m = quad_matrix(W, H, quad)
    page = skia.Path()
    page.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeWH(W, H), 64, 64))
    with fr.blurred(blur), faded(fr, alpha), view(fr, m):
        hud.glass_card(fr, 0, 0, W, H, 1.0, r=64)
        with clipped(fr, page):
            PAGES[i](fr, t)


# ------------------------------------------------------------------ S23: the board from the opening, once more

POUR = ch0.POUR
POUR_S0, POUR_RATE = 11.0, 7.6  # sim seconds at COLLAPSE_T + 0.3, and sim seconds per narration second


def pour_s(t):
    return POUR_S0 + (t - COLLAPSE_T - 0.3) * POUR_RATE


def board_alpha(t):
    return smooth(lin(t, COLLAPSE_T + 0.3, COLLAPSE_T + 0.8))


def draw_board(fr, t):
    a = board_alpha(t)
    if a <= 0.003:
        return
    bg = 1 - 0.85 * smooth(lin(t, AND_T, AND_T + 0.8))  # it settles to 15 % behind the end screen
    pile = 1 - smooth(lin(t, WATCH_T, WATCH_T + 1.0))  # the pile and its bell clear for the end-screen slots
    zoom = 1.06 - 0.06 * ease_out(lin(t, COLLAPSE_T + 0.3, COLLAPSE_T + 1.2))
    m = skia.Matrix()
    m.setScale(zoom, zoom, 960, 560)
    with view(fr, m), faded(fr, a * bg):
        POUR.draw_frame(fr, 1.0)
        POUR.draw_balls(fr, pour_s(t), pile)
        draw_stream(fr, t, 1.0)
        reveal = ease_io(lin(t, SHAPE_T, SHAPE_T + 0.9))
        if reveal > 0:
            kick = pop(t, ADDUP_T, 0.45)
            ch0.PILE_BELL.draw(fr, reveal=reveal, alpha=pile, width=3.4, glow=0.7 + 1.1 * kick)
            fr.light_sweep(ch0.PILE_BELL.outline(), lin(t, ADDUP_T, ADDUP_T + 0.8), strength=0.95)
            plus = math.sin(math.pi * lin(t, ADDUP_T + 0.6, ADDUP_T + 1.3))
            if plus > 0:
                fr.text("+", 960, POUR.floor - 70, "display", 90, 600, "bell", 0.35 * plus, glow=0.8 * plus)


# the endless pour behind the end screen: a stream through the same pegs, the pile left as it is
STREAM = Board(rows=12, n=2400, rate=14.0, seed=91)
STREAM_T0 = AND_T


def draw_stream(fr, t, a):
    if t < STREAM_T0:
        return
    STREAM.draw_balls(fr, (t - STREAM_T0) + 1.5, a * smooth(lin(t, STREAM_T0, STREAM_T0 + 1.0)), landed_alpha=0.0)


# ------------------------------------------------------------------ S24: e, the end screen

F24 = ((960.0, 470.0), 76.0)
E_IDX = ch3.G_E
SLOT_L = (200.0, 380.0, 680.0, 382.0)
SLOT_R = (1040.0, 380.0, 680.0, 382.0)
E_CENTER = (960.0, 540.0, 300.0)
E_SLOT = (SLOT_L[0] + SLOT_L[2] / 2, SLOT_L[1] + SLOT_L[3] / 2, 190.0)
SUB = (960.0, 905.0, 64.0)


def e_start():
    (x, y), size = F24
    return (*typmath.glyph_centers(ch3.FORMULA, x, y, size)[E_IDX], size)


def draw_formula24(fr, t):
    a = env(t, AND_T + 0.1, E_T + 0.7, 0.4, 0.5)
    if a <= 0.003:
        return
    alphas = {i: 1.0 for i in range(len(typmath.glyphs(ch3.FORMULA)[0]))}
    alphas[E_IDX] = 0.0 if t >= E_T else 1.0  # the e itself is drawn on its own
    (x, y), size = F24
    typmath.draw(fr, ch3.FORMULA, x, y, size, alpha=a, alphas=alphas)


def draw_e(fr, t):
    if t < E_T:  # until "number e" it is still part of the formula
        return
    sx, sy, ss = e_start()
    u = ease_io(lin(t, E_T, E_T + 0.9))
    v = ease_io(lin(t, WATCH_T, WATCH_T + 0.8))
    cx, cy, cs = E_CENTER
    lx, ly, ls = E_SLOT
    x = lerp(lerp(sx, cx, u), lx, v)
    y = lerp(lerp(sy, cy, u), ly, v) - 60 * math.sin(math.pi * u) * (1 - v)
    size = lerp(lerp(ss * 0.62, cs, u), ls, v)
    glow = 0.6 + 1.2 * pop(t, E_T + 0.9, 0.5) + 0.8 * pop(t, WHY_T, 0.6)
    typmath.draw(fr, tc("e", "e"), x, y, size, alpha=1.0, glow=glow)


def slot_path(rect):
    x, y, w, h = rect
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), 22, 22))
    return p


def trace(fr, path, u, color, width, alpha, glow):
    """Stroke the first ``u`` of a path's length."""
    if u <= 0:
        return
    meas = skia.PathMeasure(path, False)
    out = skia.Path()
    meas.getSegment(0, meas.getLength() * clamp01(u), out, True)
    fr.path_stroke(out, color, width, alpha, glow=glow)


def draw_end_screen(fr, t):
    sa = smooth(lin(t, WATCH_T, WATCH_T + 0.5))
    if sa <= 0.003:
        return
    breathe = 0.5 + 0.5 * math.sin(2 * math.pi * (t - SPEECH_END) / 4.0) if t > SPEECH_END else 0.5
    for rect, color, caption, lit_t in (
        (SLOT_L, "e", "why e is everywhere", WHY_T),
        (SLOT_R, "muted", "Laplace transform", THANKS_T),
    ):
        x, y, w, h = rect
        hud.glass_card(fr, x, y, w, h, sa * 0.6, r=22)
        p = slot_path(rect)
        fr.path_stroke(p, "line", 1.6, sa)
        u = ease_io(lin(t, lit_t, lit_t + 0.9))
        trace(fr, p, u, color, 2.6, sa, 0.6 + 0.3 * breathe)
        if u >= 1:
            fr.light_sweep(p, lin(t, lit_t + 0.9, lit_t + 1.6), strength=0.8)
        ca = sa * smooth(lin(t, lit_t, lit_t + 0.4))
        fr.text(caption, x + w / 2, y + h + 50, "sans", 30, 600, "ink" if color == "e" else "muted", ca)
    ta = smooth(lin(t, THANKS_T, THANKS_T + 0.6))
    if ta > 0.003:
        rise = 16 * (1 - ease_out(lin(t, THANKS_T, THANKS_T + 0.8)))
        fr.text("THE BELL CURVE", 960, 250 + rise, "display", 64, 600, "ink", ta, tracking=0.06)
        fr.text("why it's everywhere", 960, 300 + rise, "sans", 28, 500, "bell", ta)
        fr.light_sweep(
            text_path("THE BELL CURVE", 960, 250 + rise, "display", 64, 600, tracking=0.06),
            lin(t, THANKS_T + 0.6, THANKS_T + 1.4),
            strength=0.9,
        )
        x, y, r = SUB
        fr.circle(x, y, r, "tail", 2.4, ta, glow=0.4 + 0.3 * breathe)
        fr.text("subscribe", x, y + r + 40, "sans", 24, 600, "muted", ta)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_cards(fr, t)
    draw_board(fr, t)
    draw_formula24(fr, t)
    draw_end_screen(fr, t)
    draw_e(fr, t)
    hud.eyebrow(fr, t, "06 · RECAP", 387.4)
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


OFFSET = START
DURATION = END - START
STILLS = [
    387.4,
    388.0,
    388.9,
    391.0,
    392.6,
    393.6,
    395.0,
    397.0,
    398.6,
    400.4,
    401.8,
    403.5,
    405.6,
    407.0,
    408.4,
    409.4,
    411.0,
    412.8,
    414.2,
    416.0,
    419.9,
    421.8,
    424.0,
    425.6,
    426.8,
    428.0,
    429.6,
    431.6,
    433.6,
    434.0,
    435.4,
    436.6,
    438.0,
    439.0,
    440.2,
    441.2,
    445.0,
    450.0,
    461.4,
]
