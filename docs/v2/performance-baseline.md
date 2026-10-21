# V2 performance baseline and gates

Status: measured V1 diagnostics plus proposed V2 certification. Source:
`22f3beaccb5a56990bd0974666b7c639a0667a68`, audited 2026-10-20.
These audit measurements predate implementation. Current results are recorded in
[the milestone records below](m5-implementation.md). See [findings](architecture-audit.md) and
[migration gates](migration-plan.md).

Implementation follow-up: [M1](m1-implementation.md), [M2](m2-implementation.md),
[M3](m3-implementation.md), [M4](m4-implementation.md) and
[M5](m5-implementation.md) record the implemented changes and scoped evidence.
The original proposal and audit measurements below retain their dated baseline.

## Environment and measurement limits

Native Python 3.12.3, Linux x86-64/glibc 2.39, AMD A6-9225, two logical CPUs.
FFmpeg 6.1.1-3ubuntu5. Installed packages: Pillow 12.3.0, NumPy 2.5.3,
PyVista 0.49.1, VTK 9.7.1, skia-python 144.0.post2, ModernGL 5.13.0,
glcontext 3.1.0, build123d 0.13.0 and Trimesh 5.1.1.
ModernGL probe: EGL, Mesa 25.2.8, OpenGL 4.5, llvmpipe LLVM 20.1.2 software device;
shader hash `40780c27968052589c979acb2aa674ad79127fc09e269f3e37fbc4f979685a03`.

Trials used fresh child interpreters, sequentially, with no concurrent package test
run. Filesystem/OS caches were not flushed. Shared-host noise remains possible.
Rendering timings exclude FFmpeg, include conversion to the public Pillow image,
and use 1920×1080 output. These short trials are diagnostic, not release
certification, statistical proof, or a claim of visual equivalence across backends.

## Fresh-process imports

The timed region was `__import__(package)` in `.venv/bin/python -B -c ...`.
`-B` prevents writing bytecode; existing bytecode/filesystem caches may be read.
RSS is Linux `resource.getrusage(RUSAGE_SELF).ru_maxrss`, not incremental allocation.

| Package | Three import samples, ms | Median ms | Peak RSS range, KiB | Loaded Python modules |
| --- | --- | ---: | ---: | ---: |
| Core | 576.81, 463.08, 504.90 | 504.90 | 31,452–31,640 | 288 |
| Kit | 608.85, 580.96, 528.19 | 580.96 | 32,860–32,980 | 317 |
| Agent | 1,052.51, 863.36, 875.04 | 875.04 | 41,608–41,712 | 381 |

None loaded PyVista, VTK, NumPy, Skia, ModernGL, Playwright, Matplotlib, build123d,
Trimesh or chess. The confirmed import issue is broad Python wrapper loading,
while the confirmed installation issue is a required native dependency closure.
Do not confuse those costs.

## Renderer diagnostic measurements

Use the existing process-isolated worker, for example:

```bash
.venv/bin/python -B scripts/benchmark_renderers.py --worker ui 1920 pillow 1 6
.venv/bin/python -B scripts/benchmark_renderers.py --worker ui 1920 pillow 2 4
.venv/bin/python -B scripts/benchmark_renderers.py --worker ui 1920 skia 1 6
.venv/bin/python -B scripts/benchmark_renderers.py --worker effects 1920 pillow 1 4
.venv/bin/python -B scripts/benchmark_renderers.py --worker effects 1920 skia 1 6
```

Each command was run three times. Before measurement each worker renders one cold
frame and two further warm-up frames. UI is 48 moving rounded rectangles. `effects`
is the script's masked gradient/shadow card workload, not a certification of all
NumPy/GPU effect stacks. It deliberately uses raster cards for Pillow and retained
surfaces for Skia, comparing supported authoring paths rather than identical work.

| Workload/backend | AA | Frames/trial | Three trial medians, ms | Median of medians, ms | Cold-frame range, ms | Peak RSS range, KiB |
| --- | ---: | ---: | --- | ---: | --- | --- |
| UI / Pillow | 1 | 6 | 28.736, 36.105, 33.283 | 33.283 | 57.074–73.209 | 61,480–61,744 |
| UI / Pillow | 2 | 4 | 649.313, 635.328, 679.107 | 649.313 | 731.961–766.192 | 153,764–153,868 |
| UI / Skia | 1 | 6 | 69.640, 82.976, 72.837 | 72.837 | 221.984–350.237 | 101,204–101,812 |
| Cards / Pillow | 1 | 4 | 917.942, 902.118, 920.991 | 917.942 | 1,132.687–1,157.119 | 109,692–109,808 |
| Cards / Skia | 1 | 6 | 128.538, 133.861, 131.537 | 131.537 | 322.617–339.235 | 114,616–114,752 |

Raw measured frame samples in trial order, milliseconds:

```text
ui/pillow/AA1
  41.025 27.277 29.582 37.910 27.336 27.889
  45.272 31.890 29.196 38.144 38.045 34.165
  25.450 28.010 36.737 35.250 31.316 37.059
ui/pillow/AA2
  649.219 653.386 649.407 637.107
  639.703 629.820 641.108 630.953
  643.443 683.165 675.050 706.058
ui/skia/AA1
  68.698 59.449 73.946 61.826 70.583 81.013
  93.363 74.622 76.477 81.377 84.576 90.297
  73.170 79.627 68.896 79.469 72.504 58.872
effects/pillow/AA1
  890.426 1100.954 945.458 853.805
  915.228 898.177 867.616 906.059
  928.368 913.613 890.937 1250.751
effects/skia/AA1
  141.602 118.625 137.694 127.531 120.694 129.544
  132.521 128.429 163.848 135.201 131.888 139.263
  139.231 125.951 132.698 138.880 124.093 130.376
```

Pillow card authoring took 1,730.8–1,920.5 ms versus Skia retained-card authoring
19.1–27.2 ms. Skia initialization was 78.8–188.4 ms; Pillow initialization was
0.012–0.046 ms. These costs have different ownership and must be reported separately.
Pillow AA1 was faster on this UI workload; Skia was faster on the card workload.
Neither observation supports a universal fastest-backend or 4K realtime claim.

## Structural memory and footprint evidence

| Authored components in nested chain | Retained component snapshots |
| ---: | ---: |
| 5 | 15 |
| 9 | 45 |
| 17 | 153 |
| 33 | 561 |

The counts follow `n(n+1)/2` because every group's deepcopy retains its descendant
tree alongside the separate entry snapshots. The V2 target is exactly one compiled
visual snapshot per authored node plus O(n) links/tracks, without weakening source
mutation isolation. This is a confirmed structural result, not an RSS estimate.

The active Linux base dependency closure has 32 distributions including Core.
Installed-file accounting gives VTK 562.23 MiB, NumPy 53.75 MiB, PyVista 7.33 MiB,
and Pillow 18.76 MiB. These are installed distribution files, not download sizes,
incremental RSS or a fresh minimal-wheel install. Editable Core metadata alone
does not account for its source/assets. See [dependency analysis](dependency-analysis.md).

## Certification matrix to establish before implementation gates

| Area | Fixed fixtures | Required measurements |
| --- | --- | --- |
| Installation/import | Base; Skia; GPU; 3D; CAD; geometry; Kit; Agent | Fresh wheel dependency closure/installed bytes; 10 fresh-process imports per candidate; loaded native modules; no display/network requirement for base |
| Authoring/build | Hello World, narrated recipe, 100/1,000-node scenes, 1/8/32-depth groups, long property tracks | Construct, compile, measurement, asset/probe/hash time; node/track counts; retained Python/native memory |
| 2D rendering | Existing plain/UI/paths/type/effects/layers workloads; captions; charts/diagrams | 1080p and 4K, Pillow AA1/AA2, Skia AA1; cold and warm median/p95, hold hits, conversion time, cache bytes |
| Effects/GPU | Bloom, particles, background, transitions, masks | Same source-time samples and semantic inputs; hardware identity, native/raster counts, upload/readback bytes/counts, GPU timer and CPU wall time |
| Geometry | Existing bracket/gears/instances and bounded field/section viewport | Preparation separate from mesh-only replay; triangles/parts; session count, aggregate process memory, IPC; no per-frame CAD regeneration |
| Encoding | Fixed 3-second RGB source, then a rendered narrated excerpt | Render-only, RGB conversion/pipe and FFmpeg encode/mux separately; actual frames/fps/duration, complete decode, audio source alignment |
| Soak/failure | 1,000 changing assets, repeated create/close, stalled native/encoder worker | Cache eviction, post-close resource counters, bounded cancellation, RSS trend with native/driver scope identified |

Run three isolated trials for rendering, each with ten warm-up frames including the
cold frame and 120 measured frames. Record every sample; report median/p95 per
trial and across trials. Run sequentially, record OS/CPU/GPU/fonts/dependencies/
shader hashes/resolution/AA/source range, and freeze the workload revision.

For release comparisons build **complete** V1 and candidate wheels in separate
environments. `--baseline-ref` currently loads an older renderer file against
current components; that is useful diagnosis, not a full cross-version baseline.
Use identical authored intent and record unavoidable raster/native differences.
Pair timings with image/layout review; a speedup obtained by changing text metrics,
dropping effects or lowering quality does not pass.

M1 gate: Core import median at most 50% of a freshly remeasured frozen V1 median
on the same host (the diagnostic reference is 504.90 ms, suggesting 252.45 ms).
Frame median and p95 must remain within 1.10× the certified reference for matched
plain/UI AA1/AA2 fixtures. If that gate fails, narrow/rework the milestone rather
than relaxing fidelity or silently changing the default AA.

Later gates: linear snapshot retention; no duplicate backend track evaluation;
bounded cache/session behavior; unchanged correctness and image contracts; no
greater than 10% median/p95 regression in the matched certification workloads.
Do not set an absolute hardware GPU fps target from llvmpipe measurements.

## Historical and unmeasured evidence

Existing [CAD verification](../cad-geometry-verification.md),
[Skia verification](../skia-verification.md), and
[ModernGL verification](../moderngl-verification.md) contain earlier partial
benchmarks. Keep their original dates/limitations; they are not refreshed results
for the present table. The corrected roughly one-million-triangle stress fixture,
hardware GPU, sustained 4K, long soak, fresh minimal wheel footprint, and isolated
encoding timings were not measured in this audit. Normal suite exports verify
bounded fixtures, not a delivered full film. Browser integration was skipped.
