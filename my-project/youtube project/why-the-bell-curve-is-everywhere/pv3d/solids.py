"""Meshes for the PyVista layer. View/world coordinates: x right, y up, z depth (space.Camera)."""

from __future__ import annotations

import numpy as np

# Pip layouts on a unit face (u, v in -1..1), indexed by face value.
PIPS = {
    1: [(0, 0)],
    2: [(-0.5, -0.5), (0.5, 0.5)],
    3: [(-0.5, -0.5), (0, 0), (0.5, 0.5)],
    4: [(-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5), (0.5, 0.5)],
    5: [(-0.5, -0.5), (0.5, -0.5), (0, 0), (-0.5, 0.5), (0.5, 0.5)],
    6: [(-0.5, -0.55), (0.5, -0.55), (-0.5, 0), (0.5, 0), (-0.5, 0.55), (0.5, 0.55)],
}
# Face value -> (outward normal, u axis, v axis) in the die's own frame; opposite faces sum to 7.
FACES = {
    1: ((0, 0, -1), (1, 0, 0), (0, 1, 0)),
    6: ((0, 0, 1), (-1, 0, 0), (0, 1, 0)),
    2: ((1, 0, 0), (0, 0, 1), (0, 1, 0)),
    5: ((-1, 0, 0), (0, 0, -1), (0, 1, 0)),
    3: ((0, 1, 0), (1, 0, 0), (0, 0, 1)),
    4: ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
}


def die(center=(0.0, 0.0, 0.0), half=1.0, R=None, roundness=0.18):
    """A rounded cube (superquadric) rotated by ``R`` about its centre."""
    import pyvista as pv

    mesh = pv.Superquadric(center=(0, 0, 0), scale=(half, half, half), size=1.0, theta_roundness=roundness,
                           phi_roundness=roundness, theta_resolution=64, phi_resolution=64)
    pts = np.asarray(mesh.points)
    if R is not None:
        pts = pts @ np.asarray(R).T
    mesh.points = pts + np.asarray(center, float)
    return mesh.compute_normals(auto_orient_normals=True)


def pip_points(center=(0.0, 0.0, 0.0), half=1.0, R=None, inset=1.002, spread=0.62):
    """World positions, outward normals and radii of every pip, for skia to draw on top of the VTK die."""
    R = np.eye(3) if R is None else np.asarray(R)
    out = []
    for value, (n, u, v) in FACES.items():
        n, u, v = (np.asarray(a, float) for a in (n, u, v))
        for a, b in PIPS[value]:
            p = (n * inset + (u * a + v * b) * spread) * half
            out.append((R @ p + np.asarray(center, float), R @ n, 0.11 * half, value))
    return out


def gaussian_surface(height=1.6, extent=2.6, n=120, sigma=1.0):
    """The surface y = height · exp(-(x² + z²) / (2σ²)) over a disc of radius ``extent`` (polar grid)."""
    import pyvista as pv

    r = np.linspace(0.0, extent, n // 2)
    th = np.linspace(0.0, 2 * np.pi, n)
    R, T = np.meshgrid(r, th)
    x, z = R * np.cos(T), R * np.sin(T)
    y = height * np.exp(-(R ** 2) / (2 * sigma ** 2))
    grid = pv.StructuredGrid(x, y, z)
    return grid.extract_surface(algorithm="dataset_surface").triangulate().compute_normals(auto_orient_normals=True)


def rotation(ax, ay, az):
    cx, sx, cy, sy, cz, sz = np.cos(ax), np.sin(ax), np.cos(ay), np.sin(ay), np.cos(az), np.sin(az)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx
