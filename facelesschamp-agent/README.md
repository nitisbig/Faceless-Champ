# FacelessChamp Agent

Version **0.1.0rc2** supplies offline production tools for external AI agents. It uses
FacelessChamp Kit **0.1.0rc7** and core **0.1.5**. These are local source releases.
Python 3.12+ and FFmpeg/ffprobe with libx264 are required for video exports.

```bash
python -m pip install -e . -e ./facelesschamp-kit -e ./facelesschamp-agent
fc-agent doctor
fc-agent skill --output /your/skills/facelesschamp-agent
fc-agent init my-video
fc-agent --project my-video capabilities "request through a system"
fc-agent --project my-video validate
fc-agent --project my-video storyboard
fc-agent --project my-video preview
fc-agent --project my-video status
fc-agent --project my-video render
```

Run the install command from the repository root. The starter is an editable six-second
example. Your external agent replaces its plan and Python content using the exported
skill. `fc-agent` does not call an LLM, generate speech, or automatically write videos
from natural language. The external agent plans, authors, inspects, and repairs.

## Context-aware scene selection

```bash
fc-agent --project my-video plan --prompt "Explain the supplied narration"
fc-agent capabilities "request through a cache" --recommend --limit 5
fc-agent --project my-video audit-layout
python my-video/render.py
```

`plan` reads subtitles, voiceover and supplements, preserves the source cue clock,
and saves a detailed beat/scene selection brief with ranked installed capabilities.
Compact retrieval and fingerprinted reuse reduce repeated catalog/context output.
New public APIs, designs, fonts, icons and project assets are discovered locally.
Custom instructions and design override premium defaults; existing project design
is retained. The external agent confirms semantic choices, authors scenes, repairs
layout findings and inspects the rendered result.

New starters include render.py. `entrypoint` adds it to existing projects without
replacing user code. It validates and audits layout before exporting and verifying
a short preview; `--full` explicitly exports the complete video. See the
[scene-selection workflow](docs/scene-selection.md) for configuration, contracts,
limits and the five-stage authoring loop.

## Production contract

`agent-plan.json` contains a versioned `VideoPlan`: brief, story beats, scene purposes,
timing, asset declarations and design. `fc-agent schema` returns its JSON Schema.
Python in the normal kit project remains executable authoring. Start `build(ctx)`
with `AgentProject(ctx.root).new_video(ctx)` to apply style, assets and narration.
Match plan IDs/times to kit segments. Use `apply_recipe` or compose public APIs.

`DesignSpec.theme` accepts `midnight`, `light`, `whiteboard`, and `clean-flow`.
Clean-flow supplies warm gray surfaces, rounded white cards, orange accents, packaged
DM Sans and smooth element reveals/outros. Omit `design.font` to retain the selected
theme font; a supplied custom font clears inherited variable-font weights. Explicit
`segment.add(..., enter=None, exit=None)` disables automatic clean-flow motion.

All commands emit structured JSON. Results are under `result`; failures include
`error.code`, `message`, `suggested_fix`, and relevant locations. Paths explicitly
passed as outputs are relative to the caller; inputs in the plan are project-relative.
Generated outputs have unique names and existing files are not overwritten.

`status` reports structural validation, preview/full media verification, visual review,
editorial review and narration alignment separately. Outputs and reviews are associated
with fingerprints and checksums. Changes invalidate earlier evidence. Review records
are externally supplied assessments, not an automatic aesthetic judge.

`preview` without arguments samples action/boundary ranges; with `-o FILE` it exports
the first ten seconds. Use explicit `--start/--end` or `--scene` for other ranges.
`render` exports and verifies the full composition. `verify -o FILE` checks a current
recorded export. `review FILE.json` accepts the `ReviewSubmission` schema.

Without audio, outputs remain silent drafts. Declared missing required images must
be represented by visible placeholders and keep draft status. Audio tails are padded
in a derived file only by explicit `prepare`; source cues/audio are unchanged.

## Recipes and discovery

Reusable kit recipes cover process flow, request journey, before/after,
cause/mechanism/effect, metrics, trends, part/whole, hierarchy, prepared code/result,
overview/detail and technical geometry. `recipes` lists content examples; `describe recipe:ID` includes
selection guidance. Registry records include all current public core exports and kit
blocks, layouts, templates and recipes, plus public module source and packaged assets. Runtime Python
signatures come from installed APIs; bundled guide excerpts work offline.

The registry's dependency descriptions distinguish preparation from playback. Discovery
does not install optional dependencies or execute prepared code. Imports alone do not
prove that an optional preparation dependency is installed.

## Validation and examples

```bash
python -m pytest -q facelesschamp-agent/tests
python facelesschamp-agent/scripts/release_evidence.py --output output/agent-release
```

The release script prepares a deterministic code fixture, renders every recipe,
creates contact sheets, and exports three complete examples. See `docs/verification.md`
for actual results; executing the script does not perform subjective review.
The bundled `benchmarks.json` has 24 prompts and a result schema for external-agent
runs. No human-level quality or model-comparison result is claimed by this release.

MCP, model runners, TTS, artwork generation, and automatic research are outside v1.

ArchChamp is discoverable through the arch capability family and arch-design recipe. Plans accept mesh assets and structured geometry/actions/annotations. Dependency versions and geometry hashes participate in evidence fingerprints. No simulation solver, automatic dependency installation, or model fetching is provided.

See [ArchChamp structured plans and model assets](docs/archchamp.md).
