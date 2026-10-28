"""New York City, engineered: a 45-second 3D architecture study built with ArchChamp.

Beats
  0-7    Plan       top-down street grid draws in like a drafting sheet
  6-15   Rise       Manhattan extrudes district by district, wire first, then mass
  15-23  Empire     setbacks explode into an axonometric stack and reassemble
  23-31  One WTC    a vertical section opens the shell to show core and floor plates
  31-39  Midtown    the camera threads Chrysler's crown and 432 Park's open floors
  39-45  Skyline    dusk: windows ignite across the whole island

Run from the repository root:
  .venv/bin/python my-project/nyc-architecture/scene.py --check
  .venv/bin/python my-project/nyc-architecture/scene.py --frame 12
  .venv/bin/python my-project/nyc-architecture/scene.py --audit
  .venv/bin/python my-project/nyc-architecture/scene.py --preview --start 15 --duration 6
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/fc-nyc-matplotlib")

import itertools

import numpy as np
import pyvista as pv
from facelesschamp_kit.engineering import ArchCamera, ArchChamp, ArchScript
from PIL import Image as PILImage

from faceless_champ import ExportProgress, ExportSettings, FadeOut, Image, Scene, Theme, render
from faceless_champ.integrations.pyvista.model import ArchMesh, ArchPart, ArchStyle

ROOT = Path(__file__).resolve().parent
DURATION = 45.0
theme = Theme.named("midnight")
C = theme.colors


# --------------------------------------------------------------------------- palette
def hex_rgb(value):
    value = value.lstrip("#")
    return np.array([int(value[i : i + 2], 16) for i in (0, 2, 4)], dtype=float)


def mix(a, b, t):
    """Blend two theme colors so every material stays inside the palette."""
    rgb = hex_rgb(a) * (1 - t) + hex_rgb(b) * t
    return "#" + "".join(f"{round(v):02x}" for v in np.clip(rgb, 0, 255))


MASS = mix(C.border, C.muted, 0.28)  # generic towers: cool slate
MASS_FAR = mix(C.border, C.surface, 0.35)
WIRE = C.primary  # drafting lines
GROUND = mix(C.background, C.surface, 0.55)
STREET = mix(C.grid, C.primary, 0.22)
HERO = mix(C.muted, C.text, 0.45)  # landmarks: pale stone
GOLD = C.secondary
CORE = C.tertiary
GLOW = mix(C.secondary, C.text, 0.25)
DUSK = mix(C.border, C.background, 0.45)  # masses darken so window light reads


# --------------------------------------------------------------------------- geometry
# World units are metres. x runs south -> north along the island, y west -> east.
X_MIN, X_MAX, Y_MIN, Y_MAX = -1750.0, 1450.0, -620.0, 620.0
BLOCK_X, BLOCK_Y, STREET_W, AVENUE_W = 64.0, 230.0, 18.0, 32.0

HEROES = {
    "wtc": (-1430.0, -260.0),
    "esb": (60.0, 40.0),
    "chrysler": (470.0, 300.0),
    "park432": (880.0, 110.0),
}
HERO_CLEAR = {"wtc": 120.0, "esb": 110.0, "chrysler": 70.0, "park432": 60.0}


def box(cx, cy, w, d, z0, z1):
    return pv.Box((cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0, z1))


def merge(meshes):
    meshes = [m for m in meshes if m.n_points]
    return pv.merge(meshes, merge_points=False) if len(meshes) > 1 else meshes[0]


def height_field(x, y):
    """Two business districts (Midtown, Downtown) over a low residential carpet."""
    midtown = math.exp(-(((x - 450) / 520) ** 2 + (y / 520) ** 2))
    downtown = math.exp(-(((x + 1380) / 300) ** 2 + ((y + 120) / 420) ** 2))
    return 26 + 210 * midtown + 230 * downtown


def street_grid():
    """Thin raised strips for every avenue and street: the drafting sheet."""
    lines = []
    xs = np.arange(X_MIN, X_MAX + 1, BLOCK_X + STREET_W)
    ys = np.arange(Y_MIN, Y_MAX + 1, BLOCK_Y + AVENUE_W)
    for x in xs:
        lines.append(pv.Line((x - STREET_W / 2, Y_MIN, 0.6), (x - STREET_W / 2, Y_MAX, 0.6)))
    for y in ys:
        lines.append(pv.Line((X_MIN, y - AVENUE_W / 2, 0.6), (X_MAX, y - AVENUE_W / 2, 0.6)))
    lines.append(pv.Line((X_MIN, Y_MIN, 0.6), (X_MAX, Y_MIN, 0.6)))
    lines.append(pv.Line((X_MIN, Y_MAX, 0.6), (X_MAX, Y_MAX, 0.6)))
    return merge(lines)


def generic_city(rng, districts=6):
    """Return per-district (mass, windows) meshes; district index rises south -> north wave."""
    masses = [[] for _ in range(districts)]
    windows = [[] for _ in range(districts)]
    xs = np.arange(X_MIN, X_MAX - BLOCK_X, BLOCK_X + STREET_W)
    ys = np.arange(Y_MIN, Y_MAX - BLOCK_Y, BLOCK_Y + AVENUE_W)
    for bx in xs:
        for by in ys:
            lots = rng.integers(2, 5)
            cuts = np.sort(rng.uniform(0.15, 0.85, lots - 1))
            edges = np.concatenate([[0], cuts, [1]]) * BLOCK_Y
            for a, b in itertools.pairwise(edges):
                w, d = BLOCK_X - rng.uniform(4, 12), (b - a) - rng.uniform(4, 10)
                if d < 18:
                    continue
                cx, cy = bx + BLOCK_X / 2, by + (a + b) / 2
                if any(math.hypot(cx - hx, cy - hy) < HERO_CLEAR[k] for k, (hx, hy) in HEROES.items()):
                    continue
                near = min(math.hypot(cx - hx, cy - hy) / (HERO_CLEAR[k] * 2.6) for k, (hx, hy) in HEROES.items())
                h = height_field(cx, cy) * rng.uniform(0.45, 1.25) * float(np.clip(near, 0.32, 1.0))
                district = min(districts - 1, int((cx - X_MIN) / (X_MAX - X_MIN) * districts))
                tiers = 1 if h < 70 else (2 if h < 150 else 3)
                z, tw, td = 0.0, w, d
                for t in range(tiers):
                    top = h if t == tiers - 1 else z + h * (0.55 if t == 0 else 0.3)
                    masses[district].append(box(cx, cy, tw, td, z, top))
                    z, tw, td = top, tw * 0.74, td * 0.72
                # Window lights: sparse points on the two long facades.
                n = int(h / 9)
                if n:
                    zz = rng.uniform(6, h * 0.92, n)
                    yy = cy + rng.uniform(-d / 2, d / 2, n) * 0.9
                    side = np.where(rng.random(n) < 0.5, -1, 1)
                    pts = np.column_stack([cx + side * (w / 2 + 0.8), yy, zz])
                    keep = rng.random(n) < 0.55
                    if keep.any():
                        windows[district].append(pts[keep])
    return (
        [merge(m) for m in masses],
        [pv.PolyData(np.concatenate(w)) for w in windows],
    )


def empire_state():
    """Five stacked tiers: podium, shaft, setbacks, crown, mooring mast."""
    x, y = HEROES["esb"]
    return [
        box(x, y, 130, 60, 0, 25),
        box(x, y, 96, 52, 25, 250),
        box(x, y, 70, 40, 250, 300),
        box(x, y, 46, 30, 300, 320),
        merge(
            [
                pv.Cylinder(center=(x, y, 345), direction=(0, 0, 1), radius=9, height=50, resolution=16),
                pv.Cylinder(center=(x, y, 400), direction=(0, 0, 1), radius=1.6, height=86, resolution=8),
            ]
        ),
    ]


def twisted_prism(cx, cy, z0, z1, s0, s1, segments=10):
    """One WTC's shaft: a square whose corners chamfer into an octagon then a rotated square."""
    rings = []
    for i in range(segments + 1):
        t = i / segments
        size = s0 + (s1 - s0) * t
        rot = math.radians(45 * t)
        ring = []
        for k in range(4):
            a = rot + math.radians(45 + 90 * k)
            ring.append(
                (cx + size / math.sqrt(2) * math.cos(a), cy + size / math.sqrt(2) * math.sin(a), z0 + (z1 - z0) * t)
            )
        rings.append(ring)
    points = np.array([p for r in rings for p in r])
    faces = []
    for i in range(segments):
        for k in range(4):
            a, b = i * 4 + k, i * 4 + (k + 1) % 4
            faces += [3, a, b, b + 4, 3, a, b + 4, a + 4]
    faces += [4, 0, 3, 2, 1, 4, *(segments * 4 + k for k in range(4))]
    return pv.PolyData(points, faces).clean()


def one_wtc():
    x, y = HEROES["wtc"]
    shell = merge([box(x, y, 62, 62, 0, 57), twisted_prism(x, y, 57, 417, 62, 44)])
    core = box(x, y, 26, 26, 0, 430)
    slabs = merge(
        [
            box(x, y, 52 - 12 * (z - 57) / 360 * 0.6, 52 - 12 * (z - 57) / 360 * 0.6, z, z + 1.2)
            for z in range(60, 410, 9)
        ]
    )
    spire = merge(
        [
            box(x, y, 18, 18, 417, 432),
            pv.Cylinder(center=(x, y, 486), direction=(0, 0, 1), radius=1.8, height=110, resolution=10),
        ]
    )
    return shell, merge([core, slabs]), spire


def chrysler():
    x, y = HEROES["chrysler"]
    body = merge([box(x, y, 62, 62, 0, 60), box(x, y, 50, 50, 60, 200), box(x, y, 40, 40, 200, 240)])
    crown = []
    z = 240.0
    for i in range(6):
        r0, r1 = 22 - i * 3.2, 19 - i * 3.2
        crown.append(
            pv.Cone(center=(x, y, z + 7), direction=(0, 0, 1), height=14, radius=r0, resolution=8).triangulate()
        )
        crown.append(pv.Cylinder(center=(x, y, z + 3), direction=(0, 0, 1), radius=r1, height=6, resolution=8))
        z += 12
    spire = pv.Cone(center=(x, y, z + 23), direction=(0, 0, 1), height=46, radius=2.5, resolution=8)
    return body, merge(crown + [spire])


def park432():
    """Slender square tube with five open mechanical floors exposing the core."""
    x, y = HEROES["park432"]
    shells, core = [], box(x, y, 12, 12, 0, 426)
    bands = np.linspace(0, 426, 7)
    for a, b in itertools.pairwise(bands):
        shells.append(box(x, y, 28.5, 28.5, a + (0 if a == 0 else 6), b))
    return merge(shells), core


# --------------------------------------------------------------------------- 3D clip
def cam(position, focal, angle=38, up=(0, 0, 1)):
    return ArchCamera(position=position, focal_point=focal, up=up, projection="perspective", view_angle=angle)


CAMERAS = {
    "plan": cam((-150, 0, 3500), (-150, 0, 0), 40, up=(0, 1, 0)),
    "plan_push": cam((-150, -1100, 2700), (-150, 0, 0), 42, up=(0, 1, 0)),
    "rise": cam((-1150, -2500, 1050), (-150, 0, 80), 40),
    "rise_drift": cam((350, -2450, 820), (-50, 0, 110), 40),
    "esb": cam((640, -660, 540), (60, 40, 275), 40),
    "esb_orbit": cam((-460, -700, 560), (60, 40, 300), 42),
    "wtc": cam((-1020, -900, 260), (-1430, -260, 240), 40),
    "wtc_close": cam((-1180, -760, 300), (-1430, -260, 250), 38),
    "midtown": cam((150, -420, 210), (470, 300, 250), 42),
    "midtown_pass": cam((1180, -420, 330), (760, 200, 250), 44),
    "skyline": cam((-2500, -1050, 220), (-350, 120, 250), 34),
    "skyline_end": cam((-2350, -560, 230), (-450, 140, 270), 31),
}


def style(color, concept="solid", **kw):
    return ArchStyle(concept=concept, color=color, edge_color=kw.pop("edge", color), **kw)


def build_view(width, height, position):
    rng = np.random.default_rng(1811)  # the Commissioners' Plan year: a fixed, reproducible city
    masses, windows = generic_city(rng)
    script = ArchScript()
    parts = [
        ArchPart(
            "ground",
            ArchMesh.from_data(pv.Plane(center=(0, 0, -0.5), direction=(0, 0, 1), i_size=26000, j_size=26000)),
            style=style(GROUND, smooth_shading=False),
        ),
        ArchPart(
            "streets", ArchMesh.from_data(street_grid()), style=style(STREET, "wireframe", line_width=1.2, opacity=0.0)
        ),
    ]
    script.opacity("streets", 0.85, at=0.4, duration=2.6, easing="smooth")

    # District wave: wire frames rise first, solid mass fades in behind them.
    for i, (mass, lights) in enumerate(zip(masses, windows)):
        sunk = (0, 0, -float(mass.bounds[5]) - 4)
        mesh = ArchMesh.from_data(mass)
        parts += [
            ArchPart(f"wire-{i}", mesh, position=sunk, style=style(WIRE, "wireframe", line_width=1.0, opacity=0.55)),
            ArchPart(
                f"mass-{i}",
                mesh,
                position=sunk,
                style=style(MASS if i not in (0, 5) else MASS_FAR, opacity=0.0, smooth_shading=False),
            ),
            ArchPart(
                f"lights-{i}",
                ArchMesh.from_data(lights),
                position=sunk,
                style=style(GLOW, "points", point_size=4.0, opacity=0.0),
            ),
        ]
        at = 6.4 + 0.75 * i
        for kind in ("wire", "mass", "lights"):
            script.move(f"{kind}-{i}", (0, 0, 0), at=at, duration=2.4, easing="smooth")
        script.opacity(f"mass-{i}", 1.0, at=at + 1.2, duration=2.2, easing="smooth")
        script.opacity(f"wire-{i}", 0.12, at=at + 2.6, duration=2.0, easing="smooth")
        script.opacity(f"lights-{i}", 1.0, at=39.4 + 0.35 * i, duration=2.2, easing="smooth")
        script.highlight(f"mass-{i}", DUSK, at=39.0 + 0.35 * i, duration=2.2)

    # Landmarks share the same rise, then each gets its own engineered study.
    hero_parts = []
    for n, tier in enumerate(empire_state()):
        hero_parts.append(ArchPart(f"esb-{n}", ArchMesh.from_data(tier), style=style(HERO, smooth_shading=False)))
    shell, core, spire = one_wtc()
    hero_parts += [
        ArchPart("wtc-core", ArchMesh.from_data(core), style=style(CORE, smooth_shading=False)),
        ArchPart("wtc-shell", ArchMesh.from_data(shell), style=style(HERO, smooth_shading=False)),
        ArchPart("wtc-spire", ArchMesh.from_data(spire), style=style(HERO, smooth_shading=False)),
    ]
    body, crown = chrysler()
    tube, column = park432()
    hero_parts += [
        ArchPart("chrysler-body", ArchMesh.from_data(body), style=style(HERO, smooth_shading=False)),
        ArchPart("chrysler-crown", ArchMesh.from_data(crown), style=style(HERO, smooth_shading=False)),
        ArchPart("park-core", ArchMesh.from_data(column), style=style(CORE, smooth_shading=False)),
        ArchPart("park-tube", ArchMesh.from_data(tube), style=style(HERO, smooth_shading=False)),
    ]
    hero_parts = [ArchPart(p.id, p.mesh, position=(0, 0, -560), style=p.style) for p in hero_parts]
    parts += hero_parts
    for k, p in enumerate(hero_parts):
        script.move(p.id, (0, 0, 0), at=9.0 + 0.12 * k, duration=3.4, easing="smooth")

    # Empire State: exploded axonometric, gold accent, reassemble.
    esb = [f"esb-{n}" for n in range(5)]
    script.highlight(esb, GOLD, at=16.4, duration=0.8)
    # explode() measures from the sunken start pose, so the stack is opened with absolute moves.
    for n, part in enumerate(esb):
        script.move(part, (0, 0, 24.0 * n), at=17.0 + 0.08 * n, duration=1.8, easing="smooth")
        script.move(part, (0, 0, 0), at=20.4 + 0.08 * (4 - n), duration=1.6, easing="smooth")
    script.highlight(esb, HERO, at=22.4, duration=0.8)

    # One WTC: a vertical cut sweeps in to the centreline, reveals core + slabs, then closes.
    wx, wy = HEROES["wtc"]
    script.section("wtc-shell", (wx, wy - 80, 0), (0, -1, 0), cap=True, contour=True, at=24.6, duration=0.01)
    script.section("wtc-shell", (wx, wy, 0), (0, -1, 0), cap=True, contour=True, at=24.7, duration=2.4, easing="smooth")
    script.section(
        "wtc-shell", (wx, wy - 80, 0), (0, -1, 0), cap=True, contour=True, at=29.4, duration=1.4, easing="smooth"
    )
    script.highlight("wtc-core", GOLD, at=25.4, duration=1.0)

    # Midtown: crowns warm up as the camera passes.
    script.highlight("chrysler-crown", GOLD, at=32.0, duration=1.2)
    script.highlight("park-core", GOLD, at=34.4, duration=1.0)

    # Camera path: one continuous move per beat, gentle drifts during holds.
    for name, at, duration in (
        ("plan_push", 0.0, 6.0),
        ("rise", 6.0, 3.6),
        ("rise_drift", 9.6, 5.2),
        ("esb", 14.8, 2.2),
        ("esb_orbit", 17.0, 5.8),
        ("wtc", 22.8, 2.0),
        ("wtc_close", 24.8, 6.0),
        ("midtown", 30.8, 2.2),
        ("midtown_pass", 33.0, 6.0),
        ("skyline", 39.0, 2.2),
        ("skyline_end", 41.2, 3.8),
    ):
        script.camera_to(CAMERAS[name], at=at, duration=duration, easing="smooth")
    script.wait(0)

    return ArchChamp(parts, script, width=width, height=height, position=position, units="m", camera=CAMERAS["plan"])


# --------------------------------------------------------------------------- 2D layer
def backdrop(width, height):
    """Night sky gradient with a low cyan horizon glow; drawn once."""
    y = np.linspace(0, 1, height)[:, None, None]
    x = np.linspace(-1, 1, width)[None, :, None]
    top, low = hex_rgb(C.background), hex_rgb(mix(C.background, C.surface, 0.9))
    image = top + (low - top) * y**1.6
    horizon = np.exp(-(((y - 0.62) / 0.16) ** 2)) * np.exp(-((x / 1.1) ** 2))
    image = image + hex_rgb(C.primary) * 0.09 * horizon
    vignette = np.clip(1 - 0.45 * (x**2 * 0.6 + (y - 0.5) ** 2 * 1.4), 0.4, 1)
    image = np.broadcast_to(image * vignette, (height, width, 3))
    return PILImage.fromarray(np.clip(image, 0, 255).astype(np.uint8), "RGB")


def caption(scene, area, eyebrow, title, at, until, anchor="bottom_left"):
    """A two-line tag pinned to a safe-area corner. The only copy on screen."""
    box = area.fit(area.width * 0.42, 190, align=anchor)
    head = theme.fit(title, box, role="heading")
    tag = theme.text(eyebrow, role="label", color="primary", tracking=0.18)
    left, bottom = box.point(anchor)
    head.move_to(left + head.bounds.width / 2, bottom - head.bounds.height / 2)
    tag.move_to(left + tag.bounds.width / 2, head.bounds.top - 14 - tag.bounds.height / 2)
    scene.reveal(tag, head, at=at, stagger=0.12)
    if until is not None:
        scene.play_at(until, FadeOut(tag), FadeOut(head), run_time=0.7)


def build():
    with theme.use():
        scene = Scene(theme.canvas())
        bounds, area = scene.canvas.bounds, scene.canvas.safe_area()
        w, h = scene.canvas.width, scene.canvas.height
        scene.add(Image.from_source(backdrop(w, h), width=w, height=h, position=bounds.center))
        scene.add(build_view(w, h, bounds.center))

        # Opening title, centred over the plan.
        column = area.fit(1300, 360)
        title = theme.fit("New York City", column, role="display")
        eyebrow = theme.text("AN ENGINEERED SKYLINE", role="label", color="primary", tracking=0.22)
        eyebrow.next_to(title, direction="up", gap=26)
        scene.reveal(eyebrow, title, at=0.8, stagger=0.15)
        scene.play_at(5.2, FadeOut(eyebrow), FadeOut(title), run_time=0.9)

        caption(scene, area, "1931 · 443 M", "Empire State", 16.2, 22.2)
        caption(scene, area, "2014 · 541 M", "One World Trade", 24.2, 30.2)
        caption(scene, area, "1930 · 2015", "Chrysler to 432 Park", 31.8, 38.4)
        caption(scene, area, "MANHATTAN", "Built upward", 41.4, None)
        scene.wait_until(DURATION)
    return scene


# --------------------------------------------------------------------------- CLI
def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="build the scene and print key facts")
    mode.add_argument("--frame", type=float, metavar="T", help="save one still at source time T")
    mode.add_argument("--audit", action="store_true", help="run the design audit")
    mode.add_argument("--preview", action="store_true", help="export a short low-res range")
    mode.add_argument("--full", action="store_true", help="full 1080p export (explicit)")
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--duration", type=float, default=6.0)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--antialias", type=int, default=1, choices=(1, 2, 3, 4))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    scene = build()
    print(f"duration={scene.duration}s canvas={scene.canvas.width}x{scene.canvas.height}", flush=True)
    if args.check:
        return
    if args.audit:
        from faceless_champ import design_audit

        print(design_audit(scene))
        return
    size = (args.width, round(args.width * 9 / 16))
    out = ROOT / "output"
    if args.frame is not None:
        from faceless_champ.preview import save_frame

        path = args.output or out / f"frame-{args.frame:g}.png"
        save_frame(scene, args.frame, path, size=size, overwrite=True)
        print(path)
        return
    if args.full:
        settings = ExportSettings(width=1920, height=1080, fps=30, antialias=2, crf=16, preset="slow")
        path, start, end = args.output or out / "nyc-architecture.mp4", 0.0, None
    else:
        settings = ExportSettings(width=size[0], height=size[1], fps=args.fps, antialias=args.antialias, crf=20)
        start = args.start
        end = min(DURATION, start + args.duration)
        path = args.output or out / f"preview-{start:g}-{end:g}.mp4"
    out.mkdir(parents=True, exist_ok=True)
    with ExportProgress() as progress:
        render(scene, path, settings=settings, start_time=start, end_time=end, overwrite=True, progress=progress)
    print(path)


if __name__ == "__main__":
    main()
