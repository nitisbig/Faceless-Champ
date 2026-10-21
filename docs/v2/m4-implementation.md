# M4 — domain extraction and chess retirement

Implemented 2026-10-21, following the scoped M3 implementation. M4 preserves
Core → Kit → Agent ownership and retains non-chess capabilities. See the
[migration guide](m4-migration.md) for imports, installation, data and V1 recovery.

## Implementation

- Relocated the existing charts, maps/flags, coding/workspace, diagrams, desktop,
  playground, web and engineering authoring implementations into Kit. Their
  preparation, drawing, geometry and serialization algorithms are reused. Chart
  raster production remains the initial compatibility route; no chart-engine
  rewrite or blanket replacement with static external plots was introduced.
- Core `integrations/pyvista/` owns mesh/part/style/camera types, native rendering,
  the bounded isolation worker and float-environment protection. Core
  `integrations/build123d.py`, `trimesh.py`, `dependencies.py` and `geometry.py`
  own optional conversion/probes and shared rigid-body math. Engineering scripts,
  annotations, preset source loading, models and blueprints belong to Kit.
- Added small `Component.render_raster`, `validate_render` and `raster_source`
  extension hooks. Core's raster service and compiler contain no domain-class
  dispatch. Generic raster sources retain renderer-owned frame/session bounds.
  PyVistaSource accepts a supplied scientific scene description; it does not
  import an engineering frontend. Live native sessions remain outside snapshots.
- PyVista source sessions preserve floating-point state during initialization,
  frame evaluation and close. GL uses the relocated isolated worker. The shared
  subprocess deadlines, graceful native shutdown and owning-thread behavior from
  M3 remain intact. Source sessions own native cleanup/eviction and fixed density.
- Removed Core domain exports and added the same 52 authoring names to Kit's
  facade. Core-local native aliases remain. Old domain import modules are error
  notices, not reverse imports or duplicate implementations. Chart data animation
  delegates normalization to its component; ChartReveal is Kit-owned.
- Moved country/flag/networking resources to Kit with package-data declarations.
  Reused the same Core mono font for CodingChamp. Removed 254 exact root artwork
  duplicates after byte comparison; kept source/provenance documents and differing
  files. Chess artwork and its root duplicates were removed separately.
- Retired chess implementation, tests of its removed behavior, block, compiler
  report branch, template, scaffold, extra and advertisements. Mixed tests retain
  their non-chess assertions; new tests enforce retirement and migration guidance.
- Updated managed source callers, examples, workers, dependency ownership, selected
  guides/resources and the generated website catalog. Project-owned render scripts,
  audio/cues, prepared outputs, historic audit/evidence files and JSON goldens were
  left unchanged. Agent discovery recognizes the relocated integration/domain
  families and no longer offers the chess capability.
- Moved 14 domain test modules to `facelesschamp-kit/tests/domains/`; low-level
  geometry/native tests remain in Core. Their assertions are retained, with import,
  schema-resource and session-owner references updated for the new boundaries.

## Major validation

Only focused functional/integration tests were executed, following the user's
earlier key-test preference. Local evidence and wheels are under ignored
`output/v2-m4/`; they are not release artifacts.

| Check | Evidence/result |
| --- | --- |
| Core ownership, import errors, retirement, lazy identity, base render/export and relocated native guards | `core-final-key-tests.log`: 16 passed |
| Generic renderer/source/lifecycle matrix | Initial hook run: 34 passed plus one migrated test-size assertion; that assertion was corrected and rechecked in the final Core run |
| Domain rendering/data/preparation | `domain-key-tests.log`: 20 passed plus a new expected export-count assertion; corrected from 51 to the actual 52 names |
| Domain ownership, frozen pixels, networking resources, coding and engineering recipe validation | `domain-final-key-tests.log`: 6 passed |
| Kit native validation/frame/storyboard/export, coding template preparation, prepared web block | `kit-key-tests.log`: 5 passed |
| Source eviction/cleanup/caller ownership and remaining mixed theme assertions | `ownership-key-tests.log`: 3 passed |
| Agent catalog API/CLI parity, optional-native-free discovery and native frame/preview workflow | `agent-final-key-tests.log`: 3 passed |
| Native CAD/mesh bridges, units and immutable preparation | `native-bridges-test.log`: 4 passed |
| Real capped PyVista viewport followed by native Skia overlay | `native-overlay-test.log`: 1 passed |
| Fractional scientific viewport dimensions, direct and isolated sessions | `fractional-source-test.log`: 2 passed |
| Agent relocated font/icon asset catalog | `agent-assets-test.log`: 1 passed |
| Fresh installed Core wheel | `core-wheel-test.log`: 1 passed; exactly Core + Pillow; 20 distinct frozen base hashes, FFprobe/full decode/ranged audio checks |
| Fresh installed Kit wheel | Exactly Core + Kit + Pillow + packaging; all moved facade names resolve; flags, networking assets, schema and mono font exist; chart validation/frame succeeds without native extras |

The full Kit fixture compares all 28 distinct original base/domain frame hashes
against the untouched V1 JSON, including random seeks. Six native/scientific frame
hashes also match the same-host M3 reference (`native.json`). Original fixtures
remain available separately for old complete-wheel comparisons. Hash equivalence
does not establish performance or hardware acceleration.

Core (1083 at collection time) and Kit (769) collection checks inventory importability only; they are not full
suite runs. Targeted checks cover chart data tracks, geographic rotation, flag
assets, editor reveals, graph JSON/seek behavior, desktop composition, prepared web
playback, Python-only preparation without Playwright, scientific scripts and native
context/float-state preservation. No browser capture or long render was launched.

Fresh wheel inspection found stale chess files in an old setuptools build directory
during the first Kit build. The generated build directory was cleared and the Kit
wheel rebuilt; the checked candidate contains no retired files. Core keeps only
the intentional chess import-error notice. Both wheels contain the moved resources
in their owning distribution.

Ruff/format checks cover the changed Core/Kit rendering and domain code, migration
tests and Agent registry. A pre-existing Agent `project.py:81` TRY004 finding is
outside this milestone. Full Core/Kit/Agent suites, certification benchmarks,
hardware/platform lanes and long resource soaks were not run. M3/M2 historical
results do not certify M4.

## Remaining work

M4 implementation is complete within this validation scope. M5 remains: shared Kit
production services and Agent delegation, generated-document synchronization,
coordinated V2 version/bounds and release/distribution verification. The current
manifests retain development-era version numbers; install paired source/wheels,
not a mixture of M4 Kit and published V1 Core. No release was published.
