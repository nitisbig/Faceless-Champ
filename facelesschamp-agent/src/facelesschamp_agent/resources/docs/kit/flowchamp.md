# FlowChamp in the kit

`FlowCanvas(graph, script=None, theme=None, viewport=(1600,900), source_start=0, design=None)`
composes the core `FlowChamp` component. The `"diagram"` handle addresses the whole
viewport. Use `FlowScript` target IDs for individual node/connection animations.

```python
from faceless_champ.flow.examples import recipe
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FlowCanvas


def build(ctx):
    graph, script = recipe("system")
    video = Video(ctx)
    video.segment("architecture", duration=6).add(
        FlowCanvas(graph, script, viewport=(1200, 675))
    )
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

## Approved networking design

Select `FlowCanvas(..., design="networking")` for the approved soft networking
connections. Author `FlowScript.signal(marker="capsule")` or use core
`FlowDesign.signal` for rounded traffic markers. `design` also accepts a core `FlowDesign`
instance. This is an explicit diagram-level selection; it does not change the
video's global kit theme. Existing placements without `design` retain their theme
inheritance and appearance. `theme` and `design` are mutually exclusive; the design
owns its connection styling. Persistent neutral wire strokes remain visible across
quiet spans and final holds; transparent proxy-node outlines and constant focus
width keep the connections clean. Supplied script duration and actions stay unchanged.

Use the measured companion blocks for visible components:

| Block | Parameters | Named children |
| --- | --- | --- |
| `FlowCard` | `label, icon, size=(240,260), detail=None, address=None, design="networking"` | `surface`, `label`, `icon`, optional `detail`, optional `address` |
| `FlowPopup` | `kind, value, design="networking"` | `surface`, `icon`, `kind`, `value` |
| `FlowBackdrop` | `design="networking"` | `background` |

Cards and popups preserve their design proportions and fit their full allocation,
including soft shadow clearance, inside the supplied bounds. `FlowCard.size` is
the visible face size in design pixels. `FlowBackdrop` fills its allocation with
the packaged background. The available icon names are `laptop`, `router`,
`internet`, `cloud`, `server`, `dns`, `lock_tls`, and `packet`. These assets and DM
Sans are bundled with core; rendering requires no preparation or downloads.

```python
from faceless_champ import Bounds
from facelesschamp_kit import Video
from facelesschamp_kit.blocks import FlowBackdrop, FlowCard, FlowPopup

def build(ctx):
    video = Video(ctx)
    segment = video.segment("network", duration=6)
    segment.add(FlowBackdrop(), bounds=ctx.bounds, enter=None, exit=None, z_index=-1)
    segment.add(
        FlowCard("Laptop", "laptop", size=(400, 430),
                 detail="192.168.1.20", address="example.com"),
        bounds=Bounds(180, 280, 700, 850), enter=None, exit=None,
    )
    segment.add(
        FlowPopup("DNS", "example.com"),
        bounds=Bounds(900, 160, 1550, 430), enter=None, exit=None,
    )
    return video
```

Use core `FlowDesign.pop_frames`/`move_frames` with `apply_transform` and
`transform_animation` when cards and graph ports move together. These are authored
timeline helpers; the blocks do not add a lesson clock or automatic node binding.
Designed `FlowCanvas` placements expose `diagram` for foreground connections and
packets, plus `glow` for their soft highlight layer. Animate the placement handle
itself to move or fade both layers together. Ordinary placements retain the whole
`diagram` handle. Target graph IDs through `FlowScript`.
The core [saved design guide](../../docs/flowchamp.md#saved-networking-design)
documents connection layering, native `capsule` markers, and fluid motion.

For narration, attach audio/SRT once with `video.narration(...)`, create cue-bounded
segments, and use `segment.cue_time(original_index)` for FlowScript action times.
Preserve source rounding overlaps with `overlap_tolerance=0.001` where appropriate.
