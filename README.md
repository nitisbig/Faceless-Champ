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

v0.1 exports MP4 using a CPU renderer. Camera animation, charts, video
import, graphical editing, and GPU rendering are future work. Linux is the verified
platform. Animated GIFs are decoded and cached in memory; long or very large GIFs
can consume substantial memory. Video frames are streamed rather than accumulated.
