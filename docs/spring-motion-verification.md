# Spring motion verification

Verified on 2026-10-15 against the working tree at HEAD
`d61fe16594e4f46358f61cb5bca86a982d3b77da`. This records the approved example and
documentation phase. [Machine-readable evidence](spring-motion-verification.json)
includes artifact hashes and individual sample results. Phase 5 QA is complete;
see the [release evidence](spring-motion-release.json) and final checks below.
The user authorized Phase 5 after receiving the inspected Phase 4 preview.
PR publication/review is recorded in the final handoff; no automatic merge is part
of these checks. The following sections preserve the Phase 4 results.

## Delivered example

[render.py](../examples/spring_motion/render.py) uses public core APIs and the
existing Pillow/FFmpeg path. No production source, dependencies, renderer, or
earlier examples were changed in Phase 4.

| Time | Content |
| --- | --- |
| 0–4 seconds | Five simultaneous 160-pixel moves: linear, smooth, gentle, snappy, and bouncy spring configurations. All tracks start at 0.45s and last 2.6s. |
| 4–7 seconds | Text slide with an independent smooth fade; card translation/scale/rotation; a parent Group moving three cards together. |
| 7–10 seconds | Four staggered node Groups settle around an API hub, followed by conventional connection fades. |

The three spring configurations cover critical `(100,20,1)`, overdamped
`(100,25,1)`, and underdamped `(100,10,1)` behavior. They are example labels,
not public presets. Every shot holds its final state for at least 0.6 seconds.

## Render and visual evidence

The source storyboard was rendered and inspected before encoding the preview.
The first pass exposed initially transparent text/connections whose fade targets
were also transparent, plus a footer with insufficient margin. Explicit opacity
targets and a raised footer corrected these authoring errors. Regression tests
cover terminal visibility, safe margins, equal travel, timing, and storyboard CLI
overwrite protection.

| Artifact | Verified result |
| --- | --- |
| `output/spring_motion/preview.mp4` | Silent H.264/yuv420p, 960×540, 30 fps, exactly 300 frames / 10.000 seconds, 128,922 bytes. |
| `output/spring_motion/storyboard/storyboard.png` | Twelve source-time samples in a 1440×1216 contact sheet, including overshoot and terminal holds. |
| `output/spring_motion/encoded/contact-sheet.png` | Twelve frames decoded from the actual MP4, including frame 299 at 9.966667s. Inspected for layout, visibility, clipping, and settling. |
| `output/spring_motion/peak-contact-sheet.png` | Six analytical first-peak stills, inspected along with a native-size transform frame. |

FFprobe confirmed one video stream and no audio; the entire MP4 passed
`ffmpeg -v error -i ... -f null -`. Decoded frames at indices
`0,19,53,119,129,142,209,218,230,252,270,299` were compared against fresh
Pillow frames at exactly `index/30` seconds. Mean absolute RGB differences ranged
from **0.8541 to 1.0807** on the 0–255 scale, consistent with lossy H.264/color
conversion. Source and encoded contact sheets were both inspected.

The public `--check` audit evaluated **17,759 conservative bounds** at 301 times
per shot, including the endpoints, with **23 px minimum canvas clearance**.
This sampled layout check supplements the engine's continuous local-scale
certification; it does not claim to prove continuous world-space containment.

First-peak witnesses use `u = pi / (sqrt(1-zeta**2) * S)`, where `S` is the
kernel's cached dimensionless settling horizon. All six distinct underdamped
first-peak timestamps were also checked and rendered, independently of the
export frame grid:

- Comparison: **0.641225s**; minimum full-shot clearance 23 px.
- Group transform: **4.732387s**; clearance 32 px.
- Network nodes: **7.367677, 7.497677, 7.627677, 7.757677s**; clearance 32 px.

Every track's exact terminal value equaled its target. The largest change between
the representable timestamp immediately before a track end and its exact end was
**8.000001e-8** in its coordinate/property units. Fresh source frames during the
last 0.4 seconds and at the last 30-fps sample of each shot were byte-identical.
The cuts at 4s and 7s are intentional shot changes. No clipped objects, negative
scales, unexpected terminal jumps, or overshoot collisions were observed in the
inspected artifacts.

## Reproduce

Run from the repository root with its existing environment:

```bash
.venv/bin/python examples/spring_motion/render.py --check
.venv/bin/python examples/spring_motion/render.py --storyboard-only
.venv/bin/python examples/spring_motion/render.py
# Use --overwrite when replacing existing outputs.
ffprobe -v error -show_streams -show_format -of json output/spring_motion/preview.mp4
ffmpeg -v error -i output/spring_motion/preview.mp4 -f null -
```

Both new Python snippets in the [spring guide](motion-graphics.md#spring-motion)
were executed in order; their scenes ended at 1.1s and 0.8s respectively. The
guide, API reference, architecture, and README document coefficient limits,
retiming, damping regimes, unsupported properties, conservative scale safety,
keyframes, schedules, independent fades, FPS invariance, and v1 non-goals.

## Focused code checks

Python 3.12.3, Pillow 12.3.0, pytest 9.1.1, Ruff 0.16.10, and the installed
faceless-champ 0.1.5 source environment were used offline. With
`UV_CACHE_DIR=/tmp/faceless-spring-phase4-uv` and
`MPLCONFIGDIR=/tmp/faceless-spring-phase4-mpl`:

```bash
uv run --offline --no-sync pytest tests/test_spring_example.py -q
uv run --offline --no-sync pytest tests/test_spring.py tests/test_spring_timeline.py tests/test_spring_scheduling.py tests/test_motion_graphics.py tests/test_narration_previews.py -q
uv run --offline --no-sync ruff check src tests examples facelesschamp-kit/src facelesschamp-kit/tests facelesschamp-agent/src facelesschamp-agent/tests
uv run --offline --no-sync ruff format --check src/faceless_champ/spring.py src/faceless_champ/timeline.py src/faceless_champ/scheduling.py src/faceless_champ/__init__.py tests/test_spring.py tests/test_spring_timeline.py tests/test_spring_scheduling.py tests/test_spring_example.py examples/spring_motion/render.py
git diff --check
```

Results: **4 new example tests passed in 40.85s**, and **588 existing focused
tests passed in 8.48s**: **592 passed** in total. Ruff passed across all listed
source/test/example directories, and all nine listed Python files were formatted.
Twelve spring documentation links resolved, evidence JSON parsed, and whitespace
checks passed, including new untracked files. The four preexisting repository
formatter failures documented in Phase 0 were left unchanged. An earlier combined
test attempt was interrupted; both final split commands above completed normally.

Generated media stays under ignored `output/`; the checked-in evidence records
its hashes. The optional 1920×1080 export was not rendered
(`full_export_verified: false`, `full_preview_verified: true`). No 24/30/60-fps
release export matrix, performance benchmark, full package release QA, commit,
PR, merge, or next motion subsystem was performed in Phase 4.

## Phase 5 final checks

Completed on 2026-10-15 without production-source changes in this phase. New
`examples/spring_motion/verify.py`, `examples/spring_motion/benchmark.py`, and
six `tests/test_spring_release.py` cases make the release checks reproducible.

| Suite | Result |
| --- | --- |
| Full core suite | 1,272 passed, 2 skipped in 129.88s |
| Six newly added release cases | 6 passed in 17.01s |
| Full kit suite, separately collected | 255 passed in 78.25s |
| Full agent suite, separately collected | 41 passed in 75.80s |
| Unique total | **1,574 passed, 2 skipped** |

The two skipped tests are the same opt-in Chromium integrations as the baseline
(`FC_WEB_BROWSER_TESTS=1`). Core collection preceded addition of the six release
cases; the separate final command covers those new cases. Ruff passed across
core/kit/agent source/tests and examples; all **12 feature Python files** passed
formatting. The full core formatter still reports exactly the same four baseline
files listed in Phase 0. They were not reformatted. Tracked and new-file whitespace
checks passed.

The numerical review checked independent 80-digit Decimal ODE references,
critical and real-root formulas, underdamped extrema, parameter-domain corners,
near-critical limits, origin-series joins, and left-hand terminal tolerances.
Scale safety uses analytical continuous bounds rather than a sampled frame grid.
Existing regressions cover invalid fields, unsafe keyframe segments, finite-input
arithmetic overflow, clock collapse, collisions, lifetimes, and failures in later
nested/reversed schedule children. Failed trials preserve entries, hierarchy,
track identity, ownership, snapshots, and cursor. No actionable defect was found.
AST comparison confirmed `Track` and `Entry` unchanged; animation, components,
layout, renderer, export, package dependencies, and lockfile are unchanged.

### FPS and deterministic seeking

Six combinations of underdamped/critical/overdamped springs and frame caching
disabled/enabled ran **18 complete 24/30/60-fps source seek workloads**. Each run
checked **17 identical absolute timestamps**, including 11 timestamps common to all
three frame grids and extra boundary/early-motion probes. Fresh reference states
and SHA-256 hashes of source pixels matched exactly after forward, reverse, and
seeded shuffled access; authoring objects and entry snapshots stayed unchanged.
The composition includes Groups, independent conventional fades, time-scaled
nested schedules, and ping-pong. This is direct shared-timeline validation, as
allowed by the plan, rather than three encoded FPS exports.

```bash
UV_CACHE_DIR=/tmp/faceless-spring-phase5-uv MPLCONFIGDIR=/tmp/faceless-spring-phase5-mpl uv run --offline --no-sync pytest -q
UV_CACHE_DIR=/tmp/faceless-spring-phase5-uv MPLCONFIGDIR=/tmp/faceless-spring-phase5-mpl uv run --offline --no-sync pytest tests/test_spring_release.py -q
UV_CACHE_DIR=/tmp/faceless-spring-phase5-uv MPLCONFIGDIR=/tmp/faceless-spring-phase5-kit-mpl uv run --offline --no-sync pytest -q facelesschamp-kit/tests
UV_CACHE_DIR=/tmp/faceless-spring-phase5-uv MPLCONFIGDIR=/tmp/faceless-spring-phase5-agent-mpl uv run --offline --no-sync pytest -q facelesschamp-agent/tests
.venv/bin/python examples/spring_motion/verify.py --output output/spring_motion/phase5/fps-verification.json
```

### CPU performance and memory

The final benchmark used 12 rectangles at 960×540/AA1, seven warmed, interleaved
trials of 180 frames, and separate isolated memory passes. Static mode repeats
one frame; moving modes use identical sprites, track counts, distances, and time
samples. A fourth control precomputes the spring's exact sampled easing values;
its timeline states are verified identical to the live spring before timing.
This separates curve geometry from analytical evaluation cost.

| Mode | Median ms/frame | Trial standard deviation, ms/frame |
| --- | --- | --- |
| Repeated static | 1.111 | 0.148 |
| Smooth translation | 3.560 | 0.508 |
| Spring translation | 4.248 | 0.565 |
| Identical spring trajectory, values precomputed | 3.466 | 0.396 |

The point difference versus smooth is **0.688 ms/frame (19.3%)** for this sparse
scene, and 0.782 ms versus the identical-trajectory control. Individual spring
evaluation measured **3.826 microseconds**, versus 0.222 for smooth; a 12-track
authoring batch measured 1.991 ms versus 1.744 ms. Constructor medians were
80.7/84.0/131.8 microseconds for underdamped/critical/overdamped configurations.
The renderer currently samples each entry several times per frame; this existing
behavior was profiled and left unchanged. The measured Spring workload stays
well below a 30-fps frame budget, but the observed overhead is not zero.

Timing variance is visible: exploratory 90- and 300-frame runs yielded point
differences of 0.397 and 1.213 ms/frame. Their raw trials, the final trials, and
paired control differences are retained in the JSON. No universal percentage or
precise small-overhead guarantee follows from this local benchmark. No numerical
or renderer refactor was made to chase these noisy timings.

Every isolated final worker reported a whole-process peak of **49,684 KiB**
(including interpreter/import/warmup overhead, not incremental spring memory).
Moving smooth/spring Python allocation peaks were **364,352 / 364,152 bytes**,
with retained allocations **242,813 / 242,821 bytes**. `tracemalloc` excludes native
Pillow buffers and was disabled during timing. These observations cover this
fixed workload and do not claim a universal memory bound.

```bash
.venv/bin/python examples/spring_motion/benchmark.py --frames 180 --repeats 7 --output output/spring_motion/phase5/benchmark-final.json
```

### Existing demo, packaging, and handoff

The unchanged `examples/motion_graphics/render.py` showcase completed all **18
seconds / 432 H.264 frames at 480×270, 24 fps, AA1**, with no audio. FFprobe and
complete FFmpeg decode passed. Its six source and decoded frames were inspected;
decoded/source mean RGB errors were 0.6139–0.8728. The initial 960×540/AA2 attempt
was interrupted after several minutes and is **not verified**. The complete
lower-resolution render is the representative legacy-demo evidence. The Spring
preview also passed a fresh complete decode; its Phase 4 hashes are unchanged.

To reproduce the legacy preview without modifying the existing example:

```bash
.venv/bin/python - <<'PY'
import runpy
movie = runpy.run_path("examples/motion_graphics/render.py")["showcase"]()
movie.render("output/spring_motion/phase5/existing-motion-graphics-preview.mp4",
             width=480, height=270, fps=24, antialias=1, preset="fast")
PY
ffmpeg -v error -i output/spring_motion/phase5/existing-motion-graphics-preview.mp4 -f null -
```

Offline wheel/sdist builds passed. An isolated no-dependency wheel installation
under `/tmp/faceless-spring-phase5-installed`, imported from outside the checkout,
passed three-regime ping-pong and arbitrary-time CPU frame smoke checks. Third-party
dependencies were reused from the existing environment; this is not a fresh
dependency resolution. The sdist includes the QA scripts and release regressions.

The focused feature branch is `codex/spring-motion-v1`, based on the verified
`facelesschamp-agent` commit recorded above. A PR targets that branch so earlier
unrelated work is excluded. Merge remains a review action. The optional Spring
1080p export and all later Premium Motion subsystems remain outside this handoff.
