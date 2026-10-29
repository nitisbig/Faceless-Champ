# Skia code editor and terminal

A silent 60-second programming scene on a black canvas. Only source code,
line numbers, file/window labels, commands and terminal output appear.
Native Python, no Docker, external assets, or audio. Default: 1080p at 30 fps.

| Time | Action |
| --- | --- |
| 0–2s | Editor fades in with a blinking cursor |
| 2–24s | Syntax-colored Python types character by character |
| 24–29s | Code holds with a line highlight |
| 29–33s | Complete editor shrinks uniformly; terminal slides in and types a command |
| 34–41s | Incorrect average and assertion traceback appear; failing line is highlighted |
| 41–46s | Cursor returns to the function; division by the count is typed |
| 47–53s | Command runs again and prints the correct average |
| 53–60s | Result holds, cursor blinks, both windows fade to black |

Run from the repository root:

```bash
# Full minute
.venv/bin/python my-project/skia-code-terminal/render.py

# Two-second motion preview: editor/terminal transition
.venv/bin/python my-project/skia-code-terminal/render.py --preview --quality 720p --overwrite

# Key frame or custom excerpt
.venv/bin/python my-project/skia-code-terminal/render.py --frame 53
.venv/bin/python my-project/skia-code-terminal/render.py --range 42 45 --output /tmp/code-edit.mp4

# Full 4K
.venv/bin/python my-project/skia-code-terminal/render.py --quality 4k
```

Outputs live in `output/` beside the script. JSON sidecars record the source
range, rendering identity, and native backend counters. Export shows elapsed
time and ETA. Full-minute and 4K exports have not been rendered or verified.

The project uses public `CodeWindow` vector surfaces and Skia-shaped `Text`.
Pygments tokenizes source; the project places native, fixed-width token runs
and clips reveal by character count. The project-local `EditorScene.sample(t)`
and `EditorRenderer` author timestamp-based geometry and delegate all drawing
to Faceless Champ's Skia renderer. For imported use, supply `EditorRenderer()`
to `render`/`save_frame`, and close it afterward or use its context manager.
Terminal output is authored; rendering never executes the displayed program.

Limited checks covered five inspected frames, exact 60-second duration, black
endpoints, deterministic sampling, and zero raster leaves. Both trusted source
revisions were executed once during verification to confirm the printed results
and failing/passing assertions. Contact-sheet labels are outside the scene.
The two-second transition preview passed probing (720p, 30 fps, 60 frames) and
a complete FFmpeg decode. Ruff and whitespace checks passed.
