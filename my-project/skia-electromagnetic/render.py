"""Sixty seconds of mathematical and physical electromagnetic wave visualization on pure black.

Rendered natively with Faceless Champ and the CPU Skia backend.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from faceless_champ import (
    Arrow,
    Canvas,
    Circle,
    ExportProgress,
    ExportSettings,
    Line,
    PathData,
    Polyline,
    Rectangle,
    Scene,
    Text,
    VectorPath,
    create_renderer,
    render,
    rendering_identity,
    save_frame,
)

ROOT = Path(__file__).resolve().parent
DURATION = 60.0
TAU = math.tau

# Scientific Palette
CYAN = "#00F0FF"
CYAN_SOFT = "#68DDF0"
CYAN_TINT = "#00F0FF26"
GOLD = "#FFBA70"
GOLD_SOFT = "#FFC778"
GOLD_TINT = "#FFBA7026"
EMERALD = "#22C55E"
EMERALD_SOFT = "#80E7BC"
VIOLET = "#B19AFF"
MAGENTA = "#E066FF"
WHITE = "#E9F4F7"
DIM = "#344A57"
MUTED = "#5A738E"
GHOST = "#15222E"
DARK_SURFACE = "#0B1319"


def smooth(x: float) -> float:
    """Standard smoothstep clamping to [0, 1]."""
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def window(t: float, start: float, end: float, fade: float = 1.2) -> float:
    """Time envelope returning 0 outside [start, end] with smooth fades."""
    if t < start or t > end:
        return 0.0
    u_in = smooth((t - start) / fade) if fade > 0 else 1.0
    u_out = smooth((end - t) / fade) if fade > 0 else 1.0
    return u_in * u_out


def project_3d(
    x: float,
    y: float,
    z: float,
    cx: float = 900.0,
    cy: float = 540.0,
    scale: float = 1.0,
    pitch_deg: float = 20.0,
    yaw_deg: float = 34.0,
) -> tuple[float, float]:
    """Oblique isometric projection from 3D space to 2D canvas coordinates."""
    cp = math.cos(math.radians(pitch_deg))
    sp = math.sin(math.radians(pitch_deg))
    cyaw = math.cos(math.radians(yaw_deg))
    syaw = math.sin(math.radians(yaw_deg))

    # Yaw rotation around Y axis
    rx = x * cyaw - z * syaw
    rz = x * syaw + z * cyaw

    # Pitch rotation around X axis
    ry = y * cp - rz * sp

    # Screen coordinates: positive Y goes up in 3D, so invert Y for canvas
    px = cx + rx * scale
    py = cy - ry * scale
    return px, py


def safe_vector(
    start: tuple[float, float],
    end: tuple[float, float],
    stroke: str,
    stroke_width: float = 2.0,
    tip_size: float = 9.0,
    min_len: float = 3.0,
    opacity: float = 1.0,
) -> Arrow | None:
    """Create Arrow only if distance between endpoints is strictly >= min_len."""
    dist = math.hypot(end[0] - start[0], end[1] - start[1])
    if dist < min_len or opacity <= 0.001:
        return None
    scaled_tip = max(3.0, min(tip_size, dist * 0.45))
    return Arrow(
        start,
        end,
        stroke=stroke,
        stroke_width=stroke_width,
        tip_size=scaled_tip,
        opacity=opacity,
    )


def label(
    value: str,
    position: tuple[float, float],
    color: str = WHITE,
    size: int = 24,
    opacity: float = 1.0,
    anchor: str = "center",
) -> Text:
    """Technical HUD text."""
    actual_anchor = "top_left" if anchor in ("left", "top_left") else "center"
    return Text(
        value,
        position=position,
        font_size=size,
        color=color,
        opacity=opacity,
        anchor=actual_anchor,
        text_engine="skia",
    )


# =============================================================================
# ACT I: 3D TRANSVERSE PLANE WAVE (0.0s – 16.5s)
# =============================================================================
def build_act_1_plane_wave(scene: Scene, t: float, opacity: float) -> None:
    if opacity <= 0.002:
        return

    cx, cy = 900.0, 540.0
    scale = 1.0
    pitch = 20.0
    yaw = 32.0

    # Wave physics constants
    wavelength = 320.0
    k = TAU / wavelength
    omega = TAU * 0.55  # 0.55 Hz oscillation
    e_amp = 165.0
    b_amp = 165.0
    x_min, x_max = -540.0, 540.0

    # 1. 3D Coordinate Reference Axes
    origin_2d = project_3d(0, 0, 0, cx, cy, scale, pitch, yaw)
    axis_x_end = project_3d(x_max + 80, 0, 0, cx, cy, scale, pitch, yaw)
    axis_y_end = project_3d(0, e_amp + 70, 0, cx, cy, scale, pitch, yaw)
    axis_z_end = project_3d(0, 0, b_amp + 70, cx, cy, scale, pitch, yaw)

    # Base coordinate grid lines along the baseline axis
    axis_line = safe_vector(
        project_3d(x_min - 40, 0, 0, cx, cy, scale, pitch, yaw),
        axis_x_end,
        MUTED,
        stroke_width=1.8,
        tip_size=12,
        opacity=opacity * 0.8,
    )
    if axis_line:
        scene.add(axis_line)

    axis_y = safe_vector(
        origin_2d,
        axis_y_end,
        CYAN_SOFT,
        stroke_width=1.5,
        tip_size=10,
        opacity=opacity * 0.7,
    )
    if axis_y:
        scene.add(axis_y)

    axis_z = safe_vector(
        origin_2d,
        axis_z_end,
        GOLD_SOFT,
        stroke_width=1.5,
        tip_size=10,
        opacity=opacity * 0.7,
    )
    if axis_z:
        scene.add(axis_z)

    scene.add(label("k (Propagation Axis)", (axis_x_end[0] + 90, axis_x_end[1]), WHITE, 20, opacity * 0.85))
    scene.add(label("+E (Electric Axis)", (axis_y_end[0], axis_y_end[1] - 18), CYAN, 20, opacity * 0.85))
    scene.add(label("+B (Magnetic Axis)", (axis_z_end[0] - 20, axis_z_end[1] + 20), GOLD, 20, opacity * 0.85))

    # 2. Continuous Wave Ribbons (Translucent Fill between axis and wave curve)
    samples = 120
    xs = [x_min + (x_max - x_min) * (i / (samples - 1)) for i in range(samples)]

    e_pts_2d = [project_3d(x, e_amp * math.cos(k * x - omega * t), 0, cx, cy, scale, pitch, yaw) for x in xs]
    b_pts_2d = [project_3d(x, 0, b_amp * math.cos(k * x - omega * t), cx, cy, scale, pitch, yaw) for x in xs]
    axis_pts_2d = [project_3d(x, 0, 0, cx, cy, scale, pitch, yaw) for x in xs]

    # Draw semi-transparent fill ribbons under E and B waves
    # Electric Ribbon (polygon: axis forward, wave backward)
    e_poly_cmds = [("M", *axis_pts_2d[0])]
    for pt in axis_pts_2d[1:]:
        e_poly_cmds.append(("L", *pt))
    for pt in reversed(e_pts_2d):
        e_poly_cmds.append(("L", *pt))
    e_poly_cmds.append(("Z",))
    scene.add(VectorPath(PathData(tuple(e_poly_cmds)), fill=CYAN_TINT, opacity=opacity * 0.75))

    # Magnetic Ribbon
    b_poly_cmds = [("M", *axis_pts_2d[0])]
    for pt in axis_pts_2d[1:]:
        b_poly_cmds.append(("L", *pt))
    for pt in reversed(b_pts_2d):
        b_poly_cmds.append(("L", *pt))
    b_poly_cmds.append(("Z",))
    scene.add(VectorPath(PathData(tuple(b_poly_cmds)), fill=GOLD_TINT, opacity=opacity * 0.75))

    # 3. Dense Vector Stems (Field Arrows from Axis)
    stem_count = 38
    stem_xs = [x_min + (x_max - x_min) * (i / (stem_count - 1)) for i in range(stem_count)]
    for sx in stem_xs:
        phase = k * sx - omega * t
        e_val = e_amp * math.cos(phase)
        b_val = b_amp * math.cos(phase)

        base_pt = project_3d(sx, 0, 0, cx, cy, scale, pitch, yaw)
        e_tip = project_3d(sx, e_val, 0, cx, cy, scale, pitch, yaw)
        b_tip = project_3d(sx, 0, b_val, cx, cy, scale, pitch, yaw)

        # Electric Field Arrow (Cyan)
        e_vec = safe_vector(base_pt, e_tip, CYAN, stroke_width=2.0, tip_size=8, opacity=opacity * 0.9)
        if e_vec:
            scene.add(e_vec)

        # Magnetic Field Arrow (Gold)
        b_vec = safe_vector(base_pt, b_tip, GOLD, stroke_width=2.0, tip_size=8, opacity=opacity * 0.9)
        if b_vec:
            scene.add(b_vec)

    # 4. Continuous Outlining Curves for E and B waves
    scene.add(Polyline(e_pts_2d, stroke=CYAN, stroke_width=3.2, line_cap="round", opacity=opacity))
    scene.add(Polyline(b_pts_2d, stroke=GOLD, stroke_width=3.2, line_cap="round", opacity=opacity))

    # 5. Poynting Vector S = (1/μ₀)(E × B) at wave front
    poynting_start = project_3d(x_max + 10, 0, 0, cx, cy, scale, pitch, yaw)
    poynting_end = project_3d(x_max + 150, 0, 0, cx, cy, scale, pitch, yaw)
    poynting_arrow = safe_vector(
        poynting_start,
        poynting_end,
        EMERALD,
        stroke_width=4.0,
        tip_size=15,
        opacity=opacity,
    )
    if poynting_arrow:
        scene.add(poynting_arrow)
    scene.add(label("S = (1/μ₀)(E × B)", (poynting_end[0] + 100, poynting_end[1] + 28), EMERALD_SOFT, 22, opacity, "left"))

    # 6. Wavelength Caliper Bracket (measuring crest to crest)
    crest_offset = ((omega * t) / k) % wavelength
    c1_x = -wavelength / 2 + crest_offset
    c2_x = c1_x + wavelength
    if -450 <= c1_x <= 200 and -200 <= c2_x <= 480:
        p_c1 = project_3d(c1_x, e_amp, 0, cx, cy, scale, pitch, yaw)
        p_c2 = project_3d(c2_x, e_amp, 0, cx, cy, scale, pitch, yaw)
        bracket_y = min(p_c1[1], p_c2[1]) - 40
        # Dimension lines
        scene.add(Polyline([(p_c1[0], p_c1[1] - 8), (p_c1[0], bracket_y)], stroke=MUTED, stroke_width=1.2, opacity=opacity * 0.7))
        scene.add(Polyline([(p_c2[0], p_c2[1] - 8), (p_c2[0], bracket_y)], stroke=MUTED, stroke_width=1.2, opacity=opacity * 0.7))
        caliper_arr1 = safe_vector((p_c1[0] + 50, bracket_y), (p_c1[0], bracket_y), WHITE, 1.5, 7, opacity=opacity * 0.8)
        caliper_arr2 = safe_vector((p_c2[0] - 50, bracket_y), (p_c2[0], bracket_y), WHITE, 1.5, 7, opacity=opacity * 0.8)
        if caliper_arr1:
            scene.add(caliper_arr1)
        if caliper_arr2:
            scene.add(caliper_arr2)
        scene.add(label("λ = c / ν", ((p_c1[0] + p_c2[0]) / 2, bracket_y - 14), WHITE, 22, opacity * 0.95))

    # 7. Scientific HUD Annotations
    hud_bg = Rectangle(
        width=480,
        height=180,
        position=(310, 160),
        fill=DARK_SURFACE,
        stroke=MUTED,
        stroke_width=1.2,
        corner_radius=8,
        opacity=opacity * 0.88,
    )
    scene.add(hud_bg)
    scene.add(label("3D PLANE ELECTROMAGNETIC WAVE", (310, 95), CYAN_SOFT, 21, opacity, "center"))
    scene.add(label("TRANSVERSE VACUUM SOLUTION", (310, 122), MUTED, 15, opacity * 0.8, "center"))
    scene.add(label("E(x, t) = E₀ cos(kx - ωt) ŷ", (110, 158), CYAN, 20, opacity, "left"))
    scene.add(label("B(x, t) = B₀ cos(kx - ωt) ẑ", (110, 190), GOLD, 20, opacity, "left"))
    scene.add(label("c = 1 / √(μ₀ε₀) ≈ 2.998 × 10⁸ m/s", (110, 222), WHITE, 18, opacity * 0.9, "left"))

    hud_right = Rectangle(
        width=360,
        height=110,
        position=(1660, 130),
        fill=DARK_SURFACE,
        stroke=MUTED,
        stroke_width=1.2,
        corner_radius=8,
        opacity=opacity * 0.88,
    )
    scene.add(hud_right)
    scene.add(label("FIELD ORTHOGONALITY", (1660, 96), WHITE, 18, opacity, "center"))
    scene.add(label("E ⊥ B ⊥ k", (1660, 126), EMERALD_SOFT, 22, opacity, "center"))
    scene.add(label("E₀ / B₀ = c  (In-Phase)", (1660, 154), MUTED, 16, opacity * 0.85, "center"))


# =============================================================================
# ACT II: WAVE POLARIZATION & 3D HELICAL CORKSCREW (14.8s – 31.5s)
# =============================================================================
def build_act_2_polarization(scene: Scene, t: float, opacity: float) -> None:
    if opacity <= 0.002:
        return

    # Transition delta from 0 (linear) to pi/2 (circular) between 15.5s and 20.5s
    prog = smooth((t - 15.5) / 5.0)
    delta = prog * (math.pi / 2.0)  # phase shift

    cx, cy = 680.0, 540.0
    scale = 0.92
    pitch = 22.0
    yaw = 36.0

    wavelength = 300.0
    k = TAU / wavelength
    omega = TAU * 0.65
    e_amp = 150.0
    x_min, x_max = -480.0, 320.0

    # 1. Propagation Central Axis
    axis_start = project_3d(x_min - 30, 0, 0, cx, cy, scale, pitch, yaw)
    axis_end = project_3d(x_max + 50, 0, 0, cx, cy, scale, pitch, yaw)
    axis_arr = safe_vector(axis_start, axis_end, MUTED, stroke_width=1.8, tip_size=11, opacity=opacity * 0.7)
    if axis_arr:
        scene.add(axis_arr)

    # 2. 3D Helical Curve
    samples = 140
    xs = [x_min + (x_max - x_min) * (i / (samples - 1)) for i in range(samples)]
    helix_pts_2d = []
    for x in xs:
        ey = e_amp * math.cos(k * x - omega * t)
        ez = e_amp * math.cos(k * x - omega * t + delta)
        helix_pts_2d.append(project_3d(x, ey, ez, cx, cy, scale, pitch, yaw))

    scene.add(Polyline(helix_pts_2d, stroke=CYAN, stroke_width=3.5, line_cap="round", opacity=opacity))

    # 3. Rotating Radial Spokes along the Helix
    spoke_count = 28
    spoke_xs = [x_min + (x_max - x_min) * (i / (spoke_count - 1)) for i in range(spoke_count)]
    for sx in spoke_xs:
        ey = e_amp * math.cos(k * sx - omega * t)
        ez = e_amp * math.cos(k * sx - omega * t + delta)
        base_pt = project_3d(sx, 0, 0, cx, cy, scale, pitch, yaw)
        tip_pt = project_3d(sx, ey, ez, cx, cy, scale, pitch, yaw)
        vec = safe_vector(base_pt, tip_pt, VIOLET, stroke_width=1.8, tip_size=7, opacity=opacity * 0.8)
        if vec:
            scene.add(vec)

    # 4. Radiant Beads along the Helix
    bead_count = 7
    for b_idx in range(bead_count):
        bx = x_min + ((b_idx * 115.0 + t * 90.0) % (x_max - x_min))
        bey = e_amp * math.cos(k * bx - omega * t)
        bez = e_amp * math.cos(k * bx - omega * t + delta)
        b_pos = project_3d(bx, bey, bez, cx, cy, scale, pitch, yaw)
        scene.add(Circle(7.0, position=b_pos, fill=WHITE, stroke=CYAN, stroke_width=2.0, opacity=opacity))
        scene.add(Circle(14.0, position=b_pos, fill=None, stroke=CYAN_SOFT, stroke_width=1.2, opacity=opacity * 0.45))

    # =========================================================================
    # Right Detector Disc: 2D End-On Cross Section Target (Polarimeter)
    # =========================================================================
    disc_cx, disc_cy = 1500.0, 540.0
    r_disc = 175.0

    # Background plate & reticle
    scene.add(Circle(r_disc + 25, position=(disc_cx, disc_cy), fill=DARK_SURFACE, stroke=MUTED, stroke_width=1.5, opacity=opacity * 0.9))
    scene.add(Circle(r_disc, position=(disc_cx, disc_cy), fill=None, stroke=GHOST, stroke_width=1.2, opacity=opacity * 0.8))
    scene.add(Circle(r_disc * 0.5, position=(disc_cx, disc_cy), fill=None, stroke=GHOST, stroke_width=1.0, opacity=opacity * 0.6))

    # Crosshairs
    scene.add(Line(r_disc * 2.2, position=(disc_cx, disc_cy), rotation=0, stroke=GHOST, stroke_width=1.2, opacity=opacity * 0.7))
    scene.add(Line(r_disc * 2.2, position=(disc_cx, disc_cy), rotation=90, stroke=GHOST, stroke_width=1.2, opacity=opacity * 0.7))

    scene.add(label("+Ey", (disc_cx, disc_cy - r_disc - 14), CYAN, 18, opacity, "center"))
    scene.add(label("+Ez", (disc_cx + r_disc + 22, disc_cy), GOLD, 18, opacity, "left"))

    # Instantaneous detector values at probe point x = 0
    cur_ey = e_amp * math.cos(-omega * t)
    cur_ez = e_amp * math.cos(-omega * t + delta)

    # Component vectors
    vy_pt = (disc_cx, disc_cy - cur_ey)
    vz_pt = (disc_cx + cur_ez, disc_cy)
    v_net_pt = (disc_cx + cur_ez, disc_cy - cur_ey)

    # Component projection guides
    scene.add(Polyline([vy_pt, v_net_pt], stroke=MUTED, stroke_width=1.0, opacity=opacity * 0.55))
    scene.add(Polyline([vz_pt, v_net_pt], stroke=MUTED, stroke_width=1.0, opacity=opacity * 0.55))

    # Vector Ey on vertical axis
    arr_ey = safe_vector((disc_cx, disc_cy), vy_pt, CYAN, stroke_width=2.5, tip_size=9, opacity=opacity * 0.85)
    if arr_ey:
        scene.add(arr_ey)

    # Vector Ez on horizontal axis
    arr_ez = safe_vector((disc_cx, disc_cy), vz_pt, GOLD, stroke_width=2.5, tip_size=9, opacity=opacity * 0.85)
    if arr_ez:
        scene.add(arr_ez)

    # Net Vector E_total
    arr_net = safe_vector((disc_cx, disc_cy), v_net_pt, MAGENTA, stroke_width=3.8, tip_size=13, opacity=opacity)
    if arr_net:
        scene.add(arr_net)
    scene.add(Circle(6.0, position=v_net_pt, fill=WHITE, stroke=MAGENTA, stroke_width=2.0, opacity=opacity))

    # Locus ring traced by rotating tip
    if delta > 0.1:
        # Ellipse or circle locus
        locus_samples = 64
        locus_pts = [
            (
                disc_cx + e_amp * math.cos(a + delta),
                disc_cy - e_amp * math.cos(a),
            )
            for a in [TAU * (i / locus_samples) for i in range(locus_samples + 1)]
        ]
        scene.add(Polyline(locus_pts, stroke=VIOLET, stroke_width=1.8, opacity=opacity * 0.6))

    # Text annotations
    state_str = "LINEAR POLARIZATION" if delta < 0.1 else "CIRCULAR POLARIZATION" if delta > 1.4 else "ELLIPTICAL POLARIZATION"
    scene.add(label("TRANSVERSE POLARIMETER", (disc_cx, disc_cy - r_disc - 50), WHITE, 20, opacity, "center"))
    scene.add(label(state_str, (disc_cx, disc_cy + r_disc + 45), CYAN_SOFT, 18, opacity, "center"))
    scene.add(label(f"Phase Shift Δφ = {delta / math.pi * 180:.0f}°", (disc_cx, disc_cy + r_disc + 72), MUTED, 16, opacity * 0.85, "center"))

    # HUD Card Top Left
    hud_bg = Rectangle(
        width=480,
        height=170,
        position=(310, 150),
        fill=DARK_SURFACE,
        stroke=MUTED,
        stroke_width=1.2,
        corner_radius=8,
        opacity=opacity * 0.88,
    )
    scene.add(hud_bg)
    scene.add(label("WAVE POLARIZATION STATES", (310, 88), CYAN_SOFT, 21, opacity, "center"))
    scene.add(label("SUPERPOSITION OF ORTHOGONAL MODES", (310, 114), MUTED, 15, opacity * 0.8, "center"))
    scene.add(label("Ey(x, t) = E₀ cos(kx - ωt)", (110, 150), CYAN, 19, opacity, "left"))
    scene.add(label("Ez(x, t) = E₀ cos(kx - ωt + Δφ)", (110, 180), GOLD, 19, opacity, "left"))
    scene.add(label("|E|² = Ey² + Ez² = Constant (when Δφ = π/2)", (110, 210), WHITE, 17, opacity * 0.9, "left"))


# =============================================================================
# ACT III: HERTZIAN DIPOLE RADIATION FIELD (29.8s – 46.5s)
# =============================================================================
def build_act_3_dipole_radiation(scene: Scene, t: float, opacity: float) -> None:
    if opacity <= 0.002:
        return

    cx, cy = 960.0, 540.0
    omega = TAU * 0.85
    c_rad = 110.0  # radial wave speed (pixels per second)

    # 1. Expanding Closed Electric Field Detached Wavefronts
    # In dipole radiation, wavefronts expand radially: R(t) = c*(t - t0)
    # Intensity envelope scales as sin^2(theta)
    num_waves = 7
    for w_idx in range(num_waves):
        wave_age = ((t * 1.2 + w_idx * (3.8 / num_waves)) % 3.8)
        r_peak = wave_age * c_rad
        if r_peak < 25.0:
            continue

        wave_fade = smooth(wave_age / 0.5) * smooth((3.8 - wave_age) / 0.8) * opacity
        if wave_fade <= 0.005:
            continue

        # Left lobe and right lobe closed loops: r(theta) = r_peak * sin^2(theta)
        # Left Lobe (x < cx)
        left_pts = []
        right_pts = []
        theta_steps = 40
        for i in range(theta_steps + 1):
            theta = (i / theta_steps) * math.pi
            r_val = r_peak * (math.sin(theta) ** 2)
            dx = r_val * math.sin(theta)
            dy = r_val * math.cos(theta)
            left_pts.append((cx - dx, cy - dy))
            right_pts.append((cx + dx, cy - dy))

        col = CYAN_SOFT if (w_idx % 2 == 0) else GOLD_SOFT
        scene.add(Polyline(left_pts, stroke=col, stroke_width=2.0, opacity=wave_fade * 0.85))
        scene.add(Polyline(right_pts, stroke=col, stroke_width=2.0, opacity=wave_fade * 0.85))

    # 2. Toroidal Radiation Envelope (Luminous Outer Lobes)
    env_r = 340.0
    env_left = []
    env_right = []
    for i in range(61):
        theta = (i / 60.0) * math.pi
        r_val = env_r * (math.sin(theta) ** 2)
        dx = r_val * math.sin(theta)
        dy = r_val * math.cos(theta)
        env_left.append((cx - dx, cy - dy))
        env_right.append((cx + dx, cy - dy))

    scene.add(Polyline(env_left, stroke=CYAN, stroke_width=2.8, opacity=opacity * 0.95))
    scene.add(Polyline(env_right, stroke=CYAN, stroke_width=2.8, opacity=opacity * 0.95))

    # 3. Dipole Antenna Hardware & Oscillating Charges
    antenna_h = 130.0
    # Metallic conductor rods
    scene.add(Line(antenna_h, position=(cx, cy - antenna_h / 2 - 12), rotation=90, stroke=WHITE, stroke_width=4.0, opacity=opacity))
    scene.add(Line(antenna_h, position=(cx, cy + antenna_h / 2 + 12), rotation=90, stroke=WHITE, stroke_width=4.0, opacity=opacity))

    # Feed gap generator
    scene.add(Circle(10.0, position=(cx, cy), fill=DARK_SURFACE, stroke=MUTED, stroke_width=2.0, opacity=opacity))

    # Oscillating charge positions
    q_disp = (antenna_h * 0.65) * math.cos(omega * t)
    q_top_y = cy - 20 - abs(q_disp)
    q_bot_y = cy + 20 + abs(q_disp)

    # Positive and negative charge spheres
    charge_sign = math.cos(omega * t)
    top_col = CYAN if charge_sign >= 0 else GOLD
    bot_col = GOLD if charge_sign >= 0 else CYAN
    top_sym = "+q" if charge_sign >= 0 else "-q"
    bot_sym = "-q" if charge_sign >= 0 else "+q"

    scene.add(Circle(12.0, position=(cx, q_top_y), fill=top_col, stroke=WHITE, stroke_width=1.5, opacity=opacity))
    scene.add(label(top_sym, (cx + 26, q_top_y), top_col, 17, opacity, "left"))

    scene.add(Circle(12.0, position=(cx, q_bot_y), fill=bot_col, stroke=WHITE, stroke_width=1.5, opacity=opacity))
    scene.add(label(bot_sym, (cx + 26, q_bot_y), bot_col, 17, opacity, "left"))

    # Oscillating Current Arrow I(t)
    curr_val = -math.sin(omega * t)
    if abs(curr_val) > 0.15:
        curr_dir = 1.0 if curr_val > 0 else -1.0
        c_start = (cx - 35, cy - curr_dir * 30)
        c_end = (cx - 35, cy + curr_dir * 30)
        c_arrow = safe_vector(c_start, c_end, EMERALD, stroke_width=3.0, tip_size=10, opacity=opacity * 0.9)
        if c_arrow:
            scene.add(c_arrow)
        scene.add(label("I(t)", (cx - 55, cy), EMERALD_SOFT, 18, opacity, "right"))

    # Zero radiation node along antenna axis
    scene.add(label("Zero Emission Node (θ = 0)", (cx, cy - antenna_h - 45), MUTED, 16, opacity * 0.8, "center"))
    scene.add(label("Zero Emission Node (θ = π)", (cx, cy + antenna_h + 45), MUTED, 16, opacity * 0.8, "center"))

    # Maximum radiation indicators
    scene.add(label("Max Radiation (θ = π/2)", (cx - env_r - 20, cy), CYAN_SOFT, 18, opacity * 0.9, "right"))
    scene.add(label("Max Radiation (θ = π/2)", (cx + env_r + 20, cy), CYAN_SOFT, 18, opacity * 0.9, "left"))

    # HUD Card Top Left
    hud_bg = Rectangle(
        width=520,
        height=180,
        position=(330, 150),
        fill=DARK_SURFACE,
        stroke=MUTED,
        stroke_width=1.2,
        corner_radius=8,
        opacity=opacity * 0.88,
    )
    scene.add(hud_bg)
    scene.add(label("HERTZIAN DIPOLE RADIATION FIELD", (330, 85), CYAN_SOFT, 21, opacity, "center"))
    scene.add(label("ELECTRODYNAMIC WAVE EMISSION", (330, 112), MUTED, 15, opacity * 0.8, "center"))
    scene.add(label("Dipole Moment: p(t) = q₀ d cos(ωt) ẑ", (100, 150), WHITE, 18, opacity, "left"))
    scene.add(label("Intensity Envelope: I(θ) ∝ sin²θ / r²", (100, 180), CYAN, 19, opacity, "left"))
    scene.add(label("Total Radiated Power: P = μ₀ p₀² ω⁴ / (12π c)", (100, 210), GOLD, 18, opacity, "left"))


# =============================================================================
# ACT IV: ELECTROMAGNETIC SPECTRUM & MAXWELL EQUATIONS (44.8s – 60.0s)
# =============================================================================
def build_act_4_spectrum_maxwell(scene: Scene, t: float, opacity: float) -> None:
    if opacity <= 0.002:
        return

    # 1. Maxwell's Four Unified Equations (Top Architecture Cards)
    eq_w, eq_h = 390.0, 95.0
    eq_cards = [
        (260.0, 120.0, "GAUSS'S LAW (ELECTRIC)", "∇ · E = ρ / ε₀", CYAN),
        (720.0, 120.0, "GAUSS'S LAW (MAGNETIC)", "∇ · B = 0", GOLD),
        (1180.0, 120.0, "FARADAY'S INDUCTION", "∇ × E = -∂B/∂t", EMERALD_SOFT),
        (1640.0, 120.0, "AMPÈRE-MAXWELL LAW", "∇ × B = μ₀J + μ₀ε₀ ∂E/∂t", VIOLET),
    ]

    for ecx, ecy, title, eq_str, col in eq_cards:
        scene.add(
            Rectangle(
                width=eq_w,
                height=eq_h,
                position=(ecx, ecy),
                fill=DARK_SURFACE,
                stroke=MUTED,
                stroke_width=1.2,
                corner_radius=6,
                opacity=opacity * 0.88,
            )
        )
        scene.add(label(title, (ecx, ecy - 22), MUTED, 13, opacity * 0.8, "center"))
        scene.add(label(eq_str, (ecx, ecy + 12), col, 21, opacity, "center"))

    # 2. Continuous Electromagnetic Spectrum Ribbon Bar
    bar_x0, bar_x1 = 140.0, 1780.0
    bar_w = bar_x1 - bar_x0
    bar_y = 480.0
    bar_h = 60.0

    scene.add(label("THE CONTINUOUS ELECTROMAGNETIC SPECTRUM", (960, 410), WHITE, 24, opacity, "center"))

    bands = [
        ("RADIO", 0.00, 0.22, "#1B3A57", "Buildings (>1m)"),
        ("MICROWAVE", 0.22, 0.40, "#1F5466", "Butterflies (1mm-1m)"),
        ("INFRARED", 0.40, 0.54, "#6B3824", "Needle Point (1μm)"),
        ("VISIBLE", 0.54, 0.65, "#9C6ADE", "Protozoan (400-700nm)"),
        ("ULTRAVIOLET", 0.65, 0.77, "#582882", "Molecules (10nm)"),
        ("X-RAY", 0.77, 0.89, "#311B6B", "Atoms (0.1nm)"),
        ("GAMMA RAY", 0.89, 1.00, "#5E184A", "Atomic Nuclei (<10⁻¹²m)"),
    ]

    for name, u0, u1, fill_col, scale_str in bands:
        bx = bar_x0 + u0 * bar_w
        bw = (u1 - u0) * bar_w
        bc = bx + bw / 2
        scene.add(
            Rectangle(
                width=bw - 4,
                height=bar_h,
                position=(bc, bar_y),
                fill=fill_col,
                stroke=MUTED,
                stroke_width=1.0,
                corner_radius=4,
                opacity=opacity * 0.9,
            )
        )
        scene.add(label(name, (bc, bar_y - 8), WHITE, 17, opacity, "center"))
        scene.add(label(scale_str, (bc, bar_y + 16), CYAN_SOFT, 12, opacity * 0.8, "center"))

    # 3. Traveling Photon Wave Packet (Traveling Left to Right across Spectrum)
    # t goes from 46 to 58s -> progress 0 to 1
    sweep_prog = smooth((t - 46.5) / 10.0)
    packet_x = bar_x0 + sweep_prog * bar_w

    # Draw local oscillating wave inside the packet showing wavelength shortening
    local_k = 0.04 + 0.35 * (sweep_prog ** 1.8)
    wave_pts = []
    packet_span = 120.0
    for px in range(int(packet_x - packet_span), int(packet_x + packet_span), 2):
        if bar_x0 <= px <= bar_x1:
            dx = px - packet_x
            env = math.exp(-(dx ** 2) / (2.0 * (45.0 ** 2)))
            wy = 720.0 - 75.0 * env * math.cos(local_k * dx - TAU * 4.0 * t)
            wave_pts.append((float(px), wy))

    if len(wave_pts) > 2:
        scene.add(Polyline(wave_pts, stroke=CYAN, stroke_width=3.2, line_cap="round", opacity=opacity))

    # Tracking beacon arrow above the wave packet
    beacon_top = (packet_x, bar_y + bar_h / 2 + 10)
    beacon_bot = (packet_x, bar_y + bar_h / 2 + 45)
    beacon_arr = safe_vector(beacon_bot, beacon_top, WHITE, stroke_width=2.5, tip_size=9, opacity=opacity * 0.9)
    if beacon_arr:
        scene.add(beacon_arr)

    # 4. Live Digital Telemetry Gauges (Updating as packet moves)
    # Logarithmic conversions across 14 orders of magnitude
    log_freq = 6.0 + sweep_prog * 15.0  # 10^6 Hz (1 MHz Radio) to 10^21 Hz (1 ZHz Gamma)
    freq_val = 10.0 ** log_freq
    c_const = 3.0e8
    wavelength_val = c_const / freq_val
    h_ev = 4.135667e-15  # Planck constant in eV*s
    energy_ev = h_ev * freq_val

    # Format human-friendly readings
    if wavelength_val >= 1.0:
        wl_str = f"{wavelength_val:.1f} m"
    elif wavelength_val >= 1e-3:
        wl_str = f"{wavelength_val * 1e3:.1f} mm"
    elif wavelength_val >= 1e-6:
        wl_str = f"{wavelength_val * 1e6:.1f} μm"
    elif wavelength_val >= 1e-9:
        wl_str = f"{wavelength_val * 1e9:.1f} nm"
    else:
        wl_str = f"{wavelength_val * 1e12:.1f} pm"

    if freq_val < 1e9:
        fq_str = f"{freq_val / 1e6:.1f} MHz"
    elif freq_val < 1e12:
        fq_str = f"{freq_val / 1e9:.1f} GHz"
    elif freq_val < 1e15:
        fq_str = f"{freq_val / 1e12:.1f} THz"
    elif freq_val < 1e18:
        fq_str = f"{freq_val / 1e15:.1f} PHz"
    else:
        fq_str = f"{freq_val / 1e18:.1f} EHz"

    if energy_ev < 1e-3:
        en_str = f"{energy_ev * 1e6:.1f} μeV"
    elif energy_ev < 1.0:
        en_str = f"{energy_ev * 1e3:.1f} meV"
    elif energy_ev < 1e3:
        en_str = f"{energy_ev:.2f} eV"
    elif energy_ev < 1e6:
        en_str = f"{energy_ev / 1e3:.1f} keV"
    else:
        en_str = f"{energy_ev / 1e6:.1f} MeV"

    # Telemetry HUD Panel
    hud_tele_w = 780.0
    hud_tele_h = 130.0
    scene.add(
        Rectangle(
            width=hud_tele_w,
            height=hud_tele_h,
            position=(960, 890),
            fill=DARK_SURFACE,
            stroke=MUTED,
            stroke_width=1.2,
            corner_radius=8,
            opacity=opacity * 0.9,
        )
    )

    scene.add(label("DYNAMIC QUANTUM & WAVE PARAMETERS", (960, 842), CYAN_SOFT, 18, opacity, "center"))

    col_x1 = 960 - 230
    col_x2 = 960
    col_x3 = 960 + 230

    scene.add(label("WAVELENGTH  λ = c / ν", (col_x1, 882), MUTED, 14, opacity * 0.8, "center"))
    scene.add(label(wl_str, (col_x1, 915), WHITE, 24, opacity, "center"))

    scene.add(label("FREQUENCY  ν", (col_x2, 882), MUTED, 14, opacity * 0.8, "center"))
    scene.add(label(fq_str, (col_x2, 915), GOLD, 24, opacity, "center"))

    scene.add(label("PHOTON ENERGY  E = hν", (col_x3, 882), MUTED, 14, opacity * 0.8, "center"))
    scene.add(label(en_str, (col_x3, 915), EMERALD_SOFT, 24, opacity, "center"))


# =============================================================================
# SCENE CLASS WITH DETERMINISTIC SAMPLE ENGINE
# =============================================================================
class ElectromagneticScene(Scene):
    """60-second analytic electromagnetic visualization scene."""

    def construct(self) -> None:
        self.wait_until(DURATION)

    def sample(self, t: float) -> Scene:
        """Sample deterministic geometry at source time t in [0, 60]."""
        if not math.isfinite(t) or not 0 <= t <= DURATION:
            raise ValueError(f"source time must be in [0, {DURATION}]")

        scene = Scene(Canvas(1920, 1080, "#000000"))

        # Global entry / exit fade
        global_fade = window(t, 0.0, DURATION, fade=1.5)

        # Act Envelopes with smooth transitions
        act_1_op = window(t, 0.0, 16.5, fade=1.5) * global_fade
        act_2_op = window(t, 14.8, 31.5, fade=1.5) * global_fade
        act_3_op = window(t, 29.8, 46.5, fade=1.5) * global_fade
        act_4_op = window(t, 44.8, 60.0, fade=1.5) * global_fade

        build_act_1_plane_wave(scene, t, act_1_op)
        build_act_2_polarization(scene, t, act_2_op)
        build_act_3_dipole_radiation(scene, t, act_3_op)
        build_act_4_spectrum_maxwell(scene, t, act_4_op)

        scene.wait_until(DURATION)
        return scene


def build_scene() -> ElectromagneticScene:
    return ElectromagneticScene(Canvas(1920, 1080, "#000000"))


class ElectromagneticRenderer:
    """Public renderer adapter: source-time vector descriptions painted by Skia."""

    def __init__(self) -> None:
        self.native = create_renderer("skia", antialias=1, frame_cache_mb=0)

    def validate(self, node: Scene) -> None:
        self.native.validate(node.sample(0.0))

    def frame(self, node: Scene, time: float, size: tuple[int, int]):
        return self.native.frame(node.sample(time), 0.0, size)

    def __enter__(self):
        return self

    def __exit__(self, *exc: object) -> None:
        self.native.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float, metavar="SECONDS", help="Render a single frame still")
    mode.add_argument("--preview", action="store_true", help="Two-second motion excerpt (source seconds 6–8)")
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"), help="Custom source time range")
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.frame is not None and not 0 <= args.frame <= DURATION:
        parser.error(f"frame must be in [0, {DURATION}]")
    if args.range and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error(f"range must satisfy 0 <= START < END <= {DURATION}")
    if args.fps <= 0:
        parser.error("fps must be positive")

    scene = build_scene()
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png"
        if args.frame is not None
        else "preview.mp4"
        if args.preview
        else "skia-electromagnetic.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    source_range = args.range or ([6.0, 8.0] if args.preview else [0.0, DURATION])

    with ElectromagneticRenderer() as renderer:
        if args.frame is not None:
            source_range = [args.frame, args.frame]
            save_frame(
                scene,
                args.frame,
                output,
                size=settings.dimensions(scene.canvas),
                renderer=renderer,
                overwrite=args.overwrite,
            )
        else:
            with ExportProgress() as progress:
                render(
                    scene,
                    output,
                    settings=settings,
                    start_time=source_range[0],
                    end_time=source_range[1],
                    renderer=renderer,
                    overwrite=args.overwrite,
                    progress=progress,
                )
        stats = dict(renderer.native.stats)

    output.with_suffix(".json").write_text(
        json.dumps(
            {
                "scene_duration": scene.duration,
                "source_range": source_range,
                "rendering": rendering_identity("skia", scene.sample(8.0)),
                "stats": stats,
                "full_export_verified": False,
            },
            indent=2,
        )
    )
    print(f"Exported: {output}")


if __name__ == "__main__":
    main()
