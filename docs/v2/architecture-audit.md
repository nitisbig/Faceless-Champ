# FacelessChamp V2 architecture audit

Audit date: 2026-10-20. Source baseline: `master` commit
`22f3beaccb5a56990bd0974666b7c639a0667a68`; the clean `v2` checkout matched it.
This proposal changes documentation only. No V2 implementation, source cleanup,
dependency installation, release, deployment, or full-film render was performed.

This is the frozen audit snapshot. M1 was subsequently authorized and implemented;
see [the implementation record](m1-implementation.md) for current installation,
lazy-import behavior, and verification. The baseline inventories below remain dated.

## Reading this proposal

| Document | Purpose |
| --- | --- |
| [Dependency analysis](dependency-analysis.md) | Manifests, optional engines, footprint, and complete package import ledger |
| [Feature decisions](feature-decisions.md) | KEEP/REFACTOR/MERGE/REPLACE/OPTIONAL/REMOVE decisions and alternatives |
| [Architecture proposal](architecture-proposal.md) | Layer ownership and canonical scene design |
| [Backend integration](backend-integration.md) | Backend/source contracts and native library boundaries |
| [API design](api-design.md) | Current versus proposed interfaces and migration mappings |
| [Performance baseline](performance-baseline.md) | Actual measurements, limitations and certification method |
| [Migration plan](migration-plan.md) | File-level phases, regression gates and first milestone |

## Executive assessment

V1 already has a useful independent timeline, a public Renderer protocol, streaming
FFmpeg export, composition-aware audio, immutable geometry snapshots, optional
native imports, separate Kit/Agent distributions, and substantial regression tests.
V2 should retain that investment. A wholesale rewrite is not justified by this audit.

The largest immediate installation problem is **required PyVista**, not eager import
of its native engine. Runtime optional imports are generally lazy already. The
larger execution problem is that traversal, measurement, type dispatch and cache
identity remain distributed across renderer implementations and domain components.
Consolidate those seams, then move domain authoring into Kit.

The recommended first milestone is a lightweight standalone Core, detailed at the
end of the [migration plan](migration-plan.md#recommended-first-milestone).

## Coverage and evidence levels

All 283 tracked Python files parsed successfully. The package inventory contains
92 Core, 38 Kit and 15 Agent modules: 145 modules and 27,866 physical source lines
(blank/comment lines included; sample factories included). Package roots declare
166, 20 and 17 `__all__` exports respectively. These are import surfaces, not counts
of independent features. The Agent registry passed its check with 1,008 records:
673 API entries, 301 assets, 23 designs and 11 recipes; aliases are included.

Every package module was mapped for declarations, purpose, imports, ownership and
feature decision. Detailed control/data-flow inspection concentrated on timeline
snapshots/evaluation, renderer traversal/cache paths, composition, measurement,
FFmpeg/audio, native adapters, Kit compilation/project services, and Agent production
and discovery. Domain models/drawing, tests, examples, scripts and documentation
were inspected alongside these paths. Automated inventories are below; this is not
a claim of numerical line/branch coverage or successful execution of every example.

Labels used throughout:

- **Confirmed:** supported directly by current source, a deterministic probe, or
  a completed command against this baseline.
- **Suspected impact:** an observed code path whose cost/failure incidence was not
  isolated experimentally. The proposal specifies a measurement before optimization.
- **Historical:** evidence in existing verification reports, not a new measurement.
- **Proposed:** a V2 design or acceptance target, not present behavior.

## Confirmed findings

| ID | Impact | Evidence and consequence | Recommendation |
| --- | --- | --- | --- |
| V2-A01 | High installation cost | [Core manifest](../../pyproject.toml) requires PyVista for all users. The active Linux base closure contains 32 distributions including Core; installed VTK alone occupies 562.23 MiB by distribution-file accounting. Ordinary 2D users do not need this stack. | OPTIONAL 3D; Core base requires Pillow only; ensure CAD/geometry extras still include the 3D conversion requirements they actually use |
| V2-A02 | High coupling | [renderer.py:15](../../src/faceless_champ/renderer.py#L15) imports domain types; [validate:283](../../src/faceless_champ/renderer.py#L283) and sprite/frame paths dispatch on them. Layout and Kit compilation also enumerate specialist types. | Generic viewport/source seam and domain-owned lowering/validation |
| V2-A03 | Repeated execution policy | Pillow `_scene`/`_affine_scene`, Skia `_visit`, ModernGL `_signature`, and shared Compositor separately evaluate/traverse entries. Existing shared timing/affine/composition utilities only partly consolidate them. | One compiled representation/frame evaluator; keep native painting separate |
| V2-A04 | Backend-dependent measurement | [layout.py:53](../../src/faceless_champ/layout.py#L53) knows specialist types and renderer private methods; `bounds()` creates a PillowRenderer. `_render_state.entry_geometry()` recursively builds evaluated views and calls bounds. | Shared measurement service and prepared geometry; preserve chosen text engine |
| V2-A05 | Quadratic retained snapshots | [Scene.add:227](../../src/faceless_champ/timeline.py#L227) deep-copies every prepared component, including each Group's descendant tree. A chain of 33 authored components produced 561 distinct retained snapshot objects. | One snapshot per node, child IDs/shared snapshot memo; regression on linear retention |
| V2-A06 | Broad import surface | [Core root](../../src/faceless_champ/__init__.py) eagerly imports Python wrappers for many domains and both optional renderer wrappers. Fresh-process import median was 504.90 ms. Optional native engines were not loaded. | Lazy public facade; do not claim this is eager VTK loading |
| V2-A07 | Useful caches lack uniform bounds | Pillow frame/caption/code caches are bounded, but `_images`, `_fonts`, `_sprites`, `_equations` are ordinary dictionaries; GIF decode retains all frames. The raster adapter applies additional eviction. | Common byte/accounting utilities and explicit decoder/source policies; long-scene RSS benefit still requires measurement |
| V2-A08 | Duplicated production plumbing | [Kit Project](../../facelesschamp-kit/src/facelesschamp_kit/project.py) and [AgentProject](../../facelesschamp-agent/src/facelesschamp_agent/project.py) both create renderers and call Core frame/storyboard/export helpers. Agent legitimately needs the already conformance-checked compiled video. | Add compiled-input Kit services; retain Agent's distinct evidence and review policy |
| V2-A09 | Overlapping parsing/presentation mechanisms | Agent context parses raw SRT separately from SubtitleTrack; raster and retained surface authoring choose different component representations; several diagram frontends share presentation work. | Share raw parsing with separate validation policies; consolidate lowering without deleting distinct capabilities |
| V2-A10 | Duplicate assets | SHA-256 grouping of tracked, nonempty files excluding MP3/WAV found 303 identical-content groups and 17,510,653 redundant bytes. Includes 13 chess, 250 flag, 8 networking and 2 font asset groups across root/runtime locations. | Canonical ownership and reference migration; identical bytes alone do not prove one copy is unused |
| V2-A11 | Documentation/discovery drift | Website verifier fails its manifest version assertion. Bundled Agent Core copies differ for coding, ArchChamp, OS UI and Skia; Kit coding-playgrounds copy differs. CAD guide is absent from bundled Core guides. | Generate selected snapshots/metadata from canonical sources; explicit inclusion list and drift checks |
| V2-A12 | Chess maintenance footprint | Chess has 751 source lines in its two Core files, about 11.087 MiB of runtime artwork, renderer/layout/compiler/scaffold/discovery branches and a required domain migration if removed. | REMOVE from V2 per user decision; keep frozen V1 route and independent source-adapter alternative |

These are architectural findings; a high-impact dependency finding does not imply
that current 2D rendering is functionally broken.

## Circular dependencies, dead code and justified overlap

The package direct-reference graph has 405 eager internal edges after excluding
function-local and `TYPE_CHECKING` imports, with no cycles in that graph. Including
deferred/type-only references gives 558 edges and strongly connected groups of 60
Core modules and four CAD/geometry modules. These show coupling, not a demonstrated
runtime import failure. The graph does not model every implicit package initializer,
dynamic import string, or platform branch; successful imports/tests provide separate
runtime evidence.

No major dead subsystem was established. Static zero-inbound candidates include
subprocess workers and copied sample factories. Their dynamic invocation excludes
them from a deletion list. A normalized AST scan found no identical function bodies
of at least 11 lines across the package modules. The meaningful duplication here is
behavioral traversal/measurement/dispatch, not a large confirmed copy-paste body count.

Keep distinctions that solve different problems: Core compositions versus Kit
segments, Core palette roles versus Kit themes, logical versus ink bounds, CPU
effect reference versus GPU implementation, and domain semantic state versus Core
visual tracks. Pydantic is an appropriate Agent contract dependency; moving it into
Core would make the base heavier without evidence of a need.

## Suspected costs and remaining risks

| Observation | What is not established | Required next evidence |
| --- | --- | --- |
| `Entry.state_at()` scans tracks; bounds and renderer traversal revisit state | Relative runtime contribution in a long narrated scene | Profile build/evaluate/measure/draw separately on representative track/group counts |
| Package/project files are hashed during builds and Agent identity checks | Whether hashing dominates authoring latency | Record bytes/files/probe counts and command timings; never weaken evidence invalidation for an unmeasured speedup |
| RGBA conversion/readback and RGB24 encoding copies exist | Their share of total frame/export time | Conversion/readback/pipe/encoder timings, not a blanket zero-copy claim |
| CPU effects use NumPy kernels and temporary arrays | Which native replacement preserves all reference pixels | Targeted alpha/color/edge parity and workload measurements before replacement |
| Arch worker receive/pipe operations can block without a request deadline | An observed hang on this run | Fault-injected stalled-child tests and a bounded cancellation/deadline design |
| Real Chromium integrations are opt-in; hardware EGL was unavailable | Browser revision compatibility, real GPU speed, native/platform portability | Explicit installed-browser tests and hardware/multi-platform runs |

## Executed validation

These commands ran during the audit/planning pass in this same conversation, at
the unchanged source commit. Documentation authoring does not require repeating
the expensive package suites.

```bash
MPLCONFIGDIR=/tmp/fc-v2-audit-mpl PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest tests -q -p no:cacheprovider
MPLCONFIGDIR=/tmp/fc-v2-audit-mpl PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest facelesschamp-kit/tests -q -p no:cacheprovider
MPLCONFIGDIR=/tmp/fc-v2-audit-mpl PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m pytest facelesschamp-agent/tests -q -p no:cacheprovider
python3 website/scripts/verify_examples.py
git diff --check
```

| Check | Result | Limit |
| --- | --- | --- |
| Core | 1,526 passed, 2 skipped, 278.81 s | Two opt-in browser integrations skipped; one Pillow `getdata()` deprecation warning |
| Kit | 305 passed, 88.60 s | Source environment with optional dependencies installed |
| Agent | 177 passed, 232.76 s | Source environment; not a new cloud/full-film delivery |
| Python syntax | All 283 tracked Python files parsed | No numerical coverage claim |
| Public registry | `check()` passed; 1,008 records | API availability does not prove optional runtime availability |
| Blocked-import probe | Core+Kit imported, 320×180 Pillow frame validated, out-of-order repeat identical with 15 external engine modules blocked | Simulation, not a newly built minimal wheel |
| Graph | 145 nodes, 405 eager edges, no eager graph cycle | Dynamic import caveat above |
| ModernGL probe | EGL available, Mesa llvmpipe software device | No hardware acceleration claim |
| Website | Failed at `verify_examples.py:27`, version equality assertion | Confirmed documentation issue, not a renderer test failure |
| Benchmark schema | Packaged JSON equals `BenchmarkResult.model_json_schema()` | Earlier schema-drift finding is resolved at this baseline |
| Git | Clean source checkout before documentation; whitespace check passed | This proposal's final diff is restricted to `docs/v2/` |

The previous [full audit](../audits/full-audit.md) contains historical findings and
fix records. Do not copy its original failure table as current truth: held-boundary,
caption-overlap, reveal, profile, engineering-dimensions, evidence-record, schema
and PNG-publication regressions have relevant current fixes/tests. The current
package suites are the baseline; historical media is not newly verified here.

## Tests, examples, resources and documentation

The generated ancillary inventory below covers every tracked Python file outside
the three package source roots, including tests and project-local helpers.
Parameterized collection produced 1,528 Core, 305 Kit and 177 Agent tests. Raw
defined test functions number 519/144/120 in those roots, plus 52 under `my-project`;
these counts are intentionally different from collected test cases.

Core tests cover source-time semantics, atomic authoring, chart/map/domain data,
native adapters, masks/effects, cache invalidation, source-range audio, encoder
failures, progress and publication. Kit tests cover profiles, fresh block ownership,
cue windows, named layout metadata, recipes and domain starters. Agent tests cover
planning/context limits, discovery, conformance, history/fingerprints, media and
review policy. The existing suites run separately because test module names overlap.

Examples include the narrated Hello World lesson and bounded Skia, ModernGL and
engineering references. Many `my-project` films use custom public Renderer adapters
for source-time scene sampling, shaders or dynamic scientific fields. Keep that
escape hatch. Do not promote every local wrapper into a Core feature. Several
README/verification pairs distinguish previews from unrun full exports; preserve
that distinction when choosing a migration corpus.

The Roadster tree contains project-local Colab tests referencing helpers absent
from the tracked master snapshot. Package suite success does not certify those
cloud workflows. Do not launch remote jobs or repair project-local launchers as a
side effect of the V2 audit.

Canonical documentation includes Core guides/decisions/verification, 13 Kit docs,
6 Agent docs, offline Agent resource snapshots, `llms.txt`, skills, the website and
project atlas. Historical verification and retired reference notes should remain
dated records; regenerate current capability descriptions from selected canonical
guides, not by rewriting history.

The seven GLSL files and `flow/schema.json` are runtime resources. Fonts, their
licenses, flags, map data and networking assets must survive clean wheel builds.
Required demonstration narration is explicitly tracked; keep its distribution
regressions. A source-tree demo succeeding with ignored local media is insufficient.

## Documentation artifact checks

The documentation-only continuation created exactly the eight requested Markdown
files. Validation checked 727 local links/source-line targets, parsed all seven
Python snippets, verified all 145 module-to-decision mappings and all 145 import
ledgers, and checked fences, final newlines and trailing whitespace. All passed.
The tracked production source remained unchanged; package suites were not rerun
for prose-only edits. These checks validate the proposal artifacts, not V2 runtime
behavior or future API availability.

<!-- GENERATED_INVENTORY -->

## Module inventory

Generated from tracked baseline source. Feature IDs refer to the
[decision register](feature-decisions.md#subsystem-register). Each row is
a source module, including private execution modules and copied sample factories.

| Layer | Module / source | Lines | Public local declarations / explicit exports | Decision |
| --- | --- | ---: | --- | --- |
| Core | [src/faceless_champ/__init__.py](../../src/faceless_champ/__init__.py) | 312 | explicit exports: 166 | F33 |
| Core | [src/faceless_champ/__main__.py](../../src/faceless_champ/__main__.py) | 3 | entrypoint / package / private helpers | F33 |
| Core | [src/faceless_champ/_composition_plan.py](../../src/faceless_champ/_composition_plan.py) | 83 | Placement, fit, composition_plan | F05 |
| Core | [src/faceless_champ/_compositor.py](../../src/faceless_champ/_compositor.py) | 231 | density, mask_image, Compositor | F05 |
| Core | [src/faceless_champ/_cpu_device.py](../../src/faceless_champ/_cpu_device.py) | 125 | CPUDevice | F08 |
| Core | [src/faceless_champ/_effects_cpu.py](../../src/faceless_champ/_effects_cpu.py) | 228 | numpy, linear, encoded, pixels, image, sample, resize, kernel, blur, content, halos, background, crossfade | F09 |
| Core | [src/faceless_champ/_portable.py](../../src/faceless_champ/_portable.py) | 149 | guard_size, paint_image, surface_sprite, shape_sprite | F08 |
| Core | [src/faceless_champ/_render_state.py](../../src/faceless_champ/_render_state.py) | 167 | evaluated, component_size, entry_geometry, transformed_box, component_ink_box, ink_box, composition_frame, fit_frame, ByteCache | F04 |
| Core | [src/faceless_champ/_surface_raster.py](../../src/faceless_champ/_surface_raster.py) | 253 | gradient_card | F08 |
| Core | [src/faceless_champ/animation.py](../../src/faceless_champ/animation.py) | 337 | linear, smooth, ease_in, ease_out, Animation, AnimationBuilder, FadeIn, FadeOut, Typewriter, Write, Draw, SlideIn, SlideOut, ZoomIn, ZoomOut, PopIn, PopOut, BounceIn, SpinIn, Pulse, Shake, Wiggle, relative_value, interpolate, ChartReveal | F02 |
| Core | [src/faceless_champ/arch/__init__.py](../../src/faceless_champ/arch/__init__.py) | 37 | explicit exports: 23 | F22 |
| Core | [src/faceless_champ/arch/blueprint.py](../../src/faceless_champ/arch/blueprint.py) | 194 | blueprint_from_cad | F24 |
| Core | [src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py) | 277 | TessellationOptions, mesh_from_cad, parts_from_cad, read_step | F23 |
| Core | [src/faceless_champ/arch/cad_models.py](../../src/faceless_champ/arch/cad_models.py) | 198 | validate_preset, spur_gear, gear_pair, piston, slider_crank, inline_engine, portal_frame | F24 |
| Core | [src/faceless_champ/arch/camera.py](../../src/faceless_champ/arch/camera.py) | 75 | ArchCamera, part_matrix, world, project | F21 |
| Core | [src/faceless_champ/arch/clip.py](../../src/faceless_champ/arch/clip.py) | 554 | validate_design, ArchChamp | F22 |
| Core | [src/faceless_champ/arch/dependencies.py](../../src/faceless_champ/arch/dependencies.py) | 60 | geometry_capabilities | F23 |
| Core | [src/faceless_champ/arch/mechanical.py](../../src/faceless_champ/arch/mechanical.py) | 76 | slider_crank_pose | F24 |
| Core | [src/faceless_champ/arch/mesh.py](../../src/faceless_champ/arch/mesh.py) | 210 | to_trimesh, inspect_mesh, repair_mesh, simplify_mesh, boolean_mesh, parts_from_trimesh_scene | F23 |
| Core | [src/faceless_champ/arch/model.py](../../src/faceless_champ/arch/model.py) | 297 | ArchDataError, number, vector, text, color, construct, pyvista, ArchMesh, ArchStyle, ArchPart, ArchLabel, ArchDimension | F21 |
| Core | [src/faceless_champ/arch/rendering.py](../../src/faceless_champ/arch/rendering.py) | 202 | ArchSession | F21 |
| Core | [src/faceless_champ/arch/script.py](../../src/faceless_champ/arch/script.py) | 242 | ArchAction, ArchScript | F22 |
| Core | [src/faceless_champ/audio.py](../../src/faceless_champ/audio.py) | 60 | require_tools, probe, AudioClip | F11 |
| Core | [src/faceless_champ/backends/__init__.py](../../src/faceless_champ/backends/__init__.py) | 1 | entrypoint / package / private helpers | F33 |
| Core | [src/faceless_champ/backends/_arch_worker.py](../../src/faceless_champ/backends/_arch_worker.py) | 111 | send, receive, ArchWorker, main | F21 |
| Core | [src/faceless_champ/backends/_auto.py](../../src/faceless_champ/backends/_auto.py) | 57 | AutoRenderer | F07 |
| Core | [src/faceless_champ/backends/_gl/__init__.py](../../src/faceless_champ/backends/_gl/__init__.py) | 1 | entrypoint / package / private helpers | F33 |
| Core | [src/faceless_champ/backends/_gl/device.py](../../src/faceless_champ/backends/_gl/device.py) | 477 | shader, Target, GLDevice | F07 |
| Core | [src/faceless_champ/backends/_native.py](../../src/faceless_champ/backends/_native.py) | 39 | load_skia, image_from_pillow, image_to_pillow | F06 |
| Core | [src/faceless_champ/backends/_raster_adapter.py](../../src/faceless_champ/backends/_raster_adapter.py) | 156 | PillowRasterAdapter | F08 |
| Core | [src/faceless_champ/backends/_skia_paint.py](../../src/faceless_champ/backends/_skia_paint.py) | 186 | color, paint, path_data, shape_path, partial_path, draw_shape, draw_surface | F06 |
| Core | [src/faceless_champ/backends/_skia_text.py](../../src/faceless_champ/backends/_skia_text.py) | 150 | TextSession, text_size | F06 |
| Core | [src/faceless_champ/backends/moderngl.py](../../src/faceless_champ/backends/moderngl.py) | 163 | ModernGLRenderer | F07 |
| Core | [src/faceless_champ/backends/skia.py](../../src/faceless_champ/backends/skia.py) | 410 | SkiaRenderer | F06 |
| Core | [src/faceless_champ/charts/__init__.py](../../src/faceless_champ/charts/__init__.py) | 401 | ChartStyle, numbers, labels, Chart, BarChart, RankedBarChart, LineChart, ScatterPlot, Histogram, Heatmap, NetworkGraph, SankeyChart, VectorField, PieChart | F13 |
| Core | [src/faceless_champ/charts/drawing.py](../../src/faceless_champ/charts/drawing.py) | 374 | draw_ranked_bars, draw_chart | F13 |
| Core | [src/faceless_champ/charts/scales.py](../../src/faceless_champ/charts/scales.py) | 152 | Axis, domain, project, separate_positions, ticks, histogram, graph_positions, sankey_geometry, palette_color | F13 |
| Core | [src/faceless_champ/chess.py](../../src/faceless_champ/chess.py) | 648 | ChessDataError, ChessPosition, ChessMove, ChessAnnotation, ChessScript, ChessTheme, ChessChamp | F25 |
| Core | [src/faceless_champ/chess_assets.py](../../src/faceless_champ/chess_assets.py) | 103 | ChessAssets | F25 |
| Core | [src/faceless_champ/cli.py](../../src/faceless_champ/cli.py) | 50 | main | F33 |
| Core | [src/faceless_champ/coding.py](../../src/faceless_champ/coding.py) | 357 | CodeTheme, CodingChamp, CodeReveal, draw_code | F15 |
| Core | [src/faceless_champ/coding_workspace.py](../../src/faceless_champ/coding_workspace.py) | 324 | CodeWindow, CodeWorkspaceDesign | F15 |
| Core | [src/faceless_champ/colors.py](../../src/faceless_champ/colors.py) | 115 | with_alpha, ColorScheme | F03 |
| Core | [src/faceless_champ/components.py](../../src/faceless_champ/components.py) | 440 | finite, Canvas, Component, Text, Number, Equation, Image, ImageSlot, Icon, Shape, Rectangle, Square, Circle, Ellipse, Triangle, Line, Polyline, Arrow | F03 |
| Core | [src/faceless_champ/effects.py](../../src/faceless_champ/effects.py) | 154 | GaussianBlur, OuterGlow, Bloom, Distortion, ChromaticAberration, LightSweep, validate_effect_value, EffectStack, effect_stack, needs_compositor | F09 |
| Core | [src/faceless_champ/export.py](../../src/faceless_champ/export.py) | 245 | ExportSettings, render | F11 |
| Core | [src/faceless_champ/flags.py](../../src/faceless_champ/flags.py) | 38 | supported_flags, flag_path, Flag | F14 |
| Core | [src/faceless_champ/flow/__init__.py](../../src/faceless_champ/flow/__init__.py) | 20 | explicit exports: 11 | F18 |
| Core | [src/faceless_champ/flow/clip.py](../../src/faceless_champ/flow/clip.py) | 331 | FlowChamp | F18 |
| Core | [src/faceless_champ/flow/design.py](../../src/faceless_champ/flow/design.py) | 530 | FlowVisual, FlowDesign | F18 |
| Core | [src/faceless_champ/flow/drawing.py](../../src/faceless_champ/flow/drawing.py) | 263 | prepare_labels, rgba, capsule_sprite, stroke, label_image, composite_center, raster_label, draw_frame | F18 |
| Core | [src/faceless_champ/flow/examples.py](../../src/faceless_champ/flow/examples.py) | 40 | recipe | F18 |
| Core | [src/faceless_champ/flow/geometry.py](../../src/faceless_champ/flow/geometry.py) | 209 | layers, layout_graph, transform, port, port_lead, edge_path, length, sample, prefix | F18 |
| Core | [src/faceless_champ/flow/model.py](../../src/faceless_champ/flow/model.py) | 275 | FlowDataError, number, point, text, choice, color, object_fields, construct, FlowPort, FlowNode, FlowEdge, FlowTheme, FlowGraph | F18 |
| Core | [src/faceless_champ/flow/script.py](../../src/faceless_champ/flow/script.py) | 168 | FlowAction, FlowScript | F18 |
| Core | [src/faceless_champ/flow/symbols.py](../../src/faceless_champ/flow/symbols.py) | 116 | arc, symbol_paths | F18 |
| Core | [src/faceless_champ/gpu.py](../../src/faceless_champ/gpu.py) | 58 | GPUOptions, renderer_capabilities | F07 |
| Core | [src/faceless_champ/gradients.py](../../src/faceless_champ/gradients.py) | 139 | GradientStop, LinearGradient, RadialGradient | F03 |
| Core | [src/faceless_champ/indicators.py](../../src/faceless_champ/indicators.py) | 106 | ProgressBar, ProgressRing, Gauge, LoadingDots, Checkmark, Countdown, draw_indicator | F10 |
| Core | [src/faceless_champ/layout.py](../../src/faceless_champ/layout.py) | 247 | Bounds, transform_point, bounds, next_to, align_to, Group | F04 |
| Core | [src/faceless_champ/maps.py](../../src/faceless_champ/maps.py) | 287 | supported_countries, MapAnimationBuilder, Map, OutlineMap, SatelliteMap, EarthMap, draw_map | F14 |
| Core | [src/faceless_champ/masks.py](../../src/faceless_champ/masks.py) | 72 | Mask, PathMask, RectangleMask, CircleMask, ShapeMask, Wipe | F03 |
| Core | [src/faceless_champ/motion.py](../../src/faceless_champ/motion.py) | 80 | rgba, visual_state, paint_state, style_value, multiply, point, matrix, inverse | F03 |
| Core | [src/faceless_champ/narration.py](../../src/faceless_champ/narration.py) | 72 | CueScene | F12 |
| Core | [src/faceless_champ/os_ui/__init__.py](../../src/faceless_champ/os_ui/__init__.py) | 17 | explicit exports: 9 | F20 |
| Core | [src/faceless_champ/os_ui/clip.py](../../src/faceless_champ/os_ui/clip.py) | 481 | OSClip | F20 |
| Core | [src/faceless_champ/os_ui/drawing.py](../../src/faceless_champ/os_ui/drawing.py) | 465 | font, palette, Painter, display_state, draw_frame | F20 |
| Core | [src/faceless_champ/os_ui/layout.py](../../src/faceless_champ/os_ui/layout.py) | 103 | rect, window_box, listing, geometry | F20 |
| Core | [src/faceless_champ/os_ui/model.py](../../src/faceless_champ/os_ui/model.py) | 262 | File, Folder, VirtualFileSystem, Control, SettingsPage, starter_pages, MacOSPreset | F20 |
| Core | [src/faceless_champ/os_ui/script.py](../../src/faceless_champ/os_ui/script.py) | 144 | Action, OSScript | F20 |
| Core | [src/faceless_champ/paths.py](../../src/faceless_champ/paths.py) | 195 | PathData, VectorPath | F03 |
| Core | [src/faceless_champ/playground/__init__.py](../../src/faceless_champ/playground/__init__.py) | 25 | explicit exports: 16 | F16 |
| Core | [src/faceless_champ/playground/model.py](../../src/faceless_champ/playground/model.py) | 281 | PlaygroundError, fail, json_copy, relative_path, CodeCheckpoint, valid_canvas_value, CanvasItem, ValueBinding, EventBinding, PlaygroundScript | F16 |
| Core | [src/faceless_champ/playground/playback.py](../../src/faceless_champ/playground/playback.py) | 414 | EditTimeline, PlaygroundView, CodeEditor, PlaygroundCanvas, PlaygroundOutput | F16 |
| Core | [src/faceless_champ/playground/prepare.py](../../src/faceless_champ/playground/prepare.py) | 392 | validate_result, PreparedPlayground, prepare_playground | F16 |
| Core | [src/faceless_champ/playground/runtime.py](../../src/faceless_champ/playground/runtime.py) | 35 | inputs, emit, event | F16 |
| Core | [src/faceless_champ/playground/web_worker.py](../../src/faceless_champ/playground/web_worker.py) | 35 | main | F16 |
| Core | [src/faceless_champ/preview.py](../../src/faceless_champ/preview.py) | 143 | StoryboardSample, save_frame, render_storyboard | F11 |
| Core | [src/faceless_champ/procedural.py](../../src/faceless_champ/procedural.py) | 80 | ProceduralBackground, ParticleField, particle_data | F09 |
| Core | [src/faceless_champ/progress.py](../../src/faceless_champ/progress.py) | 79 | ExportProgress | F11 |
| Core | [src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py) | 1017 | Renderer, create_renderer, rendering_identity, validate_composition, managed_renderer, PillowRenderer | F05 |
| Core | [src/faceless_champ/scheduling.py](../../src/faceless_champ/scheduling.py) | 145 | Schedule, Stagger, Succession, Repeat, play_schedule | F02 |
| Core | [src/faceless_champ/spring.py](../../src/faceless_champ/spring.py) | 228 | Spring | F02 |
| Core | [src/faceless_champ/subtitles.py](../../src/faceless_champ/subtitles.py) | 167 | SubtitleCue, SubtitleTrack, Captions | F12 |
| Core | [src/faceless_champ/surfaces.py](../../src/faceless_champ/surfaces.py) | 190 | ShadowStyle, Surface, card_content_bounds, card_surface, gradient_surface, dot_grid | F10 |
| Core | [src/faceless_champ/timeline.py](../../src/faceless_champ/timeline.py) | 640 | Renderable, Track, Entry, Scene, Sequence, Grid, Layer | F01 |
| Core | [src/faceless_champ/transitions.py](../../src/faceless_champ/transitions.py) | 41 | DirectionalWipe, LuminanceWipe, ZoomBlurTransition, transition | F09 |
| Core | [src/faceless_champ/typography.py](../../src/faceless_champ/typography.py) | 93 | fit_text, load_font | F04 |
| Core | [src/faceless_champ/web/__init__.py](../../src/faceless_champ/web/__init__.py) | 18 | explicit exports: 10 | F17 |
| Core | [src/faceless_champ/web/capture.py](../../src/faceless_champ/web/capture.py) | 398 | local_server, input_digest, capture_html | F17 |
| Core | [src/faceless_champ/web/clip.py](../../src/faceless_champ/web/clip.py) | 171 | WebFocus, WebHighlight, WebCallout, HtmlClip | F17 |
| Core | [src/faceless_champ/web/model.py](../../src/faceless_champ/web/model.py) | 163 | WebError, HtmlPage, WebAction, WebScript, WebCapture | F17 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/__init__.py) | 19 | explicit exports: 20 | F33 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/__main__.py](../../facelesschamp-kit/src/facelesschamp_kit/__main__.py) | 3 | entrypoint / package / private helpers | F33 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/assets.py](../../facelesschamp-kit/src/facelesschamp_kit/assets.py) | 107 | digest, unique_object, AssetRegistry | F26 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/__init__.py) | 245 | palette, panel, panel_face, Heading, TextPanel, MetricCard, ImageCard, Comparison, StepList | F28 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/arch.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/arch.py) | 76 | ArchCanvas | F22 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/base.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/base.py) | 61 | BlockBuild, Block, fit_text, centered, build_group | F27 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/chess.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/chess.py) | 38 | ChessBoard | F25 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/coding.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/coding.py) | 94 | CodeEditor, CodingPlayground | F15 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/effects.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/effects.py) | 57 | EffectBlock, ProceduralBackdrop, ParticleBackdrop | F28 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/flow.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/flow.py) | 76 | FlowDiagram | F19 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/flow_canvas.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/flow_canvas.py) | 63 | FlowCanvas | F19 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/flow_design.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/flow_design.py) | 85 | FlowCard, FlowPopup, FlowBackdrop | F19 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/os_ui.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/os_ui.py) | 56 | OSWalkthrough, FinderWindow, SettingsWindow | F20 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/web.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/web.py) | 79 | WebWalkthrough, WebElement | F17 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/blocks/whiteboard.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/whiteboard.py) | 191 | WhiteboardPath, WhiteboardLine, WhiteboardArrow, WhiteboardRectangle, WhiteboardCircle, WhiteboardDrawing | F28 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/cli.py](../../facelesschamp-kit/src/facelesschamp_kit/cli.py) | 176 | doctor, main | F33 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/compiler.py](../../facelesschamp-kit/src/facelesschamp_kit/compiler.py) | 414 | CompiledVideo, descendants, compile_video | F27 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/context.py](../../facelesschamp-kit/src/facelesschamp_kit/context.py) | 99 | BuildContext | F26 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/dependencies.py](../../facelesschamp-kit/src/facelesschamp_kit/dependencies.py) | 66 | dependencies, check_dependencies | F26 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/diagnostics.py](../../facelesschamp-kit/src/facelesschamp_kit/diagnostics.py) | 32 | KitError, number, fields | F26 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/layouts.py](../../facelesschamp-kit/src/facelesschamp_kit/layouts.py) | 48 | Stack, Split | F28 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/project.py](../../facelesschamp-kit/src/facelesschamp_kit/project.py) | 399 | package_version, project_imports, Project, tool_versions | F26 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/recipes.py](../../facelesschamp-kit/src/facelesschamp_kit/recipes.py) | 528 | RecipeSpec, recipe_specs, validate_recipe, RecipeEvent, apply_recipe | F29 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/sample_assets/archchamp.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/archchamp.py) | 20 | build | F29 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_backend.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_backend.py) | 55 | script, build | F29 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_concept.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_concept.py) | 45 | script, build | F29 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_web.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_web.py) | 84 | script, build | F29 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/sample_assets/flowchamp.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/flowchamp.py) | 16 | build | F29 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/sample_assets/os_ui.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/os_ui.py) | 83 | tutorial, build | F29 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/sample_assets/whiteboard.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/whiteboard.py) | 50 | build | F29 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/scaffold.py](../../facelesschamp-kit/src/facelesschamp_kit/scaffold.py) | 220 | init_project | F29 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/templates.py](../../facelesschamp-kit/src/facelesschamp_kit/templates.py) | 244 | WhiteboardScene, whiteboard_basic, silent, narrated, chesschamp, coding_playground | F29 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/themes.py](../../facelesschamp-kit/src/facelesschamp_kit/themes.py) | 111 | Theme | F28 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/tutorials/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/__init__.py) | 5 | explicit exports: 2 | F28 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/__init__.py) | 6 | explicit exports: 2 | F28 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/components.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/components.py) | 197 | CodingTutorialTemplate | F28 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/style.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/style.py) | 116 | CodingTutorialStyle | F28 |
| Kit | [facelesschamp-kit/src/facelesschamp_kit/video.py](../../facelesschamp-kit/src/facelesschamp_kit/video.py) | 248 | Handle, Window, Placement, Segment, Narration, Video | F27 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/__init__.py](../../facelesschamp-agent/src/facelesschamp_agent/__init__.py) | 59 | explicit exports: 17 | F33 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/__main__.py](../../facelesschamp-agent/src/facelesschamp_agent/__main__.py) | 3 | entrypoint / package / private helpers | F33 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/cli.py](../../facelesschamp-agent/src/facelesschamp_agent/cli.py) | 197 | Parser, export_skill, main | F33 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/context.py](../../facelesschamp-agent/src/facelesschamp_agent/context.py) | 452 | read_project_context | F30 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/delivery.py](../../facelesschamp-agent/src/facelesschamp_agent/delivery.py) | 105 | write_render_entrypoint | F31 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/errors.py](../../facelesschamp-agent/src/facelesschamp_agent/errors.py) | 13 | AgentError | F31 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/examples.py](../../facelesschamp-agent/src/facelesschamp_agent/examples.py) | 127 | prepare_example, create_example | F35 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/layout.py](../../facelesschamp-agent/src/facelesschamp_agent/layout.py) | 387 | layout_sample_times, audit_layout | F31 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/media.py](../../facelesschamp-agent/src/facelesschamp_agent/media.py) | 195 | run_tool, pcm, alignment, verify_media | F31 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/models.py](../../facelesschamp-agent/src/facelesschamp_agent/models.py) | 311 | Record, NarrationInput, AssetInput, VideoBrief, DesignSpec, StoryBeat, StoryPlan, KeyEvent, ScenePlan, VideoPlan, ReviewFinding, ReviewSubmission, QualityReport, HumanScores, BenchmarkResult, BeatSelection, SelectionPlan | F30 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/planning.py](../../facelesschamp-agent/src/facelesschamp_agent/planning.py) | 723 | select_scenes, plan_project | F30 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/project.py](../../facelesschamp-agent/src/facelesschamp_agent/project.py) | 905 | AgentProject, init_project | F31 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/registry.py](../../facelesschamp-agent/src/facelesschamp_agent/registry.py) | 728 | CapabilityRegistry | F32 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/scaffold.py](../../facelesschamp-agent/src/facelesschamp_agent/scaffold.py) | 81 | entrypoint / package / private helpers | F35 |
| Agent | [facelesschamp-agent/src/facelesschamp_agent/templates.py](../../facelesschamp-agent/src/facelesschamp_agent/templates.py) | 111 | default_coding_template, load_coding_tutorial, install_coding_tutorial, coding_template_guidance | F32 |

## Public API inventory

This source-derived inventory includes explicit `__all__` aliases, public local
functions/classes, constructors, public methods/properties, selected lifecycle
dunder methods, and public data declarations. If a module has no `__all__`,
a public local name is a candidate surface, not a promise that every helper
or incidental imported name is a supported stable API. Dataclass annotated
fields are shown because constructors are generated. Signatures are syntax
from this commit, not runtime availability checks. Re-export aliases are
not counted as independent implementations. Private helpers are inventoried
through their modules/imports, not proposed as public V2 APIs.

### faceless_champ

[src/faceless_champ/__init__.py](../../src/faceless_champ/__init__.py)

Explicit exports:

```text
CLEAN_FLOW_FONT -> faceless_champ.typography.CLEAN_FLOW_FONT
COLOR_SCHEMES -> faceless_champ.colors.COLOR_SCHEMES
Animation -> faceless_champ.animation.Animation
Arrow -> faceless_champ.components.Arrow
Axis -> faceless_champ.charts.Axis
BarChart -> faceless_champ.charts.BarChart
Bloom -> faceless_champ.effects.Bloom
BounceIn -> faceless_champ.animation.BounceIn
Bounds -> faceless_champ.layout.Bounds
Canvas -> faceless_champ.components.Canvas
Captions -> faceless_champ.subtitles.Captions
Chart -> faceless_champ.charts.Chart
ChartReveal -> faceless_champ.animation.ChartReveal
ChartStyle -> faceless_champ.charts.ChartStyle
ChromaticAberration -> faceless_champ.effects.ChromaticAberration
Circle -> faceless_champ.components.Circle
ColorScheme -> faceless_champ.colors.ColorScheme
Component -> faceless_champ.components.Component
CueScene -> faceless_champ.narration.CueScene
DirectionalWipe -> faceless_champ.transitions.DirectionalWipe
Distortion -> faceless_champ.effects.Distortion
Draw -> faceless_champ.animation.Draw
EarthMap -> faceless_champ.maps.EarthMap
EffectStack -> faceless_champ.effects.EffectStack
Ellipse -> faceless_champ.components.Ellipse
Equation -> faceless_champ.components.Equation
ExportProgress -> faceless_champ.progress.ExportProgress
ExportSettings -> faceless_champ.export.ExportSettings
FadeIn -> faceless_champ.animation.FadeIn
FadeOut -> faceless_champ.animation.FadeOut
Flag -> faceless_champ.flags.Flag
GPUOptions -> faceless_champ.gpu.GPUOptions
GaussianBlur -> faceless_champ.effects.GaussianBlur
GradientStop -> faceless_champ.gradients.GradientStop
Grid -> faceless_champ.timeline.Grid
Group -> faceless_champ.layout.Group
Heatmap -> faceless_champ.charts.Heatmap
Histogram -> faceless_champ.charts.Histogram
Icon -> faceless_champ.components.Icon
Image -> faceless_champ.components.Image
ImageSlot -> faceless_champ.components.ImageSlot
Layer -> faceless_champ.timeline.Layer
LightSweep -> faceless_champ.effects.LightSweep
Line -> faceless_champ.components.Line
LineChart -> faceless_champ.charts.LineChart
LinearGradient -> faceless_champ.gradients.LinearGradient
LuminanceWipe -> faceless_champ.transitions.LuminanceWipe
ModernGLRenderer -> faceless_champ.backends.moderngl.ModernGLRenderer
NetworkGraph -> faceless_champ.charts.NetworkGraph
Number -> faceless_champ.components.Number
OuterGlow -> faceless_champ.effects.OuterGlow
OutlineMap -> faceless_champ.maps.OutlineMap
ParticleField -> faceless_champ.procedural.ParticleField
PathData -> faceless_champ.paths.PathData
PathMask -> faceless_champ.masks.PathMask
PieChart -> faceless_champ.charts.PieChart
PillowRenderer -> faceless_champ.renderer.PillowRenderer
Polyline -> faceless_champ.components.Polyline
PopIn -> faceless_champ.animation.PopIn
PopOut -> faceless_champ.animation.PopOut
ProceduralBackground -> faceless_champ.procedural.ProceduralBackground
Pulse -> faceless_champ.animation.Pulse
RadialGradient -> faceless_champ.gradients.RadialGradient
RankedBarChart -> faceless_champ.charts.RankedBarChart
Rectangle -> faceless_champ.components.Rectangle
Renderer -> faceless_champ.renderer.Renderer
SankeyChart -> faceless_champ.charts.SankeyChart
SatelliteMap -> faceless_champ.maps.SatelliteMap
ScatterPlot -> faceless_champ.charts.ScatterPlot
Scene -> faceless_champ.timeline.Scene
Sequence -> faceless_champ.timeline.Sequence
ShadowStyle -> faceless_champ.surfaces.ShadowStyle
Shake -> faceless_champ.animation.Shake
SkiaRenderer -> faceless_champ.backends.skia.SkiaRenderer
SlideIn -> faceless_champ.animation.SlideIn
SlideOut -> faceless_champ.animation.SlideOut
SpinIn -> faceless_champ.animation.SpinIn
Spring -> faceless_champ.spring.Spring
Square -> faceless_champ.components.Square
StoryboardSample -> faceless_champ.preview.StoryboardSample
SubtitleCue -> faceless_champ.subtitles.SubtitleCue
SubtitleTrack -> faceless_champ.subtitles.SubtitleTrack
Surface -> faceless_champ.surfaces.Surface
Text -> faceless_champ.components.Text
Triangle -> faceless_champ.components.Triangle
Typewriter -> faceless_champ.animation.Typewriter
VectorField -> faceless_champ.charts.VectorField
VectorPath -> faceless_champ.paths.VectorPath
Wiggle -> faceless_champ.animation.Wiggle
Write -> faceless_champ.animation.Write
ZoomBlurTransition -> faceless_champ.transitions.ZoomBlurTransition
ZoomIn -> faceless_champ.animation.ZoomIn
ZoomOut -> faceless_champ.animation.ZoomOut
card_content_bounds -> faceless_champ.surfaces.card_content_bounds
card_surface -> faceless_champ.surfaces.card_surface
create_renderer -> faceless_champ.renderer.create_renderer
dot_grid -> faceless_champ.surfaces.dot_grid
ease_in -> faceless_champ.animation.ease_in
ease_out -> faceless_champ.animation.ease_out
fit_text -> faceless_champ.typography.fit_text
flag_path -> faceless_champ.flags.flag_path
gradient_surface -> faceless_champ.surfaces.gradient_surface
linear -> faceless_champ.animation.linear
render -> faceless_champ.export.render
render_storyboard -> faceless_champ.preview.render_storyboard
renderer_capabilities -> faceless_champ.gpu.renderer_capabilities
rendering_identity -> faceless_champ.renderer.rendering_identity
save_frame -> faceless_champ.preview.save_frame
smooth -> faceless_champ.animation.smooth
supported_countries -> faceless_champ.maps.supported_countries
supported_flags -> faceless_champ.flags.supported_flags
validate_composition -> faceless_champ.renderer.validate_composition
with_alpha -> faceless_champ.colors.with_alpha
Checkmark -> faceless_champ.indicators.Checkmark
CircleMask -> faceless_champ.masks.CircleMask
Countdown -> faceless_champ.indicators.Countdown
Gauge -> faceless_champ.indicators.Gauge
LoadingDots -> faceless_champ.indicators.LoadingDots
ProgressBar -> faceless_champ.indicators.ProgressBar
ProgressRing -> faceless_champ.indicators.ProgressRing
RectangleMask -> faceless_champ.masks.RectangleMask
Repeat -> faceless_champ.scheduling.Repeat
ShapeMask -> faceless_champ.masks.ShapeMask
Stagger -> faceless_champ.scheduling.Stagger
Succession -> faceless_champ.scheduling.Succession
Wipe -> faceless_champ.masks.Wipe
CodeReveal -> faceless_champ.coding.CodeReveal
CodeTheme -> faceless_champ.coding.CodeTheme
CodingChamp -> faceless_champ.coding.CodingChamp
CodeWindow -> faceless_champ.coding_workspace.CodeWindow
CodeWorkspaceDesign -> faceless_champ.coding_workspace.CodeWorkspaceDesign
ChessAssets -> faceless_champ.chess.ChessAssets
ChessChamp -> faceless_champ.chess.ChessChamp
ChessScript -> faceless_champ.chess.ChessScript
ChessTheme -> faceless_champ.chess.ChessTheme
CanvasItem -> faceless_champ.playground.CanvasItem
CodeCheckpoint -> faceless_champ.playground.CodeCheckpoint
CodeEditor -> faceless_champ.playground.CodeEditor
EditTimeline -> faceless_champ.playground.EditTimeline
EventBinding -> faceless_champ.playground.EventBinding
PlaygroundCanvas -> faceless_champ.playground.PlaygroundCanvas
PlaygroundError -> faceless_champ.playground.PlaygroundError
PlaygroundOutput -> faceless_champ.playground.PlaygroundOutput
PlaygroundScript -> faceless_champ.playground.PlaygroundScript
PreparedPlayground -> faceless_champ.playground.PreparedPlayground
ValueBinding -> faceless_champ.playground.ValueBinding
prepare_playground -> faceless_champ.playground.prepare_playground
FlowChamp -> faceless_champ.flow.FlowChamp
FlowDataError -> faceless_champ.flow.FlowDataError
FlowDesign -> faceless_champ.flow.FlowDesign
FlowEdge -> faceless_champ.flow.FlowEdge
FlowGraph -> faceless_champ.flow.FlowGraph
FlowNode -> faceless_champ.flow.FlowNode
FlowPort -> faceless_champ.flow.FlowPort
FlowScript -> faceless_champ.flow.FlowScript
FlowTheme -> faceless_champ.flow.FlowTheme
FlowVisual -> faceless_champ.flow.FlowVisual
ArchCamera -> faceless_champ.arch.ArchCamera
ArchChamp -> faceless_champ.arch.ArchChamp
ArchDataError -> faceless_champ.arch.ArchDataError
ArchDimension -> faceless_champ.arch.ArchDimension
ArchLabel -> faceless_champ.arch.ArchLabel
ArchMesh -> faceless_champ.arch.ArchMesh
ArchPart -> faceless_champ.arch.ArchPart
ArchScript -> faceless_champ.arch.ArchScript
ArchStyle -> faceless_champ.arch.ArchStyle
```

### faceless_champ._composition_plan

[src/faceless_champ/_composition_plan.py](../../src/faceless_champ/_composition_plan.py)

Local declarations (line numbers are baseline source lines):

```text
L8 class Placement
  field node: object
  field time: float
  field viewport: tuple
  field background: str
L15 fit(canvas, size)
L39 composition_plan(node, time, size)
```

### faceless_champ._compositor

[src/faceless_champ/_compositor.py](../../src/faceless_champ/_compositor.py)

Local declarations (line numbers are baseline source lines):

```text
L16 density(world)
L22 mask_image(c, state, box, roi, q, size)
L84 class Compositor
  L85 __init__(self, device, raster, antialias=1)
  L88 frame(self, node, time, size)
  L97 fitted(self, target, node, time, bg)
  L104 node(self, target, node, time)
  L133 leaf(self, target, c, state, box, world, opacity, age)
  L159 visit(self, target, entry, time, parent, inherited)
```

### faceless_champ._cpu_device

[src/faceless_champ/_cpu_device.py](../../src/faceless_champ/_cpu_device.py)

Local declarations (line numbers are baseline source lines):

```text
L13 class CPUDevice
  L14 __init__(self, working_mb=512)
  L19 surface(self, size, color='#00000000')
  L32 clear(self, target, color='#00000000')
  L35 upload(self, image, key=None)
  L38 blit(self, target, source, box, world=IDENTITY, opacity=1)
  L65 mask(self, target, mask)
  L68 content(self, target, stack, scale, time, content_box=None)
  L74 halos(self, target, stack, scale)
  L80 shadow(self, target, shadow, scale, include_content=True)
  L100 mix(self, target, first, second, progress, transition)
  L106 component(self, target, c, state, box, world, opacity, age)
  L121 finish(self, target, size)
  L124 close(self)
```

### faceless_champ._effects_cpu

[src/faceless_champ/_effects_cpu.py](../../src/faceless_champ/_effects_cpu.py)

Local declarations (line numbers are baseline source lines):

```text
L11 numpy()
L19 linear(value)
L24 encoded(value)
L30 pixels(image)
L37 image(a)
L47 sample(a, x, y)
L61 resize(a, size)
L70 kernel(radius)
L79 blur(a, radius)
L102 content(source, stack, scale, time, content_box=None)
L132 halos(source, stack, scale)
L157 background(component, age, size, *, bounds)
L196 crossfade(first, second, progress, transition=None)
```

### faceless_champ._portable

[src/faceless_champ/_portable.py](../../src/faceless_champ/_portable.py)

Local declarations (line numbers are baseline source lines):

```text
L11 guard_size(size)
L16 paint_image(fill, width, height, size)
L25 surface_sprite(c, factor)
L68 shape_sprite(c, state, factor)
```

### faceless_champ._render_state

[src/faceless_champ/_render_state.py](../../src/faceless_champ/_render_state.py)

Local declarations (line numbers are baseline source lines):

```text
L14 evaluated(entry, time)
L24 component_size(c, state, raster, age)
L42 entry_geometry(entry, time, parent, raster)
L63 transformed_box(box, world)
L73 component_ink_box(c, box)
L84 ink_box(entry, time, parent, raster)
L109 composition_frame(renderer, node, time, size)
L130 fit_frame(renderer, node, time, size, bg)
L139 class ByteCache
  L142 __init__(self, limit)
  L147 get(self, key)
  L153 put(self, key, value, cost)
  L165 clear(self)
```

### faceless_champ._surface_raster

[src/faceless_champ/_surface_raster.py](../../src/faceless_champ/_surface_raster.py)

Local declarations (line numbers are baseline source lines):

```text
L205 gradient_card(bounds, gradient, radius, shadow, inset)
```

### faceless_champ.animation

[src/faceless_champ/animation.py](../../src/faceless_champ/animation.py)

Local declarations (line numbers are baseline source lines):

```text
L12 linear(t: float) -> float
L16 smooth(t: float) -> float
L20 ease_in(t: float) -> float
L24 ease_out(t: float) -> float
L29 class Animation
  field component: Component
  field targets: dict
  field starts: dict | None
  field keyframes: dict[str, tuple[tuple[float, object], ...]] | None
  field relative: tuple[str, ...]
  field rate_func: Callable[[float], float] | None
L38 class AnimationBuilder(Animation)
  L39 __init__(self, component: Component) -> None
  L51 fill_to(self, color) -> Self
  L56 effect_to(self, name, **parameters) -> Self
  L64 stroke_to(self, color) -> Self
  L69 color_to(self, color) -> Self
  L74 width_to(self, value) -> Self
  L77 height_to(self, value) -> Self
  L80 stroke_width_to(self, value) -> Self
  L83 corner_radius_to(self, value) -> Self
  L86 scale_xy_to(self, x, y) -> Self
  L89 progress_to(self, value) -> Self
  L92 mask_to(self, *, position=None, width=None, height=None) -> Self
  L98 data_to(self, data) -> Self
  L106 value_to(self, value: float) -> Self
  L114 move_to(self, x: float, y: float) -> Self
  L118 scale_to(self, value: float) -> Self
  L122 rotate_to(self, degrees: float) -> Self
  L126 opacity_to(self, value: float) -> Self
L134 FadeIn(component: Component) -> Animation
L138 FadeOut(component: Component) -> Animation
L142 Typewriter(component: Text) -> Animation
L148 Write(component: Equation) -> Animation
L155 Draw(component: Shape) -> Animation
L175 SlideIn(component: Component, *, direction: str='up', distance: float=80) -> Animation
L188 SlideOut(component: Component, *, direction: str='down', distance: float=80) -> Animation
L198 ZoomIn(component: Component, *, from_scale: float=0.6) -> Animation
L210 ZoomOut(component: Component, *, to_scale: float=0.6) -> Animation
L217 PopIn(component: Component, *, from_scale: float=0.45, overshoot: float=1.14) -> Animation
L232 PopOut(component: Component, *, to_scale: float=0.45, overshoot: float=1.08) -> Animation
L245 BounceIn(component: Component, *, distance: float=80) -> Animation
L260 SpinIn(component: Component, *, angle: float=-35, from_scale: float=0.7) -> Animation
L277 Pulse(component: Component, *, factor: float=1.12, cycles: int=1) -> Animation
L288 Shake(component: Component, *, distance: float=14, direction: str='horizontal', cycles: int=2) -> Animation
L305 Wiggle(component: Component, *, angle: float=8, cycles: int=2) -> Animation
L316 relative_value(property: str, base, value)
L325 interpolate(a, b, t)
L331 ChartReveal(component) -> Animation
```

### faceless_champ.arch

[src/faceless_champ/arch/__init__.py](../../src/faceless_champ/arch/__init__.py)

Explicit exports:

```text
ArchCamera -> faceless_champ.arch.camera.ArchCamera
ArchChamp -> faceless_champ.arch.clip.ArchChamp
ArchDataError -> faceless_champ.arch.model.ArchDataError
ArchDimension -> faceless_champ.arch.model.ArchDimension
ArchLabel -> faceless_champ.arch.model.ArchLabel
ArchMesh -> faceless_champ.arch.model.ArchMesh
ArchPart -> faceless_champ.arch.model.ArchPart
ArchScript -> faceless_champ.arch.script.ArchScript
ArchStyle -> faceless_champ.arch.model.ArchStyle
TessellationOptions -> faceless_champ.arch.cad.TessellationOptions
blueprint_from_cad -> faceless_champ.arch.blueprint.blueprint_from_cad
boolean_mesh -> faceless_champ.arch.mesh.boolean_mesh
geometry_capabilities -> faceless_champ.arch.dependencies.geometry_capabilities
inspect_mesh -> faceless_champ.arch.mesh.inspect_mesh
mesh_from_cad -> faceless_champ.arch.cad.mesh_from_cad
parts_from_cad -> faceless_champ.arch.cad.parts_from_cad
parts_from_trimesh_scene -> faceless_champ.arch.mesh.parts_from_trimesh_scene
read_step -> faceless_champ.arch.cad.read_step
repair_mesh -> faceless_champ.arch.mesh.repair_mesh
simplify_mesh -> faceless_champ.arch.mesh.simplify_mesh
slider_crank_pose -> faceless_champ.arch.mechanical.slider_crank_pose
to_trimesh -> faceless_champ.arch.mesh.to_trimesh
validate_design -> faceless_champ.arch.clip.validate_design
```

### faceless_champ.arch.blueprint

[src/faceless_champ/arch/blueprint.py](../../src/faceless_champ/arch/blueprint.py)

Explicit exports:

```text
blueprint_from_cad
```

Local declarations (line numbers are baseline source lines):

```text
L17 blueprint_from_cad(shape, *, camera=None, width=1600, height=900, margin=70, dimensions=(), source_units='mm', target_units='mm', color='#63d3ff', hidden_color='#567080', font=None, font_size=24, linear_deflection=0.05, max_segments=20000)
```

### faceless_champ.arch.cad

[src/faceless_champ/arch/cad.py](../../src/faceless_champ/arch/cad.py)

Explicit exports:

```text
TessellationOptions
mesh_from_cad
parts_from_cad
read_step
```

Local declarations (line numbers are baseline source lines):

```text
L46 class TessellationOptions
  field linear_deflection: float
  field angular_deflection: float
  field weld_tolerance: float
  field max_triangles: int
L69 mesh_from_cad(shape, *, options=None, source_units='mm', target_units='mm', provenance=None)
L135 parts_from_cad(shape, *, options=None, source_units='mm', target_units='mm', provenance=None)
L217 read_step(path)
```

### faceless_champ.arch.cad_models

[src/faceless_champ/arch/cad_models.py](../../src/faceless_champ/arch/cad_models.py)

Explicit exports:

```text
gear_pair
inline_engine
piston
portal_frame
slider_crank
spur_gear
validate_preset
```

Public data declarations: `CAD_PRESETS`.

Local declarations (line numbers are baseline source lines):

```text
L22 validate_preset(name, params=None)
L67 spur_gear(module=2, teeth=24, width=10, bore=6, pressure_angle=20)
L112 gear_pair(module=2, teeth=(24, 48), width=10, bore=6, pressure_angle=20)
L126 piston(diameter=12, height=14, pin_diameter=3)
L139 slider_crank(crank_radius=10, rod_length=35, diameter=12)
L154 inline_engine(cylinders=4, crank_radius=10, rod_length=35, diameter=12, pitch=24)
L177 portal_frame(bays=3, bay_width=4000, height=3000, depth=3000, member=200)
```

### faceless_champ.arch.camera

[src/faceless_champ/arch/camera.py](../../src/faceless_champ/arch/camera.py)

Local declarations (line numbers are baseline source lines):

```text
L10 class ArchCamera
  field position: tuple
  field focal_point: tuple
  field up: tuple
  field projection: str
  field zoom: float
  field view_angle: float
L33 part_matrix(state)
L49 world(point, part, states)
L55 project(point, camera, width, height, parallel_scale)
```

### faceless_champ.arch.clip

[src/faceless_champ/arch/clip.py](../../src/faceless_champ/arch/clip.py)

Public data declarations: `PRIMITIVES`.

Local declarations (line numbers are baseline source lines):

```text
L40 validate_design(data, *, registered_only=False)
L135 class ArchChamp(Component)
  L136 __init__(self, parts, script=None, *, width=1600, height=900, camera=None, style=None, labels=(), dimensions=(), units='model units', font=None, source_start=0, **kwargs)
  L245 @classmethod from_data(cls, data, **kwargs)
  L266 @classmethod from_file(cls, path, **kwargs)
  L275 @classmethod from_dict(cls, data, *, mesh_resolver=None, cad_resolver=None, **kwargs)
  L330 geometry_record(self)
  L338 state_at(self, time)
  L454 frame_key(self, age)
  L460 project_at(self, time, points, *, part=None)
  L504 annotation_overlay(self, time, factor=1)
  L535 diagnostics_at(self, time)
  L549 frame_image(self, age, factor=1)
```

### faceless_champ.arch.dependencies

[src/faceless_champ/arch/dependencies.py](../../src/faceless_champ/arch/dependencies.py)

Explicit exports:

```text
geometry_capabilities
```

Local declarations (line numbers are baseline source lines):

```text
L28 geometry_capabilities(*, cad=False, geometry=False)
```

### faceless_champ.arch.mechanical

[src/faceless_champ/arch/mechanical.py](../../src/faceless_champ/arch/mechanical.py)

Explicit exports:

```text
slider_crank_pose
```

Local declarations (line numbers are baseline source lines):

```text
L18 slider_crank_pose(angle, crank_radius, rod_length)
```

### faceless_champ.arch.mesh

[src/faceless_champ/arch/mesh.py](../../src/faceless_champ/arch/mesh.py)

Explicit exports:

```text
boolean_mesh
inspect_mesh
parts_from_trimesh_scene
repair_mesh
simplify_mesh
to_trimesh
```

Local declarations (line numbers are baseline source lines):

```text
L13 to_trimesh(mesh, *, drop_fields=False)
L39 inspect_mesh(mesh)
L88 repair_mesh(mesh, *, merge_vertices=False, fill_holes=False, drop_fields=False)
L109 simplify_mesh(mesh, target_faces, *, drop_fields=False)
L140 boolean_mesh(meshes, operation='union', *, drop_fields=False)
L168 parts_from_trimesh_scene(scene, *, scale=1, drop_fields=False)
```

### faceless_champ.arch.model

[src/faceless_champ/arch/model.py](../../src/faceless_champ/arch/model.py)

Public data declarations: `CONCEPTS`.

Local declarations (line numbers are baseline source lines):

```text
L12 class ArchDataError(ValueError)
  L13 __init__(self, field, message)
L18 number(value, name, minimum=None)
L26 vector(value, name)
L32 text(value, name)
L42 color(value)
L50 construct(cls, value)
L59 pyvista()
L67 class ArchMesh
  L75 __init__(self, dataset, *, source=None, provenance=None)
  L113 @classmethod from_data(cls, data, *, provenance=None)
  L125 @classmethod from_file(cls, path)
  L137 @classmethod from_arrays(cls, points, faces=None, *, point_data=None, cell_data=None, provenance=None)
  L171 @property provenance(self)
  L176 @property dataset(self)
L199 class ArchStyle
  field concept: str
  field color: str
  field edge_color: str
  field opacity: float
  field line_width: float
  field point_size: float
  field scalars: str | None
  field vectors: str | None
  field field_mode: str
  field clim: tuple | None
  field cmap: str
  field association: str
  field voxel_spacing: float
  field smooth_shading: bool
L239 class ArchPart
  field id: str
  field mesh: ArchMesh
  field position: tuple
  field rotation: tuple
  field scale: float
  field style: ArchStyle | None
  field explode_vector: tuple
L260 class ArchLabel
  field text: str
  field point: tuple
  field part: str | None
  field offset: tuple
  field color: str
  field font_size: float
L279 class ArchDimension
  field start: tuple
  field end: tuple
  field part: str | None
  field offset: tuple
  field color: str
  field font_size: float
  field precision: int
```

### faceless_champ.arch.rendering

[src/faceless_champ/arch/rendering.py](../../src/faceless_champ/arch/rendering.py)

Local declarations (line numbers are baseline source lines):

```text
L10 class ArchSession
  L11 __init__(self, clip, factor=1)
  L108 frame(self, age)
  L189 close(self)
  L198 __enter__(self)
  L201 __exit__(self, *exc)
```

### faceless_champ.arch.script

[src/faceless_champ/arch/script.py](../../src/faceless_champ/arch/script.py)

Public data declarations: `PROPERTIES`, `OPTIONS`.

Local declarations (line numbers are baseline source lines):

```text
L11 class ArchAction
  field kind: str
  field targets: tuple
  field at: float
  field duration: float
  field args: tuple
  field easing: str
  L20 @property options(self)
L51 class ArchScript
  L52 __init__(self)
  L57 @property actions(self)
  L61 @property duration(self)
  L64 wait(self, duration=1)
  L88 move(self, targets, position, **timing)
  L91 rotate(self, targets, rotation, **timing)
  L94 scale(self, targets, value, **timing)
  L97 opacity(self, targets, value, **timing)
  L103 explode(self, targets, factor=1, **timing)
  L106 highlight(self, targets, color_value='#ffcc66', **timing)
  L109 hide(self, targets, **timing)
  L112 show(self, targets, **timing)
  L115 camera_to(self, camera, **timing)
  L120 orbit(self, degrees=90, **timing)
  L123 section(self, targets, origin, normal=(1, 0, 0), *, cap=False, contour=True, **timing)
  L131 spin(self, targets, degrees=360, *, axis=(0, 0, 1), pivot=(0, 0, 0), **timing)
  L140 gear_pair(self, driver, driven, *, teeth=(24, 48), degrees=360, **timing)
  L158 slider_crank(self, targets, *, crank_radius=10, rod_length=35, turns=1, phase=0, **timing)
  L180 to_dict(self)
  L199 @classmethod from_dict(cls, data)
```

### faceless_champ.audio

[src/faceless_champ/audio.py](../../src/faceless_champ/audio.py)

Local declarations (line numbers are baseline source lines):

```text
L12 require_tools() -> None
L18 probe(path: Path) -> dict
L32 class AudioClip
  field path: Path
  field start: float
  field trim_start: float
  field trim_end: float | None
  field volume: float
  field fade_in: float
  field fade_out: float
  field duration: float
```

### faceless_champ.backends._arch_worker

[src/faceless_champ/backends/_arch_worker.py](../../src/faceless_champ/backends/_arch_worker.py)

Local declarations (line numbers are baseline source lines):

```text
L20 send(stream, value)
L29 receive(stream)
L46 class ArchWorker
  L47 __init__(self)
  L53 sprite(self, c, state, factor, age)
  L70 close(self)
L84 main()
```

### faceless_champ.backends._auto

[src/faceless_champ/backends/_auto.py](../../src/faceless_champ/backends/_auto.py)

Local declarations (line numbers are baseline source lines):

```text
L4 class AutoRenderer
  L5 __init__(self, antialias=2, *, gpu=None, **options)
  L11 __enter__(self)
  L14 __exit__(self, *exc)
  L17 validate(self, node)
  L47 frame(self, node, time, size)
  L54 close(self)
```

### faceless_champ.backends._gl.device

[src/faceless_champ/backends/_gl/device.py](../../src/faceless_champ/backends/_gl/device.py)

Local declarations (line numbers are baseline source lines):

```text
L16 shader(name)
L20 class Target
  L21 __init__(self, texture, framebuffer=None, retained=False)
  L26 release(self)
L32 class GLDevice
  L33 __init__(self, ctx, gl, options)
  L70 surface(self, size, color='#00000000', dtype='f2')
  L108 clear(self, target, color='#00000000')
  L113 cached(self, key)
  L120 upload(self, image, key=None)
  L159 release_upload(self, value)
  L167 @staticmethod uniforms(program, values)
  L172 draw(self, target, name, box, world=IDENTITY, **values)
  L193 blit(self, target, source, box, world=IDENTITY, opacity=1)
  L198 run(self, target, source, operation=0, second=None, **values)
  L221 replace(self, target, operation, **values)
  L226 blur(self, target, source, radius)
  L249 content(self, target, stack, scale, time, content_box=None)
  L274 mask(self, target, image)
  L281 halos(self, target, stack, scale)
  L310 shadow(self, target, shadow, scale, include_content=True)
  L327 mix(self, target, first, second, progress, transition)
  L350 component(self, target, c, state, box, world, opacity, age)
  L453 finish(self, target, size)
  L464 close(self)
```

### faceless_champ.backends._native

[src/faceless_champ/backends/_native.py](../../src/faceless_champ/backends/_native.py)

Local declarations (line numbers are baseline source lines):

```text
L6 load_skia()
L19 image_from_pillow(image, skia)
L30 image_to_pillow(image, skia)
```

### faceless_champ.backends._raster_adapter

[src/faceless_champ/backends/_raster_adapter.py](../../src/faceless_champ/backends/_raster_adapter.py)

Local declarations (line numbers are baseline source lines):

```text
L49 class PillowRasterAdapter
  L50 __init__(self, limit_mb=64, arch_session_limit=4, *, isolate_arch=False)
  L60 renderer_age_key(self, c, age)
  L78 sprite(self, c, state, factor, age)
  L143 native_text_size(self, c, state)
  L150 close(self)
```

### faceless_champ.backends._skia_paint

[src/faceless_champ/backends/_skia_paint.py](../../src/faceless_champ/backends/_skia_paint.py)

Local declarations (line numbers are baseline source lines):

```text
L11 color(s, value, opacity=1)
L16 paint(s, fill, box, opacity=1)
L55 path_data(s, data)
L62 shape_path(s, c, state)
L94 partial_path(s, path, progress)
L115 draw_shape(s, canvas, c, state, opacity)
L157 draw_surface(s, canvas, c, opacity=1)
```

### faceless_champ.backends._skia_text

[src/faceless_champ/backends/_skia_text.py](../../src/faceless_champ/backends/_skia_text.py)

Local declarations (line numbers are baseline source lines):

```text
L15 class TextSession
  L16 __init__(self)
  L56 layout(self, c, state)
  L121 paint(self, canvas, c, state)
  L127 close(self)
L146 text_size(c, state)
```

### faceless_champ.backends.moderngl

[src/faceless_champ/backends/moderngl.py](../../src/faceless_champ/backends/moderngl.py)

Explicit exports:

```text
ModernGLRenderer
```

Local declarations (line numbers are baseline source lines):

```text
L13 class ModernGLRenderer
  L14 __init__(self, antialias=1, *, gpu=None)
  L81 __enter__(self)
  L85 __exit__(self, *exc)
  L88 validate(self, node)
  L128 frame(self, node, time, size)
  L148 close(self)
```

### faceless_champ.backends.skia

[src/faceless_champ/backends/skia.py](../../src/faceless_champ/backends/skia.py)

Local declarations (line numbers are baseline source lines):

```text
L22 class SkiaRenderer
  L30 __init__(self, antialias=1, *, frame_cache_mb=64, native_cache_mb=64, working_mb=256, arch_session_limit=4)
  L52 __enter__(self)
  L55 __exit__(self, *exc)
  L58 close(self)
  L68 validate(self, node)
  L111 frame(self, node, time, size)
```

### faceless_champ.charts

[src/faceless_champ/charts/__init__.py](../../src/faceless_champ/charts/__init__.py)

Explicit exports:

```text
Axis -> faceless_champ.charts.scales.Axis
BarChart
Chart
ChartStyle
Heatmap
Histogram
LineChart
NetworkGraph
PieChart
RankedBarChart
SankeyChart
ScatterPlot
VectorField
```

Local declarations (line numbers are baseline source lines):

```text
L16 class ChartStyle
  field scheme: ColorScheme
  field colors: tuple[str, ...]
  field font_size: float
  field title_size: float
  field grid: bool
  field legend: bool
  field font: str | Path | None
  field font_weight: float | None
  field title_font: str | Path | None
  field title_font_weight: float | None
  field line_width: float
  L43 color(self, i)
L47 numbers(values, name='data')
L54 labels(values)
L61 class Chart(Component)
  L66 __init__(self, *, width=640, height=420, title='', style=None, x_axis=None, y_axis=None, **kwargs)
  L74 state(self)
  L77 transition_data(self, data)
  L84 validate_data(self, values)
L90 class BarChart(Chart)
  L93 __init__(self, categories, series, *, stacked=False, **kwargs)
  L110 normalize(self, data)
  L118 validate_data(self, values)
L123 class RankedBarChart(Chart)
  L133 __init__(self, values, *, top_n=None, label_width=180, value_width=100, value_formatter=None, missing_label='No data', bar_height=None, corner_radius=4, show_markers=True, **kwargs)
  L168 normalize(self, data)
  L179 validate_data(self, values)
L188 class LineChart(Chart)
  L191 __init__(self, series, *, end_labels=False, **kwargs)
  L202 normalize(self, data)
  L212 validate_data(self, values)
L218 class ScatterPlot(LineChart)
  L219 __init__(self, series, *, sizes=None, **kwargs)
L226 class Histogram(Chart)
  L230 __init__(self, samples, *, bins=10, **kwargs)
  L248 normalize(self, data)
  L251 validate_data(self, values)
L257 class Heatmap(Chart)
  L258 __init__(self, matrix, *, row_labels=None, column_labels=None, color_limits=None, palette=('#16324f', '#48e0cb', '#fff2b0'), colorbar=True, **kwargs)
  L285 normalize(self, data)
L292 class NetworkGraph(Chart)
  L295 __init__(self, nodes, edges, *, weights=None, positions=None, directed=False, **kwargs)
  L317 normalize(self, data)
  L323 validate_data(self, values)
L328 class SankeyChart(NetworkGraph)
  L331 __init__(self, nodes, links, **kwargs)
L340 class VectorField(Chart)
  L344 __init__(self, samples, *, vector_scale=1, equal_units=True, **kwargs)
  L360 normalize(self, data)
L367 class PieChart(Chart)
  L368 __init__(self, categories, values, *, hole=0, **kwargs)
  L376 normalize(self, data)
  L382 validate_data(self, values)
```

### faceless_champ.charts.drawing

[src/faceless_champ/charts/drawing.py](../../src/faceless_champ/charts/drawing.py)

Local declarations (line numbers are baseline source lines):

```text
L30 draw_ranked_bars(c, state, factor)
L104 draw_chart(chart, state, factor)
```

### faceless_champ.charts.scales

[src/faceless_champ/charts/scales.py](../../src/faceless_champ/charts/scales.py)

Local declarations (line numbers are baseline source lines):

```text
L12 class Axis
  field scale: str
  field limits: tuple[float, float] | None
  field ticks: tuple[float, ...] | None
  field label: str
  field unit: str
  field formatter: Callable[[float], str] | None
  L35 format(self, value)
L39 domain(values, axis, *, zero=False)
L56 project(value, bounds, scale='linear')
L63 separate_positions(positions, minimum_gap, bounds)
L80 ticks(bounds, axis)
L96 histogram(samples, edges)
L105 graph_positions(nodes, edges, *, flow=False)
L128 sankey_geometry(nodes, edges, weights, positions, height)
L148 palette_color(value, bounds, palette)
```

### faceless_champ.chess

[src/faceless_champ/chess.py](../../src/faceless_champ/chess.py)

Local declarations (line numbers are baseline source lines):

```text
L28 class ChessDataError(ValueError)
  L31 __init__(self, path, message, move_index=None)
L74 class ChessPosition
  field pieces: tuple[tuple[int, str], ...]
  field fen: str
  field turn: str
  field check_square: int | None
  field status: str
  field san: str
L107 class ChessMove
  field at: float
  field duration: float
  field uci: str
  field before: ChessPosition
  field after: ChessPosition
  field moving: tuple[tuple[int, int, str], ...]
  L116 @property end(self)
L121 class ChessAnnotation
  field type: str
  field at: float
  field duration: float
  field text: str
  field squares: tuple[int, ...]
  field color: str | None
L131 class ChessScript
  field duration: float
  field players: tuple[str, str]
  field orientation: str
  field initial: ChessPosition
  field moves: tuple[ChessMove, ...]
  field annotations: tuple[ChessAnnotation, ...]
  field audio: str | None
  field result: str
  field asset_directory: Path | None
  field board_grid: tuple | None
  L143 __init__(self, data, *, base_path=None)
  L288 @classmethod from_dict(cls, data, *, base_path=None)
  L292 @classmethod from_json(cls, path)
  L300 @classmethod from_pgn(cls, pgn, *, move_duration=0.45, move_interval=0.7, lead_in=1, tail=2, players=None)
  L343 to_dict(self)
  L379 position_at(self, time)
  L384 active_move(self, time)
  L388 annotations_at(self, time)
L393 class ChessTheme
  field light: str
  field dark: str
  field background: str
  field panel: str
  field foreground: str
  field muted: str
  field accent: str
  field check: str
  field white_piece: str
  field black_piece: str
L410 class ChessChamp(Component)
  L413 __init__(self, script, *, width=1600, height=900, source_start=0, theme=None, assets=None, **kwargs)
  L518 square_center(self, square)
  L528 frame_key(self, age)
  L531 frame_image(self, age, factor=1)
```

### faceless_champ.chess_assets

[src/faceless_champ/chess_assets.py](../../src/faceless_champ/chess_assets.py)

Public data declarations: `PIECE_FILES`.

Local declarations (line numbers are baseline source lines):

```text
L17 class ChessAssets
  L25 __init__(self, directory, *, board_grid=None)
  L69 @classmethod bundled(cls)
  L73 @property checksums(self)
```

### faceless_champ.cli

[src/faceless_champ/cli.py](../../src/faceless_champ/cli.py)

Local declarations (line numbers are baseline source lines):

```text
L12 main() -> int
```

### faceless_champ.coding

[src/faceless_champ/coding.py](../../src/faceless_champ/coding.py)

Public data declarations: `MONO_FONT`.

Local declarations (line numbers are baseline source lines):

```text
L23 class CodeTheme
  field background: str
  field chrome: str
  field foreground: str
  field muted: str
  field accent: str
  field highlight: str
  field syntax: Mapping[str, str]
  L64 @classmethod named(cls, name: str) -> CodeTheme
  L109 token_color(self, name)
L118 class CodingChamp(Component)
  L126 __init__(self, code: str, *, language='text', theme='midnight', width=1200, height=720, font_size=32, font=None, filename='', chrome=True, line_numbers=True, highlighted_lines=(), reveal_mode='typewriter', reveal=1, block_ends=None, first_line=1, tab_size=4, padding=28, **kwargs)
  L192 @property reveal(self)
  L196 reveal(self, value)
  L202 state(self)
  L264 visible_count(self, progress)
L274 CodeReveal(panel: CodingChamp, start=0, end=1) -> Animation
L284 draw_code(panel, state, factor, renderer)
```

### faceless_champ.coding_workspace

[src/faceless_champ/coding_workspace.py](../../src/faceless_champ/coding_workspace.py)

Local declarations (line numbers are baseline source lines):

```text
L39 class CodeWindow(Group)
  L48 __init__(self, bounds, *, title='', theme='clean-flow', fullscreen=False, unit=1, children=(), surface_mode='raster', text_engine='pillow')
L180 class CodeWorkspaceDesign
  field bounds: Bounds
  field theme: str | CodeTheme
  field background: str
  field editor_scale: float
  field code_size: float
  field terminal_size: float
  field shrink_duration: float
  field restore_duration: float
  field terminal_entrance_duration: float
  field terminal_exit_duration: float
  field surface_mode: str
  field text_engine: str
  L230 @classmethod named(cls, name, **kwargs)
  L237 @property unit(self)
  L241 @property editor_full(self)
  L245 @property editor_split(self)
  L253 @property terminal_bounds(self)
  L258 @property code_bounds(self)
  L267 @staticmethod fluid(progress)
  L271 window(self, box, title, *, children=(), fullscreen=False)
  L283 editor_motion(self, window, *, running)
  L295 editor_corners(self, window, *, running)
  L302 terminal_in(self, window)
  L312 terminal_out(self, window)
```

### faceless_champ.colors

[src/faceless_champ/colors.py](../../src/faceless_champ/colors.py)

Public data declarations: `COLOR_SCHEMES`.

Local declarations (line numbers are baseline source lines):

```text
L11 with_alpha(color: str, opacity: float) -> str
L21 class ColorScheme
  field name: str
  field background: str
  field surface: str
  field text: str
  field muted: str
  field axis: str
  field border: str
  field grid: str
  field primary: str
  field secondary: str
  field tertiary: str
  field highlight: str
  L51 @classmethod named(cls, name: str) -> 'ColorScheme'
  L57 color(self, role: str) -> str
  L62 series(self, index: int) -> str
```

### faceless_champ.components

[src/faceless_champ/components.py](../../src/faceless_champ/components.py)

Local declarations (line numbers are baseline source lines):

```text
L19 finite(value: float, name: str, minimum: float | None=None) -> float
L27 class Canvas
  field width: int
  field height: int
  field bg: str
  L39 @property aspect_ratio(self) -> float
L43 class Component
  L44 __init__(self, *, position: tuple[float, float]=(0, 0), anchor: str='center', scale: float=1.0, scale_x: float=1.0, scale_y: float=1.0, mask=None, shadow=None, effects=None, rotation: float=0.0, opacity: float=1.0, z_index: float=0) -> None
  L92 move_to(self, x: float, y: float) -> Self
  L96 shift(self, dx: float, dy: float) -> Self
  L101 @property bounds(self) -> Bounds
  L107 next_to(self, other: Component | Bounds, *, direction: str='right', gap: float=20, align: str='center') -> Self
  L116 align_to(self, other: Component | Bounds, *, edge: str='left') -> Self
  L124 @property animate(self) -> AnimationBuilder
  L129 state(self) -> dict
L146 class Text(Component)
  L147 __init__(self, text: str, *, font: str | Path | None=None, font_size: float=64, color: str='white', align: str='left', spacing: float=8, font_weight: float | None=None, text_engine: str='pillow', **kwargs: Any) -> None
L175 class Number(Text)
  L182 __init__(self, value: float, *, format_spec: str=',.0f', prefix: str='', suffix: str='', formatter: Callable[[float], str] | None=None, width: float | None=None, **kwargs: Any) -> None
  L201 format(self, value: float) -> str
  L208 state(self) -> dict
L212 class Equation(Component)
  L219 __init__(self, expression: str, *, font_size: float=64, color: str='white', fontset: str='stix', max_width: float | None=None, color_map: Mapping[str, str] | None=None, **kwargs: Any) -> None
L255 class Image(Component)
  L262 __init__(self, path: str | Path, *, width: float=400, height: float=300, fit: str='contain', trim: bool=False, tint: str | None=None, **kwargs: Any) -> None
  L282 @classmethod from_source(cls, source, **kwargs) -> Self
L301 class ImageSlot(Image)
  L309 __init__(self, path: str | Path, *, mode: str='auto', label: str | None=None, placeholder_fill: str='#F4F3EE', placeholder_stroke: str='#B1ADA1', placeholder_color: str='#292724', placeholder_font: str | Path | None=None, placeholder_font_size: float=30, **kwargs: Any) -> None
L333 class Icon(Image)
  L336 __init__(self, path: str | Path, *, size: float=120, color: str='white', **kwargs: Any) -> None
L341 class Shape(Component)
  L342 __init__(self, *, width: float=200, height: float=200, fill: str | None=None, stroke: str | None='white', stroke_width: float=4, **kwargs: Any) -> None
L358 class Rectangle(Shape)
  L359 __init__(self, *, corner_radius: float=0, **kwargs: Any) -> None
L366 class Square(Rectangle)
  L367 __init__(self, side: float=200, **kwargs: Any) -> None
L371 class Circle(Shape)
  L372 __init__(self, radius: float=100, **kwargs: Any) -> None
L376 class Ellipse(Shape)
L380 class Triangle(Shape)
L384 class Line(Shape)
  L387 __init__(self, length: float=200, **kwargs: Any) -> None
L391 class Polyline(Shape)
  L398 __init__(self, points, *, closed: bool=False, line_cap: str='butt', draw_by: str='length', **kwargs: Any) -> None
L422 class Arrow(Line)
  L425 __init__(self, start: tuple[float, float], end: tuple[float, float], *, tip_size: float=18, **kwargs: Any) -> None
```

### faceless_champ.effects

[src/faceless_champ/effects.py](../../src/faceless_champ/effects.py)

Explicit exports:

```text
Bloom
ChromaticAberration
Distortion
EffectStack
GaussianBlur
LightSweep
OuterGlow
```

Local declarations (line numbers are baseline source lines):

```text
L23 class GaussianBlur(_Effect)
  field radius: float
L28 class OuterGlow(_Effect)
  field color: str
  field radius: float
  field intensity: float
L35 class Bloom(_Effect)
  field radius: float
  field threshold: float
  field intensity: float
L42 class Distortion(_Effect)
  field amplitude: float
  field frequency: float
  field speed: float
L49 class ChromaticAberration(_Effect)
  field offset: float
L54 class LightSweep(_Effect)
  field intensity: float
  field width: float
  field speed: float
L75 validate_effect_value(key, value)
L86 class EffectStack
  field blur: GaussianBlur | None
  field glow: OuterGlow | None
  field bloom: Bloom | None
  field distortion: Distortion | None
  field chromatic: ChromaticAberration | None
  field light_sweep: LightSweep | None
  L99 state(self)
  L108 evaluated(self, state)
  L126 @property padding(self)
L135 effect_stack(value)
L141 needs_compositor(node)
```

### faceless_champ.export

[src/faceless_champ/export.py](../../src/faceless_champ/export.py)

Local declarations (line numbers are baseline source lines):

```text
L21 class ExportSettings
  field quality: str
  field width: int | None
  field height: int | None
  field fps: float
  field crf: int
  field preset: str
  field antialias: int
  field backend: str
  field gpu: GPUOptions | None
  L32 dimensions(self, canvas: Canvas) -> tuple[int, int]
L127 render(node: Renderable, output: str | Path, *, settings: ExportSettings | None=None, renderer: Renderer | None=None, overwrite: bool=False, progress: Callable[[int, int], None] | None=None, start_time: float=0.0, end_time: float | None=None, **options) -> Path
```

### faceless_champ.flags

[src/faceless_champ/flags.py](../../src/faceless_champ/flags.py)

Local declarations (line numbers are baseline source lines):

```text
L13 supported_flags() -> tuple[str, ...]
L18 flag_path(country_code: str) -> Path
L28 class Flag(Image)
  L35 __init__(self, country_code: str, *, width: float=120, height: float=80, **kwargs: Any) -> None
```

### faceless_champ.flow

[src/faceless_champ/flow/__init__.py](../../src/faceless_champ/flow/__init__.py)

Explicit exports:

```text
SYMBOLS -> faceless_champ.flow.model.SYMBOLS
FlowChamp -> faceless_champ.flow.clip.FlowChamp
FlowDataError -> faceless_champ.flow.model.FlowDataError
FlowDesign -> faceless_champ.flow.design.FlowDesign
FlowEdge -> faceless_champ.flow.model.FlowEdge
FlowGraph -> faceless_champ.flow.model.FlowGraph
FlowNode -> faceless_champ.flow.model.FlowNode
FlowPort -> faceless_champ.flow.model.FlowPort
FlowScript -> faceless_champ.flow.script.FlowScript
FlowTheme -> faceless_champ.flow.model.FlowTheme
FlowVisual -> faceless_champ.flow.design.FlowVisual
```

### faceless_champ.flow.clip

[src/faceless_champ/flow/clip.py](../../src/faceless_champ/flow/clip.py)

Local declarations (line numbers are baseline source lines):

```text
L21 class FlowChamp(Component)
  L22 __init__(self, graph, script=None, *, width=1600, height=900, theme=None, source_start=0, label_cache_mb=8, **kwargs)
  L96 frame_key(self, age)
  L102 diagnostics_at(self, time)
  L190 paths_for(self, id, states)
  L196 state_at(self, time)
  L259 bounds_for(self, target, time=0)
  L284 frame_image(self, age, factor=1)
  L289 to_dict(self)
  L301 @classmethod from_dict(cls, data, *, base_path=None, **kwargs)
  L325 @classmethod from_json(cls, path, **kwargs)
```

### faceless_champ.flow.design

[src/faceless_champ/flow/design.py](../../src/faceless_champ/flow/design.py)

Local declarations (line numbers are baseline source lines):

```text
L102 class FlowVisual(Group)
  L110 __init__(self, parts, face_bounds, **kwargs)
  L120 @property parts(self)
  L124 @property face_bounds(self)
L136 class FlowDesign
  field name: str
  field font: str
  field surface_mode: str
  field text_engine: str
  L162 @classmethod named(cls, name, **kwargs)
  L166 @property palette(self)
  L170 @property shadow(self)
  L174 @property shadow_padding(self)
  L178 @staticmethod icon_path(name)
  L188 @property asset_paths(self)
  L207 node_card(self, label, *, icon, position=(0, 0), size=(240, 260), detail=None, address=None)
  L268 popup(self, kind, value, position=(0, 0))
  L300 packet_marker(self, position=(0, 0), color=None)
  L315 backdrop(self, bounds=_DEFAULT_BOUNDS)
  L326 @staticmethod pop_frames(position, scale=1, duration=1)
  L344 @staticmethod move_frames(source, destination, source_scale=1, destination_scale=1, duration=1)
  L364 @staticmethod apply_transform(script, target, frames, *, at=0, duration=1)
  L382 @staticmethod transform_animation(component, frames, *, offset=(0, 0))
  L402 connection_theme(self, stroke_width=4.5)
  L418 signal(self, script, targets, *, at=None, duration=1, direction='forward', color=None, fade=0.2)
  L459 complete_connections(self, script, edges, duration)
  L491 connections(self, graph, script=None, *, width=1600, height=900, source_start=0, **component_kwargs)
```

### faceless_champ.flow.drawing

[src/faceless_champ/flow/drawing.py](../../src/faceless_champ/flow/drawing.py)

Public data declarations: `CARD_SYMBOLS`.

Local declarations (line numbers are baseline source lines):

```text
L17 prepare_labels(clip)
L46 rgba(color, opacity=1)
L52 capsule_sprite(color, factor=1)
L74 stroke(draw, points, fill, width, dashed=False)
L96 label_image(clip, id, factor, color)
L122 composite_center(layer, sprite, position, origin=(0, 0))
L129 raster_label(clip, id, state, factor)
L150 draw_frame(clip, snapshot, factor)
```

### faceless_champ.flow.examples

[src/faceless_champ/flow/examples.py](../../src/faceless_champ/flow/examples.py)

Local declarations (line numbers are baseline source lines):

```text
L7 recipe(family='workflow', *, portrait=False)
```

### faceless_champ.flow.geometry

[src/faceless_champ/flow/geometry.py](../../src/faceless_champ/flow/geometry.py)

Local declarations (line numbers are baseline source lines):

```text
L9 layers(graph)
L58 layout_graph(graph, width, height)
L88 transform(p, state)
L95 port(node, state, id, destination)
L130 port_lead(node, state, id, endpoint)
L142 edge_path(edge, nodes, states)
L184 length(points)
L188 sample(points, progress)
L199 prefix(points, progress)
```

### faceless_champ.flow.model

[src/faceless_champ/flow/model.py](../../src/faceless_champ/flow/model.py)

Public data declarations: `SYMBOLS`.

Local declarations (line numbers are baseline source lines):

```text
L37 class FlowDataError(ValueError)
  L38 __init__(self, path, message)
L43 number(value, path, minimum=None)
L51 point(value, path)
L57 text(value, path)
L63 choice(value, values, path)
L68 color(value, path)
L77 object_fields(data, allowed, path, required=())
L88 construct(cls, data, path, required=())
L97 class FlowPort
  field id: str
  field side: str
  field offset: float
L111 class FlowNode
  field id: str
  field label: str
  field symbol: str
  field position: tuple | None
  field size: tuple
  field ports: tuple
  field image: str | None
  field rotation: float
  field scale: float
L148 class FlowEdge
  field id: str
  field source: str
  field target: str
  field source_port: str | None
  field target_port: str | None
  field label: str
  field route: str
  field waypoints: tuple
  field dashed: bool
  field arrows: str
  field label_position: float
  field label_offset: tuple
L182 class FlowTheme
  field foreground: str
  field surface: str
  field accent: str
  field background: str
  field font: str | None
  field font_size: float
  field minimum_font_size: float
  field stroke_width: float
  field sketch: bool
  field seed: int
  field stroke: str | None
  field node_stroke: str | None
  field highlight_width: float
L216 class FlowGraph
  field nodes: tuple
  field edges: tuple
  field layout: str
  field direction: str
  L244 to_dict(self)
  L248 @classmethod from_dict(cls, data, *, base_path=None)
  L273 @classmethod from_json(cls, path)
```

### faceless_champ.flow.script

[src/faceless_champ/flow/script.py](../../src/faceless_champ/flow/script.py)

Public data declarations: `OPTIONS`.

Local declarations (line numbers are baseline source lines):

```text
L23 class FlowAction
  field kind: str
  field targets: tuple[str, ...]
  field at: float
  field duration: float
  field args: tuple
  L31 @property options(self)
  L35 @property end(self)
L39 class FlowScript
  L40 __init__(self)
  L44 @property actions(self)
  L48 @property duration(self)
  L111 reveal(self, targets, **kwargs)
  L114 hide(self, targets, **kwargs)
  L117 move(self, targets, position, **kwargs)
  L120 scale(self, targets, value, **kwargs)
  L123 rotate(self, targets, value, **kwargs)
  L126 signal(self, targets, **kwargs)
  L129 highlight(self, targets, **kwargs)
  L132 draw(self, targets, **kwargs)
  L135 to_dict(self)
  L144 @classmethod from_dict(cls, data)
  L167 @classmethod from_json(cls, path)
```

### faceless_champ.flow.symbols

[src/faceless_champ/flow/symbols.py](../../src/faceless_champ/flow/symbols.py)

Local declarations (line numbers are baseline source lines):

```text
L6 arc(cx, cy, rx, ry, start=0, end=360, steps=48)
L16 symbol_paths(symbol)
```

### faceless_champ.gpu

[src/faceless_champ/gpu.py](../../src/faceless_champ/gpu.py)

Explicit exports:

```text
GPUOptions
renderer_capabilities
```

Local declarations (line numbers are baseline source lines):

```text
L10 class GPUOptions
  field context_backend: str
  field device_index: int | None
  field texture_cache_mb: float
  field working_mb: float
  field frame_cache_mb: float
L28 renderer_capabilities(backend='moderngl', *, probe=False, gpu=None)
```

### faceless_champ.gradients

[src/faceless_champ/gradients.py](../../src/faceless_champ/gradients.py)

Local declarations (line numbers are baseline source lines):

```text
L26 class GradientStop
  field offset: float
  field color: str
L64 class LinearGradient
  field stops: tuple[GradientStop, ...]
  field angle: float
L79 class RadialGradient
  field stops: tuple[GradientStop, ...]
  field center: tuple[float, float]
  field radius: float
```

### faceless_champ.indicators

[src/faceless_champ/indicators.py](../../src/faceless_champ/indicators.py)

Local declarations (line numbers are baseline source lines):

```text
L12 class ProgressBar(Component)
  L13 __init__(self, *, progress=0, width=240, height=20, color='#48e0cb', track_color='#26354a', stroke_width=10, label=False, **kwargs)
  L34 state(self)
L38 class ProgressRing(ProgressBar)
  L39 __init__(self, *, width=120, height=120, **kwargs)
L43 class Gauge(ProgressRing)
L47 class LoadingDots(ProgressBar)
  L50 __init__(self, *, width=100, height=24, **kwargs)
L54 class Checkmark(ProgressBar)
  L55 __init__(self, *, width=80, height=80, **kwargs)
L59 class Countdown(Number)
  L62 __init__(self, seconds, **kwargs)
L67 draw_indicator(c, state, factor, renderer)
```

### faceless_champ.layout

[src/faceless_champ/layout.py](../../src/faceless_champ/layout.py)

Local declarations (line numbers are baseline source lines):

```text
L13 class Bounds
  field left: float
  field top: float
  field right: float
  field bottom: float
  L28 @property width(self) -> float
  L32 @property height(self) -> float
  L36 @property center(self) -> tuple[float, float]
L40 transform_point(point, origin, state)
L125 bounds(component: Component) -> Bounds
L167 next_to(component, other, *, direction='right', gap=20, align='center')
L171 align_to(component, other, *, edge='left')
L188 class Group(Component)
  L195 __init__(self, *children: Component, **kwargs: Any) -> None
  L220 @property children(self) -> tuple[Component, ...]
  L223 arrange(self, *, direction: str='right', gap: float=20, align: str='center') -> Self
```

### faceless_champ.maps

[src/faceless_champ/maps.py](../../src/faceless_champ/maps.py)

Public data declarations: `ASSETS`, `OCEANS`.

Local declarations (line numbers are baseline source lines):

```text
L38 supported_countries()
L76 class MapAnimationBuilder(AnimationBuilder)
  L77 __init__(self, component)
  L81 zoom_to(self, target, *, zoom=None)
  L88 rotate(self, degrees=None, *, longitude=None, latitude=None)
L97 class Map(Component)
  L100 __init__(self, *, width=800, height=400, longitude=0, latitude=0, zoom=1, **kwargs)
  L110 @property animate(self)
  L113 state(self)
  L137 zoom_to(self, target, *, zoom=None)
  L151 rotate(self, degrees=None, *, longitude=None, latitude=None)
L160 class OutlineMap(Map)
  L161 __init__(self, country=None, *, fill=None, border_color='white', border_width=1, **kwargs)
L174 class SatelliteMap(Map)
L178 class EarthMap(Map)
  L179 __init__(self, *, width=600, height=600, **kwargs)
L243 draw_map(c, state, factor)
```

### faceless_champ.masks

[src/faceless_champ/masks.py](../../src/faceless_champ/masks.py)

Local declarations (line numbers are baseline source lines):

```text
L9 class Mask
  field width: float
  field height: float
  field position: tuple
  field kind: str
  field points: tuple
  field path: object
L40 class PathMask(Mask)
  L43 __init__(self, path, *, width, height, position=(0, 0))
L47 class RectangleMask(Mask)
L51 class CircleMask(Mask)
  L52 __init__(self, radius, *, position=(0, 0))
L57 class ShapeMask(Mask)
  L60 __init__(self, points, *, width, height, position=(0, 0))
L66 Wipe(component, *, direction='right')
```

### faceless_champ.motion

[src/faceless_champ/motion.py](../../src/faceless_champ/motion.py)

Public data declarations: `IDENTITY`.

Local declarations (line numbers are baseline source lines):

```text
L8 rgba(value)
L19 visual_state(c)
L36 paint_state(value)
L42 style_value(key, value)
L50 multiply(a, b)
L63 point(m, x, y)
L68 matrix(state, origin=(0, 0))
L77 inverse(m)
```

### faceless_champ.narration

[src/faceless_champ/narration.py](../../src/faceless_champ/narration.py)

Local declarations (line numbers are baseline source lines):

```text
L12 class CueScene(Scene)
  L20 __init__(self, track: SubtitleTrack, canvas: Canvas | None=None, *, start_time: float=0, end_time: float | None=None) -> None
  L38 @property segment_duration(self) -> float
  L41 cue_time(self, index: int, *, edge: str='start', offset: float=0) -> float
  L59 at_cue(self, index: int, *, edge: str='start', offset: float=0)
  L63 finish(self) -> Self
```

### faceless_champ.os_ui

[src/faceless_champ/os_ui/__init__.py](../../src/faceless_champ/os_ui/__init__.py)

Explicit exports:

```text
Control -> faceless_champ.os_ui.model.Control
File -> faceless_champ.os_ui.model.File
Folder -> faceless_champ.os_ui.model.Folder
MacOSPreset -> faceless_champ.os_ui.model.MacOSPreset
OSClip -> faceless_champ.os_ui.clip.OSClip
OSScript -> faceless_champ.os_ui.script.OSScript
SettingsPage -> faceless_champ.os_ui.model.SettingsPage
VirtualFileSystem -> faceless_champ.os_ui.model.VirtualFileSystem
starter_pages -> faceless_champ.os_ui.model.starter_pages
```

### faceless_champ.os_ui.clip

[src/faceless_champ/os_ui/clip.py](../../src/faceless_champ/os_ui/clip.py)

Local declarations (line numbers are baseline source lines):

```text
L17 class OSClip(Component)
  L24 __init__(self, filesystem=None, script=None, *, preset=None, pages=None, mode='desktop', width=1920, height=1080, source_start=0, cursor=True, **kwargs)
  L458 state_at(self, time)
  L462 bounds_for(self, target, time=0)
  L475 frame_key(self, age)
  L478 frame_image(self, age, factor=1)
```

### faceless_champ.os_ui.drawing

[src/faceless_champ/os_ui/drawing.py](../../src/faceless_champ/os_ui/drawing.py)

Local declarations (line numbers are baseline source lines):

```text
L15 font(path, size)
L19 palette(appearance, accent)
L33 class Painter
  L34 __init__(self, image, clip, state, factor)
  L39 box(self, box)
  L44 rect(self, box, fill, radius=8, outline=None, width=1)
  L53 line(self, points, fill, width=2)
  L58 text(self, xy, text, *, size=None, color=None, max_width=None, center=False)
  L75 icon(self, name, x, y, size=48)
L351 display_state(clip, time)
L392 draw_frame(clip, time, factor)
```

### faceless_champ.os_ui.layout

[src/faceless_champ/os_ui/layout.py](../../src/faceless_champ/os_ui/layout.py)

Local declarations (line numbers are baseline source lines):

```text
L7 rect(x, y, w, h)
L11 window_box(state, name)
L15 listing(state)
L22 geometry(state, width, height, mode, pages)
```

### faceless_champ.os_ui.model

[src/faceless_champ/os_ui/model.py](../../src/faceless_champ/os_ui/model.py)

Local declarations (line numbers are baseline source lines):

```text
L11 class File
  field id: str
  field name: str
  field text: str
  field image: str | Path | None
L19 class Folder
  field id: str
  field name: str
  field children: tuple[File | Folder, ...]
L25 class VirtualFileSystem
  L28 __init__(self, root: Folder)
  L58 node(self, id)
  L63 visible(self, id)
  L71 children(self, id)
  L83 rename(self, id, name)
  L92 create_folder(self, parent, id, name)
  L99 move(self, id, parent)
  L111 copy(self, id, parent, new_id, name=None)
  L138 trash(self, id)
  L144 restore(self, id)
L153 class Control
  field id: str
  field label: str
  field kind: str
  field value: object
  field options: tuple[str, ...]
  field minimum: float
  field maximum: float
  L176 validate(self, value)
L196 class SettingsPage
  field id: str
  field title: str
  field controls: tuple[Control, ...]
L209 starter_pages()
L240 class MacOSPreset
  field appearance: str
  field wallpaper: str
  field accent: str
  field font: str | None
  field font_size: int
  field clock: str
  field cursor_color: str
  field cursor_size: float
  field icons: dict[str, str]
```

### faceless_champ.os_ui.script

[src/faceless_champ/os_ui/script.py](../../src/faceless_champ/os_ui/script.py)

Local declarations (line numbers are baseline source lines):

```text
L10 class Action
  field kind: str
  field target: str | None
  field at: float
  field duration: float
  field cursor: bool
  field args: dict
L19 class OSScript
  L20 __init__(self)
  L24 @property actions(self)
  L28 @property duration(self)
  L61 wait(self, duration=1)
  L64 open_folder(self, id, **timing)
  L67 back(self, **timing)
  L70 forward(self, **timing)
  L73 up(self, **timing)
  L76 select(self, id, **timing)
  L79 set_view(self, view, **timing)
  L82 search(self, text, **timing)
  L85 scroll(self, rows=1, *, window='finder', **timing)
  L88 create_folder(self, id, name, **timing)
  L91 rename(self, id, name, **timing)
  L94 copy(self, id, destination, new_id, *, name=None, **timing)
  L97 move(self, id, destination, **timing)
  L100 drag(self, id, destination, **timing)
  L103 trash(self, id, *, confirm=False, **timing)
  L106 restore(self, id, **timing)
  L109 open_trash(self, **timing)
  L112 preview(self, id, **timing)
  L115 open_settings(self, page='appearance', **timing)
  L118 set_value(self, control, value, **timing)
  L121 window(self, id, action, **kwargs)
  L125 move_cursor(self, target=None, *, position=None, **timing)
  L128 click(self, target, *, button='left', count=1, **timing)
  L131 double_click(self, target, **timing)
  L134 right_click(self, target, **timing)
  L137 type_text(self, target, text, **timing)
  L140 confirm(self, accept=True, **timing)
  L143 menu(self, name='File', **timing)
```

### faceless_champ.paths

[src/faceless_champ/paths.py](../../src/faceless_champ/paths.py)

Local declarations (line numbers are baseline source lines):

```text
L11 class PathData
  field commands: tuple
  L43 move_to(self, x, y)
  L46 line_to(self, x, y)
  L49 quad_to(self, cx, cy, x, y)
  L52 cubic_to(self, cx1, cy1, cx2, cy2, x, y)
  L55 close(self)
  L58 transformed(self, sx=1, sy=1, dx=0, dy=0)
  L67 @property bounds(self)
  L115 flatten(self, tolerance=0.25)
L171 class VectorPath(Shape)
  L178 __init__(self, path, *, fill_rule='winding', line_cap='butt', **kwargs)
  L194 @property portable(self)
```

### faceless_champ.playground

[src/faceless_champ/playground/__init__.py](../../src/faceless_champ/playground/__init__.py)

Explicit exports:

```text
CanvasItem -> faceless_champ.playground.model.CanvasItem
CodeCheckpoint -> faceless_champ.playground.model.CodeCheckpoint
CodeEditor -> faceless_champ.playground.playback.CodeEditor
EditTimeline -> faceless_champ.playground.playback.EditTimeline
EventBinding -> faceless_champ.playground.model.EventBinding
PlaygroundCanvas -> faceless_champ.playground.playback.PlaygroundCanvas
PlaygroundError -> faceless_champ.playground.model.PlaygroundError
PlaygroundOutput -> faceless_champ.playground.playback.PlaygroundOutput
PlaygroundScript -> faceless_champ.playground.model.PlaygroundScript
PlaygroundView -> faceless_champ.playground.playback.PlaygroundView
PreparedPlayground -> faceless_champ.playground.prepare.PreparedPlayground
ValueBinding -> faceless_champ.playground.model.ValueBinding
emit -> faceless_champ.playground.runtime.emit
event -> faceless_champ.playground.runtime.event
inputs -> faceless_champ.playground.runtime.inputs
prepare_playground -> faceless_champ.playground.prepare.prepare_playground
```

### faceless_champ.playground.model

[src/faceless_champ/playground/model.py](../../src/faceless_champ/playground/model.py)

Local declarations (line numbers are baseline source lines):

```text
L13 class PlaygroundError(ValueError)
  L14 __init__(self, code, message, **scope)
  L18 as_dict(self)
L22 fail(message, **scope)
L26 json_copy(value)
L33 relative_path(value)
L43 class CodeCheckpoint
  field id: str
  field files: dict[str, str]
  field active_file: str
  field entrypoint: str
  field edit_start: float
  field edit_end: float
  field publish: float
  field runtime: str
  field first_line: int
  field inputs: dict
  field expected_failure: bool
  field ready: tuple[str, ...]
  field web_script: object
  L109 record(self)
L117 valid_canvas_value(kind, value)
L135 class CanvasItem
  field id: str
  field kind: str
  field label: str
  field value: object
  field color: str
L158 class ValueBinding
  field key: str
  field target: str
  field property: str
L165 class EventBinding
  field checkpoint: str
  field event: str
  field target: str
  field at: float
  field duration: float
  field to: str | None
  field cell: tuple[int, int] | None
L183 class PlaygroundScript
  L186 __init__(self, checkpoints, *, duration, mode='concept', items=(), bindings=(), events=(), viewport=(720, 640))
  L254 record(self)
  L258 @classmethod from_record(cls, data)
```

### faceless_champ.playground.playback

[src/faceless_champ/playground/playback.py](../../src/faceless_champ/playground/playback.py)

Local declarations (line numbers are baseline source lines):

```text
L19 class EditTimeline
  L22 __init__(self, script)
  L39 layout_sample_times(self)
  L56 state_at(self, time)
L102 class PlaygroundView(Component)
  L105 __init__(self, *, width, height, source_start=0, **kwargs)
  L110 frame_key(self, age)
L114 class CodeEditor(PlaygroundView)
  L115 __init__(self, script, *, width=800, height=800, font_size=24, theme='midnight', **kwargs)
  L162 frame_image(self, age, factor=1)
L194 class PlaygroundCanvas(PlaygroundView)
  L195 __init__(self, prepared, *, width=800, height=620, font_size=24, minimum_font_size=18, theme=None, **kwargs)
  L217 state_at(self, time)
  L260 frame_image(self, age, factor=1)
L356 class PlaygroundOutput(PlaygroundView)
  L357 __init__(self, prepared, *, width=800, height=160, font_size=18, theme=None, **kwargs)
  L372 frame_image(self, age, factor=1)
```

### faceless_champ.playground.prepare

[src/faceless_champ/playground/prepare.py](../../src/faceless_champ/playground/prepare.py)

Local declarations (line numbers are baseline source lines):

```text
L133 validate_result(script, checkpoint, result)
L191 class PreparedPlayground
  L194 __init__(self, directory)
  L238 @property script(self)
  L242 @property fingerprint(self)
  L246 @property results(self)
L254 prepare_playground(script, *, cache_dir='.playground-cache', timeout=10, output_limit=1000000, fps=15, refresh=False)
```

### faceless_champ.playground.runtime

[src/faceless_champ/playground/runtime.py](../../src/faceless_champ/playground/runtime.py)

Local declarations (line numbers are baseline source lines):

```text
L7 inputs()
L24 emit(key, value)
L31 event(name, payload=None)
```

### faceless_champ.playground.web_worker

[src/faceless_champ/playground/web_worker.py](../../src/faceless_champ/playground/web_worker.py)

Local declarations (line numbers are baseline source lines):

```text
L11 main()
```

### faceless_champ.preview

[src/faceless_champ/preview.py](../../src/faceless_champ/preview.py)

Local declarations (line numbers are baseline source lines):

```text
L22 class StoryboardSample
  field time: float
  field label: str
L66 save_frame(node: Renderable, time: float, output: str | Path, *, size: tuple[int, int] | None=None, renderer: Renderer | None=None, backend: str='pillow', overwrite: bool=False) -> Path
L91 render_storyboard(node: Renderable, samples: Iterable[StoryboardSample | float], directory: str | Path, *, size: tuple[int, int] | None=None, columns: int=3, renderer: Renderer | None=None, backend: str='pillow', overwrite: bool=False) -> Path
```

### faceless_champ.procedural

[src/faceless_champ/procedural.py](../../src/faceless_champ/procedural.py)

Explicit exports:

```text
ParticleField
ProceduralBackground
```

Local declarations (line numbers are baseline source lines):

```text
L8 class ProceduralBackground(Component)
  L11 __init__(self, kind='aurora', *, width=1920, height=1080, seed=0, color='#68BFFF', speed=0.2, **options)
  L22 frame_key(self, age)
L30 class ParticleField(ProceduralBackground)
  L31 __init__(self, *, count=1000, radius=2, lifetime=5, velocity=(0, -40), **options)
  L47 frame_key(self, age)
L51 particle_data(component, age)
```

### faceless_champ.progress

[src/faceless_champ/progress.py](../../src/faceless_champ/progress.py)

Local declarations (line numbers are baseline source lines):

```text
L18 class ExportProgress
  L27 __init__(self, *, stream: TextIO | None=None, interval: float=0.5)
  L39 __enter__(self)
  L42 __call__(self, completed: int, total: int) -> None
  L75 __exit__(self, exc_type, exc, traceback)
```

### faceless_champ.renderer

[src/faceless_champ/renderer.py](../../src/faceless_champ/renderer.py)

Local declarations (line numbers are baseline source lines):

```text
L49 class Renderer(Protocol)
  L50 validate(self, node: Renderable) -> None
  L51 frame(self, node: Renderable, time: float, size: tuple[int, int]) -> PILImage.Image
L54 create_renderer(backend='pillow', *, antialias=2, **options)
L74 rendering_identity(backend='pillow', node=None, *, renderer=None)
L135 validate_composition(node)
L141 managed_renderer(antialias=1)
L161 class PillowRenderer
  L162 __init__(self, antialias: int=2, *, frame_cache_mb: float=64, caption_cache_mb: float=32, code_cache_mb: float=32, arch_session_limit: int=4)
  L196 close(self)
  L218 __enter__(self)
  L221 __exit__(self, *exc)
  L283 validate(self, node: Renderable, *, backend='pillow') -> None
  L373 frame(self, node: Renderable, time: float, size: tuple[int, int]) -> PILImage.Image
```

### faceless_champ.scheduling

[src/faceless_champ/scheduling.py](../../src/faceless_champ/scheduling.py)

Local declarations (line numbers are baseline source lines):

```text
L11 class Schedule
  L12 __init__(self, *children, duration=1, delay=0)
  L19 child_time(self, child)
L23 class Stagger(Schedule)
  L24 __init__(self, *children, lag=0.1, duration=1, delay=0)
  L29 @property run_time(self)
L33 class Succession(Schedule)
  L35 @property run_time(self)
L39 class Repeat(Schedule)
  L40 __init__(self, child, *, cycles, ping_pong=False, duration=1, delay=0)
  L48 @property run_time(self)
L73 play_schedule(scene, animations, run_time, rate_func)
```

### faceless_champ.spring

[src/faceless_champ/spring.py](../../src/faceless_champ/spring.py)

Explicit exports:

```text
Spring
```

Local declarations (line numbers are baseline source lines):

```text
L87 class Spring
  field stiffness: float
  field damping: float
  field mass: float
  L161 __call__(self, u: float) -> float
```

### faceless_champ.subtitles

[src/faceless_champ/subtitles.py](../../src/faceless_champ/subtitles.py)

Local declarations (line numbers are baseline source lines):

```text
L25 class SubtitleCue
  field index: int
  field start: float
  field end: float
  field text: str
L42 class SubtitleTrack
  L45 __init__(self, cues: Iterable[SubtitleCue], *, overlap_tolerance: float=0.0) -> None
  L63 @classmethod from_srt(cls, path: str | Path, *, overlap_tolerance: float=0.0) -> SubtitleTrack
  L67 @classmethod parse_srt(cls, text: str, *, overlap_tolerance: float=0.0) -> SubtitleTrack
  L83 @property duration(self) -> float
  L86 cue(self, index: int) -> SubtitleCue
  L90 active_at(self, time: float) -> SubtitleCue | None
  L96 phrases(self, max_words: int=7, max_duration: float=3) -> tuple[tuple[SubtitleCue, ...], ...]
L117 class Captions(Component)
  L124 __init__(self, track: SubtitleTrack, *, font: str | Path | None=None, font_size: float=42, width: float=1440, color: str='#292724', highlight_color: str='#e56c35', future_color: str='#99938b', max_words: int=7, max_duration: float=3, spacing: float=8, **kwargs: Any) -> None
  L153 phrase_at(self, time: float) -> tuple[SubtitleCue, ...]
```

### faceless_champ.surfaces

[src/faceless_champ/surfaces.py](../../src/faceless_champ/surfaces.py)

Local declarations (line numbers are baseline source lines):

```text
L18 class ShadowStyle
  field color: str
  field blur: float
  field offset: tuple[float, float]
L37 class Surface(Component)
  L44 __init__(self, bounds, *, fill, radius=0, shadow=None, pattern=None, spacing=28, dot_radius=1, **options)
L77 card_content_bounds(bounds, *, shadow=None, padding=28)
L108 card_surface(bounds, *, fill='#FFFFFF', radius=44, shadow=None, render_mode='raster', **component_options)
L160 gradient_surface(bounds, *, fill, **component_options)
L171 dot_grid(bounds, *, color='#B7B3AE55', spacing=28, radius=1, render_mode='raster', **component_options)
```

### faceless_champ.timeline

[src/faceless_champ/timeline.py](../../src/faceless_champ/timeline.py)

Local declarations (line numbers are baseline source lines):

```text
L24 class Renderable
  field canvas: Canvas
  L28 @property duration(self) -> float
  L31 render(self, output: str | Path, **kwargs: Any) -> Path
L38 class Track
  field property: str
  field start: float
  field duration: float
  field initial: object
  field target: object
  field easing: Callable[[float], float]
  field keyframes: tuple[tuple[float, object], ...] | None
  L47 value_at(self, time: float)
L62 class Entry
  field component: Component
  field start: float
  field initial: dict
  field tracks: list[Track]
  field end: float | None
  field parent: Entry | None
  field children: list[Entry]
  L71 ancestors(self)
  L77 state_at(self, time: float) -> dict
L85 class Scene(Renderable)
  L86 __init__(self, canvas: Canvas | None=None) -> None
  L95 construct(self) -> None
  L98 build(self) -> Self
  L115 @property duration(self) -> float
  L128 @property time(self) -> float
  L133 at(self, time: float)
  L147 wait_until(self, time: float) -> Self
  L154 remove(self, *components: Component) -> Self
  L227 add(self, *components: Component) -> Self
  L239 bounds_at(self, component: Component, time: float)
  L268 ink_bounds_at(self, component: Component, time: float)
  L291 play(self, *animations, run_time=None, rate_func=None) -> Self
  L432 wait(self, duration: float=1.0) -> Self
  L436 add_audio(self, path: str | Path, *, start: float | None=None, trim_start: float=0, trim_end: float | None=None, volume: float=1, fade_in: float=0, fade_out: float=0) -> Self
L548 class Sequence(Renderable)
  L549 __init__(self, *children: Renderable, crossfade: float=0.0, canvas: Canvas | None=None, transition=None) -> None
  L564 @property starts(self) -> list[float]
  L579 @property duration(self) -> float
L583 class Grid(Renderable)
  L584 __init__(self, *children: Renderable, rows: int=2, columns: int=3, canvas: Canvas | None=None, gap: float=0, padding: float | tuple[float, float, float, float]=0, start_times: list[float] | tuple[float, ...] | None=None) -> None
  L618 @property duration(self) -> float
L622 class Layer(Renderable)
  L629 __init__(self, *children: Renderable, canvas: Canvas | None=None, effects=None) -> None
  L639 @property duration(self) -> float
```

### faceless_champ.transitions

[src/faceless_champ/transitions.py](../../src/faceless_champ/transitions.py)

Explicit exports:

```text
DirectionalWipe
LuminanceWipe
ZoomBlurTransition
```

Local declarations (line numbers are baseline source lines):

```text
L9 class DirectionalWipe
  field softness: float
L20 class LuminanceWipe(DirectionalWipe)
L25 class ZoomBlurTransition
  field strength: float
L35 transition(value)
```

### faceless_champ.typography

[src/faceless_champ/typography.py](../../src/faceless_champ/typography.py)

Public data declarations: `DEFAULT_FONT`, `CLEAN_FLOW_FONT`.

Local declarations (line numbers are baseline source lines):

```text
L11 fit_text(text, bounds, *, font_size=64, min_font_size=24, font=None, font_weight=None, color='white', align='center', spacing=8, text_engine='pillow')
L76 load_font(path, size, weight=None)
```

### faceless_champ.web

[src/faceless_champ/web/__init__.py](../../src/faceless_champ/web/__init__.py)

Explicit exports:

```text
HtmlClip -> faceless_champ.web.clip.HtmlClip
HtmlPage -> faceless_champ.web.model.HtmlPage
WebAction -> faceless_champ.web.model.WebAction
WebCallout -> faceless_champ.web.clip.WebCallout
WebCapture -> faceless_champ.web.model.WebCapture
WebError -> faceless_champ.web.model.WebError
WebFocus -> faceless_champ.web.clip.WebFocus
WebHighlight -> faceless_champ.web.clip.WebHighlight
WebScript -> faceless_champ.web.model.WebScript
capture_html -> faceless_champ.web.capture.capture_html
```

### faceless_champ.web.capture

[src/faceless_champ/web/capture.py](../../src/faceless_champ/web/capture.py)

Public data declarations: `ANIMATION_DRIVER`.

Local declarations (line numbers are baseline source lines):

```text
L42 local_server(root)
L68 input_digest(page, excluded=())
L84 capture_html(page: HtmlPage, script: WebScript, *, fps=30, cache_dir='.web-cache', start_time=0, end_time=None, sample_times=None, timeout=10, progress=None, allow_errors=False, output_limit=1000000)
```

### faceless_champ.web.clip

[src/faceless_champ/web/clip.py](../../src/faceless_champ/web/clip.py)

Local declarations (line numbers are baseline source lines):

```text
L15 class WebFocus
  field selector: str
  field start: float
  field end: float
  field zoom: float
  field transition: float
L29 class WebHighlight
  field selector: str
  field start: float
  field end: float
  field color: str
L40 class WebCallout
  field text: str
  field start: float
  field end: float
L56 class HtmlClip(Component)
  L63 __init__(self, capture, *, width, height, selector=None, source_start=0, cursor=False, highlights=(), focuses=(), callouts=(), **kwargs)
  L100 frame_key(self, age)
  L103 frame_image(self, age, factor=1)
```

### faceless_champ.web.model

[src/faceless_champ/web/model.py](../../src/faceless_champ/web/model.py)

Local declarations (line numbers are baseline source lines):

```text
L13 class WebError(ValueError)
L18 class HtmlPage
  field path: str | Path
  field viewport: tuple[int, int]
  field asset_root: str | Path | None
  field storage: dict[str, str]
  field ready: tuple[str, ...]
L43 class WebAction
  field kind: str
  field selector: str
  field at: float
  field duration: float
  field value: object
L51 class WebScript
  L54 __init__(self, duration: float)
  L59 track(self, *selectors)
  L84 move(self, selector, *, at, duration=0.4)
  L87 click(self, selector, *, at)
  L90 type(self, selector, text, *, at, duration=1)
  L95 press(self, selector, key, *, at)
  L100 select(self, selector, value, *, at)
  L105 scroll(self, selector, *, at, y, x=0, duration=0.7)
  L108 assert_ready(self, selector, *, at)
  L111 record(self)
L119 class WebCapture
  L122 __init__(self, directory)
  L149 index(self, time)
  L152 metadata(self, time)
  L158 image(self, time)
```

### facelesschamp_agent

[facelesschamp-agent/src/facelesschamp_agent/__init__.py](../../facelesschamp-agent/src/facelesschamp_agent/__init__.py)

Explicit exports:

```text
AgentError -> facelesschamp_agent.errors.AgentError
AgentProject
BeatSelection -> facelesschamp_agent.models.BeatSelection
CapabilityRegistry
DesignSpec -> facelesschamp_agent.models.DesignSpec
QualityReport -> facelesschamp_agent.models.QualityReport
ReviewFinding -> facelesschamp_agent.models.ReviewFinding
ScenePlan -> facelesschamp_agent.models.ScenePlan
SelectionPlan -> facelesschamp_agent.models.SelectionPlan
StoryPlan -> facelesschamp_agent.models.StoryPlan
VideoBrief -> facelesschamp_agent.models.VideoBrief
VideoPlan -> facelesschamp_agent.models.VideoPlan
install_coding_tutorial
load_coding_tutorial
plan_project
read_project_context
select_scenes
```

### facelesschamp_agent.cli

[facelesschamp-agent/src/facelesschamp_agent/cli.py](../../facelesschamp-agent/src/facelesschamp_agent/cli.py)

Local declarations (line numbers are baseline source lines):

```text
L25 class Parser(argparse.ArgumentParser)
  L26 error(self, message)
L30 export_skill(destination)
L39 main(argv=None)
```

### facelesschamp_agent.context

[facelesschamp-agent/src/facelesschamp_agent/context.py](../../facelesschamp-agent/src/facelesschamp_agent/context.py)

Public data declarations: `SCHEMA_VERSION`, `MAX_FILES`, `MAX_ENTRIES`, `MAX_DEPTH`, `MAX_TEXT_FILE_BYTES`, `MAX_TEXT_BYTES`, `MAX_CUES`, `MAX_ASSET_SAMPLE_BYTES`, `MAX_CHARS`.

Local declarations (line numbers are baseline source lines):

```text
L287 read_project_context(root: str | Path='.', *, paths: Iterable[str | Path] | str | Path | None=None, max_chars: int=24000) -> dict[str, Any]
```

### facelesschamp_agent.delivery

[facelesschamp-agent/src/facelesschamp_agent/delivery.py](../../facelesschamp-agent/src/facelesschamp_agent/delivery.py)

Local declarations (line numbers are baseline source lines):

```text
L81 write_render_entrypoint(root, *, overwrite=False)
```

### facelesschamp_agent.errors

[facelesschamp-agent/src/facelesschamp_agent/errors.py](../../facelesschamp-agent/src/facelesschamp_agent/errors.py)

Local declarations (line numbers are baseline source lines):

```text
L6 class AgentError(KitError)
  L7 __init__(self, code, message, *, suggested_fix='Inspect the referenced input and rerun the operation', **scope)
  L12 as_dict(self)
```

### facelesschamp_agent.examples

[facelesschamp-agent/src/facelesschamp_agent/examples.py](../../facelesschamp-agent/src/facelesschamp_agent/examples.py)

Local declarations (line numbers are baseline source lines):

```text
L11 prepare_example(directory)
L35 create_example(destination, kind)
```

### facelesschamp_agent.layout

[facelesschamp-agent/src/facelesschamp_agent/layout.py](../../facelesschamp-agent/src/facelesschamp_agent/layout.py)

Local declarations (line numbers are baseline source lines):

```text
L59 layout_sample_times(compiled, plan)
L138 audit_layout(compiled, plan, *, times=None)
```

### facelesschamp_agent.media

[facelesschamp-agent/src/facelesschamp_agent/media.py](../../facelesschamp-agent/src/facelesschamp_agent/media.py)

Local declarations (line numbers are baseline source lines):

```text
L15 run_tool(command, *, timeout=300)
L32 pcm(path, start, duration, *, rate=2000)
L74 alignment(reference, output, *, source_start, duration)
L122 verify_media(path, *, width, height, fps, duration, require_audio, frame_directory, reference=None, source_start=0, samples=None, alignment_reason=None)
```

### facelesschamp_agent.models

[facelesschamp-agent/src/facelesschamp_agent/models.py](../../facelesschamp-agent/src/facelesschamp_agent/models.py)

Public data declarations: `Text`, `Id`, `Seconds`, `Positive`, `Status`, `SCHEMAS`.

Local declarations (line numbers are baseline source lines):

```text
L14 class Record(BaseModel)
L18 class NarrationInput(Record)
  field audio: Text | None
  field subtitles: Text | None
  field overlap_tolerance: Seconds
  L24 paired(self)
L30 class AssetInput(Record)
  field id: Id
  field path: Text
  field kind: Literal['image', 'audio', 'subtitle', 'font', 'data', 'prepared', 'mesh']
  field required: bool
  field description: Text
  field source: str
L39 class VideoBrief(Record)
  field title: Text
  field prompt: Text
  field audience: Text
  field intended_understanding: Text
  field format: Literal['landscape', 'shorts']
  field duration: Positive
  field delivery: Literal['full', 'preview']
  field constraints: list[Text]
  field narration: NarrationInput
  field assets: list[AssetInput]
  field repair_limit: Annotated[int, Field(ge=0, le=10, strict=True)]
L53 class DesignSpec(Record)
  field text_engine: Literal['pillow', 'skia']
  field surface_mode: Literal['raster', 'vector']
  field template: Literal['coding-tutorial'] | None
  field theme: Literal['midnight', 'light', 'whiteboard', 'clean-flow']
  field rationale: Text
  field font: Text | None
  field palette: dict[str, str]
  field semantic_colors: dict[str, str]
  field body_size: Positive
  field minimum_font_size: Positive
  field heading_size: Positive
  field spacing: Seconds
  field motion_duration: Positive
  field motion: Text
  field captions: bool
  L71 sizes(self)
L83 class StoryBeat(Record)
  field scene_id: Id
  field idea: Text
  field purpose: Text
L89 class StoryPlan(Record)
  field thesis: Text
  field beats: list[StoryBeat]
L94 class KeyEvent(Record)
  field at: Seconds
  field label: Text
  field target: str | None
  field duration: Seconds
L101 class ScenePlan(Record)
  field id: Id
  field purpose: Text
  field start: Seconds
  field duration: Positive
  field treatment: Literal['recipe', 'custom']
  field recipe: str | None
  field content: dict
  field visual_relationships: list[Text]
  field attention_sequence: list[Text]
  field key_events: list[KeyEvent]
  field required_assets: list[Id]
  field narration: str
  field sources: list[Text]
  field illustrative: bool
  field capabilities: list[Text]
  field selection_rationale: str
  field composition: str
  field motion_plan: str
  field transition: str
  field layout_strategy: str
  field intentional_overlaps: list[tuple[Text, Text]]
  field allow_bleed: list[Text]
  L126 valid_recipe_and_events(self)
L143 class VideoPlan(Record)
  field schema_version: Literal[1]
  field video_id: Id
  field brief: VideoBrief
  field story: StoryPlan
  field scenes: list[ScenePlan]
  field design: DesignSpec
  L152 references_and_timing(self)
L169 class ReviewFinding(Record)
  field scene_id: Id
  field source_time: Seconds
  field element: str | None
  field severity: Literal['info', 'warning', 'error']
  field code: Id
  field observed: Text
  field evidence_artifact: Text
  field suggested_repair: Text
L180 class ReviewSubmission(Record)
  field schema_version: Literal[1]
  field fingerprint: Text
  field reviewer: Text
  field kind: Literal['visual', 'editorial']
  field status: Literal['passed', 'failed', 'unverified']
  field evidence_artifacts: list[Text]
  field reviewed_scenes: list[Id]
  field findings: list[ReviewFinding]
  field notes: str
  L192 evidence(self)
L200 class QualityReport(Record)
  field schema_version: Literal[1]
  field fingerprint: str
  field structural_validation: Status
  field layout_validation: Status
  field preview_media_verification: Status
  field full_export_media_verification: Status
  field visual_review: Status
  field editorial_review: Status
  field narration_alignment: Status
  field draft: bool
  field draft_reasons: list[str]
  field findings: list[ReviewFinding]
  field artifacts: list[dict]
  field repair_passes: dict[str, int]
  field next_actions: list[str]
L218 class HumanScores(Record)
  field clarity: Annotated[int, Field(ge=1, le=5, strict=True)]
  field accuracy: Annotated[int, Field(ge=1, le=5, strict=True)]
  field pacing: Annotated[int, Field(ge=1, le=5, strict=True)]
  field visual_quality: Annotated[int, Field(ge=1, le=5, strict=True)]
  field reviewer: Text
  field notes: Text
L227 class BenchmarkResult(Record)
  field schema_version: Literal[1]
  field prompt_id: Id
  field agent: Text
  field model: Text
  field outcome: Literal['complete', 'incomplete', 'failed']
  field completion_seconds: Seconds
  field repair_count: Annotated[int, Field(ge=0, strict=True)]
  field cost_usd: Seconds | None
  field failures: list[Text]
  field artifact_paths: list[Text]
  field quality: QualityReport | None
  field human_scores: HumanScores | None
L242 class BeatSelection(Record)
  field scene_id: Id
  field start: Seconds
  field duration: Positive
  field narration: str
  field cue_ids: list[str]
  field purpose: Text
  field intent: Text
  field evidence: list[Text]
  field candidates: list[dict]
  field selected_capability: Text | None
  field selection_rationale: Text
  field composition: Text
  field motion: Text
  field transition: Text
  field attention_sequence: list[Text]
  field required_inputs: list[Text]
  field layout_checks: list[Text]
  field requires_authoring: Literal[True]
L265 class SelectionPlan(Record)
  field schema_version: Literal[1]
  field context_fingerprint: Text
  field registry_fingerprint: Text
  field request_fingerprint: Text
  field prompt: Text
  field instructions: list[Text]
  field format: Literal['landscape', 'shorts']
  field duration: Positive
  field timing: Literal['source', 'estimated']
  field design: DesignSpec
  field guidelines: dict
  field sources: list[dict]
  field beats: list[BeatSelection]
  field warnings: list[str]
  field editorial_review: Literal['pending']
  L283 coverage(self)
```

### facelesschamp_agent.planning

[facelesschamp-agent/src/facelesschamp_agent/planning.py](../../facelesschamp-agent/src/facelesschamp_agent/planning.py)

Public data declarations: `PLANNING_VERSION`, `PREMIUM_GUIDELINES`.

Local declarations (line numbers are baseline source lines):

```text
L576 select_scenes(root='.', *, prompt, instructions=(), design=None, format=None, duration=None, target_beat_seconds=7.0, candidate_limit=4, context=None, registry=None)
L634 plan_project(root='.', *, paths=None, max_chars=24000, **request)
```

### facelesschamp_agent.project

[facelesschamp-agent/src/facelesschamp_agent/project.py](../../facelesschamp-agent/src/facelesschamp_agent/project.py)

Public data declarations: `EXPORT_QUALITIES`.

Local declarations (line numbers are baseline source lines):

```text
L119 class AgentProject
  L120 __init__(self, root='.')
  L132 @property plan(self)
  L241 new_video(self, context)
  L421 validate(self)
  L456 audit_layout(self, *, detailed=False)
  L471 entrypoint(self)
  L480 prepare(self)
  L492 sample_times(self)
  L509 frame(self, time, output=None)
  L524 storyboard(self, output=None)
  L616 preview(self, output=None, *, start=None, end=None, scene=None, fps=None, quality=None, progress=None)
  L657 render(self, output=None, *, fps=None, quality=None, progress=None)
  L671 verify(self, output=None)
  L725 review(self, submission)
  L783 status(self)
L876 init_project(destination)
```

### facelesschamp_agent.registry

[facelesschamp-agent/src/facelesschamp_agent/registry.py](../../facelesschamp-agent/src/facelesschamp_agent/registry.py)

Public data declarations: `GUIDANCE`, `CHILDREN`.

Local declarations (line numbers are baseline source lines):

```text
L392 class CapabilityRegistry
  L402 __init__(self)
  L649 search(self, query='', *, kind=None, limit=None, compact=False)
  L654 recommend(self, query, *, limit=5, kind=None)
  L663 manifest(self)
  L675 describe(self, name)
  L690 check(self)
```

### facelesschamp_agent.templates

[facelesschamp-agent/src/facelesschamp_agent/templates.py](../../facelesschamp-agent/src/facelesschamp_agent/templates.py)

Public data declarations: `TEMPLATE_ID`, `TEMPLATE_FOLDER`.

Local declarations (line numbers are baseline source lines):

```text
L23 default_coding_template(*, root, prompt, context, instructions, design, project_design, constraints, format)
L72 load_coding_tutorial(root='.')
L81 install_coding_tutorial(root='.')
L102 coding_template_guidance(style)
```

### facelesschamp_kit

[facelesschamp-kit/src/facelesschamp_kit/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/__init__.py)

Explicit exports:

```text
Block -> facelesschamp_kit.blocks.Block
BlockBuild -> facelesschamp_kit.blocks.BlockBuild
BuildContext -> facelesschamp_kit.context.BuildContext
CompiledVideo -> facelesschamp_kit.compiler.CompiledVideo
KitError -> facelesschamp_kit.diagnostics.KitError
Project -> facelesschamp_kit.project.Project
Segment -> facelesschamp_kit.video.Segment
Video -> facelesschamp_kit.video.Video
RecipeEvent -> facelesschamp_kit.recipes.RecipeEvent
RecipeSpec -> facelesschamp_kit.recipes.RecipeSpec
apply_recipe -> facelesschamp_kit.recipes.apply_recipe
recipe_specs -> facelesschamp_kit.recipes.recipe_specs
validate_recipe -> facelesschamp_kit.recipes.validate_recipe
CLEAN_FLOW -> facelesschamp_kit.themes.CLEAN_FLOW
Theme -> facelesschamp_kit.themes.Theme
CodingTutorialStyle -> facelesschamp_kit.tutorials.CodingTutorialStyle
CodingTutorialTemplate -> facelesschamp_kit.tutorials.CodingTutorialTemplate
EffectBlock -> facelesschamp_kit.blocks.effects.EffectBlock
ParticleBackdrop -> facelesschamp_kit.blocks.effects.ParticleBackdrop
ProceduralBackdrop -> facelesschamp_kit.blocks.effects.ProceduralBackdrop
```

### facelesschamp_kit.assets

[facelesschamp-kit/src/facelesschamp_kit/assets.py](../../facelesschamp-kit/src/facelesschamp_kit/assets.py)

Local declarations (line numbers are baseline source lines):

```text
L12 digest(path)
L20 unique_object(pairs)
L29 class AssetRegistry
  L30 __init__(self, root, manifest=None)
  L42 resolve(self, asset_id, kind=None, mode='required')
  L93 image(self, asset_id, mode='required')
  L96 audio(self, asset_id)
  L99 subtitle(self, asset_id)
  L102 font(self, asset_id)
  L105 mesh(self, asset_id)
```

### facelesschamp_kit.blocks

[facelesschamp-kit/src/facelesschamp_kit/blocks/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/__init__.py)

Explicit exports:

```text
Block -> facelesschamp_kit.blocks.base.Block
BlockBuild -> facelesschamp_kit.blocks.base.BlockBuild
ChessBoard -> facelesschamp_kit.blocks.chess.ChessBoard
CodeEditor -> facelesschamp_kit.blocks.coding.CodeEditor
CodingPlayground -> facelesschamp_kit.blocks.coding.CodingPlayground
Comparison
EffectBlock -> facelesschamp_kit.blocks.effects.EffectBlock
FinderWindow -> facelesschamp_kit.blocks.os_ui.FinderWindow
FlowBackdrop -> facelesschamp_kit.blocks.flow_design.FlowBackdrop
FlowCanvas -> facelesschamp_kit.blocks.flow_canvas.FlowCanvas
FlowCard -> facelesschamp_kit.blocks.flow_design.FlowCard
FlowDiagram -> facelesschamp_kit.blocks.flow.FlowDiagram
FlowPopup -> facelesschamp_kit.blocks.flow_design.FlowPopup
Heading
ImageCard
MetricCard
OSWalkthrough -> facelesschamp_kit.blocks.os_ui.OSWalkthrough
ParticleBackdrop -> facelesschamp_kit.blocks.effects.ParticleBackdrop
ProceduralBackdrop -> facelesschamp_kit.blocks.effects.ProceduralBackdrop
SettingsWindow -> facelesschamp_kit.blocks.os_ui.SettingsWindow
StepList
TextPanel
WebElement -> facelesschamp_kit.blocks.web.WebElement
WebWalkthrough -> facelesschamp_kit.blocks.web.WebWalkthrough
WhiteboardArrow -> facelesschamp_kit.blocks.whiteboard.WhiteboardArrow
WhiteboardCircle -> facelesschamp_kit.blocks.whiteboard.WhiteboardCircle
WhiteboardDrawing -> facelesschamp_kit.blocks.whiteboard.WhiteboardDrawing
WhiteboardLine -> facelesschamp_kit.blocks.whiteboard.WhiteboardLine
WhiteboardPath -> facelesschamp_kit.blocks.whiteboard.WhiteboardPath
WhiteboardRectangle -> facelesschamp_kit.blocks.whiteboard.WhiteboardRectangle
ArchCanvas -> facelesschamp_kit.blocks.arch.ArchCanvas
```

Local declarations (line numbers are baseline source lines):

```text
L28 palette(ctx, variant, color)
L34 panel(ctx, box)
L54 panel_face(ctx, box)
L60 class Heading
  field text: str
  field variant: str
  field color: str | None
  L65 compose(self, context, bounds)
L78 class TextPanel
  field text: str
  field title: str
  field variant: str
  field color: str | None
  L84 compose(self, ctx, bounds)
L112 class MetricCard
  field value: float
  field label: str
  field variant: str
  field color: str | None
  L118 compose(self, ctx, bounds)
L147 class ImageCard
  field asset: str
  field label: str
  field mode: str
  L152 compose(self, ctx, bounds)
L183 class Comparison
  field left: str
  field right: str
  L187 compose(self, ctx, bounds)
L194 class StepList
  field steps: tuple[str, ...]
  L202 compose(self, ctx, bounds)
```

### facelesschamp_kit.blocks.arch

[facelesschamp-kit/src/facelesschamp_kit/blocks/arch.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/arch.py)

Local declarations (line numbers are baseline source lines):

```text
L20 class ArchCanvas
  field parts: object
  field script: object
  field style: ArchStyle | None
  field camera: object
  field labels: tuple
  field dimensions: tuple
  field units: str
  field viewport: tuple
  field source_start: float
  L36 compose(self, context, bounds)
```

### facelesschamp_kit.blocks.base

[facelesschamp-kit/src/facelesschamp_kit/blocks/base.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/base.py)

Local declarations (line numbers are baseline source lines):

```text
L11 class BlockBuild
  field root: Component
  field children: dict[str, Component]
  field bounds: Bounds | None
L24 class Block(Protocol)
  L25 compose(self, context, bounds: Bounds) -> BlockBuild
L28 fit_text(text, ctx, box, *, size=None, color=None, align='center', heading=False)
L52 centered(box, height, width=None)
L59 build_group(children)
```

### facelesschamp_kit.blocks.chess

[facelesschamp-kit/src/facelesschamp_kit/blocks/chess.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/chess.py)

Local declarations (line numbers are baseline source lines):

```text
L11 class ChessBoard
  field script: ChessScript
  field theme: ChessTheme | None
  field source_start: float
  field assets: ChessAssets | None
  L17 compose(self, context, bounds)
```

### facelesschamp_kit.blocks.coding

[facelesschamp-kit/src/facelesschamp_kit/blocks/coding.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/coding.py)

Local declarations (line numbers are baseline source lines):

```text
L13 class CodeEditor
  field script: PlaygroundScript
  field font_size: float
  field theme: str | None
  field source_start: float
  L19 compose(self, context, bounds)
L35 class CodingPlayground
  field prepared: PreparedPlayground
  field layout: str
  field code_ratio: float
  field font_size: float
  field theme: str | None
  field output: bool
  field source_start: float
  L44 compose(self, context, bounds: Bounds)
```

### facelesschamp_kit.blocks.effects

[facelesschamp-kit/src/facelesschamp_kit/blocks/effects.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/effects.py)

Local declarations (line numbers are baseline source lines):

```text
L11 class EffectBlock
  field block: object
  field effects: EffectStack
  L15 compose(self, context, bounds)
L21 class ProceduralBackdrop
  field kind: str
  field seed: int | None
  field color: str | None
  field speed: float
  L27 compose(self, context, bounds)
L41 class ParticleBackdrop
  field count: int
  field radius: float
  field seed: int | None
  field color: str | None
  L47 compose(self, context, bounds)
```

### facelesschamp_kit.blocks.flow

[facelesschamp-kit/src/facelesschamp_kit/blocks/flow.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/flow.py)

Local declarations (line numbers are baseline source lines):

```text
L13 class FlowDiagram
  field steps: tuple[str, ...]
  field direction: str
  L24 compose(self, ctx, bounds)
```

### facelesschamp_kit.blocks.flow_canvas

[facelesschamp-kit/src/facelesschamp_kit/blocks/flow_canvas.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/flow_canvas.py)

Local declarations (line numbers are baseline source lines):

```text
L12 class FlowCanvas
  field graph: FlowGraph
  field script: FlowScript | None
  field theme: FlowTheme | None
  field viewport: tuple
  field source_start: float
  field design: FlowDesign | str | None
  L28 compose(self, context, bounds)
```

### facelesschamp_kit.blocks.flow_design

[facelesschamp-kit/src/facelesschamp_kit/blocks/flow_design.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/flow_design.py)

Local declarations (line numbers are baseline source lines):

```text
L35 class FlowCard
  field label: str
  field icon: str
  field size: tuple
  field detail: str | None
  field address: str | None
  field design: FlowDesign | str
  L50 compose(self, context, bounds)
L64 class FlowPopup
  field kind: str
  field value: str
  field design: FlowDesign | str
  L71 compose(self, context, bounds)
L78 class FlowBackdrop
  field design: FlowDesign | str
  L83 compose(self, context, bounds)
```

### facelesschamp_kit.blocks.os_ui

[facelesschamp-kit/src/facelesschamp_kit/blocks/os_ui.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/os_ui.py)

Local declarations (line numbers are baseline source lines):

```text
L11 class OSWalkthrough
  field filesystem: VirtualFileSystem | None
  field script: OSScript | None
  field preset: MacOSPreset | None
  field pages: tuple | None
  field source_start: float
  field cursor: bool
  field mode: str
  field viewport: tuple[int, int]
  L21 compose(self, context, bounds)
L48 class FinderWindow(OSWalkthrough)
  field mode: str
  field viewport: tuple[int, int]
L54 class SettingsWindow(OSWalkthrough)
  field mode: str
  field viewport: tuple[int, int]
```

### facelesschamp_kit.blocks.web

[facelesschamp-kit/src/facelesschamp_kit/blocks/web.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/web.py)

Local declarations (line numbers are baseline source lines):

```text
L12 class WebWalkthrough
  field capture: WebCapture
  field browser_chrome: bool
  field title: str
  field cursor: bool
  field source_start: float
  field highlights: tuple[WebHighlight, ...]
  field focuses: tuple[WebFocus, ...]
  field callouts: tuple[WebCallout, ...]
  L22 compose(self, context, bounds: Bounds)
L65 class WebElement
  field capture: WebCapture
  field selector: str
  field source_start: float
  L70 compose(self, context, bounds: Bounds)
```

### facelesschamp_kit.blocks.whiteboard

[facelesschamp-kit/src/facelesschamp_kit/blocks/whiteboard.py](../../facelesschamp-kit/src/facelesschamp_kit/blocks/whiteboard.py)

Local declarations (line numbers are baseline source lines):

```text
L49 class WhiteboardPath(_Stroke)
  field points: tuple
  field closed: bool
L69 class WhiteboardLine(_Stroke)
  field start: tuple
  field end: tuple
L88 class WhiteboardArrow(WhiteboardLine)
  field tip_size: float
L103 class WhiteboardRectangle(_Stroke)
  field x: float
  field y: float
  field width: float
  field height: float
L129 class WhiteboardCircle(_Stroke)
  field center: tuple
  field radius: float
L150 class WhiteboardDrawing
  field drawings: tuple
  field viewbox: tuple
  L170 compose(self, context, bounds)
```

### facelesschamp_kit.cli

[facelesschamp-kit/src/facelesschamp_kit/cli.py](../../facelesschamp-kit/src/facelesschamp_kit/cli.py)

Public data declarations: `CATALOG`.

Local declarations (line numbers are baseline source lines):

```text
L57 doctor(root='.', *, gpu=False)
L106 main(argv=None)
```

### facelesschamp_kit.compiler

[facelesschamp-kit/src/facelesschamp_kit/compiler.py](../../facelesschamp-kit/src/facelesschamp_kit/compiler.py)

Local declarations (line numbers are baseline source lines):

```text
L30 class CompiledVideo
  field composition: object
  field report: dict
  field context: object
  L37 @property duration(self)
  L40 layout_at(self, time)
L82 descendants(root)
L97 compile_video(video)
```

### facelesschamp_kit.context

[facelesschamp-kit/src/facelesschamp_kit/context.py](../../facelesschamp-kit/src/facelesschamp_kit/context.py)

Local declarations (line numbers are baseline source lines):

```text
L15 class BuildContext
  field root: Path
  field canvas: Canvas
  field theme: Theme
  field seed: int
  field safe_margin: float
  field caption_space: float
  field captions: bool
  field assets: AssetRegistry | None
  field preparing: bool
  field refresh_prepared: bool
  field prepared_assets: list
  L40 @property bounds(self)
  L47 load_json(self, path)
  L50 load_csv(self, path)
  L54 playground(self, script, *, timeout=10, output_limit=1000000, fps=15)
```

### facelesschamp_kit.dependencies

[facelesschamp-kit/src/facelesschamp_kit/dependencies.py](../../facelesschamp-kit/src/facelesschamp_kit/dependencies.py)

Local declarations (line numbers are baseline source lines):

```text
L12 dependencies(root)
L57 check_dependencies(root)
```

### facelesschamp_kit.diagnostics

[facelesschamp-kit/src/facelesschamp_kit/diagnostics.py](../../facelesschamp-kit/src/facelesschamp_kit/diagnostics.py)

Local declarations (line numbers are baseline source lines):

```text
L6 class KitError(ValueError)
  L7 __init__(self, code, message, **scope)
  L11 as_dict(self)
L15 number(value, name, minimum=0, positive=False)
L27 fields(value, allowed, scope)
```

### facelesschamp_kit.layouts

[facelesschamp-kit/src/facelesschamp_kit/layouts.py](../../facelesschamp-kit/src/facelesschamp_kit/layouts.py)

Local declarations (line numbers are baseline source lines):

```text
L12 class Stack
  field blocks: tuple
  field gap: float
  L16 __init__(self, *blocks, gap=28)
  L22 compose(self, ctx, bounds)
L46 class Split(Stack)
  L47 compose(self, ctx, bounds)
```

### facelesschamp_kit.project

[facelesschamp-kit/src/facelesschamp_kit/project.py](../../facelesschamp-kit/src/facelesschamp_kit/project.py)

Local declarations (line numbers are baseline source lines):

```text
L45 package_version(name)
L56 project_imports(root)
L101 class Project
  L102 __init__(self, root='.')
  L136 dependencies(self)
  L142 build(self, video_id='main', *, strict_assets=False, _preparing=False, _refresh=False)
  L254 prepare(self, video_id='main', *, refresh=False)
  L258 settings(self, compiled, profile)
  L283 validate(self, video_id='main', *, strict_assets=False)
  L295 frame(self, video_id, time, output, *, overwrite=False)
  L310 storyboard(self, video_id, output, *, overwrite=False)
  L324 export(self, video_id, output, *, preview=False, profile=None, segment=None, start=None, end=None, overwrite=False, allow_placeholders=False)
L391 tool_versions()
```

### facelesschamp_kit.recipes

[facelesschamp-kit/src/facelesschamp_kit/recipes.py](../../facelesschamp-kit/src/facelesschamp_kit/recipes.py)

Explicit exports:

```text
RecipeEvent
RecipeSpec
apply_recipe
recipe_specs
validate_recipe
```

Public data declarations: `RECIPES`.

Local declarations (line numbers are baseline source lines):

```text
L28 class RecipeSpec
  field id: str
  field purpose: str
  field fields: tuple[str, ...]
  field targets: tuple[str, ...]
  field example: dict
  field avoid: str
L149 recipe_specs()
L159 validate_recipe(recipe_id, content)
L242 class RecipeEvent
  field target: str
  field at: float
  field duration: float
  field action: str
  field value: float | None
L457 apply_recipe(segment, recipe_id, content, *, bounds=None, events=(), id=None)
```

### facelesschamp_kit.sample_assets.archchamp

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/archchamp.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/archchamp.py)

Local declarations (line numbers are baseline source lines):

```text
L5 build(ctx)
```

### facelesschamp_kit.sample_assets.coding_backend

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_backend.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_backend.py)

Public data declarations: `SOURCE`.

Local declarations (line numbers are baseline source lines):

```text
L23 script()
L54 build(ctx)
```

### facelesschamp_kit.sample_assets.coding_concept

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_concept.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_concept.py)

Public data declarations: `SOURCE`.

Local declarations (line numbers are baseline source lines):

```text
L27 script()
L44 build(ctx)
```

### facelesschamp_kit.sample_assets.coding_web

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_web.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/coding_web.py)

Public data declarations: `HTML`, `CSS`, `JS`.

Local declarations (line numbers are baseline source lines):

```text
L44 script()
L83 build(ctx)
```

### facelesschamp_kit.sample_assets.flowchamp

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/flowchamp.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/flowchamp.py)

Local declarations (line numbers are baseline source lines):

```text
L9 build(ctx)
```

### facelesschamp_kit.sample_assets.os_ui

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/os_ui.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/os_ui.py)

Local declarations (line numbers are baseline source lines):

```text
L9 tutorial()
L78 build(ctx)
```

### facelesschamp_kit.sample_assets.whiteboard

[facelesschamp-kit/src/facelesschamp_kit/sample_assets/whiteboard.py](../../facelesschamp-kit/src/facelesschamp_kit/sample_assets/whiteboard.py)

Local declarations (line numbers are baseline source lines):

```text
L14 build(ctx)
```

### facelesschamp_kit.scaffold

[facelesschamp-kit/src/facelesschamp_kit/scaffold.py](../../facelesschamp-kit/src/facelesschamp_kit/scaffold.py)

Public data declarations: `CONFIG`, `SILENT`, `NARRATED`.

Local declarations (line numbers are baseline source lines):

```text
L75 init_project(destination, template='silent')
```

### facelesschamp_kit.templates

[facelesschamp-kit/src/facelesschamp_kit/templates.py](../../facelesschamp-kit/src/facelesschamp_kit/templates.py)

Local declarations (line numbers are baseline source lines):

```text
L15 class WhiteboardScene
  field name: str
  field drawing: WhiteboardDrawing
  field label: str | None
  field duration: float | None
  field start: float | None
  field cues: tuple[str, str | None] | None
L73 whiteboard_basic(ctx, *, scenes, audio=None, subtitles=None, markers=None, captions=None, theme=None, draw_fraction=0.7)
L148 silent(ctx, *, value=42, label='Reusable components')
L159 narrated(ctx, *, audio='voiceover', subtitles='word_cues', markers=None)
L183 chesschamp(ctx, data='data.json')
L204 coding_playground(ctx, script, *, start=0, audio=None, subtitles=None, markers=None, cues=None, layout='side', code_ratio=0.5, font_size=24, output=True, fps=15, timeout=10, output_limit=1000000)
```

### facelesschamp_kit.themes

[facelesschamp-kit/src/facelesschamp_kit/themes.py](../../facelesschamp-kit/src/facelesschamp_kit/themes.py)

Public data declarations: `MIDNIGHT`, `LIGHT`, `WHITEBOARD`, `CLEAN_FLOW`, `THEMES`.

Local declarations (line numbers are baseline source lines):

```text
L13 class Theme
  field name: str
  field background: str
  field surface: str
  field foreground: str
  field muted: str
  field accent: str
  field font: str | None
  field heading_size: float
  field body_size: float
  field minimum_font_size: float
  field spacing: float
  field radius: float
  field motion_duration: float
  field font_weight: float | None
  field heading_weight: float | None
  field shadow: ShadowStyle | None
  field background_pattern: str | None
  field grid_color: str
  field grid_spacing: float
  field grid_radius: float
  field default_enter: str | None
  field default_exit: str | None
  field motion_distance: float
  field motion_stagger: float
  field text_engine: str
  field surface_mode: str
  field code_theme: str
```

### facelesschamp_kit.tutorials

[facelesschamp-kit/src/facelesschamp_kit/tutorials/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/__init__.py)

Explicit exports:

```text
CodingTutorialStyle -> facelesschamp_kit.tutorials.coding.CodingTutorialStyle
CodingTutorialTemplate -> facelesschamp_kit.tutorials.coding.CodingTutorialTemplate
```

### facelesschamp_kit.tutorials.coding

[facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/__init__.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/__init__.py)

Explicit exports:

```text
CodingTutorialStyle -> facelesschamp_kit.tutorials.coding.style.CodingTutorialStyle
CodingTutorialTemplate -> facelesschamp_kit.tutorials.coding.components.CodingTutorialTemplate
```

### facelesschamp_kit.tutorials.coding.components

[facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/components.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/components.py)

Local declarations (line numbers are baseline source lines):

```text
L43 class CodingTutorialTemplate
  L46 __init__(self, style=None)
  L54 canvas(self)
  L57 group(self, *components, bounds)
  L72 finder(self, filename, source='', *, folder='Code')
  L88 editor(self, source, *, filename='main.py', language='python')
  L115 terminal(self, text, *, title='Terminal')
  L136 flow(self, script=None)
  L171 emblem(self)
```

### facelesschamp_kit.tutorials.coding.style

[facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/style.py](../../facelesschamp-kit/src/facelesschamp_kit/tutorials/coding/style.py)

Local declarations (line numbers are baseline source lines):

```text
L16 class CodingTutorialStyle
  field background: str
  field accent: str
  field python_blue: str
  field python_yellow: str
  field editor_background: str
  field editor_chrome: str
  field foreground: str
  field muted: str
  field connector: str
  field inset_x: float
  field inset_y: float
  field editor_scale: float
  field code_size: float
  field terminal_size: float
  field shrink_duration: float
  field restore_duration: float
  field terminal_entrance_duration: float
  field terminal_exit_duration: float
  field spring_stiffness: float
  field window_damping: float
  field icon_damping: float
  field surface_mode: str
  field text_engine: str
  L70 @classmethod load(cls, path=None)
  L80 to_dict(self)
  L84 @property palette(self)
  L93 workspace(self)
```

### facelesschamp_kit.video

[facelesschamp-kit/src/facelesschamp_kit/video.py](../../facelesschamp-kit/src/facelesschamp_kit/video.py)

Local declarations (line numbers are baseline source lines):

```text
L15 class Handle
  field placement: str
  field child: str | None
L26 class Window
  field start: float
  field end: float
  field cues: tuple
L33 class Placement
  field handle: Handle
  field block: object
  field bounds: object
  field enter: str | None
  field enter_duration: float
  field z_index: float
  field core: bool
  field at: float
  field duration: float | None
  field exit: str | None
  field exit_duration: float | None
L48 class Segment
  field name: str
  field start: float
  field duration: float
  field cues: tuple
  field placements: list
  field motions: list
  L58 @property end(self)
  L61 __enter__(self)
  L64 __exit__(self, *exc)
  L67 cue_time(self, index, *, edge='start', offset=0)
  L86 add(self, block, *, id=None, bounds=None, anchor='center', enter='theme', enter_duration=None, exit='theme', exit_duration=None, z_index=0, at=0, duration=None)
  L147 add_core(self, factory, **kwargs)
  L154 play(self, target, animation, *, at=0, duration=1)
L171 class Narration
  L172 __init__(self, audio, subtitles, markers, overlap_tolerance=0)
  L192 between(self, first, next=None)
L205 class Video
  L206 __init__(self, context)
  L212 segment(self, name, *, start=None, duration=None, window=None)
  L228 narration(self, *, audio, subtitles=None, markers=None, captions=None, overlap_tolerance=0)
  L245 compile(self)
```

## Ancillary Python coverage ledger

All remaining tracked Python files are listed here. Test counts are defined
functions, not expanded parameter cases. Project-local helpers are outside
the package suite/release guarantee. A source parse is not a full render,
browser run, cloud execution, or visual approval.

| Source | Purpose / ownership | Defined tests |
| --- | --- | ---: |
| [examples/engineering.py](../../examples/engineering.py) | Native engineering showcase. Install faceless-champ[cad] and run --help. | 0 |
| [examples/moderngl_showcase.py](../../examples/moderngl_showcase.py) | A bounded cinematic GPU reference. Use --backend auto for faithful CPU fallback. | 0 |
| [examples/programming/hello_world/render.py](../../examples/programming/hello_world/render.py) | Check by default. Every media export requires an explicit mode. | 0 |
| [examples/programming/hello_world/scene.py](../../examples/programming/hello_world/scene.py) | Complete, source-clock Python lesson in the approved coding tutorial design. | 0 |
| [examples/skia_showcase.py](../../examples/skia_showcase.py) | Premium native-vector reference; four-second preview by default. | 0 |
| [facelesschamp-agent/scripts/release_evidence.py](../../facelesschamp-agent/scripts/release_evidence.py) | Render reproducible recipe evidence and complete examples; review is external. | 0 |
| [facelesschamp-agent/tests/conftest.py](../../facelesschamp-agent/tests/conftest.py) | test fixture / test module | 0 |
| [facelesschamp-agent/tests/test_arch.py](../../facelesschamp-agent/tests/test_arch.py) | test fixture / test module | 2 |
| [facelesschamp-agent/tests/test_audit_contracts.py](../../facelesschamp-agent/tests/test_audit_contracts.py) | Design, durable evidence, and packaged schema contracts. | 4 |
| [facelesschamp-agent/tests/test_coding_template.py](../../facelesschamp-agent/tests/test_coding_template.py) | Default-only template selection, editable ownership, and export controls. | 10 |
| [facelesschamp-agent/tests/test_context.py](../../facelesschamp-agent/tests/test_context.py) | test fixture / test module | 12 |
| [facelesschamp-agent/tests/test_contracts.py](../../facelesschamp-agent/tests/test_contracts.py) | test fixture / test module | 19 |
| [facelesschamp-agent/tests/test_discovery.py](../../facelesschamp-agent/tests/test_discovery.py) | test fixture / test module | 13 |
| [facelesschamp-agent/tests/test_gpu_backend.py](../../facelesschamp-agent/tests/test_gpu_backend.py) | test fixture / test module | 3 |
| [facelesschamp-agent/tests/test_layout_audit.py](../../facelesschamp-agent/tests/test_layout_audit.py) | test fixture / test module | 19 |
| [facelesschamp-agent/tests/test_media.py](../../facelesschamp-agent/tests/test_media.py) | test fixture / test module | 6 |
| [facelesschamp-agent/tests/test_planning.py](../../facelesschamp-agent/tests/test_planning.py) | test fixture / test module | 24 |
| [facelesschamp-agent/tests/test_prepared_recipe.py](../../facelesschamp-agent/tests/test_prepared_recipe.py) | test fixture / test module | 1 |
| [facelesschamp-agent/tests/test_skia_backend.py](../../facelesschamp-agent/tests/test_skia_backend.py) | test fixture / test module | 2 |
| [facelesschamp-agent/tests/test_workflow.py](../../facelesschamp-agent/tests/test_workflow.py) | test fixture / test module | 5 |
| [facelesschamp-kit/scripts/build_dist.py](../../facelesschamp-kit/scripts/build_dist.py) | Build local wheel and sdist using the active interpreter's setuptools. | 0 |
| [facelesschamp-kit/scripts/catalog.py](../../facelesschamp-kit/scripts/catalog.py) | Generate reproducible thumbnails and short motion previews for all six blocks. | 0 |
| [facelesschamp-kit/scripts/prepare_sample.py](../../facelesschamp-kit/scripts/prepare_sample.py) | Developer-only fixture preparation; espeak-ng is not a kit runtime dependency. | 0 |
| [facelesschamp-kit/scripts/verify_media.py](../../facelesschamp-kit/scripts/verify_media.py) | Full short-video QA from installed packages, including a late source-clock excerpt. | 0 |
| [facelesschamp-kit/scripts/verify_whiteboard.py](../../facelesschamp-kit/scripts/verify_whiteboard.py) | Exercise whiteboard CLI/media from an installed package, without source imports. | 0 |
| [facelesschamp-kit/tests/conftest.py](../../facelesschamp-kit/tests/conftest.py) | test fixture / test module | 0 |
| [facelesschamp-kit/tests/test_arch.py](../../facelesschamp-kit/tests/test_arch.py) | test fixture / test module | 12 |
| [facelesschamp-kit/tests/test_chess.py](../../facelesschamp-kit/tests/test_chess.py) | Data-driven chess scaffolding, composition, diagnostics and narration. | 8 |
| [facelesschamp-kit/tests/test_clean_flow.py](../../facelesschamp-kit/tests/test_clean_flow.py) | test fixture / test module | 10 |
| [facelesschamp-kit/tests/test_coding_playground.py](../../facelesschamp-kit/tests/test_coding_playground.py) | test fixture / test module | 3 |
| [facelesschamp-kit/tests/test_coding_tutorial_template.py](../../facelesschamp-kit/tests/test_coding_tutorial_template.py) | Approved geometry and hackable style data, without rendering tutorial media. | 5 |
| [facelesschamp-kit/tests/test_contracts.py](../../facelesschamp-kit/tests/test_contracts.py) | test fixture / test module | 38 |
| [facelesschamp-kit/tests/test_cue_blocks.py](../../facelesschamp-kit/tests/test_cue_blocks.py) | test fixture / test module | 10 |
| [facelesschamp-kit/tests/test_flow_canvas.py](../../facelesschamp-kit/tests/test_flow_canvas.py) | test fixture / test module | 7 |
| [facelesschamp-kit/tests/test_flow_design.py](../../facelesschamp-kit/tests/test_flow_design.py) | Public layout and timeline contracts for the promoted networking design. | 11 |
| [facelesschamp-kit/tests/test_gpu_backend.py](../../facelesschamp-kit/tests/test_gpu_backend.py) | test fixture / test module | 2 |
| [facelesschamp-kit/tests/test_layout_metadata.py](../../facelesschamp-kit/tests/test_layout_metadata.py) | test fixture / test module | 1 |
| [facelesschamp-kit/tests/test_os_ui_blocks.py](../../facelesschamp-kit/tests/test_os_ui_blocks.py) | test fixture / test module | 5 |
| [facelesschamp-kit/tests/test_recipe_motion_bounds.py](../../facelesschamp-kit/tests/test_recipe_motion_bounds.py) | test fixture / test module | 3 |
| [facelesschamp-kit/tests/test_recipes.py](../../facelesschamp-kit/tests/test_recipes.py) | test fixture / test module | 7 |
| [facelesschamp-kit/tests/test_skia_backend.py](../../facelesschamp-kit/tests/test_skia_backend.py) | test fixture / test module | 3 |
| [facelesschamp-kit/tests/test_web_blocks.py](../../facelesschamp-kit/tests/test_web_blocks.py) | test fixture / test module | 1 |
| [facelesschamp-kit/tests/test_whiteboard.py](../../facelesschamp-kit/tests/test_whiteboard.py) | Behavioral checks for drawing visibility, geometry, timing, and the public starter. | 18 |
| [my-project/build123d-jet-engine/render.py](../../my-project/build123d-jet-engine/render.py) | Ten-second native build123d → ArchChamp exploded turbofan assembly. | 0 |
| [my-project/moderngl-fluid/render.py](../../my-project/moderngl-fluid/render.py) | Fifteen seconds of advected smoke, velocity tracers and vortex pressure contours. | 0 |
| [my-project/moderngl-holographic/render.py](../../my-project/moderngl-holographic/render.py) | Holographic turbine CAD study; fifteen seconds, black, silent, graphics only. | 0 |
| [my-project/moderngl-raymarch/render.py](../../my-project/moderngl-raymarch/render.py) | Ray-marched SDF morphs; fifteen seconds, black, silent, graphics only. | 0 |
| [my-project/moderngl-surfaces/render.py](../../my-project/moderngl-surfaces/render.py) | GPU-deformed mathematical surfaces; fifteen seconds, black, silent, no text. | 0 |
| [my-project/moderngl-transitions/render.py](../../my-project/moderngl-transitions/render.py) | Cinematic equation-to-wave shader transition; fifteen seconds, black, silent. | 0 |
| [my-project/pyvista-fusion/render.py](../../my-project/pyvista-fusion/render.py) | Twenty-second, graphics-only toroidal fusion plasma; native PyVista + Faceless Champ. | 0 |
| [my-project/skia-algorithms/render.py](../../my-project/skia-algorithms/render.py) | 60 seconds of algorithm graphics, using Faceless Champ and native Skia CPU. | 0 |
| [my-project/skia-black-hole/render.py](../../my-project/skia-black-hole/render.py) | Sixty seconds of native Skia black-hole graphics on a black canvas. | 0 |
| [my-project/skia-blueprint/render.py](../../my-project/skia-blueprint/render.py) | A 60-second native Skia / PyVista engineering drawing study. | 0 |
| [my-project/skia-code-terminal/render.py](../../my-project/skia-code-terminal/render.py) | Sixty-second native Skia editor: type, run, diagnose, edit, and run again. | 0 |
| [my-project/skia-gradients/render.py](../../my-project/skia-gradients/render.py) | A sixty-second, graphics-only native Skia study of silk, liquid and light. | 0 |
| [my-project/skia-hud/render.py](../../my-project/skia-hud/render.py) | 45 seconds of native Skia HUD graphics; run with the checkout's .venv Python. | 0 |
| [my-project/skia-infographics/render.py](../../my-project/skia-infographics/render.py) | Sixty seconds of native Skia infographics on pure black. Synthetic data. | 0 |
| [my-project/skia-kinetic/render.py](../../my-project/skia-kinetic/render.py) | 45-second native Skia typography film. No Docker, external assets or audio. | 0 |
| [my-project/skia-math/render.py](../../my-project/skia-math/render.py) | 45-second, text-free mathematical motion study using native Skia CPU vectors. | 0 |
| [my-project/skia-neural-network/render.py](../../my-project/skia-neural-network/render.py) | One minute of neural geometry, rendered with native Python and Skia. | 0 |
| [my-project/skia-particles/render.py](../../my-project/skia-particles/render.py) | One minute of luminous generative geometry, rendered with native Python/Skia. | 0 |
| [my-project/skia-physics/render.py](../../my-project/skia-physics/render.py) | One minute of physics diagrams, authored with public Faceless Champ / Skia APIs. | 0 |
| [my-project/skia-premium-ui/render.py](../../my-project/skia-premium-ui/render.py) | A silent, text-free, sixty-second native Skia UI motion study. | 0 |
| [my-project/tesla-roadstar-explained/.agents/skills/colab-video-render/scripts/colab_safe.py](../../my-project/tesla-roadstar-explained/.agents/skills/colab-video-render/scripts/colab_safe.py) | Run short Colab CLI commands with private project state and a real deadline. | 0 |
| [my-project/tesla-roadstar-explained/main.py](../../my-project/tesla-roadstar-explained/main.py) | Importable project entrypoint; render.py is v1, render_v2.py is v2. | 0 |
| [my-project/tesla-roadstar-explained/render.py](../../my-project/tesla-roadstar-explained/render.py) | V1 Roadster renderer with crisp typography and vector plots. Run --help for export controls. | 0 |
| [my-project/tesla-roadstar-explained/render_v2.py](../../my-project/tesla-roadstar-explained/render_v2.py) | Render the independent Roadster v2 film or a short source-clock excerpt. | 0 |
| [my-project/tesla-roadstar-explained/scene/__init__.py](../../my-project/tesla-roadstar-explained/scene/__init__.py) | Project-local Roadster engineering film; source media stays untouched. | 0 |
| [my-project/tesla-roadstar-explained/scene/drawing.py](../../my-project/tesla-roadstar-explained/scene/drawing.py) | Resolution-independent scientific composition with core MathText typesetting. | 0 |
| [my-project/tesla-roadstar-explained/scene/equations.py](../../my-project/tesla-roadstar-explained/scene/equations.py) | Progressive lines keyed to source cues, with stable chapter accumulation. | 0 |
| [my-project/tesla-roadstar-explained/scene/model.py](../../my-project/tesla-roadstar-explained/scene/model.py) | Shared refined teaching geometry and public ArchChamp viewport scenes. | 0 |
| [my-project/tesla-roadstar-explained/scene/physics.py](../../my-project/tesla-roadstar-explained/scene/physics.py) | Analytical, constant-mass teaching models in SI units. | 0 |
| [my-project/tesla-roadstar-explained/scene/qa.py](../../my-project/tesla-roadstar-explained/scene/qa.py) | Source-clock, physical, layout and encoded-media evidence for this project. | 0 |
| [my-project/tesla-roadstar-explained/scene/story.py](../../my-project/tesla-roadstar-explained/scene/story.py) | Forty-shot deterministic film renderer using public core rendering interfaces. | 0 |
| [my-project/tesla-roadstar-explained/scene/timing.py](../../my-project/tesla-roadstar-explained/scene/timing.py) | Forty production shots anchored to unchanged one-based word cue indices. | 0 |
| [my-project/tesla-roadstar-explained/scene/v1_drawing.py](../../my-project/tesla-roadstar-explained/scene/v1_drawing.py) | Crisp v1 typography and analytical plots; all coordinates retain source data. | 0 |
| [my-project/tesla-roadstar-explained/scene/v2.py](../../my-project/tesla-roadstar-explained/scene/v2.py) | Premium v2 treatment; shares source clocks and physics with the original film. | 0 |
| [my-project/tesla-roadstar-explained/scene/v2_drawing.py](../../my-project/tesla-roadstar-explained/scene/v2_drawing.py) | V2 motion typography and scientific graphics, rendered without external TeX. | 0 |
| [my-project/tesla-roadstar-explained/tests/conftest.py](../../my-project/tesla-roadstar-explained/tests/conftest.py) | test fixture / test module | 0 |
| [my-project/tesla-roadstar-explained/tests/test_colab_render.py](../../my-project/tesla-roadstar-explained/tests/test_colab_render.py) | Offline Colab contract tests. Never allocate a VM, install remotely or render. | 36 |
| [my-project/tesla-roadstar-explained/tests/test_roadster.py](../../my-project/tesla-roadstar-explained/tests/test_roadster.py) | Regression coverage for narrated engineering behavior, not drawing internals. | 16 |
| [project-map/build.py](../../project-map/build.py) | Refresh the offline project atlas from this checkout. Standard library only. | 0 |
| [scripts/benchmark_flowchamp.py](../../scripts/benchmark_flowchamp.py) | Repeatable FlowChamp raster benchmark; run with the selected installed/source package. | 0 |
| [scripts/benchmark_geometry.py](../../scripts/benchmark_geometry.py) | Process-isolated geometry benchmarks against the identical prepared mesh scene. | 0 |
| [scripts/benchmark_renderers.py](../../scripts/benchmark_renderers.py) | Bounded, process-isolated renderer benchmarks; encoding is measured separately. | 0 |
| [scripts/prepare_maps.py](../../scripts/prepare_maps.py) | Prepare offline assets from two local downloads; see docs/maps.md. | 0 |
| [scripts/probe_geometry.py](../../scripts/probe_geometry.py) | Explicit native CAD/mesh and headless renderer feasibility probe. | 0 |
| [tests/conftest.py](../../tests/conftest.py) | test fixture / test module | 0 |
| [tests/test_animations.py](../../tests/test_animations.py) | test fixture / test module | 11 |
| [tests/test_arch.py](../../tests/test_arch.py) | Geometry contracts, random-access compositing and owned-session lifecycle. | 18 |
| [tests/test_arch_geometry.py](../../tests/test_arch_geometry.py) | Optional CAD/mesh preparation contracts and exact mechanical source clocks. | 20 |
| [tests/test_chart_typography.py](../../tests/test_chart_typography.py) | Reusable styling and typography behavior introduced by the company-growth scene. | 6 |
| [tests/test_charts.py](../../tests/test_charts.py) | Numeric chart contracts and deterministic rendering through the public timeline. | 12 |
| [tests/test_chess.py](../../tests/test_chess.py) | Chess rules, source-clock playback, JSON diagnostics, and renderer contracts. | 23 |
| [tests/test_coding.py](../../tests/test_coding.py) | Behavioral contracts for reusable code editors (no FFmpeg dependency). | 13 |
| [tests/test_coding_workspace.py](../../tests/test_coding_workspace.py) | Saved workspace design contracts, independent of media rendering. | 12 |
| [tests/test_colors_math.py](../../tests/test_colors_math.py) | Color roles, glyph layout, font weight isolation, and smooth curve caps. | 11 |
| [tests/test_composition_holds.py](../../tests/test_composition_holds.py) | A shorter composition child holds its last visible, end-exclusive frame. | 3 |
| [tests/test_distribution_inputs.py](../../tests/test_distribution_inputs.py) | Required demonstration inputs must survive a clean source distribution. | 2 |
| [tests/test_engine.py](../../tests/test_engine.py) | test fixture / test module | 12 |
| [tests/test_engineering_example.py](../../tests/test_engineering_example.py) | Exercise export dimensions without requiring optional CAD construction. | 2 |
| [tests/test_equations_and_layout.py](../../tests/test_equations_and_layout.py) | Rendering, timing, and audio contracts exercised by equation-render. | 9 |
| [tests/test_export.py](../../tests/test_export.py) | test fixture / test module | 11 |
| [tests/test_export_progress.py](../../tests/test_export_progress.py) | Export feedback uses observed work and never claims premature success. | 4 |
| [tests/test_flags.py](../../tests/test_flags.py) | test fixture / test module | 6 |
| [tests/test_flow.py](../../tests/test_flow.py) | Geometry, authoring and random-access playback contracts for FlowChamp. | 29 |
| [tests/test_flow_capsule.py](../../tests/test_flow_capsule.py) | Native styled packets follow the live routed geometry without sampled overlays. | 5 |
| [tests/test_flow_design.py](../../tests/test_flow_design.py) | Public approved-design behavior and graph/card motion stay in core. | 19 |
| [tests/test_gradient_motion_regressions.py](../../tests/test_gradient_motion_regressions.py) | Independent fixtures for animated gradient lifetime and alpha-edge regressions. | 2 |
| [tests/test_gradient_surfaces.py](../../tests/test_gradient_surfaces.py) | Surface integration: legacy pixels, alpha, transforms, clocks and resource ownership. | 14 |
| [tests/test_gradients.py](../../tests/test_gradients.py) | Independent numeric, validation and raster checks for immutable gradient paints. | 15 |
| [tests/test_groups_layout.py](../../tests/test_groups_layout.py) | test fixture / test module | 16 |
| [tests/test_hello_world.py](../../tests/test_hello_world.py) | The premium opening can be checked without rendering scene frames. | 3 |
| [tests/test_image_slots.py](../../tests/test_image_slots.py) | test fixture / test module | 2 |
| [tests/test_image_sources.py](../../tests/test_image_sources.py) | test fixture / test module | 5 |
| [tests/test_maps.py](../../tests/test_maps.py) | test fixture / test module | 9 |
| [tests/test_moderngl.py](../../tests/test_moderngl.py) | Real EGL contract checks, with explicit skips on hosts without optional GL. | 21 |
| [tests/test_motion_graphics.py](../../tests/test_motion_graphics.py) | test fixture / test module | 24 |
| [tests/test_narration_previews.py](../../tests/test_narration_previews.py) | test fixture / test module | 5 |
| [tests/test_os_ui.py](../../tests/test_os_ui.py) | test fixture / test module | 14 |
| [tests/test_playground.py](../../tests/test_playground.py) | Behavioral contracts for execution, source fidelity, and random-access playback. | 19 |
| [tests/test_preview_publication.py](../../tests/test_preview_publication.py) | PNG publication preserves another writer's output and cleans failed encodes. | 2 |
| [tests/test_procedural.py](../../tests/test_procedural.py) | Particle ink includes the overhang while layout retains the field size. | 2 |
| [tests/test_ranked_charts_and_numbers.py](../../tests/test_ranked_charts_and_numbers.py) | Regression coverage for ranking motion, missing observations and live numbers. | 8 |
| [tests/test_renderer_cache_regressions.py](../../tests/test_renderer_cache_regressions.py) | Rendering regressions across lifetime, text and retained-sprite changes. | 4 |
| [tests/test_skia.py](../../tests/test_skia.py) | Backend contracts and the portable/native vector boundary. | 16 |
| [tests/test_spring.py](../../tests/test_spring.py) | Independent analytical identities and numerical limits for the pure kernel. | 22 |
| [tests/test_spring_release.py](../../tests/test_spring_release.py) | Spring sampling regressions, independent of the public example collection. | 1 |
| [tests/test_spring_scheduling.py](../../tests/test_spring_scheduling.py) | Spring composition through existing finite schedules and publication trials. | 23 |
| [tests/test_spring_timeline.py](../../tests/test_spring_timeline.py) | Public spring track integration, continuous geometry safety and atomic authoring. | 30 |
| [tests/test_subtitles.py](../../tests/test_subtitles.py) | test fixture / test module | 9 |
| [tests/test_surfaces.py](../../tests/test_surfaces.py) | Procedural surfaces keep allocated geometry, soft pixels, and ordinary motion. | 7 |
| [tests/test_text_fitting.py](../../tests/test_text_fitting.py) | test fixture / test module | 4 |
| [tests/test_timed_scene.py](../../tests/test_timed_scene.py) | test fixture / test module | 4 |
| [tests/test_web.py](../../tests/test_web.py) | test fixture / test module | 10 |
| [website/scripts/build_content.py](../../website/scripts/build_content.py) | Generate API guides with inline snippets; premium scenes live in the source collection. | 0 |
| [website/scripts/feature_content.py](../../website/scripts/feature_content.py) | Recent feature chapters; examples only execute preparation from explicit runners. | 0 |
| [website/scripts/verify_examples.py](../../website/scripts/verify_examples.py) | Check inline API documentation without rendering or publishing demo artifacts. | 0 |
