"""CHAPTER 4 - SHADOWS ARE LINEAR ALGEBRA (S17-S20), 04:36.590 - 05:41.280.

S17  A shadow forgets the height   slices collapse; a whole shadow; a PyVista glass cube under an overhead light bobs
                                   while its shadow stays put; a vertex (x, y, z) drops to (x, y);
                                   [[1,0,0],[0,1,0],[0,0,0]] (x, y, z) = (x, y, 0) with real numbers
S18  From four to three            the plaque grows to 3 x 4, the fourth column (w) is zero; the tesseract goes
                                   orthographic and its corners stack: 16 -> 8 visible
S19  Perspective along w           receding cheetah frames; a side-view w axis, a camera at w = d, and
                                   x' = d / (d - w) x written per word; a point slides: x1.20 / x0.86 (computed);
                                   the near corners inflate into a big cube, the far ones shrink
S20  A cube inside a cube          the 8 w-edges join them; the six frustum cells are real cubes, like the
                                   trapezoid faces of an ordinary cube drawn in perspective
"""

from __future__ import annotations

import math
from pathlib import Path

import media
import numpy as np
import skia
import typmath
from components import hud
from components import tesseract as T4
from components.matrix_plaque import draw_matrix
from components.vector_slot import Slot, draw_vector
from cues import AUDIO, cue
from fx import Frame, chroma_kick, col, ease_io, ease_out, env, lerp, lin, motion_blur, pulse, smooth
from pv3d import render as pvr
from pv3d import solids
from space import orbit, to_view
from theme import THEME, H, W
from typmath import tc

START = cue(793)  # 276.59 "Slices show one piece at a time"
END = cue(976)  # 341.28 "Now let's make it move"

C = {i: cue(i) for i in range(793, 977)}
T = {
    "piece": C[795],
    "shadows": C[800],
    "linear": C[809],
    "s17b": C[812],
    "light": C[814],
    "down": C[816],
    "forgets": C[823],
    "height": C[825],
    "every": C[827],
    "lands": C[831],
    "lands_end": C[834],
    "matrix": C[839],
    "keeps_x": C[841],
    "keeps_y": C[843],
    "zero": C[846],
    "zero_end": C[849],
    "s18": C[850],
    "three_by": C[856],
    "matrix4": C[859],
    "rows": [C[861], C[862], C[864]],
    "drops": C[865],
    "straight": C[868],
    "stacks": C[870],
    "top": C[873],
    "perspective": C[880],
    "s19": C[881],
    "eyes": C[884],
    "farther": C[887],
    "smaller": C[890],
    "place": C[891],
    "camera": C[893],
    "along_w": C[896],
    "scaled": C[900],
    "d_num": C[903],
    "divided": C[905],
    "d_den": C[909],
    "minus": C[910],
    "w_den": C[911],
    "large": C[915],
    "grow": C[920],
    "small": C[924],
    "shrink": C[929],
    "near": C[932],
    "big": C[937],
    "far": C[941],
    "small_cube": C[946],
    "s20": C[948],
    "join_w": C[951],
    "famous": C[956],
    "inside": C[959],
    "six": C[964],
    "real": C[970],
    "perspective4": C[974],
}
FOCAL = 1500.0
D4 = 3.0


def V3(p):
    """Math (x, y, z up) -> view world."""
    return to_view(np.asarray(p, float))


def pv_size(fr):
    return (fr.w, fr.h)


# ------------------------------------------------------------------ S17: a shadow forgets the height

CUBE_HALF = 1.0


def cube_height(t):
    """Centre height of the floating cube: it bobs on 'forgets the height', the shadow does not move."""
    bob = env(t, T["forgets"] - 0.3, T["every"] - 0.2, 0.3, 0.5)
    return 2.2 + 0.7 * math.sin((t - T["forgets"] + 0.3) * 4.0) * bob


def cam17(t):
    return orbit(V3((0.0, 0.0, 1.6)), 11.0, 0.36, -0.55 + 0.02 * (t - T["s17b"]), focal=FOCAL, center=(680.0, 560.0))


def draw_s17(fr, t):
    a = env(t, START - 0.01, T["s18"] + 0.6, 0.01, 0.6)
    if a <= 0.003:
        return
    # 17A: the slices collapse into one sheet, then a whole shadow, then a matrix bracket glints
    pa = env(t, START - 0.01, T["s17b"] + 0.1, 0.01, 0.5)
    if pa > 0:
        squeeze = ease_io(lin(t, T["piece"] - 0.2, T["piece"] + 0.6))
        for k, s in enumerate((0.6, 1.5, 2.0, 2.5, 3.4)):
            cx = lerp(620 + k * 270, 960, squeeze)
            cam = orbit((0, 0, 0), 11.0, 0.35, 0.5 + 0.2 * t, focal=FOCAL, center=(cx, 700.0))
            pts, loops = T4.corner_slice(s)
            T4.draw_solid(
                fr,
                cam,
                pts * 1.05,
                loops,
                "w",
                pa * (1 - smooth(lin(t, T["shadows"] - 0.3, T["shadows"]))),
                fill=0.14,
                width=2.0,
                glow=0.5,
            )
        sa = smooth(lin(t, T["shadows"] - 0.1, T["shadows"] + 0.6)) * pa
        if sa > 0:
            cam = orbit((0, 0, 0), 10.0, 0.30, -0.5 + 0.1 * t, focal=FOCAL, center=(960.0, 520.0))
            p3, _ = T4.project_persp(T4.C, D4)
            world = T4.place(p3, scale=1.1)
            xs, ys, _ = cam.project(world)
            hull = T4.hull_path(xs, ys)
            fr.path_fill(hull, "#060A12", 0.9 * sa)
            fr.path_stroke(hull, "ink", 2.0, 0.6 * sa, glow=0.4)
            T4.draw(fr, cam, world, 0.35 * sa, width=1.4, glow=0.2)
            ga = env(t, T["linear"] - 0.1, T["s17b"] + 0.1, 0.3, 0.4)
            if ga > 0:
                bx = 760
                for side, x in ((-1, 960 - bx / 2 - 40), (1, 960 + bx / 2 + 40)):
                    lip = 30 * -side
                    p = skia.Path()
                    p.moveTo(x + lip, 220)
                    p.lineTo(x, 220)
                    p.lineTo(x, 860)
                    p.lineTo(x + lip, 860)
                    fr.path_stroke(p, "ink", 4.0, ga, glow=0.8)
                    r = skia.Path()
                    r.addRect(skia.Rect.MakeLTRB(x - 6, 214, x + 6, 866))
                    fr.light_sweep(r, lin(t, T["linear"] + 0.1, T["linear"] + 0.9), strength=1.0)
    ca = smooth(lin(t, T["s17b"] - 0.3, T["s17b"] + 0.4)) * a
    if ca <= 0.003:
        return
    cam = cam17(t)
    h = cube_height(t)
    hud.dot_grid(fr, cam, height=0.0, extent=5.5, alpha=0.16 * ca)
    light = smooth(lin(t, T["light"] - 0.2, T["down"] + 0.3)) * ca
    # the shadow: straight down, it keeps x and y and forgets z
    floor = np.array([[x, y, 0.0] for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]) * CUBE_HALF
    xs, ys, _ = cam.project(V3(floor))
    sh = skia.Path()
    sh.addPoly([skia.Point(float(x), float(y)) for x, y in zip(xs, ys)], True)
    if light > 0:
        fr.path_fill(sh, "#000000", 0.85 * light)
        fr.path_stroke(sh, "ink", 1.6, 0.55 * light)
        _shafts(fr, cam, light)
    box = solids.box(V3((0, 0, h)), (CUBE_HALF, CUBE_HALF, CUBE_HALF))
    rgba = pvr.render([(box, pvr.GLASS | dict(color="#A9C6E8", opacity=0.28))], cam, pv_size(fr), cache="ch4_cube")
    pvr.composite(fr, rgba, ca)
    corners = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float) * CUBE_HALF
    cw = V3(corners + np.array([0, 0, h]))
    cx_, cy_, _ = cam.project(cw)
    for i in range(8):
        for j in range(i + 1, 8):
            d = np.flatnonzero(corners[i] != corners[j])
            if len(d) == 1:
                fr.line(cx_[i], cy_[i], cx_[j], cy_[j], "xyz"[d[0]], 2.4, ca, glow=0.6)
    # one vertex: (x, y, z) -> (x, y)
    v = np.array([CUBE_HALF, CUBE_HALF, h + CUBE_HALF])
    ta = smooth(lin(t, T["every"] - 0.1, T["every"] + 0.4)) * env(t, T["s17b"], T["s18"] + 0.4, 0.1, 0.5)
    if ta > 0:
        vx, vy, _ = cam.project(V3(v)[None])
        fr.glow_dot(float(vx[0]), float(vy[0]), 7, "#ffffff", ta, 1.4)
        hud.coord_chip(
            fr,
            float(vx[0]) + 110,
            float(vy[0]) - 40,
            [f"{v[0]:.1f}", f"{v[1]:.1f}", f"{v[2]:.1f}"],
            list("xyz"),
            ta,
            size=28,
        )
        drop = ease_out(lin(t, T["lands"] - 0.1, T["lands"] + 0.6))
        if drop > 0:
            p_floor = np.array([v[0], v[1], 0.0])
            q = lerp(v, p_floor, drop)
            lx, ly, _ = cam.project(V3(np.array([v, q])))
            fr.dashed(lx, ly, "z", 2.0, ta, glow=0.5, on=10, off=7)
            fx_, fy_, _ = cam.project(V3(p_floor)[None])
            la = smooth(lin(t, T["lands_end"] - 0.3, T["lands_end"] + 0.2)) * ta
            fr.glow_dot(float(fx_[0]), float(fy_[0]), 6, "ink", la, 1.2)
            hud.coord_chip(
                fr, float(fx_[0]) + 120, float(fy_[0]) + 40, [f"{v[0]:.1f}", f"{v[1]:.1f}"], list("xy"), la, size=28
            )
    _draw_plaque3(fr, t, v)


def _shafts(fr, cam, a):
    """Straight-down volumetric light: a prism of light from a square lamp to the shadow."""
    top = np.array([[x, y, 6.2] for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]) * np.array([1.15, 1.15, 1.0])
    bot = np.array([[x, y, 0.0] for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]) * 1.15
    tx, ty, _ = cam.project(V3(top))
    bx, by, _ = cam.project(V3(bot))
    for k in range(4):
        j = (k + 1) % 4
        p = skia.Path()
        p.addPoly(
            [
                skia.Point(float(tx[k]), float(ty[k])),
                skia.Point(float(tx[j]), float(ty[j])),
                skia.Point(float(bx[j]), float(by[j])),
                skia.Point(float(bx[k]), float(by[k])),
            ],
            True,
        )
        sh = skia.GradientShader.MakeLinear(
            [skia.Point(float(tx[k]), float(ty[k])), skia.Point(float(bx[k]), float(by[k]))],
            [col("light", 0.10 * a), col("light", 0.02 * a)],
        )
        fr.c.drawPath(p, skia.Paint(AntiAlias=True, Shader=sh, BlendMode=skia.BlendMode.kPlus))
    lx, ly, _ = cam.project(V3(np.array([[0, 0, 6.2]])))
    fr.glint(float(lx[0]), float(ly[0]), 50, a)


def _draw_plaque3(fr, t, v):
    a = env(t, T["matrix"] - 0.4, T["s18"] + 0.1, 0.4, 0.01)
    if a <= 0.003:
        return
    P = np.diag([1.0, 1.0, 0.0])
    out = P @ v
    cells = [[str(int(P[r, c])) for c in range(3)] for r in range(3)]
    colors = {(0, 0): "x", (1, 1): "y", (2, 2): "z"}
    zero_glow = pulse(t, T["zero"] - 0.05, T["zero_end"] - T["zero"] + 0.4)
    rows = {
        0: ("x", env(t, T["keeps_x"] - 0.1, T["keeps_y"] + 0.1, 0.15, 0.3)),
        1: ("y", env(t, T["keeps_y"] - 0.1, T["zero"], 0.15, 0.3)),
    }
    draw_matrix(
        fr,
        1290,
        470,
        cells,
        colors,
        cell_w=84,
        cell_h=70,
        size=40,
        alpha=a,
        row_hi=rows,
        glow={(2, 2): 1.4 * zero_glow},
        pad=26,
    )
    typmath.draw(fr, "dot", 1480, 470, 40, color="muted", alpha=a)
    draw_vector(fr, 1560, 470, [Slot(f"{v[k]:.1f}", "xyz"[k]) for k in range(3)], 36, alpha=a, width=96)
    typmath.draw(fr, "=", 1660, 470, 44, color="muted", alpha=a)
    squash = ease_io(lin(t, T["zero"] + 0.1, T["zero_end"]))
    res = [
        Slot(f"{out[0]:.1f}", "x"),
        Slot(f"{out[1]:.1f}", "y"),
        Slot(f"{lerp(v[2], 0.0, squash):.1f}", "z", glow=0.8 * squash),
    ]
    draw_vector(fr, 1760, 470, res, 36, alpha=a, width=96)


# ------------------------------------------------------------------ S18: from four to three


def ortho_mix(t):
    return ease_io(lin(t, T["straight"] - 0.4, T["stacks"] + 0.4)) * (
        1 - ease_io(lin(t, T["perspective"], T["s19"] + 0.4))
    )


def rig18_world(t, mix):
    R = T4.rotation(("xy", 0.12 * (t - T["s18"])), ("yz", 0.25))
    p4 = T4.C @ R.T
    persp, _ = T4.project_persp(p4, D4)
    ortho = T4.project_ortho(p4)
    return T4.place(lerp(persp, ortho, mix), scale=1.1)


def draw_s18(fr, t):
    a = env(t, T["s18"] - 0.3, T["s19"] + 0.3, 0.5, 0.4)
    if a <= 0.003:
        return
    grow = ease_out(lin(t, T["s18"] + 0.2, T["s18"] + 0.9))
    cells = [["1", "0", "0", "0"], ["0", "1", "0", "0"], ["0", "0", "1", "0"]]
    colors = {(0, 0): "x", (1, 1): "y", (2, 2): "z", (0, 3): "w", (1, 3): "w", (2, 3): "w"}
    ea = {(r, 3): grow for r in range(3)}
    rows = {}
    for r, tr in enumerate(T["rows"]):
        s = env(t, tr - 0.1, T["drops"], 0.15, 0.3)
        if s > 0:
            rows[r] = ("xyz"[r], s)
    drop = env(t, T["drops"] - 0.1, T["s19"], 0.2, 0.4)
    draw_matrix(
        fr,
        470,
        400,
        cells,
        colors,
        cell_w=80,
        cell_h=70,
        size=38,
        alpha=a,
        entry_alpha=ea,
        row_hi=rows,
        col_hi={3: ("w", drop)} if drop > 0 else None,
        pad=26,
    )
    dims = env(t, T["three_by"] - 0.1, T["s19"], 0.2, 0.4)
    typmath.draw(fr, "3 times 4", 470, 220, 40, color="ink", alpha=dims * a)
    fall = ease_io(lin(t, T["drops"], T["drops"] + 0.7))
    slots = [Slot(k, k) for k in "xyz"] + [Slot("w", "w", alpha=1 - fall)]
    typmath.draw(fr, "dot", 660, 400, 36, color="muted", alpha=a)
    draw_vector(fr, 740, 400 + 26 * fall, slots, 36, alpha=a, width=70)
    if fall > 0:
        typmath.draw(fr, "w", 740, 470 + 120 * fall, 36, color="w", alpha=a * (1 - fall))
    # 18B: the tesseract goes orthographic and its corners stack
    mix = ortho_mix(t)
    ra = smooth(lin(t, T["straight"] - 0.6, T["straight"])) * a
    if ra > 0:
        cam = orbit((0, 0, 0), 10.0, 0.32, -0.5, focal=FOCAL, center=(1380.0, 520.0))
        world = rig18_world(t, mix)
        T4.draw(fr, cam, world, ra, width=2.2, glow=0.6)
        xs, ys, _ = cam.project(world)
        pop = pulse(t, T["stacks"] + 0.3, 0.9)
        for v in range(16):
            fr.glow_dot(xs[v], ys[v], 4.5 + 6 * pop * (mix > 0.95), "#ffffff" if mix > 0.95 else "ink", ra, 0.8 + pop)
        visible = len({(round(float(x), 0), round(float(y), 0)) for x, y in zip(xs, ys)})
        ca = smooth(lin(t, T["stacks"] - 0.2, T["stacks"] + 0.3)) * ra
        hud.readout(fr, 1380, 950, "visible corners", f"{min(visible, 16)}", "ink", ca, size=34)
    # the iris ring: on to perspective
    u = lin(t, T["perspective"] - 0.1, T["perspective"] + 0.8)
    if 0 < u < 1:
        fr.circle(960, 540, 60 + 900 * ease_out(u), "ink", 3.0, (1 - u) * a, glow=1.0)


# ------------------------------------------------------------------ S19: perspective along w

AX_Y = 600.0
D_PERSP = 3.0


def wx(w):
    return 840.0 + w * 170.0


def draw_s19(fr, t):
    a = env(t, T["s19"] - 0.2, T["s20"] + 0.2, 0.4, 0.01)
    if a <= 0.003:
        return
    # 19A: a corridor of identical frames; farther ones look smaller
    ca = env(t, T["eyes"] - 0.4, T["place"] + 0.2, 0.4, 0.5) * a
    if ca > 0:
        cam = orbit((0.0, 0.0, 7.0), 10.0, 0.10, -0.62, focal=FOCAL, center=(900.0, 500.0))
        hw, hh = 1.6, 0.9

        def quad(k):
            z = 2.5 + k * 3.0
            return np.array([[-hw, hh, z], [hw, hh, z], [hw, -hh, z], [-hw, -hh, z]]) + np.array([-0.6, 0, 0])

        q0 = cam.project(quad(0))
        ref = float(q0[1][3] - q0[1][0])  # apparent height of the nearest frame (heights are not foreshortened)
        for k in reversed(range(6)):  # far to near, so nearer frames cover farther ones
            xs, ys, zz = cam.project(quad(k))
            fr.image_quad(media.thumb(40 + 6 * k), list(zip(xs, ys)), ca * (1 - 0.1 * k))
            fr.poly(xs, ys, "ink", 1.2, 0.5 * ca, close=True)
        for k in range(6):  # readouts on top of every frame
            xs, ys, _ = cam.project(quad(k))
            ra = smooth(lin(t, T["farther"] + 0.12 * k, T["farther"] + 0.12 * k + 0.3)) * ca
            hud.readout(
                fr, float(xs[0]) + 40, float(ys[3]) + 34, "×", f"{(ys[3] - ys[0]) / ref:.2f}", "ink", ra, size=24
            )
    # 19B-C: the side view: a w axis, a camera at w = d, and the rule
    sa = env(t, T["place"] - 0.2, T["near"] - 0.2, 0.4, 0.5) * a
    if sa > 0:
        fr.line(wx(-2.4), AX_Y, wx(3.6), AX_Y, "w", 2.2, sa, glow=0.5)
        hud.arrow_head(fr, wx(3.4), AX_Y, wx(3.75), AX_Y, "w", sa, 14)
        fr.text("w", wx(3.75) + 22, AX_Y + 12, "italic", 38, 500, "w", sa)
        for k in (-2, -1, 0, 1, 2):
            fr.line(wx(k), AX_Y - 8, wx(k), AX_Y + 8, "w", 1.4, sa)
            typmath.number(fr, str(k), wx(k), AX_Y + 34, 24, "muted", sa)
        cu = smooth(lin(t, T["camera"] - 0.1, T["along_w"] + 0.3)) * sa
        cx = wx(D_PERSP)
        if cu > 0:
            fr.circle(cx, AX_Y, 34, "ink", 2.4, cu, glow=0.8)
            for k in range(6):
                ang = k * math.pi / 3 + 0.3
                fr.line(
                    cx + 12 * math.cos(ang),
                    AX_Y + 12 * math.sin(ang),
                    cx + 34 * math.cos(ang + 0.6),
                    AX_Y + 34 * math.sin(ang + 0.6),
                    "ink",
                    1.4,
                    cu,
                )
            fr.text("camera", cx, AX_Y + 80, "sans", 26, 600, "muted", cu)
            typmath.draw(fr, "w = d", cx, AX_Y - 70, 34, color="w", alpha=cu)
        _draw_rule(fr, t, sa)
        _draw_point(fr, t, sa)
    _draw_inflate(fr, t, a)


def _draw_rule(fr, t, a):
    expr = f"x' = d/(d - {tc('w', 'w')}) dot x"
    when = [
        T["scaled"],
        T["scaled"] + 0.1,
        T["scaled"] + 0.2,
        T["d_num"],
        T["d_den"],
        T["minus"],
        T["w_den"],
        T["divided"],
        T["w_den"] + 0.3,
        T["w_den"] + 0.4,
    ]
    alphas = {i: smooth(lin(t, tt - 0.12, tt + 0.2)) for i, tt in enumerate(when)}
    typmath.draw(fr, expr, 840, 230, 66, alpha=a, alphas=alphas, glow=0.2)


def w_point(t):
    keys = [
        (T["large"] - 0.4, 0.0),
        (T["grow"], 0.5),
        (T["small"] - 0.2, 0.5),
        (T["shrink"], -0.5),
        (T["near"] - 0.3, -0.5),
    ]
    if t <= keys[0][0]:
        return 0.0
    for (t0, w0), (t1, w1) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp(w0, w1, ease_io(lin(t, t0, t1)))
    return keys[-1][1]


def _draw_point(fr, t, a):
    pa = smooth(lin(t, T["large"] - 0.6, T["large"] - 0.1)) * a
    if pa <= 0.003:
        return
    w = w_point(t)
    f = D_PERSP / (D_PERSP - w)
    x = wx(w)
    h = 70.0
    cx = wx(D_PERSP)
    fr.line(x, AX_Y - h, x, AX_Y + h, "x", 3.0, pa, glow=0.7)
    for y0 in (AX_Y - h, AX_Y + h):
        fr.line(x, y0, cx, AX_Y, "ink", 1.0, 0.4 * pa)
    bx = 1640.0
    fr.line(bx, AX_Y - h * f, bx, AX_Y + h * f, "x", 6.0, pa, glow=0.9)
    fr.text("on screen", bx, AX_Y + 150, "sans", 24, 600, "muted", pa)
    hud.readout(fr, bx, AX_Y - 190, "×", f"{f:.2f}", "ink", pa, size=32)
    hud.readout(fr, x, AX_Y + 120, "w", f"{w:+.2f}", "w", pa, size=26)


def inflate(t):
    near = ease_io(lin(t, T["near"] - 0.1, T["big"] + 0.4))
    far = ease_io(lin(t, T["far"] - 0.1, T["small_cube"] + 0.3))
    return near, far


def rig19_world(t, near, far):
    p4 = T4.C.copy()
    f = np.where(p4[:, 3] > 0, lerp(1.0, D4 / (D4 - 1), near), lerp(1.0, D4 / (D4 + 1), far))
    p3 = p4[:, :3] * f[:, None]
    return T4.place(p3 @ T4.rotation(("xy", 0.0))[:3, :3].T, scale=1.15)


def cam20(t):
    return orbit((0, 0, 0), 10.0, 0.30, -0.55 + 0.05 * (t - T["near"]), focal=FOCAL, center=(960.0, 500.0))


def _draw_inflate(fr, t, a):
    ra = smooth(lin(t, T["near"] - 0.5, T["near"])) * a
    if ra <= 0.003:
        return
    near, far = inflate(t)
    cam = cam20(t)
    world = rig19_world(t, near, far)
    ea = np.array([0.0 if ax == 3 else 1.0 for _, _, ax in T4.EDGES])
    T4.draw(fr, cam, world, ra, edge_alpha=ea, width=2.4, glow=0.7)
    xs, ys, _ = cam.project(world)
    gn = pulse(t, T["near"] - 0.05, 0.9)
    gf = pulse(t, T["far"] - 0.05, 0.9)
    for v in range(16):
        g = gn if T4.C[v, 3] > 0 else gf
        fr.glow_dot(xs[v], ys[v], 4.5 + 5 * g, "w" if g > 0.05 else "ink", ra, 0.8 + g)
    la = env(t, T["big"] - 0.1, T["s20"] + 0.3, 0.3, 0.4) * a
    fr.text("big cube  (w = +1)", 960, 960, "sans", 30, 600, "ink", la * (1 - smooth(lin(t, T["far"], T["far"] + 0.3))))
    lf = env(t, T["small_cube"] - 0.1, T["s20"] + 0.3, 0.3, 0.4) * a
    fr.text("small cube  (w = −1)", 960, 960, "sans", 30, 600, "ink", lf)


# ------------------------------------------------------------------ S20: a cube inside a cube


def draw_s20(fr, t):
    a = smooth(lin(t, T["s20"] - 0.2, T["s20"] + 0.1))
    if a <= 0.003:
        return
    cam = cam20(t)
    world = rig19_world(t, 1.0, 1.0)
    conn = [k for k, (_, _, ax) in enumerate(T4.EDGES) if ax == 3]
    ea = np.ones(32)
    for n, k in enumerate(conn):
        ea[k] = smooth(lin(t, T["s20"] + 0.1 * n, T["s20"] + 0.1 * n + 0.35))
    hero = pulse(t, T["inside"] - 0.05, 1.2)
    xs, ys, _ = cam.project(world)
    # the six lopsided cells are real cubes: glass tint, one by one
    frustums = [n for n, (axis, _, _) in enumerate(T4.CELLS) if axis != 3]
    both = pulse(t, T["perspective4"] - 0.05, 1.2)
    for n, cell in enumerate(frustums):
        t0 = T["six"] + 0.18 * n
        ca = smooth(lin(t, t0, t0 + 0.35)) * a
        if ca > 0:
            T4.fill_cell(fr, cam, world, cell, "w", (0.06 + 0.08 * both) * ca, stroke=0.25 * ca)
    T4.draw(fr, cam, world, a, edge_alpha=ea, width=2.6 + hero, glow=0.8 + 0.8 * hero, vertices=0.9)
    fa = lin(t, T["famous"] - 0.05, T["famous"] + 0.8)
    if 0 < fa < 1:
        fr.light_sweep(T4.hull_path(xs, ys), fa, strength=0.7)
    la = smooth(lin(t, T["inside"] - 0.1, T["inside"] + 0.4)) * (1 - smooth(lin(t, T["six"] - 0.3, T["six"])))
    fr.text("a cube inside a cube", 960, 960, "display", 54, 600, "ink", la * a, tracking=0.02)
    _draw_inset(fr, t, both)
    fr.chroma(chroma_kick(t, T["inside"], 4.0))


def _draw_inset(fr, t, both):
    a = smooth(lin(t, T["real"] - 0.3, T["real"] + 0.3))
    if a <= 0.003:
        return
    hud.glass_card(fr, 80, 640, 380, 340, a)
    cam = orbit((0, 0, 0), 7.0, 0.45, -0.55, focal=620.0, center=(270.0, 790.0))
    cube = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float)
    xs, ys, _ = cam.project(cube)
    face = [0, 1, 3, 2]  # the x = -1 face: drawn in perspective it is a trapezoid
    p = skia.Path()
    p.addPoly([skia.Point(float(xs[k]), float(ys[k])) for k in face], True)
    fr.path_fill(p, "w", (0.18 + 0.2 * both) * a, glow=0.4 * both)
    for i in range(8):
        for j in range(i + 1, 8):
            d = np.flatnonzero(cube[i] != cube[j])
            if len(d) == 1:
                fr.line(xs[i], ys[i], xs[j], ys[j], "xyz"[d[0]], 2.0, a, glow=0.4)
    fr.text("an ordinary cube, in perspective", 270, 958, "sans", 22, 600, "muted", a)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_s17(fr, t)
    draw_s18(fr, t)
    draw_s19(fr, t)
    draw_s20(fr, t)
    hud.eyebrow(fr, t, "04 · SHADOWS", START + 0.15)
    fr.vignette(0.5)
    fr.grain(t, 0.045)
    return fr.finish()


def blur_weight(t):
    return 0.0


def draw(t, size):
    t = t + START
    return motion_blur(draw_one, t, size, weight=blur_weight(t))


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch4:{Path(__file__).stat().st_mtime_ns}"
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
    277.6,
    279.5,
    282.4,
    284.8,
    286.6,
    288.6,
    290.2,
    292.5,
    293.6,
    295.1,
    297.5,
    299.3,
    301.6,
    303.0,
    304.6,
    306.3,
    308.1,
    310.0,
    312.5,
    315.6,
    318.6,
    320.8,
    323.6,
    326.3,
    328.4,
    329.9,
    332.0,
    333.4,
    335.0,
    337.2,
    339.8,
]
