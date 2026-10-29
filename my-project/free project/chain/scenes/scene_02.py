"""Scene 02: Real-World Rates & The 7-Minute Roadmap.

Timecode: 00:00:25,990 --> 00:01:07,120 (Duration: 41.13s)
Engine: skia-python (Canvas, Scene, Viewport) + LaTeX MathTex Typography (Computer Modern)

Key Improvements:
- Text clutter eliminated: bulky HUD containers, paragraphs, and redundant slogans removed.
- Symbolic mathematical markers: angle arc θ, height caliper h, velocity vector v, axis symbols t and B, divergence caliper ΔB.
- Formulas rendered with true LaTeX MathTex in Computer Modern, matching euler_scene.py:
  - Electric Cyan: #68DBE8
  - Warm Gold: #FFC878
  - Pure White: #FFFFFF
  - Light Mint/Emerald: #4EEDB2
- Responsive scaling and sub-pixel antialiased rasterization for razor-sharp visual fidelity.
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

SCENE_02_DURATION: float = 41.13

# Euler / Manim Color Palette
CYAN = "#68DBE8"
GOLD = "#FFC878"
WHITE = "#FFFFFF"
MINT = "#4EEDB2"


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


from dataclasses import dataclass

@dataclass(frozen=True)
class RealWorldRatesRoadmapSource:
    """Multi-shot skia animation source for Scene 02 with Euler-style MathTex and clean symbolic visuals."""

    intrinsic_size: tuple[int, int] = (1920, 1080)
    duration: float = SCENE_02_DURATION
    fingerprint: str = "chain:scene-02:real-world-rates-roadmap:v2-clean"
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
            "shot_02a": [
                (r"$\frac{ds}{dt}$", WHITE),
                ("$=$", WHITE),
                (r"$\frac{ds}{d\theta}$", CYAN),
                (r"$\cdot$", WHITE),
                (r"$\frac{d\theta}{dt}$", GOLD),
            ],
            "shot_02b": [
                (r"$\Delta B$", MINT),
                (r"$\approx$", WHITE),
                (r"$\frac{dB}{dr}$", CYAN),
                (r"$\cdot$", WHITE),
                (r"$\Delta r$", GOLD),
            ],
            "stage_1": [
                (r"$\frac{dA}{dC}$", WHITE),
                ("$=$", WHITE),
                (r"$\frac{dA}{dB}$", CYAN),
                (r"$\cdot$", WHITE),
                (r"$\frac{dB}{dC}$", GOLD),
            ],
            "stage_2": [
                (r"$\frac{dy}{dx}$", WHITE),
                ("$=$", WHITE),
                (r"$\lim_{\Delta x \to 0}$", WHITE),
                (r"$\frac{\Delta y}{\Delta x}$", GOLD),
            ],
            "stage_3": [
                (r"$\frac{dy}{dx}$", WHITE),
                ("$=$", WHITE),
                (r"$2x$", GOLD),
                (r"$\cdot$", WHITE),
                (r"$\cos(x^2)$", CYAN),
            ],
            "stage_4": [
                (r"$\frac{\partial L}{\partial w}$", WHITE),
                ("$=$", WHITE),
                (r"$\frac{\partial L}{\partial a}$", CYAN),
                (r"$\cdot$", WHITE),
                (r"$\frac{\partial a}{\partial z}$", GOLD),
                (r"$\cdot$", WHITE),
                (r"$\frac{\partial z}{\partial w}$", CYAN),
            ],
            "delta_r": [
                (r"$\Delta r = +0.25\%$", GOLD),
            ],
            "vec_v": [
                (r"$\vec{v}$", MINT),
            ],
            "theta_sym": [
                (r"$\theta$", GOLD),
            ],
            "h_sym": [
                (r"$h$", WHITE),
            ],
            "axis_t": [
                (r"$t$", WHITE),
            ],
            "axis_B": [
                (r"$B$", WHITE),
            ],
            "caliper_delta_B": [
                (r"$\Delta B$", MINT),
            ],
        }

        math_cache: dict[str, skia.Image] = {}
        for name, terms in formulas_dict.items():
            f_size = 26 if "stage" in name else (34 if "shot" in name else 24)
            math_cache[name] = _compose_latex_equation(terms, font_size=f_size)

        # Stage Metadata for 02C
        stages_meta = [
            {"id": 1, "num": "01", "title": "Three Gears", "eq_key": "stage_1", "accent": skia.Color4f(0.0, 0.94, 1.0, 1.0)},
            {"id": 2, "num": "02", "title": "First Principles", "eq_key": "stage_2", "accent": skia.Color4f(0.98, 0.78, 0.20, 1.0)},
            {"id": 3, "num": "03", "title": "The Crucible", "eq_key": "stage_3", "accent": skia.Color4f(0.95, 0.28, 0.65, 1.0)},
            {"id": 4, "num": "04", "title": "Neural Backprop", "eq_key": "stage_4", "accent": skia.Color4f(0.35, 0.75, 1.0, 1.0)},
        ]

        bg_black = skia.Color4f(0.0, 0.0, 0.0, 1.0)

        class Session:
            def frame(self, t: float) -> Image.Image:
                canvas.clear(bg_black)

                # ===========================================================
                # SHOT 02A: The Swinging Lamp & Accelerating Shadow (0s - 6.13s)
                # ===========================================================
                if t < 6.4:
                    shot_a_fade = 1.0
                    if t < 0.8:
                        shot_a_fade = min(1.0, max(0.0, t / 0.8))
                    elif t > 5.5:
                        shot_a_fade = min(1.0, max(0.0, (6.13 - t) / 0.63))

                    if shot_a_fade > 0:
                        # 1. Geometry Setup
                        ground_y = 860.0 * sy
                        pivot_x = 960.0 * sx
                        pivot_y = 110.0 * sy
                        cable_len = 380.0 * sy
                        rod_x = 1260.0 * sx
                        rod_h = 240.0 * sy
                        rod_top_y = ground_y - rod_h

                        # Pendulum motion
                        theta_0 = 0.58
                        omega = 2.1
                        theta = theta_0 * math.sin(t * omega)
                        d_theta = theta_0 * omega * math.cos(t * omega)

                        lamp_x = pivot_x + cable_len * math.sin(theta)
                        lamp_y = pivot_y + cable_len * math.cos(theta)

                        # Shadow projection: Ray from lamp through rod tip to ground
                        denom = (rod_top_y - lamp_y)
                        shadow_x = lamp_x + (ground_y - lamp_y) * (rod_x - lamp_x) / (denom if abs(denom) > 1e-4 else 1e-4)

                        # Shadow tip velocity: numerical derivative
                        dt_num = 0.016
                        theta_f = theta_0 * math.sin((t + dt_num) * omega)
                        lamp_xf = pivot_x + cable_len * math.sin(theta_f)
                        lamp_yf = pivot_y + cable_len * math.cos(theta_f)
                        denom_f = (rod_top_y - lamp_yf)
                        shadow_xf = lamp_xf + (ground_y - lamp_yf) * (rod_x - lamp_xf) / (denom_f if abs(denom_f) > 1e-4 else 1e-4)
                        v_shadow = (shadow_xf - shadow_x) / dt_num

                        # 2. Floor Line & Metric Grid Ticks
                        floor_p = skia.Paint(
                            Color=skia.Color4f(0.20, 0.28, 0.40, 0.60 * shot_a_fade),
                            StrokeWidth=1.5 * sx,
                            AntiAlias=True,
                        )
                        canvas.drawLine(100.0 * sx, ground_y, 1820.0 * sx, ground_y, floor_p)

                        tick_p = skia.Paint(
                            Color=skia.Color4f(0.30, 0.42, 0.58, 0.40 * shot_a_fade),
                            StrokeWidth=1.0 * sx,
                            AntiAlias=True,
                        )
                        for x_pos in range(160, 1800, 40):
                            tx = x_pos * sx
                            is_major = (x_pos % 200 == 0)
                            canvas.drawLine(tx, ground_y, tx, ground_y + (10.0 * sy if is_major else 5.0 * sy), tick_p)

                        # 3. Volumetric Light Cone from Lamp to Ground
                        cone_path = skia.Path()
                        cone_path.moveTo(lamp_x, lamp_y)
                        cone_w_ground = 780.0 * sx
                        cone_path.lineTo(lamp_x - cone_w_ground * 0.5, ground_y)
                        cone_path.lineTo(lamp_x + cone_w_ground * 0.5, ground_y)
                        cone_path.close()

                        cone_paint = skia.Paint(
                            Shader=skia.GradientShader.MakeRadial(
                                (lamp_x, lamp_y),
                                850.0 * sy,
                                [
                                    skia.Color4f(1.0, 0.88, 0.45, 0.18 * shot_a_fade),
                                    skia.Color4f(1.0, 0.82, 0.30, 0.05 * shot_a_fade),
                                    skia.Color4f(0.0, 0.0, 0.0, 0.0),
                                ],
                                [0.0, 0.45, 1.0],
                            ),
                            AntiAlias=True,
                        )
                        canvas.drawPath(cone_path, cone_paint)

                        # Light Ray tracing from lamp past rod tip to shadow tip
                        ray_p = skia.Paint(
                            Color=skia.Color4f(1.0, 0.90, 0.40, 0.55 * shot_a_fade),
                            StrokeWidth=1.2 * sx,
                            PathEffect=skia.DashPathEffect.Make([8.0 * sx, 6.0 * sx], 0.0),
                            AntiAlias=True,
                        )
                        canvas.drawLine(lamp_x, lamp_y, shadow_x, ground_y, ray_p)

                        # 4. Cast Shadow on Floor
                        s_min = min(rod_x, shadow_x)
                        s_max = max(rod_x, shadow_x)
                        shadow_rect = skia.Rect.MakeLTRB(s_min, ground_y, s_max, ground_y + 10.0 * sy)
                        shadow_p = skia.Paint(Color=skia.Color4f(0.02, 0.04, 0.08, 0.95 * shot_a_fade), AntiAlias=True)
                        canvas.drawRect(shadow_rect, shadow_p)

                        shadow_edge_p = skia.Paint(
                            Color=skia.Color4f(0.0, 0.95, 1.0, 0.70 * shot_a_fade),
                            StrokeWidth=2.0 * sx,
                            AntiAlias=True,
                        )
                        canvas.drawLine(s_min, ground_y, s_max, ground_y, shadow_edge_p)

                        # 5. Vertical Physical Rod
                        rod_w = 10.0 * sx
                        rod_rect = skia.Rect.MakeLTRB(rod_x - rod_w * 0.5, rod_top_y, rod_x + rod_w * 0.5, ground_y)
                        rod_p = skia.Paint(
                            Shader=skia.GradientShader.MakeLinear(
                                [(rod_x - rod_w * 0.5, 0), (rod_x + rod_w * 0.5, 0)],
                                [skia.Color4f(0.85, 0.90, 0.98, 0.95 * shot_a_fade), skia.Color4f(0.35, 0.45, 0.58, 0.95 * shot_a_fade)],
                                [0.0, 1.0],
                            ),
                            AntiAlias=True,
                        )
                        canvas.drawRect(rod_rect, rod_p)
                        canvas.drawCircle(rod_x, rod_top_y, 4.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 0.85, 0.20, 1.0 * shot_a_fade), AntiAlias=True))

                        # Symbolic Height Caliper 'h' (replacing "FIXED OBSTACLE" text)
                        cal_x = rod_x - 24.0 * sx
                        cal_p = skia.Paint(Color=skia.Color4f(0.40, 0.55, 0.70, 0.60 * shot_a_fade), StrokeWidth=1.2 * sx, AntiAlias=True)
                        canvas.drawLine(cal_x, rod_top_y, cal_x, ground_y, cal_p)
                        canvas.drawLine(cal_x - 4.0 * sx, rod_top_y, cal_x + 4.0 * sx, rod_top_y, cal_p)
                        canvas.drawLine(cal_x - 4.0 * sx, ground_y, cal_x + 4.0 * sx, ground_y, cal_p)
                        h_img = math_cache["h_sym"]
                        _draw_math_centered(canvas, h_img, cal_x - 14.0 * sx, (rod_top_y + ground_y) * 0.5, alpha=shot_a_fade, base_scale=0.5)

                        # 6. Dynamic Emerald Shadow Velocity Vector Arrow
                        v_len = min(280.0 * sx, abs(v_shadow) * 0.16 * sx)
                        if v_len > 14.0 * sx:
                            v_dir = 1.0 if v_shadow >= 0 else -1.0
                            arrow_end_x = shadow_x + v_dir * v_len
                            arrow_y = ground_y - 14.0 * sy

                            arrow_p = skia.Paint(
                                Color=skia.Color4f(0.0, 0.96, 0.60, 0.95 * shot_a_fade),
                                StrokeWidth=2.4 * sx,
                                AntiAlias=True,
                            )
                            canvas.drawLine(shadow_x, arrow_y, arrow_end_x, arrow_y, arrow_p)

                            head_len = 10.0 * sx
                            head_w = 6.0 * sy
                            canvas.drawLine(arrow_end_x, arrow_y, arrow_end_x - v_dir * head_len, arrow_y - head_w, arrow_p)
                            canvas.drawLine(arrow_end_x, arrow_y, arrow_end_x - v_dir * head_len, arrow_y + head_w, arrow_p)

                            # Vector symbol \vec{v} in LaTeX
                            v_img = math_cache["vec_v"]
                            _draw_math_centered(canvas, v_img, (shadow_x + arrow_end_x) * 0.5, arrow_y - 14.0 * sy, alpha=shot_a_fade, base_scale=0.55)

                        # 7. Lamp Pendulum (Mount, Cable, Housing, Bulb)
                        mount_p = skia.Paint(Color=skia.Color4f(0.50, 0.55, 0.65, 0.85 * shot_a_fade), AntiAlias=True)
                        canvas.drawRect(skia.Rect.MakeLTRB(pivot_x - 30.0 * sx, pivot_y - 12.0 * sy, pivot_x + 30.0 * sx, pivot_y), mount_p)
                        canvas.drawCircle(pivot_x, pivot_y, 4.0 * sx, mount_p)

                        # Vertical plumb line for angle theta
                        plumb_p = skia.Paint(
                            Color=skia.Color4f(0.30, 0.40, 0.55, 0.45 * shot_a_fade),
                            StrokeWidth=1.0 * sx,
                            PathEffect=skia.DashPathEffect.Make([4.0 * sx, 4.0 * sx], 0.0),
                            AntiAlias=True,
                        )
                        canvas.drawLine(pivot_x, pivot_y, pivot_x, pivot_y + 120.0 * sy, plumb_p)

                        # Angle arc theta
                        arc_rad = 75.0 * sx
                        arc_p = skia.Paint(
                            Color=skia.Color4f(0.98, 0.78, 0.20, 0.75 * shot_a_fade),
                            StrokeWidth=1.4 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        arc_rect = skia.Rect.MakeXYWH(pivot_x - arc_rad, pivot_y - arc_rad, arc_rad * 2, arc_rad * 2)
                        theta_deg = math.degrees(theta)
                        start_angle = 90.0 if theta >= 0 else 90.0 + theta_deg
                        sweep_angle = theta_deg if theta >= 0 else -theta_deg
                        canvas.drawArc(arc_rect, start_angle, sweep_angle, False, arc_p)

                        # Theta LaTeX symbol
                        th_img = math_cache["theta_sym"]
                        th_angle = math.radians(90 + theta_deg * 0.5)
                        _draw_math_centered(
                            canvas,
                            th_img,
                            pivot_x + (arc_rad + 18.0 * sx) * math.cos(th_angle),
                            pivot_y + (arc_rad + 18.0 * sx) * math.sin(th_angle),
                            alpha=shot_a_fade,
                            base_scale=0.5,
                        )

                        # Cable
                        cable_p = skia.Paint(Color=skia.Color4f(0.70, 0.75, 0.85, 0.85 * shot_a_fade), StrokeWidth=1.5 * sx, AntiAlias=True)
                        canvas.drawLine(pivot_x, pivot_y, lamp_x, lamp_y, cable_p)

                        # Bell housing
                        bell_path = skia.Path()
                        bw, bh = 28.0 * sx, 22.0 * sy
                        bell_path.moveTo(lamp_x, lamp_y - 6.0 * sy)
                        bell_path.lineTo(lamp_x - bw * 0.5, lamp_y + bh)
                        bell_path.lineTo(lamp_x + bw * 0.5, lamp_y + bh)
                        bell_path.close()
                        canvas.drawPath(bell_path, skia.Paint(Color=skia.Color4f(0.25, 0.30, 0.40, 0.95 * shot_a_fade), AntiAlias=True))

                        # Bulb
                        bulb_y = lamp_y + bh + 4.0 * sy
                        canvas.drawCircle(
                            lamp_x,
                            bulb_y,
                            16.0 * sx,
                            skia.Paint(
                                Color=skia.Color4f(1.0, 0.88, 0.35, 0.85 * shot_a_fade),
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12.0 * sx),
                                AntiAlias=True,
                            ),
                        )
                        canvas.drawCircle(lamp_x, bulb_y, 6.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 0.95, 1.0 * shot_a_fade), AntiAlias=True))

                        # 8. Floating Master LaTeX Formula (ds/dt = ds/dθ · dθ/dt)
                        eq_a = math_cache["shot_02a"]
                        eq_x = 220.0 * sx
                        eq_y = 220.0 * sy
                        # Soft focal glow behind equation
                        canvas.drawCircle(
                            eq_x + 140.0 * sx,
                            eq_y + 40.0 * sy,
                            180.0 * sx,
                            skia.Paint(
                                Shader=skia.GradientShader.MakeRadial(
                                    (eq_x + 140.0 * sx, eq_y + 40.0 * sy),
                                    180.0 * sx,
                                    [skia.Color4f(0.0, 0.85, 1.0, 0.08 * shot_a_fade), skia.Color4f(0.0, 0.0, 0.0, 0.0)],
                                    [0.0, 1.0],
                                )
                            ),
                        )
                        _draw_math_centered(canvas, eq_a, eq_x + 140.0 * sx, eq_y + 40.0 * sy, alpha=shot_a_fade, base_scale=0.65)

                # ===========================================================
                # SHOT 02B: The Compounding Bank Balance (6.13s - 11.06s)
                # ===========================================================
                if 5.8 < t < 11.3:
                    shot_b_fade = 1.0
                    if t < 6.8:
                        shot_b_fade = min(1.0, max(0.0, (t - 6.13) / 0.67))
                    elif t > 10.4:
                        shot_b_fade = min(1.0, max(0.0, (11.06 - t) / 0.66))

                    if shot_b_fade > 0:
                        # Smooth Nudge animation
                        nudge_progress = min(1.0, max(0.0, (t - 6.8) / 1.5))
                        curr_rate = 5.0 + 0.25 * (1.0 - math.cos(nudge_progress * math.pi)) * 0.5

                        # 1. Left: Minimalist Floating Rate Dial (NO bulky card container)
                        dial_cx = 380.0 * sx
                        dial_cy = 480.0 * sy
                        dial_rad = 120.0 * sx

                        dial_ring_p = skia.Paint(
                            Color=skia.Color4f(0.20, 0.30, 0.42, 0.60 * shot_b_fade),
                            StrokeWidth=2.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        canvas.drawCircle(dial_cx, dial_cy, dial_rad, dial_ring_p)

                        for deg in range(-140, 141, 10):
                            rad = math.radians(deg - 90)
                            is_maj = (deg % 30 == 0)
                            t_len = 12.0 * sx if is_maj else 6.0 * sx
                            p1 = (dial_cx + (dial_rad - 6.0 * sx) * math.cos(rad), dial_cy + (dial_rad - 6.0 * sx) * math.sin(rad))
                            p2 = (dial_cx + (dial_rad - 6.0 * sx - t_len) * math.cos(rad), dial_cy + (dial_rad - 6.0 * sx - t_len) * math.sin(rad))
                            canvas.drawLine(p1[0], p1[1], p2[0], p2[1], dial_ring_p)

                        # Active arc
                        base_deg = -30.0
                        delta_deg = 35.0 * nudge_progress
                        arc_p = skia.Paint(
                            Color=skia.Color4f(0.98, 0.78, 0.20, 0.90 * shot_b_fade),
                            StrokeWidth=4.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        arc_rect = skia.Rect.MakeXYWH(dial_cx - dial_rad + 3.0 * sx, dial_cy - dial_rad + 3.0 * sx, (dial_rad - 3.0 * sx) * 2, (dial_rad - 3.0 * sx) * 2)
                        canvas.drawArc(arc_rect, -120.0, delta_deg + 2.0, False, arc_p)

                        # Needle
                        needle_rad = math.radians(base_deg + delta_deg - 90)
                        nx = dial_cx + (dial_rad - 18.0 * sx) * math.cos(needle_rad)
                        ny = dial_cy + (dial_rad - 18.0 * sx) * math.sin(needle_rad)
                        needle_core = skia.Paint(Color=skia.Color4f(1.0, 1.0, 0.95, 1.0 * shot_b_fade), StrokeWidth=2.2 * sx, AntiAlias=True)
                        canvas.drawLine(dial_cx, dial_cy, nx, ny, needle_core)
                        canvas.drawCircle(dial_cx, dial_cy, 7.0 * sx, needle_core)

                        # Key Number: 5.25% in elegant serif
                        r_font = skia.Font(tf_serif_bold, 46.0 * sx)
                        r_paint = skia.Paint(Color=skia.Color4f(1.0, 0.98, 0.95, 1.0 * shot_b_fade), AntiAlias=True)
                        r_str = f"{curr_rate:.2f}%"
                        r_w = r_font.measureText(r_str)
                        canvas.drawString(r_str, dial_cx - r_w * 0.5, dial_cy + 155.0 * sy, r_font, r_paint)

                        # Clean LaTeX symbol \Delta r = +0.25%
                        dr_img = math_cache["delta_r"]
                        _draw_math_centered(canvas, dr_img, dial_cx, dial_cy + 205.0 * sy, alpha=shot_b_fade, base_scale=0.55)

                        # 2. Right: Compounding Curves on Bare Coordinate Axes (NO bulky box!)
                        gx0 = 760.0 * sx
                        gy0 = 760.0 * sy
                        gw = 960.0 * sx
                        gh = 480.0 * sy

                        axis_p = skia.Paint(Color=skia.Color4f(0.35, 0.45, 0.60, 0.70 * shot_b_fade), StrokeWidth=1.5 * sx, AntiAlias=True)
                        canvas.drawLine(gx0, gy0, gx0 + gw, gy0, axis_p)
                        canvas.drawLine(gx0, gy0, gx0, gy0 - gh, axis_p)

                        # Arrowheads
                        head_s = 8.0 * sx
                        canvas.drawLine(gx0 + gw, gy0, gx0 + gw - head_s, gy0 - head_s * 0.6, axis_p)
                        canvas.drawLine(gx0 + gw, gy0, gx0 + gw - head_s, gy0 + head_s * 0.6, axis_p)
                        canvas.drawLine(gx0, gy0 - gh, gx0 - head_s * 0.6, gy0 - gh + head_s, axis_p)
                        canvas.drawLine(gx0, gy0 - gh, gx0 + head_s * 0.6, gy0 - gh + head_s, axis_p)

                        # Clean LaTeX Axis Labels: t and B
                        _draw_math_centered(canvas, math_cache["axis_t"], gx0 + gw + 22.0 * sx, gy0, alpha=shot_b_fade, base_scale=0.5)
                        _draw_math_centered(canvas, math_cache["axis_B"], gx0, gy0 - gh - 22.0 * sy, alpha=shot_b_fade, base_scale=0.5)

                        # Year tick marks
                        for yr in (10, 20, 30):
                            tx = gx0 + (yr / 30.0) * gw * 0.92
                            canvas.drawLine(tx, gy0, tx, gy0 + 6.0 * sy, axis_p)
                            canvas.drawString(f"{yr}", tx - 8.0 * sx, gy0 + 26.0 * sy, skia.Font(tf_sans_med, 13.0 * sx), axis_p)

                        # Curves computation
                        num_steps = 60
                        P = 10000.0
                        b_max = P * math.pow(1.0525, 30.0)
                        base_pts, nudge_pts = [], []
                        for step in range(num_steps + 1):
                            yr = (step / num_steps) * 30.0
                            px = gx0 + (yr / 30.0) * gw * 0.92
                            b_base = P * math.pow(1.05, yr)
                            py_base = gy0 - (b_base / b_max) * (gh * 0.84)
                            b_nudge = P * math.pow(1.05 + 0.0025 * nudge_progress, yr)
                            py_nudge = gy0 - (b_nudge / b_max) * (gh * 0.84)
                            base_pts.append((px, py_base))
                            nudge_pts.append((px, py_nudge))

                        # Shaded Ribbon between curves
                        ribbon = skia.Path()
                        ribbon.moveTo(base_pts[0][0], base_pts[0][1])
                        for pt in base_pts[1:]:
                            ribbon.lineTo(pt[0], pt[1])
                        for pt in reversed(nudge_pts):
                            ribbon.lineTo(pt[0], pt[1])
                        ribbon.close()
                        ribbon_p = skia.Paint(
                            Shader=skia.GradientShader.MakeLinear(
                                [(gx0, 0), (gx0 + gw * 0.92, 0)],
                                [
                                    skia.Color4f(0.0, 0.95, 0.65, 0.05 * shot_b_fade),
                                    skia.Color4f(0.0, 0.95, 0.65, 0.35 * shot_b_fade),
                                ],
                                [0.0, 1.0],
                            ),
                            AntiAlias=True,
                        )
                        canvas.drawPath(ribbon, ribbon_p)

                        # Base curve
                        path_base = skia.Path()
                        path_base.moveTo(base_pts[0][0], base_pts[0][1])
                        for pt in base_pts[1:]:
                            path_base.lineTo(pt[0], pt[1])
                        canvas.drawPath(
                            path_base,
                            skia.Paint(Color=skia.Color4f(0.40, 0.65, 0.80, 0.70 * shot_b_fade), StrokeWidth=2.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True),
                        )

                        # Nudged curve
                        path_nudge = skia.Path()
                        path_nudge.moveTo(nudge_pts[0][0], nudge_pts[0][1])
                        for pt in nudge_pts[1:]:
                            path_nudge.lineTo(pt[0], pt[1])
                        canvas.drawPath(
                            path_nudge,
                            skia.Paint(
                                Color=skia.Color4f(0.0, 0.96, 0.60, 0.50 * shot_b_fade),
                                StrokeWidth=5.0 * sx,
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0 * sx),
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            ),
                        )
                        canvas.drawPath(
                            path_nudge,
                            skia.Paint(Color=skia.Color4f(0.20, 1.0, 0.75, 1.0 * shot_b_fade), StrokeWidth=2.4 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True),
                        )

                        # Caliper brackets at t=30
                        x30 = base_pts[-1][0]
                        y30_base = base_pts[-1][1]
                        y30_nudge = nudge_pts[-1][1]
                        cal_p = skia.Paint(Color=skia.Color4f(0.0, 0.98, 0.65, 0.90 * shot_b_fade), StrokeWidth=1.5 * sx, AntiAlias=True)
                        canvas.drawLine(x30 + 12.0 * sx, y30_nudge, x30 + 12.0 * sx, y30_base, cal_p)
                        canvas.drawLine(x30 + 6.0 * sx, y30_nudge, x30 + 18.0 * sx, y30_nudge, cal_p)
                        canvas.drawLine(x30 + 6.0 * sx, y30_base, x30 + 18.0 * sx, y30_base, cal_p)

                        # Clean LaTeX divergence caliper symbol \Delta B
                        _draw_math_centered(canvas, math_cache["caliper_delta_B"], x30 + 44.0 * sx, (y30_base + y30_nudge) * 0.5, alpha=shot_b_fade, base_scale=0.55)

                        # Floating Master LaTeX Formula: ΔB ≈ (dB/dr) · Δr
                        _draw_math_centered(canvas, math_cache["shot_02b"], gx0 + 260.0 * sx, gy0 - gh + 70.0 * sy, alpha=shot_b_fade, base_scale=0.60)

                # ===========================================================
                # SHOT 02C: The 7-Minute Roadmap (4-Stage Pipeline) (11.06s - 37.36s)
                # ===========================================================
                if 10.7 < t < 37.8:
                    shot_c_fade = 1.0
                    if t < 11.8:
                        shot_c_fade = min(1.0, max(0.0, (t - 11.06) / 0.74))
                    elif t > 36.6:
                        shot_c_fade = min(1.0, max(0.0, (37.36 - t) / 0.76))

                    if shot_c_fade > 0:
                        # Minimalist Header (clean, unobtrusive)
                        hdr_font = skia.Font(tf_sans_bold, 13.0 * sx)
                        hdr_p = skia.Paint(Color=skia.Color4f(0.50, 0.65, 0.85, 0.75 * shot_c_fade), AntiAlias=True)
                        _draw_letterspaced(canvas, "FOUR STAGES TO COMPLETE INTUITION", 960.0 * sx, 150.0 * sy, hdr_font, hdr_p, 4.0 * sx)

                        # Determine active stage
                        active_stage = 0
                        if t >= 29.16:
                            active_stage = 4
                        elif t >= 23.78:
                            active_stage = 3
                        elif t >= 18.57:
                            active_stage = 2
                        elif t >= 13.22:
                            active_stage = 1

                        card_w = 360.0 * sx
                        card_h = 580.0 * sy
                        card_y = 220.0 * sy
                        card_centers_x = [330.0 * sx, 750.0 * sx, 1170.0 * sx, 1590.0 * sx]

                        # Connecting conduits with traveling photon packets
                        for c_i in range(3):
                            p_start = (card_centers_x[c_i] + card_w * 0.5, card_y + card_h * 0.5)
                            p_end = (card_centers_x[c_i + 1] - card_w * 0.5, card_y + card_h * 0.5)

                            conduit_base_p = skia.Paint(
                                Color=skia.Color4f(0.20, 0.28, 0.40, 0.45 * shot_c_fade),
                                StrokeWidth=1.5 * sx,
                                AntiAlias=True,
                            )
                            canvas.drawLine(p_start[0], p_start[1], p_end[0], p_end[1], conduit_base_p)

                            if active_stage > c_i + 1:
                                pulse_p = skia.Paint(
                                    Color=skia.Color4f(0.0, 0.95, 1.0, 0.85 * shot_c_fade),
                                    StrokeWidth=2.2 * sx,
                                    AntiAlias=True,
                                )
                                canvas.drawLine(p_start[0], p_start[1], p_end[0], p_end[1], pulse_p)
                            elif active_stage == c_i + 1:
                                pulse_prog = (t * 2.5) % 1.0
                                cur_pulse_x = p_start[0] + pulse_prog * (p_end[0] - p_start[0])
                                p_glow = skia.Paint(
                                    Color=skia.Color4f(1.0, 0.85, 0.30, 0.95 * shot_c_fade),
                                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0 * sx),
                                    AntiAlias=True,
                                )
                                canvas.drawCircle(cur_pulse_x, p_start[1], 4.0 * sx, p_glow)

                        # Render the 4 Cards
                        for s_item in stages_meta:
                            s_id = s_item["id"]
                            cx = card_centers_x[s_id - 1]
                            is_active = (active_stage == s_id)
                            has_passed = (active_stage > s_id)
                            accent = s_item["accent"]
                            card_alpha = 1.0 if is_active else (0.75 if has_passed else 0.40)

                            card_rect = skia.Rect.MakeXYWH(cx - card_w * 0.5, card_y, card_w, card_h)

                            # Sleek dark glass card
                            c_bg_p = skia.Paint(Color=skia.Color4f(0.02, 0.04, 0.08, (0.85 if is_active else 0.60) * shot_c_fade), AntiAlias=True)
                            canvas.drawRoundRect(card_rect, 12.0 * sx, 12.0 * sy, c_bg_p)

                            # Active glow rim
                            if is_active:
                                rim_bloom = skia.Paint(
                                    Color=skia.Color4f(accent.fR, accent.fG, accent.fB, 0.55 * shot_c_fade),
                                    MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14.0 * sx),
                                    StrokeWidth=2.4 * sx,
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                )
                                canvas.drawRoundRect(card_rect, 12.0 * sx, 12.0 * sy, rim_bloom)

                            c_border_p = skia.Paint(
                                Color=skia.Color4f(accent.fR, accent.fG, accent.fB, (0.90 if is_active else 0.25) * shot_c_fade),
                                StrokeWidth=1.5 * sx if is_active else 1.0 * sx,
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            )
                            canvas.drawRoundRect(card_rect, 12.0 * sx, 12.0 * sy, c_border_p)

                            # Stage Numeral (sleek, minimalist, prominent: "01")
                            num_font = skia.Font(tf_sans_bold, 18.0 * sx)
                            num_p = skia.Paint(Color=skia.Color4f(accent.fR, accent.fG, accent.fB, card_alpha * shot_c_fade), AntiAlias=True)
                            canvas.drawString(s_item["num"], cx - card_w * 0.5 + 24.0 * sx, card_y + 38.0 * sy, num_font, num_p)

                            # Stage Title (Cormorant Garamond serif, elegant)
                            t_font = skia.Font(tf_serif_bold, 26.0 * sx)
                            t_paint = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, card_alpha * shot_c_fade), AntiAlias=True)
                            t_str = s_item["title"]
                            canvas.drawString(t_str, cx - card_w * 0.5 + 24.0 * sx, card_y + 74.0 * sy, t_font, t_paint)

                            # Thin accent divider
                            canvas.drawLine(
                                cx - card_w * 0.5 + 24.0 * sx,
                                card_y + 92.0 * sy,
                                cx + card_w * 0.5 - 24.0 * sx,
                                card_y + 92.0 * sy,
                                skia.Paint(Color=skia.Color4f(accent.fR, accent.fG, accent.fB, 0.35 * card_alpha * shot_c_fade), StrokeWidth=1.0 * sx, AntiAlias=True),
                            )

                            # Animated Dynamic Visualization Area
                            icon_cy = card_y + 240.0 * sy
                            if s_id == 1:
                                # Meshed Gears
                                g_angle = t * 1.8 if is_active else 0.8
                                g1_x, g1_y = cx - 52.0 * sx, icon_cy
                                g1_r = 38.0 * sx
                                p_g1 = skia.Paint(Color=skia.Color4f(0.0, 0.92, 1.0, card_alpha * shot_c_fade), StrokeWidth=1.8 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                                canvas.drawCircle(g1_x, g1_y, g1_r, p_g1)
                                for te in range(8):
                                    a_rad = g_angle + te * (math.tau / 8)
                                    canvas.drawLine(g1_x + (g1_r - 4.0 * sx) * math.cos(a_rad), g1_y + (g1_r - 4.0 * sx) * math.sin(a_rad), g1_x + (g1_r + 6.0 * sx) * math.cos(a_rad), g1_y + (g1_r + 6.0 * sx) * math.sin(a_rad), p_g1)

                                g2_x, g2_y = cx + 10.0 * sx, icon_cy
                                g2_r = 25.0 * sx
                                p_g2 = skia.Paint(Color=skia.Color4f(0.98, 0.78, 0.20, card_alpha * shot_c_fade), StrokeWidth=1.8 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                                canvas.drawCircle(g2_x, g2_y, g2_r, p_g2)
                                for te in range(6):
                                    a_rad = -g_angle * 1.54 + te * (math.tau / 6)
                                    canvas.drawLine(g2_x + (g2_r - 4.0 * sx) * math.cos(a_rad), g2_y + (g2_r - 4.0 * sx) * math.sin(a_rad), g2_x + (g2_r + 5.0 * sx) * math.cos(a_rad), g2_y + (g2_r + 5.0 * sx) * math.sin(a_rad), p_g2)

                                g3_x, g3_y = cx + 54.0 * sx, icon_cy
                                g3_r = 16.0 * sx
                                p_g3 = skia.Paint(Color=skia.Color4f(0.95, 0.35, 0.45, card_alpha * shot_c_fade), StrokeWidth=1.8 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                                canvas.drawCircle(g3_x, g3_y, g3_r, p_g3)
                                for te in range(4):
                                    a_rad = g_angle * 2.42 + te * (math.tau / 4)
                                    canvas.drawLine(g3_x + (g3_r - 3.0 * sx) * math.cos(a_rad), g3_y + (g3_r - 3.0 * sx) * math.sin(a_rad), g3_x + (g3_r + 4.0 * sx) * math.cos(a_rad), g3_y + (g3_r + 4.0 * sx) * math.sin(a_rad), p_g3)

                            elif s_id == 2:
                                # Secant to Tangent Limit
                                p_curve = skia.Paint(Color=skia.Color4f(0.98, 0.78, 0.20, card_alpha * shot_c_fade), StrokeWidth=2.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                                curve_path = skia.Path()
                                curve_path.moveTo(cx - 75.0 * sx, icon_cy + 45.0 * sy)
                                curve_path.quadTo(cx - 10.0 * sx, icon_cy + 35.0 * sy, cx + 75.0 * sx, icon_cy - 45.0 * sy)
                                canvas.drawPath(curve_path, p_curve)

                                step_t = (math.sin(t * 3.0) + 1.0) * 0.5 if is_active else 0.15
                                dx_offset = 12.0 * sx + 45.0 * sx * step_t
                                p0_x = cx - 20.0 * sx
                                p0_y = icon_cy + 15.0 * sy
                                p1_x = p0_x + dx_offset
                                p1_y = p0_y - dx_offset * 0.7
                                p_sec = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, card_alpha * shot_c_fade), StrokeWidth=1.5 * sx, AntiAlias=True)
                                canvas.drawLine(p0_x - 20.0 * sx, p0_y + 14.0 * sy, p1_x + 20.0 * sx, p1_y - 14.0 * sy, p_sec)
                                canvas.drawCircle(p0_x, p0_y, 3.5 * sx, p_sec)
                                canvas.drawCircle(p1_x, p1_y, 3.5 * sx, p_sec)

                            elif s_id == 3:
                                # Wave Crucible
                                p_wave = skia.Paint(Color=skia.Color4f(0.95, 0.28, 0.65, card_alpha * shot_c_fade), StrokeWidth=2.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                                wave_path = skia.Path()
                                for wi in range(70):
                                    rel_x = (wi / 69.0) * 150.0 * sx - 75.0 * sx
                                    x_val = (wi / 69.0) * 2.8
                                    y_val = math.sin(x_val * x_val) * 38.0 * sy
                                    if wi == 0:
                                        wave_path.moveTo(cx + rel_x, icon_cy - y_val)
                                    else:
                                        wave_path.lineTo(cx + rel_x, icon_cy - y_val)
                                canvas.drawPath(wave_path, p_wave)

                            elif s_id == 4:
                                # Neural Backpropagation
                                mini_layers = (3, 4, 4, 2)
                                l_xs = [cx - 65.0 * sx, cx - 22.0 * sx, cx + 22.0 * sx, cx + 65.0 * sx]
                                mini_nodes = []
                                for l_idx, count in enumerate(mini_layers):
                                    node_pts = []
                                    spacing = 22.0 * sy
                                    for ni in range(count):
                                        ny = icon_cy + (ni - (count - 1) / 2) * spacing
                                        node_pts.append((l_xs[l_idx], ny))
                                    mini_nodes.append(node_pts)
                                p_syn = skia.Paint(Color=skia.Color4f(0.30, 0.50, 0.70, 0.35 * card_alpha * shot_c_fade), StrokeWidth=1.0 * sx, AntiAlias=True)
                                for l_idx in range(len(mini_nodes) - 1):
                                    for p1 in mini_nodes[l_idx]:
                                        for p2 in mini_nodes[l_idx + 1]:
                                            canvas.drawLine(p1[0], p1[1], p2[0], p2[1], p_syn)

                                b_wave = ((t * 1.8) % 1.0) * 3.5 if is_active else 1.5
                                for l_idx, node_pts in enumerate(mini_nodes):
                                    is_back_active = abs((3 - l_idx) - b_wave) < 0.8
                                    n_color = skia.Color4f(0.95, 0.25, 0.35, card_alpha * shot_c_fade) if is_back_active else skia.Color4f(0.35, 0.75, 1.0, card_alpha * shot_c_fade)
                                    p_node = skia.Paint(Color=n_color, AntiAlias=True)
                                    for pt in node_pts:
                                        canvas.drawCircle(pt[0], pt[1], 3.2 * sx, p_node)

                            # Floating Master LaTeX Formula (styled like euler_scene.py)
                            eq_item = math_cache[s_item["eq_key"]]
                            _draw_math_centered(canvas, eq_item, cx, card_y + 440.0 * sy, max_w=card_w - 44.0 * sx, alpha=card_alpha * shot_c_fade, base_scale=0.52)

                # ===========================================================
                # SHOT 02D: "You Will See It" Reveal (37.36s - 41.13s)
                # ===========================================================
                if t >= 37.0:
                    shot_d_st = 37.36
                    shot_d_fade = min(1.0, max(0.0, (t - shot_d_st) / 0.85)) if t >= shot_d_st else 0.0
                    if t > 40.5:
                        shot_d_fade *= max(0.0, (41.13 - t) / 0.63)

                    if shot_d_fade > 0:
                        # 1. Subtle central ambient focal nebula
                        nebula = skia.Paint(
                            Shader=skia.GradientShader.MakeRadial(
                                (960.0 * sx, 520.0 * sy),
                                580.0 * sx,
                                [
                                    skia.Color4f(0.0, 0.85, 1.0, 0.15 * shot_d_fade),
                                    skia.Color4f(0.98, 0.72, 0.12, 0.08 * shot_d_fade),
                                    skia.Color4f(0.0, 0.0, 0.0, 0.0),
                                ],
                                [0.0, 0.45, 1.0],
                            )
                        )
                        canvas.drawCircle(960.0 * sx, 520.0 * sy, 580.0 * sx, nebula)

                        # 2. Horizontal Anamorphic Laser Streak
                        streak_w = 1100.0 * sx * min(1.0, (t - shot_d_st) / 0.8)
                        streak_p = skia.Paint(
                            Shader=skia.GradientShader.MakeLinear(
                                [(960.0 * sx - streak_w * 0.5, 595.0 * sy), (960.0 * sx + streak_w * 0.5, 595.0 * sy)],
                                [
                                    skia.Color4f(0.0, 0.90, 1.0, 0.0),
                                    skia.Color4f(0.20, 0.95, 1.0, 0.55 * shot_d_fade),
                                    skia.Color4f(0.0, 0.90, 1.0, 0.0),
                                ],
                                [0.0, 0.5, 1.0],
                            ),
                            StrokeWidth=1.2 * sx,
                            AntiAlias=True,
                        )
                        canvas.drawLine(960.0 * sx - streak_w * 0.5, 595.0 * sy, 960.0 * sx + streak_w * 0.5, 595.0 * sy, streak_p)

                        # 3. Line 1: "By the end, you will not just know the formula."
                        l1_font = skia.Font(tf_serif_bold, 44.0 * sx)
                        l1_text = "By the end, you will not just know the formula."
                        l1_w = l1_font.measureText(l1_text)
                        l1_p = skia.Paint(
                            Color=skia.Color4f(0.94, 0.96, 1.0, 0.95 * shot_d_fade),
                            AntiAlias=True,
                        )
                        canvas.drawString(l1_text, (1920.0 * sx - l1_w) * 0.5, 475.0 * sy, l1_font, l1_p)

                        # Hairline Divider with Central Diamond
                        div_len = 380.0 * sx * min(1.0, (t - shot_d_st) / 0.7)
                        div_y = 515.0 * sy
                        div_p = skia.Paint(
                            Color=skia.Color4f(0.98, 0.78, 0.20, 0.85 * shot_d_fade),
                            StrokeWidth=1.4 * sx,
                            AntiAlias=True,
                        )
                        canvas.drawLine(960.0 * sx - div_len * 0.5, div_y, 960.0 * sx - 16.0 * sx, div_y, div_p)
                        canvas.drawLine(960.0 * sx + 16.0 * sx, div_y, 960.0 * sx + div_len * 0.5, div_y, div_p)

                        dia = skia.Path()
                        dia.moveTo(960.0 * sx, div_y - 5.0 * sy)
                        dia.lineTo(965.0 * sx, div_y)
                        dia.lineTo(960.0 * sx, div_y + 5.0 * sy)
                        dia.lineTo(955.0 * sx, div_y)
                        dia.close()
                        p_dia = skia.Paint(Color=skia.Color4f(1.0, 0.88, 0.35, 1.0 * shot_d_fade), AntiAlias=True)
                        canvas.drawPath(dia, p_dia)

                        # 4. Line 2: "YOU WILL SEE IT."
                        l2_fade = min(1.0, max(0.0, (t - (shot_d_st + 0.35)) / 0.7)) if t >= shot_d_st + 0.35 else 0.0
                        if t > 40.5:
                            l2_fade *= max(0.0, (41.13 - t) / 0.63)

                        if l2_fade > 0:
                            l2_font = skia.Font(tf_sans_bold, 86.0 * sx)
                            l2_y = 610.0 * sy

                            p_l2_glow_wide = skia.Paint(
                                Color=skia.Color4f(0.0, 0.80, 1.0, 0.45 * l2_fade),
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 20.0 * sx),
                                AntiAlias=True,
                            )
                            p_l2_glow_tight = skia.Paint(
                                Color=skia.Color4f(1.0, 0.85, 0.30, 0.75 * l2_fade),
                                MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0 * sx),
                                AntiAlias=True,
                            )
                            p_l2_core = skia.Paint(
                                Color=skia.Color4f(1.0, 1.0, 1.0, 1.0 * l2_fade),
                                AntiAlias=True,
                            )

                            _draw_letterspaced(canvas, "YOU WILL SEE IT.", 960.0 * sx, l2_y, l2_font, p_l2_glow_wide, 6.0 * sx)
                            _draw_letterspaced(canvas, "YOU WILL SEE IT.", 960.0 * sx, l2_y, l2_font, p_l2_glow_tight, 6.0 * sx)
                            _draw_letterspaced(canvas, "YOU WILL SEE IT.", 960.0 * sx, l2_y, l2_font, p_l2_core, 6.0 * sx)

                snapshot = surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_02(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build Scene 02: Real-World Rates & The 7-Minute Roadmap."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            # Scene 02 starts at 25.99s and ends at 67.12s in the master audio
            scene.add_audio(str(p), start=0.0, trim_start=25.99, trim_end=67.12)

    viewport = Viewport(RealWorldRatesRoadmapSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_02_DURATION)
    return scene
