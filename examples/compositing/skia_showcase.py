"""Skia compositing showcase (about 13 seconds).

SkSL background, displacement, dotted/dashed strokes, trim-path orbit, path
booleans, rounded/jittered path effects, screen blending, Typst math written
symbol by symbol, and a perspective-tilted card with an SVG icon.

    python examples/compositing/skia_showcase.py --frame 2 5 9 12 --backend skia
    python examples/compositing/skia_showcase.py --quality medium --backend skia
"""

from faceless_champ import (
    SVG,
    Canvas,
    Circle,
    DisplacementMap,
    Draw,
    EffectStack,
    Equation,
    FadeIn,
    FadeOut,
    Group,
    Line,
    MathGlyphs,
    PathData,
    PopIn,
    Rectangle,
    Scene,
    ShaderFill,
    Text,
    Theme,
    Trace,
    VectorPath,
    run,
)

AURORA = """
uniform float iTime;
uniform float2 iResolution;
uniform half4 deep;
uniform half4 glow;
half4 main(float2 xy) {
    float2 uv = xy / iResolution;
    float wave = sin(uv.x * 6.0 + iTime * 0.6) * 0.08 + sin(uv.x * 13.0 - iTime * 0.9) * 0.03;
    float band = exp(-pow((uv.y - 0.42 - wave) / 0.16, 2.0));
    float vignette = smoothstep(1.1, 0.2, length(uv - 0.5));
    half3 color = mix(deep.rgb, glow.rgb, half(band * 0.45)) * half(vignette);
    return half4(color, 1.0);
}
"""

BOLT = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<path d="M13 2 L4 14 h7 l-1 8 l9 -12 h-7 Z" fill="#FFD166"/></svg>'
)

theme = Theme.named("midnight")


def build():
    with theme.use():
        scene = Scene(Canvas(1920, 1080, bg="#05070D"))
        scene.add(
            ShaderFill(
                AURORA,
                width=1920,
                height=1080,
                position=(960, 540),
                uniforms={"deep": "#05070D", "glow": "#2EC4B6"},
                resolution=0.25,  # a smooth field: shade 1/16 of the pixels, then upscale
            )
        )

        # Beat 1: a title that settles out of turbulence, and a dotted baseline.
        title = Text(
            "Compositing",
            role="display",
            position=(960, 150),
            effects=EffectStack(displacement=DisplacementMap(amplitude=26, size=70, octaves=3, speed=60)),
        )
        axis = Line(1560, stroke="#FFFFFF", stroke_width=5, position=(960, 270), dash=(0, 20), line_cap="round")
        scene.add(title, axis)
        scene.play(
            title.animate.effect_to("displacement", amplitude=0), Draw(axis), run_time=1.8, rate_func="decelerate"
        )

        # Beat 2: screen-blended Venn, a gear cut with path booleans, a trim-path orbit.
        venn = Group(
            Circle(130, fill="#FF4D6D", stroke=None, position=(400, 540)),
            Circle(130, fill="#3A86FF", stroke=None, position=(540, 540), blend="screen"),
            Circle(130, fill="#06D6A0", stroke=None, position=(470, 660), blend="screen"),
        )
        gear = VectorPath(
            PathData.star(0, 0, 105, 72, points=10) - PathData.ellipse(0, 0, 38),
            fill="#FFFFFF",
            stroke=None,
            fill_rule="even_odd",
            round_corners=10,
            position=(1460, 580),
        )
        guide = Circle(200, fill=None, stroke="#FFFFFF", stroke_width=3, position=(1460, 580), dash=(14, 12))
        orbit = Circle(200, fill=None, stroke="#FFD166", stroke_width=10, position=(1460, 580), line_cap="round")
        sketch = Rectangle(
            width=380, height=300, fill=None, stroke="#FFFFFF", stroke_width=3, jitter=(14, 3.5), position=(960, 600)
        )
        scene.reveal(venn, gear, guide, sketch, stagger=0.15)
        scene.wait(0.7)
        scene.add(orbit)
        scene.play(
            Trace(orbit, length=0.22),
            gear.animate.rotate_to(72),
            guide.animate.dash_offset_to(-104),
            run_time=2.6,
            rate_func="linear",
        )
        scene.play(orbit.animate.trim_to(start=0, end=1, offset=0), run_time=0.7)

        # Beat 3: Typst math, written symbol by symbol, inside the sketched box.
        euler = MathGlyphs("e^(i pi) + 1 = 0", font_size=66, position=(960, 560), outline=True)
        euler.glyphs[0].fill = "#FFD166"
        rotation = Equation(
            "R(theta) = mat(cos theta, -sin theta; sin theta, cos theta)",
            engine="typst",
            font_size=48,
            color="#FFFFFF",
            position=(960, 960),
        )
        scene.add(euler)
        scene.play(*[Draw(g) for g in euler.glyphs], run_time=2.2)
        scene.play(FadeIn(rotation), run_time=0.8)

        # Beat 4: a card swings into place in perspective.
        card = Group(
            Rectangle(
                width=420,
                height=260,
                fill="#3A86FF",
                stroke="#FFFFFF",
                stroke_width=4,
                corner_radius=28,
                position=(960, 540),
            ),
            SVG(BOLT, height=120, position=(880, 540)),
            Text("2.5D", role="title", position=(1040, 540)),
            tilt_y=55,
        )
        scene.play(FadeOut(euler), FadeOut(sketch), run_time=0.5)
        scene.add(card)
        scene.play(PopIn(card), run_time=0.6)
        scene.play(
            card.animate.tilt_to(y=-18),
            run_time=2.2,
            rate_func="emphasized",
        )
        scene.wait(1.2)
        return scene


scene = build()
if __name__ == "__main__":
    run(build)
