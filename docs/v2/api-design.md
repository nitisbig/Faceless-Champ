# V2 API design and compatibility

Status: original API proposal with M1-M5 implementation follow-up below. Baseline:
`22f3beaccb5a56990bd0974666b7c639a0667a68`, audited 2026-10-20.
The complete current declaration inventory is in the
[audit](architecture-audit.md#public-api-inventory). See
[backend contracts](backend-integration.md) and [migration](migration-plan.md).

Implementation follow-up: [M1](m1-implementation.md), [M2](m2-implementation.md),
[M3](m3-implementation.md), [M4](m4-implementation.md) and
[M5](m5-implementation.md) record the implemented changes and scoped evidence.
The original proposal and audit measurements below retain their dated baseline.

## Three levels of authoring

Keep the established entrypoints rather than add a fourth facade/framework.

| Level | User API | Output / ownership |
| --- | --- | --- |
| Core | Canvas, components, Scene/Sequence/Grid/Layer, animations, `render`, preview helpers | Deterministic composition; Core owns painting/audio/encoding |
| Kit | BuildContext, Video/Segment, blocks, layouts, themes, Project, CompiledVideo | Reusable authoring compiled into Core; no second visual evaluator |
| Agent | AgentProject, plans, discovery, context, review/status | Production evidence and conformance around Kit operations; no model service required |

Advanced projects can keep using Core directly or use Kit domain components inside
ordinary Core scenes without adopting Project configuration. Installing Kit for a
domain does not require using Agent or its project workflow.

### Core example: preserved API

This uses current public APIs and remains the intended basic V2 experience.
The audit parsed examples; it did not execute exports from this document.

```python
from faceless_champ import Canvas, FadeIn, Scene, Text, render

scene = Scene(Canvas(1920, 1080, "#000000"))
title = Text("A deterministic scene", position=(960, 540), font_size=64)
scene.play(FadeIn(title), run_time=0.6)
scene.wait(1.4)

if __name__ == "__main__":
    render(scene, "output/example.mp4", backend="pillow", fps=30)
```

Keep `at()`, `wait_until()`, atomic `play()`, snapshot-on-add, named source cue
lookup, explicit audio, ranges, progress, overwrite protection, and `Path` returns.
Default antialias behavior is unchanged; users can explicitly request another
supported backend/profile. Existing custom renderer parameters remain accepted.

### Kit example: narrated composition

The following build factory retains the current master-clock idiom. It requires
project-owned audio and SRT inputs; they are not generated or retimed here.

```python
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import Heading


def build(ctx):
    video = Video(ctx)
    video.narration(
        audio="audio.mp3",
        subtitles="cue-per-word.srt",
        overlap_tolerance=0.001,
    )
    with video.segment("opening", start=0, duration=4) as segment:
        segment.add(Heading("How the system works"), id="title")
    return video
```

Project remains the entrypoint for configuration, profiles, assets, preparation,
validation, frames, storyboards and export. `Segment.add_core(factory)` remains
the escape hatch for custom Core compositions; factories return fresh components.
Do not make users author JSON render commands or manipulate private Entry objects.

### Agent example: existing production workflow

```python
from facelesschamp_agent import AgentProject

project = AgentProject("my-video")
validation = project.validate()
layout = project.audit_layout()
if layout["status"] == "passed":
    preview = project.preview(start=0, end=3)
```

The caller still authors ordinary Python and inspects evidence. `prepare()` is
explicit; rendering never executes checkpoints, opens a browser or downloads media.
Keep preview/full, structural/media, and visual/editorial review statuses separate.

## Advanced rendering and generic sources

Preserve the current renderer interface:

```python
class Renderer(Protocol):
    def validate(self, node: Renderable) -> None: ...
    def frame(
        self, node: Renderable, time: float, size: tuple[int, int]
    ) -> PIL.Image.Image: ...
```

Existing project-local renderer adapters, including source-time `sample(t)` scenes,
GLSL viewports and dynamic PyVista fields, continue to work. A supplied renderer is
caller-owned. Helpers manage only the renderers they create. Do not require a new
`close()` method or internal compiled-scene type from every existing custom renderer.

Add these public source contracts in Core's proposed `sources.py`, re-exporting
`Viewport` and `RasterSource` through the lazy root. Protocol snippets describe
interfaces; omitted imports/types are illustrative rather than runnable modules.

```python
class RasterSession(Protocol):
    def frame(self, source_time: float) -> PIL.Image.Image: ...
    def close(self) -> None: ...


class RasterSource(Protocol):
    intrinsic_size: tuple[int, int]
    duration: float | None
    fingerprint: str
    requirements: tuple[str, ...]

    def frame_key(self, source_time: float) -> Hashable: ...
    def open(self, size: tuple[int, int]) -> RasterSession: ...


class Viewport(Component):
    def __init__(
        self,
        source: RasterSource,
        *,
        width: float | None = None,
        height: float | None = None,
        source_start: float = 0,
        **component_options,
    ): ...
```

Both width/height are either omitted (intrinsic size) or supplied. Source dimensions
are positive integers; duration is positive finite seconds or `None` for a static
unbounded source; source_start is nonnegative and within a finite source. The
viewport does not advance the Scene cursor automatically. It uses normal component
lifetimes, transforms, masks, opacity and effects.

The descriptor contains immutable inputs/identity, not live native handles. Scene
snapshotting retains source mutation isolation. Renderers open/close sessions keyed
by source identity and target pixel size, with bounded retention. The session owns
those resources and returns independent straight-alpha RGBA/sRGB frames at its
opened size. Pure `frame_key(t)` identifies equivalent content; frame time remains
the requested source time, not a hash/key passed as a timestamp.

Sampling maps component age to `source_start + age`, clamped to the finite source's
terminal state for holds. Domain adapters preserve their existing endpoint policy;
composition left-limit handling remains in the shared composition evaluator. No
universal FPS quantization is applied. Prepared browser captures quantize through
their own frame keys; scientific sources may remain continuous.

Preserve existing viewport resolution behavior: target sampling size follows
authored viewport size and output canvas density, so an animated ancestor scale
does not create a new VTK session every frame. World transforms are applied by the
compositor. Measurement reads intrinsic/authored dimensions without opening sessions.

Example of the proposed generic API, with a source supplied by an integration:

```python
from faceless_champ import Canvas, Scene, Viewport


def build_view(source):
    view = Viewport(source, width=1280, height=720, position=(960, 540))
    return Scene(Canvas(1920, 1080)).add(view).wait(3)
```

Native PyVista/Trimesh/build123d objects remain accessible through explicit optional
integration functions and immutable inspection copies, outside generic snapshots.
Custom GLSL/context interop continues through custom Renderer implementations;
V2 does not promise safe shared-context interop across every native library.

## Animation extension points

Remove `Chart`, map-property and other domain checks from generic timeline code
only after their owning modules can preserve the same validation.

```python
class Component:
    def validate_animation(self, property: str, value: object) -> None: ...


class Animation:
    def resolve(self, state: Mapping[str, object]) -> Animation: ...
```

The default component hook validates Core-owned properties. A domain component
handles its own declared state keys and delegates Core keys to the default hook;
unknown keys are rejected. Scene preparation calls validation for resolved starts,
targets and keyframes before publishing any changes. Domain builders such as
Chart's data builder reuse numeric-tuple interpolation and supply their own shape,
range and structure validation.

`Animation.resolve(state)` defaults to a detached description with unchanged
semantics. Domain builders can normalize requests against the current evaluated
state at scheduling time (for example shortest geographic rotation), returning
ordinary Core animation data. It must be pure and cannot mutate the component,
scene or input animation. Core then resolves its normal transform-relative values,
validates the whole call, and certifies Spring tracks. Repeats/ping-pong retain the
existing resolved-value and endpoint rules. This avoids a new property descriptor
hierarchy or another animation engine.

## Kit production service additions

Add operations on the existing `CompiledVideo`, keeping the exact compiled object
that Agent validated instead of rebuilding or reproducing Core calls in Agent.

| Proposed method | Result / contract |
| --- | --- |
| `frame(time, *, size, backend="pillow", antialias=1, gpu=None, renderer=None)` | PIL image, original source time, caller-owned supplied renderer |
| `save_frame(time, output, *, size, backend="pillow", antialias=1, gpu=None, renderer=None, overwrite=False)` | Operation result mapping |
| `storyboard(samples, directory, *, size=None, columns=3, backend="pillow", antialias=1, gpu=None, renderer=None, overwrite=False)` | Operation result mapping, same source-time samples |
| `export(output, *, settings, start_time=0, end_time=None, progress=None, renderer=None, overwrite=False, cancel=None)` | Operation result mapping; Core remains authoritative for encoding/audio/publication |

Operation results use existing dictionaries rather than another public model
hierarchy: `output` (Path), `rendering` (actual backend/version/font/device identity),
`source_range` (two source endpoints for MP4; `None` for still/contact sheet), and
`settings` (effective JSON-compatible settings, including output dimensions/fps
where applicable). Identity is captured from the actual session before close.
Agent adds record IDs, checksums, plan/build fingerprints, expected media values,
verification and review status; these do not move into Core.

Existing Project methods keep their signatures/Path results and delegate to these
operations after building/resolving a profile. ExportProgress can be re-exported
by Kit without duplicating it. Kit exposes thin `media_probe(path)`,
`read_subtitle_cues(text)` and `public_capabilities()` facades over Core media,
raw cue parsing and static capability/resource metadata, so Agent need not own a
second runtime integration. Core's raw `parse_srt_cues(text)` returns immutable
SubtitleCue records; SubtitleTrack applies overlap tolerance, while Agent retains
its own byte/cue limits and permissive source-overlap policy.

## Import and data migration map

| Current surface | V2 surface / treatment |
| --- | --- |
| Core shared primitives, animation, Scene/compositions, render/preview | Preserve lazy root imports and existing shared module aliases |
| `faceless_champ.charts` / root chart exports | `facelesschamp_kit.charts`, retaining class names/data semantics |
| `faceless_champ.maps`, `flags` / root geographic exports | `facelesschamp_kit.maps`, including Flag/lookup helpers |
| `faceless_champ.coding`, `coding_workspace` | `facelesschamp_kit.coding` |
| `faceless_champ.playground` | `facelesschamp_kit.playground`; update checkpoint runtime import strings too |
| `faceless_champ.web` | `facelesschamp_kit.web`; prepared assets remain browser-free |
| `faceless_champ.flow` | `facelesschamp_kit.diagrams`; existing Flow class names retained initially |
| `faceless_champ.os_ui` | `facelesschamp_kit.desktop`; existing semantic class names retained |
| Core ArchMesh/ArchCamera/ArchPart/ArchStyle and native geometry bridge | Explicit Core `integrations.pyvista`, `.build123d`, `.trimesh`; retain low-level function/type names at documented destinations |
| ArchChamp/ArchScript/labels/dimensions/designs, blueprint/mechanism recipes | `facelesschamp_kit.engineering`; low-level Core camera/snapshot/part/style types re-exported there for convenient composition |
| ChessChamp/Script/Theme/Assets, Kit ChessBoard/starter | Removed; frozen V1 source route or separately authored source adapter |
| `Block.compose`, `BlockBuild`, Segment handles, Project/AgentProject | Preserve; domain imports/internal rendering delegation change |

Deprecation precedes physical movement. Shared Core aliases stay within Core;
removed domain imports must not lazily import Kit. A V2 error/migration guide may
identify a replacement, but Core must not acquire a Kit dependency to emulate V1.

Keep schema-1 prepared captures, scripts/plans and reports readable where their
meaning remains unchanged. Readers may normalize into current internal records;
do not silently rewrite source files. A breaking persisted shape requires a new
schema version, explicit converter, fixture tests and retained original. Any V2
implementation/package/font change naturally invalidates earlier fingerprinted
render/review evidence; preserve that history and require new verification.

CLI names remain `faceless-champ`, `fc-kit`, `fc-agent`. Preserve explicit preparation,
short-preview entrypoint defaults, `--full`, source ranges, independent fps/quality
overrides, structured errors and overwrite protection. Proposed API additions do
not imply V2 is installed or examples have been rendered.
