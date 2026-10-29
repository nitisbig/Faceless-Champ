"""Scene 05: The Function Machine Pipeline (y = f(g(x))).

Timecode: 00:02:11,990 --> 00:02:40,630 (Duration: 28.64s)
Engine: skia-python (Canvas, Scene, Viewport) + LaTeX MathTex Typography (Computer Modern)

Key Mechanics & Aesthetics:
- Transition from Chapter 2: Mechanical gears smoothly dissolve into glowing particles.
- Two futuristic glassmorphic function processors materialize side-by-side:
  - Machine g (Electric Cyan, intake funnel, internal silicon grid, rotating reticle).
  - Machine f (Laser Coral & Radiant Gold, exhaust nozzle, internal dials).
- Transparent illuminated glass conduit pipe connecting Machine g to Machine f.
- Complete data journey animation:
  - Input capsule x glides into Machine g.
  - Intermediate capsule u emerges and travels along the glass conduit pipe into Machine f.
  - Output capsule y emerges from Machine f and hovers at the destination.
- Overhead master composite equation: y = f(g(x)) revealed with a progressive laser wipe.
- The Nudge Question:
  - Emerald vector nudge Delta x at the input.
  - High-arching Laser Mint question arc spanning across both machines: Delta y / Delta x = ?
  - Local rate badges underneath processors: Delta u / Delta x and Delta y / Delta u.
- Zero sentence text clutter on a pure #000000 void canvas.
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

SCENE_05_DURATION: float = 28.64

# High-Contrast Sharp Neon RGB Color Palette
CYAN = "#00F5FF"   # Electric Laser Cyan (Machine g / Input x)
GOLD = "#FFB800"   # Rich Deep Radiant Gold (Intermediate u / Pipe conduit / Shell f)
WHITE = "#FFFFFF"  # Pure Brilliant White (Operators & Specular highlights)
MINT = "#05FFA1"   # High-Voltage Neon Mint (The Nudge Delta x / Question)
CORAL = "#FF2A6D"  # Laser Neon Coral (Machine f / Output y)


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
    """Draw a precompiled LaTeX formula centered at (cx, cy) with bilinear filtering."""
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
class FunctionMachineSource:
    """Animation source for Scene 05: The Function Machine Pipeline (y = f(g(x)))."""

    intrinsic_size: tuple[int, int] = (1920, 1080)
    duration: float = SCENE_05_DURATION
    fingerprint: str = "chain:scene-05:function-machine-pipeline:v1"
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

        assets_dir = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "fonts"
        cg_font_path = assets_dir / "CormorantGaramond[wght].ttf"
        sg_font_path = assets_dir / "SpaceGrotesk[wght].ttf"

        tf_serif_bold = _make_weighted_tf(cg_font_path, 700.0, "serif")
        tf_sans_bold = _make_weighted_tf(sg_font_path, 700.0, "sans-serif")
        tf_sans_med = _make_weighted_tf(sg_font_path, 500.0, "sans-serif")

        # Precompile all LaTeX formulas once at startup (matching euler_scene.py)
        formulas_dict = {
            # Machine labels
            "label_g": [(r"$g$", CYAN)],
            "label_f": [(r"$f$", CORAL)],
            # Data capsules
            "capsule_x": [(r"$x$", CYAN)],
            "capsule_u": [(r"$u$", GOLD)],
            "capsule_y": [(r"$y$", CORAL)],
            # Composite formula: y = f( g( x ) )
            "composite_formula": [
                (r"$y$", CORAL),
                ("$=$", WHITE),
                (r"$f($", GOLD),
                (r"$g($", CYAN),
                (r"$x$", CYAN),
                (r"$)$", CYAN),
                (r"$)$", GOLD),
            ],
            # Nudge badges
            "nudge_dx": [(r"$\Delta x$", MINT)],
            "nudge_du": [(r"$\Delta u$", GOLD)],
            "nudge_dy": [(r"$\Delta y$", CORAL)],
            # Question arc formula: \frac{\Delta y}{\Delta x} = ?
            "question_nudge": [
                (r"$\frac{\Delta y}{\Delta x}$", MINT),
                ("$=$", WHITE),
                (r"$?$", GOLD),
            ],
            # Local rate badges
            "rate_g": [(r"$\frac{\Delta u}{\Delta x}$", CYAN)],
            "rate_f": [(r"$\frac{\Delta y}{\Delta u}$", CORAL)],
        }

        math_cache: dict[str, skia.Image] = {}
        for name, terms in formulas_dict.items():
            if "composite" in name or "question" in name:
                f_size = 42
            elif "rate" in name:
                f_size = 34
            elif "capsule" in name or "nudge" in name:
                f_size = 32
            elif "label" in name:
                f_size = 54
            else:
                f_size = 28
            math_cache[name] = _compose_latex_equation(terms, font_size=f_size)

        # Layout Geometry
        bg_black = skia.Color4f(0.0, 0.0, 0.0, 1.0)
        c_cyan_rgb = skia.Color4f(0.0, 0.96, 1.0, 1.0)
        c_gold_rgb = skia.Color4f(1.0, 0.72, 0.0, 1.0)
        c_coral_rgb = skia.Color4f(1.0, 0.16, 0.43, 1.0)
        c_mint_rgb = skia.Color4f(0.02, 1.0, 0.63, 1.0)

        # Processors Centerline Axis
        y_mach = 560.0 * sy
        x_g = 680.0 * sx
        x_f = 1240.0 * sx
        mach_w = 230.0 * sx
        mach_h = 170.0 * sy
        mach_r = 24.0 * sx

        # Conduit pipe span between processors
        pipe_x1 = x_g + mach_w * 0.5
        pipe_x2 = x_f - mach_w * 0.5
        pipe_h = 44.0 * sy

        class Session:
            def frame(self, t: float) -> Image.Image:
                canvas.clear(bg_black)

                scene_fade = min(1.0, max(0.0, t / 0.8))

                # Helper to draw a glassmorphic pill container
                def draw_pill(cx: float, cy: float, img: skia.Image, color_rgb: skia.Color4f, alpha: float, scale: float = 0.52):
                    if alpha <= 0.01:
                        return
                    pw = img.width() * scale + 26.0 * sx
                    ph = img.height() * scale + 14.0 * sy
                    pill_rect = skia.Rect.MakeXYWH(cx - pw * 0.5, cy - ph * 0.5, pw, ph)
                    pill_r = ph * 0.5
                    # Dark glass core
                    canvas.drawRoundRect(pill_rect, pill_r, pill_r, skia.Paint(Color=skia.Color4f(0.01, 0.02, 0.05, 0.92 * alpha), AntiAlias=True))
                    # Soft neon blur outline
                    canvas.drawRoundRect(
                        pill_rect, pill_r, pill_r,
                        skia.Paint(
                            Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.45 * alpha),
                            StrokeWidth=3.5 * sx,
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 5.0 * sx),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ),
                    )
                    # Crisp border
                    canvas.drawRoundRect(
                        pill_rect, pill_r, pill_r,
                        skia.Paint(
                            Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.92 * alpha),
                            StrokeWidth=1.5 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ),
                    )
                    _draw_math_centered(canvas, img, cx, cy, alpha=alpha, base_scale=scale)

                # -----------------------------------------------------------
                # 0. Dissolving Gear Particles (Transition from Scene 04)
                # 0.0s - 3.5s
                # -----------------------------------------------------------
                if t < 3.5:
                    part_fade = max(0.0, 1.0 - t / 3.0)
                    for i in range(24):
                        seed = i * 137.5
                        p_rad = 90.0 * sx + (seed % 140.0) * sx + (t * 40.0 * sx)
                        p_ang = math.radians(seed * 3.7 + t * 20.0)
                        px = (960.0 * sx) + p_rad * math.cos(p_ang)
                        py = y_mach + (p_rad * 0.6) * math.sin(p_ang)
                        p_sz = (2.5 + (seed % 3.0)) * sx
                        p_col = c_cyan_rgb if i % 3 == 0 else (c_gold_rgb if i % 3 == 1 else c_coral_rgb)
                        canvas.drawCircle(
                            px, py, p_sz,
                            skia.Paint(Color=skia.Color4f(p_col.fR, p_col.fG, p_col.fB, 0.60 * part_fade), AntiAlias=True)
                        )

                # -----------------------------------------------------------
                # 1. SHOT 05A: The Function Processors Materialize (0.0s - 8.5s)
                # -----------------------------------------------------------
                # Processors fade and settle into place (0.5s - 2.5s)
                p_mach_in = min(1.0, max(0.0, (t - 0.6) / 1.8))
                mach_ease = 1.0 - (1.0 - p_mach_in) ** 3
                mach_alpha = mach_ease * scene_fade

                # Subtle breathing offset
                y_offset = (1.0 - mach_ease) * 30.0 * sy

                # Helper to draw a CAD-grade Glassmorphic Function Processor
                def draw_function_processor(
                    cx: float, cy: float, w_box: float, h_box: float,
                    label_img: skia.Image, color_rgb: skia.Color4f, alpha: float,
                    pulse_val: float, has_intake: bool, has_exhaust: bool,
                ):
                    if alpha <= 0.01:
                        return

                    left = cx - w_box * 0.5
                    top = cy - h_box * 0.5
                    right = cx + w_box * 0.5
                    bottom = cy + h_box * 0.5
                    rect = skia.Rect.MakeXYWH(left, top, w_box, h_box)

                    # Ambient radial halo
                    halo_r = max(w_box, h_box) * 1.1
                    canvas.drawCircle(
                        cx, cy, halo_r,
                        skia.Paint(
                            Shader=skia.GradientShader.MakeRadial(
                                (cx, cy), halo_r,
                                [
                                    skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.16 * alpha * (1.0 + pulse_val * 0.4)),
                                    skia.Color4f(0.0, 0.0, 0.0, 0.0),
                                ],
                                [0.0, 1.0],
                            ),
                            AntiAlias=True,
                        ),
                    )

                    # Intake Funnel (Left Port)
                    if has_intake:
                        funnel_p = skia.Path()
                        funnel_w = 40.0 * sx
                        funnel_mouth = 70.0 * sy
                        funnel_neck = 36.0 * sy
                        funnel_p.moveTo(left - funnel_w, cy - funnel_mouth * 0.5)
                        funnel_p.lineTo(left, cy - funnel_neck * 0.5)
                        funnel_p.lineTo(left, cy + funnel_neck * 0.5)
                        funnel_p.lineTo(left - funnel_w, cy + funnel_mouth * 0.5)
                        funnel_p.close()

                        # Dark fill
                        canvas.drawPath(funnel_p, skia.Paint(Color=skia.Color4f(0.02, 0.04, 0.08, 0.90 * alpha), AntiAlias=True))
                        # Glowing contour
                        canvas.drawPath(
                            funnel_p,
                            skia.Paint(
                                Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.70 * alpha),
                                StrokeWidth=1.5 * sx,
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            ),
                        )
                        # Inward directional chevrons
                        chv_p = skia.Paint(Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.55 * alpha), StrokeWidth=1.5 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                        for k in range(2):
                            kx = left - 26.0 * sx + k * 14.0 * sx
                            p_ch = skia.Path()
                            p_ch.moveTo(kx - 6.0 * sx, cy - 10.0 * sy)
                            p_ch.lineTo(kx, cy)
                            p_ch.lineTo(kx - 6.0 * sx, cy + 10.0 * sy)
                            canvas.drawPath(p_ch, chv_p)

                    # Exhaust / Output Nozzle (Right Port)
                    if has_exhaust:
                        nozzle_p = skia.Path()
                        nozzle_w = 40.0 * sx
                        nozzle_neck = 36.0 * sy
                        nozzle_mouth = 56.0 * sy
                        nozzle_p.moveTo(right, cy - nozzle_neck * 0.5)
                        nozzle_p.lineTo(right + nozzle_w, cy - nozzle_mouth * 0.5)
                        nozzle_p.lineTo(right + nozzle_w, cy + nozzle_mouth * 0.5)
                        nozzle_p.lineTo(right, cy + nozzle_neck * 0.5)
                        nozzle_p.close()

                        canvas.drawPath(nozzle_p, skia.Paint(Color=skia.Color4f(0.02, 0.04, 0.08, 0.90 * alpha), AntiAlias=True))
                        canvas.drawPath(
                            nozzle_p,
                            skia.Paint(
                                Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.70 * alpha),
                                StrokeWidth=1.5 * sx,
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            ),
                        )
                        # Outward directional chevrons
                        chv_p = skia.Paint(Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.55 * alpha), StrokeWidth=1.5 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                        for k in range(2):
                            kx = right + 14.0 * sx + k * 14.0 * sx
                            p_ch = skia.Path()
                            p_ch.moveTo(kx - 6.0 * sx, cy - 10.0 * sy)
                            p_ch.lineTo(kx, cy)
                            p_ch.lineTo(kx - 6.0 * sx, cy + 10.0 * sy)
                            canvas.drawPath(p_ch, chv_p)

                    # Main Glass Processor Chassis
                    canvas.drawRoundRect(rect, mach_r, mach_r, skia.Paint(Color=skia.Color4f(0.02, 0.03, 0.07, 0.94 * alpha), AntiAlias=True))

                    # Internal Silicon Circuit / Calibration Grid
                    grid_p = skia.Paint(Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.08 * alpha), StrokeWidth=1.0 * sx, AntiAlias=True)
                    for gx in range(int(left + 24.0 * sx), int(right - 20.0 * sx), int(22.0 * sx)):
                        canvas.drawLine(gx, top + 16.0 * sy, gx, bottom - 16.0 * sy, grid_p)
                    for gy in range(int(top + 24.0 * sy), int(bottom - 20.0 * sy), int(22.0 * sy)):
                        canvas.drawLine(left + 16.0 * sx, gy, right - 16.0 * sx, gy, grid_p)

                    # Neon Outer Blur Rim
                    canvas.drawRoundRect(
                        rect, mach_r, mach_r,
                        skia.Paint(
                            Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.35 * alpha),
                            StrokeWidth=4.0 * sx,
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6.0 * sx),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ),
                    )
                    # Crisp Vector Border
                    canvas.drawRoundRect(
                        rect, mach_r, mach_r,
                        skia.Paint(
                            Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.90 * alpha),
                            StrokeWidth=1.8 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ),
                    )

                    # Top Edge Specular Reflection (Acrylic light-catch)
                    spec_p = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.65 * alpha), StrokeWidth=1.2 * sx, AntiAlias=True)
                    canvas.drawLine(left + mach_r, top + 2.0 * sy, right - mach_r, top + 2.0 * sy, spec_p)

                    # Center Rotating Mechanism / Reticle Dial
                    dial_r = 44.0 * sx
                    canvas.drawCircle(cx, cy, dial_r, skia.Paint(Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.06 * alpha), AntiAlias=True))
                    canvas.drawCircle(
                        cx, cy, dial_r,
                        skia.Paint(
                            Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.40 * alpha),
                            StrokeWidth=1.2 * sx,
                            PathEffect=skia.DashPathEffect.Make([4.0 * sx, 4.0 * sx], -(t * 15.0 * sx)),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ),
                    )

                    # Center Reticle Crosshairs
                    ch_p = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.25 * alpha), StrokeWidth=1.0 * sx, AntiAlias=True)
                    canvas.drawLine(cx - dial_r * 1.15, cy, cx + dial_r * 1.15, cy, ch_p)
                    canvas.drawLine(cx, cy - dial_r * 1.15, cx, cy + dial_r * 1.15, ch_p)

                    # Center Insignia (g or f)
                    _draw_math_centered(canvas, label_img, cx, cy, alpha=alpha, base_scale=0.60)

                    # Corner Precision Tick Bolts
                    corner_dot_p = skia.Paint(Color=skia.Color4f(color_rgb.fR, color_rgb.fG, color_rgb.fB, 0.80 * alpha), AntiAlias=True)
                    pad = 12.0 * sx
                    canvas.drawCircle(left + pad, top + pad, 2.2 * sx, corner_dot_p)
                    canvas.drawCircle(right - pad, top + pad, 2.2 * sx, corner_dot_p)
                    canvas.drawCircle(left + pad, bottom - pad, 2.2 * sx, corner_dot_p)
                    canvas.drawCircle(right - pad, bottom - pad, 2.2 * sx, corner_dot_p)

                # Processors Processing Pulses
                pulse_g = 0.0
                pulse_f = 0.0
                if 10.8 <= t <= 12.0:
                    pulse_g = math.sin((t - 10.8) / 1.2 * math.pi)
                if 15.0 <= t <= 16.5:
                    pulse_f = math.sin((t - 15.0) / 1.5 * math.pi)

                # Draw Processors
                draw_function_processor(
                    x_g, y_mach + y_offset, mach_w, mach_h,
                    math_cache["label_g"], c_cyan_rgb, mach_alpha,
                    pulse_g, has_intake=True, has_exhaust=False,
                )
                draw_function_processor(
                    x_f, y_mach + y_offset, mach_w, mach_h,
                    math_cache["label_f"], c_coral_rgb, mach_alpha,
                    pulse_f, has_intake=False, has_exhaust=True,
                )

                # -----------------------------------------------------------
                # Transparent Illuminated Glass Conduit Pipe
                # -----------------------------------------------------------
                if mach_alpha > 0.01:
                    pipe_top = y_mach + y_offset - pipe_h * 0.5
                    pipe_bottom = y_mach + y_offset + pipe_h * 0.5
                    pipe_rect = skia.Rect.MakeLTRB(pipe_x1, pipe_top, pipe_x2, pipe_bottom)

                    # Glass core interior fill
                    canvas.drawRect(pipe_rect, skia.Paint(Color=skia.Color4f(0.01, 0.04, 0.10, 0.65 * mach_alpha), AntiAlias=True))

                    # Top and Bottom Specular Rails
                    p_glass_rim = skia.Paint(
                        Color=skia.Color4f(1.0, 0.72, 0.0, 0.55 * mach_alpha),
                        StrokeWidth=1.8 * sx,
                        AntiAlias=True,
                    )
                    canvas.drawLine(pipe_x1, pipe_top, pipe_x2, pipe_top, p_glass_rim)
                    canvas.drawLine(pipe_x1, pipe_bottom, pipe_x2, pipe_bottom, p_glass_rim)

                    # Center Laser Energy Track inside pipe
                    p_center_track = skia.Paint(
                        Color=skia.Color4f(1.0, 0.72, 0.0, 0.25 * mach_alpha),
                        StrokeWidth=1.0 * sx,
                        PathEffect=skia.DashPathEffect.Make([5.0 * sx, 4.0 * sx], -(t * 24.0 * sx)),
                        AntiAlias=True,
                    )
                    canvas.drawLine(pipe_x1, y_mach + y_offset, pipe_x2, y_mach + y_offset, p_center_track)

                    # Coupler Flanges
                    flange_p = skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.85 * mach_alpha), StrokeWidth=3.0 * sx, AntiAlias=True)
                    canvas.drawLine(pipe_x1, pipe_top - 4.0 * sy, pipe_x1, pipe_bottom + 4.0 * sy, flange_p)
                    canvas.drawLine(pipe_x2, pipe_top - 4.0 * sy, pipe_x2, pipe_bottom + 4.0 * sy, flange_p)
                    # Mid-span stabilizer ring
                    mid_x = (pipe_x1 + pipe_x2) * 0.5
                    canvas.drawLine(mid_x, pipe_top - 2.0 * sy, mid_x, pipe_bottom + 2.0 * sy, skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.45 * mach_alpha), StrokeWidth=1.5 * sx, AntiAlias=True))

                    # Traveling ambient photons inside pipe
                    for i in range(4):
                        p_frac = ((t * 0.75 + i * 0.25) % 1.0)
                        px = pipe_x1 + (pipe_x2 - pipe_x1) * p_frac
                        canvas.drawCircle(px, y_mach + y_offset, 2.5 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.80 * mach_alpha), AntiAlias=True))
                        canvas.drawCircle(
                            px, y_mach + y_offset, 6.0 * sx,
                            skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.40 * mach_alpha), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.0 * sx), AntiAlias=True)
                        )

                # -----------------------------------------------------------
                # 2. SHOT 05B: The Data Journey (8.5s - 18.5s)
                # Input x -> Intermediate u -> Output y
                # -----------------------------------------------------------
                # 2A. Capsule x (8.5s - 11.4s)
                # "A number, x, enters the first machine, which we call g."
                if 8.5 <= t < 11.5:
                    x_enter_p = min(1.0, max(0.0, (t - 8.6) / 2.2))
                    x_ease = x_enter_p ** 1.8
                    capsule_x_pos = 320.0 * sx + (x_g - 320.0 * sx) * x_ease
                    fade_x = min(1.0, (t - 8.5) / 0.4) * max(0.0, 1.0 - max(0.0, (t - 10.8) / 0.5)) * scene_fade

                    # Subtle suction particle trails into Machine g
                    for k in range(3):
                        trail_x = capsule_x_pos - (k + 1) * 16.0 * sx
                        canvas.drawCircle(
                            trail_x, y_mach, (4.0 - k) * sx,
                            skia.Paint(Color=skia.Color4f(0.0, 0.96, 1.0, 0.35 * fade_x), AntiAlias=True)
                        )
                    draw_pill(capsule_x_pos, y_mach, math_cache["capsule_x"], c_cyan_rgb, fade_x, scale=0.55)

                # 2B. Capsule u (11.4s - 15.5s)
                # "Out comes a new number, u. Then u enters the second machine, called f..."
                if 11.4 <= t < 15.5:
                    u_move_p = min(1.0, max(0.0, (t - 11.8) / 3.0))
                    u_ease = 0.5 - 0.5 * math.cos(u_move_p * math.pi)
                    capsule_u_pos = pipe_x1 + (x_f - pipe_x1) * u_ease
                    fade_u = min(1.0, (t - 11.4) / 0.4) * max(0.0, 1.0 - max(0.0, (t - 14.8) / 0.5)) * scene_fade

                    # Glowing stream trail inside the pipe
                    for k in range(3):
                        trail_u = capsule_u_pos - (k + 1) * 16.0 * sx
                        canvas.drawCircle(
                            trail_u, y_mach, (4.0 - k) * sx,
                            skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.40 * fade_u), AntiAlias=True)
                        )
                    draw_pill(capsule_u_pos, y_mach, math_cache["capsule_u"], c_gold_rgb, fade_u, scale=0.55)

                # 2C. Capsule y (16.0s - 28.64s)
                # "...and out comes the final number, y."
                if t >= 16.0:
                    y_out_p = min(1.0, max(0.0, (t - 16.2) / 1.8))
                    y_ease = 1.0 - (1.0 - y_out_p) ** 2.5
                    capsule_y_pos = (x_f + mach_w * 0.5) + (1520.0 * sx - (x_f + mach_w * 0.5)) * y_ease
                    fade_y = min(1.0, (t - 16.0) / 0.4) * scene_fade

                    # Subtle emission flash at 16.2s
                    if 16.2 <= t <= 17.0:
                        fl_y = 1.0 - (t - 16.2) / 0.8
                        canvas.drawCircle(
                            x_f + mach_w * 0.5, y_mach, 40.0 * sx * (1.0 + (1.0 - fl_y)),
                            skia.Paint(Color=skia.Color4f(1.0, 0.16, 0.43, 0.75 * fl_y), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 8.0 * sx), AntiAlias=True)
                        )

                    draw_pill(capsule_y_pos, y_mach, math_cache["capsule_y"], c_coral_rgb, fade_y, scale=0.58)

                # Static input capsule x remaining in position for Shot 05C
                if t >= 18.0:
                    fade_x_static = min(1.0, (t - 18.0) / 0.5) * scene_fade
                    draw_pill(340.0 * sx, y_mach, math_cache["capsule_x"], c_cyan_rgb, fade_x_static, scale=0.55)

                # -----------------------------------------------------------
                # 3. SHOT 05C: Composite Formula Reveal (18.5s - 28.64s)
                # "So y equals f of g of x. A function inside a function."
                # -----------------------------------------------------------
                if t >= 18.5:
                    comp_fade = min(1.0, (t - 18.5) / 0.6) * scene_fade
                    f_cx = 960.0 * sx
                    f_cy = 210.0 * sy

                    comp_img = math_cache["composite_formula"]
                    comp_scale = 0.76
                    cw = comp_img.width() * comp_scale * sx
                    ch = comp_img.height() * comp_scale * sy
                    c_left = f_cx - cw * 0.5
                    c_top = f_cy - ch * 0.5

                    # Progressive Laser Materialization Wipe (18.5s - 20.8s)
                    p_comp_wipe = min(1.0, max(0.0, (t - 18.5) / 2.2))
                    comp_wipe_ease = 0.5 - 0.5 * math.cos(p_comp_wipe * math.pi)

                    # Ambient radial glow behind composite formula
                    canvas.drawCircle(
                        f_cx, f_cy, 380.0 * sx,
                        skia.Paint(
                            Shader=skia.GradientShader.MakeRadial(
                                (f_cx, f_cy), 380.0 * sx,
                                [skia.Color4f(1.0, 0.72, 0.0, 0.14 * comp_fade), skia.Color4f(0.0, 0.0, 0.0, 0.0)],
                                [0.0, 1.0],
                            ),
                            AntiAlias=True,
                        ),
                    )

                    # Clip canvas for progressive reveal
                    canvas.save()
                    canvas.clipRect(
                        skia.Rect.MakeLTRB(c_left - 10.0 * sx, c_top - 10.0 * sy, c_left + cw * comp_wipe_ease, c_top + ch + 10.0 * sy),
                        skia.ClipOp.kIntersect,
                        True,
                    )
                    _draw_math_centered(canvas, comp_img, f_cx, f_cy, alpha=comp_fade, base_scale=comp_scale)
                    canvas.restore()

                    # Laser Cursor while wiping
                    if 0.01 < comp_wipe_ease < 0.99:
                        x_claser = c_left + cw * comp_wipe_ease
                        canvas.drawLine(
                            x_claser, c_top - 6.0 * sy, x_claser, c_top + ch + 6.0 * sy,
                            skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.90), StrokeWidth=3.0 * sx, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0 * sx), AntiAlias=True)
                        )
                        canvas.drawLine(x_claser, c_top - 6.0 * sy, x_claser, c_top + ch + 6.0 * sy, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.95), StrokeWidth=1.4 * sx, AntiAlias=True))
                        canvas.drawCircle(x_claser, f_cy, 5.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.95), AntiAlias=True))

                    # Golden Caliper Divider below formula (draws outward from center)
                    if t >= 19.5:
                        p_cdiv = min(1.0, (t - 19.5) / 0.7)
                        div_c_ease = 1.0 - (1.0 - p_cdiv) ** 3
                        div_y = 295.0 * sy
                        cdiv_half = 240.0 * sx * div_c_ease

                        canvas.drawLine(
                            f_cx - cdiv_half, div_y, f_cx - 7.0 * sx, div_y,
                            skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.55 * comp_fade), StrokeWidth=1.5 * sx, AntiAlias=True)
                        )
                        canvas.drawLine(
                            f_cx + 7.0 * sx, div_y, f_cx + cdiv_half, div_y,
                            skia.Paint(Color=skia.Color4f(1.0, 0.72, 0.0, 0.55 * comp_fade), StrokeWidth=1.5 * sx, AntiAlias=True)
                        )
                        # Center diamond
                        canvas.save()
                        canvas.translate(f_cx, div_y)
                        canvas.rotate(45.0 * div_c_ease)
                        canvas.drawRect(
                            skia.Rect.MakeXYWH(-3.5 * sx, -3.5 * sx, 7.0 * sx, 7.0 * sx),
                            skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.90 * comp_fade), AntiAlias=True)
                        )
                        canvas.restore()

                    # Nested Function Underline Bracket (g(x) inside f)
                    if t >= 20.8:
                        nest_alpha = min(1.0, (t - 20.8) / 0.6) * comp_fade
                        # g(x) is between ~48% and ~80% of composite formula width
                        gx_left = c_left + cw * 0.48
                        gx_right = c_left + cw * 0.82
                        b_y = f_cy + ch * 0.5 + 4.0 * sy

                        p_bracket = skia.Path()
                        p_bracket.moveTo(gx_left, b_y)
                        p_bracket.lineTo(gx_left, b_y + 6.0 * sy)
                        p_bracket.lineTo((gx_left + gx_right) * 0.5 - 4.0 * sx, b_y + 6.0 * sy)
                        p_bracket.lineTo((gx_left + gx_right) * 0.5, b_y + 11.0 * sy)
                        p_bracket.lineTo((gx_left + gx_right) * 0.5 + 4.0 * sx, b_y + 6.0 * sy)
                        p_bracket.lineTo(gx_right, b_y + 6.0 * sy)
                        p_bracket.lineTo(gx_right, b_y)

                        canvas.drawPath(
                            p_bracket,
                            skia.Paint(Color=skia.Color4f(0.0, 0.96, 1.0, 0.85 * nest_alpha), StrokeWidth=1.5 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                        )

                # Local Processor Rate Badges (below machines at y = 700)
                if t >= 21.0:
                    badge_fade = min(1.0, (t - 21.0) / 0.6) * scene_fade
                    draw_pill(x_g, 695.0 * sy, math_cache["rate_g"], c_cyan_rgb, badge_fade, scale=0.55)
                    draw_pill(x_f, 695.0 * sy, math_cache["rate_f"], c_coral_rgb, badge_fade, scale=0.55)

                # -----------------------------------------------------------
                # 4. The Traveling Nudge Question (23.5s - 28.64s)
                # "We want to know: if we nudge x by a tiny amount, how much does y move?"
                # -----------------------------------------------------------
                if t >= 23.5:
                    nudge_fade = min(1.0, (t - 23.5) / 0.6) * scene_fade

                    # Emerald Nudge Vector Delta x at Input (x = 340)
                    in_x = 340.0 * sx
                    draw_pill(in_x, y_mach + 54.0 * sy, math_cache["nudge_dx"], c_mint_rgb, nudge_fade, scale=0.55)

                    # Dynamic Nudge Arrow pushing Input Capsule
                    arrow_pulse = 0.5 + 0.5 * math.sin(t * 8.0)
                    p_arrow = skia.Paint(Color=skia.Color4f(0.02, 1.0, 0.63, 0.90 * nudge_fade), StrokeWidth=2.4 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
                    arr_x1 = in_x - 36.0 * sx + arrow_pulse * 6.0 * sx
                    arr_x2 = in_x - 14.0 * sx + arrow_pulse * 6.0 * sx
                    canvas.drawLine(arr_x1, y_mach, arr_x2, y_mach, p_arrow)
                    arr_head = skia.Path()
                    arr_head.moveTo(arr_x2 - 5.0 * sx, y_mach - 5.0 * sy)
                    arr_head.lineTo(arr_x2, y_mach)
                    arr_head.lineTo(arr_x2 - 5.0 * sx, y_mach + 5.0 * sy)
                    canvas.drawPath(arr_head, p_arrow)

                    # High-Arching Nudge Question Trajectory: Delta x -> y
                    q_start = (in_x, y_mach - 40.0 * sy)
                    q_end = (1520.0 * sx, y_mach - 40.0 * sy)
                    q_apex = (960.0 * sx, 350.0 * sy)

                    arc_nudge = skia.Path()
                    arc_nudge.moveTo(q_start[0], q_start[1])
                    arc_nudge.quadTo(q_apex[0], q_apex[1], q_end[0], q_end[1])

                    # Glowing Mint Stroke
                    canvas.drawPath(
                        arc_nudge,
                        skia.Paint(
                            Color=skia.Color4f(0.02, 1.0, 0.63, 0.35 * nudge_fade),
                            StrokeWidth=3.5 * sx,
                            PathEffect=skia.DashPathEffect.Make([8.0 * sx, 5.0 * sx], -(t * 35.0 * sx)),
                            Style=skia.Paint.kStroke_Style,
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0 * sx),
                            AntiAlias=True,
                        ),
                    )
                    canvas.drawPath(
                        arc_nudge,
                        skia.Paint(
                            Color=skia.Color4f(0.02, 1.0, 0.63, 0.85 * nudge_fade),
                            StrokeWidth=1.6 * sx,
                            PathEffect=skia.DashPathEffect.Make([8.0 * sx, 5.0 * sx], -(t * 35.0 * sx)),
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ),
                    )

                    # Traveling Emerald Photons along Question Arc
                    for i in range(4):
                        u_arc = ((t * 0.8 + i * 0.25) % 1.0)
                        ux = (1.0 - u_arc)**2 * q_start[0] + 2.0 * (1.0 - u_arc) * u_arc * q_apex[0] + u_arc**2 * q_end[0]
                        uy = (1.0 - u_arc)**2 * q_start[1] + 2.0 * (1.0 - u_arc) * u_arc * q_apex[1] + u_arc**2 * q_end[1]
                        canvas.drawCircle(ux, uy, 3.5 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, 0.95 * nudge_fade), AntiAlias=True))
                        canvas.drawCircle(ux, uy, 8.0 * sx, skia.Paint(Color=skia.Color4f(0.02, 1.0, 0.63, 0.60 * nudge_fade), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.0 * sx), AntiAlias=True))

                    # Hero Question Formula Badge at Arc Apex: Delta y / Delta x = ?
                    draw_pill(960.0 * sx, 365.0 * sy, math_cache["question_nudge"], c_mint_rgb, nudge_fade, scale=0.68)

                snapshot = surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_05(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build Scene 05: The Function Machine Pipeline (y = f(g(x)))."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            # Scene 05 starts at 131.99s and ends at 160.63s in the master audio
            scene.add_audio(str(p), start=0.0, trim_start=131.99, trim_end=160.63)

    viewport = Viewport(FunctionMachineSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_05_DURATION)
    return scene
