# ModernGL verification

Date: 2026-10-19. Status: experimental first release, locally verified with
software EGL. Hardware acceleration and performance certification remain open.

See the [user guide](moderngl.md), [architecture decision](decisions/moderngl-backend.md)
and [phase/file mapping](decisions/moderngl-phases.md).

## Environment

- Python 3.12.3, Pillow 12.3.0, NumPy 2.5.3, Skia 144.0.post2.
- ModernGL 5.13.0 and glcontext 3.1.0.
- EGL, OpenGL 4.5 Core, Mesa 25.2.8; llvmpipe LLVM 20.1.2 (software).
- PyVista 0.49.1 / VTK 9.7.1; FFmpeg/libx264 for encoded previews.
- Two logical CPUs in the test environment. Software GL and BLAS threads were
  limited to two and one respectively for bounded local verification.

The runtime shader hash is
`40780c27968052589c979acb2aa674ad79127fc09e269f3e37fbc4f979685a03`.
The recorded color pipeline is
`encoded-srgb-composition/linear-effects-v1`.

## Regression and packaging evidence

Core's full suite passed: **1,423 tests, two skips** (1,425 collected). The focused
ModernGL suite then passed **27 tests without skips**, including the procedural
mask preflight fix. Three additional descriptor/preflight checks passed after
canonicalizing immutable numeric parameters. A final focused run passed **13
tests**, covering all six filters, all four transition modes and those three
preflight/descriptor cases. Kit's full suite passed **275 tests**.
Agent's full suite passed **162 tests**. The three new preflight/descriptor cases
were checked separately from the full Core run.

New Core coverage exercises lazy optional imports, RGBA orientation, canonical
transparent pixels, nested composition with a single final readback, masks,
member opacity, combined shadow/glow, all six effect families, transition
endpoints, animated effect bounds, deterministic random seeks, disabled caches,
resource guards, particles, actual auto fallback, ranged MP4/audio export,
caller-owned renderers and VTK context isolation. Filter comparisons allow at
most two channel levels for visible pixels; composited windowed SSIM must be at
least 0.995. These checks isolate intentional backend primitive raster differences
from effect arithmetic.

Kit tests cover public wrapper blocks, GPU profile parsing and actual export
identity. Agent tests cover offline discovery, resolved auto profiles and
rejection of review evidence with a changed shader pipeline.

All three packages built as wheels and source distributions locally. An
installed-wheel smoke test ran outside the repository, confirmed that imports
came from the installed wheel directory, checked all seven packaged GLSL files
and Agent's bundled guide, and rendered a glow scene through EGL. This uses the
local interpreter's existing dependencies; it does not certify an independently
provisioned operating system or dependency matrix.

`fc-kit --json doctor --gpu` and `fc-agent doctor --gpu --json` both reported
available software EGL and the actual driver/shader identity. `uv lock --check
--offline`, changed-file Ruff checks/format checks and `git diff --check` passed.
Lint retains the repository's existing E402/E741 conventions in touched legacy
modules; it does not claim a repository-wide cleanup.

## Inspected media

Local ignored artifacts are under `output/moderngl-integration/`:

| Artifact | Verified scope |
| --- | --- |
| `preview-1080p.mp4` | 1920×1080, 12 FPS, 12 frames, exactly one second, H.264; complete FFmpeg decode passed; extracted encoded frame visually inspected |
| `encoded-frame.png` | Encoded preview frame at 0.5 seconds; typography, panel edges, glowing orb and particle/background composition inspected |
| `frame-4k.png` | 3840×2160 still; visually inspected for layout, typography, clipping and effect appearance |

The sample is silent by design. The separate regression export test checks audio
and ranged rendering. A 4K movie and a full demonstration export were not
verified; a successful 4K still does not establish sustained 4K throughput.

Reproduce the bounded preview with:

```bash
OPENBLAS_NUM_THREADS=1 LP_NUM_THREADS=2 .venv/bin/python examples/moderngl_showcase.py --seconds 1 --fps 12 --output output/moderngl-integration/preview-1080p.mp4
```

## Performance scope

The benchmark tool now supports GPU layers, bloom, particles, backgrounds and
transitions alongside the existing matrix. It records cold and warm timings,
p95, process peak RSS, actual runtime identity, transfers, resource accounting
and GL timer queries. Certified mode uses three fresh-process trials, ten warm-up
frames including the cold frame, and 120 measured frames. FFmpeg encoding stays
outside these frame timings.

The initial 1080p UI smoke report at
`output/moderngl-integration/benchmark-smoke.json` measured 138.25 ms Pillow AA1,
2409.66 ms Pillow AA2, 152.62 ms Skia AA1 and 524.19 ms ModernGL AA1 (median,
24 frames, one trial). It ran with competing verification work and software GL;
these numbers are diagnostic and cannot establish comparative speed or a release
performance gate. The original smoke report's peak-working counter was a delta
after warm-up; the benchmark now records that peak as an absolute gauge.

An additional full-canvas timing matrix completed 1080p bloom (12,230.91 ms
median, 139,968,032 peak target bytes) and 10,000 particles (216.28 ms median,
25,003,232 peak target/buffer bytes), four measured frames each. It was stopped
during the 4K portion because software rendering was too slow for useful local
certification. Only the printed summaries were retained in
`output/moderngl-integration/benchmark-gpu-partial-smoke.json`; the matrix and raw
samples are incomplete and do not qualify any performance gate.

No hardware GPU was available. Run the certification matrix on hardware EGL
before making acceleration, realtime, 4K throughput or VRAM claims. GPU and CPU
effect scratch, external decoders, VTK sessions and driver allocations have
different accounting scopes; renderer cache budgets do not bound total RSS.

## Deferred verification and features

Docker was stopped and deferred at the user's request. No successful container
build or container execution is claimed. The optional recipe remains available
for later use.

Hardware EGL/driver coverage, sustained 1080p/4K export measurements, leak/soak
certification and non-Linux native contexts remain unverified. Native mesh
viewports and public custom GLSL are subsequent releases; ArchChamp retains its
existing scientific 3D implementation with GPU composition around its raster
viewport.
