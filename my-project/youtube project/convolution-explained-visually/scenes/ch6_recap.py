"""CHAPTER 6 - RECAP AND CLOSE (S22-S23), 06:43.440 - 07:33.960 (+ end-screen hold).

S22  Everything we discovered   the recipe strip returns; five live recap cards in a 2.5D arc
                                (numbers, dice, curves, images, Fourier), each lighting on its
                                sentence; all collapse into one lime "x" (frequency by frequency).
S23  The quiet operation        echo / blurry photo / pair of dice callbacks, the nave returns with
                                the blend symbol, which becomes the CONVOLUTION wordmark; subscribe;
                                end-screen hold with two marked slots for YouTube end-screen videos.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia

from cues import AUDIO, AUDIO_DURATION, cue
from fx import (
    Frame, back, card_quad, conv_symbol, ease_in, ease_io, ease_out, env, eyebrow, font, lerp, lin, mix,
    offscreen, pulse, smooth, tokens,
)
from mathtype import Formula, Token
from theme import H, THEME, TOKENS, W

START = cue(1106)  # 403.44
END_AUDIO = AUDIO_DURATION  # 453.96
END_HOLD = 15.0  # silent end-screen hold for YouTube end-screen elements (set 0 to remove)
END = END_AUDIO + END_HOLD

T = {
    "discovered": cue(1113), "convolution": cue(1114), "recipe": cue(1118), "flip": cue(1119),
    "slide": cue(1120), "multiply": cue(1121), "add": cue(1123), "numbers": cue(1127), "smooths": cue(1129),
    "long": cue(1139), "dice": cue(1142), "triangles": cue(1148), "bell": cue(1153), "curves": cue(1157),
    "overlap": cue(1163), "slides": cue(1167), "images": cue(1171), "blur": cue(1174), "sharpen": cue(1175),
    "edges": cue(1178), "neural": cue(1180), "own": cue(1187), "fourier": cue(1191), "all": cue(1193),
    "collapses": cue(1197), "single": cue(1200), "frequency": cue(1202), "freq2": cue(1204),
    "next": cue(1205), "echo": cue(1211), "blurry": cue(1214), "photo": cue(1215), "pair": cue(1219),
    "dice2": cue(1221), "same": cue(1225), "quiet": cue(1226), "operation": cue(1227), "underneath": cue(1231),
    "if": cue(1232), "conv2": cue(1235), "subscribe": cue(1238), "one": cue(1246),
}
INK, SIG, KER, OVL, OUT = (TOKENS[k] for k in ("ink", "signal", "kernel", "overlap", "output"))


# ------------------------------------------------------------------ S22A: the recipe strip returns
PILLS = (("FLIP", "kernel", "flip"), ("SLIDE", "kernel", "slide"), ("MULTIPLY", "overlap", "multiply"), ("ADD", "output", "add"))


def draw_recipe(fr, t):
    vis = env(t, T["discovered"] - 0.4, T["collapses"], 0.5, 0.6)
    if vis <= 0.003:
        return
    from scenes.ch0_intro import _icon

    up = ease_io(lin(t, T["numbers"] - 0.9, T["numbers"] - 0.1))
    y, s = lerp(520.0, 118.0, up), lerp(1.15, 0.62, up)
    fr.text("ONE SIMPLE RECIPE", 960, y - 100 * s, "sans", 24, 700, "muted", env(t, T["convolution"] - 0.2, T["numbers"] - 0.5, 0.3, 0.3) * vis,
            tracking=0.24)
    for i, (name, color, key) in enumerate(PILLS):
        L = smooth(lin(t, T[key] - 0.12, T[key] + 0.25))
        a = ease_out(lin(t, T["discovered"] - 0.3 + 0.08 * i, T["discovered"] + 0.2 + 0.08 * i)) * vis
        cx = 960 + (i - 1.5) * 332 * s
        w, h = 300 * s, 96 * s
        fr.rrect(cx - w / 2, y - h / 2, w, h, h / 2, fill=color, fill_alpha=0.1 * L, alpha=a,
                 stroke=mix(TOKENS["line"], TOKENS[color], max(L, up)), width=1.6, glow=0.9 * pulse(t, T[key] - 0.1, 0.7))
        icol = mix(TOKENS["muted"], TOKENS[color], max(L, up))
        fr.c.save()
        fr.c.translate(cx - w / 2 + 52 * s, y)
        fr.c.scale(s, s)
        _icon(fr, i, 0, 0, icol, a, lin(t, T[key], T[key] + 0.55))
        fr.c.restore()
        fr.text(name, cx - w / 2 + 94 * s, y + 11 * s, "sans", 30 * s, 700, mix(TOKENS["muted"], INK, max(L, up)), a,
                align="left", tracking=0.1)


# ------------------------------------------------------------------ S22B: five live recap cards
CARD_W, CARD_H = 300.0, 420.0
CARD_Y = 590.0
CARDS = [
    ("NUMBERS", "smooths · multiplies", "numbers", "dice"),
    ("DICE", "triangle → bell", "dice", "curves"),
    ("CURVES", "area of overlap", "curves", "images"),
    ("IMAGES", "blur · edges · learned", "images", "fourier"),
    ("FOURIER", "one multiplication", "fourier", "collapses"),
]


def card_x(i):
    return 960 + (i - 2) * 334.0


@lru_cache(maxsize=1)
def recap_data():
    from scenes.ch1_sliding import SMOOTH, TEMPS
    from scenes.ch4_images import diverging, gabors, images

    pmf2 = np.convolve(np.ones(6), np.ones(6)) / 36
    pmf = np.ones(6) / 6
    for _ in range(11):
        pmf = np.convolve(pmf, np.ones(6) / 6)
    s = np.arange(12, 73)
    z = (s - 42) / math.sqrt(12 * 35 / 12)
    bell_at = np.interp(np.linspace(-2.3, 2.3, 11), z, pmf * math.sqrt(12 * 35 / 12))
    return TEMPS, SMOOTH, pmf2 / pmf2.max(), bell_at / bell_at.max(), images(), gabors(), diverging


MINI_THEOREM = Formula([
    Token("F1", r"\mathcal{F}\{", INK, 0.0), Token("f1", "f", SIG, 0.05), Token("st", r"\ast", OVL, 0.05),
    Token("g1", "g", KER, 0.0), Token("c1", r"\}", INK, 0.25), Token("eq", "=", INK, 0.25),
    Token("F2", r"\mathcal{F}\{", INK, 0.0), Token("f2", "f", SIG, 0.0), Token("c2", r"\}", INK, 0.1),
    Token("dot", r"\cdot", OUT, 0.1), Token("F3", r"\mathcal{F}\{", INK, 0.0), Token("g3", "g", KER, 0.0),
    Token("c3", r"\}", INK, 0.0),
], size=44)


def render_card(i, t, k):
    surf, p = offscreen(CARD_W, CARD_H, k)
    p.rrect(0.75, 0.75, CARD_W - 1.5, CARD_H - 1.5, 24, fill="card", stroke="line", width=1.5)
    title, caption, key, _ = CARDS[i]
    p.text(f"0{i + 1}", 24, 46, "display", 20, 600, "muted", 1.0, align="left")
    p.text(title, CARD_W - 24, 46, "sans", 20, 700, "ink", 1.0, align="right", tracking=0.16)
    p.text(caption, CARD_W / 2, CARD_H - 30, "sans", 18, 600, "muted", 1.0, tracking=0.08)
    temps, smoothv, tri, bell, imgs, gab, diverging = recap_data()
    u = t - T[key]
    if i == 0:
        xs = np.linspace(40, 260, 7)
        ys = 200 - (temps - 16) / 12 * 110
        p.poly(xs, ys, "signal", 2.2, 1.0)
        sa = ease_out(lin(t, T["smooths"] - 0.2, T["smooths"] + 0.6))
        m = max(2, int(5 * sa))
        if sa > 0:
            p.poly(xs[1:1 + m], 200 - (smoothv[:m] - 16) / 12 * 110, "output", 3.0, 1.0)
        la = ease_out(lin(t, T["long"] - 0.2, T["long"] + 0.4))
        p.text("123 × 11", CARD_W / 2, 280, "display", 34, 600, "ink", 0.9)
        p.text("= 1353", CARD_W / 2, 326, "display", 34, 700, "output", la)
    elif i == 1:
        m = ease_io(lin(t, T["bell"] - 0.3, T["bell"] + 0.5))
        for j in range(11):
            h = lerp(tri[j], bell[j], m) * 190
            p.rrect(32 + j * 22, 320 - h, 16, h, 3, fill="output", fill_alpha=0.85)
        if m > 0:
            x = np.linspace(32, 268, 80)
            y = 320 - np.exp(-np.linspace(-2.3, 2.3, 80) ** 2 / 2) * 190 - 8
            p.poly(x, y, "#ffffff", 2.0, m)
    elif i == 2:
        cyc = (max(0.0, u) * 0.45) % 1.0
        xa = lerp(40, 260, cyc)
        p.rrect(115, 110, 70, 70, 4, fill="signal", fill_alpha=0.12, stroke="signal", width=2.0)
        p.rrect(xa - 35, 110, 70, 70, 4, fill="kernel", fill_alpha=0.12, stroke="kernel", width=2.0)
        ov = max(0.0, 70 - abs(xa - 150))
        if ov > 0:
            p.rrect(max(xa, 150) - 35, 110, ov, 70, 2, fill="overlap", fill_alpha=0.45)
        xs = np.linspace(40, xa, 60)
        ys = 320 - np.maximum(0, 70 - np.abs(xs - 150)) / 70 * 100
        p.poly(xs, ys, "output", 2.6, 1.0)
        p.line(30, 320, 270, 320, "line", 1.0, 1.0)
    elif i == 3:
        rect = skia.Rect.MakeXYWH(25, 72, 250, 221)
        phase = "sharp"
        if t >= T["blur"] - 0.1:
            phase = "blur"
        if t >= T["edges"] - 0.2:
            phase = "edge"
        if t >= T["neural"] - 0.1:
            phase = "filters"
        if phase != "filters":
            img = imgs[phase if phase != "sharp" else "sharp"]
            p.c.drawImageRect(img, rect, skia.SamplingOptions(skia.FilterMode.kNearest, skia.MipmapMode.kNone))
            p.rrect(25, 72, 250, 221, 6, stroke="line", width=1.2)
        else:
            from fx import image_from_array

            for j in range(16):
                r, c = divmod(j, 4)
                im = image_from_array(diverging(gab[j][0]))
                p.c.drawImageRect(im, skia.Rect.MakeXYWH(38 + c * 58, 78 + r * 54, 50, 50),
                                  skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone))
    else:
        MINI_THEOREM.draw(p, CARD_W / 2, 150, 0.62)
        mm = ease_io(lin(t, T["single"] - 0.6, T["single"] + 0.2))
        spec_f = [0.9, 0.6, 0.75, 0.45, 0.3, 0.5, 0.25]
        spec_g = [1.0, 0.85, 0.6, 0.5, 0.42, 0.3, 0.22]
        for j, (a, g) in enumerate(zip(spec_f, spec_g)):
            x = 40 + j * 33
            h = 110 * lerp(a, a * g, mm)
            p.rrect(x, 320 - h, 12, h, 3, fill=mix(SIG, OUT, mm), fill_alpha=0.85)
            p.rrect(x + 14, 320 - 110 * g, 12, 110 * g, 3, fill="kernel", fill_alpha=0.85 * (1 - mm))
    return surf.makeImageSnapshot()


def draw_cards(fr, t):
    vis = env(t, T["numbers"] - 0.6, T["single"] + 0.4, 0.4, 0.3)
    if vis <= 0.003:
        return
    collapse = ease_in(lin(t, T["collapses"] - 0.3, T["single"] - 0.05))
    for i, (_, _, key, nxt) in enumerate(CARDS):
        t0 = T[key] - 0.45
        if t < t0:
            continue
        e = lin(t, t0, t0 + 0.7)
        active = 1 - smooth(lin(t, T[nxt] - 0.4, T[nxt] + 0.1)) if i < 4 else 1.0
        alpha = smooth(lin(t, t0, t0 + 0.35)) * vis * (0.38 + 0.62 * active)
        angle = 1.2 * (1 - ease_out(e)) + (2 - i) * 0.12 * (1 - collapse)
        scale = lerp(0.9, 1.0, ease_out(e)) * (1 + 0.05 * active) * (1 - collapse * 0.92)
        cx = lerp(card_x(i), 960.0, ease_io(collapse))
        cy = CARD_Y - 18 * active * (1 - collapse)
        img = render_card(i, t, fr.k * max(scale, 0.05))
        fr.image_quad(img, card_quad(cx, cy, CARD_W, CARD_H, angle, scale), alpha)
        if active > 0.5 and collapse <= 0:
            fr.rrect(cx - CARD_W * scale / 2 - 6, cy - CARD_H * scale / 2 - 6, CARD_W * scale + 12, CARD_H * scale + 12, 28,
                     stroke="output", width=1.6, alpha=0.0, glow=0.25 * vis * active)


def draw_times(fr, t):
    """All sliding collapses into one multiplication, frequency by frequency."""
    a = env(t, T["single"] - 0.15, T["next"] + 0.2, 0.3, 0.4)
    if a <= 0.003:
        return
    g = back(ease_out(lin(t, T["single"] - 0.15, T["single"] + 0.45)), 1.4)
    p = 1 + 0.18 * (pulse(t, T["frequency"] - 0.05, 0.45) + pulse(t, T["freq2"] - 0.05, 0.45))
    r = 90 * g * p
    for k in (1, -1):
        fr.line(960 - r, 560 - k * r, 960 + r, 560 + k * r, "output", 14 * g, a, glow=1.2)
    fr.text("ONE MULTIPLICATION", 960, 760, "sans", 28, 700, "output", a * smooth(lin(t, T["single"] + 0.2, T["single"] + 0.7)),
            tracking=0.26)
    fr.text("FREQUENCY BY FREQUENCY", 960, 806, "sans", 22, 700, "muted", a * smooth(lin(t, T["frequency"], T["frequency"] + 0.5)),
            tracking=0.24)


# ------------------------------------------------------------------ S23: the quiet operation
def draw_close(fr, t):
    vis = env(t, T["next"] - 0.1, END, 0.4, 0.8)
    if vis <= 0.003:
        return
    from scenes.ch0_intro import CLAP, camera, nave_lines, project

    gather = ease_io(lin(t, T["same"] - 0.3, T["quiet"] + 0.4))
    # the nave returns behind everything
    nave_a = lerp(0.12, 0.35, gather) * vis * (1 - smooth(lin(t, END_AUDIO - 0.5, END_AUDIO + 1.0)))
    cam = camera(19.5)
    for pts, base, width in nave_lines():
        sx, sy, zc = project(pts, cam)
        d = float(zc.mean())
        fr.poly(sx, sy, "stone", width * max(0.55, min(1.6, 10.0 / d)), base * nave_a * max(0.14, min(1.0, 1.3 - d / 42)))
    # three callbacks
    vig = 1 - gather
    if vig > 0.003:
        ea = ease_out(lin(t, T["echo"] - 0.3, T["echo"] + 0.2)) * vis * vig
        for k in range(4):
            age = ((t - T["echo"]) * 0.7 + k * 0.25) % 1.0
            fr.circle(480, 560, 20 + 170 * age, "signal" if k == 0 else "kernel", 1.8, ea * (1 - age), glow=0.6)
        fr.text("AN ECHO", 480, 790, "sans", 22, 700, "signal", ea, tracking=0.22)
        from scenes.ch4_images import images

        pa = ease_out(lin(t, T["blurry"] - 0.3, T["blurry"] + 0.2)) * vis * vig
        if pa > 0:
            imgs = images()
            b = smooth(lin(t, T["photo"], T["photo"] + 0.6))
            rect = skia.Rect.MakeXYWH(960 - 150, 560 - 133, 300, 265)
            nearest = skia.SamplingOptions(skia.FilterMode.kNearest, skia.MipmapMode.kNone)
            fr.c.drawImageRect(imgs["sharp"], rect, nearest, skia.Paint(Color4f=skia.Color4f(1, 1, 1, pa * (1 - b))))
            fr.c.drawImageRect(imgs["blur"], rect, nearest, skia.Paint(Color4f=skia.Color4f(1, 1, 1, pa * b)))
            fr.text("A BLURRY PHOTO", 960, 790, "sans", 22, 700, "kernel", pa, tracking=0.22)
        da = ease_out(lin(t, T["pair"] - 0.4, T["pair"])) * vis * vig
        if da > 0:
            from scenes.ch2_dice import draw_die, die_pose
            from space import Camera

            dcam = Camera((0.0, 3.4, -10.0), (0.0, 0.0, 0.0), focal=700.0, center=(1440.0, 560.0))
            for j, (x, col, spin) in enumerate(((-1.4, "signal", 1.0), (1.4, "kernel", -1.0))):
                c, R, a = die_pose(t, T["pair"] - 0.45 + 0.1 * j, x, spin=spin)
                draw_die(fr, dcam, c, R, col, a * da)
            fr.text("A PAIR OF DICE", 1440, 790, "sans", 22, 700, "output", da, tracking=0.22)
    # the blend symbol hangs in the aisle, then becomes the wordmark
    word = ease_io(lin(t, T["conv2"] - 0.4, T["conv2"] + 0.4))
    sa = ease_out(lin(t, T["same"] - 0.2, T["operation"])) * vis * (1 - word)
    if sa > 0:
        sx, sy, _ = project(CLAP[None, :], cam)
        conv_symbol(fr, lerp(960, float(sx[0]), 0.0), 520, 70 * (1 + 0.08 * math.sin(t * 2.2)), sa, glow=1.0)
        fr.text("THE SAME QUIET OPERATION", 960, 700, "sans", 24, 700, "muted",
                sa * smooth(lin(t, T["quiet"], T["operation"] + 0.3)) * (1 - smooth(lin(t, T["if"] - 0.4, T["if"]))), tracking=0.26)
    end_m = ease_io(lin(t, END_AUDIO + 0.3, END_AUDIO + 1.3))
    if word > 0:
        size = lerp(130.0, 70.0, end_m)
        base = lerp(560.0, 200.0, end_m)
        f = font("display", size, 700)
        tracking = 0.04 * size
        title = "CONVOLUTION"
        widths = [f.measureText(ch) for ch in title]
        total = sum(widths) + tracking * (len(title) - 1)
        x = 960 - total / 2
        for i, ch in enumerate(title):
            ai = ease_out(lin(t, T["conv2"] - 0.3 + 0.03 * i, T["conv2"] + 0.1 + 0.03 * i)) * vis
            fr.text(ch, x, base + 20 * (1 - ai), "display", size, 700, "ink", ai, align="left", glow=0.2)
            x += widths[i] + tracking
        fr.line(960 - total * 0.51 * word, base + 0.26 * size, 960 + total * 0.51 * word, base + 0.26 * size, "overlap",
                1.0 + 3.2 * size / 150, vis, glow=0.9)
    # subscribe pill
    sb = ease_out(lin(t, T["subscribe"] - 0.2, T["subscribe"] + 0.3)) * vis * (1 - end_m)
    if sb > 0:
        w = lerp(40, 300, sb)
        fr.rrect(960 - w / 2, 690, w, 70, 35, fill="ink", fill_alpha=0.06, stroke="ink", width=2.0, alpha=sb,
                 glow=0.6 * pulse(t, T["subscribe"] + 0.2, 0.8))
        fr.text("SUBSCRIBE", 960, 735, "sans", 26, 700, "ink", sb * smooth(lin(sb, 0.6, 1.0)), tracking=0.24)
    # end screen: two slots for YouTube end-screen video elements
    if END_HOLD > 0 and end_m > 0:
        ea = end_m * vis
        fr.text("WATCH NEXT", 960, 330, "sans", 24, 700, "muted", ea, tracking=0.3)
        for cx, label, color in ((560.0, "FOURIER TRANSFORM", "signal"), (1360.0, "LAPLACE TRANSFORM", "kernel")):
            fr.rrect(cx - 340, 400, 680, 382, 18, fill="card", stroke=color, width=1.6, alpha=ea, glow=0.3)
            fr.text(label, cx, 830, "sans", 22, 700, color, ea, tracking=0.22)


# ------------------------------------------------------------------ assembly

def draw(t, size):
    t = t + START
    fr = Frame(size)
    draw_recipe(fr, t)
    draw_cards(fr, t)
    draw_times(fr, t)
    draw_close(fr, t)
    eyebrow(fr, t, "06 · RECAP", START + 0.15)
    return fr.finish()


def build(audio: bool = True):
    from faceless_champ import FunctionSource, Scene

    key = f"ch6:{Path(__file__).stat().st_mtime_ns}"
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
STILLS = [404.6, 407.0, 409.8, 412.6, 416.2, 419.8, 421.8, 425.0, 429.8, 431.2, 432.8, 436.0, 439.0, 440.6,
          443.4, 444.2, 445.8, 447.5, 450.6, 452.2, 456.0, 462.0]
