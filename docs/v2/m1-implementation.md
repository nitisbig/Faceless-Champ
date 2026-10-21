# M1 — lightweight standalone Core

Implementation record for the first milestone in [the migration plan](migration-plan.md#recommended-first-milestone).
The user authorized M1 after the documentation-only audit. The frozen V1 reference
is commit `22f3beaccb5a56990bd0974666b7c639a0667a68`. M2 and later phases remain deferred.

## Changes

- Core's only required runtime distribution is Pillow. `3d` supplies
  `pyvista>=0.49.1,<0.50`. This is an intentional new upper bound on the tested
  PyVista minor series; the locked native versions were retained.
- `cad`, `geometry`, and `geometry-advanced` explicitly include PyVista because
  their conversion results use ArchMesh. Kit and Agent forward all four extras.
- The Core facade resolves existing objects on first attribute access, caches
  their identities, preserves the ordered 166-name `__all__`, and exposes lazy
  names, including the CLI entrypoint, through `dir()`. Typed imports and
  `py.typed` remain available. No domains moved or public names were removed.
- Missing native dependencies produce explicit installation remedies. Camera,
  mesh, CAD, and mesh-inspection entrypoints check their optional engine before
  incidental NumPy use. Geometry capability metadata now includes PyVista/VTK/NumPy.
- Doctor treats 3D as optional and lists packages from distribution metadata.
  `checks.pyvista` and `checks.vtk` move into `optional`; consumers of doctor JSON
  should update those field paths. Declared missing/incompatible project
  requirements still fail. Arch scaffolds explicitly request `facelesschamp-kit[3d]` and explain installation.
- Agent discovery deliberately resolves the enumerated public facade and reads
  typed lazy re-export declarations statically. A clean-wheel test found the
  previous assumption that all root exports were eagerly present in `vars()`.
  This compatibility change preserves full signatures and consistent API/CLI
  catalogs without importing native engines or executing arbitrary submodules.
- Current installation guides and selected bundled references were synchronized.
  Historical verification reports and the original audit evidence remain dated.

Renderer/timeline algorithms, antialiasing defaults, native text opt-in, source
clocks, audio/export implementation, VTK isolation, and all domain implementations
are retained. These import improvements defer the existing internal feature
import graphs; they do not claim that every first attribute lookup is equally
cheap. Agent source/API fingerprints can change despite image parity; existing
production evidence remains historical and should be regenerated for this build.
The only production changes outside facades, metadata, installation
and doctor/scaffolding are dependency guards at existing native entrypoints and
Agent's necessary facade-discovery compatibility adjustment.

## Validation lanes

The final acceptance results, commands, and raw measurements are recorded below.

### Frozen reference and installed wheels

A complete V1 wheel was built from `git archive` of the reference commit, rather
than loading one old renderer module against new components. The reference and
candidate comparison environments install complete wheels and use the same
existing native dependency stack through a `.pth` path to its site-packages.
Their own wheel directories precede that shared dependency path. This avoids a
second native download but is **not** an independently resolved clean native
installation. Every measured package path was recorded. No checkout `src` path
is added to these wheel environments, and benchmark processes use `-I -B`.

The separate base Core and base three-wheel environments are fresh virtual
environments without system site-packages or a shared dependency path. The Core
lane asserts its complete installed distribution set and that its package file
resides under its venv prefix. Pytest runs outside it and invokes that interpreter
with `-I` from a temporary working directory.

### Regression fixtures

[Scene fixtures](../../tests/fixtures/minimal_scenes.py) and the
[frozen V1 reference](../../tests/fixtures/m1-v1-reference.json) cover:

- 166 public export names, original order, defining modules, and object identity;
- logical layout bounds and 28 distinct frame/time hashes for an animated base
  scene, nested opacity/mask/text, captions, charts, diagrams, vector paths, and
  prepared GIF playback, including repeated out-of-order sampling;
- six optional native text/path/mask and scientific-field frame hashes;
- a one-second source-range H.264/AAC export at 320×180 and 12 fps, full FFmpeg
  decode, exact 12-frame count, and rebased audio silence/tone/silence windows.

The hashes identify a fixed stack, not a platform-independent raster standard.
Native hash comparison explicitly requires `FC_NATIVE_REFERENCE_PIXELS=1` on the
recorded native rendering stack; normal cross-platform native tests retain their
existing semantic/tolerance checks. The base lane requires the frozen Pillow
version for certification. Blocked-import checks run in fresh processes, and the
minimal wheel lane also proves that optional distributions are actually absent.

### Reproduction

Build into a chosen artifact directory from the repository root:

```bash
UV_CACHE_DIR=/tmp/fc-m1/uv uv build --wheel --out-dir /tmp/fc-m1/final-wheels
UV_CACHE_DIR=/tmp/fc-m1/uv uv build --wheel --no-build-isolation --python .venv/bin/python --out-dir /tmp/fc-m1/final-wheels ./facelesschamp-kit
UV_CACHE_DIR=/tmp/fc-m1/uv uv build --wheel --no-build-isolation --python .venv/bin/python --out-dir /tmp/fc-m1/final-wheels ./facelesschamp-agent
uv venv /tmp/fc-m1/base
uv pip install --python /tmp/fc-m1/base/bin/python 'Pillow==12.3.0' /tmp/fc-m1/final-wheels/faceless_champ-0.1.6-py3-none-any.whl
FC_MINIMAL_PYTHON=/tmp/fc-m1/base/bin/python python -m pytest tests/test_minimal_install.py -q
```

The invoking test environment needs pytest; the base venv does not. FFmpeg and
ffprobe with libx264 are system prerequisites for the bounded export probe.
Build isolation can be used for Kit/Agent instead of `--no-build-isolation` when
setuptools is not already installed in the selected build interpreter.

For the all-capabilities source lane, synchronize the root lock and then install
Kit and Agent into that environment (they are separate packages, not uv workspace
members):

```bash
UV_CACHE_DIR=/tmp/fc-m1/uv uv sync --all-extras --group dev
UV_CACHE_DIR=/tmp/fc-m1/uv uv pip install -e ./facelesschamp-kit -e ./facelesschamp-agent
```

Run package source suites separately in that environment:

```bash
FC_MINIMAL_PYTHON=/tmp/fc-m1/base/bin/python FC_NATIVE_REFERENCE_PIXELS=1 MPLCONFIGDIR=/tmp/fc-m1/mpl .venv/bin/python -m pytest tests -q
MPLCONFIGDIR=/tmp/fc-m1/mpl .venv/bin/python -m pytest facelesschamp-kit/tests -q
MPLCONFIGDIR=/tmp/fc-m1/mpl .venv/bin/python -m pytest facelesschamp-agent/tests -q
```

`FC_WEB_BROWSER_TESTS=1` separately enables the two existing browser integration
checks and requires Playwright's matching Chromium/headless browser installation.

For the V1 build, use an empty reference directory with:

```bash
git archive 22f3beaccb5a56990bd0974666b7c639a0667a68 | tar -x -C /tmp/fc-m1/reference
UV_CACHE_DIR=/tmp/fc-m1/uv uv build --wheel --out-dir /tmp/fc-m1/baseline-wheels /tmp/fc-m1/reference
```

Both comparison venvs must have matched dependency versions. Warm each package once with normal bytecode writing, then measure nine fresh
imports with `python -I -B -c 'import time; start=time.perf_counter(); import faceless_champ; print((time.perf_counter()-start)*1000)'`.
Use the frozen benchmark worker with the selected wheel interpreter and these
arguments for each `plain`/`ui` × AA1/AA2 case, in three fresh processes:

```bash
/path/to/wheel-env/bin/python -I -B -c 'import runpy,sys,json; m=runpy.run_path("/tmp/fc-m1/reference/scripts/benchmark_renderers.py"); print(json.dumps(m["trial"](sys.argv[1],1920,"pillow",int(sys.argv[2]),120,certify=True)))' plain 1
```

Each trial has one cold frame, nine warm-up frames and 120 distinct measured
source-time samples. Plain is a retained static scene, so its warm measurements
include cached-frame copying; UI animates 48 cards. Timings include frame pixel
conversion and exclude FFmpeg. Run suites and benchmarks sequentially. Aggregate
using the median of trial medians and median of trial p95 values; raw samples are
retained so variability remains visible. These are same-host gates, not universal
throughput claims or evidence of hardware GPU acceleration.

## Acceptance and limitations

M1 is implemented and its installation, API, image, export, and performance gates
passed on this Linux x86-64 / Python 3.12.3 host. Coverage limits below remain
explicit; this is not a V2 release or certification of other platforms.

| Acceptance criterion | Evidence / result |
| --- | --- |
| Core base runtime is exactly Core + Pillow | Fresh isolated venv asserts exactly those two installed distributions; Pillow 12.3.0. No native/Kit/Agent/Pydantic packages. |
| Base import, CLI, layout, still and ranged export | Installed wheel checks pass from a temporary cwd with `-I`, no display, and optional imports blocked. Fully decoded 320×180, 12 fps, 12-frame H.264/AAC output; audio source-range windows pass. |
| Supported public APIs and visual/source-time behavior retained | All 166 ordered exports resolve to original defining objects; 28 base and six native hashes match V1; all 295 non-Python Core package resources are byte-identical and `py.typed` remains packaged. |
| Import median at least 50% lower | **437.44 ms → 11.88 ms (97.3% lower)**, nine fresh processes per wheel after bytecode warm-up. |
| Plain/UI AA1/AA2 median and p95 regression ≤10% | All four cells pass the protocol below. Defaults and rendering algorithms are unchanged. |
| Suites and capability lanes | Core **1,533 passed / 2 skipped**, Kit **308 passed**, Agent **178 passed**; **2,019 source passes** total. Installed-wheel capability checks: **17 passed / 0 skipped**. Ruff, formatting, wheel/source identity and lock consistency checks pass. |
| M1 scope only | No domain extraction, chess retirement, scene compilation, backend rewrite, mandatory package addition, schema conversion, release, or deployment. |

Source suite durations: Core 299.45 s, Kit 89.94 s, Agent 226.73 s. The one Core
warning is the existing Pillow `getdata()` deprecation in a test. The two skips
are the existing opt-in Chromium integration checks; browser preparation is not
certified by this milestone. The newly forwarded 3D/CAD/geometry capabilities
executed their real native tests. The installed-wheel lane additionally exercised
CAD tessellation, booleans/decimation, scientific fields/sections, native overlays,
Skia and software EGL, plus public and minimal-runtime checks.

The fresh base three-wheel environment has ten distributions: the three SDK
wheels, Pillow, packaging, Pydantic and its four supporting distributions. It has
no NumPy, PyVista, VTK, Skia, ModernGL, CAD, or browser packages. In that environment,
the 1,008-entry registry, doctor, starter validation and frame production pass;
the Arch starter fails with `ARCH_DEPENDENCY` and the explicit `3d` remedy.

### Certified frame samples

Values are milliseconds, V1 → M1, at 1920×1080. Each aggregate is the median of
three trial medians or three trial p95 values, with 120 measured frames per trial.
The regression ceiling is 110% of V1 for both statistics.

| Workload | Median ms | p95 ms | Gate |
| --- | --- | --- | --- |
| plain / AA1 | 5.26 → 5.02 | 14.10 → 10.59 | Pass |
| plain / AA2 | 5.47 → 5.09 | 11.50 → 9.32 | Pass |
| ui / AA1 | 50.39 → 35.16 | 91.21 → 43.82 | Pass |
| ui / AA2 | 907.26 → 756.35 | 1593.92 → 845.32 | Pass |

These measurements establish a same-host nonregression gate. The large variation
in the original UI trials is visible in the raw samples; the lower candidate
frame timings should not be attributed to a renderer rewrite or extrapolated to
all workloads. There was no renderer rewrite. Reference initial import samples
before bytecode warm-up are also retained; acceptance uses the freshly remeasured,
warmed-bytecode V1 median to keep the import comparison fair.

Explicit native probes report EGL **Mesa llvmpipe**, OpenGL 4.5 / Mesa 25.2.8,
with `device="software"`. CAD and geometry probes both pass. Metadata-only calls
load none of those native engines; context creation happens only in explicit probes,
and the renderer probe closes its owned context. Hardware GPU throughput, fresh
native dependency resolution on other platforms, Python 3.13+, 4K certification,
long soak/export benchmarks and full narrated films remain unverified here.

### Evidence and local artifacts

Tracked records:

- [Acceptance numbers](m1-evidence/acceptance.json), [V1 raw samples](m1-evidence/baseline-benchmarks.json), [M1 raw samples](m1-evidence/candidate-benchmarks.json).
- [Wheel sizes and SHA-256](m1-evidence/wheels.json), [unchanged Core resources](m1-evidence/resources.json).
- [Fresh base-stack evidence](m1-evidence/base-stack.json), [metadata and explicit native probes](m1-evidence/probes.json).
- [Frozen API/image/font/backend reference](../../tests/fixtures/m1-v1-reference.json).

Generated local artifacts are under the git-ignored [output/v2-m1](../../output/v2-m1/):

- Final [Core](../../output/v2-m1/wheels/faceless_champ-0.1.6-py3-none-any.whl), [Kit](../../output/v2-m1/wheels/facelesschamp_kit-0.1.0rc7-py3-none-any.whl), and [Agent](../../output/v2-m1/wheels/facelesschamp_agent-0.1.0rc2-py3-none-any.whl) wheels.
- [Frozen V1 wheel](../../output/v2-m1/reference/faceless_champ-0.1.6-py3-none-any.whl), kept separately because its version is also 0.1.6.
- [Base still](../../output/v2-m1/base-still.png), [decoded ranged export](../../output/v2-m1/base-range.mp4), [Agent base frame](../../output/v2-m1/agent-base-frame.png).
- Source-suite logs/JUnit: [Core log](../../output/v2-m1/core.log) / [XML](../../output/v2-m1/core.xml), [Kit log](../../output/v2-m1/kit.log) / [XML](../../output/v2-m1/kit.xml), [Agent log](../../output/v2-m1/agent.log) / [XML](../../output/v2-m1/agent.xml); [wheel log](../../output/v2-m1/wheel.log) / [XML](../../output/v2-m1/wheel.xml).

Versions remain the existing local source-candidate versions. Reinstall the chosen
wheel when switching between V1 and M1; do not rely on an ordinary same-version
upgrade to distinguish them. Nothing was published or committed, and M2 remains
deferred pending its own authorization.
