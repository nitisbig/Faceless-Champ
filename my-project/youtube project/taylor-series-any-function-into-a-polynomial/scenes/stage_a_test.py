"""Stage A component sheet (not part of the film): every shared component and finish effect, 24 s.

 0-4   TaylorStage on cos: P0 → P2 → P4 hugs (spring, glow pulse, light sweep, brackets), Derivative Ladder, colored P4
 4-8   TaylorStage on sin (π ticks): P5 → P7 hug, error band, blue probe at 0.5, ×200 loupe, Digit Lock, Horner tally
 8-12  The Chip running the × / + program for sin 0.5; title-card serif test (A: Typst New Computer Modern, B: Cormorant)
12-16  Term Stack (2.5D): cos terms on floating panels, camera swings to the front and the panels merge into P6
16-20  Complex plane: domain coloring of 1/(1+z²), circle of convergence, poles ±i with the chroma kick; pendulum pair
20-24  PyVista: the |f| pole surface (domain-colored), then the loss surface with its Hessian bowl

    python render.py --chapter test --stills
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from components import taylor as T
from components.chip import Chip
from components.digits import lock
from components.ladder import Ladder
from components.motion import enter
from components.pendulum import Pendulums, draw_pendulum, trail
from components.plane import ComplexPlane
from components.stack25d import TermStack, terms_of
from components.stage import TaylorStage
from theme import PV_CACHE, THEME, H, W

from faceless_champ.draw import Frame, chroma_kick, ease_io, ease_out, env, hud, lin, smooth, text_path
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc
from faceless_champ.draw.space import orbit

DURATION = 24.0
OFFSET = 0.0
STILLS = [1.75, 3.6, 5.4, 7.6, 9.6, 11.6, 13.0, 15.7, 17.4, 19.3, 21.0, 23.4]

X = tc("x", "x")


def minus():
    return tc("minus", "-")


def plus():
    return tc("plus", "+")


def fact(s):
    return tc("fact", s)


# ------------------------------------------------------------------ 0-4: the hug on cos

COS = TaylorStage("cos", view=(-4.2, 4.2, -1.7, 1.7), rect=(96, 170, 1120, 760))
LADDER = Ladder(x=1320, y=170, rows=5, title="DERIVATIVES AT 0")
COS_D = T.derivs_at("cos", 0, 4)
P4 = f"P_4 = 1 {minus()} {X}^2 / {fact('2')} {plus()} {X}^4 / {fact('24')}"


def seg_cos(fr, t):
    a = env(t, 0.0, 4.0, 0.01, 0.3)
    if a <= 0:
        return
    COS.static(fr, a)
    COS.original(fr, a, reveal=ease_io(lin(t, 0.0, 0.7)))
    if t < 1.0:
        c = T.coeffs("cos", 0)
        COS.error_band(fr, c, a * enter(t, 0.6))
        COS.copy(fr, c, a, reveal=enter(t, 0.6, 0.4), sym=True)
        COS.brackets(fr, COS.zone(0), a * enter(t, 0.75))
    elif t < 2.4:
        COS.hug(fr, t, 0, 2, 1.0, a)
    else:
        COS.hug(fr, t, 2, 4, 2.4, a)
    fills = [(0.7, COS_D[0]), (1.05, COS_D[1]), (1.3, COS_D[2]), (2.45, COS_D[3]), (2.7, COS_D[4])]
    LADDER.draw(fr, t, fills, struck={1: 3.1, 3: 3.25}, alpha=a * enter(t, 0.2), focus=4 if t > 2.4 else 2)
    typmath.draw(fr, P4, 1540, 690, 46, None, a * enter(t, 2.9), glow=0.15)
    hud.eyebrow(fr, t, "02 · COPYING A CURVE", 0.1, hold=3.4)


# ------------------------------------------------------------------ 4-8: sin, probe, loupe, digit lock

SIN = TaylorStage("sin", view=(-7.2, 7.2, -2.2, 2.2), rect=(96, 150, 1728, 560), pi_ticks=True)
SIN_TOTAL = f"{float(T.evaluate(T.coeffs('sin', 5), 0.5)):.6f}"
SIN_TRUE = f"{math.floor(math.sin(0.5) * 1e6) / 1e6:.6f}"
PROG = T.ops(T.coeffs("sin", 5), 0.5)


def seg_sin(fr, t):
    a = env(t, 4.0, 8.0, 0.3, 0.3)
    if a <= 0:
        return
    SIN.static(fr, a)
    SIN.original(fr, a)
    if t < 4.6:
        SIN.error_band(fr, T.coeffs("sin", 5), a)
        SIN.copy(fr, T.coeffs("sin", 5), a)
        SIN.brackets(fr, SIN.zone(5), a)
    else:
        SIN.hug(fr, t, 5, 7, 4.6, a)
    y = math.sin(0.5)
    SIN.probe(fr, 0.5, a * enter(t, 4.9), label=f"{X} = 0.5", y=y)
    c3 = T.coeffs("sin", 3)

    def inside(sub):
        SIN.original(fr, a, ax=sub, width=2.5)
        SIN.copy(fr, c3, a, ax=sub, width=4.0, glow=0.5)

    la = a * enter(t, 5.3)
    if la > 0.003:
        SIN.loupe(fr, (0.5, y), 200, (1560, 330), 120, inside, la)
    # digit lock: the three-term total against the true value
    n = len(SIN_TOTAL)
    shown = int(min(n, max(0, (t - 5.8) / 0.18)))
    if shown:
        lock(fr, SIN_TOTAL[:shown], SIN_TRUE, 1180, 880, 64, a, align="left")
        lock(fr, SIN_TRUE, SIN_TRUE, 1180, 960, 34, a * 0.8 * enter(t, 6.2), align="left", locked="muted")
        hud.pill(fr, 1095, 860, "sin 0.5", "x", a * enter(t, 5.8), 22)
    # Horner tally: × × + × + ×
    for i, step in enumerate(PROG):
        on = smooth(lin(t, 6.0 + 0.22 * i, 6.2 + 0.22 * i))
        token = "fact" if step["op"] == "×" else "plus"
        hud.pill(
            fr, 240 + 86 * i, 900, step["op"], token, a * (0.35 + 0.65 * on), 28, fill=0.08 + 0.3 * on, glow=0.4 * on
        )
    fr.text("4 ×   2 +", 240, 980, "sans", 28, 600, "muted", a * enter(t, 7.4), align="left")
    hud.eyebrow(fr, t, "06 · WRAPPING THE SINE", 4.3, hold=3.4)


# ------------------------------------------------------------------ 8-12: chip and the title-card test

CHIP = Chip(cx=540, cy=560, size=440)
TITLE = "The Taylor Series"


def seg_chip(fr, t):
    a = env(t, 8.0, 12.0, 0.3, 0.3)
    if a <= 0:
        return
    k = math.floor((t - 8.4) / 0.45)  # negative before the program starts
    active, display = {}, "0.5"
    if 0 <= k < len(PROG):
        u = (t - 8.4) / 0.45 - k
        active = {PROG[k]["op"]: math.sin(math.pi * min(1, u * 1.4)) ** 0.7}
    if k >= 0:
        display = f"{PROG[min(k, len(PROG) - 1)]['value']:.6f}"
    done = k >= len(PROG)
    CHIP.draw(fr, t, a, display=display, active=active, display_color="result" if done else "ink")
    # title card test: serif on slate, pushed into frame
    for i, (label, y) in enumerate((("A · TYPST NEW COMPUTER MODERN", 360), ("B · CORMORANT GARAMOND", 720))):
        u = ease_out(lin(t, 8.4 + 0.3 * i, 9.4 + 0.3 * i))
        s = 0.94 + 0.06 * u
        fr.rrect(1060, y - 170, 760, 300, 18, fill="slate", alpha=a * u)
        fr.text(label, 1100, y - 128, "sans", 22, 700, "muted", a * u, align="left", tracking=0.22)
        if i == 0:
            expr = f'#text(font: "New Computer Modern")[{TITLE}]'
            typmath.draw(fr, expr, 1440, y, 84 * s, "ink", a * u)
        else:
            fr.text(TITLE, 1440, y + 30, "serif", 100 * s, 600, "ink", a * u)
    fr.light_sweep(text_path(TITLE, 1440, 750, "serif", 100, 600), lin(t, 10.4, 11.4), 0.8)


# ------------------------------------------------------------------ 12-16: term stack (2.5D)

STACK = TermStack(
    terms_of("cos", 6),
    view=(-3.2, 3.2, -1.6, 1.6),
    labels=[
        "1",
        f"{minus()} {X}^2 / {fact('2!')}",
        f"{plus()} {X}^4 / {fact('4!')}",
        f"{minus()} {X}^6 / {fact('6!')}",
    ],
)


def seg_stack(fr, t):
    a = env(t, 12.0, 16.0, 0.3, 0.3)
    if a <= 0:
        return
    u = ease_io(lin(t, 12.0, 15.0))
    cam = orbit((0.0, 0.0, 0.0), 15.0 - 3.0 * u, 0.42 * (1 - u), -0.85 * (1 - u), focal=1100.0, center=(960.0, 560.0))
    merge = lin(t, 14.0, 15.3)
    STACK.draw(fr, cam, merge=merge, alpha=a)
    if merge > 0.9:
        xs = np.linspace(STACK.x0, STACK.x1, 240)
        P = STACK.world(xs, np.clip(np.cos(xs), STACK.y0, STACK.y1), STACK.z(0, merge))
        px, py, _ = cam.project(P)
        fr.poly(px, py, "original", 2.5, a * smooth(lin(merge, 0.9, 1.0)))
    hud.eyebrow(fr, t, "04 · THE RECIPE", 12.3, hold=3.4)


# ------------------------------------------------------------------ 16-20: complex plane and pendulums

PLANE = ComplexPlane(center=(600, 560), unit=165, extent=(-2.6, 2.6, -2.2, 2.2))
PEND = Pendulums(theta0=0.35)


def seg_plane(fr, t):
    a = env(t, 16.0, 20.0, 0.3, 0.3)
    if a <= 0:
        return
    PLANE.domain(fr, "hill", a * 0.55 * enter(t, 16.2, 0.8))
    PLANE.draw(fr, a)
    PLANE.disk(fr, 1.0, ease_io(lin(t, 16.8, 17.8)), a)
    s = smooth(lin(t, 18.0, 18.3))
    for z in (1j, -1j):
        PLANE.pole(fr, z, strength=s * (1 + 0.3 * math.sin(6 * t)), alpha=a * s)
    fr.chroma(chroma_kick(t, 18.1))
    typmath.draw(fr, "R = 1", 600, 1000, 40, "circle", a * enter(t, 17.8))
    # pendulums: exact (ink) and small-angle (gold copy)
    pivot = (1460.0, 230.0)
    tau = t - 16.0
    ex, sm = PEND.angles(tau)
    trail(fr, pivot, 420, [PEND.exact(tau - 0.03 * k) for k in range(24, 0, -1)], "circle", a * 0.7)
    draw_pendulum(fr, pivot, 420, sm, "copy", a * 0.8, r=16)
    draw_pendulum(fr, pivot, 420, ex, "original", a, r=12)
    hud.readout(fr, 1460, 820, "θ₀", "20°", "ink", a)
    typmath.draw(fr, f"sin {tc('x', 'theta')} approx {tc('x', 'theta')}", 1460, 920, 44, None, a * enter(t, 16.6))
    hud.eyebrow(fr, t, "07 · WHERE IT BREAKS", 16.3, hold=3.4)


# ------------------------------------------------------------------ 20-24: PyVista

BOWL_AT = (0.7, -1.28)


def seg_pv(fr, t):
    a = env(t, 20.0, 24.0, 0.3, 0.01)
    if a <= 0:
        return
    from pv3d import surfaces as S

    from faceless_champ.draw import mesh3d as pv3

    size = pv3.frame_size(fr)
    if t < 22.0:
        cam = orbit((0.0, 0.7, 0.0), 9.5, 0.55, 0.55 + 0.06 * (t - 20.0), focal=1150.0, center=(960.0, 600.0))
        rgba = pv3.render([(S.pole_surface(1.0), S.surface_style())], cam, size, cache="stage_a_poles", root=PV_CACHE)
        pv3.composite(fr, rgba, a)
        for z in (1, -1):
            xs, ys, _ = cam.project(np.array([[0.0, 3.25, float(z)]]))
            fr.glow_dot(float(xs[0]), float(ys[0]), 7, "alert", a, 1.2)
        typmath.draw(fr, "abs(1/(1 + z^2))", 960, 140, 48, "ink", a)
    else:
        b = smooth(lin(t, 22.0, 22.4))
        cam = orbit((0.3, 0.4, -0.4), 9.0, 0.62, -0.5 + 0.05 * (t - 22.0), focal=1150.0, center=(960.0, 620.0))
        meshes = [
            (S.loss_surface(), pv3.gloss("#2A3346")),
            (S.hessian_bowl(BOWL_AT), pv3.glass("copy", opacity=0.55, smooth_shading=True)),
        ]
        rgba = pv3.render(meshes, cam, size, cache="stage_a_loss", root=PV_CACHE)
        pv3.composite(fr, rgba, a * b)
        f0 = float(S.loss(*BOWL_AT))
        xs, ys, _ = cam.project(np.array([[BOWL_AT[0], f0 + 0.03, BOWL_AT[1]]]))
        fr.glow_dot(float(xs[0]), float(ys[0]), 7, "x", a * b, 1.0)
        fr.text("A SIMPLE BOWL", 960, 140, "sans", 22, 700, "muted", a * b, tracking=0.22)


# ------------------------------------------------------------------ assembly


def draw(t, size):
    fr = Frame(size)
    seg_cos(fr, t)
    seg_sin(fr, t)
    seg_chip(fr, t)
    seg_stack(fr, t)
    seg_plane(fr, t)
    seg_pv(fr, t)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def build(audio: bool = False):
    from faceless_champ import FunctionSource, Scene

    key = f"stage_a:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=DURATION, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(DURATION)
    return scene
