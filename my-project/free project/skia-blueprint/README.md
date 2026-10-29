# Skia blueprint / CAD study

A silent **60-second** Faceless Champ scene on a pure black canvas. Native Skia
draws the engineering grids, dimension arrows, projected measurements, shaped
labels, cubic schematic curve and section hatching. ArchChamp renders a procedural
PyVista coupling assembly into the same composition. The only text is engineering
notation; there are no headings, subtitles or title cards.

| Source time | Graphics |
| --- | --- |
| 0–18 s | Side and end elevations, dimensions, section station A–A, routed cubic schematic |
| 18–40 s | Orbiting assembly, separated flanges and tie rods, reassembly, Skia dimensions following 3D projection |
| 40–56 s | Moving capped longitudinal cutaway, shaft/bore exposure, hatched flange section with bolt sections |
| 56–60 s | Finished section drawing holds |

The assembly uses millimetres: 120 mm between flange ends, a 96 mm barrel, 12 mm
flange thickness, Ø80 flanges, Ø52 barrel, Ø24 bore, Ø18 shaft and six Ø6 tie rods.
It is an illustrative engineering model, with simplified embedded rod joints.
The routed curve is an independent schematic detail.

Run with the checkout's **native Python environment** from the repository root:

```bash
.venv/bin/python my-project/skia-blueprint/render.py
```

This exports the full 1920 × 1080, 30 FPS scene to
`my-project/skia-blueprint/output/skia-blueprint.mp4`. Use `--quality 4k` for
3840 × 2160, or `--overwrite` when replacing an existing output. Dependencies
are the library's existing `skia` extra and PyVista; the script needs no Docker,
downloads, external models or artwork.

For a short native export or a single source-clock still:

```bash
.venv/bin/python my-project/skia-blueprint/render.py --preview --quality 720p --fps 12 --overwrite
.venv/bin/python my-project/skia-blueprint/render.py --frame 52 --overwrite
.venv/bin/python my-project/skia-blueprint/render.py --range 40 46 --overwrite
```

`--preview` exports a two-second excerpt at source time 24–26 s. `--output PATH`
selects a different destination. Every render/still writes a JSON sidecar with
the source range and backend/dependency/font identity. Generated output is ignored
by Git.

Validation is deliberately limited to representative frames, a two-second encoded
assembly sample, its metadata/full decode, and project lint. The full one-minute
export has not been rendered or verified here.

The cutaway exposed a host-specific VTK/Skia handoff issue: capped clipping could
leave floating-point status that made later native overlays disappear. The core
raster adapter now preserves that environment. Focused checks cover the combined
viewport/overlay and restoration after successful and failed raster production.
