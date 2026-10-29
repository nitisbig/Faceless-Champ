# Mathematical motion — native Skia

A silent **45-second, 1920 × 1080, 30 FPS** Faceless Champ scene on a pure black (`#000000`) background. Every visible element is procedural geometry rendered with `skia-python` on the CPU. No titles, labels, subtitles, numerals, external assets, or Docker.

| Source time | Graphics |
| --- | --- |
| 0–9.5 s | Analytic function reveal and moving tracer; converging secant |
| 9.5–19.5 s | Moving tangent, analytic derivative, linked points |
| 19–28.5 s | Signed Riemann rectangles, coarse to fine |
| 28–37.4 s | Four odd-harmonic Fourier epicycles and synchronized waveform |
| 37–45 s | Vortex vector field with particles and curved trails |

Run from the repository root using native Python:

```bash
.venv/bin/python my-project/skia-math/render.py --overwrite
```

Output: `my-project/skia-math/output/skia-math.mp4`.

Optional targeted samples:

```bash
.venv/bin/python my-project/skia-math/render.py --frame 14 --overwrite
.venv/bin/python my-project/skia-math/render.py --preview --overwrite
```

`--preview` exports source seconds 13–15; it preserves the original animation clock. `--quality 4k` selects 3840 × 2160. Exports include a JSON sidecar with the source range and renderer dependency identity. All animation uses public Faceless Champ components and deterministic animation tracks; no custom raster producer or library changes are needed.

Verification is deliberately limited to representative frame inspection, project lint, and MP4 metadata/decode checks. No broad test suite or benchmark is run.

For environments with short process time limits, `--range START END --output PATH` exports a section without retiming the scene. The delivered full export was assembled from consecutive source-clock sections (nine seconds each, reduced to three seconds for the vector field) with FFmpeg stream copy.
