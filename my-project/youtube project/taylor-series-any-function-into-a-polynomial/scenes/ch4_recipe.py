"""CHAPTER 4 · THE RECIPE, 04:45.920 – 05:59.560 (cue #778 "Now," → #987 "Let's").

S20  One recipe              a generic ink curve with a gold copy at 0 -> the ladder rows f(0), f′(0), f″(0), f‴(0), ⋮
                             set on their words, every 0 glows blue ("measured at 0") -> each row label flies into its
                             slot of f(0) + f′(0)x + f″(0)/2! x² + f‴(0)/3! x³ + ⋯ -> sweep on "forever" -> the Σ form
S21  Each term has one job   three small gold plots: x (slope), x² (bend, comb), x³ (the comb flips through 0) -> a punch
                             in on x⁴/24 with a ×40 lens: flat at 0, its rows read 0 0 0 0 +1 -> the cos copy gains x⁴/24
                             while the lens shows nothing move -> the Term Stack: 1, −x²/2, x⁴/24, −x⁶/720 in depth
S22  Series vs polynomial    "Taylor series" over the expanded sum -> a gold cut after x³, the tail to a ghost ->
                             "Taylor polynomial", P₃ -> the hug five times P₂ … P₁₀, brackets ±0.70 … ±3.62
S23  Any center              the blue centre unpins and slides to a = 2, P₄ re-expands there -> the distance x − a and
                             (x − a)ⁿ in the formula -> a sweeps to −1, the copy and its hug zone travel with it

Clean frame: no cards or pills. Formulas are plain Typst, colored by role. One FunctionSource on the narration clock.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import skia
from components import taylor as T
from components.fx import glow_path, layer_alpha
from components.ladder import float_rows
from components.moves import comb, zoom_about
from components.stack25d import TermStack, terms_of
from components.stage import Axes, TaylorStage, clip, curve_path
from cues import AUDIO, beat, cue
from theme import DISPLAY, THEME, H, W

from faceless_champ.draw import Frame, ease_io, ease_out, hud, lin, pulse, smooth, text_path
from faceless_champ.draw import mathtype as typmath
from faceless_champ.draw.mathtype import tc
from faceless_champ.draw.space import orbit
from scenes import ch3_factorials as ch3

START = cue(778)  # 285.92 "Now, we can write the whole trick as a single recipe."
END = cue(987)  # 359.56 "Let's see the recipe pay off"

b = beat

S20, S21, S22, S23 = START, cue(850), cue(921), cue(957)

X = tc("x", "x")
A = tc("x", "a")
PLUS, MINUS = tc("plus", "+"), tc("minus", "-")
Z0 = tc("x", "0")


def F(s):
    return tc("fact", s)


BLUE = "#5fb6ff"
FACT = "#ff3d9a"

# ------------------------------------------------------------------ S20A · a function, then the ladder

G_C = np.array([0.25, 0.88, -0.55125, -0.21970])  # g below: value and derivatives / k! at 0


def g(x):
    return 0.6 * np.sin(1.3 * x) + 0.25 * np.cos(2.1 * x) + 0.1 * x


G_AX = Axes(-5.0, 5.0, -1.6, 1.6, (96.0, 220.0, 1728.0, 640.0))

ROWS = [f"f({Z0})", f"f'({Z0})", f"f''({Z0})", f"f'''({Z0})", "dots.v"]
ROW_T = [b(797), b(800), b(803), b(805), b(808)]  # "value", "first derivative", "second …", "third", "so on"
RX, RY, RH, RS = 260.0, 140.0, 120.0, 66.0


def row_center(k):
    w = typmath.size_of(ROWS[k], RS)[0]
    return RX + 40 + w / 2, RY + RH * (k + 0.5)


def draw_rows(fr, t, a):
    if a <= 0.003:
        return
    blue = smooth(lin(t, b(810), b(810) + 0.4)) * (1 - 0.6 * smooth(lin(t, b(813), b(813) + 0.8)))
    fr.line(
        RX + 12, RY + 10, RX + 12, RY + RH * 5 - 10, "line", 1.0, 0.7 * a * smooth(lin(t, ROW_T[0] - 0.3, ROW_T[0]))
    )
    for k, (lab, t0) in enumerate(zip(ROWS, ROW_T)):
        ra = a * smooth(lin(t, t0, t0 + 0.35))
        if ra <= 0.003:
            continue
        _, cy = row_center(k)
        slide = 30 * (1 - ease_out(lin(t, t0, t0 + 0.5)))
        gs = typmath.glyphs(lab)[0]
        zeros = [i for i, gl in enumerate(gs) if gl.color.lower() == BLUE]
        colors = {i: fr.mix("ink", "x", blue) for i in zeros}
        glows = {i: 0.9 * blue for i in zeros}
        typmath.draw(fr, lab, RX + 40 + slide, cy, RS, None, ra, colors=colors, glows=glows, align="left")
        fr.line(RX + 40, cy + RH / 2 - 8, RX + 560, cy + RH / 2 - 8, "line", 1.0, 0.6 * ra)


def draw_function(fr, t):
    a = smooth(lin(t, b(778), b(778) + 0.5)) * (1 - smooth(lin(t, b(796), b(797) + 0.3)))
    if a <= 0.003:
        return
    ax = G_AX
    fr.line(ax.left, float(ax.py(0)), ax.right, float(ax.py(0)), "axis", 2.0, a)
    fr.line(float(ax.px(0)), ax.top, float(ax.px(0)), ax.bottom, "axis", 1.2, 0.6 * a)
    reveal = ease_io(lin(t, b(778) + 0.2, b(788)))
    xs = np.linspace(ax.x0, ax.x0 + (ax.x1 - ax.x0) * reveal, 500)
    fr.path_stroke(curve_path(ax, xs, g(xs)), "original", 2.5, a, glow=0.15)
    cu = ease_out(lin(t, b(790), b(793) + 0.3))  # "copy a function near 0"
    if cu > 0:
        r = 1.6 * cu
        xs = np.linspace(-r, r, 200)
        with clip(fr, ax.rect):
            fr.path_stroke(curve_path(ax, xs, T.evaluate(G_C, xs)), "copy", 4.0, a, glow=0.6)
        fr.glow_dot(float(ax.px(0)), float(ax.py(G_C[0])), 7.0, "x", a * cu, 1.0)


# ------------------------------------------------------------------ S20B · the recipe builds, row by row

PARTS = [
    "f(0)",
    f"{PLUS} f'(0) {X}",
    f"{PLUS} (f''(0))/{F('2!')} {X}^2",
    f"{PLUS} (f'''(0))/{F('3!')} {X}^3",
    f"{PLUS} dots.c",
]
PARTS5 = PARTS[:4] + [f"{PLUS} (f^((4))(0))/{F('4!')} {X}^4", PARTS[4]]
FORM, FORM5 = " ".join(PARTS), " ".join(PARTS5)


def ranges(parts):
    out, i = [], 0
    for p in parts:
        n = len(typmath.glyphs(p)[0])
        out.append(range(i, i + n))
        i += n
    return out


R4, R5 = ranges(PARTS), ranges(PARTS5)
FY, FS = 880.0, 64.0
LAND = [b(818) + 0.1, b(822), b(828), b(838), b(846)]  # each piece lands as its derivative is named
FLY = 0.55
SUM = f"sum_(n=0)^oo (f^((n))(0))/({F('n!')}) {X}^n"


def piece_center(expr, rng, cx, cy, size, skip_plus=True):
    cs = typmath.glyph_centers(expr, cx, cy, size)
    idx = list(rng)[1:] if skip_plus and len(rng) > 1 else list(rng)
    return tuple(np.mean([cs[i] for i in idx], axis=0))


def draw_recipe(fr, t, a, focus=None):
    """The expanded recipe. ``focus``: {piece index: 0..1} glow (S21)."""
    if a <= 0.003:
        return
    alphas, glows = {}, {}
    fact = [i for i, gl in enumerate(typmath.glyphs(FORM)[0]) if gl.color.lower() == FACT]
    for k, (rng, t0) in enumerate(zip(R4, LAND)):
        u = smooth(lin(t, t0, t0 + 0.35))
        dim = 1.0
        if focus is not None:
            dim = 0.5 + 0.5 * focus.get(k, 0.0)
        for i in rng:
            alphas[i] = u * dim
            if focus and k in focus:
                glows[i] = 0.9 * focus[k]
    for i in fact[:2]:  # "2 factorial"
        glows[i] = max(glows.get(i, 0.0), 1.0 * pulse(t, b(834), 0.9))
    for i in fact[2:4]:  # "3 factorial"
        glows[i] = max(glows.get(i, 0.0), 1.0 * pulse(t, b(844), 0.9))
    typmath.draw(fr, FORM, 960, FY, FS, None, a, glow=0.15, alphas=alphas, glows=glows)
    # each row label flies down into its slot
    for k in range(4):
        u = lin(t, LAND[k] - FLY, LAND[k])
        if 0 < u < 1:
            sx, sy = row_center(k)
            dx, dy = piece_center(FORM, R4[k], 960, FY, FS, skip_plus=k > 0)
            e = ease_io(u)
            x, y = sx + (dx - sx) * e, sy + (dy - sy) * e - 80 * math.sin(math.pi * e)
            typmath.draw(fr, ROWS[k], x, y, RS + (FS - RS) * e, None, a, glow=0.5)
    # "forever": a gold line under the recipe and one sweep along it
    if t >= b(849):
        w, h = typmath.size_of(FORM, FS)
        ul = ease_out(lin(t, b(849), b(849) + 0.6))
        line = skia.Path()
        line.moveTo(960 - w / 2, FY + h * 0.62)
        line.lineTo(960 - w / 2 + w * ul, FY + h * 0.62)
        fr.path_stroke(line, "copy", 3.0, 0.8 * a * (1 - smooth(lin(t, S21, S21 + 0.6))), glow=0.6)
        fr.light_sweep(glow_path(line, 12), lin(t, b(849) + 0.2, b(849) + 1.0), 0.8 * a)


def draw_s20(fr, t):
    if t >= S22:
        return
    draw_function(fr, t)
    draw_rows(fr, t, 1 - smooth(lin(t, b(850), b(850) + 0.5)))
    if t < S21:
        draw_recipe(fr, t, 1.0)
        sa = 0.6 * smooth(lin(t, b(849) + 0.4, b(849) + 1.0))
        typmath.draw(fr, SUM, 1420, 440, 72, None, sa, glow=0.2)


# ------------------------------------------------------------------ S21A · each term has one job

JOBS = [(b(856), b(862)), (b(862), b(869)), (b(869), b(878))]
PLOTS = [480.0, 960.0, 1440.0]
POW = [1, 2, 3]


def draw_jobs(fr, t):
    out = 1 - smooth(lin(t, b(882), b(882) + 0.3))
    if out <= 0.003:
        return
    focus = {}
    for k, (t0, t1) in enumerate(JOBS):
        focus[k + 1] = smooth(lin(t, t0, t0 + 0.3)) * (1 - smooth(lin(t, t1, t1 + 0.3)))
    draw_recipe(fr, t, out, focus=focus)
    for k, (cx, n, (t0, t1)) in enumerate(zip(PLOTS, POW, JOBS)):
        a = out * smooth(lin(t, t0, t0 + 0.4)) * (0.45 + 0.55 * focus[k + 1])
        if a <= 0.003:
            continue
        rise = 24 * (1 - ease_out(lin(t, t0, t0 + 0.5)))
        ax = Axes(-1.6, 1.6, -1.8, 1.8, (cx - 190, 250.0 + rise, 380.0, 300.0))
        fr.line(ax.left, float(ax.py(0)), ax.right, float(ax.py(0)), "axis", 1.6, a)
        fr.line(float(ax.px(0)), ax.top, float(ax.px(0)), ax.bottom, "axis", 1.0, 0.6 * a)
        xs = np.linspace(-1.6, 1.6, 200)
        with clip(fr, ax.rect):
            fr.path_stroke(curve_path(ax, xs, xs**n), "copy", 3.0, a, glow=0.5)
        if n >= 2:  # the bend, and (x³) how the bend changes
            cx_ = np.linspace(-1.15 if n == 2 else -1.0, 1.15 if n == 2 else 1.0, 25)
            d1, d2 = n * cx_ ** (n - 1), n * (n - 1) * cx_ ** (n - 2)
            grow = ease_out(lin(t, t0 + 0.3, t0 + 1.1))
            with clip(fr, ax.rect):
                comb(fr, ax, cx_, cx_**n, d1, d2, "frame", a, scale=60.0, grow=grow)


# ------------------------------------------------------------------ S21B · invisible to the lower derivatives

LEFT = (96.0, 150.0, 1180.0, 780.0)
Q_AX = Axes(-2.4, 2.4, -0.4, 1.6, LEFT)
LENS = (930.0, 330.0)
COS_L = TaylorStage("cos", view=(-3.4, 3.4, -1.6, 1.6), rect=LEFT)
Q_ROWS = ["g(0)", "g'(0)", "g''(0)", "g'''(0)", "g^((4))(0)"]
COS_ROWS = ["f(0)", "f'(0)", "f''(0)", "f'''(0)", "f^((4))(0)"]
COS_V = [tc("plus", "+1"), tc("muted", "0"), tc("minus", "−1"), tc("muted", "0"), tc("plus", "+1")]


def lens(fr, t, src, inside, a, ax):
    r = 130 * ease_out(lin(t, b(890), b(890) + 0.45))
    if r > 1:
        COS_L.loupe(fr, src, 40, LENS, r, inside, a, ax=ax, label=False)


def draw_invisible(fr, t):
    if not b(882) <= t < b(908) + 0.6:
        return
    punch = ease_out(lin(t, b(882), b(882) + 0.4))
    swap = smooth(lin(t, b(897), b(897) + 0.5))
    out = 1 - smooth(lin(t, b(908), b(908) + 0.4))
    # the lone term x⁴/24, punched in
    qa = smooth(punch) * (1 - swap)
    if qa > 0.003:
        with zoom_about(fr, 686, 540, 1.25 - 0.25 * punch):
            ax = Q_AX
            fr.line(ax.left, float(ax.py(0)), ax.right, float(ax.py(0)), "axis", 2.0, qa)
            fr.line(float(ax.px(0)), ax.top, float(ax.px(0)), ax.bottom, "axis", 1.2, 0.6 * qa)
            xs = np.linspace(ax.x0, ax.x1, 300)
            with clip(fr, ax.rect):
                fr.path_stroke(curve_path(ax, xs, xs**4 / 24), "copy", 4.0, qa, glow=0.6)
            typmath.draw(fr, f"{X}^4 / {F('24')}", 300, 260, 64, None, qa)

            def inside(sub):
                fr.line(sub.left - 200, float(sub.py(0)), sub.right + 200, float(sub.py(0)), "axis", 2.0, qa)
                ys = np.linspace(sub.x0, sub.x1, 100)
                fr.path_stroke(curve_path(sub, ys, ys**4 / 24), "copy", 4.0, qa, glow=0.5)

            lens(fr, t, (0.0, 0.0), inside, qa, ax)
        zeros = smooth(lin(t, b(896), b(896) + 0.5))
        rows = []
        for k, lab in enumerate(Q_ROWS):
            fill = smooth(lin(t, b(891) + 0.2 * k, b(891) + 0.2 * k + 0.3))
            val = (tc("plus", "+1") if k == 4 else tc("muted", "0")) if fill > 0 else None
            rows.append((lab, val, (1 - 0.7 * zeros) if k < 4 else 1.0, zeros if k == 4 else 0.0))
        float_rows(fr, 1330.0, 230.0, rows, qa, w=480.0, size=42.0, row_h=78.0)
    # the cos copy gains x⁴/24; inside the lens nothing moves
    ca = swap * out
    if ca > 0.003:
        ax = COS_L.ax
        COS_L.static(fr, ca, labels=False)
        COS_L.original(fr, ca)
        c, _, s = COS_L.chain(t, [2, 4], [b(901)])
        COS_L.error_band(fr, c, 0.6 * ca)
        COS_L.copy(fr, c, ca, glow=0.6 + 0.5 * s)

        def inside(sub):
            COS_L.original(fr, ca, ax=sub)
            COS_L.copy(fr, c, ca, ax=sub, glow=0.5)

        lens(fr, t, (0.0, 1.0), inside, ca, ax)
        lit4 = smooth(lin(t, b(901) + 0.4, b(901) + 0.9))
        rows = [
            (lab, COS_V[k], 1.0 if k < 3 or k == 4 and lit4 > 0 else 0.35, 1.0 if k < 3 else lit4 if k == 4 else 0.0)
            for k, lab in enumerate(COS_ROWS)
        ]
        float_rows(fr, 1330.0, 230.0, rows, ca, w=480.0, size=42.0, row_h=78.0)


# ------------------------------------------------------------------ S21C · stack term after term

STACK = TermStack(
    terms_of("cos", 6),
    view=(-3.2, 3.2, -1.6, 1.6),
    span=8.0,
    gap=3.4,
    height=4.6,
    labels=["1", f"{MINUS} {X}^2 / {F('2')}", f"{X}^4 / {F('24')}", f"{MINUS} {X}^6 / {F('720')}"],
)
STACK_T = [b(910), b(911) + 0.1, b(912) + 0.1, b(913)]
EVEN_ROWS = [
    ("f(0)", tc("plus", "+1")),
    ("f''(0)", tc("minus", "−1")),
    ("f^((4))(0)", tc("plus", "+1")),
    ("f^((6))(0)", tc("minus", "−1")),
]


def draw_stack(fr, t):
    if not b(908) <= t < S22 + 0.5:
        return
    a = smooth(lin(t, b(908) + 0.2, b(908) + 0.6)) * (1 - smooth(lin(t, b(921), b(921) + 0.4)))
    if a <= 0.003:
        return
    azim = 0.52 + 0.1 * ease_io(lin(t, b(908), S22))
    cam = orbit((0.0, 0.0, 0.0), 14.0, 0.26, azim, focal=1100.0, center=(720.0, 490.0))
    appear = [ease_out(lin(t, t0, t0 + 0.5)) for t0 in STACK_T]
    STACK.draw(fr, cam, alpha=a, appear=appear, label_size=40)
    rows = []
    for k, (lab, val) in enumerate(EVEN_ROWS):
        lit = smooth(lin(t, b(918) + 0.3 * k, b(918) + 0.3 * k + 0.3))
        rows.append((lab, val if lit > 0 else None, 0.35 + 0.65 * lit, lit))
    float_rows(fr, 1450.0, 330.0, rows, w=400.0, size=42.0, row_h=78.0, alpha=a * smooth(lin(t, b(913), b(913) + 0.5)))


# ------------------------------------------------------------------ S22 · Taylor series, Taylor polynomial

STAGE = TaylorStage("cos", view=(-5.2, 5.2, -1.7, 1.7), rect=(96.0, 220.0, 1728.0, 760.0))
HUG_DEG = [2, 4, 6, 8, 10, 4]
HUG_T = [b(944) + 0.78 * k for k in range(4)] + [b(957)]  # five hugs out, then back to P₄ for S23
ZONES = [T.hug_zone("cos", n) for n in (2, 4, 6, 8, 10)]
P3 = f"{tc('copy', 'P_3')} ({X}) ="
FORM_A = " ".join(
    [
        f"f({A})",
        f"{PLUS} f'({A}) ({X} {MINUS} {A})",
        f"{PLUS} (f''({A}))/{F('2!')} ({X} {MINUS} {A})^2",
        f"{PLUS} (f'''({A}))/{F('3!')} ({X} {MINUS} {A})^3",
        f"{PLUS} dots.c",
    ]
)


def draw_s22_text(fr, t):
    if t < b(921):
        return
    a = smooth(lin(t, b(921) + 0.2, b(921) + 0.7))
    up = ease_io(lin(t, b(942), b(942) + 0.8))  # the words make room for the graph
    y, size = 560 - 440 * up, 58 - 22 * up
    pre = smooth(lin(t, b(940), b(940) + 0.5))
    shift = 110 * pre * (1 - up)
    cx = 960 + shift
    cut = ease_out(lin(t, b(931), b(931) + 0.5))
    tail = 1 - 0.75 * smooth(lin(t, b(931) + 0.3, b(931) + 0.8))
    alphas = {i: tail for k in (4, 5) for i in R5[k]}
    m = lin(t, b(975), b(975) + 0.8)  # S23: "measuring distances" -> (x − a)ⁿ
    if m > 0:
        typmath.morph(fr, FORM5, FORM_A, m, cx, y, size, a)
    else:
        typmath.draw(fr, FORM5, cx, y, size, None, a, alphas=alphas, glow=0.15)
    w, h = typmath.size_of(FORM5, size)
    if cut > 0 and m <= 0:
        cs = typmath.glyph_centers(FORM5, cx, y, size)
        xc = (cs[R5[3][-1]][0] + cs[R5[4][0]][0]) / 2
        fr.line(xc, y - h * 0.75, xc, y - h * 0.75 + h * 1.5 * cut, "copy", 2.4, a * (1 - 0.6 * up), glow=0.6)
    if pre > 0:
        pw = typmath.size_of(P3, size)[0]
        typmath.draw(fr, P3, cx - w / 2 - 24 - pw / 2, y, size, None, a * pre * (1 - smooth(m)))
    # the name, over the sum
    la = a * smooth(lin(t, b(927), b(927) + 0.4)) * (1 - up)
    if la > 0.003:
        sw = smooth(lin(t, b(940) - 0.2, b(940) + 0.3))
        for name, na in (("Taylor series", 1 - sw), ("Taylor polynomial", sw)):
            if na > 0.003:
                fr.text(name, 960, 420, DISPLAY, 60, 600, "ink", la * na)
        fr.light_sweep(
            text_path("Taylor series", 960, 420, DISPLAY, 60, 600), lin(t, b(927) + 0.2, b(927) + 1.0), 0.8 * la
        )


def cos_coeffs(n, a):
    d = [math.cos(a), -math.sin(a), -math.cos(a), math.sin(a)]
    return np.array([d[k % 4] / math.factorial(k) for k in range(n + 1)])


def zone_lr(c, a, tol=0.01, reach=6.0):
    steps = np.arange(1, int(reach / 0.004) + 1) * 0.004
    out = []
    for s in (-1, 1):
        xs = a + s * steps
        bad = np.nonzero(np.abs(np.cos(xs) - T.evaluate(c, xs, a)) >= tol)[0]
        out.append(steps[bad[0] - 1] if len(bad) and bad[0] else (0.0 if len(bad) else reach))
    return a - out[0], a + out[1]


def center_a(t):
    a = 2.0 * ease_io(lin(t, b(965), b(970) + 0.4))
    return a - 3.0 * ease_io(lin(t, b(983), END - 0.05))


def bracket(fr, ax, x, s, alpha, height=46.0):
    y = min(max(float(ax.py(0.0)), ax.top), ax.bottom)
    px = float(ax.px(x))
    p = skia.Path()
    p.moveTo(px - 12 * s, y - height / 2)
    p.lineTo(px, y - height / 2)
    p.lineTo(px, y + height / 2)
    p.lineTo(px - 12 * s, y + height / 2)
    fr.path_stroke(p, "copy", 2.6, alpha, glow=0.5)


def draw_stage(fr, t):
    if t < b(942):
        return
    a = smooth(lin(t, b(942) + 0.2, b(942) + 0.8))
    ax = STAGE.ax
    STAGE.static(fr, a, labels=False)
    STAGE.original(fr, a)
    ca = center_a(t)
    if t < b(965):
        STAGE.a = 0.0
        c, _, s = STAGE.chain(t, HUG_DEG, HUG_T)
    else:
        STAGE.a = ca
        c, s = cos_coeffs(4, ca), 0.0
    STAGE.error_band(fr, c, 0.7 * a)
    STAGE.copy(fr, c, a, glow=0.6 + 0.5 * s)
    for t0 in HUG_T[:4]:  # a light sweep along each new hug zone
        u = lin(t, t0 + 0.3, t0 + 1.1)
        if 0 < u < 1:
            r = ZONES[HUG_T.index(t0) + 1]
            zp = STAGE.copy_path(c, ax, lo=-r, hi=r)
            fr.light_sweep(glow_path(zp, 24), u, 0.55 * a)
    lo, hi = zone_lr(c, ca)
    bracket(fr, ax, hi, 1, a)
    bracket(fr, ax, lo, -1, a)
    if t < b(957) + 0.5:  # the readout climbs with each hug (settled value, never the overshoot)
        r = (hi - lo) / 2
        shown = min(ZONES, key=lambda z: abs(z - r))
        y = float(ax.py(0.0)) - 49
        ra = a * (1 - smooth(lin(t, b(957), b(957) + 0.4)))
        hud.tabular(fr, f"±{shown:.2f}", float(ax.px(hi)), y, 26, "copy", ra, glow=0.25)
    # S23 · the blue centre, and the distance x − a
    ma = a * smooth(lin(t, b(957), b(957) + 0.4))
    if ma > 0.003:
        STAGE.probe(fr, ca, ma, ax=ax, drop=False)
        fr.glow_dot(
            float(ax.px(ca)),
            float(ax.py(0)),
            8 + 14 * pulse(t, b(957), 0.8),
            "x",
            0.6 * ma * pulse(t, b(957), 0.8),
            1.0,
        )
    da = a * smooth(lin(t, b(975), b(975) + 0.4))
    if da > 0.003:
        xp = ca + 1.5
        y = float(ax.py(0)) + 70
        x0, x1 = float(ax.px(ca)), float(ax.px(xp))
        grow = ease_out(lin(t, b(975), b(976) + 0.2))
        fr.line(x0, y, x0 + (x1 - x0) * grow, y, "x", 2.0, da, glow=0.4)
        for xx in (x0, x0 + (x1 - x0) * grow):
            fr.line(xx, y - 10, xx, y + 10, "x", 2.0, da)
        fr.glow_dot(x1, float(ax.py(0)), 5.0, "x", da * grow, 0.8)
        typmath.draw(fr, f"{X} {MINUS} {A}", (x0 + x1) / 2, y + 40, 40, None, da * grow)


# ------------------------------------------------------------------ assembly


def draw_handoff(fr, t):
    a = 1 - smooth(lin(t, START, START + 0.7))
    if a > 0.003:
        with layer_alpha(fr, a):
            ch3.draw_delivers(fr, t)


def draw_one(t, size):
    fr = Frame(size)
    draw_handoff(fr, t)
    draw_s20(fr, t)
    if S21 <= t < b(882) + 0.4:
        draw_jobs(fr, t)
    draw_invisible(fr, t)
    draw_stack(fr, t)
    draw_stage(fr, t)
    draw_s22_text(fr, t)
    hud.eyebrow(fr, t, "04 · THE RECIPE", START + 0.2)
    fr.zoom_blur(0.15 * (1 - ease_out(lin(t, b(882), b(882) + 0.4))) * (t >= b(882)))
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


def draw(t, size):
    return draw_one(t + START, size)


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


SCENES = {
    "S20": (S20, S21, [295.6, 305.8, 311.6]),
    "S21": (S21, S22, [315.4, 321.2, 327.8, 331.6, 336.4]),
    "S22": (S22, S23, [340.6, 343.9, 348.9]),
    "S23": (S23, END, [352.9, 355.4, 358.9]),
}
OFFSET = START
DURATION = END - START
STILLS = [s for _, _, st in SCENES.values() for s in st]
