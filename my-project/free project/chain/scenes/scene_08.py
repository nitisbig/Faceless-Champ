r"""Scene 08: Shrinking to Zero: From Discrete Fractions to Leibniz Derivatives.

Timecode: 00:03:46,560 --> 00:04:48,110 (Duration: 61.55s)
Engine: skia-python (Canvas, Scene, Viewport) + LaTeX MathTex Typography (Computer Modern)

Key Mechanics & Aesthetics:
- Pure pitch-black void canvas (#000000) with zero heading banner or subtitle boxes.
- Computer Modern MathTex typography matching euler_scene.py and scene_07.py.
- High-contrast saturated neon RGB palette:
  - Cyan #00F5FF (Input domain x / Machine g / dx / du/dx)
  - Gold #FFB800 (Intermediate u / Machine f / du / dy/du)
  - Coral #FF2A6D (Output domain y / dy / dy/dx / Total Rate)
  - Mint #05FFA1 (Limits / Infinitesimals / Energy / Bloom)
  - White #FFFFFF (Equalities / Math symbols / Brackets)
- Shot 08A (0.0s - 11.6s): Identifying Machine Rates:
  - Upper stage: Factored fractions (Δy/Δu) · (Δu/Δx).
  - Machine g rate gauge on right (Cyan) linked to Δu/Δx <-> g'(x).
  - Machine f rate gauge on left (Gold) linked to Δy/Δu <-> f'(u).
  - Conduit beams and flowing particles.
- Shot 08B (11.6s - 23.2s): Shrinking to Zero (Δx -> 0 ==> Δu -> 0):
  - Limit formula distributes: lim_{Δx->0} [...] = lim (Δy/Δu) · lim (Δu/Δx).
  - Lower stage: Dual contracting calipers on x and u axes.
  - Δx contracts smoothly towards 0, and Δu shrinks right along with it due to continuity of g.
  - Settles into true derivatives with quantum sparkle burst.
- Shot 08C (23.2s - 38.7s): The Grand Emergence of Leibniz Notation (Δ -> d):
  - Δy/Δu morphs into dy/du with radiant pulse.
  - Δu/Δx morphs into du/dx with cyan pulse.
  - Master equation dy/dx = (dy/du) · (du/dx) crystallizes at center stage with anamorphic laser streak and expanding shockwaves.
- Shot 08D (38.7s - 49.0s): Plain-Words Deconstruction:
  - Precision underbraces drop below each term:
    Total Rate = Outer Rate at u=g(x) × Inner Rate at x.
  - Golden evaluation arc highlighting u=g(x).
- Shot 08E (49.0s - 61.55s): The Honest Footnote & Final Product Law:
  - Technical cybernetic footnote card for Δu = 0 (Carathéodory formulation).
  - Climax resolution: footnote dissolves, master formula expands with full energy cascade:
    Total Rate = Product of Rates Along the Chain.
"""

from __future__ import annotations

from dataclasses import dataclass
import io
import math
import os
from pathlib import Path
from typing import Sequence

# Configure matplotlib cache safely for sandbox environment
os.environ["MPLCONFIGDIR"] = "/tmp/mpl_cache"

from matplotlib import figure
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import MathTextParser
import numpy as np
from PIL import Image
import skia

from faceless_champ import Canvas, Scene, Viewport

SCENE_08_DURATION: float = 61.55

# High-Contrast Sharp Neon RGB Color Palette
CYAN = "#00F5FF"   # Electric Laser Cyan (Variable x / Machine g / dx / du/dx)
GOLD = "#FFB800"   # Rich Radiant Gold (Variable u / Machine f / du / dy/du)
WHITE = "#FFFFFF"  # Pure Brilliant White (Operators / Grid / Ticks)
MINT = "#05FFA1"   # High-Voltage Neon Mint (Limits / Continuity / Bloom)
CORAL = "#FF2A6D"  # Laser Neon Coral (Variable y / dy / dy/dx / Total Rate)
CARD_BG = "#0b1220" # Dark Cybernetic Slate Card Background


def _render_mathtext_transparent(
    s: str,
    color: str = "white",
    prop: FontProperties | None = None,
    dpi: int = 200,
) -> tuple[Image.Image, float]:
    """Render a single LaTeX math token to a transparent RGBA image with TeX depth."""
    s_math = s.strip()
    if not (s_math.startswith("$") and s_math.endswith("$")):
        s_math = f"${s_math}$"

    parser = MathTextParser("path")
    width, height, depth, _, _ = parser.parse(s_math, dpi=72, prop=prop)
    fig = figure.Figure(figsize=(width / 72.0, height / 72.0))
    fig.patch.set_alpha(0.0)
    fig.text(0, depth / height, s_math, fontproperties=prop, color=color)
    buf = io.BytesIO()
    fig.savefig(buf, dpi=dpi, format="png", transparent=True)
    buf.seek(0)
    return Image.open(buf).convert("RGBA"), depth * (dpi / 72.0)


def _compose_two_tone_fraction(
    num_tex: str,
    num_color: str,
    den_tex: str,
    den_color: str,
    bar_color: str = WHITE,
    font_size: float = 30.0,
    dpi: int = 200,
) -> tuple[Image.Image, float]:
    """Compose a high-precision two-tone fraction with colored numerator, colored denominator, and horizontal bar."""
    prop = FontProperties(size=font_size)
    img_num, d_num = _render_mathtext_transparent(num_tex, color=num_color, prop=prop, dpi=dpi)
    img_den, d_den = _render_mathtext_transparent(den_tex, color=den_color, prop=prop, dpi=dpi)

    bar_pad = 8
    width = max(img_num.width, img_den.width) + bar_pad * 2
    bar_thickness = max(2, int(2.2 * (dpi / 72.0) * (font_size / 30.0)))
    spacing = 4

    height = img_num.height + spacing + bar_thickness + spacing + img_den.height
    comp = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Paste Numerator
    num_x = (width - img_num.width) // 2
    comp.alpha_composite(img_num, (num_x, 0))

    # Draw Bar
    bar_y = img_num.height + spacing
    draw = Image.new("RGBA", (width, bar_thickness), bar_color)
    comp.paste(draw, (0, bar_y))

    # Paste Denominator
    den_x = (width - img_den.width) // 2
    den_y = bar_y + bar_thickness + spacing
    comp.alpha_composite(img_den, (den_x, den_y))

    depth = height - (bar_y + bar_thickness // 2)
    return comp, depth


def _compose_latex_equation(
    terms: list[tuple[str, str]],
    font_size: float = 32.0,
    dpi: int = 200,
    spacing: int = 14,
) -> skia.Image:
    """Compose multi-term colored LaTeX equation with exact TeX mathematical baseline alignment."""
    prop = FontProperties(size=font_size)
    imgs_with_depth = [_render_mathtext_transparent(t, color=c, prop=prop, dpi=dpi) for t, c in terms]
    max_ascent = max(img.height - d for img, d in imgs_with_depth)
    max_descent = max(d for img, d in imgs_with_depth)
    total_height = int(max_ascent + max_descent + 8)
    total_width = sum(img.width for img, d in imgs_with_depth) + spacing * (len(imgs_with_depth) - 1) + 16

    comp = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
    cur_x = 8
    baseline_y = max_ascent + 4

    for img, d in imgs_with_depth:
        y = int(baseline_y - (img.height - d))
        comp.alpha_composite(img, (cur_x, y))
        cur_x += img.width + spacing

    return skia.Image.fromarray(np.array(comp), skia.ColorType.kRGBA_8888_ColorType)


def _compose_leibniz_master(
    font_size: float = 42.0,
    dpi: int = 200,
    spacing: int = 44,
) -> tuple[skia.Image, list[float]]:
    """Compose the master Leibniz Chain Rule formula with exact mathematical baseline alignment and relative centers."""
    prop = FontProperties(size=font_size)
    f1, d1 = _compose_two_tone_fraction(r"dy", CORAL, r"dx", CYAN, font_size=font_size, dpi=dpi)
    eq, de = _render_mathtext_transparent(r"=", WHITE, prop=prop, dpi=dpi)
    f2, d2 = _compose_two_tone_fraction(r"dy", CORAL, r"du", GOLD, font_size=font_size, dpi=dpi)
    dot, dd = _render_mathtext_transparent(r"\cdot", WHITE, prop=prop, dpi=dpi)
    f3, d3 = _compose_two_tone_fraction(r"du", GOLD, r"dx", CYAN, font_size=font_size, dpi=dpi)

    items = [(f1, d1), (eq, de), (f2, d2), (dot, dd), (f3, d3)]
    max_ascent = max(img.height - d for img, d in items)
    max_descent = max(d for img, d in items)
    total_h = int(max_ascent + max_descent + 8)
    total_w = sum(img.width for img, d in items) + spacing * (len(items) - 1) + 16

    comp = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    cur_x = 8
    baseline_y = max_ascent + 4
    centers: list[float] = []

    for idx, (img, d) in enumerate(items):
        y = int(baseline_y - (img.height - d))
        comp.alpha_composite(img, (cur_x, y))
        if idx in (0, 2, 4):
            centers.append(cur_x + img.width / 2.0)
        cur_x += img.width + spacing

    skia_img = skia.Image.fromarray(np.array(comp), skia.ColorType.kRGBA_8888_ColorType)
    return skia_img, centers


def _skia_color(hex_str: str, alpha: float = 1.0) -> skia.Color:
    hex_clean = hex_str.lstrip("#")
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    a = int(max(0.0, min(1.0, alpha)) * 255)
    return skia.ColorSetARGB(a, r, g, b)


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def _draw_math_centered(
    canvas: skia.Canvas,
    img: skia.Image,
    cx: float,
    cy: float,
    max_w: float | None = None,
    alpha: float = 1.0,
    base_scale: float = 0.5,
) -> None:
    """Draw a precompiled LaTeX formula centered at (cx, cy) with bilinear filtering."""
    if alpha <= 0.0 or img is None:
        return

    scale = base_scale
    if max_w is not None and img.width() * scale > max_w:
        scale = max_w / float(img.width())

    w = img.width() * scale
    h = img.height() * scale
    dst_rect = skia.Rect.MakeXYWH(cx - w / 2.0, cy - h / 2.0, w, h)

    paint = skia.Paint(Alphaf=max(0.0, min(1.0, alpha)), AntiAlias=True)
    canvas.drawImageRect(
        img,
        skia.Rect.MakeWH(img.width(), img.height()),
        dst_rect,
        skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear),
        paint,
    )


@dataclass(frozen=True)
class LimitToDerivativeSource:
    """Procedural vector graphics renderer for Scene 08: Discrete Fractions to Leibniz Chain Rule."""

    intrinsic_size: tuple[int, int] = (1920, 1080)
    duration: float = SCENE_08_DURATION
    fingerprint: str = "chain:scene-08:limit-to-derivative:v2-clean-math"
    requirements: tuple[str, ...] = ()

    def frame_key(self, source_time: float) -> int:
        return int(source_time * 60)

    def open(self, size: tuple[int, int]) -> object:
        w, h = size

        class Session:
            def __init__(self):
                self.w = w
                self.h = h
                self.sx = w / 1920.0
                self.sy = h / 1080.0
                info = skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
                self.surface = skia.Surface.MakeRaster(info)
                self.canvas = self.surface.getCanvas()

                # 1. Precompile MathTex Assets for High Performance & Exact Baseline Alignment
                prop_32 = FontProperties(size=32)
                prop_24 = FontProperties(size=24)
                prop_22 = FontProperties(size=22)
                prop_20 = FontProperties(size=20)
                prop_18 = FontProperties(size=18)

                # Fractions: Discrete (Δ)
                f_dy_du_delta, _ = _compose_two_tone_fraction(r"\Delta y", CORAL, r"\Delta u", GOLD, WHITE, font_size=32)
                self.img_dy_du_delta = skia.Image.fromarray(np.array(f_dy_du_delta), skia.ColorType.kRGBA_8888_ColorType)

                f_du_dx_delta, _ = _compose_two_tone_fraction(r"\Delta u", GOLD, r"\Delta x", CYAN, WHITE, font_size=32)
                self.img_du_dx_delta = skia.Image.fromarray(np.array(f_du_dx_delta), skia.ColorType.kRGBA_8888_ColorType)

                # Fractions: Differential Leibniz (d)
                f_dy_du_diff, _ = _compose_two_tone_fraction(r"dy", CORAL, r"du", GOLD, WHITE, font_size=32)
                self.img_dy_du_diff = skia.Image.fromarray(np.array(f_dy_du_diff), skia.ColorType.kRGBA_8888_ColorType)

                f_du_dx_diff, _ = _compose_two_tone_fraction(r"du", GOLD, r"dx", CYAN, WHITE, font_size=32)
                self.img_du_dx_diff = skia.Image.fromarray(np.array(f_du_dx_diff), skia.ColorType.kRGBA_8888_ColorType)

                # Multiplication Dots
                img_dot_pil, _ = _render_mathtext_transparent(r"\cdot", WHITE, prop_32)
                self.img_dot = skia.Image.fromarray(np.array(img_dot_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_dot_lg_pil, _ = _render_mathtext_transparent(r"\cdot", WHITE, FontProperties(size=42))
                self.img_dot_large = skia.Image.fromarray(np.array(img_dot_lg_pil), skia.ColorType.kRGBA_8888_ColorType)

                # Master Leibniz Equation Composite (dy/dx = (dy/du) · (du/dx))
                self.img_leibniz_master, self.master_centers = _compose_leibniz_master(font_size=42, spacing=44)

                # Full expanded limit distribution formula
                self.img_lim_expanded = _compose_latex_equation(
                    [
                        (r"\lim_{\Delta x \to 0}", MINT),
                        (r"[", WHITE),
                        (r"\frac{\Delta y}{\Delta u}", CORAL),
                        (r"\cdot", WHITE),
                        (r"\frac{\Delta u}{\Delta x}", CYAN),
                        (r"]", WHITE),
                        (r"=", WHITE),
                        (r"(", WHITE),
                        (r"\lim_{\Delta u \to 0}", MINT),
                        (r"\frac{\Delta y}{\Delta u}", CORAL),
                        (r")", WHITE),
                        (r"\cdot", WHITE),
                        (r"(", WHITE),
                        (r"\lim_{\Delta x \to 0}", MINT),
                        (r"\frac{\Delta u}{\Delta x}", CYAN),
                        (r")", WHITE),
                    ],
                    font_size=24,
                    spacing=8,
                )

                # Implication: Δx -> 0 ==> Δu -> 0
                self.img_implication = _compose_latex_equation(
                    [
                        (r"\Delta x \to 0", CYAN),
                        (r"\Longrightarrow", MINT),
                        (r"\Delta u \to 0", GOLD),
                    ],
                    font_size=28,
                    spacing=16,
                )

                # Caliper tags
                tag_dx_pil, _ = _render_mathtext_transparent(r"\Delta x", CYAN, prop_22)
                self.img_tag_dx = skia.Image.fromarray(np.array(tag_dx_pil), skia.ColorType.kRGBA_8888_ColorType)

                tag_du_pil, _ = _render_mathtext_transparent(r"\Delta u", GOLD, prop_22)
                self.img_tag_du = skia.Image.fromarray(np.array(tag_du_pil), skia.ColorType.kRGBA_8888_ColorType)

                # Machine Rate Gauge Badges
                img_g_prime_pil, _ = _render_mathtext_transparent(r"g^\prime(x)", CYAN, prop_24)
                self.img_g_prime = skia.Image.fromarray(np.array(img_g_prime_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_f_prime_pil, _ = _render_mathtext_transparent(r"f^\prime(u)", GOLD, prop_24)
                self.img_f_prime = skia.Image.fromarray(np.array(img_f_prime_pil), skia.ColorType.kRGBA_8888_ColorType)

                self.img_gauge_g_tag = _compose_latex_equation(
                    [
                        (r"\frac{\Delta u}{\Delta x}", CYAN),
                        (r"\longleftrightarrow", WHITE),
                        (r"g^\prime(x)", CYAN),
                    ],
                    font_size=22,
                    spacing=10,
                )

                self.img_gauge_f_tag = _compose_latex_equation(
                    [
                        (r"\frac{\Delta y}{\Delta u}", GOLD),
                        (r"\longleftrightarrow", WHITE),
                        (r"f^\prime(u)", GOLD),
                    ],
                    font_size=22,
                    spacing=10,
                )

                # Underbrace Labels for Shot 08D
                img_tot_rate_pil, _ = _render_mathtext_transparent(r"\mathrm{Total\ Rate}", CORAL, prop_20)
                self.img_total_rate = skia.Image.fromarray(np.array(img_tot_rate_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_out_rate_l1_pil, _ = _render_mathtext_transparent(r"\mathrm{Outer\ Rate}", GOLD, prop_20)
                self.img_outer_rate_l1 = skia.Image.fromarray(np.array(img_out_rate_l1_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_out_rate_l2_pil, _ = _render_mathtext_transparent(r"\mathrm{at\ } u=g(x)", GOLD, prop_18)
                self.img_outer_rate_l2 = skia.Image.fromarray(np.array(img_out_rate_l2_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_in_rate_l1_pil, _ = _render_mathtext_transparent(r"\mathrm{Inner\ Rate}", CYAN, prop_20)
                self.img_inner_rate_l1 = skia.Image.fromarray(np.array(img_in_rate_l1_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_in_rate_l2_pil, _ = _render_mathtext_transparent(r"\mathrm{at\ } x", CYAN, prop_18)
                self.img_inner_rate_l2 = skia.Image.fromarray(np.array(img_in_rate_l2_pil), skia.ColorType.kRGBA_8888_ColorType)

                # Footnote Card Items for Shot 08E
                img_fn_head_pil, _ = _render_mathtext_transparent(r"\ast\ \mathrm{Honest\ Footnote:\ Rigorous\ Limit\ Case}", GOLD, prop_20)
                self.img_fn_head = skia.Image.fromarray(np.array(img_fn_head_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_fn_l1_pil, _ = _render_mathtext_transparent(r"\Delta u = 0 \Longrightarrow \mathrm{Division\ by\ zero\ in\ discrete\ step}", CORAL, prop_18)
                self.img_fn_l1 = skia.Image.fromarray(np.array(img_fn_l1_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_fn_l2_pil, _ = _render_mathtext_transparent(r"\mathrm{Carath\acute{e}odory\ formulation\ handles\ constant\ intervals\ formally}", MINT, prop_18)
                self.img_fn_l2 = skia.Image.fromarray(np.array(img_fn_l2_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_fn_l3_pil, _ = _render_mathtext_transparent(r"\mathbf{\mathrm{The\ chain\ rule\ product\ law\ remains\ 100\%\ exact}}", WHITE, prop_18)
                self.img_fn_l3 = skia.Image.fromarray(np.array(img_fn_l3_pil), skia.ColorType.kRGBA_8888_ColorType)

                # Final Climax Banner
                self.img_climax_summary = _compose_latex_equation(
                    [
                        (r"\mathbf{\mathrm{Total\ Rate}}", CORAL),
                        (r"=", WHITE),
                        (r"\mathbf{\mathrm{Product\ of\ Rates\ Along\ the\ Chain}}", GOLD),
                    ],
                    font_size=26,
                    spacing=14,
                )

            def frame(self, t: float) -> Image.Image:
                w, h = self.w, self.h
                sx, sy = self.sx, self.sy
                surface = self.surface
                canvas = self.canvas

                # 1. Pure Pitch-Black Void Canvas (#000000)
                canvas.clear(skia.ColorSetRGB(0, 0, 0))

                # Subtle Cybernetic Void Grid (very faint, non-distracting)
                grid_paint = skia.Paint(
                    Color=_skia_color(WHITE, 0.025),
                    StrokeWidth=1.0 * sx,
                    Style=skia.Paint.kStroke_Style,
                    AntiAlias=False,
                )
                grid_step = int(120 * sx)
                for gx in range(0, w, grid_step):
                    canvas.drawLine(gx, 0, gx, h, grid_paint)
                for gy in range(0, h, grid_step):
                    canvas.drawLine(0, gy, w, gy, grid_paint)

                # =========================================================================
                # TIMELINE & SHOT LOGIC
                # -------------------------------------------------------------------------
                # Shot 08A: 0.0s - 11.6s  (Identifying Machine Rates: g and f)
                # Shot 08B: 11.6s - 23.2s (Shrinking to Zero: Calipers Δx -> 0 ==> Δu -> 0)
                # Shot 08C: 23.2s - 38.7s (Grand Emergence of Leibniz: Δ -> d & dy/dx)
                # Shot 08D: 38.7s - 49.0s (Plain-Words Deconstruction: Underbraces)
                # Shot 08E: 49.0s - 61.55s (Honest Footnote & Final Product Law Climax)
                # =========================================================================

                # -------------------------------------------------------------------------
                # SHOT 08A: Identifying Machine Rates (0.0s - 11.6s)
                # -------------------------------------------------------------------------
                shot_a_alpha = _smoothstep(0.0, 1.2, t) * (1.0 - _smoothstep(11.0, 12.0, t))

                if shot_a_alpha > 0.0:
                    eq_y = 260.0 * sy

                    # Left fraction: Δy/Δu (cx = 830)
                    # Dot: · (cx = 960)
                    # Right fraction: Δu/Δx (cx = 1090)
                    left_frac_x = 830.0 * sx
                    dot_x = 960.0 * sx
                    right_frac_x = 1090.0 * sx

                    # Fraction highlights based on voiceover cues:
                    # t in [1.5, 6.5]: Right fraction (Δu/Δx) highlighted in Cyan
                    # t in [6.5, 11.6]: Left fraction (Δy/Δu) highlighted in Gold
                    right_active = _smoothstep(1.5, 2.5, t) * (1.0 - _smoothstep(6.2, 6.8, t))
                    left_active = _smoothstep(6.5, 7.5, t)

                    # Draw Glow Box for active fractions
                    if right_active > 0.0:
                        rb_w, rb_h = 160.0 * sx, 150.0 * sy
                        rb_rect = skia.Rect.MakeXYWH(right_frac_x - rb_w / 2.0, eq_y - rb_h / 2.0, rb_w, rb_h)
                        canvas.drawRoundRect(rb_rect, 14.0 * sx, 14.0 * sy, skia.Paint(
                            Color=_skia_color(CYAN, 0.15 * right_active * shot_a_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(rb_rect, 14.0 * sx, 14.0 * sy, skia.Paint(
                            Color=_skia_color(CYAN, 0.85 * right_active * shot_a_alpha),
                            StrokeWidth=2.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                    if left_active > 0.0:
                        lb_w, lb_h = 160.0 * sx, 150.0 * sy
                        lb_rect = skia.Rect.MakeXYWH(left_frac_x - lb_w / 2.0, eq_y - lb_h / 2.0, lb_w, lb_h)
                        canvas.drawRoundRect(lb_rect, 14.0 * sx, 14.0 * sy, skia.Paint(
                            Color=_skia_color(GOLD, 0.15 * left_active * shot_a_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(lb_rect, 14.0 * sx, 14.0 * sy, skia.Paint(
                            Color=_skia_color(GOLD, 0.85 * left_active * shot_a_alpha),
                            StrokeWidth=2.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                    # Render Fractions
                    _draw_math_centered(canvas, self.img_dy_du_delta, left_frac_x, eq_y, alpha=shot_a_alpha, base_scale=0.55 * sx)
                    _draw_math_centered(canvas, self.img_dot, dot_x, eq_y, alpha=shot_a_alpha, base_scale=0.55 * sx)
                    _draw_math_centered(canvas, self.img_du_dx_delta, right_frac_x, eq_y, alpha=shot_a_alpha, base_scale=0.55 * sx)

                    # Lower Stage: Dual Machine Rate Gauges
                    # Right Gauge: Machine g (linked to Δu/Δx)
                    gauge_g_alpha = _smoothstep(1.8, 3.0, t) * shot_a_alpha
                    if gauge_g_alpha > 0.0:
                        gx_c, gy_c = 1260.0 * sx, 640.0 * sy
                        card_w, card_h = 360.0 * sx, 320.0 * sy
                        card_rect = skia.Rect.MakeXYWH(gx_c - card_w / 2.0, gy_c - card_h / 2.0, card_w, card_h)

                        canvas.drawRoundRect(card_rect, 16.0 * sx, 16.0 * sy, skia.Paint(
                            Color=_skia_color(CARD_BG, 0.88 * gauge_g_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(card_rect, 16.0 * sx, 16.0 * sy, skia.Paint(
                            Color=_skia_color(CYAN, 0.70 * gauge_g_alpha),
                            StrokeWidth=1.8 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                        arc_r = 75.0 * sx
                        arc_rect = skia.Rect.MakeXYWH(gx_c - arc_r, gy_c - 30.0 * sy - arc_r, arc_r * 2.0, arc_r * 2.0)
                        canvas.drawArc(arc_rect, 140.0, 260.0, False, skia.Paint(
                            Color=_skia_color(WHITE, 0.15 * gauge_g_alpha),
                            StrokeWidth=6.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))
                        sweep_g = 160.0 + 20.0 * math.sin(t * 3.5)
                        canvas.drawArc(arc_rect, 140.0, sweep_g, False, skia.Paint(
                            Color=_skia_color(CYAN, 0.90 * gauge_g_alpha),
                            StrokeWidth=6.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))
                        needle_ang = math.radians(140.0 + sweep_g)
                        nx = gx_c + (arc_r - 10.0 * sx) * math.cos(needle_ang)
                        ny = (gy_c - 30.0 * sy) + (arc_r - 10.0 * sx) * math.sin(needle_ang)
                        canvas.drawLine(gx_c, gy_c - 30.0 * sy, nx, ny, skia.Paint(
                            Color=_skia_color(WHITE, 0.95 * gauge_g_alpha),
                            StrokeWidth=2.5 * sx,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(gx_c, gy_c - 30.0 * sy, 6.0 * sx, skia.Paint(
                            Color=_skia_color(CYAN, 0.95 * gauge_g_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                        _draw_math_centered(canvas, self.img_g_prime, gx_c, gy_c + 60.0 * sy, alpha=gauge_g_alpha, base_scale=0.60 * sx)
                        _draw_math_centered(canvas, self.img_gauge_g_tag, gx_c, gy_c + 115.0 * sy, alpha=gauge_g_alpha, base_scale=0.50 * sx)

                        cond_p = skia.Paint(
                            Color=_skia_color(CYAN, 0.55 * gauge_g_alpha),
                            StrokeWidth=2.0 * sx,
                            PathEffect=skia.DashPathEffect.Make([6.0 * sx, 6.0 * sy], (t * 40.0) % 24.0),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        path_g = skia.Path()
                        path_g.moveTo(right_frac_x, eq_y + 70.0 * sy)
                        path_g.cubicTo(right_frac_x + 40.0 * sx, eq_y + 180.0 * sy, gx_c - 40.0 * sx, gy_c - 200.0 * sy, gx_c, gy_c - card_h / 2.0)
                        canvas.drawPath(path_g, cond_p)

                    # Left Gauge: Machine f (linked to Δy/Δu)
                    gauge_f_alpha = _smoothstep(6.5, 7.8, t) * shot_a_alpha
                    if gauge_f_alpha > 0.0:
                        fx_c, fy_c = 660.0 * sx, 640.0 * sy
                        card_w, card_h = 360.0 * sx, 320.0 * sy
                        card_rect = skia.Rect.MakeXYWH(fx_c - card_w / 2.0, fy_c - card_h / 2.0, card_w, card_h)

                        canvas.drawRoundRect(card_rect, 16.0 * sx, 16.0 * sy, skia.Paint(
                            Color=_skia_color(CARD_BG, 0.88 * gauge_f_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(card_rect, 16.0 * sx, 16.0 * sy, skia.Paint(
                            Color=_skia_color(GOLD, 0.70 * gauge_f_alpha),
                            StrokeWidth=1.8 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                        arc_r = 75.0 * sx
                        arc_rect = skia.Rect.MakeXYWH(fx_c - arc_r, fy_c - 30.0 * sy - arc_r, arc_r * 2.0, arc_r * 2.0)
                        canvas.drawArc(arc_rect, 140.0, 260.0, False, skia.Paint(
                            Color=_skia_color(WHITE, 0.15 * gauge_f_alpha),
                            StrokeWidth=6.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))
                        sweep_f = 140.0 + 25.0 * math.cos(t * 3.0)
                        canvas.drawArc(arc_rect, 140.0, sweep_f, False, skia.Paint(
                            Color=_skia_color(GOLD, 0.90 * gauge_f_alpha),
                            StrokeWidth=6.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))
                        needle_ang = math.radians(140.0 + sweep_f)
                        nx = fx_c + (arc_r - 10.0 * sx) * math.cos(needle_ang)
                        ny = (fy_c - 30.0 * sy) + (arc_r - 10.0 * sx) * math.sin(needle_ang)
                        canvas.drawLine(fx_c, fy_c - 30.0 * sy, nx, ny, skia.Paint(
                            Color=_skia_color(WHITE, 0.95 * gauge_f_alpha),
                            StrokeWidth=2.5 * sx,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(fx_c, fy_c - 30.0 * sy, 6.0 * sx, skia.Paint(
                            Color=_skia_color(GOLD, 0.95 * gauge_f_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                        _draw_math_centered(canvas, self.img_f_prime, fx_c, fy_c + 60.0 * sy, alpha=gauge_f_alpha, base_scale=0.60 * sx)
                        _draw_math_centered(canvas, self.img_gauge_f_tag, fx_c, fy_c + 115.0 * sy, alpha=gauge_f_alpha, base_scale=0.50 * sx)

                        cond_p = skia.Paint(
                            Color=_skia_color(GOLD, 0.55 * gauge_f_alpha),
                            StrokeWidth=2.0 * sx,
                            PathEffect=skia.DashPathEffect.Make([6.0 * sx, 6.0 * sy], (t * 40.0) % 24.0),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        path_f = skia.Path()
                        path_f.moveTo(left_frac_x, eq_y + 70.0 * sy)
                        path_f.cubicTo(left_frac_x - 40.0 * sx, eq_y + 180.0 * sy, fx_c + 40.0 * sx, fy_c - 200.0 * sy, fx_c, fy_c - card_h / 2.0)
                        canvas.drawPath(path_f, cond_p)

                    # Dynamic photon energy transfer between Machine g and Machine f
                    if gauge_g_alpha > 0.5 and gauge_f_alpha > 0.5:
                        pulse_prog = (t * 0.8) % 1.0
                        px = (1260.0 * (1.0 - pulse_prog) + 660.0 * pulse_prog) * sx
                        py = (640.0 - math.sin(pulse_prog * math.pi) * 60.0) * sy
                        canvas.drawCircle(px, py, 6.0 * sx, skia.Paint(
                            Color=_skia_color(WHITE, 0.95 * shot_a_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(px, py, 14.0 * sx, skia.Paint(
                            Color=_skia_color(MINT, 0.40 * shot_a_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                # -------------------------------------------------------------------------
                # SHOT 08B: Shrinking to Zero (11.6s - 23.2s)
                # -------------------------------------------------------------------------
                shot_b_alpha = _smoothstep(11.5, 12.8, t) * (1.0 - _smoothstep(22.6, 23.6, t))

                if shot_b_alpha > 0.0:
                    # Upper Stage: Distributed Limit Expression
                    lim_y = 220.0 * sy
                    _draw_math_centered(canvas, self.img_lim_expanded, 960.0 * sx, lim_y, alpha=shot_b_alpha, base_scale=0.55 * sx)

                    # Center Implication Banner: Δx -> 0 ==> Δu -> 0
                    imp_alpha = _smoothstep(14.0, 15.2, t) * shot_b_alpha
                    _draw_math_centered(canvas, self.img_implication, 960.0 * sx, 370.0 * sy, alpha=imp_alpha, base_scale=0.58 * sx)

                    # Lower Stage: Dual Contracting Calipers on Tracks
                    shrink_p = _smoothstep(14.5, 21.2, t)

                    cal_cx = 960.0 * sx
                    track_w = 640.0 * sx

                    # 1. Caliper for Δx on Input Axis (y = 740)
                    x_track_y = 740.0 * sy
                    canvas.drawLine(cal_cx - track_w / 2.0, x_track_y, cal_cx + track_w / 2.0, x_track_y, skia.Paint(
                        Color=_skia_color(WHITE, 0.20 * shot_b_alpha),
                        StrokeWidth=1.5 * sx,
                        AntiAlias=True,
                    ))

                    dx_width = (300.0 * (1.0 - shrink_p) + 16.0) * sx
                    dx_left = cal_cx - dx_width / 2.0
                    dx_right = cal_cx + dx_width / 2.0

                    cal_p = skia.Paint(
                        Color=_skia_color(CYAN, 0.90 * shot_b_alpha),
                        StrokeWidth=2.5 * sx,
                        AntiAlias=True,
                    )
                    canvas.drawLine(dx_left, x_track_y - 20.0 * sy, dx_left, x_track_y + 20.0 * sy, cal_p)
                    canvas.drawLine(dx_right, x_track_y - 20.0 * sy, dx_right, x_track_y + 20.0 * sy, cal_p)
                    canvas.drawLine(dx_left, x_track_y, dx_right, x_track_y, cal_p)

                    canvas.drawRect(skia.Rect.MakeLTRB(dx_left, x_track_y - 12.0 * sy, dx_right, x_track_y + 12.0 * sy), skia.Paint(
                        Color=_skia_color(CYAN, 0.22 * shot_b_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))

                    _draw_math_centered(canvas, self.img_tag_dx, cal_cx, x_track_y + 35.0 * sy, alpha=shot_b_alpha, base_scale=0.50 * sx)

                    # 2. Caliper for Δu on Intermediate Axis (y = 560)
                    u_track_y = 560.0 * sy
                    canvas.drawLine(cal_cx - track_w / 2.0, u_track_y, cal_cx + track_w / 2.0, u_track_y, skia.Paint(
                        Color=_skia_color(WHITE, 0.20 * shot_b_alpha),
                        StrokeWidth=1.5 * sx,
                        AntiAlias=True,
                    ))

                    du_width = (360.0 * (1.0 - shrink_p) + 20.0) * sx
                    du_left = cal_cx - du_width / 2.0
                    du_right = cal_cx + du_width / 2.0

                    cal_u_p = skia.Paint(
                        Color=_skia_color(GOLD, 0.90 * shot_b_alpha),
                        StrokeWidth=2.5 * sx,
                        AntiAlias=True,
                    )
                    canvas.drawLine(du_left, u_track_y - 20.0 * sy, du_left, u_track_y + 20.0 * sy, cal_u_p)
                    canvas.drawLine(du_right, u_track_y - 20.0 * sy, du_right, u_track_y + 20.0 * sy, cal_u_p)
                    canvas.drawLine(du_left, u_track_y, du_right, u_track_y, cal_u_p)

                    canvas.drawRect(skia.Rect.MakeLTRB(du_left, u_track_y - 12.0 * sy, du_right, u_track_y + 12.0 * sy), skia.Paint(
                        Color=_skia_color(GOLD, 0.22 * shot_b_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))

                    _draw_math_centered(canvas, self.img_tag_du, cal_cx, u_track_y - 35.0 * sy, alpha=shot_b_alpha, base_scale=0.50 * sx)

                    # Smoothness Transmission Conduit
                    flow_p = skia.Paint(
                        Color=_skia_color(MINT, 0.45 * shot_b_alpha),
                        StrokeWidth=1.8 * sx,
                        PathEffect=skia.DashPathEffect.Make([5.0 * sx, 5.0 * sy], (-t * 30.0) % 20.0),
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    path_flow = skia.Path()
                    path_flow.moveTo(dx_left, x_track_y - 20.0 * sy)
                    path_flow.cubicTo(dx_left - 40.0 * sx, (x_track_y + u_track_y) / 2.0, du_left - 40.0 * sx, (x_track_y + u_track_y) / 2.0, du_left, u_track_y + 20.0 * sy)
                    canvas.drawPath(path_flow, flow_p)

                    path_flow_r = skia.Path()
                    path_flow_r.moveTo(dx_right, x_track_y - 20.0 * sy)
                    path_flow_r.cubicTo(dx_right + 40.0 * sx, (x_track_y + u_track_y) / 2.0, du_right + 40.0 * sx, (x_track_y + u_track_y) / 2.0, du_right, u_track_y + 20.0 * sy)
                    canvas.drawPath(path_flow_r, flow_p)

                    # Quantum Sparkle Flashes
                    settle_flash = _smoothstep(20.5, 21.8, t) * (1.0 - _smoothstep(22.8, 23.4, t))
                    if settle_flash > 0.0:
                        sparkle_r = (24.0 + 12.0 * math.sin(t * 15.0)) * sx
                        canvas.drawCircle(cal_cx, x_track_y, sparkle_r, skia.Paint(
                            Color=_skia_color(CYAN, 0.45 * settle_flash),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(cal_cx, u_track_y, sparkle_r, skia.Paint(
                            Color=_skia_color(GOLD, 0.45 * settle_flash),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                # -------------------------------------------------------------------------
                # SHOT 08C: The Grand Emergence of Leibniz Notation (23.2s - 38.7s)
                # -------------------------------------------------------------------------
                shot_c_active = _smoothstep(23.0, 24.2, t) * (1.0 - _smoothstep(38.0, 39.0, t))

                if shot_c_active > 0.0:
                    if t < 29.0:
                        morph_y = 500.0 * sy
                        left_cx = 830.0 * sx
                        right_cx = 1090.0 * sx

                        # Left fraction morph: Δ -> d (23.2s - 26.0s)
                        left_morph_p = _smoothstep(23.2, 25.5, t)
                        _draw_math_centered(canvas, self.img_dy_du_delta, left_cx, morph_y, alpha=(1.0 - left_morph_p) * shot_c_active, base_scale=0.60 * sx)
                        _draw_math_centered(canvas, self.img_dy_du_diff, left_cx, morph_y, alpha=left_morph_p * shot_c_active, base_scale=0.60 * sx)

                        if 0.1 < left_morph_p < 0.9:
                            aura_r = (80.0 + 20.0 * math.sin(left_morph_p * math.pi)) * sx
                            canvas.drawCircle(left_cx, morph_y, aura_r, skia.Paint(
                                Color=_skia_color(GOLD, 0.25 * math.sin(left_morph_p * math.pi)),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))

                        # Right fraction morph: Δ -> d (26.0s - 28.8s)
                        right_morph_p = _smoothstep(26.0, 28.5, t)
                        _draw_math_centered(canvas, self.img_du_dx_delta, right_cx, morph_y, alpha=(1.0 - right_morph_p) * shot_c_active, base_scale=0.60 * sx)
                        _draw_math_centered(canvas, self.img_du_dx_diff, right_cx, morph_y, alpha=right_morph_p * shot_c_active, base_scale=0.60 * sx)

                        if 0.1 < right_morph_p < 0.9:
                            aura_r = (80.0 + 20.0 * math.sin(right_morph_p * math.pi)) * sx
                            canvas.drawCircle(right_cx, morph_y, aura_r, skia.Paint(
                                Color=_skia_color(CYAN, 0.25 * math.sin(right_morph_p * math.pi)),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))

                        # Multiplication dot between them
                        _draw_math_centered(canvas, self.img_dot_large, 960.0 * sx, morph_y, alpha=shot_c_active, base_scale=0.60 * sx)

                    else:
                        climax_p = _smoothstep(29.0, 31.0, t)
                        eq_cy = 480.0 * sy

                        # Anamorphic Laser Streak behind the formula
                        streak_p = _smoothstep(29.5, 33.0, t)
                        if streak_p > 0.0:
                            streak_len = 1100.0 * sx * streak_p
                            streak_paint = skia.Paint(
                                Color=_skia_color(MINT, 0.25 * streak_p * (0.8 + 0.2 * math.sin(t * 4.0))),
                                StrokeWidth=3.0 * sy,
                                AntiAlias=True,
                            )
                            canvas.drawLine(960.0 * sx - streak_len / 2.0, eq_cy, 960.0 * sx + streak_len / 2.0, eq_cy, streak_paint)

                        # Expanding shockwave rings from multiplication dot
                        shock_t = (t - 31.0)
                        if shock_t > 0.0:
                            for ring_idx in range(3):
                                r_age = (shock_t * 0.8 + ring_idx * 0.33) % 1.0
                                r_rad = r_age * 180.0 * sx
                                r_alpha = (1.0 - r_age) * 0.40 * climax_p
                                canvas.drawCircle(960.0 * sx, eq_cy, r_rad, skia.Paint(
                                    Color=_skia_color(MINT, r_alpha),
                                    StrokeWidth=2.0 * sx,
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                ))

                        # Draw Master Leibniz Equation Composite
                        _draw_math_centered(canvas, self.img_leibniz_master, 960.0 * sx, eq_cy, alpha=climax_p, base_scale=0.60 * sx)

                # -------------------------------------------------------------------------
                # SHOT 08D: Plain-Words Deconstruction (38.7s - 49.0s)
                # -------------------------------------------------------------------------
                shot_d_active = _smoothstep(38.5, 39.8, t) * (1.0 - _smoothstep(48.5, 49.5, t))

                if shot_d_active > 0.0:
                    eq_cy = 350.0 * sy
                    eq_scale = 0.58 * sx

                    # Draw Equation at Upper Anchor
                    _draw_math_centered(canvas, self.img_leibniz_master, 960.0 * sx, eq_cy, alpha=shot_d_active, base_scale=eq_scale)

                    # Compute exact X coordinates of the three fractions from composite centers
                    eq_left = 960.0 * sx - (self.img_leibniz_master.width() * eq_scale) / 2.0
                    x_dydx = eq_left + self.master_centers[0] * eq_scale
                    x_dydu = eq_left + self.master_centers[1] * eq_scale
                    x_dudx = eq_left + self.master_centers[2] * eq_scale

                    # Underbrace Architecture
                    ub_prog = _smoothstep(39.5, 41.2, t) * shot_d_active
                    ub_top_y = eq_cy + 75.0 * sy
                    ub_bot_y = ub_top_y + 35.0 * sy
                    label_y = ub_bot_y + 40.0 * sy

                    def _draw_bracket_brace(cx: float, bw: float, color_hex: str):
                        bp = skia.Paint(
                            Color=_skia_color(color_hex, 0.85 * ub_prog),
                            StrokeWidth=2.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        b_path = skia.Path()
                        b_path.moveTo(cx - bw / 2.0, ub_top_y)
                        b_path.quadTo(cx - bw / 2.0, ub_bot_y - 10.0 * sy, cx - bw / 4.0, ub_bot_y - 5.0 * sy)
                        b_path.quadTo(cx - 15.0 * sx, ub_bot_y - 2.0 * sy, cx, ub_bot_y + 8.0 * sy)
                        b_path.quadTo(cx + 15.0 * sx, ub_bot_y - 2.0 * sy, cx + bw / 4.0, ub_bot_y - 5.0 * sy)
                        b_path.quadTo(cx + bw / 2.0, ub_bot_y - 10.0 * sy, cx + bw / 2.0, ub_top_y)
                        canvas.drawPath(b_path, bp)

                    # Draw precision underbraces matching fraction widths
                    bw = 120.0 * sx
                    _draw_bracket_brace(x_dydx, bw, CORAL)
                    _draw_bracket_brace(x_dydu, bw, GOLD)
                    _draw_bracket_brace(x_dudx, bw, CYAN)

                    l1_y = label_y - 2.0 * sy
                    l2_y = label_y + 26.0 * sy

                    # 1. Total Rate Underbrace (under dy/dx)
                    _draw_math_centered(canvas, self.img_total_rate, x_dydx, label_y + 8.0 * sy, alpha=ub_prog, base_scale=0.52 * sx)

                    # 2. Outer Rate Underbrace (under dy/du: two-line stacked)
                    _draw_math_centered(canvas, self.img_outer_rate_l1, x_dydu, l1_y, alpha=ub_prog, base_scale=0.52 * sx)
                    _draw_math_centered(canvas, self.img_outer_rate_l2, x_dydu, l2_y, alpha=ub_prog, base_scale=0.48 * sx)

                    # 3. Inner Rate Underbrace (under du/dx: two-line stacked)
                    _draw_math_centered(canvas, self.img_inner_rate_l1, x_dudx, l1_y, alpha=ub_prog, base_scale=0.52 * sx)
                    _draw_math_centered(canvas, self.img_inner_rate_l2, x_dudx, l2_y, alpha=ub_prog, base_scale=0.48 * sx)

                    # Highlighting callout: "measured at the inner machine's output"
                    eval_highlight = _smoothstep(42.0, 43.5, t) * (1.0 - _smoothstep(48.0, 49.0, t))
                    if eval_highlight > 0.0:
                        eval_box_rect = skia.Rect.MakeXYWH(x_dydu - 85.0 * sx, l2_y - 16.0 * sy, 170.0 * sx, 32.0 * sy)
                        canvas.drawRoundRect(eval_box_rect, 8.0 * sx, 8.0 * sy, skia.Paint(
                            Color=_skia_color(GOLD, 0.20 * eval_highlight),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(eval_box_rect, 8.0 * sx, 8.0 * sy, skia.Paint(
                            Color=_skia_color(GOLD, 0.75 * eval_highlight),
                            StrokeWidth=1.5 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                        arc_p = skia.Paint(
                            Color=_skia_color(GOLD, 0.60 * eval_highlight),
                            StrokeWidth=2.0 * sx,
                            PathEffect=skia.DashPathEffect.Make([6.0 * sx, 6.0 * sy], (t * 25.0) % 24.0),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        path_eval = skia.Path()
                        path_eval.moveTo(x_dudx, l2_y)
                        path_eval.quadTo((x_dudx + x_dydu) / 2.0, l2_y + 55.0 * sy, x_dydu + 75.0 * sx, l2_y + 4.0 * sy)
                        canvas.drawPath(path_eval, arc_p)

                # -------------------------------------------------------------------------
                # SHOT 08E: The Honest Footnote & Final Product Law (49.0s - 61.55s)
                # -------------------------------------------------------------------------
                shot_e_active = _smoothstep(49.0, 50.2, t)

                if shot_e_active > 0.0:
                    # Phase 1: Technical Footnote Card (49.0s - 55.0s)
                    fn_alpha = _smoothstep(49.2, 50.5, t) * (1.0 - _smoothstep(54.6, 55.6, t))

                    if fn_alpha > 0.0:
                        eq_cy = 320.0 * sy
                        _draw_math_centered(canvas, self.img_leibniz_master, 960.0 * sx, eq_cy, alpha=fn_alpha, base_scale=0.55 * sx)

                        # Lower Footnote Card
                        card_cx = 960.0 * sx
                        card_cy = 710.0 * sy
                        card_w = 1100.0 * sx
                        card_h = 240.0 * sy
                        card_rect = skia.Rect.MakeXYWH(card_cx - card_w / 2.0, card_cy - card_h / 2.0, card_w, card_h)

                        canvas.drawRoundRect(card_rect, 18.0 * sx, 18.0 * sy, skia.Paint(
                            Color=_skia_color(CARD_BG, 0.92 * fn_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(card_rect, 18.0 * sx, 18.0 * sy, skia.Paint(
                            Color=_skia_color(GOLD, 0.65 * fn_alpha),
                            StrokeWidth=1.8 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                        # Footnote Content Lines
                        _draw_math_centered(canvas, self.img_fn_head, card_cx, card_cy - 75.0 * sy, alpha=fn_alpha, base_scale=0.52 * sx)
                        _draw_math_centered(canvas, self.img_fn_l1, card_cx, card_cy - 25.0 * sy, alpha=fn_alpha, base_scale=0.48 * sx)
                        _draw_math_centered(canvas, self.img_fn_l2, card_cx, card_cy + 25.0 * sy, alpha=fn_alpha, base_scale=0.48 * sx)
                        _draw_math_centered(canvas, self.img_fn_l3, card_cx, card_cy + 75.0 * sy, alpha=fn_alpha, base_scale=0.48 * sx)

                    # Phase 2: Grand Climax Resolution (55.0s - 61.55s)
                    climax_final = _smoothstep(54.8, 56.2, t)

                    if climax_final > 0.0:
                        eq_cy = 460.0 * sy
                        eq_scale = 0.64 * sx

                        # Anamorphic Laser Streak
                        streak_w = 1200.0 * sx
                        canvas.drawLine(960.0 * sx - streak_w / 2.0, eq_cy, 960.0 * sx + streak_w / 2.0, eq_cy, skia.Paint(
                            Color=_skia_color(MINT, 0.35 * climax_final),
                            StrokeWidth=3.5 * sy,
                            AntiAlias=True,
                        ))

                        eq_left = 960.0 * sx - (self.img_leibniz_master.width() * eq_scale) / 2.0
                        x_dydu = eq_left + self.master_centers[1] * eq_scale
                        x_dudx = eq_left + self.master_centers[2] * eq_scale

                        # Radiant Halo Auras around terms
                        canvas.drawCircle(x_dydu, eq_cy, 90.0 * sx, skia.Paint(
                            Color=_skia_color(GOLD, 0.18 * climax_final),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(x_dudx, eq_cy, 90.0 * sx, skia.Paint(
                            Color=_skia_color(CYAN, 0.18 * climax_final),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                        # Revolving photon rings around the machine rates
                        rev_ang = t * 3.0
                        for r_offset in [0.0, math.pi]:
                            rx1 = x_dydu + 95.0 * sx * math.cos(rev_ang + r_offset)
                            ry1 = eq_cy + 35.0 * sy * math.sin(rev_ang + r_offset)
                            canvas.drawCircle(rx1, ry1, 5.0 * sx, skia.Paint(
                                Color=_skia_color(GOLD, 0.90 * climax_final),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))

                            rx2 = x_dudx + 95.0 * sx * math.cos(rev_ang + r_offset)
                            ry2 = eq_cy + 35.0 * sy * math.sin(rev_ang + r_offset)
                            canvas.drawCircle(rx2, ry2, 5.0 * sx, skia.Paint(
                                Color=_skia_color(CYAN, 0.90 * climax_final),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))

                        # Draw Master Equation
                        _draw_math_centered(canvas, self.img_leibniz_master, 960.0 * sx, eq_cy, alpha=climax_final, base_scale=eq_scale)

                        # Crowning Master Summary Badge at Bottom
                        badge_cy = 680.0 * sy
                        _draw_math_centered(canvas, self.img_climax_summary, 960.0 * sx, badge_cy, alpha=climax_final, base_scale=0.55 * sx)

                        # Decorative Neon Border Frame for Climax Summary
                        cw = 1100.0 * sx
                        ch = 80.0 * sy
                        b_rect = skia.Rect.MakeXYWH(960.0 * sx - cw / 2.0, badge_cy - ch / 2.0, cw, ch)
                        canvas.drawRoundRect(b_rect, 14.0 * sx, 14.0 * sy, skia.Paint(
                            Color=_skia_color(WHITE, 0.12 * climax_final),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(b_rect, 14.0 * sx, 14.0 * sy, skia.Paint(
                            Color=_skia_color(MINT, 0.65 * climax_final),
                            StrokeWidth=1.5 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                snapshot = surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_08(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build and assemble Scene 08: Shrinking to Zero: From Discrete Fractions to Leibniz Derivatives."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    # Subtitles 88 to 110 span:
    # 00:03:46,560 --> 00:04:48,110 (226.56s to 288.11s, Duration = 61.55s)
    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            scene.add_audio(str(p), start=0.0, trim_start=226.56, trim_end=288.11)

    viewport = Viewport(LimitToDerivativeSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_08_DURATION)
    return scene
