"""Minimal PyVista scene using the included procedural OBJ assets.
Install: pip install pyvista vtk
Run this file from anywhere; it resolves the asset pack relative to itself.
"""

from pathlib import Path

import pyvista as pv

ROOT = Path(__file__).resolve().parent.parent
MESH = ROOT / "11_3D_Models"

plotter = pv.Plotter(window_size=(1920, 1080), off_screen=False)
plotter.set_background("#050911")
for name, color in [
    ("roadster_body", "#57EDFF"),
    ("roadster_canopy", "#ECFAFF"),
    ("roadster_chassis", "#2D9CFF"),
    ("roadster_tires", "#57EDFF"),
    ("roadster_rims", "#F3FAFF"),
    ("roadster_suction_fans", "#359CFF"),
    ("roadster_pressure_tanks", "#AF82FF"),
    ("roadster_thruster_tubes", "#FF985A"),
]:
    mesh = pv.read(str(MESH / f"{name}.obj"))
    plotter.add_mesh(mesh, style="wireframe", color=color, line_width=1.4, opacity=0.83, lighting=False)
plotter.camera_position = [(8, -11, 5.5), (0, 0, 0.7), (0, 0, 1)]
plotter.show()
