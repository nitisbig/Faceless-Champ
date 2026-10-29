# Roadster v2

V2 is a separate treatment of the complete source timeline. `render.py` and the
red/blue v1 review remain available. V2 uses `render_v2.py`, `scene/v2.py` and
`scene/v2_drawing.py`, sharing the original physics, geometry and source audio.

## Research translated into design decisions

- [IBM: classic animation principles](https://www.ibm.com/design/language/animation/classic-principles/)
  recommends staging attention, sequential animation, restrained secondary motion
  and plausible momentum. V2 establishes the whole road, moves the car immediately,
  and introduces the radius construction only during the bend. Technical scenes
  introduce the object, then the relationship, then the equation. Camera motion
  and physical motion stay continuous; the background stays black.
- [Material: choreography](https://m1.material.io/motion/choreography.html)
  uses shared elements and orderly transitions to preserve orientation. V2 retains
  the same physical model while it moves into the explanation layout; supporting
  diagrams enter together with a slight delay. The optical axis of the equation
  remains consistent. These are adaptations for this narrated film, not claims
  that interface animation durations are optimal for video retention.
- [IBM: type scale](https://www.ibm.com/design/language/typography/type-scale/)
  describes scale as a basis for hierarchy and consistent spacing. V2 uses STIX
  mathematical typography: approximately 92 px main equations, 46–54 px diagram
  variables, 30–38 px supporting relations and 23–26 px ticks at 1080p. Relations
  are measured before centering, and prior equations retire after a brief handoff.

## Treatment

- Full C-road opening: a dimensional road deck, blue edge light, red centerline,
  twin car-attached wakes, a wider three-quarter orbit and physical radius guide.
  The first frame contains the entire road and car, without titles or crop.
- Larger main experiments, asymmetric technical layouts, a dominant equation,
  no chapter titles, subtitles, footers or explanatory prose on the video canvas.
- Quieter graph axes, brighter traces, staged trace reveals and a distinct physical
  cursor. The underlying data remain unchanged while light moves along the curve.
- A transparent isometric pressure chamber, moving roof rotors, intake arrows and
  underbody flow; curved nozzle cutaways with moving streamlines.
- A diagonal-emphasized inertia matrix, fixed values and moving bracket light.
  The allocation diagram uses signed columns `[d; r × d]` for an illustrative
  ten-nozzle arrangement, rather than random changing coefficients. It is a
  teaching schematic, not a validated Tesla actuator layout or controller.
- Blueprint views have one large side view and two secondary projections. The
  three-question bridge now gives one experiment at a time the full stage.

STIX/MathText is already local. No TeX distribution, new font or asset download is
required. Source audio, subtitle cues, duration and scientific equations retain
their original timing. The visual changes do not establish a measured retention
improvement; the user will review the treatment.

## Render

From this project directory, use the repository environment:

```bash
../../.venv/bin/python render_v2.py --range 0 6.76 --quality low --fps 15
../../.venv/bin/python render_v2.py --frame 216 --quality low
../../.venv/bin/python render_v2.py --preview 8 --quality low --fps 10
../../.venv/bin/python render_v2.py --full --quality 4k --fps 30
```

`--fps` accepts 10, 15 or 30. `--quality` accepts low (960×540), high
(1920×1080), or 4k (3840×2160). Excerpts and stills default to low; full exports
default to 4k. Add `--overwrite` to intentionally replace an output.
The `--preview` argument selects one chapter, so it never queues ten previews by
accident. Exports stay under `output/v2/` unless `--output` is supplied.

Only selected key scenes are rendered for this revision. A full-film export and
exhaustive layout audit are intentionally not part of this review.
