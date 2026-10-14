# ArchChamp plans

Search with `fc-agent capabilities search architecture`, then describe
`facelesschamp_kit.blocks.ArchCanvas` or `recipe:arch-design`. The bundled guides
cover the shared geometry, script, camera, field and annotation contracts.

Use the existing `ScenePlan` recipe treatment with content such as:

```json
{
  "design": {
    "units": "m",
    "parts": [{"id": "body", "mesh": {"asset": "body-model"}}],
    "script": {"actions": [{"kind": "orbit", "degrees": 45, "at": 0, "duration": 2}]},
    "dimensions": [{"start": [-1, 0, 0], "end": [1, 0, 0], "part": "body"}]
  }
}
```

Declare `body-model` in brief assets with `kind: "mesh"`, a local file path and
source information, and include it in the scene's `required_assets`. The existing
starter factory uses `AgentProject.new_video(ctx)`, which registers those assets
before applying recipes. Structured validation opens no render window. Primitive
geometry can replace mesh assets with `{"primitive": "cube", "params": {...}}`.
Native Python scenes can use PyVista/VTK, arrays, converted geometry or MultiBlock
assemblies; external library imports stay in the project factory.

Project tools are declared in standard pyproject requirements using `uv add`,
then installed with `uv sync`. Kit/agent doctor checks installed versions;
build never installs or downloads anything. Dependency versions, mesh checksums
and geometry fingerprints participate in evidence identity. Changing inputs
invalidates old review evidence. Frame and preview services use the normal
source clock and media checks; a successful render does not establish scientific
validity. Supplied field results require provenance or an explicit illustrative
explanation. ArchChamp provides visualization, not a simulation solver.

The ArchChamp thumbnail and motion preview reuse the single verified core
assembly preview. Existing recipe media and historical release evidence remain
unchanged. No extra narrated example or complete film is generated for ArchChamp.
