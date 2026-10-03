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
| `Icon(path, ...)` | `size=120`, `color="white"`; square image box, tinted alpha mask |
| `Rectangle(...)` | `width=200`, `height=200` |
| `Square(side=200, ...)` | Equal width and height |
| `Circle(radius=100, ...)` | Diameter is twice the radius |
| `Triangle(...)` | `width=200`, `height=200`; upward-pointing triangle |
| `Line(length=200, ...)` | Horizontal line; use rotation for other directions |
| `Arrow(start, end, ...)` | Two `(x, y)` endpoints; `tip_size=18`; supports `Draw` |

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

Icons use transparent raster assets and retain their original alpha masks; source
RGB colors are replaced by `color`. SVG inputs should be exported to PNG first.
Arrow position and rotation are calculated from its endpoints; ordinary component
transforms can then move, rotate, or scale it. Arrowheads use the stroke color.

## Scenes and animation

Subclass `Scene(canvas=None)` and implement `construct(self)`.
Construction happens once, lazily on `build()`, duration access, or rendering.
You can also use a plain Scene and call authoring methods directly.

| Method | Behavior |
| --- | --- |
| `add(*components)` | Introduce visuals at the cursor; adding the same object twice is a no-op |
| `play(*animations, run_time=1, rate_func=smooth)` | Run animations concurrently and advance the cursor |
| `wait(duration=1)` | Advance the cursor while holding current visuals |
| `time` | Current authoring cursor, in seconds |
| `at(time)` | Context manager for authoring at an absolute scene time; keeps the furthest cursor afterward |
| `wait_until(time)` | Advance to an absolute time; rejects moving backward |
| `remove(*components)` | End visual lifetimes at the cursor; use new instances to reintroduce visuals |
| `add_audio(path, ...)` | Schedule audio without advancing the cursor |
| `build()` | Construct once and return the scene |
| `duration` | Maximum of visual cursor, audio clip ends, and caption track ends |
| `render(output, **options)` | Export through the top-level render function |

`play()` automatically adds components that are not already present. Timings are
seconds. Positive animation durations are required. A scene must have positive
duration to export. Objects persist after animations; FadeOut hides them.

Independent objects may be scheduled out of order with `at()`. Animations of the
same object's property must be authored in chronological order and cannot overlap.
Removal cannot precede the object's start or the end of its authored animations.
Removed objects are excluded from rendering at and after their removal timestamp.

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

## SRT and captions

`SubtitleTrack.from_srt(path)` reads UTF-8/BOM SRT with LF or CRLF line endings.
`SubtitleTrack.parse_srt(text)` parses an in-memory string. Comma and dot timestamp
separators and multiline cue text are supported. Malformed timestamps, duplicate
cue numbers, empty cue text, reversed intervals, overlaps, and out-of-order cues
raise `ValueError`. Tracks contain at least one cue.

`SubtitleCue(index, start, end, text)` is immutable. `track.cues` contains the ordered
cue tuple. `track.cue(index)` looks up an original SRT number; absent numbers raise
`KeyError`. `track.duration` is the last cue's end time. `track.active_at(time)` uses
`start <= time < end`, returning `None` in gaps. Cues are never retimed.

`Captions(track, font=None, font_size=42, width=1440, color="#292724",
highlight_color="#e56c35", future_color="#99938b", max_words=7, max_duration=3,
spacing=8, **component_options)` displays centered phrases, wraps at `width`, and
highlights the active cue. Completed cues use `color`; future cues use
`future_color`. A word-per-cue file highlights words; sentence cues highlight the
whole cue. Phrases break at punctuation and the configured word/duration limits;
an individual cue is kept intact even if it exceeds those limits. A single word
wider than the caption box raises an error; reduce the font size or increase width.

Cue times are relative to the caption component's introduction time. Add it at time
zero for absolute audio timestamps. Adding captions extends the scene to their last
cue, unless explicitly removed earlier. `Captions.phrase_at(time)` and
`track.phrases(max_words=7, max_duration=3)` expose the same phrase segmentation.
Caption lookup is deterministic, including when frames render out of order.

```python
track = SubtitleTrack.from_srt("cue-per-word.srt")
scene = Scene()
scene.add(Captions(track, position=(960, 1000)))
scene.add_audio("audio.mp3", start=0)
with scene.at(track.cue(4).start):
    scene.play(FadeIn(Text("a student", position=(960, 540))), run_time=0.25)
```

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
