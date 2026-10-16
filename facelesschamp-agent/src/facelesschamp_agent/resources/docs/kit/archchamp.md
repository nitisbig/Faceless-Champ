# ArchChamp authoring

`ArchCanvas` fits a fresh core ArchChamp viewport into any allocated bounds and
exposes the whole viewport as handle `model`. Put world-space part actions in
`ArchScript`; use kit handle animation to move or fade the viewport itself.
The compiler checks the original script duration against the placement window,
accounting for `source_start`, and samples annotation diagnostics.

```python
import pyvista as pv
from faceless_champ import ArchMesh, ArchPart, ArchScript
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import ArchCanvas

def build(ctx):
    video = Video(ctx)
    parts = [ArchPart("body", ArchMesh.from_data(pv.Cube()))]
    script = ArchScript().orbit(45, duration=2).wait(1)
    with video.segment("design", duration=3) as segment:
        segment.add(ArchCanvas(parts, script, units="m"))
    return video
```

`ArchCanvas` also accepts a structured design dictionary. Use `apply_recipe(segment,
"arch-design", {"design": design})` for the same contract through an agent plan.
For dictionary designs, a supplied non-`None` `script` or `camera`, and explicitly
supplied `labels`, `dimensions`, or `units`, override the corresponding design
fields. Omitted settings preserve the dictionary values and otherwise use the
usual canvas defaults. Empty annotation sequences clear the design's annotations;
`ArchScript()` clears its actions, and `units="model units"` resets its units.
The dictionary's `style` keeps its existing precedence; the block's `style` or
kit theme supplies the default when the dictionary has no style. Composing the
block leaves the source dictionary and supplied objects unchanged.

Mesh file sources in recipes must use registered assets, for example
`{"id": "body", "mesh": {"asset": "building"}}`. Register `building` in
`assets/manifest.json` with `{"type": "mesh", "path": "assets/building.vtp"}`.
`ctx.assets.mesh("building")` resolves and checksums it. Missing files fail; mesh
assets never use image placeholders. Reported geometry hashes also capture changes
to in-memory meshes and VTM child datasets.

Scaffold with `fc-kit init my-design --template archchamp`. This is a silent
landscape project demonstrating an exploded assembly and a dimension line. Core
PyVista is required transitively; external model-generation tools remain project
dependencies. No automatic installation or model downloads occur.

## External project dependencies

Use `uv add trimesh meshio scipy` to declare chosen tools in the standard
`pyproject.toml` `[project].dependencies`, then `uv sync` in that project's environment.
`Project.dependencies()` reports requirement, distribution name, installed version,
extras, direct URL and status. Active missing or incompatible requirements stop
build before importing the video factory with `PROJECT_DEPENDENCY`. Environment
markers are respected; absent pyproject files preserve earlier projects.

Checks cover installed distribution versions. Package-manager resolution remains
responsible for transitive extras and URL provenance. Kit/agent doctor include the
same checks and PyVista/VTK versions without opening a render window. Build reports
include dependency versions and geometry hashes so agent reviews become stale
when those inputs change. Add your model files to the asset registry even when
Python generates geometry from external data.

See the core ArchChamp guide for concepts, model units, world anchors, fields,
section constraints and renderer lifecycle. Scalar/vector fields display supplied
results; identify sources or explicitly mark illustrative values in agent plans.
