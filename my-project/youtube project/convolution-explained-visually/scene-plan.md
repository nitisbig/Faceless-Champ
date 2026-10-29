# Convolution Explained Visually — Scene Plan

**Project folder:** `my-project/youtube project/convolution-explained-visually/`
**Audio:** `audio.mp3` — 453.96 s (07:33.96)
**Timing sources:** `cue-per-word.srt` (1,246 word cues, used for anchors), `normal-subtitle.srt` (phrase lines)
**Canvas:** 1920 × 1080, 30 fps (final export 1080p; 4K optional), background pure black `#000000`
**Library:** Faceless Champ core + kit (`faceless_champ`, `facelesschamp_kit`)

All timecodes below are **source-clock** times in the narration (mm:ss.mmm). Scene boundaries are snapped to word cues; `cue #N` refers to the one-based index in `cue-per-word.srt`. Boundaries marked `≈` must be snapped to the named word's cue at build time.

> Note: the generated audio uses a slightly earlier wording in the recap (e.g. "blur, sharpen, and find edges"). This plan follows the **audio**, not `voiceover.md`.

---

## 1. Visual system (applies to every scene)

### 1.1 Look

- **Mood:** black-stage "precision instrument". Pure black field, razor-thin luminous geometry, few elements per frame, generous negative space. Glow is a highlight tool, never a wash.
- **No background textures.** At most a faint dot grid (`dot_grid`, spacing 32, opacity ≤ 0.08) under math-plot scenes, so the black stays deep.
- **Depth:** 2D for arithmetic and plots, 2.5D (perspective layers, parallax, tilted planes) for transitions and stacking, true 3D (PyVista) only where depth explains something.

### 1.2 Semantic color (never break this mapping)

Define once in a project theme (`theme.py`, derived from `Theme.named("midnight")` with background forced to `#000000`). Scene code refers to token names, not hex.

| Token | Hex | Meaning everywhere in the video |
| --- | --- | --- |
| `signal` | `#22D3EE` (electric cyan) | the input signal / f / image / first die |
| `kernel` | `#FFB020` (amber) | the kernel / g / sliding window / second die |
| `overlap` | `#FF3D9A` (magenta) | products, overlap area, "multiply" moments |
| `output` | `#C6FF4A` (acid lime) | the result / f∗g / output image |
| `ink` | `#F5F7FA` | primary text, axes labels |
| `muted` | `#7C8597` | secondary text, ticks |
| `grid` | `#1A1F2B` | axes, grid lines, tracks |
| `alert` | `#FF4D4D` | cost / "slow" warnings only (S17) |

Viewers learn the mapping in the first minute. Cyan always means "signal", amber always means "kernel", and so on. This is the main teaching device of the whole video.

### 1.3 Typography

- Display / chapter titles: **Space Grotesk** (`role="display"`, `role="title"`), tracking +0.02.
- Labels / body: **DM Sans** (`role="label"`, `role="body"`).
- All numerals in tiles and readouts: **mono** font (tabular figures so counting digits don't jitter).
- Equations: **Manim `MathTex`** (Computer Modern), colored per token with `color_map` / `tex_to_color_map`.
- Text budget: on-screen text is a label, never the transcript. Titles ≤ 6 words, labels ≤ 4 words.

### 1.4 Motion language

- Entrances: `rate_func="emphasized"`, 0.45–0.7 s. Exits: fast `accelerate`, 0.3 s.
- Tile and bar motion: `Spring()` (slightly underdamped). The "slide" is the hero motion of this video, so make it feel physical: ease in, tiny settle.
- Every visual beat lands **0.10–0.20 s before** its spoken word (`cue.start - 0.15`).
- One idea per beat. Remove the old idea before the next arrives. No stacking of five things on screen.

### 1.5 Recurring motifs

1. **The Slide Rig:** a horizontal track, cyan signal tiles fixed on top, an amber kernel window gliding below, magenta "×" sparks where they overlap, a lime result tile dropping into the output row. Used in S03, S04, S05, S06, S09, S13 and the recap, so it must be built once as a reusable component (`components/slide_rig.py`).
2. **The Recipe Strip:** four glyph pills `FLIP · SLIDE · MULTIPLY · ADD`, each with a micro-icon. Introduced in S03, re-lit in S12 and S22.
3. **The Echo Ring:** expanding thin rings (sound wavefronts). Used in S01, S07, S18, S20, S23 to tie the cathedral metaphor through the whole video.

### 1.6 Chapter markers

The narration is continuous, so chapters get no title cards that stop the audio. Each chapter opens with a **corner eyebrow** (top-left safe area, `role="label"`, muted, 2.5 s): `01 · SLIDING BY HAND`, `02 · DICE`, `03 · SMOOTH SHAPES`, `04 · IMAGES`, `05 · THE SHORTCUT`, `06 · RECAP`. These also become YouTube chapter timestamps later.

---

## 2. Engine map

| Engine / feature | Faceless Champ entry point | Used for |
| --- | --- | --- |
| **skia-python** | `ExportSettings(backend="skia")` / `backend="auto"`; `VectorPath`, `PathData`, `Polyline(draw_by="x")`, `Text`, `Number`, `card_surface`, `LinearGradient` | All crisp 2D vector work: tiles, bars, plots, curves, grids, HUD, numbers |
| **moderngl** | `backend="moderngl"`; `EffectStack(glow=OuterGlow, bloom=Bloom, light_sweep=LightSweep, chromatic=ChromaticAberration)`, `ParticleField`, `DirectionalWipe`, `ZoomBlurTransition`, `LuminanceWipe` | Composition bloom, highlight glows, particle dust, wavefront shaders, chapter transitions |
| **manim** | `facelesschamp_kit.mathematics.EquationTransform`; core `prepare_manim` + `Viewport` | Every formula: integral definition, piece-by-piece reading, the convolution theorem, transfer function, the 123 × 11 working |
| **pyvista** | `ArchChamp` / `PyVistaSource` (`faceless-champ[3d]`) | True 3D: cathedral nave, 6×6 dice tower board, dice ridge-line, image height field, CNN feature-map stack, echo ribbons |
| **numpy / scipy** | inside `FunctionSource(fn, size, duration)` | **Real computation, never faked:** `np.convolve`, `scipy.signal.convolve2d`, `np.fft.fft`, Gaussian kernels |
| **Pillow / numpy** | `FunctionSource` / `Image.from_source` | Procedural test image for the image chapter (no external photo needed) |
| **Narration** | `SubtitleTrack.from_srt`, `CueScene(...).at_cue(n)`, `Sequence` + `Layer` with continuous audio | Chapter scenes on the source clock |

**Compositing:** final render with `backend="auto"` (hardware ModernGL → Skia fallback), `antialias=1`. One global `Layer` effect: `Bloom(radius=10, threshold=0.62)`. Glows on individual hero elements only.

**3D look rules (PyVista):** black background, no floor plane, no default lighting gradients. Geometry is rendered as emissive edges or thin tubes in token colors with a slight `Bloom` in composite. Cameras move slowly with deterministic keyframes (`ArchCamera`), and every camera move eases in and out.

---

## 3. Chapter map

| # | Chapter | Span | Scenes | Dimension |
| --- | --- | --- | --- | --- |
| 0 | Cold open: the cathedral | 00:00.030 – 00:53.080 | S01–S03 | 3D → 2.5D → 2D |
| 1 | Sliding by hand | 00:53.080 – ≈02:32.3 | S04–S07 | 2D, 2.5D |
| 2 | Dice | ≈02:32.3 – ≈03:23.4 | S08–S10 | 2.5D, 3D |
| 3 | Smooth shapes (continuous) | ≈03:23.4 – 04:28.850 | S11–S13 | 2D + manim |
| 4 | Images (2D convolution) | 04:28.850 – 05:22.710 | S14–S16 | 3D, 2D, 3D |
| 5 | The shortcut: Fourier | 05:22.710 – 06:45.170 | S17–S21 | 2D, 2.5D + manim |
| 6 | Recap and close | 06:45.170 – 07:33.960 | S22–S23 | 2.5D |

---

## CHAPTER 0 — COLD OPEN: THE CATHEDRAL

### S01 — One Clap, Many Echoes
**Time:** 00:00.030 → 00:19.720 (19.7 s) · **Dimension:** 3D → 2.5D
**Engines:** pyvista (nave), moderngl (wavefront shader + bloom), skia (waveform)
**Purpose:** Hook with sound you can *see*. The song and the room blend, and that blend is what we'll name.

**VO:** "Clap your hands inside a cathedral … a perfect blend of the song and the room."

- **01A · The nave (00:00.0–00:04.5).** Black. A gothic nave builds out of thin `ink` edge lines: a run of pointed arches receding in depth (PyVista procedural geometry: arches swept along the nave axis, rendered as edge lines only, opacity falling with depth). The camera holds low at the center aisle with a slow push-in. On "Clap" (cue #2), a single white flash point appears mid-aisle.
- **01B · Wavefronts (00:04.5–00:09.2).** From the flash, thin cyan rings expand (moderngl shader in a `FunctionSource`: analytic ring SDF, 1.5 px core plus glow). When a ring meets an arch it reflects as a fainter amber ring. "It rings, it echoes, it slowly fades" (cue #11–#20): each new reflection generation is dimmer. By "fades" the nave holds a lacework of decaying rings.
- **01C · The song (00:09.2–00:16.9).** The camera rises above the nave into a **top-down 2.5D** plane (the nave becomes a floor plan). A cyan waveform (the "song") streams in from the left at the bottom third. Under it, **amber echo copies** of that waveform peel off, each delayed and smaller, and stack in shallow perspective depth (z-offset layers, 4–5 copies). "pile on top of each other" (cue ≈#40): the copies collapse forward into one row.
- **01D · The blend (00:16.9–00:19.7).** The stacked copies sum into one thick **lime** waveform (real `np.convolve(song, room_impulse)`). Above it, a 3-element equation of pictograms fades in: `[cyan wave] ⊛ [amber decaying impulse] = [lime wave]`. The ⊛ symbol pulses once in magenta.

**Design notes:** The nave never exceeds 30% luminance, so the rings stay the brightest thing on screen. Use `LightSweep` once across the arches at 00:01.0 for a premium reveal.
**Out:** The ⊛ symbol stays and scales up into S02.

---

### S02 — It's Everywhere
**Time:** 00:19.720 → ≈00:35.40 (snap to "One", 15.7 s) · **Dimension:** 2.5D
**Engines:** skia (cards, word), moderngl (glow, transitions), numpy/scipy (real blur, edge, dice, multiplication)
**Purpose:** Name it, then a fast montage that previews every chapter. This is the retention promise.

**VO:** "That blending has a name, convolution, and it's everywhere … the long multiplication you learned in school."

- **02A · The name (00:19.72–00:23.0).** The ⊛ glyph slides left. The word **CONVOLUTION** types on in Space Grotesk display at cue #62 (00:21.69), white, with a magenta underline drawn left to right. A slight `ChromaticAberration` kick (0.15 s) on landing.
- **02B · Montage of four panels (00:23.0–00:34.0).** Four tall glass panels (`card_surface`, black fill, 1 px `grid` border) arranged in a 2.5D arc, each rotating into view on its cue:
  1. **Blur** (cue #67, 00:24.25): procedural photo tile, a soft amber 3×3 frame sweeps across and the image behind it turns soft (real Gaussian convolution).
  2. **Edges** (≈00:26.6, "neural networks see edges"): the same tile becomes a black image with lime edge lines (real Sobel kernel).
  3. **Dice** (cue #88, 00:30.40): two die glyphs whose sum histogram grows into a triangle.
  4. **Long multiplication** (≈00:32.0, "long multiplication"): `123 × 11` in mono with the result digits `1 3 5 3` flashing lime.
- Each panel holds about 2.5 s while the camera trucks past (parallax). The previous panel dims to 35%.

**Out:** All four panels shrink into four tiny dots that line up as a row and become the four pills of the Recipe Strip in S03.

---

### S03 — The Recipe and the Promise
**Time:** ≈00:35.40 → 00:53.080 (17.7 s) · **Dimension:** 2D
**Engines:** skia (recipe strip, slide rig), manim (tiny F{f∗g} teaser), moderngl (light sweep)
**Purpose:** Install the four-word recipe as a visual mantra and tease the Fourier payoff.

**VO:** "One simple recipe, flip, slide, multiply, and add … into a single, simple multiplication."

- **03A · Recipe Strip (00:35.4–00:40.5).** Four pills light up exactly on their words: **FLIP** (cue #103, 00:36.78, icon: a mirrored arrow), **SLIDE** (cue #104, 00:37.36, arrow), **MULTIPLY** (cue #105, 00:38.04, ×), **ADD** (cue #107, 00:39.31, Σ). Each pill's icon does its own micro-animation (the flip icon mirrors, the slide icon nudges right, and so on). Pill fill colors: flip and slide in `kernel`, multiply in `overlap`, add in `output`.
- **03B · From scratch (00:40.5–00:46.6).** "nothing but shapes sliding past each other": below the strip, a cyan box and an amber box glide past each other on a thin track. A lime trace draws under them (live preview of S13's triangle).
- **03C · Fourier tease (00:46.6–00:53.08).** The track compresses into a small panel at left. On the right a manim teaser renders `𝓕{f ∗ g} = 𝓕{f} · 𝓕{g}`, with the `∗` in magenta morphing into a plain `·`. Keep it small and slightly blurred (`GaussianBlur` 4 px), then defocus it: "we'll get there". A light sweep crosses the equation once.

**Out:** `DirectionalWipe` (left to right, softness 0.08) into Chapter 1.

---

## CHAPTER 1 — SLIDING BY HAND
Eyebrow: `01 · SLIDING BY HAND` at 00:53.1.

### S04 — Smoothing a Jumpy Week
**Time:** 00:53.080 → 01:21.560 (28.5 s) · **Dimension:** 2D
**Engines:** skia (plot, tiles, slide rig), numpy (moving average)
**Purpose:** First real convolution, a moving average, with the kernel named on screen.

**VO:** "Let's start with something you can do by hand … is exactly what convolution is."

- **04A · The jumpy week (00:53.1–01:02.1).** A minimal plot: seven day ticks (M T W T F S S, mono, muted), a cyan polyline drawing in point by point with values `20, 24, 18, 26` (then plausible continuation values to fill 7 days, e.g. `21, 25, 19`). Each point is a small glowing dot; the numbers pop above the first four exactly as spoken (≈00:58.1–01:02.1).
- **04B · The window (01:02.1–01:07.1).** An amber rounded window spans the first three points. Inside it, three `⅓` weight chips appear. Values move down into a small working line: `⅓·20 + ⅓·24 + ⅓·18`, with magenta "×" sparks on "multiply" (cue #176, 01:03.91) and the sum collapsing into a lime number `20.7` on "add" (cue #182, 01:05.69). A lime dot is placed on a second, smoother line.
- **04C · Slide and repeat (01:07.1–01:13.0).** On "slide" (cue #186, 01:07.44) the window glides one day right (Spring) and the process repeats faster: two more steps at normal speed, then the remaining steps sped up. A lime smoothed line draws behind the window as it goes.
- **04D · Name it (01:13.0–01:21.56).** The amber window lifts off the plot and floats center as three tiles `⅓ ⅓ ⅓`. The label **kernel** appears under it on cue #206 (01:14.21). Then "sliding a kernel along a signal": the plot dims, the cyan line and the window are shown together with labels `signal` (cyan) and `kernel` (amber). On "convolution" (cue #223, 01:20.15), the lime smoothed line glows and the label `output = signal ⊛ kernel` appears.

**Design notes:** The y-axis has no numbers; show only the four spoken values. Smoothed values are computed with `np.convolve(x, [1/3]*3, mode="valid")`.

---

### S05 — The Smallest Possible Example
**Time:** 01:21.560 → 02:00.730 (39.2 s) · **Dimension:** 2D (hero use of the Slide Rig)
**Engines:** skia (Slide Rig), moderngl (overlap glows)
**Purpose:** Teach the mechanics step by step. This is the core scene of the video, so the pacing must be exactly on the words.

**VO:** "Let's make it even smaller … So the answer is one, three, five, three."

- **05A · Set up (01:21.6–01:31.0).** Clear stage. Cyan tiles `1 2 3` (large mono numerals in 120 px rounded squares with a 2 px cyan stroke and a dark cyan inner fill) arrive one per word (≈01:25.5–01:27.5). Below, amber tiles `1 1` arrive at ≈01:29.5–01:30.6.
- **05B · Flip (01:31.0–01:33.6).** On "flip" (cue #252, 01:31.74) the amber pair rotates 180° around its vertical axis (2.5D card flip with perspective). A subtle "mirror" line flashes. Since the kernel is symmetric, the flip changes nothing visually; to show the action, mark the tiles `a b` → `b a` with small index dots under each tile so the order reversal is visible.
- **05C · Four positions (01:33.6–01:56.8).** "slide it in from the left" (cue #258, 01:33.79): the amber pair parks off-left under the track. Each step:
  1. Slide (Spring, 0.5 s) → overlapping tile pairs connect with magenta vertical "×" beams → small product chips `1×1` → sum → a **lime output tile** drops into an output row below.
  2. Position 1 (≈01:38.1–01:41.2): `1×1 = 1`.
  3. Position 2 (cue #282 "Slide", 01:41.76 → ≈01:47.9): two beams, `1×1 + 2×1 = 3`.
  4. Position 3 (cue #297, 01:47.88 → ≈01:54.0): `2×1 + 3×1 = 5`.
  5. Position 4 (≈01:54.0–01:56.8): only the 3 overlaps, `3`.
  The working line sits under the rig in DM Sans mono, and each product appears on its spoken word.
- **05D · The answer (01:56.8–02:00.73).** The output row `1 3 5 3` brightens tile by tile on each spoken number, then the whole row glows once.

**Design notes:** Overlap beams use `OuterGlow` (overlap color, radius 14). Non-overlapping tiles dim to 40% during each step so the eye goes straight to the pairs.
**Out:** The output row stays and lifts up into S06.

---

### S06 — Long Multiplication Is Convolution
**Time:** 02:00.730 → ≈02:15.90 (snap to "But", 15.2 s) · **Dimension:** 2D
**Engines:** manim (column multiplication layout + `TransformMatchingShapes`), skia (Slide Rig miniature)
**Purpose:** The "whoa" moment. Make the match unmistakable.

**VO:** "Now here's the surprise. Multiply 123 by 11 … sliding one list of digits across another."

- **06A (02:00.7–02:05.0).** The lime `1 3 5 3` row slides to the right half. On the left, a manim column multiplication writes in: `123` (cyan digits) `× 11` (amber digits), with partial-product rows `123` and `123` shifted one place, then a line, then the result `1353` (cue #331 "Multiply" at 02:01.96, result lands at cue #337, 02:04.98).
- **06B (02:05.0–02:11.0).** "one, three, five, three. The same digits": each result digit connects to its matching lime tile on the right with a thin magenta arc, one per spoken digit. On "same digits", both rows flash together.
- **06C (02:11.0–02:15.9).** The partial-product rows turn sideways: the two shifted `123` rows are revealed to be the sliding signal under two amber `1`s. Show the column sums `1 | 2+1 | 3+2 | 3` matching the Slide Rig positions. On "convolution" (cue #348, 02:12.36) the caption `long multiplication = convolution` appears in the label role.

**Design notes:** There are no carries in this example, which is why the match is perfect. Keep it that way and don't introduce carries.

---

### S07 — Why Flip? Listening Backwards
**Time:** ≈02:15.90 → ≈02:32.30 (snap to "Now" before "let's roll", 16.4 s) · **Dimension:** 2.5D
**Engines:** skia (timeline), moderngl (echo rings), numpy
**Purpose:** Give the flip an intuitive reason using the echo.

**VO:** "But why flip the kernel? Think of the echo … line up the present with the past."

- **07A (02:15.9–02:20.2).** A horizontal time axis with a bright "NOW" playhead at center-right. The left side is labeled `past` (muted). A small echo-ring icon pulses at the playhead.
- **07B (02:20.2–02:27.7).** The kernel appears as amber weight bars `[1.0, 0.6, 0.3]` that each reach back into the past from NOW, connecting "this instant" (tallest bar at NOW), "a quieter copy from a moment ago" (shorter bar, one step back) and "a fainter copy from before that" (shortest, two steps back). Cyan sound events on the timeline light up as each bar connects to them.
- **07C (02:27.7–02:32.3).** "The output looks backwards in time": a magenta arrow sweeps right to left along the bars. Then the kernel as originally written (`[1.0, 0.6, 0.3]`, left to right) is shown above, and the reversed reading below is revealed as the **flip** (the FLIP pill from the Recipe Strip flickers in the corner). On "the past" the timeline fades out.

---

## CHAPTER 2 — DICE
Eyebrow: `02 · DICE` at ≈02:32.3.

### S08 — Counting the Ways
**Time:** ≈02:32.30 → 02:53.080 (20.8 s) · **Dimension:** 2.5D → 3D
**Engines:** skia (bars, dice faces), pyvista (6×6 outcome tower board)
**Purpose:** Build the two-dice distribution by counting, so the convolution in S09 has something to explain.

**VO:** "Now let's roll some dice. A fair die … a single way to make twelve."

- **08A (02:32.3–02:42.4).** One crisp vector die (rounded cube, isometric, white edges, cyan pips) tumbles in and settles. Next to it, six equal cyan bars rise together, labeled `1/6` each (cue ≈#425 "six" area). "a flat shape": a thin lime line is drawn across their tops.
- **08B (02:42.4–02:53.08).** A second die (amber pips) lands. The camera tilts down into a **3D 6×6 outcome board** (PyVista): 36 small square plates, with the first die's faces along the cyan edge and the second die's along the amber edge. Each anti-diagonal (one per total) lights up as it is mentioned:
  - "total of two … only one way" → one corner plate glows.
  - "total of seven … six ways" (cue #452, 02:45.92) → the long anti-diagonal glows magenta.
  - "back to a single way to make twelve" → the far corner plate.
  Then the camera swings to look along the anti-diagonals: plates stack into towers by total, and the **triangle histogram** appears in 3D (heights 1,2,3,4,5,6,5,4,3,2,1).

**Design notes:** Tower faces are flat-shaded black with emissive token-colored edges. The camera move is one continuous 4 s eased orbit, not cuts.

---

### S09 — Dice as a Slide
**Time:** 02:53.080 → 03:09.600 (16.5 s) · **Dimension:** 2D
**Engines:** skia (Slide Rig in bar form), numpy (`np.convolve(p, p)`)
**Purpose:** Show the same triangle again, now produced by the recipe.

**VO:** "Watch it as convolution. Flip one row of six bars … The flat shape has become a triangle."

- **09A (02:53.1–02:58.6).** Flatten back to 2D. Top: six cyan bars. Below: six amber bars that flip (cue #477, 02:55.08) and slide (cue #484, 02:56.71) in from the left.
- **09B (02:58.6–03:08.1).** As they slide, the overlapping bar pairs light magenta and the overlap count (1, 2, … 6, … 1) drops as a lime bar into an output histogram at the bottom, labeled with the total (2 … 12). On "seven" (cue #500, 03:03.39) all six bars align, the peak bar flashes, and the label `6 / 36` appears. Then the overlap shrinks.
- **09C (03:08.1–03:09.6).** On "triangle" (cue #515, 03:08.89) the lime histogram outline is traced with a glowing line.

---

### S10 — Many Dice Become a Bell
**Time:** 03:09.600 → ≈03:23.40 (snap to "Now" before "let's make", 13.8 s) · **Dimension:** 3D
**Engines:** pyvista (ridge-line of distributions), numpy (repeated convolution)
**Purpose:** The central limit theorem as repeated convolution. A beautiful 3D payoff.

**VO:** "Add a third die and convolve again … seen as convolution repeated again and again."

- **10A (03:09.6–03:15.2).** The 2D triangle tilts back into 3D and becomes the second layer of a **ridge-line**: distributions for 1, 2, 3 … dice stacked in depth. Each new layer is computed by `np.convolve` with one more die. "third die … softens into a hill" (cue #529, 03:13.77) → layer 3 appears.
- **10B (03:15.2–03:20.1).** "Keep adding dice": layers 4, 5, 6, 8, 12 appear quickly. Their colors shift along a gradient from cyan toward lime. The camera slowly orbits about 25°. On "bell" (cue #539, 03:17.35) a smooth Gaussian curve overlays the last layer and glows.
- **10C (03:20.1–03:23.4).** The label `central limit theorem` appears (label role), with `= convolution, repeated` under it.

**Design notes:** Normalize each layer's area so the shapes widen and lower like real distributions (x scaled per n). Layers are thin emissive ribbons, not solid surfaces.

---

## CHAPTER 3 — SMOOTH SHAPES
Eyebrow: `03 · SMOOTH SHAPES` at ≈03:23.4.

### S11 — From Bars to Curves: The Formula
**Time:** ≈03:23.40 → ≈03:41.40 (snap to "It" before "looks intimidating", 18.0 s) · **Dimension:** 2D
**Engines:** skia (bars melting), manim (`MathTex` build of the definition)
**Purpose:** The jump from sum to integral, and the formula itself.

**VO:** "Now let's make our shapes smooth … d tau."

- **11A (03:23.4–03:29.4).** The bell from S10 reappears as 2D bars. The bars get thinner and multiply (12 → 48 → 200) until they merge into a smooth filled curve. The Σ symbol morphs into ∫ (manim `TransformMatchingShapes`) on "integral" (cue #568, 03:29.43).
- **11B (03:29.4–03:41.4).** The full definition writes on, center screen, large, in step with the narration:
  `(f ∗ g)(t) = ∫_{−∞}^{∞} f(τ) g(t − τ) dτ`
  Color map: `f` cyan, `g` amber, `∗` magenta, `(f∗g)` lime. Each symbol group writes as it is spoken ("F star g of t" ≈03:31.0, "integral from minus infinity to infinity" ≈03:32.8–03:35.3, "f of tau" ≈03:35.8, "times g of t minus tau d tau" ≈03:37.6–03:41.4).

---

### S12 — Reading It in Pieces
**Time:** ≈03:41.40 → 04:06.370 (25.0 s) · **Dimension:** 2D (equation on top, plot below)
**Engines:** manim (`EquationTransform` highlight and extract), skia (live plot), numpy
**Purpose:** Connect each piece of the formula to a geometric action. Recipe and formula become one thing.

**VO:** "It looks intimidating, but read it in pieces … Flip one shape, slide it to t, and measure the overlap."

- **Layout:** The equation shrinks to the top 25%. The bottom 70% is a plot with a τ axis. Cyan curve `f(τ)` is a smooth bump, amber curve `g(τ)` is a lopsided bump (asymmetric on purpose so the flip is visible).
- **12A · g(−τ) (≈03:43.6–03:46.5).** The `g(−τ)` piece is extracted and glows. In the plot, the amber curve mirrors across the vertical axis (animated reflection). The FLIP pill flickers.
- **12B · g(t−τ) (≈03:46.5–03:52.2).** The `t −` part glows. A lime vertical marker labeled `t` appears; the flipped amber curve glides to sit at t. The SLIDE pill flickers.
- **12C · multiply (≈03:52.2–03:55.2).** "multiply it by f point by point" (cue #630 multiply, 03:51.02): the product curve `f(τ)·g(t−τ)` appears as a magenta curve where the two overlap. The MULTIPLY pill flickers.
- **12D · integral = area (03:55.2–03:57.5).** "the integral measures the total area of the overlap" (cue #646, 03:56.34): the magenta region fills with a gradient (overlap color at 55% opacity), and its area is read out as a lime `Number`. The ADD pill flickers.
- **12E · Summary (03:57.5–04:06.37).** On "Flip" (cue #656, 04:00.44), "slide" (cue #659, 04:01.48) and "overlap" (cue #666, 04:03.34), the three pills light in sequence. The marker t sweeps across once and the lime area number leaves a trace that draws the output curve (f∗g)(t) above the plot (a preview of S13).

**Design notes:** All curves are computed numerically; the area is computed with `np.trapz`. The equation pieces stay highlighted in the same color as the matching plot element.

---

### S13 — Box ⊛ Box = Triangle
**Time:** 04:06.370 → 04:28.850 (22.5 s) · **Dimension:** 2D
**Engines:** skia (boxes, trace), numpy, moderngl (glow on trace)
**Purpose:** The classic example. A clean, satisfying geometric result.

**VO:** "Let's try the classic example. Two boxes … Convolution smooths, spreads, and blends."

- **13A (04:06.4–04:12.2).** On "boxes" (cue #673, 04:06.37) two unit boxes appear: cyan box fixed at center, amber box far left. A height `1` and width `1` dimension appear (thin dimension lines with ticks). The output plot below starts at zero ("no overlap, so the output is zero").
- **13B (04:12.2–04:22.4).** On "Slide" (cue #691, 04:12.92) the amber box glides right at constant speed (linear easing, unlike everywhere else, because the straight-line growth must look linear). The overlap region fills magenta. The lime trace draws in real time below: rising straight line, peak `1` on "peaks at one" (≈04:19.0), falling straight line.
- **13C (04:22.4–04:28.85).** On "triangle" (cue #724, 04:23.24) the trace glows and the label `□ ⊛ □ = △` appears. "smooths, spreads, and blends": three quick micro-beats on the triangle — the corners soften (blend with a Gaussian), the base widens, and the color transitions toward lime.

---

## CHAPTER 4 — IMAGES
Eyebrow: `04 · IMAGES` at 04:28.85.

### S14 — An Image Is a Grid of Numbers
**Time:** 04:28.850 → ≈04:47.90 (snap to "Fill", 19.1 s) · **Dimension:** 3D → 2D
**Engines:** pyvista (height field), skia (pixel grid, 3×3 kernel), Pillow/numpy (procedural test image)
**Purpose:** Turn the image into numbers and show the 2D slide.

**VO:** "Now let's step into two dimensions. An image is a grid of brightness values … Then slide one pixel over, and repeat."

**Source image (no external file):** a procedurally generated 96×96 grayscale picture with sharp, recognizable structure: a moon disc, a skyline of rectangles with lit windows, and a horizon line. Built with Pillow and numpy. Every result in this chapter is computed with `scipy.signal.convolve2d` on this image.

- **14A (04:28.9–04:33.0).** On "dimensions" (cue #735, 04:28.85) the image appears as a flat cyan-tinted picture. The camera tilts and the image **warps into a 3D height field** (PyVista `warp_by_scalar`): bright pixels rise as towers. "grid of brightness values": numbers fade onto a zoomed patch.
- **14B (04:33.0–04:37.9).** It flattens back to 2D. Zoom into a 9×7 patch of big pixel squares, each showing its brightness value (mono, small). "kernel becomes a small grid, three by three": an amber 3×3 frame drops in over the patch.
- **14C (04:37.9–04:47.9).** "multiply each pixel by the weight above it" (cue #761, 04:37.93): nine magenta product chips flash; on "add all nine" (cue #769–#771) they fly into one lime number, which drops into the matching cell of an **output grid** at the right. "slide one pixel over" (cue #781, 04:44.0): the frame steps right, and the next lime cell fills. Then the process accelerates: the frame scans the whole patch row by row, and the output grid fills in.

---

### S15 — Blur and Edges
**Time:** ≈04:47.90 → ≈05:07.70 (snap to "and" before "here's the remarkable part", 19.8 s) · **Dimension:** 2D
**Engines:** skia (kernel tiles, split view), numpy/scipy (real filters), moderngl (scan light)
**Purpose:** Two kernels with very different results, so viewers see that the kernel decides what happens.

**VO:** "Fill the kernel with one ninth everywhere … We've built an edge detector."

- **Layout:** Left, the 3×3 kernel card (big). Right, the full image in a 16:9 frame with a before/after split.
- **15A · Blur (04:47.9–04:54.1).** The kernel cells fill with `1/9` (amber). A thin amber scan line sweeps down the image; behind it the image becomes blurred (real `convolve2d` result, rows revealed with a `RectangleMask` wipe). On "blurs" (≈04:53.0) the split handle snaps to the middle: sharp on the left, blurred on the right.
- **15B · Edges (04:54.1–05:07.7).** The kernel resets. Cells are filled on their spoken words: `−1` left column (cyan-negative style, ≈04:54.5), `0` middle (≈04:56.5), `+1` right column (≈04:58.0). The image goes black except for a demo: the kernel hovers over a flat sky region and reads `0` ("cancel to zero", ≈05:01.4), then over the moon's left edge and the readout jumps to a bright lime value ("lights up", ≈05:04.7). Then a full scan: the output image shows **lime vertical edges on black** (real result, absolute value, normalized). On "edge detector" (cue #846, 05:06.29), the label appears.

**Design notes:** The edge output is the most striking frame in the chapter. Add a `Bloom` boost to the edge layer only (threshold 0.5).

---

### S16 — Networks Learn Their Own Kernels
**Time:** ≈05:07.70 → 05:22.710 (15.0 s) · **Dimension:** 3D
**Engines:** pyvista (feature-map stack), skia (filter grid), moderngl (bloom)
**Purpose:** The neural network connection (your audience responds to AI angles), kept brief.

**VO:** "and here's the remarkable part. Convolutional neural networks … like the one we just built by hand."

- **16A (05:07.7–05:13.9).** The image card tilts into 3D and becomes the first plane of a **CNN stack**: a series of glowing translucent feature-map planes receding into depth (PyVista planes textured with real convolution outputs of the test image using different kernels). A small amber kernel cube slides across the first plane, and light streams to the next plane.
- **16B (05:13.9–05:19.8).** "learn them from millions of examples": the camera pulls back. A grid of 16 tiny **learned-style filters** (procedural Gabor kernels at different orientations, labeled `illustrative`) flickers from noise into ordered stripes.
- **16C (05:19.8–05:22.7).** "like the one we just built by hand": the hand-built `−1 0 +1` kernel from S15 flies in and docks next to its matching learned filter (vertical orientation). The two flash together.

**Honesty note:** The filters are illustrative Gabor patterns, not weights from a trained model. The small `illustrative` label stays on screen.

---

## CHAPTER 5 — THE SHORTCUT
Eyebrow: `05 · THE SHORTCUT` at 05:22.7.

### S17 — The Problem: Sliding Is Slow
**Time:** 05:22.710 → 05:33.690 (11.0 s) · **Dimension:** 2D
**Engines:** skia (counter, dot field), moderngl (`ParticleField` for scale)
**Purpose:** Create tension: the cost that the theorem solves.

**VO:** "There's just one problem, sliding is slow … a trillion multiplications."

- **17A (05:22.7–05:26.0).** A long Slide Rig zooms out until tiles become dots. On "problem" (cue #889, 05:22.71) the slide motion visibly drags (frame-step stutter on the kernel only).
- **17B (05:26.0–05:33.7).** Labels `1,000,000 samples` (cyan) and `1,000,000 samples` (amber) appear on cues #895 and #899. On "trillion" (cue #904, 05:29.31) a `ParticleField` of tiny `alert`-red points floods the frame, and a mono counter spins up to `1,000,000,000,000` with the label `multiplications`. The counter text has a slight red glow.

---

### S18 — A Pure Tone Through the Cathedral
**Time:** 05:33.690 → ≈05:54.24 (snap to "We" before "can split", 20.6 s) · **Dimension:** 2.5D / 3D
**Engines:** pyvista (echo ribbons in depth) or moderngl shader, numpy, skia (waves)
**Purpose:** The key insight: sine waves pass through a convolution unchanged except in size and timing.

**VO:** "This is where the Fourier transform comes to the rescue … just scaled and shifted."

- **18A (05:33.7–05:37.8).** On "rescue" (cue #915, 05:33.69) the red particles dissolve. The cathedral nave from S01 returns faintly. On "tone" (cue #920, 05:35.51) one clean cyan sine wave enters.
- **18B (05:37.8–05:44.4).** "Every echo is a copy … delayed and quieter": amber copies of the sine peel off and stack in perspective depth (3D ribbons, PyVista tubes), each shifted in phase and smaller in amplitude.
- **18C (05:44.4–05:50.4).** "adding copies of one sine wave always gives back the same sine wave": the ribbons slide forward and sum into one **lime** sine with the **same frequency**. A ghost of the original cyan wave stays overlaid, so the viewer sees that only the amplitude (`× gain`) and phase (`→ shift`) changed; small labels mark both.
- **18D (05:50.4–05:54.2).** On "frequency … untouched" (cue #959, 05:49.34), three sine waves of different frequencies pass through a "convolution box" (a glass card labeled ⊛) and come out with the same frequencies at different heights.

---

### S19 — The Convolution Theorem
**Time:** ≈05:54.24 → 06:12.570 (18.3 s) · **Dimension:** 2D (dual panel)
**Engines:** manim (theorem), skia (spectra), numpy (`np.fft`)
**Purpose:** Split, scale, recombine, then state the theorem.

**VO:** "We can split any signal into frequencies … Convolution in time becomes simple multiplication in frequency."

- **19A (05:54.2–06:00.2).** A complex cyan signal splits (prism-like) into five stacked sine components (Fourier decomposition, real FFT of the signal). Each component passes under an amber gain bar (the kernel's frequency response) and is scaled. The scaled components merge back into the lime output, which exactly matches `np.convolve`'s result; a faint ghost of the slid version overlays to prove it.
- **19B (06:00.2–06:09.4).** On "theorem" (cue #988, 06:01.26), manim writes `𝓕{f ∗ g} = 𝓕{f} · 𝓕{g}` large and centered, with each piece glowing on its spoken words. The `∗` in magenta and the `·` in lime are linked by a thin arc.
- **19C (06:09.4–06:12.6).** A dual panel slides in under the equation: **TIME** (left), showing the Slide Rig busy sliding, and **FREQUENCY** (right), showing two spectra multiplied bar by bar into a result spectrum in one beat. Labels "convolution" ↔ "multiplication" appear on cue #1008 (06:08.80) and "frequency" (cue #1015, 06:11.63).

---

### S20 — From a Trillion to a Hundred Million, and Reverb
**Time:** 06:12.570 → ≈06:32.19 (snap to "And" before "the same idea", 19.6 s) · **Dimension:** 2D → 2.5D
**Engines:** skia (counters, waveforms), moderngl (rings), numpy (real reverb convolution of a short synthetic clip)
**Purpose:** Practical payoff: speed, then a real-world product people know.

**VO:** "With the fast Fourier transform, that trillion multiplications drops to roughly 100 million … as if it were played inside that cathedral."

- **20A (06:12.6–06:19.2).** The red trillion counter from S17 returns. On "trillion" (cue #1022, 06:14.25) it begins to collapse; it rolls down to `100,000,000` in lime ("roughly 100 million", ≈06:18.0). A horizontal bar comparison shows the length ratio: a long red bar shrinks to a tiny lime bar (labeled `FFT`). Note in muted text: `≈ 10,000× fewer`.
- **20B (06:19.2–06:27.6).** "reverb" (cue #1035, 06:20.18): a sleek audio-plugin card (glass, minimal knobs, no brand). "Record a single clap": a single white spike, then an amber decaying impulse-response waveform (the room's echo tail) draws in. The label `impulse response` appears on ≈06:26.5.
- **20C (06:27.6–06:32.2).** "any song with it": a cyan song waveform ⊛ amber impulse = lime reverberant waveform (real computation on a synthetic melody). On "inside that cathedral", the faint nave outline and Echo Rings return behind the lime waveform.

---

### S21 — Laplace, Z, and the Transfer Function
**Time:** ≈06:32.19 → 06:45.170 (13.0 s) · **Dimension:** 2D
**Engines:** manim (equations), skia (cards)
**Purpose:** Connect to your existing Laplace and Z-transform videos (end-screen hook).

**VO:** "And the same idea lives inside the Laplace transform and the Z-transform … quietly using the convolution theorem."

- **21A (06:32.2–06:37.5).** Two glass cards slide in side by side: **Laplace** (cue #1079, 06:33.82) with `Y(s) = H(s) · X(s)`, and **Z-transform** (cue #1083, 06:35.25) with `Y(z) = H(z) · X(z)`. In each, `X` is cyan, `H` amber and `Y` lime, matching the token colors.
- **21B (06:37.5–06:45.17).** "output equals the input times a transfer function": the `H` term in both cards glows amber. A thin line from each card converges on a center badge `convolution theorem` (cue #1104–#1105, 06:42.07–06:42.76).

**Design notes:** The card visuals echo your Laplace and Z-transform thumbnails so returning viewers recognize them. Mark both cards as end-screen targets in the edit.

---

## CHAPTER 6 — RECAP AND CLOSE
Eyebrow: `06 · RECAP` at 06:45.2.

### S22 — Everything We Discovered
**Time:** 06:45.170 → ≈07:21.40 (snap to "The" before "next time", 36.2 s) · **Dimension:** 2.5D
**Engines:** skia (mosaic cards, reused miniatures), moderngl (light sweep, glow), pyvista thumbnails (pre-rendered stills from S08/S10/S16)
**Purpose:** Reinforce the five ideas with the exact visuals viewers already saw.

**VO:** "So let's look back at what we discovered … frequency by frequency."

- **22A (06:45.2–06:52.7).** On "discovered" (cue #1113) the Recipe Strip returns large at the center; the pills light again on "Flip" (cue #1119, 06:48.44), "slide" (#1120), "multiply" (#1121) and "add" (#1123, 06:50.74). Then the strip moves to the top edge.
- **22B (06:52.7–07:16.7).** Five recap cards appear in a 2.5D arc, one per sentence, each a live miniature of its chapter:
  1. **Numbers** (≈06:52.7): smoothed line + `123 × 11 = 1353`.
  2. **Dice** (≈06:58.6): triangle → bell, lime outline (cue #1153 "bell", 07:01.41).
  3. **Curves** (≈07:04.6): box ⊛ box sliding, overlap fill (cue #1163 "overlap", 07:04.94).
  4. **Images** (≈07:08.0): split view sharp / blur / edges; then the learned-filter grid on "neural networks".
  5. **Fourier** (≈07:16.7): `𝓕{f∗g} = 𝓕{f}·𝓕{g}`.
  The camera trucks gently along the arc. The active card is at 100% and the others dim to 30%.
- **22C (07:16.7–07:21.4).** "all of that sliding collapses into a single multiplication, frequency by frequency" (cues #1202–#1204): all five cards collapse into a single lime "×" glyph.

---

### S23 — The Quiet Operation (End)
**Time:** ≈07:21.40 → 07:33.960 (12.6 s, plus end-screen hold) · **Dimension:** 3D → 2D
**Engines:** pyvista (nave), moderngl (rings, bloom), skia (end card)
**Purpose:** Close the loop with the cathedral image, then the subscribe call.

**VO:** "The next time you hear an echo, see a blurry photo, or roll a pair of dice … I'll see you in the next one."

- **23A (07:21.4–07:29.7).** Three quick callbacks, one per phrase: "echo" (cue #1211, 07:23.18) → Echo Rings in the nave; "blurry photo" → the skyline image softening; "pair of dice" → two dice settling, showing 3 and 4 (sum seven). Then everything fades except the nave, and the ⊛ symbol hangs glowing in the aisle ("the same quiet operation").
- **23B (07:29.7–07:33.96).** On "convolution" (cue #1235, 07:30.19) the ⊛ morphs into the wordmark **CONVOLUTION**. On "subscribe" (cue #1238, 07:31.53) a minimal subscribe pill outlines in white.
- **End screen:** hold on black with two slots (left: Fourier Transform video; right: Laplace Transform video) for the YouTube end-screen editor. If the platform requires it, the end-screen hold runs past 07:33.96; extend the timeline to 07:54.0 with silence (end-screen elements need at least 5 s and usually take up to 20 s).

---

## 4. Build stages (one per session)

Each stage ends with `--frame` stills at the listed times and `--audit`, then a short preview render, before moving on.

| Stage | Contents | Check stills at |
| --- | --- | --- |
| **A · Foundation** | `theme.py` (tokens, fonts), `timeline.py` (track loading, `CueScene` per chapter, continuous audio `Layer`, `Sequence`), `render.py` (test / preview / frame / range / full), shared components: `SlideRig`, `RecipeStrip`, `EchoRings`, `Tile`, `Eyebrow` | component test frames only |
| **B · Chapter 0** | S01–S03 (PyVista nave, ring shader, montage) | 00:03, 00:08, 00:18, 00:22, 00:30, 00:38, 00:50 |
| **C · Chapter 1** | S04–S07 | 01:05, 01:15, 01:32, 01:45, 01:59, 02:06, 02:25 |
| **D · Chapter 2** | S08–S10 | 02:40, 02:47, 03:04, 03:18 |
| **E · Chapter 3** | S11–S13 (manim prep first) | 03:28, 03:38, 03:48, 03:57, 04:19, 04:24 |
| **F · Chapter 4** | S14–S16 | 04:31, 04:42, 04:53, 05:06, 05:19 |
| **G · Chapter 5** | S17–S21 | 05:30, 05:46, 06:03, 06:16, 06:28, 06:40 |
| **H · Chapter 6** | S22–S23 + end screen | 06:50, 07:02, 07:12, 07:27, 07:32 |
| **I · Final** | Full-length 1080p render, full storyboard pass, audio-sync spot checks at 10 random cues, loudness check | — |

### Suggested folder layout

```
convolution-explained-visually/
  audio.mp3  cue-per-word.srt  normal-subtitle.srt  voiceover.md  scene-plan.md
  theme.py  timeline.py  render.py
  components/   slide_rig.py  recipe_strip.py  echo_rings.py  tiles.py  eyebrow.py
  sources/      test_image.py  ring_shader.py  signals.py   (FunctionSource producers)
  manim/        formula.py  theorem.py  long_multiplication.py  transfer.py
  pyvista/      nave.py  dice_board.py  ridge_line.py  height_field.py  cnn_stack.py
  scenes/       ch0_intro.py  ch1_sliding.py  ch2_dice.py  ch3_smooth.py
                ch4_images.py  ch5_fourier.py  ch6_recap.py
  output/       frames/  previews/  cache/
```

### Quality bar (applies to every stage)

- Every number on screen is computed by code from the same data the narration describes.
- Token colors never change meaning.
- Each frame has at most one focal point; anything else is at ≤ 40% opacity.
- Line weights: 1.5–2 px for plot lines and geometry at 1080p, 3 px for hero strokes, 1 px for grid.
- No text smaller than the `label` role. `--audit` must pass with no contrast or clutter warnings.
- 3D shots: one continuous, eased camera move per shot; no cuts inside a 3D move.
