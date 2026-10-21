# M4 migration: domain ownership and ChessChamp retirement

M4 is an unreleased V2 source migration. Install Core, Kit and Agent from the same
checkout (or the matching local wheels). Published V1 packages are not substitutes
for the paired M4 implementations. Coordinated release versions and dependency
bounds are M5 work; no release or V1 maintenance announcement was published here.

## Imports

Generic scenes, animation, text, images, paths, effects, timelines, layout,
renderers, raster-source contracts and FFmpeg exports remain in `faceless_champ`.
Domain authoring now belongs to Kit:

| Previous module/API | V2 owner |
| --- | --- |
| Core chart classes, Axis, ChartStyle, ChartReveal | `facelesschamp_kit.charts` |
| EarthMap, OutlineMap, SatelliteMap, supported_countries | `facelesschamp_kit.maps` |
| Flag, flag_path, supported_flags | `facelesschamp_kit.maps.flags` |
| CodingChamp, CodeTheme, CodeReveal | `facelesschamp_kit.coding` |
| CodeWindow, CodeWorkspaceDesign | `facelesschamp_kit.coding.workspace` (also available from `coding`) |
| Core `flow` package | `facelesschamp_kit.diagrams` |
| Core `os_ui` package | `facelesschamp_kit.desktop` |
| Core `playground` and `web` packages | `facelesschamp_kit.playground`, `facelesschamp_kit.web` |
| ArchChamp, ArchScript, ArchLabel, ArchDimension | `facelesschamp_kit.engineering` |
| CAD presets, blueprint authoring | `facelesschamp_kit.engineering.models`, `.blueprint` |
| Mechanism convenience function | `facelesschamp_kit.engineering.mechanisms` |
| ArchMesh, ArchPart, ArchStyle, ArchCamera, ArchDataError | Core `faceless_champ.integrations.pyvista`; existing Core root names remain |
| Core CAD/mesh conversion functions | `faceless_champ.integrations.build123d`, `.trimesh` |
| Native dependency metadata/probes | `faceless_champ.integrations.dependencies` |

The 52 moved public names are also available from the Kit root. Their class/function
names and non-chess authoring semantics are retained. For example:

```python
from faceless_champ import Canvas, Scene, render
from facelesschamp_kit.charts import BarChart, ChartReveal
from facelesschamp_kit.engineering import ArchChamp, ArchScript
from faceless_champ.integrations.pyvista import ArchMesh, ArchPart
```

Core's old domain modules raise actionable migration errors. Core never imports
Kit to emulate the old facade. The old `faceless_champ.arch` package retains only
Core-local geometry aliases; engineering authoring imports must change.
`component.animate.data_to(...)` remains available through the component's
`transition_data()` hook; ChartReveal belongs to Kit.

## Installation and assets

```bash
python -m pip install -e . -e './facelesschamp-kit[coding]' -e ./facelesschamp-agent
```

Core's only required dependency remains Pillow. Core owns `3d`, `cad`, `geometry`,
`geometry-advanced`, `gpu`, `skia`, `effects` and `equations` extras. Kit owns
`coding` (Pygments), `maps` (NumPy), `web` (Playwright) and `playground`
(Pygments/Playwright); Agent forwards those authoring extras. Native forwarding
remains available through Kit and Agent. Chromium installation and all browser/
checkpoint execution remain explicit preparation steps. Prepared playback stays
offline and does not require Playwright.

Country data, Earth texture, flags, networking artwork, licenses and schema are
packaged with their owning Kit domain. Shared fonts remain Core assets. Use
`flag_path()`, `FlowDesign.asset_paths`, or package resources instead of old
Core/root artwork paths. Exactly matching root artwork duplicates were removed;
source/provenance documents and differing source files were retained. No project
artwork, audio, cue files or prepared directories were edited or deleted.

Package moves change implementation fingerprints, resource paths and Python class
module paths. Existing Agent evidence is historical and must be revalidated; it is
not relabeled as V2 verification. Source prep fingerprints include the Kit version
and relocated driver. Existing JSON graph/script/design records and prepared asset
schemas retain their readers; preparation is not rerun implicitly. Arbitrary old
Python pickles referring to moved private classes are not a stable interchange
format. Keep them in their original V1 environment or recreate them from inputs.

## ChessChamp

V2 removes the supported ChessChamp/ChessScript/ChessTheme/ChessAssets implementation,
ChessBoard block, `chesschamp` template, starter, dependency extra, runtime artwork
and current discovery/site advertisements. No equivalent supported chess frontend
is shipped in V2.

For unchanged PGN/UCI/JSON projects, create an isolated checkout at the audited V1
commit and use its original chess extra and lock:

```bash
git worktree add --detach ../faceless-champ-v1 22f3beaccb5a56990bd0974666b7c639a0667a68
cd ../faceless-champ-v1
uv sync --extra chess
```

These are recovery instructions, not commands executed during M4. Preserve custom
artwork and project data with that environment. The original contracts are archived
in [V1 ChessChamp](../legacy/v1/chesschamp.md) and
[V1 Kit chess](../legacy/v1/kit-chesschamp.md); asset attribution remains in V1 Git
history. A separately maintained board producer could use Core RasterSource and
Viewport, but no automatic script converter or drop-in replacement is promised.
