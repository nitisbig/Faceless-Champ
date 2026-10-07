# Whiteboard videos

`whiteboard_basic` returns an editable kit `Video`. Each scene draws its paths and shapes in order, holds the completed
diagram, and clears at the next scene boundary. It uses the existing engine and requires no extra dependencies or downloads.

## Start a project

```bash
fc-kit init my-board --template whiteboard-basic
cd my-board
fc-kit validate main
fc-kit frame main --time 4 -o output/frame.png
fc-kit storyboard main -o output/storyboard
fc-kit preview main -o output/preview.mp4
fc-kit render main -o output/final.mp4
```

The editable `videos/main.py` contains two five-second scenes using only local geometry. The starter selects landscape,
the whiteboard theme, and no captions. Change `format = "shorts"` in `facelesschamp.toml` for portrait. Preview retains the
existing ten-second limit; final rendering covers the complete video. Existing overwrite protection applies.

## Python recipes

```python
from facelesschamp_kit.blocks import WhiteboardArrow, WhiteboardCircle, WhiteboardDrawing
from facelesschamp_kit.templates import WhiteboardScene, whiteboard_basic


def build(ctx):
    return whiteboard_basic(
        ctx,
        scenes=[
            WhiteboardScene(
                name="connection",
                duration=5,
                drawing=WhiteboardDrawing(
                    drawings=(
                        WhiteboardCircle(center=(250, 500), radius=100),
                        WhiteboardArrow(start=(380, 500), end=(620, 500), color="#2563EB"),
                        WhiteboardCircle(center=(750, 500), radius=100),
                    ),
                ),
            ),
        ],
    )
```

The complete factory interface is:

```python
whiteboard_basic(
    ctx, *, scenes, audio=None, subtitles=None, markers=None,
    captions=None, theme=None, draw_fraction=0.7,
)  # -> Video
```

`WhiteboardScene(name, drawing, label=None, duration=None, start=None, cues=None)` is immutable. Supply a positive duration
for each scene or use a cue window. An omitted start appends after the previous scene. Explicit starts can leave blank gaps;
scenes must remain in chronological order without overlaps, and names must be unique. The last visual board holds through
an attached audio tail using the standard kit behavior.

The first 70% of a scene is divided equally among its drawing elements. Each stroke progresses linearly; the remaining
30% holds the finished board. Set `0 < draw_fraction < 1` to change that split. A later stroke stays completely hidden until
its scheduled start. Changing frame rate does not change the source timeline.

An optional `label` fades in at the scene start and uses the upper 15% of the safe area. Labels wrap and shrink using the
normal theme minimum; text that cannot fit produces a `TEXT_FIT` diagnostic. There is no label or reserved label space by
default. Captions reserve their usual separate bottom area.

## Drawing coordinates and helpers

Import the specifications from `facelesschamp_kit.blocks`:

| Specification | Geometry |
| --- | --- |
| `WhiteboardPath(points, closed=False)` | Two or more distinct points; three for a closed outline |
| `WhiteboardLine(start, end)` | A straight stroke between two points |
| `WhiteboardArrow(start, end, tip_size=18)` | A straight stroke with an arrowhead |
| `WhiteboardRectangle(x, y, width, height)` | Top-left position and dimensions |
| `WhiteboardCircle(center, radius)` | Center and radius |

All accept keyword arguments `color=None` and `stroke_width=5`. Colors default to the theme foreground; shapes have no
fill. Open paths and lines have rounded ends. Stroke widths and arrowhead sizes use source units and scale with the drawing.
The helpers defensively copy point sequences and are immutable, so they can be shared across scenes and builds.

`WhiteboardDrawing(drawings, viewbox=(1000, 1000))` is a reusable composition block. Coordinates start at the top-left and
increase right/down. Geometry must fit inside the viewbox; a circle's entire outline must fit. Dimensions must be finite;
rectangle sides and line lengths are at least one source unit, circle radii at least half a unit, and arrowheads at least
one unit and no longer than their line. Stroke widths are positive. A different viewbox, such as `(1400, 700)`, can suit
a wide diagram.

The complete viewbox, including intentional whitespace, fits uniformly inside the available drawing area. Renderer padding
and arrowheads receive additional room. Switching formats preserves circles and proportions; it does not rearrange the
supplied geometry. Composition creates fresh core components each time. Named children are `stroke-0`, `stroke-1`, etc.
Using the block directly with `segment.add()` displays the completed drawing; the template schedules its animated strokes.

## Narration and original cues

Register user-supplied media in `assets/manifest.json`:

```json
{
  "voice": {"type": "audio", "path": "assets/audio/voice.wav"},
  "words": {"type": "subtitle", "path": "assets/words.srt"}
}
```

In `build(ctx)`, define drawings as above and pass the original SRT cue indices:

```python
return whiteboard_basic(
    ctx,
    audio="voice",
    subtitles="words",
    markers={"opening": 7, "explanation": 19},
    captions=False,
    scenes=[
        WhiteboardScene("opening", first_drawing, cues=("opening", "explanation")),
        WhiteboardScene("explanation", second_drawing, cues=("explanation", None)),
    ],
)
```

Replace those indices with indices that exist in your SRT. Marker indices need not be consecutive. Windows start at the
original cue start times; `None` as the end marker uses the audio duration. Never combine `cues` with `start` or `duration`
on the same recipe. Explicitly timed scenes may coexist with cue-based scenes as long as they do not overlap.

Audio stays at master time zero, including any leading silence. A leading gap before the first cue shows the empty board.
Audio, subtitle asset IDs, and a nonempty marker mapping must be supplied together. `captions=None` inherits the context
setting; `True` enables captions. Existing SRT/audio validation and ranged preview behavior apply.

## Customize and extend

The factory applies the registered `WHITEBOARD` theme and matching canvas background to its supplied context before
building. For custom styling, pass a `Theme` instance:

```python
from dataclasses import replace
from facelesschamp_kit.themes import WHITEBOARD

custom_theme = replace(WHITEBOARD, foreground="#17324D", accent="#F97316")
video = whiteboard_basic(ctx, scenes=scenes, theme=custom_theme)
```

Pass `theme=ctx.theme` to honor the project's configured theme, as the generated starter does. Individual strokes can
override their colors. Updating the context is deliberate, so subsequent segments use the same style and background.

The returned video supports the ordinary kit API:

```python
from facelesschamp_kit.blocks import Heading

video = whiteboard_basic(ctx, scenes=scenes)
video.segment("closing", duration=2).add(Heading("Your closing message"), enter="fade")
return video
```

You can also add explicit overlay segments through `video.segment(start=..., duration=...)`. Template placements use the
IDs `drawing` and, when present, `label`. Existing scene, narration, and asset reports remain available through `Project`.

Version one supports paths and shape outlines. Hand overlays, image tracing/reveals, handwriting fonts, media generation,
and persistent boards across recipe scenes are outside this template's current scope.
