# Architecture

The engine separates authoring from rasterization and encoding:

1. Components describe static visual properties in design pixels.
2. Scene construction snapshots components and records per-property animation tracks.
3. Timeline evaluation computes state at arbitrary times without modifying components.
4. Sequence and Grid map global time and bounds into their child compositions.
5. PillowRenderer rasterizes and composites one frame at a time.
6. Export streams RGB frames to FFmpeg and builds an audio graph from leaf clips.

Sequence start times derive from current durations. Audio placements are collected
recursively with global offsets and ancestor crossfade envelopes. FFmpeg trims and
resamples clips, applies local fades, delays them, applies composition fades, mixes,
pads, and encodes. Sample-based timestamp normalization after delay avoids invalid
timestamps from FFmpeg 6.1's inserted silence.

`Renderer` is a protocol with `validate(node)` and
`frame(node, time, size) -> PIL.Image.Image`. A replacement renderer must return the
requested dimensions, support deterministic frame sampling, and validate supported
node/component types. Pass it with `render(..., renderer=custom_renderer)`.
The current exporter still owns FFmpeg, audio, and output publication.

`Animation(component, targets, starts=None)` represents property interpolation.
Built-in properties are position, scale, rotation, opacity, reveal, and draw.
A custom easing function must be deterministic. The base Component and renderer
protocol provide extension points; adding a new visual type requires a renderer
that understands it. v0.1 does not have a global plugin registry.

The renderer caches font instances, decoded image/GIF assets, and static sprites
per renderer instance. Dynamic typewriter and outline frames are not retained.
Memory therefore depends on source assets and current frame dimensions, not video
length; decoding all frames of a large GIF is a known exception.

Export uses a temporary directory beside the output. Explicit overwrite uses atomic
replacement; default publication uses an exclusive hard link to avoid a race that
could overwrite a file created while rendering. This requires a filesystem with
hard-link support. Source media is never modified.
