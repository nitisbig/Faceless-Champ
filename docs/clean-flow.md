# Clean-flow surfaces

Clean-flow uses a warm gray background, white rounded cards, dark headings, and an
orange accent. Native editors use `CodeTheme.named("clean-flow")` for charcoal
surfaces. Select coordinated graph colors with `ColorScheme.named("clean-flow")`.

The core helpers return ordinary Image components, generated once from Pillow
pixels without filesystem or network access. The package includes variable DM Sans
and its OFL license; `CLEAN_FLOW_FONT` resolves the installed font's absolute path.

```python
from faceless_champ import (
    CLEAN_FLOW_FONT, Bounds, Canvas, ColorScheme, Scene, ShadowStyle,
    SlideIn, SlideOut, Text, card_content_bounds, card_surface, dot_grid,
)

scheme = ColorScheme.named("clean-flow")
scene = Scene(Canvas(1920, 1080, scheme.background))
scene.add(dot_grid(Bounds(0, 0, 1920, 1080), z_index=-1))
allocation = Bounds(220, 180, 1700, 900)
shadow = ShadowStyle()
card = card_surface(allocation, fill=scheme.surface, radius=44, shadow=shadow)
content = card_content_bounds(allocation, shadow=shadow, padding=40)
heading = Text(
    "A clean flow", font=CLEAN_FLOW_FONT, font_weight=700, font_size=96,
    color=scheme.text, position=content.center,
)
scene.play(SlideIn(card, distance=24), SlideIn(heading, distance=24), run_time=0.6)
scene.wait(2)
scene.play(SlideOut(heading, distance=24), SlideOut(card, distance=24), run_time=0.6)
```

The allocated bounds include the shadow's transparent padding. With the default
16-pixel blur and `(0, 12)` offset, the card face is inset 60 pixels on every side.
Content padding adds to that clearance. Both helpers reject bounds that leave no
content area. Rounded radius is clamped to half the smaller face dimension.

Place chart components inside `card_content_bounds(...)` and set their
`ChartStyle.scheme.surface` to `"#00000000"`; this retains the card's rounded
corners and shadow. Pass `font=CLEAN_FLOW_FONT`, `font_weight=400`, and
`title_font_weight=700` to ChartStyle for consistent typography.

`dot_grid` has a transparent background, so its dots overlay the Canvas color.
Factories rasterize once at 2× design resolution; existing renderer source and
sprite caches replay those pixels. Opacity, masks, transforms, and image reveal
effects remain available. Fill, blur, and dot spacing are fixed pixels: construct
a new surface when changing these values. Core components have explicit animation
timing; the kit's clean-flow theme supplies automatic entrance and outro defaults.

`card_surface(fill=LinearGradient(...))` and `RadialGradient(...)` add static
gradient faces while retaining the same allocated bounds and `ShadowStyle` API.
`gradient_surface(...)` makes a rectangular backdrop. See [gradient surfaces](premium-effects.md)
for stop/alpha semantics, allocation limits and the light/dark comparison preview.
