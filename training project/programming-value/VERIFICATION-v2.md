# Programming Value v2 — verification

Current status: the complete 1920×1080 / 30 fps export is rendered and verified. Final file: `output/programming-value-v2-full.mp4` (493.166667 s, 14,795 frames, H.264 video and AAC audio).

## Checks already completed

- The outline was written before animation code; the smallest 0–12 s prototype was rendered and its encoded frames inspected before expanding the film.
- All 1,379 source cues and the original audio retain their SHA256 checksums. Six intentional 1 ms cue overlaps remain unchanged.
- 43 shots cover the complete 493.152 s source clock. Six recurring motifs appear in the first 24.4 s. 294 scheduled attention events have a maximum gap of 2.992 s.
- Layout audit passed all 14,795 final-frame times: 485,172 component/frame states and 1,613,683 collision-pair/frame states. No detected safe-margin violations, label collisions, or connector/label crossings. Documented containment, halos, depth silhouettes and connector/node joins are intentional.
- All semantic text colors exceed 4.5:1 contrast against black and the dark surfaces. Minimum design font size is 32 px.
- The 1080p question excerpt passed source-audio comparison: correlations 0.999836–0.999881, zero measured offset, zero measured drift.
- Nine timing/layout/renderer regression tests passed. The separate real checkpoint-export test passed complete decode, exact joined frame count, audio presence, completed-chunk reuse, and changed-input cache invalidation.
- Ruff checks passed. Version one remains callable with its original white canvas and six chapters.

## Completed full-export verification

- `python3 verify_v2.py --clips` passed. Complete FFmpeg decode recovered all 14,795 frames, with zero video timestamp error against the 30 fps schedule.
- Beginning, middle and ending audio windows measured zero offset and zero drift, with correlations 0.999849–0.999859 and gain ratios 0.99729–0.99775 against the decoded original narration. The source file remains unchanged; the final export uses AAC encoding.
- Inspected encoded frames from every shot, the opening lead-in and audio tail, plus five late-reveal frames showing fully populated diagrams. Typography, safe margins, connector spacing and progressive reveals are clean. Four inspection sheets and six representative chapter clips are available under `output/encoded-v2/` and `output/clips-v2/`.
- Machine-readable results: `output/verification-v2.json`.
- Final output SHA256: `de54d311fcaf81744761049e28af61e4e0924059b6c055a87f6408a51f8654e1`.

## Reproduction

```bash
python3 render.py --full
python3 render.py --audit-layout
python3 verify_v2.py --clips
MPLCONFIGDIR=output/.matplotlib ../../.venv/bin/python -m unittest discover -s tests -v
```

Full exports reuse only completed, frame-count-checked chunks under a fingerprint of source files, fonts, vector scene/library code, and export settings. Video frames are sampled on the absolute source clock. Silent chunks are joined before the original audio is attached once at master zero. Repeating `--full` after interruption resumes from completed chunks; `--overwrite` is required to replace an existing final output.

Retention improvement has not been measured. 4K exports have not been validated. The current target is 1920×1080 / 30 fps.
