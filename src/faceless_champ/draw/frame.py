"""Immediate-mode Skia frames for ``FunctionSource`` draw functions.

Author in design pixels (1920x1080 by default); the frame scales to the requested output size,
so 720p previews and 1080p/4K finals share one code path::

    def draw(t, size):
        fr = Frame(size)
        fr.circle(960, 540, 120, "primary", 3.0, glow=0.6)
        fr.text("Hello", 960, 400, "display", 72, 600)
        fr.vignette(0.5)
        fr.grain(t, 0.04)
        return fr.finish()

Glow goes to a reduced-resolution canvas ``g`` that is blurred once in ``finish()`` and added on
top, which is far cheaper than per-shape mask blurs. ``c`` is the crisp canvas; both are public
skia canvases for custom drawing.
"""

from __future__ import annotations

import contextlib
import math
import os
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import skia

from ..typography import font_path
from .palette import Palette, default_palette

DESIGN = (1920, 1080)
LINEAR = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone)
WGHT = 0x77676874
FAMILIES = {"italic": "serif-italic"}

# ---------------------------------------------------------------- color


def col(value: str, alpha: float = 1.0, palette: Palette | None = None) -> skia.Color4f:
    """skia color for a token or hex (default palette unless ``palette`` is given)."""
    r, g, b = (palette or default_palette()).rgb(value)
    return skia.Color4f(r, g, b, max(0.0, min(1.0, alpha)))


def mix(a: str, b: str, u: float, palette: Palette | None = None) -> str:
    return (palette or default_palette()).mix(a, b, u)


# ---------------------------------------------------------------- fonts


@lru_cache(maxsize=32)
def typeface(family: str, weight: int):
    """Variable-weight typeface: ``sans``, ``display``, ``serif``, ``italic``, ``mono`` or a font path."""
    tf = skia.Typeface.MakeFromFile(font_path(FAMILIES.get(family, family)))
    if tf is None:
        raise ValueError(f"skia could not load font {family!r}")
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


def text_path(
    s: str, x: float, y: float, family="display", size=64.0, weight=600, align="center", tracking=0.0
) -> skia.Path:
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


# ---------------------------------------------------------------- image helpers


def image_from_array(arr: np.ndarray) -> skia.Image:
    """uint8 RGBA (straight, opaque or not) -> skia.Image."""
    arr = np.ascontiguousarray(arr)
    return skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)


def quad_matrix(src_w, src_h, quad):
    """Matrix mapping a ``src_w x src_h`` rectangle onto four corners (perspective)."""
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


# ---------------------------------------------------------------- glow


@dataclass(frozen=True)
class GlowStyle:
    """How glow is drawn and bloomed.

    resolution: glow canvas size as a fraction of the output. stroke_scale/stroke_min: glow stroke
    width from the crisp width. dot_scale: glow_dot halo radius. sigma: core blur in glow-canvas px
    at design width. halo/halo_alpha: second, wider blur pass and its strength.
    """

    resolution: float = 0.5
    stroke_scale: float = 2.4
    stroke_min: float = 4.0
    dot_scale: float = 2.2
    sigma: float = 2.4
    halo: float = 2.8
    halo_alpha: float = 0.55

    @classmethod
    def named(cls, name: str) -> GlowStyle:
        try:
            return GLOW_STYLES[name]
        except KeyError:
            raise ValueError(f"unknown glow style {name!r}; use one of: {', '.join(GLOW_STYLES)}") from None


GLOW_STYLES = {
    "tight": GlowStyle(),  # half-res: crisp core bloom plus a short, faint halo
    "soft": GlowStyle(0.25, 3.5, 6.0, 3.2, 3.2, 3.0, 1.0),  # quarter-res: wide, dreamy halos
}

# ---------------------------------------------------------------- frame


class Frame:
    """One output frame: crisp canvas ``c`` plus reduced-resolution glow canvas ``g``.

    size: output pixels. design: authoring coordinate space. palette: color tokens (default:
    ``default_palette()``). glow: a GlowStyle or a preset name (``tight``, ``soft``).
    """

    def __init__(self, size, background="bg", *, palette: Palette | None = None, design=DESIGN, glow="tight"):
        self.palette = palette or default_palette()
        self.glow_style = GlowStyle.named(glow) if isinstance(glow, str) else glow
        self.dw, self.dh = float(design[0]), float(design[1])
        self.w, self.h = int(size[0]), int(size[1])
        self.k = self.w / self.dw
        self.arr = np.zeros((self.h, self.w, 4), np.uint8)
        self.surface = skia.Surface(self.arr, colorType=skia.kRGBA_8888_ColorType, alphaType=skia.kPremul_AlphaType)
        self.c = self.surface.getCanvas()
        self.c.clear(self.col(background))
        self.c.scale(self.k, self.k)
        res = self.glow_style.resolution
        self.gw, self.gh = max(2, int(self.w * res)), max(2, int(self.h * res))
        self.gsurf = skia.Surface(self.gw, self.gh)
        self.g = self.gsurf.getCanvas()
        self.g.clear(skia.ColorTRANSPARENT)
        self.g.scale(self.gw / self.dw, self.gh / self.dh)
        self.glow_used = False
        self.chroma_px = 0.0
        self.zoom_amount = 0.0
        self.zoom_samples = 7

    # -- paints -------------------------------------------------------------
    def col(self, value: str, alpha: float = 1.0) -> skia.Color4f:
        return col(value, alpha, self.palette)

    def mix(self, a: str, b: str, u: float) -> str:
        return self.palette.mix(a, b, u)

    def stroke_paint(self, color, width, alpha, cap=skia.Paint.kRound_Cap):
        return skia.Paint(
            AntiAlias=True,
            Style=skia.Paint.kStroke_Style,
            StrokeWidth=width,
            StrokeCap=cap,
            StrokeJoin=skia.Paint.kRound_Join,
            Color4f=self.col(color, alpha),
        )

    def fill_paint(self, color, alpha):
        return skia.Paint(AntiAlias=True, Style=skia.Paint.kFill_Style, Color4f=self.col(color, alpha))

    def glow_width(self, width):
        s = self.glow_style
        return max(s.stroke_min, width * s.stroke_scale)

    # -- primitives -------------------------------------------------------
    def path_stroke(self, path, color, width=2.0, alpha=1.0, glow=0.0, glow_width=None):
        if alpha <= 0.003:
            return
        self.c.drawPath(path, self.stroke_paint(color, width, alpha))
        if glow > 0:
            self.glow_used = True
            self.g.drawPath(path, self.stroke_paint(color, glow_width or self.glow_width(width), alpha * glow))

    def path_fill(self, path, color, alpha=1.0, glow=0.0):
        if alpha <= 0.003:
            return
        self.c.drawPath(path, self.fill_paint(color, alpha))
        if glow > 0:
            self.glow_used = True
            self.g.drawPath(path, self.fill_paint(color, alpha * glow))

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
        if fill:
            self.path_fill(p, color, alpha=alpha, glow=glow)
        else:
            self.path_stroke(p, color, width=width, alpha=alpha, glow=glow)

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
        self.g.drawCircle(
            float(x), float(y), float(r * self.glow_style.dot_scale), self.fill_paint(color, alpha * strength)
        )

    def text(
        self,
        s,
        x,
        y,
        family="sans",
        size=28,
        weight=500,
        color="ink",
        alpha=1.0,
        align="center",
        tracking=0.0,
        glow=0.0,
    ):
        """Draw text with its *baseline* at y."""
        if alpha <= 0.003 or not s:
            return
        f = font(family, size, weight)
        width = text_width(s, f, tracking)
        x0 = x - width / 2 if align == "center" else x - width if align == "right" else x
        paint = skia.Paint(AntiAlias=True, Color4f=self.col(color, alpha))
        gpaint = skia.Paint(AntiAlias=True, Color4f=self.col(color, alpha * glow)) if glow > 0 else None
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
        """Draw ``image`` onto four corners (see ``card_quad``); ``blend`` is a skia.BlendMode."""
        if alpha <= 0.003:
            return
        paint = skia.Paint(AntiAlias=True, Color4f=self.col("#ffffff", alpha))
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
        w, h = self.dw * scale, self.dh * scale
        rect = skia.Rect.MakeXYWH((self.dw - w) / 2, (self.dh - h) / 2, w, h)
        self.c.drawImageRect(image, rect, LINEAR, skia.Paint(AntiAlias=True, Color4f=self.col("#ffffff", alpha)))

    def dashed(self, xs, ys, color, width=2.0, alpha=1.0, glow=0.0, on=12.0, off=9.0, phase=0.0):
        """Dashed polyline (drop-lines, hypothetical arrows)."""
        if len(xs) < 2 or alpha <= 0.003:
            return
        p = skia.Path()
        p.moveTo(float(xs[0]), float(ys[0]))
        for x, y in zip(xs[1:], ys[1:]):
            p.lineTo(float(x), float(y))
        effect = skia.DashPathEffect.Make([on, off], phase)
        paint = self.stroke_paint(color, width, alpha, cap=skia.Paint.kButt_Cap)
        paint.setPathEffect(effect)
        self.c.drawPath(p, paint)
        if glow > 0:
            self.glow_used = True
            gp = self.stroke_paint(color, self.glow_width(width), alpha * glow, cap=skia.Paint.kButt_Cap)
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
            [skia.Point(*p0), skia.Point(*p1)], [self.col(color, 0.0), self.col(color, strength), self.col(color, 0.0)]
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
            [skia.Point(*apex), skia.Point(*base)],
            [self.col(color, alpha), self.col(color, alpha * 0.35), self.col(color, 0.0)],
            [0.0, 0.55, 1.0],
        )
        paint = skia.Paint(
            AntiAlias=True,
            Shader=shader,
            BlendMode=skia.BlendMode.kPlus,
            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14.0),
        )
        self.c.drawPath(p, paint)

    def glint(self, x, y, size=60.0, alpha=1.0, color="light"):
        """Lens glint: hot core, soft halo, anamorphic horizontal streak and a faint four-point star."""
        if alpha <= 0.003:
            return
        add = skia.BlendMode.kPlus
        halo = skia.GradientShader.MakeRadial(
            skia.Point(x, y), size, [self.col(color, 0.55 * alpha), self.col(color, 0.0)]
        )
        self.c.drawCircle(x, y, size, skia.Paint(AntiAlias=True, Shader=halo, BlendMode=add))
        streak = skia.GradientShader.MakeLinear(
            [skia.Point(x - size * 6, y), skia.Point(x + size * 6, y)],
            [self.col(color, 0.0), self.col(color, 0.55 * alpha), self.col(color, 0.0)],
        )
        self.c.drawRect(
            skia.Rect.MakeLTRB(x - size * 6, y - 1.2, x + size * 6, y + 1.2),
            skia.Paint(AntiAlias=True, Shader=streak, BlendMode=add),
        )
        for ang in (math.pi / 4, -math.pi / 4):
            dx, dy = math.cos(ang) * size * 1.2, math.sin(ang) * size * 1.2
            self.line(x - dx, y - dy, x + dx, y + dy, color, 1.0, 0.35 * alpha)
        self.glow_dot(x, y, size * 0.09, "#ffffff", alpha, strength=1.4)

    def chroma(self, amount):
        """Chromatic-aberration kick: split R and B by ``amount`` design px at finish (see ``chroma_kick``)."""
        self.chroma_px = max(self.chroma_px, amount)

    def dim(self, amount):
        """Darken everything drawn so far, glow included, by ``amount`` (0..1); later draws stay bright."""
        if amount <= 0.003:
            return
        self.c.save()
        self.c.resetMatrix()
        self.c.drawRect(skia.Rect.MakeWH(self.w, self.h), skia.Paint(Color4f=self.col("bg", amount)))
        self.c.restore()
        if self.glow_used:
            self.g.save()
            self.g.resetMatrix()
            self.g.drawRect(
                skia.Rect.MakeWH(self.gw, self.gh),
                skia.Paint(Color4f=skia.Color4f(0, 0, 0, 1 - amount), BlendMode=skia.BlendMode.kDstIn),
            )
            self.g.restore()

    def zoom_blur(self, amount, samples=7):
        """Radial zoom-blur push about the frame centre at finish (chapter exits); ``amount`` ~0.05-0.4."""
        self.zoom_amount = max(self.zoom_amount, amount)
        self.zoom_samples = samples

    # -- cinematic finish -------------------------------------------------------
    def letterbox(self, amount):
        """2.39:1 bars; ``amount`` 0..1 slides them in from the frame edges."""
        if amount <= 0.001:
            return
        bar = (self.dh - self.dw / 2.39) / 2 * amount
        paint = self.fill_paint("bg", 1.0)
        self.c.drawRect(skia.Rect.MakeXYWH(0, 0, self.dw, bar), paint)
        self.c.drawRect(skia.Rect.MakeXYWH(0, self.dh - bar, self.dw, bar), paint)

    def vignette(self, strength=0.55):
        shader = skia.GradientShader.MakeRadial(
            skia.Point(self.dw / 2, self.dh / 2),
            self.dw * 0.72,
            [self.col("bg", 0.0), self.col("bg", 0.0), self.col("bg", strength)],
            [0.0, 0.55, 1.0],
        )
        self.c.drawRect(skia.Rect.MakeWH(self.dw, self.dh), skia.Paint(Shader=shader))

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
        """Bloom the glow layer, apply zoom blur and chroma, and return opaque HxWx4 uint8 RGBA."""
        if self.glow_used:
            s = self.glow_style
            snap = self.gsurf.makeImageSnapshot()
            blur = skia.Surface(self.gw, self.gh)
            bc = blur.getCanvas()
            bc.clear(skia.ColorTRANSPARENT)
            sigma = max(1.0, s.sigma * self.gw / (self.dw * s.resolution))
            bc.drawImage(snap, 0, 0, LINEAR, skia.Paint(ImageFilter=skia.ImageFilters.Blur(sigma, sigma)))
            bc.drawImage(
                snap,
                0,
                0,
                LINEAR,
                skia.Paint(
                    ImageFilter=skia.ImageFilters.Blur(sigma * s.halo, sigma * s.halo),
                    Alphaf=s.halo_alpha,
                    BlendMode=skia.BlendMode.kPlus,
                ),
            )
            img = blur.makeImageSnapshot()
            self.c.save()
            self.c.resetMatrix()
            self.c.drawImageRect(
                img, skia.Rect.MakeWH(self.w, self.h), LINEAR, skia.Paint(BlendMode=skia.BlendMode.kPlus)
            )
            self.c.restore()
        if self.zoom_amount > 0.001:
            snap = self.surface.makeImageSnapshot()
            self.c.save()
            self.c.resetMatrix()
            self.c.clear(self.col("bg"))
            n = self.zoom_samples
            for k in range(n):
                s = 1.0 + self.zoom_amount * k / (n - 1)
                rect = skia.Rect.MakeXYWH(self.w * (1 - s) / 2, self.h * (1 - s) / 2, self.w * s, self.h * s)
                self.c.drawImageRect(snap, rect, LINEAR, skia.Paint(Alphaf=1.0 / n, BlendMode=skia.BlendMode.kPlus))
            self.c.restore()
        shift = round(self.chroma_px * self.k)
        if shift > 0:
            self.arr[..., 0] = np.roll(self.arr[..., 0], shift, axis=1)
            self.arr[..., 2] = np.roll(self.arr[..., 2], -shift, axis=1)
        self.arr[..., 3] = 255
        return self.arr


class _NullCanvas:
    """Swallows glow calls when drawing into an offscreen card."""

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


class Pen(Frame):
    """Frame drawing helpers on an existing skia canvas (no glow layer, no finish)."""

    def __init__(self, canvas, *, palette: Palette | None = None, k: float = 1.0, glow="tight"):
        self.palette = palette or default_palette()
        self.glow_style = GlowStyle.named(glow) if isinstance(glow, str) else glow
        self.c = canvas
        self.g = _NullCanvas()
        self.k = k
        self.glow_used = False


def offscreen(w: float, h: float, k: float, *, palette: Palette | None = None):
    """Transparent surface for a ``w x h`` design-pixel card at output scale ``k`` (use ``fr.k``)."""
    surf = skia.Surface(max(2, round(w * k)), max(2, round(h * k)))
    canvas = surf.getCanvas()
    canvas.clear(skia.ColorTRANSPARENT)
    canvas.scale(k, k)
    return surf, Pen(canvas, palette=palette, k=k)


# ---------------------------------------------------------------- motion blur


def blur_samples() -> int:
    """Motion-blur subframes: ``FC_MOTION_BLUR=N`` (finals). 0/1 = off (previews, stills)."""
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


# ---------------------------------------------------------------- scene wiring


def draw_scene(draw, duration, *, theme=None, key=None, audio=None, audio_trim_start=0.0, design=DESIGN):
    """A Scene that plays ``draw(t, size)`` full-frame for ``duration`` seconds.

    ``key`` should change whenever the drawing changes outside ``draw``'s own code (pass the
    module's mtime). ``audio`` adds a narration file at scene time 0, trimmed by ``audio_trim_start``
    seconds so a chapter can start mid-narration.
    """
    from ..sources import FunctionSource
    from ..theme import current_theme
    from ..timeline import Scene

    theme = theme or current_theme()
    w, h = int(design[0]), int(design[1])
    with theme.use():
        scene = Scene(theme.canvas(w, h))
        source = FunctionSource(draw, size=(w, h), duration=duration, key=key)
        scene.add(source.viewport(width=w, height=h, position=(w / 2, h / 2)))
        scene.wait_until(duration)
        if audio is not None:
            scene.add_audio(audio, start=0, trim_start=audio_trim_start)
    return scene
