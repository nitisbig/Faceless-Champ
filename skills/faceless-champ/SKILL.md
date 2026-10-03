---
name: faceless-champ
description: Author and render Python videos with Faceless Champ scenes, animations, layouts, images, and audio. Use when creating or editing videos with this library.
---

# Faceless Champ authoring

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
- Start with ql previews. Render to output/ and inspect representative decoded frames
  and media metadata. Add a final wait() when an animation's endpoint needs a hold.
- For narration, read SubtitleTrack.from_srt() and schedule visual events with
  scene.at(track.cue(number).start). Add Captions at zero for absolute audio timing.
  Preserve the source transcript and cue times; caption grouping does not retime it.
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
