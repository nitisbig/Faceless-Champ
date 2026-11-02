"""Skia drawing toolkit used inside Faceless Champ FunctionSources.

Adapted from convolution-explained-visually/fx.py; adds blend-aware image quads
and the cinematic finish (letterbox, vignette, film grain).

Everything is authored in 1920x1080 design pixels and scaled to the requested
output size, so previews (720p) and finals (1080p/4K) share one code path.
Glow is drawn on a quarter-resolution layer, blurred once per frame and added
on top, which is far cheaper than per-shape mask blurs.
"""

from __future__ import annotations

import contextlib
import math
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia
from theme import TOKENS, H, W

LIB = Path(__file__).resolve().parents[3]
FONT_DIR = LIB / "assets" / "fonts"
FONT_FILES = {
    "display": "SpaceGrotesk[wght].ttf",
    "sans": "DMSans[opsz,wght].ttf",
    "italic": "CormorantGaramond-Italic[wght].ttf",
}
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
    return lo if x < lo else min(x, hi)


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


def text_path(s: str, x: float, y: float, family="display", size=64.0, weight=600, align="center",
              tracking=0.0) -> skia.Path:
    """Outline of a text run (baseline at y) for clipping light sweeps or tracing titles."""
    f = font(family, size, weight)
    width = text_width(s, f, tracking)
    cx = x - width / 2 if align == "center" else x - width if align == "right" else x
    out = skia.Path()
    for ch in s:
        glyph = f.textToGlyphs(ch)
        if len(glyph):
            p = f.getPath(glyph[0])
            if p is not None:
                p.offset(cx, y)
                out.addPath(p)
        cx += f.measureText(ch) + tracking * size
    return out


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


@lru_cache(maxsize=6)
def _grain_tile(seed: int) -> skia.Image:
    rng = np.random.default_rng(seed)
    v = np.clip(rng.normal(128, 46, (384, 384)), 0, 255).astype(np.uint8)
    rgba = np.dstack([v, v, v, np.full_like(v, 255)])
    return image_from_array(rgba)


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
        self.gw, self.gh = max(2, self.w // 2), max(2, self.h // 2)  # half-res glow: tight, crisp halos
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
            self.g.drawPath(path, self._stroke(color, glow_width or max(4.0, width * 2.4), alpha * glow))

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
        self.g.drawCircle(float(x), float(y), float(r * 2.2), self._fill(color, alpha * strength))

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

    def image_quad(self, image, quad, alpha=1.0, blend=None):
        if alpha <= 0.003:
            return
        paint = skia.Paint(AntiAlias=True, Color4f=col("#ffffff", alpha))
        if blend is not None:
            paint.setBlendMode(blend)
        self.c.save()
        self.c.concat(quad_matrix(image.width(), image.height(), quad))
        self.c.drawImage(image, 0, 0, LINEAR, paint)
        self.c.restore()

    def image_fill(self, image, scale=1.0, alpha=1.0):
        """Image covering the frame, scaled about the centre (push-ins)."""
        if alpha <= 0.003:
            return
        w, h = W * scale, H * scale
        rect = skia.Rect.MakeXYWH((W - w) / 2, (H - h) / 2, w, h)
        self.c.drawImageRect(image, rect, LINEAR, skia.Paint(AntiAlias=True, Color4f=col("#ffffff", alpha)))

    def dashed(self, xs, ys, color, width=2.0, alpha=1.0, glow=0.0, on=12.0, off=9.0, phase=0.0):
        """Dashed polyline (the 'cannot picture it' w arrow, projection drop-lines)."""
        if len(xs) < 2 or alpha <= 0.003:
            return
        p = skia.Path()
        p.moveTo(float(xs[0]), float(ys[0]))
        for x, y in zip(xs[1:], ys[1:]):
            p.lineTo(float(x), float(y))
        effect = skia.DashPathEffect.Make([on, off], phase)
        paint = self._stroke(color, width, alpha, cap=skia.Paint.kButt_Cap)
        paint.setPathEffect(effect)
        self.c.drawPath(p, paint)
        if glow > 0:
            self.glow_used = True
            gp = self._stroke(color, max(4.0, width * 2.4), alpha * glow, cap=skia.Paint.kButt_Cap)
            gp.setPathEffect(effect)
            self.g.drawPath(p, gp)

    # -- premium finish -------------------------------------------------------
    @contextlib.contextmanager
    def blurred(self, sigma):
        """Depth of field: everything drawn inside is Gaussian-blurred by ``sigma`` design px."""
        if sigma <= 0.05:
            yield
            return
        # The layer filter is mapped through the canvas scale, so sigma stays in design px.
        self.c.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma)))
        try:
            yield
        finally:
            self.c.restore()

    def light_sweep(self, path, u, strength=0.55, width=0.16, angle=0.38, color="light"):
        """A bright diagonal band crossing ``path`` (clipped to it) as ``u`` goes 0 -> 1."""
        if not 0.0 < u < 1.0 or strength <= 0.003:
            return
        b = path.computeTightBounds()
        d = np.array([math.cos(angle), math.sin(angle)])  # sweep direction; the band is perpendicular to it
        corners = np.array([[b.left(), b.top()], [b.right(), b.top()], [b.right(), b.bottom()], [b.left(), b.bottom()]])
        along = corners @ d
        band = width * float(along.max() - along.min())
        pos = along.min() - band + (along.max() - along.min() + 2 * band) * u
        p0, p1 = d * (pos - band), d * (pos + band)
        shader = skia.GradientShader.MakeLinear(
            [skia.Point(*p0), skia.Point(*p1)], [col(color, 0.0), col(color, strength), col(color, 0.0)]
        )
        self.c.save()
        self.c.clipPath(path, doAntiAlias=True)
        self.c.drawRect(b, skia.Paint(AntiAlias=True, Shader=shader, BlendMode=skia.BlendMode.kPlus))
        self.c.restore()

    def light_cone(self, apex, left, right, color="light", alpha=0.25):
        """Volumetric light: an additive triangle fading from the apex to its base."""
        if alpha <= 0.003:
            return
        p = skia.Path()
        p.addPoly([skia.Point(*apex), skia.Point(*left), skia.Point(*right)], True)
        base = ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2)
        shader = skia.GradientShader.MakeLinear(
            [skia.Point(*apex), skia.Point(*base)], [col(color, alpha), col(color, alpha * 0.35), col(color, 0.0)],
            [0.0, 0.55, 1.0],
        )
        paint = skia.Paint(AntiAlias=True, Shader=shader, BlendMode=skia.BlendMode.kPlus,
                           MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14.0))
        self.c.drawPath(p, paint)

    def glint(self, x, y, size=60.0, alpha=1.0, color="light"):
        """Lens glint: hot core, soft halo, anamorphic horizontal streak and a faint four-point star."""
        if alpha <= 0.003:
            return
        add = skia.BlendMode.kPlus
        halo = skia.GradientShader.MakeRadial(skia.Point(x, y), size, [col(color, 0.55 * alpha), col(color, 0.0)])
        self.c.drawCircle(x, y, size, skia.Paint(AntiAlias=True, Shader=halo, BlendMode=add))
        streak = skia.GradientShader.MakeLinear(
            [skia.Point(x - size * 6, y), skia.Point(x + size * 6, y)],
            [col(color, 0.0), col(color, 0.55 * alpha), col(color, 0.0)],
        )
        self.c.drawRect(skia.Rect.MakeLTRB(x - size * 6, y - 1.2, x + size * 6, y + 1.2),
                        skia.Paint(AntiAlias=True, Shader=streak, BlendMode=add))
        for ang in (math.pi / 4, -math.pi / 4):
            dx, dy = math.cos(ang) * size * 1.2, math.sin(ang) * size * 1.2
            self.line(x - dx, y - dy, x + dx, y + dy, color, 1.0, 0.35 * alpha)
        self.glow_dot(x, y, size * 0.09, "#ffffff", alpha, strength=1.4)

    def chroma(self, amount):
        """Chromatic-aberration kick: split R and B by ``amount`` design px at finish."""
        self.chroma_px = max(getattr(self, "chroma_px", 0.0), amount)

    def dim(self, amount):
        """Darken everything drawn so far, glow included, by ``amount`` (0..1); later draws stay bright."""
        if amount <= 0.003:
            return
        self.c.save()
        self.c.resetMatrix()
        self.c.drawRect(skia.Rect.MakeWH(self.w, self.h), skia.Paint(Color4f=col("bg", amount)))
        self.c.restore()
        if self.glow_used:
            self.g.save()
            self.g.resetMatrix()
            self.g.drawRect(skia.Rect.MakeWH(self.gw, self.gh),
                            skia.Paint(Color4f=skia.Color4f(0, 0, 0, 1 - amount), BlendMode=skia.BlendMode.kDstIn))
            self.g.restore()

    def zoom_blur(self, amount, samples=7):
        """Radial zoom-blur push about the frame centre at finish (chapter exits); ``amount`` ~0.05-0.4."""
        self.zoom_amount = max(getattr(self, "zoom_amount", 0.0), amount)
        self.zoom_samples = samples

    # -- cinematic finish -------------------------------------------------------
    def letterbox(self, amount):
        """2.39:1 bars; ``amount`` 0..1 slides them in from the frame edges."""
        if amount <= 0.001:
            return
        bar = (H - W / 2.39) / 2 * amount
        paint = self._fill("bg", 1.0)
        self.c.drawRect(skia.Rect.MakeXYWH(0, 0, W, bar), paint)
        self.c.drawRect(skia.Rect.MakeXYWH(0, H - bar, W, bar), paint)

    def vignette(self, strength=0.55):
        shader = skia.GradientShader.MakeRadial(
            skia.Point(W / 2, H / 2), W * 0.72, [col("bg", 0.0), col("bg", 0.0), col("bg", strength)], [0.0, 0.55, 1.0]
        )
        self.c.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=shader))

    def grain(self, t, strength=0.05):
        """Film grain: one of a few pre-baked noise tiles per frame, overlaid."""
        tile = _grain_tile(int(t * 24) % 6)
        self.c.save()
        self.c.resetMatrix()
        paint = skia.Paint(
            Shader=tile.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, LINEAR),
            Alphaf=strength,
            BlendMode=skia.BlendMode.kOverlay,
        )
        self.c.drawRect(skia.Rect.MakeWH(self.w, self.h), paint)
        self.c.restore()

    # -- output -------------------------------------------------------------
    def finish(self) -> np.ndarray:
        if self.glow_used:
            snap = self.gsurf.makeImageSnapshot()
            blur = skia.Surface(self.gw, self.gh)
            bc = blur.getCanvas()
            bc.clear(skia.ColorTRANSPARENT)
            # Two tight scales (about 5 and 14 output px at 1080p): a crisp core bloom plus a short, faint halo.
            sigma = max(1.0, 2.4 * self.gw / 960)
            bc.drawImage(snap, 0, 0, LINEAR, skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma)))
            bc.drawImage(
                snap, 0, 0, LINEAR,
                skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma * 2.8, sigma * 2.8), Alphaf=0.55,
                           BlendMode=skia.BlendMode.kPlus),
            )
            img = blur.makeImageSnapshot()
            self.c.save()
            self.c.resetMatrix()
            self.c.drawImageRect(img, skia.Rect.MakeWH(self.w, self.h), LINEAR, skia.Paint(BlendMode=skia.BlendMode.kPlus))
            self.c.restore()
        zoom = getattr(self, "zoom_amount", 0.0)
        if zoom > 0.001:
            snap = self.surface.makeImageSnapshot()
            self.c.save()
            self.c.resetMatrix()
            self.c.clear(col("bg"))
            n = self.zoom_samples
            for k in range(n):
                s = 1.0 + zoom * k / (n - 1)
                rect = skia.Rect.MakeXYWH(self.w * (1 - s) / 2, self.h * (1 - s) / 2, self.w * s, self.h * s)
                self.c.drawImageRect(snap, rect, LINEAR, skia.Paint(Alphaf=1.0 / n, BlendMode=skia.BlendMode.kPlus))
            self.c.restore()
        shift = int(round(getattr(self, "chroma_px", 0.0) * self.k))
        if shift > 0:
            self.arr[..., 0] = np.roll(self.arr[..., 0], shift, axis=1)
            self.arr[..., 2] = np.roll(self.arr[..., 2], -shift, axis=1)
        self.arr[..., 3] = 255
        return self.arr


def chroma_kick(t, at, amount=6.0, width=0.18):
    """Chromatic split in design px for a kick landing at ``at`` (fast attack, short decay)."""
    if t < at - 0.03 or t > at + width:
        return 0.0
    return amount * math.exp(-max(0.0, t - at) / (width / 3))


def blur_samples() -> int:
    """Motion-blur subframes: FC_MOTION_BLUR=N (finals). 0/1 = off (previews, stills)."""
    return max(1, int(os.environ.get("FC_MOTION_BLUR", "1") or 1))


def motion_blur(draw, t, size, weight=1.0, shutter=0.5 / 30, samples=None):
    """Average ``samples`` subframes of ``draw(t, size)`` over a 180-degree shutter.

    ``weight`` (0..1) scales the shutter so only fast beats pay for it; with weight 0
    or one sample this is exactly ``draw(t, size)``.
    """
    n = blur_samples() if samples is None else samples
    if n <= 1 or weight <= 0.01:
        return draw(t, size)
    span = shutter * weight
    acc = None
    for k in range(n):
        frame = draw(t - span * (1 - k / (n - 1)), size).astype(np.uint16)
        acc = frame if acc is None else acc + frame
    return (acc // n).astype(np.uint8)


class _NullCanvas:
    """Swallows glow calls when drawing into an offscreen card."""

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class Pen(Frame):
    """Frame drawing helpers on an existing skia canvas (no glow layer)."""

    def __init__(self, canvas):
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


