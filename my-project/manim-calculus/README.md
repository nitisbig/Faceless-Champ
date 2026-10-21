# Calculus / native Manim integration

45 seconds on pure black (`#000000`). A secant converges to a tangent,
the tangent traverses a parabola alongside its live derivative, pauses at the
maximum, and midpoint Riemann rectangles refine into the definite integral.
Only mathematical labels and numerical values appear. No audio or LaTeX needed.

Run from the repository root using native Python and a Manim 0.22 environment:

```bash
# Bounded verification: 180 prepared frames; seven FacelessChamp-composited PNGs.
.venv/bin/python my-project/manim-calculus/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Optional complete preview (640×360, 15 fps).
.venv/bin/python my-project/manim-calculus/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python

# Full export (1920×1080, 30 fps).
.venv/bin/python my-project/manim-calculus/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

The example runtime path is local and temporary; use `--manim-python` or
`FC_MANIM_PYTHON` for another environment. FFmpeg and ffprobe must be on PATH.
Manim prepares immutable frames through the public adapter; FacelessChamp
composites them through `Viewport` and exports the MP4. Outputs and preparation
cache live in `output/` beside the scripts. Pass `--overwrite` to replace an MP4.

Timing: 0–12s secant limit; 12–20s moving tangent and derivative;
20–25s stationary maximum and transition; 25–37s midpoint sums (8–128 bins);
37–45s exact area `122/15` and final hold.
