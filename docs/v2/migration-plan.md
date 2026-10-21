# FacelessChamp V2 phased migration plan

Status: the original audit was documentation-only. M1 and M2 were subsequently
authorized; their implementation records describe source changes and validation.
Baseline: `22f3beaccb5a56990bd0974666b7c639a0667a68`, audited 2026-10-20.
Follow-up: M1 implementation was subsequently authorized. Its changes, validation,
and acceptance status are recorded in [M1 implementation](m1-implementation.md).
M2 was subsequently authorized; see [M2 implementation](m2-implementation.md) for
its shared compilation, measurement, source contracts and validation. M3 was subsequently
authorized with major key tests only; see [M3 implementation](m3-implementation.md)
for backend convergence and the scoped validation record. M4 was subsequently
authorized; see [M4 implementation](m4-implementation.md) and the
[M4 migration guide](m4-migration.md). M5 was subsequently authorized; see
[M5 implementation](m5-implementation.md) and the [M5 migration guide](m5-migration.md).
All five implementation milestones are complete; release certification remains scoped
to the checks recorded for each milestone. The original
audit/proposal below remains the migration reference.
See [decisions](feature-decisions.md), [interfaces](api-design.md),
[backend contracts](backend-integration.md) and [benchmarks](performance-baseline.md).

## Ordering and compatibility policy

Implement and validate each milestone independently. Keep the audited V1 source
and dependency lock as a reproducible reference. Build complete baseline/candidate
wheels in isolated environments; do not compare one old renderer module against
new components as a release gate. Branch/worktree operations, releases and source
changes below are future work, not actions performed by this documentation change.

Announce domain import removals and the move to explicit 3D installation in a V1
maintenance/deprecation release before the V2 major release. Coordinate Core/Kit/
Agent compatibility bounds; the present `<0.2.0` requirements cannot be carried
into an eventual V2 major release. Preserve shared Core imports with Core-local
aliases. Do not make Core forward imports to Kit. Users who cannot migrate domain
imports, especially ChessChamp projects, retain an isolated pinned V1 source path.

No migration changes cue timestamps, audio source bytes, authored defaults, or
user-owned render.py/template content automatically. Persisted schema changes must
retain originals and have explicit converters. Old Agent evidence remains historical
and becomes stale against changed implementation fingerprints; it is not deleted
or relabeled as verification of V2.

## M0 — audit and contract freeze

Deliver this documentation set. Record the source commit, API/import inventories,
current test results, diagnostic benchmark samples, proposed interfaces, first
milestone, and unresolved platform/performance evidence. Preserve existing
verification reports as dated records.

Before M1 implementation, establish clean V1 wheel fixtures for a base scene,
narrated excerpt, nested groups, charts/diagrams, native text/path/masks, prepared
playback and scientific fields/sections. Capture image/timing/font/backend identity
with each reference. Most current tests already cover these cases; do not replace
them with implementation-mirroring tests or rerender every project film.

Gate: all eight documents have valid local links, complete module/decision mapping,
consistent targets, and no implied implementation claim. Rollback: documentation
changes only; no source migration exists yet.

## M1 — lightweight standalone Core

| Files | Concrete change |
| --- | --- |
| Root `pyproject.toml`, `uv.lock` | Move required PyVista into a new `3d` extra. Keep Pillow as the sole base dependency. Ensure `cad`, `geometry`, `geometry-advanced` explicitly retain the PyVista conversion dependencies their advertised operations need. Keep tested native bounds; introduce the proposed tested PyVista minor bound separately and transparently. |
| Kit and Agent `pyproject.toml` | Forward 3D/CAD/geometry capabilities consistently without making them mandatory. Keep domain extras working until M4; no physical extraction now. |
| Core `__init__.py` | Lazy resolution of existing supported exports; preserve `__all__`, `dir()`, public names, CLI entrypoint and type discoverability. No domain deletion or Core → Kit imports. |
| `arch/model.py`, `arch/dependencies.py`, `gpu.py`, relevant CLI doctor guidance | Actionable explicit-extra errors and metadata-only capability listing. Native probing stays opt-in, closes resources, and reports actual software/hardware identity. |
| `README.md`, installation/Arch guides, Kit/Agent installation guidance | Explain base versus 3D and migration impact; synchronize selected current resource copies without rewriting historical verification. |
| New `tests/test_minimal_install.py`, `tests/test_architecture_boundaries.py`; existing distribution/API tests | Clean-wheel dependency/import/CLI/base-frame/export coverage, blocked-import probes, public-export resolution, no upward Core imports, native metadata/probe separation. |

Keep source-tree tests and clean-wheel tests separate. The minimal wheel lane must
not accidentally import the checkout or reuse the current all-extras environment.
An existing Arch starter must either be installed with the explicit 3D extra or
fail with a clear remedy; do not silently substitute a 2D approximation.

Gate: the [first milestone criteria](#recommended-first-milestone) all pass.
Rollback: revert M1 packaging/lazy-facade changes as a unit; existing full V1
environment remains runnable. Do not proceed into scene compilation to hide an
installation/API regression.

## M2 — shared compilation, measurement and source seam

Proposed new Core files:

- `_rendering/plan.py`: private immutable node/resource/track/composition records.
- `_rendering/evaluate.py`: one arbitrary-time evaluator and geometry/isolation plan.
- `_rendering/measure.py`: reusable logical/ink/text/intrinsic measurement service.
- `_rendering/resources.py`: shared byte accounting/cache and owned-source session helpers.
- `sources.py`: public Viewport/RasterSource/RasterSession contracts.

Refactor `timeline.py` snapshot creation to retain one visual snapshot per node,
using graph IDs/shared snapshot ownership rather than copying descendant trees
for every Group. Preserve component mutation isolation and existing authoring
atomicity. Compile immutable execution data after authoring; invalidate compilation
when supported authoring adds/removes/changes tracks. Never rely on private direct
mutation of entries as a public invalidation API.

Move timing/geometry responsibilities from `_composition_plan.py`, `_render_state.py`
and renderer-dependent `layout.py` measurement into those modules. Keep temporary
private forwarding helpers while backends transition; remove them after M3's
call-site inventory is empty. `renderer.py` remains the public facade. Move shared
Pillow painting into `backends/pillow.py` while retaining `PillowRenderer` aliases.

Add the public animation validation/resolution hooks described in
[API design](api-design.md#animation-extension-points). Adapt the old domain
components to the source/validation seams without moving them yet. Extract shared
raw SRT parsing from `subtitles.py`; retain SubtitleTrack overlap validation and
Agent input bounds through Kit's facade.

Add `tests/test_render_plan.py`, `tests/test_sources.py` and measurement cases;
extend groups/timed-scene/composition-hold/scheduling/Spring/cache regressions.
Prove one snapshot per authored node for 5/9/17/33 and a wider scene, source mutation
isolation, stable z ties, arbitrary-order sampling, track conflict atomicity,
terminal left-limit holds, captions/GIF/source-age keys, and no native context during
measurement. Test custom Renderer protocol compatibility independently of the IR.

Gate: common evaluation/geometry matches V1 fixtures, snapshot retention is linear,
all relevant suites pass and no native handles enter generic snapshots. Run the
matched build/render memory benchmarks. Rollback: use the complete frozen M1 wheel as the external reference and revert
the milestone if parity fails. The implemented M2 does not ship a second runtime
evaluator.

## M3 — converge backend execution

| Current files | Target behavior |
| --- | --- |
| `renderer.py`, new `backends/pillow.py`, `_compositor.py` | Public facade + shared frame-plan compositor; eliminate Pillow's parallel `_scene`/`_affine_scene` policy after parity |
| `backends/skia.py`, `_skia_paint.py`, `_skia_text.py`, `_native.py` | Keep native paint/text/surface code and conversions; replace Skia traversal/age/signature policy with the shared plan |
| `backends/moderngl.py`, `_gl/device.py`, shaders | Consume shared plans/identities; retain device allocation, kernels, transfer counters, owned thread/context and final readback |
| `_raster_adapter.py`, `_portable.py`, `_surface_raster.py`, `_cpu_device.py` | Shared primitive/source adapters and caches; remove private PillowRenderer method dependency as the integration seam |
| `_effects_cpu.py`, effects/procedural/transitions | Retain CPU semantic reference; adopt native optimized operations only if targeted parity/performance gates pass |
| `gpu.py`, `_auto.py`, `export.py`, `preview.py`, `audio.py` | Feature support requirements, one-time resolution, concrete FFmpeg lifecycle/cancellation refactor; retain output and audio contracts |

Add `tests/test_backend_contracts.py`; parameterize shared fixtures for all installed
backends. Keep `test_skia.py`, `test_moderngl.py`, cache/gradient regressions, export
and publication tests. Include alpha-zero handling, opacity ordering, masks/effect
padding, density, retained corner radius, native font/weight metrics, unsupported
feature preflight, close on partial initialization/error, and caller-owned renderer.
Fault-inject stalled workers/encoders and cancellation without long real sleeps.

Keep `_arch_worker.py` and float-environment preservation until equivalent relocated
integration tests pass. Never remove them on the strength of a software-GL smoke.

Gate: all package suites, backend image/state contracts and source-range audio
checks pass; matched certified frame median/p95 within 10% of V1; resource/soak
accounting bounded and cleanup verified. Hardware EGL performance/platform lanes
remain explicitly unverified until executed. Rollback: revert a backend's frame-plan
adapter before removing its old traversal; retain only one implementation at release.

## M4 — domain extraction and chess retirement

All destinations below are proposed paths. Move implementations once and update
imports/tests/resources together; retain names where semantics stay unchanged.

| Source | Destination / action |
| --- | --- |
| Core `charts/*` | Kit `charts/`; scales/data contracts and native-primitive lowering; compatibility raster producer initially |
| Core `maps.py`, `flags.py`, geographic data | Kit `maps/` and owned assets; Core generic images/paths stay below it |
| Core `coding.py`, `coding_workspace.py` | Kit `coding/`; update tutorial/block imports and Pygments ownership |
| Core `playground/*` | Kit `playground/`; update subprocess module targets, embedded runtime import strings and source fingerprints |
| Core `web/*` | Kit `web/`; browser preparation stays separate from prepared source playback |
| Core `flow/*` | Kit `diagrams/`; preserve JSON schema, signals/routes/symbols, independent child handles and existing raster adapter |
| Core `os_ui/*` | Kit `desktop/`; semantic simulation and primitive presentation share measured geometry |
| Core `arch/model.py`, `camera.py`, `rendering.py`, `_arch_worker.py` | Core `integrations/pyvista/`; retain ArchMesh/ArchCamera/ArchPart/ArchStyle and sessions; move label/dimension presentation records to Kit |
| Core `arch/cad.py`, `mesh.py`, dependency helpers | Core `integrations/build123d.py`, `integrations/trimesh.py`, `integrations/dependencies.py`; preserve units/fields/provenance |
| Arch clip/script/annotation design authoring | Kit `engineering/`; composition frontend over optional Core source; Core snapshot/camera/part/style types reused/re-exported |
| CAD presets, mechanisms, blueprints | Kit `engineering/models.py`, `mechanisms.py`, `blueprint.py`; illustrative presets also exercised as examples |
| Core chess files/assets and Kit chess block | Remove supported V2 implementation after V1 deprecation; follow the complete feature-decision ledger |

Update root facades, animation/domain normalization, Kit compiler type dispatch,
blocks, themes, sample factories, recipes, templates, CLI scaffold lists and
dependency extras. Remove obsolete Core-private integration imports only after all
callers have moved. Repoint root asset consumers to owning package resources before
removing identical copies; retain artist-source/provenance material that is still needed.

Move domain-specific test modules into Kit's domain suite, retaining low-level
native/geometry tests in Core. Update tests that combine domains and Core animation
without deleting their assertions. Add legacy import/deprecation/error mapping,
old serialized-data reading, no Core → Kit edges, Python-only preparation without
Playwright, off-network prepared playback, and no current chess advertisement tests.

Gate: all non-chess capabilities in the decision register have an equivalent tested
route; no generic renderer/compiler hard-codes domain classes; no upward import;
no prepared asset/schema loss; representative custom renderers still work. Chess
is the explicit supported-capability removal, with a reproducible V1 alternative.
Rollback: move one domain at a time; retain V1 source/environment rather than add
reverse-import compatibility shims or duplicate V2 domain engines.

## M5 — production services, documentation and release

Add CompiledVideo methods to Kit `compiler.py` and delegate their implementation
to a focused new Kit `rendering.py` to keep compilation separate. The public
methods/results are fixed in [API design](api-design.md#kit-production-service-additions).
Make Kit Project delegate to them and expose thin media/cue/capability/progress facades.
Refactor Agent `project.py`, `media.py`, `registry.py`, `cli.py`, `examples.py` and
generated `delivery.py` source to use Kit services. Preserve Agent-specific alignment,
review, conformance, checksum and history policy; do not collapse it into an exporter.

Add a repository-only documentation build helper, `scripts/sync_reference_docs.py`,
with an explicit source→resource inclusion table and check mode. Generate selected
Agent guide snapshots, current versions and capability metadata from canonical
Core/Kit/Agent docs. Reuse that metadata in website/atlas build scripts, without a
runtime Agent dependency in Core. Keep model-generated schema equivalence checks;
fix release gallery allocation to derive rows from recipe count.

Update the three manifests/METADATA bounds, optional forwarding, package-data and
sdist manifests, READMEs, llms references, exported skills, website and atlas. V2
documentation/examples must never advertise removed chess or uninstalled capabilities
as default. Preserve history and full-export verification boundaries.

Gate: clean wheel/sdist installs in separate 3.12/3.13 Linux lanes, base and selected
extras, offline Agent discovery/prepared playback, schema/data compatibility,
production failure/recovery tests, documentation drift/link checks and representative
media decoding/audio alignment. Report hardware/browser/platform coverage separately.
No push, publish, remote render or release is authorized by this audit.

## Regression and acceptance matrix

| Contract | Existing anchors | Required addition / migration check |
| --- | --- | --- |
| Authoring/timing | engine, timed-scene, animations, scheduling/Spring suites | Shared evaluator endpoints/conflict atomicity; no source-clock changes |
| Composition holds | `test_composition_holds.py` | Nested Scene/Sequence/Grid/Layer terminal removals and caption expiry preserved |
| Snapshot/layout | groups/layout, text fitting, Kit layout metadata | Linear retention; no renderer/context per fixed-viewport measurement |
| Paint/cache | renderer cache and gradient motion regressions, Skia/GL tests | Unified identities include lifetimes, captions, GIFs, paint/radius, density and ancestors |
| Export/audio | export, narration previews, progress, preview publication | Ranged master audio/envelopes, exact frame count, decode, cancellation and atomic no-overwrite |
| Native integration | Arch/geometry and Skia/GL regression modules | Fields/units/assembly/HLR/float state/worker isolation, missing dependencies, no regeneration per frame |
| Preparation | web/playground and Kit prepared contracts | No implicit execution/network/browser; stored manifest/old asset readers |
| Agent production | workflow, media, planning, discovery, audit contracts | Exact compiled-input delegation, fingerprints/history, malformed evidence, separate preview/full/review states |
| Distribution/docs | distribution inputs, schema equality, website verifier | Clean minimal wheels, required media/resources, public aliases, generated-doc drift and migrated snippets |

## Recommended first milestone

Implement **M1 only: lightweight standalone Core** when V2 implementation is separately
authorized. It gives a concrete dependency/import improvement before the riskier
scene/backend/domain work.

Acceptance criteria:

1. A fresh base wheel resolves to exactly Core plus Pillow at runtime. PyVista,
   VTK, NumPy, Matplotlib, Skia, ModernGL, CAD, browser, Pydantic and Kit/Agent are
   absent from that base environment.
2. Base import, lazy public lookup, CLI help, logical layout, Pillow stills and a
   bounded FFmpeg export work without optional engines/display/network. Export
   fully decodes with expected dimensions/fps/frame count and ranged audio fixtures.
3. Existing shared public imports, defaults, images and source-time behavior are
   unchanged. Source and clean-wheel tests both pass; missing native extras give
   actionable errors. Discovery initializes no native context.
4. Fresh-process Core import median improves by at least 50% against the freshly
   remeasured frozen V1 reference on the same host. Certified plain/UI AA1/AA2
   frame median and p95 remain within 10%; no quality/default-AA reduction.
5. All current package suites and new minimal-install/boundary tests pass in the
   appropriate capability lanes. Native/optional tests may skip only in the base
   lane; advertised extra lanes must actually execute their relevant tests.
6. Only M1 files change: no domain extraction, chess deletion, scene-engine rewrite,
   new mandatory package, or release/deployment. Report exact artifacts, commands,
   measured values and remaining limitations for review before starting M2.
