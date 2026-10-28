# Claude for a Month

A silent 60-second native-Skia motion graphic. One month of Claude Code, from the
first small idea to the final launch.

The film is a cinematic, light-mode editorial piece. Instead of counting one second
per day, it moves through three acts of three visual beats each: **EXPLORE**,
**BUILD**, and **SHIP**. Every beat pairs a sparse typographic statement with a
full-screen generative motif, orbital rings, drafting marks, satellite cards, and
travelling signal paths. A thirty-tile mosaic brings the whole month back at once
before a final brand card.

| Time | Section | Beats |
| --- | --- | --- |
| 0:00–0:08 | Cold open | `STARTS SMALL.` / one idea becoming a bloom |
| 0:08–0:22 | EXPLORE | `FOLLOW THE SIGNAL.` / `MAP THE UNKNOWN.` / `MAKE CONNECTIONS.` |
| 0:22–0:36 | BUILD | `STRUCTURE THE IDEA.` / `MAKE IT TANGIBLE.` / `TUNE THE SYSTEM.` |
| 0:36–0:50 | SHIP | `MAKE IT MATTER.` / `SEND IT FORWARD.` / `LAUNCH THE MONTH.` |
| 0:50–0:56.8 | Month mosaic | all 30 day tiles in a six-by-five grid |
| 0:56.8–1:00 | Finale | `CLAUDE` / `FOR A MONTH` / `ONE IDEA. THIRTY DAYS. SHIPPED.` |

The palette moves from violet/teal, through teal/olive, to coral/ochre on warm
paper. Solar flash transitions, soft bloom, drifting rays, giant ghost act
numerals, a fine grain layer, and a restrained vignette carry the film between
chapters.

## Run

From the repository root, using the checkout environment:

```bash
# Full 60-second film, 1080p / 30 FPS
.venv/bin/python my-project/claude-for-month/render.py

# Two-second preview from the build act (source 24–26 s), 720p
.venv/bin/python my-project/claude-for-month/render.py --preview --quality 720p --overwrite

# Key stills
.venv/bin/python my-project/claude-for-month/render.py --frame 2.5 --overwrite
.venv/bin/python my-project/claude-for-month/render.py --frame 11 --overwrite
.venv/bin/python my-project/claude-for-month/render.py --frame 25 --overwrite
.venv/bin/python my-project/claude-for-month/render.py --frame 40 --overwrite
.venv/bin/python my-project/claude-for-month/render.py --frame 53 --overwrite
.venv/bin/python my-project/claude-for-month/render.py --frame 58.5 --overwrite

# A custom excerpt
.venv/bin/python my-project/claude-for-month/render.py --range 55 58 --quality 1080p \
  --output my-project/claude-for-month/output/excerpt-55-58.mp4 --overwrite
```

Add `--overwrite` when replacing existing files. Outputs go into `output/`
beside this README; `--output PATH` overrides the destination. Each export writes
a JSON sidecar with the source range and rendering identity.

## Concept notes

- The left third stays typographic: act index, day range, and a two-line statement
  that reveals upward into place.
- The right side carries a large daily motif at poster scale, with an orbit, bloom,
  drafting ticks, a secondary signet, and up to three satellite cards. Cards are
  clipped at the frame edge when the composition calls for it.
- Each act uses three cards from the existing motif library rather than one per
  second, giving every image room to breathe.
- Chapter changes are covered by a solar flash: a warm veil, expanding bloom,
  spinning rays, and two rings. The outgoing scene washes out as the next one
  emerges, so the cut feels optical rather than mechanical.
- The month mosaic reuses all thirty daily motifs at miniature scale, then the
  film ends on a centered wordmark with a warm halo and a short tagline.
- The top-left wordmark and top-right line remain persistent, fading out just
  before the finale.

## Verification

Built and inspected on the checkout environment:

- 60-second scene construction, duration exactly `60.0`.
- 1080p stills inspected across the cold open, all three acts, transitions, the
  month mosaic, and the finale.
- Two-second 1280×720 / 30 FPS preview exported and fully decoded.
- `ruff check` and `py_compile` pass.
- No full 1080p export was run; `full_export_verified` remains `false` in the
  sidecars.
