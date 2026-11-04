# The Math Trick That Turns Any Function Into a Polynomial — Scene Plan

**Project folder:** `my-project/youtube project/taylor-series-any-function-into-a-polynomial/`
**Audio:** `audio.mp3`, 817.008 s (13:37.008). The last word ("time.", #2183) starts at 816.64 s. A 20 s end-screen hold follows (total 837.008 s).
**Timing sources:** `cue-per-word.srt` (2,183 word cues, used for every anchor) and `normal-subtitle.srt` (273 phrase lines).
**Canvas:** 1920 × 1080 design px, 30 fps, `stage` black. Claude renders 720p stills and previews only. You run `--final` (1080p) locally and 4K on Kaggle.
**Design system:** *Aion YouTube Design System First* (claude.ai artifact `UjKmD2Ly4RSgWq3opzcMPs`): its tokens, roles, type, motion and finish rules. Nothing in this plan adds a hex value.
**Library:** Faceless Champ core, used directly through `faceless_champ.draw` (Frame, Palette, hud, mathtype, space, mesh3d, noise, CueClock).
No project copies of `fx.py`, `typmath.py`, `space.py` or `hud.py` this time.

**Clock convention:** all times are narration source-clock **seconds**, the same numbers `cue(n)` returns in code.
Scene headers also give mm:ss. `#N` is the one-based index in `cue-per-word.srt`. Every visual beat lands 0.15 s before its word: `beat(N) = cue(N) − 0.15`.

> **The SRT text has ASR errors. The audio is correct.** Anchor these by **index**, never with `word()`:
> #31 "sign" = *sine* · #158 "factorial" = *factorials* · #543 "X0," = *at zero* · #611 "New" = *Near* · #1246 "sines" = *signs* ·
> #1349 "offense." = *a fence.* · **#1383 "0.0026." is spoken and true as 0.00026** (0.5⁵ / 120 = 0.000260).
> "E" (#171, #1505, #2076) is the number *e*; "I," (#1701) is *i*. Every digit token (#33 `0.5?`, #55 `0.4794.`, #243 `3X` …) is spoken as words.
> **Two aligner collapses** are hand-timed in `cues.py` `OVERRIDES` (measured in Stage A from a 20 ms loudness envelope):
> #694–700 ("the pattern. 2 is 2 times 1") are really spoken 254.58–257.18 ("Two" at 255.46), and #1118–1129 ("plus 1 over 120, 2.7167.
> The true value of e is 2.71828") at 415.82–424.02 ("2.7167" at 417.84, "The" at 420.28, "2.71828" at 421.56). Fix the subtitle text before uploading captions to YouTube.

---

## 0. What is better than the bell-curve plan

1. **Library first.** Faceless Champ now has the `draw` toolkit (Nov 2), so the project imports Frame, hud, mathtype, space, mesh3d, noise
   and `CueClock` instead of copying four modules. The only files copied over are `render.py` and `kaggle/`, both from the bell-curve project.
2. **Design system first.** `theme.py` maps a few local names onto Aion roles (§1.2). Colors, type sizes, strokes, opacity steps, radii and
   spacing all come from Aion tokens, so this video matches the channel's earlier videos.
3. **One hero component.** About 70 % of the film happens on one `TaylorStage` (§1.6): axes, the true curve, the polynomial copy, the
   error band and the "hug zone". The polynomial snaps into place with the same motion every time. Fewer bespoke scenes means faster builds and a
   more coherent film.
4. **Built scene by scene.** `render.py --scene S12` renders one scene's range and stills. Each stage below is 3–9 scenes, so each one fits a single session.
5. **Math checked before writing.** Every number on screen has already been computed (§5), and each coefficient comes from SymPy at build time.
   That check found two traps the narration hides: the "ten terms / seven decimals" line, and the third sine term (0.00026).
6. **Audio on the library chain.** SFX use `add_sfx(..., align="peak")` and come from the scenes' own beat constants. There is an optional
   `process_voice` A/B, and the final is mastered to −14 LUFS with true peak −1 dB, then checked with `delivery_report`.
7. **Performance budget per scene.** Static layers are cached offscreen (`Pen`), domain-coloring images are computed once per view, PyVista
   frames are cached on disk, and motion blur runs only on 4 named fast beats.

### Retention design (from the channel analysis used for the bell-curve plan)

- **Viewers leave at 0:20–0:40 and after about 60 s.** So frame 0 is already the most beautiful image in the film (a gold polynomial wrapping a sine
  wave inside the calculator's display), and nothing in the cold open holds still for more than 4 s.
- **Four open loops**, each paid off on screen with the *same* visual it opened with:
  1. *How does the chip know sin(0.5) = 0.4794?* Opened in S01–S02, paid off in S32–S33 (same chip, same digits, same 6-op flicker).
  2. *Why factorials show up uninvited.* Opened in S05, paid off in S17–S19 (the exponent drop).
  3. *e by hand, from fractions.* Opened in S05, paid off in S26 (the fraction bar and the digit lock).
  4. *A smooth curve where the trick fails, for a reason you cannot see on the graph.* Opened in S05 (poles glimpsed under the floor),
     paid off in S41 (the same tilt, now all the way).
- **Pattern interrupts:** the dominant visual changes every 8–12 s, and the 4 s narration pauses (S26C, S32C) are filled with deliberate zoom beats.
- **Top video:** *Why e Is Everywhere*. The e beats are lime from the start, the outro teases e^(ix), and the end screen links that video.

---

## 1. Visual system

### 1.1 Look

- **Mood: "gold copy, ink original."** The true function is a calm `ink` curve, like the original drawing. The polynomial is a luminous
  `gold` line that tries to match it. It snaps on, tightens and climbs. The viewer watches one line learn to be another.
- Pure black `stage`, thin luminous geometry, one focal point per frame, non-focal elements at `opacity-nonfocal` (0.4) or less.
- **Depth vocabulary:** **2D** for graphs and formulas (most of the film). **2.5D** (`draw.space.Camera` projecting skia geometry) for the
  stacked-pieces motif (S04, S21C, S50), the tilt into the complex plane (S40, S42C) and the recap card arc. **True 3D** (PyVista) only where
  depth teaches: the |f(z)| surface with its two poles (S41, S43) and the machine-learning loss surface (S44C).
- A faint `grid` dot floor (`opacity-grid`, pitch `space-4`) sits under every plot. No textures and no gradients. The black stays black.

### 1.2 Color: local names mapped onto Aion roles (`theme.py`)

| Local token | Aion role → hue | Means, everywhere in this video |
| --- | --- | --- |
| `original` | `ink` | the true function f(x): cos, sin, eˣ, the hill 1/(1+x²) |
| `copy` | `role-law` → `hue-gold` | the Taylor polynomial Pₙ, its terms, the hug zone, the pieces in S04 |
| `x` | `role-input` → `hue-blue` | the variable x in every formula, the probe, the input 0.5, the center a, the speed v |
| `error` | `role-spread` → `hue-violet` | the gap between f and Pₙ (the error band), and the imaginary direction i |
| `fact` | `role-product` → `hue-magenta` | factorials, dropped exponents, × moments, the × pad |
| `result` | `role-output` → `hue-lime` | the number e, and correct digits that lock (e, sin 0.5, 0.8) |
| `plus` / `minus` | `role-plus` / `role-minus` → orange / teal | + and − signs in a series, derivative values +1 / −1, the + and − pads |
| `circle` | `role-trace` → `hue-pink` | circles and rotation: the unit circle, the derivative wheel, the convergence disk, pendulum trails, e^(ix) |
| `alert` | `role-alert` → `hue-red` | **Chapter 7 only:** divergence outside |x| < 1, the poles at ±i |
| plane | `plane-major` / `plane-minor` | complex-plane grid lines |

- **Formulas are colored by role:** x blue, factorial denominators magenta, signs orange/teal, e lime, i violet. Digits and brackets stay `ink`.
- The **eˣ curve stays `ink`** like every other original. Only the *symbol* e and the *value* of e are lime. Keeping "ink original, gold copy"
  consistent matters more inside this film.
- Red appears **once**: Chapter 7. The S05 teaser previews the break with gold whipping off-frame, never red.
- At most five hues per frame. Domain coloring (S41–S42) is the one place the full hue wheel appears without a role, as the system allows.

### 1.3 Typography (Aion)

- **Space Grotesk** (`hero`, `headline`, `heading`): statements and card titles. **DM Sans** (`label`, `readout`, `caption`, `eyebrow`, `tick`): labels,
  pills and readouts. Every counter uses tabular figures (`hud.tabular`).
- **Math:** Typst (New Computer Modern Math) through `draw.mathtype`, for every formula, morph and live number (`mathtype.number`).
- **Title card serif: Cormorant Garamond** (decided in Stage A). Aion asks for STIX Two Text, which is not bundled; the Stage A sheet compared
  Typst New Computer Modern and Cormorant Garamond, and Cormorant was chosen. Set titles with `fr.text(..., "serif", 112, 600)`
  (`theme.SERIF`, `theme.TITLE_WEIGHT`) and `text_path` with the same arguments for light sweeps. Formulas stay in Typst.
- Text budget: titles ≤ 6 words, labels ≤ 4. No on-screen questions and no exclamation marks. Use real minus signs (−) and real multiplication signs (×).

### 1.4 Motion: three signature motions, identical every time

1. **The hug** (hero motion of the film): Pₙ → Pₙ₊ₖ by interpolating coefficients on an under-damped spring (0.7 s, one ~4 % overshoot).
   On settle: a soft glow pulse on the newly matched stretch, a `light` sweep along the hug zone, and the two gold hug brackets spring outward to the
   new width with their readout (`±0.70`). The violet error band shrinks with the curve. The viewer learns that this motion means "one more term".
2. **The exponent drop:** the exponent glyph leaves the superscript, falls along a short gravity arc to the front (0.45 s, back-ease
   landing, magenta trail) and a small × spark multiplies it in. Used in S15, S17, S19 and S47.
3. **The digit lock:** a tabular readout whose digits turn `result` lime (with a one-frame glint) when they match the target. Unmatched digits stay
   `muted`. Used in S02, S26–S27, S32, S37 and S48.

Entrances are ease-out or back, 0.45–0.7 s. Exits accelerate, 0.3 s. Camera moves in 3D follow eased `space.orbit_path` keys, never linear.

### 1.5 Finish (Frame, Aion "Finish")

| Effect | `faceless_champ.draw` call | Where |
| --- | --- | --- |
| Glow (`tight`, `opacity-glow`) | `glow=` on the gold copy, hero dots, locked digits | hero elements only |
| Light sweep | `fr.light_sweep(path, u)` | every hug settle, title card, e reveal, sin(0.5) answer, end card |
| Chromatic kick | `chroma_kick(t, at)` → `fr.chroma` | **once:** the pole explosion, S41B |
| Camera shake | `noise.shake(t, 6 · env(...))` | **once:** S41B |
| Vine tip | `noise.wobble(tip_points, t, 2.0, fps=12)` | the growing tip of the copy in S31C |
| Zoom blur | `fr.zoom_blur` | chapter pushes, the S01 pull-back, S05 whip-pans |
| Depth of field | `with fr.blurred(sigma):` | S04 planes, S47–S48 card arc |
| Motion blur | `motion_blur(..., weight=)` (finals only) | S01 pull-back, S05 whips, S27B factorial bars, S31C vine climb |
| Grade | `fr.vignette(0.5)`, `fr.grain(t, 0.04)` | every frame |

### 1.6 Components (build once in Stage A, reuse everywhere)

1. **`components/taylor.py`** (pure math, no drawing; unit-tested). `coeffs(f, n, a=0)` via `sympy.series`; Horner `evaluate(c, xs)`;
   `hug_zone(f, n, tol=0.01)`; `partial_sums(...)`; `ops(c)` returns the exact × / + program of a Horner evaluation (S02 flicker, S33 tally);
   `derivs_at(f, a, k)` for the ladder. Values are cached at import. No number on screen is typed by hand.
2. **`components/stage.py` → `TaylorStage`** (the hero). Axes in `axis` (switched to `ink` when focal), `tick` labels, the dot floor, the
   `original` curve (2.5 px ink), the `copy` curve (`stroke-curve` 4 px gold, glow 0.6) clipped to the frame, the error band (violet at
   `opacity-ghost`), the hug brackets and readout, a blue probe (Aion ParameterSlider marker), a circular **loupe** (any magnification, linked by a
   hairline), and `hug(t, n_from, n_to, t0)`, the signature motion. Static layers (axes, floor, ticks) render once per output size into an
   offscreen `Pen`.
3. **`components/ladder.py` → Derivative Ladder:** a glass card of rows `f(0)`, `f′(0)`, `f″(0)` …, filled one at a time with Typst values in role colors
   (+1 orange, −1 teal, 0 muted, skipped rows struck through to a ghost). Recurs in S12–S17, S20, S25, S29 and S47.
4. **`components/chip.py` → The Chip:** a square die (`stage-raised`, `line` rim, `radius-sm`) with pin rows, faint traces carrying light pulses,
   a 2×2 core of operation pads (+ orange, − teal, × magenta, ÷ ink) and a display window. This is geometry, not an icon. S01–S03, S09, S28, S33, S47.
5. **`components/stack25d.py` → Term Stack:** gold term curves on floating hairline frames in depth (`space.Camera`), which slide together into
   their sum when the camera reaches the front view. S04, S21C, S50.
6. **`components/digits.py` → Digit Lock** readout (§1.4.3), on `hud.tabular`.
7. **`components/plane.py` → Complex plane** (Aion ComplexPlane): grids, `i` ticks in violet, pole glows, and `domain_image(fn, view, size)`, a
   numpy domain coloring (hue = arg along the Aion hue wheel, brightness bands = log|f|), computed once per (fn, view, size).
8. **`pv3d/` (on `draw.mesh3d`):** `pole_surface(height_scale)` (|1/(1+z²)| over the plane with the domain-colored texture, poles clipped
   off-frame), `loss_surface()` and `hessian_bowl(p)`. Renders are camera-matched to `space.Camera` and cached on disk.
9. **`components/pendulum.py`:** two pendulums, exact (`scipy.integrate.solve_ivp`, rtol 1e-10) and small-angle (closed form), sampled by t.
10. **Eyebrow:** `hud.eyebrow`, top-left at (96, 96). Not shown in the cold open.

---

## 2. Engine map

| Engine | Entry point | Used for | Why |
| --- | --- | --- | --- |
| **skia-python** via `faceless_champ.draw` | one `draw_scene(draw, duration, ...)` per chapter; `Frame`, `hud`, `space`, `noise` | every 2D and 2.5D element: curves, plates, chip, ladder, digit locks, transitions, the 2.5D tilts | deterministic CPU frames; `workers=2` chunked renders are identical on this machine and on Kaggle |
| **Typst** (`~/.local/bin/typst`) | `draw.mathtype`: `draw`, `morph`, `number`, `tc` | every formula, term-by-term builds, the exponent drop (glyph flight), `x → 1` and `x → ix` morphs, live numbers | no LaTeX on this machine; `morph` flies matched glyphs, which the exponent drop needs |
| **SymPy** | `components/taylor.py` | Taylor coefficients, derivative ladders, the relativistic expansion (S45), powers of i (S49) | coefficients are derived, not typed |
| **NumPy / mpmath** | Horner evaluation, hug zones, partial sums, domain coloring, Newton steps; mpmath for reference digits | all live curves and readouts | exact and fast |
| **SciPy** | `solve_ivp` | the true pendulum vs the small-angle pendulum (S34) | the "sin x ≈ x" claim is shown, not asserted |
| **PyVista** (VTK 9.7) | `draw.mesh3d.render(..., cache=)` + `composite` | the pole surface (S41, S43) and the loss surface with its quadratic bowl (S44C) | true 3D where height *is* the lesson; cached, so each frame renders once |
| **noise** (opensimplex) | `draw.noise` | the S41 shake, the vine-tip wobble, chip-trace pulse jitter | pure in t, so chunk-safe |
| Manim 0.22 | — | **not used** | Typst `morph` covers every formula move; no LaTeX; avoids a second preparation pass |
| ModernGL | — | **not used** | Frame's glow layer already blooms; the GPU is an integrated Radeon R4; the skia path is what `workers` forks |
| pymunk (`draw.physics`) | — | **not used** | no rigid bodies; the pendulum is an ODE solved exactly |

**Compositing order per frame:** PyVista RGBA (if any) → skia geometry → glow canvas → vignette and grain.
**Determinism:** there is no unseeded randomness. noise is pure in t, and the only random set (S01 trace pulses) uses `numpy.random.default_rng(7)` created at import.

---

## 3. Chapter map

| # | Chapter | Span (s) | mm:ss | Scenes | Eyebrow |
| --- | --- | --- | --- | --- | --- |
| 0 | Cold open: the calculator's secret | 0.000 – 80.840 (#218) | 00:00 – 01:20 | S01–S06 | — |
| 1 | Why polynomials | 80.840 – 132.880 (#371) | 01:20 – 02:12 | S07–S10 | `01 · WHY POLYNOMIALS` |
| 2 | Copying a curve | 132.880 – 251.520 (#691) | 02:12 – 04:11 | S11–S17 | `02 · COPYING A CURVE` |
| 3 | Why factorials | 251.520 – 285.920 (#778) | 04:11 – 04:45 | S18–S19 | `03 · WHY FACTORIALS` |
| 4 | The recipe | 285.920 – 359.560 (#987) | 04:45 – 05:59 | S20–S23 | `04 · THE RECIPE` |
| 5 | e from fractions | 359.560 – 444.240 (#1177) | 05:59 – 07:24 | S24–S27 | `05 · e FROM FRACTIONS` (e in serif italic, lime) |
| 6 | Wrapping the sine wave | 444.240 – 568.280 (#1495) | 07:24 – 09:28 | S28–S34 | `06 · WRAPPING THE SINE` |
| 7 | Where the trick breaks | 568.280 – 693.000 (#1839) | 09:28 – 11:33 | S35–S43 | `07 · WHERE IT BREAKS` |
| 8 | Why it matters | 693.000 – 748.080 (#2004) | 11:33 – 12:28 | S44–S46 | `08 · WHY IT MATTERS` |
| 9 | Recap and outro | 748.080 – 817.008, end screen to 837.008 | 12:28 – 13:57 | S47–S51 | `09 · RECAP` |

Each eyebrow fades in 0.2 s after the chapter starts. Chapter changes are in-frame transitions (push, whip or tilt). The narration never stops.

**YouTube chapters (phase 5 description):** 00:00 The calculator's secret · 01:20 Why polynomials · 02:12 Copying a curve ·
04:11 Why factorials · 04:45 The recipe · 05:59 e from fractions · 07:24 Wrapping the sine wave · 09:28 Where the trick breaks ·
11:33 Why it matters · 12:28 Recap.

### Scene index

| Scene | Title | Start → end (s) | Dur | Dim | Heavy engine |
| --- | --- | --- | --- | --- | --- |
| S01 | The calculator's secret | 0.000 → 14.840 | 14.8 | 2.5D | chip, zoom blur |
| S02 | No circle inside | 14.840 → 24.560 | 9.7 | 2D | digit lock |
| S03 | How does it know waves? | 24.560 → 33.440 | 8.9 | 2D | — |
| S04 | Rebuilt from simple pieces | 33.440 → 52.320 | 18.9 | 2.5D | Term Stack |
| S05 | The promise | 52.320 → 76.840 | 24.5 | 2D/2.5D | 5 vignettes |
| S06 | Title card | 76.840 → 80.840 | 4.0 | 2D | TitleCard |
| S07 | What a computer finds easy | 80.840 → 100.000 | 19.2 | 2D | Typst |
| S08 | Friendly functions | 100.000 → 109.400 | 9.4 | 2D | — |
| S09 | Circles, growth, areas | 109.400 → 121.680 | 12.3 | 2D | 3 framed panels |
| S10 | The impostor plan | 121.680 → 132.880 | 11.2 | 2D | TaylorStage |
| S11 | The cosine hill | 132.880 → 142.440 | 9.6 | 2D | TaylorStage |
| S12 | Attempt 1: a constant | 142.440 → 163.600 | 21.2 | 2D | TaylorStage, ladder |
| S13 | Match the slope | 163.600 → 177.360 | 13.8 | 2D | TaylorStage |
| S14 | The bend | 177.360 → 186.400 | 9.0 | 2D | curvature comb |
| S15 | How much x²? | 186.400 → 214.360 | 28.0 | 2D | exponent drop |
| S16 | The parabola hugs | 214.360 → 225.560 | 11.2 | 2D | the hug |
| S17 | The fourth derivative | 225.560 → 251.520 | 26.0 | 2D | exponent drop |
| S18 | Two, twenty-four | 251.520 → 267.720 | 16.2 | 2D | Typst |
| S19 | The exponent drops | 267.720 → 285.920 | 18.2 | 2D | exponent drop |
| S20 | One recipe | 285.920 → 312.290 | 26.4 | 2D | Typst, ladder |
| S21 | Each term has one job | 312.290 → 338.000 | 25.7 | 2D → 2.5D | loupe, Term Stack |
| S22 | Series vs polynomial | 338.000 → 349.680 | 11.7 | 2D | the hug ×5 |
| S23 | Any center | 349.680 → 359.560 | 9.9 | 2D | live re-expansion |
| S24 | Its own slope | 359.560 → 377.160 | 17.6 | 2D → 2.5D | — |
| S25 | All ones | 377.160 → 397.600 | 20.4 | 2D | the hug ×4 |
| S26 | Out comes e | 397.600 → 424.650 | 27.1 | 2D | fraction bar, loupe, digit lock |
| S27 | Factorials win | 424.650 → 444.240 | 19.6 | 2D | bar race |
| S28 | Back to the calculator | 444.240 → 453.360 | 9.1 | 2D | chip |
| S29 | The derivative loop | 453.360 → 471.200 | 17.8 | 2D | derivative wheel |
| S30 | The sine series | 471.200 → 484.000 | 12.8 | 2D | Typst |
| S31 | The vine climbs | 484.000 → 506.160 | 22.2 | 2D | the hug ×9, noise |
| S32 | The calculation | 506.160 → 536.120 | 30.0 | 2D split | loupe, digit lock |
| S33 | The secret revealed | 536.120 → 556.160 | 20.0 | 2D | chip |
| S34 | Small angles: the pendulum | 556.160 → 568.280 | 12.1 | 2D | SciPy |
| S35 | So far, so good | 568.280 → 582.200 | 13.9 | 2D | 3 lanes |
| S36 | The innocent hill | 582.200 → 603.320 | 21.1 | 2D | TaylorStage |
| S37 | Inside: it settles | 603.320 → 610.160 | 6.8 | 2D | zigzag sum |
| S38 | At the edge: it flips | 610.160 → 621.000 | 10.8 | 2D | zigzag sum |
| S39 | Beyond: it explodes | 621.000 → 631.960 | 11.0 | 2D | red divergence |
| S40 | Off the graph | 631.960 → 640.960 | 9.0 | 2.5D tilt | space.Camera |
| S41 | The hidden explosion | 640.960 → 658.840 | 17.9 | 3D | **PyVista**, chroma, shake |
| S42 | The circle of trust | 658.840 → 679.360 | 20.5 | 3D → 2D → 2.5D | domain coloring |
| S43 | Radius of convergence | 679.360 → 693.000 | 13.6 | 2D + 3D peek | PyVista (cached) |
| S44 | Everywhere | 693.000 → 712.560 | 19.6 | 2D + 3D | **PyVista** loss surface |
| S45 | Einstein's series | 712.560 → 735.000 | 22.4 | 2D | Typst morph |
| S46 | Newton was never wrong | 735.000 → 748.080 | 13.1 | 2D | — |
| S47 | What we built, part 1 | 748.080 → 774.280 | 26.2 | 2.5D arc | card arc, DOF |
| S48 | What we built, part 2 | 774.280 → 792.760 | 18.5 | 2.5D arc | card arc, DOF |
| S49 | Next time: e meets i | 792.760 → 811.680 | 18.9 | 2D | Typst sort |
| S50 | One term at a time | 811.680 → 817.008 | 5.3 | 2.5D | Term Stack |
| S51 | End screen | 817.008 → 837.008 | 20.0 | 2D | loop |

---

## CHAPTER 0 — COLD OPEN: THE CALCULATOR'S SECRET

### S01 — The Calculator's Secret
**Time:** 0.000 → 14.840 (#34 "There") · 00:00.000–00:14.840 · **Dim:** 2.5D
**Engines:** skia (Chip, TaylorStage inside the display), `space.Camera` push, zoom blur, motion blur (final)
**Purpose:** The hook. Frame 0 is the payoff image, then the mystery: a machine that only knows four operations.
**VO:** "Your calculator has a secret. Deep inside, it can only do a few simple things. Add, subtract, multiply, divide. That's it. So what happens when you ask it for the sine of 0.5?"

- **01A · The secret (0.0–2.5).** Frame 0: an extreme close-up of glowing gold, mid-wrap on an ink sine wave (degree 9 climbing to 13, one term
  every 0.4 s). Nothing is static on the first frame. On "calculator" (#2, 0.33) the camera **pulls back fast** (zoom blur, motion blur in finals) through
  the display glass to reveal the Chip floating on black, its traces lighting inward with light pulses. On "secret" (#5, 1.49) the display frosts
  (`blurred(8)`) and the wave dims behind it: hidden.
- **01B · Deep inside (2.5–6.0).** On "Deep inside" (#6–7, 2.52–2.89) the camera pushes into the die. Pin rows slide past in parallax and the
  2×2 operation core rises out of the dark. On "few simple things" (#13–15, 4.54–5.45) the four pads draw their outlines.
- **01C · Four operations (6.0–10.7).** The pads light on their words, each with a pulse ring and a soft tick: **+** orange on "Add" (#16, 6.04),
  **−** teal on "subtract" (#17, 6.62), **×** magenta on "multiply" (#18, 7.78), **÷** ink on "divide" (#19, 8.78). On "That's it." (#20–21, 9.64–10.24) all four pulse once
  together and everything else on the die drops to `opacity-ghost`.
- **01D · The question (10.7–14.8).** On "ask it" (#27–28, 12.05–12.24) the display clears. On "sine of 0.5" (#31–33, 13.40–13.60) it types `sin(0.5)` in Typst
  (0.5 blue), with a blinking caret. No answer yet.

**SFX:** a pulled whoosh at 0.33; one tick per pad (pitched + − × ÷); a typing tick on #31 and #33.
**Stills:** 0.2, 1.8, 7.9, 14.2

---

### S02 — No Circle Inside
**Time:** 14.840 → 24.560 (#56 "How") · 00:14.840–00:24.560 · **Dim:** 2D
**Engines:** skia (Chip, x-ray scan, ghost geometry), `taylor.ops` (the real op sequence), Digit Lock
**Purpose:** Remove the obvious explanations, then make the answer appear "in a blink". Plants open loop 1.
**VO:** "There is no tiny circle hidden in the chip. No little triangle being measured. And yet, in a blink, it answers. 0.4794."

- **02A · X-ray (14.8–19.4).** A thin `light` scan band sweeps down the die. On "circle" (#38, 15.77) a pink unit circle ghost forms inside the scan.
  On "hidden in the chip" (#39–42, 16.20–16.97) the band passes and it dissolves with a muted strike. On "little triangle" (#44–45, 17.46–17.89)
  a pink right triangle with a 0.5 rad angle arc appears. On "being measured" (#46–47) a ruler tick crawls along its side, then it dissolves the same way.
- **02B · In a blink (19.4–22.1).** On "And yet" (#48–49, 19.44–19.74) the four pads go dark. On "blink" (#52, 20.54) they flash the **exact
  op program of the 3-term sine polynomial** (from `taylor.ops`: × × + × + ×) in 0.6 s, like an instruction trace. The same flicker returns in S33.
- **02C · The answer (22.1–24.6).** On "answers" (#54, 22.09) the display shows `0.4794`. Each digit lands as it is spoken
  (#55 starts 22.16; spread the six spoken tokens across about 22.2–24.3, checked by ear) in lime, with a digit-lock glint. A `light` sweep crosses the display.
  The rest of the pause is a slow push-in on the digits, with the gold wave faintly visible *behind* them: the secret, hinted.

**SFX:** a soft scan hum; 6 ultra-short ticks on the op flicker; a rising pop per digit; a chime on the sweep.
**Stills:** 15.9, 18.0, 20.8, 23.8

---

### S03 — How Does It Know Waves?
**Time:** 24.560 → 33.440 (#83 "It") · 00:24.560–00:33.440 · **Dim:** 2D
**Engines:** skia (Chip, TaylorStage axes)
**Purpose:** Turn the mystery into the film's question, then promise a beautiful answer.
**VO:** "How does a machine that can only add and multiply know anything about waves? The answer is one of the most beautiful tricks in all of mathematics."

- On "add" (#63, 26.12) and "multiply" (#65, 26.59) only the + and × pads glow. On "waves" (#69, 28.53) an ink sine wave **unrolls out of the display** and
  runs to the right edge of frame.
- On "The answer" (#70–71, 29.28–29.38) the camera rises. The chip slides out at the bottom left and the wave settles centered on the dot floor. On "beautiful" (#77, 30.64)
  a `light` sweep runs along the wave. On "tricks" (#78, 31.15) a faint gold glimmer runs along it for 0.4 s: the copy, hinted.

**SFX:** a soft riser into "beautiful". **Stills:** 26.4, 28.9, 31.2

---

### S04 — Rebuilt From Simple Pieces
**Time:** 33.440 → 52.320 (#136 "In") · 00:33.440–00:52.320 · **Dim:** 2.5D
**Engines:** Term Stack (`space.Camera`, `orbit_path`), TaylorStage (eˣ), depth of field
**Purpose:** Show the core idea as one picture: simple pieces stacked in depth sum into a copy of a curve.
**VO:** "It says that almost any smooth curve, a wave, a growth curve, a slow decay, can be rebuilt out of the simplest pieces we know, a constant, a straight line, a parabola, a cubic. Stacked one on top of another until the copy hugs the original so tightly you cannot tell them apart."

- **04A · Smooth curves (33.4–39.6).** Three thin ink curves fan in as floating strips: a wave on "wave" (#91, 36.01), eˣ on "growth curve" (#93–94, 36.65–37.19),
  and e^(−x/2) on "slow decay" (#96–97, 37.93–38.58). On "rebuilt" (#100, 39.11) the wave and decay strips fall back into blur and the growth curve centers.
- **04B · The pieces (39.6–46.1).** The camera swings to an oblique view (yaw 35°, pitch 18°). Four hairline frames float in depth, one per piece,
  each holding a gold curve with its Typst label: on "constant" (#109, 41.95) `1`; on "straight line" (#111–112, 42.78–43.41) `x`; on "parabola" (#114, 44.01) `x²/2`;
  on "cubic" (#116, 45.08) `x³/6`. These are the eˣ pieces, and exactly the four the narration names.
- **04C · Stacked (46.1–49.9).** On "Stacked one on top of another" (#117–122, 46.08–47.38) the camera orbits to the front view and the frames slide together.
  Their curves add into the gold P₃. On "the copy hugs the original" (#125–128, 48.73–49.39) the ink eˣ appears behind it, and the violet error band shows
  the gap far from 0.
- **04D · Can't tell them apart (49.9–52.3).** On "so tightly" (#129–130, 49.89–50.03) **the hug** runs P₃ → P₄ → P₆ → P₈ (fast, 0.45 s each). The band
  vanishes inside x ∈ [−2, 2]: P₈(2) misses e² by 0.0003. On "apart" (#135, 51.78) the hug brackets slide off both frame edges and a light sweep runs the whole curve.

**SFX:** a soft glass tick per piece; one resolve per hug. **Stills:** 37.5, 44.5, 48.0, 51.5

---

### S05 — The Promise
**Time:** 52.320 → 76.840 (#208 "This") · 00:52.320–01:16.840 · **Dim:** 2D, 2.5D in vignette 5
**Engines:** TaylorStage (sin, 1/(1+x²)), Typst, fraction bar, Digit Lock, `space.Camera` tilt; whip-pans (horizontal zoom blur) between vignettes
**Purpose:** Preview the film as five fast vignettes (about 5 s each, each a pattern interrupt) and plant open loops 2–4.
**VO:** "In this video, we will watch a polynomial slowly wrap itself around a sine wave … for a reason hiding in a place you cannot even see on the graph."

1. **Wrap (52.3–57.3).** On "wrap itself around a sine wave" (#145–150, 55.06–56.65) the gold copy climbs along an ink sine wave from 0 outward
   (degree 1 → 15, about 0.3 s per step), and the camera tracks right with the growing tip.
2. **Factorials (57.3–62.6).** Whip-pan. The formula row `1 + x + x²/□ + x³/□ + x⁴/□ + ⋯` has empty denominators. On "factorial(s)" (#158, 59.20)
   magenta `2!`, `3!`, `4!` drop in from above. On "uninvited" (#161, 60.56) each pops into its slot (0.15 s stagger) with a small × spark.
3. **e by hand (62.6–67.6).** Whip-pan. A number line from 0 to 3. On "number E" (#170–171, 64.10–64.48) a lime `e` tick appears at 2.718. On "fractions" (#177, 66.74) gold segments
   1, 1, ½, ⅙, 1/24 stack along the line toward it, and a readout climbs with the digit lock (`2.7083…`, "2.7" locked).
4. **The trick fails (67.6–72.9).** Whip-pan. The ink hill 1/(1+x²), gold copy hugging. On "innocent looking curve" (#186–188, 70.33–70.72) everything is calm.
   On "fails" (#193, 72.62) the copy whips off-frame vertically at x = ±1, still **gold**. Red is held back for Chapter 7.
5. **Off the graph (72.9–76.8).** On "hiding" (#197, 73.69) the camera tilts below the graph plane. A faint complex-plane grid lies beneath it, and on
   "cannot even see" (#202–204, 74.71–75.40) two dim glows pulse at ±i through the floor, then the camera tilts back. *(Paid off in S41.)*

**SFX:** a whoosh per whip; tick pops on the factorials; digit pops; a low thud under the whip-off at 72.62. **Stills:** 55.8, 60.9, 66.5, 72.7, 75.2

---

### S06 — Title Card
**Time:** 76.840 → 80.840 (#218 "Start") · 01:16.840–01:20.840 · **Dim:** 2D
**Engines:** Aion TitleCard on `slate` (serif title, framed live clip), push transition
**Purpose:** Name the topic without stopping the narration.
**VO:** "This is the Taylor series. Let's build it from scratch."

- On "This" (#208, 76.84) the stage turns to `slate`. A FramedPanel (`radius-none`, 2 px `frame` border) holds a live clip: the gold copy wrapping sine,
  still climbing. On "Taylor series" (#211–212, 77.74–78.33) the title `Taylor series` sets above it in the `title-card` serif (112 px, ink), with a light sweep.
- On "from scratch" (#216–217, 79.96–80.32) the camera **pushes into the frame** until it fills 1920 × 1080, and the clip collapses to its origin: a single blue dot.
  That dot becomes the `x` chip of S07.

**SFX:** a soft chime on the title; a whoosh on the push. **Stills:** 78.6, 80.4

---

## CHAPTER 1 — WHY POLYNOMIALS
Eyebrow `01 · WHY POLYNOMIALS` at 81.04.

### S07 — What a Computer Finds Easy
**Time:** 80.840 → 100.000 (#273 "Polynomials") · 01:20.840–01:40.000 · **Dim:** 2D
**Engines:** Typst (chips → formula), TaylorStage (parabola), ParameterSlider
**Purpose:** A polynomial is just multiplying and adding.
**VO:** "Start with what a computer finds easy. Take a number X, multiply it by itself, multiply by a constant, add a few of those together. 3X squared minus 2X plus 5. That is a polynomial. Every piece of it is just multiplying and adding. Give a computer any X and it can evaluate this instantly."

- **07A · Building (80.8–88.9).** On "number X" (#227–228, 83.42–83.93) a blue `x` chip. On "multiply it by itself" (#229–232, 84.18–85.65) a second `x` meets it with a magenta × spark
  and they fuse into `x²`. On "constant" (#236, 86.49) a `3 ×` slides in, giving `3x²`. On "add a few of those together" (#237–242, 87.16–88.42) `−2x` and `+5` slide in.
- **07B · The formula (88.9–96.4).** The chips set as `3x² − 2x + 5` (`math-display`, x blue), term by term on #243 (88.92), #245–246 (90.00–90.48) and #247–248 (90.86–91.29).
  On "polynomial" (#252, 92.44) a gold pill `polynomial`. On "multiplying" (#259, 94.83) the implied products glow magenta. On "adding" (#261, 95.74) the + and − glow orange and teal.
- **07C · Instantly (96.4–100.0).** On "any X" (#265–266, 97.44–97.59) the formula moves up and a blue slider plus a small ink parabola graph appear.
  On "instantly" (#272, 99.04) the slider sweeps x from −2 to 2 in 0.8 s, a blue dot rides the parabola, and the readout `p(x)` updates every frame (tabular).

**Stills:** 85.0, 91.6, 99.4

---

### S08 — Friendly Functions
**Time:** 100.000 → 109.400 (#302 "Sine,") · 01:40.000–01:49.400 · **Dim:** 2D
**Engines:** TaylorStage, Typst
**VO:** "Polynomials are friendly in other ways too. Their slopes are easy to find. The areas under them are easy to find. They never jump, never break, never surprise you."

- On "slopes" (#281, 102.69) an ink tangent glides along the parabola and `p′(x) = 6x − 2` sets beside it.
- On "areas under them" (#287–289, 104.18–104.78) the area from 0 to x fills translucent blue, and the readout shows `x³ − x² + 5x` (computed).
- On "never jump, never break, never surprise you" (#295–301, 106.33–108.97) the camera pulls very wide and the parabola runs smooth to both frame edges.
  A single light sweep runs its length on "surprise" (#300, 108.70).

**Stills:** 103.3, 105.0, 108.8

---

### S09 — Circles, Growth and Areas
**Time:** 109.400 → 121.680 (#338 "So") · 01:49.400–02:01.680 · **Dim:** 2D, three FramedPanels on stage
**Engines:** skia (three live panels), Chip
**Purpose:** The functions we care about are born from ideas a chip cannot type.
**VO:** "Sine, on the other hand, is defined by a circle. The exponential function is defined by growth. The logarithm by an area under a curve. Beautiful ideas. But you cannot type a circle into a chip."

1. On "Sine" (#302, 109.40) panel 1 opens. On "circle" (#311, 111.62) a point turns on a pink unit circle and its height traces an ink sine wave to the right (`role-trace`).
2. On "exponential" (#313, 112.43) panel 2: an ink eˣ with a riding tangent triangle. On "growth" (#318, 114.07) the readouts `height` and `slope` show the same number.
   *(This foreshadows S24.)*
3. On "logarithm" (#320, 115.11) panel 3: the curve 1/t, the area from 1 to x filling, and the readout `area = ln x`.

- On "Beautiful ideas" (#327–328, 117.56–118.38) one light sweep crosses all three panels.
- On "type a circle into a chip" (#332–337, 119.97–121.12) the Chip rises at the bottom center. The pink circle lifts out of panel 1, drops toward the
  input slot, bounces off with a back-ease and fades.

**Stills:** 111.9, 116.5, 120.6

---

### S10 — The Impostor Plan
**Time:** 121.680 → 132.880 (#371 "Let's") · 02:01.680–02:12.880 · **Dim:** 2D
**Engines:** TaylorStage (sin, P₃)
**VO:** "So here's the plan. If we cannot compute the real function, let's build a polynomial that pretends to be it. A perfect imposter. The only question is how to make the disguise convincing."

- On "real function" (#347–348, 124.49–124.74) the ink sin x draws, labeled `f(x)` in `math-inline`.
- On "build a polynomial" (#350–352, 125.55–125.88) a gold P₃ materializes slightly offset above. On "pretends to be it" (#354–357, 126.68–127.52) it glides down onto the ink
  curve. Near 0 the two lines become one.
- On "perfect imposter" (#359–360, 128.07–128.72) a gold pill `impostor`.
- On "disguise convincing" (#369–370, 131.47–132.45) the violet error band blooms where the copy peels away (|x| > 1). The question is shown, not written.

**Stills:** 124.9, 128.4, 132.3

---

## CHAPTER 2 — COPYING A CURVE
Eyebrow `02 · COPYING A CURVE` at 133.08. TaylorStage: x ∈ [−4, 4], y ∈ [−1.6, 1.6], the original is cos x.

### S11 — The Cosine Hill
**Time:** 132.880 → 142.440 (#405 "First") · 02:12.880–02:22.440 · **Dim:** 2D
**VO:** "Let's try it with the cosine curve right around the point X equals 0. Cosine starts at the top of a hill at a height of 1 and gently curves down on both sides."

- On "cosine curve" (#376–377, 133.80–134.12) the ink cos x draws from left to right. On "X equals 0" (#382–384, 135.40–136.12) the blue probe marker drops to x = 0 with a vertical
  hairline, and the camera eases in 1.3× on the origin.
- On "top of a hill" (#389–392, 137.87–138.26) a blue dot at (0, 1). On "height of 1" (#397, 139.41) the `1` tick on the y axis switches to ink.
- On "curves down on both sides" (#401–404, 140.86–141.71) two short ink arrows trace down both shoulders.

**Stills:** 134.6, 139.6, 141.6

---

### S12 — Attempt 1: A Constant
**Time:** 142.440 → 163.600 (#457 "What") · 02:22.440–02:43.600 · **Dim:** 2D
**Engines:** TaylorStage, Derivative Ladder (first use), loupe
**VO:** "First attempt. The simplest polynomial there is. A constant. Just match the height. Cosine of 0 is 1. So our imposter is the flat line. Y equals 1. Right at 0. It's perfect. But move a little to the side and the real curve falls away while our line stays stubbornly flat."

- **12A (142.4–150.2).** On "First attempt" (#405–406, 142.44–142.86) a gold pill `attempt 1`. The ladder card slides in at the right with five empty rows.
  On "match the height" (#415–417, 147.31–147.85) the feature pill `height` lights gold. On "Cosine of 0 is 1" (#418–422, 148.48–149.65) row `f(0)` fills with `1`.
- **12B (150.2–157.4).** On "flat line" (#428–429, 151.55–151.83) **the hug** draws P₀ = 1 outward from the origin. The formula chip `P(x) = 1` sits top left.
  On "Right at 0" (#433–435, 154.96–155.57) a loupe opens at (0, 1) showing the two curves touching. On "perfect" (#437, 156.48) the hug brackets snap at `±0.14`.
- **12C (157.4–163.6).** On "move a little to the side" (#439–444, 157.67–158.78) the probe slides to x = 1.5 and a violet error segment grows, with the readout
  `error 0.93` (1 − cos 1.5). On "falls away" (#449–450, 160.06–160.33) the violet band shades the whole gap. On "stubbornly flat" (#455–456, 162.26–163.02) the gold line pulses once, flat.

**Stills:** 149.8, 155.6, 160.8

---

### S13 — Attempt 2: Match the Slope
**Time:** 163.600 → 177.360 (#495 "What") · 02:43.600–02:57.360 · **Dim:** 2D
**VO:** "What did we miss? The slope. So let's match that too. At the top of the hill, cosine is perfectly level. Its slope is 0. Our flat line also has a slope of 0. So nothing changes yet."

- On "The slope" (#462, 165.37) the pill `slope` lights. On "top of the hill" (#470–473, 168.38–168.86) an ink tangent draws on cos x at 0, with a small rise/run triangle.
  On "perfectly level" (#476–477, 169.89–170.73) the triangle collapses flat. On "slope is 0" (#479–481, 171.45–172.20) row `f′(0)` fills with a muted `0`.
- On "Our flat line also has" (#482–486, 172.96–174.01) the gold line's tangent lands exactly on the ink one and both flash.
- On "nothing changes yet" (#492–494, 175.54–176.80) the formula chip becomes `P(x) = 1 + 0·x`, the `0·x` fades to a ghost, and the gold curve stays still.
  The stillness is the joke.

**Stills:** 169.0, 172.3, 176.4

---

### S14 — The Bend
**Time:** 177.360 → 186.400 (#519 "Now") · 02:57.360–03:06.400 · **Dim:** 2D
**Engines:** TaylorStage plus a **curvature comb** (hairline normals with length ∝ curvature, a CAD-style read of bend)
**VO:** "What is still missing is the bend. Cosine is curving downward. And to capture a bend, we need a parabola, an X squared term."

- On "the bend" (#501, 179.15) the pill `bend` lights. A muted curvature comb grows along the top of the cos hill, while the gold flat line shows none.
- On "curving downward" (#504–505, 180.37–180.90) the comb pulses.
- On "parabola, an X squared term" (#514–518, 183.82–185.50) a small gold ghost parabola with the Typst label `x²` (x blue) floats in at the upper right.

**Stills:** 180.6, 185.2

---

### S15 — How Much x²?
**Time:** 186.400 → 214.360 (#595 "Our") · 03:06.400–03:34.360 · **Dim:** 2D
**Engines:** skia (stacked mini-plots), Typst derivation in a FramedPanel, **exponent drop** (first use), ladder
**Purpose:** The quiet "aha" that sets up factorials: x² has a bend of 2, so we need half of it.
**VO:** "Now here is a subtle point. The bend of a curve is measured by its second derivative, the slope of the slope … To get a bend of exactly minus 1, we need minus 1/2 of X squared."

- **15A · Slope of the slope (186.4–197.0).** A slow push-in. On "second derivative" (#534–535, 190.37–191.14) `f″(x)` sets. On "the slope of the slope" (#537–540, 191.87–192.77)
  three framed mini-plots stack vertically, joined by `frame`-colored arrows: cos x → −sin x → −cos x (computed). On "that bend is minus 1" (#545–548, 195.26–196.37)
  the bottom plot's value at 0 lights teal (−1) and ladder row `f″(0)` fills with teal `−1`.
- **15B · x² has bend 2 (197.0–209.0).** A derivation flows top to bottom inside a FramedPanel. On "Take X squared" (#557–559, 199.57–199.94) `x²`. On "find its slope, 2X" (#561–564,
  200.88–202.18) the **exponent drop**: the 2 falls to the front, giving `2x`. On "Take the slope again, 2" (#565–569, 202.88–204.94) the drop runs again, giving `2`.
  On "bend of 2, not 1" (#575–579, 207.03–208.41) the `2` glows magenta.
- **15C · Half of it (209.0–214.4).** On "exactly minus 1" (#585–587, 210.12–210.96) a teal target chip `−1`. On "minus 1/2 of X squared" (#590–594, 211.97–213.37) `−½ x²` builds,
  followed by the check line `−½ · 2 = −1` with a right-angle tick mark.

**SFX:** a drop and land tick per exponent drop. **Stills:** 192.5, 202.4, 208.0, 213.6

---

### S16 — The Parabola Hugs
**Time:** 214.360 → 225.560 (#624 "Keep") · 03:34.360–03:45.560 · **Dim:** 2D
**VO:** "Our new imposter is 1 minus X squared over 2. Look at it on the graph. Near 0, it bends down exactly like the cosine, a much better disguise."

- On "1 minus X squared over 2" (#599–604, 216.02–218.10) the formula chip morphs to `P(x) = 1 − x²/2` and **the hug** runs P₀ → P₂.
- On "Look at it on the graph" (#605–610, 218.76–219.67) the camera eases back. On "Near 0, it bends down exactly" (#611–616, 220.28–221.80) the two curvature combs overlay and coincide at 0.
- On "much better disguise" (#621–623, 223.69–224.32) the hug brackets spring from `±0.14` to `±0.70`, with a light sweep along the zone.

**Stills:** 218.4, 221.6, 224.8

---

### S17 — The Fourth Derivative
**Time:** 225.560 → 251.520 (#691 "2,") · 03:45.560–04:11.520 · **Dim:** 2D
**Engines:** ladder, Typst derivation, exponent drop ×4, the hug
**VO:** "Keep going. The third derivative of cosine at 0 is 0, so we skip it. The fourth derivative is plus 1 … 1 minus X squared over 2 plus X to the fourth over 24."

- **17A (225.6–236.3).** On "third derivative" (#627–628, 226.91–227.20) ladder row `f‴(0)` fills with `0`. On "skip it" (#637–638, 229.76–230.37) the row strikes through to a ghost.
  On "fourth derivative is plus 1" (#640–644, 231.07–232.71) row `f⁗(0)` fills with orange `+1`. On "X to the fourth term" (#651–655, 234.73–235.86) a `x⁴` chip.
- **17B · The cascade (236.3–245.5).** On "differentiated 4 times" (#661–663, 237.46–238.98) the derivation runs `x⁴ → 4x³ → 12x² → 24x → 24` with four exponent drops.
  The dropped digits light on their spoken numbers: "4" (#665, 240.21), "3" (#667, 241.04), "2" (#669, 242.13), "1" (#671, 242.70). On "24" (#672, 243.22) the result glows magenta.
  On "divide by 24" (#675–677, 244.62–245.46) the term becomes `x⁴/24`.
- **17C (245.5–251.5).** The formula builds on its words, #678–690 (246.44–250.52): `1 − x²/2 + x⁴/24`, then **the hug** runs P₂ → P₄ and the brackets spring to `±1.40`.

**Stills:** 232.9, 241.2, 243.4, 250.9

---

## CHAPTER 3 — WHY FACTORIALS
Eyebrow `03 · WHY FACTORIALS` at 251.72.

### S18 — Two, Twenty-Four
**Time:** 251.520 → 267.720 (#724 "And") · 04:11.520–04:27.720 · **Dim:** 2D
**Engines:** Typst (`math-display`), number tiles
**VO:** "2, 24. Notice the pattern. 2 is 2 times 1. 24 is 4 times 3 times 2 times 1. These are factorials. 4 factorial means 4 multiplied by every whole number below it."

- **18A (251.5–255.3).** The denominators lift out of the S17 formula and enlarge in magenta: `2` on #691 (251.52) and `24` on #692 (252.44). The 1.8 s pause holds a slow breathing glow.
  On "Notice the pattern" (#693–695, 254.22–254.70) they separate into a staircase layout.
- **18B (255.3–262.0).** `2 = 2 × 1` builds on the hand-timed #696–700 override ("Two" 255.46, "one" 256.90). Then `24 = 4 × 3 × 2 × 1` builds factor by factor: "4" (#703, 258.42),
  "3" (#705, 259.25), "2" (#707, 260.25), "1" (#709, 260.91).
- **18C (262.0–267.7).** On "factorials" (#712, 262.23) each product collapses into `2!` and `4!`, and the `!` pops with a magenta glint.
  On "4 multiplied by every whole number below it" (#716–722, 264.71–266.80) a descending staircase of tiles 4, 3, 2, 1 joined by × lights left to right, ending on `4! = 24`.
  A muted row `1! 2! 3! 4! 5!` = `1 2 6 24 120` sits beneath.

**Stills:** 253.4, 260.95, 266.5

---

### S19 — The Exponent Drops
**Time:** 267.720 → 285.920 (#778 "Now,") · 04:27.720–04:45.920 · **Dim:** 2D
**Engines:** Typst, exponent drop (the chapter's hero motion), Derivative Ladder
**Purpose:** Pay off open loop 2: factorials come from differentiating powers.
**VO:** "And they show up for a simple reason. Every time you take the derivative of a power, the exponent drops down in front and multiplies … each term delivers exactly the amount we asked for."

- **19A (267.7–275.4).** A large `x⁵` sits center. On "derivative of a power" (#737–740, 271.00–271.73) `d/dx` slides in. On "the exponent drops down in front" (#742–746, 272.55–273.87)
  the `5` falls slowly this time (0.8 s), landing in front as `5x⁴`. On "multiplies" (#748, 274.93) a magenta × spark.
- **19B (275.4–279.8).** On "Take enough derivatives" (#749–751, 275.44–275.95) the drops run fast: `5x⁴ → 20x³ → 60x² → 120x → 120`. Each dropped digit also flies into a row
  at the bottom: `5 × 4 × 3 × 2 × 1`. On "multiplied all of those exponents together" (#755–760, 277.00–278.96) the row collapses into `5! = 120`.
- **19C (279.8–285.9).** On "Dividing by the factorial" (#761–764, 279.76–280.57) the same cascade runs on `x⁵/5!`. On "cancels that out" (#765–767, 281.13–281.93) the result
  `120 / 120` wipes to `1` (both 120s strike out). On "delivers exactly the amount we asked for" (#771–777, 282.98–285.08) the cos stage returns in miniature:
  the `x⁴/24` term lights the ladder row `f⁗(0) = 1` and nothing else.

**Stills:** 273.6, 278.8, 281.9, 284.6

---

## CHAPTER 4 — THE RECIPE
Eyebrow `04 · THE RECIPE` at 286.12.

### S20 — One Recipe
**Time:** 285.920 → 312.290 (#850 "Each") · 04:45.920–05:12.290 · **Dim:** 2D
**Engines:** ladder (generic), Typst term-by-term build with glyph flights from the ladder
**VO:** "Now, we can write the whole trick as a single recipe. To copy a function near 0, find its value, its first derivative … and on and on forever."

- **20A (285.9–298.2).** On "single recipe" (#787–788, 287.87–288.58) a glass recipe card slides in at the left. The generic ladder fills on its words:
  `f(0)` on "value" (#797, 291.89), `f′(0)` on "first derivative" (#800, 292.98), `f″(0)` on "second derivative" (#803, 294.16), `f‴(0)` on "third" (#805, 295.23), and `⋮` on "and so on" (#808, 296.17).
  On "measured at 0" (#810–812, 296.72–297.38) every `0` in the ladder glows blue.
- **20B (298.2–312.3).** The Taylor formula builds in `math-display`, and each ladder value **flies into its slot**: `f(0)` on "the value" (#818, 299.48);
  `+ f′(0) x` on #819–824 (299.88–302.08); `+ f″(0)/2! x²` on #825–834 (302.76–305.50); `+ f‴(0)/3! x³` on #835–844 (306.48–309.25); `+ ⋯` on "and on and on forever" (#845–849, 310.04–311.12),
  with a light sweep on "forever". The compact sum `sum_(n=0)^oo f^((n))(0)/(n!) x^n` fades in beneath at `opacity-nonfocal`.

**Stills:** 295.6, 305.8, 311.6

---

### S21 — Each Term Has One Job
**Time:** 312.290 → 338.000 (#921 "That") · 05:12.290–05:38.000 · **Dim:** 2D → 2.5D
**Engines:** mini-plots, loupe (×40 on the origin), Term Stack
**VO:** "Each term has one job. The X term handles the slope … You can stack term after term, and each one only brings new information."

- **21A · Jobs (312.3–322.6).** Each term glows in the formula with a small plot and a pill beside it: the `x` term on "slope" (#856–860, 314.55–315.80) with the line y = x; the `x²` term
  on "bend" (#862–867, 316.79–318.58) with a parabola and its comb; the `x³` term on "how the bend is changing" (#869–877, 319.47–321.86) with a cubic whose comb flips sign through 0.
- **21B · Invisible at 0 (322.6–332.1).** On "the clever part" (#882–883, 323.47–323.93) the camera zooms on the origin (a pattern interrupt). On "completely invisible to all the lower derivatives"
  (#890–896, 326.19–328.46) a ×40 loupe shows `x⁴/4!` lying perfectly flat at 0. Its own ladder reads `0 0 0 0 1` (computed), and the four zeros dim.
  On "never spoils the features you have already matched" (#901–907, 330.33–332.08) the cos stage adds `x⁴/24` to P₂: inside the loupe nothing moves and the pills `height` `slope` `bend` stay lit,
  while far from 0 the curve changes.
- **21C · Stack (332.1–338.0).** On "stack term after term" (#910–913, 333.51–334.58) the Term Stack returns from S04: cos terms `1`, `−x²/2`, `x⁴/24`, `−x⁶/720` drop as layers in depth.
  On "brings new information" (#918–920, 336.08–336.82) each new layer lights one new ladder row.

**Stills:** 315.4, 321.2, 327.8, 331.6, 336.4

---

### S22 — Taylor Series, Taylor Polynomial
**Time:** 338.000 → 349.680 (#957 "Zero") · 05:38.000–05:49.680 · **Dim:** 2D
**VO:** "That infinite sum is called the Taylor series. When we stop after a few terms, we call it a Taylor polynomial. And with every term you add, the copy hugs the original a little further out."

- On "Taylor series" (#927–928, 339.87–340.65) a `heading` label `Taylor series` sets over the Σ formula, with a light sweep.
- On "stop after a few terms" (#931–935, 341.39–342.23) a vertical gold cut line slices the formula after the x³ term, and everything to its right fades to a ghost.
  On "Taylor polynomial" (#940–941, 343.65–343.79) the label `Taylor polynomial` and `P₃`.
- On "with every term you add … further out" (#944–956, 345.38–349.20) the cos stage runs **the hug** five times: P₂ → P₄ → P₆ → P₈ → P₁₀ (0.7 s each), and the bracket readouts climb
  `±0.70 → ±1.40 → ±2.13 → ±2.88 → ±3.62`.

**Stills:** 340.6, 343.9, 348.9

---

### S23 — Any Center
**Time:** 349.680 → 359.560 (#987 "Let's") · 05:49.680–05:59.560 · **Dim:** 2D
**Engines:** TaylorStage with a live center (`taylor.coeffs(f, 4, a)` recomputed every frame)
**VO:** "Zero isn't special, by the way. You can center the copy at any point you like, simply by measuring distances from that point instead. The idea stays exactly the same."

- On "Zero isn't special" (#957–959, 349.68–350.24) the blue center marker unpins from 0. On "center the copy at any point" (#965–970, 351.88–352.97) it slides to a = 2
  and the gold P₄ re-expands around it, hugging there.
- On "measuring distances" (#975–976, 354.38–355.00) a blue dimension bracket `x − a` spans from a to the probe, and the formula morphs `xⁿ → (x − a)ⁿ`.
- On "stays exactly the same" (#983–986, 357.70–358.94) the center a sweeps slowly from 2 to −1, and the copy follows continuously, its hug zone traveling with it.

**Stills:** 352.9, 355.4, 358.9

---

## CHAPTER 5 — e FROM FRACTIONS
Eyebrow `05 · e FROM FRACTIONS` at 359.76 (e set in the math face, lime).

### S24 — The Function That Is Its Own Slope
**Time:** 359.560 → 377.160 (#1033 "And") · 05:59.560–06:17.160 · **Dim:** 2D → 2.5D
**Engines:** TaylorStage (eˣ, x ∈ [−3, 3]), Digit Lock pair, depth stack
**VO:** "Let's put the recipe to work on the most famous function of all, e to the X. This function has one remarkable property. Its slope is always equal to its own height. So its derivative is itself. Its second derivative is itself. Every derivative is itself."

- **24A (359.6–367.3).** On "e to the X" (#1000–1003, 363.08–363.87) `eˣ` (e lime, x blue) sets and the ink eˣ draws.
- **24B (367.3–370.6).** On "slope is always equal to its own height" (#1011–1018, 367.59–369.98) a probe rides the curve with its tangent. Two readouts, `height` and `slope`, tick identically.
  They are computed separately (exp(x) and a central difference) so the equality is earned. A vertical height bar and the tangent's rise over a run of 1 are visibly the same length.
- **24C (370.6–377.2).** On "derivative is itself" (#1021–1023, 370.93–371.93) a copy of the curve labeled `f′` slides onto it exactly. `f″` follows on "second derivative" (#1025–1028).
  On "Every derivative is itself" (#1029–1032, 375.12–376.44) five ghost copies cascade in depth (2.5D) and collapse into one line in the front view.

**Stills:** 363.9, 369.4, 376.2

---

### S25 — All Ones
**Time:** 377.160 → 397.600 (#1089 "Now") · 06:17.160–06:37.600 · **Dim:** 2D
**Engines:** ladder, Typst glyph flights, the hug ×4
**VO:** "And at 0, e to the 0 is 1. So every single derivative at 0 is simply 1. Feed that into the recipe … plus X to the 4th, over 4 factorial, and so on."

- **25A (377.2–383.8).** On "at 0" (#1034–1035, 377.44–377.67) the probe snaps to 0. On "e to the 0 is 1" (#1036–1041, 378.23–379.33) a dot at (0, 1). On "every single derivative at 0 is simply 1"
  (#1043–1050, 380.21–383.20) the ladder fills with `1 1 1 1 1 ⋯` in one quick cascade (0.1 s stagger).
- **25B (383.8–397.6).** On "Feed that into the recipe" (#1051–1055, 383.76–384.84) the S20 formula returns. The ladder's 1s fly into the `f⁽ⁿ⁾(0)` slots and the slots dissolve ("clean").
  The series builds on its words: `1` (#1063, 387.84), `+ x` (#1064–1065, 388.15–388.56), `+ x²/2!` (#1066–1071, 388.66–390.62), `+ x³/3!` (#1072–1077, 391.60–392.95), `+ x⁴/4!` (#1078–1085, 394.24–395.59), `+ ⋯` (#1086–1088).
  On the graph, **the hug** runs P₁ → P₂ → P₃ → P₄ in sync with the terms (brackets `±0.14 → ±0.38 → ±0.68 → ±1.00`).

**Stills:** 382.6, 390.9, 396.4

---

### S26 — Out Comes e
**Time:** 397.600 → 424.650 (#1130 "After") · 06:37.600–07:04.650 · **Dim:** 2D
**Engines:** number line, fraction bar, loupe chain (×10, ×100), Digit Lock
**Purpose:** Pay off open loop 3. This is the most satisfying beat of the film: a number assembling itself from fractions.
**VO:** "Now set X equal to 1, and out comes the number e itself. 1, plus 1, that's 2, plus 1/2, 2.5, plus 1/6, 2.667, plus 1 over 24, 2.708, plus 1 over 120, 2.7167. The true value of e is 2.71828."

- **26A (397.6–401.9).** On "set X equal to 1" (#1090–1094, 397.79–398.60) every `x` in the series **morphs into a blue `1`**. On "the number e itself" (#1099–1101, 400.18–400.72) a number line runs 0 → 3, and a lime ghost tick
  `e` sits at 2.71828.
- **26B · The fraction bar (401.9–419.6).** Each spoken term adds a gold segment along the line, with its fraction above it and a running digit-lock readout (lime when correct):
  `1` on #1102 (401.88) · `+1 → 2` on #1103–1106 (402.61–404.81) · `+½ → 2.5` on #1107–1109 (405.62–407.19) · `+⅙ → 2.667` on #1110–1112 (408.72–409.75) ·
  `+1/24 → 2.708` on #1113–1117 (411.76–413.82, "2.7" locks) · `+1/120 → 2.7167` on #1118–1122 (415.82–417.84, hand-timed, "2.71" locks).
  Once segments become too thin to see (from 1/24 on), a **loupe** opens on the bar's tip at ×10, then ×100, so every segment stays visible.
- **26C · True value (419.6–424.7).** In the 0.7 s pause after "2.7167" the loupe holds and the lime ghost tick breathes. On "The true value of e is" (the #1123–1128 override, 420.28) the target readout
  `e = 2.71828…` sets in lime under the running sum. On "2.71828" (#1129, 421.56) a violet sliver labeled `0.0016` shows the remaining gap in the loupe, then a light sweep.

**SFX:** one glass tick per segment, rising in pitch; a pop per locked digit; a chime on the true value. **Stills:** 400.6, 404.9, 409.9, 418.4, 422.3

---

### S27 — Factorials Win
**Time:** 424.650 → 444.240 (#1177 "Now") · 07:04.650–07:24.240 · **Dim:** 2D
**Engines:** Digit Lock, loupe chain, bar race on a log axis, motion blur (final, 27B)
**VO:** "After just six terms, we are already very close. After 10 terms, the first seven decimal places are correct. Why so fast? Because factorials grow ridiculously quickly. 10 factorial is already more than 3.5 million. The terms shrink so fast that the sum settles down almost immediately."

- **27A (424.7–431.8).** On "six terms" (#1132–1133, 425.26–425.49) the counter shows `n = 5` / `6 terms`. On "After 10 terms" (#1139–1141, 427.96–428.64) the counter ticks up to `n = 10`
  (through x¹⁰/10!; see §5). Segments keep landing and the loupe deepens through ×10³ … ×10⁷ (an infinite-zoom feel; tick labels re-scale each step).
  On "seven decimal places are correct" (#1143–1148, 429.25–430.97) the readout `2.7182818` sits over `2.7182818…` and the seven decimals lock one by one.
- **27B · The race (431.8–439.9).** On "Why so fast?" (#1149–1151, 431.84–432.37) cut to a bar race on a log axis: `2ⁿ` in muted ink and `n!` in magenta, for n = 1 … 10.
  On "grow ridiculously quickly" (#1154–1156, 434.27–435.77) the magenta bars rocket. On "10 factorial" (#1157–1158, 436.12–436.56) the camera tilts up following the last bar.
  On "3.5 million" (#1163–1164, 438.43–439.10) the readout counts up to `10! = 3,628,800`.
- **27C (439.9–444.2).** On "terms shrink" (#1166–1167, 440.15–440.47) the bars flip into `1/n!`, shrinking to hairlines. On "settles down almost immediately" (#1173–1176, 441.94–443.15) the running sum's curve
  (lime) lands flat on the e line by n = 5, with a light sweep.

**Stills:** 425.8, 430.8, 435.5, 439.0, 443.4

---

## CHAPTER 6 — WRAPPING THE SINE WAVE
Eyebrow `06 · WRAPPING THE SINE` at 444.44.

### S28 — Back to the Calculator
**Time:** 444.240 → 453.360 (#1203 "The") · 07:24.240–07:33.360 · **Dim:** 2D
**Engines:** Chip (callback), Typst
**VO:** "Now let's return to the question from the very beginning. How does your calculator find the sine of 0.5? Apply the recipe to sine at 0."

- On "question from the very beginning" (#1182–1186, 445.32–446.88) the Chip slides back in, its display frosted over the hidden `0.4794` exactly as in S01.
- On "sine of 0.5" (#1193–1195, 449.29–449.78) `sin(0.5)` lifts out of the display and becomes the Typst title of the chapter stage.
- On "Apply the recipe to sine at 0" (#1196–1202, 450.72–452.70) the Chip slides away and the ink sin x draws on TaylorStage (x ∈ [−7, 7]).

**Stills:** 446.6, 449.9, 452.9

---

### S29 — The Derivative Loop
**Time:** 453.360 → 471.200 (#1249 "Sine") · 07:33.360–07:51.200 · **Dim:** 2D
**Engines:** derivative wheel (pink ring, four nodes with mini-curves), ladder
**VO:** "The derivatives of sine go around in a loop. Sine, then cosine, then minus sine, then minus cosine, and back to sine again. At 0, these give 0, 1, 0, minus 1, over, and over. So all the even powers vanish, and the signs take turns."

- **29A (453.4–461.5).** On "loop" (#1211, 455.32) a pink ring draws, with four nodes at 12, 3, 6 and 9 o'clock. A pink pointer moves node to node on its words:
  `sin x` (#1212, 455.84) → `cos x` (#1214, 456.69) → `−sin x` (#1216–1217, 457.71–458.14) → `−cos x` (#1219–1220, 459.04–459.57) → back to `sin x` (#1222–1225, 460.23–460.89), closing the circle with a sweep.
- **29B (461.5–467.0).** On "At 0" (#1226–1227) each node shows its value at 0: `0` muted (#1230, 463.16), `1` orange (#1231, 463.62), `0` (#1232, 464.18), `−1` teal (#1233–1234, 464.64–465.25).
  On "over, and over" (#1235–1237, 465.65–466.59) the wheel spins twice and the ladder fills down `0 1 0 −1 0 1 0 −1`.
- **29C (467.0–471.2).** On "even powers vanish" (#1241–1243, 467.69–468.57) the zero rows dim and their x^even slots slide out. On "the signs take turns" (#1246–1248, 469.68–470.40) the remaining signs flash
  orange and teal in alternation.

**Stills:** 458.2, 465.3, 470.6

---

### S30 — The Sine Series
**Time:** 471.200 → 484.000 (#1282 "The") · 07:51.200–08:04.000 · **Dim:** 2D
**VO:** "Sine of X equals X minus X cubed over 6, plus X to the 5th over 120, minus X to the 7th over 5040, and on forever. Let's watch it on the graph."

- The series builds in `math-display` on its words: `sin x =` (#1249–1252, 471.20–471.99) · `x` (#1253, 472.68) · `− x³/6` (#1254–1258, 472.79–474.51) · `+ x⁵/120` (#1259–1265, 474.92–476.63) ·
  `− x⁷/5040` (#1266–1272, 477.66–479.36) · `+ ⋯` (#1273–1275, 480.76–481.27). Denominators are magenta. Under each one, a muted `3!`, `5!` or `7!` fades in, and the signs are orange and teal.
- On "Let's watch it on the graph" (#1276–1281, 482.36–483.41) the formula shrinks into a top strip and the camera dollies back to a wide stage (x ∈ [−8, 8]).

**Stills:** 476.8, 481.0, 483.8

---

### S31 — The Vine Climbs (hero scene)
**Time:** 484.000 → 506.160 (#1350 "Now") · 08:04.000–08:26.160 · **Dim:** 2D
**Engines:** TaylorStage, the hug ×9, `noise.wobble` vine tip, motion blur (final, 31C)
**Purpose:** The image the whole film promised. The gold copy climbs the wave term by term.
**VO:** "The first term, just X, is a straight line through the center … like a vine climbing a fence."

- **31A (484.0–491.4).** On "just X" (#1285–1286, 485.08–485.31) the strip term `x` glows and the gold P₁ draws through the origin. On "hugs the sine wave for a short stretch" (#1295–1302, 487.89–489.47)
  the brackets snap to `±0.39`. On "shoots away" (#1304–1305, 490.43–490.87) the line exits at the top right and the violet band widens.
- **31B (491.4–499.2).** On "Add the cubic term" (#1306–1309, 491.40–492.07) **the hug** runs P₁ → P₃ (brackets `±1.04`). On "following the first hump" (#1316–1319, 494.17–495.22) the camera drifts to the
  hump at +π/2, where P₃ reads 0.925 against 1. On "Add the 5th power" (#1320–1323, 495.72–496.31) the hug runs P₃ → P₅ (`±1.76`). On "catching the valley" (#1328–1330, 498.37–498.65) the camera drifts to the
  **valley at −π/2**, where P₅ reads −1.0045 against −1 (see §5).
- **31C · The climb (499.2–506.2).** On "With every new term" (#1331–1334, 499.16–499.95) the degree climbs 7 → 9 → 11 → 13 → 15 → 17, about 0.6 s per hug. The brackets jump outward on both sides
  (`±2.50 … ±6.25`), the camera pulls out to x ∈ [−12, 12], and a `degree 17` readout ticks. On "like a vine climbing a fence" (#1345–1349, 504.00–505.35) the two leading tips of the copy,
  where it leaves the wave, get a hand-drawn `noise.wobble` (fps=12) and a small glint. One long light sweep runs along the gold.

**Design notes:** evaluate with Horner on 1,600 samples and clip at |y| > 2.2 before stroking, so high-degree tails never produce huge paths.
**SFX:** one resolve per hug, rising a semitone each step. **Stills:** 488.6, 493.9, 498.6, 502.4, 505.4

---

### S32 — The Calculation
**Time:** 506.160 → 536.120 (#1393 "Three") · 08:26.160–08:56.120 · **Dim:** 2D, SplitStage (graph left, calculation card right)
**Engines:** TaylorStage loupe (×100, ×10,000), glass calculation card, Digit Lock
**Purpose:** Pay off open loop 1 with real arithmetic.
**VO:** "Now the calculation. X is 0.5. The first term is 0.5. The second term is 0.125 divided by 6, about 0.0208. Subtract it, and we get 0.4792. The third term adds a tiny 0.00026. The total is 0.479427. The true answer is 0.479425."

- **32A (506.2–512.2).** On "calculation" (#1352, 506.67) the dashed split divider draws and the card slides in at the right. On "X is 0.5" (#1353–1355, 507.76–508.15) the blue probe glides to 0.5.
  On "first term is 0.5" (#1357–1360, 510.03–510.98) row 1 sets, `x = 0.5`, and a gold marker sits on P₁ at (0.5, 0.5).
- **32B (512.2–522.2).** On "0.125 divided by 6" (#1365–1368, 513.35–515.37) row 2 sets, `x³/6 = 0.125 / 6`. On "about 0.0208" (#1369–1370, 515.84–516.40) `≈ 0.0208` follows. On "Subtract it … 0.4792" (#1371–1376,
  518.60–520.31) the running total `0.4792` appears, with "0.479" locking lime against sin 0.5, and the graph marker drops from P₁ to P₃.
- **32C (522.2–536.1).** On "third term adds a tiny" (#1378–1383, 522.52–524.37) row 3 sets, `+ x⁵/120 ≈ 0.00026` (**not** the SRT's 0.0026). The loupe opens at ×100 on the tiny step.
  On "The total is 0.479427" (#1385–1387, 527.10–528.09) the total sets and "0.47942" locks. In the 3.9 s pause the loupe deepens to ×10,000: gold and ink almost touch,
  separated by a violet sliver labeled `1.5 × 10⁻⁶`. On "The true answer is 0.479425" (#1388–1392, 531.96–533.42) the ink readout `sin 0.5 = 0.4794255…` slides under the total and the digits compare
  column by column. Five decimals light lime in pairs.

**Stills:** 508.4, 516.2, 520.6, 529.9, 534.5

---

### S33 — The Secret Revealed
**Time:** 536.120 → 556.160 (#1454 "And") · 08:56.120–09:16.160 · **Dim:** 2D
**Engines:** Chip (callback, op flicker), `taylor.ops` tally
**VO:** "Three terms, a few multiplications and additions, and we are correct to five decimal places. That is the secret your calculator was keeping … It only knows the polynomial that pretends to be one."

- **33A (536.1–542.1).** On "Three terms" (#1393–1394, 536.12–536.48) the three card rows pulse. On "multiplications and additions" (#1397–1399, 537.26–538.78) the four pads return small, with tallies computed from the
  Horner program: `× 4` and `+ 2`. On "five decimal places" (#1405–1407, 540.48–541.20) the five lime digits glow.
- **33B (542.1–550.5).** On "the secret your calculator was keeping" (#1411–1415, 542.58–544.06) the card **slides into the Chip** and the display unfrosts: `0.4794`, the same digits as S02, with a light sweep.
  Loop 1 is closed. On "clever refinements" (#1419–1420, 545.57–545.98) two `caption` labels flicker inside the die: `range reduction` and `tuned coefficients` (honest, muted). On "at the heart of it"
  (#1430–1434, 549.35–550.25) the gold polynomial glows at the die's core while the pads replay the same 6-op flicker from S02.
- **33C (550.5–556.2).** On "does not know what a circle is" (#1435–1443, 550.52–552.49) a pink circle ghost hovers outside the chip and fades. On "only knows the polynomial that pretends to be one"
  (#1446–1453, 553.34–555.72) the gold sine copy is left glowing alone.

**Stills:** 538.4, 544.2, 549.8, 555.2

---

### S34 — Small Angles: The Pendulum
**Time:** 556.160 → 568.280 (#1495 "So") · 09:16.160–09:28.280 · **Dim:** 2D
**Engines:** TaylorStage zoom, `components/pendulum.py` (SciPy)
**VO:** "And look at that very first term. For small angles, the sine of X is almost exactly X. Physicists use this all the time. It is how the swing of a pendulum becomes a simple equation you can solve by hand."

- **34A (556.2–562.0).** On "very first term" (#1458–1460, 557.00–557.59) the strip term `x` glows. On "small angles" (#1462–1463, 558.28–558.61) the stage zooms to x ∈ [−0.4, 0.4], where gold y = x and ink sin x
  are one line. On "almost exactly X" (#1469–1471, 560.73–561.59) `sin x ≈ x` sets.
- **34B (562.0–568.3).** On "Physicists" (#1472, 562.04) a split shows two pendulums (ink rods, blue bobs, pink trails), both released from 10°. On the left, the exact θ″ = −(g/L) sin θ (solve_ivp);
  on the right, the small-angle closed form. On "swing of a pendulum" (#1482–1485, 564.56–565.04) they swing in visible lockstep. On "solve by hand" (#1492–1494, 567.04–567.69)
  `θ(t) = θ₀ cos(√(g/L) t)` sets under the right one (t blue).

**Stills:** 559.0, 564.8, 567.9

---

## CHAPTER 7 — WHERE THE TRICK BREAKS
Eyebrow `07 · WHERE IT BREAKS` at 568.48. **`alert` red is allowed from S39 on.**

### S35 — So Far, So Good
**Time:** 568.280 → 582.200 (#1540 "Look") · 09:28.280–09:42.200 · **Dim:** 2D, three stacked FramedPanel lanes
**VO:** "So far, the series has worked everywhere we looked. For E to the X, for sine and for cosine, you can travel as far from 0 as you like. Add enough terms, and the copy always catches up. But not every function is so kind."

- On "E to the X, for sine and for cosine" (#1505–1513, 571.49–573.85) three lanes stack in: eˣ, sin and cos, each with its gold copy.
- On "travel as far from 0 as you like" (#1516–1523, 574.62–576.21) a blue probe in each lane runs out to x = 8. On "the copy always catches up" (#1529–1532, 578.18–579.50) each lane's degree climbs until its hug zone
  passes the probe. The hugs are slightly staggered across lanes.
- On "not every function is so kind" (#1534–1539, 580.19–581.63) all three lanes drop to `opacity-ghost` and slide away. The stage goes quiet and black for 0.4 s.

**Stills:** 573.9, 578.9, 581.6

---

### S36 — The Innocent Hill
**Time:** 582.200 → 603.320 (#1602 "Try") · 09:42.200–10:03.320 · **Dim:** 2D
**VO:** "Look at this curve. One divided by one plus X squared. It is a gentle hill … One minus X squared plus X to the fourth minus X to the sixth and so on."

- **36A (582.2–596.0).** On "One divided by one plus X squared" (#1544–1550, 583.32–585.03) `f(x) = 1/(1 + x²)` sets and the ink hill draws (x ∈ [−3, 3]). On "highest at zero" (#1556–1558, 587.24–588.02) a dot at the peak.
  On "sliding smoothly down" (#1559–1564, 588.62–590.29) a probe glides down both sides.
  On "No breaks, no corners, no sudden jumps" (#1565–1571, 591.00–593.65) a loupe visits three points (one per phrase) and shows a smooth curvature comb each time, while the muted pills `no breaks`, `no corners` and `no jumps` light in turn.
  On "As innocent as a curve can be" (#1573–1578, 594.19–595.63) one soft light sweep.
- **36B (596.0–603.3).** On "Its Taylor series" (#1579–1581, 596.04–596.62) the series builds: `1` (#1585, 598.05) · `− x²` (#1586–1588) · `+ x⁴` (#1589–1593) · `− x⁶` (#1594–1598) · `+ ⋯` (#1599–1601), with alternating orange and teal signs.
  The gold copy hugs P₂ → P₆ in sync.

**Stills:** 584.9, 592.5, 602.3

---

### S37 — Inside: It Settles
**Time:** 603.320 → 610.160 (#1617 "Now") · 10:03.320–10:10.160 · **Dim:** 2D
**Engines:** partial-sum zigzag (a damped staircase against a target line), Digit Lock
**VO:** "Try X equals 0.5. The terms shrink and the sum settles on 0.8. Exactly right."

- On "X equals 0.5" (#1603–1605, 603.60–604.26) the probe goes to 0.5 and the ink value f(0.5) = 0.8 becomes a horizontal target line in a side panel.
- On "terms shrink" (#1607–1608, 605.71–606.06) a zigzag draws the running sums 1 → 0.75 → 0.8125 → 0.7969 → 0.8008 → … with gold step bars that shrink (orange up, teal down).
- On "settles on 0.8" (#1612–1614, 607.22–608.09) the readout locks `0.8000` in lime. On "Exactly right" (#1615–1616, 608.92–609.49) a glint where the zigzag meets the line.

**Stills:** 606.2, 609.4

---

### S38 — At the Edge: It Flips
**Time:** 610.160 → 621.000 (#1640 "And") · 10:10.160–10:21.000 · **Dim:** 2D
**VO:** "Now try X equals one. One minus one plus one minus one. The sum never settles. It just flips back and forth forever."

- On "X equals one" (#1619–1621, 610.90–611.75) the probe goes to 1.0 and the target line drops to 0.5.
- The zigzag steps on the spoken terms: up on "One" (#1622, 612.52), down on "minus one" (#1623–1624, 612.97–613.72), up on "plus one" (#1625–1626, 614.16–615.17), down on "minus one" (#1627–1628, 615.22–615.97).
  It stays pinned between 1 and 0.
- On "never settles" (#1631–1632, 617.43–617.80) the readout flickers `1 → 0 → 1 → 0` and the digit lock fails (no lime). On "back and forth forever" (#1635–1639, 619.06–620.25) the zigzag keeps going faster as a ghost trail.
  The target 0.5 sits in the middle, never reached.

**Stills:** 614.3, 618.0, 620.4

---

### S39 — Beyond: It Explodes
**Time:** 621.000 → 631.960 (#1668 "Why?") · 10:21.000–10:31.960 · **Dim:** 2D
**Engines:** TaylorStage, partial sums P₂ … P₂₀, **first `alert` red**
**VO:** "And beyond one, it gets even worse. The terms grow larger and larger. And the polynomial flies off toward infinity, while the real curve sits there, perfectly calm."

- On "beyond one" (#1641–1642, 621.27–621.72) the probe goes to 1.2. On "grow larger and larger" (#1649–1652, 624.23–625.26) the zigzag swings outgrow the panel and exit top and bottom.
- On "flies off toward infinity" (#1656–1659, 626.89–628.41) back on the hill, the copy steps through P₂, P₄ … P₂₀ (0.15 s each). Inside |x| < 1 it hugs tighter and tighter, at x = ±1 it pinches,
  and outside it whips vertically off-frame, alternating up and down. **Outside |x| > 1 the copy turns `alert` red.**
- On "perfectly calm" (#1666–1667, 631.17–631.32) the camera holds completely still. The ink hill rests, and the hug brackets are stuck at exactly ±1 as two red hairline walls.

**SFX:** a low boom building under 626.9–628.4, then silence on "calm". **Stills:** 624.8, 628.2, 631.4

---

### S40 — Off the Graph
**Time:** 631.960 → 640.960 (#1691 "Suppose") · 10:31.960–10:40.960 · **Dim:** 2D → 2.5D tilt
**Engines:** loupe, `space.Camera` (`orbit_path`), complex plane (`plane-major`, `plane-minor`)
**VO:** "Why? The graph shows nothing strange at X equals one. Nothing at all. The reason lives off the graph in the complex numbers."

- On "Why?" (#1668, 631.96) the red walls pulse once. On "nothing strange at X equals one" (#1672–1677, 633.79–635.25) a loupe at x = 1 on the ink hill shows a perfectly smooth curve with a normal comb.
  On "Nothing at all" (#1678–1680, 635.68–636.51) the loupe closes.
- On "lives off the graph" (#1683–1686, 637.80–638.67) **the camera tilts**: the graph plane rotates back (pitch 0° → 62°), and the x axis becomes the real axis of a horizontal plane. On "complex numbers" (#1689–1690, 639.74–640.11)
  the complex-plane grid extends from the real axis toward the horizon, with an imaginary axis and a violet `i` tick. The ink hill now stands as a vertical slice along the real axis.

**Stills:** 634.6, 638.4, 640.6

---

### S41 — The Hidden Explosion (the surprise beat)
**Time:** 640.960 → 658.840 (#1737 "Here") · 10:40.960–10:58.840 · **Dim:** 3D
**Engines:** **PyVista** `pole_surface(height_scale)` with a domain-colored texture (`mesh3d.render`, cached) + skia overlays through the same `space.Camera`; Typst morph; `chroma_kick` and `noise.shake` (the only time in the film)
**Purpose:** Pay off open loop 4. The reason the series fails is two towers you cannot see from the real line.
**VO:** "Suppose X is allowed to be imaginary. At X equals I, the square root of minus one, X squared becomes minus one. And the bottom of the fraction becomes zero. The function explodes. And that hidden explosion sits at a distance of exactly one from zero."

- **41A (641.0–651.8).** On "allowed to be imaginary" (#1694–1697, 641.86–642.85) the blue probe leaves the real axis and walks up the imaginary axis, leaving a violet path. On "X equals I" (#1699–1701, 644.23–645.04) it stops on `i`.
  On "square root of minus one" (#1703–1707, 645.60–646.90) the readout `i² = −1`. On "X squared becomes minus one" (#1708–1712, 647.16–648.87) the denominator morphs step by step, `1 + x²` → `1 + (−1)`.
  On "the bottom of the fraction becomes zero" (#1715–1720, 649.56–651.26) it becomes `0`.
- **41B · Explodes (651.8–655.5).** On "The function explodes" (#1722–1723, 652.07–652.89) the **surface rises** (height_scale 0 → 1 over 0.9 s, back-ease). Hue follows arg f(z) and the brightness bands follow log|f|.
  Two towers shoot up at ±i and continue off-frame (clipped high, as the system asks for poles). The chroma kick and camera shake fire at `beat(1723)`. The ink hill along the real axis shows as
  the low ridge between the towers.
- **41C (655.5–658.8).** On "a distance of exactly one from zero" (#1731–1736, 655.96–658.08) a blue dimension line runs 0 → i with the readout `|i| = 1`, and a matching line runs to −i.

**Performance:** about 540 PyVista frames. Render them once per output size (cache key = camera, height_scale, size). **SFX:** a deep impact plus a sub-drop on 652.74; a soft tick on the |i| = 1 readout.
**Stills:** 645.2, 650.9, 653.4, 657.6

---

### S42 — The Circle of Trust
**Time:** 658.840 → 679.360 (#1799 "This") · 10:58.840–11:19.360 · **Dim:** 3D → top-down 2D → 2.5D tilt back
**Engines:** PyVista (towers sinking while the camera orbits to top-down), then a **numpy domain-coloring plane** (`plane.domain_image`), a disk mask, and the `space.Camera` tilt back to the S39 graph
**VO:** "Here is the rule. A Taylor series works inside a circle around its center. That circle grows only until it touches the nearest trouble spot, even a trouble spot hiding in the complex plane. For this curve, the circle has a radius of one. On the ordinary number line, that means the series can only be trusted between minus one and one."

- **42A (658.8–663.9).** On "Here is the rule" (#1737–1740, 658.84–659.66) the camera orbits to straight top-down and the towers sink to height 0.15. At exactly top-down the view crossfades (0.3 s)
  to the 2D numpy domain image, with the poles as red glow dots at ±i. On "inside a circle around its center" (#1745–1750, 661.58–663.25) a pink circle appears at 0 with radius 0.
- **42B (663.9–670.4).** On "grows" (#1753, 664.54) the radius grows. **Inside the disk the plane shows the domain coloring of P₂₀(z); outside it still shows f(z).** As the disk grows, the coloring
  inside matches f exactly. On "touches the nearest trouble spot" (#1757–1761, 665.53–666.88) the circle hits ±i with a hard spring stop and the poles flash. For a moment, an extra 0.15 of radius shows
  P₂₀'s coloring scrambling into tight bands beyond the poles, then it springs back. On "hiding in the complex plane" (#1766–1770, 668.68–669.88) the poles pulse once more.
- **42C (670.4–679.4).** On "radius of one" (#1778–1780, 672.40–673.10) the readout `R = 1` in pink. On "the ordinary number line" (#1783–1785, 673.88–674.70) the camera tilts back down to the side view of S39.
  The circle meets the real axis at −1 and 1, and these drop as two pink ticks onto the red walls, coinciding exactly. On "between minus one and one" (#1794–1798, 677.12–678.78) the interval [−1, 1] lights pink and the gold
  copy is visible only inside it.

**Stills:** 662.4, 666.2, 670.0, 675.4, 678.9

---

### S43 — Radius of Convergence
**Time:** 679.360 → 693.000 (#1839 "Once") · 11:19.360–11:33.000 · **Dim:** 2D + a 3D peek (cached PyVista frames)
**VO:** "This distance is called the radius of convergence. It is a reminder that our polynomial imposter only knows what the function looks like near a single point. How far that knowledge reaches depends on secrets the graph does not show."

- On "radius of convergence" (#1804–1806, 681.01–682.02) a `heading` label `radius of convergence` and `R = 1` in pink, with a light sweep.
- On "only knows … near a single point" (#1816–1825, 685.36–687.82) a soft pink disk of "knowledge" glows around 0 on the graph, and everything outside it dims to `opacity-nonfocal`.
- On "How far that knowledge reaches" (#1826–1830, 688.48–689.63) the disk breathes. On "secrets the graph does not show" (#1833–1838, 691.13–692.40) the graph tilts back 25° just far enough to show the two tower tips glowing
  below the plane (cached PyVista), then returns flat. Cut.

**Stills:** 681.8, 686.4, 691.9

---

## CHAPTER 8 — WHY IT MATTERS
Eyebrow `08 · WHY IT MATTERS` at 693.20.

### S44 — Everywhere
**Time:** 693.000 → 712.560 (#1897 "And") · 11:33.000–11:52.560 · **Dim:** 2D panels, then 3D
**Engines:** three FramedPanels; **PyVista** loss surface + Hessian bowl (cached); numpy Newton steps
**VO:** "Once you know this trick, you start seeing it everywhere. Engineers keep the first few terms to turn hard equations into easy ones. Game engines use short polynomials to compute waves and rotations quickly. Optimization methods in machine learning replace a complicated surface with a simple bowl, which is just a Taylor series stopped at the squared term."

1. **Engineers (696.2–700.3).** On "Engineers" (#1849, 696.16) panel 1: ink `√(1 + x)` with the gold two-term copy `1 + x/2` hugging near 0. On "hard equations into easy ones" (#1857–1861, 698.40–699.79)
   the formula morphs `sqrt(1 + x) → 1 + x/2` and a pill `linearize` appears.
2. **Game engines (700.3–704.6).** On "Game engines" (#1862–1863, 700.32–700.59) panel 2: a unit arrow rotating on a pink ring. Its (cos, sin) come from a degree-7 polynomial, and a readout shows the computed max
   error against `numpy.sin`. On "waves and rotations" (#1869–1871, 702.84–703.36) the arrow tip traces a wave.
3. **Machine learning (704.6–712.6).** On "Optimization" (#1873, 704.56) panel 3 expands to full frame: a bumpy PyVista loss surface (a smooth sum of Gaussians, ink wireframe over a translucent fill) with a blue
   parameter point. On "simple bowl" (#1884–1885, 708.50–709.14) the gold quadratic bowl (second-order Taylor, Hessian by finite differences) snaps on at the point. On "stopped at the squared term" (#1892–1896, 710.68–712.11)
   the point slides to the bowl's bottom (one Newton step) and a new bowl forms there (a second step). The camera orbits slowly.

**Stills:** 698.9, 702.6, 709.4, 711.8

---

### S45 — Einstein's Series
**Time:** 712.560 → 735.000 (#1968 "The") · 11:52.560–12:15.000 · **Dim:** 2D
**Engines:** Typst build and morph (SymPy expansion), energy-vs-speed plot
**VO:** "And one of the most famous examples comes from Einstein. In relativity, the energy of a moving object is its mass times c squared divided by the square root of 1 minus v squared over c squared … the first two terms are m c squared plus 1/2 m v squared."

- **45A (712.6–724.6).** No portrait: the formula is the star. On "energy of a moving object" (#1910–1914, 716.97–718.41) `E =` sets. On "mass times c squared" (#1917–1920, 718.90–719.83) `m c²`.
  On "divided by the square root of 1 minus v squared over c squared" (#1921–1933, 720.52–723.73) it grows into `m c² / sqrt(1 − v²/c²)` (v blue).
- **45B (724.6–727.4).** On "nothing like the physics we learn in school" (#1936–1943, 725.05–726.76) a muted ghost `½ m v²` sits far to the right, unconnected.
- **45C (727.4–735.0).** On "expand it as a Taylor series in the speed" (#1945–1953, 727.71–729.65) the square root unrolls (morph) into `m c² (1 + ½ v²/c² + ⅜ v⁴/c⁴ + ⋯)`. On "the first two terms are m c squared plus 1/2 m v squared"
  (#1956–1967, 730.55–733.95) it multiplies out to `E ≈ m c² + ½ m v² + ⋯`. The second term glows gold, and the ghost from 45B flies in and lands on it exactly.

**Stills:** 718.9, 723.9, 729.4, 734.4

---

### S46 — Newton Was Never Wrong
**Time:** 735.000 → 748.080 (#2004 "So") · 12:15.000–12:28.080 · **Dim:** 2D
**VO:** "The first term is the energy locked inside mass itself. The second is the familiar kinetic energy from school physics. Newton's formula was never wrong. It was simply the first useful term of a deeper series."

- On "energy locked inside mass itself" (#1973–1977, 736.08–737.74) `m c²` gets a `light` glint and the pill `rest energy`. On "kinetic energy" (#1983–1984, 740.02–740.49) `½ m v²` gets a gold pill `kinetic energy`.
- On "Newton's formula was never wrong" (#1988–1992, 742.41–743.87) a plot of kinetic energy against v/c ∈ [0, 0.99]: the exact relativistic curve (ink, rising to infinity at c) and Newton's parabola (gold).
  They hug at low speed, with the readout `0.76 % apart at 0.1 c`, and separate near c.
- On "first useful term of a deeper series" (#1997–2003, 745.37–747.22) the rest of the series `+ ⅜ m v⁴/c² + ⋯` fades in muted to the right of the gold term, followed by a light sweep.

**Stills:** 737.4, 743.4, 747.2

---

## CHAPTER 9 — RECAP AND OUTRO
Eyebrow `09 · RECAP` at 748.28.

### S47 — What We Built, Part 1
**Time:** 748.080 → 774.280 (#2070 "With") · 12:28.080–12:54.280 · **Dim:** 2.5D card arc
**Engines:** five glass recap cards on an arc with live miniatures (Chip, TaylorStage, exponent drop), camera truck, depth of field
**VO:** "So let's look back at what we built. Computers can only add and multiply … because the factorial cancels what repeated differentiation multiplies in."

The active card is at 100 %. The others sit at `opacity-nonfocal` with `blurred(6)`, and the camera trucks along the arc.
1. **The chip** (#2012–2025, 750.16–755.34): the four pads light, then `3x² − 2x + 5`.
2. **Match, one term at a time** (#2026–2051, 756.04–765.22): the cos stage hugs on its words, P₀ on "value" (#2036, 759.39), tangent on "slope" (#2039, 760.47), P₂ on "bend" (#2042, 761.78), P₄ → P₆ on "each higher derivative"
   (#2044–2046, 762.48–763.28); the ladder fills alongside.
3. **Factorials** (#2052–2069, 766.04–773.84): the `x⁴` exponent drop cascade, then `/4!` cancels on "cancels" (#2064, 770.59).

**Stills:** 753.0, 761.9, 770.9

---

### S48 — What We Built, Part 2
**Time:** 774.280 → 792.760 (#2122 "Here") · 12:54.280–13:12.760 · **Dim:** 2.5D card arc
**VO:** "With this one recipe, the number E becomes a sum of simple fractions. And sine becomes a handful of multiplications your calculator can do in a blink. And every series has a reach. It works inside a circle that stops at the nearest trouble spot, even one hidden in the complex numbers."

4. **e and sine** (#2074–2096, 775.94–783.34): the fraction bar locks `2.718` in lime on "simple fractions" (#2081–2082, 778.01–778.16). On "sine becomes a handful of multiplications" (#2084–2089, 779.31–780.65) the vine wrap runs,
   and on "in a blink" (#2094–2096, 783.13–783.34) the Chip display flashes `0.4794`.
5. **The reach** (#2097–2121, 784.00–791.97): top-down complex plane. On "circle that stops at the nearest trouble spot" (#2107–2114, 787.28–789.37) the pink disk grows to the red poles and springs.

**Stills:** 778.2, 783.4, 789.5

---

### S49 — Next Time: e Meets i
**Time:** 792.760 → 811.680 (#2172 "Any") · 13:12.760–13:31.680 · **Dim:** 2D
**Engines:** Typst glyph sorting (powers of i from SymPy), complex plane with a rotating point and its shadows
**Purpose:** An open loop out of the video, pointing to the end-screen video on e.
**VO:** "Here is something to think about until next time. What happens if you put an imaginary number into the series for e to the x? Sort the terms carefully and the series for cosine and sine fall out side by side. Growth, waves, and circles, all part of one family."

- **49A (792.8–800.9).** The eˣ series row returns. On "imaginary" (#2137, 796.93) every `x` morphs to `ix` (i violet). On "series for e to the x" (#2141–2146, 798.77–800.43) the powers evaluate: `1, ix, −x²/2!, −ix³/3!, x⁴/4!, …`.
- **49B (800.9–806.8).** On "Sort the terms carefully" (#2147–2150, 800.92–801.80) the terms **sort by glyph flight**: real terms drop to a lower row and i-terms rise to an upper row. On "cosine and sine fall out side by side"
  (#2155–2162, 803.58–805.95) the rows bracket as `cos x` and `i sin x`, and `e^(ix) = cos x + i sin x` sets faintly. It is a teaser, not a derivation.
- **49C (806.8–811.7).** On "Growth, waves, and circles" (#2163–2166, 806.76–808.67) one picture: a point e^(ix) runs around a pink unit circle on the complex plane, while its real and imaginary shadows trace an ink cosine and sine
  along two edges. On "one family" (#2170–2171, 810.49–810.64) a light sweep.

**Stills:** 797.8, 804.9, 809.6

---

### S50 — One Term at a Time
**Time:** 811.680 → 817.008 (end of narration) · 13:31.680–13:37.008 · **Dim:** 2.5D
**Engines:** Term Stack (S04 callback)
**VO:** "Any function built from the simplest pieces, one term at a time."

- On "Any function" (#2172–2173, 811.68–811.95) the S04 depth stack returns, this time with sine's pieces `x`, `−x³/6`, `x⁵/120`, `−x⁷/5040`. On "simplest pieces" (#2177–2178, 813.62–814.34) the camera orbits to the front and they
  slide together. On "one term at a time" (#2179–2183, 815.51–816.64) the last term clicks in, the copy hugs the ink wave, and a light sweep runs over the title `Taylor series` (serif, small) above.

**Stills:** 812.4, 816.7

---

### S51 — End Screen
**Time:** 817.008 → 837.008 (20 s of silence appended) · **Dim:** 2D

- Black stage. In the background, at 15 % opacity, a seamless loop of the gold copy climbing the sine wave (degree 1 → 17, then a soft reset under a sweep).
- Two FramedPanel slots for the YouTube end-screen editor. Left: *Why e Is Everywhere* (the channel's top video, and the direct follow-on to S49). Right: *The Math Trick That Turns Calculus Into Algebra | Laplace Transform*
  (best subscriber conversion). A subscribe circle sits at the bottom center. No text beyond the small title lockup.

**Stills:** 820.0, 835.0

---

## 4. Audio plan

| Layer | Library call | Notes |
| --- | --- | --- |
| Narration | `add_audio("audio.mp3", role="voice", start=0)` | ElevenLabs output is already clean. Run `faceless_champ.voice.process_voice` as an **A/B** in Stage L; keep it only if it sounds better (de-esser, gentle compression) |
| SFX | `add_sfx(path, at=beat(N), align="peak")` from each scene module's named beat constants; `sfx/build_mix.py` writes `sfx/cue_sheet.csv` | library: `convolution-explained-visually/sfx/raw/` plus `assets/sfx/equation-render/` (`tick`, `resolve`, `transition`) |
| Music (optional) | `add_audio(bed, role="music", duck=-12)` | a very low ambient pad, about −30 dB under the voice. Skip it if no license-clean bed is available |
| Master | `ExportSettings(loudness=-14, true_peak=-1)`, then `delivery_report(path)` | YouTube loudness; BT.709 tags are automatic |

**SFX vocabulary (one sound per meaning, never decoration):** pad tick (pitched per op) · **resolve** on every hug (rising a semitone across a sequence) · drop + land tick on every exponent drop ·
rising **pop** per locked digit · whoosh on whips, pushes and tilts · glass **chime** on law-level light sweeps (title, e, sin 0.5, R = 1) · one deep impact + sub-drop, used only in S41B.
Target levels: SFX peaks −20 to −16 dB under the voice. Never place a hit on a stressed syllable; land it in the gap after the word.

---

## 5. Math verification (computed before writing; reproduce these in `tests/test_taylor.py`)

| Item | Value | Used in |
| --- | --- | --- |
| Hug zones, cos (|f − Pₙ| < 0.01) | P₀ ±0.14 · P₂ ±0.70 · P₄ ±1.40 · P₆ ±2.13 · P₈ ±2.88 · P₁₀ ±3.62 | S12, S16, S17, S22 |
| Hug zones, sin | P₁ ±0.39 · P₃ ±1.04 · P₅ ±1.76 · P₇ ±2.50 · P₉ ±3.25 · P₁₁ ±4.00 · P₁₃ ±4.75 · P₁₅ ±5.50 · P₁₇ ±6.25 | S31 |
| Hug zones, eˣ (positive side) | P₁ 0.14 · P₂ 0.38 · P₃ 0.68 · P₄ 1.00 · P₆ 1.69 · P₈ 2.41 | S25 |
| 1 − cos 1.5 | 0.929 | S12C |
| e partial sums | 1 · 2 · 2.5 · 2.6667 · 2.7083 · **2.7167** (6 terms, gap 0.0016) · 2.71806 · 2.71825 · 2.71828 | S26 |
| "After 10 terms, seven decimals" | 10 terms (through 1/9!) = 2.7182815 → only **six** decimals. **11 terms (through 1/10!) = 2.7182818 → seven.** Show the counter as `n = 10` (the highest power, x¹⁰/10!), which makes the screen exactly true | S27A |
| 10! | 3,628,800 | S27B |
| sin 0.5 by series | 0.5 · 0.125/6 = 0.0208333 · 0.4791667 · **0.5⁵/120 = 0.00026042** · total 0.47942708 · true 0.47942554 · gap 1.5 × 10⁻⁶ · five decimals correct | S32 |
| Horner program for x − x³/6 + x⁵/120 | x·(1 + x²·(−1/6 + x²/120)): **4 ×, 2 +**, op order × × + × + × | S02B, S33A |
| "catching the valley" | P₃(π/2) = 0.925 (hump at +π/2) · P₅(−π/2) = −1.0045 (valley at −π/2). P₅ does not reach the 3π/2 valley, so frame the valley on the **left** | S31B |
| 1/(1+x²) at x = 0.5 | 1 · 0.75 · 0.8125 · 0.796875 · 0.80078 · 0.79980 → 0.8 | S37 |
| at x = 1 | 1 · 0 · 1 · 0 … | S38 |
| poles of 1/(1+z²) | z = ±i, |±i| = 1, so R = 1 | S41, S42 |
| Relativistic KE ÷ ½mv² at v = 0.1c | 1.0076 → `0.76 %` | S46 |
| √(1−β²)⁻¹ expansion | 1 + ½β² + ⅜β⁴ + ⋯ (SymPy) | S45C |

Simulated or illustrative pieces (the loss surface and the game-engine arrow's sample angles) are seeded and labeled as illustrations only by context. They never carry a typed claim.

---

## 6. Build stages (one session each, in order)

Each stage ends with `--frame` stills at the scenes' listed **Stills** times, then `--audit`, then a 720p `--preview` of that stage's range. Full-quality renders are never run in these sessions.

| Stage | Contents | Done when |
| --- | --- | --- |
| **A · Foundation** | copy `render.py` (add `--scene SNN` and `--pv-cache SIZE`) and `kaggle/` from the bell-curve project; `theme.py` (Aion mapping §1.2, `set_default_palette`); `cues.py` (`CueClock`, `AUDIO_DURATION = 817.008`, `END_SCREEN = 20`, `OVERRIDES` for #696–700 and #1123–1128 measured with silencedetect); `components/` taylor, stage, ladder, chip, stack25d, digits, plane, pendulum; `pv3d/` smoke frames (one pole-surface frame, one loss-surface frame); `tests/test_taylor.py` reproducing §5; serif title decision (§1.3: Cormorant Garamond) | component sheet stills + tests pass |
| **B · Cold open I** | S01–S03 (Chip, x-ray, op flicker, digit lock) | the first 3 s pass the retention check: moving on frame 0, nothing still > 4 s |
| **C · Cold open II** | S04–S06 (Term Stack, five vignettes, TitleCard push) | full 0:00–1:21 preview reviewed |
| **D · Ch1** | S07–S10 | |
| **E · Ch2** | S11–S17 (the hug, ladder, exponent drop locked in here) | the hug is identical in every use |
| **F · Ch3 + Ch4** | S18–S23 | the #696–700 override checked by ear |
| **G · Ch5** | S24–S27 (fraction bar, loupe chain, bar race) | the #1123–1128 override checked by ear |
| **H · Ch6** | S28–S34 (vine climb, calculation, pendulum) | |
| **I · Ch7, 2D** | S35–S40 | |
| **J · Ch7, 3D** | S41–S43 (PyVista cache at 720p; `--pv-cache 1080` and `2160` are commands **you** run) | the surprise beat lands on 652.74 |
| **K · Ch8 + Ch9** | S44–S51 (loss surface cache, card arc, e^(ix) sort, end screen) | |
| **L · Audio and polish** | `sfx/build_mix.py` (cue sheet from beat constants), the voice-chain A/B, optional music bed, full 720p preview, audio-sync spot checks at 12 random cues, `--audit` with zero contrast or clutter warnings | |
| **M · Final** | **not run by Claude.** You run `python render.py --chapter full --final` (1080p, `workers=2`, chunked and resumable) and the 4K Kaggle bundle (with the PyVista caches), then `python -m faceless_champ check final/…mp4` | delivery report OK |

### Folder layout

```
taylor-series-any-function-into-a-polynomial/
  audio.mp3  cue-per-word.srt  normal-subtitle.srt  voiceover.md  scene-plan.md
  theme.py  cues.py  render.py
  components/  taylor.py  stage.py  ladder.py  chip.py  stack25d.py  digits.py  plane.py  pendulum.py
  pv3d/        surfaces.py (pole surface, loss surface, Hessian bowl)
  scenes/      ch0_open.py  ch1_polynomials.py  ch2_copy.py  ch3_factorials.py  ch4_recipe.py
               ch5_e.py  ch6_sine.py  ch7_breaks.py  ch8_matters.py  ch9_recap.py  full.py
  tests/       test_taylor.py
  output/      frames/  previews/  cache/{pyvista,typst,domain}/  chunks/
  sfx/  kaggle/  final/
```

Each chapter module follows the house pattern: `START = cue(a)` and `END = cue(b)` (Chapter 0 starts at 0.0; Chapter 9 ends at 837.008); a `B` dict of named beats
(`B["explodes"] = beat(1723)`), which `sfx/build_mix.py` also imports; one `draw_sNN(fr, t)` per scene; one `draw_scene` source; and `SCENES = {"S41": (t0, t1, stills)}` for `--scene`.
`full.py` checks that the chapters are contiguous and lays one continuous narration `Layer` over them.

### Quality bar (every stage)

- **Ink original, gold copy.** The true function is always `ink`, the polynomial is always `gold`, and the gap is always violet. Red appears only in Chapter 7. Token colors never change meaning.
- Every number on screen comes from `components/taylor.py`, SymPy, SciPy or mpmath, matching §5. Nothing is typed.
- One focal point per frame; everything else at 0.4 opacity or less; at most five hues per frame.
- Line weights at 1080p: 1 px grids, 2–2.5 px geometry and the original, 4 px the gold copy (`stroke-curve`). Glow only on the focal element.
- No text below the `tick` role on plots or the `label` role elsewhere, no paragraphs, no on-screen questions. `--audit` passes clean.
- Dominant visual changes every 8–12 s; no shot holds unchanged for more than about 6 s (pauses excepted, where a zoom carries motion).
- **Performance** (2 CPU cores, 3.7 GB RAM, integrated GPU): target ≤ 0.8 s per 720p frame. Static layers are cached per size; Typst paths are cached; domain images are cached per (fn, view, size);
  PyVista frames are cached on disk; motion blur is finals-only and only on S01, S05, S27B and S31C. A full 720p preview (25,110 frames) takes about 3 h on 2 workers. Preview chapters, not the whole film, until Stage L.
