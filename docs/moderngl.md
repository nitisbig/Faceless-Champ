# Optional ModernGL renderer

ModernGL is an optional headless compositor for existing scenes, components,
animations, timelines, and ArchChamp viewports. It adds GPU effects, procedural
backgrounds, instanced particles and transitions. Pillow remains the default.

```bash
python -m pip install 'faceless-champ[gpu]'
# Native Skia typography/compound paths additionally need the existing extra:
python -m pip install 'faceless-champ[gpu,skia]'
fc-kit --json doctor --gpu
fc-agent doctor --gpu --json
```

Python 3.12+, ModernGL 5.13+, glcontext 3.1+ and OpenGL 3.3+ are the baseline.
Linux uses EGL without a display server. Install/provide system EGL/OpenGL drivers
and pass the appropriate render devices into containers. Python packages do not
install graphics drivers. NVIDIA environments need graphics-capable EGL driver
access in addition to compute access. Software Mesa is useful for correctness,
but it is not evidence of GPU acceleration. Windows/macOS native standalone
contexts remain outside the first hardware certification matrix.

## Selection and ownership

```python
from faceless_champ import ExportSettings, GPUOptions, render

render(scene, "gpu.mp4", settings=ExportSettings(
    backend="moderngl", antialias=1,
    gpu=GPUOptions(working_mb=512, texture_cache_mb=256),
))
```

Use `backend="auto"` to select hardware ModernGL, then compatible CPU Skia or
Pillow. Explicit `moderngl` may use software OpenGL and records that fact. Auto
skips software OpenGL. Missing required features fail preflight; fallback never
omits effects or changes particle counts, resolution, FPS or AA. Runtime resource
failures abort the export and preserve existing output files.

`antialias` retains its supersampling meaning (1–4). Native primitive edges have
analytic antialiasing, so 1 is the recommended GPU profile value. Large AA/scale
combinations may exceed budgets and fail explicitly. The legacy default stays 2.

Renderers created by helpers close on success/failure. Supplied renderers remain
caller-owned. Use and close a ModernGLRenderer on its creating thread. Each owns
its context, programs, caches and local targets; GPU objects are not global or
snapshotted into scenes. ArchChamp windows run in a renderer-owned private
interpreter to isolate VTK's EGL display lifecycle. Geometry is sent once while
resident and subsequent frames transfer RGBA pixels; the existing bounded VTK
session cache and source clocks are preserved. The worker closes with the GPU
renderer and never re-executes a project entrypoint.

## Local effects and animation

```python
from faceless_champ import (
    Bloom, Canvas, Circle, EffectStack, GaussianBlur, Layer,
    OuterGlow, Scene, linear,
)

orb = Circle(90, fill="#9DE1FF", stroke=None, position=(480, 270),
             effects=EffectStack(glow=OuterGlow("#55AEFF", 20, 0.7)))
scene = Scene(Canvas(960, 540, "#091225")).add(orb)
scene.play(orb.animate.effect_to("glow", radius=32, intensity=1),
           run_time=2, rate_func=linear)
video = Layer(scene, effects=EffectStack(bloom=Bloom(radius=12, threshold=0.5)))
```

EffectStack has fixed optional slots: `blur`, `glow`, `bloom`, `distortion`,
`chromatic` and `light_sweep`. Attach it to leaves, groups, or Layer. The latter
provides composition-wide effects. Numeric parameters animate through existing
tracks; effect topology and colors remain static. Spring retains its existing
transform-only restrictions.

Effects run in local space: light sweep, distortion, chromatic separation, blur,
then own mask/wipe, then glow/bloom and the existing leaf shadow. Halos may extend
outside the leaf mask; ancestor masks clip the final result. Group opacity is
applied per member, preserving existing overlap behavior; it is not reapplied to
the finished group. Group shadows are still rejected. `bounds_at` remains logical;
`ink_bounds_at` includes evaluated effect padding.

CPU equivalents are available through `[effects]` without ModernGL. GPU `[gpu]`
includes their NumPy dependency for fallback. Source geometry/typography can have
documented backend raster differences. New filters use linear-light premultiplied
values and preserve colored transparent edges. Legacy gradients and crossfades
keep their existing encoded-sRGB conventions. Wide Gaussian filters use the same
bounded downsample/convolve/upsample algorithm on CPU and GPU. Bloom combines
three scales. Neither floating-point working targets nor bloom imply HDR export.

## Procedural motion and transitions

```python
from faceless_champ import ProceduralBackground, ParticleField, Sequence, DirectionalWipe

background = ProceduralBackground("aurora", width=1920, height=1080,
                                  position=(960, 540), seed=17)
particles = ParticleField(width=1920, height=1080, position=(960, 540),
                          seed=17, count=10000, color="#A2DEFF")
video = Sequence(first_scene, second_scene, crossfade=0.6,
                 transition=DirectionalWipe(softness=0.08))
```

Background kinds are `aurora` and `noise_gradient`. ParticleField uses seed-indexed
float32 instance records and GPU instancing. State depends only on source age,
not evaluation order or FPS. Positions/opacity are evaluated analytically on CPU;
particle drawing and transforms are batched on GPU. There is no hidden physics
simulation or frame history. `frame_key` includes source age.

Transitions are DirectionalWipe, LuminanceWipe and ZoomBlurTransition. Existing
Sequence.crossfade still controls overlap and audio envelopes. With transition=None
the historical straight-RGBA crossfade remains unchanged. Transitions have exact
endpoints and require a positive overlap.

## Kit and Agent

```toml
[profiles.preview]
backend = "auto"
antialias = 1

[profiles.final]
backend = "moderngl"
antialias = 1

[profiles.final.gpu]
context_backend = "egl"
working_mb = 512
texture_cache_mb = 256
frame_cache_mb = 64
```

Install `facelesschamp-kit[gpu]` or `facelesschamp-agent[gpu]` for forwarded
dependencies. EffectBlock wraps a normal Kit block and preserves named children;
ProceduralBackdrop and ParticleBackdrop use theme color and build seed. Rendering
and effects stay in Core. Existing preparation boundaries do not change.

`renderer_capabilities(probe=False)` and Agent discovery do not import GL or open
contexts. An explicit probe records availability, driver and software/hardware
status. `rendering_identity(..., renderer=renderer)` records actual execution;
without a renderer, GPU identity remains unresolved. Kit/Agent export and preview
records use actual identities. GPU review qualification includes shader hash,
driver, device renderer and color pipeline, so auto fallback cannot masquerade as
GPU evidence. Review/status resolve the final GPU/auto profile before qualification.

## Performance and verification

```bash
python examples/moderngl_showcase.py --frame --quality 4k
python examples/moderngl_showcase.py --seconds 1 --fps 12
python scripts/benchmark_renderers.py --backends moderngl --workloads ui bloom layers --trials 1 --output output/moderngl/benchmark.json
python scripts/benchmark_renderers.py --backends pillow skia moderngl --workloads layers bloom --certify --output output/moderngl/certification.json
```

The normal quick matrix is retained. Certification uses three fresh-process
trials, ten warm-ups and 120 measured samples, keeping animated sample times
inside their authored intervals. Reports distinguish device type, cold/warm
latency, p95, CPU RSS, cache bytes, transfers and GPU resource accounting. Frame
timings include final readback and exclude FFmpeg; measure exports separately.
There is no realtime 4K promise and no hardware speedup claim from llvmpipe.

GPU caches default to 256 MiB textures, 512 MiB working targets and 64 MiB frames.
These are separate budgets. External raster decoders, VTK, CPU effect scratch and
driver allocations consume additional memory. Returned RGBA frames are independent
copies. Save renderer.frame(...).save("alpha.png") for alpha inspection; existing
save_frame/storyboard helpers remain RGB and MP4 remains opaque H.264.

See the architecture decision and `moderngl-verification.md` for actual evidence
and remaining certification work. Native mesh viewports and public custom GLSL
remain subsequent releases; ArchChamp scientific 3D is preserved.
