# Stock analysis — motion redesign

A 62.088-second NVIDIA analysis on a 1080×1620 (2:3) white canvas. The redesign
uses large animated numbers, a true zero-baseline revenue comparison, a labeled
revenue-mix ring, causal diagrams, custom vector chip icons, and a moving growth
tracker. The existing three PNGs, narration, and both subtitle files are preserved
byte for byte. Visual pacing is faster; the narration remains at its original speed.

## Review and render

From this folder, use the repository virtual environment if system Python lacks
Pillow:

```bash
../../.venv/bin/python render.py --image required
../../.venv/bin/python render.py --storyboard --image required --overwrite -o output/redesign-storyboard
../../.venv/bin/python render.py --scene growth --image required
../../.venv/bin/python render.py --range 38.54 47.28 --image required
../../.venv/bin/python render.py --frame 37.8 --image required --resolution design
../../.venv/bin/python render.py --list-scenes
../../.venv/bin/python render.py --full --image required --resolution design --fps 30 -o output/stock-analysis-redesign.mp4
```

The default preview renders the 7.280-second opening at 540×810 / 24 fps.
`--full` explicitly selects the entire narration. Full design exports default to 2×
antialiasing, H.264 CRF 18, and the medium encoder preset. `--antialias 1`
uses native design-pixel rendering; values 2–4 select supersampling. The supplied
full redesign uses native rendering at 1080×1620 / 30 fps. `--fps` controls frame
rate; the full-export command above selects 30 fps. Times always refer to the
original audio clock. `--overwrite` replaces only the selected output. Paths work
from any cwd. Older MP4s in `output/` are previous designs, not this redesign.

`output/redesign-storyboard/storyboard.png` contains 17 source-time frames.
`output/redesign-verification.json` records the asset, timing, pacing, and media
checks for this version. The export duration rounds up to a whole frame. Re-run verification (including graph-marker geometry, full decode and five-window
narration alignment) with
`../../.venv/bin/python verify.py --media output/stock-analysis-redesign.mp4`.

## Visual sequence

| Scene | Source seconds | Visual evidence |
| --- | --- | --- |
| opening | 0–7.280 | Drawing price path and attached tracker; chip artwork; business-versus-stock question |
| growth | 7.280–24.430 | $46.7B → $96.2B; +106% YoY; +$49.5B; 2.06×; $89.0B data-center revenue and 92.5% mix; demand → buildout → NVIDIA |
| expectations | 24.430–38.540 | Growth → price → hurdle; ordinary versus exceptional growth against a priced-in bar |
| risks | 38.540–47.280 | Spending split between suppliers; a power-blocked deployment pipeline; rates rising as valuation pressure increases |
| verdict | 47.280–59.150 | Strong business versus a demanding price; future growth passes the expectation line |
| closing | 59.150–62.088 | Two watchpoints; narrated analysis disclaimer; original audio tail |

Meaningful visual beats arrive approximately every second. `scene/chapters.py`
records their absolute source times and durations in `output/timeline.json`.
A thin six-stage progress rail supplies continuous orientation. Motion is tied to
information: bar heights and counters interpolate together, graph dots follow
the same paths, arrows reveal causal relationships, and finished evidence clears
before the next composition appears.

`scene/design.py` owns typography, surfaces, icons and numeric formatting;
`scene/story.py` assembles cue-based chapters over continuous narration. All
rendering and animation behavior uses the main Faceless Champ public API.
`project.json` stores the exact earnings inputs, rounded display calculations,
chapter cue anchors, storyboard samples, and preservation checksums.

## Data and artwork

See [data-sources.md](data-sources.md) for verified figures and calculations.
Reported values use NVIDIA's dated Q2 FY2027 earnings release. Price, expectation,
and risk diagrams remain visibly illustrative; they contain no invented market
prices, forecasts, or impact percentages. The ambiguous spoken valuation is
shown qualitatively. The audio's existing transcription and spoken “asterisk”
artifacts are preserved; the scene does not repeat them as captions.

`--image required` loads all three original PNGs. `auto` uses existing images
and placeholders for missing files; `placeholder` forces named boxes. See
[img-info.md](img-info.md) for updated placements. The redesign never rewrites
or regenerates the artwork.
