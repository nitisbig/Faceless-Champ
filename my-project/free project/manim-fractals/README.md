# Complex dynamics / native Manim integration

15 seconds on pure black (`#000000`). No headings, subtitles, audio, TeX or Docker.
Only the recurrence, complex coordinates and functional mapping labels appear.

- 0–4s: the Mandelbrot parameter plane accompanies the bounded orbit of
  `c = -0.5 + 0.5i`, starting at `z₀ = 0`. Each step separates squaring (gold)
  from translation by `c` (cyan).
- 4–8s: `c = 0.7 + 0.2i` produces an escaping orbit. The faint circle marks
  `|z| = 2`; the moving point turns pink after crossing it.
- 8–15s: the right plane becomes a Julia view. A linked marker moves through
  `c = -0.8 + 0.156i`, `-0.4 + 0.6i`, and `0.285 + 0.01i`, changing the
  Julia geometry while keeping its complex-plane window fixed.

The left image samples `z₀ = 0` for every parameter `c`; the right Julia image
samples every `z₀` for one shared `c`. Raster images use 144 iterations,
smooth escape-time coloring, and a radius-4 numerical bailout. Black means
no escape detected within that finite budget, rather than proof of membership.
The right orbit uses the radius-2 escape criterion for these selected parameters.

Run from the repository root:

```bash
# Key testing only: 60 native source frames and six FacelessChamp-composited stills.
.venv/bin/python my-project/manim-fractals/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Optional complete preview: 640×360, 15 fps.
.venv/bin/python my-project/manim-fractals/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python

# Full export: 1920×1080, 30 fps.
.venv/bin/python my-project/manim-fractals/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

Set `--manim-python` or `FC_MANIM_PYTHON` to your native Manim 0.22 environment
(the path above is this machine's temporary environment). It needs Manim and
NumPy. The parent interpreter needs FacelessChamp; FFmpeg and ffprobe must be on
PATH. The public `prepare_manim` adapter prepares the scene; FacelessChamp owns
the 15-second timeline, `Viewport` composition, and final MP4 export.
The scene supplies a small axis-aligned image camera to work around Manim 0.22's
invalid float RGBA canvas allocation; installed packages and library code are unchanged.

Outputs and preparation caches live in `output/`. Use `--overwrite` to replace
an MP4. Validation is intentionally restricted to numerical smoke checks,
60-frame preparation, six inspected key stills, and Ruff. Full preview and
1080p export are intentionally left unrendered.
