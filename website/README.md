# Faceless Champ developer guides

Two static pages share the same design, assets, and JavaScript:

- **Core library:** `dist/index.html` — 16 chapters about scenes, components,
  timelines, narration, composition, motion graphics, and rendering.
- **Kit framework:** `dist/kit.html` — 10 chapters about structured projects,
  blocks, themes, narration, templates, and the kit workflow.

The Core / Kit switch stays visible on mobile. Each guide has its own sidebar,
chapter numbering, search results, installation instructions, and export help.
Existing core hashes still work. Old framework hashes on `index.html` redirect to
`kit.html` with their chapter and section intact.

The kit guide covers all four starters: `silent`, its `explainer-short` alias,
`narrated-short`, and `whiteboard-basic`. It explains editable scaffolds and
callable templates, whiteboard geometry and timing, format/theme changes, and
source-time narration. The kit is documented from the bundled local 0.1.0rc1
release candidate; the guide does not claim published package availability.

## Preview

From the repository root:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory website/dist
```

Open [the core guide](http://127.0.0.1:8765/index.html) or
[the kit guide](http://127.0.0.1:8765/kit.html).
HTTP serving is required because chapters load from JSON. `website/dist/` works
on any static host without URL rewrite rules or JavaScript dependencies.
Fonts use optional Google Fonts with local fallbacks.

## Edit and regenerate

Chapter text, guide metadata, and the 18 downloadable Python examples come from
`scripts/build_content.py`. Every chapter has a `guide` assignment. The shared
renderer selects the active guide using the HTML body's `data-guide` attribute.
The two HTML shells, `dist/styles.css`, and `dist/app.js` control presentation.
Content supports code, tables, notes, and local guide links.

```bash
.venv/bin/python website/scripts/build_content.py
.venv/bin/python website/scripts/verify_examples.py --render
node --check website/dist/app.js
```

The verifier checks both page entrypoints and content links, parses all 30 Python
snippets, builds all 18 downloadable examples, and validates all four template
starters. Kit examples declare the scaffold they need, including the narrated
sample assets and the whiteboard theme/format. Preview dimensions follow the
composition's canvas. The whiteboard example is also validated and sampled in
portrait, including drawing, holding, and clearing moments.

With `--render`, the verifier exports eight previews, checks their metadata and
duration with ffprobe, and completely decodes them with FFmpeg. The framework
quickstart clip shows its three-second hook; the whiteboard clip includes both
five-second scenes. The remaining narrated whiteboard recipe requires the
reader's own media; it is syntax-checked rather than claimed as a rendered film.
Results are written to `verification.json`. Without `--render`, the report covers
build/frame checks only and does not claim fresh media verification.

## Browser QA

Check both pages at desktop and mobile widths (1440 × 900 and 390 × 844):

- Core / Kit switching, scoped chapter counts, sidebar and previous/next links.
- Search isolation, Ctrl/Cmd+K, Escape, and keyboard-operable result links.
- Exact code and command copying, and downloadable Python source parity.
- Light/dark theme persistence across pages, mobile menu closing, and overflow.
- Old framework chapter/section links redirecting to the matching kit page.
- Preview posters and controls, section links, and browser console errors.

Inspect encoded preview frames in addition to browser screenshots. Manual browser
and visual inspection results may be recorded separately under `browser_checks`
and `visual_review` in `verification.json`; rerunning the verifier replaces that
report, so repeat those inspections before recording them again.

`.openai/hosting.json` retains the existing private Sites identity. Publication
is a separate step; these local changes do not deploy the site. Do not commit
credentials or temporary deployment archives.
