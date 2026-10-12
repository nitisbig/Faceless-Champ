# Faceless Champ guide

A 286.10-second, 16:9 quickstart authored against the original 819 word cues.
The guide has a black canvas, syntax-colored macOS-style editors, a prepared
Python playground, coordinate diagrams, animation timelines, and Kit workflows.
There are no guide titles or captions. The taught example text appears only in
its output canvas.

Run commands from this folder:

```bash
cd '/home/kingnit/Desktop/Faceless Champ/guide video'
python3 render.py --prepare
python3 render.py --check
python3 render.py
```

The last command exports only the first 12 seconds at **1280×720 / 10 FPS**.
Preparation has already been performed in this checkout. The opening preview
already exists; use `python3 render.py --overwrite` to regenerate it. The wrapper selects
the repository's `.venv` interpreter when available and imports both packages
from their current source folders. It also works when invoked by absolute path
from another directory. This project is intended to stay inside the checkout;
its image and font assets belong to the existing core/kit library.

## Preview and inspect

```bash
python3 render.py --quality low --fps 10 --range 114 121
python3 render.py --quality low --fps 30 --range 161 167
python3 render.py --frame 128
python3 render.py --storyboard
python3 render.py --list-scenes
```

Add `--output PATH` to choose a destination and `--overwrite` to replace it.
Frame/storyboard modes default to low resolution. `--check` validates the entire
composition without exporting video and writes `output/preflight.json`.

## Export the complete guide

**An explicit quality without a range exports the complete guide.**

```bash
python3 render.py --quality high --fps 30
python3 render.py --quality 4k --fps 30
```

Both FPS values, 10 and 30, work with every quality. High means 1920×1080;
4K means 3840×2160. High/4K use 2× supersampling and CRF 18. Low uses
1280×720, 1× antialiasing, and CRF 23 for testing.

Full exports are available for you to run. No complete guide, high-quality video,
or 4K video was exported during implementation; preview checks do not establish
complete-export or 4K media correctness.

## Authoring and preparation

`scene/story.py` composes twelve Kit segments on one master clock. Exact cue
indices trigger placements and motions. The full cue map is retained; the five
original 1 ms overlaps are explicitly accepted. Components have finite lifetimes,
and the guide uses no captions or sequence crossfades that shorten the timeline.

`examples/hello.py` is the runnable source of the example. Complete revisions are
selected by Python syntax nodes, and the editor shows animated changes with
explicit scrolling. `--prepare` executes those complete revisions through
CodingChamp checkpoints. `scene/checkpoint.py` records actual Text/Circle
components and their animation tracks; `scene/playground.py` reconstructs native
core scenes from that prepared data at export resolution. No source code executes
while checking, seeking, previewing, or exporting the guide.

Preparation also writes runnable `hello_text.py`, `hello_color.py`, and
`hello_duration.py` examples, and creates an actual Kit silent scaffold under
`.fc-kit/starter/`. The guide shows that scaffold's generated source. Re-run
`--prepare` after changing the baseline example, checkpoint adapter, code timing,
source audio, or cue file. Missing, stale, or corrupt dependencies must be prepared
again; ordinary exports never repair them by executing source code.

The supplied MP3, voiceover, and SRT files are preserved. The decoded MP3 ends at
284.569 s, while the last cue ends at 286.08 s. Preparation decodes the source to
`.fc-kit/narration.wav` and adds a silent tail to 286.10 s. Narration is attached
once at zero, with no time stretching or shifted words. Frame counts are 2,861
at 10 FPS and 8,583 at 30 FPS for a complete export.

## Verification

```bash
python3 verify.py
python3 verify.py --inspect-only
```

`verify.py` exports only nine short low-quality excerpts, totaling 64 seconds
across separate files. It checks CLI settings without exporting full/high/4K
video, forbids checkpoint execution during playback, compares cached and
uncached random-access frames, fully decodes the excerpts, and measures audio
correlation and lag against each matching source interval. It saves representative
encoded frames for visual inspection and writes `verification.json`.

`verification.json` records the actual checks. `full_export_verified` remains
`false`. Geometry checks cover lifetimes and sampled motion positions; they are
paired with inspected stills and encoded frames, rather than a claim of continuous
collision detection.
