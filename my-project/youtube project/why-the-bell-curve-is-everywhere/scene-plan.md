# Why the Bell Curve Is Everywhere — Scene Plan

**Project folder:** `my-project/youtube project/why-the-bell-curve-is-everywhere/`
**Audio:** `audio.mp3`, 441.576 s (07:21.576). Narration ends at 441.3 s, followed by a 20 s end-screen hold (total 461.576 s).
**Timing sources:** `cue-per-word.srt` (1,289 word cues, used for anchors) and `normal-subtitle.srt` (162 phrase lines).
**Canvas:** 1920 × 1080, 30 fps, background pure black `#000000`. Previews are 720p; the final is 1080p locally and 4K on Kaggle.
**Library:** Faceless Champ core + kit (`faceless_champ`, `facelesschamp_kit`), with project modules copied from
`understanding-4d-visually/` (`fx.py`, `typmath.py`, `cues.py`, `render.py`, `space.py`, `components/hud.py`, `pv3d/`) and a new `theme.py`.

All timecodes are **source-clock** times in the narration (mm:ss.mmm). Scene boundaries are snapped to word cues, and
`#N` is the one-based cue index in `cue-per-word.srt`. Each visual beat lands 0.15 s before its cue (`cue(N) - 0.15`).

> **The SRT text has ASR errors. The audio is correct.** Anchor these cues by **index**, never with `word()` text matching:
> #28 "end" = *land* · #109 "pie" = *pi* · #218, #222 "than" = *then* · #549–550 "add it" = *added* · #695 "to" is an ASR insertion
> (spoken: *makes a mistake to the left count*) · #722 "have" = *halve* · #1006 "Height" = *Heights* · #1269 "wanna" = *want to*.
> These cues are digits in the SRT but spoken as words: #2, #52, #266, #272, #285, #291, #420, #808, #816, #830, #882, #902, #919, #921,
> #927, #939, #945, #1207, #1208, #1210. "E" (#1192, #1274, #1283) is the number *e*.
> Fix the subtitle text before uploading captions to YouTube.

### What the channel analytics change in this plan

- **Retention is the bottleneck** (viewers leave after 50–70 s, often with a drop around 0:20–0:40). So the video starts on the payoff
  visual at 0.0 s: the balls are already falling on the first word. There is no title card before 0:52. The title lockup is part of the motion, not a pause.
- **Open loops carry the viewer past the first minute.** The cold open plants three questions and pays each one off later on screen:
  *why the same curve* (paid off in S06/S11), *why pi* (paid off in S15, with the same pink π glyph flying back),
  and *where it breaks* (the red tail teased in S03D, paid off in S20).
- **Pattern interrupts every 8–12 s:** each beat changes the dominant visual (board → crowd → montage → formula → board).
  No shot holds unchanged for more than about 6 s.
- **The top video is "Why e Is Everywhere".** The e in the formula is green from the start, the narration points to it at the end,
  and the end screen links it.

---

## 1. Visual system (applies to every scene)

### 1.1 Look

- **Mood:** "light falling in the dark." Pure black, thin luminous geometry, and soft glowing particles. The balls and data points
  are the only things that move freely. Everything else is calm, slow and eased. Lots of negative space and at most one focal point
  per frame. Non-focal elements stay at 40 % opacity or less.
- **Depth vocabulary:** **2D** for histograms, curves and formulas (most of the film). **2.5D** (tilted glass cards, parallax panels,
  depth of field) for montages, comparisons and the recap. **True 3D** only where depth teaches something: the tumbling die (S08) and the
  Gaussian surface split into rings (S15B).
- **Floors and grids:** a very faint baseline grid (opacity 0.08 or less) under every histogram, so bars always stand on a shared floor.
  No textures and no gradient backgrounds. The black stays black.

### 1.2 Semantic color (never break this mapping)

Defined once in `theme.py` (new scheme `bell-noir`). Scene code uses token names only, never hex values.

| Token | Hex | Meaning everywhere in the video |
| --- | --- | --- |
| `ball` | `#5FB6FF` electric blue | **the data**: balls, darts, samples, people as dots, histogram bars, dice outcomes |
| `bell` | `#FFD17E` warm gold | **the law**: the bell curve, its outline and fills, and the mean line μ (the bell's center) |
| `sigma` | `#B58CFF` violet | spread: σ, ±σ brackets, the 68/95/99.7 bands, the width dial |
| `left` | `#36D6B0` teal | a left step on the board, a "minus" nudge, the horizontal error of a dart |
| `right` | `#FFA24C` orange | a right step on the board, a "plus" nudge, the vertical error of a dart |
| `e` | `#A6E35A` lime | the number e, `e^(…)` terms, growth/decay curves |
| `pi` | `#FF6FA8` pink | π, circles, the rings around the bullseye |
| `tail` | `#FF4D4D` red | multiplication, heavy tails, extremes, warnings, the "break" |
| `ink` | `#F5F7FA` | primary text, counts, results |
| `muted` | `#7C8597` | secondary labels, ticks, ghost elements |
| `grid` / `line` | `#1A2130` / `#2A3140` | floors, pegs at rest, plaque borders |
| `light` | `#FFE9C7` | light sweeps and glints |

- **Pegs** are `line` at rest and flash `ink` when a hero ball hits them.
- **Paths** on the board are drawn step by step: each left step is a `left` segment and each right step is a `right` segment.
  A path is therefore readable as a sequence of colors.
- **Every bell curve is gold**, whatever the data. Every data histogram is blue. This is the film's core contrast: **blue data,
  gold law**. Red appears only once the bell fails (S03D teaser, then Chapter 5).
- **The formula is colored by origin:** σ violet, μ gold, e lime, π pink, x ink. The same colors return in the recap.

### 1.3 Typography

- Display / title lockups: **Space Grotesk** (`display`), tracking +0.02.
- Labels, readouts and pills: **DM Sans** (`sans`). All numerals in counters use tabular figures so they don't jitter.
- Variables in labels (x, μ, σ): through **Typst** (`typmath.py`), since DM Sans has no Greek glyphs.
- Math: **Typst** (New Computer Modern Math) through `typmath.py` for every formula, count and morph. Live numbers use its cached digit
  strip (`typmath.number`) so they never recompile.
- Text budget: on-screen text is a label, never the transcript. Titles are 6 words or fewer, labels 4 words or fewer.
  Numbers, curves and formulas carry the teaching.

### 1.4 Motion language

- Entrances use emphasized easing (`fx.back` or ease-out, 0.45–0.7 s). Exits use accelerate, 0.3 s. Histogram bars grow with a slightly
  under-damped spring (one small overshoot), so the bells feel "poured", not drawn.
- **The pour is the hero motion of the film** (S01, S06, S23): balls hop from peg to peg on short parabolic arcs and settle into stacks
  with a tiny bounce. Every bell that forms from data forms by pouring or stacking. Bells never just fade in.
- **The bell snap:** when the gold curve fits a histogram, it traces left to right in 0.6 s, then settles with a soft glow pulse and a light
  sweep. It is the same motion every time, so the viewer learns it means "the law appears".
- **Histogram morphs** (dice, the lopsided die) interpolate exact distributions: x is re-standardized each step, so the shape changes but
  the frame doesn't jump.
- One idea per beat. Remove the old idea before the next arrives.

### 1.5 Premium finish (built in Skia)

| Effect | Implementation | Where |
| --- | --- | --- |
| Two-scale bloom and glow | `fx.Frame` quarter-res glow canvas plus an optional final `Layer(EffectStack(bloom=Bloom(radius=10, threshold=0.62)))` | gold curves, hero balls, key numbers only |
| Light sweep | `fx.light_sweep` (gradient band clipped to the shape) | every bell snap, title lockup, √π, end card |
| Chromatic-aberration kick | `fx.chroma_kick`, 0.15 s RGB split | "A bell." (S01), √π (S15), the break (S03D, S20A) |
| Motion blur | `fx.motion_blur`, 4–6 subframes, finals only | ball pours, die tumble, dart throws |
| Depth of field | per-layer Gaussian blur on 2.5D card stacks | S02 montage, S20C cards, S22 recap arc |
| Ball trails | fading polyline of the past positions of a hero ball (exact, evaluated at t − k·dt) | hero balls in S01, S04, S06 |
| Additive path light | 1,024 paths drawn with additive blending at low alpha, so brightness equals path count | S06A (the bell appears *as light*) |
| Glass plaques | dark translucent card, 1 px gradient border, inner glow; Skia `Lighting(bevel=6)` rim (from `components/hud.py`) | Pascal's triangle, formula plaques, rule cards, recap cards |
| Crack | a jagged polyline split of the curve path, two halves offset 6 px, red edge glow | the bell breaking (S03D, S20A, S22.6) |
| Cinematic finish | `fr.vignette(0.5)`, `fr.grain(t, 0.04)` | everywhere |

### 1.6 Recurring motifs (build once, reuse everywhere)

1. **Galton Board** (`components/galton.py`): the single source of truth for the board. It holds `rows`, peg layout, and a seeded
   `numpy` array of ball paths (`L/R` per row) and release times. `ball_pos(i, t)` is evaluated analytically: a parabolic hop
   between pegs and a stacking position in the bin by arrival order. This makes it deterministic per frame, with no physics engine
   (`pymunk` is not installed and isn't needed). It also provides path polylines (`left`/`right` colored), per-peg Pascal counts,
   per-bin counts, and `draw_all_paths(alpha)` for the additive 1,024-path light. Every count on screen is computed from it, never typed.
2. **Histogram** (`components/histogram.py`): blue bars on a shared floor, with spring growth, value labels, and `morph_to(pmf, u)` between
   exact distributions. Dice PMFs are computed exactly with `numpy.convolve`. (The sum of dice *is* a convolution, which is a quiet nod to
   the convolution video. Show a tiny muted `∗` between two die PMFs in S08C.)
3. **Bell** (`components/bell.py`): the gold curve from the real pdf, with live `mu`, `sigma` and `scale`. It also provides `fit(hist)` (moment-matched
   overlay), `snap(t0)` (trace + pulse + sweep), `band(k)` (σ-band fills), `crack(u)`, and `tail(u)` (a red heavy-tail extension).
4. **Dial pair** (`components/dials.py`): two glass knobs labeled μ (gold) and σ (violet), driving a live Bell. Used in S11, S16, S22.
5. **Dart Target** (`components/darts.py`): thin concentric rings, a bullseye, seeded 2D Gaussian darts, a horizontal (`left` teal)
   and vertical (`right` orange) error decomposition, marginal histograms on both axes, and pink iso-density rings.
6. **Crowd** (`components/crowd.py`): simple human silhouettes (one vector path, scaled per height) that can collapse into a dot
   histogram (one dot per person) and back. Used in S02, S12, S17, S19, S20.
7. **Eyebrow** (`hud.eyebrow`): a corner chapter marker (see §1.7).

### 1.7 Chapter markers

The narration is continuous, so there are no title cards that stop the audio. Each chapter opens with a top-left eyebrow
(`label` role, muted, 2.5 s): `01 · COUNTING PATHS`, `02 · ADDING DICE`, `03 · WHERE e AND π COME FROM`, `04 · THE RULER`,
`05 · WHERE IT BREAKS`, `06 · RECAP`. Chapter changes use an **in-frame transition** drawn inside the frame function
(zoom-blur push, a "pour" wipe of falling balls, or an iris), because `Sequence` transitions need an overlap that would break the single
narration clock.

---

## 2. Engine map

| Engine / feature | Faceless Champ entry point | Used for |
| --- | --- | --- |
| **skia-python** (main renderer) | one `FunctionSource(draw, size, duration, key)` per chapter, drawing into `fx.Frame` (crisp canvas plus glow canvas) | everything 2D and 2.5D: the board, histograms, curves, darts, crowd, plaques, HUD, transitions |
| **numpy / scipy** | inside the frame functions, all seeded | **real computation, never faked:** Galton paths and bin counts, exact dice PMFs by convolution, moment-matched bell fits, Gaussian darts, `scipy.special.erf` for band percentages, tail probabilities, multiplicative random walks for wealth, contour maps of f(x)·f(y) |
| **PyVista** (VTK 9.7, offscreen, optional) | `pv3d/render.py` (copied from 4D, cached RGBA, camera-matched to `space.Camera`) | the glass die tumble (S08B) and the gold Gaussian surface split into pink rings (S15B). Both have a skia fallback (isometric die; wireframe surface) if the cache is too slow |
| **Typst** (CLI, `~/.local/bin/typst`) | `typmath.py`: `draw`, `morph`, `number`, `tc(token, body)` | every formula and count: `2^10 = 1024`, `binom(10, 5) = 252`, `e^(-x^2)`, `∫ e^(-x^2) dx = sqrt(pi)`, the full normal pdf, `68.27%` etc. |
| **Manim** (optional) | `prepare_manim(...)` | fallback only; no scene needs it |
| **Narration** | `cues.py` (`AUDIO_DURATION = 441.576`, `cue(n)`), `SubtitleTrack.from_srt`; `scenes/full.py` chains the chapters with `check_contiguous` and one continuous audio `Layer` | source-clock sync |

**Not available:** LaTeX is not installed, so no Manim `MathTex`. Use Typst syntax everywhere (`e^(-x^2)`, `sqrt(2 pi)`, `binom(10, 5)`, `integral`, `sigma`, `mu`).
**Compositing order per frame:** PyVista solid (if any) → skia geometry → glow canvas → vignette and grain.
**Determinism:** every random element uses a fixed `numpy.random.default_rng(seed)` created once at module import. Frames must be
identical between preview and final, and between chunks on Kaggle.

---

## 3. Chapter map

| # | Chapter | Span | Scenes | Dimension |
| --- | --- | --- | --- | --- |
| 0 | Cold open: bell after bell | 00:00.000 – 00:56.720 (#168) | S01–S03 | 2D → 2.5D |
| 1 | Counting paths | 00:56.720 – 01:56.620 (#343) | S04–S07 | 2D |
| 2 | Adding dice: the central limit theorem | 01:56.620 – 03:10.500 (#560) | S08–S12 | 3D die → 2D |
| 3 | Where e and π come from | 03:10.500 – 04:55.220 (#883) | S13–S16 | 2D, 3D surface, Typst |
| 4 | The ruler: 68, 95, 99.7 | 04:55.220 – 05:36.780 (#986) | S17–S18 | 2D |
| 5 | Where the bell breaks | 05:36.780 – 06:27.180 (#1127) | S19–S21 | 2D → 2.5D |
| 6 | Recap and outro | 06:27.180 – 07:21.576 (+ end screen to 07:41.576) | S22–S24 | 2.5D → 2D |

**YouTube chapters (for the description in phase 5):** 00:00 Bell after bell · 00:56 Counting paths · 01:56 Adding dice: the
central limit theorem · 03:10 Where e and π come from · 04:55 The 68–95–99.7 ruler · 05:36 Where the bell breaks · 06:27 Recap.

---

## CHAPTER 0 — COLD OPEN: BELL AFTER BELL

### S01 — The Board
**Time:** 00:00.000 → 00:17.180 (#47 "Now", 17.2 s) · **Dimension:** 2D
**Engines:** skia (Galton Board, ball trails, bell snap), numpy (1,000 seeded paths, 12 rows), fx (motion blur, chroma kick, light sweep)
**Purpose:** The hook. Chaos turns into a perfect shape inside 16 seconds, before any explanation.

**VO:** "Drop a thousand small balls into a board full of pegs … the same smooth shape. A bell."

- **01A · Drop (00:00.0–00:05.7).** Frame 0 already shows the funnel and the first ball in the air (no black lead-in). On "Drop" (#1, 00:00.020)
  a 12-row board of pegs cascades in from the top, row by row in 0.6 s. On "thousand" (#2, 00:00.300) the funnel opens and a thin stream of blue balls
  begins. One **hero ball** carries a short trail. On "left" (#14, 00:04.670) it hops left and the peg flashes, with a tiny teal tick. On "right"
  (#16, 00:05.150) it hops right with an orange tick.
- **01B · Unpredictable (00:05.7–00:10.4).** On "random" (#19, 00:06.930) the camera eases in on the hero ball. On "cannot predict" (#21–22, 00:07.52–00:07.96)
  a faint **fan of ghost futures** opens below it (all the remaining paths from that peg, muted, additive). On "single ball" (#25–26, 00:09.07–00:09.51) the
  ghosts collapse and the ball drops into one bin with a soft click.
- **01C · The pile (00:10.4–00:17.2).** On "And yet" (#29–30, 00:10.38–00:10.68) the camera pulls back and time accelerates (a small muted `×20` chip):
  hundreds of balls pour. On "pile at the bottom grows" (#35–39, 00:12.64–00:13.54) the bins stack visibly. On "same smooth shape" (#42–44, 00:14.45–00:15.27)
  a gold curve begins tracing over the stack tops. On "A bell." (#45–46, 00:16.02–00:16.16) the **bell snap**: glow pulse, light sweep, chroma kick.

**Design notes:** The final pile must read as a clean bell. Choose a seed whose 1,000-ball histogram is within 3 % of the binomial at every bin.
**Out:** The board shrinks into a small glass panel at the left of frame (it becomes panel 1 of the montage).

---

### S02 — Bell After Bell
**Time:** 00:17.180 → 00:34.660 (#94 "So", 17.5 s) · **Dimension:** 2D → 2.5D panel grid
**Engines:** skia (Crowd, mini histograms, glass panels, depth of field), numpy (seeded samples per panel)
**Purpose:** Show the same law in unrelated places, fast.

**VO:** "Now measure the heights of ten thousand people … Pegs, people and stars have nothing in common."

- **02A · Heights (00:17.2–00:21.5).** On "measure" (#48, 00:17.350) a row of ink silhouettes of varying height walks in from the right. On "ten thousand"
  (#52, 00:18.450) they collapse into blue dots that stack by height into a dot histogram, and a counter ticks to `10,000`. On "The same bell" (#54–56, 00:20.02–00:20.77)
  the bell snap.
- **02B · Montage (00:21.5–00:28.6).** Three more glass panels slide in, each building its own blue histogram from a live process, each finishing with a gold snap:
  1. "astronomer measures a star" (#64–67, 00:23.08–00:24.14): a star with a jittering crosshair; each measurement drops a dot into the histogram.
  2. "noise in a camera sensor" (#69–73, 00:25.02–00:25.96): a 12 × 12 patch of flickering grey pixels; their brightness values stream into bins.
  3. "scores on a big exam" (#75–79, 00:26.81–00:28.19): a stack of score cards flips; scores fill bins 0–100.
- **02C · Bell after bell (00:28.6–00:31.4).** The five panels (board, heights, star, sensor, exam) arrange into a 2.5D arc. On each "bell" (#81, 00:28.910;
  #83, 00:29.900; #85, 00:30.910) one more gold curve brightens. On the last one, all five curves **lift out of their panels and fly to the center**,
  re-standardized, and land exactly on top of each other as one curve. This is the image of the whole film.
- **02D · Nothing in common (00:31.4–00:34.7).** The panels dim to 25 %. On "Pegs" (#86, 00:31.380), "people" (#87, 00:31.890) and "stars" (#89, 00:32.600) three
  ink icons (a peg, a silhouette, a star) appear in a row. On "nothing in common" (#91–93, 00:33.26–00:33.98) thin vertical dividers draw between them.

---

### S03 — The Questions and the Promise
**Time:** 00:34.660 → 00:56.720 (#168 "Let's", 22.1 s) · **Dimension:** 2D
**Engines:** skia (icons, bell, teaser chips, title lockup), Typst (formula, π), fx (chroma kick, crack, light sweep)
**Purpose:** Plant the three open loops, then promise the route. This is where the analytics show viewers leaving, so every 2–3 s something changes.

**VO:** "So why do they all draw the same curve? … some of the most important things in our world do not follow it at all."

- **03A · Same curve? (00:34.7–00:37.1).** On "why" (#95, 00:34.800) each icon emits a gold line. On "same curve?" (#101–102, 00:36.15–00:36.44) the lines
  converge into one bell at the center, and a small muted `?` sits above its peak.
- **03B · Why π? (00:37.1–00:43.1).** On "formula" (#107, 00:37.970) the full normal pdf types in under the curve (Typst, ink at 60 %, small). On "pi" (#109, 00:39.040)
  only the π glows pink and lifts out of the formula, enlarging. On "circles" (#113, 00:39.760) a pink circle draws around it. On "no circle anywhere in sight"
  (#117–121, 00:41.21–00:42.51) the circle fades and a thin scan line sweeps across the bell: no circle anywhere. The π hangs with a pink `?`.
  (**Open loop:** this exact π glyph returns in S15C.)
- **03C · The route (00:43.1–00:52.0).** Four small teaser chips, 1.5 s each, left to right along the bottom third:
  1. "single coin flip" (#129–131, 00:44.56–00:45.18): a coin flips, and on landing one peg splits a path teal/orange.
  2. "hidden circle" (#134–135, 00:46.01–00:46.43): a cloud of blue darts, and a pink ring fades in inside it.
  3. "simple ruler" (#140–141, 00:48.04–00:48.39): a bell with three violet bands and ruler ticks.
  4. "bell breaks" (#150–151, 00:51.12–00:51.47): the bell **cracks** on its right shoulder (chroma kick).
- **03D · Title (00:52.0–00:56.7).** On "most important things" (#156–158, 00:52.82–00:53.50) a **red long tail** whips out of the crack and stretches off the right edge of frame.
  On "do not follow it at all" (#162–167, 00:54.50–00:56.03) the camera pulls back and the title lockup sets: **THE BELL CURVE** (display, ink) over
  `why it's everywhere` (sans, gold), with a light sweep on "all" (#167, 00:56.030).

**Out:** On "Let's" (#168) a zoom-blur push into the top peg of the board. Chapter 1.

---

## CHAPTER 1 — COUNTING PATHS
Eyebrow: `01 · COUNTING PATHS` at 00:57.0.

### S04 — One Peg, Two Rows
**Time:** 00:56.720 → 01:15.620 (#232 "Keep", 18.9 s) · **Dimension:** 2D
**Engines:** skia (Galton Board in teach mode: 1–2 rows, large pegs; coin), numpy
**Purpose:** Turn the board into counting, with the smallest possible example.

**VO:** "Let's go back to the board of pegs. A ball meets a peg … The edges can only be reached one way."

- **04A · A coin flip (00:56.7–01:02.5).** One large peg at center. On "ball meets a peg" (#177–180, 00:58.80–00:59.51) a single blue ball falls and touches it,
  with a tiny spark. On "left" (#183, 01:00.210) a dashed teal arc shows the left hop. On "right" (#185, 01:00.720) a dashed orange arc shows the right hop. On "coin flip" (#188–189,
  01:01.61–01:02.13) a thin coin spins in 3D above the peg; its faces read `L` (teal) and `R` (orange).
- **04B · Rows (01:02.5–01:07.1).** On "After one row" (#190–192, 01:02.50–01:03.01) two landing slots appear. On "two places" (#195–196, 01:03.84–01:04.03) each slot
  shows `1`. On "After two rows" (#200–202, 01:05.14–01:05.67) a second row of pegs drops in. On "three" (#205, 01:06.590) three slots appear.
- **04C · Two ways to the middle (01:07.1–01:15.6).** On "middle one" (#208–209, 01:07.44–01:07.75) the middle slot glows. On "two different ways" (#214–216,
  01:08.70–01:09.74) two balls replay side by side: on "left then right" (#217–219, 01:10.02–01:10.72) path one draws as a teal segment then an orange segment;
  on "right then left" (#221–223, 01:11.33–01:12.12) path two draws orange then teal. Both end in the middle slot, which reads `2`.
  On "edges" (#225, 01:13.080) the outer slots each light one single-colored path (teal-teal, orange-orange) and read `1`.

---

### S05 — Pascal's Triangle
**Time:** 01:15.620 → 01:29.780 (#265 "With", 14.2 s) · **Dimension:** 2D
**Engines:** skia (board → glass plaque), Typst (numbers), Histogram (mini bars)
**Purpose:** The counts have a pattern, and the pattern is already bell-shaped.

**VO:** "Keep going, and you are really just counting paths … One, four, six, four, one."

- **05A (01:15.6–01:21.4).** On "Keep going" (#232–233, 01:15.62–01:15.92) rows 3 and 4 drop in. On "counting paths" (#239–240, 01:17.60–01:18.02) all paths to each slot
  draw as faint fans. On "Write those counts down" (#241–244, 01:18.58–01:19.70) each gap between pegs gets its count, and each new number shows two tiny
  arrows from the two counts above it (`1 + 1 → 2`, `1 + 2 → 3`).
- **05B (01:21.4–01:29.8).** On "Pascal's triangle" (#251–252, 01:21.36–01:22.14) the numbers lift off the board into a glass plaque, set as a clean triangle.
  The rows light on the spoken numbers: row 2 on "One, two, one" (#253–255, 01:22.94–01:24.02), row 3 on #256–259 (01:24.72–01:26.22), and row 4 number by number
  on "One, four, six, four, one" (#260–264, 01:26.74–01:29.09). Beside each lit row, a **mini blue bar chart** of the same numbers grows. By row 4 the bars are
  visibly bell-shaped (no gold yet; the viewer should notice it first).

---

### S06 — Ten Rows: 1,024 Paths
**Time:** 01:29.780 → 01:47.060 (#315 "That", 17.3 s) · **Dimension:** 2D
**Engines:** skia (Galton Board, 10 rows; additive path light), numpy (all 1,024 paths), Typst (`2^10`, `binom(10, 5)`)
**Purpose:** The punchline of counting: the middle wins because there are more ways to get there.

**VO:** "With ten rows of pegs, there are one thousand twenty four possible paths … There are simply far more ways to get there."

- **06A · All paths as light (01:29.8–01:34.1).** On "ten rows" (#266–267, 01:30.08–01:30.37) a 10-row board cascades in. On "one thousand twenty four" (#272, 01:31.760)
  all 1,024 paths draw at once with **additive blending at low alpha**, so each segment's brightness equals the number of paths through it. The center
  of the board glows brightest; the bell appears *as light* before any ball falls. A Typst chip reads `2^10 = 1,024`.
- **06B · Only one (01:34.1–01:38.3).** On "Only one" (#275–276, 01:34.06–01:34.36) everything dims except the leftmost path. On "far left bin" (#281–283, 01:35.58–01:36.04)
  that bin reads `1`. On "left, ten times in a row" (#284–289, 01:36.42–01:37.86) ten teal `L` chips tick along the path, one per row.
- **06C · 252 to the middle (01:38.3–01:47.1).** On "two hundred fifty two" (#291, 01:38.600) the 252 paths ending in the middle bin light up as a bright braid, and a counter
  ticks to `252` (small chip `binom(10, 5) = 252`). On "Nothing pushes the balls" (#299–302, 01:42.26–01:43.13) a single ball falls straight through the braid with
  no force arrows. On "far more ways" (#309–311, 01:45.40–01:45.84) every bin shows its count (`1 10 45 120 210 252 210 120 45 10 1`), the counts become blue bars,
  and on "get there" (#313–314, 01:46.24–01:46.44) the gold bell snaps over them.

---

### S07 — The First Secret
**Time:** 01:47.060 → 01:56.620 (#343 "But", 9.6 s) · **Dimension:** 2D
**Engines:** skia (step chips, cancellation sparks), hud (glass pill)
**Purpose:** Name the idea in one picture: extremes need agreement, the middle only needs cancellation.

**VO:** "That is the first secret of the bell … An ordinary result only needs the steps to roughly cancel out."

- **07A (01:47.1–01:52.8).** On "first secret" (#318–319, 01:47.71–01:48.07) a glass pill `secret 1 · counting` sets in at top. On "extreme result" (#324–325,
  01:49.57–01:50.09) a row of ten teal `L` chips appears on the left half. On "every random step to agree" (#327–331, 01:50.91–01:52.18) they click into
  alignment like a lock, and a pointer slides all the way to the left edge of a mini number line.
- **07B (01:52.8–01:56.6).** On "ordinary result" (#333–334, 01:52.95–01:53.47) the right half shows a mixed row `L R R L R L L R L R`. On "roughly cancel out"
  (#340–342, 01:55.15–01:56.36) teal and orange chips pair up and annihilate in small sparks, and the pointer settles near the center.

---

## CHAPTER 2 — ADDING DICE: THE CENTRAL LIMIT THEOREM
Eyebrow: `02 · ADDING DICE` at 01:56.8.

### S08 — One Die, Two Dice
**Time:** 01:56.620 → 02:18.740 (#409 "Add", 22.1 s) · **Dimension:** 3D die → 2D
**Engines:** **PyVista** (glass die with ink pips, cached tumble; skia isometric fallback), skia (6 × 6 outcome grid, Histogram), numpy (`convolve`)
**Purpose:** Show that the bell isn't about coins: it comes from adding.

**VO:** "But a peg is a perfectly fair coin. What if the randomness is messier? … The flat shape has become a triangle."

- **08A · Coin → die (01:56.6–02:01.3).** On "perfectly fair coin" (#348–350, 01:57.45–01:58.60) the `L/R` coin spins once more. On "messier" (#356, 02:00.590) it wobbles and
  folds into a die.
- **08B · One die is flat (02:01.3–02:08.2).** On "Roll one die" (#357–359, 02:01.30–02:02.05) the die tumbles and lands. On "one to six" (#363–365, 02:03.68–02:04.04) six
  blue bars rise to the same height, labeled 1–6. On "flat" (#373, 02:06.550) a thin level line runs across their tops. On "no bell at all" (#374–377, 02:07.03–02:07.77)
  a ghost gold bell tries to snap, doesn't fit, and fades.
- **08C · Two dice make a triangle (02:08.2–02:18.7).** On "two dice and add them" (#380–384, 02:08.78–02:09.83) two dice roll, with a `+` and a sum chip. A 6 × 6 grid of
  all pairs fades in, with each cell showing its sum. On "seven is the favorite" (#386–389, 02:11.00–02:11.60) the anti-diagonal of sevens lights. On "six different
  pairs" (#391–393, 02:12.61–02:13.26) its six cells pulse with a count `6`. On "only one pair makes two" (#397–401, 02:14.65–02:15.70) the corner cell (1, 1) lights alone.
  Then the anti-diagonals **slide down and stack** into bars 2–12. On "triangle" (#408, 02:17.880) an ink outline traces the triangle. A tiny muted `∗` between two
  flat die PMFs sits beside it.

---

### S09 — Three Dice, Ten Dice
**Time:** 02:18.740 → 02:25.220 (#429 "Here", 6.5 s) · **Dimension:** 2D
**Engines:** Histogram (`morph_to`, exact PMFs), Bell (fit)
**Purpose:** The bell grows out of the triangle.

**VO:** "Add three dice, and the corners soften into a curve. Add ten dice, and you get a nearly perfect bell."

- On "three dice" (#410–411, 02:18.95–02:19.30) the histogram morphs to the exact sum of 3 dice (16 bars) and a dice counter reads `n = 3`. On "corners soften"
  (#414–415, 02:20.00–02:20.50) the triangle outline relaxes into a curve. On "ten dice" (#420–421, 02:22.13–02:22.59) it morphs to the sum of 10 dice (51 bars), `n = 10`.
  On "nearly perfect bell" (#426–428, 02:23.66–02:24.63) the bell snap.

---

### S10 — The Lopsided Die
**Time:** 02:25.220 → 02:36.380 (#463 "This", 11.2 s) · **Dimension:** 2D
**Engines:** skia (warped die glyph), Histogram (exact convolution powers), Bell
**Purpose:** The surprise: even an unfair start ends in the same bell.

**VO:** "Here is the surprising part. Start with a lopsided die … You still get the same bell."

- **10A (02:25.2–02:31.1).** On "surprising part" (#432–433, 02:25.82–02:26.49) the bell clears. On "lopsided die" (#437–438, 02:27.67–02:28.24) a die appears with its six face
  bulging and glowing. On "six half the time" (#443–446, 02:29.76–02:30.52) its PMF rises: five short bars at 0.1 and one tall bar at 0.5. The shape is lopsided.
- **10B (02:31.1–02:36.4).** On "Add enough of them together" (#447–451, 02:31.10–02:31.89) the counter steps `n = 2, 3, 5, 10, 30`, and the histogram morphs through the exact
  convolution powers, re-standardized. The skew is visible at first. On "melts away" (#455–456, 02:33.60–02:33.95) it disappears. On "same bell" (#461–462, 02:35.53–02:35.83)
  the bell snap, and a small inset shows the fair-dice bell landing exactly on top of it.

---

### S11 — The Central Limit Theorem
**Time:** 02:36.380 → 02:54.740 (#513 "And", 18.4 s) · **Dimension:** 2D
**Engines:** skia (mini-distribution glyphs, blur dissolve, title), Bell, Dial pair
**Purpose:** Name the theorem and state it in one picture.

**VO:** "This is called the central limit theorem … where the center is, and how wide the spread is."

- **11A (02:36.4–02:39.1).** On "central limit theorem" (#467–469, 02:37.47–02:38.36) the title sets in display type, with a gold underline and a light sweep.
- **11B (02:39.1–02:47.7).** On "add up many small, independent random effects" (#472–478, 02:39.62–02:41.98) a row of eight tiny, different blue distributions appears
  (flat, lopsided, coin, triangle, U-shape, spike, exponential-like, two-bump) with `+` signs between them. On "independent" (#476) they space apart. On "total follows a bell curve"
  (#480–484, 02:42.80–02:44.26) they funnel down into one sum, and a bell pours out below. On "no matter what each single effect looks like" (#485–493, 02:44.70–02:47.30)
  the small shapes keep changing while the bell stays perfectly still.
- **11C (02:47.7–02:54.7).** On "washed out" (#497–498, 02:48.80–02:49.29) the small shapes blur and dissolve. On "Only two things survive" (#499–502, 02:49.82–02:50.82)
  the Dial pair fades in under the bell. On "where the center is" (#503–505, 02:51.64–02:52.21) the gold center line glows. On "how wide the spread is" (#508–512,
  02:53.09–02:54.53) a violet double arrow stretches across the bell's width.

---

### S12 — Addition Is the Bell
**Time:** 02:54.740 → 03:10.500 (#560 "So", 15.8 s) · **Dimension:** 2D
**Engines:** Crowd, skia (nudge arrows, path morph), numpy (seeded random walks)
**Purpose:** Connect the theorem back to the cold open, then compress it into one image.

**VO:** "And this explains the list from the start … The bell is simply what addition looks like."

- **12A (02:54.7–02:57.1).** On "the list from the start" (#516–520, 02:55.67–02:56.53) the five S02 panels flash past at the top as a thin strip.
- **12B (02:57.1–03:07.9).** On "Your height" (#521–522, 02:57.06–02:57.36) one silhouette stands at center with a height marker. On "thousands of genes" (#525–527, 02:58.31–02:59.04)
  a cloud of tiny ticks surrounds it. On "food, sleep, and health" (#531–534, 03:00.28–03:01.77) three small icon chips appear (bowl, moon, heart). On "nudging you a little up
  or a little down" (#537–545, 03:02.73–03:04.69) dozens of tiny arrows (orange up, teal down) push the marker, and it jitters. On "Many small pushes, added together"
  (#546–551, 03:05.26–03:06.91) the arrows **stack tip to tail** into a vertical random walk, and the marker lands. On the right, a crowd of silhouettes does the same at
  high speed, and their final heights pour into a blue histogram.
- **12C (03:07.9–03:10.5).** On "The bell is simply what addition looks like" (#552–559, 03:07.86–03:10.00) a large gold `+` sits at center and **morphs into the bell
  curve** (resampled outline morph), with a light sweep on "addition" (#557, 03:09.130).

---

## CHAPTER 3 — WHERE e AND π COME FROM
Eyebrow: `03 · WHERE e AND π COME FROM` at 03:10.7.

### S13 — The Dart Target
**Time:** 03:10.500 → 03:31.500 (#619 "Those", 21.0 s) · **Dimension:** 2D
**Engines:** Dart Target, skia (rule cards), numpy (seeded 2D Gaussian darts)
**Purpose:** Set up the two assumptions behind the formula with a physical picture.

**VO:** "So what is the exact shape of this curve? … Second, only the distance from the center matters. Not the direction."

- **13A (03:10.5–03:18.1).** On "exact shape" (#564–565, 03:11.34–03:11.72) the camera pushes into the bell's shoulder (what is this curve exactly?). On "surprising place" (#574–575,
  03:14.59–03:15.29) the bell fades. On "throwing darts at a target" (#577–581, 03:16.37–03:17.41) a minimal target draws (thin rings, bullseye), and darts land as blue dots with
  tiny impact sparks.
- **13B (03:18.1–03:22.0).** On "not perfect" (#585–586, 03:18.91–03:19.17) the darts scatter around the center (2D Gaussian, about 300 of them). On "two things" (#590–591,
  03:21.07–03:21.30) two empty glass rule cards appear at the right, labeled `1` and `2`.
- **13C · Rule 1 (03:22.0–03:27.2).** On "First" (#592, 03:22.020) card 1 lights. One hero dart is picked out. On "left or right" (#595–597, 03:23.34–03:23.78) its horizontal
  error draws as a teal segment. On "up or down" (#605–607, 03:26.34–03:26.64) its vertical error draws as an orange segment. A teal histogram of all horizontal errors grows
  along the bottom, and an orange one up the side. On "nothing to do with" (#599–602) the dart cloud is filtered to one vertical strip at a time, and the orange marginal
  stays the same shape (independence). Card 1 gets the label `independent`.
- **13D · Rule 2 (03:27.2–03:31.5).** On "Second" (#608, 03:27.180) card 2 lights. On "distance from the center matters" (#611–615, 03:28.30–03:29.78) an ink ring passes through the hero
  dart with its radius r drawn. On "Not the direction" (#616–618, 03:30.10–03:30.61) the dart slides around the ring, and a density readout next to it stays fixed.
  Card 2 gets the label `round`.

---

### S14 — e to the Minus x Squared
**Time:** 03:31.500 → 04:04.660 (#725 "And", 33.2 s) · **Dimension:** 2D
**Engines:** Typst (`e^(-x^2)` build), skia (contour insets, decay chart, parabola, bars), numpy (real f(x)·f(y) contour maps, exact values)
**Purpose:** Derive the core shape visually, then explain e and the square.

**VO:** "Those two simple rules force a single answer … Double the distance, and the chance does not just halve. It collapses."

- **14A · One answer (03:31.5–03:45.7).** On "force a single answer" (#623–626, 03:33.00–03:33.96) the two rule cards merge into one plaque. On "missing by a distance x"
  (#630–634, 03:35.47–03:36.73) the teal marginal histogram lifts out and its axis is labeled x. On "e to the power of minus x squared" (#639–646, 03:38.10–03:39.51) the Typst
  formula `e^(-x^2)` builds term by term (e lime on #639, the minus on #644, `x^2` on #645–646), and its curve traces exactly over the histogram.
  On "No other shape" (#647–649, 03:40.42–03:40.93) two small insets show the 2D pattern made by multiplying other candidate curves, f(x)·f(y): a triangle curve gives
  **diamond** contours and a 1/(1+x²) curve gives **star-shaped** contours. Both are computed and both get a muted strike. On "perfectly round" (#660–661, 03:44.60–03:45.14)
  a third inset shows the Gaussian's contours: perfect pink-tinted circles. It grows and replaces the other two.
- **14B · Why e (03:45.7–03:52.7).** On "number e" (#666–667, 03:46.58–03:47.05) the `e` in the formula glows lime. On "natural growth" (#675–676, 03:49.00–03:49.50) a small chart
  draws `e^x` rising. On "running in reverse" (#678–680, 03:50.20–03:50.86) it mirrors into `e^(-x)`. On "natural decay" (#682–683, 03:51.52–03:52.04) it falls away, lime.
- **14C · Why squared (03:52.7–04:04.7).** On "Why x squared?" (#684–686, 03:52.66–03:53.00) the `x^2` term pulses. On "a mistake to the left" (#690–694, 03:54.93–03:55.75)
  a parabola draws and a teal point sits at x = −2. On "to the right" (#701–704, 03:57.12–03:57.88) an orange point sits at x = +2, and both map to the same value, 4 (dashed
  lines meet). On "fall off fast" (#710–712, 03:59.52–04:00.02) back to the curve `e^(-x^2)`. On "Double the distance" (#713–715, 04:00.54–04:01.06) two blue bars stand
  at x = 1 (value 0.368) and x = 2. On "does not just halve" (#719–722, 04:02.10–04:02.70) a dashed ghost bar at half height (0.184) appears at x = 2. On "It collapses" (#724,
  04:03.520) the real bar drops to 0.018 with a squash, and a chip reads `÷ 20`. (All values computed: e⁻¹ = 0.368, e⁻⁴ = 0.0183, ratio 20.1.)

---

### S15 — The Hidden Circle
**Time:** 04:04.660 → 04:26.140 (#795 "Put", 21.5 s) · **Dimension:** 2D → 3D → 2D
**Engines:** Dart Target, **PyVista** (gold Gaussian surface of revolution, sliced into pink rings; skia wireframe fallback), Typst (`∫ e^(-x^2) dx = sqrt(pi)` morph), fx (chroma kick, light sweep)
**Purpose:** Pay off the cold open's π question. This is the film's "aha" beat.

**VO:** "And now, the circle. Those darts spread out in rings around the bullseye … The circle was hiding in the symmetry of the darts all along."

- **15A (04:04.7–04:09.2).** On "the circle" (#727–728, 04:05.20–04:05.47) the dart cloud returns. On "spread out in rings" (#731–734, 04:06.92–04:07.61) pink iso-density rings
  fade in through the cloud. On "bullseye" (#737, 04:08.490) the center glows.
- **15B (04:09.2–04:16.6).** On "total area under the curve" (#743–747, 04:10.20–04:11.20) the view returns to the 1D curve, and the area under it fills with translucent gold. On "add up to one"
  (#753–756, 04:13.11–04:13.57) a chip reads `area = 1`. On "quietly travels around those rings" (#758–763, 04:14.14–04:16.61) the camera tilts into 3D: the curve spins into the
  gold surface `e^(-(x^2 + y^2))` above the target, and it splits into thin pink concentric shells that light from the center outward (the polar trick, shown, not stated).
- **15C (04:16.6–04:26.1).** On "area under e to the minus x squared" (#765–772, 04:17.44–04:19.01) the Typst integral `integral e^(-x^2) dif x` sets under the curve. On
  "exactly the square root of pi" (#777–782, 04:20.50–04:22.20) it morphs to `= sqrt(pi)`, with π pink, a chroma kick and a readout `≈ 1.7725`. On "The circle was hiding"
  (#784–786, 04:22.83–04:23.34) **the same pink π glyph from S03B flies back in** and settles in the bullseye of the ringed target. On "all along" (#793–794, 04:25.14–04:25.38) a light sweep.

**Math notes:** (∫e^(−x²)dx)² = ∬e^(−(x²+y²)) dx dy = ∫₀^2π∫₀^∞ e^(−r²) r dr dθ = π. The shells in 15B are the r dr rings of that integral.

---

### S16 — The Full Formula and Its Two Dials
**Time:** 04:26.140 → 04:55.220 (#883 "Those", 29.1 s) · **Dimension:** 2D
**Engines:** Typst (term-by-term build with token colors), Bell, Dial pair, readouts
**Purpose:** Assemble the formula from parts the viewer has already met, then make it friendly with two dials.

**VO:** "Put everything together and you get the normal distribution … Everything else simply keeps the total area equal to one."

- **16A · Build (04:26.1–04:38.5).** On "normal distribution" (#802–803, 04:28.12–04:28.47) a chip `normal distribution` sets at top. The formula builds on its spoken terms:
  `f(x) =` (#804–807, 04:29.46–04:29.82); `1 / (sigma sqrt(2 pi))` (#808–817, 04:30.36–04:33.02, σ violet, π pink, with the `√π` glowing briefly as "the circle");
  `e^(...)` (#818–819, 04:33.38–04:33.89, e lime); `-(x - mu)^2` (#824–828, 04:34.92–04:36.10, μ gold); `/ (2 sigma^2)` (#829–832, 04:36.86–04:37.73). The `e^(-x^2)` core briefly
  outlines in lime as "the darts' answer".
- **16B · Two dials (04:38.5–04:41.5).** On "looks frightening" (#833–835, 04:38.50–04:38.86) the formula shrinks to the top. On "two dials" (#840–841, 04:40.57–04:40.85) μ and σ
  slide out of the formula and become the two glass knobs of the Dial pair, under a live bell.
- **16C · μ and σ (04:41.5–04:55.2).** On "Mu slides the bell" (#842–843, 04:41.54–04:41.69) the μ knob turns: the bell slides left on "left" (#846, 04:42.680) and right on "right"
  (#848, 04:43.150). On "average" (#852, 04:44.290) a gold center line is labeled `μ = average`. On "Sigma stretches the bell wider" (#853–857, 04:44.88–04:46.26) the σ knob turns
  and the bell widens and flattens. On "squeezes it narrower" (#859–861, 04:46.72–04:47.46) it narrows and rises. On "standard deviation" (#865–866, 04:48.69–04:49.10) a violet
  `±σ` bracket sets. On "typical distance from the average" (#868–872, 04:50.00–04:51.37) a violet arrow runs from μ to μ + σ. On "keeps the total area equal to one" (#873–882,
  04:51.90–04:54.70) the `1/(σ√(2π))` term glows while σ wobbles once more, and a live `area = 1.000` readout never changes.

---

## CHAPTER 4 — THE RULER: 68, 95, 99.7
Eyebrow: `04 · THE RULER` at 04:55.4.

### S17 — Heights in Sigma
**Time:** 04:55.220 → 05:22.660 (#946 "Beyond", 27.4 s) · **Dimension:** 2D
**Engines:** Bell (bands), Crowd (dot histogram ↔ silhouettes), skia (σ ruler), scipy (`erf` for band shares)
**Purpose:** Turn the two dials into a practical ruler with a concrete example.

**VO:** "Those two dials give us a powerful ruler … Three sigma, and it is ninety nine point seven percent."

- **17A (04:55.2–05:05.3).** On "powerful ruler" (#889–890, 04:56.70–04:57.30) a violet ruler graduated in σ units (−3σ … +3σ) slides in under the bell. On "adult men" (#892–893,
  04:58.47–04:58.68) the crowd returns as a dot histogram of heights (seeded, illustrative). On "one hundred seventy five centimeters" (#902–903, 05:01.32–05:02.03) the gold μ line is
  labeled `175 cm`. On "about seven" (#908–910, 05:04.28–05:04.76) the `σ = 7 cm` bracket sets and the ruler relabels in cm: 154, 161, 168, 175, 182, 189, 196.
- **17B (05:05.3–05:15.3).** On "Step one sigma away on each side" (#911–917, 05:05.30–05:07.50) two violet markers step out from μ. On "one hundred sixty eight" (#919, 05:08.450) and "one hundred
  eighty two" (#921, 05:09.400) their labels light. The band between them fills violet. On "sixty eight percent" (#927, 05:13.460) a large readout `68%` sets (small muted `68.27%`
  computed from erf), and the dots inside the band brighten.
- **17C (05:15.3–05:22.7).** On "two sigma" (#933–934, 05:15.81–05:16.04) the band extends in a lighter violet, and on "ninety five" (#939, 05:17.990) `95%` sets. On "Three sigma" (#940–941,
  05:19.22–05:19.74) it extends again, and on "ninety nine point seven" (#945, 05:20.980) `99.7%` sets. The three nested bands hold for a beat as the classic diagram.

---

### S18 — Five Sigma
**Time:** 05:22.660 → 05:36.780 (#986 "But", 14.1 s) · **Dimension:** 2D
**Engines:** Bell (tail loupe, log inset), skia (bump plot, significance meter), scipy (tail probabilities)
**Purpose:** Show how fast the tails vanish, and why that matters in science.

**VO:** "Beyond five sigma, you find fewer than one in a million … They are almost impossible."

- **18A (05:22.7–05:26.6).** On "Beyond five sigma" (#946–948, 05:22.66–05:23.41) the camera pulls out along the ruler to ±5σ. The curve is invisible out there, so a circular loupe opens
  on the 5σ tail with a log-scale inset. On "fewer than one in a million" (#951–956, 05:24.42–05:25.64) a readout sets: `< 1 in 1,000,000` (muted, computed: `5.7 × 10⁻⁷`).
- **18B (05:26.6–05:31.4).** On "physicists" (#960, 05:27.090) a generic particle-detector plot appears: blue event counts over a smooth background, with a small bump. On "five sigma result"
  (#964–966, 05:28.19–05:28.91) a vertical significance meter climbs `1σ … 5σ`. On "discovery" (#971, 05:30.600) the bump and the meter light gold.
- **18C (05:31.4–05:36.8).** On "extreme events are not just rare" (#976–981, 05:32.66–05:34.38) the bell returns and its tails shrink to hairlines. On "almost impossible" (#984–985,
  05:35.35–05:35.88) the tail beyond 5σ fades to a single dim dot.

---

## CHAPTER 5 — WHERE THE BELL BREAKS
Eyebrow: `05 · WHERE IT BREAKS` at 05:37.0.

### S19 — Adding vs Multiplying
**Time:** 05:36.780 → 05:54.540 (#1033 "When", 17.8 s) · **Dimension:** 2D
**Engines:** Crowd (silhouettes with a height ruler), skia (stacked blocks, compounding bars), numpy (seeded additive and multiplicative walks)
**Purpose:** Introduce the one difference that breaks the bell.

**VO:** "But that last sentence is also a warning … A fortune earns returns, and those returns earn more returns."

- **19A (05:36.8–05:39.6).** On "warning" (#993, 05:38.760) the label `almost impossible` from S18 cracks, and a faint red vignette breathes once at the frame edges.
- **19B (05:39.6–05:47.0).** On "tallest person ever recorded" (#995–998, 05:39.74–05:40.89) two silhouettes stand on a height ruler: average (175 cm) and tallest recorded (272 cm,
  labeled `tallest recorded · 272 cm`). On "not even twice" (#1000–1002, 05:41.66–05:42.14) a dashed ghost outline at 2× (350 cm) appears above, clearly not reached. On "built by
  adding" (#1012–1014, 05:45.84–05:46.33) the 175 cm bar fills with small stacked `+` blocks (gold).
- **19C (05:47.0–05:54.5).** On "wealth" (#1018, 05:47.690) a second lane appears beside it. On "multiplying" (#1022, 05:49.360) a red `×` replaces the `+`. On "earns returns"
  (#1024–1026, 05:50.54–05:51.54) its bar grows by a factor each step. On "returns earn more returns" (#1028–1032, 05:52.33–05:54.02) the growth compounds: segments get longer and longer,
  and the bar shoots past the top of the frame while the height lane barely moves.

---

### S20 — The Long Tail
**Time:** 05:54.540 → 06:15.380 (#1094 "In", 20.8 s) · **Dimension:** 2D → 2.5D cards
**Engines:** Histogram, Bell (crack, tail), Crowd (one giant silhouette, camera crane), numpy (10,000 seeded multiplicative walks), fx (chroma kick)
**Purpose:** The visual payoff of the teaser in S03D.

**VO:** "When effects multiply instead of add, the bell breaks … stock market crashes, and viral videos."

- **20A (05:54.5–06:01.2).** On "multiply instead of add" (#1035–1038, 05:55.19–05:56.30) 10,000 multiplicative walks pour into a blue histogram, with a gold bell overlaid that
  no longer fits. On "the bell breaks" (#1039–1041, 05:56.89–05:57.45) the gold curve **cracks** (chroma kick), and the histogram's right side crawls out into a red tail. On
  "long tail stretching far to the right" (#1045–1051, 05:58.77–06:00.59) the camera pans right along the tail, past a few isolated extreme dots.
- **20B (06:01.2–06:09.0).** On "If human height were spread out like wealth" (#1052–1059, 06:01.22–06:02.99) the crowd returns, re-sampled from the wealth shape so that the median
  is still 170 cm (most people get slightly shorter). On "tallest person would stand" (#1061–1064, 06:03.54–06:04.52) one silhouette starts to grow. On "thousands of kilometers high"
  (#1065–1068, 06:05.38–06:05.98) the camera cranes up with it through clouds and the thin blue line of the atmosphere, while a readout climbs in km. On "far above the orbit of the
  space station" (#1070–1076, 06:06.74–06:08.30) a dashed orbit line at `space station · 400 km` passes below, and the readout ends at `> 1,000 km`.
- **20C (06:09.0–06:15.4).** On "same long tails appear" (#1077–1081, 06:09.04–06:10.07) four glass cards fan in, each holding a red long-tail histogram: "cities" (#1086, 06:11.230),
  "earthquakes" (#1087, 06:11.940), "stock market crashes" (#1088–1090, 06:12.76–06:13.46), and "viral videos" (#1092–1093, 06:14.31–06:14.67).

**Design notes:** The height readout is illustrative. It comes from the ratio of a top fortune to median wealth (roughly 10⁶) times 1.7 m, so keep
it as `> 1,000 km`, never a precise figure. *Optional:* the "viral videos" card can use the channel's own view counts (27 uploads, from the analytics export:
one video at 97,728 views, the median near 2,000). It is a genuine long tail and a nice wink. Leave it generic if you'd rather not show channel numbers.

---

### S21 — Added or Multiplied?
**Time:** 06:15.380 → 06:27.180 (#1127 "Let's", 11.8 s) · **Dimension:** 2D
**Engines:** Bell, Histogram, skia (share bar, + / × toggles), numpy (top-1 % share from the S20 simulation)
**Purpose:** The practical takeaway.

**VO:** "In these worlds, the rare event is not almost impossible. It is the one that matters most. So before you trust a bell, ask one question. Are the pieces being added, or multiplied?"

- **21A (06:15.4–06:21.1).** On "In these worlds" (#1094–1096, 06:15.38–06:15.89) a split view: the gold bell's thin tail (left) and the red long tail (right), each with its 5σ-equivalent
  marker. On "not almost impossible" (#1101–1103, 06:17.36–06:17.98) the red marker is still clearly visible while the gold one is a hairline. On "matters most" (#1109–1110, 06:20.04–06:20.59)
  a horizontal share bar under the red tail shows the top 1 % holding a large slice of the total (computed from the simulation), and the extreme dot glows red.
- **21B (06:21.1–06:27.2).** On "trust a bell" (#1114–1116, 06:21.96–06:22.41) a single gold bell sits at center. On "one question" (#1118–1119, 06:23.22–06:23.54) a pill `?` appears above.
  On "added" (#1124, 06:25.670) a gold `+` toggle lights, and a mini bell forms under it. On "multiplied?" (#1126, 06:26.180) a red `×` toggle lights, and a mini long tail forms under it.

---

## CHAPTER 6 — RECAP AND OUTRO
Eyebrow: `06 · RECAP` at 06:27.4.

### S22 — Everything We Built
**Time:** 06:27.180 → 07:06.400 (#1237 "So", 39.2 s) · **Dimension:** 2.5D card arc
**Engines:** skia (six glass recap cards with live miniatures, camera truck, depth of field), Galton Board, Histogram, Bell, Dial pair, Dart Target (all mini)
**Purpose:** Reinforce every idea with a visual the viewer has already seen, in the colors they have learned.

**VO:** "Let's bring it all together … And when effects multiply instead of add, the bell breaks, and the extremes take over."

Six cards in an arc. The camera trucks along it. The active card is at 100 % and the others are at 30 % with depth-of-field blur.

1. **Counting** (#1132–1150, 06:28.62–06:33.28): the 10-row board with the additive path light. "middle" (#1146, 06:32.290) lights the center bins and "edges" (#1150, 06:33.280) the single paths.
2. **Adding** (#1151–1176, 06:33.98–06:42.16): dice sums morph into a bell. "independent" (#1161, 06:36.800) spaces the mini distributions. "No matter how strange" (#1170–1173, 06:40.18–06:40.95)
   swaps in the lopsided die, and the bell doesn't move.
3. **Two dials** (#1177–1189, 06:42.50–06:46.76): the Dial pair. "mu" (#1185, 06:45.470) slides the bell. "sigma" (#1189, 06:46.760) stretches it.
4. **e and π** (#1190–1206, 06:47.46–06:53.42): the formula with token colors. "e" (#1192, 06:48.150) glows lime, "independence" (#1195, 06:48.900) shows the teal/orange dart axes, "pi" (#1197, 06:50.050)
   glows pink, and "circular symmetry" (#1202–1203, 06:51.31–06:51.84) brings up the ringed target.
5. **The ruler** (#1207–1221, 06:53.78–07:00.30): the nested σ bands. `68%` on #1207 (06:53.780), `95%` on #1208 (06:54.600), `99.7%` on #1210 (06:55.760). "one, two, and three sigma" (#1217–1220,
   06:58.78–06:59.91) steps the markers out.
6. **Where it breaks** (#1222–1236, 07:00.94–07:05.78): `+` vs `×`. "the bell breaks" (#1229–1231, 07:03.30–07:03.86) cracks the curve, and "extremes take over" (#1234–1236, 07:04.82–07:05.78) whips out the red tail.

---

### S23 — Not a Coincidence
**Time:** 07:06.400 → 07:14.620 (#1266 "And", 8.2 s) · **Dimension:** 2D
**Engines:** Galton Board (same seed as S01), Bell, fx (light sweep)
**Purpose:** Close the loop on the hook with the exact opening image.

**VO:** "So the next time you see a bell curve, you will know it is not a coincidence. It is the shape randomness takes whenever many little things add up."

- **23A (07:06.4–07:10.6).** On "next time you see a bell curve" (#1239–1245, 07:06.70–07:07.92) the cards collapse to a point, and the S01 board returns with balls already pouring.
  On "not a coincidence" (#1251–1253, 07:09.35–07:09.63) the bins fill.
- **23B (07:10.6–07:14.6).** On "shape randomness takes" (#1257–1259, 07:11.13–07:11.99) the gold curve traces over the pile. On "many little things add up" (#1261–1265, 07:12.90–07:14.33)
  the bell snap, with a light sweep, and a faint gold `+` flickers once inside the curve.

---

### S24 — Next: Why e Is Everywhere (End)
**Time:** 07:14.620 → 07:21.576 (7.0 s), plus the end-screen hold to 07:41.576 · **Dimension:** 2D
**Engines:** Typst (e glyph), skia (end-screen slots, subscribe circle), fx (light sweep)
**Purpose:** Send viewers to the channel's best-performing video.

**VO:** "And if you want to see where that number e really comes from, watch the video on why e is everywhere next. Thanks for watching."

- **24A (07:14.6–07:20.5).** On "number e" (#1273–1274, 07:15.62–07:16.02) a lime `e` lifts out of the bell's formula and grows to center. On "watch the video" (#1278–1280, 07:17.46–07:18.10)
  it slides into the left end-screen slot. On "why e is everywhere" (#1282–1285, 07:18.68–07:19.16) the slot's outline traces with a light sweep.
- **24B (07:20.5–07:21.6).** On "Thanks for watching" (#1287–1289, 07:20.54–07:21.05) the title lockup **THE BELL CURVE** reappears, small, above the slots.
- **End screen (07:21.6–07:41.6).** Black, with a slow, endless pour on the board at 15 % opacity in the background. Two outlined slots for the YouTube end-screen editor: left,
  *Why e Is Everywhere* (named in the narration; the channel's top video); right, *The Math Trick That Turns Calculus Into Algebra | Laplace Transform* (the best subscriber
  conversion, 12.6 per 1,000 views). A subscribe circle sits at the center bottom. The timeline is extended with 20 s of silence.

---

## 4. Build stages (one per session)

Each stage ends with `--frame` stills at the listed times and `--audit`, then a 720p `--preview` of that chapter, before moving on.
Full-quality renders (`--final`, 1080p/4K) are never run in these sessions.

| Stage | Contents | Check stills at (s) |
| --- | --- | --- |
| **A · Foundation** | copy `fx.py`, `typmath.py`, `space.py`, `render.py`, `components/hud.py`, `pv3d/` from `understanding-4d-visually/`; new `theme.py` (`bell-noir`), `cues.py` (AUDIO_DURATION 441.576), `scenes/full.py`; components `galton.py`, `histogram.py`, `bell.py`, `dials.py`, `darts.py`, `crowd.py`; pick and lock the Galton seeds; PyVista smoke test (one die frame, one Gaussian surface frame) | component test frames only |
| **B · Chapter 0** | S01–S03 | 2.0, 4.8, 8.0, 13.6, 16.4, 19.5, 24.0, 30.9, 33.5, 36.3, 40.0, 46.2, 51.5, 55.5 |
| **C · Chapter 1** | S04–S07 | 60.5, 65.8, 70.6, 74.0, 79.0, 89.2, 92.0, 97.0, 100.0, 106.6, 111.5, 116.2 |
| **D · Chapter 2** | S08–S12 (exact PMF morphs first) | 120.8, 126.6, 132.0, 137.9, 142.6, 144.7, 150.0, 155.8, 158.4, 163.5, 174.2, 181.0, 186.7, 189.6 |
| **E · Chapter 3** | S13–S16 (the f(x)·f(y) contour insets and the √π morph first) | 197.0, 203.6, 209.9, 219.6, 225.0, 230.8, 237.6, 243.8, 247.6, 255.8, 262.6, 265.0, 277.8, 282.7, 286.3, 293.0 |
| **F · Chapter 4** | S17–S18 | 297.0, 304.8, 313.6, 321.2, 325.6, 330.7, 336.0 |
| **G · Chapter 5** | S19–S21 | 338.8, 342.2, 353.8, 357.6, 360.4, 368.4, 374.6, 380.6, 386.4 |
| **H · Chapter 6** | S22–S24 plus the end screen | 391.0, 397.0, 405.6, 411.0, 416.0, 424.0, 429.6, 434.0, 439.0, 441.2, 450.0 |
| **I · Polish** | the optional SFX cue sheet (reuse `convolution…/sfx/`: very soft, randomly pitched peg clicks under the pours, a die roll in S08, a glass chime on each bell snap, a low crack on the break), the composite bloom pass, a full 720p preview, and audio-sync spot checks at 10 random cues | — |
| **J · Final** | **not run in this session**: Claude renders 720p previews only. You run the full 1080p (`--final`) locally or the 4K Kaggle bundle (`kaggle/`, the same chunked runner as the earlier projects), then check loudness | — |

### Folder layout

```
why-the-bell-curve-is-everywhere/
  audio.mp3  cue-per-word.srt  normal-subtitle.srt  voiceover.md  scene-plan.md
  theme.py  fx.py  space.py  cues.py  typmath.py  render.py
  components/  galton.py  histogram.py  bell.py  dials.py  darts.py  crowd.py  hud.py
  pv3d/        solids.py (die, Gaussian surface, ring shells)  render.py (camera-matched, cached RGBA renders)
  scenes/      ch0_intro.py  ch1_paths.py  ch2_dice.py  ch3_formula.py  ch4_ruler.py
               ch5_breaks.py  ch6_recap.py  full.py
  output/      frames/  previews/  cache/{pyvista,typst}/
  sfx/  kaggle/  final/
```

Each chapter module follows the earlier projects' pattern: `START = cue(a)`, `END = cue(b)` (Chapter 0 starts at 0.0 and Chapter 6 ends at
461.576), a `T` dict of cue times, `draw_sXX(fr, t)` per scene, one `FunctionSource` with an mtime key, and `OFFSET`, `DURATION` and `STILLS`.
`full.py` checks that the chapters are contiguous.

### Quality bar (applies to every stage)

- Every number on screen is computed: Galton counts from the board's paths, dice PMFs by convolution, band shares from erf, tail probabilities,
  e⁻¹ and e⁻⁴, √π, and the top-1 % share from the simulation. Simulated data (heights, stars, sensors, exams, wealth) is seeded and illustrative.
- **Blue data, gold law.** Bars and dots are always `ball`; the curve is always `bell`. Red appears only after the bell fails. Token colors never change meaning.
- One focal point per frame. Everything else is at 40 % opacity or less.
- Line weights at 1080p: 1 px for grids, 1.5–2 px for geometry, 2.5–3 px for the gold curve. Glow only on the focal element.
- No text smaller than the `label` role, and no paragraph text. `--audit` must pass with no contrast or clutter warnings.
- Retention check for Chapter 0: in the 720p preview, nothing holds unchanged for more than 6 s, and the first ball is moving on frame 0.
- Performance: 2 CPU cores, 3.7 GB RAM, integrated GPU only. The 1,000-ball pour is evaluated analytically per frame (no simulation state). The
  1,024-path light is pre-rendered once to a cached image. PyVista frames are rendered once and cached. Motion blur is enabled only in finals and only for
  the pours (S01, S23), the die tumble (S08B) and the dart throws (S13A). Previews are 720p with motion blur off.
