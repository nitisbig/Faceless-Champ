> Architecture reference. Prior baseline images and media evidence were retired
> during the premium reference reset; use current source and tests for behavior.

# ADR: Premium effects and compositing

Status: **approved; Phase 0 audit complete**. Phase 2A implementation was
authorized by the user's subsequent "approved. next complete phase" instruction.
Date: 2026-10-16, Asia/Kathmandu. Scope: System 02, Phase 0 only.

## Decision and approval boundary

Implement gradients as immutable paint descriptions consumed by one-shot surface
factories. A surface remains an ordinary snapshotted `Image`. Keep the existing
Pillow renderer, timeline, Spring restrictions, masking, layout and exporter intact
in Phase 2A. Design runtime effects separately, and implement them only after their
own approval gates.

This ADR and its baseline evidence are the Phase 0 deliverable. No production,
test, example, dependency or package code is changed. The supplied System 02 plan
was already untracked and is left intact. The audit stays on the existing `master`
branch; no implementation branch, commit, push or PR is created during this
documentation-only phase. After approval, use `codex/premium-effects-2a` for 2A.

Audited revision: `e1312dd409da072e38f308095491418836e9699d`, containing Spring
implementation `bab707894d4c171bd8cb939f91bbe854c29cdf83`. This establishes the
prerequisite at a known local revision; it does not assert a remote release or
merge state. Runtime inspected: Python 3.12.3, Pillow 12.3.0, core 0.1.5,
kit 0.1.0rc7, agent 0.1.0rc2. No downloads or dependency installation occurred.

## Existing architecture and reusable functionality

| Source | Verified behavior and reuse decision |
| --- | --- |
| `src/faceless_champ/surfaces.py` | Frozen `ShadowStyle(color, blur, offset)` validates colors/finite geometry. `_shadow_padding` is `ceil(3*blur + max(abs(dx), abs(dy)))`. `card_surface` rasterizes at 2x design size; allocation includes shadow clearance. `card_content_bounds` uses the same inset plus content padding. Reuse these layout contracts. |
| `components.py: Image.from_source` | Pillow input becomes immutable encoded PNG bytes; byte input is captured as immutable bytes. `trim=False` preserves allocation. `_image` in surfaces reserves width/height/position/anchor/fit/trim, then returns an ordinary Image. Reuse, including existing component options. |
| `timeline.py: Scene._prepare_add`, `Scene.add`, `Entry.state_at`, `Track.value_at` | Addition validates ownership, deep-copies component descriptions and records initial state. Tracks evaluate by absolute source time, without mutating authoring objects. Keep these contracts. A changed gradient requires a new surface before scene addition. |
| `motion.py`, `layout.py` | Reuse finite/validated color conventions, affine matrix multiplication/inverse/point helpers, Bounds, fixed Group pivot, transformed corner bounds, and `Scene.bounds_at`. Logical layout bounds and future effect ink bounds must remain distinct. |
| `renderer.py: PillowRenderer._scene` | Fast path sorts siblings locally by z-index, flattens groups, reuses sprites, transforms them and composites RGBA. Group subtrees retain their parent stacking position; a child's z-index cannot cross unrelated parent siblings. Keep this path unchanged in 2A. |
| `renderer.py: PillowRenderer._affine_scene` | Any attached mask, non-default clip or nonuniform scale selects the affine path for the entire scene. Each visited entry allocates a canvas-sized RGBA layer; masks allocate canvas-sized L images. Masks clip complete group subtrees. Reuse semantics, **not this allocation pattern**, for new runtime filters. |
| `renderer.py: _sprite`, `_image`, `managed_renderer`, `close` | Reuse sprite production, image/GIF decoding, source ages, backend frame keys, caller-image copy protection and owned-renderer cleanup. Do not add effect logic to individual clip implementations in 2A. |
| `flow/drawing.py: draw_frame`, `composite_center` | Existing integer-origin, padded per-element ROI composition is a useful design precedent for 2B. Flow's label cache has a byte budget. `capsule_sprite` is a small purpose-specific blurred/glossy sprite with a 128-entry global LRU; it is not a general gradient/shadow API. Leave it untouched. |
| `os_ui/drawing.py` | Window shadows and four-entry surface caches already exist, but their shadows use full-viewport RGBA filtering. These are specialized renderer internals, not reusable safe general effect passes. No OS renderer rewrite is included. |
| `arch/clip.py`, `arch/rendering.py` | ArchChamp has deterministic source-time frame keys and renderer-owned VTK sessions. Keep live sessions out of styles and scene snapshots. Effects on a future Arch target could operate only on its finished 2D RGBA viewport, never on meshes/actors. |
| `preview.py`, `export.py` | Existing still/storyboard helpers, ranged export, renderer protocol and streamed FFmpeg encoding are sufficient. Keep straight RGBA at the renderer boundary; MP4 output is opaque RGB/H.264. |

The relevant existing regression coverage is in `test_surfaces.py`,
`test_image_sources.py`, `test_groups_layout.py`, `test_motion_graphics.py`,
`test_spring_release.py`, `test_flow.py`, `test_arch.py`, `test_web.py`, and export
tests. Existing docs explicitly describe member-wise group opacity and the
canvas-area cost of masked rendering. No global effect plugin registry is needed.

### Current cache and lifetime contract

* Scene frames: one last frame per scene, 64 MiB byte-bounded LRU, keyed by canvas,
  output dimensions, visible component identities and evaluated state, ancestor
  transforms/state, captions, GIF age and clip-specific frame keys. Return copies.
* Sprites: `(component snapshot, factor, GIF frame index)`. Dynamic style/reveal/
  draw sprites bypass retention. Charts/maps render from evaluated state;
  Flow/HTML/OS/Chess/prepared playback use their own frame producers.
* Decoded images: resolved file path or immutable encoded bytes. Identical source
  bytes share decoded assets, while distinct component snapshots can still retain
  distinct sprites. Replacing a file requires a fresh renderer.
* Captions and code: separate 32 MiB byte budgets; caption layouts have a count
  cap. Arch sessions: four by default, closed on eviction and renderer close.
* `_images`, `_sprites`, `_fonts` and `_equations` are renderer-local dictionaries,
  **not byte-bounded LRUs**. GIFs decode all frames. A bounded scene-frame cache
  does not bound total renderer memory. Avoid describing the whole renderer as
  globally memory-bounded.
* `close()` clears the dictionaries/LRUs and closes Arch sessions; supplied
  renderers remain caller-owned. Releasing references does not guarantee the
  native allocator immediately returns all RSS to the OS.

## Phase 2A public API proposal

The following names and signatures are proposals, not implemented imports:

```python
from faceless_champ import (
    Bounds, GradientStop, LinearGradient, RadialGradient,
    ShadowStyle, card_surface, gradient_surface,
)

stops = (
    GradientStop(0.0, "#15182D"),
    GradientStop(0.55, "#3647A0"),
    GradientStop(1.0, "#62DDDB"),
)
linear = LinearGradient(stops=stops, angle=125)
radial = RadialGradient(stops=stops, center=(0.5, 0.4), radius=0.75)

card = card_surface(Bounds(200, 160, 1300, 840), fill=linear,
                    radius=44, shadow=ShadowStyle())
backdrop = gradient_surface(Bounds(0, 0, 1920, 1080), fill=radial)

# Existing call and default shadow geometry retain their current behavior.
legacy = card_surface(Bounds(200, 160, 1300, 840), fill="#FFFFFF",
                      shadow=ShadowStyle(blur=16, offset=(0, 12)))
```

* `GradientStop(offset: float, color: str)`; `LinearGradient(stops, angle=0)`;
  `RadialGradient(stops, center=(0.5, 0.5), radius=0.5)`: frozen dataclasses.
  Coerce stops/center to tuples, validate types and canonicalize numeric/color
  values once. No Pillow images, renderers or mutable buffers in descriptors.
* `card_surface(bounds, *, fill: str | LinearGradient | RadialGradient =
  "#FFFFFF", radius=44, shadow: ShadowStyle | None = None, **component_options)`.
  Preserve the existing string branch, defaults, signature behavior and reserved
  geometry checks. Gradient coordinates cover the **face**, excluding shadow
  clearance. Radius still clamps to half the smaller face dimension.
* `gradient_surface(bounds, *, fill: LinearGradient | RadialGradient,
  **component_options)` returns the rectangular, radius-zero, shadow-free version.
  No new background component or canvas fill schema. `dot_grid` is unchanged.
* Do not introduce another surface-shadow type, alter `ShadowStyle` fields,
  introduce spread/inset shadows, or add a generic `effects=` field in 2A.
* Both factories return Image. They work as ordinary siblings/backdrops inside
  Scene/Group/Sequence/Grid/Layer and with current masks, z-index and Spring
  transform tracks. Gradient or shadow parameters are static source pixels.
  Shape.fill, Text.color, ChartStyle, FlowTheme and Canvas.bg remain their current
  types. Kit blocks/themes and agent schemas wait for settled core APIs.

### Gradient math and coordinate decisions

1. Accept 2–64 strictly increasing stop offsets in `[0,1]`; reject coincident or
   decreasing stops instead of silently sorting or creating hard edges. Stops
   need not include 0/1: extend the nearest stop color outside their interval.
   Reject NaN/Inf and invalid color strings at construction.
2. `angle` is clockwise in the image plane: 0 degrees is left-to-right, 90 is
   top-to-bottom. Normalize finite angles modulo 360. Project the face rectangle
   onto `d=(cos(angle), sin(angle))`; map its minimum/maximum projections to 0/1.
   Sampling uses the first/last raster sample centers as the rectangle endpoints,
   so cardinal endpoint samples are exact. Rounded coverage can hide projected
   extreme corners; exact paint endpoints do not imply every rounded card exposes
   them as opaque pixels. A one-sample axis contributes zero
   extent; if both axes collapse, use the first stop color.
3. Radial center is normalized within the face rectangle, with each coordinate
   in `[0,1]`. Radius is a fraction of the smaller face dimension, **not output
   pixels and not an elliptical X/Y pair**. Require `1e-6 <= radius <= 16`.
   Compute normalized design-space distance from center, divide by radius, clamp
   to `[0,1]`. Own/ancestor nonuniform transforms may subsequently make it elliptical.
4. Interpolate **premultiplied, encoded-sRGB channels and alpha**, then unpremultiply
   once. This is not linear-light interpolation. Fully transparent sample RGB is
   canonical zero; exact stop/end colors refer to this normalized RGBA form.
   Preserve exact nonzero-alpha endpoints; quantize intermediate channels with
   deterministic nearest-integer rounding. Do not reuse the timeline's straight
   RGBA interpolation for gradient paint or change that existing animation rule.
5. Bounds/blur/offset/radius use authored design pixels; the radial center/radius
   above are explicitly normalized paint coordinates. Factories rasterize at 2x
   design resolution once, independently of output FPS/resolution/renderer AA.
   Rendering factor is `min(output_width*AA/canvas_width,
   output_height*AA/canvas_height)`. Do not multiply baked shadow blur by AA again.
6. Keep current rejection of allocations smaller than one design pixel, and
   allocations without positive space after shadow clearance. New gradient paths
   also require at least one raster sample in each face dimension. No arbitrary
   shapes, stroke gradients, conic gradients or extrapolating/repeating paint in 2A.

### Alpha, shadow and compatibility decisions

The existing shadow draws colored RGBA onto transparent black, blurs RGBA, then
draws the face directly over that image. The face replaces shadow pixels inside
its geometric coverage, including when the face fill is translucent. Consequently
the current card shadow is independent of face paint alpha and does not shine
through a translucent face. Preserve that convention.

An installed-Pillow probe of the existing filter pattern produces `(49,0,0,49)`
outside an opaque red rectangle. Correct straight RGBA there would retain red
255 with alpha 49. Compositing the former darkens the red twice. Black shadows
hide the RGB error. This is a verified existing limitation, not a new feature.

For **new gradient surfaces**, blur only the L-mode geometric coverage, offset in
design space, then colorize with constant shadow RGB and multiply shadow color
alpha once. Use a separate face coverage mask, independent of paint alpha. The
face replaces the shadow inside its coverage: combine premultiplied face and
shadow as `P = C*P_face + (1-C)*P_shadow` and
`A = C*A_face + (1-C)*A_shadow`, where C is geometric face coverage. Unpremultiply
for the returned RGBA image. Never multiply straight RGB by coverage and then
store it as straight RGBA. Sanitize RGB where alpha is zero.

**Approved compatibility choice:** keep legacy string-fill rasterization
pixel-identical under the same Pillow version, including existing colored-shadow
and translucent-face behavior. Apply the alpha-safe implementation to new gradient
paths and later runtime effects. A retroactive correction to legacy colored
shadows needs a separately approved change and new goldens; do not silently
repaint existing videos. A solid-color gradient with a colored shadow may therefore
differ from a legacy solid string card at shadow fringes. The existing limitation
must be documented rather than presented as fixed globally.

Filtering/resampling boundaries are explicit: new shadow filtering is alpha-only;
new general colored filtering in 2B is premultiplied; encode/store/return straight
RGBA. Installed Pillow 12.3 resize/affine operations internally convert RGBA to
premultiplied RGBa for non-nearest resampling. Verify pixel behavior across supported
Pillow versions in 2A instead of assuming the inspected version proves every
supported version. Do not change Sequence's current blend implementation in 2A.

### CPU, memory and cache design for 2A

Keep pure scalar gradient evaluation as a reference, separate from a private
bounded raster helper. Use Pillow native numeric/channel operations in tiles
(initially at most 64 rows), with precomputed axis coordinates and stop constants.
Use native one-dimensional expansion for cardinal linear cases. Avoid Python
per-pixel RGBA objects, full-frame float channel stacks, a prequantized 256-step
gradient before multi-stop interpolation, and dependency on transitive NumPy.
The tiled kernel must match the scalar reference within one 8-bit channel level;
exact endpoints/stops are handled explicitly. Profile construction separately from
frame replay. Detect stop intervals too narrow for the native field precision and
fall back to reference sampling for affected samples instead of collapsing stops.
This is an implementation strategy to prove in 2A, not a claim of
an already-built optimized gradient kernel.

Proposed initial limits for **new gradient allocations only**: maximum raster
side 8192, maximum 8,388,608 raster pixels (one RGBA plane is 32 MiB), and a
conservative 192 MiB per-call working-set estimate including coverage, shadow,
tile scratch and PNG encoding copies. Reject over-budget inputs with an actionable
ValueError **before allocation**. The default 1920x1080 design at 2x fits; a
3840x2160 design at 2x does not. A 4K output can still render an ordinary 1080p
design. Large-design/high-magnification quality is a known limit, not a promise of
resolution-independent vector paint. If measurements cannot meet these limits,
reduce simultaneously live planes or revise this proposal before shipping.

No global factory cache or per-frame gradient generation. The factory owns and
releases scratch images; only encoded Image source bytes survive. The existing
renderer decodes/caches these through its normal Image pipeline. Reuse a surface
by moving the component/group, not by constructing it per frame. New descriptor,
new surface, new scene snapshot is the authoring invalidation contract. Existing
scene signatures need no new fields in 2A. Do not add dormant effect machinery
to the no-effect render path.

## Future runtime effects: design reservations, not 2A implementation

### Minimal API and fixed order for 2B

Provisional descriptors are `DropShadow(style=ShadowStyle(...))`,
`OuterGlow(color=..., blur=...)`, `GaussianBlur(radius=...)` and a frozen
`EffectStack(shadow=None, glow=None, blur=None)`, attached with a future
`effects=EffectStack(...)` Component/Group option. One optional operation of each
kind keeps order explicit; do not introduce a general plugin/dispatch framework
or reorderable arbitrary filter graph. Numeric limits and resource errors must
be validated before rendering.

For a supported leaf:

1. Rasterize evaluated content locally, including reveal/draw.
2. Apply optional GaussianBlur to content in premultiplied form.
3. Derive shadow/glow from that filtered content alpha. Composite **shadow below
   glow below content**; neither operation captures canvas/background pixels.
4. Apply the target's own mask and wipe/clip to the entire resulting layer.
5. Multiply own and inherited opacity once, apply target/ancestor transforms,
   then source-over composite at the target's existing sibling z position.

Thus effects are local and transform with the target, including rotated offsets
and elliptical blur under anisotropic scale. The target's mask clips its halo.
To cast an exterior shadow from a masked silhouette, put the mask on an inner
group and the effect on an unmasked outer group. Ancestor masks still clip the
complete descendant result. Cropping to the viewport is the final composition
operation, not a pre-filter operation.

For a Group, first compose active descendants in group-local coordinates with
their own transforms/effects/masks. Child masks constrain the silhouette from
which group effects are derived; the group's own mask clips its finished effects.
**Keep existing member-opacity semantics:** pass group/ancestor opacity down to
leaves, then derive group effects from the already attenuated subtree. Do not
apply group opacity again at group exit. Two overlapping opaque members under
opacity 0.5 retain overlap alpha 192, not 128 (verified baseline). A group filter
therefore operates on that attenuated subtree. An isolated post-composite group
opacity model would require an explicit future API, not an incidental refactor.

### ROI and bounds

* Represent an internal local raster as pixels plus a design-space rectangle/
  origin. Keep effect padding separate from logical bounds, pivot, mask center
  and `card_content_bounds`. Translation of ROI origins must not move content.
* For blur radius sigma, initially reserve `ceil(3*sigma*q)+2` raster pixels on
  each affected side (q is local raster density, 2 is reconstruction guard).
  Shadow bounds union content with the shifted, expanded silhouette. Glow expands
  symmetrically; combined supports compose in stage order. Prove the padding
  against Pillow's actual finite blur support with alpha-edge tests; increase it
  within the budget if a visible tail remains. Legacy card's symmetric allocation
  formula stays unchanged.
* Union active children's transformed ink bounds for a group. Include child effect
  extents, glyph/stroke raster padding, and evaluated reveal/geometry. Do not use
  initial layout bounds as runtime effect bounds or include inactive lifetimes.
* Transform all four corners of the padded local rectangle through the complete
  world affine matrix; floor minimum and ceil maximum, with resampling guard.
  Use a conservative density based on the largest singular value of the composed
  linear transform, not only its X scale, for nested rotations/anisotropic scales.
  This can be expensive at extreme magnification: preflight the resulting budget.
* Never crop an offscreen source before retaining the filter/offset halo needed
  by visible output. For huge mostly offscreen layers, inverse-map the requested
  output region, inflate by kernel support, then tile/filter with overlap. Reject
  nonfinite/unsafe transforms or over-budget effect ROIs explicitly; no OOM or
  silent blur/quality reduction.
* Reuse matrix/sprite evaluation and Flow's integer-origin ROI approach. Add a
  small private compositor beside the renderer. Do not run new object filters
  on full-canvas `_affine_scene` temporaries or duplicate full-canvas layers per
  effect. Legacy affine scenes may remain expensive; preserve their semantics.

### Future caching and integration boundary

In 2B, add a renderer-owned effect cache with an explicit byte budget (proposed
32 MiB default, zero disables it), LRU eviction, oversized-entry bypass, and
close/exception cleanup. Charge every retained output/intermediate, not just the
last image. Keys include immutable style values, content snapshot identity,
evaluated paint/reveal/geometry, mask/clip state at that stage, actual raster
dimensions/density, alpha/kernel version, and source frame identity. Group keys
include descendant state, lifetimes and frame identities. Local filters may omit
pure world translation from their keys; changed raster density and transforms
embedded in a group cannot be omitted. Never retain every timestamp or rely on
global mutable state. Update scene-frame signatures to include effect specs when
the opt-in field actually exists.

| Target/integration | 2A | 2B starting scope / later boundary |
| --- | --- | --- |
| Image, Text, basic Shape, nested Group | Ordinary gradient Image composition and current transforms/masks | Isolated effect targets, with explicit coverage/opacity rules above |
| Charts and maps | Gradient cards/backdrops as siblings, transparent chart surface when desired | Keep dynamic data/state keys; defer whole-viewport effects until separately tested |
| FlowChamp | Existing RGBA viewport and frame keys; gradient backdrop/card sibling | Whole-viewport adapter later; no node-theme fill or internal graph effect schema |
| ArchChamp | Ordinary sibling composition; renderer sessions unchanged | Later whole RGBA viewport only, not mesh/material effects or extra GL contexts |
| GIF Image | Existing decoded frame timing and cache invalidation unchanged | Any Image support must include GIF index/source-age tests from the start |
| HtmlClip / OSClip / ChessChamp / prepared playback | Existing prepared/offline viewport paths unchanged | Explicitly defer new effect targeting; never trigger live browser capture/preparation |
| Captions, Equation, Number, indicators | Existing renderer behavior unchanged | Defer until dedicated dynamic-source and cache tests pass |
| Sequence/Grid/Layer | Existing source-clock/layout/composition behavior | No effects on Renderable containers; use supported scene components/groups |

2C must separately define background-only, already-composited z-order capture for
glass; foreground, self capture and recursive backdrop/mask combinations require
explicit exclusions. 2D may add typed scalar tracks for bounded effect values,
with continuous bounds/cache review. Neither entire style-object interpolation
nor expanded Spring property support follows from this ADR. No 2B/2C/2D work is
authorized by Phase 0 or by a later approval of 2A alone.

## Diff-sized Phase 2A execution list

These four milestones were approved together by the user's request to complete
the next phase. The implementation stops at the Phase 2A acceptance gate; no
additional milestone approval is required within that authorized phase:

1. **A1 — descriptions and math.** Add `src/faceless_champ/gradients.py` and
   `tests/test_gradients.py`: frozen types, color/numeric limits, scalar sampling,
   strict stops, endpoint/direction/radial semantics, premultiplied interpolation.
   No renderer, timeline or base-component changes.
2. **A2 — bounded surfaces.** Add a small private `_surface_raster.py`; extend
   `surfaces.py` only for gradient dispatch/new rectangular helper, and export
   public names from `__init__.py`. Extend `tests/test_surfaces.py` for alpha-safe
   colored shadows, geometric face replacement, allocation budgets, exact legacy
   source/frame hashes and no rerasterization during motion. Existing ShadowStyle
   and content-bounds math stay in place. No `effects.py` in this phase.
3. **A3 — integration and visual evidence.** Add a small
   a local surface composition with short preview as default, fixed-time
   screenshots and a flat/linear/radial by light/dark 3x2 sheet. Exercise Spring,
   transparent charts, masks, nested opacity, nonuniform rotation, z-order and
   GIF/HTML sibling clocks using local prepared fixtures. Update a focused effects
   guide, clean-flow/motion-graphics docs and a concise README link.
4. **A4 — verification and review.** Run core/kit/agent separately, lint changed
   files plus baseline lint scope, format changed files without incidental cleanup,
   compare performance/memory with this baseline and the pinned old revision,
   inspect decoded preview plus 6+ reference PNGs, review the diff and stop at the
   2A acceptance gate. No automatic Phase 2B work or merge/publication.

## Validation gates and risks

| Concern | Measurable acceptance / mitigation for the proposed phase |
| --- | --- |
| Backward compatibility | Existing tests pass; same-environment legacy string card PNG source and raw frame hashes match these fixtures. Add colored/translucent legacy fixtures before modifying dispatch. Geometry, reserved options and ShadowStyle defaults/errors retain meaning. |
| Gradient correctness | Scalar/pixel tests cover 0/1 and interior stops, 0/90/180/270/125-degree directions, endpoint extension, centered/off-center radial paint, alpha transitions and transparent RGB. Kernel error <=1 LSB relative to reference, exact normalized endpoints. Invalid NaN/Inf/colors/stop order/center/radius and unsupported fills fail before large allocations. |
| Alpha/edge quality | Inspect premultiplied-alpha transitions against black/white/checkerboard backgrounds; colored shadow RGB must stay constant where alpha is nonzero. Corners/masks must have transparent exterior and no black/color contamination. Test 2x source against AA1/2/4 output, fractional allocation sizes and rotated/nonuniform groups; cross-size frames are compared perceptually, not assumed byte-identical. |
| Existing parent semantics | Preserve sibling stacking, nested mask intersection and overlap alpha 192 under member-wise 0.5 Group opacity. No additional opacity multiplication on shadow. The face allocation includes existing symmetric shadow padding; reject too-small cards. |
| Determinism | Same-size raw bytes match at the six audit times after forward/reverse/shuffled/repeated orders and 24/30/60-FPS seek workloads, caches enabled/disabled, including new surfaces with Spring. Encode short 24/30/60 previews in 2A and decode completely; compare source frames at equal timestamps, not lossy encoded bytes. |
| CPU cost | New gradient construction measured independently for small cards and full 1080p design. One-time work only: monkeypatch gradient generation/blur to fail after construction and render motion/holds successfully. Compare gradient Images with same-size ordinary Images, separating cold decode and replay. Use paired 7-trial before/after runs if a median replay regression exceeds max(10%, 0.5 ms/frame); do not accept a persistent excess without investigation. Apply the same gate to unchanged plain/surface controls. |
| Memory safety | Allocation guard is exercised before Pillow allocation, huge/overflowing inputs rejected, tiles obey scratch budget. Measure native RSS and explicit cache bytes, not tracemalloc alone. Repeat construction/export/close 20 times; caches empty after close, no retained scene/descriptor/renderer references in a weak-reference lifecycle check, no monotonic live-buffer growth. RSS alone is not a leak oracle. |
| Cache growth | No new retained per-frame surface state or global cache in 2A. Existing unbounded asset/sprite dictionaries remain a documented renderer-session risk. 2B must introduce a bounded effect cache and test eviction/oversized bypass before enabling effects. |
| ROI/group expense | The legacy affine path is already costly. 2A adds no runtime filters there. Require local-only filtered allocations, halo completeness, transform bounds and worst-case nesting/memory tests in 2B; no silent whole-canvas filter fallback. |
| Visual quality / versions | Fixed 2x source paint can soften under large scale/4K output; do not claim infinite detail or linear-light color. No stochastic dithering in v1. Test supported Pillow versions, inspect long shallow ramps for banding, and revise the raster strategy before shipping if native tiled math misses quality or construction-cost goals. |
| Integration claims | Full current tests provide regression evidence; Phase 0 manually captures only 2D/card/chart cases. No new 3D/GIF/browser-effect behavior is claimed tested. Existing optional integrations/dependencies stay lazy; no live web capture or GPU installation. |

Suggested performance gate values above are local review triggers, not universal
real-time guarantees. Re-run paired controls on the same machine/settings before
making an acceptance decision; the raw trials capture visible host variation.

## Approval checklist

- [x] Approve the immutable gradient API and explicit angle/radial/color semantics.
- [x] Approve Image-based Phase 2A with unchanged renderer/timeline/Spring schemas.
- [x] Approve legacy pixel preservation, with alpha-safe new gradient paths and a
      documented legacy colored-shadow limitation rather than a silent retrofit.
- [x] Approve new-gradient allocation limits, tiled raster strategy and measured
      replay/memory/visual acceptance gates.
- [x] Approve A1–A4 as the only next implementation scope, with a phase review stop;
      runtime glow/blur, glass and animated effects require later authorization.

Phase 0 stopped here for approval. Phase 2A was subsequently authorized; its
implementation and actual validation are recorded in
[the Phase 2A report](../premium-effects-verification.md). Phase 2B remains outside
the authorization.
