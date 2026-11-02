# Frame drawing (`faceless_champ.draw`)

`faceless_champ.draw` is an immediate-mode Skia toolkit for films drawn frame by frame in
code, such as math explainers and data stories. You write one function `draw(t, size)` that
paints the whole frame for time `t`. `draw_scene` wraps it in a `FunctionSource`, so the normal
render, `save_frame`, `Sequence` and audio tools all still work.

Use it when a shot needs exact per-frame control: simulations, 3D projections, equation morphs,
and many effects layered in one place. For standard beats, use Scene components and kit shots.

Needs `faceless-champ[skia]`. `mathtype` needs Typst (see [skia.md](skia.md)), and `mesh3d`
needs `faceless-champ[3d]`. `timing` and `palette` import neither. `noise` and `physics` need
`faceless-champ[motion]` (opensimplex, pymunk) but not Skia, so they also work in any `FunctionSource`.

## A complete scene

```python
from faceless_champ import Theme
from faceless_champ.draw import Frame, Palette, draw_scene, ease_out, env, hud, lin, smooth

THEME = Theme.named("midnight")
PALETTE = Palette.from_theme(THEME, ball="#5FB6FF")


def draw(t, size):
    fr = Frame(size, palette=PALETTE)
    r = 180 * ease_out(lin(t, 0.2, 1.2))
    fr.circle(960, 540, r, "ball", 3.0, glow=0.7)
    fr.glow_dot(960, 540, 10, "secondary", smooth(lin(t, 0.8, 1.2)))
    hud.pill(fr, 960, 820, "unit circle", "ink", env(t, 1.0, 3.0))
    hud.eyebrow(fr, t, "01 · CIRCLES", 0.2)
    fr.vignette(0.5)
    fr.grain(t, 0.04)
    return fr.finish()


scene = draw_scene(draw, 3.0, theme=THEME)
```

## Coordinates and output size

You draw in design pixels (`design=(1920, 1080)` by default). The frame scales to whatever size
the renderer asks for, so 720p previews and 4K finals run the same code. `fr.k` is the
output-to-design scale. `fr.c` is the crisp skia canvas and `fr.g` is the glow canvas. Both are
public, so you can `save`, `concat` and draw on them directly.

Export with `antialias=1`. Skia already antialiases every edge. The default export setting,
`antialias=2`, would make each frame draw at twice the width and height. That costs about four
times as long (2.8 s instead of 0.8 s per 720p frame in a glow-heavy test) and looks no
smoother.

## Colors: Palette

Colors are tokens resolved through a `Palette`, never hard-coded:

- `Palette.from_theme(theme, **extra)` exposes every `ColorScheme` role (`background`, `text`,
  `muted`, `primary`, `secondary`, ...), the aliases `bg`, `ink` and `line`, and four drawing
  tokens: `light` (glints and sweeps), `glass` and `glass_deep` (glass cards) and `floor`
  (3D dot floors). Keyword arguments add project tokens or override any of them.
- Anything that takes a color also accepts a `#rrggbb` hex.
- `set_default_palette(PALETTE)` makes it the default for `Frame(size)`, `col`, `mix` and
  `mathtype.tc`. Call it in the project's theme module, so render workers that import the scene
  get it too. Without a default, the active theme's palette is used.

## Timing

`lin(t, t0, t1)` gives a 0→1 ramp, and `smooth`, `ease_in`, `ease_out`, `ease_io` and `back`
shape it. `env(t, a, b, fin, fout)` is a visibility envelope. `pulse(t, at, width)` is a
0→1→0 bump. `chroma_kick(t, at, amount)` decays a color split you pass to `fr.chroma`.

`CueClock("cue-per-word.srt")` gives narration times: `cue(n)` is a word cue's start,
`beat(n)` lands `lead` seconds (default 0.15) before it, and `word("text", after=)` finds a
word by its text.

## Frame

- **Shapes:** `path_stroke`, `path_fill`, `poly`, `line`, `circle`, `rrect`, `dashed`,
  `glow_dot`, `text` (baseline at y; families `sans`, `display`, `serif`, `italic`, `mono`),
  `image_quad`, `image_fill`. Most take `glow=` (0..1), which draws onto the glow canvas.
- **Light:** `light_sweep(path, u)`, `light_cone`, `glint`, and `blurred(sigma)`, a context
  manager for depth-of-field layers.
- **Finish:** `dim`, `chroma`, `zoom_blur`, `letterbox`, `vignette`, `grain`, then `finish()`,
  which blooms the glow layer and returns opaque HxWx4 uint8.
- **Glow style:** `glow="tight"` (half-resolution, the default) or `"soft"` (quarter-resolution,
  wider halos), or pass a `GlowStyle`.
- **Offscreen drawing:** `offscreen(w, h, fr.k)` returns `(surface, Pen)`. A `Pen` has the same
  drawing methods on an existing canvas, for cards you build once and place many times.
- **Motion blur:** `motion_blur(draw_one, t, size, weight=)` averages subframes. The count comes
  from `FC_MOTION_BLUR` (default 1, which means off). Pass `weight` (0..1) so only fast beats
  pay for it.

## hud, mathtype, space, mesh3d

- `hud`: `glass_card`, `pill`, `readout`, `coord_chip`, `tabular` (digits that don't jitter),
  `eyebrow`, `arrow`, `arrow3d`, `axis3d`, `right_angle` and `dot_grid`.
- `mathtype`: Typst math as paths. Use `draw(fr, expr, cx, cy, size, reveal=)`,
  `morph(fr, a, b, u, ...)` (glyphs with the same shape fly across and the rest cross-fade),
  `number` (live values without recompiling), `term`, `size_of`, `glyph_centers`, and
  `tc(token, body)` to color a sub-term.
- `space`: `Camera`, `orbit`, `orbit_path` (eased Catmull-Rom camera keys), `Spline`, `to_view`,
  `rot_x/y/z`, `draw_box`, `draw_boxes` (painter-sorted) and `text3d`.
- `mesh3d`: `render(meshes, cam, size, cache=, root=)` renders PyVista meshes through the same
  `space.Camera` and caches the frames on disk. `composite(fr, rgba)` draws the result under
  the skia edges. `glass()` and `gloss()` are ready-made material styles.

## noise: organic motion

Smooth, repeatable OpenSimplex randomness. Each function depends only on `t` and `seed`, so
frames can render in any order. Values are roughly in [-1, 1].

```python
from faceless_champ.draw import noise

dx, dy, deg = noise.shake(t, 6.0 * env(t, 4.0, 4.8))     # handheld drift, stronger on a hit
pts = noise.wobble(curve, t, 2.0, fps=12)               # hand-drawn line boil at 12 fps
xy = noise.drift(120, t, (0, 0, 1920, 1080))            # (120, 2) floating particles
grid = noise.field(t, (48, 27))                         # coarse grid for fog or aurora
```

- `value(t, freq=1, seed=0, octaves=1, lane=0)` is the base signal. `freq` is roughly wiggles
  per second, and different `lane`s are independent.
- `shake(t, amount=6, freq=0.8, rotation=0.3)` returns `(dx, dy, degrees)`. Multiply `amount`
  by an envelope to shake only around an impact.
- `wobble(points, t, amount=2, scale=0.01, speed=1.5, fps=None)` displaces points with noise
  that varies along the line. `fps=12` holds each pose for 1/12 s, like hand-drawn animation.
- `drift(count, t, area, speed=18, wander=40)` gives each particle its own heading and a
  wandering offset, and wraps it around `area` (x, y, width, height).
- `field(t, shape=(48, 27), scale=3, speed=0.12)` returns a float32 `(rows, columns)` grid.
  Scale it up with `image_from_array`.

Each sample is pure Python (about 40-70 µs). Keep point counts in the hundreds and fields
coarse, or install `numba`, which opensimplex uses automatically.

## physics: baked rigid bodies

pymunk worlds are simulated once at a fixed step, stored, and then sampled by time. A live
simulation would differ between parallel render workers; a baked one is identical everywhere.

```python
from faceless_champ.draw import physics

world = physics.World(gravity=1800, bounds=(0, -400, 1920, 1600))  # y down, design px
world.walls((600, 40, 720, 1000))
world.peg(960, 300, 5)
for i in range(150):
    world.ball(960, 60, 11, at=i * 0.07, elasticity=0.5, friction=0.1, tag="bead")
sim = world.bake(18.0)            # at import or build time; cached on disk

def draw(t, size):
    fr = Frame(size)
    for s in sim.statics:         # pegs, segments and static boxes, for drawing
        ...
    for b in sim.at(t, "bead"):   # live bodies, interpolated between 240 Hz samples
        fr.circle(b.x, b.y, b.radius, "primary", fill=True)
    return fr.finish()

for hit in sim.impacts(min_speed=300, tag="bead"):
    scene.add_sfx("tick.wav", hit.time, volume=min(1.0, hit.speed / 1500))
```

- `World(gravity=1800, rate=240, damping=1, iterations=20, bounds=None)`. A number for
  `gravity` falls down the screen; an `(x, y)` pair sets any direction. A body that leaves
  `bounds` (x, y, width, height) is removed.
- Bodies:
  - `ball(x, y, radius, at=, velocity=, mass=, elasticity=, friction=, tag=)`
  - `box(x, y, width, height, angle=, spin=, static=False, ...)`
  - static `segment(a, b, radius)`, `peg(x, y, radius)` and `walls(area, top=False)`

  `at` spawns a body later. Elasticity is 0-1, and a contact uses the product of both
  shapes' values.
- `bake(duration, cache=True)` returns a `Simulation`. The cache is
  `FC_CACHE_DIR/physics/<hash>.npz`, keyed by everything in the world, so any edit re-simulates.
- `Simulation` methods:
  - `at(t, tag=None)` returns `Body(index, kind, x, y, angle, radius, width, height, tag)`.
    `angle` is in radians.
  - `positions(t, tag=None)` returns `(n, 3)` arrays.
  - `statics` lists the fixed shapes for drawing.
  - `impacts(min_speed=200, tag=None, spacing=0.04)` returns `Impact(time, x, y, speed, tags)`,
    ready for `add_sfx`.
  - `settle_time(speed=5)` is the last time anything was still moving.
- Physics is deterministic but chaotic: a tiny change to a peg or a spawn time changes where
  every later body lands. Tune the world until the outcome reads well, then keep it. For a
  Galton board, use a funnel above a full-width staggered peg grid. A peg triangle alone lets
  beads bounce off its edges and fall outside it. Make the funnel neck at least 3-4 bead
  diameters wide, or beads jam in it.
