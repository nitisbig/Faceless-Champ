"""Scene 01: Inside the AI Brain (Numbers Recognition Neural Network Training).

Visual narrative:
- 0.0s - 2.0s: Pure pitch black void (#000000) fades into an expansive 7-layer neural architecture.
- 2.0s - 10.8s: "Right now, somewhere in the world, a neural network is learning..."
    Input side: Classic digital block-style digit recognition card displaying training digits.
    Optical laser conduits feed signals into 10 Input Layer nodes.
    Output side: 10 Output nodes corresponding to digits 0-9, with classic block-style digit indicators
    and live segmented probability meters mimicking real-time prediction fluctuations during training.
    108 compact, razor-sharp jewel neurons anchored in fixed geometric columns (NO shaking).
    Over 1,500 connection filaments undulating with fluid, harmonic traveling wave motion.
- 10.8s - 18.4s: "But how does it know which way to turn one dial, buried deep inside..."
    The surrounding network dims smoothly into a dark indigo depth-of-field silhouette.
    A single interior golden synapse is isolated and flares with molten solar radiance.
    A precision holographic circular dial HUD badge emerges with 36 radial calibration ticks
    and a sharp white-hot needle that turns clockwise (+dw) then counter-clockwise (-dw).
- 18.4s - 21.8s: "The answer is one idea from calculus..."
    Input digit locks onto '7'. The network makes an incorrect prediction on digit '2'.
    A high-speed radiant photon wave surges forward through the layers from the focal dial to the output.
    Output node 2 detonates into an intense ruby crimson Loss beacon with expanding multi-frequency shockwaves.
    A delicate dashed golden tracer ray arcs gracefully from the dial across to the error beacon.
- 21.8s - 25.99s: "...an idea you may have memorized, without ever feeling why it works. The chain rule."
    The network dissolves gracefully into deep black void.
    Center stage reveals the grand cinematic title: "The Chain Rule" in Cormorant Garamond serif with warm
    golden optical glow, hairline divider, and tracked architectural DM Sans subtitle:
    "THE MATHEMATICAL ENGINE OF ARTIFICIAL INTELLIGENCE".
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

SCENE_01_DURATION = 25.99

# 7 Distinct, Vivid High-Contrast Layer Palette Colors (RGB floats 0.0 - 1.0)
LAYER_PALETTES = (
    (0.00, 0.95, 1.00),  # L0: Electric Cyan (Input - 10 nodes)
    (0.00, 1.00, 0.55),  # L1: Neon Emerald (14 nodes)
    (1.00, 0.80, 0.10),  # L2: Cyber Solar Gold (18 nodes)
    (0.72, 0.28, 1.00),  # L3: Deep Ultraviolet Core (24 nodes)
    (1.00, 0.18, 0.65),  # L4: Hot Neon Fuchsia (18 nodes)
    (0.12, 0.62, 1.00),  # L5: Electric Cobalt (14 nodes)
    (0.98, 1.00, 1.00),  # L6: Crystalline Ice White (Output - 10 digits 0-9)
)


def get_handwritten_sample(digit: int, cx: float, cy: float, scale: float):
    """Generate authentic handwritten training data strokes and 10 topological receptor probe points."""
    paths = []
    if digit == 3:
        p = skia.Path()
        p.moveTo(cx - 38 * scale, cy - 66 * scale)
        p.cubicTo(cx - 10 * scale, cy - 88 * scale, cx + 42 * scale, cy - 78 * scale, cx + 46 * scale, cy - 40 * scale)
        p.cubicTo(cx + 48 * scale, cy - 14 * scale, cx + 18 * scale, cy - 2 * scale, cx - 4 * scale, cy - 2 * scale)
        p.cubicTo(cx + 25 * scale, cy - 2 * scale, cx + 52 * scale, cy + 18 * scale, cx + 48 * scale, cy + 52 * scale)
        p.cubicTo(cx + 44 * scale, cy + 82 * scale, cx - 2 * scale, cy + 92 * scale, cx - 42 * scale, cy + 74 * scale)
        paths.append(p)
        pts = [
            (cx - 38 * scale, cy - 66 * scale),  # 0: top start
            (cx + 12 * scale, cy - 82 * scale),  # 1: top crest
            (cx + 46 * scale, cy - 40 * scale),  # 2: top right
            (cx + 28 * scale, cy - 18 * scale),  # 3: upper inward
            (cx - 4 * scale, cy - 2 * scale),    # 4: waist cusp
            (cx + 32 * scale, cy + 12 * scale),  # 5: lower outward
            (cx + 48 * scale, cy + 52 * scale),  # 6: lower right
            (cx + 30 * scale, cy + 80 * scale),  # 7: lower bottom
            (cx - 2 * scale, cy + 92 * scale),   # 8: bottom crest
            (cx - 42 * scale, cy + 74 * scale),  # 9: bottom end
        ]
        weights = [0.95, 0.90, 0.95, 0.35, 1.0, 0.30, 0.92, 0.88, 0.90, 0.85]
    elif digit == 5:
        p1 = skia.Path()
        p1.moveTo(cx - 28 * scale, cy - 68 * scale)
        p1.lineTo(cx - 34 * scale, cy - 12 * scale)
        p1.cubicTo(cx - 10 * scale, cy - 26 * scale, cx + 38 * scale, cy - 16 * scale, cx + 44 * scale, cy + 20 * scale)
        p1.cubicTo(cx + 50 * scale, cy + 58 * scale, cx + 15 * scale, cy + 86 * scale, cx - 38 * scale, cy + 76 * scale)
        paths.append(p1)
        p2 = skia.Path()
        p2.moveTo(cx - 32 * scale, cy - 68 * scale)
        p2.cubicTo(cx, cy - 72 * scale, cx + 25 * scale, cy - 70 * scale, cx + 42 * scale, cy - 66 * scale)
        paths.append(p2)
        pts = [
            (cx - 32 * scale, cy - 68 * scale),  # 0: top bar start
            (cx + 15 * scale, cy - 71 * scale),  # 1: top bar mid
            (cx + 42 * scale, cy - 66 * scale),  # 2: top bar end
            (cx - 30 * scale, cy - 40 * scale),  # 3: neck mid
            (cx - 34 * scale, cy - 12 * scale),  # 4: neck bottom
            (cx + 18 * scale, cy - 10 * scale),  # 5: belly top
            (cx + 44 * scale, cy + 20 * scale),  # 6: belly right
            (cx + 38 * scale, cy + 68 * scale),  # 7: belly lower
            (cx + 10 * scale, cy + 86 * scale),  # 8: bottom crest
            (cx - 38 * scale, cy + 76 * scale),  # 9: tail end
        ]
        weights = [0.92, 0.95, 0.88, 0.90, 0.96, 0.35, 0.92, 0.85, 0.90, 0.82]
    else:  # 7
        p1 = skia.Path()
        p1.moveTo(cx - 44 * scale, cy - 68 * scale)
        p1.lineTo(cx + 42 * scale, cy - 68 * scale)
        p1.cubicTo(cx + 32 * scale, cy - 18 * scale, cx + 8 * scale, cy + 28 * scale, cx - 20 * scale, cy + 82 * scale)
        paths.append(p1)
        p2 = skia.Path()
        p2.moveTo(cx - 14 * scale, cy + 8 * scale)
        p2.lineTo(cx + 24 * scale, cy + 6 * scale)
        paths.append(p2)
        pts = [
            (cx - 44 * scale, cy - 68 * scale),  # 0: top start
            (cx, cy - 68 * scale),               # 1: top mid
            (cx + 42 * scale, cy - 68 * scale),  # 2: top right
            (cx + 32 * scale, cy - 38 * scale),  # 3: diag upper
            (cx + 20 * scale, cy - 10 * scale),  # 4: diag pre-cross
            (cx + 5 * scale, cy + 7 * scale),    # 5: cross center
            (cx - 4 * scale, cy + 30 * scale),   # 6: diag post-cross
            (cx - 12 * scale, cy + 56 * scale),  # 7: diag lower
            (cx - 20 * scale, cy + 82 * scale),  # 8: diag end
            (cx + 24 * scale, cy + 6 * scale),   # 9: cross right
        ]
        weights = [0.88, 0.96, 0.94, 0.85, 0.25, 0.98, 0.82, 0.78, 0.90, 0.30]
    return paths, pts, weights


def get_network_layer_activations(digit: int, layer_counts: tuple[int, ...]) -> list[list[float]]:
    """Compute forward layer-by-layer activations across all 7 layers for a given digit."""
    activations: list[list[float]] = []
    rng_d = random.Random(digit * 777 + 99)
    if digit == 3:
        l0 = [0.95, 0.90, 0.95, 0.20, 1.00, 0.20, 0.92, 0.88, 0.90, 0.85]
    elif digit == 5:
        l0 = [0.92, 0.95, 0.88, 0.90, 0.96, 0.20, 0.92, 0.85, 0.90, 0.82]
    else:  # 7
        l0 = [0.88, 0.96, 0.94, 0.85, 0.15, 0.98, 0.82, 0.78, 0.90, 0.20]
    activations.append(l0)

    prev = l0
    for l_idx in range(1, 6):
        count = layer_counts[l_idx]
        curr = []
        for j in range(count):
            val = sum(prev[i] * max(0.0, rng_d.uniform(-0.35, 1.25)) for i in range(len(prev)))
            norm_val = 1.0 / (1.0 + math.exp(-val * 0.45 + 1.2))
            curr.append(norm_val)
        m = max(curr) or 1.0
        curr = [min(1.0, (c / m) ** 1.6) for c in curr]
        activations.append(curr)
        prev = curr

    # Layer 6 (Output 0-9 predictions)
    l6 = [0.08] * 10
    if digit == 3:
        l6[3] = 0.95
        l6[8] = 0.35
    elif digit == 5:
        l6[5] = 0.92
        l6[6] = 0.38
    else:  # 7: Erroneous prediction on node 2!
        l6[2] = 0.95
        l6[7] = 0.28
    activations.append(l6)
    return activations



# Classic 5x7 Block Digit Pixel Bitmaps
DIGIT_5X7 = {
    0: (
        "01110",
        "10001",
        "10011",
        "10101",
        "11001",
        "10001",
        "01110",
    ),
    1: (
        "00100",
        "01100",
        "00100",
        "00100",
        "00100",
        "00100",
        "01110",
    ),
    2: (
        "01110",
        "10001",
        "00001",
        "00110",
        "01000",
        "10000",
        "11111",
    ),
    3: (
        "11110",
        "00001",
        "00001",
        "01110",
        "00001",
        "00001",
        "11110",
    ),
    4: (
        "00010",
        "00110",
        "01010",
        "10010",
        "11111",
        "00010",
        "00010",
    ),
    5: (
        "11111",
        "10000",
        "11110",
        "00001",
        "00001",
        "10001",
        "01110",
    ),
    6: (
        "00110",
        "01000",
        "10000",
        "11110",
        "10001",
        "10001",
        "01110",
    ),
    7: (
        "11111",
        "00001",
        "00010",
        "00100",
        "01000",
        "01000",
        "01000",
    ),
    8: (
        "01110",
        "10001",
        "10001",
        "01110",
        "10001",
        "10001",
        "01110",
    ),
    9: (
        "01110",
        "10001",
        "10001",
        "01111",
        "00001",
        "00010",
        "01100",
    ),
}


def draw_block_digit(
    canvas: skia.Canvas,
    digit: int,
    x: float,
    y: float,
    cell_w: float,
    cell_h: float,
    gap: float,
    paint_lit: skia.Paint,
    paint_dim: skia.Paint | None = None,
):
    """Draw a classic block style 5x7 digit at (x, y)."""
    pattern = DIGIT_5X7.get(digit, DIGIT_5X7[0])
    for r, row in enumerate(pattern):
        for c, char in enumerate(row):
            bx = x + c * (cell_w + gap)
            by = y + r * (cell_h + gap)
            rect = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(bx, by, cell_w, cell_h), 1.0, 1.0)
            if char == "1":
                canvas.drawRRect(rect, paint_lit)
            elif paint_dim is not None:
                canvas.drawRRect(rect, paint_dim)


def cubic_pts(x1: float, y1: float, x2: float, y2: float, sway1: float, sway2: float, num_pts: int = 14) -> list[tuple[float, float]]:
    """Compute sampled points along a dynamic fluid cubic Bézier curve."""
    dx = x2 - x1
    sag = (y2 - y1) * 0.035
    c1x = x1 + dx * 0.48
    c1y = y1 + sag + sway1
    c2x = x2 - dx * 0.48
    c2y = y2 - sag - sway2
    pts = []
    for step in range(num_pts):
        u = step / (num_pts - 1)
        v = 1.0 - u
        x = v**3 * x1 + 3 * v**2 * u * c1x + 3 * v * u**2 * c2x + u**3 * x2
        y = v**3 * y1 + 3 * v**2 * u * c1y + 3 * v * u**2 * c2y + u**3 * y2
        pts.append((x, y))
    return pts


@dataclass(frozen=True)
class NeuralNetworkIntroSource:
    """Procedural raster source rendering the numbers recognition network, block digits, and title."""

    intrinsic_size: tuple[int, int] = (1920, 1080)
    duration: float = SCENE_01_DURATION
    fingerprint: str = "chain:scene-01:numbers-recognition:v1"
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

        # Load packaged fonts with bold variation coordinates for premium weight
        assets_dir = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "fonts"
        cg_font_path = assets_dir / "CormorantGaramond[wght].ttf"
        sg_font_path = assets_dir / "SpaceGrotesk[wght].ttf"
        dm_font_path = assets_dir / "DMSans[opsz,wght].ttf"

        def _make_weighted_tf(path: Path, weight: float = 700.0, fallback: str = "sans-serif") -> skia.Typeface:
            if not path.exists():
                return skia.Typeface(fallback)
            base = skia.Typeface.MakeFromFile(str(path))
            if base is None:
                return skia.Typeface(fallback)
            try:
                tag_wght = int.from_bytes(b'wght', 'big')
                coords = skia.FontArguments.VariationPosition.Coordinates()
                coords.append(skia.FontArguments.VariationPosition.Coordinate(tag_wght, float(weight)))
                pos = skia.FontArguments.VariationPosition(coords)
                args = skia.FontArguments()
                args.setVariationDesignPosition(pos)
                clone = base.makeClone(args)
                return clone if clone is not None else base
            except Exception:
                return base

        tf_serif_bold = _make_weighted_tf(cg_font_path, 700.0, "serif")
        tf_sans_bold = _make_weighted_tf(sg_font_path, 700.0, "sans-serif")
        tf_sans = _make_weighted_tf(dm_font_path, 500.0, "sans-serif")

        # 1. Architecture: 7 distinct layers
        # Input Layer: 10 nodes (x=360), Output Layer: 10 nodes (x=1560) for digits 0-9
        layer_counts = (10, 14, 18, 24, 18, 14, 10)
        xs = (360.0, 560.0, 760.0, 960.0, 1160.0, 1360.0, 1560.0)
        center_y = 540.0
        spacings = (54.0, 42.0, 36.0, 28.0, 36.0, 42.0, 54.0)

        # Base static positions: NEVER SHAKE THE NEURONS
        static_positions: list[list[tuple[float, float]]] = []
        phases: list[list[float]] = []
        rng = random.Random(42)

        for count, x, spacing in zip(layer_counts, xs, spacings):
            pts = []
            layer_phases = []
            for i in range(count):
                y = center_y + (i - (count - 1) / 2) * spacing
                pts.append((x, y))
                layer_phases.append(rng.uniform(0, math.tau))
            static_positions.append(pts)
            phases.append(layer_phases)

        # 2. Precompute connections with individual fluid traveling wave parameters
        conns: list[tuple[int, int, int, float, float, float, float, int]] = []
        for l_idx, (left, right) in enumerate(pairwise(static_positions)):
            for i in range(len(left)):
                for j in range(len(right)):
                    weight = rng.uniform(-1.0, 1.0)
                    sway_phase = rng.uniform(0, math.tau)
                    freq = rng.uniform(1.2, 2.0)
                    amp = rng.uniform(5.0, 12.0)
                    depth_tier = 1 if abs(weight) > 0.45 else 0
                    conns.append((l_idx, i, j, weight, sway_phase, freq, amp, depth_tier))

        # Precompute forward layer-by-layer activations for digits 3, 5, 7
        digit_layer_acts = {d: get_network_layer_activations(d, layer_counts) for d in (3, 5, 7)}


        # Reusable paints
        bg_clear = skia.Color4f(0.0, 0.0, 0.0, 1.0)
        conn_paint = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
        gold_stroke = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
        stroke_paint = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)

        def _draw_letterspaced(target_canvas, text, cx, y, font, paint, letter_spacing=4.0):
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

        class Session:
            def frame(self, t: float) -> Image.Image:
                # 100% Pure Pitch Black Clear
                canvas.clear(bg_clear)

                open_fade = min(1.0, max(0.0, (t - 0.2) / 1.8))
                if open_fade <= 0:
                    snapshot = surface.makeImageSnapshot()
                    return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

                # Outro fade for the network when title emerges (t >= 21.8s)
                net_fade = 1.0
                if t >= 21.8:
                    net_fade = max(0.0, 1.0 - (t - 21.8) / 1.4)

                composite_net_alpha = open_fade * net_fade

                # Pure pitch black background (no soft background nebula circle)
                # -----------------------------------------------------------
                # State Flags for Visual Storytelling Events
                # -----------------------------------------------------------
                # Focal Dial Active: 10.8s to 18.4s
                is_dial_active = 10.8 <= t <= 18.4
                dial_fade = min(1.0, max(0.0, (t - 10.8) / 0.8)) if t < 17.6 else min(1.0, max(0.0, (18.4 - t) / 0.8))

                # Dial Needle Motion: Clockwise +dw, then Counter-Clockwise -dw
                dial_rot = 0.0
                if 12.0 <= t < 14.5:
                    dial_rot = min(1.0, (t - 12.0) / 1.8)
                elif 14.5 <= t <= 18.0:
                    turn_back = min(1.0, (t - 14.5) / 1.5)
                    dial_rot = 1.0 - 1.8 * turn_back

                # Attribution Pulse Wave: 18.4s to 21.0s
                pulse_st = 18.4
                pulse_dur = 2.4
                is_pulse_active = pulse_st <= t <= pulse_st + pulse_dur
                pulse_prog = (t - pulse_st) / pulse_dur if is_pulse_active else 0.0

                # Loss Detonation Active: 20.0s to 25.99s
                loss_st = 20.0
                is_loss_active = t >= loss_st
                loss_fade = min(1.0, max(0.0, (t - loss_st) / 0.6)) if is_loss_active else 0.0

                # Title Active: 21.8s to 25.99s
                title_st = 21.8
                is_title_active = t >= title_st
                title_fade = min(1.0, max(0.0, (t - title_st) / 1.2)) if is_title_active else 0.0

                # Background Network Dimming factor when dial is isolated
                bg_dim = 1.0
                if is_dial_active:
                    bg_dim = 1.0 - 0.72 * dial_fade

                # Current Training Input Digit (cycles 3 -> 5 -> 7)
                # Prompt change at 5.0s and 9.5s
                if t < 5.0:
                    curr_input_digit = 3
                elif t < 9.5:
                    curr_input_digit = 5
                else:
                    curr_input_digit = 7

                # Prompt transition flash on digit switch
                trans_flash = 0.0
                for trans_t in (5.0, 9.5):
                    if 0.0 <= t - trans_t <= 0.22:
                        rel_trans = (t - trans_t) / 0.22
                        trans_flash = math.sin(rel_trans * math.pi)
                        break

                # -----------------------------------------------------------
                # INPUT SIDE: Handwritten Training Data Digit (NO STRINGS, PLAIN BLACK BG)
                # -----------------------------------------------------------
                digit_cx = 180.0 * sx
                digit_cy = 540.0 * sy
                digit_scale = 1.25 * sx

                paths, _, _ = get_handwritten_sample(
                    curr_input_digit, digit_cx, digit_cy, digit_scale
                )

                # Continuous traveling forward inference wave sweeping across layers (L0 -> L6)
                wave_speed = 0.85
                wave_phase = (t * wave_speed) % 1.0
                wave_front_l = wave_phase * 6.6

                # Forward surge wave on prompt digit transitions
                surge_boost = [0.0] * 7
                for trans_t in (5.0, 9.5):
                    if 0.0 <= t - trans_t <= 0.45:
                        rel_t = (t - trans_t) / 0.45
                        surge_front = rel_t * 6.5
                        for l_i in range(7):
                            d_l = abs(l_i - surge_front)
                            if d_l < 1.2:
                                surge_boost[l_i] = max(surge_boost[l_i], (1.0 - d_l / 1.2) * math.sin(rel_t * math.pi))

                # Dynamic effective activations for all neurons across the entire network
                effective_acts: list[list[float]] = []
                for l_idx, count in enumerate(layer_counts):
                    layer_acts = []
                    base_layer = digit_layer_acts[curr_input_digit][l_idx]
                    wave_dist = abs(l_idx - wave_front_l)
                    wave_boost = max(0.0, 1.0 - wave_dist / 1.1) if wave_dist < 1.1 else 0.0
                    for i in range(count):
                        bw = base_layer[i]
                        jitter = 0.04 * math.sin(7.0 * t + l_idx * 1.7 + i * 1.3)
                        eff = min(1.0, max(0.0, bw + jitter + 0.35 * wave_boost + 0.45 * surge_boost[l_idx]))
                        layer_acts.append(eff)
                    effective_acts.append(layer_acts)

                active_weights = effective_acts[0]

                if composite_net_alpha > 0.01:
                    # Render Handwritten Digit Strokes with high-contrast glowing ink (STANDALONE, NO STRINGS)
                    glow_ink = skia.Paint(
                        Color=skia.Color4f(0.00, 0.95, 1.00, (0.35 + 0.25 * trans_flash) * composite_net_alpha * bg_dim),
                        StrokeWidth=26.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        StrokeCap=skia.Paint.kRound_Cap,
                        StrokeJoin=skia.Paint.kRound_Join,
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10.0 * sx),
                        AntiAlias=True,
                    )
                    body_ink = skia.Paint(
                        Color=skia.Color4f(0.85, 0.98, 1.00, 0.98 * composite_net_alpha * bg_dim),
                        StrokeWidth=12.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        StrokeCap=skia.Paint.kRound_Cap,
                        StrokeJoin=skia.Paint.kRound_Join,
                        AntiAlias=True,
                    )
                    core_ink = skia.Paint(
                        Color=skia.Color4f(1.00, 1.00, 1.00, 1.00 * composite_net_alpha * bg_dim),
                        StrokeWidth=4.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        StrokeCap=skia.Paint.kRound_Cap,
                        StrokeJoin=skia.Paint.kRound_Join,
                        AntiAlias=True,
                    )
                    for p in paths:
                        canvas.drawPath(p, glow_ink)
                        canvas.drawPath(p, body_ink)
                        canvas.drawPath(p, core_ink)

                    # Vertical Optical Datum Rail behind Layer 0
                    in_layer_x = static_positions[0][0][0] * sx
                    top_node_y = static_positions[0][0][1] * sy
                    bot_node_y = static_positions[0][9][1] * sy
                    rail_pad = 42.0 * sy

                    rail_p = skia.Paint(
                        Color=skia.Color4f(0.00, 0.85, 1.00, 0.28 * composite_net_alpha * bg_dim),
                        StrokeWidth=1.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(in_layer_x, top_node_y - rail_pad, in_layer_x, bot_node_y + rail_pad, rail_p)
                    for end_y in (top_node_y - rail_pad, bot_node_y + rail_pad):
                        canvas.drawLine(in_layer_x - 6.0 * sx, end_y, in_layer_x + 6.0 * sx, end_y, rail_p)

                # -----------------------------------------------------------
                # OUTPUT SIDE: 0-9 Digits Prediction Ladder & Segmented Meters
                # -----------------------------------------------------------
                if composite_net_alpha > 0.01:
                    meter_orig_x = xs[6] * sx + 18.0 * sx
                    bar_w = 90.0 * sx
                    bar_h = 7.0 * sy

                    track_p = skia.Paint(
                        Color=skia.Color4f(0.05, 0.08, 0.16, 0.50 * composite_net_alpha * bg_dim),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    border_track_p = skia.Paint(
                        Color=skia.Color4f(0.15, 0.25, 0.45, 0.40 * composite_net_alpha * bg_dim),
                        StrokeWidth=0.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    bar_fill_p = skia.Paint(Style=skia.Paint.kFill_Style, AntiAlias=True)

                    # Compute dynamic probabilities for digits 0-9 mimicking training
                    probs: list[float] = [0.0] * 10
                    jitter = 0.03 * math.sin(6.0 * t)

                    if curr_input_digit == 3:
                        for d in range(10):
                            probs[d] = 0.05 + 0.02 * math.sin(4.0 * t + d)
                        probs[3] = 0.62 + jitter
                        probs[8] = 0.18 - jitter
                    elif curr_input_digit == 5:
                        for d in range(10):
                            probs[d] = 0.04 + 0.02 * math.sin(4.0 * t + d)
                        probs[5] = 0.58 + jitter
                        probs[6] = 0.22 - jitter
                    else:  # curr_input_digit == 7 (Early Training Mistake: predicts digit 2!)
                        for d in range(10):
                            probs[d] = 0.03 + 0.015 * math.sin(3.5 * t + d)
                        # High erroneous guess on digit 2
                        probs[2] = 0.76 + jitter
                        # True digit 7 has low probability early on
                        probs[7] = 0.12 - jitter * 0.5

                    # Render each of the 10 prediction rows
                    for d in range(10):
                        out_pt = static_positions[6][d]
                        row_y = out_pt[1] * sy
                        row_x = meter_orig_x

                        # 1. Classic Block-Style Digit Badge (Small 3x5 block digit)
                        badge_lit = skia.Paint(
                            Color=(
                                skia.Color4f(1.0, 0.15, 0.30, 0.98 * composite_net_alpha)
                                if (is_loss_active and d == 2)
                                else (
                                    skia.Color4f(0.98, 0.75, 0.14, 0.95 * composite_net_alpha * bg_dim)
                                    if probs[d] > 0.4
                                    else skia.Color4f(0.70, 0.85, 1.0, 0.80 * composite_net_alpha * bg_dim)
                                )
                            ),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        )
                        badge_dim = skia.Paint(
                            Color=skia.Color4f(0.2, 0.3, 0.5, 0.15 * composite_net_alpha * bg_dim),
                            Style=skia.Paint.kFill_Style,
                            AntiAlias=True,
                        )

                        # Mini 5x7 block digit
                        draw_block_digit(
                            canvas,
                            d,
                            row_x,
                            row_y - 7.0 * sy,
                            1.8 * sx,
                            2.0 * sy,
                            0.7 * sx,
                            badge_lit,
                            badge_dim,
                        )

                        # 2. Segmented Probability Bar Meter
                        bar_start_x = row_x + 18.0 * sx
                        track_rrect = skia.RRect.MakeRectXY(
                            skia.Rect.MakeXYWH(bar_start_x, row_y - bar_h * 0.5, bar_w, bar_h),
                            2.0 * sx,
                            2.0 * sy,
                        )
                        canvas.drawRRect(track_rrect, track_p)
                        canvas.drawRRect(track_rrect, border_track_p)

                        # Active filled bar with segmented ticks
                        prob_val = max(0.02, min(1.0, probs[d]))
                        fill_w = prob_val * bar_w

                        if is_loss_active and d == 2:
                            bar_col = skia.Color4f(1.0, 0.15, 0.30, 0.98 * composite_net_alpha)
                        elif probs[d] > 0.4:
                            bar_col = skia.Color4f(0.98, 0.75, 0.14, 0.95 * composite_net_alpha * bg_dim)
                        elif d == curr_input_digit:
                            bar_col = skia.Color4f(0.00, 0.96, 0.63, 0.80 * composite_net_alpha * bg_dim)
                        else:
                            bar_col = skia.Color4f(0.18, 0.45, 0.80, 0.45 * composite_net_alpha * bg_dim)

                        bar_fill_p.setColor(bar_col)
                        fill_rrect = skia.RRect.MakeRectXY(
                            skia.Rect.MakeXYWH(bar_start_x, row_y - bar_h * 0.5, fill_w, bar_h),
                            2.0 * sx,
                            2.0 * sy,
                        )
                        canvas.drawRRect(fill_rrect, bar_fill_p)

                        # Segment division lines across bar
                        div_p = skia.Paint(
                            Color=skia.Color4f(0.0, 0.0, 0.0, 0.70 * composite_net_alpha * bg_dim),
                            StrokeWidth=1.0 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        for seg_i in range(1, 10):
                            seg_x = bar_start_x + seg_i * (bar_w / 10.0)
                            if seg_x < bar_start_x + fill_w:
                                canvas.drawLine(seg_x, row_y - bar_h * 0.5, seg_x, row_y + bar_h * 0.5, div_p)

                # -----------------------------------------------------------
                # Render Dynamic Fluid Connection Filaments
                # (Neurons are static; connections have multi-harmonic wave sway)
                # -----------------------------------------------------------
                hl_l, hl_i, hl_j = 1, 5, 7

                if composite_net_alpha > 0.01:
                    for l_idx, i, j, weight, sway_phase, freq, amp, depth_tier in conns:
                        p1 = static_positions[l_idx][i]
                        p2 = static_positions[l_idx + 1][j]

                        # Multi-frequency traveling wave physics for silky fluid motion
                        sway1 = (
                            amp * math.sin(freq * t + sway_phase) * 0.72
                            + amp * 0.40 * math.sin(freq * 1.8 * t + sway_phase * 1.4)
                        ) * sy
                        sway2 = (
                            amp * math.cos(freq * 0.9 * t + sway_phase * 0.8) * 0.65
                            + amp * 0.35 * math.sin(freq * 2.1 * t + sway_phase * 1.6)
                        ) * sy

                        x1, y1 = p1[0] * sx, p1[1] * sy
                        x2, y2 = p2[0] * sx, p2[1] * sy
                        dx = x2 - x1
                        sag = (y2 - y1) * 0.035

                        c1x = x1 + dx * 0.48
                        c1y = y1 + sag + sway1
                        c2x = x2 - dx * 0.48
                        c2y = y2 - sag - sway2

                        path = skia.Path()
                        path.moveTo(x1, y1)
                        path.cubicTo(c1x, c1y, c2x, c2y, x2, y2)

                        # Highlighted Focal Dial Synapse
                        if l_idx == hl_l and i == hl_i and j == hl_j:
                            if is_dial_active and dial_fade > 0:
                                gold_stroke.setColor(skia.Color4f(0.98, 0.75, 0.14, 0.35 * dial_fade * composite_net_alpha))
                                gold_stroke.setStrokeWidth(6.0 * sx)
                                canvas.drawPath(path, gold_stroke)

                                gold_stroke.setColor(skia.Color4f(0.98, 0.85, 0.24, 0.95 * dial_fade * composite_net_alpha))
                                gold_stroke.setStrokeWidth(2.4 * sx)
                                canvas.drawPath(path, gold_stroke)

                                gold_stroke.setColor(skia.Color4f(1.0, 1.0, 1.0, 0.98 * dial_fade * composite_net_alpha))
                                gold_stroke.setStrokeWidth(1.0 * sx)
                                canvas.drawPath(path, gold_stroke)
                                continue

                        # Loss feeder tint: connections feeding into Output Node 2 pulse ruby
                        is_error_feeder = is_loss_active and l_idx == 5 and j == 2
                        if is_error_feeder:
                            alpha = (0.20 + 0.45 * loss_fade * math.sin(4.0 * t + sway_phase) ** 2) * composite_net_alpha
                            stroke_paint.setColor(skia.Color4f(1.0, 0.12, 0.28, alpha))
                            stroke_paint.setStrokeWidth(1.8 * sx)
                            canvas.drawPath(path, stroke_paint)
                            continue

                        # Connection activation status across entire network
                        act_src = effective_acts[l_idx][i]
                        act_dst = effective_acts[l_idx + 1][j]
                        is_active_synapse = (act_src > 0.42) and (act_dst > 0.42) and (weight > -0.25)

                        wave_dist = abs(l_idx + 0.5 - wave_front_l)
                        wave_boost = max(0.0, 1.0 - wave_dist / 1.1) if wave_dist < 1.1 else 0.0

                        c1_rgb = LAYER_PALETTES[l_idx]
                        c2_rgb = LAYER_PALETTES[l_idx + 1]
                        r_blend = 0.55 * c1_rgb[0] + 0.45 * c2_rgb[0]
                        g_blend = 0.55 * c1_rgb[1] + 0.45 * c2_rgb[1]
                        b_blend = 0.55 * c1_rgb[2] + 0.45 * c2_rgb[2]

                        if is_active_synapse:
                            alpha = (0.24 + 0.38 * (act_src * act_dst) + 0.28 * wave_boost) * composite_net_alpha * bg_dim
                            strk_w = (0.95 + 0.70 * wave_boost + abs(weight) * 0.35) * sx
                        else:
                            base_a = 0.06 if depth_tier == 0 else 0.12
                            alpha = (base_a + abs(weight) * 0.10) * composite_net_alpha * bg_dim
                            strk_w = (0.50 if depth_tier == 0 else 0.80) * sx

                        conn_paint.setColor(skia.Color4f(r_blend, g_blend, b_blend, min(1.0, alpha)))
                        conn_paint.setStrokeWidth(strk_w)
                        canvas.drawPath(path, conn_paint)

                # -----------------------------------------------------------
                # Ambient Fluid Photon Packets (Living Signals)
                # -----------------------------------------------------------
                if composite_net_alpha > 0.05 and t < 18.5:
                    pkt_p = skia.Paint(Style=skia.Paint.kFill_Style, AntiAlias=True)
                    for cycle_t in (1.2, 4.0, 6.8, 9.6, 12.4, 15.2):
                        if cycle_t <= t <= cycle_t + 2.8:
                            rel_t = (t - cycle_t) / 2.8
                            step_idx = min(5, int(rel_t * 6))
                            u_prog = (rel_t * 6) - step_idx
                            sample_c = conns[(step_idx * 53 + 19) % len(conns)]
                            l_idx, i, j, _, s_phase, freq, amp, _ = sample_c
                            p1 = static_positions[l_idx][i]
                            p2 = static_positions[l_idx + 1][j]
                            sway1 = amp * math.sin(freq * t + s_phase) * sy
                            sway2 = amp * 0.6 * math.cos(freq * 1.1 * t + s_phase) * sy
                            pts_line = cubic_pts(p1[0], p1[1], p2[0], p2[1], sway1, sway2, num_pts=14)
                            k = min(len(pts_line) - 1, max(0, int(u_prog * (len(pts_line) - 1))))
                            px, py = pts_line[k][0] * sx, pts_line[k][1] * sy

                            col_r, col_g, col_b = LAYER_PALETTES[l_idx]
                            pkt_p.setColor(skia.Color4f(col_r, col_g, col_b, 0.25 * composite_net_alpha * bg_dim))
                            canvas.drawCircle(px, py, 5.0 * sx, pkt_p)
                            pkt_p.setColor(skia.Color4f(1.0, 1.0, 1.0, 0.90 * composite_net_alpha * bg_dim))
                            canvas.drawCircle(px, py, 1.2 * sx, pkt_p)

                # -----------------------------------------------------------
                # Precision Circular Dial HUD (10.8s - 18.4s) - ZERO TEXT CLUTTER
                # -----------------------------------------------------------
                if is_dial_active and dial_fade > 0 and composite_net_alpha > 0:
                    hl_p1 = static_positions[hl_l][hl_i]
                    hl_p2 = static_positions[hl_l + 1][hl_j]
                    dial_cx = (hl_p1[0] + hl_p2[0]) * 0.5 * sx
                    dial_cy = (hl_p1[1] + hl_p2[1]) * 0.5 * sy - 75.0 * sy

                    synapse_contact_y = (hl_p1[1] + hl_p2[1]) * 0.5 * sy

                    # Delicate leader line from dial to synapse
                    leader_p = skia.Paint(
                        Color=skia.Color4f(0.98, 0.75, 0.14, 0.65 * dial_fade * composite_net_alpha),
                        StrokeWidth=1.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(
                        dial_cx,
                        dial_cy + 36.0 * sx,
                        dial_cx,
                        synapse_contact_y,
                        leader_p,
                    )

                    # Concentric radar locator rings on synapse contact
                    radar_p = skia.Paint(
                        Color=skia.Color4f(0.98, 0.85, 0.24, 0.95 * dial_fade * composite_net_alpha),
                        Style=skia.Paint.kStroke_Style,
                        StrokeWidth=0.8 * sx,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(dial_cx, synapse_contact_y, 4.0 * sx, radar_p)
                    canvas.drawCircle(dial_cx, synapse_contact_y, 7.5 * sx, radar_p)
                    jewel_p = skia.Paint(
                        Color=skia.Color4f(1.0, 1.0, 1.0, 0.95 * dial_fade * composite_net_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(dial_cx, synapse_contact_y, 2.0 * sx, jewel_p)

                    # Dark Obsidian Dial Disc
                    dial_bg = skia.Paint(
                        Color=skia.Color4f(0.01, 0.02, 0.06, 0.92 * dial_fade * composite_net_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(dial_cx, dial_cy, 34.0 * sx, dial_bg)

                    # Outer Brushed Titanium/Gold Reticle Ring
                    ring_p = skia.Paint(
                        Color=skia.Color4f(0.98, 0.75, 0.14, 0.45 * dial_fade * composite_net_alpha),
                        StrokeWidth=1.0 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(dial_cx, dial_cy, 33.0 * sx, ring_p)

                    # 36 Fine Radial Calibration Ticks
                    tick_p = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
                    for deg in range(0, 360, 10):
                        rad = math.radians(deg)
                        is_card = deg % 90 == 0
                        is_sub = deg % 30 == 0
                        r_in = 34.0 * sx if is_card else (35.5 * sx if is_sub else 37.0 * sx)
                        r_out = 39.5 * sx
                        tx1 = dial_cx + r_in * math.cos(rad)
                        ty1 = dial_cy + r_in * math.sin(rad)
                        tx2 = dial_cx + r_out * math.cos(rad)
                        ty2 = dial_cy + r_out * math.sin(rad)
                        tick_p.setColor(
                            skia.Color4f(
                                0.98,
                                0.80,
                                0.20,
                                (0.95 if is_card else (0.65 if is_sub else 0.30)) * dial_fade * composite_net_alpha,
                            )
                        )
                        tick_p.setStrokeWidth((1.2 if is_card else 0.7) * sx)
                        canvas.drawLine(tx1, ty1, tx2, ty2, tick_p)

                    # Sweeping Circular Arc Gauge
                    needle_ang = -45.0 + 90.0 * dial_rot
                    arc_p = skia.Paint(
                        Color=skia.Color4f(0.98, 0.85, 0.24, 0.90 * dial_fade * composite_net_alpha),
                        StrokeWidth=2.2 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    arc_rect = skia.Rect.MakeXYWH(dial_cx - 28.0 * sx, dial_cy - 28.0 * sx, 56.0 * sx, 56.0 * sx)
                    start_angle = -135.0
                    sweep_angle = needle_ang - start_angle
                    canvas.drawArc(arc_rect, start_angle, sweep_angle, False, arc_p)

                    # Needle Pointer
                    n_rad = math.radians(needle_ang)
                    n_len = 30.0 * sx
                    nx_tip = dial_cx + n_len * math.cos(n_rad)
                    ny_tip = dial_cy + n_len * math.sin(n_rad)

                    needle_p = skia.Paint(
                        Color=skia.Color4f(1.0, 1.0, 1.0, 0.98 * dial_fade * composite_net_alpha),
                        StrokeWidth=1.8 * sx,
                        Style=skia.Paint.kStroke_Style,
                        AntiAlias=True,
                    )
                    canvas.drawLine(dial_cx, dial_cy, nx_tip, ny_tip, needle_p)

                    # Center Pin Jewel
                    center_pin = skia.Paint(
                        Color=skia.Color4f(0.98, 0.75, 0.14, 1.0 * dial_fade * composite_net_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )
                    canvas.drawCircle(dial_cx, dial_cy, 3.5 * sx, center_pin)
                    center_pin.setColor(skia.Color4f(1.0, 1.0, 1.0, 1.0 * dial_fade * composite_net_alpha))
                    canvas.drawCircle(dial_cx, dial_cy, 1.2 * sx, center_pin)

                # -----------------------------------------------------------
                # Forward Attribution Pulse (18.4s - 21.0s)
                # -----------------------------------------------------------
                if is_pulse_active and composite_net_alpha > 0:
                    sweep_x = 560.0 + pulse_prog * (1560.0 - 560.0)
                    pulse_front_p = skia.Paint(
                        Shader=skia.GradientShader.MakeLinear(
                            [((sweep_x - 120.0) * sx, 540.0 * sy), ((sweep_x + 30.0) * sx, 540.0 * sy)],
                            [
                                skia.ColorSetARGB(0, 0, 240, 255),
                                skia.ColorSetARGB(max(0, min(255, round(0.35 * composite_net_alpha * 255))), 0, 240, 255),
                                skia.ColorSetARGB(max(0, min(255, round(0.80 * composite_net_alpha * 255))), 255, 255, 255),
                            ],
                            [0.0, 0.75, 1.0],
                        ),
                        AntiAlias=True,
                    )
                    canvas.drawRect(
                        skia.Rect.MakeXYWH(
                            (sweep_x - 120.0) * sx,
                            120.0 * sy,
                            150.0 * sx,
                            840.0 * sy,
                        ),
                        pulse_front_p,
                    )

                # -----------------------------------------------------------
                # Output Error Node & Crimson Loss Flare (20.0s - 25.99s)
                # -----------------------------------------------------------
                err_l, err_idx = 6, 2
                err_pt = static_positions[err_l][err_idx]
                err_x, err_y = err_pt[0] * sx, err_pt[1] * sy

                if is_loss_active and loss_fade > 0 and composite_net_alpha > 0:
                    # Expanding Multi-Frequency Shockwave Rings
                    shock_time = t - loss_st
                    for r_ring in (25.0, 50.0, 80.0):
                        prog_ring = (shock_time * 1.5 + r_ring / 80.0) % 1.0
                        ring_rad = (12.0 + prog_ring * 75.0) * sx
                        ring_alpha = (1.0 - prog_ring) * 0.75 * loss_fade * composite_net_alpha
                        shock_p = skia.Paint(
                            Color=skia.Color4f(1.0, 0.12, 0.28, ring_alpha),
                            StrokeWidth=1.2 * sx,
                            Style=skia.Paint.kStroke_Style,
                            AntiAlias=True,
                        )
                        canvas.drawCircle(err_x, err_y, ring_rad, shock_p)

                    # Crimson Beacon Core Flare
                    loss_glow = skia.Paint(
                        Shader=skia.GradientShader.MakeRadial(
                            (err_x, err_y),
                            42.0 * sx,
                            [
                                skia.Color4f(1.0, 0.15, 0.30, 0.95 * loss_fade * composite_net_alpha),
                                skia.Color4f(1.0, 0.05, 0.20, 0.35 * loss_fade * composite_net_alpha),
                                skia.Color4f(0.0, 0.0, 0.0, 0.0),
                            ],
                            [0.0, 0.45, 1.0],
                        )
                    )
                    canvas.drawCircle(err_x, err_y, 42.0 * sx, loss_glow)

                    # Elegant Dashed Golden Quad Curve (Tracer from dial to error)
                    arc_path = skia.Path()
                    dial_px = (static_positions[hl_l][hl_i][0] + static_positions[hl_l + 1][hl_j][0]) * 0.5 * sx
                    dial_py = (static_positions[hl_l][hl_i][1] + static_positions[hl_l + 1][hl_j][1]) * 0.5 * sy
                    arc_path.moveTo(dial_px, dial_py)
                    arc_path.quadTo((dial_px + err_x) * 0.5, 180.0 * sy, err_x, err_y)

                    arc_paint = skia.Paint(
                        Color=skia.Color4f(0.98, 0.75, 0.14, 0.50 * loss_fade * composite_net_alpha),
                        StrokeWidth=1.5 * sx,
                        Style=skia.Paint.kStroke_Style,
                        PathEffect=skia.DashPathEffect.Make([7.0 * sx, 5.0 * sx], 0.0),
                        AntiAlias=True,
                    )
                    canvas.drawPath(arc_path, arc_paint)

                # -----------------------------------------------------------
                # Render Razor-Sharp, Compact Micro-Neurons (108 Nodes)
                # -----------------------------------------------------------
                if composite_net_alpha > 0.01:
                    orbit_p = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
                    disc_p = skia.Paint(Color=skia.Color4f(0.01, 0.02, 0.05, 0.98 * composite_net_alpha), AntiAlias=True)
                    border_p = skia.Paint(Style=skia.Paint.kStroke_Style, AntiAlias=True)
                    core_p = skia.Paint(Style=skia.Paint.kFill_Style, AntiAlias=True)
                    spark_p = skia.Paint(
                        Color=skia.Color4f(1.0, 1.0, 1.0, 0.98 * composite_net_alpha),
                        Style=skia.Paint.kFill_Style,
                        AntiAlias=True,
                    )

                    for l_idx, pts in enumerate(static_positions):
                        col_r, col_g, col_b = LAYER_PALETTES[l_idx]
                        is_layer_active = is_pulse_active and abs(l_idx - pulse_prog * 6.0) < 0.9

                        for i, (bx, by) in enumerate(pts):
                            px, py = bx * sx, by * sy

                            is_dial_node = is_dial_active and (
                                (l_idx == hl_l and i == hl_i) or (l_idx == hl_l + 1 and i == hl_j)
                            )
                            is_error_node = is_loss_active and l_idx == err_l and i == err_idx
                            node_act = effective_acts[l_idx][i]
                            is_node_firing = node_act > 0.42

                            # High-Tech Firing Visuals Across WHOLE Network
                            if is_node_firing and composite_net_alpha > 0.05:
                                # 1. Glowing area where neuron affects (Radial Bloom Aura)
                                glow_rad = (18.0 + 14.0 * node_act) * sx
                                area_glow = skia.Paint(
                                    Shader=skia.GradientShader.MakeRadial(
                                        (px, py),
                                        glow_rad,
                                        [
                                            skia.Color4f(col_r, col_g, col_b, 0.60 * node_act * composite_net_alpha * bg_dim),
                                            skia.Color4f(col_r * 0.7, col_g * 0.7, col_b * 0.7, 0.20 * node_act * composite_net_alpha * bg_dim),
                                            skia.Color4f(0.00, 0.00, 0.00, 0.0),
                                        ],
                                        [0.0, 0.45, 1.0],
                                    ),
                                    AntiAlias=True,
                                )
                                canvas.drawCircle(px, py, glow_rad, area_glow)

                                # 2. Anamorphic horizontal laser streak through firing neuron
                                streak_w = (38.0 + 26.0 * node_act) * sx
                                streak_paint = skia.Paint(
                                    Shader=skia.GradientShader.MakeLinear(
                                        [(px - streak_w, py), (px + streak_w, py)],
                                        [
                                            skia.Color4f(col_r, col_g, col_b, 0.0),
                                            skia.Color4f(1.00, 1.00, 1.00, 0.92 * node_act * composite_net_alpha * bg_dim),
                                            skia.Color4f(col_r, col_g, col_b, 0.0),
                                        ],
                                        [0.0, 0.50, 1.0],
                                    ),
                                    StrokeWidth=1.3 * sy,
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                )
                                canvas.drawLine(px - streak_w, py, px + streak_w, py, streak_paint)

                                # 3. Precision Optical Reticle Ticks
                                tick_p = skia.Paint(
                                    Color=skia.Color4f(col_r, col_g, col_b, 0.90 * node_act * composite_net_alpha * bg_dim),
                                    StrokeWidth=1.0 * sx,
                                    Style=skia.Paint.kStroke_Style,
                                    AntiAlias=True,
                                )
                                t_gap = 6.5 * sx
                                t_len = 3.5 * sx
                                canvas.drawLine(px - t_gap - t_len, py, px - t_gap, py, tick_p)
                                canvas.drawLine(px + t_gap, py, px + t_gap + t_len, py, tick_p)
                                canvas.drawLine(px, py - t_gap - t_len, px, py - t_gap, tick_p)
                                canvas.drawLine(px, py + t_gap, px, py + t_gap + t_len, tick_p)

                            # 1. Subtle Outer Reticle Orbit (Delicate stroked ring, tight 4.2px)
                            orbit_rad = (
                                4.2
                                + (
                                    1.5
                                    if is_error_node
                                    else (0.8 if (is_layer_active or is_node_firing) else 0.0)
                                )
                            ) * sx
                            if is_dial_node:
                                orbit_color = skia.Color4f(0.98, 0.75, 0.14, 0.65 * dial_fade * composite_net_alpha)
                            elif is_error_node:
                                orbit_color = skia.Color4f(1.0, 0.15, 0.30, 0.85 * loss_fade * composite_net_alpha)
                            elif is_node_firing:
                                orbit_color = skia.Color4f(
                                    col_r, col_g, col_b, (0.45 + 0.50 * node_act) * composite_net_alpha * bg_dim
                                )
                            else:
                                orbit_color = skia.Color4f(
                                    col_r,
                                    col_g,
                                    col_b,
                                    0.30 * composite_net_alpha * bg_dim,
                                )
                            orbit_p.setColor(orbit_color)
                            orbit_p.setStrokeWidth(0.7 * sx)
                            canvas.drawCircle(px, py, orbit_rad, orbit_p)

                            # 2. Compact Obsidian Body Disc (2.8px)
                            disc_rad = 2.8 * sx
                            canvas.drawCircle(px, py, disc_rad, disc_p)

                            # 3. Micro Border Ring
                            border_p.setColor(skia.Color4f(col_r, col_g, col_b, 0.85 * composite_net_alpha * bg_dim))
                            border_p.setStrokeWidth(0.6 * sx)
                            canvas.drawCircle(px, py, disc_rad, border_p)

                            # 4. Photonic Nucleus Core (1.4px)
                            core_rad = (
                                1.4
                                + (0.8 if is_error_node else 0.0)
                                + (0.5 if is_dial_node else 0.0)
                                + (0.6 if is_node_firing else 0.0)
                            ) * sx
                            if is_error_node:
                                core_color = skia.Color4f(1.0, 0.15, 0.30, 0.98 * loss_fade * composite_net_alpha)
                            elif is_dial_node:
                                core_color = skia.Color4f(0.98, 0.85, 0.24, 0.98 * dial_fade * composite_net_alpha)
                            elif is_node_firing:
                                core_color = skia.Color4f(1.00, 1.00, 1.00, 0.98 * composite_net_alpha * bg_dim)
                            else:
                                core_color = skia.Color4f(col_r, col_g, col_b, 0.65 * composite_net_alpha * bg_dim)
                            core_p.setColor(core_color)
                            canvas.drawCircle(px, py, core_rad, core_p)

                            # 5. Photonic Center Spark (0.6px white-hot jewel)
                            canvas.drawCircle(px, py, 0.6 * sx, spark_p)

                # -----------------------------------------------------------
                # Grand Title Reveal: "The Chain Rule" (21.8s - 25.99s)
                # (Appears only after the network dissolves into deep void)
                # -----------------------------------------------------------
                if is_title_active and title_fade > 0:
                    # 1. Subtle central ambient focal illumination
                    title_nebula = skia.Paint(
                        Shader=skia.GradientShader.MakeRadial(
                            (960.0 * sx, 520.0 * sy),
                            600.0 * sx,
                            [
                                skia.Color4f(0.98, 0.72, 0.12, 0.22 * title_fade),
                                skia.Color4f(0.0, 0.85, 1.0, 0.06 * title_fade),
                                skia.Color4f(0.0, 0.0, 0.0, 0.0),
                            ],
                            [0.0, 0.40, 1.0],
                        )
                    )
                    canvas.drawCircle(960.0 * sx, 520.0 * sy, 600.0 * sx, title_nebula)

                    # 2. Horizontal anamorphic laser streak across center
                    streak_w = 1000.0 * sx * min(1.0, (t - title_st) / 0.8)
                    streak_p = skia.Paint(
                        Shader=skia.GradientShader.MakeLinear(
                            [(960.0 * sx - streak_w * 0.5, 526.0 * sy), (960.0 * sx + streak_w * 0.5, 526.0 * sy)],
                            [
                                skia.Color4f(1.0, 0.80, 0.20, 0.0),
                                skia.Color4f(1.0, 0.85, 0.30, 0.45 * title_fade),
                                skia.Color4f(1.0, 0.80, 0.20, 0.0),
                            ],
                            [0.0, 0.5, 1.0],
                        ),
                        StrokeWidth=1.0 * sx,
                        AntiAlias=True,
                    )
                    canvas.drawLine(
                        960.0 * sx - streak_w * 0.5, 526.0 * sy,
                        960.0 * sx + streak_w * 0.5, 526.0 * sy,
                        streak_p,
                    )

                    # 3. Chapter Kicker Badge: CHAPTER 01  //  THE ARCHITECTURE
                    kicker_font = skia.Font(tf_sans_bold, 14.0 * sx)
                    kicker_p = skia.Paint(
                        Color=skia.Color4f(0.98, 0.78, 0.20, 0.95 * title_fade),
                        AntiAlias=True,
                    )
                    _draw_letterspaced(
                        canvas,
                        "CHAPTER 01  //  THE ARCHITECTURE",
                        960.0 * sx,
                        435.0 * sy,
                        kicker_font,
                        kicker_p,
                        letter_spacing=5.5 * sx,
                    )

                    # 4. Main Title: Cormorant Garamond Bold (700) at 100px with smooth upward float
                    drift = (1.0 - math.pow(1.0 - title_fade, 2)) * 12.0 * sy
                    t_y = (538.0 - drift) * sy

                    title_font = skia.Font(tf_serif_bold, 100.0 * sx)
                    title_text = "The Chain Rule"
                    t_w = title_font.measureText(title_text)
                    t_x = (1920.0 * sx - t_w) * 0.5

                    # Wide atmospheric amber bloom
                    p_glow_wide = skia.Paint(
                        Color=skia.Color4f(1.0, 0.68, 0.08, 0.40 * title_fade),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24.0 * sx),
                        AntiAlias=True,
                    )
                    canvas.drawString(title_text, t_x, t_y, title_font, p_glow_wide)

                    # Tight razor-sharp laser aura
                    p_glow_tight = skia.Paint(
                        Color=skia.Color4f(1.0, 0.86, 0.30, 0.85 * title_fade),
                        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0 * sx),
                        AntiAlias=True,
                    )
                    canvas.drawString(title_text, t_x, t_y, title_font, p_glow_tight)

                    # Pure white crystalline foreground with specular intensity
                    p_core = skia.Paint(
                        Color=skia.Color4f(1.0, 0.99, 0.97, 1.0 * title_fade),
                        AntiAlias=True,
                    )
                    canvas.drawString(title_text, t_x, t_y, title_font, p_core)

                    # 5. Golden Hairline Geometry Divider
                    div_len = 340.0 * sx * min(1.0, (t - title_st) / 0.7)
                    if div_len > 36.0 * sx:
                        p_div = skia.Paint(
                            Color=skia.Color4f(0.98, 0.80, 0.25, 0.90 * title_fade),
                            StrokeWidth=1.4 * sx,
                            AntiAlias=True,
                        )
                        canvas.drawLine(
                            960.0 * sx - div_len * 0.5, 565.0 * sy,
                            960.0 * sx - 18.0 * sx, 565.0 * sy,
                            p_div,
                        )
                        canvas.drawLine(
                            960.0 * sx + 18.0 * sx, 565.0 * sy,
                            960.0 * sx + div_len * 0.5, 565.0 * sy,
                            p_div,
                        )

                        # Precision diamond emblem at center
                        dia = skia.Path()
                        dia.moveTo(960.0 * sx, 560.0 * sy)
                        dia.lineTo(965.0 * sx, 565.0 * sy)
                        dia.lineTo(960.0 * sx, 570.0 * sy)
                        dia.lineTo(955.0 * sx, 565.0 * sy)
                        dia.close()
                        p_dia = skia.Paint(Color=skia.Color4f(1.0, 0.90, 0.40, 1.0 * title_fade), AntiAlias=True)
                        canvas.drawPath(dia, p_dia)

                        # Corner ticks on divider
                        canvas.drawLine(
                            960.0 * sx - div_len * 0.5, 562.0 * sy,
                            960.0 * sx - div_len * 0.5, 568.0 * sy,
                            p_div,
                        )
                        canvas.drawLine(
                            960.0 * sx + div_len * 0.5, 562.0 * sy,
                            960.0 * sx + div_len * 0.5, 568.0 * sy,
                            p_div,
                        )

                    # 6. Subtext: Crisp, high-contrast, razor-sharp Electric Cyan
                    sub_fade = min(1.0, max(0.0, (t - (title_st + 0.3)) / 0.8)) if is_title_active else 0.0
                    if sub_fade > 0:
                        sub_font_m = skia.Font(tf_sans_bold, 18.5 * sx)
                        sub_paint_m = skia.Paint(
                            Color=skia.Color4f(0.20, 0.92, 1.0, 1.0 * sub_fade),
                            AntiAlias=True,
                        )
                        # Subtle tight glow on subtext to make it electric and sharp
                        sub_glow_p = skia.Paint(
                            Color=skia.Color4f(0.0, 0.80, 1.0, 0.50 * sub_fade),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.0 * sx),
                            AntiAlias=True,
                        )
                        _draw_letterspaced(
                            canvas,
                            "THE MATHEMATICAL ENGINE OF ARTIFICIAL INTELLIGENCE",
                            960.0 * sx,
                            612.0 * sy,
                            sub_font_m,
                            sub_glow_p,
                            letter_spacing=4.5 * sx,
                        )
                        _draw_letterspaced(
                            canvas,
                            "THE MATHEMATICAL ENGINE OF ARTIFICIAL INTELLIGENCE",
                            960.0 * sx,
                            612.0 * sy,
                            sub_font_m,
                            sub_paint_m,
                            letter_spacing=4.5 * sx,
                        )

                snapshot = surface.makeImageSnapshot()
                return Image.frombytes("RGBA", (w, h), snapshot.tobytes())

            def close(self):
                pass

        return Session()


def build_scene_01(
    audio_path: str | Path | None = None,
) -> Scene:
    """Build Scene 01: Numbers Recognition Neural Network Training."""
    scene = Scene(Canvas(1920, 1080, "#000000"))

    if audio_path is not None:
        p = Path(audio_path)
        if p.exists():
            scene.add_audio(str(p), start=0.0, trim_start=0.0, trim_end=SCENE_01_DURATION)

    viewport = Viewport(NeuralNetworkIntroSource(), width=1920, height=1080, position=(960, 540))
    scene.add(viewport)

    scene.wait_until(SCENE_01_DURATION)
    return scene
