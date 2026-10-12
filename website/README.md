# Faceless Champ developer guides

Two static guides share the existing design, search, assets, and JavaScript:

- **Core:** `dist/index.html` — 22 chapters, source version 0.1.4.
- **Kit:** `dist/kit.html` — 15 chapters, local release candidate 0.1.0rc5.

The guides cover code reveals, prepared concept/backend/web playgrounds, local HTML
capture, offline OS tutorials, timed legal chess games, FlowChamp diagrams, and the
existing scenes, motion, narration, charts, composition, and whiteboard workflows.
All ten registered kit starters are documented. Package versions come from the two
`pyproject.toml` manifests; availability on a package index is not assumed.

There are 30 downloadable Python examples and 12 video previews. Every preview and
poster uses a **black canvas background**, including the whiteboard drawing example;
player letterboxing is black too. Card/editor/board surfaces retain their visual colors.
The previews include four new short demos: coding (3.5 seconds), playground (6 seconds),
chess (6 seconds), and flow diagrams (6 seconds). MP4 durations round to frame boundaries.
The kit overview shows its three-second hook; the whiteboard preview shows both five-second scenes.

## Preview locally

From the repository root:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory website/dist
```

Open [core](http://127.0.0.1:8765/index.html) or
[kit](http://127.0.0.1:8765/kit.html). HTTP serving is required for chapter JSON.
The distribution works on a static host without rewrite rules or JavaScript dependencies.
Existing chapter/section hashes remain supported, including redirects from old kit
hashes on the core page. Fonts use optional Google Fonts with local fallbacks.

## Edit and regenerate

`scripts/build_content.py` owns guide metadata and existing chapters;
`scripts/feature_content.py` supplies the recent feature chapters and examples.
The generator writes chapter JSON, exact downloadable source, and version fallback labels.
HTML shells, `dist/styles.css`, and `dist/app.js` control presentation.

From the repository root, use the same Python 3.12+ environment for installation,
checkpoint execution, and verification:

```bash
python -m pip install -e '.[coding,chess,playground]' -e './facelesschamp-kit[playground,chess]'
python -m playwright install chromium
python website/scripts/build_content.py
python website/scripts/verify_examples.py --render
node --check website/dist/app.js
```

The verifier checks both entrypoints, versions, chapter/section links, all ten template
entries, 45 Python snippets, source/download parity, 30 example builds, and ten starter
builds. It samples source-time frames and whiteboard portrait layouts. Playground inputs
are prepared explicitly in temporary projects; build/validation/frame/export checks
block checkpoint and browser process launches while permitting FFmpeg/ffprobe.

`--render` regenerates all 12 previews and posters. Both modes inspect existing MP4
metadata (codec, dimensions, FPS, duration) and completely decode every preview with
FFmpeg. `rendered_this_run` distinguishes regeneration from verification of existing
media. Results replace `verification.json`; append manual browser/frame-review evidence
only after the final verifier run. Temporary prepared paths in reports are audit evidence,
not reusable distributed assets.

HTML factory playback uses a clearly identified synthetic one-frame capture fixture.
It is not claimed as real browser interaction verification. The `coding-web` starter
uses actual Chromium checkpoint preparation and then verifies browser-free replay.
The core `html_video.py` runner also offers explicit `--prepare` and `--capture` modes.
Prepared examples do no execution on import. Narrated recipes requiring reader media
are syntax-checked rather than claimed as verified full films.

## Browser and media QA

Check both pages at 1440 × 900 and 390 × 844:

- Core/Kit switching, scoped chapter counts, previous/next links, and legacy redirects.
- Search isolation, Ctrl/Cmd+K, Escape, and keyboard-accessible results.
- Copy feedback, exact source/download parity, and example setup commands.
- Theme persistence, mobile-menu closing, and horizontal overflow.
- Posters, player controls/playback, section links, and console errors.

Inspect representative encoded frames as well as PNG posters. Preparation, still
samples, and these short website previews do not verify full training-video exports.

The existing `.openai/hosting.json` identity and audience are preserved. This update
is local-only; no site deployment or package publication is performed.
