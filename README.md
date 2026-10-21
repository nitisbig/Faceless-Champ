# Faceless Champ

A Python video engine for developers and AI agents. Compose deterministic scenes
with components, measured layouts, animation timelines, local assets, narration,
and FFmpeg exports.

## Install

Python 3.12+ is required. The base engine installs only Pillow; FFmpeg/ffprobe
with libx264 are system tools needed for video/audio exports. From this checkout:

```bash
python -m pip install -e . -e './facelesschamp-kit[coding]' -e ./facelesschamp-agent
```

For the standalone engine, use `python -m pip install -e .`. Imports and capability
listing initialize no native engines. ArchChamp now requires an explicit `3d` extra:
`python -m pip install -e '.[3d]'`, or use `facelesschamp-kit[3d]` /
`facelesschamp-agent[3d]` for the higher layers. Existing Arch projects must add this
extra when rebuilding their environment. PyVista is bounded to the tested 0.49
minor series (`>=0.49.1,<0.50`); VTK remains PyVista's dependency.

The `cad`, `geometry`, and `geometry-advanced` extras include the PyVista conversion
stack their ArchMesh results need. Add only the capabilities used by your project.
Core owns native/equation extras. Install Kit extras for maps, highlighted code,
web capture and prepared playgrounds. Domain APIs now live in Kit; see the
[M4 migration guide](docs/v2/m4-migration.md). Browser/checkpoint preparation is explicit;
ordinary playback reuses prepared assets.

Optional [Skia rendering](docs/skia.md) adds native vectors, Bézier paths, shaped
typography and retained gradient surfaces: install `faceless-champ[skia]`, select
`backend="skia"`, and use `antialias=1`. Pillow remains the default.

Custom [raster sources and animation extensions](docs/raster-sources.md) integrate
prepared or scientific frames through `Viewport`, with renderer-owned sessions.
M2 implementation and validation: [docs/v2/m2-implementation.md](docs/v2/m2-implementation.md).
M3 backend convergence and bounded export cancellation:
[docs/v2/m3-implementation.md](docs/v2/m3-implementation.md).
M4 domain ownership and migration: [docs/v2/m4-implementation.md](docs/v2/m4-implementation.md).

Optional [Manim mathematical animation](docs/manim.md) prepares authored Cairo
scenes in an isolated subprocess, then replays verified RGBA frames through the
existing renderers. Install `faceless-champ[manim]` or select a separate Manim
environment. Kit supplies an equation-transformation preset and `ManimCanvas`;
normal playback requires only Pillow and never starts Manim.

## Premium references

The [premium collection](examples/README.md) is the default scene reference for
agents. Its first entry is the [Hello World opening](examples/programming/hello_world/README.md),
a 14.96-second opening with an approved design using CodingChamp, OSChamp,
FlowChamp, clean-flow and spring motion.

```bash
python3 examples/programming/hello_world/render.py --check
python3 examples/programming/hello_world/render.py --render
```

The first command checks construction, narration placement, input checksums and
sampled geometry. The second explicitly renders 1080p/60. The user approved its
design; the agent has not verified a full export. Previous standalone demos and
training data were removed; package starters and reusable library assets remain.
See the [approved template collection](templates/README.md) for editable defaults.

## Authoring layers

- **Core:** scenes, components, interpolation, rendering, audio mixing and encoding.
- **Kit:** projects, blocks, layouts, themes, asset resolution and narration windows.
- **Agent:** capability discovery, plans, diagnostics and fingerprinted evidence.

Keep ownership flowing from project to kit to core. Scene content stays local;
promote reusable design only after review and approval.

## Guides

- [Authoring guide](docs/guide.md) and [API reference](docs/api.md)
- [CodingChamp and clean-flow workspace](docs/coding.md)
- [OSChamp](docs/os-ui.md), [FlowChamp](docs/flowchamp.md), [ArchChamp](docs/archchamp.md)
- [Motion and spring easing](docs/motion-graphics.md), [gradient surfaces](docs/premium-effects.md)
- [Narration](docs/narration.md), [HTML capture](docs/html-to-video.md), [prepared playgrounds](docs/coding-playgrounds.md)
- [Kit](facelesschamp-kit/README.md), [agent](facelesschamp-agent/README.md), [local website](website/README.md)
- [Project atlas](project-map/README.md)
- [Agent core reference](llms.txt) and [kit reference](facelesschamp-kit/llms.txt)

## Checks

Run package suites separately:

```bash
python -m pytest tests -q
python -m pytest facelesschamp-kit/tests -q
python -m pytest facelesschamp-agent/tests -q
```

Run source suites in an environment containing their optional capabilities. The
standalone wheel check uses a separate fresh environment containing only the Core
wheel and Pillow. Set `FC_MINIMAL_PYTHON` to that environment's Python when running
`tests/test_minimal_install.py`; see the [M1 verification record](docs/v2/m1-implementation.md)
for build commands and the fixed-stack rendering checks.

Structural checks, rendered-media verification, and visual approval are separate.
See [verification status](docs/verification.md). No new example export is claimed.

## Optional ModernGL graphics

Install `faceless-champ[gpu]` and select `backend="moderngl"` for headless GPU compositing, bloom/glow/blur, procedural backgrounds, particles and transitions. `backend="auto"` selects a compatible renderer without omitting effects. Pillow remains the default. See [ModernGL](docs/moderngl.md) and its [verification status](docs/moderngl-verification.md).

## Optional CAD and geometry

Build123d CAD preparation, Trimesh processing, analytic mechanisms and CAD-derived
blueprints extend ArchChamp. Install the cad, geometry or geometry-advanced extra.
See [CAD and geometry](docs/cad-geometry.md) for units, APIs and native/headless use.

## V2 production candidate

Core, Kit and Agent are coordinated at `2.0.0rc1`. Domain authoring belongs to Kit;
Core stays standalone. Kit production methods reuse a compiled video, and Agent
adds verification and review evidence. See the [M5 migration guide](docs/v2/m5-migration.md)
and [implementation evidence](docs/v2/m5-implementation.md).
This is a local candidate; publication and untested platform certification are separate.

## Repository layout

Core remains at `src/faceless_champ/`; Kit and Agent are independently packaged in
`facelesschamp-kit/` and `facelesschamp-agent/`. Domain implementations now live
inside Kit. The [V2 layout guide](docs/v2/repository-layout.md) maps each directory
and distinguishes intentional migration notices from disposable generated caches.
The [offline project atlas](project-map/index.html) shows current ownership and
historical milestones. User projects, design references and render evidence stay
in their existing directories.
