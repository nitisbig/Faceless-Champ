# Country Economy

A six-minute narrated finance explainer with **14 chapters**, composed using the
main Faceless Champ library. `scene/` contains the art direction and compositions;
`main.py` exposes `country_economy_video(image_mode="auto")`; `render.py` provides
full exports and feedback previews. Image slots, subtitle tolerance, caching, and ranged exports are
implemented in the main library rather than in this example.

From this project folder:

```bash
python3 render.py
python3 render.py --fps 60 --resolution 4k
python3 render.py --fps 24 --resolution 1280x720
python3 render.py --image placeholder --preview
python3 render.py --image placeholder --storyboard
python3 render.py --image placeholder --scene deficit
python3 render.py --image placeholder --range 120 127
python3 render.py --image placeholder --frame 235.2
python3 render.py --list-scenes
```

From the repository root, use `python3 'training project/country-economy/render.py'`
with the same options. Python 3.12+, Pillow, FFmpeg, and ffprobe are required;
`uv sync --extra equations` installs the repository development environment. The
example itself needs no equation dependency or network downloads.

The default command renders the **full 360.4-second narration at 1920×1080 / 30 fps**,
with antialias 2 and CRF 18, to `output/country-economy-full.mp4`.
Use `--fps NUMBER` for a custom frame rate, including fractional rates such as 29.97.
Use `--resolution` (or `-r`) with **540p, 720p, 1080p, 4k**, or **WIDTHxHEIGHT**.
Custom dimensions must be positive even integers and preserve the 16:9 canvas.

`--scene` renders a chapter; `--range START END` uses absolute narration times and
trims visuals and audio together. These modes use the same export defaults.
`--preview` renders only the **0–16.7s opening** at **960×540 / 15 fps**, antialias 1,
CRF 26. `--all-preview` exports the full narration at those low-quality settings.
Explicit `--fps` and `--resolution` override either preview preset. Resolution also
controls the size of `--frame` and individual storyboard PNGs.

Outputs go to `output/`. Use `--output` for an MP4, single-frame PNG, or storyboard
directory as appropriate. Use `--overwrite` to replace the chosen artifact.
The CLI writes `output/timeline.json` with exact cue-derived chapter boundaries,
visual events, palette, and storyboard times.

Place `1.png` through `6.png` in **image/**. Default `--image auto` picks them up on
the next render; missing images remain placeholders. `--image placeholder` always
shows labeled boxes; `--image required` fails on missing assets. See [img-info.md](img-info.md)
for dimensions, placements, and illustration prompts.

## Art direction and timing

The design canvas is 1920×1080, with 96 px side margins.
White background, terracotta accents, taupe outlines, ivory cards, charcoal text;
Cormorant Garamond headings, DM Sans body text, and Material Symbols outline icons.
Existing licensed assets are shared from the main repository's `assets/` folders.

The scenes omit the recurring title banner, chapter numbers, chapter headings,
and subtitles, keeping the diagrams and their explanatory labels.

The original **991 word cues** drive visual events.
Four 1 ms source overlaps use `SubtitleTrack.from_srt(..., overlap_tolerance=0.001)`;
neither source subtitle file is edited. The visual sequence uses cuts and brief
entrances on its own clock. A continuous audio layer carries narration
from zero, so scene transitions do not accumulate timing drift.

The source MP3 is 360.384s; the final subtitle ends at 360.4s. The last visual holds
through that endpoint, and export pads the tiny remaining audio gap with silence.
The original spoken ending and transcript are retained.

| Scene ID | Source interval | Visual |
| --- | --- | --- |
| opening | 0–16.7s | News and financial warning cards |
| household | 16.7–40.5s | Household balance and government options |
| budget | 40.5–57.37s | Tax inflows and six spending categories |
| deficit | 57.37–66.4s | $100B revenue, $110B spending, $10B deficit |
| bonds | 66.4–84.16s | IOU and repayment with interest |
| debt | 84.16–103.5s | Illustrative $100B → $200B → $300B debt |
| shocks | 103.5–127.1s | Shocks and 3% → 6% → 10% → 20% rates |
| interest-loop | 127.1–148.2s | Debt feedback cycle and borrowing limit |
| currency | 148.2–185.5s | Own-currency versus foreign-currency debt |
| reserves | 185.5–221.4s | Currency sources, reserves, and imports |
| conversion | 221.4–241s | Currency value halves; local repayment cost doubles |
| policies | 241–294.9s | Austerity, assistance, restructuring, default |
| aftermath | 294.9–327.47s | Continued activity, trust, and household effects |
| recap | 327.47–360.4s | Constraints and the closing confidence statement |

Charts show the narration's **illustrative numbers**, not historical country data.
Reserve bars are conceptual rather than measured values. The conversion example
shows percentages and a repayment multiplier, avoiding an invented exchange rate.
