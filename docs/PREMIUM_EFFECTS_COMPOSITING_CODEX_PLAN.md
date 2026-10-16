> Historical design proposal. Standalone demo data and media evidence were retired
> during the premium reference reset. Current source, tests and API guides are authoritative.

# FacelessChamp Premium Motion Engine — System 02: Effects & Compositing

**Target repository:** `nitisbig/Faceless-Champ`

**Prerequisite:** Spring Motion Engine (System 01) merged, tested, and released or otherwise fixed to a known revision.

**Mission:** Add Apple-keynote-style gradient surfaces, polished shadows, soft glow, blur, and frosted-glass effects as reusable capabilities of the existing FacelessChamp Python video engine. The project MUST preserve its deterministic scene/timeline model, Pillow/FFmpeg exporter, masking, group transforms, optional renderers, 2D/3D integrations, and existing public APIs.

**Repository facts to verify at start (source inspected October 2026):**
- `src/faceless_champ/surfaces.py` already exports `ShadowStyle`, `card_surface`, `card_content_bounds`, and `dot_grid`. `card_surface` pre-rasterizes a round-corner card + blurred shadow at 2x using Pillow and returns an ordinary `Image`.
- `src/faceless_champ/renderer.py` defines `Renderer` and `PillowRenderer`, a fast sprite-composition path (`_scene`), a masked/non-uniform transform path (`_affine_scene`), cached sprite/frame evaluation, and `RGBA` alpha compositing.
- `src/faceless_champ/components.py` defines base components and their `state()` snapshot contract. `Group` supports nested transforms, clipping and masking.
- `src/faceless_champ/timeline.py` evaluates tracks at arbitrary times. Do not add a mutable wall-clock animation loop.
- `src/faceless_champ/spring.py` exposes analytical `Spring`; its existing supported-property restrictions remain in place.
- `docs/clean-flow.md` documents current surface helpers; `docs/architecture.md` and `docs/motion-graphics.md` document compositing and caching.

## Non-negotiable engineering rules

1. **Incremental milestones, no large rewrite.** Do not replace `PillowRenderer`, rewrite the scene scheduler, or introduce GPU/Skia/ModernGL dependencies during System 02.
2. **Preserve backward compatibility.** Old uses of `card_surface(fill="#FFFFFF", shadow=ShadowStyle(...))`, image and group masking, alpha, z-order, `Scene.play`, and render/export must continue to work.
3. **Renderer-independent descriptions.** Separate immutable effect style descriptions, pure gradient/shadow math, bounded raster stages, and renderer integration. Prepare for future optional GPU backend without requiring it.
4. **Correct premultiplied alpha behavior.** No black halos, unexpected dark fringes or crossfaded incorrect RGB around partially transparent pixels. Define where filtering happens and how alpha is handled.
5. **Do not filter the entire canvas for object-only effects.** Calculate local effect regions including blur-spread padding; crop/clip only at the appropriate stage; use bounded memory caches and avoid deeply nested full-canvas RGBA temporaries.
6. **Deterministic arbitrary-time rendering.** Re-render of frame `t` must match across shuffled queries and after prior frames are rendered, at 24/30/60 fps.
7. **Correct parent semantics.** Effects must respect component/group transform, masks, opacity, clipping and stacking. Document whether shadow/glow is applied before or after the group mask. These rules should be explicit before coding.
8. **No effect-parameter animation in 2A.** Avoid expanding timeline/property schemas until static gradients/shadows pass acceptance; add animated effects in 2D.
9. **Keep baseline scenes fast.** No-effects scenes must retain their optimized fast path. Effects pay their own cost.
10. **Preview-first workflow.** Generate 960x540 previews and fixed-time PNG golden screenshots; benchmark at 1080p and inspect 4K smoke frames later.
11. **No external downloads and no hidden asset dependencies.** Core CPU-only functionality works offline on Linux.
12. **Codex must stop at each milestone** and present changed files, tests run, screenshots and known limitations. Never mark complete merely because code compiles.

## Delivery phases

### Phase 0 — Audit + architecture decision (NO CODE CHANGES)

Inspect the latest files/tests, list existing relevant helpers and cache contracts. Write an Architecture Decision Record (ADR) addressing:
- distinction between procedural **surface generators** (rasterize once and become Image components) and **runtime effect passes** on arbitrary component/group layers;
- immutable public API sketches, effect order (`content`, `shadow`, `glow`, `blur`, `mask`, `opacity`, `composite`) and which operations occur before/after transforms;
- coordinate units: authored design pixels vs supersampled output pixels;
- ROI (region-of-interest) calculation and padding for blur, rotated/anisotropically scaled objects, and group effects;
- safe default alpha processing, existing `ShadowStyle` compatibility, cache-key and invalidation strategy;
- interaction with `Scene._scene`, `_affine_scene`, charts, FlowChamp, ArchChamp, and GIF/HTML clips;
- supported effect targets and explicit exclusions per phase;
- baseline render/lint/tests and performance measurements.

**Deliverable:** `docs/decisions/premium-effects-architecture.md` with a diff-sized Phase 2A execution list and screenshots of pre-change baseline. **Stop for review.**

### Phase 2A — Gradient surfaces + existing shadow extension (BUILD FIRST)

Scope: first-class immutable gradient definitions and reusable **pre-rendered** surfaces. Do not introduce generic live per-object postprocessing yet.

Suggested API (proposal, refine during ADR; not existing code):

```python
from faceless_champ import Bounds, LinearGradient, RadialGradient, GradientStop, card_surface

gradient = LinearGradient(
    stops=(GradientStop(0.0, "#15182D"), GradientStop(0.55, "#3647A0"), GradientStop(1.0, "#62DDDB")),
    angle=125,
)
card = card_surface(Bounds(200, 160, 1300, 840), fill=gradient, radius=44)
# Existing `fill="#FFFFFF"` remains valid.
```

Capabilities:
- linear and radial gradients; >=2 ordered stops and exact end colors, optional alpha, multi-stop interpolation;
- validated finite stop offsets in [0, 1] and angles/centers/radii; stable behavior for coincident stops (choose and document rejection or hard edge), zero-size shapes and unsupported geometry;
- full-size/rounded-card surface generators with correct transparent edges, antialiasing, and clean corners;
- extend existing `card_surface()` without breaking `ShadowStyle` or `card_content_bounds()` conventions;
- generate once / reuse by existing image component motion, masking and z-order, including Spring entrance;
- tests for pixel sampling, gradient direction, edge transparency, offset zero/one endpoints, visual consistency at different output scales, and transformed layouts;
- example video and a 3x2 static comparison/contact sheet: flat vs linear vs radial, light/dark shadow variants.

**Explicitly out of scope:** dynamically animating gradient stops; full-screen backdrop blur; general glow on text/3D shapes; replacing `PillowRenderer` or redesigning all component fill interfaces.

**Phase 2A completion gate:** new public surface API + tests + documentation + example render; no existing API regressions; render under CPU-only environment; no clipping or black edges; Codex review complete. **Stop for review/merge.**

### Phase 2B — Isolated glow/blur + reusable effect stack

Implement a minimal immutable effect model (naming set in ADR), e.g. `DropShadow`, `OuterGlow`, `GaussianBlur`, and `EffectStack`, with isolated compositing on supported targets (begin with basic Text, Shape, Image, Group; expand carefully). Reuse old `ShadowStyle` rather than silently introducing contradictory shadow semantics.

Define effect chain ordering, clipping, group behavior and an ROI compositor that filters only the object-region image, including blur padding. Preserve baseline renderer fast path. Ensure render-time effects are deterministic and do not mutate the source component. Add alpha-correct blur tests, edge/crop regression screenshots, bounded caches, rotated/non-uniform group tests, nested opacity + mask semantics, and repeated frame sampling tests.

**Phase 2B gate:** supported objects visibly glow/blur/shadow without clipping or compositing errors; no-effects scenes incur no meaningful regression; 1080p benchmark and memory report. **Stop for review/merge.**

### Phase 2C — Frosted glass + backdrop effects

Implement backdrop blur only after formally defining scene z-order capture: sample already-composited *background behind* the glass element, not foreground or the glass itself. Apply local blur to the clipped rounded shape, optional translucency/tint/border, then render later layers normally. Avoid circular dependencies between group masks, nested clips and blur; explicitly reject unsupported compositions. Provide side-by-side demo of flat/translucent/frosted in dark and light scenes.

**Phase 2C gate:** background-only blur, clean glass borders, correct layering and no screenshot regressions under nested groups. **Stop for review/merge.**

### Phase 2D — Animated effects + polished presets + optimization

Expose a small, typed subset of animatable effect properties (e.g. glow intensity and blur radius) through existing deterministic timeline tracks only after examining property validation and bounds. Avoid animation of entire style objects in a scalar interpolation path. Add named presets for `subtle`, `keynote`, `focus`, `technical`, etc. Benchmark with scene complexity, sample random-timestamp rendering, detect cache leaks, and package an 8–12 second premium examples video.

**Phase 2D gate:** existing animation behavior unchanged, effect animations reliable at 24/30/60 fps, correct repeated/shuffled samples, documentation and example assets pass review. **System 02 completed.**

## Recommended file strategy (not a mandatory directory map)

- Keep or extend `src/faceless_champ/surfaces.py` for one-shot surface generation.
- Introduce a small module for immutable gradient descriptions (`gradients.py`) only if it reduces coupling; otherwise keep style types beside surfaces in 2A.
- Introduce `effects.py` for compositing descriptors when needed in 2B; avoid an abstract plugin architecture before it has real consumers.
- Keep rendering details in short, testable renderer helpers rather than doubling the size of `renderer.py` with unrelated logic.
- Add `tests/test_gradients.py`, `tests/test_effects.py`, `tests/test_effects_compositing.py` as relevant; adopt existing test naming conventions.
- Add `project-local-scene.py/` with preview commands, sample outputs, and scripted fixed-time screenshots.
- Document public APIs in `docs/motion-graphics.md`, `docs/clean-flow.md`, or a focused new effects page and update `README.md` succinctly.
- Changes to kit themes or kit block APIs are opt-in and should wait until core APIs settle; preserve core/kit version compatibility.

## Detailed acceptance and tests

### Correctness and validation
- Reject NaN/Inf positions, angles, radii, blur sizes, stop offsets and invalid color syntax.
- Check gamma/color interpolation is specified and tested (straight sRGB is acceptable for v1 if documented; do not claim linear-light rendering).
- Check gradients at stop boundaries, fully transparent colors and mixed opacity.
- Preserve straight-alpha export with alpha-safe filtering (use premultiplied intermediate processing when necessary).
- Correctly pad shadows and glow, including corner radii, rotations and 2x/4x antialiasing.
- Verify mask/group/nested opacity handling; avoid double-applying alpha and shadow opacity.
- Maintain correct z-index ordering and static frame caching.
- Ensure old string-fill cards and `ShadowStyle` exactly retain their semantic meaning.

### Determinism and lifecycle
- Evaluate same scene at times [0, .1, .37, .77, 1, 2] forward, reverse, shuffled and repeatedly; compare raw rendered bytes/hashes under same settings.
- Render previews at 24/30/60 fps; at equal timestamps outputs should be visually identical for deterministic, non-frame-dependent effects.
- Ensure caches invalidate when gradient/effect config changes through a new authoring object or new renderer; never rely on global mutable state.
- Verify `PillowRenderer.close()` still clears resources and repeated exports do not increase retained references unexpectedly.

### Quality/performance
- Benchmark no-effect baseline before/after with fixed machine/scene/output resolution; report time/frame, RSS and cache memory; choose regression thresholds from baseline rather than pretending fixed universal timing numbers.
- Benchmark 960x540 preview and 1920x1080 output; 4K single-frame smoke test only if hardware allows.
- Do not allocate multiple full-frame RGBA images for per-object blur effects in common scenes; profile worst-case blur/group nesting.
- Export 6+ reference frames demonstrating gradients, shadows, masked cards and transformed scenes; manually inspect edges in addition to automated tests.

## Codex operating protocol

For every phase:
1. Inspect actual latest code, confirm branch/commit and run baselines.
2. Provide short plan: design/API changes, files to edit, test cases, risks.
3. Implement one phase only on `feature/premium-effects-2a` (adapt branch name to phase).
4. Run `uv run pytest -q` and `uv run ruff check src tests examples` (or repository-approved commands).
5. Render sample PNG contact sheet and short preview; report exact commands, FPS, size, memory/runtime, and output locations.
6. Perform focused `/review` (if supported), address issues, and rerun tests.
7. Summarize exactly what was done, what was not done, and whether acceptance gate passes; do not proceed to next phase unprompted.

## Copy-ready Codex prompt — Phase 0

> Work in the FacelessChamp repository. I have completed and merged the Spring Motion Engine. Read `PREMIUM_EFFECTS_COMPOSITING_CODEX_PLAN.md` and inspect the latest `surfaces.py`, `renderer.py`, `components.py`, `layout.py`, `motion.py`, `timeline.py`, and the existing tests/docs. We are starting System 02, Effects & Compositing. Complete **Phase 0 only**: audit the current capabilities, document a minimal safe architecture, clarify alpha/mask/z-index/cache semantics, record test and rendering baselines, and propose a Phase 2A public API for linear/radial gradients plus backward-compatible shadow surfaces. Do not modify production code yet, do not install GPU dependencies, and do not implement Phases 2B–2D. Finish with risks, measurable acceptance criteria, and a short approval checklist. Stop for review.

## Copy-ready Codex prompt — Phase 2A (after approval)

> Implement **Phase 2A only** from `PREMIUM_EFFECTS_COMPOSITING_CODEX_PLAN.md`, following the approved architecture decision. Add immutable linear/radial gradient specs and multi-stop validation, create reusable CPU-rendered rounded gradient surfaces, and extend existing `card_surface()` while preserving existing string-fill and `ShadowStyle` behavior. Make it compatible with current Scene/Group/Spring animation without changing the timeline or renderer architecture. Add tests, docs, a short sample render and a light/dark contact sheet. Run pytest and Ruff, report performance vs baseline, and review changes. Avoid new large dependencies, runtime backdrop blur, generic glow, or unrelated refactors. Stop at the Phase 2A acceptance gate.

## Copy-ready Codex prompt — Phase 2B (after 2A merge)

> Implement **Phase 2B only** from `PREMIUM_EFFECTS_COMPOSITING_CODEX_PLAN.md`. Add the smallest reusable runtime effect pipeline for isolated object-layer drop shadow, glow and Gaussian blur on supported components while preserving fast no-effect rendering, masks, nested opacity/z-index, antialiasing, deterministic frame sampling and memory-bounded local ROI processing. Add focused unit/pixel/regression tests and example renders. Benchmark against baseline, run full tests/Ruff, conduct code review, and stop without implementing backdrop glass or animated effect properties.

## Definition of done for System 02

All four phases merged, public API documented, no compatibility regressions, gradient and light/dark glass showcase renders, deterministic image output, acceptable memory use, and reviewed examples demonstrating premium visual quality with existing Spring animation.
