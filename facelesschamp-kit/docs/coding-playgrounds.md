# Coding playground projects

Install `facelesschamp-kit[playground]`. For web preparation, separately install the
browser with `python -m playwright install chromium`.

```sh
fc-kit init lesson --template coding-concept
cd lesson
fc-kit prepare main
fc-kit validate main
fc-kit preview main -o output/preview.mp4
fc-kit render main -o output/main.mp4
```

The other starters are `coding-web` and `coding-backend`. Each creates an editable
six-second example in `videos/main.py`, with complete source revisions and explicit
value/event bindings. The web starter allows 60 seconds per browser checkpoint.

`Project.prepare()` / `fc-kit prepare` execute trusted local code. They are not a
security sandbox. Build, validate, inspect, frame, storyboard, preview, and render
replay prepared assets without launching checkpoint programs or browsers. Run prepare
after changing a lesson, or `prepare --refresh` to explicitly re-execute cached inputs.

`ctx.playground(script, timeout=10, output_limit=1_000_000, fps=15)` declares a
prepared dependency. `coding_playground(ctx, script, ...)` composes it as a video,
accepting the same preparation settings plus timing and layout options.

`CodeEditor` and `CodingPlayground` are composition blocks exported from
`facelesschamp_kit.blocks`. Use `layout="side"` (default) or `"stacked"`,
`code_ratio=.5`, and a font size at or above the theme's minimum. Named children
`editor`, `canvas`, and optional `output` work with existing kit animations.

Use `start` for absolute placement, or `audio`, `subtitles`, `markers`, and `cues`
for a narration window. Checkpoint and event times are local to that window; authored
edits must finish before publication. Extra narration time holds the completed result.

The core package's `docs/coding-playgrounds.md` documents source checkpoints,
`emit`/`event` helpers, canvas items, bindings, time-seekable playback, and cache contracts.
Missing dependencies, unprepared lessons, execution failures, invalid bindings, and
layout problems produce actionable `PLAYGROUND_*` errors, also available through
`--json`. Reports list prepared assets and their fingerprints separately from exports.
