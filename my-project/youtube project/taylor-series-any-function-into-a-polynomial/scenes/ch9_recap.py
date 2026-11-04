"""CHAPTER 9 · RECAP AND OUTRO, 12:28.080 – 13:57.008 (cue #2004 "So" → end of narration + the 20 s end screen).

S47  What we built I      five memories float on an arc, each a live replay of the film itself (no cards): the camera
                          starts wide, then trucks along the arc -> the Chip's pads fire, 3x² − 2x + 5 -> the cos hug,
                          P₀ on "value", the tangent on "slope", P₂ on "bend", P₄ -> P₆, the ladder filling -> the exponent
                          drop, 120/120 cancels on "cancels"
S48  What we built II     the fraction bar locks 2.718 -> the vine climbs -> the Chip's display lands 0.4794 "in a blink" ->
                          the pink disk grows to the poles and springs
S49  Next time: e meets i the eˣ series row; every x becomes i x; the powers evaluate; the terms sort by flight, real down,
                          imaginary up -> cos x and i sin x -> e^(ix) = cos x + i sin x, faint -> a point runs the unit
                          circle while its shadows trace an ink cosine and sine
S50  One term at a time   sine's pieces on the S04 depth stack -> the camera turns to the front, they slide together ->
                          the last term clicks in, the copy hugs the wave, a light sweep over "Taylor series"
S51  End screen           20 s: the gold copy climbing the sine at 15 % opacity, two end-screen slots and a subscribe ring

The memories render the earlier chapters' own draw functions on a time map tied to these words (live for the pane
in focus, cached stills for the rest); the cos hug in memory 2 is drawn fresh at the recap's pace.
"""

from __future__ import annotations

import math
from functools import lru_cache
from importlib import import_module
from pathlib import Path

import numpy as np
import skia
from components import taylor as T
from components.fx import layer_alpha
from components.ladder import Ladder
from components.motion import spring
from components.stack25d import TermStack, terms_of
from components.stage import TaylorStage
from cues import AUDIO, AUDIO_DURATION, TOTAL, beat, cue
from theme import SERIF, THEME, H, W

from faceless_champ.draw import LINEAR, Frame, ease_io, ease_out, hud, lin, pulse, smooth, text_path
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc
from faceless_champ.draw.space import Camera, orbit
from scenes import ch8_matters as ch8

START = cue(2004)  # 748.08 "So let's look back"
END = TOTAL  # 837.008: narration ends at 817.008, then 20 s of end screen

b = beat

S47, S48, S49, S50, S51 = START, cue(2070), cue(2122), cue(2172), AUDIO_DURATION

X = tc("x", "x")
I = tc("error", "i")

# ------------------------------------------------------------------ S47–S48 · the memory arc

PW, PH = 16.0, 9.0  # pane size, world units
RC = 36.0  # arc radius; the panes face its centre
DPHI = 0.5  # angle between panes
FOCAL = 1100.0
D_NEAR = PW * FOCAL / 1240.0  # a pane in focus is 1240 px wide
D_WIDE = 34.0  # the opening overview
C = np.array([0.0, 0.0, -RC])


def dir_(phi):
    return np.array([math.sin(phi), 0.0, math.cos(phi)])


def pane_frame(i):
    """Centre, right and up vectors of pane i (it faces the arc's centre)."""
    phi = (i - 2) * DPHI
    p = C + RC * dir_(phi)
    r = np.array([math.cos(phi), 0.0, -math.sin(phi)])
    return p, r, np.array([0.0, 1.0, 0.0])


# (dest time, source time) knots per memory; a memory may cut between two chapters
FOCUS = [S47, b(2026) - 0.2, b(2052) - 0.25, S48 - 0.15, b(2097) + 0.3, S49]
CLIPS = [
    [("ch0_open", [(S47, 5.2), (cue(2017), 8.9)]), ("ch1_polynomials", [(b(2018), 88.7), (b(2025), 92.4)])],
    [("match", None)],
    [("ch3_factorials", [(FOCUS[2], 272.6), (b(2064), 281.13), (FOCUS[3], 283.8)])],
    [
        ("ch5_e", [(FOCUS[3], 413.4), (b(2082), 421.9)]),
        ("ch6_sine", [(b(2084), 491.3), (b(2093), 503.0)]),
        ("ch0_open", [(b(2094) - 0.1, 22.9), (b(2096) + 0.6, 24.6)]),
    ],
    [("ch7_breaks", [(FOCUS[4], 660.4), (b(2107), 664.4), (b(2114), 666.4), (S49, 671.6)])],
]
STILL = [
    ("ch0_open", 9.0),
    ("match", b(2046) + 1.0),
    ("ch3_factorials", 281.6),
    ("ch5_e", 422.3),
    ("ch7_breaks", 667.0),
]


def focus(t):
    """Continuous pane index in focus (the camera trucks between panes in 0.7 s)."""
    s = 0.0
    for i in range(1, 5):
        s += ease_io(lin(t, FOCUS[i] - 0.35, FOCUS[i] + 0.35))
    return s


def arc_cam(t):
    s = focus(t)
    phi = (s - 2) * DPHI
    wide = 1 - ease_io(lin(t, START + 0.9, b(2012)))
    d = D_NEAR + (D_WIDE - D_NEAR) * wide
    target = C + RC * dir_(phi)
    eye = target - d * dir_(phi) + np.array([0.0, 2.2 * wide, 0.0])
    return Camera(eye, target + np.array([0.0, -0.6 * wide, 0.0]), FOCAL, (960.0, 520.0))


def source_time(knots, t):
    ts = [k[0] for k in knots]
    vs = [k[1] for k in knots]
    return float(np.interp(t, ts, vs))


def clip_at(i, t):
    """(module name, source time, alpha) for the clips of memory i that are visible at t (0.3 s cuts)."""
    clips = CLIPS[i]
    if clips[0][1] is None:
        return [(clips[0][0], t, 1.0)]
    starts = [kn[0][0] for _, kn in clips]
    out = []
    for k, (name, kn) in enumerate(clips):
        a_in = 1.0 if k == 0 else smooth(lin(t, starts[k] - 0.15, starts[k] + 0.15))
        a_out = 1.0 if k == len(clips) - 1 else 1 - smooth(lin(t, starts[k + 1] - 0.15, starts[k + 1] + 0.15))
        a = a_in * a_out
        if a > 0.003:
            out.append((name, source_time(kn, t), a))
    return out


def render_source(name, ts, size):
    if name == "match":
        return draw_match(ts, size)
    return import_module(f"scenes.{name}").draw_one(ts, size)


@lru_cache(maxsize=8)
def still(i, size):
    name, ts = STILL[i]
    return to_image(render_source(name, ts, size))


def to_image(arr):
    return skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.ColorType.kRGBA_8888_ColorType)


def draw_image_quad(fr, img, quad, alpha, blur=0.0, radius=26.0):
    w, h = img.width(), img.height()
    src = [skia.Point(0, 0), skia.Point(w, 0), skia.Point(w, h), skia.Point(0, h)]
    dst = [skia.Point(float(x), float(y)) for x, y in quad]
    m = skia.Matrix()
    if not m.setPolyToPoly(src, dst):
        return
    paint = skia.Paint(Alphaf=alpha, AntiAlias=True)
    if blur > 0.05:
        paint.setImageFilter(skia.ImageFilters.Blur(blur, blur))
    fr.c.save()
    fr.c.concat(m)
    fr.c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeWH(w, h), radius * w / 1240, radius * w / 1240), True)
    fr.c.drawImage(img, 0, 0, LINEAR, paint)
    fr.c.restore()


def quad_of(cam, i, mirror=False):
    p, r, u = pane_frame(i)
    hw, hh = PW / 2, PH / 2
    if mirror:  # the reflection on the floor below the pane
        p = p - u * (PH + 0.5)
        u = -u
    pts = np.array([p - r * hw + u * hh, p + r * hw + u * hh, p + r * hw - u * hh, p - r * hw - u * hh])
    xs, ys, _ = cam.project(pts)
    return list(zip(xs, ys)), min(cam.depth(q) for q in pts)


def draw_arc(fr, t):
    a = smooth(lin(t, START - 0.1, START + 0.6)) * (1 - smooth(lin(t, S49 - 0.1, S49 + 0.6)))
    if a <= 0.003:
        return
    cam = arc_cam(t)
    s = focus(t)
    k = fr.k
    live = round(s) if t >= b(2012) - 0.3 else None
    order = sorted(range(5), key=lambda i: -cam.depth(pane_frame(i)[0]))
    for i in order:
        quad, depth = quad_of(cam, i)
        if depth <= 0.5:
            continue
        w = max(0.0, 1 - abs(s - i)) if live is not None else 0.0
        wide = 1 - ease_io(lin(t, START + 0.9, b(2012)))  # the overview shows every memory clearly
        pa = a * max(0.4 + 0.6 * w, 0.85 * wide)
        blur = (1 - w) * (1 - wide) * 6.0 * k
        if i == live:
            layers = [
                (to_image(render_source(name, ts, (int(1240 * k), int(698 * k)))), ca) for name, ts, ca in clip_at(i, t)
            ]
        else:
            layers = [(still(i, (int(620 * k), int(349 * k))), 1.0)]
        rq, rdepth = quad_of(cam, i, mirror=True)
        for img, ca in layers:
            if rdepth > 0.5:
                draw_image_quad(fr, img, rq, 0.09 * pa * ca, blur + 4 * k)
            draw_image_quad(fr, img, quad, pa * ca, blur)
        if w > 0.6:  # a hairline of light along the top edge of the pane in focus
            (x0, y0), (x1, y1) = quad[0], quad[1]
            fr.line(x0 + 30, y0, x1 - 30, y1, "light", 1.0, 0.25 * a * (w - 0.6) / 0.4, glow=0.4)


# --- memory 2: the cos hug at the recap's pace

COS = TaylorStage("cos", view=(-4.4, 4.4, -1.7, 1.7), rect=(110.0, 230.0, 1080.0, 640.0))
LADDER = Ladder(x=1300.0, y=270.0, rows=5, w=480.0)
HUG_T = [b(2042), b(2044), b(2046)]
FILLS = [(b(2036), 1), (b(2039), 0), (b(2042), -1), (b(2044), 0), (b(2045), 1)]


def draw_match(t, size):
    fr = Frame(size)
    COS.static(fr, 1.0, labels=False)
    COS.original(fr, 1.0, reveal=ease_io(lin(t, FOCUS[1] - 0.3, FOCUS[1] + 0.9)))
    pa = smooth(lin(t, b(2031), b(2031) + 0.4))
    if pa > 0.003:
        COS.probe(fr, 0.0, pa)
    ca = smooth(lin(t, b(2036), b(2036) + 0.3))
    if ca > 0.003:
        c, _, sp = COS.chain(t, [0, 2, 4, 6], HUG_T)
        COS.copy(fr, c, ca, glow=0.6 + 0.5 * sp)
    ta = pulse(t, b(2039) + 0.3, 1.0)  # "slope": the tangent at 0 lights, flat
    if ta > 0.003:
        x0, y0 = COS.ax.at(-1.6, 1.0)
        x1, y1 = COS.ax.at(1.6, 1.0)
        fr.line(x0, y0, x1, y1, "x", 3.0, ta, glow=0.6)
    LADDER.draw(fr, t, fills=FILLS, card=False, alpha=smooth(lin(t, FOCUS[1], FOCUS[1] + 0.5)))
    return fr.finish()


# ------------------------------------------------------------------ S49 · e meets i

ROW_Y, UP_Y, LOW_Y, SZ = 470.0, 380.0, 640.0, 60.0
# (x-form, i-form, evaluated, imaginary?)
TERMS = [
    ("1", "1", "1", False),
    (f"+ {X}", f"+ {I} {X}", f"+ {I} {X}", True),
    (f"+ {X}^2/2!", f"+ ({I} {X})^2/2!", f"- {X}^2/2!", False),
    (f"+ {X}^3/3!", f"+ ({I} {X})^3/3!", f"- {I} {X}^3/3!", True),
    (f"+ {X}^4/4!", f"+ ({I} {X})^4/4!", f"+ {X}^4/4!", False),
    (f"+ {X}^5/5!", f"+ ({I} {X})^5/5!", f"+ {I} {X}^5/5!", True),
]
DOTS = "+ dots.c"
LEAD_X = f"e^{X} ="
LEAD_I = f"e^({I} {X}) ="
I_T = b(2137)  # "imaginary"
EVAL_T = [b(2141) + 0.28 * k for k in range(6)]  # the powers evaluate left to right
SORT_T = (b(2147), b(2150) + 0.4)
COS_T, SIN_T, EULER_T = b(2155), b(2157), b(2160)
CIRCLE_T = b(2163)
GAP = 16.0


def _rows_x0():
    up = [f"{I} {X}", f"- {I} {X}^3/3!", f"+ {I} {X}^5/5!", DOTS, f"= {I} sin {X}"]
    w = sum(typmath.size_of(e, SZ)[0] for e in up) + GAP * 3 + 24
    return 960 - w / 2


ROWS_X0 = _rows_x0()


def lay(exprs, y, size, x0=None):
    ws = [typmath.size_of(e, size)[0] for e in exprs]
    total = sum(ws) + GAP * (len(ws) - 1)
    x = 960 - total / 2 if x0 is None else x0
    out = []
    for w in ws:
        out.append((x + w / 2, y))
        x += w + GAP
    return out, x


def first(e):
    """Drop a leading '+ ' when a term opens its row."""
    return e.removeprefix("+ ")


def draw_series(fr, t):
    a = smooth(lin(t, S49 + 0.2, S49 + 0.8)) * (1 - smooth(lin(t, CIRCLE_T - 0.3, CIRCLE_T + 0.4)))
    if a <= 0.003:
        return
    mi = ease_io(lin(t, I_T, I_T + 0.6))
    lead = LEAD_I if mi > 0.5 else LEAD_X
    # the single row: x-forms -> i-forms -> evaluated
    row = []
    for k, (ex, ei, ev, _) in enumerate(TERMS):
        e_from, e_to, u = (ex, ei, mi) if t < EVAL_T[k] else (ei, ev, ease_io(lin(t, EVAL_T[k], EVAL_T[k] + 0.4)))
        row.append((e_from, e_to, u))
    widest = [max(e_from, e_to, key=lambda e: typmath.size_of(e, SZ)[0]) for e_from, e_to, _ in row]
    pos, _ = lay([lead, *widest, DOTS], ROW_Y, SZ)
    # the sorted rows: imaginary up, real down
    up = [k for k, term in enumerate(TERMS) if term[3]]
    low = [k for k, term in enumerate(TERMS) if not term[3]]
    up_e = [first(TERMS[k][2]) if j == 0 else TERMS[k][2] for j, k in enumerate(up)] + [DOTS]
    up_pos, up_end = lay(up_e, UP_Y, SZ, ROWS_X0)
    low_pos, low_end = lay([TERMS[k][2] for k in low] + [DOTS], LOW_Y, SZ, ROWS_X0)
    su = ease_io(lin(t, *SORT_T))
    lead_y = ROW_Y + (215.0 - ROW_Y) * ease_io(lin(t, SORT_T[0], SORT_T[0] + 0.8))
    lead_e = lead if t < EULER_T else f"e^({I} {X}) = cos {X} + {I} sin {X}"
    if t < EULER_T:
        lx = pos[0][0] + (960 - pos[0][0]) * ease_io(lin(t, SORT_T[0], SORT_T[0] + 0.8))
        typmath.morph(fr, LEAD_X, LEAD_I, mi, lx, lead_y, SZ, a) if mi < 1 else typmath.draw(
            fr, lead_e, lx, lead_y, SZ, None, a
        )
    else:
        m = ease_io(lin(t, EULER_T, EULER_T + 0.8))
        typmath.morph(fr, LEAD_I, lead_e, m, 960, 215.0, SZ, a * (1 - 0.35 * m), glow=0.2 * m)
    for k, (e_from, e_to, u) in enumerate(row):
        (x0, y0) = pos[k + 1]
        if TERMS[k][3]:
            j = up.index(k)
            (x1, y1), tgt = up_pos[j], (first(TERMS[k][2]) if j == 0 else TERMS[k][2])
        else:
            j = low.index(k)
            (x1, y1), tgt = low_pos[j], TERMS[k][2]
        if su <= 0:
            typmath.morph(fr, e_from, e_to, u, x0, y0, SZ, a)
        else:
            arc = -60.0 if TERMS[k][3] else 60.0
            typmath.morph(fr, TERMS[k][2], tgt, su, x0, y0, SZ, a, b_cx=x1, b_cy=y1, arc=arc)
    # the trailing dots split into both rows
    xd, yd = pos[-1]
    for x1, y1 in (up_pos[-1], low_pos[-1]):
        typmath.draw(fr, DOTS, xd + (x1 - xd) * su, yd + (y1 - yd) * su, SZ, None, a)
    # the rows name themselves
    for t0, y, x, e, col in (
        (COS_T, LOW_Y, low_end, f"= cos {X}", "ink"),
        (SIN_T, UP_Y, up_end, f"= {I} sin {X}", "ink"),
    ):
        na = a * smooth(lin(t, t0, t0 + 0.4))
        if na > 0.003:
            w = typmath.size_of(e, SZ)[0]
            typmath.draw(fr, e, x + 24 + w / 2, y, SZ, None, na, glow=0.3 * pulse(t, t0 + 0.2, 0.8))
            fr.line(ROWS_X0, y + 52, x - 10, y + 52, "error" if y == UP_Y else "line", 1.4, 0.6 * na)


# --- 49C: one picture

CC, CR = (500.0, 470.0), 170.0
OM = 2 * math.pi / 3.2


def theta(t):
    return OM * max(0.0, t - CIRCLE_T)


def draw_circle(fr, t):
    a = smooth(lin(t, CIRCLE_T, CIRCLE_T + 0.6)) * (1 - smooth(lin(t, S50 - 0.4, S50 + 0.2)))
    if a <= 0.003:
        return
    cx, cy = CC
    fr.line(cx - CR - 50, cy, cx + CR + 50, cy, "axis", 1.4, a)
    fr.line(cx, cy - CR - 50, cx, cy + CR + 50, "axis", 1.4, a)
    fr.circle(cx, cy, CR * ease_out(lin(t, CIRCLE_T, CIRCLE_T + 0.8)), "circle", 2.6, a, glow=0.5)
    typmath.draw(fr, I, cx + 22, cy - CR - 26, 32, None, a * 0.8)
    th = theta(t)
    px, py = cx + CR * math.cos(th), cy - CR * math.sin(th)
    # the sine runs right, the cosine runs down: each a shadow of the point
    taus = np.linspace(0.0, min(3.2, max(0.0, t - CIRCLE_T)), 160)
    sx = cx + CR + 90 + taus * 300
    sy = cy - CR * np.sin(th - OM * taus)
    fr.poly(sx, sy, "original", 2.6, a, glow=0.15)
    dx = cx + CR * np.cos(th - OM * taus)
    dy = cy + CR + 90 + taus * 85
    fr.poly(dx, dy, "original", 2.6, a, glow=0.15)
    fr.dashed([px, sx[0]], [py, sy[0]], "muted", 1.2, 0.6 * a)
    fr.dashed([px, dx[0]], [py, dy[0]], "muted", 1.2, 0.6 * a)
    fr.line(cx, cy, px, py, "error", 2.4, a, glow=0.3)
    fr.glow_dot(px, py, 9, "error", a, 1.2)
    fr.glow_dot(sx[0], sy[0], 5, "ink", a, 0.8)
    fr.glow_dot(dx[0], dy[0], 5, "ink", a, 0.8)
    euler = f"e^({I} {X}) = cos {X} + {I} sin {X}"
    ea = a * 0.65
    typmath.draw(fr, euler, 960, 215.0, SZ, None, ea, glow=0.2)
    fr.light_sweep(ch8.outline(euler, 960, 215.0, SZ), lin(t, b(2170), b(2170) + 1.0), 0.7 * a)


# ------------------------------------------------------------------ S50 · one term at a time

SPAN, PANEL_H = 8.0, 4.6
D_FRONT = SPAN * FOCAL / 1500.0
SIN_VIEW = (-4.2, 4.2, -1.7, 1.7)
SIN_LABELS = [X, f"- {X}^3/{tc('fact', '6')}", f"+ {X}^5/{tc('fact', '120')}", f"- {X}^7/{tc('fact', '5040')}"]
STACK = TermStack(terms_of("sin", 7), view=SIN_VIEW, span=SPAN, gap=3.0, height=PANEL_H, labels=SIN_LABELS)
_PH = PANEL_H * FOCAL / D_FRONT
SINE = TaylorStage("sin", view=SIN_VIEW, rect=(210.0, 540 - _PH / 2, 1500.0, _PH), samples=600)
TURN = (b(2177), b(2178) + 0.4)  # "simplest pieces": the camera turns to the front, the pieces slide together
CLICK = b(2179)  # "one term at a time": the last piece clicks in


def stack_cam(t):
    u = ease_io(lin(t, *TURN))
    return orbit((0.0, 0.0, 0.0), 12.5 + (D_FRONT - 12.5) * u, 0.3 * (1 - u), -0.66 * (1 - u), focal=FOCAL)


def draw_stack(fr, t):
    a = smooth(lin(t, S50 - 0.2, S50 + 0.5)) * (1 - smooth(lin(t, S51 + 0.1, S51 + 0.8)))
    if a <= 0.003:
        return
    cam = stack_cam(t)
    merge = ease_io(lin(t, TURN[0] + 0.2, TURN[1]))
    appear = [ease_out(lin(t, S50 + 0.18 * i, S50 + 0.18 * i + 0.45)) for i in range(3)]
    appear.append(smooth(lin(t, CLICK - 0.6, CLICK)))
    flat = smooth(lin(t, TURN[1] - 0.1, TURN[1] + 0.3))  # hand over to the flat stage once the camera is square on
    if flat < 1:
        STACK.draw(fr, cam, merge=merge, alpha=a * (1 - flat), show_sum=0.0, appear=appear, label_size=46)
    if flat > 0.003:
        SINE.original(fr, a * flat, width=2.4)
        c3, c4 = T.coeffs("sin", 5), T.coeffs("sin", 7)
        u = spring(t, CLICK)
        c = T.blend(c3, c4, u)
        SINE.copy(fr, c, a * flat, glow=0.6 + 0.6 * pulse(t, CLICK + 0.15, 0.6))
        fr.glint(*SINE.ax.at(0.0, 0.0), 70, a * pulse(t, CLICK + 0.1, 0.7))
    ta = a * smooth(lin(t, b(2180), b(2180) + 0.5))
    if ta > 0.003:
        fr.text("Taylor series", 960, 200, SERIF, 64, 600, "ink", ta)
        fr.light_sweep(text_path("Taylor series", 960, 200, SERIF, 64, 600), lin(t, b(2181), b(2181) + 1.1), 0.8 * ta)


# ------------------------------------------------------------------ S51 · end screen

LOOP = 10.0
BG = TaylorStage("sin", view=(-10.0, 10.0, -1.7, 1.7), rect=(0.0, 300.0, 1920.0, 520.0), samples=700)
CLIMB = list(range(1, 19, 2))
SLOTS = [(160.0, 330.0, 740.0, 416.0), (1020.0, 330.0, 740.0, 416.0)]
SUB = (960.0, 900.0, 92.0)


def draw_end(fr, t):
    a = smooth(lin(t, S51, S51 + 0.8))
    if a <= 0.003:
        return
    ph = (t - S51) % LOOP
    times = [0.6 + 0.9 * k for k in range(len(CLIMB) - 1)]
    c, _, sp = BG.chain(ph, CLIMB, times)
    reset = 1 - smooth(lin(ph, LOOP - 0.8, LOOP - 0.1))
    bg = 0.15 * a * reset * smooth(lin(ph, 0.0, 0.4))
    BG.original(fr, 0.15 * a, width=2.0)
    BG.copy(fr, c, bg, glow=0.5 + 0.4 * sp)
    for x, y, w, h in SLOTS:
        fr.rrect(x, y, w, h, 18, fill="stage_raised", stroke="frame", width=1.0, alpha=0.4 * a, fill_alpha=0.85 * a)
    cx, cy, r = SUB
    fr.circle(cx, cy, r, "circle", 1.6, a * (0.55 + 0.25 * math.sin(2 * math.pi * (t - S51) / 2.4)), glow=0.6)
    fr.text("Taylor series", 960, 200, SERIF, 52, 600, "ink", 0.8 * a)


# ------------------------------------------------------------------ assembly


def draw_handoff(fr, t):
    a = 1 - smooth(lin(t, START, START + 0.8))
    if a > 0.003:
        with layer_alpha(fr, a):
            ch8.draw_formula(fr, t)
            ch8.draw_plot(fr, t)


def draw_one(t, size):
    fr = Frame(size)
    draw_handoff(fr, t)
    if t < S49 + 0.7:
        draw_arc(fr, t)
    if S49 - 0.2 <= t < S50 + 0.3:
        draw_series(fr, t)
        draw_circle(fr, t)
    if S50 - 0.3 <= t < S51 + 1.0:
        draw_stack(fr, t)
    if t >= S51:
        draw_end(fr, t)
    hud.eyebrow(fr, t, "09 · RECAP", START + 0.2)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch9:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=END - START, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(END - START)
        if audio:
            scene.add_audio(AUDIO, start=0, trim_start=START)
    return scene


SCENES = {
    "S47": (S47, S48, [749.0, 753.0, 761.9, 770.9]),
    "S48": (S48, S49, [778.2, 781.5, 783.4, 789.5]),
    "S49": (S49, S50, [797.8, 800.6, 801.6, 804.9, 806.2, 809.6]),
    "S50": (S50, S51, [812.4, 814.2, 816.7]),
    "S51": (S51, END, [820.0, 835.0]),
}
OFFSET = START
DURATION = END - START
STILLS = [s for _, _, st in SCENES.values() for s in st]
