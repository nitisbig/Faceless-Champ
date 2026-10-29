# ModernGL fluid flow scene

15 seconds, black background, graphics only, silent. Cyan velocity filaments
develop into two counter-rotating vortices with warm high-speed tracers, subtle
pressure contours and turbulent smoke-like trails. The first and last frames
fade to black.

Run from the repository root with native Python:

```bash
.venv/bin/python my-project/moderngl-fluid/render.py
```

Default export: `output/moderngl-fluid.mp4` beside this script, 1920×1080 at
30 FPS. Existing outputs require `--overwrite`.

```bash
# Bounded motion sample, source time 9–10 seconds.
.venv/bin/python my-project/moderngl-fluid/render.py --preview --quality 720p --fps 12

# Inspect a still or export another source range.
.venv/bin/python my-project/moderngl-fluid/render.py --frame 9 --quality 1080p
.venv/bin/python my-project/moderngl-fluid/render.py --range 3 5 --quality 720p
```

Uses the existing Faceless Champ ModernGL compositor, EGL, GPU-instanced ambient
particles, vector paths and local glow. A project-local renderer adapter samples
the source-time geometry and delegates painting to the library. It requires the
repository's GPU and Skia dependencies; no Docker is used.

The flow is an artistic divergence-free velocity field integrated with a fixed
1/60-second midpoint step and a fixed seed. Trails break at inlet resets. This
allows repeatable seeking at any export FPS. Smoke is layered tracer filaments;
the contours illustrate vortex pressure, rather than a numerical pressure solve.
This is not a Navier–Stokes simulation or a custom fluid GLSL implementation.

Each output has a JSON sidecar with the actual renderer/driver identity and
source range. Software EGL is supported but can be slow. A sidecar retains
`full_export_verified: false` until a complete movie is separately inspected.

Local verification is intentionally limited to key geometry checks, two 720p
stills and a one-second 720p/12 FPS preview. The full 15-second export is left to
the command above.
