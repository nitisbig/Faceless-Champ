# facelesschamp-kit

The current kit requires **faceless-champ>=2.0.0rc1,<3.0.0**. It offers code editors and prepared playgrounds, local HTML walkthroughs, offline OS tutorials, and scripted FlowChamp diagrams alongside the original blocks and whiteboard recipes. See the [complete block and starter catalog](docs/catalog.md) and [agent reference](llms.txt).

For coding projects, preparation is explicit:

```bash
fc-kit init lesson --template coding-concept
cd lesson
fc-kit prepare main
fc-kit validate main
fc-kit preview main -o output/preview.mp4
```

Preparation executes trusted authored code. Ordinary build, validation, inspection, and rendering replay prepared assets. Run `prepare` again after changing sources, bindings, input, timing, or preparation settings; `--refresh` forces re-execution.

A structured Python video framework built on the independent **faceless-champ** engine.
Version **2.0.0rc1** is a local release candidate, not a published release. Python 3.12+ and FFmpeg/ffprobe with libx264 are required for exports.

## Install and start

Install the two wheels built from these repositories into your environment:

```bash
python -m pip install /path/to/faceless_champ-2.0.0rc1-py3-none-any.whl /path/to/facelesschamp_kit-2.0.0rc1-py3-none-any.whl
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

The base Core dependency installs only Pillow. Select `facelesschamp-kit[3d]` for
ArchChamp, or `cad`, `geometry`, or `geometry-advanced` for those preparation APIs;
each includes the PyVista conversion dependencies. For local wheels, request the
extra on the Kit wheel path (for example `/path/to/facelesschamp_kit-2.0.0rc1-py3-none-any.whl[3d]`)
and supply the matching Core wheel in the same install command. Existing Arch
projects must declare the extra when recreating their environment. Doctor reports
3D packages as optional; declared missing project requirements still fail.

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

Create a whiteboard video with `fc-kit init my-board --template whiteboard-basic`, or import
`whiteboard_basic` and `WhiteboardScene` from `facelesschamp_kit.templates`. Ordered paths, lines, arrows, rectangles,
and circles draw sequentially, hold, then clear between scenes. Recipes support explicit durations and original narration
cue windows. The returned `Video` remains editable. See the [whiteboard guide](docs/whiteboard.md) for examples and timing.

Install `facelesschamp-kit[maps]` for maps or `[equations]` to forward Core equations. Use explicit Python imports for custom blocks and templates. The V2 major-line compatibility range is `faceless-champ>=2.0.0rc1,<3.0.0`; only versions actually tested are claimed in verification records.

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

## Coding playgrounds

Animate source edits beside real web output, car/object illustrations, or backend/AI data.
Prepare checkpoints explicitly, then render without executing code. See the [CodingChamp playground guide](docs/coding-playgrounds.md).

### FlowChamp

`FlowCanvas` fits scripted diagrams into kit layouts. Start with `fc-kit init my-flow --template flowchamp`; see [FlowChamp](docs/flowchamp.md).

Use ArchCanvas or the arch-design recipe for fitted technical 3D designs. Scaffold with `fc-kit init my-design --template archchamp`. Register files as mesh assets; declare external tools in project pyproject.toml with uv add. Project.dependencies() and doctor check installed requirements without installation. See [ArchChamp](docs/archchamp.md).

Use the [premium collection](../examples/README.md) for current scene references.
Reusable package starter templates remain available; draft styling awaits approval.

## Optional GPU graphics

Install `facelesschamp-kit[gpu]` and set a profile backend to `moderngl` or `auto`. Nested `[profiles.final.gpu]` options configure resources. `EffectBlock`, `ProceduralBackdrop`, and `ParticleBackdrop` use public Core APIs. `fc-kit --json doctor --gpu` explicitly probes EGL; reports record the renderer actually used. See the Core [ModernGL guide](../docs/moderngl.md).

## V2 production candidate

Core, Kit and Agent are coordinated at `2.0.0rc1`. Domain authoring belongs to Kit;
Core stays standalone. Kit production methods reuse a compiled video, and Agent
adds verification and review evidence. See the [M5 migration guide](../docs/v2/m5-migration.md)
and [implementation evidence](../docs/v2/m5-implementation.md).
This is a local candidate; publication and untested platform certification are separate.
