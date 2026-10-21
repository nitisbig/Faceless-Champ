# M3 — shared backend execution and bounded subprocess lifecycle

Implemented 2026-10-21 after M2. The user authorized M3 with **major key tests
only**. This record describes that scoped validation, not full release certification.
M4 domain extraction and ChessChamp retirement remain deferred.

## Execution and ownership

| Files | M3 change |
| --- | --- |
| `_rendering/evaluate.py` | Frame entries carry inherited visibility, evaluated state/effects, component age and isolation decisions. All backends use the same frame and sprite signatures, including source/caption/GIF identities, lifetime boundaries and dynamic effect clocks. |
| `_rendering/execute.py` | One scene walk over compiled, stable z-ordered roots/children. Painters receive evaluated entries and a child continuation; they do not sort or evaluate authoring tracks. |
| `_rendering/composition.py` | Shared Pillow/Skia fitting and composition painting, driven by canonical source-time placements. The device compositor consumes those same placements. |
| `backends/pillow.py`, `backends/_pillow_paint.py` | Small public renderer executor and backend pixel kernels. `_affine_scene` and the independent scene traversal are gone. Rounded placement and affine sampling remain separate paint kernels to preserve Pillow pixels. |
| `_rendering/raster.py` | Owned primitive, caption, equation, image and legacy domain raster production. Integrations call `sprite()`, `primitive()` and `measurement`; no adapter constructs a PillowRenderer to call its private methods. |
| `backends/_raster_adapter.py`, `_portable.py`, `playground/playback.py` | Consume the raster service. CodeEditor now explicitly closes its temporary painter. Native text/vector tiles, VTK float-state preservation and isolated scientific rendering remain available. |
| `backends/skia.py`, `_compositor.py`, `backends/moderngl.py`, `_cpu_device.py` | Shared evaluation, walk, density and identities. Native Skia painting, local surfaces, GPU device/shader operations, owning-thread checks and final-only readback are retained. |
| `_rendering/support.py`, `gpu.py`, `backends/_auto.py` | Offline feature requirements and unsupported-feature metadata. Auto selection skips incompatible fallbacks before allocation, resolves once, records reasons and excludes software GL from automatic acceleration. |
| `_rendering/process.py`, `export.py`, `backends/_arch_worker.py` | A shared bounded pipe worker for FFmpeg and isolated VTK requests; cancellation, termination escalation, child reaping and bounded joins. Normal VTK shutdown still exits gracefully. |
| `_render_state.py`, `_composition_plan.py` | Removed after the source/test call-site inventory became empty. Their policies already live in `_rendering`; no second evaluator or compatibility execution path remains. |

Each scene/time evaluates its indexed tracks once. Frame-cache signatures and
paint traversal reuse that evaluation. Backend painting still calls shared geometry
helpers with its actual surface transform/density; the private plan is not a new
public scene format or a serialized schema.

The raster service caps its combined decoded-image, primitive-sprite and equation
retention at 64 MiB by default. Caption/code budgets, source-frame bytes/session
counts, backend frame/native caches and working-surface budgets remain separate.
Adapter-specific raster budgets are passed to the service. Oversized results can
be rendered without being retained. This accounts for retained RGBA images, not
total RSS, font memory or arbitrary allocations inside a native library. Multi-frame
GIF decoding can still require transient memory before eviction.

Closing a renderer attempts all owned cleanup even if an earlier resource fails.
Skia partial initialization releases its raster service; GL partial initialization
releases its context. Public Pillow, Skia, GL and Auto renderers reject use after
close. Existing caller-owned two-method renderers keep their protocol and ownership.

## Export API and failure behavior

The existing render signature gains an optional `cancel` callable, and
`ExportSettings` gains `encoder_timeout=60` (also accepted as a render keyword):

```python
from concurrent.futures import CancelledError
from faceless_champ import render

try:
    render(scene, "video.mp4", encoder_timeout=60, cancel=stop_requested.is_set)
except CancelledError:
    pass
```

Cancellation is polled between frames and during encoder waits. Returning true
raises `CancelledError`; exceeding a per-operation deadline raises `TimeoutError`.
The pipe worker accepts only one operation at a time, so rendered frames cannot
queue without bound. Pixel conversion and all rendering remain on the caller
thread; only subprocess I/O runs in the worker. FFmpeg command/audio/filter timing,
frame counts, progress order and atomic publication are retained. Failure removes
temporary output and leaves an existing destination intact. Caller-owned renderers
remain open.

VTK requests use a 60-second deadline. Normal close sends the shutdown sentinel
and allows up to three seconds for native session cleanup. A failed/stalled child
is terminated, then killed if necessary; termination/kill waits are each bounded
at 0.5 seconds and the pipe-thread join at one second. The isolation process and
float-environment guard were retained and exercised, not replaced by an in-process
VTK/GL integration.

These bounds do not interrupt native rendering, validation, source implementations,
progress callbacks or other user code executing on the caller thread. They are
subprocess I/O deadlines, not a whole-export runtime limit. Native mask/text/path
features still require their explicit supported backend; auto never silently
substitutes Pillow for them. No required dependency or rendering default changed.

## Major validation performed

Evidence is under ignored `output/v2-m3/evidence/`; it is local execution evidence,
not packaged reference data. Existing frozen fixtures were not regenerated.

- Final affected-path run: **27 passed** (`final-key-tests.log`). This includes the
  new 13-case backend/lifecycle matrix, source clocks/fixed density, cache regressions,
  raster byte eviction, float-state restoration, real VTK/GL interoperability and
  the optional-import-blocked base runtime probe.
- The broader targeted selection covered composition terminal holds, stable z ties,
  custom Renderer compatibility, native font/weight metrics, retained gradients,
  corner-radius tracks, mask/shadow padding, working budgets, effect clocks,
  alpha-zero handling, final-only readback and ranged FFmpeg/audio output. Its first
  run passed 77 cases and exposed three failures (`key-tests.log`): two test hooks
  still addressed the removed private renderer adapter, and normal VTK shutdown
  returned a termination code. The hooks now target the raster service; graceful
  shutdown was restored. All three passed the 15-case cleanup recheck and final run.
- The base probe checks **28 distinct frozen frame hashes**, random seeks, layout,
  still output and a 12-frame source-range/audio export with optional imports blocked.
  It checks FFprobe metadata, full decode and source-aligned audio samples.
- **Six native/scientific hashes match the complete installed M2 wheel** on this
  host (`m2-native.json`, `m3-native.json`), including repeated seeks. The reference
  imported from `/tmp/fc-m2/candidate-env/.../site-packages`, the candidate from this
  checkout. Original V1 fixtures and M2 wheels remain untouched. Scientific pixels
  are compared on the same host because native driver differences affect them.
- Kit's backend validation/frame/storyboard/short-export workflow: **1 passed**.
  Agent's native design/frame/short-preview/provenance workflow: **1 passed**.
  These ran separately to avoid colliding test module names.
- Ruff, formatting and `git diff --check` passed for the changed rendering files
  and tests. The canonical export API guide and its Agent resource copy agree.

Pillow, CPU Skia and software EGL/ModernGL all executed; the GL lane was not skipped.
Software GL is not evidence of hardware acceleration. Existing Pillow/fontconfig
warnings did not prevent the pixel, timing or integration assertions from passing.

## Acceptance boundary

M3 implementation and its requested key checks are complete. Full Core/Kit/Agent
suites, fresh candidate wheels, certified median/p95 performance comparisons,
long-running resource/RSS soaks, hardware EGL and other platform lanes were **not
run for M3**, following the user's testing limit. No speedup or 10-percent performance
gate is claimed. M2's full-suite/performance results remain historical M2 evidence.

The next implementation milestone is M4, starting with one domain and its callers,
tests and compatibility mapping. It is not implemented by this change. Before a
release, run the deferred package/distribution/performance/platform gates in the
[migration plan](migration-plan.md#m3--converge-backend-execution).
