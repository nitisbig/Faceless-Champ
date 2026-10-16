# Faceless Champ API guides

Core and kit guides retain inline API snippets, copy controls, search, theme
switching and chapter navigation. Retired standalone demo downloads, posters and
video previews are no longer published. The current scene collection lives in
[the premium reference index](../examples/README.md); its first entry is a draft.

Regenerate and check documentation without rendering:

```bash
python3 website/scripts/build_content.py
python3 website/scripts/verify_examples.py
node --check website/dist/app.js
```

The generator reads API snippets from maintained documentation, writes chapter
JSON and version labels, and never creates a downloadable demo collection.
The verifier checks guide versions, chapter links and Python snippet syntax.
These checks make no media or visual approval claim. Package suites separately
cover executable library behavior and starter templates.

Preview locally:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory website/dist
```

Open [core](http://127.0.0.1:8765/index.html) or
[kit](http://127.0.0.1:8765/kit.html). This is a local documentation change;
hosting configuration is retained.
