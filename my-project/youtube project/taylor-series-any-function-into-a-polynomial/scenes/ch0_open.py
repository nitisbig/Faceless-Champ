"""CHAPTER 0 · COLD OPEN: THE CALCULATOR'S SECRET, 00:00.000 – 01:20.840 (cue #218 "Start").

S01  The calculator's secret   frame 0 is a gold copy mid-wrap on a sine wave inside the display -> fast pull back
                               to the chip -> display frosts -> push into the die, the core rises, pads draw on ->
                               + − × ÷ fire on their words -> "That's it" -> display clears, types sin(0.5)
S02  No circle inside          x-ray scan finds a pink circle ghost, then a triangle, both struck out -> pads go dark ->
                               the real × × + × + × program flickers -> 0.4794 lands digit by digit in lime
S03  How does it know waves?   + and × glow -> an ink sine wave unrolls out of the display -> the camera rises, the chip
                               slides away, the wave settles on the dot floor -> light sweep, a gold glimmer (the copy)
S04–S06 arrive in Stage C; until then the chapter holds the settled wave.

Clean frame: no captions, no cards, no labels. The chip, the curve and the digits carry the scene.
One FunctionSource on the narration clock; beats land 0.15 s before their word cue (cues.beat).
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
from components.fx import feather, glow_path
from components.stack25d import TermStack, terms_of
from components.stage import Axes, TaylorStage, clip, curve_path
from cues import AUDIO, beat, cue
from theme import SERIF, THEME, TITLE_WEIGHT, H, W

from faceless_champ.draw import Frame, back, ease_in, ease_io, ease_out, lin, motion_blur, smooth, text_path
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc
from faceless_champ.draw.space import orbit

START = 0.0
END = cue(218)  # 80.84 "Start with what a computer finds easy."

b = beat

B = {
    "pullback": b(2),  # "calculator"
    "secret": b(5),
    "deep": b(6),
    "few": b(13),
    "things": b(15),
    "add": b(16),
    "subtract": b(17),
    "multiply": b(18),
    "divide": b(19),
    "thats_it": b(20),
    "ask": b(27),
    "sine": b(31),
    "half": b(33),
    "circle": b(38),
    "hidden": b(42),
    "triangle": b(44),
    "measured": b(46),
    "and_yet": b(48),
    "blink": b(52),
    "answers": b(54),
    "add2": b(63),
    "multiply2": b(65),
    "waves": b(69),
    "answer": b(70),
    "beautiful": b(77),
    "tricks": b(78),
}
# "zero point four seven nine four": onsets measured from a 10 ms envelope of audio.mp3 (the SRT collapses them)
DIGITS = [(22.98, 1), (23.21, 2), (23.42, 3), (23.62, 4), (23.90, 5), (24.08, 6)]
ANSWER = "0.4794"
TRUE = f"{math.sin(0.5):.6f}"

S02, S03, S04, S05, S06 = cue(34), cue(56), cue(83), cue(136), cue(208)  # 14.84, 24.56, 33.44, 52.32, 76.84

# ------------------------------------------------------------------ world: the chip and its camera

CHIP = Chip(cx=960.0, cy=560.0, size=420.0)
DX, DY, DW, DH = CHIP.display_rect()
D = (DX + DW / 2, DY + DH / 2)  # display centre
C = CHIP.core_center()
M0 = (CHIP.cx, CHIP.cy)
UP = (960.0, 505.0)

# (time, zoom, focus x, focus y): the world point at focus sits at frame centre, scaled by zoom
KEYS = [
    (0.00, 11.0, *D),  # the display fills the frame; the copy peels off at both edges
    (B["pullback"], 10.4, *D),
    (1.30, 1.15, *M0),
    (B["deep"], 1.22, *M0),
    (3.50, 2.60, *C),
    (9.40, 2.85, *C),
    (10.20, 2.50, *C),
    (B["ask"] - 0.1, 2.45, *C),
    (12.90, 4.40, *D),
    (14.69, 4.70, *D),
    (15.50, 1.25, *M0),
    (19.20, 1.32, *M0),
    (21.90, 3.40, *D),
    (24.40, 4.00, *D),
    (25.70, 1.70, *UP),
    (B["answer"], 1.80, *UP),
    (30.30, 0.95, 1500.0, 180.0),
]


def camera(t):
    """(zoom, fx, fy): eased segments between keys, zoom interpolated in log space."""
    if t <= KEYS[0][0]:
        return KEYS[0][1:]
    for (t0, z0, x0, y0), (t1, z1, x1, y1) in pairwise(KEYS):
        if t <= t1:
            u = ease_io(lin(t, t0, t1))
            return math.exp(math.log(z0) + (math.log(z1) - math.log(z0)) * u), x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    return KEYS[-1][1:]


def matrix(z, fx, fy):
    m = skia.Matrix()
    m.setTranslate(-fx, -fy)
    m.postScale(z, z)
    m.postTranslate(W / 2, H / 2)
    return m


def to_screen(cam, x, y):
    z, fx, fy = cam
    return W / 2 + (x - fx) * z, H / 2 + (y - fy) * z


class world:
    """Draw inside a camera matrix on both the crisp and the glow canvas."""

    def __init__(self, fr, m):
        self.fr, self.m = fr, m

    def __enter__(self):
        for c in (self.fr.c, self.fr.g):
            c.save()
            c.concat(self.m)

    def __exit__(self, *exc):
        self.fr.c.restore()
        self.fr.g.restore()


def zoom_speed(t, dt=1 / 60):
    return abs(math.log(camera(t + dt)[0]) - math.log(camera(t - dt)[0])) / (2 * dt)


# ------------------------------------------------------------------ display content (screen space, crisp at any zoom)

SINE = TaylorStage("sin", view=(-7.0, 7.0, -1.55, 1.55), samples=700)
WRAP = [(-0.25, 9, 11), (0.15, 11, 13), (0.55, 13, 15), (0.95, 15, 17)]  # (t0, n_from, n_to): a term every 0.4 s


def display_axes(cam):
    x0, y0 = to_screen(cam, DX, DY)
    z = cam[0]
    return Axes(SINE.ax.x0, SINE.ax.x1, SINE.ax.y0, SINE.ax.y1, (x0, y0, DW * z, DH * z))


def wrap_copy(t):
    """Coefficients of the climbing copy at time t (mid-spring on frame 0)."""
    from components.motion import spring

    for t0, n0, n1 in reversed(WRAP):
        if t >= t0:
            return T.blend(T.coeffs("sin", n0), T.coeffs("sin", n1), spring(t, t0)), t0, n1
    return T.coeffs("sin", 9), WRAP[0][0], 11


def draw_display_wave(fr, t, cam, alpha):
    """The secret: the gold copy wrapping the ink wave, inside the display window."""
    if alpha <= 0.003:
        return
    ax = display_axes(cam)
    frost = smooth(lin(t, B["secret"], B["secret"] + 0.6))
    c, t0, _ = wrap_copy(t)
    with clip(fr, ax.rect):
        fr.line(ax.left, float(ax.py(0)), ax.right, float(ax.py(0)), "axis", 1.6, alpha * 0.8)
        sigma = 9.0 * frost
        if sigma > 0.2:
            with fr.blurred(sigma):
                _wave(fr, ax, c, t, t0, alpha * (1 - 0.55 * frost), glow=0.0)
        else:
            _wave(fr, ax, c, t, t0, alpha, glow=0.6)


def _wave(fr, ax, c, t, t0, alpha, glow):
    SINE.error_band(fr, c, alpha * 0.8, ax=ax)
    SINE.original(fr, alpha, ax=ax)
    p = SINE.copy(fr, c, alpha, ax=ax, glow=glow)
    if glow and p is not None:
        stroke = skia.Path()
        skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=30).getFillPath(p, stroke)
        fr.light_sweep(stroke, lin(t, t0 + 0.25, t0 + 0.95), 0.5 * alpha)


# ------------------------------------------------------------------ S01 / S02 chip state

PROG = T.ops(T.coeffs("sin", 5), 0.5)


def fire(t, at, hold=0.35, tau=0.35):
    """Pad glow after its word: a flash that settles to a soft hold."""
    if t < at:
        return 0.0
    return hold + (1 - hold) * math.exp(-(t - at) / tau)


def pad_state(t):
    active, rings = {}, []
    dark = smooth(lin(t, B["and_yet"], B["and_yet"] + 0.35))
    for op, key in (("+", "add"), ("−", "subtract"), ("×", "multiply"), ("÷", "divide")):
        a = fire(t, B[key]) * (1 - dark)
        a += 0.65 * math.exp(-max(0.0, t - B["thats_it"]) / 0.4) * (t >= B["thats_it"]) * (1 - dark)
        active[op] = min(1.0, a)
        rings.append((op, lin(t, B[key], B[key] + 0.6)))
    # the blink: the real Horner program, 0.1 s per op
    k = math.floor((t - B["blink"]) / 0.1)
    if 0 <= k < len(PROG):
        op = PROG[k]["op"]
        active[op] = 1.0
        rings.append((op, lin(t, B["blink"] + 0.1 * k, B["blink"] + 0.1 * k + 0.45)))
    # S03: only + and × answer "add and multiply"
    for op, key in (("+", "add2"), ("×", "multiply2")):
        if t >= B[key]:
            active[op] = max(active.get(op, 0.0), fire(t, B[key], 0.45))
            rings.append((op, lin(t, B[key], B[key] + 0.6)))
    return active, rings


def draw_chip(fr, t, cam):
    leave = smooth(lin(t, 29.9, 30.6))
    a = 1.0 - leave
    if a <= 0.003:
        return
    z, fx, fy = cam
    push = smooth(lin(t, B["deep"], 3.5)) * (1 - smooth(lin(t, 9.4, 10.2)))
    with world(fr, matrix(z * (1 + 0.16 * push), fx, fy)):  # pins slide past faster: parallax
        CHIP.pins(fr, a)
    active, rings = pad_state(t)
    dim = smooth(lin(t, B["thats_it"], B["thats_it"] + 0.6)) * (1 - smooth(lin(t, 14.7, 15.4)))
    dim = max(dim, 0.5 * smooth(lin(t, B["and_yet"], B["and_yet"] + 0.4)) * (1 - smooth(lin(t, 24.6, 25.4))))
    xray = smooth(lin(t, 15.0, 15.5)) * (1 - smooth(lin(t, 19.0, 19.4)))
    with world(fr, matrix(z, fx, fy)):
        CHIP.body(
            fr,
            t,
            a,
            active=active,
            pulses=1.0 - smooth(lin(z, 3.0, 4.5)),
            core_alpha=1.0 - 0.6 * xray,
            dim=dim,
            core_rise=ease_out(lin(t, B["deep"], B["deep"] + 1.1)),
            pad_reveal=ease_io(lin(t, B["few"], B["things"] + 0.3)),
            pad_fill=1.0 - 0.7 * smooth(lin(t, B["and_yet"], B["and_yet"] + 0.35)) * (1 - smooth(lin(t, 25.6, 26.0))),
        )
        for op, u in rings:
            CHIP.pulse_ring(fr, op, u, a)
        core_ring(fr, lin(t, B["thats_it"], B["thats_it"] + 0.8), a)
        draw_xray(fr, t)


def core_ring(fr, u, alpha):
    """ "That's it": one light ring leaves the whole core."""
    if not 0 < u < 1:
        return
    x, y, w = CHIP.core()
    g = w * (0.08 + 0.35 * ease_out(u))
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - g, y - g, w + 2 * g, w + 2 * g), 14, 14))
    fr.path_stroke(p, "light", 1.6, alpha * 0.8 * (1 - u) ** 1.6, glow=0.6)


# ------------------------------------------------------------------ S02 x-ray (world space, inside the die)

TRI_A = (C[0] - 96.0, C[1] + 62.0)
TRI_L = 190.0


def strike(fr, t, at, x0, y0, x1, y1, alpha):
    u = ease_out(lin(t, at, at + 0.25))
    if u > 0:
        fr.line(x0, y0, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, "muted", 2.0, alpha)


def draw_xray(fr, t):
    if not S02 - 0.2 <= t <= 19.8:
        return
    s = CHIP.size
    u = lin(t, 14.95, 19.3)
    if 0 < u < 1:
        y = CHIP.y0 + s * u
        body = skia.Path()
        body.addRect(skia.Rect.MakeXYWH(CHIP.x0, CHIP.y0, s, s))
        with clip(fr, path=body):
            for k in range(14):
                fr.line(CHIP.x0, y - 3 * k, CHIP.x0 + s, y - 3 * k, "light", 3.0, 0.07 * (1 - k / 14))
            fr.line(CHIP.x0, y, CHIP.x0 + s, y, "light", 1.4, 0.75, glow=0.6)
    # the circle that is not there
    ca = smooth(lin(t, B["circle"], B["circle"] + 0.5)) * (1 - smooth(lin(t, B["hidden"] + 0.25, B["hidden"] + 0.7)))
    if ca > 0.003:
        r = 112.0
        sweep = ease_out(lin(t, B["circle"], B["circle"] + 0.6))
        p = skia.Path()
        p.addArc(skia.Rect.MakeXYWH(C[0] - r, C[1] - r, 2 * r, 2 * r), -90, 360 * sweep)
        fr.path_stroke(p, "circle", 2.2, ca * 0.85, glow=0.35)
        fr.circle(*C, 3.5, "circle", alpha=ca, fill=True)
        strike(fr, t, B["hidden"], C[0] - r * 0.8, C[1] + r * 0.8, C[0] + r * 0.8, C[1] - r * 0.8, ca)
    # the triangle that is not measured
    ta = smooth(lin(t, B["triangle"], B["triangle"] + 0.4)) * (1 - smooth(lin(t, 19.0, 19.45)))
    if ta > 0.003:
        ax, ay = TRI_A
        bx, by = ax + TRI_L * math.cos(0.5), ay - TRI_L * math.sin(0.5)
        cx = bx
        draw_u = ease_out(lin(t, B["triangle"], B["triangle"] + 0.55))
        tri = skia.Path()
        tri.moveTo(ax, ay)
        tri.lineTo(cx, ay)
        tri.lineTo(bx, by)
        tri.close()
        m = skia.PathMeasure(tri, False)
        seg = skia.Path()
        m.getSegment(0, m.getLength() * draw_u, seg, True)
        fr.path_stroke(seg, "circle", 2.2, ta * 0.85, glow=0.35)
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeXYWH(ax - 44, ay - 44, 88, 88), 0, -math.degrees(0.5) * draw_u)
        fr.path_stroke(arc, "circle", 1.6, ta * 0.8)
        q = 14.0  # right-angle mark
        fr.poly([cx - q, cx - q, cx], [ay, ay - q, ay - q], "circle", 1.2, ta * 0.6 * draw_u)
        # ruler ticks crawl along the base
        n = int(10 * ease_io(lin(t, B["measured"], B["measured"] + 0.7)))
        for i in range(n):
            x = ax + (cx - ax) * (i + 1) / 11
            fr.line(x, ay, x, ay + (10 if i % 5 == 4 else 6), "light", 1.2, ta * 0.8)
        strike(fr, t, 18.95, ax - 10, ay + 20, bx + 10, by - 20, ta)


# ------------------------------------------------------------------ the display's text: sin(0.5), the program, 0.4794

QUESTION = f"sin({tc('x', '0.5')})"


def draw_display_text(fr, t, cam):
    if t < B["ask"] or t > 29.9:
        return
    z = cam[0]
    x0, y0 = to_screen(cam, DX, DY)
    w, h = DW * z, DH * z
    pad = h * 0.28
    size = h * 0.46
    clear_old = smooth(lin(t, B["blink"] - 0.05, B["blink"]))
    # sin(0.5) and its caret
    qa = 1.0 - clear_old
    if qa > 0.003:
        reveal = lin(t, B["sine"], B["half"] + 0.25)
        typmath.draw(fr, QUESTION, x0 + pad, y0 + h / 2, size, None, qa, reveal=reveal, align="left")
        qw = typmath.size_of(QUESTION, size)[0] * reveal
        if (t * 1.7) % 1.0 < 0.55 and t < S02 + 4.4:
            fr.rrect(
                x0 + pad + qw + size * 0.12, y0 + h * 0.24, max(2.0, size * 0.06), h * 0.52, 1, fill="x", alpha=qa * 0.9
            )
    # the blink: each step's value flashes through the window
    k = math.floor((t - B["blink"]) / 0.1)
    if 0 <= k < len(PROG):
        v = f"{PROG[k]['value']:.6f}".replace("-", "−")
        lock(fr, v, "", x0 + w - pad, y0 + h * 0.68, size * 0.9, 0.8, align="right", base="ink")
    # the answer, digit by digit as it is spoken
    n = sum(1 for at, _ in DIGITS if t >= at - 0.08)
    if n:
        last = max(at for at, _ in DIGITS if t >= at - 0.08)
        fade = 1.0 - smooth(lin(t, B["waves"] - 0.3, B["waves"] + 0.05))
        lock(
            fr,
            ANSWER[:n],
            TRUE,
            x0 + w - pad,
            y0 + h * 0.7,
            size * 1.05,
            fade,
            align="right",
            glint=lin(t, last - 0.08, last + 0.3),
        )
        rect = skia.Path()
        rect.addRect(skia.Rect.MakeXYWH(x0, y0, w, h))
        fr.light_sweep(rect, lin(t, 24.15, 24.95), 0.45)


def draw_answer_ghost(fr, t, cam):
    """During the answer's hold, the gold wave shows faintly behind the digits: the secret, hinted."""
    a = 0.22 * smooth(lin(t, 23.4, 24.3)) * (1 - smooth(lin(t, 25.0, 25.6)))
    if a <= 0.003:
        return
    ax = display_axes(cam)
    with clip(fr, ax.rect), fr.blurred(1.5):
        SINE.copy(fr, T.coeffs("sin", 17), a, ax=ax, glow=0.0, width=3.0)


# ------------------------------------------------------------------ S03: the wave leaves the display

STAGE = TaylorStage("sin", view=(-7.2, 7.2, -1.7, 1.7), rect=(96, 200, 1728, 680), pi_ticks=True)
PUSHED = Axes(-6.6, 6.6, -1.56, 1.56, STAGE.ax.rect)


def unroll_axes():
    cam = camera(B["waves"])
    cx, cy = to_screen(cam, DX + 0.1 * DW, D[1])
    span = 52.5  # px per unit: one period ≈ 330 px
    hh = 70.0
    return Axes(0.0, (W - cx) / span, -hh / 40.0, hh / 40.0, (cx, cy - hh, W - cx, 2 * hh))


UNROLL = unroll_axes()


def wave_axes(t):
    u = ease_io(lin(t, B["answer"], B["answer"] + 1.35))
    ax = UNROLL.lerp(STAGE.ax, u)
    return ax.lerp(PUSHED, ease_io(lin(t, B["answer"] + 1.35, b(88)))) if u >= 1 else ax


def draw_wave(fr, t):
    if not B["waves"] <= t < S04:
        return
    ax = wave_axes(t)
    floor = smooth(lin(t, B["answer"] + 0.5, B["answer"] + 1.3))
    if floor > 0.003:
        STAGE.static(fr, floor, ax=ax, labels=False)
    reveal = ease_out(lin(t, B["waves"], B["waves"] + 0.9))
    hi = ax.x0 + (ax.x1 - ax.x0) * reveal if ax.x0 >= -1e-9 else ax.x1
    lo = ax.x0
    xs = np.linspace(lo, max(lo + 1e-3, hi), 700)
    path = curve_path(ax, xs, np.sin(xs))
    with clip(fr, ax.rect):
        fr.path_stroke(path, "original", 2.5, 1.0, glow=0.15)
        if reveal < 1:
            px, py = ax.at(hi, math.sin(hi))
            fr.glow_dot(px, py, 4.0, "light", 0.9, 1.0)
    stroke = skia.Path()
    skia.Paint(Style=skia.Paint.kStroke_Style, StrokeWidth=10).getFillPath(path, stroke)
    fr.light_sweep(stroke, lin(t, B["beautiful"], B["beautiful"] + 0.9), 0.6, width=0.1)
    # the copy, hinted: a gold glimmer travels the wave
    g = lin(t, B["tricks"], B["tricks"] + 0.6)
    if 0 < g < 1:
        c = ax.x0 + (ax.x1 - ax.x0) * g
        env_g = math.sin(math.pi * g)
        seg = STAGE.copy_path(T.coeffs("sin", 17), ax, max(ax.x0, c - 1.1), min(ax.x1, c + 1.1))
        with clip(fr, ax.rect):
            fr.path_stroke(seg, "copy", 4.0, 0.75 * env_g, glow=0.9)


# ------------------------------------------------------------------ shared helpers for S04–S06


class shift:
    """Translate everything drawn inside by (dx, dy) design px, blurred horizontally while whipping."""

    def __init__(self, fr, dx, blur=0.0):
        self.fr, self.dx, self.blur = fr, dx, blur

    def __enter__(self):
        fr = self.fr
        if self.blur > 0.3:
            s = self.blur * fr.k
            fr.c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(s, 0.01)))
        else:
            fr.c.save()
        fr.g.save()
        fr.c.translate(self.dx, 0)
        fr.g.translate(self.dx, 0)

    def __exit__(self, *exc):
        self.fr.c.restore()
        self.fr.g.restore()


def curve3d(fr, cam, xs, ys, z, color, width, alpha, glow=0.0, ylim=(-1e9, 1e9), sx=1.0, sy=1.0, oy=0.0):
    """A math curve in the plane z of a 3D world, drawn in runs that stay inside ``ylim``."""
    if alpha <= 0.003:
        return
    ys = np.asarray(ys, float)
    inside = (ys >= ylim[0]) & (ys <= ylim[1])
    P = np.column_stack([np.asarray(xs) * sx, (np.clip(ys, *ylim) - oy) * sy, np.full(len(xs), z)])
    px, py, _ = cam.project(P)
    start = None
    for i, ok in enumerate(np.r_[inside, False]):
        if ok and start is None:
            start = i
        elif not ok and start is not None:
            if i - start > 1:
                fr.poly(px[start:i], py[start:i], color, width, alpha, glow)
            start = None


def cam_lerp(keys, t):
    """Orbit keys (time, dist, elev, azim): eased segments, distance in log space."""
    if t <= keys[0][0]:
        k = keys[0]
    elif t >= keys[-1][0]:
        k = keys[-1]
    else:
        for a, b2 in pairwise(keys):
            if t <= b2[0]:
                u = ease_io(lin(t, a[0], b2[0]))
                d = math.exp(math.log(a[1]) + (math.log(b2[1]) - math.log(a[1])) * u)
                k = (t, d, a[2] + (b2[2] - a[2]) * u, a[3] + (b2[3] - a[3]) * u)
                break
    return k[1:]


# ------------------------------------------------------------------ S04: rebuilt from simple pieces

FOCAL = 1100.0
SPAN, PANEL_H = 8.0, 4.6
D_FRONT = SPAN * FOCAL / 1500.0  # the merged panel is 1500 px wide in the front view
EXP_VIEW = (-2.6, 2.6, -1.0, 8.0)
X_ = tc("x", "x")
EXP_LABELS = ["1", X_, f"{X_}^2 / {tc('fact', '2')}", f"{X_}^3 / {tc('fact', '6')}"]
STACK = TermStack(terms_of("exp", 3), view=EXP_VIEW, span=SPAN, gap=3.4, height=PANEL_H, labels=EXP_LABELS)
_PW, _PH = 1500.0, PANEL_H * FOCAL / D_FRONT
EXP = TaylorStage("exp", view=EXP_VIEW, rect=(960 - _PW / 2, 540 - _PH / 2, _PW, _PH), samples=600)

STRIP_SINE = Axes(-6.6, 6.6, -1.3, 1.3, (260.0, 190.0, 1400.0, 170.0))
STRIP_EXP = Axes(-3.0, 2.2, -0.4, 9.5, (260.0, 455.0, 1400.0, 170.0))
STRIP_DECAY = Axes(-1.5, 9.0, -0.1, 2.2, (260.0, 720.0, 1400.0, 170.0))

STACK_KEYS = [
    (b(100) + 0.6, D_FRONT, 0.0, 0.0),
    (b(109) - 0.1, 11.5, 0.31, -0.61),  # yaw 35°, pitch 18°
    (b(117) - 0.1, 11.0, 0.29, -0.68),
    (b(122) + 0.2, D_FRONT, 0.0, 0.0),
]
STACK_END = STACK_KEYS[-1][0]
EXP_HUG = ([3, 4, 6, 8], [b(129), b(129) + 0.45, b(129) + 0.9])


def stack_cam(t):
    d, e, a = cam_lerp(STACK_KEYS, t)
    return orbit((0.0, 0.0, 0.0), d, e, a, focal=FOCAL, center=(960.0, 540.0))


def strip(fr, ax, f, alpha, reveal=1.0, blur=0.0, width=2.5):
    if alpha <= 0.003 or reveal <= 0:
        return
    xs = np.linspace(ax.x0, ax.x0 + (ax.x1 - ax.x0) * min(1.0, reveal), 500)
    path = curve_path(ax, xs, f(xs))
    with clip(fr, (ax.left - 4, ax.top - 30, ax.rect[2] + 8, ax.rect[3] + 60)):
        if blur > 0.3:
            with fr.blurred(blur):
                fr.path_stroke(path, "original", width, alpha)
        else:
            fr.path_stroke(path, "original", width, alpha, glow=0.15)
            if reveal < 1:
                fr.glow_dot(*ax.at(xs[-1], float(f(xs[-1:])[0])), 4.0, "light", alpha, 1.0)


def draw_s04(fr, t):
    if not S04 <= t < b(136) + 0.45:
        return
    # 04A · three smooth curves fan in as floating strips
    if t < STACK_END:
        back = smooth(lin(t, b(100), b(100) + 0.6))
        gone = smooth(lin(t, b(100) + 0.6, b(109) - 0.6))
        u = ease_io(lin(t, b(88), b(91)))
        sine_ax = wave_axes(t).lerp(STRIP_SINE, u)
        STAGE.static(fr, 1.0 - smooth(lin(t, S04, b(88) + 0.4)), ax=sine_ax, labels=False)
        a_side = (1 - 0.7 * back) * (1 - gone)
        shrink = lambda ax: ax.lerp(Axes(ax.x0, ax.x1, ax.y0, ax.y1, _scaled(ax.rect, 0.86)), back)
        strip(fr, shrink(sine_ax), np.sin, a_side, blur=7 * back)
        strip(
            fr,
            shrink(STRIP_DECAY),
            lambda x: np.exp(-x / 2),
            a_side,
            ease_out(lin(t, b(96), b(96) + 0.8)),
            blur=7 * back,
        )
        # the growth curve centres, then hands over to the 3D world
        to_front = ease_io(lin(t, b(100), b(100) + 0.6))
        ea = 1.0 - smooth(lin(t, b(100) + 0.55, b(100) + 0.65))
        strip(fr, STRIP_EXP.lerp(EXP.ax, to_front), np.exp, ea, ease_out(lin(t, b(93), b(93) + 0.8)))
    # 04B–04C · the pieces in depth, then stacked
    if b(100) + 0.6 <= t < STACK_END + 0.05:
        cam = stack_cam(t)
        appear = [ease_out(lin(t, b(k), b(k) + 0.5)) for k in (109, 111, 114, 116)]
        merge = lin(t, b(117), b(122) + 0.1)
        target = 1.0 - 0.75 * smooth(lin(t, b(109) - 0.8, b(109))) + 0.25 * smooth(lin(t, b(117), b(122)))
        xs = np.linspace(EXP_VIEW[0], EXP_VIEW[1], 400)
        curve3d(
            fr,
            cam,
            xs,
            np.exp(xs),
            0.0,
            "original",
            2.5,
            target,
            ylim=EXP_VIEW[2:],
            sx=STACK.sx,
            sy=STACK.sy,
            oy=(EXP_VIEW[2] + EXP_VIEW[3]) / 2,
        )
        STACK.draw(fr, cam, merge=merge, appear=appear, label_size=40)
    # 04C–04D · the copy hugs the original (2D from here: identical to the front view)
    if t >= STACK_END:
        ax = EXP.ax
        frame_a = 1.0 - smooth(lin(t, STACK_END, STACK_END + 0.7))
        fr.rrect(*ax.rect, 0, fill="stage_raised", stroke="frame", width=1.0, alpha=frame_a * 0.8, fill_alpha=0.82)
        orig = 0.5 + 0.5 * smooth(lin(t, b(125), b(125) + 0.4))
        c, r, s = EXP.chain(t, *EXP_HUG)
        band = smooth(lin(t, b(125), b(125) + 0.5)) * (1 - smooth(lin(t, b(135), b(135) + 0.6)))
        EXP.error_band(fr, c, band)
        EXP.original(fr, orig)
        p = EXP.copy(fr, c, 1.0, glow=0.6 + 0.5 * s)
        off = ease_out(lin(t, b(135), b(135) + 0.6)) * 4.0
        if t >= b(129) - 0.3:
            EXP.brackets(fr, r + off, smooth(lin(t, b(129) - 0.3, b(129))), label=False)
        if p is not None:
            fr.light_sweep(glow_path(p, 12), lin(t, b(135), b(135) + 0.9), 0.6, width=0.1)


def _scaled(rect, k):
    x, y, w, h = rect
    return (x + w * (1 - k) / 2, y + h * (1 - k) / 2, w * k, h * k)


# ------------------------------------------------------------------ S05: the promise, five vignettes

WHIPS = [(b(136), 0), (b(151), 1), (b(165), 2), (b(178), 3)]  # (time, from vignette): whip to the next one
WHIP = 0.42

V1 = TaylorStage("sin", view=(-6.5, 6.5, -1.6, 1.6), rect=(0, 180, 1920, 720), samples=700)
V1_HUG = (list(range(1, 17, 2)), [b(145) + 0.3 * k for k in range(7)])


def draw_v1(fr, t):
    """Wrap: the gold copy climbs along the ink sine wave; the camera tracks the growing tip."""
    c, r, s = V1.chain(t, *V1_HUG)
    cx = 0.55 * r
    ax = Axes(cx - 6.5, cx + 6.5, -1.6, 1.6, V1.ax.rect)
    V1.static(fr, 1.0, ax=ax, labels=False)
    V1.error_band(fr, c, 0.8, ax=ax)
    V1.original(fr, 1.0, ax=ax)
    V1.copy(fr, c, 1.0, ax=ax, glow=0.6 + 0.5 * s, reveal=ease_out(lin(t, b(143), b(143) + 0.6)), sym=True)
    if t >= b(145) - 0.2:
        V1.brackets(fr, r, 1.0, ax=ax, label=False)


Q = tc("muted", "square.stroked")
SERIES_GAPS = f"1 + {X_} + {X_}^2/{Q} + {X_}^3/{Q} + {X_}^4/{Q} + dots.c"
SERIES_FULL = f"1 + {X_} + {X_}^2/{tc('fact', '2!')} + {X_}^3/{tc('fact', '3!')} + {X_}^4/{tc('fact', '4!')} + dots.c"
SLOTS = [i for i, g in enumerate(typmath.glyphs(SERIES_GAPS)[0]) if g.color.lower() == "#7c8597"]
FACTS = ["2!", "3!", "4!"]
SERIES_SIZE = 92.0


def draw_v2(fr, t):
    """Factorials: empty denominators, then 2!, 3!, 4! drop in and pop into their slots."""
    push = 1.0 + 0.05 * ease_io(lin(t, b(151), b(165)))
    size = SERIES_SIZE * push
    centers = typmath.glyph_centers(SERIES_GAPS, 960, 600, size)
    landed = [b(161) + 0.15 * k + 0.35 for k in range(3)]
    final = smooth(lin(t, landed[-1] + 0.1, landed[-1] + 0.4))
    alphas = {}
    for k, gi in enumerate(SLOTS):
        alphas[gi] = 1.0 - smooth(lin(t, landed[k] - 0.1, landed[k]))
    if final < 1:
        typmath.draw(
            fr, SERIES_GAPS, 960, 600, size, None, 1 - final, reveal=lin(t, b(151) + 0.2, b(151) + 0.9), alphas=alphas
        )
    if final > 0:
        typmath.draw(fr, SERIES_FULL, 960, 600, size, None, final)
    for k, (gi, s) in enumerate(zip(SLOTS, FACTS)):
        drop = back(lin(t, b(158) + 0.1 * k, b(158) + 0.1 * k + 0.55)) if t >= b(158) + 0.1 * k else 0.0
        if drop <= 0 or final >= 1:
            continue
        sx, sy = centers[gi]
        hx, hy = sx, 330.0
        fly = ease_io(lin(t, landed[k] - 0.35, landed[k]))
        x = hx + (sx - hx) * fly
        y = (-80 + (hy + 80) * drop) * (1 - fly) + sy * fly - 60 * math.sin(math.pi * fly)
        typmath.draw(fr, tc("fact", s), x, y, size * (0.82 + 0.18 * fly), None, (1 - final), glow=0.35)
        g = lin(t, landed[k], landed[k] + 0.35)
        if 0 < g < 1:
            fr.glint(sx, sy, 70, 1 - g, "fact")


LINE_X0, LINE_UNIT, LINE_Y = 330.0, 420.0, 560.0
E_SUMS = T.e_sums(4)
SEG_T = [b(172) + 0.36 * k for k in range(5)]


def draw_v3(fr, t):
    """e by hand: segments 1, 1, ½, ⅙, 1/24 stack along a number line toward a lime e."""
    z = 1.0 + 0.12 * ease_io(lin(t, b(165), b(178)))
    ex = LINE_X0 + math.e * LINE_UNIT
    X = lambda v: ex + (LINE_X0 + v * LINE_UNIT - ex) * z
    span = ease_io(lin(t, b(165) + 0.2, b(170)))
    # the line draws itself in behind a travelling spark, then cools to a quiet axis
    tip = -0.15 + 3.35 * span
    cool = smooth(lin(t, b(170), b(172)))
    fr.line(X(-0.15), LINE_Y, X(tip), LINE_Y, "light", 2.6, 0.75 - 0.4 * cool, glow=0.5 * (1 - cool))
    if 0 < span < 1:
        fr.glow_dot(X(tip), LINE_Y, 5.0, "light", math.sin(math.pi * span) ** 0.5, 1.0)
    for v in range(4):
        tick = ease_out(lin(tip, v, v + 0.35))  # each tick rises as the spark passes it
        fr.line(X(v), LINE_Y - 12 * tick, X(v), LINE_Y + 12 * tick, "light", 2.2, tick * (0.8 - 0.35 * cool))
        fr.text(str(v), X(v), LINE_Y + 56 + 8 * (1 - tick), "display", 34, 500, "light", tick * (0.75 - 0.35 * cool))
    ea = smooth(lin(t, b(170), b(170) + 0.5))
    if ea > 0:
        fr.line(ex, LINE_Y - 70, ex, LINE_Y + 20, "result", 2.4, ea, glow=0.6)
        typmath.draw(fr, tc("result", "e"), ex, LINE_Y - 110, 64, None, ea, glow=0.4)
    prev, shown = 0.0, None
    for k, t0 in enumerate(SEG_T):
        u = ease_out(lin(t, t0, t0 + 0.4))
        if u <= 0:
            break
        end = prev + (E_SUMS[k] - prev) * u
        fr.line(X(prev) + 2, LINE_Y - 22, X(end) - 2, LINE_Y - 22, "copy", 7.0, 1.0, glow=0.6)
        fr.line(X(prev), LINE_Y - 34, X(prev), LINE_Y - 10, "copy", 1.6, 0.7)
        if u > 0.6:
            shown = (k, t0)
        prev = E_SUMS[k]
    if shown:
        k, t0 = shown
        s = f"{E_SUMS[k]:.4f}".rstrip("0").rstrip(".") if k < 3 else f"{E_SUMS[k]:.4f}"
        lock(fr, s, f"{math.e:.5f}", 960, 820, 84, 1.0, glint=lin(t, t0 + 0.25, t0 + 0.6))


HILL_VIEW = (-2.4, 2.4, -0.6, 1.6)
HILL_D = 4.8 * FOCAL / 1500.0
HILL_KEYS = [
    (b(178), HILL_D * 1.12, 0.06, -0.14),
    (b(197) - 0.1, HILL_D, 0.0, 0.0),
    (b(201), HILL_D * 1.55, 0.78, 0.18),
    (b(205), HILL_D * 1.55, 0.80, 0.24),
    (b(208) - 0.05, HILL_D, 0.0, 0.0),
]
HILL_HUG = ([2, 8, 16, 26], [b(186), b(193), b(193) + 0.16])


def hill_cam(t):
    d, e, a = cam_lerp(HILL_KEYS, t)
    return orbit((0.0, 0.5, 0.0), d, e, a, focal=FOCAL, center=(960.0, 560.0))


def draw_v4(fr, t):
    """The trick fails, then the camera tilts under the graph to glimpse the complex plane."""
    cam = hill_cam(t)
    tilt = smooth(lin(t, b(197) - 0.1, b(201)))
    # the complex plane lies on the floor (the real axis): faint, only seen from above
    if tilt > 0.01:
        for v in np.arange(-2.5, 2.51, 0.5):
            major = abs(v - round(v)) < 1e-6
            tok, a = ("plane_major", 0.5) if major else ("plane_minor", 0.9)
            curve3d(fr, cam, np.array([v, v]), np.array([0.0, 0.0]), 0.0, tok, 1.0, a * tilt)
            P = np.array([[-2.5, 0.0, v], [2.5, 0.0, v]])
            px, py, _ = cam.project(P)
            fr.line(px[0], py[0], px[1], py[1], tok, 1.0, a * tilt)
        P = np.array([[0.0, 0.0, z] for z in np.linspace(-2.5, 2.5, 2)])
        px, py, _ = cam.project(P)
        fr.line(px[0], py[0], px[1], py[1], "error", 1.6, 0.7 * tilt)
        pulse = 0.35 + 0.65 * math.sin(math.pi * min(1.0, lin(t, b(202), b(204) + 0.6))) ** 2
        for zi in (1.0, -1.0):
            gx, gy, _ = cam.project(np.array([[0.0, 0.0, zi]]))
            fr.glow_dot(float(gx[0]), float(gy[0]), 7.0, "error", tilt * pulse, 0.9)
    xs = np.linspace(HILL_VIEW[0], HILL_VIEW[1], 600)
    curve3d(fr, cam, xs, np.zeros_like(xs), 0.0, "axis", 2.0, 1.0 - 0.3 * tilt)
    curve3d(fr, cam, xs, 1 / (1 + xs * xs), 0.0, "original", 2.5, 1.0, glow=0.15)
    c, _, s = HILL.chain(t, *HILL_HUG)
    reach = 0.9 + 1.5 * ease_in(lin(t, b(193), b(193) + 0.35))
    xc = np.linspace(-reach, reach, 600)
    grow = ease_out(lin(t, b(178) + 0.3, b(178) + 1.0))
    xc = xc * grow
    curve3d(fr, cam, xc, T.evaluate(c, xc), 0.0, "copy", 4.0, 1.0, glow=0.6 + 0.5 * s, ylim=(-6.0, 6.0))


HILL = TaylorStage("hill", view=HILL_VIEW)


VIGNETTES = [None, draw_v1, draw_v2, draw_v3, draw_v4]  # 0 = S04's eˣ stage


def draw_s05(fr, t):
    if not b(136) <= t < b(208) + 0.4:
        return
    # which vignette, and is a whip running?
    for tw, k in reversed(WHIPS):
        if t >= tw:
            u = lin(t, tw, tw + WHIP)
            break
    else:
        return
    e = ease_io(u)
    speed = math.sin(math.pi * u)
    leave = smooth(lin(t, b(208) - 0.2, b(208) + 0.3))
    for idx, dx in ((k, -e * W), (k + 1, (1 - e) * W)):
        if abs(dx) >= W or (idx == k and u >= 1):
            continue
        fn = VIGNETTES[idx]
        with shift(fr, dx, 60 * speed):
            if fn is None:
                draw_s04(fr, min(t, b(136) + 0.4))
            else:
                if leave < 1:
                    if leave > 0:
                        fr.c.saveLayerAlpha(None, int(255 * (1 - leave)))
                    fn(fr, t)
                    if leave > 0:
                        fr.c.restore()


# ------------------------------------------------------------------ S06: title card

PANEL = (160.0, 430.0, 1600.0, 440.0)  # open field, no frame: the edges feather into the dark
TITLE = "Taylor series"
CARD = TaylorStage("sin", view=(-11.0, 11.0, -1.6, 1.6), rect=PANEL, samples=900)
CARD_HUG = (list(range(5, 23, 2)), [b(208) + 0.2 + 0.4 * k for k in range(8)])


def draw_s06(fr, t):
    if t < b(208) - 0.2:
        return
    a = smooth(lin(t, b(208) - 0.2, b(208) + 0.3))
    # the push dives into the origin: sine flattens to its tangent line, then to a single point
    push = ease_in(lin(t, b(216), END - 0.1))
    dot = smooth(lin(t, END - 0.75, END - 0.1))
    k = 1.0 + 1.6 * push
    m = skia.Matrix()
    m.setTranslate(-960, -650)
    m.postScale(k, k)
    m.postTranslate(960, 650 - 120 * push)
    with world(fr, m):
        ta = a * smooth(lin(t, b(211), b(211) + 0.5)) * (1 - smooth(lin(t, b(216), b(216) + 0.5)))
        rise = 16 * (1 - ease_out(lin(t, b(211), b(211) + 0.6)))
        fr.text(TITLE, 960, 330 + rise, SERIF, 112, TITLE_WEIGHT, "ink", ta)
        fr.light_sweep(
            text_path(TITLE, 960, 330 + rise, SERIF, 112, TITLE_WEIGHT), lin(t, b(211) + 0.3, b(211) + 1.2), 0.8
        )
    z = 1.0 / (1.0 + 60.0 * push**2)
    ax = Axes(-11.0 * z, 11.0 * z, -1.6 * z, 1.6 * z, PANEL)
    c, _, s = CARD.chain(t, *CARD_HUG)
    ca = a * (1 - dot)
    with feather(fr, PANEL):
        CARD.original(fr, ca, ax=ax)
        CARD.copy(fr, c, ca, ax=ax, glow=0.6 + 0.5 * s)
    if dot > 0:
        fr.glow_dot(*ax.at(0.0, 0.0), 4.0 + 5.0 * dot, "x", dot, 1.0)
    fr.zoom_blur(0.08 * math.sin(math.pi * push))


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    cam = camera(t)
    draw_chip(fr, t, cam)
    show_wave = 1.0 - smooth(lin(t, B["ask"] - 0.2, B["ask"] + 0.4))
    draw_display_wave(fr, t, cam, show_wave)
    draw_answer_ghost(fr, t, cam)
    draw_display_text(fr, t, cam)
    draw_wave(fr, t)
    if t < b(136):
        draw_s04(fr, t)
    draw_s05(fr, t)
    draw_s06(fr, t)
    fr.zoom_blur(min(0.2, 0.07 * max(0.0, zoom_speed(t) - 1.0)))
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def blur_weight(t):
    """Motion blur (finals only) on the pull-back, the push into the die and the S05 whip-pans."""
    whip = any(tw <= t <= tw + WHIP for tw, _ in WHIPS)
    return max(smooth(lin(t, 0.1, 0.3)) * (1 - smooth(lin(t, 1.2, 1.4))), 0.6 * (B["deep"] <= t <= 3.5), 1.0 * whip)


def draw(t, size):
    t = t + START
    return motion_blur(draw_one, t, size, weight=blur_weight(t))


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch0:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=END - START, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(END - START)
        if audio:
            scene.add_audio(AUDIO, start=0, trim_start=START)
    return scene


SCENES = {
    "S01": (0.0, S02, [0.2, 1.8, 4.9, 7.9, 10.0, 14.2]),
    "S02": (S02, S03, [15.9, 18.0, 20.8, 23.8]),
    "S03": (S03, S04, [26.4, 28.9, 31.2]),
    "S04": (S04, S05, [37.5, 40.8, 44.5, 48.0, 51.5]),
    "S05": (S05, S06, [52.4, 55.8, 60.9, 66.5, 72.7, 75.2]),
    "S06": (S06, END, [78.6, 80.4]),
}
OFFSET = START
DURATION = END - START
STILLS = [s for _, _, st in SCENES.values() for s in st]
