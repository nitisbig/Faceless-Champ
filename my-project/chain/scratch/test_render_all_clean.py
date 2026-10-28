import os
os.environ['MPLCONFIGDIR'] = '/tmp/mpl_cache'
import io
import math
import time
from pathlib import Path
from matplotlib import figure
from matplotlib.mathtext import MathTextParser
from matplotlib.font_manager import FontProperties
from PIL import Image
import numpy as np
import skia

# Colors matching euler_scene.py
CYAN = '#68DBE8'
GOLD = '#FFC878'
WHITE = '#FFFFFF'
MINT = '#4EEDB2'

def render_mathtext_transparent(s: str, color: str = 'white', prop=None, dpi: int = 200):
    parser = MathTextParser('path')
    width, height, depth, _, _ = parser.parse(s, dpi=72, prop=prop)
    fig = figure.Figure(figsize=(width / 72.0, height / 72.0))
    fig.patch.set_alpha(0.0)
    fig.text(0, depth / height, s, fontproperties=prop, color=color)
    buf = io.BytesIO()
    fig.savefig(buf, dpi=dpi, format='png', transparent=True)
    buf.seek(0)
    return Image.open(buf).convert('RGBA'), depth * (dpi / 72.0)

def compose_equation(terms: list[tuple[str, str]], font_size: float = 32.0, dpi: int = 200, spacing: int = 14) -> tuple[skia.Image, Image.Image]:
    prop = FontProperties(size=font_size)
    imgs_with_depth = [render_mathtext_transparent(t, color=c, prop=prop, dpi=dpi) for t, c in terms]
    max_ascent = max(img.height - d for img, d in imgs_with_depth)
    max_descent = max(d for img, d in imgs_with_depth)
    total_height = int(max_ascent + max_descent + 8)
    total_width = sum(img.width for img, d in imgs_with_depth) + spacing * (len(imgs_with_depth) - 1) + 16

    comp = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
    cur_x = 8
    baseline_y = max_ascent + 4

    for img, d in imgs_with_depth:
        y = int(baseline_y - (img.height - d))
        comp.alpha_composite(img, (cur_x, y))
        cur_x += img.width + spacing

    sk_img = skia.Image.fromarray(np.array(comp), skia.ColorType.kRGBA_8888_ColorType)
    return sk_img, comp

print("Precompiling LaTeX formulas...")
t0 = time.time()
FORMULAS_DEF = {
    'shot_02a': [
        (r'$\frac{ds}{dt}$', WHITE),
        ('$=$', WHITE),
        (r'$\frac{ds}{d\theta}$', CYAN),
        (r'$\cdot$', WHITE),
        (r'$\frac{d\theta}{dt}$', GOLD)
    ],
    'shot_02b': [
        (r'$\Delta B$', MINT),
        (r'$\approx$', WHITE),
        (r'$\frac{dB}{dr}$', CYAN),
        (r'$\cdot$', WHITE),
        (r'$\Delta r$', GOLD)
    ],
    'stage_1': [
        (r'$\frac{dA}{dC} = \frac{dA}{dB} \cdot \frac{dB}{dC}$', WHITE),
    ],
    'stage_1_colored': [
        (r'$\frac{dA}{dC}$', WHITE),
        ('$=$', WHITE),
        (r'$\frac{dA}{dB}$', CYAN),
        (r'$\cdot$', WHITE),
        (r'$\frac{dB}{dC}$', GOLD),
    ],
    'stage_2': [
        (r'$\frac{dy}{dx}$', WHITE),
        ('$=$', WHITE),
        (r'$\lim_{\Delta x \to 0}$', WHITE),
        (r'$\frac{\Delta y}{\Delta x}$', GOLD)
    ],
    'stage_3': [
        (r'$\frac{dy}{dx}$', WHITE),
        ('$=$', WHITE),
        (r'$2x$', GOLD),
        (r'$\cdot$', WHITE),
        (r'$\cos(x^2)$', CYAN)
    ],
    'stage_4': [
        (r'$\frac{\partial L}{\partial w}$', WHITE),
        ('$=$', WHITE),
        (r'$\frac{\partial L}{\partial a}$', CYAN),
        (r'$\cdot$', WHITE),
        (r'$\frac{\partial a}{\partial z}$', GOLD),
        (r'$\cdot$', WHITE),
        (r'$\frac{\partial z}{\partial w}$', CYAN)
    ],
    'delta_r': [
        (r'$\Delta r = +0.25\%$', GOLD)
    ],
    'vec_v': [
        (r'$\vec{v}$', MINT)
    ],
    'theta_sym': [
        (r'$\theta$', GOLD)
    ],
    'h_sym': [
        (r'$h$', WHITE)
    ],
    'axis_t': [
        (r'$t$', WHITE)
    ],
    'axis_B': [
        (r'$B$', WHITE)
    ],
    'caliper_delta_B': [
        (r'$\Delta B$', MINT)
    ]
}

CACHE: dict[str, skia.Image] = {}
for name, terms in FORMULAS_DEF.items():
    f_size = 26 if 'stage' in name else (34 if 'shot' in name else 24)
    sk_img, _ = compose_equation(terms, font_size=f_size)
    CACHE[name] = sk_img

print(f"Precompiled all formulas in {time.time() - t0:.2f}s!")

# Test rendering Scene 02 shots with zero text clutter
w, h = 1920, 1080
sx, sy = w / 1920.0, h / 1080.0
info = skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
surface = skia.Surface.MakeRaster(info)
canvas = surface.getCanvas()

# Fonts
assets_dir = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "fonts"
tf_serif = skia.Typeface.MakeFromFile(str(assets_dir / "CormorantGaramond[wght].ttf"))
tf_sans = skia.Typeface.MakeFromFile(str(assets_dir / "SpaceGrotesk[wght].ttf"))
if tf_serif is None:
    tf_serif = skia.Typeface("serif")
if tf_sans is None:
    tf_sans = skia.Typeface("sans-serif")

out_dir = Path("output/scene_02_clean_tests")
out_dir.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------
# SHOT 02A FRAME (3.5s)
# -------------------------------------------------------------
canvas.clear(skia.Color4f(0, 0, 0, 1))
t = 3.5
ground_y = 860.0 * sy
pivot_x = 960.0 * sx
pivot_y = 110.0 * sy
cable_len = 380.0 * sy
rod_x = 1260.0 * sx
rod_h = 240.0 * sy
rod_top_y = ground_y - rod_h

theta_0 = 0.58
omega = 2.1
theta = theta_0 * math.sin(t * omega)
d_theta = theta_0 * omega * math.cos(t * omega)

lamp_x = pivot_x + cable_len * math.sin(theta)
lamp_y = pivot_y + cable_len * math.cos(theta)

denom = (rod_top_y - lamp_y)
shadow_x = lamp_x + (ground_y - lamp_y) * (rod_x - lamp_x) / (denom if abs(denom) > 1e-4 else 1e-4)

# Velocity
dt_num = 0.016
theta_f = theta_0 * math.sin((t + dt_num) * omega)
lamp_xf = pivot_x + cable_len * math.sin(theta_f)
lamp_yf = pivot_y + cable_len * math.cos(theta_f)
denom_f = (rod_top_y - lamp_yf)
shadow_xf = lamp_xf + (ground_y - lamp_yf) * (rod_x - lamp_xf) / (denom_f if abs(denom_f) > 1e-4 else 1e-4)
v_shadow = (shadow_xf - shadow_x) / dt_num

# Floor line & ticks
floor_p = skia.Paint(Color=skia.Color4f(0.20, 0.28, 0.40, 0.60), StrokeWidth=1.5 * sx, AntiAlias=True)
canvas.drawLine(100.0 * sx, ground_y, 1820.0 * sx, ground_y, floor_p)
tick_p = skia.Paint(Color=skia.Color4f(0.30, 0.42, 0.58, 0.40), StrokeWidth=1.0 * sx, AntiAlias=True)
for x_pos in range(160, 1800, 40):
    tx = x_pos * sx
    is_major = (x_pos % 200 == 0)
    canvas.drawLine(tx, ground_y, tx, ground_y + (10.0 * sy if is_major else 5.0 * sy), tick_p)

# Volumetric Light Cone
cone_path = skia.Path()
cone_path.moveTo(lamp_x, lamp_y)
cone_w_ground = 780.0 * sx
cone_path.lineTo(lamp_x - cone_w_ground * 0.5, ground_y)
cone_path.lineTo(lamp_x + cone_w_ground * 0.5, ground_y)
cone_path.close()
cone_paint = skia.Paint(
    Shader=skia.GradientShader.MakeRadial(
        (lamp_x, lamp_y), 850.0 * sy,
        [skia.Color4f(1.0, 0.88, 0.45, 0.18), skia.Color4f(1.0, 0.82, 0.30, 0.05), skia.Color4f(0, 0, 0, 0)],
        [0.0, 0.45, 1.0]
    ),
    AntiAlias=True
)
canvas.drawPath(cone_path, cone_paint)

# Light Ray
ray_p = skia.Paint(
    Color=skia.Color4f(1.0, 0.90, 0.40, 0.55),
    StrokeWidth=1.2 * sx,
    PathEffect=skia.DashPathEffect.Make([8.0 * sx, 6.0 * sx], 0.0),
    AntiAlias=True
)
canvas.drawLine(lamp_x, lamp_y, shadow_x, ground_y, ray_p)

# Shadow on ground
s_min = min(rod_x, shadow_x)
s_max = max(rod_x, shadow_x)
shadow_rect = skia.Rect.MakeLTRB(s_min, ground_y, s_max, ground_y + 10.0 * sy)
shadow_p = skia.Paint(Color=skia.Color4f(0.02, 0.04, 0.08, 0.95), AntiAlias=True)
canvas.drawRect(shadow_rect, shadow_p)
shadow_edge_p = skia.Paint(Color=skia.Color4f(0.0, 0.95, 1.0, 0.70), StrokeWidth=2.0 * sx, AntiAlias=True)
canvas.drawLine(s_min, ground_y, s_max, ground_y, shadow_edge_p)

# Rod
rod_w = 10.0 * sx
rod_rect = skia.Rect.MakeLTRB(rod_x - rod_w * 0.5, rod_top_y, rod_x + rod_w * 0.5, ground_y)
rod_p = skia.Paint(
    Shader=skia.GradientShader.MakeLinear(
        [(rod_x - rod_w * 0.5, 0), (rod_x + rod_w * 0.5, 0)],
        [skia.Color4f(0.85, 0.90, 0.98, 0.95), skia.Color4f(0.35, 0.45, 0.58, 0.95)],
        [0.0, 1.0]
    ),
    AntiAlias=True
)
canvas.drawRect(rod_rect, rod_p)
canvas.drawCircle(rod_x, rod_top_y, 4.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 0.85, 0.20, 1.0), AntiAlias=True))

# Symbolic height caliper h next to rod (clean geometric notation)
cal_x = rod_x - 24.0 * sx
cal_p = skia.Paint(Color=skia.Color4f(0.40, 0.55, 0.70, 0.60), StrokeWidth=1.2 * sx, AntiAlias=True)
canvas.drawLine(cal_x, rod_top_y, cal_x, ground_y, cal_p)
canvas.drawLine(cal_x - 4.0 * sx, rod_top_y, cal_x + 4.0 * sx, rod_top_y, cal_p)
canvas.drawLine(cal_x - 4.0 * sx, ground_y, cal_x + 4.0 * sx, ground_y, cal_p)
h_img = CACHE['h_sym']
canvas.drawImage(h_img, cal_x - h_img.width() - 8.0 * sx, (rod_top_y + ground_y) * 0.5 - h_img.height() * 0.5)

# Velocity vector arrow with LaTeX symbol
v_len = min(280.0 * sx, abs(v_shadow) * 0.16 * sx)
if v_len > 14.0 * sx:
    v_dir = 1.0 if v_shadow >= 0 else -1.0
    arrow_end_x = shadow_x + v_dir * v_len
    arrow_y = ground_y - 14.0 * sy
    arrow_p = skia.Paint(Color=skia.Color4f(0.0, 0.96, 0.60, 0.95), StrokeWidth=2.4 * sx, AntiAlias=True)
    canvas.drawLine(shadow_x, arrow_y, arrow_end_x, arrow_y, arrow_p)
    head_len = 10.0 * sx
    head_w = 6.0 * sy
    canvas.drawLine(arrow_end_x, arrow_y, arrow_end_x - v_dir * head_len, arrow_y - head_w, arrow_p)
    canvas.drawLine(arrow_end_x, arrow_y, arrow_end_x - v_dir * head_len, arrow_y + head_w, arrow_p)
    v_img = CACHE['vec_v']
    canvas.drawImage(v_img, (shadow_x + arrow_end_x) * 0.5 - v_img.width() * 0.5, arrow_y - v_img.height() - 4.0 * sy)

# Lamp Pendulum & Pivot
mount_p = skia.Paint(Color=skia.Color4f(0.50, 0.55, 0.65, 0.85), AntiAlias=True)
canvas.drawRect(skia.Rect.MakeLTRB(pivot_x - 30.0 * sx, pivot_y - 12.0 * sy, pivot_x + 30.0 * sx, pivot_y), mount_p)
canvas.drawCircle(pivot_x, pivot_y, 4.0 * sx, mount_p)

# Vertical plumb line for angle theta
plumb_p = skia.Paint(Color=skia.Color4f(0.30, 0.40, 0.55, 0.45), StrokeWidth=1.0 * sx, PathEffect=skia.DashPathEffect.Make([4.0 * sx, 4.0 * sx], 0.0), AntiAlias=True)
canvas.drawLine(pivot_x, pivot_y, pivot_x, pivot_y + 120.0 * sy, plumb_p)

# Angle arc theta
arc_rad = 75.0 * sx
arc_p = skia.Paint(Color=skia.Color4f(0.98, 0.78, 0.20, 0.75), StrokeWidth=1.4 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
arc_rect = skia.Rect.MakeXYWH(pivot_x - arc_rad, pivot_y - arc_rad, arc_rad * 2, arc_rad * 2)
theta_deg = math.degrees(theta)
start_angle = 90.0 if theta >= 0 else 90.0 + theta_deg
sweep_angle = theta_deg if theta >= 0 else -theta_deg
canvas.drawArc(arc_rect, start_angle, sweep_angle, False, arc_p)
# Theta symbol
th_img = CACHE['theta_sym']
th_angle = math.radians(90 + theta_deg * 0.5)
canvas.drawImage(th_img, pivot_x + (arc_rad + 18.0 * sx) * math.cos(th_angle) - th_img.width() * 0.5, pivot_y + (arc_rad + 18.0 * sx) * math.sin(th_angle) - th_img.height() * 0.5)

# Cable & Lamp
cable_p = skia.Paint(Color=skia.Color4f(0.70, 0.75, 0.85, 0.85), StrokeWidth=1.5 * sx, AntiAlias=True)
canvas.drawLine(pivot_x, pivot_y, lamp_x, lamp_y, cable_p)
# Bell
bell_path = skia.Path()
bw, bh = 28.0 * sx, 22.0 * sy
bell_path.moveTo(lamp_x, lamp_y - 6.0 * sy)
bell_path.lineTo(lamp_x - bw * 0.5, lamp_y + bh)
bell_path.lineTo(lamp_x + bw * 0.5, lamp_y + bh)
bell_path.close()
canvas.drawPath(bell_path, skia.Paint(Color=skia.Color4f(0.25, 0.30, 0.40, 0.95), AntiAlias=True))
# Bulb
bulb_y = lamp_y + bh + 4.0 * sy
canvas.drawCircle(lamp_x, bulb_y, 16.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 0.88, 0.35, 0.85), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12.0 * sx), AntiAlias=True))
canvas.drawCircle(lamp_x, bulb_y, 6.0 * sx, skia.Paint(Color=skia.Color4f(1.0, 1.0, 0.95, 1.0), AntiAlias=True))

# Master LaTeX Equation Floating Cleanly (NO HUD box, NO text clutter!)
eq_img = CACHE['shot_02a']
eq_x = 220.0 * sx
eq_y = 220.0 * sy
# Subtle soft radial glow behind formula
f_glow = skia.Paint(
    Shader=skia.GradientShader.MakeRadial(
        (eq_x + eq_img.width() * 0.5, eq_y + eq_img.height() * 0.5),
        eq_img.width() * 0.8,
        [skia.Color4f(0.0, 0.85, 1.0, 0.08), skia.Color4f(0, 0, 0, 0)],
        [0.0, 1.0]
    )
)
canvas.drawCircle(eq_x + eq_img.width() * 0.5, eq_y + eq_img.height() * 0.5, eq_img.width() * 0.8, f_glow)
canvas.drawImage(eq_img, eq_x, eq_y)

# Save Shot 02A test
surface.makeImageSnapshot().save(str(out_dir / "clean_shot_02A.png"))

# -------------------------------------------------------------
# SHOT 02B FRAME (8.5s)
# -------------------------------------------------------------
canvas.clear(skia.Color4f(0, 0, 0, 1))
t = 8.5
nudge_progress = 1.0
curr_rate = 5.25

# Minimalist Floating Dial on Left (no card outline!)
dial_cx = 380.0 * sx
dial_cy = 500.0 * sy
dial_rad = 120.0 * sx

dial_ring_p = skia.Paint(Color=skia.Color4f(0.20, 0.30, 0.42, 0.60), StrokeWidth=2.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
canvas.drawCircle(dial_cx, dial_cy, dial_rad, dial_ring_p)

for deg in range(-140, 141, 10):
    rad = math.radians(deg - 90)
    is_maj = (deg % 30 == 0)
    t_len = 12.0 * sx if is_maj else 6.0 * sx
    p1 = (dial_cx + (dial_rad - 6.0 * sx) * math.cos(rad), dial_cy + (dial_rad - 6.0 * sx) * math.sin(rad))
    p2 = (dial_cx + (dial_rad - 6.0 * sx - t_len) * math.cos(rad), dial_cy + (dial_rad - 6.0 * sx - t_len) * math.sin(rad))
    canvas.drawLine(p1[0], p1[1], p2[0], p2[1], dial_ring_p)

# Active golden arc
arc_p = skia.Paint(Color=skia.Color4f(0.98, 0.78, 0.20, 0.90), StrokeWidth=4.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
arc_rect = skia.Rect.MakeXYWH(dial_cx - dial_rad + 3.0 * sx, dial_cy - dial_rad + 3.0 * sx, (dial_rad - 3.0 * sx) * 2, (dial_rad - 3.0 * sx) * 2)
canvas.drawArc(arc_rect, -120.0, 37.0, False, arc_p)

# Needle
needle_rad = math.radians(5.0 - 90)
nx = dial_cx + (dial_rad - 18.0 * sx) * math.cos(needle_rad)
ny = dial_cy + (dial_rad - 18.0 * sx) * math.sin(needle_rad)
needle_core = skia.Paint(Color=skia.Color4f(1.0, 1.0, 0.95, 1.0), StrokeWidth=2.2 * sx, AntiAlias=True)
canvas.drawLine(dial_cx, dial_cy, nx, ny, needle_core)
canvas.drawCircle(dial_cx, dial_cy, 7.0 * sx, needle_core)

def draw_math_centered(canvas, img: skia.Image, cx: float, cy: float, max_w: float | None = None, alpha: float = 1.0, base_scale: float = 0.5):
    scale = base_scale
    if max_w and (img.width() * scale > max_w):
        scale = max_w / img.width()
    w = img.width() * scale
    h = img.height() * scale
    dst = skia.Rect.MakeXYWH(cx - w * 0.5, cy - h * 0.5, w, h)
    p = skia.Paint(Alphaf=alpha, AntiAlias=True)
    canvas.drawImageRect(img, dst, skia.SamplingOptions(skia.FilterMode.kLinear), p)

# Key Number: 5.25%
r_font = skia.Font(tf_serif, 46.0 * sx)
r_paint = skia.Paint(Color=skia.Color4f(1.0, 0.98, 0.95, 1.0), AntiAlias=True)
r_str = f"{curr_rate:.2f}%"
r_w = r_font.measureText(r_str)
canvas.drawString(r_str, dial_cx - r_w * 0.5, dial_cy + 155.0 * sy, r_font, r_paint)

# Clean LaTeX symbol \Delta r = +0.25% below dial
dr_img = CACHE['delta_r']
draw_math_centered(canvas, dr_img, dial_cx, dial_cy + 205.0 * sy, base_scale=0.55)

# Compounding Curves on Right (bare axes, no bulky card box!)
gx0 = 760.0 * sx
gy0 = 760.0 * sy
gw = 960.0 * sx
gh = 480.0 * sy

# Bare coordinate axes
axis_p = skia.Paint(Color=skia.Color4f(0.35, 0.45, 0.60, 0.70), StrokeWidth=1.5 * sx, AntiAlias=True)
canvas.drawLine(gx0, gy0, gx0 + gw, gy0, axis_p)
canvas.drawLine(gx0, gy0, gx0, gy0 - gh, axis_p)

# Arrowheads on axes
head_s = 8.0 * sx
canvas.drawLine(gx0 + gw, gy0, gx0 + gw - head_s, gy0 - head_s * 0.6, axis_p)
canvas.drawLine(gx0 + gw, gy0, gx0 + gw - head_s, gy0 + head_s * 0.6, axis_p)
canvas.drawLine(gx0, gy0 - gh, gx0 - head_s * 0.6, gy0 - gh + head_s, axis_p)
canvas.drawLine(gx0, gy0 - gh, gx0 + head_s * 0.6, gy0 - gh + head_s, axis_p)

# Clean LaTeX Axis Labels: t and B
t_img = CACHE['axis_t']
b_img = CACHE['axis_B']
draw_math_centered(canvas, t_img, gx0 + gw + 22.0 * sx, gy0, base_scale=0.5)
draw_math_centered(canvas, b_img, gx0, gy0 - gh - 22.0 * sy, base_scale=0.5)

# Year tick marks
for yr in (10, 20, 30):
    tx = gx0 + (yr / 30.0) * gw * 0.92
    canvas.drawLine(tx, gy0, tx, gy0 + 6.0 * sy, axis_p)
    canvas.drawString(f"{yr}", tx - 8.0 * sx, gy0 + 26.0 * sy, skia.Font(tf_sans, 13.0 * sx), axis_p)

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
    b_nudge = P * math.pow(1.0525, yr)
    py_nudge = gy0 - (b_nudge / b_max) * (gh * 0.84)
    base_pts.append((px, py_base))
    nudge_pts.append((px, py_nudge))

# Shaded Ribbon
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
        [skia.Color4f(0.0, 0.95, 0.65, 0.05), skia.Color4f(0.0, 0.95, 0.65, 0.35)],
        [0.0, 1.0]
    ),
    AntiAlias=True
)
canvas.drawPath(ribbon, ribbon_p)

# Base curve
path_base = skia.Path()
path_base.moveTo(base_pts[0][0], base_pts[0][1])
for pt in base_pts[1:]:
    path_base.lineTo(pt[0], pt[1])
canvas.drawPath(path_base, skia.Paint(Color=skia.Color4f(0.40, 0.65, 0.80, 0.70), StrokeWidth=2.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True))

# Nudge curve
path_nudge = skia.Path()
path_nudge.moveTo(nudge_pts[0][0], nudge_pts[0][1])
for pt in nudge_pts[1:]:
    path_nudge.lineTo(pt[0], pt[1])
canvas.drawPath(path_nudge, skia.Paint(Color=skia.Color4f(0.0, 0.96, 0.60, 0.50), StrokeWidth=5.0 * sx, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0 * sx), Style=skia.Paint.kStroke_Style, AntiAlias=True))
canvas.drawPath(path_nudge, skia.Paint(Color=skia.Color4f(0.20, 1.0, 0.75, 1.0), StrokeWidth=2.4 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True))

# Caliper brackets at t=30
x30 = base_pts[-1][0]
y30_base = base_pts[-1][1]
y30_nudge = nudge_pts[-1][1]
cal_p = skia.Paint(Color=skia.Color4f(0.0, 0.98, 0.65, 0.90), StrokeWidth=1.5 * sx, AntiAlias=True)
canvas.drawLine(x30 + 12.0 * sx, y30_nudge, x30 + 12.0 * sx, y30_base, cal_p)
canvas.drawLine(x30 + 6.0 * sx, y30_nudge, x30 + 18.0 * sx, y30_nudge, cal_p)
canvas.drawLine(x30 + 6.0 * sx, y30_base, x30 + 18.0 * sx, y30_base, cal_p)

# Clean LaTeX divergence caliper symbol \Delta B
db_img = CACHE['caliper_delta_B']
draw_math_centered(canvas, db_img, x30 + 44.0 * sx, (y30_base + y30_nudge) * 0.5, base_scale=0.55)

# Floating Master LaTeX Formula (NO card box, pure mathematical clarity!)
eq2_img = CACHE['shot_02b']
draw_math_centered(canvas, eq2_img, gx0 + 260.0 * sx, gy0 - gh + 70.0 * sy, base_scale=0.60)

surface.makeImageSnapshot().save(str(out_dir / "clean_shot_02B.png"))

# -------------------------------------------------------------
# SHOT 02C FRAME (Stage 1 Active - 14.0s)
# -------------------------------------------------------------
canvas.clear(skia.Color4f(0, 0, 0, 1))
t = 14.0
active_stage = 1

# Sleek minimalist header (clean, unobtrusive)
hdr_font = skia.Font(tf_sans, 13.0 * sx)
hdr_p = skia.Paint(Color=skia.Color4f(0.50, 0.65, 0.85, 0.70), AntiAlias=True)
hdr_text = "FOUR STAGES TO COMPLETE INTUITION"
canvas.drawString(hdr_text, (1920.0 * sx - hdr_font.measureText(hdr_text)) * 0.5, 150.0 * sy, hdr_font, hdr_p)

card_w = 360.0 * sx
card_h = 580.0 * sy
card_y = 220.0 * sy
card_centers_x = [330.0 * sx, 750.0 * sx, 1170.0 * sx, 1590.0 * sx]

# Connecting conduits
for c_i in range(3):
    p_start = (card_centers_x[c_i] + card_w * 0.5, card_y + card_h * 0.5)
    p_end = (card_centers_x[c_i + 1] - card_w * 0.5, card_y + card_h * 0.5)
    canvas.drawLine(p_start[0], p_start[1], p_end[0], p_end[1], skia.Paint(Color=skia.Color4f(0.20, 0.28, 0.40, 0.45), StrokeWidth=1.5 * sx, AntiAlias=True))

stages_meta = [
    {"id": 1, "num": "01", "title": "Three Gears", "eq_key": "stage_1_colored", "accent": skia.Color4f(0.0, 0.94, 1.0, 1.0)},
    {"id": 2, "num": "02", "title": "First Principles", "eq_key": "stage_2", "accent": skia.Color4f(0.98, 0.78, 0.20, 1.0)},
    {"id": 3, "num": "03", "title": "The Crucible", "eq_key": "stage_3", "accent": skia.Color4f(0.95, 0.28, 0.65, 1.0)},
    {"id": 4, "num": "04", "title": "Neural Backprop", "eq_key": "stage_4", "accent": skia.Color4f(0.35, 0.75, 1.0, 1.0)},
]

for s_item in stages_meta:
    s_id = s_item["id"]
    cx = card_centers_x[s_id - 1]
    is_active = (active_stage == s_id)
    accent = s_item["accent"]
    alpha = 1.0 if is_active else 0.45

    card_rect = skia.Rect.MakeXYWH(cx - card_w * 0.5, card_y, card_w, card_h)

    # Sleek dark glass card
    c_bg_p = skia.Paint(Color=skia.Color4f(0.02, 0.04, 0.08, 0.85 if is_active else 0.60), AntiAlias=True)
    canvas.drawRoundRect(card_rect, 12.0 * sx, 12.0 * sy, c_bg_p)

    # Active glow rim
    if is_active:
        rim_bloom = skia.Paint(
            Color=skia.Color4f(accent.fR, accent.fG, accent.fB, 0.50),
            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14.0 * sx),
            StrokeWidth=2.4 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True
        )
        canvas.drawRoundRect(card_rect, 12.0 * sx, 12.0 * sy, rim_bloom)

    c_border_p = skia.Paint(
        Color=skia.Color4f(accent.fR, accent.fG, accent.fB, 0.90 if is_active else 0.25),
        StrokeWidth=1.5 * sx if is_active else 1.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True
    )
    canvas.drawRoundRect(card_rect, 12.0 * sx, 12.0 * sy, c_border_p)

    # Stage Numeral (sleek, minimalist, prominent: "01")
    num_font = skia.Font(tf_sans, 18.0 * sx)
    num_p = skia.Paint(Color=skia.Color4f(accent.fR, accent.fG, accent.fB, alpha), AntiAlias=True)
    canvas.drawString(s_item["num"], cx - card_w * 0.5 + 24.0 * sx, card_y + 38.0 * sy, num_font, num_p)

    # Stage Title (Cormorant Garamond serif, elegant)
    t_font = skia.Font(tf_serif, 26.0 * sx)
    t_paint = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, alpha), AntiAlias=True)
    t_str = s_item["title"]
    canvas.drawString(t_str, cx - card_w * 0.5 + 24.0 * sx, card_y + 74.0 * sy, t_font, t_paint)

    # Thin accent divider
    canvas.drawLine(cx - card_w * 0.5 + 24.0 * sx, card_y + 92.0 * sy, cx + card_w * 0.5 - 24.0 * sx, card_y + 92.0 * sy,
                    skia.Paint(Color=skia.Color4f(accent.fR, accent.fG, accent.fB, 0.35 * alpha), StrokeWidth=1.0 * sx, AntiAlias=True))

    # Animated Dynamic Visualization Area
    icon_cy = card_y + 240.0 * sy
    if s_id == 1:
        # Meshed Gears
        g_angle = t * 1.8 if is_active else 0.8
        g1_x, g1_y = cx - 52.0 * sx, icon_cy
        g1_r = 38.0 * sx
        p_g1 = skia.Paint(Color=skia.Color4f(0.0, 0.92, 1.0, alpha), StrokeWidth=1.8 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
        canvas.drawCircle(g1_x, g1_y, g1_r, p_g1)
        for te in range(8):
            a_rad = g_angle + te * (math.tau / 8)
            canvas.drawLine(g1_x + (g1_r - 4.0 * sx) * math.cos(a_rad), g1_y + (g1_r - 4.0 * sx) * math.sin(a_rad), g1_x + (g1_r + 6.0 * sx) * math.cos(a_rad), g1_y + (g1_r + 6.0 * sx) * math.sin(a_rad), p_g1)

        g2_x, g2_y = cx + 10.0 * sx, icon_cy
        g2_r = 25.0 * sx
        p_g2 = skia.Paint(Color=skia.Color4f(0.98, 0.78, 0.20, alpha), StrokeWidth=1.8 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
        canvas.drawCircle(g2_x, g2_y, g2_r, p_g2)
        for te in range(6):
            a_rad = -g_angle * 1.54 + te * (math.tau / 6)
            canvas.drawLine(g2_x + (g2_r - 4.0 * sx) * math.cos(a_rad), g2_y + (g2_r - 4.0 * sx) * math.sin(a_rad), g2_x + (g2_r + 5.0 * sx) * math.cos(a_rad), g2_y + (g2_r + 5.0 * sx) * math.sin(a_rad), p_g2)

        g3_x, g3_y = cx + 54.0 * sx, icon_cy
        g3_r = 16.0 * sx
        p_g3 = skia.Paint(Color=skia.Color4f(0.95, 0.35, 0.45, alpha), StrokeWidth=1.8 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
        canvas.drawCircle(g3_x, g3_y, g3_r, p_g3)
        for te in range(4):
            a_rad = g_angle * 2.42 + te * (math.tau / 4)
            canvas.drawLine(g3_x + (g3_r - 3.0 * sx) * math.cos(a_rad), g3_y + (g3_r - 3.0 * sx) * math.sin(a_rad), g3_x + (g3_r + 4.0 * sx) * math.cos(a_rad), g3_y + (g3_r + 4.0 * sx) * math.sin(a_rad), p_g3)

    elif s_id == 2:
        # Secant to Tangent Limit
        p_curve = skia.Paint(Color=skia.Color4f(0.98, 0.78, 0.20, alpha), StrokeWidth=2.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
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
        p_sec = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, alpha), StrokeWidth=1.5 * sx, AntiAlias=True)
        canvas.drawLine(p0_x - 20.0 * sx, p0_y + 14.0 * sy, p1_x + 20.0 * sx, p1_y - 14.0 * sy, p_sec)
        canvas.drawCircle(p0_x, p0_y, 3.5 * sx, p_sec)
        canvas.drawCircle(p1_x, p1_y, 3.5 * sx, p_sec)

    elif s_id == 3:
        # Wave Crucible
        p_wave = skia.Paint(Color=skia.Color4f(0.95, 0.28, 0.65, alpha), StrokeWidth=2.0 * sx, Style=skia.Paint.kStroke_Style, AntiAlias=True)
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
        p_syn = skia.Paint(Color=skia.Color4f(0.30, 0.50, 0.70, 0.35 * alpha), StrokeWidth=1.0 * sx, AntiAlias=True)
        for l_idx in range(len(mini_nodes) - 1):
            for p1 in mini_nodes[l_idx]:
                for p2 in mini_nodes[l_idx + 1]:
                    canvas.drawLine(p1[0], p1[1], p2[0], p2[1], p_syn)
        for l_idx, node_pts in enumerate(mini_nodes):
            p_node = skia.Paint(Color=skia.Color4f(0.35, 0.75, 1.0, alpha), AntiAlias=True)
            for pt in node_pts:
                canvas.drawCircle(pt[0], pt[1], 3.2 * sx, p_node)

    # Master LaTeX Formula in Card (NO button outline, floating authentically!)
    eq_item = CACHE[s_item["eq_key"]]
    draw_math_centered(canvas, eq_item, cx, card_y + 440.0 * sy, max_w=card_w - 44.0 * sx, alpha=alpha, base_scale=0.52)

surface.makeImageSnapshot().save(str(out_dir / "clean_shot_02C.png"))
print("All clean test frames saved to output/scene_02_clean_tests/!")
