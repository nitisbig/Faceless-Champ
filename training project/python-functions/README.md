# function in python

A silent, 120-second CodingChamp training scene, authored at 1920×1080 / 30 FPS. This approved design is saved in the main library as `CodeWorkspaceDesign.named("clean-flow")`; the scene now uses that shared preset. Lesson content and timings remain here.

The dark editor fills the entire screen while code appears with a typewriter effect. There are no titles, callouts, chapter labels, footers, or explanatory text on screen. Visible text belongs to the code, window labels, and terminal command/output. Colorful clean-flow syntax and brief line highlights guide attention.

Before each run, the whole editor—including its chrome, code, and highlights—uniformly shrinks to 64% of its original size over 0.8 seconds. It moves to a 48-pixel left margin, centered vertically, revealing the warm light background and making room for a terminal on the right with a 32-pixel gap. Text keeps its proportions throughout the move. The terminal enters with a restrained macOS-style scale-and-fade transition. After its 0.45-second exit, the editor smoothly returns to its full-screen size and position over 0.9 seconds before typing resumes. Editor motion settles without overshoot.

| Time | Lesson | Terminal output |
| --- | --- | --- |
| 0–6s | Full-screen editor; start typing `def greet():` at 1.2s | — |
| 6–32s | Complete the function body and call `greet()` | `Hello, Python!` |
| 32–62s | Parameters and arguments: `greet(name)` | `Hello, Maya!` and `Hello, Leo!` |
| 62–92s | Return a value with `add(3, 4)` | `7` |
| 92–114s | Reuse `add()` with another call | `7` and `15` |
| 114–120s | Hold the final code, then fade out | — |

Run from the repository root:

```bash
# Default: structural checks only; creates no video or still image.
python3 'training project/python-functions/render.py'

# Equivalent explicit check; optionally save its JSON report.
python3 'training project/python-functions/render.py' --check
python3 'training project/python-functions/render.py' --check --output /tmp/python-functions-check.json

# Explicit visual review commands, for your rendering pass.
python3 'training project/python-functions/render.py' --frame 25
python3 'training project/python-functions/render.py' --range 21 30 --quality low --fps 15
python3 'training project/python-functions/render.py' --full
```

The runner uses the existing root `.venv` when available and imports the checkout's source. Renders default to 1080p / 30 FPS; `--quality low|high|4k`, `--fps 15|30|60`, `--output PATH`, and `--overwrite` are available. Default media paths are under this project's `output/` directory. Frame times must be in `[0, 120)`; ranges must satisfy `0 <= START < END <= 120`.

`scene.py` exposes `build_video() → (composition, report)`. Examples, typing stages, highlights and output are local; window chrome, layout and fluid motion use the public `CodeWorkspaceDesign` / `CodeWindow` helpers. See the core CodingChamp guide and `examples/coding/workspace.py` for reuse. Playback uses authored output and never runs tutorial code. `--check` validates the scene without executing examples. The trusted examples are executed separately during development to compare their stdout with the displayed output.

No new video or frame exports were performed while saving the approved design. Structural validation does not verify a full export. No dependency additions or website deployment are included.
