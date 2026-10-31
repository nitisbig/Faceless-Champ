"""CHAPTER 3 - SLICES (S13-S16), 03:37.120 - 04:36.590.

S13  Only in pieces          the tesseract separates into its real w-slices (7 cubes) like a sliced loaf; the world
                             flattens into one glowing sheet
S14  Flatland                a creature on the sheet; a PyVista sphere falls through it (clipped by the sheet); the
                             real cross-section r = sqrt(R^2 - h^2) in the main view and the creature's-view inset;
                             a filmstrip of 7 slices along a blue time axis
S15  A 4D ball               the sheet becomes our space; a w slider with r(w) drives a PyVista glass sphere that
                             appears, swells, shrinks, vanishes; rack focus to the cheetah block (the same idea)
S16  Corner-first slices     the rig turns until 0000 leads; the hyperplane x+y+z+w = s cuts it: blue dots ride the
                             32 edges and the real ConvexHull solid (PyVista glass + skia edges) goes tetrahedron ->
                             truncated -> octahedron (two pyramids) -> back; face-first vs corner-first filmstrip
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
import typmath
from components import hud
from components import tesseract as T4
from components.cheetah_block import CheetahBlock, playback_frame
from cues import AUDIO, cue
from fx import Frame, chroma_kick, ease_io, env, lerp, lin, motion_blur, pulse, smooth
from pv3d import render as pvr
from pv3d import solids
from scipy.spatial import ConvexHull
from space import orbit
from theme import THEME, TOKENS, H, W

START = cue(630)  # 217.12 "But how would we actually see"
END = cue(793)  # 276.59 "Slices show one piece at a time"

C = {i: cue(i) for i in range(630, 794)}
T = {
    "pieces": C[639],
    "shrink": C[645],
    "dimension": C[649],
    "s14": C[650],
    "creature": C[653],
    "ball": C[661],
    "falls": C[662],
    "never": C[668],
    "dot": C[675],
    "circle": C[680],
    "shrink2": C[681],
    "vanish": C[683],
    "slice": C[687],
    "sphere": C[691],
    "s15": C[692],
    "tiny": C[706],
    "swelling": C[711],
    "shrinking": C[712],
    "gone": C[714],
    "playing": C[719],
    "frame": C[725],
    "one_slice": C[727],
    "block": C[731],
    "block_end": C[732],
    "s16": C[733],
    "stranger": C[739],
    "corner": C[743],
    "tetra": C[750],
    "pyramid": C[753],
    "grows": C[756],
    "clipped": C[758],
    "clipped_end": C[760],
    "middle": C[764],
    "octa": C[768],
    "two_pyr": C[771],
    "base": C[776],
    "reverse": C[780],
    "reverse_end": C[782],
    "same": C[783],
    "slices": C[787],
    "angle": C[792],
}
FOCAL = 1500.0
D4 = 3.0


def pv_size(fr):
    return (fr.w, fr.h)


# ------------------------------------------------------------------ S13: only in pieces


def rig_world(t, scale=1.25, center=(0.0, 0.0, 0.0)):
    R = T4.rotation(("xw", 0.18 * (t - START)), ("yz", 0.10 * (t - START)))
    p3, _ = T4.project_persp(T4.C @ R.T, D4)
    return T4.place(p3, center=center, scale=scale)


def draw_s13(fr, t):
    a = 1 - smooth(lin(t, T["dimension"] - 0.4, T["s14"] + 0.2))
    if a <= 0.003:
        return
    flat = ease_io(lin(t, T["shrink"] - 0.1, T["dimension"] + 0.2))  # the world flattens
    cam = orbit((0, 0, 0), lerp(9.5, 11.0, flat), lerp(0.28, 0.42, flat), -0.45, focal=FOCAL)
    split = ease_io(lin(t, T["pieces"] - 0.2, T["pieces"] + 0.9))
    squash = np.array([1.0, 1.0 - flat, 1.0])
    if split < 0.02:
        world = rig_world(t) * squash
        T4.draw(fr, cam, world, a, width=2.4, glow=0.7, vertices=0.8)
    else:
        # the real w-slices of the (face-first) tesseract are cubes; spread them like a sliced loaf
        n = 7
        for k in range(n):
            w = -1 + 2 * k / (n - 1)
            off = np.array([(k - 3) * 0.82, 0.0, (k - 3) * -0.32]) * split
            cube = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float)
            f = D4 / (D4 - w)
            pts = (cube * 1.15 * f * (1 - 0.45 * split) + off) * squash
            xs, ys, zz = cam.project(pts)
            ka = a * (0.55 + 0.45 * math.cos(math.pi * (k - 3) / 7))
            for i in range(8):
                for j in range(i + 1, 8):
                    if bin(i ^ j).count("1") == 1:
                        fr.line(xs[i], ys[i], xs[j], ys[j], "w", 1.8, ka, glow=0.6)
    sheet = smooth(lin(t, T["shrink"] + 0.3, T["dimension"]))
    if sheet > 0:
        _draw_sheet(fr, cam_sheet(t), t, sheet * a)


# ------------------------------------------------------------------ S14: Flatland

R_BALL = 1.3
BALL_X, BALL_Z = 0.9, 0.3


def cam_sheet(t):
    up = ease_io(lin(t, T["s15"] - 0.1, T["s15"] + 1.4))
    return orbit(
        (0.2, lerp(-0.3, 0.6, up), 0.0),
        lerp(11.0, 13.5, up),
        lerp(0.42, 0.30, up),
        lerp(-0.30, -0.55, up),
        focal=FOCAL,
        center=(lerp(860.0, 960.0, up), 520.0),
    )


def _draw_sheet(fr, cam, t, a, glow=0.0):
    """The glass sheet (y = 0) with a fine perspective grid."""
    if a <= 0.003:
        return
    X, Z = 4.4, 3.0
    corners = np.array([[-X, 0, -Z], [X, 0, -Z], [X, 0, Z], [-X, 0, Z]])
    xs, ys, _ = cam.project(corners)
    p = skia.Path()
    p.addPoly([skia.Point(float(x), float(y)) for x, y in zip(xs, ys)], True)
    fr.path_fill(p, "#0C1422", 0.85 * a)
    fr.path_stroke(p, "w", 1.6, 0.55 * a, glow=0.4 + glow)
    for gx in np.arange(-X, X + 1e-6, 0.5):
        q = cam.project(np.array([[gx, 0, -Z], [gx, 0, Z]]))
        fr.line(q[0][0], q[1][0], q[0][1], q[1][1], "#2C3B55", 1.0, 0.5 * a)
    for gz in np.arange(-Z, Z + 1e-6, 0.5):
        q = cam.project(np.array([[-X, 0, gz], [X, 0, gz]]))
        fr.line(q[0][0], q[1][0], q[0][1], q[1][1], "#2C3B55", 1.0, 0.5 * a)


def ball_h(t):
    """Height of the ball's centre above the sheet."""
    keys = [
        (T["ball"] - 0.1, 4.8),
        (T["dot"], R_BALL),
        (T["circle"], 0.0),
        (T["vanish"], -R_BALL),
        (T["vanish"] + 1.2, -3.2),
    ]
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, h0), (t1, h1) in zip(keys, keys[1:]):
        if t <= t1:
            u = lin(t, t0, t1)
            if t0 == keys[0][0]:
                u = u * u  # falling: gravity
            return lerp(h0, h1, u)
    return keys[-1][1]


def section_r(h):
    return math.sqrt(max(0.0, R_BALL**2 - h**2))


def _creature(fr, cx, cy, size, alpha, heading=0.0):
    """A flat creature: a rounded triangle with one eye."""
    if alpha <= 0.003:
        return
    pts = []
    for k in range(3):
        ang = heading + k * 2 * math.pi / 3
        pts.append((cx + size * math.cos(ang), cy + size * 0.6 * math.sin(ang)))
    p = skia.Path()
    p.addPoly([skia.Point(*q) for q in pts], True)
    fr.path_fill(p, "#FFB86B", alpha * 0.85, glow=0.4)
    fr.path_stroke(p, "#FFE3C2", 1.6, alpha)
    fr.circle(
        cx + size * 0.45 * math.cos(heading),
        cy + size * 0.27 * math.sin(heading),
        size * 0.14,
        "#000000",
        alpha=alpha,
        fill=True,
    )


def draw_s14(fr, t):
    a = env(t, T["s14"] - 0.3, T["s15"] + 1.2, 0.3, 0.8)
    if a <= 0.003:
        return
    cam = cam_sheet(t)
    sheet_a = a * (1 - smooth(lin(t, T["s15"] + 0.2, T["s15"] + 1.2)))
    h = ball_h(t)
    show_ball = T["ball"] - 0.2 < t < T["vanish"] + 1.2
    clip_y = 0.0
    # PyVista: the part of the ball under the sheet is drawn first (the sheet veils it), then the part above
    below = above = None
    if show_ball:
        ball = solids.sphere((BALL_X, h, BALL_Z), R_BALL, 72)
        style = pvr.GLOSS | dict(color="#2A3346")
        if h - R_BALL < clip_y:
            low = ball.clip(normal=(0, 1, 0), origin=(0, clip_y, 0), invert=True)
            if low.n_points:
                below = pvr.render([(low, style)], cam, pv_size(fr), cache="ch3_ball")
        if h + R_BALL > clip_y:
            high = ball.clip(normal=(0, -1, 0), origin=(0, clip_y, 0), invert=True) if h - R_BALL < clip_y else ball
            if high.n_points:
                above = pvr.render([(high, style)], cam, pv_size(fr), cache="ch3_ball")
    if below is not None:
        pvr.composite(fr, below, 0.55 * a)
    _draw_sheet(fr, cam, t, sheet_a)
    # the creature glides toward where the ball will land
    ca = smooth(lin(t, T["creature"] - 0.2, T["creature"] + 0.4)) * sheet_a
    if ca > 0:
        cx = lerp(-3.2, -1.2, ease_io(lin(t, T["creature"] - 0.2, T["never"])))
        xs, ys, z = cam.project(np.array([[cx, 0.0, BALL_Z]]))
        _creature(fr, float(xs[0]), float(ys[0]), 26 * 12 / float(z[0]), ca)
    if above is not None:
        pvr.composite(fr, above, a)
    # the cross-section: real radius, drawn on the sheet
    r = section_r(h)
    if r > 0.005 and show_ball:
        ring = np.array(
            [[BALL_X + r * math.cos(u), 0.0, BALL_Z + r * math.sin(u)] for u in np.linspace(0, 2 * math.pi, 72)]
        )
        xs, ys, _ = cam.project(ring)
        p = skia.Path()
        p.addPoly([skia.Point(float(x), float(y)) for x, y in zip(xs, ys)], True)
        fr.path_fill(p, "w", 0.22 * a, glow=0.5)
        fr.path_stroke(p, "w", 2.8, a, glow=1.2)
    # the creature's view: only what lies in the sheet
    ia = env(t, T["never"] - 0.2, T["s15"] + 0.4, 0.4, 0.5)
    if ia > 0:
        _draw_inset(fr, t, r if show_ball else 0.0, ia)
    _draw_filmstrip(fr, t, a)


def _draw_inset(fr, t, r, a):
    x, y, w, h = 1430.0, 110.0, 400.0, 300.0
    hud.glass_card(fr, x, y, w, h, a)
    fr.text("creature's view", x + w / 2, y + h - 22, "sans", 24, 600, "muted", a)
    cx, cy = x + w / 2 + 50, y + h / 2 - 16
    fr.line(x + 30, cy, x + w - 30, cy, "#2C3B55", 1.0, 0.6 * a)
    _creature(fr, x + 90, cy, 22, a)
    if r > 0.005:
        px = r * 80
        fr.circle(cx, cy, px, "w", 2.6, a, glow=1.0)
        fr.circle(cx, cy, px, "w", alpha=0.18 * a, fill=True)
    elif t < T["dot"]:
        fr.text("nothing yet", cx, cy + 8, "sans", 22, 500, "muted", 0.7 * a)


def _draw_filmstrip(fr, t, a):
    fa = env(t, T["slice"] - 0.15, T["s15"] + 0.4, 0.4, 0.5) * a
    if fa <= 0.003:
        return
    glow = pulse(t, T["sphere"] - 0.05, 0.8)
    y = 960.0
    fr.line(520, y, 1400, y, "w", 2.0, fa, glow=0.5)
    hud.arrow_head(fr, 1300, y, 1420, y, "w", fa, 14)
    fr.text("t", 1440, y + 12, "italic", 36, 500, "w", fa)
    for k in range(7):
        h = R_BALL - 2 * R_BALL * k / 6
        r = section_r(h) * 34
        cx = 560 + k * 130
        u = smooth(lin(t, T["slice"] - 0.1 + 0.06 * k, T["slice"] + 0.2 + 0.06 * k)) * fa
        if r < 1:
            fr.glow_dot(cx, y - 40, 3.0, "w", u, 0.6)
        else:
            fr.circle(cx, y - 40, r, "w", 2.2, u, glow=0.5 + glow)
        fr.line(cx, y - 6, cx, y + 6, "w", 1.4, u)


# ------------------------------------------------------------------ S15: a 4D ball through our space

R4 = 1.6


def w_of(t):
    keys = [(T["tiny"] - 0.25, -0.995 * R4), (T["swelling"], 0.0), (T["gone"], 0.995 * R4)]
    if t <= keys[0][0]:
        return -R4 * 1.05
    if t >= keys[-1][0]:
        return R4 * 1.05 if t > keys[-1][0] + 0.1 else keys[-1][1]
    for (t0, w0), (t1, w1) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp(w0, w1, ease_io(lin(t, t0, t1)))
    return keys[-1][1]


def draw_s15(fr, t):
    a = env(t, T["s15"] - 0.2, END - 18.0, 0.6, 0.6) if t < T["s16"] else 0.0
    if a <= 0.003:
        return
    rack = smooth(lin(t, T["playing"] - 0.3, T["playing"] + 0.6))
    cam = cam_sheet(t)
    room = smooth(lin(t, T["s15"] + 0.2, T["s15"] + 1.2)) * (1 - rack)
    with fr.blurred(7.0 * rack):
        if room > 0:
            b = np.array([[x, y, z] for x in (-3.0, 3.0) for y in (-1.6, 2.6) for z in (-2.4, 2.4)])
            xs, ys, _ = cam.project(b)
            for i in range(8):
                for j in range(i + 1, 8):
                    if bin(i ^ j).count("1") == 1:
                        fr.line(xs[i], ys[i], xs[j], ys[j], "ink", 1.2, 0.3 * room * a)
            fr.text(
                "our space",
                float(xs[1]) + 10,
                float(ys[1]) - 14,
                "sans",
                26,
                600,
                "muted",
                0.8 * room * a,
                align="left",
            )
            w = w_of(t)
            r = math.sqrt(max(0.0, R4**2 - w**2))
            if r > 0.01:
                sph = solids.sphere((0.0, 0.5, 0.0), r, 72)
                rgba = pvr.render(
                    [(sph, pvr.GLASS | dict(color=TOKENS["w"], opacity=0.42, smooth_shading=True))],
                    cam,
                    pv_size(fr),
                    cache="ch3_ball4",
                )
                pvr.composite(fr, rgba, room * a)
                sx, sy, sz = cam.project(np.array([[0.0, 0.5, 0.0]]))
                pr = r * FOCAL / float(sz[0])
                fr.circle(float(sx[0]), float(sy[0]), pr, "w", 2.0, room * a * 0.8, glow=0.7)
            _draw_slider(fr, t, w, room * a)
    _draw_block(fr, t, rack * a)


def _draw_slider(fr, t, w, a):
    """The w slider: a blue track, the profile r(w) = sqrt(R^2 - w^2), the marker and live readouts."""
    x0, x1, y = 560.0, 1360.0, 960.0
    k = (x1 - x0) / (2 * R4 * 1.2)
    fr.line(x0, y, x1, y, "w", 2.0, a, glow=0.4)
    fr.text("w", x1 + 26, y + 12, "italic", 38, 500, "w", a)
    ws = np.linspace(-R4, R4, 81)
    xs = (x0 + x1) / 2 + ws * k
    ky = 0.42 * k  # the profile is drawn shallow so it sits under the room
    ys = y - np.sqrt(np.maximum(0.0, R4**2 - ws**2)) * ky
    fr.poly(xs, ys, "w", 1.6, 0.6 * a)
    mx = (x0 + x1) / 2 + float(np.clip(w, -R4 * 1.2, R4 * 1.2)) * k
    r = math.sqrt(max(0.0, R4**2 - w**2))
    fr.line(mx, y, mx, y - r * ky, "ink", 1.6, a, glow=0.5)
    fr.glow_dot(mx, y, 7, "w", a, 1.4)
    fr.glow_dot(mx, y - r * ky, 5, "ink", a * (r > 0.01), 1.0)
    typmath.draw(fr, "r = sqrt(R^2 - w^2)", 1600, 800, 44, alpha=a)
    hud.readout(fr, 1560, 900, "w", f"{w / R4:+.2f}", "w", a, size=30)
    hud.readout(fr, 1560, 960, "r", f"{r / R4:.2f}", "ink", a, size=30)


BLOCK = CheetahBlock(center=(0.0, 0.0, 0.0))


def _draw_block(fr, t, a):
    if a <= 0.003:
        return
    cam = orbit((0.0, -0.1, 0.0), 10.4, 0.26, -0.80, focal=FOCAL, center=(960.0, 500.0))
    f = playback_frame(t, T["playing"] + 0.2, T["block_end"])
    flash = pulse(t, T["one_slice"] - 0.05, 0.6)
    outline = env(t, T["block"] - 0.1, T["block_end"] + 0.5, 0.3, 0.4)
    BLOCK.draw(
        fr,
        cam,
        t,
        unfold=1.0,
        hold=1,
        active=f,
        volume=a,
        active_alpha=a,
        slice_alpha=a * (1 + flash),
        outline=0.2 * a + 0.8 * outline * a,
    )
    BLOCK.draw_axes(fr, cam, alpha=a)
    pa = env(t, T["block"] + 0.4, T["s16"] + 0.1, 0.3, 0.3)
    if pa > 0:
        hud.pill(fr, 760, 960, "sphere → circles", "w", pa, size=26)
        hud.pill(fr, 1160, 960, "block → frames", "w", pa, size=26)


# ------------------------------------------------------------------ S16: corner-first slices


def s_of(t):
    keys = [
        (T["corner"] - 0.1, 0.02),
        (T["tetra"] + 0.1, 0.6),
        (T["grows"] - 0.1, 0.8),
        (T["clipped_end"], 1.5),
        (T["middle"], 2.0),
        (T["reverse"] - 0.1, 2.0),
        (T["reverse_end"] + 0.4, 3.98),
    ]
    if t <= keys[0][0]:
        return 0.0
    for (t0, s0), (t1, s1) in zip(keys, keys[1:]):
        if t <= t1:
            return lerp(s0, s1, ease_io(lin(t, t0, t1)))
    return 4.0


@lru_cache(maxsize=1)
def lead_angles():
    """Camera elevation and azimuth that look at the rig with vertex 0000 nearest (it leads the cut)."""
    p3, _ = T4.project_persp(T4.C, D4)
    v = T4.place(p3)[T4.index_of("0000")]
    d = v / np.linalg.norm(v)
    elev = math.asin(d[1])
    azim = math.atan2(d[0], -d[2])
    return elev, azim


def rig_cam(t):
    le, la = lead_angles()
    u = ease_io(lin(t, T["s16"] + 0.6, T["stranger"] + 0.8))
    tilt = 0.25 * ease_io(lin(t, T["angle"] - 0.2, T["angle"] + 0.8))
    return orbit(
        (0, 0, 0), 11.5, lerp(0.3, 0.8 * le, u) + tilt, lerp(-0.6, la + 0.35, u), focal=FOCAL, center=(540.0, 500.0)
    )


def stage_cam(t, center=(1380.0, 470.0), dist=6.8):
    return orbit((0, 0, 0), dist, 0.32, 0.4 + 0.22 * (t - T["s16"]), focal=FOCAL, center=center)


def slice_world(s, scale=1.45):
    pts, loops = T4.corner_slice(max(1e-3, min(3.999, s)))
    return pts * scale, loops


def split_pyramids(pts, sep):
    """The octahedron as two square pyramids (local y up), pulled apart by ``sep``."""
    top = pts[pts[:, 1] >= -1e-6] + np.array([0, sep, 0])
    bot = pts[pts[:, 1] <= 1e-6] - np.array([0, sep, 0])
    out = []
    for half in (top, bot):
        hull = ConvexHull(half)
        faces = {}
        for simplex, eq in zip(hull.simplices, hull.equations):
            faces.setdefault(tuple(np.round(eq, 6)), set()).update(simplex.tolist())
        loops = []
        for key, idx in faces.items():
            idx = list(idx)
            n = np.array(key[:3])
            c = half[idx].mean(0)
            u = half[idx[0]] - c
            u /= np.linalg.norm(u)
            v = np.cross(n, u)
            loops.append([idx[k] for k in np.argsort([math.atan2((half[k] - c) @ v, (half[k] - c) @ u) for k in idx])])
        out.append((half, loops))
    return out


def draw_s16(fr, t):
    a = env(t, T["s16"] - 0.3, END + 0.5, 0.6, 0.01)
    if a <= 0.003:
        return
    film = smooth(lin(t, T["same"] - 0.2, T["same"] + 0.6))
    main = a * (1 - film)
    s = s_of(t)
    if main > 0.003:
        # left: the rig, vertices lit by which side of the hyperplane they are on, blue dots where it cuts the edges
        cam = rig_cam(t)
        p3, _ = T4.project_persp(T4.C, D4)
        world = T4.place(p3, scale=1.05)
        T4.draw(fr, cam, world, 0.55 * main, width=1.8, glow=0.35)
        xs, ys, _ = cam.project(world)
        sums = T4.V.sum(1)
        for v in range(16):
            lit = sums[v] < s
            fr.glow_dot(xs[v], ys[v], 6.0 if lit else 3.5, "w" if lit else "muted", main, 0.9 if lit else 0.2)
        for i, j, _ in T4.EDGES:
            si, sj = sums[i], sums[j]
            if min(si, sj) < s < max(si, sj):
                u = (s - si) / (sj - si)
                p = lerp(world[i], world[j], u)
                qx, qy, _ = cam.project(p[None])
                fr.glow_dot(float(qx[0]), float(qy[0]), 4.5, "#ffffff", main, 1.6)
        lt = smooth(lin(t, T["stranger"] - 0.2, T["stranger"] + 0.6)) * main
        i0 = T4.index_of("0000")
        fr.text("0000", xs[i0] - 16, ys[i0] + 40, "sans", 28, 700, "w", lt, align="right", glow=0.4)
        # right: the real slice solid
        _draw_solid_stage(fr, t, s, main)
        # the s slider
        _draw_s_slider(fr, s, main)
    if film > 0.003:
        _draw_compare(fr, t, film * a)


def _draw_solid_stage(fr, t, s, a):
    if not (0.0 < s < 4.0):
        return
    cam = stage_cam(t)
    pts, loops = slice_world(s, 1.25)
    sep = 0.42 * env(t, T["two_pyr"] - 0.1, T["base"] + 0.4, 0.6, 0.6)
    octa = abs(s - 2.0) < 1e-3
    parts = split_pyramids(pts, sep) if octa and sep > 1e-3 else [(pts, loops)]
    meshes = [(solids.convex_solid(p, lp), pvr.GLASS) for p, lp in parts]
    rgba = pvr.render(meshes, cam, pv_size(fr), cache="ch3_slices")
    pvr.composite(fr, rgba, a)
    hero = pulse(t, T["octa"] - 0.05, 1.2)
    sweep = lin(t, T["octa"] - 0.05, T["octa"] + 0.8) if octa else None
    clip_flash = env(t, T["clipped"] - 0.1, T["clipped_end"] + 0.4, 0.2, 0.4)
    for p, lp in parts:
        T4.draw_solid(fr, cam, p, lp, "w", a, fill=0.0, width=2.6 + 1.2 * hero, glow=0.9 + 1.0 * hero, sweep=sweep)
        if clip_flash > 0:  # the new hexagonal faces left by the clipped corners
            xs, ys, _ = cam.project(p)
            for loop in lp:
                if len(loop) == 6:
                    q = skia.Path()
                    q.addPoly([skia.Point(float(xs[k]), float(ys[k])) for k in loop], True)
                    fr.path_fill(q, "#ffffff", 0.10 * clip_flash * a, glow=0.3)
    if sep > 1e-3:  # the shared square base, outlined in ink
        sq = pts[np.abs(pts[:, 1]) < 1e-6]
        c = sq.mean(0)
        order = np.argsort([math.atan2(q[2] - c[2], q[0] - c[0]) for q in sq])
        ring = sq[order]
        for off in (sep, -sep):
            r = ring + np.array([0, off, 0])
            xs, ys, _ = cam.project(np.vstack([r, r[:1]]))
            fr.poly(xs, ys, "ink", 2.4, a * smooth(lin(sep, 0.0, 0.3)), glow=0.6)
    fr.chroma(chroma_kick(t, T["octa"], 5.0))
    # name of the current solid
    name = "tetrahedron" if s <= 1.0 or s >= 3.0 else ("octahedron" if octa else "truncated tetrahedron")
    na = smooth(lin(t, T["tetra"] - 0.1, T["tetra"] + 0.4)) * a
    hud.pill(fr, 1380, 820, name, "w", na, size=28)
    pa = env(t, T["pyramid"] - 0.1, T["grows"], 0.3, 0.4) * a
    fr.text("a triangular pyramid", 1380, 872, "sans", 26, 600, "muted", pa)


def _draw_s_slider(fr, s, a):
    x0, x1, y = 1130.0, 1630.0, 930.0
    fr.line(x0, y, x1, y, "w", 2.0, a, glow=0.3)
    for k in range(5):
        x = x0 + (x1 - x0) * k / 4
        fr.line(x, y - 8, x, y + 8, "w", 1.4, a)
        typmath.number(fr, str(k), x, y + 32, 26, "muted", a)
    mx = x0 + (x1 - x0) * float(np.clip(s, 0, 4)) / 4
    fr.glow_dot(mx, y, 8, "#ffffff", a, 1.4)
    hud.readout(fr, 1380, 1010, "s = x + y + z + w", f"{s:.2f}", "w", a, size=30)


def _draw_compare(fr, t, a):
    """Same object, different slices: face-first (always a cube) vs corner-first (it changes shape)."""
    tilt = 0.35 * ease_io(lin(t, T["angle"] - 0.2, T["angle"] + 0.8))
    fr.text("face first", 210, 360, "sans", 30, 600, "muted", a, align="left")
    fr.text("corner first", 210, 720, "sans", 30, 600, "muted", a, align="left")
    cube = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float) * 0.62
    for k, s in enumerate((0.6, 1.5, 2.0, 2.5, 3.4)):
        cx = 620 + k * 270
        u = smooth(lin(t, T["same"] + 0.08 * k, T["same"] + 0.08 * k + 0.4)) * a
        if u <= 0.003:
            continue
        cam_top = orbit((0, 0, 0), 11.0, 0.35 + tilt, 0.5 + 0.2 * t, focal=FOCAL, center=(cx, 340.0))
        xs, ys, _ = cam_top.project(cube)
        for i in range(8):
            for j in range(i + 1, 8):
                if bin(i ^ j).count("1") == 1:
                    fr.line(xs[i], ys[i], xs[j], ys[j], "w", 2.0, u, glow=0.4)
        cam_bot = orbit((0, 0, 0), 11.0, 0.35 + tilt, 0.5 + 0.2 * t, focal=FOCAL, center=(cx, 700.0))
        pts, loops = slice_world(s, 1.05)
        T4.draw_solid(fr, cam_bot, pts, loops, "w", u, fill=0.14, width=2.0, glow=0.5)
        typmath.draw(fr, f"s = {s:g}", cx, 870, 30, color="muted", alpha=u)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_s13(fr, t)
    draw_s14(fr, t)
    draw_s15(fr, t)
    draw_s16(fr, t)
    hud.eyebrow(fr, t, "03 · SLICES", START + 0.15)
    fr.vignette(0.5)
    fr.grain(t, 0.045)
    return fr.finish()


def blur_weight(t):
    return env(t, T["pieces"] - 0.2, T["pieces"] + 1.0, 0.2, 0.3)


def draw(t, size):
    t = t + START
    return motion_blur(draw_one, t, size, weight=blur_weight(t))


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch3:{Path(__file__).stat().st_mtime_ns}"
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
    219.5,
    221.6,
    223.9,
    225.3,
    226.8,
    230.0,
    231.6,
    233.4,
    234.9,
    235.6,
    238.3,
    240.5,
    243.6,
    245.3,
    246.3,
    249.6,
    251.7,
    253.3,
    255.5,
    258.3,
    260.6,
    263.4,
    265.5,
    266.7,
    268.4,
    270.9,
    273.0,
    276.2,
]
