# Electromagnetic Wave & Field Dynamics — Native Skia

A silent, **60-second, 1920 × 1080, 30 FPS** physics visualization on pure black (`#000000`). All visuals are procedural vector graphics and technical annotations rendered via Faceless Champ's native `skia-python` CPU backend. No external raster assets, web dependencies, or Docker containers are required.

## Narrative & Physical Acts

| Source Time | Movement | Mathematical Principles & Visuals |
| :--- | :--- | :--- |
| **0.0–16.5 s** | **3D Transverse Plane Wave** | 3D isometric frame ($X, Y, Z$). Propagating transverse electromagnetic wave: Electric field $\vec{E}$ in vertical plane (Cyan), Magnetic field $\vec{B}$ in horizontal plane (Gold), in-phase ($E_0 = c B_0$). Translucent gradient envelope ribbons, array of harmonic vector field arrows, wavelength caliper $\lambda = c/\nu$, and forward Poynting energy vector $\vec{S} = \frac{1}{\mu_0}(\vec{E} \times \vec{B})$. |
| **14.8–31.5 s** | **Wave Polarization & Helical Corkscrew** | Continuous phase shift $\Delta\phi: 0 \to \pi/2$ transforming a linear wave into a **Circularly Polarized Wave**. $\vec{E}(x, t)$ forms an undulating 3D spatial helix with orbiting radiant beads. Adjacent circular polarimeter reticle shows components $E_y$ and $E_z$ projecting onto a rotating resultant vector tracing a circular locus. |
| **29.8–46.5 s** | **Hertzian Dipole Radiation** | Central dipole antenna with metallic rods and oscillating charges ($+q(t)$, $-q(t)$) driving an alternating current $\vec{I}(t)$. Expanding closed electric field loops detaching and radiating outward at speed $c$. Toroidal radiation intensity envelope $I(\theta) \propto \frac{\sin^2\theta}{r^2}$ with zero-emission nodal axes along the antenna. |
| **44.8–60.0 s** | **Electromagnetic Spectrum & Maxwell Synthesis** | Seven-band continuous spectrum ribbon: Radio $\to$ Microwave $\to$ Infrared $\to$ Visible (rainbow dispersion) $\to$ Ultraviolet $\to$ X-Ray $\to$ Gamma Ray. Traveling wave packet demonstrating relativistic wavelength compression, with real-time telemetry ($\lambda$, $\nu$, $E = h\nu$). Overhead Maxwell's four differential equations. Fades to pure black at 60.0s. |

---

## Execution Instructions

Run from the repository root using the project virtual environment:

```bash
# Render a single still keyframe from each of the 4 acts:
.venv/bin/python my-project/skia-electromagnetic/render.py --frame 8.0 --overwrite    # Act I
.venv/bin/python my-project/skia-electromagnetic/render.py --frame 23.0 --overwrite   # Act II
.venv/bin/python my-project/skia-electromagnetic/render.py --frame 38.0 --overwrite   # Act III
.venv/bin/python my-project/skia-electromagnetic/render.py --frame 53.0 --overwrite   # Act IV

# Render two-second preview excerpt (source seconds 6–8, 720p):
.venv/bin/python my-project/skia-electromagnetic/render.py --preview --quality 720p --overwrite

# Render full 60-second video at 1080p (or custom range):
.venv/bin/python my-project/skia-electromagnetic/render.py --quality 1080p --overwrite
.venv/bin/python my-project/skia-electromagnetic/render.py --range 0 16 --output output/act1.mp4 --overwrite
```

*Note: The project is also accessible via the symlink `my-project/electromagnetic`.*

---

## Architecture & Verification

- `sample(t)` deterministically generates immutable Faceless Champ vector geometry directly from source time $t$, ensuring zero simulation drift and sample-rate independence.
- `ElectromagneticRenderer` implements the public renderer protocol delegating directly to Skia CPU vector rendering.
- Quality outputs (`720p`, `1080p`, `4k`) and custom framerates (`--fps`) scale dimensions while preserving geometry and temporal timing.
