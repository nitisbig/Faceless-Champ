"""Thirty-second ArchChamp showcase of a procedurally modelled Burj Khalifa."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/fc-burj-matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/fc-burj-cache")

import numpy as np
from PIL import Image as PILImage

from faceless_champ import (
    CLEAN_FLOW_FONT,
    Canvas,
    ExportProgress,
    ExportSettings,
    FadeIn,
    FadeOut,
    Image,
    Rectangle,
    Scene,
    Text,
    render,
)
from faceless_champ.arch import TessellationOptions, mesh_from_cad
from faceless_champ.integrations.pyvista.model import ArchPart, ArchStyle
from facelesschamp_kit.engineering import ArchCamera, ArchChamp, ArchScript

ROOT = Path(__file__).resolve().parent
DURATION = 30.0
VIEW_WIDTH, VIEW_HEIGHT = 1600, 1080
CANVAS_WIDTH, CANVAS_HEIGHT = 1920, 1080
VIEW_POSITION = (1120, 540)

BG_TOP = "#02060d"
BG_BOTTOM = "#061626"
GLOW = (26, 82, 116)
GOLD = "#c9a15c"
WHITE = "#eef3f9"
MUTED = "#8299b0"
SILVERS = ("#e4ebf4", "#d8e1ed", "#cdd8e6")
TOWER_RADIUS = 68.0

CAMERAS = {
    "start": ArchCamera(
        position=(520, -660, 70),
        focal_point=(0, 0, 250),
        projection="perspective",
        view_angle=55,
    ),
    "rise": ArchCamera(
        position=(760, -1010, 165),
        focal_point=(0, 0, 305),
        projection="perspective",
        view_angle=47,
    ),
    "wide": ArchCamera(
        position=(520, -1340, 300),
        focal_point=(0, 0, 370),
        projection="perspective",
        view_angle=39,
    ),
    "orbit": ArchCamera(
        position=(-700, -1360, 395),
        focal_point=(0, 0, 405),
        projection="perspective",
        view_angle=35,
    ),
    "final": ArchCamera(
        position=(-390, -1690, 465),
        focal_point=(0, 0, 415),
        projection="perspective",
        view_angle=33,
    ),
}

TIER_COUNT = 22


def y_outline(scale: float, radius: float = TOWER_RADIUS):
    """Three-lobed, deep-notched plan inspired by the tower's Y footprint."""
    points = []
    for arm in range(3):
        base = math.radians(90 + arm * 120)
        for degrees, factor in ((-56, 0.34), (-27, 0.64), (-12, 0.90), (0, 1.0), (12, 0.90), (27, 0.64)):
            angle = base + math.radians(degrees)
            r = radius * scale * factor
            points.append((r * math.cos(angle), r * math.sin(angle)))
    return points


def lofted_tier(bd, z0, z1, s0, s1, taper=0.985):
    bottom = bd.Face(bd.Wire.make_polygon([(x, y, z0) for x, y in y_outline(s0)]))
    top = bd.Face(bd.Wire.make_polygon([(x, y, z1) for x, y in y_outline(s1 * taper)]))
    return bd.loft([bottom, top], ruled=True)


def build_tower():
    """Return labelled build123d solids and their authored colours."""
    import build123d as bd

    solids = []
    z = 18.0
    heights = []
    for i in range(TIER_COUNT):
        heights.append(42.0 + (12.0 - 42.0) * i / (TIER_COUNT - 1))
    total = sum(heights)
    heights = [h * (610.0 - 18.0) / total for h in heights]

    scales = []
    for i in range(TIER_COUNT):
        t = i / (TIER_COUNT - 1)
        scales.append(1.0 - 0.755 * t**1.12)

    # Broad stepped podium below the main shaft.
    solids.append(("podium-lower", bd.Pos(0, 0, 0) * bd.Pos(0, 0, 0) * lofted_tier(bd, 0.0, 7.0, 1.38, 1.38, 0.998), "#aebfd2"))
    solids.append(("podium-upper", lofted_tier(bd, 7.0, 13.0, 1.26, 1.26, 0.998), "#b8c7d9"))
    solids.append(("podium-crown", lofted_tier(bd, 13.0, 18.0, 1.13, 1.13, 0.998), "#c2d0e0"))

    for i, (h, s0) in enumerate(zip(heights, scales)):
        s1 = s0 - 0.02 * (1.0 - 0.4 * i / TIER_COUNT)
        color = SILVERS[i % len(SILVERS)]
        solids.append((f"tier-{i + 1:02d}", lofted_tier(bd, z, z + h, s0, s1, 0.992), color))
        z += h

    # Stepped crown and mast.
    crown = [
        ("crown-lower", 610.0, 668.0, 0.252, 0.190),
        ("crown-mid", 668.0, 724.0, 0.176, 0.118),
        ("crown-upper", 724.0, 772.0, 0.106, 0.052),
    ]
    for name, z0, z1, s0, s1 in crown:
        solids.append((name, lofted_tier(bd, z0, z1, s0, s1, 0.99), "#e7c47f"))

    solids.append(
        (
            "mast",
            bd.Pos(0, 0, 771.0) * bd.Cone(bottom_radius=2.6, top_radius=0.35, height=53.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)),
            "#e3bd74",
        )
    )
    solids.append(
        (
            "beacon",
            bd.Pos(0, 0, 824.0) * bd.Sphere(radius=2.6),
            "#fff2cd",
        )
    )

    # Display plinth and its thin gold trim rings.
    solids.append(
        (
            "plinth",
            bd.Pos(0, 0, -6.0) * bd.Cylinder(radius=252, height=6, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)),
            "#0c1a27",
        )
    )
    solids.append(("plinth-ring", bd.Pos(0, 0, -0.2) * bd.Torus(250, 1.1), "#a9884f"))
    solids.append(("plinth-ring-inner", bd.Pos(0, 0, -0.2) * bd.Torus(214, 0.55), "#3f5164"))
    return solids


def build_view():
    options = TessellationOptions(linear_deflection=0.05, angular_deflection=0.08, max_triangles=1_200_000)
    parts, base_styles = [], {}
    for name, solid, color in build_tower():
        mesh = mesh_from_cad(solid, options=options, source_units="m", target_units="m")
        style = ArchStyle(color=color, opacity=0.0, smooth_shading=True)
        base_styles[name] = (color, style)
        parts.append(ArchPart(name, mesh, style=style))

    script = ArchScript()
    reveal_start = 0.35
    for index, part in enumerate(parts):
        if part.id.startswith("plinth") or part.id.startswith("podium"):
            at = 0.15 + 0.10 * index
        elif part.id.startswith("tier-"):
            at = reveal_start + 0.65 + 0.135 * (index - 3)
        elif part.id == "crown-lower":
            at = 4.15
        elif part.id == "crown-mid":
            at = 4.35
        elif part.id == "crown-upper":
            at = 4.55
        elif part.id == "mast":
            at = 4.75
        else:
            at = 5.10
        script.opacity(part.id, 1.0, at=at, duration=0.85, easing="smooth")

    script.camera_to(CAMERAS["rise"], at=1.0, duration=8.0, easing="smooth")
    script.camera_to(CAMERAS["wide"], at=9.0, duration=7.4, easing="smooth")
    script.camera_to(CAMERAS["orbit"], at=16.4, duration=7.6, easing="smooth")
    script.camera_to(CAMERAS["final"], at=24.0, duration=6.0, easing="smooth")
    script.wait(0)

    view = ArchChamp(
        parts,
        script,
        width=VIEW_WIDTH,
        height=VIEW_HEIGHT,
        position=VIEW_POSITION,
        units="m",
        camera=CAMERAS["start"],
    )
    return view


def background_image():
    width, height = CANVAS_WIDTH, CANVAS_HEIGHT
    y = np.linspace(0, 1, height)[:, None]
    top = np.array([int(BG_TOP[i : i + 2], 16) for i in (1, 3, 5)], dtype=float)
    bottom = np.array([int(BG_BOTTOM[i : i + 2], 16) for i in (1, 3, 5)], dtype=float)
    base = top + (bottom - top) * (y**1.35)
    image = np.repeat(base[:, None, :], width, axis=1)

    xx, yy = np.meshgrid(np.arange(width), np.arange(height))
    glow = np.exp(-(((xx - 1115) / 560) ** 2 + ((yy - 690) / 500) ** 2) * 2.1)
    image += np.array(GLOW, dtype=float) * glow[..., None] * 0.62

    warm = np.exp(-(((xx - 1115) / 300) ** 2 + ((yy - 250) / 360) ** 2) * 2.0)
    image += np.array([42, 34, 26], dtype=float) * warm[..., None] * 0.30

    vignette = 1.0 - 0.55 * (((xx - width / 2) / (width * 0.78)) ** 2 + ((yy - height / 2) / (height * 0.72)) ** 2)
    image *= np.clip(vignette, 0.15, 1.0)[..., None]
    return PILImage.fromarray(np.clip(image, 0, 255).astype(np.uint8), "RGB")


def add_text(scene):
    accent = Rectangle(width=4, height=104, fill=GOLD, stroke=None, position=(122, 800), anchor="center")
    heading = Text(
        "BURJ KHALIFA",
        font=CLEAN_FLOW_FONT,
        font_size=82,
        color=WHITE,
        font_weight=700,
        position=(150, 804),
        anchor="top_left",
    )
    subtitle = Text(
        "DUBAI · UNITED ARAB EMIRATES",
        font=CLEAN_FLOW_FONT,
        font_size=23,
        color=MUTED,
        font_weight=400,
        position=(152, 914),
        anchor="top_left",
    )
    with scene.at(0.8):
        scene.add(accent, heading, subtitle)
        scene.play(FadeIn(accent), FadeIn(heading), FadeIn(subtitle), run_time=0.9)
    with scene.at(7.4):
        scene.play(FadeOut(accent), FadeOut(heading), FadeOut(subtitle), run_time=0.9)

    with scene.at(23.2):
        stat_rule = Rectangle(width=72, height=2, fill=GOLD, stroke=None, position=(158, 838), anchor="center")
        stat = Text(
            "828 M",
            font=CLEAN_FLOW_FONT,
            font_size=104,
            color=WHITE,
            font_weight=700,
            position=(120, 848),
            anchor="top_left",
        )
        detail = Text(
            "163 FLOORS · COMPLETED 2010",
            font=CLEAN_FLOW_FONT,
            font_size=23,
            color=MUTED,
            font_weight=400,
            position=(124, 968),
            anchor="top_left",
        )
        scene.add(stat_rule, stat, detail)
        scene.play(FadeIn(stat_rule), FadeIn(stat), FadeIn(detail), run_time=1.0)


def build_scene():
    canvas = Canvas(CANVAS_WIDTH, CANVAS_HEIGHT, BG_TOP)
    scene = Scene(canvas)
    backdrop = Image.from_source(background_image(), width=CANVAS_WIDTH, height=CANVAS_HEIGHT, fit="cover", position=(960, 540))
    scene.add(backdrop)
    scene.add(build_view())
    scene.wait_until(DURATION)
    add_text(scene)
    scene.wait_until(DURATION)
    return scene


def key_check(scene):
    assert scene.duration == DURATION
    assert scene.canvas.width == CANVAS_WIDTH and scene.canvas.height == CANVAS_HEIGHT
    print(
        json.dumps(
            {
                "duration": scene.duration,
                "canvas": [CANVAS_WIDTH, CANVAS_HEIGHT],
                "tier_count": TIER_COUNT,
                "camera_keys": len(CAMERAS),
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--frame", type=float, metavar="SECONDS")
    mode.add_argument("--preview", action="store_true")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--antialias", type=int, default=2, choices=(1, 2, 3, 4))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame <= DURATION:
        parser.error("--frame must be between 0 and 30")
    if args.width < 2 or args.fps < 1:
        parser.error("width must be >= 2 and fps must be positive")

    scene = build_scene()
    key_check(scene)
    if args.check:
        return

    if args.frame is not None:
        from faceless_champ.preview import save_frame

        output = args.output or ROOT / "output" / f"frame-{args.frame:g}.png"
        save_frame(scene, args.frame, output, size=(args.width, round(args.width * 9 / 16)), overwrite=args.overwrite)
        print(output, flush=True)
        return

    preview = args.preview
    width = 960 if preview else args.width
    fps = 12 if preview else args.fps
    output = args.output or ROOT / "output" / ("preview.mp4" if preview else "burj-khalifa.mp4")
    output.parent.mkdir(parents=True, exist_ok=True)
    settings = ExportSettings(
        width=width,
        height=round(width * 9 / 16),
        fps=fps,
        antialias=args.antialias,
        crf=16,
        preset="slow" if not preview else "medium",
    )
    with ExportProgress() as progress:
        render(
            scene,
            output,
            settings=settings,
            overwrite=args.overwrite,
            progress=progress,
        )
    evidence = {
        "scene_duration": scene.duration,
        "output": str(output),
        "width": width,
        "height": round(width * 9 / 16),
        "fps": fps,
        "antialias": args.antialias,
        "full_export_verified": False,
        "audio": False,
        "geometry": "procedural build123d Y-plan, 22 setbacks + crown + mast",
    }
    output.with_suffix(".json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(output, flush=True)


if __name__ == "__main__":
    main()
