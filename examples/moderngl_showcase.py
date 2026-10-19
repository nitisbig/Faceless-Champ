"""A bounded cinematic GPU reference. Use --backend auto for faithful CPU fallback."""

import argparse
from pathlib import Path

from faceless_champ import (
    Bloom,
    Bounds,
    Canvas,
    Circle,
    EffectStack,
    GradientStop,
    LinearGradient,
    OuterGlow,
    ParticleField,
    ProceduralBackground,
    Rectangle,
    Scene,
    ShadowStyle,
    Text,
    card_surface,
    create_renderer,
    linear,
    render,
)
from faceless_champ.typography import CLEAN_FLOW_FONT


def build():
    scene = Scene(Canvas(1920, 1080, "#080D1A"))
    scene.add(ProceduralBackground(width=1920, height=1080, position=(960, 540), color="#214678", seed=17, speed=0.35))
    scene.add(
        ParticleField(
            width=1920, height=1080, position=(960, 540), color="#9DDFFF", seed=17, count=160, radius=1.5, opacity=0.4
        )
    )

    def text(value, position, size=32, color="#F2F7FF", **options):
        return Text(value, font=CLEAN_FLOW_FONT, font_size=size, position=position, color=color, **options)

    scene.add(text("FACELESS CHAMP  /  GPU STUDIO", (960, 96), 24, "#8CB8E4"))
    scene.add(text("Make every frame feel considered.", (960, 165), 60))
    panel = card_surface(
        Bounds(250, 240, 1670, 920),
        radius=38,
        fill=LinearGradient((GradientStop(0, "#253B57F0"), GradientStop(1, "#101B32F0")), angle=35),
        shadow=ShadowStyle(color="#00000088", blur=10, offset=(0, 12)),
        render_mode="vector",
    )
    scene.add(panel)
    scene.add(text("Light. Motion. Detail.", (670, 376), 42))
    scene.add(text("One deterministic timeline.", (670, 440), 29, "#A5BAD1"))
    labels = ("GPU composition", "Linear-light bloom", "Seeded particles")
    for i, label in enumerate(labels):
        y = 560 + i * 80
        scene.add(
            Rectangle(width=470, height=60, corner_radius=15, fill="#BDDFFF0D", stroke="#C4E6FF22", position=(670, y))
        )
        scene.add(Circle(5, fill="#A1DFFF", stroke=None, position=(475, y)))
        scene.add(text(label, (690, y), 27, "#DCEEFF"))
    orb = Circle(
        108,
        fill="#A8E6FF",
        stroke="#E9FAFF",
        stroke_width=2,
        position=(1260, 555),
        effects=EffectStack(glow=OuterGlow("#54AEFF", 28, 0.7), bloom=Bloom(18, 0.4, 0.8)),
    )
    ring = Circle(145, fill=None, stroke="#A2D8FF70", stroke_width=1.5, position=(1260, 555))
    scene.add(orb, ring, text("1080p  /  4K", (1260, 766), 25, "#A5BAD1"))
    scene.add(text("OPTIONAL MODERNGL BACKEND", (960, 979), 20, "#90ADC9"))
    with scene.at(0):
        scene.play(orb.animate.move_to(1260, 535), run_time=4, rate_func=linear)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/moderngl/showcase.mp4"))
    parser.add_argument("--backend", choices=["moderngl", "auto", "skia", "pillow"], default="moderngl")
    parser.add_argument("--quality", choices=["1080p", "4k"], default="1080p")
    parser.add_argument("--frame", action="store_true")
    parser.add_argument("--seconds", type=float, default=4)
    parser.add_argument("--fps", type=float, default=30)
    args = parser.parse_args()
    scene = build()
    with create_renderer(args.backend, antialias=1) as renderer:
        if args.frame:
            size = (3840, 2160) if args.quality == "4k" else (1920, 1080)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            renderer.frame(scene, 1.5, size).save(args.output.with_suffix(".png"))
        else:
            render(
                scene,
                args.output,
                renderer=renderer,
                quality=args.quality,
                antialias=1,
                fps=args.fps,
                end_time=min(scene.duration, args.seconds),
                overwrite=True,
            )
        print(getattr(renderer, "identity", {"backend": args.backend}))


if __name__ == "__main__":
    main()
