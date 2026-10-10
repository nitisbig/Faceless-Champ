# CodingChamp verification — 2026-10-10

`full_export_verified: false`

The complete tutorial is authored, but the full video was intentionally **not rendered**.
No claim of full-duration 4K/60 performance or final-film validation is made.

## Timeline and layout

- Original narration: 151.464 seconds; 447 original word cues ending at 151.280 seconds.
- Nine cue-derived chapters; strict non-overlapping source cues; narration attached once at zero.
- 70 recorded visual events; every component animation checked against its lifetime and chapter boundary.
- 329 sampled root bounds checks inside the canvas safe area, including transforms and animation endpoints.
- Correct state at the spoken results: Alex 70 HP at 113.800s, Alex 85 HP at 117.310s, Sam 90 HP at 121.000s.
- No Captions components, title overlays, or subtitle overlays. Editor filenames, code and diagram labels remain.
- Final audio tail holds the last visual. Original audio, SRT files and class.py were not edited.
- Sam's damage and Alex's healing are shown in narration order; their independence preserves reference results.

## Automated checks

- Core and kit regression suites: **479 passed, 1 skipped**.
- CodingChamp coverage within that suite: **28 passed**, including Python/JavaScript/TypeScript,
  LF/CRLF whitespace, indentation and tabs, all reveals, themes, layout errors, dependency errors,
  staged animation, snapshots, transforms/masks, bounded caches and cached/uncached parity.
- Project acceptance suite: **6 passed**, including all themes, health timing, source-clock structure,
  invocation from another directory and invalid FPS rejection.
- Installed-wheel CodingChamp tests outside the source tree: **28 passed**.
- Source distribution and wheel built offline successfully. Installed wheel rendering, optional-extra
  metadata, bundled monospace font and license checked. Final wheel bytes matched current core files.
- Ruff lint/format, `git diff --check`, and offline lockfile consistency passed.

## Actual encoded excerpts

| Source range | Output | FPS | Frames | Source-audio correlation |
|---|---|---:|---:|---:|
| 33–41s | 1280×720 | 20 | 160 | 0.999838 |
| 72–80s | 1280×720 | 30 | 240 | 0.999648 |
| 110.64–124.84s | 1280×720 | 30 | 426 | 0.999841 |
| 38–39s | 1920×1080 | 60 | 60 | 0.999852 |
| 124–124.25s | 3840×2160 | 30 | 8 | 0.999848 |

All five MP4s (894 frames) passed complete FFmpeg decoding, exact dimensions/FPS/frame counts,
and frame-rounded video duration checks. Audio was compared sample-aligned against a full decode
of the source MP3, without direct MP3 seeking. The quarter-second 4K interval rounds to eight frames.

Visual inspection covered a 23-frame storyboard across the complete narrative, a decoded frame
from each MP4, and paper/ocean theme stills at 135 seconds. Code is readable, indentation remains
stable, and player/console cards fit without overlapping code. This is sampled visual QA, not
an inspection of every final-film frame.

Artifacts are under `output/`: the five descriptive MP4 filenames, decoded `*-frame.png` files,
`storyboard-midnight/storyboard.png`, theme stills, `structural-verification.json`, and
`media-verification.json`. Generated media remains ignored by Git.

Reproduce structural checks with `python3 render.py --check`. Run the project's pytest file
from the repository environment. `scene/verify_media.py` rechecks the five existing excerpts
and requires NumPy for audio comparison; it does not render a video.

Source SHA-256 values recorded after implementation:

```text
audio.mp3          28f2aa86e1322c3817e7fb65a3875c5a1bc0a8bda901c963ecb391af68105b6a
cue-per-word.srt    685a29f87fa1766664cb3580a46517661e342cf06feee25499518c3b0aae9a56
class.py           a4d3fae1b76e591a1ebb52e48c5a7f0d8eb7d9e9993407e6286065790904aebb
```
