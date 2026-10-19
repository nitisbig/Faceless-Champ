# Physics diagrams — native Skia

A silent, **60-second, 1920 × 1080, 30 FPS** scene on pure black. Procedural vector graphics use Faceless Champ's public scene/animation APIs with the native `skia-python` CPU backend. Text is limited to small physical symbols; there are no headings, titles, or subtitles. No Docker or external assets are required.

| Source time | Graphics |
| --- | --- |
| 0–14 s | Inclined block, weight, normal reaction, static friction, resolved weight, closed equilibrium force triangle |
| 14–29 s | Parabolic projectile, equal-time markers, tangent velocity, horizontal/vertical components, downward gravity |
| 29–44 s | Spring/mass oscillator, restoring force, velocity, synchronized displacement trace |
| 44–60 s | Uniform circular motion, tangent velocity, inward acceleration, radius projections, right-angle construction |

Run from the repository root:

```bash
.venv/bin/python my-project/skia-physics/render.py --overwrite
```

Output: `my-project/skia-physics/output/skia-physics.mp4`.

For focused inspection:

```bash
.venv/bin/python my-project/skia-physics/render.py --frame 35 --overwrite
.venv/bin/python my-project/skia-physics/render.py --preview --overwrite
.venv/bin/python my-project/skia-physics/render.py --range 44 50 --output /tmp/circular-motion.mp4 --overwrite
```

`--preview` exports source seconds 34–36. `--quality 4k` selects 3840 × 2160. Default export is 1080p at 30 FPS; source time is preserved for every sample. Each CLI export includes a JSON sidecar recording source range and renderer identity.

The inclined block is in equilibrium: `N = mg cos(theta)` and `f = mg sin(theta)`. Projectile position is quadratic in time and its velocity arrow follows the analytic derivative. The spring uses three sinusoidal cycles, with restoring force opposite displacement and velocity one quarter-cycle out of phase. Circular velocity is perpendicular to the radius and acceleration points inward. Vector lengths use diagram-specific scales.

Verification is limited to project lint, one representative frame from each study, and exported MP4 metadata/decode checks. No broad test suite or performance benchmark is needed for this scene.

Delivered export: H.264, 1920 × 1080, 30 FPS, 1,800 frames, exactly 60 seconds. Full FFmpeg decode completed without errors. Native Skia frames at 10.5, 19, 35, and 49 seconds were visually inspected; their contact sheet is `output/key-frames.jpg`. Project Ruff checks and `git diff --check` passed.
