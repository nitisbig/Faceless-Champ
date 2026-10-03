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
