# Physics and vector fields — native Manim + FacelessChamp

45 seconds on pure black (`#000000`), with graphics only and no LaTeX dependency.
Manim prepares the animation through the public adapter; FacelessChamp composes
the prepared frames in a `Viewport` and owns the timeline and final MP4 export.

- **0–15s:** circular flow, magnitude-colored arrows, particles and trailing paths.
  The field is `F(x,y) = (−0.7y, 0.7x)`; particle positions are exact solutions.
- **14.2–29.5s:** three staggered projectiles in a uniform gravity field. Arrows
  show velocity; vertical lines show its changing vertical component.
- **28.7–45s:** spring–mass motion and its synchronized phase portrait. The
  oscillator obeys `x'' = −1.25²x`; the portrait uses `(x, v/1.25)` with equal
  display scaling, so trajectories are circles. Arrow length shows field magnitude.

Transitions overlap briefly. Every moving object is evaluated from the absolute
clock, with analytic paths rather than accumulated integration steps.

Run from the repository root, using native Python:

```bash
# Key checks only: prepare 90 low-resolution frames and composite seven PNGs.
.venv/bin/python my-project/manim-physics/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Optional full 45-second preview: 640×360, 15 fps.
.venv/bin/python my-project/manim-physics/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python

# Full export: 1920×1080, 30 fps.
.venv/bin/python my-project/manim-physics/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

The example Manim environment is temporary. Select another native Manim 0.22
environment with `--manim-python` or `FC_MANIM_PYTHON`. The parent environment
needs FacelessChamp; the producer environment needs Manim. FFmpeg and ffprobe
must be on PATH. No Docker is used.

Outputs and prepared caches live in `output/` beside these scripts. Pass
`--overwrite` to replace an existing MP4 or `--output PATH` to choose a filename.
`--manim-timeout SECONDS` controls the preparation deadline (default: 7200).
`--frames` uses the same scene geometry at 640×360/2 fps; it does not produce
a full preview or production MP4.

Verified locally: native Manim preparation at 640×360/2 fps (90 frames, exactly
45 seconds), seven inspected FacelessChamp-composited PNGs, nonblank imagery
and pure-black corners, ballistic endpoints/apex, conserved oscillator energy,
and Ruff. The contact sheet is `output/keyframes.jpg`. Full preview and 1080p
exports have not been run.
