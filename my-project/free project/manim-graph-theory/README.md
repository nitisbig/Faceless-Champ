# Graph algorithms / native Manim integration

45 seconds on pure black (`#000000`). One eight-node, twelve-edge directed
network demonstrates BFS, recursive DFS, and Dijkstra. Text is limited to node
IDs, edge weights, algorithm/frontier labels, tentative distances, and the final
path cost. No title cards, headings, narration, or subtitles appear in the video.

Run from the repository root with native Python:

```bash
# Key verification only: 180 prepared frames, seven composited PNGs.
.venv/bin/python my-project/manim-graph-theory/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Full 45-second preview, 640×360/15 fps.
.venv/bin/python my-project/manim-graph-theory/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python

# Full 45-second export, 1920×1080/30 fps.
.venv/bin/python my-project/manim-graph-theory/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

Use `--manim-python` or `FC_MANIM_PYTHON` to select another native Manim 0.22
environment. The temporary interpreter above exists on this machine. Native
Cairo/Pango, FFmpeg, and ffprobe are required; the scene needs no LaTeX or Docker.
FacelessChamp's public `prepare_manim` prepares the animation, then `Viewport`
composites it onto a 45-second FacelessChamp timeline. Outputs and preparation
cache stay in `output/`. Pass `--overwrite` to replace an exported video.

Timing:

- 0–3s: directed graph, node IDs, and weights appear.
- 3–11s: BFS discovery tree; FIFO frontier updates after each expansion.
- 11–19s: recursive DFS discovery tree; stack shows the current call path.
- 19–20s: reset traversal highlights and initialize tentative distances.
- 20–40s: select the lowest-distance unsettled node, probe outgoing edges,
  relax successful candidates, and update the sorted priority frontier.
- 40–45s: isolate the shortest route and send a gold packet along it.

Adjacency order follows `EDGES`; equal Dijkstra priorities use alphabetical node
IDs. BFS marks nodes when enqueued; DFS marks them on entry. Neither traversal
uses edge weights. Green Dijkstra probe packets indicate improving candidates;
gray packets indicate candidates that do not improve the current distance.
Distance labels are updated after all outgoing candidates are examined. The
priority frontier contains each unsettled discovered node once. Earlier relaxed
edges remain visible until the final route is isolated.

The computed route is `S → B → A → D → F → T`, with cost
`1 + 2 + 2 + 2 + 3 = 10`. Dijkstra improves `A: 4 → 3`, `D: 6 → 5`, and
`E: 9 → 8`, demonstrating relaxation on an actual weighted graph.

Key verification completed: native 640×360/4 fps preparation produced exactly
180 frames / 45 seconds; seven frames were composited through FacelessChamp
with black-corner checks. Representative traversal and shortest-path frames were
visually inspected, and distance labels were moved clear of the vertical edges.
Traversal orders and all eleven simple source-to-target paths were checked;
the computed route has minimum cost 10. Ruff lint/format and whitespace checks
passed. The full 15 fps preview and 1080p/30 fps export have not been rendered.
