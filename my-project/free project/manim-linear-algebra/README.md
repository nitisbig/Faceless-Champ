# Matrix transformations

A 45-second native Manim producer prepared through FacelessChamp's public
`prepare_manim` API and composited using `Viewport`. Pure black, no titles or
subtitles, no audio. Matrix columns and basis arrows share cyan/pink colors;
the gold vector is their sum. Matrix entries update throughout each transformation.
Geometry and Pango text require no LaTeX.

Timing: 0–3 introduction; 3–12 rotation by 60°; 12–14 reset;
14–23 stretch by (1.6, 0.65); 23–25 reset; 25–34 horizontal shear by 0.8;
34–36 reset; 36–42 apply R, then S, then H; 42–45 hold HSR.
The displayed matrix is the cumulative map from the original coordinates.

From the repository root, use a native Python environment with Manim 0.22:

```bash
# Key testing: prepare 640×360/15 source, then save five FacelessChamp frames.
.venv/bin/python my-project/manim-linear-algebra/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Optional full preview or 1080p30 export (each prepares its own source profile).
.venv/bin/python my-project/manim-linear-algebra/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python
.venv/bin/python my-project/manim-linear-algebra/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

Replace the temporary environment path with your own persistent native Manim
environment, or set `FC_MANIM_PYTHON`. FFmpeg and ffprobe must be on PATH.
Preparation caches the full low-resolution 45-second source even in `--frames`
mode; that mode does not export a final MP4. Outputs live in this folder's
`output/` directory. Existing MP4s require `--overwrite`.
