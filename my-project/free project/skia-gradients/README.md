# Skia abstract gradients

A silent, graphics-only 60-second scene on a pure black canvas. Native Python,
Faceless Champ and Skia CPU rendering; no Docker or external assets. Default
export is 1920×1080 at 30 fps. There are no titles, labels or text overlays.

The continuous choreography moves from flowing gradient ribbons (0–26s), through
softly glowing liquid Bézier shapes (17–45s), into layered orbital silk (36–60s).
Overlapping sequences dissolve naturally. Colors drift from violet/cyan toward
coral/peach and back, with soft background halos and a fade to black.

Run from the repository root:

```bash
# Full one-minute export
.venv/bin/python my-project/skia-gradients/render.py

# Two-second preview, source time 28–30s
.venv/bin/python my-project/skia-gradients/render.py --preview --quality 720p --overwrite

# Still or custom source-time excerpt
.venv/bin/python my-project/skia-gradients/render.py --frame 8
.venv/bin/python my-project/skia-gradients/render.py --range 46 49 --output /tmp/orbital-silk.mp4

# Full 4K export
.venv/bin/python my-project/skia-gradients/render.py --quality 4k
```

Outputs live in `output/` beside the script. Export sidecars record source range,
rendering identity and backend counters. The native export progress bar shows
frame progress, elapsed time and ETA.

Core v1 does not animate path geometry or gradient stops. The project-local
`AbstractGradients.sample(t)` authors fresh immutable `VectorPath`, `PathData`,
`LinearGradient` and `RadialGradient` descriptions at each source time.
`GradientRenderer` implements the public renderer protocol and delegates those
ordinary scenes to Faceless Champ's native Skia renderer. This produces actual
cubic Bézier deformation and changing gradients without modifying core APIs.
When importing this project, pass `renderer=GradientRenderer()` to `render` or
`save_frame` and close the renderer afterward (or use its context manager).

Limited verification completed:

- Exact 60-second timeline; black endpoints; representative stills at 8, 22, 30,
  43, 51 and 59 seconds inspected in `output/key-frames.jpg`. Contact-sheet
  timestamps sit outside the scene images.
- Repeat sampling at 30s after sampling 8s produced identical pixels.
- Backend counters confirmed native vector leaves and zero raster leaves.
- Two-second preview: 1280×720, 30 fps, 60 frames; complete FFmpeg decode passed.
- Ruff formatting/lint and whitespace checks passed.

Full-minute and 4K exports have not been rendered or verified.
