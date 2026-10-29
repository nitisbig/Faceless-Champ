# NEON ROADSTER — REUSABLE VIDEO ASSET PACK

Visual direction: black background, white/cyan neon wireframe, restrained science UI.
Target format: 16:9 / 1920×1080 PNG output, editable vector SVG source.

## Structure

01_Vehicle — sports-car wireframe model, 6 projected views, inverted and ghost version.
02_Ramps_and_Road — curved ramp, wall/ceiling, track layers, tire contact.
03_Suction_and_Airflow — fans, four-fan schematic, pressure cutaway, skirt, airflow field.
04_Thrusters — nitrogen tank schematic, dual tanks, nozzle, jet plume, valves, nozzle overlay.
05_Force_Vectors — transparent gravity, normal, friction, suction, velocity and thrust arrows,
                    body axes, torque indicator, center of mass, angle construction.
06_Simulation_Overlays — grids, telemetry card, mathematical plots, trajectories, control loop.
07_Equations — high-resolution transparent PNGs and SVGs with actual math typesetting.
08_Scene_Layouts — 10 black-background 16:9 composition samples, editable SVG + PNG.
09_Preview — contact sheet and style preview.
11_3D_Models — genuine editable procedural OBJ/GLB geometry for PyVista, Blender, etc.
10_Guides — design system and scene-asset mapping.

## How to composite

* Import SVG for editable/scalable artwork into your renderer or Inkscape.
* Import corresponding transparent PNGs into FFmpeg/Blender/Manim/your own compositor.
* PNG image dimensions for reusable art layers: 1920×1080; transparency retained.
* 08_Scene_Layouts includes an opaque black/blue background, intended as scene references.
* All other PNGs are transparent to allow stacking, coloring, and motion.
* For best sharpness in 4K, rasterize SVGs at 3840×2160 rather than upscaling PNGs.
* For an authentic Tesla body, replace the stylized wireframe coupe with licensed or original
  exact Roadster geometry; these assets are custom abstract technical illustrations.

## Physics disclaimer

These images are vector representations and composition aids, NOT a physical simulator,
Tesla CAD, CFD results, telemetry or validated engineering data. Equation numerics refer
to deliberately hypothetical demo inputs (1700 kg, 2 m² effective suction area, etc.).
Use separate physics solvers for frame-by-frame forces, positions and flight dynamics.
The schematic nozzle array is invented to illustrate concepts, not Tesla nozzle placement.

## Palette

Background    #050911
Panels        #0B1827
Neon cyan     #57EDFF
Electric blue #359CFF
Purple        #AF82FF
Orange        #FF985A
Amber         #FFC46B
Green         #72F7BA
Text          #F3FAFF

## Recommended layers (back to front)

background / grid -> ramp -> car -> translucent science effects -> force arrows ->
LaTeX equations -> telemetry -> subtitles.

For animation, turn force vector SVGs into transformed/repositioned instances; they are
reference arrows. The actual vector magnitude should drive arrow length.
