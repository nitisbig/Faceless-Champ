# ADR: Optional ModernGL rendering and effects

Status: implemented experimental first release; hardware certification pending.

Ownership remains Project → Agent → Kit → Core. ModernGL implements the existing
validate/frame renderer protocol and returns independent straight RGBA Pillow
images. Pillow remains the default; CPU Skia and custom renderers retain their
existing interfaces. No GPU handles enter component snapshots or animation tracks.

The compositor consumes shared source-clock composition placements and affine
geometry. GPU child scenes remain textures until the final readback. Specialist
leaves retain their existing raster producers, including renderer-owned VTK
sessions. ModernGL explicitly rebinds its context after raster work. VTK windows
run in a renderer-owned private interpreter because their EGL display lifecycle
can invalidate another engine's contexts in the same process. The worker reuses
the existing raster producer and bounded session cache, and closes with its owner. GPU rendering
does not imply GPU encoding or zero-copy VTK integration.

Explicit moderngl selection either works or reports an actionable error. The new
auto selector chooses a compatible hardware ModernGL renderer, then Skia, then
Pillow; software OpenGL is skipped by auto. Selection is fixed for the session.
Required operations are never omitted. Runtime failures abort atomic export rather
than changing its appearance midway.

Effects use immutable descriptors and the existing property tracks. Content
filters precede own masks/wipes. Halos and the existing leaf shadow derive from
the masked content; ancestor masks clip the completed layer. Group opacity still
attenuates each member before group filtering. Group shadows remain unsupported.
This resolves the unimplemented Phase 2B reservations in the earlier premium
effects ADR; its legacy baked surface compatibility decisions remain intact.

Legacy gradients and crossfades retain encoded-sRGB semantics. New filters and
luminous effects use linear-light floating-point working values. Bloom uses a
three-scale pyramid; wide Gaussian kernels use a bounded resolution pyramid.
These are shared CPU/GPU algorithms, not silent quality reductions on fallback.
All exports remain SDR; the existing MP4 path is opaque H.264.

Contexts are renderer-owned and thread-affine. Target pools, texture caches,
readback staging, particle buffers and frame caches are renderer-scoped. GL
resources release explicitly on eviction/close; allocations are checked against
device limits and configured budgets. External decoders, VTK, driver allocations
and CPU reference scratch are separate memory consumers.

Offline identity describes requested configuration. Runtime identity records the
actual renderer, driver, software/hardware device and shader hash. Agent reviews
cannot qualify another resolved backend or changed GPU pipeline. Discovery never
opens a GL context; doctor --gpu is the explicit probe.

Native mesh rendering and custom GLSL authoring remain subsequent releases.
ArchChamp continues to supply scientific 3D with GPU compositing/effects around
its raster viewport. First-release acceleration claims require hardware evidence.
