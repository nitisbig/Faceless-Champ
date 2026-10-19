# Orbital HUD — native Skia scene

A silent, 45-second graphics scene using Faceless Champ's public scene and animation APIs with the native `skia` backend. All graphics are procedural vectors; typography and animated numbers also use Skia. No Docker, external artwork, or network access is needed.

The display combines opposing circular rings, a radar sweep with eight moving contacts, a tracking reticle, a wireframe globe, two animated gauges, segmented energy meters, waveforms, coordinate/angle readouts, a spacecraft scanner, and a spectrum strip. Short instrument labels support the graphics.

| Time | State |
| --- | --- |
| 0–8 s | Acquire contacts; instrument activation |
| 8–20 s | Track a moving contact |
| 20–34 s | Target lock |
| 34–45 s | Rescan while instruments continue running |

From the repository root, render the full film at **1920 × 1080, 30 FPS**:

```bash
.venv/bin/python my-project/skia-hud/render.py --overwrite
```

The result is `my-project/skia-hud/output/skia-hud.mp4`. Use `--quality 4k` for a 3840 × 2160 export. A source-clock range is used for the preview, preserving the full film's animation timing.

For a short sample or a still:

```bash
.venv/bin/python my-project/skia-hud/render.py --preview --overwrite
.venv/bin/python my-project/skia-hud/render.py --frame 24 --overwrite
```

Each output has a JSON sidecar recording its source range and backend/dependency/font identity. Sampled animation tracks are deterministic and do not depend on previous frames. Generated media lives in the ignored `output/` directory.

Verification is intentionally limited to representative still inspection, the three-second tracking sample, lint, and the delivered MP4's duration/frame count and decode. No broad library test suite is required for this project-local scene.
