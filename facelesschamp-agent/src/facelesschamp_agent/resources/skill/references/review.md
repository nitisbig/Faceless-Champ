# Evidence-based review

Run `fc-agent audit-layout` before exporting. It samples scene/placement boundaries,
key events and animation windows, checks canvas/safe bounds and named children,
and reports scoped repair suggestions plus internal engine layout diagnostics.
Bounds are conservative: opacity and masks do not shrink them and widget internals
may be opaque. A passed audit is sampled geometry evidence, not an aesthetic verdict.
Repair findings in Python; rerun the audit and inspect changed motion and frames.
Use intentional_overlaps and allow_bleed only for exact reviewed IDs. Misspelled
exceptions fail, and allow_bleed never permits clipping outside the canvas.

New projects include render.py; `entrypoint` adds it to existing projects without
overwriting user code. `python render.py` validates, audits, renders up to ten seconds
and verifies the encoded preview. `--start` and `--duration` target another passage.
It does not prepare executable checkpoints implicitly. Layout failure blocks export.

Use `fc-agent storyboard` for entrances, key events, and exits. `fc-agent preview`
without a range renders short excerpts around planned actions and boundaries.
Pass `--scene ID` or `--start S --end E` for a particular concern. Verify each video
using `fc-agent verify --output PATH` before recording the review.

Inspect readable text, clear hierarchy, meaningful motion, scene continuity, factual
claims, narration correspondence, and enough time to understand each change. Review
findings identify scene_id, source_time, element when known, observed problem,
evidence_artifact ID, and suggested_repair. Avoid numerical quality scores without
an established rubric or claims about human-level quality.

Get the current fingerprint and artifact IDs with `fc-agent status`. Use
`fc-agent schema ReviewSubmission` for the review format. Submit a JSON file with
`fc-agent review review.json`. For example:

```json
{
  "fingerprint": "CURRENT_FINGERPRINT",
  "reviewer": "external-agent",
  "kind": "visual",
  "status": "passed",
  "reviewed_scenes": ["process"],
  "evidence_artifacts": ["ACTUAL_ARTIFACT_ID"],
  "findings": [],
  "notes": "Inspected entrance, packet motion, label readability, and exit."
}
```

This is an example format, not evidence. Fill it only after real inspection. If visual
access is unavailable, submit status unverified with the reviewed_scenes and a reason;
no evidence is claimed. Editorial review is recorded separately with kind editorial.

Changing plans, sources, assets, or configuration invalidates old reviews. Repeated
failed reviews of the same build do not count as additional repair attempts; a failed
review after each revision does. After the configured limit, preserve artifacts and
report remaining issues rather than looping indefinitely.

For full delivery, `render` exports the complete video and performs full decoding,
metadata checks, frame extraction, and supported narration alignment checks. Inspect
the resulting decoded frames. Report each status separately, identify silent or
placeholder drafts, and do not turn a passed encode into a visual/editorial approval.
