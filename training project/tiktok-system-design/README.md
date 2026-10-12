# TikTok-like system design

Complete 150.216-second narrated composition using Faceless Champ and FacelessChamp
Kit. Read [the cue outline](outline.md) for the nine scenes. Graphs and cue events
live in `scene/story.py`; rendering, caching, typography and diagnostics live in
the main libraries. Black canvas, terracotta emphasis, neutral strokes, labels only.

Run from this folder:

```bash
python3 render.py                         # 0–12 s, 960×540, 15 FPS
python3 render.py --list-scenes
python3 render.py --range 47 54
python3 render.py --scene delivery
python3 render.py --frame 149.1
python3 render.py --storyboard
python3 render.py --check --output output/check.json
python3 render.py --full                  # explicit later full export, 1080p/30
```

`--quality low|high`, `--fps 15|24|30|60`, `--output PATH`, and `--overwrite` are
available. Preview exports never select the whole film implicitly. Times use the
original audio clock. The wrapper selects the checkout's environment and both
local source packages, so `python3 /absolute/path/to/render.py` also works elsewhere.
For installed-package checks, set `FC_INSTALLED_ONLY=1` to skip checkout resolution.

`main.build(ctx)` and `facelesschamp.toml` also support normal `fc-kit` commands.
Keep `audio.mp3` and the original `cue-per-word.srt` here. The SRT has 399 word cues,
two accepted 1 ms overlaps, and an end at 150.08 s; the final visual holds through
the audio tail. `normal-subtitle.srt` is a reading aid rather than the timing source.

The architecture is illustrative. The narration explains public recommendation
signals and explicitly notes that TikTok's exact internal design is not public.

Validation records are in [verification.json](verification.json). A full export
has not been rendered or verified; `full_export_verified` remains false.
