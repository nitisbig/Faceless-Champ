# Spring Motion v1: Phase 0 architecture proposal

Status: **architecture approved; Phases 1–5 implementation and local QA complete**.
The user authorized Phase 5 after the inspected Phase 4 handoff and then requested
that the completed changes remain local. A PR description is prepared; nothing
was pushed or merged. Audited on 2026-10-15
(Asia/Kathmandu), branch `facelesschamp-agent`, HEAD
`d61fe16594e4f46358f61cb5bca86a982d3b77da`.

This document records Phase 0 of
[the implementation brief](../SPRING_MOTION_ENGINE_CODEX_PLAN.md), followed by the
approved Phase 1–5 implementation evidence below. Phase 0 changed only this plan;
the brief was already untracked when that audit began. Phase 1 added the isolated
kernel; Phase 2 added track validation and the root import; Phase 3 adds preserved
spring reversal metadata and schedule endpoint alignment. Phase 4 adds a public
example, documentation, and inspected preview evidence. Dependencies, renderer,
and existing examples remain unchanged. Phase 5 adds reproducible release
verification and benchmarks, six regressions, and a focused review handoff.

## Recommended architecture

Add one immutable callable `Spring` in a pure, standard-library-only
`faceless_champ.spring` module. Pass it through the existing `rate_func` contract.
Keep `Animation`, `Track`, `Entry`, scene composition, renderer, and export timing
as the single existing animation system. Add spring-specific validation while
tracks are prepared, before publication. Preserve spring metadata through the
scheduler's time reversal with a private callable adapter.

The first release supports position, rotation, and proven-safe uniform/nonuniform
scales, including Groups. Reject every other property for a recognized spring,
even for critical or overdamped settings. Keep fades on independent ordinary
easing tracks. No property saturation, renderer clamping, new Track subclass,
frame integration, new dependency, or renderer-specific spring behavior.

## Current architecture and integration points

Line references below describe the audited HEAD, rather than an assumed API.

| Existing code | Observed contract | Proposed use |
| --- | --- | --- |
| `animation.py:29–35`, `Animation` | Description with targets, explicit starts, per-property keyframes, relative fields, optional callable easing. | No signature change. `Animation(..., rate_func=Spring(...))` already fits. |
| `animation.py:38–131`, builder | Supports move, rotation, uniform and axis scales, plus many bounded/style channels. Validates endpoint inputs. | Keep builders unchanged; endpoint checks alone cannot prove spring trajectory safety. |
| `animation.py:308–320` | Relative uniform scale multiplies; position/rotation add. Interpolation is `a + (b-a)*t`, recursively for tuples. | Validate resolved values and arithmetic after relative resolution, using actual interpolation semantics. |
| `timeline.py:33–54`, `Track.value_at` | Arbitrary timestamp evaluation; returns initial/target exactly outside the open interval. Easing restarts in each keyframe segment. | Keep evaluation unchanged. A spring describes each segment, not a global keyframe-time warp. |
| `timeline.py:73–78`, `Entry.state_at` | Replays chronologically authored tracks without advancing mutable simulation state; later tracks win at shared boundaries. | Preserve seekability, holds, and boundary precedence. |
| `timeline.py:266–403`, `Scene.play/_play` | Ordinary duration defaults to one second. Effective easing is play override, then animation easing, then `smooth`. Resolves starts/keyframes/relative values, prepares the entire batch, then adds snapshots and tracks. | Run private spring trajectory validation after resolution, before `prepared` is published or `self.add` runs. Validate only the effective easing. |
| `timeline.py:426–463` | Existing endpoint validators enforce scale/width/height minimum `0.001`, bounded fractions, colors, and other property rules. | Preserve these validators for all animations; add a separate spring-only allowlist and continuous-range check. |
| `scheduling.py:50–118` | Compiles nested finite schedules against copied entries, then publishes atomically. Explicit `run_time` rescales delays, gaps, and durations. | Reuse the same path and its existing transaction. Do not introduce a spring scheduler. |
| `scheduling.py:90–107` | Repeat captures resolved first-traversal tracks. Reverse uses swapped endpoints, reversed keyframes, and `1-f(1-u)` in a lambda. | For recognized spring easing only, replace that anonymous wrapper with a private immutable adapter retaining progress bounds. Keep the current lambda for other callables. |
| `timeline.py:137–150`, `Scene.at` | Independent properties/objects can overlap. Same-property tracks must be chronological. Context exit preserves the furthest cursor. | Author spring transform plus conventional fade with existing concurrency. Do not change context-manager cursor semantics on exceptions. |
| `components.py:43–127`, `layout.py`, `renderer.py:287–369` | All components expose transforms. Group snapshots compose ancestor transforms. Renderer samples evaluated states and caches their signatures; axis scales use the existing affine path. | Group support comes from tracks. No changes to component state, bounds, rasterization, or caches are expected. |
| `export.py:153–161,213–215` | Samples `start_time + index/fps`; export usually excludes the exact final timestamp. | Retain duration/audio clocks. Add a brief hold in demos so the exact resting state appears in encoded frames. |
| `__init__.py` | Explicit imports and `__all__`. | Add `Spring` during integration, without removing or renaming imports. |

The README development commands, architecture/motion documentation, core tests,
and downstream kit/agent tests were inspected. Existing tests already cover
snapshot isolation, out-of-order frame sampling, preset easing overrides,
relative/keyframe resolution, Group transforms, scheduling atomicity, lifetime
errors, repeat boundary behavior, reversed easing/keyframes, and audio ranges.
These contracts are regression gates, not behaviors to redesign.

## Public Python API and duration contract

Proposed constructor: `Spring(stiffness=180, damping=23, mass=1)`; three numeric
fields only, immutable after construction. No initial velocity, automatic
duration, per-frame update, interruption state, or presets in the MVP.

```python
from faceless_champ import Canvas, Rectangle, Scene, Spring

scene = Scene(Canvas(1920, 1080, bg="#0C1020"))
card = Rectangle(
    width=360, height=220, corner_radius=28, fill="#26395B",
    position=(300, 780), scale=0.82,
)
scene.add(card)
scene.play(
    card.animate.move_to(960, 540).scale_to(1),
    run_time=0.75,
    rate_func=Spring(stiffness=180, damping=23, mass=1),
)
```

`Spring.__call__(u)` accepts finite real normalized progress, returning exactly
zero for `u <= 0` and exactly one for `u >= 1`. Reject nonfinite progress and
invalid types. Constructor values accept real numbers convertible to finite
floats, but reject booleans, strings, complex numbers, and nonnumeric objects.
Use `TypeError` for invalid types and `ValueError` for invalid numeric domains.
Do not alter the repository's more permissive `finite()` utility.

`run_time` retains its existing minimum of `0.000001` seconds and ordinary
one-second default. It determines the entire on-screen duration; no implicit
wait, solver extension, FPS rounding, or audio retiming occurs. Explicit schedule
duration scaling changes only the timeline mapping. Each new segment starts with
zero spring velocity; consecutive animations do not conserve physical velocity.

The response is sampled across a cached settling horizon and retimed to `[0,1]`.
Parameters describe a physical reference response, not physical seconds in the
finished video. With this normalization, equal damping ratios produce the same
normalized curve within numerical tolerance: changing frequency alone is canceled
by the horizon retiming. Stiffness/damping/mass influence shape through damping
ratio; use `run_time` to change speed. Critical and overdamped curves are
non-oscillatory, but their completed, retimed curves are not promises of physical
settling-time comparisons. Document this consequence rather than imply three
independent visual controls.

## Analytical model and numerical policy

For displacement error `y = 1 - p`, use:

```text
m*y'' + c*y' + k*y = 0,   y(0) = 1,   y'(0) = 0
omega = sqrt(k/m),       zeta = c/(2*sqrt(k*m))
s = omega*t,            y_ss + 2*zeta*y_s + y = 0
p(u) = 1 - y(S*u),      H = S/omega
```

The three damping regimes follow the standard characteristic-root model; see
[MIT's damped harmonic oscillator course notes](https://ocw.mit.edu/courses/18-03sc-differential-equations-fall-2011/pages/unit-ii-second-order-constant-coefficient-linear-equations/damped-harmonic-oscillators/).
The stable evaluation forms, completion envelopes, and safety policy below are
the proposed engineering design for this repository.

| Regime | Dimensionless error response |
| --- | --- |
| `0 < zeta < 1`, `q = sqrt((1-zeta)*(1+zeta))` | `exp(-zeta*s) * [cos(q*s) + zeta*s*sinc(q*s)]` |
| `zeta == 1` | `(1+s)*exp(-s)` |
| `zeta > 1`, `a = zeta + sqrt((zeta-1)*(zeta+1))`, `b = 1/a`, `d = a-b` | `exp(-b*s) * [1 + b*s*E(d*s)]` |

Here `sinc(x)=sin(x)/x`, with its stable limit at zero, and
`E(x)=-expm1(-x)/x`, also with limit one at zero. Small-argument series must have
explicit truncation-error tests. In the overdamped case, the roots are `-a` and
`-b`; computing the slow root as `-1/a` avoids cancellation. All exponentials have
nonpositive arguments. No growing `cosh`, subtraction of nearly equal large root
coefficients, or division by a small critical-damping discriminant is needed.
Near-critical branches must converge to the critical formula from both sides;
avoid a wide approximate critical band that would change the motion model.
Use a small-`s` response expansion where necessary to avoid losing tiny positive
progress in `1-y`. Underflow of a decayed tail is acceptable; NaN/inf is not.

Proposed v1 supported numeric domain, subject to the Phase 1 stability gate:

- `1e-6 <= stiffness, damping, mass <= 1e6`, all finite and strictly positive.
- Derived damping ratio `0.02 <= zeta <= 100`; reject undamped, negative damping,
  arbitrarily slow decay, and excessively ill-conditioned configurations.
- Cached dimensionless horizon `S <= 1e5`; bounded constructor work, with at most
  64 bracketing steps and 64 refinement steps. Failure to certify a horizon is a
  configuration error, never a request to fall back to integration.

These are explicit initial product limits, not physical laws or performance
measurements. Phase 1 must test their corners before accepting them; do not
silently widen them or clamp user parameters.

Choose completion using a conservative envelope valid for all future reference
times, not the first zero crossing or a frame grid. One uniform construction is
`mu=zeta` below critical, `mu=1` at critical, and `mu=b` above critical:

```text
|y(s)|   <= (1 + mu*s)*exp(-mu*s)
|y_s(s)| <= s*exp(-mu*s)
```

Select `S >= 2/mu` such that both bounds hold:

```text
(1 + mu*S)*exp(-mu*S) <= 1e-9    # displacement / segment travel
S*S*exp(-mu*S)        <= 1e-7    # |dp/du| at the terminal limit
```

Beyond this bracket both construction criteria decrease. A bounded deterministic
search of these analytical bounds is allowed once at construction; it is not a
time-step solver. Store derived coefficients, `S`, and conservative progress
bounds on the immutable object. Frame sampling then uses constant-work formulas
and has no history or allocations proportional to duration/FPS. No global cache
or lazy mutation is needed.

The Phase 1 record below refines the overdamped completion bound and reserves
floating-point headroom; the public tolerances and parameter limits stay the same.

Exact terminal returns introduce at most the documented normalized residual,
without dividing by the final response or modifying the whole curve to hit one.
Displacement tolerance is relative to segment travel: `1e-9` corresponds to at
most `0.000002` design pixels for a 2000-pixel translation before ancestor
transforms. This is not a universal pixel-error guarantee for unbounded scene
geometry. Speed in property units/second additionally scales with travel divided
by the segment's actual duration; the threshold above is explicitly in normalized
progress units. Test the left-hand terminal limit separately from `Spring(1)`.

## Property safety and authoring-time failure

Only direct `Spring` instances and the engine's private reversed-spring adapter
receive the new rules. Arbitrary user callables retain their existing behavior;
wrapping a spring in a user lambda opts into that existing custom-callable
contract and is outside the certified spring API. Do not introspect closures or
change all easing validation globally.

| Property | v1 policy |
| --- | --- |
| `position`, `rotation` | Allow natural overshoot. Check resolved values, interpolation differences, and conservative result intervals are finite. Rotation remains numeric degrees with the existing direction/path semantics, not shortest-angle interpolation. |
| `scale`, `scale_x`, `scale_y` | Allow only when every resolved segment stays at or above the existing `0.001` minimum for its entire continuous trajectory. Reject unsafe shrink/bounce combinations before scene mutation. |
| `opacity`, `reveal`, `draw`, `progress`, `wipe` | Reject, including no-op tracks and non-oscillatory springs. Use ordinary easing separately. |
| `fill`, `stroke`, `color`, `clip` | Reject RGBA and normalized clip tuples; no channel saturation. |
| All other fields | Reject: width/height, stroke width, corner radius, mask position/dimensions, Number/Countdown value, chart data, map longitude/latitude/rotation/zoom, and custom channels. Transforming the whole component is still supported. |

For an underdamped forward response, a conservative global progress range is
`[0, 1+M]`, where `M=exp(-pi*zeta/sqrt(1-zeta*zeta))`. For critical/overdamped
responses it is `[0,1]`. A global bound can conservatively exceed the extrema
actually reached before `S`; accepting a few fewer extreme scale transitions is
preferable to missing a violation. Zero-velocity forward progress does not dip
below zero, but reversed progress can be negative.

For each resolved scalar segment from `A` to `B`, evaluate the affine range
`A+(B-A)*[p_min,p_max]`, accounting for the sign of `B-A`. Check both coordinates
for position. For scale, the lower bound must be at least `0.001`. Include a
documented conservative floating-point error allowance/outward bound; reject an
uncertifiable transition near the minimum instead of sampling a few frames or
clamping the rendered scale. Constant valid tracks can be accepted directly.
Finite endpoints alone are insufficient: `B-A` or overshoot arithmetic can
overflow. Validate the same arithmetic that the existing interpolation performs.

Apply this proof **to every adjacent keyframe pair**, after timeline starts,
relative transforms, and first-repeat resolved values are known. There is no
global spring warp across a keyframed path. Mixed spring-supported/unsupported
targets in one animation or play override fail as a whole. Even a spring preset
that happens not to overshoot must obey the same property policy.

For ping-pong, preserve `f_rev(u)=1-f(1-u)` and transform the bound to
`[1-p_max, 1-p_min]`. The private adapter must retain the original settings and
bounds through copying, repeated reversal, and nested Repeat. In particular,
revalidating a reversed scale track as a fresh forward spring is incorrect.
Generic callable reversal stays as it is today.

Validation belongs inside `_play` preparation, before publishing any track or
auto-adding a component. Nested-schedule failures must discard the trial and
preserve original entries, tracks, ownership, cursor, and existing Entry identity.
The independent action of entering/exiting `Scene.at` retains its documented
cursor behavior; the new validator must not promise to undo that context manager.

To combine a spring transform and fade, use existing different-property tracks:

```python
from faceless_champ import FadeIn, smooth

start = scene.time
with scene.at(start):
    scene.play(card.animate.move_to(960, 540), run_time=0.75, rate_func=Spring())
with scene.at(start):
    scene.play(FadeIn(card), run_time=0.25, rate_func=smooth)
```

Alternatively, use an animation-level spring with a separate fade animation in
one play call and no outer spring override. Existing combined presets such as
SlideIn/ZoomIn/PopIn/SpinIn include opacity; overriding the whole preset with a
spring will intentionally reject. Their ordinary behavior remains unchanged.

## Compatibility risks and limits

- **Effective easing precedence:** an explicit ordinary easing must override an
  animation-level spring without triggering spring restrictions, and vice versa.
  Preserve the existing callable/truthiness selection behavior for old users.
- **Keyframe boundaries:** springs settle and restart per segment. Unequal/short
  segments compress the response. Existing explicit-start jumps remain explicit
  jumps; spring integration does not promise continuity for discontinuous inputs.
- **Repeat:** cycles count traversals. Forward repeats can reset at a boundary;
  ping-pong reverses time, so it can begin with a tiny terminal velocity and end
  at the original zero-velocity start. Do not replace reversal with a new
  zero-velocity forward response. Odd/even endpoints and next-track precedence
  must match existing behavior.
- **Groups:** parent/child scale and axis scales multiply in existing world
  transforms. Local scale certification does not establish canvas containment,
  collision freedom, bounded world raster sizes, or a minimum world scale.
  Existing renderer resource limits still apply to very large or deeply nested
  geometry. Keep demo trajectories and nested transforms within measured bounds.
- **Scope:** whole Text, chart, diagram, code-panel, and Group transforms work;
  spring-driven internal chart data or domain-specific clip scripts are outside
  v1. No live retargeting, velocity handoff, reflections/negative scale, general
  custom-property certification, or infinite repeats.
- **Determinism:** evaluation order/FPS invariance applies to the same timestamps
  and configuration. Do not promise byte-identical libm results across platforms
  or byte-identical lossy encodings. Test state equivalence and same-renderer
  image repeatability separately.
- **Settling:** a sampled zero crossing alone proves nothing about future decay.
  Check both envelope displacement and normalized velocity, including the final
  open interval and near-critical neighbors. No numerical implementation has been
  validated by this Phase 0 audit.

## Small implementation milestones and proposed patch map

Every phase requires a separate reviewable diff and a stop at its requested gate.
No phase below is authorized by this document alone.

| Phase | Proposed files / change | Required review gate |
| --- | --- | --- |
| **0 — this audit** | Add only `docs/plans/spring-motion-v1.md`. | Approve the API, retiming semantics, parameter domain, property policy, and numerical strategy before coding. |
| **1 — pure mathematical kernel** | Add `src/faceless_champ/spring.py` and `tests/test_spring.py`; update this plan with actual stability evidence. Import from the submodule for this phase. | Closed-form regime/reference checks, near-critical limits, immutable validation, exact endpoints, left-hand settling, arbitrary sample order, parameter-domain corners, bounded constructor work, and analytic extrema checks pass. No renderer/timeline/scheduler edits or dependencies. Stop. |
| **2 — track integration** | Add a private trajectory validator in `timeline.py`; add `Spring` to `__init__.py` imports/`__all__`; add `tests/test_spring_timeline.py`. | Position/rotation/safe scales, all unsupported fields, unsafe shrinking scales, raw Animation/relative/keyframe paths, finite arithmetic, Group/axis transforms, effective-easing precedence, out-of-order frames/bounds, atomic failures, and old presets/callables pass. Export is moved here from the brief's final-docs phase so the integration MVP is testable through its promised public import. Stop. |
| **3 — schedules/composition** | Add private reversal adapter/bounds support to `spring.py`; minimally update `scheduling.py`; add `tests/test_spring_scheduling.py`. | Stagger/Succession/Repeat, nested/repeated reversal, transformed scale bounds, natural/explicit duration scaling, delays/gaps, overlapping independent fades, lifetimes, late-child failures, existing Entry identity, odd/even final values, and shared-boundary continuity pass. Stop. |
| **4 — visual evidence/docs** | Add `examples/spring_motion/render.py`; update `docs/motion-graphics.md`, `docs/architecture.md`, `docs/api.md`, README usage, and a focused verification record. | Runnable 8–12 second Pillow/FFmpeg showcase: equal-distance linear/smooth/three numeric spring profiles, text, translated/scaled card, Group, network node; safe margins and terminal hold. Inspect low-resolution preview and storyboard first, including overshoot extrema and near-end frames. Stop for requested visual review. |
| **5 — final QA/review** | Extend only relevant tests/evidence and fix demonstrated spring issues; no unrelated formatting cleanup. | All package suites and lint; documented preexisting format baseline; representative existing motion demo; deterministic matching-time states at 24/30/60 fps; inspected and fully decoded preview; benchmark/evidence review; focused PR when requested. No next Premium Motion subsystem. |

Presets remain optional after the MVP. The comparison demo can use three explicit,
documented numeric configurations without creating `Spring.preset` or a public
registry. Add a preset API only in a separately agreed change backed by rendered
evidence. `animation.py`, `components.py`, `layout.py`, `renderer.py`, `export.py`,
and kit/agent production packages should not need modification for this design.

New numerical tests must use independent analytical identities/reference cases,
including exact critical response and underdamped first-peak timing/amplitude,
rather than reproducing the implementation. Dense deterministic grids help find
bugs but are not the proof of scale safety. Timeline/scheduler tests must include
adversarial cases between typical frame samples and real shrinking transitions;
endpoint-only and grow-only tests are insufficient.

For final QA, benchmark constructor/authoring cost separately from evaluation and
the actual renderer. Compare matched scenes/resolutions using fixed workload,
warm-up, repeated timings, and peak memory; report overhead relative to run-to-run
variation. Include repeated static-frame reuse and moving tracks. No performance
claim or acceptance percentage is established by Phase 0.

## Live baseline evidence

The commands below ran against the audited source before this plan was written.
The older review's aggregate count was not reused as a current baseline.

Environment: existing root `.venv`, Python **3.12.3**, pytest **9.1.1**, Ruff
**0.16.10**, Pillow **12.3.0**, uv **0.12.5**, FFmpeg **6.1.1**. Core, kit, and
agent imports resolved to this checkout's source directories.

Both literal requested commands, `uv run pytest -q` and
`uv run ruff check src tests examples`, initially exited **2** before running:
uv could not create a lock temporary file in read-only `/home/kingnit/.cache/uv`.
The reruns used a temporary cache and `--offline --no-sync` to use the installed
environment without dependency/network changes. This is an installed-environment
baseline, not evidence of a fresh dependency resolution or clean installation.

All commands ran from the repository root. For the table, `UV_CACHE_DIR` was
`/tmp/faceless-spring-phase0-uv`; test commands also set `MPLCONFIGDIR` to
`/tmp/faceless-spring-phase0-mpl`. Full reproductions:

```bash
UV_CACHE_DIR=/tmp/faceless-spring-phase0-uv MPLCONFIGDIR=/tmp/faceless-spring-phase0-mpl uv run --offline --no-sync pytest -q
UV_CACHE_DIR=/tmp/faceless-spring-phase0-uv uv run --offline --no-sync ruff check src tests examples
UV_CACHE_DIR=/tmp/faceless-spring-phase0-uv uv run --offline --no-sync ruff format --check src tests examples
UV_CACHE_DIR=/tmp/faceless-spring-phase0-uv MPLCONFIGDIR=/tmp/faceless-spring-phase0-mpl uv run --offline --no-sync pytest -q facelesschamp-kit/tests
UV_CACHE_DIR=/tmp/faceless-spring-phase0-uv MPLCONFIGDIR=/tmp/faceless-spring-phase0-mpl uv run --offline --no-sync pytest -q facelesschamp-agent/tests
UV_CACHE_DIR=/tmp/faceless-spring-phase0-uv uv run --offline --no-sync ruff check facelesschamp-kit/src facelesschamp-kit/tests facelesschamp-agent/src facelesschamp-agent/tests
```

| Check | Exit | Observed result |
| --- | --- | --- |
| Core pytest | 0 | **730 passed, 2 skipped in 149.02s** |
| Kit pytest, separate invocation | 0 | **255 passed in 101.37s** |
| Agent pytest, separate invocation | 0 | **41 passed in 92.57s** |
| Core Ruff check (`src tests examples`) | 0 | **All checks passed!** |
| Kit/agent Ruff check | 0 | **All checks passed!** |
| Core Ruff format, check only | 1 | **4 files would be reformatted, 105 files already formatted** |
| `git diff --check`, before adding this plan | 0 | No whitespace errors. |

Total executed test cases: **1026 passed, 2 skipped** across three separate suite
invocations. The two core skips correspond to opt-in Chromium integration in
`tests/test_playground.py:278` and `tests/test_web.py:76`, gated by
`FC_WEB_BROWSER_TESTS=1`. Source inspection confirmed those gates; this audit did
not enable browser integration or run every training-project suite. Tests used
independent processes to avoid similarly named downstream test-module collisions.
Suite runtimes overlapped and are not standalone performance benchmarks.

Existing format failures, left unchanged:

- `examples/chesschamp/showcase.py`
- `src/faceless_champ/layout.py`
- `src/faceless_champ/surfaces.py`
- `tests/test_surfaces.py`

No spring preview, solver benchmark, or new numerical verification was run during
Phase 0. The following work was performed after explicit Phase 1 approval.

## Phase 1 implementation and verification

Implemented only:

- `src/faceless_champ/spring.py`: frozen, slotted `Spring`, validated settings,
  all three analytical regimes, cached coefficients/horizon/progress bounds,
  exact endpoint returns, and deterministic arbitrary-progress evaluation.
- `tests/test_spring.py`: independent critical/distinct-root solutions,
  underdamped extrema/crossings, 80-digit ODE references, explicit series-error
  bounds, parameter corners, strict validation, tail certification, retiming
  equivalence, shuffled evaluation, and immutable copy/serialization checks.
- This plan: implementation notes and current evidence.

Phase 1 import and standalone use:

```python
from faceless_champ.spring import Spring

bounce = Spring(stiffness=1, damping=1.2, mass=1)
assert bounce(0) == 0
assert bounce(1) == 1
print(bounce(0.1))  # 1.0933035373...: normalized overshoot
```

At the Phase 1 stop, `Spring` was not yet exported from the root package.
Timeline property safety, Group/scale certification, scheduler reversal adapters,
and render examples were still pending. Phase 2 integration is recorded below.

The approved parameter domain is retained: each input in `[1e-6, 1e6]`, damping
ratio in `[0.02, 100]`, and horizon at most `1e5`. Type validation uses real
numbers (including Fraction), excluding booleans, strings, complex, and nonfinite
values; float-conversion overflow raises a clear numeric-domain error.

Two numerical refinements were necessary and are covered by regression tests:

1. The original loose overdamped envelope changes the normalized horizon by
   `O(sqrt(zeta-1))` near critical damping. Instead, certify the exact positive,
   monotone overdamped error and velocity using the already stable root formula:
   for `E=E(d*S)`, displacement is `(1+b*S*E)*exp(-b*S)` and normalized speed is
   `S*S*E*exp(-b*S)`. With `S>=2/b`, both certification criteria decrease;
   `E(d*S)` is positive and nonincreasing. Their critical limit matches the
   critical bound without a broad damping-regime approximation band.
2. Use half the public displacement/speed thresholds for horizon certification
   to reserve rounding headroom. Solving directly to the published threshold
   produced a returned critical displacement of `1.0000000827e-9`, slightly
   outside `1e-9`. The public limits remain `1e-9` and `1e-7`.

Near the origin, a degree-eight response polynomial is used only for
`s*max(1,zeta)<=0.01`; it is a fixed analytical limit, not frame integration.
Its progress and derivative truncation bounds are checked separately against an
80-digit ODE series. `sinc` and exponential-average regularization handle the
repeated-root limit; `expm1` and a half-angle identity reduce cancellation when
evaluating progress outside the origin branch.

Validation on 2026-10-15, existing root environment, no sync/network changes:

```bash
UV_CACHE_DIR=/tmp/faceless-spring-phase1-uv MPLCONFIGDIR=/tmp/faceless-spring-phase1-mpl uv run --offline --no-sync pytest -q tests/test_spring.py tests/test_animations.py tests/test_motion_graphics.py tests/test_engine.py tests/test_timed_scene.py tests/test_groups_layout.py --tb=short
UV_CACHE_DIR=/tmp/faceless-spring-phase1-uv uv run --offline --no-sync ruff check src tests examples
UV_CACHE_DIR=/tmp/faceless-spring-phase1-uv uv run --offline --no-sync ruff format --check src/faceless_champ/spring.py tests/test_spring.py
```

Result: **429 passed in 5.14s**, including **297 kernel cases** and **132 existing
motion/scene/Group cases**. Root Ruff check passed; both new Python files passed
format checking. The four Phase 0 formatting failures remain outside this change.
The full core and downstream suites were not rerun in this isolated-kernel phase.

An additional deterministic development sweep (seed 6401) evaluated **274,097
samples across 600 logarithmically distributed damping ratios**, including
analytical extrema. All outputs were finite and within cached progress bounds;
maximum observed terminal displacement was `5.0000004137e-10` and normalized
speed `1.12690785096e-8`. A smaller seeded logarithmic sweep is retained in the
tests. This is numerical evidence, not a proof based on a frame grid or a renderer
performance benchmark.

Numerical examples, `stiffness=mass=1`:

| Damping / regime | `p(0.05)` | `p(0.1)` | `p(0.2)` | Dimensionless horizon S |
| --- | --- | --- | --- | --- |
| `1.2`, underdamped | 0.8033787530 | 1.0933035373 | 0.9915348187 | 41.1023349546 |
| `2`, critical | 0.3492909774 | 0.7056831840 | 0.9572279975 | 24.6614009727 |
| `2.5`, overdamped | 0.5538984771 | 0.8478820647 | 0.9826322024 | 43.4081901799 |

Every row has exact `p(0)=0` and `p(1)=1`. Horizon retiming explains why these
normalized samples do not imply comparisons of physical settling speed.
No renderer, timeline, scheduler, root export, or dependency changes were made
during Phase 1; no spring rendering/performance claim was established at that stop.

## Phase 2 track integration

Implemented after explicit Phase 2 approval:

- `timeline.py`: prepare existing Tracks as before, then validate recognized
  Spring tracks before publishing the play batch or auto-adding any components.
- `__init__.py`: export the existing `Spring` class from the package root and
  add it to `__all__`. No second Spring class, Track type, or animation system.
- `tests/test_spring_timeline.py`: public API, resolved/relative/keyframed
  trajectories, overshoot safety, finite arithmetic/time intervals, atomic
  failure, Groups, bounds, CPU frames, and ordinary-callable compatibility.
- `spring.py`: module description updated for the now-available integration;
  the numerical kernel is unchanged.

Public use now works through the established API:

```python
from faceless_champ import Animation, Canvas, FadeIn, Rectangle, Scene, Spring

scene = Scene(Canvas(240, 140))
card = Rectangle(width=60, height=40, position=(40, 60), scale=0.8)
scene.play(
    Animation(card, {"position": (180, 60), "scale": 1}, rate_func=Spring()),
    FadeIn(card),
    run_time=0.75,
)
```

The animation-level spring leaves FadeIn on conventional easing. An outer
`rate_func=Spring()` applies to the entire batch, so that same mixed-property
batch would intentionally reject. Play-level overrides still take precedence
over animation-level easing, including the existing treatment of falsy callables.
Unrecognized user callables retain their previous contract.

Certified spring properties are exactly `position`, `rotation`, `scale`,
`scale_x`, and `scale_y`. Unsupported fields reject for every damping regime,
including bounded no-op tracks and custom channels. RGB/alpha, fraction, reveal,
progress, wipe/clip, dimensions, masks, chart data, numeric values, and map-domain
properties remain outside the spring allowlist. Whole component/Group transforms
remain available through their existing fields. Raw Spring target/start/keyframe
coordinates must be real numbers; numeric strings are rejected before sampling.

The validator operates on resolved starts and **every adjacent keyframe pair**.
It uses the kernel's global analytical progress range, enlarging the underdamped
upper range outward by 32 float ulps for evaluation roundoff. Forward progress
has lower bound zero; critical/overdamped evaluation stays within `[0,1]`.
For a fixed finite difference, the existing floating-point multiply/add mapping
is monotone in progress. Evaluating that mapping at the progress bounds therefore
accounts for its rounded arithmetic without inventing a downward epsilon at an
exactly valid growing start of `0.001`. Differences, products, and sums must be
finite; each scale bound must remain at or above `0.001`.

This can reject a near-boundary scale transition that cannot be certified under
the current interpolation formula, even with critical damping. For example,
`2 + (0.001 - 2)*1` rounds slightly below `0.001`; failure is explicit rather
than silently adjusting the trajectory. A constant `0.001` or growing transition
from `0.001` remains accepted. Group validation certifies local transform tracks,
not global canvas containment, world matrix/resource bounds, or world minimum size.

Spring intervals also require a finite, representable end strictly after their
start; adding a tiny duration to a huge authoring cursor must not create a
zero-length effective interval, and duration addition must not overflow. The
existing one-second default, minimum positive run_time, cursor/Scene.at behavior,
exact Track endpoints, and hold semantics are unchanged for normal intervals.
These new checks apply only to recognized spring easing.

Regression evidence includes a scale trajectory whose endpoints are valid and
whose minimum across 30 fps samples is approximately `0.196737588761`, but whose
analytical peak produces scale `0.00099`. It rejects before publication. Other
tests cover hidden tiny keyframe segments, unsafe axis/Group scales, explicit and
timeline-resolved starts, finite endpoints whose interpolation overflows, and
preservation of existing Entry identities, tracks, hierarchy ownership, and cursor
when a later animation in a batch fails. Source objects and snapshots remain
unchanged during out-of-order Pillow frame and bounds sampling.

At the Phase 2 stop, scheduler reversal adapters, spring-specific nested schedule
certification, FPS export comparisons, showcases, and benchmarks remained pending.
No changes to the scheduler, Track/Entry sampling, renderer, export, components,
builders, or dependencies were needed during Phase 2. That phase did not claim
spring ping-pong composition was certified; Phase 3 evidence follows below.

Phase 2 verification on 2026-10-15 used the existing root environment with
`UV_CACHE_DIR=/tmp/faceless-spring-phase2-uv`; pytest also used
`MPLCONFIGDIR=/tmp/faceless-spring-phase2-mpl`. Commands, from the repository root:

```bash
UV_CACHE_DIR=/tmp/faceless-spring-phase2-uv MPLCONFIGDIR=/tmp/faceless-spring-phase2-mpl uv run --offline --no-sync pytest -q tests/test_spring_timeline.py tests/test_spring.py --tb=short
UV_CACHE_DIR=/tmp/faceless-spring-phase2-uv MPLCONFIGDIR=/tmp/faceless-spring-phase2-mpl uv run --offline --no-sync pytest -q --tb=short
UV_CACHE_DIR=/tmp/faceless-spring-phase2-uv MPLCONFIGDIR=/tmp/faceless-spring-phase2-mpl uv run --offline --no-sync pytest -q facelesschamp-kit/tests --tb=short
UV_CACHE_DIR=/tmp/faceless-spring-phase2-uv MPLCONFIGDIR=/tmp/faceless-spring-phase2-mpl uv run --offline --no-sync pytest -q facelesschamp-agent/tests --tb=short
UV_CACHE_DIR=/tmp/faceless-spring-phase2-uv uv run --offline --no-sync ruff check src tests examples facelesschamp-kit/src facelesschamp-kit/tests facelesschamp-agent/src facelesschamp-agent/tests
UV_CACHE_DIR=/tmp/faceless-spring-phase2-uv uv run --offline --no-sync ruff format --check src/faceless_champ/timeline.py src/faceless_champ/__init__.py src/faceless_champ/spring.py tests/test_spring.py tests/test_spring_timeline.py
git diff --check
```

| Check | Observed result |
| --- | --- |
| Focused kernel/track tests | **421 passed in 2.92s**: 297 kernel cases and 124 track integration cases |
| Full core suite | **1151 passed, 2 skipped in 141.82s** |
| Kit suite, separate invocation | **255 passed in 103.73s** |
| Agent suite, separate invocation | **41 passed in 91.77s** |
| Core and downstream Ruff check | **All checks passed!** |
| Format check on the five relevant Python files | **5 files already formatted** |
| Tracked and newly added file whitespace checks | Passed |

The three full suites total **1447 passed, 2 skipped**; the focused run is a subset
and is not added again. The four unrelated Phase 0 format failures remain
unchanged. Suite timings overlap and are not performance benchmarks. AST
comparison confirmed unchanged Track/Entry sampling; Git comparison confirmed
unchanged scheduler, renderer, exporter, components, builders, dependency files,
and downstream production packages. No new mandatory dependency or full spring
video render was introduced. Phase 2 is complete; stop before Phase 3.

## Phase 3 schedules and composition

Implemented after explicit Phase 3 approval:

- `spring.py`: private frozen/slotted `_ReversedSpring` and shared
  `_spring_progress_bounds` recognition. The mathematical Spring kernel, settings,
  horizon, endpoint policy, and public API are unchanged.
- `scheduling.py`: recognize spring reversal, canonicalize double reversal to the
  original kernel, and align terminal floating-point roundoff for spring tracks.
  Generic callables retain the original `1-f(1-u)` lambda behavior.
- `timeline.py`: consume the same certified bounds for forward and reversed
  spring easing, retaining every Phase 2 property/arithmetic/time-interval check.
- `tests/test_spring_scheduling.py`: 117 cases covering all damping regimes,
  Stagger/Succession/Repeat nesting, keyframes, retiming, boundaries, holds,
  independent fades, Group lifetimes, and atomic failures.

The reversal adapter evaluates exactly `1-spring(1-u)` in the open interval, with
the same exact 0/1 endpoints and progress validation as the forward callable. Its
cached interval is `[1-upper, 1-lower]` of the already padded forward bounds.
Underdamped reversed progress can therefore be negative. Copying/serialization
retains the base kernel and bounds. A second reversal returns the original kernel,
so nested Repeat cannot accumulate wrappers or numerical-bound padding.

Geometry validation runs on each reversed segment using those transformed bounds
and its swapped endpoints. For example, scale `0.1 -> 1 -> 0.1` is safe; applying
a fresh forward spring bound to the return would falsely reject it. Conversely,
growth `0.001 -> 2` is safe forward, while return interpolation can round below
`0.001`. The latter now rejects the complete ping-pong schedule before any track
is published. The same rules hold for axis scales and all damping regimes.

Decimal retiming exposed an existing finite-precision end condition: with three
traversals, duration `0.3`, delay `0.13`, and total run_time `0.6`, independent
offset/duration arithmetic could end the last track at `0.6000000000000001`.
Sampling the scene end then returned `9.999999995` instead of exact target `10`.
Ordinary spring play calls have the same subtraction issue at some absolute
start times. Preparation now stores each recognized spring interval as
`(start + requested_duration) - start`, ensuring its representable end subtracts
to exactly the stored duration. The scene cursor still advances by the requested
duration; generic tracks retain their previous arithmetic. For schedules, the
compiler also sets a terminal spring's duration to `scene_end - track.start`
when its computed end equals or exceeds the scene end by at most 16 ulps. This
uses the existing exact Track boundary return; it does not change frame sampling
or clamp easing. Earlier leaf ends are never extended into intentional holds.
Generic callable duration arithmetic and the established scene duration
calculation remain unchanged. Stored spring track durations can differ from the
requested input by clock roundoff; the input duration validation still runs first.
Nonfinite/zero-length intervals still reject.
Regression coverage includes 36 decimal combinations and a representable tiny
terminal hold near a large absolute clock.

Composition example using only existing APIs:

```python
from faceless_champ import Animation, Canvas, FadeIn, Rectangle, Repeat, Scene, Spring, Stagger

scene = Scene(Canvas(240, 140))
card = Rectangle(width=60, height=40, position=(40, 60), scale=0.8)
scene.add(card)
scene.play(Stagger(
    Repeat(
        Animation(card, {"position": (180, 60), "scale": 1}, rate_func=Spring()),
        cycles=2, ping_pong=True, duration=0.5,
    ),
    FadeIn(card),
    lag=0, duration=0.25,
))
```

The result lasts one second, returns the card's original transform after two
traversals, and holds opacity at one after its independent conventional fade.
An outer spring override still rejects a batch containing opacity. `Scene.at`
can author the same different-property overlap, preserving its existing cursor
semantics. Odd ping-pong counts finish at the forward target; forward-only repeats
still reset at their shared boundary. Delays/gaps remain holds, and explicit
schedule run_time scales all traversals, durations, lags, and delays.

Late failures in a nested child, collision, reversed keyframe ordering, scale
check, or overflowing return interval discard the copied trial. Tests preserve
existing Entry identities, fields, tracks, hierarchy links, ownership, cursor,
and source objects on failure; successful subsequent scheduling also preserves
existing reversed curves through copying. Group removal still checks descendants
and renderer visibility follows their lifetimes. Out-of-order CPU frames for
spring/fade compositions remain reproducible.

No Track/Entry sampling, renderer, export, component/builder, dependency, or root
API changes were needed in Phase 3. No showcase, FPS-export comparison, benchmark,
or next Premium Motion subsystem was started.

Phase 3 verification on 2026-10-15 used the existing root environment without
sync/network changes. Final commands, from the repository root:

```bash
UV_CACHE_DIR=/tmp/faceless-spring-phase3-uv MPLCONFIGDIR=/tmp/faceless-spring-phase3-mpl uv run --offline --no-sync pytest -q tests/test_spring_scheduling.py tests/test_spring.py tests/test_spring_timeline.py tests/test_motion_graphics.py tests/test_timed_scene.py --tb=short
UV_CACHE_DIR=/tmp/faceless-spring-phase3-uv MPLCONFIGDIR=/tmp/faceless-spring-phase3-mpl uv run --offline --no-sync pytest -q --tb=short
UV_CACHE_DIR=/tmp/faceless-spring-phase3-uv MPLCONFIGDIR=/tmp/faceless-spring-phase3-mpl uv run --offline --no-sync pytest -q facelesschamp-kit/tests --tb=short
UV_CACHE_DIR=/tmp/faceless-spring-phase3-uv MPLCONFIGDIR=/tmp/faceless-spring-phase3-mpl uv run --offline --no-sync pytest -q facelesschamp-agent/tests --tb=short
UV_CACHE_DIR=/tmp/faceless-spring-phase3-uv uv run --offline --no-sync ruff check src tests examples facelesschamp-kit/src facelesschamp-kit/tests facelesschamp-agent/src facelesschamp-agent/tests
UV_CACHE_DIR=/tmp/faceless-spring-phase3-uv uv run --offline --no-sync ruff format --check src/faceless_champ/spring.py src/faceless_champ/timeline.py src/faceless_champ/scheduling.py tests/test_spring.py tests/test_spring_timeline.py tests/test_spring_scheduling.py
git diff --check
```

| Check | Final observed result |
| --- | --- |
| Focused kernel/track/schedule/motion/timed-scene tests | **580 passed in 5.40s**, including 117 new Phase 3 cases |
| Full core suite | **1268 passed, 2 skipped in 177.88s** |
| Kit suite, separate invocation | **255 passed in 130.85s** |
| Agent suite, separate invocation | **41 passed in 120.81s** |
| Core and downstream Ruff check | **All checks passed!** |
| Format check on six relevant Python files | **6 files already formatted** |
| Tracked/new-file whitespace and plan code-fence checks | Passed |

The three full suites total **1564 passed, 2 skipped**; the focused subset is not
added again. Earlier successful suite runs preceded the final endpoint fixes;
the results above are the final reruns after those fixes. Existing unrelated
format failures are unchanged, and overlapping suite timings are not benchmarks.
The documented one-second composition and decimal endpoint example were executed
successfully. AST comparison confirms Track/Entry sampling remains unchanged;
renderer/export, components/builders, dependency files, and downstream production
packages match the audited HEAD. Phase 3 is complete; stop before Phase 4.

## Phase 4 implementation and visual evidence

Completed on 2026-10-15 in the same working tree, following explicit approval to
start and complete Phase 4. Production modules, dependencies, renderer/export,
and earlier examples were not changed during this phase.

- Added `examples/spring_motion/render.py`: a self-contained, silent, 10-second
  public-API showcase with three shots. Equal-distance linear/smooth/gentle/snappy/
  bouncy comparisons share a 160-pixel move and 2.6-second duration. Explicit
  `(stiffness,damping,mass)` configurations `(100,20,1)`, `(100,25,1)`, and
  `(100,10,1)` show critical, overdamped, and underdamped behavior. Text motion
  with independent fade, card translate/scale/rotation, a three-card Group, and
  staggered network nodes use the existing track/schedule/render paths. There
  is no new preset API or animation framework.
- The CLI defaults to a 960×540, 30-fps preview. `--storyboard-only` and `--frames`
  use the public storyboard API; `--check` runs a sampled layout audit;
  `--quality high` optionally selects 1920×1080/2× antialiasing. Overwrite remains
  explicit. All three shots include terminal holds of at least 0.6 seconds.
- Added four example regressions in `tests/test_spring_example.py`: equal travel,
  timing/holds; sampled safe margins; visible text/connections and actual nested
  card membership; storyboard CLI output/overwrite protection.
- Updated `docs/motion-graphics.md`, `docs/api.md`, `docs/architecture.md`, and
  README with the public constructor, coefficient/damping-ratio ranges,
  finite-duration retiming, equal-ratio equivalence, endpoint tolerances,
  supported transforms, continuous local-scale safety, unsupported properties,
  separate fades, keyframes/repeats, FPS invariance, configuration examples,
  preview commands, and v1 limitations. The two new guide snippets executed.
  The root `Spring` export was already delivered in Phase 2.
- Added [human-readable](../spring-motion-verification.md) and
  [machine-readable](../spring-motion-verification.json) verification records
  with artifact hashes, sample timestamps, results, and explicit pending scope.

The source storyboard was rendered and inspected before encoding. Inspection
caught transparent fade endpoints and an underspaced footer; both were corrected
in the example before the final preview. The final MP4 is exactly 10.000 seconds,
960×540, 30 fps, 300 H.264/yuv420p frames, 128,922 bytes, with no audio. FFprobe and
complete FFmpeg decode passed. Twelve decoded MP4 frames matched fresh source
frames at their exact `index/30` timestamps with mean absolute RGB errors of
0.8541–1.0807 on a 0–255 scale. Source/encoded contact sheets, six analytical
first-peak stills, and a native-size transform frame were inspected. No unexpected
clipping, scale inversion, overshoot collision, or terminal jump was observed.

The layout audit checked 17,759 bounds at 301 timestamps per shot and retained at
least 23 pixels of canvas clearance. Independent first-extremum witnesses at
0.641225s, 4.732387s, and 7.367677/7.497677/7.627677/7.757677s also remained safe.
The largest immediately-before/end coordinate change was 8.000001e-8; exact ends
equaled targets and source frames throughout each shot's final hold agreed.
Sampled world bounds supplement, rather than replace, the continuous local-scale
proof implemented in earlier phases.

Final focused checks used the existing offline environment and task-specific
`UV_CACHE_DIR`/`MPLCONFIGDIR`: **4 example cases passed in 40.85s** and **588 spring,
motion-graphics, and narration-preview cases passed in 8.48s** (**592 total**).
Ruff passed across core/kit/agent source and tests plus examples. Nine touched
Python files passed formatting; tracked/new-file whitespace, twelve spring doc
links, and evidence JSON checks passed. The four preexisting formatter failures
remain untouched. Full package suites last ran in Phase 3 and are not recounted
as a Phase 4 run.

Artifacts are local under ignored `output/spring_motion/`: `preview.mp4`,
`storyboard/storyboard.png`, `encoded/contact-sheet.png`,
`peak-contact-sheet.png`, and six native-size peak stills. The high-resolution
export was intentionally not run (`full_preview_verified: true`,
`full_export_verified: false`). Phase 4 is complete. User visual approval and
Phase 5 release QA, matching-time 24/30/60-fps export checks, benchmarks, review,
and any requested PR remain pending; no later motion subsystem has begun.

## Phase 5 final QA and review

Completed the authorized local QA on 2026-10-15. The user's request to complete
Phase 5 followed the inspected Phase 4 preview/handoff. This phase changed no
production source, dependencies, renderer, or preexisting examples.

- Full core: **1,272 passed, 2 skipped in 129.88s**; six newly added release cases
  subsequently **passed in 17.01s**. Full kit: **255 passed in 78.25s**. Full agent:
  **41 passed in 75.80s**. Unique total: **1,574 passed, 2 existing opt-in Chromium
  skips**. Separate package collection avoids duplicate test-module names.
- Added `examples/spring_motion/verify.py` and `tests/test_spring_release.py`.
  All three damping regimes, cache disabled/enabled, and forward/reverse/shuffled
  seek order produce identical state dictionaries and pixel hashes at 17 matching
  timestamps following 18 complete 24/30/60-fps source workloads. Authoring
  objects/snapshots are unchanged. This uses the approved direct-timeline option;
  it does not claim three encoded FPS exports.
- Added `examples/spring_motion/benchmark.py`: separate constructor/authoring/
  evaluation timings; warmed interleaved static/smooth/spring rendering; an
  identical-trajectory precomputed control; isolated Python/native memory evidence.
  Final 180-frame, seven-trial medians were static **1.111**, smooth **3.560**,
  spring **4.248**, and control **3.466 ms/frame** at 960×540/AA1 with 12 objects.
  A spring evaluation measured **3.826 microseconds**. The local absolute overhead
  is small relative to a 30-fps frame budget, but sparse-scene point overhead is
  **19.3%** and trial variance is material. Raw exploratory/final trials are
  preserved; no universal negligible-overhead claim is made. Workers reported
  49,684 KiB whole-process peak RSS; smooth/spring Python peaks were
  364,352/364,152 bytes. Timings exclude tracemalloc and FFmpeg encoding.
- Completed the existing motion graphics demo at **480×270, 24 fps, AA1**, all
  **18 seconds / 432 silent H.264 frames**; FFprobe, full decode, six decoded/source
  comparisons, and source/encoded storyboard inspection passed. The original
  960×540/AA2 attempt was interrupted and is not counted as verified. The Spring
  960×540 preview passed a fresh full decode and retained its recorded hashes.
- Numerical/safety/rollback review found no actionable defect. Independent Decimal
  ODE/closed-form/extremum references, domain corners, near-critical limits,
  cancellation guards, continuous overshoot bounds, reversed metadata, clock
  endpoints, and failure publication paths were reviewed. `Track` and `Entry`
  ASTs match the audited base; generic callable behavior stays covered. Existing
  rollback cases preserve IDs, ownership, hierarchy, values, and cursor on failures.
- Ruff passed across core/kit/agent source/tests and examples. All 12 feature
  Python files passed formatting. The full formatter still reports the same four
  baseline files; no unrelated formatting was changed. Whitespace, evidence JSON,
  documentation links, and source/artifact fingerprints were checked.
- Offline wheel/sdist builds and an isolated installed-wheel three-regime
  ping-pong/CPU-frame smoke passed, reusing the installed third-party runtime.
  Source distributions include the example verification and benchmark scripts.

See [the full verification report](../spring-motion-verification.md#phase-5-final-checks)
and [release JSON](../spring-motion-release.json) for methods, raw trials, source
hashes, artifact paths, limitations, and reproducible commands. The dedicated
`codex/spring-motion-v1` review branch targets `facelesschamp-agent`, the verified
base, to exclude earlier unrelated commits. After automatic approval review
rejected publication, the user explicitly selected **Keep changes local**. The
[prepared PR description](../spring-motion-pr.md) is retained for review; no push,
GitHub PR, merge, or later Premium Motion subsystem was performed.
