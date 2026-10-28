r"""Scene 07: The Limit Definition & The Stepping Stone Trick.

Timecode: 00:03:12,160 --> 00:03:46,560 (Duration: 34.40s)
Engine: skia-python (Canvas, Scene, Viewport) + LaTeX MathTex Typography (Computer Modern)

Key Mechanics & Aesthetics:
- Pure pitch-black void canvas (#000000) with zero sentence text clutter.
- NO heading text: the screen is clean, immersive, and void of banner clutter.
- High-contrast saturated neon RGB palette:
  - Cyan #00F5FF (Variable x / Input domain)
  - Gold #FFB800 (Variable u / Stepping stone intermediate)
  - Coral #FF2A6D (Variable y / Output domain)
  - Mint #05FFA1 (Operators / Limits / Tangent line / Energy)
  - White #FFFFFF (Equalities / Axes / High-precision core)
- Shot 07A (0.0s - 12.0s): The Advanced Manim Calculus Limit Graph:
  - Left Stage: Precision coordinate system with glowing curve y = f(x).
    - Anchor point A = (x, y) with glowing amber focus halo.
    - Perturbed point B = (x + Δx, y + Δy) with coral focus halo.
    - Differential secant triangle (Rise Δy over Run Δx) in Coral & Cyan.
    - Extended secant line passing through A and B.
    - Dynamic limit animation (8.7s - 11.5s): Point B slides smoothly down the curve as Δx -> 0.
    - The triangle shrinks to zero, and the secant line rotates smoothly, snapping into the exact Tangent Line in Neon Mint!
  - Right Stage: Formal Limit Equation in Computer Modern MathTex:
    dy/dx = lim_{Δx -> 0} Δy / Δx with slope convergence callout.
- Shot 07B & 07C (12.0s - 28.2s): The Stepping-Stone Algebraic Factorization & Cancellation:
  - Master formula materializes at upper stage: Δy/Δx = Δy/Δu · Δu/Δx.
  - Two Radiant Gold Δu variables slide into place dynamically.
  - Diagonal laser ray links both Δu terms with pulsing concentric aura rings.
  - Dual diagonal neon laser cancellation strikes strike through both terms:
    Δy / \cancel{Δu} · \cancel{Δu} / Δx ≡ Δy / Δx.
- Shot 07D (28.2s - 34.40s): The Dual Manim Function Graphs (Stepping-Stone Bridge):
  - Left Graph: Inner Function u = g(x) with slope tag Δu/Δx.
  - Right Graph: Outer Function y = f(u) with slope tag Δy/Δu.
  - Cybernetic conduit laser connects u_output to u_input.
  - Jumping photon energy bead travels through the chain: x -> u -> y.
  - Pure symbolic summary formula at bottom: x -> u -> y  ≡  x -> y.
"""

from __future__ import annotations

from dataclasses import dataclass
import io
import math
import os
from pathlib import Path
from typing import Sequence

# Configure matplotlib cache directory safely for sandbox
os.environ["MPLCONFIGDIR"] = "/tmp/mpl_cache"

from matplotlib import figure
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import MathTextParser
import numpy as np
from PIL import Image
import skia

from faceless_champ import Canvas, Scene, Viewport

SCENE_07_DURATION: float = 34.40

# High-Contrast Sharp Neon RGB Color Palette
CYAN = "#00F5FF"   # Electric Laser Cyan (Variable x / Machine g)
GOLD = "#FFB800"   # Rich Deep Radiant Gold (Variable u / Stepping stone)
WHITE = "#FFFFFF"  # Pure Brilliant White (Operators / Grid / Ticks)
MINT = "#05FFA1"   # High-Voltage Neon Mint (Limits / Accents / Energy)
CORAL = "#FF2A6D"  # Laser Neon Coral (Variable y / Machine f)


def _render_mathtext_transparent(s: str, color: str = "white", prop: FontProperties | None = None, dpi: int = 200) -> tuple[Image.Image, float]:
    """Render a single LaTeX math token to a transparent RGBA image with TeX depth."""
    parser = MathTextParser("path")
    width, height, depth, _, _ = parser.parse(s, dpi=72, prop=prop)
    fig = figure.Figure(figsize=(width / 72.0, height / 72.0))
    fig.patch.set_alpha(0.0)
    fig.text(0, depth / height, s, fontproperties=prop, color=color)
    buf = io.BytesIO()
    fig.savefig(buf, dpi=dpi, format="png", transparent=True)
    buf.seek(0)
    return Image.open(buf).convert("RGBA"), depth * (dpi / 72.0)


def _compose_latex_equation(terms: list[tuple[str, str]], font_size: float = 32.0, dpi: int = 200, spacing: int = 14) -> skia.Image:
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


def _compose_two_tone_fraction(num_tex: str, num_color: str, den_tex: str, den_color: str, bar_color: str = WHITE, font_size: float = 30.0, dpi: int = 200) -> tuple[skia.Image, float]:
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
    return skia.Image.fromarray(np.array(comp), skia.ColorType.kRGBA_8888_ColorType), depth


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
    if max_w and (img.width() * scale > max_w):
        scale = max_w / img.width()
    w = img.width() * scale
    h = img.height() * scale
    dst = skia.Rect.MakeXYWH(cx - w * 0.5, cy - h * 0.5, w, h)
    p = skia.Paint(Alphaf=alpha, AntiAlias=True)
    canvas.drawImageRect(img, dst, skia.SamplingOptions(skia.FilterMode.kLinear), p)


@dataclass(frozen=True)
class LimitSteppingStoneSource:
    """Animation source for Scene 07: The Limit Definition & The Stepping Stone Trick."""

    intrinsic_size: tuple[int, int] = (1920, 1080)
    duration: float = SCENE_07_DURATION
    fingerprint: str = "chain:scene-07:limit-stepping-stone:v4-manim-graph"
    requirements: tuple[str, ...] = ()

    def frame_key(self, source_time: float) -> int:
        return int(source_time * 60)

    def open(self, size: tuple[int, int]) -> object:
        w, h = size
        sx = w / 1920.0
        sy = h / 1080.0

        info = skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
        surface = skia.Surface.MakeRaster(info)
        canvas = surface.getCanvas()

        # Precompile all LaTeX math equations once at startup
        dpi = 200

        # Shot 07A Equations & Labels
        img_dy_dx_lhs = _compose_latex_equation([
            (r"$\frac{dy}{dx}$", MINT),
            ("$=$", WHITE),
        ], font_size=46.0, dpi=dpi, spacing=16)

        img_lim_op = _compose_latex_equation([
            (r"$\lim_{\Delta x \to 0}$", GOLD),
        ], font_size=44.0, dpi=dpi)

        img_frac_dy_dx, _ = _compose_two_tone_fraction(r"$\Delta y$", CORAL, r"$\Delta x$", CYAN, font_size=42.0, dpi=dpi)

        img_slope_conv = _compose_latex_equation([
            (r"$\frac{\Delta y}{\Delta x}$", GOLD),
            (r"$\longrightarrow$", WHITE),
            (r"$\frac{dy}{dx}$", MINT),
        ], font_size=32.0, dpi=dpi, spacing=18)

        # Graph A Coordinate Labels
        img_lbl_x = _compose_latex_equation([(r"$x$", CYAN)], font_size=28.0, dpi=dpi)
        img_lbl_y = _compose_latex_equation([(r"$y$", CORAL)], font_size=28.0, dpi=dpi)
        img_lbl_u = _compose_latex_equation([(r"$u$", GOLD)], font_size=28.0, dpi=dpi)
        img_lbl_fx = _compose_latex_equation([(r"$y = f(x)$", CYAN)], font_size=26.0, dpi=dpi)

        img_lbl_pt_a = _compose_latex_equation([(r"$A$", GOLD)], font_size=24.0, dpi=dpi)
        img_lbl_pt_b = _compose_latex_equation([(r"$B$", CORAL)], font_size=24.0, dpi=dpi)

        img_lbl_dx_leg = _compose_latex_equation([(r"$\Delta x$", CYAN)], font_size=24.0, dpi=dpi)
        img_lbl_dy_leg = _compose_latex_equation([(r"$\Delta y$", CORAL)], font_size=24.0, dpi=dpi)

        img_lbl_tangent = _compose_latex_equation([(r"$\text{Tangent: } \frac{dy}{dx}$", MINT)], font_size=24.0, dpi=dpi)

        # Shot 07B Equations: The Stepping Stone Factorization
        img_frac_dy_du, _ = _compose_two_tone_fraction(r"$\Delta y$", CORAL, r"$\Delta u$", GOLD, font_size=42.0, dpi=dpi)
        img_frac_du_dx, _ = _compose_two_tone_fraction(r"$\Delta u$", GOLD, r"$\Delta x$", CYAN, font_size=42.0, dpi=dpi)

        img_dot = _compose_latex_equation([(r"$\cdot$", WHITE)], font_size=46.0, dpi=dpi)
        img_equals = _compose_latex_equation([("$=$", WHITE)], font_size=46.0, dpi=dpi)
        img_equiv = _compose_latex_equation([(r"$\equiv$", MINT)], font_size=46.0, dpi=dpi)

        # Shot 07D Graph Labels
        img_lbl_gx = _compose_latex_equation([(r"$u = g(x)$", CYAN)], font_size=24.0, dpi=dpi)
        img_lbl_fu = _compose_latex_equation([(r"$y = f(u)$", CORAL)], font_size=24.0, dpi=dpi)
        img_tag_du_dx = _compose_latex_equation([(r"$\frac{\Delta u}{\Delta x}$", CYAN)], font_size=24.0, dpi=dpi)
        img_tag_dy_du = _compose_latex_equation([(r"$\frac{\Delta y}{\Delta u}$", CORAL)], font_size=24.0, dpi=dpi)

        # Symbolic Equivalence Summary at Bottom
        img_bridge_summary = _compose_latex_equation([
            (r"$x$", CYAN),
            (r"$\longrightarrow$", WHITE),
            (r"$u$", GOLD),
            (r"$\longrightarrow$", WHITE),
            (r"$y$", CORAL),
            (r"$\equiv$", MINT),
            (r"$x \longrightarrow y$", WHITE),
        ], font_size=32.0, dpi=dpi, spacing=20)

        # Graph A Curve Function: smooth convex quadratic
        def f_curve(x_m: float) -> float:
            return 0.35 + 0.55 * x_m + 0.18 * x_m * x_m

        def f_deriv(x_m: float) -> float:
            return 0.55 + 0.36 * x_m

        class Session:
            def frame(self, t: float) -> Image.Image:
                # 1. Pure Pitch-Black Void Canvas (Zero Heading / Zero Clutter)
                canvas.clear(_skia_color("#000000", 1.0))

                # =============================================================
                # SHOT 07A (0.0s - 12.2s): The Advanced Manim Calculus Limit Graph
                # Voice: "Now let us make this precise. The derivative of Y with respect to X is defined as a limit..."
                # =============================================================
                shot_a_alpha = 1.0 - _smoothstep(11.8, 12.8, t)

                if shot_a_alpha > 0.0:
                    # Coordinate System Geometry
                    ox = 180.0 * sx
                    oy = 720.0 * sy
                    scale_xm = 180.0 * sx
                    scale_ym = 145.0 * sy

                    def c2p(xm: float, ym: float) -> tuple[float, float]:
                        return ox + xm * scale_xm, oy - ym * scale_ym

                    # Graph Entrance Fade
                    g_in = _smoothstep(0.5, 2.2, t) * shot_a_alpha

                    if g_in > 0.0:
                        # 1. Coordinate Grid Lines (Subtle Technical Manim Style)
                        p_grid = skia.Paint(
                            Color=_skia_color("#16222E", g_in * 0.70),
                            StrokeWidth=1.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        for gx_m in [1.0, 2.0, 3.0]:
                            g_px, _ = c2p(gx_m, 0.0)
                            canvas.drawLine(g_px, oy, g_px, oy - 460.0 * sy, p_grid)
                        for gy_m in [1.0, 2.0, 3.0]:
                            _, g_py = c2p(0.0, gy_m)
                            canvas.drawLine(ox, g_py, ox + 680.0 * sx, g_py, p_grid)

                        # 2. Main Axes (x & y) with End Ticks and Arrows
                        p_axis = skia.Paint(
                            Color=_skia_color("#4A6075", g_in * 0.90),
                            StrokeWidth=1.8 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        # X-Axis
                        canvas.drawLine(ox - 30.0 * sx, oy, ox + 680.0 * sx, oy, p_axis)
                        # X-Axis Arrowhead
                        canvas.drawLine(ox + 680.0 * sx, oy, ox + 668.0 * sx, oy - 5.0 * sy, p_axis)
                        canvas.drawLine(ox + 680.0 * sx, oy, ox + 668.0 * sx, oy + 5.0 * sy, p_axis)
                        _draw_math_centered(canvas, img_lbl_x, ox + 705.0 * sx, oy, alpha=g_in, base_scale=0.55 * sx)

                        # Y-Axis
                        canvas.drawLine(ox, oy + 30.0 * sy, ox, oy - 460.0 * sy, p_axis)
                        # Y-Axis Arrowhead
                        canvas.drawLine(ox, oy - 460.0 * sy, ox - 5.0 * sx, oy - 448.0 * sy, p_axis)
                        canvas.drawLine(ox, oy - 460.0 * sy, ox + 5.0 * sx, oy - 448.0 * sy, p_axis)
                        _draw_math_centered(canvas, img_lbl_y, ox, oy - 485.0 * sy, alpha=g_in, base_scale=0.55 * sx)

                        # Axis Graduation Ticks
                        p_tick = skia.Paint(Color=_skia_color("#4A6075", g_in * 0.75), StrokeWidth=1.5 * sx, AntiAlias=True)
                        for tm in [1.0, 2.0, 3.0]:
                            tx, _ = c2p(tm, 0.0)
                            canvas.drawLine(tx, oy - 4.0 * sy, tx, oy + 4.0 * sy, p_tick)
                            _, ty = c2p(0.0, tm)
                            canvas.drawLine(ox - 4.0 * sx, ty, ox + 4.0 * sx, ty, p_tick)

                        # 3. Smooth Curved Function: y = f(x)
                        curve_in = _smoothstep(1.5, 3.2, t) * shot_a_alpha
                        if curve_in > 0.0:
                            path_curve = skia.Path()
                            steps = 60
                            for step in range(steps + 1):
                                xm_val = 0.15 + (step / steps) * 3.4
                                ym_val = f_curve(xm_val)
                                px_val, py_val = c2p(xm_val, ym_val)
                                if step == 0:
                                    path_curve.moveTo(px_val, py_val)
                                else:
                                    path_curve.lineTo(px_val, py_val)

                            # Outer Glow Stroke
                            canvas.drawPath(
                                path_curve,
                                skia.Paint(
                                    Color=_skia_color(CYAN, curve_in * 0.20),
                                    StrokeWidth=8.0 * sx,
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                ),
                            )
                            # Inner Stroke
                            canvas.drawPath(
                                path_curve,
                                skia.Paint(
                                    Color=_skia_color(CYAN, curve_in * 0.85),
                                    StrokeWidth=3.0 * sx,
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                ),
                            )
                            # Core Bright Line
                            canvas.drawPath(
                                path_curve,
                                skia.Paint(
                                    Color=_skia_color(WHITE, curve_in * 0.90),
                                    StrokeWidth=1.2 * sx,
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                ),
                            )
                            _draw_math_centered(canvas, img_lbl_fx, ox + 610.0 * sx, oy - 430.0 * sy, alpha=curve_in * 0.90, base_scale=0.55 * sx)

                        # 4. Points A, B and the Dynamic Secant/Tangent Line
                        pts_in = _smoothstep(3.2, 4.8, t) * shot_a_alpha
                        if pts_in > 0.0:
                            xm_A = 1.10
                            ym_A = f_curve(xm_A)
                            px_A, py_A = c2p(xm_A, ym_A)

                            # Dynamic Δx Shrinking Animation (Voice: "as the change in X shrinks towards zero" 8.7s - 11.5s)
                            shrink_p = _smoothstep(8.7, 11.4, t) if t > 8.7 else 0.0
                            dx_val = 1.35 * (1.0 - shrink_p) + 0.02 * shrink_p
                            xm_B = xm_A + dx_val
                            ym_B = f_curve(xm_B)
                            px_B, py_B = c2p(xm_B, ym_B)

                            # Dashed drop lines from A to axes
                            p_drop = skia.Paint(
                                Color=_skia_color(WHITE, pts_in * 0.35),
                                StrokeWidth=1.2 * sx,
                                PathEffect=skia.DashPathEffect.Make([4.0 * sx, 4.0 * sy], 0.0),
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            )
                            canvas.drawLine(px_A, py_A, px_A, oy, p_drop)
                            canvas.drawLine(px_A, py_A, ox, py_A, p_drop)

                            # Dashed drop lines from B to axes (fade out as B converges)
                            p_drop_b = skia.Paint(
                                Color=_skia_color(WHITE, pts_in * 0.30 * (1.0 - shrink_p * 0.8)),
                                StrokeWidth=1.2 * sx,
                                PathEffect=skia.DashPathEffect.Make([4.0 * sx, 4.0 * sy], 0.0),
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            )
                            canvas.drawLine(px_B, py_B, px_B, oy, p_drop_b)
                            canvas.drawLine(px_B, py_B, ox, py_B, p_drop_b)

                            # 5. Differential Secant Triangle (Slope Triangle)
                            tri_alpha = pts_in * (1.0 - shrink_p * 0.95)
                            if tri_alpha > 0.05:
                                corner_x = px_B
                                corner_y = py_A

                                # Shaded interior
                                path_tri = skia.Path()
                                path_tri.moveTo(px_A, py_A)
                                path_tri.lineTo(corner_x, corner_y)
                                path_tri.lineTo(px_B, py_B)
                                path_tri.close()
                                canvas.drawPath(path_tri, skia.Paint(Color=_skia_color(CYAN, tri_alpha * 0.12), Style=skia.Paint.kFill_Style, AntiAlias=True))

                                # Horizontal Leg: Δx (Electric Cyan)
                                p_dx = skia.Paint(Color=_skia_color(CYAN, tri_alpha * 0.95), StrokeWidth=2.2 * sx, AntiAlias=True)
                                canvas.drawLine(px_A, py_A, corner_x, corner_y, p_dx)
                                _draw_math_centered(canvas, img_lbl_dx_leg, (px_A + corner_x) * 0.5, py_A + 16.0 * sy, alpha=tri_alpha, base_scale=0.52 * sx)

                                # Vertical Leg: Δy (Laser Coral)
                                p_dy = skia.Paint(Color=_skia_color(CORAL, tri_alpha * 0.95), StrokeWidth=2.2 * sx, AntiAlias=True)
                                canvas.drawLine(corner_x, corner_y, px_B, py_B, p_dy)
                                _draw_math_centered(canvas, img_lbl_dy_leg, corner_x + 22.0 * sx, (corner_y + py_B) * 0.5, alpha=tri_alpha, base_scale=0.52 * sx)

                            # 6. Secant / Tangent Line
                            # Calculate slope m
                            m_secant = (ym_B - ym_A) / dx_val
                            is_tangent = shrink_p > 0.90
                            line_color = MINT if is_tangent else GOLD

                            # Extended line through A and B
                            x_span_l = 0.70
                            x_span_r = 0.90
                            sec_x1 = xm_A - x_span_l
                            sec_y1 = ym_A - m_secant * x_span_l
                            sec_x2 = xm_B + x_span_r
                            sec_y2 = ym_B + m_secant * x_span_r
                            p_sec1, p_sec2 = c2p(sec_x1, sec_y1), c2p(sec_x2, sec_y2)

                            # Outer Glow for Secant/Tangent
                            glow_w = 6.0 if is_tangent else 4.0
                            canvas.drawLine(
                                p_sec1[0], p_sec1[1], p_sec2[0], p_sec2[1],
                                skia.Paint(Color=_skia_color(line_color, pts_in * 0.35), StrokeWidth=glow_w * sx, AntiAlias=True),
                            )
                            # Core Line
                            canvas.drawLine(
                                p_sec1[0], p_sec1[1], p_sec2[0], p_sec2[1],
                                skia.Paint(Color=_skia_color(WHITE if is_tangent else line_color, pts_in * 0.95), StrokeWidth=2.2 * sx, AntiAlias=True),
                            )

                            # 7. Anchor Dot A (Radiant Gold)
                            canvas.drawCircle(px_A, py_A, 14.0 * sx, skia.Paint(Color=_skia_color(GOLD, pts_in * 0.25), Style=skia.Paint.kStroke_Style, StrokeWidth=3.0 * sx, AntiAlias=True))
                            canvas.drawCircle(px_A, py_A, 6.0 * sx, skia.Paint(Color=_skia_color(GOLD, pts_in), Style=skia.Paint.kFill_Style, AntiAlias=True))
                            canvas.drawCircle(px_A, py_A, 2.5 * sx, skia.Paint(Color=_skia_color(WHITE, pts_in), Style=skia.Paint.kFill_Style, AntiAlias=True))

                            # 8. Perturbed Dot B (Laser Coral)
                            b_alpha = pts_in * (1.0 - shrink_p * 0.9)
                            if b_alpha > 0.05:
                                canvas.drawCircle(px_B, py_B, 14.0 * sx, skia.Paint(Color=_skia_color(CORAL, b_alpha * 0.25), Style=skia.Paint.kStroke_Style, StrokeWidth=3.0 * sx, AntiAlias=True))
                                canvas.drawCircle(px_B, py_B, 6.0 * sx, skia.Paint(Color=_skia_color(CORAL, b_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True))
                                canvas.drawCircle(px_B, py_B, 2.5 * sx, skia.Paint(Color=_skia_color(WHITE, b_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True))

                            # Tangent label badge when snapped
                            if is_tangent:
                                tang_alpha = _smoothstep(0.90, 1.0, shrink_p) * shot_a_alpha
                                _draw_math_centered(canvas, img_lbl_tangent, p_sec2[0] + 50.0 * sx, p_sec2[1] - 15.0 * sy, alpha=tang_alpha, base_scale=0.55 * sx)

                    # =========================================================
                    # Right Stage: Master Limit Formula & Slope Convergence
                    # =========================================================
                    rhs_x = 1380.0 * sx
                    rhs_y = 420.0 * sy

                    # 1. LHS: dy/dx = (appears 2.5s - 4.0s)
                    lhs_alpha = _smoothstep(2.5, 4.0, t) * shot_a_alpha
                    if lhs_alpha > 0.0:
                        _draw_math_centered(canvas, img_dy_dx_lhs, rhs_x - 190.0 * sx, rhs_y, alpha=lhs_alpha, base_scale=0.62 * sx)

                    # 2. Limit operator: lim_{Δx -> 0} (appears 4.4s - 5.8s)
                    lim_alpha = _smoothstep(4.4, 5.8, t) * shot_a_alpha
                    if lim_alpha > 0.0:
                        _draw_math_centered(canvas, img_lim_op, rhs_x, rhs_y, alpha=lim_alpha, base_scale=0.62 * sx)

                    # 3. Difference quotient: Δy / Δx (appears 6.0s - 7.6s)
                    frac_alpha = _smoothstep(6.0, 7.6, t) * shot_a_alpha
                    if frac_alpha > 0.0:
                        _draw_math_centered(canvas, img_frac_dy_dx, rhs_x + 180.0 * sx, rhs_y, alpha=frac_alpha, base_scale=0.62 * sx)

                    # 4. Slope Convergence Callout (secant slope -> tangent derivative)
                    conv_alpha = _smoothstep(7.8, 9.5, t) * shot_a_alpha
                    if conv_alpha > 0.0:
                        _draw_math_centered(canvas, img_slope_conv, rhs_x, rhs_y + 130.0 * sy, alpha=conv_alpha, base_scale=0.56 * sx)

                # =============================================================
                # SHOT 07B & 07C (12.0s - 28.2s): Stepping-Stone Factorization & Cancellation Proof
                # Voice: "Now comes one small trick. We rewrite Delta Y over Delta X as two fractions multiplied together..."
                # =============================================================
                shot_bc_alpha = _smoothstep(12.0, 13.2, t)

                if shot_bc_alpha > 0.0:
                    eq_y = 220.0 * sy

                    # Left base difference quotient: Δy / Δx =
                    lhs_frac_x = 510.0 * sx
                    lhs_eq_x = 610.0 * sx
                    _draw_math_centered(canvas, img_frac_dy_dx, lhs_frac_x, eq_y, alpha=shot_bc_alpha, base_scale=0.62 * sx)
                    _draw_math_centered(canvas, img_equals, lhs_eq_x, eq_y, alpha=shot_bc_alpha, base_scale=0.62 * sx)

                    # Fractional Expansion Coordinates
                    first_frac_x = 750.0 * sx
                    dot_x = 870.0 * sx
                    second_frac_x = 990.0 * sx

                    # Multiplication dot
                    bar_expand = _smoothstep(14.0, 15.5, t)
                    if bar_expand > 0.0:
                        _draw_math_centered(canvas, img_dot, dot_x, eq_y, alpha=bar_expand * shot_bc_alpha, base_scale=0.62 * sx)

                    # Δu insertion animation (Voice: "Delta Y over Delta U times Delta U over Delta X" 17.99s - 20.61s)
                    u_insert_prog = _smoothstep(17.5, 19.5, t)

                    # Δu cancellation opacity modulation
                    cancel_strike_prog = _smoothstep(26.2, 27.4, t)
                    du_alpha_mod = 1.0 - cancel_strike_prog * 0.55

                    if u_insert_prog < 0.99:
                        num1_alpha = _smoothstep(14.8, 16.5, t)
                        den2_alpha = _smoothstep(14.8, 16.5, t)
                        _draw_math_centered(canvas, img_frac_dy_du, first_frac_x, eq_y, alpha=num1_alpha * u_insert_prog * shot_bc_alpha, base_scale=0.62 * sx)
                        _draw_math_centered(canvas, img_frac_du_dx, second_frac_x, eq_y, alpha=den2_alpha * u_insert_prog * shot_bc_alpha, base_scale=0.62 * sx)

                        if 0.01 < u_insert_prog < 0.99:
                            cap_y1 = (eq_y + 42.0 * sy) - 42.0 * (1.0 - u_insert_prog) * sy
                            cap_y2 = (eq_y - 42.0 * sy) + 42.0 * (1.0 - u_insert_prog) * sy
                            canvas.drawCircle(first_frac_x, cap_y1, 8.0 * sx, skia.Paint(Color=_skia_color(GOLD, 0.55), Style=skia.Paint.kFill_Style, AntiAlias=True))
                            canvas.drawCircle(second_frac_x, cap_y2, 8.0 * sx, skia.Paint(Color=_skia_color(GOLD, 0.55), Style=skia.Paint.kFill_Style, AntiAlias=True))
                    else:
                        _draw_math_centered(canvas, img_frac_dy_du, first_frac_x, eq_y, alpha=shot_bc_alpha * du_alpha_mod, base_scale=0.62 * sx)
                        _draw_math_centered(canvas, img_frac_du_dx, second_frac_x, eq_y, alpha=shot_bc_alpha * du_alpha_mod, base_scale=0.62 * sx)

                    # ---------------------------------------------------------
                    # SHOT 07C (20.6s - 28.2s): Diagonal Cancellation Proof
                    # Voice: "is that allowed. Watch the screen. Delta U sits on the top of one fraction and the bottom of the other..."
                    # ---------------------------------------------------------
                    cancel_prep = _smoothstep(20.5, 23.5, t)
                    if cancel_prep > 0.0:
                        u1_pos = (first_frac_x, eq_y + 30.0 * sy)
                        u2_pos = (second_frac_x, eq_y - 30.0 * sy)

                        # Diagonal laser link beam
                        beam_p = skia.Paint(
                            Color=_skia_color(GOLD, cancel_prep * 0.50),
                            StrokeWidth=2.0 * sx,
                            PathEffect=skia.DashPathEffect.Make([6.0 * sx, 4.0 * sy], (t * 26.0 * sx) % (10.0 * sx)),
                            AntiAlias=True,
                        )
                        canvas.drawLine(u1_pos[0], u1_pos[1], u2_pos[0], u2_pos[1], beam_p)

                        # Highlight rings around both Δu terms
                        ring_p = skia.Paint(Color=_skia_color(GOLD, cancel_prep * 0.85), Style=skia.Paint.kStroke_Style, StrokeWidth=1.8 * sx, AntiAlias=True)
                        ring_glow = skia.Paint(Color=_skia_color(GOLD, cancel_prep * 0.25), Style=skia.Paint.kStroke_Style, StrokeWidth=5.0 * sx, AntiAlias=True)
                        canvas.drawCircle(u1_pos[0], u1_pos[1], 24.0 * sx, ring_glow)
                        canvas.drawCircle(u1_pos[0], u1_pos[1], 24.0 * sx, ring_p)
                        canvas.drawCircle(u2_pos[0], u2_pos[1], 24.0 * sx, ring_glow)
                        canvas.drawCircle(u2_pos[0], u2_pos[1], 24.0 * sx, ring_p)

                    # Laser cancellation strike slashes (Voice: "so it cancels, leaving exactly what we started with" 26.4s - 28.5s)
                    if cancel_strike_prog > 0.0:
                        slash_len = 34.0 * cancel_strike_prog * sx
                        slash_glow = skia.Paint(Color=_skia_color(CORAL, 0.55), StrokeWidth=6.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                        slash_core = skia.Paint(Color=_skia_color(WHITE, 0.98), StrokeWidth=2.6 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)

                        # Strike 1 on denominator Δu
                        u1_cx, u1_cy = first_frac_x, eq_y + 30.0 * sy
                        canvas.drawLine(u1_cx - slash_len, u1_cy + slash_len * 0.65, u1_cx + slash_len, u1_cy - slash_len * 0.65, slash_glow)
                        canvas.drawLine(u1_cx - slash_len, u1_cy + slash_len * 0.65, u1_cx + slash_len, u1_cy - slash_len * 0.65, slash_core)

                        # Strike 2 on numerator Δu
                        u2_cx, u2_cy = second_frac_x, eq_y - 30.0 * sy
                        canvas.drawLine(u2_cx - slash_len, u2_cy + slash_len * 0.65, u2_cx + slash_len, u2_cy - slash_len * 0.65, slash_glow)
                        canvas.drawLine(u2_cx - slash_len, u2_cy + slash_len * 0.65, u2_cx + slash_len, u2_cy - slash_len * 0.65, slash_core)

                    # Equivalence Identity: ≡ Δy / Δx (reveals at 27.2s)
                    equiv_alpha = _smoothstep(27.2, 28.4, t)
                    if equiv_alpha > 0.0:
                        _draw_math_centered(canvas, img_equiv, 1130.0 * sx, eq_y, alpha=equiv_alpha, base_scale=0.62 * sx)
                        _draw_math_centered(canvas, img_frac_dy_dx, 1250.0 * sx, eq_y, alpha=equiv_alpha, base_scale=0.62 * sx)

                # -------------------------------------------------------------
                # Caliper Divider Line below equations (y = 360)
                # -------------------------------------------------------------
                caliper_prog = _smoothstep(10.0, 12.0, t)
                if caliper_prog > 0.0:
                    caliper_y = 360.0 * sy
                    cdw = 640.0 * caliper_prog * sx
                    c_paint = skia.Paint(Color=_skia_color(GOLD, caliper_prog * 0.60), StrokeWidth=1.5 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                    canvas.drawLine(960.0 * sx - cdw, caliper_y, 960.0 * sx + cdw, caliper_y, c_paint)

                    # End tick notches
                    canvas.drawLine(960.0 * sx - cdw, caliper_y - 5.0 * sy, 960.0 * sx - cdw, caliper_y + 5.0 * sy, c_paint)
                    canvas.drawLine(960.0 * sx + cdw, caliper_y - 5.0 * sy, 960.0 * sx + cdw, caliper_y + 5.0 * sy, c_paint)

                    # Center rotating diamond
                    dia_size = 5.5 * sx
                    dia_p = skia.Paint(Color=_skia_color(GOLD, caliper_prog * 0.90), Style=skia.Paint.kFill_Style, AntiAlias=True)
                    canvas.save()
                    canvas.translate(960.0 * sx, caliper_y)
                    canvas.rotate(t * 22.0)
                    dia_path = skia.Path()
                    dia_path.moveTo(0, -dia_size)
                    dia_path.lineTo(dia_size, 0)
                    dia_path.lineTo(0, dia_size)
                    dia_path.lineTo(-dia_size, 0)
                    dia_path.close()
                    canvas.drawPath(dia_path, dia_p)
                    canvas.restore()

                # =============================================================
                # SHOT 07D (28.2s - 34.40s): The Dual Manim Function Graphs (The Stepping-Stone Bridge)
                # Voice: "Nothing has changed. We have only added a stepping stone in the middle."
                # =============================================================
                bridge_alpha = _smoothstep(28.0, 29.5, t)

                if bridge_alpha > 0.0:
                    # 1. Left Function Graph: u = g(x)
                    # Origin at (280, 720)
                    g1_ox = 260.0 * sx
                    g1_oy = 710.0 * sy
                    g1_w = 420.0 * sx
                    g1_h = 240.0 * sy

                    p_g_axis = skia.Paint(Color=_skia_color("#3A5065", bridge_alpha * 0.85), StrokeWidth=1.6 * sx, AntiAlias=True)
                    # Graph 1 X-axis (Cyan)
                    canvas.drawLine(g1_ox, g1_oy, g1_ox + g1_w, g1_oy, p_g_axis)
                    _draw_math_centered(canvas, img_lbl_x, g1_ox + g1_w + 20.0 * sx, g1_oy, alpha=bridge_alpha, base_scale=0.52 * sx)

                    # Graph 1 U-axis (Gold)
                    canvas.drawLine(g1_ox, g1_oy, g1_ox, g1_oy - g1_h, p_g_axis)
                    _draw_math_centered(canvas, img_lbl_u, g1_ox, g1_oy - g1_h - 20.0 * sy, alpha=bridge_alpha, base_scale=0.52 * sx)

                    # Graph 1 Curve: u = g(x)
                    path_g = skia.Path()
                    for step in range(35):
                        t_step = step / 34.0
                        cx_val = g1_ox + t_step * (g1_w - 40.0 * sx)
                        # smooth concave/exponential upward curve
                        cy_val = g1_oy - (0.15 + 0.50 * t_step + 0.35 * t_step * t_step) * (g1_h - 40.0 * sy)
                        if step == 0:
                            path_g.moveTo(cx_val, cy_val)
                        else:
                            path_g.lineTo(cx_val, cy_val)

                    canvas.drawPath(path_g, skia.Paint(Color=_skia_color(CYAN, bridge_alpha * 0.25), StrokeWidth=6.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True))
                    canvas.drawPath(path_g, skia.Paint(Color=_skia_color(CYAN, bridge_alpha * 0.90), StrokeWidth=2.2 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True))
                    _draw_math_centered(canvas, img_lbl_gx, g1_ox + 160.0 * sx, g1_oy - g1_h + 30.0 * sy, alpha=bridge_alpha, base_scale=0.50 * sx)
                    _draw_math_centered(canvas, img_tag_du_dx, g1_ox + 310.0 * sx, g1_oy - 165.0 * sy, alpha=bridge_alpha * 0.95, base_scale=0.54 * sx)

                    # Operating Point on Graph 1
                    pt1_x = g1_ox + 0.55 * (g1_w - 40.0 * sx)
                    pt1_y = g1_oy - (0.15 + 0.50 * 0.55 + 0.35 * 0.55 * 0.55) * (g1_h - 40.0 * sy)
                    canvas.drawCircle(pt1_x, pt1_y, 5.0 * sx, skia.Paint(Color=_skia_color(GOLD, bridge_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True))

                    # 2. Right Function Graph: y = f(u)
                    # Origin at (1180, 710)
                    g2_ox = 1180.0 * sx
                    g2_oy = 710.0 * sy
                    g2_w = 420.0 * sx
                    g2_h = 240.0 * sy

                    # Graph 2 U-axis (Gold)
                    canvas.drawLine(g2_ox, g2_oy, g2_ox + g2_w, g2_oy, p_g_axis)
                    _draw_math_centered(canvas, img_lbl_u, g2_ox + g2_w + 20.0 * sx, g2_oy, alpha=bridge_alpha, base_scale=0.52 * sx)

                    # Graph 2 Y-axis (Coral)
                    canvas.drawLine(g2_ox, g2_oy, g2_ox, g2_oy - g2_h, p_g_axis)
                    _draw_math_centered(canvas, img_lbl_y, g2_ox, g2_oy - g2_h - 20.0 * sy, alpha=bridge_alpha, base_scale=0.52 * sx)

                    # Graph 2 Curve: y = f(u)
                    path_f = skia.Path()
                    for step in range(35):
                        t_step = step / 34.0
                        cx_val = g2_ox + t_step * (g2_w - 40.0 * sx)
                        # steeper exponential curve
                        cy_val = g2_oy - (0.10 + 0.45 * t_step + 0.45 * t_step * t_step) * (g2_h - 40.0 * sy)
                        if step == 0:
                            path_f.moveTo(cx_val, cy_val)
                        else:
                            path_f.lineTo(cx_val, cy_val)

                    canvas.drawPath(path_f, skia.Paint(Color=_skia_color(CORAL, bridge_alpha * 0.25), StrokeWidth=6.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True))
                    canvas.drawPath(path_f, skia.Paint(Color=_skia_color(CORAL, bridge_alpha * 0.90), StrokeWidth=2.2 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True))
                    _draw_math_centered(canvas, img_lbl_fu, g2_ox + 160.0 * sx, g2_oy - g2_h + 30.0 * sy, alpha=bridge_alpha, base_scale=0.50 * sx)
                    _draw_math_centered(canvas, img_tag_dy_du, g2_ox + 310.0 * sx, g2_oy - 165.0 * sy, alpha=bridge_alpha * 0.95, base_scale=0.54 * sx)

                    # Operating Point on Graph 2
                    pt2_x = g2_ox + 0.55 * (g2_w - 40.0 * sx)
                    pt2_y = g2_oy - (0.10 + 0.45 * 0.55 + 0.45 * 0.55 * 0.55) * (g2_h - 40.0 * sy)
                    canvas.drawCircle(pt2_x, pt2_y, 5.0 * sx, skia.Paint(Color=_skia_color(CORAL, bridge_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True))

                    # 3. Intermediate Stepping-Stone Conduit linking Graph 1 to Graph 2
                    # Dashed Golden cybernetic bridge connecting output u to input u
                    p_conduit = skia.Paint(
                        Color=_skia_color(GOLD, bridge_alpha * 0.65),
                        StrokeWidth=1.8 * sx,
                        PathEffect=skia.DashPathEffect.Make([6.0 * sx, 4.0 * sy], (t * 22.0 * sx) % (10.0 * sx)),
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    conduit_path = skia.Path()
                    conduit_path.moveTo(pt1_x, pt1_y)
                    conduit_path.cubicTo((pt1_x + g2_ox) * 0.5, pt1_y - 40.0 * sy, (pt1_x + g2_ox) * 0.5, g2_oy + 30.0 * sy, pt2_x, g2_oy)
                    canvas.drawPath(conduit_path, p_conduit)

                    # Central Stepping-Stone Node U
                    node_u_x = (g1_ox + g1_w + g2_ox) * 0.5
                    node_u_y = (pt1_y + g2_oy) * 0.5 - 10.0 * sy
                    stone_w, stone_h = 160.0 * sx, 46.0 * sy
                    rect_u = skia.Rect.MakeXYWH(node_u_x - stone_w * 0.5, node_u_y - stone_h * 0.5, stone_w, stone_h)
                    canvas.drawRoundRect(rect_u, 12.0 * sx, 12.0 * sy, skia.Paint(Color=_skia_color("#1C1406", bridge_alpha * 0.95), Style=skia.Paint.kFill_Style, AntiAlias=True))
                    canvas.drawRoundRect(rect_u, 12.0 * sx, 12.0 * sy, skia.Paint(Color=_skia_color(GOLD, bridge_alpha * 0.85), Style=skia.Paint.kStroke_Style, StrokeWidth=1.8 * sx, AntiAlias=True))
                    _draw_math_centered(canvas, img_lbl_u, node_u_x, node_u_y, alpha=bridge_alpha, base_scale=0.58 * sx)

                    # 4. Animated Jumping Photon Bead through the whole chain
                    jump_cycle = ((t - 28.5) / 2.5) % 1.0
                    if 0.0 <= jump_cycle < 0.40:
                        # Traversing Graph 1: input x -> curve -> u
                        sub_t = jump_cycle / 0.40
                        px_t = g1_ox + sub_t * (pt1_x - g1_ox)
                        py_t = g1_oy - (0.15 + 0.50 * (sub_t * 0.55) + 0.35 * (sub_t * 0.55) ** 2) * (g1_h - 40.0 * sy)
                        canvas.drawCircle(px_t, py_t, 8.0 * sx, skia.Paint(Color=_skia_color(CYAN, 0.40), Style=skia.Paint.kFill_Style, AntiAlias=True))
                        canvas.drawCircle(px_t, py_t, 4.0 * sx, skia.Paint(Color=_skia_color(WHITE, 0.98), Style=skia.Paint.kFill_Style, AntiAlias=True))
                    elif 0.40 <= jump_cycle < 0.65:
                        # Crossing Conduit: pt1 -> Node U -> pt2 input
                        sub_t = (jump_cycle - 0.40) / 0.25
                        px_t = pt1_x * (1.0 - sub_t) + pt2_x * sub_t
                        py_t = pt1_y * (1.0 - sub_t) + g2_oy * sub_t - math.sin(sub_t * math.pi) * 35.0 * sy
                        canvas.drawCircle(px_t, py_t, 8.0 * sx, skia.Paint(Color=_skia_color(GOLD, 0.40), Style=skia.Paint.kFill_Style, AntiAlias=True))
                        canvas.drawCircle(px_t, py_t, 4.0 * sx, skia.Paint(Color=_skia_color(WHITE, 0.98), Style=skia.Paint.kFill_Style, AntiAlias=True))
                    else:
                        # Traversing Graph 2: u -> curve -> y
                        sub_t = (jump_cycle - 0.65) / 0.35
                        px_t = pt2_x + (sub_t - 0.5) * 60.0 * sx
                        py_t = g2_oy * (1.0 - sub_t) + pt2_y * sub_t
                        canvas.drawCircle(px_t, py_t, 8.0 * sx, skia.Paint(Color=_skia_color(CORAL, 0.40), Style=skia.Paint.kFill_Style, AntiAlias=True))
                        canvas.drawCircle(px_t, py_t, 4.0 * sx, skia.Paint(Color=_skia_color(WHITE, 0.98), Style=skia.Paint.kFill_Style, AntiAlias=True))

                    # 5. Overhead Direct Trajectory Chord (x -> y direct)
                    direct_p = skia.Paint(
                        Color=_skia_color(WHITE, bridge_alpha * 0.28),
                        StrokeWidth=1.5 * sx,
                        PathEffect=skia.DashPathEffect.Make([4.0 * sx, 4.0 * sy], 0.0),
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    path_dir = skia.Path()
                    path_dir.moveTo(g1_ox + 40.0 * sx, g1_oy)
                    path_dir.quadTo(node_u_x, 435.0 * sy, g2_ox + g2_w - 40.0 * sx, pt2_y)
                    canvas.drawPath(path_dir, direct_p)

                    # 6. Bottom Master Symbolic Formula: x -> u -> y  ≡  x -> y
                    _draw_math_centered(canvas, img_bridge_summary, 960.0 * sx, 875.0 * sy, alpha=bridge_alpha, base_scale=0.62 * sx)

                snapshot = surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_07(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build and assemble Scene 07: The Limit Definition & The Stepping Stone Trick."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    # Subtitles 74 to 87 span:
    # 00:03:12,160 --> 00:03:46,560 (192.16s to 226.56s, Duration = 34.40s)
    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            scene.add_audio(str(p), start=0.0, trim_start=192.16, trim_end=226.56)

    viewport = Viewport(LimitSteppingStoneSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_07_DURATION)
    return scene
