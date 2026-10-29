# Cinematic Shader Transitions

A silent 15-second, 1920×1080, 30 fps scene on pure `#000000`.
Only the wave equation appears as text.

- **0–3s:** luminous wave equation settles into view.
- **3–7.7s:** equation particles dissolve, curl and reform into a 3D wave surface. Radial distortion, displacement, chromatic aberration, multi-tap blur and two brief glitch accents drive the transition.
- **7.7–13.5s:** a cyan/magenta wave mesh evolves under a slow orbit.
- **13.5–15s:** fade to black.

The deterministic mesh and particle motion run in project-local GLSL. A GPU post pass supplies the transition effects; the public Faceless Champ Image/EffectStack pipeline adds ModernGL bloom and exports through the normal renderer interface. Custom shaders stay project-local because the library does not yet expose a public custom GLSL component.

Run from the repository root using native Python:

```bash
.venv/bin/python my-project/moderngl-transitions/render.py
```

Default output: `output/moderngl-transitions.mp4` (relative to this project).

```bash
# One-second excerpt of the dissolve at source time 5–6s
.venv/bin/python my-project/moderngl-transitions/render.py --preview --quality 720p --fps 12
# Still or chosen interval
.venv/bin/python my-project/moderngl-transitions/render.py --frame 10 --quality 720p
.venv/bin/python my-project/moderngl-transitions/render.py --range 3 8 --quality 1080p
# Full 4K/30 export
.venv/bin/python my-project/moderngl-transitions/render.py --quality 4k --fps 30
```

Use `--overwrite` to replace an existing file. Each render records its actual renderer, shader hash, source interval and settings in a JSON sidecar. Verification here is limited to representative stills and a short excerpt; the complete export is unverified. The local execution device is Mesa llvmpipe (software OpenGL), so hardware acceleration has not been verified.
