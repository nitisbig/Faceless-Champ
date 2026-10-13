# Agent v1 verification

Local release candidates: agent **0.1.0rc1**, kit **0.1.0rc6**, core **0.1.4**.
Nothing has been published to a package registry.

## Core features delivered

- Pydantic plans and generated JSON Schema, with scene, timing, asset and recipe validation.
- Python services and a JSON CLI for discovery, scaffolding, preparation, inspection, review, export and verification.
- Offline registry of 198 installed API/recipe entries, bundled guides, ten recipe thumbnails and motion previews.
- Ten reusable kit recipes and public `CompiledVideo.layout_at(time)` geometry inspection.
- Fingerprinted evidence, independent review states, stale-review rejection and repair-count reporting.
- Original cue preservation, explicit derived audio tails, silent drafts and required-artwork placeholders.
- Portable authoring skill, editable examples, 24 benchmark prompts and a generated benchmark-result schema.

External agents still supply planning, Python authoring and subjective review. This
release contains no model runner, provider integrations, TTS or automatic research.

## Automated checks

Core and kit suites run separately. Core passed **522 tests** with **2 skipped**; kit passed **203 tests**. The clean
installed-wheel agent suite passed **29 tests**, including code playback, narration,
review invalidation, CLI contracts and placeholder behavior. Core results and media
metadata are recorded in `release-evidence.json` alongside this document.

Wheel and source distributions were built and installed in separate temporary
environments. Discovery covered all 198 entries with numpy, matplotlib, Pygments,
chess and Playwright absent. A complete starter export passed in that environment.
The coding extra was then installed for the installed-wheel test suite. The portable
skill passed its structural validator. Source distributions also passed discovery.

## Media evidence

Artifacts are under `output/agent-release-verified/` at the repository root. The ten
recipe previews are complete four-second 960×540/15fps exports. Each passed complete
FFmpeg decoding, metadata checks and decoded-frame extraction. Their entrance,
action and exit samples were visually inspected. A code-width issue and chart-legend
spacing issue found during inspection were corrected before the final recipe renders.

Representative full exports use native 1920×1080 at 30fps and antialias=1. The normal
project starter retains antialias=2. The narrated example uses supplied synthetic kit
speech and unchanged cues; chart and code examples remain silent drafts. See the
machine-readable evidence file for checks on all three completed exports: narrated system (30 seconds), chart explanation (6 seconds), and prepared code/result (4 seconds). All passed complete decoding, dimensions, frame rate and duration checks. Narration alignment passed with zero offset in the sampled waveform windows. Decoded entrance/action/exit frames were inspected for each export.
Earlier interrupted exports and excerpts are not counted as full-export evidence.

Sampled image inspection is not a human quality benchmark or continuous playback
review. Visual/editorial review remains separate from media verification. No
human-level quality claim or comparison between models has been measured. The
24-prompt suite supplies the protocol for future external-agent and human-rated runs.

## Reproduce

```bash
python -m pytest tests -q
python -m pytest facelesschamp-kit/tests -q
python -m pytest facelesschamp-agent/tests -q
python facelesschamp-agent/scripts/release_evidence.py --output output/agent-release-new
python -m build facelesschamp-kit
python -m build facelesschamp-agent
```

Use a new output directory so earlier artifacts remain available. See the package
README and `examples/README.md` for the authoring workflow and example factory.
