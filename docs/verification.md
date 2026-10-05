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

## Image sources and AI audience example

Verified on 2026-10-04:

- **185 pytest cases passed**. Added source parity and snapshot tests, transparent
  trimming/tint checks, invalid source handling, in-memory GIF playback across
  cached frames, and horizontal polyline reveal validation.
- Ruff lint/format and Git whitespace checks passed for the library, tests,
  examples, and the new training project.
- The full 30-second illustrative preview exported as 1280×720 H.264, 24 fps,
  720 frames. FFmpeg fully decoded the export without errors. The scene is silent.
- Six storyboard frames and a decoded mid-animation frame were inspected for
  readable disclosures, logo contrast, continuous curves, and marker alignment.
- No additional runtime dependencies or build configuration changes are required;
  the new image-source API uses the existing Pillow dependency.

Run `uv run python 'training project/ai-comapny-graph/render.py' --preview`.
The training project's original folder spelling is retained. All user counts and
relative origins are fictional; they do not assert company founding dates or
historical adoption. Default exports use 2× supersampling; previews use 1× for speed. A 1080p
frame with 2× supersampling was also checked from outside the repository.
An additional 2× full-preview render was interrupted by the execution environment;
the completed 1× preview remained intact through the atomic export mechanism.

## Country Economy, image slots, and narration ranges

Verified on 2026-10-04:

- **196 pytest cases passed**. New coverage checks opt-in subtitle overlaps with
  exact timestamp preservation, image-slot modes and asset replacement, fitting,
  transforms, corrupt asset errors, bounded caption caching and pixel parity,
  held-frame reuse, and ranged audio/visual exports with composition offsets/fades.
- Ruff lint/format and Git whitespace checks passed. The project's `python3`
  entry point also exported a frame while invoked from outside the repository.
- The complete composition contains **14 chapters, 344 chapter components,
  154 visual events, and 991 original word cues**. Four source overlaps of 1 ms
  are accepted explicitly; both subtitle files and the source audio remain intact.
  Chapter text bounds stay inside the design canvas and above the caption band.
- **37 storyboard frames** cover chapters and key moments. Before/during/after
  samples were checked for the spending bar, 20% borrowing rate, doubled local
  repayment cost, and closing confidence reveal. Each check has distinct frames;
  the final Confidence entrance begins on original cue 990 at 359.1s.
- Only four short low-quality clips were rendered: the opening (16.733333s),
  deficit chapter (9.066667s), borrowing rates (7s), and currency conversion (10s).
  All are **960×540, H.264, 15 fps**, with stereo 48 kHz AAC. Both streams begin
  at zero; fractional source intervals round up to whole video frames.
- All four clips decoded fully through FFmpeg without errors. Correlation of their
  decoded audio with the corresponding trimmed source audio exceeded **0.9998**,
  verifying source-time alignment after re-encoding. This is a signal check, not
  a subjective listening assessment. A decoded deficit-animation frame was inspected.
- The complete six-minute video was **not rendered**. `--all-preview` remains an
  explicit option. Existing licensed fonts and symbols were reused from shared
  assets; no new dependency or asset download was needed. Asset hashes, sources,
  and license paths are recorded in `assets/country-economy-sources.json`.

Run `python3 'training project/country-economy/render.py' --image placeholder`
for the opening, or add `--storyboard`, `--scene deficit`, or `--range 120 127`.
Artifacts and detailed checks are in the project's `output/`, including
`timeline.json`, `media-verification.json`, and `scene-verification.json`.

## Maps (2026-10-05)

- Added offline country outlines, satellite maps, and a textured orthographic Earth sphere.
- Full suite: **207 passed**; Ruff checks and `git diff --check` passed.
- Map tests cover lookup, asset hashes and size, animation endpoints, full rotations,
  shortest longitude travel, polygon holes, date-line wrapping, poles, texture orientation,
  alpha masks, viewport-sized zoom rendering, and missing optional NumPy errors.
- Built wheel and source distribution. All four map asset files are included; the asset
  directory is approximately **1.2 MB**. Rendered all three map types from an installed
  wheel with network access blocked. Fresh package import and ordinary shape rendering
  also work with NumPy imports blocked.
- Exported `media/maps/maps.mp4`: **18 seconds, 640×360, 12 FPS, 216 frames**, fully decoded
  without FFmpeg errors. Inspected world/country outlines, satellite country zoom, and
  globe start, rotation midpoint, country zoom, and final ocean view.
- HD/4K export performance is unverified. Close-up imagery is limited by the bundled
  4096×2048 texture. Country coverage is the 177 bundled Natural Earth records.

## Country flags (2026-10-05)

- Added public `Flag`, `flag_path`, and `supported_flags` APIs using country codes.
  All 254 supplied PNGs are bundled unchanged; the original `assets/flags` remains available.
- Full suite: **228 passed**. The 21 flag tests cover uppercase/whitespace lookup,
  territory and subdivision codes, invalid codes and path traversal, non-string inputs,
  every bundled PNG, original colors/transparency, contain/cover fitting, fades, and transforms.
  Flag tests also passed after removing a deprecated Pillow call from the test itself.
- Ruff lint/format checks and `git diff --check` passed.
- Built wheel and source distribution; both contain all 254 flag PNGs. SHA-256 hashes
  match the supplied files and the installed wheel for every flag. Installed-package
  lookup and rendering passed from `/tmp` with network, NumPy, and Matplotlib blocked.
- Rendered `output/flags/flags.mp4`: **2.25 seconds, 1280×720, 12 FPS, 27 H.264 frames**.
  FFmpeg decoded the entire video without errors. Inspected the final gallery frame,
  including Nepal's transparent outline, rectangular flags, and Switzerland's square flag.
  Reproduce with `uv run faceless-champ render examples/flags.py FlagsShowcase -o output/flags/flags.mp4 -q ql --fps 12`.

## Object groups and measured layouts (2026-10-05)

- Added `Group` and `Bounds`, with `arrange`, `next_to`, `align_to`, and `shift` helpers.
  Nested group movement, uniform scaling, clockwise rotation, and inherited opacity
  compose with independent member animations and local stacking order.
- Full suite: **258 passed**, including **30 new group/layout cases**. Coverage includes
  measured text and rotated/scaled edge spacing in all four directions, center/edge
  alignment, nested transforms, simultaneous member animation, snapshot isolation,
  out-of-order frame sampling, caption lifetimes, GIF timing, ownership validation,
  atomic rejection, and identity-group equivalence at multiple export resolutions.
- Ruff lint/format checks and `git diff --check` passed. Built wheel and source distribution.
  An installed wheel rendered grouped text/shapes from `/tmp` with network access and
  NumPy/Matplotlib imports blocked, confirming ordinary grouping needs no new dependency.
- Rendered `output/groups.mp4`: **6 seconds, 960×540, 24 FPS, 144 H.264 frames**.
  FFmpeg decoded the full video without errors. Visually inspected the rotating connected
  diagram, measured labels, and independent center-node scaling.
- Reproduce with `uv run faceless-champ render examples/groups.py GroupedDiagram -o output/groups.mp4 --width 960 --height 540 --fps 24 --antialias 2`.
- Membership is fixed before scene addition; existing members cannot be reparented.
  Layout bounds describe initial sprite rectangles and do not implement text wrapping,
  collision detection, or time-evaluated layout constraints.
