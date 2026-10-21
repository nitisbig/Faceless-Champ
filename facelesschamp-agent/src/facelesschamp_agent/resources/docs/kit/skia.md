# Skia profiles and native components

Install `facelesschamp-kit[skia]` or the core/kit editable checkout extras.
Pillow remains the default. Configure both profiles when native typography is used:

```toml
[profiles.preview]
backend = "skia"
antialias = 1
fps = 15

[profiles.final]
backend = "skia"
antialias = 1
fps = 30
quality = "4k"
```

Existing frame/storyboard/preview/render commands resolve these profiles. Validation
checks each selected backend. Config-file edits reload before building; explicit
in-memory Project.config changes are retained when the file is unchanged.

```python
from dataclasses import replace

ctx.theme = replace(ctx.theme, text_engine="skia", surface_mode="vector")
```

Text helpers and card/backdrop factories use these opt-ins. Explicit FlowDesign
objects keep their own settings. CodingTutorialStyle, CodeWorkspaceDesign and
CodeWindow accept the same selectors. Specialist CodingChamp/FlowChamp content
retains its existing raster implementation.

Reports include backend/version/font identity. Logical placement bounds remain
unchanged; shadowed placements also provide ink bounds for canvas clipping audits.
Pillow still supports simple vector paths, retained surfaces and gradients. Native
text, compound paths and PathMask require Skia. No network or GPU is required
during rendering. See the core Skia guide for native libraries and memory budgets.
