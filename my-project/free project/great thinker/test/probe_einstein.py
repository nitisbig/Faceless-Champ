"""Probe the 3D spacetime grid and the improved Newton 3D card."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "facelesschamp-kit/src")]

import numpy as np
import pyvista as pv
from faceless_champ import (
    Bounds,
    Canvas,
    Circle,
    GradientStop,
    LinearGradient,
    RadialGradient,
    Rectangle,
    Scene,
    ShadowStyle,
    Text,
    card_surface,
    gradient_surface,
    save_frame,
)
from faceless_champ.integrations.pyvista.camera import ArchCamera
from faceless_champ.integrations.pyvista.model import ArchMesh, ArchPart, ArchStyle
from facelesschamp_kit.engineering.clip import ArchChamp
from facelesschamp_kit.engineering.script import ArchScript

FONT_SERIF = ROOT / "assets/fonts/CormorantGaramond[wght].ttf"
FONT_SANS = ROOT / "assets/fonts/SpaceGrotesk[wght].ttf"


def card_layer(bounds):
    card = card_surface(
        Bounds(*bounds),
        fill=LinearGradient((GradientStop(0, "#1B1F26"), GradientStop(1, "#0C0F13")), angle=140),
        radius=36,
        shadow=ShadowStyle("#3B302040", blur=20, offset=(0, 18)),
        render_mode="vector",
    )
    hairline = Rectangle(
        width=bounds[2] - bounds[0],
        height=bounds[3] - bounds[1],
        corner_radius=36,
        fill=None,
        stroke="#C08A3E40",
        stroke_width=1,
        position=((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2),
    )
    glow = gradient_surface(
        Bounds(bounds[0] + 100, bounds[1] + 20, bounds[2] - 100, bounds[3] - 20),
        fill=RadialGradient(
            (GradientStop(0, "#C08A3E55"), GradientStop(0.45, "#C08A3E18"), GradientStop(1, "#C08A3E00")),
            center=(0.5, 0.52),
            radius=0.9,
        ),
    )
    return card, glow, hairline


def scene_einstein():
    bounds = (980, 210, 1780, 850)
    scene = Scene(Canvas(1920, 1080, "#F3EFE6"))
    card, glow, hairline = card_layer(bounds)
    plane = pv.Plane(i_size=5.2, j_size=5.2, i_resolution=46, j_resolution=46)
    pts = np.asarray(plane.points).copy()
    r2 = pts[:, 0] ** 2 + pts[:, 1] ** 2
    pts[:, 2] = -1.05 * np.exp(-r2 / 1.2)
    plane.points = pts
    grid = ArchPart(
        "spacetime",
        ArchMesh.from_data(plane),
        style=ArchStyle(concept="wireframe", color="#C08A3E", edge_color="#C08A3E", line_width=1.1),
    )
    mass = ArchPart(
        "mass",
        ArchMesh.from_data(pv.Sphere(radius=0.22, theta_resolution=32, phi_resolution=32)),
        position=(0, 0, -0.86),
        style=ArchStyle(concept="solid", color="#F0E3C8", edge_color="#F0E3C8", smooth_shading=True),
    )
    initial = ArchCamera(position=(4.7, -6.4, 4.0), focal_point=(0, 0, -0.45))
    final = ArchCamera(position=(3.6, -5.5, 4.8), focal_point=(0, 0, -0.45))
    script = ArchScript().camera_to(final, duration=7.5, easing="smooth")
    view = ArchChamp(
        [grid, mass],
        script,
        camera=initial,
        width=bounds[2] - bounds[0],
        height=bounds[3] - bounds[1],
        position=((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2),
    )
    core = Circle(7, fill="#F0D9A6", stroke=None, position=(1380, 532))
    label = Text(
        "Albert Einstein",
        font=FONT_SERIF,
        font_weight=600,
        font_size=108,
        color="#1C1A17",
        position=(180, 392),
        anchor="top_left",
        text_engine="skia",
    )
    scene.add(card, glow, hairline, view, core, label)
    scene.wait(8)
    return scene


def scene_newton():
    bounds = (980, 210, 1780, 850)
    scene = Scene(Canvas(1920, 1080, "#F3EFE6"))
    card, glow, hairline = card_layer(bounds)
    sphere = ArchPart(
        "planet",
        ArchMesh.from_data(pv.Sphere(radius=1.05, theta_resolution=48, phi_resolution=48)),
        style=ArchStyle(concept="solid", color="#D8C8A8", edge_color="#C08A3E", smooth_shading=True),
    )
    ring_a = ArchPart(
        "orbit_a",
        ArchMesh.from_data(pv.ParametricTorus(ringradius=1.8, crosssectionradius=0.018)),
        rotation=(74, 0, 18),
        style=ArchStyle(concept="solid", color="#C08A3E", edge_color="#C08A3E"),
    )
    ring_b = ArchPart(
        "orbit_b",
        ArchMesh.from_data(pv.ParametricTorus(ringradius=1.55, crosssectionradius=0.012)),
        rotation=(52, 38, 64),
        style=ArchStyle(concept="solid", color="#C08A3E", edge_color="#C08A3E"),
    )
    script = ArchScript().orbit(50, duration=7.5, easing="smooth")
    view = ArchChamp(
        [sphere, ring_a, ring_b],
        script,
        camera=ArchCamera(position=(180, -320, 210), focal_point=(0, 0, 0)),
        width=bounds[2] - bounds[0],
        height=bounds[3] - bounds[1],
        position=((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2),
    )
    label = Text(
        "Isaac Newton",
        font=FONT_SERIF,
        font_weight=600,
        font_size=108,
        color="#1C1A17",
        position=(180, 392),
        anchor="top_left",
        text_engine="skia",
    )
    scene.add(card, glow, hairline, view, label)
    scene.wait(8)
    return scene


if __name__ == "__main__":
    out = Path(__file__).resolve().parent
    for name, builder in (("einstein", scene_einstein), ("newton", scene_newton)):
        scene = builder()
        start = time.perf_counter()
        path = out / f"probe-{name}.png"
        save_frame(scene, 3.8, path, size=(1920, 1080), backend="skia", overwrite=True)
        print(name, f"{time.perf_counter() - start:.2f}s", path)
