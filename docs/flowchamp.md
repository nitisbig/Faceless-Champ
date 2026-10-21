# FlowChamp

FlowChamp renders workflows, software architectures, networks, idea maps and circuit
illustrations offline. Core owns geometry and playback; kit provides themed placement.
It uses Pillow and bundled vector symbols, with no additional runtime dependency.
Circuit diagrams are illustrations, not electrical simulations.

```python
from faceless_champ import Canvas, Scene
from facelesschamp_kit.diagrams import FlowChamp, FlowGraph, FlowNode, FlowEdge, FlowPort, FlowScript

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
route="orthogonal", waypoints=(), dashed=False, arrows="end",
label_position=0.5, label_offset=(0,0))` connects node IDs.
Arrow choices are `none`, `start`, `end`, `both`. Straight routes follow any supplied
waypoints; orthogonal routes insert right-angle bends through them; Bezier routes
accept zero or two control points. Waypoints remain in fixed viewport coordinates
while node endpoints move. Wires cross without a junction; use a `junction` node
and distinct edges to represent an electrical connection. Self-loops are supported.
Bezier curves use deterministic subdivision and approximate arc-length travel.

Use `label_position` (0 to 1) to anchor a label by distance along the current routed
path, and `label_offset=(dx, dy)` to shift it in viewport design pixels. Offsets use
the viewport's horizontal/vertical axes and scale with the whole diagram. The anchor
follows moving endpoints; fixed waypoints retain their existing behavior. Defaults
preserve midpoint labels. Rendering, bounds and collision diagnostics share the same
label geometry. For example, `FlowEdge("read", "api", "cache", label="Read",
label_position=0.35, label_offset=(0, -24))` places the label above the wire.

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
| `signal` | `direction="forward"`, `repeat=1`, `marker="dot"`, `color` | Travel an edge or connected edge sequence; reverse direction and `dot`, `packet`, or rounded `capsule` markers supported |
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
are available through `facelesschamp_kit.diagrams.examples.recipe(family, portrait=False)`;
families are `workflow`, `system`, `network`, `idea-map`, `circuit`. Their recommended
viewports are `(1200,675)` and `(600,1000)` respectively.

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

`FlowTheme.node_stroke=None` inherits the ordinary `stroke`/`accent` outline color.
Set it to a separate color, including transparent, to style node boundaries
independently of the connections. `highlight_width=2` preserves the legacy focus
outline expansion; choose `0` for a constant connection width during color emphasis.
Both fields are optional and included in diagram JSON.

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

## Saved networking design

`FlowDesign.named("networking")` saves the approved Networking Explained visual
design: cool washed background, white rounded cards, soft shadows, bundled DM Sans,
dark labels, blue requests, teal responses, and violet DNS emphasis. It is an
explicit design selection; existing FlowChamp themes keep their defaults.

The design composes ordinary core components through `node_card`, `popup`,
`packet_marker`, and `backdrop`. Device cards accept a label, one bundled icon,
position and face size, with optional detail and browser address. Protocol popups
accept short `kind` and `value` text. Cards, popups, packet markers and connection
layers return `FlowVisual` objects, which are ordinary
`Group` components with named `parts` and transformed `face_bounds`. Add and animate
the visual directly. Its `bounds` includes symmetric shadow clearance; the visible
face remains centered. `backdrop` returns an ordinary core `Image`.

```python
from faceless_champ import Bounds, Canvas, Scene
from facelesschamp_kit.diagrams import FlowDesign

design = FlowDesign.named("networking")
scene = Scene(Canvas(1920, 1080, design.palette["background"]))
scene.add(design.backdrop(Bounds(0, 0, 1920, 1080)))
laptop = design.node_card(
    "Laptop", icon="laptop", position=(420, 540), size=(400, 430),
    detail="192.168.1.20", address="example.com",
)
scene.add(laptop)
# Named parts are components: laptop.parts["icon"], laptop.parts["address"].
scene.wait(4)
```

The bundled icon names are `laptop`, `router`, `internet`, `cloud`, `server`, `dns`,
`lock_tls`, and `packet`. Icons and the approved background are package assets and
resolve independently of the current working directory. No preparation step,
download, or optional image-processing dependency is required.

`design.connections(graph, script, width=..., height=..., source_start=...)`
provides the coordinated diagram and soft connection glow as named visual parts.
Connections have a persistent neutral wire stroke, transparent proxy-node outlines,
and constant width during focus. Authored highlights supply emphasis colors. The
caller's script remains unchanged, including its duration, so a bare graph gets
visible connections and final holds retain their neutral cables without extra actions.
Keep visible device cards above those connections. Author graph node positions,
sizes and ports to match the card faces; the connection layers use transparent
graph nodes as proxy geometry. Bézier edges without fixed control points reshape
from their moving named ports. `FlowScript.signal(..., marker="capsule")` renders a rounded,
glossy packet natively along the same routed path; dot and rectangular packet
markers retain their existing appearance.

`pop_frames` supplies the small lift, overshoot and settling motion;
`move_frames` supplies a smooth repositioning curve. Apply the same frame sequence
to graph nodes with `apply_transform` and to a card's root with
`transform_animation`. Both helpers accept the same sampled frame sequence;
`apply_transform(script, target, frames, at=..., duration=...)` authors public
FlowScript moves/scales and `transform_animation(component, frames, offset=...)`
returns the corresponding core animation. These helpers keep the card and its
connection ports on the same deterministic timeline.

`design.signal(script, targets, at=..., duration=..., direction=..., color=...)`
authors capsule traffic with eased connection emphasis. Optionally call
`design.complete_connections(script, edges, duration=...)` after authoring traffic
to add explicit neutral-color actions or extend the authored horizon to a desired
scene length. Connections already retain their neutral base stroke without this
step. Timings and lesson content remain authored
by the caller. Select `tool="none"` on connection draws for the clean presentation.
