# Understanding 4D Visually — Scene Plan

**Project folder:** `my-project/youtube project/understanding-4d-visually/`
**Audio:** `audio.mp3`, 510.00 s (08:30.000). Narration ends at 509.8 s, followed by a 20 s end-screen hold (total 530.0 s).
**Timing sources:** `cue-per-word.srt` (1,439 word cues, used for anchors) and `normal-subtitle.srt` (phrase lines).
**Canvas:** 1920 × 1080, 30 fps, background pure black `#000000`. Previews are 720p; the final is 1080p locally and 4K on Kaggle.
**Library:** Faceless Champ core + kit (`faceless_champ`, `facelesschamp_kit`), with project modules `fx.py`, `space.py`, `media.py`, `theme.py`.
**Footage:** `media/cheetah.mp4` (1920 × 1080, 24 fps, 25.17 s) and `media/cheetah_frames/` (126 frames at 5 fps).
`prepare_media.py` crops the burned-in timer from every derived image.

All timecodes are **source-clock** times in the narration (mm:ss.mmm). Scene boundaries are snapped to word cues, and
`#N` is the one-based cue index in `cue-per-word.srt`. Each visual beat lands 0.15 s before its cue (`cue(N) - 0.15`).

> **The SRT text has ASR errors. The audio is correct.** Anchor these cues by **index**, never with `word()` text matching:
> #226–228 "three to five" = *three, two, five* · #328 "Three pixel" = *Every pixel* · #457 "end" = *n* ·
> #553 "Third" = *And* · #793 "Just" = *Slices* · #948 "Find" = *Join* · #1254 "This" = *Physics* · #1278 "An" = *And* ·
> "tesoract" (#1159, #1307, #1353) = *tesseract*. #1102/#1105/#1108/#1111/#1175 are digits in the SRT but spoken as words.
> Fix the subtitle text before uploading captions to YouTube.

> The existing 25 s demo (`scenes/s01_cinematic.py`) is the visual prototype for S01–S02. Its beats are kept but re-timed
> from silent clock times to the cues below. Chapter 0 replaces it as `scenes/ch0_intro.py`.

---

## 1. Visual system (applies to every scene)

### 1.1 Look

- **Mood:** "a black stage, light in a void." Pure black, razor-thin luminous geometry, and very high contrast. The cheetah
  footage is the only "real" thing in the film. Everything else is light. Lots of negative space and at most one focal point
  per frame. Non-focal elements stay at 40 % opacity or less.
- **Depth vocabulary:** **2D** for arithmetic, formulas and plots. **2.5D** (tilted glass cards, perspective planes, parallax
  layers, depth of field) for comparisons and recaps. **True 3D** (a perspective camera with eased orbits) for every object
  that has depth, and **4D** objects are always shown as live projections of real 4D coordinates.
- **Floors:** where a shadow or a space needs grounding, use a faint perspective dot grid (spacing 0.5 units,
  opacity 0.10 or less) that fades with distance. No textures or gradient backgrounds. The black stays black.

### 1.2 Semantic color (never break this mapping)

Defined once in `theme.py` (already present: `TOKENS`, scheme `tesseract-noir`). Scene code uses token names only, never hex values.

| Token | Hex | Meaning everywhere in the video |
| --- | --- | --- |
| `x` | `#FF5A4E` red | the x direction, x coordinates, x edges |
| `y` | `#FF9F3D` orange | the y direction |
| `z` | `#FFD17E` warm yellow | the z direction (vertical "height" in teaching scenes) |
| `w` | `#5FB6FF` electric blue | **the extra direction.** Time while the cheetah frames stack, then w. Also slices and the slicing plane, since slices are taken along w |
| `ink` | `#F5F7FA` | primary text, lengths, diagonals, results, "the whole object" |
| `muted` | `#7C8597` | secondary labels, ticks |
| `grid` / `line` | `#1C2433` / `#2A3140` | floors, tracks, plaque borders |
| `light` | `#FFE9C7` | the light source, light cones, specular glints |

- **Rotation planes** are two-axis gradients. xy = red→orange, xz = red→yellow, xw = red→blue, yz = orange→yellow,
  yw = orange→blue, zw = yellow→blue. A plane is "made of" its two axes, so the color teaches it.
- **Edges are colored by the axis they run along.** For the tesseract, an edge's axis is the one coordinate in which its
  two corners differ. This rule holds from S08 onward, so viewers can always read the w-edges (blue) in any projection.
- **Coordinate convention:** in teaching scenes, x = right, y = forward, z = up (this matches the ant in S04 and the
  "height" in S17). `space.py` is y-up on screen, so all world points go through one helper,
  `to_view(p) = (x, z, y)`. Never swap axes ad hoc.

### 1.3 Typography

- Display / title lockups: **Space Grotesk** (`display`), tracking +0.02.
- Labels, readouts and pills: **DM Sans** (`sans`). All numerals in readouts and counters use tabular figures so they don't jitter.
- Axis letters and θ: **Cormorant Garamond Italic** (`italic`), colored by axis.
- Math: **Typst** (New Computer Modern Math) through `typmath.py` for every formula, matrix, vector entry and morph,
  so the whole film shares one math typeface. Live numbers use its cached digit strip (`typmath.number`), so they never
  recompile. Greek in readout labels (θ) also goes through Typst: DM Sans has no Greek glyphs.
- Text budget: on-screen text is a label, never the transcript. Titles are 6 words or fewer, labels 4 words or fewer. Formulas and
  numbers carry the teaching.

### 1.4 Motion language

- Entrances use emphasized easing (`fx.back` or ease-out, 0.45–0.7 s). Exits use accelerate, 0.3 s. Physical moves (drags, docks,
  card flips) use a slightly under-damped spring settle.
- **The "drag" is the hero motion of the film** (S08, S10, S28): it eases in, leaves a short sweep trail with motion blur, and settles with a tiny overshoot.
- One idea per beat. Remove the old idea before the next arrives.
- Each 3D shot has one continuous, eased camera move (a Hermite spline over keyframes, as in `s01_cinematic._spline`). Never cut inside a 3D move.

### 1.5 Premium finish (an After Effects-grade pipeline, built in Skia)

| Effect | Implementation | Where |
| --- | --- | --- |
| Two-scale bloom and glow | `fx.Frame` quarter-res glow canvas (exists) plus an optional final `Layer(EffectStack(bloom=Bloom(radius=10, threshold=0.62)))` | everywhere, only on hero strokes |
| Light sweep | a gradient band clipped to the shape (`fx.light_sweep`, new). Optional `EffectStack(light_sweep=LightSweep)` | title lockup, octahedron, cube-in-cube, end card |
| Chromatic-aberration kick | an RGB split of 0.15 s on reveals (`fx.chroma_kick`, new; or `ChromaticAberration`) | w arrow, tesseract birth, "Exactly two", "six" |
| Motion blur | subframe accumulation, 4–6 samples, 180° shutter (`fx.motion_blur(draw, t)`, new). Off in previews | fast drags, ZW and double rotations |
| Depth of field | per-layer Gaussian blur by camera depth (2.5D card stacks, Cheetah Block rack focus) | S07, S15B, S26, S28 |
| Volumetric light | additive radial and cone gradients from the `light` token, plus a lens glint and anamorphic streak | S02, S17 |
| Glass plaques | dark translucent card, 1 px gradient border, inner glow; Skia `Lighting(light="distant", bevel=6, specular=0.5)` and `Morphology(dilate)` for the rim | every matrix, vector and stats card |
| Motion trails | fading polyline of past vertex positions (exact, evaluated at t − k·dt) | rotations S24–S25 |
| Parallax dust | sparse depth-sorted points drifting slowly (skia; `ParticleField` if the moderngl backend is used) | hero 3D shots only, 6 % opacity or less |
| Cinematic finish | `fr.letterbox` (footage acts only), `fr.vignette(0.5)`, `fr.grain(t, 0.045)` at 24 fps | footage scenes; vignette and grain everywhere |

### 1.6 Recurring motifs (build once, reuse everywhere)

1. **Tesseract Rig** (`components/tesseract.py`): the single source of truth for the 4D model. It holds the 16 vertices in
   {0, 1}⁴ (centered), 32 edges (Hamming distance 1, colored by axis), 24 squares, 8 cells, `rotate4(planes, angles)`,
   `project_persp(d)` and `project_ortho()`. Every count on screen is computed from it, never typed.
2. **Vector Slot** (`components/vector_slot.py`): a column vector whose slots are colored by axis. It can grow a slot
   (x y z → w → … n), fill digits per cue, and stream thousands of slots into depth (S12, S27).
3. **Matrix Plaque** (`components/matrix_plaque.py`): a glass card holding a matrix. It supports row and column highlights, live
   cos/sin values, block glows (zw block), and "docking" one matrix into another (S24).
4. **Blue Slice Plane** (`components/slice_plane.py`): a translucent blue plane with a bright edge, scan shimmer and a cut line.
   Used in S01, S14–S16, S29.
5. **Cheetah Block** (`components/cheetah_block.py`): factored out of `s01_cinematic.py`. It covers the footage → loose frame →
   stacked translucent sheets → slice playback. Used in S01, S07, S15B, S19A, S26B, S29.
6. **Eyebrow** (`hud.eyebrow`): a corner chapter marker (see §1.7).

### 1.7 Chapter markers

The narration is continuous, so there are no title cards that stop the audio. Each chapter opens with a top-left eyebrow
(`label` role, muted, 2.5 s): `01 · DIMENSIONS`, `02 · BUILD A TESSERACT`, `03 · SLICES`, `04 · SHADOWS`, `05 · ROTATION`,
`06 · WHY IT MATTERS`, `07 · RECAP`. Chapter changes use an **in-frame transition** drawn inside the frame function
(zoom-blur push, w-slice wipe or iris), because `Sequence` transitions need an overlap that would break the single
narration clock.

---

## 2. Engine map

| Engine / feature | Faceless Champ entry point | Used for |
| --- | --- | --- |
| **skia-python** (main renderer) | one `FunctionSource(draw, size, duration, key)` per chapter, drawing into `fx.Frame` (crisp canvas plus glow canvas); `space.Camera`/`orbit`/`text3d` for 3D wireframes; `fr.image_quad` for footage on 3D planes | all 2D, 2.5D and wireframe 3D: the tesseract projections, axes, vectors, plaques, HUD, footage planes and transitions |
| **numpy / scipy** | inside the frame functions | **real computation, never faked:** 4D rotation matrices, perspective and orthographic projection, `scipy.spatial.ConvexHull` slice solids, sphere slice radii, PCA projection of the embedding cloud |
| **PyVista** (VTK 9.7, offscreen) | `pv3d/render.py` (`render(meshes, cam, size)` → cached RGBA in `output/cache/pyvista/`, `composite(fr, rgba)`) draws lit solids **under** the skia glow edges of the same frame. The camera matches `space.Camera`: same eye, target, `view_angle = 2·atan(540/focal)`, and the principal point as a window-centre shift. `space.Camera` is left-handed, so the VTK scene is mirrored in x (verified: ≤ 1.1 px bbox error at 720p, `smoke_tests.py --pyvista`) | lit glass and PBR solids: the falling sphere (S14), the 4D-ball slice sphere (S15), corner-first slice solids (S16), the shadow-casting glass cube (S17), the quaternion spacecraft (S26) |
| **Typst** (CLI 0.15, `~/.local/bin/typst`) | `typmath.py`: `draw(fr, expr, …)`, `morph(fr, a, b, u, …)` (matching glyphs fly, the rest cross-fade), `number()` for live values, `tc(token, body)` to colour sub-terms. Expressions compile once to SVG via `faceless_champ.typst_math` (disk cache) and become skia paths | every formula: vectors, the matrix plaques, x′ = d/(d−w)·x, ‖v‖, 2ⁿ, the edge equations, and the four morph sequences: √(1²+1²) → √2 → √3 → √4 = 2 (S12), the 2×2 rotation build (S21), n(n−1)/2 → 6 (S23), the 4×4 ZW assembly (S24A) |
| **Manim** (0.22, Cairo, optional) | `prepare_manim(ManimSceneSpec(...))` → `PreparedFrameSource` → `Viewport` over the chapter layer. No LaTeX here, so only STIX `Text` (verified: `smoke_tests.py --manim`) | kept as a fallback for any choreography `typmath.morph` cannot do; not needed by any scene so far |
| **ModernGL** (optional) | `ExportSettings(backend="auto")` plus a composite `Layer(EffectStack(bloom=Bloom, chromatic=ChromaticAberration, light_sweep=LightSweep))`; CPU fallback through `[effects]` | the final composite bloom only. This machine has an integrated AMD Radeon R4 (Mesa OpenGL 4.5), not a discrete GPU, so previews use `backend="skia"`; try `auto` only for finals |
| **Narration** | `cues.py` (`cue(n)`, `word(text, after)`), `SubtitleTrack.from_srt`; `scenes/full.py` chains the chapters with `check_contiguous` and one continuous audio `Layer` | source-clock sync |

**Not available:** LaTeX is not installed, so no Manim `MathTex`. Use Typst syntax everywhere (`a/b`, `sqrt(x)`, `mat(1, 0; 0, 1)`, `theta`, `dot`, `norm(v)`).
**Compositing order per frame:** PyVista solid (if any) → skia geometry → glow canvas → Manim overlay (if ever used) → vignette and grain.
**PyVista look rules:** black transparent background, no floor mesh, no default light kit. Use one key light (warm `light`) and
one blue rim light. Glass is `opacity 0.18–0.30`, `metallic 0.0`, `roughness 0.08`. Edges are **not** drawn in VTK; skia
draws them on top from the same coordinates, so the lines stay razor-sharp and match the rest of the film.

---

## 3. Chapter map

| # | Chapter | Span | Scenes | Dimension |
| --- | --- | --- | --- | --- |
| 0 | Cold open: the cheetah and the shadow | 00:00.000 – 00:49.560 (#142) | S01–S03 | footage → 3D → 4D |
| 1 | What is a dimension? | 00:49.560 – 02:03.040 (#365) | S04–S07 | 2.5D → 3D, 2D |
| 2 | Building the tesseract | 02:03.040 – 03:37.120 (#630) | S08–S12 | 3D/4D, 2D + Typst |
| 3 | Slices | 03:37.120 – 04:36.590 (#793) | S13–S16 | 2.5D, 3D (PyVista) |
| 4 | Shadows are linear algebra | 04:36.590 – 05:41.280 (#976) | S17–S20 | 3D, 2D |
| 5 | Rotation | 05:41.280 – 07:13.760 (#1233) | S21–S25 | 2D, 3D, 4D + Typst |
| 6 | Why it matters | 07:13.760 – 07:45.680 (#1323) | S26–S27 | 2.5D |
| 7 | Recap and outro | 07:45.680 – 08:30.000 (+ end screen to 08:50.000) | S28–S30 | 2.5D → footage → 4D |

**YouTube chapters (for the description in phase 5):** 00:00 Cold open · 00:49 What is a dimension? · 02:03 Building a
tesseract · 03:37 Slicing the fourth dimension · 04:36 Shadows are linear algebra · 05:41 Rotating in 4D · 07:13 Why it
matters · 07:45 Recap.

---

## CHAPTER 0 — COLD OPEN: THE CHEETAH AND THE SHADOW

### S01 — Time Is a Direction
**Time:** 00:00.000 → 00:18.480 (#52 "Now", 18.5 s) · **Dimension:** footage → 3D
**Engines:** skia (footage planes via `image_quad`, block, slice plane), numpy (camera spline), fx (letterbox, grain, motion blur)
**Purpose:** The hook. Real footage turns into geometry before the viewer expects it.

**VO:** "This is a cheetah at full sprint. But slow it down … sliding a flat slice through a solid block."

- **01A · Full sprint (00:00.0–00:06.0).** The cheetah at full speed, 30 fps prepared opener, 2.39:1 letterbox, a slow push-in.
  On "slow it down" (#9, 00:02.99) a **speed ramp** eases playback from real time to 25 % (frame-blended from the prepared
  opener), with motion blur on. On "strange" (#14, 00:04.24) a single thin blue scanline crosses the frame top to bottom. It is the first hint of w.
- **01B · Flat pictures (00:06.0–00:09.4).** On "Every video" (#16, 00:06.04) playback steps at 5 fps with a soft tick per
  frame. The letterbox retracts, and on "stack" (#21, 00:07.52) the current frame comes loose and tilts into 3D space. On "flat"
  (#23, 00:08.09) its bottom edge traces red (x) and its side edge traces orange (y).
- **01C · Stack them (00:09.4–00:14.1).** On "Stack" (#25, 00:09.36) the other frames unfold before and behind it into a translucent
  block (every second frame, as in `SHEETS`). The bright cheetah adds up into a ghost trail. On "time" (#31, 00:11.36) a **blue t axis**
  draws along the stack. On "direction" (#34, 00:12.24) its arrowhead flares. On "point to" (#37, 00:13.29) a small glint runs down the axis.
- **01D · A slice through a block (00:14.1–00:18.5).** On "Playing" (#39, 00:14.08) the Blue Slice Plane enters. On "sliding"
  (#44, 00:15.72) it sweeps the block, and the full-res frame plays where it cuts (the slice *is* playback). On "solid block"
  (#50–51, 00:17.50–00:17.90) the sheets fuse into one glass block with bright edges.

**Design notes:** The footage is the only thing allowed above 70 % luminance in this scene. The camera path is the existing
`_KEYS` spline, re-keyed to these cue times.
**Out:** The block's edges stay and become the cube in S02.

---

### S02 — The Shadow of a Cube, the Shadow of a Tesseract
**Time:** 00:18.480 → 00:35.240 (#96 "By", 16.8 s) · **Dimension:** 3D → 4D
**Engines:** skia (cube, point-light shadow, light pool, tesseract rig, w-slices of footage), numpy (ZW rotation, projection), fx (volumetric light, chroma kick, bloom)
**Purpose:** Pose the central question visually: what casts a 3D shadow?

**VO:** "Now take a cube. We only ever see its flat shadow … and this is what its shadow looks like."

- **02A · A cube and its shadow (00:18.5–00:25.1).** On "cube" (#55, 00:19.22) the block morphs into a cube, and t turns yellow and becomes z.
  A warm point light opens above it (volumetric cone, lens glint, anamorphic streak), and the floor dot grid grows out of the dark.
  On "flat shadow" (#61–62, 00:21.36) the rotating cube's real point-light shadow lands on the floor (convex hull of the projected
  corners), soft-edged. On "understand" (#66, 00:23.08) the shadow's outline traces in ink and changes shape (square → hexagon) as the cube turns.
- **02B · The question (00:25.1–00:30.3).** On "two-dimensional shadow" (#75–76, 00:26.11–00:27.66) a small label pill
  `3D → 2D` hangs by the shadow. On "three-dimensional one?" (#80, 00:28.53) everything dims to 25 % and a **dashed blue w
  arrow** points away from the cube in a direction no axis covers, with a slight shimmer.
- **02C · The answer (00:30.3–00:35.2).** On "fourth dimension" (#86–87, 00:31.41–00:31.85) the cube extrudes along w into a
  tesseract (chroma kick plus bloom swell, blue w-edges). On "this is what its shadow looks like" (#89–95, 00:32.98–00:34.63) the
  ZW rotation begins and the tesseract turns inside out. The cheetah plays frame by frame on 7 w-slices inside it, and the floor
  shows the shadow of the shadow.

**Out:** The tesseract keeps turning, and the camera eases closer for S03.

---

### S03 — The Promise
**Time:** 00:35.240 → 00:49.560 (#142 "So", 14.3 s) · **Dimension:** 4D
**Engines:** skia (Tesseract Rig, HUD, title lockup), Typst (vector, matrix chips), fx (light sweep, motion blur)
**Purpose:** The retention promise. A fast preview of every chapter, all on the *same* object, with no cuts.

**VO:** "By the end of this video, you will not just see this shape … rotate it in a way that is impossible in our world."

- **03A · See → understand (00:35.2–00:40.2).** A slow orbit. On "see this shape" (#106–108, 00:37.34–00:37.90) the wireframe is
  shown bare. On "understand it" (#111, 00:38.92) tiny binary coordinates (`0110`, digits colored by axis) bloom next to every vertex: the shape becomes data.
- **03B · Tools (00:40.2–00:42.9).** On "vectors" (#114, 00:40.53) a glass Vector Slot `(x, y, z, w)` slides in at the left. On
  "linear algebra" (#118, 00:41.72) a 4×4 Matrix Plaque slides in at the right. Both are small and slightly defocused (depth of field), and the tesseract stays the focus.
- **03C · Four teasers (00:42.9–00:47.9).** Each is a 1.2 s flash on the same rig, matching the chapters:
  1. "count its corners" (#122–124, 00:42.90–00:43.18): the 16 vertices pop in sequence and a counter ticks `1 → 16`.
  2. "measure its diagonal" (#125–127, 00:43.70–00:44.41): a white diagonal shoots from `0000` to `1111` and the readout `= 2` appears.
  3. "slice it" (#128, 00:45.28): the Blue Slice Plane cuts through and a glass octahedron flashes for 0.5 s.
  4. "rotate it" (#131, 00:46.19): a hard ZW spin with motion blur and trails.
- **03D · Title lockup (00:47.9–00:49.6).** On "impossible" (#138, 00:47.94) the rig pulls back and the title
  **UNDERSTANDING 4D** (display, ink) appears with a thin blue underline and the subtitle `visually` (italic, w-blue). A light
  sweep crosses it on "world" (#141, 00:49.10).

**Out:** A zoom-blur push into the tesseract's center, into black. Chapter 1.

---

## CHAPTER 1 — WHAT IS A DIMENSION?
Eyebrow: `01 · DIMENSIONS` at 00:53.0.

### S04 — An Ant on a Wire, a Table, a Room
**Time:** 00:49.560 → 01:08.640 (#201 "So", 19.1 s) · **Dimension:** 2D → 2.5D → 3D (one continuous camera crane)
**Engines:** skia (ant glyph, axes, readouts, perspective grid), space.py (camera crane), fx (motion blur on the flight)
**Purpose:** Define dimension as "how many numbers", with a physical, playful example.

**VO:** "So first, what actually is a dimension? Imagine an ant on a wire … how high."

- **04A · The question (00:49.6–00:53.0).** `What is a dimension?` sets in display type at the center, letters snapping in with tracking.
  On "dimension?" (#148, 00:52.22) the question mark pulses once, then the text lifts away.
- **04B · Wire (00:53.0–01:00.2).** On "ant" (#151, 00:53.71) a thin red glowing wire spans the frame (x), with mono ticks under it. A
  vector-drawn **ant** (a stylized silhouette, 6 legs animated with a walk cycle, ink with a soft red glow) walks along it. On
  "one number" (#162–163, 00:56.48–00:56.72) a readout chip `x = 2.4` rides above the ant, updating live. On "one dimension"
  (#169–170, 00:58.96) a pill `1D` appears.
- **04C · Table (01:00.2–01:05.0).** On "table" (#176, 01:01.08) the camera tilts back and the wire becomes the edge of a perspective
  tabletop grid, and the orange y axis draws. On "two" (#180, 01:02.18) the chip becomes `(x, y)`. On "right" (#183, 01:02.98) the x digits
  and axis pulse red. On "forward" (#187, 01:04.15) the y digits pulse orange. Dashed projection lines run from the ant to both axes.
- **04D · Room (01:05.0–01:08.6).** On "fly" (#190, 01:05.43) the ant lifts off (wing blur, motion blur) and the camera cranes into a 3D
  room (a very dim wireframe corner). The yellow z axis rises. On "third" (#198, 01:07.65) the chip becomes `(x, y, z)`. On "high" (#200,
  01:08.03) a yellow dashed drop-line runs from the ant to the floor.

**Out:** The ant fades, and its readout chip flies to the center.

---

### S05 — Numbers Make a Vector
**Time:** 01:08.640 → 01:29.320 (#262 "Now", 20.7 s) · **Dimension:** 2D + 3D
**Engines:** skia (axes, arrows, step ticks), Typst (vector brackets, linear combination), space.py
**Purpose:** Turn the readout into a vector, then into arrows: basis vectors and linear combination.

**VO:** "So a dimension is simply the number of independent numbers … every point is just a mix of those arrows."

- **05A · Independent numbers (01:08.6–01:14.1).** The `(x, y, z)` chip scales up. On "independent" (#209, 01:11.30) the three slots
  separate with gaps, each gets an axis-colored underline, and one slot changes while the others hold still. On "position" (#216, 01:13.33)
  the label `dimension = how many numbers` appears (label role).
- **05B · The vector (3, 2, 5) (01:14.1–01:23.0).** On "vector" (#223, 01:15.66) the chip rotates into a Vector Slot column with
  drawn-on brackets. The values fill on "three" (#226, 01:17.10), "two" (#227, 01:17.52) and "five" (#228, 01:17.80). On the right, 3D axes:
  "three steps along x" (#230–233, 01:18.91–01:19.77) draws a red arrow of length 3 with three step ticks. "two along y" (#234–236)
  draws an orange arrow tip-to-tail. "five along z" (#238–240, 01:21.19–01:22.18) draws a yellow arrow. Then the ink resultant arrow
  from the origin to (3, 2, 5) draws with glow, and a faint dashed coordinate box frames it.
- **05C · Basis vectors (01:23.0–01:29.3).** On "unit arrow" (#246–247, 01:24.40–01:24.74) three short unit arrows sit at the origin,
  labeled *e*ₓ, *e*ᵧ, *e*_z in italic. On "basis vector" (#250, 01:25.59) they glint. On "mix of those arrows" (#258, 01:27.68) the unit
  arrows replicate into the step chains (3 red, 2 orange, 5 yellow copies), and the formula `3eₓ + 2eᵧ + 5e_z = (3, 2, 5)` assembles under the vector.

---

### S06 — The Fourth Arrow
**Time:** 01:29.320 → 01:47.920 (#320 "You", 18.6 s) · **Dimension:** 3D + 2D
**Engines:** skia (axes, the searching arrow, angle markers), Typst (4-vector arithmetic plaque), numpy (angles, norm), fx (chroma kick, glitch shimmer)
**Purpose:** Make w feel real algebraically even though it can't be pictured.

**VO:** "Now here is the trick. Nothing forces us to stop at three … The algebra does not even flinch."

- **06A · A wall after three (01:29.3–01:33.5).** On "trick" (#266, 01:30.47) the camera pulls back. On "stop at three" (#271–273, 01:32.68–01:32.90)
  a faint vertical "wall" line appears just below the z slot of the vector.
- **06B · Add w (01:33.5–01:39.7).** On "fourth number, w" (#276–278, 01:33.82–01:34.96) the vector grows a fourth **blue** slot. It pushes the
  wall away, with a chroma kick. On "fourth arrow" (#281–282, 01:36.18) a blue arrow springs from the origin. On "right angles to x, y, and z" (#284–290,
  01:36.55–01:38.21) the arrow **searches**: it swings through three candidate directions, and live angle readouts `∠(w,x)`,
  `∠(w,y)`, `∠(w,z)` show at most two of the three reaching 90°. Each 90° gets a small right-angle marker in that axis's color. On
  "all at once" (#291–293, 01:38.28–01:38.76) the arrow fails, breaks into a dashed shimmer, and hangs outside the axes.
- **06C · The algebra doesn't flinch (01:39.7–01:47.9).** On "cannot picture" (#295–296, 01:39.87–01:40.26) the dashed arrow dims to 30 % and a glass
  plaque slides in with three computed lines, each on its cue:
  - "add it" (#303, 01:42.34): `(1, 2, 0, 3) + (2, 0, 1, 1) = (3, 2, 1, 4)`
  - "scale it" (#305, 01:42.70): `2 · (1, 2, 0, 3) = (2, 4, 0, 6)`
  - "measure it" (#308, 01:43.50): `‖(1, 2, 0, 3)‖ = √14 ≈ 3.742`
  The fourth entry is always blue. On "algebra does not even flinch" (#315–319, 01:45.94–01:47.25) all three lines flash ink together and settle.

---

### S07 — You Have Already Seen It
**Time:** 01:47.920 → 02:03.040 (#365 "So", 15.1 s) · **Dimension:** 3D
**Engines:** skia (Cheetah Block, pixel loupe, Vector Slot), fx (depth of field rack focus)
**Purpose:** Tie the abstraction back to the hook. The video block is a real 3D data space.

**VO:** "You have already seen a space like this. Every pixel in the cheetah video … you have four dimensions."

- **07A · The block returns (01:47.9–01:52.4).** On "space like this" (#325–327, 01:49.40–01:49.80) the Cheetah Block slides in from depth with a
  rack focus. Its axes are x (red), y (orange) and t (blue). On "pixel" (#329, 01:50.61) a reticle locks onto the cheetah's eye on one sheet, and a
  circular loupe magnifies the real pixel grid.
- **07B · Three numbers (01:52.4–01:59.6).** A readout vector fills per cue: x = 1115 (#338, 01:53.42), y = 354 (#340, 01:54.02), frame = 38 (#343,
  01:54.90; blue slot). These are the real pixel coordinates of the eye in `media/prepared/full/038.jpg` (measured). On "three-dimensional block" (#348–349, 01:56.40–01:57.52) the block outline glows. On
  "third direction is time" (#352–355, 01:58.51–01:59.56) the t arrow flares.
- **07C · One more (01:59.6–02:03.0).** On "Add one more number" (#356–359, 02:00.08–02:00.75) a fourth, empty ink slot appears with a pulsing `?`.
  On "four dimensions" (#363–364, 02:01.90–02:02.14) the block dims and the 4-slot vector holds.

**Out:** The vector collapses into a single glowing point at the center: the point that S08 drags.

---

## CHAPTER 2 — BUILDING THE TESSERACT
Eyebrow: `02 · BUILD A TESSERACT` at 02:03.2.

### S08 — The Drag
**Time:** 02:03.040 → 02:27.960 (#440 "Every", 24.9 s) · **Dimension:** 0D → 1D → 2D → 3D → 4D (one continuous camera move)
**Engines:** skia (Tesseract Rig in build mode, sweep trails, sparks), numpy (4D perspective projection), fx (motion blur, bloom, chroma kick)
**Purpose:** The hero build. One move, repeated, makes the tesseract feel inevitable.

**VO:** "So let's build a four-dimensional object with one simple move … The result is a tesseract, a hypercube."

- **08A · One simple move (02:03.0–02:09.6).** A single point breathes at the center. On "one simple move" (#372–374, 02:05.96–02:06.63) a ghost arrow
  hints a direction. On "new direction" (#380–381, 02:08.44–02:08.72) the ghost arrow fades.
- **08B · Point → segment (02:09.6–02:13.4).** On "point along x" (#384–386, 02:09.95–02:10.65) the point drags along x, leaving a red segment. A sweep trail with motion
  blur and sparks follows the moving end. On "two ends" (#394–395, 02:12.62–02:12.83) both endpoints flash.
- **08C · Segment → square (02:13.4–02:17.3).** On "along y" (#399–400, 02:14.34–02:14.74) the segment sweeps along y. The swept area flashes a translucent orange sheen
  and fades, leaving the square. On "four corners" (#407–408, 02:16.21–02:16.56) the corners flash in sequence.
- **08D · Square → cube (02:17.3–02:21.1).** The camera orbits from the front view to three-quarters (the 2D→3D change *is* the camera move).
  On "along z" (#412–413, 02:18.15–02:18.50) the square extrudes and yellow edges grow. On "eight corners" (#420–421, 02:19.98–02:20.40) the corners flash.
- **08E · Cube → tesseract (02:21.1–02:28.0).** On "drag the cube along w" (#423–427, 02:21.30–02:22.56) the dashed blue w arrow from S06 returns. A copy of the cube
  emerges and moves **inward** (that is how w looks in perspective) while the 8 blue w-edges grow. On "cannot see" (#431–432, 02:23.76–02:24.24)
  the blue edges shimmer. On "tesseract" (#437, 02:25.79) the whole rig lights up with a bloom swell and a chroma kick, and the label `tesseract` sets in
  display type. On "hypercube" (#439, 02:26.83) the sub-label `hypercube` appears and a slow XW rotation begins.

**Design notes:** Every drag uses the same timing curve (0.9 s, ease-in-out, tiny overshoot), so the repetition reads as a rule.

---

### S09 — The Corners Double
**Time:** 02:27.960 → 02:38.600 (#466 "Edges", 10.6 s) · **Dimension:** 2.5D row of five shapes
**Engines:** skia (mini shapes, counters), Typst (2ⁿ)
**Purpose:** The first pattern: corners double, 2ⁿ.

**VO:** "Every drag copies the shape, so the corners double … has two to the power n corners."

- **09A (02:28.0–02:31.2).** The build history lays out as a row of five small glowing shapes (point, segment, square, cube, tesseract). On "copies" (#442,
  02:28.63) each shape shows a ghost copy beside it. On "double" (#448, 02:30.62) `×2` arcs appear between neighbors.
- **09B (02:31.2–02:34.5).** The numbers `1, 2, 4, 8, 16` pop under each shape on "One" (#449, 02:31.16), "two" (#450), "four" (#451), "eight" (#452) and
  "sixteen" (#453, 02:33.82). Each shape's corners flash with its number, and sixteen gets the bloom.
- **09C (02:34.5–02:38.6).** The formula `corners = 2ⁿ` appears. The *n* glows on "n" (#457, 02:35.08) and "power n" (#463–464, 02:37.16–02:37.64),
  and the counts relabel as `2⁰ 2¹ 2² 2³ 2⁴`.

---

### S10 — Counting Edges, Faces and Cells
**Time:** 02:38.600 → 02:59.680 (#524 "In", 21.1 s) · **Dimension:** 3D / 4D
**Engines:** skia (Tesseract Rig in counting mode, glass faces), Typst (edge equations), Matrix-Plaque-style stats card (Skia `Lighting` bevel)
**Purpose:** Make the edge rule visible: old edges, copy edges and new edges.

**VO:** "Edges follow a pattern too … and eight cubes as its walls."

- **10A · The rule (02:38.6–02:45.4).** Replay the square → cube drag slowly. On "edges of both copies" (#474–477, 02:41.10–02:41.88) both squares' edges
  glow white. On "one new edge for every corner that moved" (#480–487, 02:42.65–02:44.69) the 4 yellow connecting edges draw one by one, in time with
  "every corner".
- **10B · Cube: 2 × 4 + 4 = 12 (02:45.4–02:50.0).** The equation builds term by term: "two" (#491, 02:46.08), "times four" (#493, 02:46.84),
  "plus four" (#494–495, 02:47.18–02:47.48), and "twelve" (#498, 02:48.69) lands as a result chip while an edge counter on the cube ticks to 12.
- **10C · Tesseract: 2 × 12 + 8 = 32 (02:50.0–02:55.1).** The inner and outer cubes' 24 edges glow. On "plus eight" (#506–507, 02:52.13–02:52.70)
  the 8 blue w-edges draw. On "thirty-two" (#510, 02:53.59) the counter shows 32 (computed from the rig).
- **10D · Faces and cells (02:55.1–02:59.7).** On "twenty-four square faces" (#515–517, 02:55.80–02:57.15) the 24 squares fill fast with a faint glass
  tint and the counter shows 24. On "eight cubes as its walls" (#519–523, 02:57.82–02:59.00) the 8 cells light one at a time. A glass stats card settles
  in the corner: `V 16 · E 32 · F 24 · C 8`.

---

### S11 — Corners Are Binary Numbers
**Time:** 02:59.680 → 03:12.870 (#553 "And", 13.2 s) · **Dimension:** 4D + 2D table
**Engines:** skia (rig with vertex labels, a 4×4 code table, hairline links)
**Purpose:** Coordinates make the shape countable without seeing it.

**VO:** "In coordinates, every corner is made of zeros and ones … Sixteen combinations, sixteen corners."

- **11A (02:59.7–03:03.6).** On "coordinates" (#525, 02:59.84) every vertex gets a 4-digit label in mono, each digit in its axis color. On "zeros and
  ones" (#531–533, 03:02.42–03:03.03) all the labels shimmer.
- **11B (03:03.6–03:06.9).** The camera nudges to one corner, and the label `0000` assembles one digit per spoken "zero" (#534–537, 03:03.64–03:05.23).
- **11C (03:06.9–03:10.0).** The opposite corner `1111` assembles on "one" ×4 (#541–544, 03:06.88–03:08.02). On "opposite" (#547, 03:08.70) a faint dashed
  line joins the two corners (a setup for S12).
- **11D (03:10.0–03:12.9).** On "Sixteen combinations" (#549–550, 03:10.04–03:10.55) a 4×4 table of all 16 codes appears on the left (truth-table look),
  each cell linked to its vertex by a hairline. On "sixteen corners" (#551–552) every label lights together.

---

### S12 — Measuring the Diagonal
**Time:** 03:12.870 → 03:37.120 (#630 "But", 24.3 s) · **Dimension:** 2D → 3D → 4D, plus a 2D formula
**Engines:** **Typst** (`typmath.morph` Pythagoras chain), skia (shapes, diagonals, ruler), Vector Slot (2,000-entry stream), fx (chroma kick)
**Purpose:** A clean, surprising number (exactly 2) from a space we can't see.

**VO:** "And we can measure it. By Pythagoras … whether it has two parts or two thousand."

- **12A · Square (03:12.9–03:20.9).** On "Pythagoras" (#559, 03:16.24) a unit square appears with a right triangle: legs `1` (red) and `1` (orange), diagonal
  in ink. The Typst formula builds `√(1² + 1²)` on "one plus one" (#571–573, 03:18.39–03:18.79) and morphs to `√2` on "two" (#580, 03:20.42). A small readout shows `≈ 1.414`.
- **12B · Cube (03:20.9–03:24.7).** The square extrudes into a cube and the body diagonal draws. On "adds one more term" (#583–586, 03:21.28–03:22.08) the formula
  gains `+ 1²` (yellow). On "three" (#592, 03:24.08) it shows `√3 ≈ 1.732`.
- **12C · Tesseract: exactly two (03:24.7–03:30.2).** The rig's long diagonal from `0000` to `1111` draws, and the formula gains a blue `+ 1²`. On "four" (#603,
  03:28.05) it shows `√4`. On "Exactly two" (#604–605, 03:28.64–03:29.47) `√4` morphs to a large **2** with a chroma kick and bloom. Two unit edges
  lay end to end along the diagonal and fit exactly. (They are compared in true 4D length. Show the ruler in the w-projection-free
  orthographic view so the lengths read honestly.)
- **12D · Any vector (03:30.2–03:37.1).** The general formula `‖v‖ = √(v₁² + v₂² + … + vₙ²)` appears (Typst). On "squared parts" (#620–621, 03:33.36–03:33.74)
  the squares glow. On "two parts or two thousand" (#625–629, 03:34.89–03:36.07) a Vector Slot on the right grows from 2 entries into a
  **2,000-entry column** that streams into perspective depth like a data waterfall, with a counter `n = 2,000`. The *n* in the formula glows.

---

## CHAPTER 3 — SLICES
Eyebrow: `03 · SLICES` at 03:37.3.

### S13 — Only in Pieces
**Time:** 03:37.120 → 03:45.520 (#650 "Imagine", 8.4 s) · **Dimension:** 4D → 2D
**Engines:** skia (exploded slice stack, flatten transition)
**Purpose:** Set up the slicing idea, then shrink the world by one dimension.

**VO:** "But how would we actually see a four-dimensional object? Only in pieces. To understand why, shrink down by one dimension."

- **13A (03:37.1–03:42.0).** The tesseract rig turns slowly. On "Only in pieces" (#639–641, 03:40.72–03:41.23) it separates into an **exploded stack of
  blue cross-section shells** spread along w (real slices of the rig at 7 w-values), like a sliced loaf.
- **13B (03:42.0–03:45.5).** On "shrink down" (#645–646, 03:43.48–03:43.82) the whole world flattens: the vertical scale eases to 0 and the camera
  drops onto a flat plane. On "dimension" (#649, 03:44.66) only a glowing sheet remains. That sheet is Flatland.

---

### S14 — Flatland: A Ball Through Paper
**Time:** 03:45.520 → 03:59.440 (#692 "One", 13.9 s) · **Dimension:** 2.5D + inset 2D
**Engines:** **PyVista** (glossy PBR sphere, warm key and blue rim light), skia (sheet, intersection circle, creature, inset card, filmstrip), numpy (r = √(R² − h²))
**Purpose:** The classic intuition pump, done beautifully.

**VO:** "Imagine a flat creature living on a sheet of paper … Each moment is one slice of the sphere."

- **14A (03:45.5–03:48.2).** A dark glass sheet sits in perspective with a fine grid. On "creature" (#653, 03:46.24) a tiny flat creature (a simple 2D glyph,
  a rounded triangle with one eye-dot) glides across it.
- **14B (03:48.2–03:52.2).** On "ball falls" (#661–662, 03:48.27–03:48.63) a PyVista sphere (glossy, warm specular) descends from above toward the sheet. On "never sees
  a ball" (#668–671, 03:51.10–03:51.88) a glass inset card (top right), labeled `creature's view`, shows only what lies *in* the sheet, which is nothing yet.
- **14C (03:52.2–03:56.8).** On "dot appear" (#675–676, 03:52.76–03:53.00) a blue dot appears where the sphere touches the sheet. It grows into a circle (#680,
  03:54.85), shrinks (#681, 03:55.08), and vanishes (#683, 03:56.02). The radius is real (`r = √(R² − h²)`), and the main view and the inset stay in sync.
- **14D (03:56.8–03:59.4).** On "one slice" (#687–688, 03:57.69–03:57.92) 7 sampled slice circles lay out as a filmstrip along a blue time axis
  under the sheet. This is a visual rhyme with the cheetah frames. On "sphere" (#691, 03:58.69) the filmstrip glows.

---

### S15 — A 4D Ball Passing Through Our Space
**Time:** 03:59.440 → 04:14.200 (#733 "Slices", 14.8 s) · **Dimension:** 3D + 2D graph, then footage-3D
**Engines:** **PyVista** (glass sphere with blue rim), skia (room wireframe, w slider, r(w) curve, Cheetah Block callback), numpy
**Purpose:** Lift the analogy one level, and land it on the hook.

**VO:** "One level up, a four-dimensional ball passing through our space … Each frame was one slice of a three-dimensional block."

- **15A (03:59.4–04:07.9).** On "One level up" (#692–694, 03:59.44–03:59.87) the camera pulls up and out, and the sheet becomes a dim wireframe cube: "our space". A blue
  **w slider** runs along the bottom with a semicircular profile `r(w) = √(R² − w²)`. On "tiny sphere appearing" (#706–708, 04:03.26–04:03.84) a PyVista glass
  sphere appears at the center, then swells (#711, 04:05.32), shrinks (#712, 04:05.95), and disappears (#714, 04:06.88). The radius is driven by the slider marker through the real formula.
- **15B (04:07.9–04:14.2).** On "playing the cheetah video" (#719–722, 04:08.94–04:09.97) the scene racks focus into the Cheetah Block (same look as S01D), and
  the Blue Slice Plane sweeps while the frames play. On "one slice" (#727–728, 04:11.52–04:11.79) the plane flashes. On "three-dimensional block" (#731–732,
  04:12.32–04:13.57) the block outline glows. A small side-by-side holds for 1 s: `sphere → circles` next to `block → frames`.

---

### S16 — Corner-First Slices of a Tesseract
**Time:** 04:14.200 → 04:36.590 (#793 "Slices", 22.4 s) · **Dimension:** 4D rig + 3D solids
**Engines:** **PyVista** (glass slice solids), **scipy** (`ConvexHull` of the real section `x+y+z+w = s` of the unit tesseract), skia (rig with lit vertices, s slider, edges of the solid, filmstrip), fx (light sweep)
**Purpose:** The strangest, most memorable visual of the film: the slices are computed, not drawn by hand.

**VO:** "Slices of a tesseract are even stranger. Push it through corner first … depending only on its angle."

- **16A · Set up (04:14.2–04:17.6).** Split composition. On the left, the tesseract rig with vertices colored by which side of the hyperplane they are on. On the right, an
  empty glass stage. A mono slider reads `s = x + y + z + w` from 0 to 4. On "stranger" (#739, 04:16.02) the rig turns until vertex `0000` leads.
- **16B · Tetrahedron (04:17.6–04:22.2).** On "corner first" (#743–744, 04:17.62–04:17.99) s starts moving. On "tiny tetrahedron" (#750–751, 04:19.50–04:19.54) a PyVista
  glass tetrahedron appears with razor blue edges (drawn by skia from the hull). On "triangular pyramid" (#753–754, 04:20.38–04:21.08) a small label appears.
- **16C · Clipped → octahedron (04:22.2–04:29.8).** On "grows" (#756, 04:22.37) the solid grows. On "corners get clipped" (#758–760, 04:23.03–04:23.72) it becomes a truncated tetrahedron, and the new
  hexagonal faces flash. On "middle" (#764, 04:24.90) s reaches 2. On "perfect octahedron" (#768–769, 04:26.06–04:26.31) the solid is a regular octahedron: hero beat, light
  sweep across the glass, bloom. On "two pyramids glued base to base" (#771–776, 04:27.44–04:29.20) it separates vertically into two square pyramids
  (exploded view) and rejoins, with the shared square outlined in ink.
- **16D · Reverse and compare (04:29.8–04:36.6).** On "plays in reverse" (#780–782, 04:30.52–04:31.28) s runs 2 → 4 and the solid shrinks back to an inverted tetrahedron and vanishes.
  On "Same object, completely different slices" (#783–787, 04:31.92–04:34.53) a two-row filmstrip appears. The top row is face-first (5 identical cubes). The bottom row is corner-first
  (tetrahedron → truncated → octahedron → truncated → tetrahedron). On "angle" (#792, 04:35.94) both rows' rigs tilt.

**Math notes:** For 0 < s ≤ 1 the section is a tetrahedron, for 1 < s < 2 a truncated tetrahedron, and at s = 2 a regular
octahedron, symmetric about s = 2. The section is computed by intersecting the 32 edges with the hyperplane, hulling the
points, and mapping them into the hyperplane's 3D basis.

---

## CHAPTER 4 — SHADOWS ARE LINEAR ALGEBRA
Eyebrow: `04 · SHADOWS` at 04:36.8.

### S17 — A Shadow Forgets the Height
**Time:** 04:36.590 → 04:56.160 (#850 "From", 19.6 s) · **Dimension:** 3D + 2D plaque
**Engines:** **PyVista** (glass cube, overhead light), skia (light shafts, floor shadow, coordinate tags), Matrix Plaque (Typst), fx (volumetric light)
**Purpose:** A projection is a matrix. Show the "forgetting" literally.

**VO:** "Slices show one piece at a time. Shadows show everything at once … and multiplies z by zero."

- **17A (04:36.6–04:43.6).** On "one piece at a time" (#795–799, 04:37.41–04:38.04) the S16 filmstrip compresses into a single sheet. On "shadows show everything at
  once" (#800–804, 04:38.47–04:40.38) a full shadow silhouette appears. On "pure linear algebra" (#809–811, 04:41.85–04:42.70) a matrix-bracket glyph glints.
- **17B (04:43.6–04:50.6).** A PyVista glass cube floats above a dark floor. On "Shine a light straight down" (#812–816, 04:43.60–04:44.75) an overhead light opens with
  straight volumetric shafts, and a crisp square shadow appears. On "forgets the height" (#823–825, 04:46.26–04:46.76) the cube bobs up and down while the shadow does
  not change. One vertex is tagged `(x, y, z)` on "Every point" (#827–830, 04:47.85–04:49.00). On "lands at x, y" (#831–834, 04:49.14–04:50.15) a drop-line falls to the floor tag `(x, y)`.
- **17C (04:50.6–04:56.2).** The Matrix Plaque `[[1,0,0],[0,1,0],[0,0,0]] · (x, y, z) = (x, y, 0)` appears with real numbers for that vertex. On "keeps x" (#841–842,
  04:53.28–04:53.30) the red row lights. On "keeps y" (#843–844, 04:53.52–04:53.93) the orange row lights. On "multiplies z by zero" (#846–849, 04:54.46–04:55.50) the bottom-right 0
  glows, and the z entry of the result collapses to 0 with a small squash.

---

### S18 — From Four to Three: Drop w
**Time:** 04:56.160 → 05:06.980 (#881 "The", 10.8 s) · **Dimension:** 2D plaque + 4D rig
**Engines:** Matrix Plaque, skia (rig in orthographic mode, merge pops), numpy (`project_ortho`)
**Purpose:** The same idea one level up, and why it isn't enough.

**VO:** "From four dimensions to three, a three by four matrix keeps x, y and z, and drops w … so we use perspective."

- **18A (04:56.2–05:01.5).** On "four dimensions to three" (#851–854, 04:56.50–04:57.87) the plaque grows a column into **3 × 4**, and `3 × 4` dimension ticks appear on
  "three by four" (#856–858, 04:58.82–04:59.15). The rows light on "x, y, and z" (#861–864, 05:00.44–05:01.19). On "drops w" (#865–866, 05:01.27–05:01.53) the all-zero fourth column glows blue, and the input
  vector's w entry falls away.
- **18B (05:01.5–05:07.0).** The tesseract rig switches to orthographic projection: the inner and outer cubes slide into each other. On "stacks corners on top of each other"
  (#870–876, 05:03.32–05:04.96) vertex pairs merge with a soft pop, and a counter reads `16 corners → 8 visible`. On "perspective" (#880, 05:05.98) an iris ring opens (transition).

---

### S19 — Perspective Along w
**Time:** 05:06.980 → 05:30.950 (#948 "Join", 24.0 s) · **Dimension:** 3D example → 2D side view → 4D rig
**Engines:** skia (receding frames, w-axis diagram, camera icon, rays), Typst (live x′ = d/(d − w)·x with numbers), Cheetah frames, numpy
**Purpose:** Explain the famous picture before showing it.

**VO:** "The same rule your eyes use, farther things look smaller … and the eight far corners form a small cube."

- **19A (05:07.0–05:11.2).** On "your eyes" (#884–885, 05:07.86–05:08.18) a corridor of identical cheetah frames recedes into depth. On "farther things look smaller" (#887–890,
  05:08.90–05:10.28) each frame shows its apparent-size readout.
- **19B (05:11.2–05:18.8).** A side-view diagram: a horizontal blue w axis, and a camera icon (aperture ring) placed on "camera out along w" (#893–896, 05:11.72–05:13.03).
  The formula `x′ = d / (d − w) · x` builds per cue: "scaled" (#900, 05:14.25), "camera distance" (#903–904, 05:15.06–05:15.50) gives `d`, "divided by" (#905, 05:16.10) gives the fraction bar,
  "distance minus w" (#909–911, 05:17.42–05:18.38) gives `d − w` with w in blue.
- **19C (05:18.8–05:25.2).** A point slides along w with rays to the camera and a live scale readout (d = 3: w = +0.5 gives ×1.20, w = −0.5 gives ×0.86). On "large w come closer and grow"
  (#915–920, 05:19.72–05:21.42) its projected size bar grows. On "small w move away and shrink" (#924–929, 05:22.95–05:24.70) it shrinks.
- **19D (05:25.2–05:31.0).** Back to the rig, unconnected. On "eight near corners" (#932–934, 05:25.51–05:26.14) the w = +1 corners light up and inflate into a **big cube** (#937–938,
  05:26.98–05:27.21). On "eight far corners" (#941–943, 05:28.04–05:28.58) the w = −1 corners shrink into a **small cube** (#946–947, 05:29.44–05:29.80).

---

### S20 — A Cube Inside a Cube
**Time:** 05:30.950 → 05:41.280 (#976 "Now", 10.3 s) · **Dimension:** 4D + 2D inset
**Engines:** skia (rig, glass frustum cells, perspective-cube inset), fx (light sweep)
**Purpose:** Name the famous picture and correct the misreading that it is "squashed".

**VO:** "Join them along w, and you get the famous picture, a cube inside a cube … seen in four-dimensional perspective."

- **20A (05:31.0–05:35.7).** On "Join them along w" (#948–951, 05:30.95–05:31.90) the 8 blue w-edges draw. On "famous picture" (#956–957, 05:33.03–05:33.58) a light sweep runs. On "cube inside a cube"
  (#959–962, 05:34.26–05:35.09) the hero shot, with a slow orbit.
- **20B (05:35.7–05:41.3).** On "six lopsided shapes" (#964–966, 05:35.92–05:36.65) the six frustum cells fill one by one with glass tint. On "real cubes" (#970–971, 05:38.28–05:38.38) a glass
  inset (bottom left) shows an ordinary cube drawn in perspective, with one trapezoid face highlighted in the same tint as a frustum cell. On "four-dimensional perspective"
  (#974–975, 05:39.14–05:40.22) both pulse together.

---

## CHAPTER 5 — ROTATION
Eyebrow: `05 · ROTATION` at 05:41.5.

### S21 — The 2×2 Rotation Matrix
**Time:** 05:41.280 → 05:56.600 (#1021 "In", 15.3 s) · **Dimension:** 2D
**Engines:** **Typst** (`typmath` matrix build and term highlights), skia (plane, rotating point, θ arc, component projections), numpy
**Purpose:** Teach the one rotation formula that the whole chapter extends.

**VO:** "Now let's make it move. In two dimensions, rotating by an angle theta is a two by two matrix … plus cosine theta times y."

- **21A (05:41.3–05:46.9).** On "make it move" (#978–980, 05:41.97–05:42.49) the rig twitches into motion, then flattens to a 2D plane with x (red) and y (orange) axes. On "rotating by an
  angle theta" (#984–988, 05:44.60–05:45.78) a point P = (1, 0.4) rotates along a circle, an arc marks *θ*, and a live readout shows `θ = 30°`.
- **21B (05:46.9–05:56.6).** On "two by two matrix" (#991–994, 05:46.28–05:46.94) the Typst plaque `[[cos θ, −sin θ], [sin θ, cos θ]]` appears. The row equations build term by term:
  `x′ = cos θ · x − sin θ · y` (#996–1007, 05:47.84–05:51.74) and `y′ = sin θ · x + cos θ · y` (#1009–1020, 05:52.47–05:56.16). Each spoken term highlights both the equation
  term and its matrix entry. Projection lines show the components on the axes changing live.

---

### S22 — Rotation Happens in a Plane
**Time:** 05:56.600 → 06:12.040 (#1066 "That", 15.4 s) · **Dimension:** 3D
**Engines:** skia (spinning cube, axis rod, plane disc, vertex trails, live coordinate HUD), numpy
**Purpose:** Replace "around an axis" with "in a plane". This is the key idea for 4D.

**VO:** "In three dimensions, we say an object rotates around an axis … The axis is just what is left over."

- **22A (05:56.6–06:00.6).** A cube with a thin vertical rod through it. On "rotates around an axis" (#1028–1031, 05:58.73–05:59.94) it spins around the rod.
- **22B (06:00.6–06:06.9).** A HUD tracks one vertex's `(x, y, z)`. On "height never changes" (#1042–1044, 06:03.23–06:03.91) the z digits stay steady (yellow, with a small lock glyph).
  On "the other two coordinates mix" (#1047–1050, 06:04.90–06:06.47) the x and y digits oscillate.
- **22C (06:06.9–06:12.0).** On "rotation really happens in a plane" (#1052–1057, 06:07.08–06:09.03) a red→orange gradient disc appears in the xy plane with a circular arrow, and vertex
  trails trace circles parallel to it. On "just what is left over" (#1061–1065, 06:10.40–06:11.45) the rod dims to 20 % and gets the small label `leftover`.

---

### S23 — Three Planes, Then Six
**Time:** 06:12.040 → 06:34.920 (#1117 "Let's", 22.9 s) · **Dimension:** 3D → 2D pair grid
**Engines:** skia (gradient plane discs, a 4×4 pair grid of plane chips), **Typst** (`typmath.morph`: n(n−1)/2 → 4·3/2 → 6)
**Purpose:** Count rotation planes with a linear-algebra-looking grid, so "six" feels earned.

**VO:** "That idea unlocks four dimensions. With three axes, there are three planes … six ways to rotate."

- **23A (06:12.0–06:19.6).** On "three axes, there are three planes" (#1072–1077, 06:14.79–06:16.40) three gradient discs appear on the 3D axes: xy (#1078, 06:17.04), xz (#1079, 06:17.71) and
  yz (#1081, 06:18.86).
- **23B (06:19.6–06:27.5).** On "four axes … six" (#1083–1087, 06:19.96–06:21.46) the discs fly into a **4×4 grid**, labeled x y z w along the top and side. The upper-triangle
  cells light one per spoken pair as gradient chips: xy (#1088, 06:21.92), xz (#1089, 06:22.69), xw (#1090, 06:23.46), yz (#1091, 06:24.05), yw (#1092, 06:25.08) and zw (#1094, 06:26.39).
  The diagonal cells are crossed out in muted grey (a plane needs two different axes). The lower triangle mirrors the upper one at 15 % opacity.
- **23C (06:27.5–06:34.9).** The Typst formula `n(n − 1) / 2` builds on "n times n minus one divided by two" (#1098–1105, 06:28.52–06:30.68). It substitutes to `4 · 3 / 2` (#1106–1111,
  06:31.28–06:32.99) and resolves to `= 6` on "six" (#1113, 06:33.38) with a chroma kick. The six chips line up in a row under it on "ways to rotate" (#1114–1116).

---

### S24 — The ZW Rotation: Inside Out
**Time:** 06:34.920 → 07:02.600 (#1198 "Four", 27.7 s) · **Dimension:** 4D (hero)
**Engines:** **Typst** (4×4 assembly and the 2×2 dock), Matrix Plaque (live θ), skia (Tesseract Rig, trails, edge-length bars, floor shadow), numpy (`rotate4`, `project_persp`, edge lengths, RᵀR, det), fx (motion blur, bloom)
**Purpose:** The payoff. The famous inside-out motion, proven rigid with numbers.

**VO:** "Let's rotate in the zw plane. The matrix leaves x and y alone … turning in a direction we can only see as a shadow."

- **24A · The matrix (06:34.9–06:43.0).** On "zw plane" (#1121–1122, 06:36.29–06:36.40) the zw chip enlarges. The 4×4 plaque assembles: on "leaves x and y alone" (#1125–1129, 06:37.86–06:38.80) the top-left
  identity glows red and orange and all off-diagonal zeros dim. On "mixes z with w" (#1131–1134, 06:39.74–06:40.35) the zw block glows its gradient. On "same cosine and sine" (#1137–1140,
  06:41.12–06:42.25) the 2×2 matrix from S21 flies in and **docks** into the zw block (callback).
- **24B · Inside out (06:43.0–06:51.0).** The plaque shrinks to the corner with a live `θ` readout, and the tesseract fills the frame. On "Watch the shadow" (#1141–1143, 06:42.96–06:43.47) the rotation starts.
  On "inner cube grows" (#1145–1147, 06:44.27–06:44.83) the inner cell is tinted blue. On "outer cube shrinks" (#1149–1151, 06:45.56–06:46.01) the outer cell is tinted ink. On "pass through each other"
  (#1154–1157, 06:47.01–06:47.95) and "turn inside out" (#1162–1164, 06:50.00–06:50.57) the hero motion plays with motion blur, trails and bloom.
- **24C · Nothing bends (06:51.0–07:02.6).** On "nothing bends" (#1166–1167, 06:51.28–06:51.83) the rotation slows. A strip of **32 thin bars** shows the edge lengths: the true 4D length bars
  stay locked at 1.000 (ink), while ghost bars for the projected lengths fluctuate (muted). On "orthogonal" (#1171, 06:53.22) the plaque shows `RᵀR = I` with the identity glowing. On "determinant
  is one" (#1173–1175, 06:54.40–06:55.32) it shows `det R = cos²θ + sin²θ = 1`. On "every edge keeps its length" (#1178–1181, 06:56.22–06:57.07) the bars pulse. On "rigid object … see as a shadow"
  (#1185–1197, 06:58.19–07:01.76) the camera pulls back to reveal a floor with the tesseract's soft shadow (the shadow of the shadow).

---

### S25 — Double Rotation: Only the Center Stays Still
**Time:** 07:02.600 → 07:13.760 (#1233 "So", 11.2 s) · **Dimension:** 4D
**Engines:** Matrix Plaque (block-diagonal, two angles), skia (rig, long trails, center star), numpy (simultaneous xy and zw rotation)
**Purpose:** One thing 3D can never do.

**VO:** "Four dimensions even allow a double rotation … the only point that stays still is the very center."

- **25A (07:02.6–07:09.0).** On "double rotation" (#1203–1204, 07:04.08–07:04.44) the plaque becomes block-diagonal with two rotation blocks: xy (red→orange, angle *θ*) and zw (yellow→blue,
  angle *φ*). The chips light on "xy plane" (#1207, 07:05.61) and "zw plane" (#1211, 07:06.79). On "same time" (#1215–1216, 07:07.90–07:08.32) the tesseract begins a double rotation (θ = φ),
  with every vertex trailing a long, fading circle.
- **25B (07:09.0–07:13.8).** On "No axis is left over" (#1217–1221, 07:08.96–07:09.82) a ghost axis rod appears and dissolves. On "only point that stays still" (#1224–1228, 07:10.69–07:11.99) a bright
  white star marks the center with a radial pulse, and a readout shows `fixed points: 1`. On "very center" (#1231–1232, 07:12.78–07:13.00) everything else keeps moving.

---

## CHAPTER 6 — WHY IT MATTERS
Eyebrow: `06 · WHY IT MATTERS` at 07:14.0.

### S26 — The Math Is Everywhere
**Time:** 07:13.760 → 07:40.040 (#1308 "That", 26.3 s) · **Dimension:** 2.5D card arc
**Engines:** skia (glass card arc, depth of field, Cheetah Block world-line), **PyVista** (procedural spacecraft: box body plus panel slabs, PBR), numpy (quaternion slerp; synthetic clustered embeddings and a real PCA projection), Matrix Plaque (3×4 callback)
**Purpose:** Real-world anchors, each a callback to a visual the viewer already knows.

**VO:** "So is any of this real? We may never step into a fourth direction of space … the same tools we just used on a tesseract."

- **26A (07:13.8–07:21.2).** On "real?" (#1238, 07:15.24) the tesseract shrinks to a small glowing object. On "never step into a fourth direction" (#1242–1246, 07:16.39–07:17.50) our space is shown as a glass
  box, with the dashed blue w arrow outside it, out of reach. On "everywhere" (#1253, 07:20.15) three glass cards swing into a 2.5D arc.
- **26B · Physics (07:21.2–07:24.4).** On "Physics treats time as a fourth coordinate" (#1254–1260, 07:21.15–07:22.67) card 1 shows the Cheetah Block with the cheetah's path drawn as a blue **world-line**
  through the frames, and a Vector Slot `(t, x, y, z)` with the t slot in blue. On "spacetime" (#1262–1263, 07:23.78) the card glints. (No distance formula is shown: spacetime measures distance differently.)
- **26C · Quaternions (07:24.4–07:30.2).** On "Game engines and spacecraft" (#1264–1267, 07:24.38–07:25.23) card 2 shows a PyVista spacecraft turning smoothly. On "quaternions" (#1269, 07:26.03) the label `q = (w, x, y, z)`
  appears with w as the blue scalar slot. On "four parts" (#1272–1273, 07:27.54–07:27.72) the slots pulse. On "rotate objects smoothly" (#1275–1277, 07:28.27–07:29.16) a slerp arc trail draws.
- **26D · Word vectors (07:30.2–07:40.0).** On "a model like ChatGPT" (#1281–1284, 07:30.83–07:31.81) card 3 shows a mono word chip `cheetah`. On "a single word is a vector" (#1287–1290, 07:32.82–07:33.22) a tall
  number column rises from the chip. On "thousands of dimensions" (#1292–1294, 07:33.98–07:34.80) a counter rolls to `4,096` (small label `for example`). On "measured" (#1295, 07:35.76) a length readout `‖v‖` appears.
  On "projected" (#1297, 07:36.54) a cloud of word points is projected down to 3D (a real PCA of synthetic clusters), and the 3×4 Matrix Plaque from S18 slides in beside it. On "on a tesseract"
  (#1305–1307, 07:39.00–07:39.21) a tiny tesseract icon joins the plaque.

---

### S27 — Your Eyes Stop at Three
**Time:** 07:40.040 → 07:45.680 (#1323 "Let's", 5.6 s) · **Dimension:** 2.5D
**Engines:** skia (axes, wall, Vector Slot stream), fx (bloom)
**Purpose:** The thesis in one image.

**VO:** "That is the real lesson. Your eyes stop at three dimensions. Linear algebra does not."

- **27A (07:40.0–07:43.8).** The cards fade. On "eyes stop at three" (#1314–1318, 07:41.87–07:43.08) the x, y and z axes glow and the S06 "wall" line reappears after z.
- **27B (07:43.8–07:45.7).** On "Linear algebra does not" (#1319–1322, 07:43.80–07:45.28) the Vector Slot breaks through the wall: x y z w, then slots 5, 6, 7 … n stream upward into perspective with bloom.

---

## CHAPTER 7 — RECAP AND OUTRO
Eyebrow: `07 · RECAP` at 07:45.9.

### S28 — Everything We Built
**Time:** 07:45.680 → 08:15.390 (#1395 "So", 29.7 s) · **Dimension:** 2.5D card arc
**Engines:** skia (five glass recap cards with live miniatures, camera truck, depth of field), Tesseract Rig (mini)
**Purpose:** Reinforce the five ideas with visuals the viewer has already seen.

**VO:** "Let's recap. A dimension is the number of independent numbers … giving four dimensions six ways to turn."

Five cards in an arc. The camera trucks along it. The active card is at 100 % and the others are at 30 % with depth-of-field blur.

1. **Numbers** (#1326–1337, 07:46.75–07:51.05): the ant with its `(x, y, z)` chip.
2. **A fourth direction** (#1338–1345, 07:51.96–07:54.62): the Vector Slot grows w, and the dashed blue arrow appears.
3. **The tesseract** (#1346–1365, 07:55.48–08:02.79): the build replays fast. Counters land on "16" (#1355, 07:58.39), "32" (#1357, 07:59.52) and "two" (#1365, 08:02.79) as the diagonal draws.
4. **Slices and shadows** (#1366–1382, 08:03.60–08:08.64): a split card. The octahedron slice and a cheetah frame appear on "slices … frames" (#1370–1375). The 3×4 plaque appears on "projection matrices" (#1381–1382).
5. **Rotation in planes** (#1383–1394, 08:10.04–08:14.71): the six plane chips, then a ZW spin. "six" (#1391, 08:13.98) flashes.

---

### S29 — One Frame at a Time
**Time:** 08:15.390 → 08:22.800 (#1417 "If", 7.4 s) · **Dimension:** footage → 3D
**Engines:** skia (footage, Cheetah Block, Blue Slice Plane), fx (letterbox, grain)
**Purpose:** Close the loop on the hook.

**VO:** "So the next time you watch a video, remember, you are already sliding through a higher dimension, one frame at a time."

- **29A (08:15.4–08:17.6).** The cards collapse to a point. On "watch a video" (#1400–1402, 08:16.27–08:16.84) the cheetah footage returns full screen and the letterbox closes in.
- **29B (08:17.6–08:22.8).** On "sliding through a higher dimension" (#1407–1411, 08:18.34–08:19.68) the footage tilts back into the block and the Blue Slice Plane sweeps. On "one frame at a time" (#1412–1416,
  08:20.85–08:22.34) the plane steps frame by frame at 5 fps with a tick each step, and the last frame holds.

---

### S30 — See You in the Next Dimension (End)
**Time:** 08:22.800 → 08:30.000 (7.2 s), plus the end-screen hold to 08:50.000 · **Dimension:** 4D → 2D
**Engines:** skia (rig, subscribe pill, end-screen slots), fx (light sweep, zoom-blur push)
**Purpose:** The call to action and the end screen.

**VO:** "If this made the fourth dimension a little less mysterious, subscribe for more complex math made visual. See you in the next dimension."

- **30A (08:22.8–08:28.8).** The frozen frame folds back into a slowly turning tesseract. On "less mysterious" (#1425–1426, 08:24.72–08:24.94) its coordinates fade in and out once. On "subscribe" (#1427,
  08:25.60) a minimal subscribe pill outlines in white with a light sweep. On "complex math made visual" (#1430–1433, 08:26.62–08:27.78) the title lockup **UNDERSTANDING 4D** reappears, small.
- **30B (08:28.8–08:30.0).** On "next dimension" (#1438–1439, 08:29.19–08:29.31) the tesseract turns inside out once more and the camera flies into its inner cube, then to black.
- **End screen (08:30.0–08:50.0).** Black, with the tesseract turning at 15 % opacity in the background. Two outlined slots for the YouTube end-screen editor: left, *Why the
  Jacobian Matrix Is So Powerful* (the channel's best linear-algebra long-form); right, *Eigenvectors Finally Make Sense*. A subscribe circle sits at the center bottom. The timeline is extended with silence (end-screen elements need at least 5 s and usually up to 20 s).

---

## 4. Build stages (one per session)

Each stage ends with `--frame` stills at the listed times and `--audit`, then a 720p `--preview` of that chapter, before moving on.
Full-quality renders (`--final`, 1080p/4K) are never run in these sessions.

| Stage | Contents | Check stills at (s) |
| --- | --- | --- |
| **A · Foundation** | `cues.py` (AUDIO_DURATION 510.0, `cue()`, `word()`), `render.py` (chapter CLI: stills / frame / preview / final, as in the convolution project), `scenes/full.py`; `components/`: `tesseract.py`, `vector_slot.py`, `matrix_plaque.py`, `slice_plane.py`, `cheetah_block.py` (from s01), `hud.py` (eyebrow, readouts, pills, glass card); `fx.py` additions: `motion_blur`, `chroma_kick`, `light_sweep`, `dof`; copy `mathtype.py`; **PyVista offscreen smoke test** (one glass sphere frame, camera-matched overlay); **Manim smoke test** (one `prepare_manim` clip) | component test frames only |
| **B · Chapter 0** | S01–S03: port and re-time `s01_cinematic.py` into `ch0_intro.py`, add S02C slices and S03 | 3.5, 8.4, 12.5, 16.5, 21.5, 29.0, 33.8, 38.9, 43.2, 46.4, 48.6 |
| **C · Chapter 1** | S04–S07 (ant glyph, vector arrows, searching w arrow, pixel loupe) | 56.8, 63.5, 67.8, 72.0, 81.6, 87.8, 97.8, 103.6, 111.0, 114.9, 121.9 |
| **D · Chapter 2** | S08–S12 (Pythagoras Typst morph first) | 130.6, 134.7, 138.6, 142.3, 146.0, 153.9, 157.7, 163.9, 173.6, 178.3, 185.4, 191.6, 200.5, 209.6, 216.0 |
| **E · Chapter 3** | S13–S16 (PyVista sphere and slice-solid caches first) | 221.2, 224.6, 229.0, 234.9, 245.4, 251.8, 259.8, 263.8, 266.4, 268.6, 274.0 |
| **F · Chapter 4** | S17–S20 | 279.4, 286.5, 295.4, 299.6, 304.4, 308.9, 317.8, 321.4, 329.6, 334.9, 338.5 |
| **G · Chapter 5** | S21–S25 (three Typst equation sequences first) | 345.8, 351.4, 355.2, 363.5, 368.9, 378.9, 386.4, 393.5, 400.4, 405.6, 410.3, 415.4, 421.5, 428.4, 432.2 |
| **H · Chapters 6–7** | S26–S30 plus the end screen | 437.3, 442.4, 446.6, 456.6, 464.5, 468.0, 478.6, 484.5, 493.9, 498.8, 505.7, 509.0, 520.0 |
| **I · Polish** | the optional SFX cue sheet (reuse `convolution…/sfx/` Mixkit/Kenney sounds: soft whoosh on drags, tick on frame steps, low boom on tesseract reveals, glass ping on "Exactly two" / "six"), the composite bloom pass, a full 720p preview, and audio-sync spot checks at 10 random cues | — |
| **J · Final** | **not run in this session**: Claude renders 720p previews only. You run the full 1080p (`--final`) locally or the 4K Kaggle bundle (`kaggle/`, the same chunked runner as the convolution project), then check loudness | — |

### Folder layout

```
understanding-4d-visually/
  audio.mp3  cue-per-word.srt  normal-subtitle.srt  voiceover.md  scene-plan.md  README.md
  theme.py  fx.py  space.py  media.py  prepare_media.py  cues.py  typmath.py  mathtype.py  render.py
  components/  tesseract.py  vector_slot.py  matrix_plaque.py  slice_plane.py  cheetah_block.py  hud.py
  pv3d/        solids.py (sphere, box, convex slice solids)  render.py (camera-matched, cached RGBA renders)
  smoke_tests.py  (engine checks: --pyvista, --manim)
  manim/       smoke.py + fonts (optional fallback; equation morphs live in typmath.py)
  scenes/      ch0_intro.py  ch1_dimension.py  ch2_build.py  ch3_slices.py  ch4_shadows.py
               ch5_rotation.py  ch6_matters.py  ch7_recap.py  full.py   (s01_cinematic.py kept as reference)
  media/       cheetah.mp4  cheetah_frames/  prepared/
  output/      frames/  previews/  cache/{pyvista,manim}/
  sfx/  kaggle/  final/
```

Each chapter module follows the convolution pattern: `START = cue(a)`, `END = cue(b)` (Chapter 0 starts at 0.0 and
Chapter 7 ends at 530.0), a `T` dict of cue times, `draw_sXX(fr, t)` per scene, one `FunctionSource` with an mtime key, and
`OFFSET`, `DURATION` and `STILLS`. `full.py` checks that the chapters are contiguous.

### Quality bar (applies to every stage)

- Every number on screen is computed from the Tesseract Rig or numpy: counts, lengths, angles, slice shapes, pixel coordinates.
- Token colors never change meaning. Edges are always colored by their axis, and planes are always two-axis gradients.
- One focal point per frame. Everything else is at 40 % opacity or less.
- Line weights at 1080p: 1 px for grids, 1.5–2 px for geometry, 2.5–3 px for hero strokes. Glow only on the focal element.
- No text smaller than the `label` role, and no paragraph text. `--audit` must pass with no contrast or clutter warnings.
- 3D shots use one continuous, eased camera move with no cuts. Every PyVista layer must line up with its skia edges to within 1 px (check in a still).
- Performance: 2 CPU cores, 3.7 GB RAM, integrated GPU only. PyVista frames are rendered once and cached. Motion blur (4–6 subframes) is enabled only in finals and
  only for the hero beats (S01A, S03C, S08, S24B, S25). Previews are 720p with motion blur off.
