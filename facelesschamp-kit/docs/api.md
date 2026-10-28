# Public API and workflow

Current source: **2.0.0rc1**, requiring Core **>=2.0.0rc1,<3.0.0**.

| Capability | Public interface | Guide |
| --- | --- | --- |
| Prepared coding lessons | CodeEditor, CodingPlayground, ctx.playground, templates.coding_playground | [Coding playgrounds](coding-playgrounds.md) |
| HTML walkthroughs | WebWalkthrough, WebElement | [HTML to video](html-to-video.md) |
| Virtual OS tutorials | OSWalkthrough, FinderWindow, SettingsWindow | [OS UI](os-ui.md) |
| Scripted graphs and networking cards | FlowCanvas, FlowCard, FlowPopup, FlowBackdrop | [FlowChamp](flowchamp.md) |

### Explicit preparation

`Project.prepare(video_id="main", refresh=False)` returns the compiled preparation report. CLI: `fc-kit prepare main [--refresh] [--json]`. `ctx.playground(script, timeout=10, output_limit=1_000_000, fps=15)` declares a prepared dependency. Preparation executes trusted local checkpoints; build, validate, inspect, frame, storyboard, preview, and render replay assets without checkpoint execution or browser launch. Changed sources, inputs, bindings, timing, or settings invalidate preparation. Reports include `prepared_assets` paths, fingerprints, and status; errors retain `PLAYGROUND_*` context.

`coding_playground(ctx, script, ...)` returns a Video with editor, canvas, and optional console. Blocks accept `layout="side"` or `"stacked"`, `code_ratio`, and a readable font size. Use `start` or narration `audio/subtitles/markers/cues`; checkpoint times are local to the authored window. [Full contracts](coding-playgrounds.md).

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
theme = "midnight" # or light, whiteboard, clean-flow
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

`segment.add(block, id=None, bounds=None, anchor="center", enter="theme", enter_duration=None, exit="theme", exit_duration=None, z_index=0, at=0, duration=None)` returns a placement handle. `bounds` overrides the context safe area, including for deliberate overlays. `at` is segment-local seconds; `duration` gives an explicit positive lifetime. Omitting duration holds to the segment end (including a final audio-tail hold). Entry recipes are `theme`, `flow`, `fade`, `pop`, `stagger`, or `None`; outros are `theme`, `flow`, `fade`, or `None`. The theme supplies default durations (0.6 seconds). Entrance and outro windows must fit without overlapping. `stagger` enters immediate children; `flow` recursively enters leaves and reverses their order on exit. Explicit `None` disables a side. Existing themes resolve omitted motion to none; `clean-flow` enables flow on both sides. Build reports include resolved motion and absolute placement start/end times. See [Clean-flow](clean-flow.md).

`segment.play(handle_or_child, callback, at=0, duration=1)` schedules a core Animation within the placement's authored lifetime. Local `at` becomes global time once. Use `handle["value"]` for named children. Overlapping writes to the same property are rejected by the engine; different properties and distinct placements may overlap. A finite placement disappears at its own end; an open placement disappears at the segment end.

`segment.cue_time(original_index, edge="start", offset=0)` translates a master narration cue to local seconds. Attach narration first; existing segments also become cue-aware when narration is attached later. Cue starts must lie in the segment's half-open source interval; a resulting event may reach its end boundary. Offsets may be signed but may not move the event outside the segment. Source cue times/indices are never changed.

```python
at = segment.cue_time(19)  # choose an original cue in this segment
card = segment.add(Heading("The important idea"), at=at, duration=2, enter="fade")
segment.play(card, lambda c: c.animate.opacity_to(0), at=at + 1.7, duration=0.3)
```

`segment.add_core(lambda ctx, bounds: component, ...)` supports advanced authoring. Return a fresh Component or BlockBuild every invocation. Direct components must already fit the supplied bounds. A complete core Scene/Sequence/Grid/Layer can also be returned by a project factory; segment metadata is unavailable for those entries.

## Custom blocks and themes

Implement `compose(context, bounds) -> BlockBuild(root, children={}, bounds=None)`. Construct fresh core objects every time, assemble all Group membership, and finish layout before returning. Named children must belong to that root's hierarchy. Measurement uses the root's actual core bounds; claimed bounds cannot bypass overflow checks.

Block content props are defensively copied when added. Prefer frozen dataclasses and tuples. Store core components only inside `compose`, never on the reusable block definition. Do not mutate the context while composing a block. Failed compilations publish no result and can be retried with fresh components.

Themes are frozen dataclasses in `facelesschamp_kit.themes`; `Theme` and `CLEAN_FLOW` are also exported at package root. Assign a custom Theme to `ctx.theme` in the factory before constructing Video; update `ctx.canvas` with a matching background if desired. Heading, TextPanel, and MetricCard support default/accent/muted variants and explicit color overrides. Precedence is theme defaults → chosen theme → variant → explicit color. Stack and Split are composable blocks; Split uses rows in portrait and columns in landscape. Optional theme tokens cover font weights, card shadows, a dot-grid backdrop, default entrances/outros, motion distance/stagger and editor theme. For regular custom fonts clear the variable-font weights. [Clean-flow](clean-flow.md) documents defaults and measured card content bounds.

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

`fc-kit [--project PATH] [--json] COMMAND`. Commands: init, doctor, list videos/blocks/themes/templates, prepare, validate, inspect, frame, storyboard, preview, render. `inspect main --json` is also accepted. Preview supports `--segment ID` or paired `--start/--end`.

Library errors are KitError with stable `code`, `message`, and optional scope. CLI exits 1 for build/runtime failures and 2 for argument syntax failures. JSON build failures return an `error` object on stderr; argparse syntax diagnostics remain plain text. Reports in `.fc-kit/reports/` include a versioned schema, original segment/cue timing, asset checksums, source hashes, settings, environment, and output metadata. Fingerprints are audit identities, not promises of byte-identical media across machines. Unregistered external data dependencies are not discovered; declare them through the asset registry. Persistent render-result caching is intentionally absent.

## FlowCanvas

`FlowCanvas(graph, script=None, theme=None, viewport=(1600,900), source_start=0, design=None)` exposes the `"diagram"` handle. Pass `design="networking"` or a core `FlowDesign` instance for the approved soft connection styling; this adds a `"glow"` handle. Animate the placement handle to transform both layers together. `theme` and `design` are mutually exclusive. Without `design`, kit theme inheritance is unchanged.

`FlowCard(label, icon, size=(240,260), detail=None, address=None, design="networking")`,
`FlowPopup(kind, value, design="networking")`, and `FlowBackdrop(design="networking")`
compose the approved networking components. Cards expose `surface`, `label`, `icon`
and supplied `detail`/`address`; popups expose `surface`, `icon`, `kind`, `value`;
backdrops expose `background`. See [FlowChamp](flowchamp.md).

Default strokes inherit `Theme.muted`. Compilation includes sampled visible core
diagnostics with placement/segment scope and script/master source times.

## Explanatory recipes and layout inspection

`apply_recipe(segment, recipe_id, content, bounds=None, events=(), id=None)`
validates content and returns a dictionary of named handles. `recipe_specs()` lists
all ten recipes with editable content examples and selection constraints.
`validate_recipe(recipe_id, content)` validates without requiring a renderer.
Recipe events use local segment time and explicit targets. The `code-result` recipe
requires prepared playground assets; compilation never executes preparation.

`CompiledVideo.layout_at(time)` reports conservative evaluated bounds for active
placements and named children at a master-clock time, along with segment/placement
IDs and lifetimes. It uses public core geometry with retained compiler handles.
Visibility, masks, and intentional intersections need visual review; intersecting
bounding boxes alone do not prove a design error. Valid sample times are
`0 <= time < compiled.duration`.

## Technical models and dependencies

ArchCanvas exposes model and fits a fresh core viewport. assets.mesh(id) resolves/checksums required model files. The arch-design recipe uses a shared structured design contract. Project.dependencies() inspects standard pyproject requirements before factory imports; reports include dependency versions and geometry fingerprints. See [ArchChamp and external tools](archchamp.md).

## Compiled video production

Compile once and call `compiled.frame(t, size=(960, 540))` for a PIL image,
`compiled.save_frame(t, path, size=(960, 540))`,
`compiled.storyboard([0.5, 1.0], directory)`, or
`compiled.export(path, settings=ExportSettings(...), start_time=0, end_time=None)`.
ExportSettings is the public Core value object. Methods never rerun a factory.
Export also accepts progress and cancel callbacks and overwrite=False.
Saved operations return a dict with output (Path), rendering, source_range and
settings. Still/contact-sheet ranges are None; source_time belongs to the caller.
Renderer identity includes the actual session and fonts, captured before close.
A supplied renderer is not closed. Existing Project methods still return Path.
Kit facades: media_probe(path), read_subtitle_cues(text), public_capabilities(),
validate_rendering(compiled, settings), and the identical Core ExportProgress type.

## Shot templates and theme bridge

`facelesschamp_kit.shots` provides complete single-idea shots as blocks: `TitleCard(title,
subtitle="", eyebrow="")`, `BigStat(value, label, prefix="", suffix="", context="")`,
`QuoteCard(text, attribution="")`, `StepsCard(steps, title="")` (2-5 steps, at most 9 words each),
`CompareCard(left_title, left, right_title, right)` and `EndCard(title, action="")`. They use
the role budgets (KitError TEXT_BUDGET when copy is too long), scale with the canvas and
animate with the theme entrance. `shot(name, content)` builds one from a mapping;
`shot_video(name, content, theme=, duration=, size=)` returns a CompiledVideo.
CLI: `fc-kit shot --list`, `fc-kit shot stat CONTENT.json --theme neon --frame 3` (also
`--preview`, `--storyboard`, `--audit`, `--portrait`, `--output`).

Kit themes: midnight, light, whiteboard, clean-flow, neon, documentary, paper. `Theme.core()`
returns the matching faceless_champ Theme. It is active while blocks compose, so core
primitives and role text inside blocks follow the kit theme. `Theme.from_core("neon",
accent=...)` builds a kit theme from a core preset. `heading_font` sets a separate heading
font. Block sizes scale with the canvas short side (1.0 at 1080p).
`Stack(*blocks, gap=28, weights=None)` and `Split` accept relative weights.
`Comparison(left, right, left_title="Before", right_title="After")`.
