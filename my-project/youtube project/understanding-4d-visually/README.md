# Understanding 4D Visually

An 8:30 explainer (8 chapters, 30 scenes) that turns real cheetah footage into a 4D explanation: vectors, the
tesseract, slices, shadows as projection matrices, and rotation in planes. The production plan, with cue-snapped
timings and build stages, is in [scene-plan.md](scene-plan.md). Narration: `audio.mp3`; timing: `cue-per-word.srt`.

## Run (from this folder, with the repo's venv)

```bash
../../../.venv/bin/python prepare_media.py                          # once: crop the timer, build full/thumb/opener JPEGs
../../../.venv/bin/python render.py --chapter test --stills         # Stage A component sheet, 720p stills
../../../.venv/bin/python render.py --chapter 0 --frame 12.4 30.0   # specific narration seconds
../../../.venv/bin/python render.py --chapter 0 --preview           # 720p MP4 with narration
../../../.venv/bin/python render.py --chapter full --preview        # whole video, 720p (once chapters exist)
../../../.venv/bin/python smoke_tests.py                            # PyVista + Manim engine checks
```

`--chapter` takes `0`–`7` (as each stage lands), `full`, `test` (the Stage A sheet) or `s01` (the original 25 s demo).
The build sessions render 720p previews only. Run `--final` (1080p, motion blur on) or `--final --quality 4k` yourself.

## Layout

| File | Role |
|---|---|
| `theme.py` | Colour tokens (x red, y orange, z yellow, blue = time / w) and the Faceless Champ theme |
| `cues.py` | `cue(n)` / `word()` on the narration clock; `AUDIO_DURATION` 510.0, `TOTAL` 530.0 with the end screen |
| `fx.py` | Skia `Frame` (quarter-res glow layer), letterbox, vignette, grain, plus `dashed`, `blurred` (depth of field), `light_sweep`, `light_cone`, `glint`, `chroma`/`chroma_kick`, `motion_blur`, `text_path` |
| `space.py` | Pinhole `Camera`, `orbit`, rotations, `text3d`, `to_view` (math z-up → view y-up), `Spline`/`orbit_path` camera moves |
| `typmath.py` | **The math engine.** Typst math as skia paths: `draw`, `morph` (matching glyphs fly), `number` (live values from a cached digit strip), `tc` (colour a sub-term by token). Needs the Typst CLI on PATH |
| `mathtype.py` | Matplotlib MathText (STIX) as skia paths, copied from the convolution project; legacy fallback |
| `components/tesseract.py` | The Tesseract Rig: vertices, 32 edges, 24 squares, 8 cells, `rot4`/`rotation`, perspective and orthographic projection, real corner-first slices (`ConvexHull`), drawing, trails, glass cells |
| `components/vector_slot.py` | Column vectors with axis-coloured slots, growing slots and the 2,000-entry stream |
| `components/matrix_plaque.py` | Matrices on glass cards with row, column and block highlights; `zw_rotation_cells()` |
| `components/slice_plane.py` | The Blue Slice Plane (rim, shimmer, corner ticks) and cut lines |
| `components/cheetah_block.py` | Footage frames stacked into a block of time, slice playback, block axes, `track()` (the cheetah's position per frame, for the world-line) |
| `components/cards.py` | The 2.5D glass card arc (S26, S28): perspective card space, trucking focus, depth of field, collapse |
| `components/hud.py` | Lit glass cards (cached), pills, tabular readouts, eyebrows, 2D/3D arrows, axes, right-angle marks, dot floors |
| `pv3d/` | PyVista offscreen renders camera-matched to `space.Camera` (`render`, `composite`) and meshes (`solids`, including the S26 `spacecraft`) |
| `manim/` | Optional Manim fallback (STIX `Text`; no LaTeX on this machine) and its fonts |
| `scenes/` | `chN_*.py` chapters (one `FunctionSource` each), `full.py`, `stage_a_test.py`, `s01_cinematic.py` (reference) |
| `render.py` | Chapter CLI: stills / frame / preview / final |
| `smoke_tests.py` | Engine checks: PyVista alignment and look, Manim prepare and overlay |
| `media/` | `cheetah.mp4`, `cheetah_frames/`, and `prepared/` (generated) |

## FacelessChamp gaps this project hit
1. **No `VideoSource`.** Smooth footage needs an ffmpeg prepare step and a hand-written JPEG cache (`media.py`).
2. **No cinematic finish primitives**: letterbox, vignette, film grain, light sweeps, glints and motion blur are custom Skia here.
3. **No 3D camera or depth-sorted image planes in core or Kit.** `space.py` is now duplicated across two projects;
   promote `Camera`/`orbit`/`text3d`, plus a homography `image_quad`, into Kit.
4. **No camera-path helper.** A Hermite/Catmull-Rom spline over keyframes (`space.Spline`) is the natural API for continuous moves.
5. **No planar shadow / light helpers.** The point-light shadow, hull and light pool are about 60 lines that recur in any 3D explainer.
6. **No camera bridge between Skia 3D and PyVista.** `pv3d/render.py` matches field of view and principal point, and mirrors
   the scene in x because `space.Camera` is left-handed.
