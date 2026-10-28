r"""Scene 09: Decomposing the Formula: Parabola into Sine Wave (y = sin(x^2)).

Timecode: 00:04:48,110 --> 00:05:15,640 (Duration: 27.53s)
Engine: skia-python (Canvas, Scene, Viewport) + LaTeX MathTex Typography (Computer Modern)

Key Mechanics & Aesthetics:
- Pure pitch-black void canvas (#000000) with zero heading banner or subtitle boxes.
- Computer Modern MathTex typography matching euler_scene.py and scene_08.py.
- High-contrast saturated neon RGB palette:
  - Cyan #00F5FF (Input domain x / Parabola / du/dx = 2x / Inner machine)
  - Gold #FFB800 (Intermediate u / Sine wave / dy/du = cos(u) / Outer machine)
  - Coral #FF2A6D (Output y / Composite dy/dx / Total rate)
  - Mint #05FFA1 (Operators / Limits / Tangents / Final Bloom)
  - White #FFFFFF (Equalities / Grid / Axes / Ticks)
- Shot 09A (0.0s - 5.3s): Target Formula Reveal:
  - Master composite function y = sin(x^2) in Computer Modern MathTex with anamorphic laser streak.
  - Sub-badge: Composite Nonlinear Function.
- Shot 09B (5.3s - 13.3s): Dual Split-Screen Cartesian Plots:
  - Left Graph: Parabola u = x^2 in Cyan against dark CAD pane. Header: Inner Machine: u = x^2.
  - Right Graph: Sine wave y = sin(u) in Gold against dark CAD pane. Header: Outer Machine: y = sin(u).
  - Operating points at x=1, u=1 and u=1, y=sin(1) linked by an illuminated conduit bridge with flowing photon beads.
- Shot 09C (13.3s - 27.53s): Tangent Slopes & Algebraic Synthesis:
  - Left graph reveals tangent slope du/dx = 2x.
  - Right graph reveals tangent slope dy/du = cos(u).
  - Upper formula synthesizes: dy/dx = (dy/du) · (du/dx) = cos(u) · 2x ==> dy/dx = 2x cos(x^2).
  - Substitution badge: u ==> x^2 with cyan spark.
  - Climax interrogation hook: Is the formula telling the truth?
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

SCENE_09_DURATION: float = 27.53

# High-Contrast Sharp Neon RGB Color Palette
CYAN = "#00F5FF"    # Electric Laser Cyan (Variable x / Parabola / du/dx)
GOLD = "#FFB800"    # Rich Radiant Gold (Variable u / Sine wave / dy/du)
WHITE = "#FFFFFF"   # Pure Brilliant White (Operators / Grid / Ticks)
MINT = "#05FFA1"    # High-Voltage Neon Mint (Tangent lines / Energy / Bloom)
CORAL = "#FF2A6D"   # Laser Neon Coral (Variable y / dy/dx / Target function)
CARD_BG = "#0b1220"  # Dark Cybernetic Slate Card Background


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
    terms: list[tuple[str, str]],
    font_size: float = 32.0,
    dpi: int = 200,
    spacing: int = 14,
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


def _eval_cubic_bezier(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """Evaluate 1D cubic Bezier polynomial at parameter t in [0, 1]."""
    it = 1.0 - t
    return (
        it * it * it * p0
        + 3.0 * it * it * t * p1
        + 3.0 * it * t * t * p2
        + t * t * t * p3
    )


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

    num_x = (width - img_num.width) // 2
    comp.alpha_composite(img_num, (num_x, 0))

    bar_y = img_num.height + spacing
    draw = Image.new("RGBA", (width, bar_thickness), bar_color)
    comp.paste(draw, (0, bar_y))

    den_x = (width - img_den.width) // 2
    den_y = bar_y + bar_thickness + spacing
    comp.alpha_composite(img_den, (den_x, den_y))

    depth = height - (bar_y + bar_thickness // 2)
    return comp, depth


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
class ParabolaToSineSource:
    """Procedural vector graphics renderer for Scene 09: Parabola into Sine Wave (y = sin(x^2))."""

    intrinsic_size: tuple[int, int] = (1920, 1080)
    duration: float = SCENE_09_DURATION
    fingerprint: str = "chain:scene-09:parabola-to-sine:v1"
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

                # 1. Precompile MathTex Assets
                prop_44 = FontProperties(size=44)
                prop_34 = FontProperties(size=34)
                prop_24 = FontProperties(size=24)
                prop_20 = FontProperties(size=20)
                prop_18 = FontProperties(size=18)

                # Shot 09A: Target Formula Display
                self.img_target_formula = _compose_latex_equation(
                    [
                        (r"y", CORAL, 12),
                        (r"=", WHITE, 14),
                        (r"\sin", GOLD, 2),
                        (r"(", WHITE, 2),
                        (r"x^2", CYAN, 2),
                        (r")", WHITE, 0),
                    ],
                    font_size=44,
                    spacing=12,
                )

                img_badge_target_pil, _ = _render_mathtext_transparent(r"\mathrm{Composite\ Nonlinear\ Function}", MINT, prop_20)
                self.img_badge_target = skia.Image.fromarray(np.array(img_badge_target_pil), skia.ColorType.kRGBA_8888_ColorType)

                # Shot 09B: Dual Graph Headers & Labels
                self.img_hdr_inner = _compose_latex_equation(
                    [
                        (r"\mathbf{\mathrm{Inner\ Machine:}}", CYAN),
                        (r"u = x^2", CYAN),
                    ],
                    font_size=24,
                    spacing=14,
                )

                self.img_hdr_outer = _compose_latex_equation(
                    [
                        (r"\mathbf{\mathrm{Outer\ Machine:}}", GOLD),
                        (r"y = \sin(u)", GOLD),
                    ],
                    font_size=24,
                    spacing=14,
                )

                # Axis Labels
                img_lbl_x_pil, _ = _render_mathtext_transparent(r"x", CYAN, prop_20)
                self.img_lbl_x = skia.Image.fromarray(np.array(img_lbl_x_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_lbl_u_gold_pil, _ = _render_mathtext_transparent(r"u", GOLD, prop_20)
                self.img_lbl_u_gold = skia.Image.fromarray(np.array(img_lbl_u_gold_pil), skia.ColorType.kRGBA_8888_ColorType)

                img_lbl_y_coral_pil, _ = _render_mathtext_transparent(r"y", CORAL, prop_20)
                self.img_lbl_y_coral = skia.Image.fromarray(np.array(img_lbl_y_coral_pil), skia.ColorType.kRGBA_8888_ColorType)

                # Shot 09C: Tangent Slope Badges
                self.img_tag_du_dx = _compose_latex_equation(
                    [
                        (r"\frac{du}{dx}", CYAN),
                        (r"=", WHITE),
                        (r"2x", CYAN),
                    ],
                    font_size=24,
                    spacing=8,
                )

                self.img_tag_dy_du = _compose_latex_equation(
                    [
                        (r"\frac{dy}{du}", GOLD),
                        (r"=", WHITE),
                        (r"\cos(u)", GOLD),
                    ],
                    font_size=24,
                    spacing=8,
                )

                # Step 1 Synthesis: dy/dx = (dy/du) · (du/dx)
                self.img_synth_step1 = _compose_latex_equation(
                    [
                        (r"\frac{dy}{dx}", CORAL),
                        (r"=", WHITE),
                        (r"\frac{dy}{du}", GOLD),
                        (r"\cdot", WHITE),
                        (r"\frac{du}{dx}", CYAN),
                    ],
                    font_size=36,
                    spacing=12,
                )

                # Step 2 Synthesis: dy/dx = cos(u) · 2x
                self.img_synth_step2 = _compose_latex_equation(
                    [
                        (r"\frac{dy}{dx}", CORAL),
                        (r"=", WHITE),
                        (r"\cos(u)", GOLD),
                        (r"\cdot", WHITE),
                        (r"2x", CYAN),
                    ],
                    font_size=38,
                    spacing=12,
                )

                # Substitution Badge: u ==> x^2
                self.img_subst_badge = _compose_latex_equation(
                    [
                        (r"u", GOLD),
                        (r"\Longrightarrow", MINT),
                        (r"x^2", CYAN),
                    ],
                    font_size=24,
                    spacing=10,
                )

                # Step 3 Final Analytic Derivative: dy/dx = 2x cos(x^2)
                self.img_synth_final = _compose_latex_equation(
                    [
                        (r"\frac{dy}{dx}", CORAL, 12),
                        (r"=", WHITE, 14),
                        (r"2x", CYAN, 8),
                        (r"\cos", GOLD, 2),
                        (r"(", WHITE, 2),
                        (r"x^2", CYAN, 2),
                        (r")", WHITE, 0),
                    ],
                    font_size=44,
                    spacing=10,
                )

                # Conduit Bridge Transfer Badge
                self.img_conduit_badge = _compose_latex_equation(
                    [
                        (r"u = 1", GOLD),
                    ],
                    font_size=20,
                    spacing=4,
                )

                # Shot 09C Climax Hook Question Badge
                self.img_hook_question = _compose_latex_equation(
                    [
                        (r"?", CORAL),
                        (r"\mathbf{\mathrm{Is\ the\ formula\ telling\ the\ truth?}}", GOLD),
                        (r"?", CYAN),
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

                # Subtle Cybernetic Void Grid
                grid_paint = skia.Paint(
                    Color=_skia_color(WHITE, 0.022),
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
                # Shot 09A: 0.0s - 5.3s  (Target Formula Display: y = sin(x^2))
                # Shot 09B: 5.3s - 13.3s (Dual Split-Screen Cartesian Plots: Parabola & Sine)
                # Shot 09C: 13.3s - 27.53s (Tangent Slopes, Synthesis, and Hook Question)
                # =========================================================================

                # -------------------------------------------------------------------------
                # UPPER STAGE: TARGET FORMULA & ALGEBRAIC SYNTHESIS
                # -------------------------------------------------------------------------
                # In Shot 09A & early 09B (0.0s - 16.5s): Show y = sin(x^2)
                # In Shot 09C (16.5s - 21.0s): Show dy/dx = cos(u) · 2x
                # In Shot 09C (21.0s - 27.53s): Show dy/dx = 2x cos(x^2)
                upper_y = 190.0 * sy

                if t < 16.5:
                    target_alpha = _smoothstep(0.0, 1.2, t)
                    _draw_math_centered(canvas, self.img_target_formula, 960.0 * sx, upper_y, alpha=target_alpha, base_scale=0.62 * sx)

                    # Anamorphic Laser Streak across baseline
                    streak_p = _smoothstep(0.6, 2.5, t)
                    if streak_p > 0.0:
                        streak_w = 800.0 * sx * streak_p
                        canvas.drawLine(
                            960.0 * sx - streak_w / 2.0, upper_y + 25.0 * sy,
                            960.0 * sx + streak_w / 2.0, upper_y + 25.0 * sy,
                            skia.Paint(
                                Color=_skia_color(MINT, 0.28 * streak_p * (0.8 + 0.2 * math.sin(t * 3.5))),
                                StrokeWidth=2.5 * sy,
                                AntiAlias=True,
                            )
                        )

                    # Sub-badge in early Shot 09A (1.0s - 5.5s)
                    badge_alpha = _smoothstep(1.0, 2.0, t) * (1.0 - _smoothstep(5.0, 6.0, t))
                    if badge_alpha > 0.0:
                        _draw_math_centered(canvas, self.img_badge_target, 960.0 * sx, upper_y + 60.0 * sy, alpha=badge_alpha, base_scale=0.50 * sx)

                elif 16.5 <= t < 21.0:
                    # Step 2: dy/dx = cos(u) · 2x
                    synth1_p = _smoothstep(16.5, 17.8, t)
                    _draw_math_centered(canvas, self.img_synth_step2, 960.0 * sx, upper_y, alpha=synth1_p, base_scale=0.62 * sx)

                else:
                    # Step 3 Final: dy/dx = 2x cos(x^2)
                    final_p = _smoothstep(21.0, 22.2, t)
                    _draw_math_centered(canvas, self.img_synth_final, 960.0 * sx, upper_y, alpha=final_p, base_scale=0.66 * sx)

                    # Neon Mint Bloom & Anamorphic Flare on crystallization
                    bloom_flare = _smoothstep(21.2, 22.8, t) * (1.0 - _smoothstep(26.5, 27.5, t))
                    if bloom_flare > 0.0:
                        streak_w = 1100.0 * sx
                        canvas.drawLine(
                            960.0 * sx - streak_w / 2.0, upper_y,
                            960.0 * sx + streak_w / 2.0, upper_y,
                            skia.Paint(
                                Color=_skia_color(MINT, 0.32 * bloom_flare),
                                StrokeWidth=3.0 * sy,
                                AntiAlias=True,
                            )
                        )

                    # Substitution transition badge (20.5s - 23.5s)
                    subst_alpha = _smoothstep(20.5, 21.2, t) * (1.0 - _smoothstep(23.0, 23.8, t))
                    if subst_alpha > 0.0:
                        _draw_math_centered(canvas, self.img_subst_badge, 960.0 * sx, upper_y + 65.0 * sy, alpha=subst_alpha, base_scale=0.50 * sx)

                # -------------------------------------------------------------------------
                # DUAL CARTESIAN PLOTS (SHOT 09B & SHOT 09C)
                # -------------------------------------------------------------------------
                # Left Graph: Parabola u = x^2 (Cyan)
                # Right Graph: Sine Wave y = sin(u) (Gold)
                # Active from 4.8s to end
                graphs_alpha = _smoothstep(4.8, 6.2, t) * (1.0 - _smoothstep(24.5, 26.0, t) * 0.40)

                if graphs_alpha > 0.0:
                    # =====================================================================
                    # GRAPH 1 (LEFT): PARABOLA u = x^2
                    # =====================================================================
                    g1_cx = 500.0 * sx
                    g1_cy = 640.0 * sy
                    g1_w = 540.0 * sx
                    g1_h = 380.0 * sy
                    g1_rect = skia.Rect.MakeXYWH(g1_cx - g1_w / 2.0, g1_cy - g1_h / 2.0, g1_w, g1_h)

                    # Card Background & Border
                    canvas.drawRoundRect(g1_rect, 16.0 * sx, 16.0 * sy, skia.Paint(
                        Color=_skia_color(CARD_BG, 0.88 * graphs_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawRoundRect(g1_rect, 16.0 * sx, 16.0 * sy, skia.Paint(
                        Color=_skia_color(CYAN, 0.65 * graphs_alpha),
                        StrokeWidth=1.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))

                    # Graph 1 Header
                    _draw_math_centered(canvas, self.img_hdr_inner, g1_cx, g1_cy - g1_h / 2.0 + 35.0 * sy, alpha=graphs_alpha, base_scale=0.52 * sx)

                    # Graph 1 Coordinate Geometry
                    # Domain: x in [-2.0, 2.0], Range: u in [0.0, 4.0]
                    # Origin (x=0, u=0): at center bottom of plot area
                    ox1 = g1_cx
                    oy1 = g1_cy + 130.0 * sy
                    sx1 = 110.0 * sx  # 110px per unit of x (total span 440px)
                    su1 = 52.0 * sy   # 52px per unit of u (total span 208px, well below header)

                    def c2p_1(xv: float, uv: float) -> tuple[float, float]:
                        return ox1 + xv * sx1, oy1 - uv * su1

                    # Plot Gridlines
                    g_line_p = skia.Paint(
                        Color=_skia_color(WHITE, 0.08 * graphs_alpha),
                        StrokeWidth=1.0 * sx,
                        AntiAlias=True,
                    )
                    for tick_x in [-2.0, -1.0, 1.0, 2.0]:
                        px_t, _ = c2p_1(tick_x, 0.0)
                        canvas.drawLine(px_t, oy1, px_t, oy1 - 4.0 * su1, g_line_p)
                    for tick_u in [1.0, 2.0, 3.0, 4.0]:
                        _, py_t = c2p_1(0.0, tick_u)
                        canvas.drawLine(ox1 - 2.0 * sx1, py_t, ox1 + 2.0 * sx1, py_t, g_line_p)

                    # Coordinate Axes (x-axis and u-axis)
                    axis_p = skia.Paint(
                        Color=_skia_color(WHITE, 0.70 * graphs_alpha),
                        StrokeWidth=1.8 * sx,
                        AntiAlias=True,
                    )
                    # Horizontal x-axis
                    canvas.drawLine(ox1 - 2.1 * sx1, oy1, ox1 + 2.1 * sx1, oy1, axis_p)
                    # Vertical u-axis (peaks at 545px, comfortably below header at 482px)
                    canvas.drawLine(ox1, oy1 + 10.0 * sy, ox1, oy1 - 4.15 * su1, axis_p)

                    # Axis Labels
                    _draw_math_centered(canvas, self.img_lbl_x, ox1 + 2.25 * sx1, oy1, alpha=graphs_alpha, base_scale=0.50 * sx)
                    _draw_math_centered(canvas, self.img_lbl_u_gold, ox1 - 18.0 * sx, oy1 - 4.15 * su1, alpha=graphs_alpha, base_scale=0.50 * sx)

                    # Curve: Parabola u = x^2 in Cyan
                    path_para = skia.Path()
                    pts_para = 80
                    for i in range(pts_para + 1):
                        x_val = -1.92 + 3.84 * (i / pts_para)
                        u_val = x_val * x_val
                        px, py = c2p_1(x_val, u_val)
                        if i == 0:
                            path_para.moveTo(px, py)
                        else:
                            path_para.lineTo(px, py)

                    # Parabola Glow Halo & Core
                    canvas.drawPath(path_para, skia.Paint(
                        Color=_skia_color(CYAN, 0.20 * graphs_alpha),
                        StrokeWidth=8.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawPath(path_para, skia.Paint(
                        Color=_skia_color(CYAN, 0.95 * graphs_alpha),
                        StrokeWidth=2.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))

                    # Operating Point: (x0=1, u0=1)
                    op_x1, op_u1 = c2p_1(1.0, 1.0)
                    canvas.drawCircle(op_x1, op_u1, 14.0 * sx, skia.Paint(
                        Color=_skia_color(CYAN, 0.28 * graphs_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawCircle(op_x1, op_u1, 5.5 * sx, skia.Paint(
                        Color=_skia_color(WHITE, 0.98 * graphs_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))

                    # Drop projection lines to axes for (x0=1, u0=1)
                    proj_p = skia.Paint(
                        Color=_skia_color(CYAN, 0.35 * graphs_alpha),
                        StrokeWidth=1.2 * sx,
                        PathEffect=skia.DashPathEffect.Make([4.0 * sx, 4.0 * sy], 0.0),
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(op_x1, op_u1, op_x1, oy1, proj_p)  # drop to x=1
                    canvas.drawLine(op_x1, op_u1, ox1, op_u1, proj_p)  # drop to u=1

                    # Shot 09C: Tangent Slope Line on Parabola (at x0=1, m = 2x = 2)
                    tangent1_alpha = _smoothstep(13.2, 14.5, t) * graphs_alpha
                    if tangent1_alpha > 0.0:
                        t1_start_x, t1_start_u = c2p_1(0.3, 1.0 + 2.0 * (0.3 - 1.0))
                        t1_end_x, t1_end_u = c2p_1(1.7, 1.0 + 2.0 * (1.7 - 1.0))
                        canvas.drawLine(t1_start_x, t1_start_u, t1_end_x, t1_end_u, skia.Paint(
                            Color=_skia_color(CYAN, 0.90 * tangent1_alpha),
                            StrokeWidth=2.2 * sx,
                            AntiAlias=True,
                        ))
                        # Slope Tag Badge: du/dx = 2x
                        _draw_math_centered(canvas, self.img_tag_du_dx, op_x1 - 65.0 * sx, op_u1 - 45.0 * sy, alpha=tangent1_alpha, base_scale=0.52 * sx)

                    # =====================================================================
                    # GRAPH 2 (RIGHT): SINE WAVE y = sin(u)
                    # =====================================================================
                    g2_cx = 1420.0 * sx
                    g2_cy = 640.0 * sy
                    g2_w = 540.0 * sx
                    g2_h = 380.0 * sy
                    g2_rect = skia.Rect.MakeXYWH(g2_cx - g2_w / 2.0, g2_cy - g2_h / 2.0, g2_w, g2_h)

                    # Card Background & Border
                    canvas.drawRoundRect(g2_rect, 16.0 * sx, 16.0 * sy, skia.Paint(
                        Color=_skia_color(CARD_BG, 0.88 * graphs_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawRoundRect(g2_rect, 16.0 * sx, 16.0 * sy, skia.Paint(
                        Color=_skia_color(GOLD, 0.65 * graphs_alpha),
                        StrokeWidth=1.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))

                    # Graph 2 Header
                    _draw_math_centered(canvas, self.img_hdr_outer, g2_cx, g2_cy - g2_h / 2.0 + 35.0 * sy, alpha=graphs_alpha, base_scale=0.52 * sx)

                    # Graph 2 Coordinate Geometry
                    # Domain: u in [0.0, 2*pi approx 6.28], Range: y in [-1.2, 1.2]
                    # Origin (u=0, y=0): at left center of plot area
                    ox2 = g2_cx - 210.0 * sx
                    oy2 = g2_cy + 25.0 * sy
                    su2 = 68.0 * sx   # 68px per unit of u (span 2*pi approx 427px)
                    sy2 = 105.0 * sy  # 105px per unit of y (span 1.2 approx 126px)

                    def c2p_2(uv: float, yv: float) -> tuple[float, float]:
                        return ox2 + uv * su2, oy2 - yv * sy2

                    # Plot Gridlines for Sine Wave
                    for tick_u in [math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0, 2.0 * math.pi]:
                        px_t, _ = c2p_2(tick_u, 0.0)
                        canvas.drawLine(px_t, oy2 - 1.1 * sy2, px_t, oy2 + 1.1 * sy2, g_line_p)
                    for tick_y in [-1.0, 1.0]:
                        _, py_t = c2p_2(0.0, tick_y)
                        canvas.drawLine(ox2, py_t, ox2 + 2.0 * math.pi * su2, py_t, g_line_p)

                    # Coordinate Axes
                    canvas.drawLine(ox2, oy2, ox2 + 2.1 * math.pi * su2, oy2, axis_p)  # Horizontal u-axis
                    canvas.drawLine(ox2, oy2 + 1.2 * sy2, ox2, oy2 - 1.25 * sy2, axis_p)  # Vertical y-axis

                    # Axis Labels
                    _draw_math_centered(canvas, self.img_lbl_u_gold, ox2 + 2.15 * math.pi * su2, oy2 + 18.0 * sy, alpha=graphs_alpha, base_scale=0.50 * sx)
                    _draw_math_centered(canvas, self.img_lbl_y_coral, ox2 - 18.0 * sx, oy2 - 1.25 * sy2, alpha=graphs_alpha, base_scale=0.50 * sx)

                    # Curve: Sine Wave y = sin(u) in Gold
                    path_sine = skia.Path()
                    pts_sine = 100
                    for i in range(pts_sine + 1):
                        u_val = 0.0 + (2.0 * math.pi) * (i / pts_sine)
                        y_val = math.sin(u_val)
                        px, py = c2p_2(u_val, y_val)
                        if i == 0:
                            path_sine.moveTo(px, py)
                        else:
                            path_sine.lineTo(px, py)

                    canvas.drawPath(path_sine, skia.Paint(
                        Color=_skia_color(GOLD, 0.20 * graphs_alpha),
                        StrokeWidth=8.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawPath(path_sine, skia.Paint(
                        Color=_skia_color(GOLD, 0.95 * graphs_alpha),
                        StrokeWidth=2.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))

                    # Operating Point on Sine Wave: (u0=1, y0=sin(1) approx 0.8415)
                    op_u2, op_y2 = c2p_2(1.0, math.sin(1.0))
                    canvas.drawCircle(op_u2, op_y2, 14.0 * sx, skia.Paint(
                        Color=_skia_color(GOLD, 0.28 * graphs_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawCircle(op_u2, op_y2, 5.5 * sx, skia.Paint(
                        Color=_skia_color(WHITE, 0.98 * graphs_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))

                    # Drop projection lines to axes for (u0=1, y0=sin(1))
                    proj2_p = skia.Paint(
                        Color=_skia_color(GOLD, 0.35 * graphs_alpha),
                        StrokeWidth=1.2 * sx,
                        PathEffect=skia.DashPathEffect.Make([4.0 * sx, 4.0 * sy], 0.0),
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(op_u2, op_y2, op_u2, oy2, proj2_p)  # drop to u=1
                    canvas.drawLine(op_u2, op_y2, ox2, op_y2, proj2_p)  # drop to y=sin(1)

                    # Shot 09C: Tangent Slope Line on Sine Wave (at u0=1, m = cos(1) approx 0.5403)
                    tangent2_alpha = _smoothstep(13.8, 15.0, t) * graphs_alpha
                    if tangent2_alpha > 0.0:
                        m2 = math.cos(1.0)
                        t2_start_u, t2_start_y = c2p_2(0.2, math.sin(1.0) + m2 * (0.2 - 1.0))
                        t2_end_u, t2_end_y = c2p_2(1.8, math.sin(1.0) + m2 * (1.8 - 1.0))
                        canvas.drawLine(t2_start_u, t2_start_y, t2_end_u, t2_end_y, skia.Paint(
                            Color=_skia_color(GOLD, 0.90 * tangent2_alpha),
                            StrokeWidth=2.2 * sx,
                            AntiAlias=True,
                        ))
                        # Slope Tag Badge: dy/du = cos(u)
                        _draw_math_centered(canvas, self.img_tag_dy_du, op_u2 + 65.0 * sx, op_y2 - 38.0 * sy, alpha=tangent2_alpha, base_scale=0.52 * sx)

                    # =====================================================================
                    # CYBERNETIC CONDUIT BRIDGE (Linking u output to u input)
                    # =====================================================================
                    # Links Operating Point (op_x1, op_u1) on Parabola to (op_u2, op_y2) on Sine Wave
                    bridge_alpha = _smoothstep(7.5, 9.0, t) * graphs_alpha
                    if bridge_alpha > 0.0:
                        cp1_x = g1_cx + g1_w / 2.0 + 40.0 * sx
                        cp1_y = op_u1 - 25.0 * sy
                        cp2_x = g2_cx - g2_w / 2.0 - 40.0 * sx
                        cp2_y = op_y2 + 35.0 * sy

                        conduit_p = skia.Paint(
                            Color=_skia_color(GOLD, 0.55 * bridge_alpha),
                            StrokeWidth=2.2 * sx,
                            PathEffect=skia.DashPathEffect.Make([6.0 * sx, 6.0 * sy], (t * 30.0) % 24.0),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        path_bridge = skia.Path()
                        path_bridge.moveTo(op_x1, op_u1)
                        path_bridge.cubicTo(cp1_x, cp1_y, cp2_x, cp2_y, op_u2, op_y2)
                        canvas.drawPath(path_bridge, conduit_p)

                        # Flowing photon beads along conduit using exact Bezier evaluation
                        pulse_t = (t * 0.9) % 1.0
                        bx = _eval_cubic_bezier(op_x1, cp1_x, cp2_x, op_u2, pulse_t)
                        by = _eval_cubic_bezier(op_u1, cp1_y, cp2_y, op_y2, pulse_t)
                        canvas.drawCircle(bx, by, 5.5 * sx, skia.Paint(
                            Color=_skia_color(WHITE, 0.95 * bridge_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(bx, by, 14.0 * sx, skia.Paint(
                            Color=_skia_color(MINT, 0.40 * bridge_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                        # Floating Conduit Transfer Badge: u = 1 (active during narration of transfer)
                        conduit_badge_alpha = _smoothstep(8.2, 9.5, t) * (1.0 - _smoothstep(13.2, 14.5, t)) * bridge_alpha
                        if conduit_badge_alpha > 0.0:
                            mid_x = _eval_cubic_bezier(op_x1, cp1_x, cp2_x, op_u2, 0.50)
                            mid_y = _eval_cubic_bezier(op_u1, cp1_y, cp2_y, op_y2, 0.50) - 28.0 * sy
                            b_w = 95.0 * sx
                            b_h = 36.0 * sy
                            b_rect = skia.Rect.MakeXYWH(mid_x - b_w / 2.0, mid_y - b_h / 2.0, b_w, b_h)
                            canvas.drawRoundRect(b_rect, 8.0 * sx, 8.0 * sy, skia.Paint(
                                Color=_skia_color(CARD_BG, 0.92 * conduit_badge_alpha),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))
                            canvas.drawRoundRect(b_rect, 8.0 * sx, 8.0 * sy, skia.Paint(
                                Color=_skia_color(GOLD, 0.75 * conduit_badge_alpha),
                                StrokeWidth=1.2 * sx,
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            ))
                            _draw_math_centered(canvas, self.img_conduit_badge, mid_x, mid_y, alpha=conduit_badge_alpha, base_scale=0.50 * sx)

                # -------------------------------------------------------------------------
                # SHOT 09C CLIMAX: HOOK QUESTION CARD (24.0s - 27.53s)
                # -------------------------------------------------------------------------
                # "But is the formula telling the truth?"
                hook_alpha = _smoothstep(24.2, 25.5, t)
                if hook_alpha > 0.0:
                    hook_cy = 900.0 * sy
                    card_w = 760.0 * sx
                    card_h = 75.0 * sy
                    hook_rect = skia.Rect.MakeXYWH(960.0 * sx - card_w / 2.0, hook_cy - card_h / 2.0, card_w, card_h)

                    # Interrogation Card Background
                    canvas.drawRoundRect(hook_rect, 14.0 * sx, 14.0 * sy, skia.Paint(
                        Color=_skia_color(CARD_BG, 0.92 * hook_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    # Pulsing Neon Border
                    pulse_val = 0.70 + 0.30 * math.sin(t * 8.0)
                    canvas.drawRoundRect(hook_rect, 14.0 * sx, 14.0 * sy, skia.Paint(
                        Color=_skia_color(GOLD, pulse_val * hook_alpha),
                        StrokeWidth=1.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))

                    # Question Badge Text
                    _draw_math_centered(canvas, self.img_hook_question, 960.0 * sx, hook_cy, alpha=hook_alpha, base_scale=0.55 * sx)

                snapshot = surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_09(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build and assemble Scene 09: Decomposing the Formula: Parabola into Sine Wave."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    # Subtitles 110 to 120 span:
    # 00:04:48,110 --> 00:05:15,640 (288.11s to 315.64s, Duration = 27.53s)
    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            scene.add_audio(str(p), start=0.0, trim_start=288.11, trim_end=315.64)

    viewport = Viewport(ParabolaToSineSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_09_DURATION)
    return scene
