# Mathematical camera / native Manim integration

45 seconds, pure black (`#000000`), 16:9. A layered oscillating curve leads into
a small region, a secant converges to a tangent, and the camera tracks the
moving point. The linear approximation becomes a quadratic approximation;
a second close-up and pullback reveal local agreement and later divergence.
Only essential mathematical labels and equations appear. No audio or LaTeX.

Run from the repository root with native Python (Manim 0.22, FFmpeg/ffprobe):

```bash
# Key testing: prepare 180 low-rate frames and composite ten PNGs.
.venv/bin/python my-project/manim-camera/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Optional full 45-second preview, 640×360 / 15 fps.
.venv/bin/python my-project/manim-camera/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python

# Full export, 1920×1080 / 30 fps.
.venv/bin/python my-project/manim-camera/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

The example interpreter is temporary; choose your native Manim environment with
`--manim-python` or `FC_MANIM_PYTHON`. The main process uses FacelessChamp's
public `prepare_manim` → `Viewport` → `render` path. Outputs and immutable
preparation caches live under `output/`. Use `--overwrite` to replace an MP4.

Timing: 0–6s overview and callout; 6–10s zoom; 10–15s secant limit;
15–18s focus tracking; 18–25s equation isolation and transformation;
25–32s return to geometry and quadratic correction; 32–40s close-up and
pullback; 40–45s final equation and hold.

`--frames` checks composition and duration at 4 fps; it does not establish
full-rate motion quality or a completed full MP4 export.
