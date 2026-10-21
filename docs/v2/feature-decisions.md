# V2 feature decisions

Status: original feature decisions; implementation evidence is in the M1-M5 records
and [current M5 acceptance](m5-implementation.md). Baseline: `master` commit
`22f3beaccb5a56990bd0974666b7c639a0667a68`, audited 2026-10-20.
See [module/API inventory](architecture-audit.md#module-inventory),
[ownership](architecture-proposal.md), and [migration](migration-plan.md).

## Decision vocabulary

KEEP preserves the implementation/contract; REFACTOR changes internal ownership or
structure; MERGE consolidates overlapping implementations; REPLACE substitutes a
specific mechanism; OPTIONAL removes a capability from default requirements/imports;
REMOVE retires it from the supported main stack. An optional installation qualifier
can accompany a primary code decision. No category authorizes deletion during this audit.

## Subsystem register

| ID | Subsystem / current modules | Decision | V2 destination and retained behavior | Migration impact |
| --- | --- | --- | --- | --- |
| F01 | `timeline.py` | REFACTOR | Core; immutable compiled graph, one snapshot per component, indexed tracks, shared source-time evaluation | Preserve public authoring, atomic play/add, lifetimes, terminal holds and composition offsets; private Entry storage may change |
| F02 | `animation.py`, `scheduling.py`, `spring.py` | KEEP | Core; deterministic easing, presets, schedules and analytical Spring safety | Move chart/map-specific builders/validation with their domains; no simulation-step replacement for Spring |
| F03 | `components.py`, `motion.py`, `paths.py`, `masks.py`, `gradients.py`, `colors.py` | REFACTOR | Core primitives, immutable paint/path data and generic animation-validation hook | Keep current coordinate, color and anchor semantics; public names retained |
| F04 | `layout.py`, `typography.py`, `_render_state.py` measurement | REPLACE | Core measurement service plus shared geometry evaluation | Replace per-query private Pillow measurement and recursive snapshot measurement; preserve logical/ink bounds and explicit text-engine metrics |
| F05 | `renderer.py`, `_composition_plan.py`, `_compositor.py` | MERGE | Core renderer facade, compiled frame evaluator, common compositor | Share lifecycle/geometry/timing decisions; preserve old Renderer protocol; delete duplicate traversal only after parity |
| F06 | `backends/skia.py`, `_native.py`, `_skia_paint.py`, `_skia_text.py` | REFACTOR; OPTIONAL | Core Skia adapter consuming the common frame plan | Retain native vector/text/surface painting and explicit text selection; no mandatory Skia or guaranteed cross-platform pixel identity |
| F07 | `backends/moderngl.py`, `_gl/device.py`, shaders, `_auto.py`, `gpu.py` | REFACTOR; OPTIONAL | Core ModernGL device/compositor adapter and capability selection | Keep bounded resources, effects, particles, real device identity, software-GL exclusion from auto acceleration; no new mesh renderer |
| F08 | `_raster_adapter.py`, `_cpu_device.py`, `_portable.py`, `_surface_raster.py` | MERGE | Core image/primitive adapters, measurement and cache services | Preserve useful portable fallbacks; remove reliance on PillowRenderer's private methods as integration API |
| F09 | `effects.py`, `_effects_cpu.py`, `procedural.py`, `transitions.py` | KEEP, then targeted REFACTOR; OPTIONAL NumPy | Core semantic effect descriptions and CPU/GPU implementations | CPU reference is needed for fallback/parity. Delegate native blur/filters only when alpha, color-space, edge and radius tests pass; retain reference otherwise |
| F10 | `surfaces.py`, `indicators.py` | REFACTOR | Core retained surfaces and basic progress primitives; Kit styling | Prefer a backend-neutral retained Surface; preserve legacy raster factory output during compatibility. Do not conflate surface shadow clearance with masked leaf shadows |
| F11 | `audio.py`, `export.py`, `progress.py`, `preview.py` | KEEP, focused REFACTOR | Core FFmpeg adapter, audio graph, progress and atomic preview/export publication | Preserve streaming RGB24/H.264/AAC defaults, sample delays, mixed-audio ranges and overwrite behavior; isolate subprocess lifecycle without adding a second encoder stack |
| F12 | `subtitles.py`, `narration.py`; Agent's SRT parser | MERGE parsing, KEEP timing | Core raw cue parser/SubtitleTrack/Captions/CueScene; Kit narration windows | Share parsing but retain different overlap policies and Agent input limits; never retime cues or merge local chapters with global segments indiscriminately |
| F13 | `charts/*` | REFACTOR | `facelesschamp_kit.charts`; primitive lowering, existing scales/data normalization | Keep animated data, rankings, Sankey/graph semantics, units and labels. Retain raster compatibility producer initially; do not replace all charts with Matplotlib images |
| F14 | `maps.py`, `flags.py`, map/flag data | REFACTOR; OPTIONAL map NumPy | `facelesschamp_kit.maps`; bundled offline assets, generic images/paths | Keep country lookup, globe/outline/satellite behavior and source provenance. No mandatory GeoPandas/GIS stack or network maps |
| F15 | `coding.py`, `coding_workspace.py` | REFACTOR; OPTIONAL Pygments | `facelesschamp_kit.coding`; source/token model and editor/terminal compositions | Keep exact code/reveal, named targets and existing styles; syntax tokenization remains delegated to Pygments |
| F16 | `playground/*` | REFACTOR; OPTIONAL preparation | `facelesschamp_kit.playground`; explicit trusted checkpoint execution and prepared playback | Keep outputs/events, bindings, limits, cache integrity and no implicit execution. Python-only preparation must not require Playwright |
| F17 | `web/*` | REFACTOR; OPTIONAL Playwright preparation | `facelesschamp_kit.web`; local browser preparation, generic prepared viewport playback | Keep CSS/script source clocks, selectors, crop/focus geometry and offline replay; installed playback must not need a browser |
| F18 | `flow/*` | REFACTOR | `facelesschamp_kit.diagrams`; graph/script/semantic state and primitive lowering | Keep ports/routes, signals, symbols, sketch behavior and JSON contracts. Adapt the existing raster producer before replacing drawing |
| F19 | Kit `FlowDiagram`, `FlowCanvas`, `FlowDesign` wrappers | MERGE shared lowering/layout | Kit diagrams; lightweight step-flow convenience over graph/primitive mechanisms | Keep independently animatable named children; a raster viewport cannot silently replace that capability. Treat step-flow and semantic graph APIs as distinct frontends |
| F20 | `os_ui/*` | REFACTOR | `facelesschamp_kit.desktop`; virtual filesystem/settings/action state and presentation | Preserve random-access semantic state, hit targets, navigation, scroll and editable artwork; it remains a simulation, not host automation |
| F21 | `arch/model.py`, `camera.py`, `rendering.py`, `_arch_worker.py` | REFACTOR; OPTIONAL | Core `integrations/pyvista/`; immutable scientific source, native part/style/camera contracts and owned sessions | Keep datasets/fields, glyphs, sections, camera projection, shared snapshots, VTK isolation and float-environment guard; split annotation presentation into Kit |
| F22 | `arch/clip.py`, `script.py`, annotations and design authoring | REFACTOR | `facelesschamp_kit.engineering`; public semantic authoring over Core integration | Preserve named parts, source offsets, sections, annotations, fingerprints and structured designs; reuse/re-export Core native part/style types and use generic viewport seam |
| F23 | `arch/cad.py`, `mesh.py`, `dependencies.py` | KEEP adapter logic; OPTIONAL | Core `integrations/build123d.py`, `integrations/trimesh.py`, shared optional dependency diagnostics | Preserve absolute units/tessellation, assemblies, explicit field-loss policy, provenance and native-provider conflict checks; no new CAD/mesh kernel |
| F24 | `arch/cad_models.py`, `mechanical.py`, `blueprint.py` | REFACTOR | Kit engineering models/mechanisms/blueprints; examples for illustrative presets | Keep analytic mechanism poses and CAD-derived drawings. Models are useful recipes, not mandatory engine primitives or physics solvers |
| F25 | `chess.py`, `chess_assets.py`, ChessBoard, starter, assets, guidance | REMOVE | Frozen V1 environment; optional independent source-adapter design outside supported stack | Built-in legal PGN/UCI playback, annotations, themes and artwork leave V2. See the explicit removal ledger below |
| F26 | Kit `project.py`, `context.py`, `assets.py`, dependencies and diagnostics | REFACTOR | Kit public project/build/render services with reusable compiled input | Preserve isolated imports, asset identity, strict assets, profile precedence, explicit preparation and errors; no automatic installation |
| F27 | Kit `video.py`, `compiler.py`, `blocks/base.py` | REFACTOR | Kit authoring records/handles and lowering through public Core | Keep fresh ownership, stable events, named child handles, cue windows and reports. Remove specialist type branches via domain metadata/validation |
| F28 | Kit blocks, layouts, themes, whiteboard, effects, tutorials | KEEP, shared helpers REFACTOR | Kit composition-only modules and editable templates | Core `ColorScheme` and Kit `Theme` serve different roles; keep them. Whiteboard stays a composition frontend; do not build a separate renderer |
| F29 | Kit recipes/templates/scaffold/sample assets | REFACTOR | Kit; domain imports and shared descriptor metadata | Preserve runnable offline starters and required narration; retire chess starter explicitly; no per-domain wheel |
| F30 | Agent models/planning/context | KEEP, parser/service REFACTOR | Agent; Pydantic remains here, shared raw cue parser via Kit | Preserve bounded read-only context, complete source clock, selection vs executable plan distinction, conformance and design precedence |
| F31 | Agent `project.py`, `media.py`, `layout.py`, delivery/errors | REFACTOR | Agent orchestration/policy; Kit render operations and Core media primitives underneath | Preserve evidence checksums, history, output identity, decode/alignment checks, separate preview/full/review status and cancellation |
| F32 | Agent registry and templates | REFACTOR | Agent editorial guidance over Kit public discovery metadata | Keep offline/static discovery and installed-signature authority; avoid importing all optional modules to enumerate APIs |
| F33 | CLI/root exports in all three distributions | REFACTOR | Existing commands and focused lazy facades | Keep commands and supported shared imports; deprecate moved domain imports and report replacements clearly |
| F34 | Documentation snapshots, website, atlas, release evidence scripts | REFACTOR | Canonical Markdown plus generated selected resource snapshots/site metadata | Keep offline Agent guidance; build-time drift checks, schema equivalence and dynamic gallery sizing; historical verification remains historical |
| F35 | Tests, benchmarks, examples and project-local renderers | KEEP, migrate imports | Separate package suites, installed-wheel checks, representative parity/benchmark corpus | Preserve advanced custom Renderer examples; distinguish reusable examples from project content and unverified cloud launchers |
| F36 | Duplicate root/runtime assets | MERGE canonical ownership | Runtime assets beside their owning distribution; source/provenance records retained | Update references before deleting duplicates. Root artist-source assets with different provenance/usage are not automatically redundant |

The [audit module inventory](architecture-audit.md#module-inventory) assigns every
package module to these decision IDs, including entrypoints and sample factories.

## ChessChamp removal ledger

Removal is a user-selected product boundary, not a claim that chess is broken,
unreachable, or duplicated rules code. The implementation already delegates legal
moves and PGN to the optional `chess` package. Its own contribution includes timed
scripts, assets, presentation and annotations. Those capabilities have real migration cost.

| Surface | Required V2 action | Migration route |
| --- | --- | --- |
| `ChessChamp`, `ChessScript`, `ChessTheme`, `ChessAssets`, PGN/UCI/JSON authoring | Announce deprecation in V1; remove supported V2 exports and implementations | Keep unchanged projects in an isolated checkout at the audited V1 commit with the chess extra and lock |
| `renderer.py`, `layout.py`, root exports | Remove chess dispatch/imports after generic sources and V1 migration notes exist | New independent board producers use Core Viewport/RasterSource; no Core → Kit shim |
| Kit block/compiler/template/scaffold/CLI | Remove ChessBoard, chess asset report branch and chess starter | Preserve legacy starter/data documentation with the V1 migration reference |
| `src/faceless_champ/assets/chess/`, `assets/chess/` | Remove both runtime and duplicate repository artwork when no retained reference needs them | Preserve attribution/provenance with the V1 source; do not delete user-supplied project artwork |
| Extras, Agent discovery, benchmark prompts, guides/site/atlas | Remove current capability advertisements and dependency forwarding | Historical documents must label V1 rather than falsely promise V2 support |
| Chess-specific tests | Keep passing on the frozen V1 baseline; replace V2 tests with absence/migration checks | V2 generic-source tests cover viewport transform/cache/timing, not chess legality |

Bundled runtime chess artwork is about 11.087 MiB before wheel compression; all 13
files also have identical root-asset copies. The `chess` dependency is optional
already, so its removal is not the main base-install dependency saving.

An independent extension could use `python-chess` for positions/legal moves and a
Pillow board producer conforming to RasterSource. This is a design alternative,
not an implemented or promised drop-in replacement. No new supported extension
wheel or automatic translation of existing chess scripts is part of V2.

## Consolidation rules

Keep small dependency-free geometry/math that serves the portable backend. Native
Skia painting does not make a tiny Pillow path fallback dead code. Keep CPU effect
references where they define matching GPU semantics. Keep renderer wrappers that
translate ownership, units, fields, or alpha correctly; remove duplicate timeline,
measurement and dispatch policy instead.

No major subsystem was proven dead by the audit. Zero inbound static imports are
insufficient: subprocess workers, CLI entrypoints, public exports and copied sample
factories are dynamically reached. Delete a candidate only with a caller/resource
ledger, an alternative, regression evidence, and a migration note.
