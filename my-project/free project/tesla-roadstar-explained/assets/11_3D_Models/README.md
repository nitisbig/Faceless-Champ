# Procedural 3D Mesh Assets

Each OBJ file is a real triangulated mesh in **meters**, suitable for PyVista, trimesh,
or Blender. The GLB files preserve separate mesh components for 3D packages and viewers.
The vehicle uses +X forward, +Y to its right and +Z upward; its center is near (0,0,0.7).
Ramp spans approximately x=-7 to x=6, z=0 to z=12, and y=-1.7 to +1.7 meters.
The ramp is an IDEALIZED inside-loop profile with radius 6 meters, not the real Tesla ramp.
Vehicle geometry is stylized concept geometry (not Tesla Roadster CAD and not dimensionally accurate).
Nozzle geometry and mounting locations are SCHEMATIC, not Tesla hardware.

PyVista can load the OBJ files with `pv.read` and draw edges or wireframe.
See `10_Guides/pyvista_wireframe_example.py` for a minimal example.

Use this as animation scaffolding; for high-fidelity engineering CAD replace the meshes
with legally usable manufacturer-accurate geometry.
