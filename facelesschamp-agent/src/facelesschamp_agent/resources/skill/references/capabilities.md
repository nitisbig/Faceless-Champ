# Discovering and composing

`fc-agent capabilities "request through services"` searches installed API records and
recipe selection guidance. `fc-agent describe facelesschamp_kit.blocks.FlowCanvas`
returns constructor parameters, handles and a bundled guide. Ambiguous names require
fully qualified IDs. `fc-agent recipes` provides validated sample content.

Use `from facelesschamp_kit.recipes import apply_recipe` and call
`apply_recipe(segment, "process-flow", {"steps": ["Input", "Process", "Output"]})`.
The returned dictionary maps semantic names to kit handles. Explicit RecipeEvents
supplement the default staging; use segment-local times and avoid conflicting tracks.
For recipe content constraints, inspect describe recipe:RECIPE-ID.

Normal Python authoring stays available: segment.add(block), segment.play(handle,
animation_factory), and segment.add_core(factory). Factories return fresh objects.
Finish group membership and layout before scene insertion. Use measured bounds and
fit_text; never infer supported arguments from similarly named libraries.

Prepared code/results require complete checkpoint execution during explicit preparation.
Rendering and inspection only replay prepared assets. Core maps, equations, chess,
highlighting, or browser preparation can require optional extras. Follow the returned
dependency guidance and the current core/kit guides; preparation is not a sandbox.

The package does not dynamically install dependencies, fetch remote assets, call model
providers, or edit arbitrary code. The external agent controls authored Python and
uses the existing environment's permissions.

ArchChamp/ArchCanvas and arch-design cover technical mesh/point/field/voxel visualization, named assemblies, camera and section actions, and anchored dimensions. Declare model files as mesh assets and external tools in project pyproject.toml. Review geometry/units and field provenance; rendered visuals do not prove physical accuracy.
