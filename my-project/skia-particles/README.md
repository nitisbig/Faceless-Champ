# Skia particle and generative art

A silent 60-second scene on pure black, with no headings, labels, or text.
Native Python and Faceless Champ's Skia CPU renderer; no Docker or external assets.
Default export: 1920×1080, 30 fps.

Five overlapping movements dissolve into one another:

| Source time | Graphics |
| --- | --- |
| 0–15s | Orbiting particles with fading luminous trails |
| 11–28s | Five rotating mathematical spiral arms |
| 24–40s | Layered 3:2 Lissajous curves and traveling lights |
| 36–52s | Undulating procedural point field |
| 48–60s | Breathing golden-angle phyllotaxis bloom, fading to black |

Run from the repository root:

```bash
# Full minute
.venv/bin/python my-project/skia-particles/render.py

# Two-second preview at source time 6–8s
.venv/bin/python my-project/skia-particles/render.py --preview --quality 720p --overwrite

# Still, custom excerpt, or full 4K export
.venv/bin/python my-project/skia-particles/render.py --frame 55
.venv/bin/python my-project/skia-particles/render.py --range 40 43 --output /tmp/point-field.mp4
.venv/bin/python my-project/skia-particles/render.py --quality 4k
```

Outputs are placed in `output/` beside the script. JSON sidecars record source
range, rendering identity and native backend counters. Export progress includes
elapsed time and ETA. Full-minute and 4K exports have not been verified.

The project-local `ParticleArt.sample(t)` computes immutable geometry directly
from source time, without a simulation history or randomness. `ParticleRenderer`
implements the public renderer protocol and delegates painting to Faceless Champ's
Skia renderer. Dots are batched cubic circle contours; glow uses concentric fills
and layered strokes. There are no raster sprites or direct Skia drawing calls.
For imported use, pass `renderer=ParticleRenderer()` to `render` or `save_frame`,
and close it afterward (or use its context manager).

Limited checks: exact 60-second duration, black first/last frames, deterministic
out-of-order sampling, five inspected key frames, and native vector leaves with
zero raster leaves. `output/key-frames.jpg` has timestamps outside scene images.
The two-second preview passed MP4 probing (1280×720, 30 fps, 60 frames) and a
complete FFmpeg decode. Ruff and whitespace checks passed.
