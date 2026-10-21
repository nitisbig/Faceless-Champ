The equation PNGs are inspected RGBA references from the six-second Kit example:
640x360, 15 FPS, transparent Cairo rendering, Manim CE 0.22.0, seed 0.
`equation-reference.json` records the producing stack. The native integration
test compares fixed source times with a tolerance for TeX/rasterizer differences;
it never updates these files. Review any replacement frames visually.

Run with `FC_MANIM_PYTHON=/path/to/manim/python FC_MANIM_TEX=1` and LaTeX/dvisvgm
on PATH. Geometry tests need no TeX. Normal unit tests require no Manim.
