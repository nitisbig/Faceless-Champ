"""Shared refined teaching geometry and public ArchChamp viewport scenes."""

import itertools
from dataclasses import dataclass, replace
from functools import lru_cache
from math import pi

import numpy as np
import pyvista as pv

from faceless_champ import ArchCamera, ArchChamp, ArchMesh, ArchPart, ArchScript, ArchStyle, Canvas, Scene

from . import ASSETS, OUTPUT
from . import physics as p

CYAN, BLUE, PURPLE = "#3886FF", "#3973D9", "#568AFF"
WHITE, ORANGE = "#E4EBF7", "#FF304F"
MODELS = ASSETS / "11_3D_Models"


def lines(points, closed=False):
    points = np.asarray(points, dtype=float)
    if closed:
        points = np.vstack((points, points[0]))
    return pv.lines_from_points(points)


def circle(center, radius, normal="z", count=64):
    a = np.linspace(0, 2 * pi, count, endpoint=False)
    xyz = np.column_stack((np.cos(a) * radius, np.sin(a) * radius, np.zeros(count)))
    if normal == "y":
        xyz = xyz[:, (0, 2, 1)]
    elif normal == "x":
        xyz = xyz[:, (2, 0, 1)]
    return lines(xyz + np.asarray(center), True)


def merge(meshes):
    meshes = list(meshes)
    return meshes[0].merge(meshes[1:], merge_points=False) if len(meshes) > 1 else meshes[0]


def source(name, closed=False):
    mesh = pv.read(MODELS / f"roadster_{name}.obj").copy()
    mesh.clear_data()
    # Imported pack declares +Y right. Reflect once to the FLU body frame, then
    # reverse winding, so subsequent cross products and outward normals agree.
    mesh.points[:, 1] *= -1
    mesh = mesh.flip_faces()
    mesh.translate((0, 0, -p.CG_HEIGHT), inplace=True)
    mesh = mesh.clean().triangulate()
    if closed:
        mesh = mesh.fill_holes(20).clean().triangulate()
        if not mesh.is_manifold and name == "canopy":
            mesh = pv.PolyData(mesh.points).delaunay_3d().extract_surface(algorithm="dataset_surface").triangulate()
        if not mesh.is_manifold:
            raise ValueError(f"Refined {name} must be manifold before capped cuts")
    return mesh.compute_normals(auto_orient_normals=closed, split_vertices=False)


def part(id, mesh, color, concept="solid", opacity=1, width=1.5, explode=(0, 0, 0)):
    return ArchPart(
        id,
        ArchMesh.from_data(mesh),
        style=ArchStyle(
            concept=concept,
            color=color,
            edge_color=color,
            opacity=opacity,
            line_width=width,
            smooth_shading=concept != "wireframe",
        ),
        explode_vector=explode,
    )


def edges(mesh, angle=30):
    return mesh.extract_feature_edges(
        feature_angle=angle, boundary_edges=True, non_manifold_edges=True, manifold_edges=False
    )


@lru_cache(maxsize=1)
def components():
    body, canopy = source("body", True), source("canopy", True)
    chassis = source("chassis", True)
    tires, rims = source("tires", True), source("rims")
    suspension_adjustment = -p.CG_HEIGHT - tires.bounds[4]
    tires.translate((0, 0, suspension_adjustment), inplace=True)
    rims.translate((0, 0, suspension_adjustment), inplace=True)
    tanks = source("pressure_tanks", True)
    fan_cases, rotors = [], []
    for x in (-0.58, 0.58):
        for y in (-0.47, 0.47):
            center = (x, y, -0.46)
            fan_cases += [
                pv.Cylinder(center=center, direction=(0, 0, 1), radius=0.30, height=0.11, resolution=48).triangulate()
            ]
            blades = [
                pv.Cylinder(
                    center=(x, y, -0.525), direction=(0, 0, 1), radius=0.075, height=0.025, resolution=24
                ).triangulate()
            ]
            for angle in np.arange(0, 360, 45):
                blade = pv.Cube(center=(x + 0.15, y, -0.53), x_length=0.24, y_length=0.065, z_length=0.015)
                blade.rotate_z(angle, point=(x, y, 0), inplace=True)
                blades.append(blade.triangulate())
            rotors.append(merge(blades))
    skirts = merge(
        pv.Cube(center=center, x_length=length[0], y_length=length[1], z_length=0.16).triangulate()
        for center, length in [
            ((0, -0.80, -0.48), (2.7, 0.035)),
            ((0, 0.80, -0.48), (2.7, 0.035)),
            ((-1.37, 0, -0.48), (0.035, 1.6)),
            ((1.37, 0, -0.48), (0.035, 1.6)),
        ]
    )
    # Ten mounts are explicitly schematic, including opposing attitude jets.
    mounts = [(-2.18, y, -0.12, (-1, 0, 0)) for y in (-0.62, -0.22, 0.22, 0.62)]
    mounts += [(x, y, -0.27, (0, 0, -1)) for x in (-1.25, 1.25) for y in (-0.73, 0.73)]
    mounts += [(0, y, 0.12, (0, 0, 1)) for y in (-0.82, 0.82)]
    nozzles = merge(
        pv.Cone(
            center=(x, y, z), direction=direction, height=0.24, radius=0.12, resolution=24, capping=True
        ).triangulate()
        for x, y, z, direction in mounts
    )
    # Deliberate silhouette rings replace every triangulated tire edge.
    wheel_rings = []
    for x in (-1.60, 1.35):
        for y in (-0.95, 0.95):
            for r in (0.37, 0.25):
                wheel_rings.append(circle((x, y, -0.28 + suspension_adjustment), r, normal="y"))
    return {
        "body": body,
        "canopy": canopy,
        "chassis": chassis,
        "tires": tires,
        "rims": rims,
        "tanks": tanks,
        "fan_cases": merge(fan_cases),
        "rotors": rotors,
        "skirts": skirts,
        "nozzles": nozzles,
        "contours": merge([edges(body, 25), edges(canopy, 30), *wheel_rings]),
    }


def vehicle(technical=False, exploded=False, prefix=""):
    c = components()
    specs = [
        ("body", WHITE, "solid", 0.20 if technical else 1, (0, 0, 1.6)),
        ("canopy", "#080F1C", "solid", 0.15 if technical else 0.85, (0, 0, 2.0)),
        ("chassis", BLUE, "solid", 0.38 if technical else 0.55, (0, 0, 0)),
        ("tires", "#15202D", "solid", 1, (0, 0.38, 0)),
        ("rims", "#819FB1", "solid", 1, (0, 0.38, 0)),
        ("tanks", PURPLE, "solid", 0.85 if technical else 0.12, (0, 0, 0.5)),
        ("fan_cases", BLUE, "solid", 0.55 if technical else 0.06, (0, 0, -0.65)),
        ("skirts", CYAN, "solid", 0.55 if technical else 0.08, (0, 0, -0.40)),
        ("nozzles", ORANGE, "solid", 0.9 if technical else 0.14, (0, 0, -0.25)),
        ("contours", CYAN, "wireframe", 1, (0, 0, 1.6)),
    ]
    result = [
        part(prefix + id, c[id], color, concept, opacity, 2.1, explode if exploded else (0, 0, 0))
        for id, color, concept, opacity, explode in specs
        if not (exploded and id in {"tires", "rims"})
    ]
    if exploded:
        centers = np.array([(x, y) for x in (-1.6, 1.35) for y in (-0.95, 0.95)])
        for name, color in (("tires", "#15202D"), ("rims", "#819FB1")):
            mesh = c[name]
            xy = mesh.cell_centers().points[:, :2]
            nearest = np.argmin(((xy[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2), axis=1)
            for i, center in enumerate(centers):
                group = mesh.extract_cells(np.flatnonzero(nearest == i)).extract_surface(algorithm="dataset_surface")
                result.append(part(f"{prefix}{name}{i}", group, color, explode=(0, np.sign(center[1]) * 0.9, 0)))
    if not technical:
        hidden = {"tanks", "fan_cases", "skirts", "nozzles"}
        result = [
            replace(a, style=replace(a.style, opacity=0 if a.id.removeprefix(prefix) in hidden else 1)) for a in result
        ]
    return result


def road(angle=0):
    plane = pv.Cube(center=(0, 0, -p.CG_HEIGHT - 0.09), x_length=13, y_length=4.5, z_length=0.18).triangulate()
    grid = [lines(((-6, y, -p.CG_HEIGHT), (6, y, -p.CG_HEIGHT))) for y in (-2, -1, 0, 1, 2)]
    grid += [lines(((x, -2, -p.CG_HEIGHT), (x, 2, -p.CG_HEIGHT))) for x in np.arange(-6, 6.1, 1)]
    plane.rotate_y(-angle, inplace=True)
    guides = merge(grid)
    guides.rotate_y(-angle, inplace=True)
    return [part("road", plane, "#101B27", opacity=0.8), part("road_grid", guides, "#214357", "wireframe", 0.75, 0.8)]


def ramp(top_only=False):
    radius = p.RADIUS + p.CG_HEIGHT
    angles = np.linspace(pi / 2 if top_only else 0, pi, 140)
    center = np.array((0, 0, radius))
    points = np.array([(radius * np.sin(a), y, radius - radius * np.cos(a)) for a in angles for y in (-2.3, 2.3)])
    faces = [[2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2] for i in range(len(angles) - 1)]
    mesh = pv.PolyData(points, np.column_stack((np.full(len(faces), 4), faces)).ravel())
    rails = [lines(points[side::2]) for side in (0, 1)]
    rails += [lines(points[2 * i : 2 * i + 2]) for i in range(0, len(angles), 12)]
    if not top_only:
        rails += [lines(((-42, y, 0), (0, y, 0))) for y in (-2.3, 2.3)]
    del center
    centerline = lines([(radius * np.sin(a), 0, radius - radius * np.cos(a)) for a in angles])
    return [
        part("ramp", mesh, "#070B12", opacity=0.8),
        part("rails", merge(rails), CYAN, "wireframe", 1, 2.2),
        part("ramp_red", centerline, ORANGE, "wireframe", 1, 2.8),
    ]


def experiment_road():
    """A complete, finite C-shaped demonstration stage with two luminous rails."""
    radius = p.RADIUS + p.CG_HEIGHT
    angles = np.linspace(0, pi, 181)
    path = [(-23.0, 0.0), (0.0, 0.0)]
    path += [(radius * np.sin(a), radius - radius * np.cos(a)) for a in angles[1:]]
    path += [(-10.0, 2 * radius)]
    points = np.array([(x, y, z) for x, z in path for y in (-2.6, 2.6)])
    faces = np.array([[4, 2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2] for i in range(len(path) - 1)])
    surface = pv.PolyData(points, faces.ravel())
    borders = merge([lines(points[side::2]) for side in (0, 1)])
    # Offset the line toward the inside of the curve to avoid depth fighting.
    red_path = [(-23, -0.015, 0.045), (0, -0.015, 0.045)]
    red_path += [((radius - 0.045) * np.sin(a), -0.015, radius - (radius - 0.045) * np.cos(a)) for a in angles[1:]]
    red_path += [(-10, -0.015, 2 * radius - 0.045)]
    middle = lines(red_path)
    # Sparse structural ties show the road's depth without a dense wire grid.
    ties = merge(lines(points[2 * i : 2 * i + 2]) for i in (0, 1, 26, 51, 76, 101, 126, 151, 181, 182))
    return [
        part("stage", surface, "#101B2B", opacity=1),
        part("stage_blue", borders, "#4B9CFF", "wireframe", 1, 5.0),
        part("stage_red", middle, "#FF244D", "wireframe", 1, 5.2),
        part("stage_ties", ties, "#345B90", "wireframe", 0.8, 1.5),
    ]


@dataclass
class View:
    component: ArchChamp
    scene: Scene
    duration: float


def tracks(script, ids, samples):
    for (ta, pa, ra), (tb, pb, rb) in itertools.pairwise(samples):
        if not np.allclose(pa, pb):
            script.move(ids, tuple(pb), at=ta, duration=tb - ta)
        if not np.allclose(ra, rb):
            script.rotate(ids, tuple(rb), at=ta, duration=tb - ta)
    script.wait(max(0, samples[-1][0] - script.duration))


HOOK_DURATION = 6.76


def hook_state(time):
    local = p.clamp(time, 0, HOOK_DURATION)
    clock = 1.1 + (p.RELEASE_TIME + 0.7 - 1.1) * local / HOOK_DURATION
    return "hook-establish", local, clock


def make_view(mode):
    script = ArchScript()
    camera = ArchCamera((7, -10, 5), (0, 0, 0), projection="perspective", view_angle=32, zoom=1.35)
    duration = 1.0
    if mode == "hook-establish":
        duration = HOOK_DURATION
        parts = vehicle() + experiment_road()
        ids = tuple(a.id for a in parts if not a.id.startswith("stage"))
        first = p.replay(hook_state(0)[2])
        parts = [replace(a, position=first.position, rotation=first.rotation) if a.id in ids else a for a in parts]
        samples = []
        for t in np.linspace(0, duration, 73):
            state = p.replay(hook_state(float(t))[2])
            samples.append((float(t), state.position, state.rotation))
        tracks(script, ids, samples)
        # Establish the whole apparatus. Both camera endpoints retain a generous
        # margin around the road, including its approach and upper return.
        camera = ArchCamera((-13, -53, 28), (-3, 0, 12.6), projection="perspective", view_angle=35, zoom=1.05)
        script.camera_to(
            ArchCamera((-8, -51, 26), (-3, 0, 12.6), projection="perspective", view_angle=35, zoom=1.05),
            at=0,
            duration=duration,
            easing="smooth",
        )
    elif mode in {"side", "top", "front"}:
        parts = vehicle(True)
        script.opacity(("body", "canopy"), 0.04, at=0, duration=0.1)
        camera = {
            "side": ArchCamera((0, -10, 0), (0, 0, 0), zoom=2.3),
            "top": ArchCamera((0, 0, 10), (0, 0, 0), up=(1, 0, 0), zoom=1.1),
            "front": ArchCamera((10, 0, 0), (0, 0, 0), zoom=2.3),
        }[mode]
        script.wait(1)
    elif mode in {"hero", "model", "assembly", "fans", "control"}:
        parts = vehicle(mode != "hero", mode == "assembly")
        duration = 12.0
        if mode == "hero":
            script.camera_to(
                ArchCamera((6.4, -10.2, 3.4), (0, 0, 0), projection="perspective", view_angle=32, zoom=1.5),
                at=0,
                duration=12,
                easing="smooth",
            )
        elif mode == "assembly":
            for item in parts:
                if item.id != "tires" and item.id != "rims":
                    script.explode(item.id, 0.8, at=2, duration=4, easing="smooth")
            script.opacity("body", 0.08, at=0, duration=2)
            script.opacity("contours", 0.2, at=2, duration=4)
            for item in parts:
                if item.id not in {"tires", "rims"}:
                    script.explode(item.id, 0, at=7, duration=3, easing="smooth")
            camera = ArchCamera((7, -10, 5), (0, 0, 0.2), zoom=1.55)
        elif mode == "fans":
            camera = ArchCamera((5, -7, -5), (0, 0, -0.2), zoom=2.5)
            script.opacity(("body", "canopy", "contours"), 0.06, at=0, duration=1)
            script.section("chassis", (0, 0, -0.23), normal=(0, 0, 1), cap=True, at=0, duration=2)
            script.move("skirts", (0, 0, -0.14), at=0.2, duration=1.8, easing="smooth")
            for i, rotor in enumerate(components()["rotors"]):
                center = rotor.center
                centered = rotor.copy().translate(-np.asarray(center))
                parts.append(
                    ArchPart(
                        f"rotor{i}", ArchMesh.from_data(centered), position=tuple(center), style=ArchStyle(color=CYAN)
                    )
                )
                script.rotate(f"rotor{i}", (0, 0, 1080), at=0, duration=12)
            field = pv.Plane(
                center=(0, 0, -0.61), direction=(0, 0, 1), i_size=2.6, j_size=1.6, i_resolution=40, j_resolution=24
            )
            xy = np.abs(field.points[:, :2])
            rim = np.clip(np.maximum((xy[:, 0] - 1) / 0.3, (xy[:, 1] - 0.5) / 0.3), 0, 1)
            field.point_data["pressure_kPa"] = 84.648 + 16.677 * rim
            parts.append(
                ArchPart(
                    "pressure_field",
                    ArchMesh.from_data(field),
                    style=ArchStyle(
                        concept="heatmap", scalars="pressure_kPa", clim=(84.648, 101.325), cmap="Blues", opacity=0.45
                    ),
                )
            )
        elif mode == "control":
            camera = ArchCamera((7, -10, 5), (0, 0, 0), zoom=2.0)
            script.opacity(("body", "canopy"), 0.08, at=0, duration=1)
            ids = tuple(a.id for a in parts)
            parts = [ArchPart(a.id, a.mesh, a.position, (12, 0, 0), a.scale, a.style, a.explode_vector) for a in parts]
            samples = [
                (float(t), (0, 0, 0), (12 * (1 - p.roll(t, duration=2)["theta"] / pi), 0, 0))
                for t in np.linspace(0, 2, 33)
            ]
            tracks(script, ids, samples)
            parts.append(part("target_attitude", components()["contours"], WHITE, "wireframe", 0.2, 1))
        elif mode == "model":
            camera = ArchCamera((7, -10, 5), (0, 0, 0), projection="perspective", view_angle=32, zoom=2.65)
        script.wait(max(0, duration - script.duration))
    elif mode == "slope":
        parts = vehicle() + road()
        ids = tuple(item.id for item in parts)
        script.rotate(ids, (0, -90, 0), at=0, duration=90)
        camera = ArchCamera((0, -18, 2), (0, 0, 0), zoom=4.1)
        duration = 90
    elif mode == "wall":
        parts = vehicle(True) + road(90)
        ids = tuple(item.id for item in parts if not item.id.startswith("road"))
        # Initial Euler orientation is fixed before sampling starts.
        parts = [
            ArchPart(
                x.id, x.mesh, x.position, (0, -90, 0) if x.id in ids else x.rotation, x.scale, x.style, x.explode_vector
            )
            for x in parts
        ]
        script.move(ids, (0, 0, 3), at=3, duration=9)
        camera = ArchCamera((0, -18, 1), (0, 0, 1), zoom=2.35)
        script.camera_to(ArchCamera((0, -18, 4), (0, 0, 4), zoom=2.35), at=3, duration=9)
        duration = 12
    elif mode == "loop":
        parts = vehicle(True) + ramp(True)
        ids = tuple(x.id for x in parts if x.id not in {"ramp", "rails", "ramp_red"})
        initial = p.loop(0)
        parts = [
            ArchPart(
                x.id,
                x.mesh,
                tuple(initial["position"]) if x.id in ids else x.position,
                x.rotation,
                x.scale,
                x.style,
                x.explode_vector,
            )
            for x in parts
        ]
        samples = [(float(a), p.loop(a)["position"], p.loop(a)["rotation"]) for a in np.linspace(0, pi, 65)]
        tracks(script, ids, samples)

        def follow(position):
            x, _, z = position
            return ArchCamera((x + 1, -36, z + 0.3), (x + 1, 0, z - 0.8), zoom=6.4)

        camera = follow(initial["position"])
        for (ta, _, _), (tb, position, _) in itertools.pairwise(samples):
            script.camera_to(follow(position), at=ta, duration=tb - ta)
        duration = pi
    elif mode == "replay":
        parts = vehicle() + ramp()
        ground = pv.Cube(center=(-15, 0, -0.15), x_length=66, y_length=5, z_length=0.3).triangulate()
        parts.append(part("ground", ground, "#0F1A26", opacity=0.65))
        ids = tuple(x.id for x in parts if x.id not in {"ramp", "rails", "ramp_red", "ground"})
        first = p.replay(0)
        parts = [
            ArchPart(
                x.id,
                x.mesh,
                first.position if x.id in ids else x.position,
                x.rotation,
                x.scale,
                x.style,
                x.explode_vector,
            )
            for x in parts
        ]
        samples = [
            (float(t), p.replay(t).position, p.replay(t).rotation)
            for t in sorted(
                {
                    *np.linspace(0, p.REPLAY_TIME, 140),
                    p.RELEASE_TIME,
                    p.RELEASE_TIME + p.ROLL_TIME / 2,
                    p.RELEASE_TIME + p.ROLL_TIME,
                }
            )
        ]
        tracks(script, ids, samples)

        def follow_replay(position, t):
            position = np.asarray(position)
            offset = np.array((8 + 2 * np.sin(t * 0.5), -22, 7))
            return ArchCamera(
                tuple(position + offset), tuple(position), projection="perspective", view_angle=40, zoom=1.15
            )

        camera = follow_replay(first.position, 0)
        for (ta, _, _), (tb, position, _) in itertools.pairwise(samples):
            script.camera_to(follow_replay(position, tb), at=ta, duration=tb - ta)
        duration = p.REPLAY_TIME
    elif mode == "roll":
        parts = vehicle(True)
        parts = [
            replace(
                a,
                style=replace(
                    a.style,
                    opacity=0 if a.id in {"body", "canopy"} else 1,
                    concept="wireframe" if a.id == "chassis" else a.style.concept,
                ),
            )
            for a in parts
        ]
        ids = tuple(x.id for x in parts)
        parts = [ArchPart(x.id, x.mesh, x.position, (0, -180, 0), x.scale, x.style, x.explode_vector) for x in parts]
        samples = [(float(t), (0, 0, 0), (p.roll(t)["theta"] * 180 / pi, -180, 0)) for t in np.linspace(0, 1.6, 49)]
        tracks(script, ids, samples)
        camera = ArchCamera((10, 0, 0.05), (0, 0, 0), zoom=2.6)
        duration = 1.6
    elif mode == "tanks":
        parts = vehicle(True)
        script.opacity(("body", "canopy", "contours"), 0.025, at=0, duration=1)
        script.section("tanks", (0, 0, 0), normal=(0, -1, 0), cap=True, at=0, duration=3)
        camera = ArchCamera((4, -7, 4), (0, 0, 0), zoom=2.4)
        duration = 5
        script.wait(2)
    elif mode == "nozzle":
        vessel = (
            pv.Cylinder(center=(-1.2, 0, 0), direction=(1, 0, 0), radius=0.56, height=2.8, resolution=64)
            .clean()
            .triangulate()
        )
        bell = (
            pv.Cone(center=(0.9, 0, 0), direction=(-1, 0, 0), height=1.3, radius=0.68, resolution=64)
            .clean()
            .triangulate()
        )
        pipe = pv.Cylinder(
            center=(0.25, 0, 0), direction=(1, 0, 0), height=0.6, radius=0.13, resolution=32
        ).triangulate()
        parts = [
            part("vessel", vessel, PURPLE, opacity=0.5),
            part("bell", bell, "#A9C8D8", opacity=0.8),
            part("pipe", pipe, BLUE),
            part("outline", edges(merge((vessel, bell, pipe))), CYAN, "wireframe"),
        ]
        script.section(("vessel", "bell"), (0, 0, 0), normal=(0, -1, 0), cap=True, at=0, duration=2)
        script.wait(2)
        camera = ArchCamera((2, -10, 3), (0, 0, 0), zoom=1.8)
        duration = 4
    elif mode == "hover":
        parts = vehicle()
        ids = tuple(a.id for a in parts)
        parts = [ArchPart(a.id, a.mesh, (0, 0, 20), a.rotation, a.scale, a.style, a.explode_vector) for a in parts]
        tracks(script, ids, [(float(t), (0, 0, p.hover_demo(t)["height"]), (0, 0, 0)) for t in np.linspace(0, 1, 49)])
        ground = pv.Cube(center=(0, 0, -p.CG_HEIGHT - 0.075), x_length=12, y_length=4, z_length=0.15).triangulate()
        parts.append(part("ground", ground, "#173040", opacity=0.8))

        def follow_hover(t):
            height = p.hover_demo(t)["height"]
            return ArchCamera((3, -24, height + 2), (0, 0, height), projection="perspective", view_angle=38, zoom=1.25)

        camera = follow_hover(0)
        for ta, tb in itertools.pairwise(np.linspace(0, 1, 33)):
            script.camera_to(follow_hover(float(tb)), at=float(ta), duration=float(tb - ta))
        duration = 1
    elif mode == "landing":
        parts = vehicle(prefix="free_") + vehicle(prefix="brake_")
        end = p.landing(0)["end"]
        for prefix, x, assisted in (("free_", -4.6, False), ("brake_", 4.6, True)):
            ids = tuple(a.id for a in parts if a.id.startswith(prefix))
            startpos = (x, 0, 20)
            parts = [
                ArchPart(
                    a.id,
                    a.mesh,
                    startpos if a.id in ids else a.position,
                    a.rotation,
                    a.scale,
                    a.style,
                    a.explode_vector,
                )
                for a in parts
            ]
            times = sorted({*np.linspace(0, end, 65), p.landing(0)["switch"], p.landing(0, assisted=False)["end"]})
            tracks(
                script, ids, [(float(t), (x, 0, p.landing(t, assisted=assisted)["height"]), (0, 0, 0)) for t in times]
            )
        ground = pv.Cube(center=(0, 0, -p.CG_HEIGHT - 0.075), x_length=19, y_length=4, z_length=0.15).triangulate()
        parts.append(part("ground", ground, "#173040", opacity=0.8))

        def follow_landing(t):
            height = max(p.landing(t, assisted=a)["height"] for a in (False, True))
            focal = (0, 0, height / 2 + p.CG_HEIGHT)
            distance = max(19, 1.65 * height)
            return ArchCamera((0, -distance, focal[2] + 0.7), focal, projection="perspective", view_angle=38, zoom=1.05)

        camera = follow_landing(0)
        for ta, tb in itertools.pairwise(np.linspace(0, end, 49)):
            script.camera_to(follow_landing(float(tb)), at=float(ta), duration=float(tb - ta))
        duration = end
    else:
        raise ValueError(mode)
    invisible = tuple(a.id for a in parts if a.style is not None and a.style.opacity == 0)
    if invisible:
        script.hide(invisible, at=0, duration=0.000001)
    script.wait(max(0, duration - script.duration))
    viewport = ArchChamp(
        parts,
        script,
        width=1600,
        height=900,
        position=(800, 450),
        camera=camera,
        units="m",
        style=ArchStyle(concept="solid"),
    )
    scene = Scene(Canvas(1600, 900, "#00000000")).add(viewport).wait(duration)
    return View(viewport, scene, duration)


def export_refined():
    folder = ASSETS / "12_Refined_Models"
    folder.mkdir(parents=True, exist_ok=True)
    c = components()
    report = {}
    for name, mesh in c.items():
        if isinstance(mesh, list):
            for i, item in enumerate(mesh):
                item.save(folder / f"rotor_{i}.vtp")
            continue
        mesh.save(folder / f"{name}.vtp")
        report[name] = {"points": mesh.n_points, "cells": mesh.n_cells, "manifold": bool(mesh.is_manifold)}
    for item in ramp():
        item.mesh.dataset.save(folder / f"{item.id}_12m.vtp")
    return report


def reference_frames(renderer):
    folder = OUTPUT / "references"
    folder.mkdir(parents=True, exist_ok=True)
    for mode, age in (("hero", 3), ("replay", 5.8), ("fans", 4), ("tanks", 4), ("roll", 1.6)):
        view = make_view(mode)
        renderer.frame(view.scene, age, (1600, 1152)).save(folder / f"{mode}.png")
    return folder
