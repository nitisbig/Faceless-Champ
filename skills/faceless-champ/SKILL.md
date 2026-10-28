---
name: faceless-champ
description: Author and render Python videos with Faceless Champ scenes, animations, layouts, images, and audio. Use when creating or editing videos with this library.
---

# Faceless Champ authoring

- Start from a [CHEATSHEET](../../CHEATSHEET.md) pattern: `with Theme.named(...).use():`,
  role text, `canvas.safe_area()` + Bounds helpers, primitives (Stat, Callout, Pill,
  GlassCard, Arc), `scene.reveal(...)`, and `run(build)`. Check `--frame` and `--audit`.

- Style text with roles: Text("...", role="title"|"heading"|"body"|"label"|...) and
  fit_text(text, Bounds(...), role="body", color=...). Never hand-pick tiny sizes.
  A TextBudgetError means the copy is too long: shorten it or split the beat; do
  not pass budget=False or a lower min_font_size to force it in. Use ordinary Text
  for exact whitespace such as code indentation.
- In kit projects, use Segment.cue_time(original_index, edge="start", offset=0)
  and add/add_core(at=..., duration=...) for individual word-triggered visuals.
  Entrances and motions must remain inside placement lifetimes; narration is attached
  once at master zero. Keep defaults compatible and preserve original cue indices.
- Use kit FlowDiagram(steps, direction="horizontal" or "vertical") for measured
  workflows. Named node-N, label-N, edge-N children support independent animation.
  ImageCard uses ImageSlot boxes labeled with the manifest filename. Compact
  TextPanel grids fit both title and body using measured allocations.

Read [the API](../../docs/api.md) for supported constructors and
[the premium references](../../examples/README.md) for complete scenes. Use
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
  Fonts: font="sans" (default), "display", "serif", "mono"; or
  TypeScale.named("tech"|"editorial") for a heading/body pairing.
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
  preview size preserves canvas aspect ratio, including portrait.
- Use Icon for tintable transparent PNGs and Arrow for drawable diagram spokes.
  FadeOut then remove() components when their lifetime ends. Use fresh instances
  when bringing a removed visual back. Animate each property chronologically.
- Use SlideIn/Out, ZoomIn/Out, PopIn/Out, BounceIn, and SpinIn for entrances/exits.
  Pulse, Shake, and Wiggle emphasize a visual and return to its current transform.
  These are component effects. Combine icon/label animations in one play call.
  Motion entrances already animate opacity; do not add FadeIn on the same object.
  Use explicit play(rate_func=...) to override preset easing. Custom Animation
  keyframes must increase from progress 0 to 1 and end at the declared target.
- Reuse the bundled named fonts or an explicit local TTF/OTF. Discover chart and camera APIs from their owning Kit/Core modules; do not invent
  unsupported video-import or graphical-editor constructors.

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
  never start implicit clocks. See docs/motion-graphics.md and the current premium
  collection for scene references.

- Use CodingChamp for source-preserving syntax-highlighted editor panels; install the
  optional coding extra for language aliases, or choose language="text" for plain text.
  CodeReveal(panel, start=0, end=1) uses the panel's typewriter, word, or block reveal_mode.
  block_ends are increasing inclusive local line numbers including the last line.
  Keep code readable by selecting excerpts; overflow raises instead of wrapping code.
  CodeTheme.named supplies midnight/ocean/paper/clean-flow. See docs/coding.md.
  Use explicit source-time ranges for excerpts and report full-export QA separately.

### FlowChamp diagrams

Use public `faceless_champ.flow` graph and script APIs for animated diagrams; use kit `FlowCanvas` for themed placement. Read `docs/flowchamp.md` for contracts. Inspect `FlowDataError.path`, `clip.diagnostics`, `state_at(time)`, and `bounds_for(id,time)` before export. Individual elements use FlowScript IDs; scene/kit handles animate the full viewport. Keep motion inside authored placement windows, including narration tails. Validate short encoded previews before claiming full-export correctness.

- For restrained diagrams, set FlowTheme.stroke to a neutral color and use accent
  for packets/highlights; kit defaults inherit Theme.muted. `stroke=None` preserves
  the core's original accent outlines. Use draw(tool="none") to omit drawing tools.
- Use diagnostics_at(original_script_time) for visible node/label overlaps and
  overflow. Kit samples action boundaries/midpoints and translates warnings to
  master source_time. Conservative rectangle warnings require visual inspection;
  no automatic obstacle routing or continuous collision proof is provided.
- Exterior technical labels can wrap to two lines. Keep minimum font sizes readable
  in the output and use node sizes/ports/waypoints that leave space for labels.
- FlowChamp label sprites have an 8 MiB bounded cache; label_cache_mb=0 verifies
  uncached parity. Static frame-key reuse preserves transient action boundaries.

The Hello World design is approved. For fc-agent coding tutorials, use its saved
template only when no custom design/instructions are supplied. The project-owned
templates/coding-tutorial/style.json controls colors, layout and springs. Generated
render.py must accept --fps and --quality low|high|4k.
Its structural checks do not render scene frames; honor the user's render boundary.

## V2 production ownership

Core owns deterministic composition, rendering and FFmpeg. Kit owns domain APIs,
preparation and CompiledVideo.frame/save_frame/storyboard/export. These operations
reuse the compiled object and return backend provenance before closing owned
renderers. Supplied renderers remain caller-owned. Agent delegates production to
Kit and retains checksums, source alignment, evidence history and review policy.
Preview, decoded export, visual review and editorial review are separate claims.
Discover optional capabilities offline; discovery does not prove device support.
ChessChamp is V1-only; migrate with the V2 M4 guide rather than installing a V2 chess extra.
