# Good at math

A 60.2-second Faceless Champ scene based on `layout.png`: warm paper, fine serif
type, orange/green accents, outline icons, and short arrows around a central idea.
All 12 story beats use cue numbers from `cue-per-word.srt`. Each icon/label reveal
starts at its corresponding word. The original narration starts at zero, and the
final message holds briefly after the last word. No added music or sound effects.

Every diagram icon, symbol, and related label now has an animated entrance. The
scene cycles through pop, slide, zoom, bounce, spin, typewriter, and fade effects,
with fade, slide, zoom, and pop exits. Pulse, shake, wiggle, scaling, translation,
rotation, and opacity changes provide emphasis. Arrows draw in at the same cue.
Late cues use shorter animations to preserve the original scene boundaries.

From the repository root:

```bash
# Fast feedback render: 720p, 24 fps.
uv run python 'training project/good-math/render.py' --preview

# Full render: 1080p, 30 fps, antialiasing.
uv run python 'training project/good-math/render.py'

# Replace a previous render after editing the scene.
uv run python 'training project/good-math/render.py' --preview --overwrite

# Render the motion test at 30 fps to a separate preview.
uv run python 'training project/good-math/render.py' --preview --fps 30 \
  -o 'training project/good-math/output/good-math-motion-preview.mp4' --overwrite

# Storyboard only, or inspect a particular narration time.
uv run python 'training project/good-math/render.py' --frames
uv run python 'training project/good-math/render.py' --frame 24.7
```

The script also works from this folder with `uv run python render.py`, or with an
absolute script path from another working directory when Pillow is installed.
FFmpeg/ffprobe must be on PATH for video export. The script uses this checkout's
`src/faceless_champ` directly. Outputs go to this project's `output/` folder;
`-o path.mp4` selects another output. `--no-captions` hides the caption line.
`--quality qk`, `--fps 60`, and `--antialias 1` override render settings.

Edit `scene/story.py`: `BEATS` controls the story, `SLOTS` controls icon positions,
and the palette/font constants control the design. Scene timing uses original,
one-based SRT cue IDs rather than guessed seconds. `output/timeline.json` records
the visual beat times. `output/animations.json` records every effect's timing,
duration, and affected components, including previews rendered with `--frames`.
Change `ENTRANCES`, `EXITS`, and `EMPHASES` to select the motion styles.
The subtitle text is preserved verbatim, including the
spoken “asterisk” artifacts and unusual wording in the supplied files.

Assets are already local in the repository's shared `assets/fonts/` and
`assets/icons/`. The font is [Cormorant Garamond from Google Fonts](https://github.com/google/fonts/tree/main/ofl/cormorantgaramond)
(SIL Open Font License); the icons are [Google Material Symbols](https://github.com/google/material-design-icons)
(Apache 2.0), rasterized from their original outline glyphs at weight 200.
Their licenses and a source/checksum manifest are included. Rendering is offline.
To restore missing assets, run `uv run python download_assets.py` from this folder
with network access. This downloads the fonts and icon font, then recreates the
transparent icon PNGs; it does not change the narration or subtitle sources.

Reusable library additions: `SubtitleTrack`, `SubtitleCue`, `Captions`, `Icon`,
`Arrow`, `Scene.at()`, `Scene.wait_until()`, and `Scene.remove()`.
Reusable motion additions: `SlideIn`, `SlideOut`, `ZoomIn`, `ZoomOut`, `PopIn`,
`PopOut`, `BounceIn`, `SpinIn`, `Pulse`, `Shake`, `Wiggle`, and `ease_in`/`ease_out`.
Custom `Animation` objects now support keyframes, relative transforms, and easing.
