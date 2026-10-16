# Story and scene planning

Start with `plan --prompt "..."` to ingest project context and save
`.fc-agent/planning/FINGERPRINT/{context,scene-selection}.json`. The command works
before agent-plan.json exists and never replaces authored plans or Python. Repeated
identical requests reuse the artifact; input additions, edits, custom direction and
installed catalog changes produce a fresh one. Its JSON response is a short handoff.
Use `--input PATH` repeatedly for large projects and `--max-chars N` for excerpt size.
Complete selected SRT cue clocks remain in context even when excerpts are truncated.

The ranking uses explicit relationship signals and the live registry. Read the
whole story before accepting suggested boundaries or treatment. Cues determine
source time, not semantic understanding. Preserve original cue IDs; a scene boundary
may partition an overlapping source interval without modifying either source cue.
Do not copy recipe example values or generic labels into the finished explanation.

Custom design JSON is a partial DesignSpec (theme, font, palette, sizes, motion,
captions). Explicit fields override the clean-flow starting design. Free-form
instructions remain verbatim in the selection artifact and take precedence over
all defaults; interpret them before choosing or authoring a treatment. Supplied
project design references and constraints must be read too. The tool does not claim
to translate arbitrary natural language into executable styling automatically.

For each final scene, record why the chosen capability explains this beat better
than its alternatives, the composition, cue-linked motion, transition, assets,
provenance and layout strategy. Populate ScenePlan capabilities,
selection_rationale, composition, motion_plan, transition and layout_strategy.
Then write matching Python. Core primitives remain available when a recipe limits
the explanation; prepared dependencies still require explicit prepare.

Turn the prompt into a brief containing audience, intended understanding, duration,
format, constraints and available inputs. Record assumptions instead of repeatedly
asking about low-impact defaults. Default to landscape 1080p/30fps, no captions,
and complete delivery unless the user requests a narrower result.

Give every beat a scene ID, idea, and reason to exist. For every scene describe what
the viewer should understand, the relationship that demonstrates it, the change
over time, and where attention should move. Match beats to scenes in the same order.
Use source seconds for scene starts and local seconds for key events. Key events
drive sampling; they describe actions that Python must actually implement.

Example: caching can be explained as repeated work → first request misses → result
is stored → repeated request hits → explain expiry. Choose only the beats needed
for the requested duration. The API cannot establish factual correctness; preserve
source references and mark illustrative data explicitly in both the plan and visuals.

Run `fc-agent schema VideoPlan` for fields and validation. Keep authored plans in
`agent-plan.json`; generated reports belong under `.fc-agent/`. Put the readable
narration in `narration.md` and required artwork descriptions in `asset-brief.md`.
When revising, update the plan and Python together. A successful parse does not mean
the story is effective; compare the rendered result against the scene purpose.
