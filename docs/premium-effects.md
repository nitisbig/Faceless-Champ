# Gradient surfaces and shadows

Phase 2A adds reusable, CPU-only surface paint. `LinearGradient` and
`RadialGradient` are frozen descriptions. `card_surface` and `gradient_surface`
rasterize once into ordinary `Image` components; moving, rotating, fading or
masking them uses the existing renderer and timeline. No new dependency, live
effect loop or browser/GPU context is involved.

```python
from faceless_champ import Bounds, Canvas, GradientStop, LinearGradient, RadialGradient, Scene, ShadowStyle, Spring, card_surface, gradient_surface

stops = (
    GradientStop(0, "#15182D"),
    GradientStop(0.55, "#3647A0"),
    GradientStop(1, "#62DDDB"),
)
scene = Scene(Canvas(960, 540, "#111827"))
scene.add(gradient_surface(
    Bounds(0, 0, 960, 540),
    fill=RadialGradient(stops, center=(0.3, 0.2), radius=1.2),
    opacity=0.35, z_index=-1,
))
card = card_surface(
    Bounds(120, 75, 840, 465),
    fill=LinearGradient(stops, angle=125), radius=36,
    shadow=ShadowStyle(color="#00000080", blur=12, offset=(0, 8)),
)
scene.add(card)
scene.play(card.animate.move_to(500, 260).scale_to(0.95),
           run_time=1.2, rate_func=Spring())
scene.wait(1)
scene.render("gradient-preview.mp4", width=960, height=540, fps=30,
             antialias=1, overwrite=True)
```

## Public API

| API | Contract |
| --- | --- |
| `GradientStop(offset, color)` | Finite offset in `[0,1]`, Pillow color string including alpha. Colors canonicalize to RGBA hex; invisible RGB becomes zero. |
| `LinearGradient(stops, angle=0)` | 2–64 strictly increasing stops. Angle is finite and normalized modulo 360. 0 points right, 90 down, clockwise. |
| `RadialGradient(stops, center=(0.5,0.5), radius=0.5)` | Center coordinates in `[0,1]`. Radius in `[1e-6,16]`, as a fraction of the smaller face dimension. Circular in design pixels. |
| `card_surface(bounds, fill=..., radius=44, shadow=None, **component_options)` | Accepts an existing color string or either gradient. Returns Image; radius clamps to half the smaller face side. Bounds include shadow clearance. |
| `gradient_surface(bounds, fill=..., **component_options)` | Requires a linear/radial gradient. Rectangular surface with zero corner radius and no shadow. |
| `ShadowStyle(color="#00000026", blur=16, offset=(0,12))` | Existing frozen style, unchanged. Blur and offset use design pixels. |
| `card_content_bounds(bounds, shadow=None, padding=28)` | Existing layout helper; identical clearance for solid and gradient cards. |

The factories reserve `width`, `height`, `position`, `anchor`, `fit` and `trim` to
preserve their allocated viewport. Set these through Bounds, then use ordinary
component/group transforms. Options such as `opacity`, `rotation`, `mask`,
`scale_x`, `scale_y` and `z_index` retain normal Image behavior. Width/height and
position retain authored values; measured `.bounds` follows existing rounded
viewport measurements for fractional dimensions.

Stops are copied into an immutable tuple. Duplicate offsets, unordered stops,
NaN/Inf, invalid colors and unsupported fill types fail explicitly. A gradient
can omit endpoints: samples before its first stop or after its last stop use
the nearest stop color. There are no implicit hard edges at coincident stops.

## Paint and alpha semantics

Linear paint projects the face rectangle onto its angle direction and maps its
minimum/maximum projections to 0/1. Radial distance uses the face's physical
aspect ratio, so it remains circular on an untransformed rectangular card. Its
radius is relative to `min(face_width, face_height)`. Center and radius are the
only normalized coordinates; card radius, shadow blur and shadow offset use
design pixels. Rounded coverage can hide the extreme projected corners.

Interpolation uses premultiplied **encoded sRGB** plus alpha. An opaque red stop
fading to transparent blue stays red as coverage fades; hidden blue does not
contaminate the transition. This is not linear-light interpolation. Samples
unpremultiply before deterministic nearest-integer RGBA quantization. Fully
transparent samples store `(0,0,0,0)`; exact end colors refer to that normalized
form. Existing animated color tracks keep their current straight-RGBA rule.

For gradient-card shadows, the engine blurs an L-mode geometric mask, then
colorizes with constant shadow RGB and multiplies the shadow color alpha once.
The geometric face replaces the shadow beneath it, even where the paint is
transparent; paint alpha does not change the shadow silhouette. The complete
baked image is then affected by component/group opacity, masks and clipping.
Geometric coverage receives a fixed 0.75-source-pixel antialias filter; fractional
face/shadow coverage mixes in premultiplied float tiles. This suppresses bright
fringes during successive image scaling/rotation. Full opaque rectangular
backdrops bypass the edge filter and coverage mixing.

String-fill cards keep their historical pixels. Their original RGBA-blurred
colored shadows can have darker fringes; black shadows hide this limitation.
Gradient cards use the new alpha-safe stage, so a constant-color gradient with a
colored shadow can differ from a legacy color-string card at shadow fringes.
There is no silent retrofit of existing videos. Both paths keep the existing
face-replacement convention and shadow clearance:

```python
clearance = ceil(3 * shadow.blur + max(abs(dx), abs(dy)))
```

Default ShadowStyle therefore reserves 60 design pixels on every side. Content
padding adds to that inset. Both helpers reject allocations without room for
the face/content; new gradient faces also need one raster sample per axis.

## Cost, limits and reuse

Factories generate at 2x design resolution, independently of export FPS, output
resolution and renderer antialiasing. General fields use bounded row tiles and
native Pillow channel math; cardinal linear gradients expand a sampled line.
Very narrow stop intervals and tiny radial radii use the scalar reference path
to preserve precision. Those unusual paints can take longer to construct.

New gradient allocations are checked before raster allocation:

* Each design side must be between 1 and 4096 pixels (8192 at 2x).
* Total source pixels must not exceed 8,388,608.
* A conservative working-set estimate, including scratch and encoding, must fit
  192 MiB. Passing the pixel limit alone does not guarantee passing this estimate.

A 1920x1080 design at 2x fits. A 3840x2160 design at 2x exceeds the limit; render
a smaller design canvas to a 4K output instead. Strong magnification can soften
baked detail. These bounds protect each new construction; they do not impose a
global budget on existing renderer asset/sprite dictionaries or legacy factories.

Only encoded source bytes survive construction. Renderer sessions reuse decoded
images and sprites; there is no global paint cache or retained per-frame gradient
state. Construct surfaces before frame rendering and reuse their components.
Changing paint requires a new surface and scene snapshot. Use a renderer context
manager or call `close()` when finished, as for ordinary images.

The private raster stages use `ImageMath.lambda_eval` with callables, supported
within the existing Pillow requirement; see Pillow's [10.3 release notes](https://pillow.readthedocs.io/en/stable/releasenotes/10.3.0.html).
They do not evaluate user-provided expression strings.

Gradients paint surface helpers only. Shape/Text/Canvas/Chart/Flow/Arch fill
schemas are unchanged; place gradient Images behind transparent viewports.
Runtime blur/glow, backdrop glass, spread/inset shadows and animated effect
parameters are outside this API.
