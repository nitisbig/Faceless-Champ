# Skia infographics scene

A silent, 60-second motion study on pure black. All geometry, paths, counters,
and text use Faceless Champ's native Skia renderer. Values are synthetic demo
data. Only data labels appear on screen.

| Time | Graphic |
| --- | --- |
| 0–12 s | 12,480-unit counter, accumulation dots, progress line |
| 12–24 s | Three radial percentages: 72%, 54%, 89% |
| 24–36 s | A/B bars: 40 versus 68, with +70% uplift |
| 36–48 s | 76-of-100 dot grid and synchronized percentage arc |
| 48–60 s | Annual trend: 100 to 184, with +84% growth |

Run from the repository root with the local Python environment:

```bash
.venv/bin/python my-project/skia-infographics/render.py --overwrite
```

Default output: `output/skia-infographics.mp4`, 1920×1080, 30 fps, H.264.
No Docker, audio, external assets, or network access is needed to render.
The environment needs the checkout installed with its Skia extra and FFmpeg.

Optional bounded rendering:

```bash
.venv/bin/python my-project/skia-infographics/render.py --preview --overwrite
.venv/bin/python my-project/skia-infographics/render.py --frame 21 --overwrite
.venv/bin/python my-project/skia-infographics/render.py --range 36 39 --overwrite
.venv/bin/python my-project/skia-infographics/render.py --quality 4k --overwrite
```

The adjacent export JSON records source timing and renderer identity. Exporting
alone leaves `full_export_verified` false; separate verification is recorded in
`output/verification.json`. `output/key-frames.jpg` shows five representative
scene frames. Validation is deliberately limited to key visuals, scene timing,
lint, and one encoded export check.
