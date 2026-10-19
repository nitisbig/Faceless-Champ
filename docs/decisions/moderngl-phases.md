# ModernGL integration phases

The first release is implemented behind an optional backend. Hardware performance
certification is still open; see [verification](../moderngl-verification.md).
Pillow is still the default, and existing CPU Skia routes remain available.

| Phase | Implementation | Independent verification |
| --- | --- | --- |
| 0: contracts and baseline | `gpu.py`, `GPUOptions`, lazy capability discovery; optional `gpu` and `effects` extras in Core, Kit and Agent | Import with native dependencies blocked; existing package suites |
| 1: renderer lifecycle | `backends/moderngl.py`, `backends/_gl/device.py`, `backends/_auto.py`; owned EGL context, budgets, target pool, texture/frame caches and final readback | RGBA orientation, alpha, cache ownership, resource failure, actual fallback identity |
| 2: composition | `_composition_plan.py`, `_compositor.py`, `_cpu_device.py`; shared source times and local isolation, retained specialist raster producers | Nested Sequence/Grid/Layer with one final GPU readback, masks, member opacity, shadow/glow interaction |
| 3: effects | `effects.py`, `_effects_cpu.py`, packaged GLSL; immutable descriptors, existing animation tracks, linear-light blur, glow, bloom, distortion, chromatic aberration and light sweep | CPU/GPU numerical comparisons, composited SSIM, animated ink bounds and random seeks |
| 4: cinematic motion | `procedural.py`, `transitions.py`; seeded backgrounds, instanced particles, overlap transitions | Seek determinism, independent particle clock, transition agreement and exact endpoints |
| 5: Kit and Agent | Kit `blocks/effects.py`, nested GPU profile settings, runtime export identity; Agent discovery, explicit doctor probe and review qualification | Separate Kit/Agent suites; public block discovery and rejection of mismatched render evidence |
| 6: delivery and evidence | Example entrypoint, extended renderer benchmark matrix, user guide and packaged shader resources | Local wheel/sdist builds, installed-wheel smoke, 1080p encoded preview and inspected 4K still |

Core owns graphics, effects and renderer resources. Kit wraps existing blocks and
profiles. Agent discovers capabilities and assesses evidence. No package above
Core owns a second shader engine or effect implementation.

The existing VTK raster producer continues to own scientific 3D. A private,
renderer-owned interpreter isolates its EGL display lifecycle from ModernGL;
this preserves the existing source clock and bounded VTK sessions. Its regression
test verifies that VTK initialization and shutdown leave GPU overlays usable.

## Remaining certification

Run the certification matrix on hardware EGL with recorded GPU/driver identity,
three fresh processes, ten warm-up frames and 120 samples per workload at 1080p
and 4K. Include layers, bloom, particles, backgrounds, transitions, source assets,
alpha edges and typography. Compare equal resolution, FPS and AA; retain p95,
RSS, transfer counts, GPU timings, cache usage and quality checks. Time encoded
exports separately. Software Mesa results cannot satisfy hardware speed gates.

Docker verification is deferred at the user's request. The optional recipe is
provided, but no successful container build or container execution is claimed.

Native mesh viewports and public custom GLSL are subsequent releases. Their
interfaces should build on the same owned devices, immutable authoring state,
source clocks, effect stack and final RGBA boundary rather than replacing
ArchChamp or adding a second timeline.
