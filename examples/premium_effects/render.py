"""Six-second offline gradient/shadow showcase. Defaults to a 960x540 preview."""

from __future__ import annotations

import argparse
from pathlib import Path

from faceless_champ import (
    Bounds,
    Canvas,
    GradientStop,
    Group,
    LinearGradient,
    PillowRenderer,
    RadialGradient,
    Rectangle,
    Scene,
    ShadowStyle,
    Spring,
    StoryboardSample,
    Text,
    card_surface,
    render_storyboard,
    save_frame,
    smooth,
)

TIMES = (0, 0.4, 0.9, 1.8, 3.5, 5.9)


def comparison(animate=True):
    """Three paint types, two lighting schemes; only transforms/opacity animate."""
    scene = Scene(Canvas(960, 540, "#EFF2F7"))
    scene.add(Rectangle(width=960, height=270, fill="#111827", stroke=None, stroke_width=0, position=(480, 405)))
    groups = []
    for row in range(2):
        dark = bool(row)
        text = "#F2F6FF" if dark else "#182B49"
        muted = "#94A5C2" if dark else "#62718A"
        colors = ("#17213B", "#3647A0", "#62DDDB") if dark else ("#FFFFFF", "#DCE8FF", "#99B6F2")
        stops = tuple(GradientStop(offset, color) for offset, color in zip((0, 0.55, 1), colors))
        radial_colors = ("#627BD1", "#2D406D", "#17243E") if dark else ("#FFFFFF", "#CBDDFB", "#8FAEEB")
        radial = RadialGradient(
            tuple(GradientStop(offset, color) for offset, color in zip((0, 0.55, 1), radial_colors)),
            center=(0.28, 0.24),
            radius=1.1,
        )
        fills = ("#253852" if dark else "#FFFFFF", LinearGradient(stops, angle=125), radial)
        shadow = ShadowStyle(color="#000000A8" if dark else "#304C7138", blur=7, offset=(0, 6))
        with scene.at(0):
            scene.add(
                Text(
                    "DARK  /  GRADIENTS + LOCAL SHADOWS" if dark else "LIGHT  /  SOLID, LINEAR, RADIAL",
                    position=(480, 290 if dark else 25),
                    font_size=13,
                    color=muted,
                )
            )
        for column, (name, fill, detail) in enumerate(
            zip(
                ("Flat", "Linear", "Radial"),
                fills,
                ("String fill", "3 stops / 125 degrees", "Offset center / circular paint"),
            )
        ):
            x, y = 180 + column * 300, 414 if dark else 154
            surface = card_surface(Bounds(x - 150, y - 100, x + 150, y + 100), fill=fill, radius=26, shadow=shadow)
            word = Text(name, position=(x, y), font_size=28, color=text)
            label = Text(detail, position=(x, y + 93), font_size=12, color=muted)
            group = Group(
                surface,
                word,
                position=(x, y + 18) if animate else (x, y),
                scale=0.94 if animate else 1,
                opacity=0 if animate else 1,
            )
            with scene.at(0):
                scene.add(group, label)
            groups.append(group)
            if animate:
                start = 0.12 + column * 0.12 + row * 0.12
                with scene.at(start):
                    scene.play(group.animate.move_to(x, y).scale_to(1), run_time=1.4, rate_func=Spring(100, 20, 1))
                with scene.at(start):
                    scene.play(group.animate.opacity_to(1), run_time=0.35, rate_func=smooth)
    if animate:
        for group in (groups[1], groups[5]):
            with scene.at(3):
                scene.play(group.animate.rotate_to(4).scale_to(1.03), run_time=0.9, rate_func=Spring(100, 20, 1))
            with scene.at(4.5):
                scene.play(group.animate.rotate_to(0).scale_to(1), run_time=0.9, rate_func=Spring(100, 20, 1))
    scene.wait_until(6)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/premium_effects/phase2a/preview.mp4"))
    parser.add_argument("--fps", type=int, choices=(24, 30, 60), default=30)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=540)
    parser.add_argument("--antialias", type=int, choices=(1, 2, 3, 4), default=1)
    parser.add_argument("--frames", action="store_true")
    parser.add_argument("--stills-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    movie = comparison()
    directory = args.output.parent
    with PillowRenderer(args.antialias) as renderer:
        save_frame(
            comparison(False),
            2,
            directory / "comparison.png",
            size=(args.width, args.height),
            renderer=renderer,
            overwrite=args.overwrite,
        )
        if args.frames or args.stills_only:
            samples = tuple(StoryboardSample(t, f"t={t:.2f}s") for t in TIMES)
            sheet = render_storyboard(
                movie, samples, directory / "storyboard", size=(960, 540), renderer=renderer, overwrite=args.overwrite
            )
            print(f"Storyboard: {sheet}")
        if not args.stills_only:
            path = movie.render(
                args.output,
                width=args.width,
                height=args.height,
                fps=args.fps,
                antialias=args.antialias,
                renderer=renderer,
                crf=18,
                preset="fast",
                overwrite=args.overwrite,
            )
            print(f"Preview: {path}")
    print(f"Comparison: {directory / 'comparison.png'}")


if __name__ == "__main__":
    main()
