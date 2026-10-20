# Core CAD and geometry verification

Core integration only. Kit, Agent and website changes are deferred. Remaining
stress benchmarks and expanded export checks were stopped at the user's request.
No Docker was used.

## Completed checks

- Complete core suite: **1472 passed, 2 skipped** before the final targeted fixes.
- Focused geometry run: **32 passed**, covering tessellation accuracy, units, STEP,
  native assembly transforms, immutable snapshots, mesh operations, mechanical
  closure, CAD cutaways, blueprint overlays and all three rendering backends.
- Fresh-process CAD repeatability, including odd-tooth driven-gear placement: passed.
- Final targeted checks cover dependency-provider conflicts, field-loss rejection,
  reflected/shared Trimesh scenes and exact slider-crank closure.
- Ruff and `git diff --check`: passed. Optional dependency lock check: passed.
- Fresh wheels previously passed base, CAD-only and geometry-only smoke checks,
  without source-checkout imports. Those wheel checks precede final targeted fixes;
  final release artifacts have not been rebuilt after scope reduction.

The engineering example passed structural validation. Four representative stills
were rendered and inspected: gear pair, engine cutaway, portal structure and CAD
blueprint. The local contact sheet is `output/cad-geometry/contact-sheet.png`.
No full showcase or CAD MP4 export is claimed as verified.

## Partial performance evidence

Native Python 3.12.3, Linux x86-64/glibc 2.39, AMD A6-9225 (two cores), 3795 MiB RAM.
Versions: build123d 0.13.0, OCP-novtk 8.0.1.1.0, PyVista 0.49.1, VTK 9.7.1,
NumPy 2.5.3, Trimesh 5.1.1, SciPy 1.18.1, Manifold 3.5.4,
fast-simplification 0.2.0. Renderer tests also used Skia 144.0.post2 and ModernGL 5.13.0.

Completed benchmarks used three isolated preparation/mesh-replay pairs, 30 measured
warm frames per process, 1920×1080 output and antialias 1. RSS is an aggregate
parent/child peak upper bound; ratios below 1.0 reflect shared-host variation,
not an established CAD speedup. The bracket run overlapped a bounded test.

| Case | Parts / triangles | Median prepare s | Median warm frame s | Warm ratio | Incremental peak MiB |
|---|---:|---:|---:|---:|---:|
| Bracket | 1 / 1032 | 15.90 | 0.187 | 0.936 | 715 |
| Gear pair | 2 / 9264 | 27.19 | 0.140 | 0.822 | 769 |
| Shared instances | 100 / 52000 | 9.11 | 0.303 | 0.922 | 710 |

These cases met the local ≤1.10 warm-ratio and ≤1536 MiB incremental-memory targets.
The 100 instances share one mesh snapshot; the scene snapshot is about 44 KiB.

The first mesh stress fixture accidentally generated **1,992,000** source triangles
because Trimesh doubles longitude subdivisions. Its peak was **3895–3947 MiB**,
with **3223 MiB** incremental memory, exceeding the target. The raw stress data is
retained at `output/cad-geometry/stress-mesh-2m.json`. The fixture now generates
996,000 source triangles; that corrected benchmark has **not been run**. Engine,
blueprint and remaining benchmarks are incomplete.

Native CAD keeps substantial kernel memory resident. Output triangle budgets cannot
bound allocations inside OCCT before extraction. Decimation records sampled
nearest-vertex distances, not a certified Hausdorff bound. Gear involute sampling
is separate from tessellation tolerance. Other Python versions, platforms, remote
CI and final 4K/video exports remain unverified.
