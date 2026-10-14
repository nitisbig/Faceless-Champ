"""Three original, silent core fixtures. Only the assembly gets a motion preview."""

import argparse
from pathlib import Path

import numpy as np
import pyvista as pv

from faceless_champ import (
    ArchCamera,
    ArchChamp,
    ArchDimension,
    ArchLabel,
    ArchMesh,
    ArchPart,
    ArchScript,
    ArchStyle,
    Canvas,
    Scene,
    render,
    save_frame,
)


def build_scene():
    """An original mechanical housing: internal parts, explosion and moving section."""
    parts = [
        ArchPart(
            "base",
            ArchMesh.from_data(pv.Cube(x_length=3, y_length=1.8, z_length=0.2)),
            position=(0, 0, -0.65),
            style=ArchStyle(color="#849ab1"),
        ),
        ArchPart(
            "shell",
            ArchMesh.from_data(pv.Cube(x_length=2.8, y_length=1.6, z_length=1.1)),
            style=ArchStyle(concept="transparent", color="#63d3ff"),
        ),
        ArchPart(
            "shaft",
            ArchMesh.from_data(pv.Cylinder(direction=(1, 0, 0), radius=0.28, height=2.3, resolution=32)),
            style=ArchStyle(color="#ffbe69"),
        ),
        ArchPart(
            "cover",
            ArchMesh.from_data(pv.Cube(x_length=2.8, y_length=1.6, z_length=0.12)),
            position=(0, 0, 0.65),
            explode_vector=(0, 0, 1),
            style=ArchStyle(color="#c9d5e3"),
        ),
    ]
    script = (
        ArchScript()
        .orbit(-35, at=0, duration=2)
        .explode("cover", 0.85, at=2, duration=2)
        .highlight("shaft", "#ffdd88", at=4, duration=1)
        .orbit(-25, at=4, duration=2)
        .section("shell", (0, 0, 0), (1, 0, 0), at=6, duration=3)
        .explode("cover", 0, at=9, duration=2)
        .wait(1)
    )
    clip = ArchChamp(
        parts,
        script,
        width=1600,
        height=900,
        position=(800, 450),
        units="m",
        camera=ArchCamera(position=(7, -7, 5), focal_point=(0, 0, 0.3), zoom=1.25),
        labels=[
            ArchLabel("Removable cover", (0, 0, 0), "cover", offset=(200, -100), font_size=40),
            ArchLabel("Internal shaft", (0, 0, 0), "shaft", offset=(-250, 30), font_size=40),
        ],
        dimensions=[ArchDimension((-1.5, -0.9, -0.1), (1.5, -0.9, -0.1), "base", offset=(0, 80), font_size=36)],
    )
    scene = Scene(Canvas(1600, 900, "#000000"))
    scene.add(clip)
    scene.wait(12)
    return scene


def field_scene():
    """Illustrative point values and a supplied analytic vector field, no solver."""
    grid = pv.ImageData(dimensions=(8, 6, 5), spacing=(0.2, 0.2, 0.2))
    grid["value"] = grid.points[:, 0]
    grid["flow"] = np.tile([1.0, 0.2, 0.0], (grid.n_points, 1))
    clip = ArchChamp(
        ArchMesh.from_data(grid),
        style=ArchStyle(concept="heatmap", scalars="value", vectors="flow", clim=(0, 1.4)),
        width=1600,
        height=900,
        position=(800, 450),
    )
    return Scene(Canvas(1600, 900, "#000000")).add(clip).wait(1)


def voxel_scene():
    """Voxelization of an original parametric surface."""
    mesh = ArchMesh.from_data(pv.ParametricEllipsoid(1.2, 0.8, 1))
    clip = ArchChamp(
        mesh,
        style=ArchStyle(concept="voxel", voxel_spacing=0.16, color="#c4a37a"),
        width=1600,
        height=900,
        position=(800, 450),
    )
    return Scene(Canvas(1600, 900, "#000000")).add(clip).wait(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("output/archchamp"))
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--stills", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    node = build_scene()
    if args.preview:
        render(node, args.output / "preview.mp4", width=960, height=540, fps=12, antialias=2, overwrite=args.overwrite)
    if args.stills:
        for name, scene, time in (
            ("assembly", node, 4.5),
            ("section", node, 8.5),
            ("field", field_scene(), 0),
            ("voxel", voxel_scene(), 0),
        ):
            save_frame(scene, time, args.output / (name + ".png"), size=(960, 540), overwrite=args.overwrite)
