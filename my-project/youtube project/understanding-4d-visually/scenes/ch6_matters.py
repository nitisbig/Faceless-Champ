"""CHAPTER 6 - WHY IT MATTERS (S26-S27), 07:13.760 - 07:45.680.

S26  The math is everywhere    the tesseract shrinks into a glass box (our space) with the dashed w arrow outside it;
                               three glass cards swing into an arc: physics (the Cheetah Block with the cheetah's
                               blue world-line, (t, x, y, z)), quaternions (a PyVista probe turning by slerp,
                               q = (w, x, y, z) live), word vectors (a 4,096-number vector, its length, a real PCA
                               of synthetic clusters down to 3D, and the 3x4 plaque from S18 beside it)
S27  Your eyes stop at three   x, y, z glow; a wall after z; linear algebra breaks through: w, then x5 ... xn
                               stream upward into perspective
"""

from __future__ import annotations

import itertools
import math
from pathlib import Path

import numpy as np
import skia
import typmath
from components import cards, hud
from components import tesseract as T4
from components.cheetah_block import CheetahBlock, track
from components.matrix_plaque import draw_matrix
from components.vector_slot import Slot, bracket, draw_vector
from cues import AUDIO, cue
from fx import Frame, back, chroma_kick, ease_in, ease_io, ease_out, env, lerp, lin, motion_blur, pulse, smooth
from pv3d import render as pvr
from pv3d import solids
from space import orbit, text3d
from theme import THEME, H, W

from scenes import ch5_rotation as ch5

START = cue(1233)  # 433.76 "So is any of this real?"
END = cue(1323)  # 465.68 "Let's recap."

C = {i: cue(i) for i in range(1233, 1324)}
T = {
    "real": C[1238],
    "step": C[1242],
    "fourth": C[1245],
    "space": C[1248],
    "everywhere": C[1253],
    "physics": C[1254],  # ASR: "This"
    "time": C[1256],
    "coordinate": C[1260],
    "spacetime": C[1262],
    "game": C[1264],
    "spacecraft": C[1267],
    "quaternions": C[1269],
    "four": C[1272],
    "parts": C[1273],
    "rotate": C[1275],
    "smoothly": C[1277],
    "and": C[1278],  # ASR: "An"
    "model": C[1281],
    "word": C[1287],
    "vector": C[1290],
    "thousands": C[1292],
    "dimensions": C[1294],
    "measured": C[1295],
    "projected": C[1297],
    "same": C[1300],
    "tesseract": C[1305],
    "s27": C[1308],
    "eyes": C[1314],
    "stop": C[1315],
    "three": C[1317],
    "linear": C[1319],
    "algebra": C[1320],
    "not": C[1322],
}
FOCAL = 1500.0
CW, CH = 700.0, 600.0  # card size, design px

# ------------------------------------------------------------------ S26A: is any of this real?


def shrink(t):
    return ease_io(lin(t, T["real"] - 0.3, T["real"] + 0.6))


def cam26(t):
    u = shrink(t)
    return orbit(
        (0, 0, 0),
        10.0,
        lerp(0.28, 0.34, u),
        -0.5 + 0.03 * (t - ch5.T["watch"]),
        focal=FOCAL,
        center=(lerp(900.0, 960.0, u), lerp(470.0, 520.0, u)),
    )


def world26(t, scale):
    p3, _ = T4.project_persp(T4.C @ ch5.R_at(t).T, ch5.D4)
    return T4.place(p3, scale=scale)


BOX = 1.5
BOX_EDGES = [(i, j) for i in range(8) for j in range(i + 1, 8) if (i ^ j).bit_count() == 1]
BOX_PTS = np.array([[x, y, z] for x in (-BOX, BOX) for y in (-BOX, BOX) for z in (-BOX, BOX)])


def draw_s26a(fr, t):
    if t > T["everywhere"] + 0.7:
        return
    handoff = smooth(lin(t, START, START + 0.5))
    if handoff < 1:  # chapter 5's last frame (plaque, trails, the centre star) dims away under the live rig
        ch5.draw_s24(fr, t)
        fr.dim(handoff)
    out = smooth(lin(t, T["everywhere"] - 0.2, T["everywhere"] + 0.5))
    a = handoff * (1 - out)
    if a <= 0.003:
        return
    cam = cam26(t)
    scale = lerp(1.25, 0.42, shrink(t)) * (1 - 0.6 * out)
    world = world26(t, scale)
    trails = 1 - shrink(t)
    if trails > 0.01:
        T4.draw_trails(
            fr,
            cam,
            lambda tt: world26(tt, scale),
            t,
            span=1.6,
            steps=36,
            alpha=0.5 * trails * a,
            width=1.4,
            color="ink",
        )
    small = shrink(t)
    _glass_box(fr, t, cam, a)
    T4.draw(fr, cam, world, a, width=lerp(2.6, 2.2, small), glow=lerp(0.8, 1.0, small), vertices=0.9)


def _glass_box(fr, t, cam, a):
    ba = smooth(lin(t, T["step"] - 0.35, T["step"] + 0.4)) * a
    if ba <= 0.003:
        return
    grow = ease_out(lin(t, T["step"] - 0.35, T["step"] + 0.5))
    pts = BOX_PTS * lerp(0.6, 1.0, grow)
    xs, ys, _ = cam.project(pts)
    faces = [(0, 1, 3, 2), (4, 5, 7, 6), (0, 1, 5, 4), (2, 3, 7, 6), (0, 2, 6, 4), (1, 3, 7, 5)]
    for f in faces:
        p = skia.Path()
        p.addPoly([skia.Point(float(xs[k]), float(ys[k])) for k in f], True)
        fr.path_fill(p, "w", 0.028 * ba)
    fr.light_sweep(T4.hull_path(xs, ys), lin(t, T["space"] - 0.3, T["space"] + 0.7), strength=0.16)
    for i, j in BOX_EDGES:
        fr.line(xs[i], ys[i], xs[j], ys[j], "ink", 1.6, 0.55 * ba, glow=0.3)
    bx, by, _ = cam.project(np.array([[0.0, -BOX * 1.05, -BOX]]))
    fr.text("our space", float(bx[0]), float(by[0]) + 56, "sans", 24, 600, "muted", ba, tracking=0.12)
    # the fourth direction: outside the box, dashed, out of reach
    wa = smooth(lin(t, T["fourth"] - 0.1, T["fourth"] + 0.4)) * a
    if wa > 0.003:
        u = ease_out(lin(t, T["fourth"] - 0.1, T["fourth"] + 0.6))
        p0 = np.array([BOX * 1.25, 0.2, BOX * 0.2])
        p1 = p0 + np.array([1.5, 1.3, 1.1]) * u
        flick = 0.75 + 0.25 * math.sin(9.0 * t)
        hud.arrow3d(fr, cam, p0, p1, "w", 2.6, wa * flick, glow=0.9, dashed=True)
        text3d(fr, cam, "w", p1 + np.array([0.25, 0.2, 0.1]), 0.5, "w", wa * smooth(lin(u, 0.6, 1.0)), 500, "italic")


# ------------------------------------------------------------------ S26 cards


def swing(t, i):
    return smooth(lin(t, T["everywhere"] - 0.15 + 0.16 * i, T["everywhere"] + 0.65 + 0.16 * i))


def focus(t):
    return cards.truck(t, [(START, 1.0), (T["physics"] - 0.45, 0.0), (T["game"] - 0.4, 1.0), (T["and"] - 0.2, 2.0)])


def arc_alpha(t):
    return env(t, T["everywhere"] - 0.3, T["s27"] + 0.9, 0.01, 0.8)


def arc_center(t):
    u = ease_io(lin(t, T["projected"] - 0.25, T["projected"] + 0.6))
    return (lerp(960.0, 660.0, u), 548.0)


# -- card 1: physics

BLOCK = CheetahBlock(center=(0.0, 0.0, 0.0), scale=0.85)
LINE_FRAMES = np.linspace(1.0, 126.0, 96)
WORLD_LINE = np.array([BLOCK.pixel(f, *track(f)) for f in LINE_FRAMES])


def card_physics(fr, t, a, active):
    cards.header(fr, 1, "PHYSICS", a)
    cam = orbit((0.0, 0.0, 0.0), 11.5, 0.30, 0.78, focal=1020, center=(300.0, 330.0))
    f = 1.0 + ((t - T["everywhere"] + 2.0) * 5.0) % 124.0
    u = ease_io(lin(t, T["time"] - 0.15, T["coordinate"] + 0.5))
    BLOCK.draw(
        fr,
        cam,
        t,
        unfold=1.0,
        hold=1,
        active=f,
        active_alpha=0.9 * a,
        volume=a * (1 - 0.45 * u),
        outline=0.35 * a,
        border=0.3,
    )
    BLOCK.draw_axes(fr, cam, alpha=0.8 * a, t_flare=0.45 * pulse(t, T["time"] - 0.05, 0.9))
    if u > 0:
        n = max(2, int(len(WORLD_LINE) * u))
        xs, ys, _ = cam.project(WORLD_LINE[:n])
        fr.poly(xs, ys, "bg", 7.0, 0.5 * a)
        fr.poly(xs, ys, "w", 3.2, a, glow=1.3)
        px, py, _ = cam.project(np.array([BLOCK.pixel(f, *track(f))]))
        fr.glow_dot(float(px[0]), float(py[0]), 5.0, "#ffffff", a * smooth(lin(u, 0.9, 1.0)), 1.3)
        g = pulse(t, T["spacetime"] - 0.05, 0.9)
        if g > 0:
            fr.glint(float(xs[-1]), float(ys[-1]), 22, g * a)
    tp = pulse(t, T["time"] - 0.05, 0.9) + pulse(t, T["coordinate"] - 0.05, 0.8)
    slots = [Slot("t", "w", glow=0.4 + tp, underline=1.0), Slot("x", "x"), Slot("y", "y"), Slot("z", "z")]
    va = smooth(lin(t, T["physics"] - 0.2, T["physics"] + 0.4)) * a
    draw_vector(fr, 600, 300, slots, 40, alpha=va, width=70)
    fr.text("world-line", 300, 548, "sans", 22, 600, "w", a * smooth(lin(u, 0.5, 1.0)), tracking=0.1)
    sp = smooth(lin(t, T["spacetime"] - 0.1, T["spacetime"] + 0.4)) * a
    fr.text("spacetime", 600, 470, "italic", 34, 500, "ink", sp, glow=0.3)
    sweep = skia.Path()
    sweep.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeWH(CW, CH), 22, 22))
    fr.light_sweep(sweep, lin(t, T["spacetime"] - 0.1, T["spacetime"] + 0.8), strength=0.18 * a)


# -- card 2: quaternions


def quat(axis, angle):
    v = np.asarray(axis, float)
    v = v / np.linalg.norm(v)
    return np.r_[math.cos(angle / 2), math.sin(angle / 2) * v]


def slerp(q0, q1, u):
    d = float(q0 @ q1)
    if d < 0:
        q1, d = -q1, -d
    if d > 0.9995:
        q = q0 + (q1 - q0) * u
        return q / np.linalg.norm(q)
    th = math.acos(d)
    return (math.sin((1 - u) * th) * q0 + math.sin(u * th) * q1) / math.sin(th)


def quat_R(q):
    w, x, y, z = q
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


Q_KEYS = [
    (T["everywhere"] - 1.0, quat([0.1, 1.0, 0.15], 0.5)),
    (T["spacecraft"], quat([0.25, 1.0, 0.2], 1.4)),
    (T["parts"], quat([1.0, 0.35, 0.25], 2.2)),
    (T["smoothly"] + 0.4, quat([0.2, 0.5, 1.0], 2.9)),
    (T["vector"], quat([0.6, 1.0, 0.3], 3.9)),
    (T["projected"] + 1.0, quat([1.0, 0.2, 0.6], 4.6)),
    (END + 1.0, quat([0.4, 1.0, 0.1], 5.4)),
]


def q_at(t):
    if t <= Q_KEYS[0][0]:
        return Q_KEYS[0][1]
    for (t0, q0), (t1, q1) in itertools.pairwise(Q_KEYS):
        if t <= t1:
            u = lin(t, t0, t1)
            return slerp(q0, q1, 0.5 * u + 0.5 * smooth(u))  # never stops between keys
    return Q_KEYS[-1][1]


VX, VY, VW, VH = 30.0, 84.0, 640.0, 360.0  # the probe's 16:9 viewport inside the card
PCAM = orbit((0.0, 0.0, 0.0), 5.6, 0.22, -0.55, focal=FOCAL)
HULL = pvr.GLOSS | {"color": "#8C97AB", "specular": 1.0, "specular_power": 70, "diffuse": 0.85, "ambient": 0.06}
STYLES = {
    "hull": HULL,
    "dark": pvr.GLOSS | {"color": "#2A3346"},
    "panel": pvr.GLOSS | {"color": "#173A66", "specular": 1.0, "specular_power": 40, "smooth_shading": False},
}


def _to_view(xs, ys):
    return VX + np.asarray(xs) * VW / W, VY + np.asarray(ys) * VH / H


def card_quat(fr, t, a, active):
    cards.header(fr, 2, "QUATERNIONS", a)
    fr.rrect(VX, VY, VW, VH, 14, stroke="line", width=1.0, alpha=0.8 * a)
    q = q_at(t)
    R = quat_R(q)
    size = (max(2, round(VW * fr.k)), max(2, round(VH * fr.k)))
    meshes = [(m, STYLES[kind]) for m, kind in solids.spacecraft(R)]
    rgba = pvr.render(meshes, PCAM, size, cache="ch6_probe")
    img = skia.Image.fromarray(
        np.ascontiguousarray(rgba), colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kUnpremul_AlphaType
    )
    fr.c.drawImageRect(img, skia.Rect.MakeXYWH(VX, VY, VW, VH), pvr.LINEAR, skia.Paint(AntiAlias=True, Alphaf=a))
    # the slerp arc: the nose's path over the last seconds, a great-circle trail
    ta = smooth(lin(t, T["rotate"] - 0.4, T["rotate"] + 0.3)) * a
    if ta > 0.003:
        hist = np.array([quat_R(q_at(t - 2.6 * k / 40)) @ np.array([1.25, 0.0, 0.0]) for k in range(41)])
        xs, ys, _ = PCAM.project(hist)
        xs, ys = _to_view(xs, ys)
        for k in range(40):
            fr.line(
                xs[k], ys[k], xs[k + 1], ys[k + 1], "w", 2.6 * (1 - 0.6 * k / 40), ta * (1 - k / 40) ** 1.3, glow=0.8
            )
        fr.glow_dot(float(xs[0]), float(ys[0]), 5.0, "#ffffff", ta, 1.2)
    la = smooth(lin(t, T["quaternions"] - 0.15, T["quaternions"] + 0.5)) * a
    if la > 0.003:
        expr = f"q = ({typmath.tc('w', 'w')}, {typmath.tc('x', 'x')}, {typmath.tc('y', 'y')}, {typmath.tc('z', 'z')})"
        typmath.draw(fr, expr, 350, 492, 40, alpha=la, reveal=lin(t, T["quaternions"] - 0.15, T["quaternions"] + 0.6))
        for k, (name, val) in enumerate(zip("wxyz", q)):
            x = 350 + (k - 1.5) * 118
            p = pulse(t, T["four"] - 0.05 + 0.09 * k, 0.6) + pulse(t, T["parts"] + 0.1, 0.6)
            fr.rrect(
                x - 50,
                528,
                100,
                44,
                12,
                fill=name,
                fill_alpha=(0.06 + 0.12 * p) * la,
                stroke=name,
                width=1.2,
                alpha=(0.5 + 0.5 * p) * la,
                glow=0.6 * p,
            )
            typmath.number(fr, f"{val:+.2f}", x, 550, 24, name, la, glow=0.5 * p)


# -- card 3: word vectors

_rng = np.random.default_rng(4)
DIM, PER, K = 4096, 30, 6
CENTERS = _rng.normal(0, 0.2, (K, DIM))
LABELS = np.repeat(np.arange(K), PER)
WORDS = CENTERS[LABELS] + _rng.normal(0, 1, (K * PER, DIM))
_X = WORDS - WORDS.mean(0)
_, _, _VT = np.linalg.svd(_X, full_matrices=False)
CLOUD = _X @ _VT[:3].T  # a real PCA: 4,096 numbers per word -> 3
CLOUD = CLOUD / np.abs(CLOUD).max()
VEC = WORDS[0]  # "cheetah"
NORM = float(np.linalg.norm(VEC))
TAGS = {0: "cheetah"}
ROWS = 12


def card_words(fr, t, a, active):
    cards.header(fr, 3, "WORD VECTORS", a)
    ca = smooth(lin(t, T["model"] - 0.1, T["model"] + 0.4)) * a
    if ca <= 0.003:
        return
    fr.rrect(
        150 - 82,
        540 - 24,
        164,
        48,
        12,
        fill="light",
        fill_alpha=0.08 * ca,
        stroke="light",
        width=1.4,
        alpha=ca,
        glow=0.3,
    )
    fr.text("cheetah", 150, 548, "sans", 24, 600, "light", ca)
    fly = lin(t, T["projected"] - 0.05, T["projected"] + 1.3)
    col_a = ca * (1 - smooth(lin(fly, 0.3, 0.9)))
    rise = lin(t, T["word"] - 0.15, T["vector"] + 0.4)
    shown = ROWS * ease_out(rise)
    for k in range(ROWS):
        ra = col_a * float(np.clip(shown - k, 0.0, 1.0)) * (1 - 0.04 * k)
        typmath.number(fr, f"{VEC[k]:+.2f}", 150, 488 - k * 30, 21 * (1 - 0.012 * k), "ink", ra)
    if shown > 1:
        top = 488 - (min(shown, ROWS) - 1) * 30 - 16
        bracket(fr, 150 - 52, top - 22, 506, -1, "ink", col_a * 0.8)
        bracket(fr, 150 + 52, top - 22, 506, 1, "ink", col_a * 0.8)
        typmath.draw(fr, "dots.v", 150, top - 34, 22, color="muted", alpha=col_a * smooth(lin(rise, 0.8, 1.0)))
    # thousands of dimensions
    na = smooth(lin(t, T["thousands"] - 0.15, T["thousands"] + 0.3)) * a
    if na > 0.003:
        n = round(4096 * ease_out(lin(t, T["thousands"] - 0.05, T["dimensions"] + 0.35)))
        fr.text("for example", 480, 112, "sans", 17, 600, "muted", na, tracking=0.12)
        hud.tabular(fr, f"{n:,}", 480, 178, 60, "ink", na, family="display", weight=600, glow=0.2)
        fr.text("dimensions", 480, 214, "sans", 21, 600, "muted", na, tracking=0.08)
    ma = smooth(lin(t, T["measured"] - 0.1, T["measured"] + 0.4)) * a
    if ma > 0.003:
        g = pulse(t, T["measured"], 0.8)
        typmath.draw(fr, "norm(bold(v)) =", 486, 276, 32, alpha=ma, align="right")
        typmath.number(fr, f"{NORM:.1f}", 498, 276, 32, "light", ma, glow=0.4 * g, align="left")
    _cloud(fr, t, a, fly)


def _cloud(fr, t, a, fly):
    if fly <= 0:
        return
    cam = orbit((0.0, 0.0, 0.0), 6.0, 0.35, 0.3 + 0.22 * (t - T["projected"]), focal=640, center=(480.0, 440.0))
    ax_a = smooth(lin(fly, 0.4, 0.9)) * a
    for v in np.eye(3) * 1.1:
        xs, ys, _ = cam.project(np.array([-v, v]))
        fr.line(xs[0], ys[0], xs[1], ys[1], "muted", 1.0, 0.35 * ax_a)
    xs, ys, z = cam.project(CLOUD[:, [0, 2, 1]])
    zn = (z - z.min()) / max(1e-6, z.max() - z.min())
    for i in np.argsort(-z):
        u = ease_io(lin(fly, 0.004 * (i % PER) + 0.02 * LABELS[i], 0.004 * (i % PER) + 0.02 * LABELS[i] + 0.55))
        if u <= 0:
            continue
        x0, y0 = 150.0, 488 - (i % ROWS) * 30
        x, y = lerp(x0, float(xs[i]), u), lerp(y0, float(ys[i]), u)
        hero = LABELS[i] == 0
        color = "light" if hero else ("ink" if LABELS[i] % 2 else "muted")
        fr.glow_dot(
            x,
            y,
            (4.0 if i == 0 else 2.4) * (1.2 - 0.4 * zn[i]),
            color,
            a * (1.0 - 0.5 * zn[i]),
            strength=0.9 if i == 0 else 0.25,
        )
    ta = smooth(lin(fly, 0.8, 1.0)) * a
    for i, word in TAGS.items():
        fr.text(
            word,
            float(xs[i]) + 10,
            float(ys[i]) - 8,
            "sans",
            17 if i else 19,
            600,
            "light" if i == 0 else "muted",
            ta,
            align="left",
        )
    typmath.draw(fr, "RR^(4096) -> RR^3", 480, 576, 24, color="muted", alpha=ta)


CARDS = [card_physics, card_quat, card_words]


def draw_cards(fr, t):
    a = arc_alpha(t)
    if a <= 0.003:
        return
    cards.draw_arc(
        fr,
        t,
        CARDS,
        focus(t),
        CW,
        CH,
        a,
        swing=[swing(t, i) for i in range(3)],
        center=arc_center(t),
        spacing=720.0,
        zoom=1.18,
    )
    _draw_plaque(fr, t, a)


def _draw_plaque(fr, t, a):
    """The 3x4 projection plaque from S18 slides in beside the word cloud: the same tool."""
    u = ease_out(lin(t, T["projected"] - 0.05, T["projected"] + 0.8))
    pa = smooth(lin(t, T["projected"] - 0.05, T["projected"] + 0.5)) * a
    if pa <= 0.003:
        return
    x = lerp(2100.0, 1450.0, u)
    g = pulse(t, T["same"] - 0.05, 1.0)
    cells = [["1", "0", "0", "0"], ["0", "1", "0", "0"], ["0", "0", "1", "0"]]
    colors = {(0, 0): "x", (1, 1): "y", (2, 2): "z", (0, 3): "w", (1, 3): "w", (2, 3): "w"}
    draw_matrix(
        fr,
        x,
        470,
        cells,
        colors,
        cell_w=78,
        cell_h=66,
        size=34,
        alpha=pa,
        glow={(0, 0): g, (1, 1): g, (2, 2): g},
        pad=24,
    )
    typmath.draw(fr, "RR^4 -> RR^3", x, 318, 34, color="muted", alpha=pa)
    ia = smooth(lin(t, T["tesseract"] - 0.15, T["tesseract"] + 0.35)) * pa
    if ia > 0.003:
        cam = orbit((0, 0, 0), 10.0, 0.3, -0.5 + 0.4 * (t - T["tesseract"]), focal=FOCAL, center=(x, 730.0))
        R = T4.rotation(("xw", 0.6 * (t - START)), ("zw", 0.4 * (t - START)))
        p3, _ = T4.project_persp(T4.C @ R.T, 3.0)
        pop = back(ease_out(lin(t, T["tesseract"] - 0.15, T["tesseract"] + 0.45)))
        T4.draw(fr, cam, T4.place(p3, scale=0.26 * pop), ia, width=1.8, glow=1.0)
        fr.chroma(chroma_kick(t, T["tesseract"], 3.0))


# ------------------------------------------------------------------ S27: your eyes stop at three

CAM27 = orbit((0.0, 0.3, 0.0), 10.0, 0.36, -0.62, focal=FOCAL, center=(600.0, 600.0))
AXES = [("x", np.array([2.6, 0, 0])), ("y", np.array([0, 0, 2.6])), ("z", np.array([0, 2.6, 0]))]
VEC_X, Y0, PITCH, SIZE = 1340.0, 470.0, 74.0, 54.0
COLUMN = ["x", "y", "z", "w", "x_5", "x_6", "x_7", "x_8", "x_9", "dots.v", "x_n"]
DEPTH = 0.8


def row_y(p):
    """Screen y and scale of row position p: flat for p >= -1, receding upward in perspective above."""
    if p >= -1:
        return Y0 + p * PITCH, 1.0
    k = -1 - p
    return Y0 - PITCH - PITCH * (1 - DEPTH**k) / (1 - DEPTH), DEPTH**k


def draw_s27(fr, t):
    a = env(t, T["s27"] + 0.2, END, 0.6, 0.45)
    if a <= 0.003:
        return
    lights = [T["eyes"], T["stop"], T["three"]]
    stream = lin(t, T["algebra"] - 0.15, END)
    for k, (name, vec) in enumerate(AXES):
        u = ease_out(lin(t, T["s27"] + 0.4 + 0.15 * k, T["s27"] + 1.2 + 0.15 * k))
        g = pulse(t, lights[k] - 0.05, 0.9)
        dimmed = 1 - 0.5 * smooth(lin(t, T["linear"], T["linear"] + 0.6))
        hud.axis3d(fr, CAM27, np.zeros(3), vec, name, name, u * a * dimmed)
        if g > 0:
            xs, ys, _ = CAM27.project(np.array([np.zeros(3), vec]))
            fr.line(xs[0], ys[0], xs[1], ys[1], name, 4.0, g * a, glow=1.6)
    _column(fr, t, a, stream)


def _column(fr, t, a, stream):
    ca = smooth(lin(t, T["s27"] + 0.5, T["s27"] + 1.1)) * a
    if ca <= 0.003:
        return
    s = 7.0 * ease_in(stream) ** 0.8 if stream > 0 else 0.0
    w_in = ease_out(lin(t, T["linear"] - 0.05, T["linear"] + 0.5))
    glow = 0.3 + 0.9 * smooth(lin(t, T["algebra"], T["algebra"] + 0.6))
    for i, tex in enumerate(COLUMN):
        if i >= 3 and t < T["linear"] - 0.05:
            continue
        p = i - 1 - s
        y, k = row_y(p)
        ia = ca * (w_in if i == 3 else 1.0)
        if i >= 4:
            ia *= smooth(lin(stream * 9.0, i - 4.0, i - 3.0)) if stream > 0 else 0.0
        ia *= min(1.0, k * 1.6)
        if ia <= 0.003 or y < -40:
            continue
        color = tex if tex in "xyzw" else "ink"
        typmath.term(fr, tex, VEC_X, y, SIZE * k, color, ia, glow=glow * k)
    ba = ca * (1 - smooth(lin(stream, 0.0, 0.25)))
    if ba > 0.003:
        top, bottom = row_y(-1)[0] - SIZE * 0.75, row_y(1 + w_in)[0] + SIZE * 0.75
        bracket(fr, VEC_X - 58, top, bottom, -1, "ink", ba)
        bracket(fr, VEC_X + 58, top, bottom, 1, "ink", ba)
    _wall(fr, t, ca)


def _wall(fr, t, a):
    wa = smooth(lin(t, T["three"] - 0.1, T["three"] + 0.4)) * a
    if wa <= 0.003:
        return
    y = Y0 + 1.5 * PITCH + 2
    br = lin(t, T["linear"] - 0.05, T["linear"] + 0.9)
    if br <= 0:
        fr.line(VEC_X - 110, y, VEC_X + 110, y, "ink", 2.4, 0.8 * wa, glow=0.5)
        for k in range(-5, 6):
            fr.line(VEC_X + k * 20, y, VEC_X + k * 20 - 10, y + 12, "ink", 1.2, 0.4 * wa)
        fr.text("3", VEC_X + 150, y + 9, "display", 28, 600, "muted", wa)
        return
    rng = np.random.default_rng(11)  # shards: the wall breaks outward as w pushes through
    for k in range(10):
        x0 = VEC_X - 110 + 22 * k
        vx, vy, spin = rng.uniform(-260, 260), rng.uniform(-60, 220), rng.uniform(-6, 6)
        u = ease_out(br)
        cx, cy = x0 + 11 + vx * u, y + vy * u + 180 * br * br
        ang = spin * br
        dx, dy = 11 * math.cos(ang), 11 * math.sin(ang)
        fr.line(cx - dx, cy - dy, cx + dx, cy + dy, "ink", 2.4, 0.8 * wa * (1 - br), glow=0.5)
    fr.chroma(chroma_kick(t, T["linear"], 5.0))


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_s26a(fr, t)
    draw_cards(fr, t)
    draw_s27(fr, t)
    hud.eyebrow(fr, t, "06 · WHY IT MATTERS", START + 0.24)
    fr.vignette(0.5)
    fr.grain(t, 0.045)
    return fr.finish()


def blur_weight(t):
    return max(env(t, T["everywhere"] - 0.2, T["everywhere"] + 1.2, 0.2, 0.3), env(t, T["algebra"], END, 0.3, 0.2))


def draw(t, size):
    t = t + START
    return motion_blur(draw_one, t, size, weight=blur_weight(t))


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
    434.0,
    435.9,
    437.3,
    438.6,
    440.6,
    442.4,
    443.9,
    446.6,
    448.9,
    452.0,
    453.6,
    455.2,
    456.6,
    457.6,
    459.6,
    461.2,
    462.9,
    464.5,
    465.3,
]
