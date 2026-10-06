# Cue-based narration and preview inspection

`CueScene` maps an unchanged `SubtitleTrack` to a chapter's local scene clock.
Use original one-based SRT indices, including nonconsecutive indices, to author
chapters without repeatedly calculating offsets.

```python
from faceless_champ import (
    Canvas, CueScene, FadeIn, Layer, Scene, Sequence, SubtitleTrack, Text,
    StoryboardSample, render_storyboard, save_frame,
)

track = SubtitleTrack.from_srt("cue-per-word.srt")
canvas = Canvas(1080, 1620, "#FFFFFF")
boundary = track.cue(20).start
audio = Scene(Canvas(1080, 1620, "#00000000"))
audio.add_audio("audio.mp3", start=0)

opening = CueScene(track, canvas, end_time=boundary)
with opening.at_cue(1):
    opening.play(FadeIn(Text("The question", color="#292724", position=(540, 600))), run_time=0.3)
opening.finish()

evidence = CueScene(track, canvas, start_time=boundary, end_time=max(track.duration, audio.duration))
with evidence.at_cue(20):
    evidence.play(FadeIn(Text("The evidence", color="#292724", position=(540, 600))), run_time=0.3)
evidence.finish()

video = Layer(Sequence(opening, evidence, canvas=canvas), audio, canvas=canvas)
save_frame(video, boundary + 0.5, "output/evidence.png", size=(540, 810))
render_storyboard(video, [StoryboardSample(1, "opening"), StoryboardSample(boundary + 1, "evidence")],
                  "output/storyboard", size=(360, 540), columns=2)
```

Choose cues and durations that fit the supplied narration. Positions remain in
design pixels; preview dimensions preserve the canvas aspect ratio.

## Timing contract

- `CueScene(track, canvas=None, *, start_time=0, end_time=None)` uses track.duration
  when end is omitted. An explicit end may extend beyond the last cue for an audio
  tail. End must exceed start.
- `cue_time(index, *, edge="start", offset=0)` returns local seconds. `edge="end"`
  uses the cue end; offset is signed seconds. The cue start must belong to
  `[start_time, end_time)`; the event must fall in `[start_time, end_time]`.
  Unknown indices raise KeyError.
- `with scene.at_cue(...)` uses `Scene.at()` semantics: independent objects may
  be authored out of order; one object's property tracks remain chronological.
- `finish()` holds to the exact segment duration and rejects animation, caption,
  or audio overflow. No silent trimming. Call after authoring before composition;
  adding more content afterward requires another check.

No narration or captions are added automatically. Put continuous audio on a
transparent parent Layer and use a cut-only Sequence. Sequence crossfades shorten
the clock and need deliberate timing adjustments. Input cues remain intact.
Range exports trim visuals and audio on the original composition clock.

## Stills and storyboards

`save_frame(node, time, output, *, size=None, renderer=None, overwrite=False)` saves
an RGB PNG. `render_storyboard(node, samples, directory, *, size=None, columns=3,
renderer=None, overwrite=False)` saves numbered PNGs and **storyboard.png**.
Samples are float times or `StoryboardSample(time, label="")`; input order and
repeated times are preserved.

Both helpers validate the composition, require `0 <= time < node.duration`, use
1× antialiasing by default, and protect existing files. Storyboard checks all
requested paths before writing. Neither exports video. Default width is 480 with
height derived from the canvas, including portrait. Explicit size preserves aspect
ratio. Labels fit cell width and use the bundled font. Supply a renderer to reuse caches.

The [stock-analysis example](../training%20project/stock-analysis/README.md) demonstrates
six chapters, image reservations, a dated revenue chart, conceptual diagrams,
and a preview-first CLI. Project prompts and source figures are composition data;
the timing, rendering, animation, and image fallback behavior belong to the library.
