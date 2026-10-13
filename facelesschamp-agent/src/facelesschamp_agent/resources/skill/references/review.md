# Evidence-based review

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
