# Backend and external-library integration

Status: original backend proposal with M1-M5 implementation follow-up below. Source baseline:
`22f3beaccb5a56990bd0974666b7c639a0667a68`, 2026-10-20.
Read with [architecture](architecture-proposal.md), [APIs](api-design.md),
[performance](performance-baseline.md), and [migration](migration-plan.md).

Implementation follow-up: [M1](m1-implementation.md), [M2](m2-implementation.md),
[M3](m3-implementation.md), [M4](m4-implementation.md) and
[M5](m5-implementation.md) record the implemented changes and scoped evidence.
The original proposal and audit measurements below retain their dated baseline.

## Existing seams to retain

[Renderer](../../src/faceless_champ/renderer.py#L49) already exposes validation and
arbitrary-time frame sampling returning a Pillow image. Export and preview own
publication; FFmpeg/audio are separate from painting. `_composition_plan.py`
already centralizes timing/viewport allocation. `_compositor.py` is shared by
ModernGL and CPU effects, while ordinary Pillow and Skia retain separate traversals.
Use those implementations as migration inputs, not as disposable prototypes.

## Minimal shared contracts

| Interface | Contract |
| --- | --- |
| Public Renderer | Existing `validate(node)` and `frame(node, time, size) -> PIL.Image.Image`; custom implementations need not expose Core internals or a new IR |
| Built-in backend session | Managed resource ownership, idempotent close, runtime identity/counters; factory-created sessions close on success/failure, supplied custom renderer remains caller-owned |
| Internal compiled scene/frame plan | Prepared resource descriptors, shared evaluated state/geometry/order/isolation; no backend-native objects and no backend-specific timeline evaluation |
| Viewport / RasterSource | Immutable source descriptor, intrinsic size, duration, fingerprint, declared requirements, random-access frame key and `open(size)` session factory |
| Raster source session | `frame(source_time)` returns requested-size RGBA image; `close()` releases all owned resources; no dependency download or preparation |
| FFmpeg adapter | Concrete command construction, streaming frame sink, audio filtergraph, process completion/cancellation and atomic output handoff; no new generic encoder framework |

The Core compositor consumes the frame plan and a small device surface/paint API.
Refactor existing device methods rather than introducing an inheritance tree.
Backends implement allocation, draw/blit, masks, isolated layers, effects and finish.
The evaluator decides source time, visibility, transforms and bounds exactly once.
Native paint handlers must not import Kit domains to understand a leaf.

## Pixel and visual semantics

The public image/source boundary is **8-bit RGBA, straight alpha, encoded sRGB**,
with the requested dimensions and independent returned storage. Backend internals
may use premultiplied buffers. Conversion happens at adapter boundaries and must
handle alpha-zero pixels consistently. Do not globally change composition to
linear light during consolidation: current ModernGL provenance explicitly records
encoded-sRGB composition with linear-light effects.

Preserve clockwise rotation, design-pixel lengths, top-left anchoring including
raster padding, stable z-order ties, clipping/mask coordinates, and output-density
behavior. Retain current descendant opacity multiplication; generic save-layer
opacity is not equivalent for overlapping descendants. Keep the current order of
content effects, mask, halos/shadow and ancestor clipping. Surface shadow clearance
and leaf drop shadows have different semantics and cannot be silently collapsed.

Text measurement and drawing use the same declared text engine/font/weight. The
default Pillow text path remains available in Skia/ModernGL through raster tiles.
Native shaped text remains opt-in. Fixed dependencies, fonts, backend and platform
define repeatability; different font rasterizers/platforms need not be byte-identical.

## Current capability matrix

This table describes the audited implementation, not future universal native support.
`Adapter` means reuse of a raster/prepared producer; `reject` means explicit preflight
failure, rather than dropped visuals.

| Feature | Pillow | Skia CPU | ModernGL |
| --- | --- | --- | --- |
| Timeline/composition | Separate Pillow traversal + shared composition helpers | Separate Skia traversal + shared helpers | Shared Compositor; separate frame signature |
| Basic shapes | Pillow native/portable raster | Skia native | Supported native shape subset, other leaves adapted |
| Portable single-contour paths | Pillow flatten/raster | Skia native | Raster/native adapter path as supported |
| Compound/even-odd paths | Reject | Native | Requires Skia raster adapter |
| Pillow text/captions | Native raster | Adapter | Adapter |
| Explicit Skia text | Reject | Native | Skia adapter |
| PathMask | Reject | Native | Skia mask adapter required |
| Retained surfaces/gradients | Portable raster | Native | Native subset; adapters where needed |
| Effects/procedural/particles/transitions | CPU reference with NumPy when needed | Shared CPU effects path when needed | GLSL/device operations and shared seeded particle records |
| Charts/maps/coding/Flow/OS/chess | Domain raster producers | Same raster producers | Same raster producers uploaded as textures |
| PyVista viewport | Renderer-owned session | Raster session plus float-environment preservation | Isolated VTK worker + raster upload |
| Prepared HTML/playground | Browser-free playback | Adapter | Adapter |

`gpu` alone does not promise native Skia text or PathMask: those semantic features
also need Skia. Current `renderer_capabilities()` advertises broad feature names;
V2 must distinguish native/adapter/unsupported and required extras per feature.

V2 capability records retain the existing dictionary interface and add a
`feature_support` mapping with `mode` (`native`, `adapter`, `unsupported`) and
`requirements` for each semantic feature. Keep `features` as the compatible
supported-name list. Unprobed installed metadata is not `available=True` hardware
evidence. Explicit probing records success/failure and actual device identity.

## External responsibilities and adapter choices

| Library | Delegate | FacelessChamp retains | Do not duplicate |
| --- | --- | --- | --- |
| Pillow | Default image decoding, raster primitives, font metrics, portable compositing | Source clocks, cache identities, ownership, paint semantics | A new image codec or basic font loader |
| Skia | Native paths, paints, clipping, shaped typography and raster surfaces | Description translation, explicit font policy, native resource session, frame-plan integration | A second vector/font engine implemented in Python |
| ModernGL/glcontext | Headless GL context, framebuffer/texture/shader APIs | Deterministic built-in shader contracts, device budgets, transfer stats and session selection | Raw OpenGL binding layer or second scientific mesh renderer |
| PyVista/VTK | Scientific datasets, field visualization, clipping/capping, offscreen rendering | Immutable snapshots, timed viewport/part state, annotations, explicit isolation and cleanup | Mesh/volume/scalar visualization already supported by VTK |
| Trimesh and selected helpers | Topology inspection, repair, booleans, simplification | Copy-on-processing, explicit field loss, units, result validation and provenance | A new mesh-processing kernel |
| build123d/OCCT | CAD construction/import, native geometry, tessellation and hidden-line projection | Absolute units/tolerance, detached preparation, output budgets, part identity, provenance | A new CAD kernel or unconstrained preset modeling system |
| FFmpeg/ffprobe | Probe, encode/mux, trim/resample/delay/fade/mix/pad and full decode | Event collection, master/ranged clock semantics, argument construction, lifecycle, publication and evidence policy | A Python codec/audio-mixing engine |
| Matplotlib MathText / Pygments / Playwright | Equation typesetting / syntax tokenization / explicit browser capture | Caching, source-preserving presentation, preparation manifests and offline playback | Custom TeX parser, language lexer or browser engine |

Official references checked during the audit: [Skia API](https://skia.org/docs/user/api/),
[ModernGL](https://moderngl.readthedocs.io/en/stable/),
[PyVista plotting](https://docs.pyvista.org/api/plotting/index.html),
[Trimesh installation](https://trimesh.org/install.html),
[build123d import/export](https://build123d.readthedocs.io/en/latest/import_export.html),
and [FFmpeg documentation](https://www.ffmpeg.org/ffmpeg-all.html).
ModernGL's stable web documentation reported 5.12.0 while the installed engine is
5.13.0; build123d's latest guide is a development snapshot. Current installed source
and contract tests are authoritative for exact calls/version behavior.

### CAD tessellation is a justified adapter

Installed build123d 0.13.0 `Shape.mesh()` calls `BRepMesh_IncrementalMesh` with
relative deflection and parallel execution enabled. Current
[cad.py](../../src/faceless_champ/arch/cad.py) explicitly uses absolute deflection
and serial execution on detached geometry, checks output budgets, and handles
orientation/locations. Replacing it blindly with `shape.tessellate()` would change
the documented contract. Keep the minimal OCCT bridge and reassess only when an
upstream API provides matching semantics. HLR already delegates to build123d's
`project_to_viewport()`. Preserve field-loss rejection and provider conflict checks.

### Scientific viewports remain raster integration boundaries

Move the existing owned ArchSession/ArchWorker mechanisms behind RasterSource.
Keep PyVista datasets and their custom fields within that optional integration;
the generic IR references the immutable source. Do not convert all scientific
content into flat triangles or recreate its renderer in ModernGL.

ModernGL currently isolates VTK because native EGL initialization/finalization can
invalidate another library's context. Skia's float-environment guard protects a
separate native interaction. Keep both safeguards with regressions. A new integration
must not remove them simply because a one-frame smoke test succeeds.

## Caching, lifecycle and failures

Prepare scene hierarchy, stable ordering, immutable resource identity and track
indexes once per compilation. Evaluate each node once per frame; derive bounds and
cache keys from the resolved state. Include visibility/lifetimes, source age/frame
key, active caption state, paint changes, corner radius, geometry, density, font
identity and relevant ancestors. Do not use absolute source time to invalidate a
static hold unnecessarily.

Reuse ByteCache-style byte-bounded retention and renderer-owned font/decoder/source
sessions. Separately report cached image/texture bytes, temporary surface bytes,
native worker memory and driver allocations. Preserve independent returned images.
An oversized item may render but must not be retained beyond its budget. Close
every owned native resource on success, exception, cancellation and partial initialization.

ModernGL already performs a final framebuffer readback per output frame. Optimize
extra conversion/copy costs only after profiling; do not describe current behavior
as per-leaf framebuffer readback. Public PIL compatibility remains the default
export boundary; direct hardware encoding/zero-copy is outside initial V2.

FFmpeg remains a concrete adapter. Preserve sample-based delays at 48 kHz,
composition fade envelopes, range trimming after mixing, frame count and source
sampling, encoder exit checks, broken-pipe diagnostics and same-filesystem atomic
publication. Add fault-injected bounded worker cancellation/deadline handling without
giving every legitimate long export an arbitrary fixed total duration timeout.

## Backend acceptance

Use one parametrized contract corpus for shared semantics, plus native adapter tests.
Check exact repeatability within the same backend, shared evaluated geometry/order,
flat-color alpha cases, and current feature-specific edge/text tolerances. Preserve
existing backend-specific visual references; do not demand identical antialiasing
from unrelated engines. Test unsupported features before encoder start, no fallback
for explicit backend requests, one-time auto resolution, caller/owned cleanup,
VTK/Skia interaction, software GL reporting, and source range/audio behavior.

Native filter replacement is conditional: adopt it only if the fixed parity and
performance tests pass; otherwise keep the current reference path. That rule avoids
turning an architecture consolidation into an unreviewed visual redesign.
