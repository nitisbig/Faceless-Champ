# M5 production migration

Core, Kit and Agent now use `2.0.0rc1`. Install matching V2 packages together;
Kit requires Core `>=2.0.0rc1,<3.0.0` and Agent requires matching Kit bounds.
Existing projects with V1 pins must update their project dependency and lockfile
explicitly. Do not combine V1 domain imports with V2 wheels. See
[M4 domain migration](m4-migration.md) for renamed owners and V1 ChessChamp recovery.

```python
from faceless_champ import ExportSettings
from facelesschamp_kit import Project

project = Project("my-video")
compiled = project.build("main")
image = compiled.frame(0.5, size=(540, 960))  # match the composition aspect
still = compiled.save_frame(0.5, "output/frame.png", size=(540, 960))
sheet = compiled.storyboard([0.5, 1.0], "output/samples")
result = compiled.export(
    "output/preview.mp4",
    settings=ExportSettings(width=540, height=960, fps=15, antialias=1),
    start_time=0.5, end_time=1.5,
)
print(result["output"], result["rendering"], result["source_range"])
```

These methods use the already compiled object and original source times. Saved
operations return `output` (Path), `rendering`, `source_range` and `settings`.
Only exports have a source range. Stills/contact sheets return None for that field.
Export accepts progress and cancel callbacks; Core retains atomic publication,
overwrite protection, bounded encoder I/O and audio trimming. A supplied renderer
remains caller-owned; only sessions created by Kit are closed, including on errors.

Existing Kit Project methods preserve arguments and Path results. Agent never
calls Project production methods that would rebuild its validated object. Agent
continues to own media conformance, source-audio alignment, checksums, fingerprints,
history, layout findings and visual/editorial review. A preview or decoded export
does not count as visual/editorial approval. Version/source changes invalidate
prior review evidence intentionally; preserve the old records and regenerate it.

Kit exports `media_probe`, `read_subtitle_cues`, `public_capabilities`,
`validate_rendering` and the unchanged Core `ExportProgress` type. Static discovery
does not allocate native contexts, import optional engines, prepare assets or prove
hardware support. Optional extras are forwarded through Agent → Kit → Core;
maps, coding and browser preparation belong to Kit. `equations` is now forwarded
through all three distributions. Base Core still requires only Pillow.

Canonical docs stay in the root and each package's docs/llms files. Run
`python scripts/sync_reference_docs.py` after changing an included reference;
`--check` detects drift without writing. The script's explicit inclusion table
selects offline Agent resources, retaining historical reports separately. The
website and recipe gallery/atlas use the same generated capability metadata.
Run `python website/scripts/build_content.py` and
`python website/scripts/verify_examples.py` for the website's content/link gate.
The offline project atlas is built by `project-map/build.py` using the shared V2
metadata. Run `python3 project-map/build.py --check` to detect a stale page without
writing. `release_evidence.py` separately builds the recipe gallery. See
[repository layout and cleanup](repository-layout.md).

The [M5 implementation record](m5-implementation.md) distinguishes executed
Linux checks from deferred native/platform/browser and human review coverage.
