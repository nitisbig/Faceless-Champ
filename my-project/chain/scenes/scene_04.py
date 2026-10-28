"""Scene 04: The Cascade to Gear C & The Multiplicative Law (2 x 3 = 6).

Timecode: 00:01:29,200 --> 00:02:11,990 (Duration: 42.79s)
Engine: skia-python (Canvas, Scene, Viewport) + LaTeX MathTex Typography (Computer Modern)

Key Mechanics & Aesthetics:
- Demonstrates the second relative gear ratio: Gear B to Gear C (3:1, x3 rate).
- Poses the cascading intuition question: Gear A (1 Turn) -> Gear C (? Turns).
- Synchronous full-chain mechanical run:
  - Gear A rotates 1 full turn (360° clockwise).
  - Gear B rotates 2 full turns (720° counter-clockwise).
  - Gear C spins 6 full turns (2160° clockwise).
- Real-time turn pill counters with haptic-like tick increments up to 6 turns.
- Numbers slide and merge animation: 2 and 3 collide with a radiant flare, merging into 6.
- The Chain Rule in Disguise reveal:
  Derivative = Rate of Change = Output / Input
  dC/dA = (dC/dB) * (dB/dA) = 3 * 2 = 6
- Zero text clutter: pure physical mechanics and mathematical elegance on pitch black (#000000).
"""

from __future__ import annotations

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

SCENE_04_DURATION: float = 42.79

# High-Contrast Sharp Neon RGB Color Palette
CYAN = "#00F5FF"   # Electric Laser Cyan (Gear A / Input terms)
GOLD = "#FFB800"   # Rich Deep Radiant Gold (Gear B / Multiplier 2)
WHITE = "#FFFFFF"  # Pure Brilliant White (Operators & Specular accents)
MINT = "#05FFA1"   # High-Voltage Neon Mint (Product 6 / Multiplicative factors)
CORAL = "#FF2A6D"  # Laser Neon Coral / Crimson (Gear C / Multiplier 3)


def _make_weighted_tf(path: Path, weight: float = 700.0, fallback: str = "sans-serif") -> skia.Typeface:
    if not path.exists():
        return skia.Typeface(fallback)
    base = skia.Typeface.MakeFromFile(str(path))
    if base is None:
        return skia.Typeface(fallback)
    try:
        tag_wght = int.from_bytes(b"wght", "big")
        coords = skia.FontArguments.VariationPosition.Coordinates()
        coords.append(skia.FontArguments.VariationPosition.Coordinate(tag_wght, float(weight)))
        pos = skia.FontArguments.VariationPosition(coords)
        args = skia.FontArguments()
        args.setVariationDesignPosition(pos)
        clone = base.makeClone(args)
        return clone if clone is not None else base
    except Exception:
        return base


def _draw_letterspaced(target_canvas, text: str, cx: float, y: float, font: skia.Font, paint: skia.Paint, letter_spacing: float = 4.0):
    total_w = 0.0
    advances = []
    for char in text:
        w_char = font.measureText(char)
        advances.append(w_char)
        total_w += w_char + letter_spacing
    total_w -= letter_spacing

    cur_x = cx - total_w * 0.5
    for idx, char in enumerate(text):
        target_canvas.drawString(char, cur_x, y, font, paint)
        cur_x += advances[idx] + letter_spacing


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


def _draw_math_centered(canvas: skia.Canvas, img: skia.Image, cx: float, cy: float, max_w: float | None = None, alpha: float = 1.0, base_scale: float = 0.5):
    """Draw a precompiled LaTeX formula centered at (cx, cy) with bilinear retina filtering."""
    scale = base_scale
    if max_w and (img.width() * scale > max_w):
        scale = max_w / img.width()
    w = img.width() * scale
    h = img.height() * scale
    dst = skia.Rect.MakeXYWH(cx - w * 0.5, cy - h * 0.5, w, h)
    p = skia.Paint(Alphaf=alpha, AntiAlias=True)
    canvas.drawImageRect(img, dst, skia.SamplingOptions(skia.FilterMode.kLinear), p)


def _create_gear_path(r: float, num_teeth: int, tooth_depth: float = 16.0) -> skia.Path:
    """Generate precision spur gear tooth profile with involute-like flanks."""
    path = skia.Path()
    r_root = r - tooth_depth * 0.5
    r_tip = r + tooth_depth * 0.5
    pitch_angle = math.tau / num_teeth

    for i in range(num_teeth):
        a0 = i * pitch_angle
        a1 = a0 + pitch_angle * 0.20
        a2 = a0 + pitch_angle * 0.35
        a3 = a0 + pitch_angle * 0.65
        a4 = a0 + pitch_angle * 0.80
        a5 = a0 + pitch_angle

        p0 = (r_root * math.cos(a0), r_root * math.sin(a0))
        p1 = (r_root * math.cos(a1), r_root * math.sin(a1))
        p2 = (r_tip * math.cos(a2), r_tip * math.sin(a2))
        p3 = (r_tip * math.cos(a3), r_tip * math.sin(a3))
        p4 = (r_root * math.cos(a4), r_root * math.sin(a4))
        p5 = (r_root * math.cos(a5), r_root * math.sin(a5))

        if i == 0:
            path.moveTo(p0[0], p0[1])
        else:
            path.lineTo(p0[0], p0[1])
        path.lineTo(p1[0], p1[1])
        path.lineTo(p2[0], p2[1])
        path.lineTo(p3[0], p3[1])
        path.lineTo(p4[0], p4[1])
        path.lineTo(p5[0], p5[1])

    path.close()
    return path


from dataclasses import dataclass

@dataclass(frozen=True)
class CascadeGearsSource:
    """Multi-shot skia animation source for Scene 04: The Cascade to Gear C & The Multiplicative Law."""

    intrinsic_size: tuple[int, int] = (1920, 1080)
    duration: float = SCENE_04_DURATION
    fingerprint: str = "chain:scene-04:cascade-gears-multiplicative-law:v1"
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

        # Load typography
        assets_dir = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "fonts"
        cg_font_path = assets_dir / "CormorantGaramond[wght].ttf"
        sg_font_path = assets_dir / "SpaceGrotesk[wght].ttf"

        tf_serif_bold = _make_weighted_tf(cg_font_path, 700.0, "serif")
        tf_sans_bold = _make_weighted_tf(sg_font_path, 700.0, "sans-serif")
        tf_sans_med = _make_weighted_tf(sg_font_path, 500.0, "sans-serif")

        # Precompile all LaTeX formulas once at startup (matching euler_scene.py)
        formulas_dict = {
            # Hub marks
            "hub_a": [(r"$A$", CYAN)],
            "hub_b": [(r"$B$", GOLD)],
            "hub_c": [(r"$C$", CORAL)],
            # Rate formulas
            "badge_x2": [(r"$\times 2$", GOLD)],
            "badge_x3": [(r"$\times 3$", CORAL)],
            "rate_ab_badge": [
                (r"$\frac{dB}{dA}$", CYAN),
                ("$=$", WHITE),
                (r"$2$", GOLD),
                (r"$(\times 2)$", MINT),
            ],
            "rate_bc_formula": [
                (r"$\frac{dC}{dB}$", GOLD),
                ("$=$", WHITE),
                (r"$3$", CORAL),
                (r"$(\times 3)$", MINT),
            ],
            # Cascading question
            "question_formula": [
                (r"$\frac{dC}{dA}$", CYAN),
                ("$=$", WHITE),
                (r"$?$", GOLD),
            ],
            # Turn pill labels
            "turn_1": [(r"$1\ \mathrm{Turn}$", CYAN)],
            "turn_2": [(r"$2\ \mathrm{Turns}$", GOLD)],
            "turn_3": [(r"$3\ \mathrm{Turns}$", CORAL)],
            "turn_4": [(r"$4\ \mathrm{Turns}$", CORAL)],
            "turn_5": [(r"$5\ \mathrm{Turns}$", CORAL)],
            "turn_6": [(r"$6\ \mathrm{Turns}$", MINT)],
            # Arithmetic transformation
            "arithmetic_formula": [
                (r"$2$", GOLD),
                (r"$\times$", WHITE),
                (r"$3$", CORAL),
                ("$=$", WHITE),
                (r"$6$", MINT),
            ],
            "slide_2": [(r"$2$", GOLD)],
            "slide_times": [(r"$\times$", WHITE)],
            "slide_3": [(r"$3$", CORAL)],
            "slide_6": [(r"$6$", MINT)],
            "takeaway_rates_multiply": [(r"$\mathbf{Rates\ Multiply}$", WHITE)],
            # Final Chain Rule Definition
            "def_rate": [
                (r"$\mathrm{Derivative}$", CYAN),
                ("$=$", WHITE),
                (r"$\mathrm{Rate\ of\ Change}$", GOLD),
                ("$=$", WHITE),
                (r"$\frac{\Delta \mathrm{Output}}{\Delta \mathrm{Input}}$", MINT),
            ],
            "chain_rule_formula": [
                (r"$\frac{dC}{dA}$", CYAN),
                ("$=$", WHITE),
                (r"$\frac{dC}{dB}$", CORAL),
                (r"$\cdot$", WHITE),
                (r"$\frac{dB}{dA}$", CYAN),
                ("$=$", WHITE),
                (r"$3$", CORAL),
                (r"$\times$", WHITE),
                (r"$2$", GOLD),
                ("$=$", WHITE),
                (r"$6$", MINT),
            ],
            # Transmission node badges
            "delta_a": [(r"$\Delta A$", CYAN)],
            "delta_b": [(r"$\Delta B$", GOLD)],
            "delta_c": [(r"$\Delta C$", CORAL)],
            "badge_total_x6": [(r"$\times 6$", MINT)],
        }

        math_cache: dict[str, skia.Image] = {}
        for name, terms in formulas_dict.items():
            if "def_" in name or "chain_rule" in name:
                f_size = 38
            elif "formula" in name or "takeaway" in name:
                f_size = 36
            elif "slide_6" in name:
                f_size = 54
            elif "slide_" in name:
                f_size = 44
            elif "badge_total" in name:
                f_size = 40
            elif "badge" in name or "question" in name or "delta_" in name:
                f_size = 34
            else:
                f_size = 28
            math_cache[name] = _compose_latex_equation(terms, font_size=f_size)

        # Precompute gear paths in normalized scale
        rA, nA = 240.0 * sx, 48
        rB, nB = 120.0 * sx, 24
        rC, nC = 40.0 * sx, 8

        path_A = _create_gear_path(rA, nA, tooth_depth=16.0 * sx)
        path_B = _create_gear_path(rB, nB, tooth_depth=16.0 * sx)
        path_C = _create_gear_path(rC, nC, tooth_depth=16.0 * sx)

        # Centers
        xA = 800.0 * sx
        yA = 540.0 * sy
        xB = xA + rA + rB
        yB = 540.0 * sy
        xC = xB + rB + rC
        yC = 540.0 * sy

        # Contact Junction points
        x_jab = xA + rA  # 1040
        x_jbc = xB + rB  # 1280

        bg_black = skia.Color4f(0.0, 0.0, 0.0, 1.0)
        c_cyan_rgb = skia.Color4f(0.0, 0.96, 1.0, 1.0)
        c_gold_rgb = skia.Color4f(1.0, 0.72, 0.0, 1.0)
        c_coral_rgb = skia.Color4f(1.0, 0.16, 0.43, 1.0)
        c_mint_rgb = skia.Color4f(0.02, 1.0, 0.63, 1.0)

        class Session:
            def frame(self, t: float) -> Image.Image:
                canvas.clear(bg_black)

                # Global scene fade in
                scene_fade = min(1.0, max(0.0, t / 1.0))

                # -----------------------------------------------------------
                # Timing Phases based on Audio / Subtitles:
                # Shot 04A (0.0s - 11.47s): Gear B drives Gear C (x3 rate)
                # Shot 04B (11.47s - 16.67s): The cascading question: A -> C (? turns)
                # Shot 04C (16.67s - 25.11s): Synchronous full chain run (1 -> 2 -> 6)
                # Shot 04D (25.11s - 30.30s): Numbers slide and merge (Rates Multiply)
                # Shot 04E (30.30s - 42.79s): Chain Rule in Disguise reveal
                # -----------------------------------------------------------

                # Base phase offsets for zero-slip involute tooth meshing
                phi_B = math.pi / nB
                phi_C = (math.pi / nC) - (nB / nC) * phi_B

                # Kinematics variables
                theta_A = 0.0
                theta_B = phi_B
                theta_C = phi_C
                rot_active = False

                # -----------------------------------------------------------
                # Phase 1 Kinematics: Gear B drives Gear C (2.0s - 7.5s)
                # Gear B makes 1 full turn CCW (-360 deg); Gear C makes 3 full turns CW (+1080 deg)
                # -----------------------------------------------------------
                p1_start = 2.0
                p1_dur = 5.5
                if p1_start <= t < 11.47:
                    rot_active = True
                    p1_p = min(1.0, max(0.0, (t - p1_start) / p1_dur))
                    p1_smooth = 0.5 - 0.5 * math.cos(p1_p * math.pi)
                    theta_A = 0.0
                    theta_B = phi_B - math.tau * p1_smooth
                    theta_C = phi_C - (nB / nC) * (theta_B - phi_B)

                # -----------------------------------------------------------
                # Phase 3 Kinematics: Synchronous Full-Chain Run (16.8s - 23.5s)
                # Gear A turns 1 turn CW; Gear B turns 2 turns CCW; Gear C spins 6 turns CW
                # -----------------------------------------------------------
                p3_start = 16.8
                p3_dur = 6.0
                if t >= p3_start:
                    rot_active = True
                    p3_p = min(1.0, max(0.0, (t - p3_start) / p3_dur))
                    p3_smooth = 0.5 - 0.5 * math.cos(p3_p * math.pi)
                    theta_A = math.tau * p3_smooth
                    theta_B = phi_B - 2.0 * theta_A
                    theta_C = phi_C - (nB / nC) * (theta_B - phi_B)

                # Ambient gear opacity (smoothly dissolves to absolute black during Shot 04E definition reveal)
                gear_alpha_factor = max(0.0, 1.0 - (t - 29.5) / 1.5) if t >= 29.5 else 1.0

                # 1. Subtle horizontal mounting rail / alignment axis
                axis_p = skia.Paint(
                    Color=skia.Color4f(0.12, 0.22, 0.35, 0.40 * scene_fade * gear_alpha_factor),
                    StrokeWidth=1.2 * sx,
                    PathEffect=skia.DashPathEffect.Make([8.0 * sx, 6.0 * sx], 0.0),
                    AntiAlias=True,
                )
                canvas.drawLine(xA - rA - 70.0 * sx, yA, xC + rC + 90.0 * sx, yA, axis_p)

                # 2. Draw Helper Function for Individual Gears
                def draw_mechanical_gear(
                    cx: float,
                    cy: float,
                    r: float,
                    num_teeth: int,
                    gear_path: skia.Path,
                    rot_angle: float,
                    color_hex: str,
                    alpha: float,
                    flare: float,
                ):
                    c_rgb = skia.Color4f(
                        int(color_hex[1:3], 16) / 255.0,
                        int(color_hex[3:5], 16) / 255.0,
                        int(color_hex[5:7], 16) / 255.0,
                        1.0,
                    )

                    eff_alpha = alpha * gear_alpha_factor * scene_fade
                    eff_flare = flare * gear_alpha_factor * scene_fade

                    # Atmospheric nebula bloom
                    if eff_flare > 0.04:
                        glow_paint = skia.Paint(
                            Shader=skia.GradientShader.MakeRadial(
                                (cx, cy),
                                r * 1.6,
                                [
                                    skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, 0.38 * eff_flare),
                                    skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, 0.08 * eff_flare),
                                    skia.Color4f(0.0, 0.0, 0.0, 0.0),
                                ],
                                [0.0, 0.55, 1.0],
                            ),
                            AntiAlias=True,
                        )
                        canvas.drawCircle(cx, cy, r * 1.6, glow_paint)

                    canvas.save()
                    canvas.translate(cx, cy)
                    canvas.rotate(math.degrees(rot_angle))

                    # Gear Body Glass Fill (Deep smoked dark core)
                    p_body = skia.Paint(Color=skia.Color4f(0.01, 0.02, 0.04, 0.94 * eff_alpha), AntiAlias=True)
                    canvas.drawPath(gear_path, p_body)

                    # Perimeter Glow Filter
                    glow_intensity = max(eff_alpha * 0.45, eff_flare * 0.90)
                    if glow_intensity > 0.05:
                        p_glow_stroke = skia.Paint(
                            Color=skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, glow_intensity),
                            StrokeWidth=5.5 * sx,
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7.0 * sx),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        canvas.drawPath(gear_path, p_glow_stroke)

                    # Crisp Gear Outer Tooth Outline
                    p_outline = skia.Paint(
                        Color=skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, eff_alpha),
                        StrokeWidth=2.4 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawPath(gear_path, p_outline)

                    # Specular Tooth Crest Highlight
                    p_specular = skia.Paint(
                        Color=skia.Color4f(1.0, 1.0, 1.0, 0.40 * eff_alpha),
                        StrokeWidth=1.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawPath(gear_path, p_specular)

                    # Concentric Lightening Rim Groove
                    p_rim_groove = skia.Paint(
                        Color=skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, 0.40 * eff_alpha),
                        StrokeWidth=1.2 * sx,
                        PathEffect=skia.DashPathEffect.Make([3.0 * sx, 3.0 * sx], 0.0),
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(0, 0, r * 0.82, p_rim_groove)

                    # Dashed Pitch Circle Guide
                    p_pitch = skia.Paint(
                        Color=skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, 0.35 * eff_alpha),
                        StrokeWidth=1.1 * sx,
                        PathEffect=skia.DashPathEffect.Make([5.0 * sx, 5.0 * sx], 0.0),
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(0, 0, r, p_pitch)

                    # Hub concentric structure
                    hub_r = r * 0.34
                    canvas.drawCircle(0, 0, hub_r, p_outline)
                    canvas.drawCircle(0, 0, hub_r * 0.45, p_body)
                    canvas.drawCircle(0, 0, hub_r * 0.45, p_outline)

                    # Center axle micro-crosshair
                    ch_p = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.35 * eff_alpha), StrokeWidth=1.0 * sx, AntiAlias=True)
                    ch_len = 4.5 * sx
                    canvas.drawLine(-ch_len, 0, ch_len, 0, ch_p)
                    canvas.drawLine(0, -ch_len, 0, ch_len, ch_p)

                    # Double-Bevel Truss Spokes
                    num_spokes = 6 if num_teeth >= 24 else 4
                    spoke_half_w = 2.0 * sx
                    for sp in range(num_spokes):
                        sa = sp * (math.tau / num_spokes)
                        csa = math.cos(sa)
                        ssa = math.sin(sa)
                        nx = -ssa * spoke_half_w
                        ny = csa * spoke_half_w
                        r_in = hub_r * 0.98
                        r_out = r * 0.80
                        canvas.drawLine(r_in * csa + nx, r_in * ssa + ny, r_out * csa + nx, r_out * ssa + ny, p_outline)
                        canvas.drawLine(r_in * csa - nx, r_in * ssa - ny, r_out * csa - nx, r_out * ssa - ny, p_outline)

                    # 12 o'clock marker notch & jewel indicator dot
                    notch_p = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, eff_alpha), StrokeWidth=3.0 * sx, AntiAlias=True)
                    canvas.drawLine(0, -r + 8.0 * sx, 0, -r - 14.0 * sx, notch_p)
                    canvas.drawCircle(0, -r - 14.0 * sx, 3.8 * sx, notch_p)

                    canvas.restore()

                # Draw All Three Gears
                # Flare active based on narrative focus:
                flare_b = 1.0 if (t < 11.5 or (16.8 <= t < 25.0)) else 0.4
                flare_c = 1.0 if (t < 11.5 or (16.8 <= t < 25.0)) else 0.4
                flare_a = 1.0 if (11.5 <= t < 25.0) else 0.4

                draw_mechanical_gear(xA, yA, rA, nA, path_A, theta_A, CYAN, 0.95, flare_a)
                draw_mechanical_gear(xB, yB, rB, nB, path_B, theta_B, GOLD, 0.95, flare_b)
                draw_mechanical_gear(xC, yC, rC, nC, path_C, theta_C, CORAL, 0.95, flare_c)

                # Center Hub Insignias (A, B, C)
                _draw_math_centered(canvas, math_cache["hub_a"], xA, yA, alpha=gear_alpha_factor * scene_fade, base_scale=0.58)
                _draw_math_centered(canvas, math_cache["hub_b"], xB, yB, alpha=gear_alpha_factor * scene_fade, base_scale=0.58)
                _draw_math_centered(canvas, math_cache["hub_c"], xC, yC, alpha=gear_alpha_factor * scene_fade, base_scale=0.52)

                # Helper for premium turn badges in pill containers
                def draw_turn_pill(cx: float, cy: float, img: skia.Image, color_rgb: skia.Color4f, alpha: float):
                    if alpha <= 0.01:
                        return
                    pw = img.width() * 0.55 + 26.0 * sx
                    ph = img.height() * 0.55 + 14.0 * sy
                    pill_rect = skia.Rect.MakeXYWH(cx - pw * 0.5, cy - ph * 0.5, pw, ph)
                    pill_r = ph * 0.5
                    # Dark glass fill
                    canvas.drawRoundRect(pill_rect, pill_r, pill_r, skia.Paint(Color=skia.Color4f(0.01, 0.02, 0.05, 0.90 * alpha), AntiAlias=True))
                    # Neon glow outline
                    canvas.drawRoundRect(
                        pill_rect,
                        pill_r,
                        pill_r,
                        skia.Paint(
                            Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.45 * alpha),
                            StrokeWidth=3.5 * sx,
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5.0 * sx),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ),
                    )
                    # Crisp vector border
                    canvas.drawRoundRect(
                        pill_rect,
                        pill_r,
                        pill_r,
                        skia.Paint(
                            Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.95 * alpha),
                            StrokeWidth=1.5 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ),
                    )
                    _draw_math_centered(canvas, img, cx, cy, alpha=alpha, base_scale=0.55)

                # -----------------------------------------------------------
                # SHOT 04A (0.0s - 11.47s): Gear B Drives Gear C (x3 Rate)
                # -----------------------------------------------------------
                if t < 11.5:
                    # Directional rotation vector on Gear B & C during spin (2.0s - 7.5s)
                    if 2.0 <= t <= 8.0:
                        v_alpha = min(1.0, (t - 2.0) / 0.5) * max(0.0, min(1.0, (8.0 - t) / 0.5)) * scene_fade

                        # Gear B: Counter-Clockwise Vector
                        b_vec_r = rB + 26.0 * sx
                        b_vec_rect = skia.Rect.MakeXYWH(xB - b_vec_r, yB - b_vec_r, b_vec_r * 2, b_vec_r * 2)
                        canvas.drawArc(
                            b_vec_rect, -35.0, -95.0, False,
                            skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.85 * v_alpha), StrokeWidth=2.4 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                        )

                        # Gear C: Clockwise Vector
                        c_vec_r = rC + 20.0 * sx
                        c_vec_rect = skia.Rect.MakeXYWH(xC - c_vec_r, yC - c_vec_r, c_vec_r * 2, c_vec_r * 2)
                        canvas.drawArc(
                            c_vec_rect, -150.0, 100.0, False,
                            skia.Paint(Color=skia.Color4f(1.0, 0.16, 0.43, 0.85 * v_alpha), StrokeWidth=2.2 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                        )

                        # Meshing sparks at J_BC
                        rot_p1 = min(1.0, max(0.0, (t - p1_start) / p1_dur))
                        pulse_bc = 0.5 + 0.5 * math.sin(nC * theta_C)
                        mesh_bc_spark = v_alpha * (0.65 + 0.35 * pulse_bc)
                        p_bc_flare = skia.Paint(
                            Color=skia.Color4f(1.0, 0.16, 0.43, 0.80 * mesh_bc_spark),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8.0 * sx),
                            AntiAlias=True,
                        )
                        canvas.drawCircle(x_jbc, yB, 15.0 * sx, p_bc_flare)
                        canvas.drawCircle(x_jbc, yB, 4.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.95 * mesh_bc_spark), AntiAlias=True))

                    # Turn counter on Gear C (counts 1 -> 2 -> 3)
                    if t >= 3.5:
                        c_turn_alpha = min(1.0, (t - 3.5) / 0.5) * scene_fade
                        turn_progress = (t - p1_start) / p1_dur
                        if turn_progress >= 0.85:
                            c_turn_img = math_cache["turn_3"]
                        elif turn_progress >= 0.45:
                            c_turn_img = math_cache["turn_2"]
                        else:
                            c_turn_img = math_cache["turn_1"]
                        draw_turn_pill(xC + 45.0 * sx, yB + rB + 54.0 * sy, c_turn_img, c_coral_rgb, c_turn_alpha)

                    # Rate Formula dC/dB = 3  (x3) (blooms at 7.0s, "Label that rate: times three")
                    if t >= 6.8:
                        fbc_fade = min(1.0, max(0.0, (t - 6.8) / 0.8)) * scene_fade
                        f_cx = x_jbc
                        f_cy = 160.0 * sy

                        # Lens flare nebula
                        f_nebula = skia.Paint(
                            Shader=skia.GradientShader.MakeRadial(
                                (f_cx, f_cy),
                                260.0 * sx,
                                [
                                    skia.Color4f(1.0, 0.16, 0.43, 0.22 * fbc_fade),
                                    skia.Color4f(1.0, 0.72, 0.0, 0.08 * fbc_fade),
                                    skia.Color4f(0.0, 0.0, 0.0, 0.0),
                                ],
                                [0.0, 0.50, 1.0],
                            ),
                            AntiAlias=True,
                        )
                        canvas.drawCircle(f_cx, f_cy, 260.0 * sx, f_nebula)

                        # Golden divider
                        div_y = f_cy + 46.0 * sy
                        canvas.drawLine(
                            f_cx - 120.0 * sx, div_y, f_cx + 120.0 * sx, div_y,
                            skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.55 * fbc_fade), StrokeWidth=1.4 * sx, AntiAlias=True)
                        )
                        _draw_math_centered(canvas, math_cache["rate_bc_formula"], f_cx, f_cy, alpha=fbc_fade, base_scale=0.68)

                # -----------------------------------------------------------
                # SHOT 04B (11.47s - 16.67s): The Cascading Question Posed
                # "Here is the question. When gear A turns once, how many times does gear C turn?"
                # -----------------------------------------------------------
                if 11.5 <= t < 16.8:
                    q_fade = min(1.0, max(0.0, (t - 11.5) / 0.6)) * max(0.0, min(1.0, (16.8 - t) / 0.4)) * scene_fade

                    # Compact rate badges cleanly framed under question formula (inside arc)
                    _draw_math_centered(canvas, math_cache["badge_x2"], 1000.0 * sx, 220.0 * sy, alpha=0.90 * q_fade, base_scale=0.62)
                    _draw_math_centered(canvas, math_cache["badge_x3"], 1160.0 * sx, 220.0 * sy, alpha=0.90 * q_fade, base_scale=0.62)

                    # High arched question arc from Gear A to Gear C over the top
                    arc_q_p = skia.Paint(
                        Color=skia.Color4f(1.0, 0.72, 0.0, 0.85 * q_fade),
                        StrokeWidth=2.4 * sx,
                        PathEffect=skia.DashPathEffect.Make([8.0 * sx, 5.0 * sx], 0.0),
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    q_path = skia.Path()
                    q_path.moveTo(xA, yA - rA - 15.0 * sy)
                    q_path.cubicTo(
                        xA + 120.0 * sx, 50.0 * sy,
                        xC - 60.0 * sx, 50.0 * sy,
                        xC, yC - rC - 15.0 * sy,
                    )
                    canvas.drawPath(q_path, arc_q_p)

                    # Question formula centered at top: dC/dA = ?
                    q_cx = (xA + xC) * 0.5
                    q_cy = 110.0 * sy
                    _draw_math_centered(canvas, math_cache["question_formula"], q_cx, q_cy, alpha=q_fade, base_scale=0.72)

                # -----------------------------------------------------------
                # SHOT 04C (16.67s - 25.11s): Synchronous Full-Chain Run (1 -> 2 -> 6)
                # -----------------------------------------------------------
                if 16.8 <= t < 25.5:
                    run_fade = min(1.0, (t - 16.8) / 0.5) * max(0.0, min(1.0, (25.5 - t) / 0.5)) * scene_fade

                    # Directional rotation vectors during active spin
                    if t < 23.5:
                        # Gear A: Clockwise Vector
                        canvas.drawArc(
                            skia.Rect.MakeXYWH(xA - (rA + 28.0 * sx), yA - (rA + 28.0 * sx), (rA + 28.0 * sx) * 2, (rA + 28.0 * sx) * 2),
                            -145.0, 95.0, False,
                            skia.Paint(Color=skia.Color4f(0.0, 0.96, 1.0, 0.85 * run_fade), StrokeWidth=2.4 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                        )
                        # Gear B: Counter-Clockwise Vector
                        canvas.drawArc(
                            skia.Rect.MakeXYWH(xB - (rB + 26.0 * sx), yB - (rB + 26.0 * sx), (rB + 26.0 * sx) * 2, (rB + 26.0 * sx) * 2),
                            -35.0, -95.0, False,
                            skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.85 * run_fade), StrokeWidth=2.4 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                        )
                        # Gear C: Clockwise Vector
                        canvas.drawArc(
                            skia.Rect.MakeXYWH(xC - (rC + 20.0 * sx), yC - (rC + 20.0 * sx), (rC + 20.0 * sx) * 2, (rC + 20.0 * sx) * 2),
                            -150.0, 100.0, False,
                            skia.Paint(Color=skia.Color4f(1.0, 0.16, 0.43, 0.85 * run_fade), StrokeWidth=2.2 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                        )

                        # Dual meshing sparks
                        p3_ratio = min(1.0, max(0.0, (t - p3_start) / p3_dur))
                        sp_ab = 0.5 + 0.5 * math.sin(nA * theta_A)
                        sp_bc = 0.5 + 0.5 * math.sin(nC * theta_C)

                        canvas.drawCircle(x_jab, yA, 16.0 * sx, skia.Paint(Color=skia.Color4f(0.0, 0.96, 1.0, 0.80 * run_fade * (0.6 + 0.4 * sp_ab)), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8.0 * sx), AntiAlias=True))
                        canvas.drawCircle(x_jbc, yB, 15.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 0.16, 0.43, 0.80 * run_fade * (0.6 + 0.4 * sp_bc)), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8.0 * sx), AntiAlias=True))

                    # Turn badges underneath gears
                    # Gear A: 1 Turn
                    if t >= 18.0:
                        fade_a_pill = min(1.0, (t - 18.0) / 0.5) * run_fade
                        draw_turn_pill(xA, yA + rA + 54.0 * sy, math_cache["turn_1"], c_cyan_rgb, fade_a_pill)

                    # Gear B: 1 Turn -> 2 Turns
                    if t >= 18.0:
                        p3_progress = (t - p3_start) / p3_dur
                        which_b_pill = math_cache["turn_2"] if p3_progress >= 0.50 else math_cache["turn_1"]
                        draw_turn_pill(xB - 25.0 * sx, yB + rB + 54.0 * sy, which_b_pill, c_gold_rgb, run_fade)

                    # Gear C: increments through 1, 2, 3, 4, 5, 6
                    if t >= 17.5:
                        p3_progress = (t - p3_start) / p3_dur
                        turn_idx = min(6, max(1, int(p3_progress * 6.0) + 1))
                        c_pill_key = f"turn_{turn_idx}"
                        pill_col = c_mint_rgb if turn_idx == 6 else c_coral_rgb
                        draw_turn_pill(xC + 45.0 * sx, yB + rB + 54.0 * sy, math_cache[c_pill_key], pill_col, run_fade)

                    # Glowing equation blooms at t >= 22.0s: "Two times three. Six full turns."
                    if t >= 22.0:
                        eq_fade = min(1.0, (t - 22.0) / 0.6) * run_fade
                        eq_cx = (xA + xC) * 0.5
                        eq_cy = 160.0 * sy
                        _draw_math_centered(canvas, math_cache["arithmetic_formula"], eq_cx, eq_cy, alpha=eq_fade, base_scale=0.75)

                # -----------------------------------------------------------
                # SHOT 04D (25.11s - 30.30s): Numbers Slide & Merge (Rates Multiply)
                # -----------------------------------------------------------
                if 25.0 <= t < 30.5:
                    merge_fade = min(1.0, (t - 25.0) / 0.5) * max(0.0, min(1.0, (30.5 - t) / 0.5)) * scene_fade

                    m_cx = 960.0 * sx
                    m_cy = 135.0 * sy

                    # Slide progress: 25.2s -> 27.2s
                    slide_p = min(1.0, max(0.0, (t - 25.2) / 2.0))
                    slide_smooth = 0.5 - 0.5 * math.cos(slide_p * math.pi)

                    if slide_smooth < 1.0:
                        # Gold '2' starts at x=830, slides to 915
                        x2 = 830.0 * sx + (85.0 * sx) * slide_smooth
                        # Coral '3' starts at x=1090, slides to 1005
                        x3 = 1090.0 * sx - (85.0 * sx) * slide_smooth
                        # Operator 'x' centered
                        _draw_math_centered(canvas, math_cache["slide_2"], x2, m_cy, alpha=merge_fade, base_scale=0.85)
                        _draw_math_centered(canvas, math_cache["slide_times"], m_cx, m_cy, alpha=merge_fade, base_scale=0.85)
                        _draw_math_centered(canvas, math_cache["slide_3"], x3, m_cy, alpha=merge_fade, base_scale=0.85)
                    else:
                        # Collision burst flash at t=27.2s
                        flash_t = t - 27.2
                        flash_alpha = max(0.0, 1.0 - flash_t / 0.6)
                        if flash_alpha > 0.01:
                            canvas.drawCircle(
                                m_cx, m_cy, 60.0 * sx * (1.0 + flash_t),
                                skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.85 * flash_alpha), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12.0 * sx), AntiAlias=True)
                            )
                        # Radiant Merged '6'
                        _draw_math_centered(canvas, math_cache["slide_6"], m_cx, m_cy, alpha=merge_fade, base_scale=0.88)

                    # Takeaway below: Rates Multiply (plenty of clearance from 6 and gear teeth)
                    if t >= 27.4:
                        rm_fade = min(1.0, (t - 27.4) / 0.5) * merge_fade
                        _draw_math_centered(canvas, math_cache["takeaway_rates_multiply"], m_cx, 252.0 * sy, alpha=rm_fade, base_scale=0.68)

                # -----------------------------------------------------------
                # SHOT 04E (30.30s - 42.79s): The Chain Rule in Disguise
                # -----------------------------------------------------------
                if t >= 30.0:
                    d_cx = 960.0 * sx

                    # 1. Master Definition Header (30.0s - 32.5s)
                    # Smooth ease-out vertical glide from y=250 to y=230
                    p_def = min(1.0, max(0.0, (t - 30.0) / 0.8))
                    def_ease = 1.0 - (1.0 - p_def) ** 3
                    def_alpha = def_ease * scene_fade
                    d_cy1 = (250.0 - 20.0 * def_ease) * sy

                    # Anamorphic horizontal bloom behind definition
                    nebula_p = skia.Paint(
                        Shader=skia.GradientShader.MakeRadial(
                            (d_cx, d_cy1),
                            420.0 * sx,
                            [
                                skia.Color4f(0.0, 0.96, 1.0, 0.14 * def_alpha),
                                skia.Color4f(1.0, 0.72, 0.0, 0.05 * def_alpha),
                                skia.Color4f(0.0, 0.0, 0.0, 0.0),
                            ],
                            [0.0, 0.50, 1.0],
                        ),
                        AntiAlias=True,
                    )
                    canvas.drawCircle(d_cx, d_cy1, 420.0 * sx, nebula_p)

                    # Definition: Derivative = Rate of Change = Delta Output / Delta Input
                    _draw_math_centered(canvas, math_cache["def_rate"], d_cx, d_cy1, alpha=def_alpha, base_scale=0.68)

                    # 2. Golden Caliper Divider with Rotating Diamond (30.4s - 31.4s)
                    if t >= 30.4:
                        p_div = min(1.0, (t - 30.4) / 0.7)
                        div_ease = 1.0 - (1.0 - p_div) ** 3
                        div_alpha = div_ease * scene_fade
                        div_y = 310.0 * sy
                        half_len = 260.0 * sx * div_ease

                        p_div_line = skia.Paint(
                            Color=skia.Color4f(1.0, 0.72, 0.0, 0.55 * div_alpha),
                            StrokeWidth=1.5 * sx,
                            AntiAlias=True,
                        )
                        canvas.drawLine(d_cx - half_len, div_y, d_cx - 7.0 * sx, div_y, p_div_line)
                        canvas.drawLine(d_cx + 7.0 * sx, div_y, d_cx + half_len, div_y, p_div_line)

                        # Center Diamond with rotation ease
                        canvas.save()
                        canvas.translate(d_cx, div_y)
                        canvas.scale(div_ease, div_ease)
                        canvas.rotate(45.0 * div_ease)
                        canvas.drawRect(
                            skia.Rect.MakeXYWH(-3.5 * sx, -3.5 * sx, 7.0 * sx, 7.0 * sx),
                            skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.90 * div_alpha), AntiAlias=True)
                        )
                        canvas.restore()

                    # 3. Hero Chain Rule Formula with Progressive Laser Wipe (32.5s - 36.5s)
                    d_cy2 = 415.0 * sy
                    if t >= 32.5:
                        p_wipe = min(1.0, max(0.0, (t - 32.5) / 3.3))
                        wipe_ease = 0.5 - 0.5 * math.cos(p_wipe * math.pi)

                        cr_img = math_cache["chain_rule_formula"]
                        cr_scale = 0.72
                        cr_w = cr_img.width() * cr_scale * sx
                        cr_h = cr_img.height() * cr_scale * sy
                        cr_left = d_cx - cr_w * 0.5
                        cr_top = d_cy2 - cr_h * 0.5
                        cr_right = cr_left + cr_w

                        # Soft radial bloom behind hero formula
                        canvas.drawCircle(
                            d_cx, d_cy2, 400.0 * sx,
                            skia.Paint(
                                Shader=skia.GradientShader.MakeRadial(
                                    (d_cx, d_cy2), 400.0 * sx,
                                    [skia.Color4f(0.0, 0.96, 1.0, 0.10 * wipe_ease), skia.Color4f(0.0, 0.0, 0.0, 0.0)],
                                    [0.0, 1.0],
                                ),
                                AntiAlias=True,
                            )
                        )

                        # Progressive Laser Reveal
                        canvas.save()
                        clip_w = cr_w * wipe_ease
                        canvas.clipRect(
                            skia.Rect.MakeLTRB(cr_left - 10.0 * sx, cr_top - 10.0 * sy, cr_left + clip_w, cr_top + cr_h + 10.0 * sy),
                            skia.ClipOp.kIntersect,
                            True
                        )
                        _draw_math_centered(canvas, cr_img, d_cx, d_cy2, alpha=scene_fade, base_scale=0.72)
                        canvas.restore()

                        # Laser vertical cursor bar while wiping
                        if 0.01 < wipe_ease < 0.99:
                            x_laser = cr_left + clip_w
                            p_laser_glow = skia.Paint(
                                Color=skia.Color4f(0.0, 0.96, 1.0, 0.85),
                                StrokeWidth=3.5 * sx,
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0 * sx),
                                AntiAlias=True,
                            )
                            p_laser_core = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.95), StrokeWidth=1.5 * sx, AntiAlias=True)
                            canvas.drawLine(x_laser, cr_top - 4.0 * sy, x_laser, cr_top + cr_h + 4.0 * sy, p_laser_glow)
                            canvas.drawLine(x_laser, cr_top - 4.0 * sy, x_laser, cr_top + cr_h + 4.0 * sy, p_laser_core)
                            canvas.drawCircle(x_laser, d_cy2, 5.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.95), AntiAlias=True))

                        # Climax burst on the digit '6' when laser arrives (35.8s)
                        if t >= 35.8:
                            flash_t = t - 35.8
                            if flash_t <= 0.8:
                                flash_a = max(0.0, 1.0 - flash_t / 0.8)
                                x_six = cr_right - 22.0 * sx
                                canvas.drawCircle(
                                    x_six, d_cy2, 50.0 * sx * (1.0 + flash_t),
                                    skia.Paint(
                                        Color=skia.Color4f(0.02, 1.0, 0.63, 0.75 * flash_a),
                                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10.0 * sx),
                                        AntiAlias=True,
                                    )
                                )
                                canvas.drawCircle(x_six, d_cy2, 12.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.95 * flash_a), AntiAlias=True))

                        # Intermediate Variable Linking Arc: dB denominator to dB numerator
                        if t >= 33.8:
                            link_alpha = min(1.0, (t - 33.8) / 0.6) * scene_fade
                            # dB in dC/dB is at ~28% width, dB in dB/dA is at ~39% width
                            x_db1 = cr_left + cr_w * 0.28
                            y_db1 = d_cy2 + 18.0 * sy
                            x_db2 = cr_left + cr_w * 0.39
                            y_db2 = d_cy2 - 16.0 * sy

                            link_path = skia.Path()
                            link_path.moveTo(x_db1, y_db1)
                            # Downward loop connecting dB1 up to dB2
                            ctrl_x = (x_db1 + x_db2) * 0.5
                            ctrl_y = d_cy2 + 38.0 * sy
                            link_path.cubicTo(x_db1 + 8.0 * sx, ctrl_y, x_db2 - 8.0 * sx, ctrl_y - 12.0 * sy, x_db2, y_db2)

                            p_link_glow = skia.Paint(
                                Color=skia.Color4f(1.0, 0.72, 0.0, 0.50 * link_alpha),
                                StrokeWidth=3.0 * sx,
                                PathEffect=skia.DashPathEffect.Make([4.0 * sx, 3.0 * sx], -(t * 20.0 * sx)),
                                Style=skia.Paint.kStroke_Style,
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.0 * sx),
                                AntiAlias=True,
                            )
                            p_link_core = skia.Paint(
                                Color=skia.Color4f(1.0, 0.88, 0.40, 0.90 * link_alpha),
                                StrokeWidth=1.4 * sx,
                                PathEffect=skia.DashPathEffect.Make([4.0 * sx, 3.0 * sx], -(t * 20.0 * sx)),
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            )
                            canvas.drawPath(link_path, p_link_glow)
                            canvas.drawPath(link_path, p_link_core)

                            # Micro indicator dots at both dB anchors
                            pulse_dot = 0.7 + 0.3 * math.sin(t * 6.0)
                            canvas.drawCircle(x_db1, y_db1, 2.8 * sx, skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.95 * link_alpha * pulse_dot), AntiAlias=True))
                            canvas.drawCircle(x_db2, y_db2, 2.8 * sx, skia.Paint(Color=skia.Color4f(0.0, 0.96, 1.0, 0.95 * link_alpha * pulse_dot), AntiAlias=True))

                    # 4. Secondary Separator Caliper (36.0s - 42.79s)
                    if t >= 36.0:
                        p_sep = min(1.0, (t - 36.0) / 0.6) * scene_fade
                        div2_y = 510.0 * sy
                        canvas.drawLine(
                            d_cx - 180.0 * sx * p_sep, div2_y, d_cx + 180.0 * sx * p_sep, div2_y,
                            skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.35 * p_sep), StrokeWidth=1.2 * sx, AntiAlias=True)
                        )

                    # 5. 3-Stage Holographic Transmission Cascade (36.5s - 42.79s)
                    # "And when one thing drives a second, which drives a third, the rates multiply."
                    if t >= 36.5:
                        cascade_fade = min(1.0, (t - 36.5) / 0.8) * scene_fade

                        node_y = 750.0 * sy
                        nx_A = 580.0 * sx
                        nx_B = 960.0 * sx
                        nx_C = 1340.0 * sx

                        nr_A = 36.0 * sx
                        nr_B = 30.0 * sx
                        nr_C = 24.0 * sx

                        # Staged reveal progression
                        p_node_a = min(1.0, (t - 36.5) / 0.4)
                        p_rail_ab = min(1.0, max(0.0, (t - 36.7) / 0.5))
                        p_node_b = min(1.0, max(0.0, (t - 37.1) / 0.4))
                        p_rail_bc = min(1.0, max(0.0, (t - 37.4) / 0.5))
                        p_node_c = min(1.0, max(0.0, (t - 37.8) / 0.4))
                        p_arc = min(1.0, max(0.0, (t - 38.2) / 0.6))

                        # Helper to render a transmission hub node
                        def draw_transmission_hub(cx: float, cy: float, r: float, hub_img: skia.Image, delta_img: skia.Image, col: skia.Color4f, alpha: float, num_ticks: int):
                            if alpha <= 0.01:
                                return
                            # Radial soft halo
                            canvas.drawCircle(
                                cx, cy, r * 1.8,
                                skia.Paint(
                                    Shader=skia.GradientShader.MakeRadial(
                                        (cx, cy), r * 1.8,
                                        [skia.Color4f(col.fR, col.fG, col.fB, 0.25 * alpha), skia.Color4f(0.0, 0.0, 0.0, 0.0)],
                                        [0.0, 1.0],
                                    ),
                                    AntiAlias=True,
                                )
                            )
                            # Dark glass core
                            canvas.drawCircle(cx, cy, r, skia.Paint(Color=skia.Color4f(0.02, 0.03, 0.06, 0.92 * alpha), AntiAlias=True))
                            # Neon outer border
                            canvas.drawCircle(
                                cx, cy, r,
                                skia.Paint(
                                    Color=skia.Color4f(col.fR, col.fG, col.fB, 0.45 * alpha),
                                    StrokeWidth=3.0 * sx,
                                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0 * sx),
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                )
                            )
                            canvas.drawCircle(cx, cy, r, skia.Paint(Color=skia.Color4f(col.fR, col.fG, col.fB, 0.90 * alpha), StrokeWidth=1.6 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True))
                            # Concentric inner groove
                            canvas.drawCircle(cx, cy, r * 0.72, skia.Paint(Color=skia.Color4f(col.fR, col.fG, col.fB, 0.35 * alpha), StrokeWidth=1.0 * sx, PathEffect=skia.DashPathEffect.Make([2.5 * sx, 2.5 * sx], 0.0), Style=skia.Paint.kStroke_Style, AntiAlias=True))

                            # Micro peripheral gear ticks
                            tick_p = skia.Paint(Color=skia.Color4f(col.fR, col.fG, col.fB, 0.75 * alpha), StrokeWidth=1.5 * sx, AntiAlias=True)
                            for i in range(num_ticks):
                                ang = i * (math.tau / num_ticks) + (t * 0.8 * (1.0 if num_ticks % 2 == 0 else -1.0))
                                cos_a, sin_a = math.cos(ang), math.sin(ang)
                                canvas.drawLine(cx + (r - 2.0 * sx) * cos_a, cy + (r - 2.0 * sx) * sin_a, cx + (r + 4.0 * sx) * cos_a, cy + (r + 4.0 * sx) * sin_a, tick_p)

                            # Center Insignia (A, B, C)
                            _draw_math_centered(canvas, hub_img, cx, cy, alpha=alpha, base_scale=0.50)

                            # Identifier badge below node (Delta A, Delta B, Delta C)
                            draw_turn_pill(cx, cy + r + 24.0 * sy, delta_img, col, alpha)

                        # Draw Hub Nodes
                        draw_transmission_hub(nx_A, node_y, nr_A, math_cache["hub_a"], math_cache["delta_a"], c_cyan_rgb, cascade_fade * p_node_a, 8)
                        draw_transmission_hub(nx_B, node_y, nr_B, math_cache["hub_b"], math_cache["delta_b"], c_gold_rgb, cascade_fade * p_node_b, 6)
                        draw_transmission_hub(nx_C, node_y, nr_C, math_cache["hub_c"], math_cache["delta_c"], c_coral_rgb, cascade_fade * p_node_c, 4)

                        # Helper for directed conduit rails with traveling photon particles
                        def draw_conduit(x1: float, x2: float, cy: float, badge_img: skia.Image, col: skia.Color4f, rail_p: float, speed: float):
                            if rail_p <= 0.01:
                                return
                            w_rail = (x2 - x1) * rail_p
                            x_curr = x1 + w_rail

                            # Dual parallel laser rails
                            p_rail = skia.Paint(Color=skia.Color4f(col.fR, col.fG, col.fB, 0.40 * cascade_fade), StrokeWidth=1.3 * sx, AntiAlias=True)
                            canvas.drawLine(x1, cy - 6.0 * sy, x_curr, cy - 6.0 * sy, p_rail)
                            canvas.drawLine(x1, cy + 6.0 * sy, x_curr, cy + 6.0 * sy, p_rail)

                            # Traveling photon particles along conduit
                            num_photons = 3
                            for i in range(num_photons):
                                p_frac = ((t * speed + i / num_photons) % 1.0)
                                if p_frac <= rail_p:
                                    px = x1 + (x2 - x1) * p_frac
                                    canvas.drawCircle(px, cy, 3.2 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.95 * cascade_fade), AntiAlias=True))
                                    canvas.drawCircle(px, cy, 7.0 * sx, skia.Paint(Color=skia.Color4f(col.fR, col.fG, col.fB, 0.50 * cascade_fade), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.0 * sx), AntiAlias=True))

                            # Floating multiplier badge centered on rail
                            if rail_p >= 0.70:
                                b_alpha = min(1.0, (rail_p - 0.70) / 0.30) * cascade_fade
                                draw_turn_pill((x1 + x2) * 0.5, cy, badge_img, col, b_alpha)

                        # Conduits A -> B and B -> C
                        draw_conduit(nx_A + nr_A + 8.0 * sx, nx_B - nr_B - 8.0 * sx, node_y, math_cache["badge_x2"], c_gold_rgb, p_rail_ab, 0.55)
                        draw_conduit(nx_B + nr_B + 8.0 * sx, nx_C - nr_C - 8.0 * sx, node_y, math_cache["badge_x3"], c_coral_rgb, p_rail_bc, 1.35)

                        # Overarching Master Cascade Arc (Node A -> Node C)
                        if p_arc > 0.01:
                            arc_alpha = p_arc * cascade_fade
                            apex_y = 580.0 * sy

                            # Bezier curve from A to C
                            arc_p0 = (nx_A, node_y - nr_A - 8.0 * sy)
                            arc_p2 = (nx_C, node_y - nr_C - 8.0 * sy)
                            arc_p1 = (nx_B, apex_y)

                            cascade_path = skia.Path()
                            cascade_path.moveTo(arc_p0[0], arc_p0[1])
                            cascade_path.quadTo(arc_p1[0], arc_p1[1], arc_p2[0], arc_p2[1])

                            # Radiant mint glow stroke
                            canvas.drawPath(
                                cascade_path,
                                skia.Paint(
                                    Color=skia.Color4f(0.02, 1.0, 0.63, 0.35 * arc_alpha),
                                    StrokeWidth=3.5 * sx,
                                    PathEffect=skia.DashPathEffect.Make([8.0 * sx, 5.0 * sx], -(t * 30.0 * sx)),
                                    Style=skia.Paint.kStroke_Style,
                                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0 * sx),
                                    AntiAlias=True,
                                )
                            )
                            # Crisp mint core stroke
                            canvas.drawPath(
                                cascade_path,
                                skia.Paint(
                                    Color=skia.Color4f(0.02, 1.0, 0.63, 0.85 * arc_alpha),
                                    StrokeWidth=1.6 * sx,
                                    PathEffect=skia.DashPathEffect.Make([8.0 * sx, 5.0 * sx], -(t * 30.0 * sx)),
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                )
                            )

                            # Animated traveling photon stream along overarching arc
                            for i in range(4):
                                u = ((t * 0.7 + i / 4.0) % 1.0)
                                if u <= p_arc:
                                    ux = (1.0 - u)**2 * arc_p0[0] + 2.0 * (1.0 - u) * u * arc_p1[0] + u**2 * arc_p2[0]
                                    uy = (1.0 - u)**2 * arc_p0[1] + 2.0 * (1.0 - u) * u * arc_p1[1] + u**2 * arc_p2[1]
                                    canvas.drawCircle(ux, uy, 3.5 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.95 * arc_alpha), AntiAlias=True))
                                    canvas.drawCircle(ux, uy, 8.0 * sx, skia.Paint(Color=skia.Color4f(0.02, 1.0, 0.63, 0.60 * arc_alpha), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.0 * sx), AntiAlias=True))

                            # Apex Compound Multiplier Badge: \times 6
                            if t >= 38.6:
                                badge_alpha = min(1.0, (t - 38.6) / 0.5) * cascade_fade
                                draw_turn_pill(nx_B, 595.0 * sy, math_cache["badge_total_x6"], c_mint_rgb, badge_alpha)

                snapshot = surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_04(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build Scene 04: The Cascade to Gear C & The Multiplicative Law (2 x 3 = 6)."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            # Scene 04 starts at 89.20s and ends at 131.99s in the master audio
            scene.add_audio(str(p), start=0.0, trim_start=89.20, trim_end=131.99)

    viewport = Viewport(CascadeGearsSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_04_DURATION)
    return scene
