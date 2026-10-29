"""Scene 12: Backpropagation at Scale & The Grand Intuition.

Curriculum Chapter 6 Finale & Masterclass Climax:
Pure pitch-black void canvas (#000000), zero text clutter, Euler-style MathTex,
reverse gear kinematics, multi-layer cosmic neural matrix at billion scale,
'do not see symbols, see gears' dynamic nudge cascade, and three-pillar grand unification.
"""

from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Sequence

from matplotlib import figure
from matplotlib.font_manager import FontProperties
from matplotlib.mathtext import MathTextParser
import numpy as np
from PIL import Image
import skia

from faceless_champ import Canvas, Scene, Viewport

SCENE_12_DURATION: float = 55.30

# High-Voltage Electric RGB Color Palette (Matching euler_scene.py)
CYAN = "#00F5FF"     # Electric Laser Cyan (Input Layer X, Nudge dx, du/dx)
GOLD = "#FFB800"     # Radiant Gold (Hidden Layer H, Weight w, da/dz, intermediate rates)
WHITE = "#FFFFFF"    # Crisp Pure White (Operators, equals, fraction bars, grid ticks)
MINT = "#05FFA1"     # High-Voltage Neon Mint (Total composite derivatives, product laws, gradient update)
CORAL = "#FF2A6D"    # Laser Neon Coral (Output Layer Y_hat, Loss L, dy/du, shadow velocity)
AMBER = "#FF8800"    # Radiant Amber (Output weights W2, bank multiplier)
VIOLET = "#9D00FF"   # Electric Bioluminescent Violet (Synaptic filaments)


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
    w_safe = max(1.0, float(width))
    h_safe = max(1.0, float(height))
    fig = figure.Figure(figsize=(w_safe / 72.0, h_safe / 72.0))
    fig.patch.set_alpha(0.0)
    fig.text(0, depth / h_safe, s_math, fontproperties=prop, color=color)
    buf = io.BytesIO()
    fig.savefig(buf, dpi=dpi, format="png", transparent=True)
    buf.seek(0)
    return Image.open(buf).convert("RGBA"), depth * (dpi / 72.0)


def _compose_latex_equation(
    terms: Sequence[tuple[str, str] | tuple[str, str, int]],
    font_size: int = 34,
    spacing: int = 14,
    dpi: int = 200,
) -> tuple[skia.Image, list[float], list[float]]:
    """Compose multi-term colored LaTeX equation with exact TeX mathematical baseline alignment.

    Returns:
        (skia_image, term_center_xs, term_widths)
    """
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

    term_centers = []
    term_widths = []

    for i, ((img, d), gap) in enumerate(imgs_with_depth_gap):
        y = int(baseline_y - (img.height - d))
        comp.alpha_composite(img, (cur_x, y))
        term_centers.append(cur_x + img.width / 2.0)
        term_widths.append(float(img.width))
        cur_x += img.width + (gap if i < len(imgs_with_depth_gap) - 1 else 0)

    skia_img = skia.Image.fromarray(np.array(comp), skia.ColorType.kRGBA_8888_ColorType)
    return skia_img, term_centers, term_widths


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
) -> float:
    """Draw a precompiled LaTeX formula centered at (cx, cy) with bilinear filtering.

    Returns the scale factor used.
    """
    if alpha <= 0.0 or img is None:
        return base_scale

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
    return scale


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

    tooth_h = radius * 0.22
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


class Scene12ScaleAndIntuitionSource:
    """Climactic finale source: Backpropagation at scale and the grand geometric intuition."""

    duration: float = SCENE_12_DURATION
    fps: int = 30
    intrinsic_size: tuple[int, int] = (1920, 1080)
    fingerprint: str = "chain:scene-12:scale-and-intuition:v1"
    requirements: tuple[str, ...] = ()

    def frame_key(self, source_time: float) -> int:
        return int(source_time * 60)

    def open(self, size: tuple[int, int] | None = None):
        target_size = size or self.intrinsic_size

        class Session:
            def __init__(self):
                self.w, self.h = target_size
                self.sx = self.w / 1920.0
                self.sy = self.h / 1080.0

                info = skia.ImageInfo.Make(self.w, self.h, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
                self.surface = skia.Surface.MakeRaster(info)
                self.canvas = self.surface.getCanvas()

                # =========================================================================
                # PRECOMPILE ALL MATHEMATICAL EQUATIONS IN EULER MATHTEX
                # =========================================================================

                # -------------------------------------------------------------
                # 1. ACT 1: REVERSE GEAR RATE LABELS & WEIGHT ADJUSTMENT FORMULA
                # -------------------------------------------------------------
                self.img_gear_rate_loss, _, _ = _compose_latex_equation(
                    [(r"\mathbf{\frac{\partial \mathcal{L}}{\partial \hat{y}}}", CORAL, 0)],
                    font_size=34,
                )
                self.img_gear_rate_out, _, _ = _compose_latex_equation(
                    [(r"\mathbf{\frac{\partial \hat{y}}{\partial a}}", AMBER, 0)],
                    font_size=34,
                )
                self.img_gear_rate_act, _, _ = _compose_latex_equation(
                    [(r"\mathbf{\frac{\partial a}{\partial z}}", GOLD, 0)],
                    font_size=34,
                )
                self.img_gear_rate_aff, _, _ = _compose_latex_equation(
                    [(r"\mathbf{\frac{\partial z}{\partial w}}", CYAN, 0)],
                    font_size=34,
                )

                # Weight adjustment formula below the reverse gears
                self.img_weight_adjust, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\Delta w}", GOLD, 14),
                        (r"=", WHITE, 14),
                        (r"\mathbf{-\eta}", MINT, 14),
                        (r"\mathbf{\frac{\partial \mathcal{L}}{\partial w}}", MINT, 0),
                    ],
                    font_size=42,
                    spacing=14,
                )

                # Dial label
                self.img_tok_wij, _, _ = _compose_latex_equation([(r"\mathbf{w_{ij}}", GOLD, 0)], font_size=34)

                # -------------------------------------------------------------
                # 2. ACT 2: MASSIVE NEURAL MATRIX AT BILLIONS SCALE
                # -------------------------------------------------------------
                self.img_matrix_gradient, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\nabla_{\mathbf{W}^{[l]}} \mathcal{L}}", MINT, 16),
                        (r"=", WHITE, 16),
                        (r"\mathbf{\delta^{[l]}}", CORAL, 12),
                        (r"\cdot", WHITE, 12),
                        (r"(\mathbf{a}^{[l-1]})^T", CYAN, 0),
                    ],
                    font_size=46,
                    spacing=16,
                )

                self.img_scale_billions, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\sum_{\text{paths}} \prod \text{rates}}", GOLD, 40),
                        (r"\mathbf{\left(N \sim 10^9\right)}", MINT, 0),
                    ],
                    font_size=32,
                    spacing=24,
                )

                # -------------------------------------------------------------
                # 3. ACT 3: "DO NOT SEE SYMBOLS, SEE GEARS" (NUDGE CASCADE)
                # -------------------------------------------------------------
                self.img_chain_master, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\frac{dy}{dx}}", MINT, 20),
                        (r"=", WHITE, 20),
                        (r"\mathbf{\frac{dy}{du}}", CORAL, 18),
                        (r"\cdot", WHITE, 18),
                        (r"\mathbf{\frac{du}{dx}}", CYAN, 0),
                    ],
                    font_size=54,
                    spacing=18,
                )

                self.img_gear_symbol_left, _, _ = _compose_latex_equation([(r"\mathbf{\frac{du}{dx}}", CYAN, 0)], font_size=30)
                self.img_gear_symbol_right, _, _ = _compose_latex_equation([(r"\mathbf{\frac{dy}{du}}", CORAL, 0)], font_size=30)

                self.img_nudge_dx, _, _ = _compose_latex_equation([(r"\mathbf{\Delta x}", CYAN, 0)], font_size=32)
                self.img_nudge_du, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\Delta u}", GOLD, 10),
                        (r"=", WHITE, 10),
                        (r"\mathbf{\frac{du}{dx}}", CYAN, 6),
                        (r"\cdot", WHITE, 6),
                        (r"\mathbf{\Delta x}", CYAN, 0),
                    ],
                    font_size=32,
                    spacing=10,
                )
                self.img_nudge_dy, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\Delta y}", CORAL, 10),
                        (r"=", WHITE, 10),
                        (r"\mathbf{\frac{dy}{du}}", CORAL, 6),
                        (r"\cdot", WHITE, 6),
                        (r"\mathbf{\Delta u}", GOLD, 0),
                    ],
                    font_size=32,
                    spacing=10,
                )

                # Composite stretch bracket formula
                self.img_nudge_product_bracket, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\Delta y}", CORAL, 14),
                        (r"=", WHITE, 14),
                        (r"\mathbf{\Delta x}", CYAN, 12),
                        (r"\cdot", WHITE, 12),
                        (r"\mathbf{(}", WHITE, 10),
                        (r"\mathbf{\frac{dy}{du}}", CORAL, 10),
                        (r"\cdot", WHITE, 10),
                        (r"\mathbf{\frac{du}{dx}}", CYAN, 10),
                        (r"\mathbf{)}", WHITE, 0),
                    ],
                    font_size=42,
                    spacing=12,
                )

                # -------------------------------------------------------------
                # 4. ACT 4: THE THREE PILLARS & SOVEREIGN PRODUCT THEOREM
                # -------------------------------------------------------------
                # Pillar 1: Shadow Kinematics
                self.img_pillar_shadow, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\frac{ds}{dt}}", CORAL, 12),
                        (r"=", WHITE, 12),
                        (r"\mathbf{\frac{ds}{dx}}", CORAL, 10),
                        (r"\cdot", WHITE, 10),
                        (r"\mathbf{\frac{dx}{dt}}", CYAN, 0),
                    ],
                    font_size=34,
                    spacing=10,
                )

                # Pillar 2: Compounding Bank Rate
                self.img_pillar_bank, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\frac{d}{dt}\left[e^{rt}\right]}", GOLD, 12),
                        (r"=", WHITE, 12),
                        (r"\mathbf{r}", AMBER, 8),
                        (r"\mathbf{e^{rt}}", GOLD, 0),
                    ],
                    font_size=34,
                    spacing=10,
                )

                # Pillar 3: AI Neural Gradient
                self.img_pillar_neural, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\nabla_{\mathbf{W}} \mathcal{L}}", MINT, 12),
                        (r"=", WHITE, 12),
                        (r"\mathbf{\delta}", CORAL, 8),
                        (r"\cdot", WHITE, 8),
                        (r"\mathbf{x}^T", CYAN, 0),
                    ],
                    font_size=34,
                    spacing=10,
                )

                # Sovereign Multi-Link Product Law
                self.img_sovereign_theorem, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\frac{dy}{dx}}", MINT, 20),
                        (r"=", WHITE, 20),
                        (r"\mathbf{\prod_{k=1}^K}", GOLD, 18),
                        (r"\mathbf{\frac{du_k}{du_{k-1}}}", CYAN, 0),
                    ],
                    font_size=46,
                    spacing=20,
                )

                # -------------------------------------------------------------
                # PROCEDURAL PRECALCULATIONS: COSMIC 5-LAYER NEURAL MATRIX
                # -------------------------------------------------------------
                # Layer counts: 8 -> 12 -> 14 -> 12 -> 4
                layer_xs = [320.0, 640.0, 960.0, 1280.0, 1600.0]
                layer_node_counts = [8, 12, 14, 12, 4]
                self.deep_matrix_layers: list[list[tuple[float, float]]] = []

                for l_idx, (lx, count) in enumerate(zip(layer_xs, layer_node_counts)):
                    # Center each layer vertically around y = 410, height range ~500px
                    span_h = 480.0
                    y_step = span_h / max(1, count - 1)
                    start_y = 410.0 - (span_h / 2.0)
                    layer_nodes = [(lx, start_y + i * y_step) for i in range(count)]
                    self.deep_matrix_layers.append(layer_nodes)

                # Sample deterministic filament connections (subset to keep rendering 30fps)
                self.matrix_synapses: list[tuple[tuple[float, float], tuple[float, float], float]] = []
                np.random.seed(42)
                for l_idx in range(4):
                    l_from = self.deep_matrix_layers[l_idx]
                    l_to = self.deep_matrix_layers[l_idx + 1]
                    for n1 in l_from:
                        # Connect each node to ~4-6 nodes in the next layer
                        chosen_indices = np.random.choice(len(l_to), size=min(5, len(l_to)), replace=False)
                        for c_idx in chosen_indices:
                            weight_amp = float(np.random.uniform(0.4, 1.0))
                            self.matrix_synapses.append((n1, l_to[c_idx], weight_amp))

            def frame(self, t: float) -> Image.Image:
                canvas = self.canvas
                w = self.w
                h = self.h
                sx = self.sx
                sy = self.sy

                # Pure Pitch-Black Void Canvas
                canvas.clear(skia.ColorSetARGB(255, 0, 0, 0))

                # =========================================================================
                # 1. ACT 1: REVERSE GEARS TURNING & WEIGHT DIAL ADJUSTMENT (0.0s - 12.0s)
                # =========================================================================
                act1_alpha = _smoothstep(0.0, 1.2, t) * (1.0 - _smoothstep(10.8, 12.0, t))
                if act1_alpha > 0.0:
                    # 4 Interlocked Involute Gears centered along y = 300
                    # Gear 4: Pre-activation rate dz/dw (Cyan)
                    # Gear 3: Activation rate da/dz (Gold)
                    # Gear 2: Output weight rate dy_hat/da (Amber)
                    # Gear 1: Loss rate dL/dy_hat (Coral)
                    gear_y = 300.0 * sy
                    r_gear = 68.0 * sx
                    t_teeth = 14

                    # Reverse rotational velocities:
                    # Gear 1 turns clockwise (-), Gear 2 turns counter-clockwise (+), etc.
                    # Base reverse speed
                    rev_speed = 1.4
                    ang1 = -t * rev_speed
                    ang2 = t * rev_speed + (math.pi / t_teeth)  # Phase-shifted for tooth engagement
                    ang3 = -t * rev_speed
                    ang4 = t * rev_speed + (math.pi / t_teeth)

                    gear_xs = [900.0 * sx, 1040.0 * sx, 1180.0 * sx, 1320.0 * sx]
                    gear_angles = [ang4, ang3, ang2, ang1]
                    gear_colors = [CYAN, GOLD, AMBER, CORAL]
                    gear_labels = [
                        self.img_gear_rate_aff,
                        self.img_gear_rate_act,
                        self.img_gear_rate_out,
                        self.img_gear_rate_loss,
                    ]

                    # Draw 4 meshed gears
                    for gx, ga, gc, gl in zip(gear_xs, gear_angles, gear_colors, gear_labels):
                        _draw_involute_gear(canvas, gx, gear_y, r_gear, t_teeth, ga, gc, act1_alpha, sx)
                        # Rate formula directly above gear
                        _draw_math_centered(canvas, gl, gx, gear_y - r_gear - 30.0 * sy, alpha=act1_alpha, base_scale=0.52 * sx)

                    # Reverse Transmission Laser Beam across bottom of gears
                    canvas.drawLine(gear_xs[3], gear_y + r_gear + 15.0 * sy, gear_xs[0], gear_y + r_gear + 15.0 * sy, skia.Paint(
                        Color=_skia_color(WHITE, 0.25 * act1_alpha),
                        StrokeWidth=1.8 * sx,
                        AntiAlias=True,
                    ))

                    # Reverse energy arrow head (<--)
                    canvas.drawLine(gear_xs[0] + 16.0 * sx, gear_y + r_gear + 9.0 * sy, gear_xs[0], gear_y + r_gear + 15.0 * sy, skia.Paint(
                        Color=_skia_color(MINT, 0.95 * act1_alpha),
                        StrokeWidth=2.4 * sx,
                        AntiAlias=True,
                    ))
                    canvas.drawLine(gear_xs[0] + 16.0 * sx, gear_y + r_gear + 21.0 * sy, gear_xs[0], gear_y + r_gear + 15.0 * sy, skia.Paint(
                        Color=_skia_color(MINT, 0.95 * act1_alpha),
                        StrokeWidth=2.4 * sx,
                        AntiAlias=True,
                    ))

                    # Lower Section: Rotary Weight Dial w_ij at (960, 680)
                    dial_cx = 960.0 * sx
                    dial_cy = 680.0 * sy
                    dial_r = 62.0 * sx

                    # Dial Background & Rim
                    canvas.drawCircle(dial_cx, dial_cy, dial_r, skia.Paint(
                        Color=_skia_color("#050d18", 0.94 * act1_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawCircle(dial_cx, dial_cy, dial_r, skia.Paint(
                        Color=_skia_color(GOLD, 0.95 * act1_alpha),
                        StrokeWidth=2.4 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))

                    # 16 Graduation Ticks
                    for tick_i in range(16):
                        ta = tick_i * (2.0 * math.pi / 16.0)
                        tr0 = dial_r - 8.0 * sx
                        tr1 = dial_r - 2.0 * sx
                        canvas.drawLine(
                            dial_cx + tr0 * math.cos(ta), dial_cy + tr0 * math.sin(ta),
                            dial_cx + tr1 * math.cos(ta), dial_cy + tr1 * math.sin(ta),
                            skia.Paint(
                                Color=_skia_color(WHITE, 0.65 * act1_alpha),
                                StrokeWidth=1.5 * sx,
                                AntiAlias=True,
                            ),
                        )

                    # Dial Needle physically rotating in reverse (starts at 5.5s, finishes turn by 9.5s)
                    turn_prog = _smoothstep(5.5, 9.5, t)
                    needle_ang = math.radians(-30.0 - turn_prog * 85.0)

                    # Dynamic Angular Adjustment Arc
                    if turn_prog > 0.0:
                        arc_rect = skia.Rect.MakeXYWH(dial_cx - (dial_r - 18.0 * sx), dial_cy - (dial_r - 18.0 * sx), (dial_r - 18.0 * sx) * 2.0, (dial_r - 18.0 * sx) * 2.0)
                        canvas.drawArc(arc_rect, -30.0, -turn_prog * 85.0, False, skia.Paint(
                            Color=_skia_color(MINT, 0.85 * act1_alpha),
                            StrokeWidth=3.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                    # Needle Laser
                    canvas.drawLine(
                        dial_cx, dial_cy,
                        dial_cx + (dial_r - 10.0 * sx) * math.cos(needle_ang),
                        dial_cy + (dial_r - 10.0 * sx) * math.sin(needle_ang),
                        skia.Paint(
                            Color=_skia_color(CYAN, 0.98 * act1_alpha),
                            StrokeWidth=2.6 * sx,
                            AntiAlias=True,
                        ),
                    )
                    canvas.drawCircle(dial_cx, dial_cy, 6.0 * sx, skia.Paint(
                        Color=_skia_color(WHITE, 0.98 * act1_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))

                    # Dial Label w_ij
                    _draw_math_centered(canvas, self.img_tok_wij, dial_cx - dial_r - 40.0 * sx, dial_cy, alpha=act1_alpha, base_scale=0.52 * sx)

                    # Adjustment Formula below Dial: Delta w = -eta * dL/dw
                    adj_alpha = _smoothstep(6.0, 7.5, t) * act1_alpha
                    _draw_math_centered(canvas, self.img_weight_adjust, dial_cx, dial_cy + dial_r + 55.0 * sy, alpha=adj_alpha, base_scale=0.56 * sx)

                # =========================================================================
                # 2. ACT 2: MASSIVE NEURAL MATRIX AT BILLIONS SCALE (11.5s - 24.5s)
                # =========================================================================
                act2_alpha = _smoothstep(11.5, 13.0, t) * (1.0 - _smoothstep(23.0, 24.5, t))
                if act2_alpha > 0.0:
                    # Camera Zoom Out: Multi-layer network pulses with bioluminescence
                    # Synaptic Filaments
                    for (n1, n2, amp) in self.matrix_synapses:
                        canvas.drawLine(
                            n1[0] * sx, n1[1] * sy,
                            n2[0] * sx, n2[1] * sy,
                            skia.Paint(
                                Color=_skia_color(VIOLET, 0.16 * amp * act2_alpha),
                                StrokeWidth=1.0 * sx,
                                AntiAlias=True,
                            ),
                        )

                    # Cascading Reverse Energy Waves (Right to Left across 5 layers)
                    # Wave cycle repeats every 2.4 seconds
                    wave_time = ((t - 13.0) * 0.42) % 1.0 if t >= 13.0 else 0.0
                    for (n1, n2, amp) in self.matrix_synapses:
                        # Flow from n2 (right) to n1 (left)
                        if t >= 13.0:
                            prog = (wave_time + amp * 0.25) % 1.0
                            px = n2[0] - prog * (n2[0] - n1[0])
                            py = n2[1] - prog * (n2[1] - n1[1])
                            canvas.drawCircle(px * sx, py * sy, 2.5 * sx, skia.Paint(
                                Color=_skia_color(MINT, 0.65 * act2_alpha),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))

                    # Deep Matrix Layer Nodes
                    layer_colors = [CYAN, GOLD, AMBER, GOLD, CORAL]
                    for l_idx, (layer_nodes, l_col) in enumerate(zip(self.deep_matrix_layers, layer_colors)):
                        for (nx, ny) in layer_nodes:
                            # Halo
                            canvas.drawCircle(nx * sx, ny * sy, 12.0 * sx, skia.Paint(
                                Color=_skia_color(l_col, 0.22 * act2_alpha),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))
                            # Core
                            canvas.drawCircle(nx * sx, ny * sy, 5.0 * sx, skia.Paint(
                                Color=_skia_color(WHITE, 0.90 * act2_alpha),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))

                    # Top Center: Matrix Gradient Tensor Formula
                    _draw_math_centered(canvas, self.img_matrix_gradient, 960.0 * sx, 95.0 * sy, alpha=act2_alpha, base_scale=0.55 * sx)

                    # Bottom Center: Billions Scale Badge
                    badge_alpha = _smoothstep(15.5, 17.0, t) * act2_alpha
                    if badge_alpha > 0.0:
                        bw = 780.0 * sx
                        bh = 145.0 * sy
                        bcx = 960.0 * sx
                        bcy = 880.0 * sy
                        r_rect = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bcx - bw / 2.0, bcy - bh / 2.0, bw, bh), 18.0 * sx, 18.0 * sy)

                        canvas.drawRRect(r_rect, skia.Paint(
                            Color=_skia_color("#05121c", 0.85 * badge_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRRect(r_rect, skia.Paint(
                            Color=_skia_color(GOLD, 0.65 * badge_alpha),
                            StrokeWidth=1.8 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))
                        _draw_math_centered(canvas, self.img_scale_billions, bcx, bcy, alpha=badge_alpha, base_scale=0.50 * sx)

                # =========================================================================
                # 3. ACT 3: "DO NOT SEE SYMBOLS, SEE GEARS" (NUDGE CASCADE) (24.0s - 41.5s)
                # =========================================================================
                act3_alpha = _smoothstep(24.0, 25.5, t) * (1.0 - _smoothstep(40.5, 41.8, t))
                if act3_alpha > 0.0:
                    # 1. Master Leibniz Chain Rule Formula at y = 150
                    eq_y = 150.0 * sy
                    _draw_math_centered(canvas, self.img_chain_master, 960.0 * sx, eq_y, alpha=act3_alpha, base_scale=0.58 * sx)

                    # 2. Dual Meshed Mechanical Transmission Gears at y = 390
                    gear_g_y = 390.0 * sy
                    rg1 = 62.0 * sx
                    rg2 = 62.0 * sx
                    g1_cx = (960.0 - 62.0) * sx
                    g2_cx = (960.0 + 62.0) * sx

                    rot_omega = t * 2.2
                    _draw_involute_gear(canvas, g1_cx, gear_g_y, rg1, 14, rot_omega, CYAN, act3_alpha, sx)
                    _draw_involute_gear(canvas, g2_cx, gear_g_y, rg2, 14, -rot_omega + (math.pi / 14.0), CORAL, act3_alpha, sx)

                    # Gear Labels
                    _draw_math_centered(canvas, self.img_gear_symbol_left, g1_cx, gear_g_y - rg1 - 58.0 * sy, alpha=act3_alpha, base_scale=0.50 * sx)
                    _draw_math_centered(canvas, self.img_gear_symbol_right, g2_cx, gear_g_y - rg2 - 58.0 * sy, alpha=act3_alpha, base_scale=0.50 * sx)

                    # 3. Dynamic 3-Tier Nudge Stretch Cascade at y in [580, 880]
                    # Calibrated horizontal rail
                    rail_y = 580.0 * sy
                    canvas.drawLine(340.0 * sx, rail_y, 1580.0 * sx, rail_y, skia.Paint(
                        Color=_skia_color(WHITE, 0.22 * act3_alpha),
                        StrokeWidth=1.8 * sx,
                        AntiAlias=True,
                    ))

                    # Caliper Tier 1: Input Nudge dx (Cyan, length 90px)
                    # Starts at x = 380
                    x_dx_start = 380.0 * sx
                    x_dx_end = 470.0 * sx
                    canvas.drawLine(x_dx_start, rail_y, x_dx_end, rail_y, skia.Paint(
                        Color=_skia_color(CYAN, 0.98 * act3_alpha),
                        StrokeWidth=5.0 * sx,
                        AntiAlias=True,
                    ))
                    # Caliper tips
                    canvas.drawLine(x_dx_start, rail_y - 8.0 * sy, x_dx_start, rail_y + 8.0 * sy, skia.Paint(
                        Color=_skia_color(CYAN, 0.95 * act3_alpha), StrokeWidth=2.0 * sx, AntiAlias=True
                    ))
                    canvas.drawLine(x_dx_end, rail_y - 8.0 * sy, x_dx_end, rail_y + 8.0 * sy, skia.Paint(
                        Color=_skia_color(CYAN, 0.95 * act3_alpha), StrokeWidth=2.0 * sx, AntiAlias=True
                    ))
                    _draw_math_centered(canvas, self.img_nudge_dx, (x_dx_start + x_dx_end) / 2.0, rail_y - 24.0 * sy, alpha=act3_alpha, base_scale=0.50 * sx)

                    # Caliper Tier 2: First Stretch du = (du/dx) * dx (Gold, stretched to 220px)
                    # Appears at 30.5s
                    tier2_alpha = _smoothstep(30.5, 32.0, t) * act3_alpha
                    if tier2_alpha > 0.0:
                        x_du_start = 570.0 * sx
                        # Dynamic stretch animation
                        s_prog1 = _smoothstep(31.0, 33.0, t)
                        x_du_end = x_du_start + (90.0 + s_prog1 * 130.0) * sx
                        canvas.drawLine(x_du_start, rail_y, x_du_end, rail_y, skia.Paint(
                            Color=_skia_color(GOLD, 0.98 * tier2_alpha),
                            StrokeWidth=5.0 * sx,
                            AntiAlias=True,
                        ))
                        canvas.drawLine(x_du_start, rail_y - 8.0 * sy, x_du_start, rail_y + 8.0 * sy, skia.Paint(
                            Color=_skia_color(GOLD, 0.95 * tier2_alpha), StrokeWidth=2.0 * sx, AntiAlias=True
                        ))
                        canvas.drawLine(x_du_end, rail_y - 8.0 * sy, x_du_end, rail_y + 8.0 * sy, skia.Paint(
                            Color=_skia_color(GOLD, 0.95 * tier2_alpha), StrokeWidth=2.0 * sx, AntiAlias=True
                        ))
                        _draw_math_centered(canvas, self.img_nudge_du, (x_du_start + x_du_end) / 2.0, rail_y - 24.0 * sy, alpha=tier2_alpha, base_scale=0.48 * sx)

                    # Caliper Tier 3: Second Stretch dy = (dy/du) * du (Coral, stretched to 420px)
                    # Appears at 34.0s
                    tier3_alpha = _smoothstep(34.0, 35.5, t) * act3_alpha
                    if tier3_alpha > 0.0:
                        x_dy_start = 920.0 * sx
                        s_prog2 = _smoothstep(34.5, 36.8, t)
                        x_dy_end = x_dy_start + (220.0 + s_prog2 * 200.0) * sx
                        canvas.drawLine(x_dy_start, rail_y, x_dy_end, rail_y, skia.Paint(
                            Color=_skia_color(CORAL, 0.98 * tier3_alpha),
                            StrokeWidth=5.0 * sx,
                            AntiAlias=True,
                        ))
                        canvas.drawLine(x_dy_start, rail_y - 8.0 * sy, x_dy_start, rail_y + 8.0 * sy, skia.Paint(
                            Color=_skia_color(CORAL, 0.95 * tier3_alpha), StrokeWidth=2.0 * sx, AntiAlias=True
                        ))
                        canvas.drawLine(x_dy_end, rail_y - 8.0 * sy, x_dy_end, rail_y + 8.0 * sy, skia.Paint(
                            Color=_skia_color(CORAL, 0.95 * tier3_alpha), StrokeWidth=2.0 * sx, AntiAlias=True
                        ))
                        _draw_math_centered(canvas, self.img_nudge_dy, (x_dy_start + x_dy_end) / 2.0, rail_y - 24.0 * sy, alpha=tier3_alpha, base_scale=0.48 * sx)

                    # Multiplicative Product Bracket Formula at y = 780
                    brack_alpha = _smoothstep(36.5, 38.0, t) * act3_alpha
                    if brack_alpha > 0.0:
                        _draw_math_centered(canvas, self.img_nudge_product_bracket, 960.0 * sx, 780.0 * sy, alpha=brack_alpha, base_scale=0.55 * sx)

                # =========================================================================
                # 4. ACT 4: THE THREE PILLARS & SOVEREIGN PRODUCT THEOREM (41.0s - 55.30s)
                # =========================================================================
                act4_alpha = _smoothstep(41.0, 42.5, t) * (1.0 - _smoothstep(53.8, 55.3, t))
                if act4_alpha > 0.0:
                    # Three-Pillar Triptych Stations at y = 340
                    station_y = 340.0 * sy
                    p1_cx = 400.0 * sx
                    p2_cx = 960.0 * sx
                    p3_cx = 1520.0 * sx

                    stations = [
                        (p1_cx, CORAL, self.img_pillar_shadow),
                        (p2_cx, GOLD, self.img_pillar_bank),
                        (p3_cx, MINT, self.img_pillar_neural),
                    ]

                    # Card plates for each pillar
                    cw = 420.0 * sx
                    ch = 220.0 * sy
                    for cx, col_hex, eq_img in stations:
                        c_rect = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(cx - cw / 2.0, station_y - ch / 2.0, cw, ch), 18.0 * sx, 18.0 * sy)
                        canvas.drawRRect(c_rect, skia.Paint(
                            Color=_skia_color("#050d18", 0.88 * act4_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawRRect(c_rect, skia.Paint(
                            Color=_skia_color(col_hex, 0.70 * act4_alpha),
                            StrokeWidth=2.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                        # Top Iconic Glyph inside card
                        # Pillar 1: Shadow line icon
                        if cx == p1_cx:
                            # Moving ray & shadow ground
                            canvas.drawLine(cx - 50.0 * sx, station_y - 50.0 * sy, cx + 50.0 * sx, station_y - 20.0 * sy, skia.Paint(
                                Color=_skia_color(CORAL, 0.85 * act4_alpha), StrokeWidth=2.4 * sx, AntiAlias=True
                            ))
                            canvas.drawLine(cx - 60.0 * sx, station_y - 20.0 * sy, cx + 60.0 * sx, station_y - 20.0 * sy, skia.Paint(
                                Color=_skia_color(WHITE, 0.40 * act4_alpha), StrokeWidth=1.5 * sx, AntiAlias=True
                            ))
                        # Pillar 2: Compounding exponential curve icon
                        elif cx == p2_cx:
                            exp_path = skia.Path()
                            exp_path.moveTo(cx - 60.0 * sx, station_y - 20.0 * sy)
                            exp_path.cubicTo(cx - 10.0 * sx, station_y - 22.0 * sy, cx + 25.0 * sx, station_y - 35.0 * sy, cx + 60.0 * sx, station_y - 65.0 * sy)
                            canvas.drawPath(exp_path, skia.Paint(
                                Color=_skia_color(GOLD, 0.90 * act4_alpha), StrokeWidth=2.4 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True
                            ))
                        # Pillar 3: Neural network icon
                        else:
                            for n_i in range(3):
                                ny0 = station_y - 55.0 * sy + n_i * 20.0 * sy
                                ny1 = station_y - 45.0 * sy + (n_i % 2) * 20.0 * sy
                                canvas.drawCircle(cx - 30.0 * sx, ny0, 4.0 * sx, skia.Paint(Color=_skia_color(CYAN, 0.90 * act4_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True))
                                canvas.drawCircle(cx + 30.0 * sx, ny1, 4.0 * sx, skia.Paint(Color=_skia_color(CORAL, 0.90 * act4_alpha), Style=skia.Paint.kFill_Style, AntiAlias=True))
                                canvas.drawLine(cx - 30.0 * sx, ny0, cx + 30.0 * sx, ny1, skia.Paint(Color=_skia_color(VIOLET, 0.45 * act4_alpha), StrokeWidth=1.2 * sx, AntiAlias=True))

                        # Mathematical Formula in Card
                        _draw_math_centered(canvas, eq_img, cx, station_y + 35.0 * sy, alpha=act4_alpha, base_scale=0.52 * sx)

                    # Convergence Laser Arcs from 3 stations down to Center (starts at 45.5s)
                    arc_alpha = _smoothstep(45.5, 47.0, t) * act4_alpha
                    target_cx = 960.0 * sx
                    target_cy = 760.0 * sy

                    if arc_alpha > 0.0:
                        arc_paint = skia.Paint(
                            Color=_skia_color(MINT, 0.40 * arc_alpha),
                            StrokeWidth=1.6 * sx,
                            AntiAlias=True,
                        )
                        canvas.drawLine(p1_cx, station_y + ch / 2.0, target_cx, target_cy - 150.0 * sy, arc_paint)
                        canvas.drawLine(p2_cx, station_y + ch / 2.0, target_cx, target_cy - 150.0 * sy, arc_paint)
                        canvas.drawLine(p3_cx, station_y + ch / 2.0, target_cx, target_cy - 150.0 * sy, arc_paint)

                    # Sovereign Multi-Link Product Theorem (blooms at 47.0s)
                    theo_alpha = _smoothstep(47.0, 48.5, t) * act4_alpha
                    if theo_alpha > 0.0:
                        # Grand Plate
                        tw = 960.0 * sx
                        th = 300.0 * sy
                        t_rect = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(target_cx - tw / 2.0, target_cy - th / 2.0, tw, th), 26.0 * sx, 26.0 * sy)

                        canvas.drawRRect(t_rect, skia.Paint(
                            Color=_skia_color("#051610", 0.90 * theo_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        # Double Emerald Border
                        canvas.drawRRect(t_rect, skia.Paint(
                            Color=_skia_color(MINT, 0.85 * theo_alpha),
                            StrokeWidth=2.6 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                        # Radial Pulsing Aura
                        pulse_r = (th / 2.0) + (10.0 + 8.0 * math.sin(t * 3.0)) * sx
                        canvas.drawCircle(target_cx, target_cy, pulse_r * 2.2, skia.Paint(
                            Color=_skia_color(MINT, 0.12 * theo_alpha),
                            StrokeWidth=1.5 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                        _draw_math_centered(canvas, self.img_sovereign_theorem, target_cx, target_cy, alpha=theo_alpha, base_scale=0.50 * sx)

                snapshot = self.surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_12(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build and assemble Scene 12: Backpropagation at Scale & The Grand Intuition."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    # Subtitles 151 to 172 span:
    # 00:06:43,900 --> 00:07:39,192 (403.90s to 459.192s, Duration = 55.30s)
    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            scene.add_audio(str(p), start=0.0, trim_start=403.90, trim_end=459.192)

    viewport = Viewport(Scene12ScaleAndIntuitionSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_12_DURATION)
    return scene
