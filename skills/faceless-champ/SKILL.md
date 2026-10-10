---
name: faceless-champ
description: Author and render Python videos with Faceless Champ scenes, animations, layouts, images, and audio. Use when creating or editing videos with this library.
---

# Faceless Champ authoring

- Use public fit_text(text, Bounds(...), font_size=..., min_font_size=..., color=...)
  for measured wrapping/shrinking; it returns an unowned centered Text. Use ordinary
  Text for exact whitespace such as code indentation. Impossible fits are errors.
- In kit projects, use Segment.cue_time(original_index, edge="start", offset=0)
  and add/add_core(at=..., duration=...) for individual word-triggered visuals.
  Entrances and motions must remain inside placement lifetimes; narration is attached
  once at master zero. Keep defaults compatible and preserve original cue indices.
- Use kit FlowDiagram(steps, direction="horizontal" or "vertical") for measured
  workflows. Named node-N, label-N, edge-N children support independent animation.
  ImageCard uses ImageSlot boxes labeled with the manifest filename. Compact
  TextPanel grids fit both title and body using measured allocations.
- The programming-value example supplies six chapters, four images/ slots and
  an outline written before scene code. Its render.py defaults to 0–12 seconds at
  960×540/15 fps. Use --storyboard, --range, --scene and --frame for feedback;
  --full is an explicit later action, not part of preview validation.

Read [the API](../../docs/api.md) for supported constructors and
[the examples](../../examples/showcase.py) for complete scenes. Use
[the guide](../../docs/guide.md) when working with timing, sound, or nested layouts.

- Subclass Scene and implement construct(); the CLI accepts the class name or a
  zero-argument composition factory. Resolve media paths relative to the script.
- Place elements in design pixels. Default canvas: 1920×1080, top-left origin,
  positive Y down. Components default to a center anchor.
- Configure properties before add(). Use play(component.animate...) for changes.
  Separate play calls are sequential; animations within one call are concurrent.
- Set audio start explicitly when syncing to an event. Otherwise it uses the current
  cursor. Audio may extend scene duration without advancing the visual cursor.
- Use Sequence for successive scenes and Grid for simultaneous panels. A grid's
  duration is its longest child. Crossfades need enough duration in adjacent scenes.
- Grid accepts padding (top, right, bottom, left) and start_times per child for
  staggered reveals; its duration includes the offsets, which also shift audio.
  Use Layer with transparent child canvases for a shared heading over a grid.
- Use Equation for single-line TeX-style expressions without dollar delimiters and
  Write for a left-to-right formula reveal. This needs the optional equations extra
  (`uv sync --extra equations`); MathText does not require system LaTeX. max_width
  fits long formulas. Use Polyline for drawable curves and closed filled regions,
  and Rectangle(corner_radius=...) for rounded cards.
- Use ColorScheme.named("midnight"), "paper", or "ocean" to coordinate background,
  surface, text, axis, and series roles. Match Equation(color_map=...) symbols to
  graph colors and labels. Keys are individual characters or TeX symbol commands;
  matches include roman-text glyphs, so choose a map for each expression.
  with_alpha() makes shaded fills; Polyline(line_cap="round") rounds endpoints.
  Text(font_weight=...) needs an explicit variable font with a Weight axis.
- Start with ql previews. Render to output/ and inspect representative decoded frames
  and media metadata. Add a final wait() when an animation's endpoint needs a hold.
- For narration, read SubtitleTrack.from_srt() and schedule visual events with
  scene.at(track.cue(number).start). Add Captions at zero for absolute audio timing.
  Preserve the source transcript and cue times; caption grouping does not retime it.
- For narration chapters, use CueScene(track, canvas, start_time=..., end_time=...)
  and with scene.at_cue(original_index). finish() checks overflow and holds to the
  exact boundary. Keep continuous audio on a transparent Layer over a cut-only
  Sequence. Include any audio tail beyond the final cue in the last chapter.
  See [chapter and preview contracts](../../docs/narration.md).
- Use save_frame(node, source_time, path) and render_storyboard(node, samples,
  directory) for shared preview export. StoryboardSample(time, label) adds labels;
  preview size preserves canvas aspect ratio, including portrait. The stock-analysis
  example defaults to a short opening; full export requires its explicit --full flag.
- Use Icon for tintable transparent PNGs and Arrow for drawable diagram spokes.
  FadeOut then remove() components when their lifetime ends. Use fresh instances
  when bringing a removed visual back. Animate each property chronologically.
- Use SlideIn/Out, ZoomIn/Out, PopIn/Out, BounceIn, and SpinIn for entrances/exits.
  Pulse, Shake, and Wiggle emphasize a visual and return to its current transform.
  These are component effects. Combine icon/label animations in one play call.
  Motion entrances already animate opacity; do not add FadeIn on the same object.
  Use explicit play(rate_func=...) to override preset easing. Custom Animation
  keyframes must increase from progress 0 to 1 and end at the declared target.
- Reuse the bundled default font or an explicit local TTF/OTF. Do not invent camera,
  chart, video-import, or graphical-editor APIs absent from v0.1.

Typical command:

```bash
uv run faceless-champ render script.py MyScene -o output/my_scene.mp4 -q ql
```

Use --overwrite only when replacing the chosen output is intended.

- Import raster assets with `Image.from_source(path_or_encoded_bytes_or_pillow)`.
  Pillow inputs snapshot the current frame; GIF bytes retain animation. URLs are
  not sources. Use `trim=True` for transparent padding and `tint=...` to preserve
  alpha while applying a palette. `Icon.from_source(..., color=...)` also works.
- Use `Polyline(draw_by="x")` with `Draw` and linear easing for horizontal time
  reveals; x coordinates must strictly increase and the path must be open. Render
  one continuous curve, not hundreds of tiny shapes that can produce seams.
- The `training project/ai-comapny-graph` example has a root render.py with preview,
  storyboard, single-frame, output, and overwrite options. Its data is fictional:
  retain the visible disclaimer and never describe it as historical adoption.

- Reserve missing artwork with ImageSlot(path, mode="auto", width=..., height=...).
  Auto loads existing files and draws labeled boxes for absent files; placeholder
  always forces boxes; required fails on missing files. Configure placeholder colors
  and font on the component, and keep asset-mode selection in the project CLI.
  Replace files and create a fresh renderer to load them. Existing corrupt files
  must surface as errors instead of being silently replaced by placeholders.
- SubtitleTrack accepts overlap_tolerance=0.0 on constructors and SRT loaders.
  Keep the default strict; opt into a small known source rounding overlap such as
  0.001 seconds without editing cue times. Latest-starting cues win accepted overlaps.
- Export short synchronized previews with render(start_time=..., end_time=...).
  Times refer to the original composition/audio clock. A Layer with continuous
  captions and audio over a cut-only Sequence avoids cumulative scene timing drift.
  Component fades can soften those cuts without changing chapter duration.
- Long narration uses bounded caption sprites via PillowRenderer(caption_cache_mb=32),
  separate from frame_cache_mb. Phrase layouts reuse measurements and held caption
  states reuse frames. Use zero budgets when checking cached/uncached parity.
- The country-economy example defaults to a 960×540 / 15 fps opening preview and has
  --image placeholder, --scene, --range, --frame, and --storyboard options. Its entire
  narration requires explicit --all-preview. Start visual QA with a storyboard and
  short clips. Its six numbered image prompts are in img-info.md; fonts and symbols
  reuse licensed assets in the main checkout. Keep the financial examples illustrative.

- Motion graphics: use fill_to/stroke_to/color_to, width_to/height_to,
  stroke_width_to/corner_radius_to, and scale_xy_to on supported components.
  Colors interpolate straight RGBA; explicit transparent same-hue colors avoid
  hue shifts. scale_x/scale_y multiply uniform scale. Scene.bounds_at measures
  animated geometry; component.bounds remains an initial-layout measurement.
- Use Stagger(lag=seconds), Succession, and Repeat(cycles=N, ping_pong=True).
  duration sets direct leaf duration; nested schedules retain their own run_time.
  Explicit play(run_time=...) scales the entire schedule. Two ping-pong cycles
  traverse forward then backward. Conflicting property tracks fail atomically.
- Attach RectangleMask, CircleMask, or normalized polygon ShapeMask before add().
  Masks are local to sprite centers or group pivots. Animate mask_to dimensions
  and position; Wipe reuses the alpha-mask compositor. Form groups before adding
  members. Keep masked hierarchies shallow for CPU previews.
- ProgressBar, ProgressRing, Gauge, LoadingDots and Checkmark animate via
  progress_to in [0,1]. Countdown is a nonnegative Number animated with value_to(0).
  LoadingDots has identical endpoints for finite Repeat loops. These components
  never start implicit clocks. See docs/motion-graphics.md and the self-contained
  examples/motion_graphics/render.py for timing and validation examples.
