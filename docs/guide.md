# Authoring guide

## Narrated previews and image reservations

Keep a continuous narration/caption overlay at zero when composing multiple
chapters. Build the visuals with cue-derived durations in `Sequence(crossfade=0)`
and combine them with the overlay using `Layer`. Crossfades shorten a sequence;
account for that overlap when synchronizing to narration. Component fades within
a chapter leave the source clock intact.

```python
from faceless_champ import ImageSlot, SubtitleTrack

track = SubtitleTrack.from_srt("cue-per-word.srt", overlap_tolerance=0.001)
scene.add(ImageSlot("image/1.png", width=800, height=500, fit="cover",
                    position=(960, 540)))
scene.render("output/detail-preview.mp4", start_time=12, end_time=18,
             width=960, height=540, fps=15, antialias=1)
```

Opt into overlap tolerance only when the source requires it. Cue timestamps remain
unchanged, and default parsing remains strict. Use original cue indices to schedule
visuals, including extremely short cues; do not replace the word track with a
retimed phrase transcript. Captions already group words into readable phrases.

ImageSlot's auto mode shows a labeled box until the path exists. Force
`mode="placeholder"` when checking placement, or `mode="required"` when all images
should be supplied. Run with a fresh renderer after adding/replacing files.
Placeholder styling belongs to the component; an example CLI should only select
the mode and supply its scene paths. Corrupt existing files are errors.

For long narration, `PillowRenderer(caption_cache_mb=32)` bounds highlighted caption
sprites separately from the scene-frame budget. Layouts reuse word measurements.
Set `caption_cache_mb=0` to compare uncached output. The Country Economy project
demonstrates these APIs with short previews and a complete source-clock composition.

## Layout and timing

Think in design pixels, independent of output resolution. Place a centered title at
`(960, 540)` on the default canvas. Use `anchor="top_left"` for labels and explicit
image boxes. Scale multiplies component dimensions; rotation is clockwise and
always happens around the center. Layers sort by `z_index`, then insertion order.

Use measured layout helpers before adding components. For an icon with a label,
call `label.next_to(icon, direction="down", gap=20)`, then
`Group(icon, label).move_to(960, 540)`. Arrange several groups with
`Group(*cards).arrange(gap=40)` or align a heading using
`heading.align_to(diagram, edge="left")`. These helpers account for font metrics,
rotation, and scale; they do not automatically wrap text or resolve every overlap.

Group diagrams before `add()`. Moving or scaling a group leaves its member
coordinates intact, so independent member animation targets use those original
coordinates. Parent transforms apply afterward. A group can animate at the same
time as its members, and nested groups preserve local stacking and timing.
See [the group API](api.md#groups-and-measured-layout) for precise rules.

Each `play()` is a timeline step. Multiple arguments animate together; separate calls
animate sequentially. `wait()` creates a hold. Direct style changes after `add()`
are not scheduled edits: create a new component or use its animation builder.

```python
from faceless_champ import Scene, Text, FadeIn, FadeOut

class Caption(Scene):
    def construct(self):
        text = Text("Build once. Render at any resolution.", position=(960, 540))
        self.play(FadeIn(text), run_time=0.4)
        self.wait(1.2)
        self.play(FadeOut(text), run_time=0.4)
```

## Motion presets

Pair icons with their labels and play their entrance animations concurrently:

```python
from faceless_champ import PopIn, SlideIn, Pulse, Wiggle, SlideOut, ZoomOut

self.play(PopIn(icon), SlideIn(label, direction="up"), run_time=0.5)
self.play(Pulse(icon), Wiggle(label, angle=3), run_time=0.6)
self.play(SlideOut(icon), ZoomOut(label), run_time=0.35)
self.remove(icon, label)
```

Zooms and pops affect a component, or the whole hierarchy when applied to a Group.
Slide direction describes movement;
an upward entrance starts below the resting position. Scale factors are relative
to the evaluated timeline state, so emphasis effects still return to the right
size after earlier scaling. Shake and wiggle also return to the current transform.
Entrances animate opacity together with movement; do not also apply FadeIn to the
same component in that call. Typewriter and Draw animate different properties and
may be combined with a motion preset. Explicit `rate_func` overrides preset easing.

The good-math scene exercises every preset and all four animation builder methods.
Its `ENTRANCES`, `EXITS`, and `EMPHASES` constants select the motion rotation.
Every render writes `output/animations.json` with effect names, affected visuals,
and timings. Late narration cues use shorter entrances to fit their scene boundary.

## Syncing a narration to word cues

```python
from faceless_champ import Captions, SubtitleTrack

track = SubtitleTrack.from_srt("cue-per-word.srt")
self.add(Captions(track, position=(960, 1008)))  # Add at zero for audio timestamps.
self.add_audio("audio.mp3", start=0)
with self.at(track.cue(4).start):
    self.play(FadeIn(Text("a student", position=(960, 540))), run_time=0.24)
```

Use original SRT cue numbers as event markers. `at()` lets you schedule independent
objects at absolute times without accumulating the lengths of preceding animations.
Each block restores the furthest authoring cursor. Author animations of the same
property in chronological order; overlapping or earlier insertions are rejected.
Use `wait_until()` to finish at an absolute time. Fade an object out, then `remove()`
it to end its lifetime. Reintroduce it with a new instance.

Captions use short phrases with word highlighting when supplied word-level cues.
They preserve all text, including transcript artifacts. Source times remain exact;
video frames sample those times at the requested frame rate, so a cue shorter than
one frame may not appear in the video. Increase fps when those short cues matter.

See `training project/good-math/scene/story.py` for the complete narrated example.

## Sequence and grid

```python
from faceless_champ import Canvas, Grid, Sequence

# Each expression creates a separate instance of Caption from above.
panels = Grid(*(Caption() for _ in range(6)), rows=2, columns=3,
              gap=16, canvas=Canvas(bg="#101b30"))
video = Sequence(Caption(), panels, Caption(), crossfade=0.4)
video.render("output/composition.mp4", quality="ql")
```

Changing a built child's duration shifts later children automatically. For subclassed
scenes, use `child.build().wait(1)` to append a hold after construction. Calling
`wait()` before construction prepends time to a lazily constructed scene.
Composition is a tree of scenes and layouts; do not create cycles in `children`.

## Consistent colors and readable equations

Choose a `ColorScheme` and pass the same roles to the formula symbols, graph paths,
and their labels. For instance, use primary for a triangle's horizontal side,
secondary for its vertical side, and tertiary for its hypotenuse. Keep operators
and supporting copy in the scheme's text and muted roles, and use axis/grid roles
for reference lines. A translucent fill can use `with_alpha(scheme.tertiary, .18)`.
The `paper` preset has darker series colors suited to its light surface.

Use `Equation(color_map={"a": scheme.primary, "b": scheme.secondary})` for matching
symbol colors, including Greek keys such as `r"\mu"`. Color maps select individual
glyphs throughout the formula, including letters inside roman text; supply a map
appropriate to that particular expression. The example's `SYMBOL_ROLES` in
`scene/equations.py` makes the assignments explicit.

For readable variable fonts, pass `Text(font=path, font_weight=500)`. Rounded
Polyline caps soften graph endpoints without blurring their geometry. Preview
and export with `antialias=2` for smooth curves and type; raising antialias adds
rendering work. The equation example uses CRF 18 for previews and 16 for final
exports to preserve small symbols.

```bash
uv run --extra equations python 'training project/equation-render/render.py' --color-scheme midnight
uv run --extra equations python 'training project/equation-render/render.py' --color-scheme paper --frames
```

## Audio and imported assets

```python
from pathlib import Path
from faceless_champ import Scene, Image, FadeIn

ASSETS = Path(__file__).resolve().parent / "assets"

class Media(Scene):
    def construct(self):
        self.add_audio(ASSETS / "music.wav", start=0, trim_end=4,
                       volume=0.3, fade_in=0.2, fade_out=0.5)
        self.play(FadeIn(Image(ASSETS / "photo.png", width=1200, height=700,
                               position=(960, 540), fit="cover")))
        self.wait(3)
```

Audio does not advance the visual cursor. Set `start` explicitly when synchronizing
with a known event. A clip's end can extend the scene; it is not implicitly cut to
the last visual command. Grid audio tracks mix together. Sequence crossfades apply
to entire child soundtracks, including nested compositions.

Use font files containing the glyphs you need. The bundled font is suitable for
common Latin text; language shaping support depends on the Pillow build. Set
newlines explicitly; automatic wrapping and advanced typography are outside v0.1.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| FFmpeg/ffprobe missing | Install FFmpeg and ensure both commands are on PATH |
| Unknown encoder `libx264` | Use an FFmpeg build containing the H.264 encoder |
| File already exists | Choose another output or pass `overwrite=True` / `--overwrite` |
| Missing media/font | Check the path; use a path relative to the authoring file |
| Invalid custom dimensions | Supply both dimensions, make them even, preserve aspect ratio |
| Animation overlap error | Combine different properties or use consecutive play calls |
| Crossfade too long | Shorten the fade or lengthen the affected scene |
| Audio starts late | Pass `start=0`; the default is the current cursor |
| Final state flashes or is absent | Add a hold after the final play call |
| Slow high-resolution render | Preview at ql, use antialias=1, or choose a faster preset |

Failed exports preserve existing files and remove temporary media. Encoder stderr
is included in the raised error. Exports are published only after FFmpeg succeeds.

## Validation workflow

Run `uv run pytest -q` for unit and FFmpeg integration tests. Then run
`uv run python examples/render_all.py` for three 720p showcase exports, preview
frames, audio measurements, and short 1080p/4K checks. Inspect the previews and
videos under `output/`; machine checks cannot establish aesthetic quality.

## Logos and in-memory images

```python
from pathlib import Path
from faceless_champ import Image

logo = Image.from_source(
    Path(__file__).parent / "logo" / "openai.png",
    width=64, height=64, trim=True, tint="#C15F3C",
    position=(200, 300),
)
# Encoded data and Pillow images use the same API:
# logo = Image.from_source(png_bytes, width=64, height=64)
```

Use `trim` for uneven transparent margins and `tint` for monochrome designs.
Retain original colors by omitting `tint`. Do not pass URLs; download assets
explicitly before authoring if needed. Keep image paths relative to the scene's
file, rather than the process working directory.

The 30-second `training project/ai-comapny-graph/render.py` example uses five
provided logos, a white/terracotta palette, continuous time-revealed paths, and
keyframed markers and counters. Its user counts and relative origins are expressly
fictional. The persistent on-screen disclosure must remain when changing its
illustrative values. Use `--preview`, `--frames`, or `--frame 15` for feedback.
