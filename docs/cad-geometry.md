# CAD and geometry

ArchChamp accepts dimensioned build123d models and processed Trimesh surfaces through
optional preparation APIs. Rendering still uses PyVista and the existing Pillow,
Skia and ModernGL composition paths. This is the local core 0.1.6 source candidate. From this checkout, install only
the capabilities your project uses:

```sh
uv pip install --python .venv/bin/python -e '.[cad,geometry-advanced]'
```

`cad` uses build123d 0.13 and its OCP 8 `cadquery-ocp-novtk` provider on Python
3.12–3.14. Do not install the competing `cadquery-ocp` distribution in the same
environment. The existing PyVista/VTK dependency remains unchanged. The CAD wheel
requires a supported native platform; Linux wheels require glibc 2.28 or later.
`geometry` installs Trimesh, SciPy and NetworkX. `geometry-advanced` adds Manifold
booleans and fast-simplification decimation. These packages load only when called.

## A native CAD scene

```python
from faceless_champ import Canvas, Scene
from faceless_champ.arch import ArchChamp, ArchScript, parts_from_cad
from faceless_champ.arch.cad_models import gear_pair

def build_scene():
    parts = parts_from_cad(gear_pair(module=2, teeth=(24, 48), width=10))
    motion = ArchScript().gear_pair("driver", "driven", degrees=720, duration=4)
    view = ArchChamp(parts, motion, units="mm", width=1920, height=1080,
                     position=(960, 540))
    return Scene(Canvas(1920, 1080, "#080f1c")).add(view).wait(4)
```

Use build123d's native sketch, extrusion, revolve, sweep, loft, boolean, fillet and
chamfer APIs for arbitrary models. `mesh_from_cad(shape)` produces one immutable
ArchMesh; `parts_from_cad(assembly)` preserves named leaf parts and accumulated
locations. Root assembly labels are omitted from IDs; nested labels use `/`.
Missing labels use `part-N`, duplicate sibling labels receive numeric suffixes,
and `/` inside labels becomes `_`. Repeated native solids share snapshots within
one conversion. The renderer shares compatible prepared geometry between actors.

`read_step(path)` imports local `.step`/`.stp` assemblies into millimetre coordinates.
It returns a native build123d object. Pass it to `parts_from_cad` for rendering or
to a native build123d exporter for CAD interchange. No file download or installation
occurs during construction or rendering.

## Units, accuracy and memory

Native build123d shapes have no intrinsic units. New CAD bridge functions interpret
their source coordinates as `mm` by default. Explicit `source_units` and
`target_units` support `mm`, `cm`, `m`, `in`, and `ft`. Conversion scales geometry
and assembly translations together. STEP imports and built-in presets use source
millimetres. Set `ArchChamp.units` to the target units for accurate labels.
Existing ArchChamp unit strings retain their display-only behavior.

All ArchScript distances, pivots and ArchChamp dimension anchors are in **target model
coordinates**. For example, a 10 mm crank rendered in metres uses
`crank_radius=0.01` in its animation. Preset CAD parameters remain in millimetres.

`TessellationOptions(linear_deflection=0.05, angular_deflection=0.1,
weld_tolerance=1e-7, max_triangles=1_000_000)` controls serial absolute OCCT
meshing. Linear/weld values are in source units, angular deflection is in radians.
The adapter copies native geometry and discards inherited triangulations before
meshing, then welds face seams. Fine and coarse conversions do not depend on call
order. Accuracy tests use analytic fixtures; these settings are not a universal
certification of arbitrary CAD models.

The triangle budget covers the complete rendered assembly, including instances.
It bounds extracted output; OCCT can allocate native working memory before that
limit is checked. Use coarser explicit settings or split large designs. No automatic
decimation or quality downgrade occurs. Four live Arch sessions remain the existing
default; closing a renderer closes its native sessions and VTK worker.

`ArchMesh.provenance` returns independent JSON metadata: generation parameters,
source checksums where available, units, tessellation, processing and engine versions.
Geometry fingerprints continue to identify actual geometry. CAD objects never enter
scene snapshots or the private VTK process protocol. Fixed-stack fresh-process
repeatability is tested; kernel/driver upgrades can change geometry or pixels.

## Parametric teaching models and motion

`faceless_champ.arch.cad_models` supplies `spur_gear`, `gear_pair`, `piston`,
`slider_crank`, `inline_engine`, and `portal_frame`. They return native Shapes or
Compounds. `validate_preset(name, params)` validates the bounded preset contract
without loading the kernel. Gears use sampled involute flanks and full-depth
proportions; unsupported undercut configurations are rejected. These models are
engineering teaching geometry, not tool-specific manufacturing specifications.

`ArchScript.spin(targets, degrees, axis=(0,0,1), pivot=(0,0,0), **timing)` adds
local pivoted rotation beneath the existing part position/rotation/scale. Consecutive
spins compose; ordinary move/explode actions can position the moving part.
`gear_pair(driver, driven, teeth=(24,48), degrees=360, **timing)` atomically schedules
opposite local-Z rotations with the exact external-gear ratio.

`slider_crank([crank, rod, piston], crank_radius=10, rod_length=35, turns=1,
phase=0, **timing)` evaluates the absolute angle `phase + 360*turns*progress`.
The canonical plane is XY, crank axis Z, slider direction +X. Crank local origin is
its shaft; rod local endpoints are `(0,0,0)` and `(rod_length,0,0)` with rest part
position `(crank_radius,0,0)`; piston local origin is its pin with rest part position
`(crank_radius+rod_length,0,0)`. The native slider-crank preset uses that convention.
The rod must exceed the crank radius. Consecutive mechanism actions set absolute
phase; choose matching phases for continuity. Overlapping analytic ownership of a
part fails. Framing covers complete analytic trajectories, including intermediate
extrema. Section planes and annotations use the same evaluated matrices.

All actions serialize through ArchScript, use its source clock and easing, hold
their endpoint and support arbitrary seeking. This is analytic kinematics, not
joint solving, collision response, stress analysis or combustion simulation.

## Mesh processing

`ArchMesh.from_data(trimesh_mesh)` remains the forward conversion. `to_trimesh`
returns an independent surface. `parts_from_trimesh_scene` preserves named instances,
shares compatible snapshots and bakes affine geometry/reflections into copied arrays.
Feed a locally loaded Trimesh GLB/glTF scene to this adapter when scene transforms
are needed; register source files and sidecars in the project for provenance.

- `inspect_mesh` reports topology, components, finite geometry, area and solid volume.
  Open or inconsistently oriented surfaces have no reported solid volume.
- `repair_mesh` removes duplicate/degenerate faces and fixes normals. Vertex welding
  and small-hole filling are explicit options; inspect the result for remaining defects.
- `simplify_mesh(mesh, target_faces)` uses explicit quadric decimation and records
  source/result faces and volumes plus deterministic sampled nearest-vertex
  distances. The sampled metric is not a surface Hausdorff bound; measure error
  for the intended use.
- `boolean_mesh(meshes, operation="union")` explicitly uses Manifold and requires
  watertight, consistently wound positive-volume inputs with compatible units.

Conversions reject supplied data arrays that would be lost, unless `drop_fields=True`
is explicitly supplied. Derived normals, VTK original-index arrays and PyVista's
conversion metadata are disposable; custom point, cell and dataset arrays are
checked. Use `ArchMesh.provenance` for preparation metadata. Existing PyVista clipping, slicing, voxelization and field
rendering remain available through ArchChamp. Processing works on copies.

## CAD blueprints

`blueprint_from_cad(shape, camera=ArchCamera(...), dimensions=(...), ...)` prepares
orthographic visible/hidden CAD edges into existing portable drawing components.
Hidden edges use dash segments, curves use adaptive subdivision, and values use
original 3D dimension anchors. Part-bound anchors use the same leaf IDs as CAD
conversion. Blueprint anchors use source CAD coordinates; labels convert to target
units. A segment budget bounds drawing
complexity. Choose anchors visible in the view; coincident projected anchors fail.

Projection happens once during preparation. The returned Group can animate normally
on all backends. Compose multiple views with existing Grid/Kit layouts. Moving 3D
cutaways continue to use ArchScript.section; per-frame CAD hidden-line removal and
formal manufacturing sheets/GD&T are outside this release.

## Structured core designs

`ArchChamp.from_dict` accepts either the existing `parts` form or a bounded CAD
source. Structural `validate_design` checks import no optional native engines.

```python
from faceless_champ.arch import ArchChamp

view = ArchChamp.from_dict({
    "units": "mm",
    "cad": {"preset": "gear_pair", "params": {"teeth": [24, 48]}}
})
```

For registered STEP sources, pass `cad_resolver` explicitly:
`ArchChamp.from_dict({"cad": {"asset": "body"}}, cad_resolver=resolve_local_step)`.
The callback returns a local file path. Imported part IDs are checked after
conversion. `view.geometry_record()` exposes portable geometry/preparation identity
for downstream tooling. Kit/Agent adapters and starter templates are deferred.

`geometry_capabilities()` reports optional dependency metadata without native
imports. `geometry_capabilities(cad=True, geometry=True)` explicitly probes both
engines without GL. `scripts/probe_geometry.py` additionally checks the selected
rendering backend.

## Verification and benchmarks

Run `examples/engineering.py --check` for structural validation. Its default export
is a three-second 1080p/30 silent excerpt; `--start`, `--seconds`, `--width`, and
`--backend` select bounded engineering samples. `--width 3840` preserves 4K output.

`scripts/benchmark_geometry.py` measures isolated preparation and identical mesh-only
replay, cold/warm median/p95 frames, aggregate RSS upper bounds, and snapshot bytes.
Cases: bracket, gears, 100 shared instances, approximately one million source
triangles with 250k-face decimation, engine cutaway, and prepared blueprint.
Run three trials and record CPU/driver details. The warm-overhead target is 10%;
the incremental RSS target is 1536 MiB. Rendering FPS is measured, not assumed to
match the encoded playback FPS. See the [core verification record](cad-geometry-verification.md).
