"""Deterministic teaching geometry in metres; no model download or solver."""

import math
from functools import lru_cache

import numpy as np
import pyvista as pv

from faceless_champ import ArchMesh, ArchPart, ArchStyle

NAVY = "#0B1020"
CYAN = "#57D8EE"
AMBER = "#FFC36A"
ORANGE = "#F88C55"
WHITE = "#F0F6FF"
MUTED = "#95ABC4"
BLUE = "#69A1BA"


def rotate_xy(points, angle):
    a = math.radians(angle)
    c, s = math.cos(a), math.sin(a)
    return [(x * c - y * s, x * s + y * c) for x, y in points]


def prism(points, bottom, top):
    """Closed polygon prism; authored polygons are convex and counterclockwise."""
    n = len(points)
    vertices = [(x, y, bottom) for x, y in points] + [(x, y, top) for x, y in points]
    faces = [n, *reversed(range(n)), n, *range(n, 2 * n)]
    for i in range(n):
        j = (i + 1) % n
        faces.extend((4, i, j, j + n, i + n))
    return pv.PolyData(np.asarray(vertices, dtype=float), faces)


def hexagon(radius):
    return [(radius * math.cos(i * math.pi / 3), radius * math.sin(i * math.pi / 3)) for i in range(6)]


def wing_outline(length=60, width=11, angle=0):
    points = [(7, -width)]
    points += [
        (length - width + width * math.cos(a), width * math.sin(a)) for a in np.linspace(-math.pi / 2, math.pi / 2, 9)
    ]
    points.append((7, width))
    return rotate_xy(points, angle)


def batch(meshes):
    return pv.merge(meshes, merge_points=False).extract_surface(algorithm="dataset_surface")


def cylinder(start, end, radius=0.8, resolution=8):
    a, b = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    return pv.Cylinder(
        center=(a + b) / 2,
        direction=b - a,
        radius=radius,
        height=np.linalg.norm(b - a),
        resolution=resolution,
        capping=True,
    ).clean()


def arrow(start, end, radius=1):
    a, b = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    return pv.Arrow(
        start=a,
        direction=b - a,
        scale=float(np.linalg.norm(b - a)),
        shaft_radius=radius / np.linalg.norm(b - a),
        tip_radius=3 * radius / np.linalg.norm(b - a),
        tip_length=0.22,
        shaft_resolution=10,
        tip_resolution=10,
    )


def curve(points, radius=0.5):
    return pv.lines_from_points(np.asarray(points, dtype=float)).tube(radius=radius, n_sides=6)


def part(id, mesh, color=CYAN, concept="solid", opacity=1, explode=(0, 0, 0)):
    sealed = mesh if isinstance(mesh, ArchMesh) else ArchMesh.from_data(mesh)
    return ArchPart(
        id,
        sealed,
        style=ArchStyle(
            concept=concept, color=color, edge_color=color, opacity=opacity, line_width=1.1, smooth_shading=False
        ),
        explode_vector=explode,
    )


@lru_cache(maxsize=1)
def geometry():
    """Shared sealed meshes. Setbacks/member sizes are illustrative, never surveyed."""
    raw = {}
    cores = []
    for tier in range(24):
        cores.append(prism(hexagon(12.8 - tier * 0.34), tier * 25, (tier + 1) * 25))
    raw["core"] = batch(cores)
    for wing in range(3):
        angle = wing * 120 + 90
        shells, walls, columns, bands = [], [], [], []
        for tier in range(24):
            cut = (tier + wing) // 3
            length = max(13, 61 - cut * 5.8)
            width = 5 + 6 * (length / 61)
            z0, z1 = tier * 25, (tier + 1) * 25
            shells.append(prism(wing_outline(length, width, angle), z0, z1))
            for y in (-4.2, 4.2):
                walls.append(
                    prism(
                        rotate_xy(
                            [(7, y - 0.65), (length - 7, y - 0.65), (length - 7, y + 0.65), (7, y + 0.65)], angle
                        ),
                        z0,
                        z1,
                    )
                )
            for x in np.arange(15, length - 3, 9):
                for y in (-width + 1, width - 1):
                    px, py = rotate_xy([(x, y)], angle)[0]
                    columns.append(cylinder((px, py, z0), (px, py, z1), 0.85))
            for z in (z0 + 8, z0 + 16, z1):
                outline = wing_outline(length + 0.12, width + 0.12, angle)
                bands.append(pv.lines_from_points(np.array([(x, y, z) for x, y in [*outline, outline[0]]])))
        key = "abc"[wing]
        raw[f"wing-{key}"] = batch(shells)
        raw[f"walls-{key}"] = batch(walls)
        raw[f"columns-{key}"] = batch(columns)
        raw[f"bands-{key}"] = batch(bands)
    raw["crown"] = pv.Cone(center=(0, 0, 669), direction=(0, 0, 1), height=138, radius=6, resolution=12, capping=True)
    raw["spire"] = cylinder((0, 0, 720), (0, 0, 828), 0.9, 12)
    raw["raft"] = batch(
        [prism(wing_outline(64, 14, i * 120 + 90), -8.7, -5) for i in range(3)] + [prism(hexagon(16), -8.7, -5)]
    )
    piles = []
    # 3 wings × 8 radial rows × 8 columns = 192; arrangement is schematic.
    for i in range(3):
        for x in np.linspace(10, 57, 8):
            for y in np.linspace(-10, 10, 8):
                px, py = rotate_xy([(x, y)], i * 120 + 90)[0]
                piles.append(cylinder((px, py, -51.7), (px, py, -8.7), 0.6))
    raw["piles"] = batch(piles)
    raw["soil"] = pv.Cube(center=(0, 0, -31), x_length=158, y_length=138, z_length=62)
    raw["pump-pipe"] = cylinder((-17, -20, 0), (-17, -20, 606), 1.1)
    raw["pump-packet"] = pv.Sphere(radius=3.4, center=(-17, -20, 0), theta_resolution=12, phi_resolution=10)
    raw["ground"] = pv.Plane(
        center=(0, 0, -0.1), direction=(0, 0, 1), i_size=145, j_size=145, i_resolution=1, j_resolution=1
    )
    # Broader teaching proportions preserve the three-lobed silhouette at video scale.
    for mesh in raw.values():
        mesh.points[:, :2] *= 1.25
    return {key: ArchMesh.from_data(mesh) for key, mesh in raw.items()}


def tower(mode="wireframe", structure=False, facade=False):
    g = geometry()
    parts = [part("core", g["core"], AMBER if structure else CYAN, "solid" if structure else mode)]
    for i, key in enumerate("abc"):
        angle = math.radians(i * 120 + 90)
        outward = (22 * math.cos(angle), 22 * math.sin(angle), 0)
        if structure:
            parts += [
                part(f"walls-{key}", g[f"walls-{key}"], CYAN, explode=outward),
                part(f"columns-{key}", g[f"columns-{key}"], MUTED, explode=outward),
            ]
        else:
            parts.append(
                part(f"wing-{key}", g[f"wing-{key}"], BLUE if facade else CYAN, mode, 0.8 if facade else 1, outward)
            )
        if facade:
            parts.append(part(f"bands-{key}", g[f"bands-{key}"], "#7FBDD4"))
    parts += [
        part("crown", g["crown"], MUTED if facade else CYAN, mode),
        part("spire", g["spire"], WHITE if facade else CYAN, mode),
    ]
    return parts


def floor_plan():
    return [part("plan-core", prism(hexagon(12.8), 0, 5), AMBER)] + [
        part(
            f"plan-{key}",
            prism(wing_outline(angle=i * 120 + 90), 0, 2),
            CYAN,
            "isometric",
            0.65,
            (*rotate_xy([(16, 0)], i * 120 + 90)[0], 0),
        )
        for i, key in enumerate("abc")
    ]


def foundation():
    g = geometry()
    return [
        part("raft", g["raft"], AMBER),
        part("piles", g["piles"], CYAN),
        part("soil", g["soil"], "#28364B", opacity=0.3),
    ]


MODEL_FACTS = {
    "height_m": 828,
    "raft_thickness_m": 3.7,
    "pile_count": 192,
    "pile_diameter_m": 1.5,
    "pile_length_m": 43,
    "pump_height_m": 606,
    "geometry": "simplified procedural teaching model",
    "fields": "illustrative; no solver",
}
