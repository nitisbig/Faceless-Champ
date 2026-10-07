# Local release-candidate verification

Verified 2026-10-06 on Linux x86_64, Python 3.12.3, Pillow 12.3.0, FFmpeg/ffprobe 6.1.1. Core source baseline: `e95c89399da1fb3a6e62f5f690a1625d8685bde4`, distribution version 0.1.0. Kit version: 0.1.0rc1. No core source changes were needed.

## Automated and packaging checks

- 62 tests passed: all six blocks in portrait/landscape and both themes; timing and lifetimes; fresh ownership; retry after compilation failure; property conflicts; delayed stagger visibility; custom child motion; text fitting; strict assets; checksums; package resource materialization; cue/audio validation; master-clock captions; project import isolation; malformed config; overwrite protection; source-range forwarding; and a 100-segment timeline sampled out of order with a bounded core frame cache.
- Ruff check and formatting checks passed.
- Fresh core wheel/sdist built with uv. Kit wheel/sdist built with setuptools.
- Isolated environment installed core and kit wheels with Pillow as the only mandatory third-party runtime dependency. Media commands ran from /tmp, outside both source trees, without PYTHONPATH or editable installations.
- Built-in synthetic speech and SRT resources loaded from the installed kit package and materialized into the project cache. Narrated scaffolding is runnable offline.
- CI is configured for Python 3.12/3.13 against the pinned core baseline and current master. Remote CI has not been run; local evidence is for the environment above.

## Media evidence

| Artifact | Output | Verified |
| --- | --- | --- |
| Silent starter | 10 seconds, 1080×1920, 30 fps, no audio | Full export, ffprobe, full decode, inspected storyboard |
| Narrated starter | 30 seconds, 1080×1920, 30 fps, audio | Full export, ffprobe, full decode, inspected storyboard |
| Late excerpt | Source 22–27 seconds, 540×960, 15 fps, audio | Full decode, source audio/frame comparisons |
| Catalog | 24 stills and six 2-second motion clips | Both formats and themes rendered; representative gallery inspected |
| Captions | Narrated comparison at source time 12 seconds | Inspected frame with measured fitting and unchanged cue timestamps |

Late-excerpt decoded audio correlation against the corresponding original WAV samples: **0.9999127603**. Source-clock renders from independent builds were pixel-identical. Decoded excerpt frames at offsets 0, 2, and 4 seconds had mean absolute RGB differences of **1.1470, 1.1449, and 1.1449** out of 255 against their source-time renders, within the codec tolerance of 4.

The speech fixture is synthetic and persistently labeled. Its three cues are sentence-level cues at 0, 10, and 20 seconds, not claimed word alignment.

Artifacts are under `output/verification/` and `output/catalog/`. JSON reports preserve the original temporary verification paths and tool environment as historical build evidence; copied artifacts remain available in this repository. Reproduce with `python scripts/verify_media.py --output output/new-verification --profile final`. Use a fresh output directory for an untouched scaffold. `scripts/catalog.py` regenerates the visual catalog.

## Whiteboard addition — 2026-10-07

The `whiteboard_basic` addition was checked against core source baseline
`96d990e833f5c2f2dcc9e826f82640190d124e09`, with no core source changes.

- All 62 existing kit cases passed, alongside 50 whiteboard cases (112 total). These cover sequential visibility,
  linear progress and holds, scene clearing, fresh builds, immutable recipes, geometry errors, both canvas formats,
  label/caption reservation, original nonsequential cue indices, audio tails, and CLI registration/scaffolding.
- Ruff lint, formatting, and Git whitespace checks passed. Kit wheel/sdist and a fresh core wheel/sdist were built.
- Core and kit wheels were installed offline into an isolated environment. Pillow was copied from the existing local
  runtime. CLI media checks ran from `/tmp`, without `PYTHONPATH` or editable package imports.
- The installed CLI initialized the starter, validated it, produced a frame and storyboard, previewed it, and exported
  its complete ten-second video. The first export process was terminated; a separate retry completed successfully.

| Artifact | Output | Verification |
| --- | --- | --- |
| Whiteboard preview | 10 seconds, 960×540, 15 fps, silent | ffprobe and complete decode |
| Whiteboard final | 10 seconds, 1920×1080, 30 fps, silent; default final profile | ffprobe, complete decode, eight decoded frames inspected |
| Narrated excerpt | Source 1.25–3.75 seconds, 960×540, 15 fps | Complete decode, source audio/frame comparison, three decoded frames inspected |

The excerpt uses a clearly labeled synthetic test tone and SRT indices 7, 19, and 55. Audio correlation with the original
source range was **0.9988811054**. Maximum decoded-frame mean absolute RGB error was **0.803/255** for the final video and
**0.100/255** for the excerpt. Inspected frames showed the intended partial strokes, completed holds, and clean scene reset.

Artifacts and machine-readable results are under `output/whiteboard-verification/`. Reproduce from an installed environment:

```bash
python scripts/verify_whiteboard.py --output output/new-whiteboard-verification
```

Use a fresh directory, or `--resume` to reuse generated outputs and repeat the media checks. Portrait geometry and label
layout were tested; this addition does not claim a full portrait, 4K, or long-form export verification.

## General limits

This verifies short full exports at 1080p portrait, catalog rendering in landscape, and source-clock excerpts. It does not establish full 4K, sustained long-form rendering, alternate operating systems, or optional maps/equations extras. Core capabilities remain available, but kit domain sections are deferred.

Factories are trusted Python. Source modules and declared inputs are fingerprinted conservatively; arbitrary external dependencies and user-provided nondeterministic callbacks cannot be inferred. Do not edit media while exporting. Reports identify core-authored outputs whose block/asset metadata is unavailable. No byte-identical MP4 guarantee across encoder/font/platform versions is made.

Public publication and project-code licensing remain undecided. No remote repository, release, or package publication was created.
