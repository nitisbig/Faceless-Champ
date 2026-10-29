"""Scene 11: The Synaptic Path from Weight to Loss.

Curriculum Chapter 6: Inside the AI Brain: Backpropagation as Reverse Gears.
Pure pitch-black void canvas (#000000), zero text clutter, Euler-style MathTex,
3-layer luminous neural lattice in upper hemisphere, forward propagation pulse,
crimson loss beacon, and grand 4-factor Chain Rule master gradient formulation in lower hemisphere.
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

SCENE_11_DURATION: float = 33.30

# High-Voltage Electric RGB Color Palette (Matching euler_scene.py)
CYAN = "#00F5FF"     # Electric Laser Cyan (Input Layer X, x_i, dz/dw)
GOLD = "#FFB800"     # Radiant Gold (Hidden Layer H, Weight w, da/dz, z, a)
WHITE = "#FFFFFF"    # Crisp Pure White (Operators, equals, fraction bars, grid ticks)
MINT = "#05FFA1"     # High-Voltage Neon Mint (Total gradient dL/dw, verified rate)
CORAL = "#FF2A6D"    # Laser Neon Coral (Output Layer Y_hat, Loss L, dL/dy_hat)
AMBER = "#FF8800"    # Radiant Amber (Output weights W2, dy_hat/da)
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


class Scene11NeuralChainSource:
    """High-voltage neural backpropagation visualization source with zero text clutter."""

    duration: float = SCENE_11_DURATION
    fps: int = 30
    intrinsic_size: tuple[int, int] = (1920, 1080)
    fingerprint: str = "chain:scene-11:synaptic-path:v1"
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

                # -------------------------------------------------------------
                # PRECOMPILE ALL MATHEMATICAL EQUATIONS IN EULER MATHTEX
                # -------------------------------------------------------------
                # 1. Shot 11A: Layer Dimensions Formula (0.0s - 7.5s)
                self.img_layer_flow, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{X \in \mathbb{R}^4}", CYAN, 18),
                        (r"\longrightarrow", WHITE, 18),
                        (r"\mathbf{H \in \mathbb{R}^5}", GOLD, 18),
                        (r"\longrightarrow", WHITE, 18),
                        (r"\mathbf{\hat{Y} \in \mathbb{R}^2}", CORAL, 0),
                    ],
                    font_size=42,
                    spacing=18,
                )

                # 2. Shot 11B: Weight dial label
                self.img_weight_w, _, _ = _compose_latex_equation(
                    [(r"\mathbf{w_{ij}}", GOLD, 0)],
                    font_size=36,
                )

                # 3. Shot 11B: Pre-activation Linear Combination z = w * x + b
                self.img_neuron_affine, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{z}", GOLD, 12),
                        (r"=", WHITE, 12),
                        (r"\mathbf{w}", GOLD, 6),
                        (r"\cdot", CYAN, 6),
                        (r"\mathbf{x}", CYAN, 12),
                        (r"+", WHITE, 12),
                        (r"\mathbf{b}", WHITE, 0),
                    ],
                    font_size=34,
                    spacing=10,
                )

                # 4. Shot 11B: Activation Output a = sigma(z) = 1 / (1 + e^-z)
                self.img_neuron_sigma, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{a}", GOLD, 10),
                        (r"=", WHITE, 10),
                        (r"\mathbf{\sigma(z)}", GOLD, 10),
                        (r"=", WHITE, 10),
                        (r"\mathbf{\frac{1}{1 + e^{-z}}}", WHITE, 0),
                    ],
                    font_size=34,
                    spacing=10,
                )

                # 5. Shot 11C: Layer 2 Weight W_2
                self.img_weight_w2, _, _ = _compose_latex_equation(
                    [(r"\mathbf{W_2}", AMBER, 0)],
                    font_size=32,
                )

                # 6. Shot 11C: Prediction Vector y_hat
                self.img_pred_yhat, _, _ = _compose_latex_equation(
                    [(r"\mathbf{\hat{y}}", CORAL, 0)],
                    font_size=38,
                )

                # 7. Shot 11C: Quadratic Loss Function L = 1/2 ||y_hat - y*||^2
                self.img_loss_beacon, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{\mathcal{L}}", CORAL, 12),
                        (r"=", WHITE, 12),
                        (r"\mathbf{\frac{1}{2}}\left\|\mathbf{\hat{y}} - \mathbf{y}^*\right\|^2", CORAL, 0),
                    ],
                    font_size=38,
                    spacing=12,
                )

                # 8. Shot 11D: Grand 4-Factor Master Chain Rule Gradient Equation
                # Terms breakdown:
                # 0: dL/dw (Mint)
                # 1: = (White)
                # 2: dL/dy_hat (Coral)
                # 3: \cdot (White)
                # 4: dy_hat/da (Amber)
                # 5: \cdot (White)
                # 6: da/dz (Gold)
                # 7: \cdot (White)
                # 8: dz/dw (Cyan)
                (
                    self.img_chain_gradient,
                    self.chain_term_centers,
                    self.chain_term_widths,
                ) = _compose_latex_equation(
                    [
                        (r"\mathbf{\frac{\partial \mathcal{L}}{\partial w}}", MINT, 20),
                        (r"=", WHITE, 20),
                        (r"\mathbf{\frac{\partial \mathcal{L}}{\partial \hat{y}}}", CORAL, 24),
                        (r"\cdot", WHITE, 24),
                        (r"\mathbf{\frac{\partial \hat{y}}{\partial a}}", AMBER, 24),
                        (r"\cdot", WHITE, 24),
                        (r"\mathbf{\frac{\partial a}{\partial z}}", GOLD, 24),
                        (r"\cdot", WHITE, 24),
                        (r"\mathbf{\frac{\partial z}{\partial w}}", CYAN, 0),
                    ],
                    font_size=48,
                    spacing=20,
                )

                # 9. Shot 11D: Local Rate Value Calipers
                self.img_rate_loss_val, _, _ = _compose_latex_equation(
                    [(r"\mathbf{(\hat{y} - y^*)}", CORAL, 0)],
                    font_size=26,
                )
                self.img_rate_output_val, _, _ = _compose_latex_equation(
                    [(r"\mathbf{W_2}", AMBER, 0)],
                    font_size=26,
                )
                self.img_rate_act_val, _, _ = _compose_latex_equation(
                    [(r"\mathbf{\sigma'(z)}", GOLD, 0)],
                    font_size=26,
                )
                self.img_rate_affine_val, _, _ = _compose_latex_equation(
                    [(r"\mathbf{x}", CYAN, 0)],
                    font_size=26,
                )

                # 10. Shot 11D: Conduit Rail Station Tokens
                self.img_tok_w, _, _ = _compose_latex_equation([(r"\mathbf{w}", GOLD, 0)], font_size=28)
                self.img_tok_z, _, _ = _compose_latex_equation([(r"\mathbf{z}", GOLD, 0)], font_size=28)
                self.img_tok_a, _, _ = _compose_latex_equation([(r"\mathbf{a}", GOLD, 0)], font_size=28)
                self.img_tok_y, _, _ = _compose_latex_equation([(r"\mathbf{\hat{y}}", CORAL, 0)], font_size=28)
                self.img_tok_L, _, _ = _compose_latex_equation([(r"\mathbf{\mathcal{L}}", CORAL, 0)], font_size=28)

                # 11. Shot 11D: Gradient Descent Weight Update Rule
                self.img_grad_update, _, _ = _compose_latex_equation(
                    [
                        (r"\mathbf{w}", GOLD, 14),
                        (r"\longleftarrow", WHITE, 14),
                        (r"\mathbf{w}", GOLD, 12),
                        (r"-", WHITE, 12),
                        (r"\mathbf{\eta}", MINT, 12),
                        (r"\mathbf{\frac{\partial \mathcal{L}}{\partial w}}", MINT, 0),
                    ],
                    font_size=40,
                    spacing=14,
                )

                # -------------------------------------------------------------
                # 3-LAYER NEURAL LATTICE NODE POSITIONS (Upper Hemisphere: y in [160, 500])
                # -------------------------------------------------------------
                # Layer 1: Input (4 nodes) at x = 360, centered around y = 335
                self.input_nodes = [(360.0, 200.0 + i * 90.0) for i in range(4)]   # y = 200, 290, 380, 470
                # Layer 2: Hidden (5 nodes) at x = 960, centered around y = 330
                self.hidden_nodes = [(960.0, 160.0 + i * 85.0) for i in range(5)]  # y = 160, 245, 330, 415, 500
                # Layer 3: Output (2 nodes) at x = 1460, centered around y = 335
                self.output_nodes = [(1460.0, 280.0 + i * 110.0) for i in range(2)]  # y = 280, 390

                # Precompile Sigmoid Curve Path (Local coordinate space)
                self.sigmoid_points = []
                for step_idx in range(50):
                    zv = -4.0 + (8.0 * step_idx / 49.0)
                    av = 1.0 / (1.0 + math.exp(-zv))
                    self.sigmoid_points.append((zv, av))

            def frame(self, t: float) -> Image.Image:
                canvas = self.canvas
                w = self.w
                h = self.h
                sx = self.sx
                sy = self.sy

                # Pure Pitch-Black Void Canvas
                canvas.clear(skia.ColorSetARGB(255, 0, 0, 0))

                # =========================================================================
                # 1. SHOT 11A: THE 3-LAYER NEURAL LATTICE (0.0s - 7.5s)
                # =========================================================================
                lattice_alpha = _smoothstep(0.0, 1.5, t)
                # In Shot 11B, 11C, 11D, ambient non-active connections dim smoothly to 10%
                macro_dim = _smoothstep(7.0, 8.5, t)
                ambient_alpha = (1.0 - 0.90 * macro_dim) * lattice_alpha

                # Layer 1 -> Layer 2 Synaptic Filaments
                syn_paint = skia.Paint(
                    Color=_skia_color(VIOLET, 0.22 * ambient_alpha),
                    StrokeWidth=1.2 * sx,
                    AntiAlias=True,
                )
                for in_x, in_y in self.input_nodes:
                    for hid_x, hid_y in self.hidden_nodes:
                        canvas.drawLine(in_x * sx, in_y * sy, hid_x * sx, hid_y * sy, syn_paint)

                # Layer 2 -> Layer 3 Synaptic Filaments
                syn2_paint = skia.Paint(
                    Color=_skia_color(AMBER, 0.18 * ambient_alpha),
                    StrokeWidth=1.2 * sx,
                    AntiAlias=True,
                )
                for hid_x, hid_y in self.hidden_nodes:
                    for out_x, out_y in self.output_nodes:
                        canvas.drawLine(hid_x * sx, hid_y * sy, out_x * sx, out_y * sy, syn2_paint)

                # Bioluminescent ambient node halos & cores
                # Input Nodes (Cyan)
                for idx, (nx, ny) in enumerate(self.input_nodes):
                    node_alpha = _smoothstep(0.2 + idx * 0.15, 1.2 + idx * 0.15, t) * lattice_alpha
                    core_a = 0.95 * node_alpha if (macro_dim < 1.0 or idx == 1) else 0.25 * node_alpha
                    canvas.drawCircle(nx * sx, ny * sy, 18.0 * sx, skia.Paint(
                        Color=_skia_color(CYAN, 0.22 * core_a),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawCircle(nx * sx, ny * sy, 8.5 * sx, skia.Paint(
                        Color=_skia_color(CYAN, core_a),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))

                # Hidden Nodes (Gold)
                for idx, (nx, ny) in enumerate(self.hidden_nodes):
                    node_alpha = _smoothstep(0.5 + idx * 0.12, 1.5 + idx * 0.12, t) * lattice_alpha
                    core_a = 0.95 * node_alpha if (macro_dim < 1.0 or idx == 2) else 0.25 * node_alpha
                    canvas.drawCircle(nx * sx, ny * sy, 20.0 * sx, skia.Paint(
                        Color=_skia_color(GOLD, 0.22 * core_a),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawCircle(nx * sx, ny * sy, 9.5 * sx, skia.Paint(
                        Color=_skia_color(GOLD, core_a),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))

                # Output Nodes (Coral)
                for idx, (nx, ny) in enumerate(self.output_nodes):
                    node_alpha = _smoothstep(0.8 + idx * 0.2, 1.8 + idx * 0.2, t) * lattice_alpha
                    core_a = 0.95 * node_alpha if (macro_dim < 1.0 or idx == 0) else 0.25 * node_alpha
                    canvas.drawCircle(nx * sx, ny * sy, 22.0 * sx, skia.Paint(
                        Color=_skia_color(CORAL, 0.25 * core_a),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    canvas.drawCircle(nx * sx, ny * sy, 10.5 * sx, skia.Paint(
                        Color=_skia_color(CORAL, core_a),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))

                # Top Title Formula: X in R4 -> H in R5 -> Y_hat in R2 (active 0.0s - 7.5s)
                flow_alpha = _smoothstep(0.5, 1.8, t) * (1.0 - _smoothstep(6.8, 8.0, t))
                _draw_math_centered(canvas, self.img_layer_flow, 960.0 * sx, 75.0 * sy, alpha=flow_alpha, base_scale=0.52 * sx)

                # =========================================================================
                # 2. SHOT 11B: MACRO ISOLATION OF WEIGHT DIAL & NEURON MECHANICS (7.5s - 16.5s)
                # =========================================================================
                shot_b_alpha = _smoothstep(7.5, 9.0, t)
                active_in = self.input_nodes[1]    # Node x2 at (360, 290)
                active_hid = self.hidden_nodes[2]  # Node h3 at (960, 330)
                active_out = self.output_nodes[0]  # Node y1 at (1460, 280)

                x1_px, y1_px = active_in[0] * sx, active_in[1] * sy
                x2_px, y2_px = active_hid[0] * sx, active_hid[1] * sy
                x3_px, y3_px = active_out[0] * sx, active_out[1] * sy

                if shot_b_alpha > 0.0:
                    # High-Intensity Synaptic Line (x1 -> h2) in Radiant Gold
                    canvas.drawLine(x1_px, y1_px, x2_px, y2_px, skia.Paint(
                        Color=_skia_color(GOLD, 0.40 * shot_b_alpha),
                        StrokeWidth=7.0 * sx,
                        AntiAlias=True,
                    ))
                    canvas.drawLine(x1_px, y1_px, x2_px, y2_px, skia.Paint(
                        Color=_skia_color(GOLD, 0.98 * shot_b_alpha),
                        StrokeWidth=2.6 * sx,
                        AntiAlias=True,
                    ))

                    # Rotary Weight Dial w_ij positioned along the line (at 50% midpoint)
                    dial_cx = (x1_px + x2_px) / 2.0
                    dial_cy = (y1_px + y2_px) / 2.0
                    dial_r = 32.0 * sx

                    # Dial Background Plate
                    canvas.drawCircle(dial_cx, dial_cy, dial_r, skia.Paint(
                        Color=_skia_color("#050c18", 0.94 * shot_b_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))
                    # Dial Border
                    canvas.drawCircle(dial_cx, dial_cy, dial_r, skia.Paint(
                        Color=_skia_color(GOLD, 0.95 * shot_b_alpha),
                        StrokeWidth=2.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))

                    # Radial graduation ticks on weight dial (12 ticks)
                    for tick_i in range(12):
                        ta = tick_i * (2.0 * math.pi / 12.0)
                        tr0 = dial_r - 5.5 * sx
                        tr1 = dial_r - 1.5 * sx
                        canvas.drawLine(
                            dial_cx + tr0 * math.cos(ta), dial_cy + tr0 * math.sin(ta),
                            dial_cx + tr1 * math.cos(ta), dial_cy + tr1 * math.sin(ta),
                            skia.Paint(
                                Color=_skia_color(WHITE, 0.60 * shot_b_alpha),
                                StrokeWidth=1.4 * sx,
                                AntiAlias=True,
                            ),
                        )

                    # Dial Needle (Rotates smoothly)
                    n_angle = math.radians(-45.0 + 35.0 * math.sin(t * 2.2))
                    canvas.drawLine(
                        dial_cx, dial_cy,
                        dial_cx + (dial_r - 7.0 * sx) * math.cos(n_angle),
                        dial_cy + (dial_r - 7.0 * sx) * math.sin(n_angle),
                        skia.Paint(
                            Color=_skia_color(CYAN, 0.98 * shot_b_alpha),
                            StrokeWidth=2.2 * sx,
                            AntiAlias=True,
                        ),
                    )
                    canvas.drawCircle(dial_cx, dial_cy, 4.5 * sx, skia.Paint(
                        Color=_skia_color(WHITE, 0.98 * shot_b_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    ))

                    # Weight Label above dial
                    _draw_math_centered(canvas, self.img_weight_w, dial_cx, dial_cy - dial_r - 20.0 * sy, alpha=shot_b_alpha, base_scale=0.50 * sx)

                    # Destination Hidden Neuron Mechanics: Node h2 at (960, 330)
                    hid_cx, hid_cy = x2_px, y2_px
                    pulse_r = (24.0 + 5.0 * math.sin(t * 3.5)) * sx
                    canvas.drawCircle(hid_cx, hid_cy, pulse_r, skia.Paint(
                        Color=_skia_color(GOLD, 0.45 * shot_b_alpha),
                        StrokeWidth=1.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    ))

                    # 1. Linear combination: z = w * x + b (active from 10.0s, fades at 24.5s)
                    z_alpha = _smoothstep(10.0, 11.5, t) * (1.0 - _smoothstep(24.5, 25.8, t))
                    if z_alpha > 0.0:
                        _draw_math_centered(canvas, self.img_neuron_affine, hid_cx, hid_cy - 115.0 * sy, alpha=z_alpha, base_scale=0.52 * sx)

                    # 2. Activation transfer: a = sigma(z) (active from 13.5s, fades at 24.5s)
                    act_alpha = _smoothstep(13.5, 14.8, t) * (1.0 - _smoothstep(24.5, 25.8, t))
                    if act_alpha > 0.0:
                        # Sigmoid formula below
                        _draw_math_centered(canvas, self.img_neuron_sigma, hid_cx + 115.0 * sx, hid_cy + 75.0 * sy, alpha=act_alpha, base_scale=0.48 * sx)

                        # Manim Sigmoid Plot Mini-Graph beside Node h2 (Offset to the right)
                        gw = 100.0 * sx
                        gh = 50.0 * sy
                        gx = hid_cx + 105.0 * sx
                        gy = hid_cy
                        # Mini Axes
                        canvas.drawLine(gx - gw / 2.0, gy, gx + gw / 2.0, gy, skia.Paint(
                            Color=_skia_color(WHITE, 0.35 * act_alpha),
                            StrokeWidth=1.2 * sx,
                            AntiAlias=True,
                        ))
                        canvas.drawLine(gx, gy - gh / 2.0, gx, gy + gh / 2.0, skia.Paint(
                            Color=_skia_color(WHITE, 0.35 * act_alpha),
                            StrokeWidth=1.2 * sx,
                            AntiAlias=True,
                        ))

                        # Draw Sigmoid S-Curve
                        sig_path = skia.Path()
                        for s_i, (zv, av) in enumerate(self.sigmoid_points):
                            px = gx + (zv / 4.0) * (gw / 2.0)
                            py = gy - (av - 0.5) * gh
                            if s_i == 0:
                                sig_path.moveTo(px, py)
                            else:
                                sig_path.lineTo(px, py)

                        canvas.drawPath(sig_path, skia.Paint(
                            Color=_skia_color(GOLD, 0.95 * act_alpha),
                            StrokeWidth=2.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        ))

                        # Glowing Operating Point on Sigmoid Curve (z = 1.0, a = 0.73)
                        op_px = gx + (1.0 / 4.0) * (gw / 2.0)
                        op_py = gy - (0.731 - 0.5) * gh
                        canvas.drawCircle(op_px, op_py, 4.0 * sx, skia.Paint(
                            Color=_skia_color(MINT, 0.98 * act_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                # =========================================================================
                # 3. SHOT 11C: FORWARD PROPAGATION & CRIMSON LOSS BEACON (16.5s - 25.0s)
                # =========================================================================
                shot_c_alpha = _smoothstep(16.5, 18.0, t)
                beacon_cx = 1700.0 * sx
                beacon_cy = 280.0 * sy

                if shot_c_alpha > 0.0:
                    # High-Energy Synaptic Beam from Hidden Node 2 to Output Node 0
                    canvas.drawLine(x2_px, y2_px, x3_px, y3_px, skia.Paint(
                        Color=_skia_color(AMBER, 0.40 * shot_c_alpha),
                        StrokeWidth=6.5 * sx,
                        AntiAlias=True,
                    ))
                    canvas.drawLine(x2_px, y2_px, x3_px, y3_px, skia.Paint(
                        Color=_skia_color(AMBER, 0.98 * shot_c_alpha),
                        StrokeWidth=2.4 * sx,
                        AntiAlias=True,
                    ))

                    # Weight W2 label along synapse
                    w2_alpha = shot_c_alpha * (1.0 - _smoothstep(24.5, 25.8, t))
                    _draw_math_centered(canvas, self.img_weight_w2, (x2_px + x3_px) / 2.0 + 20.0 * sx, (y2_px + y3_px) / 2.0 - 18.0 * sy, alpha=w2_alpha, base_scale=0.50 * sx)

                    # Traveling Photon Data Packet (propagates from 17.0s to 19.5s)
                    pulse_t = _smoothstep(17.0, 19.5, t)
                    if 0.0 < pulse_t < 1.0:
                        px = x2_px + pulse_t * (x3_px - x2_px)
                        py = y2_px + pulse_t * (y3_px - y2_px)
                        canvas.drawCircle(px, py, 12.0 * sx, skia.Paint(
                            Color=_skia_color(MINT, 0.45 * shot_c_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(px, py, 5.0 * sx, skia.Paint(
                            Color=_skia_color(WHITE, 0.98 * shot_c_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                    # Prediction Output Label at Output Node 0
                    pred_alpha = _smoothstep(19.0, 20.2, t)
                    _draw_math_centered(canvas, self.img_pred_yhat, x3_px + 45.0 * sx, y3_px, alpha=pred_alpha, base_scale=0.52 * sx)

                    # Synapse from Output Node to Target Beacon
                    canvas.drawLine(x3_px, y3_px, beacon_cx, beacon_cy, skia.Paint(
                        Color=_skia_color(CORAL, 0.40 * shot_c_alpha),
                        StrokeWidth=2.0 * sx,
                        AntiAlias=True,
                    ))

                    # Crimson Loss Beacon at the output target (active from 20.5s)
                    loss_alpha = _smoothstep(20.5, 22.0, t)
                    if loss_alpha > 0.0:
                        # Radial Pulsing Shockwave Rings
                        shock_p = (t * 1.6) % 1.0
                        for sw_i in range(3):
                            sw_prog = (shock_p + sw_i * 0.33) % 1.0
                            sw_r = (25.0 + sw_prog * 85.0) * sx
                            sw_a = (1.0 - sw_prog) * 0.70 * loss_alpha
                            canvas.drawCircle(beacon_cx, beacon_cy, sw_r, skia.Paint(
                                Color=_skia_color(CORAL, sw_a),
                                StrokeWidth=2.0 * sx,
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            ))

                        # Loss Beacon Core Bullseye
                        canvas.drawCircle(beacon_cx, beacon_cy, 22.0 * sx, skia.Paint(
                            Color=_skia_color(CORAL, 0.35 * loss_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(beacon_cx, beacon_cy, 9.0 * sx, skia.Paint(
                            Color=_skia_color(WHITE, 0.98 * loss_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                        # Quadratic Loss Formula above Beacon (Safe coordinates, no clipping!)
                        _draw_math_centered(canvas, self.img_loss_beacon, beacon_cx - 20.0 * sx, beacon_cy - 120.0 * sy, alpha=loss_alpha, base_scale=0.52 * sx)

                # =========================================================================
                # 4. LOWER HEMISPHERE: DIVIDER & 5-STATION CONDUIT RAIL (24.5s - 33.30s)
                # =========================================================================
                shot_d_alpha = _smoothstep(24.5, 26.0, t)
                if shot_d_alpha > 0.0:
                    # Sleek horizontal laser divider at y = 550
                    div_y = 550.0 * sy
                    canvas.drawLine(240.0 * sx, div_y, 1680.0 * sx, div_y, skia.Paint(
                        Color=_skia_color("#1a2b3c", 0.70 * shot_d_alpha),
                        StrokeWidth=1.5 * sx,
                        AntiAlias=True,
                    ))

                    # 5-Station Horizontal Synaptic Pathway Conduit Rail at y = 615
                    rail_y = 615.0 * sy
                    c_x_w = 420.0 * sx
                    c_x_z = 690.0 * sx
                    c_x_a = 960.0 * sx
                    c_x_y = 1230.0 * sx
                    c_x_L = 1500.0 * sx

                    # Glowing Rail Track
                    canvas.drawLine(c_x_w, rail_y, c_x_L, rail_y, skia.Paint(
                        Color=_skia_color(WHITE, 0.22 * shot_d_alpha),
                        StrokeWidth=2.0 * sx,
                        AntiAlias=True,
                    ))

                    # Forward connection arrows (between stations)
                    arrow_paint = skia.Paint(
                        Color=_skia_color(WHITE, 0.40 * shot_d_alpha),
                        StrokeWidth=1.5 * sx,
                        AntiAlias=True,
                    )
                    station_xs = [c_x_w, c_x_z, c_x_a, c_x_y, c_x_L]
                    station_tokens = [self.img_tok_w, self.img_tok_z, self.img_tok_a, self.img_tok_y, self.img_tok_L]
                    station_colors = [GOLD, GOLD, GOLD, CORAL, CORAL]

                    for s_idx in range(4):
                        mid_seg_x = (station_xs[s_idx] + station_xs[s_idx + 1]) / 2.0
                        # Small forward arrowhead '>'
                        ah = 6.0 * sx
                        canvas.drawLine(mid_seg_x - ah, rail_y - ah, mid_seg_x + ah, rail_y, arrow_paint)
                        canvas.drawLine(mid_seg_x - ah, rail_y + ah, mid_seg_x + ah, rail_y, arrow_paint)

                    # 5 Station Nodes
                    for s_x, s_tok, s_col in zip(station_xs, station_tokens, station_colors):
                        canvas.drawCircle(s_x, rail_y, 14.0 * sx, skia.Paint(
                            Color=_skia_color(s_col, 0.28 * shot_d_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(s_x, rail_y, 6.0 * sx, skia.Paint(
                            Color=_skia_color(WHITE, 0.95 * shot_d_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        # Token label above station node
                        _draw_math_centered(canvas, s_tok, s_x, rail_y - 24.0 * sy, alpha=shot_d_alpha, base_scale=0.50 * sx)

                    # =====================================================================
                    # 5. GRAND MASTER CHAIN RULE GRADIENT EQUATION (25.5s - 33.30s)
                    # =====================================================================
                    eq_alpha = _smoothstep(25.5, 27.0, t)
                    eq_cx = 960.0 * sx
                    eq_cy = 730.0 * sy

                    eq_scale = _draw_math_centered(canvas, self.img_chain_gradient, eq_cx, eq_cy, alpha=eq_alpha, base_scale=0.56 * sx)

                    # Dynamic Rate Calipers / Local Derivative Identifiers (active from 27.5s)
                    cal_alpha = _smoothstep(27.5, 29.0, t)
                    if cal_alpha > 0.0 and self.chain_term_centers:
                        # Exact screen X coordinates calculated directly from TeX token centers
                        eq_left = eq_cx - (self.img_chain_gradient.width() * eq_scale) / 2.0

                        # Term indices in img_chain_gradient:
                        # 2: dL/dy_hat (Coral)
                        # 4: dy_hat/da (Amber)
                        # 6: da/dz (Gold)
                        # 8: dz/dw (Cyan)
                        t_indices = [2, 4, 6, 8]
                        cal_colors = [CORAL, AMBER, GOLD, CYAN]
                        cal_imgs = [
                            self.img_rate_loss_val,
                            self.img_rate_output_val,
                            self.img_rate_act_val,
                            self.img_rate_affine_val,
                        ]

                        bracket_y = eq_cy + 55.0 * sy
                        val_y = bracket_y + 40.0 * sy

                        for t_idx, c_hex, c_img in zip(t_indices, cal_colors, cal_imgs):
                            term_cx = eq_left + self.chain_term_centers[t_idx] * eq_scale
                            term_w = self.chain_term_widths[t_idx] * eq_scale * 0.85

                            # Horizontal bracket line
                            canvas.drawLine(term_cx - term_w / 2.0, bracket_y, term_cx + term_w / 2.0, bracket_y, skia.Paint(
                                Color=_skia_color(c_hex, 0.85 * cal_alpha),
                                StrokeWidth=2.0 * sx,
                                AntiAlias=True,
                            ))
                            # Left & right vertical tick tips
                            canvas.drawLine(term_cx - term_w / 2.0, bracket_y - 5.0 * sy, term_cx - term_w / 2.0, bracket_y, skia.Paint(
                                Color=_skia_color(c_hex, 0.90 * cal_alpha),
                                StrokeWidth=1.6 * sx,
                                AntiAlias=True,
                            ))
                            canvas.drawLine(term_cx + term_w / 2.0, bracket_y - 5.0 * sy, term_cx + term_w / 2.0, bracket_y, skia.Paint(
                                Color=_skia_color(c_hex, 0.90 * cal_alpha),
                                StrokeWidth=1.6 * sx,
                                AntiAlias=True,
                            ))

                            # Evaluated local derivative below bracket
                            _draw_math_centered(canvas, c_img, term_cx, val_y, alpha=cal_alpha, base_scale=0.52 * sx)

                    # =====================================================================
                    # 6. REVERSE BACKPROPAGATION BEAMS & GRADIENT DESCENT UPDATE (29.5s - 33.3s)
                    # =====================================================================
                    backprop_alpha = _smoothstep(29.5, 31.0, t)
                    if backprop_alpha > 0.0:
                        # Reverse Laser Pulse travelling from Right to Left (L -> y -> a -> z -> w)
                        rev_prog = _smoothstep(29.8, 32.5, t)
                        cur_rail_x = c_x_L - rev_prog * (c_x_L - c_x_w)

                        # Draw laser beam along rail (Right to Left)
                        canvas.drawLine(c_x_L, rail_y, cur_rail_x, rail_y, skia.Paint(
                            Color=_skia_color(MINT, 0.95 * backprop_alpha),
                            StrokeWidth=3.2 * sx,
                            AntiAlias=True,
                        ))
                        # Traveling Mint Photon Packet
                        canvas.drawCircle(cur_rail_x, rail_y, 9.0 * sx, skia.Paint(
                            Color=_skia_color(MINT, 0.45 * backprop_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(cur_rail_x, rail_y, 4.0 * sx, skia.Paint(
                            Color=_skia_color(WHITE, 0.98 * backprop_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                        # Simultaneously in upper hemisphere: reverse pulse flows along active network synapses!
                        if rev_prog < 0.5:
                            # From beacon to output to hidden
                            p_seg = rev_prog / 0.5
                            upper_x = beacon_cx - p_seg * (beacon_cx - x2_px)
                            upper_y = beacon_cy - p_seg * (beacon_cy - y2_px)
                        else:
                            # From hidden to weight to input
                            p_seg = (rev_prog - 0.5) / 0.5
                            upper_x = x2_px - p_seg * (x2_px - x1_px)
                            upper_y = y2_px - p_seg * (y2_px - y1_px)

                        canvas.drawCircle(upper_x, upper_y, 11.0 * sx, skia.Paint(
                            Color=_skia_color(MINT, 0.50 * backprop_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))
                        canvas.drawCircle(upper_x, upper_y, 4.5 * sx, skia.Paint(
                            Color=_skia_color(WHITE, 0.98 * backprop_alpha),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        ))

                        # Bottom Highlighted Badge: Gradient Descent Weight Update Rule (active from 30.5s)
                        upd_alpha = _smoothstep(30.5, 32.0, t)
                        if upd_alpha > 0.0:
                            upd_cx = 960.0 * sx
                            upd_cy = 950.0 * sy

                            # Luminous badge plate
                            bw = 520.0 * sx
                            bh = 70.0 * sy
                            r_rect = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(upd_cx - bw / 2.0, upd_cy - bh / 2.0, bw, bh), 16.0 * sx, 16.0 * sy)

                            canvas.drawRRect(r_rect, skia.Paint(
                                Color=_skia_color("#051810", 0.75 * upd_alpha),
                                Style=skia.Paint.kFill_Style,
                                AntiAlias=True,
                            ))
                            canvas.drawRRect(r_rect, skia.Paint(
                                Color=_skia_color(MINT, 0.70 * upd_alpha),
                                StrokeWidth=2.2 * sx,
                                Style=skia.Paint.kStroke_Style,
                                AntiAlias=True,
                            ))

                            _draw_math_centered(canvas, self.img_grad_update, upd_cx, upd_cy, alpha=upd_alpha, base_scale=0.55 * sx)

                snapshot = self.surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_11(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build and assemble Scene 11: The Synaptic Path from Weight to Loss."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    # Subtitles 138 to 150 span:
    # 00:06:11,090 --> 00:06:43,900 (370.60s to 403.90s, Duration = 33.30s)
    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            scene.add_audio(str(p), start=0.0, trim_start=370.60, trim_end=403.90)

    viewport = Viewport(Scene11NeuralChainSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_11_DURATION)
    return scene
