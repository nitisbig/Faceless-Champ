"""CHAPTER 1 - WHAT IS A DIMENSION? (S04-S07), 00:49.560 - 02:03.040.

S04  An ant on a wire, a table, a room   one continuous camera crane: 1 number -> 2 -> 3, live readout chip
S05  Numbers make a vector               chip -> column vector (3, 2, 5); tip-to-tail arrows; basis vectors and
                                         the linear combination 3e_x + 2e_y + 5e_z
S06  The fourth arrow                    the vector grows a blue w slot; a blue arrow searches for a direction at
                                         right angles to x, y and z (live angles) and fails; the algebra plaque
                                         adds, scales and measures 4-vectors (computed)
S07  You have already seen it            the cheetah block returns; a reticle and loupe on the eye's real pixel
                                         (1115, 354) of frame 38; one more slot; collapse to a point (-> S08)

Math coordinates are x right, y forward, z up; ``W3`` maps them into the y-up view world of space.Camera.
"""

from __future__ import annotations

import math
from pathlib import Path

import media
import numpy as np
import skia
import typmath
from components import hud
from components.cheetah_block import CheetahBlock
from components.vector_slot import Slot, draw_vector
from cues import AUDIO, cue
from fx import Frame, chroma_kick, ease_io, ease_out, env, font, lerp, lin, motion_blur, pulse, smooth, text_width
from space import Spline, orbit, text3d, to_view
from theme import THEME, TOKENS, H, W
from typmath import tc

START = cue(142)  # 49.56 "So first, what actually is a dimension?"
END = cue(365)  # 123.04 "So let's build a four-dimensional object"

_C = {
    i: cue(i)
    for i in (
        148,
        151,
        162,
        169,
        176,
        180,
        183,
        187,
        190,
        198,
        200,
        201,
        209,
        216,
        223,
        226,
        227,
        228,
        230,
        233,
        234,
        236,
        238,
        240,
        246,
        250,
        258,
        262,
        266,
        271,
        274,
        276,
        278,
        282,
        284,
        287,
        288,
        290,
        291,
        293,
        295,
        303,
        305,
        308,
        315,
        319,
        320,
        325,
        329,
        338,
        340,
        343,
        348,
        349,
        352,
        355,
        356,
        359,
        363,
    )
}
T = {
    "dimension?": _C[148],
    "ant": _C[151],
    "one_number": _C[162],
    "one_dim": _C[169],
    "table": _C[176],
    "two": _C[180],
    "right": _C[183],
    "forward": _C[187],
    "fly": _C[190],
    "third": _C[198],
    "high": _C[200],
    "s05": _C[201],
    "independent": _C[209],
    "position": _C[216],
    "vector": _C[223],
    "v3": _C[226],
    "v2": _C[227],
    "v5": _C[228],
    "ax": (_C[230], _C[233]),
    "ay": (_C[234], _C[236]),
    "az": (_C[238], _C[240]),
    "unit": _C[246],
    "basis": _C[250],
    "mix": _C[258],
    "s06": _C[262],
    "trick": _C[266],
    "stop": _C[271],
    "add_w": _C[274],
    "fourth": _C[276],
    "w": _C[278],
    "arrow": _C[282],
    "right_angles": _C[284],
    "at_x": _C[287],
    "at_y": _C[288],
    "at_z": _C[290],
    "all_once": (_C[291], _C[293]),
    "cannot": _C[295],
    "add": _C[303],
    "scale": _C[305],
    "measure": _C[308],
    "flinch": (_C[315], _C[319]),
    "s07": _C[320],
    "space": _C[325],
    "pixel": _C[329],
    "px": _C[338],
    "py": _C[340],
    "pf": _C[343],
    "block": (_C[348], _C[349]),
    "time": (_C[352], _C[355]),
    "one_more": (_C[356], _C[359]),
    "four": _C[363],
}

FOCAL = 1500.0
EYE_FRAME, EYE_PX, EYE_PY = 38, 1115, 354  # the cheetah's eye in media/prepared/full/038.jpg (measured)


def W3(p):
    """Math point(s) (x, y, z up) -> view world."""
    return to_view(np.asarray(p, float))


# ------------------------------------------------------------------ one camera crane for S04-S06

# time, view target (3), dist, elev, azim, screen centre x
CAMERA = Spline(
    [
        (START, W3((3.0, 0.0, 0.0)), 7.0, 0.02, 0.0, 960.0),
        (T["table"] - 0.2, W3((3.0, 0.0, 0.0)), 7.0, 0.02, 0.0, 960.0),
        (T["table"] + 1.4, W3((3.0, 1.6, 0.0)), 9.0, 0.62, -0.08, 960.0),
        (T["fly"] - 0.1, W3((3.0, 1.6, 0.0)), 9.2, 0.60, -0.12, 960.0),
        (T["fly"] + 2.0, W3((3.0, 1.8, 1.4)), 12.0, 0.42, -0.55, 960.0),
        (T["s05"] + 0.6, W3((2.6, 1.8, 2.2)), 13.0, 0.36, -0.60, 1320.0),  # axes step right for the chip
        (T["vector"] + 0.8, W3((2.0, 1.5, 2.4)), 12.0, 0.32, -0.62, 1180.0),
        (T["unit"] - 0.4, W3((2.0, 1.5, 2.4)), 12.0, 0.32, -0.60, 1180.0),
        (T["unit"] + 0.6, W3((1.0, 0.9, 1.0)), 7.5, 0.34, -0.60, 1180.0),  # push in on the basis vectors
        (T["mix"] - 0.2, W3((1.0, 0.9, 1.0)), 7.8, 0.34, -0.58, 1180.0),
        (T["mix"] + 1.0, W3((2.0, 1.5, 2.4)), 12.4, 0.30, -0.52, 1180.0),
        (T["trick"] + 1.2, W3((1.2, 0.9, 1.5)), 10.0, 0.30, -0.46, 1180.0),  # close on the origin: w's search
        (T["s07"], W3((1.2, 0.9, 1.5)), 10.5, 0.28, -0.40, 1180.0),
    ]
)


def camera(t):
    v = CAMERA(t)
    return orbit(v[:3], v[3], v[4], v[5], focal=FOCAL, center=(v[6], 540.0))


# ------------------------------------------------------------------ the ant


def ant_pos(t: float) -> np.ndarray:
    """Math position of the ant: walk the wire, walk the table, fly up."""
    if t < T["table"] + 0.2:
        x = lerp(0.6, 2.4, ease_io(lin(t, T["ant"] + 0.2, T["one_number"] + 0.3)))
        x = lerp(x, 3.0, ease_io(lin(t, T["one_dim"] - 0.4, T["table"])))
        return np.array([x, 0.0, 0.0])
    u = ease_io(lin(t, T["table"] + 0.2, T["forward"] + 0.5))
    p = np.array([lerp(3.0, 3.4, u), lerp(0.0, 1.8, u), 0.0])
    f = ease_io(lin(t, T["fly"], T["third"] + 0.1))
    bob = 0.06 * math.sin((t - T["fly"]) * 5.0) * f
    return p + np.array([0.0, 0.0, 2.6 * f + bob])


def ant_alpha(t):
    return env(t, T["ant"] - 0.1, T["s05"] + 0.5, 0.4, 0.6)


def _ellipse(fr, cx, cy, rx, ry, ang, color, alpha, glow=0.0):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(-rx, -ry, rx, ry))
    m = skia.Matrix()
    m.setRotate(math.degrees(ang))
    m.postTranslate(cx, cy)
    p.transform(m)
    fr.path_fill(p, color, alpha, glow=glow)


def draw_ant(fr, x, y, size, heading, t, alpha=1.0, flying=0.0):
    """Stylized top-down ant: three body segments, six legs in a tripod walk cycle, antennae; wings when flying."""
    if alpha <= 0.003:
        return
    c, s = math.cos(heading), math.sin(heading)

    def P(u, v):
        return x + size * (u * c - v * s), y + size * (u * s + v * c)

    phase = t * 9.0
    lw = max(1.2, size * 0.05)
    tuck = 1 - 0.55 * flying
    for k, hip_u in enumerate((0.08, 0.0, -0.08)):  # front, middle, back
        for side in (1, -1):
            group = (k + (0 if side > 0 else 1)) % 2  # tripod gait
            swing = math.sin(phase + math.pi * group) * (1 - flying)
            reach = (0.18, 0.02, -0.18)[k] + 0.08 * swing
            hip = P(hip_u, 0.07 * side)
            knee = P(hip_u + reach * 0.6, 0.27 * side * tuck)
            foot = P(hip_u + reach, 0.42 * side * tuck)
            fr.poly([hip[0], knee[0], foot[0]], [hip[1], knee[1], foot[1]], "ink", lw, alpha * 0.9)
    for side in (1, -1):  # antennae
        a0, a1, a2 = P(0.34, 0.04 * side), P(0.5, 0.16 * side), P(0.62, 0.2 * side)
        fr.poly([a0[0], a1[0], a2[0]], [a0[1], a1[1], a2[1]], "ink", lw * 0.8, alpha * 0.85)
    if flying > 0.01:  # a blur of wings: several translucent beats
        for k in range(4):
            beat = math.sin(t * 60.0 + k * 1.6) * 0.5
            for side in (1, -1):
                wx, wy = P(-0.12, 0.18 * side)
                _ellipse(
                    fr,
                    wx,
                    wy,
                    size * 0.34,
                    size * 0.12,
                    heading + side * (0.9 + beat),
                    "#CFE6FF",
                    alpha * flying * 0.12,
                )
    for u, rx, ry in ((-0.42, 0.30, 0.20), (0.0, 0.16, 0.11), (0.27, 0.12, 0.11)):
        cx, cy = P(u, 0.0)
        _ellipse(fr, cx, cy, size * rx, size * ry, heading, "ink", alpha, glow=0.0)
        _ellipse(fr, cx, cy, size * rx * 1.05, size * ry * 1.05, heading, "x", alpha * 0.25, glow=0.6)


def ant_screen(cam, t):
    """Screen position, depth and heading. The heading looks further back in time while the ant stands still, so it
    keeps facing the way it last walked (deterministic: no state between frames)."""
    xs, ys, z = cam.project(W3(ant_pos(t))[None])
    heading = 0.0
    for d in (0.06, 0.25, 0.6, 1.2, 2.5):
        p0, p1 = ant_pos(t - d), ant_pos(t + 0.06)
        if np.linalg.norm(p1[:2] - p0[:2]) > 1e-3:
            ax, ay, _ = cam.project(W3(np.array([p0 * [1, 1, 0], p1 * [1, 1, 0]])))
            heading = math.atan2(ay[1] - ay[0], ax[1] - ax[0])
            break
    return float(xs[0]), float(ys[0]), float(z[0]), heading


def draw_s04(fr, cam, t):
    # 04A: the question
    qa = env(t, START - 0.01, T["ant"] - 0.4, 0.01, 0.6)
    if qa > 0:
        lift = 60 * ease_io(lin(t, T["dimension?"] + 0.5, T["ant"] - 0.4))
        track = lerp(0.3, 0.02, ease_out(lin(t, START, START + 0.9)))
        base, y = "What is a dimension", 560 - lift
        q = pulse(t, T["dimension?"] - 0.05, 0.5)
        f = font("display", 84, 600)
        wb = text_width(base, f, track)
        x0 = 960 - (wb + 8 + f.measureText("?")) / 2
        a_in = smooth(lin(t, START, START + 0.7)) * qa
        fr.text(base, x0, y, "display", 84, 600, "ink", a_in, align="left", tracking=track)
        fr.text("?", x0 + wb + 8, y, "display", 84 * (1 + 0.35 * q), 600, "w", a_in, align="left", glow=0.6 * q)
    hud.eyebrow(fr, t, "01 · DIMENSIONS", T["ant"] - 0.7)
    aa = ant_alpha(t)
    # axes and floor
    wire_u = ease_out(lin(t, T["ant"] - 0.5, T["ant"] + 0.4))
    if wire_u > 0:
        _draw_axes(fr, cam, t, wire_u)
    _draw_table_grid(fr, cam, t)
    _draw_room(fr, cam, t)
    if aa <= 0.003:
        return
    x, y, z, heading = ant_screen(cam, t)
    size = 90.0 * 7.0 / max(z, 1.0)
    fly = smooth(lin(t, T["fly"] - 0.1, T["fly"] + 0.5))
    p = ant_pos(t)
    # projection guides
    if T["two"] - 0.3 < t < T["s05"] + 0.5:
        ga = env(t, T["two"] - 0.3, T["s05"] + 0.5, 0.4, 0.5) * aa
        foot = W3((p[0], p[1], 0.0))
        for q in (W3((p[0], 0, 0)), W3((0, p[1], 0))):
            xs, ys, _ = cam.project(np.array([foot, q]))
            fr.dashed(xs, ys, "muted", 1.4, 0.6 * ga, on=8, off=7)
    if t > T["high"] - 0.3:
        ha = env(t, T["high"] - 0.3, T["s05"] + 0.5, 0.3, 0.5) * aa
        xs, ys, _ = cam.project(np.array([W3(p), W3((p[0], p[1], 0.0))]))
        fr.dashed(xs, ys, "z", 2.0, ha, glow=0.5, on=10, off=7)
    draw_ant(fr, x, y, size, heading, t, aa, fly)
    # the readout chip rides above the ant, then flies to the centre (S05A)
    _draw_ant_chip(fr, t, x, y - size * 1.4, aa)


def _draw_axes(fr, cam, t, wire_u):
    """x (the wire), then y on 'table', then z on 'fly'. They stay for S05-S06 as the vector space."""
    out = 1 - smooth(lin(t, T["s07"] - 0.2, T["s07"] + 0.9))
    if out <= 0:
        return
    pr = pulse(t, T["right"] - 0.05, 0.6)
    pf = pulse(t, T["forward"] - 0.05, 0.6)
    ends = {
        "x": (W3((-0.6, 0, 0)), W3((6.6, 0, 0))),
        "y": (W3((0, 0, 0)), W3((0, 4.6, 0))),
        "z": (W3((0, 0, 0)), W3((0, 0, 5.8))),
    }
    grow = {
        "x": wire_u,
        "y": ease_io(lin(t, T["table"] + 0.2, T["table"] + 1.1)),
        "z": ease_io(lin(t, T["fly"] + 0.3, T["fly"] + 1.3)),
    }
    flare = {"x": pr, "y": pf, "z": 0.0}
    for k in "xyz":
        u = grow[k]
        if u <= 0:
            continue
        p0, p1 = ends[k]
        p1 = p0 + (p1 - p0) * u
        xs, ys, z = cam.project(np.array([p0, p1]))
        if np.any(z <= 0.05):
            continue
        hud.arrow(fr, xs[0], ys[0], xs[1], ys[1], k, 2.4 + 1.6 * flare[k], out, glow=0.7 + 0.8 * flare[k])
        la = smooth(lin(u, 0.6, 1.0)) * out
        text3d(fr, cam, k, p0 + (p1 - p0) * 1.05, 0.42, TOKENS[k], la, 500, "italic")
    # mono ticks under the wire (1D only)
    ta = wire_u * (1 - smooth(lin(t, T["table"], T["table"] + 0.8)))
    if ta > 0:
        for i in range(7):
            xs, ys, _ = cam.project(np.array([W3((i, 0, 0)), W3((i, 0, -0.12))]))
            fr.line(xs[0], ys[0], xs[1], ys[1], "muted", 1.4, 0.7 * ta)
            fr.text(str(i), xs[1], ys[1] + 26, "sans", 20, 500, "muted", 0.6 * ta)


def _draw_table_grid(fr, cam, t):
    a = smooth(lin(t, T["table"] - 0.1, T["table"] + 1.0)) * (1 - smooth(lin(t, T["s07"] - 0.2, T["s07"] + 0.9)))
    a *= 0.55 - 0.3 * smooth(lin(t, T["fly"], T["fly"] + 1.0))
    if a <= 0.003:
        return
    for i in range(7):
        xs, ys, _ = cam.project(np.array([W3((i, 0, 0)), W3((i, 4.0, 0))]))
        fr.line(xs[0], ys[0], xs[1], ys[1], "#3A4A63", 1.0, a)
    for j in range(5):
        xs, ys, _ = cam.project(np.array([W3((0, j, 0)), W3((6.0, j, 0))]))
        fr.line(xs[0], ys[0], xs[1], ys[1], "#3A4A63", 1.0, a)


def _draw_room(fr, cam, t):
    a = 0.14 * smooth(lin(t, T["fly"], T["fly"] + 1.2)) * (1 - smooth(lin(t, T["s05"], T["s05"] + 1.5)))
    if a <= 0.003:
        return
    X, Y, Z = 6.5, 4.5, 5.2
    for p, q in (
        ((0, Y, 0), (0, Y, Z)),
        ((X, Y, 0), (X, Y, Z)),
        ((0, Y, Z), (X, Y, Z)),
        ((0, 0, Z), (0, Y, Z)),
        ((X, 0, 0), (X, Y, 0)),
        ((0, Y, 0), (X, Y, 0)),
    ):
        xs, ys, _ = cam.project(np.array([W3(p), W3(q)]))
        fr.line(xs[0], ys[0], xs[1], ys[1], "ink", 1.0, a)


def _chip_values(t):
    p = ant_pos(min(t, T["s05"] - 0.2))
    return [f"{p[0]:.1f}", f"{p[1]:.1f}", f"{p[2]:.1f}"]


def _draw_ant_chip(fr, t, x, y, aa):
    """1D 'x = 2.4' -> 2D '(x, y)' -> 3D '(x, y, z)', riding above the ant until S05 takes it."""
    if t >= T["s05"] - 0.35:
        return
    a = aa * smooth(lin(t, T["one_number"] - 0.2, T["one_number"] + 0.3))
    if a <= 0.003:
        return
    vals = _chip_values(t)
    if t < T["two"] - 0.1:
        hud.readout(fr, x, y, "x =", vals[0], "x", a, size=32)
        hud.pill(fr, x, y + 220, "1D", "x", a * smooth(lin(t, T["one_dim"] - 0.1, T["one_dim"] + 0.3)), size=24)
        return
    n = 2 if t < T["third"] - 0.1 else 3
    flash = {0: pulse(t, T["right"] - 0.05, 0.6), 1: pulse(t, T["forward"] - 0.05, 0.6)}
    if n == 3:
        flash[2] = pulse(t, T["third"] - 0.05, 0.6)
    hud.coord_chip(fr, x, y, vals[:n], list("xyz"[:n]), a, size=28, flash=flash)


# ------------------------------------------------------------------ S05: numbers make a vector

VEC_X, VEC_Y, VEC_SIZE = 250.0, 520.0, 60.0


def chip_state(t):
    """Centre chip (S05A): position, size and the spread between its numbers."""
    fly = ease_io(lin(t, T["s05"] - 0.35, T["s05"] + 0.6))
    gap = lerp(1.0, 2.3, ease_out(lin(t, T["independent"] - 0.1, T["independent"] + 0.6)))
    return fly, gap


def draw_s05(fr, cam, t):
    fade_all = 1 - smooth(lin(t, T["s07"] - 0.3, T["s07"] + 0.8))
    if t < T["s05"] - 0.35 or fade_all <= 0:
        return
    # --- 05A: the chip flies to the centre and its numbers come apart
    morph = ease_io(lin(t, T["vector"] - 0.1, T["vector"] + 0.8))  # chip -> column
    p_last = ant_pos(T["s05"] - 0.2)
    old = [f"{v:.1f}" for v in p_last]
    vary = math.sin(math.pi * lin(t, T["independent"] + 0.4, T["position"] - 0.3))  # y changes, x and z hold
    if vary > 0:
        old[1] = f"{p_last[1] + 2.1 * vary:.1f}"
    fly, gap = chip_state(t)
    if morph < 1:
        x0, y0 = lerp(960.0, 720.0, fly), lerp(380.0, 540.0, fly)
        a = fade_all if morph <= 0.0 else 0.0  # the flying copies take over in one frame, at identical positions
        centers = hud.coord_chip(
            fr, x0, y0, old, list("xyz"), a, size=lerp(28, 60, fly), gap=gap, flash={1: 0.8 * vary}, card=morph < 0.05
        )
        ul = smooth(lin(t, T["independent"], T["independent"] + 0.5)) * a
        for cx, k in zip(centers, "xyz"):
            fr.line(cx - 34, y0 + 52, cx + 34, y0 + 52, k, 2.4, ul, glow=0.5)
        la = env(t, T["position"] - 0.1, T["vector"] + 0.2, 0.4, 0.4) * fade_all
        fr.text("dimension = how many numbers", x0, y0 + 140, "sans", 32, 600, "muted", la)
        if morph > 0:  # the numbers travel into the column
            for i, (cx, k) in enumerate(zip(centers, "xyz")):
                tx, ty = lerp(cx, VEC_X, morph), lerp(y0, VEC_Y + (i - 1) * VEC_SIZE * 1.3, morph)
                handoff = 1 - smooth(lin(morph, 0.9, 1.0))  # the Typst entries take over as they land
                hud.tabular(fr, old[i], tx, ty + 20, lerp(60, VEC_SIZE, morph), k, handoff * fade_all)
    # --- 05B: the vector (3, 2, 5)
    if morph > 0:
        vals = ["3", "2", "5"]
        cue_t = (T["v3"], T["v2"], T["v5"])
        slots = []
        for i, k in enumerate("xyz"):
            u = smooth(lin(t, cue_t[i] - 0.1, cue_t[i] + 0.2))
            glow = 0.9 * pulse(t, cue_t[i] - 0.1, 0.5) + 0.8 * _slot_link(t, i)
            slots.append(Slot(vals[i] if u > 0.5 else old[i], k, alpha=1.0, glow=glow, underline=1.0))
        draw_vector(
            fr,
            VEC_X,
            VEC_Y,
            _maybe_w(slots, t),
            VEC_SIZE,
            alpha=smooth(lin(morph, 0.9, 1.0)) * fade_all,
            brackets=ease_out(lin(t, T["vector"] + 0.2, T["vector"] + 0.8)),
            grow=_grow_w(t),
        )
        _draw_wall(fr, t)
    # --- right side: the arrows in the same 3D world
    _draw_chain(fr, cam, t, fade_all)
    _draw_basis(fr, cam, t, fade_all)
    fa = env(t, T["mix"] - 0.1, T["trick"] + 0.2, 0.3, 0.6) * fade_all
    if fa > 0:
        expr = f"{tc('x', '3 e_x')} + {tc('y', '2 e_y')} + {tc('z', '5 e_z')} = (3, 2, 5)"
        typmath.draw(fr, expr, 110, 840, 50, alpha=fa, align="left", reveal=lin(t, T["mix"] - 0.05, T["mix"] + 0.9))


def _slot_link(t, i):
    """A slot glows while its arrow is drawing (S05B)."""
    a, b = (T["ax"], T["ay"], T["az"])[i]
    return env(t, a - 0.1, b + 0.5, 0.2, 0.4)


def _maybe_w(slots, t):
    if t < T["fourth"] - 0.1:
        return slots
    pw = pulse(t, T["w"] - 0.1, 0.6)
    return slots + [Slot("w", "w", glow=0.5 + 0.9 * pw, underline=1.0)]


def _grow_w(t):
    if t < T["fourth"] - 0.1:
        return None
    return (3, lin(t, T["fourth"] - 0.1, T["fourth"] + 0.55))


def _draw_wall(fr, t):
    """'Nothing forces us to stop at three': a faint wall under the z slot, pushed away when w arrives."""
    a = env(t, T["stop"] - 0.1, T["w"] + 0.4, 0.4, 0.5)
    if a <= 0:
        return
    push = ease_out(lin(t, T["fourth"] - 0.1, T["fourth"] + 0.55))
    y = VEC_Y + 1.5 * VEC_SIZE * 1.3 + 34 + push * VEC_SIZE * 1.3
    fr.line(VEC_X - 70, y, VEC_X + 70, y, "ink", 2.0, 0.7 * a * (1 - 0.5 * push), glow=0.4)
    for k in range(-3, 4):
        fr.line(VEC_X + k * 20, y, VEC_X + k * 20 - 10, y + 12, "ink", 1.2, 0.35 * a * (1 - 0.5 * push))


def _arrow_m(fr, cam, p0, p1, color, width, alpha, glow=0.6, head=16.0):
    return hud.arrow3d(fr, cam, W3(p0), W3(p1), color, width, alpha, glow, head)


def _draw_chain(fr, cam, t, fade_all):
    """S05B tip-to-tail: 3 along x (with step ticks), 2 along y, 5 along z, then the resultant (3, 2, 5)."""
    dim = 1 - 0.65 * smooth(lin(t, T["unit"] - 0.3, T["unit"] + 0.3))
    split = smooth(lin(t, T["mix"] - 0.05, T["mix"] + 0.8))  # long arrows give way to unit copies
    a_all = fade_all * (1 - 0.7 * smooth(lin(t, T["trick"], T["trick"] + 1.0)))
    legs = (
        ((0, 0, 0), (3, 0, 0), "x", T["ax"]),
        ((3, 0, 0), (3, 2, 0), "y", T["ay"]),
        ((3, 2, 0), (3, 2, 5), "z", T["az"]),
    )
    for p0, p1, k, (a, b) in legs:
        u = ease_io(lin(t, a - 0.05, b + 0.1))
        if u <= 0:
            continue
        p0, p1 = np.array(p0, float), np.array(p1, float)
        tip = p0 + (p1 - p0) * u
        _arrow_m(fr, cam, p0, tip, k, 3.0, a_all * dim * (1 - split), 0.8)
        n = int(round(np.linalg.norm(p1 - p0)))
        d = (p1 - p0) / n
        side = np.array([0, 0, 1.0]) if k != "z" else np.array([1.0, 0, 0])
        for s in range(1, n + 1):  # step ticks
            if s / n <= u + 1e-6:
                c = p0 + d * s
                xs, ys, _ = cam.project(np.array([W3(c - side * 0.12), W3(c + side * 0.12)]))
                fr.line(xs[0], ys[0], xs[1], ys[1], k, 1.6, 0.8 * a_all * dim)
    ru = ease_io(lin(t, T["az"][1] + 0.1, T["az"][1] + 0.8))
    if ru > 0:
        tip = np.array([3.0, 2.0, 5.0]) * ru
        _arrow_m(fr, cam, (0, 0, 0), tip, "ink", 3.4, a_all * (0.5 + 0.5 * dim), 1.0, 20)
        ba = 0.28 * smooth(lin(t, T["az"][1] + 0.5, T["az"][1] + 1.0)) * a_all
        box = np.array([[x, y, z] for x in (0, 3) for y in (0, 2) for z in (0, 5)], float)
        for i in range(8):
            for j in range(i + 1, 8):
                if bin(i ^ j).count("1") == 1:
                    xs, ys, _ = cam.project(W3(box[[i, j]]))
                    fr.dashed(xs, ys, "ink", 1.0, ba, on=6, off=6)
    # 05C "mix of those arrows": unit copies, 3 red + 2 orange + 5 yellow
    if split > 0:
        copies = (
            [((k, 0, 0), (k + 1, 0, 0), "x") for k in range(3)]
            + [((3, k, 0), (3, k + 1, 0), "y") for k in range(2)]
            + [((3, 2, k), (3, 2, k + 1), "z") for k in range(5)]
        )
        for n, (p0, p1, k) in enumerate(copies):
            ca = smooth(lin(t, T["mix"] + 0.07 * n, T["mix"] + 0.07 * n + 0.3)) * a_all
            if ca > 0:
                _arrow_m(fr, cam, p0, p1, k, 2.6, ca, 0.7, 13)


def _draw_basis(fr, cam, t, fade_all):
    a = smooth(lin(t, T["unit"] - 0.1, T["unit"] + 0.4)) * fade_all
    if a <= 0:
        return
    g = pulse(t, T["basis"] - 0.05, 0.7)
    for k, d in (("x", (1, 0, 0)), ("y", (0, 1, 0)), ("z", (0, 0, 1))):
        xs, ys = _arrow_m(fr, cam, (0, 0, 0), d, k, 4.0 + 1.5 * g, a, 1.0 + 1.2 * g, 18)
        lx, ly, _ = cam.project(W3(np.array(d, float) * 1.35)[None])
        typmath.draw(fr, f"e_{k}", float(lx[0]), float(ly[0]), 40, color=k, alpha=a, glow=0.3 + g)
        if g > 0.05:
            fr.glow_dot(xs[1], ys[1], 4 + 6 * g, k, g, 1.4)


# ------------------------------------------------------------------ S06: the fourth arrow

A4 = np.array([1, 2, 0, 3])
B4 = np.array([2, 0, 1, 1])


def _search_dir(t):
    """The blue arrow's direction while it searches (math coords, unit)."""
    keys = [
        (T["arrow"], np.array([1.0, 1.0, 1.0])),  # every angle about 55 degrees
        (T["at_x"], np.array([0.0, -1.0, 1.0])),  # right angle to x
        (T["at_y"] + 0.12, np.array([0.0, 0.0, 1.0])),  # right angles to x and y ... but it *is* z
        (T["at_z"], np.array([1.0, -1.0, 0.0])),  # right angle to z, but not x or y
    ]
    keys = [(k, v / np.linalg.norm(v)) for k, v in keys]
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            return _slerp(a, b, ease_io(lin(t, t0, t1)))
    return keys[-1][1]


def _slerp(a, b, u):
    d = float(np.clip(a @ b, -1, 1))
    om = math.acos(d)
    if om < 1e-4:
        return a
    return (math.sin((1 - u) * om) * a + math.sin(u * om) * b) / math.sin(om)


OUT_DIR = np.array([-0.55, -0.45, 0.70]) / np.linalg.norm([-0.55, -0.45, 0.70])


def draw_s06(fr, cam, t):
    fade_all = 1 - smooth(lin(t, T["s07"] - 0.3, T["s07"] + 0.8))
    if t < T["arrow"] - 0.2 or fade_all <= 0:
        return
    fail = ease_io(lin(t, T["all_once"][0] - 0.05, T["all_once"][1]))
    dim_arrow = 1 - 0.7 * smooth(lin(t, T["cannot"] - 0.1, T["cannot"] + 0.5))
    grow = back_ease(lin(t, T["arrow"] - 0.15, T["arrow"] + 0.45))
    d = _search_dir(t)
    d = _slerp(d, OUT_DIR, fail) if fail > 0 else d
    L = 2.6 * grow
    jitter = np.zeros(3)
    if 0 < fail < 1:
        rng = np.random.default_rng(int(t * 30))
        jitter = rng.normal(0, 0.05, 3) * math.sin(math.pi * fail)
    tip = d * L + jitter
    xs, ys = hud.arrow3d(
        fr, cam, W3((0, 0, 0)), W3(tip), "w", 3.2, fade_all * dim_arrow, 1.0 + 0.4 * fail, 20, dashed=fail > 0.5
    )
    if fail > 0.5:
        lx, ly, _ = cam.project(W3(d * (L + 0.35))[None])
        typmath.draw(fr, "w", float(lx[0]), float(ly[0]), 46, color="w", alpha=fade_all * dim_arrow, glow=0.5)
    # live angles and right-angle markers while it searches
    ra = env(t, T["right_angles"] - 0.2, T["cannot"] + 0.2, 0.3, 0.4) * fade_all
    if ra > 0:
        for i, k in enumerate("xyz"):
            axis = np.eye(3)[i]
            ang = math.degrees(math.acos(float(np.clip(d @ axis, -1, 1))))
            hud.readout(fr, 1660, 160 + 80 * i, f"∠(w, {k})", f"{ang:5.1f}°", k, ra, size=32)
            hit = smooth(lin(1.5 - abs(ang - 90.0), 0.0, 1.0)) * ra
            if hit > 0 and grow > 0.5:
                hud.right_angle(fr, cam, W3((0, 0, 0)), W3(d), W3(axis), 0.42, k, hit)
    # 06C: the algebra does not flinch: three visual tiles (add, scale, measure), one key word each
    pa = smooth(lin(t, T["add"] - 0.8, T["add"] - 0.2)) * fade_all
    if pa > 0:
        fr.dim(0.72 * pa)
        flash = pulse(t, T["flinch"][0] - 0.05, T["flinch"][1] - T["flinch"][0] + 0.4)
        for i, (kind, tc0) in enumerate((("add", T["add"]), ("scale", T["scale"]), ("measure", T["measure"]))):
            _op_tile(fr, t, 620 + 340 * i, 640, kind, tc0, pa, flash)
        ta = smooth(lin(t, T["flinch"][0] - 0.1, T["flinch"][0] + 0.4)) * pa
        hud.pill(fr, 960, 905, "same rules in 4D", "w", ta, size=26)
        fr.chroma(chroma_kick(t, T["flinch"][0], 3.0))


TILE = 300.0


def _op_tile(fr, t, cx, cy, kind, t0, alpha, flash):
    """A glass tile: the operation drawn as arrows, a 4-dot (x y z w) strip, and one key word."""
    a = smooth(lin(t, t0 - 0.35, t0 + 0.1)) * alpha
    if a <= 0.003:
        return
    rise = (1 - ease_out(lin(t, t0 - 0.35, t0 + 0.3))) * 30
    cy += rise
    x0, y0 = cx - TILE / 2, cy - TILE / 2
    hud.glass_card(fr, x0, y0, TILE, TILE, a, r=20, glow=0.35 * flash, glow_color="w")
    u = ease_io(lin(t, t0 - 0.05, t0 + 0.7))
    o = np.array([cx - 95.0, cy + 55.0])
    g = 0.5 + 0.8 * flash
    if kind == "add":
        va, vb = np.array([120.0, -35.0]), np.array([45.0, -105.0])
        hud.arrow(fr, *o, *(o + va), "ink", 2.6, a, glow=0.3, head=13)
        if u > 0:
            hud.arrow(fr, *(o + va), *(o + va + vb * min(1.0, 2 * u)), "w", 2.6, a, glow=0.5, head=13)
        if u > 0.5:
            s = ease_out((u - 0.5) * 2)
            hud.arrow(fr, *o, *(o + (va + vb) * s), "#ffffff", 3.2, a, glow=g, head=15)
        typmath.draw(fr, "bold(a) + bold(b)", cx + 70, cy + 32, 30, color="muted", alpha=a * smooth(u))
    elif kind == "scale":
        v = np.array([80.0, -55.0])
        hud.arrow(fr, *o, *(o + 2.2 * v), "muted", 1.6, 0.35 * a, glow=0.0, head=11, dashed=True)
        k = lerp(1.0, 2.0, u)
        hud.arrow(fr, *o, *(o + k * v), "w", 3.2, a, glow=g, head=15)
        typmath.draw(fr, "times 2", cx + 82, cy - 62, 32, color="ink", alpha=a * smooth(u))
    else:
        v = np.array([190.0, -110.0])
        hud.arrow(fr, *o, *(o + v), "ink", 3.0, a, glow=0.4, head=15)
        n = np.array([v[1], -v[0]]) / np.linalg.norm(v) * 24
        p0, p1 = o + n, o + n + v * u
        fr.line(*p0, *p1, "w", 2.2, a, glow=g)
        for p in (p0, p1):
            fr.line(*(p - n * 0.35), *(p + n * 0.35), "w", 2.2, a)
        typmath.draw(fr, "norm(bold(v))", cx - 6, cy - 82, 32, color="w", alpha=a * smooth(lin(u, 0.6, 1.0)))
    for k, c in enumerate("xyzw"):  # four numbers, one per axis: the same in any dimension
        fr.glow_dot(cx - 36 + 24 * k, cy + 98, 4.5, c, a, strength=0.5 + 0.6 * flash)
    fr.text(kind.upper(), cx, y0 - 22, "sans", 22, 700, "ink", a, tracking=0.24)


def _v(v):
    """Typst for a 4-vector with its fourth entry in blue."""
    return f"({v[0]}, {v[1]}, {v[2]}, {tc('w', str(v[3]))})"


def back_ease(u, s=1.7):
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    v = u - 1
    return 1 + (s + 1) * v**3 + s * v**2


# ------------------------------------------------------------------ S07: you have already seen it

BLOCK = CheetahBlock(center=(0.0, 0.0, 0.0))


def block_camera(t):
    u = ease_io(lin(t, T["space"] - 0.6, T["space"] + 0.8))
    return orbit(
        (0.0, -0.1, 0.0),
        lerp(26.0, 10.2, u),
        0.26,
        -0.72 + 0.04 * (t - T["s07"]) / 10,
        focal=FOCAL,
        center=(1080.0, 560.0),
    )


def draw_s07(fr, t):
    if t < T["s07"] - 0.2:
        return
    cam = block_camera(t)
    a = smooth(lin(t, T["space"] - 0.6, T["space"] + 0.3))
    rack = 7.0 * (1 - smooth(lin(t, T["space"] - 0.2, T["space"] + 0.9)))
    dimming = 0.5 * smooth(lin(t, T["four"] - 0.2, T["four"] + 0.4))
    outline = env(t, T["block"][0] - 0.1, T["block"][1] + 0.6, 0.3, 0.5)
    collapse = ease_io(lin(t, END - 0.75, END - 0.05))
    with fr.blurred(rack):
        BLOCK.draw(
            fr,
            cam,
            t,
            unfold=1.0,
            hold=EYE_FRAME,
            active=EYE_FRAME,
            volume=a,
            active_alpha=a,
            outline=0.25 * a + 0.9 * outline,
            fade=1 - collapse,
        )
        flare = pulse(t, T["time"][0] - 0.1, T["time"][1] - T["time"][0] + 0.5)
        BLOCK.draw_axes(
            fr,
            cam,
            *(ease_io(lin(t, T["space"] + 0.2 * k, T["space"] + 0.8 + 0.2 * k)) for k in range(3)),
            t_flare=flare,
            alpha=1 - collapse,
        )
    _draw_loupe(fr, cam, t, 1 - collapse)
    fr.dim(dimming * (1 - collapse) + 0.6 * collapse)
    _draw_pixel_vector(fr, t, collapse)


def _draw_loupe(fr, cam, t, fade):
    a = (
        smooth(lin(t, T["pixel"] - 0.1, T["pixel"] + 0.4))
        * fade
        * (1 - smooth(lin(t, T["block"][0], T["block"][0] + 0.6)))
    )
    if a <= 0.003:
        return
    xs, ys, _ = cam.project(BLOCK.pixel(EYE_FRAME, EYE_PX, EYE_PY)[None])
    px, py = float(xs[0]), float(ys[0])
    r = lerp(80.0, 18.0, ease_out(lin(t, T["pixel"] - 0.1, T["pixel"] + 0.5)))
    fr.circle(px, py, r, "ink", 1.8, a, glow=0.6)
    for ang in (0, 90, 180, 270):
        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        fr.line(px + c * (r + 4), py + s * (r + 4), px + c * (r + 16), py + s * (r + 16), "ink", 1.8, a)
    la = smooth(lin(t, T["pixel"] + 0.3, T["pixel"] + 0.8)) * fade
    if la <= 0.003:
        return
    lx, ly, R = 1600.0, 300.0, 170.0
    fr.line(px + r * 0.7, py - r * 0.7, lx - R * 0.7, ly + R * 0.7, "ink", 1.2, 0.6 * la)
    # the real pixels: a 21 x 21 crop around the eye, nearest-neighbour, with a pixel grid
    n = 21
    img = media.frame(EYE_FRAME)
    src = skia.Rect.MakeXYWH(EYE_PX - n // 2, EYE_PY - n // 2, n, n)
    dst = skia.Rect.MakeXYWH(lx - R, ly - R, 2 * R, 2 * R)
    clip = skia.Path()
    clip.addCircle(lx, ly, R)
    fr.c.save()
    fr.c.clipPath(clip, doAntiAlias=True)
    fr.c.drawImageRect(img, src, dst, skia.SamplingOptions(skia.FilterMode.kNearest), skia.Paint(Alphaf=la))
    cell = 2 * R / n
    for k in range(n + 1):
        fr.line(lx - R + k * cell, ly - R, lx - R + k * cell, ly + R, "#000000", 1.0, 0.35 * la)
        fr.line(lx - R, ly - R + k * cell, lx + R, ly - R + k * cell, "#000000", 1.0, 0.35 * la)
    fr.c.restore()
    c0 = lx - R + (n // 2) * cell
    fr.rrect(c0, ly - R + (n // 2) * cell, cell, cell, 2, stroke="ink", width=2.2, alpha=la, glow=0.8)
    fr.circle(lx, ly, R, "ink", 2.2, la, glow=0.5)


def _draw_pixel_vector(fr, t, collapse):
    a = smooth(lin(t, T["px"] - 0.8, T["px"] - 0.3)) * (1 - collapse)
    if a <= 0.003 and collapse <= 0:
        return
    cx = lerp(250.0, 960.0, collapse)
    cy = lerp(560.0, 540.0, collapse)
    size = lerp(48.0, 6.0, collapse)
    vals = ((T["px"], str(EYE_PX), "x", "x"), (T["py"], str(EYE_PY), "y", "y"), (T["pf"], str(EYE_FRAME), "w", "frame"))
    slots = []
    for tc0, v, k, _ in vals:
        u = smooth(lin(t, tc0 - 0.1, tc0 + 0.2))
        slots.append(Slot(v, k, alpha=u, glow=0.9 * pulse(t, tc0 - 0.1, 0.5), underline=u))
    grow = None
    if t > T["one_more"][0] - 0.1:
        q = 0.6 + 0.4 * math.sin(t * 6.0)
        slots.append(Slot("?", "ink", alpha=1.0, glow=0.4 * q))
        grow = (3, lin(t, T["one_more"][0] - 0.1, T["one_more"][1]))
    centers = draw_vector(fr, cx, cy, slots, size, alpha=a, width=size * 2.6, grow=grow) if a > 0.003 else []
    la = a * (1 - collapse)
    for (tc0, _, k, name), yc in zip(vals, centers):
        fr.text(
            name,
            cx - size * 2.0,
            yc + 10,
            "sans",
            30,
            600,
            "muted",
            la * smooth(lin(t, tc0 - 0.1, tc0 + 0.2)),
            align="right",
        )
    if collapse > 0:  # the point S08 drags
        fr.glow_dot(960.0, 540.0, 7.0 * collapse, "ink", collapse, 1.2)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    cam = camera(t)
    rack_out = 8.0 * smooth(lin(t, T["s07"] - 0.3, T["s07"] + 0.9))
    with fr.blurred(rack_out):
        draw_s04(fr, cam, t)
        draw_s05(fr, cam, t)
        draw_s06(fr, cam, t)
    draw_s07(fr, t)
    fr.chroma(chroma_kick(t, T["w"], 5.0))
    fr.vignette(0.5)
    fr.grain(t, 0.045)
    return fr.finish()


def blur_weight(t):
    return max(
        env(t, T["fly"] - 0.1, T["fly"] + 1.4, 0.2, 0.3), env(t, T["arrow"] - 0.1, T["all_once"][1] + 0.2, 0.2, 0.3)
    )


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
STILLS = [
    51.0,
    52.3,
    55.0,
    57.5,
    59.5,
    62.5,
    64.3,
    66.5,
    68.2,
    70.0,
    72.3,
    74.5,
    76.4,
    78.2,
    79.8,
    81.6,
    83.4,
    85.7,
    88.5,
    91.5,
    93.4,
    95.3,
    96.9,
    97.7,
    98.3,
    99.0,
    101.0,
    104.0,
    106.4,
    109.8,
    111.6,
    115.3,
    117.0,
    119.0,
    121.0,
    122.4,
    122.95,
]
