"""CHAPTER 5 - ROTATION (S21-S25), 05:41.280 - 07:13.760.

S21  The 2x2 rotation matrix        a point rotates by theta; [[cos, -sin], [sin, cos]] with each spoken term lit
S22  Rotation happens in a plane    a cube spins around a rod: z (height) is locked, x and y mix; the xy disc;
                                    the axis is what is left over
S23  Three planes, then six         xy, xz, yz discs; a 4x4 pair grid lights xy xz xw yz yw zw; n(n-1)/2 -> 4.3/2 -> 6
S24  The ZW rotation: inside out    the 4x4 ZW matrix assembles, the 2x2 docks into its zw block; the tesseract
                                    turns inside out; 32 edge-length bars stay at 1.000 (computed), R^T R = I, det 1;
                                    the floor shows the shadow of the shadow
S25  Double rotation                block-diagonal xy + zw; long trails; no axis left; only the centre stays still
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import skia
import typmath
from components import hud
from components import tesseract as T4
from components.matrix_plaque import draw_matrix
from cues import AUDIO, cue
from fx import Frame, chroma_kick, col, ease_io, ease_out, env, lerp, lin, motion_blur, pulse, smooth
from space import orbit, to_view
from theme import THEME, TOKENS, H, W

START = cue(976)  # 341.28 "Now let's make it move"
END = cue(1233)  # 433.76 "So is any of this real?"

C = {i: cue(i) for i in range(976, 1234)}
T = {
    "move": C[978],
    "rotating": C[984],
    "theta": C[988],
    "two_by": C[991],
    "matrix2": C[994],
    "eq1": (C[996], C[1007]),
    "cos1": (C[999], C[1002]),
    "sin1": (C[1003], C[1007]),
    "eq2": (C[1009], C[1020]),
    "sin2": (C[1012], C[1015]),
    "cos2": (C[1016], C[1020]),
    "s22": C[1021],
    "rotates": C[1028],
    "axis": C[1031],
    "but": C[1032],
    "spins": C[1036],
    "height": C[1042],
    "changes": C[1044],
    "other_two": C[1047],
    "mix": C[1050],
    "plane": C[1052],
    "plane_end": C[1057],
    "left": C[1061],
    "over": C[1065],
    "s23": C[1066],
    "three_planes": C[1072],
    "xy": C[1078],
    "xz": C[1079],
    "yz": C[1081],
    "four": C[1083],
    "six": C[1087],
    "pairs": [C[1088], C[1089], C[1090], C[1091], C[1092], C[1094]],
    "formula": C[1096],
    "n_start": C[1098],
    "n_end": C[1105],
    "sub": C[1106],
    "sub_end": C[1111],
    "eq6": C[1113],
    "ways": C[1114],
    "s24": C[1117],
    "zw": C[1121],
    "leaves": C[1125],
    "alone": C[1129],
    "mixes": C[1131],
    "w": C[1134],
    "same": C[1137],
    "sine": C[1140],
    "watch": C[1141],
    "inner": C[1145],
    "outer": C[1149],
    "pass": C[1154],
    "inside_out": C[1162],
    "nothing": C[1166],
    "orthogonal": C[1171],
    "det": C[1173],
    "det_end": C[1175],
    "edge": C[1178],
    "length": C[1181],
    "rigid": C[1185],
    "shadow": C[1197],
    "s25": C[1198],
    "double": C[1203],
    "xy2": C[1207],
    "zw2": C[1211],
    "same_time": C[1215],
    "no": C[1217],
    "over2": C[1221],
    "only": C[1224],
    "still": C[1228],
    "center": C[1232],
}
FOCAL = 1500.0
D4 = 3.0


def V3(p):
    return to_view(np.asarray(p, float))


# ------------------------------------------------------------------ S21: the 2x2 rotation matrix

O2 = np.array([620.0, 560.0])
U2 = 230.0
P0 = np.array([1.0, 0.4])


def theta21(t):
    return math.radians(30) * ease_io(lin(t, T["rotating"] - 0.1, T["theta"] + 0.6)) + 0.12 * max(0.0, t - T["matrix2"])


def draw_s21(fr, t):
    a = env(t, START - 0.01, T["s22"] + 0.4, 0.01, 0.5)
    if a <= 0.003:
        return
    # 21A: the rig twitches, then flattens into the plane
    tw = 1 - smooth(lin(t, T["move"] + 0.3, T["move"] + 1.1))
    if tw > 0.003:
        cam = orbit((0, 0, 0), 10.0, 0.30 * tw, -0.5 * tw, focal=FOCAL)
        R = T4.rotation(("zw", 0.6 * math.sin(6 * max(0.0, t - T["move"])) * (1 - tw)), ("xw", 0.2 * (t - START)))
        p3, _ = T4.project_persp(T4.C @ R.T, D4)
        world = T4.place(p3, scale=1.2) * np.array([1, tw, 1])
        T4.draw(fr, cam, world, a * tw, width=2.2, glow=0.6)
    pa = smooth(lin(t, T["move"] + 0.5, T["move"] + 1.2)) * a
    if pa <= 0.003:
        return
    ox, oy = O2
    hud.arrow(fr, ox - 260, oy, ox + 300, oy, "x", 2.2, pa, glow=0.5)
    hud.arrow(fr, ox, oy + 240, ox, oy - 290, "y", 2.2, pa, glow=0.5)
    fr.text("x", ox + 320, oy + 12, "italic", 40, 500, "x", pa)
    fr.text("y", ox + 18, oy - 300, "italic", 40, 500, "y", pa)
    th = theta21(t)
    c, s = math.cos(th), math.sin(th)
    p = np.array([c * P0[0] - s * P0[1], s * P0[0] + c * P0[1]])
    rx, ry = ox + U2 * P0[0], oy - U2 * P0[1]
    px, py = ox + U2 * p[0], oy - U2 * p[1]
    r = U2 * float(np.linalg.norm(P0))
    fr.circle(ox, oy, r, "muted", 1.0, 0.35 * pa)
    fr.line(ox, oy, rx, ry, "ink", 1.4, 0.35 * pa)
    hud.arrow(fr, ox, oy, px, py, "ink", 2.8, pa, glow=0.8)
    fr.glow_dot(px, py, 7, "#ffffff", pa, 1.4)
    # the theta arc
    a0 = math.atan2(P0[1], P0[0])
    arc = skia.Path()
    arc.addArc(skia.Rect.MakeLTRB(ox - 90, oy - 90, ox + 90, oy + 90), -math.degrees(a0), -math.degrees(th))
    fr.path_stroke(arc, "w", 2.4, pa, glow=0.6)
    mid = a0 + th / 2
    typmath.draw(fr, "theta", ox + 120 * math.cos(mid), oy - 120 * math.sin(mid), 40, color="w", alpha=pa)
    hud.readout(fr, ox, oy + 330, "θ", f"{math.degrees(th) % 360:5.1f}°", "w", pa, size=30)
    # projection guides: the components of the rotated point
    fr.dashed([px, px], [py, oy], "x", 1.4, 0.7 * pa, on=8, off=6)
    fr.dashed([px, ox], [py, py], "y", 1.4, 0.7 * pa, on=8, off=6)
    _draw_matrix2(fr, t, th, pa)


def _draw_matrix2(fr, t, th, a):
    ma = smooth(lin(t, T["two_by"] - 0.1, T["matrix2"] + 0.3)) * a
    if ma <= 0.003:
        return
    cells = [["cos theta", "-sin theta"], ["sin theta", "cos theta"]]
    lit = {
        (0, 0): env(t, *T["cos1"], 0.15, 0.3),
        (0, 1): env(t, *T["sin1"], 0.15, 0.3),
        (1, 0): env(t, *T["sin2"], 0.15, 0.3),
        (1, 1): env(t, *T["cos2"], 0.15, 0.3),
    }
    draw_matrix(
        fr,
        1400,
        330,
        cells,
        {k: "w" for k in lit},
        cell_w=190,
        cell_h=86,
        size=46,
        alpha=ma,
        glow={k: 1.2 * v for k, v in lit.items()},
    )
    eq1 = "x' = cos theta dot x - sin theta dot y"
    eq2 = "y' = sin theta dot x + cos theta dot y"
    typmath.draw(
        fr,
        eq1,
        1400,
        600,
        48,
        alpha=a,
        reveal=lin(t, T["eq1"][0] - 0.1, T["eq1"][1] + 0.1),
        glow=0.3 * env(t, T["eq1"][0], T["eq1"][1] + 0.4, 0.2, 0.4),
    )
    typmath.draw(
        fr,
        eq2,
        1400,
        700,
        48,
        alpha=a,
        reveal=lin(t, T["eq2"][0] - 0.1, T["eq2"][1] + 0.1),
        glow=0.3 * env(t, T["eq2"][0], T["eq2"][1] + 0.4, 0.2, 0.4),
    )


# ------------------------------------------------------------------ S22: rotation happens in a plane

CUBE = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float)


def spin22(t):
    return 0.9 * max(0.0, t - T["rotates"] + 0.2)


def cam22(t):
    return orbit(V3((0, 0, 0.2)), 10.5, 0.38, -0.5, focal=FOCAL, center=(820.0, 540.0))


def cube_pts(ang):
    c, s = math.cos(ang), math.sin(ang)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])  # a rotation in the xy plane: z (height) is untouched
    return CUBE @ R.T * 1.3


def draw_s22(fr, t):
    a = env(t, T["s22"] - 0.3, T["s23"] + 0.3, 0.5, 0.5)
    if a <= 0.003:
        return
    cam = cam22(t)
    ang = spin22(t)
    pts = cube_pts(ang)
    disc = smooth(lin(t, T["plane"] - 0.1, T["plane"] + 0.6)) * a
    if disc > 0:
        _plane_disc(fr, cam, np.eye(3)[0], np.eye(3)[1], 2.6, TOKENS["x"], TOKENS["y"], disc, z0=-1.3)
        for k in range(8):  # vertex trails: circles parallel to the disc
            rr = float(np.hypot(*pts[k, :2]))
            ring = np.array([[rr * math.cos(u), rr * math.sin(u), pts[k, 2]] for u in np.linspace(0, 2 * math.pi, 60)])
            xs, ys, _ = cam.project(V3(ring))
            fr.poly(xs, ys, "ink", 1.0, 0.25 * disc, close=True)
    rod = (0.55 - 0.4 * smooth(lin(t, T["left"] - 0.1, T["over"] + 0.2))) * a
    xs, ys, _ = cam.project(V3(np.array([[0, 0, -2.6], [0, 0, 2.6]])))
    fr.line(xs[0], ys[0], xs[1], ys[1], "ink", 2.0, rod, glow=0.3)
    la = smooth(lin(t, T["left"] - 0.1, T["over"] + 0.3)) * a
    fr.text("leftover", float(xs[1]) + 14, float(ys[1]) + 10, "sans", 26, 600, "muted", la, align="left")
    xs, ys, _ = cam.project(V3(pts))
    for i in range(8):
        for j in range(i + 1, 8):
            d = np.flatnonzero(CUBE[i] != CUBE[j])
            if len(d) == 1:
                fr.line(xs[i], ys[i], xs[j], ys[j], "xyz"[d[0]], 2.4, a, glow=0.6)
    # one vertex tracked: x and y mix, z holds
    v = 7
    fr.glow_dot(xs[v], ys[v], 7, "#ffffff", a, 1.4)
    ha = smooth(lin(t, T["but"] - 0.2, T["but"] + 0.4)) * a
    lock = env(t, T["height"] - 0.1, T["plane"], 0.2, 0.4)
    mixing = env(t, T["other_two"] - 0.1, T["plane"], 0.2, 0.4)
    centers = hud.coord_chip(
        fr,
        1500,
        300,
        [f"{pts[v, 0]:+.2f}", f"{pts[v, 1]:+.2f}", f"{pts[v, 2]:+.2f}"],
        list("xyz"),
        ha,
        size=40,
        flash={0: 0.6 * mixing, 1: 0.6 * mixing, 2: 0.8 * lock},
    )
    if lock > 0 and centers:
        lx = centers[2]
        fr.rrect(lx - 12, 360, 24, 18, 4, stroke="z", width=2.0, alpha=lock * ha)
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeLTRB(lx - 9, 346, lx + 9, 366), 180, 180)
        fr.path_stroke(arc, "z", 2.0, lock * ha)
        fr.text("height locked", lx, 410, "sans", 24, 600, "z", lock * ha)


def _plane_disc(fr, cam, u, v, r, ca, cb, a, z0=0.0, n=72):
    """A translucent two-colour disc spanned by math directions u, v (gradient from u's colour to v's)."""
    pts = np.array(
        [r * (math.cos(s) * u + math.sin(s) * v) + np.array([0, 0, z0]) for s in np.linspace(0, 2 * math.pi, n)]
    )
    xs, ys, _ = cam.project(V3(pts))
    p = skia.Path()
    p.addPoly([skia.Point(float(x), float(y)) for x, y in zip(xs, ys)], True)
    a0 = cam.project(V3((r * u + np.array([0, 0, z0]))[None]))
    b0 = cam.project(V3((r * v + np.array([0, 0, z0]))[None]))
    sh = skia.GradientShader.MakeLinear(
        [skia.Point(float(a0[0][0]), float(a0[1][0])), skia.Point(float(b0[0][0]), float(b0[1][0]))],
        [col(ca, 0.22 * a), col(cb, 0.22 * a)],
    )
    fr.c.drawPath(p, skia.Paint(AntiAlias=True, Shader=sh))
    sh2 = skia.GradientShader.MakeLinear(
        [skia.Point(float(a0[0][0]), float(a0[1][0])), skia.Point(float(b0[0][0]), float(b0[1][0]))],
        [col(ca, 0.9 * a), col(cb, 0.9 * a)],
    )
    fr.c.drawPath(p, skia.Paint(AntiAlias=True, Shader=sh2, Style=skia.Paint.kStroke_Style, StrokeWidth=2.0))


# ------------------------------------------------------------------ S23: three planes, then six

GRID_C = np.array([740.0, 500.0])
CELL = 112.0
PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]


def draw_s23(fr, t):
    a = env(t, T["s23"] - 0.3, T["s24"] + 0.5, 0.5, 0.5)
    if a <= 0.003:
        return
    to_grid = smooth(lin(t, T["four"] - 0.2, T["four"] + 0.6))
    if to_grid < 1:
        cam = orbit(V3((0.6, 0.6, 0.6)), 10.0, 0.35, -0.65, focal=FOCAL, center=(960.0, 540.0))
        ga = a * (1 - to_grid)
        for k, d in zip("xyz", np.eye(3)):
            hud.axis3d(fr, cam, V3((0, 0, 0)), V3(d * 3.2), k, k, 1.0, label_alpha=ga, width=2.4)
        for (i, j), tc0 in zip(((0, 1), (0, 2), (1, 2)), (T["xy"], T["xz"], T["yz"])):
            da = smooth(lin(t, tc0 - 0.1, tc0 + 0.4)) * ga
            if da > 0:
                _plane_disc(fr, cam, np.eye(3)[i], np.eye(3)[j], 2.0, TOKENS["xyz"[i]], TOKENS["xyz"[j]], da)
        la = env(t, T["three_planes"] - 0.1, T["four"], 0.3, 0.3) * ga
        typmath.draw(fr, '3 "axes" -> 3 "planes"', 960, 930, 46, alpha=la)
    if to_grid > 0:
        _draw_pair_grid(fr, t, a * to_grid)
        _draw_count(fr, t, a)


def _chip(fr, x, y, w, h, ca, cb, alpha, label=None, size=34, glow=0.0):
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h), 14, 14)
    sh = skia.GradientShader.MakeLinear(
        [skia.Point(x - w / 2, y), skia.Point(x + w / 2, y)], [col(ca, 0.30 * alpha), col(cb, 0.30 * alpha)]
    )
    fr.c.drawRRect(rr, skia.Paint(AntiAlias=True, Shader=sh))
    sh2 = skia.GradientShader.MakeLinear(
        [skia.Point(x - w / 2, y), skia.Point(x + w / 2, y)], [col(ca, alpha), col(cb, alpha)]
    )
    fr.c.drawRRect(rr, skia.Paint(AntiAlias=True, Shader=sh2, Style=skia.Paint.kStroke_Style, StrokeWidth=2.0))
    if glow > 0:
        p = skia.Path()
        p.addRRect(rr)
        fr.glow_used = True
        fr.g.drawPath(p, fr._stroke(ca, 10.0, alpha * glow))
    if label:
        if label.isalpha() and len(label) > 1:  # Typst reads "xy" as one variable name: space the letters
            label = " ".join(label)
        typmath.draw(fr, label, x, y, size, color="ink", alpha=alpha)


def _draw_pair_grid(fr, t, a):
    gx, gy = GRID_C
    for k, name in enumerate("xyzw"):
        x = gx + (k - 1.5) * CELL
        y = gy + (k - 1.5) * CELL
        typmath.draw(fr, name, x, gy - 2.2 * CELL, 44, color=name, alpha=a)
        typmath.draw(fr, name, gx - 2.2 * CELL, y, 44, color=name, alpha=a)
    for r in range(4):
        for c in range(4):
            x, y = gx + (c - 1.5) * CELL, gy + (r - 1.5) * CELL
            if r == c:
                fr.line(x - 26, y - 26, x + 26, y + 26, "muted", 1.6, 0.45 * a)
                fr.line(x - 26, y + 26, x + 26, y - 26, "muted", 1.6, 0.45 * a)
                continue
            i, j = min(r, c), max(r, c)
            k = PAIRS.index((i, j))
            lit = smooth(lin(t, T["pairs"][k] - 0.1, T["pairs"][k] + 0.3))
            mirror = 0.15 if r > c else 1.0
            ca, cb = TOKENS["xyzw"[i]], TOKENS["xyzw"[j]]
            fr.rrect(
                x - CELL / 2 + 6, y - CELL / 2 + 6, CELL - 12, CELL - 12, 12, stroke="line", width=1.0, alpha=0.5 * a
            )
            if lit > 0:
                g = pulse(t, T["pairs"][k] - 0.05, 0.6) if r < c else 0.0
                _chip(
                    fr,
                    x,
                    y,
                    CELL - 18,
                    CELL - 18,
                    ca,
                    cb,
                    lit * mirror * a,
                    label="xyzw"[i] + "xyzw"[j] if r < c else None,
                    size=32,
                    glow=g,
                )


def _draw_count(fr, t, a):
    fa = smooth(lin(t, T["n_start"] - 0.2, T["n_start"] + 0.3)) * a
    if fa <= 0.003:
        return
    f1, f2, f3 = "(n(n - 1))/2", "(4 dot 3)/2", "6"
    x, y = 1480.0, 420.0
    if t < T["sub"] - 0.1:
        typmath.draw(fr, f1, x, y, 72, alpha=fa, reveal=lin(t, T["n_start"] - 0.1, T["n_end"] + 0.2))
    elif t < T["eq6"] - 0.15:
        typmath.morph(fr, f1, f2, lin(t, T["sub"] - 0.1, T["sub"] + 0.5), x, y, 72, alpha=fa)
    else:
        u = lin(t, T["eq6"] - 0.15, T["eq6"] + 0.35)
        typmath.morph(fr, f2, f3, u, x, y, 72, alpha=fa, glow=0.3 + pulse(t, T["eq6"], 0.8), b_size=130)
        fr.chroma(chroma_kick(t, T["eq6"] + 0.1, 6.0))
    ra = smooth(lin(t, T["ways"] - 0.1, T["ways"] + 0.4)) * a
    for k, (i, j) in enumerate(PAIRS):
        cx = x - 2.5 * 92 + k * 92
        u = smooth(lin(t, T["ways"] - 0.1 + 0.05 * k, T["ways"] + 0.25 + 0.05 * k)) * ra
        if u > 0:
            _chip(fr, cx, 640, 80, 56, TOKENS["xyzw"[i]], TOKENS["xyzw"[j]], u, label="xyzw"[i] + "xyzw"[j], size=26)


# ------------------------------------------------------------------ S24-S25: ZW rotation, double rotation


def omega(t):
    """Angular speed of the ZW rotation: starts on 'Watch', slows on 'nothing bends'."""
    on = smooth(lin(t, T["watch"] - 0.1, T["watch"] + 0.8))
    slow = smooth(lin(t, T["nothing"] - 0.1, T["nothing"] + 0.8))
    return on * lerp(0.95, 0.22, slow)


_GRID = np.linspace(0.0, 1.0, 241)


def theta_zw(t):
    t0 = T["watch"] - 0.2
    if t <= t0:
        return 0.0
    ts = t0 + (t - t0) * _GRID
    w = np.array([omega(x) for x in ts])
    return float(np.sum((w[1:] + w[:-1]) / 2) * (t - t0) / (len(_GRID) - 1))


def double_angle(t):
    return 0.85 * max(0.0, t - T["same_time"] + 0.2) * smooth(lin(t, T["same_time"] - 0.2, T["same_time"] + 0.6))


def R_at(t):
    R = T4.rot4("zw", theta_zw(t))
    if t > T["same_time"] - 0.3:
        d = double_angle(t)
        R = T4.rotation(("xy", d), ("zw", d)) @ R
    return R


def world_at(t, scale=1.25):
    p3, _ = T4.project_persp(T4.C @ R_at(t).T, D4)
    return T4.place(p3, scale=scale)


def cam24(t):
    back = ease_io(lin(t, T["rigid"] - 0.2, T["shadow"]))
    back2 = 1 - ease_io(lin(t, T["s25"] - 0.3, T["s25"] + 0.8))
    return orbit(
        (0, lerp(0.0, -0.6, back * back2), 0),
        lerp(10.0, 13.0, back * back2),
        lerp(0.28, 0.42, back * back2),
        -0.5 + 0.03 * (t - T["watch"]),
        focal=FOCAL,
        center=(900.0, 470.0),
    )


def plaque_state(t):
    """Matrix plaque: centre and size while it assembles, then docked small in the top-right corner."""
    dock = ease_io(lin(t, T["watch"] - 0.4, T["watch"] + 0.4))
    cx, cy = lerp(960.0, 1600.0, dock), lerp(520.0, 210.0, dock)
    k = lerp(1.0, 0.55, dock)
    return cx, cy, k


def draw_s24(fr, t):
    a = env(t, T["s24"] - 0.3, END + 0.5, 0.5, 0.01)
    if a <= 0.003:
        return
    # the zw chip enlarges
    za = env(t, T["s24"] - 0.2, T["leaves"] - 0.2, 0.3, 0.4) * a
    if za > 0:
        g = smooth(lin(t, T["zw"] - 0.1, T["zw"] + 0.4))
        _chip(
            fr,
            960,
            520,
            lerp(90, 260, g),
            lerp(60, 170, g),
            TOKENS["z"],
            TOKENS["w"],
            za,
            label="zw",
            size=lerp(30, 90, g),
            glow=0.6 * g,
        )
    ra = smooth(lin(t, T["watch"] - 0.6, T["watch"] + 0.2)) * a
    if ra > 0:
        cam = cam24(t)
        world = world_at(t)
        if t > T["rigid"] - 0.4:
            _floor_shadow(
                fr,
                cam,
                world,
                smooth(lin(t, T["rigid"] - 0.2, T["shadow"]))
                * ra
                * (1 - smooth(lin(t, T["s25"] - 0.3, T["s25"] + 0.5))),
            )
        inner_outer = env(t, T["inner"] - 0.2, T["nothing"] + 0.6, 0.3, 0.5) * ra
        if inner_outer > 0:
            n_in = [n for n, (ax, val, _) in enumerate(T4.CELLS) if ax == 3 and val == 0][0]
            n_out = [n for n, (ax, val, _) in enumerate(T4.CELLS) if ax == 3 and val == 1][0]
            T4.fill_cell(fr, cam, world, n_in, "w", 0.14 * inner_outer, stroke=0.5 * inner_outer)
            T4.fill_cell(fr, cam, world, n_out, "ink", 0.06 * inner_outer)
        fast = env(t, T["watch"], T["nothing"] + 0.5, 0.3, 0.6)
        if fast > 0:
            T4.draw_trails(fr, cam, world_at, t, span=0.35, steps=12, alpha=0.4 * fast * ra, width=1.5, color="w")
        dbl = smooth(lin(t, T["same_time"] - 0.2, T["same_time"] + 0.6)) * ra
        if dbl > 0:
            T4.draw_trails(fr, cam, world_at, t, span=1.6, steps=36, alpha=0.5 * dbl, width=1.4, color="ink")
        hero = pulse(t, T["inside_out"] - 0.05, 1.0)
        T4.draw(fr, cam, world, ra, width=2.6 + hero, glow=0.8 + 0.8 * hero, vertices=0.9)
        fr.chroma(chroma_kick(t, T["inside_out"], 4.0))
        _edge_bars(fr, t, a)
        _center(fr, t, cam, a)
    _draw_plaque4(fr, t, a)


def _floor_shadow(fr, cam, world, a):
    if a <= 0.003:
        return
    floor_y = -2.8
    flat = world * np.array([1.0, 0.0, 1.0]) + np.array([0.0, floor_y, 0.0])
    xs, ys, _ = cam.project(flat)
    fr.path_fill(T4.hull_path(xs, ys), "#000000", 0.6 * a)
    for i, j, _ in T4.EDGES:
        fr.line(xs[i], ys[i], xs[j], ys[j], "ink", 1.0, 0.25 * a)
    hud.dot_grid(fr, cam, height=floor_y, extent=6.0, alpha=0.12 * a)


def _edge_bars(fr, t, a):
    ba = env(t, T["nothing"] - 0.1, T["s25"] - 0.2, 0.4, 0.5) * a
    if ba <= 0.003:
        return
    p4 = T4.C @ R_at(t).T
    true = T4.edge_lengths(p4) / 2.0  # unit edges: the rotation keeps every one at exactly 1
    proj = T4.edge_lengths(T4.project_persp(p4, D4)[0]) / 2.0
    x0, y0, h = 960 - 31 * 11, 1035.0, 56.0
    pulse_e = pulse(t, T["edge"] - 0.05, T["length"] - T["edge"] + 0.5)
    for k in range(32):
        x = x0 + k * 22
        fr.line(x + 6, y0, x + 6, y0 - h * proj[k], "muted", 7.0, 0.5 * ba)
        fr.line(x, y0, x, y0 - h * true[k], "ink", 4.0, ba, glow=0.15 + 0.35 * pulse_e)
    hud.readout(fr, 960, y0 - h - 46, "4D edge length", f"{true.min():.3f}", "ink", ba, size=28)
    fr.text("projected", 960 + 31 * 11 + 40, y0 - 10, "sans", 22, 600, "muted", ba, align="left")


def _center(fr, t, cam, a):
    sa = smooth(lin(t, T["only"] - 0.2, T["only"] + 0.4)) * env(t, T["only"] - 0.3, END + 0.5, 0.3, 0.01) * a
    ga = env(t, T["no"] - 0.1, T["over2"] + 0.5, 0.2, 0.5) * a
    if ga > 0:  # a ghost axis appears and dissolves: there is none
        xs, ys, _ = cam.project(np.array([[0, -2.6, 0], [0, 2.6, 0]]))
        fr.dashed(xs, ys, "muted", 2.0, ga * (1 - smooth(lin(t, T["over2"] - 0.2, T["over2"] + 0.5))), on=10, off=8)
    if sa > 0:
        xs, ys, _ = cam.project(np.zeros((1, 3)))
        x, y = float(xs[0]), float(ys[0])
        r = lin(t, T["still"] - 0.3, T["still"] + 1.0)
        if 0 < r < 1:
            fr.circle(x, y, 20 + 180 * ease_out(r), "#ffffff", 2.0, (1 - r) * sa, glow=0.8)
        fr.glint(x, y, 40, sa)
        hud.readout(
            fr, 960, 1000, "fixed points", "1", "ink", sa * smooth(lin(t, T["still"], T["still"] + 0.4)), size=32
        )


def _draw_plaque4(fr, t, a):
    pa = smooth(lin(t, T["leaves"] - 0.4, T["leaves"])) * a
    if pa <= 0.003:
        return
    cx, cy, k = plaque_state(t)
    dbl = smooth(lin(t, T["double"] - 0.1, T["double"] + 0.5))
    th = theta_zw(t)
    live = t > T["watch"] + 0.4
    c, s = math.cos(th), math.sin(th)
    zw = (
        [[f"{c:.2f}", f"{-s:.2f}"], [f"{s:.2f}", f"{c:.2f}"]]
        if live
        else [["cos theta", "-sin theta"], ["sin theta", "cos theta"]]
    )
    if dbl > 0.5:
        cells = [
            ["cos theta", "-sin theta", "0", "0"],
            ["sin theta", "cos theta", "0", "0"],
            ["0", "0", "cos phi", "-sin phi"],
            ["0", "0", "sin phi", "cos phi"],
        ]
    else:
        cells = [["1", "0", "0", "0"], ["0", "1", "0", "0"], ["0", "0", *zw[0]], ["0", "0", *zw[1]]]
    colors = {}
    ea = {}
    for r in range(4):
        for cc in range(4):
            in_zw = r >= 2 and cc >= 2
            in_xy = r < 2 and cc < 2
            if in_zw:
                colors[(r, cc)] = "z" if r == 2 else "w"
            elif in_xy and (dbl > 0.5 or r == cc):
                colors[(r, cc)] = "x" if r == 0 else "y"
            else:
                ea[(r, cc)] = 0.35
    alone = env(t, T["leaves"] - 0.1, T["mixes"], 0.2, 0.4)
    mixes = smooth(lin(t, T["mixes"] - 0.1, T["w"] + 0.3))
    dock = smooth(lin(t, T["same"] - 0.1, T["sine"] + 0.3))
    blocks = [((2, 2, 3, 3), TOKENS["z"], TOKENS["w"], max(mixes, dbl))]
    if dbl > 0:
        blocks.append(((0, 0, 1, 1), TOKENS["x"], TOKENS["y"], dbl))
    glow = {(0, 0): 1.0 * alone, (1, 1): 1.0 * alone}
    if dbl > 0:
        glow.update({(0, 0): pulse(t, T["xy2"] - 0.05, 0.6), (2, 2): pulse(t, T["zw2"] - 0.05, 0.6)})
    draw_matrix(
        fr,
        cx,
        cy,
        cells,
        colors,
        cell_w=150 * k,
        cell_h=78 * k,
        size=40 * k,
        alpha=pa,
        entry_alpha=ea,
        blocks=blocks,
        glow=glow,
        pad=30 * k,
    )
    # the 2x2 from S21 flies in and docks into the zw block
    if 0 < dock < 1 and not live:
        fx, fy = lerp(380.0, cx + 150 * k * 1.0, ease_io(dock)), lerp(860.0, cy + 78 * k * 1.0, ease_io(dock))
        draw_matrix(
            fr,
            fx,
            fy,
            [["cos theta", "-sin theta"], ["sin theta", "cos theta"]],
            {},
            cell_w=150 * k,
            cell_h=78 * k,
            size=40 * k,
            alpha=(1 - dock) * pa,
            card=False,
        )
    if live:
        hud.readout(fr, cx, cy + 4 * 78 * k / 2 + 50, "θ", f"{math.degrees(th) % 360:5.1f}°", "w", pa, size=28)
    oa = env(t, T["orthogonal"] - 0.1, T["rigid"], 0.3, 0.4) * a
    if oa > 0:
        typmath.draw(
            fr, "R^T R = I", cx, cy + 4 * 78 * k / 2 + 120, 40, alpha=oa, glow=0.4 * pulse(t, T["orthogonal"], 0.8)
        )
        R = R_at(t)
        assert np.allclose(R.T @ R, np.eye(4)) and abs(np.linalg.det(R) - 1) < 1e-9
        da = smooth(lin(t, T["det"] - 0.1, T["det"] + 0.3)) * oa
        typmath.draw(fr, "det R = cos^2 theta + sin^2 theta = 1", cx - 60, cy + 4 * 78 * k / 2 + 190, 34, alpha=da)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_s21(fr, t)
    draw_s22(fr, t)
    draw_s23(fr, t)
    draw_s24(fr, t)
    hud.eyebrow(fr, t, "05 · ROTATION", START + 0.15)
    fr.vignette(0.5)
    fr.grain(t, 0.045)
    return fr.finish()


def blur_weight(t):
    return max(env(t, T["watch"], T["nothing"] + 0.5, 0.3, 0.6), env(t, T["same_time"] - 0.2, END, 0.4, 0.01))


def draw(t, size):
    t = t + START
    return motion_blur(draw_one, t, size, weight=blur_weight(t))


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch5:{Path(__file__).stat().st_mtime_ns}"
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
    342.4,
    345.9,
    349.0,
    351.0,
    353.6,
    355.6,
    358.9,
    362.0,
    363.6,
    365.6,
    368.2,
    371.3,
    376.4,
    377.9,
    379.4,
    382.9,
    386.6,
    389.9,
    392.6,
    393.8,
    394.6,
    396.6,
    398.6,
    400.1,
    401.8,
    404.6,
    406.6,
    410.4,
    413.5,
    415.1,
    416.6,
    420.4,
    424.3,
    427.0,
    429.4,
    432.4,
]
