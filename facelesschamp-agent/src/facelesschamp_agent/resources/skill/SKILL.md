---
name: facelesschamp-agent
description: Plan, author, inspect, and deliver Faceless Champ videos through core and kit, using structured scene plans, Python recipes, and recorded media review. Use for creating or revising videos with this library.
---

# Faceless Champ production

Use `fc-agent` (or `python -m facelesschamp_agent`) as the production interface.
The external agent supplies reasoning and edits Python; this package does not call a model.
Commands return JSON with artifact paths and scoped diagnostics. Use `--project PATH`
from any directory. Run `fc-agent doctor` before a new production environment.

## Plan and author

Follow the user's explicit design, scene, motion and delivery instructions first.
Project constraints come next; the premium defaults fill only unspecified choices.
Do not add titles, captions, cards or effects that contradict custom direction.

For landscape coding tutorials, use the approved `coding-tutorial` design only
when no custom design or instructions were provided. Pass all custom prose design
instructions through `--instructions` or `--design`; never call the fallback pack
to replace those instructions. Read the returned template guide when selected.
The editable copy lives in PROJECT/templates/coding-tutorial/. Keep lesson code,
narration and cue timing separate from style and component helpers. Carry
`design.template` into the authored plan only when this design was selected.
Use `load_coding_tutorial(ctx.root)` for fresh components and
`template.group(..., bounds=bounds)` for safe kit placement. Style edits reload.

Use this five-stage loop when creating or improving a narrated project:

1. Run `fc-agent --project PROJECT plan --prompt "USER REQUEST"`, passing custom
   `--instructions "..."`, `--instructions-file FILE`, or `--design FILE.json`.
   It reads normal-subtitle.srt, cue-per-word.srt, voiceover.md (also voicover.md),
   narration.md and supplementary project files without executing their code.
   Word cues own timing; preserve every source time and tiny overlap. Read the
   returned selection artifact and consult source refs if context was truncated.
2. Understand the whole narration, then refine its suggested beats into meaningful
   ideas. Each beat needs a teaching purpose, evidence, visual relationship and
   attention sequence. Estimated timing must remain labelled until cues exist.
3. Select a treatment for every beat. The packet ranks the installed library and
   assets; confirm the choice against the meaning, not only matching words.
   Use `capabilities "QUERY" --recommend --limit 5`, then `describe ID` only for
   chosen APIs. New public APIs, designs, fonts and icons are discovered locally.
   Write detailed ScenePlan direction: capabilities, selection_rationale,
   composition, motion_plan, transition, layout_strategy, cue-linked key_events,
   required_assets and provenance. Author real recipe content or custom Python.
   For long films, read beat rows in small batches from the JSON artifact and reuse
   shared direction; retrieve only affected beats during repairs. Read the complete
   narration once, and avoid repeatedly loading the full cue clock or catalog.
4. Run `audit-layout`, then inspect `storyboard` and motion previews. Repair only
   failing scenes and rerun checks, up to brief.repair_limit. Preserve readable
   type; reflow/split crowded content. Declare only verified intentional overlaps
   in intentional_overlaps (placement/child IDs). allow_bleed permits safe-area
   use, never clipping outside the canvas. Record unresolved failures honestly.
5. Run `entrypoint` for existing projects (new starters include render.py). Run
   `python PROJECT/render.py` for an audited, verified short preview, inspect
   encoded frames, and deliver the script and preview. `--full` is available for
   an explicitly requested full export. Report visual/editorial review separately.
   Renderers accept `--fps` and `--quality low|high|4k`; these override export
   settings without changing the selected preview/full length.
   Video exports show frame progress, elapsed time and ETA on stderr. Preserve
   that feedback and keep stdout available for the structured result.

The planner supplies a retrieval draft, not semantic understanding or a quality
verdict. You supply that reasoning, scene code and visual repairs. Never hand the
user the untouched starter as an interpretation of their narration.

For a new video, `fc-agent init PROJECT` creates an editable example, not a finished
interpretation of the prompt. Replace its `agent-plan.json`, narration draft, and
Python content. Existing projects retain their files; add or update a plan in place.

Read [planning](references/planning.md) to convert the user's goal into story beats
and timed scene purposes. Use `fc-agent schema VideoPlan` for the current contract.
Read [design](references/design.md) when choosing visual treatments and art direction.
Use `fc-agent capabilities "meaning or subject" --recommend --limit 5`, `recipes`, and `describe ID` to
retrieve only relevant capabilities. [Discovery](references/capabilities.md) explains
imports, optional dependencies, and custom Python compositions.

Write ordinary kit/core Python. Start `build(ctx)` with `AgentProject(ctx.root).new_video(ctx)`
to apply the plan's design, asset declarations, and master narration. Match segment IDs
and source times to the plan. Recipes are a starting point; use public APIs for custom
scenes. Each scene should show a relationship or change that supports its purpose.

When audio or cues are supplied, read [narration](references/narration.md).
Do not invent speech, word timings, facts, or unavailable artwork. Without narration,
create a narration script and identify the completed media as a silent draft.

## Inspect and finish

Run `validate`; use `prepare` only for declared prepared dependencies or audio-tail
padding. Create `storyboard` and `preview` artifacts. Inspect actual image and motion
output, not only the plan or build report. Use [review](references/review.md) to record
findings against the exact artifacts and fingerprint.

Repair the affected scene, then regenerate and inspect the changed evidence. The
default budget is three repair passes per failing scene. Preserve earlier outputs
and report unresolved findings when the budget is exhausted.

For a request to make a complete video, continue through `render` and `verify` after
preview review. A request limited to a storyboard or preview keeps that boundary.
Render already runs full-export media verification. Inspect decoded frames as well.
Use `status` to report structural, media, narration, visual, and editorial results
separately. If you cannot inspect media, record the applicable review as `unverified`;
never claim visual or human-level quality from automated checks alone.

## V2 production ownership

Core owns deterministic composition, rendering and FFmpeg. Kit owns domain APIs,
preparation and CompiledVideo.frame/save_frame/storyboard/export. These operations
reuse the compiled object and return backend provenance before closing owned
renderers. Supplied renderers remain caller-owned. Agent delegates production to
Kit and retains checksums, source alignment, evidence history and review policy.
Preview, decoded export, visual review and editorial review are separate claims.
Discover optional capabilities offline; discovery does not prove device support.
ChessChamp is V1-only; migrate with the V2 M4 guide rather than installing a V2 chess extra.
