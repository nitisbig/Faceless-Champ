# Stock analysis

Six cue-synchronized scenes on a 1080×1620 (2:3) white canvas. The thesis:
NVIDIA's next test is whether growth can beat the expectations already priced in.
The plan is in [scene-outline.md](scene-outline.md); prompts in [img-info.md](img-info.md).

From this folder:

```bash
python3 render.py --image placeholder
python3 render.py --storyboard --image placeholder
python3 render.py --scene growth --image placeholder
python3 render.py --range 55.3 59.5 --image placeholder
python3 render.py --frame 37.8 --image placeholder
python3 render.py --list-scenes
```

The default renders **only the 7.280-second opening**, at 540×810 / 12 fps.
`--preview` explicitly selects the same opening. All times use the source audio
clock. `--overwrite` replaces the selected output; `-o PATH` selects an MP4,
PNG, or storyboard directory. `--fps 15` adjusts FPS; `--resolution design`
uses 1080×1620. From the repo root, run
`python3 'training project/stock-analysis/render.py'`. Paths work from any cwd.
If system Python lacks Pillow, use the repository's `.venv/bin/python`.

Save **1.png, 2.png, 3.png** in **image/**. Default `auto` mode loads existing
files and uses named boxes for missing files. `placeholder` forces boxes;
`required` requires all assets. Existing corrupt images raise errors.

**scene/chapters.py** contains the visual compositions; **scene/story.py** assembles
them and **main.py** exposes `stock_analysis_video()`. Reusable behavior comes
from the main package: `CueScene`, `ImageSlot`, charts, animations, storyboard
helpers, and source-time exports. **project.json** stores the palette, preview
settings, chapter cue anchors, frame times and dated revenue data.
Placements use design pixels; changing aspect ratio also needs layout changes.
**output/timeline.json** records chapter boundaries and absolute animation times.

| ID | Source seconds | Purpose |
| --- | --- | --- |
| opening | 0–7.280 | The question after the run |
| growth | 7.280–24.430 | Revenue and infrastructure demand |
| expectations | 24.430–38.540 | The valuation hurdle |
| risks | 38.540–47.280 | Chips, power, rates |
| verdict | 47.280–59.150 | Growth must beat expectations |
| closing | 59.150–62.088 | Disclaimer and audio tail |

Audio and both SRT inputs are preserved, including spoken 'asterisk' artifacts
and NVIDIA transcription errors. No captions repeat those artifacts. Last cue:
61.840s; the final scene preserves the audio tail to 62.088s. Video duration
rounds up to a whole frame, so it can be slightly longer.

The revenue comparison ($46.7B vs $96.2B, +106% YoY, fiscal Q2 FY26/FY27) uses
[NVIDIA's dated earnings release](https://investor.nvidia.com/news/press-release-details/2026/NVIDIA-Announces-Financial-Results-for-Second-Quarter-Fiscal-2027/).
Price/hurdle diagrams stay labeled as conceptual; no historical prices or
forecasts are invented. The ambiguous spoken valuation is shown qualitatively.

An entire-video export requires an explicit flag:

```bash
python3 render.py --full --resolution design --fps 30
```

Full-video export was **not run**. Verification covers selected low-quality clips,
stills, and a storyboard; details in **output/verification.json**.
