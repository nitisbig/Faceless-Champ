# v0.1 block catalog

## Current capability catalog

| Block | Content | Named children | Guide |
| --- | --- | --- | --- |
| CodeEditor | Authored source edit timeline | editor | [Coding](coding-playgrounds.md) |
| CodingPlayground | Prepared code, results, optional output | editor, canvas, output when present | [Coding](coding-playgrounds.md) |
| WebWalkthrough | Prepared capture with optional chrome/annotations | page, chrome/title when enabled | [Web](html-to-video.md) |
| WebElement | Tracked selector crop | element | [Web](html-to-video.md) |
| OSWalkthrough | Authored desktop script | ui | [OS UI](os-ui.md) |
| FinderWindow | Authored isolated Finder | ui | [OS UI](os-ui.md) |
| SettingsWindow | Authored isolated settings | ui | [OS UI](os-ui.md) |
| ChessBoard | Legal timed ChessScript | board | [Chess](chesschamp.md) |
| FlowCanvas | Graph and timed FlowScript | diagram | [Flow](flowchamp.md) |

Check named children in the feature guide before targeting a handle. OS/window blocks preserve transparent surroundings where applicable. FlowDiagram remains a simple ordered chain; FlowCanvas provides authored graph topology and timed element actions.

## All registered starters

| CLI template | Starting content | Preparation |
| --- | --- | --- |
| silent | Metric, comparison, and steps | none |
| explainer-short | Alias of silent | none |
| narrated-short | Labeled synthetic narration fixture | none |
| whiteboard-basic | Two sequential drawing recipes | none |
| os-ui | Virtual desktop/Finder/settings tutorial | none |
| chesschamp | Required timed game data.json | chess extra, no checkpoint preparation |
| flowchamp | Editable graph recipe | none |
| coding-concept | Independent cars and bound properties | fc-kit prepare |
| coding-backend | Flows, data, and tensor results | fc-kit prepare |
| coding-web | Local HTML/CSS/JS with browser interactions | fc-kit prepare and explicit Chromium installation |

Use `fc-kit list templates` and `fc-kit list blocks` for the installed catalog. `init` creates editable files and refuses existing destinations. Only playground preparation executes authored code; normal playback consumes prepared assets.

Each block constructs ordinary core components. The original basic-block gallery below covers portrait/landscape and midnight/light themes. The complete current catalog above also includes specialized code, web, OS, chess, and graph blocks. Block code licensing is pending; chess uses core bundled PNG artwork and other blocks use their declared local assets. The engine supplies its licensed default font and asset notices.

| Block | Content properties | Style properties | Named children |
| --- | --- | --- | --- |
| Heading | text | variant, color | text |
| TextPanel | text, title="" | variant, color | background, text, title when present |
| MetricCard | value, label | variant="accent", color | background, value, label |
| ImageCard | asset, label="", mode="required" | theme surface | background, image, label when present |
| Comparison | left, right | theme surface/accent | 0, 1 (the two panel roots) |
| StepList | steps (copied to tuple) | theme accent | 0, 1, … (step roots) |
| FlowDiagram | steps (copied to tuple), direction="horizontal" or "vertical" | theme surface/accent | node-0, label-0, edge-0, … |

Heading, TextPanel, and MetricCard variants: default, accent, muted. Explicit color overrides the variant. Text wraps then shrinks to a 24-pixel theme minimum; an unbreakable word or excessive text that still cannot fit fails with TEXT_FIT. MetricCard displays whole numbers using the core Number default; animate its value child with value_to. ImageCard uses contain fitting and never crops the source image. Required media cannot be silently replaced; auto/placeholder substitutions visibly identify themselves.

TextPanel allocates title and body space from its available height, so compact grid cards retain a readable body. All fitted block text uses the public core `fit_text` helper. ImageCard uses core `ImageSlot`: missing artwork reserves the same image geometry as real files and displays the manifest filename (or asset ID without a path). Auto loads a present file, placeholder always forces a box, and required fails on missing files. Existing corrupt files still fail in auto/required modes.

FlowDiagram measures an ordered chain of rounded cards and connectors inside its allocation. It does not run an implicit clock. Use `handle["node-1"]` for card transforms, `handle["label-1"]` for text emphasis, and `handle["edge-0"]` with core Draw for connector reveals. Choose vertical direction for tall allocations; an allocation too small for its steps fails with LAYOUT. The new self-contained example is `examples/workflow.py`.

Stack(*blocks, gap=28) allocates vertical cells. Split(*blocks, gap=28) stacks in portrait and uses columns in landscape. Nested layouts remain ordinary reusable blocks. Each child must fit its measured allocation. For explicit placement, pass core Bounds to segment.add.

Entry motion: fade, pop, stagger. Default duration is 0.6 seconds. Stagger animates immediate children, keeping later children invisible before their entrance. Entries must fit their segment. For more control, target named children with segment.play and core animation callbacks.

## Generated examples

Run `python scripts/catalog.py --output output/catalog`. This creates 24 thumbnails (six blocks × two themes × two formats), six two-second motion previews, and catalog.json. The local release candidate includes these generated artifacts under output/catalog.

| Block | Portrait midnight | Motion |
| --- | --- | --- |
| Heading | [Thumbnail](../output/catalog/Heading-midnight-portrait.png) | [Preview](../output/catalog/Heading.mp4) |
| TextPanel | [Thumbnail](../output/catalog/TextPanel-midnight-portrait.png) | [Preview](../output/catalog/TextPanel.mp4) |
| MetricCard | [Thumbnail](../output/catalog/MetricCard-midnight-portrait.png) | [Preview](../output/catalog/MetricCard.mp4) |
| ImageCard | [Thumbnail](../output/catalog/ImageCard-midnight-portrait.png) | [Preview](../output/catalog/ImageCard.mp4) |
| Comparison | [Thumbnail](../output/catalog/Comparison-midnight-portrait.png) | [Preview](../output/catalog/Comparison.mp4) |
| StepList | [Thumbnail](../output/catalog/StepList-midnight-portrait.png) | [Preview](../output/catalog/StepList.mp4) |

The corresponding `-light-portrait`, `-midnight-landscape`, and `-light-landscape` PNGs demonstrate theme/format variants. The ImageCard example deliberately demonstrates labeled missing media. Contract tests include long-text wrapping, minimum-size failures, strict missing media, real image loading, and captions within their reserved area.

Callable templates in facelesschamp_kit.templates: silent(ctx, value=42, label="Reusable components") and narrated(ctx, audio="voiceover", subtitles="word_cues", markers=None). These return Video definitions. CLI init generates editable starter files; upgrades never rewrite user projects. `explainer-short` is an alias for the silent scaffold. The narrated scaffold references a bundled, clearly labeled synthetic sample; replacing its manifest entries removes the sample-only label.

`whiteboard_basic(ctx, scenes=...)` adds ordered drawing recipes with explicit or narrated timing. `WhiteboardDrawing`
composes `WhiteboardPath`, `WhiteboardLine`, `WhiteboardArrow`, `WhiteboardRectangle`, and `WhiteboardCircle` specifications.
Its named children are `stroke-0`, `stroke-1`, etc. It displays the complete drawing when used as a standalone block;
the template controls sequential reveals. The `whiteboard-basic` CLI starter and `whiteboard` theme are registered.
See the [whiteboard guide](whiteboard.md) for geometry, styling, and narration examples.

## OS UI

`OSWalkthrough`, `FinderWindow`, and `SettingsWindow` fit authored system tutorials
into any layout. See [OS UI tutorials](os-ui.md); starter template: `os-ui`.

## ChessChamp

`ChessBoard(script, theme=None, source_start=0)` exposes the named child `board`. The `chesschamp` template and CLI scaffold use required root `data.json`. See [ChessChamp](chesschamp.md).

## FlowChamp

- Block: `FlowCanvas` (whole-component `diagram` handle).
- Template: `flowchamp`.
- Recipes: workflow, system, network, idea-map, circuit.
- Neutral strokes inherit theme muted; packets/highlights inherit accent.
- Timed diagnostics: overflow, node overlap, label overlap at action samples.
- [Usage and timing](flowchamp.md).

## ArchChamp

ArchCanvas places technical 3D geometry with model handle. arch-design is the structured recipe. The silent landscape archchamp starter demonstrates a multipart assembly, camera motion and dimensions. See [ArchChamp](archchamp.md).
