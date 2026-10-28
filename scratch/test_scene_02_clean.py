import os
os.environ['MPLCONFIGDIR'] = '/tmp/mpl_cache'
import math
from pathlib import Path
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.mathtext as mathtext
import io
import skia

def render_latex(parts: list[tuple[str, str]], dpi: int = 240, spacing: int = 8) -> skia.Image:
    images = []
    max_h = 0
    total_w = 0
    for tex, color in parts:
        buf = io.BytesIO()
        mathtext.math_to_image(f'${tex}$', buf, dpi=dpi, format='png', color=color)
        buf.seek(0)
        im = Image.open(buf).convert('RGBA')
        images.append(im)
        max_h = max(max_h, im.height)
        total_w += im.width + spacing
    total_w -= spacing

    canvas_im = Image.new('RGBA', (total_w, max_h), (0, 0, 0, 0))
    cur_x = 0
    for im in images:
        y_pos = (max_h - im.height) // 2
        canvas_im.paste(im, (cur_x, y_pos), im)
        cur_x += im.width + spacing

    w, h = canvas_im.size
    info = skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
    return skia.Image.MakeRasterData(info, skia.Data.MakeWithCopy(canvas_im.tobytes()), w * 4)

def draw_latex_glow(canvas, img: skia.Image, cx: float, cy: float, alpha: float = 1.0, scale: float = 1.0):
    w = img.width() * scale
    h = img.height() * scale
    x = cx - w * 0.5
    y = cy - h * 0.5

    # 1. Subtle soft glow behind formula
    glow_p = skia.Paint(
        Color=skia.Color4f(0.0, 0.85, 1.0, 0.25 * alpha),
        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10.0),
        AntiAlias=True
    )
    canvas.save()
    canvas.translate(x, y)
    canvas.scale(scale, scale)
    # Draw core image
    core_p = skia.Paint(Color=skia.Color4f(1.0, 1.0, 1.0, alpha), AntiAlias=True)
    canvas.drawImage(img, 0, 0, core_p)
    canvas.restore()

out_dir = Path("my-project/chain/output/scene_02_clean_tests")
out_dir.mkdir(parents=True, exist_ok=True)

w, h = 1920, 1080
info = skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)

# Pre-render key formulas
eq_chain = render_latex([
    (r'\frac{ds}{dt}', '#FFFFFF'),
    ('=', '#FFFFFF'),
    (r'\frac{ds}{d\theta}', '#68DBE8'),
    (r'\cdot', '#FFFFFF'),
    (r'\frac{d\theta}{dt}', '#FFC878')
], dpi=260)

sym_theta = render_latex([(r'\theta', '#FFC878')], dpi=200)
sym_v = render_latex([(r'\vec{v}', '#4EEDB2')], dpi=200)
sym_h = render_latex([(r'h', '#68DBE8')], dpi=200)

eq_bank = render_latex([
    (r'\Delta B', '#4EEDB2'),
    (r'\approx', '#FFFFFF'),
    (r'\frac{dB}{dr}', '#68DBE8'),
    (r'\cdot', '#FFFFFF'),
    (r'\Delta r', '#FFC878')
], dpi=260)
sym_delta_b = render_latex([(r'\Delta B', '#4EEDB2')], dpi=220)
sym_delta_r = render_latex([(r'\Delta r = +0.25\%', '#FFC878')], dpi=220)
sym_axis_t = render_latex([(r't', '#8EA4C8')], dpi=180)
sym_axis_B = render_latex([(r'B(t)', '#8EA4C8')], dpi=180)

# -------------------------------------------------------------
# TEST 1: Shot 02A Clean
# -------------------------------------------------------------
surface1 = skia.Surface.MakeRaster(info)
c1 = surface1.getCanvas()
c1.clear(skia.Color4f(0.0, 0.0, 0.0, 1.0))

# Geometry
ground_y = 860.0
pivot_x, pivot_y = 960.0, 110.0
cable_len = 380.0
rod_x = 1260.0
rod_h = 240.0
rod_top_y = ground_y - rod_h

# Pendulum at t = 3.5s
t = 3.5
theta_0 = 0.58
omega = 2.1
theta = theta_0 * math.sin(t * omega)
lamp_x = pivot_x + cable_len * math.sin(theta)
lamp_y = pivot_y + cable_len * math.cos(theta)
denom = rod_top_y - lamp_y
shadow_x = lamp_x + (ground_y - lamp_y) * (rod_x - lamp_x) / denom

# Floor
floor_p = skia.Paint(Color=skia.Color4f(0.20, 0.28, 0.40, 0.60), StrokeWidth=1.5, AntiAlias=True)
c1.drawLine(100.0, ground_y, 1820.0, ground_y, floor_p)

# Light cone
cone_path = skia.Path()
cone_path.moveTo(lamp_x, lamp_y)
cone_path.lineTo(lamp_x - 420.0, ground_y)
cone_path.lineTo(lamp_x + 420.0, ground_y)
cone_path.close()
c1.drawPath(cone_path, skia.Paint(
    Shader=skia.GradientShader.MakeRadial(
        (lamp_x, lamp_y), 850.0,
        [skia.Color4f(1.0, 0.88, 0.45, 0.16), skia.Color4f(1.0, 0.82, 0.30, 0.04), skia.Color4f(0, 0, 0, 0)],
        [0.0, 0.45, 1.0]
    ),
    AntiAlias=True
))

# Ray trace line
ray_p = skia.Paint(Color=skia.Color4f(1.0, 0.90, 0.40, 0.50), StrokeWidth=1.2, PathEffect=skia.DashPathEffect.Make([8.0, 6.0], 0.0), AntiAlias=True)
c1.drawLine(lamp_x, lamp_y, shadow_x, ground_y, ray_p)

# Floor shadow
shadow_p = skia.Paint(Color=skia.Color4f(0.02, 0.04, 0.08, 0.95), AntiAlias=True)
c1.drawRect(skia.Rect.MakeLTRB(min(rod_x, shadow_x), ground_y, max(rod_x, shadow_x), ground_y + 10.0), shadow_p)
shadow_edge_p = skia.Paint(Color=skia.Color4f(0.0, 0.95, 1.0, 0.75), StrokeWidth=2.0, AntiAlias=True)
c1.drawLine(min(rod_x, shadow_x), ground_y, max(rod_x, shadow_x), ground_y, shadow_edge_p)

# Vertical Rod with height marker h
rod_w = 10.0
rod_p = skia.Paint(Color=skia.Color4f(0.70, 0.78, 0.90, 0.95), AntiAlias=True)
c1.drawRect(skia.Rect.MakeLTRB(rod_x - rod_w * 0.5, rod_top_y, rod_x + rod_w * 0.5, ground_y), rod_p)
c1.drawCircle(rod_x, rod_top_y, 4.0, skia.Paint(Color=skia.Color4f(1.0, 0.85, 0.20, 1.0), AntiAlias=True))

# Symbolic height caliper for rod (replaces "FIXED OBSTACLE" text!)
cal_x = rod_x + 22.0
cal_p = skia.Paint(Color=skia.Color4f(0.40, 0.85, 0.95, 0.60), StrokeWidth=1.0, AntiAlias=True)
c1.drawLine(cal_x, rod_top_y, cal_x, ground_y, cal_p)
c1.drawLine(cal_x - 4.0, rod_top_y, cal_x + 4.0, rod_top_y, cal_p)
c1.drawLine(cal_x - 4.0, ground_y, cal_x + 4.0, ground_y, cal_p)
draw_latex_glow(c1, sym_h, cal_x + 16.0, (rod_top_y + ground_y) * 0.5)

# Lamp cable & bulb
cable_p = skia.Paint(Color=skia.Color4f(0.65, 0.70, 0.80, 0.75), StrokeWidth=1.4, AntiAlias=True)
c1.drawLine(pivot_x, pivot_y, lamp_x, lamp_y, cable_p)

# Symbolic angle arc \theta at pivot
plumb_p = skia.Paint(Color=skia.Color4f(0.40, 0.50, 0.65, 0.40), StrokeWidth=1.0, PathEffect=skia.DashPathEffect.Make([4.0, 4.0], 0.0), AntiAlias=True)
c1.drawLine(pivot_x, pivot_y, pivot_x, pivot_y + 120.0, plumb_p)
arc_rect = skia.Rect.MakeXYWH(pivot_x - 70.0, pivot_y - 70.0, 140.0, 140.0)
arc_deg = math.degrees(theta)
c1.drawArc(arc_rect, 90.0, arc_deg, False, skia.Paint(Color=skia.Color4f(1.0, 0.85, 0.30, 0.85), StrokeWidth=1.5, Style=skia.Paint.kStroke_Style, AntiAlias=True))
draw_latex_glow(c1, sym_theta, pivot_x + 36.0 * math.sin(theta * 0.5), pivot_y + 85.0)

# Bulb glow
bulb_y = lamp_y + 16.0
c1.drawCircle(lamp_x, bulb_y, 16.0, skia.Paint(Color=skia.Color4f(1.0, 0.88, 0.35, 0.85), MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 12.0), AntiAlias=True))
c1.drawCircle(lamp_x, bulb_y, 5.0, skia.Paint(Color=skia.Color4f(1.0, 1.0, 0.95, 1.0), AntiAlias=True))

# Dynamic Velocity Vector Arrow with symbolic \vec{v}
v_arrow_x = shadow_x - 120.0
c1.drawLine(shadow_x, ground_y - 12.0, v_arrow_x, ground_y - 12.0, skia.Paint(Color=skia.Color4f(0.0, 0.96, 0.60, 0.95), StrokeWidth=2.4, AntiAlias=True))
c1.drawLine(v_arrow_x, ground_y - 12.0, v_arrow_x + 10.0, ground_y - 18.0, skia.Paint(Color=skia.Color4f(0.0, 0.96, 0.60, 0.95), StrokeWidth=2.4, AntiAlias=True))
c1.drawLine(v_arrow_x, ground_y - 12.0, v_arrow_x + 10.0, ground_y - 6.0, skia.Paint(Color=skia.Color4f(0.0, 0.96, 0.60, 0.95), StrokeWidth=2.4, AntiAlias=True))
draw_latex_glow(c1, sym_v, (shadow_x + v_arrow_x) * 0.5, ground_y - 30.0)

# Clean Floating LaTeX Formula (Euler Style, NO BOX)
draw_latex_glow(c1, eq_chain, 380.0, 240.0, scale=1.35)

snap1 = surface1.makeImageSnapshot()
Image.frombytes("RGBA", (w, h), snap1.tobytes()).save(out_dir / "clean_shot_02A.png")

# -------------------------------------------------------------
# TEST 2: Shot 02B Clean
# -------------------------------------------------------------
surface2 = skia.Surface.MakeRaster(info)
c2 = surface2.getCanvas()
c2.clear(skia.Color4f(0.0, 0.0, 0.0, 1.0))

# Floating Clean Dial on Left (No heavy outer card box)
dial_cx, dial_cy = 400.0, 520.0
dial_rad = 125.0
c2.drawCircle(dial_cx, dial_cy, dial_rad, skia.Paint(Color=skia.Color4f(0.04, 0.07, 0.12, 0.85), AntiAlias=True))
c2.drawCircle(dial_cx, dial_cy, dial_rad, skia.Paint(Color=skia.Color4f(0.20, 0.30, 0.45, 0.50), StrokeWidth=2.0, Style=skia.Paint.kStroke_Style, AntiAlias=True))

# Needle at 5.25%
needle_rad = math.radians(-30.0 + 35.0 - 90.0)
nx = dial_cx + (dial_rad - 20.0) * math.cos(needle_rad)
ny = dial_cy + (dial_rad - 20.0) * math.sin(needle_rad)
c2.drawLine(dial_cx, dial_cy, nx, ny, skia.Paint(Color=skia.Color4f(1.0, 0.85, 0.30, 0.65), StrokeWidth=4.0, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0), AntiAlias=True))
c2.drawLine(dial_cx, dial_cy, nx, ny, skia.Paint(Color=skia.Color4f(1.0, 1.0, 0.95, 1.0), StrokeWidth=2.2, AntiAlias=True))
c2.drawCircle(dial_cx, dial_cy, 7.0, skia.Paint(Color=skia.Color4f(1.0, 1.0, 0.95, 1.0), AntiAlias=True))

# Key Number and Symbolic Badge
tf_serif = skia.Typeface("DejaVu Serif", skia.FontStyle.Bold())
f_num = skia.Font(tf_serif, 46.0)
num_str = "5.25%"
nw = f_num.measureText(num_str)
c2.drawString(num_str, dial_cx - nw * 0.5, dial_cy + 130.0, f_num, skia.Paint(Color=skia.Color4f(1.0, 0.98, 0.92, 1.0), AntiAlias=True))
draw_latex_glow(c2, sym_delta_r, dial_cx, dial_cy + 195.0, scale=1.1)

# Floating Clean Compounding Graph on Right (No heavy card box)
gx0 = 780.0
gy0 = 760.0
gw = 950.0
gh = 450.0

# Coordinate axes with arrowheads
axis_p = skia.Paint(Color=skia.Color4f(0.35, 0.45, 0.60, 0.70), StrokeWidth=1.5, AntiAlias=True)
c2.drawLine(gx0, gy0, gx0 + gw, gy0, axis_p)
c2.drawLine(gx0, gy0, gx0, gy0 - gh, axis_p)
# Arrowheads
c2.drawLine(gx0 + gw, gy0, gx0 + gw - 8.0, gy0 - 5.0, axis_p)
c2.drawLine(gx0 + gw, gy0, gx0 + gw - 8.0, gy0 + 5.0, axis_p)
c2.drawLine(gx0, gy0 - gh, gx0 - 5.0, gy0 - gh + 8.0, axis_p)
c2.drawLine(gx0, gy0 - gh, gx0 + 5.0, gy0 - gh + 8.0, axis_p)

# Axis labels in LaTeX Math
draw_latex_glow(c2, sym_axis_t, gx0 + gw + 24.0, gy0)
draw_latex_glow(c2, sym_axis_B, gx0, gy0 - gh - 24.0)

# Curves & Ribbon
base_pts = []
nudge_pts = []
P = 10000.0
b_max = P * math.pow(1.0525, 30.0)
for step in range(61):
    yr = (step / 60.0) * 30.0
    px = gx0 + (yr / 30.0) * (gw * 0.92)
    py_base = gy0 - (P * math.pow(1.05, yr) / b_max) * (gh * 0.85)
    py_nudge = gy0 - (P * math.pow(1.0525, yr) / b_max) * (gh * 0.85)
    base_pts.append((px, py_base))
    nudge_pts.append((px, py_nudge))

ribbon = skia.Path()
ribbon.moveTo(base_pts[0][0], base_pts[0][1])
for pt in base_pts[1:]: ribbon.lineTo(pt[0], pt[1])
for pt in reversed(nudge_pts): ribbon.lineTo(pt[0], pt[1])
ribbon.close()
c2.drawPath(ribbon, skia.Paint(
    Shader=skia.GradientShader.MakeLinear([(gx0, 0), (gx0 + gw, 0)], [skia.Color4f(0, 0.95, 0.65, 0.05), skia.Color4f(0, 0.95, 0.65, 0.35)], [0, 1]),
    AntiAlias=True
))

path_base = skia.Path()
path_base.moveTo(base_pts[0][0], base_pts[0][1])
for pt in base_pts[1:]: path_base.lineTo(pt[0], pt[1])
c2.drawPath(path_base, skia.Paint(Color=skia.Color4f(0.40, 0.65, 0.80, 0.65), StrokeWidth=2.0, Style=skia.Paint.kStroke_Style, AntiAlias=True))

path_nudge = skia.Path()
path_nudge.moveTo(nudge_pts[0][0], nudge_pts[0][1])
for pt in nudge_pts[1:]: path_nudge.lineTo(pt[0], pt[1])
c2.drawPath(path_nudge, skia.Paint(Color=skia.Color4f(0.20, 1.0, 0.75, 1.0), StrokeWidth=2.4, Style=skia.Paint.kStroke_Style, AntiAlias=True))

# Caliper bracket at Year 30 with symbolic \Delta B
x30 = base_pts[-1][0]
y_base_end = base_pts[-1][1]
y_nudge_end = nudge_pts[-1][1]
c2.drawLine(x30 + 15.0, y_nudge_end, x30 + 15.0, y_base_end, skia.Paint(Color=skia.Color4f(0.0, 0.98, 0.65, 0.90), StrokeWidth=1.5, AntiAlias=True))
c2.drawLine(x30 + 9.0, y_nudge_end, x30 + 21.0, y_nudge_end, skia.Paint(Color=skia.Color4f(0.0, 0.98, 0.65, 0.90), StrokeWidth=1.5, AntiAlias=True))
c2.drawLine(x30 + 9.0, y_base_end, x30 + 21.0, y_base_end, skia.Paint(Color=skia.Color4f(0.0, 0.98, 0.65, 0.90), StrokeWidth=1.5, AntiAlias=True))
draw_latex_glow(c2, sym_delta_b, x30 + 52.0, (y_base_end + y_nudge_end) * 0.5)

# Clean Floating LaTeX Formula (Euler Style)
draw_latex_glow(c2, eq_bank, gx0 + 320.0, gy0 - gh + 50.0, scale=1.35)

snap2 = surface2.makeImageSnapshot()
Image.frombytes("RGBA", (w, h), snap2.tobytes()).save(out_dir / "clean_shot_02B.png")

print("Clean tests rendered successfully!")
