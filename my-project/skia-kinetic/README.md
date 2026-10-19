# Skia kinetic typography

A silent 45-second, 1920×1080 scene at 30 fps. Uses native Skia text shaping,
the bundled DM Sans variable font at weight 900, retained vector shapes, animated
subtree masks, and Faceless Champ's source-time animation tracks. No Docker or
external assets. Words are the graphic subject; no explanatory overlays.

Run from the repository root using its native Python environment:

```bash
# Full 45-second export (1080p / 30 fps)
.venv/bin/python my-project/skia-kinetic/render.py

# Two-second masked typography preview, original source time 15–17
.venv/bin/python my-project/skia-kinetic/render.py --preview --quality 720p --overwrite

# Still, custom section, or full 4K export
.venv/bin/python my-project/skia-kinetic/render.py --frame 18
.venv/bin/python my-project/skia-kinetic/render.py --range 30.6 38.2 --output /tmp/flow.mp4
.venv/bin/python my-project/skia-kinetic/render.py --quality 4k
```

Outputs default to `output/` beside the script. Each export writes a JSON sidecar
with its source range, dependency versions, and rendering identity.

The choreography moves through MOVE (staggered glyph entrances), MAKE IT BIG
(size and width changes), THROUGH (three sliding masked slices), STAY / IN /
MOTION (vertical replacements), FLOW (per-letter waves), and AGAIN (expanding
circle and closing shutters). The final fraction of a second holds on dark.

Limited verification: asserted 45-second timeline; inspected one still from each
sequence; exported and decoded a two-second 720p/30 preview; Ruff checks passed.
`output/key-frames.jpg` is a review contact sheet with timestamps outside the
video images. Full-length and 4K exports have not been rendered or verified.
