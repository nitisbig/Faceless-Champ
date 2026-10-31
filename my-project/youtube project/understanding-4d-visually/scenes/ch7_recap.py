"""CHAPTER 7 - RECAP AND OUTRO (S28-S30 + end screen), 07:45.680 - 08:50.000.

S28  Everything we built       five glass cards on an arc, the camera trucks along them: numbers (the ant and its
                               chip), a fourth direction (w grows, the dashed arrow), the tesseract (fast build,
                               16 / 32 / diagonal 2), slices and shadows (octahedron, a cheetah frame, the 3x4
                               plaque), rotation in planes (six chips, a ZW spin)
S29  One frame at a time       the cards collapse; the cheetah footage returns letterboxed, tilts back into the
                               block, the blue slice plane sweeps, then steps at 5 fps with a tick each frame
S30  See you in the next dim.  the block folds into the tesseract; subscribe pill with a light sweep; the title
                               lockup; inside-out turn and a fly into the inner cube; end screen (two video slots,
                               subscribe circle, the tesseract at 15 %) on silence to cues.TOTAL
"""

from __future__ import annotations

import math
from pathlib import Path

import media
import numpy as np
import skia
import typmath
from components import cards, hud
from components import tesseract as T4
from components.cheetah_block import CheetahBlock, stutter_tick
from components.matrix_plaque import draw_matrix
from components.vector_slot import Slot, draw_vector
from cues import AUDIO, AUDIO_DURATION, TOTAL, cue
from fx import (
    Frame,
    back,
    chroma_kick,
    ease_in,
    ease_io,
    ease_out,
    env,
    lerp,
    lin,
    motion_blur,
    pulse,
    smooth,
    text_path,
)
from space import orbit
from theme import THEME, TOKENS, H, W

from scenes.ch1_dimension import draw_ant
from scenes.ch5_rotation import _chip

START = cue(1323)  # 465.68 "Let's recap."
END = TOTAL  # 530.0: narration ends at 510.0, then the end-screen hold
AUDIO_END = AUDIO_DURATION

C = {i: cue(i) for i in range(1323, 1440)}
T = {
    "independent": C[1331],
    "adding": C[1338],
    "number4": C[1341],
    "fourth_dir": C[1344],
    "dragging": C[1346],
    "tesseract": C[1353],
    "n16": C[1355],
    "n32": C[1357],
    "diagonal": C[1361],  # "long"
    "two": C[1365],
    "we_see": C[1366],
    "slices": C[1370],
    "frames": C[1372],
    "shadows": C[1378],
    "projection": C[1381],
    "and_rot": C[1383],
    "rotation": C[1384],
    "planes": C[1387],
    "six": C[1391],
    "s29": C[1395],
    "watch": C[1400],
    "video": C[1402],
    "sliding": C[1407],
    "higher": C[1410],
    "one": C[1412],
    "time": C[1416],
    "s30": C[1417],
    "less": C[1425],
    "subscribe": C[1427],
    "complex": C[1430],
    "visual": C[1433],
    "see": C[1434],
    "next": C[1438],
}
FOCAL = 1500.0
CW, CH = 700.0, 600.0

# ------------------------------------------------------------------ S28: five recap cards


def axes_in(fr, cam, a, length=2.2, names=("x", "y", "z")):
    vecs = {"x": [length, 0, 0], "y": [0, 0, length], "z": [0, length, 0]}
    for n in names:
        hud.axis3d(fr, cam, np.zeros(3), vecs[n], n, n, a, size=0.36)


def card_numbers(fr, t, a, active):
    cards.header(fr, 1, "NUMBERS", a)
    cam = orbit((0.8, 0.6, 0.8), 9.0, 0.42, -0.7, focal=900, center=(350.0, 300.0))
    hud.dot_grid(fr, cam, 0.0, extent=2.6, spacing=0.4, alpha=0.18 * a, center=(0.8, 0.8))
    axes_in(fr, cam, a)
    p = np.array([1.6, 1.4, 1.2])  # view coords of the math point (1.6, 1.2, 1.4)
    foot = np.array([1.6, 0.0, 1.2])
    for p0, p1 in ((p, foot), (foot, [1.6, 0, 0]), (foot, [0, 0, 1.2])):
        xs, ys, _ = cam.project(np.array([p0, p1], float))
        fr.dashed(xs, ys, "muted", 1.4, 0.7 * a, on=6, off=5)
    xs, ys, _ = cam.project(p[None])
    draw_ant(fr, float(xs[0]), float(ys[0]), 40, -0.5, t, a)
    flash = {k: pulse(t, T["independent"] - 0.05 + 0.3 * k, 0.6) for k in range(3)}
    hud.coord_chip(fr, 350, 505, ["1.6", "1.2", "1.4"], ["x", "y", "z"], a, size=34, flash=flash)
    fr.text("one number per direction", 350, 572, "sans", 20, 600, "muted", a, tracking=0.06)


def card_fourth(fr, t, a, active):
    cards.header(fr, 2, "A FOURTH DIRECTION", a)
    cam = orbit((0.6, 0.6, 0.6), 9.0, 0.38, -0.65, focal=900, center=(250.0, 330.0))
    axes_in(fr, cam, a)
    da = smooth(lin(t, T["fourth_dir"] - 0.2, T["fourth_dir"] + 0.4)) * a
    if da > 0.003:
        u = ease_out(lin(t, T["fourth_dir"] - 0.2, T["fourth_dir"] + 0.6))
        tip = np.array([-1.5, 1.9, -1.3]) * u
        flick = 0.75 + 0.25 * math.sin(9.0 * t)
        hud.arrow3d(fr, cam, np.zeros(3), tip, "w", 2.6, da * flick, glow=0.9, dashed=True)
        from space import text3d

        text3d(fr, cam, "w", tip * 1.12, 0.4, "w", da * smooth(lin(u, 0.6, 1.0)), 500, "italic")
    g = lin(t, T["adding"] - 0.1, T["number4"] + 0.2)
    pw = pulse(t, T["number4"] - 0.05, 0.7)
    slots = [Slot(k, k) for k in "xyz"]
    if g > 0:
        slots.append(Slot("w", "w", glow=0.4 + pw, underline=1.0))
    draw_vector(fr, 560, 310, slots, 46, alpha=a, width=74, grow=(3, g) if g > 0 else None)
    fr.text("one more number", 350, 572, "sans", 20, 600, "muted", a, tracking=0.06)


def build_extent(t):
    b0 = T["dragging"] - 0.25
    return np.array([ease_io(lin(t, b0 + 0.5 * k, b0 + 0.5 * k + 0.55)) for k in range(4)])


def card_tesseract(fr, t, a, active):
    cards.header(fr, 3, "THE TESSERACT", a)
    e = build_extent(t) if t > T["dragging"] - 0.4 else np.ones(4)
    R = T4.rotation(("xw", 0.35 * (t - START)), ("yz", 0.12 * (t - START)))
    p3, _ = T4.project_persp((T4.C * e) @ R.T, 3.0)
    world = T4.place(p3, scale=0.62)
    cam = orbit((0, 0, 0), 10.0, 0.3, -0.5, focal=1100, center=(350.0, 270.0))
    T4.draw(fr, cam, world, a, width=2.0, glow=0.6, vertices=0.8 * e[3])
    du = ease_io(lin(t, T["diagonal"] - 0.1, T["diagonal"] + 0.7))
    if du > 0:
        i0, i1 = T4.index_of("0000"), T4.index_of("1111")
        xs, ys, _ = cam.project(world[[i0, i1]])
        x1, y1 = lerp(xs[0], xs[1], du), lerp(ys[0], ys[1], du)
        g = pulse(t, T["two"] - 0.05, 0.9)
        fr.line(xs[0], ys[0], x1, y1, "#ffffff", 3.0 + 2 * g, a, glow=1.0 + g)
    for k, (label, value, at, x) in enumerate((("corners", "16", T["n16"], 205), ("edges", "32", T["n32"], 495))):
        ra = smooth(lin(t, at - 0.15, at + 0.25)) * a
        pop = pulse(t, at - 0.05, 0.5)
        hud.readout(fr, x, 492 - 6 * pop, label, value, "ink", ra, size=32)
    fa = smooth(lin(t, T["diagonal"], T["diagonal"] + 0.5)) * a
    if fa > 0.003:
        g = pulse(t, T["two"] - 0.05, 0.9)
        expr = "sqrt(1 + 1 + 1 + 1) = 2"
        n = len(typmath.glyphs(expr)[0])
        typmath.draw(
            fr,
            expr,
            350,
            562,
            34,
            alpha=fa,
            glows={n - 1: 1.4 * g},
            colors={n - 1: TOKENS["light"]} if t > T["two"] - 0.1 else None,
        )
        fr.chroma(chroma_kick(t, T["two"], 3.0))


def card_slices(fr, t, a, active):
    cards.header(fr, 4, "SLICES & SHADOWS", a)
    fr.line(350, 100, 350, 560, "ink", 1.0, 0.16 * a)
    fr.text("slices", 175, 122, "italic", 30, 500, "w", a)
    fr.text("shadows", 525, 122, "italic", 30, 500, "ink", a)
    pts, loops = T4.corner_slice(2.0)
    cam = orbit((0, 0, 0), 6.0, 0.35, 0.5 * (t - START), focal=760, center=(175.0, 262.0))
    sa = smooth(lin(t, T["slices"] - 0.15, T["slices"] + 0.35)) * a
    T4.draw_solid(fr, cam, pts * 0.95, loops, "w", sa, fill=0.14, width=2.0, glow=0.7)
    fa = smooth(lin(t, T["frames"] - 0.15, T["frames"] + 0.35)) * a
    if fa > 0.003:
        f = 30 + int((t - T["frames"]) * 5) % 60
        for k in (2, 1, 0):  # a short stack of frames: the top one is the slice
            x, y = 62 + 12 * k, 395 - 12 * k
            img = media.thumb(f - 2 * k)
            fr.image_quad(img, [(x, y), (x + 220, y), (x + 220, y + 124), (x, y + 124)], fa * (1 - 0.35 * k))
            fr.rrect(
                x,
                y,
                220,
                124,
                2,
                stroke="w" if k == 0 else "line",
                width=1.6 if k == 0 else 1.0,
                alpha=fa,
                glow=0.6 if k == 0 else 0.0,
            )
    ha = smooth(lin(t, T["shadows"] - 0.15, T["shadows"] + 0.35)) * a
    if ha > 0.003:
        R = T4.rotation(("xw", 0.4 * (t - START)), ("yw", 0.2 * (t - START)))
        p3 = T4.project_ortho(T4.C @ R.T)
        cam2 = orbit((0, 0, 0), 10.0, 0.3, -0.5, focal=760, center=(525.0, 255.0))
        world = T4.place(p3, scale=1.0)
        xs, ys, _ = cam2.project(world)
        fr.path_fill(T4.hull_path(xs, ys), "ink", 0.05 * ha)
        T4.draw(fr, cam2, world, ha * 0.8, width=1.6, glow=0.4)
    pa = smooth(lin(t, T["projection"] - 0.15, T["projection"] + 0.35)) * a
    if pa > 0.003:
        cells = [["1", "0", "0", "0"], ["0", "1", "0", "0"], ["0", "0", "1", "0"]]
        colors = {(0, 0): "x", (1, 1): "y", (2, 2): "z", (0, 3): "w", (1, 3): "w", (2, 3): "w"}
        g = pulse(t, T["projection"] + 0.3, 0.8)
        draw_matrix(
            fr,
            525,
            470,
            cells,
            colors,
            cell_w=50,
            cell_h=44,
            size=24,
            alpha=pa,
            pad=16,
            col_hi={3: ("w", g)} if g > 0 else None,
        )


PLANES = ("xy", "xz", "xw", "yz", "yw", "zw")


def card_rotation(fr, t, a, active):
    cards.header(fr, 5, "ROTATION IN PLANES", a)
    six = pulse(t, T["six"] - 0.05, 0.9)
    for k, plane in enumerate(PLANES):
        ca = smooth(lin(t, T["rotation"] - 0.1 + 0.11 * k, T["rotation"] + 0.25 + 0.11 * k)) * a
        x, y = 200 + 150 * (k % 3), 136 + 66 * (k // 3)
        glow = 0.5 * six + (0.7 if plane == "zw" else 0.0) * smooth(lin(t, T["planes"], T["planes"] + 0.4))
        _chip(fr, x, y, 112, 50, TOKENS[plane[0]], TOKENS[plane[1]], ca, label=plane, size=28, glow=glow)
    sa = smooth(lin(t, T["planes"] - 0.3, T["planes"] + 0.3)) * a
    if sa > 0.003:
        th = 1.1 * max(0.0, t - T["planes"] + 0.3)
        R = T4.rotation(("zw", th), ("xy", 0.15 * (t - START)))
        p3, _ = T4.project_persp(T4.C @ R.T, 3.0)
        cam = orbit((0, 0, 0), 10.0, 0.3, -0.5, focal=1000, center=(260.0, 400.0))
        T4.draw(fr, cam, T4.place(p3, scale=0.55), sa, width=2.0, glow=0.7)
    na = smooth(lin(t, T["six"] - 0.15, T["six"] + 0.25)) * a
    if na > 0.003:
        typmath.draw(fr, "6", 545, 400, 110 + 12 * six, color="ink", alpha=na, glow=0.4 + 1.2 * six)
        fr.text("ways to turn", 545, 492, "sans", 22, 600, "muted", na, tracking=0.08)
        fr.chroma(chroma_kick(t, T["six"], 4.0))


CARDS = [card_numbers, card_fourth, card_tesseract, card_slices, card_rotation]


def focus(t):
    stops = [
        (START, 0.0),
        (T["adding"] - 0.4, 1.0),
        (T["dragging"] - 0.45, 2.0),
        (T["we_see"] - 0.4, 3.0),
        (T["and_rot"] - 0.45, 4.0),
    ]
    return cards.truck(t, stops)


def collapse(t):
    return lin(t, T["s29"] - 0.05, T["s29"] + 0.75)


def draw_s28(fr, t):
    u = collapse(t)
    if u >= 1:
        return
    sw = [smooth(lin(t, START - 0.1 + 0.12 * i, START + 0.7 + 0.12 * i)) for i in range(5)]
    cards.draw_arc(
        fr, t, CARDS, focus(t), CW, CH, 1.0, swing=sw, spacing=720.0, zoom=1.18, collapse=u, center=(960.0, 548.0)
    )
    if 0 < u < 1:
        fr.zoom_blur(0.2 * math.sin(math.pi * u))


# ------------------------------------------------------------------ S29: one frame at a time

BLOCK = CheetahBlock(center=(0.0, 0.0, 0.0))
FULL = np.array([(0.0, 0.0), (W, 0.0), (W, H), (0.0, H)])


def clip_time(t):
    return 1.2 + max(0.0, t - (T["watch"] - 0.25))


HOLD = media.frame_at(clip_time(T["sliding"] - 0.15))
SWEEP_TO = 82.0


def tilt(t):
    return ease_io(lin(t, T["sliding"] - 0.15, T["sliding"] + 0.75))


def cam29(t):
    return orbit((0.0, -0.1, 0.0), 10.4, 0.26, -0.80 + 0.015 * (t - T["sliding"]), focal=FOCAL, center=(960.0, 500.0))


def active_frame(t):
    sweep = ease_io(lin(t, T["sliding"] + 0.8, T["one"] - 0.1))
    f = lerp(HOLD, SWEEP_TO, sweep)
    if t < T["one"]:
        return f
    return SWEEP_TO + int((min(t, T["time"] + 0.3) - T["one"]) * media.FRAME_FPS)


def draw_s29(fr, t):
    a = env(t, T["watch"] - 0.3, T["s30"] + 0.8, 0.3, 0.7)
    if a <= 0.003:
        return
    u = tilt(t)
    if u <= 0:
        c = clip_time(t)
        fr.image_fill(media.opener(int(c * media.OPENER_FPS) + 1), 1.0 + 0.012 * c, a)
    else:
        cam = cam29(t)
        unfold = smooth(lin(t, T["sliding"] + 0.4, T["higher"] + 0.6))
        f = active_frame(t)
        stepping = t >= T["one"]
        tick = stutter_tick(t - T["one"]) if stepping and t < T["time"] + 0.5 else 0.0
        BLOCK.draw(
            fr,
            cam,
            t,
            unfold=unfold,
            hold=HOLD,
            active=f if u >= 1 else HOLD,
            active_alpha=a if u >= 1 else 0.0,
            volume=a,
            slice_alpha=a * smooth(lin(u, 0.8, 1.0)) * (1 + tick),
            outline=0.5 * a * unfold,
        )
        if u < 1:
            xs, ys, _ = cam.project(BLOCK.sheet(BLOCK.z_of(HOLD)))
            quad = [tuple(lerp(FULL[k], np.array([xs[k], ys[k]]), u)) for k in range(4)]
            fr.image_quad(media.frame(HOLD), quad, a)
        if stepping:
            _ticks(fr, cam, t, a)
    lb = smooth(lin(t, T["watch"], T["video"] + 0.3)) * (1 - smooth(lin(t, T["sliding"] - 0.1, T["sliding"] + 0.6)))
    fr.letterbox(lb)


def _ticks(fr, cam, t, a):
    """A tick on the block's base for every 5 fps step; the newest one flashes."""
    n = int(active_frame(t) - SWEEP_TO)
    for k in range(n + 1):
        f = SWEEP_TO + k
        p = BLOCK.sheet(BLOCK.z_of(f))[3]
        xs, ys, _ = cam.project(np.array([p, p + np.array([0, -0.18, 0])]))
        hot = k == n and t < T["time"] + 0.5
        fr.line(
            xs[0], ys[0], xs[1], ys[1], "w", 2.4 if hot else 1.6, a * (1.0 if hot else 0.6), glow=0.9 if hot else 0.2
        )
    ca = smooth(lin(t, T["one"], T["one"] + 0.3)) * a * (1 - smooth(lin(t, T["s30"], T["s30"] + 0.5)))
    hud.pill(fr, 960, 930, "5 frames per second", "w", ca, size=24)


# ------------------------------------------------------------------ S30: see you in the next dimension


def grow30(t):
    return ease_out(lin(t, T["s30"] + 0.05, T["s30"] + 1.0))


def fly(t):
    return ease_in(lin(t, T["next"] - 0.1, AUDIO_END))


def R30(t):
    turn = math.pi * ease_io(lin(t, T["next"] - 0.2, T["next"] + 0.7))
    return T4.rotation(("xw", 0.22 * (t - T["s30"])), ("zw", 0.3 * (t - T["s30"]) + turn))


def world30(t, scale):
    p3, _ = T4.project_persp(T4.C @ R30(t).T, 3.0)
    return T4.place(p3, scale=scale)


def cam30(t):
    return orbit((0, 0, 0), 10.0, 0.3, -0.5 + 0.05 * (t - T["s30"]), focal=FOCAL, center=(960.0, 535.0))


def draw_s30(fr, t):
    if t < T["s30"] - 0.1 or t > AUDIO_END:
        return
    g = grow30(t)
    fl = fly(t)
    a = smooth(lin(t, T["s30"], T["s30"] + 0.6)) * (1 - smooth(lin(t, AUDIO_END - 0.35, AUDIO_END)))
    cam = cam30(t)
    world = world30(t, 0.86 * g + 3.4 * fl)
    T4.draw(fr, cam, world, a, width=2.4 + 2.0 * fl, glow=0.8, vertices=0.8 * (1 - fl))
    la = env(t, T["less"] - 0.2, T["less"] + 1.1, 0.3, 0.45) * a
    if la > 0.003:
        xs, ys, _ = cam.project(world)
        for v in range(16):
            fr.text(T4.label(v), float(xs[v]) + 10, float(ys[v]) - 10, "sans", 16, 600, "muted", la, align="left")
    if fl > 0:
        fr.zoom_blur(0.3 * fl)
    _subscribe(fr, t)
    _title(fr, t)


def _subscribe(fr, t):
    sa = smooth(lin(t, T["subscribe"] - 0.15, T["subscribe"] + 0.35)) * (
        1 - smooth(lin(t, T["see"] - 0.1, T["see"] + 0.4))
    )
    if sa <= 0.003:
        return
    s = back(lin(t, T["subscribe"] - 0.15, T["subscribe"] + 0.45))
    w, h = 330 * s, 72 * s
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(960 - w / 2, 940 - h / 2, w, h), h / 2, h / 2)
    p = skia.Path()
    p.addRRect(rr)
    fr.path_fill(p, "ink", 0.06 * sa)
    fr.path_stroke(p, "ink", 2.0, sa, glow=0.5)
    fr.text("SUBSCRIBE", 960, 949, "sans", 26 * s, 700, "ink", sa, tracking=0.22)
    fr.light_sweep(p, lin(t, T["subscribe"] + 0.05, T["subscribe"] + 0.95), strength=0.8)


def _title(fr, t):
    a = smooth(lin(t, T["complex"] - 0.15, T["complex"] + 0.4)) * (1 - smooth(lin(t, T["see"] - 0.1, T["see"] + 0.4)))
    if a <= 0.003:
        return
    title, size, y = "UNDERSTANDING 4D", 54, 118
    fr.text(title, 960, y, "display", size, 600, "ink", a, tracking=0.06, glow=0.2)
    fr.light_sweep(
        text_path(title, 960, y, "display", size, 600, tracking=0.06),
        lin(t, T["visual"] - 0.1, T["visual"] + 0.7),
        strength=0.9,
    )
    half = 190 * ease_io(lin(t, T["complex"], T["complex"] + 0.6))
    fr.line(960 - half, y + 20, 960 + half, y + 20, "w", 2.2, a, glow=0.8)
    fr.text("visually", 960, y + 70, "italic", 38, 500, "w", a, glow=0.3)


# ------------------------------------------------------------------ end screen (silence to cues.TOTAL)

SLOTS = (
    (220.0, "Why the Jacobian Matrix Is So Powerful"),
    (1060.0, "Eigenvectors Finally Make Sense"),
)
SLOT_Y, SLOT_W, SLOT_H = 250.0, 640.0, 360.0


def draw_end(fr, t):
    if t < AUDIO_END - 0.05:
        return
    a = smooth(lin(t, AUDIO_END + 0.1, AUDIO_END + 1.0))
    R = T4.rotation(("xw", 0.12 * (t - AUDIO_END)), ("zw", 0.08 * (t - AUDIO_END)), ("xy", 0.05 * (t - AUDIO_END)))
    p3, _ = T4.project_persp(T4.C @ R.T, 3.0)
    cam = orbit((0, 0, 0), 10.0, 0.3, -0.5 + 0.02 * (t - AUDIO_END), focal=FOCAL, center=(960.0, 540.0))
    T4.draw(fr, cam, T4.place(p3, scale=1.9), 0.15 * a, width=2.0, glow=0.3)
    fr.text("KEEP EXPLORING", 960, 170, "sans", 22, 700, "muted", a, tracking=0.3)
    for k, (x, title) in enumerate(SLOTS):
        sa = smooth(lin(t, AUDIO_END + 0.3 + 0.15 * k, AUDIO_END + 1.1 + 0.15 * k))
        hud.glass_card(fr, x, SLOT_Y, SLOT_W, SLOT_H, 0.6 * sa, r=16)
        fr.rrect(x, SLOT_Y, SLOT_W, SLOT_H, 16, stroke="ink", width=1.6, alpha=0.45 * sa)
        fr.text(title, x + SLOT_W / 2, SLOT_Y + SLOT_H + 52, "sans", 26, 600, "ink", 0.85 * sa)
    ca = smooth(lin(t, AUDIO_END + 0.6, AUDIO_END + 1.4))
    fr.circle(960, 820, 78, "ink", 2.0, 0.6 * ca, glow=0.3)
    fr.text("SUBSCRIBE", 960, 940, "sans", 20, 700, "muted", ca, tracking=0.26)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_s28(fr, t)
    draw_s29(fr, t)
    draw_s30(fr, t)
    draw_end(fr, t)
    hud.eyebrow(fr, t, "07 · RECAP", START + 0.22)
    fr.vignette(0.5)
    fr.grain(t, 0.045)
    return fr.finish()


def blur_weight(t):
    return max(env(t, T["s29"] - 0.1, T["s29"] + 0.9, 0.2, 0.3), env(t, T["next"] - 0.2, AUDIO_END, 0.3, 0.05))


def draw(t, size):
    t = t + START
    return motion_blur(draw_one, t, size, weight=blur_weight(t))


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch7:{Path(__file__).stat().st_mtime_ns}"
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
    466.4,
    468.0,
    470.2,
    473.4,
    474.9,
    478.6,
    481.0,
    482.9,
    484.5,
    486.4,
    488.6,
    491.4,
    493.9,
    495.8,
    496.6,
    498.8,
    500.2,
    501.6,
    502.6,
    503.4,
    504.9,
    505.7,
    507.6,
    509.0,
    509.7,
    511.5,
    520.0,
]
