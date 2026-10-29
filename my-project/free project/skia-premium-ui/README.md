# Premium UI / native Skia

60 seconds, silent, entirely graphical. No titles, subtitles, numbers, or font
assets. Uses the existing Faceless Champ public APIs with `backend="skia"`.
No Docker, browser, downloads, or external graphics are involved.

The visual sequence moves from a glass-style dashboard with native Bézier charts
and a live histogram, to floating sliders, toggles, a pressable icon button and a
progress ring, then a processor diagram with flowing packets, and back to the
dashboard. Panels overlap briefly during transitions. Translucent gradients,
edge highlights, soft shadows, and background light fields simulate glass;
this is not backdrop blur.

Run from the repository root using the installed native environment:

```bash
# Full 60-second scene: 1080p / 30 FPS by default
.venv/bin/python my-project/skia-premium-ui/render.py

# Bounded two-second preview, source time 7–9 seconds
.venv/bin/python my-project/skia-premium-ui/render.py --preview --quality 720p

# Still or custom excerpt
.venv/bin/python my-project/skia-premium-ui/render.py --frame 28
.venv/bin/python my-project/skia-premium-ui/render.py --range 25 28 --quality 1080p

# Optional 4K full export
.venv/bin/python my-project/skia-premium-ui/render.py --quality 4k --fps 30
```

Use `--overwrite` when replacing an existing output. Files go into `output/`
beside this entrypoint; `--output PATH` overrides the destination. Each export
writes a JSON sidecar with the source interval and rendering identity.

Key verification performed: built the 60-second timeline; checked the absence
of text and audio; visually inspected 1080p frames at 8, 28, 45, and 56 seconds;
exported the 7–9 second excerpt at 1280×720 / 30 FPS (60 frames); verified its
H.264 metadata and complete FFmpeg decode. Ruff checks pass. No full export or
broad package test suite was run. `full_export_verified` remains false.
