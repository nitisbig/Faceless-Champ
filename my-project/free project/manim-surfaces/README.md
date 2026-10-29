# 3D mathematical surfaces / native Manim integration

A 45-second saddle study on pure black (`#000000`), with an orbiting camera,
3D axes, partial-derivative cross-sections and tangent vectors, a moving tangent
plane, a unit-direction surface normal, and a gradient on the projected domain.
The point completes a circuit and returns to the saddle's stationary origin.
Only mathematical labels appear. No narration or LaTeX dependency.

Manim prepares the animation through the public FacelessChamp adapter.
FacelessChamp places the prepared frames in a `Viewport`, owns the 45-second
timeline, and exports the MP4. Native Python only.

Run from the repository root:

```bash
# Key verification: 90 low-resolution prepared frames, seven composited PNGs.
.venv/bin/python my-project/manim-surfaces/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Optional full preview: 640×360, 15 fps.
.venv/bin/python my-project/manim-surfaces/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python

# Full export: 1920×1080, 30 fps.
.venv/bin/python my-project/manim-surfaces/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

The example producer environment is temporary. Use `--manim-python` or
`FC_MANIM_PYTHON` to select another native Manim 0.22 environment. FFmpeg and
ffprobe must be available on PATH. Outputs and immutable preparation caches
live in `output/` beside the scripts. Pass `--overwrite` to replace an MP4.

Preparation allows two hours by default, rather than the adapter's ten-minute
default. Native Cairo rendering of the 3D meshes at 1080p can take tens of minutes.
Use `--manim-timeout 14400` to allow four hours on a slower machine. This deadline
includes rendering and frame extraction; it does not change the 45-second video.
A timed-out preparation must restart; incomplete work is not a resumable cache.

Timing: 0–8s reveal and orbit; 8–14s x partial; 14–20s y partial;
20–27s tangent plane and normal; 27–36s projected gradient and moving point;
36–42s approach the stationary point; 42–45s final orbit over its flat tangent plane.

`--frames` checks the complete timeline at 2 fps with a 14×14 surface mesh and
saves seven images after FacelessChamp composition. Preview and production
exports use a 24×24 mesh. This check does not export a full preview or production MP4.

Verified locally with native Manim 0.22: a 45-second/90-frame prepared source,
seven inspected FacelessChamp-composited frames, pure-black corners, numerical
gradient and tangent-contact checks, and Ruff. The contact sheet is saved to
`output/keyframes.jpg`. Full preview and 1080p exports have not been run.
