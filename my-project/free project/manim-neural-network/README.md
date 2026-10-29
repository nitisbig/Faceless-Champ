# Neural networks / native Manim integration

45 seconds on pure black (`#000000`), with mathematical labels only. A seeded
3–4–3–1 network uses tanh hidden layers, a linear output, and squared-error loss.
Cyan/pink edges encode positive/negative weights; cyan packets travel forward,
and gold gradient packets travel backward. Packet sizes reflect gradient
magnitudes. All 20 gradient-descent steps update every weight and bias using
analytic backpropagation on the same input and target shown in the scene.

Run from the repository root:

```bash
# Key verification: 180 prepared frames at 640×360/4 fps, seven composited PNGs.
.venv/bin/python my-project/manim-neural-network/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Complete 45-second preview, 640×360/15 fps.
.venv/bin/python my-project/manim-neural-network/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python

# Full 45-second export, 1920×1080/30 fps.
.venv/bin/python my-project/manim-neural-network/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

The temporary native Manim 0.22 interpreter above is available on this machine.
Use `--manim-python` or `FC_MANIM_PYTHON` for another environment. Native
FFmpeg/ffprobe and Cairo/Pango are required; no Docker or LaTeX is used.
FacelessChamp's public `prepare_manim` adapter prepares the scene, then
`Viewport` composites the prepared frames onto a FacelessChamp timeline.
Outputs and the preparation cache are local to `output/`. Use `--overwrite`
to replace an exported MP4.

Timing:

- 0–8s: weighted network construction and forward activations.
- 8–17s: numerical first-layer matrix product, highlighting one row at a time.
- 17–23s: tanh curve, moving activation, and its local derivative.
- 23–32s: squared loss, backward gradient pulses, chain rule, update equation.
- 32–45s: parameter updates, loss trace, prediction and weight readouts, final hold.

Key verification completed: 45-second/180-frame preparation, seven
FacelessChamp-composited frames with black-corner checks, inspected matrix,
activation, backpropagation and final training frames, numerical finite-difference
checks of all weight/bias gradients, and decreasing loss at every training step
(0.37693 → 0.00161). Python lint/format checks passed. The complete 15 fps preview
and 1080p export have not been rendered.

Timing regression: cumulative cue boundaries are rounded to frames, preventing
fractional beats from accumulating extra frames at export FPS. The focused
regression passes at 4, 15, and 30 fps. A native 320×180/30 fps preparation
produced exactly 1,350 frames (45 seconds) and passed FacelessChamp scene creation.
Run the regression with:

```bash
/tmp/fc-manim-runtime/bin/python my-project/manim-neural-network/test_timing.py
```
