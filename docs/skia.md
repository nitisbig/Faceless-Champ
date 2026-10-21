# Optional Skia rendering

Skia is an opt-in CPU renderer for native geometry, Bézier paths, shaped text,
retained surfaces, gradients, masks and leaf shadows. Pillow remains the default.
All renderers share the existing scene snapshots, animation tracks, Spring easing,
layouts, composition timing, source-clock previews, audio and FFmpeg exporter.

## Install and select

```bash
python -m pip install 'faceless-champ[skia]'
# Or from this checkout:
python -m pip install -e '.[skia]' -e './facelesschamp-kit[skia]' -e './facelesschamp-agent[skia]'
```

The supported native binding is `skia-python>=144.0.post2,<145`. Linux needs
`libfontconfig1`, `libgl1`, and `libegl1` even for CPU raster surfaces. A display,
GPU context, browser, network connection, or system font search is not required.
The wheel baseline is glibc 2.28; use a glibc-based image, not Alpine/musl.

```python
from faceless_champ import ExportSettings, render, save_frame

render(scene, "native.mp4", settings=ExportSettings(backend="skia", antialias=1))
save_frame(scene, 1.0, "native.png", backend="skia")
```

`antialias` still means supersampling (1–4). Native geometry already has edge
antialiasing at 1; use that for 1080p/4K. The legacy export default remains 2.
An unavailable explicitly requested backend raises an actionable error. It never
silently substitutes Pillow. Importing the library does not import Skia/NumPy.
`renderer=custom` remains authoritative and caller-owned; factory-created
renderers are closed on success and failure.

## Geometry, paint and typography

```python
from faceless_champ import Bounds, GradientStop, LinearGradient, PathData, VectorPath, ShadowStyle, Text, card_surface, fit_text

path = PathData().move_to(100, 200).cubic_to(220, 40, 350, 340, 500, 180)
curve = VectorPath(path, stroke="#567CF4", stroke_width=4)
paint = LinearGradient((GradientStop(0, "#5260EF"), GradientStop(1, "#8ED8EA")), angle=30)
card = card_surface(Bounds(40, 40, 800, 520), fill=paint, radius=28,
                    shadow=ShadowStyle(blur=10), render_mode="vector")
title = fit_text("Measured native type", Bounds(140, 140, 690, 260),
                 font_size=48, text_engine="skia")
```

Path commands are immutable absolute M/L/Q/C/Z tuples. Fluent methods return a
new PathData. VectorPath normalizes into its analytic tight bounds, with placement
and transforms following Polyline. It supports Draw by arc length; closed fills
appear when drawing completes. Compound contours and `even_odd` fills require Skia.
PathMask uses normalized [0,1] PathData and also requires Skia.

Existing solid Shape fills remain animatable. Shape fills can additionally use
the existing immutable linear/radial paints. Gradient stops and stroke gradients
are not animatable/supported in v1. Gradient descriptors retain clockwise angles,
normalized radial center, radius relative to the shorter face side, clamping and
premultiplied encoded-sRGB interpolation. Native samples use pixel centers, so
native raster edges/stop samples need not equal baked Pillow pixels exactly.

`card_surface`, `gradient_surface`, and `dot_grid` retain their Image return value
by default. `render_mode="vector"` returns a Surface description and rasterizes
at the current output/transform scale. Card allocations still include shadow
clearance; `card_content_bounds` retains the same inset convention. The face
replaces the surface shadow even when its fill is transparent. Existing baked
cards, including their historical colored-shadow behavior, are unchanged.

Text uses Pillow by default even with a Skia compositor. `text_engine="skia"`
opts into paragraph shaping and the same engine's bounds/fitting. It supports
explicit font files, variable weights, multiline spacing, alignment, color,
Number, and Typewriter's existing code-point reveal clock. Reveal reserves the
full text box. Native font files are explicitly registered; missing glyphs raise
an error instead of consulting machine-dependent fallback fonts. Supply fonts
covering the authored script. Native paragraph caches are renderer-owned.

## Compositing and compatibility

Native primitives: Rectangle/Square, Circle/Ellipse, Triangle, Line, Arrow,
Polyline, VectorPath, retained Surface and opt-in native Text/Number.
Charts, maps, MathText equations, captions, CodingChamp, FlowChamp, browser/OS/
chess/prepared clips, and ArchChamp use their existing raster producers. Their
finished RGBA images are composited by Skia. FlowDesign and CodeWindow groups can
opt into native surfaces/type; this does not rewrite specialist clip internals.
The ArchChamp raster handoff preserves the caller's floating-point environment
where the host exposes C99 environment functions. This prevents VTK capped
clipping from disrupting subsequent native Skia curves or text on affected hosts.

Masks clip a completed subtree once. Group opacity still multiplies each member;
it is not applied once to the finished group image. Sibling stacking, inherited
transforms, masks/wipes, clip ages and composition crossfade rules are preserved.

Leaf components accept `shadow=ShadowStyle(...)`. Effect state is stored as
`drop_shadow` to preserve CodeWindow's existing `.shadow` visual child. A leaf's
own mask/wipe is applied before casting its shadow; ancestor masks clip the final
content and shadow. Skia casts shadows in local design space before transforms.
Pillow provides a functional device-space fallback for leaf shadows; under
nonuniform transforms it is not pixel-identical to Skia. Group shadows are rejected.
`Scene.ink_bounds_at()` expands conservative effect bounds while `bounds_at()`
keeps logical layout bounds. Kit/Agent use ink bounds for canvas clipping checks.

Pillow also renders retained surfaces, gradients and one-contour winding Bézier
paths using adaptive flattening. Native text, compound fills, and PathMask fail
preflight with a capability error when Pillow is selected.

## Memory, determinism and verification

SkiaRenderer defaults: 64 MiB frame cache, 64 MiB native image cache, 256 MiB local
surface working budget; font/paragraph caches have count limits. Raster adapter
sprite/image/equation retention is separately bounded and Arch sessions close on
eviction/close. Decoding a single large source can still require transient memory.
Allocation guards reject sides over 16384 or surfaces over 33,554,432 pixels.
Group masks allocate explicit local surfaces; saveLayer hints are not memory guards.

No Skia handles enter scene snapshots. Repeated/out-of-order source-time samples
are deterministic with fixed library versions, CPU platform and fonts. Record
`rendering_identity("skia", scene)` for backend, dependency versions, font hashes
and native opt-ins. Cross-platform byte-identical glyph pixels are not promised.
MP4 remains opaque H.264/YUV420. `save_frame` retains its existing RGB still
behavior. For alpha inspection, save the renderer's RGBA frame directly:

```python
from faceless_champ import create_renderer

with create_renderer("skia", antialias=1) as renderer:
    renderer.frame(scene, 1.0, (1920, 1080)).save("rgba-frame.png")
```

```bash
python examples/skia_showcase.py --output output/skia/preview.mp4
python examples/skia_showcase.py --frame --quality 4k
python scripts/benchmark_renderers.py --output output/skia/benchmarks.json
```

The benchmark uses fresh processes, three trials, 24 warm frames at 1080p and
eight at 4K, after three warm-up frames. It reports construction/cold/warm time,
median/p95, RSS, caches and native raster/readback counters. FFmpeg is excluded;
measure preview export separately. `--baseline-ref HEAD` adds the previous Pillow
renderer for legacy workloads. A Pillow regression exceeding max(10%, 0.5 ms/frame)
requires investigation. No realtime 4K guarantee is implied by a 30 FPS export.

GPU, SVG DOM import, path morphing, animated paint stops, group shadows and
backdrop blur remain outside v1. See [the architecture decision](decisions/skia-backend.md)
and [verification evidence and limits](skia-verification.md).
