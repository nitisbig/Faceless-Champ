# FacelessChamp Premium Motion Engine — Spring Motion v1

**Codex implementation brief** · Target repository: `nitisbig/Faceless-Champ` · Proposed feature: deterministic spring-based timeline easing.

## Goal

Add a production-ready **Spring Motion Engine v1** to the existing FacelessChamp core, not a parallel animation system. It should improve transforms for Text, cards, charts, Groups, code panels, and diagrams through smooth approach, controllable overshoot, and settling. Stay CPU-renderer-compatible, preserve backwards compatibility, and do not implement the other nine Premium Motion subsystems yet.

## Architecture audit (verify against the current checkout)

- `src/faceless_champ/animation.py`: `Animation`, `AnimationBuilder`, existing easing helpers (`linear`, `smooth`, `ease_in`, `ease_out`) and presets.
- `src/faceless_champ/timeline.py`: `Scene.play(..., rate_func=...)`; `Track.value_at()` evaluates the interpolation for arbitrary time and has exact boundary returns; `_validate_animated_value` enforces property invariants.
- `src/faceless_champ/scheduling.py`: `Stagger`, `Succession`, `Repeat`; schedule compilation, ping-pong easing reversal, and atomic publish semantics.
- `src/faceless_champ/__init__.py`: stable public imports.
- `docs/motion-graphics.md`, `docs/architecture.md`: public behavior and limitations.

**Do not presume line numbers, class signatures, or tests are unchanged.** Read the local checkout before implementation. Preserve the existing renderer contract and avoid unrelated refactors.

## Design decision: clearly distinguish v1 from a real-time spring simulator

**v1 is spring-shaped deterministic easing**, evaluated at any normalized timeline progress. It solves the damped harmonic oscillator analytically, then maps its response into an animation's finite `run_time`. This is ideal for offline video: seekable, repeatable, fixed duration, compatible with current `Track` and FFmpeg workflows. It is **not** frame-to-frame numerical integration, interactive dragging, retarget-on-interruption, or conservation of velocity across animations. Those are separate future enhancements.

Expose a spring function object that can initially be supplied via the existing API:

```python
from faceless_champ import Canvas, Rectangle, Scene, Spring

scene = Scene(Canvas(1920, 1080, bg="#0C1020"))
card = Rectangle(width=360, height=220, corner_radius=28,
                 fill="#26395B", position=(300, 780), scale=0.82)
scene.add(card)
scene.play(
    card.animate.move_to(960, 540).scale_to(1.0),
    run_time=0.75,
    rate_func=Spring(stiffness=180, damping=23, mass=1),
)
```

**Time semantics:** `Spring.__call__(u)` takes normalized `u in [0,1]`; its physical response is sampled over a derived internal settling horizon and retimed into the supplied `run_time`. Stiffness/damping/mass change the *shape* of the response, and `run_time` changes the total on-screen duration. Do **not** describe these as real-time physics parameters of a continuously running physical body. Guarantee `Spring(0)==0`, `Spring(1)==1`. Near the endpoint, the trajectory must be within an explicit settle tolerance so there is no visually significant final-frame snap.

## Mathematical behavior

Use the second-order spring equation for an error `y = 1 - progress`:

`y'' + (damping/mass) * y' + (stiffness/mass) * y = 0`.

Let `omega = sqrt(stiffness/mass)` and `zeta = damping/(2*sqrt(stiffness*mass))`.

- Underdamped `zeta < 1`: decaying sinusoidal response; overshoot is possible.
- Critical `zeta == 1` (within a numerical tolerance): fastest non-oscillatory decay for zero initial velocity.
- Overdamped `zeta > 1`: sum of two decaying exponentials.

Use stable closed-form expressions (including stable real-root computation for the overdamped case). Avoid frame-step integration, unbounded exponentials/cosh overflow, division by tiny denominators near critical damping, NaN/inf, and iteration that depends on frame rate. For v1, omit `initial_velocity` unless its semantics are clearly normalized and fully tested. Store immutable validated spring settings. Derive and cache a finite settling horizon once per settings object; base completion on both displacement and velocity tolerances, or a conservative analytic envelope, so the trajectory is effectively settled before its explicit terminal return. Define practical upper limits to protect against pathological inputs.

## Property safety: explicit v1 contract

The current timeline interpolates many kinds of values. Under-damped springs may exceed `1` or dip below `0`; simply using a spring for every property would create invalid opacity, RGB, reveal, progress, scale, or size values. Do not silently rely on renderer clamping.

- **Primary v1 targets:** `position`, `rotation`, `scale`, `scale_x`, `scale_y`. Supports Groups through existing tracks.
- Allow `position` and `rotation` to overshoot naturally.
- For positive geometry (`scale`, `scale_x`, `scale_y`), either prove the eased trajectory remains above existing minimum or explicitly use a documented constraint method. Prefer transparent validation/failure over an undocumented correction.
- For properties bounded to `[0,1]` (`opacity`, `reveal`, `draw`, `progress`, `wipe`) and RGBA channels, do **not** apply an unconstrained spring. For v1, reject unsupported spring-target property combinations with clear errors at scheduling time, OR introduce and thoroughly test property-aware saturation (document any loss of bounce). Pick one coherent documented strategy before coding; **prefer reject for v1**.
- For preset spring entrances that also fade, author independent overlapping property tracks: spring `position/scale`, conventional easing for `opacity`. `Scene.at()` and different-property track concurrency already enable this.
- Validate inputs at authoring/scheduling time, not after export begins. Bad spring configurations, invalid property combinations, and impossible geometries should not partially mutate the scene timeline.

## Public API goals

MVP:

```python
Spring(stiffness=180, damping=23, mass=1)
scene.play(card.animate.move_to(960, 540), run_time=0.75, rate_func=Spring(...))
```

Optional, **only after MVP passes tests**:

```python
SPRING_PRESETS = {"gentle": ..., "snappy": ..., "bouncy": ..., "precise": ...}
Spring.preset("snappy")
```

If a preset is added, expose documented numeric parameters and tune using actual rendered examples, not Apple branding. Keep API surface small; don't introduce `spring_to`, a new Scene superclass, or a second Track type without clear necessity.

## Execution order (each phase should be reviewable on its own)

### Phase 0 — Audit + test baseline (NO production code)
1. Inspect repository structure, existing test contracts, `Scene.play`, track sampling, scheduling, and README/architecture docs.
2. Run baseline: `uv run pytest -q`, `uv run ruff check src tests examples` (adjust only to the repo's documented environment).
3. Record relevant existing behaviors, backward-compatibility risks, and the v1 API.
4. Produce a short proposed patch/file map and explicit property-safety policy. **Stop for approval before implementation.**

Deliverable: `docs/plans/spring-motion-v1.md` (if appropriate for repository), baseline results, proposed file edits.

### Phase 1 — Pure spring mathematical kernel
1. Add isolated spring module (suggest `src/faceless_champ/spring.py`).
2. Implement immutable, validated, deterministic spring evaluator; handle damping regimes and stable limits.
3. Implement normalized `Spring.__call__(u)` with exact endpoints and finite sample outputs.
4. Document time/retiming and tolerance semantics. No renderer changes.
5. Unit tests: analytic sanity, damping categories, underdamped overshoot, critical no-overshoot (zero initial velocity), overdamped no-overshoot, arbitrary evaluation order, repeatability, strict invalid-input rejection, extreme numerical stability, exact endpoints, adequate final settling.

**Gate:** math tests pass, no new mandatory dependencies, pure deterministic samples.

### Phase 2 — Integrate with existing tracks
1. Wire `Spring` into existing `rate_func` path with minimal change, preserving callables.
2. Add spring-specific property validation with safe handling of positive scales and clear rejection of unsupported property channels.
3. Ensure `Track.value_at`, `Entry.state_at`, renderer snapshots, `Scene.at`, Group transforms, and explicit `run_time` remain correct.
4. Check transactional behavior on invalid/overlapping animations.
5. Add regression tests for position, rotation, supported scale, Groups, renders sampled out of order, normal `smooth` and `linear`, and preexisting motion presets.

**Gate:** old API results unchanged for non-spring animations; timeline samples reproducible irrespective of FPS.

### Phase 3 — Scheduling and composition integration
1. Verify spring animations inside `Stagger`, `Succession`, and `Repeat` (including ping-pong reversal), with and without schedule time scaling.
2. Verify simultaneous property tracks and `Scene.at()` for spring transform plus smooth fade.
3. Detect and reject invalid collisions at authoring time; respect component removal and lifetimes.
4. Add tests for repeat boundary continuity and consistent final states.

**Gate:** no mutation on failed schedule; compatible with all existing scheduling semantics.

### Phase 4 — Visual examples and documentation
1. Create `examples/spring_motion/render.py` (or match existing examples conventions) rendering a compact 8–12 second spring showcase.
2. Include side-by-side `linear / smooth / gentle spring / snappy spring / bouncy spring`, with identical motion distances.
3. Showcase text slide, card translate/scale, Group of cards, network node settling. Respect existing authoring/renderer APIs.
4. Add a frame-sample storyboard and run a low-resolution preview first.
5. Document parameters, expected limitations, FPS invariance, v1 non-goals, valid properties and presets. Export `Spring` from `faceless_champ.__init__`.

**Gate:** preview MP4 renders with existing Pillow/FFmpeg path; no unexpected jumps, negative scale, overshoot artifacts or clipped objects. Keep safe margins in the visual examples.

### Phase 5 — QA, review, merge
1. Run all tests, ruff, and existing representative demos/verification commands.
2. Sample deterministic frames at matching absolute timestamps from 24, 30, and 60 fps exports or directly from the shared timeline. Assert equivalent states; permit documented raster/encoding differences.
3. Benchmark a repeated static render and a moving spring render; record runtime and memory. A spring evaluation should not materially impact frame time.
4. Review tests for numerical stability and precise safety guarantees. Check any exception path for partial state mutation.
5. Prepare a focused PR with usage docs, test evidence, a preview link/path and no unrelated changes.

**Gate:** tests/review pass, visual approval granted, feature mergeable; only then start Premium Motion System 02 (effects/compositing).

## Acceptance checklist

- [ ] One importable `Spring` object works through `Scene.play(..., rate_func=...)`.
- [ ] Preserves old animation callables and preset behavior.
- [ ] Exact start/end positions and documented settling tolerance.
- [ ] Supports at least position and rotation, plus safe scale/Group transforms.
- [ ] Underdamped, critical, and overdamped behavior is validated and visible.
- [ ] No NaN, inf, invalid size/scale, opacity overflow, or unsupported property animations leak into the renderer.
- [ ] Same scene state at same timestamp, regardless of sampling order or export FPS.
- [ ] `Stagger`, `Succession`, `Repeat(ping_pong=True)`, and `Scene.at` tested.
- [ ] Existing tests and motion graphics showcase continue to pass.
- [ ] Standalone example/demo, documentation and public imports included.
- [ ] No Skia, ModernGL, shaders, new runtime dependencies or alternate scheduler added.

## How to direct Codex

**Prompt 1 — Plan only:**

> Read `SPRING_MOTION_ENGINE_CODEX_PLAN.md` and audit the actual FacelessChamp checkout, especially `animation.py`, `timeline.py`, `scheduling.py`, `components.py`, public imports, and existing tests. Complete **Phase 0 only**. Do not modify production code. Summarize baseline tests, exact integration points, spring parameter semantics, overshoot/scale safety, and the proposed PR breakdown. Do not begin implementation until I approve.

**Prompt 2 — Implement math only:**

> Follow the approved plan. Implement **Phase 1 only**: the pure deterministic spring easing kernel, its unit tests and minimal documentation. Do not touch renderer or scheduling code. Run focused tests and ruff. Show numerical examples and stop. Do not proceed to other phases.

**Prompt 3 — Integrate:**

> Implement **Phase 2 only** from the approved Spring Motion plan. Reuse existing timeline and `rate_func` contracts. Add spring-specific property validation, ensure support for position/rotation/safe scale, test Groups and timeline behavior, and preserve non-spring behavior. Run tests, report results, then stop.

**Prompt 4 — Compose:**

> Implement **Phase 3 only**. Test spring usage in `Stagger`, `Succession`, `Repeat` including ping-pong, and `Scene.at`. Verify failure atomicity and boundary behavior. Do not introduce unrelated animation features. Show diffs and tests, then stop.

**Prompt 5 — Demo and finish:**

> Implement **Phases 4 and 5** in one final reviewable PR: create a rendered 8–12s comparison showcase, docs, examples, and complete QA. Check 24/30/60 fps time sampling consistency; run project test/lint suites. Report limitations and test evidence. Do not begin Premium Motion System 02.

## Codex engineering rules

- Investigate actual APIs before editing; don't invent API names or modules assumed to exist.
- Make small, reversible commits or PRs with tests for each stage.
- No broad refactor, dependency additions, GPU work, or unrelated feature implementation.
- Reject invalid inputs clearly; don't mask bugs with broad exception handling.
- Preserve determinism, rendering contracts, sequence audio timing and backward compatibility.
- Never claim a test/preview passed without having run it. Summarize changed files, commands, results, performance and known limitations at each stop.

## Future roadmap after v1

After acceptance, consider v1.1: direct spring presets for combined entrance (`position/scale` spring + independent opacity ease), parameter visualization and style profiles. Later, if needed, add real-time retargeting and velocity-continuity via an explicitly new time-aware motion model. Then proceed to Premium Motion System 02: advanced compositing (gradients, shadows, blur, glow).
