# Compositing, shapes, shaders and math

After Effects style tools built on Skia. They need `skia-python`
(`pip install -e '.[skia]'`) and run on the CPU, so they work with
`backend="skia"` (recommended) and `backend="pillow"`, including 4K renders on
CPU-only machines. `backend="moderngl"` rejects them with a clear error, and
`backend="auto"` picks a CPU backend for scenes that use them.

| Feature | API | After Effects equivalent |
|---|---|---|
| Blend modes | `blend="screen"` on any component | Layer blending modes |
| Track matte | `blend="stencil"` / `"silhouette"` inside a `Group` | Alpha matte / inverted matte |
| Trim paths | `trim_start`, `draw`, `trim_offset`, `Trace()` | Trim Paths (start, end, offset) |
| Dashes | `dash=(on, off)`, `dash_offset` | Stroke dashes |
| Path booleans | `a | b`, `a & b`, `a - b`, `a ^ b` | Merge Paths |
| SVG import | `SVG("logo.svg", width=400)` | Importing vector artwork |
| Custom shaders | `ShaderFill`, `ShaderEffect` (SkSL) | Pixel Bender / custom effects |
| Displacement | `DisplacementMap(amplitude, size, speed, map)` | Turbulent Displace / Displacement Map |
| Lighting | `Lighting(light, azimuth, elevation, bevel, depth, specular)` | Bevel and Emboss / Lights |
| Morphology | `Morphology(radius, mode="dilate" or "erode")` | Minimax / Simple Choker |
| Path effects | `round_corners=24`, `jitter=(8, 2.5)` | Round Corners / Roughen Edges |
| 2.5D layers | `tilt_x`, `tilt_y`, `perspective`, `animate.tilt_to()` | 3D layer rotation + camera |
| Math | `Equation("mat(1, 2; 3, 4)", engine="typst")`, `MathGlyphs(...)` | (none built in) |

## Blend modes

```python
from faceless_champ import Canvas, Circle, Group, Scene

scene = Scene(Canvas(1920, 1080, bg="#0E1116"))
red = Circle(220, fill="#FF4D6D", stroke=None, position=(860, 480))
blue = Circle(220, fill="#3A86FF", stroke=None, position=(1060, 480), blend="screen")
scene.add(Group(red, blue))
scene.wait(2)
```

Modes: `normal`, `multiply`, `screen`, `overlay`, `darken`, `lighten`,
`color_dodge`, `color_burn`, `hard_light`, `soft_light`, `difference`,
`exclusion`, `hue`, `saturation`, `color`, `luminosity`, `add`, `stencil`,
`silhouette`.

A blended component combines with what is drawn beneath it inside its layer.
A `Group` becomes its own layer when it blends or one of its direct children
does, so blending stays inside the group (like a pre-comp). Use that for mattes:

```python
from faceless_champ import Canvas, Circle, Group, Image, Scene

scene = Scene(Canvas(1920, 1080))
photo = Image("assets/photo.jpg", width=1920, height=1080, position=(960, 540))
spotlight = Circle(300, fill="white", stroke=None, position=(960, 540), blend="stencil")
scene.add(Group(photo, spotlight))  # the photo shows only inside the circle
scene.play(spotlight.animate.move_to(1300, 500), run_time=2)
```

`silhouette` does the opposite: it cuts a hole. Without a group, a stencil
cuts the whole scene, background included.

## Trim paths and dashes

All shapes (`Line`, `Polyline`, `Circle`, `Rectangle`, `Arrow`, `VectorPath`...)
accept:

- `draw`: trim end (0-1). `Draw(shape)` animates it from 0 to 1.
- `trim_start`: trim start (0-1).
- `trim_offset`: shifts the visible span along the path. It wraps on closed
  paths, so animating it from 0 to 1 sends a segment around a circle.
- `dash=(on, off, ...)`: on/off lengths in design pixels. `(0, 14)` with
  `line_cap="round"` gives dots.
- `dash_offset`: slides the dashes; animate it for "marching ants" or flow.

```python
from faceless_champ import Canvas, Circle, Line, Scene, Trace

scene = Scene(Canvas(1920, 1080, bg="#0E1116"))
orbit = Circle(300, fill=None, stroke="#FFD166", stroke_width=10, position=(960, 540), line_cap="round")
wire = Line(1200, stroke="#4FD1C5", stroke_width=6, position=(960, 900), dash=(24, 14))
scene.add(orbit, wire)
scene.play(Trace(orbit, length=0.2), wire.animate.dash_offset_to(-380), run_time=2, rate_func="linear")
scene.play(orbit.animate.trim_to(start=0, end=1, offset=0), run_time=0.8)
```

Lengths are measured along the whole path, and dashes are anchored to the
path start, so trimming a dashed stroke never makes the pattern swim.
Arrowheads follow the trim end. On the Pillow backend `Arrow` uses only `draw`.

## Paths: SVG data, helpers, text outlines and booleans

```python
from faceless_champ import PathData, VectorPath

gear = PathData.ellipse(0, 0, 160) - PathData.ellipse(0, 0, 60)
badge = PathData.star(0, 0, 200, 90, points=6) | PathData.rect(-60, 120, 120, 80, radius=16)
logo = PathData.from_svg("M10 80 Q 95 10 180 80 T 350 80")  # any SVG path d string
word = PathData.from_text("CALCULUS", font_size=160)  # glyph outlines, baseline at y=0

VectorPath(gear, fill="#3A86FF", stroke=None, fill_rule="even_odd", position=(960, 540))
VectorPath(word, fill=None, stroke="#FFFFFF", stroke_width=3, position=(960, 540))  # then play Draw(...)
```

Booleans use Skia PathOps, so their results are exact curves. Paths with
several contours (holes, text) need `backend="skia"`.

## Path effects

`round_corners=r` rounds every corner of a shape's outline (stars, polygons,
polylines, boolean results). `jitter=(segment, deviation[, seed])` roughens it
into a hand-drawn line. Both apply to fill and stroke and need `backend="skia"`.

```python
from faceless_champ import PathData, Rectangle, VectorPath

soft_star = VectorPath(PathData.star(0, 0, 120, 55), fill="#F72585", stroke=None, round_corners=14)
sketch = Rectangle(width=420, height=260, fill=None, stroke="#FFFFFF", stroke_width=3, jitter=(14, 3.5))
```

## Perspective (2.5D) layers

Any component or Group can rotate around its horizontal (`tilt_x`) or vertical
(`tilt_y`) axis through its center, seen from `perspective` design pixels
(default 1400 when a tilt is given). Set `perspective=` with zero tilts to make
the tilt animatable from flat.

```python
from faceless_champ import Group, Rectangle, Text

card = Group(
    Rectangle(width=420, height=260, fill="#3A86FF", stroke=None, corner_radius=28, position=(960, 540)),
    Text("2.5D", role="title", position=(960, 540)),
    tilt_y=55,
)
scene.play(card.animate.tilt_to(y=0), run_time=1.2)
```

Works on `backend="skia"` and `"pillow"` (via the CPU compositor), not ModernGL.

## SVG artwork

```python
from faceless_champ import SVG

logo = SVG("assets/logo.svg", width=480, position=(960, 540))
icon = SVG("assets/icons/bolt.svg", height=96, color="#FFD166", position=(200, 200))
```

The file is re-rasterized at the output density, so 4K stays sharp. `<use>`
and `<symbol>` references (icon sprite sheets, Figma exports) are expanded.
Every component feature works: transforms, masks, effects, blend modes.

## Custom SkSL shaders

SkSL is Skia's shading language and is very close to GLSL. `ShaderFill`
paints a rectangle with a program whose `xy` is in design pixels:

```python
from faceless_champ import ShaderFill

PLASMA = """
uniform float iTime;
uniform float2 iResolution;
uniform half4 tint;
half4 main(float2 xy) {
    float2 uv = xy / iResolution;
    float v = sin(uv.x * 9.0 + iTime) + sin(uv.y * 7.0 - iTime * 1.3) + sin((uv.x + uv.y) * 5.0);
    return half4(tint.rgb * (0.5 + 0.25 * v), 1.0);
}
"""
background = ShaderFill(PLASMA, width=1920, height=1080, position=(960, 540), uniforms={"tint": "#4FD1C5"})
```

Built-in uniforms are filled in when declared: `iTime` (seconds since the
layer appeared) and `iResolution` (layer size in design pixels). Other
uniforms come from `uniforms=`: a number, a 2-4 number sequence, a color
string (becomes a 0-1 float4), or a function of time such as
`{"glow": lambda t: 0.5 + 0.5 * math.sin(t)}`.

`ShaderEffect` runs a program over a component's own pixels:

```python
from faceless_champ import EffectStack, ShaderEffect, Text

SCANLINES = """
uniform shader content;
uniform float iTime;
uniform float iScale;
half4 main(float2 xy) {
    half4 c = content.eval(xy);
    float line = 0.75 + 0.25 * sin((xy.y / iScale) * 1.6 + iTime * 8.0);
    return half4(c.rgb * line, c.a);
}
"""
title = Text("SIGNAL", font_size=160, effects=EffectStack(shader=ShaderEffect(SCANLINES)))
```

`content.eval(xy)` returns premultiplied color. `xy` is in layer pixels; use
`iScale` (pixels per design pixel) to keep sizes resolution independent.
`iResolution` is the layer size and `iBox` the component box (x, y, w, h) in
layer pixels. `mix` (0-1) is animatable:
`scene.play(title.animate.effect_to("shader", mix=0))`.

Compile errors are raised when the shader is created, with Skia's message
and the failing line.

## Displacement

```python
from faceless_champ import Canvas, DisplacementMap, EffectStack, Scene, Text

scene = Scene(Canvas(1920, 1080, bg="#0E1116"))
heat = EffectStack(displacement=DisplacementMap(amplitude=10, size=90, octaves=3, speed=40))
title = Text("Heat haze", font_size=140, effects=heat, position=(960, 540))
scene.add(title)
scene.play(title.animate.effect_to("displacement", amplitude=0), run_time=1.2)  # settles into place
```

With `map="assets/map.png"` the red/green channels of an image displace x/y
(mid grey means no shift), stretched over the component.

## Lighting (bevel and emboss)

`Lighting` treats a layer's alpha as a height map and shades it with Skia's
diffuse and specular lighting filters. Flat areas keep their color; edges
facing the light brighten and the far edges darken.

```python
from faceless_champ import Canvas, EffectStack, Lighting, Scene, Text

scene = Scene(Canvas(1920, 1080, bg="#0E1116"))
emboss = EffectStack(lighting=Lighting(azimuth=225, elevation=40, bevel=8, depth=5, specular=0.6))
title = Text("CHROME", font_size=200, color="#8FA3BF", effects=emboss, position=(960, 540))
scene.add(title)
scene.play(title.animate.effect_to("lighting", azimuth=315), run_time=2)  # the light swings round
```

- `light="distant"` (default): `azimuth` degrees (0 = from the right, 90 = from
  below, 225 = top-left) and `elevation` (0-90).
- `light="point"` / `"spot"`: placed at `x`, `y` (fractions of the component
  box, may lie outside it) and `height` design pixels above it. A spot aims at
  the box centre with a `cone` half-angle in degrees.
- `bevel` (edge softness, design px), `depth` (negative debosses), `diffuse`,
  `specular`, `shininess` (1-128), `color` (light tint) and `mix` (0-1).

## Morphology (dilate and erode)

```python
from faceless_champ import EffectStack, Morphology, Text

bold = Text("Grow", font_size=120, effects=EffectStack(morphology=Morphology(radius=6)))
thin = Text("Thin", font_size=120, effects=EffectStack(morphology=Morphology(radius=2, mode="erode")))
# scene.play(bold.animate.effect_to("morphology", radius=0))
```

`radius` is in design pixels and is applied in whole output pixels. Dilate
thickens strokes, fills small gaps and merges nearby shapes; erode thins them
and removes fine detail. Morphology runs first, then displacement, lighting and
any `ShaderEffect`, so a dilated shape is also what gets lit.

## Typst math

[Typst](https://typst.app) typesets math with matrices, cases, alignment and
big operators, without a LaTeX installation:

```python
from faceless_champ import Equation

Equation("A = mat(1, 2; 3, 4)", engine="typst", font_size=72)
Equation("integral_0^oo e^(-x^2) dif x = sqrt(pi) / 2", engine="typst")
Equation('f(x) = cases(x^2 &"if" x >= 0, -x &"otherwise")', engine="typst")
Equation("a + #text(fill: red, $x^2$) = b", engine="typst")  # color one term
```

Install the compiler once, either way:

- `pip install typst` (a Python wheel; easiest on Kaggle/Colab), or
- download the `typst` executable from the
  [releases page](https://github.com/typst/typst/releases), put it on `PATH`
  (for example `~/.local/bin/typst`), or set `FC_TYPST=/path/to/typst`.

Compiled SVGs are cached in `~/.cache/faceless_champ/typst` (or
`$FC_CACHE_DIR/typst`), so parallel render workers and resumed renders don't
recompile. `Write(eq)` and `max_width=` work as with the default engine;
`color_map` is MathText-only.

### Symbol-by-symbol math (`MathGlyphs`)

`MathGlyphs` typesets with Typst and returns a Group with one `VectorPath`
per symbol (`eq.glyphs`, left to right), so each symbol can be colored,
revealed or hand-written individually:

```python
from faceless_champ import Draw, MathGlyphs

eq = MathGlyphs("e^(i pi) + 1 = 0", font_size=96, position=(960, 540), outline=True)
eq.glyphs[0].fill = "#FFD166"  # before scene.add
scene.add(eq)
scene.play(*[Draw(g) for g in eq.glyphs], run_time=2)  # outlines draw, then fill in
# or: scene.reveal(*eq.glyphs, stagger=0.06)
```

It needs `backend="skia"` (glyphs are compound paths).

LaTeX to Typst:

| LaTeX | Typst |
|---|---|
| `\frac{a}{b}` | `a/b` or `frac(a, b)` |
| `\sqrt{x}`, `\sqrt[3]{x}` | `sqrt(x)`, `root(3, x)` |
| `\int_0^\infty` | `integral_0^oo` |
| `\sum_{n=1}^{N}` | `sum_(n=1)^N` |
| `\alpha, \pi, \theta` | `alpha, pi, theta` |
| `\begin{bmatrix}1&0\\0&1\end{bmatrix}` | `mat(1, 0; 0, 1)` (`mat(delim: "[", ...)` for brackets) |
| `\vec{v}`, `\hat{x}` | `arrow(v)`, `hat(x)` |
| `\mathbb{R}` | `RR` |
| `\cdot`, `\times`, `\to` | `dot`, `times`, `->` |
| `\text{loss}` | `"loss"` |
