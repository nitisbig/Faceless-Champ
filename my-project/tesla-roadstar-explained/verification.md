# Verification

## Current v2

Review scope was limited to two short low-quality motion excerpts and four
representative mathematical compositions, as requested.

- Opening: source 0–6.76 s, encoded 6.8 s, 102 frames at 960×540 / 15 fps.
- Pressure: source 215–217 s, encoded 2.0 s, 30 frames at 960×540 / 15 fps.
- Both clips decode completely and retain AAC narration. Every adjacent decoded
  frame differs in the sampled pixel comparison; this is evidence for these two
  excerpts, not a full-timeline motion audit.
- Encoded opening samples at 0, 2.27, 4.47 and 6.4 s were inspected. The complete
  road and car remain in view. The introductory camera orbits around the road.
- The pressure composition was inspected and its underbody framing adjusted to
  retain the outer wheel. The final encoded 216 s frame was inspected afterward.
- Graph (141 s), pressure (216 s), inertia matrix (553 s), and allocation matrix
  (570 s) text bounds remain inside the canvas. These are selected key frames,
  not an exhaustive collision audit. The graph and matrix images were inspected.
- Source fingerprints pass. Python syntax, Ruff and formatting checks pass.
- No full film, 4K export, broad test suite or full-timeline layout audit was run.
  No fresh audio correlation test was run; the existing master audio path is reused.

Review: `output/v2/index.html`. Evidence: `output/v2/review.json` and
`output/v2/key-layout.json`. Research and implementation: `V2-DESIGN.md`.

`full_export_verified: false`

## Retained v1 red/blue revision

Only the opening and representative mathematical scenes were reviewed.

- The continuous intro exports as 68 frames at 960×540 / 10 fps, lasting 6.8 s
  for the source window 0–6.76 s. It decodes completely and retains AAC narration.
- All adjacent encoded frames differ. Encoded frames at 0, 3.5 and 6.4 s were
  inspected; the full C-shaped apparatus and car are visible in the opening.
- The road's projected geometry lies completely inside the viewport at those
  three sampled times. The introductory camera uses no overscan or cropping.
- The graph scene at 141 s and matrix scene at 553 s were rendered at low quality,
  visually inspected, and have no sampled text-layout findings.
- The background is pure black, with red trajectory lines and blue outlines.
  Mathematical results are centered and matrix entries align within their cells.
- Source fingerprints match. Python syntax, Ruff and formatting checks pass.
- No broad test suite, full-timeline audit or complete film export was run.

Review: `output/revision-red-blue/index.html`.
Evidence: `intro-review.json` and `key-review.json` in that directory.

`full_export_verified: false`

## Earlier neon revision

The current edit has a deliberately small review scope: six 960×540 key frames
covering the incline graph, pressure field, roll graphs, inertia matrix,
allocation matrix and landing. The six sampled text layouts have zero findings;
the landing camera was then tightened and its replacement frame inspected.
The 6.8-second encoded opening (source 0–6.76 s) contains 68 frames at
960×540 / 10 fps with AAC narration. It decodes completely, and all adjacent
frames differ. Four encoded action frames were visually inspected. The video
and key frames are in `output/revision-neon/index.html`.

Export controls accept 10/15/30 fps and low/high/4k. CLI help, Python syntax and
Ruff checks pass. Formula rendering uses the existing offline STIX MathText
engine; no TeX packages or other assets were downloaded. Source media and cue
files remain unchanged. No broad test suite or complete layout audit was run for
this edit. The complete revised film and 4K output are unrendered.

`full_export_verified: false`

## Previous design evidence

The following checks describe the previous design, before the neon revision.
They do not certify the current revised frames or a current full export.

The complete 40-shot implementation passes the source-clock, mathematical,
geometry and layout checks. The full film has not been exported.

- 1,975 word cues and all five intentional 1 ms overlaps are preserved.
- The original narration, both SRT files and supplied scene plan match their recorded hashes.
- One master narration clip starts at zero; the frame-aligned endpoint is 738.300 s.
- 46 distinct expressions typeset successfully. SI force balances, release continuity,
  friction capacity, torque reversal, hover descent and calculated landing endpoints pass.
- All surfaces receiving capped cutaways are closed; decorative rims are excluded.
- 16 project regression tests pass.
- The native 3840×2160 glyph audit passes at 1,879 sampled times, with zero text collisions.
- 80 storyboard frames pass layout checks and were visually reviewed across all ten chapters.
- 14 native 4K review frames were produced and reviewed across all ten chapters.
- Five reference-guided cinematic illustrations were generated and used; their
  prompts, native dimensions and hashes are recorded in the asset provenance file.

All ten narrated HD previews pass encoded-media verification:

- 3,947 frames total; 1920×1080 at 30 fps. Every file decodes completely.
- Frame counts and audio durations match the requested source windows.
- 30 full three-second audio comparisons pass, with **0.000 s measured lag**
  at the 8 kHz analysis rate. Minimum correlation is 0.9997286.
- 30 decoded sample frames and two additional roll/reversal checkpoints were
  visually reviewed. This is sampled visual inspection of the encoded previews.
- Ruff, formatting and `git diff --check` pass.

Open `output/index.html` for the narrated preview player, or
`output/storyboard/index.html` for the complete shot storyboard.

Machine-readable evidence: `output/checks.json`, `output/layout-audit.json`,
`output/storyboard/layout-findings.json`, `output/frames/frames.json` and
`output/verification.json`. Images and pressure fields are illustrative; hidden
hardware and control architecture are schematic.

`full_export_verified: false`
