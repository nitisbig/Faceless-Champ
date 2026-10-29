# Fourier synthesis / native Manim integration

45 seconds on pure black (`#000000`), with rotating complex vectors and epicycles,
a live scrolling reconstruction, and a matching one-sided amplitude spectrum.
Only functional axis and frequency labels appear. No audio, TeX, or Docker.

The five sinusoidal components use frequencies 1, 2, 3, 5 and 7 relative to a
six-second fundamental period. Colors match vectors to spectrum spikes.
The signal is the imaginary projection of their complex sum; its current sample
connects directly to the epicycle endpoint. Twelve seconds of actual signal history
scroll to the right, including the changing filter envelope. The faint reference
curve shows the complete five-component waveform. Spectrum heights show sinusoid
amplitudes (one-sided convention), with a common visual scale.

Timing: 0–9s fundamental; 9–15s second and third harmonics enter; 16–22s fifth
and seventh enter; 22–30s full synthesis; 30–34s smooth low-pass filtering;
34–38s first two components; 38–42s higher components return; 42–45s full synthesis.

Run from the repository root:

```bash
# Key verification only: 180 low-resolution source frames, five composited stills.
.venv/bin/python my-project/manim-fourier/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Optional full preview: 640×360, 15 fps.
.venv/bin/python my-project/manim-fourier/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python

# Full export: 1920×1080, 30 fps.
.venv/bin/python my-project/manim-fourier/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

Use `--manim-python` or `FC_MANIM_PYTHON` for your native Manim 0.22 interpreter;
the example interpreter is a temporary local environment. FFmpeg and ffprobe must
be on PATH. The producer environment needs Manim and NumPy; the parent environment
needs FacelessChamp. Manim prepares frames through the public adapter, and
FacelessChamp composites them through `Viewport` and exports the MP4. Outputs and
immutable preparation caches live in `output/` beside these scripts. Pass
`--overwrite` to replace an exported MP4.

Validation for this example is intentionally limited to the 4 fps preparation,
five composited key frames, numerical projection/filter checks, and Ruff. Full
15 fps preview and 1080p export are left for the commands above.
