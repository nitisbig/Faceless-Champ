
Scope: **animated visual properties, animation composition and loops, masks and reveals, and progress/indicator components.**

Inspect the latest repository, `AGENTS.md`, documentation, and existing tests before editing. Build on the current `Component`, `Animation`, `Scene`, `Group`, `PillowRenderer`, and caching architecture. Preserve existing public APIs and rendering behavior.

**1. Animated visual properties**

Extend the animation system to support:

- Fill, stroke, and text colors, including alpha.
- Shape width, height, stroke width, and corner radius.
- Independent X/Y scaling while retaining existing uniform `scale` behavior.
- Chainable animation builders consistent with the current API.

Introduce explicit validation and interpolation for each property type. Define color interpolation and transparent-color behavior clearly. Handle nested group transforms correctly; nonuniform scaling combined with rotation requires proper affine transformation.

Dynamic geometry and styling must update layout/render bounds and invalidate relevant caches. Keep memory bounded rather than caching every intermediate animation frame.

**2. Animation composition and loops**

Add reusable scheduling helpers such as:

- `Stagger`: animations with delayed starts.
- `Succession`: animations played sequentially.
- `Repeat`: finite repetition, with an optional ping-pong mode.

These names are proposed; adapt them to repository conventions without conflicting with existing scene compositions.

Support nested scheduling and clearly document delay, duration, total `run_time`, cycle boundaries, and final-state behavior. Keep the scene cursor accurate and preserve `Scene.at()` timing.

Validate conflicting property tracks before modifying the scene. Repetition must have a finite cycle count or explicit duration.

**3. Masks and reveals**

Add reusable alpha masking for components and groups:

- Rectangular and circular masks.
- Shape-based masks where practical.
- Directional wipe/reveal animations.
- Animatable mask position and dimensions.

Define mask coordinates explicitly, preferably local to the masked object by default. Ensure masks behave correctly with nested groups, transforms, opacity, transparent backgrounds, and overlapping objects.

Apply masks to the complete intended target. Reuse the same masking infrastructure for reveals rather than creating separate rendering implementations for every effect.

**4. Progress and indicator components**

Implement reusable, configurable components:

- `ProgressBar`
- `ProgressRing`
- `Gauge`
- `Countdown`
- `LoadingDots`
- `Checkmark`

Provide consistent styling, placement, group compatibility, and animation APIs. For example, progress components should support an equivalent of `.animate.progress_to(value)`.

Define valid ranges and endpoint behavior. Support configurable colors, dimensions, stroke thickness, and optional labels where appropriate. Reuse existing `Number`, text, shapes, and grouping behavior when suitable.

**Implementation requirements**

- Put reusable behavior in the main library, not example-specific workarounds.
- Preserve deterministic frame evaluation: requesting frame `t` must produce the same result regardless of previous frame requests.
- Preserve existing scene snapshots, member lifetimes, caption/GIF clocks, and source-clock rendering.
- Keep ordinary usage lightweight and suitable for CPU rendering on a low-end laptop.
- Avoid mandatory heavyweight dependencies.
- Keep unrelated features outside this milestone.
- Make routine implementation decisions autonomously and document material tradeoffs.

**Validation and deliverables**

1. Add meaningful tests for interpolation, endpoints, scheduler timing, conflicts, nested groups, masking, transparency, cache invalidation, and out-of-order frame sampling.
2. Run the full existing test suite and repository lint/format checks.
3. Create a self-contained showcase demonstrating every new feature with clean typography, readable spacing, and smooth motion.
4. Render the showcase, inspect representative frames, and verify video dimensions, frame rate, duration, and full decoding.
5. Update public exports, API documentation, authoring guidance, and verification notes.
6. Build and check the installable package.

Complete the implementation and verification before reporting back. Summarize the new APIs, usage examples, checks performed, and any remaining limitations.