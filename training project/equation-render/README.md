# Equation render

Ten useful equations, animated one at a time in a **60-second, 1920×1080** composition.
The first two canvases each contain four scenes in a 2×2 grid. The last canvas
contains two larger scenes side by side (2 columns × 1 row). Completed panels stay
visible until their canvas transitions out.

From the repository root:

```bash
uv sync --extra equations
uv run --extra equations python 'training project/equation-render/render.py' --preview
uv run --extra equations python 'training project/equation-render/render.py'
```

The preview is 720p at 24 fps; the default is 1080p at 30 fps with supersampling.
Both now use antialias 2. CRF 18 for previews and 16 for final exports preserve
small equation symbols, and variable font weights strengthen headings and labels.
Outputs are saved in this project's `output/` directory as `equations-preview.mp4`
and `equations.mp4`. Add `--overwrite` when replacing an existing video.
The script resolves paths from its own location and can run from any directory.

```bash
# Storyboard: each equation and all three completed canvases
uv run --extra equations python 'training project/equation-render/render.py' --frames

# A frame during the first canvas transition
uv run --extra equations python 'training project/equation-render/render.py' --frame 24.3

# Customize the export or mute sound effects
uv run --extra equations python 'training project/equation-render/render.py' --silent --fps 60 -q qh

# Switch the formula, graph, and canvas colors together
uv run --extra equations python 'training project/equation-render/render.py' --color-scheme paper
uv run --extra equations python 'training project/equation-render/render.py' --color-scheme ocean --frames
```

| Canvas | Interval | Layout | Equations |
| --- | --- | --- | --- |
| Foundations | 0–24.6 s | 2×2 | Pythagorean theorem, quadratic formula, slope, compound interest |
| Change & chance | 24–48.6 s | 2×2 | Derivative, fundamental theorem of calculus, Newton's second law, Bayes' theorem |
| Patterns | 48–60 s | 2×1 | Normal distribution, Fourier transform |

Adjacent canvases overlap for 0.6 seconds. The three durations sum to 61.2 seconds;
subtracting the two overlaps gives **60 seconds**. The final canvas's two panels are
revealed at 48.6 and 53.8 seconds. `output/timeline.json` records all reveal times.
This is a curated selection of useful equations, not a universal ranking.

The default `midnight` scheme uses bright series colors over an ink canvas.
`paper` uses darker colors on a warm light canvas, and `ocean` uses a deep blue
canvas. The library's immutable `ColorScheme` exposes the same roles for other
projects; use `dataclasses.replace()` to make a custom palette.

| Diagram | Blue / primary | Amber / secondary | Mint / tertiary |
| --- | --- | --- | --- |
| Right triangle | Horizontal side a | Vertical side b | Hypotenuse c |
| Slope | Horizontal change in x | Vertical change in y | Slope m |
| Normal distribution | Density curve f | Mean μ | Spread σ and shaded region |
| Fourier transform | Time t | Frequency ν | Signal f |

Formula glyphs use `Equation(color_map=...)` and stay aligned as they are revealed.
The roles are defined in `SYMBOL_ROLES` in `scene/equations.py`. Graph labels and
strokes repeat those colors; axes remain neutral and shaded regions use subdued
alpha. `--color-scheme` applies the palette to every canvas. Other schemes get
their own MP4 names (such as `equations-paper.mp4`); frame/storyboard outputs are
in `output/frames/<scheme>/`. `output/timeline-<scheme>.json` records symbol colors;
`output/timeline.json` also contains the most recently rendered plan.

Scene authoring lives in `scene/`:

- `equations.py`: titles, formulas, explanations, examples, icons, and accent colors.
- `panels.py`: entrance, formula reveal, diagram drawing, emphasis, and reading window.
- `diagrams.py`: triangles, curves, shaded areas, force arrows, probability nodes, and signals.
- `story.py`: padded grids, staggered starts, shared headings, sound, and crossfades.
- `style.py`: shared palette, fonts, and helper constructors.

The example uses Faceless Champ's `Scene`, `Grid`, `Layer`, and `Sequence`. The library
now includes `Equation` with a `Write` reveal, drawable `Polyline` paths, rounded
rectangles, grid padding and delayed starts, and transparent composition with `Layer`.
Equations use the optional Matplotlib MathText dependency and its STIX math fonts.
[MathText](https://matplotlib.org/stable/users/explain/text/mathtext.html) supports
the TeX notation used here without a system LaTeX installation.

Fonts and icons are stored in the shared repository `assets/fonts/` and `assets/icons/`
folders. Space Grotesk and DM Sans come from [Google Fonts](https://github.com/google/fonts)
under the SIL Open Font License. Icons come from Google's
[Material Symbols](https://github.com/google/material-design-icons) under Apache 2.0.
Original procedural click, chime, and sweep effects are in `assets/sfx/equation-render/`
under CC0. Licenses and `assets/equation-render-sources.json` include provenance and
checksums. Rendering works offline after setup.

If assets are missing, download them once:

```bash
uv run --extra equations python 'training project/equation-render/download_assets.py'
```
