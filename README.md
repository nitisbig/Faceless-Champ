# Faceless Champ

A Python library for creating animated videos from text, shapes, images, and audio.
Inspired by Manim's scene authoring model, built for general video components.

## Install

Python 3.12+ and FFmpeg/ffprobe are required. On Ubuntu:

```bash
sudo apt install ffmpeg
uv sync
```

For use in another environment, install from this checkout with `pip install .`.
FFmpeg must include the `libx264` encoder. The Python package uses Pillow and bundles
a DejaVu Sans font with its license; no system font setup is needed.

## Your first scene

Save this as `hello.py`:

```python
from faceless_champ import Scene, Text, Circle, Typewriter, FadeIn

class Hello(Scene):
    def construct(self):
        title = Text("Hello, world!", font_size=100, position=(960, 400))
        dot = Circle(60, fill="#48e0cb", stroke=None, position=(400, 700))
        self.play(Typewriter(title), FadeIn(dot), run_time=1.5)
        self.play(dot.animate.move_to(1520, 700), run_time=1)
        self.wait(0.5)
```

```bash
uv run faceless-champ render hello.py Hello -o output/hello.mp4 -q ql
```

Or render directly in Python:

```python
Hello().render("output/hello.mp4", quality="ql", overwrite=True)
```

The default canvas is 1920×1080 design pixels. Exporting at 720p scales everything,
including font sizes, strokes, and positions. Component anchors default to their
center; canvas coordinates start at the top-left. Positive Y points down.

## Example videos

All examples generate their own assets locally; no downloads or accounts are needed.

```bash
uv run faceless-champ render examples/showcase.py AnimatedTitle -o output/animated_title.mp4 -q ql
uv run faceless-champ render examples/showcase.py media_sequence -o output/media_sequence.mp4 -q ql
uv run faceless-champ render examples/showcase.py six_panel_canvas -o output/six_panel_canvas.mp4 -q ql
```

Use `--overwrite` to replace existing outputs. To render all examples, extract preview
frames, and check their media metadata and audio, run:

```bash
uv run python examples/render_all.py
```

## Narrated training project

The [good-math project](training%20project/good-math/README.md) follows a supplied
layout reference with serif text, outline icons, and simple diagram animations.
Its 12 visual beats and word highlights use the original SRT timestamps.
Downloaded fonts, icons, and licenses live in the shared `assets/` folders.

```bash
uv run python 'training project/good-math/render.py' --preview
uv run python 'training project/good-math/render.py'
```

The library now includes `SubtitleTrack`, `Captions`, `Icon`, and `Arrow`, plus
`Scene.at()`, `wait_until()`, and `remove()` for narration-driven authoring.
The scene also demonstrates pop, slide, zoom, bounce, spin, pulse, shake, and wiggle
presets alongside fades, drawing, typewriter reveals, and transform builders.
See the [animation API](docs/api.md#scenes-and-animation) for reusable presets.

## Animated equation training project

The [equation-render project](training%20project/equation-render/README.md) presents
ten useful equations in one minute: two 2×2 canvases followed by a 2×1 canvas.
Each equation has a typeset formula, animated diagram, and example. Panels reveal
one at a time, with crossfades between canvases and quiet sound effects.

```bash
uv sync --extra equations
uv run --extra equations python 'training project/equation-render/render.py' --preview
uv run --extra equations python 'training project/equation-render/render.py'
```

This example adds optional `Equation`/`Write` support, `Polyline` paths, rounded
rectangles, padded grids with delayed starts, and transparent `Layer` compositions.
Downloaded Google fonts and Material icons, their licenses, and original sound
effects are stored in the shared `assets/` folders. MathText handles formulas
without requiring a separate LaTeX installation.

Choose `--color-scheme midnight`, `paper`, or `ocean` for coordinated equation,
graph, and canvas colors. Formula symbols share colors with their graph quantities.
The library exposes `ColorScheme`, `Equation(color_map=...)`, variable font
`Text(font_weight=...)`, rounded Polyline caps, and `with_alpha()` for shaded areas.
Unchanged scene frames are reused within a configurable memory budget, reducing
the rendering work during held panels while preserving animation and caption timing.

## Documentation

- [API reference](docs/api.md): components, scenes, animation, composition, and exports.
- [Authoring guide](docs/guide.md): timing, grids, audio, fonts, and troubleshooting.
- [Architecture](docs/architecture.md): extension points and renderer contracts.
- [Agent entry point](llms.txt) and [authoring skill](skills/faceless-champ/SKILL.md).
- [Verification record](docs/verification.md): test and sample-render results.

## Development

```bash
uv sync
uv run pytest -q
uv run ruff check src tests examples
uv run ruff format --check src tests examples
uv build
```

v0.1 exports MP4 using a CPU renderer. Camera animation, video
import, graphical editing, and GPU rendering are future work. Linux is the verified
platform. Animated GIFs are decoded and cached in memory; long or very large GIFs
can consume substantial memory. Video frames are streamed rather than accumulated.

### Data-driven charts

Render and animate bar, line, scatter, histogram, heatmap, network, vector-field,
Sankey, and pie charts directly from Python data. Charts support scientific axes,
themes, reveal animations, and transitions between matching datasets, with no extra
dependencies. See the [charting guide](docs/charts.md) and
[renderable showcase](examples/charts/render.py).

### Company-growth training project

The [company-growth example](training%20project/company-growth/README.md) renders
a 45-second light-mode video of the latest US top-ten public-company cohort from
2010 to an October 2026 market-cap snapshot. Its scene imports the main library's
`RankedBarChart` (animated ranks, stable colors, missing data, readable crossing
labels) and `Number` (formatted live numeric animation). Chart fonts are cached
within a fixed limit; dynamic chart and number sprites do not accumulate.

```bash
uv run python 'training project/company-growth/render.py' --preview --overwrite
uv run python 'training project/company-growth/render.py' --frames
uv run python 'training project/company-growth/render.py' --overwrite
```

The project's `render.py` supports preview, full-quality video, individual frames,
storyboards, output paths, and overwrite controls. Source data and methodology are
included for reproducible feedback.

### Image sources and AI audience example

Use `Image.from_source(path_or_bytes_or_pillow_image, trim=True, tint="#C15F3C")`
to import and normalize logos. Existing `Image(path)` calls remain supported.
`Polyline(draw_by="x")` reveals continuous time graphs along their horizontal axis.
See [image source details](docs/api.md#importing-image-sources).

```bash
uv run python 'training project/ai-comapny-graph/render.py' --preview
uv run python 'training project/ai-comapny-graph/render.py' --frames
```

This 30-second example uses five supplied logos and explicitly fictional user
counts. Scene code lives under `scene/`; reusable behavior lives in the main library.
