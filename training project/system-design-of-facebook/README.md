# System design of Facebook

A silent, 32-second FlowChamp architecture study using the **clean-flow** layout:
warm gray dot grid, white rounded cards, soft shadows, packaged DM Sans, neutral
connectors and orange packets. Four focused views replace one crowded diagram.
All symbols and fonts are local; no preparation, downloads, audio or captions are required.

| Nominal time | View | What moves |
|---|---|---|
| 0–8s | Request routing | Client → load balancer → API → feed/post service; a response travels back |
| 8–16s | Publish a post | Commit → event queue → concurrent feed/notification workers |
| 16–24s | Build the feed | Candidate posts + graph/cache signals → aggregator → ranking → client |
| 24–32s | Deliver media | Upload → origin storage; CDN miss → origin fetch → delivery; later cache hit |

Cards overlap by 0.6 seconds around each nominal boundary. Text hands off at the
boundary. Each diagram uses explicit ports/routes, staged reveals and wire drawing
without a drawing tool, then packet travel and brief highlights.

This is an **illustrative teaching design**, not a diagram of Facebook's exact
current production stack. In particular, the event queue and worker arrangement
are generic asynchronous processing concepts. The simplified post-store → queue
arrow represents event publication after a successful commit; it does not model
an atomic database/queue transaction, outbox, retries, deduplication or delivery guarantees.
Feed eligibility, privacy/integrity checks, model internals, replication and failures
are outside this short visual test. No benchmark or production scale is implied.

## Run

From this directory:

```bash
python3 render.py --check
python3 render.py --list-scenes
python3 render.py --storyboard --overwrite
python3 render.py --frame 19.5 --quality high --overwrite

# Default export: ONLY the first 10 seconds, 960×540 at 15 FPS.
python3 render.py --overwrite

# Optional targeted excerpt; this is not needed for the delivered preview.
python3 render.py --range 25 29 --overwrite
```

The wrapper uses the repository's `.venv` when available and imports the public
core/Kit APIs from this checkout. FFmpeg is required for video export. Existing
artifacts require `--overwrite`; `--output PATH` redirects the result. `--quality`
changes resolution, not the selected time range. There is no implicit full export.

Default output: `output/facebook-0-10s-low-15fps.mp4`. The storyboard samples all
four views and their transitions without encoding the complete scene.
`output/preflight.json` records sampled geometry/timing/silence checks;
`output/verification.json` records the delivered preview's media and visual checks.
**Full-scene export remains unverified** (`full_export_verified: false`).

## Reusable feature exercised

The public core `FlowEdge` now accepts `label_position` (a fraction of routed path
length) and `label_offset` (viewport design pixels). This scene uses them to keep
branch labels clear of destination cards, without changing packet paths. The
default `0.5` and `(0, 0)` retain existing output. Core rendering, bounds and
collision diagnostics share the adjusted label geometry; `FlowCanvas` needs no adapter.

## References

These historical public descriptions inform the teaching model rather than certify
its complete topology:

- [Meta: How machine learning powers Facebook's News Feed ranking algorithm (2021)](https://engineering.fb.com/2021/01/26/ml-applications/news-feed-ranking/) — aggregation and ranking.
- [Meta: TAO: The power of the graph (2013)](https://engineering.fb.com/2013/06/25/core-infra/tao-the-power-of-the-graph/) — objects/associations, cache and persistent storage.
- [Meta: Needle in a haystack: efficient storage of billions of photos (2009)](https://engineering.fb.com/2009/04/30/core-infra/needle-in-a-haystack-efficient-storage-of-billions-of-photos/) — upload/storage and cached photo delivery.

## Verified result

The delivered excerpt is exactly **10 seconds, 960×540, 15 FPS, 150 H.264 frames,
zero audio streams** and passes a complete FFmpeg decode. The final 16-frame
storyboard, one 1080p still and six decoded preview frames were visually inspected.
The full scene passed 389 FlowChamp geometry samples and 274 canvas-layout samples
with no findings. Twelve default-label frames matched pre-change raster hashes exactly.

All core test files passed in batches (**590 passed, 2 skipped**); all Kit test files
passed separately (**236 passed**). Ruff and whitespace checks passed. Earlier
monolithic runs were interrupted with exit 143; the completed batches cover every
test file. The complete 32-second movie was not rendered.
