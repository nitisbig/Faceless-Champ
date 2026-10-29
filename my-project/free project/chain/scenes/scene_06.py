"""Scene 06: The Traveling Nudge: Number Lines & Local Stretches.

Timecode: 00:02:40,630 --> 00:03:12,160 (Duration: 31.53s)
Engine: skia-python (Canvas, Scene, Viewport) + LaTeX MathTex Typography (Computer Modern)

Key Mechanics & Aesthetics:
- Three precision horizontal number lines stacked vertically:
  - Top Line: Variable x (Electric Cyan #00F5FF, input slider at y=280).
  - Middle Line: Variable u (Radiant Gold #FFB800, intermediate slider at y=500).
  - Bottom Line: Variable y (Laser Coral #FF2A6D, output slider at y=720).
- Minor graduation ticks, glowing origin marker at x0=580, and resting vertical alignment beam.
- The Input Nudge:
  - Vector arrow pushes slider x forward by +80px with precision caliper bracket Δx.
- The First Stretch:
  - Vertical projection laser drops to middle line; Machine g stretches displacement 2x (+160px).
  - Amber caliper bracket encloses Δu = 2·Δx; floating gauge displays Machine g Rate = Δu / Δx = 2.
- The Second Stretch:
  - Vertical projection laser drops to bottom line; Machine f stretches displacement 3x (+480px).
  - Coral caliper bracket encloses Δy = 3·Δu; floating gauge displays Machine f Rate = Δy / Δu = 3.
- The Compounding Chain Climax:
  - High-voltage Neon Mint energy pulse cascades through Δx -> Δu -> Δy.
  - Master composite formula materializes overhead: Δy / Δx = (Δy / Δu) · (Δu / Δx) = 3 · 2 = 6.
  - Zero sentence text clutter on a pure #000000 void canvas.
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

SCENE_06_DURATION: float = 31.53

# High-Contrast Sharp Neon RGB Color Palette
CYAN = "#00F5FF"   # Electric Laser Cyan (Line x / Machine g)
GOLD = "#FFB800"   # Rich Deep Radiant Gold (Line u / Intermediate)
WHITE = "#FFFFFF"  # Pure Brilliant White (Axes / Ticks / Values)
MINT = "#05FFA1"   # High-Voltage Neon Mint (Nudge Δx / Energy Pulses)
CORAL = "#FF2A6D"  # Laser Neon Coral (Line y / Machine f)


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
    """Draw a precompiled LaTeX formula centered at (cx, cy) with bilinear retina filtering."""
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
class TravelingNudgeSource:
    """Animation source for Scene 06: The Traveling Nudge: Number Lines & Local Stretches."""

    intrinsic_size: tuple[int, int] = (1920, 1080)
    duration: float = SCENE_06_DURATION
    fingerprint: str = "chain:scene-06:traveling-nudge:v1"
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

        img_sym_x = _compose_latex_equation([(r"$x$", CYAN)], font_size=36.0, dpi=dpi)
        img_sym_u = _compose_latex_equation([(r"$u$", GOLD)], font_size=36.0, dpi=dpi)
        img_sym_y = _compose_latex_equation([(r"$y$", CORAL)], font_size=36.0, dpi=dpi)

        img_sym_g = _compose_latex_equation([(r"$\mathit{g}$", CYAN)], font_size=26.0, dpi=dpi)
        img_sym_f = _compose_latex_equation([(r"$\mathit{f}$", CORAL)], font_size=26.0, dpi=dpi)

        img_badge_dx = _compose_latex_equation([(r"$\Delta x$", MINT)], font_size=24.0, dpi=dpi)
        img_badge_du = _compose_latex_equation([(r"$\Delta u = 2\,\Delta x$", GOLD)], font_size=24.0, dpi=dpi)
        img_badge_dy = _compose_latex_equation([(r"$\Delta y = 3\,\Delta u$", CORAL)], font_size=24.0, dpi=dpi)

        img_rate_g = _compose_latex_equation([
            (r"$\frac{\Delta u}{\Delta x}$", CYAN),
            ("$=$", WHITE),
            (r"$2$", CYAN),
            (r"$(\times 2)$", GOLD),
        ], font_size=26.0, dpi=dpi, spacing=10)

        img_rate_f = _compose_latex_equation([
            (r"$\frac{\Delta y}{\Delta u}$", CORAL),
            ("$=$", WHITE),
            (r"$3$", CORAL),
            (r"$(\times 3)$", GOLD),
        ], font_size=26.0, dpi=dpi, spacing=10)

        img_hero_eq = _compose_latex_equation([
            (r"$\frac{\Delta y}{\Delta x}$", MINT),
            ("$=$", WHITE),
            (r"$\frac{\Delta y}{\Delta u}$", CORAL),
            (r"$\cdot$", WHITE),
            (r"$\frac{\Delta u}{\Delta x}$", CYAN),
            ("$=$", WHITE),
            (r"$3$", CORAL),
            (r"$\times$", WHITE),
            (r"$2$", CYAN),
            ("$=$", WHITE),
            (r"$6$", MINT),
        ], font_size=34.0, dpi=dpi, spacing=12)

        # Axis Layout Geometry
        AXIS_X_MIN = 220.0
        AXIS_X_MAX = 1720.0
        ORIGIN_X = 580.0
        DX_STEP = 80.0     # Step for Δx (+80px -> x1 = 660)
        DU_STEP = 160.0    # Step for Δu (2x -> +160px -> u1 = 740)
        DY_STEP = 480.0    # Step for Δy (3x -> +480px -> y1 = 1060)

        Y_LINE_X = 280.0
        Y_LINE_U = 500.0
        Y_LINE_Y = 720.0

        def _draw_micro_gear(cx: float, cy: float, radius: float, num_teeth: int, rot_rad: float, color_hex: str, img_sym: skia.Image, alpha: float):
            if alpha <= 0.0:
                return
            # Ambient radial glow & outer chassis ring
            glow_paint = skia.Paint(Color=_skia_color(color_hex, alpha * 0.16), Style=skia.Paint.kStroke_Style, StrokeWidth=5.0 * sx, AntiAlias=True)
            ring_paint = skia.Paint(Color=_skia_color(color_hex, alpha * 0.85), Style=skia.Paint.kStroke_Style, StrokeWidth=1.5 * sx, AntiAlias=True)
            canvas.drawCircle(cx, cy, radius * sx, glow_paint)
            canvas.drawCircle(cx, cy, radius * sx, ring_paint)

            # Precision gear teeth
            tooth_w = (2.0 * math.pi * radius / (num_teeth * 2.0)) * 0.75 * sx
            tooth_h = 5.5 * sx
            tooth_p = skia.Paint(Color=_skia_color(color_hex, alpha * 0.85), Style=skia.Paint.kFill_Style, AntiAlias=True)
            for i in range(num_teeth):
                angle = rot_rad + i * (2.0 * math.pi / num_teeth)
                tx = cx + radius * math.cos(angle) * sx
                ty = cy + radius * math.sin(angle) * sy
                canvas.save()
                canvas.translate(tx, ty)
                canvas.rotate(math.degrees(angle))
                t_rect = skia.Rect.MakeXYWH(-tooth_w * 0.5, -tooth_h * 0.5, tooth_w, tooth_h)
                canvas.drawRect(t_rect, tooth_p)
                canvas.restore()

            # Inner silicon core hub
            hub_bg = skia.Paint(Color=_skia_color("#080D14", alpha * 0.92), Style=skia.Paint.kFill_Style, AntiAlias=True)
            canvas.drawCircle(cx, cy, (radius * 0.65) * sx, hub_bg)
            canvas.drawCircle(cx, cy, (radius * 0.65) * sx, ring_paint)

            # Reticle crosshair ticks
            tick_p = skia.Paint(Color=_skia_color(WHITE, alpha * 0.40), StrokeWidth=1.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
            canvas.drawLine(cx - 5.0 * sx, cy, cx + 5.0 * sx, cy, tick_p)
            canvas.drawLine(cx, cy - 5.0 * sy, cx, cy + 5.0 * sy, tick_p)

            # Center symbol
            _draw_math_centered(canvas, img_sym, cx, cy, alpha=alpha, base_scale=0.55 * sx)

        class Session:
            def frame(self, t: float) -> Image.Image:
                # 1. Pure Pitch-Black Void
                canvas.clear(_skia_color("#000000", 1.0))

                # -------------------------------------------------------------
                # SHOT 06A (0.0s - 2.7s): Three Stacked Number Lines Materialize
                # Voice: "Watch the nudge travel. On the number line, we" (0.0s - 2.70s)
                # -------------------------------------------------------------
                draw_prog = _smoothstep(0.0, 1.8, t)
                axes_alpha = min(1.0, draw_prog * 1.2)
                ticks_alpha = _smoothstep(0.8, 2.0, t)

                cur_left = ORIGIN_X - (ORIGIN_X - AXIS_X_MIN) * draw_prog
                cur_right = ORIGIN_X + (AXIS_X_MAX - ORIGIN_X) * draw_prog

                lines_config = [
                    (Y_LINE_X, CYAN, img_sym_x),
                    (Y_LINE_U, GOLD, img_sym_u),
                    (Y_LINE_Y, CORAL, img_sym_y),
                ]

                # Draw horizontal laser rails & ticks
                for y_pos_raw, color_hex, img_sym in lines_config:
                    y_pos = y_pos_raw * sy

                    # Ambient glow rail (layered vector glow)
                    glow_outer = skia.Paint(
                        Color=_skia_color(color_hex, axes_alpha * 0.16),
                        StrokeWidth=6.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    glow_inner = skia.Paint(
                        Color=_skia_color(color_hex, axes_alpha * 0.35),
                        StrokeWidth=3.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(cur_left * sx, y_pos, cur_right * sx, y_pos, glow_outer)
                    canvas.drawLine(cur_left * sx, y_pos, cur_right * sx, y_pos, glow_inner)

                    # Sharp core rail
                    core_paint = skia.Paint(
                        Color=_skia_color(WHITE, axes_alpha * 0.8),
                        StrokeWidth=1.5 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(cur_left * sx, y_pos, cur_right * sx, y_pos, core_paint)

                    # Arrowhead on right tip
                    if draw_prog > 0.95:
                        tip_paint = skia.Paint(
                            Color=_skia_color(color_hex, axes_alpha * 0.85),
                            StrokeWidth=2.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        canvas.drawLine(AXIS_X_MAX * sx, y_pos, (AXIS_X_MAX - 10) * sx, y_pos - 6 * sy, tip_paint)
                        canvas.drawLine(AXIS_X_MAX * sx, y_pos, (AXIS_X_MAX - 10) * sx, y_pos + 6 * sy, tip_paint)

                    # Graduation ticks
                    if ticks_alpha > 0.0:
                        tick_paint = skia.Paint(
                            Color=_skia_color(WHITE, ticks_alpha * 0.35),
                            StrokeWidth=1.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        origin_tick_paint = skia.Paint(
                            Color=_skia_color(color_hex, ticks_alpha * 0.9),
                            StrokeWidth=2.5 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )

                        tick_start = int(math.ceil((cur_left - ORIGIN_X) / 40.0)) * 40 + int(ORIGIN_X)
                        for tx in range(tick_start, int(cur_right) + 1, 40):
                            if tx == int(ORIGIN_X):
                                # Prominent origin tick (height 20px)
                                canvas.drawLine(tx * sx, y_pos - 10 * sy, tx * sx, y_pos + 10 * sy, origin_tick_paint)
                            else:
                                is_major = (tx - int(ORIGIN_X)) % 80 == 0
                                th = 12 * sy if is_major else 6 * sy
                                canvas.drawLine(tx * sx, y_pos - th / 2, tx * sx, y_pos + th / 2, tick_paint)

                    # Left Variable Symbol (x, u, y)
                    if draw_prog > 0.2:
                        sym_alpha = _smoothstep(0.4, 1.8, t)
                        _draw_math_centered(canvas, img_sym, 150.0 * sx, y_pos, alpha=sym_alpha, base_scale=0.55 * sx)

                # -------------------------------------------------------------
                # Vertical Alignment Beam at Origin (x0 = 580)
                # -------------------------------------------------------------
                beam_alpha = _smoothstep(1.0, 2.2, t)
                if beam_alpha > 0.0:
                    beam_paint = skia.Paint(
                        Color=_skia_color(WHITE, beam_alpha * 0.22),
                        StrokeWidth=1.5 * sx,
                        PathEffect=skia.DashPathEffect.Make([4.0 * sx, 4.0 * sy], 0.0),
                        AntiAlias=True,
                    )
                    canvas.drawLine(ORIGIN_X * sx, (Y_LINE_X - 30) * sy, ORIGIN_X * sx, (Y_LINE_Y + 30) * sy, beam_paint)

                    diamond_paint = skia.Paint(
                        Color=_skia_color(WHITE, beam_alpha * 0.75),
                        Style=skia.Paint.kStroke_Style,
                        StrokeWidth=1.5 * sx,
                        AntiAlias=True,
                    )
                    for y_raw in [Y_LINE_X, Y_LINE_U, Y_LINE_Y]:
                        canvas.drawCircle(ORIGIN_X * sx, y_raw * sy, 3.0 * sx, diamond_paint)

                # Inner white pip paint for slider handles
                inner_pip = skia.Paint(Color=_skia_color(WHITE, 0.95), Style=skia.Paint.kFill_Style, AntiAlias=True)

                # -------------------------------------------------------------
                # SHOT 06B (2.7s - 7.5s): The Input Nudge Δx
                # Voice: "push X forward by a tiny step, which we call Delta X" (2.70s - 7.82s)
                # -------------------------------------------------------------
                nudge_prog = _smoothstep(2.7, 4.4, t)
                cur_x_pos = ORIGIN_X + DX_STEP * nudge_prog

                # Slider x handle
                slider_paint = skia.Paint(Color=_skia_color(CYAN, min(1.0, axes_alpha * 1.5)), Style=skia.Paint.kFill_Style, AntiAlias=True)
                slider_glow_outer = skia.Paint(Color=_skia_color(CYAN, 0.22 * axes_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True)
                slider_glow_mid = skia.Paint(Color=_skia_color(CYAN, 0.45 * axes_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True)
                canvas.drawCircle(cur_x_pos * sx, Y_LINE_X * sy, 11.0 * sx, slider_glow_outer)
                canvas.drawCircle(cur_x_pos * sx, Y_LINE_X * sy, 8.0 * sx, slider_glow_mid)
                canvas.drawCircle(cur_x_pos * sx, Y_LINE_X * sy, 5.0 * sx, slider_paint)
                canvas.drawCircle(cur_x_pos * sx, Y_LINE_X * sy, 2.0 * sx, inner_pip)

                # Displacement vector arrow Δx
                if nudge_prog > 0.01:
                    disp_glow_outer = skia.Paint(
                        Color=_skia_color(MINT, 0.25),
                        StrokeWidth=8.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    disp_glow_inner = skia.Paint(
                        Color=_skia_color(MINT, 0.50),
                        StrokeWidth=5.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    disp_core = skia.Paint(
                        Color=_skia_color(MINT, 0.95),
                        StrokeWidth=2.5 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(ORIGIN_X * sx, Y_LINE_X * sy, cur_x_pos * sx, Y_LINE_X * sy, disp_glow_outer)
                    canvas.drawLine(ORIGIN_X * sx, Y_LINE_X * sy, cur_x_pos * sx, Y_LINE_X * sy, disp_glow_inner)
                    canvas.drawLine(ORIGIN_X * sx, Y_LINE_X * sy, cur_x_pos * sx, Y_LINE_X * sy, disp_core)

                    ah_paint = skia.Paint(Color=_skia_color(MINT, 0.95), Style=skia.Paint.kFill_Style, AntiAlias=True)
                    ah_path = skia.Path()
                    ah_path.moveTo(cur_x_pos * sx, Y_LINE_X * sy)
                    ah_path.lineTo((cur_x_pos - 10) * sx, (Y_LINE_X - 5) * sy)
                    ah_path.lineTo((cur_x_pos - 8) * sx, Y_LINE_X * sy)
                    ah_path.lineTo((cur_x_pos - 10) * sx, (Y_LINE_X + 5) * sy)
                    ah_path.close()
                    canvas.drawPath(ah_path, ah_paint)

                # Caliper bracket for Δx
                caliper_dx_alpha = _smoothstep(4.0, 5.2, t)
                if caliper_dx_alpha > 0.0:
                    c_y = Y_LINE_X - 35
                    c_paint = skia.Paint(
                        Color=_skia_color(MINT, caliper_dx_alpha * 0.85),
                        StrokeWidth=1.5 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    c_path = skia.Path()
                    c_path.moveTo(ORIGIN_X * sx, (Y_LINE_X - 18) * sy)
                    c_path.lineTo(ORIGIN_X * sx, c_y * sy)
                    c_path.lineTo(cur_x_pos * sx, c_y * sy)
                    c_path.lineTo(cur_x_pos * sx, (Y_LINE_X - 18) * sy)
                    canvas.drawPath(c_path, c_paint)

                    mid_x = (ORIGIN_X + cur_x_pos) / 2.0
                    _draw_math_centered(canvas, img_badge_dx, mid_x * sx, (c_y - 20) * sy, alpha=caliper_dx_alpha, base_scale=0.55 * sx)

                # -------------------------------------------------------------
                # SHOT 06C (7.5s - 11.8s): The First Stretch Δx -> Δu (2x)
                # Voice: "The first machine stretches or squeezes that step into a new step in U called Delta U" (7.82s - 12.01s)
                # -------------------------------------------------------------
                u_stretch_prog = _smoothstep(7.8, 9.8, t)
                cur_u_pos = ORIGIN_X + DU_STEP * u_stretch_prog

                # Vertical projection beam from x1 to line u
                beam1_alpha = _smoothstep(6.2, 7.5, t)
                if beam1_alpha > 0.0:
                    beam_p = skia.Paint(
                        Color=_skia_color(MINT, beam1_alpha * 0.5),
                        StrokeWidth=1.5 * sx,
                        PathEffect=skia.DashPathEffect.Make([5.0 * sx, 5.0 * sy], (t * 20.0 * sx) % (10.0 * sx)),
                        AntiAlias=True,
                    )
                    canvas.drawLine(cur_x_pos * sx, (Y_LINE_X + 10) * sy, cur_x_pos * sx, (Y_LINE_U - 10) * sy, beam_p)

                    # CAD contact reticle tick on line u
                    canvas.drawLine((cur_x_pos - 6.0) * sx, Y_LINE_U * sy, (cur_x_pos + 6.0) * sx, Y_LINE_U * sy, skia.Paint(Color=_skia_color(MINT, beam1_alpha * 0.8), StrokeWidth=1.5 * sx, AntiAlias=True))

                    if t < 10.0:
                        pulse_y = (Y_LINE_X + 10) + ((Y_LINE_U - Y_LINE_X - 20) * ((t - 6.2) / 2.0 % 1.0))
                        canvas.drawCircle(cur_x_pos * sx, pulse_y * sy, 7.0 * sx, skia.Paint(Color=_skia_color(MINT, 0.35), Style=skia.Paint.kFill_Style, AntiAlias=True))
                        canvas.drawCircle(cur_x_pos * sx, pulse_y * sy, 3.5 * sx, skia.Paint(Color=_skia_color(WHITE, 0.95), Style=skia.Paint.kFill_Style, AntiAlias=True))

                # Slider u handle
                slider_u_paint = skia.Paint(Color=_skia_color(GOLD, min(1.0, axes_alpha * 1.5)), Style=skia.Paint.kFill_Style, AntiAlias=True)
                slider_u_glow_outer = skia.Paint(Color=_skia_color(GOLD, 0.22 * axes_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True)
                slider_u_glow_mid = skia.Paint(Color=_skia_color(GOLD, 0.45 * axes_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True)
                canvas.drawCircle(cur_u_pos * sx, Y_LINE_U * sy, 11.0 * sx, slider_u_glow_outer)
                canvas.drawCircle(cur_u_pos * sx, Y_LINE_U * sy, 8.0 * sx, slider_u_glow_mid)
                canvas.drawCircle(cur_u_pos * sx, Y_LINE_U * sy, 5.0 * sx, slider_u_paint)
                canvas.drawCircle(cur_u_pos * sx, Y_LINE_U * sy, 2.0 * sx, inner_pip)

                # Displacement vector arrow Δu
                if u_stretch_prog > 0.01:
                    disp_glow_u_outer = skia.Paint(
                        Color=_skia_color(GOLD, 0.25),
                        StrokeWidth=8.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    disp_glow_u_inner = skia.Paint(
                        Color=_skia_color(GOLD, 0.50),
                        StrokeWidth=5.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    disp_core_u = skia.Paint(
                        Color=_skia_color(GOLD, 0.95),
                        StrokeWidth=2.5 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(ORIGIN_X * sx, Y_LINE_U * sy, cur_u_pos * sx, Y_LINE_U * sy, disp_glow_u_outer)
                    canvas.drawLine(ORIGIN_X * sx, Y_LINE_U * sy, cur_u_pos * sx, Y_LINE_U * sy, disp_glow_u_inner)
                    canvas.drawLine(ORIGIN_X * sx, Y_LINE_U * sy, cur_u_pos * sx, Y_LINE_U * sy, disp_core_u)

                    ah_paint_u = skia.Paint(Color=_skia_color(GOLD, 0.95), Style=skia.Paint.kFill_Style, AntiAlias=True)
                    ah_path_u = skia.Path()
                    ah_path_u.moveTo(cur_u_pos * sx, Y_LINE_U * sy)
                    ah_path_u.lineTo((cur_u_pos - 10) * sx, (Y_LINE_U - 5) * sy)
                    ah_path_u.lineTo((cur_u_pos - 8) * sx, Y_LINE_U * sy)
                    ah_path_u.lineTo((cur_u_pos - 10) * sx, (Y_LINE_U + 5) * sy)
                    ah_path_u.close()
                    canvas.drawPath(ah_path_u, ah_paint_u)

                # Caliper bracket for Δu
                caliper_du_alpha = _smoothstep(9.2, 10.5, t)
                if caliper_du_alpha > 0.0:
                    c_y_u = Y_LINE_U - 35
                    c_paint_u = skia.Paint(
                        Color=_skia_color(GOLD, caliper_du_alpha * 0.85),
                        StrokeWidth=1.5 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    c_path_u = skia.Path()
                    c_path_u.moveTo(ORIGIN_X * sx, (Y_LINE_U - 18) * sy)
                    c_path_u.lineTo(ORIGIN_X * sx, c_y_u * sy)
                    c_path_u.lineTo(cur_u_pos * sx, c_y_u * sy)
                    c_path_u.lineTo(cur_u_pos * sx, (Y_LINE_U - 18) * sy)
                    canvas.drawPath(c_path_u, c_paint_u)

                    mid_x_u = (ORIGIN_X + cur_u_pos) / 2.0
                    _draw_math_centered(canvas, img_badge_du, mid_x_u * sx, (c_y_u - 20) * sy, alpha=caliper_du_alpha, base_scale=0.55 * sx)

                # -------------------------------------------------------------
                # SHOT 06D (11.8s - 17.5s): The Second Stretch Δu -> Δy (3x)
                # Voice: "Then the second machine stretches or squeezes Delta U into a step in Y called Delta Y" (12.01s - 17.68s)
                # -------------------------------------------------------------
                y_stretch_prog = _smoothstep(12.0, 14.5, t)
                cur_y_pos = ORIGIN_X + DY_STEP * y_stretch_prog

                # Vertical projection beam from u1 to line y
                beam2_alpha = _smoothstep(10.8, 12.0, t)
                if beam2_alpha > 0.0:
                    beam_p2 = skia.Paint(
                        Color=_skia_color(GOLD, beam2_alpha * 0.5),
                        StrokeWidth=1.5 * sx,
                        PathEffect=skia.DashPathEffect.Make([5.0 * sx, 5.0 * sy], (t * 20.0 * sx) % (10.0 * sx)),
                        AntiAlias=True,
                    )
                    canvas.drawLine(cur_u_pos * sx, (Y_LINE_U + 10) * sy, cur_u_pos * sx, (Y_LINE_Y - 10) * sy, beam_p2)

                    # CAD contact reticle tick on line y
                    canvas.drawLine((cur_u_pos - 6.0) * sx, Y_LINE_Y * sy, (cur_u_pos + 6.0) * sx, Y_LINE_Y * sy, skia.Paint(Color=_skia_color(GOLD, beam2_alpha * 0.8), StrokeWidth=1.5 * sx, AntiAlias=True))

                    if t < 14.5:
                        pulse_y2 = (Y_LINE_U + 10) + ((Y_LINE_Y - Y_LINE_U - 20) * ((t - 10.8) / 2.0 % 1.0))
                        canvas.drawCircle(cur_u_pos * sx, pulse_y2 * sy, 7.0 * sx, skia.Paint(Color=_skia_color(GOLD, 0.35), Style=skia.Paint.kFill_Style, AntiAlias=True))
                        canvas.drawCircle(cur_u_pos * sx, pulse_y2 * sy, 3.5 * sx, skia.Paint(Color=_skia_color(WHITE, 0.95), Style=skia.Paint.kFill_Style, AntiAlias=True))

                # Slider y handle
                slider_y_paint = skia.Paint(Color=_skia_color(CORAL, min(1.0, axes_alpha * 1.5)), Style=skia.Paint.kFill_Style, AntiAlias=True)
                slider_y_glow_outer = skia.Paint(Color=_skia_color(CORAL, 0.22 * axes_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True)
                slider_y_glow_mid = skia.Paint(Color=_skia_color(CORAL, 0.45 * axes_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True)
                canvas.drawCircle(cur_y_pos * sx, Y_LINE_Y * sy, 11.0 * sx, slider_y_glow_outer)
                canvas.drawCircle(cur_y_pos * sx, Y_LINE_Y * sy, 8.0 * sx, slider_y_glow_mid)
                canvas.drawCircle(cur_y_pos * sx, Y_LINE_Y * sy, 5.0 * sx, slider_y_paint)
                canvas.drawCircle(cur_y_pos * sx, Y_LINE_Y * sy, 2.0 * sx, inner_pip)

                # Displacement vector arrow Δy
                if y_stretch_prog > 0.01:
                    disp_glow_y_outer = skia.Paint(
                        Color=_skia_color(CORAL, 0.25),
                        StrokeWidth=8.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    disp_glow_y_inner = skia.Paint(
                        Color=_skia_color(CORAL, 0.50),
                        StrokeWidth=5.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    disp_core_y = skia.Paint(
                        Color=_skia_color(CORAL, 0.95),
                        StrokeWidth=2.5 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(ORIGIN_X * sx, Y_LINE_Y * sy, cur_y_pos * sx, Y_LINE_Y * sy, disp_glow_y_outer)
                    canvas.drawLine(ORIGIN_X * sx, Y_LINE_Y * sy, cur_y_pos * sx, Y_LINE_Y * sy, disp_glow_y_inner)
                    canvas.drawLine(ORIGIN_X * sx, Y_LINE_Y * sy, cur_y_pos * sx, Y_LINE_Y * sy, disp_core_y)

                    ah_paint_y = skia.Paint(Color=_skia_color(CORAL, 0.95), Style=skia.Paint.kFill_Style, AntiAlias=True)
                    ah_path_y = skia.Path()
                    ah_path_y.moveTo(cur_y_pos * sx, Y_LINE_Y * sy)
                    ah_path_y.lineTo((cur_y_pos - 10) * sx, (Y_LINE_Y - 5) * sy)
                    ah_path_y.lineTo((cur_y_pos - 8) * sx, Y_LINE_Y * sy)
                    ah_path_y.lineTo((cur_y_pos - 10) * sx, (Y_LINE_Y + 5) * sy)
                    ah_path_y.close()
                    canvas.drawPath(ah_path_y, ah_paint_y)

                # Caliper bracket for Δy
                caliper_dy_alpha = _smoothstep(14.0, 15.2, t)
                if caliper_dy_alpha > 0.0:
                    c_y_y = Y_LINE_Y - 35
                    c_paint_y = skia.Paint(
                        Color=_skia_color(CORAL, caliper_dy_alpha * 0.85),
                        StrokeWidth=1.5 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    c_path_y = skia.Path()
                    c_path_y.moveTo(ORIGIN_X * sx, (Y_LINE_Y - 18) * sy)
                    c_path_y.lineTo(ORIGIN_X * sx, c_y_y * sy)
                    c_path_y.lineTo(cur_y_pos * sx, c_y_y * sy)
                    c_path_y.lineTo(cur_y_pos * sx, (Y_LINE_Y - 18) * sy)
                    canvas.drawPath(c_path_y, c_paint_y)

                    mid_x_y = (ORIGIN_X + cur_y_pos) / 2.0
                    _draw_math_centered(canvas, img_badge_dy, mid_x_y * sx, (c_y_y - 20) * sy, alpha=caliper_dy_alpha, base_scale=0.55 * sx)

                # -------------------------------------------------------------
                # Kinetic Micro-Gears: Machine g & Machine f
                # Voice: "Each machine behaves like a gear with its own local rate" (17.68s - 20.09s)
                # -------------------------------------------------------------
                gears_alpha = _smoothstep(16.5, 18.5, t)
                if gears_alpha > 0.0:
                    _draw_micro_gear(360.0 * sx, 390.0 * sy, 26.0, 8, t * 1.5, CYAN, img_sym_g, gears_alpha)
                    _draw_micro_gear(360.0 * sx, 610.0 * sy, 26.0, 8, -t * 1.0, CORAL, img_sym_f, gears_alpha)

                # -------------------------------------------------------------
                # Local Rate Gauges: Machine g & Machine f
                # Voice: "The first machine's rate compares Delta U to Delta X" (20.09s - 23.49s)
                # Voice: "The second machine's rate compares Delta Y to Delta U" (23.49s - 26.25s)
                # -------------------------------------------------------------
                rate_g_alpha = _smoothstep(20.0, 21.0, t)
                if rate_g_alpha > 0.0:
                    gauge_x = 1180.0
                    gauge_y = 390.0
                    gw = img_rate_g.width() * 0.50 + 44.0
                    gh = img_rate_g.height() * 0.50 + 20.0
                    grt = skia.Rect.MakeXYWH((gauge_x - gw / 2) * sx, (gauge_y - gh / 2) * sy, gw * sx, gh * sy)

                    # Pulse highlight when spoken
                    pulse_g = math.exp(-max(0.0, t - 20.1) * 2.5) if t >= 20.1 else 0.0
                    rim_alpha = min(1.0, 0.75 + pulse_g * 0.25)
                    glow_w = (4.5 + pulse_g * 3.0) * sx

                    pill_bg = skia.Paint(Color=_skia_color("#0A121A", rate_g_alpha * 0.88), Style=skia.Paint.kFill_Style, AntiAlias=True)
                    pill_rim = skia.Paint(Color=_skia_color(CYAN, rate_g_alpha * rim_alpha), Style=skia.Paint.kStroke_Style, StrokeWidth=1.5 * sx, AntiAlias=True)
                    pill_glow = skia.Paint(Color=_skia_color(CYAN, rate_g_alpha * (0.30 + pulse_g * 0.40)), Style=skia.Paint.kStroke_Style, StrokeWidth=glow_w, AntiAlias=True)
                    canvas.drawRoundRect(grt, 16.0 * sx, 16.0 * sy, pill_bg)
                    canvas.drawRoundRect(grt, 16.0 * sx, 16.0 * sy, pill_glow)
                    canvas.drawRoundRect(grt, 16.0 * sx, 16.0 * sy, pill_rim)

                    _draw_math_centered(canvas, img_rate_g, gauge_x * sx, gauge_y * sy, alpha=rate_g_alpha, base_scale=0.50 * sx)

                rate_f_alpha = _smoothstep(23.4, 24.4, t)
                if rate_f_alpha > 0.0:
                    gauge_x2 = 1380.0
                    gauge_y2 = 610.0
                    gw2 = img_rate_f.width() * 0.50 + 44.0
                    gh2 = img_rate_f.height() * 0.50 + 20.0
                    grt2 = skia.Rect.MakeXYWH((gauge_x2 - gw2 / 2) * sx, (gauge_y2 - gh2 / 2) * sy, gw2 * sx, gh2 * sy)

                    # Pulse highlight when spoken
                    pulse_f = math.exp(-max(0.0, t - 23.5) * 2.5) if t >= 23.5 else 0.0
                    rim_alpha2 = min(1.0, 0.75 + pulse_f * 0.25)
                    glow_w2 = (4.5 + pulse_f * 3.0) * sx

                    pill_bg2 = skia.Paint(Color=_skia_color("#1A0A12", rate_f_alpha * 0.88), Style=skia.Paint.kFill_Style, AntiAlias=True)
                    pill_rim2 = skia.Paint(Color=_skia_color(CORAL, rate_f_alpha * rim_alpha2), Style=skia.Paint.kStroke_Style, StrokeWidth=1.5 * sx, AntiAlias=True)
                    pill_glow2 = skia.Paint(Color=_skia_color(CORAL, rate_f_alpha * (0.30 + pulse_f * 0.40)), Style=skia.Paint.kStroke_Style, StrokeWidth=glow_w2, AntiAlias=True)
                    canvas.drawRoundRect(grt2, 16.0 * sx, 16.0 * sy, pill_bg2)
                    canvas.drawRoundRect(grt2, 16.0 * sx, 16.0 * sy, pill_glow2)
                    canvas.drawRoundRect(grt2, 16.0 * sx, 16.0 * sy, pill_rim2)

                    _draw_math_centered(canvas, img_rate_f, gauge_x2 * sx, gauge_y2 * sy, alpha=rate_f_alpha, base_scale=0.50 * sx)

                # -------------------------------------------------------------
                # SHOT 06E (26.2s - 31.53s): The Compounding Chain Climax
                # Voice: "The nudge travels down the chain, getting scaled at every link" (28.52s - 31.53s)
                # -------------------------------------------------------------
                climax_alpha = _smoothstep(26.2, 27.5, t)
                if climax_alpha > 0.0:
                    # High-Voltage Neon Mint cascade wave down the 3 levels
                    for idx, y_pos_raw in enumerate([Y_LINE_X, Y_LINE_U, Y_LINE_Y]):
                        delay = idx * 0.25
                        if (t - 26.2) > delay:
                            pulse_local = math.exp(-((t - 26.2 - delay) * 2.0)) * math.sin((t - 26.2 - delay) * 8.0)
                            if pulse_local > 0.0:
                                wave_outer = skia.Paint(
                                    Color=_skia_color(MINT, pulse_local * 0.30),
                                    StrokeWidth=8.0 * sx,
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                )
                                wave_inner = skia.Paint(
                                    Color=_skia_color(MINT, pulse_local * 0.70),
                                    StrokeWidth=3.0 * sx,
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                )
                                canvas.drawLine(AXIS_X_MIN * sx, y_pos_raw * sy, AXIS_X_MAX * sx, y_pos_raw * sy, wave_outer)
                                canvas.drawLine(AXIS_X_MIN * sx, y_pos_raw * sy, AXIS_X_MAX * sx, y_pos_raw * sy, wave_inner)

                    # Overhead Master Equation Reveal: Δy / Δx = (Δy / Δu) · (Δu / Δx) = 3 · 2 = 6
                    eq_y = 115.0 * sy
                    hero_scale = 0.55 * sx
                    hero_w = img_hero_eq.width() * hero_scale
                    hero_h = img_hero_eq.height() * (0.55 * sy)
                    hero_left = 960.0 * sx - hero_w * 0.5
                    hero_top = eq_y - hero_h * 0.5

                    laser_wipe_prog = _smoothstep(26.8, 29.2, t)
                    revealed_w = hero_w * laser_wipe_prog

                    canvas.save()
                    canvas.clipRect(
                        skia.Rect.MakeLTRB(hero_left - 10.0 * sx, hero_top - 10.0 * sy, hero_left + revealed_w, hero_top + hero_h + 10.0 * sy),
                        skia.ClipOp.kIntersect,
                        True,
                    )
                    _draw_math_centered(canvas, img_hero_eq, 960.0 * sx, eq_y, alpha=1.0, base_scale=hero_scale)
                    canvas.restore()

                    # Laser cursor scanning line with spark emitter
                    if 0.0 < laser_wipe_prog < 1.0:
                        cursor_x = hero_left + revealed_w
                        cursor_glow_outer = skia.Paint(
                            Color=_skia_color(MINT, 0.35),
                            StrokeWidth=6.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        cursor_paint = skia.Paint(
                            Color=_skia_color(WHITE, 0.95),
                            StrokeWidth=2.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        top_y = hero_top - 8.0 * sy
                        bot_y = hero_top + hero_h + 8.0 * sy
                        canvas.drawLine(cursor_x, top_y, cursor_x, bot_y, cursor_glow_outer)
                        canvas.drawLine(cursor_x, top_y, cursor_x, bot_y, cursor_paint)

                        spark_paint = skia.Paint(Color=_skia_color(WHITE, 1.0), Style=skia.Paint.kFill_Style, AntiAlias=True)
                        canvas.drawCircle(cursor_x, eq_y, 4.0 * sx, spark_paint)

                    # Golden Caliper Divider Line below formula (y = 190)
                    caliper_y = 190.0 * sy
                    divider_prog = _smoothstep(27.2, 29.2, t)
                    if divider_prog > 0.0:
                        dw = 480.0 * divider_prog * sx
                        div_p = skia.Paint(
                            Color=_skia_color(GOLD, 0.75 * divider_prog),
                            StrokeWidth=1.5 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        canvas.drawLine(960.0 * sx - dw, caliper_y, 960.0 * sx + dw, caliper_y, div_p)

                        # End tick notches
                        canvas.drawLine((960.0 * sx - dw), caliper_y - 4.0 * sy, (960.0 * sx - dw), caliper_y + 4.0 * sy, div_p)
                        canvas.drawLine((960.0 * sx + dw), caliper_y - 4.0 * sy, (960.0 * sx + dw), caliper_y + 4.0 * sy, div_p)

                        # Center rotating diamond flare
                        rot_deg = divider_prog * 45.0
                        dia_size = 5.0 * sx
                        dia_p = skia.Paint(Color=_skia_color(GOLD, 0.9 * divider_prog), Style=skia.Paint.kFill_Style, AntiAlias=True)
                        canvas.save()
                        canvas.translate(960.0 * sx, caliper_y)
                        canvas.rotate(rot_deg)
                        dia_path = skia.Path()
                        dia_path.moveTo(0, -dia_size)
                        dia_path.lineTo(dia_size, 0)
                        dia_path.lineTo(0, dia_size)
                        dia_path.lineTo(-dia_size, 0)
                        dia_path.close()
                        canvas.drawPath(dia_path, dia_p)
                        canvas.restore()

                    # Climax Bloom Flash on product "6" (t = 29.4s)
                    if t > 29.4:
                        bloom_t = t - 29.4
                        bloom_alpha = math.exp(-bloom_t * 2.5)
                        if bloom_alpha > 0.01:
                            digit_6_x = hero_left + hero_w - 18.0 * sx
                            digit_6_y = eq_y

                            # Anamorphic horizontal lens flare streak
                            streak_len = 160.0 * bloom_alpha * sx
                            canvas.drawLine(digit_6_x - streak_len, digit_6_y, digit_6_x + streak_len, digit_6_y, skia.Paint(Color=_skia_color(MINT, bloom_alpha * 0.40), StrokeWidth=3.5 * sy, AntiAlias=True))
                            canvas.drawLine(digit_6_x - streak_len * 0.5, digit_6_y, digit_6_x + streak_len * 0.5, digit_6_y, skia.Paint(Color=_skia_color(WHITE, bloom_alpha * 0.85), StrokeWidth=1.5 * sy, AntiAlias=True))

                            # Layered radial bloom flare (outer, mid, core, white spark)
                            canvas.drawCircle(digit_6_x, digit_6_y, 45.0 * bloom_alpha * sx, skia.Paint(Color=_skia_color(MINT, bloom_alpha * 0.18), Style=skia.Paint.kFill_Style, AntiAlias=True))
                            canvas.drawCircle(digit_6_x, digit_6_y, 25.0 * bloom_alpha * sx, skia.Paint(Color=_skia_color(MINT, bloom_alpha * 0.38), Style=skia.Paint.kFill_Style, AntiAlias=True))
                            canvas.drawCircle(digit_6_x, digit_6_y, 12.0 * bloom_alpha * sx, skia.Paint(Color=_skia_color(MINT, bloom_alpha * 0.70), Style=skia.Paint.kFill_Style, AntiAlias=True))
                            canvas.drawCircle(digit_6_x, digit_6_y, 5.0 * bloom_alpha * sx, skia.Paint(Color=_skia_color(WHITE, bloom_alpha * 0.95), Style=skia.Paint.kFill_Style, AntiAlias=True))

                snapshot = surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_06(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build Scene 06: The Traveling Nudge: Number Lines & Local Stretches."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            # Scene 06 starts at 160.63s and ends at 192.16s in the master audio
            scene.add_audio(str(p), start=0.0, trim_start=160.63, trim_end=192.16)

    viewport = Viewport(TravelingNudgeSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_06_DURATION)
    return scene
