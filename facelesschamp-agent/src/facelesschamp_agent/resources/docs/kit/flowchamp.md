# FlowChamp in the kit

`FlowCanvas(graph, script=None, theme=None, viewport=(1600,900), source_start=0)`
composes the core `FlowChamp` component. The `"diagram"` handle addresses the whole
viewport. Use `FlowScript` target IDs for individual node/connection animations.

```python
from faceless_champ.flow.examples import recipe
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FlowCanvas


def build(ctx):
    graph, script = recipe("system")
    video = Video(ctx)
    video.segment("architecture", duration=6).add(FlowCanvas(graph, script, viewport=(1200, 675)))
    return video
```

Start with `fc-kit init my-flow --template flowchamp`. The starter follows the canvas
orientation and can switch between workflow, system, network, idea-map, and circuit
recipes. Kit colors/fonts are inherited unless a `FlowTheme` is supplied.

JSON uses the public core `FlowChamp.from_json`/`to_dict` document API. To place a
loaded document, pass its `graph`, `script`, `theme`, viewport and `source_start` to
`FlowCanvas`. Asset paths are resolved when loading the file.

The compiler rejects scripts extending beyond authored placements with `MOTION_WINDOW`,
including placements with narration tails. `source_start` permits excerpts. Layout
warnings are returned as `FLOW_OVERLAP`/`FLOW_BOUNDS` diagnostics. Invalid core diagram
data becomes `FLOW_DATA` with a field path and placement scope.

See [the full core guide](../../docs/flowchamp.md) for symbol, port, route, timing,
serialization, diagnostic and deterministic-playback contracts.

Default FlowCanvas themes use `context.theme.muted` for outlines and `accent` for
highlights/packets. Pass an explicit `FlowTheme(stroke=None)` to retain accent-colored
outlines, or set a custom neutral stroke. The core JSON document also carries `stroke`.

Compilation preserves initial warnings and additionally calls core `diagnostics_at`
at action starts, midpoints, ends, and excerpt endpoints. Timed warnings include
`segment`, `placement`, `script_time`, and `source_time`. The source time is on the
master narration clock: `segment.start + placement.at + script_time - source_start`.
Only times inside the authored playback window are sampled. `FLOW_LABEL_OVERLAP`
checks actual labels against labels/node rectangles rather than full connection bounds.
Sampling cannot guarantee that no collision occurs between the inspected times.

Core `FlowEdge(label_position=0.5, label_offset=(0, 0))` also works inside
`FlowCanvas`: move labels along routed connections by path-length fraction and
offset them in viewport design pixels. The compiler's label diagnostics use the
adjusted geometry. Defaults preserve existing placement.

For narration, attach audio/SRT once with `video.narration(...)`, create cue-bounded
segments, and use `segment.cue_time(original_index)` for FlowScript action times.
Keep source rounding overlaps with `overlap_tolerance=0.001` where appropriate.
The [TikTok example](../../training%20project/tiktok-system-design/README.md) provides
an editable, label-only landscape composition and a preview-default root renderer.
