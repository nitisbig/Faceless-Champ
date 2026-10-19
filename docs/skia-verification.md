# Skia integration verification

Implementation is local and unreleased. Pillow remains the default; Skia and
native typography/retained surfaces are explicit opt-ins. See [usage](skia.md)
and [architecture](decisions/skia-backend.md).

## Completed checks

The implementation session completed these checks; the final continuation did
not repeat the full suites:

- Core suite: 1,388 passed, 2 skipped before the final specialist-session
  regression was added. The final focused Skia suite passed all 13 tests.
- Kit suite: 273 passed, including backend/profile integration.
- Agent: all 159 cases covered across suite and targeted runs. This was not a
  single clean full-suite run: the final media rerun passed all 9 media tests
  after a concurrent source edit correctly invalidated an evidence fingerprint.
  Backend/storyboard and discovery checks also passed.
- Latest Core/Kit/Agent wheels installed and exercised in headless Docker as
  UID 10001, with network disabled. Lazy imports, native paths/text, a two-frame
  MP4 and complete FFmpeg decode passed. This is installed-wheel Docker
  evidence, not a remote cloud deployment or full-film export.
- Optional-dependency import/failure checks, deterministic source-time sampling,
  alpha/mask semantics, allocation guards, native font fitting and renderer
  ownership are covered by the focused tests.
- Lock consistency, Ruff and whitespace checks passed during implementation.

Existing HelloWorld tests were updated to derive duration/frame expectations
from the lesson's actual duration rather than an obsolete 14.96-second constant.
Lesson content was not changed.

## Preview artifacts

`output/skia-integration/preview-1080p.mp4` is a four-second reference preview,
1920×1080, 24 fps, 96 frames. Final continuation verified metadata and a complete
FFmpeg decode, and visually inspected an encoded frame and the 3840×2160 still
at `output/skia-integration/frame-4k.png`. Generated output is intentionally
ignored by Git. Reproduce it with:

```bash
python examples/skia_showcase.py --output output/skia-integration/preview-1080p.mp4
python examples/skia_showcase.py --frame --quality 4k --output output/skia-integration/frame-4k.png
```

## Performance evidence

The original comprehensive benchmark was interrupted without a report. The
continuation started a reduced, single-trial UI/effects comparison, then stopped
the remaining matrix once the slow legacy effects workload was characterized.
This deliberately avoids further lengthy comparison runs. The completed 1080p
warm-frame medians (24 samples after 3 warmups) were:

| Workload | Pillow 1× | Pillow 2× | Skia 1× | Previous Pillow 2× |
| --- | ---: | ---: | ---: | ---: |
| 48 animated UI cards | 27.64 ms | 624.63 ms | 79.72 ms | 612.54 ms |
| Masked gradient/shadow effects | 828.20 ms | 3,995.48 ms | 129.69 ms | Not completed |

The UI default-Pillow comparison was approximately +2%, below the guide's
investigation threshold, but one trial does not establish a regression budget.
Skia is not universally faster: simple UI cards were faster in Pillow at 1×.
The previous renderer was loaded from `00869a7` against current components, not
from a separate historical installation. Effects use native retained surfaces
for Skia and legacy raster surfaces for Pillow; this compares supported authoring
paths, not identical internal work. Frame timings include conversion but exclude
FFmpeg. The interrupted comparison did not produce the complete JSON report.

A separate bounded 4K native-effects check measured two warm frames after three
warmups: 483.60 ms median (about 2.07 fps), 911.11 ms cold frame and 234.4 MiB
peak process RSS. Two samples verify the 4K path, not sustained throughput.
Completed measurements are summarized in
`output/skia-integration/benchmarks.json`; its partial status is explicit and
it must not be confused with the full benchmark script's report schema.

The benchmark script remains available for a later, deliberate full measurement:

```bash
python scripts/benchmark_renderers.py --trials 1 --workloads ui effects --baseline-ref HEAD --output output/skia-integration/benchmarks.json
```

An uninterrupted script run saves per-frame timings, warm/cold timings, peak
process RSS, native counters and dependency/font provenance. A single trial is
a smoke benchmark, not a statistically conclusive performance certification.

## Remaining boundaries

Specialist clip producers remain raster-backed. GPU acceleration, SVG DOM
import, path morphing, animated gradient stops, group shadows and backdrop blur
are outside v1. Native pixels are deterministic for fixed dependencies, fonts
and platform, not guaranteed byte-identical across platforms. No full-film,
remote cloud, or sustained realtime 4K claim is made.
