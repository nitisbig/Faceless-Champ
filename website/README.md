# Faceless Champ guide website

A buildless guide for the core library and facelesschamp-kit, with 21 sidebar chapters,
copyable highlighted code, 15 downloadable Python examples, chapter search, deep links,
light/dark themes, and responsive navigation. Seven real Python-rendered preview clips
are bundled with their poster frames. The framework clip covers its three-second hook;
the complete framework example is ten seconds.

## Preview

From the repository root:

```bash
python3 -m http.server 8765 --directory website/dist
```

Open http://localhost:8765. HTTP serving is required because chapters load from JSON.
`website/dist/` can be served by any static host. No JavaScript dependencies or build
step are required. Fonts use optional Google Fonts with local fallback fonts.

## Edit and regenerate

Chapter text and Python examples have one source: `scripts/build_content.py`.
The site layout and interactions live in `dist/index.html`, `dist/styles.css`, and
`dist/app.js`. After editing content, run:

```bash
.venv/bin/python website/scripts/build_content.py
.venv/bin/python website/scripts/verify_examples.py --render
node --check website/dist/app.js
```

The verifier parses all 25 Python snippets, builds all 15 complete examples,
validates all three kit projects, and samples three frames per example. Asset-dependent
narration/audio recipes are syntax-checked; they require the reader's own media.
With `--render`, it also exports seven preview videos, checks metadata with ffprobe,
and completely decodes them with FFmpeg. Results live in `verification.json`.

Browser QA covers copying the exact Python code, search results and navigation,
chapter navigation, and the mobile menu at a 390-pixel viewport. The two packages'
current source APIs ground the guide; it does not claim published availability for
the kit's local 0.1.0rc1 release candidate.

`.openai/hosting.json` retains the private Sites identity for publication. Deployment
source synchronization uses a separate checkout, keeping the library repository's Git
history independent. Do not commit credentials or temporary deployment archives.
