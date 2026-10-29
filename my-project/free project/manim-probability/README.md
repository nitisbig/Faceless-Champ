# Probability simulations — native Manim + FacelessChamp

45 seconds, pure black (`#000000`), no headings, subtitles, audio, or Docker.
Only functional mathematical labels and live values appear.

- **0–17s:** 1,200 repeated samples of 24 uniform random values. Their standardized
  means accumulate in a density histogram against the standard Gaussian density.
  The upper row shows the current sample; the white marker shows its mean in z units.
- **17–29s:** 640 Monte Carlo points in a square, colored by circle membership.
  The area ratio estimates π, with a running convergence trace.
- **29–45s:** simulated Bernoulli observations with true probability 0.65 update a
  uniform Beta(1,1) prior to Beta(successes+1, failures+1). The curve uses a fixed
  vertical density scale. The separate green interval is the frequentist 95%
  Wilson score confidence interval, computed from the same observations.

All randomness uses seed 241021. The Gaussian is the central-limit approximation
for finite uniform samples. The Bayesian curve is an exact conjugate posterior;
the green confidence interval is not a Bayesian credible interval. The final
2.3 seconds hold the final inference state.

From the repository root:

```bash
# Key verification: 180 prepared frames at 640×360/4 fps, six composited stills.
.venv/bin/python my-project/manim-probability/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Optional 45-second preview, 640×360/15 fps.
.venv/bin/python my-project/manim-probability/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python

# Full 45-second export, 1920×1080/30 fps.
.venv/bin/python my-project/manim-probability/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

Use `--manim-python` or `FC_MANIM_PYTHON` to select your native Manim 0.22
interpreter. The example runtime is a temporary local environment. It requires
Manim and NumPy; the parent Python requires FacelessChamp. FFmpeg and ffprobe
must be on PATH. This scene does not require LaTeX.

The public `prepare_manim` adapter prepares the animation. FacelessChamp places
the prepared source in a `Viewport` on its own 45-second timeline and composites
the stills or exports the MP4. Outputs and immutable preparation caches are under
`output/`. Pass `--overwrite` to replace an existing MP4.

Validation is limited to the low-resolution preparation, six key stills, focused
numerical checks, and Ruff. Full preview and 1080p export are intentionally unrun.
