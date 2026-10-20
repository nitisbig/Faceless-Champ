"""Closed-form mechanical poses. No integration steps or native CAD handles."""

import math

__all__ = ["slider_crank_pose"]


def _euler_xyz(matrix):
    """Extract the existing Rz @ Ry @ Rx convention from a rigid matrix."""
    y = math.asin(max(-1.0, min(1.0, -float(matrix[2, 0]))))
    if abs(math.cos(y)) > 1e-9:
        x, z = math.atan2(matrix[2, 1], matrix[2, 2]), math.atan2(matrix[1, 0], matrix[0, 0])
    else:
        x, z = math.atan2(-matrix[1, 2], matrix[1, 1]), 0
    return tuple(math.degrees(v) for v in (x, y, z))


def slider_crank_pose(angle, crank_radius, rod_length):
    """XY mechanism: crank at origin, slider along +X, lengths in model units.

    Returns crank_pin, piston_pin and rod_angle (degrees). The rod length must
    exceed the crank radius; the positive slider branch is used throughout.
    """
    from .model import ArchDataError, number

    r = number(crank_radius, "crank_radius", 1e-9)
    length = number(rod_length, "rod_length", 1e-9)
    if length <= r:
        raise ArchDataError("rod_length", "must exceed crank_radius")
    theta = math.radians(number(angle, "angle"))
    x, y = r * math.cos(theta), r * math.sin(theta)
    dx = math.sqrt(max(0, length * length - y * y))
    return {"crank_pin": (x, y, 0), "piston_pin": (x + dx, 0, 0), "rod_angle": math.degrees(math.atan2(-y, dx))}


def _rotation(degrees, axis=(0, 0, 1), pivot=(0, 0, 0)):
    import numpy as np

    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    x, y, z = axis
    cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    theta = math.radians(degrees)
    rotation = np.eye(3) + math.sin(theta) * cross + (1 - math.cos(theta)) * (cross @ cross)
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = np.asarray(pivot) - rotation @ pivot
    return matrix


def _poses(action, progress):
    import numpy as np

    o = action.options
    if action.kind == "spin":
        return [_rotation(o["degrees"] * progress, o["axis"], o["pivot"])] * len(action.targets)
    pose = slider_crank_pose(o["phase"] + 360 * o["turns"] * progress, o["crank_radius"], o["rod_length"])
    crank = _rotation(o["phase"] + 360 * o["turns"] * progress)
    rod = _rotation(pose["rod_angle"])
    rod[:3, 3] = np.asarray(pose["crank_pin"]) - (o["crank_radius"], 0, 0)
    piston = np.eye(4)
    piston[0, 3] = pose["piston_pin"][0] - o["crank_radius"] - o["rod_length"]
    return crank, rod, piston


def _travel_bound(action, index, center):
    """Conservative center travel for framing, independent of sampled FPS."""
    o = action.options
    if action.kind == "spin":
        return 2 * math.dist(center, o["pivot"])
    r, length = o["crank_radius"], o["rod_length"]
    return (
        2 * math.dist(center, (0, 0, 0)),
        2 * r + 2 * math.dist(center, (0, 0, 0)) * math.sin(math.asin(r / length) / 2),
        2 * r,
    )[index]
