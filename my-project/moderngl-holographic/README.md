# Holographic wireframe & CAD

A 15-second silent turbine study on pure black, with no text. Cyan technical
meshes, translucent housing, rotating blade stacks, exploded retaining rings,
a mint scan band, dimensional ticks, and a perspective blueprint grid.

- 0–2s: upward scan assembles the hologram.
- 3–6s: collars separate and the rotor stages expand.
- 6–11.5s: the exploded assembly rotates under repeated scans.
- 11.5–14s: the parts return to their assembled positions.
- 14–15s: hold the assembled study with continued rotation and scanning.

Run from the repository root using native Python:

```bash
.venv/bin/python my-project/moderngl-holographic/render.py
```

Writes `output/moderngl-holographic.mp4` beside the script: 1920×1080, 30 FPS,
15 seconds. Add `--overwrite` to replace an existing output.

```bash
# Small motion check: source seconds 7–8, four frames.
.venv/bin/python my-project/moderngl-holographic/render.py --preview --quality 720p --fps 4

# Still, bounded excerpt, or full 4K output.
.venv/bin/python my-project/moderngl-holographic/render.py --frame 7.5 --quality 720p
.venv/bin/python my-project/moderngl-holographic/render.py --range 4 6
.venv/bin/python my-project/moderngl-holographic/render.py --quality 4k
```

Requires the repository Python environment with `faceless-champ[gpu]`, working
EGL/OpenGL 3.3+, and FFmpeg. No Docker or external assets are used.

The project uploads procedural meshes once, animates model matrices at source
time, and renders derivative-filtered wireframes and transparent surfaces with
additive GLSL shading. Its renderer shares the Faceless Champ ModernGL context.
The current library has no public custom mesh/shader component, so this test
uses a project-local viewport with readback into public `Image.from_source`,
then Faceless Champ GPU bloom, composition, progress reporting, and export.
This bridge is not zero-copy. No core library changes are required.

Each output includes a JSON sidecar with actual device identity, shader hash,
source interval and dimensions. Native EGL here reports Mesa llvmpipe (software
OpenGL); a GPU acceleration claim would require a hardware device.

Local verification is deliberately limited to two inspected 720p stills, one
one-second 720p/4 FPS preview, basic media metadata/decode checks, and Ruff.
The full 15-second export has not been rendered or verified; sidecars retain
`full_export_verified: false`.
