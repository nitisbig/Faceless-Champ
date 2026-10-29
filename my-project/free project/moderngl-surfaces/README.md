# Procedural mathematical surfaces

15 seconds, black background, graphics only, silent. A fine luminous mesh evolves
from radial interference waves into a hyperbolic saddle, then curls into a
breathing torus. Traveling color gradients, a bright latitude pulse and a slow
camera orbit reveal its depth. The opening and closing fade to black.

Run from the repository root with native Python (no Docker):

```bash
.venv/bin/python my-project/moderngl-surfaces/render.py
```

Default output: `output/moderngl-surfaces.mp4` beside the script, 1920×1080,
30 FPS, exactly 15 seconds. Pass `--overwrite` to replace an existing output.

```bash
# One-second motion sample during the saddle → torus morph.
.venv/bin/python my-project/moderngl-surfaces/render.py --preview --quality 720p --fps 4

# Still frame, custom source range, or 4K export.
.venv/bin/python my-project/moderngl-surfaces/render.py --frame 12 --quality 720p
.venv/bin/python my-project/moderngl-surfaces/render.py --range 5 7 --quality 1080p
.venv/bin/python my-project/moderngl-surfaces/render.py --quality 4k
```

Requires the repository's native Python environment with its GPU dependencies
(`faceless-champ[gpu]`), working EGL/OpenGL 3.3+, and FFmpeg for video.

The project uploads a static 240×240 UV lattice once (115,200 triangles).
`surface.vert` evaluates positions and finite-difference normals in GLSL at the
requested source time. `surface.frag` shades the surface and draws derivative-
filtered parameter lines. A depth buffer handles the folding surface.

The project-local renderer shares the Faceless Champ ModernGL context. Since
custom GLSL/mesh components are not yet public library APIs, the viewport uses a
CPU readback / public `Image.from_source` bridge. Faceless Champ then applies
GPU bloom, composition and its normal video export. This is a test integration,
not a new core API or a zero-copy viewport. Seeking is deterministic and requires
no simulation history. Real-time playback speed depends on the OpenGL device;
the local EGL device reports Mesa llvmpipe (software).

Each rendered artifact has a JSON sidecar recording actual device/driver identity,
the surface shader hash, source range and `full_export_verified: false`.
Verification here is intentionally limited to two 720p stills, a one-second
720p/4 FPS morph preview and basic Python/format checks. An initial 12 FPS preview
was terminated before completion; the smaller sample checks video export and
the morph while keeping local testing bounded. The full export remains unrun.
