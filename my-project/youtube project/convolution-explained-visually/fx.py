"""Skia drawing toolkit used inside Faceless Champ FunctionSources.

Everything is authored in 1920x1080 design pixels and scaled to the requested
output size, so previews (720p) and finals (1080p/4K) share one code path.
Glow is drawn on a quarter-resolution layer, blurred once per frame and added
on top, which is far cheaper than per-shape mask blurs.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia

from theme import H, TOKENS, W

LIB = Path(__file__).resolve().parents[3]
FONT_DIR = LIB / "assets" / "fonts"
FONT_FILES = {"display": "SpaceGrotesk[wght].ttf", "sans": "DMSans[opsz,wght].ttf"}
WGHT = 0x77676874
LINEAR = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone)

# ---------------------------------------------------------------- color


def hex_rgb(value: str):
    value = TOKENS.get(value, value).lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def col(value: str, alpha: float = 1.0) -> skia.Color4f:
    r, g, b = hex_rgb(value)
    return skia.Color4f(r, g, b, max(0.0, min(1.0, alpha)))


def mix(a: str, b: str, u: float) -> str:
    ra, rb = hex_rgb(a), hex_rgb(b)
    u = max(0.0, min(1.0, u))
    return "#" + "".join(f"{round((x + (y - x) * u) * 255):02x}" for x, y in zip(ra, rb))


# ---------------------------------------------------------------- easing


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lin(t, t0, t1):
    return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)


def smooth(u):
    return u * u * (3 - 2 * u)


def ease_out(u):
    return 1 - (1 - u) ** 3


def ease_in(u):
    return u**3


def ease_io(u):
    return 4 * u**3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def back(u, s=1.6):
    v = u - 1
    return 1 + (s + 1) * v**3 + s * v**2


def env(t, a, b, fin=0.4, fout=0.4):
    """Visibility envelope: fade in from a, fade out to zero at b."""
    if t < a or t > b:
        return 0.0
    return smooth(lin(t, a, a + fin)) * (1 - smooth(lin(t, b - fout, b)))


def lerp(a, b, u):
    return a + (b - a) * u


def pulse(t, at, width=0.5):
    """0 -> 1 -> 0 bump centred just after ``at``."""
    u = lin(t, at, at + width)
    return math.sin(math.pi * u) if 0 < u < 1 else 0.0


# ---------------------------------------------------------------- fonts


@lru_cache(maxsize=32)
def typeface(family: str, weight: int):
    tf = skia.Typeface.MakeFromFile(str(FONT_DIR / FONT_FILES[family]))
    coord = skia.FontArguments.VariationPosition.Coordinate(WGHT, float(weight))
    args = skia.FontArguments()
    args.setVariationDesignPosition(
        skia.FontArguments.VariationPosition(skia.FontArguments.VariationPosition.Coordinates([coord]))
    )
    return tf.makeClone(args)


def font(family: str, size: float, weight: int = 500) -> skia.Font:
    f = skia.Font(typeface(family, weight), size)
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
    f.setHinting(skia.FontHinting.kNone)
    return f


def text_width(s: str, f: skia.Font, tracking: float = 0.0) -> float:
    if not tracking:
        return f.measureText(s)
    return sum(f.measureText(ch) for ch in s) + tracking * f.getSize() * (len(s) - 1)


# ---------------------------------------------------------------- image helpers


def image_from_array(arr: np.ndarray) -> skia.Image:
    """uint8 RGBA (straight, opaque or not) -> skia.Image."""
    arr = np.ascontiguousarray(arr)
    return skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)


def quad_matrix(src_w, src_h, quad):
    m = skia.Matrix()
    m.setPolyToPoly(
        [skia.Point(0, 0), skia.Point(src_w, 0), skia.Point(src_w, src_h), skia.Point(0, src_h)],
        [skia.Point(*p) for p in quad],
    )
    return m


def card_quad(cx, cy, w, h, angle, scale=1.0, persp=1500.0):
    """Corners of a card rotated about its vertical axis (radians), perspective-projected."""
    hw, hh = w / 2 * scale, h / 2 * scale
    dx = hw * math.cos(angle)
    dz = hw * math.sin(angle)
    sl = persp / (persp - dz)
    sr = persp / (persp + dz)
    return [
        (cx - dx * sl, cy - hh * sl),
        (cx + dx * sr, cy - hh * sr),
        (cx + dx * sr, cy + hh * sr),
        (cx - dx * sl, cy + hh * sl),
    ]


# ---------------------------------------------------------------- frame


class Frame:
    """One output frame: crisp canvas ``c`` plus quarter-res glow canvas ``g``."""

    def __init__(self, size, background="#000000"):
        self.w, self.h = int(size[0]), int(size[1])
        self.k = self.w / W
        self.arr = np.zeros((self.h, self.w, 4), np.uint8)
        self.surface = skia.Surface(self.arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        self.c = self.surface.getCanvas()
        self.c.clear(col(background))
        self.c.scale(self.k, self.k)
        self.gw, self.gh = max(2, self.w // 4), max(2, self.h // 4)
        self.gsurf = skia.Surface(self.gw, self.gh)
        self.g = self.gsurf.getCanvas()
        self.g.clear(skia.ColorTRANSPARENT)
        self.g.scale(self.gw / W, self.gh / H)
        self.glow_used = False

    # -- primitives -------------------------------------------------------
    @staticmethod
    def _stroke(color, width, alpha, cap=skia.Paint.kRound_Cap):
        return skia.Paint(
            AntiAlias=True,
            Style=skia.Paint.kStroke_Style,
            StrokeWidth=width,
            StrokeCap=cap,
            StrokeJoin=skia.Paint.kRound_Join,
            Color4f=col(color, alpha),
        )

    @staticmethod
    def _fill(color, alpha):
        return skia.Paint(AntiAlias=True, Style=skia.Paint.kFill_Style, Color4f=col(color, alpha))

    def path_stroke(self, path, color, width=2.0, alpha=1.0, glow=0.0, glow_width=None):
        if alpha <= 0.003:
            return
        self.c.drawPath(path, self._stroke(color, width, alpha))
        if glow > 0:
            self.glow_used = True
            self.g.drawPath(path, self._stroke(color, glow_width or max(6.0, width * 3.5), alpha * glow))

    def path_fill(self, path, color, alpha=1.0, glow=0.0):
        if alpha <= 0.003:
            return
        self.c.drawPath(path, self._fill(color, alpha))
        if glow > 0:
            self.glow_used = True
            self.g.drawPath(path, self._fill(color, alpha * glow))

    def poly(self, xs, ys, color, width=2.0, alpha=1.0, glow=0.0, close=False):
        if len(xs) < 2 or alpha <= 0.003:
            return
        p = skia.Path()
        p.moveTo(float(xs[0]), float(ys[0]))
        for x, y in zip(xs[1:], ys[1:]):
            p.lineTo(float(x), float(y))
        if close:
            p.close()
        self.path_stroke(p, color, width, alpha, glow)

    def line(self, x0, y0, x1, y1, color, width=2.0, alpha=1.0, glow=0.0):
        self.poly([x0, x1], [y0, y1], color, width, alpha, glow)

    def circle(self, x, y, r, color, width=2.0, alpha=1.0, glow=0.0, fill=False):
        if alpha <= 0.003 or r <= 0:
            return
        p = skia.Path()
        p.addCircle(float(x), float(y), float(r))
        (self.path_fill if fill else self.path_stroke)(p, color, alpha=alpha, glow=glow, **({} if fill else {"width": width}))

    def rrect(self, x, y, w, h, r, fill=None, stroke=None, width=1.5, alpha=1.0, fill_alpha=None, glow=0.0):
        p = skia.Path()
        p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r))
        if fill:
            self.path_fill(p, fill, alpha if fill_alpha is None else fill_alpha * alpha)
        if stroke:
            self.path_stroke(p, stroke, width, alpha, glow)

    def glow_dot(self, x, y, r, color, alpha=1.0, strength=1.0):
        self.circle(x, y, r, color, alpha=alpha, fill=True)
        self.glow_used = True
        self.g.drawCircle(float(x), float(y), float(r * 3.2), self._fill(color, alpha * strength))

    def text(self, s, x, y, family="sans", size=28, weight=500, color="ink", alpha=1.0, align="center",
             tracking=0.0, glow=0.0):
        """Draw text with its *baseline* at y."""
        if alpha <= 0.003 or not s:
            return
        f = font(family, size, weight)
        width = text_width(s, f, tracking)
        x0 = x - width / 2 if align == "center" else x - width if align == "right" else x
        paint = skia.Paint(AntiAlias=True, Color4f=col(color, alpha))
        gpaint = skia.Paint(AntiAlias=True, Color4f=col(color, alpha * glow)) if glow > 0 else None
        if not tracking:
            self.c.drawString(s, x0, y, f, paint)
            if gpaint:
                self.glow_used = True
                self.g.drawString(s, x0, y, f, gpaint)
            return
        cx = x0
        for ch in s:
            self.c.drawString(ch, cx, y, f, paint)
            if gpaint:
                self.glow_used = True
                self.g.drawString(ch, cx, y, f, gpaint)
            cx += f.measureText(ch) + tracking * size

    def image_quad(self, image, quad, alpha=1.0):
        if alpha <= 0.003:
            return
        self.c.save()
        self.c.concat(quad_matrix(image.width(), image.height(), quad))
        self.c.drawImage(image, 0, 0, LINEAR, skia.Paint(AntiAlias=True, Color4f=col("#ffffff", alpha)))
        self.c.restore()

    # -- output -------------------------------------------------------------
    def finish(self) -> np.ndarray:
        if self.glow_used:
            snap = self.gsurf.makeImageSnapshot()
            blur = skia.Surface(self.gw, self.gh)
            bc = blur.getCanvas()
            bc.clear(skia.ColorTRANSPARENT)
            sigma = max(1.0, 3.2 * self.gw / 480)
            bc.drawImage(snap, 0, 0, LINEAR, skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma)))
            bc.drawImage(
                snap, 0, 0, LINEAR,
                skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma * 3, sigma * 3), BlendMode=skia.BlendMode.kPlus),
            )
            img = blur.makeImageSnapshot()
            self.c.save()
            self.c.resetMatrix()
            self.c.drawImageRect(img, skia.Rect.MakeWH(self.w, self.h), LINEAR, skia.Paint(BlendMode=skia.BlendMode.kPlus))
            self.c.restore()
        self.arr[..., 3] = 255
        return self.arr


class _NullCanvas:
    """Swallows glow calls when drawing into an offscreen card."""

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class Pen(Frame):
    """Frame drawing helpers on an existing skia canvas (no glow layer)."""

    def __init__(self, canvas):  # noqa: D401 - intentionally skips Frame.__init__
        self.c = canvas
        self.g = _NullCanvas()
        self.glow_used = False


def offscreen(w: float, h: float, k: float):
    """Transparent surface for a ``w x h`` design-pixel card at output scale ``k``."""
    surf = skia.Surface(max(2, int(round(w * k))), max(2, int(round(h * k))))
    canvas = surf.getCanvas()
    canvas.clear(skia.ColorTRANSPARENT)
    canvas.scale(k, k)
    return surf, Pen(canvas)


# ---------------------------------------------------------------- shared motifs


def tile(fr, cx, cy, size, label, color, alpha=1.0, lit=0.0, scale_x=1.0, text_color=None, font_scale=0.46,
         glow=0.0):
    """Rounded number tile: token-colored stroke, faint tinted face, big numeral."""
    if alpha <= 0.003:
        return
    w = size * abs(scale_x)
    fr.rrect(cx - w / 2, cy - size / 2, w, size, size * 0.16, fill=color, fill_alpha=(0.10 + 0.22 * lit) * alpha,
             stroke=color, width=2.2, alpha=alpha, glow=glow + 0.6 * lit)
    if label and abs(scale_x) > 0.15:
        fr.c.save()
        fr.c.translate(cx, cy)
        fr.c.scale(abs(scale_x), 1.0)
        fr.text(label, 0, size * font_scale * 0.36, "display", size * font_scale, 600, text_color or "ink", alpha)
        fr.c.restore()


def eyebrow(fr, t, label, t0, hold=3.0):
    a = env(t, t0, t0 + hold, 0.5, 0.6)
    if a <= 0.003:
        return
    x, y = 96.0, 96.0
    fr.line(x, y - 8, x + 28 * ease_out(lin(t, t0, t0 + 0.5)), y - 8, "kernel", 2.4, a)
    fr.text(label, x + 44, y, "sans", 22, 700, "muted", a, align="left", tracking=0.22)


def tokens(fr, items, cx, y, size=40, alpha=1.0, family="display", weight=600, gap=0.28):
    """Centered row of (text, color, alpha) tokens; returns the x-centers."""
    f = font(family, size, weight)
    widths = [size * 0.62 if s == "⊛" else f.measureText(s) for s, _, _ in items]
    space = size * gap
    total = sum(widths) + space * (len(items) - 1)
    x = cx - total / 2
    centers = []
    for (s, color, a), w in zip(items, widths):
        if s == "⊛":
            conv_symbol(fr, x + w / 2, y - size * 0.34, size * 0.27, a * alpha, color)
        else:
            fr.text(s, x, y, family, size, weight, color, a * alpha, align="left")
        centers.append(x + w / 2)
        x += w + space
    return centers


def conv_symbol(fr, x, y, r, alpha=1.0, color="overlap", rot=0.0, glow=0.6):
    """The convolution operator: a circled asterisk (fonts lack U+229B)."""
    if alpha <= 0.003:
        return
    w = max(1.6, r * 0.12)
    fr.circle(x, y, r, color, width=w, alpha=alpha, glow=glow)
    for k in range(3):
        a = rot + k * math.pi / 3 + math.pi / 2
        dx, dy = 0.5 * r * math.cos(a), 0.5 * r * math.sin(a)
        fr.line(x - dx, y - dy, x + dx, y + dy, color, w, alpha, glow=glow)
