# Scene selection and preview delivery

See [local verification results](scene-selection-verification.md) and the
[runnable example](../examples/scene-selection/README.md).

The agent layer now supplies a five-stage local workflow: ingest context, suggest
beats, retrieve scene treatments, audit authored layouts, and deliver a runnable
renderer with a verified short preview. An external authoring agent supplies
semantic interpretation, scene code and visual repairs. The local tools use no
model API and do not equate keyword ranking or a successful encode with premium
editorial quality.

## A short instruction

Give your authoring agent the exported FacelessChamp skill and a request such as:

> Use the narration and supplied files in my-video. Plan each beat, select the best
> installed visual treatment, author the scenes, fix layout issues, and deliver
> render.py with a short preview. Use a light palette with blue accents and no titles.

The agent follows the skill's five-stage loop. For direct use:

```bash
fc-agent --project my-video plan --prompt "Explain the supplied narration"
fc-agent --project my-video plan --prompt "Explain the supplied narration" \
  --instructions "Full screen editor, no headings or callouts" \
  --design my-design.json
fc-agent capabilities "request through a cache" --recommend --limit 5
fc-agent describe recipe:request-journey
```

`--design` accepts a partial DesignSpec JSON. `--instructions-file` accepts explicit
custom direction. User direction takes precedence over project design and defaults.
Existing project design is retained unless explicitly overridden. Defaults use
clean-flow with packaged DM Sans, restrained accents, measured safe bounds, readable
type, purposeful reveals, a settled hold and no automatic captions. Set `--format shorts`
for portrait direction; a short preview and a portrait video are separate
choices. Configure the authored kit video and VideoPlan to match the chosen format.
Omitting format and duration retains the existing brief's format and closing hold.
If new source cues outgrow an inherited duration, planning extends to the complete
source clock and reports a warning; an explicit duration cannot trim source cues.

## Context and timing

`plan` works in a directory before an executable kit project exists. It creates
fingerprinted `context.json` and `scene-selection.json` under `.fc-agent/planning/`
and returns a compact handoff. It never replaces agent-plan.json or authored Python.
Read both artifacts, including supplemental design/data sources and asset references.

Discovery recognizes cue-per-word.srt, normal-subtitle.srt, voiceover.md, the
voicover.md alias, narration.md, supplemental text/data/code and local assets.
Word cues take timing precedence. Cue IDs, original indices, source times and tiny
overlaps remain intact. Suggested scene spans partition the source clock from zero
through the final hold; they do not rewrite SRT files. Supply `--duration` only to
extend a source clock, never to cut off cues. Without cues, timing is explicitly
estimated. Truncated untimed narration must be read completely before planning.

Use `context --max-chars N` for a standalone inventory. `plan --input PATH` can be
repeated to narrow a large project; `--max-chars`, `--beat-seconds` and `--candidates`
control excerpt size, suggested beat size and candidate count. Complete selected cue
clocks remain available beyond the excerpt budget, subject to explicit hard limits.
Oversized clocks fail with instructions to split into chapters. Hidden, generated
and vendor trees are excluded; project files are read as data and never executed.
Large media uses labelled sampled checksums and file metadata for planning freshness;
export/review evidence retains its separate full-content verification contract.

## Selection and efficient retrieval

Every suggested beat has source cue references, purpose, relationship intent,
ranked candidates and reasons, composition, motion, attention order, transition,
required inputs and layout checks. Confirm all choices against the whole story.
Do not invent chart data or use recipe example labels as finished content.

The registry inventories installed public APIs, public module source, recipes,
design presets and resources. New public exports/modules, fonts and icons become
discoverable on the next inventory. Optional modules can be indexed from source
without executing them. `evidence` distinguishes installed API, source and resource
records; source discovery does not establish optional dependency availability.
Current signatures take priority over bundled guide excerpts.
Preset enumeration covers public literal design/theme mappings and named selectors;
dynamic/private plugin registries still expose their public API but may require
describe or explicit documentation to list all choices. Source-only constructor
signatures cannot resolve generated or inherited constructors automatically.

Use compact, limited retrieval and describe only selected IDs. Reuse unchanged
planning artifacts; changes to inputs, instructions, design or catalog invalidate
reuse. This reduces repeated context and catalog output. It does not claim a
model-token benchmark or guaranteed inference speedup.

## Author, repair and deliver

Create or update agent-plan.json and videos/main.py. Match scene IDs/times exactly.
ScenePlan now records capabilities, selection_rationale, composition, motion_plan,
transition and layout_strategy alongside existing content and cue-linked events.
Use public kit/core APIs and explicit preparation for prepared dependencies.

```bash
fc-agent --project my-video audit-layout
fc-agent --project my-video storyboard
fc-agent --project my-video preview --scene beat-001
fc-agent --project my-video entrypoint
python my-video/render.py
python my-video/render.py --start 12 --duration 6 --output output/passage.mp4
```

The audit checks canvas/safe bounds, named children, unintended intersections,
motion samples and engine layout diagnostics. It deduplicates repeated findings and
provides scene/time/element scope with repairs. A compact summary points to the full
record; `audit-layout --full` includes every sample time. Exact intentional_overlaps pairs and
allow_bleed IDs must refer to compiled placements or placement/child handles.
Bleed allows the safe margin, never canvas clipping. Actual named ancestry prevents
parent/child unions from being mistaken for content collisions.

Repair Python and regenerate affected evidence up to brief.repair_limit. These
checks sample conservative bounds and cannot prove all-frame visual quality.
Inspect encoded frames and motion, then record visual/editorial review separately.
The generated render.py runs validation and layout gates, exports a preview of at
most ten seconds and verifies decoding/metadata/audio. It anchors the project and
relative outputs at its own directory, so it runs from another working directory.
It preserves an existing user renderer. Full export is explicit with `--full`.

## Python API

```python
from facelesschamp_agent import AgentProject, plan_project, read_project_context

context = read_project_context("my-video")
handoff = plan_project("my-video", prompt="Teach the supplied narration",
                       instructions=["Use my custom design; no captions"])
project = AgentProject("my-video")  # after authoring a kit project and VideoPlan
audit = project.audit_layout()
project.entrypoint()
```

SelectionPlan and BeatSelection have JSON schemas through `fc-agent schema`.
QualityReport reports layout_validation independently of structural/media and
external visual/editorial review. Full-export evidence remains false for previews.
