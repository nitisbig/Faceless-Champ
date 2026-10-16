# Hello World — approved premium coding design

A 14.96-second source-clock introduction using CodingChamp, OSChamp, FlowChamp,
clean-flow surfaces, and analytical spring motion. The complete lesson is not yet
authored. Only code, essential interface labels, and terminal output appear.

From the repository root, check without rendering:

```bash
python3 examples/programming/hello_world/render.py --check
```

Render the opening at 1920×1080 / 60 fps:

```bash
python3 examples/programming/hello_world/render.py --full --fps 60 --quality high
```

Use the repository virtual environment's Python if dependencies are not installed
in your system Python. Install the core `coding` extra for syntax highlighting.

For focused review, use `--frame 12.5` or `--range 9.79 14.96`.
`--full` exports all authored content, currently this 14.96-second opening;
`--render` remains an alias. Video exports show a progress bar, completed frames,
elapsed time and an ETA on stderr. ETA follows observed frame throughput;
Finalizing means frames are complete and the encoder is finishing the file.
Quality values are `--quality low` (720p), `high` (1080p), and `4k` (2160p).
Combine with `--fps 60`; neither option changes the selected source range.
`--width 960 --height 540 --fps 30` produces a smaller review export.
Use `--output PATH` and `--overwrite` explicitly when replacing an existing file.
Inputs and default outputs resolve relative to this example, so the script also
works from another directory. An explicit relative `--output` uses the caller's
working directory.

The supplied audio and both SRT files remain unchanged. Audio starts at master zero
and the opening stops at 14.96s. Subtitle files guide timing; captions are not shown.
Outputs are authored, and playback never executes the displayed Python.

The user approved this design on 2026-10-16. Reusable helpers and defaults now live
in the kit's separate coding tutorial package. Edit the local
[style.json](templates/coding-tutorial/style.json) to change background, accent,
editor colors, font sizes, layout and springs; builds reload it each time.
Lesson content and timing stay in `scene.py`. fc-agent uses this template only
when no custom design or instructions are supplied.

No new render was produced for the extraction. Agent media evidence remains
`media_rendered: false`, `full_export_verified: false`; user design approval is
recorded separately from encoded-media verification.
