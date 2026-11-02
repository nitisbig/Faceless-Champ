"""CHAPTER 1 - COUNTING PATHS (S04-S07), 00:56.720 (#168 "Let's") - 01:56.620 (#343 "But").

S04  One peg, two rows   push from the 12-row board into its top peg -> a ball meets the peg, spark -> dashed teal /
                         orange options and a coin flip -> one row: two places (1, 1) -> two rows: three places ->
                         the middle is reached two ways (L then R, R then L) -> the edges only one way.
S05  Pascal's triangle   rows three and four drop in -> faint path fans -> every peg becomes its count, parents feed
                         children -> the counts lift into a glass plaque, row by row, each with a blue bar chart.
S06  Ten rows            the triangle folds into the top of a ten-row board -> path light flows down, 2^10 = 1,024 ->
                         one path to the far left (ten L chips) -> the 252 braid to the middle -> one ball, no push ->
                         every bin's count -> blue bars -> the bell snaps on.
S07  The first secret    pill "secret 1 · counting" -> ten L chips agree, the pointer runs to the edge -> an ordinary
                         row flips its R steps and the pointer walks in -> the pairs cancel, the middle glows.

One FunctionSource on the narration clock (t = narration seconds); beats land 0.15 s before their word cue.
The teaching board is the 12-row board of S01 scaled x3 about its top peg, so the opening push is one zoom.
"""

from __future__ import annotations

import contextlib
import math
from pathlib import Path

import numpy as np
import skia
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw import hud
from components.bell import Bell
from components.galton import Board, binom_row
from components.histogram import Axes, bars_from, draw_bars, spring, stagger
from cues import AUDIO, beat, cue
from faceless_champ.draw import Frame, back, chroma_kick, clamp, ease_in, ease_io, ease_out, env, lin, mix, motion_blur, smooth
from theme import THEME, H, W

START = cue(168)  # 56.72 "Let's go back to the board of pegs."
END = cue(343)  # 116.62 "But a peg ..."

b = beat


@contextlib.contextmanager
def view(fr, m):
    """Draw inside a scale+translate transform (crisp and glow canvases together)."""
    if m is None:
        yield
        return
    fr.c.save()
    fr.g.save()
    fr.c.concat(m)
    fr.g.concat(m)
    try:
        yield
    finally:
        fr.c.restore()
        fr.g.restore()


def scale_about(z, fx_, fy_, dx=0.0, dy=0.0):
    m = skia.Matrix()
    m.setTranslate(-fx_, -fy_)
    m.postScale(z, z)
    m.postTranslate(fx_ + dx, fy_ + dy)
    return m


def comb(n, k):
    return math.comb(n, k) if 0 <= k <= n else 0


def bezier(p0, p1, p2, u):
    u = np.asarray(u, float)
    x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0]
    y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]
    return x, y


def polyline_at(pts, u):
    """Point at fraction ``u`` of a polyline, by segment count (one step per segment)."""
    s = min(max(u, 0.0), 1.0) * (len(pts) - 1)
    i = min(int(s), len(pts) - 2)
    f = s - i
    return pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f


def pop(t, t0, dur=0.35):
    """Scale for a number landing at t0: 0 -> overshoot -> 1."""
    return back(lin(t, t0, t0 + dur)) if t >= t0 else 0.0


def number(fr, s, x, y, t0, t, size=34.0, color="ink", alpha=1.0, glow=0.5):
    """A count that pops in at t0, centred on (x, y), with a short glow kick."""
    k = pop(t, t0)
    if k <= 0.01 or alpha <= 0.003:
        return
    kick = math.exp(-(t - t0) / 0.35)
    sz = size * k
    hud.tabular(fr, s, x, y + sz * 0.36, sz, color, alpha * min(1.0, 3 * k), weight=700, glow=glow * kick)


# ------------------------------------------------------------------ teaching geometry (S04, S05)

TX, TY, TDX, TDY = 960.0, 300.0, 168.0, 120.0  # = S01's board (dx 56, dy 40, top 130) scaled x3 about its top peg
PEG_R, BALL_R = 12.0, 12.0
BUBBLE_R = 30.0


def node(r, k):
    return TX + (k - r / 2) * TDX, TY + r * TDY


def contact(r, k):
    x, y = node(r, k)
    return x, y - PEG_R - BALL_R


def in_cup(r, k):
    x, y = node(r, k)
    return x, y + 12.0


PUSH = (57.3, 58.6)


def push_matrix(t):
    """The overview (S01's board, x1/3) zooming into the teaching board: a scale about (960, 45)."""
    if t >= PUSH[1]:
        return None
    e = ease_io(lin(t, *PUSH))
    return scale_about(math.exp(math.log(1 / 3) * (1 - e)), 960.0, 45.0)


def teach_matrix(t):
    e = ease_io(lin(t, *PUSH)) * (1 - ease_io(lin(t, KEEP_T, KEEP_T + 1.0)))
    cam = scale_about(1 + 0.4 * e, 960.0, 300.0, dy=40.0 * e)  # peg 0 at y 340, the level 2 cups near y 680
    m = push_matrix(t)
    if m is None:
        return cam
    m.postConcat(cam)
    return m


def draw_overview(fr, t):
    a = smooth(lin(t, START, START + 0.5)) * (1 - smooth(lin(t, 57.55, 58.35)))
    if a <= 0.003:
        return
    for r in range(1, 12):
        for k in range(r + 1):
            x, y = node(r, k)
            fr.circle(x, y, PEG_R, "line", alpha=a, fill=True)


# ------------------------------------------------------------------ S04: one peg, two rows

DROP = (58.6, 59.42)  # "A ball meets a peg" (#177-180): contact on "peg"
OPTION_T = (b(183), b(185))  # "left" / "right": dashed teal and orange arcs
COIN_T = b(188)  # "coin flip"
SPLIT_T = b(190)  # "After one row": the ball splits into both futures
ROW2_T = b(200)  # "After two rows"
THREE_T = b(205)  # "three."
MIDDLE_T = b(208)  # "middle one"
KEEP_T = b(232)  # "Keep going"


def option_arc(k):
    """The hop from the top peg into level 1 place k (a small arc up, then down)."""
    p0 = contact(0, 0)
    p2 = in_cup(1, k)
    p1 = (p0[0] + 0.55 * (p2[0] - p0[0]), p0[1] - 40.0)
    return p0, p1, p2


def cup(fr, x, y, alpha, color="line", glow=0.0, width=2.4):
    if alpha <= 0.003:
        return
    w, h, r = 34.0, 24.0, 14.0
    p = skia.Path()
    p.moveTo(x - w, y - h)
    p.lineTo(x - w, y + h - r)
    p.quadTo(x - w, y + h, x - w + r, y + h)
    p.lineTo(x + w - r, y + h)
    p.quadTo(x + w, y + h, x + w, y + h - r)
    p.lineTo(x + w, y - h)
    fr.path_stroke(p, color, width, alpha, glow=glow)


def cup_alpha(r, k, t):
    if r == 1:
        return smooth(lin(t, SPLIT_T, SPLIT_T + 0.4)) * (1 - smooth(lin(t, ROW2_T, ROW2_T + 0.5)))
    if r == 2:
        t0 = THREE_T - 0.25 + 0.12 * k
        return smooth(lin(t, t0, t0 + 0.3)) * (1 - smooth(lin(t, KEEP_T, KEEP_T + 0.45)))
    return 0.0


def draw_cups(fr, t):
    for r in (1, 2):
        for k in range(r + 1):
            a = cup_alpha(r, k, t)
            if a <= 0.003:
                continue
            x, y = node(r, k)
            hot = 0.0
            if r == 2 and k == 1:
                hot = env(t, MIDDLE_T, KEEP_T, 0.35, 0.45) * (0.75 + 0.25 * math.sin(6.0 * (t - MIDDLE_T)))
            cup(fr, x, y, a, mix("line", "ball", hot) if hot > 0 else "line", glow=0.9 * hot, width=2.4 + hot)
    # counts: level 1 on "two places", level 2 after its paths
    fade1 = 1 - smooth(lin(t, ROW2_T, ROW2_T + 0.4))
    for k in range(2):
        x, y = node(1, k)
        number(fr, "1", x, y + 4, b(195) + 0.12 * k, t, size=42, alpha=fade1)
    fade2 = 1 - smooth(lin(t, KEEP_T, KEEP_T + 0.4))
    x, y = node(2, 1)
    number(fr, "2", x, y + 4, ROUTE_DONE[1], t, size=42, color="ball", alpha=fade2, glow=0.9)
    for k in (0, 2):
        x, y = node(2, k)
        number(fr, "1", x, y + 4, ROUTE_DONE[2], t, size=42, alpha=fade2)


def draw_options(fr, t):
    """The two dashed hop arcs ("left" / "right") with their L and R labels."""
    a_all = 1 - smooth(lin(t, SPLIT_T, SPLIT_T + 0.35))
    for k, (t0, color, label) in enumerate(((OPTION_T[0], "left", "L"), (OPTION_T[1], "right", "R"))):
        u = ease_out(lin(t, t0, t0 + 0.45))
        if u <= 0 or a_all <= 0.003:
            continue
        p0, p1, p2 = option_arc(k)
        us = np.linspace(0.0, 0.86 * u, 40)
        xs, ys = bezier(p0, p1, p2, us)
        fr.dashed(xs, ys, color, 3.0, a_all, glow=0.5, on=10, off=8)
        if u > 0.6:
            hud.arrow_head(fr, xs[-3], ys[-3], xs[-1], ys[-1], color, a_all * smooth((u - 0.6) / 0.4), 15.0)
        lx = node(0, 0)[0] + (-1 if k == 0 else 1) * 128
        fr.text(label, lx, node(0, 0)[1] - 6, "sans", 38, 700, color, a_all * smooth(lin(t, t0, t0 + 0.3)), glow=0.5)


def draw_ball(fr, t):
    """The S04 ball: drop, balance on the peg, then split into both level 1 places."""
    if t < DROP[0] or t > b(195) + 0.4:
        return
    x0, y0 = contact(0, 0)
    if t < SPLIT_T:
        if t < DROP[1]:
            u = lin(t, *DROP)
            x, y = x0, y0 - 230 * (1 - u * u)
        else:
            tau = t - DROP[1]
            x, y = x0 + 3.5 * math.sin(9.0 * tau) * math.exp(-1.4 * tau), y0
        fr.glow_dot(x, y, BALL_R, "ball", smooth(lin(t, DROP[0], DROP[0] + 0.12)), strength=1.2)
        return
    u = ease_io(lin(t, SPLIT_T, SPLIT_T + 0.55))
    fade = 1 - smooth(lin(t, b(195), b(195) + 0.25))
    for k in range(2):
        p0, p1, p2 = option_arc(k)
        x, y = bezier(p0, p1, p2, u)
        fr.glow_dot(float(x), float(y), BALL_R * 0.92, "ball", 0.62 * fade, strength=1.0)


def draw_spark(fr, t):
    tau = t - DROP[1]
    if tau < 0 or tau > 0.8:
        return
    x, y = node(0, 0)
    a = math.exp(-tau / 0.22)
    fr.glint(x, y - PEG_R, 46.0, a)
    fr.circle(x, y, PEG_R + 40 * ease_out(min(1.0, tau / 0.5)), "ink", 1.6, 0.8 * (1 - min(1.0, tau / 0.5)))
    fr.circle(x, y, PEG_R * 1.1, "ink", alpha=a, fill=True, glow=0.9 * a)


def draw_coin(fr, t):
    """A coin beside the peg: spins up and lands on L ("like a coin flip")."""
    a = env(t, COIN_T - 0.1, SPLIT_T + 0.6, 0.25, 0.4)
    if a <= 0.003:
        return
    cx, cy, R = 1330.0, 300.0, 58.0
    land = COIN_T + 0.85
    u = lin(t, COIN_T, land)
    ph = 6 * math.pi * ease_out(u)  # three turns, landing face up on L
    y = cy - 80 * math.sin(math.pi * u)
    c = math.cos(ph)
    color = "left" if c > 0 else "right"
    rx = max(2.5, R * abs(c))
    fr.path_fill(ellipse(cx, y + 5, rx, R), "line", a * 0.8)  # rim
    fr.path_fill(ellipse(cx, y, rx, R), color, a * 0.22, glow=0.0)
    fr.path_stroke(ellipse(cx, y, rx, R), color, 3.0, a, glow=0.6)
    fr.path_stroke(ellipse(cx, y, rx * 0.78, R * 0.78), color, 1.4, a * 0.5)
    fr.text("L" if c > 0 else "R", cx, y + 17, "sans", 48, 700, color, a * smooth(clamp((abs(c) - 0.72) / 0.2)))
    if t >= land:  # a soft settle ring
        v = lin(t, land, land + 0.45)
        fr.path_stroke(ellipse(cx, cy, R + 26 * v, R + 26 * v), color, 1.4, a * (1 - v))


def ellipse(x, y, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(x - rx, y - ry, x + rx, y + ry))
    return p


# routes into level 2: (bits, step windows); a step is teal (left) or orange (right)
ROUTES = (
    ((0, 1), ((b(217), b(217) + 0.42), (b(219), b(219) + 0.42))),  # "left then right"
    ((1, 0), ((b(221), b(221) + 0.42), (b(223), b(223) + 0.42))),  # "right then left"
    ((0, 0), ((b(225), b(225) + 0.45), (b(225) + 0.45, b(225) + 0.9))),  # "The edges"
    ((1, 1), ((b(225), b(225) + 0.45), (b(225) + 0.45, b(225) + 0.9))),
)
ROUTE_DONE = (b(219) + 0.42, b(223) + 0.42, b(225) + 0.9)


def route_pts(bits):
    k1 = bits[0]
    x, y = node(2, k1 + bits[1])
    return [contact(0, 0), contact(1, k1), (x, y - 26.0)]


def draw_routes(fr, t):
    fade = 1 - smooth(lin(t, KEEP_T - 0.1, KEEP_T + 0.4))
    if fade <= 0.003:
        return
    for bits, steps in ROUTES:
        pts = route_pts(bits)
        for i, (t0, t1) in enumerate(steps):
            f = ease_io(lin(t, t0, t1))
            if f <= 0:
                break
            (xa, ya), (xb, yb) = pts[i], pts[i + 1]
            color = "right" if bits[i] else "left"
            xe, ye = xa + (xb - xa) * f, ya + (yb - ya) * f
            fr.line(xa, ya, xe, ye, color, 5.0, fade * 0.95, glow=0.6)
            if f < 1.0:
                fr.glow_dot(xe, ye, 8.0, color, fade, strength=1.3)


# ------------------------------------------------------------------ S05: Pascal's triangle

DROP_ROWS = {3: KEEP_T + 0.1, 4: KEEP_T + 0.4}  # "Keep going": rows three and four drop in
FAN_T = b(239)  # "counting paths"
WRITE_T = b(241)  # "Write those counts down"
PLAQUE_T = b(251)  # "Pascal's triangle"
PLAQUE_X, PLAQUE_Y, PLAQUE_DX, PLAQUE_DY = 620.0, 318.0, 124.0, 124.0
CARD = (316.0, 200.0, 608.0, 672.0)
CHART_X, CHART_PITCH, CHART_W, CHART_UNIT = 1390.0, 52.0, 40.0, 17.0
HAND_T, HAND_D = b(265), 0.8  # "With ten rows": the triangle folds into the top of the ten-row board
NUMS = {2: (253, 254, 255), 3: (256, 257, 258, 259), 4: (260, 261, 262, 263, 264)}  # "One, two, one." ...
ROW_SPAN = {2: (b(253), b(256)), 3: (b(256), b(260)), 4: (b(260), b(264) + 0.55)}


def write_at(r):
    return WRITE_T + 0.3 * r


def plaque_node(r, k):
    return PLAQUE_X + (k - r / 2) * PLAQUE_DX, PLAQUE_Y + r * PLAQUE_DY


def level_alpha(r, t):
    """Is level r on the board yet (as pegs or places)?"""
    if r == 0:
        return 1.0
    if r == 1:
        return smooth(lin(t, ROW2_T, ROW2_T + 0.4))
    if r == 2:
        return smooth(lin(t, KEEP_T, KEEP_T + 0.4))
    return smooth(lin(t, DROP_ROWS[r], DROP_ROWS[r] + 0.4))


def node_xy(r, k, t):
    x, y = node(r, k)
    if r in DROP_ROWS:
        y -= 60 * (1 - ease_out(lin(t, DROP_ROWS[r], DROP_ROWS[r] + 0.5)))
    u = ease_io(lin(t, PLAQUE_T, PLAQUE_T + 0.9))
    if u > 0:
        px, py = plaque_node(r, k)
        x, y = x + (px - x) * u, y + (py - y) * u
    v = ease_io(lin(t, HAND_T, HAND_T + HAND_D))
    if v > 0:
        qx, qy = TEN.peg(r, k)
        x, y = x + (qx - x) * v, y + (qy - y) * v
    return x, y


def current_row(t):
    for r, (t0, t1) in ROW_SPAN.items():
        if t0 <= t < t1:
            return r
    return None


def row_level(r, t):
    """Brightness of a row in the plaque while the narration reads the rows out."""
    level = 1.0
    for rr, (t0, t1) in ROW_SPAN.items():
        on = env(t, t0, t1, 0.2, 0.3)
        level = level * (1 - 0.45 * on) if rr != r else level
    return level


def draw_fans(fr, t):
    """Every route down to level 4, faint, brightness by share ("counting paths")."""
    a = env(t, FAN_T, WRITE_T + 1.2, 0.45, 0.6) * 0.55
    if a <= 0.003:
        return
    for r in range(4):
        row = binom_row(r)
        for k in range(r + 1):
            share = row[k] / row.max()
            x0, y0 = node(r, k)
            for bit in (0, 1):
                x1, y1 = node(r + 1, k + bit)
                fr.line(x0, y0, x1, y1, "ball", 1.4 + 1.6 * share, a * (0.25 + 0.75 * share), glow=0.4 * share)


def draw_card(fr, t):
    a = smooth(lin(t, PLAQUE_T, PLAQUE_T + 0.7)) * (1 - smooth(lin(t, HAND_T, HAND_T + 0.45)))
    if a <= 0.003:
        return
    rise = 24 * (1 - ease_out(lin(t, PLAQUE_T, PLAQUE_T + 0.8)))
    x, y, w, h = CARD
    hud.glass_card(fr, x, y + rise, w, h, a, r=28, glow=0.25, glow_color="ball")
    fr.text("PASCAL'S TRIANGLE", x + w / 2, y + 54 + rise, "sans", 22, 700, "muted", a, tracking=0.22)


def parent_arrows(fr, r, k, t, alpha):
    """Tiny arrows from both parents into an inner count as it is written (1 + 1 -> 2)."""
    t0 = write_at(r)
    a = alpha * env(t, t0 - 0.05, t0 + 1.3, 0.2, 0.5)
    if a <= 0.003:
        return
    cx, cy = node_xy(r, k, t)
    for pk in (k - 1, k):
        px, py = node_xy(r - 1, pk, t)
        dx, dy = cx - px, cy - py
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        u = ease_out(lin(t, t0 - 0.05, t0 + 0.3))
        sx, sy = px + ux * (BUBBLE_R + 6), py + uy * (BUBBLE_R + 6)
        ex, ey = sx + (cx - ux * (BUBBLE_R + 8) - sx) * u, sy + (cy - uy * (BUBBLE_R + 8) - sy) * u
        hud.arrow(fr, sx, sy, ex, ey, "ball", 2.2, a * 0.85, glow=0.5, head=11.0)


def draw_nodes(fr, t):
    """Pegs that become count bubbles, lift into the plaque, then shrink onto the ten-row board."""
    if t >= HAND_T + HAND_D:
        return
    hand = ease_io(lin(t, HAND_T, HAND_T + HAND_D))
    swap = smooth(lin(t, HAND_T, HAND_T + 0.4))  # bubbles turn back into pegs early in the flight
    num_fade = 1 - smooth(lin(t, HAND_T, HAND_T + 0.3))
    cur = current_row(t)
    for r in range(5):
        la = level_alpha(r, t)
        if la <= 0.003:
            continue
        wu = smooth(lin(t, write_at(r), write_at(r) + 0.35))
        lvl = row_level(r, t)
        lit = 1.0 if cur == r else 0.0
        counts = binom_row(r)
        for k in range(r + 1):
            x, y = node_xy(r, k, t)
            rad = PEG_R + (BUBBLE_R - PEG_R) * back(wu, 1.2) if wu > 0 else PEG_R
            rad = rad + (TEN.peg_r - rad) * hand
            peg_a = la * max(1 - wu, swap)
            if peg_a > 0.003:
                fr.circle(x, y, rad, "line", alpha=peg_a, fill=True)
            ba = la * wu * (1 - swap)
            if ba > 0.003:
                ring = mix("line", "ball", lit)
                fr.circle(x, y, rad, "bg", alpha=ba, fill=True)
                fr.circle(x, y, rad, ring, 2.0 + 0.8 * lit, ba * (0.6 + 0.4 * lvl), glow=0.6 * lit)
                spoken = NUMS.get(r)
                t_num = b(spoken[k]) if spoken else None
                kick = math.exp(-(t - t_num) / 0.35) if t_num is not None and t >= t_num else 0.0
                size = 30 * (1 + 0.28 * kick)
                hud.tabular(fr, str(int(counts[k])), x, y + size * 0.36, size, "ink",
                            ba * num_fade * (0.45 + 0.55 * lvl), weight=700, glow=0.3 + 0.9 * kick)
            if 0 < k < r and 1 <= r <= 4:
                parent_arrows(fr, r, k, t, la)


def draw_charts(fr, t):
    """A small blue bar chart beside each row of the plaque (rows 2-4 grow bar by bar on their numbers)."""
    a = smooth(lin(t, PLAQUE_T + 0.4, PLAQUE_T + 0.9)) * (1 - smooth(lin(t, HAND_T, HAND_T + 0.4)))
    if a <= 0.003:
        return
    for r in range(5):
        _, ry = plaque_node(r, 0)
        base = ry + 28
        n = r + 1
        lvl = row_level(r, t)
        ra = a * (0.4 + 0.6 * lvl)
        left = CHART_X - (n - 1) / 2 * CHART_PITCH - CHART_W / 2
        fr.dashed([CARD[0] + CARD[2] + 20, left - 26], [ry, ry], "muted", 1.2, ra * 0.35, on=6, off=7)
        fr.line(left - 8, base, left + (n - 1) * CHART_PITCH + CHART_W + 8, base, "line", 1.6, ra)
        body = skia.Path()
        for k, c in enumerate(binom_row(r)):
            if r in NUMS:
                t0 = b(NUMS[r][k])
            else:
                t0 = PLAQUE_T + 0.6 + 0.25 * r + 0.08 * k
            g = float(spring(lin(t, t0, t0 + 0.55)))
            h = c * CHART_UNIT * g
            if h < 0.5:
                continue
            x0 = left + k * CHART_PITCH
            body.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, base - h, x0 + CHART_W, base), 3, 3))
        fr.path_fill(body, "ball", ra * 0.85, glow=0.3 * (1 if current_row(t) == r else 0.4))


# ------------------------------------------------------------------ S06: ten rows

HERO10 = [1, 0, 0, 1, 1, 0, 1, 0, 1, 1]  # one ball, no push: lands in bin 6
NOTHING_T = b(299)  # "Nothing pushes"
TEN = Board(rows=10, cx=960.0, top=170.0, dx=64.0, dy=46.0, peg_r=5.0, ball_r=6.0, n=1, bits=[HERO10],
            release=[NOTHING_T], hop=0.17, fall=0.32, floor=1000.0)
LABEL_Y = TEN.top + TEN.rows * TEN.dy + 36
ROWS_IN = (HAND_T + HAND_D - 0.05, HAND_T + HAND_D + 0.7)
LIGHT = (b(266) + 0.85, b(272))  # the light reaches the bins as "1,024" is said
ONLY_T = b(275)  # "Only one"
FARLEFT_T = b(281)  # "far left bin"
TIMES_T = b(284)  # "left, ten times in a row"
BUT_T = b(290)  # "But"
MID_T = b(291)  # "252"
MID_LIGHT = (MID_T, MID_T + 1.0)
MID_DONE = MID_T + 1.15
THERE_T = b(306)  # "There are simply far more ways"
BARS_T = b(309)  # "far more ways"
SNAP_T = b(313)  # "get there"
HS = 1.15  # px per path in a bin
SD10 = math.sqrt(10) / 2
BINS = bars_from(np.arange(11), binom_row(10) / 1024.0)
BAX = Axes(cx=TEN.cx, floor=TEN.floor, unit=TEN.dx * SD10, hscale=HS * 1024 / SD10)
BELL = Bell(BAX, -3.5, 3.5)


def _shares():
    every, middle = {}, {}
    for r in range(10):
        row = binom_row(r)
        mid = {(k, bit): comb(r, k) * comb(9 - r, 5 - k - bit) for k in range(r + 1) for bit in (0, 1)}
        top = max(mid.values())
        for k in range(r + 1):
            for bit in (0, 1):
                every[(r, k, bit)] = row[k] / row.max()
                middle[(r, k, bit)] = mid[(k, bit)] / top
    return every, middle


EVERY, MIDDLE = _shares()


def draw_light(fr, R, alpha, shares, color="ball", gamma=1.0, width=2.4, floor=0.04):
    """Route segments down to fractional row ``R``; brightness = share of the routes counted."""
    if alpha <= 0.003 or R <= 0:
        return
    for r, k, bit, p0, p1 in TEN._segments(10):
        if r >= R:
            break
        s = shares[(r, k, bit)]
        if s <= 0 and floor <= 0:
            continue
        f = min(1.0, R - r)
        w = s ** gamma
        x1, y1 = p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f
        fr.line(p0[0], p0[1], x1, y1, color, width * (0.55 + 0.65 * w), alpha * (floor + (1 - floor) * w),
                glow=0.7 * w)


def bin_glow(fr, k, color, alpha):
    if alpha <= 0.003:
        return
    x = float(TEN.bin_x(k))
    fr.rrect(x - TEN.dx / 2 + 4, TEN.wall_top, TEN.dx - 8, TEN.floor - TEN.wall_top, 8, fill=color,
             fill_alpha=0.10 * alpha, alpha=alpha)


def label_color(k, t):
    if k == 0:
        return mix("left", "ink", smooth(lin(t, BUT_T, BUT_T + 0.5)))
    if k == 5:
        return mix("ball", "ink", smooth(lin(t, THERE_T, THERE_T + 0.6)))
    return "ink"


def label_t0(k):
    if k == 0:
        return FARLEFT_T
    if k == 5:
        return MID_DONE
    return THERE_T + 0.1 + 0.08 * k


def draw_ten(fr, t, fade):
    """The ten-row board, its lights, labels, bars and bell (inside the S07 shift)."""
    if t < ROWS_IN[0]:
        return
    rows = 5 + 5 * ease_out(lin(t, *ROWS_IN))
    flash = TEN.hit_flash(0, t)
    TEN.draw_frame(fr, fade, rows_shown=rows, funnel=False, flash=flash)
    # 1,024: every route, flowing down row by row
    every_a = smooth(lin(t, LIGHT[0], LIGHT[0] + 0.15)) * (1 - 0.8 * smooth(lin(t, ONLY_T, ONLY_T + 0.45)))
    every_a *= 1 - smooth(lin(t, BUT_T, BUT_T + 0.45))
    draw_light(fr, 10 * lin(t, *LIGHT), every_a, EVERY, gamma=1.3)
    # only one: the far-left route
    left_a = env(t, ONLY_T, BUT_T + 0.3, 0.3, 0.45)
    TEN.draw_path(fr, [0] * 10, ease_io(lin(t, ONLY_T, ONLY_T + 0.7)), left_a, width=4.0, glow=0.8)
    bin_glow(fr, 0, "left", env(t, FARLEFT_T, BUT_T + 0.3, 0.3, 0.45))
    # 252: the braid into the middle bin
    mid_a = smooth(lin(t, MID_LIGHT[0], MID_LIGHT[0] + 0.15)) * (1 - 0.65 * smooth(lin(t, NOTHING_T, NOTHING_T + 0.5)))
    mid_a *= 1 - smooth(lin(t, THERE_T, THERE_T + 0.7))
    draw_light(fr, 10 * lin(t, *MID_LIGHT), mid_a, MIDDLE, gamma=0.8, width=3.0, floor=0.0)
    bin_glow(fr, 5, "ball", env(t, MID_DONE - 0.2, THERE_T + 0.4, 0.3, 0.5))
    # one ball, nothing pushing it
    TEN.draw_hero(fr, 0, t, env(t, NOTHING_T - 0.05, BARS_T - 0.05, 0.1, 0.3), trail=0.3, size=1.7)
    # every bin's count, then blue bars, then the bell
    for k, c in enumerate(binom_row(10)):
        x = float(TEN.bin_x(k))
        number(fr, f"{c}", x, LABEL_Y, label_t0(k), t, size=25, color=label_color(k, t), alpha=fade * 0.92, glow=0.6)
    grow = stagger(t, BARS_T, 11, spread=0.5, dur=0.6)
    hl = {5: 0.45 * smooth(lin(t, 116.0, 116.45))}
    draw_bars(fr, BAX, BINS, alpha=1.0, grow=grow, gap=0.16, glow=0.3, highlight=hl if hl[5] > 0 else None)
    BELL.snap(fr, t, SNAP_T, width=3.2)


def draw_runner(fr, t):
    """Ten L chips down the left edge, one per row, with a teal ball racing down the far-left route."""
    a = env(t, TIMES_T - 0.05, BUT_T + 0.35, 0.15, 0.4)
    if a <= 0.003:
        return
    for i in range(10):
        t0 = TIMES_T + 0.155 * i
        u = smooth(lin(t, t0, t0 + 0.2))
        if u <= 0:
            continue
        px, py = TEN.peg(i, 0)
        chip(fr, px - 46, py, "L", a * u, size=30.0 * (0.7 + 0.3 * back(lin(t, t0, t0 + 0.3))))
    pts, _ = TEN.route([0] * 10)
    u = lin(t, TIMES_T, TIMES_T + 1.65)
    if 0 < u < 1:
        x, y = polyline_at(pts, u)
        fr.glow_dot(x, y, 7.0, "left", a, strength=1.3)


def chip(fr, x, y, letter, alpha, size=56.0, sx=1.0, glow=0.3):
    """A step chip: teal L or orange R; ``sx`` squashes it horizontally (a flip)."""
    if alpha <= 0.003 or sx <= 0.01:
        return
    color = "left" if letter == "L" else "right"
    w = size * sx
    fr.rrect(x - w / 2, y - size / 2, w, size, min(size * 0.22, w / 2), fill=color, fill_alpha=0.16, stroke=color,
             width=2.2, alpha=alpha, glow=glow)
    la = smooth(clamp((sx - 0.35) / 0.4))
    fr.text(letter, x, y + size * 0.18, "sans", size * 0.5, 700, color, alpha * la)


def draw_counts_hud(fr, t):
    """The live path counter and its Typst formulas (top right)."""
    a = env(t, LIGHT[0], NOTHING_T + 0.3, 0.3, 0.5)
    if a > 0.003:
        if t < ONLY_T:
            R = 10 * lin(t, *LIGHT)
            v, color = 2 ** min(10, int(R)), "ball"
        elif t < MID_T:
            v, color = 1, "left"
        else:
            v, color = max(1, round(252 * ease_out(lin(t, MID_T, MID_DONE)))), "ball"
        hud.readout(fr, 1600, 210, "paths", f"{v:,}", color, a, size=36)
    ta = env(t, b(272), ONLY_T, 0.35, 0.35)
    typmath.draw(fr, '2^(10) = "1,024"', 1600, 310, 48, color="ink", alpha=ta, reveal=lin(t, b(272), b(272) + 0.6))
    ba = env(t, MID_DONE, NOTHING_T + 0.3, 0.35, 0.5)
    typmath.draw(fr, "binom(10, 5) = 252", 1600, 320, 46, color="ink", alpha=ba,
                 reveal=lin(t, MID_DONE, MID_DONE + 0.6))


def draw_no_push(fr, t):
    """Dashed inward 'push' arrows, struck out: nothing pushes the balls toward the centre."""
    a = env(t, NOTHING_T, THERE_T, 0.3, 0.4)
    if a <= 0.003:
        return
    strike = ease_out(lin(t, b(300), b(300) + 0.35))
    y = 400.0
    for x0, x1 in ((470.0, 720.0), (1450.0, 1200.0)):
        hud.arrow(fr, x0, y, x1, y, "muted", 2.6, a * (1 - 0.5 * strike), glow=0.2, dashed=True)
        if strike > 0:
            mx = (x0 + x1) / 2
            fr.line(mx - 34, y + 34, mx - 34 + 68 * strike, y + 34 - 68 * strike, "ink", 3.0, a, glow=0.4)


# ------------------------------------------------------------------ S07: the first secret

SHIFT = (cue(315), cue(315) + 0.95)  # "That is the first secret": board clears, bars and bell move up
SHIFT_Y = -140.0
SECRET_T = b(318)
EXTREME_T = b(324)  # "extreme result": ten teal L chips
AGREE_RUN = (b(327), b(331) + 0.1)  # "every random step to agree": the pointer runs to the edge
LOCK_T = b(331)
ORDINARY_T = b(333)  # "ordinary result"
ROW = "LRRLRLLRLR"
R_IDX = [i for i, s in enumerate(ROW) if s == "R"]
FLIP_T = [ORDINARY_T + 0.15 + 0.3 * j for j in range(len(R_IDX))]
FLIP_D = 0.32
CANCEL_T = b(340)  # "roughly cancel out"
CHIPS_Y = 420.0


def pointer_k(t):
    k = 5 - 5 * ease_io(lin(t, *AGREE_RUN))
    for tf in FLIP_T:
        k += smooth(lin(t, tf + 0.12, tf + 0.45))
    return k


def draw_pointer(fr, t):
    """A pointer under the bins (in the shifted frame) and the paths count of the bin it points at."""
    a = smooth(lin(t, EXTREME_T, EXTREME_T + 0.4))
    if a <= 0.003:
        return
    k = pointer_k(t)
    x = float(TEN.bin_x(k))
    y = TEN.floor + 12
    kk = round(k)
    color = mix("left", "ball", min(1.0, k))
    settle = 0.6 * smooth(lin(t, 116.0, 116.45))
    path = skia.Path()
    path.addPoly([skia.Point(x, y), skia.Point(x - 13, y + 22), skia.Point(x + 13, y + 22)], True)
    fr.path_fill(path, color, a, glow=0.6 + settle)
    n = comb(10, kk)
    fr.text(f"{n} path" + ("" if n == 1 else "s"), x, y + 58, "sans", 26, 600, color, a)


def chips_x(t):
    lock = smooth(lin(t, LOCK_T - 0.1, LOCK_T + 0.25)) * (1 - smooth(lin(t, ORDINARY_T, ORDINARY_T + 0.35)))
    pitch = 72.0 - 12.0 * lock
    return [960.0 + (i - 4.5) * pitch for i in range(10)], lock


def draw_chips(fr, t):
    if t < EXTREME_T:
        return
    xs, lock = chips_x(t)
    # the locked row: one teal outline around ten agreeing steps
    if lock > 0.003:
        x0, x1 = xs[0] - 36, xs[-1] + 36
        pulse = math.exp(-max(0.0, t - LOCK_T - 0.25) / 0.5)
        fr.rrect(x0, CHIPS_Y - 40, x1 - x0, 80, 18, stroke="left", width=2.4, alpha=lock, glow=0.4 + 0.9 * pulse)
    for i, x in enumerate(xs):
        t0 = EXTREME_T + 0.05 * i
        u = ease_out(lin(t, t0, t0 + 0.55))
        if u <= 0:
            continue
        x = -60 + (x + 60) * u
        y = CHIPS_Y
        letter, sx = "L", 1.0
        if i in R_IDX:
            tf = FLIP_T[R_IDX.index(i)]
            f = lin(t, tf, tf + FLIP_D)
            sx = abs(math.cos(math.pi * f))
            letter = "R" if f >= 0.5 else "L"
        p, size = i // 2, 56.0
        tc0 = CANCEL_T + 0.22 * p
        c = lin(t, tc0, tc0 + 0.45)
        if c > 0:  # the pair (2p, 2p+1) slides together and cancels
            mid = (xs[2 * p] + xs[2 * p + 1]) / 2
            x = x + (mid - x) * ease_in(c)
            size *= 1 - c * c
            if c >= 0.8:
                fl = lin(t, tc0 + 0.36, tc0 + 0.75)
                fr.circle(mid, y, 10 + 40 * ease_out(fl), "light", 1.6, 0.8 * (1 - fl))
                fr.glow_dot(mid, y, 5.0, "light", 1 - fl, strength=1.2)
        if size > 1.0:
            chip(fr, x, y, letter, smooth(min(1.0, u * 1.5)), size=size, sx=sx, glow=0.3 + 0.5 * lock)
    if t >= CANCEL_T:  # the flashes after the chips are gone
        for p in range(5):
            tc0 = CANCEL_T + 0.22 * p
            fl = lin(t, tc0 + 0.36, tc0 + 0.75)
            if t > tc0 + 0.45 and fl < 1:
                mid = (xs[2 * p] + xs[2 * p + 1]) / 2
                fr.circle(mid, CHIPS_Y, 10 + 40 * ease_out(fl), "light", 1.6, 0.8 * (1 - fl))


def draw_pill(fr, t):
    a = smooth(lin(t, SECRET_T, SECRET_T + 0.5))
    if a > 0.003:
        rise = 14 * (1 - ease_out(lin(t, SECRET_T, SECRET_T + 0.6)))
        hud.pill(fr, 960, 150 + rise, "secret 1 · counting", "bell", a, 28)


# ------------------------------------------------------------------ assembly


def draw_teach(fr, t):
    with view(fr, teach_matrix(t)):
        draw_overview(fr, t)
        draw_fans(fr, t)
        draw_card(fr, t)
        draw_charts(fr, t)
        draw_cups(fr, t)
        draw_routes(fr, t)
        draw_options(fr, t)
        draw_nodes(fr, t)
        draw_spark(fr, t)
        draw_ball(fr, t)


def draw_one(t, size):
    fr = Frame(size)
    if t < HAND_T + HAND_D:
        draw_teach(fr, t)
    draw_coin(fr, t)
    shift = smooth(lin(t, *SHIFT))
    fade = 1 - smooth(lin(t, SHIFT[0], SHIFT[1] - 0.15))
    m = scale_about(1.0, 0.0, 0.0, 0.0, SHIFT_Y * shift) if shift > 0 else None
    with view(fr, m):
        draw_ten(fr, t, fade)
        if t >= SHIFT[0]:
            BAX.floor_line(fr, -3.6, 3.6, smooth(lin(t, SHIFT[0], SHIFT[1])), "line", 2.0)
        draw_runner(fr, t)
        draw_pointer(fr, t)
    draw_counts_hud(fr, t)
    draw_no_push(fr, t)
    draw_pill(fr, t)
    draw_chips(fr, t)
    hud.eyebrow(fr, t, "01 · COUNTING PATHS", 57.0)
    fr.chroma(chroma_kick(t, DROP[1], 3.0))
    fr.chroma(chroma_kick(t, SNAP_T + 0.6, 4.0))
    inn = 1 - smooth(lin(t, START, START + 0.45))
    if inn > 0:
        fr.zoom_blur(0.3 * inn)
        fr.dim(inn)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def blur_weight(t):
    fast = (DROP[0] - 0.1 <= t <= DROP[1] + 0.1) or (NOTHING_T <= t <= NOTHING_T + 2.3)
    return 1.0 if fast else 0.0


def draw(t, size):
    t = t + START
    return motion_blur(draw_one, t, size, weight=blur_weight(t))


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


OFFSET = START
DURATION = END - START
STILLS = [57.2, 58.1, 60.8, 62.2, 63.9, 65.8, 67.0, 70.6, 72.4, 74.0, 76.4, 77.9, 79.0, 80.6, 82.4, 85.0, 89.2,
          90.2, 92.0, 95.8, 97.0, 99.0, 100.4, 102.8, 105.6, 106.6, 108.5, 110.4, 111.5, 112.6, 114.3, 115.6, 116.4]
