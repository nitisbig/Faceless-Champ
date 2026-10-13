# Story and scene planning

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
