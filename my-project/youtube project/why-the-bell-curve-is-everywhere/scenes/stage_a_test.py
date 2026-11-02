"""Stage A component sheet (not part of the film): every shared component and finish effect, 20 s.

 0-4   Galton Board: 1,000-ball pour (locked seed) with a speed ramp, hero ball and trail, bell snap on the pile
 4-8   10-row board: additive path light, Pascal counts, one teal/orange route, ghost fan, 2^10 chip
 8-12  Histogram: exact 1 die -> 2 dice -> 10 dice morphs (mass-preserving), bell snap, ±1σ band and share
12-16  Dart Target: throws, error segments, marginals, pink rings; the coloured Typst pdf; μ/σ dials on a live bell
16-20  Crowd -> 10,000-dot histogram, crack and red tail; PyVista glass die with skia pips, gold Gaussian surface with rings

    python render.py --chapter test --stills
    python scenes/stage_a_test.py --seeds          # re-run the Galton seed search behind galton.SEED_POUR
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import typmath
from components import crowd, hud
from components.bell import Bell, band_share, pdf
from components.darts import Target, draw_dots
from components.dials import dial_pair
from components.galton import Board, binom_row, warp
from components.histogram import Axes, bars_from, die_pmf, draw_bars, label_bars, morph, stagger, sum_pmf
from fx import Frame, chroma_kick, ease_io, ease_out, env, lin, motion_blur, smooth, text_path
from theme import THEME, TOKENS, H, W
from typmath import tc

DURATION = 20.0
OFFSET = 0.0
STILLS = [1.2, 3.8, 5.6, 7.6, 9.4, 11.6, 13.2, 15.6, 17.4, 19.6]

# ------------------------------------------------------------------ 0-4: the pour

POUR = Board(rows=12, n=1000)
POUR_WARP = [(0.0, 1.0), (1.0, 8.0)]
SD12 = math.sqrt(12) / 2
PILE_AX = Axes(cx=POUR.cx, floor=POUR.floor, unit=POUR.dx * SD12,
               hscale=POUR.n * 2 * POUR.ball_r * 0.87 / (POUR.per_layer * SD12) * 1.05)


def draw_pour(fr, t):
    a = env(t, 0.0, 4.0, 0.01, 0.35)
    if a <= 0:
        return
    s = warp(t, POUR_WARP)
    POUR.draw_frame(fr, a, rows_shown=12 * ease_out(lin(t, 0.0, 0.6)) + 0.999, flash=POUR.hit_flash(0, s))
    POUR.draw_balls(fr, s, a, skip=(0,))
    POUR.draw_hero(fr, 0, s, a)
    Bell(PILE_AX, -3.8, 3.8).snap(fr, t, 3.0, alpha=a)
    fr.chroma(chroma_kick(t, 3.6))
    hud.pill(fr, 1500, 140, f"×{8 if t > 1.3 else 1}", "muted", a * smooth(lin(t, 1.0, 1.4)), 22)
    hud.eyebrow(fr, t, "01 · COUNTING PATHS", 0.2)


# ------------------------------------------------------------------ 4-8: path light and routes

TEN = Board(rows=10, cx=620.0, top=200.0, dx=62.0, dy=52.0, n=1, floor=860.0)


def draw_paths(fr, t):
    a = env(t, 4.0, 8.0, 0.35, 0.35)
    if a <= 0:
        return
    TEN.draw_frame(fr, a, funnel=False)
    TEN.draw_path_light(fr, a * smooth(lin(t, 4.3, 5.0)))
    # Pascal counts in the first five rows, under each peg
    for r in range(5):
        row = binom_row(r)
        for k in range(r + 1):
            x, y = TEN.peg(r, k)
            fr.text(str(row[k]), x, y + 22, "sans", 16, 600, "ink", a * smooth(lin(t, 5.0 + 0.1 * r, 5.4 + 0.1 * r)))
    counts = TEN.exact_counts()
    for k, c in enumerate(counts):
        fr.text(str(c), float(TEN.bin_x(k)), TEN.floor + 34, "sans", 18, 600, "muted", a * smooth(lin(t, 5.2, 5.6)))
    typmath.draw(fr, "2^10 = 1024", 620, 120, 44, alpha=a * smooth(lin(t, 4.6, 5.0)))
    # right: one route on a second view of the same board, with a fan of ghost futures
    route = [0, 1, 1, 0, 1, 0, 0, 1, 1, 0]
    TEN2 = Board(rows=10, cx=1400.0, top=200.0, dx=62.0, dy=52.0, n=1, floor=860.0)
    TEN2.draw_frame(fr, a * 0.8, funnel=False)
    TEN2.draw_fan(fr, 3, 2, a * smooth(lin(t, 5.6, 6.2)) * (1 - smooth(lin(t, 6.6, 7.0))))
    TEN2.draw_path(fr, route, ease_io(lin(t, 6.4, 7.6)), a)
    fr.text("L R R L R L L R R L", 1400, 140, "sans", 26, 600, "muted", a * smooth(lin(t, 6.4, 6.8)), tracking=0.1)


# ------------------------------------------------------------------ 8-12: dice morphs

DICE_AX = Axes(cx=960.0, floor=820.0, unit=170.0, hscale=1050.0)
ONE = bars_from(*die_pmf())
TWO = bars_from(*sum_pmf(*die_pmf(), 2))
TEN_DICE = bars_from(*sum_pmf(*die_pmf(), 10))


def draw_dice(fr, t):
    a = env(t, 8.0, 12.0, 0.35, 0.35)
    if a <= 0:
        return
    DICE_AX.floor_line(fr, alpha=a)
    if t < 9.0:
        bars, grow, n, labels = ONE, stagger(t, 8.2, 6, 0.4), 1, [str(int(v)) for v in ONE.values]
    elif t < 10.0:
        bars, grow, n, labels = morph(ONE, TWO, ease_io(lin(t, 9.0, 9.8))), 1.0, 2, None
    else:
        bars, grow, n, labels = morph(TWO, TEN_DICE, ease_io(lin(t, 10.0, 10.8))), 1.0, 10, None
    draw_bars(fr, DICE_AX, bars, a, grow, clip=(-3.6, 3.6), highlight={5: 1.0} if 9.85 < t < 10.0 else None)
    if labels:
        label_bars(fr, DICE_AX, bars, labels, a)
    bell = Bell(DICE_AX)
    bell.band(fr, 1.0, alpha=a, u=lin(t, 11.2, 11.6))
    bell.snap(fr, t, 10.85, alpha=a)
    hud.readout(fr, 960, 180, "dice", f"{n:>2d}", "ball", a)
    share = band_share(1.0) * 100
    hud.readout(fr, 960, 940, "\"within\" 1σ", f"{share:.2f}%", "sigma", a * smooth(lin(t, 11.4, 11.7)))


# ------------------------------------------------------------------ 12-16: darts, formula, dials

TARGET = Target(cx=600.0, cy=430.0, unit=88.0)
FORMULA = (f"f(x) = 1/({tc('sigma', 'sigma')} sqrt(2 {tc('pi', 'pi')})) "
           f"{tc('e', 'e')}^(-(x - {tc('bell', 'mu')})^2 / (2 {tc('sigma', 'sigma')}^2))")
MINI_AX = Axes(cx=1420.0, floor=640.0, unit=70.0, hscale=260.0)


def draw_darts_panel(fr, t):
    a = env(t, 12.0, 16.0, 0.35, 0.35)
    if a <= 0:
        return
    TARGET.draw_board(fr, a, reveal=ease_out(lin(t, 12.0, 12.5)))
    n = TARGET.landed(t, 12.2, 160)
    TARGET.draw_darts(fr, t, 12.2, 160, a)
    TARGET.draw_errors(fr, 7, ease_out(lin(t, 13.2, 13.6)), ease_out(lin(t, 13.6, 14.0)), a)
    TARGET.draw_marginals(fr, n, a * smooth(lin(t, 13.4, 14.0)), gap=26.0, hscale=150.0)
    TARGET.draw_rings(fr, a, u=lin(t, 14.4, 15.4))
    hud.glass_card(fr, 1040, 120, 760, 150, a)
    typmath.draw(fr, FORMULA, 1420, 195, 46, alpha=a, reveal=lin(t, 12.3, 13.3))
    mu = 0.9 * math.sin(2.2 * (t - 13.5)) if t > 13.5 else 0.0
    sigma = 1.0 + 0.45 * math.sin(2.0 * (t - 14.8)) if t > 14.8 else 1.0
    bell = Bell(MINI_AX, -3.6, 3.6)
    MINI_AX.floor_line(fr, alpha=a)
    bell.draw(fr, mu, sigma, alpha=a, fill=0.12)
    bell.mean_line(fr, mu, sigma, alpha=a * 0.8)
    zz = np.linspace(-12, 12, 4001)
    area = float(np.sum(pdf(zz, mu, sigma)) * (zz[1] - zz[0]))
    hud.readout(fr, 1420, 700, "area", f"{area:.3f}", "ink", a * 0.9, 24)
    dial_pair(fr, 1420, 860, mu, sigma, a, active_mu=float(13.5 < t < 14.8), active_sigma=float(t > 14.8))


# ------------------------------------------------------------------ 16-20: crowd, break, PyVista

HEIGHTS = crowd.sample_heights()
PX_CM, DOT_R = 14.0, 1.2  # 1 cm bins of 14 px hold 5 dots of 2.4 px per layer
COLS = int(PX_CM // (2 * DOT_R))
# dot pile height = count / COLS * 2r, and count per 1 cm bin = N * pdf(z) / SD, so in density units:
CM_AX = Axes(cx=520.0, floor=860.0, unit=PX_CM * crowd.SD_CM,
             hscale=len(HEIGHTS) * 2 * DOT_R / (crowd.SD_CM * COLS) * 1.04)


def cm_x(v):
    return CM_AX.cx + (np.asarray(v) - crowd.MEAN_CM) * PX_CM


DOTS = crowd.dot_layout(HEIGHTS, cm_x, bin_w=1.0, r=DOT_R, floor=860.0)
ROW = HEIGHTS[:9]


def draw_crowd_panel(fr, t):
    a = env(t, 16.0, 20.0, 0.35, 0.35)
    if a <= 0:
        return
    u = ease_io(lin(t, 16.6, 17.4))
    for k, h in enumerate(ROW):
        x0 = 170 + k * 85
        fx, fy = DOTS[k]
        x = x0 + (fx - x0) * u
        hp = h * 2.0 * (1 - u)
        crowd.person(fr, x, 860.0 + (fy - 860.0) * u, hp, a * (1 - u), fill=0.08)
    n = int(len(HEIGHTS) * smooth(lin(t, 17.2, 18.0)))
    draw_dots(fr, DOTS[:n], DOT_R, "ball", a)
    hud.tabular(fr, f"{n:,}", 520, 420, 34, "ink", a * smooth(lin(t, 17.2, 17.4)))
    bell = Bell(CM_AX, -3.4, 3.4)
    if t < 18.6:
        bell.snap(fr, t, 18.0, alpha=a)
    else:
        bell.crack(fr, lin(t, 18.6, 19.1), at=0.9, alpha=a)
        bell.tail(fr, lin(t, 18.8, 19.9), at=0.9, alpha=a, reach=6.0)
        fr.chroma(chroma_kick(t, 18.6))
    draw_3d(fr, t, a)


def draw_3d(fr, t, a):
    from pv3d import render as pv3
    from pv3d import solids
    from space import orbit

    cam = orbit((0.0, 0.7, 0.0), 8.0, 0.30, 0.35 + 0.08 * (t - 16.0), focal=1250.0, center=(1460.0, 600.0))
    size = pv3.frame_size(fr)
    if t < 18.0:
        k = ease_out(lin(t, 16.0, 17.8))
        R = solids.rotation(5.0 * (1 - k) + 0.5, 4.0 * (1 - k) + 0.6, 2.5 * (1 - k))
        centre = (0.0, 0.9 + 1.4 * (1 - k) * abs(math.cos(6 * k)), 0.0)
        rgba = pv3.render([(solids.die(centre, 0.9, R), dict(pv3.GLASS, opacity=0.34, smooth_shading=True))], cam, size,
                          cache="stage_a_die")
        pv3.composite(fr, rgba, a)
        for p, nrm, r, _ in solids.pip_points(centre, 0.9, R):
            facing = float(np.dot(nrm, cam.eye - p) / np.linalg.norm(cam.eye - p))
            if facing <= 0.05:
                continue
            xs, ys, z = cam.project(p)
            fr.circle(float(xs[0]), float(ys[0]), cam.focal * r / float(z[0]) * math.sqrt(facing), "ink",
                      alpha=a * min(1.0, facing * 2), fill=True)
    else:
        b = smooth(lin(t, 18.0, 18.4))
        style = {"color": TOKENS["bell"], "opacity": 0.42, "specular": 0.9, "specular_power": 70, "diffuse": 0.75,
                 "ambient": 0.25, "smooth_shading": True}
        rgba = pv3.render([(solids.gaussian_surface(height=2.2, extent=2.4, sigma=0.8), style)], cam, size,
                          cache="stage_a_surface")
        pv3.composite(fr, rgba, a * b)
        th = np.linspace(0, 2 * np.pi, 120)
        radii = (0.3, 0.6, 0.9, 1.2, 1.5, 1.8)
        lit = lin(t, 18.6, 19.6) * (len(radii) + 1)
        for k, r in enumerate(radii):
            ra = a * b * min(1.0, max(0.0, lit - k))
            if ra <= 0.003:
                continue
            pts = np.c_[r * np.cos(th), np.full_like(th, 2.2 * np.exp(-r * r / (2 * 0.64)) + 0.01), r * np.sin(th)]
            xs, ys, _ = cam.project(pts)
            fr.poly(xs, ys, "pi", 2.0, ra, glow=0.6, close=True)
        typmath.draw(fr, f"integral e^(-x^2) dif x = sqrt({tc('pi', 'pi')})", 1460, 950, 48,
                     alpha=a * smooth(lin(t, 19.0, 19.4)))
        title = "THE BELL CURVE"
        fr.text(title, 1460, 150, "display", 56, 600, "ink", a * b, tracking=0.06)
        fr.light_sweep(text_path(title, 1460, 150, "display", 56, 600, tracking=0.06), lin(t, 18.9, 19.8), 0.9)


# ------------------------------------------------------------------ assembly


def draw_one(t, size):
    fr = Frame(size)
    draw_pour(fr, t)
    draw_paths(fr, t)
    draw_dice(fr, t)
    draw_darts_panel(fr, t)
    draw_crowd_panel(fr, t)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return motion_blur(draw_one, t, size, weight=1.0 if t < 4.0 else 0.0)


def build(audio: bool = False):
    from faceless_champ import FunctionSource, Scene

    key = f"stage_a:{Path(__file__).stat().st_mtime_ns}"
    with THEME.use():
        scene = Scene(THEME.canvas())
        source = FunctionSource(draw, size=(W, H), duration=DURATION, key=key)
        scene.add(source.viewport(width=W, height=H, position=(W / 2, H / 2)))
        scene.wait_until(DURATION)
    return scene


def seed_report(rows=12, n=1000, seeds=20_000, top=5):
    """The search behind galton.SEED_POUR: closest to the binomial among monotone (unimodal) pours."""
    p = binom_row(rows) / 2 ** rows
    found = []
    for seed in range(seeds):
        c = np.bincount(np.random.default_rng(seed).integers(0, 2, (n, rows)).sum(1), minlength=rows + 1)
        half = rows // 2
        if all(c[i] <= c[i + 1] for i in range(half)) and all(c[i] >= c[i + 1] for i in range(half, rows)):
            found.append((float(np.abs(c / n - p).max()), int(np.abs(c - c[::-1]).max()), seed, c.tolist()))
    for dev, sym, seed, c in sorted(found)[:top]:
        print(f"seed {seed:>5}  max dev {dev * 100:.2f} pp  asym {sym}  {c}")


if __name__ == "__main__" and "--seeds" in sys.argv:
    seed_report()
