# Hello World — premium opening draft

A 14.96-second source-clock introduction using CodingChamp, OSChamp, FlowChamp,
clean-flow surfaces, and analytical spring motion. The complete lesson is not yet
authored. Only code, essential interface labels, and terminal output appear.

From the repository root, check without rendering:

```bash
python3 examples/programming/hello_world/render.py --check
```

Render the opening at 1920×1080 / 60 fps:

```bash
python3 examples/programming/hello_world/render.py --render
```

Use the repository virtual environment's Python if dependencies are not installed
in your system Python. Install the core `coding` extra for syntax highlighting.

For focused review, use `--frame 12.5` or `--range 9.79 14.96`.
`--width 960 --height 540 --fps 30` produces a smaller review export.
Use `--output PATH` and `--overwrite` explicitly when replacing an existing file.
Inputs and default outputs resolve relative to this example, so the script also
works from another directory. An explicit relative `--output` uses the caller's
working directory.

The supplied audio and both SRT files remain unchanged. Audio starts at master zero
and the opening stops at 14.96s. Subtitle files guide timing; captions are not shown.
Outputs are authored, and playback never executes the displayed Python.

Design parameters remain named constants in `scene.py` during iteration. This draft
has structural checks only: `media_rendered: false`, `full_export_verified: false`.
Render and review before approving the design or saving an agent design preset.
