# Faceless Champ

A Python video engine for developers and AI agents. Compose deterministic scenes
with components, measured layouts, animation timelines, local assets, narration,
and FFmpeg exports.

## Install

Python 3.12+ and FFmpeg/ffprobe are required. From this checkout:

```bash
python -m pip install -e '.[coding]' -e ./facelesschamp-kit -e ./facelesschamp-agent
```

Use optional extras for chess, maps, equations, web capture, and prepared playgrounds
when those capabilities are needed. Browser/checkpoint preparation is explicit;
ordinary playback reuses prepared assets.

Optional [Skia rendering](docs/skia.md) adds native vectors, Bézier paths, shaped
typography and retained gradient surfaces: install `faceless-champ[skia]`, select
`backend="skia"`, and use `antialias=1`. Pillow remains the default.

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
- [Charts](docs/charts.md), [maps](docs/maps.md), [ChessChamp](docs/chesschamp.md)
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

Structural checks, rendered-media verification, and visual approval are separate.
See [verification status](docs/verification.md). No new example export is claimed.

## Optional ModernGL graphics

Install `faceless-champ[gpu]` and select `backend="moderngl"` for headless GPU compositing, bloom/glow/blur, procedural backgrounds, particles and transitions. `backend="auto"` selects a compatible renderer without omitting effects. Pillow remains the default. See [ModernGL](docs/moderngl.md) and its [verification status](docs/moderngl-verification.md).

## Optional CAD and geometry

Build123d CAD preparation, Trimesh processing, analytic mechanisms and CAD-derived
blueprints extend ArchChamp. Install the cad, geometry or geometry-advanced extra.
See [CAD and geometry](docs/cad-geometry.md) for units, APIs and native/headless use.
