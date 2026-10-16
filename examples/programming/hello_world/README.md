# Hello World — full Python lesson

A complete **131.12-second** source-clock lesson using CodingChamp, OSChamp,
FlowChamp, clean-flow surfaces, and analytical spring motion. The approved
14.96-second opening is preserved. Only code, essential interface labels, and
terminal output appear.

From the repository root, check without rendering:

```bash
python3 examples/programming/hello_world/render.py --check
```

Render the full lesson at 1920×1080 / 60 fps:

```bash
python3 examples/programming/hello_world/render.py --full --fps 60 --quality high
```

Use the repository virtual environment's Python if dependencies are not installed
in your system Python. Install the core `coding` extra for syntax highlighting.

The default full output is `output/hello-world-full.mp4`. From this example's
directory, the equivalent command is `../../../.venv/bin/python render.py --full`.

For focused review, use `--frame 78.98`, `--frame 129.6`, or
`--range 88.24 91.92`. Excerpts have separate filenames under `output/`.
`--full` exports the complete lesson; `--render` remains an alias.
Video exports show a progress bar, completed frames,
elapsed time and an ETA on stderr. ETA follows observed frame throughput;
Finalizing means frames are complete and the encoder is finishing the file.
Quality values are `--quality low` (720p), `high` (1080p), and `4k` (2160p).
Combine with `--fps 60`; neither option changes the selected source range.
`--width 960 --height 540 --fps 30` produces a smaller review export.
Use `--output PATH` and `--overwrite` explicitly when replacing an existing file.
Inputs and default outputs resolve relative to this example, so the script also
works from another directory. An explicit relative `--output` uses the caller's
working directory.

The supplied audio and both SRT files remain unchanged. The complete 131.016-second
audio starts at master zero, with no trimming or fades. The visual timeline ends
at the final word cue, 131.12s, preserving a 104 ms hold beyond the audio container.
All 345 word cues retain their original times, including the 1 ms overlap.
Subtitle files guide timing; captions are not shown. Outputs are authored, and
playback never executes the displayed Python.

| Time | Scene content |
| --- | --- |
| 0:00–0:14.96 | Approved opening and Hello World goal |
| 0:14.96–0:28.65 | Empty editor, new file, `hello.py` filename |
| 0:28.65–0:39.65 | Type `print("Hello World")` |
| 0:39.65–1:04.16 | Focus on `print`, parentheses, string, and quotation marks |
| 1:04.16–1:23.11 | Save, show `python hello.py` / `python3 hello.py`, run, and output |
| 1:23.11–1:31.92 | Change the message to `I'm learning Python` and run again |
| 1:31.92–1:53.84 | Type `print(5 + 3)`, output `8`, and focus on evaluation |
| 1:53.84–2:04.96 | Instruction-to-output signal and three-example recap |
| 2:04.96–2:11.12 | Preview a `message` variable and hold through the goodbye |

The editor, its code, caret, and focus marks share a complete window hierarchy,
so each transition to and from the terminal preserves uniform scaling. The check
audits timing, input hashes, Python syntax, output reveals, and root geometry at
60 samples per second across the entire timeline.

The user approved this design on 2026-10-16. Reusable helpers and defaults now live
in the kit's separate coding tutorial package. Edit the local
[style.json](templates/coding-tutorial/style.json) to change background, accent,
editor colors, font sizes, layout and springs; builds reload it each time.
Lesson content and timing stay in `scene.py`. fc-agent uses this template only
when no custom design or instructions are supplied.

`--check` produces structural evidence only, so its `media_rendered` and
`full_export_verified` fields remain false. Review artifacts and their verification
are recorded separately in [VERIFICATION.md](VERIFICATION.md). A full-resolution
full-length video has not been exported as part of scene authoring.
