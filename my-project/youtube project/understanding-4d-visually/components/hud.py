"""HUD pieces shared by every chapter: glass cards, pills, readouts, arrows, axes, floors, eyebrows."""

from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia
import typmath
from fx import LINEAR, col, ease_out, env, font, lin, smooth
from theme import TOKENS

# ------------------------------------------------------------------ glass card (cached, lit bevel)


@lru_cache(maxsize=64)
def _glass_image(w: int, h: int, r: int, k: float, tint: str):
    """A dark translucent card with a gradient rim and a specular bevel (Skia lighting), rendered once per size."""
    pw, ph = max(2, int(round(w * k))), max(2, int(round(h * k)))
    surf = skia.Surface(pw, ph)
    c = surf.getCanvas()
    c.clear(skia.ColorTRANSPARENT)
    c.scale(k, k)
    rect = skia.Rect.MakeXYWH(1, 1, w - 2, h - 2)
    rr = skia.RRect.MakeRectXY(rect, r, r)
    body = skia.GradientShader.MakeLinear(
        [skia.Point(0, 0), skia.Point(0, h)], [col("#0E131C", 0.88), col("#04060A", 0.82)]
    )
    c.drawRRect(rr, skia.Paint(AntiAlias=True, Shader=body))
    if tint != "none":
        c.drawRRect(rr, skia.Paint(AntiAlias=True, Color4f=col(tint, 0.05)))
    # Bevel: a blurred alpha mask lit by a distant specular light, kept inside the card.
    mask = skia.Paint(AntiAlias=True, Color4f=col("#ffffff", 1.0))
    lit = skia.ImageFilters.DistantLitSpecular(
        skia.Point3(-0.45, -0.75, 0.48), skia.Color4f(1, 1, 1, 1).toColor(), 2.2, 0.55, 18.0,
        skia.ImageFilters.Blur(3.0, 3.0),
    )
    c.save()
    c.clipRRect(rr, doAntiAlias=True)
    c.saveLayer(None, skia.Paint(ImageFilter=lit, Alphaf=0.22, BlendMode=skia.BlendMode.kPlus))
    c.drawRRect(rr, mask)
    c.restore()
    c.restore()
    rim = skia.GradientShader.MakeLinear(
        [skia.Point(0, 0), skia.Point(w, h)],
        [col(TOKENS["ink"], 0.34), col(TOKENS["line"], 0.9), col(TOKENS["ink"], 0.14)],
        [0.0, 0.55, 1.0],
    )
    c.drawRRect(rr, skia.Paint(AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=1.2, Shader=rim))
    c.drawLine(r, 2.2, w - r, 2.2, skia.Paint(AntiAlias=True, StrokeWidth=1.0, Color4f=col("#ffffff", 0.10)))
    return surf.makeImageSnapshot()


def glass_card(fr, x, y, w, h, alpha=1.0, r=18, tint="none", glow=0.0, glow_color="w"):
    """Glass plaque with its top-left corner at (x, y) in design px."""
    if alpha <= 0.003:
        return
    img = _glass_image(int(round(w)), int(round(h)), int(r), round(fr.k, 4), tint)
    fr.c.drawImageRect(img, skia.Rect.MakeXYWH(x, y, w, h), LINEAR, skia.Paint(AntiAlias=True, Alphaf=alpha))
    if glow > 0:
        p = skia.Path()
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
        fr.glow_used = True
        fr.g.drawPath(p, fr._stroke(glow_color, 6.0, alpha * glow))


# ------------------------------------------------------------------ text helpers


def tabular(fr, s, x, y, size=30, color="ink", alpha=1.0, family="sans", weight=600, align="center", glow=0.0):
    """Text with fixed-advance digits so counters and readouts never jitter."""
    if alpha <= 0.003 or not s:
        return 0.0
    f = font(family, size, weight)
    adv = f.measureText("0")
    widths = [adv if ch.isdigit() else f.measureText(ch) for ch in s]
    total = sum(widths)
    cx = x - total / 2 if align == "center" else x - total if align == "right" else x
    for ch, wd in zip(s, widths):
        off = (wd - f.measureText(ch)) / 2
        fr.text(ch, cx + off, y, family, size, weight, color, alpha, align="left", glow=glow)
        cx += wd
    return total


def pill(fr, cx, cy, text, color="ink", alpha=1.0, size=24, fill=0.10, glow=0.3, family="sans", weight=600):
    """Capsule label (e.g. '1D', '3D -> 2D')."""
    if alpha <= 0.003:
        return
    f = font(family, size, weight)
    w = f.measureText(text) + size * 1.4
    h = size * 1.75
    fr.rrect(cx - w / 2, cy - h / 2, w, h, h / 2, fill=color, fill_alpha=fill * alpha, stroke=color, width=1.6,
             alpha=alpha, glow=glow)
    fr.text(text, cx, cy + size * 0.36, family, size, weight, color, alpha)


def readout(fr, x, y, label, value, color="ink", alpha=1.0, size=30, card=True, align="center"):
    """A glass chip '<label> <value>' with a tabular value, centred on (x, y)."""
    if alpha <= 0.003:
        return
    lf = font("sans", size * 0.62, 600)
    vf = font("sans", size, 600)
    math_label = bool(label) and any(ord(ch) > 127 for ch in label)  # Greek etc.: DM Sans has no glyphs, use Typst
    if math_label:
        lw = typmath.size_of(label, size * 0.8)[0]
    else:
        lw = lf.measureText(label) if label else 0.0
    digit = vf.measureText("0")
    vw = sum(digit if ch.isdigit() else vf.measureText(ch) for ch in value)
    gap = size * 0.4 if label else 0.0
    total = lw + gap + vw
    w, h = total + size * 1.1, size * 1.8
    left = x - w / 2 if align == "center" else x
    if card:
        glass_card(fr, left, y - h / 2, w, h, alpha, r=int(h / 2.6))
    tx = left + size * 0.55
    if math_label:
        typmath.draw(fr, label, tx + lw / 2, y, size * 0.8, color="muted", alpha=alpha)
    elif label:
        fr.text(label, tx, y + size * 0.22, "sans", size * 0.62, 600, "muted", alpha, align="left")
    tabular(fr, value, tx + lw + gap, y + size * 0.36, size, color, alpha, align="left")


def coord_chip(fr, cx, cy, values, colors, alpha=1.0, size=30.0, flash=None, card=True, gap=1.0):
    """Glass chip '(2.4, 1.8, 2.6)' with each component in its axis colour; returns the x centre of each value.

    values: preformatted strings; flash: {index: 0..1} brightens and glows a component; gap (>= 1) spreads the
    components apart ("independent numbers"). The layout is returned even at alpha 0, so other elements can
    take over the numbers' positions.
    """
    if not values:
        return []
    draw = alpha > 0.003
    f = font("sans", size, 600)
    digit = f.measureText("0")

    def width(s):
        return sum(digit if ch.isdigit() else f.measureText(ch) for ch in s)

    comma, paren = f.measureText(", ") * gap, f.measureText("(")
    widths = [width(v) for v in values]
    total = 2 * paren + sum(widths) + comma * (len(values) - 1)
    if card and draw:
        w, h = total + size * 1.3, size * 1.9
        glass_card(fr, cx - w / 2, cy - h / 2, w, h, alpha, r=int(h / 2.6))
    x = cx - total / 2
    base = cy + size * 0.36
    if draw:
        fr.text("(", x, base, "sans", size, 500, "muted", alpha, align="left")
    x += paren
    centers = []
    flash = flash or {}
    for i, (v, c, wv) in enumerate(zip(values, colors, widths)):
        fl = flash.get(i, 0.0)
        if draw:
            tabular(fr, v, x, base, size * (1 + 0.12 * fl), c, alpha, align="left", glow=0.9 * fl)
        centers.append(x + wv / 2)
        x += wv
        if i < len(values) - 1:
            if draw:
                fr.text(",", x, base, "sans", size, 500, "muted", alpha, align="left")
            x += comma
    if draw:
        fr.text(")", x, base, "sans", size, 500, "muted", alpha, align="left")
    return centers


def eyebrow(fr, t, label, t0, hold=2.5):
    """Chapter marker in the top-left safe area: '01 · DIMENSIONS'."""
    a = env(t, t0, t0 + hold, 0.5, 0.6)
    if a <= 0.003:
        return
    x, y = 96.0, 96.0
    fr.line(x, y - 8, x + 28 * ease_out(lin(t, t0, t0 + 0.5)), y - 8, "w", 2.4, a, glow=0.4)
    fr.text(label, x + 44, y, "sans", 22, 700, "muted", a, align="left", tracking=0.22)


# ------------------------------------------------------------------ arrows and axes


def arrow_head(fr, x0, y0, x1, y1, color, alpha, size=16.0, glow=0.5):
    ang = math.atan2(y1 - y0, x1 - x0)
    pts = [(x1, y1)] + [(x1 - size * math.cos(ang + s * 0.42), y1 - size * math.sin(ang + s * 0.42)) for s in (1, -1)]
    path = skia.Path()
    path.addPoly([skia.Point(float(x), float(y)) for x, y in pts], True)
    fr.path_fill(path, color, alpha, glow=glow)


def arrow(fr, x0, y0, x1, y1, color, width=2.6, alpha=1.0, glow=0.6, head=16.0, dashed=False):
    """2D arrow; the shaft stops short of the tip so the head stays sharp."""
    if alpha <= 0.003:
        return
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1e-3:
        return
    back = min(head * 0.7, L) / L
    xe, ye = x1 - (x1 - x0) * back, y1 - (y1 - y0) * back
    if dashed:
        fr.dashed([x0, xe], [y0, ye], color, width, alpha, glow)
    else:
        fr.line(x0, y0, xe, ye, color, width, alpha, glow)
    arrow_head(fr, x0, y0, x1, y1, color, alpha, min(head, L * 0.6), glow)


def arrow3d(fr, cam, p0, p1, color, width=2.6, alpha=1.0, glow=0.6, head=16.0, dashed=False):
    xs, ys, z = cam.project(np.array([p0, p1], float))
    if np.all(z > 0.05):
        arrow(fr, xs[0], ys[0], xs[1], ys[1], color, width, alpha, glow, head, dashed)
    return xs, ys


def axis3d(fr, cam, origin, vec, name, color, u=1.0, label_alpha=None, width=2.4, size=0.42, dashed=False):
    """An axis drawing on (u: 0 -> 1) with an italic letter past its tip."""
    from space import text3d

    if u <= 0:
        return
    origin = np.asarray(origin, float)
    vec = np.asarray(vec, float)
    arrow3d(fr, cam, origin, origin + vec * u, color, width, 0.95, 0.6, dashed=dashed)
    la = smooth(lin(u, 0.6, 1.0)) if label_alpha is None else label_alpha
    text3d(fr, cam, name, origin + vec * (u + 0.08), size, color, la, 500, "italic")


def right_angle(fr, cam, corner, d1, d2, size=0.22, color="ink", alpha=1.0):
    """Small square marker in 3D where directions d1 and d2 meet at ``corner``."""
    c = np.asarray(corner, float)
    d1 = np.asarray(d1, float) / np.linalg.norm(d1) * size
    d2 = np.asarray(d2, float) / np.linalg.norm(d2) * size
    xs, ys, z = cam.project(np.array([c + d1, c + d1 + d2, c + d2]))
    if np.all(z > 0.05):
        fr.poly(xs, ys, color, 1.6, alpha)


def dot_grid(fr, cam, height=0.0, extent=7.0, spacing=0.5, alpha=0.10, radius=1.6, center=(0.0, 0.0), reveal=None):
    """Perspective dot floor (view y = height) fading with distance. ``reveal`` grows it from the centre."""
    if alpha <= 0.003:
        return
    ticks = np.arange(-extent, extent + 1e-6, spacing)
    gx, gz = np.meshgrid(ticks + center[0], ticks + center[1])
    pts = np.stack([gx.ravel(), np.full(gx.size, height), gz.ravel()], 1)
    dist = np.hypot(pts[:, 0] - center[0], pts[:, 2] - center[1])
    xs, ys, z = cam.project(pts)
    fog = np.clip(1.15 - dist / extent, 0, 1)
    if reveal is not None:
        fog *= np.clip((reveal * (extent + 1) - dist) / 1.2, 0, 1)
    for x, y, zz, f in zip(xs, ys, z, fog):
        if zz > 0.2 and f > 0.02:
            fr.circle(x, y, radius * min(1.6, 6.0 / zz) ** 0.5, "#8FA0BF", alpha=alpha * f, fill=True)
