# clean-flow feature tour

A connected, silent one-minute design test. Its warm dotted background, soft white cards, dark workspace/editor, orange focus, bold headings and measured flow motion follow the 13 reference images in `design inspiration/clean flow/`.

The project uses real public core and Kit components. Every placement receives the theme's smooth entrance and outro. Major scene windows overlap by 0.6 seconds around their nominal boundary; the total stays exactly 60 seconds. There are no audio tracks or captions.

Incoming content is layered above outgoing content. Headings and scene footnotes hand off at the nominal boundary with shorter flow windows, keeping text readable throughout each transition.

| Nominal time | Story | Public features |
|---|---|---|
| 0–6s | Plan a dashboard | Named local/package assets, typography, shapes, groups, masks, progress |
| 6–14s | Organize the workspace | OSChamp/Finder, virtual filesystem, rename, preview, drag, settings |
| 14–24s | Process project data | CodingChamp prepared Python checkpoints, bound values/events, console |
| 24–33s | Use the local dashboard | Actual HTML/CSS/JS capture, click/filter/publish, cursor, selector focus/highlight |
| 33–43s | Explore the result | Animated line/bar/donut charts, outline/satellite/earth maps, Nepal flag, metric/ring/gauge |
| 43–52s | Inspect the underlying module | ArchChamp assembly, explode/reassemble, orbit, highlight, section, dimensions |
| 52–60s | Connect every detail | Three legal chess moves, equation writing, whiteboard stroke, FlowChamp packet, completion |

From this directory:

```bash
# Required first: explicit Python/browser preparation. No movie is exported.
python3 render.py --prepare

# Structural/timing/features/layout/silence checks; prepared assets only.
python3 render.py --check

# Default: only the opening six seconds, 960×540 at 15 FPS.
python3 render.py --overwrite

python3 render.py --frame 28.7 --quality high --overwrite
python3 render.py --storyboard --overwrite
python3 render.py --range 42.7 46 --overwrite
python3 render.py --list-scenes

# Run this yourself to export the complete silent minute, 1920×1080 at 30 FPS.
python3 render.py --full --overwrite

# Optional resolutions/FPS for your own exports.
python3 render.py --full --quality 4k --fps 30 --overwrite
```

`--quality` changes resolution; it never selects the full minute. Only `--full` or an explicit `--range 0 60` does that. `--output PATH` redirects an artifact, and existing frames/videos require `--overwrite`.

Only `--prepare` runs authored Python checkpoints or starts Chromium. Check, frame, storyboard, preview and full export replay `.fc-kit/` assets. Source changes produce an actionable unprepared/stale error until you prepare again. The line, bar, donut and metric read actual emitted values from the two prepared Python checkpoints (109 → 121 sessions); their update uses the authored publication time. The HTML capture uses local files and a bundled font, at 1440×760/30 FPS; exporting at a larger size scales that capture. The fixture numbers and geometry are illustrative.

The wrapper uses this checkout's `.venv` when present. Dependencies are the core/Kit packages plus the coding, chess, web, maps and equations extras. Playwright Chromium and FFmpeg must be installed for preparation/export. Render paths do not install or download anything.

Project verification uses `python3 render.py --check` and the small replay-boundary tests. Frames and short excerpts are preview evidence; the full-minute export is intentionally left for you to run.

Local verification is recorded in `output/verification.json`, `output/preflight.json`, and `output/media-verification.json`. The final checks passed 282 layout samples, seven project tests, and 100 tests against the installed core/Kit/agent wheels (one optional browser test skipped). Four two-second silent excerpts passed complete decode and encoded-frame inspection. The storyboard and 1080p code, HTML and Arch stills were inspected. `full_export_verified` remains false.
