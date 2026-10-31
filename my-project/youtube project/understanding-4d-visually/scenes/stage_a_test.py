"""Stage A component sheet (not part of the film): every shared component and finish effect, 12 s.

 0-3   Tesseract Rig: double rotation (xy + zw), trails, motion blur, glass stats card, dot floor, chroma kick
 3-6   Vector Slot (grows w), ZW Matrix Plaque with live cos/sin and block wash, Typst formula and morph, readouts
 6-9   Corner-first slice solid swept s = 0 -> 4 (real ConvexHull), lit corners on the rig, light sweep at s = 2
 9-12  Cheetah Block with axes and the Blue Slice Plane, light cone and glint, depth-of-field card, title sweep

    python render.py --chapter test --stills
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import typmath
from components import hud
from components import tesseract as T4
from components.cheetah_block import CheetahBlock, playback_frame
from components.matrix_plaque import draw_matrix, zw_rotation_cells
from components.vector_slot import Slot, draw_stream, draw_vector
from fx import Frame, chroma_kick, ease_io, ease_out, env, lin, motion_blur, smooth, text_path
from space import orbit
from theme import THEME, TOKENS, H, W
from typmath import tc

DURATION = 12.0
OFFSET = 0.0
STILLS = [1.0, 2.5, 4.4, 5.6, 7.0, 7.9, 10.0, 11.5]
D4 = 3.0


# ------------------------------------------------------------------ 0-3: the rig


def rig_world(t, center=(0.0, 0.0, 0.0), scale=1.15):
    R = T4.rotation(("xy", 0.35 * t), ("zw", 0.55 * t))
    p3, _ = T4.project_persp(T4.C @ R.T, D4)
    return T4.place(p3, center=center, scale=scale)


def draw_rig_panel(fr, t):
    a = env(t, 0.0, 3.0, 0.35, 0.35)
    if a <= 0:
        return
    cam = orbit((0, 0, 0), 9.0, 0.32, -0.55 + 0.05 * t, focal=1500.0)
    hud.dot_grid(fr, cam, height=-2.4, extent=6.0, alpha=0.12 * a, reveal=ease_out(lin(t, 0.0, 1.2)))
    T4.draw_trails(fr, cam, rig_world, t, span=0.8, steps=16, alpha=0.35 * a)
    world = rig_world(t)
    T4.draw(fr, cam, world, a, width=2.2, glow=0.7, vertices=0.9)
    counts = f"V {len(T4.V)} · E {len(T4.EDGES)} · F {len(T4.SQUARES)} · C {len(T4.CELLS)}"
    hud.glass_card(fr, 1380, 820, 420, 96, a)
    hud.tabular(fr, counts, 1590, 880, 30, "ink", a)
    hud.eyebrow(fr, t, "02 · BUILD A TESSERACT", 0.15)
    fr.chroma(chroma_kick(t, 0.5))


# ------------------------------------------------------------------ 3-6: vector, matrix, formula


def draw_math_panel(fr, t):
    a = env(t, 3.0, 6.0, 0.35, 0.35)
    if a <= 0:
        return
    slots = [Slot("1", "x", underline=1), Slot("2", "y", underline=1), Slot("0", "z", underline=1),
             Slot("3", "w", glow=0.6, underline=1)]
    draw_vector(fr, 300, 470, slots, 54, alpha=a, grow=(3, lin(t, 3.4, 4.0)))
    hud.readout(fr, 300, 760, "length", f"{math.sqrt(14):.3f}", "ink", a)
    theta = 0.9 * (t - 3.0)
    c, s = math.cos(theta), math.sin(theta)
    cells = zw_rotation_cells()
    if t > 4.6:  # live values
        cells = [["1", "0", "0", "0"], ["0", "1", "0", "0"], ["0", "0", f"{c:.2f}", f"{-s:.2f}"],
                 ["0", "0", f"{s:.2f}", f"{c:.2f}"]]
    colors = {(0, 0): "x", (1, 1): "y", (2, 2): "z", (2, 3): "z", (3, 2): "w", (3, 3): "w"}
    zero = {(r, k): 0.35 for r in range(4) for k in range(4) if (r, k) not in colors}
    draw_matrix(fr, 960, 470, cells, colors, cell_w=130, size=40, alpha=a, entry_alpha=zero,
                blocks=[((2, 2, 3, 3), TOKENS["z"], TOKENS["w"], smooth(lin(t, 3.8, 4.4)))])
    hud.readout(fr, 960, 760, "θ", f"{math.degrees(theta) % 360:05.1f}°", "w", a)
    typmath.draw(fr, f"x' = {tc('w', 'd/(d - w)')} dot {tc('x', 'x')}", 1580, 480, 60, alpha=a)
    hud.pill(fr, 1580, 640, "3D → 2D", "ink", a)
    draw_stream(fr, 1820, 1000, 2000, reveal=lin(t, 4.0, 5.8), alpha=a * 0.8, size=24)
    ones = " + ".join(tc(k, "1^2") for k in "xyzw")
    chain = [f"sqrt({ones})", "sqrt(4)", "2"]
    u = lin(t, 4.2, 5.6) * 2
    step = min(1, int(u))
    typmath.morph(fr, chain[step], chain[step + 1], u - step, 960, 900, 72, alpha=a, glow=0.3)


# ------------------------------------------------------------------ 6-9: slices


def draw_slice_panel(fr, t):
    a = env(t, 6.0, 9.0, 0.35, 0.35)
    if a <= 0:
        return
    s = 4.0 * ease_io(lin(t, 6.2, 8.8))
    cam = orbit((0, 0, 0), 8.6, 0.30, -0.6, focal=1500.0, center=(560.0, 540.0))
    world = T4.place(T4.project_persp(T4.C, D4)[0], scale=1.1)
    lit = T4.V.sum(1) <= s
    T4.draw(fr, cam, world, a * 0.55, width=1.6, glow=0.3)
    xs, ys, _ = cam.project(world)
    for i in range(16):
        fr.glow_dot(xs[i], ys[i], 6.0 if lit[i] else 3.5, "w" if lit[i] else "muted", a, 0.9 if lit[i] else 0.2)
    pts, loops = T4.corner_slice(max(1e-3, min(3.999, s)))
    if len(pts):
        cam2 = orbit((0, 0, 0), 5.2, 0.35, 0.5 + 0.2 * t, focal=1500.0, center=(1380.0, 520.0))
        sweep = lin(t, 7.35, 8.0) if 7.3 < t < 8.0 else None
        T4.draw_solid(fr, cam2, T4.place(pts, scale=1.4), loops, "w", a, fill=0.16, sweep=sweep)
    hud.readout(fr, 1380, 900, "s = x + y + z + w", f"{s:.2f}", "w", a)


# ------------------------------------------------------------------ 9-12: block, light, depth of field


BLOCK = CheetahBlock(center=(0.0, 0.0, 0.0))


def draw_block_panel(fr, t):
    a = env(t, 9.0, 12.01, 0.35, 0.01)
    if a <= 0:
        return
    cam = orbit((0, -0.2, 0), 10.0, 0.30, -0.85, focal=1500.0)
    with fr.blurred(6.0 * (1 - smooth(lin(t, 9.0, 10.0)))):
        f = playback_frame(t, 9.6, 11.8)
        BLOCK.draw(fr, cam, t, unfold=ease_out(lin(t, 9.0, 9.8)), active=f, slice_alpha=a, volume=a, fade=a)
        BLOCK.draw_axes(fr, cam, *(ease_io(lin(t, 9.3 + 0.2 * k, 10.1 + 0.2 * k)) for k in range(3)))
    fr.light_cone((1650, 40), (1460, 420), (1840, 420), alpha=0.22 * a)
    fr.glint(1650, 40, 70, a)
    with fr.blurred(5.0):
        hud.glass_card(fr, 120, 760, 360, 200, a * 0.8)
        fr.text("depth of field", 300, 870, "sans", 30, 600, "muted", a * 0.8)
    title = "UNDERSTANDING 4D"
    fr.text(title, 960, 1010, "display", 64, 600, "ink", a, tracking=0.06)
    fr.light_sweep(text_path(title, 960, 1010, "display", 64, 600, tracking=0.06), lin(t, 10.6, 11.6), strength=0.9)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_rig_panel(fr, t)
    draw_math_panel(fr, t)
    draw_slice_panel(fr, t)
    draw_block_panel(fr, t)
    fr.vignette(0.5)
    fr.grain(t, 0.045)
    return fr.finish()


def draw(t, size):
    return motion_blur(draw_one, t, size, weight=1.0 if t < 3.0 else 0.0)


def build(audio: bool = False):
    from faceless_champ import FunctionSource, Scene

    key = f"stage_a:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=DURATION, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(DURATION)
    return scene


_ = np  # numpy is used through the components; kept for interactive poking
