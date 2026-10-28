import math
from pathlib import Path
from PIL import Image
import skia

def get_typeface(path: Path, weight: float = 400.0) -> skia.Typeface:
    base = skia.Typeface.MakeFromFile(str(path))
    if base is None:
        return skia.Typeface("sans-serif")
    tag_wght = int.from_bytes(b'wght', 'big')
    coords = skia.FontArguments.VariationPosition.Coordinates()
    coords.append(skia.FontArguments.VariationPosition.Coordinate(tag_wght, float(weight)))
    pos = skia.FontArguments.VariationPosition(coords)
    args = skia.FontArguments()
    args.setVariationDesignPosition(pos)
    clone = base.makeClone(args)
    return clone if clone is not None else base

def draw_letterspaced_text(canvas, text, cx, y, font, paint, letter_spacing=4.0):
    total_w = 0.0
    advances = []
    for char in text:
        w = font.measureText(char)
        advances.append(w)
        total_w += w + letter_spacing
    total_w -= letter_spacing
    
    cur_x = cx - total_w * 0.5
    for i, char in enumerate(text):
        canvas.drawString(char, cur_x, y, font, paint)
        cur_x += advances[i] + letter_spacing

def generate_variants():
    assets_dir = Path("assets/fonts")
    cg_path = assets_dir / "CormorantGaramond[wght].ttf"
    dm_path = assets_dir / "DMSans[opsz,wght].ttf"
    sg_path = assets_dir / "SpaceGrotesk[wght].ttf"
    
    # 3 Typeface variations:
    # 1: Cormorant Garamond Bold 700 + Space Grotesk Bold
    tf_cg_700 = get_typeface(cg_path, 700.0)
    tf_sg_700 = get_typeface(sg_path, 700.0)
    tf_dm_700 = get_typeface(dm_path, 700.0)
    
    out_dir = Path("my-project/chain/output/title_experiments")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    w, h = 1920, 1080
    
    # VARIANT A: Royal Cinematic Gold & Electric Cyan (Cormorant Garamond 700)
    info = skia.ImageInfo.Make(w, h, skia.ColorType.kRGBA_8888_ColorType, skia.AlphaType.kPremul_AlphaType)
    surface = skia.Surface.MakeRaster(info)
    canvas = surface.getCanvas()
    canvas.clear(skia.Color4f(0.0, 0.0, 0.0, 1.0))
    
    # Subtle deep atmospheric focal bloom
    nebula = skia.Paint(
        Shader=skia.GradientShader.MakeRadial(
            (960.0, 520.0),
            560.0,
            [
                skia.Color4f(0.98, 0.70, 0.10, 0.18),
                skia.Color4f(0.05, 0.40, 0.85, 0.08),
                skia.Color4f(0.0, 0.0, 0.0, 0.0),
            ],
            [0.0, 0.45, 1.0],
        )
    )
    canvas.drawCircle(960.0, 520.0, 560.0, nebula)
    
    # Chapter Tag / Kicker
    tag_font = skia.Font(tf_sg_700, 15.0)
    tag_paint = skia.Paint(Color=skia.Color4f(0.98, 0.76, 0.18, 0.95), AntiAlias=True)
    draw_letterspaced_text(canvas, "CHAPTER 01  //  THE ARCHITECTURE OF LEARNING", 960.0, 440.0, tag_font, tag_paint, letter_spacing=5.0)
    
    # Main Title: Cormorant Garamond 700 at 96px
    title_font = skia.Font(tf_cg_700, 96.0)
    title_text = "The Chain Rule"
    t_w = title_font.measureText(title_text)
    t_x = (w - t_w) * 0.5
    t_y = 535.0
    
    # Ambient glow pass
    p_glow_wide = skia.Paint(
        Color=skia.Color4f(1.0, 0.65, 0.05, 0.35),
        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 20.0),
        AntiAlias=True
    )
    canvas.drawString(title_text, t_x, t_y, title_font, p_glow_wide)
    
    # Sharp laser glow pass
    p_glow_tight = skia.Paint(
        Color=skia.Color4f(1.0, 0.84, 0.25, 0.65),
        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.5),
        AntiAlias=True
    )
    canvas.drawString(title_text, t_x, t_y, title_font, p_glow_tight)
    
    # Crisp core text: Pure sharp warm white with brilliant specular punch
    p_core = skia.Paint(
        Color=skia.Color4f(1.0, 0.98, 0.94, 1.0),
        AntiAlias=True
    )
    canvas.drawString(title_text, t_x, t_y, title_font, p_core)
    
    # Precision golden hairline divider with diamond center
    div_w = 320.0
    p_div = skia.Paint(
        Color=skia.Color4f(0.98, 0.78, 0.20, 0.85),
        StrokeWidth=1.5,
        AntiAlias=True
    )
    canvas.drawLine(960.0 - div_w * 0.5, 570.0, 960.0 - 18.0, 570.0, p_div)
    canvas.drawLine(960.0 + 18.0, 570.0, 960.0 + div_w * 0.5, 570.0, p_div)
    # Diamond glyph
    dia_path = skia.Path()
    dia_path.moveTo(960.0, 565.0)
    dia_path.lineTo(965.0, 570.0)
    dia_path.lineTo(960.0, 575.0)
    dia_path.lineTo(955.0, 570.0)
    dia_path.close()
    p_dia = skia.Paint(Color=skia.Color4f(1.0, 0.88, 0.35, 0.95), AntiAlias=True)
    canvas.drawPath(dia_path, p_dia)
    
    # Subtext: Sharp High-Contrast Ice Cyan / Platinum
    sub_font = skia.Font(tf_sg_700, 18.0)
    sub_paint = skia.Paint(Color=skia.Color4f(0.35, 0.88, 1.0, 0.95), AntiAlias=True)
    draw_letterspaced_text(canvas, "THE MATHEMATICAL ENGINE OF ARTIFICIAL INTELLIGENCE", 960.0, 615.0, sub_font, sub_paint, letter_spacing=4.0)
    
    snap = surface.makeImageSnapshot()
    Image.frombytes("RGBA", (w, h), snap.tobytes()).save(out_dir / "variant_A_serif_gold_cyan.png")
    
    # VARIANT B: Ultra-modern Geometric Sans (Space Grotesk 700) with Hyper-Neon Gold & White
    surface2 = skia.Surface.MakeRaster(info)
    canvas2 = surface2.getCanvas()
    canvas2.clear(skia.Color4f(0.0, 0.0, 0.0, 1.0))
    canvas2.drawCircle(960.0, 520.0, 560.0, nebula)
    
    draw_letterspaced_text(canvas2, "CHAPTER 01  ·  THE ARCHITECTURE OF LEARNING", 960.0, 440.0, tag_font, tag_paint, letter_spacing=5.0)
    
    title_font_sg = skia.Font(tf_sg_700, 88.0)
    title_text_caps = "THE CHAIN RULE"
    t_w2 = title_font_sg.measureText(title_text_caps)
    t_x2 = (w - t_w2) * 0.5
    t_y2 = 538.0
    
    canvas2.drawString(title_text_caps, t_x2, t_y2, title_font_sg, p_glow_wide)
    canvas2.drawString(title_text_caps, t_x2, t_y2, title_font_sg, p_glow_tight)
    canvas2.drawString(title_text_caps, t_x2, t_y2, title_font_sg, p_core)
    
    canvas2.drawLine(960.0 - div_w * 0.5, 570.0, 960.0 - 18.0, 570.0, p_div)
    canvas2.drawLine(960.0 + 18.0, 570.0, 960.0 + div_w * 0.5, 570.0, p_div)
    canvas2.drawPath(dia_path, p_dia)
    
    draw_letterspaced_text(canvas2, "THE MATHEMATICAL ENGINE OF ARTIFICIAL INTELLIGENCE", 960.0, 615.0, sub_font, sub_paint, letter_spacing=4.0)
    
    snap2 = surface2.makeImageSnapshot()
    Image.frombytes("RGBA", (w, h), snap2.tobytes()).save(out_dir / "variant_B_sans_gold_cyan.png")
    
    # VARIANT D: Master Cinematic Edition (Chiseled Serif + Anamorphic Streak + Dual Tone)
    surface4 = skia.Surface.MakeRaster(info)
    canvas4 = surface4.getCanvas()
    canvas4.clear(skia.Color4f(0.0, 0.0, 0.0, 1.0))
    
    # 1. Subtle central ambient focal illumination
    nebula_master = skia.Paint(
        Shader=skia.GradientShader.MakeRadial(
            (960.0, 520.0),
            600.0,
            [
                skia.Color4f(0.98, 0.72, 0.12, 0.22),
                skia.Color4f(0.0, 0.85, 1.0, 0.06),
                skia.Color4f(0.0, 0.0, 0.0, 0.0),
            ],
            [0.0, 0.40, 1.0],
        )
    )
    canvas4.drawCircle(960.0, 520.0, 600.0, nebula_master)
    
    # 2. Horizontal anamorphic laser streak across center
    streak_p = skia.Paint(
        Shader=skia.GradientShader.MakeLinear(
            [(960.0 - 500.0, 525.0), (960.0 + 500.0, 525.0)],
            [
                skia.Color4f(1.0, 0.80, 0.20, 0.0),
                skia.Color4f(1.0, 0.85, 0.30, 0.45),
                skia.Color4f(1.0, 0.80, 0.20, 0.0),
            ],
            [0.0, 0.5, 1.0]
        ),
        StrokeWidth=1.0,
        AntiAlias=True
    )
    canvas4.drawLine(960.0 - 500.0, 525.0, 960.0 + 500.0, 525.0, streak_p)
    
    # 3. Chapter Kicker Badge: CHAPTER 01  ·  THE ARCHITECTURE
    kicker_font = skia.Font(tf_sg_700, 14.0)
    kicker_p = skia.Paint(Color=skia.Color4f(0.98, 0.78, 0.20, 0.95), AntiAlias=True)
    draw_letterspaced_text(canvas4, "CHAPTER 01  //  THE ARCHITECTURE", 960.0, 435.0, kicker_font, kicker_p, letter_spacing=5.5)
    
    # 4. Main Title: Cormorant Garamond 700 at 100px
    title_font_master = skia.Font(tf_cg_700, 100.0)
    title_text = "The Chain Rule"
    t_w = title_font_master.measureText(title_text)
    t_x = (w - t_w) * 0.5
    t_y = 528.0
    
    # Wide atmospheric amber bloom
    p_glow_wide = skia.Paint(
        Color=skia.Color4f(1.0, 0.68, 0.08, 0.40),
        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 24.0),
        AntiAlias=True
    )
    canvas4.drawString(title_text, t_x, t_y, title_font_master, p_glow_wide)
    
    # Tight razor-sharp laser aura
    p_glow_tight = skia.Paint(
        Color=skia.Color4f(1.0, 0.86, 0.30, 0.85),
        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4.0),
        AntiAlias=True
    )
    canvas4.drawString(title_text, t_x, t_y, title_font_master, p_glow_tight)
    
    # Pure white crystalline foreground with specular intensity
    p_core = skia.Paint(
        Color=skia.Color4f(1.0, 0.99, 0.97, 1.0),
        AntiAlias=True
    )
    canvas4.drawString(title_text, t_x, t_y, title_font_master, p_core)
    
    # 5. Golden Hairline Geometry Divider
    div_len = 340.0
    p_div = skia.Paint(
        Color=skia.Color4f(0.98, 0.80, 0.25, 0.90),
        StrokeWidth=1.4,
        AntiAlias=True
    )
    canvas4.drawLine(960.0 - div_len * 0.5, 565.0, 960.0 - 18.0, 565.0, p_div)
    canvas4.drawLine(960.0 + 18.0, 565.0, 960.0 + div_len * 0.5, 565.0, p_div)
    
    # Precision diamond emblem at center
    dia = skia.Path()
    dia.moveTo(960.0, 560.0)
    dia.lineTo(965.0, 565.0)
    dia.lineTo(960.0, 570.0)
    dia.lineTo(955.0, 565.0)
    dia.close()
    p_dia = skia.Paint(Color=skia.Color4f(1.0, 0.90, 0.40, 1.0), AntiAlias=True)
    canvas4.drawPath(dia, p_dia)
    
    # Corner ticks on divider
    canvas4.drawLine(960.0 - div_len * 0.5, 562.0, 960.0 - div_len * 0.5, 568.0, p_div)
    canvas4.drawLine(960.0 + div_len * 0.5, 562.0, 960.0 + div_len * 0.5, 568.0, p_div)
    
    # 6. Subtext: Crisp, high-contrast, razor-sharp Cyan / Platinum
    sub_font_m = skia.Font(tf_sg_700, 18.0)
    sub_paint_m = skia.Paint(
        Color=skia.Color4f(0.20, 0.92, 1.0, 1.0),
        AntiAlias=True
    )
    # Subtle tight glow on subtext to make it electric and sharp
    sub_glow_p = skia.Paint(
        Color=skia.Color4f(0.0, 0.80, 1.0, 0.50),
        MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.0),
        AntiAlias=True
    )
    draw_letterspaced_text(canvas4, "THE MATHEMATICAL ENGINE OF ARTIFICIAL INTELLIGENCE", 960.0, 612.0, sub_font_m, sub_glow_p, letter_spacing=4.5)
    draw_letterspaced_text(canvas4, "THE MATHEMATICAL ENGINE OF ARTIFICIAL INTELLIGENCE", 960.0, 612.0, sub_font_m, sub_paint_m, letter_spacing=4.5)
    
    snap4 = surface4.makeImageSnapshot()
    Image.frombytes("RGBA", (w, h), snap4.tobytes()).save(out_dir / "variant_D_master_cinematic.png")

if __name__ == "__main__":
    generate_variants()
    print("Done generating title variants!")
