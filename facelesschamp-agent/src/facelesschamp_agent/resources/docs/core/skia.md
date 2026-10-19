# Skia authoring and evidence

Install `facelesschamp-agent[skia]`. The core uses CPU raster surfaces and requires
Linux libfontconfig1/libgl1/libegl1. No display or GPU context is required.
Pillow stays the default; explicit Skia failure is an error, not silent fallback.

Select `backend="skia"` and `antialias=1` in both Kit preview/final TOML profiles.
DesignSpec has optional `text_engine="skia"` and `surface_mode="vector"` selectors;
their defaults preserve legacy text and Image-based surfaces. These forward into
Kit themes and existing UI helpers. Custom Python can use public core APIs:

```python
from faceless_champ import PathData, VectorPath, Text

curve = VectorPath(PathData().move_to(20,80).cubic_to(90,0,160,160,240,50),
                   stroke="#527BEF",stroke_width=4)
label = Text("Native type",text_engine="skia")
```

Public capabilities: SkiaRenderer, create_renderer, PathData, VectorPath, PathMask,
Surface, existing linear/radial gradient descriptions and ShadowStyle. Request
retained surfaces through existing factories with render_mode="vector". Paths
support existing transforms/Draw and immutable scene snapshots. Native text uses
explicit font files and matching measurement/fit_text; missing glyphs are errors.

Charts, maps, equations, captions, specialist clips and Arch viewports initially
remain raster adapters. Pillow supports simple paths/gradients/retained surfaces.
Native typography, compound path fills and path masks require Skia. GPU rendering,
SVG DOM import, morphing and backdrop blur are outside v1.

Check capability requirements before authoring. Review decoded frames from the
final backend: Pillow evidence cannot certify Skia output. Kit/Agent fingerprints
include configured backend versions and font identities, and render records name
the actual backend. Backend/version changes invalidate earlier evidence. Inspect
logical layout and shadow ink bounds; native antialiasing is not proof of a good
composition or successful full export. Render a bounded preview before full work.
