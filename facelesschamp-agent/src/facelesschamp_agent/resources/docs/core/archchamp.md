# ArchChamp

ArchChamp is a technical 3D viewport that composes with ordinary Faceless Champ
scenes, groups, masks, transitions, Sequence, Grid and Layer. PyVista is a required
dependency; install the library normally, or use `uv add pyvista` in an existing
source environment. Rendering uses an offscreen VTK window and the existing
FFmpeg exporter. No browser, speech generation or remote model download is used.

## First design

```python
import pyvista as pv
from faceless_champ import (
    ArchChamp, ArchMesh, ArchPart, ArchScript, ArchStyle, Canvas, Scene, render,
)

body = ArchPart("body", ArchMesh.from_data(pv.Cube()))
script = ArchScript().orbit(45, duration=2).wait(1)
view = ArchChamp([body], script, style=ArchStyle(concept="wireframe"),
                 width=1600, height=900, position=(800, 450))
scene = Scene(Canvas(1600, 900, "#000000")).add(view).wait(3)
render(scene, "design.mp4", width=960, height=540, fps=12)
```

`ArchChamp(ArchMesh(...))` names the single part `model`. `ArchChamp.from_data`
also accepts PyVista MultiBlock assemblies and preserves block names, including
nested names separated by `/`. `ArchChamp.from_file` reads a complete assembly;
`ArchMesh.from_file` reads a single dataset. STL, OBJ, PLY, VTP, VTU and VTM are
covered. CAD interchange formats such as STEP need an external tessellation tool.

`ArchMesh.from_arrays(points, faces=None, point_data=None, cell_data=None)` accepts
XYZ coordinates and polygon index rows or VTK connectivity. `from_data` wraps
PyVista, VTK, NumPy XYZ, trimesh and meshio objects. Install extra geometry tools
in your project, for example `uv add trimesh meshio`. Imported coordinates, topology
and arrays are copied. The inspection `dataset` property returns another copy;
rendering never changes your input geometry. A SHA-256 `fingerprint` identifies
the snapshotted content. Scene snapshots share this sealed asset.

## Concepts and fields

`ArchStyle.concept` accepts `clay`, `solid`, `wireframe`, `topology`, `transparent`,
`xray`, `blueprint`, `points`, `isometric`, `heatmap` and `voxel`. Blueprint chooses
an orthographic front camera when applied to the viewport. Isometric is the default
orthographic view. Transparent and xray presets multiply authored opacity by 0.24;
internal components must exist in the supplied geometry. A surface wireframe does
not infer an internal structural skeleton. Procedural and parametric surfaces use
the same input API rather than a separate modeling engine.

Styles expose color, edge color, line width, point size, opacity and smooth shading.
Use `scalars="temperature"`, `association="point"` or `"cell"`, `clim=(low, high)`
and `cmap="viridis"` for supplied scalar fields. Heatmap requires a scalar array.
`vectors="velocity"`, with `field_mode="glyphs"` or `"streamlines"`, displays a
supplied three-component field. Glyphs use deterministic sampling of at most 256
points; streamlines use bounded integration on spatially connected input data.
These are visualization filters, not physical simulation solvers.

Voxel spacing is in model coordinates. A two-million-cell estimate prevents an
accidental huge allocation. Voxelization and capped sections require closed
manifold surfaces and reject scalar/vector styles because those filters do not
preserve field semantics. Self-intersecting surfaces must be repaired upstream.

## Animation and inspection

`ArchScript` methods return the script: `move`, `rotate` (XYZ degrees), `scale`,
`opacity`, `show`, `hide`, `highlight`, `explode`, `camera_to`, `orbit`, `section`
and `wait`. Actions default to sequential one-second intervals; `at` and `duration`
allow independent tracks to run together. Conflicting tracks on one property fail.
Continuous actions accept `easing="smooth"` for eased starts and stops; the default
`"linear"` preserves existing playback. This option round-trips in script JSON.
Visibility (`show`/`hide`) still switches immediately at the action's start.
Part IDs are explicit; `camera` is reserved. Explosions target each part's initial
position plus its `explode_vector * factor`, so factor zero reassembles it.
Orbit rotates around world Z. Visibility switches at the beginning of the action.
When show is a part's first visibility action, that part starts hidden. Scalar-field
highlights retain the colormap and emphasize edges/point size; vector overlays use
the accent color until highlighted.

Section `origin` and `normal` are world coordinates; the first plane enters from
outside the geometry and subsequent sections interpolate from the previous plane.
`cap=True` closes the cut, while `contour=True` adds its boundary. Camera transitions
interpolate position, focal point, up, zoom and field of view; projection switches
at the endpoint. Avoid camera paths that pass through a degenerate camera frame.

`state_at(time)` inspects original script time. `source_start` offsets playback,
with final states held after the script finishes. Existing component `.animate`
controls the complete 2D viewport; ArchScript controls its 3D contents. Evaluation
is independent of frame order. Pixel repeatability is tested within one backend,
not promised across drivers or machines.

## Labels and dimensions

`ArchLabel(text, point, part=None, offset=(24, -24))` adds a world-anchored callout.
`ArchDimension(start, end, part=None, offset=(0, 32), precision=2)` measures the
distance between endpoints. Anchors with a part ID use its local coordinates and
follow its transform; unbound anchors use world coordinates. Set viewport `units`
explicitly, such as `"m"` or `"mm"`; the default is `"model units"`. Values refer
to the authored model and are unaffected by screen scaling. Labels are always
drawn above geometry and disappear when behind the camera or attached to a hidden
part. No physical-unit conversion or automatic collision rearrangement occurs.

`project_at(time, points, part=None)` returns viewport pixel coordinates or `None`
behind the camera. `diagnostics_at(time)` reports projected annotation overflow
and text-box overlaps. Font, label colors and font sizes are configurable.

## Structured authoring

`ArchChamp.from_dict(design, mesh_resolver=...)` accepts `parts`, `style`, `camera`,
`script`, `labels`, `dimensions` and `units`. Each part has `id`, `mesh`, and optional
transform/style/explosion settings. Mesh sources use one of `primitive` with `params`,
`file`, or `asset`. Supported structured primitives are cube, sphere, cylinder,
cone, plane and torus. Scripts serialize through `to_dict`/`from_dict` with `actions`
and optional final `duration`; camera actions use camera dictionaries. JSON does
not import factories or execute arbitrary expressions. `validate_design` performs
structural validation without opening VTK rendering resources.

## Runtime and examples

Offscreen sessions live in `PillowRenderer`, which reuses actors and static filters.
`arch_session_limit=4` bounds live sessions; evictions close their native windows.
Use `with PillowRenderer(...) as renderer` or call `close()` for direct frame work.
Export/still/storyboard helpers close renderers they create, including on failure.
Caller-supplied renderers remain caller-owned. Layout measurement and validation
never open OpenGL. Standalone `frame_image` uses a short-lived session.

VTK 9.5+ can use EGL with runtime OpenGL/EGL libraries on headless Linux. ArchChamp
disables multisampling before depth peeling and uses Faceless Champ supersampling.
Missing GL support requires fixing the host environment; dependencies are never
installed by rendering. See [PyVista installation](https://docs.pyvista.org/getting-started/installation.html).
