# v0.1 verification

Verified on Linux on 2026-10-03 with Python 3.12.3, Pillow 12.3.0, and FFmpeg 6.1.1.

- **28 pytest cases passed**, covering deterministic animation, snapshots, conflicts,
  invalid inputs, shape drawing, GIF timing, alpha, JPEG/WebP, clipping, sequence
  timing, resolution settings, WAV/MP3/M4A, audio trims/offsets/mixing/fades,
  nested crossfade audio, CLI behavior, overwrite protection, missing FFmpeg, and
  cleanup after encoder failure.
- Ruff lint and formatting checks passed for source, examples, and tests.
- The project-local authoring skill passed the skill-creator validator.
- Source distribution and wheel built successfully. The wheel includes the default
  font and license. A clean temporary environment imported the installed wheel,
  rendered text using the bundled font, and ran the installed CLI.

| Export | Resolution | FPS | Duration | Streams |
| --- | --- | --- | --- | --- |
| `animated_title.mp4` | 1280×720 | 30 | 4.4 s | H.264 |
| `media_sequence.mp4` | 1280×720 | 30 | 5.4 s | H.264 + AAC |
| `six_panel_canvas.mp4` | 1280×720 | 30 | 3.5 s | H.264 |
| `resolution_qh.mp4` | 1920×1080 | 30 | 0.1 s | H.264 |
| `resolution_qk.mp4` | 3840×2160 | 30 | 0.1 s | H.264 |

All exports passed full FFmpeg decoding and ffprobe checks for resolution, codec,
frame rate, and duration. Representative decoded frames were inspected for text,
layout, clipping, transparency, and transition state. The six-panel example uses
panel proportions matched to its grid cells.

Decoded media-sequence audio measured RMS 0.000 before the scheduled clip,
approximately 0.045 during it, and 0.000 after it. Integration tests separately
checked fade levels, mixing amplitude, compressed input formats, and nested
composition timing. These are signal measurements, not a subjective listening review.

Artifacts and preview PNGs are in `output/`, which is ignored by Git. Run
`uv run python examples/render_all.py` to regenerate them and `output/verification.json`.
The 4K test confirms a short export; it is not a long-video performance benchmark.

## Good-math additions

Verified on 2026-10-03 after adding SRT cues, captions, absolute scene timing,
component lifetimes, tintable icons, and drawable arrows:

- **49 pytest cases passed**. Added coverage includes SRT boundary/gap handling,
  BOM/CRLF/multiline inputs, invalid cues, phrase limits, caption wrapping and
  highlighting, composition offsets, out-of-order rendering, timed lifetimes,
  temporal animation conflicts, icon alpha/tint, and arrow drawing.
- Ruff lint/format checks passed for source, tests, examples, and good-math scripts.
- The complete narrated preview exported as 1280×720 H.264 at 24 fps with AAC,
  starting at zero, for 60.208333 seconds (the 60.2-second scene rounded to a frame).
- The 12-frame storyboard and decoded preview frames were inspected for spacing,
  typography, arrows, and caption placement. A 1920×1080 frame was rendered from
  a different working directory to check path independence and supersampling.
- Comparing decoded source/export audio from 1–2 seconds gave correlation 0.999726
  and exported narration RMS 0.232559, confirming preserved narration alignment.
  The preview includes a short final hold after narration ends.

Run `uv run python 'training project/good-math/render.py' --preview --overwrite`
to regenerate the preview, or `--frames` to regenerate the storyboard in the
project's `output/` folder. The downloaded asset licenses and source/checksum
manifest are in the shared `assets/` folder. Wheel/distribution checks above
describe the original v0.1 baseline; those were not repeated for these additions.

## Motion presets

Verified on 2026-10-03 after adding 11 motion presets and keyframe/relative tracks:

- **89 pytest cases passed**. New coverage includes nondefault transforms, pop
  overshoot, bounded opacity, all slide directions, exits after earlier transforms,
  repeated emphasis without drift, bounce/spin intermediate values, easing
  overrides, invalid keyframes, atomic rejection, and absolute-time conflicts.
- Lint and formatting checks passed for source, tests, examples, and project scripts.
- The complete good-math motion preview exported and decoded without errors:
  1280×720 H.264, 30 fps, 60.2 seconds, with AAC narration starting at zero.
- An audit of all 175 scene entries confirmed every diagram visual has animation
  tracks, all 19 named effects/builder operations occur, the 38 icons animate,
  resting transforms return correctly before exits, and node cue starts are intact.
- Decoded entrance, emphasis, and ending frames were visually inspected. The
  motion preview is `training project/good-math/output/good-math-motion-preview.mp4`;
  the effect log and audit are `animations.json` and `motion-verification.json`
  in the same output folder.

## Equation render and composition additions

Verified on 2026-10-03 with the optional `equations` extra (Matplotlib 3.11.2):

- **101 pytest cases passed**. New coverage checks stable formula reveals and width
  limits, invalid math syntax, helpful missing-dependency errors, drawable path
  length, rounded corners, polygon fills, delayed grid boundaries and padding,
  transparent layers, held frames, and nested audio offsets/crossfade envelopes.
- Ruff lint, formatting, and whitespace checks passed for the library, tests,
  examples, and equation-render scripts.
- The complete preview exported as 1280×720 H.264 at 24 fps, with 1,440 video
  frames and 48 kHz stereo AAC. Both streams start at zero and last exactly
  **60.000000 seconds**. Full video/audio decoding completed without errors.
- The ten-equation storyboard, three complete 1920×1080 canvases, and decoded
  transition/final frames were inspected. Body copy uses supported font glyphs;
  math symbols use the equation renderer. The grids are 2×2, 2×2, and 2×1.
- Decoded sound effects peak at −22.8 dBFS; they are deliberately quiet and
  sparse. This is a signal measurement, not a subjective listening review.

Run `uv run --extra equations python 'training project/equation-render/render.py'
--preview --overwrite` to regenerate the preview, or use `--frames` for the
storyboard. Downloaded fonts/icons, original effects, licenses, and provenance
are in the shared `assets/` directory. A default export selects 1080p/30 fps;
the full video checked here is the 720p preview.

## Color schemes and rendering quality

Verified on 2026-10-03 after adding coordinated palettes and per-symbol math colors:

- **117 pytest cases passed**, including the previous scene/export checks. New
  coverage includes palette validation, alpha multiplication, glyph coloring with
  unchanged formula geometry, Greek aliases, color-map validation, weighted font
  cache isolation, rounded path caps, scene-cache invalidation, caller image edits,
  out-of-order animation sampling, LRU eviction, and disabled frame caching.
- Ruff lint/format and whitespace checks passed. Public color APIs also imported
  successfully through the installed editable library from outside the checkout.
- Storyboards for `midnight`, `paper`, and `ocean` were generated, with completed
  canvases checked for text contrast, distinct graph quantities, formula alignment,
  and readable type. A decoded preview frame confirmed the exported symbol colors.
- The refreshed midnight preview uses antialias 2 and CRF 18. It fully decoded
  without errors: H.264 at 1280×720/24 fps, 1,440 frames, 48 kHz stereo AAC, and
  exactly 60.000000 seconds on both streams. Default final exports use CRF 16.
- In a focused benchmark of twelve held 720p frames from the first completed
  canvas, rasterization took 6.7736 seconds with the scene cache disabled and
  1.3423 seconds with the 64 MiB cache. The final RGBA hashes were identical.
  This measures a static hold; it is not a full-video speedup estimate.

The refreshed preview remains `training project/equation-render/output/equations-preview.mp4`.
Preset storyboards are under `output/frames/<scheme>/`, and symbol color assignments
are recorded in `output/timeline-<scheme>.json`. Renderer frame caching is bounded
and configurable with `PillowRenderer(frame_cache_mb=...)`.
