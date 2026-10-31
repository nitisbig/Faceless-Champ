# Understanding 4D visually — 45 s preview

1920 × 1080, 30 FPS, Skia CPU backend, `midnight` theme. Silent.

| Source time | What happens |
| --- | --- |
| 0–3 s | A point stretches into a line (red = x). Bottom label `1D · a line (x)` |
| 3–6 s | The line sweeps into a square (orange = y) |
| 6.4–9.5 s | The square extrudes into a cube (yellow = z) that sways in 3D |
| 9.6–15 s | The cube extrudes along **w** (blue) into a tesseract. From 11.6 s the video frames stack onto w-slices one by one, then play frame by frame. The newest frame is bright, older frames trail as ghosts. "Each slice is one moment in time" |
| 15–16.6 s | The visual shrinks into the centre card and the title appears |
| 17–24 s | Left: column vector `x y z w` (w pulses), "Four numbers, one point". Right: x/y/z axes, then a floating blue w arrow, "At 90° to x, y and z" |
| 24–32 s | Left: dim / vertices / edges table, one row every 2 s. The matching vertices pulse in the tesseract on each beat. Then `V = 2^n, E = n·2^(n−1)` |
| 32–45 s | Right: 4 × 4 ZW rotation matrix and a live θ read-out. It uses the same `theta_zw()` that drives the visual |
| 39.4–45 s | Projection formula `x' = d/(d−w)·x`. The title changes to "Moving along w is moving through time" |

## Run (from the repository root)

```bash
.venv/bin/python "my-project/free project/4d-visual-preview/render.py" --frame 20 --overwrite
.venv/bin/python "my-project/free project/4d-visual-preview/render.py" --preview --overwrite   # 13–19 s, the shrink
.venv/bin/python "my-project/free project/4d-visual-preview/render.py" --overwrite             # full 45 s
```

Output: `output/4d-preview.mp4`. Use `--range START END --output PATH` to export a section on the original clock.

## Using the real cheetah clip

Put the frames in `frames/` as `0001.png`, `0002.png`, … (png, jpg or webp, sorted by name). They are resized to
480 × 300 and replace the procedural cat automatically. To extract frames from a video:

```bash
ffmpeg -i cheetah.mp4 -vf "fps=12,scale=480:300:force_original_aspect_ratio=increase,crop=480:300" frames/%04d.png
```

`CLIP_FPS` (12) and `SLICE_COUNT` (7) are in `dimension_source.py`. Run `python sample_frames.py` to write a contact sheet of the frames in use.

## Files

- `render.py`: scene, layout, timing and CLI. Uses only public Faceless Champ components.
- `dimension_source.py`: one `FunctionSource`. The 16 vertices and 32 edges of a 4-cube are drawn with unextruded
  axes squashed to zero, so the point, line, square, cube and tesseract are one continuous object. Edge colour =
  the axis the edge runs along. Video frames are warped onto the slices with `skia.Matrix.setPolyToPoly`.
- `sample_frames.py`: frame loader plus a procedural placeholder clip.

## FacelessChamp gaps found while building this (to optimise later)

1. **No video-file source.** `PreparedFrameSource` plays only a fingerprinted RGBA-PNG manifest. Nothing decodes an
   `.mp4` or a plain folder of frames. A `VideoSource("cheetah.mp4")` (ffmpeg decode, `RasterSource`) plus
   `ImageSequence("frames/*.png", fps=)` would replace `sample_frames.py`.
2. **No textured quad / perspective image warp.** Pinning an image to 4 projected corners needed raw
   `skia.Matrix.setPolyToPoly` inside a `FunctionSource`. A `QuadImage(image, corners)` would make this declarative.
3. **No lightweight N-D / 3D wireframe primitive.** ArchChamp needs PyVista. A `Wireframe(vertices, edges, rotation=,
   camera=)` with N-D rotations and perspective, built on core paths, would turn the tesseract into components
   (per-edge Draw, labelled vertices, audit-aware).
4. **Matrices need Typst, which isn't installed.** `Equation(engine="mathtext")` can't do `\begin{bmatrix}`, so
   the matrix here is a grid of single Equations plus hand-drawn bracket paths. A `Matrix(cells, brackets="[")`
   primitive, or a bundled Typst, would fix this. Mathtext also spaces `x^{\prime}` badly.
5. **No shared-element "shrink to slot" helper.** The shrink is hand-authored scale + position keyframes.
   Something like `scene.morph_to(view, bounds, run_time=, rate_func=)` would cover this common reveal.
6. **The audit counts math symbols as words.** `TEXT_CLUTTER` fires at ~31–36 s because the 16 matrix cells count
   as words. Equations should probably be weighted differently.
7. **`assets/sfx` holds no sound effects** (only `equation-render/`). There are no whooshes or ticks for the shrink or the w-arrow beat.
