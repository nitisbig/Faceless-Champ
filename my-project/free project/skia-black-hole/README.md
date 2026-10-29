# Skia black hole

A silent 60-second scene, using native Python, Faceless Champ and skia-python.
Pure black background, faint deterministic stars, glowing gradient accretion disk,
animated orbital knots, a warped grid, and cyan/gold light trajectories. Only key
annotations and equations appear; no headings, titles or subtitles. Default output
is 1920×1080 at 30 fps. No Docker or downloaded assets.

Run from the repository root:

```bash
# Full minute
.venv/bin/python my-project/skia-black-hole/render.py

# Bounded two-second motion preview (source seconds 40–42)
.venv/bin/python my-project/skia-black-hole/render.py --preview --quality 720p --overwrite

# Key frame, excerpt, or 4K full export
.venv/bin/python my-project/skia-black-hole/render.py --frame 24 --overwrite
.venv/bin/python my-project/skia-black-hole/render.py --range 18 21 --quality 1080p
.venv/bin/python my-project/skia-black-hole/render.py --quality 4k
```

`--output PATH`, `--fps N` and `--overwrite` are available. Files default to the
adjacent `output/` directory. Exports display progress, elapsed time and ETA.
JSON sidecars record source range, backend identity and native renderer counters.
`full_export_verified` remains false until the full encoded film is inspected.

The disk persists through a slow camera push: 0–18s introduces the horizon and
radius equation; 14–39s reveals the warped embedding grid; 32–54s introduces light
paths and the weak-field deflection equation; 52–60s returns to the disk and fades
to black. The grid and lensing are illustrative graphics, not numerical solutions
of general relativity. The deflection approximation is explicitly limited to
`b ≫ rₛ`; the drawn near-hole paths are schematic.

`build_scene()` returns the 60-second source scene. Its `sample(t)` creates fresh
immutable public paths, paints, shapes, arrows and native text at source time.
Use `BlackHoleRenderer()` as the renderer when calling `render` / `save_frame`
programmatically; its context manager closes the native renderer. This adapter
allows smooth path/gradient changes without adding unsupported animation tracks
or modifying the library. Equations use the bundled default DejaVu font for Greek
and mathematical glyph coverage. No raster artwork is involved.

Verification is intentionally limited to representative frames, one two-second
720p motion excerpt, timeline/endpoints, native-backend counters and lint checks.
A full-minute or 4K export is not verified here.

Key checks completed: exact 60-second duration; completely black frames at 0 and
60 seconds; grid frame at 24s and ray frame at 41s inspected; 720p/30 fps excerpt
contains 60 frames over 2 seconds and passes complete FFmpeg decode. Excerpt
backend counters report 12,360 native leaves and zero raster leaves. The final
annotation arrow was moved below the equation and checked in the 41s still.
