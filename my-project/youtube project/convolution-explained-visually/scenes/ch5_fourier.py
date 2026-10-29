"""CHAPTER 5 - THE SHORTCUT (S17-S21), 05:21.280 - 06:43.440.

S17  Sliding is slow            a long rig zooms out to dots and drags; 10^6 x 10^6 -> a red flood
                                of points and a counter spinning to 1,000,000,000,000.
S18  A pure tone                faint cathedral returns; one sine, its amber echo copies peel off in
                                depth, collapse and sum to the same sine (scaled + shifted); three
                                frequencies pass through a convolution box with their real gains.
S19  The convolution theorem    split -> scale (real |H|) -> recombine == direct sliding result;
                                theorem written word by word; TIME vs FREQUENCY panels.
S20  FFT and reverb             trillion collapses to 100 million; reverb card: clap -> impulse
                                response -> song * IR = wet song (real np.convolve).
S21  Laplace and Z              Y = H X in both domains; highlights on output / input / transfer.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia

from cues import AUDIO, cue
from fx import (
    Frame, back, conv_symbol, ease_in, ease_io, ease_out, env, eyebrow, lerp, lin, mix, pulse, smooth, tile,
    tokens,
)
from mathtype import Formula, Token, symbol
from theme import H, THEME, TOKENS, W

START = cue(886)  # 321.28
END = cue(1106)  # 403.44 "So let's look back"

T = {
    "problem": cue(889), "slow": cue(892), "convolving": cue(893), "million1": cue(895), "million2": cue(899),
    "trillion": cue(904), "mults": cue(905), "fourier": cue(910), "rescue": cue(915), "tone": cue(920),
    "cathedral": cue(923), "every": cue(924), "echo": cue(925), "delayed": cue(934), "quieter": cue(936),
    "adding": cue(938), "same_wave": cue(948), "size": cue(953), "timing": cue(955), "so": cue(957),
    "frequency": cue(959), "untouched": cue(964), "scaled": cue(966), "shifted": cue(968), "we": cue(969),
    "split": cue(971), "scale": cue(976), "back": cue(982), "that": cue(984), "theorem": cue(988),
    "F1": cue(990), "f1": cue(993), "star": cue(994), "g1": cue(995), "equals": cue(996), "F2": cue(998),
    "f2": cue(1001), "times": cue(1002), "F3": cue(1004), "g3": cue(1007), "conv_in_time": cue(1008),
    "multiplication": cue(1013), "freq": cue(1015), "with_fft": cue(1016), "trillion2": cue(1022),
    "drops": cue(1024), "hundred": cue(1027), "million3": cue(1028), "audio": cue(1032), "reverb": cue(1035),
    "record": cue(1039), "clap": cue(1042), "recording": cue(1049), "impulse": cue(1053), "response": cue(1054),
    "hold": cue(1055), "song": cue(1057), "sounds": cue(1063), "inside": cue(1069), "cathedral2": cue(1071),
    "and": cue(1072), "laplace": cue(1079), "z": cue(1083), "every2": cue(1084), "output": cue(1091),
    "input": cue(1094), "transfer": cue(1097), "conv_thm": cue(1104), "theorem2": cue(1105),
}
INK, SIG, KER, OVL, OUT = (TOKENS[k] for k in ("ink", "signal", "kernel", "overlap", "output"))


# ------------------------------------------------------------------ shared: faint cathedral from chapter 0
def nave_faint(fr, alpha):
    if alpha <= 0.003:
        return
    from scenes.ch0_intro import camera, nave_lines, project

    cam = camera(19.5)
    for pts, base, width in nave_lines():
        sx, sy, zc = project(pts, cam)
        depth = float(zc.mean())
        a = base * alpha * max(0.14, min(1.0, 1.3 - depth / 42.0))
        fr.poly(sx, sy, "stone", width * max(0.55, min(1.6, 10.0 / depth)), a)


# ------------------------------------------------------------------ S17: sliding is slow
@lru_cache(maxsize=1)
def flood_points():
    rng = np.random.default_rng(11)
    pts = rng.uniform([40, 140], [1880, 1040], (4200, 2))
    order = rng.permutation(len(pts))
    return pts[order]


def fmt(n):
    return f"{int(round(n)):,}"


def draw_s17(fr, t):
    vis = env(t, START - 0.1, T["rescue"] + 0.3, 0.4, 0.6)
    if vis <= 0.003:
        return
    zoom = ease_io(lin(t, START + 0.2, T["slow"] + 0.2))
    n_sig = int(lerp(12, 220, zoom))
    size = lerp(78.0, 5.0, zoom)
    span = 1500.0
    step = span / n_sig
    x0 = 960 - span / 2 + step / 2
    rows_a = vis * (1 - smooth(lin(t, T["trillion"] - 0.2, T["trillion"] + 0.6)))
    for i in range(n_sig):
        x = x0 + i * step
        if size > 14:
            fr.rrect(x - size / 2, 430 - size / 2, size, size, size * 0.18, fill="signal", fill_alpha=0.1, stroke="signal",
                     width=1.8, alpha=rows_a)
        else:
            fr.circle(x, 430, max(1.6, size / 2), "signal", alpha=rows_a, fill=True)
    # kernel drags: a stuttering, frame-stepped slide
    k_n = max(3, int(n_sig * 0.4))
    stutter = math.floor((t - START) * 3.0) / 3.0
    k_off = ((stutter * 0.9) % 1.0) * span * 0.6
    for i in range(k_n):
        x = 960 - span / 2 + k_off + i * step
        if size > 14:
            fr.rrect(x - size / 2, 560 - size / 2, size, size, size * 0.18, fill="kernel", fill_alpha=0.1, stroke="kernel",
                     width=1.8, alpha=rows_a)
        else:
            fr.circle(x, 560, max(1.6, size / 2), "kernel", alpha=rows_a, fill=True)
    fr.text("SLOW", 960, 690, "sans", 26, 700, "alert", env(t, T["slow"] - 0.2, T["convolving"] + 0.6, 0.2, 0.4) * rows_a,
            tracking=0.3)
    fr.text("1,000,000 samples", 960, 360, "display", 40, 600, "signal",
            ease_out(lin(t, T["million1"] - 0.15, T["million1"] + 0.3)) * rows_a)
    fr.text("1,000,000 samples", 960, 650, "display", 40, 600, "kernel",
            ease_out(lin(t, T["million2"] - 0.15, T["million2"] + 0.3)) * rows_a)
    # the flood
    fa = ease_out(lin(t, T["trillion"] - 0.3, T["trillion"] + 1.2))
    dissolve = ease_in(lin(t, T["rescue"] - 0.3, T["rescue"] + 0.4))
    if fa > 0:
        pts = flood_points()
        n = int(len(pts) * fa)
        paint = skia.Paint(AntiAlias=True, Color4f=skia.Color4f(*[c for c in hex_rgb_alert()], 0.75 * vis * (1 - dissolve)),
                           StrokeWidth=3.0 * (1 - 0.7 * dissolve), StrokeCap=skia.Paint.kRound_Cap)
        fr.c.drawPoints(skia.Canvas.kPoints_PointMode, [skia.Point(float(x), float(y)) for x, y in pts[:n]], paint)
        u = lin(t, T["trillion"] - 0.4, T["trillion"] + 0.9)
        value = 10 ** lerp(6, 12, ease_out(u))
        ca = vis * (1 - dissolve)
        fr.rrect(460, 440, 1000, 200, 30, fill="bg", fill_alpha=0.92, stroke="alert", width=2.0, alpha=ca, glow=0.4)
        fr.text(fmt(value), 960, 560, "display", 88, 600, "alert", ca, glow=0.5)
        fr.text("MULTIPLICATIONS", 960, 616, "sans", 24, 700, "muted", ca, tracking=0.26)


def hex_rgb_alert():
    from fx import hex_rgb

    return hex_rgb("alert")


# ------------------------------------------------------------------ S18: a pure tone through the cathedral
X_L, X_R, BASE = 230.0, 1690.0, 640.0
PERIOD, AMP = 190.0, 95.0
D_K, G_K = [0.0, 0.28, 0.56, 0.84, 1.12], [1.0, 0.6, 0.36, 0.22, 0.13]  # delays in periods, gains
VANISH = (960.0, 300.0)


def sine_pts(x0, x1, amp, phase=0.0, period=PERIOD, n=360, base=BASE, depth=0.0, upto=1.0):
    xs = np.linspace(x0, x0 + (x1 - x0) * upto, max(2, int(n * upto)))
    ys = base - amp * np.sin(2 * math.pi * (xs - x0) / period - phase)
    s = 1.0 / (1.0 + 0.17 * depth)
    return VANISH[0] + (xs - VANISH[0]) * s, VANISH[1] + (ys - VANISH[1]) * s


def tone_sum():
    """Sum of the delayed, quieter copies is one sine: amplitude and phase from the phasor sum."""
    z = sum(g * np.exp(-2j * math.pi * d) for g, d in zip(G_K, D_K))
    return abs(z), -np.angle(z)


def draw_s18(fr, t):
    vis = env(t, T["rescue"] - 0.2, T["we"] + 0.1, 0.5, 0.5)
    if vis <= 0.003:
        return
    nave_faint(fr, 0.22 * vis * (1 - smooth(lin(t, T["so"] - 0.4, T["so"] + 0.4))))
    part1 = vis * (1 - smooth(lin(t, T["so"] - 0.3, T["so"] + 0.3)))
    if part1 > 0.003:
        up = ease_io(lin(t, T["tone"] - 0.2, T["tone"] + 1.1))
        pile = ease_io(lin(t, T["adding"] - 0.2, T["adding"] + 0.9))
        merge = ease_io(lin(t, T["copies_merge"] if "copies_merge" in T else T["same_wave"] - 0.9, T["same_wave"] + 0.2))
        # echo copies peel off backwards in depth, delayed and quieter
        for k in range(1, len(G_K)):
            st = T["every"] + 0.35 * (k - 1)
            ak = ease_out(lin(t, st, st + 0.8))
            if ak <= 0:
                continue
            depth = k * ak * (1 - pile)
            px, py = sine_pts(X_L, X_R, AMP * G_K[k], phase=2 * math.pi * D_K[k] * ak, depth=depth)
            fr.poly(px, py, "kernel", 2.0, part1 * ak * (1 - 0.85 * merge) * (0.5 + 0.5 * G_K[k] ** 0.5), glow=0.45)
        px, py = sine_pts(X_L, X_R, AMP, upto=up)
        fr.poly(px, py, "signal", 2.8, part1 * (1 - 0.45 * merge), glow=0.6)
        if merge > 0:
            amp, ph = tone_sum()
            px, py = sine_pts(X_L, X_R, AMP * lerp(1.0, amp, merge), phase=ph * merge)
            fr.poly(px, py, "output", 3.2, part1 * merge, glow=0.9)
            # size and timing annotations
            sa = ease_out(lin(t, T["size"] - 0.2, T["size"] + 0.3)) * part1
            if sa > 0:
                crest_x = X_L + PERIOD * (0.25 + ph / (2 * math.pi))
                x = crest_x + 3 * PERIOD
                fr.line(x, BASE, x, BASE - AMP * amp, "output", 2.0, sa)
                fr.text(f"× {amp:.2f}", x, BASE - AMP * 1.45, "display", 34, 600, "output", sa)
            ta = ease_out(lin(t, T["timing"] - 0.2, T["timing"] + 0.3)) * part1
            if ta > 0:
                c0 = X_L + PERIOD * 0.25 + PERIOD
                c1 = X_L + PERIOD * (0.25 + ph / (2 * math.pi)) + PERIOD
                y = BASE - AMP * 1.35
                fr.line(c0, y, c1, y, "kernel", 2.4, ta, glow=0.5)
                fr.line(c1, y, c1 - 10, y - 8, "kernel", 2.4, ta)
                fr.line(c1, y, c1 - 10, y + 8, "kernel", 2.4, ta)
                fr.text("SHIFT", (c0 + c1) / 2, y - 22, "sans", 22, 700, "kernel", ta, tracking=0.2)
        labels = [("ONE PURE TONE", "signal", T["tone"] - 0.1, T["every"] + 0.3),
                  ("ECHOES: DELAYED, QUIETER", "kernel", T["every"] + 0.2, T["adding"] + 0.4),
                  ("SAME SINE WAVE", "output", T["same_wave"] - 0.3, T["so"]),]
        for text, color, a0, a1 in labels:
            fr.text(text, X_L, 300, "sans", 24, 700, color, env(t, a0, a1, 0.3, 0.3) * part1, align="left", tracking=0.2)
    # three frequencies through a convolution box
    part2 = vis * smooth(lin(t, T["so"], T["so"] + 0.5))
    if part2 > 0.003:
        draw_freq_box(fr, t, part2)


def H_of(cycles_per_period):
    """Frequency response of the echo kernel at a given frequency (relative to the tone)."""
    z = sum(g * np.exp(-2j * math.pi * d * cycles_per_period) for g, d in zip(G_K, D_K))
    return abs(z), -np.angle(z)


def draw_freq_box(fr, t, a):
    box = (860.0, 300.0, 200.0, 520.0)
    fr.rrect(*box, 26, fill="card", stroke="line", width=1.6, alpha=a)
    conv_symbol(fr, 960, 560, 34, a, glow=0.8)
    fr.text("CONVOLUTION", 960, 280, "sans", 20, 700, "muted", a, tracking=0.2)
    freqs = [(0.6, 400.0), (1.0, 560.0), (1.7, 720.0)]
    for i, (f, y) in enumerate(freqs):
        ai = ease_out(lin(t, T["frequency"] - 0.2 + 0.25 * i, T["frequency"] + 0.4 + 0.25 * i)) * a
        if ai <= 0:
            continue
        period = PERIOD / f * 0.8
        px, py = sine_pts(200.0, 830.0, 55.0, period=period, base=y, n=200)
        fr.poly(px, py, "signal", 2.4, ai, glow=0.5)
        gain, ph = H_of(f)
        out_a = ease_out(lin(t, T["untouched"] - 0.3 + 0.2 * i, T["untouched"] + 0.3 + 0.2 * i)) * a
        px, py = sine_pts(1090.0, 1720.0, 55.0 * gain / 2.4, phase=ph, period=period, base=y, n=200)
        fr.poly(px, py, "output", 2.6, out_a, glow=0.7)
        fr.text(f"×{gain:.2f}", 1740, y + 10, "display", 26, 600, "output", out_a * ease_out(lin(t, T["scaled"] - 0.2, T["scaled"] + 0.3)),
                align="left")
    fr.text("SAME FREQUENCIES · SCALED · SHIFTED", 960, 900, "sans", 24, 700, "output",
            ease_out(lin(t, T["scaled"] - 0.3, T["scaled"] + 0.3)) * a, tracking=0.2)


# ------------------------------------------------------------------ S19: split, scale, recombine; the theorem
N = 512
COMP_F = [1, 2, 3, 5, 7]
COMP_A = [1.0, 0.7, 0.55, 0.4, 0.3]
COMP_P = [0.0, 1.1, 2.3, 0.6, 1.8]
KERNEL_TAPS = {0: 1.0, 24: 0.6, 48: 0.36, 72: 0.22}  # the echo kernel, in samples


@lru_cache(maxsize=1)
def recombine():
    n = np.arange(N)
    comps = [a * np.sin(2 * math.pi * f * n / N + p) for f, a, p in zip(COMP_F, COMP_A, COMP_P)]
    signal = np.sum(comps, axis=0)
    gains, out_comps = [], []
    for f, c, a, p in zip(COMP_F, comps, COMP_A, COMP_P):
        h = sum(g * np.exp(-2j * math.pi * f * d / N) for d, g in KERNEL_TAPS.items())
        gains.append(abs(h))
        out_comps.append(a * abs(h) * np.sin(2 * math.pi * f * n / N + p + np.angle(h)))
    via_freq = np.sum(out_comps, axis=0)
    direct = np.zeros(N)  # direct sliding (circular) convolution, no FFT involved
    for d, g in KERNEL_TAPS.items():
        direct += g * np.roll(signal, d)
    assert np.allclose(via_freq, direct, atol=1e-9)
    return signal, comps, gains, out_comps, via_freq, direct


def wave(fr, vals, x0, x1, y, scale, color, alpha, width=2.4, glow=0.5, upto=1.0):
    m = max(2, int(len(vals) * upto))
    xs = np.linspace(x0, x1, len(vals))[:m]
    fr.poly(xs, y - vals[:m] * scale, color, width, alpha, glow=glow)


THEOREM = Formula([
    Token("F1", r"\mathcal{F}\{", INK, 0.0), Token("f1", "f", SIG, 0.05), Token("st", r"\ast", OVL, 0.05),
    Token("g1", "g", KER, 0.0), Token("c1", r"\}", INK, 0.3), Token("eq", "=", INK, 0.3),
    Token("F2", r"\mathcal{F}\{", INK, 0.0), Token("f2", "f", SIG, 0.0), Token("c2", r"\}", INK, 0.14),
    Token("dot", r"\cdot", OUT, 0.14), Token("F3", r"\mathcal{F}\{", INK, 0.0), Token("g3", "g", KER, 0.0),
    Token("c3", r"\}", INK, 0.0),
], size=104)
THEOREM_WRITE = {"F1": "F1", "f1": "f1", "st": "star", "g1": "g1", "c1": "g1", "eq": "equals", "F2": "F2",
                 "f2": "f2", "c2": "f2", "dot": "times", "F3": "F3", "g3": "g3", "c3": "g3"}


def draw_s19(fr, t):
    vis = env(t, T["we"] - 0.2, T["with_fft"] + 0.2, 0.5, 0.5)
    if vis <= 0.003:
        return
    signal, comps, gains, out_comps, via_freq, direct = recombine()
    # 19A: split -> scale -> recombine
    a1 = vis * (1 - smooth(lin(t, T["that"] - 0.2, T["that"] + 0.4)))
    if a1 > 0.003:
        sp = ease_io(lin(t, T["split"] - 0.2, T["split"] + 0.8))
        sc = ease_io(lin(t, T["scale"] - 0.2, T["scale"] + 0.6))
        rc = ease_io(lin(t, T["back"] - 0.4, T["back"] + 0.6))
        x0, x1 = 220.0, 1380.0
        wave(fr, signal, x0, x1, 230, 38, "signal", a1 * (1 - 0.6 * rc), glow=0.6)
        fr.text("SIGNAL", x0, 160, "sans", 22, 700, "signal", a1, align="left", tracking=0.2)
        ys = [380 + i * 92 for i in range(5)]
        for i, (c, oc, g) in enumerate(zip(comps, out_comps, gains)):
            y = lerp(230, ys[i], sp) if rc < 1 else ys[i]
            y = lerp(y, 880, rc)
            vals = lerp(c, oc, sc)
            color = mix(SIG, OUT, sc)
            wave(fr, vals, x0, x1, y, 34, color, a1 * sp * (1 - rc), width=2.0, glow=0.35)
            ga = ease_out(lin(t, T["scale"] - 0.4 + 0.08 * i, T["scale"] + 0.1 + 0.08 * i)) * a1 * sp * (1 - rc)
            if ga > 0:
                fr.rrect(1480, ys[i] - 14, 260 * g / max(gains), 28, 8, fill="kernel", fill_alpha=0.85, alpha=ga)
                fr.text(f"×{g:.2f}", 1480 + 260 * g / max(gains) + 14, ys[i] + 9, "display", 24, 600, "kernel", ga, align="left")
        fr.text("SPLIT INTO FREQUENCIES", x0, 350, "sans", 20, 700, "muted", env(t, T["split"], T["scale"], 0.3, 0.3) * a1,
                align="left", tracking=0.2)
        fr.text("SCALE EACH ONE", 1480, 350, "sans", 20, 700, "kernel", env(t, T["scale"] - 0.2, T["back"], 0.3, 0.3) * a1,
                align="left", tracking=0.2)
        if rc > 0:
            wave(fr, via_freq, x0, x1, 880, 26, "output", a1 * rc, width=3.0, glow=0.9)
            # ghost: the direct sliding convolution lands exactly on it
            ga = smooth(lin(t, T["back"] + 0.4, T["back"] + 0.9)) * a1
            xs = np.linspace(x0, x1, N)
            for k in range(0, N - 6, 12):
                fr.line(xs[k], 880 - direct[k] * 26, xs[k + 6], 880 - direct[k + 6] * 26, "#ffffff", 1.4, ga * 0.9)
            fr.text("PUT BACK TOGETHER", x0, 790, "sans", 20, 700, "output", rc * a1, align="left", tracking=0.2)
            fr.text("= direct sliding result", x1 + 30, 890, "sans", 22, 600, "#ffffff", ga * 0.85, align="left")
    # 19B: the theorem
    b = vis * smooth(lin(t, T["that"] - 0.1, T["that"] + 0.4))
    if b <= 0.003:
        return
    base, scale = 330.0, 1.0
    alpha, dy, glow = {}, {}, {}
    for tok in THEOREM.tokens:
        t0 = T[THEOREM_WRITE[tok.key]] - 0.12
        u = ease_out(lin(t, t0, t0 + 0.35))
        alpha[tok.key] = u * b
        dy[tok.key] = 16 * (1 - u)
    lit_star = pulse(t, T["conv_in_time"] - 0.1, 1.0)
    lit_dot = pulse(t, T["multiplication"] - 0.1, 1.0)
    glow["st"], glow["dot"] = 0.9 * lit_star, 0.9 * lit_dot
    THEOREM.draw(fr, 960, base, scale, alpha=alpha, dy=dy, glow=glow)
    fr.text("THE CONVOLUTION THEOREM", 960, 170, "sans", 24, 700, "muted", ease_out(lin(t, T["theorem"] - 0.3, T["theorem"] + 0.3)) * b,
            tracking=0.26)
    arc = ease_io(lin(t, T["g3"] + 0.2, T["g3"] + 0.9))
    if arc > 0:
        s0 = THEOREM.bounds("st", 960, base, scale)
        s1 = THEOREM.bounds("dot", 960, base, scale)
        xa, xb = (s0[0] + s0[2]) / 2, (s1[0] + s1[2]) / 2
        p = skia.Path()
        n = 40
        for k in range(int(n * arc) + 1):
            s = k / n
            x = lerp(xa, xb, s)
            y = base + 40 + 70 * 4 * s * (1 - s)
            (p.moveTo if k == 0 else p.lineTo)(x, y)
        fr.path_stroke(p, mix(OVL, OUT, arc), 2.4, b, glow=0.6)
    draw_panels(fr, t, b)


def draw_panels(fr, t, b):
    pa = ease_out(lin(t, T["conv_in_time"] - 0.5, T["conv_in_time"] + 0.2)) * b
    if pa <= 0:
        return
    # TIME panel: boxes sliding (busy)
    fr.rrect(160, 500, 740, 420, 28, fill="card", stroke="line", width=1.5, alpha=pa)
    fr.text("TIME", 200, 548, "sans", 22, 700, "muted", pa, align="left", tracking=0.22)
    u = ((t - T["conv_in_time"]) * 0.55) % 1.0
    xa = lerp(260, 800, u)
    fr.rrect(500, 640, 120, 120, 6, fill="signal", fill_alpha=0.12, stroke="signal", width=2.2, alpha=pa)
    fr.rrect(xa - 60, 640, 120, 120, 6, fill="kernel", fill_alpha=0.12, stroke="kernel", width=2.2, alpha=pa)
    ov = max(0.0, 120 - abs(xa - 560))
    if ov > 0:
        lo = max(xa, 560) - 60
        fr.rrect(lo, 640, ov, 120, 2, fill="overlap", fill_alpha=0.4, alpha=pa)
    fr.text("convolution", 530, 870, "display", 40, 600, "overlap", pa * ease_out(lin(t, T["conv_in_time"] - 0.1, T["conv_in_time"] + 0.3)))
    # FREQUENCY panel: two spectra multiplied bar by bar
    fr.rrect(1020, 500, 740, 420, 28, fill="card", stroke="line", width=1.5, alpha=pa)
    fr.text("FREQUENCY", 1060, 548, "sans", 22, 700, "muted", pa, align="left", tracking=0.22)
    spec_f = [0.9, 0.6, 0.75, 0.45, 0.3, 0.5, 0.25, 0.15]
    spec_g = [1.0, 0.85, 0.6, 0.5, 0.42, 0.3, 0.22, 0.15]
    m = ease_io(lin(t, T["multiplication"] - 0.4, T["multiplication"] + 0.4))
    for i, (a, g) in enumerate(zip(spec_f, spec_g)):
        x = 1100 + i * 76
        h1, h2 = 110 * a, 110 * g
        prod = 110 * a * g
        fr.rrect(x, 760 - lerp(h1, prod, m), 22, lerp(h1, prod, m), 4, fill=mix(SIG, OUT, m), fill_alpha=0.85, alpha=pa)
        fr.rrect(x + 26, 760 - h2, 22, h2, 4, fill="kernel", fill_alpha=0.85 * (1 - m), alpha=pa)
        if 0.05 < m < 0.95:
            fr.text("×", x + 24, 760 - max(h1, h2) - 14, "display", 20, 600, "overlap", pa * (1 - abs(2 * m - 1)))
    fr.line(1080, 762, 1720, 762, "line", 1.2, pa)
    fr.text("multiplication", 1390, 870, "display", 40, 600, "output", pa * ease_out(lin(t, T["multiplication"] - 0.1, T["multiplication"] + 0.3)))


# ------------------------------------------------------------------ S20: FFT and reverb
@lru_cache(maxsize=1)
def reverb_data():
    from scenes.ch0_intro import song

    dry = song()[0]
    rng = np.random.default_rng(5)
    n = 360
    ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / 70.0)
    ir[0] = 3.2
    ir = ir / np.abs(ir).max()
    wet = np.convolve(dry, ir)[: len(dry) + n // 2]
    return dry / np.abs(dry).max(), ir, wet / np.abs(wet).max()


def draw_s20(fr, t):
    vis = env(t, T["with_fft"] - 0.2, T["and"] + 0.3, 0.4, 0.5)
    if vis <= 0.003:
        return
    # 20A: trillion -> 100 million
    a1 = vis * (1 - smooth(lin(t, T["audio"] - 0.4, T["audio"] + 0.2)))
    if a1 > 0.003:
        u = ease_io(lin(t, T["drops"] - 0.2, T["million3"] + 0.1))
        value = 10 ** lerp(12, 8, u)
        color = mix(TOKENS["alert"], OUT, smooth(lin(u, 0.7, 1.0)))
        fr.text("WITH THE FAST FOURIER TRANSFORM", 960, 260, "sans", 24, 700, "muted", a1, tracking=0.24)
        fr.text(fmt(value), 960, 430, "display", 92, 600, color, a1, glow=0.5)
        fr.text("MULTIPLICATIONS", 960, 486, "sans", 24, 700, "muted", a1, tracking=0.26)
        ba = ease_out(lin(t, T["hundred"] - 0.3, T["hundred"] + 0.3)) * a1
        if ba > 0:
            fr.rrect(310, 600, 1300, 46, 10, fill="alert", fill_alpha=0.75, alpha=ba)
            fr.text("SLIDING DIRECTLY", 310, 586, "sans", 22, 700, "alert", ba, align="left", tracking=0.2)
            fr.rrect(310, 720, max(2.0, 1300 / 10000), 46, 2, fill="output", fill_alpha=1.0, alpha=ba, glow=1.0)
            fr.text("FFT", 310, 706, "sans", 22, 700, "output", ba, align="left", tracking=0.2)
            fr.text("≈ 10,000× fewer", 360, 754, "display", 34, 600, "output", ba, align="left")
    # 20B/C: reverb plugin card
    a2 = vis * smooth(lin(t, T["audio"] - 0.2, T["audio"] + 0.4))
    if a2 <= 0.003:
        return
    inside = ease_io(lin(t, T["inside"] - 0.3, T["cathedral2"] + 0.3))
    nave_faint(fr, 0.2 * a2 * inside)
    if inside > 0:
        from scenes.ch0_intro import CLAP, camera, project

        sx, sy, zc = project(CLAP[None, :], camera(19.5))
        for k in range(4):
            age = ((t - T["inside"]) * 0.6 + k * 0.25) % 1.0
            fr.circle(sx[0], sy[0], 40 + 520 * age, "signal" if k == 0 else "kernel", 1.6, a2 * inside * (1 - age) * 0.6, glow=0.5)
    lift = ease_io(lin(t, T["hold"] - 0.5, T["hold"] + 0.3))
    cy = lerp(560.0, 330.0, lift)
    ch = lerp(440.0, 300.0, lift)
    card_a = a2 * (1 - smooth(lin(lift, 0.3, 1.0)))
    fr.rrect(460, cy - ch / 2, 1000, ch, 30, fill="card", stroke="line", width=1.6, alpha=card_a)
    fr.text("REVERB", 510, cy - ch / 2 + 52, "sans", 26, 700, "ink", card_a, align="left", tracking=0.3)
    fr.text("REVERB  =  SONG ⊛ ROOM".replace("⊛", "*"), 960, 470, "sans", 26, 700, "muted", a2 * smooth(lin(lift, 0.5, 1.0)),
            tracking=0.26)
    for i, lab in enumerate(("SIZE", "DECAY", "MIX")):
        kx = 1170 + i * 100
        ky = cy - ch / 2 + 46
        a2k = card_a
        fr.circle(kx, ky, 22, "line", 2.0, a2k)
        ang = -math.pi * 0.75 + math.pi * 1.5 * (0.35 + 0.2 * i)
        fr.line(kx, ky, kx + 16 * math.cos(ang), ky + 16 * math.sin(ang), "kernel", 2.4, a2k)
        fr.text(lab, kx, ky + 46, "sans", 14, 700, "muted", a2k, tracking=0.16)
    dry, ir, wet = reverb_data()
    disp_y = cy + ch * 0.12
    # clap spike, then the impulse response
    spike = ease_out(lin(t, T["clap"] - 0.15, T["clap"] + 0.2))
    ir_u = ease_io(lin(t, T["recording"] - 0.2, T["response"] + 0.3))
    if spike > 0 and lift < 1:
        fr.line(540, disp_y, 1380, disp_y, "line", 1.2, a2 * (1 - lift))
        fr.line(560, disp_y, 560, disp_y - 120 * spike, "#ffffff", 3.0, a2 * (1 - lift), glow=1.0)
        if ir_u > 0:
            wave(fr, ir, 560, 1380, disp_y, 110, "kernel", a2 * (1 - lift), width=1.8, glow=0.5, upto=ir_u)
        fr.text("CLAP", 560, disp_y + 50, "sans", 20, 700, "ink", spike * a2 * (1 - lift) * (1 - ir_u), tracking=0.2)
        fr.text("IMPULSE RESPONSE", 960, disp_y + 150, "sans", 24, 700, "kernel",
                ease_out(lin(t, T["impulse"] - 0.2, T["impulse"] + 0.3)) * a2 * (1 - lift), tracking=0.22)
    # song * IR = song in the cathedral
    if lift > 0:
        y = 620.0
        sa = ease_out(lin(t, T["song"] - 0.2, T["song"] + 0.3)) * a2
        wave(fr, dry, 120, 640, y, 70, "signal", sa, width=1.6, glow=0.4)
        conv_symbol(fr, 700, y, 22, sa)
        wave(fr, ir, 760, 1060, y, 70, "kernel", sa, width=1.6, glow=0.4)
        fr.text("=", 1110, y + 16, "display", 52, 500, "ink", sa)
        wa = ease_io(lin(t, T["sounds"] - 0.3, T["inside"] + 0.4)) * a2
        wave(fr, wet, 1160, 1800, y, 70, "output", a2 * min(1.0, wa * 2), width=1.8, glow=0.7, upto=max(0.02, wa))
        fr.text("SONG", 380, y + 120, "sans", 20, 700, "signal", sa, tracking=0.2)
        fr.text("ROOM", 910, y + 120, "sans", 20, 700, "kernel", sa, tracking=0.2)
        fr.text("SONG IN THE CATHEDRAL", 1480, y + 120, "sans", 20, 700, "output", wa * a2, tracking=0.2)


# ------------------------------------------------------------------ S21: Laplace and Z
def ytf(var):
    return Formula([
        Token("Y", "Y", OUT, 0.0), Token("ya", f"({var})", INK, 0.25), Token("eq", "=", INK, 0.25),
        Token("H", "H", KER, 0.0), Token("ha", f"({var})", INK, 0.12), Token("X", "X", SIG, 0.0),
        Token("xa", f"({var})", INK, 0.0),
    ], size=80)


LAPLACE, ZT = ytf("s"), ytf("z")


def draw_s21(fr, t):
    vis = env(t, T["and"] - 0.1, END, 0.4, 0.45)
    if vis <= 0.003:
        return
    cards = ((LAPLACE, "LAPLACE TRANSFORM", 560.0, T["laplace"]), (ZT, "Z-TRANSFORM", 1360.0, T["z"]))
    hl = {"Y": pulse(t, T["output"] - 0.1, 0.9), "X": pulse(t, T["input"] - 0.1, 0.9),
          "H": smooth(lin(t, T["transfer"] - 0.2, T["transfer"] + 0.2)) * (1 - smooth(lin(t, T["conv_thm"], T["theorem2"] + 0.4)))}
    for formula, title, cx, t0 in cards:
        a = ease_out(lin(t, t0 - 0.3, t0 + 0.3)) * vis
        if a <= 0:
            continue
        dy = 30 * (1 - a)
        fr.rrect(cx - 340, 300 + dy, 680, 340, 30, fill="card", stroke="line", width=1.6, alpha=a, glow=0.0)
        fr.text(title, cx, 370 + dy, "sans", 24, 700, "muted", a, tracking=0.24)
        formula.draw(fr, cx, 520 + dy, 1.0, alpha={k: a for k in ("Y", "ya", "eq", "H", "ha", "X", "xa")},
                     glow={k: 0.9 * v for k, v in hl.items()})
        lab_y = 600 + dy
        for key, text, color in (("Y", "OUTPUT", "output"), ("H", "TRANSFER FUNCTION", "kernel"), ("X", "INPUT", "signal")):
            b = formula.bounds(key, cx, 520 + dy)
            la = smooth(lin(t, {"Y": T["output"], "X": T["input"], "H": T["transfer"]}[key] - 0.2,
                            {"Y": T["output"], "X": T["input"], "H": T["transfer"]}[key] + 0.2)) * a
            fr.text(text, (b[0] + b[2]) / 2, lab_y, "sans", 16, 700, color, la, tracking=0.16)
    # both converge on the theorem
    ca = ease_io(lin(t, T["conv_thm"] - 0.4, T["conv_thm"] + 0.4)) * vis
    if ca > 0:
        for cx in (560.0, 1360.0):
            fr.line(cx, 640, lerp(cx, 960, ca), lerp(640, 820, ca), "overlap", 2.0, vis, glow=0.6)
        fr.rrect(960 - 260, 790, 520, 70, 35, fill="card", alpha=ca)
        fr.rrect(960 - 260, 790, 520, 70, 35, fill="overlap", fill_alpha=0.12, stroke="overlap", width=2.2,
                 alpha=ca, glow=0.6 * pulse(t, T["theorem2"] - 0.1, 0.8) + 0.2)
        fr.text("CONVOLUTION THEOREM", 960, 834, "sans", 24, 700, "overlap", ca, tracking=0.24)


# ------------------------------------------------------------------ assembly

def draw(t, size):
    t = t + START
    fr = Frame(size)
    draw_s17(fr, t)
    draw_s18(fr, t)
    draw_s19(fr, t)
    draw_s20(fr, t)
    draw_s21(fr, t)
    eyebrow(fr, t, "05 · THE SHORTCUT", START + 0.15)
    return fr.finish()


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
STILLS = [322.0, 324.3, 327.8, 330.4, 334.4, 336.4, 339.6, 343.0, 347.8, 350.6, 353.4, 355.6, 357.6, 359.4,
          361.4, 366.0, 370.0, 372.0, 374.6, 377.4, 380.0, 383.0, 386.0, 389.0, 391.0, 394.6, 399.6, 402.8]
