"""Scene 01: Inside the AI Brain (7-Layer Prism Architecture, Compact Sharp Neurons, Void Black).

High-end computational visualization:
- Zero text (clean screen, pure motion graphics).
- Pure black void background (#000000).
- 7 distinctly colored layers across the optical spectrum:
    L0: Electric Cyan (#00F0FF) - 10 Input nodes
    L1: Neon Emerald (#00F5A0) - 14 Feature nodes
    L2: Cyber Amber (#FBBF24) - 18 Feature nodes
    L3: Deep Ultraviolet (#A855F7) - 26 Central Latent Core nodes
    L4: Hot Neon Fuchsia (#EC4899) - 18 High-Level Feature nodes
    L5: Electric Cobalt (#38BDF8) - 14 Decision Plane nodes
    L6: Ice White / Ruby (#FFFFFF / #FF1E44) - 8 Output Logit nodes
    Total: 108 neurons.
- 1,692 dynamically swinging cubic Bézier connection filaments with harmonic wave physics.
- Refined, compact, microscopic neurons: razor-sharp aperture discs, tight non-overlapping
  ambient halos, precision orbital reticles, and white-hot photonic center sparks.
- Pure visual holographic synaptic dial (12.0s - 21.5s):
    Anchored to highlighted golden synapse with 36 radial calibration ticks, dynamic filling
    circular arc gauge, rotating needle (-30° to +60°), and harmonic golden ripple beads.
- Pure visual input hologram (21.5s - 40.7s):
    28x28 phosphor digit '7' matrix card with sweeping laser scanline and optical conduits
    pulsing energy packets into Layer 0 input nodes.
- High-velocity 6-stage forward propagation cascade (23.8s - 31.0s):
    Radiant photon streams surge across all 7 layers, exciting each layer into brilliant luminescence.
- Output distribution & crimson loss shockwave (31.0s - 40.7s):
    8 sleek horizontal probability distribution meters; at t=33.5s, the erroneous node detonates
    with a blazing ruby crimson loss flare, emitting expanding shockwaves and reverse tension ripples.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

import skia
from PIL import Image

from faceless_champ import (
    Canvas,
    Scene,
    Viewport,
)

SCENE_01_DURATION = 40.70

# 7 Distinct, Sharp Layer Palette Colors (RGB floats 0.0 - 1.0)
LAYER_PALETTES = (
    (0.00, 0.94, 1.00),  # L0: Electric Cyan
    (0.00, 0.96, 0.63),  # L1: Neon Emerald
    (0.98, 0.75, 0.14),  # L2: Cyber Amber / Solar Gold
    (0.68, 0.35, 0.98),  # L3: Deep Ultraviolet / Neon Violet (26-node Core)
    (0.95, 0.28, 0.62),  # L4: Hot Neon Fuchsia
    (0.22, 0.65, 0.98),  # L5: Electric Cobalt
    (0.96, 0.98, 1.00),  # L6: Crystalline Ice White (Output)
)


def cubic_pts(x1: float, y1: float, x2: float, y2: float, sway: float, num_pts: int = 14) -> list[tuple[float, float]]:
    """Compute sampled points along a swinging cubic Bézier curve."""
    dx = x2 - x1
    sag = (y2 - y1) * 0.035
    c1x, c1y = x1 + dx * 0.48, y1 + sag + sway
    c2x, c2y = x2 - dx * 0.48, y2 - sag - sway
    pts = []
    for step in range(num_pts):
        u = step / (num_pts - 1)
        v = 1.0 - u
        x = v**3 * x1 + 3 * v**2 * u * c1x + 3 * v * u**2 * c2x + u**3 * x2
        y = v**3 * y1 + 3 * v**2 * u * c1y + 3 * v * u**2 * c2y + u**3 * y2
        pts.append((x, y))
    return pts


@dataclass(frozen=True)
class FluidNeuralNetworkSource:
    """Procedural raster source rendering 108 nodes, 1,692 swinging connections, and all visual HUD events."""

    intrinsic_size: tuple[int, int] = (1920, 1080)
    duration: float = SCENE_01_DURATION
    fingerprint: str = "chain-rule:7-layer-prism-nn:v5"
    requirements: tuple[str, ...] = ()

    def frame_key(self, source_time: float) -> int:
        return int(source_time * 60)

    def open(self, size: tuple[int, int]):
        w, h = size
        sx = w / 1920.0
        sy = h / 1080.0

        # Enforce true RGBA8888 color space
        info = skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
        surface = skia.Surface.MakeRaster(info)
        canvas = surface.getCanvas()

        # 1. Architecture: 108 neurons across 7 distinct layers
        layer_counts = (10, 14, 18, 26, 18, 14, 8)
        xs = (315.0, 530.0, 745.0, 960.0, 1175.0, 1390.0, 1605.0)
        center_y = 540.0
        spacings = (60.0, 46.0, 38.0, 28.0, 38.0, 46.0, 74.0)

        base_positions: list[list[tuple[float, float]]] = []
        phases: list[list[float]] = []
        rng = random.Random(42)

        for count, x, spacing in zip(layer_counts, xs, spacings):
            pts = []
            layer_phases = []
            for i in range(count):
                y = center_y + (i - (count - 1) / 2) * spacing
                pts.append((x, y))
                layer_phases.append(rng.uniform(0, math.tau))
            base_positions.append(pts)
            phases.append(layer_phases)

        # 2. Precompute 1,692 connections with individual harmonic wave physics
        conns: list[tuple[int, int, int, float, float, float, float, int]] = []
        for l_idx, (left, right) in enumerate(pairwise(base_positions)):
            for i in range(len(left)):
                for j in range(len(right)):
                    weight = rng.uniform(-1.0, 1.0)
                    sway_phase = rng.uniform(0, math.tau)
                    freq = rng.uniform(1.3, 2.3)
                    amp = rng.uniform(5.0, 11.0)
                    depth_tier = 1 if abs(weight) > 0.45 else 0
                    conns.append((l_idx, i, j, weight, sway_phase, freq, amp, depth_tier))

        # Reusable paints
        bg_clear = skia.Color4f(0.0, 0.0, 0.0, 1.0)
        conn_paint = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
        gold_stroke = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
        fill_paint = skia.Paint(Style=skia.Paint.kFill_Style, AntiAlias=True)
        stroke_paint = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)

        class Session:
            def frame(self, t: float) -> Image.Image:
                # 100% Void Black Clear
                canvas.clear(bg_clear)

                open_fade = min(1.0, max(0.0, (t - 0.2) / 2.0))
                if open_fade <= 0:
                    snapshot = surface.makeImageSnapshot()
                    return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

                # -----------------------------------------------------------
                # Atmospheric Central Nebula Glow (subtle depth on pure black)
                # -----------------------------------------------------------
                nebula_paint = skia.Paint(
                    Shader=skia.GradientShader.MakeRadial(
                        (960.0 * sx, 540.0 * sy),
                        880.0 * sx,
                        [
                            skia.Color4f(0.04, 0.07, 0.16, 0.40 * open_fade),
                            skia.Color4f(0.06, 0.02, 0.12, 0.20 * open_fade),
                            skia.Color4f(0.0, 0.0, 0.0, 0.0),
                        ],
                        [0.0, 0.60, 1.0],
                    )
                )
                canvas.drawCircle(960.0 * sx, 540.0 * sy, 880.0 * sx, nebula_paint)

                # -----------------------------------------------------------
                # Subtle Architectural Layer Guides (Geometric Lines, No Text)
                # -----------------------------------------------------------
                for l_idx, x_col in enumerate(xs):
                    col_r, col_g, col_b = LAYER_PALETTES[l_idx]
                    guide_p = skia.Paint(
                        Color=skia.Color4f(col_r, col_g, col_b, 0.10 * open_fade),
                        StrokeWidth=1.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    cx = x_col * sx
                    canvas.drawLine(cx, 130.0 * sy, cx, 950.0 * sy, guide_p)
                    # Technical column crosshairs
                    ch_sz = 4.0 * sx
                    canvas.drawLine(cx - ch_sz, 130.0 * sy, cx + ch_sz, 130.0 * sy, guide_p)
                    canvas.drawLine(cx - ch_sz, 950.0 * sy, cx + ch_sz, 950.0 * sy, guide_p)

                # -----------------------------------------------------------
                # Compute Organic Floating Coordinates for all 108 Neurons
                # -----------------------------------------------------------
                live_positions: list[list[tuple[float, float]]] = []
                for l_idx, pts in enumerate(base_positions):
                    layer_live = []
                    for i, (bx, by) in enumerate(pts):
                        phi = phases[l_idx][i]
                        dy = 4.0 * math.sin(1.6 * t + phi)
                        dx = 1.2 * math.cos(1.1 * t + phi * 0.7)
                        layer_live.append((bx + dx, by + dy))
                    live_positions.append(layer_live)

                # -----------------------------------------------------------
                # State Flags for Visual Storytelling Events
                # -----------------------------------------------------------
                is_dial_active = 12.0 <= t <= 21.5
                dial_fade = min(1.0, max(0.0, (t - 12.0) / 0.8)) if t < 20.8 else min(1.0, max(0.0, (21.5 - t) / 0.7))
                dial_boost = min(1.0, max(0.0, (t - 14.0) / 2.0)) if is_dial_active else 0.0

                wave_st = 23.8
                wave_dur = 7.0
                is_wave_active = wave_st <= t <= wave_st + wave_dur
                wave_prog = (t - wave_st) / wave_dur if is_wave_active else 0.0

                loss_st = 33.5
                is_loss_active = t >= loss_st
                loss_fade = min(1.0, max(0.0, (t - loss_st) / 0.8)) if is_loss_active else 0.0

                # -----------------------------------------------------------
                # Render 1,692 Dynamically Swinging Connection Filaments
                # -----------------------------------------------------------
                # Highlighted connection: Layer 0 Node 4 -> Layer 1 Node 6
                hl_l, hl_i, hl_j = 0, 4, 6

                for l_idx, i, j, weight, sway_phase, freq, amp, depth_tier in conns:
                    p1 = live_positions[l_idx][i]
                    p2 = live_positions[l_idx + 1][j]

                    # Multi-harmonic wave equation for delicate swinging motion
                    sway = amp * math.sin(freq * t + sway_phase) * math.cos(0.85 * t + sway_phase * 0.5)

                    x1, y1 = p1[0] * sx, p1[1] * sy
                    x2, y2 = p2[0] * sx, p2[1] * sy
                    dx = x2 - x1
                    sag = (y2 - y1) * 0.035
                    sway_px = sway * sy

                    c1x = x1 + dx * 0.48
                    c1y = y1 + sag + sway_px
                    c2x = x2 - dx * 0.48
                    c2y = y2 - sag - sway_px

                    path = skia.Path()
                    path.moveTo(x1, y1)
                    path.cubicTo(c1x, c1y, c2x, c2y, x2, y2)

                    # Highlighted Dial Synapse
                    if l_idx == hl_l and i == hl_i and j == hl_j:
                        if is_dial_active and dial_fade > 0:
                            # Molten gold flare
                            gold_stroke.setColor(skia.Color4f(0.98, 0.75, 0.14, 0.35 * dial_fade * open_fade))
                            gold_stroke.setStrokeWidth((6.0 + 3.0 * dial_boost) * sx)
                            canvas.drawPath(path, gold_stroke)

                            gold_stroke.setColor(skia.Color4f(0.98, 0.82, 0.22, 0.95 * dial_fade * open_fade))
                            gold_stroke.setStrokeWidth((2.6 + 1.2 * dial_boost) * sx)
                            canvas.drawPath(path, gold_stroke)

                            gold_stroke.setColor(skia.Color4f(1.0, 1.0, 1.0, 0.95 * dial_fade * open_fade))
                            gold_stroke.setStrokeWidth(1.2 * sx)
                            canvas.drawPath(path, gold_stroke)
                            continue

                    # Loss feedback tint: connections feeding into erroneous Output Node 2 turn ruby
                    is_error_feeder = is_loss_active and l_idx == 5 and j == 2
                    if is_error_feeder:
                        alpha = (0.25 + 0.50 * loss_fade * math.sin(4.0 * t + sway_phase) ** 2) * open_fade
                        stroke_paint.setColor(skia.Color4f(1.0, 0.12, 0.28, alpha))
                        stroke_paint.setStrokeWidth(1.8 * sx)
                        canvas.drawPath(path, stroke_paint)
                        continue

                    # Layer-specific color blending between Layer L and Layer L+1
                    c1_rgb = LAYER_PALETTES[l_idx]
                    c2_rgb = LAYER_PALETTES[l_idx + 1]
                    # Blend 60% source layer color, 40% target layer color
                    r_blend = 0.60 * c1_rgb[0] + 0.40 * c2_rgb[0]
                    g_blend = 0.60 * c1_rgb[1] + 0.40 * c2_rgb[1]
                    b_blend = 0.60 * c1_rgb[2] + 0.40 * c2_rgb[2]

                    base_a = 0.05 if depth_tier == 0 else 0.13
                    alpha = (base_a + abs(weight) * 0.14) * open_fade
                    strk_w = (0.55 if depth_tier == 0 else 0.95 + abs(weight) * 0.45) * sx

                    conn_paint.setColor(skia.Color4f(r_blend, g_blend, b_blend, alpha))
                    conn_paint.setStrokeWidth(strk_w)
                    canvas.drawPath(path, conn_paint)

                # -----------------------------------------------------------
                # Ambient Idle Photons Sliding Along Filaments (Baseline Life)
                # -----------------------------------------------------------
                if t < 22.5:
                    pkt_p = skia.Paint(Style=skia.Paint.kFill_Style, AntiAlias=True)
                    for cycle_t in (2.0, 5.0, 8.0, 11.5, 15.0, 18.5):
                        if cycle_t <= t <= cycle_t + 3.0:
                            rel_t = (t - cycle_t) / 3.0
                            step_idx = min(5, int(rel_t * 6))
                            u_prog = (rel_t * 6) - step_idx
                            sample_c = conns[(step_idx * 59 + 17) % len(conns)]
                            l_idx, i, j, _, s_phase, freq, amp, _ = sample_c
                            p1 = live_positions[l_idx][i]
                            p2 = live_positions[l_idx + 1][j]
                            sway = amp * math.sin(freq * t + s_phase) * math.cos(0.85 * t + s_phase * 0.5)
                            pts_line = cubic_pts(p1[0], p1[1], p2[0], p2[1], sway, num_pts=14)
                            k = min(len(pts_line) - 1, max(0, int(u_prog * (len(pts_line) - 1))))
                            px, py = pts_line[k][0] * sx, pts_line[k][1] * sy

                            col_p = LAYER_PALETTES[l_idx]
                            pkt_p.setColor(skia.Color4f(col_p[0], col_p[1], col_p[2], 0.90 * open_fade))
                            canvas.drawCircle(px, py, 2.5 * sx, pkt_p)

                # -----------------------------------------------------------
                # Pure Visual Holographic Synaptic Dial (12.0s - 21.5s, NO TEXT)
                # -----------------------------------------------------------
                if is_dial_active and dial_fade > 0:
                    hl_p1 = live_positions[hl_l][hl_i]
                    hl_p2 = live_positions[hl_l + 1][hl_j]
                    dial_cx = (hl_p1[0] + hl_p2[0]) * 0.5 * sx
                    dial_cy = (hl_p1[1] + hl_p2[1]) * 0.5 * sy - 52.0 * sy

                    # Outer technical reticle brackets
                    b_size = 54.0 * sx
                    reticle_paint = skia.Paint(
                        Color=skia.Color4f(0.98, 0.75, 0.14, 0.45 * dial_fade * open_fade),
                        StrokeWidth=1.2 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    arm = 10.0 * sx
                    for dx_sign in (-1, 1):
                        for dy_sign in (-1, 1):
                            bx = dial_cx + dx_sign * b_size
                            by = dial_cy + dy_sign * b_size
                            p_b = skia.Path()
                            p_b.moveTo(bx - dx_sign * arm, by)
                            p_b.lineTo(bx, by)
                            p_b.lineTo(bx, by - dy_sign * arm)
                            canvas.drawPath(p_b, reticle_paint)

                    # Dial dark glass body
                    glass_p = skia.Paint(
                        Color=skia.Color4f(0.01, 0.03, 0.07, 0.94 * dial_fade * open_fade),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(dial_cx, dial_cy, 44.0 * sx, glass_p)

                    # Dial concentric rings
                    ring_p = skia.Paint(
                        Color=skia.Color4f(0.98, 0.75, 0.14, 0.90 * dial_fade * open_fade),
                        StrokeWidth=1.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(dial_cx, dial_cy, 44.0 * sx, ring_p)
                    ring_p.setColor(skia.Color4f(0.98, 0.75, 0.14, 0.35 * dial_fade * open_fade))
                    ring_p.setStrokeWidth(0.9 * sx)
                    canvas.drawCircle(dial_cx, dial_cy, 36.0 * sx, ring_p)

                    # 36 precision radial ticks
                    tick_p = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
                    for deg in range(0, 360, 10):
                        rad = math.radians(deg)
                        is_card = deg % 90 == 0
                        is_sub = deg % 30 == 0
                        r_inner = 37.0 * sx if is_card else (39.0 * sx if is_sub else 40.5 * sx)
                        r_outer = 43.0 * sx
                        tx1 = dial_cx + r_inner * math.cos(rad)
                        ty1 = dial_cy + r_inner * math.sin(rad)
                        tx2 = dial_cx + r_outer * math.cos(rad)
                        ty2 = dial_cy + r_outer * math.sin(rad)
                        tick_p.setColor(
                            skia.Color4f(
                                0.98, 0.80, 0.20, (0.95 if is_card else (0.65 if is_sub else 0.35)) * dial_fade * open_fade
                            )
                        )
                        tick_p.setStrokeWidth((1.4 if is_card else 0.8) * sx)
                        canvas.drawLine(tx1, ty1, tx2, ty2, tick_p)

                    # Animated Arc Gauge (sweeps with dial_boost)
                    needle_ang = -30.0 + 90.0 * dial_boost
                    arc_p = skia.Paint(
                        Color=skia.Color4f(0.98, 0.85, 0.24, 0.95 * dial_fade * open_fade),
                        StrokeWidth=2.6 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    arc_rect = skia.Rect.MakeXYWH(dial_cx - 31.0 * sx, dial_cy - 31.0 * sx, 62.0 * sx, 62.0 * sx)
                    start_angle = -140.0
                    sweep_angle = needle_ang - start_angle
                    canvas.drawArc(arc_rect, start_angle, sweep_angle, False, arc_p)

                    # Rotating Needle Indicator
                    n_rad = math.radians(needle_ang)
                    n_len = 35.0 * sx
                    nx_tip = dial_cx + n_len * math.cos(n_rad)
                    ny_tip = dial_cy + n_len * math.sin(n_rad)
                    needle_p = skia.Paint(
                        Color=skia.Color4f(1.0, 1.0, 1.0, 0.98 * dial_fade * open_fade),
                        StrokeWidth=2.2 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(dial_cx, dial_cy, nx_tip, ny_tip, needle_p)

                    # Center Pin Jewel
                    pin_p = skia.Paint(
                        Color=skia.Color4f(0.98, 0.75, 0.14, 1.0 * dial_fade * open_fade),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(dial_cx, dial_cy, 4.5 * sx, pin_p)
                    pin_p.setColor(skia.Color4f(1.0, 1.0, 1.0, 1.0 * dial_fade * open_fade))
                    canvas.drawCircle(dial_cx, dial_cy, 1.8 * sx, pin_p)

                    # Leader line from dial to synapse
                    canvas.drawLine(
                        dial_cx,
                        dial_cy + 44.0 * sx,
                        dial_cx,
                        (hl_p1[1] + hl_p2[1]) * 0.5 * sy,
                        reticle_paint,
                    )

                # -----------------------------------------------------------
                # Pure Visual Input Hologram Matrix (21.5s - 40.7s, NO TEXT)
                # -----------------------------------------------------------
                card_st = 21.5
                if t >= card_st:
                    card_fade = min(1.0, max(0.0, (t - card_st) / 0.8))
                    card_cx = 140.0 * sx
                    card_cy = 540.0 * sy
                    card_w = 145.0 * sx
                    card_h = 205.0 * sy

                    # Hologram body
                    hologram_bg = skia.Paint(
                        Color=skia.Color4f(0.01, 0.03, 0.07, 0.92 * card_fade * open_fade),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    rrect = skia.RRect.MakeRectXY(
                        skia.Rect.MakeXYWH(card_cx - card_w * 0.5, card_cy - card_h * 0.5, card_w, card_h),
                        12.0 * sx,
                        12.0 * sy,
                    )
                    canvas.drawRRect(rrect, hologram_bg)

                    # Hologram border
                    holo_stroke = skia.Paint(
                        Color=skia.Color4f(0.0, 0.94, 1.0, 0.75 * card_fade * open_fade),
                        StrokeWidth=1.4 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawRRect(rrect, holo_stroke)

                    # 28x28 digital pixel grid
                    grid_sz = 96.0 * sx
                    grid_rect = skia.Rect.MakeXYWH(
                        card_cx - grid_sz * 0.5, card_cy - grid_sz * 0.5 - 12.0 * sy, grid_sz, grid_sz
                    )
                    grid_bg = skia.Paint(
                        Color=skia.Color4f(0.0, 0.02, 0.05, 0.95 * card_fade * open_fade),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    canvas.drawRect(grid_rect, grid_bg)

                    grid_border = skia.Paint(
                        Color=skia.Color4f(0.22, 0.74, 0.97, 0.30 * card_fade * open_fade),
                        StrokeWidth=0.9 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawRect(grid_rect, grid_border)

                    # Background matrix pixel dots
                    dot_p = skia.Paint(
                        Color=skia.Color4f(0.0, 0.94, 1.0, 0.12 * card_fade * open_fade),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    for r_i in range(7):
                        for c_i in range(7):
                            dx_p = grid_rect.left() + (c_i + 0.5) * (grid_sz / 7.0)
                            dy_p = grid_rect.top() + (r_i + 0.5) * (grid_sz / 7.0)
                            canvas.drawCircle(dx_p, dy_p, 1.0 * sx, dot_p)

                    # Sweeping laser scanline
                    scan_y = grid_rect.top() + ((t * 1.8) % 1.0) * grid_sz
                    scan_p = skia.Paint(
                        Color=skia.Color4f(0.0, 0.94, 1.0, 0.50 * card_fade * open_fade),
                        StrokeWidth=1.4 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(grid_rect.left(), scan_y, grid_rect.right(), scan_y, scan_p)

                    # Vector Phosphor Digit '7'
                    d7_paint = skia.Paint(
                        Color=skia.Color4f(0.0, 0.94, 1.0, 0.98 * card_fade * open_fade),
                        StrokeWidth=4.2 * sx,
                        StrokeCap=skia.Paint.kRound_Cap,
                        StrokeJoin=skia.Paint.kRound_Join,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    d7_glow = skia.Paint(
                        Color=skia.Color4f(0.0, 0.94, 1.0, 0.35 * card_fade * open_fade),
                        StrokeWidth=9.0 * sx,
                        StrokeCap=skia.Paint.kRound_Cap,
                        StrokeJoin=skia.Paint.kRound_Join,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )

                    d7_path = skia.Path()
                    d7_path.moveTo(card_cx - 28.0 * sx, card_cy - 40.0 * sy)
                    d7_path.lineTo(card_cx + 28.0 * sx, card_cy - 40.0 * sy)
                    d7_path.lineTo(card_cx - 12.0 * sx, card_cy + 22.0 * sy)

                    cross_path = skia.Path()
                    cross_path.moveTo(card_cx - 5.0 * sx, card_cy - 10.0 * sy)
                    cross_path.lineTo(card_cx + 15.0 * sx, card_cy - 10.0 * sy)

                    canvas.drawPath(d7_path, d7_glow)
                    canvas.drawPath(d7_path, d7_paint)
                    canvas.drawPath(cross_path, d7_glow)
                    canvas.drawPath(cross_path, d7_paint)

                    # Holographic status indicator bars
                    for bar_k in range(4):
                        bx = card_cx - 36.0 * sx + bar_k * 20.0 * sx
                        by = card_cy + 60.0 * sy
                        bw = 14.0 * sx
                        bh = 4.0 * sy
                        bar_active = bar_k < 3
                        bar_p = skia.Paint(
                            Color=skia.Color4f(
                                0.0, 0.94, 1.0, (0.85 if bar_active else 0.20) * card_fade * open_fade
                            ),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        )
                        canvas.drawRect(skia.Rect.MakeXYWH(bx, by, bw, bh), bar_p)

                    # Optical Laser Conduits to all 10 Input Layer 0 Nodes
                    conduit_p = skia.Paint(
                        Color=skia.Color4f(0.0, 0.94, 1.0, 0.30 * card_fade * open_fade),
                        StrokeWidth=1.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    pulse_p = skia.Paint(
                        Color=skia.Color4f(1.0, 1.0, 1.0, 0.95 * card_fade * open_fade),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    conduit_orig_x = card_cx + card_w * 0.5
                    conduit_orig_y = card_cy

                    for idx_node, (in_x, in_y) in enumerate(live_positions[0]):
                        target_x = in_x * sx
                        target_y = in_y * sy
                        mid_x = (conduit_orig_x + target_x) * 0.5

                        c_path = skia.Path()
                        c_path.moveTo(conduit_orig_x, conduit_orig_y)
                        c_path.cubicTo(mid_x, conduit_orig_y, mid_x - 20.0 * sx, target_y, target_x, target_y)
                        canvas.drawPath(c_path, conduit_p)

                        pulse_u = ((t * 1.5 + idx_node * 0.1) % 1.0)
                        px = (1.0 - pulse_u) ** 2 * conduit_orig_x + 2 * (1.0 - pulse_u) * pulse_u * mid_x + pulse_u**2 * target_x
                        py = (1.0 - pulse_u) ** 2 * conduit_orig_y + 2 * (1.0 - pulse_u) * pulse_u * target_y + pulse_u**2 * target_y
                        canvas.drawCircle(px, py, 2.4 * sx, pulse_p)

                # -----------------------------------------------------------
                # High-Velocity 6-Stage Forward Propagation Wave (23.8s - 31.0s)
                # -----------------------------------------------------------
                if is_wave_active:
                    curr_stage = min(5, int(wave_prog * 6))
                    stage_u = (wave_prog * 6) - curr_stage

                    stage_conns = [c for c in conns if c[0] == curr_stage]
                    wave_pkt_paint = skia.Paint(Style=skia.Paint.kFill_Style, AntiAlias=True)

                    for k in range(0, len(stage_conns), max(1, len(stage_conns) // 20)):
                        _, i, j, _, sway_phase, freq, amp, _ = stage_conns[k]
                        p1 = live_positions[curr_stage][i]
                        p2 = live_positions[curr_stage + 1][j]
                        sway = amp * math.sin(freq * t + sway_phase) * math.cos(0.85 * t + sway_phase * 0.5)
                        pts_line = cubic_pts(p1[0], p1[1], p2[0], p2[1], sway, num_pts=14)
                        idx_pt = min(len(pts_line) - 1, max(0, int(stage_u * (len(pts_line) - 1))))
                        px, py = pts_line[idx_pt][0] * sx, pts_line[idx_pt][1] * sy

                        col_hit = LAYER_PALETTES[curr_stage + 1]
                        wave_pkt_paint.setColor(skia.Color4f(1.0, 1.0, 1.0, 0.95))
                        canvas.drawCircle(px, py, 3.2 * sx, wave_pkt_paint)
                        wave_pkt_paint.setColor(skia.Color4f(col_hit[0], col_hit[1], col_hit[2], 0.50))
                        canvas.drawCircle(px, py, 7.5 * sx, wave_pkt_paint)

                # -----------------------------------------------------------
                # Output Probability Distribution HUD (31.0s - 40.7s, NO TEXT)
                # -----------------------------------------------------------
                out_st = 31.0
                if t >= out_st:
                    out_fade = min(1.0, max(0.0, (t - out_st) / 0.8))
                    track_p = skia.Paint(
                        Color=skia.Color4f(0.06, 0.10, 0.18, 0.85 * out_fade * open_fade),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    bar_fill = skia.Paint(Style=skia.Paint.kFill_Style, AntiAlias=True)

                    # 8 output indicator bars aligned directly with the 8 output nodes (Layer 6)
                    for out_idx, (on_x, on_y) in enumerate(live_positions[6]):
                        bar_y = on_y * sy
                        bar_x = (on_x + 22.0) * sx
                        track_w = 140.0 * sx
                        bar_h = 7.0 * sy

                        canvas.drawRRect(
                            skia.RRect.MakeRectXY(
                                skia.Rect.MakeXYWH(bar_x, bar_y - bar_h * 0.5, track_w, bar_h),
                                3.5 * sx,
                                3.5 * sy,
                            ),
                            track_p,
                        )

                        if out_idx == 2:
                            # Erroneous high prediction
                            active_len = (120.0 + 6.0 * math.sin(3.5 * t)) * sx
                            color = (
                                skia.Color4f(1.0, 0.12, 0.28, 0.95 * out_fade * open_fade)
                                if is_loss_active
                                else skia.Color4f(0.98, 0.75, 0.14, 0.95 * out_fade * open_fade)
                            )
                        elif out_idx == 5:
                            # True target
                            active_len = 22.0 * sx
                            color = skia.Color4f(0.00, 0.96, 0.63, 0.75 * out_fade * open_fade)
                        else:
                            active_len = (8.0 + (out_idx * 2.5)) * sx
                            color = skia.Color4f(0.20, 0.45, 0.75, 0.40 * out_fade * open_fade)

                        bar_fill.setColor(color)
                        canvas.drawRRect(
                            skia.RRect.MakeRectXY(
                                skia.Rect.MakeXYWH(bar_x, bar_y - bar_h * 0.5, active_len, bar_h),
                                3.5 * sx,
                                3.5 * sy,
                            ),
                            bar_fill,
                        )

                # -----------------------------------------------------------
                # Crimson Loss Shockwave & Error Detonation (33.5s - 40.7s)
                # -----------------------------------------------------------
                if is_loss_active and loss_fade > 0:
                    err_node = live_positions[6][2]
                    err_cx = err_node[0] * sx
                    err_cy = err_node[1] * sy

                    shock_paint = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
                    for r_pulse in (0.0, 1.8, 3.6, 5.4):
                        pulse_age = t - loss_st - r_pulse
                        if 0.0 <= pulse_age <= 2.2:
                            prog_ring = pulse_age / 2.2
                            ring_rad = (18.0 + prog_ring * 200.0) * sx
                            ring_alpha = (1.0 - prog_ring) * 0.85 * loss_fade * open_fade
                            shock_paint.setColor(skia.Color4f(1.0, 0.12, 0.28, ring_alpha))
                            shock_paint.setStrokeWidth((2.8 * (1.0 - prog_ring) + 0.8) * sx)
                            canvas.drawCircle(err_cx, err_cy, ring_rad, shock_paint)

                    # Crimson Caliper Brackets around Error Node
                    caliper_p = skia.Paint(
                        Color=skia.Color4f(1.0, 0.15, 0.30, 0.95 * loss_fade * open_fade),
                        StrokeWidth=1.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    c_gap = (22.0 + 2.5 * math.sin(5.0 * t)) * sx
                    c_len = 12.0 * sx
                    # Left bracket
                    canvas.drawLine(err_cx - c_gap, err_cy - c_len, err_cx - c_gap, err_cy + c_len, caliper_p)
                    canvas.drawLine(err_cx - c_gap, err_cy, err_cx - c_gap + 6.0 * sx, err_cy, caliper_p)
                    # Right bracket
                    canvas.drawLine(err_cx + c_gap, err_cy - c_len, err_cx + c_gap, err_cy + c_len, caliper_p)
                    canvas.drawLine(err_cx + c_gap, err_cy, err_cx + c_gap - 6.0 * sx, err_cy, caliper_p)

                # -----------------------------------------------------------
                # Render All 108 Refined, Microscopic, Razor-Sharp Neurons
                # -----------------------------------------------------------
                halo_p = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
                disc_p = skia.Paint(Style=skia.Paint.kFill_Style, AntiAlias=True)
                border_p = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
                core_p = skia.Paint(Style=skia.Paint.kFill_Style, AntiAlias=True)
                bead_p = skia.Paint(
                    Color=skia.Color4f(1.0, 1.0, 1.0, 0.98 * open_fade),
                    Style=skia.Paint.kFill_Style,
                    AntiAlias=True,
                )

                for l_idx, pts in enumerate(live_positions):
                    col_r, col_g, col_b = LAYER_PALETTES[l_idx]

                    is_layer_active = False
                    if is_wave_active:
                        stage_hit = int(wave_prog * 6)
                        if stage_hit == l_idx or (stage_hit + 1 == l_idx and (wave_prog * 6 - stage_hit) > 0.6):
                            is_layer_active = True

                    for i, (nx, ny) in enumerate(pts):
                        px, py = nx * sx, ny * sy
                        phi = phases[l_idx][i]

                        breathe = math.sin(2.0 * t + phi)
                        is_dial_node = is_dial_active and (
                            (l_idx == hl_l and i == hl_i) or (l_idx == hl_l + 1 and i == hl_j)
                        )
                        is_error_node = is_loss_active and l_idx == 6 and i == 2

                        # 1. Subtle, Tight Ambient Corona (Refined radius so it never blobs or overlaps!)
                        corona_rad = (
                            10.0
                            + 1.5 * breathe
                            + (5.0 if is_layer_active else 0.0)
                            + (8.0 if is_error_node else 0.0)
                        ) * sx

                        if is_error_node:
                            corona_color = skia.Color4f(1.0, 0.12, 0.28, 0.45 * loss_fade * open_fade)
                        elif is_dial_node:
                            corona_color = skia.Color4f(0.98, 0.75, 0.14, 0.45 * dial_fade * open_fade)
                        else:
                            corona_color = skia.Color4f(
                                col_r, col_g, col_b, (0.16 + (0.35 if is_layer_active else 0.0)) * open_fade
                            )

                        disc_p.setColor(corona_color)
                        canvas.drawCircle(px, py, corona_rad, disc_p)

                        # 2. Precision Outer Orbital Reticle Ring (Crisp & Compact)
                        orbit_rad = (6.8 + 0.6 * breathe + (1.5 if is_layer_active else 0.0)) * sx
                        if is_error_node:
                            halo_color = skia.Color4f(1.0, 0.20, 0.35, 0.98 * loss_fade * open_fade)
                        elif is_dial_node:
                            halo_color = skia.Color4f(0.98, 0.85, 0.25, 0.98 * dial_fade * open_fade)
                        else:
                            halo_color = skia.Color4f(
                                col_r, col_g, col_b, (0.50 + (0.45 if is_layer_active else 0.0)) * open_fade
                            )

                        halo_p.setColor(halo_color)
                        halo_p.setStrokeWidth(0.9 * sx)
                        canvas.drawCircle(px, py, orbit_rad, halo_p)

                        # 3. Aperture Disc (Obsidian glass core)
                        disc_rad = 4.8 * sx
                        disc_p.setColor(skia.Color4f(0.01, 0.02, 0.05, 0.98 * open_fade))
                        canvas.drawCircle(px, py, disc_rad, disc_p)

                        border_p.setColor(skia.Color4f(col_r * 0.4, col_g * 0.4, col_b * 0.4, 0.80 * open_fade))
                        border_p.setStrokeWidth(0.8 * sx)
                        canvas.drawCircle(px, py, disc_rad, border_p)

                        # 4. Bioluminescent Nucleus Core (Razor-sharp compact dot)
                        core_rad = (
                            2.4
                            + 0.5 * breathe
                            + (1.2 if is_layer_active else 0.0)
                            + (1.5 if is_error_node else 0.0)
                            + (1.0 if is_dial_node else 0.0)
                        ) * sx

                        if is_error_node:
                            core_color = skia.Color4f(1.0, 0.12, 0.28, 0.98 * loss_fade * open_fade)
                        elif is_dial_node:
                            core_color = skia.Color4f(0.98, 0.85, 0.24, 0.98 * dial_fade * open_fade)
                        else:
                            core_color = skia.Color4f(
                                col_r, col_g, col_b, (0.85 + (0.15 if is_layer_active else 0.0)) * open_fade
                            )

                        core_p.setColor(core_color)
                        canvas.drawCircle(px, py, core_rad, core_p)

                        # 5. Photonic Center Spark (Crystalline white-hot point)
                        canvas.drawCircle(px, py, 1.0 * sx, bead_p)

                snapshot = surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_01(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build Scene 01: 7-Layer Prism Architecture, Compact Sharp Neurons, Void Black."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            scene.add_audio(str(p), start=0.0, trim_start=0.0, trim_end=SCENE_01_DURATION)

    viewport = Viewport(FluidNeuralNetworkSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_01_DURATION)
    return scene
