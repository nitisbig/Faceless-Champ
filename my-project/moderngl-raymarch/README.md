# Ray-marched 3D objects

A 15-second, silent, graphics-only ModernGL integration scene for Faceless Champ.
The canvas is pure `#000000`; no headings, labels, or subtitles are drawn.

## Run with native Python

From the repository root, using the existing `.venv`:

```bash
# Full 15-second export: 1920×1080, 30 fps
.venv/bin/python my-project/moderngl-raymarch/render.py

# Small verification export: source seconds 9–10, 720p, 12 fps
.venv/bin/python my-project/moderngl-raymarch/render.py --preview --quality 720p --fps 12

# Individual frame, or a custom interval
.venv/bin/python my-project/moderngl-raymarch/render.py --frame 11.8 --quality 720p
.venv/bin/python my-project/moderngl-raymarch/render.py --range 3 5 --quality 1080p
```

Outputs go into `output/`. Use `--overwrite` to replace an existing output.
`--quality 4k`, `--fps`, and `--output` are also supported. No Docker is used.
Requires the repository's GPU dependencies, an EGL/OpenGL 3.3+ driver, and FFmpeg
for MP4 export. Mesa software OpenGL works but can render this shader slowly.

## Visual sequence

- 0–3.5s: orbiting spheres merge with smooth SDF unions into one continuous body.
- 3.6–5.7s: the sphere morphs into a softly rounded cube.
- 6.1–8.2s: the cube opens into a thick torus.
- 9–11.7s: the torus becomes a rounded cube with three intersecting tunnels.
- 12–15s: the tunnelled sculpture rotates with restrained procedural surface motion.

The continuous source clock controls every frame; there is no simulation state.
The fragment shader performs bounded sphere tracing, finite-difference normals,
ambient occlusion, soft self-shadowing, and three colored GGX-style lights.
Teal, warm metal, and violet highlights reveal the changing geometry.

## Integration and verification

`build_scene()` owns the Faceless Champ canvas and 15-second duration.
`RaymarchRenderer` uses the context from `create_renderer("moderngl")` for a
project-local fullscreen GLSL pass. Its RGBA readback becomes a public `Image`
with subtle public `Bloom`, composed by the native ModernGL renderer and exported
through Faceless Champ's `render`/`ExportSettings`/`ExportProgress` APIs.
The bridge follows existing project examples; the library currently exposes no
public custom GLSL component. The scene does not change library code.

JSON sidecars record actual backend/driver identity, shader hashes, source range,
resolution, and FPS. The initial verification is intentionally limited to shader
compilation, scene duration, representative frames, and a one-second preview.
The local EGL driver is Mesa llvmpipe (software OpenGL); hardware acceleration
and the full 15-second export have not been verified. `full_export_verified`
remains false in export sidecars until a full output is separately inspected.
