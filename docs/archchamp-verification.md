# ArchChamp v1 verification

Verified locally on 2026-10-14 with core 0.1.5, kit 0.1.0rc7, agent 0.1.0rc2,
PyVista 0.49.1 and VTK 9.7.1. Historical verification records remain unchanged.

- Source suites: 549 core passed / 2 skipped; 211 kit passed; 31 agent passed.
  The final ArchChamp core changes were rechecked with all 27 focused cases.
- Independent wheels: 27 core, 8 kit and 2 agent cases passed outside source
  imports. Installed imports resolved under /tmp/fc-arch-installed. Third-party
  runtimes were reused locally for offline validation; uv pip check passed.
- Layout, random seeking, fresh/reused framebuffer parity, geometry isolation,
  field sections, native resource cleanup, mesh assets, requirements, agent
  evidence fingerprints and bundled guides/media were verified.
- One silent preview: 12.000 seconds, 960 x 540, 12 FPS, 144 H.264 frames,
  no audio stream, complete FFmpeg decode. Encoded frames at 0, 4.5, 8.5 and
  11 seconds matched fresh supersampled frames with mean RGB differences below
  0.3 on a 0-255 scale. Assembly, section, field and voxel frames were inspected.
- Website selective verification checked all 39 chapters / 47 Python snippets,
  built only two ArchChamp examples and one silent starter, and verified the
  existing core preview. Browser inspection confirmed the core/kit chapters,
  linked navigation, version labels, preview and download controls.
- Ruff checks and git diff whitespace checks passed. The uv lockfile is current.

No narrated media, landmark model collection, full film or deployment was produced.
See [machine-readable evidence](archchamp-verification.json) and [API guide](archchamp.md).
