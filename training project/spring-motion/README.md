# Spring motion — 45 seconds

A silent, self-contained training scene using the public Faceless Champ API.
Warm paper, dark typography, orange accents, measured guides and short source
examples keep the motion readable. All geometry and fonts are local; no asset
downloads, browser preparation, audio, or external services are needed.

| Time | Example |
| --- | --- |
| 0–5s | The actual spring response: move, overshoot, settle |
| 5–14s | Equal-distance tracks with damping 6, 12, and 20 |
| 14–21s | A notification moves as a complete parent group |
| 21–29s | A button scales and a card rotates into place |
| 29–38s | Three cards arrive with a 0.22-second stagger |
| 38–45s | Position, scale, and rotation together |

From the repository root:

```bash
# Complete 45-second silent preview: 960×540, 30 fps.
python3 "training project/spring-motion/render.py" --overwrite

# Complete 1080p export; optionally use --quality 4k or --fps 60.
python3 "training project/spring-motion/render.py" --quality high --overwrite

# Inspect without exporting the movie.
python3 "training project/spring-motion/render.py" --check
python3 "training project/spring-motion/render.py" --storyboard --overwrite
python3 "training project/spring-motion/render.py" --frame 5.96 --quality high --overwrite
python3 "training project/spring-motion/render.py" --range 29 33 --overwrite
```

The wrapper selects the checkout's `.venv` when available and works from any
working directory. FFmpeg is required to encode a movie. `--output PATH` redirects
the artifact; for a storyboard it names a directory. Existing outputs require
`--overwrite`. Default outputs live in this project's `output/` directory.

`scene.py` contains the six examples. `build_video()` returns the full composition;
`build_shots()` exposes individual shots. The default configuration is
`Spring(stiffness=100, damping=12, mass=1)`. This is analytical easing retimed to
`run_time`: the damping ratio sets the normalized character, while `run_time`
sets the on-screen duration. The comparison holds stiffness and mass fixed.
Spring animates position, scale, and rotation; separate smooth tracks fade cards.

`--check` verifies the 45-second timing, silence, spring properties and sampled
canvas clearance, including dense samples around early overshoot. This is layout
evidence; the rendered media is verified separately.

Local verification: the complete 45-second preview was rendered at 960×540,
30 fps (1,350 frames), fully decoded, and inspected through encoded-frame samples.
The project audit passed 1,856 sampled bounds checks with a minimum 17-pixel
canvas clearance. All 538 spring kernel, timeline, and scheduling regression tests
passed, as did Ruff and formatting. The CLI was also checked from a different
working directory, including invalid ranges and overwrite protection.

Artifacts: `output/preview.mp4`, `output/storyboard/storyboard.png`,
`output/encoded-storyboard.png`, `output/structural-verification.json`, and
`output/media-verification.json`. One 1080p still was inspected; complete 1080p
and 4K exports remain unrendered (`full_export_verified: false`).
