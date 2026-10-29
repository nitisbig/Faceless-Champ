# Pythagorean rearrangement

45 seconds on pure black (`#000000`), with geometry and essential mathematical
labels only. Native Manim 0.22 creates the animation; FacelessChamp prepares,
caches, and composites it through `Viewport`. No Docker or LaTeX required.

The triangle has legs a = 3 and b = 2. Four rigid copies occupy the same area
inside two equal squares of side a + b. Their first arrangement leaves c²;
their second leaves a² and b². Colors track individual triangles through each
rotation and translation. Side squares, a right-angle marker and a measured
33.7° angle establish the geometry before the rearrangement.

Timing: 0–12 triangle and side squares; 12–19 first arrangement;
19–22 duplicate; 22–30 rigid rearrangement; 30–35 uncovered squares;
35–41 area cancellation and equation; 41–45 final hold.

From the repository root:

```bash
# Key testing only: 180 prepared frames at 640×360/4 fps; seven composite stills.
.venv/bin/python my-project/manim-pythagorean/render.py --frames --manim-python /tmp/fc-manim-runtime/bin/python

# Optional full preview (640×360/15) or full export (1920×1080/30).
.venv/bin/python my-project/manim-pythagorean/render.py --preview --manim-python /tmp/fc-manim-runtime/bin/python
.venv/bin/python my-project/manim-pythagorean/render.py --manim-python /tmp/fc-manim-runtime/bin/python
```

Use your own persistent native environment in place of the temporary Python path,
or set `FC_MANIM_PYTHON`. FFmpeg and ffprobe must be on PATH. Outputs are local to
`output/`; existing MP4s require `--overwrite`. `--frames` prepares a sparse
45-second source and writes stills without exporting a final MP4.

Key validation completed with native Manim 0.22: exactly 180 frames / 45 seconds,
seven FacelessChamp composite stills inspected, pure black corner pixels, area
arithmetic checked, and Ruff passed. Full preview and 1080p export remain unrun.

Rearrangement durations use whole-frame budgets so the paired rotations and
translations remain exactly two seconds at each supported frame rate. Native
timing checks at 320×180 confirm 1350 frames at 30 fps and 675 at 15 fps,
both exactly 45 seconds.
