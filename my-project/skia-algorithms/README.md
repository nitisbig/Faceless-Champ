# Skia algorithm scene

A silent 60-second Faceless Champ scene on pure black, with native Skia geometry
and shaped text. Only values, node IDs, and flow/capacity notation appear.

| Time | Graphics |
| --- | --- |
| 0–14s | Selection sort: comparisons, swaps, retained sorted prefix |
| 14–25s | Binary search tree assembly and in-order traversal |
| 25–36s | Breadth-first graph traversal and visit order |
| 36–43s | Linked-list insertion and pointer rewiring |
| 43–51s | Stack pushes and LIFO pops |
| 51–60s | Two augmenting flow paths, edge capacities, total flow 7 |

Run from the repository root with the existing native virtual environment:

```bash
.venv/bin/python my-project/skia-algorithms/render.py
```

Default: `output/skia-algorithms.mp4`, 1920×1080, 30 FPS, 60 seconds.
The command shows export progress, elapsed time and ETA. No Docker is used.

```bash
# Short sample, source seconds 3–5
.venv/bin/python my-project/skia-algorithms/render.py --preview --quality 720p --overwrite

# One frame or a source-clock excerpt
.venv/bin/python my-project/skia-algorithms/render.py --frame 58.6 --overwrite
.venv/bin/python my-project/skia-algorithms/render.py --range 43 50 --overwrite

# Full 4K export
.venv/bin/python my-project/skia-algorithms/render.py --quality 4k --overwrite
```

`--output PATH` and `--fps N` are also available. Each output has a JSON sidecar
with source times, rendering identity, and algorithm results.

## Limited verification

Checked the 60-second timeline, sorting result, BST in-order result, BFS order,
LIFO order, and network flow capacities/conservation. Inspected six chapter stills
in `output/contact-sheet.jpg`. Exported a two-second H.264 720p/30 sample (60 frames)
and verified its metadata and complete decode. Ruff format and lint passed.

The full minute and 4K output have not been rendered or verified.
