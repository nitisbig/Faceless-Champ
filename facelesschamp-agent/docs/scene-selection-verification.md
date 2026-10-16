# Scene-selection verification — 2026-10-16

The local changes were checked with the repository's Python environment. Nothing
was published or pushed.

| Check | Result |
| --- | --- |
| Core package suite | 1,368 passed, 2 skipped |
| Kit package suite | 262 passed |
| Agent package suite | 136 passed |
| Final focused discovery/planning/contracts/workflow run | 74 passed, including the added import-order regression |
| Kit ancestry copy-isolation regression | Passed |
| Ruff and Python formatting on affected code | Passed |
| Git whitespace check | Passed |
| Wheel build/resources and installed renderer from another directory | Passed |

The final focused run followed the catalog import-order fix. It verifies identical
catalogs in fresh CLI/API processes, actual planning-cache reuse, source/configuration
invalidation, inherited design/format/final holds, explicit overrides and layout
evidence freshness. Other coverage checks bounded context, original cue times and
overlaps, future public APIs/assets, layout/motion failures and renderer error gates.

The authored [example](../examples/scene-selection/README.md) has a 12.320-second
source timeline with a 0.320-second closing hold. Its ten-second silent preview
at `examples/scene-selection/output/agent/preview-delivery.mp4` passed full decoding,
640×360 resolution, 15 fps and duration checks. Its current layout audit passed
88 samples. Decoded frames at 3.000, 6.567 and 9.160 seconds were inspected for
readability, progressive disclosure and unintended intersections.

The final build fingerprint is
`472341193230c7d3e5333ede2d1a0edd4ce585fc3992ecc786f3d4d3820e8c1f`.
`AgentProject.status()` confirmed current layout and preview verification both
passed. No narration audio was supplied: this is a silent draft, and no full
12.320-second export or full-video editorial approval is claimed.

A local discovery sample returned the same ten animation matches using 13,279
bytes of full JSON versus 3,689 bytes of compact JSON, a 72.2% reduction. Thirty
repeated bounded searches averaged about 9 ms in this environment. These are
payload/runtime observations, not model-token, model-cost or quality benchmarks.

Semantic treatment decisions, factual checks, scene authoring and visual repairs
remain the external author's responsibility. The local tools provide evidence,
retrieval, contracts and gates; sampled bounds cannot prove all-frame aesthetics.
