# v0.1 block catalog

Each block constructs ordinary core components. Both 9:16 and 16:9 and both themes are tested. Block code licensing is pending; no externally sourced artwork is bundled in these compositions. The engine supplies its licensed default font.

| Block | Content properties | Style properties | Named children |
| --- | --- | --- | --- |
| Heading | text | variant, color | text |
| TextPanel | text, title="" | variant, color | background, text, title when present |
| MetricCard | value, label | variant="accent", color | background, value, label |
| ImageCard | asset, label="", mode="required" | theme surface | background, image, label when present |
| Comparison | left, right | theme surface/accent | 0, 1 (the two panel roots) |
| StepList | steps (copied to tuple) | theme accent | 0, 1, … (step roots) |

Heading, TextPanel, and MetricCard variants: default, accent, muted. Explicit color overrides the variant. Text wraps then shrinks to a 24-pixel theme minimum; an unbreakable word or excessive text that still cannot fit fails with TEXT_FIT. MetricCard displays whole numbers using the core Number default; animate its value child with value_to. ImageCard uses contain fitting and never crops the source image. Required media cannot be silently replaced; auto/placeholder substitutions visibly identify themselves.

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
