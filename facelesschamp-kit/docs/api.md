# Public API and workflow

## Project configuration

```toml
schema_version = 1
[project]
name = "my-video"
seed = 0
safe_margin = 64
caption_space = 220
[videos.main]
factory = "videos.main:build"
format = "shorts" # or landscape
theme = "midnight" # or light, whiteboard
captions = false
[profiles.preview]
fps = 15
antialias = 1
preset = "veryfast"
[profiles.final]
fps = 30
antialias = 2
preset = "medium"
```

Unknown configuration fields are errors. Export profiles additionally accept paired width/height, quality, and crf. Their dimensions must preserve canvas aspect ratio. Omit dimensions for portable format switching: preview defaults to a 540-pixel short edge, final to the design canvas (1080×1920 or 1920×1080). Preview and final profiles are supplied automatically when absent. Additional named profiles are allowed. Final-profile exports reject placeholders unless `allow_placeholders=True` / `--allow-placeholders` is explicit.

## Python services

- `Project(root)`: load a directory or TOML file.
- `project.build(video_id="main", strict_assets=False) -> CompiledVideo`: fresh factory, fresh components, compile and validate supported rendering types.
- `project.validate(...) -> dict`: additionally validate all export profiles.
- `project.frame(video_id, time, output, overwrite=False)`: source-clock PNG.
- `project.storyboard(video_id, output, overwrite=False)`: segment midpoint frames and contact sheet.
- `project.export(video_id, output, preview=False, profile=None, segment=None, start=None, end=None, overwrite=False, allow_placeholders=False)`: MP4, bounded preview or full export.
- `CompiledVideo.composition`, `.context`, `.report`, `.duration`: engine output and metadata.

Programmatic output paths, like CLI output paths, are relative to the calling working directory. Resource paths from context are relative to the project. A build executes trusted Python project code; this is not a sandbox. Builds temporarily isolate project imports, serialized through a process-local lock. Factory/module globals are not persistent state between builds.

`BuildContext` supplies `root`, `canvas`, `theme`, `assets`, `seed`, seeded `random`, safe-area `bounds`, `load_json(path)`, and `load_csv(path)`. JSON and CSV loaders return ordinary Python values; domain-specific validation belongs to your template. Missing observations must not be implicitly replaced by zero.

## Video, segments, and motion

`Video(ctx).segment(name, duration=N)` appends. Supply `start=T` for an absolute window, or `window=voice.between(...)` for a cue window. Names must be unique. Segments are context managers but can also be populated directly. Empty segments represent intentional holds/gaps.

`segment.add(block, id=None, bounds=None, anchor="center", enter=None, enter_duration=None, z_index=0)` returns a placement handle. `bounds` overrides the context safe area, including for deliberate overlays. Entry recipes are `fade`, `pop`, and `stagger`; their default duration comes from the theme (0.6 seconds). They must fit the segment. Stagger enters immediate children in order.

`segment.play(handle_or_child, callback, at=0, duration=1)` schedules a core Animation. Local `at` becomes global time once. Use `handle["value"]` for named children. Overlapping writes to the same property are rejected by the engine; different properties and distinct placements may overlap. A placement disappears exactly at its segment end, after all its animations complete.

`segment.add_core(lambda ctx, bounds: component, ...)` supports advanced authoring. Return a fresh Component or BlockBuild every invocation. Direct components must already fit the supplied bounds. A complete core Scene/Sequence/Grid/Layer can also be returned by a project factory; segment metadata is unavailable for those entries.

## Custom blocks and themes

Implement `compose(context, bounds) -> BlockBuild(root, children={}, bounds=None)`. Construct fresh core objects every time, assemble all Group membership, and finish layout before returning. Named children must belong to that root's hierarchy. Measurement uses the root's actual core bounds; claimed bounds cannot bypass overflow checks.

Block content props are defensively copied when added. Prefer frozen dataclasses and tuples. Store core components only inside `compose`, never on the reusable block definition. Do not mutate the context while composing a block. Failed compilations publish no result and can be retried with fresh components.

Themes are frozen dataclasses in `facelesschamp_kit.themes`. Assign a custom Theme to `ctx.theme` in the factory before constructing Video; update `ctx.canvas` with a matching background if desired. Heading, TextPanel, and MetricCard support default/accent/muted variants and explicit color overrides. Precedence is theme defaults → chosen theme → variant → explicit color. Stack and Split are composable blocks; Split uses rows in portrait and columns in landscape.

`whiteboard_basic(ctx, *, scenes, audio=None, subtitles=None, markers=None, captions=None, theme=None,
draw_fraction=0.7)` and immutable `WhiteboardScene` recipes are available from `facelesschamp_kit.templates`.
`WhiteboardDrawing` and its five geometry specifications are exported from `facelesschamp_kit.blocks`.
See the [whiteboard API and examples](whiteboard.md). The factory applies `WHITEBOARD` or its explicit theme to the context
and canvas; pass `theme=ctx.theme` to use project configuration. `fc-kit init ... --template whiteboard-basic` generates
an editable two-scene landscape starter.

## Assets

`assets/manifest.json` maps unique names to entries:

```json
{
  "photo": {"type": "image", "path": "assets/images/photo.png", "source": "Original artwork", "license": "Project-owned"},
  "voiceover": {"type": "audio", "path": "assets/audio/voice.wav"},
  "word_cues": {"type": "subtitle", "path": "assets/cues.srt"},
  "font": {"type": "font", "package": "my_pack", "resource": "fonts/body.ttf"}
}
```

Use `ctx.assets.image/audio/subtitle/font(id)` or `resolve(id, kind, mode)`. Entries may include checksum (SHA-256), source, license, and attribution. Package resources materialize into a content-addressed project cache, so they outlive temporary resource handles. No plugin installation or network access occurs. Image modes: required fails, placeholder always substitutes, auto substitutes only when absent. Substitutions are labeled and reported. Corrupt present files fail rather than silently becoming placeholders.

Fresh builds rehash referenced assets and use fresh renderers. Inputs changed during an active export are unsupported; do not edit source media while exporting.

## CLI and diagnostics

`fc-kit [--project PATH] [--json] COMMAND`. Commands: init, doctor, list videos/blocks/themes/templates, validate, inspect, frame, storyboard, preview, render. `inspect main --json` is also accepted. Preview supports `--segment ID` or paired `--start/--end`.

Library errors are KitError with stable `code`, `message`, and optional scope. CLI exits 1 for build/runtime failures and 2 for argument syntax failures. JSON build failures return an `error` object on stderr; argparse syntax diagnostics remain plain text. Reports in `.fc-kit/reports/` include a versioned schema, original segment/cue timing, asset checksums, source hashes, settings, environment, and output metadata. Fingerprints are audit identities, not promises of byte-identical media across machines. Unregistered external data dependencies are not discovered; declare them through the asset registry. Persistent render-result caching is intentionally absent.
