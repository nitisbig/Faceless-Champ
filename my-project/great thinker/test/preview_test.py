"""Key capability probe: Skia typography, CPU glow, and a transparent ArchChamp 3D card."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "facelesschamp-kit/src")]

import pyvista as pv
from faceless_champ import (
    Bloom,
    Bounds,
    Canvas,
    Circle,
    EffectStack,
    GradientStop,
    Group,
    LinearGradient,
    OuterGlow,
    Rectangle,
    Scene,
    ShadowStyle,
    Text,
    card_surface,
    save_frame,
)
from faceless_champ.integrations.pyvista.camera import ArchCamera
from faceless_champ.integrations.pyvista.model import ArchMesh, ArchPart, ArchStyle
from facelesschamp_kit.engineering.clip import ArchChamp
from facelesschamp_kit.engineering.script import ArchScript

FONT_SERIF = ROOT / "assets/fonts/CormorantGaramond[wght].ttf"
FONT_SANS = ROOT / "assets/fonts/SpaceGrotesk[wght].ttf"


def scene_2d():
    scene = Scene(Canvas(1920, 1080, "#F3EFE6"))
    title = Text(
        "Great Thinkers",
        font=FONT_SERIF,
        font_weight=600,
        font_size=150,
        color="#1B1A17",
        position=(960, 470),
        text_engine="skia",
    )
    eyebrow = Text(
        "A 2,500-YEAR TIMELINE OF IDEAS",
        font=FONT_SANS,
        font_weight=500,
        font_size=24,
        color="#8A7F6B",
        position=(960, 330),
        text_engine="skia",
    )
    orb = Circle(
        120,
        fill="#C08A3E",
        stroke=None,
        position=(1390, 250),
        effects=EffectStack(glow=OuterGlow("#C08A3E", 40, 0.5), bloom=Bloom(20, 0.35, 0.7)),
    )
    card = card_surface(
        Bounds(250, 700, 1670, 980),
        fill=LinearGradient((GradientStop(0, "#FFFFFF"), GradientStop(1, "#EDE6D8")), angle=90),
        radius=30,
        shadow=ShadowStyle("#3B302020", blur=14, offset=(0, 10)),
        render_mode="vector",
    )
    scene.add(card, eyebrow, title, orb)
    scene.wait(2)
    return scene


def scene_3d():
    scene = Scene(Canvas(1920, 1080, "#F3EFE6"))
    card = card_surface(
        Bounds(980, 250, 1780, 850),
        fill=LinearGradient((GradientStop(0, "#1A1E24"), GradientStop(1, "#0C0F13")), angle=140),
        radius=36,
        shadow=ShadowStyle("#3B302040", blur=20, offset=(0, 18)),
        render_mode="vector",
    )
    sphere = ArchPart(
        "planet",
        ArchMesh.from_data(pv.Sphere(radius=0.9, theta_resolution=48, phi_resolution=48)),
        style=ArchStyle(concept="solid", color="#D8C8A8", edge_color="#C08A3E", smooth_shading=True),
    )
    ring = ArchPart(
        "orbit",
        ArchMesh.from_data(pv.ParametricTorus(ringradius=1.7, crosssectionradius=0.02)),
        rotation=(72, 0, 22),
        style=ArchStyle(concept="solid", color="#C08A3E", edge_color="#C08A3E"),
    )
    script = ArchScript().orbit(70, duration=7, easing="smooth")
    view = ArchChamp(
        [sphere, ring],
        script,
        camera=ArchCamera(position=(180, -320, 210), focal_point=(0, 0, 0)),
        style=ArchStyle(concept="solid"),
        width=800,
        height=600,
        position=(1380, 550),
    )
    label = Text(
        "Isaac Newton",
        font=FONT_SERIF,
        font_weight=600,
        font_size=112,
        color="#1B1A17",
        position=(220, 390),
        anchor="top_left",
        text_engine="skia",
    )
    scene.add(card, view, label)
    scene.wait(8)
    return scene


if __name__ == "__main__":
    out = Path(__file__).resolve().parent
    for name, builder, at in (("2d", scene_2d, 1.0), ("3d", scene_3d, 1.0)):
        scene = builder()
        start = time.perf_counter()
        path = out / f"probe-{name}.png"
        save_frame(scene, at, path, size=(1920, 1080), backend="skia", overwrite=True)
        print(name, f"{time.perf_counter() - start:.2f}s", path)
