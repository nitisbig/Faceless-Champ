# Black hole visualizer

A 30-second, 1920×1080 Faceless Champ scene built on a GPU Schwarzschild ray tracer.
Every pixel of the black hole is a photon integrated through curved spacetime. Nothing
in it is a painted effect.

## Files

| File | Role |
| --- | --- |
| `physics.py` | Mathematical model: metric quantities, photon geodesics (CPU), Shakura–Sunyaev disk, Doppler/gravitational redshift, blackbody → sRGB LUT from CIE 1931 fits |
| `shaders/blackhole.frag` | Simulator kernel: per-pixel null geodesics, thin-disk emission at every equatorial crossing, lensed star field, filmic tonemap |
| `engine.py` | `CameraRig` (Catmull–Rom keyframes, projection, shadow size) and `BlackHoleEngine` (headless ModernGL/EGL), exposed as a `FunctionSource` |
| `scene.py` | Faceless Champ scene: overlays, 2D geodesic diagram, HUD, callouts, CLI |

## Model

Units are G = c = M = 1, with the horizon at r = 2 (1 rs).

- Light: `x'' = -3 h² x / r⁵` reproduces the exact Binet orbit `u'' + u = 3u²`. It is
  integrated with velocity-Verlet using adaptive steps. `python physics.py` checks the
  capture threshold against the analytic `b = 3√3 M` and the bending angle against `4M/b`.
- Disk: Keplerian, from the ISCO (6M) to 21M. `T⁴ ∝ r⁻³(1 − √(6/r))`, with a peak of 4300 K at 8.17M.
- Observed light: `g = √(1 − 3/r) / (1 − Ωλ)`. The colour is a blackbody at `g·T`, and
  the brightness scales as `g⁴ T⁴`. The approaching side is blueshifted and boosted.
  Higher-order images (the lensed far side and the photon ring) come out of the
  integration on their own.

## Timeline

| Time | Beat |
| --- | --- |
| 0–6.5 s | Approach from 78M, near edge-on; title |
| 7–14.5 s | Hole parked right (lens shift). A 2D card shows true photon paths from `physics.trace_planar_ray`, with the horizon, photon sphere and ISCO |
| 16–20.5 s | Callouts on the 3D image: photon ring, approaching and receding sides (placed with the rig projection) |
| 21–25 s | Swing to a polar view |
| 25–30 s | Dive to 7.5 rs; closing line; fade |

The HUD readouts (distance and static-observer clock rate `√(1 − rs/r)`) come from the same camera rig as the tracer, sampled every 0.25 s.

## Run

From the repository root, using `.venv`:

```bash
python my-project/black-hole-visualizer/scene.py --frame 3 10.5 19 27.8   # 720p stills
python my-project/black-hole-visualizer/scene.py --preview 6 11            # 720p excerpt
python my-project/black-hole-visualizer/scene.py --audit                   # overlay design audit
python my-project/black-hole-visualizer/scene.py                           # full 1080p, 2×2 SSAA, CRF 14
python my-project/black-hole-visualizer/scene.py --quality 4k --samples 2  # 4K master
```

Compositing uses the ModernGL backend (`antialias=1`, GPU bloom). The tracer has its
own EGL context. On an AMD R4, a 720p frame traces in about 0.1 s, and a 720p preview
exports at about 0.37 s per frame.
