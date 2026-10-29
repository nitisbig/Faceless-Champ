"""Scene 03: The Three Glowing Gears (Gear A to Gear B).

Timecode: 00:01:07,120 --> 00:01:29,200 (Duration: 22.08s)
Engine: skia-python (Canvas, Scene, Viewport) + LaTeX MathTex Typography (Computer Modern)

Key Mechanics & Aesthetics:
- Precision CAD-grade mechanical spur gears with true involute teeth meshing without slipping or collision.
- Color coding matching euler_scene.py palette:
  - Gear A: Electric Cyan (#68DBE8), R = 240px, 48 teeth
  - Gear B: Warm Gold (#FFC878), R = 120px, 24 teeth (Ratio 2:1)
  - Gear C: Coral Red (#FF5376), R = 40px, 8 teeth (Ratio 3:1 to B, 6:1 to A)
- Synchronized mechanical rotational kinematics:
  - Gear A completes exactly 1 full clockwise turn (360°).
  - Gear B synchronously completes exactly 2 full counter-clockwise turns (720°).
  - Gear C synchronously spins through 6 full turns.
- Glowing circumference sweep arcs tracking revolutions.
- Floating Computer Modern LaTeX formula above junction J_AB:
  dB/dA = 2  (×2)
- Zero text clutter: pure physical and mathematical elegance on pitch black (#000000).
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

SCENE_03_DURATION: float = 22.08

# High-Contrast Sharp Neon RGB Color Palette
CYAN = "#00F5FF"   # Electric Laser Cyan
GOLD = "#FFB800"   # Rich Deep Radiant Gold
WHITE = "#FFFFFF"  # Pure Brilliant White
MINT = "#05FFA1"   # High-Voltage Neon Mint
CORAL = "#FF2A6D"  # Laser Neon Coral / Crimson



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
class ThreeGearsDriveSource:
    """Multi-shot skia animation source for Scene 03 with interlocking gears and Euler-style MathTex."""

    intrinsic_size: tuple[int, int] = (1920, 1080)
    duration: float = SCENE_03_DURATION
    fingerprint: str = "chain:scene-03:three-glowing-gears:v1"
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
            "gear_a_title": [(r"$\mathrm{Gear}\ A$", CYAN)],
            "gear_b_title": [(r"$\mathrm{Gear}\ B$", GOLD)],
            "gear_c_title": [(r"$\mathrm{Gear}\ C$", CORAL)],
            "hub_a": [(r"$A$", CYAN)],
            "hub_b": [(r"$B$", GOLD)],
            "hub_c": [(r"$C$", CORAL)],
            "turn_1": [(r"$1\ \mathrm{Turn}$", CYAN)],
            "turn_2": [(r"$2\ \mathrm{Turns}$", GOLD)],
            "rate_formula": [
                (r"$\frac{dB}{dA}$", CYAN),
                ("$=$", WHITE),
                (r"$2$", GOLD),
                (r"$(\times 2)$", MINT),
            ],
            "rate_badge": [(r"$\mathrm{Rate} = \times 2$", GOLD)],
        }

        math_cache: dict[str, skia.Image] = {}
        for name, terms in formulas_dict.items():
            f_size = 36 if "formula" in name else (30 if "title" in name else 26)
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
        x_jab = xA + rA
        x_jbc = xB + rB

        bg_black = skia.Color4f(0.0, 0.0, 0.0, 1.0)

        class Session:
            def frame(self, t: float) -> Image.Image:
                canvas.clear(bg_black)

                # Global scene fade in
                scene_fade = min(1.0, max(0.0, t / 1.0))

                # -----------------------------------------------------------
                # Timing Milestones based on Audio/Subtitles:
                # 0.0s - 3.85s: "Imagine three gears in a row, glowing against a dark background."
                # 3.85s - 8.69s: "The first gear, call it gear A, meshes with the second, gear B."
                # 8.69s - 11.28s: "Gear B meshes with the third, gear C."
                # 12.0s - 17.0s: Gear A 1 Turn, Gear B 2 Turns
                # 17.0s - 22.08s: "So gear B moves twice as fast... Label that rate on screen: times two."
                # -----------------------------------------------------------

                # Sequential illumination opacities
                # Gear A lights up prominently at 3.85s
                fade_a_active = min(1.0, max(0.40, (t - 2.5) / 1.5)) if t >= 2.5 else 0.35
                fade_a_flare = min(1.0, max(0.0, (t - 3.85) / 1.0)) if t >= 3.85 else 0.0

                # Gear B lights up prominently at 6.0s (meshes with second, gear B)
                fade_b_active = min(1.0, max(0.35, (t - 4.5) / 1.5)) if t >= 4.5 else 0.25
                fade_b_flare = min(1.0, max(0.0, (t - 6.0) / 1.0)) if t >= 6.0 else 0.0

                # Gear C lights up at 8.69s (meshes with third, gear C)
                fade_c_active = min(1.0, max(0.30, (t - 7.5) / 1.5)) if t >= 7.5 else 0.20
                fade_c_flare = min(1.0, max(0.0, (t - 8.69) / 1.0)) if t >= 8.69 else 0.0

                # Contact spark flashes
                spark_ab = max(0.0, 1.0 - abs(t - 6.2) / 0.7) if 5.5 < t < 7.0 else 0.0
                spark_bc = max(0.0, 1.0 - abs(t - 9.0) / 0.7) if 8.3 < t < 9.8 else 0.0

                # -----------------------------------------------------------
                # Rotational Kinematics (Starts at 12.0s, completes at 17.0s)
                # -----------------------------------------------------------
                rot_start = 12.0
                rot_duration = 5.0
                rot_p = min(1.0, max(0.0, (t - rot_start) / rot_duration))
                # Smooth cosine ease-in-out
                rot_smooth = (0.5 - 0.5 * math.cos(rot_p * math.pi)) if rot_p > 0 else 0.0

                # Gear A turns 1 full turn (360 degrees clockwise)
                theta_A = math.tau * rot_smooth

                # Gear B turns 2 full turns (720 degrees counter-clockwise)
                # Initial phase offset pi/nB ensures teeth mesh perfectly into gaps
                theta_B = (math.pi / nB) - 2.0 * theta_A

                # Gear C rolls in sync (6 full turns clockwise)
                theta_C = (math.pi / nC) - (nB / nC) * theta_B

                # 1. Subtle horizontal mounting rail / alignment axis
                axis_p = skia.Paint(
                    Color=skia.Color4f(0.12, 0.22, 0.35, 0.40 * scene_fade),
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

                    # Radial atmospheric bloom glow under active gear
                    if flare > 0.04:
                        glow_paint = skia.Paint(
                            Shader=skia.GradientShader.MakeRadial(
                                (cx, cy),
                                r * 1.6,
                                [
                                    skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, 0.38 * flare * scene_fade),
                                    skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, 0.08 * flare * scene_fade),
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
                    p_body = skia.Paint(Color=skia.Color4f(0.01, 0.02, 0.04, 0.94 * alpha * scene_fade), AntiAlias=True)
                    canvas.drawPath(gear_path, p_body)

                    # Perimeter Glow Filter (Vivid neon saturation wrap)
                    glow_intensity = max(alpha * 0.45, flare * 0.90)
                    if glow_intensity > 0.05:
                        p_glow_stroke = skia.Paint(
                            Color=skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, glow_intensity * scene_fade),
                            StrokeWidth=5.5 * sx,
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 7.0 * sx),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        canvas.drawPath(gear_path, p_glow_stroke)

                    # Crisp Gear Outer Tooth Outline
                    p_outline = skia.Paint(
                        Color=skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, alpha * scene_fade),
                        StrokeWidth=2.4 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawPath(gear_path, p_outline)

                    # Specular Tooth Crest Highlight (Razor-sharp bright core)
                    p_specular = skia.Paint(
                        Color=skia.Color4f(1.0, 1.0, 1.0, 0.40 * alpha * scene_fade),
                        StrokeWidth=1.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawPath(gear_path, p_specular)

                    # Concentric Lightening Rim Groove
                    p_rim_groove = skia.Paint(
                        Color=skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, 0.40 * alpha * scene_fade),
                        StrokeWidth=1.2 * sx,
                        PathEffect=skia.DashPathEffect.Make([3.0 * sx, 3.0 * sx], 0.0),
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(0, 0, r * 0.82, p_rim_groove)

                    # Dashed Pitch Circle Guide
                    p_pitch = skia.Paint(
                        Color=skia.Color4f(c_rgb.fR, c_rgb.fG, c_rgb.fB, 0.35 * alpha * scene_fade),
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
                    ch_p = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.35 * alpha * scene_fade), StrokeWidth=1.0 * sx, AntiAlias=True)
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

                    # 12 o'clock marker notch & jewel indicator dot (locked to gear body)
                    notch_p = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, alpha * scene_fade), StrokeWidth=3.0 * sx, AntiAlias=True)
                    canvas.drawLine(0, -r + 8.0 * sx, 0, -r - 14.0 * sx, notch_p)
                    canvas.drawCircle(0, -r - 14.0 * sx, 3.8 * sx, notch_p)

                    canvas.restore()

                # 3. Draw All Three Gears
                draw_mechanical_gear(xA, yA, rA, nA, path_A, theta_A, CYAN, fade_a_active, fade_a_flare)
                draw_mechanical_gear(xB, yB, rB, nB, path_B, theta_B, GOLD, fade_b_active, fade_b_flare)
                draw_mechanical_gear(xC, yC, rC, nC, path_C, theta_C, CORAL, fade_c_active, fade_c_flare)

                # 4. Draw Center Hub Labels (A, B, C)
                if t >= 3.0:
                    _draw_math_centered(canvas, math_cache["hub_a"], xA, yA, alpha=fade_a_active * scene_fade, base_scale=0.58)
                if t >= 5.0:
                    _draw_math_centered(canvas, math_cache["hub_b"], xB, yB, alpha=fade_b_active * scene_fade, base_scale=0.58)
                if t >= 8.0:
                    _draw_math_centered(canvas, math_cache["hub_c"], xC, yC, alpha=fade_c_active * scene_fade, base_scale=0.52)

                # 5. Draw Gear Titles Floating Above Gears (3.5s - 12.0s, smoothly dissolving before rotation & formula)
                title_fade_out = max(0.0, min(1.0, (12.4 - t) / 0.8)) if t >= 11.6 else 1.0
                if t >= 3.5 and title_fade_out > 0.01:
                    _draw_math_centered(canvas, math_cache["gear_a_title"], xA, yA - rA - 52.0 * sy, alpha=fade_a_flare * title_fade_out * scene_fade, base_scale=0.55)
                if t >= 6.0 and title_fade_out > 0.01:
                    _draw_math_centered(canvas, math_cache["gear_b_title"], xB, yB - rB - 52.0 * sy, alpha=fade_b_flare * title_fade_out * scene_fade, base_scale=0.55)
                if t >= 8.69 and title_fade_out > 0.01:
                    _draw_math_centered(canvas, math_cache["gear_c_title"], xC + 18.0 * sx, yC - rC - 56.0 * sy, alpha=fade_c_flare * title_fade_out * scene_fade, base_scale=0.50)

                # 6. Directional Rotation Motion Vectors (11.5s - 17.5s)
                if 11.5 <= t <= 17.5:
                    arrow_alpha = min(1.0, max(0.0, (t - 11.5) / 0.6)) * max(0.0, min(1.0, (17.5 - t) / 0.6)) * scene_fade

                    # Gear A: Clockwise Direction Vector (upper rim)
                    arc_a_vec_p = skia.Paint(
                        Color=skia.Color4f(0.0, 0.96, 1.0, 0.85 * arrow_alpha),
                        StrokeWidth=2.4 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    vec_a_r = rA + 28.0 * sx
                    vec_a_rect = skia.Rect.MakeXYWH(xA - vec_a_r, yA - vec_a_r, vec_a_r * 2, vec_a_r * 2)
                    canvas.drawArc(vec_a_rect, -145.0, 95.0, False, arc_a_vec_p)
                    # Arrowhead at -50 deg (pointing clockwise: downward/right)
                    ah_ang = math.radians(-50.0)
                    tip_x = xA + vec_a_r * math.cos(ah_ang)
                    tip_y = yA + vec_a_r * math.sin(ah_ang)
                    tan_x = -math.sin(ah_ang)
                    tan_y = math.cos(ah_ang)
                    head_len = 10.0 * sx
                    head_w = 5.0 * sx
                    ah_p = skia.Path()
                    ah_p.moveTo(tip_x, tip_y)
                    ah_p.lineTo(tip_x - tan_x * head_len + (-tan_y) * head_w, tip_y - tan_y * head_len + tan_x * head_w)
                    ah_p.lineTo(tip_x - tan_x * head_len - (-tan_y) * head_w, tip_y - tan_y * head_len - tan_x * head_w)
                    ah_p.close()
                    canvas.drawPath(ah_p, skia.Paint(Color=skia.Color4f(0.0, 0.96, 1.0, 0.90 * arrow_alpha), AntiAlias=True))

                    # Gear B: Counter-Clockwise Direction Vector (upper rim)
                    arc_b_vec_p = skia.Paint(
                        Color=skia.Color4f(1.0, 0.72, 0.0, 0.85 * arrow_alpha),
                        StrokeWidth=2.4 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    vec_b_r = rB + 26.0 * sx
                    vec_b_rect = skia.Rect.MakeXYWH(xB - vec_b_r, yB - vec_b_r, vec_b_r * 2, vec_b_r * 2)
                    canvas.drawArc(vec_b_rect, -35.0, -95.0, False, arc_b_vec_p)
                    # Arrowhead at -130 deg (pointing counter-clockwise: downward/left)
                    bh_ang = math.radians(-130.0)
                    tip_bx = xB + vec_b_r * math.cos(bh_ang)
                    tip_by = yB + vec_b_r * math.sin(bh_ang)
                    btan_x = math.sin(bh_ang)
                    btan_y = -math.cos(bh_ang)
                    bah_p = skia.Path()
                    bah_p.moveTo(tip_bx, tip_by)
                    bah_p.lineTo(tip_bx - btan_x * head_len + (-btan_y) * head_w, tip_by - btan_y * head_len + btan_x * head_w)
                    bah_p.lineTo(tip_bx - btan_x * head_len - (-btan_y) * head_w, tip_by - btan_y * head_len - btan_x * head_w)
                    bah_p.close()
                    canvas.drawPath(bah_p, skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.90 * arrow_alpha), AntiAlias=True))

                # 7. Contact Junction Energy Sparks & Meshing Energy at J_AB
                if 12.0 <= t <= 17.2:
                    rot_energy = min(1.0, (t - 12.0) / 0.5) * max(0.0, min(1.0, (17.2 - t) / 0.4))
                    tooth_pulse = 0.5 + 0.5 * math.sin(nA * theta_A)
                    mesh_spark = rot_energy * (0.65 + 0.35 * tooth_pulse) * scene_fade

                    p_mesh = skia.Paint(
                        Color=skia.Color4f(0.0, 0.96, 1.0, 0.85 * mesh_spark),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10.0 * sx),
                        AntiAlias=True,
                    )
                    canvas.drawCircle(x_jab, yA, 18.0 * sx, p_mesh)

                    p_laser = skia.Paint(
                        Color=skia.Color4f(1.0, 0.85, 0.20, 0.90 * mesh_spark),
                        StrokeWidth=2.2 * sy,
                        AntiAlias=True,
                    )
                    canvas.drawLine(x_jab - 24.0 * sx, yA, x_jab + 24.0 * sx, yA, p_laser)
                    canvas.drawCircle(x_jab, yA, 4.5 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.95 * mesh_spark), AntiAlias=True))

                elif spark_ab > 0.05:
                    p_spark = skia.Paint(
                        Color=skia.Color4f(0.0, 0.96, 1.0, spark_ab * scene_fade),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8.0 * sx),
                        AntiAlias=True,
                    )
                    canvas.drawCircle(x_jab, yA, 16.0 * sx * spark_ab, p_spark)
                    canvas.drawCircle(x_jab, yA, 4.5 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, spark_ab * scene_fade), AntiAlias=True))

                if spark_bc > 0.05:
                    p_spark2 = skia.Paint(
                        Color=skia.Color4f(1.0, 0.16, 0.43, spark_bc * scene_fade),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8.0 * sx),
                        AntiAlias=True,
                    )
                    canvas.drawCircle(x_jbc, yB, 14.0 * sx * spark_bc, p_spark2)
                    canvas.drawCircle(x_jbc, yB, 4.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, spark_bc * scene_fade), AntiAlias=True))

                # 8. Revolution Sweep Arcs during rotation (12.0s - 22.08s)
                if t >= rot_start:
                    sweep_alpha = min(1.0, max(0.0, (t - rot_start) / 0.5)) * scene_fade

                    # Gear A Sweep Arc (Clockwise from top: -90 deg)
                    arc_a_p = skia.Paint(
                        Color=skia.Color4f(0.0, 0.96, 1.0, 0.85 * sweep_alpha),
                        StrokeWidth=3.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    sweep_a_deg = min(360.0, 360.0 * rot_smooth)
                    arc_a_rect = skia.Rect.MakeXYWH(xA - rA - 14.0 * sx, yA - rA - 14.0 * sx, (rA + 14.0 * sx) * 2, (rA + 14.0 * sx) * 2)
                    canvas.drawArc(arc_a_rect, -90.0, sweep_a_deg, False, arc_a_p)

                    # Gear B Sweep Arc (Counter-Clockwise from top: -90 deg)
                    arc_b_p = skia.Paint(
                        Color=skia.Color4f(1.0, 0.72, 0.0, 0.90 * sweep_alpha),
                        StrokeWidth=3.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    sweep_b_deg = min(720.0, 720.0 * rot_smooth)
                    arc_b_rect = skia.Rect.MakeXYWH(xB - rB - 14.0 * sx, yB - rB - 14.0 * sx, (rB + 14.0 * sx) * 2, (rB + 14.0 * sx) * 2)
                    canvas.drawArc(arc_b_rect, -90.0, -sweep_b_deg, False, arc_b_p)

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

                    c_cyan = skia.Color4f(0.0, 0.96, 1.0, 1.0)
                    c_gold = skia.Color4f(1.0, 0.72, 0.0, 1.0)

                    # Over Gear A: 1 Turn badge
                    if rot_smooth >= 0.85:
                        turn_a_fade = min(1.0, (rot_smooth - 0.85) / 0.15) * sweep_alpha
                        draw_turn_pill(xA, yA + rA + 54.0 * sy, math_cache["turn_1"], c_cyan, turn_a_fade)

                    # Over Gear B: Turn badge (1 Turn at 50%, 2 Turns at 100%)
                    if rot_smooth >= 0.40:
                        turn_b_fade = min(1.0, (rot_smooth - 0.40) / 0.15) * sweep_alpha
                        which_turn = math_cache["turn_2"] if rot_smooth >= 0.85 else math_cache["turn_1"]
                        draw_turn_pill(xB, yB + rB + 54.0 * sy, which_turn, c_gold, turn_b_fade)

                # 9. Floating Master LaTeX Rate Formula (dB/dA = 2  (×2))
                # Materializes at t >= 16.2s ("So gear B moves twice as fast... Label that rate: times two.")
                if t >= 16.2:
                    rate_fade = min(1.0, max(0.0, (t - 16.2) / 0.8)) * scene_fade

                    f_cx = x_jab
                    f_cy = 160.0 * sy

                    # Anamorphic horizontal lens flare behind formula
                    f_nebula = skia.Paint(
                        Shader=skia.GradientShader.MakeRadial(
                            (f_cx, f_cy),
                            280.0 * sx,
                            [
                                skia.Color4f(0.0, 0.96, 1.0, 0.22 * rate_fade),
                                skia.Color4f(1.0, 0.72, 0.0, 0.08 * rate_fade),
                                skia.Color4f(0.0, 0.0, 0.0, 0.0),
                            ],
                            [0.0, 0.50, 1.0],
                        ),
                        AntiAlias=True,
                    )
                    canvas.drawCircle(f_cx, f_cy, 280.0 * sx, f_nebula)

                    # Sleek gold divider with diamond center below formula
                    div_y = f_cy + 48.0 * sy
                    p_div = skia.Paint(
                        Color=skia.Color4f(1.0, 0.72, 0.0, 0.55 * rate_fade),
                        StrokeWidth=1.4 * sx,
                        AntiAlias=True,
                    )
                    canvas.drawLine(f_cx - 130.0 * sx, div_y, f_cx + 130.0 * sx, div_y, p_div)
                    # Diamond accent at center
                    p_dia = skia.Path()
                    p_dia.moveTo(f_cx, div_y - 4.5 * sy)
                    p_dia.lineTo(f_cx + 4.5 * sx, div_y)
                    p_dia.lineTo(f_cx, div_y + 4.5 * sy)
                    p_dia.lineTo(f_cx - 4.5 * sx, div_y)
                    p_dia.close()
                    canvas.drawPath(p_dia, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.90 * rate_fade), AntiAlias=True))

                    # Formula in Computer Modern MathTex
                    _draw_math_centered(canvas, math_cache["rate_formula"], f_cx, f_cy, alpha=rate_fade, base_scale=0.68)

                snapshot = surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_03(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build Scene 03: The Three Glowing Gears (Gear A to Gear B)."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            # Scene 03 starts at 67.12s and ends at 89.20s in the master audio
            scene.add_audio(str(p), start=0.0, trim_start=67.12, trim_end=89.20)

    viewport = Viewport(ThreeGearsDriveSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_03_DURATION)
    return scene
