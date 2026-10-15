# facelesschamp-kit

The current kit requires **faceless-champ>=0.1.5,<0.2.0**. It offers code editors and prepared playgrounds, local HTML walkthroughs, offline OS tutorials, legal chess games, and scripted FlowChamp diagrams alongside the original blocks and whiteboard recipes. See the [complete block and starter catalog](docs/catalog.md) and [agent reference](llms.txt).

For coding projects, preparation is explicit:

```bash
fc-kit init lesson --template coding-concept
cd lesson
fc-kit prepare main
fc-kit validate main
fc-kit preview main -o output/preview.mp4
```

Preparation executes trusted authored code. Ordinary build, validation, inspection, and rendering replay prepared assets. Run `prepare` again after changing sources, bindings, input, timing, or preparation settings; `--refresh` forces re-execution.

Workflow authoring now includes `FlowDiagram`, cue-to-local timing via
`segment.cue_time()`, and delayed/finite placements via `segment.add(at=..., duration=...)`.
TextPanel fits compact cards; ImageCard reserves labeled core ImageSlot boxes.
See [API](docs/api.md), [catalog](docs/catalog.md), and [workflow example](examples/workflow.py).

A structured Python video framework built on the independent **faceless-champ** engine.
Version **0.1.0rc7** is a local release candidate, not a published release. Python 3.12+ and FFmpeg/ffprobe with libx264 are required for exports.

## Install and start

Install the two wheels built from these repositories into your environment:

```bash
python -m pip install /path/to/faceless_champ-0.1.5-py3-none-any.whl /path/to/facelesschamp_kit-0.1.0rc7-py3-none-any.whl
fc-kit init my-video --template silent
cd my-video
fc-kit doctor
fc-kit validate main
fc-kit frame main --time 1 -o output/frame.png
fc-kit storyboard main -o output/storyboard
fc-kit preview main --segment hook -o output/hook.mp4
fc-kit render main -o output/main.mp4
```

`fc-kit --project /absolute/project/path ...` works from an unrelated directory. Paths passed as CLI outputs are relative to the invoking directory; assets and data resolve relative to the project. Default preview covers the first ten seconds; `render` covers the complete video. Output replacement requires `--overwrite`.

The engine owns components, animation interpolation, rasterization, audio mixing, and encoding. The kit owns project conventions, blocks, measured layouts, themes, asset resolution, narration windows, and workflow tools. The core package does not import the kit.

## Author a video

```python
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import MetricCard, Comparison


def build(ctx):
    video = Video(ctx)
    with video.segment("hook", duration=3) as segment:
        card = segment.add(MetricCard(42, "Reusable components"), enter="pop")
        segment.play(card["value"], lambda number: number.animate.value_to(100), at=1, duration=1)
    with video.segment("comparison", duration=5) as segment:
        segment.add(Comparison("Repeated setup", "Shared building blocks"), enter="fade")
    return video
```

A segment without `start` appends after the latest segment end. Use explicit `start` for overlays; placement `z_index` controls stacking. `segment.play` receives a handle and a callback that creates a **core Animation** from its supplied component. Named children are documented in the [catalog](docs/catalog.md).

## Narration

`fc-kit init narrated --template narrated-short` includes a runnable 30-second synthetic speech fixture through installed package resources. A persistent label identifies the sample audio. Replace manifest entries with your own audio/SRT paths and update the original cue indices in `videos/main.py`. The bundled SRT uses sentence cues, not word alignment. The runtime never generates speech or downloads media.

```python
voice = video.narration(
    audio=ctx.assets.audio("voiceover"),
    subtitles=ctx.assets.subtitle("word_cues"),
    markers={"hook": 1, "comparison": 54, "recap": 129},
    captions=False,
)
with video.segment("comparison", window=voice.between("comparison", "recap")) as segment:
    segment.add(Comparison("Before", "After"), enter="fade")
```

`voice.between("recap")` ends at audio duration. Cues retain original timestamps. Narration is placed at master time zero. The last visual segment holds through an audio tail; reports identify that extension. Ranged previews preserve the original audio and visual clock. Captions are opt-in and reserve space before layout.

## Reuse and configuration

The built-ins support portrait `shorts` and `landscape` design canvases, with `midnight`, `light`, `whiteboard`, and `clean-flow` themes. Export profiles scale the selected canvas; switching format rebuilds layout. Text wraps, then shrinks, and fails if it cannot fit at the theme minimum.

[Clean-flow](docs/clean-flow.md) combines a warm gray dot-grid canvas, rounded white shadowed cards, bold packaged DM Sans, charcoal editors, and orange accents. Selecting it enables smooth staggered entrances and outros automatically. `enter=None` or `exit=None` disables a placement side; existing themes keep their previous behavior. A silent 60-second feature tour and preview-first `render.py` live in [training project/clean-flow](../training%20project/clean-flow/README.md).

Create a whiteboard video with `fc-kit init my-board --template whiteboard-basic`, or import
`whiteboard_basic` and `WhiteboardScene` from `facelesschamp_kit.templates`. Ordered paths, lines, arrows, rectangles,
and circles draw sequentially, hold, then clear between scenes. Recipes support explicit durations and original narration
cue windows. The returned `Video` remains editable. See the [whiteboard guide](docs/whiteboard.md) for examples and timing.

- [API and project configuration](docs/api.md)
- [Block catalog and visual examples](docs/catalog.md)
- [Whiteboard template and drawing recipes](docs/whiteboard.md)
- [Architecture and extension contract](docs/architecture.md)
- [Verification and known limits](docs/verification.md)
- [Custom block example](examples/custom_block.py)

Install `facelesschamp-kit[maps]` or `[equations]` to forward the engine extras. Use explicit Python imports for custom blocks and templates. The current minor-line compatibility range is `faceless-champ>=0.1.5,<0.2.0`; only versions actually tested are claimed in verification records.

## Development

```bash
python -m pip install -e '.[dev]' /path/to/core-wheel.whl
pytest
ruff check .
python scripts/build_dist.py
python scripts/catalog.py --output output/catalog
python scripts/verify_media.py --output output/verification
```

The build script uses the active interpreter's setuptools/wheel. `scripts/prepare_sample.py` is an optional developer-only fixture generator requiring espeak-ng; it is not used by rendering or scaffolding.

No public repository or package publication is performed by this implementation. Licensing for project code remains undecided; `LICENSE.pending` records that status rather than granting a license. Core asset licenses remain in the core distribution.

## HTML walkthroughs

`WebWalkthrough` and `WebElement` compose prepared core HTML captures into kit videos.
See [the walkthrough guide](docs/html-to-video.md). Install the optional `web` extra
for browser preparation; playback and block composition do not need Playwright.

### OS UI tutorials

Use `OSWalkthrough`, `FinderWindow`, and `SettingsWindow`, or start with
`fc-kit init my-tutorial --template os-ui`. See [OS UI tutorials](docs/os-ui.md).

### ChessChamp

Start with `fc-kit init my-chess --template chesschamp` after installing `facelesschamp-kit[chess]`. Edit required `data.json` for legal White/Black moves, commentary, arrows, highlights, and optional existing audio. See [ChessChamp](docs/chesschamp.md).

## Coding playgrounds

Animate source edits beside real web output, car/object illustrations, or backend/AI data.
Prepare checkpoints explicitly, then render without executing code. See the [CodingChamp playground guide](docs/coding-playgrounds.md).

### FlowChamp

`FlowCanvas` fits scripted diagrams into kit layouts. Start with `fc-kit init my-flow --template flowchamp`; see [FlowChamp](docs/flowchamp.md).

FlowCanvas inherits neutral strokes from the theme's muted role. Timed layout warnings
include segment/placement scope and master source times. See the cue-synchronized
[TikTok-like example](../training%20project/tiktok-system-design/README.md) for a complete
composition with a short preview as its default export.

Use ArchCanvas or the arch-design recipe for fitted technical 3D designs. Scaffold with `fc-kit init my-design --template archchamp`. Register files as mesh assets; declare external tools in project pyproject.toml with uv add. Project.dependencies() and doctor check installed requirements without installation. See [ArchChamp](docs/archchamp.md).
