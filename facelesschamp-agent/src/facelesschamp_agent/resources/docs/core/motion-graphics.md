# Motion graphics

All APIs below are public imports from `faceless_champ`; Pillow is the only required
Python dependency. See `examples/motion_graphics/render.py` for a complete 18-second,
960×540, 24 fps showcase.

## Animated properties

```python
from faceless_champ import Canvas, Rectangle, Scene, linear

scene = Scene(Canvas(960, 540))
card = Rectangle(width=160, height=90, fill="white", position=(480, 270))
scene.add(card)
scene.play(
    card.animate.fill_to("#708fff80")
    .stroke_to("#48e0cb")
    .width_to(240)
    .height_to(140)
    .stroke_width_to(6)
    .corner_radius_to(30)
    .scale_xy_to(1.2, 0.8),
    run_time=2,
    rate_func=linear,
)
box = scene.bounds_at(card, 1)
```

Shape builders support fill, stroke, width, height, stroke width and rectangle
corner radius. Text and Number support `color_to(color)`. Colors accept Pillow color
strings or four-channel RGBA tuples. `None` means transparent black `(0,0,0,0)`.
Interpolation is **straight, unpremultiplied sRGB channel interpolation**, including
alpha, with channels rounded only for rasterization. It is not linear-light color
mixing. Use an explicit transparent version of the same RGB color when fading its
alpha without changing hue. To fade an entire visual, use `opacity_to` instead.
Raw `Animation` color tracks require four-channel tuples, including keyframes.

Width/height and scales must be positive; stroke width and radius may be zero.
Corner radius is clamped at rendering to half the smaller current dimension, so
shrinking a rounded rectangle stays well formed. Polyline dimensions rescale its
local path. Width/height are independent even for Circle and Square; animate both
if their aspect ratio must remain fixed.

All components accept `scale_x=1, scale_y=1`. These multiply the existing uniform
`scale`; `scale_to` retains its meaning. Local scaling precedes clockwise rotation.
Nested nonuniform scales and rotations use composed affine matrices, including
shear. Top-left anchoring keeps the existing unrotated anchor-box convention.

`component.bounds` still measures initial authoring geometry. Use
`scene.bounds_at(component, time)` for a conservative world-space box that includes
animated geometry and ancestor transforms. Masks, opacity and lifetimes do not
shrink this reserved layout box. Render states never mutate source objects or
scene snapshots. Intermediate style/geometry sprites are not cached.

## Scheduling

```python
from faceless_champ import Repeat, Stagger, Succession

scene.play(
    Stagger(
        Succession(card.animate.rotate_to(15), card.animate.rotate_to(0), duration=0.5),
        card.animate.opacity_to(0.5),
        lag=0.2,
    )
)
scene.play(Repeat(card.animate.scale_to(1.2), cycles=4, ping_pong=True, duration=0.4))
```

| Helper | Timing |
| --- | --- |
| `Stagger(*children, lag=0.1, duration=1, delay=0)` | Child i starts at delay + i × lag seconds. |
| `Succession(*children, duration=1, delay=0)` | Each child follows the previous child's total duration. |
| `Repeat(child, cycles=N, ping_pong=False, duration=1, delay=0)` | N finite traversals of the child, after one initial delay. |

`duration` supplies the duration of direct Animation children. A nested schedule
uses its own `run_time`, including its delay. Every schedule exposes `run_time`.
Stagger ends when its latest child ends. Succession sums child times; Repeat
multiplies the child's time by cycles. Delays are nonnegative, durations positive,
and cycles must be a positive integer (booleans are rejected).

`scene.play(schedule)` uses its natural duration. An explicit
`scene.play(schedule, run_time=...)` proportionally scales all durations, delays,
and gaps. Multiple top-level arguments start together. Ordinary animation-only
`play()` keeps its one-second default. `Scene.at()` preserves the furthest cursor.

Nested schedules flatten into chronological tracks before publication. Conflicting
tracks, invalid lifetimes, and invalid values fail before changing the scene,
including when a failure occurs in a later nested child. Different properties may
overlap. Scheduling trials copy existing timeline entries; this adds authoring-time
cost but no per-frame scheduling cost. Avoid millions of repetitions: finite loops
expand tracks in proportion to cycle count.

Repeat captures the first traversal's resolved values. Subsequent forward cycles
restart those values instead of accumulating relative motion. Ping-pong reverses
alternate traversals, including keyframe order and easing. **Cycles counts
traversals**, so two ping-pong cycles finish at the initial state; three finish at
the forward target. At an exact shared track boundary, the next track's initial
value wins. Forward loops can jump at that boundary; use a cyclic animation (such
as LoadingDots) or ping-pong for continuity. Within gaps each property holds its
last value until its next track begins. The last traversal's endpoint is held.
Add components before scheduling if they should be visible before their first
track; otherwise automatic addition occurs at that first track's start.

## Masks and directional reveals

```python
from faceless_champ import CircleMask, Group, Text, Wipe

label = Text("READY", position=(480, 270), font_size=28)
group = Group(card, label, mask=CircleMask(100))  # form groups before scene.add()
masked_scene = Scene(Canvas(960, 540))
masked_scene.add(group)
masked_scene.play(Wipe(group, direction="right"), run_time=1)
masked_scene.play(group.animate.mask_to(position=(20, 0), width=160, height=120))
```

Attach `mask=` before scene addition to any component or group:

- `RectangleMask(width, height, position=(0,0))`
- `CircleMask(radius, position=(0,0))`; independently animated dimensions make an ellipse.
- `ShapeMask(points, width=..., height=..., position=(0,0))`; points are polygon
  coordinates normalized to `[0,1]` inside the mask box.

Masks are centered at their local position, relative to a leaf's sprite center or
a group's fixed layout pivot. Dimensions use design pixels before the target's
transform. Zero dimensions hide the target. Position and dimensions animate with
`mask_to(position=..., width=..., height=...)`; a mask must already be attached.
Mask type and polygon vertices remain fixed. General raster/gradient masks and
independent mask rotations are outside this API; rotate the target or a subgroup.

`Wipe(target, direction="right"|"left"|"down"|"up")` animates a normalized rectangular
clip from empty to full. Direction describes the reveal's travel. It uses the same
alpha-mask compositor and intersects any attached mask. A group's wipe box encloses
evaluated child bounds. Group masks clip the complete composited subtree; they never
clip unrelated siblings or the canvas background. Nested masks intersect. Ancestor
opacity continues to multiply each member's opacity, preserving existing Group
semantics even where members overlap. Transparent canvas pixels remain transparent.

Affine/masked rendering uses temporary canvas-sized layers and transformed masks.
Memory scales with canvas area and hierarchy depth, not animation length. Large
canvases and deeply nested masked groups cost more CPU than ordinary sprites; use
small previews and avoid unnecessary nesting. Existing ordinary scenes retain the
original renderer path. GIF/caption ages and ranged export source clocks are unchanged.

## Indicators

All five progress visuals support `progress=0`, `.animate.progress_to(value)`,
placement/opacity/transforms, and Group membership. Progress is finite in `[0,1]`.
They share `width`, `height`, `color`, `track_color`, `stroke_width`, and optional
`label=True` (a numeric percentage centered in the viewport). Choose a viewport
large enough for a label, especially for a bar. Fonts reuse the library's default.

| Component | Behavior |
| --- | --- |
| `ProgressBar` | Left-to-right rounded track, defaults 240×20. |
| `ProgressRing` | Clockwise ring from twelve o'clock, defaults 120×120. |
| `Gauge` | Semicircle from left to right across the upper half of a 120×120 viewport. |
| `LoadingDots` | Three phase-shifted dots, defaults 100×24; progress 0 and 1 are identical. |
| `Checkmark` | Draws a two-segment check from empty to complete, defaults 80×80. |
| `Countdown(seconds, **Number_options)` | Nonnegative Number; defaults to ceiling seconds, ending exactly at zero. |

```python
from faceless_champ import Countdown, LoadingDots, ProgressRing, Repeat

ring = ProgressRing(position=(200, 200), label=True)
timer = Countdown(5, position=(400, 200), font_size=48)
dots = LoadingDots(position=(600, 200))
scene.add(ring, timer, dots)
with scene.at(scene.time):
    scene.play(ring.animate.progress_to(1), timer.animate.value_to(0), run_time=5, rate_func=linear)
# Schedule the dots at an explicitly chosen overlapping time with Scene.at().
scene.play(Repeat(dots.animate.progress_to(1), cycles=3, duration=1), rate_func=linear)
```

Indicators never run their own wall clock. Countdown accepts Number formatting,
font, color and fixed-width options; `value_to` rejects negative values. A loading
loop must be scheduled with a finite cycle count. No indicator frame sprites are
retained, and arbitrary out-of-order sampling produces the same image.

## Reproduce the showcase

```bash
.venv/bin/python examples/motion_graphics/render.py --frames
.venv/bin/python examples/motion_graphics/render.py
# Add --overwrite when intentionally replacing a previous render.
```

Output: `output/motion_graphics/showcase.mp4`; six representative PNGs are written
beside it with `--frames`. No external artwork, fonts, audio, or network access is required.
