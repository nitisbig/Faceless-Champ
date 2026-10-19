"""45-second native Skia typography film. No Docker, external assets or audio."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Animation,
    Canvas,
    Circle,
    ExportProgress,
    ExportSettings,
    Group,
    Rectangle,
    RectangleMask,
    Scene,
    Text,
    create_renderer,
    ease_out,
    linear,
    render,
    rendering_identity,
    save_frame,
    smooth,
)

ROOT = Path(__file__).resolve().parent
DURATION = 45.0
INK, PAPER, LIME, PURPLE = "#101014", "#F1EDE5", "#D2FF5A", "#AA95FF"


def type_(word, size=240, position=(960, 540), color=PAPER):
    return Text(
        word, font=CLEAN_FLOW_FONT, font_size=size, font_weight=900, text_engine="skia", color=color, position=position
    )


def track(scene, obj, prop, values, start, end, easing=smooth):
    values = tuple(values)
    with scene.at(start):
        scene.play(
            Animation(
                obj,
                {prop: values[-1]},
                starts={prop: values[0]},
                keyframes={prop: tuple((i / (len(values) - 1), v) for i, v in enumerate(values))},
                rate_func=easing,
            ),
            run_time=end - start,
        )


def show(scene, obj, start, end, fade=0.18):
    with scene.at(start):
        scene.add(obj)
    track(scene, obj, "opacity", (0, 1), start, start + fade)
    track(scene, obj, "opacity", (1, 0), end - fade, end)


def letters(word, size, gap, y=540, color=PAPER):
    """Measured glyph advances keep individual animated letters optically spaced."""
    glyphs = [type_(c, size, color=color) for c in word]
    widths = [g.bounds.width for g in glyphs]
    x = 960 - (sum(widths) + gap * (len(word) - 1)) / 2
    for glyph, width in zip(glyphs, widths):
        glyph.move_to(x + width / 2, y)
        x += width + gap
    return glyphs


def build_scene():
    scene = Scene(Canvas(1920, 1080, INK))

    # 00–08: individual glyphs drop, overshoot, settle, then fly apart.
    glyphs = letters("MOVE", 350, 16)
    for i, glyph in enumerate(glyphs):
        x, y = glyph.position
        start = 0.3 + i * 0.22
        show(scene, glyph, start, 7.9)
        track(scene, glyph, "position", ((x, 1120), (x, 505), (x, y)), start, start + 1.2, ease_out)
        track(scene, glyph, "rotation", (-16 + i * 8, 0), start, start + 1.3)
        track(scene, glyph, "position", ((x, y), (x, y - 35), (x, y)), 2.7 + i * 0.13, 5 + i * 0.13)
        track(scene, glyph, "position", ((x, y), (x + (i - 1.5) * 220, -330)), 6.8 + i * 0.08, 7.9)
    rule = Rectangle(width=1100, height=9, fill=LIME, stroke=None, position=(960, 760))
    show(scene, rule, 1.3, 7.5)
    track(scene, rule, "scale_x", (0.001, 1, 0.35), 1.3, 7.4)

    # 08–15: deliberately different sizes; BIG grows as a complete phrase.
    make = type_("MAKE", 125, (720, 325))
    it = type_("IT", 125, (1190, 325), PURPLE)
    big = type_("BIG", 440, (960, 640), LIME)
    for i, obj in enumerate((make, it, big)):
        show(scene, obj, 7.9 + i * 0.2, 15.1)
        track(scene, obj, "scale", (0.2, 1.05, 1), 7.9 + i * 0.2, 9.6 + i * 0.2, ease_out)
    track(scene, big, "scale", (1, 0.7, 1.16, 1), 10.1, 13.6)
    track(scene, big, "scale_x", (1, 1.18, 0.85, 1), 10.1, 13.6)
    for obj in (make, it, big):
        x, y = obj.position
        track(scene, obj, "position", ((x, y), (x - 2100, y)), 14.15, 15.1)

    # 15–23: three real subtree masks reconstruct a single word in sliding slices.
    for i in range(3):
        word = type_("THROUGH", 285, (960, 540), LIME if i == 1 else PAPER)
        # The mask remains fixed while its child travels through the aperture.
        window = Group(word, mask=RectangleMask(1700, 105, position=(0, (i - 1) * 105)))
        show(scene, window, 14.9, 23.0)
        direction = 1 if i % 2 else -1
        track(
            scene,
            word,
            "position",
            ((960 + direction * 1850, 540), (960, 540)),
            15.1 + i * 0.22,
            17.0 + i * 0.22,
            ease_out,
        )
        track(scene, word, "position", ((960, 540), (960 - direction * 65, 540), (960, 540)), 18.3, 20.9)
        track(scene, window, "mask_height", (105, 1), 21.6 + i * 0.12, 22.9)
    for y in (379, 701):
        edge = Rectangle(width=1540, height=3, position=(960, y), fill=PURPLE, stroke=None)
        show(scene, edge, 15.2, 22.8)
        track(scene, edge, "scale_x", (0.001, 1, 0.001), 15.2, 22.8)

    # 23–31: large type replaces itself through a shared rectangular aperture.
    for i, (word, color) in enumerate((("STAY", PAPER), ("IN", PURPLE), ("MOTION", LIME))):
        start = 22.8 + i * 2.45
        obj = type_(word, 300 if i != 1 else 380, color=color)
        window = Group(obj, mask=RectangleMask(1780, 400))
        show(scene, window, start, start + 2.65, 0.08)
        track(scene, obj, "position", ((960, 1060), (960, 540)), start, start + 0.85, ease_out)
        track(scene, obj, "scale", (0.9, 1.04), start + 0.85, start + 1.9)
        track(scene, obj, "position", ((960, 540), (960, 40)), start + 1.95, start + 2.65)

    # 31–38: per-letter traveling wave, spacing and size choreography.
    glyphs = letters("FLOW", 340, 28, color=PURPLE)
    for i, glyph in enumerate(glyphs):
        x, y = glyph.position
        show(scene, glyph, 30.6 + i * 0.12, 38.2)
        track(scene, glyph, "scale", (0.01, 1.1, 1), 30.6 + i * 0.12, 32.0 + i * 0.12, ease_out)
        samples = [j / 64 for j in range(65)]
        track(
            scene,
            glyph,
            "position",
            [(x + 35 * math.sin(t * math.tau), y + 95 * math.sin(t * math.tau * 2 - i * 0.7)) for t in samples],
            32.2,
            37,
            linear,
        )
        track(
            scene,
            glyph,
            "scale_y",
            [1 + 0.16 * math.sin(t * math.tau * 2 - i * 0.7) for t in samples],
            32.2,
            37,
            linear,
        )
        track(scene, glyph, "rotation", (0, -10 if i % 2 else 10), 37.1, 38.2)
        track(scene, glyph, "scale", (1, 0.01), 37.1 + i * 0.08, 38.2)

    # 38–45: a circular reveal, tight tracking, then a clean closing shutter.
    disk = Circle(35, fill=LIME, stroke=None, position=(960, 540))
    show(scene, disk, 38, 44.6, 0.1)
    track(scene, disk, "scale", (0.01, 35), 38, 39.25, ease_out)
    glyphs = letters("AGAIN", 275, 10, color=INK)
    for i, glyph in enumerate(glyphs):
        x, y = glyph.position
        show(scene, glyph, 38.8 + i * 0.10, 44.2)
        track(
            scene,
            glyph,
            "position",
            ((960 + (x - 960) * 1.8, y + 180), (x, y)),
            38.8 + i * 0.1,
            40.4 + i * 0.1,
            ease_out,
        )
        track(scene, glyph, "scale_y", (0.05, 1), 38.8 + i * 0.1, 40.4 + i * 0.1)
        track(scene, glyph, "position", ((x, y), (960 + (x - 960) * 0.92, y)), 41, 43.1)
    for y, final in ((-270, 270), (1350, 810)):
        shutter = Rectangle(width=1920, height=540, fill=INK, stroke=None, position=(960, y))
        with scene.at(43.35):
            scene.add(shutter)
        track(scene, shutter, "position", ((960, y), (960, final)), 43.35, 44.65)
    scene.wait_until(DURATION)
    return scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--frame", type=float)
    mode.add_argument("--preview", action="store_true", help="Two seconds of masked type, source time 15–17")
    mode.add_argument("--range", type=float, nargs=2, metavar=("START", "END"))
    parser.add_argument("--quality", choices=("720p", "1080p", "4k"), default="1080p")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame < DURATION:
        parser.error("frame must be in [0, 45)")
    if args.range and not 0 <= args.range[0] < args.range[1] <= DURATION:
        parser.error("range must satisfy 0 <= START < END <= 45")
    scene = build_scene()
    assert scene.duration == DURATION
    settings = ExportSettings(backend="skia", antialias=1, quality=args.quality, fps=args.fps)
    output = args.output or ROOT / "output" / (
        f"frame-{args.frame:g}.png" if args.frame is not None else "preview.mp4" if args.preview else "skia-kinetic.mp4"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    source_range = args.range or ([15, 17] if args.preview else [0, DURATION])
    if args.frame is not None:
        source_range = [args.frame, args.frame]
        with create_renderer("skia", antialias=1) as renderer:
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
                overwrite=args.overwrite,
                progress=progress,
            )
    output.with_suffix(".json").write_text(
        json.dumps(
            {
                "scene_duration": DURATION,
                "source_range": source_range,
                "rendering": rendering_identity("skia", scene),
            },
            indent=2,
        )
    )
    print(output)


if __name__ == "__main__":
    main()
