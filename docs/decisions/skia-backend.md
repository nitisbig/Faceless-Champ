# ADR: Optional CPU Skia backend

Accepted implementation: preserve Project → Agent → Kit → Core ownership and the
two-method Renderer protocol. Core selects an explicit CPU backend; Pillow stays
the default and no automatic backend substitution occurs.

Core owns renderer-neutral paths/paints/surfaces, native measurement, compositing,
cache lifetimes and raster adapters. Kit owns profile configuration, themes and
layout/effect diagnostics. Agent owns capability discovery, design intent and
backend-specific evidence. Existing animation/timeline/FFmpeg/audio semantics stay
shared. Optional native imports occur only on selection or native text measurement.

SkiaRenderer composes native leaves directly. Existing specialist raster producers
remain behind one adapter, including renderer-owned Arch sessions. Shared composition
helpers preserve fitting, source clocks and straight-RGBA crossfades. Premultiplied
internal Skia pixels cross the public boundary as independent straight RGBA images.

Native text is opt-in and measured by its drawing engine. Retained surfaces are
opt-in through existing factory names. Existing Image-returning factories and
Pillow output remain the compatibility contract. Backend versions and font hashes
participate in Kit/Agent build evidence; reviews cannot certify a different backend.

Local masks and effects have explicit guarded allocations, not canvas-sized layers
per leaf. Byte-bounded renderer caches and bounded font/layout counts release on
close. The legacy Pillow affine path remains available with its documented costs.
Skia cache budgets do not imply a bound on all external decoders or OS allocator RSS.

The portable subset has functional Pillow fallbacks; native typography, compound
path fills and path masks require Skia. Native raster differences are intentional
only after backend/capability opt-in. Cross-platform bitwise native output and GPU
acceleration are not v1 guarantees. See [the usage guide](../skia.md).
