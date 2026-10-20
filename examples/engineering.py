"""Native engineering showcase. Install faceless-champ[cad] and run --help."""

import argparse
from dataclasses import replace
from pathlib import Path

from faceless_champ import Canvas, Scene, Sequence, render, validate_composition
from faceless_champ.arch import (
    ArchCamera,
    ArchChamp,
    ArchDimension,
    ArchScript,
    ArchStyle,
    blueprint_from_cad,
    parts_from_cad,
)
from faceless_champ.arch.cad_models import gear_pair, inline_engine, portal_frame


def build_scene():
    canvas = Canvas(1920, 1080, "#080f1c")
    gears = gear_pair()
    gear_parts = [
        replace(p, style=ArchStyle(color="#70cfee" if p.id == "driver" else "#d4dee7")) for p in parts_from_cad(gears)
    ]
    gear_view = ArchChamp(
        gear_parts,
        ArchScript().gear_pair("driver", "driven", degrees=720, duration=4),
        units="mm",
        width=1920,
        height=1080,
        position=(960, 540),
        camera=ArchCamera(position=(230, -270, 190), focal_point=(48, 0, 5), zoom=1.8),
        dimensions=[ArchDimension((0, 0, 0), (72, 0, 0), offset=(0, 100))],
    )
    script = ArchScript()
    for i in range(2):
        script.slider_crank(
            [f"cylinder-{i + 1}/{p}" for p in ("crank", "rod", "piston")], phase=i * 180, at=0, duration=4, turns=2
        )
    script.section("block", (45, 0, 12), normal=(0, -1, 0), at=0, duration=0.4, cap=True)
    engine_parts = []
    for part in parts_from_cad(inline_engine(cylinders=2)):
        role = part.id.rsplit("/", 1)[-1]
        color = {"block": "#63768b", "shaft": "#dba65d", "crank": "#dba65d", "rod": "#52bddd", "piston": "#d9e1e5"}[
            role
        ]
        engine_parts.append(replace(part, style=ArchStyle(color=color)))
    engine_view = ArchChamp(
        engine_parts,
        script,
        units="mm",
        width=1920,
        height=1080,
        position=(960, 540),
        camera=ArchCamera(position=(180, -220, 140), focal_point=(30, 0, 12), zoom=1.6),
    )
    frame_view = ArchChamp(
        parts_from_cad(portal_frame(bays=2), target_units="m"),
        ArchScript().orbit(40, duration=4),
        units="m",
        width=1920,
        height=1080,
        position=(960, 540),
        camera=ArchCamera(position=(17, -20, 15), focal_point=(4, 1.5, 1.5), zoom=1.7),
        dimensions=[ArchDimension((0, 0, 0), (0, 0, 3), offset=(60, 0))],
    )
    drawing = blueprint_from_cad(
        gears,
        camera=ArchCamera(position=(0, 0, 300), up=(0, 1, 0)),
        width=1920,
        height=1080,
        margin=150,
        dimensions=[ArchDimension((0, 0, 0), (72, 0, 0), offset=(0, 180))],
    )
    return Sequence(
        Scene(canvas).add(gear_view).wait(4),
        Scene(canvas).add(engine_view).wait(4),
        Scene(canvas).add(frame_view).wait(4),
        Scene(canvas).add(drawing).wait(4),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--backend", choices=["pillow", "skia", "moderngl"], default="pillow")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--seconds", type=float, default=3)
    parser.add_argument("--output", type=Path, default=Path("output/engineering/preview.mp4"))
    args = parser.parse_args()
    scene = build_scene()
    validate_composition(scene)
    if not args.check:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        render(
            scene,
            args.output,
            backend=args.backend,
            width=args.width,
            fps=args.fps,
            antialias=1,
            start_time=args.start,
            end_time=min(scene.duration, args.start + args.seconds),
            overwrite=True,
        )
