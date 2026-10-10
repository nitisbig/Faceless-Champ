# CodingChamp tutorial

A 151.464-second Python classes tutorial, authored from all 447 original word cues.
The supplied audio, subtitles and reference code remain unchanged. Only `cue-per-word.srt`
controls the visual timing; neither subtitle file is rendered on screen.

Run from this directory:

```bash
python3 render.py --quality low --fps 20
python3 render.py --quality high --fps 30
python3 render.py --quality 4k --fps 60
```

**These export the full tutorial.** Defaults are high (1920×1080), 30 FPS, and midnight.
Low is 1280×720; 4k is 3840×2160. Outputs include quality/FPS in their filenames under
`output/`. Existing files require `--overwrite`; `--output PATH` selects another destination.
The wrapper reuses the repository `.venv` when available and finds assets relative to itself.
Install the checkout with its coding extra and install FFmpeg before using another environment:
`python3 -m pip install -e '../../[coding]'` (or run `uv sync --extra coding` at the repository root).

Fast inspection and partial exports:

```bash
python3 render.py --check
python3 render.py --list-scenes
python3 render.py --storyboard
python3 render.py --frame 118 --quality high
python3 render.py --range 33 41 --quality low --fps 20
python3 render.py --range 72 80 --quality low --fps 30
python3 render.py --range 110.64 124.84 --quality low --fps 30
```

`--range` uses original narration seconds for both visuals and audio. `--frame`,
`--storyboard`, `--check`, and `--list-scenes` do not export the full video.
Choose `--theme midnight`, `--theme ocean`, or `--theme paper` for the entire tutorial.
The storyboard contains time labels for review; those labels are not in the video.

The scene uses library CodingChamp editors, ordinary geometric diagrams, and health cards.
There are no title or subtitle overlays. `scene/outline.md` describes the visual proof and
source cue ranges. `scene/story.py` reads code through AST source spans without executing it.

The reference calls damage on Sam before healing Alex; the narration describes Alex healing
first. The visuals follow narration order. These operations affect separate objects and both
orders produce Alex: 85 HP and Sam: 90 HP. The reference file is preserved.

Verification covers the entire authored timeline structurally and representative short media
excerpts. See `VERIFICATION.md` for actual checks. Full export is intentionally unrun:
`full_export_verified: false`.
