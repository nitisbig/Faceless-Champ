# AI audience · 30 seconds

White canvas, terracotta logos and curves, warm-gray labels, pale baselines.
Five parallel small-multiple graphs use the same 0–100M vertical scale and a
0–3-year relative horizontal scale. Each logo and counter follows its own curve;
the final four seconds hold the completed view. No audio is added.

**All counts and origins are fictional.** This is a visual prototype, not a
historical graph, a forecast, or a comparison of actual reported active users.
Company founding dates and product launches are different; neither is encoded by
these relative origins. The visible disclaimer persists throughout the film.
User-approved illustrative values are in `data/growth.json` at six-month steps.

Run from the library root:

```bash
uv run python 'training project/ai-comapny-graph/render.py' --preview
uv run python 'training project/ai-comapny-graph/render.py' --frames
uv run python 'training project/ai-comapny-graph/render.py' --frame 15
uv run python 'training project/ai-comapny-graph/render.py' --overwrite
```

Or run `python render.py` here using the main repository's environment. Paths are
resolved from the script; the main library is imported directly from `../../src`.
Default export: 1080p/30 fps; preview: 720p/24 fps. `-o` selects output and
`--overwrite` permits replacing video/single-frame files. Storyboards regenerate
six PNGs and a contact sheet. Generated files live in ignored `output/`.

`scene/story.py` contains composition and animation timing only. Image source
import, alpha trimming, tinting, continuous time-based path reveal, animation,
caching, and export are main-library capabilities. Logos come from the supplied
`logo/` directory; no external images are downloaded. The existing folder spelling
`ai-comapny-graph` is preserved.
