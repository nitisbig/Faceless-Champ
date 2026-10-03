# Authoring guide

## Layout and timing

Think in design pixels, independent of output resolution. Place a centered title at
`(960, 540)` on the default canvas. Use `anchor="top_left"` for labels and explicit
image boxes. Scale multiplies component dimensions; rotation is clockwise and
always happens around the center. Layers sort by `z_index`, then insertion order.

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
