# Optional Manim mathematical animation

Manim Community is an explicit preparation engine. FacelessChamp continues to
own the timeline, layouts, Pillow/Skia/ModernGL compositing, narration and FFmpeg
export. Existing `Equation`/`Write`, charts and geometry remain useful for simpler
scenes. No native engine is imported by API discovery or prepared playback.

## Installation

The tested adapter targets `manim>=0.22,<0.23`, Cairo and Python 3.12 on headless
Linux. Install `faceless-champ[manim]`, or the forwarding `facelesschamp-kit[manim]`
and `facelesschamp-agent[manim]` extras. Base Core still requires only Pillow.

For stronger dependency isolation, install Manim in a separate virtual environment
and pass its Python executable to preparation. That environment does not need
FacelessChamp. On Linux install Cairo/Pango development prerequisites as described
in the [Manim installation guide](https://docs.manim.community/en/stable/installation/uv.html).
Preparation also needs FFmpeg/ffprobe. `MathTex` scenes additionally need LaTeX,
`dvisvgm` and their TeX packages; geometric scenes need no TeX installation.
Nothing installs packages automatically.

## Core authoring

```python
from faceless_champ import Canvas, Scene, Viewport
from faceless_champ.integrations.manim import (
    ManimRenderOptions, ManimSceneSpec, load_manim, prepare_manim,
)

spec = ManimSceneSpec("lesson.py", "Lesson", inputs=("helper.py",),
                      parameters={"radius": 2})
options = ManimRenderOptions(width=640, height=360, fps=15, seed=0)
frames = prepare_manim(spec, cache_dir="output/math-cache", options=options,
                       python="/path/to/manim-env/bin/python")
# On later runs, load without probing or executing the producer environment:
frames = load_manim(spec, cache_dir="output/math-cache", options=options,
                    python="/path/to/manim-env/bin/python")
view = Viewport(frames, width=640, height=360, position=(320, 180))
scene = Scene(Canvas(640, 360, "#172235")).add(view).wait(frames.duration)
```

The source file defines a standard no-argument Manim `Scene` subclass. Read JSON
parameters from `self.faceless_parameters` in `setup()` or `construct()`. The
entrypoint and explicit `inputs` are staged with their relative paths; include
helpers, local fonts, assets and custom TeX templates. `source_root` defaults to
the source file's parent. Inputs cannot escape that root. Ordinary absolute
Python imports of staged helpers work; package-relative entrypoint imports are
not an additional module-loader feature.

`quality` accepts `low_quality` (the default), `medium_quality`, `high_quality` or
`fourk_quality`. Supply width and height together. Explicit dimensions/FPS override
the preset. `background=None` requests transparency; a supplied color is opaque.
The actual movie must match the requested profile. Source and export resolution
are independent: scaling a prepared viewport never launches a higher-quality
Manim render. Reprepare explicitly when more source detail is required.

## Media and time

The worker imports Manim, resets ambient Manim configuration, applies the request
and calls public `Scene.render()` under `tempconfig`. It uses Cairo, no window,
and a single bounded encoder queue. Preparation writes lossless QTRLE/ARGB MOV,
then FFmpeg extracts RGBA PNGs without changing frame rate. This avoids the 0.22
PNG writer's frozen-wait repeat issue without patching Manim internals. Embedded
audio is rejected; add narration with FacelessChamp.

`PreparedFrameSource(directory)` verifies a versioned manifest and every frame's
hash, PNG format and dimensions. It implements `RasterSource`, declares no native
requirements, and decodes frames on demand with Pillow. Existing renderer-owned
byte caches retain frames; the descriptor contains no native objects or handles.
Keep published assets immutable. Sessions return independent straight-alpha RGBA
images, preserving aspect ratio with transparent margins when necessary.

`Viewport` supplies normal component transforms, masks, effects and source offsets.
Adding it does not advance scene time. Frame selection uses source time; shorter
placements trim playback and longer placements hold the last frame. The terminal
boundary clamps to the last frame. Arbitrary-order seeking is supported. Different
export FPS repeat/drop source frames without stretching time. The current final
export remains opaque H.264 MP4; alpha is preserved in prepared media and composition.

## Cache, limits and failures

Preparation identity includes declared input contents, parameters, settings,
interpreter path, producer package/native/tool versions and adapter code identity.
Frame hashes and provenance determine the published asset fingerprint. Warm preparation probes
the producer but skips rendering and normalization when identity matches.
`load_manim` does not probe; a missing producer environment does not prevent replay.
Declared input changes require preparation again. Cross-machine pixel identity is
not promised; declare custom fonts/templates and pin the toolchain. Hidden inputs,
network calls and environment-dependent user code cannot be discovered automatically.

Same-request preparation is serialized with a POSIX file lock. Staging and atomic
references prevent partial publication; refresh creates an immutable content
generation. Failures preserve the previous reference. Published assets are never
automatically evicted; remove old caches explicitly when they are no longer used.

`timeout=600`, `output_limit=2*1024**3` and optional `cancel()` bound a job. The
output limit covers staging/intermediates and logs; logs are additionally limited
to 8 MiB. Budget polling is not a hard filesystem quota. Cancellation raises
`concurrent.futures.CancelledError`; other failures use `ManimError.code` and
`details` (including a retained log path). POSIX process groups are terminated and
reaped on failure. Native RSS is not a byte-cache budget; use external container
limits where hard process-memory limits are needed. Preparation is POSIX-only in
this MVP; prepared playback uses portable Python/Pillow.

`manim_capabilities()` returns static support and local distribution metadata.
`manim_capabilities(python=..., probe=True)` explicitly tests the selected runtime.
Neither imports Manim in the parent process. No performance improvement is claimed;
measure cold/warm preparation, disk bytes, peak RSS and playback separately.

## Docker and verification

Docker is optional. Run preparation commands inside a version-pinned image
containing the supported Manim release, FFmpeg, Cairo and needed TeX packages;
install Core/Kit there and mount a writable project/output directory. Use your
UID/GID and explicit CPU/memory limits. There is no automatic image pull or managed
Docker runner. A copied asset directory can be loaded on the host directly with
`PreparedFrameSource`; request references retain the preparing interpreter identity.
See [Manim's Docker guide](https://docs.manim.community/en/stable/installation/docker.html).

Run the opt-in native tests with `FC_MANIM_PYTHON=/path/to/python`; set
`FC_MANIM_TEX=1` when LaTeX/dvisvgm are also available on the worker PATH. Unit
tests require no Manim. See the [Kit guide](../kit/manim.md)
for the six-second POC and explicit project preparation workflow.

The MVP has been exercised on native headless Linux with a separate Manim 0.22.0
environment: transparent and opaque geometry, frozen holds, the six-second
equation transformation, arbitrary seeking, and full MP4 decode. Inspected
equation frames are committed as tolerant visual regression references. Base
wheel checks run with only Core and Pillow installed. The optional GitHub Actions
workflow and Docker execution have not been run locally; no low-memory hardware
certification or cross-machine pixel determinism is claimed.
