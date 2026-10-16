# Full-length scene verification

Scene authored on 2026-10-16. The entire lesson is **131.12 seconds** at an
authored canvas of **1920×1080**. Full video export remains unrun.

## Structural checks

`../../../.venv/bin/python render.py --check` passes:

- All 345 word cues keep their original timing, including the 1 ms overlap.
- The original audio and both subtitle files match their recorded SHA-256 hashes.
- One complete 131.016-second narration track begins at master zero; no audio
  trimming or fades. The final visual hold extends through the last subtitle cue.
- All 7,868 layout samples pass at 60 samples per second, with a minimum 94 px
  clearance from the canvas edges and no main-window / execution-flow collisions.
- The longest blank transition is 0.15 seconds.
- Initial empty-editor states, source typing, shell commands, result reveals,
  recap, and final variable example pass timeline checks.
- All displayed Python examples compile without execution.
- Ruff checks, formatting, and `git diff --check` pass.

Reveal state is explicitly initialized through scene animations. Frame inspection
caught that assigning `panel.reveal = 0` alone does not seed the core scene state;
the final scene includes early-state checks to prevent code appearing before typing.

## Visual and excerpt evidence

Eighteen 960×540 frames were rendered and inspected at master times 13.80, 20.00,
26.00, 32.99, 41.00, 47.00, 54.00, 62.00, 70.90, 74.90, 78.98, 87.70, 90.99,
106.40, 111.80, 123.50, 129.60, and 131.10 seconds. Review frames are in
`output/review-frames/`; contact sheets are `output/storyboard-1.jpg` through
`output/storyboard-3.jpg`. The corrected empty-editor frames were inspected again.

The message-change excerpt was exported with:

```bash
../../../.venv/bin/python render.py --range 88.24 91.92 \
  --fps 15 --width 960 --height 540 \
  --output output/review-message-change.mp4 --overwrite
```

The excerpt has 56 H.264 video frames at 960×540 / 15 fps, plus AAC audio.
Its encoded duration is 3.733333 seconds because export rounds the requested
3.68-second interval up to complete frames. Complete FFmpeg decoding passed,
and an extracted encoded frame was visually inspected.

The entire 3.68-second reference audio window at master offset 88.24 seconds was
compared with the encoded excerpt: 58,880 mono samples at 16 kHz, correlation
**0.9999226** at the expected offset. This verifies the excerpt's audio placement.

`media_rendered: true` for the review frames and excerpt only.
`full_export_verified: false`. No complete video, 1080p/60 export, or 4K export
has been rendered or inspected. `--check` reports structural evidence separately
and continues to return `media_rendered: false`.
