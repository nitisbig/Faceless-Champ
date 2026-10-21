# M2 — shared compilation, measurement and raster sources

Implementation record for [M2](migration-plan.md#m2--shared-compilation-measurement-and-source-seam),
authorized after M1; validated 2026-10-21. M1's installed wheel is the comparison baseline; the original
audit and V1 fixtures remain frozen at `22f3beaccb5a56990bd0974666b7c639a0667a68`.
This phase keeps Core → Kit → Agent ownership and the existing painting paths.

## Implemented boundaries

| Files | Responsibility |
| --- | --- |
| Core `_rendering/plan.py` | Owned visual references, frozen node/resource/track/scene/composition records, stable z ordering, per-property track indexes and revision-based compilation |
| Core `_rendering/evaluate.py` | Arbitrary-time track interpolation, evaluated entry adapters, world/logical/ink bounds, lifetime/opacity/source-age/isolation records, fitted composition placement and terminal left-limit holds |
| Core `_rendering/measure.py` | Reusable CPU text/equation/caption/intrinsic/logical metrics; bounded font/layout/equation/metadata retention; no renderer, browser, GL or VTK session construction |
| Core `_rendering/resources.py` | Existing byte-accounted LRU plus bounded renderer-owned raster sessions, independent returned frames and failure/eviction/close cleanup |
| Core `sources.py` | Public RasterSource/RasterSession protocols and Viewport; private compatibility descriptor for existing domain viewport producers |
| Core `backends/pillow.py`, `renderer.py` | Pillow painting moved behind its original public class alias; unchanged custom two-method Renderer protocol and caller ownership |
| Core `components.py`, `animation.py`, domain owners | Public validation and pure resolution hooks; Chart/Map/Group/Countdown rules leave generic timeline policy |
| Core `subtitles.py`, Kit `subtitles.py`, Agent `context.py` | One raw SRT parser, Kit facade, Agent-specific bounded inputs/diagnostics and retained source overlaps |

`Scene.add()` deep-copies one graph with a shared memo, rather than copying each
descendant subtree independently. Each authored visual has one retained private
snapshot shared by its entry, group edges and compiled node. Compiling adds numeric
records and references, not another visual copy. Failed validation/add/play and
schedule preparation remain transactional. Supported add/remove/play/schedule,
wait/wait_until/at and audio mutations invalidate execution data. Canvas changes
also change the compilation key. Private direct mutation of entries is not an
invalidation API.

Built-in Pillow, Skia and shared compositing consume the same evaluated entry
states. A frame's indexed tracks are evaluated once for a scene/time; paint paths
can query those cached states repeatedly. Per-property binary search selects the
latest started track, retaining exact easing/keyframe/Spring endpoint behavior.
Geometry is optional for paths that need only evaluated states. Composition
records are cached against child plan identities and composition settings.

The record containers and numeric state are frozen. Component implementations are
existing Python classes, read-only by ownership inside execution records; this is
not a public deep-freeze of every class or a serialized interchange schema.
Legacy prepared asset caches may still be used by compatibility paint paths.
Generic sessions live outside descriptors. Legacy producers without a semantic
fingerprint receive a monotonic process-local identity, preventing cache collisions
from recycled Python object IDs. Existing scientific worker isolation,
native text opt-in, antialiasing defaults and FFmpeg/audio algorithms are retained.
The VTK worker converts read-only state mappings into detached numeric dictionaries
at the IPC boundary; compiled mapping proxies and native sessions are not pickled.

## Compatibility and phase limits

- All original 166 exports retain their defining object identities and order.
  Viewport, RasterSource, RasterSession and parse_srt_cues are appended. Kit adds
  read_subtitle_cues. Public PillowRenderer remains defined at its legacy import
  path for discovery/pickling; direct backend imports resolve the same class.
- The source integration contract and runnable example are in
  [raster sources](../raster-sources.md). Fixed-size measurement never decodes its
  source or creates native viewport contexts. Explicit Skia text metrics may
  shape fonts on the CPU; optional equation measurement may use Matplotlib.
- Source session keys include descriptor identity and target size; decoded frame
  keys include semantic fingerprint, size and content key. Retention bounds apply
  to decoded bytes and session count, not arbitrary native RSS. Descriptor
  authors own valid fingerprints, pure keys and partially failed open cleanup.
- Legacy domain adapters keep their own clock/endpoint rules. The new descriptor
  bridge can open legacy producers through owned sessions; existing optimized
  domain painting remains compatible. No domain is removed or extracted in M2.
- `_composition_plan.py` and `_render_state.py` forward shared timing/geometry
  helpers. Pixel fitting helpers remain during M3 transition. A permanent second
  evaluator is not shipped; the complete frozen M1 wheel is the external parity
  and rollback reference.
- Backend traversal/compositor convergence is M3. Chess retirement/domain
  extraction is M4. Kit production-service expansion is deferred. No releases,
  migrations of user projects or remote exports are performed by this phase.

## Validation and measurements

| Lane | Result |
| --- | --- |
| Full Core suite, with isolated base wheel and same-host native wheel reference | 1,572 passed, 2 skipped; 296.32 s |
| Full Kit suite | 309 passed; 76.30 s |
| Full Agent suite | 179 passed; 336.71 s |
| Final scoped Core checks after cache serialization/cursor guards | 183 passed; 5.89 s |
| Clean base wheel | Core + Pillow only; base scene/layout/frame hashes, still, ranged H.264/AAC export, full decode, exact frames and source audio windows pass |
| Clean three-wheel base | 10 distributions; 1,019-entry registry, new API discovery, doctor, starter validation/frame; no optional native engine imports |
| Package resources | All 295 non-Python Core resources byte-identical to M1 |
| Changed Python files | Ruff and formatting pass; AST parsing passes for all 46 changed/new Python files |

The two skips are the existing opt-in Chromium integration checks. The one Core
warning is the pre-existing Pillow getdata deprecation in a test. The final scoped
run includes five additional cache-boundary cases (absolute cursor entry plus
copy/pickle of four composition kinds) added after the full Core collection.
It also reruns timed scenes, Spring schedules, source/measurement and composition
hold regressions against the final source. Full-suite logs and wheels are retained
under `output/v2-m2/`; no full narrated film or remote render is claimed.

A broad repository Ruff scan additionally reports the unchanged pre-existing
TRY004 at `facelesschamp-agent/src/facelesschamp_agent/project.py:81`. The changed
files pass without suppressing or modifying that unrelated code.

Caption measurement reuses metric inputs in its cache key, so changing font size,
width or spacing during authoring reflows correctly. This preserves Kit's existing
caption-fitting loop without retiming any cue. Rebuildable execution caches are
excluded from composition deepcopy/pickle state; authored scenes/tracks/inputs
retain their previous copy behavior. Absolute cursor contexts invalidate on entry
as well as exit.

The original frozen 2D/native-text goldens are unchanged. On the resumed host,
three VTK scientific hashes differ from the old captured fixture in **both** the
complete M1 wheel and M2. Their exact host-level cause is not established. All six
native sample hashes match between complete M1 and M2 wheels on this host, and
native text/path hashes still match the original goldens. The explicit
`FC_NATIVE_REFERENCE_PYTHON` lane asserts an isolated installed M1 package, matched
native dependency versions and exact sampled pixels; the original
`FC_NATIVE_REFERENCE_PIXELS=1` historical-stack lane remains available. Neither
fixture nor raster tolerance was relaxed to conceal a candidate difference.

M2-specific tests cover nested/wide snapshot identity, immutable cached records,
mutation isolation, arbitrary sampling order, supported invalidation, conflicting
track atomicity, custom animation hooks, terminal holds, source clocks, GIF and
caption keys, no-context measurement, independent cached pixels, source error
cleanup and custom renderer compatibility. Existing full package suites and the
frozen pixel/export fixtures provide behavioral regression evidence.

The reproducible comparison entrypoint is `scripts/benchmark_compilation.py`.
It runs complete installed baseline/candidate packages in separate fresh
interpreters, sequentially. Snapshot/build memory uses tracemalloc after group
construction; both packages first warm a two-node scene and M2 compilation so
lazy imports do not contaminate only one snapshot region. First-use, authoring,
snapshot and compile times are recorded separately. RSS is the
whole process high-water mark. Rendering uses the frozen M1 workload script at
1920×1080, Pillow AA1/AA2, ten warmups including cold and 120 measured frames in
three fresh processes per case. Correctness suites finish before measurements.

Acceptance requires linear retained snapshots, frozen visual/export parity,
bounded resource lifecycle, all applicable suites, a standalone base wheel and
no greater than 10% median/p95 regression in matched plain/UI render cells.


## Next implementation boundary

M3 is the next milestone and requires separate authorization. Start with backend
consumption of the shared frame/geometry plan and removal of duplicate traversal,
source-age/signature and isolation policy. Keep native painting, GL/VTK ownership,
public custom renderer access and fidelity unchanged. Its acceptance gate is a
common backend contract matrix, exact/tolerance image parity appropriate to each
backend, bounded cache/session cleanup and the same matched timing limits. Domain
extraction and ChessChamp decisions remain in M4.


## Measured acceptance results

M2 passes the scoped acceptance gates on this host. Benchmark environment is
Python 3.12.3 on Linux x86-64, AMD A6-9225 (two CPUs), with the installed native
versions recorded in M1. Both comparison interpreters load their own complete
wheel before a shared dependency-only site-packages path. The clean base lanes
use independent environments without that path. Tests and timing runs are separate;
ambient desktop/scheduler activity remains outside the experiment's control.

Warm construction measurements are medians of three fresh processes. Traced bytes
are retained Python allocations after snapshot plus M2 compilation, excluding
prewarmed module imports. The snapshot timer excludes compilation; raw compile,
first-use, authoring, peak tracing and RSS measurements are retained separately.

| Shape | Retained snapshots, M1 → M2 | Snapshot ms, M1 → M2 | Retained traced bytes, M1 → M2 |
| --- | ---: | ---: | ---: |
| chain 5 | 15 → 5 | 5.04 → 3.75 | 17,824 → 17,072 |
| chain 9 | 45 → 9 | 13.90 → 5.48 | 39,376 → 27,072 |
| chain 17 | 153 → 17 | 76.23 → 5.42 | 108,864 → 46,000 |
| chain 33 | 561 → 33 | 215.78 → 21.30 | 351,592 → 83,960 |
| wide 100 | 201 → 101 | 87.93 → 71.17 | 213,136 → 254,048 |
| wide 1000 | 2001 → 1001 | 541.82 → 307.43 | 2,075,528 → 2,503,920 |

The 33-node chain retains 76% fewer traced bytes including compiled records and
snapshots about ten times faster. The wide 1,000-leaf scene retains **more** traced
Python data (2.50 MB versus 2.08 MB), because compiled state/index records replace
less duplicated visual data in a shallow tree. Its full process peak RSS is lower
(31,644 versus 37,052 KiB). This phase establishes linear snapshot ownership; it
is not a claim that every representation or cold-start cost becomes smaller.

Render measurements below are median-of-trial medians and median-of-trial p95,
including image conversion and excluding encoding, at 1920×1080. Each trial has
ten warm-up frames including cold and 120 measured source-time samples.

| Pillow workload | AA | Median ms, M1 → M2 | p95 ms, M1 → M2 | ≤10% gate |
| --- | ---: | ---: | ---: | --- |
| plain | 1 | 6.56 → 5.53 | 29.79 → 18.95 | Pass |
| plain | 2 | 5.03 → 5.11 | 8.29 → 7.83 | Pass |
| ui | 1 | 56.08 → 29.99 | 154.38 → 39.18 | Pass |
| ui | 2 | 707.81 → 705.08 | 752.00 → 748.50 | Pass |

The original three-trial static AA2 cell failed (4.77 → 6.30 ms median,
11.41 → 15.25 ms p95). Other trials also showed substantial wall-time variation.
Before repeating that cell, its protocol was fixed at **nine fresh process pairs**,
alternating which build runs first. That follow-up passes (5.03 → 5.11 ms median,
8.29 → 7.83 ms p95). Both the failure and every follow-up sample are retained;
the threshold and pixel workload were unchanged. This is same-host verification,
not universal performance certification or statistical proof across machines.

Cold compilation/import costs can rise: for example the initial plain AA1 cell's
cold frame was 79.68 → 136.63 ms. Those costs are exposed in raw results rather
than hidden by moving compilation into validation. M3 must assess startup cost
alongside hot-path convergence. Native hardware GPU, sustained 4K, long soaks,
matching Chromium integration and a full narrated-film export are not certified.

Reproduce from the repository root after installing complete wheels into the
comparison interpreters (their package files must reside under their own prefixes):

```bash
.venv/bin/python scripts/benchmark_compilation.py \
  --baseline-python /tmp/fc-m2/baseline-env/bin/python \
  --candidate-python /tmp/fc-m2/candidate-env/bin/python \
  --render-workload output/v2-m2/reference/benchmark_renderers.py \
  --trials 3 --frames 120 --output output/v2-m2/evidence/benchmarks.json

.venv/bin/python docs/v2/m2-evidence/repeat_render.py \
  --baseline-python /tmp/fc-m2/baseline-env/bin/python \
  --candidate-python /tmp/fc-m2/candidate-env/bin/python \
  --driver scripts/benchmark_compilation.py \
  --workload-script output/v2-m2/reference/benchmark_renderers.py \
  --workload plain --aa 2 --trials 9 --frames 120 \
  --output output/v2-m2/evidence/paired-static-aa2.json
```

Freeze the workload with `git show 22f3beaccb5a56990bd0974666b7c639a0667a68:scripts/benchmark_renderers.py`.
The raw artifact records its SHA-256. Do not use a single old renderer module
against the current components as a cross-version baseline.

Evidence: [acceptance](m2-evidence/acceptance.json),
[complete raw trials](m2-evidence/benchmarks.json),
[counterbalanced static repeat](m2-evidence/paired-static-aa2.json),
[wheel identities](m2-evidence/wheels.json),
[resources](m2-evidence/resources.json),
[native wheel parity](m2-evidence/native-parity.json),
[clean three-wheel runtime](m2-evidence/agent-base.json).

The M2 acceptance boundary is complete: standalone base installation retained,
one owned snapshot per authored node, shared arbitrary-time state/measurement,
owned raster-source sessions, preserved public/custom-renderer and production
contracts, passing scoped regressions and matched timing gates. No M3 backend
rewrite or M4 domain removal is included.
