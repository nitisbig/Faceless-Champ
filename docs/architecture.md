# Architecture

The engine separates authoring from rasterization and encoding:

1. Components describe static visual properties in design pixels.
2. Scene construction snapshots components and records per-property animation tracks.
3. Timeline evaluation computes state at arbitrary times without modifying components.
4. Sequence, Grid, and Layer map global time and bounds into their child compositions.
5. PillowRenderer rasterizes and composites one frame at a time.
6. Export streams RGB frames to FFmpeg and builds an audio graph from leaf clips.

Sequence start times derive from current durations. Audio placements are collected
recursively with global offsets and ancestor crossfade envelopes. FFmpeg trims and
resamples clips, applies local fades, delays them, applies composition fades, mixes,
pads, and encodes. Sample-based timestamp normalization after delay avoids invalid
timestamps from FFmpeg 6.1's inserted silence.

Grid padding defines the cell region; each child has an optional start offset that
shifts both visuals and audio. Layer composites fitted children in order, retaining
transparent child backgrounds. Neither composition changes scene authoring tracks.

`Renderer` is a protocol with `validate(node)` and
`frame(node, time, size) -> PIL.Image.Image`. A replacement renderer must return the
requested dimensions, support deterministic frame sampling, and validate supported
node/component types. Pass it with `render(..., renderer=custom_renderer)`.
The current exporter still owns FFmpeg, audio, and output publication.

`Animation(component, targets, starts=None, keyframes=None, relative=(),
rate_func=None)` represents property interpolation.
Built-in properties are position, scale, rotation, opacity, reveal, and draw.
Keyframe tracks interpolate within normalized segments and use exact endpoints.
Relative transforms resolve against the component's evaluated state at scheduling
time: position/rotation offsets and scale multipliers. Play calls prepare and
validate every track before mutating the scene. Presets use this same track model;
the renderer needs no animation-specific logic.
A custom easing function must be deterministic. The base Component and renderer
protocol provide extension points; adding a new visual type requires a renderer
that understands it. v0.1 does not have a global plugin registry.

The renderer caches font instances, decoded image/GIF assets, and static sprites
per renderer instance. Dynamic typewriter and outline frames are not retained.
It also keeps the last rendered frame per scene within a configurable 64 MiB LRU
budget. Evaluated visible component states determine reuse, so holds avoid repeated
rasterization; GIF and caption ages invalidate dynamic content. Canvas, resolution,
lifetimes, and new visuals also invalidate the cache. Returned images are independent
copies. `PillowRenderer(frame_cache_mb=0)` disables the scene-frame cache.
Equation sprites are cached by expression, fontset, color, symbol color map, font
size, width limit, and render scale. Write masks those sprites without reparsing
partial TeX. Colored formulas use MathText's complete vector layout and rasterize
the positioned glyph outlines with their assigned colors; fraction/radical bars
retain the base color. The optional MathText parser loads only when rendering an
Equation. Variable font caches include weight, so separately weighted text does
not share mutable variation settings. ColorScheme contains validated, immutable
visual roles and adds no dependency beyond Pillow.
Caption sprites are cached by phrase and active cue, so caption memory depends on
the number of distinct cue states as well as output resolution. GIFs decode all
frames into memory. Video frames themselves are streamed to the encoder.

`SubtitleTrack` stores immutable, nonoverlapping SRT cues and uses binary search
for active-cue lookup. Captions evaluate against component age; nested compositions
therefore apply their normal time offsets without changing subtitle timestamps.
`Scene.at()` changes the authoring cursor temporarily and preserves the furthest
time reached. Tracks on each component property remain chronological. Entry end
times allow removed objects to be skipped, including during out-of-order sampling.

Export uses a temporary directory beside the output. Explicit overwrite uses atomic
replacement; default publication uses an exclusive hard link to avoid a race that
could overwrite a file created while rendering. This requires a filesystem with
hard-link support. Source media is never modified.

Image components may carry encoded source bytes instead of a path. Renderer asset
keys use resolved paths or immutable encoded bytes; scene-frame signatures include
age for any decoded multi-frame image, including GIF bytes without a file suffix.
Trimming uses the union of frame alpha bounds, and tinting preserves source alpha.
Polyline x-based reveal measures horizontal segment extent instead of arc length,
so one cached source geometry can follow a shared chart time cursor.
