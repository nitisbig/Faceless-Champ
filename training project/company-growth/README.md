# Company growth

A **45-second**, light-mode video of the latest ten largest US publicly traded
companies, tracked backward from October 2026 to 2010. The metric is nominal USD
**market capitalization**. Earlier ranks are within this fixed group, not the
historical top ten of the whole US market.

All scene components import `faceless_champ` from the main checkout's `src` folder.
Reusable chart behavior, numeric animation, and rendering improvements live in the
main library. This folder contains only scene composition, source data, and a CLI.

From the Faceless Champ repository root:

```bash
uv run python 'training project/company-growth/render.py' --preview
uv run python 'training project/company-growth/render.py' --overwrite
uv run python 'training project/company-growth/render.py' --frames
uv run python 'training project/company-growth/render.py' --frame 29.3
uv run python 'training project/company-growth/render.py' --quality 4k --output /tmp/company-growth.mp4
```

From this project folder: `uv run python render.py --preview`.
The CLI also accepts `--fps`, `--antialias`, and `--output`. Preview renders at
1280×720 / 24 fps; default renders at 1920×1080 / 30 fps. Both are 45 seconds.
Rendering requires FFmpeg and Pillow; no downloads or chart dependencies are needed.
The video is silent so feedback can focus on the visuals.

Outputs go to `output/`: MP4, `timeline.json`, and optional frames/storyboard.
For frame mode, `--output` selects a PNG. For storyboard mode it selects a directory.
Use `--overwrite` to replace a video or single frame; storyboard exports refresh
their generated images.

## Story

| Time | Visual |
| --- | --- |
| 0–4s | Introduction and the latest group's value as a donut |
| 4–30s | Horizontal ranking race with stable company colors and live labels |
| 30–39s | Absolute trend lines and baseline growth multiples |
| 39–45s | Final ten-company ranking, combined value, and concentration |

## Data and methodology

[market-cap.json](data/market-cap.json) contains the offline, reproducible snapshot,
source URLs, company colors, missing observations, and methodology notes.
The latest cohort was selected from
[CompaniesMarketCap's US ranking](https://companiesmarketcap.com/usa/largest-companies-in-the-usa-by-market-cap/)
on **4 October 2026**. Values come from each company's linked market-cap history.
The sources report October 2–3 snapshots; they are not 2026 year-end observations.

2010–2025 values are the source's year-end observations. Alphabet's 2010–2013 Google
predecessor history comes from
[StockAnalysis / Nasdaq Data Link](https://stockanalysis.com/stocks/googl/market-cap/).
AVGO's history includes Avago and later acquisitions. Meta starts in 2012; the
selected SpaceX source contains only 2026. Missing observations are shown as
**No public data**, without a bar; they are not assumed to be zero market value.
New public observations appear at their snapshot boundary.

Between snapshots the animation interpolates to make changes readable. These are
visual transitions, not measured monthly values. The race's axis adjusts to keep
early years readable. The trend chart has a fixed scale. The eight companies with
a 2010 value are eligible for growth multiples; the three largest multiples are
shown. Market-cap growth includes share-count changes and acquisitions and is not
investment total return. The final concentration percentage refers to this group
of ten, not the entire US stock market.

To change the story for feedback, edit `scene/story.py`. To update the data, replace
the snapshot and update its date, sources, and cohort together.
