# Coding tutorial template verification — 2026-10-16

The user approved the reference design; encoded-media verification remains a
separate state. This extraction produced no new tutorial renders.

| Check | Result |
| --- | --- |
| Kit package suite | 271 passed |
| Agent package suite | 150 passed before final selection/option refinements |
| Final coding-template and planning regressions | 46 passed |
| Reference scene and FPS/quality routing | 5 passed; scene-frame rendering forbidden or mocked |
| Approved reference parity | 80 component-state probes match the pre-extraction reference |
| Installed kit/agent wheels | Style/guide resources, default selection, custom bypass, editable background and renderer flags passed |
| Lint, selected formatting and whitespace | Passed |

Coverage includes untouched starter recognition, custom instructions/design bypass,
known design files, portrait bypass, noncoding topics, C++ topic recognition,
separate editable folders, preserved local edits, fresh palette loading, planning
cache invalidation, evidence invalidation, kit safe-bound composition, invalid
styles, export settings/verification expectations and profile immutability.

The displayed source never executes during playback. Audio and both subtitle
inputs retain their original SHA-256 checksums. No new scene frame, preview or
full export was produced: `media_rendered: false`, `full_export_verified: false`.

## Full-export controls and progress — 2026-10-16

The example accepts `--full` (with `--render` retained as an alias). Generated
renderers retain explicit full-video selection and FPS/quality overrides. Both
renderers and fc-agent preview/render show frame progress, elapsed time and ETA
on stderr, with a separate encoder-finalization state. Library callers can pass
an optional progress callback; normal Python API calls remain silent.

| Check | Result |
| --- | --- |
| Affected core export, progress and reference checks | 28 passed |
| Kit package suite | 271 passed |
| Agent package suite | 157 passed |
| Renderer help, lint, formatting, whitespace and mirrored guides | Passed |

Progress checks cover observed-throughput estimates, redirected-output throttling,
encoder failure after the final frame and cancellation. Renderer tests mock
media export, verify the full authored range and preserve parseable stdout JSON.
The tutorial remains unrendered by this implementation; its media verification
flags remain false. Core/agent package tests use independent export fixtures.
