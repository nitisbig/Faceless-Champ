"""Render the 20 s moon lake preview: 1280x720, 30 fps, GPU (moderngl), one process.

A GPU context cannot be forked, so this renders with workers=1; at ~0.3 s per frame that is
still several times faster than the two-worker numpy renders.
"""

from pathlib import Path

from faceless_champ.export import ExportSettings, render
from faceless_champ.progress import ExportProgress
from scene import build

out = Path(__file__).with_name("output") / "moon_lake_720p.mp4"
out.parent.mkdir(exist_ok=True)
settings = ExportSettings(width=1280, height=720, fps=30, antialias=1, workers=1, preset="medium")
with ExportProgress() as progress:
    render(build(), out, settings=settings, overwrite=True, progress=progress)
print(out)
