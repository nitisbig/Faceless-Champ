"""Premium native-vector reference; four-second preview by default.

Run: python examples/skia_showcase.py --output output/skia/preview.mp4
     python examples/skia_showcase.py --frame --quality 4k
The portable scene uses the same APIs with --backend pillow.
"""

import argparse
from pathlib import Path

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Bounds,
    Canvas,
    Circle,
    CircleMask,
    ExportProgress,
    ExportSettings,
    FadeIn,
    GradientStop,
    Group,
    Line,
    LinearGradient,
    PathData,
    Scene,
    ShadowStyle,
    Text,
    VectorPath,
    Wipe,
    card_surface,
    create_renderer,
    render,
    save_frame,
)


def showcase(backend="skia"):
    native = backend == "skia"
    engine = "skia" if native else "pillow"
    mode = "vector" if native else "raster"
    scene = Scene(Canvas(1920, 1080, "#F4F5F9"))

    def label(value, x, y, size=24, color="#151822", weight=400):
        return Text(
            value,
            font=CLEAN_FLOW_FONT,
            font_size=size,
            font_weight=weight,
            color=color,
            anchor="top_left",
            position=(x, y),
            text_engine=engine,
        )

    title = label("Precision, in motion.", 98, 110, 88, weight=700)
    scene.add(label("FACELESS CHAMP  /  NATIVE GRAPHICS", 104, 58, 20, "#637087", 500))
    scene.play(FadeIn(title), run_time=0.45)
    scene.add(label("Fluid curves, considered typography, and light with depth.", 104, 235, 28, "#657087"))
    shadow = ShadowStyle("#25315220", 10, (0, 9))
    cards = [
        card_surface(Bounds(*box), fill="white", radius=32, shadow=shadow, render_mode=mode)
        for box in ((70, 305, 1208, 996), (1176, 305, 1854, 659), (1176, 622, 1854, 996))
    ]
    scene.play(*(FadeIn(c) for c in cards), run_time=0.45)
    scene.add(
        label("EVERY CURVE. EVERY PIXEL.", 148, 379, 18, "#77829A", 500),
        label("Beautiful at any scale.", 145, 418, 48, weight=700),
        label("Bézier geometry with clean, deliberate edges.", 148, 490, 25, "#6C7689"),
    )
    for y in (600, 680, 760, 840):
        scene.add(Line(968, position=(637, y), stroke="#EDF0F6", stroke_width=1))
    path = (
        PathData()
        .move_to(153, 816)
        .cubic_to(280, 815, 280, 674, 412, 706)
        .cubic_to(530, 735, 570, 790, 675, 701)
        .cubic_to(765, 620, 836, 677, 903, 624)
        .cubic_to(988, 565, 1048, 622, 1122, 572)
    )
    area = path.line_to(1122, 864).line_to(153, 864).close()
    curve = VectorPath(path, stroke="#347EEF", stroke_width=5)
    area_fill = LinearGradient((GradientStop(0, "#6B91F500"), GradientStop(1, "#527DF540")), angle=270)
    chart = Group(VectorPath(area, fill=area_fill, stroke=None), curve)
    scene.add(
        *(
            label(value, x, 892, 18, "#8490A4")
            for x, value in ((153, "Geometry"), (466, "Motion"), (780, "Compositing"), (1037, "Detail"))
        )
    )
    scene.add(
        label("Light, softly layered.", 1248, 377, 27, weight=500),
        label("Gradients · masks · transparency", 1248, 419, 19, "#7C879B"),
    )
    wash = card_surface(
        Bounds(1248, 465, 1548, 579),
        fill=LinearGradient(
            (GradientStop(0, "#4056DA"), GradientStop(0.53, "#8B7FEF"), GradientStop(1, "#A6DFED")), angle=30
        ),
        render_mode=mode,
        radius=22,
    )
    circles = Group(
        Circle(50, fill="#FFFFFF33", stroke=None, position=(1435, 510)),
        Circle(44, fill="#FFFFFF29", stroke=None, position=(1360, 553)),
        mask=CircleMask(65, position=(12, 0)),
    )
    scene.add(
        wash,
        circles,
        Circle(54, fill=None, stroke="#7381E3", stroke_width=8, position=(1679, 514)),
        label("92", 1648, 482, 38, weight=700),
        label("Type with intention.", 1248, 688, 27, weight=500),
        label("Aa", 1242, 740, 101, weight=700),
        label("DM Sans", 1457, 782, 28, weight=500),
        label("400 / 500 / 700", 1459, 827, 19, "#7C879B"),
        label("AVATAR  office  0123456789", 1248, 905, 19, "#7C879B"),
    )
    scene.add(
        label("NATIVE SKIA CPU RASTER" if native else "PILLOW PORTABLE REFERENCE", 104, 1010, 17, "#7B879B", 500),
        label("Core → Kit → Agent / shared animation timeline", 1205, 1010, 17, "#7B879B"),
    )
    scene.play(Wipe(chart), run_time=2.2)
    scene.wait(0.9)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("pillow", "skia"), default="skia")
    parser.add_argument("--quality", choices=("1080p", "4k"), default="1080p")
    parser.add_argument("--frame", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    scene = showcase(args.backend)
    settings = ExportSettings(backend=args.backend, antialias=1, fps=24, quality=args.quality)
    output = args.output or Path("output/skia") / (f"frame-{args.quality}.png" if args.frame else "preview.mp4")
    if args.frame:
        with create_renderer(args.backend, antialias=1) as renderer:
            save_frame(
                scene, 3.5, output, size=settings.dimensions(scene.canvas), renderer=renderer, overwrite=args.overwrite
            )
    else:
        with ExportProgress() as progress:
            render(scene, output, settings=settings, end_time=4, overwrite=args.overwrite, progress=progress)
    print(output)


if __name__ == "__main__":
    main()
