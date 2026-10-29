"""CHAPTER 4 - IMAGES (S14-S16), 04:27.440 - 05:21.280.

S14  An image is a grid of numbers   skyline -> 3D brightness terrain -> zoom into a 9x7 patch of
                                     pixel values; a 3x3 kernel multiplies, adds all nine, writes a
                                     new pixel, slides and repeats (real 1/9 averages).
S15  Blur and edges                  the kernel card fills with 1/9 (real 3x3 box blur, split view),
                                     then -1 0 +1 (flat sky reads 0, the moon's edge lights up,
                                     full real edge map).
S16  Networks learn their kernels    the image becomes the first plane of a 3D feature-map stack;
                                     a grid of learned-style filters (illustrative Gabor patterns)
                                     resolves from noise; the hand-built kernel docks next to its twin.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
from scipy import ndimage

from cues import AUDIO, cue
from fx import (
    Frame, back, ease_in, ease_io, ease_out, env, eyebrow, hex_rgb, image_from_array, lerp, lin, mix, pulse,
    smooth, tile, tokens,
)
from sources.test_image import skyline, tint
from space import orbit
from theme import H, THEME, TOKENS, W

START = cue(730)  # 267.44
END = cue(886)  # 321.28 "There's just one problem"

T = {
    "two": cue(734), "dimensions": cue(735), "image": cue(737), "grid": cue(740), "brightness": cue(742),
    "values": cue(743), "kernel": cue(745), "small_grid": cue(749), "three": cue(753), "place": cue(754),
    "pixels": cue(760), "multiply": cue(761), "weight": cue(766), "add": cue(769), "nine": cue(771),
    "write": cue(773), "new_image": cue(779), "slide": cue(781), "repeat": cue(786),
    "fill": cue(787), "ninth": cue(792), "everywhere": cue(793), "average": cue(799), "blurs": cue(805),
    "now": cue(806), "minus": cue(808), "left_col": cue(813), "zero": cue(814), "plus": cue(819),
    "right": cue(823), "flat": cue(825), "cancel": cue(830), "zero2": cue(832), "wherever": cue(834),
    "changes": cue(837), "lights": cue(840), "up": cue(841), "edge": cue(845), "detector": cue(846),
    "and": cue(847), "remarkable": cue(850), "cnn": cue(852), "kernels": cue(858), "learn": cue(862),
    "millions": cue(865), "first": cue(871), "layers": cue(872), "discover": cue(873), "edge2": cue(874),
    "like": cue(878), "built": cue(883), "hand": cue(885),
}
NEAREST = skia.SamplingOptions(skia.FilterMode.kNearest, skia.MipmapMode.kNone)
LINEAR = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone)
SIG, OUT = hex_rgb("signal"), hex_rgb("output")


# ------------------------------------------------------------------ data (all real convolutions)
@lru_cache(maxsize=1)
def low():
    """The skyline at 113x100 so individual pixels are visible."""
    img = skyline()[:, :339]
    return img.reshape(100, 3, 113, 3).mean(axis=(1, 3))


@lru_cache(maxsize=1)
def blocks():
    """34x30 block averages for the zoomed pixel patch (values 0..255)."""
    img = skyline()
    return np.rint(img.reshape(30, 10, 34, 10).mean(axis=(1, 3)) * 255).astype(int)


PATCH_R0, PATCH_C0, PATCH_ROWS, PATCH_COLS = 3, 18, 7, 9


@lru_cache(maxsize=1)
def patch():
    return blocks()[PATCH_R0:PATCH_R0 + PATCH_ROWS, PATCH_C0:PATCH_C0 + PATCH_COLS]


@lru_cache(maxsize=1)
def patch_out():
    p = patch().astype(float)
    out = np.zeros((PATCH_ROWS - 2, PATCH_COLS - 2))
    for r in range(PATCH_ROWS - 2):
        for c in range(PATCH_COLS - 2):
            out[r, c] = p[r:r + 3, c:c + 3].sum() / 9.0
    return np.rint(out).astype(int)


KX = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], float)


def correlate3(img, k):
    return ndimage.correlate(img, k, mode="nearest")


@lru_cache(maxsize=1)
def images():
    lo = low()
    blur = correlate3(lo, np.ones((3, 3)) / 9.0)
    gx = correlate3(lo, KX)
    gy = correlate3(lo, KX.T)
    edge_v = np.clip(np.abs(gx) / np.percentile(np.abs(gx), 99.0), 0, 1)
    edge_h = np.clip(np.abs(gy) / np.percentile(np.abs(gy), 99.0), 0, 1)
    diag = correlate3(lo, np.array([[0, 1, 1], [-1, 0, 1], [-1, -1, 0]], float))
    edge_d = np.clip(np.abs(diag) / np.percentile(np.abs(diag), 99.0), 0, 1)
    lap = correlate3(lo, np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float))
    edge_l = np.clip(np.abs(lap) / np.percentile(np.abs(lap), 99.0), 0, 1)
    mk = image_from_array
    return {
        "sharp": mk(tint(lo, SIG)),
        "blur": mk(tint(blur, SIG)),
        "edge": mk(tint(edge_v, OUT, highlight=0.25)),
        "dim": mk(tint(lo * 0.3, SIG, highlight=0.0)),
        "edge_h": mk(tint(edge_h, OUT, highlight=0.25)),
        "edge_d": mk(tint(edge_d, OUT, highlight=0.25)),
        "lap": mk(tint(edge_l, OUT, highlight=0.25)),
        "blur_feat": mk(tint(ndimage.uniform_filter(lo, 5), SIG)),
        "full": mk(tint(skyline(), SIG)),
    }


def kernel_response(row, col, k):
    """Correlate the 0..255 low-res image with kernel k at (row, col)."""
    lo = np.rint(low() * 255)
    return int(round((lo[row - 1:row + 2, col - 1:col + 2] * k).sum()))


def draw_image(fr, image, rect, alpha=1.0, sampling=NEAREST, src=None):
    if alpha <= 0.003:
        return
    x, y, w, h = rect
    s = skia.Rect.MakeWH(image.width(), image.height()) if src is None else skia.Rect.MakeLTRB(*src)
    fr.c.drawImageRect(image, s, skia.Rect.MakeXYWH(x, y, w, h), sampling,
                       skia.Paint(AntiAlias=True, Color4f=skia.Color4f(1, 1, 1, alpha)))


# ------------------------------------------------------------------ S14A: brightness terrain
GRID_W, GRID_H = 68, 60


@lru_cache(maxsize=1)
def terrain():
    img = skyline()
    return img.reshape(GRID_H, 5, GRID_W, 5).mean(axis=(1, 3))


def terrain_cam(t):
    up = ease_io(lin(t, T["image"] - 0.1, T["grid"] + 0.3))
    down = ease_io(lin(t, T["values"] + 0.1, T["kernel"] + 0.3))
    m = up * (1 - down)
    return orbit((0.0, 0.0, 0.0), 11.0, lerp(1.45, 0.62, m), lerp(0.0, -0.35, m), focal=1150.0,
                 center=(960.0, 560.0)), m


PLANE_W, PLANE_H = 4.6, 4.6 * 300 / 340


def plane_quad(cam):
    corners = np.array([[-PLANE_W, 0, PLANE_H], [PLANE_W, 0, PLANE_H], [PLANE_W, 0, -PLANE_H], [-PLANE_W, 0, -PLANE_H]])
    xs, ys, _ = cam.project(corners)
    return list(zip(xs, ys))


def draw_s14a(fr, t):
    vis = env(t, START + 0.4, T["three"] + 0.2, 0.6, 0.4)
    if vis <= 0.003:
        return
    cam, m = terrain_cam(t)
    imgs = images()
    zoom = ease_io(lin(t, T["kernel"] + 0.1, T["small_grid"] + 0.2))
    if zoom <= 0:
        fr.image_quad(imgs["full"], plane_quad(cam), vis * lerp(1.0, 0.12, m))
    # terrain rows, back to front, each filled black underneath so nearer rows occlude
    if m > 0.01:
        hgt = terrain()
        xs = np.linspace(-PLANE_W, PLANE_W, GRID_W)
        for r in range(GRID_H):
            z = lerp(PLANE_H, -PLANE_H, r / (GRID_H - 1))
            ys = hgt[r] * 2.2 * m
            pts = np.stack([xs, ys, np.full(GRID_W, z)], 1)
            px, py, _ = cam.project(pts)
            bx, by, _ = cam.project(np.array([[xs[-1], 0, z], [xs[0], 0, z]]))
            p = skia.Path()
            p.moveTo(float(px[0]), float(py[0]))
            for x, y in zip(px[1:], py[1:]):
                p.lineTo(float(x), float(y))
            p.lineTo(float(bx[0]), float(by[0]))
            p.lineTo(float(bx[1]), float(by[1]))
            p.close()
            fr.path_fill(p, "bg", vis * min(1.0, m * 3))
            depth = r / (GRID_H - 1)
            fr.poly(px, py, mix(TOKENS["signal"], "#ffffff", 0.15 * depth), 1.2, vis * m * (0.35 + 0.65 * depth), glow=0.25)
    # zoom into the patch: 2D image grows until the 9x7 patch fills the pixel grid
    if zoom > 0:
        quad = plane_quad(cam)
        x0, y0 = min(p[0] for p in quad), min(p[1] for p in quad)
        x1, y1 = max(p[0] for p in quad), max(p[1] for p in quad)
        start = (x0, y0, x1 - x0, y1 - y0)
        scale = CELL / 10.0
        end = (GX0 - PATCH_C0 * 10 * scale, GY0 - PATCH_R0 * 10 * scale, 340 * scale, 300 * scale)
        rect = tuple(lerp(a, b, zoom) for a, b in zip(start, end))
        fr.c.save()
        fr.c.clipRect(skia.Rect.MakeLTRB(0, 0, W, H))
        draw_image(fr, imgs["full"], rect, vis * (1 - smooth(lin(zoom, 0.7, 1.0))), LINEAR)
        fr.c.restore()
    fr.text("BRIGHTNESS", 960, 160, "sans", 24, 700, "signal", env(t, T["brightness"] - 0.2, T["kernel"], 0.3, 0.4) * vis,
            tracking=0.24)


# ------------------------------------------------------------------ S14B/C: pixel patch + sliding 3x3
CELL = 72.0
GX0, GY0 = 180.0, 300.0
OX0, OY0 = 1150.0, 372.0


def scan_positions():
    return [(r, c) for r in range(PATCH_ROWS - 2) for c in range(PATCH_COLS - 2)]


def scan_time(i):
    if i == 0:
        return T["place"]
    if i == 1:
        return T["slide"]
    return T["repeat"] - 0.6 + (i - 2) * 0.034


def frame_pos(t):
    """Fractional (row, col) of the kernel frame's top-left cell."""
    pos = scan_positions()
    r, c = 0.0, 0.0
    for i, (pr, pc) in enumerate(pos):
        ti = scan_time(i)
        if t >= ti:
            dur = 0.45 if i < 2 else 0.03
            u = back(lin(t, ti, ti + dur), 1.2) if i < 2 else lin(t, ti, ti + dur)
            prev = pos[i - 1] if i else (0, -2)
            r = lerp(prev[0], pr, u)
            c = lerp(prev[1], pc, u)
    return r, c


def draw_s14bc(fr, t):
    vis = env(t, T["small_grid"] - 0.1, T["fill"] + 0.1, 0.4, 0.45)
    if vis <= 0.003:
        return
    p = patch()
    fr.text("PIXELS", GX0, GY0 - 30, "sans", 22, 700, "signal", vis, align="left", tracking=0.2)
    for r in range(PATCH_ROWS):
        for c in range(PATCH_COLS):
            v = p[r, c] / 255.0
            x, y = GX0 + c * CELL, GY0 + r * CELL
            fr.rrect(x + 2, y + 2, CELL - 4, CELL - 4, 6, fill=mix(TOKENS["bg"], TOKENS["signal"], 0.15 + 0.85 * v), alpha=vis)
            fr.text(str(p[r, c]), x + CELL / 2, y + CELL / 2 + 7, "display", 20, 600, "ink" if v < 0.6 else "bg", vis * 0.9)
    # kernel frame
    ka = ease_out(lin(t, T["kernel"] + 0.6, T["three"] + 0.2)) * vis
    fr_r, fr_c = frame_pos(t)
    if ka > 0:
        x, y = GX0 + fr_c * CELL, GY0 + fr_r * CELL
        fr.rrect(x - 3, y - 3, 3 * CELL + 6, 3 * CELL + 6, 10, stroke="kernel", width=3.0, alpha=ka, glow=0.7)
        for k in range(1, 3):
            fr.line(x + k * CELL, y, x + k * CELL, y + 3 * CELL, "kernel", 1.2, ka * 0.6)
            fr.line(x, y + k * CELL, x + 3 * CELL, y + k * CELL, "kernel", 1.2, ka * 0.6)
        wa = ease_out(lin(t, T["weight"] - 0.4, T["weight"] + 0.2)) * ka
        for rr in range(3):
            for cc in range(3):
                fr.text("1/9", x + cc * CELL + CELL - 8, y + rr * CELL + 20, "display", 15, 600, "kernel", wa, align="right")
    fr.text("3 × 3 KERNEL", GX0 + 4.5 * CELL, GY0 + PATCH_ROWS * CELL + 46, "sans", 22, 700, "kernel",
            env(t, T["three"] - 0.3, T["multiply"] + 0.8, 0.3, 0.4) * vis, tracking=0.2)
    # first position: multiply sparks -> nine chips fly into one sum -> written into the new image
    mul = ease_out(lin(t, T["multiply"] - 0.1, T["multiply"] + 0.4))
    gather = ease_io(lin(t, T["add"] - 0.1, T["nine"] + 0.3))
    write = ease_io(lin(t, T["write"], T["new_image"] + 0.2))
    if mul > 0 and t < T["slide"]:
        tx, ty = GX0 + 4.5 * CELL, GY0 + PATCH_ROWS * CELL + 60
        for rr in range(3):
            for cc in range(3):
                cx0, cy0 = GX0 + (cc + 0.5) * CELL, GY0 + (rr + 0.5) * CELL
                x, y = lerp(cx0, tx, gather), lerp(cy0, ty, gather)
                a = mul * (1 - smooth(lin(gather, 0.8, 1.0))) * vis
                fr.circle(x, y, 14 + 10 * pulse(t, T["multiply"] + 0.05 * (rr * 3 + cc), 0.5), "overlap", 2.0, a, glow=0.6)
        sa = smooth(lin(gather, 0.75, 1.0)) * vis
        if sa > 0:
            sx = lerp(tx, OX0 + CELL / 2, write)
            sy = lerp(ty, OY0 + CELL / 2, write)
            fr.text(str(patch_out()[0, 0]), sx, sy + 12, "display", lerp(46, 22, write), 700, "output", sa * (1 - smooth(lin(write, 0.9, 1.0))),
                    glow=0.5)
            tokens(fr, [("÷", "muted", 1), ("9", "muted", 1)], tx + 110, ty + 14, 30, sa * (1 - write))
    # output grid (new image)
    oa = ease_out(lin(t, T["write"] - 0.4, T["write"] + 0.2)) * vis
    if oa > 0:
        fr.text("NEW IMAGE", OX0, OY0 - 30, "sans", 22, 700, "output", oa, align="left", tracking=0.2)
        po = patch_out()
        for i, (r, c) in enumerate(scan_positions()):
            x, y = OX0 + c * CELL, OY0 + r * CELL
            fr.rrect(x + 2, y + 2, CELL - 4, CELL - 4, 6, stroke="line", width=1.2, alpha=oa)
            done_t = T["new_image"] + 0.1 if i == 0 else scan_time(i) + (0.4 if i == 1 else 0.03)
            d = ease_out(lin(t, done_t, done_t + 0.25))
            if d > 0:
                v = po[r, c] / 255.0
                fr.rrect(x + 2, y + 2, CELL - 4, CELL - 4, 6, fill=mix(TOKENS["bg"], TOKENS["signal"], 0.15 + 0.85 * v), alpha=oa * d)
                fr.text(str(po[r, c]), x + CELL / 2, y + CELL / 2 + 7, "display", 20, 600, "ink" if v < 0.6 else "bg", oa * d * 0.9)
        # highlight current output cell
        fr_r_i, fr_c_i = int(round(fr_r)), int(round(fr_c))
        if t > T["write"] and 0 <= fr_r_i < PATCH_ROWS - 2 and 0 <= fr_c_i < PATCH_COLS - 2:
            fr.rrect(OX0 + fr_c_i * CELL, OY0 + fr_r_i * CELL, CELL, CELL, 8, stroke="output", width=2.4, alpha=oa, glow=0.6)
    fr.text("SLIDE · REPEAT", OX0 + 3.5 * CELL, OY0 + 5 * CELL + 60, "sans", 22, 700, "kernel",
            env(t, T["slide"] - 0.2, T["fill"], 0.3, 0.3) * vis, tracking=0.2)


# ------------------------------------------------------------------ S15: blur and edges
KC = 116.0
KX0, KY0 = 200.0, 400.0
IMG_RECT = (840.0, 250.0, 760.0, 760.0 * 100 / 113)


def kernel_card(fr, t, vis):
    fr.text("KERNEL", KX0, KY0 - 34, "sans", 24, 700, "kernel", vis, align="left", tracking=0.2)
    edge_mode = t >= T["now"] - 0.1
    reset = ease_io(lin(t, T["now"] - 0.1, T["now"] + 0.3))
    for r in range(3):
        for c in range(3):
            x, y = KX0 + c * (KC + 8), KY0 + r * (KC + 8)
            if not edge_mode:
                lab = "1/9"
                a = ease_out(lin(t, T["ninth"] - 0.4 + 0.05 * (r * 3 + c), T["ninth"] + 0.1 + 0.05 * (r * 3 + c)))
                col = "kernel"
            else:
                word = ("left_col", "zero", "right")[c]
                a = ease_out(lin(t, T[word] - 0.45 + 0.06 * r, T[word] - 0.05 + 0.06 * r))
                lab = ("−1", "0", "+1")[c]
                col = ("signal", "muted", "output")[c]
            fr.rrect(x, y, KC, KC, 14, fill="kernel", fill_alpha=0.06, stroke="kernel", width=2.0, alpha=vis)
            if a > 0:
                fr.rrect(x, y, KC, KC, 14, fill=col, fill_alpha=0.16 * a, alpha=vis)
                fr.text(lab, x + KC / 2, y + KC / 2 + 15, "display", 42, 600, col if edge_mode else "kernel", a * vis * (reset if edge_mode else 1))


def img_px(col, row):
    x, y, w, h = IMG_RECT
    return x + (col + 0.5) * w / 113, y + (row + 0.5) * h / 100


def draw_s15(fr, t):
    vis = env(t, T["fill"] - 0.2, T["and"] + 0.5, 0.45, 0.6)
    if vis <= 0.003:
        return
    imgs = images()
    kernel_card(fr, t, vis)
    x, y, w, h = IMG_RECT
    fr.rrect(x - 2, y - 2, w + 4, h + 4, 6, stroke="line", width=1.4, alpha=vis)
    edge_mode = t >= T["now"] - 0.1
    if not edge_mode:
        # amber scan line leaves the blurred image above it, then the split settles in the middle
        sweep = ease_io(lin(t, T["each_pix"] if "each_pix" in T else T["everywhere"] + 0.6, T["blurs"] - 0.6))
        split = ease_io(lin(t, T["blurs"] - 0.4, T["blurs"] + 0.3))
        cut = lerp(sweep, 0.5, split)
        if split <= 0:
            fr.c.drawImageRect(imgs["blur"], skia.Rect.MakeLTRB(0, 0, 113, 100 * sweep), skia.Rect.MakeXYWH(x, y, w, h * sweep), NEAREST,
                               skia.Paint(Color4f=skia.Color4f(1, 1, 1, vis)))
            fr.c.drawImageRect(imgs["sharp"], skia.Rect.MakeLTRB(0, 100 * sweep, 113, 100), skia.Rect.MakeXYWH(x, y + h * sweep, w, h * (1 - sweep)),
                               NEAREST, skia.Paint(Color4f=skia.Color4f(1, 1, 1, vis)))
            if 0 < sweep < 1:
                fr.line(x, y + h * sweep, x + w, y + h * sweep, "kernel", 2.4, vis, glow=0.8)
        else:
            fr.c.drawImageRect(imgs["sharp"], skia.Rect.MakeLTRB(0, 0, 113 * cut, 100), skia.Rect.MakeXYWH(x, y, w * cut, h), NEAREST,
                               skia.Paint(Color4f=skia.Color4f(1, 1, 1, vis)))
            fr.c.drawImageRect(imgs["blur"], skia.Rect.MakeLTRB(113 * cut, 0, 113, 100), skia.Rect.MakeXYWH(x + w * cut, y, w * (1 - cut), h),
                               NEAREST, skia.Paint(Color4f=skia.Color4f(1, 1, 1, vis)))
            fr.line(x + w * cut, y - 10, x + w * cut, y + h + 10, "kernel", 2.4, vis, glow=0.8)
            la = smooth(lin(t, T["blurs"] - 0.1, T["blurs"] + 0.4)) * vis
            fr.text("SHARP", x + w * 0.25, y + h + 46, "sans", 22, 700, "signal", la, tracking=0.2)
            fr.text("BLURRED", x + w * 0.75, y + h + 46, "sans", 22, 700, "kernel", la, tracking=0.2)
        return
    # edge mode: dim image, demo two positions, then the full real edge map
    scan = ease_io(lin(t, T["up"] + 0.1, T["detector"] - 0.2))
    draw_image(fr, imgs["dim"], IMG_RECT, vis)
    if scan > 0:
        fr.c.drawImageRect(imgs["edge"], skia.Rect.MakeLTRB(0, 0, 113, 100 * scan), skia.Rect.MakeXYWH(x, y, w, h * scan), NEAREST,
                           skia.Paint(Color4f=skia.Color4f(1, 1, 1, vis)))
        if scan < 1:
            fr.line(x, y + h * scan, x + w, y + h * scan, "kernel", 2.4, vis, glow=0.8)
    flat_rc, edge_rc = (20, 22), (25, 69)
    a_flat = env(t, T["flat"] - 0.2, T["wherever"] + 0.2, 0.3, 0.3)
    move = ease_io(lin(t, T["wherever"] - 0.2, T["changes"] - 0.2))
    a_edge = env(t, T["wherever"] - 0.2, T["up"] + 0.6, 0.2, 0.4)
    demo_a = max(a_flat, a_edge) * vis * (1 - scan)
    if demo_a > 0:
        r = lerp(flat_rc[0], edge_rc[0], move)
        c = lerp(flat_rc[1], edge_rc[1], move)
        cx, cy = img_px(c, r)
        s = 3 * w / 113
        fr.rrect(cx - s / 2 - 3, cy - s / 2 - 3, s + 6, s + 6, 4, stroke="kernel", width=2.6, alpha=demo_a, glow=0.9)
        val_flat = kernel_response(*flat_rc, KX)
        val_edge = kernel_response(*edge_rc, KX)
        lit = smooth(lin(t, T["lights"] - 0.3, T["lights"] + 0.1))
        val = val_flat if move < 0.5 else val_edge
        show = val if move < 0.5 else int(lerp(val_flat, val_edge, lit))
        color = mix(TOKENS["muted"], TOKENS["output"], lit if move >= 0.5 else 0.0)
        fr.text(f"{show:+d}" if show else "0", cx, cy - s / 2 - 26, "display", 46, 700, color, demo_a,
                glow=0.8 * lit * pulse(t, T["lights"], 0.8) + 0.3 * lit)
    fr.text("FLAT → 0", x + w * 0.2, y + h + 46, "sans", 22, 700, "muted", env(t, T["flat"], T["wherever"] + 0.3, 0.3, 0.3) * vis,
            tracking=0.2)
    fr.text("EDGE → LIGHTS UP", x + w * 0.75, y + h + 46, "sans", 22, 700, "output",
            env(t, T["lights"] - 0.3, T["detector"] - 0.1, 0.3, 0.3) * vis, tracking=0.2)
    fr.text("EDGE DETECTOR", x + w / 2, y + h + 46, "sans", 26, 700, "output",
            ease_out(lin(t, T["detector"] - 0.2, T["detector"] + 0.3)) * vis, tracking=0.24, glow=0.4)


# ------------------------------------------------------------------ S16: networks learn their own kernels
PLANES = ["full", "edge", "edge_h", "edge_d", "lap"]


def stack_cam(t):
    pull = ease_io(lin(t, T["learn"] - 0.4, T["millions"] + 0.4))
    return orbit((0.0, 0.0, 3.6), lerp(11.0, 12.5, pull), 0.24, lerp(-0.78, -0.92, pull) + 0.03 * math.sin(t * 0.5),
                 focal=1050.0, center=(lerp(960.0, 640.0, pull), 560.0))


def plane_corners(k):
    s = 0.86**k
    hw, hh = 2.6 * s, 2.6 * s * 100 / 113
    z = k * 1.9
    return np.array([[-hw, hh, z], [hw, hh, z], [hw, -hh, z], [-hw, -hh, z]]), hw, hh, z


def draw_s16(fr, t):
    vis = env(t, T["and"] - 0.2, END + 0.1, 0.5, 0.45)
    if vis <= 0.003:
        return
    imgs = images()
    cam = stack_cam(t)
    morph = ease_io(lin(t, T["and"] - 0.1, T["remarkable"] + 0.5))
    # planes far to near
    for k in reversed(range(len(PLANES))):
        appear = ease_out(lin(t, T["cnn"] - 0.3 + 0.18 * k, T["cnn"] + 0.3 + 0.18 * k)) if k else 1.0
        if appear <= 0:
            continue
        corners, hw, hh, z = plane_corners(k)
        xs, ys, _ = cam.project(corners)
        quad = list(zip(xs, ys))
        if k == 0:
            x, y, w, h = IMG_RECT
            flat = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            quad = [(lerp(a[0], b[0], morph), lerp(a[1], b[1], morph)) for a, b in zip(flat, quad)]
        fr.image_quad(imgs[PLANES[k]], quad, vis * appear * (0.95 if k == 0 else 0.85))
        p = skia.Path()
        p.addPoly([skia.Point(*q) for q in quad], True)
        fr.path_stroke(p, "signal" if k == 0 else "output", 1.6, vis * appear * 0.8, glow=0.4)
    # kernel square scanning the first plane, light streaming to the next plane
    sa = ease_out(lin(t, T["cnn"], T["cnn"] + 0.4)) * vis * (1 - smooth(lin(t, T["discover"], T["like"])))
    if sa > 0 and morph >= 1:
        u = (t - T["cnn"]) * 0.9
        col = (u * 6) % 1.0
        row = ((u * 6) // 1 % 5) / 5 + 0.1
        corners, hw, hh, z = plane_corners(0)
        px, py = -hw + 2 * hw * col, hh - 2 * hh * row
        sq = np.array([[px - 0.18, py + 0.18, z], [px + 0.18, py + 0.18, z], [px + 0.18, py - 0.18, z], [px - 0.18, py - 0.18, z]])
        xs, ys, _ = cam.project(sq)
        p = skia.Path()
        p.addPoly([skia.Point(float(a), float(b)) for a, b in zip(xs, ys)], True)
        fr.path_stroke(p, "kernel", 2.4, sa, glow=1.0)
        c2, hw2, hh2, z2 = plane_corners(1)
        src = cam.project(np.array([[px, py, z]]))
        dst = cam.project(np.array([[px * hw2 / hw, py * hh2 / hh, z2]]))
        fr.line(float(src[0][0]), float(src[1][0]), float(dst[0][0]), float(dst[1][0]), "kernel", 1.6, sa * 0.8, glow=0.8)
    fr.text("CONVOLUTIONAL NEURAL NETWORK", cam.cx, 180, "sans", 24, 700, "muted",
            env(t, T["cnn"] - 0.1, END, 0.4, 0.4) * vis, tracking=0.22)
    draw_filters(fr, t, vis)


@lru_cache(maxsize=1)
def gabors():
    n = 28
    yy, xx = np.mgrid[-1:1:complex(0, n), -1:1:complex(0, n)]
    out = []
    rng = np.random.default_rng(3)
    for i in range(16):
        theta = (i % 8) * math.pi / 8
        freq = 2.2 if i < 8 else 3.6
        xr = xx * math.cos(theta) + yy * math.sin(theta)
        g = np.exp(-(xx**2 + yy**2) / 0.5) * np.sin(math.pi * freq * xr + (0.0 if i < 8 else math.pi / 2))
        out.append((g / np.abs(g).max(), rng.normal(0, 0.6, (n, n))))
    return out


def diverging(v):
    v = np.clip(v, -1, 1)[..., None]
    pos = np.array(OUT)[None, None, :]
    neg = np.array(SIG)[None, None, :]
    rgb = np.where(v > 0, v * pos, -v * neg) * 0.95 + 0.02
    out = np.empty(v.shape[:2] + (4,), np.uint8)
    out[..., :3] = np.clip(rgb * 255, 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return out


FG_X0, FG_Y0, FG_C, FG_GAP = 1300.0, 300.0, 92.0, 10.0
HAND = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], float)


def draw_filters(fr, t, vis):
    ga = ease_out(lin(t, T["learn"] - 0.2, T["learn"] + 0.4)) * vis
    if ga <= 0:
        return
    fr.text("LEARNED FILTERS", FG_X0, FG_Y0 - 44, "sans", 22, 700, "output", ga, align="left", tracking=0.2)
    fr.text("illustrative", FG_X0 + 4 * (FG_C + FG_GAP) - FG_GAP, FG_Y0 - 44, "sans", 18, 500, "muted", ga, align="right")
    focus = smooth(lin(t, T["discover"] - 0.2, T["edge2"] + 0.3))
    for i, (g, noise) in enumerate(gabors()):
        r, c = divmod(i, 4)
        x, y = FG_X0 + c * (FG_C + FG_GAP), FG_Y0 + r * (FG_C + FG_GAP)
        u = ease_io(lin(t, T["millions"] - 0.6 + 0.07 * i, T["millions"] + 0.6 + 0.07 * i))
        v = lerp(noise, g, u)
        is_v = i % 8 == 0
        a = ga * (1 - 0.6 * focus * (0 if is_v else 1))
        draw_image(fr, image_from_array(diverging(v)), (x, y, FG_C, FG_C), a, LINEAR)
        fr.rrect(x, y, FG_C, FG_C, 6, stroke="output" if (is_v and focus > 0) else "line", width=2.4 if is_v else 1.2,
                 alpha=ga * (1 if is_v else a / max(ga, 1e-6)), glow=0.8 * focus if is_v else 0.0)
    # the hand-built kernel docks beside its learned twin
    ha = ease_io(lin(t, T["like"] - 0.4, T["built"] + 0.1)) * vis
    if ha > 0:
        y = FG_Y0 + 4 * (FG_C + FG_GAP) + 50
        x_learn, x_hand = FG_X0 + 40, FG_X0 + 250
        sx = lerp(KX0 + 180, x_hand, ha)
        sy = lerp(KY0 + 180, y, ha)
        g = gabors()[0][0]
        draw_image(fr, image_from_array(diverging(g)), (x_learn, y, FG_C, FG_C), ha, LINEAR)
        fr.rrect(x_learn, y, FG_C, FG_C, 6, stroke="output", width=2.2, alpha=ha, glow=0.5)
        fr.text("≈", (x_learn + FG_C + sx) / 2, y + FG_C / 2 + 18, "display", 54, 500, "ink", ha)
        draw_image(fr, image_from_array(diverging(HAND / 1.0)), (sx, sy, FG_C, FG_C), ha, NEAREST)
        fr.rrect(sx, sy, FG_C, FG_C, 6, stroke="kernel", width=2.2, alpha=ha, glow=0.5 + 0.8 * pulse(t, T["hand"] - 0.2, 0.8))
        fr.text("LEARNED", x_learn + FG_C / 2, y + FG_C + 34, "sans", 18, 700, "output", ha, tracking=0.16)
        fr.text("BY HAND", sx + FG_C / 2, sy + FG_C + 34, "sans", 18, 700, "kernel", ha, tracking=0.16)


# ------------------------------------------------------------------ assembly

def draw(t, size):
    t = t + START
    fr = Frame(size)
    draw_s14a(fr, t)
    draw_s14bc(fr, t)
    draw_s15(fr, t)
    draw_s16(fr, t)
    eyebrow(fr, t, "04 · IMAGES", START + 0.15)
    return fr.finish()


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
STILLS = [268.6, 270.2, 271.6, 273.0, 274.0, 276.6, 278.6, 280.4, 282.4, 284.6, 286.2, 288.0, 290.6, 292.9,
          295.2, 297.9, 300.0, 303.0, 304.6, 306.6, 308.5, 311.0, 314.0, 317.6, 320.2]
