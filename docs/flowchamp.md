# FlowChamp

FlowChamp renders workflows, software architectures, networks, idea maps and circuit
illustrations offline. Core owns geometry and playback; kit provides themed placement.
It uses Pillow and bundled vector symbols, with no additional runtime dependency.
Circuit diagrams are illustrations, not electrical simulations.

```python
from faceless_champ import (
    Canvas, Scene, FlowChamp, FlowGraph, FlowNode, FlowEdge, FlowPort, FlowScript,
)

graph = FlowGraph(
    nodes=(
        FlowNode("client", "Client", ports=(FlowPort("out", "right"),)),
        FlowNode("api", "API", ports=(FlowPort("in", "left"),)),
    ),
    edges=(FlowEdge("request", "client", "api", "out", "in", label="Request"),),
)
script = FlowScript().draw(["client", "api"], duration=.6, stagger=.6)
script.draw("request", duration=.8, tool="pen")
script.signal("request", duration=2, repeat=2, marker="packet")
script.highlight("api", at=2.5, duration=1, dim=.25)
clip = FlowChamp(graph, script, width=1200, height=675, position=(600, 337.5))
scene = Scene(Canvas(1200, 675))
scene.add(clip).wait(script.duration)
scene.render("flow.mp4", width=960, height=540, fps=24)
```

## Authoring contract

`FlowNode(id, label="", symbol="rounded_rectangle", position=None, size=(160,90),
ports=(), image=None, rotation=0, scale=1)` describes a node in viewport design pixels.
Positions are node centers. Rotation is clockwise in degrees. Ports use `id`,
`side` (`left`, `right`, `top`, `bottom`, `center`) and an `offset` from 0 to 1.
Named ports rotate and scale with their node. Unnamed connections use the boundary
facing the other node. Circle and diamond ports project onto their boundary.

Symbols: `rectangle`, `rounded_rectangle`, `circle`, `diamond`, `document`, `service`,
`database`, `queue`, `server`, `client`, `router`, `resistor`, `capacitor`, `battery`,
`ground`, `switch`, `diode`, `led`, `and`, `or`, `not`, `image`, `junction`.
Local image nodes load assets before export. Labels wrap and shrink once, then fail
with an actionable error if they cannot fit. Technical-symbol labels appear below
symbols; ordinary card labels appear inside.

`FlowEdge(id, source, target, source_port=None, target_port=None, label="",
route="orthogonal", waypoints=(), dashed=False, arrows="end")` connects node IDs.
Arrow choices are `none`, `start`, `end`, `both`. Straight routes follow any supplied
waypoints; orthogonal routes insert right-angle bends through them; Bezier routes
accept zero or two control points. Waypoints remain in fixed viewport coordinates
while node endpoints move. Wires cross without a junction; use a `junction` node
and distinct edges to represent an electrical connection. Self-loops are supported.
Bezier curves use deterministic subdivision and approximate arc-length travel.

`FlowGraph(nodes, edges=(), layout="layered", direction="horizontal")` supports
`manual`, `layered`, `grid`, and `radial`. Every explicit node position takes precedence.
Manual layout requires all positions. Layered layout places strongly connected
nodes in one layer, then ranks the acyclic condensation graph. Ordering is stable.
Layouts do not route around obstacles or promise collision-free placement.
`clip.diagnostics` reports initial `FLOW_OVERLAP` and `FLOW_BOUNDS` issues for nodes;
use `bounds_for(id, time)` to audit moving geometry and edge labels.

## Script actions

All actions accept an ID or ordered list of IDs, `at` and `duration`. Times are local
seconds. Omitted `at` appends after the script's current end; default duration is 1s.

| Action | Extra arguments | Behavior |
| --- | --- | --- |
| `reveal` | `stagger=0` | Fade in; targets start hidden before their first reveal/draw |
| `hide` | — | Fade out and remain hidden |
| `move` | `position=(x,y)` | Move node centers; retain the final position |
| `scale` | `value` | Set node scale; retain the final scale |
| `rotate` | `value` | Set clockwise degrees; retain the final rotation |
| `draw` | `stagger=0`, `tool="pencil"` | Draw by path length; tool is `pencil`, `pen`, or `none` |
| `signal` | `direction="forward"`, `repeat=1`, `marker="dot"`, `color` | Travel an edge or connected edge sequence; reverse direction and packet markers supported |
| `highlight` | `dim=1`, `color`, `mode="outline"` | Temporarily emphasize targets; `tint` fills card shapes, `dim` fades unrelated elements |

Reveal, hide and draw share a visibility channel. Overlapping actions on the same
property/target are rejected; independent properties can run concurrently. Signals
and highlights exist on the half-open interval `[at, at+duration)`. Repeated signals
restart at their source on each cycle. Edge sequences must be ordered from source
to target, even for reverse playback. Signals are suppressed beyond the drawn edge
portion. Connections inherit endpoint visibility. Multiple highlights combine
unrelated-element dim factors; the last authored active highlight sets target color.

Drawing follows each symbol's ordered strokes. Labels/images fade in with drawing
progress. `FlowTheme(sketch=True, seed=0)` adds a deterministic secondary sketch
stroke; the authoritative path remains shared with the pencil and markers.

`FlowChamp` snapshots graph/script inputs at construction. Configure before adding
to a scene. Use `state_at(time)` for independent snapshot dictionaries and
`bounds_for(target, time)` for conservative viewport-local bounds including labels.
Inspection times use the original script clock. `source_start` offsets playback,
not inspection. `frame_image(age)` and renderer caching honor that offset and hold
final state after script completion. Existing scene/group transforms affect the whole
viewport. Individual nodes are script targets, not standalone Scene components.

## JSON and kit

`FlowChamp.to_dict()` exports a complete document with `schema_version: 1`, `graph`,
`script`, `theme`, viewport dimensions and `source_start`. Load with
`FlowChamp.from_dict(data)` or `FlowChamp.from_json(path)`. Image/font paths in files
resolve relative to the JSON file. `FlowGraph` and `FlowScript` also expose `to_dict`,
`from_dict`, and `from_json` for their respective sections. Full document exports
exclude outer scene position/scale/opacity; pass those to `from_dict`/`from_json`.

The packaged `faceless_champ/flow/schema.json` uses JSON Schema 2020-12. It validates
structure; Python additionally checks colors, ID/port references, connected signals,
finite numbers, timing conflicts, assets, and text fitting. `FlowDataError.path`
identifies the offending field or element. Unknown fields are rejected.

```python
from facelesschamp_kit.blocks import FlowCanvas

segment = video.segment("diagram", duration=script.duration)
handle = segment.add(FlowCanvas(graph, script, viewport=(1200, 675)))
segment.play(handle["diagram"], lambda c: c.animate.opacity_to(.5), at=3, duration=.5)
```

`FlowCanvas` inherits kit colors/fonts, accepts a `FlowTheme` override and `source_start`,
and preserves aspect ratio inside the allocated bounds. It creates fresh components
on each compose. Scripts must fit the authored placement; narration-tail holds do
not extend motion windows. Initial layout diagnostics enter the compilation report.
The existing `FlowDiagram` and its child handles remain unchanged.

Run `fc-kit init my-flow --template flowchamp` for an editable starter. Five recipes
are available through `faceless_champ.flow.examples.recipe(family, portrait=False)`;
families are `workflow`, `system`, `network`, `idea-map`, `circuit`. Their recommended
viewports are `(1200,675)` and `(600,1000)` respectively.

Render complete 30-second showcases:

```bash
python examples/flowchamp/render.py --overwrite
python examples/flowchamp/render.py --portrait --overwrite
```

V1 has no interactive editor, external diagram-language parser, electrical solver,
automatic obstacle avoidance, or arbitrary embedded core components.

Minimal JSON document (save as `diagram.json`, then load with `FlowChamp.from_json`):

```json
{
  "schema_version": 1,
  "width": 1200,
  "height": 675,
  "graph": {
    "nodes": [{"id": "input", "label": "Input"}, {"id": "output", "label": "Output"}],
    "edges": [{"id": "connection", "source": "input", "target": "output"}]
  },
  "script": {
    "actions": [
      {"kind": "draw", "targets": ["input", "output"], "at": 0, "duration": 0.6, "stagger": 0.6},
      {"kind": "draw", "targets": "connection", "at": 1.2, "duration": 0.8},
      {"kind": "signal", "targets": "connection", "at": 2, "duration": 2, "repeat": 2}
    ]
  }
}
```

Exterior symbol labels have a background to keep crossing wires from obscuring text.

## Narrated diagrams, styling and performance

`FlowTheme(stroke=None)` preserves the original accent-colored outlines. Set `stroke`
to a neutral color and `accent` to an emphasis color for restrained architecture
diagrams. Highlights and signals continue to use `accent` or their explicit color.
Kit `FlowCanvas` inherits its neutral stroke from `context.theme.muted`; an explicit
`FlowTheme` takes precedence. Exterior labels allow two lines at the theme's font size.

```python
theme = FlowTheme(background="#000000", surface="#000000", foreground="#F4F3EE",
                  stroke="#B1ADA1", accent="#C15F3C", font_size=38, minimum_font_size=28)
clip = FlowChamp(graph, script, theme=theme, width=1200, height=675)
warnings = clip.diagnostics_at(2.5)
```

`diagnostics_at(time)` returns a tuple of warning dictionaries at original script time.
`FLOW_BOUNDS` identifies `element`; `FLOW_OVERLAP` and `FLOW_LABEL_OVERLAP` identify
`elements`. Each warning includes `time`. Hidden targets and targets dimmed to zero
are excluded. Label collisions compare measured label rectangles with other labels
and node geometry; a connection's large path bounding box is never a collision area.
Rotated geometry uses conservative enclosing rectangles. Stroke/arrow extent is
included in overflow checks. These are sampled warnings, not a continuous geometric
proof or automatic routing. The original `clip.diagnostics` remains an initial-layout
check of all nodes, including initially hidden ones.
Label diagnostics and drawing bounds share the actual raster measurements, including
font rounding, rotation and fixed padding when individual nodes become very small.

Rasterization uses element-sized temporary layers. Label sprites have a bounded
8 MiB cache per component; `FlowChamp(..., label_cache_mb=0)` disables it for parity
checks. Cache settings are runtime controls and are not included in diagram JSON.
Run `PYTHONPATH=src python3 scripts/benchmark_flowchamp.py` for repeatable small/dense
raster timings and Python-allocation/Linux-RSS measurements; Pillow's native pixel
buffers are excluded from Python allocation measurements.
`frame_key(age)` reuses keys during static intervals and holds final state; animation
and signal intervals retain exact times, and highlights change keys at both boundaries.
All inspection methods remain independent of playback order and cache contents.

The [TikTok-like narrated example](../training%20project/tiktok-system-design/README.md)
uses `Video`, `Segment.cue_time`, `FlowCanvas`, and core primitives. Run its root
`python3 render.py` for a 0–12 s, 960×540/15 FPS preview. It supports source-clock
ranges, scene selection, frames, storyboards and checks. Full export requires
`--full`; short previews do not verify the complete film.
The core showcase also accepts `--clean` for this palette and hidden drawing tools.
