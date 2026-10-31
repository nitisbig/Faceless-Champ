"""Meshes for the PyVista layer. All coordinates are view/world coordinates (x right, y up, z depth)."""

from __future__ import annotations

import numpy as np


def sphere(center=(0.0, 0.0, 0.0), radius=1.0, resolution=96):
    import pyvista as pv

    return pv.Sphere(radius=radius, center=tuple(center), theta_resolution=resolution, phi_resolution=resolution)


def box(center=(0.0, 0.0, 0.0), half=(1.0, 1.0, 1.0), R=None):
    import pyvista as pv

    mesh = pv.Box(bounds=(-half[0], half[0], -half[1], half[1], -half[2], half[2]), quads=True)
    pts = np.asarray(mesh.points)
    if R is not None:
        pts = pts @ np.asarray(R).T
    mesh.points = pts + np.asarray(center, float)
    return mesh


def convex_solid(points, loops):
    """A polyhedron from tesseract.corner_slice (points Nx3, faces as vertex loops)."""
    import pyvista as pv

    faces = np.hstack([[len(lp), *lp] for lp in loops]).astype(np.int64)
    return pv.PolyData(np.asarray(points, float), faces).triangulate().compute_normals(auto_orient_normals=True)


def spacecraft(R=None, center=(0.0, 0.0, 0.0), scale=1.0):
    """A procedural probe (S26C): hull, nose cone, engine bell, two solar wings on struts.

    The nose points along +x before ``R`` (3x3) is applied. Returns [(mesh, style key)] with keys
    'hull', 'dark' and 'panel' so the caller picks the materials.
    """
    import pyvista as pv

    parts = [
        (pv.Cylinder(center=(0.0, 0.0, 0.0), direction=(1, 0, 0), radius=0.30, height=1.5, resolution=48), "hull"),
        (pv.Cone(center=(0.98, 0.0, 0.0), direction=(1, 0, 0), height=0.46, radius=0.30, resolution=48), "hull"),
        (pv.Cone(center=(-0.9, 0.0, 0.0), direction=(1, 0, 0), height=0.32, radius=0.24, resolution=48), "dark"),
        (pv.Cylinder(center=(0.25, 0.0, 0.0), direction=(1, 0, 0), radius=0.315, height=0.08, resolution=48), "dark"),
        (pv.Cylinder(center=(0.0, 0.0, 0.0), direction=(0, 0, 1), radius=0.035, height=2.1, resolution=16), "dark"),
    ]
    for side in (-1, 1):
        parts.append((box((0.0, 0.0, side * 1.55), (0.42, 0.015, 0.62)), "panel"))
    R = np.eye(3) if R is None else np.asarray(R, float)
    out = []
    for mesh, kind in parts:
        mesh = mesh.triangulate() if hasattr(mesh, "triangulate") else mesh
        mesh.points = (np.asarray(mesh.points) @ R.T) * scale + np.asarray(center, float)
        out.append((mesh, kind))
    return out
