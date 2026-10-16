# Spring Motion v1 architecture reference

This preserves the architecture proposal. Prior implementation/demo evidence was
retired during the premium reference reset; consult current source and tests for
implemented behavior. This document does not establish current media verification.

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
| **4 — visual evidence/docs** | Add a local draft scene; update `docs/motion-graphics.md`, `docs/architecture.md`, `docs/api.md`, README usage, and a focused verification record. | Runnable 8–12 second Pillow/FFmpeg showcase: equal-distance linear/smooth/three numeric spring profiles, text, translated/scaled card, Group, network node; safe margins and terminal hold. Inspect low-resolution preview and storyboard first, including overshoot extrema and near-end frames. Stop for requested visual review. |
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
