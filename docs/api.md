# API reference

All names below are available from `faceless_champ` unless stated otherwise.

## Canvas and components

`Canvas(width=1920, height=1080, bg="black")` defines design dimensions.
`canvas.aspect_ratio` is derived from width/height. For portrait video, use
`Canvas(1080, 1920)`. Colors use Pillow names or hex notation including alpha.

Every component accepts:

| Argument | Default | Meaning |
| --- | --- | --- |
| `position` | `(0, 0)` | Design-pixel position of the anchor |
| `anchor` | `"center"` | `"center"` or `"top_left"` |
| `scale` | `1.0` | Positive uniform scale |
| `rotation` | `0.0` | Degrees clockwise around the component center |
| `opacity` | `1.0` | Opacity from zero to one |
| `z_index` | `0` | Higher values appear on top; ties preserve addition order |

Configure components before adding them. `component.move_to(x, y)` sets their
initial position and returns the component. Scene addition snapshots their visual
properties; later direct mutations do not alter previously authored content.
Use animation builders for changes over time.

| Component | Specific arguments |
| --- | --- |
| `Text(text, ...)` | `font=None`, `font_size=64`, `color="white"`, `align="left"`, `spacing=8` |
| `Image(path, ...)` | `width=400`, `height=300`, `fit="contain"` or `"cover"` |
| `Rectangle(...)` | `width=200`, `height=200` |
| `Square(side=200, ...)` | Equal width and height |
| `Circle(radius=100, ...)` | Diameter is twice the radius |
| `Triangle(...)` | `width=200`, `height=200`; upward-pointing triangle |
| `Line(length=200, ...)` | Horizontal line; use rotation for other directions |

Shapes accept `fill=None`, `stroke="white"`, `stroke_width=4`.
`None` disables fill/stroke. Lines have no fill. Shape raster bounds include stroke
padding so strokes are not cut off. Top-left anchors refer to that raster box.

Text accepts an explicit TTF/OTF font file; `None` uses the bundled DejaVu Sans.
Newlines are supported; `align` is left, center, or right alignment within multiline
text. There is no automatic wrapping, rich text, font-family lookup, or guaranteed
fallback for characters absent from the selected font.

Images accept PNG, JPG/JPEG, WebP, and GIF files. `contain` preserves the entire image
with transparent padding; `cover` crops to fill. GIF timing starts when the component
is added and loops while visible. Non-GIF formats use their first frame.

## Scenes and animation

Subclass `Scene(canvas=None)` and implement `construct(self)`.
Construction happens once, lazily on `build()`, duration access, or rendering.
You can also use a plain Scene and call authoring methods directly.

| Method | Behavior |
| --- | --- |
| `add(*components)` | Introduce visuals at the cursor; adding the same object twice is a no-op |
| `play(*animations, run_time=1, rate_func=smooth)` | Run animations concurrently and advance the cursor |
| `wait(duration=1)` | Advance the cursor while holding current visuals |
| `add_audio(path, ...)` | Schedule audio without advancing the cursor |
| `build()` | Construct once and return the scene |
| `duration` | Maximum of visual cursor and audio clip end times |
| `render(output, **options)` | Export through the top-level render function |

`play()` automatically adds components that are not already present. Timings are
seconds. Positive animation durations are required. A scene must have positive
duration to export. Objects persist after animations; FadeOut hides them.

Animations: `FadeIn(component)`, `FadeOut(component)`, `Typewriter(text)`, and
`Draw(shape)`. Typewriter reveals Unicode code points; complex grapheme clusters
may appear in stages. Draw traces a shape's outline and displays its fill at the end.

```python
self.play(
    title.animate.move_to(960, 300).scale_to(1.2).rotate_to(5),
    icon.animate.opacity_to(0.5),
    run_time=1.5,
)
```

Builder targets are absolute values. Chain different properties on the same builder.
Two concurrent animations cannot target the same component property. Subsequent
`play()` calls interpolate from the previous target. Built-in easing functions are
`linear` and `smooth`; custom easing is a deterministic callable mapping `[0,1]` to
`[0,1]` with endpoints zero and one.

## Composition

`Sequence(*children, crossfade=0, canvas=None)` places child scenes or compositions
one after another. A zero crossfade produces cuts. Positive crossfades overlap
adjacent visuals and audio; duration is the sum of children minus overlaps.
`starts` and `duration` are calculated from current child durations. Crossfades
must fit each child; interior children need space for both fades without triple
overlap. Children are proportionally fitted into the sequence canvas, which
inherits the first child's canvas unless supplied explicitly.

`Grid(*children, rows=2, columns=3, canvas=None, gap=0)` fills cells in row-major order.
Children start at zero and remain clipped to their cells; unused cells show the
canvas background. The default grid canvas is 1920×1080. Gap uses design pixels.
Duration is the longest child duration; shorter children hold their final visual
state, while their audio ends. Letterboxing preserves child aspect ratios.

## Audio

`scene.add_audio(path, start=None, trim_start=0, trim_end=None, volume=1,
fade_in=0, fade_out=0)` accepts WAV, MP3, and M4A.

- `start=None` means the current visual cursor; `start=0` means the scene beginning.
- Trim times refer to the source. `trim_end=None` uses the source duration.
- Fade lengths refer to the trimmed clip. Audio can extend the scene duration.
- Multiple tracks mix additively, with no automatic normalization. Reduce volumes
  to prevent clipping when summing loud tracks.
- Exports with audio use 48 kHz stereo AAC at 192 kbit/s. Exports without clips have
  no audio stream. Silence pads audio to the video duration.

## Rendering and settings

`render(node, output, *, settings=None, renderer=None, overwrite=False, **options)`
returns the absolute output `Path`. Pass either `ExportSettings(...)` or its fields
as keyword options, not both.

| Setting | Default | Values |
| --- | --- | --- |
| `quality` | `"qh"` | `ql`/`720p`, `qh`/`1080p`, `qk`/`4k` |
| `width`, `height` | `None` | Both required for custom resolution; positive even integers |
| `fps` | `30` | Positive finite frame rate |
| `crf` | `18` | Integer 0–51; lower values increase quality and file size |
| `preset` | `"medium"` | x264 presets from ultrafast through veryslow |
| `antialias` | `2` | Supersampling factor 1, 2, 3, or 4 |

Quality presets set the shorter dimension to 720, 1080, or 2160 and preserve aspect
ratio, rounding to even dimensions. Explicit dimensions override preset resolution
and must preserve the design aspect ratio to rounding tolerance.

Frames sample times `i / fps` for `ceil(duration * fps)` frames. Duration is rounded
up by less than one frame; the exact endpoint is not an additional output frame.
Add a short `wait()` if the final animation state must remain visibly on screen.

The CLI accepts the same settings as flags, plus `--overwrite`:

```bash
faceless-champ render example.py SceneOrFactory -o output.mp4 \
  --quality ql --fps 30 --crf 18 --preset medium --antialias 2
```

The named symbol can be a Scene class, an existing composition, or a zero-argument
factory returning one. Python files execute normally; resolve local assets relative
to `Path(__file__).parent` for independence from the current working directory.
