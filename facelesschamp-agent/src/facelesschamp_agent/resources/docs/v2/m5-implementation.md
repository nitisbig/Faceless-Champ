# M5 implementation and release evidence

M5 completes the five implementation milestones as a coordinated local
`2.0.0rc1` candidate. The original audit baseline remains dated and intact.
This record covers focused Linux checks, not a full platform release campaign.
No commit, push, publication or remote render was performed.

## Implemented ownership

| Files | Result |
| --- | --- |
| Kit `compiler.py`, new `rendering.py` | CompiledVideo.frame/save_frame/storyboard/export reuse the compiled composition. Core remains authoritative for drawing, encoding, source-clock audio, cancellation, timeout and atomic publication. Supplied renderers remain caller-owned; owned sessions close on success/failure. Metadata captures actual session/font provenance before close, resolved dimensions and effective contact-sheet columns. |
| Kit `project.py` | Existing Project operations build once and delegate to CompiledVideo, preserving arguments and Path results. Validation uses the same Kit renderer service. Profiles also accept Core's encoder_timeout. |
| Kit `capabilities.py`, `subtitles.py`, public facade | media_probe, raw read_subtitle_cues, public_capabilities, validate_rendering and the identical Core ExportProgress type. Discovery loads no optional engine and allocates no native context. |
| Agent `project.py`, `media.py`, `registry.py`, `cli.py`, generated `delivery.py` source | Rendering/probing/discovery/progress use Kit services. Agent retains checksum/fingerprint history, plan validation, alignment, conformance, layout diagnostics and separate visual/editorial reviews. The exact object returned by Agent's validated build reaches Kit production; no factory is rerun for that operation. User-owned render.py is not replaced. |
| `scripts/sync_reference_docs.py` | Explicit source/resource inclusion table, canonical local-link validation, rewriting links between included references, deterministic version/export/extra metadata, model-generated JSON schemas, and read-only --check drift detection. Historical audit/release reports are not bulk-copied or rewritten. References to repository-only examples/history retain their canonical source context. |
| Website builder, `project-map/build.py` and Agent `scripts/release_evidence.py` | Share V2 capability/version metadata. The project atlas is distinct from the recipe gallery. The initial M5 pass missed the project atlas; the follow-up below corrects it. Recipe gallery rows derive from recipe count; its font uses the packaged Core font loader and production calls CompiledVideo services. |
| Three manifests and public versions; Kit/Agent scaffolds; Kit MANIFEST.in; uv.lock | All distributions use 2.0.0rc1. Kit requires Core >=2.0.0rc1,<3.0.0; Agent requires Kit in that range. Extras forward through their proper owners, including newly forwarded Agent equations. Maps/diagram resources are explicit sdist inputs. |
| READMEs, llms files, current API/architecture guides, portable skills and website | Current V2 ownership/version/install guidance. ChessChamp remains V1-only with preserved migration/recovery docs. Legacy recovery links were corrected for their moved location. Existing historical verification reports retain their original claims. |

No new runtime dependency, independent frame evaluator, exporter, schema framework,
provider integration or publishing workflow was added.

## Focused validation

The user's major-key-test scope was retained. Root, Kit and Agent tests ran
separately to avoid colliding module names. **27 distinct focused pytest cases
passed**, with reruns limited to fixes found during this work:

- **Kit: 7 cases.** New production ownership/source-time/provenance tests;
  cancellation preserves an existing destination and leaves no temporary files;
  retry/overwrite protection/progress; raw static capabilities; existing minimal
  installation/discovery checks; native Skia Project validation/frame/storyboard/
  bounded export with existing Path/report contracts.
- **Agent: 12 cases.** Exact compiled-object delegation and one build per operation;
  no successful evidence on failed export, followed by successful retry; eleven
  recipe atlas entries allocate six rows; three model/schema/resource contracts;
  decoded six-second export keeps visual/editorial status pending; narration-tail
  preparation preserves original audio bytes, original cue indices and the tiny
  overlap; lazy discovery, networking guide/block handles, explicit user direction,
  benchmark schema, and runnable entrypoint paths containing spaces.
- **Core: 8 cases.** No upward imports; native-extra forwarding; required source
  narration/ignore/checksum inputs; ranged source-clock audio/video; encoder stall
  and cancellation preserve the existing destination and caller renderer.

Representative commands (run these roots separately):

```bash
.venv/bin/pytest -q facelesschamp-kit/tests/test_production_services.py facelesschamp-kit/tests/test_minimal_install.py facelesschamp-kit/tests/test_skia_backend.py::test_project_backend_applies_to_validation_frame_storyboard_export
.venv/bin/pytest -q facelesschamp-agent/tests/test_production_services.py facelesschamp-agent/tests/test_media.py::test_full_export_decode_and_review_remain_separate facelesschamp-agent/tests/test_media.py::test_audio_tail_preparation_preserves_source_and_cues
.venv/bin/pytest -q tests/test_architecture_boundaries.py::test_core_has_no_upward_imports tests/test_architecture_boundaries.py::test_three_wheels_forward_optional_3d_conversion_dependencies tests/test_distribution_inputs.py tests/test_export.py::test_source_range_rebases_composition_audio_and_visuals tests/test_backend_contracts.py::test_encoder_stall_and_cancellation_preserve_existing_output_and_caller_renderer
.venv/bin/python scripts/sync_reference_docs.py --check
.venv/bin/python website/scripts/build_content.py
.venv/bin/python website/scripts/verify_examples.py
```

The website gate passed **37 chapters, 45 Python snippets, 19 internal links**.
Generated references/schema/metadata pass the **49-output** drift gate. Ruff checks,
format checks for M5 Python changes, uv lock consistency and git diff --check pass.
The website verifier checks snippet syntax and navigation; it does not claim to
render every snippet or certify visual output.

## Clean distribution matrix

All four Linux lanes passed from fresh uv environments, using installed artifacts
outside the checkout with `python -I`; no editable SDK or source-path fallback.

| Lane | Base Core | Installed Kit/Agent | Selected extras |
| --- | --- | --- | --- |
| Python 3.12.3 wheel | Passed | Passed | coding,effects passed |
| Python 3.13.15 wheel | Passed | Passed | coding,effects passed |
| Python 3.12.3 sdist | Passed | Passed | coding,effects passed |
| Python 3.13.15 sdist | Passed | Passed | coding,effects passed |

Each base environment contains exactly Core and Pillow 12.3.0. Each matches all
**20 frozen Core pixel fixtures**, fully decodes the bounded FFmpeg export and
checks source-clock audio windows. Installed stack checks cover CLI help, version
coordination, capability/resource discovery, all three schema/model equalities,
raw cue index/overlap preservation, map/diagram/narration resources, and explicit
Python preparation followed by deterministic manifest reopening/playback with
network and child-process execution blocked during playback. Native/browser/
highlighting imports are blocked during discovery and base playback. Selected
extras install NumPy/Pygments through Agent and render highlighted code.

The installed stack reports 1,020 discoverable public records. Discovery is
contract evidence, not proof that every optional dependency or device works.
Observed shared dependencies include packaging 26.3 and Pydantic 2.14.1;
selected extras use NumPy 2.5.4 and Pygments 2.21.0. This is a tested resolution,
not a promise that every permitted future dependency release has been certified.

Local evidence lives under `output/v2-m5/`: `dist/` contains the six wheel/sdist
artifacts; `packaging.json` records hashes, sizes, metadata and required resources;
each `wheel-3.12`, `wheel-3.13`, `sdist-3.12`, `sdist-3.13` directory contains
commands, base pixel/export evidence and installed/offline/extras JSON results.
Validation probes are preserved in `output/v2-m5/validation/`. After final reference
synchronization, packages are rebuilt, archive contents inspected, and the installed
stack smoke checks refreshed. Generated setuptools build directories were cleared
before initial packaging so removed chess modules/assets cannot leak from stale
build output. Core's intentional chess migration-error stub remains.

## Compatibility and remaining release work

- Existing V1 project pins must be edited explicitly. New scaffolds pin the V2
  candidate. V1 domain imports and ChessChamp require the M4 migration/V1 recovery
  alternative; Core does not gain upward Kit import shims.
- Package/source/font changes intentionally stale prior Agent review evidence.
  Old records and supplied media/cue files remain intact; re-render/review to earn
  new evidence. Schema version 1 contracts and prepared manifest readers remain.
- The full repository suite, long render/soak benchmarks, all-recipe full exports,
  hardware ModernGL/CAD/VTK lanes, browser captures and Windows/macOS checks were
  not run for M5. Native Skia has the focused local check above. No new hardware or
  visual-quality certification is inferred from clean CPU/offline installs.
- Licensing/publication decisions remain separate: Kit LICENSE.pending explicitly
  records that the owner has not selected a project-code license. No publication
  was attempted or approval requested for it.

## Acceptance and next step

M5 implementation acceptance is satisfied: Kit production ownership; exact Agent
input delegation; caller/session lifetime and failure recovery; deterministic
source clocks and decoded media; static offline discovery/prepared playback;
current references and model schemas; coordinated versions/optional forwarding;
clean 3.12/3.13 wheel/sdist base/selected-extra lanes; required packaged data; and
no publication or automatic project migration.

**M1–M5 implementation is complete.** The next step is release-candidate review
and the chosen platform/native/media certification scope, followed by licensing
and publication decisions. There is no additional planned implementation milestone.

## Repository and atlas follow-up

The initial completion claim missed `project-map/`: its builder still referenced
removed Core web/OS packages and its curated catalog still advertised V1 ownership
and chess. This follow-up fixes those references, consumes the shared V2 capability
metadata, regenerates the offline page and adds a read-only atlas drift check.
Current backend/effects and Kit production descriptions replace obsolete feature
reservations. Dated V1 history remains labeled historical.

The root keeps the three existing package paths; their names are not evidence of
an old runtime. The [repository layout guide](repository-layout.md) documents
current ownership and intentional migration stubs. The scoped cache-cleanup tool
skips tracked files, symlinks, user projects, environments, assets, prepared caches
and render evidence. Reference synchronization now covers 50 generated outputs.
This follow-up passed four focused tooling regressions, including all seven atlas
view builders, metadata/links, read-only drift detection and cleanup exclusions.
Interactive browser/visual inspection was unavailable in this session. The 27
runtime cases above remain original M5 evidence rather than a new full-suite claim.
