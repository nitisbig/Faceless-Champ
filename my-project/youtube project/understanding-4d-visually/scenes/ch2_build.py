"""CHAPTER 2 - BUILDING THE TESSERACT (S08-S12), 02:03.040 - 03:37.120.

S08  The drag                   point -> segment (x) -> square (y) -> cube (z, the camera turns 3D) -> tesseract (w:
                                the copy moves inward), one drag curve repeated; "tesseract" / "hypercube" labels
S09  The corners double         the build history as a row of five; x2 arcs; 1, 2, 4, 8, 16; corners = 2^n
S10  Counting edges, faces,     both copies + one new edge per moved corner: 2 x 4 + 4 = 12, 2 x 12 + 8 = 32;
     cells                      24 squares and 8 cells light; stats card (all counts computed from the rig)
S11  Corners are binary         4-digit labels; 0000 and 1111 assemble digit by digit; a 16-code table linked to the rig
S12  Measuring the diagonal     square -> cube -> tesseract diagonals with the Typst morph chain sqrt(2), sqrt(3),
                                sqrt(4) = 2; a two-edge ruler; ||v|| for 2 parts or 2,000

The build model: every vertex is a corner of {0,1}^4 scaled by the current drag extents e = (ex, ey, ez, ew).
Edges along an axis exist once that axis has been dragged. w is drawn with the same perspective as the
rest of the film (x' = d / (d - w) x), so the w copy shrinks inward.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import skia
import typmath
from components import hud
from components import tesseract as T4
from components.vector_slot import Slot, draw_stream, draw_vector
from cues import AUDIO, cue
from fx import Frame, chroma_kick, ease_io, ease_out, env, lerp, lin, mix, motion_blur, pulse, smooth
from space import Spline, orbit
from theme import THEME, TOKENS, H, W
from typmath import tc

START = cue(365)  # 123.04 "So let's build a four-dimensional object"
END = cue(630)  # 217.12 "But how would we actually see"

C = {i: cue(i) for i in range(365, 631)}
T = {
    "move": C[372],
    "new_dir": C[380],
    "drag_x": C[384],
    "two_ends": C[394],
    "drag_y": C[399],
    "four": C[407],
    "drag_z": C[412],
    "eight": C[420],
    "drag_w": C[423],
    "w": C[427],
    "cannot": C[431],
    "tesseract": C[437],
    "hypercube": C[439],
    "s09": C[440],
    "copies": C[442],
    "double": C[448],
    "counts": [C[449], C[450], C[451], C[452], C[453]],
    "n1": C[457],
    "two_pow": C[460],
    "power_n": C[463],
    "s10": C[466],
    "both": C[474],
    "add_one": C[480],
    "every_corner": C[485],
    "moved": C[487],
    "eq1": [C[491], C[492], C[493], C[494], C[495], C[497], C[498]],
    "tess": C[501],
    "eq2": [C[503], C[504], C[505], C[506], C[507], C[509], C[510]],
    "faces": C[515],
    "cells": C[519],
    "walls": C[523],
    "s11": C[524],
    "coords": C[525],
    "zeros": C[531],
    "zero4": [C[534], C[535], C[536], C[537]],
    "one4": [C[541], C[542], C[543], C[544]],
    "opposite": C[547],
    "sixteen": C[549],
    "corners16": C[551],
    "s12": C[553],
    "pythagoras": C[559],
    "one_plus_one": C[571],
    "root2": C[580],
    "cube": C[582],
    "adds": C[583],
    "root3": C[592],
    "tesseract2": C[594],
    "adds2": C[595],
    "root4": C[603],
    "exactly": C[604],
    "two_word": C[605],
    "length": C[607],
    "squared": C[620],
    "two_parts": C[625],
    "thousand": C[629],
}

FOCAL = 1500.0
S = 2.4  # world size of one unit edge
D4 = 2.0 * S  # w-camera distance for the perspective projection
DRAG = 0.9  # every drag uses the same curve


def drag(t, t0, dur=DRAG):
    """The drag curve: ease in-out with a tiny overshoot, 0 -> 1."""
    u = lin(t, t0, t0 + dur)
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    base = ease_io(u)
    return base + 0.06 * math.sin(math.pi * u) ** 2 * (u > 0.6) * (u - 0.6) / 0.4


# ------------------------------------------------------------------ the build model


def rig4(e, xw=0.0, zw=0.0, center=True):
    """16 x 4 points of the partially built hypercube (w copy dragged toward -w), plus validity masks."""
    e = np.asarray(e, float)
    p = T4.V * e
    if center:
        p = p - e / 2
    p = p * np.array([S, S, S, -S])
    if xw or zw:
        p = p @ T4.rotation(("xw", xw), ("zw", zw)).T
    valid_v = np.all((T4.V == 0) | (e > 1e-3), axis=1)
    valid_e = np.array([valid_v[i] and valid_v[j] and e[a] > 1e-3 for i, j, a in T4.EDGES])
    return p, valid_v, valid_e


def project(p4):
    p3, f = T4.project_persp(p4, D4)
    return p3, f


def draw_rig(
    fr,
    cam,
    e,
    alpha=1.0,
    xw=0.0,
    zw=0.0,
    width=2.4,
    glow=0.7,
    edge_fn=None,
    vertex=1.0,
    pops=None,
    center=True,
    scale=1.0,
    offset=(0.0, 0.0, 0.0),
):
    """Draw the built shape. edge_fn(k, i, j, axis) -> (alpha_mult, draw_fraction, color or None)."""
    if alpha <= 0.003:
        return None
    p4, vv, ve = rig4(e, xw, zw, center)
    p3, _ = project(p4)
    p3 = p3 * scale + np.asarray(offset, float)
    xs, ys, z = cam.project(p3)
    if np.any(z <= 0.05):
        return None
    near = (z.max() - z) / max(1e-6, z.max() - z.min()) if z.max() > z.min() else np.ones(16)
    order = sorted(range(32), key=lambda k: -(z[T4.EDGES[k][0]] + z[T4.EDGES[k][1]]))
    for k in order:
        if not ve[k]:
            continue
        i, j, a = T4.EDGES[k]
        am, frac, color = (1.0, 1.0, None) if edge_fn is None else edge_fn(k, i, j, a)
        if am * alpha <= 0.003 or frac <= 0:
            continue
        x1, y1 = lerp(xs[i], xs[j], frac), lerp(ys[i], ys[j], frac)
        d = 0.55 + 0.45 * (near[i] + near[j]) / 2
        fr.line(xs[i], ys[i], x1, y1, color or TOKENS["xyzw"[a]], width, alpha * am * d, glow=glow)
    if vertex > 0:
        for v in range(16):
            if vv[v]:
                pv = 0.0 if pops is None else pops[v]
                fr.glow_dot(
                    xs[v],
                    ys[v],
                    3.5 + 2.0 * near[v] + 6.0 * pv,
                    "#ffffff" if pv > 0.02 else "ink",
                    alpha * vertex * (0.6 + 0.4 * near[v]) + pv,
                    0.6 + 1.2 * pv,
                )
    return xs, ys, z, vv


def shape_e(t):
    """Drag extents during S08."""
    return np.array(
        [
            drag(t, T["drag_x"]),
            drag(t, T["drag_y"] - 0.1),
            drag(t, T["drag_z"] - 0.05),
            drag(t, T["drag_w"] + 0.35, 1.3),
        ]
    )


def xw_angle(t):
    return 0.22 * max(0.0, t - T["hypercube"]) * smooth(lin(t, T["hypercube"], T["hypercube"] + 1.0))


# ------------------------------------------------------------------ S08: the drag

CAM08 = Spline(
    [  # time, target(3), dist, elev, azim
        (START, (0, 0, 0), 6.4, 0.0, 0.0),  # close while the shape is flat
        (T["drag_z"] - 0.9, (0, 0, 0), 6.6, 0.0, 0.0),
        (T["drag_z"] + 0.9, (0, 0, 0), 9.6, 0.36, -0.62),
        (T["tesseract"], (0, 0, 0), 9.8, 0.30, -0.50),
        (T["s09"], (0, 0, 0), 10.0, 0.28, -0.42),
    ]
)


def cam08(t, center=(960.0, 520.0), dist_scale=1.0):
    v = CAM08(t)
    return orbit(v[:3], v[3] * dist_scale, v[4], v[5], focal=FOCAL, center=center)


def corner_pops(t, t0, n_axes, gap=0.09):
    """Sequential flash of the valid corners of an n-dimensional stage."""
    out = np.zeros(16)
    valid = [v for v in range(16) if np.all(T4.V[v, n_axes:] == 0)]
    for k, v in enumerate(valid):
        out[v] = pulse(t, t0 + gap * k, 0.35)
    return out


def draw_s08(fr, t):
    a = 1 - smooth(lin(t, T["s09"] - 0.4, T["s09"] + 0.4))
    if a <= 0.003:
        return
    e = shape_e(t)
    cam = cam08(t)
    # 08A: the breathing point and a ghost arrow hinting a direction
    if e[0] <= 1e-3:
        r = 6 + 1.5 * math.sin(t * 3.0)
        fr.glow_dot(960, 520, r, "ink", 1.0, 1.4)
        ga = env(t, T["move"] - 0.1, T["new_dir"] + 0.4, 0.4, 0.5)
        if ga > 0:
            ang = -0.5 + 0.35 * math.sin((t - T["move"]) * 1.4)
            hud.arrow(
                fr,
                975,
                520,
                975 + 170 * math.cos(ang),
                520 + 170 * math.sin(ang),
                "muted",
                2.0,
                0.7 * ga,
                glow=0.2,
                dashed=True,
            )
        return
    pops = np.zeros(16)
    pops += corner_pops(t, T["two_ends"] - 0.05, 1, 0.2)
    pops += corner_pops(t, T["four"] - 0.05, 2)
    pops += corner_pops(t, T["eight"] - 0.05, 3, 0.07)
    shimmer = env(t, T["cannot"] - 0.1, T["tesseract"] - 0.3, 0.3, 0.4)

    def edges(k, i, j, axis):
        if axis == 3 and shimmer > 0:
            return 0.65 + 0.35 * math.sin(t * 31.0 + k), 1.0, None
        return 1.0, 1.0, None

    born = pulse(t, T["tesseract"] - 0.05, 1.0)
    out = draw_rig(
        fr, cam, e, a, xw=xw_angle(t), width=2.6 + 1.0 * born, glow=0.8 + 1.0 * born, edge_fn=edges, pops=pops
    )
    if out is None:
        return
    xs, ys, _, _ = out
    _sweep_fx(fr, cam, t, e, xs, ys, a)
    # 08E: the dashed w arrow follows the corner that the copy drags inward
    wa = env(t, T["drag_w"] - 0.15, T["cannot"] + 0.4, 0.3, 0.5) * a
    if wa > 0:
        i_out, i_in = T4.index_of("1110"), T4.index_of("1111")
        p_full, _, _ = rig4(np.array([1, 1, 1, 1.0]))
        q3, _ = project(p_full)
        qx, qy, _ = cam.project(q3[[i_out, i_in]])
        hud.arrow(fr, qx[0] + 30, qy[0] - 30, qx[1] + 12, qy[1] - 12, "w", 2.6, wa, glow=0.9, dashed=True)
        fr.text("w", qx[0] + 46, qy[0] - 40, "italic", 44, 500, "w", wa, glow=0.5)
    la = smooth(lin(t, T["tesseract"] - 0.05, T["tesseract"] + 0.5)) * a
    fr.text("tesseract", 960, 950, "display", 72, 600, "ink", la, tracking=0.04, glow=0.3)
    ha = smooth(lin(t, T["hypercube"] - 0.05, T["hypercube"] + 0.5)) * a
    fr.text("hypercube", 960, 1010, "italic", 40, 500, "w", ha, glow=0.3)
    fr.chroma(chroma_kick(t, T["tesseract"], 6.0))


def _sweep_fx(fr, cam, t, e, xs, ys, a):
    """Sparks behind the dragged point (x) and the orange sheen of the swept square (y)."""
    ux = lin(t, T["drag_x"], T["drag_x"] + DRAG)
    if 0 < ux < 1:
        x1, y1 = xs[T4.index_of("1000")], ys[T4.index_of("1000")]
        rng = np.random.default_rng(int(t * 30))
        for k in range(8):
            age = rng.uniform(0, 1)
            fr.glow_dot(
                x1 - 60 * age + rng.normal(0, 4),
                y1 + rng.normal(0, 6),
                2.0 * (1 - age),
                "x",
                a * (1 - age) * math.sin(math.pi * ux),
                1.2,
            )
        fr.glow_dot(x1, y1, 6, "#ffffff", a, 1.6)
    uy = lin(t, T["drag_y"] - 0.1, T["drag_y"] + DRAG + 0.5)
    if 0 < uy < 1:
        quad = [T4.index_of(b) for b in ("0000", "1000", "1100", "0100")]
        p = skia.Path()
        p.addPoly([skia.Point(float(xs[v]), float(ys[v])) for v in quad], True)
        fr.path_fill(p, "y", 0.22 * a * math.sin(math.pi * uy), glow=0.25)


# ------------------------------------------------------------------ S09: the corners double

ROW_X = (300.0, 630.0, 960.0, 1290.0, 1620.0)
ROW_Y = 470.0
STAGES = [np.array(v, float) for v in ((0, 0, 0, 0), (1, 0, 0, 0), (1, 1, 0, 0), (1, 1, 1, 0), (1, 1, 1, 1))]


ROW_DIST = (15.5, 15.5, 16.0, 21.0, 24.0)


def row_cam(i, t, dist=None):
    azim = (-0.55 if i >= 3 else 0.0) + 0.12 * math.sin(0.5 * t + i)
    elev = 0.30 if i >= 3 else 0.0
    return orbit((0, 0, 0), dist or ROW_DIST[i], elev, azim, focal=FOCAL, center=(ROW_X[i], ROW_Y))


def draw_s09(fr, t):
    a = env(t, T["s09"] - 0.3, T["s10"] + 0.3, 0.6, 0.5)
    if a <= 0.003:
        return
    move = ease_io(lin(t, T["s09"] - 0.4, T["s09"] + 0.5))  # the big tesseract flies into slot 5
    for i, e in enumerate(STAGES):
        sa = a if i == 4 else a * smooth(lin(t, T["s09"] - 0.1 + 0.08 * i, T["s09"] + 0.4 + 0.08 * i))
        cam = row_cam(i, t, lerp(10.0, ROW_DIST[4], move) if i == 4 else None)
        if i == 4:
            cam.cx = lerp(960.0, ROW_X[4], move)
            cam.cy = lerp(520.0, ROW_Y, move)
        flash = pulse(t, T["counts"][i] - 0.05, 0.6)
        pops = np.zeros(16)
        if flash > 0:
            pops[np.all(T4.V[:, i:] == 0, axis=1)] = flash
        if i == 0:
            fr.glow_dot(ROW_X[0], ROW_Y, 7 + 6 * flash, "#ffffff" if flash > 0.05 else "ink", sa, 1.2 + flash)
        else:
            # "copies": the previous stage, ghosted at both copy positions that make this shape
            ga = env(t, T["copies"] - 0.1, T["double"] + 0.2, 0.3, 0.5)
            if ga > 0:
                prev = STAGES[i - 1]
                half = (e - prev)[:3] * S / 2
                if i == 4:  # the w copy: same centre, smaller
                    draw_rig(fr, cam, prev, 0.35 * ga * sa, width=1.6, glow=0.2, vertex=0.0, scale=D4 / (D4 + S / 2))
                else:
                    for sign in (-1, 1):
                        draw_rig(
                            fr, cam, prev, 0.35 * ga * sa, width=1.6, glow=0.2, vertex=0.0, offset=sign * half * 1.25
                        )
            draw_rig(
                fr, cam, e, sa, xw=xw_angle(t) if i == 4 else 0.0, width=2.2, glow=0.6, pops=0.45 * pops, vertex=0.8
            )
    # x2 arcs
    da = smooth(lin(t, T["double"] - 0.1, T["double"] + 0.5)) * a
    if da > 0:
        for i in range(4):
            x0, x1 = ROW_X[i] + 40, ROW_X[i + 1] - 40
            p = skia.Path()
            p.moveTo(x0, 300)
            p.quadTo((x0 + x1) / 2, 230, x1, 300)
            fr.path_stroke(p, "muted", 1.6, da)
            hud.arrow_head(fr, (x0 + x1) / 2 + 60, 258, x1, 300, "muted", da, 12, 0.0)
            typmath.draw(fr, "times 2", (x0 + x1) / 2, 215, 34, color="ink", alpha=da)
    # 1, 2, 4, 8, 16 -> 2^0 ... 2^4
    relabel = smooth(lin(t, T["two_pow"] - 0.1, T["two_pow"] + 0.5))
    for i in range(5):
        na = smooth(lin(t, T["counts"][i] - 0.1, T["counts"][i] + 0.2)) * a
        flash = pulse(t, T["counts"][i] - 0.05, 0.6) + (0.8 * pulse(t, T["counts"][4] - 0.05, 1.0) if i == 4 else 0)
        n_corners = int(np.all(T4.V[:, i:] == 0, axis=1).sum())  # computed: 2^i
        typmath.number(
            fr, str(n_corners), ROW_X[i], 660, 64 * (1 + 0.15 * flash), "ink", na * (1 - relabel), glow=0.3 + flash
        )
        typmath.draw(fr, f"2^{i}", ROW_X[i], 660, 60, color="w" if i == 4 else "ink", alpha=na * relabel, glow=0.3)
    fa = smooth(lin(t, T["n1"] - 0.6, T["n1"])) * a
    if fa > 0:
        g = pulse(t, T["n1"] - 0.05, 0.6) + pulse(t, T["power_n"] - 0.05, 0.8)
        typmath.draw(fr, f'"corners" = 2^{tc("w", "n")}', 960, 860, 64, alpha=fa, glow=0.2 + 1.0 * g)


# ------------------------------------------------------------------ S10: counting edges, faces and cells

CAM10 = Spline(
    [
        (T["s10"], (0, 0, 0), 10.0, 0.30, -0.62),
        (T["tess"], (0, 0, 0), 10.4, 0.30, -0.50),
        (T["s11"], (0, 0, 0), 10.8, 0.28, -0.40),
    ]
)


def cam10(t, cx=900.0):
    v = CAM10(t)
    return orbit(v[:3], v[3], v[4], v[5], focal=FOCAL, center=(cx, 470.0))


def s10_e(t):
    return np.array([1.0, 1.0, drag(t, T["s10"] + 0.5, 1.2), drag(t, T["tess"] - 0.3, 1.2)])


def eq_tokens(fr, t, expr, cx, cy, size, times, alpha):
    """A Typst equation whose glyphs appear one by one; glyph i appears at times[i] (last time repeats)."""
    gs, _ = typmath.glyphs(expr)
    am = {}
    for i in range(len(gs)):
        tt = times[min(i, len(times) - 1)]
        am[i] = smooth(lin(t, tt - 0.12, tt + 0.18))
    typmath.draw(fr, expr, cx, cy, size, alpha=alpha, alphas=am)


def draw_s10(fr, t):
    a = env(t, T["s10"] - 0.4, T["s11"] + 0.6, 0.5, 0.01)
    if a <= 0.003 or t > T["s11"] + 0.6:
        return
    cam = cam10(t, cx=lerp(900.0, 1200.0, ease_io(lin(t, T["walls"], T["s11"] + 0.6))))
    e = s10_e(t)
    both = env(t, T["both"] - 0.1, T["add_one"] + 0.3, 0.3, 0.5)
    tess_glow = env(t, T["eq2"][0] - 0.2, T["eq2"][3] + 0.2, 0.3, 0.4)
    conn_z = [k for k, (i, j, ax) in enumerate(T4.EDGES) if ax == 2 and T4.V[i, 3] == 0]
    conn_w = [k for k, (i, j, ax) in enumerate(T4.EDGES) if ax == 3]

    def edges(k, i, j, axis):
        if axis == 2 and T4.V[i, 3] == 0:  # the cube's 4 new edges, one per moved corner
            n = conn_z.index(k)
            t0 = T["add_one"] + 0.45 * n
            return 1.0, ease_out(lin(t, t0, t0 + 0.4)), None
        if axis == 3:  # the tesseract's 8 new edges
            n = conn_w.index(k)
            t0 = T["eq2"][3] - 0.1 + 0.08 * n
            return 1.0, ease_out(lin(t, t0, t0 + 0.35)), None
        if T4.V[i, 3] == 0 and T4.V[j, 3] == 0 and axis < 2 and both > 0:
            return 1.0, 1.0, mix(TOKENS["xyzw"[axis]], "#ffffff", 0.7 * both)
        if axis < 3 and tess_glow > 0:
            return 1.0, 1.0, mix(TOKENS["xyzw"[axis]], "#ffffff", 0.6 * tess_glow)
        return 1.0, 1.0, None

    p4, vv, ve = rig4(e)
    p3, _ = project(p4)
    # 10D: glass squares and cells (under the edges)
    sq_a = env(t, T["faces"] - 0.2, T["cells"], 0.2, 0.4) * a
    if sq_a > 0:
        for n in range(24):
            u = smooth(lin(t, T["faces"] + 0.045 * n, T["faces"] + 0.045 * n + 0.25))
            if u > 0:
                T4.fill_square(fr, cam, p3, n, "ink", 0.07 * u * sq_a)
    for n in range(8):
        t0 = T["cells"] + 0.14 * n
        ca = env(t, t0 - 0.05, t0 + 0.55, 0.1, 0.35) * a
        if ca > 0:
            axis, val, _ = T4.CELLS[n]
            T4.fill_cell(fr, cam, p3, n, TOKENS["xyzw"[axis]], 0.16 * ca, stroke=0.6 * ca)
    draw_rig(fr, cam, e, a, edge_fn=edges, width=2.4, glow=0.7)
    # counters, computed from what is visible
    visible = _visible_edges(t, e, conn_z, conn_w)
    label, value = "edges", str(visible)
    if t > T["faces"] - 0.2:
        label, value = "faces", str(min(24, int(max(0.0, (t - T["faces"]) / 0.045 + 1))))
    if t > T["cells"] - 0.05:
        label, value = "cells", str(min(len(T4.CELLS), int(max(0.0, (t - T["cells"]) / 0.14 + 1))))
    ca = env(t, T["both"] - 0.3, T["s11"] + 0.3, 0.4, 0.4) * a
    hud.readout(fr, 1560, 150, label, value, "ink", ca, size=36)
    # the edge equations, glyph by glyph on the spoken words
    e_sq = 4  # edges of a square
    v_sq = int(np.all(T4.V[:, 2:] == 0, axis=1).sum())
    e_cube = 2 * e_sq + v_sq
    v_cube = int(np.all(T4.V[:, 3:] == 0, axis=1).sum())
    e_tess = 2 * e_cube + v_cube
    assert e_tess == len(T4.EDGES)
    e1 = env(t, T["eq1"][0] - 0.3, T["eq2"][0] - 0.3, 0.3, 0.4) * a
    if e1 > 0:
        eq_tokens(
            fr,
            t,
            f"2 times {e_sq} + {tc('z', str(v_sq))} = {e_cube}",
            900,
            930,
            66,
            [T["eq1"][0], T["eq1"][1], T["eq1"][2], T["eq1"][3], T["eq1"][4], T["eq1"][5], T["eq1"][6]],
            e1,
        )
    e2 = env(t, T["eq2"][0] - 0.2, T["faces"] - 0.2, 0.3, 0.4) * a
    if e2 > 0:
        eq_tokens(
            fr,
            t,
            f"2 times {e_cube} + {tc('w', str(v_cube))} = {e_tess}",
            900,
            930,
            66,
            [
                T["eq2"][0],
                T["eq2"][1],
                T["eq2"][2],
                T["eq2"][2],
                T["eq2"][3],
                T["eq2"][4],
                T["eq2"][5],
                T["eq2"][6],
                T["eq2"][6],
            ],
            e2,
        )
    sa = smooth(lin(t, T["walls"] - 0.2, T["walls"] + 0.4)) * env(t, T["s10"], T["s11"] + 0.6, 0.1, 0.4)
    if sa > 0:
        hud.glass_card(fr, 1340, 880, 470, 100, sa)
        stats = f"V {len(T4.V)} · E {len(T4.EDGES)} · F {len(T4.SQUARES)} · C {len(T4.CELLS)}"
        hud.tabular(fr, stats, 1575, 942, 32, "ink", sa)


def _visible_edges(t, e, conn_z, conn_w):
    _, _, ve = rig4(e)
    n = 0
    for k, (i, j, a) in enumerate(T4.EDGES):
        if not ve[k]:
            continue
        if k in conn_z:
            t0 = T["add_one"] + 0.45 * conn_z.index(k)
            n += t >= t0 + 0.3
        elif k in conn_w:
            t0 = T["eq2"][3] - 0.1 + 0.08 * conn_w.index(k)
            n += t >= t0 + 0.3
        else:
            n += 1
    return n


# ------------------------------------------------------------------ S11: corners are binary numbers


def cam11(t):
    nudge = env(t, T["zero4"][0] - 0.4, T["one4"][3] + 0.6, 0.6, 0.8)
    v = CAM10(min(t, T["s11"]))
    return orbit(
        (0.0, 0.0, 0.0), v[3] - 1.2 * nudge, v[4], v[5] + 0.04 * (t - T["s11"]), focal=FOCAL, center=(1200.0, 470.0)
    )


def draw_s11(fr, t):
    a = env(t, T["s11"] - 0.2, T["s12"] + 0.2, 0.3, 0.6)
    if a <= 0.003:
        return
    cam = cam11(t)
    e = np.ones(4)
    out = draw_rig(fr, cam, e, a, width=2.2, glow=0.6, vertex=0.9)
    if out is None:
        return
    xs, ys, z, _ = out
    near = (z.max() - z) / max(1e-6, z.max() - z.min())
    i0, i1 = T4.index_of("0000"), T4.index_of("1111")
    focus = env(t, T["zero4"][0] - 0.3, T["sixteen"] + 0.1, 0.4, 0.5)
    shimmer = env(t, T["zeros"] - 0.1, T["zero4"][0] - 0.2, 0.2, 0.3)
    every = pulse(t, T["corners16"] - 0.05, 0.9)
    for v in range(16):
        bloom = smooth(lin(t, T["coords"] + 0.03 * v, T["coords"] + 0.03 * v + 0.4))
        if v in (i0, i1):
            continue
        sh = shimmer * (0.5 + 0.5 * math.sin(t * 17 + v * 2.3))
        la = a * bloom * (0.5 + 0.5 * near[v]) * (1 - 0.65 * focus) + every
        _label(fr, T4.label(v), xs[v] + 12, ys[v] - 12, 24 + 8 * near[v], min(1.0, la), glow=0.5 * sh + every)
    for v, times in ((i0, T["zero4"]), (i1, T["one4"])):
        bits = T4.label(v)
        base = a * smooth(lin(t, T["coords"] + 0.03 * v, T["coords"] + 0.03 * v + 0.4))
        x0 = xs[v] + (16 if v == i1 else -150)
        for k, ch in enumerate(bits):
            big = smooth(lin(t, times[k] - 0.1, times[k] + 0.2))
            size = lerp(26, 44, big)
            g = pulse(t, times[k] - 0.05, 0.5)
            fr.text(
                ch,
                x0 + k * size * 0.66,
                ys[v] - 14,
                "sans",
                size,
                700,
                "xyzw"[k],
                min(1.0, base + every),
                align="left",
                glow=0.3 + g + every,
            )
    da = env(t, T["opposite"] - 0.1, T["s12"], 0.4, 0.5) * a
    if da > 0:
        fr.dashed([xs[i0], xs[i1]], [ys[i0], ys[i1]], "ink", 1.8, 0.7 * da, glow=0.4, on=10, off=8)
    _draw_code_table(fr, t, xs, ys, a)


def _label(fr, bits, x, y, size, alpha, glow=0.0):
    for k, ch in enumerate(bits):
        fr.text(ch, x + k * size * 0.62, y, "sans", size, 600, "xyzw"[k], alpha, align="left", glow=glow)


def _draw_code_table(fr, t, xs, ys, a):
    ta = smooth(lin(t, T["sixteen"] - 0.15, T["sixteen"] + 0.4)) * a
    if ta <= 0.003:
        return
    every = pulse(t, T["corners16"] - 0.05, 0.9)
    hud.glass_card(fr, 90, 230, 520, 500, ta)
    for v in range(16):
        r, c = divmod(v, 4)
        cx, cy = 150 + c * 120, 300 + r * 110
        u = smooth(lin(t, T["sixteen"] + 0.03 * v, T["sixteen"] + 0.03 * v + 0.3)) * ta
        _label(fr, T4.label(v), cx - 24, cy + 10, 28, u, glow=0.2 + every)
        if u > 0:
            fr.line(cx + 50, cy, xs[v], ys[v], "muted", 0.8, 0.22 * u)


# ------------------------------------------------------------------ S12: measuring the diagonal

SQ_C = np.array([560.0, 560.0])
UNIT_PX = 300.0
F_X, F_Y = 1420.0, 430.0


def chain_exprs():
    one = {k: tc(k, "1^2") for k in "xyzw"}
    return {
        "f1": f"sqrt({one['x']} + {one['y']})",
        "f2": "sqrt(2)",
        "f3": f"sqrt({one['x']} + {one['y']} + {one['z']})",
        "f4": "sqrt(3)",
        "f5": f"sqrt({one['x']} + {one['y']} + {one['z']} + {one['w']})",
        "f6": "sqrt(4)",
        "f7": "2",
    }


def cam12(t):
    turn = ease_io(lin(t, T["cube"] - 0.1, T["cube"] + 0.9))
    back = ease_io(lin(t, T["tesseract2"] - 0.1, T["tesseract2"] + 1.0))  # room for the w copy
    return orbit((0, 0, 0), 9.0 + 1.4 * back, 0.30 * turn, -0.62 * turn, focal=FOCAL, center=(SQ_C[0], SQ_C[1]))


def draw_s12(fr, t):
    a = env(t, T["s12"] + 0.2, END + 0.5, 0.5, 0.01)
    if a <= 0.003:
        return
    out_shapes = 1 - smooth(lin(t, T["length"] - 0.3, T["length"] + 0.4))
    cam = cam12(t)
    e = np.array([1.0, 1.0, drag(t, T["cube"] - 0.05), drag(t, T["tesseract2"] - 0.05, 1.1)])
    sa = smooth(lin(t, T["pythagoras"] - 0.3, T["pythagoras"] + 0.3)) * a * out_shapes
    if sa > 0:
        res = draw_rig(fr, cam, e, sa, width=2.6, glow=0.7)
        if res is not None:
            xs, ys, _, _ = res
            # the diagonal of the current stage, from 0000 to the far corner
            n = 2 + (e[2] > 0.999) + (e[3] > 0.999)
            far = T4.index_of("1" * n + "0" * (4 - n))
            t0 = {2: T["pythagoras"] + 0.3, 3: T["cube"] + 0.9, 4: T["tesseract2"] + 1.1}[n]
            u = ease_out(lin(t, t0, t0 + 0.6))
            i0 = T4.index_of("0000")
            x1, y1 = lerp(xs[i0], xs[far], u), lerp(ys[i0], ys[far], u)
            fr.line(xs[i0], ys[i0], x1, y1, "#ffffff", 3.2, sa, glow=1.3)
            if n == 2:  # legs and the right angle
                la = smooth(lin(t, T["pythagoras"] + 0.4, T["pythagoras"] + 0.9)) * sa * (1 - e[2])
                i_x = T4.index_of("1000")
                typmath.draw(fr, "1", (xs[i0] + xs[i_x]) / 2, (ys[i0] + ys[i_x]) / 2 + 40, 44, color="x", alpha=la)
                typmath.draw(fr, "1", xs[i_x] + 36, (ys[i_x] + ys[far]) / 2, 44, color="y", alpha=la)
                s = 26
                fr.poly([xs[i_x] - s, xs[i_x] - s, xs[i_x]], [ys[i_x], ys[i_x] - s, ys[i_x] - s], "ink", 1.6, la)
    # the Typst morph chain
    F = chain_exprs()
    steps = [  # (morph start, from, to)
        (T["one_plus_one"] - 0.15, None, "f1"),
        (T["root2"] - 0.15, "f1", "f2"),
        (T["adds"] - 0.1, "f2", "f3"),
        (T["root3"] - 0.15, "f3", "f4"),
        (T["adds2"] - 0.1, "f4", "f5"),
        (T["root4"] - 0.15, "f5", "f6"),
        (T["exactly"] + 0.25, "f6", "f7"),
    ]
    fa = a * out_shapes
    cur = None
    for k, (t0, frm, to) in enumerate(steps):
        nxt = steps[k + 1][0] if k + 1 < len(steps) else 1e9
        if t0 <= t < nxt:
            cur = (t0, frm, to)
    if cur is not None and fa > 0:
        t0, frm, to = cur
        u = lin(t, t0, t0 + 0.55)
        big = to == "f7"
        size_to = 150.0 if big else 70.0
        if frm is None:
            typmath.draw(fr, F[to], F_X, F_Y, 70, alpha=fa, reveal=lin(t, t0, t0 + 0.6))
        else:
            typmath.morph(
                fr,
                F[frm],
                F[to],
                u,
                F_X,
                F_Y,
                70,
                alpha=fa,
                glow=0.25 + (0.9 * pulse(t, t0 + 0.3, 0.8) if big else 0),
                b_size=size_to,
            )
        if big:
            fr.chroma(chroma_kick(t, t0 + 0.35, 7.0))
    # numeric readouts: computed lengths
    for n, (t_on, t_off) in ((2, (T["root2"] + 0.3, T["adds"] - 0.1)), (3, (T["root3"] + 0.3, T["adds2"] - 0.1))):
        ra = env(t, t_on, t_off, 0.3, 0.3) * fa
        if ra > 0:
            diag = np.linalg.norm(T4.V[T4.index_of("1" * n + "0" * (4 - n))] - T4.V[0])
            hud.readout(fr, F_X, F_Y + 120, "≈", f"{diag:.3f}", "ink", ra, size=34)
    # 12C ruler: the diagonal (length 2) against two unit edges laid end to end (true lengths, 1D)
    ra = smooth(lin(t, T["two_word"] - 0.2, T["two_word"] + 0.4)) * fa
    if ra > 0:
        L = 230.0
        y0 = F_Y + 210
        diag = np.linalg.norm(T4.V[15] - T4.V[0])
        fr.line(F_X - L * diag / 2, y0, F_X + L * diag / 2, y0, "#ffffff", 4.0, ra, glow=1.0)
        for k in range(2):
            u = ease_out(lin(t, T["two_word"] + 0.1 * k, T["two_word"] + 0.1 * k + 0.4))
            x0 = F_X - L + k * L
            fr.line(x0 + 4, y0 + 30, x0 + L * u - 4, y0 + 30, "x" if k == 0 else "y", 3.0, ra, glow=0.6)
            fr.line(x0, y0 + 20, x0, y0 + 40, "ink", 1.6, ra)
        fr.line(F_X + L, y0 + 20, F_X + L, y0 + 40, "ink", 1.6, ra)
        fr.text("diagonal", F_X - L - 24, y0 + 10, "sans", 30, 600, "muted", ra, align="right")
        fr.text("two edges", F_X - L - 24, y0 + 44, "sans", 30, 600, "muted", ra, align="right")
    # 12D: any vector, two parts or two thousand
    ga = smooth(lin(t, T["length"] - 0.1, T["length"] + 0.5)) * a
    if ga > 0:
        sq = pulse(t, T["squared"] - 0.05, 0.8)
        ng = pulse(t, T["thousand"] - 0.05, 0.9)
        expr = f"norm(v) = sqrt(v_1^2 + v_2^2 + dots.c + v_{tc('w', 'n')}^2)"
        typmath.draw(fr, expr, 720, 540, 70, alpha=ga, glow=0.2 + 0.8 * sq + 0.6 * ng)
        va = smooth(lin(t, T["two_parts"] - 0.2, T["two_parts"] + 0.3)) * a
        stream = lin(t, T["two_parts"] + 0.7, T["thousand"] + 0.5)
        if va > 0:
            draw_vector(
                fr,
                1560,
                600,
                [Slot("v_1", "ink"), Slot("v_2", "ink")],
                52,
                alpha=va * (1 - smooth(lin(stream, 0.0, 0.3))),
            )
            if stream > 0:
                draw_stream(fr, 1560, 880, 2000, reveal=stream, alpha=va, size=46, colors=("x", "y", "z", "w", "ink"))
                n = int(lerp(2, 2000, ease_io(stream)))
                hud.readout(fr, 1560, 975, "n =", f"{n:,}", "w", va, size=42)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_s08(fr, t)
    draw_s09(fr, t)
    draw_s10(fr, t)
    draw_s11(fr, t)
    draw_s12(fr, t)
    hud.eyebrow(fr, t, "02 · BUILD A TESSERACT", START + 0.15)
    fr.vignette(0.5)
    fr.grain(t, 0.045)
    return fr.finish()


def blur_weight(t):
    drags = [
        T["drag_x"],
        T["drag_y"] - 0.1,
        T["drag_z"] - 0.05,
        T["drag_w"] + 0.35,
        T["s09"] - 0.4,
        T["s10"] + 0.5,
        T["tess"] - 0.3,
    ]
    return max(env(t, d - 0.05, d + 1.3, 0.15, 0.3) for d in drags)


def draw(t, size):
    t = t + START
    return motion_blur(draw_one, t, size, weight=blur_weight(t))


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


OFFSET = START
DURATION = END - START
STILLS = [
    125.0,
    127.5,
    130.5,
    132.7,
    134.8,
    136.4,
    138.6,
    140.3,
    142.2,
    144.0,
    146.2,
    147.4,
    149.0,
    150.9,
    152.5,
    154.0,
    157.4,
    160.0,
    161.5,
    163.6,
    165.2,
    168.9,
    172.4,
    174.0,
    176.6,
    178.6,
    181.0,
    183.0,
    185.4,
    188.9,
    190.6,
    192.2,
    196.6,
    198.8,
    200.7,
    202.3,
    204.4,
    206.5,
    208.3,
    209.2,
    209.9,
    213.5,
    215.5,
    216.6,
]
