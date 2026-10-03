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
