"""Ten-second native build123d → ArchChamp exploded turbofan assembly."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/fc-jet-matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/fc-jet-cache")

from faceless_champ import Canvas, ExportProgress, Scene, render, validate_composition
from faceless_champ.arch import ArchCamera, ArchChamp, ArchScript, ArchStyle, TessellationOptions, parts_from_cad
from faceless_champ.renderer import create_renderer

ROOT = Path(__file__).resolve().parent
DURATION = 10.0


def make_assembly():
    """Original teaching geometry in mm; a high-bypass turbofan, not Boeing CAD."""
    import build123d as bd

    children, metadata = [], {}

    def add(name, shape, x, color, offset, *, rotor=False):
        # Preserve the solid's native orientation inside a module whose local
        # animation frame is always engine X (Cylinder/Cone are authored on Z).
        shape = bd.Compound([shape])
        shape.label = name
        shape.location = bd.Location((x, 0, 0))
        children.append(shape)
        metadata[name] = (color, offset, rotor)

    def tube(outer, inner, length):
        return bd.Rot(0, 90, 0) * (bd.Cylinder(outer, length) - bd.Cylinder(inner, length + 2))

    def rotor(radius, hub, chord, count):
        # Lofted airfoils change pitch and sweep between root and tip.
        sections = []
        for radial, sweep, pitch, width in (
            (hub - 1, 0, -0.48, chord * 0.7),
            (radius * 0.66, chord * 0.17, -0.18, chord),
            (radius, chord * 0.36, 0.22, chord * 0.73),
        ):
            profile = bd.Polygon(
                (-width / 2, -1.4),
                (-width * 0.2, -2),
                (width / 2, pitch * width),
                (width * 0.42, pitch * width + 2.2),
                (-width * 0.22, 1.6),
                align=None,
            )
            sections.append(bd.Pos(sweep, 0, radial) * profile)
        blade = bd.loft(sections)
        disk = bd.Rot(0, 90, 0) * bd.Cylinder(hub, chord * 0.72)
        return bd.Compound([disk, *(bd.Rot(i * 360 / count, 0, 0) * blade for i in range(count))])

    silver, blue, gold = "#C8D8E3", "#75BDD3", "#DBA260"
    add("fan", rotor(94, 25, 25, 24), -122, silver, (-130, 0, 0), rotor=True)
    nose = bd.Rot(0, -90, 0) * bd.Cone(25, 2, 42)
    add("spinner", nose, -154, "#E0E9EF", (-160, 0, 0), rotor=True)
    add("intake-ring", tube(103, 97, 24), -122, blue, (-95, 0, 90))
    add("shaft", bd.Rot(0, 90, 0) * bd.Cylinder(7, 266), 10, "#7C8E9E", (0, 0, -105), rotor=True)
    for i, (x, radius) in enumerate(((-69, 57), (-32, 51), (3, 45))):
        add(f"compressor-{i + 1}", rotor(radius, 19, 15, 26), x, blue, (-65 + i * 34, 0, 0), rotor=True)
        add(f"stator-{i + 1}", tube(radius + 4, radius - 2, 7), x + 13, silver, (-53 + i * 34, 0, 0))
    # Twelve cooling ports are native CAD booleans in the annular combustor.
    combustor = tube(43, 32, 48)
    for i in range(12):
        cutter = bd.Rot(i * 30, 0, 0) * bd.Pos(0, 0, 40) * bd.Cylinder(3.1, 22)
        combustor = combustor - cutter
    add("combustor", combustor, 47, gold, (74, 0, 0))
    for i, x in enumerate((86, 112)):
        add(
            f"turbine-{i + 1}",
            rotor(40 + i * 4, 17, 12, 30),
            x,
            gold if i == 0 else silver,
            (112 + i * 43, 0, 0),
            rotor=True,
        )
    nozzle = bd.Rot(0, 90, 0) * (bd.Cone(48, 32, 48) - bd.Cone(44, 28, 50))
    add("exhaust", nozzle, 150, "#879CAA", (205, 0, 0))
    # Two solid shell halves lift away to expose the core without transparency.
    shell = tube(68, 64, 220)
    for upper in (True, False):
        half = shell & (bd.Pos(0, 0, 80 if upper else -80) * bd.Box(250, 160, 160))
        add("casing-upper" if upper else "casing-lower", half, 12, "#819BAD", (10, 0, 140 if upper else -140))
    return bd.Compound(children=children, label="turbofan"), metadata


def build_scene():
    assembly, metadata = make_assembly()
    print("Tessellating native CAD assembly…", flush=True)
    prepared = parts_from_cad(assembly, options=TessellationOptions(linear_deflection=0.22, angular_deflection=0.18))
    script, parts = ArchScript(), []
    for i, part in enumerate(prepared):
        color, offset, rotor = metadata[part.id]
        parts.append(replace(part, style=ArchStyle(color=color), explode_vector=offset))
        # A quiet opening, staggered separation, inspection hold, reverse assembly.
        delay = 0.035 * i
        script.explode(part.id, factor=1, at=1.0 + delay, duration=2.05, easing="smooth")
        script.explode(part.id, factor=0, at=6.05 + (len(prepared) - i - 1) * 0.035, duration=2.05, easing="smooth")
        if rotor:
            script.spin(part.id, degrees=105, axis=(1, 0, 0), at=0, duration=DURATION)
    # Same view direction at the start/end; a gentle inspection move in the middle.
    script.camera_to(
        ArchCamera(position=(-430, -850, 355), focal_point=(25, 0, 0), zoom=1.60), at=0, duration=4.2, easing="smooth"
    )
    script.camera_to(
        ArchCamera(position=(-520, -850, 285), focal_point=(25, 0, 0), zoom=1.85), at=6, duration=4, easing="smooth"
    )
    view = ArchChamp(
        parts,
        script,
        width=1920,
        height=1080,
        position=(960, 540),
        units="mm",
        camera=ArchCamera(position=(-520, -850, 285), focal_point=(25, 0, 0), zoom=1.85),
    )
    scene = Scene(Canvas(1920, 1080, "#000000")).add(view).wait_until(DURATION)
    return scene, view


def key_check(scene, view):
    validate_composition(scene)
    assert scene.duration == DURATION and scene.canvas.bg == "#000000"
    assert not view.labels and not view.dimensions
    for part in view.parts:
        initial = view.state_at(0)["parts"][part.id]["position"]
        final = view.state_at(10)["parts"][part.id]["position"]
        assert all(abs(a - b) < 1e-8 for a, b in zip(initial, final)), part.id
        assert part.mesh.provenance["generator"] == "build123d"
    assert view.state_at(4.5)["parts"]["fan"]["position"] != view.state_at(0)["parts"]["fan"]["position"]
    print(
        json.dumps(
            {
                "duration": scene.duration,
                "cad_parts": len(view.parts),
                "triangles": sum(p.mesh.dataset.n_cells for p in view.parts),
                "reassembly_check": "passed",
                "background": scene.canvas.bg,
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--frame", type=float)
    mode.add_argument("--preview", action="store_true", help="Full timeline at 960×540 / 12 fps")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.frame is not None and not 0 <= args.frame <= DURATION:
        parser.error("--frame must be between 0 and 10")
    if args.width < 2 or args.fps < 1:
        parser.error("width must be >= 2 and fps must be positive")
    scene, view = build_scene()
    key_check(scene, view)
    if args.check:
        return
    width, fps = (960, 12) if args.preview else (args.width, args.fps)
    out = args.output or ROOT / "media" / (
        f"frame-{args.frame:g}.png" if args.frame is not None else "preview.mp4" if args.preview else "jet-engine.mp4"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    with create_renderer("pillow", antialias=1) as renderer:
        if args.frame is not None:
            if out.exists() and not args.overwrite:
                raise FileExistsError(out)
            renderer.frame(scene, args.frame, (width, round(width * 9 / 16))).save(out)
        else:
            render(
                scene,
                out,
                renderer=renderer,
                width=width,
                height=round(width * 9 / 16),
                fps=fps,
                antialias=1,
                overwrite=args.overwrite,
                progress=ExportProgress(),
            )
    print(out, flush=True)


if __name__ == "__main__":
    main()
