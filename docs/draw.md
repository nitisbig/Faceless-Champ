# Frame drawing (`faceless_champ.draw`)

`faceless_champ.draw` is an immediate-mode Skia toolkit for films drawn frame by frame in
code, such as math explainers and data stories. You write one function `draw(t, size)` that
paints the whole frame for time `t`. `draw_scene` wraps it in a `FunctionSource`, so the normal
render, `save_frame`, `Sequence` and audio tools all still work.

Use it when a shot needs exact per-frame control: simulations, 3D projections, equation morphs,
and many effects layered in one place. For standard beats, use Scene components and kit shots.

Needs `faceless-champ[skia]`. `mathtype` needs Typst (see [skia.md](skia.md)), and `mesh3d`
needs `faceless-champ[3d]`. `timing` and `palette` import neither.

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
