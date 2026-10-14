"""Camera snapshots, matrices and backend-independent screen projection."""

import math
from dataclasses import dataclass

from .model import ArchDataError, number, vector


@dataclass(frozen=True)
class ArchCamera:
    position: tuple = (4, -4, 3)
    focal_point: tuple = (0, 0, 0)
    up: tuple = (0, 0, 1)
    projection: str = "orthographic"
    zoom: float = 1
    view_angle: float = 30

    def __post_init__(self):
        import numpy as np

        for key in ("position", "focal_point", "up"):
            object.__setattr__(self, key, vector(getattr(self, key), key))
        forward = np.asarray(self.focal_point) - self.position
        if np.linalg.norm(forward) < 1e-9 or np.linalg.norm(np.cross(forward, self.up)) < 1e-9:
            raise ArchDataError("camera", "position, focal point and up must define a valid frame")
        if self.projection not in {"orthographic", "perspective"}:
            raise ArchDataError("projection", "expected orthographic or perspective")
        number(self.zoom, "zoom", 0.000001)
        if not 1 <= number(self.view_angle, "view_angle") <= 120:
            raise ArchDataError("view_angle", "must be between 1 and 120")


def part_matrix(state):
    import numpy as np

    x, y, z = [math.radians(v) for v in state["rotation"]]
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    result = np.eye(4)
    result[:3, :3] = rz @ ry @ rx * state["scale"]
    result[:3, 3] = state["position"]
    return result


def world(point, part, states):
    import numpy as np

    return tuple((part_matrix(states[part]) @ np.array([*point, 1]))[:3]) if part else tuple(point)


def project(point, camera, width, height, parallel_scale):
    import numpy as np

    forward = np.asarray(camera.focal_point) - camera.position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, camera.up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    delta = np.asarray(point) - camera.position
    depth = float(delta @ forward)
    if depth <= 1e-9:
        return None
    extent = (
        parallel_scale / camera.zoom
        if camera.projection == "orthographic"
        else depth * math.tan(math.radians(camera.view_angle / 2)) / camera.zoom
    )
    return (
        width / 2 + float(delta @ right) * height / (2 * extent),
        height / 2 - float(delta @ up) * height / (2 * extent),
    )
