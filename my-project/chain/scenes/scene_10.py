"""Scene 10: The Crucible of Verification: Analytic vs. Brute-Force at x = 1.

Chapter 5: Testing on a Real Example: y = sin(x^2).
Pure pitch-black void canvas (#000000), zero chalkboard formula clutter.
Clean, minimal, high-contrast, premium motion graphics:
- Dynamic CAD-grade rate modulators with animated stretch/compression calipers
- Microscopic coordinate rail with holographic magnifying loupe and displacement pulses
- Side-by-side cybernetic rate gauges with sweeping needles and illuminated laser bridge
- Holographic convergence verification badge with expanding shockwaves
- Mechanical involute gear train with physical disengagement animation and missing gear alert
"""

from __future__ import annotations

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

SCENE_10_DURATION: float = 54.96

# High-Voltage Electric RGB Color Palette (Matching project visual style)
CYAN = "#00F5FF"     # Electric Laser Cyan (Variable x, 2x, du/dx, Delta x)
GOLD = "#FFB800"     # Radiant Gold (Variable u, cos(1), dy/du, Delta u)
WHITE = "#FFFFFF"    # Crisp Pure White (Operators, grid, specular highlights)
MINT = "#05FFA1"     # High-Voltage Neon Mint (dy/dx, 1.0806, 1.080, verified check)
CORAL = "#FF2A6D"    # Laser Neon Coral (Variable y, Delta y, Fatal Error, !=)
AMBER = "#FF8800"    # Emergency Amber (50% loss, gear disconnect spark)
CARD_BG = "#080e18"  # Ultra-dark cybernetic glassmorphic card fill
CARD_BORDER = "#1b293d"  # Subtle structural card border


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


def _compose_latex_equation(
    terms: Sequence[tuple[str, str] | tuple[str, str, int]],
    font_size: int = 34,
    spacing: int = 14,
    dpi: int = 200,
) -> skia.Image:
    """Compose multi-term colored LaTeX equation with exact TeX mathematical baseline alignment."""
    prop = FontProperties(size=font_size)
    parsed_terms = []
    for item in terms:
        if len(item) == 3:
            parsed_terms.append((item[0], item[1], int(item[2])))
        else:
            parsed_terms.append((item[0], item[1], spacing))

    imgs_with_depth_gap = [
        (_render_mathtext_transparent(t, color=c, prop=prop, dpi=dpi), gap)
        for t, c, gap in parsed_terms
    ]
    max_ascent = max(img.height - d for (img, d), gap in imgs_with_depth_gap)
    max_descent = max(d for (img, d), gap in imgs_with_depth_gap)
    total_height = int(max_ascent + max_descent + 8)

    total_width = 16
    for i, ((img, d), gap) in enumerate(imgs_with_depth_gap):
        total_width += img.width
        if i < len(imgs_with_depth_gap) - 1:
            total_width += gap

    comp = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
    cur_x = 8
    baseline_y = max_ascent + 4

    for i, ((img, d), gap) in enumerate(imgs_with_depth_gap):
        y = int(baseline_y - (img.height - d))
        comp.alpha_composite(img, (cur_x, y))
        cur_x += img.width + (gap if i < len(imgs_with_depth_gap) - 1 else 0)

    return skia.Image.fromarray(np.array(comp), skia.ColorType.kRGBA_8888_ColorType)


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


def _draw_dial_gauge(
    canvas: skia.Canvas,
    cx: float,
    cy: float,
    radius: float,
    value: float,
    max_value: float,
    color_hex: str,
    alpha: float,
    sx: float,
    sy: float,
    title_img: skia.Image | None = None,
    val_img: skia.Image | None = None,
) -> None:
    """Draw a high-precision semi-circular rate gauge with needle, tick marks, and glow arc."""
    if alpha <= 0.0:
        return

    start_angle = 135.0
    sweep_angle = 270.0
    rect = skia.Rect.MakeXYWH(cx - radius, cy - radius, radius * 2.0, radius * 2.0)

    # Dial Face Backplate
    canvas.drawCircle(cx, cy, radius + 14.0 * sx, skia.Paint(
        Color=_skia_color(CARD_BG, 0.70 * alpha),
        Style=skia.Paint.kFill_Style,
        AntiAlias=True,
    ))
    canvas.drawCircle(cx, cy, radius + 14.0 * sx, skia.Paint(
        Color=_skia_color(CARD_BORDER, 0.80 * alpha),
        StrokeWidth=1.5 * sx,
        Style=skia.Paint.kStroke_Style,
        AntiAlias=True,
    ))

    # Background Track
    bg_paint = skia.Paint(
        Color=_skia_color(WHITE, 0.12 * alpha),
        StrokeWidth=6.0 * sx,
        Style=skia.Paint.kStroke_Style,
        AntiAlias=True,
    )
    canvas.drawArc(rect, start_angle, sweep_angle, False, bg_paint)

    # Active Value Arc
    pct = max(0.0, min(1.0, value / max_value))
    active_sweep = sweep_angle * pct
    if active_sweep > 0.0:
        # Glow Halo
        canvas.drawArc(rect, start_angle, active_sweep, False, skia.Paint(
            Color=_skia_color(color_hex, 0.28 * alpha),
            StrokeWidth=14.0 * sx,
            Style=skia.Paint.kStroke_Style,
            AntiAlias=True,
        ))
        # Core Crisp Line
        canvas.drawArc(rect, start_angle, active_sweep, False, skia.Paint(
            Color=_skia_color(color_hex, 0.98 * alpha),
            StrokeWidth=5.0 * sx,
            Style=skia.Paint.kStroke_Style,
            AntiAlias=True,
        ))

    # Precision Tick Marks (9 major ticks)
    num_ticks = 8
    for i in range(num_ticks + 1):
        frac = i / float(num_ticks)
        deg = start_angle + frac * sweep_angle
        rad = math.radians(deg)
        r_inner = radius - (10.0 if i % 2 == 0 else 6.0) * sx
        r_outer = radius + 3.0 * sx
        x0 = cx + r_inner * math.cos(rad)
        y0 = cy + r_inner * math.sin(rad)
        x1 = cx + r_outer * math.cos(rad)
        y1 = cy + r_outer * math.sin(rad)
        canvas.drawLine(x0, y0, x1, y1, skia.Paint(
            Color=_skia_color(WHITE, (0.60 if i % 2 == 0 else 0.30) * alpha),
            StrokeWidth=(2.0 if i % 2 == 0 else 1.2) * sx,
            AntiAlias=True,
        ))

    # Needle
    needle_angle = start_angle + pct * sweep_angle
    n_rad = math.radians(needle_angle)
    nx = cx + (radius - 8.0 * sx) * math.cos(n_rad)
    ny = cy + (radius - 8.0 * sx) * math.sin(n_rad)

    # Needle Laser Line
    canvas.drawLine(cx, cy, nx, ny, skia.Paint(
        Color=_skia_color(color_hex, 0.98 * alpha),
        StrokeWidth=2.8 * sx,
        AntiAlias=True,
    ))
    # Center Pivot Hub
    canvas.drawCircle(cx, cy, 5.5 * sx, skia.Paint(
        Color=_skia_color(WHITE, 0.98 * alpha),
        Style=skia.Paint.kFill_Style,
        AntiAlias=True,
    ))
    canvas.drawCircle(cx, cy, 12.0 * sx, skia.Paint(
        Color=_skia_color(color_hex, 0.35 * alpha),
        Style=skia.Paint.kFill_Style,
        AntiAlias=True,
    ))

    # Title & Value readouts
    if title_img is not None:
        _draw_math_centered(canvas, title_img, cx, cy - radius * 0.38, alpha=alpha, base_scale=0.46 * sx)
    if val_img is not None:
        _draw_math_centered(canvas, val_img, cx, cy + radius + 28.0 * sy, alpha=alpha, base_scale=0.52 * sx)


def _draw_involute_gear(
    canvas: skia.Canvas,
    cx: float,
    cy: float,
    radius: float,
    teeth: int,
    angle: float,
    color_hex: str,
    alpha: float,
    sx: float,
) -> None:
    """Draw a precision mechanical involute gear with teeth, pitch circle, spokes, and hub."""
    if alpha <= 0.0:
        return

    tooth_h = radius * 0.20
    r_outer = radius + tooth_h * 0.5
    r_inner = radius - tooth_h * 0.5
    step = 2.0 * math.pi / teeth

    path = skia.Path()
    for i in range(teeth):
        a0 = angle + i * step
        a1 = a0 + step * 0.22
        a2 = a0 + step * 0.50
        a3 = a0 + step * 0.72

        p0 = (cx + r_inner * math.cos(a0), cy + r_inner * math.sin(a0))
        p1 = (cx + r_outer * math.cos(a1), cy + r_outer * math.sin(a1))
        p2 = (cx + r_outer * math.cos(a2), cy + r_outer * math.sin(a2))
        p3 = (cx + r_inner * math.cos(a3), cy + r_inner * math.sin(a3))

        if i == 0:
            path.moveTo(p0[0], p0[1])
        else:
            path.lineTo(p0[0], p0[1])
        path.lineTo(p1[0], p1[1])
        path.lineTo(p2[0], p2[1])
        path.lineTo(p3[0], p3[1])
    path.close()

    # Semi-transparent gear body
    canvas.drawPath(path, skia.Paint(
        Color=_skia_color(color_hex, 0.16 * alpha),
        Style=skia.Paint.kFill_Style,
        AntiAlias=True,
    ))
    # Crisp Glowing Border
    canvas.drawPath(path, skia.Paint(
        Color=_skia_color(color_hex, 0.95 * alpha),
        StrokeWidth=2.4 * sx,
        Style=skia.Paint.kStroke_Style,
        AntiAlias=True,
    ))

    # Pitch Circle (dashed)
    canvas.drawCircle(cx, cy, radius, skia.Paint(
        Color=_skia_color(WHITE, 0.25 * alpha),
        StrokeWidth=1.2 * sx,
        PathEffect=skia.DashPathEffect.Make([4.0 * sx, 4.0 * sx], 0.0),
        Style=skia.Paint.kStroke_Style,
        AntiAlias=True,
    ))

    # Axle Rim & Center Hub
    canvas.drawCircle(cx, cy, radius * 0.38, skia.Paint(
        Color=_skia_color(color_hex, 0.85 * alpha),
        StrokeWidth=2.0 * sx,
        Style=skia.Paint.kStroke_Style,
        AntiAlias=True,
    ))
    canvas.drawCircle(cx, cy, radius * 0.14, skia.Paint(
        Color=_skia_color(WHITE, 0.98 * alpha),
        Style=skia.Paint.kFill_Style,
        AntiAlias=True,
    ))

    # 4 Mechanical Spokes
    for s_idx in range(4):
        spoke_a = angle + s_idx * (math.pi / 2.0)
        sx0 = cx + (radius * 0.14) * math.cos(spoke_a)
        sy0 = cy + (radius * 0.14) * math.sin(spoke_a)
        sx1 = cx + (radius * 0.75) * math.cos(spoke_a)
        sy1 = cy + (radius * 0.75) * math.sin(spoke_a)
        canvas.drawLine(sx0, sy0, sx1, sy1, skia.Paint(
            Color=_skia_color(color_hex, 0.75 * alpha),
            StrokeWidth=2.2 * sx,
            AntiAlias=True,
        ))


class Scene10VerificationSource:
    """Procedural source for Scene 10: Clean, minimal, high-contrast, premium motion graphics."""

    duration: float = SCENE_10_DURATION
    fps: int = 30
    intrinsic_size: tuple[int, int] = (1920, 1080)
    fingerprint: str = "chain:scene-10:visual-redesign:v3"
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

                # =================================================================
                # PRECOMPILE MINIMAL HIGH-CONTRAST LATEX TOKENS (ZERO REDUNDANCY)
                # =================================================================

                # 1. Operating Point Badge (Clean & Minimal)
                self.img_op_point = _compose_latex_equation(
                    [
                        (r"\mathbf{x = 1}", CYAN, 14),
                        (r"\mathbf{\Longrightarrow}", WHITE, 14),
                        (r"\mathbf{u = 1}", GOLD, 0),
                    ],
                    font_size=38,
                    spacing=14,
                )

                # 2. Panel Headers
                self.img_hdr_analytic = _compose_latex_equation(
                    [(r"\mathbf{Analytic\ Transmission\ \left[ \frac{dy}{dx} \right]}", MINT, 0)],
                    font_size=32,
                )
                self.img_hdr_brute = _compose_latex_equation(
                    [(r"\mathbf{Empirical\ Perturbation\ \left[ \frac{\Delta y}{\Delta x} \right]}", MINT, 0)],
                    font_size=32,
                )

                # 3. Inner Machine: Rate & Multiplier Tag
                self.img_inner_tag = _compose_latex_equation(
                    [
                        (r"\left.\frac{du}{dx}\right|_{x=1}", CYAN, 12),
                        (r"=", WHITE, 12),
                        (r"2x", CYAN, 12),
                        (r"=", WHITE, 12),
                        (r"\mathbf{2.00}", CYAN, 0),
                    ],
                    font_size=30,
                    spacing=10,
                )
                self.img_inner_mult = _compose_latex_equation(
                    [(r"\mathbf{\times 2.0}", CYAN, 0)],
                    font_size=32,
                )

                # 4. Outer Machine: Rate & Multiplier Tag
                self.img_outer_tag = _compose_latex_equation(
                    [
                        (r"\left.\frac{dy}{du}\right|_{u=1}", GOLD, 12),
                        (r"=", WHITE, 12),
                        (r"\cos(1)", GOLD, 12),
                        (r"\approx", WHITE, 12),
                        (r"\mathbf{0.54}", GOLD, 0),
                    ],
                    font_size=30,
                    spacing=10,
                )
                self.img_outer_mult = _compose_latex_equation(
                    [(r"\mathbf{\times 0.54}", GOLD, 0)],
                    font_size=32,
                )

                # 5. Master Composite Product Formula
                self.img_product_rate = _compose_latex_equation(
                    [
                        (r"\frac{dy}{dx}", MINT, 12),
                        (r"=", WHITE, 12),
                        (r"\mathbf{2.0}", CYAN, 10),
                        (r"\times", WHITE, 10),
                        (r"\mathbf{0.54}", GOLD, 12),
                        (r"\approx", WHITE, 12),
                        (r"\mathbf{1.0806}", MINT, 0),
                    ],
                    font_size=36,
                    spacing=12,
                )
                self.img_gauge_t1 = _compose_latex_equation(
                    [(r"\mathbf{1.0806\times}", MINT, 0)],
                    font_size=32,
                )
                self.img_gauge_title1 = _compose_latex_equation(
                    [(r"\mathrm{Analytic}", WHITE, 0)],
                    font_size=24,
                )

                # 6. Shot 10B: Microscopic Nudge Delta x = +0.0010
                self.img_nudge_dx = _compose_latex_equation(
                    [
                        (r"\mathbf{\Delta x}", CYAN, 12),
                        (r"=", WHITE, 12),
                        (r"\mathbf{+0.0010}", CYAN, 0),
                    ],
                    font_size=32,
                    spacing=10,
                )
                self.img_squaring_du = _compose_latex_equation(
                    [
                        (r"\mathbf{\Delta u}", GOLD, 10),
                        (r"\approx", WHITE, 10),
                        (r"\mathbf{2 \times \Delta x}", CYAN, 12),
                        (r"=", WHITE, 10),
                        (r"\mathbf{+0.0020}", GOLD, 0),
                    ],
                    font_size=30,
                    spacing=10,
                )
                self.img_sine_dy = _compose_latex_equation(
                    [
                        (r"\mathbf{\Delta y}", CORAL, 10),
                        (r"\approx", WHITE, 10),
                        (r"\mathbf{0.54 \times \Delta u}", GOLD, 12),
                        (r"=", WHITE, 10),
                        (r"\mathbf{+0.00108}", CORAL, 0),
                    ],
                    font_size=30,
                    spacing=10,
                )
                self.img_empirical_ratio = _compose_latex_equation(
                    [
                        (r"\frac{\Delta y}{\Delta x}", CORAL, 12),
                        (r"=", WHITE, 12),
                        (r"\frac{0.00108}{0.00100}", WHITE, 12),
                        (r"=", WHITE, 12),
                        (r"\mathbf{1.080}", MINT, 0),
                    ],
                    font_size=36,
                    spacing=12,
                )
                self.img_gauge_t2 = _compose_latex_equation(
                    [(r"\mathbf{1.080\times}", MINT, 0)],
                    font_size=32,
                )
                self.img_gauge_title2 = _compose_latex_equation(
                    [(r"\mathrm{Empirical}", WHITE, 0)],
                    font_size=24,
                )

                # 7. Shot 10C: Grand Convergence
                self.img_grand_convergence = _compose_latex_equation(
                    [
                        (r"\mathbf{\left.\frac{dy}{dx}\right|_{x=1}}", CYAN, 18),
                        (r"\mathbf{\equiv}", WHITE, 18),
                        (r"\mathbf{\frac{\Delta y}{\Delta x}}", CORAL, 18),
                        (r"=", WHITE, 18),
                        (r"\mathbf{1.080}", MINT, 0),
                    ],
                    font_size=56,
                    spacing=18,
                )
                self.img_grand_check = _compose_latex_equation(
                    [
                        (r"\mathbf{\checkmark}", MINT, 16),
                        (r"\mathbf{Formula\ and\ Brute\ Force\ Agree}", MINT, 0),
                    ],
                    font_size=36,
                    spacing=14,
                )

                # 8. Shot 10D: Broken Drive Train & Missing Gear Alert
                self.img_alert_fatal = _compose_latex_equation(
                    [
                        (r"\frac{d}{dx}\left[\sin(x^2)\right]", WHITE, 16),
                        (r"\neq", CORAL, 16),
                        (r"\cos(x^2)", GOLD, 0),
                    ],
                    font_size=52,
                    spacing=16,
                )
                self.img_gear_lbl_inner = _compose_latex_equation(
                    [(r"\mathbf{Inner:\ 2x}", CORAL, 0)],
                    font_size=32,
                )
                self.img_gear_lbl_outer = _compose_latex_equation(
                    [(r"\mathbf{Outer:\ \cos(u)}", GOLD, 0)],
                    font_size=32,
                )
                self.img_alert_missing_desc = _compose_latex_equation(
                    [
                        (r"\mathbf{Missing\ First\ Gear:\ 2x}", CORAL, 0),
                    ],
                    font_size=34,
                )
                self.img_alert_loss_badge = _compose_latex_equation(
                    [
                        (r"\mathbf{1.08}", MINT, 16),
                        (r"\longrightarrow", WHITE, 16),
                        (r"\mathbf{0.54}", GOLD, 16),
                        (r"\mathbf{[-50\%\ Loss]}", CORAL, 0),
                    ],
                    font_size=38,
                    spacing=16,
                )

            def frame(self, t: float) -> Image.Image:
                canvas = self.canvas
                w = self.w
                h = self.h
                sx = self.sx
                sy = self.sy

                # 1. Pure Pitch-Black Void Canvas (#000000)
                canvas.clear(skia.ColorSetARGB(255, 0, 0, 0))

                # Subtle Cybernetic Void Grid (Architecture background)
                grid_p = skia.Paint(
                    Color=_skia_color(WHITE, 0.020),
                    StrokeWidth=1.0 * sx,
                    Style=skia.Paint.kStroke_Style,
                    AntiAlias=False,
                )
                grid_step = int(120 * sx)
                for gx in range(0, w, grid_step):
                    canvas.drawLine(gx, 0, gx, h, grid_p)
                for gy in range(0, h, grid_step):
                    canvas.drawLine(0, gy, w, gy, grid_p)

                # =========================================================================
                # TIMELINE & SHOT LOGIC
                # -------------------------------------------------------------------------
                # Shot 10A, 10B, 10C: Dual-Track Telemetry Lab (0.0s - 47.0s)
                # Shot 10D: Broken Drive Train & Missing Gear Alert (47.0s - 54.96s)
                # =========================================================================
                shot_d_alpha = _smoothstep(47.0, 48.2, t)
                main_alpha = 1.0 - shot_d_alpha

                if main_alpha > 0.0:
                    # Slide transition: at t=16.5s, left panel glides from center (960px) to left (480px)
                    slide_p = _smoothstep(16.5, 18.0, t)
                    left_cx = (960.0 - 480.0 * slide_p) * sx
                    right_cx = 1440.0 * sx

                    # Operating Point Badge (Pinned at top, clean and elegant)
                    op_alpha = _smoothstep(0.0, 1.2, t) * main_alpha
                    _draw_math_centered(canvas, self.img_op_point, 960.0 * sx, 70.0 * sy, alpha=op_alpha, base_scale=0.52 * sx)

                    # ---------------------------------------------------------------------
                    # LEFT PANEL: ANALYTIC TRANSMISSION (Shot 10A)
                    # ---------------------------------------------------------------------
                    panel_w = 840.0 * sx
                    panel_h = 880.0 * sy
                    panel_cy = 580.0 * sy

                    # Draw Left Glassmorphic Card Frame
                    p1_rect = skia.Rect.MakeXYWH(left_cx - panel_w / 2.0, panel_cy - panel_h / 2.0, panel_w, panel_h)
                    canvas.drawRoundRect(p1_rect, 18.0 * sx, 18.0 * sy, skia.Paint(
                        Color=_skia_color(CARD_BG, 0.75 * main_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawRoundRect(p1_rect, 18.0 * sx, 18.0 * sy, skia.Paint(
                        Color=_skia_color(CARD_BORDER, 0.85 * main_alpha),
                        StrokeWidth=1.6 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))

                    # Left Panel Header
                    _draw_math_centered(canvas, self.img_hdr_analytic, left_cx, panel_cy - panel_h / 2.0 + 40.0 * sy, alpha=main_alpha, base_scale=0.50 * sx)

                    # ---------------------------------------------------------------------
                    # 1. Inner Rate Modulator: 2x Stretch (Active from 2.0s)
                    # ---------------------------------------------------------------------
                    inner_alpha = _smoothstep(2.0, 3.2, t) * main_alpha
                    if inner_alpha > 0.0:
                        y_m1 = panel_cy - 240.0 * sy
                        _draw_math_centered(canvas, self.img_inner_tag, left_cx - 140.0 * sx, y_m1, alpha=inner_alpha, base_scale=0.50 * sx)
                        _draw_math_centered(canvas, self.img_inner_mult, left_cx + 260.0 * sx, y_m1, alpha=inner_alpha, base_scale=0.52 * sx)

                        # Graphic: Dynamic Laser Caliper Stretches 1.0x -> 2.0x
                        stretch_p = _smoothstep(3.5, 6.0, t)
                        c_bar_y = y_m1 + 42.0 * sy
                        base_len = 100.0 * sx
                        cur_len = base_len * (1.0 + stretch_p * 1.0)  # expands to 2.0x

                        # Reference baseline (dim)
                        canvas.drawLine(left_cx - base_len, c_bar_y, left_cx, c_bar_y, skia.Paint(
                            Color=_skia_color(WHITE, 0.20 * inner_alpha),
                            StrokeWidth=2.0 * sy,
                            AntiAlias=True,
                        ))
                        # Active stretched bar (Cyan neon)
                        canvas.drawLine(left_cx - base_len, c_bar_y, left_cx - base_len + cur_len, c_bar_y, skia.Paint(
                            Color=_skia_color(CYAN, 0.95 * inner_alpha),
                            StrokeWidth=4.0 * sy,
                            AntiAlias=True,
                        ))
                        # Caliper Brackets
                        canvas.drawLine(left_cx - base_len, c_bar_y - 8.0 * sy, left_cx - base_len, c_bar_y + 8.0 * sy, skia.Paint(
                            Color=_skia_color(CYAN, 0.98 * inner_alpha),
                            StrokeWidth=2.4 * sx,
                            AntiAlias=True,
                        ))
                        canvas.drawLine(left_cx - base_len + cur_len, c_bar_y - 8.0 * sy, left_cx - base_len + cur_len, c_bar_y + 8.0 * sy, skia.Paint(
                            Color=_skia_color(CYAN, 0.98 * inner_alpha),
                            StrokeWidth=2.4 * sx,
                            AntiAlias=True,
                        ))

                    # ---------------------------------------------------------------------
                    # 2. Outer Rate Modulator: 0.54x Compression (Active from 7.0s)
                    # ---------------------------------------------------------------------
                    outer_alpha = _smoothstep(7.0, 8.2, t) * main_alpha
                    if outer_alpha > 0.0:
                        y_m2 = panel_cy - 110.0 * sy
                        _draw_math_centered(canvas, self.img_outer_tag, left_cx - 140.0 * sx, y_m2, alpha=outer_alpha, base_scale=0.50 * sx)
                        _draw_math_centered(canvas, self.img_outer_mult, left_cx + 260.0 * sx, y_m2, alpha=outer_alpha, base_scale=0.52 * sx)

                        # Graphic: Dynamic Caliper Compresses to 0.54x
                        comp_p = _smoothstep(8.5, 11.0, t)
                        c_bar_y2 = y_m2 + 42.0 * sy
                        base_len2 = 200.0 * sx
                        cur_len2 = base_len2 * (1.0 - comp_p * 0.46)  # shrinks from 1.0x to 0.54x

                        # Reference baseline (dim)
                        canvas.drawLine(left_cx - base_len2 / 2.0, c_bar_y2, left_cx + base_len2 / 2.0, c_bar_y2, skia.Paint(
                            Color=_skia_color(WHITE, 0.20 * outer_alpha),
                            StrokeWidth=2.0 * sy,
                            AntiAlias=True,
                        ))
                        # Active compressed bar (Gold neon)
                        canvas.drawLine(left_cx - base_len2 / 2.0, c_bar_y2, left_cx - base_len2 / 2.0 + cur_len2, c_bar_y2, skia.Paint(
                            Color=_skia_color(GOLD, 0.95 * outer_alpha),
                            StrokeWidth=4.0 * sy,
                            AntiAlias=True,
                        ))
                        # Caliper Brackets
                        canvas.drawLine(left_cx - base_len2 / 2.0, c_bar_y2 - 8.0 * sy, left_cx - base_len2 / 2.0, c_bar_y2 + 8.0 * sy, skia.Paint(
                            Color=_skia_color(GOLD, 0.98 * outer_alpha),
                            StrokeWidth=2.4 * sx,
                            AntiAlias=True,
                        ))
                        canvas.drawLine(left_cx - base_len2 / 2.0 + cur_len2, c_bar_y2 - 8.0 * sy, left_cx - base_len2 / 2.0 + cur_len2, c_bar_y2 + 8.0 * sy, skia.Paint(
                            Color=_skia_color(GOLD, 0.98 * outer_alpha),
                            StrokeWidth=2.4 * sx,
                            AntiAlias=True,
                        ))

                    # ---------------------------------------------------------------------
                    # 3. Product Cascade & Left Dial Gauge (Active from 11.5s)
                    # ---------------------------------------------------------------------
                    prod_alpha = _smoothstep(11.5, 12.8, t) * main_alpha
                    if prod_alpha > 0.0:
                        y_prod = panel_cy + 40.0 * sy
                        _draw_math_centered(canvas, self.img_product_rate, left_cx, y_prod, alpha=prod_alpha, base_scale=0.54 * sx)

                    gauge1_alpha = _smoothstep(13.0, 14.5, t) * main_alpha
                    if gauge1_alpha > 0.0:
                        g1_p = _smoothstep(13.2, 16.0, t)
                        val1 = 1.0806 * g1_p
                        gy1 = panel_cy + 220.0 * sy
                        _draw_dial_gauge(
                            canvas, left_cx, gy1, 100.0 * sx, val1, 2.0, MINT, gauge1_alpha, sx, sy,
                            title_img=self.img_gauge_title1, val_img=self.img_gauge_t1
                        )

                    # ---------------------------------------------------------------------
                    # RIGHT PANEL: EMPIRICAL BRUTE FORCE PERTURBATION (Shot 10B)
                    # ---------------------------------------------------------------------
                    t2_alpha = _smoothstep(17.0, 18.2, t) * main_alpha
                    if t2_alpha > 0.0:
                        # Draw Right Glassmorphic Card Frame
                        p2_rect = skia.Rect.MakeXYWH(right_cx - panel_w / 2.0, panel_cy - panel_h / 2.0, panel_w, panel_h)
                        canvas.drawRoundRect(p2_rect, 18.0 * sx, 18.0 * sy, skia.Paint(
                            Color=_skia_color(CARD_BG, 0.75 * t2_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(p2_rect, 18.0 * sx, 18.0 * sy, skia.Paint(
                            Color=_skia_color(CARD_BORDER, 0.85 * t2_alpha),
                            StrokeWidth=1.6 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                        # Right Panel Header
                        _draw_math_centered(canvas, self.img_hdr_brute, right_cx, panel_cy - panel_h / 2.0 + 40.0 * sy, alpha=t2_alpha, base_scale=0.50 * sx)

                        # 1. Microscopic Coordinate Rail & Nudge Loupe
                        nudge_alpha = _smoothstep(17.5, 18.8, t) * t2_alpha
                        if nudge_alpha > 0.0:
                            y_nudge = panel_cy - 240.0 * sy
                            _draw_math_centered(canvas, self.img_nudge_dx, right_cx, y_nudge - 30.0 * sy, alpha=nudge_alpha, base_scale=0.50 * sx)

                            # Coordinate Track Rail
                            rail_y = y_nudge + 25.0 * sy
                            rail_w = 460.0 * sx
                            canvas.drawLine(right_cx - rail_w / 2.0, rail_y, right_cx + rail_w / 2.0, rail_y, skia.Paint(
                                Color=_skia_color(WHITE, 0.30 * nudge_alpha),
                                StrokeWidth=1.8 * sx,
                                AntiAlias=True,
                            ))
                            # Track Ticks
                            for tick_idx in range(-2, 3):
                                tx = right_cx + tick_idx * 90.0 * sx
                                canvas.drawLine(tx, rail_y - 6.0 * sy, tx, rail_y + 6.0 * sy, skia.Paint(
                                    Color=_skia_color(WHITE, 0.45 * nudge_alpha),
                                    StrokeWidth=1.5 * sx,
                                    AntiAlias=True,
                                ))

                            # Holographic Magnifying Loupe Circle
                            loupe_r = 38.0 * sx
                            canvas.drawCircle(right_cx, rail_y, loupe_r, skia.Paint(
                                Color=_skia_color(CYAN, 0.16 * nudge_alpha),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))
                            canvas.drawCircle(right_cx, rail_y, loupe_r, skia.Paint(
                                Color=_skia_color(CYAN, 0.95 * nudge_alpha),
                                StrokeWidth=2.2 * sx,
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            ))
                            # Animated Emerald Nudge Pulse inside Loupe
                            dx_pulse = _smoothstep(19.0, 21.0, t)
                            canvas.drawLine(right_cx - 24.0 * sx, rail_y + 3.0 * sy, right_cx - 24.0 * sx + (48.0 * dx_pulse) * sx, rail_y + 3.0 * sy, skia.Paint(
                                Color=_skia_color(MINT, 0.98 * nudge_alpha),
                                StrokeWidth=3.5 * sy,
                                AntiAlias=True,
                            ))

                        # 2. Squaring Stage Physical Displacement: Expands 2x
                        sq_alpha = _smoothstep(22.0, 23.2, t) * t2_alpha
                        if sq_alpha > 0.0:
                            y_sq = panel_cy - 120.0 * sy
                            _draw_math_centered(canvas, self.img_squaring_du, right_cx, y_sq - 25.0 * sy, alpha=sq_alpha, base_scale=0.50 * sx)

                            # Dynamic Displacement Bar (Amber, doubles to 2x)
                            du_p = _smoothstep(24.5, 27.0, t)
                            du_w = 120.0 * sx * (1.0 + du_p * 1.0)
                            du_y = y_sq + 28.0 * sy

                            canvas.drawLine(right_cx - du_w / 2.0, du_y, right_cx + du_w / 2.0, du_y, skia.Paint(
                                Color=_skia_color(GOLD, 0.95 * sq_alpha),
                                StrokeWidth=4.0 * sy,
                                AntiAlias=True,
                            ))
                            # End brackets
                            canvas.drawLine(right_cx - du_w / 2.0, du_y - 8.0 * sy, right_cx - du_w / 2.0, du_y + 8.0 * sy, skia.Paint(
                                Color=_skia_color(GOLD, 0.98 * sq_alpha),
                                StrokeWidth=2.4 * sx,
                                AntiAlias=True,
                            ))
                            canvas.drawLine(right_cx + du_w / 2.0, du_y - 8.0 * sy, right_cx + du_w / 2.0, du_y + 8.0 * sy, skia.Paint(
                                Color=_skia_color(GOLD, 0.98 * sq_alpha),
                                StrokeWidth=2.4 * sx,
                                AntiAlias=True,
                            ))

                        # 3. Sine Stage Physical Displacement: Compresses by 0.54x
                        sin_alpha = _smoothstep(29.0, 30.2, t) * t2_alpha
                        if sin_alpha > 0.0:
                            y_sin = panel_cy - 10.0 * sy
                            _draw_math_centered(canvas, self.img_sine_dy, right_cx, y_sin - 25.0 * sy, alpha=sin_alpha, base_scale=0.50 * sx)

                            # Dynamic Displacement Bar (Coral, compresses to 0.54x)
                            dy_p = _smoothstep(31.0, 33.5, t)
                            dy_w = 240.0 * sx * (1.0 - dy_p * 0.46)
                            dy_y = y_sin + 28.0 * sy

                            canvas.drawLine(right_cx - dy_w / 2.0, dy_y, right_cx + dy_w / 2.0, dy_y, skia.Paint(
                                Color=_skia_color(CORAL, 0.95 * sin_alpha),
                                StrokeWidth=4.0 * sy,
                                AntiAlias=True,
                            ))
                            # End brackets
                            canvas.drawLine(right_cx - dy_w / 2.0, dy_y - 8.0 * sy, right_cx - dy_w / 2.0, dy_y + 8.0 * sy, skia.Paint(
                                Color=_skia_color(CORAL, 0.98 * sin_alpha),
                                StrokeWidth=2.4 * sx,
                                AntiAlias=True,
                            ))
                            canvas.drawLine(right_cx + dy_w / 2.0, dy_y - 8.0 * sy, right_cx + dy_w / 2.0, dy_y + 8.0 * sy, skia.Paint(
                                Color=_skia_color(CORAL, 0.98 * sin_alpha),
                                StrokeWidth=2.4 * sx,
                                AntiAlias=True,
                            ))

                        # 4. Empirical Ratio & Right Dial Gauge
                        ratio_alpha = _smoothstep(36.0, 37.2, t) * t2_alpha
                        if ratio_alpha > 0.0:
                            y_ratio = panel_cy + 95.0 * sy
                            _draw_math_centered(canvas, self.img_empirical_ratio, right_cx, y_ratio, alpha=ratio_alpha, base_scale=0.52 * sx)

                        gauge2_alpha = _smoothstep(38.0, 39.5, t) * t2_alpha
                        if gauge2_alpha > 0.0:
                            g2_p = _smoothstep(38.2, 41.5, t)
                            val2 = 1.080 * g2_p
                            gy2 = panel_cy + 220.0 * sy
                            _draw_dial_gauge(
                                canvas, right_cx, gy2, 100.0 * sx, val2, 2.0, MINT, gauge2_alpha, sx, sy,
                                title_img=self.img_gauge_title2, val_img=self.img_gauge_t2
                            )

                    # ---------------------------------------------------------------------
                    # SHOT 10C: THE GRAND CONVERGENCE & AGREEMENT (42.0s - 47.0s)
                    # ---------------------------------------------------------------------
                    conv_alpha = _smoothstep(42.0, 43.5, t) * main_alpha
                    if conv_alpha > 0.0:
                        # Soft background dimming over panels so central card pops
                        canvas.drawRect(skia.Rect.MakeWH(w, h), skia.Paint(
                            Color=_skia_color("#000000", 0.72 * conv_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                        # Expanding Concentric Energy Shockwave Rings
                        shock_p = _smoothstep(42.5, 45.5, t)
                        for ring_idx in range(3):
                            r_off = ring_idx * 0.28
                            r_prog = (shock_p + r_off) % 1.0
                            r_radius = 600.0 * sx * r_prog
                            r_alpha = (1.0 - r_prog) * 0.65 * conv_alpha
                            canvas.drawCircle(960.0 * sx, panel_cy + 120.0 * sy, r_radius, skia.Paint(
                                Color=_skia_color(MINT, r_alpha),
                                StrokeWidth=3.2 * sx,
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            ))

                        # High-Energy Laser Bridge connecting Left & Right Gauges
                        bridge_y = panel_cy + 220.0 * sy
                        canvas.drawLine(left_cx + 100.0 * sx, bridge_y, right_cx - 100.0 * sx, bridge_y, skia.Paint(
                            Color=_skia_color(MINT, 0.40 * conv_alpha),
                            StrokeWidth=8.0 * sy,
                            AntiAlias=True,
                        ))
                        canvas.drawLine(left_cx + 100.0 * sx, bridge_y, right_cx - 100.0 * sx, bridge_y, skia.Paint(
                            Color=_skia_color(WHITE, 0.95 * conv_alpha),
                            StrokeWidth=2.8 * sy,
                            AntiAlias=True,
                        ))

                        # Center Holographic Convergence Banner
                        badge_w = 1100.0 * sx
                        badge_h = 220.0 * sy
                        badge_cy = panel_cy + 10.0 * sy
                        badge_rect = skia.Rect.MakeXYWH(960.0 * sx - badge_w / 2.0, badge_cy - badge_h / 2.0, badge_w, badge_h)

                        # Drop Shadow & Backplate
                        canvas.drawRoundRect(badge_rect.makeOutset(14.0 * sx, 14.0 * sy), 24.0 * sx, 24.0 * sy, skia.Paint(
                            Color=_skia_color("#000000", 0.96 * conv_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(badge_rect, 22.0 * sx, 22.0 * sy, skia.Paint(
                            Color=_skia_color("#02150d", 0.98 * conv_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(badge_rect, 22.0 * sx, 22.0 * sy, skia.Paint(
                            Color=_skia_color(MINT, 0.98 * conv_alpha),
                            StrokeWidth=3.2 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                        # Master Equivalence Equation & Verification Stamp
                        _draw_math_centered(canvas, self.img_grand_convergence, 960.0 * sx, badge_cy - 35.0 * sy, alpha=conv_alpha, base_scale=0.56 * sx)
                        _draw_math_centered(canvas, self.img_grand_check, 960.0 * sx, badge_cy + 45.0 * sy, alpha=conv_alpha, base_scale=0.50 * sx)

                # =========================================================================
                # SHOT 10D: BROKEN DRIVE TRAIN / "MISSING GEAR" ALERT (47.0s - 54.96s)
                # =========================================================================
                if shot_d_alpha > 0.0:
                    alert_cx = 960.0 * sx

                    # Ambient Crimson Glow Vignette
                    canvas.drawRect(skia.Rect.MakeWH(w, h), skia.Paint(
                        Color=_skia_color("#160309", 0.92 * shot_d_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))

                    # 1. Master Warning Inequality Header
                    _draw_math_centered(canvas, self.img_alert_fatal, alert_cx, 160.0 * sy, alpha=shot_d_alpha, base_scale=0.60 * sx)

                    # 2. Mechanical Involute Gear Drive Train
                    gear_cy = 530.0 * sy
                    gear_r = 95.0 * sx
                    g_angle = t * 2.2

                    # Dynamic disengagement: Gear 1 pulls away to the left at t=48.5s
                    disengage_p = _smoothstep(48.5, 50.5, t)
                    g1_cx = (820.0 - 150.0 * disengage_p) * sx
                    g2_cx = 1100.0 * sx

                    # Left Gear (First Gear: 2x, Coral) — Disengages and pulls away
                    _draw_involute_gear(canvas, g1_cx, gear_cy, gear_r, 14, g_angle, CORAL, shot_d_alpha, sx)

                    # Right Gear (Second Gear: cos u, Gold) — Spins alone at half speed
                    _draw_involute_gear(canvas, g2_cx, gear_cy, gear_r, 14, -g_angle * (1.0 - 0.5 * disengage_p), GOLD, shot_d_alpha, sx)

                    # Disconnection Vector & Broken Cross Spark Indicator
                    if disengage_p > 0.0:
                        # Dashed Disconnection Link
                        canvas.drawLine(g1_cx + gear_r, gear_cy, g2_cx - gear_r, gear_cy, skia.Paint(
                            Color=_skia_color(CORAL, 0.65 * disengage_p * shot_d_alpha),
                            StrokeWidth=2.4 * sx,
                            PathEffect=skia.DashPathEffect.Make([6.0 * sx, 6.0 * sx], 0.0),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))
                        # Broken Red Cross in gap
                        gap_x = (g1_cx + gear_r + g2_cx - gear_r) / 2.0
                        cross_s = 16.0 * sx
                        canvas.drawLine(gap_x - cross_s, gear_cy - cross_s, gap_x + cross_s, gear_cy + cross_s, skia.Paint(
                            Color=_skia_color(CORAL, 0.98 * disengage_p * shot_d_alpha),
                            StrokeWidth=3.6 * sx,
                            AntiAlias=True,
                        ))
                        canvas.drawLine(gap_x - cross_s, gear_cy + cross_s, gap_x + cross_s, gear_cy - cross_s, skia.Paint(
                            Color=_skia_color(CORAL, 0.98 * disengage_p * shot_d_alpha),
                            StrokeWidth=3.6 * sx,
                            AntiAlias=True,
                        ))

                        # Electric Fracture Sparks
                        for sp_idx in range(6):
                            sp_a = t * 6.5 + sp_idx * (math.pi / 3.0)
                            sp_dist = (20.0 + 12.0 * math.sin(t * 14.0 + sp_idx)) * sx
                            sp_x = gap_x + sp_dist * math.cos(sp_a)
                            sp_y = gear_cy + sp_dist * math.sin(sp_a)
                            canvas.drawCircle(sp_x, sp_y, 2.8 * sx, skia.Paint(
                                Color=_skia_color(AMBER, 0.90 * disengage_p * shot_d_alpha),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))

                        # Sleek Warning Pill Badge floating clearly above the Drive Train
                        tag_y = 335.0 * sy
                        w_text = self.img_alert_missing_desc.width() * 0.44 * sx
                        h_text = self.img_alert_missing_desc.height() * 0.44 * sy
                        pill_w = w_text + 56.0 * sx
                        pill_h = h_text + 18.0 * sy
                        pill_rect = skia.Rect.MakeXYWH(alert_cx - pill_w / 2.0, tag_y - pill_h / 2.0, pill_w, pill_h)
                        canvas.drawRoundRect(pill_rect, 14.0 * sx, 14.0 * sy, skia.Paint(
                            Color=_skia_color(CARD_BG, 0.95 * disengage_p * shot_d_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRoundRect(pill_rect, 14.0 * sx, 14.0 * sy, skia.Paint(
                            Color=_skia_color(CORAL, 0.90 * disengage_p * shot_d_alpha),
                            StrokeWidth=1.8 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))
                        _draw_math_centered(canvas, self.img_alert_missing_desc, alert_cx, tag_y, alpha=disengage_p * shot_d_alpha, base_scale=0.44 * sx)

                    # Gear Labels below hubs
                    _draw_math_centered(canvas, self.img_gear_lbl_inner, g1_cx, gear_cy + gear_r + 40.0 * sy, alpha=shot_d_alpha, base_scale=0.52 * sx)
                    _draw_math_centered(canvas, self.img_gear_lbl_outer, g2_cx, gear_cy + gear_r + 40.0 * sy, alpha=shot_d_alpha, base_scale=0.52 * sx)

                    # 3. Bottom Contrast Alert Card: 1.08 -> 0.54 [-50% Loss]
                    card_w = 900.0 * sx
                    card_h = 100.0 * sy
                    card_y = 810.0 * sy
                    c_rect = skia.Rect.MakeXYWH(alert_cx - card_w / 2.0, card_y - card_h / 2.0, card_w, card_h)

                    canvas.drawRoundRect(c_rect, 16.0 * sx, 16.0 * sy, skia.Paint(
                        Color=_skia_color(CARD_BG, 0.85 * shot_d_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawRoundRect(c_rect, 16.0 * sx, 16.0 * sy, skia.Paint(
                        Color=_skia_color(CORAL, 0.85 * shot_d_alpha),
                        StrokeWidth=2.2 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))

                    _draw_math_centered(canvas, self.img_alert_loss_badge, alert_cx, card_y, alpha=shot_d_alpha, base_scale=0.55 * sx)

                snapshot = self.surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_10(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build and assemble Scene 10: The Crucible of Verification: Analytic vs. Brute-Force at x = 1."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    # Subtitles 121 to 137 span:
    # 00:05:15,640 --> 00:06:10,600 (315.64s to 370.60s, Duration = 54.96s)
    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            scene.add_audio(str(p), start=0.0, trim_start=315.64, trim_end=370.60)

    viewport = Viewport(Scene10VerificationSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_10_DURATION)
    return scene
