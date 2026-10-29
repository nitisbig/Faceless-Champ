# Faceless Champ cheatsheet

Copy-paste patterns for premium scenes. Every Python block here is executed by
`tests/test_cheatsheet.py`, rendered, and must pass the design audit.

## Rules that keep scenes premium

1. Activate one theme; never hard-code hex colors, fonts or font sizes.
2. Text uses roles: `display`, `title`, `heading`, `body`, `label`, `caption`.
3. On-screen text is a label, not a transcript: titles at most 8 words, body at most 22.
   A `TextBudgetError` means cut or split the copy. Do not shrink it to fit.
4. Lay out with `canvas.safe_area()` and `Bounds` helpers, not hand-computed pixels.
5. One idea per beat. Reveal it, hold it, then exit or cut.
6. Check with `python scene.py --frame T` and `--audit` before rendering.

## 1. Skeleton (start every scene file from this)

```python
from faceless_champ import Scene, Text, Theme, run

theme = Theme.named("midnight")  # midnight paper ocean clean-flow neon documentary whiteboard


def build():
    with theme.use():
        scene = Scene(theme.canvas())  # 1920x1080; theme.canvas(1080, 1920) for shorts
        area = scene.canvas.safe_area()
        title = Text("Why caches matter", role="title", position=area.center)
        scene.reveal(title)  # rises in with the theme motion
        scene.wait(3)
    return scene


scene = build()
if __name__ == "__main__":
    run(build)  # python scene.py --preview | --frame 2 | --audit
```

## 2. Title beat: eyebrow, title, subtitle

```python
from faceless_champ import Scene, Theme

theme = Theme.named("neon")
with theme.use():
    scene = Scene(theme.canvas())
    column = scene.canvas.safe_area().fit(1400, 600)
    title = theme.fit("How networks learn", column, role="display")
    eyebrow = theme.text("CHAPTER 2", role="label", tracking=0.14).next_to(title, direction="up", gap=28)
    subtitle = theme.fit("Gradients flow backward, layer by layer.", column, role="body", color="muted")
    subtitle.next_to(title, direction="down", gap=36)
    scene.reveal(eyebrow, title, subtitle, stagger=0.12, until=4)
    scene.wait(4)
```

## 3. Big number that counts up

```python
from faceless_champ import Scene, Stat, Theme

theme = Theme.named("paper")
with theme.use():
    scene = Scene(theme.canvas())
    stat = Stat(0, "of requests served from cache", scene.canvas.bounds.center, suffix="%")
    scene.reveal(stat)
    scene.play(stat.value.animate.value_to(98), run_time=1.6, rate_func="decelerate")
    scene.wait(2)
```

## 4. Side-by-side comparison on cards

```python
from faceless_champ import GlassCard, Group, Scene, Theme

theme = Theme.named("ocean")
with theme.use():
    scene = Scene(theme.canvas())
    left, right = scene.canvas.safe_area().fit(1640, 380).columns(2, gap=48)
    items = []
    for box, heading, body in (
        (left, "Before", "Every request hits the database."),
        (right, "After", "Hot keys are served from memory."),
    ):
        inner = box.inset(56)
        title = theme.fit(heading, inner, role="heading", color="primary")
        text = theme.fit(body, inner, role="body").next_to(title, direction="down", gap=24)
        items += [GlassCard(box), Group(title, text).move_to(*box.center)]
    scene.reveal(*items, stagger=0.1)
    scene.wait(3)
```

## 5. Numbered steps, revealed one by one

```python
from faceless_champ import Bounds, Dot, Scene, Text, Theme

theme = Theme.named("whiteboard")
steps = ["Run a forward pass", "Measure the loss", "Backpropagate gradients", "Update the weights"]
with theme.use():
    scene = Scene(theme.canvas())
    column = scene.canvas.safe_area().fit(900, 520)
    for index, (row, step) in enumerate(zip(column.rows(len(steps), gap=24), steps), 1):
        x, y = row.point("left")
        marker = Dot((x + 28, y), radius=28)
        number = Text(str(index), role="label", color="background", position=(x + 28, y))
        label = Text(step, role="body", position=(x + 90, y), anchor="center")
        label.move_to(x + 90 + label.bounds.width / 2, y)
        scene.reveal(marker, number, label, at=0.6 * index, stagger=0.05)
    scene.wait(4)
```

## 6. Annotated visual: ring, callouts, pulse

```python
from faceless_champ import Arc, Callout, Draw, Scene, Theme

theme = Theme.named("documentary")
with theme.use():
    scene = Scene(theme.canvas())
    center = scene.canvas.bounds.center
    track = Arc(center, 260, color="grid", width=18)
    ring = Arc(center, 260, sweep=290, width=18)
    note = Callout("Peak load at 2 a.m.", target=(center[0] + 184, center[1] - 184), offset=(120, -80))
    scene.add(track, ring)
    scene.play(Draw(ring), run_time=1.4, rate_func="emphasized")
    scene.reveal(note.dot, note.line, note.label, stagger=0.15)
    scene.play_at(2.4, note.dot.animate.through("scale", [1, 1.6, 1]), run_time=0.8)
    scene.wait(2.5)
```

## 7. Chart from data (kit)

```python
from faceless_champ import Scene, Theme
from facelesschamp_kit.charts import BarChart

theme = Theme.named("midnight")
with theme.use():
    scene = Scene(theme.canvas())
    box = scene.canvas.safe_area().inset(80)
    title_box, chart_box = box.rows((1, 6), gap=24)
    title = theme.fit("Requests per region", title_box, role="heading")
    chart = BarChart(
        ["EU", "US", "APAC"],
        {"2025": [42, 58, 31]},
        width=chart_box.width,
        height=chart_box.height,
        position=chart_box.center,
    )
    scene.reveal(title, chart, stagger=0.2)
    scene.wait(3)
```

## 8. Several beats in one scene

```python
from faceless_champ import Scene, Stat, Theme

theme = Theme.named("clean-flow")
with theme.use():
    scene = Scene(theme.canvas())
    area = scene.canvas.safe_area()
    scene.reveal(theme.fit("Three numbers that matter", area.fit(1400, 200), role="title"), until=2.5)
    scene.wait(2.5)
    for value, label in ((98, "uptime"), (40, "faster pages"), (3, "regions")):
        scene.reveal(Stat(value, label, area.center, suffix="%" if value > 9 else ""), until=scene.time + 2)
        scene.wait(2)
```

## 9. Trim paths, dashes and blend modes (needs skia-python)

```python
from faceless_champ import Circle, Group, Scene, Theme, Trace

theme = Theme.named("neon")
with theme.use():
    scene = Scene(theme.canvas())
    x, y = scene.canvas.bounds.center
    guide = Circle(300, fill=None, stroke=theme.color("border"), stroke_width=4, position=(x, y), dash=(16, 14))
    orbit = Circle(300, fill=None, stroke=theme.color("secondary"), stroke_width=14, position=(x, y), line_cap="round")
    left = Circle(150, fill=theme.color("primary"), stroke=None, position=(x - 80, y))
    right = Circle(150, fill=theme.color("highlight"), stroke=None, position=(x + 80, y), blend="screen")
    scene.add(guide, Group(left, right), orbit)  # blending stays inside the group
    scene.play(Trace(orbit, length=0.25), guide.animate.dash_offset_to(-60), run_time=2, rate_func="linear")
    scene.play(orbit.animate.trim_to(start=0, end=1, offset=0), run_time=0.8)
    scene.wait(1.5)
```

More: `PathData` booleans (`a - b`), `SVG("logo.svg")`, `ShaderFill(sksl)`,
`EffectStack(displacement=DisplacementMap(...))` and `Equation("mat(1, 2; 3, 4)", engine="typst")`.
See [docs/compositing.md](compositing.md).

## Narration timing (pattern, not executed)

<!-- skip -->
```python
from faceless_champ import SubtitleTrack

track = SubtitleTrack.from_srt("cue-per-word.srt")
scene.add_audio("audio.mp3", start=0)
cue = track.cues[11]  # the word "cache"
scene.reveal(stat, at=cue.start - 0.15)  # visuals land just before the spoken word
```

## Fast path: complete shots from JSON (kit)

```bash
fc-kit shot --list
fc-kit shot stat '{"value": 98, "suffix": "%", "label": "of requests hit the cache"}' --theme neon --frame 3
fc-kit shot title content.json --theme paper --preview 4
```

Templates: `title`, `stat`, `quote`, `steps`, `compare`, `end`. In kit videos use the
blocks directly: `segment.add(TitleCard("How networks learn", eyebrow="Chapter 2"))`.

## Easing names

`standard`, `emphasized` (default entrances), `decelerate`, `accelerate`, `snappy`,
`gentle`, `overshoot`, `anticipate`, `linear`, `smooth`, or `cubic_bezier(x1, y1, x2, y2)`.
