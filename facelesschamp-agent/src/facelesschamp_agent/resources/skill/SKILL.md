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

For a new video, `fc-agent init PROJECT` creates an editable example, not a finished
interpretation of the prompt. Replace its `agent-plan.json`, narration draft, and
Python content. Existing projects retain their files; add or update a plan in place.

Read [planning](references/planning.md) to convert the user's goal into story beats
and timed scene purposes. Use `fc-agent schema VideoPlan` for the current contract.
Read [design](references/design.md) when choosing visual treatments and art direction.
Use `fc-agent capabilities "meaning or subject"`, `recipes`, and `describe ID` to
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
